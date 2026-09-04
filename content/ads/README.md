# Paid campaign build pack

**Status: DRAFT — DISABLED — GOOGLE $100 / 10 CALENDAR DAYS — META $0**

**NO LAUNCH AUTHORIZATION.** This folder is an offline build specification. It
does not authorize creating, enabling, publishing, funding, or changing a live
Google or Meta campaign. No row in these files is evidence that an ad ran.

> **Live-state reconciliation — 2026-08-24 PT:** the owner later gave separate
> launch authorization and one Google Search campaign was published in the live
> Leon Builds account. The CSVs remain a frozen, fail-closed build specification;
> they are not the live-account ledger. See
> [`live-campaign-checkpoint-2026-08-24.md`](live-campaign-checkpoint-2026-08-24.md)
> for the verified pre-start state and its proof limits. Meta and the separate
> app-development draft remain disabled at $0.
>
> **Current live-state reconciliation — 2026-08-25 PT:** see
> [`live-campaign-checkpoint-2026-08-25.md`](live-campaign-checkpoint-2026-08-25.md)
> for the enabled Orlando/Phoenix campaign, paused legacy Bay RSA, clean
> replacement RSA, campaign-total spend controls, zero-spend activation receipt,
> and the remaining earlier-metro-RSA cleanup.
>
> **Current live-state reconciliation — 2026-08-26 PT:** see
> [`live-campaign-checkpoint-2026-08-26.md`](live-campaign-checkpoint-2026-08-26.md)
> for the saved Bay Area and Seattle-Tacoma expansion, the eight added
> phrase-match keywords, unchanged $100 total/$5 CPC controls, and the first
> 10-impression zero-click snapshot.
>
> **Earlier live-state reconciliation — 2026-09-02 PT:** see
> [`live-campaign-checkpoint-2026-09-02.md`](live-campaign-checkpoint-2026-09-02.md)
> for the paused campaign, billing hold, $14.79 lifetime spend, disclosed search
> terms, conversion-action roles, and remaining approval-gated work. This audit
> did not change ads, bidding, locations, billing, or the September 3 end date.
>
> **Latest live state — resumed 2026-09-02, 4:06 PM PT:** see
> [`campaign-resumed-2026-09-02.md`](campaign-resumed-2026-09-02.md).
> Following separate owner authorization and final checks, the existing campaign
> is **Enabled / Eligible (Limited)**, with its $5 bid ceiling, $100 total budget,
> and September 3 end date unchanged. The clean RSA and ad group are eligible;
> both older RSAs remain paused. Billing and privacy checks passed. This is an
> activation receipt, not evidence of new customers or additional spend approval.

## Safety contract

- Keep every campaign, ad group, ad set, ad, and conversion action disabled
  until the launch checklist is separately approved by the account owner.
- The owner-approved paid-media ceiling is **$100 total across 10 calendar
  days**. The entire first-test allocation is assigned to one new Google Search
  campaign using **Campaign total budget**; Meta receives $0 and stays disabled.
  This is not $100 per platform and is not launch authorization.
- Bids, cost goals, exact start/end dates, billing, audiences, and account IDs
  remain unset or unapproved. Do not infer or auto-fill them from these drafts.
- The app-development Search lane is a separate **$0, unscheduled,
  `HOLD_NO_BUDGET` hypothesis**. It may not borrow from the existing $100
  contractor test. It is for Leon Builds business advertising only: never use a
  Curio account, profile, page, community, pixel, audience, billing identity, or
  developer account to distribute it.
- Never type a made-up `gclid`, `gbraid`, `wbraid`, `fbclid`, or another click
  identifier into a URL. Platforms may append genuine identifiers later.
- Do not put prospect or customer information in campaign names, UTMs, URLs,
  assets, spreadsheets, or repository files.
- Do not claim a number of leads, bookings, sales, savings, or revenue. The
  offer improves a response workflow; it does not guarantee business results.
- Before adding Meta or Google advertising technology, complete privacy,
  consent, data-retention, platform-terms, and legal reviews and make the live
  privacy disclosure accurate. This pack is not legal advice.

Run the local, read-only gate before considering any build row:

```bash
python3 tools/check_ads_pack.py
```

## Pack map

- `google-search-build.csv` — one disabled Bay Area Search campaign with a $100
  campaign-total budget over 10 calendar days, one eligible contractor ad group,
  one eligible contractor RSA, four natural contractor website-search themes,
  and preserved alternative/auto/restaurant drafts held for intent, copy, or
  product mismatch. It also contains reviewed negatives, conversion hierarchy,
  and a launch checklist.
