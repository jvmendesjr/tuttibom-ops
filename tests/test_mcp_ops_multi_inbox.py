"""Composição multi-inbox pela entrada Conexao, somente com dados sintéticos."""
from __future__ import annotations

import anyio
import base64
import os
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from tuttibom.mcp_ops.atendimento import (
    ChatwootLaboratorio,
    FilaLaboratorio,
    SimuladorAtendimento,
)
from tuttibom.mcp_ops.entregas_duraveis import DiarioEntregas
from tuttibom.mcp_ops.fila_persistente import FilaPersistente
from tuttibom.mcp_ops.laboratorio import (
    CONVERSA,
    IMAGEM_REF,
    PNG,
    BackendsAtendimento,
    Laboratorio,
    RecusaLab,
)
from tuttibom.mcp_ops.transporte import Conexao

CONVERSA_COLIDIDA = "77"
MENSAGEM_COLIDIDA = "900"
FUNCOES = ["01.01", "01.02"]


@dataclass
class Componentes:
    backends: BackendsAtendimento
    fila: FilaLaboratorio
    chat: ChatwootLaboratorio
    destino: SimuladorAtendimento
    diario: DiarioEntregas


def _componentes(
    tmp_path: Path,
    nome: str,
    *,
    inbox_id: str = "1",
    conversa: str = CONVERSA_COLIDIDA,
    message_ids: tuple[str, ...] = (MENSAGEM_COLIDIDA,),
    configurado: bool = False,
) -> Componentes:
    fila = FilaLaboratorio()
    chat = ChatwootLaboratorio()
    destino = SimuladorAtendimento()
    chat.registrar_mensagem(conversa, direcao="incoming", texto=f"historico-{nome}")
    for message_id in message_ids:
        fila.enfileirar(
            message_id=message_id,
            conversation_id=conversa,
            inbox_id=inbox_id,
            contato_ref="contato-sintetico",
            recebido_em="2026-01-01T00:00:00Z",
        )
    if configurado:
        chat.inbox_id = inbox_id
        fila.inbox_id = inbox_id
        destino.inbox_id = inbox_id
    diario = DiarioEntregas(tmp_path / f"{nome}.sqlite")
    backends = BackendsAtendimento(fila, chat, destino, None, diario)
    return Componentes(backends, fila, chat, destino, diario)


@contextmanager
def _aberto(lab: Laboratorio):
    try:
        yield lab
    finally:
        lab.servidor.close()


@contextmanager
def _multi(
    tmp_path: Path,
    *,
    ids1: tuple[str, ...] = (MENSAGEM_COLIDIDA,),
    ids2: tuple[str, ...] = (MENSAGEM_COLIDIDA,),
):
    um = _componentes(tmp_path, "inbox-1", inbox_id="1", message_ids=ids1)
    dois = _componentes(tmp_path, "inbox-2", inbox_id="2", message_ids=ids2)
    lab = Laboratorio(backends_por_inbox={"1": um.backends, "2": dois.backends})
    with _aberto(lab):
        yield lab, um, dois


async def _chamar(conexao: Conexao, nome: str, erro: str | None = None, **args) -> dict:
    resposta = await conexao.chamar(nome, args)
    dados = resposta.structuredContent
    assert dados is not None, (nome, resposta.content)
    assert resposta.isError == (erro is not None), (nome, dados)
    if erro is not None:
        assert dados["codigo"] == erro
    return dados


async def _conectar(
    lab: Laboratorio,
    agente: str = "ana-01",
    *,
    erro_confirmacao: str | None = None,
) -> Conexao:
    autorizacao = lab.administrar("autorizar", {"agente": agente, "funcoes": FUNCOES})
    cliente = lab.clientes[agente]
    cliente.ativar(autorizacao["referencia"], FUNCOES)
    conexao = Conexao(lab, cliente, preconfigurada=True)
    manifesto = await _chamar(conexao, "ops_minhas_atribuicoes")
    for skill in manifesto["skills"]:
        await _chamar(conexao, "ops_ler_skill", id=skill["id"])
    await _chamar(
        conexao,
        "ops_confirmar_atribuicoes",
        erro_confirmacao,
        manifesto_hash=manifesto["hash"],
        resumo="Escopo sintético confirmado; aprovação exata e lease global.",
    )
    return conexao


