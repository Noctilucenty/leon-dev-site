/* Lead intake: validate, sanitize, persist, notify.
   Copies, in order:
   1. stdout      — always, but only as durable as the host's log retention.
   2. jsonl file  — required before acknowledgement. data/leads.jsonl by default.
   3. email       — Resend over HTTPS, or SMTP on hosts where SMTP egress works.

   Resend notifications are a durable outbox: the immutable payload is embedded
   in the accepted lead record, while append-only delivery state lives beside it.
   That lets a restart recover a send that failed after the visitor got a 200. */

'use strict';

const fs = require('fs');
const path = require('path');
const { createHash, randomUUID } = require('crypto');
const { normalizeAttribution } = require('./attribution');
const { dataFile } = require('./storage');

const LEADS_FILE = dataFile('leads.jsonl', 'LEADS_FILE');
const DATA_DIR = path.dirname(LEADS_FILE);
const LEAD_EMAIL_OUTBOX_FILE = dataFile(
  'lead-email-outbox.jsonl',
  'LEAD_EMAIL_OUTBOX_FILE'
);
const LEAD_EMAIL_CONFIRMATIONS_FILE = dataFile(
  'lead-email-confirmations.jsonl',
  'LEAD_EMAIL_CONFIRMATIONS_FILE'
);
const EMAIL_OUTBOX_VERSION = 1;
const EMAIL_CONFIRMATION_VERSION = 1;
const EMAIL_OUTBOX_RETRY_BASE_MS = 60_000;
const EMAIL_OUTBOX_RETRY_MAX_MS = 60 * 60_000;
const EMAIL_OUTBOX_SCAN_MS = 60_000;
const RECEIPT_ID_RE = /^lead_[0-9a-f-]{36}$/i;

/* Single-line by default: every control character goes, including the CR/LF that
   would otherwise ride into an SMTP header. Pass multiline for the long free-text
   fields, where newlines are the whole point — those never reach a header. */
