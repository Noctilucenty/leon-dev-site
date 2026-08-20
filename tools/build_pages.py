#!/usr/bin/env python3
"""Generates the SEO page fleet: /services/*, /industries/*, both index pages,
/quote, sitemap.xml and robots.txt — all in the site's own visual language
(same styles.css, nav, footer, lowercase-by-CSS, one accent).

Run after editing PAGE DATA below:   python3 tools/build_pages.py
Anything inside services/ and industries/ is overwritten on every run.
Render static sites serve pretty URLs, so /services/websites -> websites.html.
"""
import html, json, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://leonbuilds.org"
TODAY = datetime.date.today().isoformat()

# ══════════════════════════════════════════════════════════════════
# PAGE DATA
# ══════════════════════════════════════════════════════════════════

SERVICES = [
 dict(slug="websites", name="business websites", h1=("a website that", "works as hard as you do"),
  price="$1,200", title="Business Website Design — from $1,200 | Leon Kelvin Li",
  desc="Fast business websites built directly by one developer. Fixed quote before work starts, you own everything. Serving businesses across the U.S.",
  intro=["a lot of good businesses still have no website, or one from 2016 that nobody can update. customers check online before they call — if they find nothing, or something broken on a phone, they call the next place.",
   "i build sites that load fast, read clearly on a phone in a parking lot, and that you can update yourself without calling me. price agreed in writing before i start."],
  pains=["you have no website, or you're embarrassed to send people to it","it looks broken on phones","nobody on your team can change the text or the hours","it doesn't take bookings, orders or payments","you paid an agency and can't even log into your own site"],
  build=["a fast site you own completely — domain, hosting, code","editable by you: change hours, prices and photos yourself","booking, ordering or payments built in when you need them","found on google and by ai assistants people ask instead of google","english, spanish, portuguese or chinese — i speak all four"],
  proof=("curio + this site","the app store app, this site, and every system on the work page were built by the same person you'd be hiring."),
  faqs=[("how much does a website cost?","business sites start at $1,200 and landing pages at $400. the real number depends on pages and features — you get a written fixed quote before anything starts, and it doesn't change after."),
   ("i already have a website. do i have to start over?","usually not. most sites have one real problem — slow, broken on phones, or nobody can update it. redesigns start at $1,500 and i'll tell you which parts are worth keeping."),
   ("how long does it take?","most business sites take one to two weeks, with a working link you can watch during the build.")],
  related=["booking-systems","seo","business-automation"]),

 dict(slug="mobile-apps", name="mobile apps", h1=("an app on the store,","not stuck in development"),
  price="$4,500", title="iOS & Android App Development — from $4,500 | Leon Kelvin Li",
  desc="Custom iOS and Android apps built end to end by one developer — through App Store review and onto the store. Fixed quotes, nationwide.",
  intro=["most app projects die between the idea and the store. agencies quote six figures; freelancer marketplaces hand you code that never passes apple's review.",
   "i've taken my own app through app store review solo — design, code, backend, subscriptions, the review process, and the appeal when review got it wrong. that whole path is what you're buying."],
  pains=["you have an app idea and no technical team","your customers keep asking 'do you have an app?'","you got an agency quote with too many zeros","someone built you an app that never made it to the store","you need the backend, accounts and payments — not just screens"],
  build=["ios and android from one codebase where that's the right call","the backend, accounts, notifications and payments behind it","app store and play submission handled, including review problems","subscriptions and in-app purchases wired correctly","you own the developer accounts and the code from day one"],
  proof=("curio — live on the app store","a consumer ios app built solo end to end: react/typescript, capacitor, express, postgres, storekit subscriptions, ai content in four languages."),
  faqs=[("what does an app cost?","full builds start at $4,500. a simple internal app costs less than a consumer app with accounts, payments and push. you get a fixed written quote first — the number doesn't move after."),
   ("ios first or both?","usually both from one codebase. if your customers are heavily iphone (common for consumer) or android (common for field crews), we start there."),
   ("who owns the app?","you. the developer accounts, the store listing, the code and the backend are all in your name.")],
  related=["custom-software","websites","mobile-apps"]),

 dict(slug="ai-chatbots", name="ai chatbots", h1=("answers customers,", "without inventing prices"),
  price="$1,000", title="AI Chatbot for Your Business — from $1,000 | Leon Kelvin Li",
  desc="AI chatbots trained on your business that answer customer questions on your website 24/7 — and say 'I don't know' instead of making things up.",
  intro=["most of what customers ask is the same twenty questions: hours, prices, availability, 'do you do X'. a chatbot trained on your business answers those instantly, at 2am, in multiple languages.",
   "the difference between a good one and a lawsuit is restraint: mine cite your real information and say 'i don't know — here's how to reach a person' instead of inventing a price you'll have to honour. the assistant on this site is one i built."],
  pains=["staff answer the same questions all day","after-hours visitors leave without answers","your website gets traffic but no messages","spanish or chinese-speaking customers get no help","you tried a chatbot builder and it made things up"],
  build=["a chatbot trained only on your verified business information","escalation to a human the moment it should","lead capture built in — conversations become contacts","multilingual: english, spanish, portuguese, chinese","guardrails: no invented prices, no promises you didn't make"],
  proof=("compliance-aware assistant","a chinese-language assistant for a regulated market: every claim must cite a source, and it declines to answer rather than break advertising law. try the one on this site — bottom right."),
  faqs=[("what does a chatbot cost?","from $1,000 for a site chatbot trained on your business. connecting it to booking or your other systems adds scope — fixed quote before anything starts."),
   ("will it say something wrong to a customer?","that risk is the whole design problem. mine only answer from your approved information, cite it, and hand off to a human when unsure. i've built one for a market where a wrong sentence breaks the law."),
   ("can it capture leads?","yes — the good ones qualify a visitor and package the conversation for you, like the assistant on this page does.")],
  related=["ai-phone-agents","business-automation","websites"]),

 dict(slug="ai-phone-agents", name="ai phone agents", h1=("your phone, answered", "at 2am and during the rush"),
  price="$1,200", title="AI Phone Agent — from $1,200 | Leon Kelvin Li",
  desc="An AI that answers your business phone, handles the repetitive calls, books appointments and hands anything unusual to a person. Built with written handoff rules.",
  intro=["missed calls are missed revenue: every call that rings out while your team is busy is a customer calling the next name on the list.",
   "an ai phone agent answers instantly, handles the repetitive calls — hours, booking, status checks — and transfers to a person the moment the call isn't routine. that handoff rule gets written down with you, not guessed."],
  pains=["calls ring out during the rush or after close","one person spends half their day on 'are you open' and 'is it ready'","voicemail is where your leads go to die","the front desk can't book and answer phones at once"],
  build=["an agent that answers every call, immediately","booking wired into your real calendar or scheduling system","status lookups from your own systems where they expose data","instant transfer to staff on anything unusual — rules in writing","call summaries so you see what customers actually ask"],
  proof=("built with the same discipline as the review desk","every ai system i ship keeps a human in the loop by design — the review desk drafts replies but a person presses send. phone agents get the same treatment."),
  faqs=[("what happens when the ai can't handle a call?","it transfers to a person, following escalation rules we write down together before launch. the goal is removing repetitive calls, not removing humans."),
   ("what does it cost?","from $1,200 depending on what the agent needs to do — answering and booking is simpler than pulling live order status from your systems."),
   ("does it work with my scheduling software?","often, if your system exposes the data. i verify the specific integration before quoting rather than promising first.")],
  related=["ai-chatbots","booking-systems","business-automation"]),

 dict(slug="business-automation", name="business automation", h1=("the follow-ups happen", "whether anyone remembers or not"),
  price="$600", title="Workflow & Business Automation — from $600 | Leon Kelvin Li",
  desc="Form-to-sheet-to-email workflows, Google Workspace and n8n automation, and integrations that stop your team copying data between systems by hand.",
  intro=["most 'we need software' problems are actually 'two systems don't talk' problems. the fix is rarely a new platform — it's a pipe between the tools you already pay for.",
   "i build those pipes where your team can see them: google workspace automations in apps script, n8n workflows your staff can read and edit, and integrations with quickbooks, stripe, slack, your pos, your ats."],
  pains=["data gets copied between systems by hand","new leads and form submissions sit unanswered","reports take hours of exporting and pasting","approvals and handoffs live in someone's memory","five tools, none of them talking to each other"],
  build=["form → sheet → document → email chains, end to end","n8n pipelines your team can edit without calling me","integrations: quickbooks, stripe, google, slack, twilio, your pos","automatic reports that build themselves on schedule","document workflows: created, filed, approved, versioned"],
  proof=("document control","a request names a template; seconds later the google doc exists, filed and shared correctly. approval locks it, publishing versions it. built in apps script, then again as six n8n workflows the team edits themselves."),
  faqs=[("what should i automate first?","the thing a person does most often with the least judgment — retyping, forwarding, filing. we find it in the free call; it's usually obvious within ten minutes."),
   ("is this ai?","mostly not, and that's a feature. deterministic automations are cheaper and more reliable. ai enters only where reading or drafting is involved."),
   ("what does it cost?","simple integrations start at $600 and workflow automation around $600–$1,200. the saved hours usually repay it within months.")],
  related=["business-dashboards","ai-chatbots","custom-software"]),

 dict(slug="custom-software", name="custom software", h1=("built around how your", "business actually runs"),
  price="$3,500", title="Custom Software Development | Leon Kelvin Li",
  desc="Custom business software built end to end by one developer: portals, platforms, operations systems. Fixed written quotes. U.S.-wide, remote.",
  intro=["off-the-shelf software fits the average business. yours isn't average — that's why there's still a spreadsheet holding part of it together.",
   "custom software is for when nothing on the menu is the shape of your problem: the multi-brand ordering system on my work page exists because no ordering product could split one cart into a ticket and payout per kitchen. that unusual middle part is most of what i build."],
  pains=["you've outgrown the spreadsheet that runs part of the business","off-the-shelf tools each do 70% of what you need","your industry has a workflow no product understands","you're paying for five subscriptions to approximate one system"],
  build=["operations systems designed around your real workflow","web apps your team logs into every day","the database, accounts, permissions and reports underneath","migrations off the spreadsheet without losing history","one system replacing several almost-right subscriptions"],
  proof=("multi-brand ordering","one cart across many restaurant brands; the server re-prices every line, splits a ticket per vendor and computes each vendor's fee. no off-the-shelf product does that."),
  faqs=[("how do i know custom is worth it vs off-the-shelf?","if an existing product does 90% of what you need, buy it — i'll tell you so in the free call. custom wins when the missing 30% is the part your business actually runs on."),
   ("what does custom software cost?","full builds start at $3,500 and scale with scope. quotes are written and fixed, with staged payments tied to milestones you can see working."),
   ("what happens if you get hit by a bus?","the code, repo, accounts and documentation are in your name from day one. any competent developer can pick it up — nothing is set up to make me irreplaceable.")],
  related=["mobile-apps","business-automation","business-dashboards"]),

 dict(slug="booking-systems", name="booking & online ordering", h1=("customers book and order themselves —", "the reminder does the rest"),
  price="$600", title="Booking & Online Ordering — from $600 | Leon Kelvin Li",
  desc="Booking and online ordering built into your own website: appointments, deposits, no-show-killing reminders, and a cart that keeps the commission. Owned by you, no per-booking fees.",
  intro=["every booking that happens over the phone costs staff time, and every no-show costs the whole slot. online booking fixes the first; automatic reminders fix the second — the reminder is the part that pays for the build.",
   "i build booking into your own site — your calendar, your rules, deposits if you want them — rather than renting a generic widget with someone else's branding and a per-booking fee.",
   "ordering works the same way. a cart on your own site keeps the 15-30% a delivery app takes on every order, and the customer stays yours instead of theirs."],
  pains=["booking happens by phone and eats front-desk time","no-shows are killing your calendar","after-hours visitors can't book and don't call back","a delivery app takes a cut of every order and owns your customer","your current booking tool takes a cut or looks like an ad for itself"],
  build=["booking pages that match your site, not a widget's brand","staff calendars, service durations, buffer rules","deposits and card-on-file through stripe","automatic sms/email reminders and easy rescheduling","sync with the calendar your team already lives in","commission-free ordering: cart, payment, and a ticket that reaches the kitchen"],
  proof=("built like the ordering system","the same server-side discipline as the multi-brand ordering platform: rules enforced where customers can't edit them."),
  faqs=[("what does a booking system cost?","from $600 built into your site, and commission-free online ordering from $2,000. no monthly per-booking cut — you own it."),
   ("can customers pay a deposit when they book?","yes — deposits, full prepayment or card-on-file, through stripe, with receipts handled."),
   ("we already use a scheduling tool. keep it?","if it works, keep it — sometimes the right build is your website talking to it. i'll tell you which in the free call.")],
  related=["websites","ai-phone-agents","business-automation"]),

 dict(slug="business-dashboards", name="dashboards & internal tools", h1=("the four numbers that decide", "your week, on one screen"),
  price="$750", title="Dashboards & Internal Tools — from $750 | Leon Kelvin Li",
  desc="Live dashboards that replace the Friday export ritual, plus the small internal tools and Chrome extensions that delete the copy-paste out of a job your team does forty times a day.",
  intro=["somebody on your team spends part of every week exporting, pasting and reformatting the same report. and by the time it's read, it's old.",
   "a dashboard pulls those numbers live from the systems that already have them — sales, bookings, stock, ad spend — onto one screen you check in ten seconds.",
   "the same goes for the job somebody does forty times a day in six clicks. a small internal tool or chrome extension that makes it one click is the highest return-per-dollar software i build."],
  pains=["reports are assembled by hand every week","the numbers live in five different logins","you find out about a bad week after it's over","a repetitive task eats hours across the team","the answer to 'how do we know this number' is 'ask the one person who knows'"],
  build=["live dashboards fed straight from your real systems","the handful of numbers that matter, not eighty charts","alerts when a number crosses a line you set","scheduled email summaries for people who won't open a dashboard","clean history so trends are visible, not remembered","chrome extensions and small tools built for the exact job, nothing else"],
  proof=("site intelligence","decision support scoring all 33,772 us zip codes across nine data sources — with every score carrying an uncertainty band instead of false precision. dashboards are the small sibling of that discipline."),
  faqs=[("what does a dashboard cost?","a small internal tool starts at $750 and a dashboard at $1,000, depending on how many systems feed it. fixed quote before work starts."),
   ("our data is a mess. does that matter?","that's normal — cleaning and joining it is part of the build, not a surcharge surprise."),
   ("can it pull from our pos / quickbooks / sheets?","usually yes. i verify your specific systems before quoting.")],
  related=["business-dashboards","ai-chatbots","custom-software"]),

 dict(slug="seo", name="seo & ai search", h1=("found on google — and by", "the ais people ask instead"),
  price="$450", title="SEO & AI Search Optimization | Leon Kelvin Li",
  desc="Technical SEO plus AI-search optimization: be found on Google and recommended by the AI assistants customers increasingly ask instead.",
  intro=["search is splitting in two: google on one side, and ai assistants — chatgpt, gemini, perplexity — on the other. your customers already use both to decide who to call.",
   "i do the technical side honestly: structured data, speed, clean pages that answer real questions — no doorway-page spam, no thousand junk articles. the same work that ranks you also makes ais recommend you, because both read the same web."],
  pains=["you're invisible when customers search for what you sell","competitors with worse work outrank you","an agency charges monthly and can't say what changed","ai assistants recommend other businesses, never yours"],
  build=["technical seo: speed, structure, schema, clean urls","pages that answer the questions customers actually type","ai-search optimization so assistants can read and cite you","local relevance without fake location spam","measurement, so you know what a ranking is worth"],
  proof=("this site","the site you're reading practices what it sells — structured data, honest pages, no spam. search for the work and judge it."),
  faqs=[("how is ai search different from seo?","ais read the same web but reward clear structure and verifiable claims even more. the honest version of seo serves both; the spam version now fails at both."),
   ("what does it cost?","from $450 for a technical pass on an existing site. ongoing work is scoped in writing — no vague monthly retainer."),
   ("can you guarantee rankings?","no, and nobody honest can. i can guarantee the technical work is done right and show you exactly what changed.")],
  related=["websites","ai-chatbots","business-dashboards"]),
]

