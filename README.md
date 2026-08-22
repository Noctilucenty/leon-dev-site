# Leon Kelvin Li / Noctilucenty — services site + assistant

What I build, what it starts at, what is actually running — plus a **nationwide
lead-generation layer**: problem-first homepage entry, a generated service/industry
page fleet, a quote flow, and an AI project assistant with its own secure backend.
Positioning: based in California, building for businesses across the U.S.

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
| `LEADS_KEY` | no | admin key for lead/traffic views and deep health; all three accept it only via `x-leads-key` |
| `EXTRA_ORIGIN` | no | one extra allowed browser origin |

Free plan idles: first chat reply can take ~30–60s. The widget warns the visitor and
warms the API when the panel opens; starter ($7/mo) removes the nap entirely.

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
to `data/leads.jsonl` (ephemeral on the free service), and emailed when a supported
delivery route is ready. Resend/HTTPS is the production route on Render; SMTP remains
a fallback for hosts that allow it. Chat leads include a model-written conversation
summary. UTM/referrer/first-page ride along via `localStorage.leon_attr`.

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

There is one honest delivery check: submit exactly one uniquely tagged lead and save
the non-sensitive `receiptId` returned by `POST /api/lead`. Confirm that receipt in
the Render `LEAD {...}` record, the following `LEAD_MAILED receiptId=...` line, and
the target inbox's subject/body. The human-readable tag appears in the stored lead
and email body; the API response intentionally returns only status plus the receipt.
Neither a green environment dashboard nor `/api/health?deep=1` replaces the inbox
check.

```bash
curl -i https://leon-assist.onrender.com/api/lead \
  -H 'content-type: application/json' \
  --data '{"name":"PIPELINE-CHECK-YYYYMMDD-HHMM","email":"pipeline-check@example.com","problem":"End-to-end delivery check; tag PIPELINE-CHECK-YYYYMMDD-HHMM","via":"pipeline-check"}'
```

Run this once after changing delivery configuration. A passing run has HTTP 200 with
`{"ok":true,"receiptId":"lead_..."}`, the same receipt in `LEAD`, a matching
`LEAD_MAILED` line (not `LEAD_MAIL_FAILED`), and the receipt plus test tag in the
message delivered to `LEAD_TO_EMAIL`. The log and JSONL copies are not durable
substitutes for the off-host copy. No generic webhook is treated as durable without
a real receiving system selected and verified.

## Publishing status

`content/publication-ledger.csv` is the canonical current record of what was posted
and each item's latest status. `content/facebook-audit.md` is historical narrative;
it contains useful evidence and superseded snapshots, but is not the live dashboard.
`content/facebook-group-coverage.csv` completes the other side of the audit: all 51
joined groups, including the 30 where the activity-log sweep found no group post.
Price-bearing ledger records carry a fingerprint of `tools/check_prices.py`'s
canonical floors. A reprice makes the check fail until each affected external post
is reviewed, so a live caption cannot silently drift behind the site again.

**Analytics**: first-party, log-only — `EVT {...}` lines from `data-evt` clicks
(hero_quote_click, pricing_cta_click, email_click, phone_click, quote_form_*) and the
widget (chat_open, chat_first_message, lead_submit). Records include a tab-scoped
anonymous session ID plus separate first- and last-touch source fields. No cookies,
contact fields or third parties. `/api/leads` and `/api/traffic` ignore `?key=`; use
the `x-leads-key` header so the secret does not enter URL logs or browser history.
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

**The page fleet** (`services/`, `industries/`, `quote.html`) is generated — copy edits go
in `tools/build_pages.py`'s SERVICES/INDUSTRIES data, never in the output files.

**Icons** are `<symbol>`s in the sprite at the top of `index.html`, used as
`<svg class="ic"><use href="#ic-name"/></svg>`. Copy the nearest one, keep the 24x24
viewBox and `stroke="currentColor"`, give it a new id.

**The page is lowercase by CSS**, not by hand: `body { text-transform: lowercase }`. Names,
emails and the ASCII diagrams opt out via `.keepcase` / the selector list next to it. If you
add a proper noun that must keep its capitals, add the class.

**Every claim on the page is real.** No client names for employer work, no testimonials, no
download or revenue figures, no star ratings. If you add a number, make sure it is one you
would be happy to be asked about on a call.

## Deploying

Live at **https://leonbuilds.org** — a Render static site on
`Noctilucenty/leon-dev-site`, branch `main`, root directory `.`, no build command,
publish directory `.`. Pushing to `main` redeploys it.

The 32-hex `*.txt` file at the root is the IndexNow key — Bing/DuckDuckGo/Yahoo read
it to trust our URL submissions. Keep it deployed; resubmit URLs after big content
changes with a POST to api.indexnow.org (see git log for the exact call).

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
