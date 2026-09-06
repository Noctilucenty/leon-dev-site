'use strict';

// Aggregate retained first-party evidence. Never join a search query to a person,
// infer a lead from a CTA, or promote a browser booking signal into a sale.
const { qaExclusionSets, qaEventExclusion } = require('./acquisition');
const CHANNELS = ['organic_search', 'ai_referral', 'paid', 'other_or_unknown'];
const RECEIPT = /^lead_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SEARCH = new Set(['bing.com', 'duckduckgo.com', 'search.yahoo.com', 'ecosia.org', 'search.brave.com', 'baidu.com']);
const AI = new Set(['chatgpt.com', 'chat.openai.com', 'perplexity.ai', 'claude.ai', 'gemini.google.com', 'copilot.microsoft.com']);

function searchChannel(row = {}) {
  // An explicitly recorded direct first touch has intentionally empty source
  // fields. Never fill those holes with a later campaign's attribution.
  const first = ['firstPage', 'firstRef', 'firstReferrer', 'firstUtm', 'firstUtmSource', 'firstMedium', 'firstUtmMedium', 'firstCampaign', 'firstUtmCampaign', 'firstGclid', 'firstGbraid', 'firstWbraid', 'firstMsclkid'].some(key => row[key]);
  const medium = String(first ? row.firstMedium || row.firstUtmMedium || '' : row.medium || row.utmMedium || '').toLowerCase();
  if (/^(cpc|ppc|paid|paid_social|paid social|display|cpm)$/.test(medium)
      || (first ? ['firstGclid', 'firstGbraid', 'firstWbraid', 'firstMsclkid'] : ['gclid', 'gbraid', 'wbraid', 'msclkid']).some(key => row[key])) return 'paid';
  const source = String(first ? row.firstUtm || row.firstUtmSource || '' : row.utm || row.utmSource || '').toLowerCase();
  if (medium === 'organic' && /^(google|bing|duckduckgo|yahoo|ecosia|brave|baidu)$/.test(source)) return 'organic_search';
  let host = '';
  try { host = new URL(first ? row.firstRef || row.firstReferrer : row.ref || row.referrer).hostname.toLowerCase().replace(/^www\./, ''); } catch (_) {}
  const compatibleAiSources = {
    'chatgpt.com': ['chatgpt', 'openai', 'chatgpt.com'], 'chat.openai.com': ['chatgpt', 'openai', 'chat.openai.com'],
    'perplexity.ai': ['perplexity', 'perplexity.ai'], 'claude.ai': ['claude', 'claude.ai'],
    'gemini.google.com': ['gemini', 'gemini.google.com'], 'copilot.microsoft.com': ['copilot', 'copilot.microsoft.com']
  };
  if (AI.has(host) && ['', 'referral', 'ai', 'organic'].includes(medium)
      && (!source || compatibleAiSources[host].includes(source))) return 'ai_referral';
  // A tagged source without an explicit organic medium is not automatically SEO.
  if (source) return 'other_or_unknown';
  if (SEARCH.has(host) || /^google\.(?:com|[a-z]{2}|com\.[a-z]{2}|co\.[a-z]{2})$/.test(host)) return 'organic_search';
  return 'other_or_unknown';
}

function validDay(value) {
  return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)
    && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
}

