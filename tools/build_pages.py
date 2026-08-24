#!/usr/bin/env python3
"""Generates the SEO page fleet: /services/*, /industries/*, both index pages,
/missed-lead-recovery, /quote, sitemap.xml and robots.txt — all in the site's own visual language
(same styles.css, nav, footer, lowercase-by-CSS, one accent).

Run after editing PAGE DATA below:   python3 tools/build_pages.py
Anything inside services/ and industries/ is overwritten on every run.
Render static sites serve pretty URLs, so /services/websites -> websites.html.
"""
import html, json, os, datetime, subprocess
from pathlib import Path

from testimonial_gate import load_testimonial_release

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://leonbuilds.org"
TODAY = datetime.date.today().isoformat()
TESTIMONIAL_DRAFTS, RELEASED_TESTIMONIALS = load_testimonial_release(
    Path(ROOT)
)
TESTIMONIAL_DRAFTS_BY_ID = {item["id"]: item for item in TESTIMONIAL_DRAFTS}
IDENTITY_URLS = [
    "https://trycurio.app/team.html#leon",
    "https://www.worldcubeassociation.org/persons/2016LILE01",
    "https://www.f6s.com/leonkelvinli",
    "https://www.linkedin.com/in/leon-kelvin-li",
    "https://github.com/Noctilucenty",
    "https://noctilucenty.github.io/",
    "https://apps.apple.com/us/developer/leon-kelvin-li/id6781121129",
    "https://www.instagram.com/lkelvn_/",
]

# ══════════════════════════════════════════════════════════════════
# PAGE DATA
# ══════════════════════════════════════════════════════════════════

SERVICES = [
 dict(slug="websites", name="small-business web design", h1=("small-business web design that turns visits into", "calls and bookings"),
  price="$300", title="Small Business Web Design | Fixed-Price Websites | Leon Builds",
  desc="Phone-first small-business web design from a California-based independent developer. Clear calls to action, fixed scope, direct communication and clean handover.",
  intro=["your website has seconds to answer four questions: what you do, who it is for, why the visitor should trust you, and what they should do next.",
   "i design fast, phone-first business websites around that decision. you work directly with the developer, see a working link during the build, and get a written scope and handover."],
  pains=["you have no website, or you're embarrassed to send people to it","it looks broken on phones","nobody on your team can change the text or the hours","it doesn't take bookings, orders or payments","you paid an agency and can't even log into your own site"],
  build=["a fast, responsive website with clear calls, quote requests, bookings or orders","search-ready titles, page structure, internal links, sitemap and structured data","editable content where the scope calls for it","the included source code and setup notes handed over; domains, hosting, fonts, plugins and other vendors keep their own terms","english, spanish, portuguese or chinese — i speak all four"],
  proof=("public product and workflow evidence","inspect a live app-store product, a public source-backed document workflow and a clearly labelled operator prototype."),
  faqs=[("how much does a website cost?","a frontend business site starts at $300. if it needs a backend — logins, a database, an admin area, apis, anything that stores or processes data — that work typically starts around $625. you get a written fixed quote before anything starts, and it doesn't change after."),
   ("i already have a website. do i have to start over?","usually not. most sites have one real problem — slow, broken on phones, or nobody can update it. a redesign is priced like a new build, from $300, and i'll tell you which parts are worth keeping."),
   ("how long does it take?","most focused business sites take one to two weeks after the scope, content and required access are ready. you get a working link to review during the build."),
   ("do you only design websites in california?","no. i am based in california and work remotely with businesses across the united states."),
   ("is seo included?","every build includes clean technical foundations: descriptive titles, crawlable links, a sitemap, mobile performance and structured content. ongoing search work is a separate scope when needed."),
   ("will i be able to update the site?","yes when editing is part of the scope. the proposal states what you can change, which accounts are yours and what is included in handover.")],
  review_ids=["testimonial-04", "testimonial-03"],
  web_guide=True,
  related=["booking-systems","seo","business-automation"]),

 dict(slug="mobile-apps", name="mobile apps", h1=("an app on the store,","not stuck in development"),
  price="$3,500", title="iOS & Android App Development — from $3,500 | Leon Kelvin Li",
  desc="Custom iOS and Android apps built end to end by one developer — through App Store review and onto the store. Fixed quotes, nationwide.",
  intro=["most app projects die between the idea and the store. agencies quote six figures; freelancer marketplaces hand you code that never passes apple's review.",
   "i've taken my own app through app store review solo — design, code, backend, subscriptions, the review process, and the appeal when review got it wrong. that whole path is what you're buying."],
  pains=["you have an app idea and no technical team","your customers keep asking 'do you have an app?'","you got an agency quote with too many zeros","someone built you an app that never made it to the store","you need the backend, accounts and payments — not just screens"],
  build=["ios and android from one codebase where that's the right call","the backend, accounts, notifications and payments behind it","app store and play submission handled, including review problems","subscriptions and in-app purchases wired correctly","agreed project accounts are set up in your name and included source code is handed over; app stores, libraries and vendors keep their terms"],
  proof=("curio — live on the app store","a consumer ios app built solo end to end: react/typescript, capacitor, express, postgres, storekit subscriptions, ai content in four languages."),
  faqs=[("what does an app cost?","full builds start at $3,500. a simple internal app costs less than a consumer app with accounts, payments and push. you get a fixed written quote first — the number doesn't move after."),
   ("ios first or both?","usually both from one codebase. if your customers are heavily iphone (common for consumer) or android (common for field crews), we start there."),
   ("who owns the app?","the agreed project accounts and store listing are set up in your name, and the included source code and backend setup notes are handed over. app stores, hosting providers, libraries and other vendors keep their own terms.")],
  related=["custom-software","websites","booking-systems"]),

 dict(slug="ai-chatbots", name="ai chatbots", h1=("answers customers,", "without inventing prices"),
  price="$750", title="AI Chatbot for Your Business — from $750 | Leon Kelvin Li",
  desc="AI chatbots trained on your business that answer customer questions on your website 24/7 — and say 'I don't know' instead of making things up.",
  intro=["most of what customers ask is the same twenty questions: hours, prices, availability, 'do you do X'. a chatbot trained on your business answers those instantly, at 2am, in multiple languages.",
   "the difference between a good one and a lawsuit is restraint: mine cite your real information and say 'i don't know — here's how to reach a person' instead of inventing a price you'll have to honour. the assistant on this site is one i built."],
  pains=["staff answer the same questions all day","after-hours visitors leave without answers","your website gets traffic but no messages","spanish or chinese-speaking customers get no help","you tried a chatbot builder and it made things up"],
  build=["a chatbot trained only on your verified business information","escalation to a human the moment it should","lead capture built in — conversations become contacts","multilingual: english, spanish, portuguese, chinese","guardrails: no invented prices, no promises you didn't make"],
  proof=("compliance-aware assistant","a chinese-language assistant for a regulated market: every claim must cite a source, and it declines to answer rather than break advertising law. try the one on this site — bottom right."),
 faqs=[("what does a chatbot cost?","from $750 for a site chatbot trained on your business. connecting it to booking or your other systems adds scope — fixed quote before anything starts."),
   ("will it say something wrong to a customer?","that risk is the whole design problem. mine only answer from your approved information, cite it, and hand off to a human when unsure. i've built one for a market where a wrong sentence breaks the law."),
   ("can it capture leads?","yes — the good ones qualify a visitor and package the conversation for you, like the assistant on this page does.")],
  review_ids=["testimonial-06"],
  related=["ai-phone-agents","business-automation","websites"]),

 dict(slug="ai-phone-agents", name="ai phone agents", h1=("your phone, answered", "at 2am and during the rush"),
  price="$1,000", title="AI Phone Agent — from $1,000 | Leon Kelvin Li",
  desc="An AI that answers your business phone, handles the repetitive calls, books appointments and hands anything unusual to a person. Built with written handoff rules.",
  intro=["missed calls are missed revenue: every call that rings out while your team is busy is a customer calling the next name on the list.",
   "an ai phone agent answers instantly, handles the repetitive calls — hours, booking, status checks — and transfers to a person the moment the call isn't routine. that handoff rule gets written down with you, not guessed."],
  pains=["calls ring out during the rush or after close","one person spends half their day on 'are you open' and 'is it ready'","voicemail is where your leads go to die","the front desk can't book and answer phones at once"],
  build=["an agent that answers every call, immediately","booking wired into your real calendar or scheduling system","status lookups from your own systems where they expose data","instant transfer to staff on anything unusual — rules in writing","call summaries so you see what customers actually ask"],
  proof=("built with the same discipline as the review desk","every ai system i ship keeps a human in the loop by design — the review desk drafts replies but a person presses send. phone agents get the same treatment."),
 faqs=[("what happens when the ai can't handle a call?","it transfers to a person, following escalation rules we write down together before launch. the goal is removing repetitive calls, not removing humans."),
   ("what does it cost?","from $1,000 depending on what the agent needs to do — answering and booking is simpler than pulling live order status from your systems."),
   ("does it work with my scheduling software?","often, if your system exposes the data. i verify the specific integration before quoting rather than promising first.")],
  review_ids=["testimonial-05"],
  related=["ai-chatbots","booking-systems","business-automation"]),

 dict(slug="business-automation", name="business automation", h1=("the follow-ups happen", "whether anyone remembers or not"),
  price="$500", title="Workflow & Business Automation — from $500 | Leon Kelvin Li",
  desc="Form-to-sheet-to-email workflows, Google Workspace and n8n automation, and integrations that stop your team copying data between systems by hand.",
  intro=["most 'we need software' problems are actually 'two systems don't talk' problems. the fix is rarely a new platform — it's a pipe between the tools you already pay for.",
   "i build those pipes where your team can see them: google workspace automations in apps script, n8n workflows your staff can read and edit, and integrations with quickbooks, stripe, slack, your pos, your ats."],
  pains=["data gets copied between systems by hand","new leads and form submissions sit unanswered","reports take hours of exporting and pasting","approvals and handoffs live in someone's memory","five tools, none of them talking to each other"],
  build=["form → sheet → document → email chains, end to end","n8n pipelines your team can edit without calling me","integrations: quickbooks, stripe, google, slack, twilio, your pos","automatic reports that build themselves on schedule","document workflows: created, filed, approved, versioned"],
  proof=("document control","a request names a template; seconds later the google doc exists, filed and shared correctly. approval locks it, publishing versions it. built in apps script, then again as six n8n workflows the team edits themselves."),
  faqs=[("what should i automate first?","the thing a person does most often with the least judgment — retyping, forwarding, filing. we find it in the free call; it's usually obvious within ten minutes."),
   ("is this ai?","mostly not, and that's a feature. deterministic automations are cheaper and more reliable. ai enters only where reading or drafting is involved."),
   ("what does it cost?","workflow automation starts at $500. a single pipe between two systems is the low end; multi-step pipelines touching several systems scale from there. after launch, the event log and time spent on the old process give you a concrete way to judge whether the automation is worth keeping or expanding.")],
  review_ids=["testimonial-05"],
  related=["business-dashboards","ai-chatbots","custom-software"]),

 dict(slug="custom-software", name="custom software", h1=("built around how your", "business actually runs"),
  price="$1,500", title="Custom Software Development | Leon Kelvin Li",
  desc="Custom business software built end to end by one developer: portals, platforms, operations systems. Fixed written quotes. U.S.-wide, remote.",
  intro=["off-the-shelf software fits the average business. yours isn't average — that's why there's still a spreadsheet holding part of it together.",
   "custom software is for when nothing on the menu is the shape of your problem. the public Home Screen prototype, for example, tests server-side pricing and vendor-separated order logic while clearly keeping payments and kitchen operations mocked."],
  pains=["you've outgrown the spreadsheet that runs part of the business","off-the-shelf tools each do 70% of what you need","your industry has a workflow no product understands","you're paying for five subscriptions to approximate one system"],
  build=["operations systems designed around your real workflow","web apps your team logs into every day","the database, accounts, permissions and reports underneath","migrations off the spreadsheet without losing history","one system replacing several almost-right subscriptions"],
  proof=("the Home Screen operator prototype","a public prototype with business-specific menus, server-side pricing and vendor-scoped demo tickets. payments and kitchen operations are not live."),
 faqs=[("how do i know custom is worth it vs off-the-shelf?","if an existing product does 90% of what you need, buy it — i'll tell you so in the free call. custom wins when the missing 30% is the part your business actually runs on."),
   ("what does custom software cost?","full builds start at $1,500 and scale with scope. quotes are written and fixed, with staged payments tied to milestones you can see working."),
   ("what happens if you get hit by a bus?","the agreed repo and project accounts, included source code and setup documentation are handed over. third-party hosts and licensed services keep their terms, and another competent developer can use the handoff — nothing is set up to make me irreplaceable.")],
  review_ids=["testimonial-02", "testimonial-07"],
  related=["mobile-apps","business-automation","business-dashboards"]),

 dict(slug="booking-systems", name="booking & online ordering", h1=("customers book and order themselves —", "the reminder does the rest"),
  price="$600", title="Booking & Online Ordering — from $600 | Leon Kelvin Li",
  desc="Booking and ordering on your website: appointments, deposits, reminders and a direct-order cart. Leon charges no booking fee; provider terms still apply.",
  intro=["every booking handled by phone uses staff time, and every no-show leaves a slot unused. online booking removes the retyping; reminders, deposits and easy rescheduling give you measurable ways to address missed appointments.",
   "i build booking around your site, calendar and rules instead of defaulting to a generic branded widget. any payment, messaging, hosting or calendar-provider fees stay visible in the written scope.",
   "ordering works the same way. a direct cart gives returning customers a channel you control. marketplace, card, delivery and hosting costs vary by provider and contract, so the comparison uses your real statements."],
  pains=["booking happens by phone and eats front-desk time","no-shows are killing your calendar","after-hours visitors can't book and don't call back","a delivery app takes a cut of every order and owns your customer","your current booking tool takes a cut or looks like an ad for itself"],
  build=["booking pages that match your site, not a widget's brand","staff calendars, service durations, buffer rules","deposits and card-on-file through stripe","automatic sms/email reminders and easy rescheduling","sync with the calendar your team already lives in","direct ordering with no per-order commission added by Leon: cart, payment, and a ticket that reaches the kitchen"],
  proof=("built like the ordering system","the same server-side discipline as the multi-brand ordering platform: rules enforced where customers can't edit them."),
  faqs=[("what does a booking system cost?","from $600 built into your site, and direct online ordering from $600. leon charges no monthly per-booking or per-order cut; payment, messaging, hosting and other provider terms still apply."),
   ("can customers pay a deposit when they book?","yes — deposits, full prepayment or card-on-file, through stripe, with receipts handled."),
   ("we already use a scheduling tool. keep it?","if it works, keep it — sometimes the right build is your website talking to it. i'll tell you which in the free call.")],
  related=["websites","ai-phone-agents","business-automation"]),

 dict(slug="business-dashboards", name="dashboards & internal tools", h1=("the four numbers that decide", "your week, on one screen"),
  price="$750", title="Dashboards & Internal Tools — from $750 | Leon Kelvin Li",
  desc="Live dashboards and focused internal tools that replace manual exports, surface the numbers that matter and remove repetitive copy-paste from daily work.",
  intro=["somebody on your team spends part of every week exporting, pasting and reformatting the same report. and by the time it's read, it's old.",
   "a dashboard pulls those numbers live from the systems that already have them — sales, bookings, stock, ad spend — onto one screen you check in ten seconds.",
   "the same goes for a job somebody repeats forty times a day in six clicks. a focused internal tool can shorten that path, and the scope can define exactly which clicks or minutes to measure before and after."],
  pains=["reports are assembled by hand every week","the numbers live in five different logins","you find out about a bad week after it's over","a repetitive task eats hours across the team","the answer to 'how do we know this number' is 'ask the one person who knows'"],
  build=["live dashboards fed straight from your real systems","the handful of numbers that matter, not eighty charts","alerts when a number crosses a line you set","scheduled email summaries for people who won't open a dashboard","clean history so trends are visible, not remembered","chrome extensions and small tools built for the exact job, nothing else"],
  proof=("site intelligence","decision support scoring all 33,772 us zip codes across nine data sources — with every score carrying an uncertainty band instead of false precision. dashboards are the small sibling of that discipline."),
 faqs=[("what does a dashboard cost?","both a small internal tool and a dashboard start at $750, and scale with how many systems have to feed them. fixed quote before work starts."),
   ("our data is a mess. does that matter?","that's normal — cleaning and joining it is part of the build, not a surcharge surprise."),
   ("can it pull from our pos / quickbooks / sheets?","usually yes. i verify your specific systems before quoting.")],
  review_ids=["testimonial-02"],
  related=["business-automation","ai-chatbots","custom-software"]),

 dict(slug="seo", name="technical seo & ai search", h1=("technical seo for google —", "structured for ai search"),
  price="$300", title="Technical SEO & AI Search Optimization | Leon Builds",
  desc="Technical SEO, Search Console cleanup and answer-ready site structure. Measurable changes without fake locations, ranking promises or mass content.",
  intro=["google search and ai answer systems both need a crawlable site, clear language, useful pages and claims they can verify. there is no separate shortcut that replaces those fundamentals.",
   "i fix the technical and content structure: titles, internal links, indexing, schema, sitemaps, page speed and direct answers to real buyer questions — without fake city pages or mass-produced articles."],
  pains=["google has discovered pages but does not index the ones that matter","the site never says the service in the words customers search","important pages are buried or linked with vague anchor text","nobody measures impressions, clicks, calls or inquiries after a change"],
  build=["search console and index-coverage diagnosis","titles, descriptions, headings, canonicals, sitemaps and crawlable internal links","useful service and industry pages with distinct buyer answers","structured data that matches visible content","clear entity, proof and citation paths for answer systems","measurement tied to calls, quote requests and bookings"],
  proof=("this site's public search foundation","inspect the clean sitemap, canonical pages, reciprocal language clusters, public proof links and structured data. none of those is presented as a ranking guarantee."),
  faqs=[("how is ai search different from seo?","there is no special markup that guarantees ai visibility. clear, crawlable, useful pages and verifiable claims support both traditional search and answer systems."),
   ("what does it cost?","from $300 for a technical pass on an existing site. ongoing work is scoped in writing — no vague monthly retainer."),
   ("can you guarantee rankings?","no. i can document the changes, validate the technical implementation and measure impressions, clicks and inquiries, but search engines decide rankings."),
   ("do i need an llms.txt file?","it can provide a concise factual index for some systems, but it is not a google ranking control. the main work still belongs in visible pages, normal links and accurate structured data.")],
  related=["websites","ai-chatbots","business-dashboards"]),
]

