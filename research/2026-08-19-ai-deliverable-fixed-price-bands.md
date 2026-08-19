# US market fixed-price bands: AI deliverables for small businesses (solo freelancer vs agency), 2026

Date: 2026-08-19. Method: WebSearch + WebFetch sweep of 2026 pricing guides, agency rate pages, Fiverr/Upwork listings and cost guides.
Evidence tiers: [PR] peer-reviewed/academic, [PA] platform/financial data or large-n study, [NM] news/industry media, [OWNER] vendor/agency blog (interest-laden, tends to inflate).
Companion doc: [2026-08-19-ai-price-pressure-and-pricing-psychology.md](2026-08-19-ai-price-pressure-and-pricing-psychology.md) — deflation evidence Part A there; new deflation items found in this sweep are in the last section here.

Reading rule discovered mid-sweep: almost every "cost guide" is written by an agency to anchor high ($10k+ floors). The solo-market truth lives in three places: Fiverr's own cost-guide averages, real gig listings, and the Memvers transaction study. Agency guides define the HIGH band, not the market.

## 1. AI chatbot for a business website (trained on business content, lead capture, escalation)
- LOW (marketplace solo): $45-520 fixed; Fiverr fixed-price averages $216 (chatbot) / $520 (AI chatbot dev). [PA] https://www.fiverr.com/resources/guides/costs/chatbot-developer
- Marketplace median setup: $600, up from $350 in 2024. [PA] https://memvers.com/blog/freelance-pricing-data-study-2026
- MID (solo/dev-built): $1,000-5,000 ($1,000-3,000 labor + $50-300/mo API). [OWNER] https://www.chitika.com/how-much-does-a-custom-ai-chatbot-cost-for-small-businesses-in-2026/
- "Most local businesses will happily pay between $300 and $1,500 for a customer service agent that runs 24/7." [NM] https://medium.com/the-ai-studio/how-to-sell-ai-bots-on-fiverr-and-upwork-as-a-beginner-in-2026-6cb141897fa5
- HIGH (agency): $5,000-50,000+ build + $500-5,000/mo maintenance (chitika); NLP tier $15k-80k, gen/RAG tier $30k-150k. [OWNER] https://thecrunch.io/ai-chatbot-development-cost/
- Floor pressure: capable SaaS chatbots run $19-89/mo. [OWNER] https://www.crescendo.ai/blog/how-much-do-chatbots-cost
- Solo realistic: **$1,200-3,500 fixed** (content-trained + lead capture + escalation); below ~$600 you are competing with the $19/mo SaaS tier, above $5k you are quoting like an agency.

## 2. AI phone/voice agent (answers, books, routes)
- LOW (marketplace solo): real Fiverr gigs $20-400 (Vapi/Retell/n8n receptionist builds at $20, $25, $80; premium gigs $250-400). [PA] https://www.fiverr.com/gigpilot_33/build-make-com-n8n-automation-ai-voice-agent-vapi-ai-receptionist-retell-ai
- MID: setup/onboarding $1,500-5,000 one-time; basic $0-1,500; DIY infra runs $200-950/mo. [OWNER] https://www.kingstonesystems.com/blog/how-much-does-an-ai-voice-agent-cost-for-small-business
- Common implementation fee $500-2,000; integrations add $1,000-5,000. [OWNER] https://agxntsix.ai/guides/ai-voice-agent-pricing-guide-per-minute-costs-telephony-overhead-setup-fees ; https://www.nextiva.com/blog/ai-phone-agent-pricing.html
- HIGH (agency/enterprise): onboarding $5,000-25,000; custom implementations $10k-100k+. [OWNER] kingstonesystems (above); https://aircall.io/blog/best-practices/ai-voice-agent-cost/
- Usage economics: platforms $0.05-0.15/min infra, $0.25-0.50/min managed; 1,000 min/mo on Retell ≈ $85-130/mo all-in. [OWNER] https://www.retellai.com/blog/ai-voice-agent-pricing-full-cost-breakdown-platform-comparison-roi-analysis
- Solo realistic: **$1,500-3,500 setup + $250-500/mo** management (client pays platform minutes directly).

