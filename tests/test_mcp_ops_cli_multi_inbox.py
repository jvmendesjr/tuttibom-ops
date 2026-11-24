"""CLI multi-inbox com servidores loopback só de teste. Sem serviço real."""
from __future__ import annotations

import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import socket
import sqlite3
import subprocess
import threading
from urllib.parse import parse_qs, urlsplit

import anyio
import pytest

from test_mcp_ops_stdio import ENV, SCRIPTS, cliente, dados, laboratorio

TEXTO_ENTRADA = "Mensagem ficticia da inbox dois."
TEXTO_RESPOSTA = "Resposta ficticia da inbox dois."
TOKEN = "pat-sintetico-multi"
MSG_INBOX2 = 9002
CONV_INBOX2 = 52
BACKLOG = 25
RECUSA = "laboratorio_indisponivel_ou_dados_invalidos"


def _porta_fechada() -> int:
    while True:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            porta = sock.getsockname()[1]
        if porta not in {3000, 3001, 3021}:
            return porta


def _privado(caminho: Path, texto: str) -> None:
    caminho.write_text(texto)
    caminho.chmod(0o600)


def _operador(tmp: Path) -> tuple[Path, Path]:
    segredo = secrets.token_hex(32)
    digest = hashlib.sha256(segredo.encode()).hexdigest()
    servidor = tmp / "operador.json"
    _privado(servidor, json.dumps({"operador-lab": digest}))
    cred = tmp / "operador.cred"
    _privado(cred, segredo + "\n")
    return servidor, cred


def _pat(tmp: Path) -> Path:
    caminho = tmp / "pat.txt"
    _privado(caminho, TOKEN + "\n")
    return caminho


def _canal(inbox: str, pat: Path, porta_cw: int, porta_ls: int, conta: str = "2") -> dict:
    return {
        "conta_id": conta,
        "inbox_id": inbox,
        "pat_arquivo": str(pat),
        "chatwoot_porta": porta_cw,
        "listener_porta": porta_ls,
        "intervalo_sync_segundos": 60,
    }


def _gravar(caminho: Path, cfg: object) -> None:
    _privado(caminho, json.dumps(cfg))


def _estado(tmp: Path) -> Path:
    pasta = tmp / "estado"
    pasta.mkdir(mode=0o700)
    return pasta


def _argv_servir(lab: Path, estado: Path, digests: Path, cfg: Path) -> list[str]:
    return [
        str(SCRIPTS / "tuttibom-ops-admin"), "--laboratorio", str(lab),
        "servir", "--estado-lab", str(estado),
        "--digests-operador-lab", str(digests),
        "--config-canal", str(cfg),
        "--cliente-lab", "ana",
    ]


def _recusar(argv: list[str]) -> None:
    res = subprocess.run(argv, env=ENV, capture_output=True, text=True, timeout=8)
    assert (res.returncode, res.stderr.strip()) == (1, RECUSA), res.stderr
    assert "laboratorio_pronto" not in res.stdout


def _estados_fila(caminho: Path) -> dict[str, int]:
    with sqlite3.connect(caminho) as conn:
        return dict(conn.execute(
            "SELECT estado, COUNT(*) FROM pendencias_v1 GROUP BY estado"
        ))


def _acks_locais(caminho: Path) -> int:
    with sqlite3.connect(caminho) as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM acks_listener_pendentes_v1"
        ).fetchone()[0]


