"""Testes sintéticos e isolados para scripts/preflight-multi-inbox."""

from __future__ import annotations

import fcntl
from importlib.machinery import SourceFileLoader
import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

# Carrega scripts/preflight-multi-inbox como módulo Python
_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT_PATH = _ROOT / "scripts" / "preflight-multi-inbox"

loader = SourceFileLoader("preflight_multi_inbox", str(_SCRIPT_PATH))
spec = importlib.util.spec_from_loader("preflight_multi_inbox", loader)
assert spec is not None
preflight = importlib.util.module_from_spec(spec)
loader.exec_module(preflight)


class TestChecarListener:
    def test_listener_sincronizado(self, tmp_path: Path):
        conteudo = 'VERSION = "0.7.0"\n# mesmo conteudo\n'
        live = tmp_path / "live.py"
        repo = tmp_path / "repo.py"
        live.write_text(conteudo, encoding="utf-8")
        repo.write_text(conteudo, encoding="utf-8")

        res = preflight.checar_listener(live, repo)
        assert res["status"] == "OK"
        assert "sincronizado" in res["detalhe"]
        assert "v0.7.0" in res["detalhe"]

    def test_listener_divergente(self, tmp_path: Path):
        live = tmp_path / "live.py"
        repo = tmp_path / "repo.py"
        live.write_text('VERSION = "0.6.1"\n# versao antiga\n', encoding="utf-8")
        repo.write_text('VERSION = "0.7.0"\n# versao nova\n', encoding="utf-8")

        res = preflight.checar_listener(live, repo)
        assert res["status"] == "PENDENTE"
        assert "v0.6.1" in res["detalhe"]
        assert "v0.7.0" in res["detalhe"]

    def test_listener_ausente(self, tmp_path: Path):
        live = tmp_path / "nao_existe.py"
        repo = tmp_path / "repo.py"
        repo.write_text('VERSION = "0.7.0"\n', encoding="utf-8")

        res = preflight.checar_listener(live, repo)
        assert res["status"] == "PENDENTE"


class TestChecarModoOperacao:
    def test_cumprimento_desativado_globalmente(self, tmp_path: Path):
        modo_file = tmp_path / "modo.json"
        modo_file.write_text(json.dumps({"cumprimento_automatico": False}))

        res = preflight.checar_modo_operacao(modo_file, inboxes=(1, 2))
        assert res["status"] == "OK"
        assert "cumprimento_automatico=false" in res["detalhe"]

    def test_cumprimento_suprimido_por_lista_de_inboxes(self, tmp_path: Path):
        modo_file = tmp_path / "modo.json"
        modo_file.write_text(json.dumps({
            "cumprimento_automatico": True,
            "inboxes_sem_cumprimento": [1, 2],
        }))

        res = preflight.checar_modo_operacao(modo_file, inboxes=(1, 2))
        assert res["status"] == "OK"
        assert "inboxes_sem_cumprimento" in res["detalhe"]

    def test_inboxes_sem_cumprimento_malformado_inteiro(self, tmp_path: Path):
        modo_file = tmp_path / "modo.json"
        modo_file.write_text(json.dumps({
            "cumprimento_automatico": True,
            "inboxes_sem_cumprimento": 1,
        }))

        res = preflight.checar_modo_operacao(modo_file, inboxes=(1, 2))
        assert res["status"] == "PENDENTE"
        assert "malformado" in res["detalhe"]

    def test_inboxes_sem_cumprimento_malformado_string(self, tmp_path: Path):
        modo_file = tmp_path / "modo.json"
        modo_file.write_text(json.dumps({
            "cumprimento_automatico": True,
            "inboxes_sem_cumprimento": "1,2",
        }))

        res = preflight.checar_modo_operacao(modo_file, inboxes=(1, 2))
        assert res["status"] == "PENDENTE"
        assert "malformado" in res["detalhe"]

    def test_inboxes_sem_cumprimento_malformado_objeto(self, tmp_path: Path):
        modo_file = tmp_path / "modo.json"
        modo_file.write_text(json.dumps({
            "cumprimento_automatico": True,
            "inboxes_sem_cumprimento": {"1": True, "2": True},
        }))

        res = preflight.checar_modo_operacao(modo_file, inboxes=(1, 2))
        assert res["status"] == "PENDENTE"
        assert "malformado" in res["detalhe"]

    def test_inboxes_sem_cumprimento_com_elemento_invalido(self, tmp_path: Path):
        modo_file = tmp_path / "modo.json"
        modo_file.write_text(json.dumps({
            "cumprimento_automatico": True,
            "inboxes_sem_cumprimento": [1, {"inbox": 2}],
        }))

        res = preflight.checar_modo_operacao(modo_file, inboxes=(1, 2))
        assert res["status"] == "PENDENTE"
        assert "elemento malformado" in res["detalhe"]

    def test_inboxes_sem_cumprimento_incompleto(self, tmp_path: Path):
        modo_file = tmp_path / "modo.json"
        modo_file.write_text(json.dumps({
            "cumprimento_automatico": True,
            "inboxes_sem_cumprimento": [1],
        }))

        res = preflight.checar_modo_operacao(modo_file, inboxes=(1, 2))
        assert res["status"] == "PENDENTE"
        assert "[2]" in res["detalhe"]

    def test_modo_arquivo_inexistente(self, tmp_path: Path):
        modo_file = tmp_path / "nao_existe.json"
        res = preflight.checar_modo_operacao(modo_file)
        assert res["status"] == "PENDENTE"


