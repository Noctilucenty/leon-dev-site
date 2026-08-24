#!/usr/bin/env python3
"""Build multilingual Facebook/classified image sets — one per language.

Why three images per listing instead of one crowded rate card:
  1. HOOK    — the thumbnail. It is the only thing most people ever see, so it
               asks the buyer's own problem back at them and names the next
               step ("message me"). No price wall.
  2. BUILD   — three outcomes, in their language, at a readable size.
  3. PROOF   — real Curio product art plus its public App Store URL.

Every string is written per language, not translated at render time — the
Portuguese and Chinese listings must read like a person wrote them.

Run from the repo root:  python3 tools/make_listing_images.py
Writes assets/listings/fb_<lang>_{1hook,2build,3proof}.png (1200x1200 each).
"""

import argparse
import io
import math
import os
import re
from PIL import Image, ImageDraw, ImageFont, ImageOps

S = 1200
BG = (0, 0, 0)
FG = (250, 250, 250)
MID = (170, 170, 170)
DIM = (119, 119, 119)
FAINT = (90, 90, 90)
AC = (155, 140, 255)
LINE = (34, 34, 34)

MONO = "/System/Library/Fonts/Menlo.ttc"
SANS = "/System/Library/Fonts/HelveticaNeue.ttc"      # index 7 = Light, upright
CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"    # body CJK
CJK_B = "/System/Library/Fonts/STHeiti Medium.ttc"    # headline CJK

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
outdir = os.path.join(root, "assets", "listings")
proof_image = os.path.join(outdir, "05_curio_appstore.png")
EXPECTED_DOMAIN = "leonbuilds.org"
CANONICAL_DOMAIN = EXPECTED_DOMAIN
RETIRED_DOMAIN = "leonkelvinli.onrender.com"
WORDMARK = ("[•]", "Leon Builds", "by Leon Kelvin Li")
PROOF_BADGE = "LIVE · APP STORE"

# ── copy, written per language (never machine-translated) ────────────────
L = {
    "en": {
        "hook": ["still taking orders", "by phone? still", "writing bookings", "in a notebook?"],
        "hook_a": "i turn that into software.",
        "anchor": "message me for a free workflow check",
        "cta": "message me — show me the slowest step",
        "outcomes_lab": "W H A T   G E T S   B E T T E R",
        "outcomes_note": "built around the way your business already works",
        "proof_lab": "P R O O F   Y O U   C A N   S E E",
        "proof_title": "curio — live on the app store",
        "proof_detail": "consumer iphone app · designed, built and shipped solo",
        "proof_url": "apps.apple.com/app/id6781121127",
        "foot": "free consultation  ·  working with businesses across the u.s.",
        "url": CANONICAL_DOMAIN,
        "outcomes": [
            ("orders come in without phone tag", "online ordering · booking · payments"),
            ("repeat questions answer themselves", "web · chat · phone automation"),
            ("busywork becomes one clear flow", "dashboards · tools · custom software"),
        ],
    },
    "pt": {
        "hook": ["ainda anota pedido", "no papel? ainda", "atende telefone", "o dia inteiro?"],
        "hook_a": "eu transformo isso em sistema.",
        "anchor": "me chama para uma análise grátis",
        "cta": "me chama — mostre a etapa que mais demora",
        "outcomes_lab": "O   Q U E   M E L H O R A",
        "outcomes_note": "feito para o jeito que seu negócio já funciona",
        "proof_lab": "P R O V A   Q U E   D Á   P A R A   V E R",
        "proof_title": "curio — disponível na app store",
        "proof_detail": "app para iphone · criado, desenvolvido e publicado por mim",
        "proof_url": "apps.apple.com/app/id6781121127",
        "foot": "consulta grátis  ·  atendo negócios em todos os estados unidos",
        "url": f"{CANONICAL_DOMAIN}/pt",
        "outcomes": [
            ("pedidos entram sem depender do telefone", "pedido online · agenda · pagamento"),
            ("perguntas repetidas se resolvem sozinhas", "site · chat · automação de telefone"),
            ("trabalho repetitivo vira um fluxo simples", "painéis · ferramentas · software sob medida"),
        ],
    },
    "es": {
        "hook": ["¿todavía tomas", "pedidos por teléfono?", "¿la agenda sigue", "en un cuaderno?"],
        "hook_a": "yo convierto eso en un sistema.",
        "anchor": "escríbeme para una revisión gratis",
        "cta": "escríbeme — muéstrame el paso más lento",
        "outcomes_lab": "L O   Q U E   M E J O R A",
        "outcomes_note": "hecho para la forma en que tu negocio ya trabaja",
        "proof_lab": "P R U E B A   Q U E   P U E D E S   V E R",
        "proof_title": "curio — disponible en la app store",
        "proof_detail": "app para iphone · diseñada, creada y publicada por mí",
        "proof_url": "apps.apple.com/app/id6781121127",
        "foot": "consulta gratis  ·  atiendo negocios en todo estados unidos",
        "url": f"{CANONICAL_DOMAIN}/es",
        "outcomes": [
            ("los pedidos llegan sin depender del teléfono", "pedidos · citas · pagos en línea"),
            ("las preguntas repetidas se responden solas", "web · chat · automatización telefónica"),
            ("el trabajo repetitivo se vuelve un flujo claro", "paneles · herramientas · software a medida"),
        ],
    },
    "zh": {
        "hook": ["还在用本子记单？", "还在整天接电话", "回答同样的问题？"],
        "hook_a": "我把这些变成系统。",
        "anchor": "发消息给我，免费帮你看看流程",
        "cta": "发消息给我 — 告诉我最慢的是哪一步",
        "outcomes_lab": "能 带 来 的 改 变",
        "outcomes_note": "按照你现在的生意流程来做，不让你从头适应",
        "proof_lab": "看 得 见 的 成 果",
        "proof_title": "Curio — 已上线 App Store",
        "proof_detail": "iPhone App · 由我独立设计、开发并上架",
        "proof_url": "apps.apple.com/app/id6781121127",
        "foot": "免费咨询  ·  全美国都接，线上做",
        "url": f"{CANONICAL_DOMAIN}/zh",
        "outcomes": [
            ("客户不用打电话也能下单预约", "网上点单 · 预约 · 收款"),
            ("重复问题可以自动回答", "网站 · 聊天 · 电话自动化"),
            ("重复工作变成一条清楚的流程", "数据看板 · 工具 · 定制软件"),
        ],
    },
}

