#!/home/pc/Workspace/tuttibom-ops/prototype-vision/.venv/bin/python
"""fb_trocar_capa — troca a foto de capa da Página oficial da loja.

Página: https://www.facebook.com/profile.php?id=100089750066330
(id canônico 100089750066330 = id Zernio 143473822920252, D-008).
Não é o perfil pessoal tuttibom10 ("TuttiBom Novidade").

Nome visível: "TuttiBom" depois que o Facebook aprovar a renomeação
(D-005, solicitada 2026-11-17 ~10:16). Enquanto a análise não sair,
o título continua "TutiBom" — os dois são aceitos. "TuttiBom Novidade"
aborta: é o perfil pessoal.

Roda SÓ numa janela combinada: o fb_agent.py parado e o profile-fb livre.
Reaproveita o camofox_driver.launch() do prototype-vision da main
(MESMO profile-fb, MESMA impressão digital fixa, humanize=True, Xfce :0),
sem editar o driver nem o fb_agent.

Fluxo (D-004: navegação humana, pausas aleatórias, print pelo Jev):
  1. Pré-checagem: lock do profile-fb, .parentlock, processos fb_agent /
     Camoufox com o perfil, imagem existente. Qualquer sinal de uso -> aborta
     (não mata nada).
  2. Abre a Página, checa checkpoint/login/2FA/alerta de bot e confirma o
     nome "TuttiBom" (ou "TutiBom", enquanto a renomeação não aprova).
  3. Editar foto da capa -> Enviar foto -> set_files com o PNG -> espera o
     preview -> Salvar alterações.
  4. Print final em /tmp/fb-capa-aplicada.png, fecha o navegador e confere
     que o lock do perfil foi liberado.

Uso:
  .venv/bin/python scripts/fb_trocar_capa.py --dry-run   # só pré-checagem
  .venv/bin/python scripts/fb_trocar_capa.py             # aplica

Saída: 0 ok | 2 pré-checagem bloqueou | 3 Página/nome não confirmados |
       4 alerta (checkpoint/login/2FA/bot) | 5 falha no fluxo
Nunca registra cookies, tokens ou query string de URL.
"""
import argparse
import errno
import fcntl
import hashlib
import os
import re
import struct
import sys
import time
from pathlib import Path

PROTO = Path("/home/pc/Workspace/tuttibom-ops/prototype-vision")
PROFILE = PROTO / "profile-fb"
WORKTREE = Path(__file__).resolve().parent.parent
IMAGEM_PADRAO = WORKTREE / "criativos" / "capa-2026-11-16" / "capa-A3b.png"
# Página oficial (D-008). O id 143473822920252 é o mesmo número no Zernio.
URL_PAGINA = "https://www.facebook.com/profile.php?id=100089750066330"
PAGE_ID = "100089750066330"
NOME_APROVADO = "TuttiBom"
NOME_ENQUANTO_ANALISA = "TutiBom"
NOMES_ACEITOS = (NOME_APROVADO, NOME_ENQUANTO_ANALISA)
PERFIL_PESSOAL = "TuttiBom Novidade"
SHOT_FINAL = Path("/tmp/fb-capa-aplicada.png")
SHOT_PREVIEW = Path("/tmp/fb-capa-preview.png")
SHOT_ALERTA = Path("/tmp/fb-capa-alerta.png")
SHOT_FALHA = Path("/tmp/fb-capa-falha.png")
TRAVA_SCRIPT = Path("/tmp/fb-trocar-capa.lock")

ALERTA_URL = re.compile(r"/(checkpoint|login|two_step_verification|two_factor|recover|captcha)", re.I)
ALERTA_TEXTO = re.compile(
    r"(confirme (sua|que é você)|confirme sua identidade|verifica(ção|r) (de|em) duas etapas|"
    r"autenticação de dois fatores|código de (segurança|login|verificação)|insira o código|"
    r"atividade (incomum|suspeita)|comportamento automatizado|suspeitamos|"
    r"sua conta (foi|está) (bloqueada|suspensa|temporariamente)|faça login para continuar|"
    r"entrar no facebook|we suspect automated|unusual activity|confirm your identity|"
    r"two-factor|security check|captcha)",
    re.I,
)


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def url_limpa(url: str) -> str:
    return url.split("?", 1)[0].split("#", 1)[0]


