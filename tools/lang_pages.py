#!/usr/bin/env python3
"""Service pages in Portuguese, Spanish and Chinese.

The point of these pages is the one thing an agency cannot copy: the person
who writes the code also speaks the language the owner explains the problem
in. "web development" is unwinnable — Toptal and Clutch own it — but
"criar site para restaurante nos estados unidos" is nearly uncontested, and
the person searching it is ready to buy.

The copy is written for each audience, never translated at page load, and lives in
content/lang_pages.json so it can be re-edited without touching this renderer.
Called from build_pages.py, which passes its own helpers in via ctx so the
markup, fonts and icons stay identical to the English pages.

Language homes live at es/index.html, pt/index.html and zh/index.html, which
is why the service pages can sit beside them at /pt/<slug> without the
/pt vs /pt/ ambiguity a stray pt.html would create.
"""

# Slug per (language, service). Chosen to read like the phrase the buyer
# would actually type, not like a translation of the English slug.
SLUGS = {
    ('pt', 'websites'):   'criar-site',
    ('pt', 'ordering'):   'pedidos-online',
    ('pt', 'automation'): 'automacao',
    ('es', 'websites'):   'pagina-web',
    ('es', 'ordering'):   'pedidos-en-linea',
    ('es', 'automation'): 'automatizacion',
    ('zh', 'websites'):   'zuo-wangzhan',
    ('zh', 'ordering'):   'zaixian-diandan',
    ('zh', 'automation'): 'zidonghua',
}

# The English page each one is the translation of — this is what makes the
# hreflang cluster a cluster instead of four unrelated pages.
EN_COUNTERPART = {
    'websites':   '/services/websites',
    'ordering':   '/services/booking-systems',
    'automation': '/services/business-automation',
}

# Machine-readable floors mirror the public price source. These are starting
# scopes, never instant quotes. Keep the $300 website offer framed as a limited
# presence site in the authored copy; lead follow-up is the separate $1,500
# product described on each localized website page.
STARTING_PRICES = {
    'websites': 300,
    'ordering': 600,
    'automation': 500,
}

# Everything language-specific that is chrome rather than copy.
LANGS = {
    'pt': dict(
        html_lang='pt-BR', hreflang='pt-BR', home='/pt',
        nav=[('/pt#faco', 'o que fazemos'), ('/pt#precos', 'preços'),
             ('/pt#feito', 'projetos'), ('/call', 'agendar 15 min'),
             ('/', 'english')],
        contact_kind='wa',
        wa_text='Oi%20Leon%2C%20vi%20o%20seu%20site.%20Meu%20neg%C3%B3cio%20%C3%A9%3A%20',
        contact_label='whatsapp',
        skip='pular para o conteúdo',
        crumb_home='início',
        other_label='outros serviços',
        foot='© <span id="yr">2026</span> <span class="keepcase">Leon Builds</span> · by <span class="keepcase">Leon Kelvin Li</span> · california · atendemos negócios em todos os Estados Unidos · <a href="/">english</a> · <a href="/es">español</a> · <a href="/zh">中文</a>',
        assist_starter='pode responder em português. meu negócio é o seguinte: ',
        call_label='agendar 15 minutos',
        privacy_label='privacidade',
    ),
    'es': dict(
        html_lang='es', hreflang='es', home='/es',
        nav=[('/es#hago', 'lo que hacemos'), ('/es#precios', 'precios'),
             ('/es#hecho', 'proyectos'), ('/call', 'agendar 15 min'),
             ('/', 'english')],
        contact_kind='wa',
        wa_text='Hola%20Leon%2C%20vi%20tu%20p%C3%A1gina.%20Mi%20negocio%20es%3A%20',
        contact_label='whatsapp',
        skip='saltar al contenido',
        crumb_home='inicio',
        other_label='otros servicios',
        foot='© <span id="yr">2026</span> <span class="keepcase">Leon Builds</span> · by <span class="keepcase">Leon Kelvin Li</span> · california · atendemos negocios en todo estados unidos · <a href="/">english</a> · <a href="/pt">português</a> · <a href="/zh">中文</a>',
        assist_starter='puedes responder en español. mi negocio es el siguiente: ',
        call_label='agendar 15 minutos',
        privacy_label='privacidad',
    ),
    'zh': dict(
        html_lang='zh-Hans', hreflang='zh', home='/zh',
        nav=[('/zh#zuo', '我们能做什么'), ('/zh#jiage', '价格'),
             ('/zh#zuoguo', '做过的东西'), ('/call', '预约 15 分钟'),
             ('/', 'english')],
        # WeChat, not WhatsApp. Every other language page leads with WhatsApp
        # and the Chinese pages inherited it, which is a button a Chinese owner
        # in the US will never press — while the copy told them to 发微信 and
        # then gave them no ID to add. Tap-to-copy rather than a deep link,
        # because no WeChat URL scheme reliably opens an add-friend screen from
        # mobile Safari, and a button that silently does nothing is worse than
        # an ID they can paste.
        contact_kind='wechat',
        wechat_id='leon34695820',
        contact_label='微信 leon34695820',
        skip='跳到正文',
        crumb_home='首页',
        other_label='其他服务',
        foot='© <span id="yr">2026</span> <span class="keepcase">Leon Builds</span> · by <span class="keepcase">Leon Kelvin Li</span> · 加州 · 全美国都接 · <a href="/">english</a> · <a href="/es">español</a> · <a href="/pt">português</a>',
        assist_starter='请用中文回复。我的生意是这样的：',
        call_label='预约 15 分钟',
        privacy_label='隐私',
    ),
}


