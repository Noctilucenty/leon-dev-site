'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const ROOT = path.join(__dirname, '..');
const read = file => fs.readFileSync(path.join(ROOT, file), 'utf8');

const html = read('index.html');
const css = read('styles.css');
const js = read('app.js');
const assist = read('assist.js');

function attributes(tag) {
  const result = Object.create(null);
  for (const match of tag.matchAll(/([\w:-]+)\s*=\s*(["'])(.*?)\2/gs)) {
    result[match[1].toLowerCase()] = match[3];
  }
  return result;
}

function plainText(source) {
  return source
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&(?:apos|#39|#x27);/gi, "'")
    .replace(/&(?:quot|#34|#x22);/gi, '"')
    .replace(/&amp;/gi, '&')
    .replace(/&nbsp;/gi, ' ')
    .replace(/&rarr;|&#8594;|&#x2192;/gi, '→')
    .replace(/\s+/g, ' ')
    .trim();
}

function elementWithId(source, tag, id) {
  const opener = new RegExp(`<${tag}\\b(?=[^>]*\\bid\\s*=\\s*(["'])${id}\\1)[^>]*>`, 'i');
  const match = opener.exec(source);
  assert.ok(match, `homepage has a ${tag}#${id}`);
  const end = source.indexOf(`</${tag}>`, match.index);
  assert.notEqual(end, -1, `${tag}#${id} is closed`);
  return source.slice(match.index, end + `</${tag}>`.length);
}

function mainSource(source = html) {
  const match = source.match(/<main\b[^>]*>[\s\S]*?<\/main>/i);
  assert.ok(match, 'homepage has a main landmark');
  return match[0];
}

function linksIn(source) {
  return Array.from(source.matchAll(/<a\b[^>]*>[\s\S]*?<\/a>/gi), match => {
    const opener = match[0].slice(0, match[0].indexOf('>') + 1);
    return { attrs: attributes(opener), text: plainText(match[0]) };
  });
}

function topLevelSections(source) {
  const main = mainSource(source);
  const sections = [];
  let depth = 0;
  for (const match of main.matchAll(/<\/?section\b[^>]*>/gi)) {
    if (/^<\/section/i.test(match[0])) {
      depth -= 1;
    } else {
      if (depth === 0) sections.push(attributes(match[0]));
      depth += 1;
    }
  }
  assert.equal(depth, 0, 'homepage section tags are balanced');
  return sections;
}

function initiallyVisibleMainText(source) {
  let main = mainSource(source);
  main = main.replace(/<details\b[^>]*>[\s\S]*?<summary\b[^>]*>([\s\S]*?)<\/summary>[\s\S]*?<\/details>/gi, '$1');
  main = main.replace(/<template\b[\s\S]*?<\/template>/gi, ' ');
  return plainText(main);
}

function articleContaining(source, heading) {
  const articles = source.match(/<article\b[\s\S]*?<\/article>/gi) || [];
  const needle = heading.toLowerCase();
  const result = articles.find(article => plainText(article).toLowerCase().includes(needle));
  assert.ok(result, `homepage includes the ${heading} card`);
  return result;
}

function elementsWithClass(source, tag, className) {
  const blocks = source.match(new RegExp(`<${tag}\\b(?=[^>]*\\bclass\\s*=\\s*(["'])[^"']*\\b${className}\\b[^"']*\\1)[\\s\\S]*?<\\/${tag}>`, 'gi')) || [];
  return blocks;
}

function mediaBlocks(source) {
  const blocks = [];
  const startRe = /@media\s*\(([^)]*)\)\s*\{/gi;
  let start;
  while ((start = startRe.exec(source))) {
    let depth = 1;
    let cursor = startRe.lastIndex;
    while (cursor < source.length && depth) {
      if (source[cursor] === '{') depth += 1;
      else if (source[cursor] === '}') depth -= 1;
      cursor += 1;
    }
    blocks.push({ condition: start[1], body: source.slice(startRe.lastIndex, cursor - 1) });
    startRe.lastIndex = cursor;
  }
  return blocks;
}

function schemaBlocks(source) {
  return Array.from(
    source.matchAll(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi),
    match => match[1]
  );
}

function testimonialPublication() {
  return JSON.parse(read('content/client-success/testimonial-publication.json')).approved_testimonials;
}

test('homepage is a short seven-section-or-less service funnel in the approved order', () => {
  const sections = topLevelSections(html);
  assert.ok(sections.length <= 7, `homepage has ${sections.length} major sections; maximum is 7`);

  const ids = sections.map(attrs => attrs.id).filter(Boolean);
  const requiredOrder = ['top', 'services', 'work', 'process', 'faq', 'contact'];
  let cursor = -1;
  for (const id of requiredOrder) {
    const next = ids.indexOf(id, cursor + 1);
    assert.notEqual(next, -1, `homepage includes #${id} in the approved conversion order`);
    cursor = next;
  }

  const visible = initiallyVisibleMainText(html);
  const words = visible.match(/[\p{L}\p{N}][\p{L}\p{N}'’+&/-]*/gu) || [];
  assert.ok(words.length <= 600, `homepage has ${words.length} initially visible main words; maximum is 600`);

  assert.doesNotMatch(mainSource(), /\bhidden(?:\s|>)/i, 'homepage does not retain archival content as hidden DOM');
  assert.doesNotMatch(mainSource(), /long-case|work-archive|legacy-work|archive-hidden|sr-only-work/i);
});

test('navigation has one coherent brand, service path, and no stale homepage anchors', () => {
  const header = html.match(/<header\b[^>]*>[\s\S]*?<\/header>/i)?.[0] || '';
  assert.ok(header, 'homepage has a header');
  const links = linksIn(header);
  const visible = plainText(header);

  assert.match(visible, /Leon Builds/i);
  assert.match(visible, /by Leon Kelvin Li/i);
  assert.doesNotMatch(visible, /Noctilucenty/i);
  assert.ok(links.some(link => link.attrs.href === '#services' && /services\s*&\s*pricing/i.test(link.text)), 'nav links to visible services and pricing');
  assert.ok(links.some(link => link.attrs.href === '/work' && /\bwork\b/i.test(link.text)), 'nav links to the dedicated work route');
  assert.ok(links.some(link => link.attrs.href === '/about' && /\babout\b/i.test(link.text)), 'nav links to About');
  assert.ok(links.some(link => link.attrs.href === '/quote' && /get a fixed quote/i.test(link.text)), 'nav has the one quote CTA');
  assert.doesNotMatch(header, /href=["']#(?:fix|outcomes|pricing|work)["']/i, 'old homepage anchors are not still advertised');

  const ids = new Set(Array.from(html.matchAll(/\bid\s*=\s*(["'])([^"']+)\1/gi), match => match[2]));
  for (const link of linksIn(html)) {
    if (!link.attrs.href || !link.attrs.href.startsWith('#')) continue;
    assert.ok(ids.has(link.attrs.href.slice(1)), `homepage link ${link.attrs.href} has a real target`);
  }
});

test('hero passes the five-second offer test with one filled CTA and one secondary link', () => {
  const hero = elementWithId(html, 'section', 'top');
  const visible = plainText(hero);
  const copy = elementsWithClass(hero, 'div', 'hero-copy')[0] || '';
  const actions = elementsWithClass(copy, 'div', 'hero-cta')[0] || '';
  const links = linksIn(actions);
  const filled = links.filter(link => /(?:^|\s)(?:btn-solid|btn-primary|primary-cta)(?:\s|$)/.test(link.attrs.class || ''));

  assert.match(visible, /websites\s*\+\s*lead follow-up for small businesses/i);
  assert.match(visible, /turn website visitors into calls, bookings, and quote requests\./i);
  assert.match(visible, /I build fast business websites and simple follow-up systems so new inquiries are easier to capture, see, and respond to\./i);
  assert.match(visible, /websites from \$300/i);
  assert.match(visible, /website \+ follow-up from \$1,500/i);
  assert.match(visible, /fixed price before work begins/i);
  assert.match(visible, /direct with Leon Kelvin Li/i);
  assert.match(visible, /written scope and fixed price/i);
  assert.match(visible, /agreed source and account handoff/i);
  assert.ok(linksIn(hero).some(link => link.attrs.href === '/about' && /direct with Leon Kelvin Li/i.test(link.text)));

  assert.equal(filled.length, 1, 'hero has exactly one filled CTA');
  assert.equal(filled[0].attrs.href, '/quote');
  assert.match(filled[0].text, /get a fixed quote/i);
  assert.equal(links.length, 2, 'hero has one primary CTA and one secondary link');
  assert.ok(links.some(link => link.attrs.href === '/work' && /see real work/i.test(link.text)), 'hero secondary link opens /work');

  assert.doesNotMatch(copy, /curio|app store|github/i, 'product proof does not replace the buyer offer');
  assert.doesNotMatch(hero, /<video\b[^>]*\bautoplay/i, 'hero has no autoplay media');
});

test('hero pairs the offer with three immediately verifiable trust paths', () => {
  const hero = elementWithId(html, 'section', 'top');
  const panel = elementsWithClass(hero, 'aside', 'hero-proof')[0] || '';
  const visible = plainText(panel);
  const links = linksIn(panel);

  assert.match(visible, /public proof/i);
  assert.match(visible, /operational business system/i);
  assert.match(visible, /live app store product/i);
  assert.match(visible, /Leon Kelvin Li/i);
  assert.equal(links.length, 3, 'proof panel has exactly three verification paths');
  assert.ok(links.some(link => link.attrs.href === '/work#work-site-intelligence'));
  assert.ok(links.some(link => link.attrs.href === '/work#work-curio-public'));
  assert.ok(links.some(link => link.attrs.href === '/about'));
  assert.doesNotMatch(visible, /revenue|bookings generated|guaranteed|five[- ]star/i);
});

test('services target exposes exactly three canonical starting offers', () => {
  const services = elementWithId(html, 'section', 'services');
  const cards = elementsWithClass(services, 'a', 'offer-card');
  assert.equal(cards.length, 3, 'homepage shows exactly three primary service cards');
  assert.match(plainText(services), /three practical ways to start\./i);

  const expected = [
    ['Website + lead follow-up', '$1,500', '/missed-lead-recovery', 'See the 10-day scope'],
    ['Business website', '$300', '/services/websites', 'See website scope'],
    ['Workflow automation', '$500', '/services/business-automation', 'See automation scope'],
  ];
  for (const [name, price, href, cta] of expected) {
    const card = cards.find(item => plainText(item).toLowerCase().includes(name.toLowerCase()));
    assert.ok(card, `homepage includes the ${name} card`);
    assert.match(plainText(card), new RegExp(`from \\${price}`, 'i'), `${name} shows from ${price}`);
    const cardLink = linksIn(card)[0];
    assert.equal(cardLink.attrs.href, href, `${name} opens its focused scope`);
    assert.match(cardLink.text, new RegExp(cta.replace('See website scope', 'See (?:the exact )?website scope'), 'i'), `${name} has the approved scope link`);
  }

  const website = plainText(cards.find(item => plainText(item).toLowerCase().includes('business website')) || '');
  assert.match(website, /phone-first/i);
  assert.match(website, /one clear (?:call|booking|order|quote).*(?:path|action)|one clear action/i, '$300 offer is kept to a narrow presence-site scope');
  assert.doesNotMatch(website, /follow-up|automation|dashboard|\bapp\b/i, '$300 offer does not promise custom-system scope');

  const visible = plainText(services);
  assert.match(visible, /starting prices are scope floors, not instant quotes/i);
  assert.match(visible, /written fixed price before work begins/i);
  assert.ok(linksIn(services).some(link => link.attrs.href === '/services/mobile-apps' && /mobile app development/i.test(link.text)), 'app demand gets one direct secondary path without competing in the hero');
  assert.equal((visible.match(/\$\s*(?:300|500|1,500)\b/g) || []).length, 3, 'each canonical price appears once in the section');
  assert.doesNotMatch(visible, /\$\s*1,350\b|first two projects|pilot price/i, 'untracked discount is not published');
});

test('at least two proof cards demonstrate business-facing systems and the archive lives on /work', () => {
  const proof = elementWithId(html, 'section', 'work');
  const articles = proof.match(/<article\b[\s\S]*?<\/article>/gi) || [];
  assert.equal(articles.length, 3, 'homepage shows exactly three proof cards');

  const orderedText = articles.map(article => plainText(article).toLowerCase());
  assert.ok(orderedText.some(text => /operational system|live product|public (?:demo|prototype)|prototype/.test(text)), 'proof cards state current status');
  assert.match(orderedText.join('\n'), /the home screen/);
  assert.match(orderedText.join('\n'), /prototype.*mock payments/);
  assert.match(orderedText.join('\n'), /curio/);
  assert.match(orderedText.join('\n'), /live product.*app store/);

  const businessFacing = orderedText.filter(text => /website|business|operator|order|menu|quote|estimate|lead|follow-up|workflow|disclosure|document|handoff|time-saving/.test(text));
  assert.ok(businessFacing.length >= 2, `${businessFacing.length}/3 proof cards demonstrate business-facing work; at least 2 are required`);

  for (const [index, card] of articles.entries()) {
    assert.equal(linksIn(card).length, 1, `proof card ${index + 1} has one action`);
    assert.match(linksIn(card)[0].text, /view (?:the )?(?:proof|case study)|open (?:the )?(?:proof|case study)|verify the live product/i);
    assert.doesNotMatch(plainText(card), /react|typescript|postgres|capacitor|test suite|architecture|tech stack/i);
  }

  assert.ok(fs.existsSync(path.join(ROOT, 'work.html')), '/work has a source page');
  const work = read('work.html');
  assert.match(work, /<link rel=["']canonical["'] href=["']https:\/\/leonbuilds\.org\/work["']>/i);
  assert.match(work, /<h1\b/i);
  for (const name of ['The Home Screen', 'Loqol disclosures', 'Curio']) assert.match(plainText(work), new RegExp(name, 'i'));
  assert.match(read('sitemap.xml'), /<loc>https:\/\/leonbuilds\.org\/work<\/loc>/i);
});

test('testimonials remain conditional and fail closed at the public surface', () => {
  const publication = testimonialPublication();
  const marker = html.match(/<!-- TESTIMONIALS:START -->([\s\S]*?)<!-- TESTIMONIALS:END -->/);
  assert.ok(marker, 'homepage keeps the generator-owned testimonial markers');
  const cards = marker[1].match(/<article\b(?=[^>]*\bdata-testimonial-id=)[\s\S]*?<\/article>/gi) || [];
  const header = html.match(/<header\b[^>]*>[\s\S]*?<\/header>/i)?.[0] || '';
  const navHasReviews = linksIn(header).some(link => link.attrs.href === '/reviews' && /\breviews?\b/i.test(link.text));
  const reviewsFile = fs.existsSync(path.join(ROOT, 'reviews.html'));
  const sitemapHasReviews = /<loc>https:\/\/leonbuilds\.org\/reviews<\/loc>/i.test(read('sitemap.xml'));

  if (publication.length === 0) {
    assert.equal(marker[1].trim(), '', 'zero releases render no review section or placeholder');
    assert.equal(navHasReviews, false, 'zero releases render no Reviews nav link');
    assert.equal(reviewsFile, false, 'zero releases do not create a hollow /reviews route');
    assert.equal(sitemapHasReviews, false, 'zero releases do not advertise /reviews');
    assert.doesNotMatch(html, /id=["'](?:testimonials|reviews)["']|testimonial-(?:card|stars|person|project)|5 out of 5 stars|★★★★★/i);
  } else {
    assert.equal(cards.length, Math.min(3, publication.length), 'homepage renders only the released feedback count, capped at three');
    const renderedIds = cards.map(card => attributes(card.slice(0, card.indexOf('>') + 1))['data-testimonial-id']);
    assert.equal(new Set(renderedIds).size, renderedIds.length, 'released homepage reviews are not duplicated');
    assert.ok(renderedIds.every(id => publication.some(item => item.id === id)), 'every rendered review is allowlisted');
    if (publication.length >= 3) {
      assert.equal(navHasReviews, true, 'three releases make Reviews discoverable');
      assert.equal(reviewsFile, true, 'three releases create /reviews');
      assert.equal(sitemapHasReviews, true, 'three releases advertise /reviews');
    } else {
      assert.equal(navHasReviews, false, 'one or two releases do not advertise a missing reviews route');
      assert.equal(reviewsFile, false, 'one or two releases stay on the homepage');
      assert.equal(sitemapHasReviews, false);
    }
  }

  assert.doesNotMatch(schemaBlocks(html).join('\n'), /aggregateRating|reviewRating|ratingValue|"@type"\s*:\s*"Review"/i, 'homepage emits no review or rating schema');
});

test('process, personal trust, FAQ, and final CTA each do one job', () => {
  const process = elementWithId(html, 'section', 'process');
  const processText = plainText(process);
  assert.match(processText, /from problem to handoff in three steps/i);
  assert.equal((process.match(/<li\b[\s\S]*?<\/li>/gi) || []).length, 3, 'process is exactly three steps');
  assert.match(processText, /broken, manual, or missing/i);
  assert.match(processText, /scope.*fixed price.*timeline/is);
  assert.match(processText, /review.*launch.*agreed (?:source|handoff)/is);
  assert.match(processText, /agreed source, accounts, and setup notes/i);

  const faq = elementWithId(html, 'section', 'faq');
  const details = faq.match(/<details\b[\s\S]*?<\/details>/gi) || [];
  assert.equal(details.length, 4, 'homepage keeps exactly four collapsed FAQs');
  assert.ok(details.every(item => !/<details\b[^>]*\bopen(?:\s|>)/i.test(item)), 'FAQs are collapsed initially');
  const questions = details.map(item => plainText(item.match(/<summary\b[^>]*>[\s\S]*?<\/summary>/i)?.[0] || ''));
  assert.deepEqual(questions, [
    'How much will my project cost?',
    'How long will it take?',
    'Can you work with the tools we already use?',
    'What happens after launch?',
  ]);

  const contact = elementWithId(html, 'section', 'contact');
  assert.match(plainText(contact), /tell me what is slowing the business down/i);
  assert.ok(linksIn(contact).some(link => link.attrs.href === '/quote' && /tell me what you need|get a fixed quote/i.test(link.text)));
  assert.ok(linksIn(contact).some(link => /^\/call(?:\?|$)/.test(link.attrs.href || '') && /book 15 minutes/i.test(link.text)));
  const filled = linksIn(contact).filter(link => /(?:^|\s)(?:btn-solid|btn-primary|primary-cta)(?:\s|$)/.test(link.attrs.class || ''));
  assert.equal(filled.length, 1, 'final CTA section has exactly one filled action');
});

test('homepage structured data stays factual and matches the focused offer', () => {
  const blocks = schemaBlocks(html);
  assert.ok(blocks.length > 0, 'homepage includes JSON-LD');
  const nodes = blocks.flatMap(block => {
    const parsed = JSON.parse(block);
    return parsed['@graph'] || [parsed];
  });
  const person = nodes.find(node => node['@type'] === 'Person');
  const business = nodes.find(node => node['@type'] === 'Organization');
  const website = nodes.find(node => node['@type'] === 'WebSite');
  assert.equal(person.jobTitle, 'Independent Software Developer');
  assert.doesNotMatch(person.description, /student|college|university/i);
  assert.equal(person.email, undefined, 'unverified domain email and personal Gmail stay out of Person schema');
  assert.equal(business.name, 'Leon Builds');
  assert.equal(business.contactPoint.email, 'leondragon3798@gmail.com');
  assert.deepEqual(business.contactPoint.availableLanguage, ['en', 'zh', 'pt-BR', 'es']);
  assert.equal(website.name, 'Leon Builds');
  assert.match(JSON.stringify(business.hasOfferCatalog), /iOS and Android app development/i);
  assert.ok(!nodes.some(node => node['@type'] === 'ProfessionalService'), 'unverified LocalBusiness-style schema is absent');
  assert.doesNotMatch(JSON.stringify(nodes), /aggregateRating|reviewRating|ratingValue|Noctilucenty/i);
});

test('homepage has responsive touch, keyboard, media, and motion safeguards', () => {
  assert.equal((html.match(/<h1\b/gi) || []).length, 1, 'homepage has one H1');
  assert.match(html, /<a\b[^>]*class=["'][^"']*skip[^"']*["'][^>]*href=["']#main["']/i, 'keyboard users have a skip link');
  assert.match(css, /:focus-visible\s*\{/i, 'keyboard focus is explicitly visible');
  assert.match(css, /@media\s*\(prefers-reduced-motion\s*:\s*reduce\)/i, 'reduced-motion preference is respected');
  assert.match(css, /(?:font-size\s*:\s*16px|font-size\s*:\s*1rem)/i, 'body copy has a 16px-or-equivalent base');
  assert.match(css, /min-height\s*:\s*44px/i, 'primary controls have a 44px touch floor');
  assert.match(css, /\.burger\s*\{[^}]*width\s*:\s*44px[^}]*height\s*:\s*44px/i,
    'mobile menu control keeps a 44px touch target');
  assert.match(css, /\.buyer-proof-card figure\s*\{[^}]*width\s*:\s*100%[^}]*max-width\s*:\s*100%[^}]*min-width\s*:\s*0/i,
    'proof media cannot use its intrinsic image width to overflow a phone card');
  assert.match(css, /\.buyer-proof-card figure img\s*\{[^}]*display\s*:\s*block[^}]*width\s*:\s*100%[^}]*max-width\s*:\s*100%[^}]*min-width\s*:\s*0/i,
    'proof images stay bounded to the proof card');
  assert.match(css, /\.proof-status\s*\{[^}]*font-size\s*:\s*12px/i,
    'proof status labels remain readable on mobile');

  const responsive = mediaBlocks(css).some(block => {
    const max = block.condition.match(/max-width\s*:\s*(\d+)px/i);
    return max && Number(max[1]) <= 600;
  });
  assert.ok(responsive, 'phone layout has an explicit <=600px breakpoint');

  for (const match of mainSource().matchAll(/<img\b[^>]*>/gi)) {
    const attrs = attributes(match[0]);
    assert.ok(Object.hasOwn(attrs, 'alt'), `image has alt text: ${match[0].slice(0, 100)}`);
    if (!/hero/i.test(attrs.class || '')) assert.equal(attrs.loading, 'lazy', 'below-fold images lazy-load');
  }
  assert.doesNotMatch(html, /\bid\s*=\s*(["'])cursor\1|\bclass\s*=\s*(["'])[^"']*\bcursor\b/i);
  assert.doesNotMatch(js, /#cursor\b|\.cursor\b|\bhas-cursor\b|custom cursor/i);
  assert.doesNotMatch(css, /\.has-cursor\b|(^|[,}])\s*\.cursor\b/im);
});

test('homepage suppresses only the floating assistant launcher and close cannot restore it', () => {
  assert.match(html, /<body\b[^>]*\bdata-assistant-launcher=["']hidden["']/i);
  assert.match(assist, /var launcherEnabled = document\.body\.getAttribute\('data-assistant-launcher'\) !== 'hidden'/);
  assert.match(assist, /document\.body\.appendChild\(panel\);\s*launch\.hidden = !launcherEnabled;/);
  assert.match(assist, /function close\(\)\s*\{\s*panel\.hidden = true; launch\.hidden = !launcherEnabled;/);
  assert.match(assist, /closest\('\[data-assist-open\]'\)/, 'explicit, contextual assistant triggers remain supported');
  assert.doesNotMatch(read('quote.html'), /data-assist-open/, 'quote page keeps the two-field inquiry path free of a competing helper');
});
