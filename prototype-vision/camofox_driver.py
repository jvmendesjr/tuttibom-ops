#!/home/pc/Workspace/tuttibom-ops/prototype-vision/.venv/bin/python
"""camofox_driver — Camoufox original, sem modificar o Camoufox.

- Perfil persistente (user_data_dir): cookies/login sobrevivem entre execuções.
- Impressão digital FIXA (gerada uma vez, salva em profile-fb/fingerprint.json):
  o mesmo "dispositivo" a cada lançamento; sem ela o Facebook veria um
  dispositivo novo toda vez.
- humanize=True: o próprio Camoufox humaniza o movimento do cursor
  (até ~1,5 s para atravessar a janela). Nada inventado por cima.
- headless='virtual': navegador com janela real num Xvfb gerenciado pelo pacote.
- Pausas humanizadas entre ações (1,2–4 s; leitura 5–10 s após carregar).
- Todo print passa pelo Jev (jev_navigate.locate); o clique usa page.mouse
  (humanizado pelo pacote) nas coordenadas do Box.
"""
import json
import random
import time
from pathlib import Path

from camoufox.fingerprints import generate_fingerprint
from camoufox.sync_api import Camoufox

BASE = Path(__file__).resolve().parent
PROFILE = BASE / "profile-fb"
FP_FILE = PROFILE / "fingerprint.json"
VIEWPORT = (1280, 800)


def get_fingerprint():
    """Gera uma vez, reutiliza sempre. Sem isso cada lançamento é um dispositivo novo."""
    PROFILE.mkdir(parents=True, exist_ok=True)
    if FP_FILE.exists():
        return json.loads(FP_FILE.read_text())
    fp = generate_fingerprint(window=VIEWPORT, os="linux")
    FP_FILE.write_text(json.dumps(fp))
    return fp


def human_pause(a=1.2, b=4.0):
    """Pausa entre ações, como quem lê/pensa antes do próximo passo."""
    time.sleep(random.uniform(a, b))


def reading_pause(a=5.0, b=10.0):
    time.sleep(random.uniform(a, b))


class _Launch:
    """Gerenciador de contexto que tenta abrir o Camoufox em ordem:
    (:0 real + geoip) -> (:0 real sem geoip) -> (Xvfb virtual sem geoip).
    O `Camoufox(...)` só guarda opções; o lançamento real acontece no
    `__enter__` — por isso o retry vive aqui, não no construtor."""

    def __init__(self, geoip=True, display="real"):
        self.geoip = geoip
        self.display = display
        self.ctx = None

    def __enter__(self):
        import os

        combos = [(self.geoip, self.display)]
        if self.geoip:
            combos.append((False, self.display))
        if self.display == "real":
            combos.append((False, "virtual"))
        last = None
        for geoip, display in combos:
            if display == "real":
                os.environ["DISPLAY"] = ":0"
                headless = False
            else:
                headless = "virtual"
            try:
                c = Camoufox(
                    headless=headless,
                    persistent_context=True,
                    user_data_dir=str(PROFILE),
                    fingerprint=get_fingerprint(),
                    humanize=True,
                    locale=["pt-BR"],
                    geoip=geoip,
                    window=VIEWPORT,
                    i_know_what_im_doing=True,
                )
                self.ctx = c.__enter__()
                print(f"Camoufox aberto: display={display} geoip={geoip}", flush=True)
                return self.ctx
            except Exception as e:  # noqa: BLE001 - tenta a próxima combinação
                last = e
                print(f"tentativa display={display} geoip={geoip} falhou: {e}", flush=True)
        raise last

    def __exit__(self, *exc):
        if self.ctx is not None:
            try:
                self.ctx.close()
            except Exception:  # noqa: BLE001 - fechar não pode quebrar o teste
                pass
        return False


def launch(geoip=True, display="real"):
    """Devolve o contexto persistente (ou o browser). Ambos têm new_page().

    display="real": navegador com janela de verdade no Xfce :0 do PC — o mais
    próximo de um humano (compositor, GPU e gerenciador de janelas reais);
    é o modo que o usuário vê pela tela/VNC. display="virtual": Xvfb gerenciado
    pelo pacote (reserva, sem tela física).
    """
    return _Launch(geoip=geoip, display=display)