def _argumentos_preparo(
    texto: str,
    *,
    chave: str = "mesma-chave",
    message_id: str = MENSAGEM_COLIDIDA,
    conversa: str = CONVERSA_COLIDIDA,
) -> dict:
    return {
        "conversa_ref": conversa,
        "texto": texto,
        "idempotency_key": chave,
        "message_ids": [message_id],
    }


def _aprovar(
    lab: Laboratorio,
    ref: str,
    texto: str,
    *,
    inbox_id: str | None = None,
    conversa: str = CONVERSA_COLIDIDA,
    imagem_base64: str | None = None,
) -> dict:
    args = {
        "rascunho_ref": ref,
        "conversa_ref": conversa,
        "texto": texto,
        "imagem_base64": imagem_base64,
    }
    if inbox_id is not None:
        args["inbox_id"] = inbox_id
    return lab.administrar("aprovar-resposta", args)


def test_configuracao_multi_rejeita_rotas_e_componentes_compartilhados(tmp_path: Path):
    um = _componentes(tmp_path, "um")
    dois = _componentes(tmp_path, "dois", inbox_id="2")
    with pytest.raises(ValueError, match="^backends_por_inbox_invalidos$"):
        Laboratorio(backends_por_inbox={})
    with pytest.raises(ValueError, match="^backends_por_inbox_invalidos$"):
        Laboratorio(backends_por_inbox=[])
    with pytest.raises(ValueError, match="^duas_configuracoes_de_backend$"):
        Laboratorio(backends=um.backends, backends_por_inbox={"2": dois.backends})
    with pytest.raises(ValueError, match="^duas_configuracoes_de_backend$"):
        Laboratorio(estado_dir=tmp_path / "estado", backends_por_inbox={"2": dois.backends})
    for invalido in ("", "01", "abc", "-1", 1, True, None):
        with pytest.raises(ValueError, match="^inbox_id_invalido$"):
            Laboratorio(backends_por_inbox={invalido: um.backends})
    with pytest.raises(ValueError, match="^backends_compartilhados$"):
        Laboratorio(backends_por_inbox={"1": um.backends, "2": um.backends})
    with pytest.raises(ValueError, match="^backends_compartilhados$"):
        Laboratorio(backends_por_inbox={
            "1": um.backends,
            "2": replace(dois.backends, fila=um.fila),
        })
    with pytest.raises(ValueError, match="^diario_compartilhado$"):
        Laboratorio(backends_por_inbox={
            "1": um.backends,
            "2": replace(dois.backends, diario=um.diario),
        })


def test_duas_instancias_de_diario_no_mesmo_sqlite_sao_recusadas(tmp_path: Path):
    caminho = tmp_path / "compartilhado.sqlite"
    diario1 = DiarioEntregas(caminho)
    diario2 = DiarioEntregas(caminho)
    um = _componentes(tmp_path, "um")
    dois = _componentes(tmp_path, "dois", inbox_id="2")
    with pytest.raises(ValueError, match="^diario_compartilhado$"):
        Laboratorio(backends_por_inbox={
            "1": replace(um.backends, diario=diario1),
            "2": replace(dois.backends, diario=diario2),
        })


def test_diarios_em_hardlinks_do_mesmo_sqlite_sao_recusados(tmp_path: Path):
    caminho = tmp_path / "original.sqlite"
    DiarioEntregas(caminho)
    alias = tmp_path / "alias.sqlite"
    os.link(caminho, alias)
    diario1 = DiarioEntregas(caminho)
    diario2 = DiarioEntregas(alias)
    um = _componentes(tmp_path, "um")
    dois = _componentes(tmp_path, "dois", inbox_id="2")
    with pytest.raises(ValueError, match="^diario_compartilhado$"):
        Laboratorio(backends_por_inbox={
            "1": replace(um.backends, diario=diario1),
            "2": replace(dois.backends, diario=diario2),
        })


