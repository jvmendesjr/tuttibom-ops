#!/home/pc/Workspace/tuttibom-ops/prototype-vision/.venv/bin/python
"""fb_test — teste SEM LOGIN no facebook.com via Camoufox original.

Prova o loop (print -> Jev Box -> clique humanizado) nas páginas do Facebook
sem tocar na conta: só localiza os campos de login e clica no campo de e-mail
para confirmar o foco. Nada é digitado, nada é enviado, nenhum login é tentado.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from camofox_driver import human_pause, launch, reading_pause  # noqa: E402
from jev_navigate import locate, prep  # noqa: E402

URL = "https://www.facebook.com"
SHOT = "/tmp/fb-login.png"

GT_JS = """() => {
  const pick = (sels) => {
    for (const s of sels) {
      const el = document.querySelector(s);
      if (!el) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) continue;
      return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width),
              h: Math.round(r.height), cx: Math.round(r.x + r.width/2),
              cy: Math.round(r.y + r.height/2)};
    }
    return null;
  };
  return {
    email: pick(['input[name="email"]', 'input#email', 'input[type="text"]']),
    pass: pick(['input[name="pass"]', 'input#pass', 'input[type="password"]']),
    login: pick(['button[name="login"]', 'button[type="submit"]']),
    title: document.title,
    url: location.href,
  };
}"""

TARGETS = [
    ("email", "campo de e-mail ou número de telefone"),
    ("pass", "campo de senha"),
    ("login", "botão Entrar"),
]


def main():
    print("launching Camoufox (Xfce :0, perfil persistente, humanize)...", flush=True)
    with launch() as ctx:
        page = ctx.new_page()
        print("goto", URL)
        page.goto(URL, wait_until="load", timeout=60000)
        reading_pause()
        gt = page.evaluate(GT_JS)
        print("page:", json.dumps(gt, ensure_ascii=False))
        png = page.screenshot(path=SHOT, type="png")
        print(f"screenshot {len(png)} bytes -> {SHOT}")
        _, w, h = prep(png)
        hits = 0
        for key, target in TARGETS:
            loc, rec = locate(png, target, w, h)
            g = gt.get(key)
            hit = bool(loc and g and g["x"] <= loc["x"] <= g["x"] + g["w"]
                       and g["y"] <= loc["y"] <= g["y"] + g["h"])
            hits += hit
            print(f"{'HIT ' if hit else 'MISS'} {target:38s} loc={loc} "
                  f"noul={rec.get('noul')} conf={rec.get('confidence')} "
                  f"tok={rec.get('input_tokens')} {rec.get('latency_ms')}ms "
                  f"truth={g}")
        # clique de verificação: só foco, sem digitar
        loc, _ = locate(png, "campo de e-mail ou número de telefone", w, h)
        if loc:
            human_pause()
            page.mouse.click(loc["x"], loc["y"])
            human_pause(0.8, 1.5)
            active = page.evaluate(
                "() => { const el = document.activeElement; return el ? "
                "{tag: el.tagName.toLowerCase(), name: el.getAttribute('name'), "
                "type: el.getAttribute('type')} : null; }")
            print("click email field -> activeElement:", active,
                  "->", "VERIFIED" if active and active.get("name") == "email" else "NOT VERIFIED")
        print(f"RESULTADO: {hits}/{len(TARGETS)} alvos | url final: {page.url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
