# Client-success draft queue

**Status: LOCAL DRAFTS ONLY — NO SEND CAPABILITY**

This pack turns an evidenced project completion into three local drafts:

1. one honest Google review request;
2. one honest LinkedIn recommendation request;
3. one referral request.

Nothing here contacts a client, opens a browser, publishes a case study, or
authorizes sending. Google and LinkedIn drafts remain blocked until their exact,
verified URLs are supplied. The tool never guesses a link, metric, result,
rating, testimonial, or approval.

The two `data/client-success*.json` files are intentionally ignored runtime
state because they can acquire client references. On a fresh checkout, create
their empty fail-closed forms without overwriting anything that already exists:

```sh
python3 tools/client_success_ops.py init
```

## Case-study intake

`case-study-slots.json` contains three empty slots. A slot collects:

- sourced before and after facts;
- optional before/after metrics, each with its unit and evidence;
- at least one screenshot plus evidence that it may be published;
- the exact public title, facts, quote, attribution, rating, screenshots, and
  placement sent to the client for approval.

Publication readiness is computed, not asserted. A slot is ready only when its
status and approval status are both `APPROVED`, the approved publication object
exactly equals the draft object, the SHA-256 digest matches, and the approval
and any rating evidence files exist. Store private evidence under a gitignored
`private/` path. Existing testimonial drafts in
`content/testimonial-request-pack.md` are not read, changed, or replaced.

## Existing supplied testimonial drafts

The seven supplied quotes and supplied five-star values are preserved verbatim in
the gitignored local `testimonial-drafts.json`. This repository is public, so
unapproved client wording must not be committed merely because the static site
would omit it. That file is source material, not publication permission.
`testimonial-publication.json` is the tracked public release allowlist. Each
released entry carries only its exact approved public payload, so a clean
deployment can render approved feedback without receiving the remaining private
drafts. When the local draft queue is present, the gate also requires every
released payload to match its locked private source exactly.

A release record must match the SHA-256 digest of the exact quote, attribution,
project label, context, placement, and ID. It also needs an approval date and a
SHA-256 receipt for the private approval evidence. Rating publication is a
separate nested approval with its own date and evidence receipt. Missing,
malformed, unknown, duplicated, or mismatched records stop the static build.

The homepage and generated pages emit only released IDs. The static build scans
every public HTML file and `llms.txt` so CSS hiding or stray copy cannot bypass
the gate. Check the zero-release state with:

```sh
python3 tools/testimonial_gate.py
python3 tools/check_testimonial_release.py
```

`testimonial_gate.py` prints the exact payload digest for each locked draft. An
entry is shaped like this only after the private approval evidence exists:

```json
{
  "id": "approved-testimonial-id",
  "approved_payload": {
    "id": "approved-testimonial-id",
    "project": "Approved project label",
    "attribution": "Approved attribution",
    "attribution_context": "Approved context",
    "quote": "Exact approved quote",
    "placement": "leonbuilds.org and related project marketing"
  },
  "payload_sha256": "64-lowercase-hex-characters",
  "approved_at": "YYYY-MM-DD",
  "approval_evidence_sha256": "64-lowercase-hex-characters",
  "placement": "leonbuilds.org and related project marketing",
  "rating_approval": null
}
```

Leave `rating_approval` as `null` unless the exact rating has its own client
approval and evidence receipt. Never reuse the quote approval receipt as rating
evidence.

Prepare the exact approval message after filling an intake slot:

```sh
python3 tools/client_success_ops.py approval-packet --slot-id case-study-01
```

Save the client's reply privately. Copy the exact approved package into
`approved_publication`, record its date and evidence path, and copy the printed
digest into `packet_sha256`. Do not mark `APPROVED` based on silence, site-owner
approval, or a rewritten quote.

## Completion workflow

Use a short project slug, a client greeting, and an internal contact reference;
do not put an email address or phone number in committed data.

```sh
python3 tools/client_success_ops.py add-project \
  --project-id PROJECT_SLUG \
  --project-label 'ACTUAL PROJECT LABEL' \
  --client-first-name 'CLIENT FIRST NAME' \
  --contact-ref 'PRIVATE CRM REFERENCE'
```

Review links are optional until they have been copied from the correct,
signed-in business profiles. Never substitute a search result or guessed URL.

```sh
python3 tools/client_success_ops.py set-review-links \
  --project-id PROJECT_SLUG \
  --google-review-url 'VERIFIED GOOGLE REVIEW URL' \
  --linkedin-url 'VERIFIED LINKEDIN RECOMMENDATION URL'
```

Record completion only with an existing private evidence file. This event is
idempotent and creates exactly three queue items in
`data/client-success-queue.json`:

```sh
python3 tools/client_success_ops.py complete-project \
  --project-id PROJECT_SLUG \
  --completed-at YYYY-MM-DD \
  --completion-evidence private/client-success/PROJECT_SLUG/completion.txt
```

The suggested spacing is two days for Google, nine for LinkedIn, and sixteen
for the single referral request. These are draft-review cues only; this tool
does not schedule or send them.

## Checks

```sh
python3 tools/client_success_ops.py check
python3 tools/client_success_ops.py case-study-status
node --test tests/client-success-ops.test.js
```

The queue must always retain `delivery_mode: DRAFT_ONLY`,
`manual_review_required: true`, `send_authorized: false`, and a blank
`sent_at`. A missing Google or LinkedIn URL must remain
`BLOCKED_MISSING_VERIFIED_URL`.

## Incentive separation

A pilot discount or other participation term must never be conditioned on a
Google review, LinkedIn recommendation, testimonial, rating, referral, or
case-study permission. If a pilot has discounted terms, they may compensate
only for pilot participation, timely access, baseline measurement, and honest
product feedback; document those terms separately from this queue. Every queue
item must retain `incentive_attached: false`, and validation rejects incentive
language in review and referral drafts.
