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
const RECEIPT_ID_RE = /^lead_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const BOOKING_UID_RE = /^[A-Za-z0-9._~:@+-]{8,160}$/;

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
  return BOOKING_UID_RE.test(text) ? text : '';
}

function receiptId(value) {
  return typeof value === 'string' && value === value.trim() && RECEIPT_ID_RE.test(value)
    ? value
    : '';
}

function exactBookingUid(value) {
  return typeof value === 'string' && value === value.trim() && BOOKING_UID_RE.test(value)
    ? value
    : '';
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

/* QA verification records are never deleted from the operational ledgers. An
   authenticated exclusion appends one opaque identifier here instead, so the
   original lead or booking remains auditable while reports stop treating it as
   a real inquiry or opportunity. Exactly one target is allowed per record. */
function normalizeQaExclusion(input, now) {
  if (!input || typeof input !== 'object') return { error: 'exclusion is required' };
  if (input.confirmSynthetic !== true) {
    return { error: 'confirmSynthetic must be true' };
  }
  const hasReceipt = Object.prototype.hasOwnProperty.call(input, 'receiptId');
  const hasBooking = Object.prototype.hasOwnProperty.call(input, 'bookingUid');
  if (hasReceipt === hasBooking) return { error: 'provide exactly one receiptId or bookingUid' };
  const receipt = hasReceipt ? receiptId(input.receiptId) : '';
  const uid = hasBooking ? exactBookingUid(input.bookingUid) : '';
  if (hasReceipt && !receipt) return { error: 'receiptId must be an exact lead UUID' };
  if (hasBooking && !uid) return { error: 'bookingUid must be an exact 8-160 character Cal identifier' };
  const timestamp = safeIso(now);
  const targetType = receipt ? 'receipt' : 'booking';
  const targetId = receipt || uid;
  const record = {
    schemaVersion: 1,
    recordId: 'acq_' + crypto.randomUUID(),
    ts: timestamp,
    occurredAt: timestamp,
    kind: 'qa_exclusion',
    source: 'admin',
    purpose: 'synthetic-verification',
    targetType,
    targetId,
    ...(receipt ? { receiptId: receipt } : { bookingUid: uid }),
    dedupeKey: `qa-exclusion:${targetType}:${targetId}`
  };
  return { record };
}

let dedupeLoaded = false;
const dedupeRecords = new Map();

function readLines({ strict = false } = {}) {
  let raw = '';
  try { raw = fs.readFileSync(ACQUISITION_FILE, 'utf8'); }
  catch (error) {
    if (strict && (!error || error.code !== 'ENOENT')) throw error;
    return [];
  }
  const out = [];
  const lines = raw.split('\n');
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (!line.trim()) continue;
    try { out.push(JSON.parse(line)); }
    catch (error) {
      if (strict) throw new Error(`corrupt acquisition ledger at line ${index + 1}`);
      /* Best-effort ingestion paths skip a torn line; admin reporting is strict. */
    }
  }
  return out;
}

