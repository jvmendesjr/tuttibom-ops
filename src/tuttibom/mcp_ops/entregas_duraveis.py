"""Diário SQLite durável para envio e ACK do atendimento em desenvolvimento.

O módulo não envia mensagens, não faz ACK externo e não abre rede. Ele registra
intenções, tentativas e confirmações para que a integração do AdaptadorAtendimento
saiba qual efeito é permitido depois de falhas e reinícios.

Invariantes:
- toda reserva é commitada antes do efeito externo;
- cada message_id real pertence a no máximo uma entrega lógica;
- mudança de idempotency_key reencontra a mesma entrega pelos message_ids+digest;
- reserva abandonada vira incerteza apenas por recuperação explícita e nunca retry;
- envio aceito permite somente ACK até todos os message_ids estarem confirmados;
- nenhum texto, mídia, conversa ou dado de contato é persistido.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
import uuid
from collections.abc import Callable, Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from tuttibom.contratos.pii import detectar_pii

_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS entregas_diario (
    id TEXT PRIMARY KEY,
    digest TEXT NOT NULL,
    estado TEXT NOT NULL CHECK (
        estado IN ('nao_enviado', 'reservado', 'incerto', 'aceito', 'concluido')
    ),
    tentativa_atual_id TEXT,
    envio_ref TEXT,
    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL,
    aceito_em TEXT,
    falha_ack_em TEXT,
    recuperado_em TEXT
);

CREATE TABLE IF NOT EXISTS entregas_chaves (
    chave TEXT PRIMARY KEY,
    entrega_id TEXT NOT NULL REFERENCES entregas_diario(id),
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entregas_tentativas (
    id TEXT PRIMARY KEY,
    entrega_id TEXT NOT NULL REFERENCES entregas_diario(id),
    estado TEXT NOT NULL CHECK (
        estado IN ('nao_enviado', 'reservado', 'incerto', 'aceito', 'concluido')
    ),
    reservado_em TEXT NOT NULL,
    encerrado_em TEXT
);
CREATE INDEX IF NOT EXISTS ix_entregas_tentativas_entrega
    ON entregas_tentativas(entrega_id, reservado_em);

CREATE TABLE IF NOT EXISTS entregas_mensagens (
    message_id TEXT PRIMARY KEY,
    entrega_id TEXT NOT NULL REFERENCES entregas_diario(id),
    tentativa_atual_id TEXT NOT NULL REFERENCES entregas_tentativas(id),
    ack_em TEXT,
    criado_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_entregas_mensagens_entrega
    ON entregas_mensagens(entrega_id, message_id);
"""


class ErroEntregaDuravel(Exception):
    """Erro de chamada à API, sem repetir valores potencialmente sensíveis."""

    def __init__(self, codigo: str = "argumento_invalido") -> None:
        self.codigo = codigo
        super().__init__(codigo)


def _ref(valor: object, *, verificar_pii: bool = True) -> str:
    if not isinstance(valor, str) or not _REF.fullmatch(valor):
        raise ErroEntregaDuravel()
    if verificar_pii and detectar_pii(valor) is not None:
        raise ErroEntregaDuravel()
    return valor


def _message_ids(valores: Sequence[str]) -> tuple[str, ...]:
    if isinstance(valores, (str, bytes, bytearray)):
        raise ErroEntregaDuravel()
    try:
        ids = tuple(valores)
    except TypeError as exc:
        raise ErroEntregaDuravel() from exc
    if not ids:
        raise ErroEntregaDuravel("message_ids_obrigatorios")
    limpos = tuple(_ref(valor) for valor in ids)
    if len(set(limpos)) != len(limpos):
        raise ErroEntregaDuravel("message_ids_duplicados")
    return limpos


def _digest(valor: object) -> str:
    if not isinstance(valor, str) or not _DIGEST.fullmatch(valor):
        raise ErroEntregaDuravel("digest_invalido")
    return valor


