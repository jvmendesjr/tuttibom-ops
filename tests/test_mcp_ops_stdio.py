"""Aceitação via entrypoints reais e cliente MCP; sem acesso a produção."""
from __future__ import annotations

import base64
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import select
import subprocess
import sys
import tempfile

import anyio
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from tuttibom.mcp_ops.atendimento import FilaLaboratorio
from tuttibom.mcp_ops.erros import ErroOps
from tuttibom.mcp_ops.laboratorio import CONVERSA, Laboratorio

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
ENV = {**os.environ, "PATH": f"{Path(sys.executable).parent}:{os.environ['PATH']}"}


@contextmanager
def laboratorio(*perfis, estado_dir=None, comando_host=None):
    with tempfile.TemporaryDirectory(prefix="tb-ops-") as tmp:
        dir_ = Path(tmp) / "lab"
        cmd = [str(SCRIPTS / "tuttibom-ops-admin"), "--laboratorio", str(dir_)]
        with tempfile.TemporaryFile(mode="w+") as stderr:
            perfis_cli = [arg for perfil in perfis for arg in ("--cliente-lab", perfil)]
            if estado_dir is not None:
                perfis_cli.extend(("--estado-lab", str(estado_dir)))
            partida = comando_host(dir_) if comando_host else cmd + ["servir", *perfis_cli]
            proc = subprocess.Popen(partida, env=ENV, stdout=subprocess.PIPE,
                                    text=True, stderr=stderr)
            try:
                assert select.select([proc.stdout], [], [], 12)[0]
                assert proc.stdout.readline().strip() == "laboratorio_pronto"
                assert dir_.stat().st_mode & 0o777 == 0o700
                assert (dir_ / f"{(perfis or ('ana-01',))[0]}.sock").stat().st_mode & 0o777 == 0o600

                def admin(*args, entrada=None, rc=0):
                    res = subprocess.run(
                        cmd + list(args), input=json.dumps(entrada) if entrada is not None else "",
                        capture_output=True, text=True, env=ENV, timeout=12,
                    )
                    assert res.returncode == rc, (res.returncode, res.stderr)
                    return json.loads(res.stdout)

                yield dir_, admin
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                proc.stdout.close()
                stderr.seek(0)
                assert proc.returncode == 0, stderr.read()
            assert not dir_.exists()


@asynccontextmanager
async def cliente(cmd, *args, prazo_sessao=40):
    params = StdioServerParameters(command=str(SCRIPTS / cmd), args=list(args), env={"PATH": ENV["PATH"]})
    with anyio.fail_after(prazo_sessao):
        async with stdio_client(params) as (ler, escrever):
            async with ClientSession(ler, escrever) as sessao:
                init = await sessao.initialize()
                yield sessao, init.serverInfo.name


def test_core_somente_leitura_e_alias():
    async def caso():
        esperadas = {
            "estado", "roadmap", "decisoes", "arvore", "buscar_codigo", "git_status",
            "ler_doc", "onde_esta_tudo", "checklist_fim_operacao", "propostas",
            "fila_publicacao", "catalogo",
        }
        for script in ("tuttibom-core-mcp", "tuttibom-mcp"):
            async with cliente(script) as (core, nome):
                assert nome == "tuttibom-core-mcp"
                assert {tool.name for tool in (await core.list_tools()).tools} == esperadas
                assert not (await core.call_tool("estado", {})).isError
                man = await core.call_tool("ler_doc", {"caminho": "skills/core-plataforma-manutencao/SKILL.md"})
                assert not man.isError and "name: core-plataforma-manutencao" in man.content[0].text
                assert (await core.call_tool("ler_doc", {"caminho": "skills/ops-ana-resposta/SKILL.md"})).isError
                assert (await core.call_tool("ops_atendimento_responder", {})).isError
    anyio.run(caso)


async def dados(sessao, nome, erro=None, **args):
    r = await sessao.call_tool(nome, args)
    d = r.structuredContent
    assert d is not None, (nome, r.content)
    assert r.isError == (erro is not None), (nome, d)
    if erro is not None:
        assert d["codigo"] == erro
    return d


