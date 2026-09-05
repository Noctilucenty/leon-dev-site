# Keyword and intent system

Goal: match how buyers describe a job without putting synonym lists on the website.

## Data contract

Every one of the 50 current canonical routes has `id`, `canonical_path`, `language`, `cluster`, `primary_query`, `aliases`, `question_queries`, `related_entities`, `search_intents`, and typed contextual `relationships`. Each also declares an `intent_key`, `page_type`, `audience`, and explicit `intent_boundary`. Fifteen localized routes link to their existing English `translation_of` families. Trust, privacy, portfolio and conversion routes are mapped for their actual purpose, not dressed up as generic acquisition articles. Search volume and ranking feasibility for these editorial query suggestions remain unknown.

Example: “stop copying data between apps” belongs to the business-automation service. “Do I need automation or custom software?” belongs to the buyer decision guide. One is a hiring intent; the other is a choice the buyer must make first.

## Deterministic protection

`python3 tools/seo_system.py check` requires exact sitemap/owner coverage and one owner per canonical URL. It normalizes Unicode, punctuation, case and whitespace; within a language family, an intent key or query cannot have two canonical owners. It also checks actual page language/canonicals, reciprocal translation-family hreflang, typed relationship targets, useful boundaries and candidate collisions. Adding an unmapped sitemap page fails the generator and static publisher.

Beyond exact aliases, a deliberately conservative lexical signature catches reordered wording and a small reviewed set of inflections in English, Spanish and Portuguese. It retains negation and audience/industry terms; Chinese retains exact normalized wording rather than pretending Western token rules understand Chinese paraphrases. This is **not an embedding model or complete semantic understanding**. Differently worded equivalent ideas still need editorial review. A collision blocks a proposed second owner for inspection; it never automatically merges, redirects or rewrites a page. No paid model service is used.

Ownership is not editorial approval: all 49 grandfathered routes remain `legacy_review_pending`; only the independently reviewed buyer guide is `publication_reviewed`. The registry cannot relabel a legacy route as newly approved. The separate source/render-bound publication policy remains authoritative.

## Learn real language

1. Export a joint Query + Page report from an authorized Search Console source, keeping the date window known.
2. Run the offline report described in `SEO_METRICS.md`.
3. Inspect repeated queries and their existing landing pages.
4. Attach a genuinely equivalent phrasing to its current owner. Improve the visible answer only if it helps the buyer.
5. If two URLs appear for one query, inspect the intents before merging. Multiple ranking pages alone do not prove cannibalization.
6. New canonical pages require a distinct question and a completed publication review.

Do not automate query-to-title replacement. Country/device mixes, branded demand, small samples and Google-withheld queries can all change the interpretation.

## Opportunity file

`TOP_100_SEO_OPPORTUNITIES.csv` keeps the requested filename and fields, but contains 60 rows: 50 actual canonical surfaces and 10 additional buyer-intent hypotheses. It is deliberately not padded to 100. Many hypotheses improve an existing page rather than creating a new one. `existing_curio_content` and `curio_fit` are marked not applicable; Leon Builds-specific fit and canonical URL fields are added.

All 50 current routes now have explicit owner mappings; their query phrasings are hypotheses grounded in visible page purpose, not measured search volume. Every search-potential/competition field remains unknown. Priorities are editorial planning choices. Run `npm run seo:opportunities` after an approved inventory change.

## Safe gaps to investigate

Website ownership/handover, recurring costs, automation failure handling, contact-form email delivery and chatbot handoff testing fit the current services. They need a real worked example, current sources where applicable and a cold-reader review before indexing. No market-size or competitor claims are invented.
