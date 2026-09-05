/* leon-assist — the small API behind the site's chat assistant + lead intake.
   The static site stays a Render static site; this runs as its own web service.
   Secrets live ONLY in environment variables (Render -> Environment). Nothing
   here ever sends a key to the browser or to the model context.

   Routes:
     GET  /api/health   — warm-up ping (the widget calls it when the panel opens)
     POST /api/chat     — streams assistant text (plain chunked text, not SSE)
     POST /api/lead     — validated lead intake (chat handoff + quote form)
     POST /api/lead-delivery-probe — admin-only synthetic delivery check
     GET  /api/lead-delivery-status/:receiptId — admin-only outbox metadata
     POST /api/lead-delivery-confirm/:receiptId — admin-only inbox observation
     POST /api/event    — tiny first-party analytics beacon -> stdout ("EVT ...")
     POST /api/cal/webhook — signed Cal lifecycle events -> acquisition stages
     POST /api/acquisition/exclusions — admin-only append-only QA exclusions
     GET  /api/acquisition — admin-only booking/opportunity stage records
   This process is API-only; repository files are never served from this host. */

'use strict';

/* IPv4 FIRST, PROCESS-WIDE, BEFORE ANYTHING OPENS A SOCKET (2026-08-21).
 *
 * This container has no IPv6 route. Node 20 resolves both families and will
 * hand back the AAAA record often enough that outbound connections fail most of
 * the time and succeed occasionally, which is the worst of both worlds: it
 * looks intermittent rather than broken, so it reads as "flaky network" instead
 * of a fixed, findable fault.
 *
 * Measured on the SMTP path, where `family: 4` on the nodemailer transport was
 * NOT enough — nodemailer 9 does not reliably pass it down to net.connect, and
 * the deep check still failed nine times out of ten with
 * `connect ENETUNREACH 2607:f8b0:400e:c07::6c:465` before happening to get an
 * A record on the tenth. The one success was luck, not a fix.
 *
 * setDefaultResultOrder is the layer that actually decides, and it applies to
 * every outbound connection this process makes, not just mail. It must run
 * before the first socket is opened, hence the position at the top of the file.
 */
require('dns').setDefaultResultOrder('ipv4first');

const crypto = require('crypto');
const express = require('express');

let OpenAI = null;
try { OpenAI = require('openai'); } catch (e) { /* handled at call time */ }

const { SYSTEM_PROMPT } = require('./prompt');
const { buildSearchFunnel } = require('./search-funnel');
const { webVitalsReport } = require('./web-vitals-report');
const {
  validateLead,
  persistLead,
  readLeads,
  findStoredLeadByReceipt,
  findLeadByIdempotencyKey,
  leadFingerprint,
  clean,
  verifyMail,
  leadDeliveryConfig,
  visitorEmailConfirmationConfig,
  leadEmailStatus,
  confirmLeadEmailInbox,
  leadEmailVerification,
  startLeadEmailOutbox
} = require('./leads');
const {
  persistEvent,
  readEvents,
  sourceOf,
  normalizeEvent,
  funnelStats,
  deviceJourneyStats,
  reviewMilestoneStats
} = require('./events');
const {
  FUNNEL_STAGES,
  STAGE_DEFINITIONS,
  acquisitionStorageConfig,
  acquisitionStats,
  calWebhookRecord,
  normalizeQaExclusion,
  qaEventExclusion,
  qaExclusionSets,
  readAllAcquisition,
  recordBookingAttribution,
  recordQaExclusion,
  recordStage,
  verifyCalSignature
} = require('./acquisition');

const app = express();
app.disable('x-powered-by');
app.set('trust proxy', 1); // Render sits behind a proxy; makes req.ip real

const PORT = Number(process.env.PORT || 8787);
const MODEL = process.env.OPENAI_MODEL || 'gpt-5-mini';
const MAX_OUTPUT = Math.min(Number(process.env.OPENAI_MAX_OUTPUT || 700), 2000);
const KEY = process.env.OPENAI_API_KEY || '';

const client = KEY && OpenAI ? new OpenAI({ apiKey: KEY }) : null;

function escapeHtml(value) {
  return String(value == null ? '' : value).replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[char]));
}

/* Admin routes accept LEADS_KEY only in a header. Query-string secrets leak
   into browser history, reverse-proxy logs and referrers, so `?key=` is never a
   fallback. Buffer lengths are compared before timingSafeEqual can run. */
function adminKeyState(req) {
  const expected = Buffer.from(String(process.env.LEADS_KEY || ''));
  if (!expected.length) return 'disabled';
  const given = Buffer.from(String(req.get('x-leads-key') || ''));
  if (given.length !== expected.length) return 'unauthorized';
  return crypto.timingSafeEqual(given, expected) ? 'authorized' : 'unauthorized';
}

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

// A lead carries the whole conversation, so it needs more room than a chat
// turn. Mounted BEFORE the global parser — express's json parser is a no-op
// once req.body is set, so the first matching one wins.
// Images ride inside the chat payload as data: URLs, so this route needs far
// more headroom than the 48kb the rest of the API gets. The widget downscales
// to 1280px JPEG before sending and the server re-checks the size below, so a
// normal photo lands around 150-350kb and three of them still fit.
app.use('/api/chat', express.json({ limit: '3mb' }));
app.use('/api/lead', express.json({ limit: '256kb' }));
// Cal signs the exact request bytes. This raw parser must run before the global
// JSON parser or signature verification would be based on re-serialized data.
app.use('/api/cal/webhook', express.raw({ type: 'application/json', limit: '128kb' }));
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

/* A client keeps one opaque key while a lead submission is pending. Cache the
   accepted receipt before persistence/email so overlapping retries in this
   process collapse to one side effect; the JSONL lookup below restores the
   same guarantee after a restart. Only a hash of the lead stays in memory. */
const leadIdempotency = new Map(); // key -> {receiptId, fingerprint}
function rememberLeadIdempotency(key, receiptId, fingerprint) {
  leadIdempotency.set(key, { receiptId, fingerprint });
  // The durable JSONL file remains authoritative, so a bounded cache is enough.
  if (leadIdempotency.size > 2000) {
    const oldest = leadIdempotency.keys().next().value;
    leadIdempotency.delete(oldest);
  }
}

