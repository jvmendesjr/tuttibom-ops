"""Testes do crm-dashboard — só stdlib (unittest).

Sobe o servidor com um DB SQLite de teste (tempdir, 2 leads em etapas
diferentes + mensagens + memória + produtos) e verifica auth, métodos
e conteúdo. Textos de teste FICTÍCIOS — nunca texto real de cliente.
Roda no PC: python3 -m unittest discover -s services/crm-dashboard -p 'test_*.py' -v
"""

import os
import sqlite3
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

# Ambiente de teste, antes de importar o dashboard (ele lê o env no import).
_TMP = tempfile.TemporaryDirectory()
_TEST_DB = os.path.join(_TMP.name, "crm-test.sqlite3")
os.environ["CRM_DASHBOARD_DB"] = _TEST_DB
os.environ["CRM_DASHBOARD_TOKEN"] = "token-de-teste-longo-o-bastante"
os.environ["CRM_DASHBOARD_HOST"] = "127.0.0.1"
os.environ["CRM_DASHBOARD_PORT"] = "0"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dashboard  # noqa: E402

TOKEN = "token-de-teste-longo-o-bastante"


def _criar_db_teste(path):
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE produtos (
          sku TEXT PRIMARY KEY, tipo TEXT NOT NULL,
          largura_mm INTEGER, metragem_m INTEGER,
          cor_impressao TEXT, preco_centavos INTEGER NOT NULL);
        CREATE TABLE leads (
          id INTEGER PRIMARY KEY, referencia TEXT NOT NULL UNIQUE,
          contato_ref TEXT NOT NULL, canal TEXT NOT NULL,
          etapa TEXT NOT NULL, produto_sku TEXT REFERENCES produtos(sku),
          interesse TEXT, motivo_perda TEXT, proxima_acao TEXT NOT NULL,
          data_followup TEXT, endereco_coletado INTEGER NOT NULL DEFAULT 0,
          criado_em TEXT NOT NULL, atualizado_em TEXT NOT NULL);
        CREATE TABLE mensagens (
          id INTEGER PRIMARY KEY, lead_id INTEGER NOT NULL,
          direcao TEXT NOT NULL, resumo TEXT NOT NULL,
          criado_em TEXT NOT NULL);
        CREATE TABLE memoria_contato (
          contato_ref TEXT PRIMARY KEY, interesse TEXT NOT NULL,
          ultimo_produto_sku TEXT, atualizado_em TEXT NOT NULL);
        CREATE TABLE followups (
          id INTEGER PRIMARY KEY, lead_id INTEGER NOT NULL,
          tipo TEXT NOT NULL, agendado_para TEXT NOT NULL,
          estado TEXT NOT NULL DEFAULT 'pendente',
          criado_em TEXT NOT NULL);
        """
    )
    conn.executemany(
        "INSERT INTO produtos VALUES (?,?,?,?,?,?)",
        [
            ("FITA-15-10-DOURADO", "fita_cetim", 15, 10, "DOURADO", 1900),
            ("FITA-22-50-PRETO", "fita_cetim", 22, 50, "PRETO", 7190),
        ],
    )
    conn.executemany(
        "INSERT INTO leads VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                1, "cliente-teste-a-whatsapp-20261122", "contato-5551999990001",
                "whatsapp", "Já respondi", "FITA-15-10-DOURADO", "fita",
                None, "Aguardar resposta do cliente fictício",
                "2026-11-23T12:00:00-03:00", 0,
                "2026-11-22T10:00:00-03:00", "2026-11-22T10:00:00-03:00",
            ),
            (
                2, "cliente-teste-b-messenger-20261122", "contato-5551999990002",
                "messenger", "Novo contato", None, "preco",
                None, "Responder com o preço do catálogo <b>teste</b>",
                None, 0,
                "2026-11-22T11:00:00-03:00", "2026-11-22T11:00:00-03:00",
            ),
        ],
    )
    conn.executemany(
        "INSERT INTO mensagens VALUES (?,?,?,?,?)",
        [
            (1, 1, "inbound", "Pergunta fictícia sobre preço da fita",
             "2026-11-22T10:00:00-03:00"),
            (2, 1, "outbound", "Resposta fictícia da Ana com o preço",
             "2026-11-22T10:05:00-03:00"),
            (3, 2, "inbound", "Saudação fictícia",
             "2026-11-22T11:00:00-03:00"),
        ],
    )
    conn.executemany(
        "INSERT INTO memoria_contato VALUES (?,?,?,?)",
        [
            ("contato-5551999990001", "fita", "FITA-15-10-DOURADO",
             "2026-11-22T10:00:00-03:00"),
        ],
    )
    conn.executemany(
        "INSERT INTO followups VALUES (?,?,?,?,?,?)",
        [
            (1, 1, "silencio", "2026-11-23T12:00:00-03:00", "pendente",
             "2026-11-22T10:00:00-03:00"),
        ],
    )
    conn.commit()
    conn.close()


def _request(base, path, method="GET"):
    req = urllib.request.Request(base + path, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


class DashboardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _criar_db_teste(_TEST_DB)
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), dashboard.Handler
        )
        cls.thread = threading.Thread(
            target=cls.server.serve_forever, daemon=True
        )
        cls.thread.start()
        cls.base = "http://127.0.0.1:{}".format(
            cls.server.server_address[1]
        )

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_get_com_token_retorna_200_e_contem_os_dados(self):
        status, body = _request(self.base, "/?token=" + TOKEN)
        self.assertEqual(status, 200)
        self.assertIn("CRM TuttiBom", body)
        self.assertIn("contato-5551999990001", body)
        self.assertIn("contato-5551999990002", body)
        self.assertIn("Já respondi", body)
        self.assertIn("Novo contato", body)
        self.assertIn("FITA-15-10-DOURADO", body)
        self.assertIn("R$ 19,00", body)
        self.assertIn("Pergunta fictícia sobre preço da fita", body)
        self.assertIn("Memória do contato", body)
        self.assertIn("Follow-ups pendentes", body)
        self.assertIn("silencio", body)
        self.assertIn("Catálogo", body)
        self.assertIn("FITA-22-50-PRETO", body)
        self.assertIn("R$ 71,90", body)

    def test_html_escapa_valores_do_banco(self):
        status, body = _request(self.base, "/?token=" + TOKEN)
        self.assertEqual(status, 200)
        self.assertIn("&lt;b&gt;teste&lt;/b&gt;", body)
        self.assertNotIn("<b>teste</b>", body)

    def test_get_sem_token_retorna_401(self):
        status, _body = _request(self.base, "/")
        self.assertEqual(status, 401)

    def test_get_com_token_errado_retorna_401(self):
        status, _body = _request(self.base, "/?token=errado")
        self.assertEqual(status, 401)

    def test_health_aberto_sem_token(self):
        status, body = _request(self.base, "/health")
        self.assertEqual(status, 200)
        self.assertIn('"ok": true', body)
        self.assertIn("crm-dashboard", body)

    def test_post_retorna_405(self):
        status, _body = _request(self.base, "/?token=" + TOKEN, method="POST")
        self.assertEqual(status, 405)

    def test_path_desconhecido_retorna_404(self):
        status, _body = _request(
            self.base, "/inexistente?token=" + TOKEN
        )
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
