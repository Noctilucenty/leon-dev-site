#!/usr/bin/env python3
"""Generate every off-site post from the same price list the site uses.

Written on 2026-08-21 after an audit found that five of six Facebook posts were
quoting prices from before the reprice — one of them live to 688 people offering
online ordering at $2,000 against $600 on the site. The repo already fails its
build when a price on the SITE is wrong. Nothing watched what had already been
pasted into other people's platforms, so those posts silently rotted.

The fix is not more vigilance. It is to stop writing prices by hand anywhere.
Every figure below is interpolated from FLOORS in check_prices.py, which is the
same dict the site's own gate reads. Change a price there, run this, repaste.

    python3 tools/make_posts.py          # rewrite content/posts.md
    python3 tools/make_posts.py --check  # fail if the file is stale

The prose is still hand-written per language and never translated — only the
numbers, the domain and the contact details are injected.
"""

import ast
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_floors():
    """Read FLOORS out of check_prices.py as TEXT, never by importing it.

    Importing looked obviously right and is a trap. Python validates a cached
    .pyc by (mtime, size), and editing a price is the one edit that changes
    neither: 600 -> 700 is the same number of bytes, and an edit inside the same
    second as the last compile leaves the mtime identical. Caught in the act on
    2026-08-21 — the source said 600, a fresh import returned 700, and the
    staleness check happily reported everything in agreement.

    A generator whose whole purpose is "the prices cannot drift" must not have a
    way to read a price that is silently a version behind. Parsing the literal
    is immune, and it fails loudly if the dict ever stops being a plain literal.
    """
    src = io.open(os.path.join(ROOT, 'tools', 'check_prices.py'), encoding='utf-8').read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                getattr(t, 'id', None) == 'FLOORS' for t in node.targets):
            return ast.literal_eval(node.value)
    raise SystemExit('check_prices.py no longer defines a literal FLOORS dict')


FLOORS = load_floors()

BASE = 'leonbuilds.org'
WHATSAPP = '(510) 826-7735'
WECHAT = 'leon34695820'
EMAIL = 'leondragon3798@gmail.com'
APPSTORE = 'https://apps.apple.com/app/id6781121127'


def p(slug):
    """A floor, formatted the way it is written in copy."""
    return f'${FLOORS[slug]:,}'


# Service lines per language. The label is prose; the price is never typed.
LINES = {
    'en': [
        ('Business websites', 'websites'),
        ('Websites with logins and a database', 'websites-backend'),
        ('Online ordering and booking', 'booking-systems'),
        ('Automation for the work that repeats every week', 'business-automation'),
        ('An AI chatbot for the questions you answer daily', 'ai-chatbots'),
        ('iPhone and Android apps', 'mobile-apps'),
    ],
    'pt': [
        ('Site do seu negócio', 'websites'),
        ('Site com login e banco de dados', 'websites-backend'),
        ('Pedido online e agendamento', 'booking-systems'),
        ('Automação do trabalho que se repete toda semana', 'business-automation'),
        ('Robô que responde as perguntas que você repete todo dia', 'ai-chatbots'),
        ('Aplicativo de iPhone e Android', 'mobile-apps'),
    ],
    'es': [
        ('Página de tu negocio', 'websites'),
        ('Página con cuentas y base de datos', 'websites-backend'),
        ('Pedidos en línea y citas', 'booking-systems'),
        ('Automatización del trabajo que se repite cada semana', 'business-automation'),
        ('Bot que contesta las preguntas que repites todos los días', 'ai-chatbots'),
        ('Aplicación de iPhone y Android', 'mobile-apps'),
    ],
    'zh': [
        ('商家网站', 'websites'),
        ('带后台的网站（登录、数据库、管理页面）', 'websites-backend'),
        ('网上点单和预约', 'booking-systems'),
        ('流程自动化', 'business-automation'),
        ('智能客服', 'ai-chatbots'),
        ('手机 App', 'mobile-apps'),
    ],
}

FROM = {'en': 'from', 'pt': 'a partir de', 'es': 'desde', 'zh': ''}


def bullets(lang, sep='• '):
    out = []
    for label, slug in LINES[lang]:
        if lang == 'zh':
            out.append(f'{sep}{label} — {p(slug)} 起')
        else:
            out.append(f'{sep}{label} — {FROM[lang]} {p(slug)}')
    return '\n'.join(out)


def inline_prices(lang):
    """The one-line price run used in group posts, where bullets read as an ad."""
    parts = []
    for label, slug in LINES[lang]:
        parts.append(f'{label} {p(slug)} 起' if lang == 'zh'
                     else f'{label} {FROM[lang]} {p(slug)}')
    return ' · '.join(parts)


def link(lang, tag):
    path = '' if lang == 'en' else f'/{lang}'
    return f'{BASE}{path}?s={tag}'


