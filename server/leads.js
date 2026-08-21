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
    try {
      const nodemailer = require('nodemailer');
      const t = nodemailer.createTransport({
        host: process.env.SMTP_HOST,
        port: Number(process.env.SMTP_PORT || 587),
        secure: Number(process.env.SMTP_PORT) === 465,
        /* IPv4 ONLY, AND THIS IS NOT A PREFERENCE (2026-08-21).
         *
         * Every lead silently failed to send for the first hours after SMTP was
         * configured, with the health endpoint reporting leadEmail:true the whole
         * time. Two different errors, one cause:
         *
         *   LEAD_MAIL_FAILED Connection timeout
         *   LEAD_MAIL_FAILED connect ENETUNREACH 2607:f8b0:400e:c02::6c:587
         *
         * That address is smtp.gmail.com's AAAA record. Node 20 resolves both
         * families and will happily pick IPv6; this container has no IPv6 route,
         * so the connect is unreachable. Whether it fails fast (ENETUNREACH) or
         * hangs for the full two-minute timeout is down to which record DNS
         * returned first that run — which is why it looked intermittent.
         *
         * `family: 4` is passed through to net.connect and takes IPv6 out of the
         * running entirely. Do not "clean this up": without it the mailer works
         * on any laptop and fails on the host that actually matters, and it fails
         * in the worst possible way, which is quietly.
         */
        family: 4,
        auth: process.env.SMTP_USER ? { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS } : undefined
      });
      const subj = `New website lead — ${lead.industry || lead.company || 'unknown'} — ${lead.via}`;
      const rows = Object.entries(lead)
        .filter(([, v]) => v)
        .map(([k, v]) => `${k}: ${v}`)
        .join('\n');
      t.sendMail(
        {
          from: process.env.LEAD_FROM_EMAIL || process.env.SMTP_USER,
          to: process.env.LEAD_TO_EMAIL,
          replyTo: lead.email || undefined,   // hit reply and it goes to the visitor
          subject: subj,
          text: rows
        },
        err => {
          if (err) console.error('LEAD_MAIL_FAILED', err.message);
          else console.log('LEAD_MAILED to ' + process.env.LEAD_TO_EMAIL);
        }
      );
    } catch (e) { console.error('lead mail failed:', e.message); }
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
    const nodemailer = require('nodemailer');
    const t = nodemailer.createTransport({
      host: process.env.SMTP_HOST,
      port: Number(process.env.SMTP_PORT || 587),
      secure: Number(process.env.SMTP_PORT) === 465,
      family: 4,                 // see the long note on the sender's transport
      auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS },
      connectionTimeout: 15000,  // fail the check fast; the sender may take longer
      greetingTimeout: 15000
    });
    await t.verify();
    return { ok: true, reason: 'connected and authenticated' };
  } catch (e) {
    // The message is the diagnosis and belongs in the response: ENETUNREACH is a
    // routing problem, 535 is a wrong password, and they need opposite fixes.
    return { ok: false, reason: String(e && e.message || e).slice(0, 200) };
  }
}

module.exports = { validateLead, persistLead, readLeads, clean, verifyMail };
