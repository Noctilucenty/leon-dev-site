# Web Vitals measurement

Pinned GoogleChrome `web-vitals` 6.2.1, fetched September 5, 2026 from the official [npm tarball](https://registry.npmjs.org/web-vitals/-/web-vitals-6.2.1.tgz). Registry SHA-512 was verified before extracting the unmodified 8,991-byte IIFE and full Apache 2.0 license.

Integrity: `sha512-rLcLXA2sx6+9dE88NHFubwTtGxpK4yYBLj6qHPdFoCaLr0cXGb4efOqtKLlm4loGA4OEKHIQKMKzZkKyOh5ctw==`

The browser loads this same-origin asset asynchronously. The bridge forwards only metric name, numeric value, metric ID, rating and page pathname; never the library's DOM entries, input text, selectors or page query string. Leon Builds reuses its existing first-party event transport and anonymous session convention. It does not send these metrics to the Google Ads tag. The privacy page discloses the added performance fields.

[LCP, INP and CLS](https://web.dev/articles/vitals) need actual visitor observations. Local tests verify transport and privacy boundaries, not a speed score. No Search Console field data was available in the September 5 inspection, and the public PageSpeed API returned quota HTTP 429. Missing metrics remain absent. First-party p75 is not a CrUX pass and does not prove that animations caused a change.

To review animation impact, compare the same pages, device groups and equal date windows before and after a controlled change. Keep sample counts and missing/consent-limited observations visible. Avoid claiming improvement from tiny samples. No automatic animation removal or unobserved performance score is configured.