def test_multi_rejeita_componentes_com_identidade_divergente_da_rota(tmp_path: Path):
    um = _componentes(tmp_path, "um-configurado", inbox_id="1", configurado=True)
    dois = _componentes(tmp_path, "dois-configurado", inbox_id="2", configurado=True)
    for backends in (
        dois.backends,
        replace(um.backends, fila=dois.fila),
        replace(um.backends, chat=dois.chat),
        replace(um.backends, destino=dois.destino),
    ):
        with pytest.raises(ValueError, match="^inbox_backend_divergente$"):
            Laboratorio(backends_por_inbox={"1": backends})


def test_duas_filas_no_mesmo_sqlite_ou_hardlink_sao_recusadas(tmp_path: Path):
    original = tmp_path / "fila-original.sqlite"
    alias = tmp_path / "fila-alias.sqlite"
    FilaPersistente(original, inbox_ref="canal-2-1")
    os.link(original, alias)
    um = _componentes(tmp_path, "um-fila")
    dois = _componentes(tmp_path, "dois-fila", inbox_id="2")
    for segundo_caminho in (original, alias):
        fila1 = FilaPersistente(original, inbox_ref="canal-2-1")
        fila2 = FilaPersistente(segundo_caminho, inbox_ref="canal-2-2")
        with pytest.raises(ValueError, match="^fila_compartilhada$"):
            Laboratorio(backends_por_inbox={
                "1": replace(um.backends, fila=fila1),
                "2": replace(dois.backends, fila=fila2),
            })


def test_fila_global_justa_filtro_e_inbox_ausente_invalido_ou_booleano(tmp_path: Path):
    async def cenario(lab: Laboratorio, um: Componentes, dois: Componentes):
        conexao = await _conectar(lab)
        ferramentas = {tool.name: tool for tool in await conexao.listar()}
        for nome in (
            "ops_atendimento_listar_pendencias",
            "ops_atendimento_ler_conversa",
            "ops_atendimento_preparar_resposta",
        ):
            schema = ferramentas[nome].inputSchema
            assert "inbox_id" in schema["properties"]
            assert "inbox_id" not in schema["required"]

        listagem = await _chamar(conexao, "ops_atendimento_listar_pendencias", limite=3)
        assert [(p["inbox_id"], p["message_id"]) for p in listagem["pendencias"]] == [
            ("1", "a1"), ("2", "b1"), ("1", "a2"),
        ]
        filtrada = await _chamar(
            conexao, "ops_atendimento_listar_pendencias", inbox_id="2", limite=1,
        )
        assert [(p["inbox_id"], p["message_id"]) for p in filtrada["pendencias"]] == [("2", "b1")]

        await _chamar(conexao, "ops_atendimento_ler_conversa", "inbox_obrigatorio",
                      conversa_ref=CONVERSA_COLIDIDA)
        await _chamar(conexao, "ops_atendimento_preparar_resposta", "inbox_obrigatorio",
                      **_argumentos_preparo("sem rota"))
        await _chamar(conexao, "ops_atendimento_listar_pendencias", "inbox_invalido", inbox_id="3")
        await _chamar(conexao, "ops_atendimento_ler_conversa", "inbox_invalido",
                      conversa_ref=CONVERSA_COLIDIDA, inbox_id="3")
        for nome in (
            "ops_atendimento_listar_pendencias",
            "ops_atendimento_ler_conversa",
            "ops_atendimento_preparar_resposta",
        ):
            args = {"inbox_id": True}
            if nome != "ops_atendimento_listar_pendencias":
                args.update(_argumentos_preparo("booleano"))
            await _chamar(conexao, nome, "argumento_invalido", **args)
        await _chamar(conexao, "ops_atendimento_listar_pendencias", "argumento_invalido", limite=True)

        for componentes in (um, dois):
            for message_id in ("a1", "a2", "a3") if componentes is um else ("b1", "b2"):
                assert componentes.fila.obter(message_id)["estado"] == "pendente"
                assert componentes.diario.consultar_mensagem(message_id) is None
            assert componentes.destino.envios == []

    with _multi(tmp_path, ids1=("a1", "a2", "a3"), ids2=("b1", "b2")) as (lab, um, dois):
        anyio.run(cenario, lab, um, dois)


