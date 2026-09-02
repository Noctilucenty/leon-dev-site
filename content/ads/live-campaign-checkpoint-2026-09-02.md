# Leon Builds acquisition checkpoint — 2026-09-02 PT

Read-only live account inspection plus scoped website/reporting improvements.
Google Ads is the authority for billing, serving, policy, and spend. This note
does not enable an ad, authorize a payment, or reset the existing budget.

## Live campaign

- Account: Leon Builds, `794-705-8433`.
- Campaign: `LB | Orlando + Phoenix | Search | Contractor Websites | 2026-08-25`.
- Status: **Paused**. The account also displays an overdue-payment serving hold.
- Billing overview balance: **$6.34**, observed September 2. No payment made.
- Campaign total budget: **$100**; dates: **August 25–September 3, 2026**.
- Bidding: Maximize clicks, maximum CPC **$5**; UI says bid setting limited.
- Network: Google Search only. Language: English. AI Max, broad-match expansion,
  automatically created assets, text customization, and final-URL expansion off.
- Locations: Orlando-Daytona Beach-Melbourne, Phoenix, San Francisco-Oakland-San
  Jose, and Seattle-Tacoma DMAs. Presence-only targeting is selected.
- The two-metro name is stale: the four-metro expansion was previously authorized
  and recorded on August 26. Do not treat a stale name as unauthorized targeting.
- Campaign tracking template is blank; final-URL suffix is:
  `utm_source=google&utm_medium=cpc&utm_campaign=metro-missed-lead-recovery-v1&utm_term={keyword}&utm_content={creative}`.

Lifetime report selected **August 23–September 2, 2026**:

| Measure | Observed |
| --- | ---: |
| Impressions | 70 |
| Clicks | 3 |
| CTR | 4.29% |
| Spend | $14.79 |
| Average CPC | $4.93 |
| Google Ads conversions | 0.00 |

The unspent difference is **$85.21**, not an additional $100 allocation.
Three clicks cannot establish a reliable conversion-rate estimate or explain a lack
of clients. Google Ads conversions are not the same as verified CRM outcomes.

## Search quality: evidence and limits

The Search terms table defaulted to **August 26–September 1**, showing 68
impressions, 3 clicks, and the same $14.79 spend. This is not the lifetime window.

- Disclosed paid query: `construction company website design`, 1 click, $4.95.
  This is relevant to the advertised offer; hiring intent is an interpretation,
  not a confirmed purchase or qualified lead.
- `Other search terms`: 2 clicks, $9.84. Their exact queries were not disclosed
  in the table. Do not mark all three clicks reviewed or label the hidden two junk.
- Already marked excluded: `plumbing website examples`, `best construction
  company websites`, `best general contractor website`, and `construction
  landing page examples`. These rows showed zero clicks and zero cost.
- `home care website design` remains unexcluded: 1 impression, zero clicks,
  zero cost. It is a plausible healthcare mismatch for this contractor campaign.
- `general contractor website examples` remains unexcluded: 2 impressions,
  zero clicks, zero cost. It suggests research rather than a clear hiring request.

Narrow, review-ready negative candidates: exact `[home care website design]`
and `[general contractor website examples]`. These have **not** been added.
Do not blanket-exclude `best`, `cost`, or `website`, or call impression-only
queries wasted spend. Existing exclusions must be checked again before saving
anything to avoid duplicates or positive-keyword conflicts.

## Conversion actions

The action table was directly inspected:

| Action | Optimization | Count | Tracking status |
| --- | --- | --- | --- |
| LB \| Quote Submitted | Primary | One | No recent conversions |
| LB \| Consultation Booked | Primary | One | No recent conversions |
| LB \| Phone Click | Secondary | One | No recent conversions |
| LB \| WhatsApp Click | Secondary | One | No recent conversions |
| Submit lead form (legacy) | Secondary, outside account-level goals | Every | Inactive |

The overview's extra unverified/inactive item is consistent with the legacy
action, not evidence that the four named Leon Builds actions are absent. The
Contact goal has zero primary actions and a misconfigured label; do not promote
phone or WhatsApp clicks to primary just to clear that label. Preserve quote and
booking as the real business conversions. No synthetic ad conversions were sent.

