"""Testes locais; o transporte não tem socket nem segredo."""
import json
from functools import partial

import pytest

from tuttibom.mcp_ops.atendimento import EnvioNaoEfetuado
from tuttibom.mcp_ops.chatwoot_backend_lab import LeituraLab
from tuttibom.mcp_ops.chatwoot_isolado import ChatwootIsolado, RespostaTransporte
from tuttibom.mcp_ops.piloto_conversa import (
    BackendPilotoChatwoot,
    EntradaPiloto,
    EscopoPiloto,
    permite_envio_legado,
)

ESCOPO = EscopoPiloto(11, "23", 37)
EVENTO = {
    "account_id": "11", "inbox_id": 23, "conversation_id": "37", "message_id": 101,
    "message_type": "incoming", "private": False,
}


@pytest.fixture
def piloto(tmp_path):
    estado = {"ativo": ESCOPO}
    caminho = tmp_path / "fila.sqlite"
    return EntradaPiloto(caminho, escopo=ESCOPO, obter_escopo_ativo=lambda: estado["ativo"]), estado, caminho


def test_entrada_idempotente_apos_reabrir_e_ack(piloto):
    entrada, _, caminho = piloto
    assert entrada.receber(EVENTO) == {"ok": True, "inserido": True, "codigo": None}
    outra = EntradaPiloto(caminho, escopo=ESCOPO, obter_escopo_ativo=lambda: ESCOPO)
    evento_normalizado = {**EVENTO, "message_id": "101", "message_type": 0}
    assert outra.receber(evento_normalizado) == {"ok": True, "inserido": False, "codigo": None}
    [item] = outra.listar_pendentes()
    assert (item["inbox_id"], item["conversation_id"], item["message_id"]) == (ESCOPO.fila_ref, "37", "101")
    assert outra.marcar_entregues(["101"]) == ["101"]
    assert not entrada.receber(evento_normalizado)["inserido"]
    assert entrada.listar_pendentes() == []
    assert entrada.obter("101")["estado"] == "entregue"


@pytest.mark.parametrize("campo", tuple(EVENTO))
def test_ausencia_de_metadado_nega_entrada(piloto, campo):
    entrada, _, _ = piloto
    assert entrada.receber({k: v for k, v in EVENTO.items() if k != campo})["codigo"] == "evento_invalido"
    assert entrada.listar_pendentes() == []


@pytest.mark.parametrize(("campo", "valor"), [
    ("account_id", 12), ("inbox_id", 24), ("conversation_id", 38),
    ("account_id", "011"), ("inbox_id", "23 "), ("conversation_id", "３７"),
    ("account_id", None), ("inbox_id", False), ("conversation_id", 37.0),
])
def test_rota_divergente_ou_forjada_nao_entra(piloto, campo, valor):
    entrada, _, _ = piloto
    assert entrada.receber({**EVENTO, campo: valor})["codigo"] == "fora_do_piloto"
    assert entrada.listar_pendentes() == []


@pytest.mark.parametrize("message_id", [None, True, 0, -1, 101.0, "00101", "msg-101", "101\n", 10**18])
def test_message_id_deve_ser_numerico_real_canonico(piloto, message_id):
    entrada, _, _ = piloto
    assert entrada.receber({**EVENTO, "message_id": message_id})["codigo"] == "evento_invalido"
    assert entrada.listar_pendentes() == []


def test_rejeita_campo_ambiguo_e_payload(piloto):
    entrada, _, _ = piloto
    for evento in (None, [], {**EVENTO, "account": {"id": 12}}, {**EVENTO, "content": "sintético"}):
        assert entrada.receber(evento)["codigo"] == "evento_invalido"
    assert entrada.listar_pendentes() == []


@pytest.mark.parametrize("alteracao", [
    {"private": True}, {"private": 0}, {"private": None}, {"private": "false"},
    {"message_type": "outgoing"}, {"message_type": 1}, {"message_type": False},
    {"message_type": "0"}, {"message_type": 0.0}, {"message_type": []},
])
def test_so_entrada_publica(piloto, alteracao):
    entrada, _, _ = piloto
    assert entrada.receber({**EVENTO, **alteracao})["codigo"] == "evento_nao_publico_incoming"
    assert entrada.listar_pendentes() == []


@pytest.mark.parametrize("atual", [None, True, {"account_id": 11}, EscopoPiloto(11, 23, 38)])
def test_piloto_inativo_nao_admite_nem_expoe_ou_confirma_pendencias(piloto, atual):
    entrada, estado, _ = piloto
    assert entrada.receber(EVENTO)["inserido"]
    estado["ativo"] = atual
    assert entrada.receber({**EVENTO, "message_id": 102})["codigo"] == "piloto_inativo"
    assert entrada.listar_pendentes() == []
    assert entrada.obter("101") is None
    assert entrada.marcar_entregues(["101"]) == []
    estado["ativo"] = EscopoPiloto("11", 23, "37")
    assert [p["message_id"] for p in entrada.listar_pendentes()] == ["101"]


