# Facebook group post audit — historical narrative

> **Current state lives in `content/publication-ledger.csv`.** This file is kept
> intact as an append-only account of what was believed, corrected, and learned.
> It contains retracted and superseded sections by design; do not use an early
> table here as a publishing dashboard. Validate the current ledger with
> `python3 tools/check_publication_ledger.py`. The companion
> `content/facebook-group-coverage.csv` records all 51 joined groups, including
> the 30 where the activity-log sweep found no post.

Every group post predates the reprice, the domain move to leonbuilds.org, and
the no-city rule. They all carry some combination of: prices from the old list
($49 small fixes, $400 "single-page site", $1,200 "full site", $2,000 online
ordering, $4,500 app), a link to leonkelvinli.onrender.com, and a location —
"moro em Hayward (CA)" or 住在加州.

The prices are the damaging part. A live post quoting $2,000 for online
ordering, against $600 on the site, reads as either a bait or a mistake to
anyone who checks both.

### Fixed
| group | what was wrong | state |
|---|---|---|
| 美国洛杉矶广告群 (688, **live**) | $49 · $400 · $1,200 · $2,000 · $4,500, 住在加州, old domain | corrected + WeChat added |
| Empresas Brasileiras nos EUA (6.8K, pending) | old prices, old domain | corrected, "Sou brasileiro" kept |
| Empreendedores Brasileiros dos EUA (8.7K, pending) | "moro em Hayward (CA)", $49/$400/$1,200, old domain | corrected, "Sou brasileiro" kept |

### Was reported stuck — it was not
~~Two pending posts (加州华人…生意广告, Profissionais Brasileiros nos EUA) refused
edits: the dialog accepted the new text, Save appeared to succeed, and the post
was unchanged on reload.~~

**Both edits had saved.** Re-read later from the correct profile, every one of
these posts carries the corrected text — current floors, no city,
leonbuilds.org. What looked like a save failure was a stale render of a page
belonging to a different Facebook profile. There was no edit bug, nothing needs
deleting, and nothing needs reposting. See the retraction at the end of this
file.

### Checked, nothing to fix
洛杉矶华人交流群 (46.1K) · Comunidade Brasileira nos EUA · 美国华人圈 · 美国华人群 ·
Brasileiros Nos EUA · Brasileiros Na Bay-Area · 巴西🇧🇷华人交流群 · 巴西华人 —
no posts at all, in any state.

Useful shape: the stale posts were NOT spread across 51 groups. They were
concentrated in the six groups he actually posted to, and every one of those six
was wrong. The other groups are simply empty — which makes them places to post
rather than places to fix.

### Not yet checked
巴西华人群 · 🇧🇷 Brasileiros em SF e Bay Area · 湾区华人群 · 湾区生活资讯 · 湾区租房二手 ·
ANUNCIOS CLASSIFICADOS BRASILEIROS · Gringos Buy & Sell Sao Paulo. Mostly local
Bay-Area and classifieds groups, and none showed recent activity in the joined
list. Facebook's group list stopped rendering before their IDs could be read.

The check for each is two URLs:
  facebook.com/groups/<id>/my_posted_content    (live — fix these first)
  facebook.com/groups/<id>/my_pending_content   (queued)

---

## Posted where there was nothing — 2026-08-21

| group | members | posted | outcome |
|---|---|---|---|
| 洛杉矶华人交流群 | 46.1K | Chinese | **DECLINED by admins**, within ~1h |
| Comunidade Brasileira nos EUA | 28.6K | Portuguese | **DECLINED by admins**, within ~1h |

Both went in with correct floors, no city, the live domain, the right-language
image, and WeChat on the Chinese one — and both were still declined. The copy
was not the variable. Both of these are general community groups; the one group
that published him is an ads group. See the retraction at the end of this file.

### Two older posts were DECLINED by admins
- 洛杉矶华人交流群: a restaurant-ordering pitch quoting 单页网站 $400, 网上点单 $2,000,
  小修小改 $49, and 我住在加州.
- Comunidade Brasileira nos EUA: one declined post, not opened.

Declines matter more than they look — an admin rejecting a post is a much
stronger signal than a post being ignored. But a decline costs the post, not
the membership: after four of them across two groups he is still a member of
both, and of all 51.

### Membership still under review in one group
加州华人…生意广告 still shows "admins review new participants before their content
is published". That banner explains why a post there queues instead of going
live. It does **not** stop edits — the claim that it froze them was wrong, and
is retracted at the end of this file.

### Do not use "Add groups"
The composer offers posting to up to 9 groups at once. Not used, deliberately:
the same text across Chinese, Portuguese and English groups is both wrong for
most of those audiences and the exact shape Facebook's spam heuristics look
for. One group, one language, one post.

---

## RETRACTED — he was never removed from any group (2026-08-21)

**The section that stood here was wrong, and it was wrong in the most expensive
direction: it told him to stop.** It reported that all five groups he had posted
to now showed a "Join group" button, concluded he had been removed from every
one of them, and recommended he post to no further groups and rejoin none.

