#!/home/pc/Workspace/tuttibom-ops/prototype-vision/.venv/bin/python
"""Valida a parte logada do painel no motor Camoufox (trinômio agente+camofox+jev).

- Reabre o Camoufox com o MESMO perfil-panel/ do login do usuário: se a
  sessão persistiu, a tela de Tags abre já logada (prova de persistência).
- display virtual (Xvfb: nada na tela :0 real — segundo plano).
- Localiza com o Jev o botão "Adicionar etiqueta" na tela de Tags.
  Só leitura/navegação — NÃO cria, NÃO altera nenhuma etiqueta.
- Resultado em /tmp/panel-camofox-validate.json; print em /tmp/panel-camofox-tags.png.
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
TAGS_URL = "https://deskcomm.petemcasa.com/app/settings/tags"
RESULT = "/tmp/panel-camofox-validate.json"


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
    res = {"inicio": time.strftime("%Y-%m-%d %H:%M:%S"), "display": "virtual", "passos": {}}
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
        page.goto(TAGS_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        page.screenshot(path="/tmp/panel-camofox-tags.png")
        pagina = {"title": page.title(), "url": page.url}
        res["passos"]["pagina"] = pagina
        log(f"aberto: {pagina}")
        logado = "/login" not in page.url and "/app/settings/tags" in page.url
        res["passos"]["sessao_persistida"] = logado
        log(f"sessão persistida (já logado): {logado}")
        r = jev_locate(page, "o botão verde Adicionar etiqueta no canto superior direito da página de Tags")
        res["passos"]["botao_adicionar"] = r
        log(f"botão Adicionar etiqueta: {r['result']} noul={r['noul']} conf={r['confidence']}")
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
