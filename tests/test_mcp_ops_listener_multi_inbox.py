"""Testes para suporte multi-inbox no ingestao_listener e protocolo escopado.

Cobre os requisitos de aceitação:
1. >20 mensagens no inbox 1 não escondem mensagens do inbox 2 (sem starvation).
2. Paginação keyset via after_message_id e limit.
3. Nenhum ACK gerado durante leitura de pendências ou preparação de resposta.
4. Confirmação parcial de ACKs: reattempt apenas para os restantes.
5. ACK nunca confirma ou apaga mensagem de outro inbox.
6. Recusa estrita de listener antigo sem fallback global quando protocolo_escopado=True.
7. Avanço de cursor keyset mesmo quando itens são filtrados/ignorados.
8. Validação funcional direta das rotinas do listener versionado em integracoes/ana_listener/.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from contextlib import closing
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from tuttibom.mcp_ops.fila_persistente import FilaPersistente
from tuttibom.mcp_ops.ingestao_listener import FilaIngestaoListener


# ── Simulador de Listener HTTP com Protocolo Escopado ───────────────

class ListenerSimulado:
    """Simulador em memória para testar protocolo legado e escopado."""

    def __init__(self, *, modo_escopado: bool = True) -> None:
        self.modo_escopado = modo_escopado
        # itens: lista de dicts com message_id, conversation_id, inbox_id, etc.
        self.eventos: list[dict] = []
        self.historico_chamadas: list[tuple[str, str, dict | None]] = []
        self.acks_recebidos: list[dict] = []
        self.falhar_get = False
        self.falhar_post_ack = False

    def adicionar_evento(
        self,
        message_id: int,
        inbox_id: int,
        conversation_id: int = 10,
        contato_ref: str = "ct-ok",
        handoff: str | None = None,
        estado: str = "pendente",
    ) -> None:
        self.eventos.append({
            "message_id": message_id,
            "conversation_id": conversation_id,
            "inbox_id": inbox_id,
            "contato_ref": contato_ref,
            "handoff": handoff,
            "recebido_em": "2026-11-24T10:00:00Z",
            "estado": estado,
            "cumprimento": None,
        })

    def _encontrar(self, message_id: int, inbox_id: int | None = None) -> dict | None:
        encontrados = [
            evento for evento in self.eventos
            if evento["message_id"] == message_id
            and (inbox_id is None or evento["inbox_id"] == inbox_id)
        ]
        # O modo legado não pode escolher uma linha quando o ID é ambíguo.
        if len(encontrados) != 1:
            return None
        return encontrados[0]

    def chamar(
        self, metodo: str, caminho: str, corpo: bytes | None
    ) -> tuple[int, bytes]:
        payload = json.loads(corpo.decode("utf-8")) if corpo else None
        self.historico_chamadas.append((metodo, caminho, payload))

        if metodo == "GET" and (caminho == "/pending" or caminho.startswith("/pending?")):
            if self.falhar_get:
                return 500, b'{"error": "falha_simulada"}'

            parsed = urlparse(caminho)
            qs = parse_qs(parsed.query)

            if "inbox_id" in qs and self.modo_escopado:
                target_inbox = int(qs["inbox_id"][0])
                after_mid = int(qs.get("after_message_id", [0])[0])
                limit = int(qs.get("limit", [50])[0])

                # Filtragem antes do LIMIT (inbox_id e after_message_id)
                filtrados = [
                    e for e in self.eventos
                    if e["estado"] == "pendente"
                    and e["inbox_id"] == target_inbox
                    and e["message_id"] > after_mid
                ]
                filtrados.sort(key=lambda x: x["message_id"])
                pagina = filtrados[:limit]

                resp = {
                    "ok": True,
                    "scoped": True,
                    "inbox_id": target_inbox,
                    "after_message_id": after_mid,
                    "limit": limit,
                    "count": len(pagina),
                    "pending": pagina,
                }
                return 200, json.dumps(resp).encode("utf-8")
            else:
                # Resposta legada (sem 'scoped': True, sem filtro de inbox prévio)
                filtrados = [e for e in self.eventos if e["estado"] == "pendente"]
                filtrados.sort(key=lambda x: x["message_id"])
                resp = {"pending": filtrados[:20]}
                return 200, json.dumps(resp).encode("utf-8")

        elif metodo == "POST" and caminho == "/ack":
            if self.falhar_post_ack:
                return 500, b'{"error": "falha_ack"}'

            self.acks_recebidos.append(payload or {})
            if self.modo_escopado and isinstance(payload, dict) and "inbox_id" in payload:
                target_inbox = int(payload["inbox_id"])
                mids = [int(x) for x in payload.get("message_ids", [])]

                accepted = []
                rejected = []
                marcados = 0
                for mid in mids:
                    ev = self._encontrar(mid, target_inbox)
                    if ev is not None and ev["estado"] in {"pendente", "entregue"}:
                        if ev["estado"] == "pendente":
                            ev["estado"] = "entregue"
                            marcados += 1
                        accepted.append(mid)
                    else:
                        rejected.append(mid)

                resp = {
                    "ok": True,
                    "scoped": True,
                    "inbox_id": target_inbox,
                    "marcados": marcados,
                    "accepted": accepted,
                    "rejected": rejected,
                }
                return 200, json.dumps(resp).encode("utf-8")
            else:
                # ACK legado: sem scoped
                mids = payload.get("message_ids", []) if isinstance(payload, dict) else []
                marcados = 0
                for mid in mids:
                    ev = self._encontrar(mid)
                    if ev is not None and ev["estado"] == "pendente":
                        ev["estado"] = "entregue"
                        marcados += 1
                return 200, json.dumps({"ok": True, "marcados": marcados}).encode("utf-8")

        return 404, b'{"error": "not_found"}'


# ── Testes de Aceitação ─────────────────────────────────────────────

def test_inbox1_maior_que_20_nao_esconde_inbox2(tmp_path: Path):
    """Cenário 1: >20 mensagens no inbox 1 não podem esconder mensagens do inbox 2."""
    sim = ListenerSimulado(modo_escopado=True)

    # 25 mensagens no inbox 1 (IDs 101..125)
    for i in range(1, 26):
        sim.adicionar_evento(message_id=100 + i, inbox_id=1, conversation_id=10)

    # 5 mensagens no inbox 2 (IDs 201..205)
    for i in range(1, 6):
        sim.adicionar_evento(message_id=200 + i, inbox_id=2, conversation_id=20)

    # Fila para inbox 2 com protocolo escopado
    fila_inbox2 = FilaIngestaoListener(
        tmp_path / "inbox2.sqlite",
        conta_id="2",
        inbox_id="2",
        chamar_listener=sim.chamar,
        protocolo_escopado=True,
    )

    pendentes_inbox2 = fila_inbox2.listar_pendentes(limite=20)
    # Garante que as 5 mensagens do inbox 2 foram recebidas e nenhuma foi ocultada
    assert len(pendentes_inbox2) == 5
    ids_inbox2 = [item["message_id"] for item in pendentes_inbox2]
    assert ids_inbox2 == ["201", "202", "203", "204", "205"]

    # Fila para inbox 1 com protocolo escopado
    fila_inbox1 = FilaIngestaoListener(
        tmp_path / "inbox1.sqlite",
        conta_id="2",
        inbox_id="1",
        chamar_listener=sim.chamar,
        protocolo_escopado=True,
    )

    pendentes_inbox1 = fila_inbox1.listar_pendentes(limite=50)
    assert len(pendentes_inbox1) == 25
    ids_inbox1 = [item["message_id"] for item in pendentes_inbox1]
    assert ids_inbox1[0] == "101"
    assert ids_inbox1[-1] == "125"


def test_paginacao_keyset_after_message_id_e_limit(tmp_path: Path):
    """Cenário 2: Paginação keyset via after_message_id e limit."""
    sim = ListenerSimulado(modo_escopado=True)

    # 55 mensagens no inbox 1 (IDs 1..55)
    for i in range(1, 56):
        sim.adicionar_evento(message_id=i, inbox_id=1, conversation_id=1)

    # Fila com limite de página = 20 para testar múltiplos saltos de página
    fila = FilaIngestaoListener(
        tmp_path / "paginacao.sqlite",
        conta_id="2",
        inbox_id="1",
        chamar_listener=sim.chamar,
        protocolo_escopado=True,
        limite_pagina=20,
    )

    res = fila.sincronizar()
    assert res["ok"] is True
    assert res["inseridos"] == 55

    # Inspeciona as chamadas GET realizadas
    gets = [c for c in sim.historico_chamadas if c[0] == "GET"]
    # Com 55 itens e limite 20:
    # Req 1: after_message_id=0, limit=20 (retorna 20 itens: 1..20)
    # Req 2: after_message_id=20, limit=20 (retorna 20 itens: 21..40)
    # Req 3: after_message_id=40, limit=20 (retorna 15 itens: 41..55)
    assert len(gets) == 3

    assert "after_message_id=0" in gets[0][1]
    assert "limit=20" in gets[0][1]

    assert "after_message_id=20" in gets[1][1]
    assert "limit=20" in gets[1][1]

    assert "after_message_id=40" in gets[2][1]
    assert "limit=20" in gets[2][1]

    # Nova sincronização recomeça do início do pending do inbox.
    res2 = fila.sincronizar()
    assert res2["ok"] is True
    assert res2["inseridos"] == 0
    gets2 = [c for c in sim.historico_chamadas if c[0] == "GET"][len(gets):]
    assert "after_message_id=0" in gets2[0][1]


def test_id_menor_gravado_depois_ainda_e_sincronizado(tmp_path: Path):
    """Webhook fora de ordem: ID menor que o maior já sincronizado não some."""
    sim = ListenerSimulado(modo_escopado=True)
    sim.adicionar_evento(message_id=50, inbox_id=2, conversation_id=20)
    fila = FilaIngestaoListener(
        tmp_path / "fora_de_ordem.sqlite", conta_id="2", inbox_id="2",
        chamar_listener=sim.chamar, protocolo_escopado=True,
    )
    assert fila.sincronizar()["inseridos"] == 1
    sim.adicionar_evento(message_id=49, inbox_id=2, conversation_id=21)
    assert fila.sincronizar()["inseridos"] == 1
    assert sorted(p["message_id"] for p in fila.listar_pendentes(limite=10)) == ["49", "50"]


def test_nenhum_ack_durante_leitura_ou_preparacao(tmp_path: Path):
    """Cenário 3: Nenhum ACK ocorre durante leitura ou preparação de resposta."""
    sim = ListenerSimulado(modo_escopado=True)
    sim.adicionar_evento(message_id=501, inbox_id=1, conversation_id=40)
    sim.adicionar_evento(message_id=502, inbox_id=1, conversation_id=40)

    fila = FilaIngestaoListener(
        tmp_path / "leitura_sem_ack.sqlite",
        conta_id="2",
        inbox_id="1",
        chamar_listener=sim.chamar,
        protocolo_escopado=True,
    )

    # 1. Leitura de pendências
    pendentes = fila.listar_pendentes(limite=10)
    assert len(pendentes) == 2

    # 2. Obtenção individual
    item = fila.obter("501")
    assert item is not None

    # Verifica que nenhuma chamada POST /ack foi realizada
    acks_enviados = [c for c in sim.historico_chamadas if c[0] == "POST" and c[1] == "/ack"]
    assert len(acks_enviados) == 0

    # Verifica que o banco auxiliar não tem nenhum ACK pendente de descarga
    assert fila._contar_acks_pendentes() == 0


def test_confirmacao_parcial_reattempt_somente_restantes(tmp_path: Path):
    """Cenário 4: Confirmação parcial de ACKs reattempta somente os IDs restantes."""
    db_path = tmp_path / "ack_parcial.sqlite"

    # Mock customizado onde a primeira chamada a /ack aceita apenas parte dos IDs
    tentativas: list[dict] = []

    def mock_listener(metodo: str, caminho: str, corpo: bytes | None) -> tuple[int, bytes]:
        if metodo == "GET":
            return 200, json.dumps({
                "ok": True,
                "scoped": True,
                "inbox_id": 1,
                "pending": [
                    {"message_id": 11, "conversation_id": 1, "inbox_id": 1, "contato_ref": "c1"},
                    {"message_id": 12, "conversation_id": 1, "inbox_id": 1, "contato_ref": "c2"},
                    {"message_id": 13, "conversation_id": 1, "inbox_id": 1, "contato_ref": "c3"},
                ],
            }).encode()

        if metodo == "POST" and caminho == "/ack":
            dados = json.loads(corpo.decode())
            tentativas.append(dados)
            mids = dados.get("message_ids", [])

            # Na primeira tentativa, aceita 11 e 13, mas recusa 12
            if len(tentativas) == 1:
                return 200, json.dumps({
                    "ok": True,
                    "scoped": True,
                    "inbox_id": 1,
                    "marcados": 2,
                    "accepted": [11, 13],
                    "rejected": [12],
                }).encode()
            else:
                # Na segunda tentativa, aceita o restante (12)
                return 200, json.dumps({
                    "ok": True,
                    "scoped": True,
                    "inbox_id": 1,
                    "marcados": len(mids),
                    "accepted": mids,
                    "rejected": [],
                }).encode()

        return 404, b"{}"

    fila = FilaIngestaoListener(
        db_path,
        conta_id="2",
        inbox_id="1",
        chamar_listener=mock_listener,
        protocolo_escopado=True,
    )

    fila.listar_pendentes()

    # Operador conclui as 3 mensagens
    fila.marcar_entregues(["11", "12", "13"])

    # Primeira tentativa ocorreu dentro de marcar_entregues
    assert len(tentativas) == 1
    assert set(tentativas[0]["message_ids"]) == {11, 12, 13}

    # Como 12 foi rejeitado, ele deve continuar pendente no banco local
    with closing(sqlite3.connect(db_path)) as conn:
        rows = conn.execute("SELECT message_id FROM acks_listener_pendentes_v1").fetchall()
        assert [r[0] for r in rows] == ["12"]

    # Próxima sincronização executa retry
    res_sync = fila.sincronizar()
    assert res_sync["ok"] is True

    # Segunda tentativa enviou estritamente o restante [12]
    assert len(tentativas) == 2
    assert tentativas[1]["message_ids"] == [12]

    # Agora a tabela de ACKs pendentes deve estar zerada
    with closing(sqlite3.connect(db_path)) as conn:
        assert conn.execute("SELECT COUNT(*) FROM acks_listener_pendentes_v1").fetchone()[0] == 0


def test_ack_nunca_confirma_outro_inbox(tmp_path: Path):
    """Cenário 5: ACK nunca confirma ou descarrega mensagem de outro inbox."""
    sim = ListenerSimulado(modo_escopado=True)
    sim.adicionar_evento(message_id=101, inbox_id=1, conversation_id=1)
    sim.adicionar_evento(message_id=201, inbox_id=2, conversation_id=2)

    fila1 = FilaIngestaoListener(
        tmp_path / "f1.sqlite",
        conta_id="2",
        inbox_id="1",
        chamar_listener=sim.chamar,
        protocolo_escopado=True,
    )
    fila2 = FilaIngestaoListener(
        tmp_path / "f2.sqlite",
        conta_id="2",
        inbox_id="2",
        chamar_listener=sim.chamar,
        protocolo_escopado=True,
    )

    fila1.sincronizar()
    fila2.sincronizar()

    # Tentativa de chamar marcar_entregues na fila 1 com a mensagem 201 (do inbox 2)
    marcados = fila1.marcar_entregues(["201"])
    # A fila 1 não possui a mensagem 201 registrada, portanto não a marca nem enfileira ACK
    assert "201" not in marcados
    assert fila1._contar_acks_pendentes() == 0

    # Nenhum ACK foi enviado para 201
    assert len(sim.acks_recebidos) == 0

    # Se uma chamada manual tentar forçar ACK de mensagem de outro inbox no listener escopado
    corpo = json.dumps({"inbox_id": 1, "message_ids": [201]}).encode()
    status, resp_raw = sim.chamar("POST", "/ack", corpo)
    assert status == 200
    resp = json.loads(resp_raw)
    assert resp["scoped"] is True
    assert 201 in resp["rejected"]
    assert 201 not in resp["accepted"]

    # Mensagem 201 permanece pendente no simulador
    ev201 = next(e for e in sim.eventos if e["message_id"] == 201)
    assert ev201["estado"] == "pendente"


def test_recusa_listener_antigo_sem_fallback_global(tmp_path: Path):
    """Cenário 6: Protocolo escopado recusa listener antigo e fecha com falha."""
    # Listener em modo legado (responde sem 'scoped': True)
    sim_legado = ListenerSimulado(modo_escopado=False)
    sim_legado.adicionar_evento(message_id=999, inbox_id=1)

    fila_escopada = FilaIngestaoListener(
        tmp_path / "recusa.sqlite",
        conta_id="2",
        inbox_id="1",
        chamar_listener=sim_legado.chamar,
        protocolo_escopado=True,
    )

    # Sincronização deve recusar
    resultado = fila_escopada.sincronizar()
    assert resultado["ok"] is False
    assert resultado["codigo"] == "listener_legado_incompativel"

    # Nada deve ter sido ingerido no SQLite local
    with closing(sqlite3.connect(tmp_path / "recusa.sqlite")) as conn:
        assert conn.execute("SELECT COUNT(*) FROM pendencias_v1").fetchone()[0] == 0

    # Também recusa ACK legado sem 'scoped': True
    resultado_ack = fila_escopada._post_ack_escopado(["999"])
    assert resultado_ack["ok"] is False
    assert resultado_ack["codigo"] == "listener_legado_incompativel"
    assert "999" in resultado_ack["rejected"]


def test_paginacao_avanca_cursor_mesmo_com_item_recusado_ou_ignorado(tmp_path: Path):
    """Cenário 7: Cursor avança pelo ID da mensagem mesmo quando o item é filtrado."""
    sim = ListenerSimulado(modo_escopado=True)

    # Item 1: conversa 8 (ignorada)
    sim.adicionar_evento(message_id=1, inbox_id=1, conversation_id=8)
    # Item 2: grupo @g.us (ignorado)
    sim.adicionar_evento(message_id=2, inbox_id=1, conversation_id=10, contato_ref="123@g.us")
    # Item 3: válido
    sim.adicionar_evento(message_id=3, inbox_id=1, conversation_id=10, contato_ref="ct-ok")

    fila = FilaIngestaoListener(
        tmp_path / "cursor_avanco.sqlite",
        conta_id="2",
        inbox_id="1",
        conversas_ignoradas=frozenset({"8"}),
        chamar_listener=sim.chamar,
        protocolo_escopado=True,
        limite_pagina=2,  # Página com tamanho 2 para forçar corte nos ignorados
    )

    res = fila.sincronizar()
    assert res["ok"] is True
    # Dos 3 itens, 1 inserido e 2 filtrados
    assert res["inseridos"] == 1
    assert res["filtrados"] == 2

    # Verifica que o item 3 foi recebido mesmo estando na segunda página
    itens = fila.listar_pendentes()
    assert len(itens) == 1
    assert itens[0]["message_id"] == "3"


def test_listener_versionado_funcoes_diretas(tmp_path: Path):
    """Cenário 8: Validação direta das funções no integracoes/ana_listener/listener.py."""
    # Importação do listener versionado
    import importlib.util
    listener_path = Path(__file__).resolve().parent.parent / "integracoes" / "ana_listener" / "listener.py"
    spec = importlib.util.spec_from_file_location("ana_listener_versionado", listener_path)
    assert spec is not None and spec.loader is not None
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    assert modulo.VERSION == "0.7.0"

    # Configura banco temporário para o listener
    db_file = tmp_path / "listener_test.db"
    modulo.DB_PATH = str(db_file)
    conn = modulo.db()

    # Insere 25 eventos no inbox 1 e 5 no inbox 2
    for i in range(1, 26):
        modulo.registrar(message_id=100 + i, conversation_id=1, inbox_id=1, contato_ref="c1")
    for i in range(1, 6):
        modulo.registrar(message_id=200 + i, conversation_id=2, inbox_id=2, contato_ref="c2")

    # 1. Teste de listar_pendentes com filtro escopado antes do limite
    itens_inbox2 = modulo.listar_pendentes(limite=10, inbox_id=2, after_message_id=0)
    assert len(itens_inbox2) == 5
    assert all(it["inbox_id"] == 2 for it in itens_inbox2)

    # 2. Teste de keyset pagination no inbox 1
    p1 = modulo.listar_pendentes(limite=10, inbox_id=1, after_message_id=0)
    assert len(p1) == 10
    assert p1[0]["message_id"] == 101
    assert p1[-1]["message_id"] == 110

    p2 = modulo.listar_pendentes(limite=10, inbox_id=1, after_message_id=110)
    assert len(p2) == 10
    assert p2[0]["message_id"] == 111
    assert p2[-1]["message_id"] == 120

    # 3. Teste de marcar_entregues escopado
    # Tenta marcar 101 e 201 informando inbox_id=1:
    marcados, accepted = modulo.marcar_entregues([101, 201], inbox_id=1)
    assert marcados == 1
    assert accepted == [101]
    # 201 pertence ao inbox 2, portanto NÃO foi aceito

    # Verifica estados no banco
    ev101 = conn.execute("SELECT estado FROM events WHERE message_id=101").fetchone()[0]
    ev201 = conn.execute("SELECT estado FROM events WHERE message_id=201").fetchone()[0]
    assert ev101 == "entregue"
    assert ev201 == "pendente"

    conn.close()


def _carregar_listener(tmp_path: Path):
    import importlib.util

    listener_path = (
        Path(__file__).resolve().parent.parent
        / "integracoes" / "ana_listener" / "listener.py"
    )
    spec = importlib.util.spec_from_file_location("ana_listener_regressao", listener_path)
    assert spec is not None and spec.loader is not None
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    modulo.DB_PATH = str(tmp_path / "listener-regressao.db")
    return modulo


def _criar_base_061(caminho: Path) -> None:
    with closing(sqlite3.connect(caminho)) as conn, conn:
        conn.executescript("""
            CREATE TABLE events(
                message_id INTEGER UNIQUE, conversation_id INTEGER,
                inbox_id INTEGER, contato_ref TEXT, handoff TEXT,
                recebido_em TEXT, estado TEXT DEFAULT 'pendente'
                CHECK (estado IN ('pendente','entregue','ignorado'))
            );
            CREATE TABLE cumprimentos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER, message_id INTEGER UNIQUE,
                texto TEXT, variante INTEGER, enviado_em TEXT
            );
        """)


def _snapshot_listener(caminho: Path) -> dict:
    with closing(sqlite3.connect(caminho)) as conn:
        return {
            "schema": conn.execute(
                "SELECT name, sql FROM sqlite_master WHERE type='table'"
                " AND name IN ('events', 'cumprimentos') ORDER BY name"
            ).fetchall(),
            "events": conn.execute("SELECT * FROM events ORDER BY rowid").fetchall(),
            "cumprimentos": conn.execute(
                "SELECT * FROM cumprimentos ORDER BY rowid"
            ).fetchall(),
        }


def test_listener_mesmo_id_em_dois_inboxes_e_ack_legado_ambiguo(tmp_path: Path):
    modulo = _carregar_listener(tmp_path)
    assert modulo.registrar(77, 11, 1, "ref-a")
    assert modulo.registrar(77, 22, 2, "ref-b")
    assert not modulo.registrar(77, 33, 1, "ref-duplicada")

    # Sem inbox, um ID ambíguo não pode atualizar nenhuma das duas linhas.
    assert modulo.marcar_entregues([77]) == 0
    assert len(modulo.listar_pendentes(inbox_id=1)) == 1
    assert len(modulo.listar_pendentes(inbox_id=2)) == 1

    assert modulo.marcar_entregues([77], inbox_id=1) == (1, [77])
    # Resposta perdida: repetir o mesmo ACK é aceito sem nova transição.
    assert modulo.marcar_entregues([77], inbox_id=1) == (0, [77])
    assert modulo.listar_pendentes(inbox_id=1) == []
    assert len(modulo.listar_pendentes(inbox_id=2)) == 1

    modulo.atualizar(77, inbox_id=2, handoff="fila-humana")
    with closing(sqlite3.connect(modulo.DB_PATH)) as conn:
        assert conn.execute(
            "SELECT handoff FROM events WHERE message_id=77 AND inbox_id=1"
        ).fetchone()[0] is None
        assert conn.execute(
            "SELECT handoff FROM events WHERE message_id=77 AND inbox_id=2"
        ).fetchone()[0] == "fila-humana"


def test_listener_migra_base_real_061_preservando_tudo(tmp_path: Path):
    banco = tmp_path / "listener-regressao.db"
    _criar_base_061(banco)
    eventos = [
        (101, 11, 1, "ref-a", "bot", "2026-01-01T00:00:00+00:00", "pendente"),
        (202, 22, 2, "ref-b", None, "2026-01-01T00:01:00+00:00", "entregue"),
        (303, 33, 1, "ref-c", None, "2026-01-01T00:02:00+00:00", "ignorado"),
    ]
    with closing(sqlite3.connect(banco)) as conn, conn:
        conn.executemany("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)", eventos)
        conn.executemany(
            "INSERT INTO cumprimentos VALUES (?, ?, ?, ?, ?, ?)",
            [
                (7, 11, 101, "cumprimento sintetico A", 2, "2026-01-01T00:00:10+00:00"),
                (9, 22, 202, "cumprimento sintetico B", 1, "2026-01-01T00:01:10+00:00"),
            ],
        )

    modulo = _carregar_listener(tmp_path)
    with modulo.db() as conn:
        assert conn.execute(
            "SELECT message_id, conversation_id, inbox_id, contato_ref, handoff,"
            " recebido_em, estado FROM events ORDER BY message_id"
        ).fetchall() == eventos
        assert conn.execute(
            "SELECT id, conversation_id, message_id, texto, variante, enviado_em, inbox_id"
            " FROM cumprimentos ORDER BY id"
        ).fetchall() == [
            (7, 11, 101, "cumprimento sintetico A", 2, "2026-01-01T00:00:10+00:00", 1),
            (9, 22, 202, "cumprimento sintetico B", 1, "2026-01-01T00:01:10+00:00", 2),
        ]

    assert modulo.cumprimento_de(101, inbox_id=1)["texto"] == "cumprimento sintetico A"
    assert modulo.cumprimento_de(202, inbox_id=2)["texto"] == "cumprimento sintetico B"
    # O mesmo ID antigo pode passar a existir no outro inbox sem apagar o cumprimento.
    assert modulo.registrar(101, 44, 2, "ref-d")
    assert modulo.cumprimento_de(101, inbox_id=2) is None
    modulo.registrar_cumprimento(
        44, 101, "cumprimento sintetico C", 0, "2026-01-01T00:03:00+00:00", inbox_id=2,
    )
    assert modulo.cumprimento_de(101, inbox_id=1)["texto"] == "cumprimento sintetico A"
    assert modulo.cumprimento_de(101, inbox_id=2)["texto"] == "cumprimento sintetico C"


def test_listener_migracao_orfao_faz_rollback_sem_reescrever(tmp_path: Path):
    banco = tmp_path / "listener-regressao.db"
    _criar_base_061(banco)
    with closing(sqlite3.connect(banco)) as conn, conn:
        conn.execute("INSERT INTO events VALUES (1, 11, 1, 'ref', NULL, 'ts', 'pendente')")
        conn.execute(
            "INSERT INTO cumprimentos VALUES (5, 99, 999, 'orfao sintetico', 0, 'ts')"
        )
    antes = _snapshot_listener(banco)
    modulo = _carregar_listener(tmp_path)

    with pytest.raises(RuntimeError, match="cumprimento_inbox_indeterminado"):
        modulo.db()
    assert _snapshot_listener(banco) == antes


def test_listener_migracao_atribuicao_ambigua_faz_rollback(tmp_path: Path):
    banco = tmp_path / "listener-regressao.db"
    _criar_base_061(banco)
    with closing(sqlite3.connect(banco)) as conn, conn:
        conn.executescript("""
            DROP TABLE events;
            CREATE TABLE events(
                message_id INTEGER, conversation_id INTEGER,
                inbox_id INTEGER, contato_ref TEXT, handoff TEXT,
                recebido_em TEXT, estado TEXT DEFAULT 'pendente'
                CHECK (estado IN ('pendente','entregue','ignorado')),
                UNIQUE(inbox_id, message_id)
            );
        """)
        conn.executemany(
            "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (77, 11, 1, "ref-a", None, "ts-a", "pendente"),
                (77, 22, 2, "ref-b", None, "ts-b", "pendente"),
            ],
        )
        conn.execute(
            "INSERT INTO cumprimentos VALUES (5, 11, 77, 'ambiguidade sintetica', 0, 'ts')"
        )
    antes = _snapshot_listener(banco)
    modulo = _carregar_listener(tmp_path)

    with pytest.raises(RuntimeError, match="cumprimento_inbox_indeterminado"):
        modulo.db()
    assert _snapshot_listener(banco) == antes


def test_paginacao_continua_apos_teto_e_retoma_depois_de_falha(tmp_path: Path):
    sim = ListenerSimulado(modo_escopado=True)
    for mid in range(1, 102):
        sim.adicionar_evento(message_id=mid, inbox_id=1, conversation_id=10)
    fila = FilaIngestaoListener(
        tmp_path / "continuacao.sqlite", conta_id="2", inbox_id="1",
        chamar_listener=sim.chamar, protocolo_escopado=True, limite_pagina=2,
    )

    truncada = fila.sincronizar()
    assert truncada["ok"] is False
    assert truncada["codigo"] == "paginacao_incompleta"
    assert truncada["inseridos"] == 100
    assert fila._fila.obter("101") is None

    gets = [c for c in sim.historico_chamadas if c[0] == "GET"]
    sim.falhar_get = True
    falha = fila.sincronizar()
    assert falha["codigo"] == "listener_indisponivel"
    sim.falhar_get = False
    concluida = fila.sincronizar()
    assert concluida["ok"] is True
    assert concluida["inseridos"] == 1
    assert fila._fila.obter("101") is not None

    novas = [c for c in sim.historico_chamadas if c[0] == "GET"][len(gets):]
    assert "after_message_id=100" in novas[0][1]
    assert "after_message_id=100" in novas[1][1]

    for evento in sim.eventos:
        evento["estado"] = "entregue"
    antes = len([c for c in sim.historico_chamadas if c[0] == "GET"])
    assert fila.sincronizar()["ok"] is True
    reinicio = [c for c in sim.historico_chamadas if c[0] == "GET"][antes]
    assert "after_message_id=0" in reinicio[1]


@pytest.mark.parametrize("modo,codigo", [
    ("excecao", "listener_indisponivel"),
    ("http", "listener_indisponivel"),
    ("json", "resposta_invalida"),
    ("pending", "resposta_invalida"),
])
def test_pending_escopado_classifica_erro(tmp_path: Path, modo: str, codigo: str):
    def transporte(_metodo, _caminho, _corpo):
        if modo == "excecao":
            raise TimeoutError("falha sintetica")
        if modo == "http":
            return 500, b"{}"
        if modo == "json":
            return 200, b"{"
        return 200, json.dumps({
            "ok": True, "scoped": True, "inbox_id": 1, "pending": {},
        }).encode()

    fila = FilaIngestaoListener(
        tmp_path / "erros.sqlite", conta_id="2", inbox_id="1",
        chamar_listener=transporte, protocolo_escopado=True,
    )
    resultado = fila.sincronizar()
    assert resultado["ok"] is False
    assert resultado["codigo"] == codigo


@pytest.mark.parametrize("inbox_resposta", [None, "1", True, 2])
def test_pending_escopado_exige_inbox_inteiro_exato(tmp_path: Path, inbox_resposta):
    sim = ListenerSimulado(modo_escopado=True)
    sim.adicionar_evento(message_id=10, inbox_id=1)

    def transporte(metodo, caminho, corpo):
        status, body = sim.chamar(metodo, caminho, corpo)
        if metodo == "GET":
            dados = json.loads(body)
            if inbox_resposta is None:
                dados.pop("inbox_id", None)
            else:
                dados["inbox_id"] = inbox_resposta
            body = json.dumps(dados).encode()
        return status, body

    fila = FilaIngestaoListener(
        tmp_path / "envelope.sqlite", conta_id="2", inbox_id="1",
        chamar_listener=transporte, protocolo_escopado=True,
    )
    assert fila.sincronizar()["codigo"] == "resposta_invalida"
    assert fila._fila.listar_pendentes() == []


@pytest.mark.parametrize("inbox_resposta", [None, "1", True, 2])
def test_ack_escopado_exige_inbox_inteiro_exato(tmp_path: Path, inbox_resposta):
    sim = ListenerSimulado(modo_escopado=True)
    sim.adicionar_evento(message_id=10, inbox_id=1)

    def transporte(metodo, caminho, corpo):
        status, body = sim.chamar(metodo, caminho, corpo)
        if metodo == "POST":
            dados = json.loads(body)
            if inbox_resposta is None:
                dados.pop("inbox_id", None)
            else:
                dados["inbox_id"] = inbox_resposta
            body = json.dumps(dados).encode()
        return status, body

    fila = FilaIngestaoListener(
        tmp_path / "ack-envelope.sqlite", conta_id="2", inbox_id="1",
        chamar_listener=transporte, protocolo_escopado=True,
    )
    assert fila.sincronizar()["inseridos"] == 1
    assert fila.marcar_entregues(["10"]) == []
    assert fila._contar_acks_pendentes() == 1
    assert fila._fila.obter("10")["estado"] == "pendente"


def test_ack_escopado_idempotente_depois_de_resposta_perdida(tmp_path: Path):
    sim = ListenerSimulado(modo_escopado=True)
    sim.adicionar_evento(message_id=10, inbox_id=1)
    perder = [True]

    def transporte(metodo, caminho, corpo):
        status, body = sim.chamar(metodo, caminho, corpo)
        if metodo == "POST" and perder[0]:
            perder[0] = False
            raise TimeoutError("resposta sintetica perdida")
        return status, body

    fila = FilaIngestaoListener(
        tmp_path / "ack-perdido.sqlite", conta_id="2", inbox_id="1",
        chamar_listener=transporte, protocolo_escopado=True,
    )
    fila.sincronizar()
    assert fila.marcar_entregues(["10"]) == []
    assert fila._contar_acks_pendentes() == 1
    assert fila._fila.obter("10")["estado"] == "pendente"

    assert fila.marcar_entregues(["10"]) == ["10"]
    assert fila._contar_acks_pendentes() == 0
    assert fila._fila.obter("10")["estado"] == "entregue"
    assert len(sim.acks_recebidos) == 2


def test_adaptador_ack_falho_reconcilia_sem_reenviar(tmp_path: Path):
    from tuttibom.mcp_ops.atendimento import (
        AdaptadorAtendimento,
        ChatwootLaboratorio,
        SimuladorAtendimento,
        VerificadorAprovacaoServidor,
    )
    from tuttibom.mcp_ops.entregas_duraveis import DiarioEntregas

    sim = ListenerSimulado(modo_escopado=True)
    sim.adicionar_evento(message_id=100, inbox_id=1, conversation_id=5)
    fila = FilaIngestaoListener(
        tmp_path / "fila.sqlite", conta_id="2", inbox_id="1",
        chamar_listener=sim.chamar, protocolo_escopado=True,
    )
    fila.sincronizar()
    chat = ChatwootLaboratorio()
    chat.registrar_mensagem("5", direcao="incoming", texto="entrada sintetica")
    destino = SimuladorAtendimento()
    aprovador = VerificadorAprovacaoServidor()
    diario = DiarioEntregas(tmp_path / "diario.sqlite")
    ops = AdaptadorAtendimento(
        fila=fila, chatwoot=chat, simulador=destino, transcritor=None,
        verificador=aprovador, diario=diario,
    )
    assert ops.ler_conversa("5")["ok"]
    rascunho = ops.preparar_resposta(
        conversa_ref="5", texto="resposta sintetica", idempotency_key="chave-sintetica",
        message_ids=["100"],
    )
    aprovacao = aprovador.registrar(texto="resposta sintetica")

    sim.falhar_post_ack = True
    envio = ops.responder(rascunho_ref=rascunho["rascunho_ref"], aprovacao_ref=aprovacao)
    assert envio["enviado"] is True
    assert envio["codigo"] == "ack_falhou"
    assert fila._fila.obter("100")["estado"] == "pendente"
    assert diario.listar_acoes_pendentes()[0]["acao"] == "somente_ack"
    assert len(destino.envios) == 1

    sim.falhar_post_ack = False
    reconciliado = ops.reconciliar_acks()
    assert reconciliado["ok"] is True
    assert reconciliado["resultados"][0]["acked"] == ["100"]
    assert fila._fila.obter("100")["estado"] == "entregue"
    assert diario.consultar_mensagem("100")["estado"] == "concluido"
    assert diario.consultar_mensagem("100")["ack_em"] is not None
    assert len(destino.envios) == 1
