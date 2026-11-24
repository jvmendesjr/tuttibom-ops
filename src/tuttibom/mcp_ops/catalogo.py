"""Catálogo administrativo estável do MCP OPS.

IDs são contrato permanente: nunca renumerar nem reaproveitar. A seleção é
sempre por função; não existe seleção por área ou pacote implícito.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .erros import ErroValidacao, FuncaoDesconhecida


class Risco(str, Enum):
    SEGURO = "seguro"
    ATENCAO = "atencao"
    CRITICO = "critico"


@dataclass(frozen=True, slots=True)
class Funcao:
    id: str
    area: str
    nome: str
    ferramenta: str
    risco: Risco
    escrita: bool = False

    def como_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "area": self.area,
            "nome": self.nome,
            "ferramenta": self.ferramenta,
            "risco": self.risco.value,
            "escrita": self.escrita,
            **({"ferramentas_auxiliares": list(AUXILIARES[self.id])} if self.id in AUXILIARES else {}),
        }


AREAS: dict[str, str] = {
    "01": "Atendimento",
    "02": "CRM e Vendas",
    "03": "Produto e Catálogo",
    "04": "Criativos e Mídia",
    "05": "Social e Conteúdo",
    "06": "Anúncios, Aquisição e Concorrência",
    "07": "Operação, Produção e Pagamento",
    "08": "Plataforma e Manutenção",
}

AUXILIARES = {
    "01.01": ("ops_atendimento_listar_pendencias", "ops_ler_skill"),
    "01.02": ("ops_atendimento_preparar_resposta", "ops_ler_skill"),
    "03.01": ("ops_ler_skill",),
}


def _f(
    id: str,
    nome: str,
    ferramenta: str,
    risco: Risco,
    escrita: bool = False,
) -> Funcao:
    return Funcao(id, id[:2], nome, ferramenta, risco, escrita)


CATALOGO: tuple[Funcao, ...] = (
    _f("01.01", "Ler conversa", "ops_atendimento_ler_conversa", Risco.SEGURO),
    _f("01.02", "Responder no atendimento", "ops_atendimento_responder", Risco.CRITICO, True),
    _f("02.01", "Registrar lead", "ops_crm_registrar_lead", Risco.ATENCAO, True),
    _f("02.02", "Mover etapa", "ops_crm_mover_etapa", Risco.ATENCAO, True),
    _f("02.03", "Registrar resumo de mensagem", "ops_crm_registrar_mensagem", Risco.ATENCAO, True),
    _f("02.04", "Programar follow-up", "ops_crm_followup", Risco.ATENCAO, True),
    _f("02.05", "Registrar rótulo de interesse", "ops_crm_memoria_contato", Risco.ATENCAO, True),
    _f("03.01", "Consultar produto", "ops_produto_consultar", Risco.SEGURO),
    _f("04.01", "Listar criativos aprovados", "ops_criativo_listar_aprovados", Risco.SEGURO),
    _f("04.02", "Gerar prévia de criativo", "ops_criativo_gerar_previa", Risco.ATENCAO, True),
    _f("05.01", "Criar rascunho de post", "ops_social_rascunho_post", Risco.ATENCAO, True),
    _f("05.02", "Publicar post", "ops_social_publicar", Risco.CRITICO, True),
    _f("06.01", "Consultar concorrência", "ops_anuncio_consultar_concorrencia", Risco.SEGURO),
    _f("07.01", "Registrar pedido", "ops_operacao_registrar_pedido", Risco.ATENCAO, True),
    _f("07.02", "Confirmar pagamento", "ops_operacao_confirmar_pagamento", Risco.ATENCAO, True),
    _f("08.01", "Consultar saúde da plataforma", "ops_plataforma_saude", Risco.SEGURO),
    _f("08.02", "Consultar logs sanitizados", "ops_plataforma_logs", Risco.SEGURO),
    _f("08.03", "Reindexar plataforma", "ops_plataforma_reindex", Risco.ATENCAO, True),
)

POR_ID: dict[str, Funcao] = {funcao.id: funcao for funcao in CATALOGO}
POR_FERRAMENTA: dict[str, Funcao] = {
    funcao.ferramenta: funcao for funcao in CATALOGO
}

assert len(POR_ID) == len(CATALOGO), "IDs de função devem ser únicos"
assert len(POR_FERRAMENTA) == len(CATALOGO), "Nomes de ferramenta devem ser únicos"
assert all(funcao.area in AREAS for funcao in CATALOGO)


def normalizar_funcoes(funcoes: Iterable[str] | str) -> tuple[str, ...]:
    """Valida seleção explícita e devolve IDs únicos na ordem do catálogo."""
    if isinstance(funcoes, str):
        brutos = funcoes.split(",")
    else:
        try:
            brutos = list(funcoes)
        except TypeError as exc:
            raise ErroValidacao("funcoes_devem_ser_uma_selecao") from exc
    if not brutos:
        raise ErroValidacao("selecao_vazia")
    ids: list[str] = []
    for bruto in brutos:
        if not isinstance(bruto, str):
            raise ErroValidacao("id_de_funcao_invalido")
        id = bruto.strip()
        if not id or id not in POR_ID:
            raise FuncaoDesconhecida()
        if id in ids:
            raise ErroValidacao("funcao_duplicada")
        ids.append(id)
    escolhidos = set(ids)
    return tuple(funcao.id for funcao in CATALOGO if funcao.id in escolhidos)


def funcao_por_id(id: str) -> Funcao:
    if not isinstance(id, str) or id not in POR_ID:
        raise FuncaoDesconhecida()
    return POR_ID[id]
