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
const { persistEvent, readEvents, sourceOf } = require('./events');

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
  'https://leonbuilds.org',
  'https://www.leonbuilds.org',
  // the old host stays allowed: every Marketplace listing and group post in the
  // wild still links to it, and Render keeps serving it alongside the domain.
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
    res.setHeader('Access-Control-Allow-Credentials', 'true');
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
    if (overDailyCap()) return '';
    const r = await client.responses.create({
      model: MODEL,
      instructions: 'Summarize this website chat into <=120 words of plain facts a consultant needs: business type, problem, current workflow/tools, desired outcome, timeline, budget, contact details if given. No commentary.',
      input: text,
      max_output_tokens: 220,
      ...(reasoningOpts())
    }, { timeout: 8000, maxRetries: 0 });
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
/* The visitor picks a language in the widget; honour it even when they type
   in a different one (a Brazilian owner writing broken english still wants the
   answer in portuguese). Unknown values fall through to the prompt's default. */
const REPLY_LANG = {
  pt: 'Brazilian Portuguese', zh: 'Simplified Chinese',
  es: 'Spanish', en: 'English'
};
function langLine(v) {
  const name = REPLY_LANG[String(v || '').slice(0, 2).toLowerCase()];
  if (!name) return '';
  return `\n\nREPLY LANGUAGE\nAnswer in ${name}, no matter which language the visitor writes in, unless they explicitly ask you to switch. Keep the same short, plain, one-question-at-most style. Prices stay in US dollars.`;
}

/* What the visitor is told when the model call fails for any reason. Always
   names a human channel — email and phone — in their own language. */
const DOWN_MSG = {
  en: "the assistant is down for a moment. email leondragon3798@gmail.com or call (510) 826-7735 and leon will answer you directly.",
  pt: "o assistente est\u00e1 fora do ar por um momento. manda um email para leondragon3798@gmail.com ou liga (510) 826-7735 que o leon te responde direto.",
  zh: "\u52a9\u624b\u6682\u65f6\u7528\u4e0d\u4e86\u3002\u53ef\u4ee5\u53d1\u90ae\u4ef6\u5230 leondragon3798@gmail.com \uff0c\u6216\u8005\u6253 (510) 826-7735\uff0cleon \u4f1a\u76f4\u63a5\u56de\u4f60\u3002",
  es: "el asistente est\u00e1 ca\u00eddo por un momento. escribe a leondragon3798@gmail.com o llama al (510) 826-7735 y leon te responde directamente.",
};
function downMessage(lang) {
  return DOWN_MSG[String(lang || '').slice(0, 2).toLowerCase()] || DOWN_MSG.en;
}

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
      instructions: SYSTEM_PROMPT + langLine(req.body.lang),
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
      // A dead assistant must still hand the visitor a way to reach a human —
      // on /pt and /zh the chat button is the PRIMARY call to action, so an
      // unexplained failure there is a lost lead, not a cosmetic bug.
      if (!res.headersSent) res.status(502).json({ error: downMessage(req.body.lang) });
      else res.end('\n\n' + downMessage(req.body.lang));
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
  // A transcript stands in for a summary immediately. Waiting on the model here is
  // what used to hold the request open for minutes on a slow or cold OpenAI call.
  const history = Array.isArray(body.messages) && body.messages.length ? normalizeHistory(body.messages) : null;
  if (!body.conversationSummary && history) {
    body.conversationSummary = history.map(m => `${m.role}: ${m.content}`).join('\n').slice(0, 6000);
  }
  const { lead, error, bot } = validateLead(body);
  if (bot) return res.json({ ok: true });   // looks identical to a real submission
  if (error) return res.status(400).json({ error });
  persistLead(lead);
  res.json({ ok: true });

  // The condensed version is a nicety; it lands in the log after the answer went out.
  if (history) {
    summarize(history)
      .then(sum => { if (sum) console.log('LEAD_SUMMARY ' + JSON.stringify({ ts: lead.ts, email: lead.email, summary: sum })); })
      .catch(() => {});
  }
});

/* ── reading the leads back ──
   Leads live on Render's ephemeral disk, so this shows everything since the last
   deploy. Off unless LEADS_KEY is set; ?format=json for the raw records. */