## 3. RAG knowledge base over company documents
- LOW (marketplace solo): RAG setup marketplace median $800, up from $500 in 2024 (+60%). [PA] https://memvers.com/blog/freelance-pricing-data-study-2026
- MID (senior solo, scoped pilot): interpolated $2,500-10,000 — no guide prices a solo tier; nearest anchors are dev-built chatbot $1k-5k (chitika) and "scoped single-use-case build $5,000-50,000, 2-6 weeks". [OWNER] https://quickchat.ai/post/how-much-does-chatbot-cost
- HIGH (agency): basic pilot $15k-40k (3-6 wks, one source, simple Q&A UI); production $40k-120k; enterprise $120k-300k+. [OWNER] https://getdevstudio.com/blog/rag-knowledge-base-development-cost/ ; corroborated $25k-50k basic / $75k-120k median mid-complexity at https://www.solulab.com/rag-development-cost and https://www.kellton.com/kellton-tech-blog/custom-ai-chatbot-development-llm-rag
- Cost driver quote: "the biggest cost driver is not the LLM itself. It is the work required to turn messy business information into a reliable retrieval system." (devstudio)
- Solo realistic: **$2,000-6,000** for single-source RAG with citations over a company's docs; $800 is the marketplace commodity price for a bare setup.

## 4. Document processing / data extraction automation (invoices, forms)
- LOW (marketplace solo): Fiverr parsing gigs $100-200 (tax forms from $100, python PDF/image extraction from $200); n8n services from $150-400. [PA] https://www.fiverr.com/gigs/pdf-data-extraction
- MID (solo): $1,500-4,500 as a multi-workflow AI build; per-workflow math: $900 base + AI component $250-1,500 + integration $300-1,500. [OWNER] https://www.jahanzaib.ai/blog/ai-automation-consultant-pricing-guide ; https://monetizebot.ai/blogs/ai-automation-agency-pricing-2026
- HIGH (agency): single-process automation $10k-30k. [OWNER] https://thecrunch.io/ai-automation-agency-cost/
- Floor pressure: "In 2026, any business can deploy an invoice and contract extraction system in days for hundreds of dollars per month" — SaaS parsers $19-29/mo (Parsio, Parseur). [OWNER] https://keerok.tech/en/blog/automate-invoices-contracts-with-multimodal-ai-ocr-2026/ ; https://parseur.com/blog/ai-invoice-processing-benchmarks
- ROI ammo for quotes: manual $10-30/invoice vs $2.36-2.78 automated (Ardent Partners via docuclipper). [PA] https://www.docuclipper.com/blog/cost-to-process-an-invoice/
- Solo realistic: **$1,500-3,500** for an invoices/forms -> accounting/sheet pipeline with exception handling; simple parsing alone is commoditized to SaaS.

## 5. AI content generation engine (blog/social, scheduled)
- LOW (marketplace solo): gig-level n8n content workflows $150-500 (block.fiverr n8n listings cluster here).
- MID (solo): $1,000-3,500 one-time starter build (1-2 core automations) + $500-2,000/mo SMB retainer. [OWNER] https://monetizebot.ai/blogs/ai-automation-agency-pricing-2026 ; https://taskip.net/ai-automation-agency-pricing/
- HIGH (productized/agency): DFY "AI content engine" $1,500-5,000/mo (example: $1,800/mo for 12 SEO posts); human freelance content $2k-6k/mo; agency $5k-15k/mo. [OWNER] https://www.averi.ai/how-to/the-true-cost-of-content-in-2026-freelancers-vs.-agencies-vs.-ai-platforms
- Floor pressure: DIY AI stack $50-300/mo (Jasper $49, Copy.ai $49, toolkit $50-80/mo). [OWNER] https://www.trysight.ai/blog/ai-content-generation-pricing
- Solo realistic: **$1,500-3,000 setup + $300-800/mo** oversight; the hybrid build-fee + small retainer is the recorded 2026 default engagement shape.

