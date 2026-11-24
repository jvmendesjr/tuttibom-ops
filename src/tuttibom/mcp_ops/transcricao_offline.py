"""Transcritor opcional do laboratório, sem download e sem persistência de mídia."""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

_TAXA = 16_000
_BYTES_POR_SEGUNDO = 2 * _TAXA  # PCM s16le, mono
_MAX_TEXTO = 16_384
_FORMATOS = "aac,flac,matroska,webm,mov,mp4,m4a,3gp,3g2,mj2,mp3,ogg,wav"
_AMBIENTE_OFFLINE = {
    "HF_HUB_OFFLINE": "1",
    "HF_HUB_DISABLE_TELEMETRY": "1",
    "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
    "TRANSFORMERS_OFFLINE": "1",
}


class ErroTranscricaoOffline(RuntimeError):
    """Falha fechada; a mensagem não inclui saída dos subprocessos nem mídia."""


def _validar_modelo(pasta: Path) -> None:
    # faster-whisper tenta carregar um tokenizer remoto se não houver um local,
    # mesmo com local_files_only=True no construtor.
    def arquivo_local(nome: str) -> bool:
        arquivo = pasta / nome
        return arquivo.is_file() and arquivo.stat().st_size > 0

    if (
        not pasta.is_absolute()
        or not pasta.is_dir()
        or not all(arquivo_local(nome) for nome in ("model.bin", "config.json", "tokenizer.json"))
        or not any(arquivo_local(nome) for nome in ("vocabulary.txt", "vocabulary.json"))
    ):
        raise ErroTranscricaoOffline("modelo_local_incompleto")


def _executavel(caminho: str | Path | None) -> str:
    if not caminho:
        raise ErroTranscricaoOffline("executavel_indisponivel")
    local = Path(caminho)
    if not local.is_absolute() or not local.is_file() or not os.access(local, os.X_OK):
        raise ErroTranscricaoOffline("executavel_indisponivel")
    # Não resolver symlinks: o caminho do bin/python identifica o venv.
    return str(local)


def _limpar_texto(texto: str) -> str:
    if (
        len(texto) > _MAX_TEXTO
        or "\ufffd" in texto
        or any(not (c.isprintable() or c in "\t\n\r") for c in texto)
        or not any(c.isalnum() for c in texto)
    ):
        raise ErroTranscricaoOffline("transcricao_invalida")
    return " ".join(texto.split())


