# Leon Builds lead-email checkpoint — 2026-09-05

This records the live state checked on September 5, 2026. It is an operational checkpoint, not a claim that every future message will reach every inbox.

## Sending domain

- Resend domain: `leonbuilds.org`
- Resend domain ID: `446d389d-39ff-447b-b7e8-af4f18bfb00c`
- Resend dashboard status: `verified`
- Sender configured on Render: `Leon Builds <hello@leonbuilds.org>`
- Public DNS was resolved through the system resolver, Cloudflare `1.1.1.1`, and Google `8.8.8.8`:
  - DKIM TXT at `resend._domainkey.leonbuilds.org`
  - sending CNAME `rsend.leonbuilds.org` -> `rsend.forge.rmta.net.`
  - tracking CNAME `send.leonbuilds.org` -> `send.forge.rmta.net.`
  - DMARC TXT at `_dmarc.leonbuilds.org`: `v=DMARC1; p=none;`

The existing website records, Namecheap forwarding MX records, and forwarding SPF record were left in place.

## Delivery proof

- Render service: `leon-assist` (`srv-da1pb4qjnfac739v3e4g`)
- Sender-setting deploy: `dep-dadtu3m7bikc73fdi21g`
- Controlled probe receipt: `lead_218ceb9f-3e6c-46ca-9e8c-6142013ecf6c`
- Probe tag: `PIPELINE-CHECK-20260905T094143Z-16D8F7F1`
- Resend provider message ID: `5fa39b38-f1fd-4678-90f9-c7edd7c157fe`
- Resend showed both `sent` and `delivered` for the exact message.
- The configured owner Gmail inbox showed the same sender, subject, receipt ID, and probe body at 2:41 AM PDT.
- Durable confirmation was recorded at `2026-09-05T10:07:05.424Z`.

The probe was explicitly marked synthetic and is excluded from lead and conversion counts. No fake visitor inquiry or advertising conversion was created.

## Final live health

`GET https://leon-assist.onrender.com/api/health` returned:

```json
{
  "leadEmailProvider": "resend",
  "leadEmailState": "verified",
  "leadEmailVerified": true,
  "visitorEmailConfirmationConfigured": true,
  "visitorEmailConfirmationState": "verified",
  "acquisitionStorageState": "durable-configured",
  "leadEmailVerifiedAt": "2026-09-05T10:07:05.424Z"
}
```

Visitor confirmations remain fail-closed. Changing the provider, exact `LEAD_FROM_EMAIL`, or `LEAD_TO_EMAIL` invalidates this confirmation until a new inbox-confirmed delivery probe is completed.
