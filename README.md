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
services/*.html     GENERATED — 13 service pages + index (tools/build_pages.py)
industries/*.html   GENERATED — 10 industry pages + index
quote.html          GENERATED — quote form, posts to the API
sitemap.xml robots.txt  GENERATED
styles.css          tokens + layout (+ subpage/widget styles appended at the bottom)
app.js              13 isolated behaviours (see below)
assist.js/.css      floating AI assistant + event beacon + UTM capture
server/             the API: chat (OpenAI), leads, events — its own Render web service
tools/build_pages.py  regenerates everything marked GENERATED (edit its in-file data)
render.yaml         blueprint for the API service (leon-assist)
```

The **site** is still no-build static files. The **API** is the only thing with
dependencies (`npm install`), and it deploys as a separate Render web service.

## Run it

```bash
cd ~/Desktop/dev/freelancing
npm install
OPENAI_API_KEY=sk-... npm run dev      # site + API together on http://localhost:8787
python3 tools/build_pages.py           # regenerate the page fleet after editing its data
```

## Two deployments, one repo

1. **Static site (existing, unchanged):** Render static site → leonkelvinli.onrender.com,
   publish dir `.`, auto-deploys on push. Pretty URLs serve `/services/websites` from
   `services/websites.html`.
2. **Assistant API (new):** Render **web service** from this same repo — *New + →
   Blueprint* picks up `render.yaml` (name `leon-assist`, `npm install`,
   `node server/index.js`, health `/api/health`). Then add `OPENAI_API_KEY` in that
   service's **Environment tab yourself** — it is never in git; `render.yaml` marks it
   `sync:false` on purpose.

The frontend finds the API through **one constant**: `API_BASE` at the top of
`assist.js` (default `https://leon-assist.onrender.com`; on localhost it targets
`:8787`). If Render assigns a different URL, change that constant and push.

| env var | required | notes |
|---|---|---|
| `OPENAI_API_KEY` | **yes** | dashboard only, never git |
| `OPENAI_MODEL` | no | default `gpt-5-mini` |
| `OPENAI_MAX_OUTPUT` | no | default 700 tokens/reply |
| `DAILY_MODEL_CAP` | no | default 500 calls/day, then chat politely closes |
| `SMTP_HOST/PORT/USER/PASS` + `LEAD_TO_EMAIL` | no | set all five to email each lead (Gmail app password works) |
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
summarized server-side), 90s timeout, `/server` `/tools` `/data` unservable.

**Leads** (`POST /api/lead`, from chat handoff + quote form): logged to stdout as
`LEAD {...}` (grep Render logs — the durable sink), appended to `data/leads.jsonl`
(ephemeral on free), emailed if SMTP is set. Chat leads include a model-written
conversation summary. UTM/referrer/first-page ride along via `localStorage.leon_attr`.

**Analytics**: first-party, log-only — `EVT {...}` lines from `data-evt` clicks
(hero_quote_click, pricing_cta_click, email_click, phone_click, quote_form_*) and the
widget (chat_open, chat_first_message, lead_submit). No cookies, no third parties.

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

**Prices** live in the `<b>` at the end of each cell and in `.amt` on the tiers. They are all
half the original flyer figures — halved once, in one pass, so the whole list stays internally
consistent. If you change one, check it still sits sensibly against its neighbours — **and
update the other three copies nothing syncs for you**: the fleet data in
`tools/build_pages.py` (then rerun it), the assistant's price list in `server/prompt.js`,
and `assets/facebook.png` via `tools/make_fb.py`.

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

Live at **https://leonkelvinli.onrender.com** — a Render static site on
`Noctilucenty/leon-dev-site`, branch `main`, root directory `.`, no build command,
publish directory `.`. Pushing to `main` redeploys it.

The 32-hex `*.txt` file at the root is the IndexNow key — Bing/DuckDuckGo/Yahoo read
it to trust our URL submissions. Keep it deployed; resubmit URLs after big content
changes with a POST to api.indexnow.org (see git log for the exact call).

`canonical`, `og:url` and `og:image` are all absolute against that host. If a custom domain
is added later, those three need updating — a relative `og:image` is not followed by Facebook
or iMessage, so it has to stay absolute.

## Listing image

`assets/facebook.png` is the square (1200x1200) Marketplace image, built by
`tools/make_fb.py`. Square because Marketplace crops the thumbnail to a square. Its price
table is a hand-picked twelve — **if the prices on the page change, change them there too**;
nothing links the two.

```bash
python3 tools/make_fb.py    # listing image
python3 tools/make_og.py    # link preview
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

## Listing media kit

`assets/listings/` holds the images used on the marketplace and directory listings.
Regenerated by screenshotting the live site with the reveal animations forced on — the
scroll-reveal keeps every section at `opacity:0` in headless Chrome, so a plain
`--screenshot` of `#services` comes back black. Copy `index.html`, inject

```css
[data-rise],.js [data-rise]{opacity:1!important;filter:none!important;transform:none!important}
.hero{min-height:auto!important}
```

into the head, serve it locally and capture at `--window-size=1600,14000`, then crop.

| file | what it is |
|---|---|
| `01_hero.png` | the positioning line |
| `02_services_grid.png` | every service with its starting price |
| `03_work_running.png` | the four live systems and their diagrams |
| `04_pricing_tiers.png` | the three tiers |
| `05_curio_appstore.png` | three Curio App Store slides on cream |

Everything else on the page is near-black, which renders as an empty rectangle at
thumbnail size. `05_curio_appstore.png` is the only bright one — lead with it anywhere a
listing shows a single preview image.
