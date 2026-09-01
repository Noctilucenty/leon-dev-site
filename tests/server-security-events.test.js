'use strict';

const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');

const TEMP_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'leon-server-test-'));
const EVENTS_FILE = path.join(TEMP_DIR, 'events.jsonl');
process.env.NODE_ENV = 'test';
process.env.EVENTS_FILE = EVENTS_FILE;
process.env.LEADS_KEY = 'header-only-test-key';
process.env.OPENAI_API_KEY = '';

const { app } = require('../server/index');
const { normalizeEvent, sourceOf, funnelStats } = require('../server/events');

let server;
let base;

before(async () => {
  await new Promise((resolve) => {
    server = app.listen(0, '127.0.0.1', resolve);
  });
  base = `http://127.0.0.1:${server.address().port}`;
});

after(async () => {
  if (server) await new Promise(resolve => server.close(resolve));
  fs.rmSync(TEMP_DIR, { recursive: true, force: true });
});

function postJson(route, body) {
  return fetch(base + route, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body)
  });
}

function chatBody() {
  return {
    sessionId: 'chat-test-session',
    page: '/',
    lang: 'en',
    messages: [{ role: 'user', content: 'hello' }]
  };
}

test('event names reject markup and whitespace instead of storing it', async () => {
  for (const name of ['<img src=x onerror=alert(1)>', 'page view', 'Page_View', '_page_view']) {
    const response = await postJson('/api/event', { name, path: '/' });
    assert.equal(response.status, 400);
  }
  assert.equal(fs.existsSync(EVENTS_FILE), false);
});

test('anonymous correlation rejects contact-like session values and strips referrer detail', () => {
  const event = normalizeEvent({
    name: 'page_view',
    path: '/',
    sessionId: 'visitor@example.com',
    firstRef: 'https://example.com/path?email=visitor%40example.com#details'
  }, '2026-08-22T12:00:00.000Z');
  assert.equal(event.sessionId, '');
  assert.equal(event.firstRef, 'https://example.com');
});

test('known AI referrers are referral signals, not citation claims', () => {
  const cases = [
    ['chatgpt.com', 'ChatGPT'],
    ['chat.openai.com', 'ChatGPT'],
    ['www.perplexity.ai', 'Perplexity'],
    ['claude.ai', 'Claude'],
    ['gemini.google.com', 'Gemini'],
    ['bard.google.com', 'Gemini'],
    ['copilot.microsoft.com', 'Microsoft Copilot']
  ];

  for (const [host, product] of cases) {
    assert.equal(
      sourceOf({ firstRef: `https://${host}/answer/123` }),
      `AI referral — ${product}`,
      host
    );
  }
  assert.equal(
    sourceOf({ lastRef: 'https://claude.ai/chat/example' }, 'last'),
    'AI referral — Claude'
  );
  assert.equal(
    sourceOf({ firstRef: 'https://chatgpt.com.attacker.example/path' }),
    'chatgpt.com.attacker.example',
    'lookalike domains must not enter an AI bucket'
  );
  assert.equal(
    sourceOf({ firstUtm: 'partner-newsletter', firstRef: 'https://chatgpt.com/' }),
    'partner-newsletter',
    'an explicit source tag keeps priority over the referrer'
  );
  assert.doesNotMatch(
    cases.map(([, product]) => `AI referral — ${product}`).join(' '),
    /cited|citation|mentioned|recommended/i
  );
});

