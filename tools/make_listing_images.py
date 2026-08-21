#!/usr/bin/env python3
"""Build the Marketplace listing image sets — one per language.

Why three images per listing instead of one price table:
  1. HOOK    — the thumbnail. It is the only thing most people ever see, so it
               asks the buyer's own problem back at them and names the next
               step ("message me"). No price wall.
  2. BUILD   — what he makes, in their language. No figures: price comes
               after a conversation, in writing.
  3. PROOF   — the systems that are actually running.

Every string is written per language, not translated at render time — the
Portuguese and Chinese listings must read like a person wrote them.

Run from the repo root:  python3 tools/make_listing_images.py
Writes assets/listings/fb_<lang>_{1hook,2build,3proof}.png (1200x1200 each).
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
SANS = "/System/Library/Fonts/HelveticaNeue.ttc"      # index 7 = Light, upright
CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"    # body CJK
CJK_B = "/System/Library/Fonts/STHeiti Medium.ttc"    # headline CJK

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
outdir = os.path.join(root, "assets", "listings")

# ── copy, written per language (never machine-translated) ────────────────
L = {
    "en": {
        "hook": ["still taking orders", "by phone? still", "writing bookings", "in a notebook?"],
        "hook_a": "i turn that into software.",
        "hook_b": "websites · online ordering · booking · apps · automation",
        "anchor": "free look at what you have now",
        "cta": "message me — i'll look at what you have now, free",
        "prices_lab": "W H A T   I   B U I L D",
        "prices_note": "you get a fixed written price before any work starts, and it does not change after",
        "proof_lab": "T H I N G S   T H A T   A R E   A C T U A L L Y   R U N N I N G",
        "proof": [
            ("an iphone app", "on the app store today"),
            ("an online ordering system", "one kitchen, several brands — one cart splits itself per brand"),
            ("a review tool", "reads the reviews a business gets and writes the replies"),
        ],
        "proof_note": "i speak english, chinese, portuguese and spanish",
        "foot": "free consultation  ·  working with businesses across the u.s.",
        "url": "leonbuilds.org",
        "services": [
            ("small fixes", ""), ("workflow automation", ""),
            ("booking & ordering", ""), ("dashboards & tools", ""),
            ("ai chatbots", ""), ("business websites", ""),
            ("ai phone agents", ""), ("crm & inventory", ""),
            ("online ordering", ""), ("customer portals", ""),
            ("custom software", ""), ("ios & android apps", ""),
        ],
    },
    "pt": {
        "hook": ["ainda anota pedido", "no papel? ainda", "atende telefone", "o dia inteiro?"],
        "hook_a": "eu transformo isso em sistema.",
        "hook_b": "site · pedido online · agendamento · aplicativo · automação",
        "anchor": "eu olho o que você tem hoje, de graça",
        "cta": "me manda mensagem — eu olho o que você tem hoje, de graça",
        "prices_lab": "O   Q U E   E U   F A Ç O",
        "prices_note": "você recebe o preço fechado por escrito antes de eu começar, e ele não muda depois",
        "proof_lab": "C O I S A S   Q U E   E S T Ã O   R O D A N D O   D E   V E R D A D E",
        "proof": [
            ("um aplicativo de iphone", "está na app store hoje"),
            ("um sistema de pedido online", "uma cozinha, várias marcas — o carrinho se divide sozinho por marca"),
            ("uma ferramenta de avaliações", "lê as avaliações do negócio e já escreve a resposta"),
        ],
        "proof_note": "falo português, inglês, chinês e espanhol",
        "foot": "consulta grátis  ·  atendo os estados unidos inteiros",
        "url": "leonbuilds.org/pt",
        "services": [
            ("consertos pequenos", ""), ("automação de tarefas", ""),
            ("agendamento e pedidos", ""), ("painéis e ferramentas", ""),
            ("robô de atendimento", ""), ("site do negócio", ""),
            ("atendente de telefone ia", ""), ("crm e estoque", ""),
            ("pedido online", ""), ("portal do cliente", ""),
            ("software sob medida", ""), ("aplicativo ios e android", ""),
        ],
    },
    "es": {
        "hook": ["¿todavía tomas", "pedidos por teléfono?", "¿la agenda sigue", "en un cuaderno?"],
        "hook_a": "yo convierto eso en un sistema.",
        "hook_b": "página web · pedidos en línea · citas · aplicación · automatización",
        "anchor": "reviso gratis lo que ya tienes",
        "cta": "escríbeme — reviso gratis lo que ya tienes",
        "prices_lab": "L O   Q U E   H A G O",
        "prices_note": "te doy el precio cerrado por escrito antes de empezar, y no cambia al final",
        "proof_lab": "C O S A S   Q U E   E S T Á N   F U N C I O N A N D O   D E   V E R D A D",
        "proof": [
            ("una aplicación de iphone", "está en la app store hoy"),
            ("un sistema de pedidos en línea", "una cocina, varias marcas — el carrito se separa solo por marca"),
            ("una herramienta de reseñas", "lee las reseñas del negocio y escribe la respuesta"),
        ],
        "proof_note": "hablo español, inglés, portugués y chino",
        "foot": "consulta gratis  ·  atiendo negocios en todo estados unidos",
        "url": "leonbuilds.org/es",
        "services": [
            ("arreglos pequeños", ""), ("automatización de tareas", ""),
            ("citas y pedidos", ""), ("paneles y herramientas", ""),
            ("bot de atención", ""), ("página del negocio", ""),
            ("contestador con ia", ""), ("crm e inventario", ""),
            ("pedidos en línea", ""), ("portal del cliente", ""),
            ("software a la medida", ""), ("aplicación ios y android", ""),
        ],
    },
    "zh": {
        "hook": ["还在用本子记单？", "还在整天接电话", "回答同样的问题？"],
        "hook_a": "我把这些变成系统。",
        "hook_b": "网站 · 网上点单 · 预约系统 · 手机 App · 自动化",
        "anchor": "先免费看看你现在的东西",
        "cta": "发消息给我 — 我先免费看看你现在的东西",
        "prices_lab": "我 能 做 什 么",
        "prices_note": "开工前先把价钱白纸黑字写下来，做完不会变",
        "proof_lab": "已 经 在 跑 的 东 西",
        "proof": [
            ("一个 iPhone App", "现在就在 App Store 上"),
            ("一个网上点单系统", "同一个厨房跑好几个牌子，一个购物车自动分单"),
            ("一个评论工具", "自动读客人的评论，并且写好回复"),
        ],
        "proof_note": "中文、英文、葡萄牙文、西班牙文都可以说",
        "foot": "免费咨询  ·  全美国都接，线上做",
        "url": "leonbuilds.org/zh",
        "services": [
            ("小修小改", ""), ("流程自动化", ""),
            ("预约和点单", ""), ("数据看板", ""),
            ("智能客服机器人", ""), ("公司网站", ""),
            ("AI 电话客服", ""), ("客户管理和库存", ""),
            ("网上点单系统", ""), ("客户专属后台", ""),
            ("定制软件", ""), ("iOS 和安卓 App", ""),
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
    """Latin stays in the site's mono/sans; CJK swaps in a face that has the glyphs."""
    cjk = lang == "zh"
    return {
        "mark": ImageFont.truetype(MONO, 23),
        "hand": ImageFont.truetype(MONO, 17),
        "disp": ImageFont.truetype(CJK_B if cjk else SANS, 62 if cjk else 64,
                                   **({} if cjk else {"index": 7})),
        "lead": ImageFont.truetype(CJK_B if cjk else SANS, 44 if cjk else 46,
                                   **({} if cjk else {"index": 7})),
        "lab": ImageFont.truetype(CJK if cjk else MONO, 15 if cjk else 14),
        "svc": ImageFont.truetype(CJK if cjk else MONO, 21 if cjk else 19),
        "price": ImageFont.truetype(MONO, 19),
        "body": ImageFont.truetype(CJK if cjk else MONO, 21 if cjk else 20),
        "note": ImageFont.truetype(CJK if cjk else MONO, 17 if cjk else 16),
        "foot": ImageFont.truetype(CJK if cjk else MONO, 18 if cjk else 18),
        "url": ImageFont.truetype(MONO, 21),
        "cta": ImageFont.truetype(CJK if cjk else MONO, 22 if cjk else 21),
    }


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
                d.rectangle([gx * CELL, gy * CELL, gx * CELL + CELL - 2, gy * CELL + CELL - 2],
                            fill=(int(AC[0] * a), int(AC[1] * a), int(AC[2] * a)))
    return img, d