## 6. AI output guardrails / human review layer
- Thinnest category — almost never sold standalone to SMBs; it rides as a module or an audit.
- LOW (add-on module): interpolated $500-1,500 (workflow add-on rates: monitoring +$150-600, QA/documentation +$200-800 per monetizebot calc above).
- MID (fixed audit): SMB AI audit $2,000-10,000 fixed, 1-3 weeks, written deliverable; AI readiness assessment $2,000-8,000. [OWNER] https://justinmckelvey.com/blog/what-is-an-ai-audit ; https://www.theaiconsultingnetwork.com/blog/ai-consulting-small-businesses-cost-how-it-works
- HIGH (specialist): AI red-team one-time audits $8k-25k; comprehensive $50k-150k; continuous from $5k/mo. [OWNER] https://security.aivyuh.com/blog/ai-red-teaming-pricing-2026/
- Operating cost fact for scoping: an LLM validator per turn adds 15-40% to the provider bill and 200-800ms latency; frameworks catch 60-85% of serious problems. [NM] https://jacar.es/en/llm-guardrails-frameworks-and-their-real-cost/
- Solo realistic: **$750-2,500 as an add-on** to a build; **$2,500-7,500** as a standalone review-layer + eval-harness project.

## 7. Workflow automation (n8n / Make / Zapier pipelines)
- LOW (marketplace solo): Fiverr n8n gigs $150-400; workflow automation marketplace median $400, up from $250 in 2024. [PA] https://memvers.com/blog/freelance-pricing-data-study-2026
- MID (solo): single workflow $400-1,200; multi-workflow system with AI step $1,500-4,500. [OWNER] https://www.jahanzaib.ai/blog/ai-automation-consultant-pricing-guide
- Package view: starter (1-2 automations) $1,000-3,500; growth (3-6 workflows + dashboards + QA) $4,000-12,000. [OWNER] https://monetizebot.ai/blogs/ai-automation-agency-pricing-2026
- HIGH (agency): advanced multi-step + AI $5,000-12,000; SMB agency projects $5k-25k; ops overhaul $12k-35k+. [OWNER] https://ciphernutz.com/blog/n8n-automation-implementation-cost-breakdown ; https://thecrunch.io/ai-automation-agency-cost/
- Hourly reference: Upwork n8n freelancers $40-100/hr; production-grade specialists claim $200-350/hr. [PA] https://www.upwork.com/hire/n8n-experts/ ; [OWNER] https://buldrr.com/n8n-automation-agency-pricing/
- Solo realistic: **$500-1,200 per workflow; $2,000-4,500 for a small system** with an AI step + docs + handoff.

## 8. CRM setup and business systems integration
- LOW (solo): Starter-tier HubSpot-class setup $500-2,000. [OWNER] https://www.pixcell.io/blog/hubspot-implementation-cost
- MID: straightforward SMB implementation $2,000-10,000. [OWNER] https://www.trooinbound.com/blog/how-much-does-hubspot-implementation-cost-in-2026/ ; https://vorinops.com/blog/hubspot-implementation-cost/
- HIGH (agency/consultant): multi-hub + migration + automation $10k-30k; consultant projects $12k-60k; retainers $3,500-15,000/mo. [OWNER] https://automationstrategists.com/blog/hubspot-consulting-cost/
- Anchor for quotes: HubSpot itself charges mandatory onboarding $1,500 (Pro) / $3,500 (Enterprise) — a solo undercutting that number has a built-in comparison. [OWNER] https://evenbound.com/blog/how-much-does-hubspot-cost
- Solo realistic: **$1,500-5,000** (setup + import + pipelines + 2-3 integrations + training).

## 9. API integration between two SaaS tools
- LOW (marketplace solo): Fiverr fixed-price API projects $70-432; hourly $47-315. [PA] https://www.fiverr.com/resources/guides/costs/api-developer
- MID (solo/boutique): custom integration with a modern well-documented SaaS API ~EUR 3,000-8,000 (~$3,300-8,800). [OWNER] https://cloudactivelabs.com/en/blog/custom-api-integration-cost-in-2026-a-startup-founders-guide
- HIGH (agency): SMB custom API integrations $10k-50k when no native connector exists. [OWNER] https://percengage.com/blog/custom-api-integration-cost-calculator-what-smbs-really-pay-connect-systems-2026
- Maintenance fact: initial build is only 30-40% of two-year total cost. [OWNER] https://www.inovaflow.io/insights/api-integration-cost
- Solo realistic: **$800-3,000** for a one/two-way sync between two documented tools (use Zapier/n8n under the hood where possible; pure-code syncs justify the top of band).

