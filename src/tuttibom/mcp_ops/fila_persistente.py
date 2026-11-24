"""Fila local do ambiente isolado: guarda referências opacas, não mensagens."""
from __future__ import annotations

import re
import sqlite3
from collections.abc import Sequence
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

_REF = re.compile(r"[a-zA-Z0-9_-]{1,96}")


def _ref(valor: str) -> str:
    if not isinstance(valor, str) or _REF.fullmatch(valor) is None:
        raise ValueError("referencia_invalida")
    return valor


class FilaPersistente:
    """Entrada única por mensagem; ACK não depende da sessão do atendente."""

    def __init__(self, caminho: Path, *, inbox_ref: str) -> None:
        self._caminho = caminho
        self._inbox = _ref(inbox_ref)
        with closing(self._conectar()) as conn, conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pendencias_v1 (
                    seq INTEGER PRIMARY KEY,
                    inbox_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    recebido_em TEXT NOT NULL,
                    estado TEXT NOT NULL CHECK(estado IN ('pendente', 'entregue')),
                    UNIQUE(inbox_id, message_id)
                )
            """)

    def _conectar(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._caminho, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def registrar(self, *, message_id: str, conversation_id: str) -> bool:
        message_id = _ref(message_id)
        conversa = _ref(conversation_id)
        agora = datetime.now(timezone.utc).isoformat()
        with closing(self._conectar()) as conn, conn:
            inserido = conn.execute("""
                INSERT INTO pendencias_v1 (inbox_id, message_id, conversation_id, recebido_em, estado)
                VALUES (?, ?, ?, ?, 'pendente')
                ON CONFLICT (inbox_id, message_id) DO NOTHING
            """, (self._inbox, message_id, conversa, agora)).rowcount
            if not inserido:
                anterior = conn.execute("""
                    SELECT conversation_id FROM pendencias_v1
                    WHERE inbox_id = ? AND message_id = ?
                """, (self._inbox, message_id)).fetchone()
                if anterior["conversation_id"] != conversa:
                    raise ValueError("mensagem_em_outra_conversa")
            return inserido == 1

    def listar_pendentes(self, limite: int = 20) -> list[dict]:
        if type(limite) is not int or not 1 <= limite <= 100:
            raise ValueError("limite_invalido")
        with closing(self._conectar()) as conn:
            return [dict(row) for row in conn.execute("""
                SELECT inbox_id, message_id, conversation_id, recebido_em
                FROM pendencias_v1 WHERE inbox_id = ? AND estado = 'pendente'
                ORDER BY seq LIMIT ?
            """, (self._inbox, limite))]

    def obter(self, message_id: str) -> dict | None:
        with closing(self._conectar()) as conn:
            row = conn.execute("""
                SELECT inbox_id, message_id, conversation_id, recebido_em, estado
                FROM pendencias_v1 WHERE inbox_id = ? AND message_id = ?
            """, (self._inbox, _ref(message_id))).fetchone()
            return dict(row) if row else None

    def marcar_entregues(self, message_ids: Sequence[str]) -> list[str]:
        ids = tuple(map(_ref, message_ids))
        marcados: list[str] = []
        with closing(self._conectar()) as conn, conn:
            for msg in ids:
                alterado = conn.execute("""
                    UPDATE pendencias_v1 SET estado = 'entregue'
                    WHERE inbox_id = ? AND message_id = ? AND estado = 'pendente'
                """, (self._inbox, msg)).rowcount
                if alterado:
                    marcados.append(msg)
        return marcados
