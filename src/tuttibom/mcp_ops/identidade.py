"""Fronteira de identidade verificada pelo servidor.

A ativação não recebe ``agente_id`` nem ``identidade`` do agente. Ela usa o
cliente previamente configurado e consulta novamente a fronteira do servidor.
A implementação de laboratório abaixo representa um registro já autenticado;
não é um verificador de produção nem aceita claims livres em cada pedido.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Protocol

from .erros import ErroValidacao, NaoAutenticado

_IDENTIFICADOR = re.compile(r"^[a-z][a-z0-9._-]{1,63}$")


def validar_identificador(valor: str, campo: str) -> str:
    if not isinstance(valor, str) or not _IDENTIFICADOR.fullmatch(valor):
        raise ErroValidacao(f"identificador_invalido:{campo}")
    return valor


@dataclass(frozen=True, slots=True)
class RegistroIdentidade:
    """Entrada fictícia de uma identidade já autenticada no laboratório."""

    sujeito: str
    administrador: bool = False

    def __post_init__(self) -> None:
        validar_identificador(self.sujeito, "sujeito")


class IdentidadeVerificada:
    """Capability emitida pela fronteira; o selo não aparece no repr."""

    __slots__ = ("_sujeito", "_administrador", "_fronteira")

    def __init__(
        self,
        sujeito: str,
        administrador: bool,
        fronteira: object,
    ) -> None:
        self._sujeito = validar_identificador(sujeito, "sujeito")
        self._administrador = bool(administrador)
        self._fronteira = fronteira

    @property
    def sujeito(self) -> str:
        return self._sujeito

    @property
    def administrador(self) -> bool:
        return self._administrador

    def __repr__(self) -> str:
        return f"IdentidadeVerificada(sujeito={self._sujeito!r})"


class FronteiraIdentidade(Protocol):
    def verificar(self, cliente_id: str) -> IdentidadeVerificada:
        """Resolve uma configuração autenticada, nunca um claim do pedido."""
        ...


class FronteiraIdentidadeLaboratorio:
    """Registro confiável injetado nos testes, sem rede ou credenciais reais."""

    def __init__(self, registros: Mapping[str, RegistroIdentidade]) -> None:
        self._registros = dict(registros)
        for cliente_id in self._registros:
            validar_identificador(cliente_id, "cliente_id")

    def verificar(self, cliente_id: str) -> IdentidadeVerificada:
        validar_identificador(cliente_id, "cliente_id")
        try:
            registro = self._registros[cliente_id]
        except KeyError as exc:
            raise NaoAutenticado() from exc
        return IdentidadeVerificada(
            registro.sujeito,
            registro.administrador,
            self,
        )