def wordmark(d, f):
    x = PAD
    d.text((x, 66), "[•]", font=f["mark"], fill=AC)
    x += d.textlength("[•]  ", font=f["mark"])
    d.text((x, 66), "Leon Kelvin Li", font=f["mark"], fill=FG)
    x += d.textlength("Leon Kelvin Li  ", font=f["mark"])
    d.text((x, 70), "/ Noctilucenty", font=f["hand"], fill=FAINT)


def footer(d, f, c, cta=None):
    d.line([(PAD, 1012), (S - PAD, 1012)], fill=LINE, width=1)
    d.text((PAD, 1040), cta or c["foot"], font=f["foot"], fill=MID)
    d.text((PAD, 1082), c["url"], font=f["url"], fill=AC)


def hook(lang):
    c, f = L[lang], fonts(lang)
    img, d = canvas()
    wordmark(d, f)
    y = 172
    for i, line in enumerate(c["hook"]):
        d.text((PAD, y), line, font=f["disp"], fill=FG if i >= len(c["hook"]) - 1 else DIM)
        y += 80
    d.line([(PAD, y + 22), (PAD + 86, y + 22)], fill=AC, width=3)
    d.text((PAD, y + 56), c["hook_a"], font=f["lead"], fill=AC)
    d.text((PAD, y + 128), c["hook_b"], font=f["body"], fill=MID)
    # the next step, boxed: on Marketplace the whole game is getting a message,
    # and the footer line alone was getting lost under the fold of the crop.
    bx0, by0, bx1, by1 = PAD, 782, S - PAD, 952
    d.rectangle([bx0, by0, bx1, by1], outline=AC, width=2)
    d.text((bx0 + 34, by0 + 36), c["anchor"], font=f["lead"], fill=FG)
    d.text((bx0 + 34, by0 + 106), c["cta"], font=f["cta"], fill=AC)
    footer(d, f, c)
    return img