INDUSTRIES = [
 dict(slug="restaurants", name="restaurants & food", h1=("software for", "restaurants & food businesses"),
  title="Software for Restaurants & Food | Leon Kelvin Li",
  desc="Online ordering without the 30% commission, AI phone agents for the rush, and websites customers can order from. Built by one developer, U.S.-wide.",
  intro=["restaurants run on thin margins while delivery apps take up to 30% and the phone rings through every rush. most of that is fixable with software you own instead of rent.",
   "i built a multi-brand ordering platform where one cart spans several kitchens and the server splits every order into per-vendor tickets and payouts — so the ordinary single-restaurant version is well-trodden ground."],
  pains=["delivery apps take a commission on orders that were already yours","the phone rings out during every rush","your menu is a pdf nobody can read on a phone","'are you open' and 'do you have parking' — forty times a day","multiple locations or brands, zero shared systems"],
  fixes=[("online ordering you own","commission-free ordering on your own site — cart, payment, kitchen ticket. from $2,000"),
   ("ai phone agent","answers during the rush, takes the routine calls, hands the rest to staff. from $1,200"),
   ("a menu-first website","fast, phone-first, editable by you when prices change. from $1,200"),
   ("review desk","every review read and a reply drafted for you — a human presses send. from $750")],
  proof=("multi-brand ordering","one cart across many kitchens; the server re-prices every line, splits tickets per vendor, computes fees. running for a 22-business operation."),
  faqs=[("can i stop paying delivery-app commissions?","for pickup and your own delivery, yes — ordering on your own site has no per-order cut. marketplaces still bring discovery; the goal is moving your regulars to the channel you own."),
   ("what does online ordering cost?","from $2,000 one-time, on your site, you own it. compare that to a month of commissions."),
   ("i have two locations with different menus.","that's exactly what the multi-brand system was built for — shared platform, separate menus, tickets and payouts.")],
  related_services=["booking-systems","ai-phone-agents","websites"]),

 dict(slug="contractors", name="contractors & home services", h1=("software for", "contractors & home services"),
  title="Software for Contractors | Leon Kelvin Li",
  desc="Lead follow-up automation, scheduling, job tracking and customer portals for contractors and home-service businesses across the U.S.",
  intro=["contracting work is won and lost in the follow-up: the lead that came in while you were on a roof, the estimate that never went out, the customer who called someone else because you answered second.",
   "software fixes the boring half of that — instant lead responses, scheduling, job status a customer can check without calling you."],
  pains=["leads arrive while you're on site and go cold","estimates and invoices happen at 9pm from the truck","customers call constantly for status updates","jobs live on a whiteboard or in one person's head","reviews never get asked for, so the profile looks dead"],
  fixes=[("lead follow-up automation","every web lead gets an instant text/email and lands in one list. from $600"),
   ("scheduling & job tracking","jobs, crews and dates in one system the whole team sees. from $1,500"),
   ("customer portal","clients see their own job status, photos and invoices. from $2,500"),
   ("a website that sells","before/after work, service areas, instant quote requests. from $1,200")],
  proof=("document control","approvals, versioned documents and automatic filing — the same machinery that keeps a contracting back office from living in someone's memory."),
  faqs=[("i'm not technical at all. is that a problem?","no. you describe the week, i build around it, and everything is handed over working with training included."),
   ("what pays for itself fastest?","almost always lead follow-up — answering first wins jobs. usually from $600 and live within days."),
   ("do you work outside california?","yes — remote across the u.s. this kind of build never needs me on site.")],
  related_services=["business-automation","custom-software","websites"]),

 dict(slug="automotive", name="auto repair & automotive", h1=("software for", "auto shops & automotive"),
  title="Software for Auto Repair Shops | Leon Kelvin Li",
  desc="Kill the 'is my car ready?' calls: AI phone agents, status updates, online booking and shop dashboards for automotive businesses.",
  intro=["every shop knows the two calls: 'can i bring it in?' and 'is it ready yet?'. both interrupt the person doing the actual work.",
   "booking can go straight into your calendar. status can text the customer automatically the moment a job changes state — and an ai phone agent can answer the rest."],
  pains=["'is my car ready' calls interrupt the bay all day","booking happens by phone and gets double-entered","customers wait on hold, then show up at the wrong time","your shop software has the data but customers can't see it"],
  fixes=[("automatic status updates","'your car is ready' sends itself when the job closes. from $600"),
   ("online booking","customers pick a slot; your calendar stays sane. from $600"),
   ("ai phone agent","handles hours, booking and routine status; transfers the rest. from $1,200"),
   ("shop dashboard","cars in, cars out, revenue and comebacks on one screen. from $1,000")],
  proof=("review desk","built for exactly this kind of local business: every review read, classified, and a reply drafted from your real facts — a human presses send."),
  faqs=[("does this work with my shop management system?","often — many expose the data needed for status and booking. i verify yours specifically before quoting anything."),
   ("what's the fastest win?","status notifications. one integration, and the most annoying call category mostly disappears."),
   ("multiple locations?","yes — shared platform, per-location calendars and numbers is a normal build.")],
  related_services=["ai-phone-agents","booking-systems","business-automation"]),

 dict(slug="healthcare", name="medical & dental", h1=("software for", "medical & dental practices"),
  title="Software for Medical & Dental Offices | Leon Kelvin Li",
  desc="Online booking, no-show-killing reminders and after-hours question handling for clinics and dental practices. Careful, human-in-the-loop builds.",
  intro=["a practice front desk answers the same questions all day — insurance, hours, directions, 'can i move my appointment' — while the schedule fills with no-shows that reminders would have caught.",
   "health care deserves the careful version of software: reminders and booking that reduce the front desk load, an assistant that answers the routine and hands anything clinical straight to a human. i've built compliance-aware ai that declines to answer rather than overstep — that's the posture your patients get."],
  pains=["no-shows burn schedule and revenue","the phone queue is insurance and reschedule questions","after-hours callers reach voicemail and book elsewhere","forms are still paper or pdf-by-email"],
  fixes=[("appointment reminders","sms/email sequences that actually cut no-shows. from $600"),
   ("online booking & rescheduling","patients handle the routine moves themselves. from $600"),
   ("after-hours question handling","routine questions answered; anything clinical goes to staff. from $1,000"),
   ("digital intake forms","filled on a phone before the visit, filed automatically. from $600")],
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
  fixes=[("tenant portal","submit a request, attach a photo, watch the status change. from $2,500"),
   ("maintenance tracking","requests routed to vendors, updates sent automatically. from $1,000"),
   ("owner reporting","statements that build themselves from your real data. from $1,000"),
   ("listing website","fast property pages with inquiry capture that reaches you instantly. from $1,200")],
  proof=("customer-portal discipline","the multi-brand platform runs strict per-account visibility for 22 businesses — the same permission model a tenant/owner portal needs."),
  faqs=[("can tenants see each other's information?","no — per-account visibility is enforced on the server, which is the core of the build."),
   ("we use appfolio / buildium / yardi.","keep it if it works — often the right build is a portal or automation talking to your existing system. i verify the integration before quoting."),
   ("what does a tenant portal cost?","from $2,500 depending on what tenants and owners need to see and do.")],
  related_services=["custom-software","business-automation","websites"]),

 dict(slug="logistics", name="logistics & warehousing", h1=("software for", "logistics & warehousing"),
  title="Software for Logistics & Trucking | Leon Kelvin Li",
  desc="Dispatch boards, driver apps, document automation and customer tracking for logistics and warehouse operations.",
  intro=["logistics runs on information handoffs — and every handoff that happens by phone, email-forward or retyping is a delay and an error waiting to happen.",
   "dispatchers copying between emails and spreadsheets, drivers texting photos of paperwork, customers calling for eta: each of those is a solved software problem."],
  pains=["dispatch copies the same info between email, sheets and texts","drivers hand in paperwork that gets retyped","customers call for status because they can't see it","inventory counts drift from reality"],
  fixes=[("dispatch board","loads, drivers and statuses on one live screen. from $1,500"),
   ("driver app","photos, signatures and status from the cab — no retyping. from $4,500"),
   ("document automation","pods, bols and invoices extracted and filed automatically. from $1,200"),
   ("customer tracking portal","they look it up instead of calling you. from $2,500")],
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
  fixes=[("class booking","members book, waitlist and cancel themselves. from $600"),
   ("membership dashboard","attendance, payments and fade-outs on one screen. from $1,000"),
   ("reminder automation","class reminders and win-back nudges that send themselves. from $600"),
   ("a site that converts","schedule, pricing and signup without a phone call. from $1,200")],
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
  fixes=[("inventory system","stock, suppliers and low-stock alerts that survive a rush. from $1,500"),
   ("order automation","every channel's orders into one queue with alerts. from $600"),
   ("sales dashboard","today's numbers without opening five systems. from $1,000"),
   ("storefront","fast product pages, clean checkout, no template bloat. from $1,200")],
  proof=("multi-brand ordering","server-side pricing, per-vendor tickets and payouts across 22 businesses — retail-grade order handling in production."),
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
  fixes=[("client portal","cases, files, invoices and status in one login. from $2,500"),
   ("intake automation","forms that fill in on a phone, file and notify automatically. from $600"),
   ("document workflows","created, versioned, approved and filed — automatically. from $1,200"),
   ("firm dashboard","matters, pipeline and billing on one screen. from $1,000")],
  proof=("document control","request → document created, filed, approved, locked, versioned and published — running today, built twice (apps script and n8n) so the team can edit it."),
  faqs=[("is client data safe?","per-client visibility is enforced server-side, and you own the code and hosting — auditable by anyone you choose."),
   ("we bill hourly. does this change that?","it removes the hours you can't bill — admin — and keeps the ones you can."),
   ("what does a portal cost?","from $2,500; intake automation from $600. written fixed quotes.")],
  related_services=["custom-software","business-automation","business-dashboards"]),

 dict(slug="startups", name="startups", h1=("software for", "startups & founders"),
  title="MVP & Product Development for Startups | Leon Kelvin Li",
  desc="MVPs that actually ship: app + backend + payments from one developer who has taken his own product through App Store review.",
  intro=["a founder with an idea needs the version of the product that can meet users — not a six-month engagement, not a no-code demo that collapses at the first real feature.",
   "i've shipped my own consumer app solo: design, code, backend, subscriptions, app store review, the appeal when review got it wrong. that end-to-end path is what an mvp needs, and you keep the repo."],
  pains=["you have the idea and the users, not the technical team","agency quotes start at six figures","the no-code prototype hit its ceiling","your technical co-founder search is month six"],
  fixes=[("mvp build","the smallest version that real users can use — app or web. from $3,500"),
   ("app + backend + payments","the whole stack, not just screens. from $4,500"),
   ("ai features","assistants, retrieval and pipelines with guardrails that hold. from $1,000"),
   ("ongoing development","a standing block of hours as you see fit. from $450/mo")],
  proof=("curio","consumer ios app on the app store: react/typescript, capacitor, express, postgres, storekit subscriptions, ai content in four languages — built alone."),
  faqs=[("how fast can an mvp ship?","weeks, not quarters — scope decides. we cut to the version that tests the idea, in writing, before building."),
   ("do i own the code?","completely — repo, accounts and infrastructure from day one. investors will ask; the answer is yes."),
   ("can you keep building after launch?","yes — ongoing from $450/mo, or fixed quotes per milestone as you raise.")],
  related_services=["mobile-apps","custom-software","ai-chatbots"]),
]

