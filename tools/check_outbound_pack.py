#!/usr/bin/env python3
"""Validate the offline organic/outbound execution pack.

This checker is intentionally read-only and has no network dependencies. It
keeps every versioned asset visibly unsent, prevents price drift, validates the
30-day/three-wedge/four-touch structure, and refuses real prospect data in the
tracked CRM and attribution examples.

    python3 tools/check_outbound_pack.py
"""

import ast
import csv
import io
import os
import re
import sys
from urllib.parse import parse_qs, urlparse


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "content", "outbound")

MARKDOWN = {
    "README.md": (
        "## Safety contract",
        "## Canonical offer and price snapshot",
        "## Human preflight before any later use",
    ),
    "10-day-bakeoff.md": (
        "## Objective",
        "## Wedge hypotheses",
        "## Decision",
    ),
    "30-day-calendar.md": (
        "## Daily operating block",
        "## Calendar",
        "## Weekly scoreboard",
    ),
    "outreach-scripts.md": (
        "## Warm introduction requests",
        "## Compliance footer for every cold commercial email",
        "## Reply handling",
    ),
    "community-and-partners.md": (
        "## Community rules",
        "## Partner targets",
        "## Permission-based handoff",
    ),
    "app-development-community-drafts.md": (
        "## Identity and proof boundary",
        "## Manual current-rules check before any use",
        "## Comment-first operating rule",
        "## Post drafts",
        "## Tracked source URL bank",
        "## Human review record",
    ),
    "qualification-and-stop-rules.md": (
        "## Fifteen-minute call structure",
        "## Individual-contact stop rules",
        "## Capacity gate",
    ),
}

CRM_FIELDS = (
    "record_status", "lead_id", "created_date", "contact_name", "organization",
    "role", "email", "phone", "website", "city", "language", "wedge", "source",
    "source_detail", "source_tag", "utm_source", "utm_medium", "utm_campaign",
    "utm_term", "utm_content", "gclid", "gbraid", "wbraid", "fbclid", "msclkid",
    "observed_problem", "personalization_note", "permission_basis", "touch_1_date", "touch_1_status",
    "touch_2_date", "touch_2_status", "touch_3_date", "touch_3_status",
    "touch_4_date", "touch_4_status", "last_response_date", "response_state",
    "booking_state", "meeting_date", "show_state", "qualified_score",
    "qualification_state", "proposal_state", "outcome", "do_not_contact",
    "opt_out_date", "next_action", "next_action_date", "notes",
)

TAG_FIELDS = (
    "record_status", "channel", "wedge", "language", "variant", "source_tag",
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "example_url", "notes",
)

TAG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){3,5}$")
DOLLARS = re.compile(r"\$([0-9][0-9,]*(?:\.[0-9]+)?)")
FLOOR_MARKER = re.compile(r"<!-- floor: ([a-z-]+(?: [a-z-]+)*)=([0-9]+) -->")
CAMPAIGN_ASSETS = (
    "ad_01_contractor_after_hours.png",
    "ad_02_contractor_flow.png",
    "ad_03_auto_estimates.png",
    "ad_04_restaurant_direct.png",
    "ad_05_founder_direct.png",
    "ad_06_lead_leak_review.png",
)


def load_floors():
    path = os.path.join(ROOT, "tools", "check_prices.py")
    with io.open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            getattr(target, "id", None) == "FLOORS" for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError("tools/check_prices.py no longer defines a literal FLOORS dict")


def read_markdown(errors):
    content = {}
    for name, headings in MARKDOWN.items():
        path = os.path.join(PACK, name)
        if not os.path.isfile(path):
            errors.append(f"missing pack document: content/outbound/{name}")
            continue
        with io.open(path, encoding="utf-8") as fh:
            text = fh.read()
        content[name] = text
        lead = "\n".join(text.splitlines()[:12])
        if "Status: DRAFT — UNSENT" not in lead:
            errors.append(f"{name}: top-of-file DRAFT — UNSENT marker is required")
        if "NO SEND AUTHORIZATION." not in lead:
            errors.append(f"{name}: top-of-file NO SEND AUTHORIZATION marker is required")
        for heading in headings:
            if heading not in text:
                errors.append(f"{name}: missing required section {heading!r}")
    return content


