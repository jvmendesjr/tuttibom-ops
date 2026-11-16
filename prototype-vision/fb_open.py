#!/home/pc/Workspace/tuttibom-ops/prototype-vision/.venv/bin/python
"""fb_open — abre o facebook.com no Camoufox e DEIXA A JANELA ABERTA.

Para o usuário assistir ao vivo pelo noVNC. Sem login, nada digitado,
nada enviado. Para fechar: tocar em /tmp/fb-live.stop (o processo sai
sozinho em até 60 s e fecha o navegador).
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from camofox_driver import launch, reading_pause  # noqa: E402

URL = "https://www.facebook.com"
SHOT = "/tmp/fb-login-live.png"
STOP = Path("/tmp/fb-live.stop")


def main():
    STOP.unlink(missing_ok=True)
    print("launching Camoufox (Xfce :0, perfil persistente, humanize)...", flush=True)
    with launch() as ctx:
        page = ctx.new_page()
        print("goto", URL, flush=True)
        page.goto(URL, wait_until="load", timeout=60000)
        reading_pause()
        print("title:", page.title(), "| url:", page.url, flush=True)
        png = page.screenshot(path=SHOT, type="png")
        print(f"screenshot {len(png)} bytes -> {SHOT}", flush=True)
        print("JANELA ABERTA — aguardando. Para fechar: touch /tmp/fb-live.stop", flush=True)
        while not STOP.exists():
            time.sleep(30)
        print("stop file encontrado — fechando navegador.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
