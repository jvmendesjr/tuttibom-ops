from __future__ import annotations

import io
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tuttibom.mcp_ops import transcricao_offline as modulo
from tuttibom.mcp_ops.transcricao_offline import ErroTranscricaoOffline, TranscritorOffline


@pytest.fixture
def modelo(tmp_path: Path) -> Path:
    pasta = tmp_path / "modelo"
    pasta.mkdir()
    for nome in ("model.bin", "config.json", "tokenizer.json", "vocabulary.txt"):
        (pasta / nome).write_bytes(b"fixture")
    return pasta


@pytest.fixture
def transcritor(modelo: Path) -> TranscritorOffline:
    # Substitui o binário somente nos testes que mockam subprocess.run.
    return TranscritorOffline(modelo, ffmpeg_executavel=sys.executable, max_audio_bytes=16)


def test_requer_modelo_absoluto_e_tokenizer_local(modelo, monkeypatch):
    spawn = Mock()
    monkeypatch.setattr(modulo.subprocess, "run", spawn)

    with pytest.raises(ErroTranscricaoOffline, match="modelo_local_incompleto"):
        TranscritorOffline("small")

    (modelo / "tokenizer.json").unlink()
    with pytest.raises(ErroTranscricaoOffline, match="modelo_local_incompleto"):
        TranscritorOffline(modelo)
    spawn.assert_not_called()


def test_transcritor_recusa_binario_indisponivel(modelo, monkeypatch):
    monkeypatch.setattr(modulo.shutil, "which", lambda _: None)
    with pytest.raises(ErroTranscricaoOffline, match="executavel_indisponivel"):
        TranscritorOffline(modelo)
    with pytest.raises(ErroTranscricaoOffline, match="executavel_indisponivel"):
        TranscritorOffline(modelo, python_executavel=modelo / "python")


@pytest.mark.parametrize("config", [
    {"max_audio_bytes": 0},
    {"max_duracao_segundos": 0},
    {"timeout_conversao": float("inf")},
    {"timeout_transcricao": 0},
])
def test_recusa_limites_invalidos(modelo, config):
    with pytest.raises(ValueError, match="limites_de_transcricao_invalidos"):
        TranscritorOffline(modelo, **config)


@pytest.mark.parametrize("audio, idioma, erro", [
    (b"", "pt", "audio_invalido"),
    (b"x" * 17, "pt", "audio_invalido"),
    ("arquivo.wav", "pt", "audio_invalido"),
    (b"x", "pt-BR", "idioma_invalido"),
])
def test_recusa_entrada_antes_de_executar(transcritor, monkeypatch, audio, idioma, erro):
    spawn = Mock()
    monkeypatch.setattr(modulo.subprocess, "run", spawn)
    with pytest.raises(ErroTranscricaoOffline, match=erro):
        transcritor.transcrever(audio, idioma=idioma)
    spawn.assert_not_called()


def test_converte_pcm_e_executa_python_local(modelo, transcritor, monkeypatch):
    pcm = b"\x01\x00\x02\x00"
    spawn = Mock(side_effect=[
        SimpleNamespace(stdout=pcm), SimpleNamespace(stdout="  Olá,\n tudo bem?  ".encode()),
    ])
    monkeypatch.setattr(modulo.subprocess, "run", spawn)

    assert transcritor.transcrever(b"audio") == "Olá, tudo bem?"

    conversao, inferencia = spawn.call_args_list
    comando, = conversao.args
    assert comando[comando.index("-protocol_whitelist") + 1] == "pipe"
    assert comando[comando.index("-i") + 1] == "pipe:0"
    assert comando[comando.index("-ac") + 1] == "1"
    assert comando[comando.index("-ar") + 1] == "16000"
    assert comando[comando.index("-f") + 1] == "s16le"
    assert comando[comando.index("-t") + 1] == "61"
    assert conversao.kwargs["input"] == b"audio"
    assert conversao.kwargs["timeout"] == 10
    assert inferencia.args[0][-3:] == [str(modelo), "pt", str(60 * 32_000)]
    assert inferencia.kwargs["input"] == pcm
    assert inferencia.kwargs["timeout"] == 45
    for chamada in (conversao, inferencia):
        assert chamada.kwargs["env"]["HF_HUB_OFFLINE"] == "1"
        assert chamada.kwargs["env"]["HF_HUB_DISABLE_TELEMETRY"] == "1"
        assert chamada.kwargs["stderr"] == subprocess.DEVNULL
        assert chamada.kwargs["check"] is True


