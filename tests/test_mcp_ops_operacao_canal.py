"""Testes do modo de operação com canal real simulado em loopback (CLI + MIME + inspeção)."""
from __future__ import annotations

import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import subprocess
import threading

import anyio

from test_mcp_ops_stdio import ENV, SCRIPTS, cliente, dados, laboratorio
from tuttibom.mcp_ops.transporte import _resultado

JPEG_EXEMPLO = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"
WEBP_EXEMPLO = b"RIFF\x1a\x00\x00\x00WEBPVP8 \x0e\x00\x00\x00\x30\x01\x00\x9d\x01\x2a\x01\x00\x01\x00\x00\x00\x00\x00"
PNG_EXEMPLO = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _credenciais_operador(tmp_path: Path):
    segredo = secrets.token_hex(32)
    digest = hashlib.sha256(segredo.encode()).hexdigest()
    servidor = tmp_path / "operador.json"
    servidor.touch(mode=0o600)
    servidor.write_text(json.dumps({"operador-lab": digest}))
    cred = tmp_path / "operador.cred"
    cred.touch(mode=0o600)
    cred.write_text(segredo + "\n")
    return segredo, servidor, cred


def test_transporte_detecta_mime_png_jpeg_webp():
    payload = {
        "ok": True,
        "mensagens": [
            {
                "direcao": "incoming",
                "texto": "fotos",
                "anexos": [
                    {"file_type": "image", "midia_ref": "a1", "bytes": len(PNG_EXEMPLO),
                     "sha256": "h1", "conteudo": PNG_EXEMPLO},
                    {"file_type": "image", "midia_ref": "a2", "bytes": len(JPEG_EXEMPLO),
                     "sha256": "h2", "conteudo": JPEG_EXEMPLO},
                    {"file_type": "image", "midia_ref": "a3", "bytes": len(WEBP_EXEMPLO),
                     "sha256": "h3", "conteudo": WEBP_EXEMPLO},
                ],
            },
        ],
    }
    res = _resultado(payload)
    assert [res.content[0].mimeType, res.content[1].mimeType, res.content[2].mimeType] == [
        "image/png", "image/jpeg", "image/webp",
    ]


def test_inspecionar_e_listar_rascunhos_exigem_operador(tmp_path: Path):
    _, servidor, cred = _credenciais_operador(tmp_path)

    def partida(pasta: Path):
        return [
            str(SCRIPTS / "tuttibom-ops-admin"), "--laboratorio", str(pasta),
            "servir", "--digests-operador-lab", str(servidor), "--cliente-lab", "ana-01",
        ]

    with laboratorio(comando_host=partida) as (pasta, admin):
        auth = ("--credencial-operador", str(cred))
        negado = {"ok": False, "codigo": "operador_nao_autenticado"}
        assert admin("listar-rascunhos", rc=1) == negado
        aut = admin(*auth, "autorizar", "--agente", "ana-01", "--funcoes", "01.01,01.02")

        async def preparar():
            lab = ("--laboratorio", str(pasta), "--cliente")
            async with cliente("tuttibom-ops-mcp", *lab, "ana-01") as (ana, _):
                ligado = await dados(ana, "ops_ativar", referencia=aut["referencia"],
                                     funcoes=["01.01", "01.02"])
                manifesto = ligado["manifesto"]
                for meta in manifesto["skills"]:
                    await dados(ana, "ops_ler_skill", id=meta["id"])
                await dados(ana, "ops_confirmar_atribuicoes", manifesto_hash=manifesto["hash"],
                            resumo="Escopo confirmado.")
                pend = (await dados(ana, "ops_atendimento_listar_pendencias"))["pendencias"]
                conv = pend[0]["conversation_id"]
                midia = await ana.call_tool("ops_atendimento_ler_conversa", {"conversa_ref": conv})
                img = midia.structuredContent["mensagens"][1]["anexos"][0]
                prep = await dados(
                    ana, "ops_atendimento_preparar_resposta", conversa_ref=conv,
                    texto="Resposta exata para inspeção.", idempotency_key="insp-1",
                    message_ids=[pend[0]["message_id"]], imagens_lidas=[img["sha256"]],
                )
                ref = prep["rascunho_ref"]
                assert admin("inspecionar-rascunho", "--rascunho-ref", ref, rc=1) == negado
                lista = admin(*auth, "listar-rascunhos")["rascunhos"]
                assert len(lista) == 1 and lista[0]["rascunho_ref"] == ref
                detalhe = admin(*auth, "inspecionar-rascunho", "--rascunho-ref", ref)
                assert detalhe["conversa_ref"] == conv
                assert detalhe["texto"] == "Resposta exata para inspeção."
                assert detalhe["aprovado"] is False

        anyio.run(preparar)


