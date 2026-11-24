"""Cliente mínimo da API do Chatwoot (conta 2) — só stdlib.

Uso pelos componentes da Ana no Chatwoot (ouvinte, follow-up, handoff).
Regras:
- O PAT fica guardado no caminho apontado por CHATWOOT_API_TOKEN_FILE (<CAMINHO_PRIVADO_PAT>, chmod 600);
  ele é lido dentro do processo, nunca impresso, nunca vai para log.
- Este cliente quase não envia mensagem ao cliente: a única função
  de envio é `enviar_cumprimento`, só para os textos fixos do
  cumprimento automático do ouvinte (nunca texto livre). O ouvinte e
  o runner nunca respondem; quem responde é o Muse, como Ana, pela
  API — fora deste módulo.
- Nunca logar texto de mensagem de cliente: só ids e contagens.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

CHATWOOT_URL = os.environ.get("CHATWOOT_URL", "http://127.0.0.1:3001").rstrip("/")
ACCOUNT_ID = os.environ.get("CHATWOOT_ACCOUNT_ID", "2")
PAT_FILE = os.environ.get("CHATWOOT_API_TOKEN_FILE", "")


def load_pat() -> str:
    if PAT_FILE and os.path.exists(PAT_FILE):
        with open(PAT_FILE, "r", encoding="utf-8") as fh:
            return fh.read().strip()
    return ""


PAT = load_pat()


def http_json(method, url, payload=None, headers=None, timeout=15):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:500]
        return exc.code, {"_error": body}
    except Exception as exc:  # noqa: BLE001
        return 0, {"_error": str(exc)}


def api(path, method="GET", payload=None, timeout=15):
    """Chamada à API da conta 2. Devolve (status, corpo)."""
    url = f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}{path}"
    return http_json(method, url, payload=payload,
                     headers={"api_access_token": PAT}, timeout=timeout)


def _payload_list(result):
    if isinstance(result, dict):
        payload = result.get("payload")
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, list):
                return data
    if isinstance(result, list):
        return result
    return []


# ------------------------------------------------------------ leitura
def listar_conversas_abertas(inbox_id=None):
    path = "/conversations?status=open"
    if inbox_id:
        path += f"&inbox_id={inbox_id}"
    status, result = api(path)
    if status != 200:
        return []
    return _payload_list(result.get("data") if isinstance(result, dict) else result)


def ler_mensagens(conversation_id):
    status, result = api(f"/conversations/{conversation_id}/messages")
    if status != 200:
        return []
    if isinstance(result, dict):
        return _payload_list(result)
    return []


def obter_conversa(conversation_id):
    status, result = api(f"/conversations/{conversation_id}")
    if status != 200:
        return None
    if isinstance(result, dict):
        return result.get("data") or result
    return None


def obter_contato(contact_id):
    status, result = api(f"/contacts/{contact_id}")
    if status != 200:
        return None
    if isinstance(result, dict):
        return result.get("payload") or result
    return None


def listar_etiquetas():
    status, result = api("/labels")
    if status != 200:
        return []
    if isinstance(result, dict):
        return _payload_list(result)
    return []


# --------------------------------------------------------- organização
def criar_etiqueta(title):
    """Cria a etiqueta da conta. Devolve True se criou ou já existia."""
    status, result = api("/labels", method="POST", payload={"title": title})
    if status in (200, 201):
        return True
    # 422 costuma ser "já existe" — confirmar listando.
    return any(
        (e.get("title") or e.get("name")) == title for e in listar_etiquetas()
    )


def etiquetar_conversa(conversation_id, labels):
    status, _ = api(
        f"/conversations/{conversation_id}/labels",
        method="POST",
        payload={"labels": list(labels)},
    )
    return status in (200, 201)


def atribuir_conversa(conversation_id, assignee_id):
    status, _ = api(
        f"/conversations/{conversation_id}/assignments",
        method="POST",
        payload={"assignee_id": assignee_id},
    )
    return status in (200, 201)


def desatribuir_conversa(conversation_id):
    status, _ = api(
        f"/conversations/{conversation_id}/assignments",
        method="POST",
        payload={"assignee_id": 0},
    )
    return status in (200, 201)


def resolver_conversa(conversation_id):
    status, _ = api(
        f"/conversations/{conversation_id}/toggle_status",
        method="POST",
        payload={"status": "resolved"},
    )
    return status in (200, 201)


def reabrir_conversa(conversation_id):
    status, _ = api(
        f"/conversations/{conversation_id}/toggle_status",
        method="POST",
        payload={"status": "open"},
    )
    return status in (200, 201)


# --------------------------------------------------------- cumprimento
def enviar_cumprimento(conversation_id, texto):
    """ÚNICO envio permitido neste serviço: o cumprimento automático.

    Só os textos fixos do cumprimento do ouvinte (`listener.py`) —
    nunca texto livre, nunca resposta. O cumprimento é uma mensagem
    outgoing normal (não privada) e chega ao contato pelo canal.
    Devolve True se o Chatwoot aceitou (200/201).
    """
    status, _ = api(
        f"/conversations/{conversation_id}/messages",
        method="POST",
        payload={"content": texto, "message_type": "outgoing"},
    )
    return status in (200, 201)


def adicionar_nota(conversation_id, content):
    """Nota privada na conversa (só agentes veem).

    Verificado 2026-11-21 no Chatwoot 4.20.1-ce: o endpoint
    ``POST /conversations/:id/notes`` NÃO existe (404). A nota
    privada é criada pelo endpoint de mensagens, com
    ``private: true`` — a mensagem fica marcada como privada e
    não é enviada ao contato. Nunca usar ``private: false`` aqui.
    """
    status, _ = api(
        f"/conversations/{conversation_id}/messages",
        method="POST",
        payload={
            "content": content,
            "message_type": "outgoing",
            "private": True,
        },
    )
    return status in (200, 201)
