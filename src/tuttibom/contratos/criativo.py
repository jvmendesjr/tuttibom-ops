"""Contrato Pydantic v2 para criativo — TuttiBom F4.

Versão: 1.0.0
Data: 2026-11-17

Arte da peça: formato, textos curtos legíveis, zonas seguras e os
dois botões A/B. A legenda longa é Publicacao.texto_exato, não um
overlay.

Zona 9:16 (frame 1080×1920), piso já adotado no projeto: topo 220 px,
base 380 px, direita 140 px. Os 56 px da esquerda estão no mapa de
motion e ainda não são trava deste contrato. O 4:5 não tem piso em
px no storyboard do piloto — o contrato exige margem declarada e
texto fora da zona morta, sem inventar o número.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from tuttibom.contratos.comum import Formato
from tuttibom.contratos.precos import contem_preco

MINIMO_9_16 = {"topo_px": 220, "base_px": 380, "direita_px": 140}


class TextoCriativo(BaseModel):
    """Uma linha de overlay. Curta o bastante para ler no celular."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    conteudo: str = Field(..., min_length=1, max_length=120)
    legivel: Literal[True]

    @field_validator("conteudo")
    @classmethod
    def sem_preco(cls, valor: str) -> str:
        if contem_preco(valor):
            raise ValueError("texto do criativo não leva preço")
        return valor


class ZonasSeguras(BaseModel):
    """Margens livres de texto, em px, e a declaração de que o texto não invade."""

    model_config = ConfigDict(extra="forbid")

    topo_px: int = Field(..., ge=0)
    base_px: int = Field(..., ge=0)
    direita_px: int = Field(..., ge=0)
    texto_na_zona_morta: Literal[False]


class Botao(BaseModel):
    """Rótulo de um lado da escolha A/B."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    rotulo: str = Field(..., min_length=2, max_length=40)
    legivel: Literal[True]

    @field_validator("rotulo")
    @classmethod
    def sem_preco(cls, valor: str) -> str:
        if contem_preco(valor):
            raise ValueError("botão não leva preço")
        return valor


class Criativo(BaseModel):
    """Saída de criativo antes de virar peça publicada."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = "1.0.0"

    formato: Formato

    textos: list[TextoCriativo] = Field(..., min_length=1, max_length=6)

    zonas_seguras: ZonasSeguras

    botao_a: Botao

    botao_b: Botao

    @model_validator(mode="after")
    def conferir_zonas_e_botoes(self) -> "Criativo":
        zonas = self.zonas_seguras
        if self.formato == Formato.VERTICAL:
            faltas = [
                f"{nome} {piso} px"
                for nome, piso in MINIMO_9_16.items()
                if getattr(zonas, nome) < piso
            ]
            if faltas:
                raise ValueError(
                    "9:16 exige zona segura mínima ("
                    + ", ".join(faltas)
                    + ")"
                )
        elif min(zonas.topo_px, zonas.base_px, zonas.direita_px) < 1:
            raise ValueError(
                "4:5 exige margens declaradas; o piso em px desse formato ainda não está documentado"
            )
        if zonas.texto_na_zona_morta:
            raise ValueError("texto não pode ficar na zona morta")
        if self.botao_a.rotulo.casefold() == self.botao_b.rotulo.casefold():
            raise ValueError("botões A e B precisam de rótulos diferentes")
        return self
