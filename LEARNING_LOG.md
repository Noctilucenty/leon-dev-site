# Learning log — leonbuilds.org

Append-only. Newest at the bottom. Each entry says what was believed, what
turned out to be true, and how it was verified, because the entries that cost
the most here have all been confident readings of an unverified surface.

Evidence tiers: **[measured]** something was read back from the live system ·
**[reasoned]** a conclusion from evidence, not itself observed ·
**[assumed]** a working belief, not yet checked.

---

## 2026-08-21 · A UI affordance describes the session, not the account

**Believed:** Leon had been removed from five Facebook groups. Every group
rendered a "Join group" button, which only a non-member sees.

**True:** he is a member of 51 groups, all five included. **[measured]** —
`facebook.com/groups/joins` prints "All groups you've joined (51)" in its own
heading.

**Why it went wrong:** the browser had silently switched Facebook profiles to
the Curio Insight *Page*. A Page cannot join a group, so every group offered to
join. One unverified reading became a five-row table, a reach estimate, a
strategy reversal, and a recommendation that he stop posting.

**The check that catches it costs one navigation:** `facebook.com/me`. It now
runs first in any Facebook session for this repo, before reading anything and
before posting anything.

**General form:** "Join", "Follow", "Sign in" and "Subscribe" all render
identically for a logged-out viewer, a wrong profile, and a genuine non-member.
Whenever a control's state is the evidence, establish whose session is
rendering it first.

---

## 2026-08-21 · "Unsaved changes" is not evidence a save failed

**Believed:** two Facebook edits were "silently failing" — the dialog accepted
the text, Save appeared to work, and the page then warned about unsaved changes.
Recorded as a platform bug, with delete-and-repost as the fix.

**True:** every one of those edits had saved. **[measured]** — each post read
back with the corrected text from its group's own `my_pending_content` page.

**Why:** Facebook's composer keeps a `beforeunload` handler registered for a
while *after* a successful save. Navigating away then raises "Leave site?" and
the automation reports unsaved changes. It fires on saves that worked.

**Rule:** never take a save's own dialog as the verdict on the save. Re-read the
state from a different URL. Applied here to nine consecutive edits, every one
verified by reload.

**What a real failure looks like, for contrast:** the Edit button renders
greyed out, and the ⋯ menu returns "We can't access this post, it may have been
deleted." Two pending posts are in that state — the post object is gone
server-side while the queue still lists it. Nobody can edit those; they can only
be deleted and reposted.

---

## 2026-08-21 · An inventory built from memory is not an inventory

**Believed:** the stale posts were concentrated in the six groups Leon
remembered posting to, and all six had been handled.

**True:** nine posts across nine groups were live with old prices, plus two more
unreachable in pending queues. **[measured]** —
`facebook.com/me/allactivity/?category_key=GROUPPOSTS` lists every group post
ever made, with full text, on one page.

**Rule:** when a platform offers an activity log, read the log. Group-by-group
checking samples what someone remembers, and the whole reason stale content is
a problem is that nobody remembers it.

---

## 2026-08-21 · Never put a figure on an image that leaves the repo

**Measured:** four live posts carried a picture of the old rate card — twelve
prices rendered large, above the caption, every one wrong against
`tools/check_prices.py`. An older variant was worse ($49 small fixes, $4,500
apps). Editing the caption does nothing about it, and the image is what gets
read first.

**Reasoned:** a price in text is regenerable — `tools/make_posts.py` rebuilds
every post from `FLOORS`, so a reprice is one command and a repaste. A price
baked into a PNG is a manual hunt through every surface it was ever posted to,
and it is silent until a customer finds it.

`tools/make_listing_images.py` already carried this rule in a comment ("names
only — no figures on listing creative"). This is the evidence for it. The
current `fb_*_2build.png` images list service names and no figures, and were
used as the replacements.

---

## 2026-08-21 · Where a rate card is allowed to land

**Measured**, across every group Leon has posted to:

- The one group that **published** him is 美国洛杉矶广告群-海外华人产品广告
  SmallBusiness中小企业、本地商家 — a group that exists for business ads.
- The two that **declined** him are general community groups (46K Chinese
  social, 28K Brazilian community). Four declines between them.
- Correct floors, no city, live domain and a right-language image did **not**
  prevent the declines. The copy was not the variable.

**Reasoned:** the sortable variable is the group, not the post. A price list
lands where price lists are the point and is declined where they are not. Post
rate cards only to groups that describe themselves as ad / classified /
business groups; bring something other than a rate card to community groups.

**Measured, and worth separating from the above:** a decline costs the post, not
the membership. After four declines across two groups he is still a member of
both, and of all 51.

---

## 2026-08-21 · Marketplace re-attaches the city no matter what the copy says

**Measured:** two group posts are Marketplace listings cross-posted into groups.
Their card renders "$300 · HAYWARD, CA". The city appears in no copy anywhere —
it is the listing's location field, which Marketplace requires and which has no
nationwide option.

**Reasoned:** the no-city rule can be enforced in everything this repo
generates, and cannot be enforced on a Marketplace card. The only lever is
moving the listing to a different city, which trades one geographic distortion
for another and changes who sees it. Left as Leon's decision rather than
silently changed.