const clean = (v, max, multiline) => {
  if (typeof v !== 'string') return '';
  const stripped = multiline
    ? v.replace(/\r\n?/g, '\n').replace(/[\u0000-\u0009\u000B-\u001F\u007F]/g, ' ')
    : v.replace(/[\u0000-\u001F\u007F]/g, ' ').replace(/[^\S\n]+/g, ' ');
  return stripped.trim().slice(0, max);
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const IDEMPOTENCY_KEY_RE = /^leadreq_[A-Za-z0-9-]{16,80}$/;
const SLUG_RE = /^[a-z0-9][a-z0-9-]{0,63}$/;
const TECHNICAL_PARTNER_PACKAGES = new Set([
  'systems-plan', 'focused-build-sprint', 'ongoing-technical-partner'
]);
const newReceiptId = () => 'lead_' + randomUUID();

const present = v => typeof v === 'string' ? !!v.trim() : !!v;

function isRenderRuntime(env) {
  return /^(1|true|yes)$/i.test(String(env.RENDER || '')) || present(env.RENDER_SERVICE_ID);
}

function maskEmail(value) {
  const email = String(value || '').trim();
  const at = email.lastIndexOf('@');
  if (at <= 0 || at === email.length - 1) return email ? '***' : null;
  return email.slice(0, 1) + '***' + email.slice(at);
}

/* One source of truth for sending AND health reporting. Previously these paths
 * disagreed: sending preferred Resend, while /api/health ignored Resend and
 * marked SMTP green on Render even though this service has measured SMTP egress
 * failures there. `ready` means "fully configured on a supported transport";
 * it deliberately does not mean "a message reached the inbox". */
function leadDeliveryConfig(env = process.env) {
  const onRender = isRenderRuntime(env);
  const resendMissing = ['RESEND_API_KEY', 'LEAD_TO_EMAIL'].filter(k => !present(env[k]));
  // SMTP_PORT is optional: portsToTry() has a real default of 587.
  const smtpMissing = ['SMTP_HOST', 'SMTP_USER', 'SMTP_PASS', 'LEAD_TO_EMAIL']
    .filter(k => !present(env[k]));
  const resendConfigured = resendMissing.length === 0;
  const smtpConfigured = smtpMissing.length === 0;
  const anySmtp = ['SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASS']
    .some(k => present(env[k]));

  // Match persistLead's precedence exactly. A configured Resend key always wins
  // because HTTPS is the supported production path on Render.
  const provider = present(env.RESEND_API_KEY) ? 'resend' : (anySmtp ? 'smtp' : null);
  const configured = provider === 'resend' ? resendConfigured
    : provider === 'smtp' ? smtpConfigured
    : false;
  const supported = provider === 'smtp' ? !onRender : provider === 'resend';
  const ready = configured && supported;
  const missing = provider === 'resend' ? resendMissing
    : provider === 'smtp' && onRender ? resendMissing
    : provider === 'smtp' ? smtpMissing
    : onRender ? resendMissing
    : [
        ...(!present(env.LEAD_TO_EMAIL) ? ['LEAD_TO_EMAIL'] : []),
        'RESEND_API_KEY or SMTP_HOST + SMTP_USER + SMTP_PASS'
      ];

  let state = 'not_configured';
  let warning = null;
  if (provider && !configured) state = 'incomplete';
  if (configured) state = 'configured_unverified';
  if (provider === 'smtp' && !supported) {
    state = 'blocked';
    warning = 'SMTP is selected, but outbound SMTP is unavailable on this Render service; configure RESEND_API_KEY to use HTTPS.';
  }

  return {
    provider,
    transport: provider === 'resend' ? 'https' : provider,
    configured,
    supported,
    ready,
    state,
    missing,
    warning,
    onRender,
    recipient: maskEmail(env.LEAD_TO_EMAIL),
    providers: {
      resend: { configured: resendConfigured, transport: 'https', missing: resendMissing },
      smtp: {
        configured: smtpConfigured,
        transport: 'smtp',
        supported: !onRender,
        missing: smtpMissing
      }
    }
  };
}

function validateLead(body) {
  // Bots fill the hidden `website` field. Checked before anything else so the
  // response cannot be used to tell which check rejected them. Give the fake
  // success the same receipt shape as a real submission, but do not persist it.
  if (body.website) return { bot: true, receiptId: newReceiptId() };
  const rawIdempotencyKey = body.idempotencyKey;
  const idempotencyKey = typeof rawIdempotencyKey === 'string'
    ? rawIdempotencyKey.trim()
    : '';
  if (rawIdempotencyKey != null && rawIdempotencyKey !== ''
      && !IDEMPOTENCY_KEY_RE.test(idempotencyKey)) {
    return { error: 'invalid idempotency key' };
  }
  const currentAttribution = normalizeAttribution(body);
  const firstAttribution = normalizeAttribution(body, 'first');
  const lastAttribution = normalizeAttribution(body, 'last');
  const service = clean(body.service, 64);
  const packageName = clean(body.package, 64);
  if (service && !SLUG_RE.test(service)) return { error: 'invalid service' };
  if (packageName && (
      service !== 'technical-build-partner'
      || !TECHNICAL_PARTNER_PACKAGES.has(packageName)
  )) return { error: 'invalid package' };
  const lead = {
    ts: new Date().toISOString(),
    receiptId: newReceiptId(),
    name: clean(body.name, 120),
    email: clean(body.email, 200).toLowerCase(),
    phone: clean(body.phone, 40),
    company: clean(body.company, 160),
    industry: clean(body.industry, 120),
    service,
    package: packageName,
    problem: clean(body.problem, 4000, true),
    currentTools: clean(body.currentTools, 500),
    desiredOutcome: clean(body.desiredOutcome, 1000, true),
    timeline: clean(body.timeline, 120),
    budget: clean(body.budget, 60),
    sourcePage: clean(body.sourcePage, 300),
    referrer: clean(body.referrer, 300),
    utmSource: currentAttribution.utmSource || '',
    utmMedium: currentAttribution.utmMedium || '',
    utmCampaign: currentAttribution.utmCampaign || '',
    utmTerm: currentAttribution.utmTerm || '',
    utmContent: currentAttribution.utmContent || '',
    gclid: currentAttribution.gclid || '',
    gbraid: currentAttribution.gbraid || '',
    wbraid: currentAttribution.wbraid || '',
    fbclid: currentAttribution.fbclid || '',
    msclkid: currentAttribution.msclkid || '',
    firstPage: clean(body.firstPage, 300),
    firstReferrer: clean(body.firstReferrer, 300),
    firstUtmSource: firstAttribution.utmSource || '',
    firstUtmMedium: firstAttribution.utmMedium || '',
    firstUtmCampaign: firstAttribution.utmCampaign || '',
    firstUtmTerm: firstAttribution.utmTerm || '',
    firstUtmContent: firstAttribution.utmContent || '',
    firstGclid: firstAttribution.gclid || '',
    firstGbraid: firstAttribution.gbraid || '',
    firstWbraid: firstAttribution.wbraid || '',
    firstFbclid: firstAttribution.fbclid || '',
    firstMsclkid: firstAttribution.msclkid || '',
    lastPage: clean(body.lastPage, 300) || clean(body.sourcePage, 300),
    lastReferrer: clean(body.lastReferrer, 300) || clean(body.referrer, 300),
    lastUtmSource: lastAttribution.utmSource || currentAttribution.utmSource || '',
    lastUtmMedium: lastAttribution.utmMedium || currentAttribution.utmMedium || '',
    lastUtmCampaign: lastAttribution.utmCampaign || currentAttribution.utmCampaign || '',
    lastUtmTerm: lastAttribution.utmTerm || currentAttribution.utmTerm || '',
    lastUtmContent: lastAttribution.utmContent || currentAttribution.utmContent || '',
    lastGclid: lastAttribution.gclid || currentAttribution.gclid || '',
    lastGbraid: lastAttribution.gbraid || currentAttribution.gbraid || '',
    lastWbraid: lastAttribution.wbraid || currentAttribution.wbraid || '',
    lastFbclid: lastAttribution.fbclid || currentAttribution.fbclid || '',
    lastMsclkid: lastAttribution.msclkid || currentAttribution.msclkid || '',
    analyticsSessionId: clean(body.analyticsSessionId, 96),
    chatSessionId: clean(body.chatSessionId, 96),
    idempotencyKey,
    via: clean(body.via, 30) || 'site',           // 'chat' | 'quote-form' | 'site'
    conversationSummary: clean(body.conversationSummary, 8000, true)
  };
  if (!lead.email || !EMAIL_RE.test(lead.email)) return { error: 'a valid email is required' };
  if (!lead.problem && !lead.conversationSummary) return { error: 'tell me at least a sentence about the project' };
  return { lead };
}

/* A retry receives a new timestamp and candidate receipt before it reaches the
   route, so neither belongs in the equality check. Empty fields are also
   omitted: adding a new optional field to the schema must not make an old,
   otherwise identical durable record look like a different submission. */
function leadFingerprint(lead) {
  const canonical = {};
  for (const key of Object.keys(lead || {}).sort()) {
    if (key === 'ts' || key === 'receiptId' || key === 'idempotencyKey'
        || key === '_emailOutbox') continue;
    const value = lead[key];
    if (value === '' || value == null) continue;
    canonical[key] = value;
  }
  return createHash('sha256').update(JSON.stringify(canonical)).digest('hex');
}

function leadEmailSubject(lead) {
  return `New website lead [${lead.receiptId}] — ${lead.service || lead.industry || lead.company || 'unknown'} — ${lead.via}`;
}

function leadEmailText(lead) {
  return Object.entries(lead)
    .filter(([key, value]) => key !== '_emailOutbox' && value)
    .map(([key, value]) => `${key}: ${value}`)
    .join('\n');
}

/* Store the exact Resend payload that was accepted with the lead. Rebuilding it
 * from mutable environment settings on every retry can turn a valid idempotent
 * retry into Resend's 409 "same key, different request" response. No API key is
 * stored here. The marker is removed from admin-facing lead reads below. */
function createResendOutbox(lead, env = process.env) {
  return {
    version: EMAIL_OUTBOX_VERSION,
    provider: 'resend',
    queuedAt: new Date().toISOString(),
    idempotencyKey: `lead-email/${lead.receiptId}`,
    payload: {
      from: env.LEAD_FROM_EMAIL || 'Leon Builds <onboarding@resend.dev>',
      to: [String(env.LEAD_TO_EMAIL || '').trim()],
      reply_to: lead.email,
      subject: leadEmailSubject(lead),
      text: leadEmailText(lead)
    }
  };
}

/* A confirmation is valid only for the exact provider/from/to configuration
 * exercised by the probe. If the destination or sender changes later, health
 * automatically returns to unverified until the new path reaches the inbox. */
function leadDeliveryFingerprint(env = process.env) {
  const provider = String(leadDeliveryConfig(env).provider || '');
  const from = String(env.LEAD_FROM_EMAIL || 'Leon Builds <onboarding@resend.dev>').trim();
  const to = String(env.LEAD_TO_EMAIL || '').trim().toLowerCase();
  return createHash('sha256')
    .update(JSON.stringify({ provider, from, to }))
    .digest('hex');
}

function outboxDeliveryFingerprint(outbox) {
  const payload = outbox && outbox.payload;
  if (!payload || !Array.isArray(payload.to) || !payload.to[0]) return null;
  return createHash('sha256')
    .update(JSON.stringify({
      provider: String(outbox.provider || ''),
      from: String(payload.from || '').trim(),
      to: String(payload.to[0] || '').trim().toLowerCase()
    }))
    .digest('hex');
}

function publicLead(lead) {
  if (!lead || typeof lead !== 'object') return lead;
  const { _emailOutbox, ...visible } = lead;
  return visible;
}

function readJsonl(file, { strict = false, missingOkay = true } = {}) {
  let raw = '';
  try {
    raw = fs.readFileSync(file, 'utf8');
  } catch (error) {
    if (strict && (!error || error.code !== 'ENOENT' || !missingOkay)) {
      if (error && error.code === 'ENOENT') {
        throw new Error(`required JSONL ledger is missing: ${path.basename(file)}`);
      }
      throw error;
    }
    return [];
  }
  const out = [];
  const lines = raw.split('\n');
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (!line.trim()) continue;
    try {
      out.push(JSON.parse(line));
    } catch (error) {
      if (strict) {
        throw new Error(
          `corrupt JSONL ledger: ${path.basename(file)} line ${index + 1}`);
      }
      // Admin reads retain their historical best-effort behavior.
    }
  }
  return out;
}

