#!/home/pc/Workspace/tuttibom-ops/prototype-vision/.venv/bin/python
"""Teste: painel Deskcomm no motor Camoufox (trinômio agente+camofox+jev).

- Perfil SEPARADO profile-panel/ (não toca o profile-fb do Facebook, que
  continua rodando no fb_agent com a sessão do TuttiBom Novidade).
- Impressão digital própria do perfil-panel, gerada uma vez.
- display virtual primeiro (Xvfb gerenciado pelo pacote: nada aparece na
  tela :0 real — segundo plano de verdade, sem interromper o que está na
  tela); cai para real se o virtual falhar.
- Só leitura/navegação na página de LOGIN: localiza com o Jev os campos de
  e-mail/senha e o botão Entrar, clica no campo de e-mail e confirma o foco.
  Nada digitado, nada enviado, nenhum login tentado.
- Resultado em /tmp/panel-camofox-test.json; prints em /tmp/panel-camofox-*.png.
"""
import json
import os
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from camoufox.fingerprints import generate_fingerprint  # noqa: E402
from camoufox.sync_api import Camoufox  # noqa: E402
from jev_navigate import locate, prep  # noqa: E402

BASE = Path(__file__).resolve().parent
PROFILE = BASE / "profile-panel"
FP_FILE = PROFILE / "fingerprint.json"
VIEWPORT = (1280, 800)
LOGIN_URL = "https://deskcomm.petemcasa.com/login"
RESULT = "/tmp/panel-camofox-test.json"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def get_fingerprint():
    PROFILE.mkdir(parents=True, exist_ok=True)
    if FP_FILE.exists():
        return json.loads(FP_FILE.read_text())
    fp = generate_fingerprint(window=VIEWPORT, os="linux")
    FP_FILE.write_text(json.dumps(fp))
    return fp


def jev_locate(page, target: str) -> dict:
    png = page.screenshot(type="png")
    _, w, h = prep(png)
    loc, rec = locate(png, target, w, h)
    return {"target": target, "loc": loc, "noul": rec.get("noul"),
            "count": rec.get("count"), "confidence": rec.get("confidence"),
            "zoomed": rec.get("zoomed", False), "tokens": rec.get("input_tokens"),
            "latency_ms": rec.get("latency_ms"), "result": rec.get("result", "found")}


def main() -> int:
    res = {"inicio": time.strftime("%Y-%m-%d %H:%M:%S"), "display": None, "passos": {}}
    ctx = None
    last = None
    for display in ("virtual", "real"):
        try:
            if display == "real":
                os.environ["DISPLAY"] = ":0"
                headless = False
            else:
                headless = "virtual"
            c = Camoufox(
                headless=headless,
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
            res["display"] = display
            log(f"Camoufox aberto: display={display}")
            break
        except Exception as e:  # noqa: BLE001 - tenta a próxima combinação
            last = e
            log(f"display={display} falhou: {e}")
    if ctx is None:
        res["erro"] = str(last)
        Path(RESULT).write_text(json.dumps(res, ensure_ascii=False, indent=2))
        return 1
    try:
        page = ctx.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(2)
        page.screenshot(path="/tmp/panel-camofox-login.png")
        log(f"aberto: {page.title()} {page.url}")
        for chave, alvo in [
            ("email", "o campo de e-mail na página de login do Deskcomm"),
            ("senha", "o campo de senha na página de login do Deskcomm"),
            ("entrar", "o botão Entrar na página de login do Deskcomm"),
        ]:
            r = jev_locate(page, alvo)
            res["passos"][chave] = r
            log(f"{chave}: {r['result']} noul={r['noul']} conf={r['confidence']}")
        loc = res["passos"]["email"].get("loc")
        if loc:
            page.mouse.move(loc["x"], loc["y"], steps=8)
            time.sleep(0.4)
            page.mouse.click(loc["x"], loc["y"])
            time.sleep(1)
            foco = page.evaluate(
                "() => { const a = document.activeElement; "
                "return a ? (a.tagName + '#' + (a.id || '') + '[name=' + (a.name || '') + ']') : 'nenhum'; }"
            )
            res["passos"]["foco_email"] = {"foco": foco}
            log(f"foco após clique: {foco}")
            page.screenshot(path="/tmp/panel-camofox-foco.png")
        res["fim"] = time.strftime("%Y-%m-%d %H:%M:%S")
        Path(RESULT).write_text(json.dumps(res, ensure_ascii=False, indent=2))
        log(f"resultado em {RESULT}")
        return 0
    except Exception:  # noqa: BLE001 - erro vira resultado, não morte silenciosa
        res["erro"] = traceback.format_exc(limit=5)[-800:]
        Path(RESULT).write_text(json.dumps(res, ensure_ascii=False, indent=2))
        log(f"erro: {res['erro'][-200:]}")
        return 1
    finally:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001 - fechar não pode quebrar o teste
            pass


if __name__ == "__main__":
    sys.exit(main())
