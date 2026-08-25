'use strict';

const assert = require('node:assert/strict');
const { once } = require('node:events');
const fs = require('node:fs');
const test = require('node:test');

const {
  confirmLeadEmailInbox,
  drainLeadEmailOutbox,
  leadDeliveryConfig,
  leadEmailVerification,
  leadEmailStatus,
  maskEmail,
  persistLead,
  readLeadEmailOutbox,
  readLeads,
  validateLead
} = require('../server/leads');
const { app } = require('../server/index');

const DELIVERY_KEYS = [
  'RENDER',
  'RENDER_SERVICE_ID',
  'RESEND_API_KEY',
  'LEAD_TO_EMAIL',
  'LEAD_FROM_EMAIL',
  'SMTP_HOST',
  'SMTP_PORT',
  'SMTP_USER',
  'SMTP_PASS',
  'LEADS_KEY'
];

function useDeliveryEnv(values) {
  const saved = Object.fromEntries(DELIVERY_KEYS.map(k => [k, process.env[k]]));
  for (const key of DELIVERY_KEYS) delete process.env[key];
  for (const [key, value] of Object.entries(values)) process.env[key] = value;
  return () => {
    for (const key of DELIVERY_KEYS) {
      if (saved[key] === undefined) delete process.env[key];
      else process.env[key] = saved[key];
    }
  };
}

test('Resend is the supported Render provider and takes precedence over SMTP', () => {
  const status = leadDeliveryConfig({
    RENDER: 'true',
    RESEND_API_KEY: 'test-key',
    LEAD_TO_EMAIL: 'leon@example.com',
    SMTP_HOST: 'smtp.example.com',
    SMTP_USER: 'user',
    SMTP_PASS: 'pass'
  });

  assert.equal(status.provider, 'resend');
  assert.equal(status.transport, 'https');
  assert.equal(status.configured, true);
  assert.equal(status.supported, true);
  assert.equal(status.ready, true);
  assert.equal(status.state, 'configured_unverified');
  assert.deepEqual(status.missing, []);
});

test('complete SMTP configuration is blocked, not ready, on Render', () => {
  const status = leadDeliveryConfig({
    RENDER_SERVICE_ID: 'srv-test',
    LEAD_TO_EMAIL: 'leon@example.com',
    SMTP_HOST: 'smtp.example.com',
    SMTP_USER: 'user',
    SMTP_PASS: 'pass'
  });

  assert.equal(status.provider, 'smtp');
  assert.equal(status.configured, true);
  assert.equal(status.supported, false);
  assert.equal(status.ready, false);
  assert.equal(status.state, 'blocked');
  assert.match(status.warning, /outbound SMTP is unavailable/i);
  assert.deepEqual(status.missing, ['RESEND_API_KEY']);
  assert.deepEqual(status.providers.smtp.missing, []);
});

test('SMTP remains available off Render and its port has a default', () => {
  const status = leadDeliveryConfig({
    LEAD_TO_EMAIL: 'leon@example.com',
    SMTP_HOST: 'smtp.example.com',
    SMTP_USER: 'user',
    SMTP_PASS: 'pass'
  });

  assert.equal(status.provider, 'smtp');
  assert.equal(status.configured, true);
  assert.equal(status.supported, true);
  assert.equal(status.ready, true);
  assert.deepEqual(status.missing, []);
});

test('partial routes report only their actionable missing fields', () => {
  const resend = leadDeliveryConfig({ RESEND_API_KEY: 'test-key' });
  assert.equal(resend.provider, 'resend');
  assert.equal(resend.state, 'incomplete');
  assert.deepEqual(resend.missing, ['LEAD_TO_EMAIL']);

  const smtp = leadDeliveryConfig({
    LEAD_TO_EMAIL: 'leon@example.com',
    SMTP_HOST: 'smtp.example.com'
  });
  assert.equal(smtp.provider, 'smtp');
  assert.equal(smtp.state, 'incomplete');
  assert.deepEqual(smtp.missing, ['SMTP_USER', 'SMTP_PASS']);

  const renderSmtp = leadDeliveryConfig({
    RENDER: 'true',
    SMTP_HOST: 'smtp.example.com'
  });
  assert.equal(renderSmtp.state, 'blocked');
  assert.equal(renderSmtp.ready, false);
  assert.deepEqual(renderSmtp.missing, ['RESEND_API_KEY', 'LEAD_TO_EMAIL']);
});

test('recipient masking never returns the full configured address', () => {
  assert.equal(maskEmail('leon@example.com'), 'l***@example.com');
  assert.equal(maskEmail('not-an-email'), '***');
  assert.equal(maskEmail(''), null);
});