function buildSearchFunnel({ events = [], leads = [], acquisition = [], start, end, eventsTruncated = false, coverageVerified = false }) {
  if (!validDay(start) || !validDay(end) || start > end) throw new Error('start and end must be ordered YYYY-MM-DD dates');
  const inWindow = row => {
    const time = Date.parse(row.occurredAt || row.ts || '');
    if (!Number.isFinite(time)) return false;
    const day = new Date(time).toISOString().slice(0, 10);
    return start <= day && day <= end;
  };
  const exclusions = qaExclusionSets(acquisition);
  if (exclusions.errors.length) throw new Error('acquisition exclusion ledger failed integrity checks');
  const qa = qaEventExclusion(events, leads, acquisition, acquisition);
  const retained = events.filter((event, index) => !qa.directEventIndexes.has(index) && !qa.sessionIds.has(String(event.sessionId || '')));
  const windowEvents = retained.filter(inWindow);
  // Qualification can happen after the visit/booking reporting period. Keep
  // retained source evidence through the period end for lifecycle attribution,
  // while the visit denominator still contains only this period's page views.
  const attributionEvents = retained.filter(event => {
    const time = Date.parse(event.ts || '');
    return Number.isFinite(time) && new Date(time).toISOString().slice(0, 10) <= end;
  }).sort((a, b) => Date.parse(a.ts) - Date.parse(b.ts));
  const attributionSessions = new Map();
  const sessions = new Map();
  for (const event of attributionEvents) {
    if (event.name !== 'page_view' || !event.sessionId) continue;
    if (!attributionSessions.has(event.sessionId)) attributionSessions.set(event.sessionId, searchChannel(event));
    if (inWindow(event)) sessions.set(event.sessionId, attributionSessions.get(event.sessionId));
  }
  const rows = Object.fromEntries(CHANNELS.map(channel => [channel, {
    channel, observedSessions: 0, acceptedInquiries: 0, sessionLinkedInquiries: 0,
    authoritativeBookings: 0, authoritativeQualified: 0, authoritativeWon: 0,
    sessionToInquiryRate: null
  }]));
  for (const channel of sessions.values()) rows[channel].observedSessions++;

  const uniqueLeads = new Map();
  for (const lead of leads) if (inWindow(lead) && lead.synthetic !== true && RECEIPT.test(lead.receiptId || '') && !exclusions.receiptIds.has(lead.receiptId)) uniqueLeads.set(lead.receiptId, lead);
  const linkedReceipts = new Map();
  for (const event of windowEvents) {
    if (!['quote_lead_accepted', 'lead_submit_success', 'call_request_sent'].includes(event.name) || !uniqueLeads.has(event.receipt) || !sessions.has(event.sessionId)) continue;
    const set = linkedReceipts.get(event.receipt) || new Set();
    set.add(event.sessionId); linkedReceipts.set(event.receipt, set);
  }
  const inquirySessions = Object.fromEntries(CHANNELS.map(channel => [channel, new Set()]));
  for (const [receipt, lead] of uniqueLeads) {
    rows[searchChannel(lead)].acceptedInquiries++;
    const linked = linkedReceipts.get(receipt);
    if (!linked || linked.size !== 1) continue;
    const session = [...linked][0], channel = sessions.get(session);
    rows[channel].sessionLinkedInquiries++;
    inquirySessions[channel].add(session);
  }

  // Resolve explicit reschedules; a replacement slot is not a second opportunity.
  const replacements = new Map();
  for (const record of acquisition) if (record.kind === 'funnel_stage' && record.bookingUid && record.context?.previousBookingUid && record.context.previousBookingUid !== record.bookingUid) replacements.set(record.context.previousBookingUid, record.bookingUid);
  const canonical = uid => {
    const seen = new Set(); let current = uid;
    while (replacements.has(current)) {
      if (seen.has(current)) return null;
      seen.add(current); current = replacements.get(current);
    }
    return current;
  };
  const excludedBookings = new Set([...exclusions.bookingUids].map(canonical));
  const bookingSessions = new Map();
  for (const event of attributionEvents) {
    if (event.name !== 'calendar_booking_success' || !event.bookingUid || !attributionSessions.has(event.sessionId)) continue;
    const uid = canonical(event.bookingUid);
    if (!uid || excludedBookings.has(uid)) continue;
    const set = bookingSessions.get(uid) || new Set(); set.add(event.sessionId); bookingSessions.set(uid, set);
  }
  const counted = new Set(); let unattributedStages = 0;
  const stageFields = { booked: 'authoritativeBookings', qualified: 'authoritativeQualified', won: 'authoritativeWon' };
  for (const record of acquisition) {
    if (record.kind !== 'funnel_stage' || record.authoritative === false || !stageFields[record.stage] || !inWindow(record)) continue;
    const uid = canonical(record.bookingUid);
    if (!uid || excludedBookings.has(uid)) continue;
    const key = `${uid}:${record.stage}`;
    if (counted.has(key)) continue;
    counted.add(key);
    const linked = bookingSessions.get(uid);
    if (!linked || linked.size !== 1) { unattributedStages++; continue; }
    rows[attributionSessions.get([...linked][0])][stageFields[record.stage]]++;
  }
  for (const channel of CHANNELS) {
    if (coverageVerified && !eventsTruncated && rows[channel].observedSessions) rows[channel].sessionToInquiryRate = inquirySessions[channel].size / rows[channel].observedSessions;
  }
  return {
    period: { start, end, timezone: 'UTC' }, status: coverageVerified && !eventsTruncated ? 'observed' : 'partial',
    coverageVerified, eventsTruncated, rows: Object.values(rows), unattributedAuthoritativeStages: unattributedStages,
    limitations: ['Counts cover retained observations, not all visitors or all historical business records.',
      'Only an accepted backend receipt counts as an inquiry; only a lifecycle record counts as booked, qualified or won.',
      'Booking attribution needs an unambiguous anonymous-session match; unmatched stages remain separate.',
      'Lifecycle attribution can use retained visits before this period; observed sessions and inquiry rates use only in-period page views.',
      'AI referral means an observed referrer, not an AI citation. Search Console totals cannot identify these sessions.',
      'Historical events may contain legacy mixed-touch attribution; only newly normalized events preserve empty first-touch fields.',
      'Rates remain null unless the collection window is independently verified complete.']
  };
}

module.exports = { searchChannel, buildSearchFunnel };
