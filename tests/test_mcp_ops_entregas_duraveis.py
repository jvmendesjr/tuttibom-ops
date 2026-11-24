"""Testes do diário durável de envio+ACK, somente em disco temporário."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tuttibom.mcp_ops.atendimento import _digest_envio as digest_do_adaptador
from tuttibom.mcp_ops.persistencia import BancoOps
from tuttibom.mcp_ops.entregas_duraveis import (
    DiarioEntregas,
    ErroEntregaDuravel,
    digest_envio,
)

ROOT = Path(__file__).resolve().parents[1]
IDS = ("msg-real-001", "msg-real-002")


def _digest(rotulo: str = "payload-lab") -> str:
    return hashlib.sha256(rotulo.encode("utf-8")).hexdigest()


def _reservar(diario: DiarioEntregas, **mudancas):
    argumentos = {
        "message_ids": IDS,
        "idempotency_key": "chave-lab-a",
        "digest": _digest(),
    }
    argumentos.update(mudancas)
    return diario.reservar_envio(**argumentos)


def _dump(caminho: Path) -> str:
    with sqlite3.connect(caminho) as conn:
        return "\n".join(conn.iterdump())


def _contar(caminho: Path, tabela: str) -> int:
    with sqlite3.connect(caminho) as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]


def _processo(script: str, *argumentos: object) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(ROOT / "src"), env.get("PYTHONPATH", "")]))
    return subprocess.run(
        [sys.executable, "-c", script, *(str(arg) for arg in argumentos)],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
        env=env,
    )


def test_digest_e_compativel_e_payload_nao_entra_no_diario(tmp_path: Path):
    banco = tmp_path / "entregas.sqlite3"
    texto = "TEXTO_EXATO_SINTETICO_NAO_PERSISTIR"
    imagem = b"MIDIA_SINTETICA_NAO_PERSISTIR"
    digest = digest_envio(
        conversa_ref="conv-lab-01", texto=texto, imagem=imagem, message_ids=IDS
    )
    assert digest == digest_do_adaptador("conv-lab-01", texto, imagem, IDS)

    diario = DiarioEntregas(banco)
    reserva = _reservar(diario, digest=digest)
    assert reserva["acao"] == "enviar"
    assert reserva["tentativa_id"].startswith("ten_")
    mapa = diario.consultar_mensagem(IDS[0])
    assert mapa["entrega_id"] == reserva["entrega_id"]
    assert mapa["tentativa_id"] == reserva["tentativa_id"]

    persistido = _dump(banco)
    assert digest in persistido
    assert texto not in persistido
    assert imagem.decode("ascii") not in persistido
    assert "conv-lab-01" not in persistido
    assert "texto" not in persistido
    assert "imagem" not in persistido


def test_reserva_atomica_concorrente_tem_um_so_autorizado_a_enviar(tmp_path: Path):
    banco = tmp_path / "concorrencia.sqlite3"
    diarios = [DiarioEntregas(banco) for _ in range(6)]
    barreira = threading.Barrier(len(diarios))

    def reservar(diario):
        barreira.wait(timeout=5)
        return _reservar(diario)

    with ThreadPoolExecutor(max_workers=len(diarios)) as pool:
        resultados = list(pool.map(reservar, diarios))

    autorizados = [r for r in resultados if r["acao"] == "enviar"]
    assert len(autorizados) == 1
    assert sum(r["acao"] == "aguardar" for r in resultados) == len(diarios) - 1
    assert _contar(banco, "entregas_diario") == 1
    assert _contar(banco, "entregas_tentativas") == 1

    vencedor = autorizados[0]
    aceito = diarios[0].confirmar_envio(
        tentativa_id=vencedor["tentativa_id"], envio_ref="envio-opaco-001"
    )
    assert aceito["acao"] == "somente_ack"
    for message_id in IDS:
        diarios[0].registrar_ack(
            tentativa_id=vencedor["tentativa_id"], message_id=message_id
        )
    replay = _reservar(diarios[-1])
    assert replay["acao"] == "nenhuma"
    assert replay["concluido"] is True
    assert _contar(banco, "entregas_tentativas") == 1


def test_somente_falha_comprovadamente_sem_envio_permite_retry(tmp_path: Path):
    banco = tmp_path / "retry.sqlite3"
    diario = DiarioEntregas(banco)
    primeira = _reservar(diario)
    falha = diario.registrar_falha_envio(
        tentativa_id=primeira["tentativa_id"],
        comprovadamente_nao_enviado=True,
    )
    assert falha["estado"] == "nao_enviado"
    assert falha["acao"] == "reservar"
    repetida = diario.registrar_falha_envio(
        tentativa_id=primeira["tentativa_id"],
        comprovadamente_nao_enviado=True,
    )
    assert repetida["estado"] == "nao_enviado"
    assert repetida["replay"] is True

    segunda = _reservar(diario)
    assert segunda["acao"] == "enviar"
    assert segunda["entrega_id"] == primeira["entrega_id"]
    assert segunda["tentativa_id"] != primeira["tentativa_id"]
    assert _contar(banco, "entregas_diario") == 1
    assert _contar(banco, "entregas_tentativas") == 2
    assert diario.consultar_mensagem(IDS[0])["tentativa_id"] == segunda["tentativa_id"]


def test_falha_sem_prova_de_nao_envio_fica_incerta_sem_retry(tmp_path: Path):
    banco = tmp_path / "incerto.sqlite3"
    diario = DiarioEntregas(banco)
    reserva = _reservar(diario)
    incerto = diario.registrar_falha_envio(
        tentativa_id=reserva["tentativa_id"],
        comprovadamente_nao_enviado=False,
    )
    assert incerto["estado"] == "incerto"
    assert incerto["acao"] == "bloqueado"

    for chave in ("chave-lab-a", "chave-lab-nova"):
        bloqueado = _reservar(diario, idempotency_key=chave)
        assert bloqueado["acao"] == "bloqueado"
        assert bloqueado["codigo"] == "entrega_incerta"
    nao_resolve = diario.registrar_falha_envio(
        tentativa_id=reserva["tentativa_id"],
        comprovadamente_nao_enviado=True,
    )
    assert nao_resolve["estado"] == "incerto"
    assert _contar(banco, "entregas_tentativas") == 1


def test_replay_e_mudanca_de_chave_reusam_entrega_e_tentativa(tmp_path: Path):
    banco = tmp_path / "replay.sqlite3"
    diario = DiarioEntregas(banco)
    reserva = _reservar(diario)
    diario.confirmar_envio(
        tentativa_id=reserva["tentativa_id"], envio_ref="envio-opaco-001"
    )

    mesmo = _reservar(diario)
    assert mesmo["acao"] == "somente_ack"
    assert mesmo["replay"] is True
    outra_chave = _reservar(diario, idempotency_key="chave-lab-b")
    assert outra_chave["entrega_id"] == reserva["entrega_id"]
    assert outra_chave["tentativa_id"] == reserva["tentativa_id"]
    assert outra_chave["acao"] == "somente_ack"
    assert _contar(banco, "entregas_chaves") == 2

    confirmado_de_novo = diario.confirmar_envio(
        tentativa_id=reserva["tentativa_id"], envio_ref="envio-opaco-001"
    )
    assert confirmado_de_novo["replay"] is True
    conflito_ref = diario.confirmar_envio(
        tentativa_id=reserva["tentativa_id"], envio_ref="envio-opaco-outro"
    )
    assert conflito_ref["codigo"] == "envio_conflito"

    for message_id in IDS:
        diario.registrar_ack(
            tentativa_id=reserva["tentativa_id"], message_id=message_id
        )
    concluido = _reservar(diario, idempotency_key="chave-lab-c")
    assert concluido["acao"] == "nenhuma"
    assert concluido["concluido"] is True
    assert concluido["envio_ref"] == "envio-opaco-001"
    assert _contar(banco, "entregas_chaves") == 3
    assert _contar(banco, "entregas_tentativas") == 1

    conflito = _reservar(diario, idempotency_key="chave-lab-d", digest=_digest("outro"))
    assert conflito["codigo"] == "idempotencia_conflito"
    assert _contar(banco, "entregas_tentativas") == 1


def test_ack_parcial_e_falho_retomam_em_nova_instancia_sem_reenvio(tmp_path: Path):
    banco = tmp_path / "ack-parcial.sqlite3"
    primeira = DiarioEntregas(banco)
    reserva = _reservar(primeira)
    primeira.confirmar_envio(
        tentativa_id=reserva["tentativa_id"], envio_ref="envio-opaco-001"
    )
    falha = primeira.registrar_falha_ack(tentativa_id=reserva["tentativa_id"])
    assert falha["estado"] == "aceito"
    parcial = primeira.registrar_ack(
        tentativa_id=reserva["tentativa_id"], message_id=IDS[0]
    )
    assert parcial["ack_pendentes"] == [IDS[1]]
    assert parcial["concluido"] is False

    segunda = DiarioEntregas(banco)
    assert segunda.recuperar_reservas() == 0
    pendentes = segunda.listar_acoes_pendentes()
    assert len(pendentes) == 1
    assert pendentes[0]["acao"] == "somente_ack"
    assert pendentes[0]["ack_pendentes"] == [IDS[1]]
    replay = _reservar(segunda, idempotency_key="chave-depois-reinicio")
    assert replay["acao"] == "somente_ack"
    assert replay["tentativa_id"] == reserva["tentativa_id"]

    errado = segunda.registrar_ack(
        tentativa_id=reserva["tentativa_id"], message_id="msg-nao-vinculada"
    )
    assert errado["codigo"] == "mensagem_nao_vinculada"
    assert segunda.consultar_mensagem(IDS[1])["ack_em"] is None
    final = segunda.registrar_ack(
        tentativa_id=reserva["tentativa_id"], message_id=IDS[1]
    )
    assert final["acao"] == "nenhuma"
    assert final["concluido"] is True
    assert segunda.listar_acoes_pendentes() == []
    assert _contar(banco, "entregas_tentativas") == 1


def test_timestamps_utc_de_aceite_falha_e_ack(tmp_path: Path):
    banco = tmp_path / "timestamps.sqlite3"
    inicio = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
    instantes = iter(inicio + timedelta(seconds=n) for n in range(4))
    diario = DiarioEntregas(banco, relogio=lambda: next(instantes))
    reserva = _reservar(diario, message_ids=[IDS[0]])
    diario.confirmar_envio(
        tentativa_id=reserva["tentativa_id"], envio_ref="envio-opaco-001"
    )
    diario.registrar_falha_ack(tentativa_id=reserva["tentativa_id"])
    diario.registrar_ack(tentativa_id=reserva["tentativa_id"], message_id=IDS[0])

    with sqlite3.connect(banco) as conn:
        conn.row_factory = sqlite3.Row
        entrega = conn.execute("SELECT * FROM entregas_diario").fetchone()
        mensagem = conn.execute("SELECT * FROM entregas_mensagens").fetchone()
    iso = lambda n: (inicio + timedelta(seconds=n)).isoformat(timespec="microseconds")
    assert entrega["criado_em"] == iso(0)
    assert entrega["atualizado_em"] == iso(3)
    assert entrega["aceito_em"] == iso(1)
    assert entrega["falha_ack_em"] == iso(2)
    assert mensagem["ack_em"] == iso(3)


def test_processo_que_cai_apos_reserva_deixa_entrega_incerta(tmp_path: Path):
    banco = tmp_path / "crash.sqlite3"
    script = """
