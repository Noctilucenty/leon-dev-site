# Homepage publication

The homepage is a static export of `Noctilucenty/freelance2` at commit `1a2c884434cd474ba9233a965bff392068dea594`,
branch `codex/initial-site`. Editable source: `/Users/leon/Desktop/dev/freelance2`.

The Render static site `leonkelvinli` (`srv-d9s1dhon74is73fonuag`) serves
`leonbuilds.org`. Its live Settings dashboard, inspected read-only on September 5,
2026, confirms branch `main`, build command `npm run build:static`, publish
directory `dist`, no root directory or build filters, and Auto-Deploy `On Commit`.
The separate `leon-assist` web service also deploys from `main`; static-only pushes
can redeploy unchanged API code. Keep its durable lead storage and existing
owner-email settings in place.

Correction: earlier versions of this note named `codex/freelance2-homepage` as
the live static target. That was incorrect. Matching published bytes established
the source revision, not which branch Render watched. The September 5 SEO commits
were first pushed to that review branch and did not deploy. The dashboard still
showed live commit `0c983d4bb3ea94af16b3afe5817f7c143a9db338`, deployment
`dep-dadv08favr4c73aodjdg` from 03:34:09 PDT. Follow the existing `main` workflow;
do not change hosting settings to make them match the old note.

## Updating the homepage

1. In the source repository, run `npm ci`, `npm run typecheck`,
   `npm exec oxlint -- app lib`, and `npm run build`.
2. Replace the generated `homepage/` directory with only `index.html`,
   `favicon.svg`, `_next/`, and `images/` from `dist/client/`.
   Keep prior generated output outside the repository if a backup is needed.
   Do not include server output, build manifests in JSON, or source maps.
3. Record the source commit above. Run `npm run check` and `npm run build:static`.
4. Refresh `origin/main`, review the exact diff, and integrate without overwriting
   upstream work. Normal-push the reviewed revision to `main`; no force push.
   After Render reports live, compare the served
   `/site-version.txt` with local `dist/site-version.txt`, then verify the homepage,
   browser assets, retained pages and invalid inquiry validation.

The publisher retains the existing sitemap pages, verification files and legacy
assets. It overlays the new root only after discovering those resources, and it
refuses unknown files, symlinks, collisions or unpublished resource references.
`tools/check_site.py` checks the effective new homepage at its logical root URL.

The contact form uses the existing API directly on the canonical domain. It
requires an accepted receipt before displaying success and reuses its request key
on retries. No synthetic lead or email is sent by the invalid-payload check.

Rollback: redeploy the previous static-site commit through the existing service.
Do not reset or force-push the shared `main` branch. The API and domain bindings
do not need to change.
