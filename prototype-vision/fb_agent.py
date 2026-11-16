#!/home/pc/Workspace/tuttibom-ops/prototype-vision/.venv/bin/python
"""fb_agent — Camofox + Jev em consórcio, janela aberta e operada por visão.

O celular (S10/ADB) está descartado por enquanto; o acesso ao Facebook é por
aqui. O agente mantém o Camoufox aberto no Xfce :0 (perfil persistente +
impressão digital fixa, sessão do TuttiBom Novidade) e executa tarefas de
NAVEGAÇÃO por visão: cada print passa pelo Jev (Box), o clique usa as
coordenadas do Jev com mouse humanizado. Nada é publicado, enviado, curtido
ou digitado — só navegação e leitura, até o usuário pedir outra coisa.

Fila de tarefas por arquivo (operador é o Muse, via ssh):
  - escrever a tarefa em /tmp/fb-agent-job.json:
    {"id": "t1", "action": "goto"|"locate"|"click"|"shot",
     "target": "descrição do alvo para o Jev", "url": "https://..."}
  - o agente lê, executa e escreve o resultado em /tmp/fb-agent-result.json
    + print em /tmp/fb-agent-shot.png
  - para parar: touch /tmp/fb-agent.stop (fecha o navegador de forma limpa)
"""
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from camofox_driver import human_pause, launch, reading_pause  # noqa: E402
from jev_navigate import locate, prep  # noqa: E402

BASE = Path("/tmp")
JOB = BASE / "fb-agent-job.json"
JOB_BUSY = BASE / "fb-agent-job.processing"
RESULT = BASE / "fb-agent-result.json"
SHOT = BASE / "fb-agent-shot.png"
STOP = BASE / "fb-agent.stop"
URL_HOME = "https://www.facebook.com"


def log(msg: str) -> None:
    print(msg, flush=True)


def shot(page, path: str = str(SHOT)) -> int:
    png = page.screenshot(path=path, type="png")
    return len(png)


def ver_pagina(page) -> dict:
    return {"title": page.title(), "url": page.url}


def do_locate(page, target: str) -> dict:
    png = page.screenshot(type="png")
    _, w, h = prep(png)
    loc, rec = locate(png, target, w, h)
    out = {"target": target, "loc": loc, "noul": rec.get("noul"),
           "count": rec.get("count"), "confidence": rec.get("confidence"),
           "zoomed": rec.get("zoomed", False), "tokens": rec.get("input_tokens"),
           "latency_ms": rec.get("latency_ms"), "result": rec.get("result", "found")}
    return out


def do_click(page, target: str) -> dict:
    antes = ver_pagina(page)
    found = do_locate(page, target)
    if not found["loc"]:
        return {"ok": False, "action": "click", "found": found, "before": antes}
    human_pause()
    page.mouse.click(found["loc"]["x"], found["loc"]["y"])
    human_pause(0.8, 1.5)
    reading_pause(2.0, 4.0)
    depois = ver_pagina(page)
    shot(page)
    return {"ok": True, "action": "click", "found": found,
            "before": antes, "after": depois, "shot": str(SHOT)}


def do_job(page, job: dict) -> dict:
    action = job.get("action")
    if action == "goto":
        page.goto(job["url"], wait_until="load", timeout=60000)
        reading_pause()
        shot(page)
        return {"ok": True, "action": "goto", "page": ver_pagina(page), "shot": str(SHOT)}
    if action == "locate":
        return {"ok": True, "action": "locate", "found": do_locate(page, job["target"])}
    if action == "click":
        return do_click(page, job["target"])
    if action == "shot":
        n = shot(page)
        return {"ok": True, "action": "shot", "bytes": n, "page": ver_pagina(page), "shot": str(SHOT)}
    return {"ok": False, "action": action, "error": "acao_desconhecida"}


def main() -> int:
    for f in (JOB, JOB_BUSY, STOP):
        f.unlink(missing_ok=True)
    RESULT.unlink(missing_ok=True)
    log("fb_agent: abrindo Camoufox (Xfce :0, perfil persistente, humanize)...")
    with launch() as ctx:
        page = ctx.new_page()
        log(f"goto {URL_HOME}")
        page.goto(URL_HOME, wait_until="load", timeout=60000)
        reading_pause()
        shot(page)
        log(f"aberto: {ver_pagina(page)} — aguardando tarefas em {JOB}")
        log("para parar: touch /tmp/fb-agent.stop")
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
