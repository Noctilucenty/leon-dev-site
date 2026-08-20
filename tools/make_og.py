#!/usr/bin/env python3
"""Regenerate assets/og.png — the 1200x630 social preview.

Run from the repo root:  python3 tools/make_og.py

Matches the site: pure black, mono, an ordered-dither purple field in the
top-right, and the same headline. Uses system fonts so it needs no downloads.
"""

import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG = (0, 0, 0)
FG = (250, 250, 250)
DIM = (119, 119, 119)
FAINT = (90, 90, 90)
AC = (155, 140, 255)

MONO = "/System/Library/Fonts/Menlo.ttc"
# HelveticaNeue.ttc face indices: 7 = Light (upright). 8 is Light *Italic* — not that one.
SANS = "/System/Library/Fonts/HelveticaNeue.ttc"

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(root, "assets", "og.png")

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# ── ordered-dither field, same 8x8 Bayer the site uses ──
BAYER = [
    0, 32, 8, 40, 2, 34, 10, 42,
    48, 16, 56, 24, 50, 18, 58, 26,
    12, 44, 4, 36, 14, 46, 6, 38,
    60, 28, 52, 20, 62, 30, 54, 22,
    3, 35, 11, 43, 1, 33, 9, 41,
    51, 19, 59, 27, 49, 17, 57, 25,
    15, 47, 7, 39, 13, 45, 5, 37,
    63, 31, 55, 23, 61, 29, 53, 21,
]
CELL = 6
import math

for gy in range(0, H // CELL + 1):
    for gx in range(0, W // CELL + 1):
        x = gx * CELL / W
        y = gy * CELL / H
        v = (math.sin(x * 2.1) * 0.5 + math.sin(y * 3.3) * 0.35 + math.sin((x + y) * 1.6) * 0.3)
        fall = max(0.0, 1 - abs(x - 0.86) * 1.5) * max(0.0, 1 - y * 1.1)
        v = (v * 0.5 + 0.5) * fall * 0.78
        if v > (BAYER[(gy % 8) * 8 + (gx % 8)] + 0.5) / 64:
            a = min(0.34, 0.10 + v * 0.5)
            c = (int(AC[0] * a), int(AC[1] * a), int(AC[2] * a))
            d.rectangle([gx * CELL, gy * CELL, gx * CELL + CELL - 2, gy * CELL + CELL - 2], fill=c)

f_mark = ImageFont.truetype(MONO, 22)
f_hand = ImageFont.truetype(MONO, 17)
f_disp = ImageFont.truetype(SANS, 74, index=7)
f_body = ImageFont.truetype(MONO, 19)
f_label = ImageFont.truetype(MONO, 15)

PAD = 84

# measured, not guessed — a fixed offset overlapped the name
x = PAD
d.text((x, 66), "[•]", font=f_mark, fill=AC)
x += d.textlength("[•]  ", font=f_mark)
d.text((x, 66), "Leon Kelvin Li", font=f_mark, fill=FG)
x += d.textlength("Leon Kelvin Li  ", font=f_mark)
d.text((x, 70), "/ Noctilucenty", font=f_hand, fill=FAINT)

d.text((PAD, 168), "i build the part of", font=f_disp, fill=DIM)
d.text((PAD, 250), "your business you", font=f_disp, fill=DIM)
d.text((PAD, 332), "still do by hand.", font=f_disp, fill=FG)

d.text((PAD, 452), "websites · apps · ai agents · automation", font=f_body, fill=(150, 150, 150))
d.text((PAD, 484), "built for how your business actually works", font=f_body, fill=(150, 150, 150))

d.line([(PAD, 546), (PAD + 86, 546)], fill=AC, width=3)
d.text((PAD, 566), "R E M O T E   ·   B U S I N E S S E S   A C R O S S   T H E   U . S .", font=f_label, fill=FAINT)

img.save(out, optimize=True)
print("wrote", out)
