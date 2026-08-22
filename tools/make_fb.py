#!/usr/bin/env python3
"""Build assets/facebook.png — the 1200x1200 Facebook/classified image.

Square on purpose so it survives feed, group and directory thumbnail crops.
The card stays evergreen: three business outcomes, no service catalog and no
published rates. Same palette and dither as the site.

Run from the repo root:  python3 tools/make_fb.py
"""

import argparse
import io
import math
import os
import re
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
EXPECTED_DOMAIN = "leonbuilds.org"
CANONICAL_DOMAIN = EXPECTED_DOMAIN
RETIRED_DOMAIN = "leonkelvinli.onrender.com"
WORDMARK = ("[•]", "Leon Kelvin Li", "/ Noctilucenty")
OUTCOMES_LABEL = "W H A T   G E T S   B E T T E R"

OUTCOMES = [
    ("take orders without phone tag", "online ordering · booking · payments"),
    ("answer repeat questions automatically", "web · chat · phone workflows"),
    ("turn busywork into one clear flow", "automation · dashboards · custom tools"),
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
PAD = 84

HEADLINE = ("i build the part of", "your business you", "still do by hand.")
NOTE = "built around the way your business already works"
CTA = "message me — show me the step that wastes the most time"
FOOT = "remote  ·  working with businesses across the u.s."


def checked_text(d, xy, value, *, font, fill, right=S - PAD, bottom=S - PAD):
    """Fail instead of silently drawing copy outside the square."""
    box = d.textbbox(xy, value, font=font)
    if box[0] < 0 or box[1] < 0 or box[2] > right or box[3] > bottom:
        raise ValueError(
            f"text overflow for {value!r}: bounds={box}, allowed right={right}, bottom={bottom}"
        )
    d.text(xy, value, font=font, fill=fill)


def validate_domain(domain, joined_copy):
    if domain != EXPECTED_DOMAIN:
        raise ValueError(f"facebook creative domain must be {EXPECTED_DOMAIN!r}, got {domain!r}")
    if RETIRED_DOMAIN.casefold() in joined_copy.casefold():
        raise ValueError(f"retired domain in facebook creative copy: {RETIRED_DOMAIN}")


def regression_check_domain_guard():
    """Exercise both failure modes so the safety guard cannot become decorative."""
    unsafe_cases = (
        (RETIRED_DOMAIN, "safe copy"),
        (EXPECTED_DOMAIN, f"visit {RETIRED_DOMAIN}"),
    )
    for domain, copy in unsafe_cases:
        try:
            validate_domain(domain, copy)
        except ValueError:
            continue
        raise AssertionError(f"domain guard accepted unsafe case: {domain!r}, {copy!r}")


def validate_copy():
    strings = [*WORDMARK, *HEADLINE, OUTCOMES_LABEL, NOTE, CTA, FOOT, CANONICAL_DOMAIN]
    for title, detail in OUTCOMES:
        strings.extend((title, detail))
    joined = "\n".join(strings)
    match = re.search(r"(?:[$€£]\s*\d|\bUSD\s*\d)", joined, re.IGNORECASE)
    if match:
        raise ValueError(f"facebook creative must be price-free: {match.group(0)!r}")
    validate_domain(CANONICAL_DOMAIN, joined)
    if len(OUTCOMES) != 3:
        raise ValueError("facebook creative must contain exactly three outcomes")


def canvas():
    img = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(img)
    for gy in range(S // CELL + 1):
        for gx in range(S // CELL + 1):
            x, y = gx * CELL / S, gy * CELL / S
            v = math.sin(x * 2.1) * 0.5 + math.sin(y * 3.3) * 0.35 + math.sin((x + y) * 1.6) * 0.3
            fall = max(0.0, 1 - abs(x - 0.88) * 1.7) * max(0.0, 1 - y * 2.3)
            v = (v * 0.5 + 0.5) * fall * 0.78
            if v > (BAYER[(gy % 8) * 8 + (gx % 8)] + 0.5) / 64:
                a = min(0.34, 0.10 + v * 0.5)
                d.rectangle(
                    [gx * CELL, gy * CELL, gx * CELL + CELL - 2, gy * CELL + CELL - 2],
                    fill=(int(AC[0] * a), int(AC[1] * a), int(AC[2] * a)),
                )
    return img, d


def build():
    validate_copy()
    img, d = canvas()
    f_mark = ImageFont.truetype(MONO, 23)
    f_hand = ImageFont.truetype(MONO, 17)
    f_display = ImageFont.truetype(SANS, 64, index=7)
    f_label = ImageFont.truetype(MONO, 14)
    f_outcome = ImageFont.truetype(SANS, 38, index=7)
    f_body = ImageFont.truetype(MONO, 20)
    f_note = ImageFont.truetype(MONO, 16)
    f_foot = ImageFont.truetype(MONO, 18)
    f_url = ImageFont.truetype(MONO, 25)

    x = PAD
    checked_text(d, (x, 66), WORDMARK[0], font=f_mark, fill=AC)
    x += d.textlength(f"{WORDMARK[0]}  ", font=f_mark)
    checked_text(d, (x, 66), WORDMARK[1], font=f_mark, fill=FG)
    x += d.textlength(f"{WORDMARK[1]}  ", font=f_mark)
    checked_text(d, (x, 70), WORDMARK[2], font=f_hand, fill=FAINT)

    for i, line in enumerate(HEADLINE):
        checked_text(
            d,
            (PAD, 154 + i * 70),
            line,
            font=f_display,
            fill=AC if i == len(HEADLINE) - 1 else FG,
        )
    d.line([(PAD, 382), (PAD + 86, 382)], fill=AC, width=3)
    checked_text(d, (PAD, 412), OUTCOMES_LABEL, font=f_label, fill=FAINT)

    row_y = 468
    for i, (title, detail) in enumerate(OUTCOMES, start=1):
        checked_text(d, (PAD, row_y + 4), f"0{i}", font=f_body, fill=AC)
        checked_text(d, (PAD + 68, row_y), title, font=f_outcome, fill=FG)
        checked_text(d, (PAD + 68, row_y + 56), detail, font=f_body, fill=MID)
        d.line([(PAD + 68, row_y + 106), (S - PAD, row_y + 106)], fill=LINE, width=1)
        row_y += 132

    checked_text(d, (PAD, 874), NOTE, font=f_note, fill=MID)
    cta_box = (PAD, 918, S - PAD, 998)
    d.rectangle(cta_box, outline=AC, width=2)
    checked_text(
        d,
        (PAD + 24, 942),
        CTA,
        font=f_body,
        fill=AC,
        right=S - PAD - 24,
        bottom=cta_box[3] - 10,
    )

    d.line([(PAD, 1032), (S - PAD, 1032)], fill=LINE, width=1)
    checked_text(d, (PAD, 1058), FOOT, font=f_foot, fill=MID)
    checked_text(d, (PAD, 1084), CANONICAL_DOMAIN, font=f_url, fill=AC)
    return img


def png_bytes(image):
    payload = io.BytesIO()
    image.save(payload, "PNG", optimize=True)
    return payload.getvalue()


def main(check=False):
    regression_check_domain_guard()
    image = build()
    if image.size != (S, S):
        raise ValueError(f"unexpected facebook card size: {image.size}")
    expected = png_bytes(image)
    if check:
        if not os.path.exists(out):
            print("missing", out)
            print("run: python3 tools/make_fb.py")
            return 1
        with open(out, "rb") as existing:
            if existing.read() != expected:
                print("stale", out)
                print("run: python3 tools/make_fb.py")
                return 1
        print("facebook asset matches canonical generator")
        return 0
    with open(out, "wb") as output:
        output.write(expected)
    print("wrote", out, image.size)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if committed PNG differs from a fresh render")
    args = parser.parse_args()
    raise SystemExit(main(check=args.check))
