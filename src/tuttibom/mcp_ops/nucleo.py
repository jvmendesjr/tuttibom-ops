"""Núcleo administrativo e de sessões do ``tuttibom-ops-mcp``.

O transporte e os backends são injetados. Funções críticas só podem ser
executadas por um fluxo servidor que verifique a aprovação exata.
"""

from __future__ import annotations

import json
import re
import secrets
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .auditoria import json_canonico, sanitizar, sha256_texto
from .catalogo import (
    AREAS,
    CATALOGO,
    Funcao,
    Risco,
    funcao_por_id,
    normalizar_funcoes,
)
from .erros import (
    AgenteJaAtivo,
    AprovacaoExataNecessaria,
    AreaOcupada,
    AutorizacaoInvalida,
    AutorizacaoJaUtilizada,
    AutorizacaoRevogada,
    ClienteJaAtivo,
    ClienteNaoConfigurado,
    ConfirmacaoPendente,
    ErroFerramenta,
    ErroOps,
    ErroValidacao,
    ForaDaAtribuicao,
    FuncaoIndisponivel,
    FuncoesDivergentes,
    IdentidadeNaoVinculada,
    LeasePerdido,
    ManifestoDivergente,
    NaoAutenticado,
    PermissaoAdministrativaNegada,
    SessaoEncerrada,
    TokenInvalido,
    TokenRevogado,
)
from .identidade import (
    FronteiraIdentidade,
    IdentidadeVerificada,
    validar_identificador,
)
from .persistencia import BancoOps
from .skills_operacionais import papeis_para_funcoes, skills_para_funcao

Handler = Callable[[Mapping[str, Any]], Any]
Fluxo = Callable[["SessaoOps", str, Mapping[str, Any]], Any]
_REFERENCIA = re.compile(r"^aut_[0-9a-f]{32}$")
_TOKEN_ID = re.compile(r"^tok_[0-9a-f]{32}$")


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _dados_manifesto(agente_id: str, ids: Iterable[str]) -> dict[str, Any]:
    ids = tuple(ids)
    por_funcao = {id_: skills_para_funcao(id_) for id_ in ids}
    funcoes = [
        {**funcao_por_id(id_).como_dict(), "skills": [skill.id for skill in skills]}
        for id_, skills in por_funcao.items()
    ]
    referencias = {skill.id: skill.referencia() for skills in por_funcao.values() for skill in skills}
    return {
        "versao": 2,
        "agente_id": agente_id,
        "areas": {id: AREAS[id] for id in sorted({f["area"] for f in funcoes})},
        "funcoes": funcoes,
        "skills": list(referencias.values()),
        "papeis": papeis_para_funcoes(ids),
        "nucleo": [
            "ops_minhas_atribuicoes",
            "ops_confirmar_atribuicoes",
            "ops_estado",
            "ops_auditoria",
        ],
        "limites": {
            "leitura": "somente_funcoes_atribuidas",
            "escrita": "manifesto_confirmado_e_lease_da_area",
            "critico": "aprovacao_exata_no_servidor",
        },
        "lease_sem_prazo_fixo": True,
    }


def _hash_manifesto(agente_id: str, ids: Iterable[str]) -> str:
    return sha256_texto(json_canonico(_dados_manifesto(agente_id, ids)))


@dataclass(frozen=True, slots=True)
class Autorizacao:
    referencia: str
    agente_id: str
    cliente_id: str
    funcoes: tuple[str, ...]
    manifesto_hash: str


@dataclass(frozen=True, slots=True)
class ReciboAtivacao:
    """Recibo não secreto. O token bruto nunca aparece neste retorno."""

    token_id: str
    agente_id: str
    manifesto_hash: str


@dataclass(frozen=True, slots=True)
class Manifesto:
    agente_id: str
    funcoes: tuple[Funcao, ...]
    hash: str
    lease_sem_prazo_fixo: bool = True

    def como_dict(self) -> dict[str, Any]:
        dados = _dados_manifesto(self.agente_id, [f.id for f in self.funcoes])
        dados["hash"] = self.hash
        return dados