INDUSTRIES = [
 dict(slug="restaurants", name="restaurants & food", h1=("restaurant web design,", "online ordering & automation"),
  title="Restaurant Website Design & Online Ordering | Leon Builds",
  desc="Phone-first restaurant website design, direct online ordering, menu updates and call automation from one California-based developer serving U.S. businesses.",
  intro=["restaurants run on thin margins while marketplace terms vary and the phone pulls staff away during a rush. a direct website can add a channel you control alongside the platforms that bring discovery.",
   "the public Home Screen prototype shows the underlying interaction: business-specific menus, server-side pricing and vendor-scoped demo tickets. payments and kitchen operations remain mocked."],
  pains=["delivery apps take a commission on orders that were already yours","the phone rings out during every rush","your menu is a pdf nobody can read on a phone","'are you open' and 'do you have parking' — forty times a day","multiple locations or brands, zero shared systems"],
  fixes=[("online ordering you own","direct ordering with no per-order commission added by Leon — cart, payment, kitchen ticket. from $600","booking-systems"),
   ("ai phone agent","answers during the rush, takes the routine calls, hands the rest to staff. from $1,000","ai-phone-agents"),
   ("a menu-first website","fast, phone-first, editable by you when prices change. from $300","websites"),
   ("review desk","every review read and a reply drafted for you — a human presses send. from $750",None)],
  proof=("the Home Screen operator prototype","open the public prototype to inspect business-specific menus, server-side pricing and vendor-scoped demo tickets. payments and kitchen operations are not live."),
  faqs=[("can i stop paying delivery-app commissions?","you can give regular customers a direct pickup or own-delivery option without Leon adding a per-order cut. marketplaces can still be useful for discovery, while payment, hosting, messaging and delivery providers keep their own terms."),
   ("what does online ordering cost?","from $600 one-time for ordering on your own site; leon charges no per-order cut. payment, hosting and other provider fees still apply. compare that to a month of commissions."),
   ("i have two locations with different menus.","that can be handled with a shared site and separate location menus, hours and order routing. the exact payment and kitchen integrations are verified before quoting.")],
  related_services=["booking-systems","ai-phone-agents","websites"]),

 dict(slug="contractors", name="contractors & home services", h1=("contractor web design &", "lead follow-up"),
  title="Contractor Web Design & Lead Follow-Up | Leon Builds",
  desc="Contractor website design, quote-request capture, lead follow-up and job workflows for U.S. home-service businesses, built directly by Leon.",
  intro=["contracting work is won and lost in the follow-up: the lead that came in while you were on a roof, the estimate that never went out, the customer who called someone else because you answered second.",
   "software fixes the boring half of that — instant lead responses, scheduling, job status a customer can check without calling you."],
  pains=["leads arrive while you're on site and go cold","estimates and invoices happen at 9pm from the truck","customers call constantly for status updates","jobs live on a whiteboard or in one person's head","reviews never get asked for, so the profile looks dead"],
  fixes=[("lead follow-up automation","every web lead gets an instant text/email and lands in one list. from $600","business-automation"),
   ("scheduling & job tracking","jobs, crews and dates in one system the whole team sees. from $1,500","custom-software"),
   ("customer portal","clients see their own job status, photos and invoices. from $1,500","custom-software"),
   ("a website that sells","before/after work, service areas, instant quote requests. from $300","websites")],
  proof=("document control","approvals, versioned documents and automatic filing — the same machinery that keeps a contracting back office from living in someone's memory."),
  faqs=[("i'm not technical at all. is that a problem?","no. you describe the week, i build around it, and everything is handed over working with training included."),
   ("where is a practical place to start?","lead follow-up is often a focused first workflow because response timing and handoffs can be measured. compatible standard scopes start at $600; timing depends on the tools and access involved."),
   ("do you work outside california?","yes — remote across the u.s. this kind of build never needs me on site.")],
  related_services=["business-automation","custom-software","websites"]),

 dict(slug="automotive", name="auto repair & automotive", h1=("auto repair web design,", "booking & call automation"),
  title="Auto Repair Website Design & Booking | Leon Builds",
  desc="Auto repair website design, online booking, status updates and call automation for U.S. shops, built directly by one California-based developer.",
  intro=["every shop knows the two calls: 'can i bring it in?' and 'is it ready yet?'. both interrupt the person doing the actual work.",
   "booking can go straight into your calendar. status can text the customer automatically the moment a job changes state — and an ai phone agent can answer the rest."],
  pains=["'is my car ready' calls interrupt the bay all day","booking happens by phone and gets double-entered","customers wait on hold, then show up at the wrong time","your shop software has the data but customers can't see it"],
  fixes=[("automatic status updates","'your car is ready' sends itself when the job closes. from $600","business-automation"),
   ("online booking","customers pick a slot; your calendar stays sane. from $600","booking-systems"),
   ("ai phone agent","handles hours, booking and routine status; transfers the rest. from $1,000","ai-phone-agents"),
   ("shop website","services, trust proof, booking and a clear call path on any phone. from $300","websites")],
  proof=("public implementation evidence","inspect shipped product screens, a source-backed workflow demo and a clearly labelled operator prototype; none is presented as an automotive outcome claim."),
  faqs=[("does this work with my shop management system?","often — many expose the data needed for status and booking. i verify yours specifically before quoting anything."),
   ("what is a focused first step?","status notifications can reduce manual update calls when the shop system exposes reliable status data. i verify that data and define what will be measured before quoting."),
   ("multiple locations?","yes — shared platform, per-location calendars and numbers is a normal build.")],
  related_services=["ai-phone-agents","booking-systems","business-automation"]),

 dict(slug="healthcare", name="medical & dental", h1=("software for", "medical & dental practices"),
  title="Software for Medical & Dental Offices | Leon Kelvin Li",
  desc="Online booking, appointment reminders and after-hours question handling for clinics and dental practices. Careful, human-in-the-loop builds.",
  intro=["a practice front desk answers the same questions all day — insurance, hours, directions, 'can i move my appointment' — while missed appointments leave unused time. reminders and self-service rescheduling address one part of that workflow and can be measured against the current baseline.",
   "health care deserves the careful version of software: reminders and booking that reduce the front desk load, an assistant that answers the routine and hands anything clinical straight to a human. i've built compliance-aware ai that declines to answer rather than overstep — that's the posture your patients get."],
  pains=["no-shows burn schedule and revenue","the phone queue is insurance and reschedule questions","after-hours callers reach voicemail and book elsewhere","forms are still paper or pdf-by-email"],
  fixes=[("appointment reminders","sms/email sequences with timing and opt-out rules; track confirmations, reschedules and missed appointments. from $600","booking-systems"),
   ("online booking & rescheduling","patients handle the routine moves themselves. from $600","booking-systems"),
   ("after-hours question handling","routine questions answered; anything clinical goes to staff. from $1,000","ai-phone-agents"),
   ("digital intake forms","filled on a phone before the visit, filed automatically. from $600","business-automation")],
  proof=("compliance-aware assistant","a health-education assistant for a regulated market: deterministic safety rules run before any model, every claim cites a source, and it declines rather than break the rules. that is the standard of care i bring near medicine."),
  faqs=[("is this hipaa compliant?","builds are designed so sensitive data stays in your existing systems wherever possible, and i'm direct about what i will and won't touch. compliance requirements get scoped in writing before anything starts — never assumed."),
   ("will ai talk to my patients about medical questions?","no. routine logistics only — anything clinical routes to your staff. i build assistants that decline rather than guess."),
   ("what does this cost?","reminders and intake from about $600; booking from $600. fixed written quotes.")],
  related_services=["booking-systems","ai-chatbots","business-automation"]),

 dict(slug="real-estate", name="real estate & property", h1=("software for", "real estate & property management"),
  title="Software for Real Estate & Property | Leon Kelvin Li",
  desc="Tenant portals, maintenance-request tracking, listing sites and follow-up automation for property managers and real-estate businesses.",
  intro=["property work is coordination: tenants, owners, vendors, showings, maintenance — most of it still happening over scattered calls and texts nobody can find later.",
   "a portal gives tenants somewhere to submit and track requests. automation gives owners their statements without you assembling them. your phone gets quieter."],
  pains=["maintenance requests arrive by call and text, then get lost","tenants call for updates because there's nowhere to look","owner statements are assembled by hand every month","showings and applications live in three inboxes"],
  fixes=[("tenant portal","submit a request, attach a photo, watch the status change. from $1,500","custom-software"),
   ("maintenance tracking","requests routed to vendors, updates sent automatically. from $1,000",None),
   ("owner reporting","statements that build themselves from your real data. from $1,000","business-dashboards"),
   ("listing website","fast property pages with inquiry capture that reaches you instantly. from $300","websites")],
  proof=("Loqol disclosure workflow","a public demo and source repository showing per-user saved answers, an agent review workspace, consistency checks and generated documents. signing and email delivery are incomplete."),
  faqs=[("can tenants see each other's information?","no — per-account visibility is enforced on the server, which is the core of the build."),
   ("we use appfolio / buildium / yardi.","keep it if it works — often the right build is a portal or automation talking to your existing system. i verify the integration before quoting."),
   ("what does a tenant portal cost?","from $1,500 depending on what tenants and owners need to see and do.")],
  related_services=["custom-software","business-automation","websites"]),

 dict(slug="logistics", name="logistics & warehousing", h1=("software for", "logistics & warehousing"),
  title="Software for Logistics & Trucking | Leon Kelvin Li",
  desc="Dispatch boards, driver apps, document automation and customer tracking for logistics and warehouse operations.",
  intro=["logistics runs on information handoffs — and every handoff that happens by phone, email-forward or retyping is a delay and an error waiting to happen.",
   "dispatchers copying between emails and spreadsheets, drivers texting photos of paperwork, customers calling for eta: each of those is a solved software problem."],
  pains=["dispatch copies the same info between email, sheets and texts","drivers hand in paperwork that gets retyped","customers call for status because they can't see it","inventory counts drift from reality"],
  fixes=[("dispatch board","loads, drivers and statuses on one live screen. from $1,500","custom-software"),
   ("driver app","photos, signatures and status from the cab — no retyping. from $3,500","mobile-apps"),
   ("document automation","pods, bols and invoices extracted and filed automatically. from $500","business-automation"),
   ("customer tracking portal","they look it up instead of calling you. from $1,500","custom-software")],
  proof=("site intelligence","a decision system across 33,772 zip codes and nine data sources — the data discipline logistics operations run on, applied end to end."),
  faqs=[("our process is unusual. can software fit it?","unusual processes are the reason custom exists — the build is shaped around your real workflow, not a template's guess."),
   ("what's the first thing to fix?","usually the dispatch copy-paste loop — highest error rate, easiest automation."),
   ("do drivers need new hardware?","no — driver tools run on the phones they already carry.")],
  related_services=["custom-software","business-dashboards","websites"]),

 dict(slug="gyms", name="gyms & fitness", h1=("software for", "gyms & fitness businesses"),
  title="Software for Gyms & Fitness | Leon Kelvin Li",
  desc="Class booking, membership management, reminder automation and websites for gyms, studios and trainers.",
  intro=["a gym's software problem is churn wearing a disguise: missed classes, lapsed cards, members who drift because nobody noticed they stopped coming.",
   "booking, reminders and a membership view fix the mechanics — you see who's fading while there's still time to wave them back."],
  pains=["class booking happens by dm and spreadsheet","no-shows leave paid slots empty","failed card payments quietly become lost members","you can't see who's about to churn until they're gone"],
  fixes=[("class booking","members book, waitlist and cancel themselves. from $600","booking-systems"),
   ("membership dashboard","attendance, payments and fade-outs on one screen. from $1,000","business-dashboards"),
   ("reminder automation","class reminders and win-back nudges that send themselves. from $600","business-automation"),
   ("a site that converts","schedule, pricing and signup without a phone call. from $300","websites")],
  proof=("curio","a consumer subscription app on the app store — retention mechanics, streaks and subscriptions are literally what it runs on."),
  faqs=[("we use mindbody / glofox. switch?","only if it's failing you. often the right move is automation around what you have — i'll say which in the free call."),
   ("can members pay online?","yes — stripe subscriptions, class packs and drop-ins, with receipts and failed-payment recovery."),
   ("what does this cost?","booking from $600; most gym builds land between $600 and $3,500.")],
  related_services=["booking-systems","websites","business-dashboards"]),

 dict(slug="retail", name="retail & e-commerce", h1=("software for", "retail & e-commerce"),
  title="Software for Retail & E-commerce | Leon Kelvin Li",
  desc="Inventory that survives a busy Saturday, order automation, dashboards and storefronts for retailers and e-commerce operators.",
  intro=["retail dies by a thousand small syncs: the count that drifted, the online order nobody saw, the bestseller that sold out because reordering lived in someone's head.",
   "the fix is rarely a new platform — it's the connective tissue: inventory that matches reality, orders flowing into one queue, numbers you see daily without exporting anything."],
  pains=["stock counts drift from reality","online and in-store systems don't talk","reordering depends on someone noticing","you learn about a bad week from the bank balance"],
  fixes=[("inventory system","stock, suppliers and low-stock alerts that survive a rush. from $1,500","custom-software"),
   ("order automation","every channel's orders into one queue with alerts. from $600","business-automation"),
   ("sales dashboard","today's numbers without opening five systems. from $1,000","business-dashboards"),
   ("storefront","fast product pages, clean checkout, no template bloat. from $300","websites")],
  proof=("the Home Screen operator prototype","a public prototype showing business-specific catalogs, menus, server-side pricing and vendor-scoped demo tickets. payments and fulfillment are not live."),
  faqs=[("we're on shopify / square. is that a problem?","no — keep them. most retail builds connect and automate around the platform you're on."),
   ("can inventory sync between online and the register?","usually yes, depending on your pos. i verify the specific integration before quoting."),
   ("what should we fix first?","whatever loses money silently — usually inventory drift or unwatched online orders.")],
  related_services=["business-automation","business-dashboards","websites"]),

 dict(slug="professional-services", name="professional services", h1=("software for", "professional services"),
  title="Software for Professional Firms | Leon Kelvin Li",
  desc="Client portals, intake automation, document workflows and dashboards for law, accounting, consulting and agency work.",
  intro=["service firms sell hours, then spend a shocking share of them on intake, status emails, document wrangling and 'just checking in' calls.",
   "a client portal, automated intake and document workflows give those hours back — and make the firm feel bigger and calmer than the inbox it replaced."],
  pains=["intake is a pdf emailed back and forth","clients email for status because there's nowhere to look","documents have four versions in three inboxes","billable time leaks into administration"],
  fixes=[("client portal","cases, files, invoices and status in one login. from $1,500","custom-software"),
   ("intake automation","forms that fill in on a phone, file and notify automatically. from $600","business-automation"),
   ("document workflows","created, versioned, approved and filed — automatically. from $500","business-automation"),
   ("firm dashboard","matters, pipeline and billing on one screen. from $1,000","business-dashboards")],
  proof=("Loqol guided document workflow","a public demo and source repository showing a long questionnaire, saved answers, consistency checks, an agent review view and generated PDF output."),
  faqs=[("is client data safe?","per-client visibility is enforced server-side. the agreed project accounts, included source code and setup notes are handed over, while hosting providers, licensed software and other vendors keep their own terms. your reviewer can audit the included code."),
   ("we bill hourly. does this change that?","it removes the hours you can't bill — admin — and keeps the ones you can."),
   ("what does a portal cost?","from $1,500; intake automation from $600. written fixed quotes.")],
  related_services=["custom-software","business-automation","business-dashboards"]),

 dict(slug="startups", name="startups", h1=("software for", "startups & founders"),
  title="MVP & Product Development for Startups | Leon Kelvin Li",
  desc="MVPs that actually ship: app + backend + payments from one developer who has taken his own product through App Store review.",
  intro=["a founder with an idea needs the version of the product that can meet users — not a six-month engagement, not a no-code demo that collapses at the first real feature.",
   "i've shipped my own consumer app solo: design, code, backend, subscriptions, app store review, the appeal when review got it wrong. that end-to-end path is what an mvp needs; the agreed repo, included source and setup notes are part of the written handoff, while third-party and licensed terms remain."],
  pains=["you have the idea and the users, not the technical team","agency quotes start at six figures","the no-code prototype hit its ceiling","your technical co-founder search is month six"],
  fixes=[("mvp build","the smallest version that real users can use — app or web. from $3,500","custom-software"),
   ("app + backend + payments","the whole stack, not just screens. from $3,500","mobile-apps"),
   ("ai features","assistants, retrieval and pipelines with guardrails that hold. from $1,000","ai-chatbots"),
   ("ongoing development","a standing block of hours as you see fit. from $400/mo",None)],
  proof=("curio","consumer ios app on the app store: react/typescript, capacitor, express, postgres, storekit subscriptions, ai content in four languages — built alone."),
  faqs=[("how fast can an mvp ship?","weeks, not quarters — scope decides. we cut to the version that tests the idea, in writing, before building."),
   ("do i own the code?","the agreed repo and project accounts, plus the source code and setup notes included in scope, are handed over. third-party infrastructure, app stores, libraries and other licensed services keep their own terms. investors can review the written handoff."),
   ("can you keep building after launch?","yes — ongoing from $400/mo, or fixed quotes per milestone as you raise.")],
  related_services=["mobile-apps","custom-software","ai-chatbots"]),
]