test('validated leads and honeypot successes receive opaque receipt IDs', () => {
  const first = validateLead({
    email: 'first@example.com',
    problem: 'Build a booking workflow.'
  }).lead;
  const second = validateLead({
    email: 'second@example.com',
    problem: 'Build an ordering workflow.'
  }).lead;
  const bot = validateLead({ website: 'filled-by-bot' });

  assert.match(first.receiptId, /^lead_[0-9a-f]{8}-[0-9a-f-]{27}$/);
  assert.match(second.receiptId, /^lead_[0-9a-f]{8}-[0-9a-f-]{27}$/);
  assert.match(bot.receiptId, /^lead_[0-9a-f]{8}-[0-9a-f-]{27}$/);
  assert.notEqual(first.receiptId, second.receiptId);
  assert.equal(bot.bot, true);

  const keyed = validateLead({
    email: 'keyed@example.com',
    problem: 'Build a safe retry path.',
    service: 'contractor-lead-recovery',
    idempotencyKey: 'leadreq_12345678-1234-1234-1234-123456789abc'
  });
  assert.equal(keyed.lead.idempotencyKey, 'leadreq_12345678-1234-1234-1234-123456789abc');
  assert.equal(keyed.lead.service, 'contractor-lead-recovery');
  assert.equal(validateLead({
    email: 'bad-key@example.com',
    problem: 'This key contains unsafe punctuation.',
    idempotencyKey: 'leadreq_not/allowed'
  }).error, 'invalid idempotency key');

  const publicSyntheticAttempt = validateLead({
    email: 'ordinary@example.com',
    problem: 'This must remain an ordinary lead.',
    synthetic: true,
    recordType: 'delivery_probe'
  }).lead;
  assert.equal(Object.hasOwn(publicSyntheticAttempt, 'synthetic'), false);
  assert.equal(Object.hasOwn(publicSyntheticAttempt, 'recordType'), false);
});

test('lead validation preserves bounded first/last attribution and anonymous correlation IDs', () => {
  const { lead } = validateLead({
    email: 'attribution@example.com',
    problem: 'Connect the booking flow.',
    sourcePage: '/quote',
    referrer: 'https://facebook.com/groups/example',
    utmSource: 'fbgroup-current',
    utmMedium: 'paid-social',
    utmCampaign: 'august-current',
    utmTerm: 'booking workflow',
    utmContent: 'creative-current',
    gclid: 'gclid.current_123',
    gbraid: 'gbraid-current_123',
    wbraid: 'wbraid-current_123',
    fbclid: 'fbclid.current_123',
    msclkid: '0123456789abcdef0123456789abcdef',
    firstPage: '/',
    firstReferrer: 'https://google.com/search?q=booking',
    firstUtmSource: 'google',
    firstUtmMedium: 'organic',
    firstUtmCampaign: 'evergreen',
    firstUtmTerm: 'website booking',
    firstUtmContent: 'rsa-a',
    firstGclid: 'gclid.first_123',
    firstGbraid: 'gbraid-first_123',
    firstWbraid: 'wbraid-first_123',
    firstFbclid: 'fbclid.first_123',
    firstMsclkid: 'abcdef0123456789abcdef0123456789',
    lastPage: '/quote',
    lastReferrer: 'https://facebook.com/groups/example',
    lastUtmSource: 'fbgroup-current',
    lastUtmMedium: 'social',
    lastUtmCampaign: 'august-post',
    lastUtmTerm: 'follow up automation',
    lastUtmContent: 'carousel-b',
    lastGclid: 'gclid.last_123',
    lastGbraid: 'gbraid-last_123',
    lastWbraid: 'wbraid-last_123',
    lastFbclid: 'fbclid.last_123',
    lastMsclkid: 'fedcba9876543210fedcba9876543210',
    analyticsSessionId: 'session_abc123',
    chatSessionId: 'chat_xyz789'
  });

  assert.equal(lead.firstPage, '/');
  assert.equal(lead.firstUtmSource, 'google');
  assert.equal(lead.firstUtmTerm, 'website booking');
  assert.equal(lead.firstUtmContent, 'rsa-a');
  assert.equal(lead.firstGclid, 'gclid.first_123');
  assert.equal(lead.firstGbraid, 'gbraid-first_123');
  assert.equal(lead.firstWbraid, 'wbraid-first_123');
  assert.equal(lead.firstFbclid, 'fbclid.first_123');
  assert.equal(lead.firstMsclkid, 'abcdef0123456789abcdef0123456789');
  assert.equal(lead.lastPage, '/quote');
  assert.equal(lead.lastUtmSource, 'fbgroup-current');
  assert.equal(lead.lastUtmTerm, 'follow up automation');
  assert.equal(lead.lastUtmContent, 'carousel-b');
  assert.equal(lead.lastGclid, 'gclid.last_123');
  assert.equal(lead.lastGbraid, 'gbraid-last_123');
  assert.equal(lead.lastWbraid, 'wbraid-last_123');
  assert.equal(lead.lastFbclid, 'fbclid.last_123');
  assert.equal(lead.lastMsclkid, 'fedcba9876543210fedcba9876543210');
  assert.equal(lead.utmTerm, 'booking workflow');
  assert.equal(lead.utmContent, 'creative-current');
  assert.equal(lead.gclid, 'gclid.current_123');
  assert.equal(lead.gbraid, 'gbraid-current_123');
  assert.equal(lead.wbraid, 'wbraid-current_123');
  assert.equal(lead.fbclid, 'fbclid.current_123');
  assert.equal(lead.msclkid, '0123456789abcdef0123456789abcdef');
  assert.equal(lead.analyticsSessionId, 'session_abc123');
  assert.equal(lead.chatSessionId, 'chat_xyz789');
});

