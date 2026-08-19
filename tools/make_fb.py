#!/usr/bin/env python3
"""Build assets/facebook.png — the 1200x1200 listing image.

Square on purpose: Facebook Marketplace crops the thumbnail to a square, so
anything that matters has to survive that crop. Same palette, same dither and
the same headline as the site, so the listing and the site read as one thing.

Run from the repo root:  python3 tools/make_fb.py
"""

import math
import os
from PIL import Image, ImageDraw, ImageFont

S = 1200
BG = (0, 0, 0)
FG = (250, 250, 250)
MID = (170, 170, 170)
DIM = (119, 119, 119)
FAINT = (90, 90, 90)
AC = (155, 140, 255)
LINE = (34, 34, 34)

MONO = "/System/Library/Fonts/Menlo.ttc"
SANS = "/System/Library/Fonts/HelveticaNeue.ttc"   # index 7 = Light, upright

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(root, "assets", "facebook.png")

# prices here are the site's prices — keep the two in step
SERVICES = [
    ("small fixes",            "$49+"),
    ("workflow automation",    "$600+"),
    ("booking & ordering",     "$600+"),
    ("dashboards & tools",     "$750+"),
    ("ai chatbots",            "$1,000+"),
    ("business websites",      "$1,200+"),
    ("ai phone agents",        "$1,200+"),
    ("crm & inventory",        "$1,500+"),
    ("online ordering",        "$2,000+"),
    ("customer portals",       "$2,500+"),
    ("custom software",        "$3,500+"),
    ("ios & android apps",     "$4,500+"),
]

img = Image.new("RGB", (S, S), BG)
d = ImageDraw.Draw(img)

# ── the same ordered dither the site runs, frozen at t=0 ──
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
for gy in range(S // CELL + 1):
    for gx in range(S // CELL + 1):
        x, y = gx * CELL / S, gy * CELL / S
        v = math.sin(x * 2.1) * 0.5 + math.sin(y * 3.3) * 0.35 + math.sin((x + y) * 1.6) * 0.3
        fall = max(0.0, 1 - abs(x - 0.88) * 1.7) * max(0.0, 1 - y * 2.3)
        v = (v * 0.5 + 0.5) * fall * 0.78
        if v > (BAYER[(gy % 8) * 8 + (gx % 8)] + 0.5) / 64:
            a = min(0.34, 0.10 + v * 0.5)
            d.rectangle([gx * CELL, gy * CELL, gx * CELL + CELL - 2, gy * CELL + CELL - 2],
                        fill=(int(AC[0] * a), int(AC[1] * a), int(AC[2] * a)))

f_mark = ImageFont.truetype(MONO, 23)
f_hand = ImageFont.truetype(MONO, 17)
f_disp = ImageFont.truetype(SANS, 64, index=7)
f_lab = ImageFont.truetype(MONO, 14)
f_svc = ImageFont.truetype(MONO, 19)
f_note = ImageFont.truetype(MONO, 16)
f_foot = ImageFont.truetype(MONO, 18)
f_url = ImageFont.truetype(MONO, 21)

PAD = 84

# ── wordmark ──
x = PAD
d.text((x, 66), "[•]", font=f_mark, fill=AC)
x += d.textlength("[•]  ", font=f_mark)
d.text((x, 66), "Leon Kelvin Li", font=f_mark, fill=FG)
x += d.textlength("Leon Kelvin Li  ", font=f_mark)
d.text((x, 70), "/ Noctilucenty", font=f_hand, fill=FAINT)

# ── headline ──
d.text((PAD, 158), "i build the part of", font=f_disp, fill=DIM)
d.text((PAD, 228), "your business you", font=f_disp, fill=DIM)
d.text((PAD, 298), "still do by hand.", font=f_disp, fill=FG)

d.line([(PAD, 400), (PAD + 86, 400)], fill=AC, width=3)

# ── service table ──
d.text((PAD, 432), "W H A T   I   B U I L D   ·   S T A R T I N G   A T", font=f_lab, fill=FAINT)

COL_W = 466
COL_X = [PAD, PAD + COL_W + 100]
ROW_Y = 486
ROW_H = 70

for i, (name, price) in enumerate(SERVICES):
    cx = COL_X[i % 2]
    cy = ROW_Y + (i // 2) * ROW_H
    d.text((cx, cy), name, font=f_svc, fill=FG)
    d.text((cx + COL_W - d.textlength(price, font=f_svc), cy), price, font=f_svc, fill=AC)
    d.line([(cx, cy + 40), (cx + COL_W, cy + 40)], fill=LINE, width=1)

d.text((PAD, ROW_Y + 6 * ROW_H + 14),
       "every price is a floor — you get a fixed written quote before any work starts",
       font=f_note, fill=DIM)

# ── footer ──
d.line([(PAD, 1012), (S - PAD, 1012)], fill=LINE, width=1)
d.text((PAD, 1044), "free consultation  ·  hayward, ca  ·  remote anywhere",
       font=f_foot, fill=MID)
d.text((PAD, 1086), "leonkelvinli.onrender.com", font=f_url, fill=AC)

img.save(out, optimize=True)
print("wrote", out, img.size)
