const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { normalizeEvent } = require('../server/events');
const { webVitalsReport } = require('../server/web-vitals-report');
const metric = { name: 'web_vital', metricName: 'LCP', metricValue: 1200, metricId: 'v6-example-1', device: 'mobile', path: '/guides/website-builder-or-custom-software' };
test('metric normalization accepts finite bounded values, not DOM data', () => {
  const event = normalizeEvent({ ...metric, entries: ['private DOM text'], email: 'private@example.com' });
  assert.equal(event.metricValue, 1200);
  assert.equal(event.metricName, 'LCP');
  assert.doesNotMatch(JSON.stringify(event), /private DOM|private@example/);
  for (const value of [NaN, Infinity, -1, '1200', 4000000]) assert.equal(normalizeEvent({ ...metric, metricValue: value }), null);
  assert.equal(normalizeEvent({ ...metric, metricName: 'unknown' }), null);
  assert.equal(normalizeEvent({ ...metric, metricId: '<script>' }), null);
});
test('sample report upserts metric IDs and does not claim a field pass', () => {
  const report = webVitalsReport([
    { ...metric, ts: '2026-09-05T10:00:00Z' },
    { ...metric, metricValue: 1400, ts: '2026-09-05T10:01:00Z' },
    ...[2000, 3000, 4000].map((value, i) => ({ ...metric, metricId: `sample-${i}`, metricValue: value, ts: '2026-09-05T10:01:00Z' }))
  ]);
  assert.equal(report.rows[0].samples, 4);
  assert.equal(report.rows[0].p75, 3000);
  assert.equal(report.status, 'partial_field_observation');
  assert.equal(webVitalsReport([]).status, 'unobserved');
  assert.equal(webVitalsReport([{ ...metric, ts: 'invalid' }]).status, 'unobserved');
  assert.equal(webVitalsReport([{ ...metric, ts: '2026-08-31T10:00:00Z' }], { start: '2026-09-01', end: '2026-09-05' }).status, 'unobserved');
});
test('pinned library stays self-hosted and ships its license', () => {
  const root = path.resolve(__dirname, '..');
  assert.ok(fs.statSync(path.join(root, 'assets/vendor/web-vitals-6.2.1.js')).size < 10000);
  assert.match(fs.readFileSync(path.join(root, 'assets/vendor/web-vitals.LICENSE.txt'), 'utf8'), /Apache License/);
  const bridge = fs.readFileSync(path.join(root, 'assist.js'), 'utf8');
  assert.match(bridge, /script\.src = '\/assets\/vendor\/web-vitals-6\.2\.1\.js'/);
  assert.match(bridge, /script\.async = true/);
});