def test_colisoes_rascunho_envio_ack_idempotencia_e_replay_ficam_no_inbox(tmp_path: Path):
    async def cenario(lab: Laboratorio, um: Componentes, dois: Componentes):
        conexao = await _conectar(lab)
        leitura1 = await _chamar(
            conexao, "ops_atendimento_ler_conversa",
            conversa_ref=CONVERSA_COLIDIDA, inbox_id="1",
        )
        leitura2 = await _chamar(
            conexao, "ops_atendimento_ler_conversa",
            conversa_ref=CONVERSA_COLIDIDA, inbox_id="2",
        )
        assert leitura1["mensagens"][0]["texto"] == "historico-inbox-1"
        assert leitura2["mensagens"][0]["texto"] == "historico-inbox-2"
        assert (leitura1["inbox_id"], leitura2["inbox_id"]) == ("1", "2")

        texto1 = "Resposta exata do inbox um."
        texto2 = "Resposta diferente com a mesma chave no inbox dois."
        preparo1 = await _chamar(
            conexao, "ops_atendimento_preparar_resposta",
            inbox_id="1", **_argumentos_preparo(texto1),
        )
        preparo2 = await _chamar(
            conexao, "ops_atendimento_preparar_resposta",
            inbox_id="2", **_argumentos_preparo(texto2),
        )
        ref1 = preparo1["rascunho_ref"]
        ref2 = preparo2["rascunho_ref"]
        assert ref1 != ref2
        assert (preparo1["inbox_id"], preparo2["inbox_id"]) == ("1", "2")
        listados = lab.administrar("listar-rascunhos", {})["rascunhos"]
        assert {item["rascunho_ref"]: item["inbox_id"] for item in listados} == {
            ref1: "1", ref2: "2",
        }
        assert lab.administrar("inspecionar-rascunho", {"rascunho_ref": ref1})["inbox_id"] == "1"
        assert lab.administrar("inspecionar-rascunho", {"rascunho_ref": ref2})["inbox_id"] == "2"
        assert um.fila.obter(MENSAGEM_COLIDIDA)["estado"] == "pendente"
        assert dois.fila.obter(MENSAGEM_COLIDIDA)["estado"] == "pendente"
        assert um.diario.consultar_mensagem(MENSAGEM_COLIDIDA) is None
        assert dois.diario.consultar_mensagem(MENSAGEM_COLIDIDA) is None

        with pytest.raises(RecusaLab, match="^inbox_obrigatorio$"):
            _aprovar(lab, ref1, texto1)
        with pytest.raises(RecusaLab, match="^rascunho_ausente$"):
            _aprovar(lab, ref1, texto1, inbox_id="2")
        with pytest.raises(RecusaLab, match="^conteudo_divergente$"):
            _aprovar(lab, ref1, texto1 + " ", inbox_id="1")
        aprovacao1 = _aprovar(lab, ref1, texto1, inbox_id="1")
        assert aprovacao1["inbox_id"] == "1"
        await _chamar(
            conexao, "ops_atendimento_responder", "aprovacao_exata_necessaria",
            rascunho_ref=ref2, aprovacao_ref=aprovacao1["aprovacao_ref"],
        )
        assert um.destino.envios == dois.destino.envios == []

        envio1 = await _chamar(
            conexao, "ops_atendimento_responder",
            rascunho_ref=ref1, aprovacao_ref=aprovacao1["aprovacao_ref"],
        )
        assert envio1["enviado"] and envio1["ack_ok"]
        assert envio1["acked"] == [MENSAGEM_COLIDIDA]
        assert envio1["inbox_id"] == "1"
        assert um.fila.obter(MENSAGEM_COLIDIDA)["estado"] == "entregue"
        assert dois.fila.obter(MENSAGEM_COLIDIDA)["estado"] == "pendente"
        assert um.diario.consultar_mensagem(MENSAGEM_COLIDIDA)["estado"] == "concluido"
        assert dois.diario.consultar_mensagem(MENSAGEM_COLIDIDA) is None
        assert len(um.destino.envios) == 1
        assert dois.destino.envios == []
        assert um.destino.envios[0]["idempotency_key"] == "mesma-chave"

        replay = await _chamar(
            conexao, "ops_atendimento_responder",
            rascunho_ref=ref1, aprovacao_ref=aprovacao1["aprovacao_ref"],
        )
        assert replay["replay"] and replay["envio_ref"] == envio1["envio_ref"]
        assert len(um.destino.envios) == 1
        assert dois.destino.envios == []

        aprovacao2 = _aprovar(lab, ref2, texto2, inbox_id="2")
        envio2 = await _chamar(
            conexao, "ops_atendimento_responder",
            rascunho_ref=ref2, aprovacao_ref=aprovacao2["aprovacao_ref"],
        )
        assert envio2["acked"] == [MENSAGEM_COLIDIDA]
        assert envio2["inbox_id"] == "2"
        assert len(um.destino.envios) == len(dois.destino.envios) == 1
        assert dois.destino.envios[0]["idempotency_key"] == "mesma-chave"
        assert dois.diario.consultar_mensagem(MENSAGEM_COLIDIDA)["estado"] == "concluido"

    with _multi(tmp_path) as (lab, um, dois):
        anyio.run(cenario, lab, um, dois)


