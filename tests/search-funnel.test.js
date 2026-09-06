const test = require('node:test');
const assert = require('node:assert/strict');
const { searchChannel, buildSearchFunnel } = require('../server/search-funnel');
const { normalizeEvent } = require('../server/events');
const ts = '2026-09-05T12:00:00Z';
const receipt = 'lead_12345678-1234-1234-1234-123456789abc';
const options = { start: '2026-09-01', end: '2026-09-05' };
const page = { ts, name: 'page_view', sessionId: 'session_123', ref: 'https://www.google.com.br/' };
const accepted = { ...page, name: 'quote_lead_accepted', receipt };
const lead = { ts, receiptId: receipt, referrer: page.ref, email: 'private@example.com' };
test('recognizes exact search and AI hosts without merging paid or spoofed sources', () => {
  assert.equal(searchChannel(page), 'organic_search');
  assert.equal(searchChannel({ ref: 'https://claude.ai/chat/private' }), 'ai_referral');
  assert.equal(searchChannel({ ref: 'https://google.com.evil.example' }), 'other_or_unknown');
  assert.equal(searchChannel({ ref: page.ref, firstMedium: 'cpc' }), 'paid');
  assert.equal(searchChannel({ firstUtmSource: 'google', firstUtmMedium: 'organic' }), 'organic_search');
  assert.equal(searchChannel({ firstUtm: 'seo' }), 'other_or_unknown');
});
test('selects an entire first-touch envelope before considering a later campaign', () => {
  const row = { name: 'page_view', firstRef: 'https://google.com/', medium: 'cpc', gclid: 'later-click' };
  assert.equal(searchChannel(row), 'organic_search');
  assert.equal(searchChannel(normalizeEvent(row)), 'organic_search');
  const direct = normalizeEvent({ ...row, firstPage: '/', firstRef: '', ref: 'https://google.com/' });
  assert.equal(direct.firstGclid, '');
  assert.equal(direct.firstMedium, '');
  assert.equal(searchChannel(direct), 'other_or_unknown');
  assert.equal(searchChannel({ firstUtm: 'chatgpt.com', firstRef: 'https://chatgpt.com/' }), 'ai_referral');
  assert.equal(searchChannel({ firstUtm: 'unrelated', firstRef: 'https://chatgpt.com/' }), 'other_or_unknown');
  assert.equal(searchChannel({ firstUtm: 'chatgpt.com' }), 'other_or_unknown');
  assert.equal(searchChannel({ firstRef: 'https://chatgpt.com/', firstMedium: 'cpc' }), 'paid');
});
test('joins accepted receipts, deduplicates and never returns private fields', () => {
  const report = buildSearchFunnel({ ...options, events: [page, accepted, accepted], leads: [lead, lead] });
  assert.equal(report.rows[0].observedSessions, 1);
  assert.equal(report.rows[0].acceptedInquiries, 1);
  assert.equal(report.rows[0].sessionLinkedInquiries, 1);
  assert.equal(report.rows[0].sessionToInquiryRate, null);
  assert.doesNotMatch(JSON.stringify(report), /private@example|lead_123|session_123/);
});
test('a browser success or nonexistent receipt creates no authoritative outcome', () => {
  const report = buildSearchFunnel({ ...options, events: [page, accepted, { ...page, name: 'calendar_booking_success', bookingUid: 'booking_123' }] });
  assert.equal(report.rows[0].sessionLinkedInquiries, 0);
  assert.equal(report.rows[0].authoritativeBookings, 0);
});
test('deduplicates rescheduled authoritative stages and excludes synthetic receipts', () => {
  const acquisition = [
    { ts, occurredAt: ts, kind: 'funnel_stage', stage: 'booked', bookingUid: 'booking_old' },
    { ts, occurredAt: ts, kind: 'funnel_stage', stage: 'booked', bookingUid: 'booking_new', context: { previousBookingUid: 'booking_old' } },
    { ts, occurredAt: ts, kind: 'funnel_stage', stage: 'qualified', bookingUid: 'booking_new' },
  ];
  const report = buildSearchFunnel({ ...options, events: [page, { ...page, name: 'calendar_booking_success', bookingUid: 'booking_old' }], leads: [{ ...lead, synthetic: true }], acquisition });
  assert.equal(report.rows[0].acceptedInquiries, 0);
  assert.equal(report.rows[0].authoritativeBookings, 1);
  assert.equal(report.rows[0].authoritativeQualified, 1);
});
test('unmatched stages and missing collection completeness cannot become conversion rates', () => {
  const report = buildSearchFunnel({ ...options, events: [page], acquisition: [{ ts, kind: 'funnel_stage', stage: 'won', bookingUid: 'booking_missing' }] });
  assert.equal(report.unattributedAuthoritativeStages, 1);
  assert.equal(report.rows[0].authoritativeWon, 0);
  const complete = buildSearchFunnel({ ...options, events: [page, accepted], leads: [lead], coverageVerified: true });
  assert.equal(complete.rows[0].sessionToInquiryRate, 1);
  assert.equal(buildSearchFunnel({ ...options, events: [page], coverageVerified: true, eventsTruncated: true }).rows[0].sessionToInquiryRate, null);
});
test('later qualification retains an earlier booking source without adding visits to the period', () => {
  const prior = { ...page, ts: '2026-08-31T23:59:59Z' };
  const booking = { ...prior, name: 'calendar_booking_success', bookingUid: 'booking_prior' };
  const acquisition = [
    { ts: prior.ts, kind: 'funnel_stage', stage: 'booked', bookingUid: booking.bookingUid },
    { ts, kind: 'funnel_stage', stage: 'qualified', bookingUid: booking.bookingUid },
    { ts, kind: 'funnel_stage', stage: 'won', bookingUid: booking.bookingUid },
  ];
  const report = buildSearchFunnel({ ...options, events: [booking, prior], acquisition, coverageVerified: true });
  assert.equal(report.rows[0].observedSessions, 0);
  assert.equal(report.rows[0].authoritativeBookings, 0);
  assert.equal(report.rows[0].authoritativeQualified, 1);
  assert.equal(report.rows[0].authoritativeWon, 1);
  assert.equal(report.rows[0].sessionToInquiryRate, null);
  assert.equal(report.unattributedAuthoritativeStages, 0);
});
test('historical booking matches still reject ambiguous and future session evidence', () => {
  const prior = { ...page, ts: '2026-08-31T12:00:00Z' };
  const booking = { ...prior, name: 'calendar_booking_success', bookingUid: 'booking_prior' };
  const acquisition = [{ ts, kind: 'funnel_stage', stage: 'qualified', bookingUid: booking.bookingUid }];
  const ambiguous = buildSearchFunnel({ ...options, acquisition, events: [prior, booking,
    { ...prior, sessionId: 'other_session' }, { ...booking, sessionId: 'other_session' }] });
  assert.equal(ambiguous.rows[0].authoritativeQualified, 0);
  assert.equal(ambiguous.unattributedAuthoritativeStages, 1);
  const future = buildSearchFunnel({ ...options, acquisition, events: [
    { ...prior, ts: '2026-09-06T00:00:00Z' }, { ...booking, ts: '2026-09-06T00:00:01Z' }] });
  assert.equal(future.rows[0].authoritativeQualified, 0);
  assert.equal(future.unattributedAuthoritativeStages, 1);
});
test('rejects invalid dates and respects the observation window', () => {
  assert.throws(() => buildSearchFunnel({ start: '2026-02-30', end: '2026-09-05' }));
  assert.equal(buildSearchFunnel({ ...options, events: [{ ...page, ts: '2026-08-31T23:59:59Z' }] }).rows[0].observedSessions, 0);
});
