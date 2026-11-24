"""Testes abrangentes para FilaIngestaoListener.

Cobertura:
- Ingestão do inbox 1, descarte de inbox 2 (Messenger)
- Descarte de @g.us (grupos WhatsApp)
- Descarte de conversa ignorada
- Remoção total de contato_ref/telefone (nenhum PII na resposta nem no SQLite)
- Preservação de handoff seguro e rejeição de handoff com PII
- Resiliência quando /pending cai
- Retry durável de /ack quando o listener falha no primeiro ACK e volta depois
- Deduplicação após ACK
- Integração com AdaptadorAtendimento + DiarioEntregas
"""

from __future__ import annotations

import importlib
import json
import sqlite3
import sys
import types
from collections.abc import Mapping, Sequence
from contextlib import closing
from pathlib import Path

import pytest

from tuttibom.contratos.pii import detectar_pii
from tuttibom.mcp_ops.fila_persistente import FilaPersistente
from tuttibom.mcp_ops.ingestao_listener import FilaIngestaoListener


# ── Helpers ─────────────────────────────────────────────────────────

class ListenerFake:
    """Simula o ana-listener via transporte injetável."""

    def __init__(self) -> None:
        self.pending: list[dict] = []
        self.acks: list[list[int]] = []
        self._falha = False
        self._ack_falha = False

    def falhar(self, v: bool = True) -> None:
        self._falha = v

    def falhar_ack(self, v: bool = True) -> None:
        self._ack_falha = v

    def chamar(
        self, metodo: str, caminho: str, corpo: bytes | None
    ) -> tuple[int, bytes]:
        if self._falha:
            raise ConnectionRefusedError("listener fora do ar")
        if metodo == "GET" and caminho == "/pending":
            return 200, json.dumps({"pending": self.pending}).encode()
        if metodo == "POST" and caminho == "/ack":
            if self._ack_falha:
                return 500, b'{"ok": false}'
            dados = json.loads(corpo or b"{}")
            self.acks.append(dados.get("message_ids", []))
            return 200, json.dumps({"ok": True}).encode()
        return 404, b"not found"


def _criar(tmp_path: Path, **kw) -> tuple[FilaIngestaoListener, ListenerFake]:
    db = tmp_path / "fila.db"
    listener = ListenerFake()
    defaults = dict(
        caminho_sqlite=db,
        conta_id="1",
        inbox_id="1",
        conversas_ignoradas=frozenset({"8"}),
        chamar_listener=listener.chamar,
    )
    defaults.update(kw)
    return FilaIngestaoListener(**defaults), listener


def _item(
    *,
    inbox_id=1,
    message_id=100,
    conversation_id=5,
    contato_ref="5500999990014@s.whatsapp.net",
    handoff=None,
):
    item = {
        "inbox_id": inbox_id,
        "message_id": message_id,
        "conversation_id": conversation_id,
        "contato_ref": contato_ref,
    }
    if handoff is not None:
        item["handoff"] = handoff
    return item


# ── Validação do construtor ─────────────────────────────────────────

class TestConstrutor:
    def test_conta_id_invalida(self, tmp_path):
        with pytest.raises(ValueError, match="conta_id_invalida"):
            FilaIngestaoListener(
                tmp_path / "fila.db",
                conta_id="abc",
                inbox_id="1",
                chamar_listener=lambda *a: (200, b""),
            )

    def test_inbox_id_invalido(self, tmp_path):
        with pytest.raises(ValueError, match="inbox_id_invalido"):
            FilaIngestaoListener(
                tmp_path / "fila.db",
                conta_id="1",
                inbox_id="0",
                chamar_listener=lambda *a: (200, b""),
            )

    def test_porta_invalida(self, tmp_path):
        with pytest.raises(ValueError, match="porta_invalida"):
            FilaIngestaoListener(
                tmp_path / "fila.db",
                conta_id="1",
                inbox_id="1",
                porta_listener=0,
                chamar_listener=lambda *a: (200, b""),
            )

    def test_porta_bool_rejeitada(self, tmp_path):
        with pytest.raises(ValueError, match="porta_invalida"):
            FilaIngestaoListener(
                tmp_path / "fila.db",
                conta_id="1",
                inbox_id="1",
                porta_listener=True,
                chamar_listener=lambda *a: (200, b""),
            )

    def test_caminho_relativo(self, tmp_path):
        with pytest.raises(ValueError, match="caminho_sqlite_invalido"):
            FilaIngestaoListener(
                Path("relativo.db"),
                conta_id="1",
                inbox_id="1",
                chamar_listener=lambda *a: (200, b""),
            )

    def test_construtor_valido(self, tmp_path):
        fil, _ = _criar(tmp_path)
        assert fil.conta_id == "1"
        assert fil.inbox_id == "1"


