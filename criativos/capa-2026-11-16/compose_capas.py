#!/usr/bin/env python3
"""Compoe as 3 propostas de capa TuttiBom (1640x624) com tipografia por codigo."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT = Path("/workspace/tuttibom/capa")
W, H = 1640, 624
SAFE = (220, 80, 1420, 544)  # 1200x464 centered
# Zona da foto de perfil (sobreposição no canto inferior esquerdo).
# Circulo ~170 CSS (~336 px a 2x), com folga. Nada importante aqui.
PROFILE_C = (220, 640)  # centro um pouco abaixo da borda
PROFILE_R = 190

FONT_FRAUNCES = "/usr/share/fonts/truetype/sand-box/google/Fraunces/Fraunces-VariableFont_SOFT,WONK,opsz,wght.ttf"
FONT_FRAUNCES_IT = "/usr/share/fonts/truetype/sand-box/google/Fraunces/Fraunces-Italic-VariableFont_SOFT,WONK,opsz,wght.ttf"
FONT_INTER = "/usr/share/fonts/truetype/sand-box/google/Inter/Inter-VariableFont_opsz,wght.ttf"

BG = {
    "A": Path("/cursor/stores/user/grok-bot/agents/2ad6103f-e4b2-49c2-9e2c-5a819a43f934/assets/e6fb0d0ab68f8e0ae568d01ea1632491228ea8e8d8a7273f25a0a08a33209c3b.jpg"),
    "B": Path("/cursor/stores/user/grok-bot/agents/2ad6103f-e4b2-49c2-9e2c-5a819a43f934/assets/f7c9f17bad6732b72b58128e3b9861466a4191188b84faa53beec8b14b7307d1.jpg"),
    "C": Path("/cursor/stores/user/grok-bot/agents/2ad6103f-e4b2-49c2-9e2c-5a819a43f934/assets/03e330ead074b325dd144c9998ab788f633ea5b0a1c4e1f2cfaddf2610a703dd.jpg"),
}

MARROM = (92, 58, 42)       # aprox. Marrom 46
MARROM_ESC = (58, 36, 26)
DOURADO = (201, 162, 39)    # aprox. Dourado 47
PEROLA = (246, 237, 227)    # aprox. Pérola 50
ROSA_BEBE = (244, 196, 207) # aprox. Rosa Bebê 03
BRANCO = (255, 255, 255)
PRETO = (26, 26, 26)


def font_var(path, size, axes):
    f = ImageFont.truetype(path, size)
    f.set_variation_by_axes(list(axes))
    return f


def fraunces(size, weight=500, soft=30, wonk=0, italic=False):
    path = FONT_FRAUNCES_IT if italic else FONT_FRAUNCES
    # eixos: Optical Size, Weight, Softness, Wonky
    opsz = max(9, min(144, size * 0.7))
    return font_var(path, size, (opsz, weight, soft, wonk))


def inter(size, weight=500):
    opsz = max(14, min(32, size * 0.35 + 14))
    return font_var(FONT_INTER, size, (opsz, weight))


def text_width(font, text, tracking=0):
    if not text:
        return 0
    w = 0
    for i, ch in enumerate(text):
        w += font.getlength(ch)
        if i < len(text) - 1:
            w += tracking
    return w


def draw_tracked(draw, xy, text, font, fill, tracking=0, anchor="lt"):
    x, y = xy
    width = text_width(font, text, tracking)
    # aproximar anchors horizontais
    if "m" in anchor:  # middle x
        x -= width / 2
    elif "r" in anchor:
        x -= width
    # vertical: use bbox of a reference
    asc = font.getmetrics()[0]
    dsc = font.getmetrics()[1]
    if "m" in anchor and anchor[0] in "m":  # mm
        # Pillow style: first char is baseline-related; we treat y as top if lt
        pass
    # we always draw from top-left after adjustment
    # For 'mt' (middle-top) we already shifted x. y is top.
    cx = x
    for i, ch in enumerate(text):
        draw.text((cx, y), ch, font=font, fill=fill)
        cx += font.getlength(ch) + (tracking if i < len(text) - 1 else 0)
    return width


def crop_to_cover(src: Image.Image, y_ratio: float) -> Image.Image:
    """y_ratio: 0 = top-aligned crop, 1 = bottom-aligned, 0.5 = center."""
    sw, sh = src.size
    crop_h = sw * H / W
    if crop_h > sh:
        # letterbox shouldn't happen
        crop_h = sh
        crop_w = sh * W / H
        x0 = (sw - crop_w) / 2
        box = (x0, 0, x0 + crop_w, sh)
    else:
        y0 = (sh - crop_h) * y_ratio
        box = (0, y0, sw, y0 + crop_h)
    cropped = src.crop(tuple(map(int, box)))
    return cropped.resize((W, H), Image.Resampling.LANCZOS)


def rounded_rect(size, radius, fill):
    w, h = size
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=fill)
    return im


def paste_rgba(base, overlay, xy):
    base.paste(overlay, xy, overlay)


def typography_block(align="left"):
    """Prepara fontes e strings. Medidas feitas no canvas depois."""
    return {
        "kicker": "TUTTIBOM",
        "line1": "Fitas personalizadas",
        "line2": "& impressão 3D",
        "place": "Cariri",
        "align": align,
    }


def measure_block(fonts, tracking_kicker):
    tw = {
        "kicker": text_width(fonts["kicker"], "TUTTIBOM", tracking_kicker),
        "line1": text_width(fonts["line1"], "Fitas personalizadas"),
        "line2": text_width(fonts["line2"], "& impressão 3D"),
        "place": text_width(fonts["place"], "Cariri"),
    }
    return tw


def draw_block(canvas, origin, fonts, colors, align="left", scrim=None, rule=True):
    """origin is top-left of the block if left, or top-center if center."""
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    tracking_kicker = 8
    fonts_ok = fonts
    tw = measure_block(fonts_ok, tracking_kicker)

    # vertical rhythm
    kicker_h = fonts_ok["kicker"].size
    line1_h = fonts_ok["line1"].size
    line2_h = fonts_ok["line2"].size
    place_h = fonts_ok["place"].size
    gap_k = 18
    gap_12 = 6
    gap_rule = 22
    rule_h = 2
    gap_place = 16

    content_w = max(tw.values())
    block_h = (
        kicker_h
        + gap_k
        + line1_h
        + gap_12
        + line2_h
        + (gap_rule + rule_h + gap_place if rule else 18)
        + place_h
    )

    if align == "center":
        cx, top = origin
        left = int(cx - content_w / 2)
    else:
        left, top = origin
        cx = left + content_w / 2

    pad_x, pad_y = 36, 28
    if scrim is not None:
        sw = int(content_w + pad_x * 2)
        sh = int(block_h + pad_y * 2)
        box = rounded_rect((sw, sh), 28, scrim)
        # soft edge
        box = box.filter(ImageFilter.GaussianBlur(radius=0.6))
        if align == "center":
            bx = int(cx - sw / 2)
        else:
            bx = int(left - pad_x)
        by = int(top - pad_y)
        paste_rgba(overlay, box, (bx, by))

    y = top
    # kicker
    if align == "center":
        draw_tracked(d, (cx, y), "TUTTIBOM", fonts_ok["kicker"], colors["kicker"], tracking_kicker, anchor="mt")
    else:
        draw_tracked(d, (left, y), "TUTTIBOM", fonts_ok["kicker"], colors["kicker"], tracking_kicker, anchor="lt")
    y += kicker_h + gap_k

    if align == "center":
        d.text((cx, y), "Fitas personalizadas", font=fonts_ok["line1"], fill=colors["line"], anchor="mt")
    else:
        d.text((left, y), "Fitas personalizadas", font=fonts_ok["line1"], fill=colors["line"])
    y += line1_h + gap_12

    if align == "center":
        d.text((cx, y), "& impressão 3D", font=fonts_ok["line2"], fill=colors["line"], anchor="mt")
    else:
        d.text((left, y), "& impressão 3D", font=fonts_ok["line2"], fill=colors["line"])
    y += line2_h

    if rule:
        y += gap_rule
        rw = 72
        if align == "center":
            x0 = int(cx - rw / 2)
        else:
            x0 = int(left)
        d.rectangle((x0, y, x0 + rw, y + rule_h), fill=colors["rule"])
        y += rule_h + gap_place
    else:
        y += 18

    if align == "center":
        d.text((cx, y), "Cariri", font=fonts_ok["place"], fill=colors["place"], anchor="mt")
    else:
        d.text((left, y), "Cariri", font=fonts_ok["place"], fill=colors["place"])

    out = canvas.convert("RGBA")
    out = Image.alpha_composite(out, overlay)
    return out.convert("RGB"), (left, top, content_w, block_h)


def make_guide(img: Image.Image) -> Image.Image:
    out = img.convert("RGBA")
    overlay = Image.new("RGBA", out.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # dim outside safe zone
    dim = (20, 20, 20, 80)
    x0, y0, x1, y1 = SAFE
    d.rectangle((0, 0, W, y0), fill=dim)
    d.rectangle((0, y1, W, H), fill=dim)
    d.rectangle((0, y0, x0, y1), fill=dim)
    d.rectangle((x1, y0, W, y1), fill=dim)
    # safe rect
    d.rectangle(SAFE, outline=(0, 180, 120, 230), width=3)
    # profile circle
    cx, cy = PROFILE_C
    r = PROFILE_R
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(220, 60, 80, 240), width=4)
    # hatch the profile overlap inside the cover
    # draw a filled translucent ellipse, then crop to cover bounds by just drawing it
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(220, 60, 80, 70))

    label_f = inter(22, 600)
    small_f = inter(16, 500)
    # labels with dark chips
    def chip(xy, text, color):
        tw = text_width(label_f, text) + 16
        th = 28
        x, y = xy
        d.rounded_rectangle((x, y, x + tw, y + th), 6, fill=(*color, 220))
        d.text((x + 8, y + 4), text, font=label_f, fill=BRANCO)

    chip((x0 + 10, y0 + 10), "zona segura 1200×464", (0, 130, 90))
    chip((24, H - 48), "foto de perfil (não cobrir)", (180, 40, 60))
    d.text((W - 14, 14), "1640×624  ·  rascunho  ·  não publicar", font=small_f, fill=(255, 255, 255, 230), anchor="rt")

    out = Image.alpha_composite(out, overlay)
    return out.convert("RGB")


def compose_A():
    bg = crop_to_cover(Image.open(BG["A"]).convert("RGB"), y_ratio=0.82)
    fonts = {
        "kicker": inter(22, 550),
        "line1": fraunces(64, weight=500, soft=35, italic=False),
        "line2": fraunces(58, weight=450, soft=40, italic=True),
        "place": inter(24, 500),
    }
    colors = {
        "kicker": MARROM,
        "line": MARROM_ESC,
        "rule": DOURADO,
        "place": MARROM,
    }
    # texto à esquerda, dentro da zona segura, acima da foto de perfil
    img, box = draw_block(bg, (280, 155), fonts, colors, align="left", scrim=None, rule=True)
    return img


def compose_B():
    bg = crop_to_cover(Image.open(BG["B"]).convert("RGB"), y_ratio=0.50)
    fonts = {
        "kicker": inter(20, 550),
        "line1": fraunces(58, weight=500, soft=30, italic=False),
        "line2": fraunces(52, weight=450, soft=36, italic=True),
        "place": inter(22, 500),
    }
    colors = {
        "kicker": MARROM,
        "line": MARROM_ESC,
        "rule": DOURADO,
        "place": MARROM,
    }
    # centro visual do vazio, ligeiramente à esquerda das peças 3D
    scrim = (252, 246, 238, 200)
    img, box = draw_block(bg, (760, 175), fonts, colors, align="center", scrim=scrim, rule=True)
    return img


def compose_C():
    bg = crop_to_cover(Image.open(BG["C"]).convert("RGB"), y_ratio=0.48)
    fonts = {
        "kicker": inter(22, 550),
        "line1": fraunces(60, weight=500, soft=32, italic=False),
        "line2": fraunces(54, weight=450, soft=38, italic=True),
        "place": inter(22, 500),
    }
    colors = {
        "kicker": ROSA_BEBE,
        "line": BRANCO,
        "rule": DOURADO,
        "place": PEROLA,
    }
    # à esquerda-centro, sobre a parede/janela, longe da foto de perfil
    scrim = (20, 14, 10, 145)
    img, box = draw_block(bg, (280, 150), fonts, colors, align="left", scrim=scrim, rule=True)
    return img


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    # also keep backgrounds
    for key, src in BG.items():
        Image.open(src).save(ROOT / f"capa-{key}-bg-original.jpg", quality=95)

    composers = {"A": compose_A, "B": compose_B, "C": compose_C}
    for key, fn in composers.items():
        img = fn()
        assert img.size == (W, H), img.size
        path = ROOT / f"capa-{key}.png"
        img.save(path, "PNG", optimize=True)
        guide = make_guide(img)
        gpath = ROOT / f"capa-{key}-guia.png"
        guide.save(gpath, "PNG", optimize=True)
        print(f"saved {path} {path.stat().st_size} {img.size}")
        print(f"saved {gpath} {gpath.stat().st_size}")

    # contact sheet for QA
    thumbs = []
    for key in "ABC":
        a = Image.open(ROOT / f"capa-{key}.png")
        b = Image.open(ROOT / f"capa-{key}-guia.png")
        thumbs.append(a)
        thumbs.append(b)
    sheet = Image.new("RGB", (W, H * 6 + 20 * 5), (30, 30, 30))
    y = 0
    for t in thumbs:
        sheet.paste(t, (0, y))
        y += H + 20
    sheet.save(ROOT / "capa-contato-qa.png", "PNG")
    print("contact sheet ok")


if __name__ == "__main__":
    main()
