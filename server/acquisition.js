'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { attributionFromContainers, normalizeAttribution, boundedText } = require('./attribution');
const { dataFile, storageConfig } = require('./storage');

const ACQUISITION_FILE = dataFile('acquisition.jsonl', 'ACQUISITION_FILE');
const ACQUISITION_DIR = path.dirname(ACQUISITION_FILE);

const FUNNEL_STAGES = Object.freeze([
  'booked',
  'attended',
  'qualified',
  'proposal',
  'won',
  'lost',
  'cancelled',
  'no-show'
]);
const FUNNEL_STAGE_SET = new Set(FUNNEL_STAGES);

const STAGE_DEFINITIONS = Object.freeze({
  booked: 'A booking was created. A browser success event alone is not authoritative.',
  attended: 'Leon confirmed the prospect attended; a meeting-end timestamp is not enough.',
  qualified: 'Leon confirmed fit, need, budget and a plausible buying path.',
  proposal: 'A concrete scoped proposal was sent.',
  won: 'The prospect accepted and the engagement became paid work.',
  lost: 'The opportunity ended without a sale.',
  cancelled: 'The booking was cancelled.',
  'no-show': 'Cal reported the attendee as a no-show.'
});

function bookingUid(value) {
  const text = boundedText(value, 160);
  return /^[A-Za-z0-9._~:@+-]{8,160}$/.test(text) ? text : '';
}

function safeIso(value, fallback) {
  if (value) {
    const date = new Date(value);
    if (Number.isFinite(date.getTime())) return date.toISOString();
  }
  return fallback || new Date().toISOString();
}

function safeContext(raw) {
  if (!raw || typeof raw !== 'object') return {};
  const out = {};
  for (const field of ['triggerEvent', 'reason', 'previousBookingUid']) {
    const value = field === 'previousBookingUid'
      ? bookingUid(raw[field])
      : boundedText(raw[field], field === 'reason' ? 240 : 80);
    if (value) out[field] = value;
  }
  const amount = Number(raw.value);
  if (Number.isFinite(amount) && amount >= 0 && amount <= 10_000_000) {
    out.value = Math.round(amount * 100) / 100;
    const currency = boundedText(raw.currency || 'USD', 3).toUpperCase();
    if (/^[A-Z]{3}$/.test(currency)) out.currency = currency;
  }
  return out;
}

function normalizeStageRecord(input, now) {
  if (!input || typeof input !== 'object') return { error: 'record is required' };
  const stage = boundedText(input.stage, 20).toLowerCase();
  if (!FUNNEL_STAGE_SET.has(stage)) return { error: 'invalid funnel stage' };
  const uid = bookingUid(input.bookingUid);
  if (!uid) return { error: 'valid bookingUid is required' };
  const timestamp = safeIso(now);
  const record = {
    schemaVersion: 1,
    recordId: 'acq_' + crypto.randomUUID(),
    ts: timestamp,
    occurredAt: safeIso(input.occurredAt, timestamp),
    kind: 'funnel_stage',
    stage,
    bookingUid: uid,
    source: boundedText(input.source, 40) || 'manual',
    attribution: normalizeAttribution(input.attribution || input),
    context: safeContext(input.context || input),
    dedupeKey: `booking:${uid}:stage:${stage}`
  };
  return { record };
}

let dedupeLoaded = false;
const dedupeKeys = new Set();

function readLines() {
  let raw = '';
  try { raw = fs.readFileSync(ACQUISITION_FILE, 'utf8'); } catch (e) { return []; }
  const out = [];
  for (const line of raw.split('\n')) {
    if (!line.trim()) continue;
    try { out.push(JSON.parse(line)); } catch (e) { /* skip a torn final line */ }
  }
  return out;
}

function loadDedupeKeys() {
  if (dedupeLoaded) return;
  for (const record of readLines()) if (record && record.dedupeKey) dedupeKeys.add(record.dedupeKey);
  dedupeLoaded = true;
}

