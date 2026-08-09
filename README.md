# Leon Dev — freelance services site

The website behind the Marketplace listing. It is the flyer, expanded into a page you can
send someone: what I build, what it starts at, what I have actually shipped, and how to
book the free consultation.

Structural reference is ultracontext.com — fixed nav, one centred column, mono micro-labels,
a hairline-divided grid, three pricing tiers, a multi-column footer. The brand is the flyer's,
not theirs: near-black, periwinkle accent, heavy condensed display type, handwritten asides.

```
index.html      one page, 10 sections, inline SVG icon sprite
styles.css      design tokens + layout
app.js          sticky nav, mobile menu, service filters, scroll reveal, year
assets/
  favicon.svg   monogram mark
  og.png        1200x630 social preview (regenerate with the snippet below)
```

No build step, no dependencies, no framework. Fonts come from Google Fonts; everything
else is in the three files.

## Run it

```bash
cd ~/Desktop/dev/freelancing && python3 -m http.server 4599
# then open http://localhost:4599
```

## Sections

| # | Section | What it does |
|---|---------|--------------|
| 1 | Hero | The flyer's headline, plus a proof panel of four things that exist |
| 2 | Services | 34 services in 5 filterable categories, each with a starting price |
| 3 | Work | 8 shipped projects, described by what was hard about them |
| 4 | Industries | The icon row from the flyer, 10 wide |
| 5 | About | Who the client is actually hiring |
| 6 | Process | Consult, fixed quote, weekly demo, launch and support |
| 7 | Pricing | Fixed project / full build / ongoing partner |
| 8 | FAQ | The seven questions that come up before anyone books |
| 9 | CTA | "Let's build it", contact rows, the circle arrow |
| 10 | Footer | Four columns, availability dot, contact bar |

## Editing it

**Services.** Each is one `<article class="svc" data-cat="…">` in `#svcGrid`. The category
in `data-cat` must match a chip's `data-filter` (`web`, `ai`, `ops`, `growth`, `data`) or the
card disappears when that chip is selected. `data-cat` accepts several, space-separated —
that is how the Custom Software card shows up under every filter.

**Prices** are starting points, written straight into the `.price` span. The fourteen from the
flyer are unchanged; the twenty added ones are set at the same scale. Change them in one place
and nowhere else references them.

**Icons** are `<symbol>` elements in the sprite at the top of `index.html`, used as
`<svg class="ic"><use href="#ic-name"/></svg>`. To add one, copy the nearest symbol, keep the
24x24 viewBox and `stroke="currentColor"`, and give it a new id.

**Everything on the page is a real claim.** No client names on work I did for an employer, no
invented testimonials, no download or revenue figures, no star ratings. If you add a number,
make sure it is one you would be happy to be asked about on a call.

## Deploying

It is three static files, so anything works. Two easy options:

```bash
# GitHub Pages — new repo, push, enable Pages on main
cd ~/Desktop/dev/freelancing
git remote add origin git@github.com:Noctilucenty/<repo>.git
git push -u origin main

# Render static site — root directory ".", no build command, publish directory "."
```

Two things to change before it goes live:

- `<link rel="canonical">` in `index.html` still points at `https://leondev.example/`.
- `og:image` resolves relative to the page. Once there is a real domain, make it absolute
  (`https://…/assets/og.png`) — Facebook and iMessage will not follow a relative one.

## Regenerating the OG image

```bash
cd ~/Desktop/dev/freelancing && python3 tools/make_og.py
```

## Things that will bite you

- **`app.js` is deliberately split into `run(function(){…})` blocks.** A throw inside one must
  not take the others down. Keep new features inside their own block.
- **The reveal animation only ever runs when JS is alive.** `opacity:0` is scoped to
  `.js [data-rise]`, and JS is what adds both the class and the attribute — so a script error
  can never leave the page blank. There is also a 2.6s failsafe that reveals everything
  regardless. Do not move the hiding rule out of `.js`.
- **Headless Chrome will not go below a 500px window on macOS.** A `--window-size=390`
  screenshot is a 500px layout cropped to 390, which looks exactly like a horizontal-overflow
  bug and is not one. Check real overflow by comparing `documentElement.scrollWidth` against
  `clientWidth`, not by eye.
- **`.svc-wide` spans two grid columns.** On one-column layouts the span is reset, otherwise
  the last row breaks.