test('event beacon stores bounded anonymous session plus first/last attribution', async () => {
  const response = await postJson('/api/event', {
    name: 'fixcard_ai-chatbots',
    path: '/services/ai-chatbots',
    sessionId: 'ec901d61-729a-48b8-b0fd-cac031381a88',
    firstPage: '/',
    lastPage: '/services/ai-chatbots',
    firstReferrer: 'https://www.google.com/search?q=automation',
    lastReferrer: 'https://facebook.com/groups/example',
    firstUtmSource: 'google',
    lastUtmSource: 'fbgroup-oakland',
    firstUtmMedium: 'organic',
    lastUtmMedium: 'social',
    firstUtmCampaign: 'evergreen',
    lastUtmCampaign: 'august-post',
    firstUtmTerm: 'booking software',
    lastUtmTerm: 'lead follow up',
    firstUtmContent: 'rsa-a',
    lastUtmContent: 'image-b',
    firstGclid: 'gclid.first_123',
    lastGclid: 'gclid.last_123',
    firstGbraid: 'gbraid-first_123',
    lastGbraid: 'gbraid-last_123',
    firstWbraid: 'wbraid-first_123',
    lastWbraid: 'wbraid-last_123',
    firstFbclid: 'fbclid.first_123',
    lastFbclid: 'fbclid.last_123',
    firstMsclkid: 'abcdef0123456789abcdef0123456789',
    lastMsclkid: 'fedcba9876543210fedcba9876543210',
    receipt: 'lead_12345678-1234-1234-1234-123456789abc',
    bookingUid: 'booking_example',
    status: 'accepted',
    service: 'technical-build-partner',
    package: 'systems-plan'
  });
  assert.equal(response.status, 204);

  const rows = fs.readFileSync(EVENTS_FILE, 'utf8').trim().split('\n').map(JSON.parse);
  const event = rows.at(-1);
  assert.equal(event.name, 'fixcard_ai-chatbots');
  assert.equal(event.sessionId, 'ec901d61-729a-48b8-b0fd-cac031381a88');
  assert.equal(event.firstPage, '/');
  assert.equal(event.lastPage, '/services/ai-chatbots');
  assert.equal(event.firstRef, 'https://www.google.com');
  assert.equal(event.lastRef, 'https://facebook.com');
  assert.equal(event.firstUtm, 'google');
  assert.equal(event.lastUtm, 'fbgroup-oakland');
  assert.equal(event.firstMedium, 'organic');
  assert.equal(event.lastMedium, 'social');
  assert.equal(event.firstCampaign, 'evergreen');
  assert.equal(event.lastCampaign, 'august-post');
  assert.equal(event.firstUtmTerm, 'booking software');
  assert.equal(event.lastUtmTerm, 'lead follow up');
  assert.equal(event.firstUtmContent, 'rsa-a');
  assert.equal(event.lastUtmContent, 'image-b');
  assert.equal(event.firstGclid, 'gclid.first_123');
  assert.equal(event.lastGclid, 'gclid.last_123');
  assert.equal(event.firstGbraid, 'gbraid-first_123');
  assert.equal(event.lastGbraid, 'gbraid-last_123');
  assert.equal(event.firstWbraid, 'wbraid-first_123');
  assert.equal(event.lastWbraid, 'wbraid-last_123');
  assert.equal(event.firstFbclid, 'fbclid.first_123');
  assert.equal(event.lastFbclid, 'fbclid.last_123');
  assert.equal(event.firstMsclkid, 'abcdef0123456789abcdef0123456789');
  assert.equal(event.lastMsclkid, 'fedcba9876543210fedcba9876543210');
  assert.equal(event.receipt, 'lead_12345678-1234-1234-1234-123456789abc');
  assert.equal(event.bookingUid, 'booking_example');
  assert.equal(event.status, 'accepted');
  assert.equal(event.service, 'technical-build-partner');
  assert.equal(event.package, 'systems-plan');
});

test('event correlation fields reject contact-looking, malformed, and oversized values', () => {
  const event = normalizeEvent({
    name: 'quote_lead_accepted',
    receipt: 'lead_1234567890abcdef/poison',
    bookingUid: 'visitor@example.com',
    status: 'accepted<script>',
    service: 'technical partner',
    package: 'x'.repeat(65)
  }, '2026-08-22T12:00:00.000Z');
  for (const field of ['receipt', 'bookingUid', 'status', 'service', 'package']) {
    assert.equal(Object.hasOwn(event, field), false, field);
  }
});

test('every redesigned quote and direct-contact CTA remains a high-intent funnel action', () => {
  const names = [
    'nav_quote_click',
    'hero_quote_click',
    'contact_quote_click',
    'about_quote_click',
    'work_quote_click',
    'work_final_quote_click',
    'reviews_quote_click',
    'chat_handoff_offer_click',
    'footer_email_click',
    'footer_phone_click',
    'technical_partner_call_click',
    'technical_partner_quote_click',
    'technical_partner_systems_plan_click',
    'technical_partner_sprint_click',
    'technical_partner_ongoing_click',
  ];
  const events = names.flatMap((name, index) => {
    const sessionId = `redesign-intent-${index}`;
    return [
      { name: 'page_view', sessionId, path: '/' },
      { name, sessionId, path: '/' },
    ];
  });
  const intent = funnelStats(events).stages.find(stage => stage.id === 'intent');
  assert.equal(intent.eventCount, names.length);
  assert.equal(intent.sessionCount, names.length);
  assert.equal(intent.qualifiedCount, names.length);
});

