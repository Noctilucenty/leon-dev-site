const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const read = (file) => fs.readFileSync(path.join(ROOT, file), 'utf8');
const text = (html) => html
  .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
  .replace(/<style\b[\s\S]*?<\/style>/gi, ' ')
  .replace(/<[^>]+>/g, ' ')
  .replace(/&amp;/g, '&')
  .replace(/&#x27;|&#39;/g, "'")
  .replace(/\s+/g, ' ')
  .trim();

test('homepage clearly targets small-business web design and exposes inspectable proof early', () => {
  const html = read('index.html');
  assert.match(html, /<title>Small Business Web Design &amp; Custom Software \| Leon Builds<\/title>/i);
  assert.match(text(html), /small-business web design · custom software · california \/ u\.s\./i);
  assert.ok(html.indexOf('class="proof-strip"') < html.indexOf('id="fix"'));
  assert.ok(html.indexOf('class="proof-strip"') < html.indexOf('id="work"'));
  assert.match(html, /href="\/services\/websites"[^>]*data-evt="hero_webdesign_click"/i);
  assert.match(html, /href="#work"[^>]*data-evt="hero_work_click"/i);
  assert.match(text(html), /contractor product website \+ lead follow-up/i);
});

test('website pillar answers search, trust, scope, and next-action questions', () => {
  const html = read('services/websites.html');
  const visible = text(html);

  assert.match(html, /<title>Small Business Web Design \| Fixed-Price Websites \| Leon Builds<\/title>/i);
  assert.match(visible, /small-business web design that turns visits into calls and bookings/i);
  assert.match(visible, /what your website must answer in five seconds/i);
  assert.match(visible, /website cost depends on what the site must do/i);
  assert.match(visible, /public product and workflow evidence/i);
  assert.doesNotMatch(html, /data-testimonial-id|testimonial-stars|5 out of 5 stars|★★★★★/i);
  assert.match(html, /href="\/industries\/contractors"/i);
  assert.match(html, /href="\/industries\/automotive"/i);
  assert.match(html, /href="\/industries\/restaurants"/i);

  const hero = html.match(/<section class="sec page-hero">[\s\S]*?<\/section>/i)?.[0] || '';
  assert.ok(hero.indexOf('href="/call"') < hero.indexOf('href="/quote"'), 'calendar is the first service-page action');
});

test('services index exposes starting floors without making buyers open nine pages', () => {
  const visible = text(read('services/index.html'));
  for (const floor of ['$300', '$3,500', '$750', '$1,000', '$500', '$1,500', '$600']) {
    assert.ok(visible.includes(`from ${floor}`), `services index includes ${floor}`);
  }
});

test('high-intent industry pages form a focused web-design and lead-recovery cluster', () => {
  const pages = [
    ['industries/restaurants.html', /restaurant website design &amp; online ordering/i, /what a restaurant website needs/i],
    ['industries/contractors.html', /contractor web design &amp; lead follow-up/i, /what a contractor website needs/i],
    ['industries/automotive.html', /auto repair website design &amp; booking/i, /what an auto repair website needs/i],
  ];

  for (const [file, titlePattern, contentPattern] of pages) {
    const html = read(file);
    assert.match(html, titlePattern, `${file} has a specific search title`);
    assert.match(text(html), contentPattern, `${file} has distinct buyer guidance`);
    assert.match(html, /href="\/services\/websites"/i, `${file} links to the web-design pillar`);
    if (file === 'industries/contractors.html') {
      assert.match(html, /href="\/missed-lead-recovery"/i, `${file} links to the contractor product`);
    } else {
      assert.doesNotMatch(html, /href="\/missed-lead-recovery/i, `${file} does not point to a mismatched contractor product`);
    }
  }
});

test('unreleased client feedback and ratings stay off every related service page', () => {
  const pages = [
    'services/ai-chatbots.html',
    'services/ai-phone-agents.html',
    'services/business-automation.html',
    'services/business-dashboards.html',
    'services/custom-software.html',
  ];

  for (const file of pages) {
    const html = read(file);
    assert.doesNotMatch(html, /data-testimonial-id|testimonial-stars|5 out of 5 stars|★★★★★/i);
    const schemas = Array.from(html.matchAll(/<script\b[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi), match => match[1]);
    assert.doesNotMatch(schemas.join('\n'), /AggregateRating|Review|reviewRating|ratingValue/i);
  }
});

test('GEO index states current proof and avoids stale contradictions', () => {
  const llms = read('llms.txt');
  assert.match(llms, /Small-business web design/i);
  assert.match(llms, /inspectable public work/i);
  assert.match(llms, /Curio.*App Store/is);
  assert.doesNotMatch(llms, /client testimonials|client reviews|five-star|all 5 stars|#testimonials|22-business operation/i);
});