test('one idempotency key returns one receipt and persists/emails only once', async () => {
  const server = app.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const base = `http://127.0.0.1:${server.address().port}`;
  const restoreEnv = useDeliveryEnv({
    RENDER: 'true',
    RESEND_API_KEY: 'test-key',
    LEAD_TO_EMAIL: 'owner@example.com'
  });
  const original = {
    fetch: global.fetch,
    mkdirSync: fs.mkdirSync,
    appendFileSync: fs.appendFileSync,
    readFileSync: fs.readFileSync,
    log: console.log,
    error: console.error
  };
  const logs = [];
  const errors = [];
  const appended = [];
  const files = new Map();
  const mailRequests = [];

  fs.mkdirSync = () => {};
  fs.appendFileSync = (file, data) => {
    const key = String(file);
    appended.push({ file, data });
    files.set(key, (files.get(key) || '') + data);
  };
  fs.readFileSync = (file, ...args) => {
    const key = String(file);
    if (files.has(key)) return files.get(key);
    if (key.endsWith('/leads.jsonl') || key.endsWith('/lead-email-outbox.jsonl')
        || key.endsWith('/lead-email-confirmations.jsonl')) {
      const error = new Error(`ENOENT: ${key}`);
      error.code = 'ENOENT';
      throw error;
    }
    return original.readFileSync(file, ...args);
  };
  console.log = (...args) => logs.push(args.join(' '));
  console.error = (...args) => errors.push(args.join(' '));
  global.fetch = async (url, options) => {
    if (String(url) === 'https://api.resend.com/emails') {
      mailRequests.push({ url: String(url), options });
      return { ok: true, json: async () => ({ id: 'resend-test-id' }) };
    }
    return original.fetch(url, options);
  };

  try {
    const requestBody = {
      name: 'Pipeline check',
      email: 'pipeline-check@example.com',
      problem: 'Receipt correlation test tag PIPELINE-CHECK-TEST',
      via: 'pipeline-check',
      idempotencyKey: 'leadreq_aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'
    };
    const response = await global.fetch(base + '/api/lead', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(requestBody)
    });
    const result = await response.json();
    const retryResponse = await global.fetch(base + '/api/lead', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(requestBody)
    });
    const retryResult = await retryResponse.json();
    const conflictResponse = await global.fetch(base + '/api/lead', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ ...requestBody, problem: 'A materially different project.' })
    });
    const conflictResult = await conflictResponse.json();
    await new Promise(resolve => setImmediate(resolve));

    assert.equal(response.status, 200);
    assert.equal(result.ok, true);
    assert.match(result.receiptId, /^lead_[0-9a-f-]{36}$/);
    assert.equal(retryResponse.status, 200);
    assert.deepEqual(retryResult, {
      ok: true,
      receiptId: result.receiptId,
      deduplicated: true
    });
    assert.equal(conflictResponse.status, 409);
    assert.match(conflictResult.error, /already used for a different lead/);

    const leadLog = logs.find(line => line.startsWith('LEAD {'));
    assert.ok(leadLog);
    assert.equal(JSON.parse(leadLog.slice(5)).receiptId, result.receiptId);

    assert.equal(appended.length, 3);
    const queuedState = JSON.parse(appended[0].data);
    const durableLead = JSON.parse(appended[1].data);
    const deliveryState = JSON.parse(appended[2].data);
    assert.equal(queuedState.receiptId, result.receiptId);
    assert.equal(queuedState.state, 'queued');
    assert.equal(durableLead.receiptId, result.receiptId);
    assert.equal(durableLead._emailOutbox.provider, 'resend');
    assert.equal(deliveryState.receiptId, result.receiptId);
    assert.equal(deliveryState.state, 'sent');
    assert.notEqual(appended[0].file, appended[1].file);
    assert.equal(appended[0].file, appended[2].file);

    assert.equal(mailRequests.length, 1);
    const mail = JSON.parse(mailRequests[0].options.body);
    assert.equal(
      mailRequests[0].options.headers['idempotency-key'],
      `lead-email/${result.receiptId}`
    );
    assert.match(mail.subject, new RegExp(result.receiptId));
    assert.match(mail.text, new RegExp(`receiptId: ${result.receiptId}`));
    assert.match(mail.text, /PIPELINE-CHECK-TEST/);
    assert.ok(logs.some(line => line.includes(`LEAD_MAILED receiptId=${result.receiptId}`)));
    assert.deepEqual(errors, []);
  } finally {
    global.fetch = original.fetch;
    fs.mkdirSync = original.mkdirSync;
    fs.appendFileSync = original.appendFileSync;
    fs.readFileSync = original.readFileSync;
    console.log = original.log;
    console.error = original.error;
    restoreEnv();
    await new Promise((resolve, reject) => {
      server.close(err => err ? reject(err) : resolve());
    });
  }
});

