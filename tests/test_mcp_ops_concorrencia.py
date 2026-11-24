"""Corridas reais no SQLite temporário do núcleo OPS."""

from __future__ import annotations

import itertools
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tuttibom.mcp_ops import (
    FronteiraIdentidadeLaboratorio,
    RegistroIdentidade,
    ServidorOps,
)
from tuttibom.mcp_ops.erros import AreaOcupada, AutorizacaoJaUtilizada, ErroOps

RESUMO = "Confirmação sintética das funções e limites recebidos no manifesto."


def _fronteira() -> FronteiraIdentidadeLaboratorio:
    return FronteiraIdentidadeLaboratorio({
        "admin-lab": RegistroIdentidade("identidade-admin-lab", administrador=True),
        "cliente-a": RegistroIdentidade("identidade-lab-a"),
        "cliente-b": RegistroIdentidade("identidade-lab-b"),
    })


def _handlers():
    return {
        "ops_produto_consultar": lambda _args: {"ok": True},
        "ops_crm_registrar_lead": lambda _args: {"ok": True},
    }


def test_ativacao_concorrente_consome_autorizacao_uma_vez(tmp_path: Path):
    banco = tmp_path / "ativacao-concorrente.sqlite3"
    fronteira = _fronteira()
    servidor_a = ServidorOps(
        banco, fronteira, handlers=_handlers(),
        gerador_token=lambda: "ops_lab_servidor_a_VALOR_SINTETICO",
    )
    servidor_b = ServidorOps(
        banco, fronteira, handlers=_handlers(),
        gerador_token=lambda: "ops_lab_servidor_b_VALOR_SINTETICO",
    )
    try:
        admin = servidor_a.configurar_administrador("admin-lab")
        cliente_a = servidor_a.configurar_cliente("cliente-a")
        cliente_b = servidor_b.configurar_cliente("cliente-a")
        autorizacao = admin.autorizar(
            agente_id="agente-lab-a", cliente=cliente_a, funcoes=["03.01"]
        )
        barreira = threading.Barrier(2)

        def ativar(cliente):
            barreira.wait(timeout=5)
            try:
                return cliente.ativar(autorizacao.referencia, ["03.01"])
            except ErroOps as exc:
                return exc

        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados = list(pool.map(ativar, (cliente_a, cliente_b)))

        erros = [r for r in resultados if isinstance(r, ErroOps)]
        sucessos = [r for r in resultados if not isinstance(r, ErroOps)]
        assert len(sucessos) == 1
        assert len(erros) == 1
        assert isinstance(erros[0], AutorizacaoJaUtilizada)
        with sqlite3.connect(banco) as conn:
            assert conn.execute("SELECT COUNT(*) FROM tokens").fetchone()[0] == 1
            assert conn.execute(
                "SELECT COUNT(*) FROM autorizacoes WHERE consumido_em IS NOT NULL"
            ).fetchone()[0] == 1
    finally:
        servidor_a.close()
        servidor_b.close()


def test_confirmacao_concorrente_deixa_um_so_escritor_por_area(tmp_path: Path):
    banco = tmp_path / "lease-concorrente.sqlite3"
    sequencia = itertools.count(1)
    servidor = ServidorOps(
        banco,
        _fronteira(),
        handlers=_handlers(),
        gerador_token=lambda: f"ops_lab_{next(sequencia):06d}_VALOR_SINTETICO",
    )
    try:
        admin = servidor.configurar_administrador("admin-lab")
        clientes = {
            "a": servidor.configurar_cliente("cliente-a"),
            "b": servidor.configurar_cliente("cliente-b"),
        }
        sessoes = {}
        manifestos = {}
        recibos = {}
        for nome, cliente in clientes.items():
            agente = f"agente-lab-{nome}"
            autorizacao = admin.autorizar(
                agente_id=agente, cliente=cliente, funcoes=["02.01", "03.01"]
            )
            recibos[nome] = cliente.ativar(
                autorizacao.referencia, ["02.01", "03.01"]
            )
            sessoes[nome] = cliente.conectar()
            manifestos[nome] = sessoes[nome].manifesto().hash

        barreira = threading.Barrier(2)

        def confirmar(nome):
            barreira.wait(timeout=5)
            try:
                return sessoes[nome].confirmar_atribuicoes(manifestos[nome], RESUMO)
            except ErroOps as exc:
                return exc

        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados = dict(zip(("a", "b"), pool.map(confirmar, ("a", "b"))))

        vencedores = [nome for nome, r in resultados.items() if not isinstance(r, ErroOps)]
        perdedores = [nome for nome, r in resultados.items() if isinstance(r, AreaOcupada)]
        assert len(vencedores) == 1
        assert len(perdedores) == 1
        vencedor = vencedores[0]
        perdedor = perdedores[0]
        assert sessoes[vencedor].chamar("02.01")["ok"] is True
        assert sessoes[perdedor].chamar("03.01")["ok"] is True
        with sqlite3.connect(banco) as conn:
            assert conn.execute("SELECT COUNT(*) FROM leases WHERE area = '02'").fetchone()[0] == 1

        assert admin.revogar_agente(f"agente-lab-{vencedor}") == 1
        sessoes[perdedor].confirmar_atribuicoes(manifestos[perdedor], RESUMO)
        assert sessoes[perdedor].chamar("02.01")["ok"] is True
        with sqlite3.connect(banco) as conn:
            dono = conn.execute(
                "SELECT token_id FROM leases WHERE area = '02'"
            ).fetchone()[0]
        assert dono == recibos[perdedor].token_id
    finally:
        servidor.close()
