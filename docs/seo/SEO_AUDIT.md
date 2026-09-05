# Leon Builds SEO acquisition audit

Audit date: September 5, 2026. Goal: qualified inquiry → scoped conversation → booked work, not page count or raw traffic. This adapts the supplied Curio framework to a founder-led services business.

## Verified architecture

- Production is `https://leonbuilds.org`, a Render static site (`leonkelvinli`) behind Cloudflare. The separate Express intake/analytics API is `https://leon-assist.onrender.com`.
- The publishing repository is `Noctilucenty/leon-dev-site`, branch `main`. The live Render Settings dashboard confirms `npm run build:static` → `dist`, Auto-Deploy `On Commit`, and no root directory or build filters. The separate API also tracks `main`; a static-only push can redeploy unchanged API code. The audited live revision was `0c983d4bb3ea94af16b3afe5817f7c143a9db338`.
- `homepage/` is the reviewed React/Vinext prerendered export from `Noctilucenty/freelance2` at `d14a4eedf0ef60ebdb6ba6e5dab9583c7c86c7fe`. Do not edit its compiled HTML or browser chunks. Edit its separate source and export only when a homepage change is needed.
- Existing subpages are plain generated HTML. Their authority is `tools/build_pages.py`, `tools/lang_pages.py`, and `content/lang_pages.json`. `tools/build_static.py` combines the allowlisted legacy pages and homepage export into `dist/`.
- There are 49 canonical sitemap URLs: homepage, service/industry hubs, nine service pages, ten industry pages, three detailed project cases, one inquiry guide, translated landing/service/booking pages, trust pages, and conversion pages. There is no large unpublished public knowledge database analogous to Curio cards.
- Public case studies distinguish deployed products, client systems and simulations. Their evidence is useful acquisition material already present, not a reason to fabricate more portfolio claims.

## Live evidence, not assumptions

At approximately 21:07 UTC, all 49 sitemap URLs returned HTTP 200, one H1 and the expected canonical. Every body matched this checkout's effective published source byte-for-byte. The live root is the newer homepage, not the legacy `index.html` source.

| Check | Observation | Interpretation |
| --- | --- | --- |
| `/robots.txt` | `User-agent: *`, `Allow: /`, canonical sitemap declared | No site-wide crawling prohibition observed |
| Unknown audit URL | HTTP 404 | No catch-all homepage soft 404 observed |
| HTTP / www | Redirected to HTTPS non-www | Preferred host signals align |
| `/services/websites.html`, trailing-slash variant | Both serve 200; canonical points to `/services/websites` | Duplicate aliases remain accessible but have a canonical signal; a host redirect is useful, not a critical outage |
| Homepage HTML | 61,987 bytes, visible content prerendered | Search does not require initial client execution; this is not a Core Web Vitals measurement |
| Subpage HTML | 8–23 KB across sampled inventory | Static answer surfaces are light; fonts, script execution and field vitals still need measurement |
| Publication fingerprint | `d03ac085dab475164e916f59e2de1380c274f1b7ef94d03210f17d76c0c8bcd1` | Exact release marker; not ranking evidence |
| Existing quality checks | Canonicals, one H1, schema, link targets, private asset allowlist, proof boundaries and prices already tested | Extend existing checks; do not replace working foundations |

The repository's September 4 Search Console record reports 6 clicks / 55 impressions for August 19–September 2, and a dated indexing report with 37 indexed pages. Those are historical observations, **not a refreshed September 5 baseline**. Query rows were withheld/limited, so search demand, competition, the clicked queries, qualified-lead rate and organic revenue remain unknown here. No authenticated account, booking webhook or campaign was modified in this audit.

### Deployment-target correction

The initial audit incorrectly identified `codex/freelance2-homepage` as the live static branch, relying on `HOMEPAGE_DEPLOYMENT.md` and the README. Both branches then pointed to the same revision, so byte-matching all 49 live pages could not establish which branch Render watched. That was a verification gap, not a deployment delay.

After commits `c3686da` and `14ef080` reached the review branch, the guide still returned 404 and the old fingerprint remained on both the canonical domain and `leonkelvinli.onrender.com`. Read-only Render inspection on September 5 confirmed the actual branch is `main`; the latest static deployment remained `dep-dadv08favr4c73aodjdg`, commit `0c983d4`, at 03:34:09 PDT. Remote `main` remained at that commit, while the review branch reached `14ef080`. The two SEO commits are a fast-forward from that base and contain no API runtime, lockfile, hosting or workflow changes. Correct the documentation and use the existing `main` workflow, without changing Render settings. The existing main-triggered search workflow is correctly wired.

## Prioritized findings

Scores below are planning judgments, not measured growth forecasts. Impact / difficulty / confidence / risk / product benefit use 1–10; priority estimate is `impact × confidence × product benefit ÷ (difficulty × risk)`, used within a priority tier only.