function readStoredLeads({ strict = false } = {}) {
  return readJsonl(LEADS_FILE, { strict });
}

function readLeadEmailOutbox({ required = false } = {}) {
  // A missing file means nothing has been attempted yet. Any other read error
  // must stop a drain: treating an unreadable sent ledger as empty would resend
  // every queued notification and defeat local deduplication.
  const events = readJsonl(LEAD_EMAIL_OUTBOX_FILE, {
    strict: true,
    missingOkay: !required
  });
  if (required && events.length === 0) {
    throw new Error(`required JSONL ledger is empty: ${path.basename(LEAD_EMAIL_OUTBOX_FILE)}`);
  }
  for (let index = 0; index < events.length; index += 1) {
    const event = events[index];
    if (!event || event.version !== EMAIL_OUTBOX_VERSION
        || !RECEIPT_ID_RE.test(String(event.receiptId || ''))
        || !['queued', 'failed', 'sent'].includes(event.state)) {
      throw new Error(
        `invalid lead email outbox event: ${path.basename(LEAD_EMAIL_OUTBOX_FILE)} record ${index + 1}`);
    }
  }
  return events;
}

function readLeadEmailConfirmations() {
  const events = readJsonl(LEAD_EMAIL_CONFIRMATIONS_FILE, {
    strict: true,
    missingOkay: true
  });
  for (let index = 0; index < events.length; index += 1) {
    const event = events[index];
    if (!event || event.version !== EMAIL_CONFIRMATION_VERSION
        || !RECEIPT_ID_RE.test(String(event.receiptId || ''))
        || event.state !== 'inbox_confirmed'
        || !/^\d{4}-\d{2}-\d{2}T/.test(String(event.at || ''))
        || !/^[0-9a-f]{64}$/.test(String(event.configFingerprint || ''))) {
      throw new Error(
        `invalid lead email confirmation event: ${path.basename(LEAD_EMAIL_CONFIRMATIONS_FILE)} record ${index + 1}`);
    }
  }
  return events;
}

