'use strict';

const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { after, before, test } = require('node:test');

const TEMP_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'leon-acquisition-test-'));
const ACQUISITION_FILE = path.join(TEMP_DIR, 'acquisition.jsonl');
process.env.NODE_ENV = 'test';
process.env.ACQUISITION_FILE = ACQUISITION_FILE;
process.env.EVENTS_FILE = path.join(TEMP_DIR, 'events.jsonl');
process.env.LEADS_FILE = path.join(TEMP_DIR, 'leads.jsonl');
process.env.CAL_WEBHOOK_SECRET = 'cal-webhook-test-secret';
process.env.LEADS_KEY = 'acquisition-admin-test-key';
process.env.OPENAI_API_KEY = '';

const { app } = require('../server/index');
const {
  FUNNEL_STAGES,
  acquisitionStats,
  acquisitionStorageConfig,
  deliverToSink,
  normalizeQaExclusion,
  verifyCalSignature
} = require('../server/acquisition');

let server;
let base;

before(async () => {
  await new Promise(resolve => { server = app.listen(0, '127.0.0.1', resolve); });
  base = `http://127.0.0.1:${server.address().port}`;
});

after(async () => {
  if (server) await new Promise(resolve => server.close(resolve));
  fs.rmSync(TEMP_DIR, { recursive: true, force: true });
});

function rows() {
  if (!fs.existsSync(ACQUISITION_FILE)) return [];
  return fs.readFileSync(ACQUISITION_FILE, 'utf8').trim().split('\n').filter(Boolean).map(JSON.parse);
}

function sign(raw, secret = process.env.CAL_WEBHOOK_SECRET) {
  return crypto.createHmac('sha256', secret).update(raw).digest('hex');
}

function postWebhook(payload, signature) {
  const raw = JSON.stringify(payload);
  return fetch(base + '/api/cal/webhook', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-cal-signature-256': signature || sign(raw)
    },
    body: raw
  });
}

function postAdmin(body, key = 'acquisition-admin-test-key') {
  return fetch(base + '/api/acquisition/stage', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-leads-key': key },
    body: JSON.stringify(body)
  });
}

function postExclusion(body, key = 'acquisition-admin-test-key') {
  return fetch(base + '/api/acquisition/exclusions', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-leads-key': key },
    body: JSON.stringify(body)
  });
}

test('Cal HMAC verification uses the exact raw bytes', () => {
  const raw = Buffer.from('{"triggerEvent":"BOOKING_CREATED"}');
  assert.equal(verifyCalSignature(raw, sign(raw), process.env.CAL_WEBHOOK_SECRET), true);
  assert.equal(verifyCalSignature(raw, 'sha256=' + sign(raw), process.env.CAL_WEBHOOK_SECRET), true);
  assert.equal(verifyCalSignature(Buffer.from(raw + ' '), sign(raw), process.env.CAL_WEBHOOK_SECRET), false);
  assert.equal(verifyCalSignature(raw, 'not-a-signature', process.env.CAL_WEBHOOK_SECRET), false);
});

test('unsigned or incorrectly signed Cal requests never create a record', async () => {
  const response = await postWebhook({ triggerEvent: 'BOOKING_CREATED', payload: { uid: 'cal_invalid_1' } }, '0'.repeat(64));
  assert.equal(response.status, 401);
  assert.deepEqual(rows(), []);
});

test('signed Cal booking is minimized, attributed and deduped by booking UID plus stage', async () => {
  const webhook = {
    triggerEvent: 'BOOKING_CREATED',
    createdAt: '2026-08-23T17:00:00.000Z',
    payload: {
      uid: 'cal_booking_1',
      title: 'Private discovery call',
      attendees: [{ name: 'Private Person', email: 'private@example.com' }],
      metadata: {
        utm_source: 'google',
        utm_medium: 'cpc',
        utm_campaign: 'bay area websites',
        utm_term: 'small business developer',
        gclid: 'opaque.Google-Click_Id'
      },
      responses: {
        utm_content: { label: 'Campaign creative', value: 'rsa-proof-1', isHidden: true },
        privateAnswer: { value: 'Never store this answer' }
      }
    }
  };
  let response = await postWebhook(webhook);
  assert.equal(response.status, 204);
  response = await postWebhook(webhook);
  assert.equal(response.status, 204);

  const stored = rows();
  assert.equal(stored.length, 1);
  assert.equal(stored[0].stage, 'booked');
  assert.equal(stored[0].bookingUid, 'cal_booking_1');
  assert.equal(stored[0].dedupeKey, 'booking:cal_booking_1:stage:booked');
  assert.deepEqual(stored[0].attribution, {
    utmSource: 'google',
    utmMedium: 'cpc',
    utmCampaign: 'bay area websites',
    utmTerm: 'small business developer',
    utmContent: 'rsa-proof-1',
    gclid: 'opaque.Google-Click_Id'
  });
  const serialized = JSON.stringify(stored[0]);
  assert.equal(serialized.includes('Private Person'), false);
  assert.equal(serialized.includes('private@example.com'), false);
  assert.equal(serialized.includes('Never store this answer'), false);
});