test('admin delivery probe is fixed, synthetic, filtered and receipt-status only', async () => {
  const server = app.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const base = `http://127.0.0.1:${server.address().port}`;
  const restoreEnv = useDeliveryEnv({
    RENDER: 'true',
    RESEND_API_KEY: 'test-key',
    LEAD_TO_EMAIL: 'owner@example.com',
    LEAD_FROM_EMAIL: 'Leon Builds <leads@example.com>',
    LEADS_KEY: 'probe-admin-key'
  });
  const original = {
    fetch: global.fetch,
    mkdirSync: fs.mkdirSync,
    appendFileSync: fs.appendFileSync,
    readFileSync: fs.readFileSync,
    log: console.log,
    error: console.error
  };
  const files = new Map();
  const mailRequests = [];

  fs.mkdirSync = () => {};
  fs.appendFileSync = (file, data) => {
    const key = String(file);
    files.set(key, (files.get(key) || '') + data);
  };
  fs.readFileSync = (file, ...args) => {
    const key = String(file);
    if (files.has(key)) return files.get(key);
    if (key.endsWith('/leads.jsonl') || key.endsWith('/lead-email-outbox.jsonl')
        || key.endsWith('/lead-email-confirmations.jsonl')) {
      const error = new Error(`ENOENT: ${key}`);
      error.code = 'ENOENT';
      throw error;
    }
    return original.readFileSync(file, ...args);
  };
  console.log = () => {};
  console.error = () => {};
  global.fetch = async (url, options) => {
    if (String(url) === 'https://api.resend.com/emails') {
      mailRequests.push({ url: String(url), options });
      return { ok: true, json: async () => ({ id: 'resend-probe-message-id' }) };
    }
    return original.fetch(url, options);
  };

  try {
    const unauthorized = await global.fetch(base + '/api/lead-delivery-probe', {
      method: 'POST'
    });
    assert.equal(unauthorized.status, 401);

    const queryOnly = await global.fetch(base + '/api/lead-delivery-probe?key=probe-admin-key', {
      method: 'POST'
    });
    assert.equal(queryOnly.status, 401);

    const callerData = await global.fetch(base + '/api/lead-delivery-probe', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-leads-key': 'probe-admin-key'
      },
      body: JSON.stringify({
        email: 'private-person@example.net',
        problem: 'Caller text must never enter a probe.'
      })
    });
    assert.equal(callerData.status, 400);
    assert.equal(mailRequests.length, 0);

    const response = await global.fetch(base + '/api/lead-delivery-probe', {
      method: 'POST',
      headers: { 'x-leads-key': 'probe-admin-key' }
    });
    const result = await response.json();
    assert.equal(response.status, 202);
    assert.equal(response.headers.get('cache-control'), 'no-store');
    assert.equal(result.ok, true);
    assert.equal(result.synthetic, true);
    assert.match(result.receiptId, /^lead_[0-9a-f-]{36}$/);
    assert.match(result.tag, /^PIPELINE-CHECK-\d{8}T\d{6}Z-[A-F0-9]{8}$/);
    assert.equal(result.statusPath, `/api/lead-delivery-status/${result.receiptId}`);

    await new Promise(resolve => setImmediate(resolve));
    await drainLeadEmailOutbox();
    assert.equal(mailRequests.length, 1);

    const mail = JSON.parse(mailRequests[0].options.body);
    assert.equal(mail.reply_to, 'pipeline-check@example.com');
    assert.deepEqual(mail.to, ['owner@example.com']);
    assert.match(mail.subject, new RegExp(result.receiptId));
    assert.match(mail.text, new RegExp(result.tag));
    assert.match(mail.text, /synthetic: true/);
    assert.match(mail.text, /recordType: delivery_probe/);
    assert.doesNotMatch(mail.text, /private-person|Caller text/);

    assert.deepEqual(readLeads(10), []);
    const probes = readLeads(10, { includeSynthetic: true });
    assert.equal(probes.length, 1);
    assert.equal(probes[0].receiptId, result.receiptId);
    assert.equal(probes[0].synthetic, true);
    assert.equal(probes[0].recordType, 'delivery_probe');
    assert.equal(probes[0].email, 'pipeline-check@example.com');
    assert.equal(Object.hasOwn(probes[0], '_emailOutbox'), false);

    const defaultList = await global.fetch(base + '/api/leads?format=json', {
      headers: { 'x-leads-key': 'probe-admin-key' }
    });
    assert.equal(defaultList.status, 200);
    assert.equal((await defaultList.json()).count, 0);

    const includedList = await global.fetch(base + '/api/leads?format=json&includeSynthetic=1', {
      headers: { 'x-leads-key': 'probe-admin-key' }
    });
    const includedBody = await includedList.json();
    assert.equal(includedList.status, 200);
    assert.equal(includedBody.count, 1);
    assert.equal(includedBody.leads[0].receiptId, result.receiptId);

    const missingStatusAuth = await global.fetch(base + result.statusPath);
    assert.equal(missingStatusAuth.status, 401);
    const statusResponse = await global.fetch(base + result.statusPath, {
      headers: { 'x-leads-key': 'probe-admin-key' }
    });
    const status = await statusResponse.json();
    assert.equal(statusResponse.status, 200);
    assert.equal(statusResponse.headers.get('cache-control'), 'no-store');
    assert.deepEqual(Object.keys(status).sort(), [
      'at', 'attempts', 'provider', 'providerMessageId', 'receiptId', 'state'
    ]);
    assert.equal(status.receiptId, result.receiptId);
    assert.equal(status.state, 'sent');
    assert.equal(status.attempts, 1);
    assert.equal(status.provider, 'resend');
    assert.equal(status.providerMessageId, 'resend-probe-message-id');
    assert.doesNotMatch(JSON.stringify(status), /owner@example|pipeline-check@example|SYNTHETIC/);
    assert.deepEqual(leadEmailStatus(result.receiptId), status);

    const healthBefore = await global.fetch(base + '/api/health');
    const healthBeforeBody = await healthBefore.json();
    assert.equal(healthBefore.status, 200);
    assert.equal(healthBeforeBody.leadEmailVerified, false);
    assert.equal(Object.hasOwn(healthBeforeBody, 'leadEmailVerifiedAt'), false);

    const unauthorizedConfirmation = await global.fetch(
      base + `/api/lead-delivery-confirm/${result.receiptId}`,
      { method: 'POST' }
    );
    assert.equal(unauthorizedConfirmation.status, 401);

    const confirmationResponse = await global.fetch(
      base + `/api/lead-delivery-confirm/${result.receiptId}`,
      {
        method: 'POST',
        headers: { 'x-leads-key': 'probe-admin-key' }
      }
    );
    const confirmation = await confirmationResponse.json();
    assert.equal(confirmationResponse.status, 200);
    assert.equal(confirmation.ok, true);
    assert.equal(confirmation.verified, true);
    assert.equal(confirmation.receiptId, result.receiptId);
    assert.equal(confirmation.deduplicated, false);
    assert.match(confirmation.confirmedAt, /^\d{4}-\d{2}-\d{2}T/);

    const repeatedConfirmation = await global.fetch(
      base + `/api/lead-delivery-confirm/${result.receiptId}`,
      {
        method: 'POST',
        headers: { 'x-leads-key': 'probe-admin-key' }
      }
    );
    const repeatedConfirmationBody = await repeatedConfirmation.json();
    assert.equal(repeatedConfirmation.status, 200);
    assert.equal(repeatedConfirmationBody.deduplicated, true);
    assert.equal(repeatedConfirmationBody.confirmedAt, confirmation.confirmedAt);

    const verified = leadEmailVerification();
    assert.deepEqual(verified, {
      verified: true,
      confirmedAt: confirmation.confirmedAt
    });
    assert.deepEqual(leadEmailVerification({
      RENDER: 'true',
      RESEND_API_KEY: 'test-key',
      LEAD_TO_EMAIL: 'different-owner@example.com',
      LEAD_FROM_EMAIL: 'Leon Builds <leads@example.com>'
    }), { verified: false, confirmedAt: null });

    const healthAfter = await global.fetch(base + '/api/health');
    const healthAfterBody = await healthAfter.json();
    assert.equal(healthAfter.status, 200);
    assert.equal(healthAfterBody.leadEmailVerified, true);
    assert.equal(healthAfterBody.leadEmailState, 'verified');
    assert.equal(healthAfterBody.leadEmailVerifiedAt, confirmation.confirmedAt);
    assert.doesNotMatch(JSON.stringify(healthAfterBody), new RegExp(result.receiptId));

    const directConfirmation = confirmLeadEmailInbox(result.receiptId);
    assert.equal(directConfirmation.ok, true);
    assert.equal(directConfirmation.deduplicated, true);

    const repeated = await global.fetch(base + '/api/lead-delivery-probe', {
      method: 'POST',
      headers: { 'x-leads-key': 'probe-admin-key' }
    });
    assert.equal(repeated.status, 429);
    assert.equal(mailRequests.length, 1);
  } finally {
    global.fetch = original.fetch;
    fs.mkdirSync = original.mkdirSync;
    fs.appendFileSync = original.appendFileSync;
    fs.readFileSync = original.readFileSync;
    console.log = original.log;
    console.error = original.error;
    restoreEnv();
    await new Promise((resolve, reject) => {
      server.close(err => err ? reject(err) : resolve());
    });
  }
});