# ══════════════════════════════════════════════════════════════════
# TEMPLATE
# ══════════════════════════════════════════════════════════════════

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@200;300;400;500;600&amp;family=Space+Grotesk:wght@300;400;500&amp;display=swap" rel="stylesheet">'

def e(s): return html.escape(str(s), quote=True)


def testimonial_card(testimonial_id, classes="testimonial-card"):
    """Render one exact, individually released testimonial or nothing."""
    item = RELEASED_TESTIMONIALS.get(testimonial_id)
    if not item:
        return ''
    stars = ''
    if item["show_rating"]:
        stars = '<p class="testimonial-stars" aria-label="5 out of 5 stars">★★★★★</p>'
    return (
        f'<article class="{e(classes)}" data-testimonial-id="{e(testimonial_id)}">'
        f'{stars}<p class="testimonial-project">{e(item["project"])}</p>'
        f'<blockquote>“{e(item["quote"])}”</blockquote>'
        f'<p class="testimonial-person"><strong>{e(item["attribution"])}</strong>'
        f'<span>{e(item["attribution_context"])}</span></p></article>'
    )


def testimonial_cards(testimonial_ids, classes="testimonial-card"):
    return ''.join(testimonial_card(testimonial_id, classes) for testimonial_id in testimonial_ids)


def homepage_testimonial_section():
    """Generate the homepage section only from the explicit release manifest."""
    released_ids = [
        item["id"] for item in TESTIMONIAL_DRAFTS if item["id"] in RELEASED_TESTIMONIALS
    ]
    if not released_ids:
        return ''
    first = testimonial_cards(released_ids[:3])
    remaining = testimonial_cards(released_ids[3:], "testimonial-card testimonial-wide")
    more = ''
    if remaining:
        more = f'''<details class="testimonial-more">
      <summary><span>See more approved client feedback</span></summary>
      <div class="testimonial-grid testimonial-grid-more">{remaining}</div>
    </details>'''
    count = len(released_ids)
    noun = "review" if count == 1 else "reviews"
    return f'''<section class="sec reviews-early" id="testimonials">
  <div class="rail">
    <header class="sec-head reviews-head">
      <div><p class="label">{count} direct client {noun}</p>
        <h2 class="dsp">Feedback on real <em>business projects.</em></h2></div>
      <p class="sub business-copy">Exact project-specific feedback published with client approval.</p>
    </header>
    <div class="testimonial-grid">{first}</div>
    {more}
  </div>
</section>'''

def nav():
    return '''<a class="skip" href="#main">skip to content</a>
<div class="progress" id="progress" aria-hidden="true"></div>
<div class="cursor" id="cursor" aria-hidden="true"><span></span></div>
<header class="nav" id="nav">
  <a class="mark" href="/">
    <span class="mark-dot">[<span class="blink">•</span>]</span>
    <span class="mark-name">Leon Kelvin Li</span>
    <span class="mark-handle">/ Leon Builds</span>
  </a>
  <nav class="nav-mid" id="navMid" aria-label="site">
    <a href="/#fix"><i>[</i><span>start here</span><i>]</i></a>
    <a href="/services/"><i>[</i><span>services</span><i>]</i></a>
    <a href="/industries/"><i>[</i><span>industries</span><i>]</i></a>
    <a href="/#work"><i>[</i><span>work</span><i>]</i></a>
    <a href="/#pricing"><i>[</i><span>pricing</span><i>]</i></a>
    <a class="nav-book" href="/call"><i>[</i><span>book a 15-min call</span><i>]</i></a>
  </nav>
  <div class="nav-end">
    <a class="btn btn-solid magnet" href="/call" data-evt="nav_call_click"><span>book a 15-min call</span></a>
    <button class="burger" id="burger" aria-expanded="false" aria-controls="navMid" aria-label="menu"><span></span><span></span></button>
  </div>
</header>'''

def footer():
    slinks = ''.join(f'<a href="/services/{s["slug"]}">{e(s["name"])}</a>' for s in SERVICES)
    ilinks = ''.join(f'<a href="/industries/{i["slug"]}">{e(i["name"])}</a>' for i in INDUSTRIES)
    return f'''<footer class="foot">
  <div class="rail foot-in">
    <div class="foot-brand">
      <a class="mark" href="/"><span class="mark-dot">[<span class="blink">•</span>]</span><span class="mark-name">Leon Kelvin Li</span><span class="mark-handle">/ Leon Builds</span></a>
      <p>small-business web design and custom software, built directly by one developer for businesses across the united states.</p>
      <p class="avail"><i></i>available for new projects</p>
    </div>
    <nav><h4>services</h4>{slinks}</nav>
    <nav><h4>industries</h4>{ilinks}</nav>
    <nav><h4>site</h4><a href="/about">about leon</a><a href="/call">book a call</a><a href="/#work">public work</a><a href="/#pricing">pricing</a><a href="/#faq">faq</a><a href="/quote">get a quote</a><a href="/privacy">privacy</a><a href="https://github.com/Noctilucenty" target="_blank" rel="noopener">github</a></nav>
  </div>
  <div class="rail foot-bar">
    <p>© <span id="yr">2026</span> <span class="keepcase">Leon Kelvin Li</span> · california · working with businesses across the u.s.</p>
    <p><a href="mailto:leondragon3798@gmail.com" data-evt="footer_email_click">leondragon3798@gmail.com</a> · <a href="tel:+15108267735" data-evt="footer_phone_click">(510) 826-7735</a></p>
  </div>
</footer>
<script src="/app.js" defer></script>
<script src="/assist.js" defer></script>'''

def head(title, desc, path, schema, alts='', head_extra=''):
    """alts carries the hreflang cluster. Hreflang only works when it is
    RECIPROCAL — a Portuguese page pointing at its English twin while the twin
    stays silent is a cluster Google discards, so the English service pages that
    have translations must name them back. head_extra is reserved for page-only
    identity metadata so it does not leak into the generated page fleet."""
    head_links = "\n".join(link for link in (alts, head_extra) if link)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#000000">