def test_ops_ativacao_aprovacao_midia_replay_e_sucessao():
    async def caso(dir_, admin):
        funcoes = ["01.01", "01.02"]
        catalogo = admin("listar-atribuicoes")["funcoes"]
        assert len(catalogo) == len({f["id"] for f in catalogo}) == 18
        assert {f["id"] for f in catalogo if f["executavel_no_lab"]} == {"01.01", "01.02", "03.01"}
        assert admin("autorizar", "--agente", "ana-01", "--funcoes", "08.03",
                     rc=1)["codigo"] == "funcao_indisponivel"
        assert admin("autorizar", "--agente", "ana-01", "--funcoes", "01.02",
                     rc=1)["codigo"] == "resposta_requer_leitura"
        aut1 = admin("autorizar", "--agente", "ana-01", "--funcoes", ",".join(funcoes))
        aut2 = admin("autorizar", "--agente", "ana-02", "--funcoes", ",".join([*funcoes, "03.01"]))
        lab = ("--laboratorio", str(dir_), "--cliente")
        resumir = "Li o escopo: só atuo com aprovação exata e exclusividade."
        ler = "ops_atendimento_ler_conversa"
        fila = "ops_atendimento_listar_pendencias"
        preparar = "ops_atendimento_preparar_resposta"
        responder = "ops_atendimento_responder"
        ativar = "ops_ativar"
        confirmar = "ops_confirmar_atribuicoes"
        skill = "ops_ler_skill"
        skills_ana = ["ops-ana-atendimento", "ops-ana-triagem", "ops-ana-resposta"]

        async def ler_skills(sessao, metadados):
            for meta in metadados:
                doc = await dados(sessao, skill, id=meta["id"])
                assert doc["versao"] == meta["versao"] == hashlib.sha256(doc["conteudo"].encode()).hexdigest()
                canonico = SCRIPTS.parent / "skills" / meta["id"] / "SKILL.md"
                assert doc["conteudo"].encode() == canonico.read_bytes()

        async with cliente("tuttibom-ops-mcp", *lab, "ana-01") as (ana1, nome):
            assert nome == "tuttibom-ops-mcp"
            assert {f.name for f in (await ana1.list_tools()).tools} == {ativar, "ops_reconectar"}
            await dados(ana1, fila, "nao_autenticado")
            await dados(ana1, skill, "nao_autenticado", id="ops-ana-atendimento")
            await dados(ana1, ativar, "funcoes_divergentes", referencia=aut1["referencia"], funcoes=["01.01"])
            async with cliente("tuttibom-ops-mcp", *lab, "ana-02") as (ana2, _):
                await dados(ana2, ativar, "identidade_nao_vinculada", referencia=aut1["referencia"], funcoes=funcoes)
                ligado1 = await dados(ana1, ativar, referencia=aut1["referencia"], funcoes=funcoes)
                m1 = ligado1["manifesto"]
                assert ligado1["ambiente"] == "laboratorio"
                assert m1["papeis"] == [{
                    "area": "01", "persona": "Ana", "skills": skills_ana,
                }]
                assert [s["id"] for s in m1["skills"]] == skills_ana
                assert {f["id"]: f["skills"] for f in m1["funcoes"]} == {
                    "01.01": skills_ana[:2], "01.02": skills_ana[::2],
                }
                assert m1["hash"] == aut1["manifesto_hash"]
                assert {f["id"] for f in m1["funcoes"]} == set(funcoes)
                assert {t for f in m1["funcoes"] for t in f["ferramentas_auxiliares"]} == {fila, preparar, skill}
                assert not re.search(r"ops_[0-9a-f]{12}_", json.dumps(ligado1))
                ferramentas = {f.name for f in (await ana1.list_tools()).tools}
                assert {fila, ler, preparar, responder, skill}.issubset(ferramentas)
                assert ferramentas.isdisjoint({"ops_produto_consultar", "ler_doc", "aprovar-resposta"})
                await dados(ana1, "ops_produto_consultar", "fora_da_atribuicao", sku="FITA-22-50-DOURADO")
                await dados(ana1, "aprovar-resposta", "fora_da_atribuicao")
                ligado2 = await dados(ana2, ativar, referencia=aut2["referencia"], funcoes=[*funcoes, "03.01"])
                preco = await dados(ana2, "ops_produto_consultar", sku="FITA-22-50-DOURADO")
                assert (preco["preco"], preco["disponibilidade"]) == ("88.90", "nao_verificada")
                m2 = ligado2["manifesto"]
                assert [s["id"] for s in m2["skills"]] == [*skills_ana, "ops-produto-consulta"]
                for id_ in ("../../README.md", "ops-produto-consulta", "ops-crm-vendas",
                            "core-plataforma-manutencao"):
                    await dados(ana1, skill, "skill_indisponivel_no_escopo", id=id_)
                await ler_skills(ana1, m1["skills"][:-1])
                await dados(ana1, confirmar, "skills_pendentes", manifesto_hash=m1["hash"], resumo=resumir)
                await ler_skills(ana1, m1["skills"][-1:])
                await ler_skills(ana2, m2["skills"][:-1])
                await dados(ana2, confirmar, "skills_pendentes", manifesto_hash=m2["hash"], resumo=resumir)
                await ler_skills(ana2, m2["skills"][-1:])
                await dados(ana1, confirmar, "manifesto_divergente", manifesto_hash="incorreto", resumo=resumir)
                await dados(ana1, responder, "confirmacao_pendente", rascunho_ref="ras-impossivel")
                exclusivo = await dados(ana1, confirmar, manifesto_hash=m1["hash"], resumo=resumir)
                assert exclusivo["areas"] == ["01"]
                await dados(ana2, confirmar, "area_ocupada", manifesto_hash=m2["hash"], resumo=resumir)
                pendencias = (await dados(ana1, fila))["pendencias"]
                assert len(pendencias) == 2 and pendencias[0]["cumprimento"]["texto"] == "Olá! [LAB]"
                conversa = pendencias[0]["conversation_id"]
                msg_ids = [p["message_id"] for p in pendencias]
                texto = "Recebi a imagem e o áudio sobre a fita de 22 mm. [LAB]"
                args = dict(conversa_ref=conversa, texto=texto, idempotency_key="lab-intento-1", message_ids=msg_ids[:1])
                await dados(ana1, preparar, "leitura_obrigatoria", **args)
                midia = await ana1.call_tool(ler, {"conversa_ref": conversa})
                assert not midia.isError
                msgs = midia.structuredContent["mensagens"]
                assert [m["direcao"] for m in msgs] == ["outgoing", "incoming", "incoming"]
                assert msgs[1]["texto"] == msgs[2]["texto"] == ""
                imagem = msgs[1]["anexos"][0]
                bloco = midia.content[imagem["bloco_mcp"]]
                assert bloco.type == "image" and bloco.mimeType == "image/png"
                png = base64.b64decode(bloco.data, validate=True)
                assert png.startswith(b"\x89PNG\r\n\x1a\n")
                assert imagem["sha256"] == hashlib.sha256(png).hexdigest()
                assert "22 mm" in msgs[2]["anexos"][0]["transcricao"]
                await dados(ana1, preparar, "imagens_pendentes", **args)
                preparado1 = await dados(ana1, preparar, **args, imagens_lidas=[imagem["sha256"]],
                                        imagem_ref=imagem["midia_ref"])
                ref1 = preparado1["rascunho_ref"]
                await dados(ana1, responder, "argumento_invalido", rascunho_ref=ref1, aprovado=True)
                await dados(ana1, responder, "aprovacao_exata_necessaria", rascunho_ref=ref1)
                prova = {"conversa_ref": conversa, "rascunho_ref": ref1,
                         "texto": texto, "imagem_base64": bloco.data}
                assert admin("aprovar-resposta", entrada={**prova, "texto": texto + " "},
                             rc=1)["codigo"] == "conteudo_divergente"
                assert admin("aprovar-resposta", entrada={**prova, "imagem_base64": "YQ=="},
                             rc=1)["codigo"] == "conteudo_divergente"
                assert len((await dados(ana1, fila))["pendencias"]) == 2
                aprovacao = admin("aprovar-resposta", entrada=prova)["aprovacao_ref"]
                outro = await dados(ana1, preparar, **{**args, "idempotency_key": "outro-intento"},
                                    imagens_lidas=[imagem["sha256"]])
                await dados(ana1, responder, "aprovacao_exata_necessaria",
                            rascunho_ref=outro["rascunho_ref"], aprovacao_ref=aprovacao)
                envio = await dados(ana1, responder, rascunho_ref=ref1, aprovacao_ref=aprovacao)
                assert envio["enviado"] and envio["acked"] == msg_ids[:1] and not envio["replay"]
                segundo = await dados(ana1, responder, rascunho_ref=ref1, aprovacao_ref=aprovacao)
                assert segundo["replay"] and segundo["envio_ref"] == envio["envio_ref"]
                assert admin("revogar", "--agente", "ana-01")["revogados"] >= 1
                await dados(ana1, responder, "token_revogado", rascunho_ref=ref1, aprovacao_ref=aprovacao)
                await dados(ana1, skill, "token_revogado", id="ops-ana-atendimento")
                assert (await dados(ana2, confirmar, manifesto_hash=m2["hash"], resumo=resumir))["areas"] == ["01"]
                assert [p["message_id"] for p in (await dados(ana2, fila))["pendencias"]] == msg_ids[1:]
                await dados(ana2, responder, "rascunho_ausente", rascunho_ref=ref1, aprovacao_ref=aprovacao)
                novo = {**args, "idempotency_key": "lab-intento-2", "message_ids": msg_ids[1:]}
                await dados(ana2, preparar, "leitura_obrigatoria", **novo)
                historico = await dados(ana2, ler, conversa_ref=conversa)
                assert historico["mensagens"][-1]["texto"] == texto
                preparado2 = await dados(ana2, preparar, **novo, imagens_lidas=[imagem["sha256"]])
                ref2 = preparado2["rascunho_ref"]
                aprovacao2 = admin("aprovar-resposta", entrada={"conversa_ref": conversa, "rascunho_ref": ref2,
                                                                "texto": texto})["aprovacao_ref"]
                assert (await dados(ana2, responder, rascunho_ref=ref2, aprovacao_ref=aprovacao2))["acked"] == msg_ids[1:]
                assert not (await dados(ana2, fila))["pendencias"]
        async with cliente("tuttibom-ops-mcp", *lab, "ana-02") as (ana2, _):
            await dados(ana2, ativar, "autorizacao_ja_utilizada", referencia=aut2["referencia"], funcoes=[*funcoes, "03.01"])
            await dados(ana2, "ops_reconectar")
            estado = await dados(ana2, "ops_estado")
            assert not estado["confirmado"] and not estado["areas"]
            await dados(ana2, confirmar, "skills_pendentes", manifesto_hash=m2["hash"], resumo=resumir)
            await dados(ana2, responder, "confirmacao_pendente", rascunho_ref="ras-impossivel")
        eventos = json.dumps(admin("auditoria"), ensure_ascii=False)
        assert "token_revogado" in eventos and "fora_da_atribuicao" in eventos
        assert all(valor not in eventos for valor in (texto, bloco.data, aprovacao, resumir))
        assert not re.search(r"ops_[0-9a-f]{12}_", eventos)

    with laboratorio() as (dir_, admin):
        anyio.run(caso, dir_, admin)


