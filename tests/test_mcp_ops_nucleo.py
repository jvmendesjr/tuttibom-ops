"""Testes do núcleo OPS em laboratório; todos os dados são sintéticos."""

from __future__ import annotations

import hashlib
import inspect
import itertools
import json
import sqlite3
from dataclasses import fields
from pathlib import Path
from types import SimpleNamespace

import pytest

from tuttibom.mcp_ops import (
    ClienteConfigurado,
    FronteiraIdentidadeLaboratorio,
    RegistroIdentidade,
    Risco,
    ServidorOps,
)
from tuttibom.mcp_ops.erros import (
    AgenteJaAtivo,
    AprovacaoExataNecessaria,
    AreaOcupada,
    AutorizacaoJaUtilizada,
    AutorizacaoRevogada,
    ClienteNaoConfigurado,
    ConfirmacaoPendente,
    ErroFerramenta,
    ErroValidacao,
    ForaDaAtribuicao,
    FuncaoDesconhecida,
    FuncoesDivergentes,
    IdentidadeNaoVinculada,
    LeasePerdido,
    ManifestoDivergente,
    NaoAutenticado,
    PermissaoAdministrativaNegada,
    SessaoEncerrada,
    TokenRevogado,
)

RESUMO = "Confirmo somente as funções listadas e os limites do manifesto de laboratório."