<meta name="color-scheme" content="dark">
<link rel="canonical" href="{BASE}{path}">
{head_links}
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}{path}">
<meta property="og:site_name" content="Leon Builds">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{BASE}/assets/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
{FONTS}
<link rel="stylesheet" href="/styles.css">
<link rel="stylesheet" href="/assist.css">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
</head>
<body>'''

def crumbs(items):
    parts = ' <i>/</i> '.join(f'<a href="{h}">{e(t)}</a>' if h else f'<span>{e(t)}</span>' for t, h in items)
    return f'<p class="crumbs">{parts}</p>'

def breadcrumb_schema(items, path):
    return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":i+1,"name":t,"item":BASE+(h or path)} for i,(t,h) in enumerate(items)]}

def faq_schema(faqs):
    return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faqs]}

def faq_html(faqs):
    out = '<div class="faq">'
    for q,a in faqs:
        out += f'<details><summary>{e(q)}<i></i></summary><p>{e(a)}</p></details>'
    return out + '</div>'

def cta_block(starter):
    return f'''<div class="ctarow">
      <a class="btn btn-solid magnet" href="/call" data-evt="cta_call_click"><span>book a free 15-minute call</span><svg class="ic"><use href="#ic-arrow"/></svg></a>
      <a class="btn magnet" href="/quote" data-evt="pricing_cta_click"><span>get a fixed quote</span></a>
      <a class="cx-mini" href="mailto:leondragon3798@gmail.com" data-evt="email_click">or email leon directly →</a>
    </div>
    <p class="assist-fallback">Not ready to talk? <button class="linklike" type="button" data-assist-open data-assist-starter="{e(starter)}">Describe the problem to the site assistant.</button></p>'''

ICONS = '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="ic-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h15M13 6l6 6-6 6"/></symbol><symbol id="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 12.5l5 5 10-11"/></symbol></svg>'


# Proof links must land on visible, current public evidence. Unreleased client
# feedback is never a proof destination.
WORK_ANCHORS = [
    ('home screen', '#work-homescreen'),
    ('ordering', '#work-homescreen'),
    ('operator prototype', '#work-homescreen'),
    ('loqol', '#work-loqol'),
    ('curio', '#work-curio-public'),
]

def work_link(proof_title):
    t = (proof_title or '').lower()
    for needle, anchor in WORK_ANCHORS:
        if needle in t:
            return '/' + anchor
    return '/#work'

def service_page(s):
    path = f'/services/{s["slug"]}'
    bc = [("home","/"),("services","/services/"),(s["name"], None)]
    offer_price = s["price"].replace('$', '').replace(',', '')
    schema = [
        {"@context":"https://schema.org","@type":"Service","@id":BASE+path+"#service",
         "name":s["name"], "url":BASE+path, "serviceType":s["name"],
         "mainEntityOfPage":BASE+path,
         "provider":{"@id":BASE+"/#leon"},
         "areaServed":{"@type":"Country","name":"United States"},
         "description":s["desc"],
         "offers":{"@type":"Offer","url":BASE+path,"price":offer_price,"priceCurrency":"USD",
                   "description":"Published starting price; final fixed quote depends on the written scope."}},
        faq_schema(s["faqs"]), breadcrumb_schema(bc, path)]
    pains = ''.join(f'<li>{e(p)}</li>' for p in s["pains"])
    build = ''.join(f'<li><svg class="ic"><use href="#ic-check"/></svg>{e(b)}</li>' for b in s["build"])
    intro = ''.join(f'<p class="sub">{e(p)}</p>' for p in s["intro"])
    related = ''.join(f'<a class="rel" href="/services/{r}">{e(next(x["name"] for x in SERVICES if x["slug"]==r))} →</a>' for r in s["related"])
    starter = f'i\'m looking at {s["name"]} — here\'s my situation: '
    reviews = ''
    cards = testimonial_cards(s.get("review_ids", []), "service-review")
    if cards:
        review_heading = ("What website clients said after the build"
                          if s["slug"] == "websites"
                          else "What clients said about related work")
        reviews = f'''<section class="sec service-reviews">
  <div class="rail">
    <p class="label">direct client feedback</p>
    <h2 class="page-section-title">{e(review_heading)}</h2>
    <div class="service-review-grid">{cards}</div>
    <a class="cx-mini" href="/#testimonials">read approved client feedback →</a>
  </div>
</section>
'''
    web_guide = ''
    if s.get("web_guide"):
        web_guide = '''<section class="sec web-guide">
  <div class="rail">
    <p class="label">small-business website decision guide</p>
    <h2 class="page-section-title">What your website must answer in five seconds</h2>
    <p class="sub">A visitor should not have to hunt for the basics. The first screen needs to make these decisions easy.</p>
    <div class="answer-grid">
      <article><span>01</span><h3>What do you do?</h3><p>Name the service in the words customers search and use.</p></article>
      <article><span>02</span><h3>Who is it for?</h3><p>Make the customer, service area, or situation unmistakable.</p></article>
      <article><span>03</span><h3>Why trust you?</h3><p>Show real work, direct feedback, credentials, or a verifiable result.</p></article>
      <article><span>04</span><h3>What happens next?</h3><p>Give one obvious action: call, book, order, or request a quote.</p></article>
    </div>
  </div>
</section>
<section class="sec web-scope-guide">
  <div class="rail">
    <p class="label">choose the smallest useful scope</p>
    <h2 class="page-section-title">Website cost depends on what the site must do</h2>
    <div class="scope-grid">
      <article><span>01</span><h3>Frontend presence site</h3><p>A fast, responsive site with your offer, proof, contact path and handover. Starts at $300.</p></article>
      <article><span>02</span><h3>Website with a backend</h3><p>Accounts, a database, an admin area or APIs add application work. Typically starts at $625.</p></article>
      <article><span>03</span><h3>Booking or ordering</h3><p>Calendars, reminders, deposits, menus or checkout are scoped as a customer workflow. Starts at $600.</p></article>
    </div>
    <p class="sub web-scope-note">If an existing website only needs one repair, I will say so. If a standard platform is the better fit, I will recommend that instead of custom code.</p>
    <p class="label web-industry-label">web design by business type</p>
    <div class="relrow"><a class="rel" href="/industries/contractors">contractor web design →</a><a class="rel" href="/industries/automotive">auto repair web design →</a><a class="rel" href="/industries/restaurants">restaurant web design →</a><a class="rel" href="/industries/gyms">gym web design →</a><a class="rel" href="/industries/professional-services">professional-firm websites →</a></div>
  </div>
</section>
'''
    return head(s["title"], s["desc"], path, schema, EN_ALTS.get(s["slug"], "")) + ICONS + nav() + f'''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    {crumbs(bc)}
    <p class="label">leon --services {s["slug"]}</p>
    <h1 class="dsp" >{e(s["h1"][0])} <em>{e(s["h1"][1])}</em></h1>
    {intro}
    <p class="pricetag">starting at <b>{s["price"]}</b> · written fixed quote before any work starts · based in california, working with businesses across the u.s.</p>
    {cta_block(starter)}
  </div>
</section>
{reviews}{web_guide}<section class="sec">
  <div class="rail two-col">
    <div>
      <h2 class="page-section-title">Does this sound familiar?</h2>
      <ul class="plist">{pains}</ul>
    </div>
    <div>
      <h2 class="page-section-title">What I build for this</h2>
      <ul class="blist">{build}</ul>
    </div>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <p class="label">proof, not promises</p>
    <h2 class="page-section-title">Evidence related to this service</h2>
    <div class="proofcard">
      <h3>{e(s["proof"][0])}</h3>
      <p class="sub">{e(s["proof"][1])}</p>
      <a class="cx-mini" href="{work_link(s["proof"][0])}">open the related proof →</a>
    </div>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <p class="label">questions people ask first</p>
    <h2 class="page-section-title">Questions before starting</h2>
    {faq_html(s["faqs"])}
    <p class="label" style="margin-top:3rem">related</p>
    <div class="relrow">{related}</div>
    {cta_block(starter)}
  </div>
</section>
</main>''' + footer() + '</body></html>'


INDUSTRY_WEB_DESIGN = {
    "restaurants": {
        "heading": "What a restaurant website needs to turn searches into orders",
        "intro": "A restaurant visitor is usually deciding on a phone, quickly. The site should remove friction between the search result and the order or reservation.",
        "bullets": [
            "a readable menu with current prices, hours and location details",
            "one obvious action for ordering, reserving or calling",
            "fast pages that do not make the customer pinch and zoom",
            "separate menus and hours when locations differ",
        ],
    },
    "contractors": {
        "heading": "What a contractor website needs to turn visits into estimate requests",
        "intro": "The buyer wants to know what work you do, whether you serve their area and whether you look trustworthy before they give you a phone number.",
        "bullets": [
            "service and service-area pages written in the customer's language",
            "real project proof, licenses or credentials where applicable",
            "a short estimate request that works from the job site or driveway",
            "an immediate response and a human follow-up path",
        ],
    },
    "automotive": {
        "heading": "What an auto repair website needs to turn visits into appointments",
        "intro": "A shop website should make services, trust, hours and the next available action clear before the customer calls the next result.",
        "bullets": [
            "services and vehicle types explained without shop-software jargon",
            "one-tap calling and a booking or service-request path",
            "review and project proof near the decision point",
            "clear expectations for estimates, drop-off and status updates",
        ],
        "review_id": "testimonial-04",
    },
}


def industry_page(i):
    path = f'/industries/{i["slug"]}'
    bc = [("home","/"),("industries","/industries/"),(i["name"], None)]
    schema = [
        {"@context":"https://schema.org","@type":"Service","@id":BASE+path+"#service",
         "name":f'software for {i["name"]}', "url":BASE+path,
         "mainEntityOfPage":BASE+path,
         "provider":{"@id":BASE+"/#leon"},
         "areaServed":{"@type":"Country","name":"United States"},
         "description":i["desc"]},
        faq_schema(i["faqs"]), breadcrumb_schema(bc, path)]
    pains = ''.join(f'<li>{e(p)}</li>' for p in i["pains"])
    # THE 40 DEAD ENDS (fixed 2026-08-21). These cards are the highest-intent
    # element on an industry page — a restaurant owner reads "online ordering you
    # own — from $600" and decides right there — and every one of them was an
    # <article> with nowhere to click. Three of the four cards on a page now carry
    # the reader to the priced service page; the rest stay inert on purpose,
    # because a card promising less than the page it opens is worse than a card
    # that opens nothing. check_prices.py enforces that direction.
    fixes = ''.join(
        (f'<a class="fixcard link" href="/services/{sl}" data-evt="fixcard_{sl}">'
         f'<h3>{e(t)}</h3><p>{e(d)}</p><span class="go">see how →</span></a>'
         if sl else
         f'<article class="fixcard"><h3>{e(t)}</h3><p>{e(d)}</p></article>')
        for t, d, sl in i["fixes"])
    intro = ''.join(f'<p class="sub">{e(p)}</p>' for p in i["intro"])
    related = ''.join(f'<a class="rel" href="/services/{r}">{e(next(x["name"] for x in SERVICES if x["slug"]==r))} →</a>' for r in i["related_services"])
    starter = f'i run a business in {i["name"]} — here\'s what i\'m dealing with: '
    web_focus = ''
    if i["slug"] in INDUSTRY_WEB_DESIGN:
        focus = INDUSTRY_WEB_DESIGN[i["slug"]]
        bullets = ''.join(f'<li><svg class="ic"><use href="#ic-check"/></svg>{e(item)}</li>' for item in focus["bullets"])
        review = testimonial_card(focus.get("review_id", ""), "service-review industry-review")
        web_focus = f'''<section class="sec industry-web-focus">
  <div class="rail industry-web-grid">
    <div><p class="label">web design for {e(i["name"])}</p><h2 class="page-section-title">{e(focus["heading"])}</h2>
      <p class="sub">{e(focus["intro"])}</p><ul class="blist">{bullets}</ul>
      <a class="cx-mini" href="/services/websites">see small-business website scope and pricing →</a></div>
{review}
  </div>
</section>
'''
    sprint_copy = {
        "contractors": ("estimate requests that arrive while the owner is on a job",
                        "see the contractor website + follow-up scope"),
    }.get(i["slug"])
    sprint_bridge = ''
    if sprint_copy:
        sprint_bridge = f'''<section class="sec">
  <div class="rail">
    <p class="label">one focused starting point</p>
    <div class="proofcard">
      <h2>contractor lead recovery system</h2>
      <p class="sub">a fixed-scope, 10-business-day product for {e(sprint_copy[0])}: a focused contractor website, estimate intake, prompt acknowledgment, short follow-up sequence and documented human handoff.</p>
      <a class="cx-mini" href="/missed-lead-recovery" data-evt="lead_sprint_detail_click">{e(sprint_copy[1])} →</a>
    </div>
  </div>
</section>
'''
    return head(i["title"], i["desc"], path, schema) + ICONS + nav() + f'''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    {crumbs(bc)}
    <p class="label">leon --industries {i["slug"]}</p>
    <h1 class="dsp">{e(i["h1"][0])} <em>{e(i["h1"][1])}</em></h1>
    {intro}
    {cta_block(starter)}
  </div>
</section>
{web_focus}{sprint_bridge}<section class="sec">
  <div class="rail">
    <p class="label">the usual pain</p>
    <h2 class="page-section-title">Problems I hear from {e(i["name"])} owners</h2>
    <ul class="plist wide">{pains}</ul>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <p class="label">what actually fixes it</p>
    <h2 class="page-section-title">Practical starting points</h2>
    <div class="fixrow">{fixes}</div>
    <p class="sub" style="margin-top:1.4rem">every price is a published starting point, not a quote — the real number is agreed in writing before anything starts.</p>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <p class="label">proof, not promises</p>
    <h2 class="page-section-title">Evidence related to this work</h2>
    <div class="proofcard">
      <h2>{e(i["proof"][0])}</h2>
      <p class="sub">{e(i["proof"][1])}</p>
      <a class="cx-mini" href="{work_link(i["proof"][0])}">open the related proof →</a>
    </div>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <p class="label">questions people ask first</p>
    <h2 class="page-section-title">Questions from {e(i["name"])} owners</h2>
    {faq_html(i["faqs"])}
    <p class="label" style="margin-top:3rem">related services</p>
    <div class="relrow">{related}</div>
    {cta_block(starter)}
  </div>