# ══════════════════════════════════════════════════════════════════
# TEMPLATE
# ══════════════════════════════════════════════════════════════════

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@200;300;400;500;600&family=Space+Grotesk:wght@300;400;500&display=swap" rel="stylesheet">'

def e(s): return html.escape(str(s), quote=True)

def nav():
    return '''<a class="skip" href="#main">skip to content</a>
<div class="progress" id="progress" aria-hidden="true"></div>
<div class="cursor" id="cursor" aria-hidden="true"><span></span></div>
<header class="nav" id="nav">
  <a class="mark" href="/">
    <span class="mark-dot">[<span class="blink">•</span>]</span>
    <span class="mark-name">Leon Kelvin Li</span>
    <span class="mark-handle">/ Noctilucenty</span>
  </a>
  <nav class="nav-mid" id="navMid" aria-label="site">
    <a href="/#fix"><i>[</i><span>start here</span><i>]</i></a>
    <a href="/services/"><i>[</i><span>services</span><i>]</i></a>
    <a href="/industries/"><i>[</i><span>industries</span><i>]</i></a>
    <a href="/#work"><i>[</i><span>work</span><i>]</i></a>
    <a href="/#pricing"><i>[</i><span>pricing</span><i>]</i></a>
  </nav>
  <div class="nav-end">
    <a class="btn btn-solid magnet" href="/quote" data-evt="hero_quote_click"><span>get a quote</span></a>
    <button class="burger" id="burger" aria-expanded="false" aria-controls="navMid" aria-label="menu"><span></span><span></span></button>
  </div>
</header>'''

