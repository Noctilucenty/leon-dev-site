'use strict';

const UTM_FIELDS = Object.freeze([
  ['utmSource', 'utm_source'],
  ['utmMedium', 'utm_medium'],
  ['utmCampaign', 'utm_campaign'],
  ['utmTerm', 'utm_term'],
  ['utmContent', 'utm_content']
]);

const CLICK_ID_FIELDS = Object.freeze([
  ['gclid', 'gclid'],
  ['gbraid', 'gbraid'],
  ['wbraid', 'wbraid'],
  ['fbclid', 'fbclid'],
  ['msclkid', 'msclkid']
]);

const ATTRIBUTION_FIELDS = Object.freeze([...UTM_FIELDS, ...CLICK_ID_FIELDS]);
const CLICK_ID_NAMES = new Set(CLICK_ID_FIELDS.map(([camel]) => camel));

function boundedText(value, max) {
  if (value == null) return '';
  return String(value)
    .replace(/[\u0000-\u001f\u007f]/g, ' ')
    .trim()
    .slice(0, max);
}

/* Ad click IDs are opaque tokens. Reject unexpected punctuation rather than
   turning arbitrary public input into something that looks like a real ID. */
function attributionValue(field, value) {
  const text = boundedText(value, CLICK_ID_NAMES.has(field) ? 256 : 160);
  if (!text) return '';
  if (CLICK_ID_NAMES.has(field) && !/^[A-Za-z0-9._~:+-]+$/.test(text)) return '';
  return text;
}

function cap(name) {
  return name.charAt(0).toUpperCase() + name.slice(1);
}

function firstValue(raw, names) {
  for (const name of names) {
    if (!Object.prototype.hasOwnProperty.call(raw, name)) continue;
    const value = raw[name];
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      if (Object.prototype.hasOwnProperty.call(value, 'value')) return value.value;
      continue;
    }
    if (Array.isArray(value)) continue;
    return value;
  }
  return '';
}

/* Accept the camelCase browser schema plus snake_case fields emitted by Cal.
   `prefix` is `first` or `last` for first-/last-touch records. */
function normalizeAttribution(raw, prefix = '') {
  if (!raw || typeof raw !== 'object') return {};
  const out = {};
  for (const [camel, snake] of ATTRIBUTION_FIELDS) {
    const prefixed = prefix ? prefix + cap(camel) : camel;
    const snakePrefixed = prefix ? prefix + '_' + snake : snake;
    const value = attributionValue(camel, firstValue(raw, [prefixed, snakePrefixed]));
    if (value) out[camel] = value;
  }
  return out;
}

/* Webhook providers can place campaign values in one of a few documented
   containers. Search only those containers; never recursively sweep a payload
   that may contain attendee names, answers or notes. */
function attributionFromContainers(containers) {
  const out = {};
  for (const [camel, snake] of ATTRIBUTION_FIELDS) {
    for (const container of containers) {
      if (!container || typeof container !== 'object') continue;
      const value = attributionValue(camel, firstValue(container, [camel, snake]));
      if (value) {
        out[camel] = value;
        break;
      }
    }
  }
  return out;
}

module.exports = {
  UTM_FIELDS,
  CLICK_ID_FIELDS,
  ATTRIBUTION_FIELDS,
  boundedText,
  attributionValue,
  normalizeAttribution,
  attributionFromContainers
};