class TestContarEventosListener:
    @pytest.mark.parametrize("conexao_ativa", [False, True])
    def test_banco_wal_nao_cria_nem_altera_auxiliares(self, tmp_path: Path, conexao_ativa: bool):
        banco = tmp_path / "listener.db"
        conn = sqlite3.connect(banco)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE events (inbox_id INT, estado TEXT)")
        conn.execute("INSERT INTO events VALUES (1, 'pendente')")
        conn.commit()
        if not conexao_ativa:
            conn.close()
        antes = {
            p.name: (p.read_bytes(), p.stat().st_mtime_ns)
            for p in tmp_path.iterdir()
        }
        try:
            resultado = preflight.contar_eventos_listener(banco)
            assert resultado["status"] == "PENDENTE"
            assert "WAL" in resultado["detalhe"]
            depois = {
                p.name: (p.read_bytes(), p.stat().st_mtime_ns)
                for p in tmp_path.iterdir()
            }
            assert depois == antes
        finally:
            if conexao_ativa:
                conn.close()

    def test_contagem_banco_sintetico_com_caracteres_especiais(self, tmp_path: Path):
        # Nome contendo ? e # para validar Path.as_uri
        db_file = tmp_path / "listener?name#teste.db"
        conn = sqlite3.connect(db_file)
        conn.execute("CREATE TABLE events (message_id INT, inbox_id INT, estado TEXT)")
        conn.executemany(
            "INSERT INTO events VALUES (?, ?, ?)",
            [
                (1, 1, "pendente"),
                (2, 1, "entregue"),
                (3, 1, "entregue"),
                (4, 2, "pendente"),
            ],
        )
        conn.commit()
        conn.close()

        mtime_antes = db_file.stat().st_mtime_ns

        res = preflight.contar_eventos_listener(db_file)
        assert res["status"] == "OK"
        assert "inbox-1: 3 total (1 pendentes)" in res["detalhe"]
        assert "inbox-2: 1 total (1 pendentes)" in res["detalhe"]

        # Comprova que a consulta NÃO modificou o arquivo nem criou colaterais (-wal, -shm)
        assert db_file.stat().st_mtime_ns == mtime_antes
        assert not (tmp_path / f"{db_file.name}-wal").exists()
        assert not (tmp_path / f"{db_file.name}-shm").exists()

        # Comprova que a conexão mode=ro rejeita escritas
        uri = db_file.resolve().as_uri() + "?mode=ro"
        ro_conn = sqlite3.connect(uri, uri=True)
        try:
            with pytest.raises(sqlite3.OperationalError, match="readonly database"):
                ro_conn.execute("INSERT INTO events VALUES (5, 2, 'pendente')")
        finally:
            ro_conn.close()

    def test_banco_inexistente(self, tmp_path: Path):
        db_file = tmp_path / "nao_existe.db"
        res = preflight.contar_eventos_listener(db_file)
        assert res["status"] == "PENDENTE"


