"""Erros estáveis e sanitizados do núcleo do MCP OPS."""

from __future__ import annotations


class ErroOps(Exception):
    """Erro esperado do contrato; nunca carrega argumentos ou credenciais."""

    codigo = "erro_ops"

    def __init__(self, mensagem: str | None = None) -> None:
        super().__init__(mensagem or self.codigo)


class ErroValidacao(ErroOps):
    codigo = "validacao"


class NaoAutenticado(ErroOps):
    codigo = "nao_autenticado"


class PermissaoAdministrativaNegada(ErroOps):
    codigo = "permissao_administrativa_negada"


class ClienteNaoConfigurado(ErroOps):
    codigo = "cliente_nao_configurado"


class ClienteJaAtivo(ErroOps):
    codigo = "cliente_ja_ativo"


class AgenteJaAtivo(ErroOps):
    codigo = "agente_ja_ativo"


class AutorizacaoInvalida(ErroOps):
    codigo = "autorizacao_invalida"


class AutorizacaoJaUtilizada(ErroOps):
    codigo = "autorizacao_ja_utilizada"


class AutorizacaoRevogada(ErroOps):
    codigo = "autorizacao_revogada"


class IdentidadeNaoVinculada(ErroOps):
    codigo = "identidade_nao_vinculada"


class FuncoesDivergentes(ErroOps):
    codigo = "funcoes_divergentes"


class FuncaoDesconhecida(ErroOps):
    codigo = "funcao_desconhecida"


class TokenInvalido(ErroOps):
    codigo = "token_invalido"


class TokenRevogado(ErroOps):
    codigo = "token_revogado"


class SessaoEncerrada(ErroOps):
    codigo = "sessao_encerrada"


class ManifestoDivergente(ErroOps):
    codigo = "manifesto_divergente"


class ConfirmacaoPendente(ErroOps):
    codigo = "confirmacao_pendente"


class ForaDaAtribuicao(ErroOps):
    codigo = "fora_da_atribuicao"


class AreaOcupada(ErroOps):
    codigo = "area_ocupada"

    def __init__(self, area: str) -> None:
        self.area = area
        super().__init__(f"area_ocupada:{area}")


class LeasePerdido(ErroOps):
    codigo = "lease_perdido"


class AprovacaoExataNecessaria(ErroOps):
    """O núcleo não executa ação crítica sem um fluxo externo de aprovação."""

    codigo = "aprovacao_exata_necessaria"


class FuncaoIndisponivel(ErroOps):
    codigo = "funcao_indisponivel"


class ErroFerramenta(ErroOps):
    codigo = "erro_ferramenta"
