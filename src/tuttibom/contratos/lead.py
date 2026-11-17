"""Contrato Pydantic v2 para lead — TuttiBom F4.

Versão: 1.0.0
Data: 2026-11-17

Estágios do CRM local (`ops/triagem-interessados.md`):
Novo → Contatado → Qualificado → Proposta enviada →
Produção / Retirada → Fechado / Perdido / Adormecido.

Os nomes do funil Vendas no Deskcomm são outro vocabulário e não
entram aqui. Próxima ação e data de follow-up são obrigatórias em
todo estágio. Sem dado pessoal. Preço, se aparecer, só os da
captura Shopee 2026-10-30.
"""

from datetime import date
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from tuttibom.contratos.pii import afirmar_sem_pii
from tuttibom.contratos.precos import PRECOS_VALIDOS, interpretar_preco, validar_precos_de_catalogo


class EstagioLead(str, Enum):
    NOVO = "Novo"
    CONTATADO = "Contatado"
    QUALIFICADO = "Qualificado"
    PROPOSTA_ENVIADA = "Proposta enviada"
    PRODUCAO_RETIRADA = "Produção / Retirada"
    FECHADO = "Fechado"
    PERDIDO = "Perdido"
    ADORMECIDO = "Adormecido"


class Lead(BaseModel):
    """Ficha operacional. Não é cadastro de comprador."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: Literal["1.0.0"] = "1.0.0"

    referencia: str = Field(
        ...,
        min_length=2,
        max_length=40,
        pattern=r"^[A-Za-z][A-Za-z0-9._-]{1,39}$",
        description="Código operacional. Não é nome de pessoa.",
    )

    estagio: EstagioLead

    produto: str = Field(..., min_length=2, max_length=120)

    proxima_acao: str = Field(..., min_length=8, max_length=300)

    data_followup: date = Field(
        ...,
        description="Data de follow-up (ISO: AAAA-MM-DD).",
    )

    motivo_perda: Optional[str] = Field(default=None, max_length=200)

    valor_catalogo: Optional[str] = Field(
        default=None,
        description="Preço da captura, se houver. Fora da lista, falha.",
    )

    observacao: Optional[str] = Field(default=None, max_length=500)

    @field_validator("motivo_perda", "observacao")
    @classmethod
    def vazio_vira_nada(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None or not valor.strip():
            return None
        return valor.strip()

    @field_validator("valor_catalogo")
    @classmethod
    def so_preco_da_captura(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None or not valor.strip():
            return None
        try:
            dec = interpretar_preco(valor)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        if dec not in PRECOS_VALIDOS:
            raise ValueError("preço fora do catálogo Shopee 2026-10-30")
        return valor.strip()

    @model_validator(mode="after")
    def regras_da_ficha(self) -> "Lead":
        if self.estagio == EstagioLead.PERDIDO and not self.motivo_perda:
            raise ValueError("estágio Perdido exige motivo de perda")
        for campo in (
            "referencia",
            "produto",
            "proxima_acao",
            "motivo_perda",
            "observacao",
        ):
            valor = getattr(self, campo)
            if not isinstance(valor, str):
                continue
            afirmar_sem_pii(valor, campo)
            try:
                validar_precos_de_catalogo(valor)
            except ValueError as exc:
                raise ValueError(f"{exc} no campo {campo}") from exc
        return self
