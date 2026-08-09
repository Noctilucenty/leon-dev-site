#!/usr/bin/env python3
"""Regenerate assets/og.png — the 1200x630 social preview.

Run from the repo root:  python3 tools/make_og.py
Uses system fonts, so it needs no downloads: Impact for the display line,
Menlo for the mono labels, Futura for the body.
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1200, 630
BG = (8, 8, 10)
CREAM = (239, 237, 230)
ACCENT = (158, 147, 228)
BODY = (178, 176, 171)
LABEL = (122, 120, 114)
FOOT = (112, 110, 106)

IMPACT = "/System/Library/Fonts/Supplemental/Impact.ttf"
MENLO = "/System/Library/Fonts/Menlo.ttc"
FUTURA = "/System/Library/Fonts/Supplemental/Futura.ttc"

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(root, "assets", "og.png")

img = Image.new("RGB", (W, H), BG)

# violet bloom, blurred hard so no edge of the drawn ellipses survives
glow = Image.new("RGB", (W, H), BG)
gd = ImageDraw.Draw(glow)
for i in range(60, 0, -1):
    r = i * 16
    t = i / 60.0
    gd.ellipse(
        [260 - r, -110 - r, 260 + r, -110 + r],
        fill=(
            int(8 + 34 * (1 - t) ** 2),
            int(8 + 30 * (1 - t) ** 2),
            int(10 + 52 * (1 - t) ** 2),
        ),
    )
img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(70)), 0.95)

d = ImageDraw.Draw(img)
for x in range(0, W, 64):
    d.line([(x, 0), (x, H)], fill=(21, 21, 27), width=1)
for y in range(0, H, 64):
    d.line([(0, y), (W, y)], fill=(21, 21, 27), width=1)

f_disp = ImageFont.truetype(IMPACT, 118)
f_mono = ImageFont.truetype(MENLO, 21)
f_small = ImageFont.truetype(MENLO, 19)
f_body = ImageFont.truetype(FUTURA, 27)

PAD = 84
d.text((PAD, 74), "L E O N   D E V .", font=f_mono, fill=ACCENT)
d.text((PAD, 108), "S O F T W A R E   &   A I   S O L U T I O N S", font=f_small, fill=LABEL)
d.text((PAD, 192), "CUSTOM SOFTWARE.", font=f_disp, fill=CREAM)
d.text((PAD, 312), "REAL RESULTS.", font=f_disp, fill=ACCENT)
d.line([(PAD, 452), (PAD + 118, 452)], fill=ACCENT, width=5)
d.text((PAD, 486), "Websites, mobile apps, AI agents and automation —", font=f_body, fill=BODY)
d.text((PAD, 524), "built for your business, not from a template.", font=f_body, fill=BODY)
d.text((PAD, 578), "H A Y W A R D ,  C A   ·   R E M O T E   W O R L D W I D E", font=f_small, fill=FOOT)

img.save(out, optimize=True)
print("wrote", out)