def prices(lang):
    c, f = L[lang], fonts(lang)
    img, d = canvas()
    wordmark(d, f)
    d.text((PAD, 168), c["prices_lab"], font=f["lab"], fill=FAINT)
    d.line([(PAD, 208), (PAD + 86, 208)], fill=AC, width=3)
    COL_W, ROW_Y, ROW_H = 466, 268, 84
    COL_X = [PAD, PAD + COL_W + 100]
    for i, (name, price) in enumerate(c["services"]):
        cx = COL_X[i % 2]
        cy = ROW_Y + (i // 2) * ROW_H
        d.text((cx, cy), name, font=f["svc"], fill=FG)
        if price:
            d.text((cx + COL_W - d.textlength(price, font=f["price"]), cy + 2), price,
                   font=f["price"], fill=AC)
        d.line([(cx, cy + 42), (cx + COL_W, cy + 42)], fill=LINE, width=1)
    ny = ROW_Y + 6 * ROW_H + 24
    d.text((PAD, ny), c["prices_note"], font=f["note"], fill=DIM)
    d.rectangle([PAD, ny + 52, S - PAD, ny + 152], outline=AC, width=2)
    d.text((PAD + 34, ny + 88), c["cta"], font=f["cta"], fill=AC)
    footer(d, f, c)
    return img


def proof(lang):
    c, f = L[lang], fonts(lang)
    img, d = canvas()
    wordmark(d, f)
    d.text((PAD, 168), c["proof_lab"], font=f["lab"], fill=FAINT)
    d.line([(PAD, 208), (PAD + 86, 208)], fill=AC, width=3)
    y = 276
    for title, sub in c["proof"]:
        d.text((PAD, y), title, font=f["lead"], fill=FG)
        d.text((PAD, y + 66), sub, font=f["body"], fill=MID)
        d.line([(PAD, y + 132), (S - PAD, y + 132)], fill=LINE, width=1)
        y += 196
    d.text((PAD, y + 6), c["proof_note"], font=f["body"], fill=AC)
    d.text((PAD, y + 58), c["cta"], font=f["cta"], fill=FG)
    footer(d, f, c)
    return img


os.makedirs(outdir, exist_ok=True)
for lang in L:
    for name, fn in (("1hook", hook), ("2build", prices), ("3proof", proof)):
        p = os.path.join(outdir, f"fb_{lang}_{name}.png")
        im = fn(lang)
        im = im.quantize(colors=256, method=Image.MEDIANCUT)
        im.save(p, optimize=True)
        print("wrote", os.path.relpath(p, root), os.path.getsize(p) // 1024, "KB")