function forgetLeadIdempotency(lead) {
  if (!lead.idempotencyKey) return;
  const accepted = leadIdempotency.get(lead.idempotencyKey);
  if (accepted && accepted.receiptId === lead.receiptId) {
    leadIdempotency.delete(lead.idempotencyKey);
  }
}

function resolveLeadIdempotency(lead) {
  const key = lead.idempotencyKey;
  if (!key) return { fresh: true };
  const fingerprint = leadFingerprint(lead);
  let accepted = leadIdempotency.get(key);
  if (!accepted) {
    const durable = findLeadByIdempotencyKey(key);
    if (durable) {
      accepted = {
        receiptId: String(durable.receiptId || ''),
        fingerprint: leadFingerprint(durable)
      };
      rememberLeadIdempotency(key, accepted.receiptId, accepted.fingerprint);
    }
  }
  if (accepted) {
    if (accepted.fingerprint !== fingerprint) return { conflict: true };
    return { duplicate: true, receiptId: accepted.receiptId };
  }
  rememberLeadIdempotency(key, lead.receiptId, fingerprint);
  return { fresh: true };
}

const RECENT_WINDOW = 14;   // messages passed verbatim
const HARD_MSG_CAP = 60;    // absolute conversation cap

/* A visitor may attach photos — the menu taped to the counter, the spreadsheet
   someone updates every night, the booking notebook. Those are the fastest way
   to explain a business, and the assistant used to offer to look at them while
   the widget had no way to send one. */
const IMG_OK = /^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+$/;
const MAX_IMG_BYTES = 1_400_000;   // one downscaled photo, generously
const MAX_IMGS_PER_MSG = 3;

function normalizePart(part) {
  if (!part || typeof part !== 'object') return null;
  if (part.type === 'input_text' && typeof part.text === 'string') {
    return { type: 'input_text', text: part.text.slice(0, 4000) };
  }
  if (part.type === 'input_image' && typeof part.image_url === 'string') {
    const url = part.image_url;
    // Only inline data: URLs. A remote URL would make the server fetch whatever
    // a stranger points it at, which is a request-forgery hole, not a feature.
    if (!IMG_OK.test(url)) return null;
    if (url.length > MAX_IMG_BYTES) return null;
    return { type: 'input_image', image_url: url, detail: 'auto' };
  }
  return null;
}

function normalizeHistory(raw) {
  if (!Array.isArray(raw)) return [];
  const out = [];
  for (const m of raw) {
    if (!m || (m.role !== 'user' && m.role !== 'assistant')) continue;
    if (typeof m.content === 'string') {
      out.push({ role: m.role, content: m.content.slice(0, 4000) });
      continue;
    }
    if (Array.isArray(m.content)) {
      // Only a user turn can carry an image; an assistant turn is text we sent.
      if (m.role !== 'user') continue;
      let imgs = 0;
      const parts = [];
      for (const p of m.content) {
        const np = normalizePart(p);
        if (!np) continue;
        if (np.type === 'input_image') {
          if (++imgs > MAX_IMGS_PER_MSG) continue;
        }
        parts.push(np);
      }
      if (parts.length) out.push({ role: 'user', content: parts });
    }
  }
  return out.slice(-HARD_MSG_CAP);
}

/* Text only — for the summarizer and the lead record, where a base64 photo would
   blow the budget and tell a reader nothing. */
function textOf(m) {
  if (typeof m.content === 'string') return m.content;
  if (!Array.isArray(m.content)) return '';
  return m.content
    .map(p => (p.type === 'input_text' ? p.text : '[photo attached]'))
    .join(' ')
    .trim();
}

