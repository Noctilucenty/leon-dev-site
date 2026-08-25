# Leon Builds Google Search live checkpoint — 2026-08-24 PT

This record reconciles the frozen offline build pack with the separately
owner-authorized live Google Ads campaign. The Google Ads account remains the
authority for delivery, spend and policy state; this file is a dated observation,
not a claim that the campaign produced traffic or clients.

## Verified pre-start state

- Campaign: `LB | BA | Search | Contractor Websites | 2026-08-25`
- Live campaign ID: `24176728247`
- State: published and enabled; `Pending` before its scheduled start
- Flight: August 25 through September 3, 2026
- Schedule: 6:00 AM–10:00 PM Pacific Time
- Budget: $100 campaign total, not $100 per day
- Bidding: Maximize clicks with a $5 maximum CPC
- Inventory: Google Search only
- Location: presence-only targeting across the approved nine Bay Area counties
- Search intent: eight exact/phrase entries across four contractor website themes
- Safeguards: 43 reviewed campaign-level negative keywords; the held phrases
  `near me`, `home repair`, and `emergency service` remain excluded from the
  negative list so legitimate local contractor intent is not pre-emptively blocked
- Observed before start: $0 spend, 0 impressions, 0 clicks and no ad-attributed
  leads, bookings or clients

The RSA's visible `/contractors/follow-up` text is a display path, not a public
site route. Its actual final URL is the approved working destination:

`https://leonbuilds.org/missed-lead-recovery?utm_source=google&utm_medium=cpc&utm_campaign=ba-missed-lead-recovery-v1&utm_term=home_services&utm_content=search-hs-rsa-a`

That URL returned HTTP 200 during the final audit.

## Measurement state

The four live Google Ads actions and their intended hierarchy are:

1. `LB | Quote Submitted` — Primary, count one
2. `LB | Consultation Booked` — Primary, count one
3. `LB | Phone Click` — Secondary observation, count one
4. `LB | WhatsApp Click` — Secondary observation, count one

The site uses the real Google destination IDs, requires an explicit measurement
choice before loading the tag, sends no contact fields in the Google event
payload, and deduplicates quote receipts, booking UIDs, and contact clicks. The
implementation and all four event paths passed deterministic tests. Google Ads
still had no first real conversion event before launch, so an inactive or
misconfigured-looking platform diagnostic must not be rewritten as a confirmed
conversion or client. No synthetic lead or production conversion was sent merely
to turn that diagnostic green.

Enhanced Conversions remains off. This preserves the explicit no-customer-data
boundary: no hashed customer email or phone is sent to Google. The consented
`ad_user_data` signal used for ordinary Ads attribution is separate from Enhanced
Conversions; analytics storage and ad personalization remain denied.

The live funnel health check reported durable acquisition storage and the Cal
webhook configured. Lead email transport was ready but still honestly labeled
`configured_unverified`; no inbox-delivery claim was manufactured. Repeated
submissions from the one earlier session remain one possible inquiry, not three
clients.

## What this experiment can establish

This $100 flight is a measurement baseline, not evidence that Leon Builds can
already acquire 1–10 clients each month. Judge the result in order:

1. impressions and eligible search terms;
2. qualified landing-page visits;
3. accepted quote receipts or authoritative Cal bookings;
4. attended and qualified conversations;
5. won clients recorded once each.

If delivery is too sparse, use the separate metro research for a later,
separately funded experiment. Do not expand this campaign, borrow its budget for
the app-development draft, count contact clicks as leads, or touch any Curio
account.
