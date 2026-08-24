# Organic and outbound execution pack

**Status: DRAFT — UNSENT**

**NO SEND AUTHORIZATION.** These are offline planning and copy-review assets.
Nothing in this folder is evidence that a message, post, listing, call, or live
account action happened. Copying a draft into a live channel requires a separate
human review and decision outside this repository.

## Safety contract

- Do not publish, send, call, text, upload, import, or delete anything merely
  because it appears in this folder.
- Never commit a real prospect, email address, phone number, private conversation,
  or scraped record here. Copy `crm-template.csv` to an approved private system
  before adding real data.
- Every direct message is one-to-one and manually researched. No scraping, bought
  lists, mail merge, automated DMs, cold SMS, or cold WhatsApp/WeChat outreach.
- Check the current rules of each group or directory before any later publication.
- An opt-out, complaint, platform warning, or clear lack of fit stops outreach as
  described in `qualification-and-stop-rules.md`.
- The outreach and community drafts are deliberately price-free. If a recipient
  asks about price, use the current site page or the canonical snapshot below;
  never type a new figure from memory.
- No draft promises rankings, revenue, calendar volume, response speed, savings,
  or a business result that has not been measured and documented.

Run the local gate before reviewing any draft for use:

```bash
python3 tools/check_outbound_pack.py
```

## Canonical offer and price snapshot

This mirrors `FLOORS` in `tools/check_prices.py`. The gate fails whenever the
site changes and this snapshot does not. It is a reference, not a rate-card post.

<!-- floor: small fixes=75 -->
<!-- floor: websites=300 -->
<!-- floor: seo=300 -->
<!-- floor: business-automation=500 -->
<!-- floor: booking-systems=600 -->
<!-- floor: websites-backend=625 -->
<!-- floor: business-dashboards=750 -->
<!-- floor: ai-chatbots=750 -->
<!-- floor: ai-phone-agents=1000 -->
<!-- floor: custom-software=1500 -->
<!-- floor: mobile-apps=3500 -->
<!-- floor: ongoing=400 -->

| Published starting point | Canonical floor |
|---|---:|
| Small fixes | $75+ |
| Business website | $300+ |
| SEO and AI search | $300+ |
| Ongoing work | $400+/month |
| Workflow automation | $500+ |
| Booking or direct ordering | $600+ |
| Website with accounts and a database | $625+ |
| Dashboard or internal tool | $750+ |
| AI chatbot | $750+ |
| AI phone agent | $1,000+ |
| Custom software | $1,500+ |
| iPhone and Android app | $3,500+ |

All are floors, not quotes. A written scope, timing, and fixed price for the
agreed work come before a project begins. Changed scope is priced and approved
in writing before additional work begins. Provider charges and terms still
apply where relevant.

## The offer under test

The site can build many things; the outreach should open with one business
problem. The primary hypothesis is:

> Leon maps and fixes the path from a new inquiry to owner follow-up for a local
> service business: a clear mobile action, confirmation, one lead view, booking,
> and the smallest useful automation around the tools already in use. The work
> is scoped in writing, built directly by Leon, and handed over without pretending
> custom software is necessary when an existing tool is the better answer.

The three-wedge test applies that offer to home services, auto repair, and
restaurants/food operations. English, Spanish, Portuguese, and Simplified
Chinese are communication capabilities, not separate promises of demand or fit.

## Pack map

- `10-day-bakeoff.md` — controlled three-wedge test.
- `30-day-calendar.md` — daily execution and follow-up plan.
- `outreach-scripts.md` — warm requests, referral forwards, and three four-touch
  cold-email sequences.
- `community-and-partners.md` — value-first community posts and partner system.
- `app-development-community-drafts.md` — private-review app-development posts,
  comment-first guardrails, manual current-rules gate, and source URL templates.
- `qualification-and-stop-rules.md` — call rubric, channel gates, and stop rules.
- `source-tag-schema.csv` — synthetic attribution examples that match the live
  site's existing `?s=` capture.
- `crm-template.csv` — one synthetic sample row plus the CRM schema below.

## CRM field schema

| Field group | Fields | Rule |
|---|---|---|
| Identity | `lead_id`, contact, organization, role, website, city, language | Real data belongs only in an approved private copy, never this tracked template. |
| Targeting | `wedge`, source fields, all five UTMs, click IDs, observed problem, personalization note | Record an observable fact; label any interpretation as an inference. Never invent a click ID. |
| Permission | `permission_basis`, `do_not_contact`, `opt_out_date` | An opt-out overrides every next action. |
| Cadence | four touch dates and statuses, last response | No more than four cold touches; never fake a reply thread. |
| Funnel | booking, show, qualification, proposal, outcome | Count held qualified calls, proposals, wins, and revenue—not opens. |
| Operations | next action, date, notes | Do not store sensitive customer or project data. |

## Attribution rule

The current pipeline retains all five UTM fields—`utm_source`, `utm_medium`,
`utm_campaign`, `utm_term`, and `utm_content`—plus supported ad click IDs. New
organic/outbound links should use all five UTMs and omit the legacy `s` alias.
The composite `source_tag` belongs in `utm_content`; this gives every variant an
exact identifier while `utm_source` and `utm_medium` remain useful channel groups.

Paid platforms may append `gclid`, `gbraid`, `wbraid`, `fbclid`, or `msclkid`.
Preserve a genuine platform value, but never invent one or type one into an
organic/outbound link.

Example structure only:

```text
https://leonbuilds.org/services/business-automation?utm_source=manual_email&utm_medium=outbound&utm_campaign=cal30d-bakeoff-v1&utm_term=home_services&utm_content=obem-hs-en-seqa
```

Never put a person's name, email, phone number, company name, or other personal
data in a source tag or URL.

## Campaign asset map

The six price-free campaign cards below are generated by
`tools/make_social.py`; do not create a second generator or hand-edit their PNGs.
They are offline assets until a separate human channel review and publication
decision occurs.

| File | Angle | Best initial match |
|---|---|---|
| `assets/social/ad_01_contractor_after_hours.png` | What happens to a late quote request? | Home-service after-hours inquiry hypothesis. |
| `assets/social/ad_02_contractor_flow.png` | Inquiry to booked estimate without phone tag. | Home-service workflow explanation. |
| `assets/social/ad_03_auto_estimates.png` | Voicemail is not an estimate workflow. | Auto-repair intake and status hypothesis. |
| `assets/social/ad_04_restaurant_direct.png` | Direct orders can continue while the phone is busy. | Restaurant/food ordering hypothesis. |
| `assets/social/ad_05_founder_direct.png` | The buyer works with the developer writing the code. | Partner, referral, and founder-direct proof. |
| `assets/social/ad_06_lead_leak_review.png` | Find one weak handoff and the smallest sensible next step. | Community clinic or review invitation. |

Select an asset because it matches the message being tested, not merely because
it is available. An image does not convert a community post into an allowed ad;
the current channel rules still control whether it can be used.

## Human preflight before any later use

1. Confirm the prospect, group, and channel are genuinely in scope.
2. Confirm every observation against the current public page; do not submit a
   fake lead or impersonate a customer to test a business.
3. Confirm the recipient has not opted out and is not on a suppression list.
4. For commercial email, add the real valid postal address and complete the
   separate legal/compliance review. The placeholder intentionally blocks copy
   from being treated as send-ready.
5. For a community post, read the current group rules and remove the link if
   self-promotion is not allowed.
6. Generate or select a unique source tag without personal data.
7. Re-run `python3 tools/check_outbound_pack.py` and re-read the final copy.
8. A human—not a script—decides whether and when to use it.
