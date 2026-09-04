# Live ad destinations moved to the homepage — September 4, 2026

## Saved Google Ads changes

The owner authorized moving the existing Leon Builds ads to the new canonical
homepage. After Google completed its account-identity check, all three responsive
search ads in campaign
`LB | Orlando + Phoenix | Search | Contractor Websites | 2026-08-25` were opened
individually in the live account, updated, and saved:

- Enabled RSA `822269379998`: `https://leonbuilds.org/`. Its ad-level tracking
  template and final-URL suffix remain blank, so the existing campaign suffix is
  still inherited.
- Paused RSA `822240378944`:
  `https://leonbuilds.org/?utm_source=google&utm_medium=cpc&utm_campaign=metro-missed-lead-recovery-v1&utm_term={keyword}&utm_content=search-hs-rsa-b`.
- Paused legacy Bay Area RSA `822158837273`:
  `https://leonbuilds.org/?utm_source=google&utm_medium=cpc&utm_campaign=ba-missed-lead-recovery-v1&utm_term=home_services&utm_content=search-hs-rsa-a`.

Fresh read-only editor loads showed those exact saved destinations. A separate
post-save Overview load showed the first RSA as **Enabled / Not eligible** and
the other two as **Paused / Not eligible**. Their copy, display paths, ad status,
ad-group status, sitelinks, targeting, bidding, conversion settings, and campaign
controls were not changed.

The four sitelinks remain on their relevant Leon Builds pages (`/work`, `/call`,
`/quote`, and the original scope anchor). They are supporting links rather than
the ads' primary destinations, so replacing all four with the same homepage URL
would remove their distinct purpose.

## Delivery and spending state

This destination update did **not** restart paid delivery. The campaign still
shows an Enabled control, but its fixed flight was August 25–September 3, 2026
and the ads are not eligible to serve after that end date. The existing campaign
total budget remains **$100**. The latest account view showed **73 impressions,
3 clicks, and $14.73 spent**, leaving at most $85.27 within that original cap.
Extending the end date or approving any new allocation is a separate owner
decision.

The live Meta account was also opened fresh. The Leon Builds Instagram-profile
and Marketplace-message promotions were **Off**. Those promotions use Meta or
Instagram destinations rather than an external website final URL, so there was
no Leon Builds homepage URL to replace. No Meta campaign, unpublished edit,
budget, or status was changed.

## Local build pack and measurement

The local Google and Meta build CSVs now use `https://leonbuilds.org/` as the
primary destination while preserving their existing UTM values. The refreshed
homepage retains first/last attribution, click identifiers, the shared analytics
session, receipt-backed quote conversion, and the consent-gated Google Ads
conversion bridge. The app-development lane remains `HOLD_NO_BUDGET`; changing
its draft URL does not authorize or make that offer ready to run.

Google Ads reporting is not real-time. These saved URLs and UI statuses prove the
account configuration observed on September 4; they do not prove new delivery,
inquiries, qualified leads, or clients.