# ── Ingestão inbox 1, descarte inbox 2 ─────────────────────────────

class TestIngestaoFiltros:
    def test_inbox_1_aceito_inbox_2_descartado(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5),
            _item(inbox_id=2, message_id=200, conversation_id=6),  # Messenger
        ]
        r = fil.sincronizar()
        assert r["ok"] is True
        assert r["inseridos"] == 1
        assert r["filtrados"] == 1

        pendentes = fil.listar_pendentes()
        assert len(pendentes) == 1
        assert pendentes[0]["message_id"] == "100"

    def test_descarte_grupo_whatsapp(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(
                inbox_id=1,
                message_id=300,
                conversation_id=9,
                contato_ref="5588999990015-1234567890@g.us",
            ),
        ]
        r = fil.sincronizar()
        assert r["ok"] is True
        assert r["filtrados"] == 1
        assert r["inseridos"] == 0

    def test_descarte_grupo_whatsapp_case_insensitive(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(
                inbox_id=1,
                message_id=301,
                conversation_id=9,
                contato_ref="grupo@G.US",
            ),
        ]
        r = fil.sincronizar()
        assert r["filtrados"] == 1
        assert r["inseridos"] == 0

    def test_descarte_conversa_ignorada(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id=400, conversation_id=8),  # ignorada
        ]
        r = fil.sincronizar()
        assert r["filtrados"] == 1
        assert r["inseridos"] == 0

    def test_message_id_invalido_descartado(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            {
                "inbox_id": 1,
                "message_id": -1,
                "conversation_id": 5,
                "contato_ref": "x@s.whatsapp.net",
            },
            {
                "inbox_id": 1,
                "message_id": 0,
                "conversation_id": 5,
                "contato_ref": "x@s.whatsapp.net",
            },
            {
                "inbox_id": 1,
                "message_id": "abc",
                "conversation_id": 5,
                "contato_ref": "x@s.whatsapp.net",
            },
        ]
        r = fil.sincronizar()
        assert r["filtrados"] == 3
        assert r["inseridos"] == 0

    def test_conversation_id_invalido_descartado(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            {
                "inbox_id": 1,
                "message_id": 500,
                "conversation_id": "abc",
                "contato_ref": "x@s.whatsapp.net",
            },
        ]
        r = fil.sincronizar()
        assert r["filtrados"] == 1

    def test_item_nao_mapping_descartado(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = ["lixo", 42, None]
        r = fil.sincronizar()
        assert r["filtrados"] == 3

    def test_mid_string_numerica_aceita(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id="999", conversation_id=5),
        ]
        r = fil.sincronizar()
        assert r["inseridos"] == 1


# ── Remoção total de PII ────────────────────────────────────────────

class TestPII:
    def test_contato_ref_nunca_na_resposta(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(
                inbox_id=1,
                message_id=100,
                conversation_id=5,
                contato_ref="5588999990015@s.whatsapp.net",
            ),
        ]
        fil.sincronizar()
        pendentes = fil.listar_pendentes()
        for p in pendentes:
            assert "contato_ref" not in p
            for v in p.values():
                if isinstance(v, str):
                    assert "5588999990015" not in v

    def test_contato_ref_nunca_no_sqlite(self, tmp_path):
        db = tmp_path / "fila.db"
        fil, listener = _criar(tmp_path, caminho_sqlite=db)
        listener.pending = [
            _item(
                inbox_id=1,
                message_id=100,
                conversation_id=5,
                contato_ref="5588999990015@s.whatsapp.net",
            ),
        ]
        fil.sincronizar()

        # Verificar todas as tabelas do SQLite
        with closing(sqlite3.connect(db)) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tabelas = [row[0] for row in cursor]
            for tabela in tabelas:
                cursor = conn.execute(f"SELECT * FROM {tabela}")
                colunas = [desc[0] for desc in cursor.description]
                assert "contato_ref" not in colunas, (
                    f"contato_ref encontrado na tabela {tabela}"
                )
                for row in cursor:
                    for valor in row:
                        if isinstance(valor, str):
                            assert "5588999990015" not in valor, (
                                f"telefone encontrado em {tabela}: {valor}"
                            )

    def test_obter_nunca_tem_contato_ref(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(
                inbox_id=1,
                message_id=100,
                conversation_id=5,
                contato_ref="5588999990015@s.whatsapp.net",
            ),
        ]
        fil.sincronizar()
        item = fil.obter("100")
        assert item is not None
        assert "contato_ref" not in item