def test_erro_ao_ler_config_nega_entrada(tmp_path):
    def indisponivel():
        raise OSError("configuração indisponível")

    entrada = EntradaPiloto(tmp_path / "fila.sqlite", escopo=ESCOPO, obter_escopo_ativo=indisponivel)
    assert entrada.receber(EVENTO)["codigo"] == "piloto_inativo"
    assert entrada.listar_pendentes() == []


@pytest.mark.parametrize("ids", [(True, 23, 37), (11, "", 37), (11, 23, "conv-37"), (11, 23, 10**9)])
def test_config_invalida_nao_constroi_escopo(ids):
    with pytest.raises(ValueError, match="escopo_piloto_invalido"):
        EscopoPiloto(*ids)


def test_particao_da_fila_inclui_conta_inbox_e_conversa(piloto):
    entrada, _, caminho = piloto
    assert entrada.receber(EVENTO)["inserido"]
    for conta, inbox, conversa in ((12, 23, 37), (11, 24, 37), (11, 23, 38)):
        escopo = EscopoPiloto(conta, inbox, conversa)
        outro = EntradaPiloto(caminho, escopo=escopo, obter_escopo_ativo=lambda: escopo)
        assert outro.listar_pendentes() == []
        assert outro.receber({
            **EVENTO, "account_id": conta, "inbox_id": inbox, "conversation_id": conversa,
        })["inserido"]
    assert len(entrada.listar_pendentes()) == 1


def test_legado_reavalia_rota_exata_no_momento_do_envio(piloto):
    _, estado, _ = piloto
    disparos = []

    def enviar_se_permitido(conta, inbox, conversa):
        if permite_envio_legado(estado["ativo"], conta_id=conta, inbox_id=inbox, conversa_id=conversa):
            disparos.append((conta, inbox, conversa))

    estado["ativo"] = None
    agendado_antes_do_piloto = partial(enviar_se_permitido, 11, "23", 37)
    estado["ativo"] = ESCOPO
    agendado_antes_do_piloto()
    assert not disparos
    outras = [(12, 23, 37), (11, 24, 37), (11, 23, 38)]
    for rota in outras:
        enviar_se_permitido(*rota)
    assert disparos == outras
    estado["ativo"] = None
    agendado_antes_do_piloto()
    assert disparos[-1] == (11, "23", 37)


def test_legado_nao_confunde_config_ou_rota_invalida_com_desativacao():
    assert not permite_envio_legado({}, conta_id=11, inbox_id=23, conversa_id=37)
    assert not permite_envio_legado(None, conta_id=11, inbox_id=23, conversa_id=None)


class _TransporteFicticio:
    def __init__(self):
        self.chamadas = []

    def chamar(self, metodo, caminho, **kwargs):
        self.chamadas.append((metodo, caminho))
        raiz = "/api/v1/accounts/11/conversations/37"
        if caminho == raiz and metodo == "GET":
            dados = {"id": 37, "inbox_id": 23, "account_id": 11}
        elif caminho == raiz + "/messages" and metodo == "GET":
            dados = {"payload": [{"id": 101, "message_type": 0, "inbox_id": 23, "content": "Fictício."}]}
        elif caminho == raiz + "/messages" and metodo == "POST":
            dados = {"id": 102, "inbox_id": 23}
        else:
            raise AssertionError("caminho inesperado")
        return RespostaTransporte(200, json.dumps(dados).encode(), True)


def test_backend_rejeita_fora_do_escopo_e_envio_ja_preparado_apos_rollback(piloto):
    entrada, estado, _ = piloto
    transporte = _TransporteFicticio()
    for conta, inbox in (("12", "23"), ("11", "24")):
        with pytest.raises(ValueError, match="chatwoot_fora_do_piloto"):
            BackendPilotoChatwoot(entrada, ChatwootIsolado(transporte, conta_id=conta, inbox_id=inbox))
    backend = BackendPilotoChatwoot(entrada, ChatwootIsolado(transporte, conta_id="11", inbox_id="23"))
    enviar = partial(backend.enviar, texto="Fictício.", imagem=None, idempotency_key="chave-lab")
    assert backend.ler_mensagens("38") is None
    with pytest.raises(LeituraLab, match="conversa_fora_do_piloto"):
        backend.geracao("38")
    with pytest.raises(EnvioNaoEfetuado, match="conversa_fora_do_piloto"):
        enviar(conversa_ref="38")
    assert not transporte.chamadas
    assert backend.ler_mensagens("37")[0]["direcao"] == "incoming"
    assert enviar(conversa_ref="37") == {"ok": True, "envio_ref": "msg-102"}
    chamadas = transporte.chamadas[:]

    estado["ativo"] = None
    assert backend.ler_mensagens("37") is None
    with pytest.raises(LeituraLab, match="conversa_fora_do_piloto"):
        backend.obter_imagem("anexo-101")
    with pytest.raises(EnvioNaoEfetuado, match="conversa_fora_do_piloto"):
        enviar(conversa_ref="37")
    assert transporte.chamadas == chamadas
