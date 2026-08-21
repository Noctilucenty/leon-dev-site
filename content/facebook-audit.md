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

### Still wrong — could not be fixed from here
| group | what is wrong | why it is stuck |
|---|---|---|
| 加州华人(美国) …生意广告 (pending) | 住在加州, 小修小改 $49, 完整网站 $1,200 | Facebook shows "Your review is still pending — admins review new participants before their content is published". His MEMBERSHIP is under review, and the pending post will not accept an edit. Save silently fails and the page reports unsaved changes. Delete and repost once the membership clears. |
| Profissionais Brasileiros nos EUA (pending) | "moro em Hayward (CA)", $49 · $400 · $1,200, old domain | Edit will not commit. Tried twice: the dialog accepts the new text, Save appears to succeed, and the post is unchanged on reload while the page reports unsaved changes. Same symptom as the group above, without the membership-review banner to explain it. |

**Both stuck posts have the same fix: delete the pending post and post again**, using
the corrected text in section 2 of this file. Deleting a pending post is one click
for Leon and costs nothing — it has not been published, so no reach is lost. Two of
the four edits DID save (Empresas, Empreendedores), and both only took on a second
attempt, so Facebook appears to accept roughly one edit per pending post and then
freeze it.

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

| group | members | result |
|---|---|---|
| 洛杉矶华人交流群 | 46.1K | posted in Chinese, **pending admin approval** |
| Comunidade Brasileira nos EUA | 28.6K | posted in Portuguese, **pending admin approval** |

Both went in with correct floors, no city, the live domain, the right-language
image, and WeChat on the Chinese one.

### Two older posts were DECLINED by admins
- 洛杉矶华人交流群: a restaurant-ordering pitch quoting 单页网站 $400, 网上点单 $2,000,
  小修小改 $49, and 我住在加州.
- Comunidade Brasileira nos EUA: one declined post, not opened.

Declines matter more than they look. An admin rejecting a post is a much
stronger signal than a post being ignored, and a pattern of them can get a
member removed. Both declined posts were the old-price, city-naming versions,
which is at least consistent with them reading as low-effort ads.

### Membership still under review in at least three groups
加州华人…生意广告 · 洛杉矶华人交流群 · and the group that froze the earlier edit.
Facebook shows "admins review new participants before their content is
published". While that banner is up, posts queue and **edits to queued posts
silently fail** — which is the whole explanation for the two edits that would
not save.

### Do not use "Add groups"
The composer offers posting to up to 9 groups at once. Not used, deliberately:
the same text across Chinese, Portuguese and English groups is both wrong for
most of those audiences and the exact shape Facebook's spam heuristics look
for. One group, one language, one post.

---

## STOP — the posts are getting him removed from groups (2026-08-21)

Checked every group he had posted to. The button on all of them now reads
**"Join group"**, which means he is no longer a member:

| group | members | status |
|---|---|---|
| 加州华人(美国)…生意广告 | 56.5K | REMOVED |
| 洛杉矶华人交流群 | 46.1K | REMOVED — within ~1h of tonight's post |
| Comunidade Brasileira nos EUA | 28.6K | REMOVED — within ~1h of tonight's post |
| Profissionais Brasileiros nos EUA | 22.7K | REMOVED, pending post gone with it |
| Empreendedores Brasileiros dos EUA | 8.7K | REMOVED |

Five for five. Roughly 162,000 members of reach, gone.

This also explains what looked like a Facebook bug earlier: the two pending
posts whose edits "silently failed" were not frozen by a platform quirk. He had
already been removed from those groups, so the posts were no longer his to edit.

### What this overturns
The earlier conclusion — "Marketplace bans services, so groups are the
compliant Facebook surface" — is wrong as executed. Marketplace rejects service
listings by policy; the groups reject them by moderator, and the penalty is
worse. Marketplace removes the listing. A group removes the person.

### What it does not prove
That group posting cannot work. What was posted was, in every case, a
price-list ad: a headline, a bulleted rate card, a link. That is what these
moderators remove, and it is also the least persuasive thing he could post. The
marketing plan said this in its own words and was not followed: the channel that
works is being introduced by someone the owner already trusts, or arriving with
the work already done for one specific business — not broadcasting a rate card
to 8,000 strangers.

### Do not, until this is thought through
- Do not post to another group.
- Do not rejoin a group he was removed from. Rejoining to post the same thing
  again is how a personal account gets restricted, and that account is also his
  Marketplace access, which is where his one paying client came from.
- Do not use the composer's post-to-9-groups feature, ever.

### Worth checking
Whether the personal account itself carries a warning or restriction. Five
group removals in a day is the kind of pattern Facebook's own systems act on,
and that would be a far more expensive problem than any of the above.