app.get('/api/leads', (req, res) => {
  const key = process.env.LEADS_KEY || '';
  if (!key) return res.status(404).json({ error: 'not enabled' });
  const given = String(req.get('x-leads-key') || req.query.key || '');
  if (given.length !== key.length || given !== key) return res.status(401).json({ error: 'wrong key' });

  const asked = Math.floor(Number(req.query.limit));
  const leads = readLeads(Number.isFinite(asked) && asked > 0 ? Math.min(asked, 1000) : 200);
  if (req.query.format === 'json') return res.json({ count: leads.length, leads });

  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
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
    persistEvent({
      ts: new Date().toISOString(),
      name,
      path: clean(String(req.body.path || ''), 200),
      ref: clean(String(req.body.ref || ''), 200),
      utm: clean(String(req.body.utm || ''), 200)
    });
  }
  res.sendStatus(204);
});

/* ── traffic dashboard — where visitors came from ──
   Same key and same caveat as /api/leads: events.jsonl resets on deploy;
   the permanent record is the "EVT " lines in Render logs. */
app.get('/api/traffic', (req, res) => {
  const key = process.env.LEADS_KEY || '';
  if (!key) return res.status(404).send('set LEADS_KEY in the environment to enable this view');
  const given = String(req.get('x-leads-key') || req.query.key || '');
  if (given !== key) return res.status(403).send('wrong key');

  const events = readEvents(5000);
  if (req.query.format === 'json') return res.json({ count: events.length, events });

  const count = (map, k) => { if (k) map.set(k, (map.get(k) || 0) + 1); };
  const bySource = new Map(), byName = new Map(), byPath = new Map(), byDay = new Map(), byLang = new Map();
  for (const ev of events) {
    count(byName, ev.name);
    count(byDay, String(ev.ts || '').slice(0, 10));
    if (ev.name === 'page_view') {
      count(bySource, sourceOf(ev));
      count(byPath, ev.path || '/');
      const lang = ev.path === '/pt' ? 'português' : ev.path === '/zh' ? '中文' : 'english';
      count(byLang, lang);
    }
  }
  const rows = (map) => [...map.entries()].sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `<tr><td>${String(k).replace(/</g, '&lt;')}</td><td>${v}</td></tr>`).join('')
    || '<tr><td colspan="2">nothing yet</td></tr>';
  const recent = events.slice(-40).reverse().map(ev =>
    `<tr><td>${String(ev.ts || '').slice(5, 16).replace('T', ' ')}</td><td>${ev.name}</td><td>${(ev.path || '').replace(/</g, '&lt;')}</td><td>${sourceOf(ev).replace(/</g, '&lt;')}</td></tr>`).join('');

  res.type('html').send('<!doctype html><meta charset="utf-8">'
    + '<meta name="robots" content="noindex"><meta name="viewport" content="width=device-width,initial-scale=1"><title>traffic</title>'
    + '<style>body{background:#000;color:#fafafa;font:14px/1.6 "JetBrains Mono",monospace;padding:2rem;max-width:880px;margin:auto}'
    + 'h1,h2{font-weight:500} h2{margin:2rem 0 .5rem;color:#9b8cff} table{width:100%;border-collapse:collapse}'
    + 'td{border-bottom:1px solid #1a1a1a;padding:.35rem .5rem} td:last-child{text-align:right;color:#aaa}'
    + '.recent td{text-align:left;color:#aaa;font-size:12px} p{color:#777}</style>'
    + `<h1>traffic — ${events.length} events since last deploy</h1>`
    + '<p>tag every link you post as ?s=name (e.g. /pt?s=fbgroup-br) and it shows up under sources. permanent history: "EVT " lines in render logs.</p>'
    + `<h2>visits by source</h2><table>${rows(bySource)}</table>`
    + `<h2>visits by language page</h2><table>${rows(byLang)}</table>`
    + `<h2>visits by page</h2><table>${rows(byPath)}</table>`
    + `<h2>events</h2><table>${rows(byName)}</table>`
    + `<h2>by day</h2><table>${rows(byDay)}</table>`
    + `<h2>last 40</h2><table class="recent">${recent}</table>`);
});

/* ── static site (lets one service host everything if ever wanted) ── */
const ROOT = path.join(__dirname, '..');
app.use((req, res, next) => {
  if (/^\/(server|tools|data|node_modules|research)(\/|$)|^\/\.|\/\.env/.test(req.path)
      || /^\/(README|readme)|\.(md|ya?ml|lock|log|bak|zip|py)$|^\/package(-lock)?\.json$/.test(req.path)) {
    return res.sendStatus(404);
  }
  next();
});
app.use(express.static(ROOT, { extensions: ['html'], index: 'index.html', maxAge: '10m' }));

app.use((req, res) => res.status(404).send('not found'));

app.listen(PORT, () => {
  console.log(`leon-assist on :${PORT} — model=${client ? MODEL : 'NOT CONFIGURED'} dailyCap=${DAILY_CAP}`);
});
