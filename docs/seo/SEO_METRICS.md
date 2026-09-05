# Measure qualified inquiries, not SEO activity

## Current evidence

50 indexable sitemap routes after this local release; 49 were live and byte-verified before it. An indexable route is not an indexed route. Historical Search Console figures are in `content/search-console-baseline-2026-09-04.md`; no new account export was obtained in this task.

Current impressions, clicks, indexed count, organic sessions, qualified inquiries, bookings, won work and acquisition revenue remain **unknown** here. The new opportunity report is a system for supplying evidence, not fabricated baseline data.

Google now provides a [Generative AI performance report](https://support.google.com/webmasters/answer/16984139). Record its date/filter/scope separately from Web search and first-party visits; an impression is not a click, citation, inquiry or recommendation. Its current account data and generative-AI inclusion settings were not inspected or changed in this lane.

## Measurement ladder

| Stage | Evidence source | Do not confuse with |
| --- | --- | --- |
| Search impression / click | Search Console, same date range and filters | A visitor or a lead |
| Organic / AI referral visit | Existing first-party events; bounded first/last referrer | An AI recommendation or citation |
| Useful next step | `seo_related_click`, proof view, another service/guide visit | A successful sales conversation |
| Review interest | `seo_guide_review_click`, form start | An accepted inquiry |
| Accepted inquiry | Backend opaque lead receipt | Delivered email, qualified lead or booking |
| Booked / held / qualified / won | Authoritative booking lifecycle and reviewed business records | A calendar click or browser success message |

The site already distinguishes these stages. This release adds diagnostic link names but does not change backend schemas, callback configuration, consent handling or private lead records.

## Offline Search Console import

Use a legitimate joint report with columns `Query,Page,Clicks,Impressions,Position`. A query table and a separate page table cannot be safely joined; the tool rejects that input. Country/device splits may be included as separate rows and are aggregated, so keep exported filters and row completeness documented alongside the source.

```sh
python3 tools/seo_system.py report --csv /absolute/path/search-query-page.csv --start-date 2026-08-01 --end-date 2026-08-31
```

The tool makes no network request and does not save its report automatically. It validates canonical domain/pages, dates and finite metrics; sums clicks/impressions; recalculates CTR; weights average position by impressions; drops obvious contact-like queries; and leaves conversion fields null.

It flags positions 8–20 and low CTR after at least 20 impressions as review candidates. The 2% CTR and sample thresholds are triage choices, **not universal success targets**. Multiple pages for a query trigger an intent inspection, not an automatic redirect. Zero-impression rows have unknown CTR/position rather than invented zeros.

## Review cadence and experiments

After deployment and enough crawl/reporting time, compare equal 28-day windows using the same property, country/device filters, brand/non-brand split and completeness caveats. With the currently small historical sample, avoid attributing a few extra clicks to a specific change.

First experiment: does the buyer guide send relevant visitors to actual proof and the free review? Measure guide landings → contextual links → accepted inquiries; inspect qualification separately. Keep canonical URLs unchanged. A title experiment comes later only if enough impressions show a snippet/intent problem.

No recurring scheduler was created or changed. No paid traffic, budget, outreach, Search Console property, Google Business Profile or automatic publishing action is part of this measurement script.
