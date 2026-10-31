"""Generates the Channel 8 retro logo, TV banner and launcher icons.
Run: python make_logo.py  (requires Pillow)"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "app", "src", "main", "res")
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

NAVY = (10, 24, 74)
BLUE = (22, 86, 196)
CYAN = (64, 170, 255)
ORANGE = (255, 122, 26)
GOLD = (255, 196, 40)
WHITE = (255, 255, 255)


def vgrad(w, h, top, bottom):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


def background(w, h):
    img = vgrad(w, h, BLUE, NAVY)
    d = ImageDraw.Draw(img, "RGBA")
    # diagonal retro speed stripes
    s = max(2, h // 18)
    for i, col in enumerate([ORANGE, GOLD, CYAN]):
        off = int(w * 0.55) + i * s * 2
        d.polygon([(off, h), (off + s, h), (off + s + h, 0), (off + h, 0)], fill=col + (90,))
    # scanlines
    for y in range(0, h, max(2, h // 90)):
        d.line([(0, y), (w, y)], fill=(0, 0, 0, 28))
    return img


def big_eight(size):
    """Returns an RGBA image of an orange '8' with gold face, navy outline and 3D extrusion."""
    font = ImageFont.truetype(BOLD, size)
    bbox = font.getbbox("8")
    gw, gh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    depth = max(2, size // 14)
    stroke = max(2, size // 22)
    pad = stroke * 2 + depth
    img = Image.new("RGBA", (gw + pad * 2, gh + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ox, oy = pad - bbox[0], pad - bbox[1]
    # extrusion (down-right)
    for k in range(depth, 0, -1):
        d.text((ox + k, oy + k), "8", font=font, fill=NAVY, stroke_width=stroke, stroke_fill=NAVY)
    d.text((ox, oy), "8", font=font, fill=ORANGE, stroke_width=stroke, stroke_fill=WHITE)
    # gold highlight on top half of glyph
    face = Image.new("L", img.size, 0)
    ImageDraw.Draw(face).text((ox, oy), "8", font=font, fill=255)
    hl = Image.new("L", img.size, 0)
    ImageDraw.Draw(hl).rectangle([0, 0, img.size[0], oy + bbox[1] + gh * 0.42], fill=255)
    from PIL import ImageChops
    mask = ImageChops.multiply(face, hl)
    img.paste(Image.new("RGBA", img.size, GOLD + (255,)), (0, 0), mask)
    return img


def channel_tag(text, h):
    font = ImageFont.truetype(BOLD, int(h * 0.62))
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    w = tw + h  # slanted ends
    img = Image.new("RGBA", (w + h // 2, h + h // 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    sk = h // 3
    sh = h // 6
    d.polygon([(sk + sh, sh), (w + sh, sh), (w - sk + sh, h + sh), (sh, h + sh)], fill=NAVY)
    d.polygon([(sk, 0), (w, 0), (w - sk, h), (0, h)], fill=ORANGE, outline=WHITE, width=max(1, h // 14))
    d.text(((w - tw) // 2 - bbox[0], (h - (bbox[3] - bbox[1])) // 2 - bbox[1]), text, font=font, fill=WHITE)
    return img


def logo_on(bg, eight_h, tag_h, layout):
    w, h = bg.size
    e = big_eight(eight_h)
    t = channel_tag("CHANNEL", tag_h)
    if layout == "row":
        e = e.crop(e.getbbox())
        t = t.crop(t.getbbox())
        gap = tag_h // 5
        total = t.size[0] + gap + e.size[0]
        x0 = (w - total) // 2
        bg.alpha_composite(e, (x0 + t.size[0] + gap, (h - e.size[1]) // 2))
        bg.alpha_composite(t, (x0, (h - t.size[1]) // 2 + tag_h // 3))
    else:  # stacked: 8 on top, tag across the bottom
        bg.alpha_composite(e, ((w - e.size[0]) // 2, int(h * 0.04)))
        bg.alpha_composite(t, ((w - t.size[0]) // 2, int(h * 0.70)))
    return bg


def save(img, rel):
    p = os.path.join(RES, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.convert("RGB" if rel.endswith("banner.png") else "RGBA").save(p, optimize=True)
    print("wrote", os.path.relpath(p, os.path.join(HERE, "..")))


# Master logo (1024 square) and wide master
master = logo_on(background(1024, 1024).convert("RGBA"), 720, 190, "stack")
master.save(os.path.join(HERE, "logo_1024.png"))
wide = logo_on(background(1280, 720).convert("RGBA"), 560, 160, "row")
wide.save(os.path.join(HERE, "logo_wide.png"))

# TV banner 320x180 (drawn at 4x then downsampled for smooth edges)
banner = logo_on(background(1280, 720).convert("RGBA"), 520, 170, "row").resize((320, 180), Image.LANCZOS)
save(banner, "drawable-xhdpi/banner.png")

# Launcher icons (rounded square)
def icon(px):
    big = master.resize((px * 4, px * 4), Image.LANCZOS)
    m = Image.new("L", big.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, big.size[0] - 1, big.size[1] - 1], radius=big.size[0] // 6, fill=255)
    out = Image.new("RGBA", big.size, (0, 0, 0, 0))
    out.paste(big, (0, 0), m)
    return out.resize((px, px), Image.LANCZOS)

for dpi, px in {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}.items():
    save(icon(px), f"mipmap-{dpi}/ic_launcher.png")

# Splash/reconnect logo used in-app
save(wide.resize((640, 360), Image.LANCZOS), "drawable-nodpi/logo.png")