None of that happened. He is a member of **51 groups**, which is what
`facebook.com/groups/joins` says in its own heading, and all five of the
supposedly-lost groups are in that list.

### How the error was produced
The browser had silently switched Facebook profiles partway through the sweep,
from Leon Kelvin Li to the **Curio Insight Page**. A Page cannot be a member of
a group, so every group rendered "Join group" for it. I read that button as a
membership state without checking whose session was rendering it, and then built
a five-row table, a reach estimate, a strategy reversal and a stop-work
recommendation on top of one unverified reading.

The check that would have caught it takes one navigation: `facebook.com/me`.
It is now the first step of any Facebook session in this repo, before anything
is read and before anything is posted.

**Rule, generally: a UI affordance is evidence about the current session, not
about the account.** "Join group", "Follow", "Sign in" all render the same way
for a logged-out viewer, a wrong profile, and a genuine non-member.

### Also retracted
That section explained the two pending posts whose edits "silently failed" by
saying he had been removed and the posts were no longer his. Both edits had in
fact **saved correctly**. Every one of those posts is sitting in its group's
pending queue right now carrying the corrected text — right prices, no city,
leonbuilds.org. There was no Facebook edit bug and there is nothing to redo.

### Verified state, every group he has posted to
Read from each group's own `my_posted_content` / `my_pending_content` /
`my_declined_content` page while signed in as Leon Kelvin Li.

| group | members | membership | his content |
|---|---|---|---|
| 美国洛杉矶广告群 (ads group) | 688 | member | **Published — live**, corrected text |
| 加州华人(美国)…生意广告 | 56.5K | member | Pending ×1, corrected text; membership still under review |
| Profissionais Brasileiros nos EUA | 22.7K | member | Pending ×1, corrected text |
| Empreendedores Brasileiros dos EUA | 8.7K | member | Pending ×1, corrected text |
| 洛杉矶华人交流群 | 46.1K | member | **Declined ×2** — including the post made tonight |
| Comunidade Brasileira nos EUA | 28.6K | member | **Declined ×2** — including the post made tonight |

### The real finding, which the false one buried
Posts are being **declined by moderators**, not punished. Nothing happened to
the account or the membership. And the declines are not random:

- The one group that **published** him is the one whose name is literally
  「海外华人产品广告 SmallBusiness中小企业、本地商家」 — a group that exists for
  business ads.
- The two that **declined** him are general community groups: a 46K Chinese
  social group and a 28K Brazilian community group. A rate card is off-topic
  there whoever posts it.
- The three still **pending** are moderated groups where his membership itself
  is new and under review.

So the sortable variable is the group, not the copy. A price-list post lands
where price-list posts are the point and is declined where they are not. That is
a targeting result, and it is cheap to act on: post the rate card only to
groups that advertise themselves as ad/classified/business groups, and bring
something other than a rate card to community groups.

### What still stands from the retracted section
Two things in it were right for reasons that survive the retraction:

- **Never use the composer's post-to-9-groups feature.** One text across
  Chinese, Portuguese and English audiences is wrong for most of them and is
  the exact shape spam heuristics look for.
- **A rate card is the least persuasive thing he can post.** Two declines out
  of two community groups is weak evidence, but the marketing plan already said
  the channel that works is a referral from someone the owner trusts, or work
  already done for one specific business. That was true before tonight.

---

## The full sweep, done properly — 2026-08-21

The earlier passes checked the six groups he remembered posting to. The complete
list came from one page nobody had opened: **`facebook.com/me/allactivity/?category_key=GROUPPOSTS`**,
which lists every group post he has ever made, with its full text. It is the
only reliable inventory; the group-by-group check misses whatever he forgot.

It found **nine live posts with stale prices**, not the three the "Fixed" table
above claimed. The earlier line — "the stale posts were NOT spread across 51
groups, they were concentrated in the six he actually posted to" — was wrong,
and wrong because the sample was his memory rather than the log.

### The prices that were live
Old figures against the current floors: small fixes $49 (now $75) · single-page
site $400 (now $300, and $400 now means the monthly retainer) · full site $1,200
(now $625) · online ordering $2,000 (now $600) · website $325 (now $300) ·
app/system $2,500 (now $3,500 for an app, $1,500 for custom software).

Most were quoted **higher** than today, which reads as disorganised rather than
as a bait. `$49 → $75` is the one that runs the wrong way, and it is exactly
what rule 4 of `tools/check_prices.py` exists to stop on the site.

### Fixed, verified after saving
| group | was wrong | now |
|---|---|---|
| 美国华人圈 | 住在加州, $49, $1,200, old domain | **published**, corrected |
| 巴西🇧🇷华人交流群 | 人在美国加州, $49/$400/$1,200/$2,000 | corrected, queued for re-approval |
| 巴西华人群 \| Overseas Chinese In Brazil | 人在美国加州, $49/$400/$1,200 | **published**, corrected |
| 巴西华人 | 人在美国加州, $49/$400/$1,200 | **published**, corrected |
| Hayward, CA community | "living here in Hayward", $325/$2,500, **stale rate-card image** | corrected + image replaced, queued |
| Hayward Market Place | "I live here in Hayward", $325/$2,500, **stale rate-card image** | **published**, corrected + image replaced |
| Brasileiros Nos EUA | "moro em Hayward (CA)", $400/$2,000/$49 | corrected |
| 🇧🇷 Brasileiros em SF e Bay Area | "moro em Hayward", $325/$2,500, **stale rate-card image** | corrected + image replaced, still pending |
| Brasileiros Na Bay-Area | "moro em Hayward", $325/$2,500 | corrected + image replaced, still pending |

