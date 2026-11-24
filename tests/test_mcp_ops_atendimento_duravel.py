from tuttibom.mcp_ops.atendimento import (
    AdaptadorAtendimento,
    ChatwootLaboratorio,
    EnvioNaoEfetuado,
    SimuladorAtendimento,
    VerificadorAprovacaoServidor,
)
from tuttibom.mcp_ops.entregas_duraveis import DiarioEntregas
from tuttibom.mcp_ops.fila_persistente import FilaPersistente


def componentes(tmp_path, destino=None):
    fila = FilaPersistente(tmp_path / "fila.sqlite", inbox_ref="inbox-lab")
    diario = DiarioEntregas(tmp_path / "diario.sqlite")
    chat = ChatwootLaboratorio()
    chat.registrar_mensagem("conv-lab", direcao="incoming", texto="Olá, teste.")
    destino = destino or SimuladorAtendimento()
    verificador = VerificadorAprovacaoServidor()
    ops = AdaptadorAtendimento(
        fila=fila, chatwoot=chat, simulador=destino, transcritor=None,
        verificador=verificador, diario=diario,
    )
    return fila, diario, destino, verificador, ops


def rascunho(ops, aprovador, chave="intento-1", texto="Resposta fictícia."):
    assert ops.ler_conversa("conv-lab")["ok"]
    ref = ops.preparar_resposta(
        conversa_ref="conv-lab", texto=texto, message_ids=["m1", "m2"],
        idempotency_key=chave,
    )["rascunho_ref"]
    return {"rascunho_ref": ref, "aprovacao_ref": aprovador.registrar(texto=texto)}


def test_aceite_persistido_antes_ack_e_reconcilia_sem_reenvio(tmp_path, monkeypatch):
    fila, diario, destino, aprovador, ops = componentes(tmp_path)
    for msg in ("m1", "m2"):
        fila.registrar(message_id=msg, conversation_id="conv-lab")
    original = fila.marcar_entregues
    monkeypatch.setattr(fila, "marcar_entregues", lambda ids: original(ids[:1]))
    envio = ops.responder(**rascunho(ops, aprovador))
    assert envio["codigo"] == "ack_falhou" and envio["enviado"]
    assert len(destino.envios) == 1
    assert diario.listar_acoes_pendentes()[0]["ack_pendentes"] == ["m2"]
    nova_fila, _, _, novo_aprovador, novo_ops = componentes(tmp_path, destino)
    assert [p["message_id"] for p in nova_fila.listar_pendentes()] == ["m2"]
    conciliado = novo_ops.reconciliar_acks()
    assert conciliado["ok"] and conciliado["incertos"] == 0
    assert conciliado["resultados"][0]["envio_ref"] == envio["envio_ref"]
    assert not nova_fila.listar_pendentes()
    retry = novo_ops.responder(**rascunho(novo_ops, novo_aprovador, "chave-diferente"))
    assert retry["ok"] and retry["replay"] and retry["envio_ref"] == envio["envio_ref"]
    assert len(destino.envios) == 1


class DestinoInterrompivel(SimuladorAtendimento):
    tentativas = 0

    def __init__(self, *, incerto):
        super().__init__()
        self.incerto = incerto

    def enviar(self, **args):
        self.tentativas += 1
        if self.tentativas == 1:
            if self.incerto:
                super().enviar(**args)
                raise TimeoutError()
            raise EnvioNaoEfetuado()
        return super().enviar(**args)


def test_timeout_apos_efeito_nao_reenvia_nem_confirma_fila(tmp_path):
    destino = DestinoInterrompivel(incerto=True)
    fila, _, _, aprovador, ops = componentes(tmp_path, destino)
    for msg in ("m1", "m2"):
        fila.registrar(message_id=msg, conversation_id="conv-lab")
    assert ops.responder(**rascunho(ops, aprovador))["codigo"] == "entrega_incerta"
    nova_fila, _, _, novo_aprovador, novo_ops = componentes(tmp_path, destino)
    assert novo_ops.responder(**rascunho(novo_ops, novo_aprovador, "chave-2"))["codigo"] == "entrega_incerta"
    assert novo_ops.reconciliar_acks()["incertos"] == 1
    assert destino.tentativas == 1 and len(destino.envios) == 1
    assert len(nova_fila.listar_pendentes()) == 2


def test_retry_so_quando_destino_confirma_que_nao_enviou(tmp_path):
    destino = DestinoInterrompivel(incerto=False)
    fila, _, _, aprovador, ops = componentes(tmp_path, destino)
    for msg in ("m1", "m2"):
        fila.registrar(message_id=msg, conversation_id="conv-lab")
    tentativa = rascunho(ops, aprovador)
    assert ops.responder(**tentativa)["codigo"] == "envio_falhou"
    assert len(fila.listar_pendentes()) == 2
    assert ops.responder(**tentativa)["ok"]
    assert destino.tentativas == 2 and len(destino.envios) == 1
