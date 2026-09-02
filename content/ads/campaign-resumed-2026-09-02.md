# Existing Google Search campaign resumed — September 2, 2026

## Saved action and observed result

The owner authorized resuming when the readiness checks passed. At approximately
**4:06 PM Pacific** (`2026-09-02T23:06:55Z`), the existing campaign status was
changed from Paused to Enabled and saved. No new campaign was created.

After a full page reload, Google Ads showed:

- Campaign `LB | Orlando + Phoenix | Search | Contractor Websites | 2026-08-25`:
  **Enabled; Eligible (Limited)**, with **Bid setting limited**.
- Ad group `Contractor Websites | Exact+Phrase`: **Enabled; Eligible**.
- The clean replacement responsive search ad: **Enabled; Eligible**.
- The previous overdue-payment hold was absent. The billing card showed
  **-$13.66** and no upcoming payments. This credit is separate from media spend
  and does not increase the approved campaign budget. No payment was made during
  this activation step.

Enabled/Eligible is configuration evidence, not proof of new impressions, clicks,
inquiries, or clients after resumption. Reporting is not real-time.

## Preserved spending and delivery controls

- **$100 campaign-total budget**, not a daily budget or a new $100 allocation.
- Original dates: **August 25–September 3, 2026**. No extension.
- **Maximize clicks, maximum CPC $5**; the checked bid-limit control showed 5.00.
  The resulting delivery limitation was accepted rather than raising the bid.
- **Google Search only**; AI Max remains off.
- All seven days: **6 AM–10 PM Pacific**, with no schedule bid adjustments.
- Existing four DMAs unchanged: Orlando-Daytona Beach-Melbourne, Phoenix,
  San Francisco-Oakland-San Jose, and Seattle-Tacoma. Presence-only targeting
  and the campaign URL suffix were inspected in the preceding same-day audit;
  neither was changed during activation.
- The same-day lifetime snapshot showed **$14.79 spent**, leaving at most
  **$85.21** within the original allocation. The activation table's default
  August 26–September 1 window also showed $14.79, 3 clicks, 68 impressions,
  and zero Ads conversions; it is not the lifetime window.

A campaign-total budget has no daily ceiling. The remaining allocation is a
maximum, not an instruction to exhaust it before the September 3 end date.
No Meta or separate app-development campaign was enabled or funded.

## Ad and landing-page checks

The Ads table did not reliably expose rows. The Overview ad carousel and its
accessible editor shortcut provided a read-only alternative. No ad edits were
saved while checking these records.

- Clean replacement RSA `822269379998`: enabled, final URL
  `https://leonbuilds.org/missed-lead-recovery`; ad-level tracking template and
  final-URL suffix blank, so it inherits the existing campaign suffix. No
  separate mobile URL. Ad strength was **Average**, not a new performance result.
- Older metro RSA `822240378944`: **already paused**, including its older inline
  UTM final URL. This resolves the earlier audit's unverified duplicate cleanup.
- Legacy Bay Area RSA: **already paused** in the Overview carousel.
- The enabled ad's four sitelinks matched its contractor offer:
  - Work & Project Examples: `https://leonbuilds.org/work`
  - Book A 15-Minute Call:
    `https://leonbuilds.org/call?service=contractor-lead-recovery`
  - Free 3-Point Site Review:
    `https://leonbuilds.org/quote?service=contractor-lead-recovery`
  - See The $1,500 Scope:
    `https://leonbuilds.org/missed-lead-recovery#scope`

The deployed landing page and `assist.js` matched the reviewed main checkout
`a1029d3`. The contractor workflow is labelled illustrative. Supporting technical
projects are not presented as measured contractor conversion case studies.

## Measurement and privacy checks

- Google tag `AW-18407115426`: **Excellent**, sending data, no issues detected.
- Goals > Settings: **Turn on enhanced conversions unchecked**; enhanced
  conversions for leads not configured; customer-data terms not accepted.
- Google tag > Allow user-provided data capabilities: **unchecked**. No account
  privacy setting was changed, and no customer-data terms were accepted.
- Consent-gated deployed integration and real action labels were checked.
- Quote submitted and consultation booked remain **Primary, One**; phone and
  WhatsApp clicks remain **Secondary, One**. The legacy inactive form action
  stays outside account-level goals. No diagnostic clicks were promoted.
- Backend health reports durable storage, configured Cal webhook, and verified
  email delivery. The independent focused readiness audit passed **84 tests**
  (20 Python and 64 Node) and found no technical measurement blocker.
- No fake click identifiers or synthetic Google Ads conversions were submitted.

The local acquisition exports remain incomplete. Verified customer, qualified,
and won counts are still unknown. Three historical clicks and zero Ads conversions
are insufficient to infer that the offer cannot convert; they do not justify a
client forecast either. Prospective measurement readiness supported resuming the
already-approved bounded test, not claiming historical attribution is complete.

## Scope boundaries and next decisions

Only campaign status changed in this activation step. Budget, flight dates,
geography, keywords, negatives, copy, ad statuses, billing methods, conversion
roles, and privacy settings were not changed. The narrow negative candidates and
other acquisition work in the [earlier audit](live-campaign-checkpoint-2026-09-02.md)
remain separate unfinished items.

At the existing end date, assess actual search terms, consented sessions, genuine
inquiries, and qualified outcomes. Any flight extension, new test, or higher
spend limit needs a separate decision. Do not silently restart after September 3.
