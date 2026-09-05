# Implementation and release plan

## Phase 0 — establish reality (completed)

Verified the separate homepage source, all 49 live canonical page bodies, root/robots/sitemap/404 behavior and preserved the historical Search Console baseline as dated evidence. Created `SEO_AUDIT.md` before coding. The initial branch inference from repository notes was wrong: both branches shared the live revision. Subsequent read-only Render inspection established that the static site actually watches `main`, not `codex/freelance2-homepage`. See the audit's correction record. No account or campaign settings were changed.

## Phase 1 — confirmed low-risk fixes (implemented locally)

- One useful buyer guide: website builder vs existing-tool automation vs custom software. Answer first, customer-request example, quote checklist, named author, original dates, source/proof boundaries and existing inquiry CTA.
- Four contextual inbound links from the services hub and relevant services, with shared alias ownership for 12 concepts / 54 query variants.
- Source-hash-bound 9+ indexing gate in both generators and the actual static publishing path.
- Read-only joint Query/Page Search Console CSV analysis and a 60-row inventory/candidate report, without fake search volume.
- Corrected no-op sitemap freshness drift: unchanged pages keep their published dates; the homepage date follows the actual exported homepage rather than the obsolete legacy root source.
- Extended existing automated site checks and regression tests. No new runtime dependency or heavier UI framework.

## Local verification — September 5, 2026

`npm run build:static` and the complete `npm run check` passed: 54 Python tests, 119 Node tests, 50 public HTML pages with matching canonicals, and 54 owned query variants. The static output excludes private SEO documents, editorial records and the opportunity CSV. The existing five Facebook publication-tag warnings are unrelated to this release. `git diff --check` passed.

Browser checks at 390 × 844 and 1440 × 960 found no horizontal overflow. The comparison cards and checklist were visually inspected; local navigation worked. No inquiry was submitted, and no signed-in search account was changed. The preview tab was closed and its viewport override reset.

The independent root-agent editorial review accepted the exact guide source at 9/10 for clarity, usefulness, trust and decision support. The separate review record binds named producer/reviewer identities to the source and rendered-page hashes. This is editorial process evidence, not a reader study, ranking prediction or conversion result.

Verified local build fingerprint: `6aeb5a1cf7e232c0d0f2f68eb981ef4a68a6661ecdab53c3d5745efa844319e6`. Publication and live verification remain separate release steps below.

## Release steps (root owns final publication)

1. Review the exact diff, new guide and private output list.
2. After generation, run `npm run build:static`, then `npm run check`, `npm run seo:opportunities` and `git diff --check`. The read-only check deliberately rejects a stale existing `dist/`; rebuild it first.
3. Verify mobile/desktop rendering and key local navigation, without submitting a synthetic inquiry.
4. Fetch `origin/main` again. Integrate any new upstream work safely in this isolated checkout; never overwrite either user's saved checkout. At the read-only deployment audit, `main` was `0c983d4` and the reviewed SEO head `14ef080` was its direct two-commit descendant.
5. Commit only these scoped files. Normal-push the exact reviewed commit to `refs/heads/main`, the dashboard-confirmed target for the static site. The separate API also follows `main` and may redeploy unchanged code. Verify no API runtime, dependency, durable-data or secret changes entered the diff. No force push or hosting changes.
6. After Render deploys, match `/site-version.txt` to `dist/site-version.txt`; verify the new guide and changed service-page bytes, retained home, sitemap and robots. A local build is not deployment proof.
7. The existing main-triggered GitHub search workflow builds the exact fingerprint, waits for that release, checks crawl foundations, then submits changed canonical URLs to IndexNow. Verify the run's actual result before claiming submission; do not duplicate a successful batch. IndexNow acceptance is not Google indexing. No workflow change is needed.
8. Observe Search Console later over matched windows. Do not repeatedly request unchanged URLs or call a recrawl a ranking win.

## Next phases — not automatically authorized or completed

P2: verify exact host redirect rules for `.html`/slash aliases; expand semantic mapping to the remaining legacy pages; obtain mobile field performance and joined qualified-inquiry evidence; review source-backed guide candidates.

P3: a reusable interactive scoping tool, one public technical teardown or evidence-backed comparison only if buyers/query data demonstrate demand. No automatically published long-tail fleet, bulk outreach, paid links or location doorways.

## Rollback

Redeploy the prior static publication commit `0c983d4bb3ea94af16b3afe5817f7c143a9db338`. Preserve the API service, durable data and domain settings. On this Render setup, a removed asset may remain cached/reachable; inspect the exact URL and use replacement content if retirement is required. Do not delete a whole deployment directory to roll back.
