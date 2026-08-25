/* Lead intake: validate, sanitize, persist, notify.
   Copies, in order:
   1. stdout      — always, but only as durable as the host's log retention.
   2. jsonl file  — best effort. data/leads.jsonl by default, or LEON_DATA_DIR.
   3. email       — Resend over HTTPS, or SMTP on hosts where SMTP egress works. */

'use strict';

const fs = require('fs');
const path = require('path');
const { createHash, randomUUID } = require('crypto');
const { normalizeAttribution } = require('./attribution');
const { dataFile } = require('./storage');

const LEADS_FILE = dataFile('leads.jsonl', 'LEADS_FILE');
const DATA_DIR = path.dirname(LEADS_FILE);

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
  const lead = {
    ts: new Date().toISOString(),
    receiptId: newReceiptId(),
    name: clean(body.name, 120),
    email: clean(body.email, 200).toLowerCase(),
    phone: clean(body.phone, 40),
    company: clean(body.company, 160),
    industry: clean(body.industry, 120),
    service: clean(body.service, 120),
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
    if (key === 'ts' || key === 'receiptId' || key === 'idempotencyKey') continue;
    const value = lead[key];
    if (value === '' || value == null) continue;
    canonical[key] = value;
  }
  return createHash('sha256').update(JSON.stringify(canonical)).digest('hex');
}

function persistLead(lead) {
  // 1. stdout — the sink that always works
  console.log('LEAD ' + JSON.stringify(lead));
  // 2. jsonl — required before the visitor is told the request was saved
  try {
    fs.mkdirSync(DATA_DIR, { recursive: true });
    fs.appendFileSync(LEADS_FILE, JSON.stringify(lead) + '\n');
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
  const delivery = leadDeliveryConfig();
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
    const subj = `New website lead [${lead.receiptId}] — ${lead.service || lead.industry || lead.company || 'unknown'} — ${lead.via}`;
    const rows = Object.entries(lead)
      .filter(([, v]) => v)
      .map(([k, v]) => `${k}: ${v}`)
      .join('\n');
    if (delivery.provider === 'resend') {
      sendViaHttp(lead, subj, rows)
        .then(() => console.log(`LEAD_MAILED receiptId=${lead.receiptId} to ${process.env.LEAD_TO_EMAIL} via https (resend)`))
        .catch(err => console.error(
          `LEAD_MAIL_FAILED receiptId=${lead.receiptId}`, (err && err.message) || err,
          '— the lead remains in this log and the configured JSONL store'));
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

/* Everything captured since the last deploy, newest first. Backs GET /api/leads,
   which is the only way to read them without digging through Render's log tail. */
function readLeads(limit) {
  let raw = '';
  try { raw = fs.readFileSync(LEADS_FILE, 'utf8'); } catch (e) { return []; }
  const out = [];
  for (const line of raw.split('\n')) {
    if (!line.trim()) continue;
    try { out.push(JSON.parse(line)); } catch (e) { /* skip a torn line */ }
  }
  out.reverse();
  return out.slice(0, limit || 200);
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
async function sendViaHttp(lead, subject, text) {
  const key = String(process.env.RESEND_API_KEY || '').trim();
  // A verified domain is better than a gmail: it makes the notification look
  // like it came from the business, and it is what allows a real From address.
  const from = process.env.LEAD_FROM_EMAIL || 'Leon Builds <onboarding@resend.dev>';
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${key}` },
    signal: AbortSignal.timeout(15_000),
    body: JSON.stringify({
      from,
      to: [String(process.env.LEAD_TO_EMAIL || '').trim()],
      reply_to: lead.email || undefined,   // reply goes to the visitor, not to us
      subject,
      text
    })
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
 * confirm the pipeline end to end, post one uniquely tagged lead, look for
 * LEAD_MAILED, and confirm that same tag arrived in the target inbox. */
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
      reason: 'Resend HTTPS delivery is configured but not verified. Submit one uniquely tagged test lead and confirm both LEAD_MAILED and receipt in the target inbox.'
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
  maskEmail,
  isRenderRuntime
};