LISTINGS = {
    'en': dict(
        title='I Build Websites & Automate Small Businesses',
        body='''Still handling orders, bookings, customer questions, or paperwork by hand?

I build simple software that replaces that work.

WHAT I CAN BUILD FOR YOU
{bullets}

You talk to the person who writes the code. No agency, no account manager. Fixed price in writing before any work starts, and it does not change after. When it is done you own everything — domain, hosting, code, accounts.

Not sure what you need?
Message me what your business still does by hand. I will tell you what I would automate and roughly what it starts at — free, and I will say so when the answer is that you do not need me.

{link}
Remote · available across the U.S. · English, Português, Español, 中文'''),
    'pt': dict(
        title='Faço Sites e Automatizo o seu Negócio',
        body='''Ainda anota pedido, agendamento, pergunta de cliente ou papelada na mão?

Sou brasileiro e sou desenvolvedor. Eu faço o sistema que tira esse trabalho de você.

O QUE EU POSSO FAZER PRA VOCÊ
{bullets}

Você fala direto com quem escreve o código. Sem agência, sem gerente de conta. Preço fechado por escrito antes de começar, e não muda no final. Quando termina, tudo fica no seu nome: domínio, hospedagem, código e as contas.

Não sabe do que precisa?
Me manda o que o seu negócio ainda faz na mão. Eu falo o que dá pra automatizar e a partir de quanto sai — de graça, e falo também quando você não precisa de mim.

{link}
Online · atendo os Estados Unidos inteiros · Português, English, Español, 中文'''),
    'es': dict(
        title='Hago Páginas Web y Automatizo tu Negocio',
        body='''¿Todavía tomas pedidos, citas, preguntas de clientes o papeleo a mano?

Yo hago el sistema que reemplaza ese trabajo.

LO QUE PUEDO HACER PARA TI
{bullets}

Hablas directo con la persona que escribe el código. Sin agencia, sin ejecutivo de cuenta. Precio cerrado por escrito antes de empezar, y no cambia al final. Al terminar todo queda a tu nombre: dominio, hosting, código y las cuentas.

¿No sabes qué necesitas?
Escríbeme qué hace tu negocio a mano todavía. Te digo qué automatizaría y desde cuánto sale — gratis, y también te digo cuando no me necesitas.

{link}
En línea · atiendo negocios en todo Estados Unidos · Español, English, Português, 中文'''),
    'zh': dict(
        title='做网站 + 帮小生意做自动化',
        body='''点单、预约、客人问的那些问题、店里的表格，是不是现在还都靠人工在做？

我把这些做成系统，让它自己跑。

我能帮你做的
{bullets}

你直接跟写代码的人聊，没有中介，也没有客户经理。开工之前把价钱白纸黑字写下来，做完不变。做完之后域名、服务器、代码和账号全部在你自己名下。

不确定自己需要什么？
把你现在还靠人工做的事情发给我，我告诉你哪一块能自动化、大概从多少钱起 —— 不收钱，不值得做我也会直接说。

微信 ''' + WECHAT + '''
{link}
线上做 · 全美国都接 · 中文、English、Português、Español'''),
}

GROUP = {
    'en': '''hi all — i'm a developer. i build websites, online ordering, booking systems and apps for small businesses, remotely, anywhere in the us.

fixed price in writing before any work starts, and it does not change afterward. {inline}

if you already have something live and just want an opinion, send me the link — i'll look at it free and tell you whether it's worth changing. sometimes it isn't, and i'll say so.

{link}''',
    'pt': '''oi, pessoal. sou brasileiro e sou desenvolvedor. faço site, pedido online, agendamento e aplicativo pra negócio pequeno. atendo os estados unidos inteiros, tudo online — você me explica o problema do seu jeito, sem precisar saber nome técnico de nada.

preço fechado por escrito antes de eu começar, e não muda no final. {inline}

se você já tem alguma coisa no ar e quer só uma opinião, me manda o link que eu olho de graça e falo se vale a pena mexer — às vezes não vale, e eu falo isso.

{link}''',
    'es': '''hola a todos. soy desarrollador y hago páginas, pedidos en línea, citas y aplicaciones para negocios pequeños. atiendo todo estados unidos, en línea, y hablo español — me explicas el problema a tu manera, sin necesidad de términos técnicos.

precio cerrado por escrito antes de empezar, y no cambia al final. {inline}

si ya tienes algo en línea y solo quieres una opinión, mándame el link y lo reviso gratis. a veces la respuesta es que no vale la pena cambiarlo, y también te lo digo.

{link}''',
    'zh': '''大家好。我是做软件的，帮小生意做网站、网上点单、预约系统和手机 App。全美国都接，都是线上做，可以全程用中文聊——你用平时说话的方式把问题讲一遍就行，不用懂技术名词。

开工之前把价钱写下来，做完不变。{inline}

已经有网站或者系统的，把链接发给我，我免费看一眼告诉你值不值得改。不值得改我也会直接说。

微信 ''' + WECHAT + ''' · {link}''',
}