class ClienteConfigurado:
    """Capability criada pelo servidor; o token fica fora do repr e dos recibos."""

    def __init__(self, servidor: ServidorOps, cliente_id: str) -> None:
        self._servidor = servidor
        self._cliente_id = validar_identificador(cliente_id, "cliente_id")
        self._token: str | None = None
        self._lock = threading.RLock()

    @property
    def cliente_id(self) -> str:
        return self._cliente_id

    def ativar(
        self,
        referencia: str,
        funcoes: Iterable[str] | str,
    ) -> ReciboAtivacao:
        return self._servidor._ativar(self, referencia, funcoes)

    def conectar(self) -> SessaoOps:
        with self._lock:
            token = self._token
        if token is None:
            raise TokenInvalido()
        return self._servidor._conectar(self, token)

    def _receber_token(self, token: str) -> None:
        with self._lock:
            self._token = token

    def _limpar_token(self, token: str) -> None:
        with self._lock:
            if self._token == token:
                self._token = None

    def __repr__(self) -> str:
        return f"ClienteConfigurado(cliente_id={self._cliente_id!r})"


class AdministradorOps:
    """Cliente administrativo autenticado pela mesma fronteira do servidor."""

    def __init__(self, servidor: ServidorOps, cliente_id: str) -> None:
        self._servidor = servidor
        self._cliente_id = validar_identificador(cliente_id, "cliente_id")

    @property
    def cliente_id(self) -> str:
        return self._cliente_id

    def listar_atribuicoes(self) -> tuple[Funcao, ...]:
        return self._servidor._listar_atribuicoes(self)

    def autorizar(
        self,
        *,
        agente_id: str,
        cliente: ClienteConfigurado,
        funcoes: Iterable[str] | str,
    ) -> Autorizacao:
        return self._servidor._autorizar(self, agente_id, cliente, funcoes)

    def revogar_agente(self, agente_id: str) -> int:
        return self._servidor._revogar_agente(self, agente_id)

    def revogar_token(self, token_id: str) -> bool:
        return self._servidor._revogar_token(self, token_id)

    def auditoria(self, limite: int = 100) -> list[dict[str, Any]]:
        return self._servidor._auditoria_admin(self, limite)


class SessaoOps:
    """Uma conexão; cada reconexão exige nova confirmação do manifesto."""

    def __init__(self, servidor: ServidorOps, sessao_id: str, token_id: str) -> None:
        self._servidor = servidor
        self._id = sessao_id
        self._token_id = token_id

    @property
    def id(self) -> str:
        return self._id

    def manifesto(self) -> Manifesto:
        return self._servidor._manifesto(self)

    def minhas_atribuicoes(self) -> Manifesto:
        return self._servidor._manifesto(self)

    def confirmar_atribuicoes(self, manifesto_hash: str, resumo: str) -> dict[str, Any]:
        return self._servidor._confirmar(self, manifesto_hash, resumo)

    def estado(self) -> dict[str, Any]:
        return self._servidor._estado_sessao(self)

    def chamar(
        self, funcao_id: str, argumentos: Mapping[str, Any] | None = None,
        *, etapa: str = "executar", exigir_confirmacao: bool = False,
    ) -> Any:
        return self._servidor._chamar(self, funcao_id, argumentos, etapa,
                                     exigir_confirmacao=exigir_confirmacao)

    def auditoria(self, limite: int = 100) -> list[dict[str, Any]]:
        return self._servidor._auditoria_propria(self, limite)

    def desconectar(self) -> bool:
        return self._servidor._desconectar(self)

    def __repr__(self) -> str:
        return f"SessaoOps(id={self._id!r})"