@pytest.mark.parametrize("caso", [
    "duplicata",
    "contas_distintas",
    "inbox_zero",
    "inbox_zero_a_esquerda",
    "inbox_inteiro",
    "dezessete",
    "lista_vazia",
    "canais_nao_lista",
    "chave_extra",
    "item_nao_dict",
    "modo_aberto",
    "caminho_relativo",
])
def test_config_multi_invalida_nao_sobe(tmp_path: Path, caso: str):
    digests, _ = _operador(tmp_path)
    pat = _pat(tmp_path)
    porta = _porta_fechada()
    um = _canal("1", pat, porta, porta)
    dois = _canal("2", pat, porta, porta)
    cfg_path = tmp_path / "canal.json"
    if caso == "duplicata":
        _gravar(cfg_path, {"canais": [um, dict(um)]})
    elif caso == "contas_distintas":
        _gravar(cfg_path, {"canais": [um, _canal("2", pat, porta, porta, conta="3")]})
    elif caso == "inbox_zero":
        _gravar(cfg_path, {"canais": [_canal("0", pat, porta, porta), dois]})
    elif caso == "inbox_zero_a_esquerda":
        _gravar(cfg_path, {"canais": [_canal("02", pat, porta, porta)]})
    elif caso == "inbox_inteiro":
        invalido = dict(um)
        invalido["inbox_id"] = 1
        _gravar(cfg_path, {"canais": [invalido]})
    elif caso == "dezessete":
        _gravar(cfg_path, {"canais": [
            _canal(str(n), pat, porta, porta) for n in range(1, 18)
        ]})
    elif caso == "lista_vazia":
        _gravar(cfg_path, {"canais": []})
    elif caso == "canais_nao_lista":
        _gravar(cfg_path, {"canais": um})
    elif caso == "chave_extra":
        _gravar(cfg_path, {"canais": [um, dois], "extra": True})
    elif caso == "item_nao_dict":
        _gravar(cfg_path, {"canais": [um, "2"]})
    elif caso == "modo_aberto":
        _gravar(cfg_path, {"canais": [um, dois]})
        cfg_path.chmod(0o644)
    elif caso == "caminho_relativo":
        cfg_path = Path("canal.json")
    estado = _estado(tmp_path)
    lab = tmp_path / "lab-nao-sobe"
    _recusar(_argv_servir(lab, estado, digests, cfg_path))
    assert not lab.exists()
    assert not (estado / "inbox-1").exists()
    assert not (estado / "inbox-2").exists()


def test_symlink_de_config_pat_estado_e_trava_e_recusado(tmp_path: Path):
    digests, _ = _operador(tmp_path)
    pat = _pat(tmp_path)
    porta = _porta_fechada()
    estado = _estado(tmp_path)
    real = tmp_path / "canal-real.json"
    _gravar(real, {"canais": [
        _canal("1", pat, porta, porta),
        _canal("2", pat, porta, porta),
    ]})
    link_cfg = tmp_path / "canal-link.json"
    link_cfg.symlink_to(real)
    _recusar(_argv_servir(tmp_path / "lab-cfg", estado, digests, link_cfg))

    link_pat = tmp_path / "pat-link.txt"
    link_pat.symlink_to(pat)
    cfg_pat = tmp_path / "canal-pat.json"
    _gravar(cfg_pat, {"canais": [
        _canal("1", link_pat, porta, porta),
        _canal("2", link_pat, porta, porta),
    ]})
    _recusar(_argv_servir(tmp_path / "lab-pat", estado, digests, cfg_pat))
    assert not (estado / "inbox-2").exists()

    alvo = tmp_path / "estado-real"
    alvo.mkdir(mode=0o700)
    link_estado = tmp_path / "estado-link"
    link_estado.symlink_to(alvo, target_is_directory=True)
    cfg_ok = tmp_path / "canal-ok.json"
    _gravar(cfg_ok, {"canais": [_canal("1", pat, porta, porta)]})
    _recusar(_argv_servir(tmp_path / "lab-estado", link_estado, digests, cfg_ok))
    assert not (alvo / "host.lock").exists()
    assert not (alvo / "inbox-1").exists()

    trava = tmp_path / "trava-alvo"
    _privado(trava, "x")
    trava_estado = estado / "host.lock"
    if trava_estado.is_symlink() or trava_estado.exists():
        trava_estado.unlink()
    trava_estado.symlink_to(trava)
    _recusar(_argv_servir(tmp_path / "lab-trava", estado, digests, cfg_ok))