const volatileOutboxStates = new Map();

function appendOutboxState(event) {
  try {
    fs.mkdirSync(path.dirname(LEAD_EMAIL_OUTBOX_FILE), { recursive: true });
    fs.appendFileSync(LEAD_EMAIL_OUTBOX_FILE, JSON.stringify(event) + '\n');
    return true;
  } catch (error) {
    console.error(
      `lead email outbox write failed: ${event.receiptId}`,
      String(error && error.message || error).slice(0, 300));
    return false;
  }
}

function recordOutboxState(event) {
  if (appendOutboxState(event)) volatileOutboxStates.delete(event.receiptId);
  else volatileOutboxStates.set(event.receiptId, event);
}

function outboxStateByReceipt({ required = false } = {}) {
  const states = new Map();
  for (const event of readLeadEmailOutbox({ required })) states.set(event.receiptId, event);
  for (const [receiptId, event] of volatileOutboxStates) states.set(receiptId, event);
  return states;
}

function retryDelayMs(attempts) {
  const exponent = Math.max(0, Math.min(Number(attempts || 1) - 1, 10));
  return Math.min(EMAIL_OUTBOX_RETRY_BASE_MS * (2 ** exponent), EMAIL_OUTBOX_RETRY_MAX_MS);
}

function validResendOutbox(lead) {
  const outbox = lead && lead._emailOutbox;
  const payload = outbox && outbox.payload;
  if (!outbox || outbox.version !== EMAIL_OUTBOX_VERSION || outbox.provider !== 'resend') return null;
  if (!/^lead-email\/lead_[0-9a-f-]{36}$/i.test(String(outbox.idempotencyKey || ''))) return null;
  if (!payload || typeof payload !== 'object'
      || typeof payload.from !== 'string'
      || !Array.isArray(payload.to) || !payload.to[0]
      || typeof payload.subject !== 'string'
      || typeof payload.text !== 'string') return null;
  return outbox;
}

async function drainLeadEmailOutboxPass({ force = false, leads, now = Date.now() } = {}) {
  const queued = new Map();
  for (const lead of leads || readStoredLeads({ strict: true })) {
    if (lead && lead.receiptId && validResendOutbox(lead)) queued.set(lead.receiptId, lead);
  }
  /* Every accepted outbox lead first writes a queued ledger event. If that
   * ledger later disappears, fail closed instead of treating every historical
   * notification as unsent. */
  const states = outboxStateByReceipt({ required: queued.size > 0 });
  for (const receiptId of queued.keys()) {
    if (!states.has(receiptId)) {
      throw new Error(`lead email outbox is missing queue state for ${receiptId}`);
    }
  }

  /* If a previous provider success could not be recorded, persist that state
   * only after proving the existing ledger is readable. Recreating a lost file
   * from one volatile event could hide the loss of every older sent record. */
  for (const [receiptId, event] of volatileOutboxStates) {
    if (appendOutboxState(event)) volatileOutboxStates.delete(receiptId);
  }

  const result = { queued: queued.size, attempted: 0, sent: 0, failed: 0, skipped: 0 };
  for (const [receiptId, lead] of queued) {
    const prior = states.get(receiptId);
    if (prior && prior.state === 'sent') {
      result.skipped += 1;
      continue;
    }
    if (!force && prior && prior.state === 'failed'
        && Date.parse(prior.nextAttemptAt || '') > now) {
      result.skipped += 1;
      continue;
    }

    const attempts = Math.max(0, Number(prior && prior.attempts) || 0) + 1;
    result.attempted += 1;
    try {
      const providerResult = await sendViaHttp(lead._emailOutbox);
      const event = {
        version: EMAIL_OUTBOX_VERSION,
        receiptId,
        state: 'sent',
        at: new Date(now).toISOString(),
        attempts,
        provider: 'resend',
        providerMessageId: clean(String(providerResult && providerResult.id || ''), 200)
      };
      recordOutboxState(event);
      result.sent += 1;
      console.log(
        `LEAD_MAILED receiptId=${receiptId} to ${lead._emailOutbox.payload.to[0]} via https (resend)`);
    } catch (error) {
      const message = String(error && error.message || error).slice(0, 500);
      const nextAttemptAt = new Date(now + retryDelayMs(attempts)).toISOString();
      recordOutboxState({
        version: EMAIL_OUTBOX_VERSION,
        receiptId,
        state: 'failed',
        at: new Date(now).toISOString(),
        attempts,
        nextAttemptAt,
        provider: 'resend',
        error: message
      });
      result.failed += 1;
      console.error(
        `LEAD_MAIL_FAILED receiptId=${receiptId}`, message,
        `— durable retry queued for ${nextAttemptAt}`);
    }
  }
  return result;
}

