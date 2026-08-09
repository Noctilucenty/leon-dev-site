# Leon Kelvin Li / Noctilucenty — services site

The site behind the Marketplace listing: what I build, what it starts at, what is
actually running, and how to book the free call.

**Style references.** [ultracontext.com](https://ultracontext.com) for structure and motion —
floating nav pill, bracket-hover links, an orbit graphic in the hero, alternating
project rows, three pricing tiers, a multi-column footer.
[impossibl.com](https://impossibl.com) for the mood — pure black, mono, lowercase,
huge side rails, ordered-dither pixel canvases, `details` FAQ. The accent is a
slightly purple `#9b8cff`, which is the only colour on the page.

```
index.html      one page, 9 sections, inline SVG icon sprite
styles.css      tokens + layout + the CSS-driven motion
app.js          13 isolated behaviours (see below)
assets/
  favicon.svg   monogram
  og.png        1200x630 social preview — regenerate with tools/make_og.py
tools/make_og.py
```

No build step, no dependencies, no framework. Fonts come from Google Fonts
(JetBrains Mono + Space Grotesk); everything else is in these three files.

## Run it

```bash
cd ~/Desktop/dev/freelancing && python3 -m http.server 4599
# http://localhost:4599
```

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

**Prices** live in the `<b>` at the end of each cell. The fourteen from the flyer are
unchanged; the twenty-one added ones sit at the same scale.

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

Three static files, so anything works. It is set up for a Render static site:
root directory `.`, no build command, publish directory `.`.

Before it goes live:

- `<link rel="canonical">` still points at `https://leondev.example/`.
- `og:image` is relative. Facebook and iMessage will not follow a relative one — make it
  absolute (`https://…/assets/og.png`) once there is a real domain.

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