def render():
    out = [f'''# Posts, ready to publish

GENERATED by tools/make_posts.py — do not edit by hand. Every price below is
read from FLOORS in tools/check_prices.py, the same dict the site's own gate
uses, so a reprice is `python3 tools/make_posts.py` and a repaste rather than an
archaeology dig through 51 Facebook groups.

Rules baked in: no city or region anywhere, no invented proof, prices are the
published floors and nothing else, and Chinese copy carries WeChat rather than
WhatsApp because a Chinese owner in the US does not use WhatsApp. LEON IS
BRAZILIAN — "sou brasileiro" is true and stays in the Portuguese copy.

Links carry `?s=` so the traffic table can tell the channels apart.

Marketplace note: Facebook Marketplace REJECTS service listings outright
("your listing promotes services or offers of work" — Commerce Policies on
Services). The listing copy below is kept because it is the right copy for any
classifieds surface, but it will be removed if posted to Marketplace again.
Groups are the compliant Facebook surface.

---

## 1. Listing copy — by language
''']

    for lang in ['en', 'pt', 'es', 'zh']:
        L = LISTINGS[lang]
        body = L['body'].format(bullets=bullets(lang),
                                link=link(lang, f'fbmkt-{lang}'))
        out.append(f"### {lang.upper()} — title: `{L['title']}`\n"
                   f"Price `{FLOORS['websites']}` · Category Miscellaneous · Condition New\n\n"
                   + '\n'.join('> ' + l if l else '>' for l in body.split('\n')) + '\n')

    out.append('''---

## 2. Facebook group posts

Shorter than a listing and written as a person. Read the group's pinned rules
first; some ban service providers outright and posting there costs the account
for nothing. One group per day, one language per group, different wording each
time — the same text pasted into five groups is what gets flagged as spam.

Do NOT use the composer's "post to up to 9 groups" feature. It would push one
language into eight wrong audiences.
''')

    for lang in ['pt', 'es', 'zh', 'en']:
        body = GROUP[lang].format(inline=inline_prices(lang),
                                  link=link(lang, f'fbgrp-{lang}'))
        out.append(f'### {lang.upper()}\n'
                   + '\n'.join('> ' + l if l else '>' for l in body.split('\n')) + '\n')

    out.append(f'''---

## 3. WhatsApp forward — written to be pasted by someone else

Not posted by him. A member forwarding a message inside their own group is
normal traffic; him posting in that group is an ad from a stranger.

### PT
> gente, quem tá precisando de site ou de sistema de pedido pro negócio: eu conheço um
> desenvolvedor brasileiro que atende os estados unidos inteiros online. preço fechado por
> escrito antes de começar. site {FROM['pt']} {p('websites')}, pedido online {FROM['pt']}
> {p('booking-systems')}, e tudo fica no nome do dono no final.
> whatsapp {WHATSAPP} · {link('pt', 'wa-fwd')}

### ES
> gente, para quien necesite página o sistema de pedidos para su negocio: conozco a un
> desarrollador que habla español y atiende todo estados unidos en línea. precio cerrado
> por escrito antes de empezar. página {FROM['es']} {p('websites')}, pedidos en línea
> {FROM['es']} {p('booking-systems')}, y todo queda a nombre del dueño al terminar.
> whatsapp {WHATSAPP} · {link('es', 'wa-fwd')}

---

## 4. WeChat message

WeChat strips formatting, so this is plain text.

> 有需要做网站或者网上点单系统的老板，我推荐一个人：他自己写代码，会说中文，全美国都接，
> 都是线上做。开工之前价钱白纸黑字写清楚，做完不变。商家网站 {p('websites')} 起，
> 网上点单和预约 {p('booking-systems')} 起，做完域名和代码全部在老板自己名下。
> 微信 {WECHAT} · {link('zh', 'wechat')}

---

## Contact, by language

| audience | first contact |
|---|---|
| English · Português · Español | WhatsApp {WHATSAPP} |
| 中文 | WeChat {WECHAT} — never WhatsApp |
| anyone | {EMAIL} · booking at {BASE}/call, /pt/agendar, /es/agendar, /zh/yuyue |

Proof that may be cited: the App Store app ({APPSTORE}), the multi-brand
ordering system, the review-reply tool, the 33,772-zip-code scoring. Nothing
else. No testimonials, ratings, revenue or client names — there are none.
''')
    return '\n'.join(out)


def main():
    path = os.path.join(ROOT, 'content', 'posts.md')
    new = render()
    check = '--check' in sys.argv
    old = io.open(path, encoding='utf-8').read() if os.path.exists(path) else None
    if check:
        if old != new:
            print('POSTS STALE — content/posts.md does not match the current floors.')
            print('Run: python3 tools/make_posts.py')
            return 1
        print(f'posts ok — {len(FLOORS)} floors, every post agrees')
        return 0
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(new)
    print(f'wrote content/posts.md — {len(FLOORS)} floors interpolated, '
          f'4 listings, 4 group posts, 2 WhatsApp, 1 WeChat')
    return 0


if __name__ == '__main__':
    sys.exit(main())