| Priority | Finding and evidence state | Action | Impact / difficulty / confidence / risk / benefit | Expected effect |
| --- | --- | --- | --- | --- |
| P0 | No confirmed site-wide indexability outage | Preserve host, API storage and publication branches | — | Avoid breaking a working funnel |
| P1 | CONFIRMED: semantic query ownership and a publication eligibility record do not exist; future expansion could duplicate nine existing service intents | Add an intent registry, alias ownership checks and an explicit candidate quality gate; one intent owner per language | 8 / 3 / 9 / 2 / 8 | Safer content growth and consistent internal links; traffic effect unmeasured |
| P1 | CONFIRMED: one buyer guide exists; the service hub offers service categories but no independent “template, automation, or custom build?” decision resource | Add one answer-first buyer guide with a scope checklist, visible limitations, existing proof links and a relevant contact path | 8 / 4 / 8 / 3 / 9 | Help uncertain visitors self-qualify before requesting a quote; demand remains a hypothesis |
| P1 | CONFIRMED: organic attribution exists but an SEO-specific query/page opportunity report is absent | Add read-only Search Console CSV ingestion and a local opportunity report; missing data stays unknown | 8 / 3 / 9 / 2 / 9 | Turns actual search language into a review queue instead of guessed volume |
| P1 | CONFIRMED: structured-publication checks inspect existing pages but no build gate prevents a draft SEO candidate from entering sitemap output | Make registry references and candidate review state fail closed; preserve reviewed legacy pages | 7 / 3 / 9 / 2 / 8 | Prevent future thin/duplicate pages from publishing automatically |
| P1 | CONFIRMED during the generator check: unchanged sitemap dates drifted from September 4 to September 5 because commit dates replaced published dates; root date followed the obsolete homepage source and `/work` resolved to a missing directory index | Preserve published dates for unchanged pages and resolve the actual source file | 6 / 2 / 10 / 2 / 6 | Honest freshness signals and fewer unnecessary recrawl requests |
| P2 | CONFIRMED: HTML and trailing-slash aliases serve duplicate 200 responses | Configure exact host redirects after confirming Render's active rules; keep canonical URLs stable | 4 / 4 / 8 / 5 / 5 | Consolidate discovery signals without breaking old links |
| P2 | LIKELY: some broad industry pages have less original project evidence than the three detailed cases | Review information gain and real proof before expanding those industries | 6 / 5 / 6 / 3 / 7 | Better buyer confidence; no invented client examples |
| P2 | UNKNOWN: current mobile field LCP/INP/CLS and organic-to-qualified-inquiry rate | Obtain field reports and aligned funnel exports before optimizing by guesswork | 7 / 4 / 8 / 1 / 8 | Identifies actual conversion/performance constraints |
| P3 | EXPERIMENTAL: interactive scoping tool or public technical teardown could earn citations | Only build after query or buyer evidence identifies a specific repeated decision | 6 / 7 / 4 / 4 / 8 | Potential original value, not guaranteed backlinks |

## GEO / answer-engine assessment

Google's July 2026 guide says standard SEO foundations still matter, with no special schema, mandatory text chunking or AI file required. It emphasizes useful original work and says Google ignores `llms.txt` for ranking/visibility. [Google's current AI optimization guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)

Google confirms FAQ rich results ended in May 2026 and the documentation was removed in June. Existing markup still describes visible FAQs, but no FAQ search-benefit claims or new FAQ schema are added here. Preferred Sources is a possible reader preference feature, not a reason to turn this services site into a news publication; it is not implemented. [Google's official update log](https://developers.google.com/search/updates)

The newer guidance also requires Search Console generative-AI inclusion for eligibility. This account setting was not inspected or changed in this lane; public robots access cannot establish its state. The AI performance report is a separate measurement surface, not proof of a lead or recommendation. [Google's AI performance report](https://support.google.com/webmasters/answer/16984139)

## Do not implement

- A hundred synonym pages, nationwide city-doorway pages, fake office locations, fake reviews, invented team members, “best developer” rankings, bought backlinks or automated outreach.
- Automatic publication from a demand score. A service page needs real scope, buyer utility and reviewed claims; a query variant usually belongs to an existing canonical page.
- Medical/legal assurances for client systems, guaranteed ranking/conversion promises, or fabricated project metrics.
- Changes to Google Business Profile eligibility, ads, budgets, billing, account verification, deployment platforms, API storage or booking callbacks without separate authority.
- Republishing source, data, audit reports, prospect information or credentials inside `dist/`. The allowlisted build must keep these private.

## Scope of this iteration

Implement the confirmed, low-risk semantic ownership/gating, one decision guide, contextual links and offline measurement ingestion. Preserve the homepage export, all legacy URLs, approved prices and proof wording. Do not claim indexing or acquisition lift until deployment and downstream evidence establish those separately.