# ── Handoff ─────────────────────────────────────────────────────────

class TestHandoff:
    def test_handoff_seguro_preservado(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5, handoff="bot-v2"),
        ]
        fil.sincronizar()
        pendentes = fil.listar_pendentes()
        assert pendentes[0]["handoff"] == "bot-v2"

    def test_handoff_com_pii_rejeitado(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(
                inbox_id=1,
                message_id=100,
                conversation_id=5,
                handoff="fulano@example.com",
            ),
        ]
        fil.sincronizar()
        pendentes = fil.listar_pendentes()
        assert pendentes[0]["handoff"] is None

    def test_handoff_texto_livre_rejeitado(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(
                inbox_id=1,
                message_id=100,
                conversation_id=5,
                handoff="Olá, preciso de ajuda com meu pedido número 12345",
            ),
        ]
        fil.sincronizar()
        pendentes = fil.listar_pendentes()
        assert pendentes[0]["handoff"] is None

    def test_handoff_nao_string_rejeitado(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5, handoff=42),
        ]
        # handoff do _item vai com 42 como int dentro do dict
        listener.pending[0]["handoff"] = 42
        fil.sincronizar()
        pendentes = fil.listar_pendentes()
        assert pendentes[0]["handoff"] is None

    def test_handoff_none_quando_ausente(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5),
        ]
        fil.sincronizar()
        pendentes = fil.listar_pendentes()
        assert pendentes[0]["handoff"] is None

    def test_handoff_em_obter(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5, handoff="agente-x"),
        ]
        fil.sincronizar()
        item = fil.obter("100")
        assert item is not None
        assert item["handoff"] == "agente-x"


# ── Resiliência quando /pending cai ─────────────────────────────────

class TestResiliencia:
    def test_listener_fora_do_ar(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.falhar(True)
        r = fil.sincronizar()
        assert r["ok"] is False
        assert r["codigo"] == "listener_indisponivel"
        assert "acks_pendentes" in r

    def test_listar_pendentes_com_listener_fora(self, tmp_path):
        fil, listener = _criar(tmp_path)
        # Primeiro carrega dados
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5),
        ]
        fil.sincronizar()

        # Agora o listener cai
        listener.falhar(True)

        # Ainda devolve os itens já persistidos em SQLite
        pendentes = fil.listar_pendentes()
        assert len(pendentes) == 1
        assert pendentes[0]["message_id"] == "100"

    def test_obter_com_sync_fallback(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5),
        ]
        # obter sincroniza automaticamente se não achar na primeira vez
        item = fil.obter("100")
        assert item is not None
        assert item["message_id"] == "100"

    def test_obter_nao_existente(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = []
        item = fil.obter("999")
        assert item is None

    def test_pending_resposta_invalida(self, tmp_path):
        def transporte(metodo, caminho, corpo):
            if caminho == "/pending":
                return 200, b'{"pending": "nao_e_lista"}'
            return 200, b'{"ok": true}'

        db = tmp_path / "fila.db"
        fil = FilaIngestaoListener(
            db,
            conta_id="1",
            inbox_id="1",
            chamar_listener=transporte,
        )
        r = fil.sincronizar()
        assert r["ok"] is False
        assert r["codigo"] == "listener_indisponivel"


# ── ACK retry durável ───────────────────────────────────────────────

class TestACKRetry:
    def test_ack_falha_e_retry(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5),
        ]
        fil.sincronizar()

        # ACK falha no listener: o item local continua pendente.
        listener.falhar_ack(True)
        marcados = fil.marcar_entregues(["100"])
        assert marcados == []
        assert fil.obter("100")["estado"] == "pendente"

        # Ainda pendente no acks_listener_pendentes_v1
        assert fil._contar_acks_pendentes() > 0

        # Listener volta; a descarga também conclui o estado local.
        listener.falhar_ack(False)
        fil.sincronizar()  # _descarregar_acks é chamado no começo

        assert fil._contar_acks_pendentes() == 0
        assert fil.obter("100")["estado"] == "entregue"
        assert len(listener.acks) == 1
        assert 100 in listener.acks[0]

    def test_ack_ok_no_primeiro_try(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5),
        ]
        fil.sincronizar()

        marcados = fil.marcar_entregues(["100"])
        assert marcados == ["100"]

        # ACK já foi descarregado imediatamente
        assert fil._contar_acks_pendentes() == 0
        assert len(listener.acks) == 1

    def test_marcar_entregues_valida_ids(self, tmp_path):
        fil, listener = _criar(tmp_path)
        with pytest.raises(ValueError, match="message_id_invalido"):
            fil.marcar_entregues(["abc"])

    def test_marcar_entregues_id_inexistente(self, tmp_path):
        """IDs que não existem na fila: não gravar em acks nem marcar."""
        fil, listener = _criar(tmp_path)
        listener.pending = []
        fil.sincronizar()
        marcados = fil.marcar_entregues(["999"])
        assert marcados == []