Backend health now reports durable storage, a configured Cal webhook, and verified
lead email delivery (`2026-09-02T01:25:26.960Z`). This supersedes older unconfigured
webhook/unverified-delivery notes, but does not prove real customer acquisition.

The local event, lead, and acquisition exports are not confirmed complete. Their
funnel stages remain **unknown**, not zero. Complete private exports, exclude
synthetic QA receipts/bookings, and reconcile real inquiries before claiming a
conversion-rate diagnosis or reporting qualified/won clients.

## Implemented in this acquisition change

1. Put a clearly labelled four-step illustrative estimate/follow-up flow on
   `/missed-lead-recovery`. The unrelated location-planning project remains only
   supporting technical work, explicitly not a contractor conversion case study.
2. Relabel existing approved feedback accurately; preserve prices, scope, CTAs,
   and testimonial wording.
3. Keep incomplete or invalid exports out of reported funnel totals and rates;
   expose partial observations only as diagnostics. Add regression tests.
4. Correct two unsent outreach drafts: BEASTY PAGES has a demonstration cart,
   not live payment or kitchen operations. No messages sent.
5. Make client-success tests initialize isolated fixture state instead of copying
   private runtime data, so the complete suite can run from a clean checkout.

No live ad copy, negative keywords, status, spend controls, flight dates, or
billing settings were changed in this audit. Individual RSA final-URL cleanup
from the August 25 checkpoint is still unverified; the Ads grid did not reliably
expose its rows after refresh. Recheck before enabling the campaign.

## Next actions, in order

1. **Resolve the $6.34 billing hold.** Payment requires a separate, exact
   confirmation or owner action; do not change a payment method or auto-pay rules.
2. **Decide the flight before resuming.** The approved flight ends September 3.
   Do not silently extend it or start a fresh $100 test. A campaign-total budget
   has no daily cap and may spend faster close to its end date; the remaining
   $85.21 is a ceiling, not a target to exhaust tomorrow.
3. **Recheck the three RSA rows and current negatives**, then request exact
   approval for any final-URL/duplicate-ad cleanup and narrow exclusions.
   Preserve $5 max CPC, Search-only, presence-only, existing geography, and the
   primary/secondary conversion split until a deliberate new decision.
4. **Reconcile measurement.** Export the whole review window, match real lead
   receipts to authoritative bookings, and have a human mark qualified/won stages.
   Fill actual delivery costs and acceptable acquisition cost privately; do not
   invent a profitable-CAC threshold or expected close rate.
   Only after measurement and the preceding checks pass should a specific
   restart plan be proposed for approval; an extended flight needs a new explicit
   timing decision while retaining the original total-spend ceiling.
5. **Run a small warm-introduction experiment for Technical Build Partner.**
   Prepare five personal notes to existing clients or trusted contacts after
   checking for earlier messages. Ask who has one manual task they want fixed.
   Use a specific relevant project, one clear next step, and a free short fit
   call. These are suggestions, not sent messages or a revenue forecast.
6. **Deliver the promised free three-point review well.** For each genuine
   request, give three observations about their real site and recommend the
   smallest sensible change. Track reply, fit call, written scope, and outcome.
   Do not use another generic portfolio link as the whole response.
7. **Create relevant proof when real work earns it.** Request permission for a
   short contractor workflow case study after delivery. Use actual results only.
   Keep the new illustrative flow labelled until then.

Do not lower prices, create more general service pages, expand geography, buy
another platform subscription, or claim a 1–10-client monthly forecast based on
three clicks. Keep the Technical Build Partner offer separate from the current
contractor ad destination; promote it through relevant conversations first.

## Reference notes

- [Google: campaign total budgets](https://support.google.com/google-ads/answer/10486938?hl=en)
  explains the total cap, scheduling, and absence of a daily cap.
- [Google: negative keywords](https://support.google.com/google-ads/answer/7102995?hl=en)
  explains focused exclusions and avoiding keyword conflicts.
- [Google: negative keyword matching](https://support.google.com/google-ads/answer/2453972)
  explains why close variants need separate consideration.

These documents guide the plan; they are not evidence of this account's results.
