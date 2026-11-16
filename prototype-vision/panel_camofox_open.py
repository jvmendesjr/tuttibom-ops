#!/home/pc/Workspace/tuttibom-ops/prototype-vision/.venv/bin/python
"""Abre o Camoufox (motor) com o perfil-panel na tela de login do Deskcomm,
para o usuário logar pelo noVNC e semear a sessão do perfil-panel.

- Perfil SEPARADO profile-panel/ (não toca o profile-fb do Facebook, que
  continua rodando no fb_agent com a sessão do TuttiBom Novidade).
- Janela de verdade no Xfce :0 (o usuário vê e loga pelo noVNC).
- Abre direto a tela de Tags; sem sessão, o app redireciona para o login e,
  após o login, volta para a tela de Tags.
- Mantém aberto até existir /tmp/panel-camofox-live.stop (fecha limpo).
- Nada digitado, nada enviado — só abre a página e espera o login.
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from camoufox.fingerprints import generate_fingerprint  # noqa: E402
from camoufox.sync_api import Camoufox  # noqa: E402

BASE = Path(__file__).resolve().parent
PROFILE = BASE / "profile-panel"
FP_FILE = PROFILE / "fingerprint.json"
VIEWPORT = (1280, 800)
TAGS_URL = "https://deskcomm.petemcasa.com/app/settings/tags"
STOP = Path("/tmp/panel-camofox-live.stop")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def get_fingerprint():
    PROFILE.mkdir(parents=True, exist_ok=True)
    if FP_FILE.exists():
        return json.loads(FP_FILE.read_text())
    fp = generate_fingerprint(window=VIEWPORT, os="linux")
    FP_FILE.write_text(json.dumps(fp))
    return fp


def main() -> int:
    STOP.unlink(missing_ok=True)
    os.environ["DISPLAY"] = ":0"
    log("abrindo Camoufox (Xfce :0, perfil-panel)...")
    c = Camoufox(
        headless=False,
        persistent_context=True,
        user_data_dir=str(PROFILE),
        fingerprint=get_fingerprint(),
        humanize=True,
        locale=["pt-BR"],
        geoip=False,
        window=VIEWPORT,
        i_know_what_im_doing=True,
    )
    ctx = c.__enter__()
    try:
        page = ctx.new_page()
        page.goto(TAGS_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(2)
        page.screenshot(path="/tmp/panel-camofox-live.png")
        log(f"aberto: {page.title()} {page.url} — aguardando login")
        log("para parar: touch /tmp/panel-camofox-live.stop")
        while not STOP.exists():
            time.sleep(5)
        log("stop encontrado — fechando navegador.")
        return 0
    finally:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001 - fechar não pode quebrar o script
            pass


if __name__ == "__main__":
    sys.exit(main())