function appendLocal(record) {
  try {
    fs.mkdirSync(ACQUISITION_DIR, { recursive: true });
    fs.appendFileSync(ACQUISITION_FILE, JSON.stringify(record) + '\n');
    return { ok: true };
  } catch (error) {
    console.error('acquisition file write failed:', record.dedupeKey, error.message);
    return { ok: false, error: String(error.message || error).slice(0, 200) };
  }
}

function sinkSettings(env = process.env) {
  const raw = String(env.ACQUISITION_SINK_URL || '').trim();
  if (!raw) return { configured: false, valid: true, url: null };
  try {
    const url = new URL(raw);
    const loopback = url.hostname === '127.0.0.1' || url.hostname === 'localhost' || url.hostname === '::1';
    const transportValid = url.protocol === 'https:'
      || (url.protocol === 'http:' && loopback && env.NODE_ENV === 'test');
    const authenticated = !!String(env.ACQUISITION_SINK_TOKEN || '').trim()
      || !!String(env.ACQUISITION_SINK_SECRET || '').trim();
    const valid = transportValid && authenticated;
    const error = !transportValid
      ? 'HTTPS is required'
      : !authenticated
        ? 'set ACQUISITION_SINK_TOKEN or ACQUISITION_SINK_SECRET'
        : null;
    return { configured: true, valid, url: valid ? url.href : null, error };
  } catch (e) {
    return { configured: true, valid: false, url: null, error: 'invalid URL' };
  }
}

function acquisitionStorageConfig(env = process.env) {
  const local = storageConfig(env);
  const sink = sinkSettings(env);
  const sinkReady = sink.configured && sink.valid;
  let state = 'ephemeral-only';
  if (sink.configured && !sink.valid) state = 'invalid-sink-configuration';
  else if (local.localDurableConfigured || sinkReady) state = 'durable-configured';
  return {
    state,
    durableConfigured: local.localDurableConfigured || sinkReady,
    localMode: local.localMode,
    localDurableConfigured: local.localDurableConfigured,
    sinkConfigured: sink.configured,
    sinkReady
  };
}

async function deliverToSink(record, env = process.env) {
  const settings = sinkSettings(env);
  if (!settings.configured) return { attempted: false, ok: false };
  if (!settings.valid) return { attempted: true, ok: false, error: settings.error || 'invalid sink configuration' };

  const body = JSON.stringify(record);
  const headers = {
    'content-type': 'application/json',
    'x-leon-event-id': record.recordId,
    'x-leon-dedupe-key': record.dedupeKey
  };
  const token = String(env.ACQUISITION_SINK_TOKEN || '').trim();
  if (token) headers.authorization = `Bearer ${token}`;
  const secret = String(env.ACQUISITION_SINK_SECRET || '').trim();
  if (secret) {
    headers['x-leon-signature-256'] = 'sha256=' + crypto
      .createHmac('sha256', secret)
      .update(body)
      .digest('hex');
  }

  try {
    const response = await fetch(settings.url, {
      method: 'POST',
      headers,
      body,
      signal: AbortSignal.timeout(5000)
    });
    if (!response.ok) {
      const responseBody = await response.text().catch(() => '');
      return { attempted: true, ok: false, error: `HTTP ${response.status}: ${responseBody.slice(0, 120)}` };
    }
    return { attempted: true, ok: true };
  } catch (error) {
    return { attempted: true, ok: false, error: String(error.message || error).slice(0, 200) };
  }
}

async function persistRecord(record, env = process.env) {
  loadDedupeKeys();
  const duplicate = dedupeKeys.has(record.dedupeKey);
  let local = { ok: true, duplicate };
  if (!duplicate) {
    local = appendLocal(record);
    if (local.ok) {
      dedupeKeys.add(record.dedupeKey);
      console.log('ACQ ' + JSON.stringify(record));
    }
  }

  // A retry resends the same dedupe key so a failed remote delivery can recover;
  // the receiver must make that key unique. The local JSONL row remains single.
  const sink = await deliverToSink(record, env);
  if (sink.attempted && !sink.ok) {
    console.error('ACQUISITION_SINK_FAILED dedupeKey=' + record.dedupeKey, sink.error || 'unknown error');
  }
  const config = acquisitionStorageConfig(env);
  const durableStored = (local.ok && config.localDurableConfigured) || sink.ok;
  return {
    record,
    duplicate,
    localStored: local.ok,
    durableStored,
    sink
  };
}