let outboxDrainPromise = null;
let outboxDrainRequested = false;

/* Only one pass sends at a time in this process. A concurrent request asks for a
 * follow-up disk scan, so a lead appended during the active pass is not stranded.
 * Resend's stable Idempotency-Key also dedupes overlapping processes. */
function drainLeadEmailOutbox(options = {}) {
  if (outboxDrainPromise) {
    outboxDrainRequested = true;
    return outboxDrainPromise;
  }
  outboxDrainPromise = (async () => {
    let nextOptions = options;
    let aggregate = { queued: 0, attempted: 0, sent: 0, failed: 0, skipped: 0 };
    try {
      do {
        outboxDrainRequested = false;
        const pass = await drainLeadEmailOutboxPass(nextOptions);
        aggregate = Object.fromEntries(Object.keys(aggregate).map(key => [key, aggregate[key] + pass[key]]));
        // A follow-up pass reads the durable lead file; explicit in-memory leads
        // are only needed by the request that just appended them.
        nextOptions = { force: !!options.force, now: options.now };
      } while (outboxDrainRequested);
      return aggregate;
    } finally {
      outboxDrainPromise = null;
    }
  })();
  return outboxDrainPromise;
}

let outboxTimer = null;

function scheduleLeadEmailOutbox(lead) {
  // Do not parse the append-only ledger on the request stack. The accepted lead
  // and queued event are already durable; the response can leave immediately.
  setImmediate(() => {
    drainLeadEmailOutbox({ leads: [lead] }).catch(error => {
      console.error('lead email outbox trigger failed:', String(error && error.message || error).slice(0, 300));
    });
  });
}

function startLeadEmailOutbox() {
  if (outboxTimer) return;
  drainLeadEmailOutbox().catch(error => {
    console.error('lead email outbox startup failed:', String(error && error.message || error).slice(0, 300));
  });
  outboxTimer = setInterval(() => {
    drainLeadEmailOutbox().catch(error => {
      console.error('lead email outbox scan failed:', String(error && error.message || error).slice(0, 300));
    });
  }, EMAIL_OUTBOX_SCAN_MS);
  outboxTimer.unref();
}

function persistLead(lead) {
  const delivery = leadDeliveryConfig();
  const storedLead = delivery.ready && delivery.provider === 'resend'
    ? { ...lead, _emailOutbox: createResendOutbox(lead) }
    : lead;
  // 1. stdout — the sink that always works
  console.log('LEAD ' + JSON.stringify(lead));
  // A queued event is written before the lead. An orphan event is harmless if
  // the subsequent lead write fails, while the inverse ordering could leave an
  // acknowledged lead whose retry ledger never existed.
  if (storedLead._emailOutbox && !appendOutboxState({
    version: EMAIL_OUTBOX_VERSION,
    receiptId: lead.receiptId,
    state: 'queued',
    at: storedLead._emailOutbox.queuedAt,
    attempts: 0,
    provider: 'resend'
  })) {
    return { stored: false };
  }
  // 2. jsonl — required before the visitor is told the request was saved
  try {
    fs.mkdirSync(DATA_DIR, { recursive: true });
    fs.appendFileSync(LEADS_FILE, JSON.stringify(storedLead) + '\n');
  } catch (e) {
    console.error('lead file write failed:', lead.receiptId, e.message);
    // Do not start email after a failed write. The route returns 503 so the
    // client can retry; emailing here would turn that retry into a duplicate
    // owner notification while the lead still was not durably recorded.
    return { stored: false };
  }
  // 3. email — the only off-host copy the owner currently watches
  // Host + recipient alone looked like enough and is not:
  // nodemailer will happily connect unauthenticated, Gmail will refuse it, and
  // the lead is lost while every readiness check reports green. Half-configured
  // has to read as OFF, or the check is worse than no check.
  // Either route will do: RESEND_API_KEY (HTTPS) or a full SMTP set. On a host
  // that blocks outbound SMTP the first is the only one that works — see the
  // note above sendViaHttp.
  if (!delivery.ready) {
    // LOUD, once per lead. This was silent, and silence read as "no leads yet"
    // when it actually meant "leads arrived and nobody was told". stdout is
    // Render's log tail, so this is visible without digging.
    const missing = delivery.missing.length
      ? ' Missing: ' + delivery.missing.join(', ') + '.'
      : '';
    console.error(
      'LEAD_NOT_EMAILED receiptId=' + lead.receiptId + ' — delivery state=' + delivery.state +
      ', provider=' + (delivery.provider || 'none') + '. ' +
      (delivery.warning ? delivery.warning + ' ' : '') +
      missing +
      ' Until then this lead exists only in this log and the configured JSONL ' +
      'store; without LEON_DATA_DIR that file can disappear on a deploy.');
  } else {
    /* Fire-and-forget: the visitor already got their response, and the mail
     * must never hold the request open. openTransport() picks whichever port
     * this host can actually reach — see SMTP_PORTS above for why that is not
     * a fixed value. */
    const subj = leadEmailSubject(lead);
    const rows = leadEmailText(lead);
    if (delivery.provider === 'resend') {
      // The lead row already contains the immutable queue payload. Kick a send,
      // but do not await it: the visitor's acknowledgement remains immediate.
      scheduleLeadEmailOutbox(storedLead);
      return { stored: true };
    }
    openTransport()
      .then(({ t, port }) => t.sendMail({
        from: process.env.LEAD_FROM_EMAIL || process.env.SMTP_USER,
        to: process.env.LEAD_TO_EMAIL,
        replyTo: lead.email || undefined,   // hit reply and it goes to the visitor
        subject: subj,
        text: rows
      }).then(() => {
        // The port is in the success line on purpose: when a host's egress rules
        // change, this is the only place that records which route was working.
        console.log(`LEAD_MAILED receiptId=${lead.receiptId} to ${process.env.LEAD_TO_EMAIL} via port ${port}`);
      }))
      .catch(err => console.error(
        `LEAD_MAIL_FAILED receiptId=${lead.receiptId}`, (err && err.message) || err,
        '— tried ports', portsToTry().join(', '),
        '— the lead remains in this log and the configured JSONL store'));
  }
  return { stored: true };
}