def footer():
    slinks = ''.join(f'<a href="/services/{s["slug"]}">{e(s["name"])}</a>' for s in SERVICES[:7])
    ilinks = ''.join(f'<a href="/industries/{i["slug"]}">{e(i["name"])}</a>' for i in INDUSTRIES[:7])
    return f'''<footer class="foot">
  <div class="rail foot-in">
    <div class="foot-brand">
      <a class="mark" href="/"><span class="mark-dot">[<span class="blink">•</span>]</span><span class="mark-name">Leon Kelvin Li</span><span class="mark-handle">/ Noctilucenty</span></a>
      <p>custom software and ai, built directly by one developer for businesses across the united states.</p>
      <p class="avail"><i></i>available for new projects</p>
    </div>
    <nav><h4>services</h4>{slinks}</nav>
    <nav><h4>industries</h4>{ilinks}</nav>
    <nav><h4>site</h4><a href="/#work">work</a><a href="/#pricing">pricing</a><a href="/#faq">faq</a><a href="/quote">get a quote</a><a href="https://github.com/Noctilucenty" target="_blank" rel="noopener">github</a></nav>
  </div>
  <div class="rail foot-bar">
    <p>© <span id="yr">2026</span> <span class="keepcase">Leon Kelvin Li</span> · california · working with businesses across the u.s.</p>
    <p><a href="mailto:leondragon3798@gmail.com">leondragon3798@gmail.com</a> · <a href="tel:+15108267735">(510) 826-7735</a></p>
  </div>
</footer>
<script src="/app.js" defer></script>
<script src="/assist.js" defer></script>'''