test('Cal only maps authoritative lifecycle signals', async () => {
  const ended = await postWebhook({
    triggerEvent: 'MEETING_ENDED',
    payload: { uid: 'cal_booking_1' }
  });
  assert.equal(ended.status, 204);
  assert.equal(rows().length, 1);

  const noShow = await postWebhook({
    triggerEvent: 'BOOKING_NO_SHOW_UPDATED',
    payload: { uid: 'cal_booking_1', attendees: [{ noShow: true }] }
  });
  assert.equal(noShow.status, 204);
  const cancelled = await postWebhook({
    triggerEvent: 'BOOKING_CANCELLED',
    payload: { uid: 'cal_booking_1' }
  });
  assert.equal(cancelled.status, 204);
  assert.deepEqual(rows().map(row => row.stage), ['booked', 'no-show', 'cancelled']);
});

test('Cal reschedules use the new UID and retain the documented prior UID', async () => {
  const response = await postWebhook({
    triggerEvent: 'BOOKING_RESCHEDULED',
    createdAt: '2026-08-23T18:00:00.000Z',
    payload: {
      uid: 'cal_booking_rescheduled_new',
      rescheduleUid: 'cal_booking_rescheduled_old'
    }
  });
  assert.equal(response.status, 204);
  const stored = rows().at(-1);
  assert.equal(stored.bookingUid, 'cal_booking_rescheduled_new');
  assert.equal(stored.stage, 'booked');
  assert.equal(stored.context.previousBookingUid, 'cal_booking_rescheduled_old');
});

test('Cal reschedules remain one active booking in acquisition reporting', () => {
  const funnel = acquisitionStats([
    {
      kind: 'funnel_stage', stage: 'booked', bookingUid: 'cal_chain_original',
      occurredAt: '2026-08-23T17:30:00.000Z', attribution: { utmSource: 'google' }, context: {}
    },
    {
      kind: 'booking_attribution', bookingUid: 'cal_chain_original',
      firstAttribution: { gclid: 'gclid.original' }, lastAttribution: { utmMedium: 'cpc' }
    },
    {
      kind: 'funnel_stage', stage: 'booked', bookingUid: 'cal_chain_new',
      occurredAt: '2026-08-23T18:30:00.000Z', attribution: {},
      context: { previousBookingUid: 'cal_chain_original' }
    },
    {
      kind: 'funnel_stage', stage: 'cancelled', bookingUid: 'cal_chain_original',
      occurredAt: '2026-08-23T18:31:00.000Z', attribution: {}, context: {}
    }
  ]);
  assert.equal(funnel.stageCounts.booked, 1);
  assert.equal(funnel.stageCounts.cancelled, 0, 'the superseded slot is not a cancelled opportunity');
  assert.equal(funnel.bookingCount, 1);
  assert.equal(funnel.latestByBooking[0].bookingUid, 'cal_chain_new');
  assert.equal(funnel.latestByBooking[0].stage, 'booked');
  assert.equal(funnel.latestByBooking[0].attribution.utmSource, 'google');
  assert.equal(funnel.latestByBooking[0].attribution.utmMedium, 'cpc');
  assert.equal(funnel.latestByBooking[0].firstAttribution.gclid, 'gclid.original');
});

