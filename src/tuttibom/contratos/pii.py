"""Detecção mínima de dado pessoal para registro que vá ao repositório.

Não tenta adivinhar nome de pessoa (falso positivo em cidade e em
marca fictícia). O contrato também não tem campo de nome, telefone,
e-mail ou endereço: o que escapar em texto livre cai aqui.
"""

from __future__ import annotations

import re

_EMAIL = re.compile(r"(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b")
_CPF = re.compile(r"(?i)\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\bcpf\b\s*[:nº°]?\s*\d")
_FONE = re.compile(
    r"(?:(?:\+?55)\s*)?(?:\(?\d{2}\)?\s*)?(?:9\d{4}|\d{4})[-\s]\d{4}\b"
)
_FONE_DIGITO = re.compile(r"(?<!\d)(?:55)?\d{10,13}(?!\d)")
_WA = re.compile(r"(?i)\bwa\.me/\d{8,}\b")
_CEP = re.compile(r"\b\d{5}-\d{3}\b")
_RUA = re.compile(r"(?i)\b(?:rua|avenida|travessa|alameda|rodovia)\s+\S.{0,80}?\d")


def detectar_pii(texto: str) -> str | None:
    """Devolve o tipo encontrado, ou None."""
    if _EMAIL.search(texto):
        return "e-mail"
    if _CPF.search(texto):
        return "CPF"
    if _WA.search(texto) or _FONE.search(texto) or _FONE_DIGITO.search(texto):
        return "telefone"
    if _CEP.search(texto) or _RUA.search(texto):
        return "endereço"
    return None


def afirmar_sem_pii(texto: str, campo: str) -> None:
    tipo = detectar_pii(texto)
    if tipo:
        raise ValueError(f"dado pessoal ({tipo}) no campo {campo}")