test('Resend failure retries from the durable outbox with one stable provider request', async () => {
  const restoreEnv = useDeliveryEnv({
    RENDER: 'true',
    RESEND_API_KEY: 'test-key',
    LEAD_TO_EMAIL: 'owner@example.com',
    LEAD_FROM_EMAIL: 'Leads <leads@example.com>'
  });
  const original = {
    fetch: global.fetch,
    mkdirSync: fs.mkdirSync,
    appendFileSync: fs.appendFileSync,
    readFileSync: fs.readFileSync,
    log: console.log,
    error: console.error
  };
  const files = new Map();
  const mailRequests = [];
  const errors = [];

  fs.mkdirSync = () => {};
  fs.appendFileSync = (file, data) => {
    const key = String(file);
    files.set(key, (files.get(key) || '') + data);
  };
  fs.readFileSync = (file, ...args) => {
    const key = String(file);
    if (files.has(key)) return files.get(key);
    if (key.endsWith('/leads.jsonl') || key.endsWith('/lead-email-outbox.jsonl')) {
      const error = new Error(`ENOENT: ${key}`);
      error.code = 'ENOENT';
      throw error;
    }
    return original.readFileSync(file, ...args);
  };
  console.log = () => {};
  console.error = (...args) => errors.push(args.join(' '));
  global.fetch = async (url, options) => {
    if (String(url) !== 'https://api.resend.com/emails') {
      return original.fetch(url, options);
    }
    mailRequests.push({ url: String(url), options });
    if (mailRequests.length === 1) {
      return {
        ok: false,
        status: 503,
        text: async () => 'temporary provider outage'
      };
    }
    return { ok: true, json: async () => ({ id: 'resend-retry-id' }) };
  };

  try {
    const lead = validateLead({
      email: 'outbox-retry@example.com',
      problem: 'Recover this notification after a provider outage.',
      via: 'quote-form',
      idempotencyKey: 'leadreq_22222222-3333-4444-8555-666666666666'
    }).lead;
    const persistence = persistLead(lead);

    // Join the fire-and-forget pass. Its follow-up scan proves the failed state
    // was durably visible and respects backoff rather than sending twice at once.
    await drainLeadEmailOutbox();

    assert.equal(persistence.stored, true);
    assert.equal(mailRequests.length, 1);
    const failed = readLeadEmailOutbox();
    assert.deepEqual(failed.map(state => state.state), ['queued', 'failed']);
    assert.equal(failed[1].receiptId, lead.receiptId);
    assert.equal(failed[1].attempts, 1);
    assert.ok(Date.parse(failed[1].nextAttemptAt) > Date.now());
    assert.match(errors.join('\n'), /durable retry queued/);

    // Let persistLead's deferred kick run. It sees the durable failure and does
    // not race the explicit retry while backoff is active.
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(mailRequests.length, 1);

    const visibleLead = readLeads(1)[0];
    assert.equal(visibleLead.receiptId, lead.receiptId);
    assert.equal(Object.hasOwn(visibleLead, '_emailOutbox'), false);

    // Force only bypasses the clock for this regression test. With no explicit
    // in-memory lead, the retry has to be reconstructed from the JSONL record.
    const virtualAppendFileSync = fs.appendFileSync;
    let failSentStateOnce = true;
    fs.appendFileSync = (file, data) => {
      if (failSentStateOnce && String(data).includes('"state":"sent"')) {
        failSentStateOnce = false;
        throw new Error('simulated sent-state write failure');
      }
      virtualAppendFileSync(file, data);
    };
    const retried = await drainLeadEmailOutbox({ force: true });
    assert.equal(retried.sent, 1);
    assert.equal(mailRequests.length, 2);
    assert.equal(mailRequests[0].options.body, mailRequests[1].options.body);
    assert.equal(
      mailRequests[0].options.headers['idempotency-key'],
      mailRequests[1].options.headers['idempotency-key']
    );
    assert.equal(
      mailRequests[1].options.headers['idempotency-key'],
      `lead-email/${lead.receiptId}`
    );

    // Provider success remains terminal in memory even if its first ledger
    // append fails. The next scan persists that state before considering mail.
    assert.deepEqual(
      readLeadEmailOutbox().map(state => state.state),
      ['queued', 'failed']
    );
    fs.appendFileSync = virtualAppendFileSync;
    const afterSent = await drainLeadEmailOutbox({ force: true });
    assert.equal(afterSent.attempted, 0);
    assert.equal(mailRequests.length, 2);

    const states = readLeadEmailOutbox();
    assert.deepEqual(states.map(state => state.state), ['queued', 'failed', 'sent']);
    assert.equal(states[2].attempts, 2);
    assert.equal(states[2].providerMessageId, 'resend-retry-id');

    const outboxPath = [...files].find(([, raw]) => raw.includes('"state":"sent"'))[0];
    const virtualReadFileSync = fs.readFileSync;
    fs.readFileSync = file => {
      if (String(file) === outboxPath) {
        const error = new Error('simulated unreadable sent ledger');
        error.code = 'EACCES';
        throw error;
      }
      return virtualReadFileSync(file);
    };
    await assert.rejects(
      drainLeadEmailOutbox({ force: true }),
      /simulated unreadable sent ledger/
    );
    assert.equal(mailRequests.length, 2);
    fs.readFileSync = virtualReadFileSync;

    const intactLedger = files.get(outboxPath);
    files.set(outboxPath, intactLedger + '{not-json\n');
    await assert.rejects(
      drainLeadEmailOutbox({ force: true }),
      /corrupt JSONL ledger/
    );
    assert.equal(mailRequests.length, 2);

    files.delete(outboxPath);
    await assert.rejects(
      drainLeadEmailOutbox({ force: true }),
      /required JSONL ledger is missing/
    );
    assert.equal(mailRequests.length, 2);
    files.set(outboxPath, intactLedger);
  } finally {
    global.fetch = original.fetch;
    fs.mkdirSync = original.mkdirSync;
    fs.appendFileSync = original.appendFileSync;
    fs.readFileSync = original.readFileSync;
    console.log = original.log;
    console.error = original.error;
    restoreEnv();
  }
});

