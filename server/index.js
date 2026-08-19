/* leon-assist — the small API behind the site's chat assistant + lead intake.
   The static site stays a Render static site; this runs as its own web service.
   Secrets live ONLY in environment variables (Render -> Environment). Nothing
   here ever sends a key to the browser or to the model context.

   Routes:
     GET  /api/health   — warm-up ping (the widget calls it when the panel opens)
     POST /api/chat     — streams assistant text (plain chunked text, not SSE)
     POST /api/lead     — validated lead intake (chat handoff + quote form)
     POST /api/event    — tiny first-party analytics beacon -> stdout ("EVT ...")
   Also serves the static site, so one service can host everything if wanted. */

'use strict';

const path = require('path');
const express = require('express');

let OpenAI = null;
try { OpenAI = require('openai'); } catch (e) { /* handled at call time */ }

const { SYSTEM_PROMPT } = require('./prompt');
const { validateLead, persistLead, readLeads, clean } = require('./leads');

const app = express();
app.disable('x-powered-by');
app.set('trust proxy', 1); // Render sits behind a proxy; makes req.ip real

const PORT = Number(process.env.PORT || 8787);
const MODEL = process.env.OPENAI_MODEL || 'gpt-5-mini';
const MAX_OUTPUT = Math.min(Number(process.env.OPENAI_MAX_OUTPUT || 700), 2000);
const KEY = process.env.OPENAI_API_KEY || '';

const client = KEY && OpenAI ? new OpenAI({ apiKey: KEY }) : null;

/* ── CORS: only the site, localhost, and one optional extra origin ── */
const ORIGINS = new Set([
  'https://leonkelvinli.onrender.com',
  'http://localhost:8787', 'http://127.0.0.1:8787',
  'http://localhost:4599', 'http://127.0.0.1:4599'
]);
if (process.env.EXTRA_ORIGIN) ORIGINS.add(process.env.EXTRA_ORIGIN);

