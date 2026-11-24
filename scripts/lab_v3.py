"""Laboratório V3 (D-012) — conversa simulada ponta a ponta.

Personas 100% fictícias, banco SQLite temporário, NENHUM canal real:
não toca em WAHA, Zernio, número do WhatsApp ou página do Facebook.
As respostas da Ana aqui são o comportamento esperado segundo a skill
(`skills/ana-atendimento/SKILL.md`, commit c918ea0) — o laboratório
verifica cada resposta contra as regras duras e cada passo contra o
CRM (`src/tuttibom/crm/`, commit 54f271c). Não é um teste de LLM: é o
teste do fluxo (skill + CRM). Se uma checagem falhar, a falha vira
correção no documento do setor, não exceção.

Cenário A (caminho feliz): fita 22 mm / 50 m / Preto para aniversário
-> preço do catálogo -> frete sem valor -> prévia Modo A com aprovação
-> fechamento -> pagamento confirmado -> Pedido pago.
Cenário B (regras duras): desconto negado, frete sem valor, silêncio
-> follow-up -> Não comprou (sem_resposta).

Uso: python3 scripts/lab_v3.py [--report docs/lab-v3-relatorio.md]
Saída: PASS/FAIL por checagem + relatório em Markdown. Exit 0 só se
tudo passar.
"""

import argparse
import re
import sys
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tuttibom.contratos.pii import detectar_pii
from tuttibom.contratos.precos import PRECOS_VALIDOS
from tuttibom.crm.store import CRM

SKILL_COMMIT = "c918ea0"
CRM_COMMIT = "54f271c"

_R_REAIS = re.compile(r"R\$\s*(\d+,\d{2})")


