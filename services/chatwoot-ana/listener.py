#!/usr/bin/env python3
"""ana-listener — ouvinte de webhook da Ana no Chatwoot (nova vertente, D-013).

Recebe o webhook de conta `message_created` do Chatwoot (conta 2),
deduplica por id da mensagem, enfileira as incoming em `listener.db`
(tabela `events`) e expõe a fila em GET /pending para o hook que acorda
o Muse. Detecta handoff via `handoff.py` (módulo do outro builder) e
nunca enfileira contatos ignorados (`ignorados.py`).

Cumprimento automático (única exceção ao "nunca enviar"): na abertura
da conversa o ouvinte agenda para 10 s depois um cumprimento fixo
(saudação pelo horário + pedido cordial de espera), antes da resposta
da Ana. O atraso de 10 s dá tempo de a pessoa terminar a rajada e
parece humano; o timer é FIXO a partir da primeira mensagem (não
deslizante). Aos 10 s o ouvinte reavalia: lê as mensagens recentes e
classifica a rajada INTEIRA da janela (basta um pedido na janela para
usar o pool com "verificar"); suprime se houve qualquer mensagem
real (incoming ou outgoing) nas 2h antes do início da rajada — é a
pausa de 2h (decisão do usuário 2026-11-22): depois que o
cumprimento dispara a primeira vez, ele só dispara de novo numa
abertura nova (primeira mensagem da conversa ou última atividade há
mais de 2h). Sem a API, só envia se a conversa nunca recebeu
cumprimento (estado local — não dá para provar 2h de silêncio sem
ela). Se outro cumprimento foi enviado há menos de 10 min, suprime.
Textos fixos, dois pools (saudação fechada sem "verificar", com
pedido com "verificar"), rotação sem repetir a variante. O
cumprimento é registrado em `listener.db` (tabela `cumprimentos`) e
aparece no item do GET /pending, para o agente saber que ele foi
enviado e como o cliente reagiu.

Trava geral (decisão do usuário 2026-11-22): em grupo de WhatsApp
o cumprimento NUNCA dispara — identifier ou contato_ref terminando
em `@g.us` pula o agendamento antes do timer. Cliente da loja é
sempre conversa individual; a lista de ignorados continua como
segunda camada (o enfileiramento da mensagem segue normal).

Somente stdlib, sem dependências.

Regras de log: nunca logar texto de mensagem de cliente — só ids,
tamanhos e contagens.

Version: 0.5.0
"""

import json
import logging
import os
import re
import sqlite3
import threading
import unicodedata
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from zoneinfo import ZoneInfo

VERSION = "0.5.0"
HERE = os.path.dirname(os.path.abspath(__file__))
HOST = os.environ.get("LISTENER_HOST", "0.0.0.0")
PORT = int(os.environ.get("LISTENER_PORT", "3021"))
DB_PATH = os.environ.get(
    "LISTENER_DB", os.path.join(HERE, "listener.db")
)

ESTADOS = ("pendente", "entregue", "ignorado")

# ------------------------------------------------------- cumprimento
# Atraso do cumprimento (segundos) — fixo a partir da primeira
# mensagem da abertura. 10 s: tempo de a pessoa terminar a rajada e
# rápido o bastante para o cumprimento cumprir seu papel.
CUMPRIMENTO_ATRASO_SEG = 10
# Janelas do cumprimento automático (minutos).
CUMPRIMENTO_PAUSA_MIN = 120  # sem atividade real na conversa: é abertura
CUMPRIMENTO_JANELA_MIN = 10  # sem outro cumprimento na conversa
FUSO_FORTALEZA = "America/Fortaleza"

# Timer fixo do cumprimento (10 s a partir da primeira mensagem da
# abertura). Um timer por conversa; reinício do serviço descarta os
# timers pendentes (a mensagem segue enfileirada para o Muse).
_TIMERS = {}
_TIMERS_LOCK = threading.Lock()

