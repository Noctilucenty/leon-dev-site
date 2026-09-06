# Leon Builds Google Search live checkpoint — 2026-09-05 PT

This records the Orlando contractor Search campaign's launch and a later
September 5 correction to its spend reconciliation. Google Ads remains the
authority for billing, policy, delivery, and spend. No inquiry, booking, or
client acquisition is established by this record.

## Launch receipt — historical state

- Account: Leon Builds, `794-705-8433`.
- Campaign: `LB | Orlando | Search | Contractor Review | 2026-09-05`.
- Campaign ID: `24218199248`.
- State at launch: **Enabled — Eligible (Learning)**; superseded by the
  September 5 followthrough below.
- Flight: September 5 through September 14, 2026.
- Account timezone: Pacific Time.
- Schedule: every day, 6:00 AM–7:00 PM Pacific Time, with no bid adjustments.
- Budget at launch: **$85.27 campaign total**, subsequently reduced to
  **$75.39 campaign total** in the followthrough below.
- Bidding: Maximize clicks with a **$5 maximum CPC**.
- Inventory: Google Search only; Search Partners and Display are off.
- Geography: Orlando–Daytona Beach–Melbourne, FL Nielsen DMA only.
- Location behavior: presence-only, meaning people in or regularly in the
  included location.
- Language: English.
- Expansion: AI Max, ad-group AI Max, text customization, final-URL expansion,
  and keyword/asset generation are off.
- Conversion goals: account-default booking and lead-form goals. The reviewed
  primary actions remain `LB | Consultation Booked` and
  `LB | Quote Submitted`; contact-click actions remain secondary.

The campaign was created, immediately paused while the live controls and
negative keywords were checked, and then enabled under the owner's earlier
action-time confirmation. The old campaign ended September 3 and was not
reactivated.

## Launch spend calculation — superseded

The launch readback showed 63 impressions, 3 clicks, **$14.73 cost**, and
0 recorded Google Ads conversions. That readback covered **August 29 through
September 4**, not lifetime. This file previously described the range as
lifetime incorrectly. The older September 2 checkpoint's $14.79 value did not
resolve that reporting-window mismatch.

The launch calculation was `$14.73 + $85.27 = $100.00`. Because its prior-cost
input excluded earlier spend, it did **not** establish a $100 cumulative cap.

For the new campaign, the September 5 reporting range showed 0 impressions,
0 clicks, $0.00 cost, and 0.00 conversions at the final readback. Reporting is
not real-time, so these are launch-time observations rather than a lasting
zero-result claim.

## September 5 followthrough — reconciled and saved

A subsequent Google Ads **all-time** readback, displayed as **August 23 through
September 5, 2026**, showed:

| Campaign | Observed state | Impressions | Clicks | Cost | Recorded conversions |
| --- | --- | ---: | ---: | ---: | ---: |
| Prior campaign, ended September 3 | Ended | 98 | 5 | $24.61 | 0 |
| Orlando Contractor Review, September 5–14 | Enabled — Eligible (Limited) | 0 | 0 | $0.00 | 0 |

The successor's diagnostic was **Missing enough relevant keywords**. Its
enabled status does not establish that it has served, and zero recorded
conversions does not establish that every possible customer interaction was
measured.

After Google Ads identity verification, the successor campaign-total budget
was **saved and read back as $75.39**. This enforces the original cumulative
ceiling using the reconciled prior cost:

`$24.61 prior cost + $75.39 successor campaign-total budget = $100.00 aggregate ceiling`

The former $85.27 successor budget would have allowed $109.88 aggregate
exposure with that prior cost; this was potential exposure, not observed spend.
The saved $75.39 total supersedes the launch budget and calculation above.
These are dated account observations; future reporting can change.

## September 5, approximately 11:07 PM Pacific — delivery diagnostics

The campaign-scoped Google Ads pages showed all six reviewed positive keywords
**Enabled — Eligible**, the single ad group **Enabled — Eligible**, and the
responsive search ad **Enabled — Eligible** with **Average** ad strength.
The ad's final URL matched the contractor-review destination documented below.
The seven saved schedule rows were each **6:00 AM–7:00 PM Pacific**, with no
bid adjustments. This check occurred outside the delivery window; the next
scheduled window starts September 6 at 6:00 AM Pacific / 9:00 AM Eastern.

The campaign still reported **Eligible (Limited) — Missing enough relevant
keywords**, but the individual keyword and ad statuses did not identify a
disapproval, paused entity, or missing positive-keyword setup. An informational
account card referred to a $0 budget; the campaign's saved total-budget field
and campaign row both showed **$75.39**, so that card was not treated as evidence
to increase spending or change the budget type.

No keyword, bid, location, schedule, or ad-copy change was made during this
diagnostic pass. The reason for zero first-day impressions is not conclusively
established. Google's [Search low-traffic guidance](https://support.google.com/google-ads/answer/9208915?hl=en)
notes that new campaigns can take time to begin serving. Assess delivery during
the saved schedule before revising the controlled test.

## Search intent and safeguards

The six live positive keywords are the reviewed exact/phrase set:

- `[contractor website design]`
- `"website design for contractors"`
- `[construction company website design]`
- `"contractor website designer"`
- `"web design for construction companies"`
- `"home service website design"`

The 52 entries in
[`orlando-contractor-negatives-2026-09-04.txt`](orlando-contractor-negatives-2026-09-04.txt)
were saved at **campaign level**. Google displayed `1 - 10 of 52` and
`Your negative keywords were created.` No positive keyword appears in that
negative list.

## Ad and destination

One responsive search ad was created with the reviewed 10 headlines and four
descriptions from
[`orlando-contractor-review-checkpoint-2026-09-04.md`](orlando-contractor-review-checkpoint-2026-09-04.md).
The saved display path is `contractor/review`. The saved final URL is:

`https://leonbuilds.org/missed-lead-recovery?utm_source=google&utm_medium=cpc&utm_campaign=orlando-contractor-review-v1&utm_term={keyword}&utm_content=search-contractor-rsa-a`

Campaign URL options showed no additional suffix or template, so the inline
UTMs are not duplicated at campaign level. The live destination had already
passed desktop and mobile review, exposed the free three-point review and the
$1,500 starting scope, and preserved the quote and booking conversion paths.

## Evidence boundary and next review

The launch `Eligible (Learning)` status and subsequent `Eligible (Limited)`
status do not prove ad delivery, policy stability, conversion tracking, lead
quality, or client acquisition. No synthetic lead or production conversion was
sent.

Review disclosed search terms, spend, and first-party quote or booking receipts
before changing keywords, geography, bids, budget, dates, conversion goals, or
landing-page copy. Keep the aggregate $100 media ceiling intact.