def test_config_canal_recusa_sem_estado_ou_sem_operador_autenticado(tmp_path: Path):
    _, servidor, _ = _credenciais_operador(tmp_path)
    cfg = tmp_path / "canal.json"
    cfg.touch(mode=0o600)
    cfg.write_text(json.dumps({"conta_id": "2", "inbox_id": "1", "pat_arquivo": str(cfg)}))
    estado = tmp_path / "estado"
    estado.mkdir(mode=0o700)

    sem_estado = subprocess.run(
        [str(SCRIPTS / "tuttibom-ops-admin"), "--laboratorio", str(tmp_path / "h1"),
         "servir", "--digests-operador-lab", str(servidor), "--config-canal", str(cfg)],
        env=ENV, capture_output=True, text=True, timeout=8,
    )
    assert sem_estado.returncode == 1

    sem_operador = subprocess.run(
        [str(SCRIPTS / "tuttibom-ops-admin"), "--laboratorio", str(tmp_path / "h2"),
         "servir", "--estado-lab", str(estado), "--config-canal", str(cfg)],
        env=ENV, capture_output=True, text=True, timeout=8,
    )
    assert sem_operador.returncode == 1


def test_fluxo_completo_cli_config_canal_com_jpeg_e_ack(tmp_path: Path):
    _, servidor, cred = _credenciais_operador(tmp_path)
    pat = tmp_path / "pat.txt"
    pat.touch(mode=0o600)
    pat.write_text("pat_teste_isolado_123456\n")
    estado = tmp_path / "estado"
    estado.mkdir(mode=0o700)

    estado_mock = {
        "acks": [],
        "envios": [],
        "mensagens": [
            {
                "id": 901,
                "inbox_id": 1,
                "message_type": 0,
                "private": False,
                "content": "Oi, segue foto de referencia",
                "attachments": [
                    {
                        "id": 77,
                        "file_type": "image",
                        "data_url": "https://chatwoot.petemcasa.com/rails/active_storage/blobs/redirect/abc/foto.jpg",
                    },
                ],
            },
        ],
    }

    class ListenerHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/pending":
                itens = []
                if 901 not in estado_mock["acks"]:
                    itens.append({
                        "message_id": 901, "conversation_id": 42, "inbox_id": 1,
                        "contato_ref": "+5585999990016", "handoff": None,
                        "recebido_em": "2026-11-24T10:00:00Z",
                    })
                # Messenger (inbox 2) e grupo (@g.us) devem ser ignorados:
                itens.append({
                    "message_id": 902, "conversation_id": 43, "inbox_id": 2,
                    "contato_ref": "msg-user", "handoff": None,
                    "recebido_em": "2026-11-24T10:00:01Z",
                })
                itens.append({
                    "message_id": 903, "conversation_id": 44, "inbox_id": 1,
                    "contato_ref": "120363000@g.us", "handoff": None,
                    "recebido_em": "2026-11-24T10:00:02Z",
                })
                corpo = json.dumps({"pending": itens}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            tamanho = int(self.headers.get("Content-Length") or 0)
            dados_post = json.loads(self.rfile.read(tamanho).decode())
            if self.path == "/ack":
                estado_mock["acks"].extend(dados_post.get("message_ids", []))
                corpo = json.dumps({"ok": True, "marcados": len(dados_post.get("message_ids", []))}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, *args):
            pass

    class ChatwootHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/rails/active_storage/blobs/redirect/abc/foto.jpg":
                self.send_response(302)
                self.send_header("Location", "http://127.0.0.1/rails/active_storage/disk/xyz/foto.jpg")
                self.end_headers()
                return
            if self.path == "/rails/active_storage/disk/xyz/foto.jpg":
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(JPEG_EXEMPLO)))
                self.end_headers()
                self.wfile.write(JPEG_EXEMPLO)
                return
            if self.headers.get("api_access_token") != "pat_teste_isolado_123456":
                self.send_response(401)
                self.end_headers()
                return
            if self.path == "/api/v1/accounts/2/conversations/42":
                corpo = json.dumps({
                    "id": 42, "account_id": 2, "inbox_id": 1,
                    "meta": {"sender": {"id": 10, "identifier": "lead-piloto"}},
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)
                return
            if self.path.startswith("/api/v1/accounts/2/conversations/42/messages"):
                corpo = json.dumps({"payload": estado_mock["mensagens"]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)
                return
            self.send_response(404)
            self.end_headers()

        def do_POST(self):
            if self.headers.get("api_access_token") != "pat_teste_isolado_123456":
                self.send_response(401)
                self.end_headers()
                return
            tamanho = int(self.headers.get("Content-Length") or 0)
            bruto = self.rfile.read(tamanho)
            if self.path == "/api/v1/accounts/2/conversations/42/messages":
                estado_mock["envios"].append({
                    "content_type": self.headers.get("Content-Type", ""),
                    "corpo": bruto,
                })
                corpo = json.dumps({"id": 999, "inbox_id": 1, "message_type": 1}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, *args):
            pass

    srv_ls = ThreadingHTTPServer(("127.0.0.1", 0), ListenerHandler)
    srv_cw = ThreadingHTTPServer(("127.0.0.1", 0), ChatwootHandler)
    t_ls = threading.Thread(target=srv_ls.serve_forever, daemon=True)
    t_cw = threading.Thread(target=srv_cw.serve_forever, daemon=True)
    t_ls.start()
    t_cw.start()

    try:
        cfg = tmp_path / "canal.json"
        cfg.touch(mode=0o600)
        cfg.write_text(json.dumps({
            "conta_id": "2",
            "inbox_id": "1",
            "pat_arquivo": str(pat),
            "chatwoot_porta": srv_cw.server_port,
            "listener_porta": srv_ls.server_port,
            "conversas_ignoradas": ["8"],
            "intervalo_sync_segundos": 0.5,
        }))

        def partida(pasta: Path):
            return [
                str(SCRIPTS / "tuttibom-ops-admin"), "--laboratorio", str(pasta),
                "servir", "--estado-lab", str(estado),
                "--digests-operador-lab", str(servidor),
                "--config-canal", str(cfg),
                "--cliente-lab", "ana",
            ]

        with laboratorio("ana", comando_host=partida) as (pasta, admin):
            auth = ("--credencial-operador", str(cred))
            aut = admin(*auth, "autorizar", "--agente", "ana", "--funcoes", "01.01,01.02")

            async def caso():
                lab = ("--laboratorio", str(pasta), "--cliente")
                async with cliente("tuttibom-ops-mcp", *lab, "ana") as (ana, _):
                    ligado = await dados(ana, "ops_ativar", referencia=aut["referencia"],
                                         funcoes=["01.01", "01.02"])
                    assert ligado["ambiente"] == "operacao"
                    manifesto = ligado["manifesto"]
                    for meta in manifesto["skills"]:
                        await dados(ana, "ops_ler_skill", id=meta["id"])
                    await dados(ana, "ops_confirmar_atribuicoes", manifesto_hash=manifesto["hash"],
                                resumo="Operação WhatsApp confirmada.")
                    pend = (await dados(ana, "ops_atendimento_listar_pendencias"))["pendencias"]
                    assert len(pend) == 1
                    assert pend[0]["message_id"] == "901"
                    assert pend[0]["conversation_id"] == "42"
                    assert "contato_ref" not in pend[0]
                    assert "+5585" not in json.dumps(pend)

                    leitura = await ana.call_tool("ops_atendimento_ler_conversa", {"conversa_ref": "42"})
                    assert leitura.content[0].mimeType == "image/jpeg"
                    assert base64.b64decode(leitura.content[0].data) == JPEG_EXEMPLO
                    img = leitura.structuredContent["mensagens"][0]["anexos"][0]

                    texto_resp = "Recebi sua foto de referência! Vamos conferir os detalhes."
                    prep = await dados(
                        ana, "ops_atendimento_preparar_resposta", conversa_ref="42",
                        texto=texto_resp, idempotency_key="op-jpeg-1",
                        message_ids=["901"], imagens_lidas=[img["sha256"]],
                        imagem_ref=img["midia_ref"],
                    )
                    inspecao = admin(*auth, "inspecionar-rascunho", "--rascunho-ref", prep["rascunho_ref"])
                    assert inspecao["texto"] == texto_resp
                    aprov = admin(*auth, "aprovar-resposta", entrada={
                        "conversa_ref": "42",
                        "rascunho_ref": prep["rascunho_ref"],
                        "texto": texto_resp,
                        "imagem_base64": inspecao["imagem_base64"],
                    })["aprovacao_ref"]
                    envio = await dados(ana, "ops_atendimento_responder",
                                        rascunho_ref=prep["rascunho_ref"], aprovacao_ref=aprov)
                    assert envio["ok"] is True and envio["enviado"] is True
                    assert envio["envio_ref"] == "msg-999"
                    assert envio["acked"] == ["901"]

            anyio.run(caso)
            assert estado_mock["acks"] == [901]
            assert len(estado_mock["envios"]) == 1
            assert b"Content-Type: image/jpeg" in estado_mock["envios"][0]["corpo"]
            assert JPEG_EXEMPLO in estado_mock["envios"][0]["corpo"]
    finally:
        srv_ls.shutdown()
        srv_cw.shutdown()