import os, sys
from tuttibom.mcp_ops.entregas_duraveis import DiarioEntregas
d = DiarioEntregas(sys.argv[1])
r = d.reservar_envio(message_ids=[sys.argv[2], sys.argv[3]], idempotency_key=sys.argv[4], digest=sys.argv[5])
open(sys.argv[6], 'w', encoding='ascii').write('possivel-efeito-externo-simulado')
print(r['tentativa_id'], flush=True)
os._exit(0)
"""
    marcador = tmp_path / "efeito-externo.txt"
    filho = _processo(script, banco, *IDS, "chave-lab-a", _digest(), marcador)
    tentativa_id = filho.stdout.strip()
    assert tentativa_id.startswith("ten_")
    assert marcador.read_text(encoding="ascii") == "possivel-efeito-externo-simulado"

    reiniciado = DiarioEntregas(banco)
    assert reiniciado.recuperar_reservas() == 1
    bloqueado = _reservar(reiniciado)
    assert bloqueado["estado"] == "incerto"
    assert bloqueado["acao"] == "bloqueado"
    assert bloqueado["codigo"] == "entrega_incerta"
    confirmacao = reiniciado.confirmar_envio(
        tentativa_id=tentativa_id, envio_ref="envio-opaco-001"
    )
    assert confirmacao["estado"] == "incerto"
    assert confirmacao["envio_ref"] is None
    nao_resolve = reiniciado.registrar_falha_envio(
        tentativa_id=tentativa_id, comprovadamente_nao_enviado=True
    )
    assert nao_resolve["estado"] == "incerto"
    assert [item["acao"] for item in reiniciado.listar_acoes_pendentes()] == ["bloqueado"]
    assert _contar(banco, "entregas_tentativas") == 1


def test_novo_processo_apos_aceito_executa_somente_ack(tmp_path: Path):
    banco = tmp_path / "novo-processo.sqlite3"
    aceita = """
