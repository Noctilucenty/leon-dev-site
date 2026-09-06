# Measure qualified inquiries, not SEO activity

## Current evidence

All 50 current sitemap routes were verified live on September 5. An indexable route is not an indexed route. The newer signed-in UI baseline is `content/seo/search-baseline-2026-09-05.json`; it is not an API export. The older September 4 record remains historical evidence.

The displayed August 19–September 3 Web window had 6 clicks and 56 impressions. Google generative-AI search showed 3 impressions separately. The August 27 indexing snapshot had 37 indexed pages; it is not a current 37/50 coverage ratio. Qualified inquiries, bookings, won work and acquisition revenue for that window remain **unknown** here.

Google now provides a [Generative AI performance report](https://support.google.com/webmasters/answer/16984139). Record its date/filter/scope separately from Web search and first-party visits; an impression is not a click, citation, inquiry or recommendation. Its report was inspected; no account setting was changed.

## Measurement ladder

| Stage | Evidence source | Do not confuse with |
| --- | --- | --- |
| Search impression / click | Search Console, same date range and filters | A visitor or a lead |
| Organic / AI referral visit | Existing first-party events; bounded first/last referrer | An AI recommendation or citation |
| Useful next step | `seo_related_click`, proof view, another service/guide visit | A successful sales conversation |
| Review interest | `seo_guide_review_click`, form start | An accepted inquiry |
| Accepted inquiry | Backend opaque lead receipt | Delivered email, qualified lead or booking |
| Booked / held / qualified / won | Authoritative booking lifecycle and reviewed business records | A calendar click or browser success message |

The authenticated `/api/traffic?format=json&start=YYYY-MM-DD&end=YYYY-MM-DD` report now includes `searchFunnel`. It matches an anonymous landing session to a unique backend-accepted receipt and authoritative lifecycle records. It excludes QA/synthetic evidence, deduplicates receipts/reschedules, and reports ambiguous or unassigned outcomes separately. It does not join an individual to a Search Console query. Retention/truncation and completeness remain explicit; rates stay null unless coverage is verified. No private lead or booking record is rewritten.

The same report includes sampled `webVitals`; see [the measurement boundaries](WEB_VITALS.md). These events are not qualification evidence.

Lifecycle outcomes use their own event dates. A September qualification can keep
the source of an August visit when that anonymous session and booking link are
still retained. Those earlier visits do not enter September's session denominator
or inquiry rate. Ambiguous, missing or future-only links remain unattributed.
Homepage inquiry attribution preserves the entire recorded first visit, including
empty direct-visit fields; a later advertising click remains a separate last touch.

## Offline Search Console import

Use a legitimate joint report with columns `Query,Page,Clicks,Impressions,Position`. A query table and a separate page table cannot be safely joined; the tool rejects that input. Country/device splits may be included as separate rows and are aggregated, so keep exported filters and row completeness documented alongside the source.

```sh
python3 tools/seo_system.py report --csv /absolute/path/search-query-page.csv --start-date 2026-08-01 --end-date 2026-08-31
```

The tool makes no network request and does not save its report automatically. It validates canonical domain/pages, dates and finite metrics; sums clicks/impressions; recalculates CTR; weights average position by impressions; drops obvious contact-like queries; and leaves conversion fields null.

It flags positions 8–20 and low CTR after at least 20 impressions as review candidates. The 2% CTR and sample thresholds are triage choices, **not universal success targets**. Multiple pages for a query trigger an intent inspection, not an automatic redirect. Zero-impression rows have unknown CTR/position rather than invented zeros.

## Read-only API history

`tools/search_console_sync.py` supports the two existing URL-prefix properties, Leon Builds and Curio. It is implemented and tested offline, but **not connected**: an owner-authorized OAuth access token with Search Console read-only scope must be supplied as `SEO_GSC_ACCESS_TOKEN` by the execution environment. Never paste a token into a command, documentation, a committed file or browser extraction. The tool does not create OAuth clients, purchase services, save tokens or change properties.

```sh
python3 tools/search_console_sync.py sync --property https://leonbuilds.org/ --start-date 2026-09-06 --end-date 2026-10-03
python3 tools/search_console_sync.py history --property https://leonbuilds.org/
python3 tools/search_console_sync.py compare --previous private/seo-search-console/leonbuilds/PREVIOUS_HASH.json --current private/seo-search-console/leonbuilds/CURRENT_HASH.json
```

Use actual past finalized reporting dates when running sync; the example dates are a planned post-release window, not imported observations. Replace the comparison filenames with paths returned by successful sync. Run `--help` for optional country/device filters and bounded pagination. Missing authorization returns `BLOCKED` with null metrics. Snapshots live under the gitignored, unpublished `private/seo-search-console` directory and are immutable/content-addressed. Property totals, dates, query rows, page rows and joint rows remain separate; privacy-hidden queries and capped API rows are not a complete demand census. Equal-window comparison rejects mismatched properties, surfaces or filters.

Google generative-AI UI observations stay in the separately scoped baseline file. This Web Search API tool does not claim to import the generative-AI report or join it to a particular person.

## Review cadence and experiments

After deployment and enough crawl/reporting time, compare equal 28-day windows using the same property, country/device filters, brand/non-brand split and completeness caveats. With the currently small historical sample, avoid attributing a few extra clicks to a specific change.

First experiment: does the buyer guide send relevant visitors to actual proof and the free review? Measure guide landings → contextual links → accepted inquiries; inspect qualification separately. Keep canonical URLs unchanged. A title experiment comes later only if enough impressions show a snippet/intent problem.

No recurring scheduler was created or changed. No paid traffic, budget, outreach, Search Console property, Google Business Profile or automatic publishing action is part of this measurement script.