BAYER = [
    0, 32, 8, 40, 2, 34, 10, 42, 48, 16, 56, 24, 50, 18, 58, 26,
    12, 44, 4, 36, 14, 46, 6, 38, 60, 28, 52, 20, 62, 30, 54, 22,
    3, 35, 11, 43, 1, 33, 9, 41, 51, 19, 59, 27, 49, 17, 57, 25,
    15, 47, 7, 39, 13, 45, 5, 37, 63, 31, 55, 23, 61, 29, 53, 21,
]
CELL = 6
PAD = 84


def fonts(lang):
    """Latin stays in the site's mono/sans; CJK uses faces with full glyph coverage."""
    cjk = lang == "zh"
    latin_args = {} if cjk else {"index": 7}
    headline_face = CJK_B if cjk else SANS
    body_face = CJK if cjk else MONO
    return {
        "mark": ImageFont.truetype(MONO, 23),
        "hand": ImageFont.truetype(MONO, 17),
        "disp": ImageFont.truetype(headline_face, 62 if cjk else 64, **latin_args),
        "lead": ImageFont.truetype(headline_face, 42 if cjk else 44, **latin_args),
        "outcome": ImageFont.truetype(headline_face, 38 if cjk else 38, **latin_args),
        "lab": ImageFont.truetype(body_face, 15 if cjk else 14),
        "body": ImageFont.truetype(body_face, 21 if cjk else 20),
        "note": ImageFont.truetype(body_face, 17 if cjk else 16),
        "foot": ImageFont.truetype(body_face, 18),
        "promise": ImageFont.truetype(headline_face, 50 if cjk else 52, **latin_args),
        "url": ImageFont.truetype(MONO, 25),
        "cta": ImageFont.truetype(body_face, 22 if cjk else 21),
    }


