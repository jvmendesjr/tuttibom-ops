#!/usr/bin/env python3
"""ana-listener — ouvinte de webhook da Ana no Chatwoot (nova vertente, D-013).

Recebe o webhook de conta `message_created` do Chatwoot (conta 2),
deduplica por id da mensagem, enfileira as incoming em `listener.db`
(tabela `events`) e expõe a fila em GET /pending para o hook que acorda
o Muse. Detecta handoff via `handoff.py` (módulo do outro builder) e
nunca enfileira contatos ignorados (`ignorados.py`).

Somente stdlib, sem dependências. O ouvinte NUNCA envia mensagem ao
cliente: não existe função de envio aqui de propósito.

Regras de log: nunca logar texto de mensagem de cliente — só ids,
tamanhos e contagens.

Version: 0.1.0
"""

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "0.1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
HOST = os.environ.get("LISTENER_HOST", "0.0.0.0")
PORT = int(os.environ.get("LISTENER_PORT", "3021"))
DB_PATH = os.environ.get(
    "LISTENER_DB", os.path.join(HERE, "listener.db")
)

ESTADOS = ("pendente", "entregue", "ignorado")

log = logging.getLogger("ana-listener")
_DB_LOCK = threading.Lock()


# ---------------------------------------------------------------- db
def db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS events("
        "message_id INTEGER UNIQUE, conversation_id INTEGER,"
        " inbox_id INTEGER, contato_ref TEXT, handoff TEXT,"
        " recebido_em TEXT, estado TEXT DEFAULT 'pendente'"
        " CHECK (estado IN ('pendente','entregue','ignorado')))"
    )
    conn.commit()
    return conn