def digest_envio(
    *,
    conversa_ref: str,
    texto: str,
    imagem: bytes | None,
    message_ids: Sequence[str],
) -> str:
    """Digest byte a byte compatível com o AdaptadorAtendimento.

    O idempotency_key não entra no digest: trocar a chave não pode criar outro
    envio para os mesmos message_ids e payload. Os dados sensíveis vivem só na
    chamada; o diário recebe e persiste apenas o hexadecimal resultante.
    """
    conversa_ref = _ref(conversa_ref)
    ids = _message_ids(message_ids)
    if not isinstance(texto, str) or texto == "":
        raise ErroEntregaDuravel()
    if imagem is not None:
        if not isinstance(imagem, (bytes, bytearray)) or len(imagem) == 0:
            raise ErroEntregaDuravel()
        imagem = bytes(imagem)

    hasher = hashlib.sha256()
    bruto = texto.encode("utf-8")
    hasher.update(len(bruto).to_bytes(8, "big"))
    hasher.update(bruto)
    if imagem is None:
        hasher.update(b"\x00")
    else:
        hasher.update(b"\x01")
        hasher.update(len(imagem).to_bytes(8, "big"))
        hasher.update(imagem)
    payload_digest = hasher.hexdigest()

    hasher = hashlib.sha256()
    hasher.update(payload_digest.encode("ascii"))
    hasher.update(b"\0")
    hasher.update(conversa_ref.encode("utf-8"))
    hasher.update(b"\0")
    for message_id in ids:
        hasher.update(message_id.encode("utf-8"))
        hasher.update(b"\0")
    return hasher.hexdigest()