</section>
</main>''' + footer() + '</body></html>'


def missed_lead_recovery_page():
    """Product page for the narrow contractor acquisition offer.

    The product combines the customer-facing lead path and its first follow-up
    handoff. It deliberately sells an implementation, not leads or revenue.
    """
    path = '/missed-lead-recovery'
    title = 'Contractor Lead Recovery System | Website + Follow-Up | Leon Builds'
    desc = ('A fixed-scope contractor website and missed-lead follow-up system: estimate intake, '
            'prompt acknowledgment, owner handoff and tracking. Starting at $1,500.')
    faqs = [
        ("is this a full contractor website?",
         "the starting scope is a focused, phone-first contractor site built around one estimate-request path. extra service, location, financing, careers or content sections are scoped separately so the 10-business-day product stays bounded."),
        ("can you improve my current website instead?",
         "yes. if the current site is sound, the product can repair its estimate path and connect the follow-up workflow instead of replacing pages that already work."),
        ("is this lead generation or ad management?",
         "no. it improves how an existing visitor becomes an estimate request and how that request reaches your team. buying leads, running ads and ongoing campaign management are separate work."),
        ("does this guarantee more bookings or revenue?",
         "no. it makes the estimate and follow-up path measurable and consistent, but results still depend on traffic, lead quality, demand, pricing, availability and how your team handles the conversation."),
        ("when does the 10-business-day window start?",
         "after the written scope is approved and the compatible accounts, access and customer-facing copy are ready. delays in access, vendor approval or client feedback move the schedule."),
        ("what if my phone, inbox or crm does not connect?",
         "i check compatibility before the fixed quote. if the tools cannot connect reliably, i will propose a smaller alternative, price a separate integration or say the sprint is not a fit."),
        ("what is handed over?",
         "the agreed project accounts, included configuration or source, setup notes, a handoff session and 30 days of fixes to the written scope. phone, crm, messaging, hosting and other vendors keep their own terms and fees."),
        ("what about consent for texts and emails?",
         "you approve the copy and remain responsible for lawful permission to contact each lead. i implement the agreed stop, opt-out and human-handoff rules in the compatible tools used for the sprint."),
    ]
    bc = [("home", "/"), ("contractor lead recovery system", None)]
    schema = [
        {
            "@context": "https://schema.org",
            "@type": "Service",
            "@id": f"{BASE}{path}#service",
            "name": "Contractor Lead Recovery System",
            "url": f"{BASE}{path}",
            "provider": {"@id": f"{BASE}/#leon"},
            "areaServed": {"@type": "Country", "name": "United States"},
            "audience": {"@type": "BusinessAudience", "audienceType": "Owner-run contractors and home-service businesses"},
            "description": desc,
            "offers": {
                "@type": "Offer",
                "price": "1500",
                "priceCurrency": "USD",
                "description": "Starting scope; a written compatibility check and fixed quote come before work begins.",
            },
        },
        faq_schema(faqs),
        breadcrumb_schema(bc, path),
    ]
    call_cta = '''<a class="btn btn-solid magnet" href="/call?service=contractor-lead-recovery" data-evt="cta_call_click"><span class="business-copy">Book a free 15-minute website review</span><svg class="ic"><use href="#ic-arrow"/></svg></a>'''
    check = '<svg class="ic"><use href="#ic-check"/></svg>'
    review_cards = testimonial_cards(
        ["testimonial-04", "testimonial-05"], "service-review"
    )
    reviews_section = ''
    if review_cards:
        reviews_section = f'''<section class="sec service-reviews" id="client-feedback">
  <div class="rail">
    <p class="label">direct client feedback</p>
    <h2 class="page-section-title">Related website and follow-up work</h2>
    <div class="service-review-grid">{review_cards}</div>
    <a class="cx-mini" href="/#testimonials">read approved client feedback →</a>
  </div>
</section>'''
    page_head = head(title, desc, path, schema).replace(
        '<body>', '<body class="contractor-landing">', 1
    )
    landing_nav = nav().replace(
        'href="/call"', 'href="/call?service=contractor-lead-recovery"'
    )
    return page_head + ICONS + landing_nav + f'''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    {crumbs(bc)}
    <p class="label">contractor website + estimate follow-up · fixed 10-business-day build</p>
    <h1 class="dsp business-copy">Give every website estimate request <em>a clear path from form to follow-up.</em></h1>
    <p class="sub business-copy">Leon builds the phone-first site, estimate form, immediate acknowledgment, follow-up rules, and owner handoff in one fixed scope—so every request has a clear next step.</p>
    <p class="pricetag business-copy">From <b>$1,500</b> fixed scope · 10 business days once scope, access, and approved copy are ready · work directly with Leon.</p>
    <div class="ctarow">{call_cta}<a class="btn magnet" href="#scope" data-evt="lead_scope_click"><span class="business-copy">See the exact $1,500 scope</span></a></div>
    <p class="hero-local business-copy">California-based · serving Bay Area contractors remotely · available for U.S. projects</p>
  </div>
</section>

<section class="proof-strip" aria-labelledby="contractor-proof-title">
  <div class="rail proof-in">
    <p class="label" id="contractor-proof-title">technical evidence you can inspect before booking</p>
    <div class="proof-grid">
      <a class="proof-item" href="https://apps.apple.com/app/apple-store/id6781121127?pt=129044256&amp;ct=leonbuilds-contractor&amp;mt=8" target="_blank" rel="noopener" data-evt="contractor_proof_appstore_click"><span>live product</span><strong>Leon shipped an App Store product</strong><i>open the public listing →</i></a>
      <a class="proof-item" href="/#work-loqol" data-evt="contractor_proof_demo_click"><span>public demo + source</span><strong>Inspect a working business workflow</strong><i>see the evidence →</i></a>
      <a class="proof-item" href="/about" data-evt="contractor_proof_identity_click"><span>direct relationship</span><strong>Meet the developer doing the work</strong><i>about Leon →</i></a>
    </div>
  </div>
</section>

{reviews_section}

<section class="sec" id="workflow">
  <div class="rail">
    <p class="label">what hiring leon changes</p>
    <h2 class="page-section-title business-copy">Every estimate request gets a clear next step.</h2>
    <div class="fixrow">
      <article class="fixcard"><h3>01 · visitor asks for an estimate</h3><p>the customer sends the service, location, project details and optional photos from a phone.</p></article>
      <article class="fixcard"><h3>02 · they know it arrived</h3><p>approved email or sms copy confirms the request reached the business and explains what happens next.</p></article>
      <article class="fixcard"><h3>03 · your team sees who owns it</h3><p>the request lands in one agreed inbox, sheet or crm with a visible owner and reply state.</p></article>
      <article class="fixcard"><h3>04 · follow-up does not rely on memory</h3><p>up to two approved follow-ups stop when the customer replies or opts out.</p></article>
    </div>
    <p class="sub business-copy">The step between website visit and sales conversation becomes visible and consistent. Your traffic, availability, pricing, and closing process still determine the result.</p>
    <a class="cx-mini business-copy" href="/#work">Inspect Leon's shipped product and public demos →</a>
  </div>
</section>

<section class="sec" id="scope">
  <div class="rail">
    <p class="label">everything in the $1,500 starting scope</p>
    <h2 class="page-section-title business-copy">A complete estimate path, not just a nicer homepage.</h2>
    <div class="two-col">
      <div>
        <ul class="blist">
          <li>{check}one focused, phone-first contractor website or lead page with services, service area, trust proof and one primary estimate action</li>
          <li>{check}structured estimate intake for the agreed basics, such as service, location, project details, preferred contact and optional photos</li>
          <li>{check}one immediate email or sms acknowledgment using copy you approve</li>
          <li>{check}one destination: your current crm, a shared sheet or a monitored inbox</li>
        </ul>
      </div>
      <div>
        <ul class="blist">
          <li>{check}up to two follow-ups, with reply, stop and opt-out rules</li>
          <li>{check}one owner or staff handoff rule, plus one booking or contact link</li>
          <li>{check}a basic event log so you can see received, sent, replied and handed off</li>
          <li>{check}one handoff session, included configuration or source, and setup notes</li>
          <li>{check}30 days of fixes for defects against the agreed written scope</li>
        </ul>
      </div>
    </div>
    <div class="scope-boundary business-copy">
      <div class="faq"><details><summary>What is outside this $1,500 starting scope?<i></i></summary><p>Buying leads, paid-ad management, a large multi-location website, a new CRM, live call answering, historical-data cleanup, and ongoing campaign management are separate work. Phone, messaging, CRM, domain, and hosting providers keep their own fees.</p></details></div>
    </div>
    <details class="disclosure contractor-process">
      <summary><span>See the 10-business-day build plan</span><small>map · build · test · hand off</small></summary>
      <ol class="steps">
        <li><span class="sn">01</span><h3>map one estimate path</h3><p>confirm the visitor, primary service, intake fields, destination, response copy, handoff owner and stop conditions. compatibility is checked before the quote.</p></li>
        <li><span class="sn">02</span><h3>build site + follow-up</h3><p>build the focused web path, acknowledgment and follow-ups around the agreed tools and customer-facing copy.</p></li>
        <li><span class="sn">03</span><h3>test the full handoff</h3><p>test phones, normal submissions, replies, opt-outs, duplicates and vendor failures before the fixed scope goes live.</p></li>
        <li><span class="sn">04</span><h3>hand it over</h3><p>review the event log, document the setup and hand over the included source or configuration covered by the quote.</p></li>
      </ol>
      <p class="sub business-copy">The window starts only after scope, access, compatible tools and approved copy are ready. Vendor approval or delayed feedback moves the schedule.</p>
    </details>
  </div>
</section>

<section class="sec" id="fit">
  <div class="rail">
    <p class="label">who this product fits</p>
    <div class="fixrow">
      <article class="fixcard"><h3>good fit</h3><p>owner-run roofing, plumbing, electrical, hvac, landscaping, remodeling and similar home-service businesses with a real service area and an estimate workflow.</p></article>
      <article class="fixcard"><h3>the observable problem</h3><p>the current site is call-only, uses a generic form, hides the next step on a phone or gives the owner no reliable view of what still needs a response.</p></article>
      <article class="fixcard"><h3>needs a different scope</h3><p>buying leads, replacing a full field-service platform or building a large multi-location marketing site should not be squeezed into this ten-day product.</p></article>
    </div>
    <a class="cx-mini" href="/industries/contractors">read the contractor website decision guide →</a>
  </div>
</section>

<section class="sec" id="faq">
  <div class="rail">
    <p class="label">fit and boundaries</p>
    {faq_html(faqs)}
    <div class="ctarow">{call_cta}</div>
    <p class="sub business-copy">Bring your current website. In 15 minutes, Leon will show you the smallest sensible improvement and say plainly if this product is not the right fit.</p>
  </div>
</section>
</main>''' + footer() + '</body></html>'

def listing_page(kind, items, title, desc, blurb):
    path = f'/{kind}/'
    bc = [("home","/"),(kind, None)]
    schema = [breadcrumb_schema(bc, path)]
    def card_summary(value, limit=132):
        if len(value) <= limit:
            return value
        return value[:limit].rsplit(' ', 1)[0].rstrip(' ,;:—-') + '…'

    cards = ''.join(
        f'<a class="fixcard link" href="/{kind}/{x["slug"]}"><h3>{e(x["name"])}</h3><p>{e(card_summary(x["desc"]))}</p><span class="go">'
        f'{e("from " + x["price"] + " · details →") if kind == "services" else "open →"}</span></a>'
        for x in items)
    return head(title, desc, path, schema) + ICONS + nav() + f'''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    {crumbs(bc)}
    <p class="label">leon --{kind}</p>
    <h1 class="dsp">{e(kind)} <em>{'i build' if kind=='services' else 'i build for'}</em></h1>
    <p class="sub">{e(blurb)}</p>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <div class="fixrow">{cards}</div>
    {cta_block("i'm not sure which of these i need — here's my situation: ")}
  </div>
