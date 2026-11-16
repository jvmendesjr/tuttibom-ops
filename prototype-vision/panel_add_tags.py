#!/usr/bin/env python3
"""Cria `fita`, `3d` e `preco` como etiquetas OFICIAIS via o painel do Deskcomm,
pela nova superfície `adicionar` (botão "Adicionar etiqueta" na tela de Tags).

- Chromium com janela de verdade no Xfce :0: o usuário faz o login pela tela
  (noVNC), como no login do Facebook. O script espera o login e cria as 3
  tags sozinho, localizando cada controle com o Jev.
- Perfil persistente em /tmp/panel-tags-profile (a sessão sobrevive a um
  relançamento do script).
- Resultado em /tmp/tags-criadas.json; prints em /tmp/panel-tags-shot-*.png;
  log em /tmp/panel-tags.log.
- Para parar: touch /tmp/panel-tags.stop (o navegador fecha limpo).
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jev_navigate import locate  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

TAGS = ["fita", "3d", "preco"]
TAGS_URL = "https://deskcomm.petemcasa.com/app/settings/tags"
STOP = "/tmp/panel-tags.stop"
RESULT = "/tmp/tags-criadas.json"
LOGADO = "/tmp/deskcomm-logado.json"
PROFILE = "/tmp/panel-tags-profile"


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def shot(page, name):
    path = f"/tmp/panel-tags-shot-{name}.png"
    page.screenshot(path=path)
    return path


def jev_click(page, target):
    """Localiza com o Jev e clica com o mouse (humanizado). Devolve o achado ou None."""
    png = page.screenshot()
    w = page.viewport_size["width"]
    h = page.viewport_size["height"]
    found, rec = locate(png, target, w, h)
    log(f"locate {target!r} -> {rec.get('result')} noul={rec.get('noul')} conf={rec.get('confidence')}")
    if not found:
        return None
    page.mouse.move(found["x"], found["y"], steps=8)
    time.sleep(0.4)
    page.mouse.click(found["x"], found["y"])
    time.sleep(0.8)
    return found


def criar_uma(page, tag):
    """Cria uma etiqueta. Devolve dict com o resultado."""
    page.goto(TAGS_URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(1500)
    shot(page, f"antes-{tag}")
    if not jev_click(page, "o botão Adicionar etiqueta no topo da página de Tags"):
        return {"tag": tag, "status": "falhou", "etapa": "botao_adicionar"}
    page.wait_for_timeout(1200)
    shot(page, f"dialogo-{tag}")
    if not jev_click(page, "o campo de texto Nome da etiqueta no diálogo Adicionar etiqueta"):
        return {"tag": tag, "status": "falhou", "etapa": "campo_nome"}
    page.keyboard.type(tag, delay=70)
    page.wait_for_timeout(600)
    if not jev_click(page, "o botão Confirmar no diálogo Adicionar etiqueta"):
        return {"tag": tag, "status": "falhou", "etapa": "botao_confirmar"}
    page.wait_for_timeout(2500)
    shot(page, f"depois-{tag}")
    texto = page.evaluate("() => document.body.innerText")
    if "Etiqueta adicionada ao vocabulário" in texto:
        return {"tag": tag, "status": "criada"}
    if "já existe no vocabulário" in texto:
        return {"tag": tag, "status": "ja_existia"}
    if tag in texto:
        return {"tag": tag, "status": "criada_sem_toast_confirmado"}
    return {"tag": tag, "status": "falhou", "etapa": "confirmacao"}


def main():
    resultados = {"inicio": time.strftime("%Y-%m-%d %H:%M:%S"), "tags": {}}
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            PROFILE, headless=False, viewport={"width": 1280, "height": 800},
            locale="pt-BR", args=["--window-size=1280,800"],
        )
        page = ctx.new_page()
        page.goto(TAGS_URL, wait_until="networkidle", timeout=60000)
        log(f"aberto: {page.url} — aguardando login")
        # Espera o login: a URL sai de /login e entra em /app.
        while True:
            if os.path.exists(STOP):
                log("stop encontrado antes do login — fechando")
                break
            if "/login" not in page.url and "/app" in page.url:
                break
            time.sleep(5)
        if os.path.exists(STOP):
            ctx.close()
            return
        log(f"login detectado: {page.url}")
        with open(LOGADO, "w", encoding="utf-8") as f:
            json.dump({"url": page.url, "quando": time.strftime("%Y-%m-%d %H:%M:%S")}, f)
        for tag in TAGS:
            try:
                r = criar_uma(page, tag)
            except Exception as e:  # noqa: BLE001 - registra e segue para a próxima
                r = {"tag": tag, "status": "falhou", "etapa": "excecao", "erro": str(e)[:200]}
            resultados["tags"][tag] = r
            log(f"tag {tag}: {r['status']}")
            time.sleep(2)
        resultados["fim"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(RESULT, "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        log(f"resultado gravado em {RESULT}: {resultados['tags']}")
        # Mantém o navegador aberto para conferência até o stop.
        while not os.path.exists(STOP):
            time.sleep(5)
        log("stop encontrado — fechando navegador")
        ctx.close()


if __name__ == "__main__":
    main()
