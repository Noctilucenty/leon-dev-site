/* Traffic events: where visitors come from and what they do.
   Same storage philosophy as leads.js — stdout is the sink that always
   works (grep "EVT " in Render logs), the jsonl file is the convenient
   one and resets on every deploy. Backs GET /api/traffic. */

'use strict';

const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'data');
const EVENTS_FILE = path.join(DATA_DIR, 'events.jsonl');

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
   Priority: explicit tag (?s= or utm_source) > referrer domain > direct. */
function sourceOf(ev) {
  if (ev.utm) return ev.utm;
  if (ev.ref) {
    try {
      const h = new URL(ev.ref).hostname.replace(/^www\./, '');
      if (h && !h.includes('leonkelvinli')) return h;
      return 'internal';
    } catch (e) { return 'unknown-ref'; }
  }
  return 'direct';
}

module.exports = { persistEvent, readEvents, sourceOf };