def check_structure(content, errors):
    bakeoff = content.get("10-day-bakeoff.md", "")
    wedges = set(re.findall(r"<!-- wedge: ([a-z-]+) -->", bakeoff))
    expected_wedges = {"home-services", "auto-repair", "restaurant-food"}
    if wedges != expected_wedges:
        errors.append(
            "10-day-bakeoff.md: wedge markers must be exactly "
            + ", ".join(sorted(expected_wedges))
        )

    calendar = content.get("30-day-calendar.md", "")
    days = [int(value) for value in re.findall(r"^\| D([0-9]{2}) \|", calendar, re.M)]
    if days != list(range(1, 31)):
        errors.append("30-day-calendar.md: calendar must contain D01 through D30 exactly once")

    scripts = content.get("outreach-scripts.md", "")
    warm = set(re.findall(r"<!-- warm-script: ([a-z]{2}) -->", scripts))
    if warm != {"en", "es", "pt", "zh"}:
        errors.append("outreach-scripts.md: warm scripts must cover en, es, pt, and zh")
    sequences = set(re.findall(r"<!-- cold-sequence: ([a-z-]+) -->", scripts))
    expected_sequences = {"home-services", "auto-repair", "restaurant-food"}
    if sequences != expected_sequences:
        errors.append("outreach-scripts.md: all three cold sequence markers are required")
    touches = re.findall(r"<!-- touch: ([a-z-]+):([1-4]) -->", scripts)
    expected_touches = {(sequence, str(touch)) for sequence in expected_sequences for touch in range(1, 5)}
    if set(touches) != expected_touches or len(touches) != 12:
        errors.append("outreach-scripts.md: each wedge requires Touch 1 through Touch 4 exactly once")
    if scripts.count("[APPEND THE COMPLIANCE FOOTER BEFORE ANY SEPARATELY AUTHORIZED SEND.]") != 12:
        errors.append("outreach-scripts.md: every cold touch must require the compliance footer")
    for required in (
        "[VALID POSTAL ADDRESS]",
        "one-to-one business outreach message",
        "reply “no thanks”",
    ):
        if required not in scripts:
            errors.append(f"outreach-scripts.md: compliance footer missing {required!r}")

    community = content.get("community-and-partners.md", "")
    posts = set(re.findall(r"<!-- community-post: ([a-z-]+):([a-z]{2}) -->", community))
    expected_posts = {(kind, lang) for kind in ("process-map", "clinic") for lang in ("en", "es", "pt", "zh")}
    if posts != expected_posts:
        errors.append("community-and-partners.md: both post types must cover en, es, pt, and zh")

    app_pack = content.get("app-development-community-drafts.md", "")
    expected_app_drafts = {
        "app-readiness", "mvp-scope", "build-or-buy", "app-rescue",
        "classified-offer",
    }
    app_drafts = re.findall(r"<!-- app-community-draft: ([a-z-]+) -->", app_pack)
    if set(app_drafts) != expected_app_drafts or len(app_drafts) != 5:
        errors.append(
            "app-development-community-drafts.md: exactly five distinct app draft markers are required"
        )
    app_sources = re.findall(r"<!-- app-source: ([a-z-]+) -->", app_pack)
    if set(app_sources) != expected_app_drafts or len(app_sources) != 5:
        errors.append(
            "app-development-community-drafts.md: every app draft needs one distinct source marker"
        )
    for required in (
        "PRIVATE REVIEW ONLY — NOTHING HAS BEEN POSTED",
        "Never use a Curio account",
        "No automation, bulk cross-posting",
        "Leon Builds",
        "Leon Kelvin Li",
        "shipped a live App Store product",
        "[RULES URL + YYYY-MM-DD]",
        "[IF CURRENT RULES REQUIRE A RATE OR BUDGET FORMAT: DO NOT POST UNTIL LEON APPROVES THAT FIELD]",
        "r/smallbusiness",
        "r/startups",
    ):
        if required not in app_pack:
            errors.append(
                "app-development-community-drafts.md: missing required safety or proof text "
                + repr(required)
            )

    draft_only = app_pack.split("## Post drafts", 1)[-1].split("## Tracked source URL bank", 1)[0]
    if re.search(r"\bcurio\b", draft_only, re.I):
        errors.append(
            "app-development-community-drafts.md: post copy must not use Curio branding or identity"
        )
    for prohibited in ("guaranteed downloads", "guaranteed revenue", "mass DM", "bulk post"):
        if prohibited.lower() in draft_only.lower():
            errors.append(
                f"app-development-community-drafts.md: post copy contains prohibited phrase {prohibited!r}"
            )

    app_urls = re.findall(
        r"https://leonbuilds\.org/services/mobile-apps\?[^\s`]+", app_pack
    )
    if len(app_urls) != 5:
        errors.append(
            "app-development-community-drafts.md: exactly five mobile-app source URL templates are required"
        )
    seen_terms = set()
    seen_content = set()
    for value in app_urls:
        query = parse_qs(urlparse(value).query)
        if query.get("utm_source") != ["[community_slug]"]:
            errors.append("app-development source URL must retain [community_slug]")
        if query.get("utm_medium") != ["community"]:
            errors.append("app-development source URL must use utm_medium=community")
        if query.get("utm_campaign") != ["app-services-review-v1"]:
            errors.append("app-development source URL has an unexpected campaign")
        term = query.get("utm_term", [""])[0]
        content_value = query.get("utm_content", [""])[0]
        if not term or not content_value:
            errors.append("app-development source URL is missing utm_term or utm_content")
        seen_terms.add(term)
        seen_content.add(content_value)
    if len(seen_terms) != 5 or len(seen_content) != 5:
        errors.append(
            "app-development-community-drafts.md: source templates need distinct terms and content values"
        )

    readme = content.get("README.md", "")
    social_source_path = os.path.join(ROOT, "tools", "make_social.py")
    if not os.path.isfile(social_source_path):
        errors.append("tools/make_social.py: canonical campaign asset generator is missing")
        social_source = ""
    else:
        with io.open(social_source_path, encoding="utf-8") as fh:
            social_source = fh.read()
    for asset in CAMPAIGN_ASSETS:
        relative = f"assets/social/{asset}"
        if relative not in readme:
            errors.append(f"README.md: campaign asset map missing {relative}")
        if asset not in social_source:
            errors.append(f"tools/make_social.py: campaign asset source missing {asset}")
        if not os.path.isfile(os.path.join(ROOT, relative)):
            errors.append(f"missing generated campaign asset: {relative}")