class TestChecarBackups:
    def test_backups_validos_nao_vazios(self, tmp_path: Path):
        bdir = tmp_path / "backups"
        bdir.mkdir()
        backup_file = bdir / "backup-20261124-segredo.tar.gz"
        backup_file.write_bytes(b"conteudo real de backup")

        res = preflight.checar_backups([bdir])
        assert res["status"] == "OK"
        # Não pode expor o nome privado do arquivo!
        assert "backup-20261124-segredo" not in res["detalhe"]
        assert "1 arquivo(s) de backup não vazio(s)" in res["detalhe"]
        assert "integridade e atualidade não verificadas" in res["detalhe"]

    def test_rejeita_arquivo_vazio(self, tmp_path: Path):
        bdir = tmp_path / "backups_vazio"
        bdir.mkdir()
        (bdir / "backup_vazio.tar.gz").write_bytes(b"")

        res = preflight.checar_backups([bdir])
        assert res["status"] == "PENDENTE"
        assert "Nenhum arquivo de backup não vazio" in res["detalhe"]

    def test_rejeita_arquivo_sem_extensao_de_backup(self, tmp_path: Path):
        bdir = tmp_path / "backups_txt"
        bdir.mkdir()
        (bdir / "anotacoes.txt").write_bytes(b"texto comum")
        (bdir / "script.py").write_bytes(b"codigo")

        res = preflight.checar_backups([bdir])
        assert res["status"] == "PENDENTE"

    def test_backups_diretorio_inexistente(self, tmp_path: Path):
        bdir = tmp_path / "nao_existe"
        res = preflight.checar_backups([bdir])
        assert res["status"] == "PENDENTE"


class TestChecarMigracaoEstado:
    @pytest.mark.parametrize("arquivo_legado", [
        "fila.sqlite",
        "fila.sqlite-wal",
        "fila.sqlite-shm",
        "entregas.sqlite",
        "entregas.sqlite-wal",
        "entregas.sqlite-shm",
    ])
    def test_detecta_arquivos_legados_na_raiz(self, tmp_path: Path, arquivo_legado: str):
        estado = tmp_path / f"estado_{arquivo_legado}"
        estado.mkdir()
        (estado / arquivo_legado).write_text("dummy")

        res = preflight.checar_migracao_estado(estado)
        assert res["status"] == "PENDENTE"
        assert arquivo_legado in res["detalhe"]
        assert "inbox-1/" in res["detalhe"]

    def test_diretorio_estado_inexistente_retorna_pendente(self, tmp_path: Path):
        estado = tmp_path / "estado_fantasma"
        res = preflight.checar_migracao_estado(estado)
        # Evita default errado /estado indicando OK sem a pasta real existir
        assert res["status"] == "PENDENTE"

    def test_arquivos_ja_migrados_em_inbox_1(self, tmp_path: Path):
        estado = tmp_path / "estado"
        inbox1 = estado / "inbox-1"
        inbox1.mkdir(parents=True)
        (inbox1 / "fila.sqlite").write_text("dummy")
        (inbox1 / "entregas.sqlite").write_text("dummy")

        res = preflight.checar_migracao_estado(estado)
        assert res["status"] == "OK"
        assert "já particionado" in res["detalhe"]

    def test_estado_vazio_raiz_limpa(self, tmp_path: Path):
        estado = tmp_path / "estado_vazio"
        estado.mkdir()

        res = preflight.checar_migracao_estado(estado)
        assert res["status"] == "OK"
        assert "Raiz limpa" in res["detalhe"]


