# Content quality and indexing gate

The standard is a minimum of 9/10 in each dimension—not a compulsory perfect score. A score is an editorial judgment, never proof of engagement, traffic, ranking or conversions.

## Decisions

- INDEX: distinct useful intent, source-checked claims, all required dimensions at least 9, stable URL and reviewed source hash.
- IMPROVE: fix the named weakness; do not index the draft.
- MERGE: add the useful material to an existing intent owner. Redirect only after reviewing live routing and inbound links.
- NOINDEX: useful private or utility content that should not be a search landing page; do not include it in the sitemap. The current publisher fails if such a route is proposed for publication through its indexable manifest.
- REJECT: unsupported claims, invented proof, misleading location targeting, hidden keywords or no meaningful buyer value.

## Required dimensions

| Dimension | Reviewer question |
| --- | --- |
| SearchIntentMatch | Does the first paragraph answer the buyer's actual question? |
| InformationGain | Is there a concrete example, decision framework or useful artifact beyond a generic definition? |
| SourceQuality | Can the important factual claims be checked in linked sources or approved project evidence? |
| Originality | Is the page more than another vendor's description or a synonym of our own service page? |
| Completeness | Can the buyer make the promised decision without hidden missing steps? |
| Readability | Can a nontechnical owner explain the point after one read? |
| Curiosity | Is there a recognizable problem or surprising distinction worth continuing for? |
| FactualConfidence | Are prototypes, simulations, estimates and unknown outcomes clearly bounded? |
| DuplicateSafety | Is there one appropriate canonical owner for this intent and language? |
| ConversionFit | Is the next step useful and proportionate, after the answer? |

## Mechanical enforcement

The new guide's JSON source and exact rendered HTML are SHA-256 locked in `content/seo/publication.json`. A changed draft, low score, missing rationale, missing review date or new unreviewed sitemap URL blocks generation/publication. The static publisher additionally checks the rendered artifact, so directly editing compiled guide HTML cannot bypass the source review. Unknown candidates are never auto-indexed. The legacy snapshot preserves previously live routes without pretending they received fresh 9/10 reviews.

Numeric gates can be gamed, so reviews must name an exact weakness and explain the revision or lack of blocker. An unchanged source hash makes that review reproducible; it does not make it objective. The implementation does not call a paid critic API and does not claim ten independent reviewers.

The historical 49-route list is pinned to a code-level hash; appending a new URL to the legacy data fails rather than bypassing review. An INDEX record also requires distinct, nonempty producer/reviewer identities and a valid non-future review date. These are structural process safeguards, not a claim that self-entered identity strings authenticate a human. Root reviewed the record and final artifact before release.

## New guide review

The implementing agent reviewed the entire guide and assigned the ten dimensions 9 with written rationale. The root agent independently read the exact JSON and confirmed 9/10 clarity, usefulness, trust and decision support, with no blocking copy changes. Both noted the honest simulation labels and recommendation to buy the smallest useful solution. This is release judgment only. Search demand and conversion impact remain unmeasured.

## Refresh

Update `updated_at` only when content materially changes. Refresh official vendor/store specifics before adding them; no vendor plan comparison is in this guide. When claims change, update the source, rerun an independent cold-reader review, save a new hash and build again. Do not rotate published dates or canonical URLs as an SEO experiment.
