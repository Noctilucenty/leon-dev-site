'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const ROOT = path.join(__dirname, '..');
const read = file => fs.readFileSync(path.join(ROOT, file), 'utf8');
const html = read('homepage/index.html');
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
    .replace(/&amp;/gi, '&')
    .replace(/&(?:apos|#39|#x27);/gi, "'")
    .replace(/&nbsp;/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function extractElementAt(source, tag, start) {
  const tokens = new RegExp(`<\/?${tag}\\b[^>]*>`, 'gi');
  tokens.lastIndex = start;
  let depth = 0;
  let token;
  while ((token = tokens.exec(source))) {
    depth += /^<\//.test(token[0]) ? -1 : 1;
    if (depth === 0) return source.slice(start, tokens.lastIndex);
  }
  assert.fail(`${tag} element at ${start} is not closed`);
}

function elementWithId(source, tag, id) {
  const opener = new RegExp(`<${tag}\\b(?=[^>]*\\bid\\s*=\\s*(["'])${id}\\1)[^>]*>`, 'i');
  const match = opener.exec(source);
  assert.ok(match, `published homepage has ${tag}#${id}`);
  return extractElementAt(source, tag, match.index);
}

function elementsWithClass(source, tag, className) {
  const result = [];
  const openers = new RegExp(`<${tag}\\b[^>]*>`, 'gi');
  let match;
  while ((match = openers.exec(source))) {
    if ((attributes(match[0]).class || '').split(/\s+/).includes(className)) {
      result.push(extractElementAt(source, tag, match.index));
    }
  }
  return result;
}

function linksIn(source) {
  return Array.from(source.matchAll(/<a\b[^>]*>[\s\S]*?<\/a>/gi), match => ({
    attrs: attributes(match[0].slice(0, match[0].indexOf('>') + 1)),
    text: plainText(match[0]),
  }));
}

function hrefPath(href) {
  return new URL(href, 'https://leonbuilds.org').pathname;
}

function schemaNodes(source) {
  return Array.from(
    source.matchAll(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi),
    match => JSON.parse(match[1])
  ).flatMap(root => Array.isArray(root) ? root : [root]);
}

function referencedAssets(extension) {
  const refs = new Set(Array.from(
    html.matchAll(/(?:href|src)=["'](\/_next\/static\/[^"']+)["']/gi),
    match => match[1]
  ).filter(ref => ref.endsWith(extension)));
  assert.ok(refs.size > 0, `homepage references ${extension} assets`);
  return Array.from(refs, ref => {
    const relative = path.join('homepage', ref.replace(/^\//, ''));
    assert.ok(fs.existsSync(path.join(ROOT, relative)), `${ref} exists`);
    return read(relative);
  }).join('\n');
}

const css = referencedAssets('.css');
const clientJs = referencedAssets('.js');

test('published export has the current metadata and four-section navigation', () => {
  assert.match(html, /<title>Small Business Websites &amp; Automation \| Leon Builds<\/title>/i);
  const description = attributes(html.match(/<meta\b[^>]*name=["']description["'][^>]*>/i)?.[0] || '').content || '';
  assert.match(description, /free 3-point website review/i);
  assert.match(description, /websites from \$300/i);
  assert.match(description, /automation from \$500/i);
  assert.match(html, /rel=["']canonical["'][^>]*href=["']https:\/\/leonbuilds\.org\/?["']/i);
  assert.match(html, /property=["']og:image["'][^>]*assets\/og\.png/i);

  const sectionIds = Array.from(html.matchAll(/<section\b[^>]*\bid=["']([^"']+)["']/gi), match => match[1]);
  assert.deepEqual(sectionIds, ['services', 'work', 'about', 'start']);
  const header = html.match(/<header\b[^>]*>[\s\S]*?<\/header>/i)?.[0] || '';
  for (const [href, label] of [['#services', 'Services'], ['#work', 'Work'], ['#about', 'About'], ['#start', 'Start']]) {
    assert.ok(linksIn(header).some(link => link.attrs.href === href && link.text.includes(label)), `${label} is in the nav`);
  }
  assert.match(header, /href=["']#review-form["'][^>]*data-event=["']mobile_review_cta_click["']/i);
});

test('hero uses the free review as its primary action', () => {
  const hero = elementsWithClass(html, 'section', 'hero-journey')[0] || '';
  const visible = plainText(hero);
  assert.match(visible, /websites that make it easy to act/i);
  assert.match(visible, /automation that follows up/i);
  assert.match(visible, /small businesses.*clearer inquiry paths and less busywork/i);
  assert.match(visible, /websites from \$\s*300.*automation from \$\s*500/i);
  const primary = linksIn(hero).find(link => link.attrs['data-event'] === 'hero_review_cta_click');
  assert.equal(primary?.attrs.href, '#review-form');
  assert.match(primary?.text || '', /get a free 3-point review/i);
  assert.ok(linksIn(hero).some(link => link.attrs.href === '#work' && /see real work/i.test(link.text)));
  assert.doesNotMatch(hero, /start a project|get a fixed quote|quote_cta_click/i);
});

test('service cards have crawlable detail links and scope controls', () => {
  const services = elementWithId(html, 'section', 'services');
  const cards = elementsWithClass(services, 'article', 'service-v2-card');
  assert.equal(cards.length, 3);
  const expected = [
    ['/services/websites', '300'],
    ['/missed-lead-recovery', '1,500'],
    ['/services/business-automation', '500'],
  ];
  for (const [index, card] of cards.entries()) {
    assert.ok(linksIn(card).some(link => hrefPath(link.attrs.href) === expected[index][0]), `${expected[index][0]} is crawlable`);
    assert.match(plainText(card), new RegExp(`\\$\\s*${expected[index][1]}`));
    assert.match(card, /<button\b[^>]*aria-label=["']View [^"']+ scope["'][^>]*>[\s\S]*?View scope/i);
  }
});

test('work proof uses canonical case-study pages and repeats the review action', () => {
  const work = elementWithId(html, 'section', 'work');
  const projects = elementsWithClass(work, 'article', 'project-scene');
  assert.equal(projects.length, 3);
  assert.deepEqual(projects.map(project => hrefPath(linksIn(project)[0].attrs.href)), [
    '/work/allcpr-site-intelligence',
    '/work/curio-app',
    '/work/beastypages-website',
  ]);
  assert.match(plainText(work), /33,772.*ZIP-code records/i);
  assert.match(plainText(work), /founder-built product/i);
  assert.match(plainText(work), /client build.*demo checkout/i);
  assert.match(work, /data-conversion-proof=["']allcpr-case-study["']/i);
  assert.doesNotMatch(work, /href=["'][^"']*\/work#|apps\.apple\.com|href=["']https:\/\/(?:www\.)?beastypages\.com/i);
  const repeat = linksIn(html).find(link => link.attrs['data-event'] === 'work_review_cta_click');
  assert.equal(repeat?.attrs.href, '#review-form');
});

test('founder proof, four-step process, and reviews support the start section', () => {
  const about = elementWithId(html, 'section', 'about');
  const builder = linksIn(about).find(link => link.attrs['data-event'] === 'about_builder_click');
  assert.equal(hrefPath(builder.attrs.href), '/about');
  assert.match(plainText(about), /built by Leon/i);
  assert.match(plainText(about), /helped us evaluate and plan new locations/i);
  const process = elementWithId(about, 'div', 'process');
  assert.equal(elementsWithClass(process, 'div', 'process-stop').length, 4);
  for (const step of ['Problem', 'Scope', 'Build', 'Launch']) assert.match(plainText(process), new RegExp(`\\b${step}\\b`));

  const start = elementWithId(html, 'section', 'start');
  assert.match(plainText(start), /three specific improvements to consider/i);
  assert.match(start, /data-conversion-proof=["']website-client-review["']/i);
  assert.ok(linksIn(start).some(link => hrefPath(link.attrs.href) === '/reviews' && /client reviews/i.test(link.text)));
  assert.doesNotMatch(JSON.stringify(schemaNodes(html)), /aggregateRating|reviewRating|ratingValue/i);
});

test('free-review form keeps an optional URL and a receipt-backed lead contract', () => {
  const start = elementWithId(html, 'section', 'start');
  const form = start.match(/<form\b[^>]*>[\s\S]*?<\/form>/i)?.[0] || '';
  const website = form.match(/<input\b[^>]*id=["']business-url["'][^>]*>/i)?.[0] || '';
  const problem = form.match(/<textarea\b[^>]*id=["']quote-problem["'][^>]*>/i)?.[0] || '';
  const email = form.match(/<input\b[^>]*id=["']quote-email["'][^>]*>/i)?.[0] || '';
  assert.equal(attributes(website).name, 'business-url');
  assert.equal(attributes(website).inputmode, 'url');
  assert.doesNotMatch(website, /\brequired(?:\s|=|>)/i);
  assert.match(problem, /\brequired(?:\s|=|>)/i);
  assert.match(email, /type=["']email["'][^>]*required/i);
  assert.match(form, /class=["'][^"']*honeypot[^"']*["'][^>]*name=["']website["']/i);
  assert.match(plainText(form), /request my review.*no payment or commitment/i);

  assert.match(clientJs, /\/api\/lead/);
  assert.match(clientJs, /method:`POST`/);
  for (const field of ['problem', 'email', 'service', 'sourcePage', 'idempotencyKey', 'websiteUrl', 'website']) {
    assert.match(clientJs, new RegExp(`${field}:`), `lead payload includes ${field}`);
  }
  assert.match(clientJs, /receiptId/);
  assert.match(clientJs, /quote_lead_accepted/);
  assert.match(clientJs, /mailto:leondragon3798@gmail\.com/);
});

test('schema, mobile CSS, and media safeguards match the exported experience', () => {
  const nodes = schemaNodes(html);
  const business = nodes.find(node => node['@id'] === 'https://leonbuilds.org/#business');
  const person = nodes.find(node => node['@id'] === 'https://leonbuilds.org/#leon');
  assert.equal(business?.['@type'], 'Organization');
  assert.equal(business?.founder?.['@id'], person?.['@id']);
  assert.equal(person?.jobTitle, 'Founder and developer');
  assert.equal(hrefPath(person?.url), '/about');

  assert.equal((html.match(/<h1\b/gi) || []).length, 1);
  assert.ok(linksIn(html).some(link =>
    link.attrs.href === '#main' && (link.attrs.class || '').split(/\s+/).includes('skip-link')
  ), 'keyboard users have a skip link');
  for (const image of html.match(/<img\b[^>]*>/gi) || []) {
    const attrs = attributes(image);
    assert.ok(Object.hasOwn(attrs, 'alt'));
    assert.equal(attrs.loading, 'lazy');
    assert.ok(Number(attrs.width) > 0 && Number(attrs.height) > 0);
  }
  assert.match(css, /@media\s*\(max-width:600px\)[\s\S]*?\.mobile-nav-cta\{[^}]*min-height:44px[^}]*display:inline-flex/i);
  assert.match(css, /@media\s*\(prefers-reduced-motion:reduce\)/i);
  assert.match(clientJs, /matchMedia\(`\(prefers-reduced-motion: reduce\)`\)/);
});

test('viewport milestones and the versioned bridge preserve one acquisition funnel', () => {
  assert.match(clientJs, /onFocusCapture/);
  assert.equal((clientJs.match(/quote_form_start/g) || []).length, 1);
  assert.match(clientJs, /isIntersecting[\s\S]{0,180}start_section_view/);
  assert.match(clientJs, /isIntersecting[\s\S]{0,180}proof_view/);
  assert.equal((clientJs.match(/\b[A-Za-z_$][\w$]*\(`page_view`\)/g) || []).length, 1);
  assert.match(clientJs, /__leonMeasurementOwnsPageView/);
  assert.match(clientJs, /__leonMeasurementPageViewPending/);
  assert.match(clientJs, /__leonMeasurementPageViewSent/);
  assert.equal((clientJs.match(/\/assist\.js\?v=20260904-lead-journey/g) || []).length, 1);
  assert.match(html, /<body\b[^>]*data-assistant-launcher=["']hidden["']/i);
  assert.match(assist, /if \(window\.__leonMeasurementOwnsPageView\) return;/);
  assert.match(assist, /window\.__leonMeasurementPageViewSent = true;/);
  for (const field of ['utmTerm', 'gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid']) {
    assert.ok(clientJs.includes(field), `bridge preserves ${field}`);
  }
});
