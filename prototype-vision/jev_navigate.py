#!/usr/bin/env python3
"""jev_navigate — prototype core: screenshot -> Jev Box -> coordinates.

One Jev core, two drivers (Playwright panel, ADB phone). Model pinned: jev-1.14.0.
Image prep: EXIF-transpose, longest side <= 1568, baseline JPEG q90 (PIL).
locate() = one ask with Noul + Choice + Box; gates: noul < 0.5 or count != "one"
-> None; confidence < 0.6 -> zoom pass (half-size crop centred on the box, re-ask,
map back). Every call is logged to JSONL (tokens, latency, confidence, hit/miss).

Usage:
  python3 jev_navigate.py probe <png> "<target>"     # one locate, raw answers
  python3 jev_navigate.py panel <png> <targets.json> # 10-target accuracy run
"""
import io
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/pc/.hermes/plugins/hermes-jev")
from jevkit import client, images  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

MODEL = "jev-1.14.0"
MAX_SIDE = 1568
LOG = Path("/tmp/jev_navigate.jsonl")


def prep(png_bytes):
    """Upright, longest side <= 1568, baseline JPEG q90. Returns (jpeg_bytes, w, h)."""
    im = Image.open(io.BytesIO(png_bytes))
    im = ImageOps.exif_transpose(im)
    if im.mode != "RGB":
        im = im.convert("RGB")
    w, h = im.size
    if max(w, h) > MAX_SIDE:
        scale = MAX_SIDE / max(w, h)
        im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
        w, h = im.size
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=90, progressive=False)
    return buf.getvalue(), w, h


def _ask(screen_jpeg, target, w, h):
    ref, picture = images.asset(screen_jpeg)
    out = client.ask(
        {"screen": ref},
        {
            "visible": client.noul(f"Is there {target} in `screen`?"),
            "count": client.choice(
                f"How many {target} are in `screen`?",
                {"none": "No such element.", "one": "Exactly one.", "several": "More than one."},
            ),
            "target": client.box(f"the {target} in `screen`"),
        },
        assets={ref: picture},
        model=MODEL,
    )
    return out


def _parse(out):
    a = out["answers"]
    noul = a["visible"]["noul"]
    count = a["count"]["choice"]
    b = a["target"]
    return noul, count, b["box"], b["confidence"]


def locate(screen_png, target, w, h):
    """Returns dict or None. `w,h` are the screenshot pixel dims (after prep they match)."""
    jpeg, pw, ph = prep(screen_png)
    t0 = time.time()
    out = _ask(jpeg, target, pw, ph)
    latency_ms = out.get("latency_ms") or round((time.time() - t0) * 1000)
    rec = {
        "target": target, "model": out.get("jev_model"),
        "input_tokens": out.get("input_tokens"), "latency_ms": latency_ms,
    }
    noul, count, box, conf = _parse(out)
    rec.update({"noul": noul, "count": count, "box": box, "confidence": conf})
    if noul < 0.5 or count != "one":
        rec["result"] = "not_found_or_ambiguous"
        _log(rec)
        return None, rec
    if conf < 0.6:
        zoomed = _zoom(jpeg, target, box, pw, ph)
        if zoomed is None:
            rec["result"] = "low_confidence_after_zoom"
            _log(rec)
            return None, rec
        box, conf = zoomed
        rec.update({"box": box, "confidence": conf, "zoomed": True})
    cx = (box["left"] + box["right"]) / 2 * w
    cy = (box["top"] + box["bottom"]) / 2 * h
    rec.update({"result": "located", "x": round(cx), "y": round(cy)})
    _log(rec)
    return {"x": round(cx), "y": round(cy), "confidence": conf, "noul": noul}, rec


