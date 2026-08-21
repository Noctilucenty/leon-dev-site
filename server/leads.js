/* Lead intake: validate, sanitize, persist, notify.
   Sinks, in order of durability:
   1. stdout      — always. Render keeps logs; grep "LEAD ".
   2. jsonl file  — best effort. data/leads.jsonl (ephemeral on free Render, real on disk locally).
   3. SMTP email  — only if SMTP_HOST + LEAD_TO_EMAIL are configured. */

'use strict';

const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'data');
const LEADS_FILE = path.join(DATA_DIR, 'leads.jsonl');

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

function validateLead(body) {
  // Bots fill the hidden `website` field. Checked before anything else so the
  // response cannot be used to tell which check rejected them.
  if (body.website) return { bot: true };
  const lead = {
    ts: new Date().toISOString(),
    name: clean(body.name, 120),
    email: clean(body.email, 200).toLowerCase(),
    phone: clean(body.phone, 40),
    company: clean(body.company, 160),
    industry: clean(body.industry, 120),
    problem: clean(body.problem, 4000, true),
    currentTools: clean(body.currentTools, 500),
    desiredOutcome: clean(body.desiredOutcome, 1000, true),
    timeline: clean(body.timeline, 120),
    budget: clean(body.budget, 60),
    sourcePage: clean(body.sourcePage, 300),
    referrer: clean(body.referrer, 300),
    utmSource: clean(body.utmSource, 120),
    utmMedium: clean(body.utmMedium, 120),
    utmCampaign: clean(body.utmCampaign, 120),
    via: clean(body.via, 30) || 'site',           // 'chat' | 'quote-form' | 'site'
    conversationSummary: clean(body.conversationSummary, 8000, true)
  };
  if (!lead.email || !EMAIL_RE.test(lead.email)) return { error: 'a valid email is required' };
  if (!lead.problem && !lead.conversationSummary) return { error: 'tell me at least a sentence about the project' };
  return { lead };
}

function persistLead(lead) {
  // 1. stdout — the sink that always works
  console.log('LEAD ' + JSON.stringify(lead));
  // 2. jsonl — best effort
  try {
    fs.mkdirSync(DATA_DIR, { recursive: true });
    fs.appendFileSync(LEADS_FILE, JSON.stringify(lead) + '\n');
  } catch (e) { console.error('lead file write failed:', e.message); }
  // 3. email — the only sink the owner actually watches
  // All FOUR are required. Host + recipient alone looked like enough and is not:
  // nodemailer will happily connect unauthenticated, Gmail will refuse it, and
  // the lead is lost while every readiness check reports green. Half-configured
  // has to read as OFF, or the check is worse than no check.
  const mailReady = !!(process.env.SMTP_HOST && process.env.LEAD_TO_EMAIL
                       && process.env.SMTP_USER && process.env.SMTP_PASS);
  if (!mailReady) {
    // LOUD, once per lead. This was silent, and silence read as "no leads yet"
    // when it actually meant "leads arrived and nobody was told". stdout is
    // Render's log tail, so this is visible without digging.
    console.error(
      'LEAD_NOT_EMAILED — need all of SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS ' +
      'and LEAD_TO_EMAIL. Missing: ' +
      ['SMTP_HOST', 'SMTP_USER', 'SMTP_PASS', 'LEAD_TO_EMAIL']
        .filter(k => !process.env[k]).join(', ') +
      '. Until then this lead exists only in this log and in an ephemeral file ' +
      'that the next deploy erases.');
  } else {
    /* Fire-and-forget: the visitor already got their response, and the mail
     * must never hold the request open. openTransport() picks whichever port
     * this host can actually reach — see SMTP_PORTS above for why that is not
     * a fixed value. */
    const subj = `New website lead — ${lead.industry || lead.company || 'unknown'} — ${lead.via}`;
    const rows = Object.entries(lead)
      .filter(([, v]) => v)
      .map(([k, v]) => `${k}: ${v}`)
      .join('\n');
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
        console.log(`LEAD_MAILED to ${process.env.LEAD_TO_EMAIL} via port ${port}`);
      }))
      .catch(err => console.error(
        'LEAD_MAIL_FAILED', (err && err.message) || err,
        '— tried ports', portsToTry().join(', '),
        '— the lead is still in this log and in data/leads.jsonl until the next deploy'));
  }
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
  const configured = Number(process.env.SMTP_PORT || 587);
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
 * setting. */
async function verifyMail() {
  const missing = ['SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASS', 'LEAD_TO_EMAIL']
    .filter(k => !process.env[k]);
  if (missing.length) return { ok: false, reason: 'not configured — missing ' + missing.join(', ') };
  try {
    const { port } = await openTransport();
    return { ok: true, port, reason: `connected and authenticated on port ${port}` };
  } catch (e) {
    // The message is the diagnosis and belongs in the response: ENETUNREACH is a
    // routing problem, 535 is a wrong password, and they need opposite fixes.
    return { ok: false, reason: String(e && e.message || e).slice(0, 200) };
  }
}

module.exports = { validateLead, persistLead, readLeads, clean, verifyMail };