def head(title, desc, path, schema):
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
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}{path}">
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
      <a class="btn btn-solid magnet" href="/quote" data-evt="pricing_cta_click"><span>tell me what you need</span><svg class="ic"><use href="#ic-arrow"/></svg></a>
      <button class="btn magnet" type="button" data-assist-open data-assist-starter="{e(starter)}"><span>ask the ai about this</span></button>
      <a class="cx-mini" href="mailto:leondragon3798@gmail.com" data-evt="email_click">or email leon directly →</a>
    </div>'''

ICONS = '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="ic-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h15M13 6l6 6-6 6"/></symbol><symbol id="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 12.5l5 5 10-11"/></symbol></svg>'

def service_page(s):
    path = f'/services/{s["slug"]}'
    bc = [("home","/"),("services","/services/"),(s["name"], None)]
    schema = [
        {"@context":"https://schema.org","@type":"Service","name":s["name"],
         "provider":{"@type":"Person","name":"Leon Kelvin Li","url":BASE},
         "areaServed":{"@type":"Country","name":"United States"},
         "description":s["desc"]},
        faq_schema(s["faqs"]), breadcrumb_schema(bc, path)]
    pains = ''.join(f'<li>{e(p)}</li>' for p in s["pains"])
    build = ''.join(f'<li><svg class="ic"><use href="#ic-check"/></svg>{e(b)}</li>' for b in s["build"])
    intro = ''.join(f'<p class="sub">{e(p)}</p>' for p in s["intro"])
    related = ''.join(f'<a class="rel" href="/services/{r}">{e(next(x["name"] for x in SERVICES if x["slug"]==r))} →</a>' for r in s["related"])
    starter = f'i\'m looking at {s["name"]} — here\'s my situation: '
    return head(s["title"], s["desc"], path, schema) + ICONS + nav() + f'''
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
<section class="sec">
  <div class="rail two-col">
    <div>
      <p class="label">sounds familiar?</p>
      <ul class="plist">{pains}</ul>
    </div>
    <div>
      <p class="label">what i build for this</p>
      <ul class="blist">{build}</ul>
    </div>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <p class="label">proof, not promises</p>
    <div class="proofcard">
      <h2>{e(s["proof"][0])}</h2>
      <p class="sub">{e(s["proof"][1])}</p>
      <a class="cx-mini" href="/#work">see everything that's running →</a>
    </div>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <p class="label">questions people ask first</p>
    {faq_html(s["faqs"])}
    <p class="label" style="margin-top:3rem">related</p>
    <div class="relrow">{related}</div>
    {cta_block(starter)}
  </div>