def _all_copy(value):
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
        raise ValueError(f"listing creative domain must be {EXPECTED_DOMAIN!r}, got {domain!r}")
    if RETIRED_DOMAIN.casefold() in joined_copy.casefold():
        raise ValueError(f"retired domain in listing creative copy: {RETIRED_DOMAIN}")


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
    """Keep classified art price-free, on-domain and limited to three outcomes."""
    joined = "\n".join(_all_copy((L, WORDMARK, PROOF_BADGE, CANONICAL_DOMAIN)))
    money = re.compile(r"(?:[$€£]\s*\d|\bUSD\s*\d)", re.IGNORECASE)
    match = money.search(joined)
    if match:
        raise ValueError(f"listing creative copy must be price-free: {match.group(0)!r}")
    validate_domain(CANONICAL_DOMAIN, joined)
    for lang, copy in L.items():
        if len(copy["outcomes"]) != 3:
            raise ValueError(f"{lang}: build card must contain exactly three outcomes")
        if copy["url"] != CANONICAL_DOMAIN and not copy["url"].startswith(f"{CANONICAL_DOMAIN}/"):
            raise ValueError(f"{lang}: non-canonical listing URL {copy['url']!r}")
    if not os.path.isfile(proof_image):
        raise FileNotFoundError(f"proof image is required: {proof_image}")


def checked_text(d, xy, value, *, font, fill, right=S - PAD, bottom=S - PAD):
    """Draw a string only when its actual glyph box stays in its intended bounds."""
    box = d.textbbox(xy, value, font=font)
    if box[0] < 0 or box[1] < 0 or box[2] > right or box[3] > bottom:
        raise ValueError(
            f"text overflow for {value!r}: bounds={box}, allowed right={right}, bottom={bottom}"
        )
    d.text(xy, value, font=font, fill=fill)


def checked_rect(rect, label):
    x0, y0, x1, y1 = rect
    if x0 < 0 or y0 < 0 or x1 > S or y1 > S or x1 <= x0 or y1 <= y0:
        raise ValueError(f"{label} outside card: {rect}")


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


def wordmark(d, f):
    x = PAD
    checked_text(d, (x, 66), WORDMARK[0], font=f["mark"], fill=AC)
    x += d.textlength(f"{WORDMARK[0]}  ", font=f["mark"])
    checked_text(d, (x, 66), WORDMARK[1], font=f["mark"], fill=FG)
    x += d.textlength(f"{WORDMARK[1]}  ", font=f["mark"])
    checked_text(d, (x, 70), WORDMARK[2], font=f["hand"], fill=FAINT)


def footer(d, f, c):
    d.line([(PAD, 1012), (S - PAD, 1012)], fill=LINE, width=1)
    checked_text(d, (PAD, 1040), c["foot"], font=f["foot"], fill=MID)
    checked_text(d, (PAD, 1082), c["url"], font=f["url"], fill=AC)


def hook(lang):
    """High-contrast thumbnail: problem, promise, next step, URL."""
    c, f = L[lang], fonts(lang)
    img, d = canvas()
    wordmark(d, f)

    y = 172
    for i, line in enumerate(c["hook"]):
        checked_text(
            d,
            (PAD, y),
            line,
            font=f["disp"],
            fill=AC if i == len(c["hook"]) - 1 else FG,
        )
        y += 78

    promise_box = (PAD, 548, S - PAD, 672)
    checked_rect(promise_box, "promise panel")
    d.rectangle(promise_box, fill=AC)
    checked_text(
        d,
        (PAD + 30, 578),
        c["hook_a"],
        font=f["promise"],
        fill=BG,
        right=S - PAD - 30,
        bottom=promise_box[3] - 16,
    )

    cta_box = (PAD, 748, S - PAD, 872)
    checked_rect(cta_box, "hook CTA")
    d.rectangle(cta_box, fill=(15, 15, 15), outline=FG, width=2)
    checked_text(
        d,
        (PAD + 30, 780),
        c["anchor"],
        font=f["lead"],
        fill=FG,
        right=S - PAD - 30,
        bottom=cta_box[3] - 16,
    )
    checked_text(d, (PAD, 924), c["url"], font=f["url"], fill=AC)
    return img


