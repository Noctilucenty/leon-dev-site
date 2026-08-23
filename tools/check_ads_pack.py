#!/usr/bin/env python3
"""Validate the offline paid-campaign build pack.

This checker is intentionally read-only and has no network or ad-platform
dependencies. It validates disabled state, offer/asset coordination, RSA limits,
full UTM attribution, blank economics inputs, and no-launch gates.

    python3 tools/check_ads_pack.py
"""

import csv
import io
import os
import re
import struct
import sys
from collections import defaultdict
from urllib.parse import parse_qs, urlparse


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "content", "ads")

GOOGLE_FILE = os.path.join(PACK, "google-search-build.csv")
META_FILE = os.path.join(PACK, "meta-build.csv")
ECONOMICS_FILE = os.path.join(PACK, "economics-calculator.csv")
README_FILE = os.path.join(PACK, "README.md")

GOOGLE_FIELDS = (
    "record_type", "campaign", "ad_group", "entity_id", "status", "scope",
    "match_type", "priority", "text", "final_url", "utm_source", "utm_medium",
    "utm_campaign", "utm_term", "utm_content", "instruction",
)
META_FIELDS = (
    "record_type", "campaign", "ad_set", "variant_id", "status", "asset_path",
    "objective", "conversion_location", "performance_goal", "conversion_event",
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "final_url", "primary_text", "headline", "description", "cta", "instruction",
)
ECONOMICS_FIELDS = (
    "row_type", "key", "label", "input", "calculated_value", "unit",
    "decision_note",
)

GOOGLE_CAMPAIGN = "DRAFT | BA | Search | Missed Lead Recovery"
META_CAMPAIGN = "DRAFT | BA | Meta | Missed Lead Recovery"
CAMPAIGN_TAG = "ba-missed-lead-recovery-v1"
WEDGES = {"home_services", "auto_repair", "restaurant_food"}
CLICK_IDS = {"gclid", "gbraid", "wbraid", "fbclid", "msclkid", "dclid"}
ASSETS = {
    "assets/social/ad_01_contractor_after_hours.png",
    "assets/social/ad_02_contractor_flow.png",
    "assets/social/ad_03_auto_estimates.png",
    "assets/social/ad_04_restaurant_direct.png",
    "assets/social/ad_05_founder_direct.png",
    "assets/social/ad_06_lead_leak_review.png",
}
GOOGLE_TOTAL_BUDGET = "$100 USD total for full campaign"
GOOGLE_FLIGHT_DURATION = "10 calendar days"
GOOGLE_START_DATE = "UNSET — choose future date after final launch authorization"
GOOGLE_END_DATE = "UNSET — start date + 9 calendar days; ends 23:59 account timezone"
META_ZERO_ALLOCATION = "0 USD — NO ALLOCATION IN FIRST 10-DAY TEST"
APPROVED_ECONOMICS_INPUTS = {
    "approved_test_media_cap": ("100", "USD"),
    "approved_test_days": ("10", "calendar_days"),
    "google_test_allocation": ("100", "USD"),
    "meta_test_allocation": ("0", "USD"),
}


def read_text(path, errors):
    if not os.path.isfile(path):
        errors.append(f"missing file: {os.path.relpath(path, ROOT)}")
        return ""
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def read_csv(path, expected_fields, errors):
    if not os.path.isfile(path):
        errors.append(f"missing file: {os.path.relpath(path, ROOT)}")
        return []
    with io.open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_fields:
            errors.append(
                f"{os.path.basename(path)}: schema changed; expected exact checked header"
            )
        try:
            rows = list(reader)
        except csv.Error as exc:
            errors.append(f"{os.path.basename(path)}: invalid CSV: {exc}")
            return []
    if not rows:
        errors.append(f"{os.path.basename(path)}: no build rows")
    for line_no, row in enumerate(rows, start=2):
        if None in row:
            errors.append(
                f"{os.path.basename(path)} line {line_no}: too many CSV columns"
            )
    return rows


def one_setting(rows, entity_id, errors, file_label):
    matches = [
        row for row in rows
        if row.get("record_type") == "campaign_setting"
        and row.get("entity_id", row.get("variant_id")) == entity_id
    ]
    if len(matches) != 1:
        errors.append(f"{file_label}: expected one {entity_id!r} campaign setting")
        return {}
    return matches[0]


