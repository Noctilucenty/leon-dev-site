#!/usr/bin/env python3
"""Build the price-free organic and paid-social cards in ``assets/social/``.

The cards deliberately sell outcomes, process and proof instead of publishing
a rate card. This file is the canonical source for every export, including the
proof and campaign cards; do not hand-edit the PNGs.

Run from the repo root: python3 tools/make_social.py
"""

import argparse
import io
import math
import os
import re

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
EXPECTED_DOMAIN = "leonbuilds.org"
CANONICAL_DOMAIN = EXPECTED_DOMAIN
RETIRED_DOMAIN = "leonkelvinli.onrender.com"
FOOTER_TAGLINE = "remote  ·  businesses across the u.s."

# Output filenames stay stable because they may already be referenced by
# drafts. Their content is evergreen and intentionally contains no rates.
# The ``ad_*`` set gives the first paid test six genuinely different angles;
# none claims a result that requires access to a prospect's private data.
CARDS = {
    "ig_01_prices.png": {
        "label": "leon --outcomes",
        "headline": ("less manual work.", "more room to run", "your business."),
        "rows": (
            ("take orders while you sleep", "online ordering · payments"),
            ("let customers book themselves", "booking · reminders · follow-up"),
            ("stop copying data by hand", "automation · dashboards"),
        ),
        "note": "show me the step that wastes the most time.",
    },
    "ig_02_pricing.png": {
        "label": "leon --process",
        "headline": ("a clear path from", "bottleneck to launch."),
        "rows": (
            ("01  show me the bottleneck", "a short call or message is enough to start"),
            ("02  get a written plan", "scope, timeline and handoff agreed before work starts"),
            ("03  launch with a clean handoff", "agreed accounts · included source · setup notes"),
        ),
        "note": "one developer from first conversation through launch.",
    },
    "ig_03_work.png": {
        "label": "leon --proof",
        "headline": ("proof,", "not promises."),
        "rows": (
            ("curio", "consumer iPhone app · live on the App Store"),
            ("multi-brand ordering", "one kitchen · several brands · one cart routes orders"),
            ("review desk", "reads business reviews · drafts owner replies"),
        ),
        "note": "live product + public demos · built and shipped by one developer",
    },
    "ad_01_contractor_after_hours.png": {
        "label": "leon --missed-leads",
        "headline": ("a quote request", "came in at 8:47pm.", "what happens next?"),
        "rows": (
            ("reply right away", "confirm the request without waiting for office hours"),
            ("book the next step", "give the customer one clear action to take"),
            ("keep one owner pipeline", "see what is new · waiting · booked · won"),
        ),
        "note": "free 15-minute lead leak review · no sales team",
    },
    "ad_02_contractor_flow.png": {
        "label": "leon --lead-flow",
        "headline": ("from new inquiry", "to booked estimate", "without phone tag."),
        "rows": (
            ("01  mobile quote flow", "ask only for what the estimator needs"),
            ("02  instant confirmation", "set a real expectation while interest is high"),
            ("03  visible follow-up", "give the owner one place to close the loop"),
        ),
        "note": "built for owner-run home service businesses",
    },
    "ad_03_auto_estimates.png": {
        "label": "leon --repair-flow",
        "headline": ("the customer wants", "an estimate.", "voicemail is not a flow."),
        "rows": (
            ("capture the request", "vehicle · problem · preferred time · contact"),
            ("confirm what happens next", "reduce repeat calls and uncertain waiting"),
            ("move work through stages", "new · inspecting · approved · ready"),
        ),
        "note": "start with the smallest useful repair-shop workflow",
    },
    "ad_04_restaurant_direct.png": {
        "label": "leon --direct-orders",
        "headline": ("the phone is busy", "during dinner.", "orders can keep moving."),
        "rows": (
            ("let guests order direct", "a mobile flow that matches the real menu"),
            ("route each ticket clearly", "send the kitchen the details it actually needs"),
            ("keep the handoff visible", "payment and delivery vendors keep their terms"),
        ),
        "note": "ordering systems shaped around the operation",
    },
    "ad_05_founder_direct.png": {
        "label": "leon --one-developer",
        "headline": ("you talk to", "the developer who", "writes the code."),
        "rows": (
            ("show the bottleneck", "a call, photo or rough explanation is enough"),
            ("get a written scope", "price · timeline · limits · handoff before work"),
            ("watch the build work", "review real milestones instead of slide decks"),
        ),
        "note": "direct from first conversation through handoff",
    },
    "ad_06_lead_leak_review.png": {
        "label": "leon --free-review",
        "headline": ("where do inquiries", "get stuck after", "they reach you?"),
        "rows": (
            ("bring one real workflow", "calls · forms · texts · spreadsheets · booking"),
            ("find the weak handoff", "focus on one observable point of friction"),
            ("leave with a next step", "keep the current tools when they are good enough"),
        ),
        "note": "free 15-minute review · smallest sensible fix first",
    },
}

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