def test_cliente_arbitrario_teste_com_persona_somente_de_produto():
    async def caso(dir_, admin):
        nome = "cliente-neutro"
        autorizacao = admin("autorizar", "--agente", nome, "--funcoes", "03.01")
        async with cliente("tuttibom-ops-mcp", "--laboratorio", str(dir_), "--cliente", nome) as (sessao, _):
            ativacao = await dados(sessao, "ops_ativar", referencia=autorizacao["referencia"], funcoes=["03.01"])
            m = ativacao["manifesto"]
            assert {p["area"] for p in m["papeis"]} == {"03"}
            assert {s["id"] for s in m["skills"]} == {"ops-produto-consulta"}
            assert all(not f.name.startswith("ops_atendimento") for f in (await sessao.list_tools()).tools)
            await dados(sessao, "ops_ler_skill", "skill_indisponivel_no_escopo", id="ops-ana-atendimento")
            confirmar = {"manifesto_hash": m["hash"], "resumo": "Somente consultar SKU."}
            await dados(sessao, "ops_confirmar_atribuicoes", "skills_pendentes", **confirmar)
            assert "estoque" in (await dados(sessao, "ops_ler_skill", id="ops-produto-consulta"))["conteudo"]
            assert (await dados(sessao, "ops_confirmar_atribuicoes", **confirmar))["areas"] == []
            assert (await dados(sessao, "ops_produto_consultar", sku="FITA-15-10-PRETO"))["preco"] == "15.00"

    with laboratorio("cliente-neutro") as (dir_, admin):
        anyio.run(caso, dir_, admin)


