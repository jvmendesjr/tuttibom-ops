"""Contratos Pydantic v2 — TuttiBom F4.

Publicacao, Criativo e Lead. Validação antes de publicar ou de
gravar ficha no repositório. Ver README deste pacote.
"""

from tuttibom.contratos.comum import Formato
from tuttibom.contratos.criativo import Botao, Criativo, TextoCriativo, ZonasSeguras
from tuttibom.contratos.lead import EstagioLead, Lead
from tuttibom.contratos.precos import PRECOS_SKU, PRECOS_VALIDOS
from tuttibom.contratos.publicacao import TEXTO_PILOTO, Publicacao, Rede

__all__ = [
    "PRECOS_SKU",
    "PRECOS_VALIDOS",
    "TEXTO_PILOTO",
    "Botao",
    "Criativo",
    "EstagioLead",
    "Formato",
    "Lead",
    "Publicacao",
    "Rede",
    "TextoCriativo",
    "ZonasSeguras",
]
