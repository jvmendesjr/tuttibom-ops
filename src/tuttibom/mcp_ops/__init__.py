"""Núcleo local do MCP OPS; sem transporte, rede ou adaptadores reais."""

from .catalogo import AREAS, CATALOGO, Funcao, Risco
from .identidade import (
    FronteiraIdentidadeLaboratorio,
    RegistroIdentidade,
)
from .nucleo import (
    AdministradorOps,
    Autorizacao,
    ClienteConfigurado,
    Manifesto,
    ReciboAtivacao,
    ServidorOps,
    SessaoOps,
)

__all__ = [
    "AREAS",
    "CATALOGO",
    "AdministradorOps",
    "Autorizacao",
    "ClienteConfigurado",
    "FronteiraIdentidadeLaboratorio",
    "Funcao",
    "Manifesto",
    "ReciboAtivacao",
    "RegistroIdentidade",
    "Risco",
    "ServidorOps",
    "SessaoOps",
]
