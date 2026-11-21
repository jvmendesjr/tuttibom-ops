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
"""

import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tuttibom.crm.store import CRM


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


if __name__ == "__main__":
    unittest.main()
