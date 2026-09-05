# Leon Builds Google Search Orlando contractor review checkpoint — 2026-09-04 PT

**Status: PREPARED — NOT CREATED — DO NOT ENABLE BEFORE ACTION-TIME CONFIRMATION**

This record defines one proposed Orlando Search campaign for the public contractor
Website + Automation offer. It is a review artifact, not evidence that a campaign
exists, is eligible, has served, or has spent. Google Ads remains the authority
for billing, policy, delivery, and saved configuration.

## Decision and spend boundary

- Proposed campaign: `LB | Orlando | Search | Contractor Review | 2026-09-05`.
- Proposed state: create paused, read every saved control back, and enable only
  after the account-time checks below and the owner's action-time confirmation.
- Proposed flight: September 5 through September 14, 2026, inclusive, in the
  Google Ads account timezone.
- Proposed campaign-total budget: **at most $85.27**.
- The new total is `min($85.27, $100.00 - freshly reconciled lifetime cost of the
  ended campaign)`. It is not a second allocation. Cumulative media exposure
  across the ended campaign and this successor must remain at or below the
  original **$100 total** ceiling.
- The September 4 account view showed $14.73 lifetime cost, while the September 2
  checkpoint showed $14.79. Recheck immediately before creation and use the lower
  resulting remainder. If cost cannot be reconciled, do not enable.
- Confirm the prior campaign remains ended and unable to serve. Do not extend or
  reactivate it.
- Use Campaign total budget only. Do not substitute an average daily budget if
  that option is unavailable.

## Prepared campaign configuration

| Field | Prepared value | Action-time proof required |
| --- | --- | --- |
| Account | Leon Builds, customer ID ending `8433` | Confirm the full customer ID before any save |
| Campaign | `LB | Orlando | Search | Contractor Review | 2026-09-05` | Exact saved name and campaign ID |
| Type | Search | Exact live type |
| Goal | Leads | Only the reviewed conversion actions below may be in Conversions |
| State | Paused until readback; enable only in the confirmed action | Read back campaign, ad group, RSA, keyword, and asset states |
| Budget type | Campaign total budget | Confirm the UI did not create an average daily budget |
| Total | Maximum `$85.27`, reduced if the fresh cumulative-cap calculation requires it | Record prior spend and the resulting aggregate ceiling |
| Dates | Sep 5–Sep 14, 2026 inclusive | Confirm account timezone and exact saved dates |
| Schedule | Daily, 6:00 AM–7:00 PM Pacific / 9:00 AM–10:00 PM Orlando | Confirm the account uses Pacific time and the saved schedule has no bid adjustments |
| Bidding | Maximize Clicks, maximum CPC `$5` | Confirm exact saved bid ceiling |
| Networks | Google Search only | Search Partners off; Display off |
| Geography | Orlando–Daytona Beach–Melbourne, FL DMA only | Record Google geo target ID; remove every other location |
| Location option | Presence: people in or regularly in the targeted location | Confirm advanced setting in the live UI |
| Language | English | Confirm explicitly |
| Expansion | AI Max, broad-match expansion, automatically created assets, text customization, and final-URL expansion off | Confirm each available live control |

The schedule covers the Orlando daytime and evening without spending after 10 PM
local time. The offer does not promise a response within the ad schedule.

## Prepared keyword set

| Match | Keyword |
| --- | --- |
| Exact | `contractor website design` |
| Phrase | `website design for contractors` |
| Exact | `construction company website design` |
| Phrase | `contractor website designer` |
| Phrase | `web design for construction companies` |
| Phrase | `home service website design` |

Phrase match can reach semantically related searches. Review every disclosed paid
search term; do not describe these six entries as six exact queries.

## Negative-keyword set

Apply the exact bulk list in
[`orlando-contractor-negatives-2026-09-04.txt`](orlando-contractor-negatives-2026-09-04.txt).
It carries forward the 43 reviewed campaign exclusions and three contractor-group
cross-niche exclusions from the frozen build pack, then adds six exact terms from
the prior campaign's disclosed search-term review. A new campaign does not inherit
the old campaign's campaign-level negatives automatically.

The prior draft candidates `[best construction websites]`,
`[construction portfolio website]`, and `[plumber landing page]` are not included:
the first misses the actually observed longer query, and the latter two have no
documented search-term evidence and can express buyer intent. Negative exact match
does not cover added words or close variants. Confirm no positive-keyword conflict
before saving.

## Responsive search ad

One RSA: `search-contractor-rsa-a`. No asset is pinned unless the final
combination preview reveals ambiguity.

| ID | Headline | Characters |
| --- | --- | ---: |
| H01 | Contractor Website Design | 25 |
| H02 | Website + Lead Follow-Up | 24 |
| H03 | For Orlando Contractors | 23 |
| H04 | Make Estimate Requests Easy | 27 |
| H05 | Know Which Leads Need Reply | 27 |
| H06 | Fixed Scope From $1,500 | 23 |
| H07 | Work Directly With Leon | 23 |
| H08 | Mobile-Friendly Estimate Form | 29 |
| H09 | Get A Free 3-Point Review | 25 |
| H10 | Written Fixed Quote First | 25 |

