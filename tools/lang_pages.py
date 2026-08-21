#!/usr/bin/env python3
"""Service pages in Portuguese, Spanish and Chinese.

The point of these pages is the one thing an agency cannot copy: the person
who writes the code also speaks the language the owner explains the problem
in. "web development" is unwinnable — Toptal and Clutch own it — but
"criar site para restaurante nos estados unidos" is nearly uncontested, and
the person searching it is ready to buy.

The copy is written natively, never translated, and lives in
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

# Everything language-specific that is chrome rather than copy.
LANGS = {
    'pt': dict(
        html_lang='pt-BR', hreflang='pt-BR', home='/pt',
        nav=[('/pt#faco', 'o que eu faço'), ('/pt#precos', 'preços'),
             ('/pt#feito', 'o que eu já fiz'), ('/call', 'agendar 15 min'),
             ('/', 'english')],
        contact_kind='wa',
        wa_text='Oi%20Leon%2C%20vi%20o%20seu%20site.%20Meu%20neg%C3%B3cio%20%C3%A9%3A%20',
        contact_label='whatsapp',
        skip='pular para o conteúdo',
        crumb_home='início',
        other_label='outros serviços',
        foot='© <span id="yr">2026</span> <span class="keepcase">Leon Kelvin Li</span> · california · atendo negócios nos estados unidos inteiros · <a href="/">english</a> · <a href="/es">español</a> · <a href="/zh">中文</a>',
        assist_starter='pode responder em português. meu negócio é o seguinte: ',
        call_label='agendar 15 minutos',
    ),
    'es': dict(
        html_lang='es', hreflang='es', home='/es',
        nav=[('/es#hago', 'lo que hago'), ('/es#precios', 'precios'),
             ('/es#hecho', 'lo que ya hice'), ('/call', 'agendar 15 min'),
             ('/', 'english')],
        contact_kind='wa',
        wa_text='Hola%20Leon%2C%20vi%20tu%20p%C3%A1gina.%20Mi%20negocio%20es%3A%20',
        contact_label='whatsapp',
        skip='saltar al contenido',
        crumb_home='inicio',
        other_label='otros servicios',
        foot='© <span id="yr">2026</span> <span class="keepcase">Leon Kelvin Li</span> · california · atiendo negocios en todo estados unidos · <a href="/">english</a> · <a href="/pt">português</a> · <a href="/zh">中文</a>',
        assist_starter='puedes responder en español. mi negocio es el siguiente: ',
        call_label='agendar 15 minutos',
    ),
    'zh': dict(
        html_lang='zh-Hans', hreflang='zh', home='/zh',
        nav=[('/zh#zuo', '我能做什么'), ('/zh#jiage', '价格'),
             ('/zh#zuoguo', '做过的东西'), ('/call', '预约 15 分钟'),
             ('/', 'english')],
        contact_kind='email',
        contact_label='联系 leon',
        skip='跳到正文',
        crumb_home='首页',
        other_label='其他服务',
        foot='© <span id="yr">2026</span> <span class="keepcase">Leon Kelvin Li</span> · 加州 · 全美国都接 · <a href="/">english</a> · <a href="/es">español</a> · <a href="/pt">português</a>',
        assist_starter='请用中文回复。我的生意是这样的：',
        call_label='预约 15 分钟',
    ),
}

WA = 'https://wa.me/15108267735?text='
MAIL = 'mailto:leondragon3798@gmail.com'


def _contact_href(L):
    return WA + L['wa_text'] if L['contact_kind'] == 'wa' else MAIL + '?subject=project'


def _alternates(key, path):
    """The four-way hreflang cluster for one service, plus x-default."""
    out = [('en', EN_COUNTERPART[key])]
    for code, L in LANGS.items():
        out.append((L['hreflang'], f'/{code}/{SLUGS[(code, key)]}'))
    out.append(('x-default', EN_COUNTERPART[key]))
    return out


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
        {"@type": "Service",
         "@id": f"{BASE}{path}#service",
         "name": page['title'].split('|')[0].strip(),
         "description": page['metaDescription'],
         "serviceType": page['h1_plain'] + ' ' + page['h1_em'],
         "inLanguage": L['hreflang'],
         "provider": {"@id": f"{BASE}/#leon"},
         "areaServed": {"@type": "Country", "name": "United States"},
         "availableLanguage": ["English", "Spanish", "Portuguese", "Chinese"],
         "url": f"{BASE}{path}"},
        {"@type": "Person", "@id": f"{BASE}/#leon", "name": "Leon Kelvin Li",
         "url": f"{BASE}/about"},
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

    navlinks = ''.join(f'<a href="{h}"><i>[</i><span>{e(t)}</span><i>]</i></a>'
                       for h, t in L['nav'])
    nav = f'''{ICONS}<a class="skip" href="#main">{e(L['skip'])}</a>
<div class="progress" id="progress" aria-hidden="true"></div>
<div class="cursor" id="cursor" aria-hidden="true"><span></span></div>
<header class="nav" id="nav">
  <a class="mark" href="{L['home']}">
    <span class="mark-dot">[<span class="blink">•</span>]</span>
    <span class="mark-name">Leon Kelvin Li</span>
    <span class="mark-handle">/ Noctilucenty</span>
  </a>
  <nav class="nav-mid" id="navMid" aria-label="site">{navlinks}</nav>
  <div class="nav-end">
    <a class="btn btn-solid magnet" href="{contact}"{' target="_blank" rel="noopener"' if L['contact_kind'] == 'wa' else ''} data-evt="contact_click_{lang}_nav"><span>{e(L['contact_label'])}</span></a>
    <button class="burger" id="burger" aria-expanded="false" aria-controls="navMid" aria-label="menu"><span></span><span></span></button>
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

    wa_attr = ' target="_blank" rel="noopener"' if L['contact_kind'] == 'wa' else ''

    body = f'''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    <p class="crumbs"><a href="{L['home']}">{e(L['crumb_home'])}</a> <i>/</i> <span>{e(page['h1_plain'])} {e(page['h1_em'])}</span></p>
    <h1 class="dsp">{e(page['h1_plain'])} <em>{e(page['h1_em'])}</em></h1>
    {intro}
    <p class="pricetag">{e(page['pricetag'])}</p>
    <div class="ctarow">
      <a class="btn btn-solid magnet" href="{contact}"{wa_attr} data-evt="contact_click_{lang}_{key}"><span>{e(page['cta_primary'])}</span><svg class="ic"><use href="#ic-arrow"/></svg></a>
      <a class="btn magnet" href="/call" data-evt="call_click_{lang}_{key}"><span>{e(L['call_label'])}</span></a>
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
      <a class="btn btn-solid magnet" href="{contact}"{wa_attr} data-evt="contact_click_{lang}_{key}_end"><span>{e(page['cta_primary'])}</span><svg class="ic"><use href="#ic-arrow"/></svg></a>
      <a class="btn magnet" href="/call" data-evt="call_click_{lang}_{key}_end"><span>{e(L['call_label'])}</span></a>
    </div>
    <p class="label" style="margin-top:2.5rem">{e(L['other_label'])}</p>
    <nav class="langmore">{others}</nav>
  </div>
</section>
</main>

<footer class="foot">
  <div class="rail foot-bar">
    <p>{L['foot']}</p>
    <p><a href="mailto:leondragon3798@gmail.com">leondragon3798@gmail.com</a> · <a href="tel:+15108267735">(510) 826-7735</a></p>
  </div>
</footer>
<script src="/app.js" defer></script>
<script src="/assist.js" defer></script></body></html>'''

    return head + nav + body
