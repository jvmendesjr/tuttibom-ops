"""Contrato Pydantic v2 para publicação — TuttiBom F4.

Versão: 1.0.0
Data: 2026-11-17

Peça pública (Facebook ou Instagram). O texto do piloto aprovado em
2026-11-01 está em TEXTO_PILOTO; o contrato não trava a fila nele.
Legenda social não leva preço — nem valor inventado, nem valor do
catálogo. O catálogo fica no atendimento (contrato Lead).
"""

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from tuttibom.contratos.comum import Formato
from tuttibom.contratos.precos import contem_preco

TEXTO_PILOTO = (
    "Para deixar qualquer aniversário, casamento ou evento com a "
    "cara da sua marca: você prefere o brilho marcante do Dourado "
    "Metalizado ou a elegância clássica do Prata? Comenta aqui "
    "embaixo qual combina mais com a sua próxima festa no Cariri!"
)


class Rede(str, Enum):
    """Redes da peça pública. Marketplace fica fora deste contrato."""

    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class Publicacao(BaseModel):
    """Saída que pode seguir para publicação. O que falha aqui não publica."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: Literal["1.0.0"] = "1.0.0"

    texto_exato: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Texto exato da peça. Sem preço.",
    )

    texto_aprovado: Literal[True] = Field(
        ...,
        description="O usuário aprovou este texto exato.",
    )

    arte: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Identificador da arte aprovada. Não é caminho de aparelho.",
    )

    formato: Formato = Field(
        ...,
        description="9:16 ou 4:5.",
    )

    rede: Rede = Field(
        ...,
        description="facebook ou instagram.",
    )

    data: date = Field(
        ...,
        description="Data da peça (ISO: AAAA-MM-DD).",
    )

    rotulo_ia: Literal[True] = Field(
        ...,
        description="Rótulo de IA da plataforma ligado.",
    )

    foto_de_cliente: Literal[False] = Field(
        ...,
        description="A arte não usa foto de cliente.",
    )

    @field_validator("texto_exato", "arte")
    @classmethod
    def sem_preco(cls, valor: str) -> str:
        if contem_preco(valor):
            raise ValueError("peça pública não leva preço")
        return valor