| ID | Description | Characters |
| --- | --- | ---: |
| D01 | A focused contractor site, estimate form and follow-up flow built around your team. | 83 |
| D02 | Turn a generic contact form into a clear estimate request and follow-up process. | 80 |
| D03 | Fixed scope from $1,500. Get the price and schedule in writing before work begins. | 82 |
| D04 | Work directly with Leon. Get three specific observations about your current website. | 84 |

All assets fit the 30-character headline and 90-character description limits.
Preview mixed combinations, especially the free-review and `$1,500` build assets,
so a free review cannot be mistaken for a free build.

## Destination and attribution

Final URL:

`https://leonbuilds.org/missed-lead-recovery?utm_source=google&utm_medium=cpc&utm_campaign=orlando-contractor-review-v1&utm_term={keyword}&utm_content=search-contractor-rsa-a`

- Keep campaign, ad-group, ad, keyword, and account tracking templates and
  final-URL suffixes blank unless each layer is deliberately reconciled. The
  inline URL already carries all five UTMs.
- Allow only genuine platform-added click identifiers. Never insert a sample
  `gclid`, `gbraid`, or `wbraid`.
- Run Google's URL test and verify the expanded URL stays on `leonbuilds.org`,
  returns HTTP 200 to Google AdsBot, and preserves attribution through the review
  submission and booking paths.
- Record every sitelink, callout, structured snippet, business-name asset, logo,
  and account-level automatically associated asset. Do not allow unrelated app,
  restaurant, Technical Build Partner, or legacy homepage assets into this
  campaign.

## Offer and policy reconciliation

- The destination must visibly offer the contractor Website + Automation scope
  from `$1,500` and the free three-point website review before enablement.
- The review is free, requires no payment or commitment, and delivers three
  specific observations by email.
- `For Orlando Contractors` describes the target audience. It does not claim
  Leon Builds is Orlando-based or has an Orlando office; the site identifies Leon
  as California-based and serving U.S. businesses remotely.
- The copy promises a website, estimate intake, follow-up workflow, status
  visibility, and a written quote. It does not promise leads, bookings, revenue,
  rankings, response time, or a contractor outcome.
- Do not reintroduce `instant`, `never miss a lead`, `more leads`, a guaranteed
  result, or a 10-day build promise. The ten days here are the media flight.

## Conversion and privacy controls

- Primary, count one: `LB | Quote Submitted` and
  `LB | Consultation Booked`.
- Secondary, count one: `LB | Phone Click` and `LB | WhatsApp Click`.
- Keep the legacy inactive lead-form action outside campaign goals. Do not promote
  diagnostic clicks or form starts to primary.
- Confirm one accepted review request produces one opaque receipt-backed
  conversion and one authoritative booking UID produces one booking conversion.
- Keep enhanced conversions and user-provided-data collection off unless
  separately reviewed and authorized. Do not place contact data in URLs or Google
  event payloads.

## Action-time launch gates

- [ ] Correct Leon Builds account verified.
- [ ] Prior campaign confirmed ended and unable to spend.
- [ ] Prior lifetime cost rechecked; new total reduced so aggregate exposure is at
  most `$100`.
- [ ] Campaign total budget is available; no daily-budget substitute.
- [ ] Sep 5–Sep 14 dates, Pacific account timezone, and daily 6 AM–7 PM schedule
  verified.
- [ ] Orlando DMA target and geo ID verified; presence-only selected; no other
  geography remains.
- [ ] Search only; Search Partners, Display, AI Max, broad expansion, automatic
  text, and final-URL expansion off.
- [ ] Exact negative list attached with no positive conflict.
- [ ] Live landing and review path checked on mobile and desktop; free review and
  `$1,500` starting scope are easy to find.
- [ ] URL test passes without duplicate UTMs or a cross-domain redirect.
- [ ] Conversion-action roles and consent state verified.
- [ ] Every RSA combination is accurate and policy-eligible.
- [ ] Campaign, ad group, RSA, keywords, negatives, schedule, and assets created
  paused and read back after reload.
- [ ] Owner gives final action-time confirmation for the specified spend-capable
  action.
- [ ] After enablement, reload and write a separate observed live checkpoint.

## Live action receipt — leave blank until observed

- Campaign ID: `UNOBSERVED`
- Created at: `UNOBSERVED`
- Enabled at: `UNOBSERVED`
- Saved campaign status: `UNOBSERVED`
- Saved ad-group status: `UNOBSERVED`
- Saved RSA status and policy state: `UNOBSERVED`
- Reconciled prior spend: `UNOBSERVED`
- Enforced aggregate media ceiling: `UNOBSERVED`
- Starting impressions, clicks, spend, and conversions: `UNOBSERVED`

Do not replace `UNOBSERVED` with zero. A blank or delayed Google report is
unknown until the account is read back.

## Post-flight review

Use the prepared private run manifest scoped to
`orlando-contractor-review-v1`, source `google`, and September 5–14. Reconcile
Google clicks and spend, complete first-party exports, accepted review receipts,
authoritative bookings, qualified calls, and won clients. Search terms and click
volume are diagnostic; they do not establish client acquisition by themselves.
