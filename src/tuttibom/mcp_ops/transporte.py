"""Interface MCP do Ops. A conexão recebe seu cliente do host, não do chat."""
from __future__ import annotations

import base64
import json
from dataclasses import asdict
from functools import partial

from jsonschema import ValidationError, validate
from mcp import types
from mcp.server import NotificationOptions, Server

from .erros import ErroOps, ForaDaAtribuicao, NaoAutenticado
from .laboratorio import Laboratorio, RecusaLab
from .nucleo import ClienteConfigurado, SessaoOps
from .skills_operacionais import skills_para_funcao

NOME = "tuttibom-ops-mcp"
VERSAO = "0.1.0"


def _texto(maximo: int = 128) -> dict:
    return {"type": "string", "minLength": 1, "maxLength": maximo}


_LIMITE = {"type": "integer", "minimum": 1, "maximum": 100}


def _lista(item: dict, maximo: int) -> dict:
    return {"type": "array", "items": item, "maxItems": maximo, "uniqueItems": True}


def _tool(nome: str, descricao: str, campos: dict | None = None, *obrigatorios: str) -> types.Tool:
    return types.Tool(name=nome, description=descricao, inputSchema={
        "type": "object", "properties": campos or {},
        "required": list(obrigatorios), "additionalProperties": False,
    })


BOOTSTRAP = [
    _tool("ops_ativar", "Ativa a referência já autorizada, com a seleção exata de IDs.", {
        "referencia": _texto(), "funcoes": {**_lista(_texto(5), 18), "minItems": 1},
    }, "referencia", "funcoes"),
    _tool("ops_reconectar", "Reabre a sessão do cliente já ativado. Confirme o manifesto novamente."),
]

SESSAO = [
    _tool("ops_minhas_atribuicoes", "Retorna as funções e os IDs das skills deste manifesto. Leia as skills em ops_ler_skill e confirme o escopo antes de operar."),
    _tool("ops_confirmar_atribuicoes", "Confirma o manifesto e solicita exclusividade para escrita.", {
        "manifesto_hash": _texto(64), "resumo": _texto(4000),
    }, "manifesto_hash", "resumo"),
    _tool("ops_estado", "Informa confirmação e áreas com escrita exclusiva da sessão."),
    _tool("ops_auditoria", "Consulta apenas a auditoria sanitizada da própria sessão.", {"limite": _LIMITE}),
]

OPERACAO = [
    ("01.01", "fila", _tool("ops_atendimento_listar_pendencias", "Lista eventos pendentes sem confirmar entrega.", {
        "limite": _LIMITE, "inbox_id": _texto(),
    })),
    ("01.01", "executar", _tool("ops_atendimento_ler_conversa", "Lê histórico, imagens e transcrições.", {
        "conversa_ref": _texto(), "inbox_id": _texto(),
    }, "conversa_ref")),
    ("01.02", "preparar", _tool("ops_atendimento_preparar_resposta", "Cria rascunho. Não envia nem aprova.", {
        "conversa_ref": _texto(), "texto": _texto(8000), "inbox_id": _texto(),
        "idempotency_key": _texto(), "message_ids": {**_lista(_texto(), 100), "minItems": 1},
        "imagem_ref": _texto(), "imagens_lidas": _lista(_texto(64), 100),
    }, "conversa_ref", "texto", "idempotency_key", "message_ids")),
    ("01.02", "executar", _tool("ops_atendimento_responder", "Envia só o rascunho aprovado para esta sessão.", {
        "rascunho_ref": _texto(), "aprovacao_ref": _texto(),
    }, "rascunho_ref")),
    ("03.01", "executar", _tool("ops_produto_consultar", "Consulta o preço versionado do SKU, sem negociar ou confirmar estoque.", {
        "sku": _texto(64),
    }, "sku")),
]
_SKILL = _tool("ops_ler_skill", "Lê a skill operacional pelo ID publicado no manifesto desta sessão.", {
    "id": _texto(64),
}, "id")
_OPERACAO = {tool.name: (id_, etapa) for id_, etapa, tool in OPERACAO}
_SCHEMAS = {tool.name: tool.inputSchema for tool in BOOTSTRAP + SESSAO + [_SKILL] + [op[2] for op in OPERACAO]}


def _mime_imagem(conteudo: bytes) -> str:
    if conteudo.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(conteudo) > 12 and conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def _resultado(dados: dict) -> types.CallToolResult:
    imagens = []
    for msg in dados.get("mensagens", ()):
        for anexo in msg["anexos"]:
            if anexo["file_type"] == "image":
                bruto = anexo.pop("conteudo")
                anexo["bloco_mcp"] = len(imagens)
                imagens.append(types.ImageContent(
                    type="image", mimeType=_mime_imagem(bruto),
                    data=base64.b64encode(bruto).decode("ascii"),
                ))
    return types.CallToolResult(
        content=[*imagens, types.TextContent(type="text", text=json.dumps(dados, ensure_ascii=False))],
        structuredContent=dados, isError=dados.get("ok") is False,
    )