/* Genuine leads captured since the last deploy, newest first. Admin-created
   delivery probes stay durable for outbox recovery and audit, but normal views
   exclude them so a pipeline check never becomes a reported inquiry. */
function readLeads(limit, { includeSynthetic = false } = {}) {
  const out = readStoredLeads()
    .filter(lead => includeSynthetic === true || lead.synthetic !== true)
    .map(publicLead);
  out.reverse();
  return out.slice(0, limit || 200);
}

/* Return only operational delivery metadata for one opaque receipt. The
 * immutable email payload deliberately stays private: it contains both the
 * configured destination and any contact details supplied by a real lead. */
function leadEmailStatus(receiptId) {
  const wanted = String(receiptId || '');
  if (!RECEIPT_ID_RE.test(wanted)) return null;
  const events = readLeadEmailOutbox();
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const event = events[index];
    if (event.receiptId !== wanted) continue;
    const status = {
      receiptId: wanted,
      state: event.state,
      at: event.at,
      attempts: event.attempts,
      provider: event.provider
    };
    if (event.providerMessageId) status.providerMessageId = event.providerMessageId;
    if (event.nextAttemptAt) status.nextAttemptAt = event.nextAttemptAt;
    return status;
  }
  return null;
}

function findStoredLeadByReceipt(receiptId) {
  const wanted = String(receiptId || '');
  if (!RECEIPT_ID_RE.test(wanted)) return null;
  const leads = readStoredLeads({ strict: true });
  for (let index = leads.length - 1; index >= 0; index -= 1) {
    if (leads[index] && leads[index].receiptId === wanted) return leads[index];
  }
  return null;
}

/* Record the operator's literal inbox observation without editing either
 * append-only delivery ledger. Only a sent, server-generated synthetic probe is
 * eligible, so this route cannot turn an ordinary lead into health evidence. */
function confirmLeadEmailInbox(receiptId, { now = Date.now(), env = process.env } = {}) {
  const wanted = String(receiptId || '');
  if (!RECEIPT_ID_RE.test(wanted)) return { ok: false, reason: 'invalid_receipt' };
  const lead = findStoredLeadByReceipt(wanted);
  if (!lead) return { ok: false, reason: 'not_found' };
  if (lead.synthetic !== true || lead.recordType !== 'delivery_probe') {
    return { ok: false, reason: 'not_synthetic_probe' };
  }
  const status = leadEmailStatus(wanted);
  if (!status || status.state !== 'sent' || !status.providerMessageId) {
    return { ok: false, reason: 'not_sent' };
  }

  const fingerprint = outboxDeliveryFingerprint(lead._emailOutbox);
  if (!fingerprint || fingerprint !== leadDeliveryFingerprint(env)) {
    return { ok: false, reason: 'configuration_changed' };
  }
  const confirmations = readLeadEmailConfirmations();
  const prior = confirmations.find(event => (
    event.receiptId === wanted && event.configFingerprint === fingerprint
  ));
  if (prior) {
    return {
      ok: true,
      receiptId: wanted,
      confirmedAt: prior.at,
      deduplicated: true
    };
  }

  const event = {
    version: EMAIL_CONFIRMATION_VERSION,
    receiptId: wanted,
    state: 'inbox_confirmed',
    at: new Date(now).toISOString(),
    configFingerprint: fingerprint
  };
  try {
    fs.mkdirSync(path.dirname(LEAD_EMAIL_CONFIRMATIONS_FILE), { recursive: true });
    fs.appendFileSync(LEAD_EMAIL_CONFIRMATIONS_FILE, JSON.stringify(event) + '\n');
  } catch (error) {
    console.error(
      `lead email confirmation write failed: ${wanted}`,
      String(error && error.message || error).slice(0, 300));
    return { ok: false, reason: 'store_failed' };
  }
  return {
    ok: true,
    receiptId: wanted,
    confirmedAt: event.at,
    deduplicated: false
  };
}