def test_atualidade_e_limpeza_seguem_a_pilha_do_rascunho(tmp_path: Path):
    async def cenario(lab: Laboratorio, um: Componentes, dois: Componentes):
        conexao = await _conectar(lab)
        for inbox in ("1", "2"):
            await _chamar(
                conexao, "ops_atendimento_ler_conversa",
                conversa_ref=CONVERSA_COLIDIDA, inbox_id=inbox,
            )
        preparo1 = await _chamar(
            conexao, "ops_atendimento_preparar_resposta", inbox_id="1",
            **_argumentos_preparo("atual um", chave="atual-1"),
        )
        preparo2 = await _chamar(
            conexao, "ops_atendimento_preparar_resposta", inbox_id="2",
            **_argumentos_preparo("atual dois", chave="atual-2"),
        )
        dois.chat.registrar_mensagem(
            CONVERSA_COLIDIDA, direcao="incoming", texto="mudou somente o inbox dois",
        )
        aprovacao1 = _aprovar(lab, preparo1["rascunho_ref"], "atual um", inbox_id="1")
        envio = await _chamar(
            conexao, "ops_atendimento_responder",
            rascunho_ref=preparo1["rascunho_ref"],
            aprovacao_ref=aprovacao1["aprovacao_ref"],
        )
        assert envio["acked"] == [MENSAGEM_COLIDIDA]
        with pytest.raises(RecusaLab, match="^rascunho_obsoleto$"):
            _aprovar(lab, preparo2["rascunho_ref"], "atual dois", inbox_id="2")
        assert len(um.destino.envios) == 1
        assert dois.destino.envios == []
        assert dois.fila.obter(MENSAGEM_COLIDIDA)["estado"] == "pendente"
        conexao.fechar()
        assert lab.administrar("listar-rascunhos", {}) == {"rascunhos": []}

    with _multi(tmp_path) as (lab, um, dois):
        anyio.run(cenario, lab, um, dois)


def test_segundo_escritor_nao_obtem_lease_global_em_outro_inbox(tmp_path: Path):
    async def cenario(lab: Laboratorio, um: Componentes, dois: Componentes):
        primeiro = await _conectar(lab, "ana-01")
        segundo = await _conectar(lab, "ana-02", erro_confirmacao="area_ocupada")
        assert (await _chamar(primeiro, "ops_estado"))["areas"] == ["01"]
        estado2 = await _chamar(segundo, "ops_estado")
        assert not estado2["confirmado"] and estado2["areas"] == []
        await _chamar(
            segundo, "ops_atendimento_listar_pendencias", "confirmacao_pendente", inbox_id="2",
        )
        assert um.destino.envios == dois.destino.envios == []
        assert um.fila.obter(MENSAGEM_COLIDIDA)["estado"] == "pendente"
        assert dois.fila.obter(MENSAGEM_COLIDIDA)["estado"] == "pendente"

    with _multi(tmp_path) as (lab, um, dois):
        anyio.run(cenario, lab, um, dois)