def _all_copy(value):
    """Yield every copy string so safety checks cannot miss a nested row."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _all_copy(child)
    else:
        for child in value:
            yield from _all_copy(child)


def validate_domain(domain, joined_copy):
    if domain != EXPECTED_DOMAIN:
        raise ValueError(f"social creative domain must be {EXPECTED_DOMAIN!r}, got {domain!r}")
    if RETIRED_DOMAIN.casefold() in joined_copy.casefold():
        raise ValueError(f"retired domain in social creative copy: {RETIRED_DOMAIN}")


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
    """Refuse to render money figures or a retired domain into social art."""
    joined = "\n".join(_all_copy((CARDS, FOOTER_TAGLINE, CANONICAL_DOMAIN)))
    money = re.compile(r"(?:[$€£]\s*\d|\bUSD\s*\d)", re.IGNORECASE)
    match = money.search(joined)
    if match:
        raise ValueError(f"social creative copy must be price-free: {match.group(0)!r}")
    validate_domain(CANONICAL_DOMAIN, joined)


def checked_text(d, xy, value, *, font, fill, right=W - PAD, bottom=H - PAD):
    """Draw text only when its actual glyph bounds stay inside the card."""
    box = d.textbbox(xy, value, font=font)
    if box[0] < 0 or box[1] < 0 or box[2] > right or box[3] > bottom:
        raise ValueError(
            f"text overflow for {value!r}: bounds={box}, allowed right={right}, bottom={bottom}"
        )
    d.text(xy, value, font=font, fill=fill)


def dither(d):
    """The site's ordered dither, frozen at t=0, falling off top-right."""
    for gy in range(H // CELL + 1):
        for gx in range(W // CELL + 1):
            x, y = gx * CELL / W, gy * CELL / H
            v = math.sin(x * 2.1) * 0.5 + math.sin(y * 3.3) * 0.35 + math.sin((x + y) * 1.6) * 0.3
            fall = max(0.0, 1 - abs(x - 0.88) * 1.7) * max(0.0, 1 - y * 2.6)
            v = (v * 0.5 + 0.5) * fall * 0.78
            if v > (BAYER[(gy % 8) * 8 + (gx % 8)] + 0.5) / 64:
                a = min(0.34, 0.10 + v * 0.5)
                d.rectangle(
                    [gx * CELL, gy * CELL, gx * CELL + CELL - 2, gy * CELL + CELL - 2],
                    fill=(int(AC[0] * a), int(AC[1] * a), int(AC[2] * a)),
                )


def canvas():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    dither(d)
    return img, d


def footer(d):
    d.line([(PAD, H - 190), (W - PAD, H - 190)], fill=LINE, width=1)
    checked_text(
        d,
        (PAD, H - 155),
        FOOTER_TAGLINE,
        font=ImageFont.truetype(MONO, 22),
        fill=MID,
    )
    checked_text(
        d,
        (PAD, H - 120),
        CANONICAL_DOMAIN,
        font=ImageFont.truetype(MONO, 26),
        fill=AC,
    )


def build_card(card):
    img, d = canvas()
    f_label = ImageFont.truetype(MONO, 22)
    f_display = ImageFont.truetype(MONO, 54)
    f_title = ImageFont.truetype(MONO, 30)
    f_body = ImageFont.truetype(MONO, 21)
    f_note = ImageFont.truetype(MONO, 21)

    checked_text(d, (PAD, 196), card["label"], font=f_label, fill=FAINT)
    for i, line in enumerate(card["headline"]):
        checked_text(
            d,
            (PAD, 266 + i * 76),
            line,
            font=f_display,
            fill=FG if i == len(card["headline"]) - 1 else DIM,
        )

    divider_y = 282 + len(card["headline"]) * 76
    d.line([(PAD, divider_y), (PAD + 130, divider_y)], fill=AC, width=5)

    y = divider_y + 66
    for title, body in card["rows"]:
        checked_text(d, (PAD, y), title, font=f_title, fill=FG)
        checked_text(d, (PAD, y + 47), body, font=f_body, fill=MID)
        d.line([(PAD, y + 92), (W - PAD, y + 92)], fill=LINE, width=1)
        y += 126

    checked_text(d, (PAD, y + 14), card["note"], font=f_note, fill=AC)
    footer(d)
    return img


def png_bytes(image):
    payload = io.BytesIO()
    image.save(payload, "PNG", optimize=True)
    return payload.getvalue()


def main(check=False):
    regression_check_domain_guard()
    validate_copy()
    os.makedirs(OUT, exist_ok=True)
    stale = []
    for name, card in CARDS.items():
        image = build_card(card)
        if image.size != (W, H):
            raise ValueError(f"unexpected social card size for {name}: {image.size}")
        path = os.path.join(OUT, name)
        expected = png_bytes(image)
        if check:
            if not os.path.exists(path):
                stale.append(f"missing {path}")
            else:
                with open(path, "rb") as existing:
                    if existing.read() != expected:
                        stale.append(f"stale {path}")
        else:
            with open(path, "wb") as output:
                output.write(expected)
            print("wrote", path, image.size)
    if stale:
        for message in stale:
            print(message)
        print("run: python3 tools/make_social.py")
        return 1
    if check:
        print("social assets match canonical generator")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if committed PNGs differ from a fresh render")
    args = parser.parse_args()
    raise SystemExit(main(check=args.check))
