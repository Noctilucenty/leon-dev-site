#!/usr/bin/env python3
"""Build the Instagram-portrait cards in assets/social/ from the same palette,
dither and type as tools/make_fb.py — so the listing image, the social cards and
the site all read as one thing.

  ig_01_prices.png   six headline floors, 1080x1350
  ig_02_pricing.png  the three ways to work together, 1080x1350

These used to be one-off exports, which is how they ended up months out of date
with the site's prices. Prices live in PRICES/TIERS below; change them here and
rerun, the same way facebook.png works.

Run from the repo root:  python3 tools/make_social.py
"""

import math
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
BG = (0, 0, 0)
FG = (250, 250, 250)
MID = (170, 170, 170)
DIM = (119, 119, 119)
FAINT = (90, 90, 90)
AC = (155, 140, 255)
LINE = (34, 34, 34)

MONO = "/System/Library/Fonts/Menlo.ttc"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "social")

# keep in step with index.html, tools/build_pages.py and tools/make_fb.py
PRICES = [
    ("business websites",     "$1,200+"),
    ("booking & ordering",    "$600+"),
    ("ios & android apps",    "$4,500+"),
    ("ai chatbots",           "$1,000+"),
    ("ai phone agents",       "$1,200+"),
    ("workflow automation",   "$600+"),
]

TIERS = [
    ("small fixes",   "$49+",     "the broken thing, the one integration — a day, not a month"),
    ("fixed project", "$400+",    "one clear thing, built and handed over"),
    ("full build",    "$3,500+",  "an app or a whole system, end to end"),
    ("ongoing",       "$450/mo",  "you need a developer, not a project"),
]

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


def dither(d):
    """The site's ordered dither, frozen at t=0, falling off from the top right."""
    for gy in range(H // CELL + 1):
        for gx in range(W // CELL + 1):
            x, y = gx * CELL / W, gy * CELL / H
            v = math.sin(x * 2.1) * 0.5 + math.sin(y * 3.3) * 0.35 + math.sin((x + y) * 1.6) * 0.3
            fall = max(0.0, 1 - abs(x - 0.88) * 1.7) * max(0.0, 1 - y * 2.6)
            v = (v * 0.5 + 0.5) * fall * 0.78
            if v > (BAYER[(gy % 8) * 8 + (gx % 8)] + 0.5) / 64:
                a = min(0.34, 0.10 + v * 0.5)
                d.rectangle([gx * CELL, gy * CELL, gx * CELL + CELL - 2, gy * CELL + CELL - 2],
                            fill=(int(AC[0] * a), int(AC[1] * a), int(AC[2] * a)))


def canvas():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    dither(d)
    return img, d


def footer(d):
    d.line([(PAD, H - 190), (W - PAD, H - 190)], fill=LINE, width=1)
    d.text((PAD, H - 155), "remote  ·  businesses across the u.s.",
           font=ImageFont.truetype(MONO, 22), fill=MID)
    d.text((PAD, H - 110), "leonbuilds.org",
           font=ImageFont.truetype(MONO, 26), fill=AC)


PAD = 84


def card_prices():
    img, d = canvas()
    f_lab = ImageFont.truetype(MONO, 22)
    f_disp = ImageFont.truetype(MONO, 54)
    f_row = ImageFont.truetype(MONO, 30)

    d.text((PAD, 200), "leon --help", font=f_lab, fill=FAINT)
    for i, line in enumerate(["i build the part of", "your business you", "still do by hand."]):
        d.text((PAD, 270 + i * 82), line, font=f_disp, fill=FG if i == 2 else DIM)
    d.line([(PAD, 520), (PAD + 130, 520)], fill=AC, width=5)

    y = 580
    for name, price in PRICES:
        d.text((PAD, y), name, font=f_row, fill=FG)
        d.text((W - PAD - d.textlength(price, font=f_row), y), price, font=f_row, fill=AC)
        d.line([(PAD, y + 52), (W - PAD, y + 52)], fill=LINE, width=1)
        y += 76

    d.text((PAD, y + 24), "floors, not quotes — fixed price agreed in writing first",
           font=ImageFont.truetype(MONO, 21), fill=DIM)
    footer(d)
    return img


def card_tiers():
    img, d = canvas()
    f_lab = ImageFont.truetype(MONO, 22)
    f_disp = ImageFont.truetype(MONO, 54)
    f_name = ImageFont.truetype(MONO, 32)
    f_amt = ImageFont.truetype(MONO, 32)
    f_for = ImageFont.truetype(MONO, 20)

    d.text((PAD, 200), "leon --price", font=f_lab, fill=FAINT)
    for i, line in enumerate(["three ways to", "work together."]):
        d.text((PAD, 270 + i * 82), line, font=f_disp, fill=FG if i == 1 else DIM)
    d.line([(PAD, 440), (PAD + 130, 440)], fill=AC, width=5)

    y = 520
    for name, amt, blurb in TIERS:
        d.text((PAD, y), name, font=f_name, fill=FG)
        d.text((W - PAD - d.textlength(amt, font=f_amt), y), amt, font=f_amt, fill=AC)
        d.text((PAD, y + 46), blurb, font=f_for, fill=DIM)
        d.line([(PAD, y + 96), (W - PAD, y + 96)], fill=LINE, width=1)
        y += 128

    d.text((PAD, y + 16), "price follows scope, not hours. no hourly billing, no surprises.",
           font=ImageFont.truetype(MONO, 21), fill=DIM)
    footer(d)
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, img in [("ig_01_prices.png", card_prices()), ("ig_02_pricing.png", card_tiers())]:
        p = os.path.join(OUT, name)
        img.save(p, "PNG", optimize=True)
        print("wrote", p, img.size)


if __name__ == "__main__":
    main()