</section>
</main>''' + footer() + '</body></html>'

def industry_page(i):
    path = f'/industries/{i["slug"]}'
    bc = [("home","/"),("industries","/industries/"),(i["name"], None)]
    schema = [
        {"@context":"https://schema.org","@type":"Service","name":f'software for {i["name"]}',
         "provider":{"@type":"Person","name":"Leon Kelvin Li","url":BASE},
         "areaServed":{"@type":"Country","name":"United States"},
         "description":i["desc"]},
        faq_schema(i["faqs"]), breadcrumb_schema(bc, path)]
    pains = ''.join(f'<li>{e(p)}</li>' for p in i["pains"])
    fixes = ''.join(f'<article class="fixcard"><h3>{e(t)}</h3><p>{e(d)}</p></article>' for t,d in i["fixes"])
    intro = ''.join(f'<p class="sub">{e(p)}</p>' for p in i["intro"])
    related = ''.join(f'<a class="rel" href="/services/{r}">{e(next(x["name"] for x in SERVICES if x["slug"]==r))} →</a>' for r in i["related_services"])
    starter = f'i run a business in {i["name"]} — here\'s what i\'m dealing with: '
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
<section class="sec">
  <div class="rail">
    <p class="label">the usual pain</p>
    <ul class="plist wide">{pains}</ul>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <p class="label">what actually fixes it</p>
    <div class="fixrow">{fixes}</div>
    <p class="sub" style="margin-top:1.4rem">every price is a published starting point, not a quote — the real number is agreed in writing before anything starts.</p>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <p class="label">proof, not promises</p>
    <div class="proofcard">
      <h2>{e(i["proof"][0])}</h2>
      <p class="sub">{e(i["proof"][1])}</p>
      <a class="cx-mini" href="/#work">see everything that's running →</a>
    </div>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <p class="label">questions people ask first</p>
    {faq_html(i["faqs"])}
    <p class="label" style="margin-top:3rem">related services</p>
    <div class="relrow">{related}</div>
    {cta_block(starter)}
  </div>
</section>
</main>''' + footer() + '</body></html>'

