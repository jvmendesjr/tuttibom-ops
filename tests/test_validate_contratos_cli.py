"""O CLI rejeita preço inventado e aceita o texto do piloto."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _rodar(contrato, payload):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_contratos.py"), contrato],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_aceita_o_piloto(publicacao_piloto):
    resultado = _rodar("publicacao", publicacao_piloto)
    assert resultado.returncode == 0, resultado.stderr
    assert "JSON válido" in resultado.stderr
    assert "Cariri" in resultado.stdout


def test_cli_rejeita_preco_inventado(publicacao_piloto):
    publicacao_piloto["texto_exato"] = "Fita por apenas R$ 99,90."
    resultado = _rodar("publicacao", publicacao_piloto)
    assert resultado.returncode == 1
    assert "preço" in resultado.stderr


def test_cli_uso_errado():
    resultado = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_contratos.py")],
        text=True,
        capture_output=True,
        check=False,
    )
    assert resultado.returncode == 2