def _hash(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


@pytest.fixture
def lab(tmp_path: Path):
    fronteira = FronteiraIdentidadeLaboratorio({
        "admin-lab": RegistroIdentidade("identidade-admin-lab", administrador=True),
        "cliente-a": RegistroIdentidade("identidade-lab-a"),
        "cliente-b": RegistroIdentidade("identidade-lab-b"),
    })
    sequencia = itertools.count(1)
    criticas: list[dict] = []
    handlers = {
        "ops_produto_consultar": lambda args: {
            "ok": True, "sku": args.get("sku", "SKU-LAB-01"),
        },
        "ops_plataforma_saude": lambda args: {"ok": True, "total": 1},
        "ops_crm_registrar_lead": lambda args: {
            "ok": True,
            "mensagem": "RETORNO_SINTETICO_OMITIR",
            "token": "RETORNO_TOKEN_SINTETICO_OMITIR",
        },
        "ops_social_rascunho_post": lambda args: {"ok": True},
        "ops_atendimento_responder": lambda args: criticas.append(dict(args)),
    }
    servidor = ServidorOps(
        tmp_path / "ops-lab.sqlite3",
        fronteira,
        handlers=handlers,
        gerador_token=lambda: f"ops_lab_{next(sequencia):06d}_VALOR_SINTETICO",
    )
    ambiente = SimpleNamespace(
        servidor=servidor,
        banco=tmp_path / "ops-lab.sqlite3",
        admin=servidor.configurar_administrador("admin-lab"),
        cliente_a=servidor.configurar_cliente("cliente-a"),
        cliente_b=servidor.configurar_cliente("cliente-b"),
        criticas=criticas,
    )
    try:
        yield ambiente
    finally:
        servidor.close()


def _ativar(lab, cliente, agente: str, funcoes):
    autorizacao = lab.admin.autorizar(
        agente_id=agente, cliente=cliente, funcoes=funcoes
    )
    recibo = cliente.ativar(autorizacao.referencia, funcoes)
    return autorizacao, recibo


def _linhas_auditaveis(caminho: Path) -> str:
    with sqlite3.connect(caminho) as conn:
        valores: list[str] = []
        for tabela in ("auditoria", "sessoes", "tokens", "autorizacoes"):
            for row in conn.execute(f"SELECT * FROM {tabela}"):
                valores.extend(str(valor) for valor in row if valor is not None)
        return "\n".join(valores)


def test_gerador_padrao_emite_token_utilizavel_sem_persistir_valor_bruto(tmp_path):
    banco = tmp_path / "gerador-padrao.sqlite3"
    fronteira = FronteiraIdentidadeLaboratorio({
        "admin-lab": RegistroIdentidade("identidade-admin-lab", administrador=True),
        "cliente-a": RegistroIdentidade("identidade-lab-a"),
    })
    servidor = ServidorOps(
        banco, fronteira,
        handlers={"ops_plataforma_saude": lambda _args: {"ok": True}},
    )
    try:
        admin = servidor.configurar_administrador("admin-lab")
        cliente = servidor.configurar_cliente("cliente-a")
        autorizacao = admin.autorizar(
            agente_id="agente-lab-a", cliente=cliente, funcoes=["08.01"]
        )
        cliente.ativar(autorizacao.referencia, ["08.01"])
        token_sintetico = cliente._token
        assert isinstance(token_sintetico, str)
        assert token_sintetico.startswith("ops_")
        sessao = cliente.conectar()
        assert sessao.chamar("08.01") == {"ok": True}
        assert token_sintetico not in _linhas_auditaveis(banco)
    finally:
        servidor.close()


def test_catalogo_admin_estavel_e_critico_nao_entra_por_pacote(lab):
    catalogo = lab.admin.listar_atribuicoes()
    ids = tuple(funcao.id for funcao in catalogo)
    assert ids == (
        "01.01", "01.02", "02.01", "02.02", "02.03", "02.04", "02.05",
        "03.01", "04.01", "04.02", "05.01", "05.02", "06.01", "07.01",
        "07.02", "08.01", "08.02", "08.03",
    )
    assert len(set(ids)) == len(ids)
    por_id = {funcao.id: funcao for funcao in catalogo}
    assert por_id["01.02"].risco is Risco.CRITICO
    assert por_id["05.02"].risco is Risco.CRITICO

    with pytest.raises(PermissaoAdministrativaNegada):
        lab.servidor.configurar_administrador("cliente-a")
    with pytest.raises(NaoAutenticado):
        lab.servidor.configurar_cliente("cliente-sem-registro")

    _, _ = _ativar(lab, lab.cliente_a, "agente-lab-a", ["01.01"])
    manifesto = lab.cliente_a.conectar().manifesto()
    assert tuple(f.id for f in manifesto.funcoes) == ("01.01",)
    assert not hasattr(lab.cliente_a, "listar_atribuicoes")


def test_ativacao_exige_funcoes_exatas_e_falha_nao_consume_autorizacao(lab):
    autorizacao = lab.admin.autorizar(
        agente_id="agente-lab-a",
        cliente=lab.cliente_a,
        funcoes=["01.01", "01.02"],
    )
    assert "agente_id" not in inspect.signature(lab.cliente_a.ativar).parameters
    assert "identidade" not in inspect.signature(lab.cliente_a.ativar).parameters

    with pytest.raises(FuncoesDivergentes):
        lab.cliente_a.ativar(autorizacao.referencia, ["01.01"])

    recibo = lab.cliente_a.ativar(
        autorizacao.referencia, ["01.02", "01.01"]
    )
    assert recibo.manifesto_hash == autorizacao.manifesto_hash
    with pytest.raises(AutorizacaoJaUtilizada):
        lab.cliente_a.ativar(autorizacao.referencia, ["01.01", "01.02"])


def test_ativacao_vincula_identidade_e_exige_cliente_registrado(lab):
    autorizacao = lab.admin.autorizar(
        agente_id="agente-lab-a", cliente=lab.cliente_a, funcoes=["03.01"]
    )
    with pytest.raises(IdentidadeNaoVinculada):
        lab.cliente_b.ativar(autorizacao.referencia, ["03.01"])

    falso = ClienteConfigurado(lab.servidor, "cliente-a")
    with pytest.raises(ClienteNaoConfigurado):
        falso.ativar(autorizacao.referencia, ["03.01"])

    recibo = lab.cliente_a.ativar(autorizacao.referencia, ["03.01"])
    assert {campo.name for campo in fields(recibo)} == {
        "token_id", "agente_id", "manifesto_hash"
    }
    assert "VALOR_SINTETICO" not in repr(recibo)
    assert "VALOR_SINTETICO" not in repr(lab.cliente_a)


def test_token_fica_so_com_hash_e_revogacao_e_imediata(lab):
    _ativar(lab, lab.cliente_a, "agente-lab-a", ["02.01"])
    sessao = lab.cliente_a.conectar()
    token_sintetico = lab.cliente_a._token
    manifesto = sessao.manifesto()
    sessao.confirmar_atribuicoes(manifesto.hash, RESUMO)

    with sqlite3.connect(lab.banco) as conn:
        row = conn.execute("SELECT token_hash FROM tokens").fetchone()
        assert row[0] == _hash(token_sintetico)
        assert conn.execute("SELECT COUNT(*) FROM leases").fetchone()[0] == 1
    assert token_sintetico not in _linhas_auditaveis(lab.banco)

    assert lab.admin.revogar_agente("agente-lab-a") == 1
    with pytest.raises(TokenRevogado):
        sessao.chamar("02.01")
    with pytest.raises(TokenRevogado):
        lab.cliente_a.conectar()
    with sqlite3.connect(lab.banco) as conn:
        assert conn.execute("SELECT COUNT(*) FROM leases").fetchone()[0] == 0


def test_handshake_enforcement_e_reconexao_exige_nova_confirmacao(lab):
    _ativar(lab, lab.cliente_a, "agente-lab-a", ["02.01", "03.01"])
    sessao = lab.cliente_a.conectar()
    manifesto = sessao.manifesto()

    assert sessao.chamar("03.01", {"sku": "SKU-LAB-01"})["ok"] is True
    with pytest.raises(ConfirmacaoPendente):
        sessao.chamar("02.01")
    with pytest.raises(ForaDaAtribuicao):
        sessao.chamar("08.01")
    with pytest.raises(ManifestoDivergente):
        sessao.confirmar_atribuicoes("0" * 64, RESUMO)
    with pytest.raises(ErroValidacao):
        sessao.confirmar_atribuicoes(manifesto.hash, "  ")

    confirmado = sessao.confirmar_atribuicoes(manifesto.hash, RESUMO)
    assert confirmado["confirmado"] is True
    assert confirmado["areas"] == ["02"]
    assert sessao.estado()["lease_sem_prazo"] is True
    assert sessao.chamar("02.01")["ok"] is True

    reconectada = lab.cliente_a.conectar()
    with pytest.raises(ConfirmacaoPendente):
        reconectada.chamar("02.01")
    assert sessao.desconectar() is True
    reconectada.confirmar_atribuicoes(manifesto.hash, RESUMO)
    assert reconectada.chamar("02.01")["ok"] is True
    with pytest.raises(SessaoEncerrada):
        sessao.chamar("03.01")


def test_lease_sem_prazo_impede_segundo_escritor_e_libera_na_troca(lab):
    _ativar(lab, lab.cliente_a, "agente-lab-a", ["02.01", "03.01"])
    _, recibo_b = _ativar(lab, lab.cliente_b, "agente-lab-b", ["02.01", "03.01"])
    sessao_a = lab.cliente_a.conectar()
    sessao_b = lab.cliente_b.conectar()
    hash_a = sessao_a.manifesto().hash
    hash_b = sessao_b.manifesto().hash
    sessao_a.confirmar_atribuicoes(hash_a, RESUMO)

    assert sessao_b.chamar("03.01")["ok"] is True
    with pytest.raises(AreaOcupada) as ocupada:
        sessao_b.confirmar_atribuicoes(hash_b, RESUMO)
    assert ocupada.value.area == "02"
    with pytest.raises(ConfirmacaoPendente):
        sessao_b.chamar("02.01")

    with sqlite3.connect(lab.banco) as conn:
        colunas = {row[1] for row in conn.execute("PRAGMA table_info(leases)")}
        assert colunas == {"area", "token_id", "sessao_id", "adquirido_em"}
        assert conn.execute("SELECT COUNT(*) FROM leases").fetchone()[0] == 1

    sessao_a.desconectar()
    sessao_b.confirmar_atribuicoes(hash_b, RESUMO)
    assert sessao_b.chamar("02.01")["ok"] is True
    assert lab.admin.revogar_token(recibo_b.token_id) is True
    with pytest.raises(TokenRevogado):
        sessao_b.chamar("02.01")


def test_sessao_pode_reter_leases_em_areas_distintas(lab):
    _ativar(lab, lab.cliente_a, "agente-lab-a", ["02.01", "05.01"])
    sessao = lab.cliente_a.conectar()
    manifesto = sessao.manifesto()
    resultado = sessao.confirmar_atribuicoes(manifesto.hash, RESUMO)
    assert resultado["areas"] == ["02", "05"]
    assert sessao.chamar("02.01")["ok"] is True
    assert sessao.chamar("05.01")["ok"] is True
    with sqlite3.connect(lab.banco) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM leases WHERE sessao_id = ?", (sessao.id,)
        ).fetchone()[0] == 2


