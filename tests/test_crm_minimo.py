"""Testes do CRM próprio mínimo — D-012, V2 (stdlib unittest).

Cobre os critérios de saída da V2, com dados fictícios (nenhum dado
de comprador, nenhum telefone, nenhum nome real):
1. lead vai de Novo contato a Pedido pago, sem pular etapa;
2. lead vai a Não comprou com motivo (e sem motivo falha);
3. contato que volta é reconhecido pelo interesse anterior;
4. catálogo tem os 18 SKUs com os preços da captura;
5. follow-up de silêncio é cancelado quando a pessoa responde;
6. transição proibida e SKU fora do catálogo falham;
7. PII é rejeitado em texto livre.
8. prévia (Modo A): pedido marca 'pendente', entrega marca 'entregue'
   com data, referência da imagem e resumo na conversa; nova solicitação
   limpa a entrega anterior; bancos antigos ganham as colunas na abertura.
"""

import sqlite3
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tuttibom.crm.store import CRM
from tuttibom.contratos.precos import PRECOS_SKU


class TestCRMMinimo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.crm = CRM(Path(self.tmp.name) / "teste.sqlite3")

    def tearDown(self):
        self.crm.close()
        self.tmp.cleanup()

    def _lead(self, ref="lead-teste-01", contato="contato-teste-01"):
        return self.crm.criar_lead(
            referencia=ref,
            contato_ref=contato,
            canal="whatsapp",
            proxima_acao="Responder saudação",
            data_followup="2026-11-22",
            interesse="fita",
            produto_sku="FITA-22-50-PRETO",
        )

    def test_catalogo_tem_18_skus_com_precos_da_captura(self):
        self.assertEqual(self.crm.contar_produtos(), 18)
        self.assertEqual(
            self.crm.produto_preco("FITA-22-50-PRETO"), Decimal("71.90")
        )
        self.assertEqual(
            self.crm.produto_preco("FITA-15-10-DOURADO"), Decimal("19.00")
        )
        with self.assertRaises(ValueError):
            self.crm.produto_preco("FITA-99-99-ROSA")

    def test_reabrir_banco_atualiza_preco_sem_perder_lead(self):
        lead = self._lead()
        sku = lead["produto_sku"]
        preco_novo = self.crm.produto_preco(sku) + Decimal("1.00")
        with patch.dict(PRECOS_SKU, {sku: preco_novo}):
            reaberto = CRM(self.crm.db_path)
            try:
                self.assertEqual(reaberto.produto_preco(sku), preco_novo)
                self.assertEqual(reaberto.obter_lead(lead["id"]), lead)
                self.assertEqual(reaberto.contar_produtos(), 18)
            finally:
                reaberto.close()

    def test_lead_vai_a_pedido_pago_sem_pular_etapa(self):
        lead = self._lead()
        self.assertEqual(lead["etapa"], "Novo contato")
        for etapa in (
            "Já respondi",
            "Escolhendo o produto",
            "Vai levar",
            "Aguardando pagamento",
        ):
            lead = self.crm.mover_etapa(lead["id"], etapa)
        lead = self.crm.fechar_lead(lead["id"], ganho=True)
        self.assertEqual(lead["etapa"], "Pedido pago")
        # Pedido pago é terminal.
        with self.assertRaises(ValueError):
            self.crm.mover_etapa(lead["id"], "Novo contato")

    def test_pular_etapa_falha(self):
        lead = self._lead()
        with self.assertRaises(ValueError):
            self.crm.mover_etapa(lead["id"], "Vai levar")

    def test_lead_perdido_exige_motivo_e_registra(self):
        lead = self._lead()
        with self.assertRaises(ValueError):
            self.crm.mover_etapa(lead["id"], "Não comprou")
        with self.assertRaises(ValueError):
            self.crm.mover_etapa(
                lead["id"], "Não comprou", motivo_perda="motivo livre"
            )
        lead = self.crm.fechar_lead(lead["id"], ganho=False, motivo_perda="preco")
        self.assertEqual(lead["etapa"], "Não comprou")
        self.assertEqual(lead["motivo_perda"], "preco")
        # Lead perdido pode reabrir.
        lead = self.crm.mover_etapa(lead["id"], "Novo contato")
        self.assertEqual(lead["etapa"], "Novo contato")

    def test_retorno_reconhecido_pelo_interesse(self):
        self.crm.registrar_interesse(
            "contato-teste-01", "fita", "FITA-22-50-PRETO"
        )
        memoria = self.crm.reconhecer_retorno("contato-teste-01")
        self.assertIsNotNone(memoria)
        self.assertEqual(memoria["interesse"], "fita")
        self.assertEqual(memoria["ultimo_produto_sku"], "FITA-22-50-PRETO")
        self.assertIsNone(self.crm.reconhecer_retorno("contato-novo-99"))

    def test_followup_silencio_cancelado_ao_responder(self):
        lead = self._lead()
        followup = self.crm.agendar_followup(
            lead["id"], "silencio", "2026-11-22T11:00:00+00:00"
        )
        self.assertEqual(len(self.crm.followups_pendentes(lead["id"])), 1)
        self.crm.registrar_mensagem(
            lead["id"], "inbound", "perguntou preço da fita 22 mm 50 m"
        )
        self.assertEqual(self.crm.followups_pendentes(lead["id"]), [])
        row = self.crm.conn.execute(
            "SELECT estado FROM followups WHERE id = ?", (followup["id"],)
        ).fetchone()
        self.assertEqual(row["estado"], "cancelado")

    def test_pii_rejeitado_em_texto_livre(self):
        lead = self._lead()
        with self.assertRaises(ValueError):
            self.crm.registrar_mensagem(
                lead["id"], "inbound", "meu telefone é 88999999999"
            )
        with self.assertRaises(ValueError):
            self.crm.criar_lead(
                referencia="lead-teste-02",
                contato_ref="contato-teste-02",
                canal="messenger",
                proxima_acao="ligar para 88999999999",
            )

    def test_previa_solicitada_marca_pendente(self):
        lead = self._lead()
        self.assertIsNone(lead["previa_status"])
        self.assertIsNone(lead["previa_entregue_em"])
        self.assertIsNone(lead["previa_imagem_ref"])
        lead = self.crm.marcar_previa_solicitada(lead["id"])
        self.assertEqual(lead["previa_status"], "pendente")
        self.assertIsNone(lead["previa_entregue_em"])
        self.assertIsNone(lead["previa_imagem_ref"])

    def test_previa_entregue_marca_entregue_e_registra_resumo(self):
        lead = self._lead()
        self.crm.marcar_previa_solicitada(lead["id"])
        ref = "PREV-contato-teste-01-aniversario-2026-11-22"
        lead = self.crm.marcar_previa_entregue(lead["id"], ref)
        self.assertEqual(lead["previa_status"], "entregue")
        self.assertIsNotNone(lead["previa_entregue_em"])
        self.assertEqual(lead["previa_imagem_ref"], ref)
        row = self.crm.conn.execute(
            "SELECT direcao, resumo FROM mensagens WHERE lead_id = ?",
            (lead["id"],),
        ).fetchone()
        self.assertEqual(row["direcao"], "outbound")
        self.assertIn(ref, row["resumo"])

    def test_previa_nova_solicitacao_limpa_entrega_anterior(self):
        lead = self._lead()
        self.crm.marcar_previa_entregue(
            lead["id"], "PREV-contato-teste-01-aniversario-2026-11-22"
        )
        lead = self.crm.marcar_previa_solicitada(lead["id"])
        self.assertEqual(lead["previa_status"], "pendente")
        self.assertIsNone(lead["previa_entregue_em"])
        self.assertIsNone(lead["previa_imagem_ref"])

    def test_previa_imagem_ref_invalida_falha(self):
        lead = self._lead()
        with self.assertRaises(ValueError):
            self.crm.marcar_previa_entregue(lead["id"], "x")
        with self.assertRaises(ValueError):
            self.crm.marcar_previa_entregue(
                lead["id"], "meu telefone é 88999999999"
            )

    def test_migracao_adiciona_colunas_em_banco_antigo(self):
        # Banco criado com o esquema antigo (sem as colunas da prévia).
        path = Path(self.tmp.name) / "antigo.sqlite3"
        conn = sqlite3.connect(path)
        conn.execute(
            "CREATE TABLE leads (id INTEGER PRIMARY KEY,"
            " referencia TEXT NOT NULL UNIQUE, contato_ref TEXT NOT NULL,"
            " canal TEXT NOT NULL, etapa TEXT NOT NULL,"
            " proxima_acao TEXT NOT NULL, criado_em TEXT NOT NULL,"
            " atualizado_em TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE produtos (sku TEXT PRIMARY KEY,"
            " tipo TEXT NOT NULL, largura_mm INTEGER, metragem_m INTEGER,"
            " cor_impressao TEXT, preco_centavos INTEGER NOT NULL)"
        )
        conn.commit()
        conn.close()
        crm_antigo = CRM(path)
        cols = {
            r[1]
            for r in crm_antigo.conn.execute("PRAGMA table_info(leads)")
        }
        self.assertIn("previa_status", cols)
        self.assertIn("previa_entregue_em", cols)
        self.assertIn("previa_imagem_ref", cols)
        crm_antigo.close()


if __name__ == "__main__":
    unittest.main()
