# Homepage publication

The homepage is a static export of `Noctilucenty/freelance2` at commit `e9c7aa8c9b62f166652cacf7b59f97349f3a11c1`,
branch `codex/initial-site`. Editable source: `/Users/leon/Desktop/dev/freelance2`.

The Render static site `leonkelvinli` (`srv-d9s1dhon74is73fonuag`) serves
`leonbuilds.org`. Publish the `codex/freelance2-homepage` branch of this repository
using the existing `npm run build:static` command and `dist` directory. Leave the
separate `leon-assist` web service on `main`; no API settings or data change.

## Updating the homepage

1. In the source repository, run `npm ci`, `npm run typecheck`,
   `npm exec oxlint -- app lib`, and `npm run build`.
2. Replace the generated `homepage/` directory with only `index.html`,
   `favicon.svg`, `_next/`, and `images/` from `dist/client/`.
   Keep prior generated output outside the repository if a backup is needed.
   Do not include server output, build manifests in JSON, or source maps.
3. Record the source commit above. Run `npm run check` and `npm run build:static`.
4. Push this publication branch. After Render reports live, compare the served
   `/site-version.txt` with local `dist/site-version.txt`, then verify the homepage,
   browser assets, retained pages and invalid inquiry validation.

The publisher retains the existing sitemap pages, verification files and legacy
assets. It overlays the new root only after discovering those resources, and it
refuses unknown files, symlinks, collisions or unpublished resource references.
`tools/check_site.py` checks the effective new homepage at its logical root URL.

The contact form uses the existing API directly on the canonical domain. It
requires an accepted receipt before displaying success and reuses its request key
on retries. No synthetic lead or email is sent by the invalid-payload check.

Rollback: redeploy the previous static-site commit, or restore its `main` branch.
The API and domain bindings do not need to change.