</section>
</main>''' + footer() + '</body></html>'

def about_page():
    """The page that answers "who is Leon Kelvin Li". Nothing on the internet
       did before this existed, which is why the name query had nothing to
       resolve to. Every fact here is checkable and every claim is one he
       would be happy to be asked about on a call."""
    path = '/about'
    bc = [("home","/"),("about", None)]
    person = {
        "@type": "Person",
        "@id": f"{BASE}/#leon",
        "name": "Leon Kelvin Li",
        "alternateName": ["Leon Li", "Noctilucenty"],
        "url": f"{BASE}/about",
        "mainEntityOfPage": {"@id": f"{BASE}/about#webpage"},
        "jobTitle": "Software Developer",
        "description": ("Independent software developer and computer engineering student at California "
                        "State University, East Bay. Builds websites, mobile apps, online ordering, booking "
                        "systems, AI assistants and business automation for companies across the United States."),
        "knowsLanguage": ["en", "zh", "pt-BR", "es"],
        "knowsAbout": ["web development", "iOS development", "Android development",
                       "online ordering systems", "booking systems", "AI chatbots",
                       "business automation", "custom software"],
        "email": "leondragon3798@gmail.com",
        "telephone": "+1-510-826-7735",
        "address": {"@type": "PostalAddress", "addressRegion": "CA", "addressCountry": "US"},
        "affiliation": {"@type": "CollegeOrUniversity", "name": "California State University, East Bay"},
        "alumniOf": {"@type": "CollegeOrUniversity", "name": "Green River College"},
        "worksFor": {"@id": f"{BASE}/#business"},
        "sameAs": IDENTITY_URLS,
    }
    profile = {
        "@type": "ProfilePage",
        "@id": f"{BASE}/about#webpage",
        "url": f"{BASE}/about",
        "name": "About Leon Kelvin Li — Software Developer",
        "description": "Leon Kelvin Li's work, background, education and verified public profiles.",
        "isPartOf": {"@id": f"{BASE}/#website"},
        "mainEntity": {"@id": f"{BASE}/#leon"},
    }
    schema = [{"@context": "https://schema.org", "@graph": [profile, person]}, breadcrumb_schema(bc, path)]
    rel_me = "\n".join(f'<link rel="me" href="{e(url)}">' for url in IDENTITY_URLS)
    return head("About Leon Kelvin Li — Software Developer | Leon Kelvin Li",
        "Meet Leon Kelvin Li, a California-based independent developer who builds websites, apps and automation directly for U.S. businesses in four languages.",
        path, schema, head_extra=rel_me) + ICONS + nav() + '''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    ''' + crumbs(bc) + '''
    <p class="label">leon --about</p>
    <h1 class="dsp"><span class="keepcase">Leon Kelvin Li</span> — <em>the person who writes the code</em></h1>
    <p class="sub"><span class="keepcase">Leon Kelvin Li</span> is an independent software developer working with businesses across the united states. he builds business websites, iphone and android apps, online ordering, booking systems, ai assistants and the automation that runs behind them — and he does the work himself, so the person you talk to is the person writing the code.</p>
    <p class="sub">he works in english, chinese, portuguese and spanish. that matters more than it sounds: a lot of owners can describe their problem precisely in their own language and only roughly in english, and the rough version is where projects go wrong.</p>
  </div>
</section>

<section class="sec">
  <div class="rail two-col">
    <div>
      <p class="label">what he has actually built</p>
      <ul class="blist">
        <li><svg class="ic"><use href="#ic-check"/></svg>an iphone app that is on the app store today — built solo end to end, including subscriptions and app store review</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>an online ordering system where one kitchen runs several brands and a single cart splits itself per brand, with each brand's accounting kept separate</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>a tool that reads the reviews a business receives and drafts the replies from that business's own verified facts — a human still presses send</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>a market scoring system covering all 33,772 us zip codes across nine data sources, every score carrying an uncertainty band instead of false precision</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>a compliance-aware assistant in chinese where deterministic safety rules run before any model does, and it declines to answer rather than break advertising law</li>
      </ul>
    </div>
    <div>
      <p class="label">how he works</p>
      <ul class="blist">
        <li><svg class="ic"><use href="#ic-check"/></svg>one person, on purpose — no account manager, no handoff to a junior</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>a written fixed price before work starts; additions are priced and approved first</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>working reviews and delivery cadence stated in the written scope</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>the agreed project accounts, included source code, project data and setup notes are handed over; domains, hosting, app stores, libraries and other third-party services remain under their own terms</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>he will tell you when you don't need him — a script or an off-the-shelf tool is often the right answer, and saying so is cheaper than being wrong</li>
      </ul>
    </div>
  </div>
</section>

<section class="sec">
  <div class="rail">
    <p class="label">background</p>
    <p class="sub">he is a computer engineering student at <span class="keepcase">California State University, East Bay</span>, an alumnus of <span class="keepcase">Green River College</span>, and a working developer with a live App Store product plus public demos. all three are true at once, and he would rather say so than hide any of them.</p>
    <p class="sub">he writes under the name <span class="keepcase">Noctilucenty</span>, which is where his code lives on github.</p>
    <p class="sub">his current product is <a class="cx-mini" href="https://trycurio.app/" target="_blank" rel="noopener"><span class="keepcase">Curio</span></a>; its <a class="cx-mini" href="https://trycurio.app/team.html#leon" target="_blank" rel="me noopener">founder profile</a> connects that work to this site. older work remains in the <a class="cx-mini" href="https://noctilucenty.github.io/" target="_blank" rel="me noopener">portfolio archive</a>.</p>
    <p class="sub" aria-label="Leon Kelvin Li public profiles">public profiles: <a class="cx-mini" href="https://www.worldcubeassociation.org/persons/2016LILE01" target="_blank" rel="me noopener">wca</a> · <a class="cx-mini" href="https://www.f6s.com/leonkelvinli" target="_blank" rel="me noopener">f6s</a> · <a class="cx-mini" href="https://www.linkedin.com/in/leon-kelvin-li" target="_blank" rel="me noopener">linkedin</a> · <a class="cx-mini" href="https://github.com/Noctilucenty" target="_blank" rel="me noopener">github</a> · <a class="cx-mini" href="https://apps.apple.com/us/developer/leon-kelvin-li/id6781121129" target="_blank" rel="me noopener">apple developer</a> · <a class="cx-mini" href="https://www.instagram.com/lkelvn_/" target="_blank" rel="me noopener">instagram</a>.</p>
    <div class="ctarow">
      <a class="btn btn-solid magnet" href="/quote" data-evt="about_quote_click"><span>tell him what you need</span><svg class="ic"><use href="#ic-arrow"/></svg></a>
      <a class="btn magnet" href="https://wa.me/15108267735?text=Hi%20Leon%20-%20saw%20your%20site.%20My%20business%20is%3A%20" target="_blank" rel="noopener" data-evt="wa_click_about"><span>whatsapp</span></a>
      <a class="cx-mini" href="mailto:leondragon3798@gmail.com" data-evt="email_click">or email leon directly →</a>
    </div>
  </div>
</section>
</main>
''' + footer()

CAL_SLUG = "noctilucente-wzvdey/15min"

ZH_CALL_DESCRIPTION = "免费 15 分钟，中文沟通。你说说生意里哪一块还在靠人工、哪里最费时间，我会告诉你适合怎么做、大概从多少钱起，也会直说暂时不需要做系统。"

CAL_COPY = {
    "en": {
        "loading": "loading live availability…",
        "failed": "the inline calendar did not load. use the direct booking link below.",
        "booked_label": "you are booked",
        "booked": "cal.com will send the video link and calendar invitation to the email used for the booking.",
        "fallback": "calendar not showing?",
        "direct": "open the booking page directly",
        "email": "email leon",
        "call": "call (510) 826-7735",
        "unavailable": "online booking is temporarily unavailable. email leon or call (510) 826-7735.",
    },
    "pt": {
        "loading": "carregando os horários disponíveis…",
        "failed": "o calendário não carregou aqui. use o link direto abaixo.",
        "booked_label": "horário marcado",
        "booked": "o cal.com vai mandar o link da chamada e o convite para o e-mail usado no agendamento.",
        "fallback": "o calendário não apareceu?",
        "direct": "abrir a página de agendamento",
        "email": "mandar e-mail",
        "call": "ligar para (510) 826-7735",
        "unavailable": "o agendamento online está indisponível por enquanto. mande um e-mail ou ligue para (510) 826-7735.",
    },
    "es": {
        "loading": "cargando los horarios disponibles…",
        "failed": "el calendario no cargó aquí. usa el enlace directo de abajo.",
        "booked_label": "llamada agendada",
        "booked": "cal.com enviará el enlace de video y la invitación al correo usado para agendar.",
        "fallback": "¿no aparece el calendario?",
        "direct": "abrir la página de reservas",
        "email": "enviar un correo",
        "call": "llamar al (510) 826-7735",
        "unavailable": "las reservas en línea no están disponibles por ahora. envía un correo o llama al (510) 826-7735.",
    },
    "zh": {
        "loading": "正在加载可预约时间…",
        "failed": "日历没有成功加载，请使用下面的直接预约链接。",
        "booked_label": "预约成功",
        "booked": "cal.com 会把视频链接和日历邀请发到预约时填写的邮箱。",
        "fallback": "没有看到日历？",
        "direct": "直接打开预约页面",
        "email": "发邮件给 Leon",
        "call": "拨打 (510) 826-7735",
        "unavailable": "在线预约暂时不可用，请发邮件或拨打 (510) 826-7735。",
    },
}

# Cal.com's OFFICIAL inline embed, not a raw iframe. A raw iframe of the
# public booking URL inherits the visitor's cal.com session, so a logged-in
# user — i.e. Leon himself — sees his own bookings dashboard instead of the
# booker. The embed script renders in an isolated context and cannot.
def booker(lang="en"):
    """One instrumented Cal.com embed, shared by every booking page.

    Only the five standard UTM fields already captured by the site are forwarded.
    Arbitrary page query parameters are deliberately not forwarded: names,
    emails, or other accidental URL data must never cross into the calendar.
    """
    copy = CAL_COPY.get(lang, CAL_COPY["en"])
    if not CAL_SLUG:
        return (
            '<div class="calwrap" style="min-height:14rem;padding:2rem">'
            f'<p class="sub">{copy["unavailable"]}</p>'
            '<p class="qnote"><a href="mailto:leondragon3798@gmail.com" data-evt="calendar_email_fallback">'
            f'{copy["email"]}</a> · <a href="tel:+15108267735" data-evt="calendar_phone_fallback">'
            f'{copy["call"]}</a></p></div>'
        )

    calendar_url = f"https://cal.com/{CAL_SLUG}?redirect=false"
    template = r'''<div class="calwrap" id="leon-booker" aria-busy="true" style="min-height:680px;position:relative">
  <div id="leon-cal-status" role="status" style="position:absolute;inset:0;z-index:2;min-height:680px;padding:2rem;background:#050505;pointer-events:none">
    <p class="label" id="leon-cal-status-text">__LOADING__</p>
    <div aria-hidden="true" style="margin-top:2rem;display:grid;gap:1rem">
      <i style="display:block;height:3.25rem;border:1px solid #262626;border-radius:9px;background:linear-gradient(90deg,#090909,#151515,#090909)"></i>
      <i style="display:block;height:18rem;border:1px solid #202020;border-radius:9px;background:linear-gradient(135deg,#080808,#111,#080808)"></i>
      <i style="display:block;height:3.25rem;border:1px solid #262626;border-radius:9px;background:linear-gradient(90deg,#090909,#151515,#090909)"></i>
    </div>
  </div>
  <div id="leon-cal" style="min-height:680px"></div>
</div>
<div class="qok" id="bookingok" hidden tabindex="-1" aria-live="polite">
  <p class="label">__BOOKED_LABEL__</p>
  <p class="sub">__BOOKED__</p>
