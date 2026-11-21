"""Funil Vendas e vocabulário do CRM próprio (D-012, V2).

As 7 etapas são as do funil Vendas do Deskcomm, herdadas pelo setor 2
(`docs/setores/02-crm-vendas.md`). Os estágios do contrato F4
(`tuttibom.contratos.lead.EstágioLead`) são outro vocabulário — o da
triagem antiga — e não entram aqui; ver `src/tuttibom/crm/README.md`.
"""

from __future__ import annotations

ETAPAS = (
    "Novo contato",
    "Já respondi",
    "Escolhendo o produto",
    "Vai levar",
    "Aguardando pagamento",
    "Pedido pago",
    "Não comprou",
)

ETAPA_GANHOU = "Pedido pago"
ETAPA_PERDEU = "Não comprou"

# Transição permitida: o funil anda para a frente, pode perder em
# qualquer etapa, e um lead perdido pode REABRIR (o Junior voltou
# depois de perdido, 2026-11-18). "Pedido pago" é terminal.
TRANSICOES = {
    "Novo contato": {"Já respondi", "Não comprou"},
    "Já respondi": {"Escolhendo o produto", "Não comprou"},
    "Escolhendo o produto": {"Vai levar", "Não comprou"},
    "Vai levar": {"Aguardando pagamento", "Não comprou"},
    "Aguardando pagamento": {"Pedido pago", "Não comprou"},
    "Pedido pago": set(),
    "Não comprou": {"Novo contato"},
}

MOTIVOS_PERDA = {
    "preco": "preço",
    "desistiu": "desistiu",
    "sem_resposta": "sem resposta",
    "produto_indisponivel": "produto indisponível",
    "prazo_nao_atende": "prazo não atende",
}

# Rótulos do roteador Jev / memória por contato. Só o rótulo circula —
# nunca PII.
INTERESSES = ("fita", "impressao_3d", "preco")

CANAIS = ("whatsapp", "messenger")

TIPOS_FOLLOWUP = ("silencio", "pagamento")


def transicao_permitida(de: str, para: str) -> bool:
    """True se o funil permite ir de `de` para `para`."""
    return para in TRANSICOES.get(de, set())