import sys
from tuttibom.mcp_ops.entregas_duraveis import DiarioEntregas
d = DiarioEntregas(sys.argv[1])
r = d.reservar_envio(message_ids=[sys.argv[2], sys.argv[3]], idempotency_key=sys.argv[4], digest=sys.argv[5])
d.confirmar_envio(tentativa_id=r['tentativa_id'], envio_ref='envio-opaco-001')
d.registrar_ack(tentativa_id=r['tentativa_id'], message_id=sys.argv[2])
print(r['tentativa_id'])
"""
    tentativa_id = _processo(aceita, banco, *IDS, "chave-lab-a", _digest()).stdout.strip()
    retoma = """
import json, sys
from tuttibom.mcp_ops.entregas_duraveis import DiarioEntregas
d = DiarioEntregas(sys.argv[1])
assert d.recuperar_reservas() == 0
r = d.reservar_envio(message_ids=[sys.argv[2], sys.argv[3]], idempotency_key='chave-nova-pos-reinicio', digest=sys.argv[4])
assert r['acao'] == 'somente_ack'
assert r['tentativa_id'] == sys.argv[5]
assert r['ack_pendentes'] == [sys.argv[3]]
d.registrar_falha_ack(tentativa_id=r['tentativa_id'])
r = d.registrar_ack(tentativa_id=r['tentativa_id'], message_id=sys.argv[3])
print(json.dumps(r))
"""
    final = json.loads(_processo(retoma, banco, *IDS, _digest(), tentativa_id).stdout)
    assert final["concluido"] is True
    assert final["acao"] == "nenhuma"
    assert final["envio_ref"] == "envio-opaco-001"
    assert _contar(banco, "entregas_tentativas") == 1
    with sqlite3.connect(banco) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM entregas_mensagens WHERE ack_em IS NULL"
        ).fetchone()[0] == 0


def test_diario_usa_banco_e_transacao_independentes_do_nucleo(tmp_path: Path):
    nucleo = BancoOps(tmp_path / "nucleo.sqlite3")
    diario = DiarioEntregas(tmp_path / "envios.sqlite3")
    try:
        with nucleo.transacao() as conn:
            assert conn.execute("SELECT 1").fetchone()[0] == 1
            reserva = _reservar(diario)
        assert reserva["acao"] == "enviar"
        with sqlite3.connect(tmp_path / "envios.sqlite3") as conn:
            tabelas = {
                row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        assert "entregas_diario" in tabelas
        assert "tokens" not in tabelas
    finally:
        nucleo.close()


def test_argumentos_invalidos_nao_criam_registros(tmp_path: Path):
    banco = tmp_path / "validacao.sqlite3"
    with pytest.raises(ErroEntregaDuravel):
        DiarioEntregas(":memory:")
    diario = DiarioEntregas(banco)
    with pytest.raises(ErroEntregaDuravel):
        _reservar(diario, message_ids=[])
    with pytest.raises(ErroEntregaDuravel):
        _reservar(diario, message_ids=[IDS[0], IDS[0]])
    with pytest.raises(ErroEntregaDuravel):
        _reservar(diario, idempotency_key="chave com texto livre")
    with pytest.raises(ErroEntregaDuravel):
        _reservar(diario, digest="digest-invalido")
    assert _contar(banco, "entregas_diario") == 0