test('browser booking signal enriches attribution without creating a stage', async () => {
  const event = {
    name: 'calendar_booking_success',
    path: '/call',
    sessionId: 'session-booking-attribution-1',
    bookingUid: 'cal_booking_1',
    firstUtmSource: 'google',
    firstUtmMedium: 'cpc',
    firstUtmCampaign: 'first-campaign',
    firstGclid: 'gclid.browser-first',
    lastUtmSource: 'meta',
    lastUtmMedium: 'paid-social',
    lastUtmCampaign: 'retargeting',
    lastUtmContent: 'ad-02-flow',
    lastFbclid: 'fbclid.browser-last'
  };
  for (let index = 0; index < 2; index += 1) {
    const response = await fetch(base + '/api/event', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(event)
    });
    assert.equal(response.status, 204);
  }
  const enrichment = rows().filter(row => row.kind === 'booking_attribution');
  assert.equal(enrichment.length, 1);
  assert.equal(enrichment[0].authoritative, false);
  assert.equal(enrichment[0].firstAttribution.gclid, 'gclid.browser-first');
  assert.equal(enrichment[0].lastAttribution.fbclid, 'fbclid.browser-last');
  assert.equal(enrichment.some(row => row.stage), false);
});

test('admin QA exclusions are append-only, authenticated and idempotent', async () => {
  const bookingUid = 'cal_booking_qa_excluded';
  const receiptId = 'lead_11111111-1111-4111-8111-111111111111';
  let response = await postWebhook({
    triggerEvent: 'BOOKING_CREATED',
    payload: { uid: bookingUid }
  });
  assert.equal(response.status, 204);

  const queryOnly = await fetch(base + '/api/acquisition/exclusions?key=acquisition-admin-test-key', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ bookingUid, confirmSynthetic: true })
  });
  assert.equal(queryOnly.status, 401);
  response = await postExclusion({ bookingUid });
  assert.equal(response.status, 400, 'synthetic intent must be confirmed explicitly');
  response = await postExclusion({ bookingUid, receiptId, confirmSynthetic: true });
  assert.equal(response.status, 400, 'one append may target only one exact identifier');
  response = await postExclusion({ bookingUid: bookingUid + 'x'.repeat(160), confirmSynthetic: true });
  assert.equal(response.status, 400, 'overlong exact identifiers must never be truncated');
  response = await postExclusion({ bookingUid: 'EXACT_CAL_BOOKING_UID', confirmSynthetic: true });
  assert.equal(response.status, 409, 'a valid-looking typo cannot create a permanent exclusion');

  response = await postExclusion({ bookingUid, confirmSynthetic: true });
  assert.equal(response.status, 201);
  let result = await response.json();
  const bookingExclusionRecordId = result.recordId;
  assert.equal(result.duplicate, false);
  assert.equal(result.targetType, 'booking');
  assert.equal(result.targetId, bookingUid);
  assert.equal(result.dedupeKey, `qa-exclusion:booking:${bookingUid}`);
  response = await postExclusion({ bookingUid, confirmSynthetic: true });
  assert.equal(response.status, 200);
  result = await response.json();
  assert.equal(result.duplicate, true);
  assert.equal(result.recordId, bookingExclusionRecordId,
    'an idempotent replay returns the persisted exclusion record');

  fs.appendFileSync(process.env.LEADS_FILE, JSON.stringify({
    ts: '2026-09-01T11:59:00.000Z',
    receiptId: 'lead_22222222-2222-4222-8222-222222222222',
    name: 'Real Lead',
    email: 'real@example.com',
    via: 'quote-form'
  }) + '\n');
  fs.appendFileSync(process.env.LEADS_FILE, JSON.stringify({
    ts: '2026-09-01T12:00:00.000Z',
    receiptId,
    name: 'QA Verification',
    email: 'qa@example.com',
    analyticsSessionId: 'session-qa-quote',
    via: 'quote-form'
  }) + '\n');
  for (const event of [
    { ts: '2026-09-01T12:00:00.000Z', name: 'page_view', sessionId: 'session-qa-quote' },
    { ts: '2026-09-01T12:01:00.000Z', name: 'calendar_booking_success', sessionId: 'session-qa-booking', bookingUid },
    { ts: '2026-09-01T12:02:00.000Z', name: 'lead_submit_success', receipt: receiptId },
    { ts: '2026-09-01T12:03:00.000Z', name: 'calendar_booking_success', bookingUid },
    { ts: '2026-09-01T12:04:00.000Z', name: 'page_view', sessionId: 'session-real-traffic' }
  ]) {
    fs.appendFileSync(process.env.EVENTS_FILE, JSON.stringify(event) + '\n');
  }
  response = await postExclusion({ receiptId, confirmSynthetic: true });
  assert.equal(response.status, 201);
  const receiptExclusionRecordId = (await response.json()).recordId;
  response = await postExclusion({ receiptId, confirmSynthetic: true });
  assert.equal(response.status, 200);
  result = await response.json();
  assert.equal(result.duplicate, true);
  assert.equal(result.recordId, receiptExclusionRecordId);

  let leadDashboard = await fetch(base + '/api/leads?format=json&limit=1', {
    headers: { 'x-leads-key': 'acquisition-admin-test-key' }
  });
  let leadBody = await leadDashboard.json();
  assert.equal(leadBody.count, 1, 'filtering happens before the requested limit');
  assert.equal(leadBody.qaExcludedCount, 1);
  assert.equal(leadBody.leads[0].email, 'real@example.com');
  leadDashboard = await fetch(base + '/api/leads?format=json&includeQaExcluded=1&limit=1', {
    headers: { 'x-leads-key': 'acquisition-admin-test-key' }
  });
  leadBody = await leadDashboard.json();
  assert.equal(leadBody.count, 1);
  assert.equal(leadBody.leads[0].receiptId, receiptId);

  let trafficDashboard = await fetch(base + '/api/traffic?format=json', {
    headers: { 'x-leads-key': 'acquisition-admin-test-key' }
  });
  let trafficBody = await trafficDashboard.json();
  assert.equal(trafficBody.qaExcludedEventCount, 4);
  assert.equal(trafficBody.qaExcludedSessionCount, 2);
  assert.equal(trafficBody.events.some(event => event.sessionId === 'session-qa-quote'), false);
  assert.equal(trafficBody.events.some(event => event.sessionId === 'session-qa-booking'), false);
  assert.equal(trafficBody.events.some(event => event.receipt === receiptId), false);
  assert.equal(trafficBody.events.some(event => event.bookingUid === bookingUid), false);
  assert.equal(trafficBody.events.some(event => event.sessionId === 'session-real-traffic'), true);
  trafficDashboard = await fetch(base + '/api/traffic?format=json&includeQaExcluded=1', {
    headers: { 'x-leads-key': 'acquisition-admin-test-key' }
  });
  trafficBody = await trafficDashboard.json();
  assert.equal(trafficBody.events.some(event => event.receipt === receiptId), true);
  assert.equal(trafficBody.events.some(event => event.bookingUid === bookingUid), true);

  const exclusionRows = rows().filter(row => row.kind === 'qa_exclusion');
  assert.equal(exclusionRows.length, 2);
  assert.deepEqual(
    new Set(exclusionRows.map(row => row.dedupeKey)),
    new Set([
      `qa-exclusion:booking:${bookingUid}`,
      `qa-exclusion:receipt:${receiptId}`
    ])
  );

  const dashboard = await fetch(base + '/api/acquisition?format=json', {
    headers: { 'x-leads-key': 'acquisition-admin-test-key' }
  });
  assert.equal(dashboard.status, 200);
  const body = await dashboard.json();
  assert.equal(body.exclusions.count, 2);
  assert.equal(body.exclusions.targetsApplied, 2);
  assert.deepEqual(body.exclusions.bookingUids, [bookingUid]);
  assert.deepEqual(body.exclusions.receiptIds, [receiptId]);
  assert.equal(body.funnel.qaExclusions.bookingUidsConfigured, 1);
  assert.equal(body.funnel.qaExclusions.recordsExcluded, 1);
  assert.equal(body.funnel.latestByBooking.some(row => row.bookingUid === bookingUid), false);
  assert.equal(body.records.some(row => row.kind === 'funnel_stage' && row.bookingUid === bookingUid), true,
    'the source booking remains in the append-only ledger');

  const leadLedgerSnapshot = fs.readFileSync(process.env.LEADS_FILE);
  try {
    fs.appendFileSync(process.env.LEADS_FILE, '{corrupt lead row\n');
    response = await postExclusion({
      receiptId: 'lead_44444444-4444-4444-8444-444444444444',
      confirmSynthetic: true
    });
    assert.equal(response.status, 503, 'a corrupt lead ledger fails closed');
  } finally {
    fs.writeFileSync(process.env.LEADS_FILE, leadLedgerSnapshot);
  }

  const eventLedgerSnapshot = fs.readFileSync(process.env.EVENTS_FILE);
  try {
    fs.appendFileSync(process.env.EVENTS_FILE, '{corrupt event row\n');
    response = await fetch(base + '/api/traffic?format=json', {
      headers: { 'x-leads-key': 'acquisition-admin-test-key' }
    });
    assert.equal(response.status, 503, 'a corrupt event ledger fails closed');
  } finally {
    fs.writeFileSync(process.env.EVENTS_FILE, eventLedgerSnapshot);
  }
});