test('lead acknowledgement does not wait for the queued Resend request', async () => {
  const server = app.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const base = `http://127.0.0.1:${server.address().port}`;
  const restoreEnv = useDeliveryEnv({
    RENDER: 'true',
    RESEND_API_KEY: 'test-key',
    LEAD_TO_EMAIL: 'owner@example.com'
  });
  const original = {
    fetch: global.fetch,
    mkdirSync: fs.mkdirSync,
    appendFileSync: fs.appendFileSync,
    readFileSync: fs.readFileSync,
    log: console.log,
    error: console.error
  };
  const files = new Map();
  let releaseMail;
  let timeout;

  fs.mkdirSync = () => {};
  fs.appendFileSync = (file, data) => {
    const key = String(file);
    files.set(key, (files.get(key) || '') + data);
  };
  fs.readFileSync = (file, ...args) => {
    const key = String(file);
    if (files.has(key)) return files.get(key);
    if (key.endsWith('/leads.jsonl') || key.endsWith('/lead-email-outbox.jsonl')) {
      const error = new Error(`ENOENT: ${key}`);
      error.code = 'ENOENT';
      throw error;
    }
    return original.readFileSync(file, ...args);
  };
  console.log = () => {};
  console.error = () => {};
  global.fetch = async (url, options) => {
    if (String(url) === 'https://api.resend.com/emails') {
      return new Promise(resolve => {
        releaseMail = () => resolve({ ok: true, json: async () => ({ id: 'delayed-mail-id' }) });
      });
    }
    return original.fetch(url, options);
  };

  try {
    const response = await Promise.race([
      global.fetch(base + '/api/lead', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          email: 'immediate-ack@example.com',
          problem: 'Acknowledge durable intake while mail is still pending.',
          idempotencyKey: 'leadreq_77777777-8888-4999-8aaa-bbbbbbbbbbbb'
        })
      }),
      new Promise((resolve, reject) => {
        timeout = setTimeout(() => reject(new Error('lead response waited for Resend')), 250);
      })
    ]);
    clearTimeout(timeout);
    const body = await response.json();

    assert.equal(response.status, 200);
    assert.equal(body.ok, true);
    assert.deepEqual(readLeadEmailOutbox().map(state => state.state), ['queued']);

    // The provider kick is deferred until after the handler can return.
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(typeof releaseMail, 'function');

    releaseMail();
    await drainLeadEmailOutbox();
    assert.equal(readLeadEmailOutbox().at(-1).state, 'sent');
  } finally {
    clearTimeout(timeout);
    if (releaseMail) releaseMail();
    await drainLeadEmailOutbox().catch(() => {});
    global.fetch = original.fetch;
    fs.mkdirSync = original.mkdirSync;
    fs.appendFileSync = original.appendFileSync;
    fs.readFileSync = original.readFileSync;
    console.log = original.log;
    console.error = original.error;
    restoreEnv();
    await new Promise((resolve, reject) => {
      server.close(error => error ? reject(error) : resolve());
    });
  }
});