def call_href(lang):
    """Where "book 15 minutes" points in this language. One function, so a
    service page and the nav above it can never disagree."""
    return f"/{lang}/{CALL_COPY[lang]['slug']}"


WA = 'https://wa.me/15108267735?text='
MAIL = 'mailto:leondragon3798@gmail.com'


def _contact_href(L):
    if L['contact_kind'] == 'wa':
        return WA + L['wa_text']
    if L['contact_kind'] == 'wechat':
        return '#wechat'          # handled by the copy button, never followed
    return MAIL + '?subject=project'


def _contact_attrs(L):
    """The markup differences between a link out and a tap-to-copy button."""
    if L['contact_kind'] == 'wa':
        return ' target="_blank" rel="noopener"'
    if L['contact_kind'] == 'wechat':
        return (f' data-copy="{L["wechat_id"]}" data-copied="已复制，去微信粘贴添加"'
                ' onclick="return false"')
    return ''


def _footer_contacts(lang, L):
    """Localized contact choices with a separate analytics label per action."""
    contact = _contact_href(L)
    email_label = {"es": "enviar correo", "pt": "enviar e-mail", "zh": "发邮件给 Leon"}.get(lang, "Email Leon")
    return (
        f'<a href="{contact}"{_contact_attrs(L)} '
        f'data-evt="footer_contact_click_{lang}">{L["contact_label"]}</a> · '
        f'<a href="mailto:leondragon3798@gmail.com" '
        f'data-evt="footer_email_click_{lang}">{email_label}</a> · '
        f'<a href="tel:+15108267735" '
        f'data-evt="footer_phone_click_{lang}">(510) 826-7735</a> · '
        f'<a href="/privacy" '
        f'data-evt="footer_privacy_click_{lang}">{L["privacy_label"]}</a>'
    )


def _alternates(key, path):
    """The four-way hreflang cluster for one service, plus x-default."""
    out = [('en', EN_COUNTERPART[key])]
    for code, L in LANGS.items():
        out.append((L['hreflang'], f'/{code}/{SLUGS[(code, key)]}'))
    out.append(('x-default', EN_COUNTERPART[key]))
    return out


def _identity_schema_nodes(BASE):
    """Keep the person and the business distinct on every localized page."""
    return [
        {"@type": "Person", "@id": f"{BASE}/#leon",
         "name": "Leon Kelvin Li", "alternateName": "Leon Li",
         "url": f"{BASE}/about", "worksFor": {"@id": f"{BASE}/#business"}},
        {"@type": "Organization", "@id": f"{BASE}/#business",
         "name": "Leon Builds", "url": f"{BASE}/",
         "founder": {"@id": f"{BASE}/#leon"},
         "employee": {"@id": f"{BASE}/#leon"}},
    ]