async function summarize(messages) {
  if (!client) return '';
  try {
    const text = messages.map(m => `${m.role}: ${textOf(m)}`).join('\n').slice(0, 12000);
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
/* Reports liveness separately from lead-delivery readiness, never a secret
   value. Render polls this route, so HTTP 200 / `ok:true` only means the process
   is up; it must not pretend a configured-but-blocked notification transport is
   working. */
app.get('/api/health', async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  const deep = req.query.deep === '1' || req.query.deep === 'true';
  if (deep) {
    // The deep SMTP path opens a real outbound connection and authenticates.
    // Keep warm-up/liveness public, but do not expose that operation as a public
    // GET. This endpoint intentionally accepts the key by header only so it does
    // not leak into URLs, browser history, proxy logs, or referrers.
    const auth = adminKeyState(req);
    if (auth === 'disabled') return res.status(404).json({ error: 'deep health is not enabled' });
    if (auth !== 'authorized') return res.status(401).json({ error: 'unauthorized' });
  }
  const delivery = leadDeliveryConfig();
  const visitorConfirmation = visitorEmailConfirmationConfig();
  const acquisitionStorage = acquisitionStorageConfig();
  let emailVerification = { verified: false, confirmedAt: null };
  if (delivery.ready && delivery.provider === 'resend') {
    try {
      emailVerification = leadEmailVerification();
    } catch (error) {
      console.error(
        'lead email verification read failed:',
        String(error && error.message || error).slice(0, 200));
    }
  }
  const body = {
    ok: true,
    model: client ? MODEL : null,
    vision: !!client,
    leadEmailProvider: delivery.provider,
    leadEmailTransport: delivery.transport,
    leadEmailState: emailVerification.verified ? 'verified' : delivery.state,
    leadEmailConfigured: delivery.configured,
    leadEmailSupported: delivery.supported,
    leadEmailReady: delivery.ready,
    visitorEmailConfirmationConfigured: visitorConfirmation.configured,
    visitorEmailConfirmationState: visitorConfirmation.state,
    // Backward-compatible name, with corrected semantics: a complete but known-
    // blocked SMTP setup on Render is false instead of a false green.
    leadEmail: delivery.ready,
    leadEmailVerified: emailVerification.verified,
    leadEmailMissing: delivery.missing,
    leadEmailWarning: delivery.warning,
    leadEmailTo: delivery.recipient,
    acquisitionStorageState: acquisitionStorage.state,
    acquisitionDurableConfigured: acquisitionStorage.durableConfigured,
    acquisitionLocalMode: acquisitionStorage.localMode,
    acquisitionSinkConfigured: acquisitionStorage.sinkConfigured,
    calWebhookConfigured: !!String(process.env.CAL_WEBHOOK_SECRET || '').trim()
  };
  if (emailVerification.confirmedAt) {
    body.leadEmailVerifiedAt = emailVerification.confirmedAt;
  }
  if (deep) {
    const v = await verifyMail();
    // A connection/auth check is not an end-to-end inbox-delivery test. Keep the
    // historical field, but never set it true unless an actual delivery can be
    // observed (a public GET endpoint must not send test mail).
    body.leadEmailWorks = v.ok === false ? false : null;
    body.leadEmailCheckPassed = v.ok;
    body.leadEmailCheckLevel = v.level;
    body.leadEmailCheckProvider = v.provider;
    body.leadEmailCheck = v.reason;
  }
  res.json(body);
});

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

/* The general prompt asks for a handoff once the problem is useful. This
   per-request instruction makes the timing deterministic: a detailed first
   message or two substantive turns are enough. The client tells us when the
   offer has already been rendered so the model never nags after a decline. */
const HANDOFF_QUESTION = {
  en: 'I have enough to brief Leon. Would you like me to send this project to him?',
  pt: 'Já tenho informações suficientes para explicar o projeto ao Leon. Quer que eu envie para ele?',
  es: 'Ya tengo suficiente información para explicarle el proyecto a Leon. ¿Quieres que se lo envíe?',
  zh: '我已经有足够的信息向 Leon 说明这个项目。要我现在把项目发给他吗？'
};
function shouldOfferHandoff(history, alreadyOffered) {
  if (alreadyOffered) return false;
  const userText = history
    .filter(message => message.role === 'user')
    .map(message => textOf(message).trim())
    .filter(Boolean);
  const chars = userText.join(' ').length;
  const latest = userText.at(-1) || '';
  const directIntent = /\b(hire|quote|start|send|submit|forward)\b.{0,45}\b(leon|project|app|website|this)\b|\b(leon|project|app|website|this)\b.{0,45}\b(hire|quote|start|send|submit|forward)\b/i.test(latest)
    || /(contratar|orçamento|presupuesto|enviar|mandar).{0,35}(leon|projeto|proyecto|aplicativo|app|site|web)/i.test(latest)
    || /(发给|发送|提交|报价|开始).{0,18}(Leon|项目|应用|网站)/i.test(latest);
  return directIntent || chars >= 80 || (userText.length >= 2 && chars >= 24);
}
function handoffLine(lang) {
  const code = String(lang || '').slice(0, 2).toLowerCase();
  const question = HANDOFF_QUESTION[code] || HANDOFF_QUESTION.en;
  return '\n\nHANDOFF THIS TURN\nThe visitor has given enough useful context. Answer their current point briefly, do not ask another discovery question, then end with this exact sentence: "' + question + '" Do not add text after it.';
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
  const streamFactory = process.env.NODE_ENV === 'test'
    && typeof app.locals.chatStreamFactory === 'function'
    ? app.locals.chatStreamFactory
    : null;
  if (!client && !streamFactory) return res.status(503).json({ error: 'assistant is not configured yet. email leondragon3798@gmail.com instead.' });
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

  const handoffInstruction = shouldOfferHandoff(history, req.body.handoffOffered === true)
    ? handoffLine(req.body.lang)
    : '';

  const request = {
    model: MODEL,
    instructions: SYSTEM_PROMPT + langLine(req.body.lang) + handoffInstruction,
    input,
    max_output_tokens: MAX_OUTPUT,
    stream: true,
    ...(reasoningOpts())
  };
  const controller = new AbortController();
  const abortOnDisconnect = () => {
    if (!res.writableEnded) controller.abort();
  };
  res.once('close', abortOnDisconnect);
  const timeoutMs = process.env.NODE_ENV === 'test' && Number.isFinite(app.locals.chatTimeoutMs)
    ? Math.max(10, app.locals.chatTimeoutMs)
    : 90_000;
  let timedOut = false;
  const timeout = setTimeout(() => {
    timedOut = true;
    controller.abort();
    // Once streaming has begun, an HTTP status can no longer change. End the
    // transport as an error so fetch's reader rejects and the existing widget
    // enters its human-handoff path instead of saving an error as model text.
    if (res.headersSent && !res.writableEnded && !res.destroyed) {
      res.destroy(new Error('chat stream timed out'));
    }
  }, timeoutMs);
  try {
    const stream = streamFactory
      ? await streamFactory(request, { signal: controller.signal })
      : await client.responses.create(request, {
          signal: controller.signal,
          timeout: timeoutMs,
          maxRetries: 0
        });
    res.status(200);
    res.setHeader('Content-Type', 'text/plain; charset=utf-8');
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Accel-Buffering', 'no');
    for await (const ev of stream) {
      if (ev.type === 'response.output_text.delta' && ev.delta) res.write(ev.delta);
      if (ev.type === 'response.failed' || ev.type === 'response.incomplete' || ev.type === 'error') {
        throw new Error('response stream failed');
      }
    }
    if (!res.destroyed && !res.writableEnded) res.end();
  } catch (e) {
    const error = e instanceof Error ? e : new Error(String(e || 'chat stream failed'));
    console.error('chat error:', error.status || '', error.message);
    if (res.destroyed || res.writableEnded) return;
    // Before the first byte, send a normal non-2xx response. After the first
    // byte, destroy the stream: the browser cannot see a new status at that
    // point, but it can reliably detect a failed body read.
    if (!res.headersSent) {
      res.status(timedOut ? 504 : 502).json({ error: downMessage(req.body.lang) });
    } else {
      res.destroy(error);
    }
  } finally {
    clearTimeout(timeout);
    res.off('close', abortOnDisconnect);
  }
});

/* ── lead delivery probe ──
   This is not a public form variant. It accepts no visitor data, requires the
   header-only admin key, and marks its durable row so normal lead counts exclude
   it. The fixed reserved address exercises the real Reply-To/outbox shape
   without inventing or disclosing a person's contact details. */