@pytest.mark.parametrize("pcm", [b"", b"x", b"\0" * (60 * 32_000 + 2)])
def test_recusa_pcm_vazio_desalinhado_ou_longo(transcritor, monkeypatch, pcm):
    spawn = Mock(return_value=SimpleNamespace(stdout=pcm))
    monkeypatch.setattr(modulo.subprocess, "run", spawn)
    with pytest.raises(ErroTranscricaoOffline, match="pcm_invalido"):
        transcritor.transcrever(b"audio")
    assert spawn.call_count == 1


@pytest.mark.parametrize("texto", [b"", b"  \n", b"...", b"a\x00", b"\xff", b"x" * 65_537])
def test_recusa_saida_invalida(transcritor, monkeypatch, texto):
    spawn = Mock(side_effect=[SimpleNamespace(stdout=b"\0\0"), SimpleNamespace(stdout=texto)])
    monkeypatch.setattr(modulo.subprocess, "run", spawn)
    with pytest.raises(ErroTranscricaoOffline, match="transcricao_invalida"):
        transcritor.transcrever(b"audio")


@pytest.mark.parametrize("etapa, erro, codigo", [
    ("conversao", subprocess.TimeoutExpired(["ffmpeg"], 1, output=b"privado"), "timeout"),
    ("conversao", subprocess.CalledProcessError(1, ["ffmpeg"], stderr=b"privado"), "falhou"),
    ("transcricao", subprocess.TimeoutExpired(["python"], 1, output=b"privado"), "timeout"),
    ("transcricao", subprocess.CalledProcessError(1, ["python"], stderr=b"privado"), "falhou"),
    ("transcricao", FileNotFoundError("privado"), "falhou"),
])
def test_falhas_nao_expoem_dados(transcritor, monkeypatch, caplog, etapa, erro, codigo):
    respostas = [SimpleNamespace(stdout=b"\0\0")] if etapa == "transcricao" else []
    spawn = Mock(side_effect=[*respostas, erro])
    monkeypatch.setattr(modulo.subprocess, "run", spawn)

    with pytest.raises(ErroTranscricaoOffline, match=rf"^{etapa}_{codigo}$") as exc:
        transcritor.transcrever(b"privado")
    assert "privado" not in caplog.text
    assert exc.value.__suppress_context__
    assert spawn.call_count == len(respostas) + 1


def test_worker_usa_amostras_float_e_modelo_local(modelo, monkeypatch):
    # O venv de integração não precisa de NumPy nem faster-whisper para o teste.
    amostras = object()
    array = Mock()

    class FloatArray:
        def __truediv__(self, divisor):
            assert divisor == 32768
            return amostras

    array.astype.return_value = FloatArray()
    np = SimpleNamespace(frombuffer=Mock(return_value=array), float32=object())
    instancia = SimpleNamespace(
        supported_languages=["pt"],
        feature_extractor=SimpleNamespace(sampling_rate=16000),
        transcribe=Mock(return_value=(iter([
            SimpleNamespace(text="   Olá "),
            SimpleNamespace(text=" "),
            SimpleNamespace(text=" mundo! "),
        ]), None)),
    )
    factory = Mock(return_value=instancia)
    monkeypatch.setitem(sys.modules, "numpy", np)
    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=factory))

    assert modulo._inferir(b"\0\0", modelo, "pt") == "Olá mundo!"
    np.frombuffer.assert_called_once_with(b"\0\0", dtype="<i2")
    array.astype.assert_called_once_with(np.float32)
    factory.assert_called_once_with(
        str(modelo), local_files_only=True, device="cpu", compute_type="int8",
        cpu_threads=2, num_workers=1,
    )
    assert instancia.transcribe.call_args.args == (amostras,)
    assert instancia.transcribe.call_args.kwargs["language"] == "pt"


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg opcional")
def test_ffmpeg_real_aceita_exatamente_o_limite_e_recusa_uma_amostra_a_mais(modelo, monkeypatch):
    transcritor = TranscritorOffline(modelo, max_duracao_segundos=1)
    executar = transcritor._executar

    def sem_asr(comando, dados, *, etapa, timeout):
        if etapa == "conversao":
            return executar(comando, dados, etapa=etapa, timeout=timeout)
        assert len(dados) == 32_000
        return b"fala sintetica"

    def wav(amostras):
        saida = io.BytesIO()
        with wave.open(saida, "wb") as arquivo:
            arquivo.setparams((1, 2, 16_000, amostras, "NONE", "not compressed"))
            arquivo.writeframes(b"\0\0" * amostras)
        return saida.getvalue()

    monkeypatch.setattr(transcritor, "_executar", sem_asr)
    assert transcritor.transcrever(wav(16_000)) == "fala sintetica"
    with pytest.raises(ErroTranscricaoOffline, match="pcm_invalido"):
        transcritor.transcrever(wav(16_001))
    with pytest.raises(ErroTranscricaoOffline, match="conversao_falhou"):
        transcritor.transcrever(b"isto nao e WAV")
