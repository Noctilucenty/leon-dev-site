/* Traffic events: where visitors come from and what they do.
   Same storage philosophy as leads.js — stdout is the sink that always works
   (grep "EVT " in Render logs). JSONL is replaceable by default and becomes
   durable when LEON_DATA_DIR points inside a mounted disk. */

'use strict';

const fs = require('fs');
const path = require('path');
const { normalizeAttribution } = require('./attribution');
const { dataFile } = require('./storage');

// EVENTS_FILE keeps tests isolated. LEON_DATA_DIR is the production switch for
// putting this file on a mounted disk rather than Render's replaceable app FS.
const EVENTS_FILE = dataFile('events.jsonl', 'EVENTS_FILE');
const DATA_DIR = path.dirname(EVENTS_FILE);

// Event names become dashboard labels and log keys. Keep the vocabulary small
// and machine-readable; values such as `fixcard_ai-chatbots` are intentionally
// allowed, while markup, whitespace and control characters are not.
const EVENT_NAME_RE = /^[a-z][a-z0-9_-]{0,47}$/;

function validEventName(value) {
  return typeof value === 'string' && EVENT_NAME_RE.test(value);
}

function eventText(value, max) {
  if (value == null) return '';
  return String(value)
    .replace(/[\u0000-\u001f\u007f]/g, ' ')
    .trim()
    .slice(0, max);
}

function firstPresent(raw, names, max) {
  for (const name of names) {
    const value = eventText(raw[name], max);
    if (value) return value;
  }
  return '';
}

function anonymousSession(raw) {
  const value = firstPresent(raw, ['sessionId', 'session'], 96);
  return /^[A-Za-z0-9_-]{8,96}$/.test(value) ? value : '';
}

function referrerOrigin(value) {
  const raw = eventText(value, 500);
  if (!raw) return '';
  try {
    const url = new URL(raw);
    // The source report needs a domain, not a referrer's path/query, which can
    // contain search terms or identifiers the visitor never meant to submit.
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.origin : '';
  } catch (e) {
    return '';
  }
}

function firstReferrer(raw, names) {
  for (const name of names) {
    const value = referrerOrigin(raw[name]);
    if (value) return value;
  }
  return '';
}

/* Normalize the public beacon into a bounded analytics record with no contact
   fields. The legacy ref/utm fields remain so old log tooling keeps working;
   explicit first and last fields stop campaign re-entry from overwriting
   acquisition. */
function normalizeEvent(raw, now) {
  if (!raw || typeof raw !== 'object' || !validEventName(raw.name)) return null;

  const currentAttribution = normalizeAttribution(raw);
  const firstAttribution = normalizeAttribution(raw, 'first');
  const lastAttribution = normalizeAttribution(raw, 'last');
  const pathNow = eventText(raw.path, 200);
  const legacyRef = referrerOrigin(raw.ref);
  const legacyUtm = eventText(raw.utm, 120);
  const legacyMedium = eventText(raw.medium, 120);
  const legacyCampaign = eventText(raw.campaign, 120);
  const out = {
    ts: now || new Date().toISOString(),
    name: raw.name,
    path: pathNow,
    sessionId: anonymousSession(raw),
    firstPage: firstPresent(raw, ['firstPage'], 200),
    lastPage: firstPresent(raw, ['lastPage'], 200) || pathNow,
    firstRef: firstReferrer(raw, ['firstRef', 'firstReferrer']) || legacyRef,
    lastRef: firstReferrer(raw, ['lastRef', 'lastReferrer']) || legacyRef,
    firstUtm: firstPresent(raw, ['firstUtm', 'firstUtmSource'], 120) || legacyUtm,
    lastUtm: firstPresent(raw, ['lastUtm', 'lastUtmSource'], 120) || legacyUtm,
    firstMedium: firstPresent(raw, ['firstMedium', 'firstUtmMedium'], 120) || legacyMedium,
    lastMedium: firstPresent(raw, ['lastMedium', 'lastUtmMedium'], 120) || legacyMedium,
    firstCampaign: firstPresent(raw, ['firstCampaign', 'firstUtmCampaign'], 120) || legacyCampaign,
    lastCampaign: firstPresent(raw, ['lastCampaign', 'lastUtmCampaign'], 120) || legacyCampaign,
    firstUtmTerm: firstAttribution.utmTerm || currentAttribution.utmTerm || '',
    lastUtmTerm: lastAttribution.utmTerm || currentAttribution.utmTerm || '',
    firstUtmContent: firstAttribution.utmContent || currentAttribution.utmContent || '',
    lastUtmContent: lastAttribution.utmContent || currentAttribution.utmContent || '',
    // Backward-compatible fields used by existing Render-log searches.
    ref: legacyRef,
    utm: legacyUtm,
    medium: legacyMedium,
    campaign: legacyCampaign,
    term: currentAttribution.utmTerm || '',
    content: currentAttribution.utmContent || ''
  };

  for (const field of ['gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid']) {
    const title = field.charAt(0).toUpperCase() + field.slice(1);
    out[field] = currentAttribution[field] || '';
    out['first' + title] = firstAttribution[field] || currentAttribution[field] || '';
    out['last' + title] = lastAttribution[field] || currentAttribution[field] || '';
  }

  // These are opaque correlation values, never contact details.
  for (const field of ['receipt', 'bookingUid', 'status']) {
    const value = eventText(raw[field], 120);
    if (value) out[field] = value;
  }
  return out;
}