test('all admin views ignore query-string keys and accept the header', async () => {
  for (const route of ['/api/leads?key=header-only-test-key', '/api/traffic?key=header-only-test-key']) {
    const queryOnly = await fetch(base + route);
    assert.equal(queryOnly.status, 401, route);
  }

  const headers = { 'x-leads-key': 'header-only-test-key' };
  const leads = await fetch(base + '/api/leads?format=json', { headers });
  assert.equal(leads.status, 200);
  assert.equal(leads.headers.get('cache-control'), 'no-store');
  const traffic = await fetch(base + '/api/traffic?format=json', { headers });
  assert.equal(traffic.status, 200);
  assert.equal(traffic.headers.get('cache-control'), 'no-store');
});

test('traffic dashboard shows an honest session funnel and correlation IDs', async () => {
  const rows = [
    { name: 'page_view', sessionId: 'session-funnel-a', path: '/' },
    { name: 'pricing_cta_click', sessionId: 'session-funnel-a', path: '/' },
    { name: 'lead_submit_success', sessionId: 'session-funnel-a', path: '/', receipt: 'lead_funnel_a' },
    { name: 'calendar_booking_success', sessionId: 'session-funnel-a', path: '/call', bookingUid: 'booking_funnel_a' },
    { name: 'page_view', sessionId: 'session-funnel-b', path: '/' },
    { name: 'chat_first_message', sessionId: 'session-funnel-b', path: '/' },
    // A direct booking is a real outcome but not a lead -> booking progression.
    { name: 'calendar_booking_success', sessionId: 'session-funnel-b', path: '/call', bookingUid: 'booking_direct_b' },
    { name: 'page_view', sessionId: 'session-funnel-c', path: '/' },
    // Legacy records remain in event counts but cannot enter session rates.
    { name: 'quote_form_start', path: '/quote' }
  ].map((row, index) => ({
    ts: `2026-08-22T12:01:${String(index).padStart(2, '0')}.000Z`,
    ...row
  }));
  fs.appendFileSync(EVENTS_FILE, rows.map(row => JSON.stringify(row)).join('\n') + '\n');

  const response = await fetch(base + '/api/traffic', {
    headers: { 'x-leads-key': 'header-only-test-key' }
  });
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /data-stage="page"><td>page view<\/td><td>3<\/td><td>3<\/td><td>baseline<\/td>/);
  assert.match(html, /data-stage="intent"><td>high-intent action<\/td><td>3<\/td><td>2<\/td><td>2\/3 · 66\.7%<\/td>/);
  assert.match(html, /data-stage="lead"><td>lead accepted by API<\/td><td>1<\/td><td>1<\/td><td>1\/2 · 50%<\/td>/);
  assert.match(html, /data-stage="booking"><td>embedded calendar success signal<\/td><td>2<\/td><td>2<\/td><td>1\/1 · 100%<\/td>/);
  assert.match(html, /exclude 1 of 9 funnel records with no session ID/);
  assert.match(html, /receipt lead_funnel_a/);
  assert.match(html, /booking booking_funnel_a/);
  assert.match(html, /booking booking_direct_b/);
});

test('traffic dashboard explains that an AI referrer does not prove a citation', async () => {
  fs.appendFileSync(EVENTS_FILE, JSON.stringify({
    ts: '2026-08-22T12:02:00.000Z',
    name: 'page_view',
    sessionId: 'session-ai-referral',
    path: '/',
    firstRef: 'https://chatgpt.com'
  }) + '\n');

  const response = await fetch(base + '/api/traffic', {
    headers: { 'x-leads-key': 'header-only-test-key' }
  });
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /AI referral — ChatGPT/);
  assert.match(html, /does not prove Leon Builds was cited, mentioned, or recommended in an answer/i);
});

