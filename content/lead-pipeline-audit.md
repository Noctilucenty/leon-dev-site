# Lead pipeline audit — 2026-08-21

One real submission through the live form at leonbuilds.org/quote, traced end to
end in Render's application log. Not a code reading: an actual lead, actually
posted, actually followed.

## What was submitted

    name     PIPELINE AUDIT (not a real lead)
    email    audit@leonbuilds.org
    company  AUDIT — automated pipeline test, safe to delete
    via      quote-form

## What the server did with it

    LEAD {"ts":"2026-08-21T20:23:00.525Z","name":"PIPELINE AUDIT (not a real
    lead)","email":"audit@leonbuilds.org","company":"AUDIT — automated pipeline
    test, safe to delete","via":"quote-form","sourcePage":"/quote",
    "utmSource":"fbqun-hrq", ...}

    LEAD_NOT_EMAILED — need all of SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
    and LEAD_TO_EMAIL. Missing: SMTP_PASS. Until then this lead exists only in
    this log and in an ephemeral file that the next deploy erases.

## Verdict, stage by stage

| stage | state |
|---|---|
| page loads, language modal fires | **works** — `lang_prompt_shown`, then `lang_pick_en` |
| form renders and validates | **works** |
| analytics fires | **works** — `quote_form_start`, then `quote_form_submit` |
| POST /api/lead | **works** — full record, every field intact |
| attribution survives | **works** — `utmSource` carried through from the visit |
| email to leon@leonbuilds.org | **BLOCKED** — `SMTP_PASS` not set |
| lead survives a deploy | **NO** — see below |

## The finding that matters more than the missing password

The app's own log says it: *"this lead exists only in this log and in an
ephemeral file that the next deploy erases."*

leon-assist is on Render's **free tier, which has no persistent disk**.
`data/leads.jsonl` lives on a filesystem that is thrown away and recreated on
every deploy and on every spin-up after idle. The banner at the top of the
dashboard says the rest: *"Your free instance will spin down with inactivity."*

So the current behaviour for a real enquiry is:

1. captured correctly, with attribution
2. **not emailed** — `SMTP_PASS` missing
3. **erased** by the next deploy

Two deploys went out today. Anything submitted before them is gone, and there is
no way to recover it — the log window on the free plan does not reach back past
the restart.

`SMTP_PASS` is therefore not a nice-to-have that makes leads more convenient. It
is currently **the only thing that would turn a captured lead into a lead that
still exists tomorrow**, because the email is the only copy that leaves the
ephemeral disk.

## The second copy: the mailto handoff

`tools/build_pages.py` submits the form twice, deliberately:

```js
// fire-and-forget, errors swallowed
try{ fetch(API+'/api/lead',{...,keepalive:true}).catch(function(){}); }catch(e){}
var href=mailtoFor(d);
window.location.href=href;          // hands off to the visitor's mail app
```

and the confirmation screen then says:

> your email app just opened. **hit send and it comes straight to leon.**

That is a real second channel, and on a desktop with a configured mail client it
works. But it has three edges worth knowing:

- **It asks the visitor for one more action after they thought they were done.**
  Anyone who does not press send has, from Leon's side, silently vanished —
  while the server holds their details the whole time.
- **On mobile web and on webmail-only setups the mailto often opens nothing.**
  The visitor is then looking at a screen telling them their email app opened
  when it did not.
- **It goes to `leondragon3798@gmail.com`,** not to `leon@leonbuilds.org`. Two
  different destinations for the same enquiry.

None of that is broken exactly. But the mailto is the only path that reaches
Leon today, and it is the path with the most ways to fail silently. Once
`SMTP_PASS` is set, the server copy arrives regardless of what the visitor's
mail client does, and the mailto becomes a bonus rather than the mechanism.

## Fixed today

- **`leon@leonbuilds.org` did not exist.** Namecheap showed *"You haven't defined
  any Email Redirect yet"*. The MX records were Namecheap's defaults, present on
  every domain, which is what made it look configured.
- **`SMTP_USER`** set to `leondragon3798@gmail.com` on leon-assist. Send-only —
  it is an SMTP login, not an inbox anyone opens.
- **`LEAD_TO_EMAIL` changed to `splk3798@gmail.com`.** It was
  `leon@leonbuilds.org`, which meant every lead crossed a Namecheap forwarding
  hop to reach a real mailbox. Leon's assessment of that hop — *"never works
  efficiently 100%"* — matches how free forwarding actually behaves: it
  re-sends from a different server than the domain's SPF authorises, so a
  forwarded message is structurally more likely to be filtered or dropped than
  the same message delivered directly, and when it is dropped nobody is told.
  A lead is the wrong payload to route through a channel with silent losses.
  The hop is now out of the path entirely: Gmail SMTP → Gmail inbox, no relay.
- **The `leon` forwarder was kept, and repointed** to `splk3798@gmail.com`.
  Deleting it would make `leon@leonbuilds.org` bounce for anyone who guesses the
  address, which is worse than an unreliable forward. Nothing depends on it now
  — it is a courtesy catch, and it lands in the same single inbox as everything
  else.

Verified from the health endpoint rather than the dashboard:
`"leadEmailTo":"s***@gmail.com"`, `"leadEmailMissing":["SMTP_PASS"]`.

## Left for Leon