# "{S}" vira a saudação pelo horário. Dois pools (correção do usuário
# 2026-11-21): "verificar" só cabe quando a pessoa já pediu alguma
# informação; quem entra só com um "bom dia" não ouve falar em verificar.
POOL_SAUDACAO = (
    "{S}! Só um instante que já te atendo.",
    "{S}! Ok, só um instante.",
    "{S}! Já te atendo.",
)
POOL_PEDIDO = (
    "{S}! Vou verificar aqui e já te respondo.",
    "{S}! Só um instante que já te respondo.",
    "{S}! Ok, vou verificar e já te chamo.",
)
# Palavras permitidas numa saudação fechada (já sem acento, minúsculas).
PALAVRAS_SAUDACAO = frozenset((
    "oi", "ola", "bom", "dia", "tarde", "noite", "boa", "hey", "hello",
    "eai", "tudo", "bem", "beleza", "como", "vai",
))

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
    conn.execute(
        "CREATE TABLE IF NOT EXISTS cumprimentos("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " conversation_id INTEGER, message_id INTEGER UNIQUE,"
        " texto TEXT, variante INTEGER, enviado_em TEXT)"
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
        itens = []
        for row in rows:
            item = dict(zip(campos, row))
            item["cumprimento"] = cumprimento_de(item["message_id"])
            itens.append(item)
        return itens
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
        out["cumprimentos"] = conn.execute(
            "SELECT COUNT(*) FROM cumprimentos").fetchone()[0]
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


# ------------------------------------------------------- cumprimento
def _fuso_fortaleza():
    try:
        return ZoneInfo(FUSO_FORTALEZA)
    except Exception:  # noqa: BLE001 — sem tzdata, UTC-3 fixo
        return timezone(timedelta(hours=-3))


def _agora_fortaleza():
    return datetime.now(_fuso_fortaleza())


def saudacao_por_horario(agora=None):
    """Bom dia (06–12), Boa tarde (12–18), Boa noite (18–06)."""
    hora = (agora or _agora_fortaleza()).hour
    if 6 <= hora < 12:
        return "Bom dia"
    if 12 <= hora < 18:
        return "Boa tarde"
    return "Boa noite"


def _normalizar(texto):
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto or "")
        if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", sem_acento.lower())


def eh_saudacao_fechada(texto):
    """Só saudação, sem pedido: todas as palavras no conjunto.

    "Olá tudo bom" é saudação; "oi, quanto custa" e "Boa noite,
    queria saber o preço" são pedido.
    """
    palavras = _normalizar(texto).split()
    return bool(palavras) and all(p in PALAVRAS_SAUDACAO for p in palavras)


def texto_cumprimento(tipo, variante, agora=None):
    """Texto fixo do cumprimento. tipo: 'saudacao' ou 'pedido'."""
    pool = POOL_SAUDACAO if tipo == "saudacao" else POOL_PEDIDO
    return pool[variante % len(pool)].replace(
        "{S}", saudacao_por_horario(agora))


def ultimo_cumprimento(conversation_id):
    conn = db()
    try:
        row = conn.execute(
            "SELECT conversation_id, message_id, texto, variante,"
            " enviado_em FROM cumprimentos WHERE conversation_id=?"
            " ORDER BY id DESC LIMIT 1",
            (conversation_id,)).fetchone()
        if row is None:
            return None
        return dict(zip(("conversation_id", "message_id", "texto",
                         "variante", "enviado_em"), row))
    finally:
        conn.close()


def cumprimento_de(message_id):
    """Cumprimento enviado para esta incoming, ou None."""
    conn = db()
    try:
        row = conn.execute(
            "SELECT texto, enviado_em FROM cumprimentos"
            " WHERE message_id=?",
            (message_id,)).fetchone()
        return {"texto": row[0], "enviado_em": row[1]} if row else None
    finally:
        conn.close()


def registrar_cumprimento(conversation_id, message_id, texto, variante,
                          enviado_em=None):
    enviado_em = enviado_em or datetime.now(timezone.utc).isoformat()
    with _DB_LOCK:
        conn = db()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO cumprimentos(conversation_id,"
                " message_id, texto, variante, enviado_em)"
                " VALUES (?, ?, ?, ?, ?)",
                (conversation_id, message_id, texto, variante,
                 enviado_em))
            conn.commit()
        finally:
            conn.close()
    return {"texto": texto, "enviado_em": enviado_em}


def _parse_iso(valor):
    try:
        return datetime.fromisoformat(str(valor))
    except (TypeError, ValueError):
        return None


def _mensagens_da_conversa(conversation_id):
    """GET /conversations/{id}/messages. Devolve (ok, mensagens).

    ok=False quando a API falha — o chamador decide só pelo estado
    local nesse caso. Import tardio: o ouvinte funciona sem o PAT.
    """
    try:
        import chatwoot_client

        status, result = chatwoot_client.api(
            f"/conversations/{conversation_id}/messages")
    except Exception as exc:  # noqa: BLE001
        log.warning("leitura de mensagens falhou (conv=%s): %s",
                    conversation_id, exc)
        return False, []
    if status != 200:
        return False, []
    if isinstance(result, dict):
        for chave in ("payload", "data"):
            lista = result.get(chave)
            if isinstance(lista, list):
                return True, lista
    return True, []


