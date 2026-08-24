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

function attributes(tag) {
  const result = Object.create(null);
  for (const match of tag.matchAll(/([\w:-]+)\s*=\s*(["'])(.*?)\2/gs)) {
    result[match[1].toLowerCase()] = match[3];
  }
  return result;
}

function classTokens(attrs) {
  return (attrs.class || '').split(/\s+/).filter(Boolean);
}

function plainText(source) {
  return source
    .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&(?:apos|#39|#x27);/gi, "'")
    .replace(/&(?:quot|#34|#x22);/gi, '"')
    .replace(/&amp;/gi, '&')
    .replace(/&nbsp;/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function sectionLandmarks(source) {
  const landmarks = [];
  for (const match of source.matchAll(/<section\b[^>]*>/gi)) {
    const attrs = attributes(match[0]);
    const classes = classTokens(attrs);
    let name = null;
    if (attrs.id === 'top' || classes.includes('hero')) name = 'hero';
    else if (classes.includes('proof-strip')) name = 'proof';
    else if (attrs.id === 'fix' || attrs.id === 'outcomes') name = 'outcomes';
    else if (['work', 'testimonials', 'services', 'process', 'pricing', 'about', 'faq', 'contact'].includes(attrs.id)) name = attrs.id;
    if (name) landmarks.push({ name, index: match.index });
  }
  return landmarks;
}

function sectionWithId(source, id) {
  const opener = new RegExp(`<section\\b(?=[^>]*\\bid\\s*=\\s*(["'])${id}\\1)[^>]*>`, 'i');
  const match = opener.exec(source);
  assert.ok(match, `homepage has a ${id} section`);
  const end = source.indexOf('</section>', match.index);
  assert.notEqual(end, -1, `${id} section is closed`);
  return source.slice(match.index, end + '</section>'.length);
}

function articleContaining(source, heading) {
  const articles = source.match(/<article\b[\s\S]*?<\/article>/gi) || [];
  const needle = heading.toLowerCase();
  const result = articles.find(article => plainText(article).toLowerCase().includes(needle));
  assert.ok(result, `homepage includes the ${heading} proof card`);
  return result;
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

function navBookRules(source) {
  return Array.from(source.matchAll(/\.nav-mid\s+(?:>\s*)?\.nav-book\s*\{([^}]*)\}/gi), match => match[1]);
}

test('homepage follows the B2B conversion section order', () => {
  const names = sectionLandmarks(html).map(item => item.name);
  const expected = ['hero', 'proof', 'outcomes', 'work', 'services', 'pricing', 'process', 'about', 'faq', 'contact'];
  let cursor = -1;
  for (const name of expected) {
    const next = names.indexOf(name, cursor + 1);
    assert.notEqual(next, -1, `homepage includes ${name} after ${expected[Math.max(0, expected.indexOf(name) - 1)]}`);
    cursor = next;
  }

  const workIds = html.match(/\bid\s*=\s*(["'])work\1/gi) || [];
  assert.equal(workIds.length, 1, 'homepage has exactly one id="work" landmark');
});

test('unreleased feedback and supplied ratings are absent from the homepage', () => {
  assert.doesNotMatch(html, /id=["']testimonials["']/i);
  assert.doesNotMatch(html, /href=["']#testimonials["']/i);
  assert.doesNotMatch(html, /testimonial-(?:card|stars|person|project)/i);
  assert.doesNotMatch(html, /5 out of 5 stars|★★★★★|direct client reviews?/i);
  const schemaBlocks = Array.from(html.matchAll(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi), match => match[1]);
  assert.ok(schemaBlocks.length > 0, 'homepage includes structured data');
  assert.doesNotMatch(schemaBlocks.join('\n'), /aggregateRating|reviewRating|ratingValue/i, 'no rating schema is emitted');
});

test('verifiable public work is discoverable before service detail', () => {
  const nav = sectionWithId(html.replace('<header class="nav"', '<section id="site-nav" class="nav"').replace('</header>', '</section>'), 'site-nav');
  const navLinks = Array.from(nav.matchAll(/<a\b[^>]*>[\s\S]*?<\/a>/gi), match => {
    const attrs = attributes(match[0].slice(0, match[0].indexOf('>') + 1));
    return { href: attrs.href, text: plainText(match[0]).toLowerCase() };
  });
  assert.ok(navLinks.some(link => link.href === '#work' && link.text === '[ work ]'), 'desktop and mobile navigation link directly to work');
  assert.ok(!navLinks.some(link => link.href === '#testimonials'), 'navigation does not imply unreleased reviews exist');

  const hero = sectionWithId(html, 'top');
  assert.match(hero, /href=["']#work["'][^>]*data-evt=["']hero_work_click["']/i, 'hero links directly to public work');
  assert.match(plainText(hero), /see shipped work and public demos/i, 'hero offers inspectable proof as the secondary step');

  const landmarks = sectionLandmarks(html).map(item => item.name);
  assert.ok(landmarks.indexOf('proof') < landmarks.indexOf('outcomes'), 'verified proof appears before the service explanation');
  assert.ok(landmarks.indexOf('proof') < landmarks.indexOf('work'), 'proof strip appears before the long case-study section');

  const workIndex = navLinks.findIndex(link => link.href === '#work');
  const servicesIndex = navLinks.findIndex(link => link.href === '#services');
  assert.ok(workIndex >= 0 && workIndex < servicesIndex, 'navigation anchors follow homepage section order');
  assert.ok(navLinks.some(link => link.href === '#pricing' && link.text === '[ pricing ]'), 'navigation links directly to pricing information');
});

test('hero offers the two plain-language next steps', () => {
  const hero = sectionWithId(html, 'top');
  const links = Array.from(hero.matchAll(/<a\b[^>]*>[\s\S]*?<\/a>/gi), match => {
    const attrs = attributes(match[0].slice(0, match[0].indexOf('>') + 1));
    return { href: attrs.href, text: plainText(match[0]).toLowerCase() };
  });

  assert.ok(
    links.some(link => link.href === '/quote' && link.text === 'tell me what you need'),
    'hero primary CTA says "Tell me what you need" and opens /quote'
  );
  assert.ok(
    links.some(link => link.href === '#work' && link.text === 'see shipped work and public demos'),
    'hero proof CTA opens inspectable public work'
  );
  assert.match(hero, /class=["'][^"']*hero-product[^"']*["'][\s\S]*?assets\/proof\/curio-appstore-current\.png/i, 'hero shows a real shipped-product visual');
  assert.match(plainText(hero), /app store product · public demo \+ source/i, 'hero shows a compact verifiable proof signal');
});

test('selected work uses inspectable assets and labels limitations honestly', () => {
  const work = sectionWithId(html, 'work');
  const expectedAssets = [
    'assets/proof/curio-appstore-current.png',
    'assets/proof/curio-feed-demo.mp4',
    'assets/proof/loqol-questionnaire.png',
    'assets/proof/loqol-contradiction.png',
    'assets/proof/loqol-filled-pdf.png',
    'assets/proof/home-screen-catalog.png',
    'assets/proof/home-screen-menu.png'
  ];

  for (const asset of expectedAssets) {
    assert.match(work, new RegExp(`(?:src|poster)\\s*=\\s*(["'])/${asset.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\1`, 'i'), `${asset} is shown in selected work`);
    const stat = fs.statSync(path.join(ROOT, asset));
    assert.ok(stat.isFile() && stat.size > 1024, `${asset} exists and is non-empty`);
  }

  const curio = plainText(articleContaining(work, 'Curio')).toLowerCase();
  assert.match(curio, /live product/);
  assert.match(curio, /app store/);
  assert.match(curio, /public proof/);

  const loqol = plainText(articleContaining(work, 'Loqol disclosures')).toLowerCase();
  assert.match(loqol, /public demo/);
  assert.match(loqol, /buyer\s*\/\s*agent signing.{0,120}(?:not complete|incomplete)/);
  assert.match(loqol, /seller email delivery.{0,120}(?:not complete|incomplete)/);

  const homeScreen = plainText(articleContaining(work, 'The Home Screen')).toLowerCase();
  assert.match(homeScreen, /operator prototype/);
  assert.match(homeScreen, /mock(?:ed)? payments|payments (?:are )?mocked/);
  assert.match(homeScreen, /no live payments.{0,80}kitchen operations/);
  assert.doesNotMatch(homeScreen, /production (?:ordering )?system|payments? (?:is|are) live|live payment processing|vendor payouts?/);
});

test('homepage excludes stale claims and price-led copy', () => {
  const text = plainText(html).toLowerCase();
  for (const phrase of [
    'real systems, running in production',
    '22 businesses',
    'what if he disappears',
    'do you disappear after launch',
    'technical hostage',
    'one checkout covers them all',
    'per-vendor payouts',
    'live ticket states'
  ]) assert.ok(!text.includes(phrase), `homepage does not claim "${phrase}"`);

  assert.doesNotMatch(html, /\$\s*\d|&#0*36;\s*\d|&#x0*24;\s*\d/i, 'homepage contains no dollar amounts');
});

test('homepage structured data matches the business-facing positioning', () => {
  const block = html.match(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/i);
  assert.ok(block, 'homepage includes JSON-LD');
  const graph = JSON.parse(block[1])['@graph'];
  const person = graph.find(node => node['@type'] === 'Person');
  const business = graph.find(node => node['@type'] === 'Organization');
  const website = graph.find(node => node['@type'] === 'WebSite');
  assert.equal(person.jobTitle, 'Independent Software Developer');
  assert.doesNotMatch(person.description, /student|college|university/i);
  assert.equal(person.email, undefined, 'unverified domain email and personal Gmail are omitted from Person schema');
  assert.equal(business.name, 'Leon Builds');
  assert.equal(business.contactPoint.email, 'leondragon3798@gmail.com');
  assert.deepEqual(business.contactPoint.availableLanguage, ['en', 'zh', 'pt-BR', 'es']);
  assert.equal(website.name, 'Leon Builds');
  assert.ok(!graph.some(node => node['@type'] === 'ProfessionalService'), 'deprecated LocalBusiness-style schema is not used');
  assert.doesNotMatch(JSON.stringify([person.alternateName, person.sameAs, business.sameAs]), /Noctilucenty/i);
});

test('custom cursor code is gone and nav booking specificity is safe', () => {
  assert.doesNotMatch(html, /\bid\s*=\s*(["'])cursor\1/i);
  assert.doesNotMatch(html, /\bclass\s*=\s*(["'])[^"']*\bcursor\b[^"']*\1/i);
  assert.doesNotMatch(js, /#cursor\b|\.cursor\b|\bhas-cursor\b|custom cursor/i);
  assert.doesNotMatch(css, /\.has-cursor\b|(^|[,}])\s*\.cursor\b/im);

  const withoutComments = css.replace(/\/\*[\s\S]*?\*\//g, '');
  const rules = navBookRules(withoutComments);
  assert.ok(rules.some(body => /\bdisplay\s*:\s*none\b/i.test(body)), '.nav-mid .nav-book is hidden by default');
  assert.doesNotMatch(withoutComments, /(^|})\s*\.nav-book\s*\{/im, 'no lower-specificity standalone .nav-book rule can be overridden by .nav-mid a');

  const mobileRule = mediaBlocks(withoutComments).some(block => {
    const max = block.condition.match(/max-width\s*:\s*(\d+)px/i);
    if (!max || Number(max[1]) > 1120) return false;
    return navBookRules(block.body).some(body => /\bdisplay\s*:\s*flex\b/i.test(body));
  });
  assert.ok(mobileRule, '.nav-mid .nav-book becomes visible in the <=1120px menu');
});
