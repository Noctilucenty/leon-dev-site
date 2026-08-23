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
process.env.CAL_WEBHOOK_SECRET = 'cal-webhook-test-secret';
process.env.LEADS_KEY = 'acquisition-admin-test-key';
process.env.OPENAI_API_KEY = '';

const { app } = require('../server/index');
const {
  FUNNEL_STAGES,
  acquisitionStorageConfig,
  deliverToSink,
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