async function recordStage(input, env = process.env) {
  const normalized = normalizeStageRecord(input);
  if (normalized.error) return normalized;
  return persistRecord(normalized.record, env);
}

function eventAttribution(input, touch) {
  const prefix = touch === 'first' ? 'first' : 'last';
  const title = field => field.charAt(0).toUpperCase() + field.slice(1);
  const raw = {
    utmSource: input[prefix + 'Utm'] || input[prefix + 'UtmSource'],
    utmMedium: input[prefix + 'Medium'] || input[prefix + 'UtmMedium'],
    utmCampaign: input[prefix + 'Campaign'] || input[prefix + 'UtmCampaign'],
    utmTerm: input[prefix + 'UtmTerm'],
    utmContent: input[prefix + 'UtmContent']
  };
  for (const field of ['gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid']) {
    raw[field] = input[prefix + title(field)];
  }
  return normalizeAttribution(raw);
}

/* The embed success event links the browser's bounded campaign touch to Cal's
   opaque booking UID. This record is explicitly non-authoritative: it enriches
   attribution but never creates or advances a funnel stage. */
async function recordBookingAttribution(input, env = process.env) {
  if (!input || typeof input !== 'object') return { error: 'event is required' };
  const uid = bookingUid(input.bookingUid);
  if (!uid) return { error: 'valid bookingUid is required' };
  const firstAttribution = eventAttribution(input, 'first');
  const lastAttribution = eventAttribution(input, 'last');
  if (!Object.keys(firstAttribution).length && !Object.keys(lastAttribution).length) {
    return { ignored: true, reason: 'event has no campaign attribution' };
  }
  const fingerprint = crypto.createHash('sha256')
    .update(JSON.stringify({ firstAttribution, lastAttribution }))
    .digest('hex')
    .slice(0, 24);
  const timestamp = safeIso(input.ts);
  const record = {
    schemaVersion: 1,
    recordId: 'acq_' + crypto.randomUUID(),
    ts: timestamp,
    occurredAt: timestamp,
    kind: 'booking_attribution',
    bookingUid: uid,
    source: 'browser-event',
    authoritative: false,
    firstAttribution,
    lastAttribution,
    dedupeKey: `booking:${uid}:attribution:${fingerprint}`
  };
  return persistRecord(record, env);
}

function readAcquisition(limit) {
  const records = readLines();
  const asked = Number(limit);
  return records.slice(-(Number.isFinite(asked) && asked > 0 ? asked : 1000));
}

function acquisitionStats(records) {
  const stageCounts = Object.fromEntries(FUNNEL_STAGES.map(stage => [stage, 0]));
  const latestByBooking = new Map();
  const touchesByBooking = new Map();
  for (const record of records || []) {
    if (!record) continue;
    if (record.kind === 'booking_attribution' && record.bookingUid) {
      const touches = touchesByBooking.get(record.bookingUid) || { first: {}, last: {} };
      touches.first = { ...touches.first, ...(record.firstAttribution || {}) };
      touches.last = { ...touches.last, ...(record.lastAttribution || {}) };
      touchesByBooking.set(record.bookingUid, touches);
      const current = latestByBooking.get(record.bookingUid);
      if (current) {
        current.firstAttribution = { ...current.firstAttribution, ...touches.first };
        current.lastAttribution = { ...current.lastAttribution, ...touches.last };
        // Signed Cal fields already present on the stage win; browser fields fill
        // gaps such as ad click IDs that Cal intentionally does not receive.
        current.attribution = { ...touches.last, ...current.attribution };
        current.browserAttributionObserved = true;
      }
      continue;
    }
    if (record.kind !== 'funnel_stage' || !FUNNEL_STAGE_SET.has(record.stage)) continue;
    stageCounts[record.stage] += 1;
    const previous = latestByBooking.get(record.bookingUid);
    const touches = touchesByBooking.get(record.bookingUid) || { first: {}, last: {} };
    latestByBooking.set(record.bookingUid, {
      bookingUid: record.bookingUid,
      stage: record.stage,
      occurredAt: record.occurredAt,
      attribution: {
        ...touches.last,
        ...((previous && previous.attribution) || {}),
        ...(record.attribution || {})
      },
      firstAttribution: { ...((previous && previous.firstAttribution) || {}), ...touches.first },
      lastAttribution: { ...((previous && previous.lastAttribution) || {}), ...touches.last },
      browserAttributionObserved: !!(previous && previous.browserAttributionObserved)
        || !!Object.keys(touches.first).length
        || !!Object.keys(touches.last).length
    });
  }
  return { stageCounts, bookingCount: latestByBooking.size, latestByBooking: [...latestByBooking.values()] };
}