def test_funcao_critica_selecionada_ainda_exige_aprovacao_exata(lab):
    _ativar(lab, lab.cliente_a, "agente-lab-a", ["01.01", "01.02"])
    sessao = lab.cliente_a.conectar()
    manifesto = sessao.manifesto()
    sessao.confirmar_atribuicoes(manifesto.hash, RESUMO)
    with pytest.raises(AprovacaoExataNecessaria):
        sessao.chamar("01.02", {"mensagem": "ACAO_SINTETICA_NAO_EXECUTAR"})
    assert lab.criticas == []


def test_auditoria_sanitizada_e_limitada_a_propria_sessao(lab):
    _ativar(lab, lab.cliente_a, "agente-lab-a", ["02.01"])
    _ativar(lab, lab.cliente_b, "agente-lab-b", ["03.01"])
    sessao_a = lab.cliente_a.conectar()
    sessao_b = lab.cliente_b.conectar()
    manifesto = sessao_a.manifesto()
    resumo_livre = "RESUMO_LIVRE_SINTETICO_NAO_PERSISTIR"
    sessao_a.confirmar_atribuicoes(manifesto.hash, resumo_livre)
    sessao_a.chamar("02.01", {
        "referencia": "ref-lab-01",
        "token": "TOKEN_SINTETICO_NAO_PERSISTIR",
        "mensagem": "MENSAGEM_SINTETICA_NAO_PERSISTIR",
        "nome": "NOME_SINTETICO_NAO_PERSISTIR",
        "extra": {"texto": "ANINHADO_SINTETICO_NAO_PERSISTIR"},
        "limite": 3,
    })
    sessao_b.chamar("03.01")

    eventos_a = sessao_a.auditoria(200)
    assert eventos_a
    assert {evento["sessao_id"] for evento in eventos_a} == {sessao_a.id}
    assert sessao_b.id not in json.dumps(eventos_a)
    chamada = next(
        evento for evento in eventos_a
        if evento["acao"] == "ferramenta" and evento["erro_codigo"] is None
    )
    assert chamada["argumentos"]["token"] == "[redigido]"
    assert chamada["argumentos"]["mensagem"] == "[omitido]"
    assert "referencia" not in chamada["argumentos"]
    assert chamada["argumentos"]["referencia_sha256"] == _hash("ref-lab-01")
    assert chamada["argumentos"]["limite"] == 3
    assert chamada["resultado"]["mensagem"] == "[omitido]"
    assert chamada["resultado"]["token"] == "[redigido]"

    auditavel = _linhas_auditaveis(lab.banco)
    for valor in (
        "TOKEN_SINTETICO_NAO_PERSISTIR",
        "MENSAGEM_SINTETICA_NAO_PERSISTIR",
        "NOME_SINTETICO_NAO_PERSISTIR",
        "ref-lab-01",
        "ANINHADO_SINTETICO_NAO_PERSISTIR",
        "RETORNO_SINTETICO_OMITIR",
        "RETORNO_TOKEN_SINTETICO_OMITIR",
        resumo_livre,
    ):
        assert valor not in auditavel
    assert _hash(resumo_livre) in auditavel
    assert any(
        evento["sessao_id"] == sessao_b.id
        for evento in lab.admin.auditoria(500)
    )