def _quando_mensagem(msg):
    """created_at (epoch ou ISO) -> datetime UTC, ou None."""
    criado = msg.get("created_at") if isinstance(msg, dict) else None
    quando = None
    if isinstance(criado, (int, float)):
        quando = datetime.fromtimestamp(criado, tz=timezone.utc)
    elif isinstance(criado, str):
        quando = _parse_iso(criado)
        if quando is not None and quando.tzinfo is None:
            quando = quando.replace(tzinfo=timezone.utc)
    return quando


def _tem_atividade_recente(mensagens, janela_inicio, minutos):
    """True se há mensagem real (incoming 0 ou outgoing 1) com
    created_at em [janela_inicio - minutos, janela_inicio).

    Activity (tipo 2) e notas de sistema não contam. A janela
    termina no início da rajada (exclusivo): as mensagens da
    própria rajada não contam como atividade anterior. É a pausa
    de 2h (decisão do usuário 2026-11-22): depois que o
    cumprimento dispara, ele só dispara de novo numa abertura
    nova — primeira mensagem da conversa ou última atividade há
    mais de 2h. Sem início da rajada, não dá para provar
    atividade: devolve False.
    """
    if janela_inicio is None:
        return False
    inicio = janela_inicio - timedelta(minutes=minutos)
    for msg in mensagens:
        if not isinstance(msg, dict):
            continue
        if msg.get("message_type") not in (0, 1, "incoming", "outgoing"):
            continue
        quando = _quando_mensagem(msg)
        if quando is not None and inicio <= quando < janela_inicio:
            return True
    return False


def _classificar_rajada(mensagens, texto_inicial, janela_inicio):
    """Pool pela rajada INTEIRA da janela (refinamento 2026-11-21).

    Só usa o pool SEM "verificar" se TODAS as incoming da janela
    forem saudação fechada; basta UM pedido na janela para usar o
    pool COM "verificar". texto_inicial (a mensagem que disparou o
    timer) sempre entra, porque a API pode ainda não listá-la.
    """
    textos = []
    if texto_inicial:
        textos.append(texto_inicial)
    for msg in mensagens:
        if not isinstance(msg, dict):
            continue
        if msg.get("message_type") not in (0, "incoming"):
            continue
        quando = _quando_mensagem(msg)
        if quando is not None and janela_inicio is not None \
                and quando < janela_inicio:
            continue
        conteudo = msg.get("content")
        if isinstance(conteudo, str) and conteudo:
            textos.append(conteudo)
    if textos and all(eh_saudacao_fechada(t) for t in textos):
        return "saudacao"
    return "pedido"


def _janela_inicio(info):
    """Início da janela da rajada: created_at da mensagem que disparou
    o timer, menos 2 s de tolerância; sem ele, o agendamento."""
    quando = _quando_mensagem(info)
    if quando is None:
        quando = _parse_iso(info.get("_agendado_em"))
        if quando is not None and quando.tzinfo is None:
            quando = quando.replace(tzinfo=timezone.utc)
    if quando is None:
        return None
    return quando - timedelta(seconds=2)


def _enviar_cumprimento_api(conversation_id, texto):
    """Envio via chatwoot_client. False em qualquer falha."""
    try:
        import chatwoot_client

        return bool(chatwoot_client.enviar_cumprimento(
            conversation_id, texto))
    except Exception as exc:  # noqa: BLE001
        log.warning("envio do cumprimento falhou (conv=%s): %s",
                    conversation_id, exc)
        return False


def eh_grupo_whatsapp(identifier=None, contato_ref=None):
    """Grupo de WhatsApp: identifier ou contato_ref termina em @g.us.

    Trava geral (decisão do usuário 2026-11-22): o cumprimento nunca
    dispara em grupo — cliente da loja é sempre conversa individual.
    A lista de ignorados continua como segunda camada; o
    enfileiramento da mensagem não muda.
    """
    for valor in (identifier, contato_ref):
        if valor and str(valor).strip().lower().endswith("@g.us"):
            return True
    return False