# ── Deduplicação ────────────────────────────────────────────────────

class TestDeduplicacao:
    def test_dedup_apos_ack(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5),
        ]
        fil.sincronizar()
        fil.marcar_entregues(["100"])

        # /pending ainda devolve a mensagem (listener não flushou)
        r = fil.sincronizar()
        assert r["existentes"] == 1
        assert r["inseridos"] == 0

    def test_dedup_sem_duplicar_no_sqlite(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5),
        ]
        fil.sincronizar()
        fil.sincronizar()
        pendentes = fil.listar_pendentes()
        assert len(pendentes) == 1


# ── listar_pendentes validação de limite ────────────────────────────

class TestLimite:
    def test_limite_zero(self, tmp_path):
        fil, _ = _criar(tmp_path)
        with pytest.raises(ValueError, match="limite_invalido"):
            fil.listar_pendentes(0)

    def test_limite_101(self, tmp_path):
        fil, _ = _criar(tmp_path)
        with pytest.raises(ValueError, match="limite_invalido"):
            fil.listar_pendentes(101)

    def test_limite_bool(self, tmp_path):
        fil, _ = _criar(tmp_path)
        with pytest.raises(ValueError, match="limite_invalido"):
            fil.listar_pendentes(True)


# ── Formato de saída ────────────────────────────────────────────────

class TestFormato:
    def test_campos_exatos_listar(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5, handoff="bot"),
        ]
        fil.sincronizar()
        pendentes = fil.listar_pendentes()
        assert len(pendentes) == 1
        item = pendentes[0]
        assert set(item.keys()) == {
            "inbox_id",
            "message_id",
            "conversation_id",
            "recebido_em",
            "handoff",
        }
        assert item["inbox_id"] == "1"
        assert item["message_id"] == "100"
        assert item["conversation_id"] == "5"
        assert item["handoff"] == "bot"
        assert isinstance(item["recebido_em"], str)

    def test_campos_exatos_obter(self, tmp_path):
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5),
        ]
        fil.sincronizar()
        item = fil.obter("100")
        assert item is not None
        assert set(item.keys()) == {
            "inbox_id",
            "message_id",
            "conversation_id",
            "recebido_em",
            "handoff",
            "estado",
        }
        assert item["estado"] == "pendente"


# ── Integração com AdaptadorAtendimento + DiarioEntregas ────────────

