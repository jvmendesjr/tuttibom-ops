"""Peças compartilhadas dos contratos F4. Sem regra de negócio solta."""

from enum import Enum


class Formato(str, Enum):
    """Formatos de peça pública. Fora desta lista, o contrato recusa."""

    VERTICAL = "9:16"
    FEED = "4:5"