class TranscritorOffline:
    """Adapter do protocolo Transcritor, ativado só com um modelo local.

    `python_executavel` pode apontar ao bin/python absoluto de um venv separado
    com faster-whisper e NumPy. Cada chamada carrega o modelo em um processo
    CPU/int8 novo, com timeout próprio e stderr descartado.
    """

    def __init__(
        self,
        modelo_dir: str | Path,
        *,
        python_executavel: str | Path | None = None,
        ffmpeg_executavel: str | Path | None = None,
        max_audio_bytes: int = 8 * 1024 * 1024,
        max_duracao_segundos: int = 60,
        timeout_conversao: float = 10,
        timeout_transcricao: float = 45,
    ) -> None:
        if (
            type(max_audio_bytes) is not int
            or max_audio_bytes <= 0
            or type(max_duracao_segundos) is not int
            or max_duracao_segundos <= 0
            or not (math.isfinite(timeout_conversao) and timeout_conversao > 0)
            or not (math.isfinite(timeout_transcricao) and timeout_transcricao > 0)
        ):
            raise ValueError("limites_de_transcricao_invalidos")
        try:
            modelo = Path(modelo_dir)
            if not modelo.is_absolute():
                raise ErroTranscricaoOffline("modelo_local_incompleto")
            self._modelo = modelo.resolve(strict=True)
            _validar_modelo(self._modelo)
            self._python = _executavel(python_executavel if python_executavel is not None else sys.executable)
            self._ffmpeg = _executavel(
                ffmpeg_executavel if ffmpeg_executavel is not None else shutil.which("ffmpeg")
            )
        except (OSError, ValueError):
            raise ErroTranscricaoOffline("configuracao_offline_invalida") from None
        self._max_audio_bytes = max_audio_bytes
        self._max_duracao = max_duracao_segundos
        self._max_pcm = max_duracao_segundos * _BYTES_POR_SEGUNDO
        self._timeout_conversao = timeout_conversao
        self._timeout_transcricao = timeout_transcricao

    @staticmethod
    def _executar(
        comando: list[str], dados: bytes, *, timeout: float, etapa: str
    ) -> bytes:
        try:
            return subprocess.run(
                comando,
                input=dados,
                timeout=timeout,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=True,
                env=_AMBIENTE_OFFLINE,
            ).stdout
        except subprocess.TimeoutExpired:
            raise ErroTranscricaoOffline(f"{etapa}_timeout") from None
        except (OSError, subprocess.CalledProcessError, ValueError):
            raise ErroTranscricaoOffline(f"{etapa}_falhou") from None

    def transcrever(self, audio: bytes, *, idioma: str = "pt") -> str:
        if not isinstance(audio, bytes) or not 0 < len(audio) <= self._max_audio_bytes:
            raise ErroTranscricaoOffline("audio_invalido")
        if not isinstance(idioma, str) or re.fullmatch(r"[a-z]{2,3}", idioma) is None:
            raise ErroTranscricaoOffline("idioma_invalido")

        # O relógio da saída é reconstruído a partir do número de amostras,
        # e não dos timestamps do arquivo. Convertemos até um segundo além
        # do limite para recusar, em vez de transcrever áudio truncado.
        pcm = self._executar(
            [
                self._ffmpeg, "-nostdin", "-loglevel", "error", "-xerror",
                "-protocol_whitelist", "pipe", "-format_whitelist", _FORMATOS,
                "-threads", "1", "-i", "pipe:0",
                "-map", "0:a:0", "-vn", "-sn", "-dn", "-filter_threads", "1",
                "-af", f"aresample={_TAXA},asetpts=N/SR/TB",
                "-t", str(self._max_duracao + 1),
                "-ac", "1", "-ar", str(_TAXA), "-c:a", "pcm_s16le", "-f", "s16le", "pipe:1",
            ],
            audio,
            timeout=self._timeout_conversao,
            etapa="conversao",
        )
        if not 0 < len(pcm) <= self._max_pcm or len(pcm) % 2:
            raise ErroTranscricaoOffline("pcm_invalido")

        bruto = self._executar(
            [
                self._python, "-I", "-B", str(Path(__file__).resolve()),
                str(self._modelo), idioma, str(self._max_pcm),
            ],
            pcm,
            timeout=self._timeout_transcricao,
            etapa="transcricao",
        )
        if len(bruto) > 4 * _MAX_TEXTO:
            raise ErroTranscricaoOffline("transcricao_invalida")
        try:
            return _limpar_texto(bruto.decode("utf-8"))
        except UnicodeError:
            raise ErroTranscricaoOffline("transcricao_invalida") from None


def _inferir(pcm: bytes, modelo: Path, idioma: str) -> str:
    # Imports opcionais no processo isolado. O ndarray evita o caminho de
    # decodificação PyAV (inclusive seus erros de metadados com certos WAVs).
    _validar_modelo(modelo)
    import numpy as np
    from faster_whisper import WhisperModel

    whisper = WhisperModel(
        str(modelo), local_files_only=True, device="cpu", compute_type="int8",
        cpu_threads=2, num_workers=1,
    )
    if idioma not in whisper.supported_languages or whisper.feature_extractor.sampling_rate != _TAXA:
        raise ErroTranscricaoOffline("modelo_incompativel")
    amostras = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768
    segmentos, _ = whisper.transcribe(
        amostras, language=idioma, task="transcribe", beam_size=3,
        temperature=0, condition_on_previous_text=False, vad_filter=True,
    )
    partes = []
    tamanho = 0
    for segmento in segmentos:
        parte = segmento.text.strip()
        if parte:
            tamanho += len(parte) + bool(partes)
            if tamanho > _MAX_TEXTO:
                raise ErroTranscricaoOffline("transcricao_invalida")
            partes.append(parte)
    return _limpar_texto(" ".join(partes))


def _worker() -> int:
    try:
        _, modelo, idioma, limite = sys.argv
        max_pcm = int(limite)
        if max_pcm <= 0 or os.environ.get("HF_HUB_OFFLINE") != "1":
            return 1
        pcm = sys.stdin.buffer.read(max_pcm + 1)
        if not 0 < len(pcm) <= max_pcm or len(pcm) % 2:
            return 1
        resultado = _inferir(pcm, Path(modelo), idioma)
        sys.stdout.buffer.write(resultado.encode("utf-8"))
    except Exception:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_worker())