class TestIntegracao:
    def test_adaptador_usa_fila_listener(self, tmp_path):
        """FilaIngestaoListener satisfaz o protocolo FilaPendencias do adaptador."""
        _atendimento = importlib.import_module("tuttibom.mcp_ops.atendimento")
        AdaptadorAtendimento = _atendimento.AdaptadorAtendimento
        AuditoriaLaboratorio = _atendimento.AuditoriaLaboratorio
        ChatwootLaboratorio = _atendimento.ChatwootLaboratorio
        SimuladorAtendimento = _atendimento.SimuladorAtendimento
        VerificadorAprovacaoServidor = _atendimento.VerificadorAprovacaoServidor

        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5, handoff="bot-v2"),
        ]

        chatwoot = ChatwootLaboratorio()
        simulador = SimuladorAtendimento()
        verificador = VerificadorAprovacaoServidor()
        auditoria = AuditoriaLaboratorio()

        adaptador = AdaptadorAtendimento(
            fila=fil,
            chatwoot=chatwoot,
            simulador=simulador,
            transcritor=None,
            verificador=verificador,
            auditoria=auditoria,
        )

        resultado = adaptador.listar_pendencias()
        assert resultado["ok"] is True
        assert len(resultado["pendencias"]) == 1
        item = resultado["pendencias"][0]
        assert item["message_id"] == "100"
        assert item["inbox_id"] == "1"
        assert item["handoff"] == "bot-v2"
        # Nunca deve ter contato_ref
        assert "contato_ref" not in item

    def test_adaptador_com_diario(self, tmp_path):
        """Integração com DiarioEntregas: fluxo completo de envio."""
        _atendimento = importlib.import_module("tuttibom.mcp_ops.atendimento")
        AdaptadorAtendimento = _atendimento.AdaptadorAtendimento
        AuditoriaLaboratorio = _atendimento.AuditoriaLaboratorio
        ChatwootLaboratorio = _atendimento.ChatwootLaboratorio
        SimuladorAtendimento = _atendimento.SimuladorAtendimento
        VerificadorAprovacaoServidor = _atendimento.VerificadorAprovacaoServidor
        _entregas = importlib.import_module("tuttibom.mcp_ops.entregas_duraveis")
        DiarioEntregas = _entregas.DiarioEntregas

        db = tmp_path / "integracao.db"
        fil, listener = _criar(tmp_path, caminho_sqlite=db)
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5),
        ]
        fil.sincronizar()

        chatwoot = ChatwootLaboratorio()
        chatwoot.registrar_mensagem(
            "5",
            direcao="incoming",
            texto="Oi",
        )
        simulador = SimuladorAtendimento()
        verificador = VerificadorAprovacaoServidor()
        auditoria = AuditoriaLaboratorio()
        diario = DiarioEntregas(db)

        adaptador = AdaptadorAtendimento(
            fila=fil,
            chatwoot=chatwoot,
            simulador=simulador,
            transcritor=None,
            verificador=verificador,
            auditoria=auditoria,
            diario=diario,
        )

        # Listar pendências
        pendencias = adaptador.listar_pendencias()
        assert pendencias["ok"] is True
        assert len(pendencias["pendencias"]) == 1

        # Ler conversa
        leitura = adaptador.ler_conversa("5")
        assert leitura["ok"] is True

        # Preparar resposta
        ref_aprovacao = verificador.registrar(texto="Olá, tudo bem?")
        prep = adaptador.preparar_resposta(
            conversa_ref="5",
            texto="Olá, tudo bem?",
            idempotency_key="k-1",
            message_ids=["100"],
        )
        assert prep["ok"] is True

        # Responder (com diário)
        resp = adaptador.responder(
            rascunho_ref=prep["rascunho_ref"],
            aprovacao_ref=ref_aprovacao,
        )
        assert resp["enviado"] is True

    def test_marcar_e_ack_no_listener(self, tmp_path):
        """Verificar que marcar_entregues envia POST /ack ao listener."""
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5),
            _item(inbox_id=1, message_id=101, conversation_id=5),
        ]
        fil.sincronizar()

        marcados = fil.marcar_entregues(["100", "101"])
        assert set(marcados) == {"100", "101"}

        # Verificar que o ACK foi enviado ao listener
        assert len(listener.acks) == 1
        assert set(listener.acks[0]) == {100, 101}

    def test_contato_ref_com_telefone_real_nunca_vaza(self, tmp_path):
        """Teste extra: contato_ref com telefone real brasileiro."""
        fil, listener = _criar(tmp_path)
        listener.pending = [
            _item(
                inbox_id=1,
                message_id=100,
                conversation_id=5,
                contato_ref="+5588999990015",
            ),
        ]
        fil.sincronizar()

        # Nunca deve aparecer no resultado
        pendentes = fil.listar_pendentes()
        for p in pendentes:
            assert "contato_ref" not in p
            for v in p.values():
                if isinstance(v, str):
                    assert "5588999990015" not in v

        item = fil.obter("100")
        assert item is not None
        assert "contato_ref" not in item

    def test_multiplos_inbox_separados(self, tmp_path):
        """Dois FilaIngestaoListener com inbox_id diferente não cruzam."""
        db = tmp_path / "shared.db"
        listener1 = ListenerFake()
        listener2 = ListenerFake()

        fil1 = FilaIngestaoListener(
            db, conta_id="1", inbox_id="1", chamar_listener=listener1.chamar,
        )
        fil2 = FilaIngestaoListener(
            db, conta_id="1", inbox_id="2", chamar_listener=listener2.chamar,
        )

        listener1.pending = [
            _item(inbox_id=1, message_id=100, conversation_id=5),
        ]
        listener2.pending = [
            _item(inbox_id=2, message_id=200, conversation_id=6),
        ]

        r1 = fil1.sincronizar()
        r2 = fil2.sincronizar()

        assert r1["inseridos"] == 1
        assert r2["inseridos"] == 1

        p1 = fil1.listar_pendentes()
        p2 = fil2.listar_pendentes()

        assert len(p1) == 1
        assert p1[0]["message_id"] == "100"
        assert len(p2) == 1
        assert p2[0]["message_id"] == "200"
