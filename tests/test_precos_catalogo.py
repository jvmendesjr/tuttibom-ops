"""Os 18 SKUs e os preços da captura, sem ler o Deskcomm."""

from decimal import Decimal

from tuttibom.contratos.precos import PRECOS_SKU, PRECOS_VALIDOS

# Transcrição de catalogo/produto-fita-cetim.md (captura 2026-10-30).
ESPERADO = {
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


def test_dezoito_combinacoes():
    codigos = {
        f"FITA-{largura}-{metros}-{cor}"
        for largura in ("15", "22")
        for metros in ("10", "25", "50")
        for cor in ("PRETO", "DOURADO", "PRATA")
    }
    assert set(PRECOS_SKU) == codigos
    assert len(PRECOS_SKU) == 18


def test_precos_batem_com_o_documento():
    assert PRECOS_SKU == ESPERADO


def test_doze_valores_distintos_porque_o_metalizado_compartilha():
    assert len(PRECOS_VALIDOS) == 12
    assert Decimal("99.90") not in PRECOS_VALIDOS
    assert Decimal("71.90") in PRECOS_VALIDOS