def render(lang, key, page, ctx):
    """One service page in one language. ctx carries build_pages' helpers."""
    e, BASE, FONTS, ICONS = ctx['e'], ctx['BASE'], ctx['FONTS'], ctx['ICONS']
    L = LANGS[lang]
    slug = SLUGS[(lang, key)]
    path = f'/{lang}/{slug}'
    contact = _contact_href(L)

    alts = ''.join(
        f'<link rel="alternate" hreflang="{hl}" href="{BASE}{href}">'
        for hl, href in _alternates(key, path))

    faqs = [(f['q'], f['a']) for f in page['faqs']]
    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "@id": f"{BASE}/#website",
         "name": "Leon Builds", "alternateName": "Leon Builds by Leon Kelvin Li",
         "url": f"{BASE}/"},
        {"@type": "WebPage", "@id": f"{BASE}{path}#webpage",
         "name": page['title'].split('|')[0].strip(),
         "description": page['metaDescription'],
         "inLanguage": L['html_lang'], "url": f"{BASE}{path}",
         "isPartOf": {"@id": f"{BASE}/#website"},
         "mainEntity": {"@id": f"{BASE}{path}#service"}},
        {"@type": "Service",
         "@id": f"{BASE}{path}#service",
         "name": page['title'].split('|')[0].strip(),
         "description": page['metaDescription'],
         "serviceType": page['h1_plain'] + ' ' + page['h1_em'],
         "inLanguage": L['html_lang'],
         "provider": {"@id": f"{BASE}/#leon"},
         "areaServed": {"@type": "Country", "name": "United States"},
         "offers": {"@type": "Offer", "price": str(STARTING_PRICES[key]),
                    "priceCurrency": "USD", "description": page['pricetag'],
                    "eligibleRegion": {"@type": "Country", "name": "United States"}},
         "url": f"{BASE}{path}"},
        *_identity_schema_nodes(BASE),
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": L['crumb_home'],
             "item": BASE + L['home']},
            {"@type": "ListItem", "position": 2,
             "name": page['h1_plain'] + ' ' + page['h1_em'],
             "item": BASE + path}]},
    ]}

    import json
    head = f'''<!DOCTYPE html>
<html lang="{L['html_lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(page['title'])}</title>
<meta name="description" content="{e(page['metaDescription'])}">
<meta name="theme-color" content="#000000">
<meta name="color-scheme" content="dark">
<link rel="canonical" href="{BASE}{path}">
{alts}
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}{path}">
<meta property="og:site_name" content="Leon Builds">
<meta property="og:title" content="{e(page['title'])}">
<meta property="og:description" content="{e(page['metaDescription'])}">
<meta property="og:image" content="{BASE}/assets/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
{FONTS}
<link rel="stylesheet" href="/styles.css">
<link rel="stylesheet" href="/assist.css">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
</head>
<body>'''

    navlinks = ''.join(
        f'<a href="{call_href(lang) if h == "/call" else h}"><i>[</i><span>{e(t)}</span><i>]</i></a>'
        for h, t in L['nav'])
    nav = f'''{ICONS}<a class="skip" href="#main">{e(L['skip'])}</a>
<div class="progress" id="progress" aria-hidden="true"></div>
<div class="cursor" id="cursor" aria-hidden="true"><span></span></div>
<header class="nav" id="nav">
  <a class="mark" href="{L['home']}">
    <span class="mark-dot">[<span class="blink">•</span>]</span>
    <span class="mark-name">Leon Builds</span>
    <span class="mark-handle">/ by Leon Kelvin Li</span>
  </a>
  <nav class="nav-mid" id="navMid" aria-label="site">{navlinks}</nav>
  <div class="nav-end">
    <a class="btn btn-solid magnet" href="{contact}"{_contact_attrs(L)} data-evt="contact_click_{lang}_nav"><span>{e(L['contact_label'])}</span></a>
    <button class="burger" id="burger" aria-expanded="false" aria-controls="navMid" aria-label="Open menu"><span></span><span></span></button>
  </div>
</header>'''

    # sibling language pages — the internal links that make this a cluster
    others = ''.join(
        f'<a href="/{lang}/{SLUGS[(lang, k)]}">{e(o["h1_plain"] + " " + o["h1_em"])}</a>'
        for k, o in ctx['siblings'](lang, key))

    intro = ''.join(f'<p class="sub">{e(p)}</p>' for p in page['intro'])
    pains = ''.join(f'<li>{e(p)}</li>' for p in page['pains'])
    builds = ''.join(f'<li><svg class="ic"><use href="#ic-check"/></svg>{e(b)}</li>'
                     for b in page['build'])
    faq = '<div class="faq">' + ''.join(
        f'<details><summary>{e(q)}<i></i></summary><p>{e(a)}</p></details>'
        for q, a in faqs) + '</div>'

    wa_attr = _contact_attrs(L)
    # A button that copies a WeChat ID must be labelled with that ID. Using the
    # page's own CTA line here would leave a Chinese visitor tapping "tell me
    # what you need" and getting a clipboard they did not ask for.
    primary_label = L['contact_label'] if L['contact_kind'] == 'wechat' else page['cta_primary']

    body = f'''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    <p class="crumbs"><a href="{L['home']}">{e(L['crumb_home'])}</a> <i>/</i> <span>{e(page['h1_plain'])} {e(page['h1_em'])}</span></p>
    <h1 class="dsp">{e(page['h1_plain'])} <em>{e(page['h1_em'])}</em></h1>
    {intro}
    <p class="pricetag">{e(page['pricetag'])}</p>
    <div class="ctarow">
      <a class="btn btn-solid magnet" href="{contact}"{wa_attr} data-evt="contact_click_{lang}_{key}"><span>{e(primary_label)}</span><svg class="ic"><use href="#ic-arrow"/></svg></a>
      <a class="btn magnet" href="{call_href(lang)}" data-evt="call_click_{lang}_{key}"><span>{e(L['call_label'])}</span></a>
      <button class="btn magnet" type="button" data-assist-open data-assist-starter="{e(L['assist_starter'])}" data-evt="assist_open_{lang}_{key}"><span>{e(page['cta_secondary'])}</span></button>
    </div>
  </div>
</section>

<section class="sec">
  <div class="rail two-col">
    <div>
      <p class="label">{e(page['pains_label'])}</p>
      <ul class="plist">{pains}</ul>
    </div>
    <div>
      <p class="label">{e(page['build_label'])}</p>
      <ul class="blist">{builds}</ul>
    </div>
  </div>
</section>

<section class="sec">
  <div class="rail">
    <p class="label">{e(page['proof_label'])}</p>
    <div class="proofcard">
      <h2>{e(page['proof_title'])}</h2>
      <p class="sub">{e(page['proof_body'])}</p>
    </div>
  </div>
</section>

<section class="sec">
  <div class="rail">
    <p class="label">{e(page['faq_label'])}</p>
    {faq}
  </div>
</section>

<section class="sec">
  <div class="rail">
    <p class="sub">{e(page['close'])}</p>
    <div class="ctarow">
      <a class="btn btn-solid magnet" href="{contact}"{wa_attr} data-evt="contact_click_{lang}_{key}_end"><span>{e(primary_label)}</span><svg class="ic"><use href="#ic-arrow"/></svg></a>
      <a class="btn magnet" href="{call_href(lang)}" data-evt="call_click_{lang}_{key}_end"><span>{e(L['call_label'])}</span></a>
    </div>
    <p class="label" style="margin-top:2.5rem">{e(L['other_label'])}</p>
    <nav class="langmore">{others}</nav>
  </div>
</section>
</main>

<footer class="foot">
  <div class="rail foot-bar">
    <p>{L['foot']}</p>
    <p>{_footer_contacts(lang, L)}</p>
  </div>
</footer>
<script src="/app.js" defer></script>
<script src="/assist.js" defer></script></body></html>'''

    return head + nav + body