test('booking QA exclusion follows a reschedule chain', () => {
  const rows = [
    {
      kind: 'funnel_stage', stage: 'booked', bookingUid: 'qa_chain_original',
      occurredAt: '2026-08-23T17:30:00.000Z', attribution: {}, context: {}
    },
    {
      kind: 'funnel_stage', stage: 'booked', bookingUid: 'qa_chain_replacement',
      occurredAt: '2026-08-23T18:30:00.000Z', attribution: {},
      context: { previousBookingUid: 'qa_chain_original' }
    }
  ];
  const exclusions = [{
    kind: 'qa_exclusion',
    targetType: 'booking',
    targetId: 'qa_chain_original',
    bookingUid: 'qa_chain_original',
    dedupeKey: 'qa-exclusion:booking:qa_chain_original'
  }];
  const funnel = acquisitionStats(rows, exclusions);
  assert.equal(funnel.bookingCount, 0);
  assert.equal(funnel.stageCounts.booked, 0);
  assert.equal(funnel.qaExclusions.bookingUidsConfigured, 1);
  assert.equal(funnel.qaExclusions.recordsExcluded, 2);
});

test('QA exclusion normalization rejects ambiguous or altered identifiers', () => {
  const receiptId = 'lead_33333333-3333-4333-8333-333333333333';
  assert.match(normalizeQaExclusion({ receiptId, confirmSynthetic: true }).record.dedupeKey,
    /qa-exclusion:receipt:/);
  assert.equal(normalizeQaExclusion({
    receiptId,
    bookingUid: 'booking_valid',
    confirmSynthetic: true
  }).error, 'provide exactly one receiptId or bookingUid');
  assert.equal(normalizeQaExclusion({
    bookingUid: 'b'.repeat(161),
    confirmSynthetic: true
  }).error, 'bookingUid must be an exact 8-160 character Cal identifier');
  assert.equal(normalizeQaExclusion({
    receiptId: receiptId + 'x',
    confirmSynthetic: true
  }).error, 'receiptId must be an exact lead UUID');
});