def check_url(row, source, medium, errors, prefix):
    value = row.get("final_url", "")
    parsed = urlparse(value)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if parsed.scheme != "https" or parsed.netloc != "leonbuilds.org":
        errors.append(f"{prefix}: final URL must use https://leonbuilds.org")
    if parsed.path.rstrip("/") != "/missed-lead-recovery":
        errors.append(f"{prefix}: final URL must use /missed-lead-recovery")
    expected = {
        "utm_source": row.get("utm_source", ""),
        "utm_medium": row.get("utm_medium", ""),
        "utm_campaign": row.get("utm_campaign", ""),
        "utm_term": row.get("utm_term", ""),
        "utm_content": row.get("utm_content", ""),
    }
    for key, expected_value in expected.items():
        if not expected_value:
            errors.append(f"{prefix}: {key} column must not be blank")
        if query.get(key) != [expected_value]:
            errors.append(f"{prefix}: URL {key} must match its column")
    if expected["utm_source"] != source or expected["utm_medium"] != medium:
        errors.append(f"{prefix}: unexpected paid source/medium")
    if expected["utm_campaign"] != CAMPAIGN_TAG:
        errors.append(f"{prefix}: unexpected campaign UTM")
    if expected["utm_term"] not in WEDGES:
        errors.append(f"{prefix}: utm_term must be one of the three niche wedges")
    if "s" in query:
        errors.append(f"{prefix}: legacy s parameter is not allowed")
    present_click_ids = sorted(CLICK_IDS & set(query))
    if present_click_ids:
        errors.append(f"{prefix}: invented click-ID parameters present: {present_click_ids}")
    allowed = set(expected)
    extra = sorted(set(query) - allowed)
    if extra:
        errors.append(f"{prefix}: unexpected query parameters: {extra}")


def check_readme(errors):
    text = read_text(README_FILE, errors)
    if not text:
        return
    lead = "\n".join(text.splitlines()[:10])
    for marker in (
        "Status: DRAFT — DISABLED — GOOGLE $100 / 10 CALENDAR DAYS — META $0",
        "NO LAUNCH AUTHORIZATION.",
    ):
        if marker not in lead:
            errors.append(f"README.md: top-of-file marker missing: {marker}")
    required_links = (
        "https://support.google.com/google-ads/answer/7684791",
        "https://support.google.com/google-ads/answer/10486938",
        "https://support.google.com/google-ads/answer/10486637",
        "https://support.google.com/google-ads/answer/1722038",
        "https://support.google.com/google-ads/answer/14996023",
        "https://support.google.com/google-ads/answer/2453983",
        "https://www.facebook.com/business/ads/ad-objectives/lead-generation/lead-ads-with-forms",
        "https://www.facebook.com/help/331509497253087/",
        "https://www.facebook.com/business/ads/meta-advantage-plus/leads",
    )
    for url in required_links:
        if url not in text:
            errors.append(f"README.md: missing official source {url}")
    for asset in sorted(ASSETS):
        if asset not in text:
            errors.append(f"README.md: missing creative map row for {asset}")
    for required in (
        "calendar_booking_success", "qualified_call_held", "won_client",
        "all five standard UTM", "message/landing mismatch",
        "$100 total across 10 calendar", "Meta receives $0",
        "not $100 per platform", "not launch authorization",
    ):
        if required not in text:
            errors.append(f"README.md: missing required contract text {required!r}")