def test_leitor_de_atendimento_nao_recebe_skill_de_resposta():
    async def caso(dir_, admin):
        aut = admin("autorizar", "--agente", "triagem", "--funcoes", "01.01")
        async with cliente("tuttibom-ops-mcp", "--laboratorio", str(dir_), "--cliente", "triagem") as (ops, _):
            ativo = await dados(ops, "ops_ativar", referencia=aut["referencia"], funcoes=["01.01"])
            m = ativo["manifesto"]
            assert [s["id"] for s in m["skills"]] == ["ops-ana-atendimento", "ops-ana-triagem"]
            await dados(ops, "ops_ler_skill", "skill_indisponivel_no_escopo", id="ops-ana-resposta")
            for ref in m["skills"]:
                await dados(ops, "ops_ler_skill", id=ref["id"])
            estado = await dados(ops, "ops_confirmar_atribuicoes", manifesto_hash=m["hash"], resumo="Só leitura.")
            assert estado["areas"] == []
            await dados(ops, "ops_atendimento_responder", "fora_da_atribuicao", rascunho_ref="ras-fora")

    with laboratorio("triagem") as (dir_, admin):
        anyio.run(caso, dir_, admin)


def test_entrypoint_duravel_preserva_fila_e_replay_apos_reinicio(tmp_path):
    estado_dir = tmp_path / "estado"
    agente = "agente-sem-provedor"
    ids = ["01.01", "01.02"]

    async def turno(dir_, admin, chave):
        aut = admin("autorizar", "--agente", agente, "--funcoes", ",".join(ids))
        args = ("--laboratorio", str(dir_), "--cliente", agente)
        async with cliente("tuttibom-ops-mcp", *args) as (ops, _):
            ativo = await dados(ops, "ops_ativar", referencia=aut["referencia"], funcoes=ids)
            m = ativo["manifesto"]
            for skill in m["skills"]:
                await dados(ops, "ops_ler_skill", id=skill["id"])
            await dados(ops, "ops_confirmar_atribuicoes", manifesto_hash=m["hash"], resumo="Li as skills.")
            fila = (await dados(ops, "ops_atendimento_listar_pendencias"))["pendencias"]
            historico = await dados(ops, "ops_atendimento_ler_conversa", conversa_ref=CONVERSA)
            imagem = historico["mensagens"][1]["anexos"][0]
            texto = "Olá! Vi a imagem no laboratório."
            rascunho = await dados(
                ops, "ops_atendimento_preparar_resposta", conversa_ref=CONVERSA,
                texto=texto, message_ids=["msg-lab-01"], idempotency_key=chave,
                imagens_lidas=[imagem["sha256"]],
            )
            ref = rascunho["rascunho_ref"]
            aprovacao = admin("aprovar-resposta", entrada={
                "rascunho_ref": ref, "texto": texto, "conversa_ref": CONVERSA,
            })
            resposta = await dados(
                ops, "ops_atendimento_responder", rascunho_ref=ref,
                aprovacao_ref=aprovacao["aprovacao_ref"],
            )
            return [p["message_id"] for p in fila], resposta

    with laboratorio(agente, estado_dir=estado_dir) as (dir_, admin):
        tentativa = subprocess.run(
            [str(SCRIPTS / "tuttibom-ops-admin"), "--laboratorio", str(dir_.with_name("segundo")),
             "servir", "--estado-lab", str(estado_dir)],
            env=ENV, capture_output=True, text=True, timeout=8,
        )
        assert tentativa.returncode == 1
        assert not dir_.with_name("segundo").exists()
        pendentes1, envio1 = anyio.run(turno, dir_, admin, "chave-um")
        assert pendentes1 == ["msg-lab-01", "msg-lab-02"] and not envio1["replay"]
    with laboratorio(agente, estado_dir=estado_dir) as (dir_, admin):
        pendentes2, replay = anyio.run(turno, dir_, admin, "chave-dois")
        assert pendentes2 == ["msg-lab-02"]
        assert replay["replay"] and replay["envio_ref"] == envio1["envio_ref"]


