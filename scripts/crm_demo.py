"""Demonstração dos critérios de saída da V2 (D-012) — banco temporário.

Roda o caminho feliz e os dois fechamentos contra um SQLite em
diretório temporário e imprime PASS/FAIL por critério. Dados fictícios.
Uso: python3 scripts/crm_demo.py (a partir da raiz do repo).
"""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tuttibom.crm.store import CRM


def main() -> int:
    falhas = []

    def check(nome: str, condicao: bool) -> None:
        print(f"{'PASS' if condicao else 'FAIL'}  {nome}")
        if not condicao:
            falhas.append(nome)

    with tempfile.TemporaryDirectory() as tmp:
        crm = CRM(Path(tmp) / "demo.sqlite3")
        try:
            check("catálogo com 18 SKUs", crm.contar_produtos() == 18)

            # Lead 1: Novo contato -> Pedido pago.
            lead = crm.criar_lead(
                referencia="lead-demo-01",
                contato_ref="contato-demo-01",
                canal="whatsapp",
                proxima_acao="Responder saudação",
                data_followup="2026-11-22",
                interesse="fita",
                produto_sku="FITA-22-50-PRETO",
            )
            crm.registrar_mensagem(
                lead["id"], "inbound", "perguntou preço da fita 22 mm 50 m"
            )
            for etapa in (
                "Já respondi",
                "Escolhendo o produto",
                "Vai levar",
                "Aguardando pagamento",
            ):
                lead = crm.mover_etapa(lead["id"], etapa)
            lead = crm.fechar_lead(lead["id"], ganho=True)
            check("lead 1 chega a Pedido pago", lead["etapa"] == "Pedido pago")

            # Lead 2: Novo contato -> Não comprou, com motivo.
            lead2 = crm.criar_lead(
                referencia="lead-demo-02",
                contato_ref="contato-demo-02",
                canal="messenger",
                proxima_acao="Responder saudação",
                data_followup="2026-11-22",
                interesse="preco",
            )
            lead2 = crm.fechar_lead(
                lead2["id"], ganho=False, motivo_perda="sem_resposta"
            )
            check(
                "lead 2 fecha como Não comprou (sem_resposta)",
                lead2["etapa"] == "Não comprou"
                and lead2["motivo_perda"] == "sem_resposta",
            )

            # Retorno: o contato 01 volta e é reconhecido.
            crm.registrar_interesse(
                "contato-demo-01", "fita", "FITA-22-50-PRETO"
            )
            memoria = crm.reconhecer_retorno("contato-demo-01")
            check(
                "retorno reconhecido pelo interesse (fita)",
                memoria is not None and memoria["interesse"] == "fita",
            )
        finally:
            crm.close()

    print(f"\n{'V2 OK' if not falhas else 'V2 FALHOU'}: {len(falhas)} falha(s)")
    return 0 if not falhas else 1


if __name__ == "__main__":
    raise SystemExit(main())
