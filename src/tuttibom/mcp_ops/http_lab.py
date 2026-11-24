"""Streamable HTTP restrito ao loopback, para proxy HTTPS privado do operador."""
from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager, nullcontext
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat

from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import Response

from .transporte import Conexao

CAMINHO = "/tuttibom-ops-lab/mcp"
_CRED = re.compile(rb"Bearer ([a-f0-9]{64})")


def ler_digests(arquivo: Path, clientes: tuple[str, ...]) -> dict[str, str]:
    if not arquivo.is_absolute():
        raise ValueError("config_http_invalida")
    with os.fdopen(os.open(arquivo, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "r") as f:
        s = os.fstat(f.fileno())
        if not stat.S_ISREG(s.st_mode) or stat.S_IMODE(s.st_mode) != 0o600 or s.st_uid != os.getuid():
            raise ValueError("config_http_invalida")
        dados = json.loads(f.read(8193))
    if (not isinstance(dados, dict) or not dados or not set(dados) <= set(clientes)
            or any(not isinstance(v, str) or re.fullmatch(r"[a-f0-9]{64}", v) is None for v in dados.values())
            or len(set(dados.values())) != len(dados)):
        raise ValueError("config_http_invalida")
    return dados


class _PorSessao:
    def __init__(self, lab, cliente):
        self.lab, self.cliente = lab, cliente

    def create_initialization_options(self):
        return Conexao(self.lab, self.cliente, preconfigurada=True).opcoes()

    async def run(self, entrada, saida, opcoes, **kwargs):
        conexao = Conexao(self.lab, self.cliente, preconfigurada=True)
        try:
            await conexao.mcp.run(entrada, saida, opcoes, **kwargs)
        finally:
            conexao.fechar()


@asynccontextmanager
async def aplicativo(lab, digests: dict[str, str], host: str, porta: int):
    seguranca = TransportSecuritySettings(
        allowed_hosts=[host, f"127.0.0.1:{porta}"],
        allowed_origins=[f"https://{host}"],
    )
    async with AsyncExitStack() as pilha:
        managers = {}
        for nome in digests:
            manager = StreamableHTTPSessionManager(
                _PorSessao(lab, lab.clientes[nome]), json_response=True,
                security_settings=seguranca, max_sessions=4, session_idle_timeout=300,
                max_request_body_size=64 * 1024,
            )
            await pilha.enter_async_context(manager.run())
            managers[nome] = manager

        async def app(scope, receive, send):
            if scope["type"] != "http":
                return
            if scope["path"] != CAMINHO or scope["query_string"]:
                return await Response(status_code=404)(scope, receive, send)
            headers = [v for k, v in scope["headers"] if k == b"authorization"]
            cred = _CRED.fullmatch(headers[0]) if len(headers) == 1 else None
            if cred:
                digest = hashlib.sha256(cred[1]).hexdigest()
                for nome, esperado in digests.items():
                    if hmac.compare_digest(digest, esperado):
                        if not lab.cliente_http_ativo(nome):
                            return await Response(status_code=403)(scope, receive, send)
                        # Streamable HTTP permite servidor apenas POST/DELETE.
                        # Não abrimos um SSE autônomo para um cliente ocioso.
                        if scope["method"] == "GET":
                            return await Response(
                                status_code=405, headers={"Allow": "POST, DELETE"},
                            )(scope, receive, send)
                        return await managers[nome].handle_request(scope, receive, send)
            return await Response(status_code=401, headers={"WWW-Authenticate": "Bearer"})(scope, receive, send)

        yield app


@asynccontextmanager
async def servir_http(lab, digests, host, porta):
    import asyncio
    import socket
    import uvicorn

    if re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)+\.ts\.net(?::[0-9]{1,5})?", host) is None:
        raise ValueError("host_tailnet_invalido")

    class _Servidor(uvicorn.Server):
        def capture_signals(self):
            return nullcontext()

    async with aplicativo(lab, digests, host, porta) as app:
        config = uvicorn.Config(app, lifespan="off", proxy_headers=False, access_log=False, log_level="warning")
        servidor = _Servidor(config)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", porta))
            sock.listen(32)
            tarefa = asyncio.create_task(servidor.serve(sockets=[sock]))
            try:
                async with asyncio.timeout(5):
                    while not servidor.started:
                        if tarefa.done():
                            tarefa.result()
                            raise ValueError("http_indisponivel")
                        await asyncio.sleep(0.01)
                yield
            finally:
                servidor.should_exit = True
                tarefa.cancel()
                await asyncio.gather(tarefa, return_exceptions=True)