def test_sucessor_reconcilia_ack_pendente_sem_novo_envio_apos_ttl(monkeypatch):
    lab = Laboratorio()
    funcoes = ["01.01", "01.02"]

    def conectar(agente):
        aut = lab.administrar("autorizar", {"agente": agente, "funcoes": funcoes})
        c = lab.clientes[agente]
        c.ativar(aut["referencia"], funcoes)
        s = c.conectar()
        s.confirmar_atribuicoes(s.manifesto().hash, "Confirmei as funções.")
        return s

    s1 = conectar("ana-01")
    texto = "Resposta sintética ao primeiro item."
    ler = lambda s: s.chamar("01.01", {"conversa_ref": CONVERSA})
    entrada = {
        "conversa_ref": CONVERSA, "idempotency_key": "intento-ack",
        "message_ids": ["msg-lab-01"], "texto": texto,
        "imagens_lidas": [ler(s1)["mensagens"][1]["anexos"][0]["sha256"]],
    }
    def preparar(s, args):
        return s.chamar("01.02", args, etapa="preparar")["rascunho_ref"]

    def aprovar(ref):
        retorno = lab.administrar("aprovar-resposta", {
            "rascunho_ref": ref, "conversa_ref": CONVERSA, "texto": texto,
        })
        return retorno["aprovacao_ref"]

    def enviar(s, ref, aprovacao):
        return s.chamar("01.02", {"rascunho_ref": ref, "aprovacao_ref": aprovacao})

    try:
        r1 = preparar(s1, entrada)
        p1 = aprovar(r1)
        with monkeypatch.context() as patch:
            patch.setattr(FilaLaboratorio, "marcar_entregues", lambda *_: [])
            parcial = enviar(s1, r1, p1)
        assert parcial["enviado"] and parcial["codigo"] == "ack_falhou"
        lab.administrar("revogar", {"agente": "ana-01"})
        with pytest.raises(ErroOps, match="token_revogado"):
            aprovar(r1)
        s2 = conectar("ana-02")
        ler(s2)
        monkeypatch.setattr(lab._atendimento, "_relogio",
                            lambda: datetime.now(timezone.utc) + timedelta(days=1))
        with pytest.raises(ErroOps, match="mensagem_ja_vinculada_a_envio"):
            preparar(s2, {**entrada, "idempotency_key": "outro-intento"})
        r2 = preparar(s2, entrada)
        assert r2 != r1
        with pytest.raises(ErroOps, match="aprovacao_exata_necessaria"):
            enviar(s2, r2, p1)
        reconciliado = enviar(s2, r2, aprovar(r2))
        assert reconciliado["ok"] and reconciliado["replay"]
        assert reconciliado["envio_ref"] == parcial["envio_ref"]
        assert reconciliado["acked"] == ["msg-lab-01"]
        assert len(lab._envios_ficticios) == 1
    finally:
        lab.servidor.close()