def check_google(errors):
    rows = read_csv(GOOGLE_FILE, GOOGLE_FIELDS, errors)
    if not rows:
        return
    campaigns = {row.get("campaign") for row in rows}
    if campaigns != {GOOGLE_CAMPAIGN}:
        errors.append("google-search-build.csv: must contain exactly one named campaign")
    for line_no, row in enumerate(rows, start=2):
        if row.get("status") != "DISABLED":
            errors.append(f"google-search-build.csv line {line_no}: status must be DISABLED")

    budget_type = one_setting(rows, "budget_type", errors, "google-search-build.csv")
    if budget_type and budget_type.get("text") != "Campaign total budget":
        errors.append("google-search-build.csv: budget type must be Campaign total budget")
    budget = one_setting(rows, "budget", errors, "google-search-build.csv")
    if budget and budget.get("text") != GOOGLE_TOTAL_BUDGET:
        errors.append("google-search-build.csv: Google allocation must be the exact $100 total")
    duration = one_setting(rows, "flight_duration", errors, "google-search-build.csv")
    if duration and duration.get("text") != GOOGLE_FLIGHT_DURATION:
        errors.append("google-search-build.csv: flight must be exactly 10 calendar days")
    start_date = one_setting(rows, "start_date", errors, "google-search-build.csv")
    if start_date and start_date.get("text") != GOOGLE_START_DATE:
        errors.append("google-search-build.csv: start date must remain unset pending launch authorization")
    end_date = one_setting(rows, "end_date", errors, "google-search-build.csv")
    if end_date and end_date.get("text") != GOOGLE_END_DATE:
        errors.append("google-search-build.csv: end date must remain the unset start-plus-nine-day rule")
    bidding = one_setting(rows, "bidding_strategy", errors, "google-search-build.csv")
    if bidding and bidding.get("text") != "UNSET":
        errors.append("google-search-build.csv: bidding strategy must remain UNSET")
    location = one_setting(rows, "location_option", errors, "google-search-build.csv")
    if location and not location.get("text", "").startswith("Presence: people in or regularly in"):
        errors.append("google-search-build.csv: Presence-only location instruction is required")
    networks = one_setting(rows, "networks", errors, "google-search-build.csv")
    if networks and networks.get("text") != "Google Search only":
        errors.append("google-search-build.csv: initial network must be Google Search only")

    keywords = [row for row in rows if row.get("record_type") == "keyword"]
    groups = {row.get("ad_group") for row in keywords}
    if groups != WEDGES:
        errors.append("google-search-build.csv: keyword ad groups must be the three niche wedges")
    for group in sorted(WEDGES):
        group_rows = [row for row in keywords if row.get("ad_group") == group]
        by_text = defaultdict(set)
        for row in group_rows:
            if row.get("match_type") not in {"exact", "phrase"}:
                errors.append(f"google-search-build.csv: {group} uses a non-controlled match type")
            by_text[row.get("text", "")].add(row.get("match_type"))
        if len(by_text) < 5:
            errors.append(f"google-search-build.csv: {group} needs at least five keyword concepts")
        for keyword, match_types in by_text.items():
            if match_types != {"exact", "phrase"}:
                errors.append(
                    f"google-search-build.csv: {group} keyword {keyword!r} needs exact and phrase rows"
                )

    negatives = [row for row in rows if row.get("record_type") == "negative"]
    campaign_negatives = [row for row in negatives if row.get("scope") == "campaign"]
    if len(campaign_negatives) < 40:
        errors.append("google-search-build.csv: at least 40 reviewed campaign negatives required")
    for group in sorted(WEDGES):
        scoped = [row for row in negatives if row.get("ad_group") == group]
        if len(scoped) < 3:
            errors.append(f"google-search-build.csv: {group} needs cross-niche negatives")
    for row in negatives:
        if row.get("match_type") not in {"broad", "phrase", "exact"}:
            errors.append("google-search-build.csv: negative keyword missing valid match type")

    headlines = [row for row in rows if row.get("record_type") == "rsa_headline"]
    descriptions = [row for row in rows if row.get("record_type") == "rsa_description"]
    urls = [row for row in rows if row.get("record_type") == "rsa_url"]
    rsa_ids = {row.get("entity_id") for row in headlines}
    for group in sorted(WEDGES):
        ids = {row.get("entity_id") for row in headlines if row.get("ad_group") == group}
        if len(ids) != 2:
            errors.append(f"google-search-build.csv: {group} requires exactly two draft RSAs")
    for rsa_id in sorted(rsa_ids):
        hs = [row for row in headlines if row.get("entity_id") == rsa_id]
        ds = [row for row in descriptions if row.get("entity_id") == rsa_id]
        us = [row for row in urls if row.get("entity_id") == rsa_id]
        if not 8 <= len(hs) <= 15:
            errors.append(f"google-search-build.csv: {rsa_id} needs 8–15 headlines")
        if not 2 <= len(ds) <= 4:
            errors.append(f"google-search-build.csv: {rsa_id} needs 2–4 descriptions")
        if len({row.get("text") for row in hs}) != len(hs):
            errors.append(f"google-search-build.csv: {rsa_id} has duplicate headlines")
        if len({row.get("text") for row in ds}) != len(ds):
            errors.append(f"google-search-build.csv: {rsa_id} has duplicate descriptions")
        for row in hs:
            if len(row.get("text", "")) > 30:
                errors.append(
                    f"google-search-build.csv: {rsa_id} headline exceeds 30 characters: "
                    f"{row.get('text')!r}"
                )
        for row in ds:
            if len(row.get("text", "")) > 90:
                errors.append(
                    f"google-search-build.csv: {rsa_id} description exceeds 90 characters: "
                    f"{row.get('text')!r}"
                )
        if len(us) != 1:
            errors.append(f"google-search-build.csv: {rsa_id} needs exactly one final URL")
        else:
            check_url(us[0], "google", "cpc", errors, f"google {rsa_id}")

    conversions = [row for row in rows if row.get("record_type") == "conversion"]
    observed_order = [row.get("text") for row in sorted(conversions, key=lambda r: int(r.get("priority", "999")))]
    expected_order = [
        "won_client", "qualified_call_held", "calendar_booking_success",
        "quote_lead_accepted", "cta_click_or_form_start",
    ]
    if observed_order != expected_order:
        errors.append("google-search-build.csv: conversion hierarchy is missing or out of order")
    checks = [row for row in rows if row.get("record_type") == "launch_check"]
    if len(checks) < 14:
        errors.append("google-search-build.csv: launch checklist is incomplete")
    if sum(row.get("priority") == "BLOCKER" for row in checks) < 12:
        errors.append("google-search-build.csv: prelaunch blockers are incomplete")