# ══════════════════════════════════════════════════════════════════
# THE BOOKING PAGE, PER LANGUAGE
# ══════════════════════════════════════════════════════════════════
#
# Every language service page ends with "book 15 minutes", and that button used
# to land on the English /call. A Portuguese-speaking owner who read three
# paragraphs in Portuguese hit an English page at the exact moment of deciding —
# the most expensive place on the site to lose someone.
#
# Written here rather than generated, because it is short and it is the page
# where a sentence that reads as translated costs the most.
#
# The Cal.com widget renders in its own locale; only the page around it is
# translated. That is still the difference between "this person speaks my
# language" and a wall of English at checkout.

CALL_COPY = {
    'pt': dict(
        slug='agendar',
        title='agendar uma conversa de 15 minutos | Leon Builds',
        desc='quinze minutos, de graça, em português. você conta o que está lento ou manual no seu negócio e Leon fala o que dá pra fazer e a partir de quanto sai.',
        h1_plain='quinze minutos pra saber se',
        h1_em='vale a pena fazer',
        intro=[
            'quinze minutos já dão pra saber se tem projeto aqui. você conta o que é lento ou manual na sua semana, e Leon fala o que faria, a partir de quanto sai, e também quando você não precisa dele.',
            'a conversa é em português, com a pessoa que escreve o código. não tem vendedor, não tem gerente de conta, e não tem compromisso nenhum depois.',
        ],
        pricetag='de graça · 15 minutos · disponibilidade em dias úteis (horário do pacífico) · você fala direto com Leon',
        label='o que acontece na conversa',
        bullets=[
            'você explica o problema do seu jeito, sem precisar de palavra técnica',
            'Leon pergunta o que você usa hoje e onde é que trava de verdade',
            'você sai com um número: o que dá pra fazer e a partir de quanto',
            'se a resposta certa for não fazer nada, Leon fala isso também',
        ],
        note='prefere não marcar horário? chame Leon no whatsapp ou ligue: (510) 826-7735.',
        crumb='agendar',
    ),
    'es': dict(
        slug='agendar',
        title='agendar una llamada de 15 minutos | Leon Builds',
        desc='quince minutos, gratis, en español. le cuentas a Leon qué es lento o manual en tu negocio y él te dice qué se puede hacer y desde cuánto sale.',
        h1_plain='quince minutos para saber si',
        h1_em='vale la pena hacerlo',
        intro=[
            'quince minutos alcanzan para saber si hay proyecto. le cuentas a Leon qué es lento o manual en tu semana, y él te dice qué haría, desde cuánto sale, y también cuándo no lo necesitas.',
            'la llamada es en español, con la persona que escribe el código. no hay vendedor, no hay ejecutivo de cuenta, y no queda ningún compromiso después.',
        ],
        pricetag='gratis · 15 minutos · disponibilidad entre semana (hora del pacífico) · hablas directo con Leon',
        label='qué pasa en la llamada',
        bullets=[
            'le explicas el problema a Leon a tu manera, sin necesidad de términos técnicos',
            'Leon te pregunta qué usas hoy y dónde se traba de verdad',
            'sales con un número: qué se puede hacer y desde cuánto',
            'si lo correcto es no hacer nada, Leon también te lo dice',
        ],
        note='¿prefieres no agendar? escríbele a Leon por whatsapp o llama al (510) 826-7735.',
        crumb='agendar',
    ),
    'zh': dict(
        slug='yuyue',
        title='预约 15 分钟通话 | Leon Builds',
        desc='免费 15 分钟，中文沟通。你说说生意里哪一块还在靠人工，Leon 告诉你能怎么做、大概从多少钱起。',
        h1_plain='十五分钟，先弄清楚',
        h1_em='这件事值不值得做',
        intro=[
            '十五分钟就够判断有没有必要做了。你说说每周哪些事情又慢又费人，Leon 告诉你他会怎么做、从多少钱起，以及什么时候你根本不需要找他。',
            '全程中文，直接跟写代码的人聊。没有销售，没有客户经理，聊完也没有任何后续负担。',
        ],
        pricetag='免费 · 15 分钟 · 工作日可约（太平洋时间）· 直接跟 Leon 聊',
        label='这十五分钟会聊什么',
        bullets=[
            '你用自己的话说问题就行，不用懂任何技术名词',
            'Leon 问你现在用什么、到底卡在哪一步',
            '你会拿到一个数字：能做成什么样、从多少钱起',
            '如果答案是不用改，Leon 也会直接这么说',
        ],
        note='不想约时间？直接发微信或打电话：(510) 826-7735。',
        crumb='预约',
    ),
}