test('lead intake returns retryable 503 and does not email when JSONL persistence fails', async () => {
  const server = app.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const base = `http://127.0.0.1:${server.address().port}`;
  const restoreEnv = useDeliveryEnv({
    RENDER: 'true',
    RESEND_API_KEY: 'test-key',
    LEAD_TO_EMAIL: 'owner@example.com'
  });
  const original = {
    fetch: global.fetch,
    mkdirSync: fs.mkdirSync,
    appendFileSync: fs.appendFileSync,
    log: console.log,
    error: console.error
  };
  let mailRequests = 0;
  const errors = [];

  fs.mkdirSync = () => {};
  fs.appendFileSync = () => { throw new Error('simulated disk failure'); };
  console.log = () => {};
  console.error = (...args) => errors.push(args.join(' '));
  global.fetch = async (url, options) => {
    if (String(url) === 'https://api.resend.com/emails') {
      mailRequests += 1;
      return { ok: true, json: async () => ({ id: 'should-not-send' }) };
    }
    return original.fetch(url, options);
  };

  try {
    const response = await global.fetch(base + '/api/lead', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        email: 'retryable@example.com',
        problem: 'Save this lead only when durable storage works.',
        idempotencyKey: 'leadreq_ffffffff-eeee-4ddd-8ccc-bbbbbbbbbbbb'
      })
    });
    const result = await response.json();

    assert.equal(response.status, 503);
    assert.equal(response.headers.get('retry-after'), '2');
    assert.match(result.error, /could not save/i);
    assert.equal(mailRequests, 0);
    assert.ok(errors.some(line => line.includes('lead email outbox write failed:')));
  } finally {
    global.fetch = original.fetch;
    fs.mkdirSync = original.mkdirSync;
    fs.appendFileSync = original.appendFileSync;
    console.log = original.log;
    console.error = original.error;
    restoreEnv();
    await new Promise((resolve, reject) => {
      server.close(err => err ? reject(err) : resolve());
    });
  }
});

