"""Serialização canônica e sanitização restritiva da auditoria."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

_REDACT = ("token", "secret", "segredo", "senha", "password", "authorization",
           "cookie", "api_key", "apikey", "credential", "credencial")
_OMIT = ("mensagem", "message", "texto", "text", "body", "conteudo", "content",
         "resumo", "nome", "email", "telefone", "phone", "cpf", "cnpj",
         "endereco", "address", "contato", "contact", "comprador", "customer")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ID_FUNCAO = re.compile(r"^[0-9]{2}\.[0-9]{2}$")
_ID_AREA = re.compile(r"^0[1-8]$")
_SKU = re.compile(r"^(?:FITA|SKU)-[A-Z0-9-]{1,60}$")
_VALORES = {
    "direcao": {"inbound", "outbound"},
    "etapa": {
        "Novo contato", "Já respondi", "Escolhendo o produto", "Vai levar",
        "Aguardando pagamento", "Pedido pago", "Não comprou",
    },
    "status": {"pendente", "ativo", "inativo", "revogado", "ok", "erro"},
}
_CHAVES_NUMERO = {"limite", "offset", "total", "resumo_tamanho", "quantidade"}
_CHAVES_BOOL = {"ok", "confirmado", "escrita", "lease_sem_prazo"}


def json_canonico(valor: Any) -> str:
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_texto(valor: str) -> str:
    return hashlib.sha256(valor.encode("utf-8")).hexdigest()


def _chave_normalizada(chave: str) -> str:
    return chave.strip().lower().replace("-", "_")


def sanitizar(valor: Any, *, _profundidade: int = 0) -> Any:
    """Mantém só metadados tipados; todo texto desconhecido é omitido.

    A política é default-deny para não transformar um argumento novo em vazamento
    futuro. Em particular, resumos do handshake nunca são persistidos em claro.
    """
    if _profundidade > 4:
        return "[profundidade_omitida]"
    if valor is None or isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return "[texto_omitido]"
    if isinstance(valor, dict):
        saida: dict[str, Any] = {}
        for bruta, item in valor.items():
            if not isinstance(bruta, str) or len(bruta) > 64:
                continue
            chave = _chave_normalizada(bruta)
            if any(parte in chave for parte in _REDACT):
                saida[chave] = "[redigido]"
            elif (
                any(parte in chave for parte in _OMIT)
                and chave not in {"resumo_sha256", "resumo_tamanho"}
            ):
                saida[chave] = "[omitido]"
            elif chave in _CHAVES_NUMERO and isinstance(item, (int, float)):
                saida[chave] = item
            elif chave in _CHAVES_BOOL and isinstance(item, bool):
                saida[chave] = item
            elif chave in {"hash_manifesto", "resumo_sha256"} and isinstance(item, str):
                saida[chave] = item if _HEX64.fullmatch(item) else "[hash_invalido]"
            elif chave == "referencia" and isinstance(item, str):
                saida["referencia_sha256"] = sha256_texto(item)
            elif chave == "funcao_id" and isinstance(item, str):
                saida[chave] = item if _ID_FUNCAO.fullmatch(item) else "[valor_omitido]"
            elif chave == "area" and isinstance(item, str):
                saida[chave] = item if _ID_AREA.fullmatch(item) else "[valor_omitido]"
            elif chave == "sku" and isinstance(item, str):
                saida[chave] = item if _SKU.fullmatch(item) else "[valor_omitido]"
            elif chave == "funcoes" and isinstance(item, (list, tuple)):
                saida[chave] = [
                    id if isinstance(id, str) and _ID_FUNCAO.fullmatch(id)
                    else "[valor_omitido]"
                    for id in item[:50]
                ]
            elif chave == "areas" and isinstance(item, (list, tuple)):
                saida[chave] = [
                    area if isinstance(area, str) and _ID_AREA.fullmatch(area)
                    else "[valor_omitido]"
                    for area in item[:50]
                ]
            elif chave in _VALORES and isinstance(item, str) and item in _VALORES[chave]:
                saida[chave] = item
            elif isinstance(item, (dict, list, tuple)):
                saida[chave] = sanitizar(item, _profundidade=_profundidade + 1)
            else:
                saida[chave] = "[omitido]"
        return saida
    if isinstance(valor, (list, tuple)):
        return [sanitizar(item, _profundidade=_profundidade + 1) for item in valor[:50]]
    return f"[tipo_{type(valor).__name__}]"