def test_config_legada_grava_sqlite_na_raiz(tmp_path: Path):
    digests, _ = _operador(tmp_path)
    pat = _pat(tmp_path)
    porta = _porta_fechada()
    estado = _estado(tmp_path)
    cfg = tmp_path / "legado.json"
    _gravar(cfg, _canal("1", pat, porta, porta))

    def partida(pasta: Path):
        return _argv_servir(pasta, estado, digests, cfg)

    with laboratorio("ana", comando_host=partida):
        assert (estado / "fila.sqlite").is_file()
        assert (estado / "entregas.sqlite").is_file()
        assert (estado / "host.lock").is_file()
        assert not (estado / "inbox-1").exists()
    assert (estado / "fila.sqlite").is_file()
    assert (estado / "entregas.sqlite").is_file()


def test_dezesseis_canais_isolam_diretorios(tmp_path: Path):
    digests, _ = _operador(tmp_path)
    pat = _pat(tmp_path)
    porta = _porta_fechada()
    estado = _estado(tmp_path)
    cfg = tmp_path / "dezesseis.json"
    _gravar(cfg, {"canais": [
        _canal(str(n), pat, porta, porta) for n in range(1, 17)
    ]})

    def partida(pasta: Path):
        return _argv_servir(pasta, estado, digests, cfg)

    with laboratorio("ana", comando_host=partida):
        inodes = set()
        for n in range(1, 17):
            pasta = estado / f"inbox-{n}"
            assert pasta.is_dir()
            assert pasta.stat().st_mode & 0o777 == 0o700
            fila = pasta / "fila.sqlite"
            diario = pasta / "entregas.sqlite"
            assert fila.is_file() and diario.is_file()
            assert not (pasta / "host.lock").exists()
            inodes.add(fila.stat().st_ino)
            inodes.add(diario.stat().st_ino)
        assert len(inodes) == 32
        assert not (estado / "fila.sqlite").exists()
        assert (estado / "host.lock").is_file()
    assert (estado / "inbox-16" / "fila.sqlite").is_file()


def test_lease_do_escritor_e_global(tmp_path: Path):
    digests, _ = _operador(tmp_path)
    pat = _pat(tmp_path)
    porta = _porta_fechada()
    estado = _estado(tmp_path)
    cfg = tmp_path / "canal.json"
    _gravar(cfg, {"canais": [
        _canal("1", pat, porta, porta),
        _canal("2", pat, porta, porta),
    ]})

    def partida(pasta: Path):
        return _argv_servir(pasta, estado, digests, cfg)

    with laboratorio("ana", comando_host=partida):
        outro = tmp_path / "outro-lab"
        _recusar(_argv_servir(outro, estado, digests, cfg))
        assert not outro.exists()
        assert not (estado / "inbox-1" / "host.lock").exists()
        assert not (estado / "inbox-2" / "host.lock").exists()


@pytest.mark.parametrize("valor", [False, 0, "", {}])

def test_conversas_ignoradas_falsey_nao_lista_sao_invalidas(tmp_path: Path, valor):
    from tuttibom.mcp_ops import cli

    pat = _pat(tmp_path)
    porta = _porta_fechada()
    canal = _canal("1", pat, porta, porta)
    canal["conversas_ignoradas"] = valor
    cfg = tmp_path / f"falsey-{type(valor).__name__}.json"
    _gravar(cfg, {"canais": [canal]})
    with pytest.raises(ValueError, match="config_canal_invalida"):
        cli._montar_config_canais(cfg, _estado(tmp_path))


