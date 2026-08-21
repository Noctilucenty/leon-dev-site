# Facebook group post audit

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

