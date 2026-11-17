#!/home/pc/Workspace/tuttibom-ops/prototype-vision/.venv/bin/python
"""fb_trocar_foto — troca a foto de perfil da Página oficial pelo monograma TB.

Página: https://www.facebook.com/profile.php?id=100089750066330
(id canônico 100089750066330 = id Zernio 143473822920252, D-008).
Não é o perfil pessoal tuttibom10.

Arte: monograma TB do Magic Patterns
https://www.magicpatterns.com/c/oa6jym3ubfzkmwqd4lrydc
(artefato com prefixo b4f96dc8). Não regenerar. O PNG ainda não está
no repo; o caminho esperado é criativos/perfil-2026-11-17/monograma-tb.png.
Passos de exportação: criativos/perfil-2026-11-17/PASSOS.md.

Mesmas travas da capa: profile-fb livre, fb_agent parado, sem alerta de
bot. Não mata processo. Não abre o navegador no --dry-run.

Uso:
  .venv/bin/python scripts/fb_trocar_foto.py --dry-run
  .venv/bin/python scripts/fb_trocar_foto.py

Saída: 0 ok | 2 pré-checagem bloqueou | 3 Página/nome não confirmados |
       4 alerta | 5 falha no fluxo
"""
import argparse
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fb_trocar_capa as capa  # noqa: E402

WORKTREE = Path(__file__).resolve().parent.parent
IMAGEM_PADRAO = WORKTREE / "criativos" / "perfil-2026-11-17" / "monograma-tb.png"
SHOT_FINAL = Path("/tmp/fb-foto-aplicada.png")
SHOT_PREVIEW = Path("/tmp/fb-foto-preview.png")
SHOT_ALERTA = Path("/tmp/fb-foto-alerta.png")
SHOT_FALHA = Path("/tmp/fb-foto-falha.png")
TRAVA_SCRIPT = Path("/tmp/fb-trocar-foto.lock")


def log(msg: str) -> None:
    capa.log(msg)


def bloqueios_perfil() -> list:
    achados = []
    if not (capa.PROFILE / "fingerprint.json").is_file():
        achados.append(f"impressão digital fixa ausente em {capa.PROFILE}/fingerprint.json")
    achados += capa.checar_lock_symlink()
    achados += capa.checar_parentlock()
    achados += capa.checar_processos()
    if capa.TRAVA_SCRIPT.exists():
        achados.append(f"trava da troca de capa presente: {capa.TRAVA_SCRIPT}")
    if TRAVA_SCRIPT.exists():
        achados.append(f"trava da troca de foto presente: {TRAVA_SCRIPT}")
    return achados