## 10. Business dashboard / reporting (live metrics)
- LOW (marketplace solo): Fiverr sheets/Excel/KPI dashboards from $30; simple Power BI $300-2,000. [PA] https://www.fiverr.com/gigs/pdf-data-extraction (dashboard gigs surfaced in same listings) ; [OWNER] https://tabdelta.com/power-bi-dashboard-development-cost/
- MID: Looker Studio project, 3-5 connected reports, $2,000-6,000 one-time; medium Power BI $3k-20k. [OWNER] https://lets-viz.com/blogs/how-much-does-a-looker-studio-consultant-cost-in-2026 ; tabdelta (above)
- HIGH: + custom BigQuery pipeline $5,000-15,000; retainers $1,500-3,500/mo; enterprise $20k-150k. [OWNER] lets-viz, tabdelta (above)
- Hourly reference: senior US BI rates $120-185/hr; starter dashboard ~10 hrs. [OWNER] https://vidi-corp.com/small-business-dashboard/
- Solo realistic: **$500-2,500** for a live small-business KPI dashboard on free tooling (Looker Studio); **$3,000-6,000** when a data pipeline is part of the job.

## Cross-cutting: solo vs agency structure
- Agency guides put nearly everything at $5,000+ floors ($5k-50k/project is the repeated 2026 agency band; $100-300/hr). [OWNER] https://digitalagencynetwork.com/ai-agency-pricing/ ; https://thecrunch.io/ai-automation-agency-cost/
- The hybrid model (fixed-fee first build + small monthly retainer) is repeatedly named "the 2026 default" for SMB AI engagements. [OWNER] https://optimizewithsanwal.com/ai-automation-agency-pricing-2026-a-cfos-guide/ ; monetizebot (above)
- Solo marketplace medians for the same nouns run 5-20x below agency floors (chatbot $600 vs $5k+; automation $400 vs $5k+) — the middle ($1,200-4,500) is where a credentialed solo with direct clients (not marketplace bidding) actually lands.

## New deflation/commoditization evidence from this sweep (adds to companion doc Part A)
- [PA] GoodFirms 2026 survey via FoundersBar: "61% expected AI to reduce project budgets by 10-25%"; clients demand 50-70% cuts, "20-30% is the most common concession agencies report making"; verbatim client line: "Claude just built my MVP in a weekend, why should I pay you $80k?" Counterpoint same source: "Complex production software does not become 60% cheaper simply because code generation got faster" (40-20-40 rule: AI compressed only the 20% coding slice to ~8-12%). https://foundersbar.com/articles-and-research/why-software-development-quotes-arent-dropping
- [PA] Marketplace contraction: Fiverr 2026 guidance $380-420M vs ~$456.8M consensus (~12% miss); Upwork lost ~47,000 active clients in 2025 (832K -> 785K); "Blog posts, basic logos, translations and simple code are being completed inside ChatGPT, Claude and Midjourney — they never reach a marketplace at all"; "for higher-value work, buyers increasingly prefer vetted agencies, fractional specialists, or small in-house teams over open marketplaces." https://insights.itdukes.com/insights/upwork-fiverr-decline
- [NM] "Upwork cuts full-year forecast as AI pressures its marketplace" (Q2 2026). https://thenextweb.com/news/upwork-q2-2026-ai-disruption-guidance-cut
- [PR] Demand for substitutable skills (writing/translation) fell 20-50% vs counterfactual post-genAI, sharpest for 1-3-week jobs. https://www.sciencedirect.com/science/article/pii/S0167268124004591
- [OWNER] Deflation-side dollar claim: "a simple chatbot now runs $8,000-$15,000 versus $20,000-$50,000 pre-AI tooling, roughly a 3x compression" — surfaced in search results for the commoditization query set (sparkouttech/keyhole cluster) but NOT verified on-page (Keyhole fetch lacked it; theCrunch fetch explicitly has no such claim). Treat as unpinned until re-found.
- Counter-evidence remains in companion doc: agencies mostly not discounting (73% never asked), AI-skill work +44%/hr, AI service prices on marketplaces +60-100% since 2024 (Memvers).

## What this does NOT establish
- Almost every per-category source is [OWNER] (vendors/agencies marketing their own floors); the only transaction-grade data are Fiverr's cost-guide averages, live gig prices, and the Memvers study. Bands above weight those higher.
- No source prices a "guardrails/human review layer" as a standalone SMB product; that band is interpolated.
- The "solo realistic" lines are recommendations derived from triangulation, not observed prices.
- Agency-guide highs ($30k+ chatbots, $75k+ RAG) describe funded-startup/enterprise buyers, not Main Street small businesses; do not use them to justify SMB quotes.
