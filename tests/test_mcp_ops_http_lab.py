import hashlib
import json
import secrets
import socket

import anyio
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from test_mcp_ops_stdio import dados, laboratorio, SCRIPTS
from tuttibom.mcp_ops.http_lab import CAMINHO


def test_http_identidade_atribuicao_revogacao_e_nova_sessao(tmp_path):
    nomes = ("ana-remota", "produto-remoto")
    local = "cliente-stdio"
    chaves = {nome: secrets.token_hex(32) for nome in nomes}
    config = tmp_path / "digests.json"
    config.touch(mode=0o600)
    config.write_text(json.dumps({n: hashlib.sha256(k.encode()).hexdigest() for n, k in chaves.items()}))
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        porta = sock.getsockname()[1]
    url = f"http://127.0.0.1:{porta}{CAMINHO}"
    host = "host-lab.example.ts.net"

    def partida(dir_):
        return [str(SCRIPTS / "tuttibom-ops-admin"), "--laboratorio", str(dir_), "servir",
                "--cliente-lab", local, "--cliente-lab", nomes[0], "--cliente-lab", nomes[1],
                "--digests-http", str(config), "--host-tailnet", host, "--porta-loopback", str(porta)]

    async def caso(admin):
        ana, produto = nomes
        headers = {"Authorization": f"Bearer {chaves[ana]}"}
        headers_produto = {"Authorization": f"Bearer {chaves[produto]}"}
        async with httpx.AsyncClient() as sem:
            assert (await sem.get(url)).status_code == 401
            assert (await sem.post(url, headers=headers)).status_code == 403
            assert admin("autorizar", "--agente", ana, "--funcoes", "01.02",
                         rc=1)["codigo"] == "resposta_requer_leitura"
            recibo = admin("autorizar", "--agente", ana, "--funcoes", "01.01")
            assert recibo["funcoes"] == ["01.01"] and "referencia" not in recibo
            assert admin("autorizar", "--agente", ana, "--funcoes", "01.01,01.02",
                         rc=1)["codigo"] == "cliente_ja_ativo"
            admin("autorizar", "--agente", produto, "--funcoes", "03.01")
            assert (await sem.get(url, headers=headers)).status_code == 405
            assert (await sem.post(url + "?token=nao-aceito", headers=headers)).status_code == 404
            assert (await sem.get(url.replace(CAMINHO, "/admin"), headers=headers)).status_code == 404
        async with httpx.AsyncClient(headers=headers) as h:
            async with streamable_http_client(url, http_client=h) as (ler, escrever, session_id):
                async with ClientSession(ler, escrever) as ops:
                    assert (await ops.initialize()).serverInfo.name == "tuttibom-ops-mcp"
                    assert {t.name for t in (await ops.list_tools()).tools} == {
                        "ops_minhas_atribuicoes", "ops_confirmar_atribuicoes", "ops_estado",
                        "ops_auditoria", "ops_ler_skill", "ops_atendimento_listar_pendencias",
                        "ops_atendimento_ler_conversa",
                    }
                    m = await dados(ops, "ops_minhas_atribuicoes")
                    assert [f["id"] for f in m["funcoes"]] == ["01.01"]
                    assert {s["id"] for s in m["skills"]} == {"ops-ana-atendimento", "ops-ana-triagem"}
                    await dados(ops, "ops_atendimento_listar_pendencias", "confirmacao_pendente")
                    await dados(ops, "ops_ativar", "fora_da_atribuicao")
                    await dados(ops, "ops_reconectar", "fora_da_atribuicao")
                    await dados(ops, "ops_ler_skill", "skill_indisponivel_no_escopo",
                                id="ops-ana-resposta")
                    async with httpx.AsyncClient(headers={
                        **headers_produto,
                        "Mcp-Session-Id": session_id(),
                    }) as errado:
                        assert (await errado.delete(url)).status_code == 404
                    for ref in m["skills"]:
                        await dados(ops, "ops_ler_skill", id=ref["id"])
                    assert (await dados(ops, "ops_confirmar_atribuicoes", manifesto_hash=m["hash"],
                                        resumo="Li as skills."))["areas"] == []
                    assert (await dados(ops, "ops_atendimento_listar_pendencias"))["pendencias"]
                    await dados(ops, "ler_doc", "fora_da_atribuicao")
                    await dados(ops, "ops_atendimento_responder", "fora_da_atribuicao",
                                rascunho_ref="um-rascunho")
        async with httpx.AsyncClient(headers=headers) as h:
            async with streamable_http_client(url, http_client=h) as (ler, escrever, _):
                async with ClientSession(ler, escrever) as ops:
                    await ops.initialize()
                    assert (await dados(ops, "ops_minhas_atribuicoes"))["hash"] == m["hash"]
                    await dados(ops, "ops_atendimento_ler_conversa", "confirmacao_pendente",
                                conversa_ref="conv-lab-01")
                    await dados(ops, "ops_confirmar_atribuicoes", "skills_pendentes",
                                manifesto_hash=m["hash"], resumo="Ainda não li nesta sessão.")
                    assert admin("revogar", "--agente", ana)["revogados"] == 1
                    assert (await h.post(url)).status_code == 403
                    assert admin("autorizar", "--agente", ana, "--funcoes", "01.01",
                                 rc=1)["codigo"] == "credencial_http_revogada"
        async with httpx.AsyncClient(headers=headers_produto) as h:
            async with streamable_http_client(url, http_client=h) as (ler, escrever, _):
                async with ClientSession(ler, escrever) as ops:
                    await ops.initialize()
                    assert [f["id"] for f in (await dados(ops, "ops_minhas_atribuicoes"))["funcoes"]] == ["03.01"]

    with laboratorio(local, *nomes, comando_host=partida) as (dir_, admin):
        assert not any((dir_ / f"{nome}.sock").exists() for nome in nomes)
        with anyio.from_thread.start_blocking_portal() as portal:
            portal.call(caso, admin)
