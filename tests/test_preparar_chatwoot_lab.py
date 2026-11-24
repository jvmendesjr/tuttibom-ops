"""Preparação de laboratório com transporte falso e arquivos locais sintéticos."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from unittest.mock import patch

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/preparar_chatwoot_lab.py"
SPEC = importlib.util.spec_from_file_location("preparar_chatwoot_lab", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
preparar = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preparar)


def test_preparacao_recusa_lab_nao_isolado():
    with patch.object(preparar, "_lab_isolado", return_value=False), \
         patch.object(preparar.subprocess, "run") as executar:
        assert preparar.main() == 1
        executar.assert_not_called()


def test_cada_preparacao_tem_arquivo_unico_privado_sem_expor_caminho(capsys):
    resposta = subprocess.CompletedProcess([], 0, b"preparado conta=1 inbox=1 arquivo=sim\n")
    with patch.dict(os.environ, {}, clear=True), \
         patch.object(preparar, "_lab_isolado", return_value=True), \
         patch.object(preparar.subprocess, "run", return_value=resposta) as executar:
        assert preparar.main() == 0
        assert preparar.main() == 0
    caminhos = []
    for chamada in executar.call_args_list:
        comando = chamada.args[0]
        configuracao = comando[comando.index("-e") + 1]
        caminhos.append(configuracao.split("=", 1)[1])
        assert caminhos[-1].startswith("/tmp/tb-lab-")
        assert caminhos[-1].endswith(".json")
        assert chamada.kwargs["input"] == preparar.RUBY.encode()
    assert caminhos[0] != caminhos[1]
    saida = capsys.readouterr().out
    assert all(caminho not in saida for caminho in caminhos)


def test_arquivo_explicito_e_repassado_ao_container():
    resposta = subprocess.CompletedProcess([], 0, b"preparado conta=1 inbox=1 arquivo=sim\n")
    with patch.dict(os.environ, {"TB_LAB_ATENDIMENTO_JSON": "/tmp/fixture-lab.json"}), \
         patch.object(preparar, "_lab_isolado", return_value=True), \
         patch.object(preparar.subprocess, "run", return_value=resposta) as executar:
        assert preparar.main() == 0
    assert "TB_LAB_ATENDIMENTO_JSON=/tmp/fixture-lab.json" in executar.call_args.args[0]


def test_callers_existentes_compartilham_arquivo_por_ambiente(monkeypatch):
    from test_mcp_ops_chatwoot_isolado import preparar_chatwoot, TransporteNamespace

    monkeypatch.setenv("TB_LAB_ATENDIMENTO_JSON", "")
    resposta = subprocess.CompletedProcess([], 0, "preparado conta=1 inbox=1 arquivo=sim\n")
    with patch("test_mcp_ops_chatwoot_isolado.subprocess.run", return_value=resposta) as executar:
        assert preparar_chatwoot() == ("1", "1")
        arquivo = executar.call_args.kwargs["env"]["TB_LAB_ATENDIMENTO_JSON"]
    primeiro = TransporteNamespace()
    segundo = TransporteNamespace()
    assert primeiro.arquivo == segundo.arquivo == arquivo
    filho = subprocess.run(
        [sys.executable, "-c", "import os; print(os.environ['TB_LAB_ATENDIMENTO_JSON'])"],
        capture_output=True, text=True, timeout=10,
    )
    assert filho.returncode == 0
    assert filho.stdout.strip() == arquivo
    corpo = json.dumps({"status": 200, "enviada": True, "corpo_b64": ""}).encode()
    resposta_http = subprocess.CompletedProcess([], 0, corpo, b"")
    with patch("test_mcp_ops_chatwoot_isolado.subprocess.run", return_value=resposta_http) as executar:
        assert primeiro.chamar("GET", "/api/v1/accounts/1/conversations").status == 200
    assert f"TB_LAB_ATENDIMENTO_JSON={arquivo}" in executar.call_args.args[0]


@pytest.mark.parametrize("caminho", ["/etc/arquivo.json", "/tmp/../arquivo.json", "/tmp/nome com espaço.json"])
def test_arquivo_explicito_invalido_nao_executa_runner(caminho):
    with patch.dict(os.environ, {"TB_LAB_ATENDIMENTO_JSON": caminho}), \
         patch.object(preparar, "_lab_isolado", return_value=True), \
         patch.object(preparar.subprocess, "run") as executar:
        assert preparar.main() == 1
        executar.assert_not_called()


RUBY_FALSO = """
require "json"
require "ostruct"
class InboxesSinteticos
  def find_by!(**kwargs)
    OpenStruct.new(id: 1, channel: OpenStruct.new(identifier: "inbox-sintetico"))
  end
end
class Account
  def self.find_by(**kwargs)
    OpenStruct.new(id: 1, inboxes: InboxesSinteticos.new)
  end
end
class User
  def self.find_by!(**kwargs)
    OpenStruct.new(access_token: OpenStruct.new(token: "token-sintetico"))
  end
end
"""


@pytest.mark.skipif(shutil.which("ruby") is None, reason="Ruby local indisponível")
@pytest.mark.parametrize("preexistente", ["novo", "arquivo", "symlink"])
def test_runner_ruby_cria_0600_sem_sobrescrever_ou_seguir_symlink(tmp_path, preexistente):
    arquivo = tmp_path / "fixture.json"
    alvo = tmp_path / "alvo.json"
    if preexistente == "arquivo":
        arquivo.write_text("preservar", encoding="utf-8")
    elif preexistente == "symlink":
        alvo.write_text("preservar", encoding="utf-8")
        arquivo.symlink_to(alvo)
    resultado = subprocess.run(
        ["ruby", "-"], input=RUBY_FALSO + preparar.RUBY,
        text=True, capture_output=True, timeout=10,
        env={**os.environ, "TB_LAB_ATENDIMENTO_JSON": str(arquivo)},
    )
    if preexistente == "novo":
        assert resultado.returncode == 0, resultado.stderr
        assert stat.S_IMODE(arquivo.stat().st_mode) == 0o600
        assert json.loads(arquivo.read_text())["token"] == "token-sintetico"
        assert "token-sintetico" not in resultado.stdout
    else:
        assert resultado.returncode != 0
        assert arquivo.read_text() == "preservar"
        if preexistente == "symlink":
            assert alvo.read_text() == "preservar"