- `google-search-app-development-draft.csv` — a separate, zero-allocation app
  development Search hypothesis with two exact/phrase ad groups, two held RSAs,
  45 negatives, full UTM mapping, and twelve blockers. Every row remains
  `HOLD_NO_BUDGET`; it does not share the approved contractor allocation.
- `meta-build.csv` — one disabled Leads-objective plan using a website booking
  conversion, six mapped assets, qualification controls, retargeting gates, and
  a $0 first-test allocation.
- `economics-calculator.csv` — the four owner-approved test controls, blank
  business-economics inputs, spreadsheet formulas, and stop-rule templates.

## Canonical root landing page

Every Google and Meta ad destination in this pack resolves to:

`https://leonbuilds.org/`

The homepage presents Leon Builds' current website and automation offer, including
the Website + Automation starting point of $1,500. Contractor ad copy retains its
narrower estimate-intake, acknowledgment, follow-up, and owner-handoff scope.
Changing the destination does not waive copy/landing review or turn a draft into
launch authorization. Ads must preserve their stated boundaries and must not
recast the work as lead generation, ad management, a call center, or a revenue
promise.

The first test may target Bay Area contractors, but the service itself is
available remotely across the United States. Every auto-shop and restaurant row
is retained as a `HOLD_PRODUCT_MISMATCH` archive and is ineligible until it has a
separately reviewed matching offer and landing page.

## App-development lane — held for a separate decision

The separate app Search draft also maps both ad groups only to:

`https://leonbuilds.org/`

The homepage does not currently present a dedicated app-development offer or the
draft's $3,500 starting point. Every app row therefore remains `HOLD_NO_BUDGET`;
the destination change does not make either RSA eligible. Before any future test,
the landing experience and exact ad combinations need a fresh mobile, desktop,
offer, and truth review. The ad copy must not claim client revenue, downloads,
bookings, or another business result.

The two held intent groups are deliberately narrow:

- `business_app` — buyers explicitly looking for a business or custom app
  developer;
- `ios_android` — buyers explicitly looking for iOS, Android, or cross-platform
  app development.

Both groups use exact and phrase match only. Campaign negatives remove
employment, education, free-code, download, game-engine, DIY-builder, and
platform-support intent. `cost`, `agency`, `freelancer`, and `near me` are not
excluded because they can occur in legitimate buying searches. If this lane is
ever separately authorized, review the live Keyword Planner and Search terms
instead of treating this offline list as current volume or competition data.

The app lane has **no media allocation, schedule, bidding strategy, approved
geography, or launch permission**. It cannot be uploaded, created, funded, or
enabled merely because the CSV passes validation. Any later experiment needs a
new budget decision, its own economics, current platform review, verified
attribution, and explicit owner approval after landing-page and ad previews.

## Attribution contract

Every draft final URL carries all five standard UTM parameters. Contractor
Google and Meta drafts use `utm_campaign=ba-missed-lead-recovery-v1`; the held
app Search draft uses `utm_campaign=us-app-development-draft-v1` so the two
offers cannot be mistaken for one campaign:

- `utm_source`
- `utm_medium`
- the lane-specific `utm_campaign` value above
- `utm_term` for the niche hypothesis
- `utm_content` for the exact ad/RSA variant

The paid campaign name and source tags contain only aggregate planning labels.
Google and Meta click IDs are deliberately absent. Auto-tagging may later add a
real platform ID, which the site is designed to retain; nobody should invent one.

## Conversion hierarchy

1. `won_client` — ultimate business outcome after a reliable consented CRM or
   offline-import process exists; never optimize to this before validation.
2. `qualified_call_held` — preferred quality signal once its definition and
   upload process are consistent.
3. `calendar_booking_success` — initial website-booking conversion candidate;
   verify one confirmed booking UID produces one platform event.
4. `quote_lead_accepted` — secondary lead action, not a booking substitute.
5. Page views, CTA clicks, and form starts — diagnostic only.

Do not count a click, page view, form start, or scheduled-but-invalid event as a
qualified inquiry. The source of truth should progress from confirmed booking
to held qualified call to won client.

## Google mechanics checked on 2026-08-23

