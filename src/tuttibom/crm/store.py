"""Armazenamento do CRM próprio mínimo — SQLite, só stdlib.

Uso:
    from tuttibom.crm.store import CRM
    crm = CRM("/caminho/do/crm.sqlite3")   # cria o banco se não existir
    lead = crm.criar_lead(referencia="lead-teste-01", contato_ref="contato-teste-01",
                          canal="whatsapp", proxima_acao="Responder saudação",
                          data_followup="2026-11-22")

Regras aplicadas aqui (não no chamador):
- Preço só por SKU do catálogo (`PRECOS_SKU`); SKU desconhecido falha.
- Texto livre passa por `afirmar_sem_pii`: e-mail, CPF, telefone, CEP
  e endereço são rejeitados — o dado pessoal não entra no repo.
- "Não comprou" exige motivo de perda (código, não texto livre).
- Mensagem inbound cancela os follow-ups de silêncio pendentes.
- Memória por contato guarda só o rótulo do interesse.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from tuttibom.contratos.pii import afirmar_sem_pii
from tuttibom.contratos.precos import PRECOS_SKU

from .funil import (
    CANAIS,
    ETAPA_GANHOU,
    ETAPA_PERDEU,
    INTERESSES,
    MOTIVOS_PERDA,
    TIPOS_FOLLOWUP,
    transicao_permitida,
)

_REFERENCIA = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{1,39}$")


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_sku(sku: str) -> tuple[int, int, str]:
    """FITA-22-50-PRETO -> (22, 50, 'PRETO')."""
    _, largura, metragem, cor = sku.split("-")
    return int(largura), int(metragem), cor


class CRM:
    """Um banco SQLite, um CRM. O arquivo do banco NÃO vai para o git."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        schema = Path(__file__).resolve().parents[3] / "db" / "crm.sql"
        self.conn.executescript(schema.read_text(encoding="utf-8"))
        self._semear_produtos()
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # -- produtos ----------------------------------------------------

    def _semear_produtos(self) -> None:
        for sku, preco in PRECOS_SKU.items():
            largura, metragem, cor = _parse_sku(sku)
            self.conn.execute(
                "INSERT OR IGNORE INTO produtos"
                " (sku, tipo, largura_mm, metragem_m, cor_impressao, preco_centavos)"
                " VALUES (?, 'fita_cetim', ?, ?, ?, ?)",
                (sku, largura, metragem, cor, int(preco * 100)),
            )

    def produto_preco(self, sku: str) -> Decimal:
        """Preço do catálogo, em reais. SKU fora do catálogo falha."""
        row = self.conn.execute(
            "SELECT preco_centavos FROM produtos WHERE sku = ?", (sku,)
        ).fetchone()
        if row is None:
            raise ValueError(f"SKU fora do catálogo: {sku}")
        return Decimal(row["preco_centavos"]) / 100

    def contar_produtos(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]

    # -- leads -------------------------------------------------------

    def criar_lead(
        self,
        referencia: str,
        contato_ref: str,
        canal: str,
        proxima_acao: str,
        data_followup: str | None = None,
        interesse: str | None = None,
        produto_sku: str | None = None,
    ) -> dict:
        if not _REFERENCIA.match(referencia):
            raise ValueError(f"referência inválida: {referencia}")
        if not _REFERENCIA.match(contato_ref):
            raise ValueError(f"contato_ref inválido: {contato_ref}")
        if canal not in CANAIS:
            raise ValueError(f"canal inválido: {canal}")
        if interesse is not None and interesse not in INTERESSES:
            raise ValueError(f"interesse inválido: {interesse}")
        if produto_sku is not None:
            self.produto_preco(produto_sku)  # falha se fora do catálogo
        afirmar_sem_pii(proxima_acao, "proxima_acao")
        if len(proxima_acao.strip()) < 8:
            raise ValueError("proxima_acao curta demais (mín. 8 caracteres)")
        agora = _agora()
        cur = self.conn.execute(
            "INSERT INTO leads (referencia, contato_ref, canal, etapa,"
            " produto_sku, interesse, proxima_acao, data_followup,"
            " criado_em, atualizado_em)"
            " VALUES (?, ?, ?, 'Novo contato', ?, ?, ?, ?, ?, ?)",
            (
                referencia,
                contato_ref,
                canal,
                produto_sku,
                interesse,
                proxima_acao.strip(),
                data_followup,
                agora,
                agora,
            ),
        )
        self.conn.commit()
        return self.obter_lead(cur.lastrowid)

    def obter_lead(self, lead_id: int) -> dict:
        row = self.conn.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"lead inexistente: {lead_id}")
        return dict(row)

    def listar_leads_por_etapa(self, etapa: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM leads WHERE etapa = ? ORDER BY id", (etapa,)
        ).fetchall()
        return [dict(r) for r in rows]

    def mover_etapa(
        self,
        lead_id: int,
        nova_etapa: str,
        motivo_perda: str | None = None,
        proxima_acao: str | None = None,
        data_followup: str | None = None,
    ) -> dict:
        lead = self.obter_lead(lead_id)
        atual = lead["etapa"]
        if not transicao_permitida(atual, nova_etapa):
            raise ValueError(f"transição proibida: {atual} -> {nova_etapa}")
        if nova_etapa == ETAPA_PERDEU and motivo_perda not in MOTIVOS_PERDA:
            raise ValueError("Não comprou exige motivo de perda válido")
        if nova_etapa != ETAPA_PERDEU and motivo_perda is not None:
            raise ValueError("motivo de perda só no estágio Não comprou")
        if proxima_acao is not None:
            afirmar_sem_pii(proxima_acao, "proxima_acao")
        self.conn.execute(
            "UPDATE leads SET etapa = ?, motivo_perda = ?,"
            " proxima_acao = COALESCE(?, proxima_acao),"
            " data_followup = COALESCE(?, data_followup),"
            " atualizado_em = ? WHERE id = ?",
            (
                nova_etapa,
                motivo_perda,
                proxima_acao.strip() if proxima_acao else None,
                data_followup,
                _agora(),
                lead_id,
            ),
        )
        self.conn.commit()
        return self.obter_lead(lead_id)

    def fechar_lead(
        self, lead_id: int, ganho: bool, motivo_perda: str | None = None
    ) -> dict:
        """Atalho de fechamento: ganho -> Pedido pago; perdido -> Não comprou."""
        return self.mover_etapa(
            lead_id,
            ETAPA_GANHOU if ganho else ETAPA_PERDEU,
            motivo_perda=motivo_perda,
        )

    # -- mensagens ---------------------------------------------------

    def registrar_mensagem(
        self, lead_id: int, direcao: str, resumo: str
    ) -> dict:
        self.obter_lead(lead_id)
        if direcao not in ("inbound", "outbound"):
            raise ValueError(f"direcao inválida: {direcao}")
        afirmar_sem_pii(resumo, "resumo")
        if len(resumo.strip()) < 3:
            raise ValueError("resumo curto demais")
        agora = _agora()
        cur = self.conn.execute(
            "INSERT INTO mensagens (lead_id, direcao, resumo, criado_em)"
            " VALUES (?, ?, ?, ?)",
            (lead_id, direcao, resumo.strip(), agora),
        )
        if direcao == "inbound":
            # Cancelar-ao-responder: quem respondeu não recebe o toque.
            self.conn.execute(
                "UPDATE followups SET estado = 'cancelado'"
                " WHERE lead_id = ? AND tipo = 'silencio' AND estado = 'pendente'",
                (lead_id,),
            )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM mensagens WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)

    # -- follow-ups --------------------------------------------------

    def agendar_followup(
        self, lead_id: int, tipo: str, agendado_para: str
    ) -> dict:
        self.obter_lead(lead_id)
        if tipo not in TIPOS_FOLLOWUP:
            raise ValueError(f"tipo de follow-up inválido: {tipo}")
        cur = self.conn.execute(
            "INSERT INTO followups (lead_id, tipo, agendado_para, criado_em)"
            " VALUES (?, ?, ?, ?)",
            (lead_id, tipo, agendado_para, _agora()),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM followups WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)

    def followups_pendentes(self, lead_id: int | None = None) -> list[dict]:
        if lead_id is None:
            rows = self.conn.execute(
                "SELECT * FROM followups WHERE estado = 'pendente' ORDER BY id"
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM followups WHERE lead_id = ? AND estado = 'pendente'"
                " ORDER BY id",
                (lead_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # -- memória por contato ------------------------------------------

    def registrar_interesse(
        self,
        contato_ref: str,
        interesse: str,
        produto_sku: str | None = None,
    ) -> dict:
        """Guarda só o rótulo do interesse. Nunca PII, nunca texto livre."""
        if not _REFERENCIA.match(contato_ref):
            raise ValueError(f"contato_ref inválido: {contato_ref}")
        if interesse not in INTERESSES:
            raise ValueError(f"interesse inválido: {interesse}")
        if produto_sku is not None:
            self.produto_preco(produto_sku)
        self.conn.execute(
            "INSERT INTO memoria_contato"
            " (contato_ref, interesse, ultimo_produto_sku, atualizado_em)"
            " VALUES (?, ?, ?, ?)"
            " ON CONFLICT(contato_ref) DO UPDATE SET"
            " interesse = excluded.interesse,"
            " ultimo_produto_sku = excluded.ultimo_produto_sku,"
            " atualizado_em = excluded.atualizado_em",
            (contato_ref, interesse, produto_sku, _agora()),
        )
        self.conn.commit()
        return self.reconhecer_retorno(contato_ref)

    def reconhecer_retorno(self, contato_ref: str) -> dict | None:
        """Quem volta e diz 'olá': devolve o interesse, sem perguntar de novo."""
        row = self.conn.execute(
            "SELECT * FROM memoria_contato WHERE contato_ref = ?",
            (contato_ref,),
        ).fetchone()
        return dict(row) if row is not None else None