class ServidorOps:
    """Serviço local com enforcement no servidor em todas as operações."""

    def __init__(
        self,
        caminho_banco: str | Path,
        fronteira_identidade: FronteiraIdentidade,
        *,
        handlers: Mapping[str, Handler] | None = None,
        fluxos: Mapping[str, Fluxo] | None = None,
        gerador_token: Callable[[], str] | None = None,
    ) -> None:
        self._banco = BancoOps(caminho_banco)
        self._fronteira = fronteira_identidade
        self._handlers = dict(handlers or {})
        self._fluxos = dict(fluxos or {})
        self._gerador_token = gerador_token or (
            lambda: f"ops_{uuid.uuid4().hex[:12]}_{secrets.token_urlsafe(32)}"
        )
        self._clientes: dict[str, ClienteConfigurado] = {}
        self._admins: dict[str, AdministradorOps] = {}
        self._registro_lock = threading.RLock()

    def close(self) -> None:
        self._banco.close()

    def configurar_cliente(self, cliente_id: str) -> ClienteConfigurado:
        validar_identificador(cliente_id, "cliente_id")
        self._verificar_identidade(cliente_id)
        with self._registro_lock:
            existente = self._clientes.get(cliente_id)
            if existente is not None:
                return existente
            cliente = ClienteConfigurado(self, cliente_id)
            self._clientes[cliente_id] = cliente
            return cliente

    def configurar_administrador(self, cliente_id: str) -> AdministradorOps:
        validar_identificador(cliente_id, "cliente_id")
        identidade = self._verificar_identidade(cliente_id)
        if not identidade.administrador:
            raise PermissaoAdministrativaNegada()
        with self._registro_lock:
            existente = self._admins.get(cliente_id)
            if existente is not None:
                return existente
            admin = AdministradorOps(self, cliente_id)
            self._admins[cliente_id] = admin
            return admin

    def _verificar_identidade(self, cliente_id: str) -> IdentidadeVerificada:
        identidade = self._fronteira.verificar(cliente_id)
        if (
            not isinstance(identidade, IdentidadeVerificada)
            or identidade._fronteira is not self._fronteira
        ):
            raise NaoAutenticado()
        return identidade

    def _cliente_valido(self, cliente: ClienteConfigurado) -> None:
        if (
            not isinstance(cliente, ClienteConfigurado)
            or cliente._servidor is not self
            or self._clientes.get(cliente._cliente_id) is not cliente
        ):
            raise ClienteNaoConfigurado()

    def _admin_valido(self, admin: AdministradorOps) -> None:
        if (
            not isinstance(admin, AdministradorOps)
            or admin._servidor is not self
            or self._admins.get(admin._cliente_id) is not admin
        ):
            raise PermissaoAdministrativaNegada()
        if not self._verificar_identidade(admin._cliente_id).administrador:
            raise PermissaoAdministrativaNegada()

    def _auditar_conn(
        self,
        conn: sqlite3.Connection,
        *,
        ator_tipo: str,
        acao: str,
        ator_id: str | None = None,
        agente_id: str | None = None,
        token_id: str | None = None,
        sessao_id: str | None = None,
        area: str | None = None,
        funcao_id: str | None = None,
        argumentos: Any = None,
        resultado: Any = None,
        erro: str | None = None,
    ) -> None:
        if sessao_id and not token_id:
            row = conn.execute(
                "SELECT token_id FROM sessoes WHERE id = ?", (sessao_id,)
            ).fetchone()
            token_id = row["token_id"] if row else None
        if token_id and not agente_id:
            row = conn.execute(
                "SELECT agente_id FROM tokens WHERE id = ?", (token_id,)
            ).fetchone()
            agente_id = row["agente_id"] if row else None
        conn.execute(
            "INSERT INTO auditoria (criado_em, ator_tipo, ator_id, agente_id,"
            " token_id, sessao_id, area, funcao_id, acao, argumentos_json,"
            " resultado_json, erro_codigo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                _agora(), ator_tipo, ator_id, agente_id, token_id, sessao_id,
                area, funcao_id, acao,
                json_canonico(sanitizar({} if argumentos is None else argumentos)),
                json_canonico(sanitizar({} if resultado is None else resultado)),
                erro,
            ),
        )

    def _auditar(self, **kwargs: Any) -> None:
        with self._banco.transacao() as conn:
            self._auditar_conn(conn, **kwargs)

    def _listar_atribuicoes(self, admin: AdministradorOps) -> tuple[Funcao, ...]:
        self._admin_valido(admin)
        self._auditar(
            ator_tipo="admin", ator_id=admin._cliente_id,
            acao="catalogo_listar", resultado={"total": len(CATALOGO)},
        )
        return CATALOGO

    def _autorizar(
        self,
        admin: AdministradorOps,
        agente_id: str,
        cliente: ClienteConfigurado,
        funcoes: Iterable[str] | str,
    ) -> Autorizacao:
        self._admin_valido(admin)
        agente_auditado: str | None = None
        ids: tuple[str, ...] = ()
        try:
            self._cliente_valido(cliente)
            identidade = self._verificar_identidade(cliente._cliente_id)
            agente_id = validar_identificador(agente_id, "agente_id")
            agente_auditado = agente_id
            ids = normalizar_funcoes(funcoes)
            manifesto_hash = _hash_manifesto(agente_id, ids)
            referencia = f"aut_{uuid.uuid4().hex}"
            with self._banco.transacao() as conn:
                conn.execute(
                    "INSERT INTO autorizacoes (referencia, agente_id, cliente_id,"
                    " identidade_sujeito, funcoes_json, manifesto_hash, criado_em)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        referencia, agente_id, cliente._cliente_id, identidade.sujeito,
                        json_canonico(ids), manifesto_hash, _agora(),
                    ),
                )
                self._auditar_conn(
                    conn, ator_tipo="admin", ator_id=admin._cliente_id,
                    agente_id=agente_id, acao="autorizacao_criar",
                    argumentos={"cliente_id": cliente._cliente_id, "funcoes": ids},
                    resultado={"quantidade": len(ids)},
                )
            return Autorizacao(
                referencia, agente_id, cliente._cliente_id, ids, manifesto_hash
            )
        except ErroOps as exc:
            self._auditar(
                ator_tipo="admin", ator_id=admin._cliente_id,
                agente_id=agente_auditado, acao="autorizacao_criar",
                argumentos={"funcoes": ids}, erro=exc.codigo,
            )
            raise

    def _ativar(
        self,
        cliente: ClienteConfigurado,
        referencia: str,
        funcoes: Iterable[str] | str,
    ) -> ReciboAtivacao:
        self._cliente_valido(cliente)
        identidade = self._verificar_identidade(cliente._cliente_id)
        agente_id: str | None = None
        ids: tuple[str, ...] = ()
        token_id: str | None = None
        token: str | None = None
        try:
            if not isinstance(referencia, str) or not _REFERENCIA.fullmatch(referencia):
                raise AutorizacaoInvalida()
            ids = normalizar_funcoes(funcoes)
            candidato_token_id = f"tok_{uuid.uuid4().hex}"
            with self._banco.transacao() as conn:
                row = conn.execute(
                    "SELECT * FROM autorizacoes WHERE referencia = ?", (referencia,)
                ).fetchone()
                if row is None:
                    raise AutorizacaoInvalida()
                agente_id = row["agente_id"]
                if row["revogado_em"] is not None:
                    raise AutorizacaoRevogada()
                if row["consumido_em"] is not None:
                    raise AutorizacaoJaUtilizada()
                if (
                    row["cliente_id"] != cliente._cliente_id
                    or row["identidade_sujeito"] != identidade.sujeito
                ):
                    raise IdentidadeNaoVinculada()
                autorizadas = tuple(json.loads(row["funcoes_json"]))
                if autorizadas != ids:
                    raise FuncoesDivergentes()
                ativo = conn.execute(
                    "SELECT 1 FROM tokens WHERE cliente_id = ? AND revogado_em IS NULL",
                    (cliente._cliente_id,),
                ).fetchone()
                if ativo:
                    raise ClienteJaAtivo()
                agente_ativo = conn.execute(
                    "SELECT 1 FROM tokens WHERE agente_id = ? AND revogado_em IS NULL",
                    (agente_id,),
                ).fetchone()
                if agente_ativo:
                    raise AgenteJaAtivo()
                token = self._gerador_token()
                if (
                    not isinstance(token, str)
                    or not token.startswith("ops_")
                    or len(token) > 512
                    or any(c.isspace() for c in token)
                ):
                    raise ErroValidacao("gerador_de_token_invalido")
                token_id = candidato_token_id
                agora = _agora()
                atualizado = conn.execute(
                    "UPDATE autorizacoes SET consumido_em = ?"
                    " WHERE referencia = ? AND consumido_em IS NULL AND revogado_em IS NULL",
                    (agora, referencia),
                ).rowcount
                if atualizado != 1:
                    raise AutorizacaoJaUtilizada()
                conn.execute(
                    "INSERT INTO tokens (id, autorizacao_referencia, agente_id,"
                    " cliente_id, identidade_sujeito, token_hash, funcoes_json,"
                    " manifesto_hash, criado_em) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        token_id, referencia, agente_id, cliente._cliente_id,
                        identidade.sujeito, sha256_texto(token), row["funcoes_json"],
                        row["manifesto_hash"], agora,
                    ),
                )
                self._auditar_conn(
                    conn, ator_tipo="cliente", ator_id=cliente._cliente_id,
                    agente_id=agente_id, token_id=token_id, acao="ativacao",
                    argumentos={"funcoes": ids}, resultado={"ok": True},
                )
            try:
                cliente._receber_token(token)
            except Exception:
                with self._banco.transacao() as conn:
                    conn.execute(
                        "UPDATE tokens SET revogado_em = ? WHERE id = ?",
                        (_agora(), token_id),
                    )
                raise ClienteNaoConfigurado() from None
            return ReciboAtivacao(token_id, agente_id, row["manifesto_hash"])
        except ErroOps as exc:
            self._auditar(
                ator_tipo="cliente", ator_id=cliente._cliente_id,
                agente_id=agente_id, token_id=token_id, acao="ativacao",
                argumentos={"funcoes": ids}, erro=exc.codigo,
            )
            raise

    def _conectar(self, cliente: ClienteConfigurado, token: str) -> SessaoOps:
        self._cliente_valido(cliente)
        identidade = self._verificar_identidade(cliente._cliente_id)
        token_id: str | None = None
        try:
            token_hash = sha256_texto(token)
            sessao_id = f"ses_{uuid.uuid4().hex}"
            with self._banco.transacao() as conn:
                row = conn.execute(
                    "SELECT * FROM tokens WHERE token_hash = ?", (token_hash,)
                ).fetchone()
                if (
                    row is None
                    or row["cliente_id"] != cliente._cliente_id
                    or row["identidade_sujeito"] != identidade.sujeito
                ):
                    raise TokenInvalido()
                token_id = row["id"]
                if row["revogado_em"] is not None:
                    raise TokenRevogado()
                conn.execute(
                    "INSERT INTO sessoes (id, token_id, criado_em) VALUES (?, ?, ?)",
                    (sessao_id, token_id, _agora()),
                )
                self._auditar_conn(
                    conn, ator_tipo="agente", ator_id=cliente._cliente_id,
                    agente_id=row["agente_id"], token_id=token_id,
                    sessao_id=sessao_id, acao="conexao", resultado={"ok": True},
                )
            return SessaoOps(self, sessao_id, token_id)
        except ErroOps as exc:
            cliente._limpar_token(token)
            self._auditar(
                ator_tipo="cliente", ator_id=cliente._cliente_id,
                token_id=token_id, acao="conexao", erro=exc.codigo,
            )
            raise

    def _sessao_row(
        self, conn: sqlite3.Connection, sessao: SessaoOps
    ) -> sqlite3.Row:
        if not isinstance(sessao, SessaoOps) or sessao._servidor is not self:
            raise NaoAutenticado()
        row = conn.execute(
            "SELECT s.*, t.agente_id, t.cliente_id, t.identidade_sujeito,"
            " t.funcoes_json, t.manifesto_hash, t.revogado_em"
            " FROM sessoes s JOIN tokens t ON t.id = s.token_id"
            " WHERE s.id = ? AND s.token_id = ?",
            (sessao._id, sessao._token_id),
        ).fetchone()
        if row is None:
            raise SessaoEncerrada()
        if row["revogado_em"] is not None:
            raise TokenRevogado()
        if row["desconectado_em"] is not None:
            raise SessaoEncerrada()
        return row

    def _manifesto(self, sessao: SessaoOps) -> Manifesto:
        try:
            with self._banco.transacao() as conn:
                row = self._sessao_row(conn, sessao)
                ids = tuple(json.loads(row["funcoes_json"]))
                if _hash_manifesto(row["agente_id"], ids) != row["manifesto_hash"]:
                    raise ManifestoDivergente()
                manifesto = Manifesto(
                    row["agente_id"], tuple(funcao_por_id(id) for id in ids),
                    row["manifesto_hash"],
                )
                self._auditar_conn(
                    conn, ator_tipo="agente", ator_id=row["cliente_id"],
                    token_id=sessao._token_id, sessao_id=sessao._id,
                    acao="manifesto", resultado={"hash_manifesto": manifesto.hash},
                )
            return manifesto
        except ErroOps as exc:
            self._auditar(
                ator_tipo="agente", token_id=sessao._token_id,
                sessao_id=sessao._id, acao="manifesto", erro=exc.codigo,
            )
            raise

    def _confirmar(
        self, sessao: SessaoOps, manifesto_hash: str, resumo: str
    ) -> dict[str, Any]:
        resumo_hash: str | None = None
        try:
            with self._banco.transacao() as conn:
                row = self._sessao_row(conn, sessao)
                if manifesto_hash != row["manifesto_hash"]:
                    raise ManifestoDivergente()
                if not isinstance(resumo, str) or not resumo.strip() or len(resumo) > 4000:
                    raise ErroValidacao("resumo_de_confirmacao_invalido")
                resumo_hash = sha256_texto(resumo)
                ids = tuple(json.loads(row["funcoes_json"]))
                areas = sorted({
                    funcao_por_id(id).area for id in ids if funcao_por_id(id).escrita
                })
                for area in areas:
                    lease = conn.execute(
                        "SELECT sessao_id FROM leases WHERE area = ?", (area,)
                    ).fetchone()
                    if lease is not None and lease["sessao_id"] != sessao._id:
                        raise AreaOcupada(area)
                    if row["confirmado_em"] is not None and lease is None:
                        raise LeasePerdido()
                if row["confirmado_em"] is None:
                    agora = _agora()
                    conn.execute(
                        "UPDATE sessoes SET confirmado_em = ?,"
                        " manifesto_confirmado_hash = ?, resumo_sha256 = ?,"
                        " resumo_tamanho = ? WHERE id = ?",
                        (agora, manifesto_hash, resumo_hash, len(resumo), sessao._id),
                    )
                    for area in areas:
                        conn.execute(
                            "INSERT INTO leases (area, token_id, sessao_id, adquirido_em)"
                            " VALUES (?, ?, ?, ?)",
                            (area, sessao._token_id, sessao._id, agora),
                        )
                resultado = {
                    "confirmado": True, "lease_sem_prazo": True,
                    "areas": areas, "quantidade": len(areas),
                }
                self._auditar_conn(
                    conn, ator_tipo="agente", ator_id=row["cliente_id"],
                    token_id=sessao._token_id, sessao_id=sessao._id,
                    acao="confirmacao",
                    argumentos={
                        "hash_manifesto": manifesto_hash,
                        "resumo_sha256": resumo_hash,
                        "resumo_tamanho": len(resumo),
                    },
                    resultado=resultado,
                )
            return resultado
        except ErroOps as exc:
            self._auditar(
                ator_tipo="agente", token_id=sessao._token_id,
                sessao_id=sessao._id, acao="confirmacao",
                argumentos={
                    "hash_manifesto": manifesto_hash if isinstance(manifesto_hash, str) else "",
                    "resumo_sha256": resumo_hash or "",
                    "resumo_tamanho": len(resumo) if isinstance(resumo, str) else 0,
                },
                erro=exc.codigo,
            )
            raise

    def _estado_sessao(self, sessao: SessaoOps) -> dict[str, Any]:
        try:
            with self._banco.transacao() as conn:
                row = self._sessao_row(conn, sessao)
                areas = [r["area"] for r in conn.execute(
                    "SELECT area FROM leases WHERE sessao_id = ? ORDER BY area",
                    (sessao._id,),
                )]
                resultado = {
                    "confirmado": row["confirmado_em"] is not None,
                    "areas": areas, "lease_sem_prazo": True,
                }
                self._auditar_conn(
                    conn, ator_tipo="agente", ator_id=row["cliente_id"],
                    token_id=sessao._token_id, sessao_id=sessao._id,
                    acao="estado", resultado=resultado,
                )
            return resultado
        except ErroOps as exc:
            self._auditar(
                ator_tipo="agente", token_id=sessao._token_id,
                sessao_id=sessao._id, acao="estado", erro=exc.codigo,
            )
            raise

    def _chamar(
        self,
        sessao: SessaoOps,
        funcao_id: str,
        argumentos: Mapping[str, Any] | None,
        etapa: str,
        *,
        exigir_confirmacao: bool = False,
    ) -> Any:
        funcao: Funcao | None = None
        try:
            funcao = funcao_por_id(funcao_id)
            if argumentos is None:
                argumentos = {}
            if not isinstance(argumentos, Mapping):
                raise ErroValidacao("argumentos_devem_ser_objeto")
            argumentos = dict(argumentos)
            with self._banco.transacao() as conn:
                row = self._sessao_row(conn, sessao)
                ids = tuple(json.loads(row["funcoes_json"]))
                if funcao.id not in ids:
                    raise ForaDaAtribuicao()
                if etapa == "skill":
                    skill = next((s for s in skills_para_funcao(funcao.id) if s.id == argumentos.get("id")), None)
                    if skill is None:
                        raise FuncaoIndisponivel()
                    self._auditar_conn(
                        conn, ator_tipo="agente", ator_id=row["cliente_id"],
                        token_id=sessao._token_id, sessao_id=sessao._id,
                        area=funcao.area, funcao_id=funcao.id, acao="leitura_skill",
                        resultado={"ok": True},
                    )
                    return {"ok": True, **skill.referencia(), "conteudo": skill.conteudo}
                if funcao.escrita or exigir_confirmacao:
                    if (
                        row["confirmado_em"] is None
                        or row["manifesto_confirmado_hash"] != row["manifesto_hash"]
                    ):
                        raise ConfirmacaoPendente()
                if funcao.escrita:
                    lease = conn.execute(
                        "SELECT 1 FROM leases WHERE area = ? AND sessao_id = ?"
                        " AND token_id = ?",
                        (funcao.area, sessao._id, sessao._token_id),
                    ).fetchone()
                    if lease is None:
                        raise LeasePerdido()
                fluxo = self._fluxos.get(funcao.ferramenta)
                if funcao.risco is Risco.CRITICO and fluxo is None:
                    raise AprovacaoExataNecessaria()
                handler = self._handlers.get(funcao.ferramenta)
                if fluxo is None and (handler is None or etapa != "executar"):
                    raise FuncaoIndisponivel()
                try:
                    if fluxo is not None:
                        resultado = fluxo(sessao, etapa, argumentos)
                    else:
                        resultado = handler(argumentos)
                except ErroOps:
                    raise
                except Exception:
                    raise ErroFerramenta() from None
                self._auditar_conn(
                    conn, ator_tipo="agente", ator_id=row["cliente_id"],
                    token_id=sessao._token_id, sessao_id=sessao._id,
                    area=funcao.area, funcao_id=funcao.id, acao="ferramenta",
                    argumentos=argumentos, resultado=resultado,
                )
            return resultado
        except ErroOps as exc:
            self._auditar(
                ator_tipo="agente", token_id=sessao._token_id,
                sessao_id=sessao._id,
                area=funcao.area if funcao else None,
                funcao_id=funcao.id if funcao else None,
                acao="ferramenta", argumentos=argumentos or {},
                erro=exc.codigo,
            )
            raise

    @staticmethod
    def _limite(limite: int) -> int:
        if not isinstance(limite, int) or isinstance(limite, bool):
            raise ErroValidacao("limite_invalido")
        return max(1, min(limite, 500))

    @staticmethod
    def _eventos(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
        eventos: list[dict[str, Any]] = []
        for row in rows:
            evento = dict(row)
            evento["argumentos"] = json.loads(evento.pop("argumentos_json"))
            evento["resultado"] = json.loads(evento.pop("resultado_json"))
            eventos.append(evento)
        return eventos

    def _auditoria_propria(self, sessao: SessaoOps, limite: int) -> list[dict[str, Any]]:
        try:
            with self._banco.transacao() as conn:
                row = self._sessao_row(conn, sessao)
                limite = self._limite(limite)
                rows = conn.execute(
                    "SELECT * FROM auditoria WHERE sessao_id = ?"
                    " ORDER BY id DESC LIMIT ?",
                    (sessao._id, limite),
                ).fetchall()
                self._auditar_conn(
                    conn, ator_tipo="agente", ator_id=row["cliente_id"],
                    token_id=sessao._token_id, sessao_id=sessao._id,
                    acao="auditoria_propria", argumentos={"limite": limite},
                    resultado={"total": len(rows)},
                )
            return self._eventos(rows)
        except ErroOps as exc:
            self._auditar(
                ator_tipo="agente", token_id=sessao._token_id,
                sessao_id=sessao._id, acao="auditoria_propria", erro=exc.codigo,
            )
            raise

    def _auditoria_admin(self, admin: AdministradorOps, limite: int) -> list[dict[str, Any]]:
        self._admin_valido(admin)
        limite = self._limite(limite)
        with self._banco.transacao() as conn:
            rows = conn.execute(
                "SELECT * FROM auditoria ORDER BY id DESC LIMIT ?", (limite,)
            ).fetchall()
            self._auditar_conn(
                conn, ator_tipo="admin", ator_id=admin._cliente_id,
                acao="auditoria_admin", argumentos={"limite": limite},
                resultado={"total": len(rows)},
            )
        return self._eventos(rows)

    def _desconectar(self, sessao: SessaoOps) -> bool:
        if not isinstance(sessao, SessaoOps) or sessao._servidor is not self:
            raise NaoAutenticado()
        with self._banco.transacao() as conn:
            row = conn.execute(
                "SELECT s.desconectado_em, t.cliente_id, t.agente_id"
                " FROM sessoes s JOIN tokens t ON t.id = s.token_id"
                " WHERE s.id = ? AND s.token_id = ?",
                (sessao._id, sessao._token_id),
            ).fetchone()
            if row is None:
                raise SessaoEncerrada()
            if row["desconectado_em"] is not None:
                self._auditar_conn(
                    conn, ator_tipo="agente", ator_id=row["cliente_id"],
                    agente_id=row["agente_id"], token_id=sessao._token_id,
                    sessao_id=sessao._id, acao="desconexao", resultado={"ok": False},
                )
                return False
            conn.execute(
                "UPDATE sessoes SET desconectado_em = ? WHERE id = ?",
                (_agora(), sessao._id),
            )
            conn.execute("DELETE FROM leases WHERE sessao_id = ?", (sessao._id,))
            self._auditar_conn(
                conn, ator_tipo="agente", ator_id=row["cliente_id"],
                agente_id=row["agente_id"], token_id=sessao._token_id,
                sessao_id=sessao._id, acao="desconexao", resultado={"ok": True},
            )
        return True

    def _revogar_agente(self, admin: AdministradorOps, agente_id: str) -> int:
        self._admin_valido(admin)
        agente_id = validar_identificador(agente_id, "agente_id")
        agora = _agora()
        with self._banco.transacao() as conn:
            rows = conn.execute(
                "SELECT id FROM tokens WHERE agente_id = ? AND revogado_em IS NULL",
                (agente_id,),
            ).fetchall()
            ids = [row["id"] for row in rows]
            conn.execute(
                "UPDATE autorizacoes SET revogado_em = ?"
                " WHERE agente_id = ? AND consumido_em IS NULL AND revogado_em IS NULL",
                (agora, agente_id),
            )
            if ids:
                marcas = ",".join("?" for _ in ids)
                conn.execute(
                    f"UPDATE tokens SET revogado_em = ? WHERE id IN ({marcas})",
                    (agora, *ids),
                )
                conn.execute(
                    f"DELETE FROM leases WHERE token_id IN ({marcas})", ids
                )
                conn.execute(
                    f"UPDATE sessoes SET desconectado_em = ?"
                    f" WHERE token_id IN ({marcas}) AND desconectado_em IS NULL",
                    (agora, *ids),
                )
            self._auditar_conn(
                conn, ator_tipo="admin", ator_id=admin._cliente_id,
                agente_id=agente_id, acao="revogacao_agente",
                resultado={"total": len(ids)},
            )
        return len(ids)

    def _revogar_token(self, admin: AdministradorOps, token_id: str) -> bool:
        self._admin_valido(admin)
        if not isinstance(token_id, str) or not _TOKEN_ID.fullmatch(token_id):
            raise ErroValidacao("token_id_invalido")
        agora = _agora()
        with self._banco.transacao() as conn:
            row = conn.execute(
                "SELECT agente_id, revogado_em FROM tokens WHERE id = ?", (token_id,)
            ).fetchone()
            if row is None:
                raise TokenInvalido()
            if row["revogado_em"] is not None:
                self._auditar_conn(
                    conn, ator_tipo="admin", ator_id=admin._cliente_id,
                    agente_id=row["agente_id"], token_id=token_id,
                    acao="revogacao_token", resultado={"ok": False},
                )
                return False
            conn.execute(
                "UPDATE tokens SET revogado_em = ? WHERE id = ?", (agora, token_id)
            )
            conn.execute("DELETE FROM leases WHERE token_id = ?", (token_id,))
            conn.execute(
                "UPDATE sessoes SET desconectado_em = ?"
                " WHERE token_id = ? AND desconectado_em IS NULL",
                (agora, token_id),
            )
            self._auditar_conn(
                conn, ator_tipo="admin", ator_id=admin._cliente_id,
                agente_id=row["agente_id"], token_id=token_id,
                acao="revogacao_token", resultado={"ok": True},
            )
        return True
