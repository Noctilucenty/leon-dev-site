# Visual-first design release — September 5, 2026

## Scope

The reviewed Leon Builds homepage is the design reference. Its compiled HTML
and framework assets are unchanged. All 49 canonical subpages now use a shared
paper/ink/green design, Geist and Instrument Serif fonts, visible navigation,
pill actions and restrained dimensional motion. Existing Render hosting stays
in place; no dependency, server, credential, payment or deployment-setting change.

The buyer guide, nine English services, ten industry pages and nine localized
service pages now lead with short illustrative workflows. Longer scope text is
available through native disclosures. Other pages receive the shared visual
system without hiding legal text or rewriting their evidence. This is not a
claim that every page received a new editorial review.

The buyer guide offers three native radio choices. Page/gallery/contact,
form/inbox/message and rule-check/human-approval objects show distinct jobs.
About 210 words are visible in the default main-content view. The complete
guide remains in HTML under optional reading. Prices, selected caveats,
commercial disclosure and example limitations remain visible.

## Self-review and independent review

Root's cold-reader judgment for the visual guide: 9/10 after revision.
Independent reviewer `/root/comparison_reader_audit` approved every publication
dimension at 9 or higher (DuplicateSafety 9.5). This is editorial judgment, not
measured user comprehension, conversion performance or search ranking evidence.

Initial review rejected an absolute "not all three" and a misleading
Rules/Access/Approval sequence. The final version says "not all three at once"
and shows a request checked against a rule before human approval. All 38 checked
source body strings remain. Technical review also prompted stronger contrast,
progressively enabled replay buttons and hidden-tab observer retention.

Buyer guide rendered SHA256:
`418fa73031158a20e0a4f903a58855b3d36b35481faf3927dad24ccf405e74bf`

Unchanged source JSON SHA256:
`e9f03da0a9b2c3e74dc7a3107f7c42426fe062fd192b4cf9343739ca336c219a`

## Verification

- `npm run build:static`: 110 allowlisted files plus one generated fingerprint.
- `npm run check`: 125 JavaScript tests, 54 Python tests, price/copy/proof gates,
  all 50 canonical pages and internal links pass. Five existing social-ledger
  source-tag warnings are unrelated and unchanged.
- Six new motion/design regression tests cover all subpages, local fonts,
  conditional guide content, illustration labels, bounded replay, reduced
  motion, hidden tabs, progressive controls and form separation.
- In-app browser: guide at default width, 390px and 1280px; long AI-chatbot flow
  labels at 320px; Portuguese service navigation and quote form at 390px.
- Native radio selection works by click and keyboard arrows. Full guide opens.
- With JavaScript disabled, radio choices still switch using CSS, static diagrams
  remain visible and inert replay buttons are absent. Browser state was restored.
- Reduced-motion replay produces static completion feedback with zero playing
  scenes. Temporary viewport/media overrides were reset.
- No horizontal page overflow in the inspected mobile examples. Long service
  diagrams stack on narrow screens; localized navigation uses concise labels.
- Quote controls remain stationary with 16px input text. No real inquiry,
  calendar booking or assistant request was submitted as a test.
- No error logs observed on the final guide preview.

New shared CSS, JavaScript and three reused local font files total about 99 KB
uncompressed. Motion is finite or input/scroll-driven, with no perpetual render
loop, scroll interception, WebGL dependency or new media-generation cost.

## Release status

Local build fingerprint:
`64366356236426d833e0b5bb57c5d9c585f4bbc0ab22d1c40f3a82dd49cf3ad0`

At this record's creation, local review and tests are complete. Deployment and
the existing Search production follow-through workflow must be verified
separately after push. IndexNow notification is not Google indexing or AI citation
proof. Do not repeat an already successful automatic submission.