Nine for nine. Every one now carries the floors from `tools/check_prices.py`,
no place name, and leonbuilds.org.

### The image was worse than the text
Four of those posts carried a picture of the **old rate card** — twelve prices
rendered large, above the fold, every one of them wrong: business websites
$325, online ordering $2,000, ios & android apps $2,500, booking & scheduling
$750, ai chatbots $500. An older variant was worse still ($49 small fixes,
$4,500 apps).

Editing the text does nothing about that, and nobody reads the caption before
the image. They were replaced with `assets/listings/fb_*_2build.png`, which
lists the service names and **no figures at all** — `tools/make_listing_images.py`
already decided that ("names only — no figures on listing creative"), and this
is why that decision was right. A priced image is a price that cannot be
regenerated; it has to be hunted down in every group it was ever posted to.

**Rule: never put a figure on any image that leaves this repo.** The floors move;
the picture does not.

### Facebook mechanics worth not relearning
- **The "Leave site? — unsaved changes" dialog fires after a *successful* save.**
  It is not evidence of anything. Verify by reloading the group's own
  `my_posted_content` / `my_pending_content`, never by trusting that dialog.
  This false signal is most of what produced the retracted report below.
- **Some pending posts are server-side ghosts.** Their Edit button is greyed
  out, and the ⋯ menu returns *"We can't access this post, it may have been
  deleted."* Two are in this state (see below). That — not a membership review,
  not a platform bug — is what a genuinely un-editable post looks like.
- **Editing a *published* post can send it back to moderation.** Some groups
  warn in the menu: "Edits will be submitted for admin approval". Correcting a
  live post there costs its current visibility. Worth it for a wrong price;
  not worth it for a typo.
- **Opening the ⋯ menu and clicking its item must happen in one batch**, with a
  screenshot between them for timing. Any `find`/`read_page` in between
  dismisses the menu.
- Attached photos are removable in the edit dialog (an X on the thumbnail), and
  a replacement uploads through the dialog's hidden `input[type=file]`.

### Two ghosts — Leon has to delete and repost
Both are **pending**, so nothing was ever published and no reach is lost.
Neither can be edited by anyone; the post object is gone server-side.

> **No-delete correction — 2026-08-22:** preserve both pending records. Do not
> follow the deletion/repost instruction below. The canonical ledger records
> `retain_no_delete_edit_unavailable`; only revisit them if Facebook later makes
> non-destructive editing possible and the group rules still permit the post.

| group | what it still says |
|---|---|
| 美国华人群 | 住在加州 · 小修小改 $49 · 单页网站 $400 · 完整网站 $1,200 · 网上点单 $2,000 |
| ANUNCIOS CLASSIFICADOS BRASILEIROS … | $325 site / $2,500 app, plus the worst stale rate-card image |

Fix for each: open `facebook.com/groups/<id>/my_pending_content`, click
**Delete**, then post the corrected copy from `content/posts.md`. One click each.
Both groups also show **Removed · 1** — a separate post a moderator took down.

### Not verified
One photo-only post in **Castro Valley Hayward San Leandro & San Lorenzo
COMMUNITY HUB** (private, 2026-08-16). It very likely carries the same stale
rate-card image. The group did not surface in the joined-groups list far enough
to read its id; the check is `facebook.com/groups/<id>/my_posted_content`.

### Marketplace puts the city back, and there is no setting to stop it
Two group posts are Marketplace listings cross-posted into groups (湾区华人群,
湾区生活资讯). Their card renders **"$300 · HAYWARD, CA"**. The city is not in
any copy — it is the listing's location field, which Marketplace requires and
which has no "nationwide" option. The only lever is to move the listing to a
different city, which changes who sees it locally. Left alone deliberately;
this is Leon's call, not a bug to fix.

### Marketplace listing state, for the record
Four service listings are flagged **"This listing may go against our rules for
selling"** — expected, since Commerce Policies ban services. Two are still
active. Clicks so far: PT $300 listing **14**, old EN $49/$199 listing 9, new EN
$300 listing 4, old $0/$5 listing 4, ES $300 listing 2, ZH $300 listing 2.

The two **old** listings are still up and still quoting `$49/$199` and `$0/$5` —
the "$0" being the exact thing Leon said makes a listing read as spam. They
predate the reprice and should come down. Not deleted here: that is his to do.

> **No-delete correction — 2026-08-22:** retain these listings and their history.
> Do not use the sentence above as an action item. Their current policy-risk and
> stale-copy states are tracked in `content/publication-ledger.csv`; the repo no
> longer generates Marketplace service-listing copy.