function persistEvent(ev) {
  console.log('EVT ' + JSON.stringify(ev));
  try {
    fs.mkdirSync(DATA_DIR, { recursive: true });
    fs.appendFileSync(EVENTS_FILE, JSON.stringify(ev) + '\n');
  } catch (e) { /* file is best-effort; stdout already has it */ }
}

function readEvents(limit) {
  let raw = '';
  try { raw = fs.readFileSync(EVENTS_FILE, 'utf8'); } catch (e) { return []; }
  const out = [];
  for (const line of raw.split('\n')) {
    if (!line.trim()) continue;
    try { out.push(JSON.parse(line)); } catch (e) { /* skip a torn line */ }
  }
  return out.slice(-(limit || 5000));
}

/* One event -> which bucket it counts toward on the dashboard.
   Priority: explicit tag (?s= or utm_source) > referrer domain > direct.
   Acquisition is the default; pass "last" for the latest campaign touch. */
function sourceOf(ev, touch) {
  const last = touch === 'last';
  const utm = last ? (ev.lastUtm || ev.utm) : (ev.firstUtm || ev.utm);
  const ref = last ? (ev.lastRef || ev.ref) : (ev.firstRef || ev.ref);
  if (utm) return String(utm);
  if (ref) {
    try {
      const h = new URL(ref).hostname.replace(/^www\./, '');
      if (h && !h.includes('leonbuilds') && !h.includes('leonkelvinli')) return h;
      return 'internal';
    } catch (e) { return 'unknown-ref'; }
  }
  return 'direct';
}

const HIGH_INTENT_NAMES = new Set([
  'nav_quote_click', 'hero_quote_click', 'hero_call_click', 'pricing_cta_click',
  'nav_call_click', 'cta_call_click', 'contact_call_click', 'contact_quote_click',
  'about_quote_click', 'work_quote_click', 'work_final_quote_click',
  'reviews_quote_click', 'footer_email_click', 'footer_phone_click',
  'quote_form_start', 'quote_form_submit', 'quote_submit_attempt',
  'chat_first_message', 'lead_submit', 'lead_submit_attempt',
  'quote_to_calendar', 'lead_booking_click',
  'calendar_direct_fallback', 'calendar_email_fallback', 'calendar_phone_fallback',
  'quote_manual_email', 'lead_email_fallback', 'email_click', 'phone_click'
]);

function isHighIntent(name) {
  return HIGH_INTENT_NAMES.has(name)
    || /^(wa_click_|wechat_copy_|contact_click_|call_click_|handoff_)/.test(name);
}

/* Counts keep every matching record, including the legacy records written
   before session IDs existed. Unique-session rates are intentionally stricter:
   a rate numerator includes only IDs also seen in every preceding stage. */
function funnelStats(events) {
  const definitions = [
    { id: 'page', label: 'page view', match: name => name === 'page_view' },
    { id: 'intent', label: 'high-intent action', match: isHighIntent },
    {
      id: 'lead',
      label: 'lead accepted by API',
      match: name => name === 'lead_submit_success'
        || name === 'quote_lead_accepted'
        || name === 'call_request_sent'
    },
    {
      id: 'booking',
      label: 'calendar booking confirmed',
      match: name => name === 'calendar_booking_success'
    }
  ];

  let priorQualified = null;
  const stages = definitions.map(definition => {
    const matching = events.filter(ev => definition.match(String(ev.name || '')));
    const sessions = new Set(
      matching.map(ev => String(ev.sessionId || '')).filter(Boolean)
    );
    const qualified = priorQualified === null
      ? new Set(sessions)
      : new Set([...sessions].filter(session => priorQualified.has(session)));
    const stage = {
      id: definition.id,
      label: definition.label,
      eventCount: matching.length,
      sessionCount: sessions.size,
      sessionlessEventCount: matching.filter(ev => !ev.sessionId).length,
      qualifiedCount: qualified.size,
      priorQualifiedCount: priorQualified === null ? null : priorQualified.size
    };
    priorQualified = qualified;
    return stage;
  });

  return {
    stages,
    sessionlessEventCount: stages.reduce((sum, stage) => sum + stage.sessionlessEventCount, 0),
    funnelEventCount: stages.reduce((sum, stage) => sum + stage.eventCount, 0)
  };
}

module.exports = {
  persistEvent,
  readEvents,
  sourceOf,
  normalizeEvent,
  validEventName,
  funnelStats
};
