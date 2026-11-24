"""Entradas locais: host sintético, interface administrativa e ponte MCP stdio."""
from __future__ import annotations

import argparse
import asyncio
from contextlib import contextmanager
import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import signal
import socket
import stat
import sys
import time
from threading import Thread

import anyio
from mcp.types import JSONRPCMessage
from mcp.shared.message import SessionMessage
from pydantic import ValidationError

from .erros import ErroOps
from .identidade import validar_identificador
from .http_lab import ler_digests, servir_http
from .laboratorio import CLIENTES_LAB, BackendsAtendimento, Laboratorio
from .transporte import Conexao

_LIMITE = 512 * 1024
_ADMIN = "admin"
_OPERADOR = "operador-lab"
_RESERVADOS = {_ADMIN, _OPERADOR}
_CREDENCIAL = re.compile(r"[a-f0-9]{64}")


def _cliente_lab(valor: str) -> str:
    try:
        validar_identificador(valor, "cliente")
        if valor in _RESERVADOS:
            raise ValueError("reservado")
    except (ErroOps, ValueError):
        raise argparse.ArgumentTypeError("ID de cliente inválido ou reservado") from None
    return valor


def _privado(caminho: Path, tipo: int, modo: int) -> None:
    info = caminho.lstat()
    if (stat.S_IFMT(info.st_mode) != tipo or stat.S_IMODE(info.st_mode) != modo
            or info.st_uid != os.getuid()):
        raise PermissionError("permissao_lab_invalida")


async def _entrada(reader, stream) -> None:
    async with stream:
        while linha := await reader.readline():
            try:
                mensagem = SessionMessage(JSONRPCMessage.model_validate_json(linha))
            except ValidationError:
                mensagem = ValueError("mensagem_mcp_invalida")
            await stream.send(mensagem)


async def _saida(writer, stream) -> None:
    async with stream:
        async for mensagem in stream:
            writer.write(mensagem.message.model_dump_json(
                by_alias=True, exclude_none=True,
            ).encode() + b"\n")
            await writer.drain()


async def _mcp(reader, writer, lab: Laboratorio, cliente: str) -> None:
    conexao = Conexao(lab, lab.clientes[cliente])
    entrada, ler = anyio.create_memory_object_stream(0)
    enviar, saida = anyio.create_memory_object_stream(0)
    try:
        async with anyio.create_task_group() as tarefas:
            tarefas.start_soon(_entrada, reader, entrada)
            tarefas.start_soon(_saida, writer, saida)
            await conexao.mcp.run(ler, enviar, conexao.opcoes())
            tarefas.cancel_scope.cancel()
    finally:
        conexao.fechar()


def _operador_autenticado(pedido: dict, digest: str | None) -> bool:
    credencial = pedido.get("credencial")
    if digest is None:
        return credencial is None
    return (isinstance(credencial, str) and _CREDENCIAL.fullmatch(credencial) is not None
            and hmac.compare_digest(hashlib.sha256(credencial.encode("ascii")).hexdigest(), digest))


