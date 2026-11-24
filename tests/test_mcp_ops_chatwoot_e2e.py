"""Prova opt-in pelo cliente stdio real, com Chatwoot e estado isolados."""
from __future__ import annotations

import asyncio
import base64
import os
from pathlib import Path
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

_OPT_IN = "TUTTIBOM_TEST_CHATWOOT_LAB"
_FUNCOES = ["01.01", "01.02"]
_CLIENTES = ("ana-titular", "ana-sucessora")
_TEXTO = "Prova fictícia pelo MCP. Vi a imagem recebida."


def _rodar_host() -> None:
    from tuttibom.mcp_ops.chatwoot_backend_lab import ChatwootBackendLab
    from tuttibom.mcp_ops.cli import _servir, _travar_estado
    from tuttibom.mcp_ops.entregas_duraveis import DiarioEntregas
    from tuttibom.mcp_ops.fila_persistente import FilaPersistente
    from tuttibom.mcp_ops.laboratorio import BackendsAtendimento

    if os.environ.get(_OPT_IN) != "1":
        raise SystemExit("Chatwoot isolado requer opt-in")
    sockets, estado, conta, inbox, conversa = sys.argv[1:]
    pasta = Path(estado)
    with _travar_estado(pasta):
        chat = ChatwootIsolado(TransporteNamespace(), conta_id=conta, inbox_id=inbox)
        backend = ChatwootBackendLab(chat, conversa_ref=conversa)
        fila = FilaPersistente(pasta / "fila.sqlite", inbox_ref=f"chatwoot-lab-{inbox}")
        diario = DiarioEntregas(pasta / "entregas.sqlite")
        diario.recuperar_reservas()
        backend.importar_incoming_publicos(fila)
        backends = BackendsAtendimento(fila, backend, backend, None, diario)
        asyncio.run(_servir(Path(sockets), _CLIENTES, None, backends=backends))


@pytest.mark.skipif(os.environ.get(_OPT_IN) != "1", reason="Chatwoot isolado opt-in")
def test_ops_chatwoot_reinicio_e_sucessao():
    conta, inbox = preparar_chatwoot()
    chat = ChatwootIsolado(TransporteNamespace(), conta_id=conta, inbox_id=inbox)
    contato = f"mcp-e2e-{uuid.uuid4().hex[:12]}"
    aberta = chat.abrir_conversa(contato)
    assert aberta["ok"], aberta
    conversa = aberta["conversa_ref"]
    entradas = [
        chat.enviar_entrada_imagem(contato_ref=contato, conversa_ref=conversa, imagem=png)
        for png in (PNG_ENTRADA, PNG_SAIDA)
    ]
    assert all(e["ok"] for e in entradas), [e["codigo"] for e in entradas]
    ids_entrada = [e["message_ref"].removeprefix("msg-") for e in entradas]

    async def turno(dir_, admin, nome, chave, apos_reinicio):
        aut = admin("autorizar", "--agente", nome, "--funcoes", ",".join(_FUNCOES))
        async with cliente(
            "tuttibom-ops-mcp", "--laboratorio", str(dir_), "--cliente", nome, prazo_sessao=110,
        ) as (ops, _):
            ligado = await dados(ops, "ops_ativar", referencia=aut["referencia"], funcoes=_FUNCOES)
            m = ligado["manifesto"]
            for skill in m["skills"]:
                await dados(ops, "ops_ler_skill", id=skill["id"])
            await dados(ops, "ops_confirmar_atribuicoes", manifesto_hash=m["hash"], resumo="Li as skills.")
            pendentes = (await dados(ops, "ops_atendimento_listar_pendencias"))["pendencias"]
            assert [p["message_id"] for p in pendentes] == (ids_entrada[1:] if apos_reinicio else ids_entrada)
            assert all(p["conversation_id"] == conversa for p in pendentes)
            leitura = await ops.call_tool("ops_atendimento_ler_conversa", {"conversa_ref": conversa})
            assert not leitura.isError, leitura.structuredContent
            msgs = leitura.structuredContent["mensagens"]
            imagens = [m["anexos"][0] for m in msgs if m["direcao"] == "incoming"]
            assert all(m["texto"] == "" for m in msgs if m["direcao"] == "incoming")
            assert [base64.b64decode(leitura.content[a["bloco_mcp"]].data) for a in imagens] == [
                PNG_ENTRADA, PNG_SAIDA,
            ]
            if apos_reinicio:
                assert [m["texto"] for m in msgs if m["direcao"] == "outgoing"] == [_TEXTO]
            rascunho = await dados(
                ops, "ops_atendimento_preparar_resposta", conversa_ref=conversa,
                texto=_TEXTO, imagem_ref=imagens[0]["midia_ref"], message_ids=ids_entrada[:1],
                idempotency_key=chave, imagens_lidas=[a["sha256"] for a in imagens],
            )
            ref = rascunho["rascunho_ref"]
            await dados(ops, "ops_atendimento_responder", "aprovacao_exata_necessaria", rascunho_ref=ref)
            prova = {"rascunho_ref": ref, "conversa_ref": conversa, "texto": _TEXTO,
                     "imagem_base64": base64.b64encode(PNG_ENTRADA).decode()}
            assert admin("aprovar-resposta", entrada={**prova, "texto": _TEXTO + " "},
                         rc=1)["codigo"] == "conteudo_divergente"
            assert admin("aprovar-resposta", entrada={
                **prova, "imagem_base64": base64.b64encode(PNG_SAIDA).decode(),
            }, rc=1)["codigo"] == "conteudo_divergente"
            aprovacao = admin("aprovar-resposta", entrada=prova)["aprovacao_ref"]
            envio = await dados(ops, "ops_atendimento_responder", rascunho_ref=ref, aprovacao_ref=aprovacao)
            assert envio["enviado"] and envio["acked"] == ids_entrada[:1]
            assert envio["replay"] is apos_reinicio
            assert admin("revogar", "--agente", nome)["revogados"] == 1
            await dados(ops, "ops_ler_skill", "token_revogado", id="ops-ana-resposta")
            return envio["envio_ref"]

    with tempfile.TemporaryDirectory(prefix="tb-ops-real-") as tmp:
        estado = Path(tmp) / "estado"

        def partida(dir_):
            return [sys.executable, str(Path(__file__).resolve()), str(dir_), str(estado),
                    conta, inbox, conversa]

        with laboratorio(*_CLIENTES, comando_host=partida) as (dir_, admin):
            primeiro = anyio.run(turno, dir_, admin, _CLIENTES[0], "chave-original", False)
        with laboratorio(*_CLIENTES, comando_host=partida) as (dir_, admin):
            segundo = anyio.run(turno, dir_, admin, _CLIENTES[1], "chave-alternativa", True)
        assert primeiro == segundo

    historico = chat.ler_historico(conversa)
    assert historico["ok"], historico["codigo"]
    enviadas = [m for m in historico["mensagens"] if m["direcao"] == "outgoing"]
    assert len(enviadas) == 1 and enviadas[0]["texto"] == _TEXTO
    assert enviadas[0]["anexos"][0]["conteudo"] == PNG_ENTRADA


if __name__ == "__main__":
    _rodar_host()