test('lead idempotency recovers the accepted receipt from durable JSONL after a restart', async () => {
  const requestBody = {
    name: 'Durable retry',
    email: 'durable-retry@example.com',
    problem: 'Recover the first accepted receipt after a process restart.',
    via: 'quote-form',
    idempotencyKey: 'leadreq_11111111-2222-4333-8444-555555555555'
  };
  const storedLead = validateLead(requestBody).lead;
  storedLead.ts = '2026-08-24T00:00:00.000Z';
  storedLead.receiptId = 'lead_11111111-1111-4111-8111-111111111111';

  const server = app.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const base = `http://127.0.0.1:${server.address().port}`;
  const original = {
    fetch: global.fetch,
    readFileSync: fs.readFileSync,
    appendFileSync: fs.appendFileSync
  };
  let writes = 0;
  let mailRequests = 0;

  fs.readFileSync = () => JSON.stringify(storedLead) + '\n';
  fs.appendFileSync = () => { writes += 1; };
  global.fetch = async (url, options) => {
    if (String(url) === 'https://api.resend.com/emails') {
      mailRequests += 1;
      return { ok: true, json: async () => ({ id: 'should-not-send' }) };
    }
    return original.fetch(url, options);
  };

  try {
    const response = await global.fetch(base + '/api/lead', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(requestBody)
    });
    const result = await response.json();

    assert.equal(response.status, 200);
    assert.deepEqual(result, {
      ok: true,
      receiptId: storedLead.receiptId,
      deduplicated: true
    });
    assert.equal(writes, 0);
    assert.equal(mailRequests, 0);
  } finally {
    global.fetch = original.fetch;
    fs.readFileSync = original.readFileSync;
    fs.appendFileSync = original.appendFileSync;
    await new Promise((resolve, reject) => {
      server.close(err => err ? reject(err) : resolve());
    });
  }
});

test('health keeps service liveness separate from delivery readiness', async t => {
  const server = app.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const originalReadFileSync = fs.readFileSync;
  fs.readFileSync = (file, ...args) => {
    if (String(file).endsWith('/lead-email-confirmations.jsonl')) {
      const error = new Error(`ENOENT: ${file}`);
      error.code = 'ENOENT';
      throw error;
    }
    return originalReadFileSync(file, ...args);
  };
  t.after(() => new Promise((resolve, reject) => {
    fs.readFileSync = originalReadFileSync;
    server.close(err => err ? reject(err) : resolve());
  }));
  const base = `http://127.0.0.1:${server.address().port}`;

  let restore = useDeliveryEnv({
    RENDER: 'true',
    LEAD_TO_EMAIL: 'leon@example.com',
    SMTP_HOST: 'smtp.example.com',
    SMTP_USER: 'user',
    SMTP_PASS: 'pass'
  });
  try {
    const shallow = await fetch(base + '/api/health');
    assert.equal(shallow.status, 200);
    assert.equal((await shallow.json()).ok, true);

    const disabled = await fetch(base + '/api/health?deep=1');
    assert.equal(disabled.status, 404);
    assert.equal((await disabled.json()).error, 'deep health is not enabled');
  } finally {
    restore();
  }

  restore = useDeliveryEnv({
    RENDER: 'true',
    LEAD_TO_EMAIL: 'leon@example.com',
    SMTP_HOST: 'smtp.example.com',
    SMTP_USER: 'user',
    SMTP_PASS: 'pass',
    LEADS_KEY: 'admin-test-key'
  });
  try {
    const missing = await fetch(base + '/api/health?deep=1');
    assert.equal(missing.status, 401);

    const queryOnly = await fetch(base + '/api/health?deep=1&key=admin-test-key');
    assert.equal(queryOnly.status, 401);

    const wrong = await fetch(base + '/api/health?deep=1', {
      headers: { 'x-leads-key': 'wrong-key' }
    });
    assert.equal(wrong.status, 401);

    const response = await fetch(base + '/api/health?deep=1', {
      headers: { 'x-leads-key': 'admin-test-key' }
    });
    const body = await response.json();
    assert.equal(response.status, 200);
    assert.equal(response.headers.get('cache-control'), 'no-store');
    assert.equal(body.ok, true);
    assert.equal(body.leadEmailProvider, 'smtp');
    assert.equal(body.leadEmailConfigured, true);
    assert.equal(body.leadEmailSupported, false);
    assert.equal(body.leadEmailReady, false);
    assert.equal(body.leadEmail, false);
    assert.equal(body.leadEmailState, 'blocked');
    assert.equal(body.leadEmailWorks, false);
    assert.equal(body.leadEmailCheckLevel, 'platform');
    assert.equal(body.leadEmailTo, 'l***@example.com');
  } finally {
    restore();
  }

  restore = useDeliveryEnv({
    RENDER: 'true',
    RESEND_API_KEY: 'test-key',
    LEAD_TO_EMAIL: 'leon@example.com',
    LEADS_KEY: 'admin-test-key'
  });
  try {
    const response = await fetch(base + '/api/health?deep=true', {
      headers: { 'x-leads-key': 'admin-test-key' }
    });
    const body = await response.json();
    assert.equal(body.ok, true);
    assert.equal(body.leadEmailProvider, 'resend');
    assert.equal(body.leadEmailTransport, 'https');
    assert.equal(body.leadEmailReady, true);
    assert.equal(body.leadEmailState, 'configured_unverified');
    assert.equal(body.leadEmailWorks, null);
    assert.equal(body.leadEmailCheckPassed, null);
    assert.equal(body.leadEmailCheckLevel, 'configuration');
    assert.match(body.leadEmailCheck, /not verified/i);

    const shallow = await (await fetch(base + '/api/health?deep=0')).json();
    assert.equal(Object.hasOwn(shallow, 'leadEmailCheckPassed'), false);
  } finally {
    restore();
  }
});