def test_agregador_respeita_intervalo_individual_e_isola_excecao(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    import time
    from tuttibom.mcp_ops import cli

    pat = _pat(tmp_path)
    porta = _porta_fechada()
    canais = []
    for inbox, intervalo in (("1", 60), ("2", 0.5)):
        canal = _canal(inbox, pat, porta, porta)
        canal["intervalo_sync_segundos"] = intervalo
        canais.append(canal)
    cfg = tmp_path / "intervalos.json"
    _gravar(cfg, {"canais": canais})

    chamadas = []
    falhar_lento = [False]

    def backend_fake(_config, _estado, *, configuracao, protocolo_escopado):
        assert protocolo_escopado is True
        inbox = configuracao["inbox_id"]

        def acao():
            chamadas.append(inbox)
            if inbox == "1" and falhar_lento[0]:
                raise RuntimeError("falha sintetica isolada")

        return object(), (acao, float(configuracao["intervalo_sync_segundos"]))

    agora = [100.0]
    monkeypatch.setattr(cli, "_montar_backends_canal", backend_fake)
    monkeypatch.setattr(time, "monotonic", lambda: agora[0])
    backends, pilhas, sync_loop = cli._montar_config_canais(cfg, _estado(tmp_path))
    assert backends is None
    assert set(pilhas) == {"1", "2"}
    sincronizar, intervalo = sync_loop
    assert intervalo == 0.5

    sincronizar()
    assert chamadas == ["1", "2"]
    chamadas.clear()
    agora[0] += 0.5
    sincronizar()
    assert chamadas == ["2"]

    chamadas.clear()
    falhar_lento[0] = True
    agora[0] += 60
    sincronizar()
    assert chamadas == ["1", "2"]

def _pendentes(eventos: list[dict], inbox: int, depois: int, limite: int) -> list[dict]:
    linhas = [
        item for item in eventos
        if item["estado"] == "pendente"
        and item["inbox_id"] == inbox
        and item["message_id"] > depois
    ]
    linhas.sort(key=lambda item: item["message_id"])
    return linhas[:limite]


def _servidores(eventos: list[dict], *, scoped: bool):
    consultas: list[dict] = []
    acks: list[dict] = []
    envios: list[dict] = []
    trava = threading.Lock()

    class Listener(BaseHTTPRequestHandler):
        def do_GET(self):
            partes = urlsplit(self.path)
            if partes.path != "/pending":
                self.send_response(404)
                self.end_headers()
                return
            qs = parse_qs(partes.query)
            if not scoped or "inbox_id" not in qs:
                corpo = json.dumps({"scoped": False, "pending": []}).encode()
            else:
                inbox = int(qs["inbox_id"][0])
                depois = int(qs["after_message_id"][0])
                limite = int(qs["limit"][0])
                with trava:
                    pagina = _pendentes(eventos, inbox, depois, limite)
                    consultas.append({
                        "inbox_id": inbox,
                        "after_message_id": depois,
                        "limit": limite,
                        "ids": [item["message_id"] for item in pagina],
                    })
                corpo = json.dumps({
                    "scoped": True, "inbox_id": inbox, "pending": pagina,
                }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def do_POST(self):
            tamanho = int(self.headers.get("Content-Length") or 0)
            pedido = json.loads(self.rfile.read(tamanho).decode())
            if self.path != "/ack":
                self.send_response(404)
                self.end_headers()
                return
            inbox = pedido["inbox_id"]
            aceitos = []
            rejeitados = []
            with trava:
                for mid in pedido["message_ids"]:
                    alvo = next((
                        item for item in eventos
                        if item["message_id"] == mid and item["inbox_id"] == inbox
                        and item["estado"] in {"pendente", "entregue"}
                    ), None)
                    if alvo is None:
                        rejeitados.append(mid)
                    else:
                        alvo["estado"] = "entregue"
                        aceitos.append(mid)
                acks.append({
                    "inbox_id": inbox,
                    "message_ids": list(pedido["message_ids"]),
                    "accepted": list(aceitos),
                })
            corpo = json.dumps({
                "ok": True, "scoped": True, "inbox_id": inbox,
                "accepted": aceitos, "rejected": rejeitados,
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def log_message(self, *_args):
            pass

    class Chatwoot(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.headers.get("api_access_token") != TOKEN:
                self.send_response(401)
                self.end_headers()
                return
            if self.path == f"/api/v1/accounts/2/conversations/{CONV_INBOX2}":
                corpo = json.dumps({
                    "id": CONV_INBOX2, "account_id": 2, "inbox_id": 2,
                    "meta": {"sender": {"id": 7, "identifier": "lead-ficticio"}},
                }).encode()
            elif self.path.startswith(
                f"/api/v1/accounts/2/conversations/{CONV_INBOX2}/messages"
            ):
                corpo = json.dumps({"payload": [{
                    "id": 800, "inbox_id": 2, "message_type": 0, "private": False,
                    "content": TEXTO_ENTRADA, "attachments": [],
                }]}).encode()
            else:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def do_POST(self):
            if self.headers.get("api_access_token") != TOKEN:
                self.send_response(401)
                self.end_headers()
                return
            tamanho = int(self.headers.get("Content-Length") or 0)
            bruto = self.rfile.read(tamanho)
            if self.path != f"/api/v1/accounts/2/conversations/{CONV_INBOX2}/messages":
                self.send_response(404)
                self.end_headers()
                return
            envios.append({"corpo": bruto})
            corpo = json.dumps({"id": 910, "inbox_id": 2, "message_type": 1}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def log_message(self, *_args):
            pass

    listener = ThreadingHTTPServer(("127.0.0.1", 0), Listener)
    chatwoot = ThreadingHTTPServer(("127.0.0.1", 0), Chatwoot)
    threading.Thread(target=listener.serve_forever, daemon=True).start()
    threading.Thread(target=chatwoot.serve_forever, daemon=True).start()
    return listener, chatwoot, consultas, acks, envios


def _parar(*servidores) -> None:
    for servidor in servidores:
        servidor.shutdown()
        servidor.server_close()


async def _ativar(ana, aut: dict) -> None:
    ligado = await dados(
        ana, "ops_ativar", referencia=aut["referencia"], funcoes=["01.01", "01.02"],
    )
    assert ligado["ambiente"] == "operacao"
    for meta in ligado["manifesto"]["skills"]:
        await dados(ana, "ops_ler_skill", id=meta["id"])
    await dados(
        ana, "ops_confirmar_atribuicoes",
        manifesto_hash=ligado["manifesto"]["hash"],
        resumo="Escopo multi-inbox confirmado.",
    )


def test_listener_sem_scoped_nao_ingere(tmp_path: Path):
    digests, cred = _operador(tmp_path)
    pat = _pat(tmp_path)
    eventos = [{
        "message_id": MSG_INBOX2, "conversation_id": CONV_INBOX2,
        "inbox_id": 2, "estado": "pendente", "handoff": None,
        "recebido_em": "2026-11-24T12:00:00Z",
    }]
    listener, chatwoot, _, _, _ = _servidores(eventos, scoped=False)
    estado = _estado(tmp_path)
    try:
        cfg = tmp_path / "canal.json"
        _gravar(cfg, {"canais": [
            _canal("1", pat, chatwoot.server_port, listener.server_port),
            _canal("2", pat, chatwoot.server_port, listener.server_port),
        ]})
        cfg.write_text(json.dumps({"canais": [
            {**_canal("1", pat, chatwoot.server_port, listener.server_port),
             "intervalo_sync_segundos": 0.5},
            {**_canal("2", pat, chatwoot.server_port, listener.server_port),
             "intervalo_sync_segundos": 0.5},
        ]}))
        cfg.chmod(0o600)

        def partida(pasta: Path):
            return _argv_servir(pasta, estado, digests, cfg)

        with laboratorio("ana", comando_host=partida) as (pasta, admin):
            aut = admin(
                "--credencial-operador", str(cred),
                "autorizar", "--agente", "ana", "--funcoes", "01.01,01.02",
            )

            async def caso():
                async with cliente(
                    "tuttibom-ops-mcp", "--laboratorio", str(pasta), "--cliente", "ana",
                ) as (ana, _):
                    await _ativar(ana, aut)
                    pend = await dados(
                        ana, "ops_atendimento_listar_pendencias", inbox_id="2",
                    )
                    assert pend["pendencias"] == []

            anyio.run(caso)
        assert _estados_fila(estado / "inbox-2" / "fila.sqlite") == {}
    finally:
        _parar(listener, chatwoot)


def test_inbox2_atravessa_backlog_e_reconcilia_so_a_propria_pilha(tmp_path: Path):
    digests, cred = _operador(tmp_path)
    pat = _pat(tmp_path)
    eventos = [
        {
            "message_id": n, "conversation_id": 11, "inbox_id": 1,
            "estado": "pendente", "handoff": None,
            "recebido_em": "2026-11-24T12:00:00Z",
        }
        for n in range(1, BACKLOG + 1)
    ]
    eventos.append({
        "message_id": MSG_INBOX2, "conversation_id": CONV_INBOX2,
        "inbox_id": 2, "estado": "pendente", "handoff": None,
        "recebido_em": "2026-11-24T12:00:01Z",
    })
    listener, chatwoot, consultas, acks, envios = _servidores(eventos, scoped=True)
    estado = _estado(tmp_path)
    try:
        cfg = tmp_path / "canal.json"
        _gravar(cfg, {"canais": [
            {**_canal("1", pat, chatwoot.server_port, listener.server_port),
             "intervalo_sync_segundos": 0.5},
            {**_canal("2", pat, chatwoot.server_port, listener.server_port),
             "intervalo_sync_segundos": 0.5},
        ]})

        def partida(pasta: Path):
            return _argv_servir(pasta, estado, digests, cfg)

        with laboratorio("ana", comando_host=partida) as (pasta, admin):
            auth = ("--credencial-operador", str(cred))
            aut = admin(*auth, "autorizar", "--agente", "ana", "--funcoes", "01.01,01.02")
            fila1 = estado / "inbox-1" / "fila.sqlite"
            fila2 = estado / "inbox-2" / "fila.sqlite"
            inodes = (fila1.stat().st_ino, fila2.stat().st_ino)

            async def caso():
                async with cliente(
                    "tuttibom-ops-mcp", "--laboratorio", str(pasta), "--cliente", "ana",
                ) as (ana, _):
                    await _ativar(ana, aut)
                    inbox2 = await dados(
                        ana, "ops_atendimento_listar_pendencias",
                        inbox_id="2", limite=100,
                    )
                    assert [item["message_id"] for item in inbox2["pendencias"]] == [
                        str(MSG_INBOX2),
                    ]
                    assert inbox2["pendencias"][0]["conversation_id"] == str(CONV_INBOX2)
                    assert inbox2["pendencias"][0]["inbox_id"] == "2"
                    assert "contato_ref" not in json.dumps(inbox2)
                    inbox1 = await dados(
                        ana, "ops_atendimento_listar_pendencias",
                        inbox_id="1", limite=100,
                    )
                    assert [item["message_id"] for item in inbox1["pendencias"]] == [
                        str(n) for n in range(1, BACKLOG + 1)
                    ]
                    assert _estados_fila(fila1) == {"pendente": BACKLOG}
                    assert _estados_fila(fila2) == {"pendente": 1}
                    assert acks == []

                    await dados(
                        ana, "ops_atendimento_ler_conversa", "inbox_obrigatorio",
                        conversa_ref=str(CONV_INBOX2),
                    )
                    leitura = await ana.call_tool(
                        "ops_atendimento_ler_conversa",
                        {"conversa_ref": str(CONV_INBOX2), "inbox_id": "2"},
                    )
                    assert not leitura.isError
                    assert leitura.structuredContent["mensagens"][0]["texto"] == TEXTO_ENTRADA
                    assert leitura.structuredContent["inbox_id"] == "2"
                    await dados(
                        ana, "ops_atendimento_preparar_resposta", "inbox_obrigatorio",
                        conversa_ref=str(CONV_INBOX2), texto=TEXTO_RESPOSTA,
                        idempotency_key="op-inbox2-1", message_ids=[str(MSG_INBOX2)],
                    )
                    prep = await dados(
                        ana, "ops_atendimento_preparar_resposta",
                        conversa_ref=str(CONV_INBOX2), inbox_id="2",
                        texto=TEXTO_RESPOSTA, idempotency_key="op-inbox2-1",
                        message_ids=[str(MSG_INBOX2)],
                    )
                    assert acks == []
                    assert _acks_locais(fila1) == 0
                    assert _acks_locais(fila2) == 0

                    sem_inbox = {
                        "conversa_ref": str(CONV_INBOX2),
                        "rascunho_ref": prep["rascunho_ref"],
                        "texto": TEXTO_RESPOSTA,
                    }
                    assert admin(*auth, "aprovar-resposta", entrada=sem_inbox, rc=1)["codigo"] == (
                        "inbox_obrigatorio"
                    )
                    outra = {**sem_inbox, "inbox_id": "1"}
                    assert admin(*auth, "aprovar-resposta", entrada=outra, rc=1)["codigo"] == (
                        "rascunho_ausente"
                    )
                    flag = subprocess.run(
                        [str(SCRIPTS / "tuttibom-ops-admin"), "--laboratorio", str(pasta),
                         *auth, "aprovar-resposta", "--inbox-id", "2"],
                        env=ENV, capture_output=True, text=True, timeout=8,
                    )
                    assert flag.returncode == 2
                    aprov = admin(*auth, "aprovar-resposta", entrada={
                        **sem_inbox, "inbox_id": "2",
                    })
                    assert aprov["inbox_id"] == "2"
                    envio = await dados(
                        ana, "ops_atendimento_responder",
                        rascunho_ref=prep["rascunho_ref"],
                        aprovacao_ref=aprov["aprovacao_ref"],
                    )
                    assert envio["enviado"] is True
                    assert envio["envio_ref"] == "msg-910"
                    assert envio["acked"] == [str(MSG_INBOX2)]
                    assert envio["inbox_id"] == "2"

            anyio.run(caso)
            assert acks
            assert all(
                item["inbox_id"] == 2 and item["message_ids"] == [MSG_INBOX2]
                for item in acks
            )
            assert any(MSG_INBOX2 in item["accepted"] for item in acks)
            assert any(
                item["inbox_id"] == 2 and MSG_INBOX2 in item["ids"]
                and item["after_message_id"] == 0 and item["limit"] == 50
                for item in consultas
            )
            assert _estados_fila(fila1) == {"pendente": BACKLOG}
            assert _estados_fila(fila2) == {"entregue": 1}
            assert _acks_locais(fila1) == 0
            assert _acks_locais(fila2) == 0
            assert len(envios) == 1
            assert TEXTO_RESPOSTA.encode() in envios[0]["corpo"]

            antes = len(acks)
            assert admin(*auth, "reconciliar-acks", rc=1)["codigo"] == "inbox_obrigatorio"
            pilha1 = admin(*auth, "reconciliar-acks", "--inbox-id", "1")
            pilha2 = admin(*auth, "reconciliar-acks", "--inbox-id", "2")
            assert pilha1["inbox_id"] == "1"
            assert pilha2["inbox_id"] == "2"
            assert pilha1["resultados"] == []
            assert pilha2["resultados"] == []
            assert len(acks) == antes
            assert all(item["inbox_id"] == 2 for item in acks)
            assert fila1.stat().st_ino == inodes[0]
            assert fila2.stat().st_ino == inodes[1]
        assert fila1.stat().st_ino == inodes[0]
        assert (estado / "inbox-2" / "entregas.sqlite").is_file()
    finally:
        _parar(listener, chatwoot)
