'use strict';

// This is our retained, sampled RUM data, not Google's CrUX assessment.
function webVitalsReport(events, period = null) {
  const latest = new Map();
  for (const event of events || []) {
    if (event.name !== 'web_vital' || !['LCP', 'INP', 'CLS'].includes(event.metricName)
        || !/^[A-Za-z0-9_-]{1,96}$/.test(event.metricId || '')
        || typeof event.metricValue !== 'number' || !Number.isFinite(event.metricValue)
        || event.metricValue < 0 || !Number.isFinite(Date.parse(event.ts))) continue;
    if (period) {
      const day = new Date(event.ts).toISOString().slice(0, 10);
      if (day < period.start || day > period.end) continue;
    }
    const key = `${event.metricName}:${event.metricId}`;
    if (!latest.has(key) || Date.parse(event.ts) >= Date.parse(latest.get(key).ts)) latest.set(key, event);
  }
  const groups = new Map();
  for (const event of latest.values()) {
    const path = String(event.path || '/').split(/[?#]/)[0].slice(0, 200);
    const device = ['mobile', 'desktop', 'tablet'].includes(event.device) ? event.device : 'unknown';
    const key = `${path}:${device}:${event.metricName}`;
    if (!groups.has(key)) groups.set(key, { path, device, metric: event.metricName, values: [] });
    groups.get(key).values.push(event.metricValue);
  }
  return {
    period,
    status: groups.size ? 'partial_field_observation' : 'unobserved',
    rows: [...groups.values()].map(({ path, device, metric, values }) => {
      values.sort((a, b) => a - b);
      return { path, device, metric, samples: values.length,
        p75: values[Math.ceil(values.length * 0.75) - 1], unit: metric === 'CLS' ? 'score' : 'ms',
        goodThreshold: { LCP: 2500, INP: 200, CLS: 0.1 }[metric] };
    }),
    limitations: ['Unknown or unsupported metrics remain absent, never zero.',
      'P75 uses the latest value per metric ID, grouped by page and device.',
      'Sampled retained observations do not certify a CrUX pass or a causal animation effect.']
  };
}

module.exports = { webVitalsReport };
