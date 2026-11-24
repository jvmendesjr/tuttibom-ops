"""Prova integrada opt-in: cerca do piloto, operador autenticado e áudio offline.

Sem canal real: o Chatwoot é o lab isolado em Docker e o áudio é sintetizado
localmente. Nada aqui fala com produção nem com o listener vivo.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import uuid

import anyio
import pytest

from test_mcp_ops_chatwoot_isolado import (
    PNG_ENTRADA,
    PNG_SAIDA,
    TransporteNamespace,
    preparar_chatwoot,
)
from test_mcp_ops_stdio import cliente, dados, laboratorio
from tuttibom.mcp_ops.chatwoot_isolado import ChatwootIsolado
from tuttibom.mcp_ops.piloto_conversa import EscopoPiloto, permite_envio_legado

_OPT_CHATWOOT = "TUTTIBOM_TEST_CHATWOOT_LAB"
_OPT_WHISPER = "TUTTIBOM_TEST_WHISPER"
_FUNCOES = ["01.01", "01.02"]
_TEXTO1 = "Prova piloto: primeira resposta aprovada. [LAB]"
_TEXTO2 = "Prova piloto: segunda resposta, após reativar a cerca. [LAB]"


def _rodar_host_piloto(argv) -> None:
    from tuttibom.mcp_ops.cli import _servir, _travar_estado
    from tuttibom.mcp_ops.entregas_duraveis import DiarioEntregas
    from tuttibom.mcp_ops.laboratorio import BackendsAtendimento
    from tuttibom.mcp_ops.piloto_conversa import BackendPilotoChatwoot, EntradaPiloto

    if os.environ.get(_OPT_CHATWOOT) != "1":
        raise SystemExit("Chatwoot isolado requer opt-in")
    sockets, estado, conta, inbox, conversa, digests, ids_csv, outra, outra_msg = argv
    pasta = Path(estado)
    with _travar_estado(pasta):
        escopo = EscopoPiloto(conta, inbox, conversa)
        marcador = pasta / "piloto.json"
        marcador.write_text(json.dumps({"ativo": True}))

        def obter_escopo_ativo():
            dados_marcador = json.loads(marcador.read_text())
            return escopo if dados_marcador.get("ativo") is True else None

        entrada = EntradaPiloto(pasta / "fila.sqlite", escopo=escopo,
                                obter_escopo_ativo=obter_escopo_ativo)
        chat = ChatwootIsolado(TransporteNamespace(), conta_id=conta, inbox_id=inbox)
        backend = BackendPilotoChatwoot(entrada, chat)
        ids = ids_csv.split(",")
        eventos = [
            {"account_id": conta, "inbox_id": inbox, "conversation_id": conversa,
             "message_id": ids[0], "message_type": "incoming", "private": False},
            {"account_id": conta, "inbox_id": inbox, "conversation_id": conversa,
             "message_id": ids[1], "message_type": "incoming", "private": False},
            {"account_id": conta, "inbox_id": inbox, "conversation_id": outra,
             "message_id": outra_msg, "message_type": "incoming", "private": False},
            {"account_id": conta, "inbox_id": inbox, "conversation_id": conversa,
             "message_id": ids[0], "message_type": "incoming", "private": True},
        ]
        resultados = [entrada.receber(evento) for evento in eventos]
        (pasta / "receber.json").write_text(json.dumps(resultados))
        diario = DiarioEntregas(pasta / "entregas.sqlite")
        diario.recuperar_reservas()
        digest = json.loads(Path(digests).read_text())["operador-lab"]
        backends = BackendsAtendimento(entrada, backend, backend, None, diario)
        asyncio.run(_servir(Path(sockets), ("ana-piloto",), None, backends=backends,
                            digest_operador=digest))


def _rodar_host_audio(argv) -> None:
    from tuttibom.mcp_ops.atendimento import EnvioNaoEfetuado
    from tuttibom.mcp_ops.cli import _servir, _travar_estado
    from tuttibom.mcp_ops.entregas_duraveis import DiarioEntregas
    from tuttibom.mcp_ops.fila_persistente import FilaPersistente
    from tuttibom.mcp_ops.laboratorio import BackendsAtendimento
    from tuttibom.mcp_ops.transcricao_offline import TranscritorOffline

    if os.environ.get(_OPT_WHISPER) != "1":
        raise SystemExit("Transcrição offline requer opt-in")
    sockets, estado, wav, modelo, python_exe = argv
    pasta = Path(estado)

    class BackendAudio:
        """Uma conversa com um anexo de áudio real; envio sempre recusado."""

        def __init__(self) -> None:
            self._audio = Path(wav).read_bytes()
            self._mensagens = [
                {"direcao": "outgoing", "texto": "Olá! [LAB]", "anexos": []},
                {"direcao": "incoming", "texto": "",
                 "anexos": [{"file_type": "audio", "midia_ref": "voz-1"}]},
            ]

        def ler_mensagens(self, conversa_ref):
            if conversa_ref != "7":
                return None
            return [dict(m, anexos=[dict(a) for a in m["anexos"]]) for m in self._mensagens]

        def obter_audio(self, midia_ref):
            if midia_ref != "voz-1":
                raise KeyError(midia_ref)
            return self._audio

        def obter_imagem(self, midia_ref):
            raise KeyError(midia_ref)

        def geracao(self, conversa_ref):
            return 1

        def enviar(self, *, conversa_ref, texto, imagem, idempotency_key):
            raise EnvioNaoEfetuado("destino_indisponivel")

    with _travar_estado(pasta):
        fila = FilaPersistente(pasta / "fila.sqlite", inbox_ref="audio-lab")
        fila.registrar(message_id="11", conversation_id="7")
        diario = DiarioEntregas(pasta / "entregas.sqlite")
        diario.recuperar_reservas()
        backend = BackendAudio()
        transcritor = TranscritorOffline(Path(modelo), python_executavel=python_exe)
        backends = BackendsAtendimento(fila, backend, backend, transcritor, diario)
        asyncio.run(_servir(Path(sockets), ("ana-audio",), None, backends=backends))


def _credenciais(tmp: Path):
    segredo = secrets.token_hex(32)
    digest_srv = tmp / "operador.json"
    digest_srv.touch(mode=0o600)
    import hashlib
    digest_srv.write_text(json.dumps({
        "operador-lab": hashlib.sha256(segredo.encode()).hexdigest(),
    }))
    cred = tmp / "operador"
    cred.touch(mode=0o600)
    cred.write_text(segredo + "\n")
    return segredo, digest_srv, cred


@pytest.mark.skipif(os.environ.get(_OPT_CHATWOOT) != "1", reason="Chatwoot isolado opt-in")
def test_piloto_chatwoot_com_operador_autenticado():
    conta, inbox = preparar_chatwoot()
    chat = ChatwootIsolado(TransporteNamespace(), conta_id=conta, inbox_id=inbox)
    contato = f"mcp-piloto-{uuid.uuid4().hex[:12]}"
    conversa = chat.abrir_conversa(contato)["conversa_ref"]
    entradas = [
        chat.enviar_entrada_imagem(contato_ref=contato, conversa_ref=conversa, imagem=png)
        for png in (PNG_ENTRADA, PNG_SAIDA)
    ]
    assert all(e["ok"] for e in entradas), [e["codigo"] for e in entradas]
    ids = [e["message_ref"].removeprefix("msg-") for e in entradas]
    fora_contato = f"mcp-fora-{uuid.uuid4().hex[:12]}"
    outra = chat.abrir_conversa(fora_contato)["conversa_ref"]
    saida_fora = chat.enviar_entrada_imagem(contato_ref=fora_contato, conversa_ref=outra,
                                            imagem=PNG_ENTRADA)
    assert saida_fora["ok"], saida_fora
    outra_msg = saida_fora["message_ref"].removeprefix("msg-")

    escopo = EscopoPiloto(conta, inbox, conversa)
    assert not permite_envio_legado(escopo, conta_id=conta, inbox_id=inbox, conversa_id=conversa)
    assert permite_envio_legado(escopo, conta_id=conta, inbox_id=inbox, conversa_id=outra)
    assert permite_envio_legado(None, conta_id=conta, inbox_id=inbox, conversa_id=conversa)
    assert not permite_envio_legado(escopo, conta_id="ilegivel", inbox_id=inbox,
                                    conversa_id=conversa)

    with tempfile.TemporaryDirectory(prefix="tb-ops-piloto-") as tmp:
        tmp_path = Path(tmp)
        segredo, digest_srv, cred = _credenciais(tmp_path)
        estado = tmp_path / "estado"

        def partida(dir_):
            return [sys.executable, str(Path(__file__).resolve()), str(dir_), str(estado),
                    conta, inbox, conversa, str(digest_srv), ",".join(ids), outra, outra_msg]

        with laboratorio("ana-piloto", comando_host=partida) as (dir_, admin):
            resultados = json.loads((estado / "receber.json").read_text())
            assert resultados == [
                {"ok": True, "inserido": True, "codigo": None},
                {"ok": True, "inserido": True, "codigo": None},
                {"ok": False, "inserido": False, "codigo": "fora_do_piloto"},
                {"ok": False, "inserido": False, "codigo": "evento_nao_publico_incoming"},
            ]
            auth = ("--credencial-operador", str(cred))
            negado = {"ok": False, "codigo": "operador_nao_autenticado"}
            assert admin("autorizar", "--agente", "ana-piloto", "--funcoes",
                         ",".join(_FUNCOES), rc=1) == negado
            aut = admin(*auth, "autorizar", "--agente", "ana-piloto",
                        "--funcoes", ",".join(_FUNCOES))

            async def turno():
                lab = ("--laboratorio", str(dir_), "--cliente")
                async with cliente("tuttibom-ops-mcp", *lab, "ana-piloto",
                                   prazo_sessao=110) as (ops, _):
                    ligado = await dados(ops, "ops_ativar", referencia=aut["referencia"],
                                         funcoes=_FUNCOES)
                    for skill in ligado["manifesto"]["skills"]:
                        await dados(ops, "ops_ler_skill", id=skill["id"])
                    await dados(ops, "ops_confirmar_atribuicoes",
                                manifesto_hash=ligado["manifesto"]["hash"],
                                resumo="Li as skills do piloto.")
                    pendentes = (await dados(ops, "ops_atendimento_listar_pendencias"))["pendencias"]
                    assert [p["message_id"] for p in pendentes] == ids
                    fora_resp = await ops.call_tool("ops_atendimento_ler_conversa",
                                                    {"conversa_ref": outra})
                    assert fora_resp.isError
                    leitura = await ops.call_tool("ops_atendimento_ler_conversa",
                                                  {"conversa_ref": conversa})
                    assert not leitura.isError, leitura.structuredContent
                    msgs = leitura.structuredContent["mensagens"]
                    imagens = [m["anexos"][0] for m in msgs if m["direcao"] == "incoming"]
                    lidas = [a["sha256"] for a in imagens]
                    rasc1 = await dados(ops, "ops_atendimento_preparar_resposta",
                                        conversa_ref=conversa, texto=_TEXTO1,
                                        imagem_ref=imagens[0]["midia_ref"],
                                        message_ids=ids[:1], idempotency_key="piloto-1",
                                        imagens_lidas=lidas)
                    prova1 = {"conversa_ref": conversa, "rascunho_ref": rasc1["rascunho_ref"],
                              "texto": _TEXTO1,
                              "imagem_base64": base64.b64encode(PNG_ENTRADA).decode()}
                    assert admin("aprovar-resposta", entrada=prova1, rc=1) == negado
                    assert admin(*auth, "aprovar-resposta",
                                 entrada={**prova1, "texto": _TEXTO1 + " "},
                                 rc=1)["codigo"] == "conteudo_divergente"
                    apr1 = admin(*auth, "aprovar-resposta", entrada=prova1)["aprovacao_ref"]
                    envio1 = await dados(ops, "ops_atendimento_responder",
                                         rascunho_ref=prova1["rascunho_ref"],
                                         aprovacao_ref=apr1)
                    assert envio1["enviado"] and envio1["acked"] == ids[:1]

                    releitura = await ops.call_tool("ops_atendimento_ler_conversa",
                                                    {"conversa_ref": conversa})
                    assert not releitura.isError, releitura.structuredContent
                    msgs2 = releitura.structuredContent["mensagens"]
                    imagens2 = [m["anexos"][0] for m in msgs2 if m["direcao"] == "incoming"]
                    lidas2 = [a["sha256"] for a in imagens2]
                    rasc2 = await dados(ops, "ops_atendimento_preparar_resposta",
                                        conversa_ref=conversa, texto=_TEXTO2,
                                        imagem_ref=imagens2[0]["midia_ref"],
                                        message_ids=ids[1:], idempotency_key="piloto-2",
                                        imagens_lidas=lidas2)
                    prova2 = {"conversa_ref": conversa, "rascunho_ref": rasc2["rascunho_ref"],
                              "texto": _TEXTO2,
                              "imagem_base64": base64.b64encode(PNG_ENTRADA).decode()}
                    apr2 = admin(*auth, "aprovar-resposta", entrada=prova2)["aprovacao_ref"]
                    (estado / "piloto.json").write_text(json.dumps({"ativo": False}))
                    assert (await dados(ops, "ops_atendimento_listar_pendencias"))["pendencias"] == []
                    await dados(ops, "ops_atendimento_responder", "conversa_fora_do_piloto",
                                rascunho_ref=prova2["rascunho_ref"], aprovacao_ref=apr2)
                    (estado / "piloto.json").write_text(json.dumps({"ativo": True}))
                    envio2 = await dados(ops, "ops_atendimento_responder",
                                         rascunho_ref=prova2["rascunho_ref"],
                                         aprovacao_ref=apr2)
                    assert envio2["enviado"] and envio2["acked"] == ids[1:]
                    assert admin("revogar", "--agente", "ana-piloto", rc=1) == negado
                    assert admin(*auth, "revogar", "--agente", "ana-piloto")["revogados"] >= 1
                    assert segredo not in json.dumps(admin(*auth, "auditoria"))

            anyio.run(turno)

    historico = chat.ler_historico(conversa)
    assert historico["ok"], historico["codigo"]
    enviadas = [m["texto"] for m in historico["mensagens"] if m["direcao"] == "outgoing"]
    assert enviadas == [_TEXTO1, _TEXTO2]
    historico_fora = chat.ler_historico(outra)
    assert [m for m in historico_fora["mensagens"] if m["direcao"] == "outgoing"] == []


def _insumos_whisper():
    if os.environ.get(_OPT_WHISPER) != "1":
        pytest.skip("transcrição offline opt-in")
    espeak = shutil.which("espeak-ng")
    if espeak is None:
        pytest.skip("espeak-ng ausente")
    hub = Path.home() / ".cache/huggingface/hub"
    modelos = sorted(hub.glob("models--Systran--faster-whisper-small/snapshots/*/model.bin"))
    if not modelos:
        pytest.skip("modelo faster-whisper small não encontrado no cache local")
    raiz = Path(__file__).resolve().parents[1]
    for candidato in (Path("/home/pc/.venvs/whisper/bin/python"), raiz / ".venv/bin/python"):
        if not candidato.exists():
            continue
        probe = subprocess.run(
            [str(candidato), "-I", "-c", "import faster_whisper, numpy"],
            capture_output=True, timeout=60,
        )
        if probe.returncode == 0:
            return espeak, modelos[0].parent, str(candidato)
    pytest.skip("nenhum python com faster-whisper + numpy")


def test_audio_offline_real_no_pipeline(tmp_path):
    espeak, modelo, python_exe = _insumos_whisper()
    wav = tmp_path / "voz.wav"
    frase = "Bom dia, quero fazer um pedido de vinte canecas."
    subprocess.run([espeak, "-v", "pt-br", "-w", str(wav), frase], check=True, timeout=30)
    estado = tmp_path / "estado"

    def partida(dir_):
        return [sys.executable, str(Path(__file__).resolve()), "audio", str(dir_), str(estado),
                str(wav), str(modelo), python_exe]

    with laboratorio("ana-audio", comando_host=partida) as (dir_, admin):
        aut = admin("autorizar", "--agente", "ana-audio", "--funcoes", ",".join(_FUNCOES))

        async def turno():
            lab = ("--laboratorio", str(dir_), "--cliente")
            async with cliente("tuttibom-ops-mcp", *lab, "ana-audio",
                               prazo_sessao=110) as (ops, _):
                ligado = await dados(ops, "ops_ativar", referencia=aut["referencia"],
                                     funcoes=_FUNCOES)
                for skill in ligado["manifesto"]["skills"]:
                    await dados(ops, "ops_ler_skill", id=skill["id"])
                await dados(ops, "ops_confirmar_atribuicoes",
                            manifesto_hash=ligado["manifesto"]["hash"],
                            resumo="Li as skills do piloto de áudio.")
                pendentes = (await dados(ops, "ops_atendimento_listar_pendencias"))["pendencias"]
                assert [p["message_id"] for p in pendentes] == ["11"]
                leitura = await ops.call_tool("ops_atendimento_ler_conversa",
                                              {"conversa_ref": "7"})
                assert not leitura.isError, leitura.structuredContent
                anexo = leitura.structuredContent["mensagens"][1]["anexos"][0]
                transcricao = anexo["transcricao"].lower()
                assert any(p in transcricao for p in ("pedido", "vinte")), transcricao

        anyio.run(turno)


if __name__ == "__main__":
    if sys.argv[1] == "audio":
        _rodar_host_audio(sys.argv[2:])
    else:
        _rodar_host_piloto(sys.argv[1:])