function leadEmailVerification(env = process.env) {
  const fingerprint = leadDeliveryFingerprint(env);
  const confirmations = readLeadEmailConfirmations();
  for (let index = confirmations.length - 1; index >= 0; index -= 1) {
    const event = confirmations[index];
    if (event.configFingerprint !== fingerprint) continue;
    const lead = findStoredLeadByReceipt(event.receiptId);
    const status = lead && lead.synthetic === true && lead.recordType === 'delivery_probe'
      ? leadEmailStatus(event.receiptId)
      : null;
    if (status && status.state === 'sent' && status.providerMessageId) {
      return { verified: true, confirmedAt: event.at };
    }
  }
  return { verified: false, confirmedAt: null };
}

/* Read newest-to-oldest and stop at the first matching durable record. This is
   intentionally separate from readLeads' display limit: idempotency must still
   work after the store grows beyond the 200 records shown by default. */
function findLeadByIdempotencyKey(key) {
  if (!IDEMPOTENCY_KEY_RE.test(String(key || ''))) return null;
  let raw = '';
  try { raw = fs.readFileSync(LEADS_FILE, 'utf8'); } catch (e) { return null; }
  const lines = raw.split('\n');
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    if (!lines[i].trim()) continue;
    try {
      const lead = JSON.parse(lines[i]);
      if (lead && lead.idempotencyKey === key) return lead;
    } catch (e) { /* skip a torn line */ }
  }
  return null;
}

/* ── HTTP email, and why it is the default when configured ──────────────────
 *
 * SMTP DOES NOT WORK FROM THIS HOST. Measured 2026-08-21, after fixing two
 * unrelated faults on the way down:
 *
 *   LEAD_MAIL_FAILED Connection timeout — tried ports 587, 465
 *
 * Both Gmail ports, over IPv4, one attempt, after a four-minute cooldown to
 * rule out Google's connection throttling. Render's containers do not allow
 * outbound SMTP. No amount of credential or port fiddling changes that, and the
 * failure is silent: the lead is captured, the visitor is thanked, and nobody
 * is told.
 *
 * Port 443 demonstrably works — every OpenAI call on this service goes out that
 * way. So the mail goes out that way too.
 *
 * RESEND_API_KEY switches this on. Without it the code falls back to SMTP, so
 * this file still works unchanged on a host that permits it (a laptop, a VPS),
 * and adding the key is the only step needed here.
 */
async function sendViaHttp(outbox) {
  const key = String(process.env.RESEND_API_KEY || '').trim();
  if (!key) throw new Error('Resend API key is unavailable; notification remains queued');
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      authorization: `Bearer ${key}`,
      'idempotency-key': outbox.idempotencyKey
    },
    signal: AbortSignal.timeout(15_000),
    body: JSON.stringify(outbox.payload)
  });
  if (!r.ok) {
    const body = await r.text().catch(() => '');
    throw new Error(`resend HTTP ${r.status}: ${body.slice(0, 200)}`);
  }
  return r.json().catch(() => ({}));
}

/* SMTP ports to try, in order, and why there is more than one.
 *
 * Render's containers cannot reach smtp.gmail.com:587 at all. IPv6 gives an
 * immediate `ENETUNREACH`; IPv4 just hangs until the two-minute timeout. Port
 * 465 speaks implicit TLS instead of STARTTLS and is a different path out.
 *
 * The host's egress rules are not something this app should be brittle about,
 * and they are not something the operator should have to discover through
 * missing leads. So: try the configured port, and on a NETWORK failure only,
 * try the other one. An auth rejection (535) is not retried — a wrong password
 * is wrong on every port, and hammering Gmail with it earns a block.
 */
const SMTP_PORTS = [465, 587];

function portsToTry() {
  const asked = Number(process.env.SMTP_PORT || 587);
  const configured = Number.isInteger(asked) && asked > 0 && asked <= 65535 ? asked : 587;
  return [configured, ...SMTP_PORTS.filter(p => p !== configured)];
}

/** A network failure is worth retrying on another port; a rejection is not. */
const isNetworkError = (e) => {
  const c = String(e && (e.code || '')) + ' ' + String(e && e.message || '');
  return /ETIMEDOUT|ENETUNREACH|ECONNREFUSED|EHOSTUNREACH|Connection timeout|Greeting never received/i.test(c);
};

/* Resolve the SMTP host to an IPv4 LITERAL ourselves, and connect to that.
 *
 * Two softer fixes were tried first and both failed, which is why this one looks
 * heavy-handed:
 *
 *   1. `family: 4` on the transport. nodemailer 9 does not reliably pass it down
 *      to net.connect. 9 of 10 attempts still went to an AAAA address.
 *   2. `dns.setDefaultResultOrder('ipv4first')` process-wide. That governs
 *      dns.lookup, and nodemailer does its OWN resolution rather than going
 *      through lookup, so it sails straight past the setting. Measured: still
 *      `connect ENETUNREACH 2607:f8b0:400e:c05::6d:465 - Local (:::0)`, and the
 *      `Local (:::0)` in that message is the giveaway — an IPv6 wildcard bind.
 *
 * Handing nodemailer an address instead of a name leaves nothing to resolve and
 * nothing to get wrong. `tls.servername` carries the real hostname so SNI and
 * certificate validation still work — without it, the cert would be checked
 * against an IP and every connection would fail to verify.
 *
 * Cached for a few minutes: Gmail rotates these, and re-resolving on every lead
 * is a DNS round trip in the path of something a person is waiting on.
 */