- Google says Campaign total budget is available when creating a new Search
  campaign, requires start/end dates, supports a 3–90 day Search flight, cannot
  replace the budget type on an existing campaign, and never bills above the
  campaign total: [About campaign total
  budgets](https://support.google.com/google-ads/answer/10486938?hl=en).
- A normal $10 average daily budget is not the same hard cap: Google documents a
  daily spending limit of up to two times the average daily budget for most
  campaigns. This pack therefore does not use $10/day: [About spending
  limits](https://support.google.com/google-ads/answer/10486637?hl=en).
- Google documents up to 15 RSA headlines and four descriptions, with a
  30-character headline limit, 90-character description limit, and a minimum
  of three headlines and two descriptions: [About responsive search
  ads](https://support.google.com/google-ads/answer/7684791?hl=en).
- Google advises unique assets and describes an 8–10-headline starting point:
  [Set up your ads for
  success](https://support.google.com/google-ads/answer/6167115?hl=en).
- Exact and phrase match are explicitly separated in this small controlled
  test; Google describes the available match types here: [Google Ads keyword
  matching](https://support.google.com/google-ads/answer/14996023?hl=en).
- The campaign uses the advanced location option **Presence: people in or
  regularly in the targeted locations**, not the default Presence-or-Interest
  option: [About advanced location
  options](https://support.google.com/google-ads/answer/1722038?hl=en-GB).
- Apply and maintain negatives, then inspect the actual search-terms report:
  [negative keyword lists](https://support.google.com/google-ads/answer/2453983?hl=en)
  and [search terms
  report](https://support.google.com/google-ads/answer/2472708?hl=en).

For this small first test, only one RSA is eligible so $100 is not split across
two competing drafts. The active exact/phrase themes are `contractor website
design`, `contractor web design`, `website design for contractors`, and `home
service website design`. Unnatural software/form queries remain preserved but
held. The generic `near me` negative also remains preserved but held because it
can appear in a legitimate local B2B website-design search; use the actual
search-terms report before adding narrower consumer-service negatives.

Platform interfaces and policies change. Re-check the live help pages and the
account UI immediately before any separately authorized build. If Campaign total
budget is unavailable in the account, do not substitute a $10/day budget or
enable the campaign; stop and revise the capped plan first.

## Meta mechanics checked on 2026-08-23

- The draft uses **Objective: Leads**, **Conversion location: Website**, and a
  website conversion performance goal, matching Meta's current setup language:
  [Lead ads with website
  forms](https://www.facebook.com/business/ads/ad-objectives/lead-generation/lead-ads-with-forms).
- Meta describes Pixel, Conversions API, and offline conversions as Meta
  Business Tools. None is installed or authorized by this pack: [The Meta
  Business Tools](https://www.facebook.com/help/331509497253087/).
- Meta's current Advantage+ leads documentation says Leads campaigns may use
  Advantage+ defaults and describes CRM quality feedback and custom audiences:
  [Advantage+ leads
  campaigns](https://www.facebook.com/business/ads/meta-advantage-plus/leads).
- Meta describes location as a strict audience control while other audience
  inputs may be suggestions: [Advantage+
  audience](https://www.facebook.com/business/ads/meta-advantage-plus/audience).

No retargeting ad set may be built merely because a suggested traffic count was
reached. The gate requires accurate privacy disclosure and consent handling,
verified event deduplication, a Meta website audience shown as available in the
live account, enough eligible activity for delivery, and explicit approval of
the retention window and exclusions. Those thresholds are account- and
context-dependent, so this pack does not fabricate them.

## Creative compatibility

| Asset | Draft use | State |
|---|---|---|
| `assets/social/ad_01_contractor_after_hours.png` | Contractor after-hours inquiry | Disabled |
| `assets/social/ad_02_contractor_flow.png` | Contractor workflow explanation | Disabled |
| `assets/social/ad_03_auto_estimates.png` | Auto-shop inquiry workflow | **Hold: product/landing mismatch** |
| `assets/social/ad_04_restaurant_direct.png` | Direct ordering | **Hold: message/landing mismatch and product mismatch** |
| `assets/social/ad_05_founder_direct.png` | Auto-shop founder-direct reassurance | **Hold: product/landing mismatch** |
| `assets/social/ad_06_lead_leak_review.png` | Catering/private-event leak review | **Hold: product/landing mismatch** |

The six images are 1080×1350 (4:5). Preview every selected placement in the
live tool. Only the two contractor cards are eligible for review against the
current landing page. The four auto/restaurant cards remain preserved but held.

## Human launch boundary

Passing the validator means the offline pack is internally consistent. It
records the owner's $100/10-calendar-day paid-media ceiling and Google-only first
allocation. It does not approve launch, billing, bids, exact dates, tracking
technology, targeting, copy, creative, privacy posture, or publication. A later
authorized launch still requires a human to complete every checklist row in both
build sheets and re-check the economics with real, privately held business inputs.