def test_single_configurado_valida_inbox_explicito_e_mantem_omissao_legacy(tmp_path: Path):
    componentes = _componentes(
        tmp_path, "single-configurado", message_ids=("900", "901"), configurado=True,
    )

    async def cenario(lab: Laboratorio):
        conexao = await _conectar(lab)
        await _chamar(conexao, "ops_atendimento_listar_pendencias", "inbox_invalido", inbox_id="2")
        await _chamar(conexao, "ops_atendimento_ler_conversa", "inbox_invalido",
                      conversa_ref=CONVERSA_COLIDIDA, inbox_id="2")
        await _chamar(conexao, "ops_atendimento_preparar_resposta", "inbox_invalido",
                      inbox_id="2", **_argumentos_preparo("canal errado"))
        leitura = await _chamar(
            conexao, "ops_atendimento_ler_conversa",
            conversa_ref=CONVERSA_COLIDIDA, inbox_id="1",
        )
        assert "inbox_id" not in leitura
        preparo = await _chamar(
            conexao, "ops_atendimento_preparar_resposta", inbox_id="1",
            **_argumentos_preparo("single explícito", chave="single-1"),
        )
        assert "inbox_id" not in preparo
        aprovacao = _aprovar(lab, preparo["rascunho_ref"], "single explícito", inbox_id="1")
        assert "inbox_id" not in aprovacao
        envio = await _chamar(
            conexao, "ops_atendimento_responder",
            rascunho_ref=preparo["rascunho_ref"], aprovacao_ref=aprovacao["aprovacao_ref"],
        )
        assert envio["acked"] == ["900"] and "inbox_id" not in envio

        await _chamar(conexao, "ops_atendimento_ler_conversa", conversa_ref=CONVERSA_COLIDIDA)
        omitido = await _chamar(
            conexao, "ops_atendimento_preparar_resposta",
            **_argumentos_preparo("single omitido", chave="single-2", message_id="901"),
        )
        aprovacao2 = _aprovar(lab, omitido["rascunho_ref"], "single omitido")
        envio2 = await _chamar(
            conexao, "ops_atendimento_responder",
            rascunho_ref=omitido["rascunho_ref"], aprovacao_ref=aprovacao2["aprovacao_ref"],
        )
        assert envio2["acked"] == ["901"]
        assert componentes.fila.listar_pendentes() == []

    with _aberto(Laboratorio(backends=componentes.backends)) as lab:
        anyio.run(cenario, lab)


def test_regressao_single_sintetico_sem_inbox_e_com_imagem_exata():
    async def cenario(lab: Laboratorio):
        conexao = await _conectar(lab)
        await _chamar(conexao, "ops_atendimento_ler_conversa", "inbox_invalido",
                      conversa_ref=CONVERSA, inbox_id="1")
        pendencias = await _chamar(conexao, "ops_atendimento_listar_pendencias")
        assert len(pendencias["pendencias"]) == 2
        leitura = await _chamar(conexao, "ops_atendimento_ler_conversa", conversa_ref=CONVERSA)
        imagem = leitura["mensagens"][1]["anexos"][0]
        texto = "Resposta single com imagem exata."
        preparo = await _chamar(
            conexao, "ops_atendimento_preparar_resposta",
            conversa_ref=CONVERSA,
            texto=texto,
            idempotency_key="single-legacy",
            message_ids=["msg-lab-01"],
            imagem_ref=IMAGEM_REF,
            imagens_lidas=[imagem["sha256"]],
        )
        ref = preparo["rascunho_ref"]
        assert "inbox_id" not in lab.administrar("inspecionar-rascunho", {"rascunho_ref": ref})
        aprovacao = _aprovar(
            lab, ref, texto, conversa=CONVERSA,
            imagem_base64=base64.b64encode(PNG).decode("ascii"),
        )
        envio = await _chamar(
            conexao, "ops_atendimento_responder",
            rascunho_ref=ref, aprovacao_ref=aprovacao["aprovacao_ref"],
        )
        assert envio["acked"] == ["msg-lab-01"]
        replay = await _chamar(
            conexao, "ops_atendimento_responder",
            rascunho_ref=ref, aprovacao_ref=aprovacao["aprovacao_ref"],
        )
        assert replay["replay"] and len(lab._envios_ficticios) == 1
        restantes = await _chamar(conexao, "ops_atendimento_listar_pendencias")
        assert [item["message_id"] for item in restantes["pendencias"]] == ["msg-lab-02"]

    with _aberto(Laboratorio()) as lab:
        anyio.run(cenario, lab)