def test_nao_emite_dois_tokens_ativos_para_o_mesmo_agente(lab):
    _ativar(lab, lab.cliente_a, "agente-lab-compartilhado", ["03.01"])
    autorizacao = lab.admin.autorizar(
        agente_id="agente-lab-compartilhado",
        cliente=lab.cliente_b,
        funcoes=["03.01"],
    )
    with pytest.raises(AgenteJaAtivo):
        lab.cliente_b.ativar(autorizacao.referencia, ["03.01"])


def test_confirmacao_repetida_nao_duplica_nem_esconde_lease_perdido(lab):
    _ativar(lab, lab.cliente_a, "agente-lab-a", ["02.01"])
    sessao = lab.cliente_a.conectar()
    manifesto = sessao.manifesto()
    sessao.confirmar_atribuicoes(manifesto.hash, RESUMO)
    sessao.confirmar_atribuicoes(manifesto.hash, RESUMO)
    with sqlite3.connect(lab.banco) as conn:
        assert conn.execute("SELECT COUNT(*) FROM leases").fetchone()[0] == 1
        conn.execute("DELETE FROM leases WHERE sessao_id = ?", (sessao.id,))
        conn.commit()

    with pytest.raises(LeasePerdido):
        sessao.confirmar_atribuicoes(manifesto.hash, RESUMO)
    with pytest.raises(LeasePerdido):
        sessao.chamar("02.01")


