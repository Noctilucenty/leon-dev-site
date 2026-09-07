# Leon Builds followthrough — September 6, 2026 Pacific Time

These are dated observations from September 6 Pacific Time (September 7 UTC
for the evening checks). They supersede older setup and route-count summaries;
they do not establish that a lead, booking, or sale occurred.

## Current website and inquiry delivery

The checkout was advanced to `a331f25b732a9256707e2c645a2a0b0d2dea103a`, preserving
the newer homepage offer and attributed LOQOL seller-portal contribution case.
The live site's fingerprint matched that commit's successful
[production search workflow](https://github.com/Noctilucenty/leon-dev-site/actions/runs/34074224170):

`b2c8699afee35178d396371d36dd4bb9a2ff166f2788fe2eae1bede5a9b5cc08`

The workflow verified **51 sitemap routes** returning HTTP 200 with exact
canonicals and no `noindex`. Fresh direct checks also returned 200 for the
homepage, work archive, contractor landing, quote, call, privacy and buyer guide.
The external Cal.com destination returned the free 15-minute call page.

Backend health reported owner email and visitor confirmations **verified**,
durable acquisition storage configured, and the Cal webhook secret configured.
The quote page still checks the accepted backend receipt. These are operational
checks; no new synthetic inquiry, booking, email, or conversion was submitted.

## Google Ads assets and delivery

Campaign `24218199248`, `LB | Orlando | Search | Contractor Review | 2026-09-05`,
retains its **$75.39 campaign-total budget** and **September 14 end date**.
All **10 keywords** were Enabled and Eligible at readback.

The **September 6 Pacific Time daily range** showed **1 impression, 1 click,
$5.00 cost, and 0 recorded conversions**, associated with the keyword
`general contractor website design`. A keyword is not the disclosed search
query, and a click is not an inquiry. This is a daily snapshot, not lifetime spend.

Four existing sitelinks were associated at **9:37 PM Pacific** and read back
as Eligible:

| Sitelink | Verified destination |
| --- | --- |
| Work & Project Examples | `/work` |
| Book A 15-Minute Call | `/call?service=contractor-lead-recovery` |
| Free 3-Point Site Review | `/quote?service=contractor-lead-recovery` |
| See The $1,500 Scope | `/missed-lead-recovery#scope` |

Four existing callouts were associated at **9:38 PM Pacific** and read back as
Eligible: **Written fixed quote first**, **From $1,500 fixed scope**,
**Estimate intake included**, and **Built by one developer**. The contractor
landing still supports that $1,500 starting scope despite the newer homepage offer.

## Conversion-goal cleanup

The Contact goal's account-default label was removed and the save verified:
**0 of 2 campaigns**, **0 primary actions**. Phone and WhatsApp actions remain
**Secondary**, counting **One**. Contact still displays **Misconfigured** because
it has no primary actions; this checkpoint does not claim that warning disappeared.

Submit lead form and Book appointment remain account-default goals, each used by
**2 of 2 campaigns**, with **1 primary action**, Healthy and Active at readback.
The legacy inactive Submit Lead form action remains Secondary, counting Every,
and excluded from account goals. Its inactive state does not describe the current
receipt-backed quote flow. No synthetic conversions were sent to change statuses.

## Search indexing followthrough

An authenticated API inspection of **10 priority URLs** found **8 indexed** and
**2 not indexed**; its detailed receipt remains private. Google's UI subsequently
accepted indexing requests for `/technical-build-partner` and
`/guides/contractor-inquiry-workflow`, showing **Indexing requested** and placement
in the priority crawl queue. Accepted requests do not establish completed indexing.

The sitemap API reported **50 processed URLs**, with its latest download at
**23:31 UTC**, before the newer 51-route sitemap. Neither that sitemap status nor
the successful 51-route HTTP crawl proves that all 51 pages are indexed.

No automatic monitor was created. Search reporting access, operational delivery,
ad eligibility, actual paid delivery, indexed pages and business outcomes remain
separate evidence. No real lead, booking, or sale is proven by these checks.