def check_prices(content, errors):
    floors = load_floors()
    readme = content.get("README.md", "")
    markers = {name: int(value) for name, value in FLOOR_MARKER.findall(readme)}
    if markers != floors:
        missing = sorted(set(floors) - set(markers))
        extra = sorted(set(markers) - set(floors))
        changed = sorted(name for name in set(floors) & set(markers) if floors[name] != markers[name])
        errors.append(
            "README.md: canonical floor snapshot differs from tools/check_prices.py "
            f"(missing={missing}, extra={extra}, changed={changed})"
        )
    allowed = set(floors.values())
    for value in DOLLARS.findall(readme):
        number = float(value.replace(",", ""))
        number = int(number) if number.is_integer() else number
        if number not in allowed:
            errors.append(f"README.md: ${value} is not a canonical published floor")
    for name, text in content.items():
        if name == "README.md":
            continue
        amounts = DOLLARS.findall(text)
        if amounts:
            errors.append(
                f"{name}: outreach execution copy must stay price-free; found "
                + ", ".join(f"${value}" for value in sorted(set(amounts)))
            )


def read_csv(path, expected_fields, errors):
    if not os.path.isfile(path):
        errors.append(f"missing pack CSV: {os.path.relpath(path, ROOT)}")
        return []
    with io.open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != expected_fields:
            errors.append(
                f"{os.path.basename(path)}: schema changed; expected exact checked header"
            )
        rows = list(reader)
    if not rows:
        errors.append(f"{os.path.basename(path)}: at least one synthetic example row is required")
    return rows