def aplicar(imagem: Path) -> int:
    alerta_antes, falha_antes = capa.SHOT_ALERTA, capa.SHOT_FALHA
    capa.SHOT_ALERTA = SHOT_ALERTA
    capa.SHOT_FALHA = SHOT_FALHA
    sys.path.insert(0, str(capa.PROTO))
    import camofox_driver  # noqa: E402
    from camofox_driver import human_pause, launch, reading_pause  # noqa: E402
    from jev_navigate import locate, prep  # noqa: E402

    if Path(camofox_driver.PROFILE).resolve() != capa.PROFILE.resolve():
        capa.SHOT_ALERTA = alerta_antes
        capa.SHOT_FALHA = falha_antes
        log(f"ABORTADO: o driver aponta para {camofox_driver.PROFILE}, não para {capa.PROFILE}")
        return 2

    log("abrindo Camoufox (profile-fb, impressão digital fixa, humanize, Xfce :0)...")
    with launch() as ctx:
        page = ctx.new_page()
        try:
            log(f"goto {capa.URL_PAGINA}")
            page.goto(capa.URL_PAGINA, wait_until="load", timeout=60000)
            reading_pause()
            log(f"aberto: título '{page.title()}' | {capa.url_limpa(page.url)}")
            capa.checar_alerta(page, "abertura")
            visto = capa.confirmar_nome(page)
            if visto == capa.NOME_ENQUANTO_ANALISA:
                log(f"nome '{visto}' visível — renomeação ainda em análise; "
                    f"o esperado depois da aprovação é '{capa.NOME_APROVADO}'")
            else:
                log(f"nome '{visto}' visível")

            editar = page.get_by_role("button", name=re.compile(r"Editar foto do perfil|Atualizar foto do perfil", re.I))
            if not editar.count():
                editar = page.get_by_role("button", name=re.compile(r"foto do perfil", re.I))
            if not editar.count():
                page.screenshot(path=str(SHOT_FALHA), type="png")
                raise capa.Abortar(5, f"botão da foto do perfil não encontrado (sessão sem admin?) — {SHOT_FALHA}")
            capa.clicar(page, "botão da foto do perfil", editar, "editar perfil", human_pause, locate, prep)
            human_pause(1.5, 3.0)
            capa.checar_alerta(page, "menu da foto")

            enviar = page.get_by_role("menuitem", name=re.compile(r"(Enviar|Carregar|Escolher) foto", re.I))
            if not enviar.count():
                enviar = page.get_by_text(re.compile(r"(Enviar|Carregar|Escolher) foto", re.I))
            if not enviar.count():
                page.screenshot(path=str(SHOT_FALHA), type="png")
                raise capa.Abortar(5, f"opção de enviar a foto do perfil não apareceu — {SHOT_FALHA}")
            try:
                with page.expect_file_chooser(timeout=15000) as fc:
                    capa.clicar(page, "opção Enviar foto no menu do perfil", enviar, "enviar foto", human_pause, locate, prep)
                human_pause(1.0, 2.5)
                fc.value.set_files(str(imagem))
                log("arquivo entregue pelo seletor de arquivos")
            except Exception as e:  # noqa: BLE001
                log(f"seletor de arquivos não abriu ({type(e).__name__}); usando input[type=file]")
                entrada = page.locator("input[type='file'][accept*='image']")
                if not entrada.count():
                    entrada = page.locator("input[type='file']")
                if not entrada.count():
                    page.screenshot(path=str(SHOT_FALHA), type="png")
                    raise capa.Abortar(5, f"nenhum campo de arquivo encontrado — {SHOT_FALHA}")
                entrada.first.set_input_files(str(imagem))
                log("arquivo entregue pelo input[type=file]")

            salvar = page.get_by_role("button", name=re.compile(r"^Salvar", re.I))
            try:
                salvar.first.wait_for(state="visible", timeout=90000)
            except Exception:  # noqa: BLE001
                capa.checar_alerta(page, "preview")
                page.screenshot(path=str(SHOT_FALHA), type="png")
                raise capa.Abortar(5, f"preview sem botão Salvar em 90 s — {SHOT_FALHA}")
            reading_pause(3.0, 6.0)
            page.screenshot(path=str(SHOT_PREVIEW), type="png")
            log(f"preview carregado — print em {SHOT_PREVIEW}")
            capa.checar_alerta(page, "preview")

            capa.clicar(page, "botão Salvar da foto do perfil", salvar, "salvar", human_pause, locate, prep)
            try:
                salvar.first.wait_for(state="hidden", timeout=90000)
            except Exception:  # noqa: BLE001
                capa.checar_alerta(page, "salvando")
                page.screenshot(path=str(SHOT_FALHA), type="png")
                raise capa.Abortar(5, f"botão Salvar não sumiu em 90 s — {SHOT_FALHA}")
            reading_pause()
            capa.checar_alerta(page, "depois de salvar")
            page.screenshot(path=str(SHOT_FINAL), type="png")
            log(f"foto salva — print final em {SHOT_FINAL} | {capa.url_limpa(page.url)}")
            human_pause()
        except capa.Abortar:
            raise
        except Exception as e:  # noqa: BLE001
            try:
                page.screenshot(path=str(SHOT_FALHA), type="png")
            except Exception:  # noqa: BLE001
                pass
            raise capa.Abortar(5, f"erro inesperado: {type(e).__name__}: {str(e)[:200]} — {SHOT_FALHA}")
        finally:
            capa.SHOT_ALERTA = alerta_antes
            capa.SHOT_FALHA = falha_antes
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--dry-run", action="store_true", help="só a pré-checagem; não abre o navegador")
    ap.add_argument("--imagem", type=Path, default=IMAGEM_PADRAO)
    args = ap.parse_args()
    imagem = args.imagem.resolve()

    log(f"perfil: {capa.PROFILE}")
    log(f"Página: {capa.URL_PAGINA} (id {capa.PAGE_ID})")
    perfil = bloqueios_perfil()
    img_bloqueios, info = capa.checar_imagem(imagem)
    if info:
        log(f"imagem: {info}")
    if perfil:
        log("ABORTADO na pré-checagem do profile-fb (nada foi aberto nem encerrado):")
        for b in perfil:
            log(f"  - {b}")
        log("Aguardar a janela combinada: o dono do fb_agent para o agente e o lock some.")
        return 2
    if img_bloqueios:
        log("PNG do monograma ainda não está no caminho (nada foi aberto):")
        for b in img_bloqueios:
            log(f"  - {b}")
        log("Exportar do Magic Patterns oa6jym3ubfzkmwqd4lrydc, artefato b4f96dc8, sem regenerar.")
        log("Ver criativos/perfil-2026-11-17/PASSOS.md")
        return 2

    if args.dry_run:
        log("DRY-RUN — o que faria, com o profile-fb livre e o PNG no lugar:")
        for passo in (
            "abrir o Camoufox com o profile-fb (impressão digital fixa, humanize, Xfce :0)",
            f"abrir {capa.URL_PAGINA} e abortar se houver checkpoint/login/2FA/alerta de bot",
            f"confirmar o nome '{capa.NOME_APROVADO}' "
            f"(ou '{capa.NOME_ENQUANTO_ANALISA}' enquanto a renomeação não aprova)",
            "Editar foto do perfil > Enviar foto > set_files com o monograma TB",
            f"esperar o recorte (print em {SHOT_PREVIEW}) > Salvar",
            f"print final em {SHOT_FINAL}, fechar o navegador e conferir o lock liberado",
        ):
            log(f"  - {passo}")
        return 0

    TRAVA_SCRIPT.write_text(str(os.getpid()))
    codigo = 0
    try:
        codigo = aplicar(imagem)
    except capa.Abortar as a:
        log(f"ABORTADO: {a.motivo}")
        codigo = a.codigo
    finally:
        TRAVA_SCRIPT.unlink(missing_ok=True)
        livre = capa.esperar_lock_liberado()
        log("navegador fechado; lock do profile-fb liberado" if livre
            else "ATENÇÃO: lock do profile-fb ainda presente após fechar — conferir antes de religar o fb_agent")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