def registrar(message_id, conversation_id, inbox_id, contato_ref):
    """Reivindica o id (dedupe). Devolve True se novo, False se duplicado."""
    with _DB_LOCK:
        conn = db()
        try:
            conn.execute(
                "INSERT INTO events(message_id, conversation_id, inbox_id,"
                " contato_ref, recebido_em, estado)"
                " VALUES (?, ?, ?, ?, ?, 'pendente')",
                (message_id, conversation_id, inbox_id, contato_ref,
                 datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()


def atualizar(message_id, estado=None, handoff=None):
    with _DB_LOCK:
        conn = db()
        try:
            if estado is not None:
                conn.execute(
                    "UPDATE events SET estado=? WHERE message_id=?",
                    (estado, message_id),
                )
            if handoff is not None:
                conn.execute(
                    "UPDATE events SET handoff=? WHERE message_id=?",
                    (handoff, message_id),
                )
            conn.commit()
        finally:
            conn.close()


def listar_pendentes(limite=20):
    conn = db()
    try:
        rows = conn.execute(
            "SELECT message_id, conversation_id, inbox_id, contato_ref,"
            " handoff, recebido_em FROM events WHERE estado='pendente'"
            " ORDER BY message_id ASC LIMIT ?",
            (limite,),
        ).fetchall()
        campos = ("message_id", "conversation_id", "inbox_id",
                  "contato_ref", "handoff", "recebido_em")
        return [dict(zip(campos, row)) for row in rows]
    finally:
        conn.close()


def contagens():
    conn = db()
    try:
        rows = conn.execute(
            "SELECT estado, COUNT(*) FROM events GROUP BY estado"
        ).fetchall()
        out = {estado: 0 for estado in ESTADOS}
        for estado, total in rows:
            out[estado] = total
        out["total"] = sum(out[e] for e in ESTADOS)
        return out
    finally:
        conn.close()


def marcar_entregues(message_ids):
    """Marca como 'entregue' só quem está 'pendente'. Devolve quantos."""
    with _DB_LOCK:
        conn = db()
        try:
            marcados = 0
            for message_id in message_ids:
                cur = conn.execute(
                    "UPDATE events SET estado='entregue'"
                    " WHERE message_id=? AND estado='pendente'",
                    (message_id,),
                )
                marcados += cur.rowcount
            conn.commit()
            return marcados
        finally:
            conn.close()


# ---------------------------------------------------------------- parse
def dig(obj, *paths):
    """Primeiro valor não vazio entre vários caminhos 'a.b.c'."""
    for path in paths:
        cur = obj
        ok = True
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, ""):
            return cur
    return None


def _como_int(valor):
    try:
        return int(valor) if valor is not None else None
    except (TypeError, ValueError):
        return None


def extrair_mensagem(payload):
    """Normaliza os dois formatos de webhook do Chatwoot.

    Conta: campos aninhados em "message". Inbox: campos no topo.
    Devolve dict com message_id, conversation_id, inbox_id,
    message_type, content e sender — ou None se não houver mensagem
    com id.
    """
    if not isinstance(payload, dict):
        return None
    msg = payload.get("message")
    if not isinstance(msg, dict):
        msg = payload
    message_id = _como_int(msg.get("id") or payload.get("id"))
    if not message_id:
        return None
    conv = msg.get("conversation") or payload.get("conversation") or {}
    if not isinstance(conv, dict):
        conv = {}
    sender = msg.get("sender") or payload.get("sender") or {}
    if not isinstance(sender, dict):
        sender = {}
    content = msg.get("content")
    if not isinstance(content, str):
        content = ""
    return {
        "message_id": message_id,
        "conversation_id": _como_int(
            msg.get("conversation_id") or conv.get("id")),
        "inbox_id": _como_int(msg.get("inbox_id") or conv.get("inbox_id")),
        "message_type": msg.get("message_type"),
        "content": content,
        "sender": sender,
        "conversation": conv,
    }


def _contato_via_api(conversation_id):
    """Busca o remetente da conversa na API. Devolve dict ou None.

    Falha silenciosa: o enfileiramento não depende da API. O import
    do chatwoot_client é tardio de propósito — ele lê o PAT no import
    e o ouvinte funciona mesmo sem ele.
    """
    try:
        import chatwoot_client

        conv = chatwoot_client.obter_conversa(conversation_id)
    except Exception as exc:  # noqa: BLE001
        log.warning("lookup da conversa %s falhou: %s",
                    conversation_id, exc)
        return None
    if not isinstance(conv, dict):
        return None
    sender = (conv.get("meta") or {}).get("sender") or {}
    contato = conv.get("contact") or {}
    return {
        "telefone": dig(sender, "phone_number", "phone")
        or dig(contato, "phone_number", "phone"),
        "identifier": dig(sender, "identifier")
        or dig(contato, "identifier"),
        "nome": dig(sender, "name") or dig(contato, "name"),
        "contact_id": sender.get("id") or contato.get("id"),
    }


def identificar_contato(info):
    """Devolve (telefone, identifier, nome, contato_ref).

    Primeiro do payload; se faltar telefone e identifier, completa via
    API (obter_conversa). contato_ref é o telefone, senão o identifier,
    senão "contact:<id>", senão None.
    """
    sender = info["sender"]
    conv = info["conversation"]
    contato = conv.get("contact") or {}
    telefone = dig(sender, "phone_number", "phone") \
        or dig(contato, "phone_number", "phone")
    identifier = dig(sender, "identifier") or dig(contato, "identifier")
    nome = dig(sender, "name") or dig(contato, "name")
    contact_id = sender.get("id") or contato.get("id")
    if not telefone and not identifier and info["conversation_id"]:
        extra = _contato_via_api(info["conversation_id"])
        if extra:
            telefone = telefone or extra.get("telefone")
            identifier = identifier or extra.get("identifier")
            nome = nome or extra.get("nome")
            contact_id = contact_id or extra.get("contact_id")
    if telefone:
        contato_ref = str(telefone)
    elif identifier:
        contato_ref = str(identifier)
    elif contact_id:
        contato_ref = "contact:%s" % contact_id
    else:
        contato_ref = None
    return telefone, identifier, nome, contato_ref


# ---------------------------------------------------------------- handoff
_handoff = None
_handoff_tentado = False


def _carregar_handoff():
    """Importa handoff.py (módulo do outro builder), uma vez só.

    Sem ele — ou sem as duas funções da interface — o handoff fica
    desativado e as mensagens seguem enfileiradas como pendentes
    normais; o hook acorda o Muse do mesmo jeito.
    """
    global _handoff, _handoff_tentado
    if _handoff_tentado:
        return _handoff
    _handoff_tentado = True
    try:
        import handoff as modulo

        if callable(getattr(modulo, "detectar_handoff", None)) and \
                callable(getattr(modulo, "aplicar_handoff", None)):
            _handoff = modulo
        else:
            log.warning("handoff.py sem detectar_handoff/aplicar_handoff;"
                        " handoff desativado")
    except ImportError:
        log.warning("handoff.py nao encontrado; handoff desativado ate"
                    " o modulo existir")
    return _handoff


# ---------------------------------------------------------------- webhook
def handle_webhook(payload):
    """Processa um message_created. Devolve (ok, detalhe)."""
    event = payload.get("event") if isinstance(payload, dict) else None
    if event == "webhook.test":
        return True, "test"
    if event not in (None, "message_created"):
        return True, "evento-ignorado"
    info = extrair_mensagem(payload)
    if info is None:
        return False, "sem-mensagem"
    message_id = info["message_id"]
    mtype = info["message_type"]
    if mtype not in ("incoming", 0):
        log.info("webhook ignorado: message_type=%s (msg=%s)",
                 mtype, message_id)
        return True, "nao-incoming"
    telefone, identifier, nome, contato_ref = identificar_contato(info)
    # Dedupe ANTES de qualquer efeito (handoff só roda uma vez).
    if not registrar(message_id, info["conversation_id"],
                     info["inbox_id"], contato_ref):
        log.info("webhook duplicado ignorado (msg=%s)", message_id)
        return True, "duplicada"
    # Ignorados: empresas conhecidas — sem fila, sem handoff, sem acordar.
    try:
        import ignorados

        rotulo = ignorados.is_ignorado(
            telefone=telefone, identifier=identifier, nome=nome)
    except Exception as exc:  # noqa: BLE001
        log.warning("cheque de ignorados falhou (msg=%s): %s",
                    message_id, exc)
        rotulo = None
    if rotulo:
        atualizar(message_id, estado="ignorado")
        log.info("ignorado (%s): msg=%s conv=%s",
                 rotulo, message_id, info["conversation_id"])
        return True, "ignorado"
    # Handoff (se o módulo existir e detectar).
    texto = info["content"] or ""
    modulo = _carregar_handoff()
    if modulo is not None and texto:
        try:
            achado = modulo.detectar_handoff(texto)
        except Exception as exc:  # noqa: BLE001
            log.warning("detectar_handoff falhou (msg=%s): %s",
                        message_id, exc)
            achado = None
        if achado:
            motivo = achado.get("motivo") if isinstance(achado, dict) \
                else str(achado)
            try:
                resultado = modulo.aplicar_handoff(
                    info["conversation_id"], motivo)
            except Exception as exc:  # noqa: BLE001
                log.warning("aplicar_handoff falhou (msg=%s conv=%s): %s",
                            message_id, info["conversation_id"], exc)
                resultado = False
            # O aplicar devolve um dict {"ignorado", "aplicado", ...}
            # (o stub antigo devolvia bool) — interpretar os dois.
            if isinstance(resultado, dict):
                if resultado.get("ignorado"):
                    atualizar(message_id, estado="ignorado")
                    log.info("ignorado via handoff (%s): msg=%s conv=%s",
                             resultado.get("empresa"), message_id,
                             info["conversation_id"])
                    return True, "ignorado"
                aplicado = bool(resultado.get("aplicado"))
            else:
                aplicado = bool(resultado)
            if aplicado:
                atualizar(message_id, handoff=motivo)
                log.info("handoff aplicado: msg=%s conv=%s motivo=%s",
                         message_id, info["conversation_id"], motivo)
                return True, "handoff"
            log.warning("handoff nao aplicado (msg=%s conv=%s motivo=%s);"
                        " segue como pendente normal",
                        message_id, info["conversation_id"], motivo)
    log.info("enfileirado: msg=%s conv=%s inbox=%s chars=%d",
             message_id, info["conversation_id"], info["inbox_id"],
             len(texto))
    return True, "ok"


# ---------------------------------------------------------------- server
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"ok": True, "service": "ana-listener",
                             "version": VERSION})
        elif self.path == "/pending":
            self._send(200, {"pending": listar_pendentes()})
        elif self.path == "/stats":
            self._send(200, contagens())
        else:
            self._send(404, {"error": "not_found"})

    def do_POST(self):
        raw = self._read_body()
        if self.path == "/webhooks/chatwoot":
            self._webhook(raw)
        elif self.path == "/ack":
            self._ack(raw)
        else:
            self._send(404, {"error": "not_found"})

    def _webhook(self, raw):
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:  # noqa: BLE001
            self._send(400, {"error": "bad_json"})
            return
        if not isinstance(payload, dict):
            self._send(400, {"error": "bad_json"})
            return
        # 200 sempre aqui: o evento já foi deduplicado/registrado; uma
        # falha de processamento fica no log (um 5xx faria o Chatwoot
        # reentregar um evento que o dedupe descartaria).
        ok, detalhe = handle_webhook(payload)
        self._send(200, {"ok": ok, "detail": detalhe})

    def _ack(self, raw):
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:  # noqa: BLE001
            self._send(400, {"error": "bad_json"})
            return
        ids = []
        if isinstance(payload, dict):
            if payload.get("message_id") is not None:
                ids = [payload["message_id"]]
            elif isinstance(payload.get("message_ids"), list):
                ids = payload["message_ids"]
        limpos = []
        for mid in ids:
            try:
                limpos.append(int(mid))
            except (TypeError, ValueError):
                pass
        if not limpos:
            self._send(400, {"error": "no_message_id"})
            return
        marcados = marcar_entregues(limpos)
        self._send(200, {"ok": True, "marcados": marcados})

    def log_message(self, fmt, *args):  # silencia o log padrão
        pass


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    db()
    log.info("ana-listener %s subindo em %s:%d (db=%s)",
             VERSION, HOST, PORT, DB_PATH)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