class TestChecarLockHost:
    def test_diretorio_inexistente_retorna_pendente(self, tmp_path: Path):
        estado = tmp_path / "estado_fantasma"
        res = preflight.checar_lock_host(estado)
        # Não pode assumir lock livre se o diretório sequer existe
        assert res["status"] == "PENDENTE"

    def test_lock_ausente_em_diretorio_existente(self, tmp_path: Path):
        estado = tmp_path / "estado"
        estado.mkdir()

        res = preflight.checar_lock_host(estado)
        assert res["status"] == "OK"
        assert "host.lock ausente (lock livre)" in res["detalhe"]

    def test_lock_livre_arquivo_existe(self, tmp_path: Path):
        estado = tmp_path / "estado"
        estado.mkdir()
        lock = estado / "host.lock"
        lock.write_text("")

        res = preflight.checar_lock_host(estado)
        assert res["status"] == "OK"
        assert "host.lock livre" in res["detalhe"]

    def test_lock_ocupado(self, tmp_path: Path):
        estado = tmp_path / "estado"
        estado.mkdir()
        lock = estado / "host.lock"
        lock.write_text("")

        fd = os.open(lock, os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            res = preflight.checar_lock_host(estado)
            assert res["status"] == "PENDENTE"
            assert "ocupado por processo ativo" in res["detalhe"]
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)


class TestCLIPreflight:
    @pytest.mark.parametrize("json_output", [False, True])
    @pytest.mark.parametrize("pendencia", [False, True])
    def test_entrypoint_subprocess(self, tmp_path: Path, json_output: bool, pendencia: bool):
        amb = self._montar_ambiente_sintetico_ok(tmp_path)
        if pendencia:
            (amb["estado"] / "entregas.sqlite-shm").write_text("sintetico")
        argv = [
            sys.executable, str(_SCRIPT_PATH),
            "--listener-live", str(amb["live"]),
            "--listener-repo", str(amb["repo"]),
            "--modo-operacao", str(amb["modo"]),
            "--listener-db", str(amb["db"]),
            "--estado-host", str(amb["estado"]),
            "--backup-dir", str(amb["bdir"]),
        ]
        if json_output:
            argv.append("--json")
        resultado = subprocess.run(argv, capture_output=True, text=True, timeout=10)
        assert resultado.returncode == int(pendencia), resultado.stderr
        if json_output:
            itens = json.loads(resultado.stdout)
            assert any(item["status"] == "PENDENTE" for item in itens) == pendencia
        else:
            assert ("[PENDENTE]" in resultado.stdout) == pendencia

    def _montar_ambiente_sintetico_ok(self, tmp_path: Path):
        live = tmp_path / "live.py"
        repo = tmp_path / "repo.py"
        conteudo_listener = 'VERSION = "0.7.0"\n'
        live.write_text(conteudo_listener, encoding="utf-8")
        repo.write_text(conteudo_listener, encoding="utf-8")

        modo = tmp_path / "modo.json"
        modo.write_text(json.dumps({"cumprimento_automatico": False}), encoding="utf-8")

        db = tmp_path / "listener.db"
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE events (message_id INT, inbox_id INT, estado TEXT)")
        conn.commit()
        conn.close()

        bdir = tmp_path / "backups"
        bdir.mkdir()
        (bdir / "backup.tar.gz").write_bytes(b"dados")

        estado = tmp_path / "estado"
        estado.mkdir()

        return {
            "live": live,
            "repo": repo,
            "modo": modo,
            "db": db,
            "bdir": bdir,
            "estado": estado,
        }

    def test_cli_opcoes_obrigatorias_sem_defaults_home_pc(self):
        # Chamar sem opções deve falhar no argparse (exit 2)
        with pytest.raises(SystemExit) as exc:
            preflight.main([])
        assert exc.value.code == 2

    def test_cli_sucesso_texto(self, tmp_path: Path, capsys):
        amb = self._montar_ambiente_sintetico_ok(tmp_path)
        argv = [
            "--listener-live", str(amb["live"]),
            "--listener-repo", str(amb["repo"]),
            "--modo-operacao", str(amb["modo"]),
            "--listener-db", str(amb["db"]),
            "--estado-host", str(amb["estado"]),
            "--backup-dir", str(amb["bdir"]),
        ]
        ret = preflight.main(argv)
        assert ret == 0

        out = capsys.readouterr().out
        assert "6 OK, 0 PENDENTE(S)" in out

    def test_cli_sucesso_json(self, tmp_path: Path, capsys):
        amb = self._montar_ambiente_sintetico_ok(tmp_path)
        argv = [
            "--listener-live", str(amb["live"]),
            "--listener-repo", str(amb["repo"]),
            "--modo-operacao", str(amb["modo"]),
            "--listener-db", str(amb["db"]),
            "--estado-host", str(amb["estado"]),
            "--backup-dir", str(amb["bdir"]),
            "--json",
        ]
        ret = preflight.main(argv)
        assert ret == 0

        out = capsys.readouterr().out
        dados = json.loads(out)
        assert len(dados) == 6
        assert all(item["status"] == "OK" for item in dados)

    def test_cli_erro_pendencia_texto(self, tmp_path: Path, capsys):
        amb = self._montar_ambiente_sintetico_ok(tmp_path)
        # Cria arquivo legado na raiz do estado para forçar PENDENTE
        (amb["estado"] / "fila.sqlite").write_text("dummy")

        argv = [
            "--listener-live", str(amb["live"]),
            "--listener-repo", str(amb["repo"]),
            "--modo-operacao", str(amb["modo"]),
            "--listener-db", str(amb["db"]),
            "--estado-host", str(amb["estado"]),
            "--backup-dir", str(amb["bdir"]),
        ]
        ret = preflight.main(argv)
        assert ret == 1

        out = capsys.readouterr().out
        assert "[PENDENTE] Migração de estado" in out
        assert "PENDENTE(S)" in out

    def test_cli_erro_pendencia_json(self, tmp_path: Path, capsys):
        amb = self._montar_ambiente_sintetico_ok(tmp_path)
        (amb["estado"] / "fila.sqlite-wal").write_text("dummy")

        argv = [
            "--listener-live", str(amb["live"]),
            "--listener-repo", str(amb["repo"]),
            "--modo-operacao", str(amb["modo"]),
            "--listener-db", str(amb["db"]),
            "--estado-host", str(amb["estado"]),
            "--backup-dir", str(amb["bdir"]),
            "--json",
        ]
        ret = preflight.main(argv)
        assert ret == 1

        out = capsys.readouterr().out
        dados = json.loads(out)
        assert any(item["status"] == "PENDENTE" for item in dados)