test('manual admin route defines the complete opportunity funnel and dedupes updates', async () => {
  const queryOnly = await fetch(base + '/api/acquisition/stage?key=acquisition-admin-test-key', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ bookingUid: 'cal_booking_2', stage: 'qualified' })
  });
  assert.equal(queryOnly.status, 401);

  let response = await postAdmin({ bookingUid: 'cal_booking_2', stage: 'attended' });
  assert.equal(response.status, 201);
  response = await postAdmin({ bookingUid: 'cal_booking_2', stage: 'qualified' });
  assert.equal(response.status, 201);
  response = await postAdmin({ bookingUid: 'cal_booking_2', stage: 'qualified' });
  assert.equal(response.status, 200);
  assert.equal((await response.json()).duplicate, true);
  response = await postAdmin({ bookingUid: 'cal_booking_2', stage: 'not-real' });
  assert.equal(response.status, 400);

  const dashboard = await fetch(base + '/api/acquisition?format=json', {
    headers: { 'x-leads-key': 'acquisition-admin-test-key' }
  });
  assert.equal(dashboard.status, 200);
  assert.equal(dashboard.headers.get('cache-control'), 'no-store');
  const body = await dashboard.json();
  assert.deepEqual(Object.keys(body.stages), FUNNEL_STAGES);
  assert.equal(body.funnel.stageCounts.attended, 1);
  assert.equal(body.funnel.stageCounts.qualified, 1);
  const cancelled = body.funnel.latestByBooking.find(row => row.bookingUid === 'cal_booking_1');
  assert.equal(cancelled.stage, 'cancelled');
  assert.equal(cancelled.attribution.utmSource, 'google');
  assert.equal(cancelled.attribution.fbclid, 'fbclid.browser-last');
  assert.equal(cancelled.firstAttribution.gclid, 'gclid.browser-first');
  assert.equal(cancelled.browserAttributionObserved, true);

  const htmlResponse = await fetch(base + '/api/acquisition', {
    headers: { 'x-leads-key': 'acquisition-admin-test-key' }
  });
  assert.equal(htmlResponse.status, 200);
  assert.match(htmlResponse.headers.get('content-type'), /^text\/html/);
  const html = await htmlResponse.text();
  assert.match(html, /acquisition — \d+ bookings/);
  assert.match(html, /<td>qualified<\/td><td>1<\/td>/);
  assert.match(html, /<code>cal_booking_1<\/code><\/td><td>cancelled<\/td>/);
  assert.match(html, /gclid, fbclid/);
});