def check_source_tags(errors):
    path = os.path.join(PACK, "source-tag-schema.csv")
    rows = read_csv(path, TAG_FIELDS, errors)
    tags = set()
    allowed_channels = {
        "direct_email", "warm_intro", "partner_referral", "facebook_group",
        "linkedin", "event", "nextdoor", "yelp",
    }
    allowed_wedges = {"home_services", "auto_repair", "restaurant_food"}
    allowed_languages = {"en", "es", "pt", "zh"}
    for line_no, row in enumerate(rows, start=2):
        prefix = f"source-tag-schema.csv line {line_no}"
        if row.get("record_status") != "synthetic_example":
            errors.append(f"{prefix}: only synthetic_example rows may be committed")
        if row.get("channel") not in allowed_channels:
            errors.append(f"{prefix}: unknown channel")
        if row.get("wedge") not in allowed_wedges:
            errors.append(f"{prefix}: unknown wedge")
        if row.get("language") not in allowed_languages:
            errors.append(f"{prefix}: unknown language")
        tag = row.get("source_tag", "")
        if not TAG_RE.fullmatch(tag):
            errors.append(f"{prefix}: invalid lowercase source tag {tag!r}")
        if tag in tags:
            errors.append(f"{prefix}: duplicate source tag {tag!r}")
        tags.add(tag)
        parsed = urlparse(row.get("example_url", ""))
        query = parse_qs(parsed.query)
        if parsed.scheme != "https" or parsed.netloc != "leonbuilds.org":
            errors.append(f"{prefix}: example_url must use https://leonbuilds.org")
        if "s" in query:
            errors.append(f"{prefix}: new full-UTM examples must omit the legacy s alias")
        for field in ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"):
            if query.get(field) != [row.get(field, "")]:
                errors.append(f"{prefix}: URL {field} does not match row")
        if row.get("utm_term") != row.get("wedge"):
            errors.append(f"{prefix}: utm_term must carry the tested wedge")
        if row.get("utm_content") != tag:
            errors.append(f"{prefix}: utm_content must carry the exact source_tag")
        if row.get("utm_campaign") != "cal30d-bakeoff-v1":
            errors.append(f"{prefix}: unexpected campaign name")
        if "SYNTHETIC" not in row.get("notes", ""):
            errors.append(f"{prefix}: synthetic example must say SYNTHETIC in notes")
    return tags


def check_crm(source_tags, errors):
    path = os.path.join(PACK, "crm-template.csv")
    rows = read_csv(path, CRM_FIELDS, errors)
    if len(rows) != 1:
        errors.append("crm-template.csv: keep exactly one synthetic example row in version control")
    for line_no, row in enumerate(rows, start=2):
        prefix = f"crm-template.csv line {line_no}"
        if row.get("record_status") != "synthetic_example":
            errors.append(f"{prefix}: real CRM records must never be committed")
        if not row.get("lead_id", "").startswith("SYN-"):
            errors.append(f"{prefix}: lead_id must be visibly synthetic")
        for field in ("contact_name", "organization", "city"):
            if not row.get(field, "").startswith("SYNTHETIC"):
                errors.append(f"{prefix}: {field} must start with SYNTHETIC")
        email = row.get("email", "")
        if email and not email.lower().endswith("@example.com"):
            errors.append(f"{prefix}: synthetic email must use example.com")
        if row.get("phone"):
            errors.append(f"{prefix}: synthetic phone must remain blank")
        parsed = urlparse(row.get("website", ""))
        if parsed.netloc != "example.com":
            errors.append(f"{prefix}: synthetic website must use example.com")
        if row.get("source_tag") not in source_tags:
            errors.append(f"{prefix}: source_tag is absent from source-tag-schema.csv")
        if row.get("utm_content") != row.get("source_tag"):
            errors.append(f"{prefix}: utm_content must equal source_tag")
        if row.get("utm_term") != row.get("wedge"):
            errors.append(f"{prefix}: utm_term must equal wedge")
        for field in ("gclid", "gbraid", "wbraid", "fbclid", "msclkid"):
            if row.get(field):
                errors.append(f"{prefix}: synthetic organic sample must not invent {field}")
        if row.get("permission_basis") != "synthetic_example":
            errors.append(f"{prefix}: permission_basis must remain synthetic_example")
        if row.get("do_not_contact") not in {"true", "false"}:
            errors.append(f"{prefix}: do_not_contact must be true or false")
        if "SYNTHETIC SAMPLE ONLY" not in row.get("notes", ""):
            errors.append(f"{prefix}: notes must identify the synthetic sample")


def main():
    errors = []
    if not os.path.isdir(PACK):
        print("OUTBOUND PACK CHECK FAILED")
        print("  - content/outbound does not exist")
        return 1

    content = read_markdown(errors)
    check_structure(content, errors)
    check_prices(content, errors)
    source_tags = check_source_tags(errors)
    check_crm(source_tags, errors)

    if errors:
        print("OUTBOUND PACK CHECK FAILED")
        for error in errors:
            print("  -", error)
        return 1
    print(
        "outbound pack check ok — 7 unsent documents, 3 wedges, "
        "30 days, 12 cold touches, 8 multilingual community drafts, "
        "5 app-community drafts, "
        f"{len(source_tags)} synthetic source tags, 1 synthetic CRM row"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
