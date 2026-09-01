# Leon Builds — services site + assistant

What I build, what it starts at, what is actually running — plus a **nationwide
lead-generation layer**: problem-first homepage entry, a generated service/industry
page fleet, a quote flow, and an AI project assistant with its own secure backend.
Positioning: based in California, building for businesses across the U.S.
The missed-lead sprint is an intentionally Bay Area-targeted acquisition test;
the rest of the catalog remains nationwide.

**Style references.** [ultracontext.com](https://ultracontext.com) for structure and motion —
floating nav pill, bracket-hover links, an orbit graphic in the hero, alternating
project rows, three pricing tiers, a multi-column footer.
[impossibl.com](https://impossibl.com) for the mood — pure black, mono, lowercase,
huge side rails, ordered-dither pixel canvases, `details` FAQ. The accent is a
slightly purple `#9b8cff`, which is the only colour on the page.

```
index.html          the homepage — hand-written; 12 sections incl. problem cards + trust
services/*.html     GENERATED — 9 service pages + index (tools/build_pages.py)
industries/*.html   GENERATED — 10 industry pages + index
missed-lead-recovery.html  GENERATED — focused 10-business-day acquisition offer
quote.html          GENERATED — quote form; opens the visitor's mail app, logs to the API
sitemap.xml robots.txt  GENERATED
styles.css          tokens + layout (+ subpage/widget styles appended at the bottom)
app.js              13 isolated behaviours (see below)
assist.js/.css      floating AI assistant + event beacon + UTM capture
server/             the API: chat (OpenAI), leads, events — its own Render web service
tools/build_pages.py  regenerates everything marked GENERATED (edit its in-file data)
render.yaml         blueprint for the API service (leon-assist)
```

The **site source** is still plain static files with no bundler. Deployment uses
`tools/build_static.py` to assemble an explicit public allowlist in `dist/`; the
**API** is the only runtime with dependencies, and it deploys as a separate Render
web service.

## Run it

```bash
cd ~/Desktop/dev/freelancing
npm install
OPENAI_API_KEY=sk-... npm run dev      # API only on http://localhost:8787
python3 tools/build_pages.py           # regenerate the page fleet after editing its data
npm run build:static                    # allowlisted public files -> dist/ (deletes nothing)
python3 -m http.server 4599 --directory dist  # static preview in a second terminal
npm run check                           # content, site-integrity and server regression gates
```

## Two deployments, one repo

1. **Static site:** Render static site → leonbuilds.org, auto-deploys on push.
   Set **Build Command** to `npm run build:static` and **Publish Directory** to
   `dist`. Never publish the repository root `.`. Pretty URLs serve
   `/services/websites` from `dist/services/websites.html`.
2. **Assistant API (new):** Render **web service** from this same repo — *New + →
   Blueprint* picks up `render.yaml` (name `leon-assist`, `npm install`,
   `node server/index.js`, health `/api/health`). Then add `OPENAI_API_KEY` in that
   service's **Environment tab yourself** — it is never in git; `render.yaml` marks it
   `sync:false` on purpose. For lead notifications on Render, add
   `RESEND_API_KEY` and `LEAD_TO_EMAIL`; this service cannot reach outbound SMTP.

The static builder starts from `sitemap.xml`, adds the public verification files,
CSS/JS/icons/OG image, and follows local page/CSS asset references. It does not copy
`content/`, `tests/`, `tools/`, `server/`, `research/`, `data/`, package files,
Markdown/CSV, or unreferenced social/listing creatives. It never cleans or deletes
`dist/`: a symlink or unexpected pre-existing path makes the build stop before any
copy. Rename an old unexpected output directory aside if the manifest changes.
`python3 tools/build_static.py --check` validates the allowlist read-only and is part
of `npm run check`.

The frontend finds the API through **one constant**: `API_BASE` at the top of
`assist.js` (default `https://leon-assist.onrender.com`; on localhost it targets
`:8787`). If Render assigns a different URL, change that constant and push.

| env var | required | notes |
|---|---|---|
| `OPENAI_API_KEY` | **yes** | dashboard only, never git |
| `OPENAI_MODEL` | no | default `gpt-5-mini` |
| `OPENAI_MAX_OUTPUT` | no | default 700 tokens/reply |
| `DAILY_MODEL_CAP` | no | default 500 calls/day, then chat politely closes |
| `RESEND_API_KEY` + `LEAD_TO_EMAIL` | no | recommended on Render; sends the off-host lead copy over HTTPS |
| `LEAD_FROM_EMAIL` | no | Resend sender; use an address/domain allowed by that Resend account |
| `SMTP_HOST/USER/PASS` (+ optional `SMTP_PORT`) + `LEAD_TO_EMAIL` | no | fallback only on hosts that permit outbound SMTP; the current Render service does not |
| `LEADS_KEY` | no | admin key for lead/traffic views, delivery probes/status and deep health; accepted only via `x-leads-key` |
| `EXTRA_ORIGIN` | no | one extra allowed browser origin |
| `LEON_DATA_DIR` | no | directory for leads/events/acquisition and lead-email outbox JSONL; on Render, set only inside an attached persistent disk |
| `CAL_WEBHOOK_SECRET` | no | enables `/api/cal/webhook`; must exactly match the signing secret configured in Cal |
| `ACQUISITION_SINK_URL` | no | optional verified HTTPS receiver for minimized funnel-stage envelopes |
| `ACQUISITION_SINK_TOKEN` | no | optional Bearer credential for that receiver |
| `ACQUISITION_SINK_SECRET` | no | optional outbound HMAC secret for `x-leon-signature-256` |

`render.yaml` deliberately says `plan: starter` because that is the live API plan.
Changing it back to `free` would let a later Blueprint apply reintroduce cold-start
delay. The widget still warms the API and handles restarts or provider latency.

## The assistant

Browser → `POST /api/chat` on our server → OpenAI Responses API → streamed back as plain
text. The key exists **only** in server env; browser and model context never see it.
`server/prompt.js` is the whole personality: plain words, one question per reply, prices
only as published floors, recommends *against* AI when a script is cheaper, never quotes
finals, never claims to be Leon. Protections: CORS locked to the site, per-IP rate
limits, body-size caps, daily model-call ceiling, bounded history (older turns
summarized server-side), 90s timeout, and an API-only host that serves no repository
or duplicate site files.

**Leads** (`POST /api/lead`, from chat handoff + quote form): logged to stdout as
`LEAD {...}` (useful for diagnosis, but subject to Render's log retention), appended
to `data/leads.jsonl` by default, and emailed when a supported delivery route is
ready. Setting `LEON_DATA_DIR` moves leads, events, acquisition and lead-email
outbox JSONL together to that directory. Resend/HTTPS is the production route on
Render; its exact queued payload is stored with the accepted lead, failed sends
retry with capped backoff, and every retry uses the same provider idempotency key.
SMTP remains a fallback for hosts that allow it. Chat leads include a model-written
conversation summary. First/last referral touch, all five standard UTM values, and present
`gclid`, `gbraid`, `wbraid`, `fbclid` or `msclkid` values ride along via the bounded
`localStorage.leon_attr` record.

`GET /api/health` is a liveness check and reports lead delivery separately:
`leadEmailProvider`, `leadEmailState`, `leadEmailConfigured`, `leadEmailSupported`,
and `leadEmailReady`. A complete SMTP setup on Render reports `blocked`, not green.
`?deep=1` may check an SMTP connection, but it never sends mail and therefore never
claims inbox delivery worked. Deep health is admin-only: set `LEADS_KEY` and send it
in the `x-leads-key` header. It returns 404 when the key is not configured and 401
when the header is missing or wrong; a `?key=` query value is deliberately ignored.

```bash
curl -s https://leon-assist.onrender.com/api/health?deep=1 \
  -H 'x-leads-key: YOUR_LEADS_KEY'
```

### Verify lead delivery end to end

There is one honest delivery check: send exactly one admin-generated synthetic
probe and save its non-sensitive `receiptId` and tag. The probe accepts no request
body or caller-supplied contact data. It uses the real durable Resend outbox with a
reserved `example.com` Reply-To, is marked `synthetic:true`, and is excluded from
normal `/api/leads` results and counts. The public `POST /api/lead` route cannot set
that marker. Neither a green environment dashboard nor `/api/health?deep=1`
replaces the inbox check.

```bash
curl -i -X POST https://leon-assist.onrender.com/api/lead-delivery-probe \
  -H 'x-leads-key: YOUR_LEADS_KEY'

curl -s https://leon-assist.onrender.com/api/lead-delivery-status/RECEIPT_ID \
  -H 'x-leads-key: YOUR_LEADS_KEY'

# Run only after the same receipt/tag is visibly present in the target inbox.
curl -s -X POST \
  https://leon-assist.onrender.com/api/lead-delivery-confirm/RECEIPT_ID \
  -H 'x-leads-key: YOUR_LEADS_KEY'
```

Run this once after changing delivery configuration. A probe request returns HTTP
202, its opaque receipt and tag, and a status path. Poll that authenticated path
until it reports `state:"sent"`; it exposes only operational state and the Resend
provider message ID, never the payload or an address. Then confirm that exact ID is
`delivered` in Resend and that the same receipt/tag is visible in the target inbox.
Provider acceptance alone is not inbox proof. The final confirmation writes a
minimal append-only observation tied to the exact sender/recipient configuration;
only then can `/api/health` report `leadEmailVerified:true` and a confirmation time.
A later configuration change automatically returns health to unverified. Synthetic
rows remain available for audit through authenticated
`/api/leads?format=json&includeSynthetic=1`; do not edit the append-only lead,
outbox or confirmation ledgers to clean up a probe.

## Acquisition measurement and CRM stages

This repository includes consent-gated Google Ads conversion measurement. It does
not load Google Analytics, Meta Pixel or another ad-network script, and it does not
create audiences or make ad-account changes. The Google tag is blocked under basic
consent mode until the visitor selects **Allow measurement**; a first-time decline
does not load the tag or send Google a consent ping. When allowed, the standard
Google tag sends a configuration/page-view hit that may process the page URL
(including campaign or click identifiers), IP and device/browser signals, and
advertising-cookie identifiers. The site also sends four explicit conversion
events: API-accepted project inquiries, successful embedded
Cal bookings, phone-link clicks and WhatsApp-link clicks. A quote receipt or opaque
booking UID is required and used as the transaction identifier; contact-link events
are limited to one per action per tab and do not prove a call or message occurred.
No monetary value is assigned to these actions. Each explicit conversion event
sets `user_data` to an empty object, and ad personalization stays denied; site
code does not intentionally provide form fields, contact details or chat text to
Google's user-provided-data interface. That code does not control the separate
account-level automatic customer-data collection setting, which must remain
disabled in Google Ads. Revoking a prior grant sends the required denied
consent update, stops further conversion events on that page, and keeps the tag
blocked on later page loads.

The browser also recognizes
`utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `gclid`,
`gbraid`, `wbraid`, `fbclid` and `msclkid`; retains bounded first- and last-touch
records for up to 90 days; and sends them to the first-party lead/event API.
Referrers are reduced to their origin before storage. Quote submissions carry all
ten fields. The Cal embed and direct fallback receive only the five standard UTMs;
ad click IDs are not forwarded into Cal.

After an embed reports a successful booking, its opaque booking UID links the
browser's bounded first/last campaign touch to the CRM record. That browser signal
is marked non-authoritative and cannot create or advance a stage; only a signed Cal
webhook or the admin route can do that.

The authoritative opportunity stages are `booked`, `attended`, `qualified`,
`proposal`, `won`, `lost`, `cancelled`, and `no-show`. Cal can establish booked,
cancelled and a true no-show update. The API deliberately does not infer attendance
from `MEETING_ENDED`; Leon records attended and the downstream sales stages through
the admin route. One JSONL stage row is allowed per booking UID plus stage, so Cal
retries cannot double-count it.

Authorized end-to-end QA may still create a real-looking quote receipt or Cal
booking UID. Do not delete those source rows. Append the exact opaque identifier
to the same acquisition ledger through the admin-only exclusion route instead.
The operation is idempotent, requires `confirmSynthetic:true`, accepts exactly
one unmodified `receiptId` or `bookingUid` per request, requires that exact
source record to exist, and has no delete/unexclude counterpart. Funnel summaries
and `tools/acquisition_report.py` ignore matching QA records and any anonymous
analytics session explicitly correlated to those targets, while authenticated
raw JSON continues to expose the append-only evidence and exclusion record.
The normal `/api/leads` and `/api/traffic` views also omit excluded quote or
booking sessions; an authenticated auditor can add `?includeQaExcluded=1` to
inspect the preserved source records.

Configure a Cal webhook to POST JSON to
`https://leon-assist.onrender.com/api/cal/webhook`, subscribe to booking created,
rescheduled, cancelled and no-show-updated events, and set the same high-entropy
secret in Cal and `CAL_WEBHOOK_SECRET`. The server verifies `x-cal-signature-256`
against the exact raw body before parsing. It discards attendee names, email
addresses, answers and notes; only the booking UID, mapped stage, event time and
bounded attribution are written. The endpoint remains 404 while the secret is
unset. Use Cal's standard payload (no custom payload template); the current
`2026-07-27` version and the legacy `2021-10-20` shape are both accepted. See Cal's
[webhook payload/signature guide](https://cal.com/docs/developing/guides/automation/webhooks)
and [standard UTM tracking guide](https://cal.com/help/bookings/utm-tracking).

```bash
# Human-confirmed stage update. Never put LEADS_KEY in the URL.
curl -sS https://leon-assist.onrender.com/api/acquisition/stage \
  -H 'content-type: application/json' \
  -H 'x-leads-key: YOUR_LEADS_KEY' \
  --data '{"bookingUid":"CAL_BOOKING_UID","stage":"qualified"}'

# Minimized records, current-stage materialization and counts as JSON.
curl -sS 'https://leon-assist.onrender.com/api/acquisition?format=json' \
  -H 'x-leads-key: YOUR_LEADS_KEY'

# Exclude one synthetic quote receipt from inquiry reporting.
curl -sS https://leon-assist.onrender.com/api/acquisition/exclusions \
  -H 'content-type: application/json' \
  -H 'x-leads-key: YOUR_LEADS_KEY' \
  --data '{"receiptId":"<EXACT_LEAD_RECEIPT_ID>","confirmSynthetic":true}'

# Or exclude one synthetic booking UID from authoritative booking counts.
curl -sS https://leon-assist.onrender.com/api/acquisition/exclusions \
  -H 'content-type: application/json' \
  -H 'x-leads-key: YOUR_LEADS_KEY' \
  --data '{"bookingUid":"<EXACT_CAL_BOOKING_UID>","confirmSynthetic":true}'
```

Opening `/api/acquisition` with the same header-only authentication shows a small
human-readable scorecard; `?format=json` returns the records and materialized state.

There are two supported durability strategies:

1. Attach a Render persistent disk, create a dedicated directory on its mount,
   and set `LEON_DATA_DIR` to that directory. The Blueprint intentionally does not
   attach or price a disk automatically.
2. Set `ACQUISITION_SINK_URL` to a verified HTTPS ingestion endpoint. The app sends
   minimized JSON envelopes with `x-leon-event-id` and stable
   `x-leon-dedupe-key`; set at least one of the Bearer or HMAC credential variables.
   The receiver must make the dedupe key unique and persist
   the record before returning 2xx. Do not call a sink durable until a test record
   has been observed in its final store.

`/api/health` reports `acquisitionStorageState`,
`acquisitionDurableConfigured`, `acquisitionLocalMode`,
`acquisitionSinkConfigured`, and `calWebhookConfigured` without revealing a path,
URL, token or secret. `ephemeral-only` is an explicit warning, not a green storage
claim.

## Publishing status

`content/publication-ledger.csv` is the canonical current record of what was posted
and each item's latest status. `content/facebook-audit.md` is historical narrative;
it contains useful evidence and superseded snapshots, but is not the live dashboard.
`content/facebook-group-coverage.csv` completes the other side of the audit: all 51
joined groups, including the 30 where the activity-log sweep found no group post.
Price-bearing ledger records carry a fingerprint of `tools/check_prices.py`'s
canonical floors. A reprice makes the check fail until each affected external post
is reviewed, so a live caption cannot silently drift behind the site again.

**Analytics**: first-party — `EVT {...}` lines from `data-evt` clicks
(hero_quote_click, pricing_cta_click, email_click, phone_click, quote_form_*) and the
widget (chat_open, chat_first_message, lead_submit). Records include a tab-scoped
anonymous session ID plus separate first- and last-touch source fields. No cookies,
contact fields or third-party analytics tags are used. JSONL lives on the application
filesystem unless `LEON_DATA_DIR` is configured. `/api/leads` and `/api/traffic`
ignore `?key=`; use the `x-leads-key` header so the secret does not enter URL logs or
browser history.
The traffic view separates raw event records from unique-session funnel rates and
labels legacy records without a session ID instead of treating them as visitors.

## What moves

| # | Behaviour | Notes |
|---|---|---|
| 1 | Dither canvases | 8x8 Bayer threshold over a sine field, drawn at 1/6 scale and blown up with `image-rendering:pixelated`. ~18fps on purpose. Pauses off-screen. |
| 2 | Custom cursor | `pointer:fine` only. Grows over anything interactive. |
| 3 | Scroll progress + active nav link | One rAF-throttled scroll handler for both. |
| 4 | Mobile menu | |
| 5 | Hero terminal | Types and deletes four commands on a loop. |
| 6 | Text scramble | Headings resolve out of random glyphs on entry. |
| 7 | Scroll reveal | Blur + rise, staggered. |
| 8 | Counters | Count up once, on entry. |
| 9 | Magnetic buttons | Lerp toward the pointer. |
| 10 | Card spotlight | Purple radial follows the cursor across the service grid. |
| 11 | Service filters | |
| 12 | Marquee | Track is duplicated in JS so the loop is seamless. |
| 13 | Footer year | |

## Editing it

**Services.** Each is one `<article class="cell" data-cat="…">`. The category must match a
chip's `data-filter` (`web`, `ai`, `ops`, `growth`, `data`) or the card vanishes when that
chip is picked. `data-cat` takes several, space-separated — that is how *custom software*
appears under every filter. The `<span class="n">` numbers are manual; renumber if you
insert one.

**Prices** live in the `<b>` at the end of each cell and in `.amt` on the tiers. Each floor
sits roughly 10-15% below the low end of the 2026 US market band for a solo developer selling
direct — the bands, sources and reasoning are in `research/2026-08-19-*.md`. They are floors,
not quotes, and the whole list is meant to stay internally consistent. If you change one,
check it still sits sensibly against its neighbours — **and update the other two copies;
nothing syncs for you**: the fleet data in `tools/build_pages.py` (then rerun it) and the
assistant's price list in `server/prompt.js`. Generated social and classified art is
deliberately price-free; `tools/check_prices.py` enforces that and verifies fresh renders.

**The page fleet** (`services/`, `industries/`, `missed-lead-recovery.html`, `quote.html`) is generated — copy edits go
in `tools/build_pages.py`'s SERVICES/INDUSTRIES data, never in the output files.

**Icons** are `<symbol>`s in the sprite at the top of `index.html`, used as
`<svg class="ic"><use href="#ic-name"/></svg>`. Copy the nearest one, keep the 24x24
viewBox and `stroke="currentColor"`, give it a new id.

**The page is lowercase by CSS**, not by hand: `body { text-transform: lowercase }`. Names,
emails and the ASCII diagrams opt out via `.keepcase` / the selector list next to it. If you
add a proper noun that must keep its capitals, add the class.

**Every claim on the page must be real.** Do not name an employer's client or publish a
testimonial, rating, result, download figure, or revenue figure without the speaker's
permission and supporting record. Owner approval is not client approval. Supplied quote
drafts remain verbatim in the gitignored local `content/client-success/testimonial-drafts.json`;
public release is fail-closed through `content/client-success/testimonial-publication.json`
and private speaker evidence. Quote permission and rating permission are separate. If you add a
number, make sure it is one you would be happy to substantiate on a call.

## Deploying

Live at **https://leonbuilds.org** — a Render static site built from this
repository's `main` branch, root directory `.`, build command
`npm run build:static`, and publish directory `dist`. Pushing to `main` redeploys it.

The static build also generates `dist/site-version.txt`: a deterministic SHA-256
fingerprint of every allowlisted public source file. It is deployment evidence,
not a source file. The main-push search workflow builds the same fingerprint,
waits until Render serves that exact value, checks the live robots file, sitemap,
`llms.txt`, IndexNow key, HTTP status, content type, canonical and indexing
directives for every sitemap page, and only then considers an IndexNow request.

The 32-hex `*.txt` file at the root is the IndexNow key — Bing/DuckDuckGo/Yahoo read
it to trust our URL submissions. Keep its body identical to its filename. URL
selection is derived from the two deployed Git revisions, including deleted URLs
and same-day HTML changes. The default CLI path is a dry run and makes no network
requests:

```bash
npm run indexnow:check -- --before-ref HEAD^ --after-ref HEAD
```

`.github/workflows/search-production.yml` is the only automatic submission path.
It runs after a `main` push, waits up to 15 minutes for the exact live fingerprint,
then invokes `tools/indexnow.py --submit` explicitly. A change set with no public
URLs exits successfully without reading the key or using the network. HTTP 200 or
202 means IndexNow received the request; it does **not** prove crawling or indexing.
All other statuses and network failures fail the workflow.

For an operator-only live check without a submission, first run the static build
and pass its generated fingerprint:

```bash
npm run build:static
python3 tools/check_live_search.py \
  --expected-fingerprint "$(tr -d '\r\n' < dist/site-version.txt)" \
  --wait-seconds 0
```

This workflow does not monitor Google Search Console. Automated Search Console
coverage monitoring remains blocked until the repository has an intentionally
provisioned Google API identity/property authorization; do not disguise missing
credentials as a zero-result check.

`canonical`, `og:url` and `og:image` are all absolute against that host. If a custom domain
is added later, those three need updating — a relative `og:image` is not followed by Facebook
or iMessage, so it has to stay absolute.

## Facebook/classified image

`assets/facebook.png` is a square (1200x1200) general Facebook/classified card built by
`tools/make_fb.py`. It uses three readable business outcomes and carries no prices, so it
does not drift when site rates change. Use it only where business promotion is allowed; it
is not a recommendation to create a Marketplace service listing.

```bash
python3 tools/make_fb.py            # regenerate the classified card
python3 tools/make_fb.py --check    # verify the committed PNG is current
python3 tools/make_og.py            # link preview
```

## Things that will bite you

- **`app.js` is split into `run(function(){…})` blocks deliberately.** A throw in one must not
  take the others down. Keep new features inside their own block.
- **The reveal only hides things when JS is alive.** `opacity:0` is scoped to `.js [data-rise]`
  and JS adds both the class and the attribute, so a script error cannot blank the page. There
  is also a 3s failsafe. Do not move that rule out of `.js`.
- **Scramble writes `textContent`, which would delete the `<em>` inside a heading.** So mixed
  headings are split into parts first and each part scrambles on its own. If you add a
  `data-scramble` heading with inline markup, that path is what keeps it.
- **Scramble has two escape hatches** (a 1.8s real-time cap and a `setTimeout` snap) because rAF
  is paused outright in a background tab, and a heading frozen as random glyphs is worse than
  no effect at all.
- **Headless Chrome will not size a window below 500px on macOS**, and it throttles rAF almost
  to a stop. A `--window-size=390` screenshot is a 500px layout cropped, and every rAF
  animation will look half-finished. Check overflow by comparing `scrollWidth` to
  `clientWidth`, not by eye.
- **`min-height:100svh` on the hero makes tall-window full-page screenshots useless** — the hero
  grows to the window. Screenshot a copy with that overridden instead.

## Social/classified media kit

`assets/listings/` holds proof imagery plus multilingual square cards for permitted group,
classified and directory promotion. The `fb_<lang>_{1hook,2build,3proof}.png` sets come
from `tools/make_listing_images.py`: a high-contrast hook, three readable outcomes, and a
Curio proof card with real product art and its public App Store URL. Run the generator with
`--check` to verify that every committed PNG matches its source.

The three source/proof images below were captured from the live site with reveal animations
forced on. The scroll-reveal keeps every section at `opacity:0` in headless Chrome, so a
plain `--screenshot` of `#services` comes back black. Copy `index.html`, inject

```css
[data-rise],.js [data-rise]{opacity:1!important;filter:none!important;transform:none!important}
.hero{min-height:auto!important}
```

into the head, serve it locally and capture at `--window-size=1600,14000`, then crop.

| file | what it is |
|---|---|
| `01_hero.png` | the positioning line |
| `03_work_running.png` | the four live systems and their diagrams |
| `05_curio_appstore.png` | three Curio App Store slides on cream |

Everything else on the page is near-black, which renders as an empty rectangle at
thumbnail size. `05_curio_appstore.png` is the only bright one — lead with it anywhere a
listing shows a single preview image.
