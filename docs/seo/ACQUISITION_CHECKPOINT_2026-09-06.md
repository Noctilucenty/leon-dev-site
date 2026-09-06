# Acquisition and field-performance checkpoint — September 6, 2026

Observed September 6, 2026, Pacific Time. Repository inspected:
`f44abe5fe12b4ae0bc60b459af3679d9507f432e`. This checkpoint contains operational
status and aggregate-report findings; it contains no visitor records,
contact details, booking identifiers, or credentials.

## Current live evidence

Read-only `GET https://leon-assist.onrender.com/api/health` returned HTTP 200:

| Check | Observed value |
| --- | --- |
| Process liveness | `ok: true` |
| Owner inquiry email | `verified` |
| Recorded inbox verification | `2026-09-05T10:07:05.424Z` |
| Visitor email confirmations | `verified` |
| Acquisition storage | `durable-configured` |
| Local storage mode | `configured-persistent-path` |
| External acquisition sink | Not configured |
| Cal.com signing secret | Configured |

These fields confirm the current configuration and retained delivery-verification
state. They do not establish that a new inquiry or booking occurred, that every
future email will arrive, or that Cal.com has successfully delivered a new
lifecycle webhook.

## Authenticated access resolved

Initial unauthenticated requests to `/api/traffic?format=json` and
`/api/acquisition?format=json` returned HTTP 401. Access was subsequently resolved
through the existing signed-in Render Web Shell for `leon-assist`
(`srv-da1pb4qjnfac739v3e4g`). The shell issued localhost GET requests using the
service's existing `process.env.LEADS_KEY` in the `x-leads-key` header. The key
was not retrieved, exposed, or copied into a local file.

The successful aggregate readbacks were completed by **2026-09-06T18:01:02Z**.
The traffic report's date window is **September 5–6, 2026, UTC**. The September 6
day is incomplete. The earlier HTTP 401 was an access issue and no longer
prevents these reports; it was never evidence of missing traffic or delayed data.

## Retained funnel observations

The report returned `status: partial`, `coverageVerified: false`, and
`eventsTruncated: false`.

| Recorded channel | Observed sessions | Accepted inquiries | Attributed authoritative bookings | Qualified | Won |
| --- | ---: | ---: | ---: | ---: | ---: |
| Organic search | 0 | 0 | 0 | 0 | 0 |
| AI referral | 0 | 0 | 0 | 0 | 0 |
| Paid-tagged | 2 | 0 | 0 | 0 | 0 |
| Other or unknown | 25 | 0 | 0 | 0 | 0 |

There were **27 observed anonymous sessions**, **0 accepted inquiries** in this
retained date window, and **0 unattributed authoritative stages**. Every
session-to-inquiry rate remains **null** because collection completeness has not
been established.

The two paid-tagged sessions are not proof of two Google Ads clicks. Retained
events may include operator visits that were not explicitly marked for exclusion.
These totals do not establish that all sessions represent prospects or that the
entire business has received no inquiries, bookings, or qualified opportunities.
Business outcomes outside these retained observations remain unknown.

## Entire retained lifecycle ledger

The authenticated `/api/acquisition?format=json&limit=1` response reported
**5 retained ledger records** and **0 counted bookings**. Its aggregate funnel
is computed over the entire retained ledger even when the returned raw-record
list is limited to one; raw records and identifiers are omitted here.

| Retained stage | Count after QA exclusions and reschedule deduplication |
| --- | ---: |
| Booked | 0 |
| Attended | 0 |
| Qualified | 0 |
| Proposal | 0 |
| Won | 0 |
| Lost | 0 |
| Cancelled | 0 |
| No-show | 0 |

The report applied **1 configured booking exclusion**, excluding **3 stage
records**. These are retained system totals, not complete historical business
totals. Unknown off-site or unrecorded activity remains unknown; the presence of
a configured Cal.com secret is not proof that all lifecycle events were received.

## Sampled field-performance observations

`webVitals.status` is **partial_field_observation**. Each row is p75 for its
recorded page/device/metric group, using the latest value per metric identifier.

| Path | Device | Metric | p75 | Samples |
| --- | --- | --- | ---: | ---: |
| `/` | Desktop | LCP | 740 ms | 1 |
| `/` | Desktop | CLS | 0.0003451135711446921 | 1 |
| `/guides/website-builder-or-custom-software` | Desktop | LCP | 600 ms | 1 |
| `/guides/website-builder-or-custom-software` | Desktop | CLS | 0 | 1 |
| `/` | Tablet | LCP | 4,783 ms | 1 |
| `/` | Mobile | LCP | 248 ms | 4 |
| `/` | Mobile | INP | 40 ms | 4 |
| `/services/business-automation` | Mobile | LCP | 534 ms | 1 |
| `/technical-build-partner` | Mobile | LCP | 287 ms | 1 |
| `/quote` | Mobile | LCP | 347 ms | 1 |
| `/work` | Mobile | LCP | 244 ms | 1 |
| `/about` | Mobile | LCP | 387 ms | 3 |
| `/zh` | Mobile | LCP | 408 ms | 1 |
| `/reviews` | Mobile | LCP | 426 ms | 2 |

The tablet homepage observation warrants a targeted investigation; **one sample
does not establish a recurring tablet performance problem or its cause**. The
small, potentially mixed operator/visitor sample does not support a site-wide
speed claim, a before/after improvement claim, or an animation change justified
by measured conversion impact. Missing page/device/metric combinations remain
unknown. These first-party observations do not supply a Google CrUX assessment.
Search Console's Core Web Vitals view, updated September 4 and checked September
6, still reported insufficient usage over the last 90 days for both mobile and
desktop. That does not erase the separate first-party samples above.

## Limits and next evidence

The dated `searchFunnel` and all-retained-date lifecycle totals have different
scopes. The traffic endpoint reads at most 5,000 retained events; this response
reported no truncation, which does not independently prove complete collection.
Use authoritative lifecycle records for qualification and sales outcomes, and
match reporting windows before comparison. A browser booking signal alone is
insufficient. Obtain more page/device observations and distinguish known operator
checks before deciding whether performance materially impedes acquisition.

No paid-media changes, synthetic inquiries, synthetic conversions, or lifecycle
mutations were used to obtain these aggregate reports.