class Lab:
    def __init__(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.crm = CRM(Path(self.tmp.name) / "lab.sqlite3")
        self.passou: list[str] = []
        self.falhou: list[str] = []
        self.transcricao: list[str] = []

    def close(self) -> None:
        self.crm.close()
        self.tmp.cleanup()

    def check(self, nome: str, condicao: bool, detalhe: str = "") -> None:
        linha = f"{'PASS' if condicao else 'FAIL'}  {nome}"
        if detalhe and not condicao:
            linha += f"  ({detalhe})"
        print(linha)
        (self.passou if condicao else self.falhou).append(nome)

    # -- checagens de resposta da Ana --------------------------------

    def check_resposta(self, nome: str, reply: str, *, sem_valor: bool = False) -> None:
        """Regras que valem para TODA resposta da Ana."""
        self.check(f"{nome}: sem 'gestor'", "gestor" not in reply.lower())
        self.check(
            f"{nome}: não se diz robô/virtual",
            "robô" not in reply.lower()
            and "assistente virtual" not in reply.lower()
            and "sou virtual" not in reply.lower(),
        )
        self.check(
            f"{nome}: não diz que vai transferir",
            "transferir" not in reply.lower(),
        )
        self.check(
            f"{nome}: uma pergunta por vez",
            reply.count("?") <= 1,
            f"{reply.count('?')} interrogações",
        )
        self.check(
            f"{nome}: sem dado pessoal",
            detectar_pii(reply) is None,
            f"PII: {detectar_pii(reply)}",
        )
        for valor in _R_REAIS.findall(reply):
            dec = Decimal(valor.replace(",", "."))
            self.check(
                f"{nome}: R$ {valor} é preço do catálogo",
                dec in PRECOS_VALIDOS,
                "valor fora do catálogo",
            )
        if sem_valor:
            self.check(
                f"{nome}: frete sem nenhum valor",
                "R$" not in reply,
            )

    def turno(
        self,
        lead_id: int,
        inbound: str,
        reply: str,
        nome: str,
        *,
        sem_valor: bool = False,
        resumo: str | None = None,
    ) -> None:
        self.transcricao.append(f"**Cliente (fictício):** {inbound}")
        self.transcricao.append(f"**Ana:** {reply}")
        self.crm.registrar_mensagem(
            lead_id, "inbound", resumo or f"cliente disse: {inbound}"
        )
        self.crm.registrar_mensagem(lead_id, "outbound", reply[:120])
        self.check_resposta(nome, reply, sem_valor=sem_valor)

    # -- cenários ------------------------------------------------------

    def cenario_a(self) -> None:
        print("\n== Cenário A — fita de aniversário até Pedido pago ==")
        lead = self.crm.criar_lead(
            referencia="lead-lab-a",
            contato_ref="contato-lab-a",
            canal="whatsapp",
            proxima_acao="Responder saudação",
            data_followup="2026-11-22",
        )
        lid = lead["id"]
        self.turno(
            lid, "oi", "Oi! Me conta o que você está buscando que eu te ajudo.",
            "A1 saudação",
        )
        self.crm.mover_etapa(lid, "Já respondi")
        self.turno(
            lid,
            "quero uma fita para aniversário",
            "Para qual ocasião é a fita, aniversário de criança ou de adulto?",
            "A2 ocasião primeiro",
        )
        self.crm.mover_etapa(lid, "Escolhendo o produto")
        self.crm.registrar_interesse("contato-lab-a", "fita")
        self.turno(
            lid,
            "aniversário de criança, fita 22 mm 50 m preta",
            "A fita de 22 mm com 50 m e impressão preta fica R$ 71,90. "
            "Qual cor de fita você quer?",
            "A3 preço do catálogo",
        )
        self.check(
            "A3: preço citado é o do SKU FITA-22-50-PRETO",
            self.crm.produto_preco("FITA-22-50-PRETO") == Decimal("71.90"),
        )
        self.turno(
            lid,
            "quanto fica o frete para Juazeiro?",
            "Me passa o endereço completo que eu verifico com o produtor "
            "e te retorno, pode aguardar?",
            "A4 frete sem valor",
            sem_valor=True,
        )
        self.turno(
            lid,
            "quero ver como fica antes de fechar",
            "Quer que eu monte uma prévia para você ver como fica na fita? "
            "É uma simulação que eu preparo para você visualizar antes de confirmar.",
            "A5 prévia oferecida como pergunta",
        )
        self.check(
            "A5: prévia com rótulo de simulação",
            "simulação" in self.transcricao[-1].lower(),
        )
        self.crm.mover_etapa(lid, "Vai levar")
        # Aprovação da prévia (simulada, pelo usuário) + fechamento.
        self.crm.mover_etapa(lid, "Aguardando pagamento")
        self.crm.registrar_mensagem(
            lid, "outbound", "prévia aprovada pelo usuário, pedido fechado"
        )
        lead = self.crm.fechar_lead(lid, ganho=True)
        self.check("A6: lead chega a Pedido pago", lead["etapa"] == "Pedido pago")
        memoria = self.crm.reconhecer_retorno("contato-lab-a")
        self.check(
            "A7: retorno reconhecido pelo interesse (fita)",
            memoria is not None and memoria["interesse"] == "fita",
        )

    def cenario_b(self) -> None:
        print("\n== Cenário B — desconto, frete e silêncio até Não comprou ==")
        lead = self.crm.criar_lead(
            referencia="lead-lab-b",
            contato_ref="contato-lab-b",
            canal="messenger",
            proxima_acao="Responder saudação",
            data_followup="2026-11-22",
            interesse="preco",
        )
        lid = lead["id"]
        self.turno(
            lid, "oi", "Oi! Me conta o que você está buscando que eu te ajudo.",
            "B1 saudação",
        )
        self.crm.mover_etapa(lid, "Já respondi")
        reply_desconto = (
            "O valor já é bom e justo e, infelizmente, não podemos dar "
            "desconto. Você continua com interesse? Fico à disposição "
            "para tirar dúvidas sobre o produto."
        )
        self.turno(
            lid, "faz por metade do preço?", reply_desconto, "B2 desconto negado"
        )
        self.check(
            "B2: desconto negado sem escalar ao produtor",
            "produtor" not in reply_desconto.lower(),
        )
        self.check(
            "B2: desconto negado com a frase da regra",
            "não podemos dar desconto" in reply_desconto.lower(),
        )
        self.crm.agendar_followup(lid, "silencio", "2026-11-22T11:00:00+00:00")
        self.check(
            "B3: follow-up de silêncio agendado",
            len(self.crm.followups_pendentes(lid)) == 1,
        )
        # Silêncio: nenhum inbound. O follow-up dispara (simulado) e,
        # sem resposta, o lead fecha como perdido.
        lead = self.crm.fechar_lead(lid, ganho=False, motivo_perda="sem_resposta")
        self.check(
            "B4: lead fecha como Não comprou (sem_resposta)",
            lead["etapa"] == "Não comprou"
            and lead["motivo_perda"] == "sem_resposta",
        )

    # -- relatório -----------------------------------------------------

    def relatorio(self, caminho: Path) -> None:
        agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
        total = len(self.passou) + len(self.falhou)
        linhas = [
            "# Laboratório V3 — relatório",
            "",
            f"**Rodado em:** {agora} (UTC) — banco SQLite temporário, "
            "personas fictícias, nenhum canal real.",
            f"**Entradas:** skill da Ana `{SKILL_COMMIT}` "
            f"(`exp/atendimento-ana`), CRM `{CRM_COMMIT}` (`exp/crm-proprio`).",
            "",
            f"**Resultado: {len(self.passou)}/{total} checagens passaram; "
            f"{len(self.falhou)} falharam.**",
            "",
        ]
        if self.falhou:
            linhas += ["## Falhas (viram correção no setor, não exceção)", ""]
            linhas += [f"- {f}" for f in self.falhou]
            linhas += [""]
        linhas += ["## Transcrição (fictícia)", ""]
        linhas += self.transcricao
        linhas += [
            "",
            "## O que NÃO foi testado aqui",
            "",
            "- O texto exato da v12-B (só no painel do Deskcomm).",
            "- WAHA, Zernio, número e página: nenhum foi tocado.",
            "- O LLM gerando a resposta: as respostas acima são o "
            "comportamento esperado segundo a skill, verificado por "
            "checagens determinísticas — não geração ao vivo.",
            "- Frete com valor real e endereço pós-pagamento: fora do "
            "laboratório, com o produtor, no V4.",
            "",
        ]
        caminho.write_text("\n".join(linhas), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--report",
        default="docs/lab-v3-relatorio.md",
        help="caminho do relatório Markdown (relativo à raiz do repo)",
    )
    args = ap.parse_args()
    lab = Lab()
    try:
        lab.cenario_a()
        lab.cenario_b()
    finally:
        lab.close()
    print(
        f"\nV3 {'OK' if not lab.falhou else 'FALHOU'}: "
        f"{len(lab.passou)} passaram, {len(lab.falhou)} falharam"
    )
    lab.relatorio(ROOT / args.report)
    print(f"Relatório: {args.report}")
    return 0 if not lab.falhou else 1


if __name__ == "__main__":
    raise SystemExit(main())
