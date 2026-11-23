"""Testes do ana-listener — só stdlib (unittest).

Textos de teste FICTÍCIOS — nunca texto real de cliente.
Roda no PC: python3 -m unittest discover -s services/chatwoot-ana -p 'test_*.py' -v
"""

import json
import os
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
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
        for timer in list(listener._TIMERS.values()):
            timer.cancel()
        listener._TIMERS.clear()
        conn = listener.db()
        try:
            conn.execute("DELETE FROM events")
            conn.execute("DELETE FROM cumprimentos")
            conn.commit()
        finally:
            conn.close()

    def test_health(self):
        status, body = _get(self.base, "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"ok": True, "service": "ana-listener",
                                "version": "0.6.1"})

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
                                 "ignorado": 0, "total": 1,
                                 "cumprimentos": 0})

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
        self.assertEqual(stats["cumprimentos"], 0)

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
                                 "ignorado": 3, "total": 3,
                                 "cumprimentos": 0})

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
                                 "ignorado": 0, "total": 2,
                                 "cumprimentos": 0})

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

    # ------------------------------------------------------ cumprimento
    def _mocks_cumprimento(self, mensagens=(True, []), enviado=True,
                           hora=10):
        """Mocks: leitura da conversa, envio e relógio (10h = Bom dia)."""
        pilha = ExitStack()
        pilha.enter_context(mock.patch.object(
            listener, "_mensagens_da_conversa", return_value=mensagens))
        pilha.enter_context(mock.patch.object(
            listener, "_enviar_cumprimento_api", return_value=enviado))
        pilha.enter_context(mock.patch.object(
            listener, "_agora_fortaleza",
            return_value=datetime(2026, 11, 21, hora, 0,
                                  tzinfo=timezone.utc)))
        return pilha

    def _n_cumprimentos(self):
        _, stats = _get(self.base, "/stats")
        return stats["cumprimentos"]

    def _disparar(self, conversation_id):
        """Dispara na hora o timer agendado (sem esperar 10 s reais)."""
        timer = listener._TIMERS.get(conversation_id)
        self.assertIsNotNone(timer, "sem timer agendado")
        timer.cancel()
        listener._disparar_cumprimento(timer.args[0])

    def _envelhecer_cumprimento(self, conversation_id, minutos):
        conn = listener.db()
        try:
            conn.execute(
                "UPDATE cumprimentos SET enviado_em=?"
                " WHERE conversation_id=?",
                ((datetime.now(timezone.utc)
                  - timedelta(minutes=minutos)).isoformat(),
                 conversation_id))
            conn.commit()
        finally:
            conn.close()

    def _incoming(self, message_id, conversation_id, texto):
        """Mensagem incoming com created_at (para a janela da rajada)."""
        payload = _payload_incoming(message_id,
                                    conversation_id=conversation_id,
                                    texto=texto)
        payload["message"]["created_at"] = int(time.time())
        return payload

    def test_deteccao_saudacao_fechada(self):
        casos = [
            ("oi", True), ("Bom dia", True), ("Olá tudo bom", True),
            ("tudo bem?", True), ("boa tarde", True), ("como vai", True),
            ("oi, quanto custa", False),
            ("Boa noite, queria saber o preço", False),
            ("oi, queria uma fita", False), ("", False),
            ("quero falar com humano", False),
        ]
        for texto, esperado in casos:
            with self.subTest(texto=texto):
                self.assertEqual(
                    listener.eh_saudacao_fechada(texto), esperado)

    def test_saudacao_por_horario(self):
        casos = [
            (2, "Boa noite"), (5, "Boa noite"), (6, "Bom dia"),
            (11, "Bom dia"), (12, "Boa tarde"), (17, "Boa tarde"),
            (18, "Boa noite"), (23, "Boa noite"),
        ]
        for hora, esperado in casos:
            with self.subTest(hora=hora):
                agora = datetime(2026, 11, 21, hora, 0,
                                 tzinfo=timezone.utc)
                self.assertEqual(
                    listener.saudacao_por_horario(agora), esperado)

    def test_pools_verificar(self):
        # Saudação fechada: nenhuma variante fala em verificar.
        for variante in range(3):
            texto = listener.texto_cumprimento(
                "saudacao", variante,
                datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc))
            self.assertNotIn("verificar", texto.lower())
        # Com pedido: o pool é o de verificar (variantes 0 e 2).
        self.assertIn("verificar", listener.texto_cumprimento(
            "pedido", 0,
            datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc)).lower())
        self.assertIn("verificar", listener.texto_cumprimento(
            "pedido", 2,
            datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc)).lower())

    def test_classificar_rajada_midia_vazia(self):
        # Correção 2026-11-23: sem texto conhecido (só mídia/vazio),
        # não há pedido — o cumprimento é o genérico, sem "verificar".
        agora = int(time.time())
        midia_vazia = [
            {"message_type": 0, "content": "", "created_at": agora},
            {"message_type": 0, "content": None, "created_at": agora},
        ]
        self.assertEqual(
            listener._classificar_rajada(midia_vazia, "", None),
            "saudacao")
        # Áudio sozinho: texto inicial vazio, nenhuma mensagem com texto.
        self.assertEqual(
            listener._classificar_rajada([], "", None), "saudacao")
        # Saudação pura continua genérica.
        self.assertEqual(
            listener._classificar_rajada([], "boa noite", None),
            "saudacao")
        self.assertEqual(
            listener._classificar_rajada(
                [{"message_type": 0, "content": "bom dia",
                  "created_at": agora}],
                "oi", None),
            "saudacao")
        # Pedido real continua no pool de verificar.
        self.assertEqual(
            listener._classificar_rajada(
                [], "quanto custa a fita de 10 m", None), "pedido")
        self.assertEqual(
            listener._classificar_rajada(
                [{"message_type": 0, "content": "oi",
                  "created_at": agora}],
                "quanto custa", None), "pedido")

    def test_cumprimento_primeira_mensagem_saudacao(self):
        # Nada é enviado no ato: o cumprimento sai no disparo do timer.
        with self._mocks_cumprimento():
            _, body = _post(
                self.base, "/webhooks/chatwoot",
                self._incoming(6001, 201, "Bom dia"))
            self.assertEqual(body["detail"], "ok")
            self.assertEqual(self._n_cumprimentos(), 0)
            self.assertIn(201, listener._TIMERS)
            self._disparar(201)
        _, body = _get(self.base, "/pending")
        self.assertEqual(len(body["pending"]), 1)
        cump = body["pending"][0]["cumprimento"]
        self.assertEqual(
            cump["texto"], "Bom dia! Aguarde um instante, por favor.")
        self.assertIn("enviado_em", cump)
        self.assertEqual(self._n_cumprimentos(), 1)

    def test_cumprimento_pedido_usa_pool_com_verificar(self):
        with self._mocks_cumprimento():
            _, body = _post(
                self.base, "/webhooks/chatwoot",
                self._incoming(
                    6002, 202, "oi, quanto custa a fita de teste"))
            self.assertEqual(body["detail"], "ok")
            self.assertEqual(self._n_cumprimentos(), 0)
            self._disparar(202)
        _, body = _get(self.base, "/pending")
        cump = body["pending"][0]["cumprimento"]
        self.assertEqual(
            cump["texto"],
            "Bom dia! Vou verificar aqui e já te respondo.")

    def test_timer_fixo_nao_desliza(self):
        # Segunda mensagem na janela não agenda outro timer.
        with self._mocks_cumprimento():
            _post(self.base, "/webhooks/chatwoot",
                  self._incoming(6051, 209, "oi"))
            primeiro = listener._TIMERS.get(209)
            self.assertIsNotNone(primeiro)
            _post(self.base, "/webhooks/chatwoot",
                  self._incoming(6052, 209, "quanto custa?"))
            self.assertIs(listener._TIMERS.get(209), primeiro)
            self._disparar(209)
        self.assertEqual(self._n_cumprimentos(), 1)

    def test_rajada_mista_usa_pool_pedido(self):
        # "oi" + "quanto custa" + "oi?" na janela: basta um pedido.
        agora = int(time.time())
        rajada = [
            {"message_type": 0, "content": "oi", "created_at": agora},
            {"message_type": 0, "content": "quanto custa",
             "created_at": agora},
            {"message_type": 0, "content": "oi?", "created_at": agora},
        ]
        with self._mocks_cumprimento(mensagens=(True, rajada)):
            _post(self.base, "/webhooks/chatwoot",
                  self._incoming(6061, 210, "oi"))
            self._disparar(210)
        _, body = _get(self.base, "/pending")
        cump = body["pending"][0]["cumprimento"]
        self.assertEqual(
            cump["texto"],
            "Bom dia! Vou verificar aqui e já te respondo.")

    def test_rajada_so_saudacoes_usa_pool_sem_verificar(self):
        agora = int(time.time())
        rajada = [
            {"message_type": 0, "content": "oi", "created_at": agora},
            {"message_type": 0, "content": "bom dia",
             "created_at": agora},
        ]
        with self._mocks_cumprimento(mensagens=(True, rajada)):
            _post(self.base, "/webhooks/chatwoot",
                  self._incoming(6062, 211, "oi"))
            self._disparar(211)
        _, body = _get(self.base, "/pending")
        cump = body["pending"][0]["cumprimento"]
        self.assertEqual(
            cump["texto"], "Bom dia! Aguarde um instante, por favor.")

    def test_rotacao_nao_repete_variante(self):
        with self._mocks_cumprimento():
            _post(self.base, "/webhooks/chatwoot",
                  self._incoming(6101, 203, "oi"))
            self._disparar(203)
        _, body = _get(self.base, "/pending")
        primeiro = body["pending"][0]["cumprimento"]["texto"]
        self.assertEqual(primeiro, "Bom dia! Aguarde um instante, por favor.")
        self._envelhecer_cumprimento(203, 31)
        with self._mocks_cumprimento():
            _post(self.base, "/webhooks/chatwoot",
                  self._incoming(6102, 203, "oi"))
            self._disparar(203)
        _, body = _get(self.base, "/pending")
        self.assertEqual(len(body["pending"]), 2)
        segundo = body["pending"][1]["cumprimento"]["texto"]
        self.assertEqual(segundo, "Bom dia! Aguarde que já lhe atendo.")
        self.assertNotEqual(primeiro, segundo)
        self.assertEqual(self._n_cumprimentos(), 2)

    def test_segunda_dentro_de_10_min_nao_dispara(self):
        with self._mocks_cumprimento():
            _post(self.base, "/webhooks/chatwoot",
                  self._incoming(6201, 204, "oi"))
            self._disparar(204)
        self.assertEqual(self._n_cumprimentos(), 1)
        _post(self.base, "/webhooks/chatwoot",
              self._incoming(6202, 204, "quanto custa?"))
        self.assertNotIn(204, listener._TIMERS)
        self.assertEqual(self._n_cumprimentos(), 1)
        _, body = _get(self.base, "/pending")
        self.assertEqual(len(body["pending"]), 2)
        self.assertIsNotNone(body["pending"][0]["cumprimento"])
        self.assertIsNone(body["pending"][1]["cumprimento"])

    def test_outgoing_recente_inibe_cumprimento(self):
        # Outgoing 5 min antes da rajada: dentro da pausa de 2h.
        agora = int(time.time())
        outgoing = [{"id": 1, "message_type": 1,
                     "created_at": agora - 5 * 60,
                     "content": "resposta fictícia da Ana"}]
        with self._mocks_cumprimento(mensagens=(True, outgoing)):
            _, body = _post(
                self.base, "/webhooks/chatwoot",
                self._incoming(6301, 205, "oi"))
            self.assertEqual(body["detail"], "ok")
            self._disparar(205)
        _, body = _get(self.base, "/pending")
        self.assertIsNone(body["pending"][0]["cumprimento"])
        self.assertEqual(self._n_cumprimentos(), 0)

    def test_incoming_30_min_antes_suprime(self):
        # Pausa de 2h: incoming 30 min antes da rajada suprime.
        agora = int(time.time())
        anterior = [{"message_type": 0, "content": "oi",
                     "created_at": agora - 30 * 60}]
        with self._mocks_cumprimento(mensagens=(True, anterior)):
            _post(self.base, "/webhooks/chatwoot",
                  self._incoming(7001, 220, "oi"))
            self._disparar(220)
        _, body = _get(self.base, "/pending")
        self.assertIsNone(body["pending"][0]["cumprimento"])
        self.assertEqual(self._n_cumprimentos(), 0)

    def test_resposta_publica_durante_timer_suprime_cumprimento(self):
        payload = self._incoming(7011, 231, "oi")
        resposta = {"message_type": 1, "private": False,
                    "created_at": payload["message"]["created_at"] + 3}
        with self._mocks_cumprimento(mensagens=(True, [resposta])):
            _post(self.base, "/webhooks/chatwoot", payload)
            self._disparar(231)
            listener._enviar_cumprimento_api.assert_not_called()
        _, body = _get(self.base, "/pending")
        self.assertIsNone(body["pending"][0]["cumprimento"])

    def test_nota_privada_nao_suprime_cumprimento(self):
        payload = self._incoming(7012, 232, "oi")
        criado = payload["message"]["created_at"]
        notas = [{"message_type": 1, "private": True,
                  "created_at": criado + diferenca}
                 for diferenca in (-60, 3)]
        with self._mocks_cumprimento(mensagens=(True, notas)):
            _post(self.base, "/webhooks/chatwoot", payload)
            self._disparar(232)
            listener._enviar_cumprimento_api.assert_called_once()

    def test_outgoing_30_min_antes_suprime(self):
        # Pausa de 2h: outgoing 30 min antes da rajada suprime.
        agora = int(time.time())
        anterior = [{"id": 1, "message_type": 1,
                     "content": "resposta fictícia da Ana",
                     "created_at": agora - 30 * 60}]
        with self._mocks_cumprimento(mensagens=(True, anterior)):
            _post(self.base, "/webhooks/chatwoot",
                  self._incoming(7002, 221, "oi"))
            self._disparar(221)
        _, body = _get(self.base, "/pending")
        self.assertIsNone(body["pending"][0]["cumprimento"])
        self.assertEqual(self._n_cumprimentos(), 0)

    def test_atividade_3h_antes_dispara(self):
        # Última atividade há 3h: é abertura nova, dispara.
        agora = int(time.time())
        anterior = [{"id": 1, "message_type": 1,
                     "content": "resposta fictícia da Ana",
                     "created_at": agora - 3 * 60 * 60}]
        with self._mocks_cumprimento(mensagens=(True, anterior)):
            _post(self.base, "/webhooks/chatwoot",
                  self._incoming(7003, 222, "oi"))
            self._disparar(222)
        _, body = _get(self.base, "/pending")
        cump = body["pending"][0]["cumprimento"]
        self.assertEqual(
            cump["texto"], "Bom dia! Aguarde um instante, por favor.")
        self.assertEqual(self._n_cumprimentos(), 1)

    def test_primeira_mensagem_sem_atividade_dispara(self):
        # Conversa sem nenhuma atividade anterior: é abertura, dispara.
        with self._mocks_cumprimento(mensagens=(True, [])):
            _post(self.base, "/webhooks/chatwoot",
                  self._incoming(
                      7004, 223, "oi, quanto custa a fita de teste"))
            self._disparar(223)
        _, body = _get(self.base, "/pending")
        cump = body["pending"][0]["cumprimento"]
        self.assertEqual(
            cump["texto"],
            "Bom dia! Vou verificar aqui e já te respondo.")
        self.assertEqual(self._n_cumprimentos(), 1)

    def test_falha_api_com_cumprimento_anterior_suprime(self):
        # Sem a API não dá para provar 2h de silêncio: conversa que
        # já recebeu cumprimento não recebe outro.
        with self._mocks_cumprimento():
            _post(self.base, "/webhooks/chatwoot",
                  self._incoming(7005, 224, "oi"))
            self._disparar(224)
        self.assertEqual(self._n_cumprimentos(), 1)
        self._envelhecer_cumprimento(224, 15)
        with self._mocks_cumprimento(mensagens=(False, []),
                                      enviado=True):
            _post(self.base, "/webhooks/chatwoot",
                  self._incoming(7006, 224, "quanto custa?"))
            self._disparar(224)
        self.assertEqual(self._n_cumprimentos(), 1)
        _, body = _get(self.base, "/pending")
        self.assertEqual(len(body["pending"]), 2)
        self.assertIsNotNone(body["pending"][0]["cumprimento"])
        self.assertIsNone(body["pending"][1]["cumprimento"])

    def test_falha_api_sem_cumprimento_anterior_dispara(self):
        # Sem a API e sem cumprimento anterior no estado local: envia.
        with self._mocks_cumprimento(mensagens=(False, []),
                                      enviado=True):
            _post(self.base, "/webhooks/chatwoot",
                  self._incoming(7007, 225, "oi"))
            self._disparar(225)
        _, body = _get(self.base, "/pending")
        cump = body["pending"][0]["cumprimento"]
        self.assertEqual(
            cump["texto"], "Bom dia! Aguarde um instante, por favor.")
        self.assertEqual(self._n_cumprimentos(), 1)

    def test_falha_api_e_falha_envio_nao_bloqueiam(self):
        with self._mocks_cumprimento(mensagens=(False, []), enviado=False):
            _, body = _post(
                self.base, "/webhooks/chatwoot",
                self._incoming(6401, 206, "oi"))
            self.assertEqual(body["detail"], "ok")
            self._disparar(206)
        _, body = _get(self.base, "/pending")
        self.assertEqual(len(body["pending"]), 1)
        self.assertIsNone(body["pending"][0]["cumprimento"])
        self.assertEqual(self._n_cumprimentos(), 0)

    def test_midia_sem_legenda_usa_generico_mesmo_se_leitura_falhar(self):
        for i, (tipo, legenda, leitura_ok) in enumerate((
            ("audio", None, False),
            ("image", "", False),
            ("image", "   ", True),
        )):
            with self.subTest(tipo=tipo, legenda=legenda, leitura_ok=leitura_ok):
                conversa = 233 + i
                payload = self._incoming(7013 + i, conversa, legenda)
                payload["message"]["attachments"] = [{"file_type": tipo}]
                with self._mocks_cumprimento(mensagens=(leitura_ok, [])):
                    _post(self.base, "/webhooks/chatwoot", payload)
                    self._disparar(conversa)
                    listener._enviar_cumprimento_api.assert_called_once_with(
                        conversa, "Bom dia! Aguarde um instante, por favor.")

    def test_falha_api_usa_texto_do_disparo(self):
        # Sem a API, classifica só pelo texto que disparou o timer.
        with self._mocks_cumprimento(mensagens=(False, []), enviado=True):
            _post(self.base, "/webhooks/chatwoot",
                  self._incoming(6402, 212, "oi"))
            self._disparar(212)
        _, body = _get(self.base, "/pending")
        cump = body["pending"][0]["cumprimento"]
        self.assertEqual(
            cump["texto"], "Bom dia! Aguarde um instante, por favor.")

    def test_ignorado_nunca_cumprimenta(self):
        _, body = _post(self.base, "/webhooks/chatwoot",
                        _payload_incoming(6501, telefone=TEL_IGNORADO,
                                          identifier=ID_IGNORADO))
        self.assertEqual(body["detail"], "ignorado")
        self.assertEqual(self._n_cumprimentos(), 0)

    def test_eh_grupo_whatsapp(self):
        self.assertTrue(listener.eh_grupo_whatsapp(
            "559999999999-1234567890@g.us"))
        self.assertTrue(listener.eh_grupo_whatsapp(
            None, "553195896796-1624883545@g.us"))
        self.assertTrue(listener.eh_grupo_whatsapp(
            "559999999999-1234567890@G.US"))
        self.assertFalse(listener.eh_grupo_whatsapp(
            "+5551999990001", "+5551999990001"))
        self.assertFalse(listener.eh_grupo_whatsapp(None, None))
        self.assertFalse(listener.eh_grupo_whatsapp(
            "eab057e8-88ce-4893-89f1-41429722efaa"))

    def test_grupo_whatsapp_nunca_cumprimenta(self):
        # Trava geral (decisão do usuário 2026-11-22): grupo de
        # WhatsApp NÃO listado em ignorados.json também não recebe
        # cumprimento — nem com pedido na mensagem. A mensagem segue
        # enfileirada (o Muse decide o que fazer com ela).
        grupo = "559999999999-1234567890@g.us"
        with self._mocks_cumprimento():
            _, body = _post(self.base, "/webhooks/chatwoot",
                            _payload_incoming(
                                6801, conversation_id=213,
                                telefone=None, identifier=grupo,
                                texto="oi, quanto custa a fita"))
            self.assertEqual(body["detail"], "ok")
            self.assertNotIn(213, listener._TIMERS)
        _, body = _get(self.base, "/pending")
        self.assertEqual(len(body["pending"]), 1)
        self.assertEqual(body["pending"][0]["contato_ref"], grupo)
        self.assertIsNone(body["pending"][0]["cumprimento"])
        self.assertEqual(self._n_cumprimentos(), 0)

    def test_grupo_whatsapp_pelo_contato_ref(self):
        # Sem identifier: o JID chega como telefone/contato_ref e a
        # trava vale do mesmo jeito.
        grupo = "559999999999-1234567890@g.us"
        _, body = _post(self.base, "/webhooks/chatwoot",
                        _payload_incoming(
                            6802, conversation_id=214,
                            telefone=grupo, identifier=None,
                            texto="Bom dia"))
        self.assertEqual(body["detail"], "ok")
        self.assertNotIn(214, listener._TIMERS)
        self.assertEqual(self._n_cumprimentos(), 0)

    def test_grupo_primeira_mensagem_continua_suprimido(self):
        # Trava geral sob a regra nova: primeira mensagem, só
        # saudação (dispararia numa conversa 1:1), continua sem
        # cumprimento em grupo.
        grupo = "559999999999-1234567890@g.us"
        with self._mocks_cumprimento(mensagens=(True, [])):
            _, body = _post(self.base, "/webhooks/chatwoot",
                            _payload_incoming(
                                7008, conversation_id=226,
                                telefone=None, identifier=grupo,
                                texto="Bom dia"))
            self.assertEqual(body["detail"], "ok")
            self.assertNotIn(226, listener._TIMERS)
        _, body = _get(self.base, "/pending")
        self.assertEqual(len(body["pending"]), 1)
        self.assertIsNone(body["pending"][0]["cumprimento"])
        self.assertEqual(self._n_cumprimentos(), 0)

    def test_cumprimento_dispara_mesmo_com_handoff(self):
        def fake_aplicar(conversation_id, motivo):
            return {"ignorado": False, "aplicado": True,
                    "etiqueta": "handoff-humano", "assignee_id": 2,
                    "etiquetada": True, "atribuida": True, "nota": True}

        with self._mocks_cumprimento(), \
                mock.patch.object(
                    handoff, "detectar_handoff",
                    return_value={"motivo": "pedido-humano-teste",
                                  "regra": "teste"}), \
                mock.patch.object(handoff, "aplicar_handoff",
                                  side_effect=fake_aplicar):
            listener._handoff_tentado = False
            listener._handoff = None
            _, body = _post(
                self.base, "/webhooks/chatwoot",
                self._incoming(
                    6601, 207, "quero falar com um humano"))
            self.assertEqual(body["detail"], "handoff")
            self._disparar(207)
        self.assertEqual(self._n_cumprimentos(), 1)
        _, body = _get(self.base, "/pending")
        self.assertIsNotNone(body["pending"][0]["cumprimento"])

    def test_duplicado_nao_reenvia_cumprimento(self):
        payload = self._incoming(6701, 208, "oi")
        with self._mocks_cumprimento():
            _, first = _post(self.base, "/webhooks/chatwoot", payload)
            self.assertEqual(first["detail"], "ok")
            _, second = _post(self.base, "/webhooks/chatwoot", payload)
            self.assertEqual(second["detail"], "duplicada")
            self._disparar(208)
        self.assertEqual(self._n_cumprimentos(), 1)


if __name__ == "__main__":
    unittest.main()
