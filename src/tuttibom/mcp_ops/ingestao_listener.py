"""Listener de ingestão: sincroniza /pending do ana-listener com a fila local.

NUNCA grava, loga ou repassa contato_ref, telefone, nome ou texto.
O módulo não abre porta; consome de um listener HTTP pré-existente.

Protocolo escopado (protocolo_escopado=True)
--------------------------------------------
Quando habilitado, o listener usa o endpoint filtrado por inbox:

    GET /pending?inbox_id=<inbox_id>&after_message_id=<cursor>&limit=<n>

e ACK escopado por inbox:

    POST /ack  {"inbox_id": <inbox_id>, "message_ids": [...]}

com verificação granular da resposta (quais IDs foram aceitos vs
rejeitados). Se o listener não suportar esses parâmetros (responder
com `"scoped": false` ou sem a flag), `sincronizar` retorna
`{"ok": False, "codigo": "listener_legado_incompativel"}` — falha
fechada.

Protocolo legado (protocolo_escopado=False, default)
----------------------------------------------------
Mantém o comportamento original: `GET /pending` sem query, `POST /ack`
sem inbox_id, filtragem de inbox em memória.
"""

from __future__ import annotations

import http.client
import json
import logging
import re
import sqlite3
import threading
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from pathlib import Path
from urllib.parse import urlencode

from tuttibom.contratos.pii import detectar_pii
from tuttibom.mcp_ops.fila_persistente import FilaPersistente

log = logging.getLogger("tuttibom.mcp_ops.ingestao_listener")

_ID_CONTA = re.compile(r"^[1-9][0-9]{0,8}$")
_MID = re.compile(r"^[1-9][0-9]{0,17}$")
_CID = re.compile(r"^[1-9][0-9]{0,8}$")
_HANDOFF = re.compile(r"^[a-zA-Z0-9_-]{1,48}$")
_GRUPO_WA = re.compile(r"@g\.us$", re.IGNORECASE)

_SCHEMA_AUX = """\
CREATE TABLE IF NOT EXISTS metadados_evento_v1 (
    inbox_ref TEXT NOT NULL,
    message_id TEXT NOT NULL,
    handoff TEXT,
    PRIMARY KEY (inbox_ref, message_id)
);
CREATE TABLE IF NOT EXISTS acks_listener_pendentes_v1 (
    inbox_ref TEXT NOT NULL,
    message_id TEXT NOT NULL,
    PRIMARY KEY (inbox_ref, message_id)
);
"""

# Limite padrão e máximo para paginação keyset no protocolo escopado.
_PAGINA_LIMITE_PADRAO = 50
_PAGINA_LIMITE_MAXIMO = 200


def _sanitizar_handoff(valor: object) -> str | None:
    if not isinstance(valor, str):
        return None
    if not _HANDOFF.fullmatch(valor):
        return None
    if detectar_pii(valor) is not None:
        return None
    return valor


def _transporte_http(
    host: str, porta: int, timeout: int
) -> Callable[[str, str, bytes | None], tuple[int, bytes]]:
    def chamar(metodo: str, caminho: str, corpo: bytes | None) -> tuple[int, bytes]:
        conn = http.client.HTTPConnection(host, porta, timeout=timeout)
        try:
            headers: dict[str, str] = {}
            if corpo is not None:
                headers["Content-Type"] = "application/json"
            conn.request(metodo, caminho, body=corpo, headers=headers)
            resp = conn.getresponse()
            return resp.status, resp.read()
        finally:
            conn.close()
    return chamar