def _zoom(prepped_jpeg, target, box, w, h):
    """Half-size crop centred on the first box; re-ask; map fractions back."""
    cx = (box["left"] + box["right"]) / 2 * w
    cy = (box["top"] + box["bottom"]) / 2 * h
    cw, ch = w // 2, h // 2
    x0 = max(0, min(w - cw, round(cx - cw / 2)))
    y0 = max(0, min(h - ch, round(cy - ch / 2)))
    im = Image.open(io.BytesIO(prepped_jpeg)).convert("RGB")
    crop = im.crop((x0, y0, x0 + cw, y0 + ch))
    buf = io.BytesIO()
    crop.save(buf, format="JPEG", quality=90, progressive=False)
    out = _ask(buf.getvalue(), target, cw, ch)
    noul, count, b2, conf2 = _parse(out)
    if noul < 0.5 or count != "one" or conf2 < 0.6:
        return None
    return {
        "left": (x0 + b2["left"] * cw) / w,
        "top": (y0 + b2["top"] * ch) / h,
        "right": (x0 + b2["right"] * cw) / w,
        "bottom": (y0 + b2["bottom"] * ch) / h,
    }, conf2


def _log(rec):
    with LOG.open("a") as f:
        f.write(json.dumps(rec) + "\n")


PANEL_TARGETS = [
    ("campo de e-mail", 448, 285, 384, 40),
    ("campo de senha", 448, 367, 384, 40),
    ("botão mostrar senha", 788, 367, 44, 40),
    ("botão Entrar", 448, 423, 384, 36),
    ("botão Entrar com Google", 448, 515, 384, 36),
    ("link Esqueci minha senha", 574, 576, 132, 17),
    ("link Criar conta", 656, 604, 70, 17),
    ("título Entrar", 448, 177, 384, 32),
    ("texto DeskComm", 448, 215, 384, 20),
    ("rótulo Email", 448, 265, 34, 14),
]


def main():
    cmd = sys.argv[1]
    if cmd == "probe":
        png = Path(sys.argv[2]).read_bytes()
        target = sys.argv[3]
        jpeg, w, h = prep(png)
        out = _ask(jpeg, target, w, h)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return
    if cmd == "panel":
        png = Path(sys.argv[2]).read_bytes()
        jpeg, w, h = prep(png)
        print(f"screenshot {w}x{h}, jpeg {len(jpeg)} bytes")
        results = []
        for name, x, y, ew, eh in PANEL_TARGETS:
            loc, rec = locate(png, name, w, h)
            hit = bool(loc and x <= loc["x"] <= x + ew and y <= loc["y"] <= y + eh)
            results.append({"target": name, "hit": hit, "loc": loc,
                            "noul": rec.get("noul"), "confidence": rec.get("confidence"),
                            "input_tokens": rec.get("input_tokens"), "latency_ms": rec.get("latency_ms"),
                            "zoomed": rec.get("zoomed", False), "result": rec.get("result")})
            print(f"{'HIT ' if hit else 'MISS'} {name:28s} loc={loc} noul={rec.get('noul')} conf={rec.get('confidence')} tok={rec.get('input_tokens')} {rec.get('latency_ms')}ms{' ZOOM' if rec.get('zoomed') else ''}")
        hits = sum(r["hit"] for r in results)
        toks = [r["input_tokens"] for r in results if r["input_tokens"]]
        lats = [r["latency_ms"] for r in results if r["latency_ms"]]
        for th in (0.5, 0.6, 0.9):
            kept = [r for r in results if r["confidence"] is not None and r["confidence"] >= th]
            kh = sum(r["hit"] for r in kept)
            print(f"threshold {th}: kept {len(kept)}/10, hits among kept {kh} ({kh/len(kept)*100:.0f}%)" if kept else f"threshold {th}: kept 0/10")
        print(f"TOTAL hits {hits}/10 ({hits*10}%) | mean tokens/locate {sum(toks)/len(toks):.0f} | mean latency {sum(lats)/len(lats):.0f}ms")
        Path("/tmp/panel-accuracy.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
        return
    print("unknown cmd", cmd)
    sys.exit(2)


if __name__ == "__main__":
    main()
