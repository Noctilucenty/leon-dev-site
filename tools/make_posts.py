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
        ('Online ordering or booking', 'booking-systems'),
        ('Automation for the work that repeats every week', 'business-automation'),
        ('An AI chatbot for the questions you answer daily', 'ai-chatbots'),
        ('iPhone and Android apps', 'mobile-apps'),
    ],
    'pt': [
        ('Site para o seu negócio', 'websites'),
        ('Sistema com login e banco de dados', 'websites-backend'),
        ('Pedido online ou agendamento', 'booking-systems'),
        ('Automação de tarefas repetitivas', 'business-automation'),
        ('Chatbot para responder perguntas frequentes', 'ai-chatbots'),
        ('Aplicativo para iPhone e Android', 'mobile-apps'),
    ],
    'es': [
        ('Sitio web para tu negocio', 'websites'),
        ('Sistema con cuentas y base de datos', 'websites-backend'),
        ('Pedidos en línea o reservas', 'booking-systems'),
        ('Automatización de tareas repetitivas', 'business-automation'),
        ('Chatbot para responder preguntas frecuentes', 'ai-chatbots'),
        ('Aplicación para iPhone y Android', 'mobile-apps'),
    ],
    'zh': [
        ('商家网站', 'websites'),
        ('带登录、数据库和管理后台的网站', 'websites-backend'),
        ('在线点单或预约', 'booking-systems'),
        ('重复工作自动化', 'business-automation'),
        ('智能客服', 'ai-chatbots'),
        ('iPhone 和 Android App', 'mobile-apps'),
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


def link(lang, tag):
    path = '' if lang == 'en' else f'/{lang}'
    return f'{BASE}{path}?s={tag}'


def group_link(lang, variant):
    """A required per-group tag, deliberately impossible to mistake as final.

    GROUP-SLUG must be replaced before posting. Keeping the placeholder in the
    generated copy makes a missed attribution step visible instead of silently
    folding every group into one language-level traffic source.
    """
    return link(lang, f'fbgrp-GROUP-SLUG-{variant}')


def classified_link(lang):
    """A required per-surface tag for permitted classifieds/directories."""
    return link(lang, f'classified-SURFACE-SLUG-{lang}')


CLASSIFIEDS = {
    'en': dict(
        title='I Build Websites & Automate Small Businesses',
        body='''Still handling orders, bookings, customer questions, or paperwork by hand?

I build simple software that reduces that manual work.

WHAT I CAN BUILD FOR YOU
{bullets}

You talk to the person who writes the code. No agency, no account manager. The price for the agreed scope is fixed in writing before work starts. If the scope changes, we agree in writing on the extra work, price, and timing before I do it. At handoff, I transfer the agreed project accounts and provide the source code and setup notes included in our scope.

Not sure what you need?
Message me what your business still does by hand. I will tell you what I would automate and roughly what it starts at — free, and I will say so when the answer is that you do not need me.

{link}
Remote · available across the U.S. · English, Português, Español, 中文'''),
    'pt': dict(
        title='Crio Sites e Automatizo seu Negócio',
        body='''Ainda anota pedido, agendamento, pergunta de cliente ou papelada na mão?

Sou brasileiro e desenvolvedor. Crio sistemas para reduzir esse trabalho manual.

O QUE EU POSSO FAZER PRA VOCÊ
{bullets}

Você fala direto com quem escreve o código, sem agência nem gerente de conta. O preço do escopo combinado fica fechado por escrito antes de começar. Se o escopo mudar, combinamos por escrito o trabalho extra, o preço e o prazo antes de eu fazê-lo. Na entrega, transfiro as contas do projeto que combinamos e entrego o código-fonte e as instruções previstas no escopo.

Não sabe do que precisa?
Me conte o que o seu negócio ainda faz à mão. Eu explico o que pode ser automatizado e qual é o preço inicial — sem custo. Também digo com sinceridade quando não vale a pena contratar um sistema.

{link}
Online · atendo os Estados Unidos inteiros · Português, English, Español, 中文'''),
    'es': dict(
        title='Creo Sitios Web y Automatizo tu Negocio',
        body='''¿Todavía tomas pedidos, citas, preguntas de clientes o papeleo a mano?

Creo sistemas sencillos para reducir ese trabajo manual.

LO QUE PUEDO HACER PARA TI
{bullets}

Hablas directamente con quien escribe el código, sin agencia ni ejecutivo de cuenta. El precio del alcance acordado queda fijado por escrito antes de empezar. Si cambia el alcance, primero acordamos por escrito el trabajo adicional, el precio y el plazo. En la entrega, transfiero las cuentas del proyecto acordadas y entrego el código fuente y las instrucciones incluidas en el alcance.

¿No sabes qué necesitas?
Cuéntame qué tareas sigue haciendo tu negocio a mano. Te explico qué se podría automatizar y cuál sería el precio inicial, sin costo. También te digo con sinceridad cuando no vale la pena contratar un sistema.

{link}
En línea · atiendo negocios en todo Estados Unidos · Español, English, Português, 中文'''),
    'zh': dict(
        title='做网站 + 帮小生意做自动化',
        body='''点单、预约、客人问的那些问题、店里的表格，是不是现在还都靠人工在做？

我可以把合适的步骤做成系统，减少重复的人工操作。

我能帮你做的
{bullets}

你直接跟写代码的人沟通，没有中介或客户经理。开工前，我会根据双方确认的工作范围给出书面固定报价。如果范围有变化，新增工作、价格和时间会先书面确认，再继续做。交付时，我会移交事先约定的项目账号、源代码和使用说明。

不确定自己需要什么？
把现在还靠人工完成的步骤发给我，我可以免费帮你判断哪些适合自动化、价格大概从哪里起。如果暂时不值得做系统，我也会如实说明。

微信 ''' + WECHAT + '''
{link}
线上做 · 全美国都接 · 中文、English、Português、Español'''),
}

GROUP_AD = {
    'en': '''Still taking orders or appointments by phone, chat, or paper?

I build websites and simple systems for small businesses so customers can order or book online and staff do less repeated data entry. A business website starts at {website}; online ordering or booking starts at {system}.

The price for the agreed scope is fixed in writing before work starts. If the scope changes, we agree in writing on the extra work, price, and timing first. At handoff, I transfer the agreed project accounts and provide the source code and setup notes included in our scope.

If you already have something live, send me the link and the part that is still manual. I can tell you whether changing it is likely to help.

{link}''',
    'pt': '''Ainda recebe pedidos ou marca horários por telefone, mensagem ou papel?

Sou desenvolvedor brasileiro e crio sites e sistemas simples para pequenos negócios. Assim, o cliente pode fazer um pedido ou agendar online, e a equipe reduz o trabalho repetitivo. Um site para o negócio custa a partir de {website}; um sistema de pedido online ou agendamento, a partir de {system}.

O preço do escopo combinado fica fechado por escrito antes de começar. Se o escopo mudar, combinamos por escrito o trabalho extra, o preço e o prazo antes de eu fazê-lo. Na entrega, transfiro as contas do projeto que combinamos e entrego o código-fonte e as instruções previstas no escopo.

Se você já tem algo no ar, me mande o link e explique qual parte ainda é manual. Posso dizer se uma mudança provavelmente ajudaria.

{link}''',
    'es': '''¿Todavía recibes pedidos o reservas por teléfono, mensajes o papel?

Soy desarrollador y creo sitios web y sistemas sencillos para pequeños negocios. Así, el cliente puede pedir o reservar en línea y el equipo evita tareas repetitivas. Un sitio web para el negocio cuesta desde {website}; un sistema de pedidos en línea o reservas, desde {system}.

El precio del alcance acordado queda fijado por escrito antes de empezar. Si cambia el alcance, primero acordamos por escrito el trabajo adicional, el precio y el plazo. En la entrega, transfiero las cuentas del proyecto acordadas y entrego el código fuente y las instrucciones incluidas en el alcance.

Si ya tienes algo en línea, envíame el enlace y cuéntame qué parte sigue siendo manual. Puedo decirte si probablemente valga la pena cambiarla.

{link}''',
    'zh': '''还在用电话、聊天消息或纸质表格记录订单和预约？

我是开发者，为小商家做网站和简单系统，让顾客可以自己在线下单或预约，也减少员工重复录入。商家网站 {website} 起；在线点单或预约系统 {system} 起。

开工前，我会根据双方确认的工作范围给出书面固定报价。如果范围有变化，新增工作、价格和时间会先书面确认，再继续做。交付时，我会移交事先约定的项目账号、源代码和使用说明。

如果已经有网站或系统，可以把链接和仍需人工处理的步骤发给我。我可以帮你判断是否值得调整。

微信 ''' + WECHAT + ''' · {link}''',
}

GROUP_COMMUNITY = {
    'en': '''If orders or appointments keep getting lost between DMs, phone calls, and paper, map the process before buying software:

1. Write down exactly what the customer must provide.
2. Mark the steps a staff member really must approve.
3. Decide who needs a notification when it is complete.

Those answers show whether you need a simple form, an ordering page, or a full system—and help avoid paying for features the team does not need. If the process is straightforward, online ordering or booking starts at {system}.

I build these systems for small businesses. If this group's rules allow it, send me your current process and I will point out the first step I would simplify.

{link}''',
    'pt': '''Se pedidos ou agendamentos se perdem entre WhatsApp, telefone e caderno, vale mapear o processo antes de contratar um sistema:

1. Anote exatamente quais informações o cliente precisa enviar.
2. Marque as etapas que realmente dependem da aprovação de alguém da equipe.
3. Defina quem precisa receber uma notificação quando tudo estiver concluído.

Essas respostas mostram se você precisa de um formulário simples, de uma página de pedidos ou de um sistema completo, e ajudam a evitar funções de que a equipe não precisa. Se o processo for simples, um sistema de pedido online ou agendamento custa a partir de {system}.

Sou desenvolvedor e crio esse tipo de sistema para pequenos negócios. Se as regras do grupo permitirem, me conte como você trabalha hoje e eu aponto a primeira etapa que simplificaria.

{link}''',
    'es': '''Si los pedidos o las reservas se pierden entre mensajes, llamadas y notas en papel, conviene describir el proceso antes de contratar un sistema:

1. Anota exactamente qué información debe enviar el cliente.
2. Marca los pasos que realmente requieren la aprobación de alguien del equipo.
3. Decide quién necesita recibir una notificación al finalizar.

Las respuestas muestran si necesitas un formulario sencillo, una página de pedidos o un sistema completo, y ayudan a evitar funciones que el equipo no necesita. Si el proceso es sencillo, un sistema de pedidos en línea o reservas cuesta desde {system}.

Soy desarrollador y creo este tipo de sistemas para pequeños negocios. Si las reglas del grupo lo permiten, cuéntame cómo trabajas hoy y te señalo el primer paso que simplificaría.

{link}''',
    'zh': '''如果订单或预约散落在微信、电话和纸质记录里，先别急着买系统。可以先整理三件事：

1）顾客每次需要填写哪些信息？
2）哪些步骤确实需要员工确认？
3）流程完成后，谁需要收到通知？

先把这三点写清楚，才能判断需要的是简单表单、点单页面还是完整系统，也能避免花钱做暂时不需要的功能。如果流程比较简单，在线点单或预约系统 {system} 起。

我是开发者，平时为小商家做这类系统。如果群规允许，可以把现在的流程发给我，我会指出最值得先简化的一步。

微信 ''' + WECHAT + ''' · {link}''',
}


def render():
    out = [f'''# Post templates — review before publishing

GENERATED by tools/make_posts.py — do not edit by hand. Every price below is
read from FLOORS in tools/check_prices.py, the same dict the site's own gate
uses, so a reprice is `python3 tools/make_posts.py` and a repaste rather than an
archaeology dig through 51 Facebook groups.

This file prepares copy; it does not prove that anything was posted. A group
draft is not ready until the current group rules have been checked and its
`GROUP-SLUG` placeholder has been replaced.

Rules baked in: no city or region anywhere, no invented proof, and prices are
the published floors and nothing else. Chinese copy uses WeChat as the primary
contact; phone and email remain alternatives. LEON IS BRAZILIAN — "sou
brasileiro" is true and stays in the Portuguese copy.

Links carry `?s=` so the traffic table can tell the channels apart. Classified
and directory drafts contain a required `SURFACE-SLUG` placeholder. Facebook
group and forwarded-message drafts contain `GROUP-SLUG`. Replace the applicable
placeholder with the actual destination's short ASCII slug before posting.

Marketplace note: Facebook Marketplace REJECTS service listings outright
("your listing promotes services or offers of work" — Commerce Policies on
Services). The copy below is for a classifieds or directory surface whose rules
explicitly allow services. Do not publish it
to Marketplace. Marketplace publication history belongs in the audit and
publication ledger; this generator emits no Marketplace fields or source tags.
Nothing in this file is an instruction to delete or edit an existing listing.

---

## 1. Classifieds and directories copy — by language

Use only on a classifieds or directory surface that explicitly permits service
offers. Before publishing, replace `SURFACE-SLUG` with a short, stable,
lowercase ASCII slug for that exact destination. Example:
`classified-SURFACE-SLUG-pt` becomes `classified-brazilian-directory-pt`.
Never publish a link that still contains `SURFACE-SLUG` and do not reuse one
surface's tag for another.
''']

    for lang in ['en', 'pt', 'es', 'zh']:
        L = CLASSIFIEDS[lang]
        body = L['body'].format(bullets=bullets(lang),
                                link=classified_link(lang))
        out.append(f"### {lang.upper()} — title: `{L['title']}`\n"
                   f"Suggested lead price anchor: website work from {p('websites')}. "
                   "Keep every other figure attached to its named service.\n\n"
                   + '\n'.join('> ' + l if l else '>' for l in body.split('\n')) + '\n')

    out.append('''---

## 2. Facebook group posts

Read the group's current rules before choosing a draft:

- **Ad/classified group:** use the direct offer only when service ads are allowed.
- **Community group:** use the useful, problem-first post only when disclosed
  self-promotion is allowed.
- **No promotion, service providers banned, or rules unclear:** **SKIP THE GROUP.**
  Do not disguise an ad as advice and do not contact members unsolicited.

One group, one language, one appropriate variant. Do not use the composer's
"post to up to 9 groups" feature and do not paste identical copy into a batch.

### Tracking tag — required before posting

Replace `GROUP-SLUG` in the chosen draft with a short, stable, lowercase ASCII
slug for that exact group, using hyphens instead of spaces. Example:
`fbgrp-GROUP-SLUG-ad` becomes `fbgrp-profissionais-brasileiros-eua-ad`.
Never publish a link that still contains `GROUP-SLUG`, and never reuse a
language-only tag such as `fbgrp-pt` across several groups. Record the final tag
beside the group in the publication ledger.
''')

    for lang in ['pt', 'es', 'zh', 'en']:
        ad = GROUP_AD[lang].format(website=p('websites'),
                                    system=p('booking-systems'),
                                    link=group_link(lang, 'ad'))
        community = GROUP_COMMUNITY[lang].format(
            system=p('booking-systems'),
            link=group_link(lang, 'community'))
        out.append(
            f'### {lang.upper()} — ad/classified group\n'
            + '\n'.join('> ' + l if l else '>' for l in ad.split('\n'))
            + f'\n\n### {lang.upper()} — community group\n'
            + '\n'.join('> ' + l if l else '>' for l in community.split('\n'))
            + '\n')

    out.append(f'''---

## 3. WhatsApp forwards — DRAFTS, NOT SENT

These are preparation drafts only. Their presence in this file is **not evidence
that either message was sent**. Leon should not paste them into someone else's
group. A real member may choose to forward one only when that group's rules
allow it.

Before a member forwards a draft, replace `GROUP-SLUG` with that WhatsApp
group's stable lowercase ASCII slug. Leave it unsent if nobody independently
chooses to forward it.

### PT
> pessoal, estou compartilhando o contato do Leon, um desenvolvedor brasileiro que atende
> pequenos negócios online nos Estados Unidos. Ele combina por escrito o preço do escopo
> antes de começar; se o escopo mudar, o trabalho extra, o preço e o prazo são combinados
> antes. Site {FROM['pt']} {p('websites')}; pedido online ou agendamento {FROM['pt']}
> {p('booking-systems')}. Na entrega, ele transfere as contas do projeto e o código-fonte
> que foram combinados.
> WhatsApp {WHATSAPP} · {link('pt', 'wa-GROUP-SLUG-fwd')}

### ES
> comparto el contacto de Leon, un desarrollador que habla español y atiende en línea a
> pequeños negocios de todo Estados Unidos. Acuerda por escrito el precio del alcance antes
> de empezar; si cambia el alcance, primero se acuerdan el trabajo adicional, el precio y el
> plazo. Sitio web {FROM['es']} {p('websites')}; pedidos en línea o reservas {FROM['es']}
> {p('booking-systems')}. En la entrega, transfiere las cuentas del proyecto y el código
> fuente acordados.
> WhatsApp {WHATSAPP} · {link('es', 'wa-GROUP-SLUG-fwd')}

---

## 4. WeChat forward — DRAFT, NOT SENT

This is a preparation draft only; **it has not been sent**. WeChat strips
formatting, so the draft is plain text. If a real member voluntarily shares it
in a group whose rules allow promotion, replace `GROUP-SLUG` with that group's
stable lowercase ASCII slug first. For a one-to-one message, use
`wechat-direct-fwd` instead.

> 如果群规允许，分享一位开发者的联系方式。Leon 自己写代码，可以全程用中文沟通，
> 在线为美国各地的小商家做项目。开工前，他会根据双方确认的范围给出书面固定报价；
> 如果范围有变化，会先书面确认新增工作、价格和时间。商家网站 {p('websites')} 起，
> 在线点单或预约系统 {p('booking-systems')} 起。交付时会移交事先约定的项目账号、
> 源代码和使用说明。微信 {WECHAT} · {link('zh', 'wechat-GROUP-SLUG-fwd')}

---

## Contact, by language

| audience | primary contact | alternatives |
|---|---|---|
| English · Português · Español | WhatsApp {WHATSAPP} | phone · email |
| 中文 | WeChat {WECHAT} | phone · {EMAIL} |
| anyone | booking page | {BASE}/call · /pt/agendar · /es/agendar · /zh/yuyue |

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
          f'4 classifieds/directory drafts, 8 group variants, '
          f'3 unsent forward drafts')
    return 0


if __name__ == '__main__':
    sys.exit(main())
