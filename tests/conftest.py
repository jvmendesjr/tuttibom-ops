"""Apoio dos testes F4. Coloca src/ no path antes dos imports do pacote."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pytest

from tuttibom.contratos.publicacao import TEXTO_PILOTO


@pytest.fixture
def publicacao_piloto():
    return {
        "texto_exato": TEXTO_PILOTO,
        "texto_aprovado": True,
        "arte": "piloto-feed-2026-11-01",
        "formato": "4:5",
        "rede": "facebook",
        "data": "2026-11-01",
        "rotulo_ia": True,
        "foto_de_cliente": False,
    }


@pytest.fixture
def criativo_piloto():
    return {
        "formato": "9:16",
        "textos": [
            {"conteudo": "Ateliê Celebra", "legivel": True},
            {"conteudo": "Lembrança Especial", "legivel": True},
        ],
        "zonas_seguras": {
            "topo_px": 220,
            "base_px": 380,
            "direita_px": 140,
            "texto_na_zona_morta": False,
        },
        "botao_a": {"rotulo": "A: Dourado Metalizado", "legivel": True},
        "botao_b": {"rotulo": "B: Prata Elegante", "legivel": True},
    }


@pytest.fixture
def lead_novo():
    return {
        "referencia": "lead-001",
        "estagio": "Novo",
        "produto": "FITA-22-50-PRETO",
        "proxima_acao": "Confirmar largura 15 mm ou 22 mm e metragem 10, 25 ou 50 m",
        "data_followup": "2026-11-18",
        "observacao": "Cidade: Juazeiro do Norte. Retorno em 2026-11-18.",
    }