test('traffic HTML escapes every historical event field', async () => {
  const poisoned = {
    ts: '2026-08-22T12:00:00.000Z',
    name: '<img src=x onerror=alert(1)>',
    path: '</td><script>alert(2)</script>',
    firstUtm: '<svg onload=alert(3)>',
    lastUtm: 'safe',
    receipt: '<b id=receipt-poison>owned</b>',
    bookingUid: '</td><script>alert(4)</script>'
  };
  fs.appendFileSync(EVENTS_FILE, JSON.stringify(poisoned) + '\n');

  const response = await fetch(base + '/api/traffic', {
    headers: { 'x-leads-key': 'header-only-test-key' }
  });
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.equal(html.includes('<img src=x onerror=alert(1)>'), false);
  assert.equal(html.includes('</td><script>alert(2)</script>'), false);
  assert.equal(html.includes('<svg onload=alert(3)>'), false);
  assert.equal(html.includes('<b id=receipt-poison>owned</b>'), false);
  assert.equal(html.includes('</td><script>alert(4)</script>'), false);
  assert.match(html, /&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.match(html, /&lt;\/td&gt;&lt;script&gt;alert\(2\)&lt;\/script&gt;/);
  assert.match(html, /&lt;svg onload=alert\(3\)&gt;/);
  assert.match(html, /receipt &lt;b id=receipt-poison&gt;owned&lt;\/b&gt;/);
  assert.match(html, /booking &lt;\/td&gt;&lt;script&gt;alert\(4\)&lt;\/script&gt;/);
});

test('API host never serves the site, content ledger, tests, or repository files', async () => {
  for (const route of ['/', '/index.html', '/content/publication-ledger.csv', '/tests/lead-delivery.test.js', '/package.json']) {
    const response = await fetch(base + route);
    assert.equal(response.status, 404, route);
  }
  const health = await fetch(base + '/api/health');
  assert.equal(health.status, 200);
});

test('chat failure before the first byte is a non-2xx JSON response', async () => {
  app.locals.chatStreamFactory = async () => { throw new Error('provider unavailable'); };
  try {
    const response = await postJson('/api/chat', chatBody());
    assert.equal(response.status, 502);
    const body = await response.json();
    assert.match(body.error, /email/i);
  } finally {
    delete app.locals.chatStreamFactory;
  }
});

test('chat failure after a text delta aborts the body instead of appending an error', async () => {
  app.locals.chatStreamFactory = async () => (async function * partialThenFail() {
    yield { type: 'response.output_text.delta', delta: 'partial answer' };
    await new Promise(resolve => setTimeout(resolve, 5));
    throw new Error('provider stream failed');
  }());

  try {
    const result = await new Promise((resolve, reject) => {
      const request = http.request(base + '/api/chat', {
        method: 'POST',
        headers: { 'content-type': 'application/json' }
      }, (response) => {
        let body = '';
        response.setEncoding('utf8');
        response.on('data', chunk => { body += chunk; });
        response.on('aborted', () => resolve({ status: response.statusCode, body, aborted: true }));
        response.on('end', () => resolve({ status: response.statusCode, body, aborted: false }));
        response.on('error', () => resolve({ status: response.statusCode, body, aborted: true }));
      });
      request.on('error', reject);
      request.end(JSON.stringify(chatBody()));
    });
    assert.equal(result.status, 200);
    assert.equal(result.body, 'partial answer');
    assert.equal(result.aborted, true);
  } finally {
    delete app.locals.chatStreamFactory;
  }
});

test('chat timeout before the first byte returns 504 so the client can hand off', async () => {
  app.locals.chatTimeoutMs = 20;
  app.locals.chatStreamFactory = async (request, options) => new Promise((resolve, reject) => {
    options.signal.addEventListener('abort', () => reject(new Error('aborted by timeout')), { once: true });
  });
  try {
    const response = await postJson('/api/chat', chatBody());
    assert.equal(response.status, 504);
    const body = await response.json();
    assert.match(body.error, /email/i);
  } finally {
    delete app.locals.chatTimeoutMs;
    delete app.locals.chatStreamFactory;
  }
});

test('chat requires a one-time human handoff when useful project context exists', async () => {
  const captured = [];
  app.locals.chatStreamFactory = async (request) => {
    captured.push(request);
    return (async function * reply() {
      yield { type: 'response.output_text.delta', delta: 'A short useful answer.' };
    }());
  };
  try {
    const ready = await postJson('/api/chat', {
      sessionId: 'handoff-ready-session',
      page: '/services/business-automation',
      lang: 'en',
      handoffOffered: false,
      messages: [
        { role: 'user', content: 'I manage rental properties and produce tenant document packs by hand.' },
        { role: 'assistant', content: 'A small document tool could create those from your existing data.' },
        { role: 'user', content: 'The data is in spreadsheets and folders of Word files.' }
      ]
    });
    assert.equal(ready.status, 200);
    await ready.text();
    assert.match(captured[0].instructions, /HANDOFF THIS TURN/);
    assert.match(captured[0].instructions, /I have enough to brief Leon\. Would you like me to send this project to him\?/);
    assert.match(captured[0].instructions, /do not ask another discovery question/i);

    const alreadyShown = await postJson('/api/chat', {
      sessionId: 'handoff-once-session',
      page: '/',
      lang: 'en',
      handoffOffered: true,
      messages: [
        { role: 'user', content: 'I manage rental properties and produce tenant document packs by hand.' },
        { role: 'assistant', content: 'Would you like me to send this project to Leon?' },
        { role: 'user', content: 'Not yet, I have another question.' }
      ]
    });
    assert.equal(alreadyShown.status, 200);
    await alreadyShown.text();
    assert.doesNotMatch(captured[1].instructions, /HANDOFF THIS TURN/);
  } finally {
    delete app.locals.chatStreamFactory;
  }
});