function verifyCalSignature(rawBody, header, secret) {
  if (!Buffer.isBuffer(rawBody) || !rawBody.length || !secret || !header) return false;
  const supplied = String(header).trim().replace(/^sha256=/i, '').toLowerCase();
  if (!/^[a-f0-9]{64}$/.test(supplied)) return false;
  const expected = crypto.createHmac('sha256', secret).update(rawBody).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(supplied, 'hex'), Buffer.from(expected, 'hex'));
}

function firstCandidate(values) {
  for (const value of values) if (value != null && String(value).trim()) return value;
  return '';
}

function calWebhookRecord(body) {
  if (!body || typeof body !== 'object') return { ignored: true, reason: 'invalid payload' };
  const payload = body.payload && typeof body.payload === 'object' ? body.payload : body;
  const booking = payload.booking && typeof payload.booking === 'object' ? payload.booking : payload;
  const triggerEvent = boundedText(firstCandidate([body.triggerEvent, body.event, body.type]), 80).toUpperCase();
  let stage = '';
  if (triggerEvent === 'BOOKING_CREATED' || triggerEvent === 'BOOKING_RESCHEDULED') stage = 'booked';
  else if (triggerEvent === 'BOOKING_CANCELLED') stage = 'cancelled';
  else if (triggerEvent === 'BOOKING_NO_SHOW_UPDATED') {
    const attendees = Array.isArray(payload.attendees) ? payload.attendees
      : Array.isArray(booking.attendees) ? booking.attendees
      : [];
    if (payload.noShow === true || booking.noShow === true || attendees.some(attendee => attendee && attendee.noShow === true)) {
      stage = 'no-show';
    }
  }
  // MEETING_ENDED is deliberately ignored: a scheduled meeting ending does not
  // prove the prospect attended. Leon records attended/qualified/etc. manually.
  if (!stage) return { ignored: true, reason: 'event does not map to an authoritative stage' };

  const uid = bookingUid(firstCandidate([
    payload.uid,
    payload.bookingUid,
    booking.uid,
    booking.bookingUid,
    body.uid,
    body.bookingUid
  ]));
  if (!uid) return { error: 'webhook is missing a valid booking UID' };

  const attribution = attributionFromContainers([
    payload,
    payload.metadata,
    payload.responses,
    booking,
    booking.metadata,
    booking.responses,
    body.metadata
  ]);
  return {
    record: {
      stage,
      bookingUid: uid,
      source: 'cal-webhook',
      occurredAt: firstCandidate([body.createdAt, payload.updatedAt, payload.createdAt]),
      attribution,
      context: {
        triggerEvent,
        previousBookingUid: firstCandidate([
          payload.rescheduleUid,
          payload.previousBookingUid,
          payload.rescheduledFromUid,
          booking.previousBookingUid
        ])
      }
    }
  };
}

module.exports = {
  FUNNEL_STAGES,
  STAGE_DEFINITIONS,
  acquisitionStorageConfig,
  acquisitionStats,
  bookingUid,
  calWebhookRecord,
  deliverToSink,
  normalizeStageRecord,
  readAcquisition,
  recordBookingAttribution,
  recordStage,
  verifyCalSignature
};
