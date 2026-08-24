# Client-acquisition automation

**Status: ACTIVE LOCALLY — EXTERNAL ACTIONS REQUIRE REVIEW**

This repository prepares the work needed to acquire clients without pretending
that a draft was sent, a case study was approved, an ad was launched, or a
Business Profile was eligible. Real prospect and client records stay in the
Git-ignored `private/` directory.

## Operating loop

1. **One product:** `/missed-lead-recovery` is the Contractor Lead Recovery
   System: a focused website plus estimate intake, acknowledgment, short
   follow-up, owner handoff and event log. The published starting scope remains
   $1,500 and the 10-business-day clock starts only after scope, access and copy
   are ready.
2. **Weekday teardown queue:** `tools/outreach_ops.py` selects up to three
   current contractor observations and creates private, short, one-to-one draft
   packets. It has no send capability and blocks weekends, stale evidence,
   duplicate queues and opted-out records.
3. **Weekly useful content:** `tools/content_ops.py` creates one private
   evidence-backed contractor field-note draft per ISO week. It cannot publish
   or modify the sitemap.
4. **Client proof:** `tools/client_success_ops.py` manages evidence, approval,
   review and referral drafts once the client-success pack is configured.
5. **Funnel and ads:** `tools/acquisition_report.py` reads real event and
   opportunity records, reports the weakest measurable transition, and can only
   return pause, iterate or eligible-for-review—not an automatic scale action.
6. **Google Business Profile:** `tools/gbp_gate.py` defaults Leon Builds to
   online-only and blocked. It does not create a profile. Eligibility requires
   real in-person contact, the correct storefront/service-area conditions,
   privately verified address details and owner approval.

## Local commands

```bash
# Validate current private contractor research.
python3 tools/outreach_ops.py audit

# Prepare up to three drafts for a weekday; nothing is sent.
python3 tools/outreach_ops.py prepare --date 2026-08-24 --limit 3

# Record an external outcome only after it really happened.
python3 tools/outreach_ops.py record prospect_example sent --note "manual send recorded"

# Prepare this week's private industry draft; nothing is published.
python3 tools/content_ops.py prepare

# Validate proof/review/referral readiness; nothing is sent or published.
python3 tools/client_success_ops.py check
python3 tools/client_success_ops.py case-study-status

# Read the real funnel and return PAUSE, ITERATE or ELIGIBLE_TO_REVIEW.
python3 tools/acquisition_report.py

# Create and inspect the private GBP eligibility record.
python3 tools/gbp_gate.py init
python3 tools/gbp_gate.py check
```

## Pricing experiment

Do not reduce every public service floor. The $1,500 contractor product is
already a low-friction fixed scope, while the smaller service floors are already
entry-level prices.

If Leon activates it in an individual written proposal, the controlled pilot is
**$1,350 fixed for the first two compatible Contractor Lead Recovery projects**
whose scope is approved and deposit is paid by September 30, 2026. One decision
maker must provide required access, approved copy and implementation feedback
within two business days and attend two 20-minute workflow-review calls.
Third-party fees and added scope remain separate. The public $1,500 starting
scope stays unchanged, and the pilot expires after two projects or the deadline.

The pilot price is compensation for pilot participation only. It is never
conditioned on a Google or LinkedIn review, rating, testimonial, referral,
case-study permission or positive feedback. Those requests remain separate,
optional and honest.

## Non-negotiable gates

- Never guess, scrape or bulk-generate recipient addresses.
- Never send a cold commercial email until the lawful contact path, suppression
  check, real postal address and current compliance review are complete.
- Never publish a client quote, name, star rating, screenshot, or outcome without
  the client's exact approval and supporting evidence.
- Never turn a public-site observation into an invented loss estimate.
- Never add fake city pages or claim local presence where it does not exist.
- Never scale the $100 ad test from clicks alone. Qualified intent and completed
  business economics must pass a human review first.
