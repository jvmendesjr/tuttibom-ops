#!/home/pc/Workspace/tuttibom-ops/prototype-vision/.venv/bin/python
"""panel_drive — navegação do painel Deskcomm operada por visão (Jev), com o
Muse dirigindo passo a passo.

O script panel_add_tags.py falhou em abrir o diálogo (o clique no botão não
abriu nada e o Jev não achou o campo). Este driver não decide sozinho: ele
executa UMA ação por tarefa e devolve print + resultado, e o Muse olha cada
print antes do próximo passo. Navegação por visão: cada print passa pelo Jev
(Box); o clique usa as coordenadas do Jev com mouse humanizado.

Fila de tarefas por arquivo (operador é o Muse, via ssh):
  - escrever a tarefa em /tmp/panel-drive-job.json:
    {"id": "p1", "action": "goto"|"locate"|"click"|"type"|"shot",
     "target": "descrição do alvo para o Jev",
     "url": "https://...", "text": "texto a digitar"}
  - o agente lê, executa e escreve o resultado em /tmp/panel-drive-result.json
    + print em /tmp/panel-drive-shot.png
  - para parar: touch /tmp/panel-drive.stop (fecha o navegador de forma limpa)

Perfil persistente em /tmp/panel-tags-profile (a sessão do usuário sobrevive;
o navegador abre já logado na tela de Tags).
"""
import json
import random
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jev_navigate import locate, prep  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

BASE = Path("/tmp")
JOB = BASE / "panel-drive-job.json"
JOB_BUSY = BASE / "panel-drive-job.processing"
RESULT = BASE / "panel-drive-result.json"
SHOT = BASE / "panel-drive-shot.png"
STOP = BASE / "panel-drive.stop"
PROFILE = "/tmp/panel-tags-profile"
TAGS_URL = "https://deskcomm.petemcasa.com/app/settings/tags"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def pause(a: float = 0.8, b: float = 1.5) -> None:
    time.sleep(random.uniform(a, b))


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
    x, y = found["loc"]["x"], found["loc"]["y"]
    page.mouse.move(x, y, steps=8)
    time.sleep(0.4)
    page.mouse.click(x, y)
    pause(1.0, 1.8)
    depois = ver_pagina(page)
    shot(page)
    return {"ok": True, "action": "click", "found": found,
            "before": antes, "after": depois, "shot": str(SHOT)}


def do_type(page, target: str, text: str) -> dict:
    antes = ver_pagina(page)
    found = do_locate(page, target)
    if not found["loc"]:
        return {"ok": False, "action": "type", "found": found, "before": antes}
    x, y = found["loc"]["x"], found["loc"]["y"]
    page.mouse.move(x, y, steps=8)
    time.sleep(0.4)
    page.mouse.click(x, y)
    time.sleep(0.6)
    page.keyboard.type(text, delay=70)
    time.sleep(0.6)
    shot(page)
    return {"ok": True, "action": "type", "found": found, "text": text,
            "before": antes, "after": ver_pagina(page), "shot": str(SHOT)}


def do_job(page, job: dict) -> dict:
    action = job.get("action")
    if action == "goto":
        page.goto(job["url"], wait_until="domcontentloaded", timeout=60000)
        time.sleep(2)
        shot(page)
        return {"ok": True, "action": "goto", "page": ver_pagina(page), "shot": str(SHOT)}
    if action == "locate":
        return {"ok": True, "action": "locate", "found": do_locate(page, job["target"])}
    if action == "click":
        return do_click(page, job["target"])
    if action == "type":
        return do_type(page, job["target"], job.get("text", ""))
    if action == "scroll":
        dy = job.get("dy", 600)
        page.mouse.wheel(0, dy)
        time.sleep(1)
        shot(page)
        return {"ok": True, "action": "scroll", "dy": dy, "page": ver_pagina(page), "shot": str(SHOT)}
    if action == "shot":
        n = shot(page)
        return {"ok": True, "action": "shot", "bytes": n, "page": ver_pagina(page), "shot": str(SHOT)}
    return {"ok": False, "action": action, "error": "acao_desconhecida"}


def main() -> int:
    for f in (JOB, JOB_BUSY, STOP):
        f.unlink(missing_ok=True)
    RESULT.unlink(missing_ok=True)
    log("panel_drive: abrindo Chromium (Xfce :0, perfil persistente)...")
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            PROFILE, headless=False, viewport={"width": 1280, "height": 800},
            locale="pt-BR", args=["--window-size=1280,800"],
        )
        page = ctx.new_page()
        page.goto(TAGS_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(2)
        shot(page)
        log(f"aberto: {ver_pagina(page)} — aguardando tarefas em {JOB}")
        log("para parar: touch /tmp/panel-drive.stop")
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
