'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const ROOT = path.join(__dirname, '..');
const read = file => fs.readFileSync(path.join(ROOT, file), 'utf8');

function schemaNodes(html) {
  return Array.from(html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g))
    .flatMap(match => {
      const parsed = JSON.parse(match[1]);
      return Array.isArray(parsed) ? parsed : [parsed];
    });
}

test('three standalone case studies expose evidence, boundaries, and article metadata', () => {
  const cases = [
    {
      file: 'work/allcpr-site-intelligence.html',
      route: '/work/allcpr-site-intelligence',
      required: [/reviewed project dataset contained 33,772 U\.S\. ZIP-code records/i, /misleading validation loop/i, /human field validation/i, /data-testimonial-id="testimonial-02"/i],
      forbidden: [/guarantee(?:d|s)? (?:leads|revenue|openings)/i],
    },
    {
      file: 'work/curio-app.html',
      route: '/work/curio-app',
      required: [/React and TypeScript client/i, /Express and Postgres backend/i, /four-language in-app content experience/i, /apps\.apple\.com\/app\/apple-store\/id6781121127/i],
      forbidden: [/revenue (?:grew|increased)|user growth (?:of|reached)|retention (?:grew|increased)/i],
    },
    {
      file: 'work/beastypages-website.html',
      route: '/work/beastypages-website',
      required: [/September 4, 2026 review snapshot contained 37 businesses/i, /server-side repricing/i, /vendor-separated demo tickets/i, /Payment and kitchen progression are simulations/i, /data-testimonial-id="testimonial-03"/i],
      forbidden: [/production ordering rollout[^,.]*complete|guarantee(?:d|s)? (?:sales|leads|revenue)/i],
    },
  ];

  for (const entry of cases) {
    const html = read(entry.file);
    assert.match(html, new RegExp(`<link rel="canonical" href="https://leonbuilds\\.org${entry.route}">`));
    assert.match(html, new RegExp(`<meta property="og:url" content="https://leonbuilds\\.org${entry.route}">`));
    assert.match(html, /<meta property="og:image" content="https:\/\/leonbuilds\.org\/assets\/proof\//);
    assert.match(html, /<meta name="twitter:card" content="summary_large_image">/);
    assert.match(html, /data-view-event="proof_view"/);
    assert.match(html, /data-view-event="start_section_view"/);
    assert.match(html, /reviewed September 4, 2026/i);
    for (const pattern of entry.required) assert.match(html, pattern, `${entry.file}: ${pattern}`);
    for (const pattern of entry.forbidden) assert.doesNotMatch(html, pattern, `${entry.file}: ${pattern}`);

    const nodes = schemaNodes(html);
    const page = nodes.find(node => node['@type'] === 'WebPage');
    const article = nodes.find(node => node['@type'] === 'Article');
    const breadcrumbs = nodes.find(node => node['@type'] === 'BreadcrumbList');
    assert.equal(page.url, `https://leonbuilds.org${entry.route}`);
    assert.equal(page.dateModified, '2026-09-04');
    assert.equal(article.mainEntityOfPage['@id'], `${page.url}#page`);
    assert.equal(article.author.url, 'https://leonbuilds.org/about');
    assert.equal(breadcrumbs.itemListElement.at(-1).item, page.url);
  }
});

test('work and relevant service surfaces link to the detailed cases', () => {
  const work = read('work.html');
  for (const route of [
    '/work/allcpr-site-intelligence',
    '/work/curio-app',
    '/work/beastypages-website',
  ]) assert.match(work, new RegExp(`href="${route}"`));

  assert.match(read('services/custom-software.html'), /href="\/work\/allcpr-site-intelligence"/);
  assert.match(read('services/mobile-apps.html'), /href="\/work\/curio-app"/);
  assert.match(read('services/websites.html'), /href="\/work\/beastypages-website"/);
  const partner = read('technical-build-partner.html');
  for (const route of [
    '/work/allcpr-site-intelligence',
    '/work/curio-app',
    '/work/beastypages-website',
  ]) assert.match(partner, new RegExp(`href="${route}"`));
});

test('contractor inquiry guide is answer-first, self-auditing, and claim-bounded', () => {
  const html = read('guides/contractor-inquiry-workflow.html');
  assert.match(html, /<title>What Happens After a Contractor Quote Request\? \| Leon Builds<\/title>/);
  assert.match(html, /<link rel="canonical" href="https:\/\/leonbuilds\.org\/guides\/contractor-inquiry-workflow">/);
  assert.match(html, /five things: captures enough information to route the job, confirms receipt, assigns a person, follows up with clear stop rules, and records what happened/i);
  for (const step of ['Capture', 'Acknowledge', 'Route', 'Assign and follow up', 'Record the result']) {
    assert.match(html, new RegExp(`<h3>${step}</h3>`, 'i'));
  }
  assert.equal((html.match(/class="guide-audit"[\s\S]*?<\/div>/)?.[0].match(/<article>/g) || []).length, 8);
  assert.match(html, /automatic receipt is not a human reply/i);
  assert.match(html, /Do not count a form receipt as a booked estimate/i);
  assert.match(html, /does not create demand[^.]*guarantee leads, bookings, revenue, or won jobs/i);
  assert.match(html, /href="\/quote\?service=contractor-lead-recovery"/);
  assert.match(html, /href="\/missed-lead-recovery"/);
  assert.match(html, /data-view-event="proof_view"/);
  assert.match(html, /data-view-event="start_section_view"/);

  const nodes = schemaNodes(html);
  assert.ok(nodes.some(node => node['@type'] === 'Article'));
  assert.ok(nodes.some(node => node['@type'] === 'WebPage'));
});

test('sitemap and llms index the new evidence routes without inventing outcomes', () => {
  const sitemap = read('sitemap.xml');
  const llms = read('llms.txt');
  for (const route of [
    '/work/allcpr-site-intelligence',
    '/work/curio-app',
    '/work/beastypages-website',
    '/guides/contractor-inquiry-workflow',
  ]) {
    assert.match(sitemap, new RegExp(`<loc>https://leonbuilds\\.org${route}</loc>`));
    assert.match(llms, new RegExp(`https://leonbuilds\\.org${route}`));
  }
  assert.match(llms, /not a claim about revenue, growth or retention/i);
  assert.match(llms, /not a claim that automation creates demand or guarantees leads, bookings, revenue or won jobs/i);
});
