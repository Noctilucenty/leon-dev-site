# Keyword and intent system

Goal: match how buyers describe a job without putting synonym lists on the website.

## Data contract

Each mapped topic has `id`, `canonical_path`, `language`, `cluster`, `primary_query`, `aliases`, `question_queries`, `related_entities`, `search_intents`, and typed contextual `relationships`. Search volume and ranking feasibility are unknown, not guessed.

Example: “stop copying data between apps” belongs to the business-automation service. “Do I need automation or custom software?” belongs to the buyer decision guide. One is a hiring intent; the other is a choice the buyer must make first.

## Deterministic protection

`python3 tools/seo_system.py check` normalizes Unicode, punctuation, case and whitespace. Within each language, an exact normalized query cannot have two canonical owners. It rejects missing target pages, self-links, unsupported relationship types and empty link labels.

This is **exact-alias ownership**, not a semantic similarity model. It will not reliably detect two differently worded questions with the same meaning. The editorial duplicate review remains mandatory. No paid model or embedding service is used.

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

Unmapped legacy rows are honest inventory, not fabricated keywords. Every search-potential/competition field is unknown. Priorities are editorial planning choices. Run `npm run seo:opportunities` after an approved inventory change.

## Safe gaps to investigate

Website ownership/handover, recurring costs, automation failure handling, contact-form email delivery and chatbot handoff testing fit the current services. They need a real worked example, current sources where applicable and a cold-reader review before indexing. No market-size or competitor claims are invented.
