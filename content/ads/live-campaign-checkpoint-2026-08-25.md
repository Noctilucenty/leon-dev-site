# Leon Builds Google Search live checkpoint — 2026-08-25 PT

This is a dated observation of campaign `24176728247` after the metro-targeting
and efficiency cleanup. Google Ads remains the authority for delivery, policy,
and spend. The frozen CSV build pack is not a live-account ledger.

## Verified live state

- Campaign: `LB | Orlando + Phoenix | Search | Contractor Websites | 2026-08-25`
- Campaign state: enabled; Google reports `Eligible (Learning)`
- Ad group: `Contractor Websites | Exact+Phrase`
- Flight: August 25 through September 3, 2026
- Schedule: 6:00 AM–10:00 PM Pacific Time
- Budget: $100 campaign total
- Bidding: Maximize clicks with a $5 maximum CPC
- Inventory: Google Search only; AI Max and automatically created assets off
- Locations: Orlando-Daytona Beach-Melbourne FL DMA and Phoenix AZ DMA,
  presence-only
- Search intent: eight exact/phrase keyword entries across four contractor
  website-design themes
- Negative keywords: 59 campaign-level entries observed after the expansion
- Today at review time: 0 impressions, 0 clicks, and $0.00 cost

The legacy Bay Area RSA is paused. Two metro RSAs are eligible: the earlier
12-headline ad is rated `Average`, and the replacement 15-headline ad is rated
`Good`. The replacement uses the clean landing URL and the stronger
keyword-led copy. The service-catalog structured snippet, scope-accurate
sitelinks, and positive callouts remain associated with the campaign. No call
asset was added.

## Tracking reconciliation

A campaign-level final URL suffix is now saved:

`utm_source=google&utm_medium=cpc&utm_campaign=metro-missed-lead-recovery-v1&utm_term={keyword}&utm_content={creative}`

Google's tracking test found both sampled landing pages. This suffix covers the
clean sitelink destinations and the replacement RSA, whose saved final URL is:

`https://leonbuilds.org/missed-lead-recovery`

The earlier metro RSA still has its inline UTM query string, so it can emit
duplicate UTM keys while it remains eligible. Google Ads' ad-blocker warning
collapsed the table rows and prevented a verified UI pause of that one row.
The clean replacement is live and eligible; the older metro RSA should be
paused as the first account cleanup once the table is interactive.

This platform test does not prove that the first-party lead path, booking path,
or Ads conversion actions have completed a real end-to-end attributed receipt.
Do not interpret zero platform conversions as either a tracking success or a
confirmed absence of inquiries.

## Cold-audience gate

The current configuration is clearer than the original Bay Area build. The
published homepage now identifies The Home Screen honestly as a client website
build with a demo checkout, and the contractor landing page makes scope,
pricing, proof, and next actions easy to scan. Seven testimonial drafts exist
locally. Heather's Flores Boxing Gloves feedback and Glenn's Home Screen website
feedback are now released from the tracked public allowlist after approval of
the exact quote, attribution, and placement. No star rating is published.
Glenn's website feedback is also placed directly on the contractor landing page.

The remaining high-impact work is:

1. pause the earlier metro RSA so only the clean-tracking replacement can serve;
2. verify Resend inbox delivery end to end; and
3. verify one real Ads-attributed quote or booking receipt before changing to a
   conversion-based bidding strategy.

The owner confirmed the final spend action after the website deployment and
Google identity verification. Campaign `24176728247` was enabled on August 25,
2026 with the verified $100 campaign-total budget and $5 maximum CPC. The live
account showed 0 impressions, 0 clicks, and $0.00 cost at the activation check.
