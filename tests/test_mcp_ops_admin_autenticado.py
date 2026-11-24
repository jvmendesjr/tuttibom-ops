"""A opção de laboratório separa a credencial administrativa da operacional."""
import hashlib
import json
import secrets
import socket
import subprocess

import anyio

from test_mcp_ops_stdio import ENV, SCRIPTS, cliente, dados, laboratorio


def _credenciais(tmp_path):
    segredo = secrets.token_hex(32)
    digest = hashlib.sha256(segredo.encode()).hexdigest()
    servidor = tmp_path / "operador.json"
    servidor.touch(mode=0o600)
    servidor.write_text(json.dumps({"operador-lab": digest}))
    cliente_arq = tmp_path / "operador"
    cliente_arq.touch(mode=0o600)
    cliente_arq.write_text(segredo + "\n")
    return segredo, servidor, cliente_arq


def test_operador_autenticado_no_cli_e_no_socket(tmp_path):
    segredo, servidor, cliente_arq = _credenciais(tmp_path)
    incorreto = secrets.token_hex(32)
    outro = tmp_path / "outro"
    outro.touch(mode=0o600)
    outro.write_text(incorreto + "\n")

    def partida(pasta):
        return [
            str(SCRIPTS / "tuttibom-ops-admin"), "--laboratorio", str(pasta),
            "servir", "--digests-operador-lab", str(servidor),
        ]

    with laboratorio(comando_host=partida) as (pasta, admin):
        negado = {"ok": False, "codigo": "operador_nao_autenticado"}
        assert admin("listar-atribuicoes", rc=1) == negado
        assert admin("--credencial-operador", str(outro), "listar-atribuicoes", rc=1) == negado
        for args in ({}, {"credencial": incorreto, "operador": "operador-lab"},
                     {"credencial": ["nao-e-texto"]}):
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as canal:
                canal.settimeout(5)
                canal.connect(str(pasta / "admin.sock"))
                canal.sendall((json.dumps({"acao": "aprovar-resposta",
                                         "args": {}, **args}) + "\n").encode())
                with canal.makefile("rb") as resposta:
                    assert json.loads(resposta.readline()) == negado
        auth = ("--credencial-operador", str(cliente_arq))
        assert "funcoes" in admin(*auth, "listar-atribuicoes")
        recibo = admin(*auth, "autorizar", "--agente", "ana-01", "--funcoes", "01.01")
        assert recibo["funcoes"] == ["01.01"]
        relatorio = json.dumps(admin(*auth, "auditoria"))
        assert segredo not in relatorio and incorreto not in relatorio

    http = tmp_path / "http.json"
    http.touch(mode=0o600)
    digest = json.loads(servidor.read_text())["operador-lab"]
    http.write_text(json.dumps({"ana-01": digest}))
    pasta = tmp_path / "nao-criada"
    erro = subprocess.run(
        [*partida(pasta), "--digests-http", str(http),
         "--host-tailnet", "host-lab.test", "--porta-loopback", "45520"],
        env=ENV, capture_output=True, text=True, timeout=8,
    )
    assert (erro.returncode, erro.stderr.strip()) == (1, "laboratorio_indisponivel_ou_dados_invalidos")
    assert not pasta.exists()


def test_aprovacao_exata_exige_operador_autenticado(tmp_path):
    segredo, servidor, cliente_arq = _credenciais(tmp_path)

    def partida(pasta):
        return [
            str(SCRIPTS / "tuttibom-ops-admin"), "--laboratorio", str(pasta),
            "servir", "--digests-operador-lab", str(servidor),
            "--cliente-lab", "ana-01",
        ]

    with laboratorio(comando_host=partida) as (pasta, admin):
        auth = ("--credencial-operador", str(cliente_arq))
        negado = {"ok": False, "codigo": "operador_nao_autenticado"}
        assert admin("autorizar", "--agente", "ana-01", "--funcoes", "01.01,01.02",
                     rc=1) == negado
        aut = admin(*auth, "autorizar", "--agente", "ana-01", "--funcoes", "01.01,01.02")

        async def caso():
            lab = ("--laboratorio", str(pasta), "--cliente")
            async with cliente("tuttibom-ops-mcp", *lab, "ana-01") as (ana, _):
                ligado = await dados(ana, "ops_ativar", referencia=aut["referencia"],
                                     funcoes=["01.01", "01.02"])
                manifesto = ligado["manifesto"]
                for meta in manifesto["skills"]:
                    await dados(ana, "ops_ler_skill", id=meta["id"])
                await dados(ana, "ops_confirmar_atribuicoes", manifesto_hash=manifesto["hash"],
                            resumo="Li o escopo: só atuo com aprovação exata e exclusividade.")
                pendencias = (await dados(ana, "ops_atendimento_listar_pendencias"))["pendencias"]
                conversa = pendencias[0]["conversation_id"]
                msg_ids = [p["message_id"] for p in pendencias]
                midia = await ana.call_tool("ops_atendimento_ler_conversa",
                                            {"conversa_ref": conversa})
                imagem = midia.structuredContent["mensagens"][1]["anexos"][0]
                texto = "Recebi a imagem e o áudio sobre a fita de 22 mm. [LAB]"
                preparado = await dados(
                    ana, "ops_atendimento_preparar_resposta", conversa_ref=conversa,
                    texto=texto, idempotency_key="lab-admin-1", message_ids=msg_ids[:1],
                    imagens_lidas=[imagem["sha256"]], imagem_ref=imagem["midia_ref"])
                prova = {"conversa_ref": conversa, "rascunho_ref": preparado["rascunho_ref"],
                         "texto": texto,
                         "imagem_base64": midia.content[imagem["bloco_mcp"]].data}
                assert admin("aprovar-resposta", entrada=prova, rc=1) == negado
                divergente = admin(*auth, "aprovar-resposta",
                                   entrada={**prova, "texto": texto + " "}, rc=1)
                assert divergente["codigo"] == "conteudo_divergente"
                aprovacao = admin(*auth, "aprovar-resposta", entrada=prova)["aprovacao_ref"]
                envio = await dados(ana, "ops_atendimento_responder",
                                    rascunho_ref=prova["rascunho_ref"],
                                    aprovacao_ref=aprovacao)
                assert envio["enviado"] and envio["acked"] == msg_ids[:1]
                assert admin("revogar", "--agente", "ana-01", rc=1) == negado
                assert admin(*auth, "revogar", "--agente", "ana-01")["revogados"] >= 1
                await dados(ana, "ops_atendimento_responder", "token_revogado",
                            rascunho_ref=prova["rascunho_ref"], aprovacao_ref=aprovacao)
                assert segredo not in json.dumps(admin(*auth, "auditoria"))

        anyio.run(caso)