app.post('/api/lead-delivery-probe', (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  const auth = adminKeyState(req);
  if (auth === 'disabled') return res.status(404).json({ error: 'lead delivery probe is not enabled' });
  if (auth !== 'authorized') return res.status(401).json({ error: 'unauthorized' });
  if (req.body && Object.keys(req.body).length) {
    return res.status(400).json({ error: 'lead delivery probe does not accept caller data' });
  }
  const delivery = leadDeliveryConfig();
  if (!delivery.ready || delivery.provider !== 'resend') {
    return res.status(503).json({
      error: 'Resend lead delivery is not ready',
      state: delivery.state
    });
  }
  const ip = req.ip || 'x';
  if (limited('lp:' + ip, 1, 10 * 60_000)) {
    return res.status(429).json({ error: 'a lead delivery probe was already requested recently' });
  }

  const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
  const tag = `PIPELINE-CHECK-${stamp}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;
  const checked = validateLead({
    name: 'PIPELINE CHECK (not a lead)',
    email: 'pipeline-check@example.com',
    company: 'SYNTHETIC DELIVERY PROBE',
    service: 'lead-delivery-probe',
    problem: `Synthetic end-to-end delivery check; never count as a lead or client. Tag ${tag}`,
    via: 'pipeline-check',
    idempotencyKey: `leadreq_${crypto.randomUUID()}`
  });
  if (!checked.lead) return res.status(500).json({ error: 'could not create delivery probe' });
  checked.lead.synthetic = true;
  checked.lead.recordType = 'delivery_probe';
  const persistence = persistLead(checked.lead);
  if (!persistence.stored) {
    res.setHeader('Retry-After', '2');
    return res.status(503).json({ error: 'could not save the delivery probe' });
  }
  return res.status(202).json({
    ok: true,
    synthetic: true,
    receiptId: checked.lead.receiptId,
    tag,
    statusPath: `/api/lead-delivery-status/${checked.lead.receiptId}`
  });
});

app.get('/api/lead-delivery-status/:receiptId', (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  const auth = adminKeyState(req);
  if (auth === 'disabled') return res.status(404).json({ error: 'lead delivery status is not enabled' });
  if (auth !== 'authorized') return res.status(401).json({ error: 'unauthorized' });
  let status;
  try {
    status = leadEmailStatus(req.params.receiptId);
  } catch (error) {
    console.error('lead delivery status read failed:', String(error && error.message || error).slice(0, 200));
    return res.status(503).json({ error: 'lead delivery status is unavailable' });
  }
  if (!status) return res.status(404).json({ error: 'delivery receipt not found' });
  return res.json(status);
});

app.post('/api/lead-delivery-confirm/:receiptId', (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  const auth = adminKeyState(req);
  if (auth === 'disabled') return res.status(404).json({ error: 'lead delivery confirmation is not enabled' });
  if (auth !== 'authorized') return res.status(401).json({ error: 'unauthorized' });
  if (req.body && Object.keys(req.body).length) {
    return res.status(400).json({ error: 'lead delivery confirmation does not accept caller data' });
  }
  let confirmation;
  try {
    confirmation = confirmLeadEmailInbox(req.params.receiptId);
  } catch (error) {
    console.error('lead delivery confirmation failed:', String(error && error.message || error).slice(0, 200));
    return res.status(503).json({ error: 'lead delivery confirmation is unavailable' });
  }
  if (!confirmation.ok) {
    if (confirmation.reason === 'not_found' || confirmation.reason === 'invalid_receipt') {
      return res.status(404).json({ error: 'delivery receipt not found' });
    }
    if (confirmation.reason === 'store_failed') {
      return res.status(503).json({ error: 'could not save inbox confirmation' });
    }
    if (confirmation.reason === 'configuration_changed') {
      return res.status(409).json({ error: 'delivery configuration changed after this probe' });
    }
    return res.status(409).json({ error: 'only a sent synthetic delivery probe can be confirmed' });
  }
  return res.json({
    ok: true,
    verified: true,
    receiptId: confirmation.receiptId,
    confirmedAt: confirmation.confirmedAt,
    deduplicated: confirmation.deduplicated
  });
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
    body.conversationSummary = history.map(m => `${m.role}: ${textOf(m)}`).join('\n').slice(0, 6000);
  }
  const { lead, error, bot, receiptId } = validateLead(body);
  if (bot) return res.json({ ok: true, receiptId }); // same shape as a real submission
  if (error) return res.status(400).json({ error });
  const idempotency = resolveLeadIdempotency(lead);
  if (idempotency.conflict) {
    return res.status(409).json({ error: 'idempotency key already used for a different lead' });
  }
  if (idempotency.duplicate) {
    return res.json({ ok: true, receiptId: idempotency.receiptId, deduplicated: true });
  }
  const persistence = persistLead(lead);
  if (!persistence.stored) {
    forgetLeadIdempotency(lead);
    res.setHeader('Retry-After', '2');
    return res.status(503).json({ error: 'could not save the request — please try again.' });
  }
  res.json({ ok: true, receiptId: lead.receiptId });

  // The condensed version is a nicety; it lands in the log after the answer went out.
  if (history) {
    summarize(history)
      .then(sum => { if (sum) console.log('LEAD_SUMMARY ' + JSON.stringify({ ts: lead.ts, receiptId: lead.receiptId, email: lead.email, summary: sum })); })
      .catch(() => {});
  }
});

/* ── reading the leads back ──
   Shows records in the configured JSONL store. The default application path is
   replaceable; LEON_DATA_DIR can point at a durable mount. Off unless LEADS_KEY
   is set; ?format=json returns raw records. */
app.get('/api/leads', (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  const auth = adminKeyState(req);
  if (auth === 'disabled') return res.status(404).json({ error: 'not enabled' });
  if (auth !== 'authorized') return res.status(401).json({ error: 'unauthorized' });

  const asked = Math.floor(Number(req.query.limit));
  const includeSynthetic = req.query.includeSynthetic === '1'
    || req.query.includeSynthetic === 'true';
  const includeQaExcluded = req.query.includeQaExcluded === '1'
    || req.query.includeQaExcluded === 'true';
  const limit = Number.isFinite(asked) && asked > 0 ? Math.min(asked, 1000) : 200;
  let acquisitionRecords;
  try { acquisitionRecords = readAllAcquisition({ strict: true }); }
  catch (error) { return res.status(503).json({ error: 'acquisition ledger failed integrity checks' }); }
  const exclusionSets = qaExclusionSets(acquisitionRecords);
  if (exclusionSets.errors.length) {
    return res.status(503).json({ error: 'acquisition exclusion ledger failed integrity checks' });
  }
  const allCandidateLeads = readLeads(Number.MAX_SAFE_INTEGER, { includeSynthetic });
  const qaExcludedCount = allCandidateLeads.filter(lead =>
    exclusionSets.receiptIds.has(String(lead.receiptId || ''))).length;
  const leads = readLeads(limit, {
    includeSynthetic,
    excludeReceiptIds: includeQaExcluded ? null : exclusionSets.receiptIds
  });
  if (req.query.format === 'json') {
    return res.json({ count: leads.length, qaExcludedCount, leads });
  }

  const card = l => '<article><h2>' + escapeHtml(l.name || l.email) + ' <small>' + escapeHtml(l.via) + ' · ' + escapeHtml(l.ts) + ' · ' + escapeHtml(l.receiptId || 'legacy-no-receipt') + '</small></h2>'
    + '<p><a href="mailto:' + escapeHtml(l.email) + '">' + escapeHtml(l.email) + '</a>'
    + (l.phone ? ' · <a href="tel:' + escapeHtml(l.phone) + '">' + escapeHtml(l.phone) + '</a>' : '') + '</p>'
    + (l.company ? '<p><b>business:</b> ' + escapeHtml(l.company) + '</p>' : '')
    + (l.websiteUrl ? '<p><b>website:</b> ' + escapeHtml(l.websiteUrl) + '</p>' : '')
    + (l.service || l.package ? '<p><b>offer:</b> ' + escapeHtml(l.service || '—')
      + (l.package ? ' · ' + escapeHtml(l.package) : '') + '</p>' : '')
    + (l.problem ? '<pre>' + escapeHtml(l.problem) + '</pre>' : '')
    + (l.conversationSummary ? '<pre>' + escapeHtml(l.conversationSummary) + '</pre>' : '')
    + (l.budget || l.timeline ? '<p><b>budget:</b> ' + escapeHtml(l.budget || '—') + ' · <b>timeline:</b> ' + escapeHtml(l.timeline || '—') + '</p>' : '')
    + '<p class="src">' + escapeHtml(l.sourcePage || '') + ' ' + escapeHtml(l.utmSource || '') + '</p></article>';

  res.type('html').send('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    + '<meta name="robots" content="noindex"><title>leads (' + leads.length + ')</title>'
    + '<style>body{background:#0b0b0c;color:#e7e7ea;font:15px/1.55 ui-monospace,Menlo,monospace;margin:0;padding:24px}'
    + 'h1{font-size:15px;letter-spacing:.12em;text-transform:uppercase;color:#8a8a93}'
    + 'article{border:1px solid #26262b;border-radius:12px;padding:16px;margin:14px 0;max-width:760px}'
    + 'h2{font-size:16px;margin:0 0 6px}small{color:#8a8a93;font-weight:400}'
    + 'pre{white-space:pre-wrap;background:#141416;padding:12px;border-radius:8px;margin:8px 0}'
    + 'a{color:#a78bfa}.src{color:#6b6b73;font-size:12px}p{margin:6px 0}</style>'
    + '<h1>' + leads.length + ' leads in the current store</h1>'
    + (qaExcludedCount ? '<p>' + qaExcludedCount + ' exact QA quote receipt(s) excluded. Use <code>?includeQaExcluded=1</code> for audit.</p>' : '')
    + (leads.length ? leads.map(card).join('') : '<p>nothing in the configured lead store yet.</p>'));
});

/* ── signed Cal lifecycle webhook ──
   The route does not retain the webhook payload: it may contain attendee PII.
   Only booking UID, a bounded campaign touch, and an authoritative stage are
   extracted after verification. If durable storage was configured but failed,
   a 503 asks Cal to retry the same dedupe key. */
app.post('/api/cal/webhook', async (req, res) => {
  const secret = String(process.env.CAL_WEBHOOK_SECRET || '').trim();
  if (!secret) return res.status(404).send('not enabled');
  if (limited('w:' + (req.ip || 'x'), 300, 10 * 60_000)) return res.status(429).send('rate limited');
  const signature = req.get('x-cal-signature-256');
  if (!verifyCalSignature(req.body, signature, secret)) return res.status(401).send('invalid signature');

  let body;
  try { body = JSON.parse(req.body.toString('utf8')); }
  catch (error) { return res.status(400).send('invalid json'); }
  const mapped = calWebhookRecord(body);
  if (mapped.ignored) return res.sendStatus(204);
  if (mapped.error) return res.status(422).json({ error: mapped.error });

  const result = await recordStage(mapped.record);
  if (result.error) return res.status(422).json({ error: result.error });
  const storage = acquisitionStorageConfig();
  if ((!result.localStored && !result.sink.ok)
      || (storage.durableConfigured && !result.durableStored)
      || (storage.sinkConfigured && !storage.sinkReady)) {
    return res.status(503).send('acquisition storage unavailable');
  }
  res.sendStatus(204);
});

/* Manual CRM progression. Cal can prove booked/cancelled/no-show; only Leon can
   honestly mark attended, qualified, proposal, won or lost. */
app.post('/api/acquisition/stage', async (req, res) => {
  const auth = adminKeyState(req);
  if (auth === 'disabled') return res.status(404).json({ error: 'not enabled' });
  if (auth !== 'authorized') return res.status(401).json({ error: 'unauthorized' });
  if (limited('a:' + (req.ip || 'x'), 120, 10 * 60_000)) return res.status(429).json({ error: 'rate limited' });
  const result = await recordStage({ ...(req.body || {}), source: 'admin' });
  if (result.error) return res.status(400).json({ error: result.error, stages: FUNNEL_STAGES });
  const storage = acquisitionStorageConfig();
  if ((!result.localStored && !result.sink.ok)
      || (storage.durableConfigured && !result.durableStored)
      || (storage.sinkConfigured && !storage.sinkReady)) {
    return res.status(503).json({ error: 'acquisition storage unavailable' });
  }
  res.status(result.duplicate ? 200 : 201).json({
    ok: true,
    duplicate: result.duplicate,
    recordId: result.record.recordId,
    dedupeKey: result.record.dedupeKey,
    durableStored: result.durableStored
  });
});

/* Append-only QA exclusions preserve the original lead/booking evidence while
   keeping an exact synthetic receipt or booking UID out of funnel reporting.
   There is intentionally no delete or unexclude route. */
app.post('/api/acquisition/exclusions', async (req, res) => {
  const auth = adminKeyState(req);
  if (auth === 'disabled') return res.status(404).json({ error: 'not enabled' });
  if (auth !== 'authorized') return res.status(401).json({ error: 'unauthorized' });
  if (limited('x:' + (req.ip || 'x'), 120, 10 * 60_000)) return res.status(429).json({ error: 'rate limited' });
  const request = req.body || {};
  const normalized = normalizeQaExclusion(request);
  if (normalized.error) return res.status(400).json({ error: normalized.error });
  let records;
  try { records = readAllAcquisition({ strict: true }); }
  catch (error) { return res.status(503).json({ error: 'acquisition ledger failed integrity checks' }); }
  const existingExclusions = qaExclusionSets(records);
  if (existingExclusions.errors.length) {
    return res.status(503).json({ error: 'acquisition exclusion ledger failed integrity checks' });
  }
  const target = normalized.record;
  let targetExists;
  try {
    targetExists = target.receiptId
      ? !!findStoredLeadByReceipt(target.receiptId)
      : records.some(record => record && record.kind === 'funnel_stage'
        && record.bookingUid === target.bookingUid);
  } catch (error) {
    return res.status(503).json({ error: 'lead ledger failed integrity checks' });
  }
  if (!targetExists) {
    return res.status(409).json({ error: 'exact synthetic source record was not found' });
  }
  const result = await recordQaExclusion(request);
  if (result.error) return res.status(400).json({ error: result.error });
  const storage = acquisitionStorageConfig();
  if ((!result.localStored && !result.sink.ok)
      || (storage.durableConfigured && !result.durableStored)
      || (storage.sinkConfigured && !storage.sinkReady)) {
    return res.status(503).json({ error: 'acquisition storage unavailable' });
  }
  res.status(result.duplicate ? 200 : 201).json({
    ok: true,
    duplicate: result.duplicate,
    recordId: result.record.recordId,
    dedupeKey: result.record.dedupeKey,
    targetType: result.record.targetType,
    targetId: result.record.targetId,
    durableStored: result.durableStored
  });
});

app.get('/api/acquisition', (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  const auth = adminKeyState(req);
  if (auth === 'disabled') return res.status(404).json({ error: 'not enabled' });
  if (auth !== 'authorized') return res.status(401).json({ error: 'unauthorized' });
  const asked = Math.floor(Number(req.query.limit));
  const recordLimit = Number.isFinite(asked) && asked > 0 ? Math.min(asked, 5000) : 1000;
  let allRecords;
  try { allRecords = readAllAcquisition({ strict: true }); }
  catch (error) { return res.status(503).json({ error: 'acquisition ledger failed integrity checks' }); }
  const records = allRecords.slice(-recordLimit);
  const exclusionRecords = allRecords.filter(record => record && record.kind === 'qa_exclusion');
  const exclusionSets = qaExclusionSets(exclusionRecords);
  if (exclusionSets.errors.length) {
    return res.status(503).json({ error: 'acquisition exclusion ledger failed integrity checks' });
  }
  const exclusionTargetCount = exclusionSets.receiptIds.size + exclusionSets.bookingUids.size;
  const storage = acquisitionStorageConfig();
  const funnel = acquisitionStats(allRecords, exclusionRecords);
  const body = {
    count: records.length,
    ledgerCount: allRecords.length,
    stages: STAGE_DEFINITIONS,
    storage,
    exclusions: {
      count: exclusionRecords.length,
      targetsApplied: exclusionTargetCount,
      receiptIds: [...exclusionSets.receiptIds],
      bookingUids: [...exclusionSets.bookingUids],
      records: exclusionRecords
    },
    funnel,
    records
  };
  if (req.query.format === 'json') return res.json(body);

  const stageRows = FUNNEL_STAGES.map(stage =>
    `<tr><td>${escapeHtml(stage)}</td><td>${funnel.stageCounts[stage]}</td><td>${escapeHtml(STAGE_DEFINITIONS[stage])}</td></tr>`
  ).join('');
  const latestRows = [...funnel.latestByBooking]
    .sort((a, b) => String(b.occurredAt || '').localeCompare(String(a.occurredAt || '')))
    .map(booking => {
      const attribution = booking.attribution || {};
      const source = [attribution.utmSource, attribution.utmMedium, attribution.utmCampaign]
        .filter(Boolean).join(' / ') || 'direct or unavailable';
      const clickIds = ['gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid']
        .filter(field => attribution[field]).join(', ');
      return `<tr><td><code>${escapeHtml(booking.bookingUid)}</code></td><td>${escapeHtml(booking.stage)}</td>`
        + `<td>${escapeHtml(String(booking.occurredAt || '').replace('T', ' ').replace('.000Z', 'Z'))}</td>`
        + `<td>${escapeHtml(source)}${clickIds ? '<small> · ' + escapeHtml(clickIds) + '</small>' : ''}</td></tr>`;
    }).join('') || '<tr><td colspan="4">No authoritative booking stages yet.</td></tr>';
  const exclusionRows = exclusionRecords.map(record => {
    const type = record.receiptId ? 'quote receipt' : 'booking UID';
    const target = record.receiptId || record.bookingUid || '';
    return `<tr><td>${escapeHtml(type)}</td><td><code>${escapeHtml(target)}</code></td>`
      + `<td>${escapeHtml(String(record.occurredAt || record.ts || '').replace('T', ' ').replace('.000Z', 'Z'))}</td></tr>`;
  }).join('') || '<tr><td colspan="3">No QA exclusions recorded.</td></tr>';

  res.type('html').send('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    + '<meta name="robots" content="noindex"><title>acquisition</title>'
    + '<style>body{background:#09090a;color:#eee;font:14px/1.55 ui-monospace,Menlo,monospace;max-width:980px;margin:auto;padding:28px}'
    + 'h1,h2{font-weight:550}h2{margin-top:2rem;color:#a78bfa}p,small{color:#92929c}table{width:100%;border-collapse:collapse}'
    + 'th,td{text-align:left;vertical-align:top;border-bottom:1px solid #242428;padding:.55rem}th{color:#777;font-size:11px;text-transform:uppercase}'
    + 'td:nth-child(2){white-space:nowrap}code{color:#ddd}</style>'
    + `<h1>acquisition — ${funnel.bookingCount} bookings · ${allRecords.length} ledger records</h1>`
    + `<p>storage: ${escapeHtml(storage.state)}. ${exclusionTargetCount} exact QA target(s) configured in ${exclusionRecords.length} append-only exclusion record(s). Raw JSON is available with <code>?format=json</code> through the same header-only authentication.</p>`
    + `<h2>stage counts</h2><table><thead><tr><th>stage</th><th>count</th><th>definition</th></tr></thead><tbody>${stageRows}</tbody></table>`
    + `<h2>current booking stage</h2><table><thead><tr><th>booking UID</th><th>stage</th><th>occurred</th><th>attribution</th></tr></thead><tbody>${latestRows}</tbody></table>`
    + `<h2>QA exclusions</h2><table><thead><tr><th>type</th><th>exact ID</th><th>recorded</th></tr></thead><tbody>${exclusionRows}</tbody></table>`);
});

/* ── event beacon ── */
app.post('/api/event', (req, res) => {
  const ip = req.ip || 'x';
  if (limited('e:' + ip, 120, 10 * 60_000)) return res.sendStatus(204);
  const event = normalizeEvent(req.body || {});
  if (!event) return res.status(400).json({ error: 'invalid event name' });
  persistEvent(event);
  if (event.name === 'calendar_booking_success' && event.bookingUid) {
    recordBookingAttribution(event).catch(error => {
      console.error('booking attribution write failed:', String(error && error.message || error).slice(0, 200));
    });
  }
  res.sendStatus(204);
});

/* ── traffic dashboard — where visitors came from ──
   Same key and storage policy as /api/leads. The default JSONL path can reset;
   LEON_DATA_DIR makes it suitable for a mounted persistent disk. */
app.get('/api/traffic', (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  const auth = adminKeyState(req);
  if (auth === 'disabled') return res.status(404).send('set LEADS_KEY in the environment to enable this view');
  if (auth !== 'authorized') return res.status(401).send('unauthorized');

  const includeQaExcluded = req.query.includeQaExcluded === '1'
    || req.query.includeQaExcluded === 'true';
  let rawEvents;
  try { rawEvents = readEvents(5000, { strict: true }); }
  catch (error) { return res.status(503).json({ error: 'events ledger failed integrity checks' }); }
  let acquisitionRecords;
  try { acquisitionRecords = readAllAcquisition({ strict: true }); }
  catch (error) { return res.status(503).json({ error: 'acquisition ledger failed integrity checks' }); }
  const exclusionRecords = acquisitionRecords.filter(record => record && record.kind === 'qa_exclusion');
  const exclusionSets = qaExclusionSets(exclusionRecords);
  if (exclusionSets.errors.length) {
    return res.status(503).json({ error: 'acquisition exclusion ledger failed integrity checks' });
  }
  const qaEventState = qaEventExclusion(
    rawEvents,
    readLeads(Number.MAX_SAFE_INTEGER, { includeSynthetic: true }),
    acquisitionRecords,
    exclusionRecords
  );
  const excludedQaSessionIds = qaEventState.sessionIds;
  const eventIsQaExcluded = (event, index) => qaEventState.directEventIndexes.has(index)
    || excludedQaSessionIds.has(String(event && event.sessionId || ''));
  const excludedQaEvents = rawEvents.filter(eventIsQaExcluded);
  const qaExcludedEventCount = excludedQaEvents.length;
  const removedQaSessionIds = new Set(excludedQaEvents
    .map(event => String(event && event.sessionId || ''))
    .filter(Boolean));
  const events = includeQaExcluded
    ? rawEvents
    : rawEvents.filter((event, index) => !eventIsQaExcluded(event, index));
  const deviceJourney = deviceJourneyStats(events);
  const reviewMilestones = reviewMilestoneStats(events);
  let searchFunnel;
  try {
    const end = req.query.end || new Date().toISOString().slice(0, 10);
    const defaultStart = new Date(Date.parse(end) - 27 * 86400000);
    const start = req.query.start || (Number.isFinite(defaultStart.getTime()) ? defaultStart.toISOString().slice(0, 10) : '');
    searchFunnel = buildSearchFunnel({ events: rawEvents,
      leads: readLeads(Number.MAX_SAFE_INTEGER, { includeSynthetic: true }),
      acquisition: acquisitionRecords, start, end,
      eventsTruncated: rawEvents.length >= 5000,
      // Retained files do not establish a complete collection window.
      coverageVerified: false });
  } catch (_) { return res.status(400).json({ error: 'invalid search report dates or evidence' }); }
  if (req.query.format === 'json') {
    return res.json({
      count: events.length,
      qaExcludedEventCount,
      qaExcludedSessionCount: removedQaSessionIds.size,
      deviceJourney,
      reviewMilestones,
      searchFunnel,
      webVitals: webVitalsReport(events, searchFunnel.period),
      events
    });
  }

  const count = (map, k) => { if (k) map.set(k, (map.get(k) || 0) + 1); };
  const bySource = new Map(), byLastSource = new Map(), byName = new Map(), byPath = new Map(), byDay = new Map(), byLang = new Map();
  const sessionsSeen = new Set();
  for (const ev of events) {
    if (ev.sessionId) sessionsSeen.add(ev.sessionId);
    count(byName, ev.name);
    count(byDay, String(ev.ts || '').slice(0, 10));
    if (ev.name === 'page_view') {
      count(bySource, sourceOf(ev));
      count(byLastSource, sourceOf(ev, 'last'));
      count(byPath, ev.path || '/');
      // PREFIX, not exact match. This was a lookup keyed on the whole path,
      // which was right when the only translated URLs were /es, /pt and /zh.
      // The moment service and booking pages appeared underneath them —
      // /pt/criar-site, /zh/zaixian-diandan — nine of the twelve language pages
      // started counting as english, and the language table became the exact
      // opposite of the thing it exists to measure.
      const p = ev.path || '/';
      const lang = p.startsWith('/es') ? 'español'
                 : p.startsWith('/pt') ? 'português'
                 : p.startsWith('/zh') ? '中文'
                 : 'english';
      count(byLang, lang);
    }
  }
  const rows = (map) => [...map.entries()].sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `<tr><td>${escapeHtml(k)}</td><td>${escapeHtml(v)}</td></tr>`).join('')
    || '<tr><td colspan="2">nothing yet</td></tr>';
  const funnel = funnelStats(events);
  const stepRate = stage => {
    if (stage.priorQualifiedCount === null) return 'baseline';
    if (!stage.priorQualifiedCount) return '—';
    const percent = (stage.qualifiedCount * 100 / stage.priorQualifiedCount)
      .toFixed(1).replace(/\.0$/, '');
    return `${stage.qualifiedCount}/${stage.priorQualifiedCount} · ${percent}%`;
  };
  const funnelRows = funnel.stages.map(stage =>
    `<tr data-stage="${stage.id}"><td>${escapeHtml(stage.label)}</td><td>${stage.eventCount}</td><td>${stage.sessionCount}</td><td>${escapeHtml(stepRate(stage))}</td></tr>`
  ).join('');
  const deviceRows = deviceJourney.map(row =>
    `<tr><td>${escapeHtml(row.device)}</td><td>${row.pageViews}</td><td>${row.proofViews}</td><td>${row.startViews}</td><td>${row.formStarts}</td><td>${row.leadsAccepted}</td><td>${row.bookings}</td></tr>`
  ).join('');
  const baselineRate = stage => {
    if (!stage.baselineSessionCount) return '—';
    const percent = (stage.attributableCount * 100 / stage.baselineSessionCount)
      .toFixed(1).replace(/\.0$/, '');
    return `${stage.attributableCount}/${stage.baselineSessionCount} · ${percent}%`;
  };
  const milestoneRows = reviewMilestones.stages.map(stage =>
    `<tr data-milestone="${stage.id}"><td>${escapeHtml(stage.label)}</td><td>${stage.eventCount}</td><td>${stage.sessionCount}</td><td>${escapeHtml(baselineRate(stage))}</td></tr>`
  ).join('');
  const recent = events.slice(-40).reverse().map(ev =>
    `<tr><td>${escapeHtml(String(ev.ts || '').slice(5, 16).replace('T', ' '))}</td><td>${escapeHtml(ev.name)}</td><td>${escapeHtml(ev.path || '')}</td><td>${escapeHtml(sourceOf(ev))}</td><td>${escapeHtml([
      ev.receipt ? 'receipt ' + ev.receipt : '',
      ev.bookingUid ? 'booking ' + ev.bookingUid : ''
    ].filter(Boolean).join(' · '))}</td></tr>`).join('');

  res.type('html').send('<!doctype html><meta charset="utf-8">'
    + '<meta name="robots" content="noindex"><meta name="viewport" content="width=device-width,initial-scale=1"><title>traffic</title>'
    + '<style>body{background:#000;color:#fafafa;font:14px/1.6 "JetBrains Mono",monospace;padding:2rem;max-width:880px;margin:auto}'
    + 'h1,h2{font-weight:500} h2{margin:2rem 0 .5rem;color:#9b8cff} table{width:100%;border-collapse:collapse}'
    + 'th,td{border-bottom:1px solid #1a1a1a;padding:.35rem .5rem} th{text-align:left;color:#777;font-size:11px;font-weight:500}'
    + 'td:last-child{text-align:right;color:#aaa}.recent td{text-align:left;color:#aaa;font-size:12px}.note,p{color:#777}.note{font-size:12px}</style>'
    + `<h1>traffic — ${events.length} events · ${sessionsSeen.size} anonymous sessions in the current store</h1>`
    + (qaExcludedEventCount
      ? `<p>${qaExcludedEventCount} event record(s) across ${removedQaSessionIds.size} exact QA session(s) excluded. Use <code>?includeQaExcluded=1</code> for audit.</p>`
      : '')
    + '<p>tag every link you post as ?s=name (e.g. /pt?s=fbgroup-br) and it shows up under sources. use LEON_DATA_DIR for mounted-disk JSONL; "EVT " lines remain in render logs.</p>'
    + '<h2>unique-session funnel</h2>'
    + `<table class="funnel"><thead><tr><th>stage</th><th>event records</th><th>unique sessions*</th><th>step rate†</th></tr></thead><tbody>${funnelRows}</tbody></table>`
    + `<p class="note">* event counts include all records; unique sessions exclude ${funnel.sessionlessEventCount} of ${funnel.funnelEventCount} funnel records with no session ID (including legacy data). † each step-rate numerator includes only session IDs also recorded in every preceding row. Direct calendar bookings remain visible in their row's unique-session total even when no accepted-lead event was recorded for that session.</p>`
    + '<h2>review journey milestones</h2>'
    + `<table class="review-milestones"><thead><tr><th>milestone</th><th>event records</th><th>unique sessions</th><th>rate vs page-view sessions</th></tr></thead><tbody>${milestoneRows}</tbody></table>`
    + '<p class="note">Milestones are independent. A visitor can jump from the hero directly to the form, so a skipped proof or Start view does not erase a later action.</p>'
    + '<h2>device journey</h2>'
    + `<table class="device-journey"><thead><tr><th>viewport</th><th>page views</th><th>proof views</th><th>start views</th><th>form starts</th><th>accepted leads</th><th>bookings</th></tr></thead><tbody>${deviceRows}</tbody></table>`
    + '<p class="note">Event counts by anonymous viewport bucket. Historical events without a bucket are shown as unknown; this is a diagnostic view, not a count of people.</p>'
    + `<h2>page views by first-touch source</h2><table>${rows(bySource)}</table>`
    + `<h2>page views by last-touch source</h2><table>${rows(byLastSource)}</table>`
    + '<p class="note">Known AI-domain referral means the browser supplied that domain as the referrer. It does not prove Leon Builds was cited, mentioned, or recommended in an answer.</p>'
    + `<h2>page views by language page</h2><table>${rows(byLang)}</table>`
    + `<h2>page views by page</h2><table>${rows(byPath)}</table>`
    + `<h2>events</h2><table>${rows(byName)}</table>`
    + `<h2>by day</h2><table>${rows(byDay)}</table>`
    + `<h2>last 40</h2><table class="recent"><thead><tr><th>time</th><th>event</th><th>page</th><th>first source</th><th>correlation</th></tr></thead><tbody>${recent}</tbody></table>`);
});

app.use((req, res) => res.status(404).send('not found'));

if (require.main === module) {
  startLeadEmailOutbox();
  app.listen(PORT, () => {
    console.log(`leon-assist on :${PORT} — model=${client ? MODEL : 'NOT CONFIGURED'} dailyCap=${DAILY_CAP}`);
  });
}

module.exports = { app };