def call_alternates():
    """/call and its three translations, all pointing at each other."""
    out = [('en', '/call')]
    for code, c in CALL_COPY.items():
        out.append((LANGS[code]['hreflang'], f"/{code}/{c['slug']}"))
    out.append(('x-default', '/call'))
    return out


def render_call(lang, booker, ctx):
    """The booking page in one language, wrapped around the same Cal.com embed
    the English page uses — the widget is the proven one, only the page is new."""
    import json
    e, BASE, FONTS, ICONS = ctx['e'], ctx['BASE'], ctx['FONTS'], ctx['ICONS']
    L, C = LANGS[lang], CALL_COPY[lang]
    path = f"/{lang}/{C['slug']}"
    contact = _contact_href(L)
    wa_attr = _contact_attrs(L)

    alts = ''.join(f'<link rel="alternate" hreflang="{hl}" href="{BASE}{href}">'
                   for hl, href in call_alternates())

    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "@id": f"{BASE}/#website",
         "name": "Leon Builds", "alternateName": "Leon Builds by Leon Kelvin Li",
         "url": f"{BASE}/"},
        {"@type": "WebPage", "@id": f"{BASE}{path}#webpage",
         "name": C['title'].split('|')[0].strip(), "description": C['desc'],
         "inLanguage": L['html_lang'], "url": f"{BASE}{path}",
         "isPartOf": {"@id": f"{BASE}/#website"},
         "mainEntity": {"@id": f"{BASE}{path}#service"}},
        {"@type": "Service", "@id": f"{BASE}{path}#service",
         "name": C['title'].split('|')[0].strip(),
         "description": C['desc'],
         "inLanguage": L['html_lang'],
         "provider": {"@id": f"{BASE}/#leon"},
         "areaServed": {"@type": "Country", "name": "United States"},
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
         "url": f"{BASE}{path}"},
        *_identity_schema_nodes(BASE),
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": L['crumb_home'],
             "item": BASE + L['home']},
            {"@type": "ListItem", "position": 2, "name": C['crumb'],
             "item": BASE + path}]},
    ]}

    navlinks = ''.join(
        f'<a href="{call_href(lang) if h == "/call" else h}"><i>[</i><span>{e(t)}</span><i>]</i></a>'
        for h, t in L['nav'])
    bullets = ''.join(f'<li><svg class="ic"><use href="#ic-check"/></svg>{e(b)}</li>'
                      for b in C['bullets'])
    intro = ''.join(f'<p class="sub">{e(p)}</p>' for p in C['intro'])

    return f'''<!DOCTYPE html>
<html lang="{L['html_lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(C['title'])}</title>
<meta name="description" content="{e(C['desc'])}">
<meta name="theme-color" content="#000000">
<meta name="color-scheme" content="dark">
<link rel="canonical" href="{BASE}{path}">
{alts}
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}{path}">
<meta property="og:title" content="{e(C['title'])}">
<meta property="og:description" content="{e(C['desc'])}">
<meta property="og:image" content="{BASE}/assets/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
{FONTS}
<link rel="stylesheet" href="/styles.css">
<link rel="stylesheet" href="/assist.css">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
</head>
<body class="call-page" data-assistant-launcher="hidden">{ICONS}<a class="skip" href="#main">{e(L['skip'])}</a>
<div class="progress" id="progress" aria-hidden="true"></div>
<div class="cursor" id="cursor" aria-hidden="true"><span></span></div>
<header class="nav" id="nav">
  <a class="mark" href="{L['home']}">
    <span class="mark-dot">[<span class="blink">•</span>]</span>
    <span class="mark-name">Leon Builds</span>
    <span class="mark-handle">/ by Leon Kelvin Li</span>
  </a>
  <nav class="nav-mid" id="navMid" aria-label="site">{navlinks}</nav>
  <div class="nav-end">
    <a class="btn btn-solid magnet" href="{contact}"{wa_attr} data-evt="contact_click_{lang}_call_nav"><span>{e(L['contact_label'])}</span></a>
    <button class="burger" id="burger" aria-expanded="false" aria-controls="navMid" aria-label="Open menu"><span></span><span></span></button>
  </div>
</header>

<main id="main">
<section class="sec page-hero">
  <div class="rail">
    <p class="crumbs"><a href="{L['home']}">{e(L['crumb_home'])}</a> <i>/</i> <span>{e(C['crumb'])}</span></p>
    <h1 class="dsp">{e(C['h1_plain'])} <em>{e(C['h1_em'])}</em></h1>
    {intro}
    <p class="pricetag">{e(C['pricetag'])}</p>
  </div>
</section>

<section class="sec">
  <div class="rail">
    <div class="callgrid">
    <div>
      <p class="label">{e(C['label'])}</p>
      <ul class="blist">{bullets}</ul>
      <p class="sub">{e(C['note'])}</p>
      <div class="ctarow">
        <a class="btn magnet" href="{contact}"{wa_attr} data-evt="contact_click_{lang}_call"><span>{e(L['contact_label'])}</span></a>
      </div>
    </div>
    <div>{booker}</div>
    </div>
  </div>
</section>
</main>

<footer class="foot">
  <div class="rail foot-bar">
    <p>{L['foot']}</p>
    <p>{_footer_contacts(lang, L)}</p>
  </div>
</footer>
<script src="/app.js" defer></script>
<script src="/assist.js" defer></script></body></html>'''