class Conexao:
    def __init__(self, lab: Laboratorio, cliente: ClienteConfigurado, *,
                 preconfigurada: bool = False) -> None:
        self._lab = lab
        self._cliente = cliente
        self._preconfigurada = preconfigurada
        self._sessao: SessaoOps | None = None
        self._skills_lidas: set[tuple[str, str]] = set()
        ambiente = getattr(lab, "ambiente", "laboratorio")
        prefixo = "Operação TuttiBom. " if ambiente == "operacao" else "Laboratório sintético. "
        self.mcp = Server(
            NOME, version=VERSAO,
            instructions=(
                prefixo
                + ("Consulte suas atribuições em ops_minhas_atribuicoes, "
                   if preconfigurada else "Use a autorização fornecida pelo operador, ")
                + "confira o manifesto, leia suas skills e confirme o escopo. "
                "Só envie o rascunho exato com aprovação registrada pelo operador."
            ),
        )
        self.mcp.list_tools()(self.listar)
        self.mcp.call_tool(validate_input=False)(self.chamar)

    def opcoes(self):
        return self.mcp.create_initialization_options(NotificationOptions(tools_changed=True))

    def fechar(self) -> None:
        if self._sessao is not None:
            self._lab.limpar_sessao(self._sessao)

    def _abrir_preconfigurada(self) -> None:
        if self._preconfigurada and self._sessao is None:
            self._sessao = self._cliente.conectar()

    async def listar(self) -> list[types.Tool]:
        if not self._preconfigurada and self._sessao is None:
            return BOOTSTRAP
        try:
            self._abrir_preconfigurada()
            ids = {funcao.id for funcao in self._sessao.manifesto().funcoes}
        except ErroOps:
            return [] if self._preconfigurada else SESSAO
        skills = [_SKILL] if any(skills_para_funcao(id_) for id_ in ids) else []
        return SESSAO + skills + [tool for id_, _, tool in OPERACAO if id_ in ids]

    async def chamar(self, nome: str, argumentos: dict) -> types.CallToolResult:
        try:
            bootstrap = nome in {"ops_ativar", "ops_reconectar"}
            if nome not in _SCHEMAS or (self._preconfigurada and bootstrap):
                raise ForaDaAtribuicao()
            self._abrir_preconfigurada()
            if self._sessao is None and not bootstrap:
                raise NaoAutenticado()
            validate(instance=argumentos, schema=_SCHEMAS[nome])
            dados = await self._despachar(nome, argumentos)
        except ValidationError:
            dados = {"ok": False, "codigo": "argumento_invalido"}
        except ErroOps as exc:
            dados = {"ok": False, "codigo": exc.codigo}
        return _resultado(dados)

    async def _despachar(self, nome: str, args: dict) -> dict:
        if nome in {"ops_ativar", "ops_reconectar"}:
            if self._sessao is not None:
                raise RecusaLab("sessao_ja_iniciada")
            recibo = self._cliente.ativar(**args) if nome == "ops_ativar" else None
            self._sessao = self._cliente.conectar()
            await self.mcp.request_context.session.send_tool_list_changed()
            return {"ok": True, "ambiente": getattr(self._lab, "ambiente", "laboratorio"),
                    "manifesto": self._sessao.manifesto().como_dict(),
                    **({"recibo": asdict(recibo)} if recibo is not None else {})}
        sessao = self._sessao
        if sessao is None:
            raise NaoAutenticado()
        if nome == "ops_minhas_atribuicoes":
            return sessao.manifesto().como_dict()
        if nome == "ops_ler_skill":
            for funcao in sessao.manifesto().funcoes:
                if any(skill.id == args["id"] for skill in skills_para_funcao(funcao.id)):
                    resultado = sessao.chamar(funcao.id, args, etapa="skill")
                    if resultado["ok"]:
                        self._skills_lidas.add((resultado["id"], resultado["versao"]))
                    return resultado
            raise RecusaLab("skill_indisponivel_no_escopo")
        if nome == "ops_confirmar_atribuicoes":
            manifesto = sessao.manifesto()
            if args["manifesto_hash"] == manifesto.hash:
                exigidas = {
                    (skill.id, skill.versao)
                    for funcao in manifesto.funcoes for skill in skills_para_funcao(funcao.id)
                }
                if not self._skills_lidas.issuperset(exigidas):
                    raise RecusaLab("skills_pendentes")
            return sessao.confirmar_atribuicoes(**args)
        if nome == "ops_estado":
            return sessao.estado()
        if nome == "ops_auditoria":
            return {"eventos": sessao.auditoria(**args)}
        id_, etapa = _OPERACAO[nome]
        return sessao.chamar(id_, args, etapa=etapa,
                             exigir_confirmacao=self._preconfigurada)
