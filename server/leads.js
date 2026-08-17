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

const clean = (v, max) => {
  if (typeof v !== 'string') return '';
  return v.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, '').trim().slice(0, max);
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function validateLead(body) {
  const lead = {
    ts: new Date().toISOString(),
    name: clean(body.name, 120),
    email: clean(body.email, 200).toLowerCase(),
    phone: clean(body.phone, 40),
    company: clean(body.company, 160),
    industry: clean(body.industry, 120),
    problem: clean(body.problem, 4000),
    currentTools: clean(body.currentTools, 500),
    desiredOutcome: clean(body.desiredOutcome, 1000),
    timeline: clean(body.timeline, 120),
    budget: clean(body.budget, 60),
    sourcePage: clean(body.sourcePage, 300),
    referrer: clean(body.referrer, 300),
    utmSource: clean(body.utmSource, 120),
    utmMedium: clean(body.utmMedium, 120),
    utmCampaign: clean(body.utmCampaign, 120),
    via: clean(body.via, 30) || 'site',           // 'chat' | 'quote-form' | 'site'
    conversationSummary: clean(body.conversationSummary, 8000)
  };
  if (!lead.email || !EMAIL_RE.test(lead.email)) return { error: 'a valid email is required' };
  if (!lead.problem && !lead.conversationSummary) return { error: 'tell me at least a sentence about the project' };
  if (body.website) return { error: 'rejected' }; // honeypot field — bots fill it
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
  // 3. email — optional
  if (process.env.SMTP_HOST && process.env.LEAD_TO_EMAIL) {
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
        { from: process.env.SMTP_USER, to: process.env.LEAD_TO_EMAIL, subject: subj, text: rows },
        err => { if (err) console.error('lead mail failed:', err.message); }
      );
    } catch (e) { console.error('lead mail failed:', e.message); }
  }
}

module.exports = { validateLead, persistLead, clean };