function loadDedupeRecords() {
  if (dedupeLoaded) return;
  for (const record of readLines()) {
    if (!record || !record.dedupeKey || dedupeRecords.has(record.dedupeKey)) continue;
    if (record.kind === 'qa_exclusion' && qaExclusionSets([record]).errors.length) continue;
    dedupeRecords.set(record.dedupeKey, record);
  }
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
  loadDedupeRecords();
  const existing = dedupeRecords.get(record.dedupeKey);
  const duplicate = !!existing;
  const canonicalRecord = existing || record;
  let local = { ok: true, duplicate };
  if (!duplicate) {
    local = appendLocal(record);
    if (local.ok) {
      dedupeRecords.set(record.dedupeKey, record);
      console.log('ACQ ' + JSON.stringify(record));
    }
  }

  // A retry resends the same dedupe key so a failed remote delivery can recover;
  // the receiver must make that key unique. The local JSONL row remains single.
  const sink = await deliverToSink(canonicalRecord, env);
  if (sink.attempted && !sink.ok) {
    console.error('ACQUISITION_SINK_FAILED dedupeKey=' + canonicalRecord.dedupeKey, sink.error || 'unknown error');
  }
  if (!duplicate && !dedupeRecords.has(record.dedupeKey) && sink.ok) {
    dedupeRecords.set(record.dedupeKey, record);
  }
  const config = acquisitionStorageConfig(env);
  const durableStored = (local.ok && config.localDurableConfigured) || sink.ok;
  return {
    record: canonicalRecord,
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

async function recordQaExclusion(input, env = process.env) {
  const normalized = normalizeQaExclusion(input);
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
  const records = readAllAcquisition();
  const asked = Number(limit);
  return records.slice(-(Number.isFinite(asked) && asked > 0 ? asked : 1000));
}

function readAllAcquisition(options) {
  return readLines(options);
}

function qaExclusionSets(records) {
  const receiptIds = new Set();
  const bookingUids = new Set();
  const errors = [];
  for (let index = 0; index < (records || []).length; index += 1) {
    const record = records[index];
    if (!record || record.kind !== 'qa_exclusion') continue;
    const hasReceipt = Object.prototype.hasOwnProperty.call(record, 'receiptId');
    const hasBooking = Object.prototype.hasOwnProperty.call(record, 'bookingUid');
    const receipt = hasReceipt ? receiptId(record.receiptId) : '';
    const uid = hasBooking ? exactBookingUid(record.bookingUid) : '';
    const expectedType = hasReceipt && !hasBooking && receipt
      ? 'receipt'
      : hasBooking && !hasReceipt && uid ? 'booking' : '';
    const expectedId = receipt || uid;
    if (!expectedType
        || (record.targetType != null && record.targetType !== expectedType)
        || (record.targetId != null && record.targetId !== expectedId)
        || record.dedupeKey !== `qa-exclusion:${expectedType}:${expectedId}`) {
      errors.push(`invalid QA exclusion record at ledger index ${index + 1}`);
      continue;
    }
    if (receipt) receiptIds.add(receipt);
    else bookingUids.add(uid);
  }
  return { receiptIds, bookingUids, errors };
}

function qaEventExclusion(events, leads, records, exclusionRecords = records) {
  const exclusions = qaExclusionSets(exclusionRecords);
  const replacementByUid = new Map();
  for (const record of records || []) {
    if (!record || record.kind !== 'funnel_stage' || !record.bookingUid) continue;
    const previousUid = bookingUid(record.context && record.context.previousBookingUid);
    if (previousUid && previousUid !== record.bookingUid) {
      replacementByUid.set(previousUid, record.bookingUid);
    }
  }
  const canonicalUid = uid => {
    let current = uid;
    const seen = new Set();
    while (replacementByUid.has(current) && !seen.has(current)) {
      seen.add(current);
      current = replacementByUid.get(current);
    }
    return current;
  };
  const excludedCanonicalUids = new Set(
    [...exclusions.bookingUids].map(uid => canonicalUid(uid))
  );
  const bookingIsExcluded = uid => {
    const raw = exactBookingUid(uid);
    return !!raw && (exclusions.bookingUids.has(raw)
      || excludedCanonicalUids.has(canonicalUid(raw)));
  };
  const sessionIds = new Set();
  for (const lead of leads || []) {
    if (!lead || !exclusions.receiptIds.has(receiptId(lead.receiptId))) continue;
    const sessionId = boundedText(lead.analyticsSessionId, 96);
    if (sessionId) sessionIds.add(sessionId);
  }
  const directEventIndexes = new Set();
  for (let index = 0; index < (events || []).length; index += 1) {
    const event = events[index];
    if (!event) continue;
    const excludedReceipt = exclusions.receiptIds.has(receiptId(event.receipt));
    if (!excludedReceipt && !bookingIsExcluded(event.bookingUid)) continue;
    directEventIndexes.add(index);
    const sessionId = boundedText(event.sessionId, 96);
    if (sessionId) sessionIds.add(sessionId);
  }
  return { sessionIds, directEventIndexes };
}

function acquisitionStats(records, exclusionRecords = records) {
  const exclusions = qaExclusionSets(exclusionRecords);
  const stageCounts = Object.fromEntries(FUNNEL_STAGES.map(stage => [stage, 0]));
  const replacementByUid = new Map();
  for (const record of records || []) {
    if (!record || record.kind !== 'funnel_stage' || !record.bookingUid) continue;
    const previousUid = bookingUid(record.context && record.context.previousBookingUid);
    if (previousUid && previousUid !== record.bookingUid) replacementByUid.set(previousUid, record.bookingUid);
  }
  const canonicalUid = uid => {
    let current = uid;
    const seen = new Set();
    while (replacementByUid.has(current) && !seen.has(current)) {
      seen.add(current);
      current = replacementByUid.get(current);
    }
    return current;
  };
  const excludedCanonicalUids = new Set(
    [...exclusions.bookingUids].map(uid => canonicalUid(uid))
  );
  const bookingIsExcluded = uid => {
    const raw = bookingUid(uid);
    return !!raw && (exclusions.bookingUids.has(raw) || excludedCanonicalUids.has(canonicalUid(raw)));
  };
  const latestByBooking = new Map();
  const touchesByBooking = new Map();
  const countedStages = new Set();
  let excludedRecordCount = 0;
  for (const record of records || []) {
    if (!record || record.kind !== 'booking_attribution' || !record.bookingUid) continue;
    if (bookingIsExcluded(record.bookingUid)) {
      excludedRecordCount += 1;
      continue;
    }
    const uid = canonicalUid(record.bookingUid);
    const touches = touchesByBooking.get(uid) || { first: {}, last: {} };
    touches.first = { ...touches.first, ...(record.firstAttribution || {}) };
    touches.last = { ...touches.last, ...(record.lastAttribution || {}) };
    touchesByBooking.set(uid, touches);
  }
  for (const record of records || []) {
    if (!record) continue;
    if (record.kind === 'booking_attribution') continue;
    if (record.kind !== 'funnel_stage' || !FUNNEL_STAGE_SET.has(record.stage)) continue;
    if (bookingIsExcluded(record.bookingUid)) {
      excludedRecordCount += 1;
      continue;
    }
    // Cal may emit a cancellation for the old slot as part of a reschedule.
    // Once that UID is explicitly superseded, the old-slot cancellation is
    // transport history, not a cancelled sales opportunity.
    if (record.stage === 'cancelled' && replacementByUid.has(record.bookingUid)) continue;
    const uid = canonicalUid(record.bookingUid);
    const stageKey = `${uid}:${record.stage}`;
    if (!countedStages.has(stageKey)) {
      countedStages.add(stageKey);
      stageCounts[record.stage] += 1;
    }
    const previous = latestByBooking.get(uid);
    const touches = touchesByBooking.get(uid) || { first: {}, last: {} };
    latestByBooking.set(uid, {
      bookingUid: uid,
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
  return {
    stageCounts,
    bookingCount: latestByBooking.size,
    latestByBooking: [...latestByBooking.values()],
    qaExclusions: {
      bookingUidsConfigured: exclusions.bookingUids.size,
      recordsExcluded: excludedRecordCount
    }
  };
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
  normalizeQaExclusion,
  qaEventExclusion,
  qaExclusionSets,
  readAcquisition,
  readAllAcquisition,
  recordBookingAttribution,
  recordQaExclusion,
  recordStage,
  verifyCalSignature
};
