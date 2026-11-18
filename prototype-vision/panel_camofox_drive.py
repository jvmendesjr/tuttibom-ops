#!/home/pc/Workspace/tuttibom-ops/prototype-vision/.venv/bin/python
"""panel_camofox_drive — Camofox + Jev em consórcio para o painel Deskcomm.

Trinômio agente+camofox+jev (D-004): o Muse navega no painel com o motor
Camoufox (perfil SEPARADO profile-panel/, sessão do usuário persistida) e o
Jev tipa os prints e localiza os alvos. A janela fica no Xfce :0 real para o
usuário ver (e colar segredos) pelo noVNC — o resto roda por fila de tarefas.

Fila de tarefas por arquivo (operador é o Muse, via ssh):
  - escrever a tarefa em /tmp/panel-camofox-job.json:
    {"id": "p1", "action": "goto"|"locate"|"click"|"type"|"scroll"|"shot",
     "target": "descrição do alvo para o Jev", "url": "https://...",
     "text": "texto a digitar (só type)", "dy": 700 (só scroll)}
  - o agente lê, executa e escreve o resultado em /tmp/panel-camofox-result.json
    + print em /tmp/panel-camofox-shot.png
  - para parar: touch /tmp/panel-camofox.stop (fecha o navegador de forma limpa)

Regras: só navegação e leitura pelo agente; segredo (chave de API) o usuário
cola na tela — o agente NUNCA digita segredo. Nada é enviado sem aprovação.
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
JOB = Path("/tmp/panel-camofox-job.json")
JOB_BUSY = Path("/tmp/panel-camofox-job.processing")
RESULT = Path("/tmp/panel-camofox-result.json")
SHOT = Path("/tmp/panel-camofox-shot.png")
STOP = Path("/tmp/panel-camofox.stop")
HOME_URL = "https://deskcomm.petemcasa.com/app/settings/atendimento"


def log(msg: str) -> None:
    print(msg, flush=True)


def get_fingerprint():
    PROFILE.mkdir(parents=True, exist_ok=True)
    if FP_FILE.exists():
        return json.loads(FP_FILE.read_text())
    fp = generate_fingerprint(window=VIEWPORT, os="linux")
    FP_FILE.write_text(json.dumps(fp))
    return fp


def launch_panel():
    """Abre o Camofox com o perfil-panel. Virtual (Xvfb) SEMPRE primeiro:
    o painel nunca abre no :0 (display real do noVNC); :0 so entra como
    reserva se o virtual falhar."""
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
            log(f"Camoufox (painel) aberto: display={display}")
            return ctx
        except Exception as e:  # noqa: BLE001 - tenta a próxima combinação
            last = e
            log(f"display={display} falhou: {e}")
    raise last


def shot(page, path: str = str(SHOT)) -> int:
    png = page.screenshot(path=path, type="png")
    return len(png)


def ver_pagina(page) -> dict:
    return {"title": page.title(), "url": page.url}


def do_locate(page, target: str) -> dict:
    png = page.screenshot(type="png")
    _, w, h = prep(png)
    loc, rec = locate(png, target, w, h)
    return {"target": target, "loc": loc, "noul": rec.get("noul"),
            "count": rec.get("count"), "confidence": rec.get("confidence"),
            "zoomed": rec.get("zoomed", False), "tokens": rec.get("input_tokens"),
            "latency_ms": rec.get("latency_ms"), "result": rec.get("result", "found")}


def do_click(page, target: str) -> dict:
    antes = ver_pagina(page)
    found = do_locate(page, target)
    if not found["loc"]:
        return {"ok": False, "action": "click", "found": found, "before": antes}
    time.sleep(1.0)
    page.mouse.click(found["loc"]["x"], found["loc"]["y"])
    time.sleep(2.0)
    shot(page)
    return {"ok": True, "action": "click", "found": found,
            "before": antes, "after": ver_pagina(page), "shot": str(SHOT)}


def do_type(page, target: str, text: str) -> dict:
    """Localiza o campo com o Jev, clica para focar e digita o texto.
    NUNCA usar para segredo — só para valores não sensíveis (ex.: ID da conta)."""
    found = do_locate(page, target)
    if not found["loc"]:
        return {"ok": False, "action": "type", "found": found}
    time.sleep(1.0)
    page.mouse.click(found["loc"]["x"], found["loc"]["y"])
    time.sleep(1.0)
    page.keyboard.press("Control+A")  # substitui o conteudo do campo, nao soma
    page.keyboard.type(text, delay=30)
    time.sleep(1.0)
    shot(page)
    return {"ok": True, "action": "type", "found": found, "shot": str(SHOT)}


def do_job(page, job: dict) -> dict:
    action = job.get("action")
    if action == "goto":
        page.goto(job["url"], wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        shot(page)
        return {"ok": True, "action": "goto", "page": ver_pagina(page), "shot": str(SHOT)}
    if action == "locate":
        return {"ok": True, "action": "locate", "found": do_locate(page, job["target"])}
    if action == "click":
        return do_click(page, job["target"])
    if action == "type":
        return do_type(page, job["target"], job.get("text", ""))
    if action == "scroll":
        page.mouse.wheel(0, job.get("dy", 700))
        time.sleep(1.5)
        shot(page)
        return {"ok": True, "action": "scroll", "dy": job.get("dy", 700), "shot": str(SHOT)}
    if action == "shot":
        n = shot(page)
        return {"ok": True, "action": "shot", "bytes": n, "page": ver_pagina(page), "shot": str(SHOT)}
    return {"ok": False, "action": action, "error": "acao_desconhecida"}


def main() -> int:
    for f in (JOB, JOB_BUSY, STOP):
        f.unlink(missing_ok=True)
    RESULT.unlink(missing_ok=True)
    log("panel_camofox_drive: abrindo Camoufox (perfil-panel, sessão do usuário)...")
    ctx = launch_panel()
    try:
        page = ctx.new_page()
        log(f"goto {HOME_URL}")
        page.goto(HOME_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        shot(page)
        log(f"aberto: {ver_pagina(page)} — aguardando tarefas em {JOB}")
        log("para parar: touch /tmp/panel-camofox.stop")
        while not STOP.exists():
            if JOB.exists():
                try:
                    JOB.rename(JOB_BUSY)
                    job = json.loads(JOB_BUSY.read_text())
                except Exception as e:  # noqa: BLE001 - tarefa inválida não derruba o agente
                    log(f"tarefa inválida: {e}")
                    JOB_BUSY.unlink(missing_ok=True)
                    time.sleep(2)
                    continue
                log(f"tarefa {job.get('id')}: {job.get('action')} {job.get('target', '')[:80]}")
                try:
                    res = do_job(page, job)
                except Exception:  # noqa: BLE001 - erro da tarefa vira resultado, não morte
                    res = {"ok": False, "action": job.get("action"),
                           "error": traceback.format_exc(limit=3)[-500:]}
                res["id"] = job.get("id")
                res["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S-03:00", time.localtime())
                RESULT.write_text(json.dumps(res, ensure_ascii=False, indent=2))
                JOB_BUSY.unlink(missing_ok=True)
                log(f"resultado {job.get('id')}: ok={res.get('ok')}")
            time.sleep(2)
        log("stop encontrado — fechando navegador.")
    finally:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001 - fechar não pode quebrar o teste
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