def png_dimensions(path):
    with open(path, "rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", header[16:24])


def check_meta(errors):
    rows = read_csv(META_FILE, META_FIELDS, errors)
    if not rows:
        return
    campaigns = {row.get("campaign") for row in rows}
    if campaigns != {META_CAMPAIGN}:
        errors.append("meta-build.csv: must contain exactly one named campaign")
    allowed_status = {"DISABLED", "HOLD_MESSAGE_MISMATCH"}
    for line_no, row in enumerate(rows, start=2):
        if row.get("status") not in allowed_status:
            errors.append(f"meta-build.csv line {line_no}: invalid no-launch status")
        if row.get("objective") != "Leads":
            errors.append(f"meta-build.csv line {line_no}: objective must be Leads")
        if row.get("conversion_location") != "Website":
            errors.append(f"meta-build.csv line {line_no}: conversion location must be Website")
        if row.get("conversion_event") != "calendar_booking_success":
            errors.append(f"meta-build.csv line {line_no}: website booking event mismatch")

    budget = one_setting(rows, "budget", errors, "meta-build.csv")
    if budget and budget.get("primary_text") != META_ZERO_ALLOCATION:
        errors.append("meta-build.csv: Meta allocation must remain exactly $0 for the first test")
    schedule = one_setting(rows, "schedule", errors, "meta-build.csv")
    if schedule and schedule.get("primary_text") != "NOT SCHEDULED":
        errors.append("meta-build.csv: Meta must remain unscheduled for the first test")

    creatives = [row for row in rows if row.get("record_type") == "creative"]
    paths = {row.get("asset_path") for row in creatives}
    if paths != ASSETS or len(creatives) != 6:
        errors.append("meta-build.csv: creative map must contain each ad_01 through ad_06 exactly once")
    for row in creatives:
        path = row.get("asset_path", "")
        full_path = os.path.join(ROOT, path)
        if not os.path.isfile(full_path):
            errors.append(f"meta-build.csv: missing creative asset {path}")
        elif png_dimensions(full_path) != (1080, 1350):
            errors.append(f"meta-build.csv: {path} must be a 1080x1350 PNG")
        check_url(row, "meta", "paid_social", errors, f"meta {row.get('variant_id')}")
        combined = " ".join(
            row.get(field, "") for field in ("primary_text", "headline", "description")
        ).lower()
        if re.search(r"\bguarantee(?:d|s)?\b", combined):
            errors.append(f"meta-build.csv: {row.get('variant_id')} contains a guarantee claim")
    holds = [row for row in creatives if row.get("status") == "HOLD_MESSAGE_MISMATCH"]
    if len(holds) != 1 or not holds[0].get("asset_path", "").endswith("ad_04_restaurant_direct.png"):
        errors.append("meta-build.csv: only ad_04 must be held for message/landing mismatch")

    qualifications = [row for row in rows if row.get("record_type") == "qualification"]
    gates = [row for row in rows if row.get("record_type") == "retarget_gate"]
    checks = [row for row in rows if row.get("record_type") == "launch_check"]
    if len(qualifications) < 5:
        errors.append("meta-build.csv: qualification plan is incomplete")
    if len(gates) < 5:
        errors.append("meta-build.csv: retargeting gate is incomplete")
    if not any("numeric threshold unset" in row.get("primary_text", "").lower() for row in gates):
        errors.append("meta-build.csv: retargeting audience threshold must remain explicitly unset")
    if len(checks) < 10:
        errors.append("meta-build.csv: launch checklist is incomplete")


