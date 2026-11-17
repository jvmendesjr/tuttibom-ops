"""Preços da captura Shopee de 2026-10-30.

Fonte dos valores: `catalogo/produto-fita-cetim.md`. Os códigos
`FITA-<mm>-<m>-<COR>` são os 18 produtos do Deskcomm (citados nos
docs do projeto). O documento do produto não lista esses códigos;
a tabela abaixo só liga o código ao preço que o documento já traz.
Não alterar valor sem decisão — é ponto de partida, não preço novo.
"""

from __future__ import annotations

import re
from decimal import Decimal

# 18 SKUs. Cores metalizadas do mesmo tamanho compartilham o preço.
PRECOS_SKU: dict[str, Decimal] = {
    "FITA-22-50-PRETO": Decimal("71.90"),
    "FITA-22-50-DOURADO": Decimal("88.90"),
    "FITA-22-50-PRATA": Decimal("88.90"),
    "FITA-22-25-PRETO": Decimal("38.90"),
    "FITA-22-25-DOURADO": Decimal("47.90"),
    "FITA-22-25-PRATA": Decimal("47.90"),
    "FITA-22-10-PRETO": Decimal("18.90"),
    "FITA-22-10-DOURADO": Decimal("21.90"),
    "FITA-22-10-PRATA": Decimal("21.90"),
    "FITA-15-10-PRETO": Decimal("15.00"),
    "FITA-15-10-DOURADO": Decimal("19.00"),
    "FITA-15-10-PRATA": Decimal("19.00"),
    "FITA-15-25-PRETO": Decimal("29.00"),
    "FITA-15-25-DOURADO": Decimal("43.00"),
    "FITA-15-25-PRATA": Decimal("43.00"),
    "FITA-15-50-PRETO": Decimal("59.00"),
    "FITA-15-50-DOURADO": Decimal("79.00"),
    "FITA-15-50-PRATA": Decimal("79.00"),
}

PRECOS_VALIDOS = frozenset(PRECOS_SKU.values())

# Moeda explícita. "15 mm" e "3 a 5 dias" não entram.
_PRECO_PUBLICO = re.compile(r"(?i)r\$|\bbrl\b|\d+(?:[.,]\d{2})?\s*reais\b")
# Primeira alternativa exige centavos, para "R$ 71,90" não cair em "71".
_RS = re.compile(r"(?i)r\$\s*(?:(\d{1,4}[.,]\d{2})|(\d{1,4})|())")
_REAIS = re.compile(r"(?i)(\d{1,4}[.,]\d{2}|\d{1,4})\s*reais\b")
_PRECO_UNICO = re.compile(r"\d{1,4}[.,]\d{2}")


def contem_preco(texto: str) -> bool:
    """True se o texto cita moeda (R$, BRL ou reais)."""
    return _PRECO_PUBLICO.search(texto) is not None


def _decimal_com_centavos(bruto: str) -> Decimal:
    if not _PRECO_UNICO.fullmatch(bruto):
        raise ValueError("preço incompleto")
    return Decimal(bruto.replace(",", "."))


def precos_no_texto(texto: str) -> list[Decimal]:
    """Extrai valores com centavos. R$ solto ou sem centavos é erro."""
    if not contem_preco(texto):
        return []
    achados: list[Decimal] = []
    for match in _RS.finditer(texto):
        achados.append(_decimal_com_centavos(match.group(1) or ""))
    for match in _REAIS.finditer(texto):
        achados.append(_decimal_com_centavos(match.group(1) or ""))
    if not achados:
        raise ValueError("preço incompleto")
    return achados


def validar_precos_de_catalogo(texto: str) -> None:
    """Se há preço, cada valor tem de ser um dos 18 da captura."""
    for valor in precos_no_texto(texto):
        if valor not in PRECOS_VALIDOS:
            raise ValueError("preço fora do catálogo Shopee 2026-10-30")


def interpretar_preco(texto: str) -> Decimal:
    """Um preço só, com centavos. Aceita 'R$ 71,90' ou '71.90'."""
    limpo = re.sub(r"\s+", "", texto.strip())
    limpo = re.sub(r"(?i)^(r\$|brl)", "", limpo)
    if not _PRECO_UNICO.fullmatch(limpo):
        raise ValueError("valor de catálogo precisa ser um preço só, com centavos")
    return Decimal(limpo.replace(",", "."))