class FilaIngestaoListener:
    """Implementa FilaPendencias consumindo o ana-listener via HTTP.

    Com ``protocolo_escopado=True``, usa GET /pending?inbox_id=...&
    after_message_id=...&limit=... e POST /ack com inbox_id — mais
    seguro (filtragem antes do LIMIT, ACK nunca cruzado). Com
    ``protocolo_escopado=False`` (default), mantém o protocolo legado
    compatível com listener.py v0.6.x.
    """

    def __init__(
        self,
        caminho_sqlite: Path,
        *,
        conta_id: str,
        inbox_id: str,
        porta_listener: int = 3021,
        conversas_ignoradas: frozenset[str] = frozenset(),
        chamar_listener: Callable[[str, str, bytes | None], tuple[int, bytes]] | None = None,
        protocolo_escopado: bool = False,
        limite_pagina: int = _PAGINA_LIMITE_PADRAO,
    ) -> None:
        # Validações
        if not isinstance(caminho_sqlite, Path) or not caminho_sqlite.is_absolute():
            raise ValueError("caminho_sqlite_invalido")
        if not isinstance(conta_id, str) or not _ID_CONTA.fullmatch(conta_id):
            raise ValueError("conta_id_invalida")
        if not isinstance(inbox_id, str) or not _ID_CONTA.fullmatch(inbox_id):
            raise ValueError("inbox_id_invalido")
        if type(porta_listener) is not int or not (1 <= porta_listener <= 65535):
            raise ValueError("porta_invalida")
        if type(limite_pagina) is not int or not (1 <= limite_pagina <= _PAGINA_LIMITE_MAXIMO):
            raise ValueError("limite_pagina_invalido")

        self._caminho = caminho_sqlite
        self.conta_id = conta_id
        self.inbox_id = inbox_id
        self._inbox_ref = f"canal-{conta_id}-{inbox_id}"
        self._conversas_ignoradas = conversas_ignoradas
        self._protocolo_escopado = bool(protocolo_escopado)
        self._limite_pagina = limite_pagina
        self._cursor_escopado_continuacao = 0
        self._sincronizacao_lock = threading.Lock()
        self._ack_lock = threading.RLock()

        self._chamar = chamar_listener or _transporte_http(
            "127.0.0.1", porta_listener, 5
        )

        # Fila durável
        self._fila = FilaPersistente(caminho_sqlite, inbox_ref=self._inbox_ref)

        # Tabelas auxiliares
        with closing(self._conectar()) as conn:
            conn.executescript(_SCHEMA_AUX)

    @property
    def protocolo_escopado(self) -> bool:
        return self._protocolo_escopado

    def _conectar(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._caminho, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Transporte ──────────────────────────────────────────────────

    def _post_ack_legado(self, message_ids: list[str]) -> bool:
        """POST /ack legado → True se HTTP 200 {"ok": True}."""
        corpo = json.dumps(
            {"message_ids": [int(m) for m in message_ids]}
        ).encode("utf-8")
        try:
            status, body = self._chamar("POST", "/ack", corpo)
        except Exception:
            return False
        if status != 200:
            return False
        try:
            dados = json.loads(body)
        except Exception:
            return False
        return isinstance(dados, dict) and dados.get("ok") is True

    def _post_ack_escopado(self, message_ids: list[str]) -> dict:
        """POST /ack escopado, com envelope e aceites validados."""

        def falha(codigo: str) -> dict:
            return {
                "ok": False, "codigo": codigo,
                "accepted": [], "rejected": list(message_ids),
            }

        corpo = json.dumps({
            "inbox_id": int(self.inbox_id),
            "message_ids": [int(m) for m in message_ids],
        }).encode("utf-8")
        try:
            status, body = self._chamar("POST", "/ack", corpo)
        except Exception:
            return falha("listener_indisponivel")
        if status != 200:
            return falha("listener_indisponivel")
        try:
            dados = json.loads(body)
        except Exception:
            return falha("resposta_invalida")
        if not isinstance(dados, dict) or dados.get("ok") is not True:
            return falha("resposta_invalida")
        if dados.get("scoped") is not True:
            return falha("listener_legado_incompativel")
        inbox_resposta = dados.get("inbox_id")
        if (type(inbox_resposta) is not int
                or inbox_resposta != int(self.inbox_id)):
            return falha("resposta_invalida")
        accepted_raw = dados.get("accepted")
        if not isinstance(accepted_raw, list):
            return falha("resposta_invalida")
        accepted = [str(x) for x in accepted_raw if str(x) in set(message_ids)]
        rejected_set = set(message_ids) - set(accepted)
        return {
            "ok": True,
            "accepted": accepted,
            "rejected": [m for m in message_ids if m in rejected_set],
        }

    def _get_pending_legado(self) -> list | None:
        """GET /pending legado → lista ou None."""
        try:
            status, body = self._chamar("GET", "/pending", None)
        except Exception:
            return None
        if status != 200:
            return None
        try:
            dados = json.loads(body)
        except Exception:
            return None
        if not isinstance(dados, dict) or not isinstance(dados.get("pending"), list):
            return None
        return dados["pending"]

    def _get_pending_escopado(
        self,
        *,
        after_message_id: int = 0,
        limit: int = _PAGINA_LIMITE_PADRAO,
    ) -> tuple[dict | None, str | None]:
        """Retorna a página e, em falha, o motivo público do erro."""
        params = urlencode({
            "inbox_id": self.inbox_id,
            "after_message_id": after_message_id,
            "limit": limit,
        })
        caminho = f"/pending?{params}"
        try:
            status, body = self._chamar("GET", caminho, None)
        except Exception:
            return None, "listener_indisponivel"
        if status != 200:
            return None, "listener_indisponivel"
        try:
            dados = json.loads(body)
        except Exception:
            return None, "resposta_invalida"
        if not isinstance(dados, dict):
            return None, "resposta_invalida"
        if dados.get("scoped") is not True:
            return None, "listener_legado_incompativel"
        inbox_resposta = dados.get("inbox_id")
        if (type(inbox_resposta) is not int
                or inbox_resposta != int(self.inbox_id)):
            return None, "resposta_invalida"
        if not isinstance(dados.get("pending"), list):
            return None, "resposta_invalida"
        return dados, None

    # ── ACK pendentes ───────────────────────────────────────────────

    def _descarregar_acks(self) -> int:
        with self._ack_lock:
            return self._descarregar_acks_sem_trava()

    def _descarregar_acks_sem_trava(self) -> int:
        """Descarrega ACKs e conclui localmente só os aceites confirmados."""
        with closing(self._conectar()) as conn:
            pendentes = [
                row["message_id"]
                for row in conn.execute(
                    "SELECT message_id FROM acks_listener_pendentes_v1 WHERE inbox_ref = ?",
                    (self._inbox_ref,),
                )
            ]
        if not pendentes:
            return 0
        if self._protocolo_escopado:
            resultado = self._post_ack_escopado(pendentes)
            if not resultado["ok"]:
                return len(pendentes)
            aceitos = set(resultado["accepted"])
            remover = [m for m in pendentes if m in aceitos]
        elif self._post_ack_legado(pendentes):
            remover = pendentes
        else:
            return len(pendentes)

        if remover:
            # A aceitação externa já ocorreu. Marcar antes de apagar a intenção
            # permite que uma eventual repetição use o ACK idempotente.
            self._fila.marcar_entregues(remover)
            with closing(self._conectar()) as conn, conn:
                conn.executemany(
                    "DELETE FROM acks_listener_pendentes_v1 "
                    "WHERE inbox_ref = ? AND message_id = ?",
                    [(self._inbox_ref, m) for m in remover],
                )
        return len(pendentes) - len(remover)

    def _contar_acks_pendentes(self) -> int:
        with closing(self._conectar()) as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM acks_listener_pendentes_v1 WHERE inbox_ref = ?",
                (self._inbox_ref,),
            ).fetchone()
            return row["n"] if row else 0

    # ── Validação de item ───────────────────────────────────────────

    def _validar_item(self, item: object) -> tuple[str, str] | None:
        """Valida um item do /pending. Retorna (mid, cid) ou None."""
        if not isinstance(item, Mapping):
            return None

        # message_id: int > 0 (exceto bool) ou str numérica
        raw_mid = item.get("message_id")
        if type(raw_mid) is int and 0 < raw_mid < 10**18:
            int_mid = raw_mid
        elif isinstance(raw_mid, str) and _MID.fullmatch(raw_mid):
            int_mid = int(raw_mid)
        else:
            return None

        # conversation_id
        raw_cid = item.get("conversation_id")
        if type(raw_cid) is int and 0 < raw_cid < 10**9:
            str_cid = str(raw_cid)
        elif isinstance(raw_cid, str) and _CID.fullmatch(raw_cid):
            str_cid = raw_cid
        else:
            return None

        if not _CID.fullmatch(str_cid):
            return None

        # Conversa ignorada
        if str_cid in self._conversas_ignoradas:
            return None

        # Grupo WhatsApp — inspeciona SÓ em memória, NUNCA grava
        contato_ref = item.get("contato_ref")
        if isinstance(contato_ref, str) and _GRUPO_WA.search(contato_ref):
            return None

        return str(int_mid), str_cid

    def _filtro_inbox_legado(self, item: Mapping) -> bool:
        """Protocolo legado: filtra inbox em memória."""
        try:
            return str(item.get("inbox_id")) == self.inbox_id
        except Exception:
            return False

    # ── Sincronização ───────────────────────────────────────────────

    def _sincronizar_legado(self) -> dict:
        """Sincronização com protocolo legado (GET /pending sem filtro)."""
        itens = self._get_pending_legado()
        if itens is None:
            n_acks = self._contar_acks_pendentes()
            return {
                "ok": False,
                "codigo": "listener_indisponivel",
                "acks_pendentes": n_acks,
            }

        n_ins = 0
        n_ex = 0
        n_filt = 0

        for item in itens:
            if not isinstance(item, Mapping) or not self._filtro_inbox_legado(item):
                n_filt += 1
                continue

            resultado = self._validar_item(item)
            if resultado is None:
                n_filt += 1
                continue

            mid, str_cid = resultado
            inserido = self._fila.registrar(message_id=mid, conversation_id=str_cid)
            if inserido:
                n_ins += 1
            else:
                n_ex += 1

            handoff = _sanitizar_handoff(item.get("handoff"))
            with closing(self._conectar()) as conn, conn:
                conn.execute(
                    "INSERT INTO metadados_evento_v1 (inbox_ref, message_id, handoff) "
                    "VALUES (?, ?, ?) ON CONFLICT (inbox_ref, message_id) DO UPDATE SET handoff = ?",
                    (self._inbox_ref, mid, handoff, handoff),
                )

        n_acks = self._contar_acks_pendentes()
        return {
            "ok": True,
            "codigo": None,
            "inseridos": n_ins,
            "existentes": n_ex,
            "filtrados": n_filt,
            "acks_pendentes": n_acks,
        }

    def _sincronizar_escopado(self) -> dict:
        """Percorre o inbox e preserva o cursor somente em passagem truncada."""
        cursor = self._cursor_escopado_continuacao
        n_ins = 0
        n_ex = 0
        n_filt = 0
        paginas = 0
        max_paginas = 50
        completa = False

        while paginas < max_paginas:
            paginas += 1
            resp, erro = self._get_pending_escopado(
                after_message_id=cursor,
                limit=self._limite_pagina,
            )
            if erro is not None:
                return {
                    "ok": False,
                    "codigo": erro,
                    "acks_pendentes": self._contar_acks_pendentes(),
                }

            itens = resp["pending"]
            if not itens:
                completa = True
                break

            for item in itens:
                # O cursor avança mesmo quando o item é filtrado.
                if isinstance(item, Mapping):
                    raw_mid = item.get("message_id")
                    try:
                        if raw_mid is not None:
                            mid_num = int(raw_mid)
                            if mid_num > cursor:
                                cursor = mid_num
                    except (ValueError, TypeError):
                        pass

                if not isinstance(item, Mapping):
                    n_filt += 1
                    continue
                try:
                    item_inbox = str(item.get("inbox_id"))
                except Exception:
                    n_filt += 1
                    continue
                if item_inbox != self.inbox_id:
                    n_filt += 1
                    continue

                resultado = self._validar_item(item)
                if resultado is None:
                    n_filt += 1
                    continue
                mid, str_cid = resultado
                inserido = self._fila.registrar(message_id=mid, conversation_id=str_cid)
                if inserido:
                    n_ins += 1
                else:
                    n_ex += 1

                handoff = _sanitizar_handoff(item.get("handoff"))
                with closing(self._conectar()) as conn, conn:
                    conn.execute(
                        "INSERT INTO metadados_evento_v1 (inbox_ref, message_id, handoff) "
                        "VALUES (?, ?, ?) ON CONFLICT (inbox_ref, message_id) DO UPDATE SET handoff = ?",
                        (self._inbox_ref, mid, handoff, handoff),
                    )

            if len(itens) < self._limite_pagina:
                completa = True
                break

        resultado = {
            "inseridos": n_ins,
            "existentes": n_ex,
            "filtrados": n_filt,
            "acks_pendentes": self._contar_acks_pendentes(),
        }
        if not completa:
            self._cursor_escopado_continuacao = cursor
            return {"ok": False, "codigo": "paginacao_incompleta", **resultado}

        # Uma passagem completa sempre reinicia em zero: webhooks fora de
        # ordem podem ter criado IDs menores enquanto o backlog era lido.
        self._cursor_escopado_continuacao = 0
        return {"ok": True, "codigo": None, **resultado}

    def sincronizar(self) -> dict:
        with self._sincronizacao_lock:
            self._descarregar_acks()
            if self._protocolo_escopado:
                return self._sincronizar_escopado()
            return self._sincronizar_legado()

    # ── Handoff do metadados ────────────────────────────────────────

    def _handoff_de(self, message_id: str) -> str | None:
        with closing(self._conectar()) as conn:
            row = conn.execute(
                "SELECT handoff FROM metadados_evento_v1 WHERE inbox_ref = ? AND message_id = ?",
                (self._inbox_ref, message_id),
            ).fetchone()
            return row["handoff"] if row else None

    # ── FilaPendencias ──────────────────────────────────────────────

    def listar_pendentes(self, limite: int = 20) -> list[dict]:
        if type(limite) is not int or not (1 <= limite <= 100):
            raise ValueError("limite_invalido")

        self.sincronizar()

        bruto = self._fila.listar_pendentes(limite)
        resultado = []
        for row in bruto:
            handoff = self._handoff_de(row["message_id"])
            resultado.append({
                "inbox_id": self.inbox_id,
                "message_id": row["message_id"],
                "conversation_id": row["conversation_id"],
                "recebido_em": row["recebido_em"],
                "handoff": handoff,
            })
        return resultado

    def obter(self, message_id: str) -> dict | None:
        row = self._fila.obter(message_id)
        if row is None:
            self.sincronizar()
            row = self._fila.obter(message_id)
        if row is None:
            return None
        handoff = self._handoff_de(row["message_id"])
        return {
            "inbox_id": self.inbox_id,
            "message_id": row["message_id"],
            "conversation_id": row["conversation_id"],
            "recebido_em": row["recebido_em"],
            "handoff": handoff,
            "estado": row["estado"],
        }

    def marcar_entregues(self, message_ids: Sequence[str]) -> list[str]:
        ids_validos: list[str] = []
        for mid in message_ids:
            if not isinstance(mid, str) or not _MID.fullmatch(mid):
                raise ValueError("message_id_invalido")
            ids_validos.append(mid)

        with self._ack_lock:
            candidatos: list[str] = []
            vistos: set[str] = set()
            with closing(self._conectar()) as conn, conn:
                for mid in ids_validos:
                    if mid in vistos:
                        continue
                    vistos.add(mid)
                    item = self._fila.obter(mid)
                    if item is None:
                        continue
                    if item["estado"] == "pendente":
                        candidatos.append(mid)
                    conn.execute(
                        "INSERT INTO acks_listener_pendentes_v1 (inbox_ref, message_id) "
                        "VALUES (?, ?) ON CONFLICT (inbox_ref, message_id) DO NOTHING",
                        (self._inbox_ref, mid),
                    )

            self._descarregar_acks()
            with closing(self._conectar()) as conn:
                restantes = {
                    row["message_id"]
                    for row in conn.execute(
                        "SELECT message_id FROM acks_listener_pendentes_v1"
                        " WHERE inbox_ref = ?",
                        (self._inbox_ref,),
                    )
                }
            # A descarga já concluiu a fila local. Devolver apenas transições
            # desta chamada cuja aceitação externa foi confirmada.
            return [mid for mid in candidatos if mid not in restantes]
