#!/usr/bin/env python3
"""Valida JSON dos contratos F4.

Um CLI, três subcomandos (em vez de três scripts quase iguais):

    python scripts/validate_contratos.py publicacao peca.json
    python scripts/validate_contratos.py criativo < criativo.json
    python scripts/validate_contratos.py lead ficha.json

Exit codes:
    0 — JSON válido (o modelo sai em stdout)
    1 — JSON inválido ou arquivo ilegível (erro em stderr)
    2 — uso incorreto
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pydantic import ValidationError

from tuttibom.contratos import Criativo, Lead, Publicacao

MODELOS = {
    "publicacao": Publicacao,
    "criativo": Criativo,
    "lead": Lead,
}


def ler_json(caminho: str | None) -> object:
    if caminho:
        arquivo = Path(caminho)
        if not arquivo.is_file():
            raise FileNotFoundError(caminho)
        with arquivo.open(encoding="utf-8") as handle:
            return json.load(handle)
    return json.load(sys.stdin)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Valida JSON de contrato TuttiBom.")
    parser.add_argument("contrato", choices=sorted(MODELOS))
    parser.add_argument(
        "arquivo",
        nargs="?",
        help="Caminho do JSON. Sem este argumento, lê stdin.",
    )
    args = parser.parse_args(argv)
    try:
        dados = ler_json(args.arquivo)
        modelo = MODELOS[args.contrato].model_validate(dados)
    except FileNotFoundError:
        print(f"Erro: arquivo não encontrado: {args.arquivo}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Erro ao decodificar JSON: {exc}", file=sys.stderr)
        return 1
    except ValidationError as exc:
        print("JSON inválido:", file=sys.stderr)
        print(exc, file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Erro inesperado: {exc}", file=sys.stderr)
        return 1

    print("JSON válido", file=sys.stderr)
    print(modelo.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