def listing_page(kind, items, title, desc, blurb):
    path = f'/{kind}/'
    bc = [("home","/"),(kind, None)]
    schema = [breadcrumb_schema(bc, path)]
    cards = ''.join(
        f'<a class="fixcard link" href="/{kind}/{x["slug"]}"><h3>{e(x["name"])}</h3><p>{e(x["desc"][:110])}…</p><span class="go">open →</span></a>'
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
    <p class="sub">prefer talking it through first? <button class="linklike" type="button" data-assist-open data-assist-starter="help me describe my project">ask the ai assistant</button> — it can help you write this.</p>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <form class="qform" id="qform" novalidate>
      <label>what does your business do?<input name="company" type="text" placeholder="two taquerias in dallas / a plumbing company / a dental office…"></label>
      <label>what are you trying to fix or build? <i>(required)</i><textarea name="problem" rows="4" required placeholder="the part of the week that's still manual, the thing that's broken, or the thing you wish existed…"></textarea></label>
      <label>what do you currently use for it?<input name="currentTools" type="text" placeholder="paper + phone / spreadsheets / quickbooks / square / nothing…"></label>
      <label>what result would make this worth paying for?<input name="desiredOutcome" type="text" placeholder="phone stops ringing about status / orders without commission / one less hire…"></label>
      <div class="qrow">
        <label>when do you want to start?
          <select name="timeline"><option value="">choose…</option><option>as soon as possible</option><option>within a month</option><option>next few months</option><option>just exploring</option></select>
        </label>
        <label>rough budget <i>(optional)</i>
          <select name="budget"><option value="">not sure yet</option><option>under $1,000</option><option>$1,000–$2,500</option><option>$2,500–$5,000</option><option>$5,000–$15,000</option><option>$15,000+</option></select>
        </label>
      </div>
      <div class="qrow">
        <label>name<input name="name" type="text" autocomplete="name"></label>
        <label>email <i>(required)</i><input name="email" type="email" required autocomplete="email"></label>
      </div>
      <label>phone <i>(optional)</i><input name="phone" type="tel" autocomplete="tel"></label>
      <input name="website" type="text" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true">
      <p class="qerr" id="qerr" role="alert"></p>
      <button class="btn btn-solid magnet qsend" type="submit" data-evt="quote_form_submit"><span>send it to leon</span><svg class="ic"><use href="#ic-arrow"/></svg></button>
      <p class="qnote">goes straight to leon — no sales team exists. you'll hear back at the email above. or skip the form: <a href="https://wa.me/15108267735?text=Hi%20Leon%20-%20saw%20your%20site.%20My%20business%20is%3A%20" target="_blank" rel="noopener" data-evt="wa_click_quote">whatsapp</a> · <a href="mailto:leondragon3798@gmail.com" data-evt="email_click">leondragon3798@gmail.com</a> · <a href="tel:+15108267735" data-evt="phone_click">(510) 826-7735</a></p>
    </form>
    <div class="qok" id="qok" hidden>
      <p class="label">almost there</p>
      <h2 class="dsp">your email app just opened. <em>hit send and it comes straight to leon.</em></h2>
      <p class="sub">everything you wrote is already in the message — nothing to retype. if nothing opened, <a id="qmail" href="mailto:leondragon3798@gmail.com" data-evt="email_click">open it here</a> or write to <a href="mailto:leondragon3798@gmail.com">leondragon3798@gmail.com</a>. urgent? call <a href="tel:+15108267735">(510) 826-7735</a>.</p>
    </div>
  </div>
</section>
</main>
<script>
(function(){
  var f=document.getElementById('qform'),err=document.getElementById('qerr'),ok=document.getElementById('qok');
  if(!f)return;
  var API=(window.LEON_ASSIST&&window.LEON_ASSIST.api)||(/^(localhost|127\\.0\\.0\\.1)$/.test(location.hostname)?'http://localhost:8787':'https://leon-assist.onrender.com');
  var started=false;
  f.addEventListener('input',function(){ if(!started){started=true; if(window.leonEvt)window.leonEvt('quote_form_start');} },{once:false});
  f.addEventListener('submit',function(ev){
    ev.preventDefault(); err.textContent='';
    var d=Object.fromEntries(new FormData(f).entries());
    if(!d.problem||!d.problem.trim()){err.textContent='tell me at least a sentence about what you need.';return;}
    if(!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$/.test(d.email||'')){err.textContent='that email does not look right.';return;}
    var attr={}; try{attr=JSON.parse(localStorage.getItem('leon_attr')||'{}')}catch(e){}
    d.via='quote-form'; d.sourcePage=location.pathname; d.referrer=attr.referrer||''; d.utmSource=attr.utmSource||''; d.utmMedium=attr.utmMedium||''; d.utmCampaign=attr.utmCampaign||'';
    // Logged server-side as a backup, but the person never waits on it: the
    // browser hands the message straight to their mail app instead.
    try{ fetch(API+'/api/lead',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d),keepalive:true}).catch(function(){}); }catch(e){}
    var href=mailtoFor(d);
    document.getElementById('qmail').href=href;
    f.hidden=true; ok.hidden=false; window.scrollTo({top:0});
    if(window.leonEvt)window.leonEvt('quote_form_submit');
    window.location.href=href;
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

def w(rel, content):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)
    print('wrote', rel)

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

w('quote.html', quote_page())

# sitemap + robots
urls = ['/', '/quote', '/es', '/pt', '/zh', '/services/'] + [f'/services/{s["slug"]}' for s in SERVICES] \
     + ['/industries/'] + [f'/industries/{i["slug"]}' for i in INDUSTRIES]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u in urls:
    sm += f'  <url><loc>{BASE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n'
sm += '</urlset>\n'
w('sitemap.xml', sm)
w('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n')

print(f'\n{len(SERVICES)} service pages, {len(INDUSTRIES)} industry pages, 2 indexes, quote, sitemap ({len(urls)} urls), robots.')