def test_falha_de_handler_nao_expoe_excecao_ou_argumentos(lab):
    def falhar(_args):
        raise RuntimeError("FALHA_INTERNA_SINTETICA_NAO_VAZAR")

    lab.servidor._handlers["ops_crm_registrar_lead"] = falhar
    _ativar(lab, lab.cliente_a, "agente-lab-a", ["02.01"])
    sessao = lab.cliente_a.conectar()
    manifesto = sessao.manifesto()
    sessao.confirmar_atribuicoes(manifesto.hash, RESUMO)
    with pytest.raises(ErroFerramenta) as erro:
        sessao.chamar("02.01", {"mensagem": "VALOR_SINTETICO_OMITIR"})
    assert str(erro.value) == "erro_ferramenta"
    assert "FALHA_INTERNA" not in str(erro.value)
    assert "FALHA_INTERNA" not in _linhas_auditaveis(lab.banco)
    assert "VALOR_SINTETICO_OMITIR" not in _linhas_auditaveis(lab.banco)


def test_revogacao_tambem_invalida_autorizacao_ainda_nao_ativada(lab):
    autorizacao = lab.admin.autorizar(
        agente_id="agente-lab-a", cliente=lab.cliente_a, funcoes=["03.01"]
    )
    assert lab.admin.revogar_agente("agente-lab-a") == 0
    with pytest.raises(AutorizacaoRevogada):
        lab.cliente_a.ativar(autorizacao.referencia, ["03.01"])


def test_selecao_invalida_e_desconexao_sao_falhas_explicitas(lab):
    with pytest.raises(FuncaoDesconhecida):
        lab.admin.autorizar(
            agente_id="agente-lab-a", cliente=lab.cliente_a, funcoes=["99.99"]
        )
    with pytest.raises(ErroValidacao):
        lab.admin.autorizar(
            agente_id="agente-lab-a", cliente=lab.cliente_a,
            funcoes=["03.01", "03.01"],
        )
    with pytest.raises(ErroValidacao):
        lab.admin.autorizar(
            agente_id="AGENTE LIVRE", cliente=lab.cliente_a, funcoes=["03.01"]
        )

    _ativar(lab, lab.cliente_a, "agente-lab-a", ["03.01"])
    sessao = lab.cliente_a.conectar()
    with pytest.raises(FuncaoDesconhecida):
        sessao.chamar("99.99")
    assert sessao.desconectar() is True
    assert sessao.desconectar() is False
    with pytest.raises(SessaoEncerrada):
        sessao.manifesto()
