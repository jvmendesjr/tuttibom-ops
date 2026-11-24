"""Entrega somente SKILL.md explicitamente vinculado a uma função."""
from dataclasses import dataclass
from functools import cache
from hashlib import sha256
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[3] / "skills"
_POR_FUNCAO = {
    "01.01": ("ops-ana-atendimento", "ops-ana-triagem"),
    "01.02": ("ops-ana-atendimento", "ops-ana-resposta"),
    "03.01": ("ops-produto-consulta",),
}
_PAPEIS = {"01": "Ana", "03": "Especialista de Produto e Catálogo"}


@dataclass(frozen=True)
class Skill:
    id: str
    versao: str
    conteudo: str

    def referencia(self) -> dict[str, str]:
        return {"id": self.id, "versao": self.versao}


@cache
def _carregar(id_: str) -> Skill:
    caminho = _RAIZ / id_ / "SKILL.md"
    if caminho.resolve() != caminho or not caminho.is_file():
        raise ValueError("skill_operacional_invalida")
    bruto = caminho.read_bytes()
    conteudo = bruto.decode("utf-8")
    abertura, separador, restante = conteudo.removeprefix("---\n").partition("\n---\n")
    if (
        not conteudo.startswith("---\n") or not separador or not restante.strip()
        or f"name: {id_}" not in abertura.splitlines()
    ):
        raise ValueError("skill_operacional_invalida")
    return Skill(id_, sha256(bruto).hexdigest(), conteudo)


def skills_para_funcao(funcao: str) -> tuple[Skill, ...]:
    return tuple(_carregar(id_) for id_ in _POR_FUNCAO.get(funcao, ()))


def papeis_para_funcoes(funcoes: tuple[str, ...]) -> list[dict]:
    por_area: dict[str, dict[str, None]] = {}
    for funcao in funcoes:
        ids = _POR_FUNCAO.get(funcao)
        if ids:
            por_area.setdefault(funcao[:2], {}).update(dict.fromkeys(ids))
    return [
        {"area": area, "persona": _PAPEIS[area], "skills": list(ids)}
        for area, ids in por_area.items()
    ]
