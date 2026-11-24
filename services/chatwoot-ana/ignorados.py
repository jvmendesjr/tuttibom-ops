"""Lista de ignorados da Ana — empresas conhecidas, não clientes.

Regra do usuário (2026-11-21): contatos de empresas conhecidas
(Mercado Livre e outras) são canais de comunicação e alerta, NÃO
clientes. A Ana nunca responde, não cria lead, não faz follow-up nem
handoff para eles. O ouvinte de webhook, o runner de follow-up e o
handoff consultam esta lista; a vigília `chatwoot-watch-ana` tem a
mesma exceção (marca como vista e segue em silêncio).

Como acrescentar uma empresa: adicione o telefone (E.164) em
`por_telefone` e/ou o identifier do contato no Chatwoot (o uuid do
Deskcomm, que os contatos importados carregam) em `por_identifier`
no `ignorados.json` ao lado, e reinicie o `ana-listener`. Nunca
bloquear, apagar ou alterar esses contatos no Chatwoot.
"""

from __future__ import annotations

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
_ARQUIVO = os.environ.get(
    "IGNORADOS_FILE", os.path.join(HERE, "ignorados.json")
)


def _digitos(valor):
    return re.sub(r"\D", "", str(valor or ""))


def carregar():
    try:
        with open(_ARQUIVO, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"por_telefone": {}, "por_identifier": {}, "por_nome": []}


def is_ignorado(telefone=None, identifier=None, nome=None):
    """Devolve o rótulo da empresa (ex.: "Mercado Livre") ou None."""
    dados = carregar()
    if identifier:
        rotulo = (dados.get("por_identifier") or {}).get(str(identifier))
        if rotulo:
            return rotulo
    if telefone:
        dig = _digitos(telefone)
        for numero, rotulo in (dados.get("por_telefone") or {}).items():
            ref = _digitos(numero)
            if dig and ref and (dig.endswith(ref) or ref.endswith(dig)):
                return rotulo
    if nome:
        alvo = str(nome).strip().lower()
        for entrada in dados.get("por_nome") or []:
            if alvo and alvo == str(entrada).strip().lower():
                return entrada
    return None
