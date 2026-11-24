"""SQLite transacional do núcleo OPS, sem estado de produção."""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS autorizacoes (
    referencia TEXT PRIMARY KEY,
    agente_id TEXT NOT NULL,
    cliente_id TEXT NOT NULL,
    identidade_sujeito TEXT NOT NULL,
    funcoes_json TEXT NOT NULL,
    manifesto_hash TEXT NOT NULL,
    criado_em TEXT NOT NULL,
    consumido_em TEXT,
    revogado_em TEXT
);

CREATE TABLE IF NOT EXISTS tokens (
    id TEXT PRIMARY KEY,
    autorizacao_referencia TEXT NOT NULL UNIQUE
        REFERENCES autorizacoes(referencia),
    agente_id TEXT NOT NULL,
    cliente_id TEXT NOT NULL,
    identidade_sujeito TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    funcoes_json TEXT NOT NULL,
    manifesto_hash TEXT NOT NULL,
    criado_em TEXT NOT NULL,
    revogado_em TEXT
);
CREATE INDEX IF NOT EXISTS ix_tokens_agente ON tokens(agente_id);
CREATE INDEX IF NOT EXISTS ix_tokens_cliente ON tokens(cliente_id);

CREATE TABLE IF NOT EXISTS sessoes (
    id TEXT PRIMARY KEY,
    token_id TEXT NOT NULL REFERENCES tokens(id),
    criado_em TEXT NOT NULL,
    confirmado_em TEXT,
    manifesto_confirmado_hash TEXT,
    resumo_sha256 TEXT,
    resumo_tamanho INTEGER,
    desconectado_em TEXT
);
CREATE INDEX IF NOT EXISTS ix_sessoes_token ON sessoes(token_id);

CREATE TABLE IF NOT EXISTS leases (
    area TEXT PRIMARY KEY,
    token_id TEXT NOT NULL REFERENCES tokens(id),
    sessao_id TEXT NOT NULL REFERENCES sessoes(id),
    adquirido_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_leases_token ON leases(token_id);

CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criado_em TEXT NOT NULL,
    ator_tipo TEXT NOT NULL,
    ator_id TEXT,
    agente_id TEXT,
    token_id TEXT,
    sessao_id TEXT,
    area TEXT,
    funcao_id TEXT,
    acao TEXT NOT NULL,
    argumentos_json TEXT NOT NULL,
    resultado_json TEXT NOT NULL,
    erro_codigo TEXT
);
CREATE INDEX IF NOT EXISTS ix_auditoria_sessao ON auditoria(sessao_id, id);
CREATE INDEX IF NOT EXISTS ix_auditoria_agente ON auditoria(agente_id, id);
"""


class BancoOps:
    """Uma conexão curta por operação; escritas serializadas com BEGIN IMMEDIATE."""

    def __init__(self, caminho: str | Path) -> None:
        self._memoria = str(caminho) == ":memory:"
        if self._memoria:
            self._alvo = f"file:mcp_ops_{uuid.uuid4().hex}?mode=memory&cache=shared"
        else:
            self._alvo = str(Path(caminho))
        self._keeper = self._nova_conexao() if self._memoria else None
        with self.transacao() as conn:
            conn.executescript(SCHEMA)

    def _nova_conexao(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self._alvo,
            timeout=10,
            isolation_level=None,
            uri=self._memoria,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 10000")
        if not self._memoria:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    @contextmanager
    def transacao(self) -> Iterator[sqlite3.Connection]:
        conn = self._nova_conexao()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    @contextmanager
    def leitura(self) -> Iterator[sqlite3.Connection]:
        conn = self._nova_conexao()
        try:
            yield conn
        finally:
            conn.close()

    def close(self) -> None:
        if self._keeper is not None:
            self._keeper.close()
            self._keeper = None