class TestConfigCanaisExemplo:
    def test_exemplo_valido_e_compativel(self, tmp_path: Path):
        from tuttibom.mcp_ops.cli import _montar_config_canais

        caminho_exemplo = _ROOT / "config" / "canais-multi-inbox.example.json"
        assert caminho_exemplo.is_file()

        dados = json.loads(caminho_exemplo.read_text(encoding="utf-8"))
        assert set(dados.keys()) == {"canais"}
        assert len(dados["canais"]) == 2

        c1, c2 = dados["canais"]
        assert c1["conta_id"] == c2["conta_id"]
        assert c1["inbox_id"] != c2["inbox_id"]
        assert c1["inbox_id"] == "1"
        assert c2["inbox_id"] == "2"

        pat_dummy = tmp_path / "pat.txt"
        pat_dummy.write_text("dummy-pat")
        pat_dummy.chmod(0o600)

        dados_sinteticos = {
            "canais": [
                {**c1, "pat_arquivo": str(pat_dummy)},
                {**c2, "pat_arquivo": str(pat_dummy)},
            ]
        }

        cfg_privada = tmp_path / "canais.json"
        cfg_privada.write_text(json.dumps(dados_sinteticos))
        cfg_privada.chmod(0o600)

        estado_dir = tmp_path / "estado"
        estado_dir.mkdir(mode=0o700)

        backends, pilhas, sync_loop = _montar_config_canais(cfg_privada, estado_dir)
        assert backends is None
        assert pilhas is not None
        assert set(pilhas.keys()) == {"1", "2"}
        assert callable(sync_loop[0])
        assert isinstance(sync_loop[1], float)