def agendar_cumprimento(info, atraso=None):
    """Agenda o cumprimento 10 s depois da primeira mensagem da abertura.

    Timer FIXO (não deslizante): se já há um timer para a conversa,
    não agenda outro. Só o estado local é consultado aqui (nenhum
    cumprimento nos últimos 10 min); a reavaliação (atividade
    recente na conversa, rajada) acontece no disparo. Devolve True
    se agendou. Nunca levanta exceção.
    """
    conversation_id = info.get("conversation_id")
    if not conversation_id:
        return False
    try:
        ultimo = ultimo_cumprimento(conversation_id)
        if ultimo:
            enviado = _parse_iso(ultimo.get("enviado_em"))
            if enviado is not None and enviado.tzinfo is None:
                enviado = enviado.replace(tzinfo=timezone.utc)
            if enviado is not None and \
                    (datetime.now(timezone.utc) - enviado) < timedelta(
                        minutes=CUMPRIMENTO_JANELA_MIN):
                return False
    except Exception as exc:  # noqa: BLE001
        log.warning("agendar_cumprimento falhou (conv=%s): %s",
                    conversation_id, exc)
        return False
    with _TIMERS_LOCK:
        if conversation_id in _TIMERS:
            return False
        atraso_seg = CUMPRIMENTO_ATRASO_SEG if atraso is None else atraso
        dados = dict(info)
        dados["_agendado_em"] = datetime.now(timezone.utc).isoformat()
        timer = threading.Timer(atraso_seg, _disparar_cumprimento,
                                args=(dados,))
        timer.daemon = True
        _TIMERS[conversation_id] = timer
        timer.start()
        return True


def _disparar_cumprimento(info):
    """Callback do timer (10 s depois). Reavalia e envia ou suprime.

    Suprime se outro cumprimento foi enviado (<10 min) ou se houve
    atividade real na conversa nas 2h antes do início da rajada
    (pausa de 2h: só dispara numa abertura nova). Sem a API, só
    envia se a conversa nunca recebeu cumprimento (estado local).
    Classifica a rajada inteira da janela. Nunca levanta exceção;
    falha de envio só loga.
    """
    conversation_id = info.get("conversation_id")
    try:
        with _TIMERS_LOCK:
            _TIMERS.pop(conversation_id, None)
        agora = datetime.now(timezone.utc)
        ultimo = ultimo_cumprimento(conversation_id)
        if ultimo:
            enviado = _parse_iso(ultimo.get("enviado_em"))
            if enviado is not None and enviado.tzinfo is None:
                enviado = enviado.replace(tzinfo=timezone.utc)
            if enviado is not None and \
                    (agora - enviado) < timedelta(
                        minutes=CUMPRIMENTO_JANELA_MIN):
                log.info("cumprimento suprimido (outro recente): conv=%s",
                         conversation_id)
                return None
        ok, mensagens = _mensagens_da_conversa(conversation_id)
        janela = _janela_inicio(info)
        if ok:
            if _tem_atividade_recente(
                    mensagens, janela, CUMPRIMENTO_PAUSA_MIN):
                log.info("cumprimento suprimido (atividade recente,"
                         " pausa de 2h): conv=%s", conversation_id)
                return None
            tipo = _classificar_rajada(
                mensagens, info.get("content") or "", janela)
        else:
            # Sem a API não dá para provar 2h de silêncio: só envia
            # se esta conversa nunca recebeu cumprimento (estado
            # local); se já houve cumprimento, suprime.
            if ultimo is not None:
                log.info("cumprimento suprimido (sem API e ja"
                         " cumprimentado): conv=%s", conversation_id)
                return None
            tipo = "saudacao" if eh_saudacao_fechada(
                info.get("content") or "") else "pedido"
        variante = (ultimo["variante"] + 1) % 3 if ultimo else 0
        texto = texto_cumprimento(tipo, variante)
        if not _enviar_cumprimento_api(conversation_id, texto):
            log.warning("cumprimento nao enviado (conv=%s msg=%s)",
                        conversation_id, info.get("message_id"))
            return None
        enviado_em = datetime.now(timezone.utc).isoformat()
        registrar_cumprimento(conversation_id, info.get("message_id"),
                              texto, variante, enviado_em)
        log.info("cumprimento enviado: conv=%s msg=%s variante=%d"
                 " tipo=%s", conversation_id, info.get("message_id"),
                 variante, tipo)
        return {"texto": texto, "enviado_em": enviado_em}
    except Exception as exc:  # noqa: BLE001
        log.warning("disparo do cumprimento falhou (conv=%s): %s",
                    conversation_id, exc)
        return None


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
        "created_at": msg.get("created_at") or payload.get("created_at"),
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
    # Trava geral (decisão do usuário 2026-11-22): o cumprimento
    # nunca dispara em grupo de WhatsApp — o agendamento é pulado
    # ANTES do timer. O enfileiramento segue normal: a mensagem
    # chega ao Muse, que decide; a lista de ignorados continua
    # como segunda camada. Dispara mesmo quando há handoff (a
    # pessoa espera um humano; "só um instante" continua adequado).
    # Nunca bloqueia o enfileiramento: falha só loga.
    if eh_grupo_whatsapp(identifier, contato_ref):
        log.info("cumprimento suprimido (grupo de WhatsApp): conv=%s",
                 info["conversation_id"])
    else:
        agendar_cumprimento(info)
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
