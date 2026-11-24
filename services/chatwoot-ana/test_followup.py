"""Testes do runner de follow-up (followup.py) — só stdlib, só dados fictícios.

Banco SQLite temporário (tempfile, em /tmp — nunca no repo) e um cliente
fake do Chatwoot (nenhuma chamada real). Os textos de cliente e os
contatos aqui são FICTÍCIOS; o único número real é o do ignorado
(+5511999990002, Mercado Livre), que vem da lista de ignorados do repo.

Rodar, na raiz do repo:
    python3 -m unittest discover -s services/chatwoot-ana -p 'test_*.py' -v
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "src"))

import followup  # noqa: E402
from tuttibom.crm.store import CRM  # noqa: E402

AGORA = datetime(2026, 11, 21, 12, 0, 0, tzinfo=timezone.utc)
AGENDADO = "2026-11-21T10:00:00+00:00"  # vencido em relação a AGORA

# Contatos e textos FICTÍCIOS (nunca de cliente real).
FONE_FICTICIO = "+5588999990004"
CONTATO_REF_FONE = "contato-5588999990004"
IDENTIFIER_FICTICIO = "msg-ficticio-12345"
FONE_IGNORADO = "+5511999990002"  # Mercado Livre, da lista de ignorados


def _epoch(iso: str) -> int:
    return int(datetime.fromisoformat(iso).timestamp())


def _conversa(conv_id, telefone=None, identifier=None, inbox_id=1):
    return {
        "id": conv_id,
        "inbox_id": inbox_id,
        "meta": {
            "sender": {
                "phone_number": telefone,
                "identifier": identifier,
                "name": "Cliente Teste",
            }
        },
    }


def _msg(msg_id, tipo, criado_iso):
    return {
        "id": msg_id,
        "message_type": tipo,
        "created_at": _epoch(criado_iso),
        "private": False,
    }


class FakeClient:
    """Fake mínimo do chatwoot_client: só listar + ler mensagens."""

    def __init__(self, conversas, mensagens):
        self._conversas = conversas
        self._mensagens = mensagens

    def listar_conversas_abertas(self, inbox_id=None):
        return self._conversas

    def ler_mensagens(self, conversation_id):
        return self._mensagens.get(conversation_id, [])


class TestFollowup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "crm-teste.sqlite3")
        self.drafts = Path(self.tmp.name) / "rascunhos"
        self.crm = CRM(self.db)
        self.templates = followup.carregar_templates()

    def tearDown(self):
        self.crm.close()
        self.tmp.cleanup()

    # ---------------------------------------------------------- helpers
    def _lead(self, ref, contato_ref, etapa=None):
        lead = self.crm.criar_lead(
            referencia=ref,
            contato_ref=contato_ref,
            canal="whatsapp",
            proxima_acao="Responder sobre preco da fita",
            interesse="fita",
        )
        for proxima in (etapa or []):
            self.crm.mover_etapa(lead["id"], proxima)
        return self.crm.obter_lead(lead["id"])

    def _followup(self, lead_id, tipo="silencio", agendado=AGENDADO):
        return self.crm.agendar_followup(lead_id, tipo, agendado)

    def _rodar(self, client):
        saida = io.StringIO()
        with redirect_stdout(saida):
            escritos = followup.executar(
                self.db, self.drafts, client=client, agora=AGORA
            )
        return escritos, saida.getvalue()

    def _ler_rascunho(self, followup_id):
        caminho = self.drafts / f"followup-{followup_id}.json"
        with open(caminho, "r", encoding="utf-8") as fh:
            return json.load(fh)

    # ------------------------------------------------------------- testes
    def test_followup_vencido_gera_rascunho(self):
        lead = self._lead(
            "lead-teste-01", CONTATO_REF_FONE, ["Já respondi", "Escolhendo o produto"]
        )
        fu = self._followup(lead["id"])
        client = FakeClient(
            [_conversa(101, telefone=FONE_FICTICIO)],
            {101: [_msg(1, 0, "2026-11-21T09:00:00+00:00"),
                    _msg(2, 1, "2026-11-21T11:00:00+00:00")]},
        )
        escritos, saida = self._rodar(client)
        self.assertEqual(len(escritos), 1)
        self.assertIn("rascunho:", saida)
        rascunho = self._ler_rascunho(fu["id"])
        self.assertEqual(rascunho["lead_ref"], "lead-teste-01")
        self.assertEqual(rascunho["conversation_id"], 101)
        self.assertEqual(rascunho["inbox_id"], 1)
        self.assertEqual(rascunho["tipo"], "silencio")
        self.assertEqual(rascunho["toque_numero"], 1)
        self.assertEqual(rascunho["texto"], self.templates["silencio"]["1"])
        self.assertEqual(rascunho["agendado_para"], AGENDADO)
        self.assertEqual(rascunho["followup_id"], fu["id"])

    def test_casa_pelo_identifier_quando_nao_ha_telefone(self):
        """Messenger: contato_ref é o identifier, sem telefone."""
        lead = self._lead("lead-teste-02", IDENTIFIER_FICTICIO, ["Já respondi"])
        fu = self._followup(lead["id"])
        client = FakeClient(
            [_conversa(202, identifier=IDENTIFIER_FICTICIO, inbox_id=2)],
            {202: [_msg(1, 0, "2026-11-21T09:00:00+00:00"),
                    _msg(2, 1, "2026-11-21T11:00:00+00:00")]},
        )
        escritos, _ = self._rodar(client)
        self.assertEqual(len(escritos), 1)
        self.assertEqual(self._ler_rascunho(fu["id"])["inbox_id"], 2)

    def test_inbound_apos_agendamento_cancela(self):
        lead = self._lead(
            "lead-teste-03", CONTATO_REF_FONE, ["Já respondi", "Escolhendo o produto"]
        )
        fu = self._followup(lead["id"])
        client = FakeClient(
            [_conversa(101, telefone=FONE_FICTICIO)],
            {101: [_msg(1, 0, "2026-11-21T09:00:00+00:00"),
                    _msg(2, 1, "2026-11-21T09:30:00+00:00"),
                    # Cliente respondeu DEPOIS do agendamento (10h).
                    _msg(3, 0, "2026-11-21T11:00:00+00:00")]},
        )
        escritos, saida = self._rodar(client)
        self.assertEqual(escritos, [])
        self.assertNotIn("rascunho:", saida)
        self.assertFalse((self.drafts / f"followup-{fu['id']}.json").exists())
        estado = self.crm.conn.execute(
            "SELECT estado FROM followups WHERE id = ?", (fu["id"],)
        ).fetchone()[0]
        self.assertEqual(estado, "cancelado")

    def test_terceiro_toque_e_o_ultimo(self):
        lead = self._lead(
            "lead-teste-04", CONTATO_REF_FONE, ["Já respondi", "Escolhendo o produto"]
        )
        # Dois toques já enviados nas últimas 48 h.
        for _ in range(2):
            enviado = self._followup(lead["id"])
            self.crm.marcar_followup(enviado["id"], "enviado")
        fu = self._followup(lead["id"])
        client = FakeClient(
            [_conversa(101, telefone=FONE_FICTICIO)],
            {101: [_msg(1, 0, "2026-11-21T09:00:00+00:00"),
                    _msg(2, 1, "2026-11-21T11:00:00+00:00")]},
        )
        escritos, _ = self._rodar(client)
        self.assertEqual(len(escritos), 1)
        self.assertEqual(escritos[0]["toque_numero"], 3)
        self.assertEqual(
            self._ler_rascunho(fu["id"])["texto"], self.templates["silencio"]["3"]
        )

    def test_quarto_toque_nao_gera(self):
        lead = self._lead(
            "lead-teste-05", CONTATO_REF_FONE, ["Já respondi", "Escolhendo o produto"]
        )
        for _ in range(3):
            enviado = self._followup(lead["id"])
            self.crm.marcar_followup(enviado["id"], "enviado")
        fu = self._followup(lead["id"])
        client = FakeClient(
            [_conversa(101, telefone=FONE_FICTICIO)],
            {101: [_msg(1, 0, "2026-11-21T09:00:00+00:00"),
                    _msg(2, 1, "2026-11-21T11:00:00+00:00")]},
        )
        escritos, _ = self._rodar(client)
        self.assertEqual(escritos, [])
        self.assertFalse((self.drafts / f"followup-{fu['id']}.json").exists())

    def test_lead_fechado_nao_gera(self):
        lead = self._lead(
            "lead-teste-06", CONTATO_REF_FONE, ["Já respondi", "Escolhendo o produto"]
        )
        fu = self._followup(lead["id"])
        self.crm.fechar_lead(lead["id"], ganho=False, motivo_perda="sem_resposta")
        client = FakeClient(
            [_conversa(101, telefone=FONE_FICTICIO)],
            {101: [_msg(1, 0, "2026-11-21T09:00:00+00:00"),
                    _msg(2, 1, "2026-11-21T11:00:00+00:00")]},
        )
        escritos, _ = self._rodar(client)
        self.assertEqual(escritos, [])
        self.assertFalse((self.drafts / f"followup-{fu['id']}.json").exists())

    def test_contato_ignorado_nao_gera(self):
        lead = self._lead("lead-teste-07", "contato-5511999990002", ["Já respondi"])
        fu = self._followup(lead["id"])
        client = FakeClient(
            [_conversa(108, telefone=FONE_IGNORADO)],
            {108: [_msg(1, 0, "2026-11-21T09:00:00+00:00"),
                    _msg(2, 1, "2026-11-21T11:00:00+00:00")]},
        )
        escritos, saida = self._rodar(client)
        self.assertEqual(escritos, [])
        self.assertNotIn("rascunho:", saida)
        self.assertFalse((self.drafts / f"followup-{fu['id']}.json").exists())
        # O follow-up do ignorado nem é cancelado: fica como estava.
        estado = self.crm.conn.execute(
            "SELECT estado FROM followups WHERE id = ?", (fu["id"],)
        ).fetchone()[0]
        self.assertEqual(estado, "pendente")

    def test_pagamento_tem_um_toque_so(self):
        lead = self._lead(
            "lead-teste-08",
            CONTATO_REF_FONE,
            ["Já respondi", "Escolhendo o produto", "Vai levar",
             "Aguardando pagamento"],
        )
        fu = self._followup(lead["id"], tipo="pagamento")
        client = FakeClient(
            [_conversa(101, telefone=FONE_FICTICIO)],
            {101: [_msg(1, 0, "2026-11-21T09:00:00+00:00"),
                    _msg(2, 1, "2026-11-21T11:00:00+00:00")]},
        )
        escritos, _ = self._rodar(client)
        self.assertEqual(len(escritos), 1)
        self.assertEqual(escritos[0]["toque_numero"], 1)
        self.assertEqual(
            self._ler_rascunho(fu["id"])["texto"], self.templates["pagamento"]["1"]
        )
        # Depois de enviado, um segundo follow-up de pagamento não gera.
        self.crm.marcar_followup(fu["id"], "enviado")
        fu2 = self._followup(lead["id"], tipo="pagamento")
        escritos, _ = self._rodar(client)
        self.assertEqual(escritos, [])
        self.assertFalse((self.drafts / f"followup-{fu2['id']}.json").exists())

    def test_rascunho_existente_nao_duplica(self):
        lead = self._lead("lead-teste-09", CONTATO_REF_FONE, ["Já respondi"])
        fu = self._followup(lead["id"])
        client = FakeClient(
            [_conversa(101, telefone=FONE_FICTICIO)],
            {101: [_msg(1, 0, "2026-11-21T09:00:00+00:00"),
                    _msg(2, 1, "2026-11-21T11:00:00+00:00")]},
        )
        escritos, _ = self._rodar(client)
        self.assertEqual(len(escritos), 1)
        # Segunda passada: o rascunho já existe, não gera outro.
        escritos, _ = self._rodar(client)
        self.assertEqual(escritos, [])

    def test_sem_followup_vencido_sem_rascunhos(self):
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = followup.main(
                ["--db", self.db, "--drafts-dir", str(self.drafts)]
            )
        self.assertEqual(codigo, 0)
        self.assertIn("sem-rascunhos", saida.getvalue())


if __name__ == "__main__":
    unittest.main()