class DiarioEntregas:
    """Diário persistente com conexões e transações próprias, fora do BancoOps."""

    def __init__(
        self,
        caminho_banco: str | Path,
        *,
        relogio: Callable[[], datetime] | None = None,
    ) -> None:
        if str(caminho_banco) == ":memory:":
            raise ErroEntregaDuravel("banco_persistente_obrigatorio")
        self._caminho = Path(caminho_banco)
        self._relogio = relogio or (lambda: datetime.now(timezone.utc))
        with self._transacao() as conn:
            conn.executescript(_SCHEMA)

    def __repr__(self) -> str:
        return "DiarioEntregas(sqlite_persistente)"

    def _conectar(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self._caminho,
            timeout=10,
            isolation_level=None,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 10000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = FULL")
        return conn

    @contextmanager
    def _transacao(self) -> Iterator[sqlite3.Connection]:
        conn = self._conectar()
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
    def _leitura(self) -> Iterator[sqlite3.Connection]:
        conn = self._conectar()
        try:
            yield conn
        finally:
            conn.close()

    def _agora(self) -> str:
        valor = self._relogio()
        if not isinstance(valor, datetime):
            raise ErroEntregaDuravel("relogio_invalido")
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
        return valor.astimezone(timezone.utc).isoformat(timespec="microseconds")

    @staticmethod
    def _ids_no_banco(conn: sqlite3.Connection, entrega_id: str) -> list[str]:
        return [
            row["message_id"]
            for row in conn.execute(
                "SELECT message_id FROM entregas_mensagens"
                " WHERE entrega_id = ? ORDER BY message_id",
                (entrega_id,),
            )
        ]

    def _resultado(
        self,
        conn: sqlite3.Connection,
        entrega_id: str,
        *,
        acao: str | None = None,
        codigo: str | None = None,
        replay: bool = False,
    ) -> dict[str, Any]:
        row = conn.execute(
            "SELECT * FROM entregas_diario WHERE id = ?", (entrega_id,)
        ).fetchone()
        if row is None:
            raise ErroEntregaDuravel("entrega_desconhecida")
        if acao is None:
            acao = {
                "nao_enviado": "reservar",
                "reservado": "aguardar",
                "incerto": "bloqueado",
                "aceito": "somente_ack",
                "concluido": "nenhuma",
            }[row["estado"]]
        if codigo is None:
            if acao == "aguardar":
                codigo = "envio_em_andamento"
            elif acao == "bloqueado":
                codigo = "entrega_incerta"
        mensagens = list(conn.execute(
            "SELECT message_id, ack_em FROM entregas_mensagens"
            " WHERE entrega_id = ? ORDER BY message_id",
            (entrega_id,),
        ))
        return {
            "ok": acao in {"enviar", "reservar", "somente_ack", "nenhuma"},
            "codigo": codigo,
            "acao": acao,
            "estado": row["estado"],
            "entrega_id": row["id"],
            "tentativa_id": row["tentativa_atual_id"],
            "digest": row["digest"],
            "message_ids": [item["message_id"] for item in mensagens],
            "ack_pendentes": [item["message_id"] for item in mensagens if item["ack_em"] is None],
            "envio_ref": row["envio_ref"],
            "enviado": row["estado"] in {"aceito", "concluido"},
            "concluido": row["estado"] == "concluido",
            "replay": replay,
            "atualizado_em": row["atualizado_em"],
        }

    @staticmethod
    def _erro(codigo: str) -> dict[str, Any]:
        return {
            "ok": False,
            "codigo": codigo,
            "acao": "bloqueado",
            "estado": None,
            "entrega_id": None,
            "tentativa_id": None,
            "digest": None,
            "message_ids": [],
            "ack_pendentes": [],
            "envio_ref": None,
            "enviado": False,
            "concluido": False,
            "replay": False,
            "atualizado_em": None,
        }

    def _nova_tentativa(
        self,
        conn: sqlite3.Connection,
        entrega_id: str,
        agora: str,
    ) -> str:
        tentativa_id = f"ten_{uuid.uuid4().hex}"
        conn.execute(
            "INSERT INTO entregas_tentativas"
            " (id, entrega_id, estado, reservado_em) VALUES (?, ?, 'reservado', ?)",
            (tentativa_id, entrega_id, agora),
        )
        conn.execute(
            "UPDATE entregas_diario SET estado = 'reservado',"
            " tentativa_atual_id = ?, envio_ref = NULL, atualizado_em = ?,"
            " aceito_em = NULL, falha_ack_em = NULL, recuperado_em = NULL"
            " WHERE id = ?",
            (tentativa_id, agora, entrega_id),
        )
        conn.execute(
            "UPDATE entregas_mensagens SET tentativa_atual_id = ?, ack_em = NULL"
            " WHERE entrega_id = ?",
            (tentativa_id, entrega_id),
        )
        return tentativa_id

    def _retomar(
        self,
        conn: sqlite3.Connection,
        entrega_id: str,
        agora: str,
    ) -> dict[str, Any]:
        row = conn.execute(
            "SELECT estado FROM entregas_diario WHERE id = ?", (entrega_id,)
        ).fetchone()
        if row["estado"] == "nao_enviado":
            self._nova_tentativa(conn, entrega_id, agora)
            return self._resultado(conn, entrega_id, acao="enviar")
        return self._resultado(conn, entrega_id, replay=True)

    def reservar_envio(
        self,
        *,
        message_ids: Sequence[str],
        idempotency_key: str,
        digest: str,
    ) -> dict[str, Any]:
        """Reserva atomicamente o direito de enviar ou devolve a única ação segura.

        ``acao='enviar'`` é a única resposta que autoriza o efeito externo.
        """
        ids = _message_ids(message_ids)
        chave = _ref(idempotency_key)
        digest = _digest(digest)
        ids_ordenados = sorted(ids)
        agora = self._agora()
        with self._transacao() as conn:
            por_chave = conn.execute(
                "SELECT entrega_id FROM entregas_chaves WHERE chave = ?", (chave,)
            ).fetchone()
            if por_chave is not None:
                entrega_id = por_chave["entrega_id"]
                row = conn.execute(
                    "SELECT digest FROM entregas_diario WHERE id = ?", (entrega_id,)
                ).fetchone()
                if row["digest"] != digest or self._ids_no_banco(conn, entrega_id) != ids_ordenados:
                    return self._resultado(
                        conn, entrega_id, acao="bloqueado",
                        codigo="idempotencia_conflito", replay=True,
                    )
                return self._retomar(conn, entrega_id, agora)

            marcas = ",".join("?" for _ in ids)
            vinculos = list(conn.execute(
                f"SELECT entrega_id FROM entregas_mensagens WHERE message_id IN ({marcas})",
                ids,
            ))
            if vinculos:
                entregas = {row["entrega_id"] for row in vinculos}
                if len(vinculos) != len(ids) or len(entregas) != 1:
                    return self._erro("mensagem_ja_vinculada")
                entrega_id = next(iter(entregas))
                row = conn.execute(
                    "SELECT digest FROM entregas_diario WHERE id = ?", (entrega_id,)
                ).fetchone()
                if row["digest"] != digest or self._ids_no_banco(conn, entrega_id) != ids_ordenados:
                    return self._resultado(
                        conn, entrega_id, acao="bloqueado",
                        codigo="idempotencia_conflito", replay=True,
                    )
                conn.execute(
                    "INSERT INTO entregas_chaves (chave, entrega_id, criado_em)"
                    " VALUES (?, ?, ?)",
                    (chave, entrega_id, agora),
                )
                return self._retomar(conn, entrega_id, agora)

            entrega_id = f"ent_{uuid.uuid4().hex}"
            tentativa_id = f"ten_{uuid.uuid4().hex}"
            conn.execute(
                "INSERT INTO entregas_diario"
                " (id, digest, estado, tentativa_atual_id, criado_em, atualizado_em)"
                " VALUES (?, ?, 'reservado', ?, ?, ?)",
                (entrega_id, digest, tentativa_id, agora, agora),
            )
            conn.execute(
                "INSERT INTO entregas_tentativas"
                " (id, entrega_id, estado, reservado_em) VALUES (?, ?, 'reservado', ?)",
                (tentativa_id, entrega_id, agora),
            )
            conn.execute(
                "INSERT INTO entregas_chaves (chave, entrega_id, criado_em)"
                " VALUES (?, ?, ?)",
                (chave, entrega_id, agora),
            )
            for message_id in ids:
                conn.execute(
                    "INSERT INTO entregas_mensagens"
                    " (message_id, entrega_id, tentativa_atual_id, criado_em)"
                    " VALUES (?, ?, ?, ?)",
                    (message_id, entrega_id, tentativa_id, agora),
                )
            return self._resultado(conn, entrega_id, acao="enviar")

    def _tentativa(
        self, conn: sqlite3.Connection, tentativa_id: str
    ) -> sqlite3.Row | None:
        return conn.execute(
            "SELECT t.id AS tentativa_id, t.estado AS tentativa_estado,"
            " d.* FROM entregas_tentativas t"
            " JOIN entregas_diario d ON d.id = t.entrega_id"
            " WHERE t.id = ?",
            (tentativa_id,),
        ).fetchone()

    def confirmar_envio(
        self,
        *,
        tentativa_id: str,
        envio_ref: str,
    ) -> dict[str, Any]:
        """Persiste o aceite externo; depois disso nenhum novo envio é permitido."""
        tentativa_id = _ref(tentativa_id, verificar_pii=False)
        envio_ref = _ref(envio_ref)
        agora = self._agora()
        with self._transacao() as conn:
            row = self._tentativa(conn, tentativa_id)
            if row is None:
                return self._erro("tentativa_desconhecida")
            entrega_id = row["id"]
            if row["tentativa_atual_id"] != tentativa_id:
                return self._resultado(
                    conn, entrega_id, acao="bloqueado",
                    codigo="tentativa_substituída", replay=True,
                )
            if row["estado"] in {"aceito", "concluido"}:
                if row["envio_ref"] != envio_ref:
                    return self._resultado(
                        conn, entrega_id, acao="bloqueado",
                        codigo="envio_conflito", replay=True,
                    )
                return self._resultado(conn, entrega_id, replay=True)
            if row["estado"] == "incerto":
                return self._resultado(conn, entrega_id, replay=True)
            if row["estado"] != "reservado" or row["tentativa_estado"] != "reservado":
                return self._resultado(
                    conn, entrega_id, acao="bloqueado",
                    codigo="tentativa_nao_reservada", replay=True,
                )
            conn.execute(
                "UPDATE entregas_diario SET estado = 'aceito', envio_ref = ?,"
                " aceito_em = ?, atualizado_em = ? WHERE id = ?",
                (envio_ref, agora, agora, entrega_id),
            )
            conn.execute(
                "UPDATE entregas_tentativas SET estado = 'aceito', encerrado_em = ?"
                " WHERE id = ?",
                (agora, tentativa_id),
            )
            return self._resultado(conn, entrega_id)

    def registrar_falha_envio(
        self,
        *,
        tentativa_id: str,
        comprovadamente_nao_enviado: bool,
    ) -> dict[str, Any]:
        """Só libera retry com prova de não envio; caso contrário marca incerto."""
        tentativa_id = _ref(tentativa_id, verificar_pii=False)
        if not isinstance(comprovadamente_nao_enviado, bool):
            raise ErroEntregaDuravel()
        agora = self._agora()
        with self._transacao() as conn:
            row = self._tentativa(conn, tentativa_id)
            if row is None:
                return self._erro("tentativa_desconhecida")
            entrega_id = row["id"]
            if row["tentativa_atual_id"] != tentativa_id:
                return self._resultado(
                    conn, entrega_id, acao="bloqueado",
                    codigo="tentativa_substituída", replay=True,
                )
            if row["estado"] in {"nao_enviado", "incerto", "aceito", "concluido"}:
                return self._resultado(conn, entrega_id, replay=True)
            if row["estado"] != "reservado" or row["tentativa_estado"] != "reservado":
                return self._resultado(
                    conn, entrega_id, acao="bloqueado",
                    codigo="tentativa_nao_reservada", replay=True,
                )
            estado = "nao_enviado" if comprovadamente_nao_enviado else "incerto"
            conn.execute(
                "UPDATE entregas_diario SET estado = ?, atualizado_em = ?,"
                " recuperado_em = CASE WHEN ? = 'incerto' THEN ? ELSE recuperado_em END"
                " WHERE id = ?",
                (estado, agora, estado, agora, entrega_id),
            )
            conn.execute(
                "UPDATE entregas_tentativas SET estado = ?, encerrado_em = ? WHERE id = ?",
                (estado, agora, tentativa_id),
            )
            return self._resultado(conn, entrega_id)

    def registrar_falha_ack(self, *, tentativa_id: str) -> dict[str, Any]:
        """Registra só o timestamp; o envio aceito continua aguardando ACK."""
        tentativa_id = _ref(tentativa_id, verificar_pii=False)
        agora = self._agora()
        with self._transacao() as conn:
            row = self._tentativa(conn, tentativa_id)
            if row is None:
                return self._erro("tentativa_desconhecida")
            if row["estado"] == "concluido":
                return self._resultado(conn, row["id"], replay=True)
            if row["estado"] != "aceito" or row["tentativa_atual_id"] != tentativa_id:
                return self._resultado(
                    conn, row["id"], acao="bloqueado",
                    codigo="ack_nao_permitido", replay=True,
                )
            conn.execute(
                "UPDATE entregas_diario SET falha_ack_em = ?, atualizado_em = ?"
                " WHERE id = ?",
                (agora, agora, row["id"]),
            )
            return self._resultado(conn, row["id"])

    def registrar_ack(
        self,
        *,
        tentativa_id: str,
        message_id: str,
    ) -> dict[str, Any]:
        """Confirma um ACK real por message_id; conclui só quando não faltar nenhum."""
        tentativa_id = _ref(tentativa_id, verificar_pii=False)
        message_id = _ref(message_id)
        agora = self._agora()
        with self._transacao() as conn:
            row = self._tentativa(conn, tentativa_id)
            if row is None:
                return self._erro("tentativa_desconhecida")
            entrega_id = row["id"]
            mensagem = conn.execute(
                "SELECT * FROM entregas_mensagens"
                " WHERE message_id = ? AND entrega_id = ?",
                (message_id, entrega_id),
            ).fetchone()
            if mensagem is None:
                return self._resultado(
                    conn, entrega_id, acao="bloqueado",
                    codigo="mensagem_nao_vinculada", replay=True,
                )
            if row["estado"] == "concluido" and mensagem["ack_em"] is not None:
                return self._resultado(conn, entrega_id, replay=True)
            if (
                row["estado"] != "aceito"
                or row["tentativa_estado"] != "aceito"
                or row["tentativa_atual_id"] != tentativa_id
                or mensagem["tentativa_atual_id"] != tentativa_id
            ):
                return self._resultado(
                    conn, entrega_id, acao="bloqueado",
                    codigo="ack_nao_permitido", replay=True,
                )
            ack_repetido = mensagem["ack_em"] is not None
            if mensagem["ack_em"] is None:
                conn.execute(
                    "UPDATE entregas_mensagens SET ack_em = ? WHERE message_id = ?",
                    (agora, message_id),
                )
            pendentes = conn.execute(
                "SELECT COUNT(*) FROM entregas_mensagens"
                " WHERE entrega_id = ? AND ack_em IS NULL",
                (entrega_id,),
            ).fetchone()[0]
            if pendentes == 0:
                conn.execute(
                    "UPDATE entregas_diario SET estado = 'concluido', atualizado_em = ?"
                    " WHERE id = ?",
                    (agora, entrega_id),
                )
                conn.execute(
                    "UPDATE entregas_tentativas SET estado = 'concluido', encerrado_em = ?"
                    " WHERE id = ?",
                    (agora, tentativa_id),
                )
            else:
                conn.execute(
                    "UPDATE entregas_diario SET atualizado_em = ? WHERE id = ?",
                    (agora, entrega_id),
                )
            return self._resultado(conn, entrega_id, replay=ack_repetido)

    def recuperar_reservas(self) -> int:
        """Marca reservas abandonadas como incertas, nunca como não enviadas.

        Deve ser chamado pela inicialização somente com exclusividade de escritor.
        Não toca em envios aceitos, inclusive os que têm ACK parcial ou falho.
        """
        agora = self._agora()
        with self._transacao() as conn:
            rows = list(conn.execute(
                "SELECT id, tentativa_atual_id FROM entregas_diario"
                " WHERE estado = 'reservado'"
            ))
            for row in rows:
                conn.execute(
                    "UPDATE entregas_diario SET estado = 'incerto',"
                    " recuperado_em = ?, atualizado_em = ? WHERE id = ?",
                    (agora, agora, row["id"]),
                )
                conn.execute(
                    "UPDATE entregas_tentativas SET estado = 'incerto', encerrado_em = ?"
                    " WHERE id = ? AND estado = 'reservado'",
                    (agora, row["tentativa_atual_id"]),
                )
            return len(rows)

    def listar_acoes_pendentes(self, limite: int = 100) -> list[dict[str, Any]]:
        """Lista apenas ACK pendente e incerteza; nunca sugere reenvio automático."""
        if not isinstance(limite, int) or isinstance(limite, bool) or not 1 <= limite <= 500:
            raise ErroEntregaDuravel()
        with self._leitura() as conn:
            rows = list(conn.execute(
                "SELECT id FROM entregas_diario"
                " WHERE estado IN ('aceito', 'incerto')"
                " ORDER BY atualizado_em, id LIMIT ?",
                (limite,),
            ))
            return [self._resultado(conn, row["id"], replay=True) for row in rows]

    def consultar_mensagem(self, message_id: str) -> dict[str, Any] | None:
        """Mapa durável message_id -> entrega e tentativa atual, com timestamp de ACK."""
        message_id = _ref(message_id)
        with self._leitura() as conn:
            row = conn.execute(
                "SELECT m.*, d.estado FROM entregas_mensagens m"
                " JOIN entregas_diario d ON d.id = m.entrega_id"
                " WHERE m.message_id = ?",
                (message_id,),
            ).fetchone()
            if row is None:
                return None
            return {
                "message_id": row["message_id"],
                "entrega_id": row["entrega_id"],
                "tentativa_id": row["tentativa_atual_id"],
                "estado": row["estado"],
                "ack_em": row["ack_em"],
            }