# ---------------------------------------------------------------- pré-checagem
def _pid_vivo(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def checar_lock_symlink() -> list:
    lock = PROFILE / "lock"
    if not os.path.lexists(lock):
        return []
    alvo = os.readlink(lock) if lock.is_symlink() else "?"
    m = re.search(r"\+(\d+)$", alvo)
    pid = int(m.group(1)) if m else None
    if pid and _pid_vivo(pid):
        return [f"lock do profile-fb ATIVO: {lock} -> {alvo} (pid {pid} vivo)"]
    return [f"lock do profile-fb presente ({alvo}); pid não está vivo (lock órfão) — "
            f"confirme manualmente que nada usa o perfil antes de rodar"]


def checar_parentlock() -> list:
    """F_GETLK: só pergunta quem segura o .parentlock, sem travar nada."""
    pl = PROFILE / ".parentlock"
    if not pl.exists():
        return []
    try:
        fd = os.open(pl, os.O_RDONLY)
    except OSError as e:
        return [f".parentlock ilegível ({e.strerror})"]
    try:
        # struct flock (Linux x86_64/aarch64): short, short, off_t, off_t, pid_t + padding
        req = struct.pack("hhqqi4x", fcntl.F_WRLCK, os.SEEK_SET, 0, 0, 0)
        res = fcntl.fcntl(fd, fcntl.F_GETLK, req)
        l_type, _, _, _, l_pid = struct.unpack("hhqqi4x", res)
        if l_type != fcntl.F_UNLCK:
            return [f".parentlock do profile-fb travado pelo pid {l_pid}"]
    except OSError as e:
        if e.errno not in (errno.EINVAL,):
            return [f"não consegui consultar o .parentlock ({e.strerror})"]
    finally:
        os.close(fd)
    return []


def checar_processos() -> list:
    achados = []
    eu = os.getpid()
    perfil = str(PROFILE)
    for d in Path("/proc").iterdir():
        if not d.name.isdigit() or int(d.name) == eu:
            continue
        try:
            argv = [a.decode(errors="replace") for a in (d / "cmdline").read_bytes().split(b"\0") if a]
        except OSError:
            continue
        if not argv:
            continue
        nomes = {os.path.basename(a) for a in argv}
        if "fb_agent.py" in nomes:
            achados.append(f"processo fb_agent ativo: pid {d.name}")
        elif "-profile" in argv and perfil in argv and "camoufox" in argv[0].lower():
            achados.append(f"Camoufox usando o profile-fb: pid {d.name}")
        elif ({"fb_trocar_capa.py", "fb_trocar_foto.py"} & nomes) and "python" in os.path.basename(argv[0]):
            achados.append(f"outra execução de troca no Facebook: pid {d.name} ({' '.join(nomes & {'fb_trocar_capa.py', 'fb_trocar_foto.py'})})")
    return achados


def checar_imagem(imagem: Path) -> tuple:
    if not imagem.is_file():
        return [f"imagem não encontrada: {imagem}"], ""
    dado = imagem.read_bytes()
    if dado[:8] != b"\x89PNG\r\n\x1a\n":
        return [f"imagem não é PNG: {imagem}"], ""
    w, h = struct.unpack(">II", dado[16:24])
    info = f"{imagem} ({w}x{h}, {len(dado)} bytes, sha256 {hashlib.sha256(dado).hexdigest()[:16]})"
    return [], info


def precheck(imagem: Path) -> tuple:
    bloqueios = []
    if not (PROFILE / "fingerprint.json").is_file():
        bloqueios.append(f"impressão digital fixa ausente em {PROFILE}/fingerprint.json")
    bloqueios += checar_lock_symlink()
    bloqueios += checar_parentlock()
    bloqueios += checar_processos()
    if TRAVA_SCRIPT.exists():
        bloqueios.append(f"trava do próprio script presente: {TRAVA_SCRIPT}")
    b_img, info = checar_imagem(imagem)
    bloqueios += b_img
    return bloqueios, info


# ---------------------------------------------------------------- navegação
class Abortar(Exception):
    def __init__(self, codigo: int, motivo: str):
        super().__init__(motivo)
        self.codigo = codigo
        self.motivo = motivo


def confirmar_nome(page) -> str:
    """Confere o h1 da Página. Aceita TuttiBom ou TutiBom. Recusa o perfil pessoal."""
    try:
        titulos = page.get_by_role("heading").all_inner_texts()
    except Exception:  # noqa: BLE001
        titulos = []
    limpos = [" ".join(t.split()) for t in titulos if t and t.strip()]
    if any(PERFIL_PESSOAL in t for t in limpos):
        page.screenshot(path=str(SHOT_FALHA), type="png")
        raise Abortar(
            3,
            f"caiu no perfil pessoal '{PERFIL_PESSOAL}' — a capa é da Página "
            f"{PAGE_ID}. Print em {SHOT_FALHA}",
        )
    for esperado in NOMES_ACEITOS:
        if esperado in limpos:
            return esperado
        alvo = page.get_by_role("heading", name=esperado, exact=True)
        try:
            if alvo.count() and alvo.first.is_visible():
                return esperado
        except Exception:  # noqa: BLE001
            continue
    page.screenshot(path=str(SHOT_FALHA), type="png")
    vistos = ", ".join(repr(t) for t in limpos[:8]) or "(nenhum heading)"
    raise Abortar(
        3,
        f"nome da Página não confirmado (esperado '{NOME_APROVADO}' ou, "
        f"enquanto o Facebook analisa, '{NOME_ENQUANTO_ANALISA}'). "
        f"Headings: {vistos}. Print em {SHOT_FALHA}",
    )


def checar_alerta(page, etapa: str) -> None:
    url = url_limpa(page.url)
    motivo = None
    if ALERTA_URL.search(url):
        motivo = f"URL de alerta ({url})"
    else:
        try:
            texto = page.inner_text("body", timeout=5000)[:20000]
        except Exception:  # noqa: BLE001 - sem texto não é alerta
            texto = ""
        m = ALERTA_TEXTO.search(texto)
        if m:
            motivo = f"texto de alerta: '{m.group(0)}'"
        else:
            try:
                if page.locator("input[name='pass']").first.is_visible(timeout=1000):
                    motivo = "formulário de senha visível (sessão caiu)"
            except Exception:  # noqa: BLE001
                pass
    if motivo:
        try:
            page.screenshot(path=str(SHOT_ALERTA), type="png")
        except Exception:  # noqa: BLE001
            pass
        raise Abortar(4, f"[{etapa}] {motivo} — print em {SHOT_ALERTA}. Pausar e avisar o José.")


def clicar(page, alvo_jev: str, locator, etapa: str, human_pause, locate, prep) -> str:
    """Clique humano: tenta a coordenada do Jev (padrão D-004); se o Jev não
    achar com segurança, usa o elemento do DOM (o Camoufox humaniza o mouse
    nos dois casos). Devolve como clicou."""
    human_pause()
    try:
        png = page.screenshot(type="png")
        _, w, h = prep(png)
        loc, rec = locate(png, alvo_jev, w, h)
    except Exception as e:  # noqa: BLE001 - Jev fora não pode travar o fluxo
        loc, rec = None, {"result": f"erro Jev: {type(e).__name__}"}
    if loc:
        el = locator.first
        try:
            box = el.bounding_box(timeout=3000) if el.count() else None
        except Exception:  # noqa: BLE001
            box = None
        # Só confia no Jev se o ponto cair no elemento do DOM (ou se não houver DOM para conferir).
        if box is None or (box["x"] <= loc["x"] <= box["x"] + box["width"]
                           and box["y"] <= loc["y"] <= box["y"] + box["height"]):
            page.mouse.click(loc["x"], loc["y"])
            log(f"{etapa}: clique Jev em ({loc['x']},{loc['y']}) conf {loc['confidence']:.2f}")
            return "jev"
        log(f"{etapa}: ponto do Jev fora do elemento do DOM; usando o DOM")
    else:
        log(f"{etapa}: Jev sem localização segura ({rec.get('result')}); usando o DOM")
    locator.first.click(timeout=15000)
    log(f"{etapa}: clique pelo DOM")
    return "dom"


def aplicar(imagem: Path) -> int:
    sys.path.insert(0, str(PROTO))
    import camofox_driver  # noqa: E402
    from camofox_driver import human_pause, launch, reading_pause  # noqa: E402
    from jev_navigate import locate, prep  # noqa: E402

    if Path(camofox_driver.PROFILE).resolve() != PROFILE.resolve():
        log(f"ABORTADO: o driver aponta para {camofox_driver.PROFILE}, não para {PROFILE}")
        return 2

    log("abrindo Camoufox (profile-fb, impressão digital fixa, humanize, Xfce :0)...")
    with launch() as ctx:
        page = ctx.new_page()
        try:
            log(f"goto {URL_PAGINA}")
            page.goto(URL_PAGINA, wait_until="load", timeout=60000)
            reading_pause()
            log(f"aberto: título '{page.title()}' | {url_limpa(page.url)}")
            checar_alerta(page, "abertura")

            visto = confirmar_nome(page)
            if visto == NOME_ENQUANTO_ANALISA:
                log(f"nome '{visto}' visível — renomeação ainda em análise; "
                    f"o esperado depois da aprovação é '{NOME_APROVADO}'")
            else:
                log(f"nome '{visto}' visível")

            page.mouse.wheel(0, -600)  # garante o topo da Página (capa à vista)
            reading_pause(2.0, 4.0)

            editar = page.get_by_role("button", name=re.compile(r"Editar foto d[ae] capa", re.I))
            if not editar.count():
                editar = page.get_by_text(re.compile(r"Editar foto d[ae] capa", re.I))
            if not editar.count():
                page.screenshot(path=str(SHOT_FALHA), type="png")
                raise Abortar(5, f"botão 'Editar foto da capa' não encontrado (sessão sem admin?) — {SHOT_FALHA}")
            clicar(page, "botão Editar foto da capa", editar, "editar capa", human_pause, locate, prep)
            human_pause(1.5, 3.0)
            checar_alerta(page, "menu da capa")

            enviar = page.get_by_role("menuitem", name=re.compile(r"(Enviar|Carregar) foto", re.I))
            if not enviar.count():
                enviar = page.get_by_text(re.compile(r"^(Enviar|Carregar) foto", re.I))
            if not enviar.count():
                page.screenshot(path=str(SHOT_FALHA), type="png")
                raise Abortar(5, f"opção 'Enviar foto' não apareceu no menu — {SHOT_FALHA}")
            try:
                with page.expect_file_chooser(timeout=15000) as fc:
                    clicar(page, "opção Enviar foto no menu", enviar, "enviar foto", human_pause, locate, prep)
                human_pause(1.0, 2.5)  # tempo de quem procura o arquivo
                fc.value.set_files(str(imagem))
                log("arquivo entregue pelo seletor de arquivos")
            except Exception as e:  # noqa: BLE001 - sem seletor: usa o input do próprio menu
                log(f"seletor de arquivos não abriu ({type(e).__name__}); usando input[type=file]")
                entrada = page.locator("input[type='file'][accept*='image']")
                if not entrada.count():
                    entrada = page.locator("input[type='file']")
                if not entrada.count():
                    page.screenshot(path=str(SHOT_FALHA), type="png")
                    raise Abortar(5, f"nenhum campo de arquivo encontrado — {SHOT_FALHA}")
                entrada.first.set_input_files(str(imagem))
                log("arquivo entregue pelo input[type=file]")

            salvar = page.get_by_role("button", name=re.compile(r"Salvar altera", re.I))
            try:
                salvar.first.wait_for(state="visible", timeout=90000)
            except Exception:  # noqa: BLE001
                checar_alerta(page, "preview")
                page.screenshot(path=str(SHOT_FALHA), type="png")
                raise Abortar(5, f"preview sem 'Salvar alterações' em 90 s — {SHOT_FALHA}")
            reading_pause(3.0, 6.0)  # olhar o preview como uma pessoa
            page.screenshot(path=str(SHOT_PREVIEW), type="png")
            log(f"preview carregado — print em {SHOT_PREVIEW}")
            checar_alerta(page, "preview")

            clicar(page, "botão Salvar alterações", salvar, "salvar", human_pause, locate, prep)
            try:
                salvar.first.wait_for(state="hidden", timeout=90000)
            except Exception:  # noqa: BLE001
                checar_alerta(page, "salvando")
                page.screenshot(path=str(SHOT_FALHA), type="png")
                raise Abortar(5, f"'Salvar alterações' não sumiu em 90 s — {SHOT_FALHA}")
            reading_pause()
            checar_alerta(page, "depois de salvar")
            page.screenshot(path=str(SHOT_FINAL), type="png")
            log(f"capa salva — print final em {SHOT_FINAL} | {url_limpa(page.url)}")
            human_pause()
        except Abortar:
            raise
        except Exception as e:  # noqa: BLE001 - qualquer erro vira aborto com print
            try:
                page.screenshot(path=str(SHOT_FALHA), type="png")
            except Exception:  # noqa: BLE001
                pass
            raise Abortar(5, f"erro inesperado: {type(e).__name__}: {str(e)[:200]} — {SHOT_FALHA}")
    return 0


def esperar_lock_liberado(segundos: int = 15) -> bool:
    fim = time.time() + segundos
    while time.time() < fim:
        if not os.path.lexists(PROFILE / "lock") and not checar_parentlock():
            return True
        time.sleep(1)
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--dry-run", action="store_true", help="só a pré-checagem; não abre o navegador")
    ap.add_argument("--imagem", type=Path, default=IMAGEM_PADRAO)
    args = ap.parse_args()
    imagem = args.imagem.resolve()

    bloqueios, info = precheck(imagem)
    log(f"perfil: {PROFILE}")
    log(f"Página: {URL_PAGINA} (id {PAGE_ID}; nome esperado '{NOME_APROVADO}', "
        f"aceito enquanto analisa: '{NOME_ENQUANTO_ANALISA}')")
    if info:
        log(f"imagem: {info}")
    if bloqueios:
        log("ABORTADO na pré-checagem (nada foi aberto nem encerrado):")
        for b in bloqueios:
            log(f"  - {b}")
        log("Aguardar a janela combinada: o dono do fb_agent para o agente e o lock some.")
        return 2
    log("pré-checagem OK: profile-fb livre, nenhum fb_agent/Camoufox no perfil.")

    if args.dry_run:
        log("DRY-RUN — o que faria:")
        for passo in (
            "abrir o Camoufox com o profile-fb (impressão digital fixa, humanize, Xfce :0)",
            f"abrir {URL_PAGINA} e abortar se houver checkpoint/login/2FA/alerta de bot",
            f"confirmar o nome '{NOME_APROVADO}' visível "
            f"(ou '{NOME_ENQUANTO_ANALISA}' enquanto a renomeação não aprova; "
            f"abortar se aparecer '{PERFIL_PESSOAL}')",
            "Editar foto da capa > Enviar foto > set_files com a imagem",
            f"esperar o preview (print em {SHOT_PREVIEW}) > Salvar alterações",
            f"print final em {SHOT_FINAL}, fechar o navegador e conferir o lock liberado",
        ):
            log(f"  - {passo}")
        return 0

    TRAVA_SCRIPT.write_text(str(os.getpid()))
    codigo = 0
    try:
        codigo = aplicar(imagem)
    except Abortar as a:
        log(f"ABORTADO: {a.motivo}")
        codigo = a.codigo
    finally:
        TRAVA_SCRIPT.unlink(missing_ok=True)
        livre = esperar_lock_liberado()
        log("navegador fechado; lock do profile-fb liberado" if livre
            else "ATENÇÃO: lock do profile-fb ainda presente após fechar — conferir antes de religar o fb_agent")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
