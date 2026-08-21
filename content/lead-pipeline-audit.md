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

## Fixed today, before the audit ran

- **`leon@leonbuilds.org` did not exist.** Namecheap showed *"You haven't defined
  any Email Redirect yet"*. The MX records were Namecheap's defaults, present on
  every domain, which is what made it look configured. Created `leon` →
  `lkelvi3798@gmail.com` and verified after a reload.
- **`SMTP_USER`** set to `leondragon3798@gmail.com` on leon-assist. Deliberately
  a different account from the forward target, so Gmail cannot file the message
  as one Leon sent to himself.

## Left for Leon

1. **`SMTP_PASS`** — a Gmail app password generated on `leondragon3798@gmail.com`.
   Then `curl -s https://leon-assist.onrender.com/api/health` should read
   `"leadEmail":true` and `"leadEmailMissing":[]`.
2. **Consider a persistent store for leads.** Even with email working, the only
   durable record is Leon's inbox. A Render disk, or appending each lead to a
   Google Sheet, would mean a lead survives an SMTP outage as well as a deploy.
3. **Delete the audit lead** from the inbox when it arrives, if it arrives.

## Incidental, and worth watching rather than concluding from

The same log window shows two visits arriving **from Facebook** with campaign
tags from the group posts: `/pt` with `utm=fbgrp-cb` referred by
`www.facebook.com`, and `/zh` with `utm=fbqun-brhr3` referred by
`m.facebook.com`. The mobile referrer on the second makes a real visitor more
likely than a self-click, but two hits is not a result — it is a reason to keep
the `?s=` tags on every posted link, which is what makes this measurable at all.