test('health reports whether acquisition storage is actually durable', async () => {
  const response = await fetch(base + '/api/health');
  const health = await response.json();
  assert.equal(response.status, 200);
  assert.equal(health.acquisitionStorageState, 'ephemeral-only');
  assert.equal(health.acquisitionDurableConfigured, false);
  assert.equal(health.calWebhookConfigured, true);

  assert.equal(acquisitionStorageConfig({ LEON_DATA_DIR: '/var/data/leon-builds' }).durableConfigured, true);
  assert.equal(acquisitionStorageConfig({ ACQUISITION_SINK_URL: 'http://public.example/webhook' }).state, 'invalid-sink-configuration');
  assert.equal(acquisitionStorageConfig({ ACQUISITION_SINK_URL: 'https://crm.example/events' }).sinkReady, false);
  assert.equal(acquisitionStorageConfig({
    ACQUISITION_SINK_URL: 'https://crm.example/events',
    ACQUISITION_SINK_TOKEN: 'configured'
  }).sinkReady, true);
});

test('Render blueprint stays on Starter and contains no secret value', () => {
  const blueprint = fs.readFileSync(path.join(__dirname, '..', 'render.yaml'), 'utf8');
  assert.match(blueprint, /^\s*plan: starter\s*$/m);
  assert.doesNotMatch(blueprint, /^\s*plan: free\s*$/m);
  assert.match(blueprint, /key: CAL_WEBHOOK_SECRET[\s\S]*?sync: false/);
  assert.equal(blueprint.includes(process.env.CAL_WEBHOOK_SECRET), false);
});

test('optional HTTPS sink sends a signed, idempotent envelope', async t => {
  let received;
  const sinkServer = http.createServer((request, response) => {
    let body = '';
    request.setEncoding('utf8');
    request.on('data', chunk => { body += chunk; });
    request.on('end', () => {
      received = { headers: request.headers, body };
      response.writeHead(204).end();
    });
  });
  await new Promise(resolve => sinkServer.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise(resolve => sinkServer.close(resolve)));
  const sinkUrl = `http://127.0.0.1:${sinkServer.address().port}/ingest`;
  const record = {
    recordId: 'acq_sink_test',
    dedupeKey: 'booking:cal_sink_1:stage:booked',
    stage: 'booked'
  };
  const result = await deliverToSink(record, {
    NODE_ENV: 'test',
    ACQUISITION_SINK_URL: sinkUrl,
    ACQUISITION_SINK_TOKEN: 'sink-token',
    ACQUISITION_SINK_SECRET: 'sink-secret'
  });
  assert.deepEqual(result, { attempted: true, ok: true });
  assert.equal(received.headers.authorization, 'Bearer sink-token');
  assert.equal(received.headers['x-leon-event-id'], record.recordId);
  assert.equal(received.headers['x-leon-dedupe-key'], record.dedupeKey);
  assert.equal(received.headers['x-leon-signature-256'], 'sha256=' + crypto
    .createHmac('sha256', 'sink-secret')
    .update(received.body)
    .digest('hex'));
  assert.deepEqual(JSON.parse(received.body), record);
});