</div>
<p class="qnote">__FALLBACK__ <a id="leon-cal-direct" href="__CAL_URL__" target="_blank" rel="noopener" data-evt="calendar_direct_fallback">__DIRECT__</a> · <a href="mailto:leondragon3798@gmail.com" data-evt="calendar_email_fallback">__EMAIL__</a> · <a href="tel:+15108267735" data-evt="calendar_phone_fallback">__CALL__</a></p>
<script>
(function(){
  var scriptNode=document.currentScript;
  var wrap=document.getElementById('leon-booker');
  var status=document.getElementById('leon-cal-status');
  var statusText=document.getElementById('leon-cal-status-text');
  var confirmation=document.getElementById('bookingok');
  var readyTracked=false,failedTracked=false,bookedTracked=false;
  var timeout;

  // Put the calendar first visually immediately, then first in the DOM once the
  // parser is done. This keeps translated pages generated by their shared
  // layout accessible without duplicating that layout here.
  var column=scriptNode&&scriptNode.closest('.callgrid > div');
  if(column){
    column.style.order='-1';
    var moveFirst=function(){
      var grid=column.parentElement;
      if(grid&&grid.classList.contains('callgrid')&&grid.firstElementChild!==column){
        grid.insertBefore(column,grid.firstElementChild);
      }
    };
    if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',moveFirst,{once:true});
    else moveFirst();
  }

  function track(name,extra){
    if(window.leonEvt){ window.leonEvt(name,extra); return; }
    document.addEventListener('DOMContentLoaded',function(){ if(window.leonEvt) window.leonEvt(name,extra); },{once:true});
  }
  function safeParam(value,max){
    return String(value||'').trim().replace(/[^A-Za-z0-9._~-]/g,'-').slice(0,max);
  }
  function sourceConfig(){
    var attr={};
    try{ attr=JSON.parse(localStorage.getItem('leon_attr')||'{}')||{}; }catch(e){}
    var query=new URLSearchParams(location.search);
    var out={layout:'month_view',theme:'dark'};
    var source=safeParam(query.get('utm_source')||query.get('s')||attr.utmSource,120);
    var medium=safeParam(query.get('utm_medium')||attr.utmMedium,120);
    var campaign=safeParam(query.get('utm_campaign')||attr.utmCampaign,120);
    var term=safeParam(query.get('utm_term')||attr.utmTerm,120);
    var content=safeParam(query.get('utm_content')||attr.utmContent,120);
    if(source) out.utm_source=source;
    if(medium) out.utm_medium=medium;
    if(campaign) out.utm_campaign=campaign;
    if(term) out.utm_term=term;
    if(content) out.utm_content=content;
    return out;
  }
  function ready(){
    clearTimeout(timeout);
    wrap.setAttribute('aria-busy','false');
    status.hidden=true;
    if(!readyTracked){ readyTracked=true; track('calendar_ready'); }
  }
  function failed(){
    clearTimeout(timeout);
    wrap.setAttribute('aria-busy','false');
    statusText.textContent='__FAILED__';
    if(!failedTracked){ failedTracked=true; track('calendar_failed'); }
  }
  function booked(payload){
    ready();
    confirmation.hidden=false;
    var data=payload&&payload.detail&&payload.detail.data;
    var rawUid=data&&(data.uid||(data.booking&&data.booking.uid));
    var bookingUid=safeParam(rawUid,128);
    if(!bookedTracked){ bookedTracked=true; track('calendar_booking_success',bookingUid?{bookingUid:bookingUid}:undefined); }
    try{ confirmation.focus({preventScroll:true}); }catch(e){ confirmation.focus(); }
    confirmation.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});
  }

  (function(C,A,L){var p=function(a,ar){a.q.push(ar)};var d=C.document;
    C.Cal=C.Cal||function(){var cal=C.Cal;var ar=arguments;if(!cal.loaded){cal.ns={};cal.q=cal.q||[];
    d.head.appendChild(d.createElement('script')).src=A;cal.loaded=true}
    if(ar[0]===L){var api=function(){p(api,arguments)};var ns=ar[1];api.q=api.q||[];
    if(typeof ns==='string'){cal.ns[ns]=cal.ns[ns]||api;p(cal.ns[ns],ar);p(cal,['initNamespace',ns])}
    else p(cal,ar);return}p(cal,ar)}})(window,'https://app.cal.com/embed/embed.js','init');

  var calConfig=sourceConfig();
  var direct=document.getElementById('leon-cal-direct');
  if(direct){
    try{
      var directUrl=new URL(direct.href);
      ['utm_source','utm_medium','utm_campaign','utm_term','utm_content'].forEach(function(key){
        if(calConfig[key]) directUrl.searchParams.set(key,calConfig[key]);
      });
      direct.href=directUrl.toString();
    }catch(e){}
  }
  Cal('init','leon15',{origin:'https://app.cal.com'});
  Cal.ns.leon15('on',{action:'bookerReady',callback:ready});
  Cal.ns.leon15('on',{action:'linkFailed',callback:failed});
  Cal.ns.leon15('on',{action:'bookingSuccessfulV2',callback:booked});
  Cal.ns.leon15('inline',{elementOrSelector:'#leon-cal',config:calConfig,calLink:'__CAL_SLUG__'});
  Cal.ns.leon15('ui',{theme:'dark',hideEventTypeDetails:false,layout:'month_view'});
  var embedScript=document.querySelector('script[src="https://app.cal.com/embed/embed.js"]');
  if(embedScript) embedScript.addEventListener('error',failed,{once:true});
  timeout=setTimeout(failed,15000);
})();
</script>'''
    replacements = {
        "__LOADING__": copy["loading"],
        "__FAILED__": copy["failed"],
        "__BOOKED_LABEL__": copy["booked_label"],
        "__BOOKED__": copy["booked"],
        "__FALLBACK__": copy["fallback"],
        "__DIRECT__": copy["direct"],
        "__EMAIL__": copy["email"],
        "__CALL__": copy["call"],
        "__CAL_URL__": calendar_url,
        "__CAL_SLUG__": CAL_SLUG,
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template



def call_page():
    """Book a 15-minute call with a visible, instrumented calendar and fallbacks."""
    path = '/call'
    bc = [("home","/"),("book a call", None)]
    schema = [breadcrumb_schema(bc, path), {
        "@context": "https://schema.org", "@type": "Service",
        "name": "Free 15-minute consultation",
        "provider": {"@id": f"{BASE}/#leon"},
        "areaServed": {"@type": "Country", "name": "United States"},
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": "A free 15-minute call to look at what you have now and say honestly whether it is worth changing.",
    }]
    booker_html = booker("en")
    call_alts = ''.join(
        f'<link rel="alternate" hreflang="{hl}" href="{BASE}{href}">'
        for hl, href in lang_pages.call_alternates())
    return head("Book a Free 15-Minute Call | Leon Kelvin Li",
        "Book a free 15-minute call with Leon Kelvin Li. He looks at what you have now and tells you honestly whether it is worth changing. No sales team, no obligation.",
        path, schema, call_alts) + ICONS + nav() + '''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    ''' + crumbs(bc) + '''
    <p class="label" id="call-context-label">leon --call</p>
    <h1 class="dsp" id="call-context-title">book a free <em>15-minute call</em></h1>
    <p class="sub" id="call-context-intro">fifteen minutes is enough to know whether there is a project here. you describe what is slow or manual in your week, and leon tells you what he would build, roughly what it starts at, and just as readily when you do not need him at all.</p>
    <p class="pricetag" id="call-context-price">free · 15 minutes · weekday availability, pacific time · you talk to the person who writes the code</p>
  </div>
</section>

<section class="sec">
  <div class="rail">
    <div class="callgrid">
    <div>
      ''' + booker_html + '''
    </div>
    <div>
      <p class="label" id="call-context-agenda">what happens on the call</p>
      <ul class="blist">
        <li><svg class="ic"><use href="#ic-check"/></svg>you describe the problem in plain words — no technical vocabulary needed</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>he asks about what you use today and where it actually breaks</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>you get a straight answer on what it would take and what it starts at</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>if a cheaper tool or a small script solves it, he says so — that ends the call early and saves you money</li>
      </ul>
      <p class="sub">english, spanish, portuguese or chinese — whichever you would rather think in.</p>
    </div>
    </div>
  </div>
</section>
</main>
<script>
(function(){
  var params=new URLSearchParams(location.search);
  if(params.get('service')!=='contractor-lead-recovery') return;
  document.body.classList.add('contractor-call-context');
  document.title='Book a Contractor Website Review | Leon Builds';
  var label=document.getElementById('call-context-label');
  var title=document.getElementById('call-context-title');
  var intro=document.getElementById('call-context-intro');
  var price=document.getElementById('call-context-price');
  var agenda=document.getElementById('call-context-agenda');
  if(label) label.textContent='Contractor website + follow-up review';
  if(title) title.innerHTML='Book a free <em>15-minute website review</em>';
  if(intro) intro.textContent='Show Leon your current contractor website and estimate path. You will leave knowing the smallest useful change, what the fixed scope includes, and whether the $1,500 product fits.';
  if(price) price.textContent='Free · 15 minutes · weekday availability, Pacific time · directly with Leon';
  if(agenda) agenda.textContent='What happens in the contractor review';
  if(window.leonEvt) window.leonEvt('call_context_contractor');
})();
</script>
''' + footer()

def quote_page():
    path = '/quote'
    bc = [("home","/"),("get a quote", None)]
    schema = [breadcrumb_schema(bc, path)]
    return head("Get a Fixed Quote — Software & AI | Leon Kelvin Li",
        "Describe what your business needs in plain words. Leon reads every request himself and replies with real questions or a fixed quote — usually same day.",
        path, schema) + ICONS + nav() + '''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    ''' + crumbs(bc) + '''
    <p class="label">leon --quote</p>
    <h1 class="dsp">tell me what <em>you need</em></h1>
    <p class="sub">plain words are perfect — "customers can't book online", "we retype everything", "i want an app". leon reads every one of these himself and replies with real questions or a number, usually the same day.</p>
    <p class="assist-fallback">Not sure how to describe it? <button class="linklike" type="button" data-assist-open data-assist-starter="help me describe my project">Use the site assistant to draft a short project note.</button></p>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <form class="qform" id="qform" method="post" action="/quote" novalidate aria-describedby="qnote">
      <label>what are you trying to fix or build? <i>(required)</i><textarea name="problem" rows="4" required placeholder="the part of the week that's still manual, the thing that's broken, or the thing you wish existed…"></textarea></label>
      <div class="qrow">
        <label>name<input name="name" type="text" autocomplete="name"></label>
        <label>email <i>(required)</i><input name="email" type="email" required autocomplete="email" inputmode="email"></label>
      </div>
      <details>
        <summary style="cursor:pointer;color:var(--dim);font-size:12px;letter-spacing:.05em">add project details <i>(optional)</i></summary>
        <div style="display:grid;gap:1.1rem;margin-top:1.1rem">
          <label>what does your business do?<input name="company" type="text" placeholder="two taquerias in dallas / a plumbing company / a dental office…"></label>
          <label>what do you currently use for it?<input name="currentTools" type="text" placeholder="paper + phone / spreadsheets / quickbooks / square / nothing…"></label>
          <label>what result would make this worth paying for?<input name="desiredOutcome" type="text" placeholder="phone stops ringing about status / orders without commission / one less hire…"></label>
          <div class="qrow">
            <label>when do you want to start?
              <select name="timeline"><option value="">choose…</option><option>as soon as possible</option><option>within a month</option><option>next few months</option><option>just exploring</option></select>
            </label>
            <label>rough budget <i>(optional)</i>
              <select name="budget"><option value="">need guidance</option><option>under $1,000 — focused site or fix</option><option>$1,000–$3,500</option><option>$3,500–$7,500</option><option>$7,500–$15,000</option><option>$15,000+</option></select>
            </label>
          </div>
          <label>phone <i>(optional)</i><input name="phone" type="tel" autocomplete="tel"></label>
        </div>
      </details>
      <input name="website" type="text" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true">
      <p class="qerr" id="qerr" role="alert" aria-live="polite"></p>
      <div id="qfail" hidden role="alert">
        <p class="sub">the site did not accept that request. your answers are still here. <a id="qmail" href="mailto:leondragon3798@gmail.com" data-evt="quote_manual_email">open a prepared email</a>, then hit send in your email app; or use whatsapp or phone below.</p>
      </div>
      <button class="btn btn-solid magnet qsend" type="submit"><span>send it to leon</span><svg class="ic"><use href="#ic-arrow"/></svg></button>
      <noscript><p class="qnote">this form needs javascript to submit safely. email <a href="mailto:leondragon3798@gmail.com">leondragon3798@gmail.com</a> or call <a href="tel:+15108267735">(510) 826-7735</a>.</p></noscript>
      <p class="qnote" id="qnote">the site sends this directly; it will not open your email app when it works. no sales team exists. prefer a manual route? <a href="https://wa.me/15108267735?text=Hi%20Leon%20-%20saw%20your%20site.%20My%20business%20is%3A%20" target="_blank" rel="noopener" data-evt="wa_click_quote">whatsapp</a> · <a href="mailto:leondragon3798@gmail.com" data-evt="quote_manual_email">leondragon3798@gmail.com</a> · <a href="tel:+15108267735" data-evt="phone_click">(510) 826-7735</a></p>
    </form>
    <div class="qok" id="qok" hidden tabindex="-1" aria-live="polite">
      <p class="label">received</p>
      <h2 class="dsp">the site accepted your <em>project note.</em></h2>
      <p class="sub">your reference is <code id="qreceipt"></code>. save it if you want leon to trace this exact submission.</p>
      <div class="ctarow">
        <a class="btn btn-solid magnet" href="/call" data-evt="quote_to_calendar"><span>book the free 15-minute call</span><svg class="ic"><use href="#ic-arrow"/></svg></a>
        <a class="btn magnet" href="mailto:leondragon3798@gmail.com" data-evt="quote_manual_email"><span>email leon directly</span></a>
      </div>
    </div>
  </div>