def check_economics(errors):
    rows = read_csv(ECONOMICS_FILE, ECONOMICS_FIELDS, errors)
    if not rows:
        return
    keys = {row.get("key") for row in rows}
    required = {
        "contribution_profit_per_client", "maximum_cac",
        "maximum_cost_per_booked_call", "maximum_weekly_ad_spend",
        "actual_cost_per_booked_call", "actual_cost_per_qualified_call",
        "actual_cac", "zero_booking_stop", "booking_cost_stop",
        "qualification_stop", "profit_stop",
        "approved_test_media_cap", "approved_test_days",
        "google_test_allocation", "meta_test_allocation",
    }
    missing = sorted(required - keys)
    if missing:
        errors.append(f"economics-calculator.csv: missing required rows {missing}")
    seen = set()
    for line_no, row in enumerate(rows, start=2):
        key = row.get("key", "")
        if not key or key in seen:
            errors.append(f"economics-calculator.csv line {line_no}: blank or duplicate key")
        seen.add(key)
        row_type = row.get("row_type")
        if row_type == "input":
            approved = APPROVED_ECONOMICS_INPUTS.get(key)
            if approved:
                expected_value, expected_unit = approved
                if row.get("input") != expected_value or row.get("unit") != expected_unit:
                    errors.append(
                        f"economics-calculator.csv line {line_no}: {key} must be "
                        f"{expected_value} {expected_unit}"
                    )
                if row.get("calculated_value"):
                    errors.append(
                        f"economics-calculator.csv line {line_no}: approved input must not contain a formula"
                    )
            elif row.get("input") or row.get("calculated_value"):
                errors.append(
                    f"economics-calculator.csv line {line_no}: unapproved decision inputs must remain blank"
                )
        elif row_type in {"formula", "stop_rule"}:
            formula = row.get("calculated_value", "")
            if not formula.startswith("="):
                errors.append(f"economics-calculator.csv line {line_no}: missing formula")
            if re.search(r"(?:HYPERLINK|WEBSERVICE|IMPORT|EXEC)\s*\(", formula, re.I):
                errors.append(f"economics-calculator.csv line {line_no}: external formula is forbidden")
            if row.get("input"):
                errors.append(f"economics-calculator.csv line {line_no}: formula input cell must be blank")
        else:
            errors.append(f"economics-calculator.csv line {line_no}: unknown row_type {row_type!r}")
    if len([row for row in rows if row.get("row_type") == "stop_rule"]) < 4:
        errors.append("economics-calculator.csv: four owner-defined stop rules are required")


def check_no_fabricated_ids(errors):
    for path in (README_FILE, GOOGLE_FILE, META_FILE, ECONOMICS_FILE):
        text = read_text(path, errors)
        for key in CLICK_IDS:
            if re.search(rf"[?&]{re.escape(key)}=", text, re.I):
                errors.append(
                    f"{os.path.relpath(path, ROOT)}: URL contains forbidden {key} parameter"
                )


def main():
    errors = []
    if not os.path.isdir(PACK):
        print("ADS PACK CHECK FAILED")
        print("  - content/ads does not exist")
        return 1
    check_readme(errors)
    check_google(errors)
    check_meta(errors)
    check_economics(errors)
    check_no_fabricated_ids(errors)
    if errors:
        print("ADS PACK CHECK FAILED")
        for error in errors:
            print("  -", error)
        return 1
    print(
        "ads pack check ok — 1 disabled Google campaign / 3 niche ad groups / "
        "6 draft RSAs / 1 disabled Meta campaign / 6 mapped creatives / "
        "$100 Google campaign-total cap / 10 calendar days / Meta $0 / "
        "business-economics inputs blank / no click IDs"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
