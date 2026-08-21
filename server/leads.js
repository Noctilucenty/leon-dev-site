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
  if (!process.env.SMTP_HOST || !process.env.LEAD_TO_EMAIL) {
    // LOUD, once per lead. This was silent, and silence read as "no leads yet"
    // when it actually meant "leads arrived and nobody was told". stdout is
    // Render's log tail, so this is visible without digging.
    console.error(
      'LEAD_NOT_EMAILED — SMTP_HOST and LEAD_TO_EMAIL are not both set, so this ' +
      'lead exists only in this log and in an ephemeral file that the next deploy ' +
      'erases. Set them in the Render dashboard.');
  } else {
    try {
      const nodemailer = require('nodemailer');
      const t = nodemailer.createTransport({
        host: process.env.SMTP_HOST,
        port: Number(process.env.SMTP_PORT || 587),
        secure: Number(process.env.SMTP_PORT) === 465,
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

module.exports = { validateLead, persistLead, readLeads, clean };