</section>
</main>
<script>
(function(){
  var f=document.getElementById('qform'),err=document.getElementById('qerr'),fail=document.getElementById('qfail'),ok=document.getElementById('qok');
  if(!f)return;
  var API=(window.LEON_ASSIST&&window.LEON_ASSIST.api)||(/^(localhost|127\\.0\\.0\\.1)$/.test(location.hostname)?'http://localhost:8787':'https://leon-assist.onrender.com');
  var button=f.querySelector('button[type="submit"]'),buttonText=button.querySelector('span');
  var manual=document.getElementById('qmail'),receipt=document.getElementById('qreceipt');
  var started=false,submitting=false;
  function track(name,extra){ if(window.leonEvt) window.leonEvt(name,extra); }
  f.addEventListener('input',function(ev){
    if(!started){ started=true; track('quote_form_start'); }
    if(ev.target&&ev.target.removeAttribute) ev.target.removeAttribute('aria-invalid');
  },{once:false});
  f.addEventListener('submit',async function(ev){
    ev.preventDefault();
    if(submitting)return;
    track('quote_submit_attempt');
    err.textContent=''; fail.hidden=true;
    var d=Object.fromEntries(new FormData(f).entries());
    Object.keys(d).forEach(function(k){ if(typeof d[k]==='string') d[k]=d[k].trim(); });
    var invalid=null;
    if(!d.problem){ err.textContent='tell me at least a sentence about what you need.'; invalid=f.elements.problem; }
    else if(!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$/.test(d.email||'')){ err.textContent='that email does not look right.'; invalid=f.elements.email; }
    if(invalid){
      invalid.setAttribute('aria-invalid','true');
      invalid.focus();
      track('quote_validation_failed');
      return;
    }
    var attr={}; try{attr=JSON.parse(localStorage.getItem('leon_attr')||'{}')}catch(e){}
    d.via='quote-form'; d.sourcePage=location.pathname; d.referrer=attr.referrer||'';
    d.utmSource=attr.utmSource||''; d.utmMedium=attr.utmMedium||''; d.utmCampaign=attr.utmCampaign||''; d.utmTerm=attr.utmTerm||''; d.utmContent=attr.utmContent||'';
    d.gclid=attr.gclid||''; d.gbraid=attr.gbraid||''; d.wbraid=attr.wbraid||''; d.fbclid=attr.fbclid||''; d.msclkid=attr.msclkid||'';
    d.firstPage=(attr.first&&attr.first.page)||attr.firstPage||'/';
    d.firstReferrer=(attr.first&&attr.first.referrer)||'';
    d.firstUtmSource=(attr.first&&attr.first.utmSource)||'';
    d.firstUtmMedium=(attr.first&&attr.first.utmMedium)||'';
    d.firstUtmCampaign=(attr.first&&attr.first.utmCampaign)||'';
    d.firstUtmTerm=(attr.first&&attr.first.utmTerm)||'';
    d.firstUtmContent=(attr.first&&attr.first.utmContent)||'';
    d.firstGclid=(attr.first&&attr.first.gclid)||'';
    d.firstGbraid=(attr.first&&attr.first.gbraid)||'';
    d.firstWbraid=(attr.first&&attr.first.wbraid)||'';
    d.firstFbclid=(attr.first&&attr.first.fbclid)||'';
    d.firstMsclkid=(attr.first&&attr.first.msclkid)||'';
    d.lastPage=(attr.last&&attr.last.page)||location.pathname;
    d.lastReferrer=(attr.last&&attr.last.referrer)||attr.referrer||'';
    d.lastUtmSource=(attr.last&&attr.last.utmSource)||attr.utmSource||'';
    d.lastUtmMedium=(attr.last&&attr.last.utmMedium)||attr.utmMedium||'';
    d.lastUtmCampaign=(attr.last&&attr.last.utmCampaign)||attr.utmCampaign||'';
    d.lastUtmTerm=(attr.last&&attr.last.utmTerm)||attr.utmTerm||'';
    d.lastUtmContent=(attr.last&&attr.last.utmContent)||attr.utmContent||'';
    d.lastGclid=(attr.last&&attr.last.gclid)||attr.gclid||'';
    d.lastGbraid=(attr.last&&attr.last.gbraid)||attr.gbraid||'';
    d.lastWbraid=(attr.last&&attr.last.wbraid)||attr.wbraid||'';
    d.lastFbclid=(attr.last&&attr.last.fbclid)||attr.fbclid||'';
    d.lastMsclkid=(attr.last&&attr.last.msclkid)||attr.msclkid||'';
    try{ d.analyticsSessionId=sessionStorage.getItem('leon_analytics_session')||''; }catch(e){ d.analyticsSessionId=''; }
    submitting=true; button.disabled=true; button.setAttribute('aria-busy','true'); buttonText.textContent='sending…';
    var controller=window.AbortController?new AbortController():null;
    var timer=controller?setTimeout(function(){controller.abort();},35000):null;
    try{
      var options={method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)};
      if(controller) options.signal=controller.signal;
      var response=await fetch(API+'/api/lead',options);
      var result={}; try{result=await response.json();}catch(e){}
      if(!response.ok||result.ok!==true) throw new Error('lead rejected');
      var receiptId=String(result.receiptId||'');
      if(!/^lead_[A-Za-z0-9-]{16,}$/.test(receiptId)) throw new Error('missing receipt');
      receipt.textContent=receiptId;
      f.hidden=true; ok.hidden=false;
      track('quote_lead_accepted',{receipt:receiptId});
      try{ ok.focus({preventScroll:true}); }catch(e){ ok.focus(); }
      ok.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});
    }catch(e){
      manual.href=mailtoFor(d);
      fail.hidden=false;
      err.textContent='that did not send through the site.';
      track('quote_lead_failed');
      try{ fail.scrollIntoView({behavior:'smooth',block:'center'}); }catch(ignore){}
    }finally{
      if(timer)clearTimeout(timer);
      submitting=false; button.disabled=false; button.removeAttribute('aria-busy'); buttonText.textContent='send it to leon';
    }
  });
  function line(label,val){ return val&&String(val).trim() ? label+': '+String(val).trim()+'\\n' : ''; }
  function mailtoFor(d){
    var body=''
      + line('name',d.name)
      + line('email',d.email)
      + line('phone',d.phone)
      + line('business',d.company)
      + line('currently using',d.currentTools)
      + line('timeline',d.timeline)
      + line('budget',d.budget)
      + '\\nwhat i need:\\n' + String(d.problem||'').trim() + '\\n'
      + (d.desiredOutcome ? '\\nwhat would make it worth paying for:\\n'+String(d.desiredOutcome).trim()+'\\n' : '')
      + '\\n— sent from leonbuilds.org'+(d.sourcePage&&d.sourcePage!=='/quote'?' ('+d.sourcePage+')':'');
    if(body.length>1600) body=body.slice(0,1600)+'\\n…';
    var subject='project inquiry'+(d.company?' — '+String(d.company).trim():(d.name?' — '+String(d.name).trim():''));
    return 'mailto:leondragon3798@gmail.com?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(body);
  }
})();
</script>''' + footer() + '</body></html>'

# ══════════════════════════════════════════════════════════════════
# EMIT
# ══════════════════════════════════════════════════════════════════

CHANGED = []

def w(rel, content):
    """Writes only on a real diff, and records it.

    It used to write unconditionally, which mattered once IndexNow existed:
    every rebuild would otherwise announce all forty URLs as fresh, including
    the thirty-nine that are byte-identical, and a submitter that cries wolf is
    a submitter that gets throttled."""
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
    old = None
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            old = f.read()
    if old == content:
        return
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)
    CHANGED.append(rel)
    print('wrote', rel)

# ── language service pages ────────────────────────────────────────
# The one thing an agency cannot copy: the developer speaks the language the
# owner explains the problem in. Copy is native, never translated, and lives
# in data/lang_pages.json.
import lang_pages

# Keep the localized call metadata in the same generator path as its page.
# The long-form translation table remains owned by tools/lang_pages.py.
lang_pages.CALL_COPY["zh"]["desc"] = ZH_CALL_DESCRIPTION

LANG_COPY = {}
_copy_path = os.path.join(ROOT, 'content', 'lang_pages.json')
if os.path.exists(_copy_path):
    with open(_copy_path, encoding='utf-8') as f:
        for row in json.load(f)['pages']:
            LANG_COPY[(row['lang'], row['service'])] = row['page']

def _siblings(lang, key):
    return [(k, LANG_COPY[(lang, k)]) for (l, k) in LANG_COPY
            if l == lang and k != key]

LANG_CTX = dict(e=e, BASE=BASE, FONTS=FONTS, ICONS=ICONS, siblings=_siblings)

# Reciprocal hreflang for the English pages that now have translations. Built
# from the same SLUGS table the language pages use, so the two sides cannot
# drift into a one-way cluster Google throws away.
EN_ALTS = {}
for _key, _en in lang_pages.EN_COUNTERPART.items():
    if not any(l for (l, k) in LANG_COPY if k == _key):
        continue
    _tags = [f'<link rel="alternate" hreflang="en" href="{BASE}{_en}">']
    for _code in ['pt', 'es', 'zh']:
        if (_code, _key) in LANG_COPY:
            _hl = lang_pages.LANGS[_code]['hreflang']
            _tags.append(f'<link rel="alternate" hreflang="{_hl}" '
                         f'href="{BASE}/{_code}/{lang_pages.SLUGS[(_code, _key)]}">')
    _tags.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}{_en}">')
    EN_ALTS[_en.rsplit("/", 1)[-1]] = ''.join(_tags)


for s in SERVICES: w(f'services/{s["slug"]}.html', service_page(s))
for i in INDUSTRIES: w(f'industries/{i["slug"]}.html', industry_page(i))

w('services/index.html', listing_page('services', SERVICES,
  "Services — Websites, Apps, AI & Automation | Leon Kelvin Li",
  "Every service Leon builds, with honest starting prices: websites, mobile apps, AI chatbots and phone agents, automation, portals, dashboards and more.",
  "every price is a published floor, not a quote. most jobs turn out to be two or three of these stitched together — describe the problem and i'll quote the shape of it."))

w('industries/index.html', listing_page('industries', INDUSTRIES,
  "Industries I Build Software For | Leon Kelvin Li",
  "Software, AI and automation shaped for restaurants, contractors, auto shops, clinics, real estate, logistics, gyms, retail, firms and startups.",
  "the problems repeat inside an industry — the fixes below come from systems already running, not a template's guess. don't see yours? that's what custom means."))

LANG_URLS = []
for (lang, key), page in sorted(LANG_COPY.items()):
    slug = lang_pages.SLUGS[(lang, key)]
    w(f'{lang}/{slug}.html', lang_pages.render(lang, key, page, LANG_CTX))
    LANG_URLS.append(f'/{lang}/{slug}')

# The booking page in each language. The English /call is where a translated
# funnel used to end: three paragraphs in Portuguese, then a wall of English at
# the moment of deciding. Same Cal.com embed, translated page around it.
for _lang in sorted(lang_pages.CALL_COPY):
    _c = lang_pages.CALL_COPY[_lang]
    w(f"{_lang}/{_c['slug']}.html", lang_pages.render_call(_lang, booker(_lang), LANG_CTX))
    LANG_URLS.append(f"/{_lang}/{_c['slug']}")

# Refill the link block on each language home so the service pages are not
# orphans. Sentinels live in the hand-written homes; everything between them
# is generated, everything around them is Leon's own copy.
for _lang in sorted({l for (l, _k) in LANG_COPY}):
    _p = os.path.join(ROOT, _lang, 'index.html')
    if not os.path.exists(_p):
        continue
    with open(_p, encoding='utf-8') as f:
        _s = f.read()
    _links = ''.join(
        f'<a href="/{_lang}/{lang_pages.SLUGS[(_lang, k)]}">'
        f'{e(LANG_COPY[(_lang, k)]["h1_plain"])} {e(LANG_COPY[(_lang, k)]["h1_em"])}</a>'
        for k in ['websites', 'ordering', 'automation'] if (_lang, k) in LANG_COPY)
    _a, _b = '<!-- LANGSERVICES:START -->', '<!-- LANGSERVICES:END -->'
    if _a in _s and _b in _s:
        _pre, _rest = _s.split(_a, 1)
        _mid, _post = _rest.split(_b, 1)
        _new = _pre + _a + _links + _b + _post
        if _new != _s:
            with open(_p, 'w', encoding='utf-8') as f:
                f.write(_new)
            print('relinked', _lang + '/index.html')

# The hand-written homepage keeps one generated testimonial slot. The slot is
# empty by default and can contain only records released by testimonial_gate.py.
_home_path = os.path.join(ROOT, 'index.html')
with open(_home_path, encoding='utf-8') as _home_file:
    _home_source = _home_file.read()
_home_start = '<!-- TESTIMONIALS:START -->'
_home_end = '<!-- TESTIMONIALS:END -->'
if _home_start not in _home_source or _home_end not in _home_source:
    raise RuntimeError('homepage testimonial release sentinels are missing')
_home_pre, _home_rest = _home_source.split(_home_start, 1)
_home_old, _home_post = _home_rest.split(_home_end, 1)
_home_block = homepage_testimonial_section()
_home_new = _home_pre + _home_start + '\n' + _home_block + '\n' + _home_end + _home_post
w('index.html', _home_new)

w('quote.html', quote_page())
w('about.html', about_page())
w('call.html', call_page())
w('missed-lead-recovery.html', missed_lead_recovery_page())

# sitemap + robots
urls = ['/', '/about', '/call', '/missed-lead-recovery', '/quote', '/privacy', '/es', '/pt', '/zh', '/services/'] + [f'/services/{s["slug"]}' for s in SERVICES] \
     + ['/industries/'] + [f'/industries/{i["slug"]}' for i in INDUSTRIES]\
     + LANG_URLS

# A sitemap date means "this URL's content changed", not "the sitemap builder ran".
# The old builder stamped TODAY on all forty URLs whenever one page changed, making
# the freshness signal useless to a crawler. A working-tree change is from today;
# otherwise Git supplies the last commit date for that page. This also avoids a file
# copy or no-op generator run making an old page look new.
def url_output(url):
    if url == '/':
        return 'index.html'
    # Language homes intentionally use /es, /pt and /zh without trailing slashes.
    # Resolve any route backed by a directory before asking Git for its lastmod;
    # otherwise every generator run falsely stamps those unchanged homes as today.
    if url.endswith('/') or os.path.isdir(os.path.join(ROOT, url.strip('/'))):
        return url.strip('/') + '/index.html'
    return url.strip('/') + '.html'

def url_lastmod(url):
    rel = url_output(url)
    page = os.path.join(ROOT, rel)
    if not os.path.exists(page):
        return TODAY
    dirty = subprocess.run(
        ['git', 'status', '--porcelain', '--', rel], cwd=ROOT,
        check=True, capture_output=True, text=True).stdout.strip()
    if dirty:
        return TODAY
    committed = subprocess.run(
        ['git', 'log', '-1', '--format=%cs', '--', rel], cwd=ROOT,
        check=True, capture_output=True, text=True).stdout.strip()
    return committed or TODAY

sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u in urls:
    sm += f'  <url><loc>{BASE}{u}</loc><lastmod>{url_lastmod(u)}</lastmod></url>\n'
sm += '</urlset>\n'
w('sitemap.xml', sm)
w('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n')

print(f'\n{len(SERVICES)} service pages, {len(INDUSTRIES)} industry pages, 2 indexes, contractor product, quote, sitemap ({len(urls)} urls), robots.')

# ── IndexNow ──────────────────────────────────────────────────────
# There was no IndexNow code anywhere in this repo. README said "see git log for
# the exact call", which means it fired approximately once, by hand, ever, while
# the pages were regenerated many times a day. A step that lives in a person's
# memory is a step that does not happen; a step in the build is one that cannot
# be forgotten.
#
# Gated behind INDEXNOW=1 so local iteration does not POST the whole sitemap in
# a loop and get the key throttled. Prints the HTTP status, because a silent 4xx
# is exactly how this fails.
INDEXNOW_KEY = 'b20f1e412f2cff8af636fe5676cfdbcd'

def indexnow(paths):
    import json as _json, urllib.request, urllib.error
    if not paths:
        print('indexnow: nothing changed, nothing submitted')
        return
    host = BASE.replace('https://', '')
    payload = {
        'host': host,
        'key': INDEXNOW_KEY,
        'keyLocation': f'{BASE}/{INDEXNOW_KEY}.txt',
        'urlList': [BASE + u for u in paths],
    }
    req = urllib.request.Request(
        'https://api.indexnow.org/indexnow',
        data=_json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f'indexnow: HTTP {r.status} for {len(paths)} url(s)')
    except urllib.error.HTTPError as ex:
        print(f'indexnow: HTTP {ex.code} — {ex.read()[:200].decode(errors="replace")}')
    except Exception as ex:
        print(f'indexnow: failed — {ex}')

if os.environ.get('INDEXNOW') == '1':
    # A changed file maps back to the URL that serves it.
    def _url_of(rel):
        if rel == 'index.html':
            return '/'
        if rel.endswith('/index.html'):
            return '/' + rel[:-len('/index.html')]
        if rel.endswith('.html'):
            return '/' + rel[:-5]
        return None
    indexnow(sorted({u for u in (_url_of(r) for r in CHANGED) if u}))
else:
    print(f'{len(CHANGED)} file(s) changed — run with INDEXNOW=1 to submit them')