1. **`SMTP_PASS`** — a Gmail app password generated on `leondragon3798@gmail.com`.
   Then `curl -s https://leon-assist.onrender.com/api/health` should read
   `"leadEmail":true` and `"leadEmailMissing":[]`.

   Note that Apple Mail on the Mac currently **cannot send through Google
   either** — it failed with *"Cannot send message using the server Google"* on
   `splk3798@gmail.com` during this audit. Same root cause: Google no longer
   accepts a plain account password from a mail client. Worth fixing separately,
   because until it is, every `mailto:` link on every site dead-ends into an
   Outbox.
2. **Consider a persistent store for leads.** Even with email working, the only
   durable record is Leon's inbox. A Render disk, or appending each lead to a
   Google Sheet, would mean a lead survives an SMTP outage as well as a deploy.
3. **Decide the public contact address.** The site publishes
   `leondragon3798@gmail.com` in 41 built pages, and the quote form's `mailto:`
   goes there. Leads now arrive at `splk3798@gmail.com`, so as things stand
   there are two inboxes to watch: one for form submissions, one for anyone who
   clicks "email leon directly". Consolidating is a find-and-replace in
   `tools/build_pages.py` and `tools/lang_pages.py` plus a rebuild — held
   because it changes what customers see across the whole site, which is a
   brand call rather than a correctness fix.
4. **Delete the audit lead** from the inbox when it arrives, if it arrives.

## Incidental, and worth watching rather than concluding from

The same log window shows two visits arriving **from Facebook** with campaign
tags from the group posts: `/pt` with `utm=fbgrp-cb` referred by
`www.facebook.com`, and `/zh` with `utm=fbqun-brhr3` referred by
`m.facebook.com`. The mobile referrer on the second makes a real visitor more
likely than a self-click, but two hits is not a result — it is a reason to keep
the `?s=` tags on every posted link, which is what makes this measurable at all.

---

## Verdict — 2026-08-21, after four end-to-end runs

**Render does not permit outbound SMTP.** Final measurement, one attempt, after
a four-minute cooldown to rule out Google's connection throttling:

    LEAD_MAIL_FAILED Connection timeout — tried ports 587, 465

Both Gmail ports, over IPv4. Not the app password, not the port, and not IPv6.

### Three faults were stacked, and each one hid the next

1. **`leon@leonbuilds.org` had no forwarder.** MX records existed — Namecheap
   sets them on every domain — so it looked configured. Fixed by pointing leads
   at a real mailbox and taking the forwarding hop out of the path entirely.
2. **IPv6.** `connect ENETUNREACH 2607:f8b0:400e:c02::6c:587`. The container has
   no IPv6 route; Node resolved the AAAA record and tried it anyway. Two obvious
   fixes both failed — `family: 4` (nodemailer 9 does not pass it to
   `net.connect`) and `dns.setDefaultResultOrder('ipv4first')` (nodemailer does
   its own resolution and never calls `dns.lookup`). Only resolving to an IPv4
   literal and passing `tls.servername` for SNI removed it.
3. **Outbound SMTP is blocked.** Only visible once IPv6 stopped failing first.

Faults 1 and 2 were real and are fixed. Fault 3 is the platform's, and no
amount of configuration will move it.

### Fixed by sending over HTTPS instead

Port 443 works — every OpenAI call on this service proves it daily. Lead mail
now POSTs to Resend's API when `RESEND_API_KEY` is set, and falls back to SMTP
when it is not, so the code still works unchanged on a host that allows SMTP.

### Resend deployment — completed 2026-08-22

`RESEND_API_KEY` is now configured on leon-assist. Shallow health reports
provider `resend`, transport `https`, `leadEmailReady:true`, and no missing
delivery variables. One uniquely tagged submission passed all four checks with
receipt `lead_11c53d76-29d2-4177-9a9d-4bb81bacf09c`: HTTP 200, the matching
`LEAD` record, `LEAD_MAILED ... via https (resend)`, and the same receipt and
tag in the target Gmail inbox.

> **Superseding verification note:** the earlier unauthenticated deep-health
> command is intentionally retired. Deep health now requires `LEADS_KEY` in the
> `x-leads-key` header, and Resend reports `configured_unverified` with
> `leadEmailWorks:null` because a credential check cannot prove inbox delivery.
> After setting the key, shallow health should report provider `resend`, transport
> `https`, `leadEmailReady:true`, and no missing variables. The uniquely tagged
> end-to-end submission documented below is the only delivery proof.

> **Historical pre-fix condition:** leads were captured correctly but stored on
> an ephemeral disk while notification email was blocked, so a deploy could erase
> the only copy. The completed Resend test above resolves that delivery gap.

### What was never broken

The capture path. Every one of the four audit leads is in the log, complete,
with attribution intact. The form, the validation, the analytics events, the
`Reply-To` header and the UTM tracking have all worked from the first test.
Only the notification was failing.

### Method note, for the next person

Twice in this audit a single passing check would have shipped a broken build:
one build passed 1 of 6, another 1 of 8. But the correction has its own trap —
looping `?deep=1` to prove stability *caused* timeouts, because each call is a
real SMTP AUTH and repeated logins from a datacenter address are exactly what
Google throttles. A check that induces the failure it tests for is worse than
no check, because it reads as evidence.

The reliable test is the cheap one: post a single lead and read the log for
`LEAD_MAILED`.
