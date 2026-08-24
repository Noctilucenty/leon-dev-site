'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const ROOT = path.join(__dirname, '..');
const read = file => fs.readFileSync(path.join(ROOT, file), 'utf8');

function inlineScripts(html) {
  const scripts = [];
  const re = /<script([^>]*)>([\s\S]*?)<\/script>/g;
  let match;
  while ((match = re.exec(html))) {
    if (/application\/ld\+json/i.test(match[1])) continue;
    if (match[2].trim()) scripts.push(match[2]);
  }
  return scripts;
}

test('quote submission waits for a receipt and keeps mailto as a fallback', () => {
  const html = read('quote.html');

  assert.match(html, /<form class="qform" id="qform" method="post" action="\/quote"/);
  assert.match(html, /<noscript>[\s\S]*mailto:leondragon3798@gmail\.com[\s\S]*tel:\+15108267735[\s\S]*<\/noscript>/);
  assert.match(html, /await fetch\(API\+'\/api\/lead'/);
  assert.match(html, /method:'POST'/);
  assert.match(html, /result\.receiptId/);
  assert.match(html, /id="qreceipt"/);
  assert.match(html, /id="qfail" hidden/);
  assert.match(html, /manual\.href=mailtoFor\(d\)/);
  assert.doesNotMatch(html, /window\.location\.href/);
  assert.doesNotMatch(html, /keepalive:true/);
  assert.doesNotMatch(html, /quote_form_submit/);
  assert.match(html, /track\('quote_lead_accepted',\{receipt:receiptId\}\)/);
  for (const field of [
    'utmSource', 'utmMedium', 'utmCampaign', 'utmTerm', 'utmContent',
    'gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid',
    'firstPage', 'firstReferrer', 'firstUtmSource', 'firstUtmMedium',
    'firstUtmCampaign', 'firstUtmTerm', 'firstUtmContent', 'firstGclid',
    'firstGbraid', 'firstWbraid', 'firstFbclid', 'firstMsclkid',
    'lastPage', 'lastReferrer', 'lastUtmSource', 'lastUtmMedium',
    'lastUtmCampaign', 'lastUtmTerm', 'lastUtmContent', 'lastGclid',
    'lastGbraid', 'lastWbraid', 'lastFbclid', 'lastMsclkid',
    'analyticsSessionId'
  ]) assert.match(html, new RegExp(`d\\.${field}=`));
  assert.match(html, /sessionStorage\.getItem\('leon_analytics_session'\)/);

  for (const event of [
    'quote_submit_attempt',
    'quote_validation_failed',
    'quote_lead_accepted',
    'quote_lead_failed'
  ]) assert.match(html, new RegExp(`track\\('${event}'(?:\\)|,)`));

  const visibleRequired = html.match(/<(?:input|textarea|select)[^>]*\srequired(?:\s|>)/g) || [];
  assert.equal(visibleRequired.length, 2);
  assert.match(html, /<details>/);
  for (const field of ['company', 'currentTools', 'desiredOutcome', 'timeline', 'budget', 'phone']) {
    assert.match(html, new RegExp(`name="${field}"`));
  }

  for (const script of inlineScripts(html)) assert.doesNotThrow(() => new vm.Script(script));
});

test('all booking pages expose a resilient, privacy-bounded calendar funnel', () => {
  const pages = ['call.html', 'pt/agendar.html', 'es/agendar.html', 'zh/yuyue.html'];
  for (const file of pages) {
    const html = read(file);
    assert.match(html, /id="leon-booker"[^>]*aria-busy="true"[^>]*min-height:680px/);
    assert.match(html, /https:\/\/cal\.com\/noctilucente-wzvdey\/15min\?redirect=false/);
    assert.match(html, /action:'bookerReady'/);
    assert.match(html, /action:'linkFailed'/);
    assert.match(html, /action:'bookingSuccessfulV2'/);
    assert.match(html, /track\('calendar_ready'\)/);
    assert.match(html, /track\('calendar_failed'\)/);
    assert.match(html, /track\('calendar_booking_success'/);
    assert.match(html, /function booked\(payload\)/);
    assert.match(html, /data\.uid\|\|\(data\.booking&&data\.booking\.uid\)/);
    assert.match(html, /\{bookingUid:bookingUid\}/);
    assert.doesNotMatch(html, /track\('calendar_booking_success',payload\)/);
    assert.match(html, /query\.get\('s'\)/);
    assert.match(html, /out\.utm_source=source/);
    assert.match(html, /out\.utm_medium=medium/);
    assert.match(html, /out\.utm_campaign=campaign/);
    assert.match(html, /out\.utm_term=term/);
    assert.match(html, /out\.utm_content=content/);
    assert.match(html, /id="leon-cal-direct"/);
    assert.match(html, /hideEventTypeDetails:false/);
    assert.match(html, /\['utm_source','utm_medium','utm_campaign','utm_term','utm_content'\]/);
    assert.doesNotMatch(html, /out\.(?:gclid|gbraid|wbraid|fbclid|msclkid)/);
    assert.doesNotMatch(html, /forwardQueryParams/);
    assert.doesNotMatch(html, /query\.get\('(email|name|phone)'\)/);
    assert.doesNotMatch(html, /callform|CALL_JS/);
    for (const script of inlineScripts(html)) assert.doesNotThrow(() => new vm.Script(script));
  }
});

test('browser attribution captures only bounded campaign identifiers with first/last touch', () => {
  const source = read('assist.js');
  for (const queryField of [
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid'
  ]) assert.match(source, new RegExp(`'${queryField}'`));
  assert.match(source, /ATTR_TTL_MS = 90 \* 24 \* 60 \* 60 \* 1000/);
  assert.match(source, /referrerOrigin\(document\.referrer\)/);
  assert.match(source, /applyAttribution\(payload\)/);
  assert.match(source, /applyAttribution\(leadBody\)/);
  assert.doesNotMatch(source, /current\.forEach\(function \(value, key\)/);
});

test('generator remains the source for each localized booking variant', () => {
  const source = read('tools/build_pages.py');
  assert.match(source, /def booker\(lang="en"\):/);
  assert.match(source, /booker_html = booker\("en"\)/);
  assert.match(source, /render_call\(_lang, booker\(_lang\), LANG_CTX\)/);
  assert.doesNotMatch(source, /CALL_JS|id="callform"/);
});

test('contractor lead recovery is a focused website plus follow-up product', () => {
  const html = read('missed-lead-recovery.html');

  assert.match(html, /<link rel="canonical" href="https:\/\/leonbuilds\.org\/missed-lead-recovery">/);
  assert.match(html, /"@type": "Service"/);
  assert.match(html, /"name": "Contractor Lead Recovery System"/);
  assert.match(html, /"name": "United States"/);
  assert.match(html, /"price": "1500"/);
  assert.match(html, /10-business-day/);
  assert.match(html, /contractor website \+ estimate follow-up/i);
  assert.ok(html.indexOf('class="sec page-hero"') < html.indexOf('id="scope"'));
  assert.doesNotMatch(html, /id="client-feedback"|data-testimonial-id|testimonial-stars|5 out of 5 stars/);
  assert.match(html, /Give every website estimate request/i);
  assert.match(html, /a clear path from form to follow-up/i);
  assert.match(html, /structured estimate intake/i);
  assert.match(html, /id="fit"/);
  assert.match(html, /id="workflow"/);
  assert.doesNotMatch(html, /id="automotive"|id="restaurants"/);
  assert.match(html, /What is outside this \$1,500 starting scope/i);
  assert.match(html, /technical evidence you can inspect before booking/i);
  assert.match(html, /California-based · serving Bay Area contractors remotely/i);
  assert.ok(html.indexOf('id="workflow"') < html.indexOf('id="scope"'));
  assert.match(html, /30 days of fixes for defects against the agreed written scope/);
  assert.match(html, /Phone, messaging, CRM, domain, and hosting providers keep their own fees/i);
  assert.match(html, /data-evt="cta_call_click"/);
  assert.match(html, /href="\/call\?service=contractor-lead-recovery" data-evt="cta_call_click"/);
  assert.match(html, /Book a free 15-minute website review/i);
  assert.match(html, /See the exact \$1,500 scope/i);
  assert.equal((html.match(/href="\/call\?service=contractor-lead-recovery"/g) || []).length >= 3, true);
  assert.doesNotMatch(html, /\$2,500/);
  assert.doesNotMatch(html, /guarantee(?:d|s)? (?:leads|bookings|revenue)/);
  assert.match(read('sitemap.xml'), /<loc>https:\/\/leonbuilds\.org\/missed-lead-recovery<\/loc>/);

  const call = read('call.html');
  assert.match(call, /service'\)!=='contractor-lead-recovery'/);
  assert.match(call, /Book a free <em>15-minute website review<\/em>/);
  assert.match(read('app.js'), /closest\('\.contractor-landing,\.contractor-call-context'\)/);

  assert.match(read('industries/contractors.html'), /href="\/missed-lead-recovery"/);
  assert.doesNotMatch(read('industries/automotive.html'), /href="\/missed-lead-recovery/);
  assert.doesNotMatch(read('industries/restaurants.html'), /href="\/missed-lead-recovery/);

  const copyGate = read('tools/check_copy.py');
  assert.match(copyGate, /'missed-lead-recovery\.html': \{'bay area'\}/);
});

test('metadata, handoff copy, and generated footer stay honest and synchronized', () => {
  const source = read('tools/build_pages.py');
  const ownershipOutputs = [
    'about.html', 'services/index.html',
    ...fs.readdirSync(path.join(ROOT, 'services')).filter(f => f.endsWith('.html')).map(f => `services/${f}`),
    ...fs.readdirSync(path.join(ROOT, 'industries')).filter(f => f.endsWith('.html')).map(f => `industries/${f}`)
  ];
  const ownershipCorpus = [source, ...ownershipOutputs.map(read)].join('\n');
  for (const stale of [
    'you own everything',
    'a fast site you own completely',
    'you own the developer accounts and the code from day one',
    'you own the code and hosting',
    'completely — repo, accounts and infrastructure from day one'
  ]) assert.doesNotMatch(ownershipCorpus, new RegExp(stale));
  assert.match(source, /included source code/);
  assert.match(source, /third-party (?:hosts|infrastructure|services)/);

  const localizedCorpus = [
    'es/pagina-web.html', 'es/pedidos-en-linea.html', 'es/automatizacion.html',
    'pt/criar-site.html', 'pt/pedidos-online.html', 'pt/automacao.html',
    'zh/zuo-wangzhan.html', 'zh/zaixian-diandan.html', 'zh/zidonghua.html'
  ].map(read).join('\n');
  for (const stale of [
    'todo queda a tu nombre',
    'el sistema es tuyo, completo',
    'tudo fica no seu nome',
    'tudo é seu, completo',
    '域名、服务器、代码、账号和数据都在你名下'
  ]) assert.doesNotMatch(localizedCorpus, new RegExp(stale));
  assert.match(localizedCorpus, /(?:servicios de terceros|serviços de terceiros|第三方服务)/);

  const descriptions = ['zh/yuyue.html', 'services/booking-systems.html', 'services/business-dashboards.html'];
  for (const file of descriptions) {
    const match = read(file).match(/<meta name="description" content="([^"]+)">/);
    assert.ok(match, `${file} has a meta description`);
    assert.ok(Array.from(match[1]).length >= 50, `${file} description is at least 50 characters`);
    assert.ok(Array.from(match[1]).length <= 160, `${file} description is at most 160 characters`);
  }

  const generated = [
    'about.html', 'call.html', 'quote.html', 'missed-lead-recovery.html', 'services/index.html', 'industries/index.html',
    ...fs.readdirSync(path.join(ROOT, 'services')).filter(f => f.endsWith('.html')).map(f => `services/${f}`),
    ...fs.readdirSync(path.join(ROOT, 'industries')).filter(f => f.endsWith('.html')).map(f => `industries/${f}`)
  ];
  for (const file of new Set(generated)) {
    const html = read(file);
    assert.match(html, /href="\/privacy"/);
    assert.match(html, /data-evt="footer_email_click"/);
    assert.match(html, /data-evt="footer_phone_click"/);
  }
  assert.match(read('about.html'), /data-evt="about_quote_click"/);
  assert.match(read('sitemap.xml'), /<loc>https:\/\/leonbuilds\.org\/privacy<\/loc>/);
});