app.use((req, res, next) => {
  const o = req.headers.origin;
  if (o && ORIGINS.has(o)) {
    res.setHeader('Access-Control-Allow-Origin', o);
    res.setHeader('Vary', 'Origin');
    res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.setHeader('Access-Control-Max-Age', '86400');
  }
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

app.use(express.json({ limit: '48kb' }));

/* ── rate limiting: in-memory buckets, plus a daily model-call ceiling ── */
const buckets = new Map(); // ip -> {n, t}
function limited(ip, max, windowMs) {
  const now = Date.now();
  const b = buckets.get(ip);
  if (!b || now - b.t > windowMs) { buckets.set(ip, { n: 1, t: now }); return false; }
  b.n += 1;
  return b.n > max;
}
setInterval(() => {
  const now = Date.now();
  for (const [k, v] of buckets) if (now - v.t > 15 * 60_000) buckets.delete(k);
}, 5 * 60_000).unref();

let dayKey = '', dayCalls = 0;
const DAILY_CAP = Number(process.env.DAILY_MODEL_CAP || 500);
function overDailyCap() {
  const k = new Date().toISOString().slice(0, 10);
  if (k !== dayKey) { dayKey = k; dayCalls = 0; }
  dayCalls += 1;
  return dayCalls > DAILY_CAP;
}

/* ── per-session memory: rolling summary so history stays bounded ── */
const sessions = new Map(); // sessionId -> {summary, ts}
setInterval(() => {
  const now = Date.now();
  for (const [k, v] of sessions) if (now - v.ts > 2 * 60 * 60_000) sessions.delete(k);
}, 10 * 60_000).unref();

const RECENT_WINDOW = 14;   // messages passed verbatim
const HARD_MSG_CAP = 60;    // absolute conversation cap

function normalizeHistory(raw) {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter(m => m && (m.role === 'user' || m.role === 'assistant') && typeof m.content === 'string')
    .map(m => ({ role: m.role, content: m.content.slice(0, 4000) }))
    .slice(-HARD_MSG_CAP);
}

async function summarize(messages) {
  if (!client) return '';
  try {
    const text = messages.map(m => `${m.role}: ${m.content}`).join('\n').slice(0, 12000);
    const r = await client.responses.create({
      model: MODEL,
      instructions: 'Summarize this website chat into <=120 words of plain facts a consultant needs: business type, problem, current workflow/tools, desired outcome, timeline, budget, contact details if given. No commentary.',
      input: text,
      max_output_tokens: 220,
      ...(reasoningOpts())
    });
    return (r.output_text || '').trim();
  } catch (e) { return ''; }
}

function reasoningOpts() {
  // gpt-5 family / o-series accept reasoning effort; other models reject it
  return /^(gpt-5|o\d)/.test(MODEL) ? { reasoning: { effort: 'minimal' } } : {};
}

/* ── health ── */
app.get('/api/health', (req, res) => res.json({ ok: true, model: client ? MODEL : null }));

/* ── chat (streams plain text chunks) ── */
app.post('/api/chat', async (req, res) => {
  const ip = req.ip || 'x';
  if (limited('c:' + ip, 20, 5 * 60_000)) return res.status(429).json({ error: 'slow down a little — try again in a few minutes.' });
  if (!client) return res.status(503).json({ error: 'assistant is not configured yet. email leondragon3798@gmail.com instead.' });
  if (overDailyCap()) return res.status(503).json({ error: 'the assistant hit its daily limit. email leondragon3798@gmail.com and a human will answer.' });

  const sessionId = clean(String(req.body.sessionId || ''), 64) || ip;
  const page = clean(String(req.body.page || ''), 200);
  let history = normalizeHistory(req.body.messages);
  if (!history.length || history[history.length - 1].role !== 'user') {
    return res.status(400).json({ error: 'send at least one user message.' });
  }
  if (history.length >= HARD_MSG_CAP) {
    return res.status(400).json({ error: "this chat got long — hit 'new chat', or just email leon directly." });
  }

  // bound the context: summarize older turns once, keep the recent window verbatim
  const sess = sessions.get(sessionId) || { summary: '', ts: Date.now() };
  if (history.length > RECENT_WINDOW) {
    const older = history.slice(0, history.length - RECENT_WINDOW);
    const s = await summarize(older);
    if (s) sess.summary = s;
    history = history.slice(-RECENT_WINDOW);
  }
  sess.ts = Date.now();
  sessions.set(sessionId, sess);

  const input = [];
  if (sess.summary) input.push({ role: 'developer', content: 'Summary of the earlier part of this conversation: ' + sess.summary });
  if (page) input.push({ role: 'developer', content: 'The visitor is currently on this page of the site: ' + page });
  for (const m of history) input.push(m);

  res.status(200);
  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Accel-Buffering', 'no');

  const timeout = setTimeout(() => { try { res.end('\n[timed out — try again]'); } catch (e) {} }, 90_000);
  try {
    const stream = await client.responses.create({
      model: MODEL,
      instructions: SYSTEM_PROMPT,
      input,
      max_output_tokens: MAX_OUTPUT,
      stream: true,
      ...(reasoningOpts())
    });
    for await (const ev of stream) {
      if (ev.type === 'response.output_text.delta' && ev.delta) res.write(ev.delta);
      if (ev.type === 'response.failed') throw new Error('response failed');
    }
    res.end();
  } catch (e) {
    console.error('chat error:', e.status || '', e.message);
    try {
      if (!res.headersSent) res.status(502).json({ error: 'assistant unavailable right now.' });
      else res.end("\n\n[i lost the connection — send that again, or email leondragon3798@gmail.com]");
    } catch (e2) {}
  } finally {
    clearTimeout(timeout);
  }
});

/* ── lead intake ── */
app.post('/api/lead', async (req, res) => {
  const ip = req.ip || 'x';
  if (limited('l:' + ip, 6, 10 * 60_000)) return res.status(429).json({ error: 'too many submissions — give it a few minutes.' });

  const body = req.body || {};
  // If the widget sent a transcript instead of a summary, condense it server-side.
  if (!body.conversationSummary && Array.isArray(body.messages) && body.messages.length) {
    body.conversationSummary = await summarize(normalizeHistory(body.messages));
    if (!body.conversationSummary) {
      body.conversationSummary = normalizeHistory(body.messages)
        .map(m => `${m.role}: ${m.content}`).join('\n').slice(0, 6000);
    }
  }
  const { lead, error } = validateLead(body);
  if (error) return res.status(400).json({ error });
  persistLead(lead);
  res.json({ ok: true });
});

/* ── reading the leads back ──
   Leads live on Render's ephemeral disk, so this shows everything since the last
   deploy. Off unless LEADS_KEY is set; ?format=json for the raw records. */
app.get('/api/leads', (req, res) => {
  const key = process.env.LEADS_KEY || '';
  if (!key) return res.status(404).json({ error: 'not enabled' });
  if (String(req.query.key || '') !== key) return res.status(401).json({ error: 'wrong key' });

  const leads = readLeads(Number(req.query.limit) || 200);
  if (req.query.format === 'json') return res.json({ count: leads.length, leads });

  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const card = l => '<article><h2>' + esc(l.name || l.email) + ' <small>' + esc(l.via) + ' · ' + esc(l.ts) + '</small></h2>'
    + '<p><a href="mailto:' + esc(l.email) + '">' + esc(l.email) + '</a>'
    + (l.phone ? ' · <a href="tel:' + esc(l.phone) + '">' + esc(l.phone) + '</a>' : '') + '</p>'
    + (l.company ? '<p><b>business:</b> ' + esc(l.company) + '</p>' : '')
    + (l.problem ? '<pre>' + esc(l.problem) + '</pre>' : '')
    + (l.conversationSummary ? '<pre>' + esc(l.conversationSummary) + '</pre>' : '')
    + (l.budget || l.timeline ? '<p><b>budget:</b> ' + esc(l.budget || '—') + ' · <b>timeline:</b> ' + esc(l.timeline || '—') + '</p>' : '')
    + '<p class="src">' + esc(l.sourcePage || '') + ' ' + esc(l.utmSource || '') + '</p></article>';

  res.type('html').send('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    + '<meta name="robots" content="noindex"><title>leads (' + leads.length + ')</title>'
    + '<style>body{background:#0b0b0c;color:#e7e7ea;font:15px/1.55 ui-monospace,Menlo,monospace;margin:0;padding:24px}'
    + 'h1{font-size:15px;letter-spacing:.12em;text-transform:uppercase;color:#8a8a93}'
    + 'article{border:1px solid #26262b;border-radius:12px;padding:16px;margin:14px 0;max-width:760px}'
    + 'h2{font-size:16px;margin:0 0 6px}small{color:#8a8a93;font-weight:400}'
    + 'pre{white-space:pre-wrap;background:#141416;padding:12px;border-radius:8px;margin:8px 0}'
    + 'a{color:#a78bfa}.src{color:#6b6b73;font-size:12px}p{margin:6px 0}</style>'
    + '<h1>' + leads.length + ' leads since last deploy</h1>'
    + (leads.length ? leads.map(card).join('') : '<p>nothing yet. leads reset whenever the service redeploys.</p>'));
});

/* ── event beacon ── */
app.post('/api/event', (req, res) => {
  const ip = req.ip || 'x';
  if (limited('e:' + ip, 120, 10 * 60_000)) return res.sendStatus(204);
  const name = clean(String((req.body || {}).name || ''), 48);
  if (name) {
    console.log('EVT ' + JSON.stringify({
      ts: new Date().toISOString(),
      name,
      path: clean(String(req.body.path || ''), 200),
      ref: clean(String(req.body.ref || ''), 200),
      utm: clean(String(req.body.utm || ''), 200)
    }));
  }
  res.sendStatus(204);
});

/* ── static site (lets one service host everything if ever wanted) ── */
const ROOT = path.join(__dirname, '..');
app.use((req, res, next) => {
  if (/^\/(server|tools|data|node_modules)(\/|$)|^\/\.|\/\.env/.test(req.path)) return res.sendStatus(404);
  next();
});
app.use(express.static(ROOT, { extensions: ['html'], index: 'index.html', maxAge: '10m' }));

app.use((req, res) => res.status(404).send('not found'));

app.listen(PORT, () => {
  console.log(`leon-assist on :${PORT} — model=${client ? MODEL : 'NOT CONFIGURED'} dailyCap=${DAILY_CAP}`);
});