def _ler_credencial_operador(arquivo: Path) -> str:
    if not arquivo.is_absolute():
        raise ValueError("credencial_operador_invalida")
    with os.fdopen(os.open(arquivo, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "r") as f:
        info = os.fstat(f.fileno())
        if (not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600
                or info.st_uid != os.getuid()):
            raise ValueError("credencial_operador_invalida")
        credencial = f.read(66).removesuffix("\n")
    if _CREDENCIAL.fullmatch(credencial) is None:
        raise ValueError("credencial_operador_invalida")
    return credencial


async def _administrar(reader, writer, lab: Laboratorio, digest_operador: str | None) -> None:
    try:
        pedido = json.loads(await reader.readline())
        if not isinstance(pedido, dict):
            raise ValueError("argumento_invalido")
        if _operador_autenticado(pedido, digest_operador):
            resultado = lab.administrar(pedido["acao"], pedido["args"])
        else:
            resultado = {"ok": False, "codigo": "operador_nao_autenticado"}
    except ErroOps as exc:
        resultado = {"ok": False, "codigo": exc.codigo}
    except (KeyError, TypeError, ValueError):
        resultado = {"ok": False, "codigo": "argumento_invalido"}
    writer.write((json.dumps(resultado, ensure_ascii=False) + "\n").encode())
    await writer.drain()


@contextmanager
def _travar_estado(caminho: Path | None):
    if caminho is None:
        yield
        return
    caminho.mkdir(mode=0o700, exist_ok=True)
    _privado(caminho, stat.S_IFDIR, 0o700)
    fd = os.open(caminho / "host.lock", os.O_NOFOLLOW | os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def _ler_json_privado(arquivo: Path, erro: str) -> dict:
    if not arquivo.is_absolute():
        raise ValueError(erro)
    with os.fdopen(os.open(arquivo, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "r") as f:
        info = os.fstat(f.fileno())
        if (not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600
                or info.st_uid != os.getuid()):
            raise ValueError(erro)
        dados = json.loads(f.read(16385))
    if not isinstance(dados, dict) or not dados:
        raise ValueError(erro)
    return dados


def _montar_backends_canal(
    config_arquivo: Path, estado_dir: Path, *,
    configuracao: dict | None = None, protocolo_escopado: bool = False,
) -> tuple[BackendsAtendimento, tuple]:
    from .chatwoot_canal import BackendChatwootCanal
    from .entregas_duraveis import DiarioEntregas
    from .ingestao_listener import FilaIngestaoListener
    from .transcricao_offline import ErroTranscricaoOffline, TranscritorOffline

    cfg = (configuracao if configuracao is not None
           else _ler_json_privado(config_arquivo, "config_canal_invalida"))
    permitidos = {
        "conta_id", "inbox_id", "pat_arquivo", "chatwoot_porta", "listener_porta",
        "ignorados_arquivo", "conversas_ignoradas", "whisper_modelo_dir",
        "whisper_python", "whisper_ffmpeg", "intervalo_sync_segundos",
    }
    if not set(cfg) <= permitidos:
        raise ValueError("config_canal_invalida")
    conta_id = cfg.get("conta_id")
    inbox_id = cfg.get("inbox_id")
    pat_raw = cfg.get("pat_arquivo")
    if not all(isinstance(v, str) and v for v in (conta_id, inbox_id, pat_raw)):
        raise ValueError("config_canal_invalida")
    cw_porta = cfg.get("chatwoot_porta", 3001)
    ls_porta = cfg.get("listener_porta", 3021)
    intervalo = cfg.get("intervalo_sync_segundos", 2.0)
    if (type(cw_porta) is not int or type(ls_porta) is not int
            or type(intervalo) not in {int, float} or not 0.2 <= float(intervalo) <= 60.0):
        raise ValueError("config_canal_invalida")
    ignoradas_raw = cfg.get("conversas_ignoradas", [])
    if not isinstance(ignoradas_raw, list) or any(not isinstance(x, str) or not x for x in ignoradas_raw):
        raise ValueError("config_canal_invalida")
    conversas_ignoradas = frozenset(ignoradas_raw) | {"8"}
    ign_arq_raw = cfg.get("ignorados_arquivo")
    if ign_arq_raw is not None and (not isinstance(ign_arq_raw, str) or not Path(ign_arq_raw).is_absolute()):
        raise ValueError("config_canal_invalida")
    modelo_raw = cfg.get("whisper_modelo_dir")
    transcritor = None
    if modelo_raw is not None:
        if not isinstance(modelo_raw, str) or not modelo_raw:
            raise ValueError("config_canal_invalida")
        try:
            transcritor = TranscritorOffline(
                modelo_raw,
                python_executavel=cfg.get("whisper_python"),
                ffmpeg_executavel=cfg.get("whisper_ffmpeg"),
            )
        except ErroTranscricaoOffline as exc:
            raise ValueError("config_canal_invalida") from exc
    fila = FilaIngestaoListener(
        estado_dir / "fila.sqlite",
        conta_id=conta_id,
        inbox_id=inbox_id,
        porta_listener=ls_porta,
        conversas_ignoradas=conversas_ignoradas,
        **({"protocolo_escopado": True} if protocolo_escopado else {}),
    )
    backend = BackendChatwootCanal(
        conta_id=conta_id,
        inbox_id=inbox_id,
        pat_arquivo=Path(pat_raw),
        porta_loopback=cw_porta,
        ignorados_arquivo=Path(ign_arq_raw) if ign_arq_raw is not None else None,
        conversas_ignoradas=conversas_ignoradas,
    )
    diario = DiarioEntregas(estado_dir / "entregas.sqlite")
    diario.recuperar_reservas()
    backends = BackendsAtendimento(
        fila=fila, chat=backend, destino=backend, transcritor=transcritor, diario=diario,
    )
    return backends, (fila.sincronizar, float(intervalo))


def _montar_config_canais(config_arquivo: Path, estado_dir: Path) -> tuple:
    """Config legada ou pilhas por inbox, sempre no mesmo host/escritor."""
    cfg = _ler_json_privado(config_arquivo, "config_canal_invalida")
    if "canais" not in cfg:
        backends, sync = _montar_backends_canal(
            config_arquivo, estado_dir, configuracao=cfg,
        )
        return backends, None, sync
    canais = cfg["canais"]
    if (set(cfg) != {"canais"} or not isinstance(canais, list)
            or not 1 <= len(canais) <= 16):
        raise ValueError("config_canal_invalida")
    inboxes = []
    contas = set()
    for canal in canais:
        if not isinstance(canal, dict):
            raise ValueError("config_canal_invalida")
        inbox = canal.get("inbox_id")
        conta = canal.get("conta_id")
        if (not isinstance(inbox, str) or re.fullmatch(r"[1-9][0-9]*", inbox) is None
                or not isinstance(conta, str) or re.fullmatch(r"[1-9][0-9]*", conta) is None):
            raise ValueError("config_canal_invalida")
        inboxes.append(inbox)
        contas.add(conta)
    # inbox_id é a chave pública: contas distintas seriam ambíguas.
    if len(inboxes) != len(set(inboxes)) or len(contas) != 1:
        raise ValueError("config_canal_invalida")
    pilhas = {}
    sincronizacoes = []
    for inbox, canal in zip(inboxes, canais):
        pasta = estado_dir / f"inbox-{inbox}"
        pasta.mkdir(mode=0o700, exist_ok=True)
        _privado(pasta, stat.S_IFDIR, 0o700)
        backends, sync = _montar_backends_canal(
            config_arquivo, pasta, configuracao=canal, protocolo_escopado=True,
        )
        pilhas[inbox] = backends
        sincronizacoes.append(sync)

    proximas = [float("-inf")] * len(sincronizacoes)

    def sincronizar():
        agora = time.monotonic()
        for indice, (acao, intervalo) in enumerate(sincronizacoes):
            if agora < proximas[indice]:
                continue
            # Agenda mesmo se o canal falhar, evitando retry em laço apertado.
            proximas[indice] = agora + intervalo
            try:
                acao()
            except Exception:
                # Um canal indisponível não pode impedir a ingestão dos outros.
                # Não registrar exceções que possam conter dados do transporte.
                continue

    return None, pilhas, (sincronizar, min(s[1] for s in sincronizacoes))


async def _loop_sincronizacao(sincronizar, intervalo: float, parar: asyncio.Event) -> None:
    while not parar.is_set():
        try:
            await asyncio.to_thread(sincronizar)
        except Exception:
            pass
        try:
            await asyncio.wait_for(parar.wait(), timeout=intervalo)
        except TimeoutError:
            continue


async def _servir(
    diretorio: Path, clientes: tuple[str, ...], estado_dir: Path | None,
    *, backends: BackendsAtendimento | None = None, http: tuple | None = None,
    digest_operador: str | None = None, ambiente: str = "laboratorio",
    sync_loop: tuple | None = None,
    backends_por_inbox: dict[str, BackendsAtendimento] | None = None,
) -> None:
    # Diretório novo: não reaproveita nem apaga sockets de outra instância.
    diretorio.mkdir(mode=0o700)
    lab = None
    sockets: list[Path] = []
    servers = []
    conexoes: set[asyncio.Task] = set()
    tarefa_sync: asyncio.Task | None = None
    parar = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, parar.set)

    def handler(cliente: str):
        async def conectado(reader, writer):
            tarefa = asyncio.current_task()
            conexoes.add(tarefa)
            try:
                if cliente == _ADMIN:
                    await _administrar(reader, writer, lab, digest_operador)
                else:
                    await _mcp(reader, writer, lab, cliente)
            except Exception:
                print("conexao_lab_encerrada", file=sys.stderr)
            finally:
                writer.close()
                conexoes.discard(tarefa)
        return conectado

    try:
        _privado(diretorio, stat.S_IFDIR, 0o700)
        clientes_http = frozenset(http[0]) if http is not None else frozenset()
        lab = Laboratorio(clientes, estado_dir=estado_dir, backends=backends,
                          clientes_http=clientes_http, ambiente=ambiente,
                          **({"backends_por_inbox": backends_por_inbox}
                             if backends_por_inbox is not None else {}))
        for cliente in (_ADMIN, *(c for c in clientes if c not in clientes_http)):
            caminho = diretorio / f"{cliente}.sock"
            server = await asyncio.start_unix_server(handler(cliente), path=caminho, limit=_LIMITE)
            servers.append(server)
            sockets.append(caminho)
            caminho.chmod(0o600)
        if sync_loop is not None:
            tarefa_sync = asyncio.create_task(_loop_sincronizacao(*sync_loop, parar))
        if http is None:
            print("laboratorio_pronto", flush=True)
            await parar.wait()
        else:
            async with servir_http(lab, *http):
                print("laboratorio_pronto", flush=True)
                await parar.wait()
    finally:
        parar.set()
        if tarefa_sync is not None:
            tarefa_sync.cancel()
            await asyncio.gather(tarefa_sync, return_exceptions=True)
        for server in servers:
            server.close()
        for tarefa in tuple(conexoes):
            tarefa.cancel()
        await asyncio.gather(*conexoes, return_exceptions=True)
        for server in servers:
            await server.wait_closed()
        if lab is not None:
            lab.servidor.close()
        for caminho in sockets:
            caminho.unlink(missing_ok=True)
        diretorio.rmdir()


def _conectar(diretorio: Path, cliente: str) -> socket.socket:
    _privado(diretorio, stat.S_IFDIR, 0o700)
    caminho = diretorio / f"{cliente}.sock"
    _privado(caminho, stat.S_IFSOCK, 0o600)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(os.fspath(caminho))
    except OSError:
        sock.close()
        raise
    return sock


def _ponte(sock: socket.socket) -> None:
    def encaminhar():
        try:
            while bloco := os.read(sys.stdin.fileno(), 65536):
                sock.sendall(bloco)
        except OSError:
            pass
        finally:
            try:
                sock.shutdown(socket.SHUT_WR)
            except OSError:
                pass

    Thread(target=encaminhar, daemon=True).start()
    while bloco := sock.recv(65536):
        sys.stdout.buffer.write(bloco)
        sys.stdout.buffer.flush()


def _admin(args) -> int:
    if args.acao == "servir":
        if args.credencial_operador is not None:
            raise ValueError("credencial_operador_so_cliente")
        clientes = tuple(args.cliente_lab or CLIENTES_LAB)
        if len(clientes) > 32 or len(clientes) != len(set(clientes)):
            raise ValueError("cadastros_lab_invalidos")
        estado = args.estado_lab
        if estado is not None and (not estado.is_absolute() or estado.resolve().is_relative_to(args.laboratorio.resolve())):
            raise ValueError("diretorio_de_estado_invalido")
        campos = (args.digests_http, args.host_tailnet, args.porta_loopback)
        if any(c is not None for c in campos):
            if not all(c is not None for c in campos) or not 1024 <= args.porta_loopback <= 65535:
                raise ValueError("config_http_invalida")
            http = ler_digests(args.digests_http, clientes), args.host_tailnet, args.porta_loopback
        else:
            http = None
        digest_operador = (ler_digests(args.digests_operador_lab, (_OPERADOR,))[_OPERADOR]
                           if args.digests_operador_lab is not None else None)
        if http is not None and digest_operador in http[0].values():
            raise ValueError("credenciais_compartilhadas")
        if args.config_canal is not None and (estado is None or digest_operador is None):
            raise ValueError("canal_exige_estado_e_operador_autenticado")
        with _travar_estado(estado):
            if args.config_canal is None:
                asyncio.run(_servir(args.laboratorio, clientes, estado, http=http,
                                    digest_operador=digest_operador))
            else:
                backends, por_inbox, sync_loop = _montar_config_canais(args.config_canal, estado)
                asyncio.run(_servir(
                    args.laboratorio, clientes, None, backends=backends, http=http,
                    digest_operador=digest_operador, ambiente="operacao",
                    sync_loop=sync_loop,
                    backends_por_inbox=por_inbox,
                ))
        return 0
    valores = {k: v for k, v in vars(args).items()
               if k not in {"acao", "laboratorio", "credencial_operador"}}
    if args.acao == "aprovar-resposta":
        valores = json.loads(sys.stdin.buffer.read(_LIMITE))
        if not isinstance(valores, dict):
            raise ValueError("payload_invalido")
    pedido = {"acao": args.acao, "args": valores}
    if args.credencial_operador is not None:
        pedido["credencial"] = _ler_credencial_operador(args.credencial_operador)
    with _conectar(args.laboratorio, _ADMIN) as sock:
        sock.settimeout(10)
        sock.sendall(json.dumps(pedido).encode() + b"\n")
        with sock.makefile("rb") as leitura:
            resultado = json.loads(leitura.readline(_LIMITE))
    print(json.dumps(resultado, ensure_ascii=False))
    return int(resultado.get("ok") is False)


def main() -> int:
    parser = argparse.ArgumentParser(description="TuttiBom Ops, laboratório local sem produção")
    parser.add_argument("--laboratorio", type=Path, required=True, metavar="DIRETORIO_PRIVADO")
    modo = sys.argv[1]
    if modo == "admin":
        parser.add_argument("--credencial-operador", type=Path)
        acoes = parser.add_subparsers(dest="acao", required=True)
        servir = acoes.add_parser("servir")
        servir.add_argument("--cliente-lab", type=_cliente_lab, action="append")
        servir.add_argument("--estado-lab", type=Path, metavar="DIRETORIO_PRIVADO_ABSOLUTO")
        servir.add_argument("--digests-http", type=Path)
        servir.add_argument("--digests-operador-lab", type=Path)
        servir.add_argument("--config-canal", type=Path)
        servir.add_argument("--host-tailnet")
        servir.add_argument("--porta-loopback", type=int)
        for acao in ("listar-atribuicoes", "listar-rascunhos", "aprovar-resposta",
                     "auditoria"):
            acoes.add_parser(acao)
        acoes.add_parser("reconciliar-acks").add_argument("--inbox-id", dest="inbox_id")
        acoes.add_parser("inspecionar-rascunho").add_argument(
            "--rascunho-ref", required=True,
        )
        autorizar = acoes.add_parser("autorizar")
        autorizar.add_argument("--agente", type=_cliente_lab, required=True)
        autorizar.add_argument("--funcoes", required=True)
        acoes.add_parser("revogar").add_argument("--agente", type=_cliente_lab, required=True)
    else:
        parser.add_argument("--cliente", type=_cliente_lab, required=True)
    args = parser.parse_args(sys.argv[2:])
    if not args.laboratorio.is_absolute():
        parser.error("--laboratorio exige caminho absoluto")
    try:
        if modo == "admin":
            return _admin(args)
        with _conectar(args.laboratorio, args.cliente) as sock:
            _ponte(sock)
        return 0
    except (OSError, ValueError):
        print("laboratorio_indisponivel_ou_dados_invalidos", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