def outcomes(lang):
    """Three business outcomes, large enough to read in social previews."""
    c, f = L[lang], fonts(lang)
    img, d = canvas()
    wordmark(d, f)
    checked_text(d, (PAD, 168), c["outcomes_lab"], font=f["lab"], fill=FAINT)
    d.line([(PAD, 208), (PAD + 86, 208)], fill=AC, width=3)

    row_y = 264
    for i, (title, detail) in enumerate(c["outcomes"], start=1):
        checked_text(d, (PAD, row_y + 5), f"0{i}", font=f["body"], fill=AC)
        checked_text(d, (PAD + 68, row_y), title, font=f["outcome"], fill=FG)
        checked_text(d, (PAD + 68, row_y + 58), detail, font=f["body"], fill=MID)
        d.line([(PAD + 68, row_y + 112), (S - PAD, row_y + 112)], fill=LINE, width=1)
        row_y += 166

    checked_text(d, (PAD, 774), c["outcomes_note"], font=f["note"], fill=MID)
    cta_box = (PAD, 826, S - PAD, 934)
    checked_rect(cta_box, "outcomes CTA")
    d.rectangle(cta_box, outline=AC, width=2)
    checked_text(
        d,
        (PAD + 30, 858),
        c["cta"],
        font=f["cta"],
        fill=AC,
        right=S - PAD - 30,
        bottom=cta_box[3] - 16,
    )
    footer(d, f, c)
    return img


def proof(lang):
    """Use the real Curio product art and its public App Store URL as proof."""
    c, f = L[lang], fonts(lang)
    img, d = canvas()
    wordmark(d, f)
    checked_text(d, (PAD, 158), c["proof_lab"], font=f["lab"], fill=FAINT)
    d.line([(PAD, 198), (PAD + 86, 198)], fill=AC, width=3)
    checked_text(d, (PAD, 216), c["proof_title"], font=f["lead"], fill=FG)

    image_rect = (PAD, 280, S - PAD, 782)
    checked_rect(image_rect, "proof image")
    source = Image.open(proof_image).convert("RGB")
    product = ImageOps.fit(
        source,
        (image_rect[2] - image_rect[0], image_rect[3] - image_rect[1]),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.24),
    )
    img.paste(product, (image_rect[0], image_rect[1]))
    d.rectangle(image_rect, outline=AC, width=2)

    badge = (PAD + 20, image_rect[1] + 20, PAD + 340, image_rect[1] + 72)
    checked_rect(badge, "App Store badge")
    d.rectangle(badge, fill=BG, outline=AC, width=2)
    checked_text(
        d,
        (badge[0] + 16, badge[1] + 14),
        PROOF_BADGE,
        font=f["note"],
        fill=AC,
        right=badge[2] - 12,
        bottom=badge[3] - 6,
    )

    checked_text(d, (PAD, 814), c["proof_detail"], font=f["body"], fill=FG)
    checked_text(d, (PAD, 860), c["proof_url"], font=f["url"], fill=AC)
    checked_text(d, (PAD, 918), c["cta"], font=f["cta"], fill=MID)
    footer(d, f, c)
    return img


def png_bytes(image):
    payload = io.BytesIO()
    image.save(payload, "PNG", optimize=True)
    return payload.getvalue()


def main(check=False):
    regression_check_domain_guard()
    validate_copy()
    os.makedirs(outdir, exist_ok=True)
    stale = []
    for lang in L:
        for name, fn in (("1hook", hook), ("2build", outcomes), ("3proof", proof)):
            path = os.path.join(outdir, f"fb_{lang}_{name}.png")
            image = fn(lang)
            if image.size != (S, S):
                raise ValueError(f"unexpected listing card size for {path}: {image.size}")
            image = image.quantize(colors=256, method=Image.MEDIANCUT)
            expected = png_bytes(image)
            if check:
                if not os.path.exists(path):
                    stale.append(f"missing {os.path.relpath(path, root)}")
                else:
                    with open(path, "rb") as existing:
                        if existing.read() != expected:
                            stale.append(f"stale {os.path.relpath(path, root)}")
            else:
                with open(path, "wb") as output:
                    output.write(expected)
                print("wrote", os.path.relpath(path, root), len(expected) // 1024, "KB")
    if stale:
        for message in stale:
            print(message)
        print("run: python3 tools/make_listing_images.py")
        return 1
    if check:
        print("listing assets match canonical generator")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if committed PNGs differ from a fresh render")
    args = parser.parse_args()
    raise SystemExit(main(check=args.check))