let _ipCache = { host: null, ip: null, at: 0 };
const IP_TTL_MS = 5 * 60 * 1000;

async function resolveIPv4(host) {
  const now = Date.now();
  if (_ipCache.host === host && _ipCache.ip && now - _ipCache.at < IP_TTL_MS) return _ipCache.ip;
  const { resolve4 } = require('dns').promises;
  const addrs = await resolve4(host);
  if (!addrs || !addrs.length) throw new Error(`no A record for ${host}`);
  _ipCache = { host, ip: addrs[0], at: now };
  return addrs[0];
}

async function transportFor(port) {
  const nodemailer = require('nodemailer');
  const host = process.env.SMTP_HOST;
  const ip = await resolveIPv4(host);
  return nodemailer.createTransport({
    host: ip,                      // an address, so there is nothing left to resolve
    port,
    secure: port === 465,          // implicit TLS on 465, STARTTLS on 587
    family: 4,
    tls: { servername: host },     // SNI + cert validation against the real name
    auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS },
    connectionTimeout: 15000,
    greetingTimeout: 15000
  });
}

/** Returns a connected, authenticated transport plus the port that worked, or
 *  throws the LAST error so the caller can log something diagnostic. */
async function openTransport() {
  let last;
  for (const port of portsToTry()) {
    try {
      const t = await transportFor(port);
      await t.verify();
      return { t, port };
    } catch (e) {
      last = e;
      if (!isNetworkError(e)) throw e;   // auth/config problem — same on every port
    }
  }
  throw last;
}

/* Opens a real connection to the SMTP host and authenticates, using the SAME
 * settings the sender uses — including family:4.
 *
 * WHY THIS EXISTS. /api/health reported leadEmail:true for hours while every
 * single send failed, because it only ever counted environment variables. Five
 * variables being present says nothing about whether the host is reachable or
 * the credentials are accepted; the first real lead is a terrible place to find
 * that out, and on an ephemeral disk it is also the last place, because the
 * record is gone at the next deploy.
 *
 * Deliberately NOT run on every /api/health call: this opens a TCP connection
 * and does a full SMTP auth handshake, and health is polled. It runs on
 * /api/health?deep=1, which is the thing to curl after changing any SMTP
 * setting.
 *
 * DO NOT LOOP THIS (2026-08-21). Eight ?deep=1 calls in two minutes, to prove a
 * fix was stable, produced one success and seven `Connection timeout`s — and the
 * timeouts were caused BY the checking. Each call is a real AUTH, and repeated
 * logins from a datacenter address are what Google throttles; it drops packets
 * rather than returning an SMTP error, so the symptom is indistinguishable from
 * the network fault this check exists to find.
 *
 * A verification that induces the failure it is testing for is worse than no
 * verification, because it reads as evidence. Run it ONCE after a change. To
 * confirm the pipeline end to end, run one admin delivery probe, verify its
 * provider ID, and record that same receipt/tag observed in the target inbox. */
async function verifyMail() {
  const delivery = leadDeliveryConfig();
  if (!delivery.configured) {
    return {
      ok: false,
      provider: delivery.provider,
      level: 'configuration',
      reason: 'not configured — missing ' + delivery.missing.join(', ')
    };
  }
  if (!delivery.supported) {
    return {
      ok: false,
      provider: delivery.provider,
      level: 'platform',
      reason: delivery.warning
    };
  }
  if (delivery.provider === 'resend') {
    // There is no honest, side-effect-free Resend check that proves this API
    // key, From identity, recipient and inbox all work together. Listing domains
    // only checks one credential permission and previously overstated that as
    // "leadEmailWorks". Do not send mail from a public GET health endpoint.
    return {
      ok: null,
      provider: 'resend',
      level: 'configuration',
      reason: 'Resend HTTPS delivery is configured but not verified. Run one admin delivery probe, confirm provider acceptance, then record the matching receipt observed in the target inbox.'
    };
  }
  try {
    const { port } = await openTransport();
    return {
      ok: true,
      provider: 'smtp',
      level: 'connection',
      port,
      reason: `SMTP connected and authenticated on port ${port}; no message was sent, so inbox delivery is not verified.`
    };
  } catch (e) {
    // The message is the diagnosis and belongs in the response: ENETUNREACH is a
    // routing problem, 535 is a wrong password, and they need opposite fixes.
    return {
      ok: false,
      provider: 'smtp',
      level: 'connection',
      reason: String(e && e.message || e).slice(0, 200)
    };
  }
}

module.exports = {
  validateLead,
  persistLead,
  readLeads,
  findLeadByIdempotencyKey,
  leadFingerprint,
  clean,
  verifyMail,
  leadDeliveryConfig,
  drainLeadEmailOutbox,
  readLeadEmailOutbox,
  leadEmailStatus,
  confirmLeadEmailInbox,
  leadEmailVerification,
  startLeadEmailOutbox,
  maskEmail,
  isRenderRuntime
};
