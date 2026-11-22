"""Testes do ana-listener — só stdlib (unittest).

Textos de teste FICTÍCIOS — nunca texto real de cliente.
Roda no PC: python3 -m unittest discover -s services/chatwoot-ana -p 'test_*.py' -v
"""

import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest import mock

# Banco temporário, antes de importar o listener (ele lê o env no import).
_TMP = tempfile.TemporaryDirectory()
os.environ["LISTENER_DB"] = os.path.join(_TMP.name, "listener-test.db")
os.environ["LISTENER_HOST"] = "127.0.0.1"
os.environ["LISTENER_PORT"] = "0"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import handoff  # noqa: E402
import listener  # noqa: E402

# Contato ignorado de verdade (ignorados.json do repo): Mercado Livre.
TEL_IGNORADO = "+5511978832287"
ID_IGNORADO = "eab057e8-88ce-4893-89f1-41429722efaa"
# Telefones/ids fictícios dos demais testes.
TEL_FICTICIO = "+5551999990001"


def _post(base, path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(base + path, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8") or "{}"
        return exc.code, json.loads(body)


def _get(base, path):
    with urllib.request.urlopen(base + path, timeout=5) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def _payload_incoming(message_id, conversation_id=101, inbox_id=1,
                      telefone=TEL_FICTICIO, identifier=None,
                      texto="Olá, queria saber o preço da fita de teste"):
    sender = {"id": 9001, "name": "Cliente Fictício"}
    if telefone:
        sender["phone_number"] = telefone
    if identifier:
        sender["identifier"] = identifier
    return {
        "event": "message_created",
        "message": {
            "id": message_id,
            "content": texto,
            "message_type": "incoming",
            "conversation_id": conversation_id,
            "inbox_id": inbox_id,
            "sender": sender,
            "conversation": {"id": conversation_id, "inbox_id": inbox_id},
        },
    }


class ListenerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), listener.Handler)
        cls.port = cls.server.server_address[1]
        cls.base = "http://127.0.0.1:%d" % cls.port
        cls.thread = threading.Thread(
            target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        conn = listener.db()
        try:
            conn.execute("DELETE FROM events")
            conn.commit()
        finally:
            conn.close()

    def test_health(self):
        status, body = _get(self.base, "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"ok": True, "service": "ana-listener",
                                "version": "0.1.0"})

    def test_incoming_enfileira(self):
        status, body = _post(self.base, "/webhooks/chatwoot",
                             _payload_incoming(5001))
        self.assertEqual(status, 200)
        self.assertEqual(body["detail"], "ok")
        status, body = _get(self.base, "/pending")
        self.assertEqual(len(body["pending"]), 1)
        item = body["pending"][0]
        self.assertEqual(item["message_id"], 5001)
        self.assertEqual(item["conversation_id"], 101)
        self.assertEqual(item["inbox_id"], 1)
        self.assertEqual(item["contato_ref"], TEL_FICTICIO)
        self.assertIsNone(item["handoff"])
        _, stats = _get(self.base, "/stats")
        self.assertEqual(stats, {"pendente": 1, "entregue": 0,
                                 "ignorado": 0, "total": 1})

    def test_formato_inbox_topo_tambem_enfileira(self):
        # Webhook de inbox: campos da mensagem no topo, sem "message".
        payload = {
            "event": "message_created",
            "id": 5002,
            "content": "Mensagem fictícia em formato de inbox",
            "message_type": "incoming",
            "conversation_id": 102,
            "inbox_id": 2,
            "sender": {"id": 9002, "name": "Cliente Fictício",
                       "phone_number": "+5551999990002"},
            "conversation": {"id": 102, "inbox_id": 2},
        }
        status, body = _post(self.base, "/webhooks/chatwoot", payload)
        self.assertEqual(status, 200)
        self.assertEqual(body["detail"], "ok")
        _, body = _get(self.base, "/pending")
        self.assertEqual([p["message_id"] for p in body["pending"]], [5002])

    def test_outgoing_e_activity_sao_ignorados(self):
        for i, mtype in enumerate(("outgoing", "activity", 1, 2)):
            payload = _payload_incoming(5101 + i)
            payload["message"]["message_type"] = mtype
            status, body = _post(self.base, "/webhooks/chatwoot", payload)
            self.assertEqual(status, 200)
            self.assertEqual(body["detail"], "nao-incoming")
        _, body = _get(self.base, "/pending")
        self.assertEqual(body["pending"], [])
        _, stats = _get(self.base, "/stats")
        self.assertEqual(stats["total"], 0)

    def test_duplicado_nao_duplica(self):
        payload = _payload_incoming(5201)
        _, first = _post(self.base, "/webhooks/chatwoot", payload)
        self.assertEqual(first["detail"], "ok")
        _, second = _post(self.base, "/webhooks/chatwoot", payload)
        self.assertEqual(second["detail"], "duplicada")
        _, body = _get(self.base, "/pending")
        self.assertEqual(len(body["pending"]), 1)
        _, stats = _get(self.base, "/stats")
        self.assertEqual(stats["total"], 1)

    def test_contato_ignorado_vira_ignorado_e_nao_entra_no_pending(self):
        # Telefone + identifier do Mercado Livre (ignorados.json).
        _, body = _post(self.base, "/webhooks/chatwoot",
                        _payload_incoming(5301, telefone=TEL_IGNORADO,
                                          identifier=ID_IGNORADO))
        self.assertEqual(body["detail"], "ignorado")
        # Só pelo telefone.
        _, body = _post(self.base, "/webhooks/chatwoot",
                        _payload_incoming(5302, telefone=TEL_IGNORADO))
        self.assertEqual(body["detail"], "ignorado")
        # Só pelo identifier.
        _, body = _post(self.base, "/webhooks/chatwoot",
                        _payload_incoming(5303, telefone=None,
                                          identifier=ID_IGNORADO))
        self.assertEqual(body["detail"], "ignorado")
        _, body = _get(self.base, "/pending")
        self.assertEqual(body["pending"], [])
        _, stats = _get(self.base, "/stats")
        self.assertEqual(stats, {"pendente": 0, "entregue": 0,
                                 "ignorado": 3, "total": 3})

    def test_ack_marca_entregue(self):
        _post(self.base, "/webhooks/chatwoot", _payload_incoming(5401))
        _post(self.base, "/webhooks/chatwoot", _payload_incoming(5402))
        status, body = _post(self.base, "/ack", {"message_id": 5401})
        self.assertEqual(status, 200)
        self.assertEqual(body, {"ok": True, "marcados": 1})
        status, body = _post(self.base, "/ack",
                             {"message_ids": [5402, 9999]})
        self.assertEqual(body, {"ok": True, "marcados": 1})
        _, body = _get(self.base, "/pending")
        self.assertEqual(body["pending"], [])
        _, stats = _get(self.base, "/stats")
        self.assertEqual(stats, {"pendente": 0, "entregue": 2,
                                 "ignorado": 0, "total": 2})

    def test_handoff_via_mock(self):
        # O módulo real detecta/aplica de verdade; o mock prova a
        # fiação do ouvinte: detectar -> aplicar -> handoff gravado.
        chamadas = []

        def fake_aplicar(conversation_id, motivo):
            chamadas.append((conversation_id, motivo))
            return {"ignorado": False, "aplicado": True,
                    "etiqueta": "handoff-humano", "assignee_id": 2,
                    "etiquetada": True, "atribuida": True, "nota": True}

        with mock.patch.object(
                handoff, "detectar_handoff",
                return_value={"motivo": "pedido-humano-teste",
                              "regra": "teste"}), \
                mock.patch.object(handoff, "aplicar_handoff",
                                  side_effect=fake_aplicar):
            listener._handoff_tentado = False
            listener._handoff = None
            _, body = _post(self.base, "/webhooks/chatwoot",
                            _payload_incoming(5501))
            self.assertEqual(body["detail"], "handoff")
        self.assertEqual(chamadas, [(101, "pedido-humano-teste")])
        _, body = _get(self.base, "/pending")
        self.assertEqual(len(body["pending"]), 1)
        self.assertEqual(body["pending"][0]["handoff"],
                         "pedido-humano-teste")

    def test_handoff_ignorado_via_aplicar_marca_ignorado(self):
        # O aplicar pode descobrir o ignorado via API mesmo quando o
        # payload não trazia telefone/identifier: o ouvinte marca
        # 'ignorado' e não deixa nada no /pending.
        with mock.patch.object(
                handoff, "detectar_handoff",
                return_value={"motivo": "suspeita-golpe",
                              "regra": "teste"}), \
                mock.patch.object(
                    handoff, "aplicar_handoff",
                    return_value={"ignorado": True,
                                  "empresa": "Mercado Livre",
                                  "aplicado": False}):
            listener._handoff_tentado = False
            listener._handoff = None
            _, body = _post(self.base, "/webhooks/chatwoot",
                            _payload_incoming(5502))
            self.assertEqual(body["detail"], "ignorado")
        _, body = _get(self.base, "/pending")
        self.assertEqual(body["pending"], [])
        _, stats = _get(self.base, "/stats")
        self.assertEqual(stats["ignorado"], 1)

    def test_incoming_sem_identificador_enfileira_mesmo_assim(self):
        payload = _payload_incoming(5601, telefone=None, identifier=None)
        status, body = _post(self.base, "/webhooks/chatwoot", payload)
        self.assertEqual(status, 200)
        self.assertEqual(body["detail"], "ok")
        _, body = _get(self.base, "/pending")
        self.assertEqual(len(body["pending"]), 1)
        self.assertEqual(body["pending"][0]["contato_ref"], "contact:9001")


if __name__ == "__main__":
    unittest.main()
