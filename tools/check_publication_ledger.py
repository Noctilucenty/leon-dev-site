#!/usr/bin/env python3
"""Validate the canonical off-site publication ledger.

The historical Facebook audit is intentionally append-only and contains
retractions. This checker keeps the current-state file structurally honest and
prevents stale-price creative from being marked safe or live by accident.
"""

import ast
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "content", "publication-ledger.csv")
COVERAGE = os.path.join(ROOT, "content", "facebook-group-coverage.csv")

REQUIRED = {
    "record_id", "platform", "target", "language", "content_type", "status",
    "object_count", "submitted_date", "public_url", "evidence_url",
    "source_tag", "copy_state", "asset_state", "price_basis", "last_checked",
    "next_action", "notes",
}
STATUSES = {
    "published", "pending_corrected", "pending_partial_stale_preview", "pending_stale",
    "declined", "removed",
    "unavailable", "marketplace_active_policy_risk", "marketplace_active_unsafe",
    "marketplace_needs_attention", "marketplace_removed_by_platform",
    "draft_blocked", "draft_ready", "unsent_template",
}
CURRENT = {
    "published", "pending_corrected", "marketplace_active_policy_risk", "draft_ready",
}
STALE_COPY = {"noncanonical_price", "stale_prices", "old_domain", "zero_price"}
STALE_ASSETS = {"stale_link_preview", "stale_rate_card", "price_baked"}
COPY_STATES = {
    "corrected", "current", "mixed", "noncanonical_price", "old_domain",
    "stale_prices", "unknown", "zero_price",
}
ASSET_STATES = {
    "listing_card", "marketplace_card", "none", "price_baked", "price_free",
    "proof_card", "stale_link_preview", "stale_rate_card", "unknown",
}
COVERAGE_REQUIRED = {
    "group_id", "group_name", "group_url", "activity_status", "last_checked",
    "evidence_url", "notes",
}
COVERAGE_STATUSES = {"activity_found", "no_activity_found"}
STATIC_PRICE_BASES = {
    "mixed", "noncanonical", "not_applicable", "price_free", "stale_known", "unknown",
}
COPY_BY_CURRENT_STATUS = {
    "published": {"current"},
    "pending_corrected": {"corrected"},
    "marketplace_active_policy_risk": {"current"},
    "draft_ready": {"current"},
    "unsent_template": {"current"},
}
GROUP_ID_RE = re.compile(r"https://www\.facebook\.com/groups/([^/?]+)")


def floors_fingerprint():
    """Hash the literal FLOORS dict without importing cached Python bytecode."""
    path = os.path.join(ROOT, "tools", "check_prices.py")
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            getattr(target, "id", None) == "FLOORS" for target in node.targets
        ):
            floors = ast.literal_eval(node.value)
            payload = json.dumps(floors, sort_keys=True, separators=(",", ":"))
            return hashlib.sha256(payload.encode()).hexdigest()[:12]
    raise RuntimeError("tools/check_prices.py no longer defines a literal FLOORS dict")


def main():
    errors = []
    warnings = []
    current_floors = f"floors:{floors_fingerprint()}"
    with open(LEDGER, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            errors.append("missing columns: " + ", ".join(sorted(missing)))
        rows = list(reader)

    seen = set()
    source_tags = {}
    ledger_group_ids = set()
    unresolved_group_targets = []
    for line_no, row in enumerate(rows, start=2):
        rid = row.get("record_id", "").strip()
        prefix = f"line {line_no} ({rid or 'missing record_id'})"
        if not rid:
            errors.append(f"{prefix}: record_id is required")
        elif rid in seen:
            errors.append(f"{prefix}: duplicate record_id")
        seen.add(rid)

        status = row.get("status", "").strip()
        if status not in STATUSES:
            errors.append(f"{prefix}: unknown status {status!r}")

        try:
            count = int(row.get("object_count", ""))
            if count < 1:
                raise ValueError
        except ValueError:
            errors.append(f"{prefix}: object_count must be a positive integer")

        checked = row.get("last_checked", "").strip()
        try:
            checked_date = dt.date.fromisoformat(checked)
            if checked_date > dt.date.today():
                errors.append(f"{prefix}: last_checked cannot be in the future")
            if (dt.date.today() - checked_date).days > 30:
                warnings.append(f"{prefix}: status has not been checked in more than 30 days")
        except ValueError:
            errors.append(f"{prefix}: last_checked must be YYYY-MM-DD")

        submitted = row.get("submitted_date", "").strip()
        if submitted:
            try:
                dt.date.fromisoformat(submitted)
            except ValueError:
                errors.append(f"{prefix}: submitted_date must be blank or YYYY-MM-DD")

        evidence = row.get("evidence_url", "").strip()
        if not evidence:
            errors.append(f"{prefix}: evidence_url or local evidence path is required")
        elif not evidence.startswith(("http://", "https://")):
            local_evidence = os.path.join(ROOT, evidence)
            if not os.path.exists(local_evidence):
                errors.append(f"{prefix}: local evidence path does not exist: {evidence}")

        copy_state = row.get("copy_state", "").strip()
        asset_state = row.get("asset_state", "").strip()
        if copy_state not in COPY_STATES:
            errors.append(f"{prefix}: unknown copy_state {copy_state!r}")
        if asset_state not in ASSET_STATES:
            errors.append(f"{prefix}: unknown asset_state {asset_state!r}")
        if status in CURRENT and copy_state in STALE_COPY:
            errors.append(f"{prefix}: current content cannot use {copy_state} copy")
        if status in CURRENT and asset_state in STALE_ASSETS:
            errors.append(f"{prefix}: current content cannot use a stale/price-baked asset")
        allowed_copy = COPY_BY_CURRENT_STATUS.get(status)
        if allowed_copy is not None and copy_state not in allowed_copy:
            errors.append(
                f"{prefix}: status {status} requires copy_state in {sorted(allowed_copy)}, "
                f"found {copy_state!r}"
            )
        if status == "draft_ready":
            if copy_state != "current":
                errors.append(f"{prefix}: draft_ready requires copy_state=current")
            if asset_state not in {"price_free", "proof_card"}:
                errors.append(
                    f"{prefix}: draft_ready requires a price_free or proof_card asset"
                )

        price_basis = row.get("price_basis", "").strip()
        if price_basis.startswith("floors:"):
            if price_basis != current_floors:
                errors.append(
                    f"{prefix}: price basis {price_basis} is stale; current basis is "
                    f"{current_floors}. Re-check external prices before updating the ledger."
                )
        elif price_basis not in STATIC_PRICE_BASES:
            errors.append(f"{prefix}: unknown price_basis {price_basis!r}")

        if status in {"published", "pending_corrected", "marketplace_active_policy_risk", "unsent_template"}:
            if price_basis not in {"price_free", current_floors}:
                errors.append(
                    f"{prefix}: current price-bearing content requires {current_floors} "
                    "or an explicit price_free basis"
                )
        if status == "draft_ready" and price_basis != "price_free":
            errors.append(f"{prefix}: draft_ready requires price_basis=price_free")
        if status == "marketplace_active_unsafe" and price_basis != "noncanonical":
            errors.append(f"{prefix}: marketplace_active_unsafe requires price_basis=noncanonical")

        source_tag = row.get("source_tag", "").strip()
        if source_tag:
            if source_tag in source_tags:
                errors.append(
                    f"{prefix}: source tag {source_tag!r} also belongs to {source_tags[source_tag]}"
                )
            source_tags[source_tag] = rid
        if status in {"published", "pending_corrected"} and not source_tag:
            warnings.append(f"{prefix}: add a unique source tag when the post can next be edited")

        public_url = row.get("public_url", "").lower()
        if status == "published" and not public_url:
            errors.append(f"{prefix}: published content requires a stable public_url")
        if status == "published" and "leonkelvinli.onrender.com" in public_url:
            errors.append(f"{prefix}: published URL uses the retired domain")
        if status.startswith("marketplace_") and not public_url:
            warnings.append(
                f"{prefix}: record the stable Marketplace item URL/ID when Facebook exposes it"
            )

        if row.get("platform") == "facebook_group":
            record_group_ids = {
                match.group(1)
                for field in (row.get("public_url", ""), row.get("evidence_url", ""))
                for match in GROUP_ID_RE.finditer(field)
            }
            if len(record_group_ids) > 1:
                errors.append(f"{prefix}: record points at multiple Facebook groups")
            elif record_group_ids:
                ledger_group_ids.update(record_group_ids)
            else:
                unresolved_group_targets.append((prefix, row.get("target", "").strip()))

    with open(COVERAGE, newline="", encoding="utf-8") as fh:
        coverage_reader = csv.DictReader(fh)
        missing = COVERAGE_REQUIRED - set(coverage_reader.fieldnames or [])
        if missing:
            errors.append("facebook coverage missing columns: " + ", ".join(sorted(missing)))
        coverage_rows = list(coverage_reader)

    coverage_ids = set()
    coverage_urls = set()
    coverage_counts = {status: 0 for status in COVERAGE_STATUSES}
    for line_no, row in enumerate(coverage_rows, start=2):
        gid = row.get("group_id", "").strip()
        prefix = f"facebook coverage line {line_no} ({gid or 'missing group_id'})"
        name = row.get("group_name", "").strip()
        url = row.get("group_url", "").strip()
        status = row.get("activity_status", "").strip()
        if not gid or not name:
            errors.append(f"{prefix}: group_id and group_name are required")
        if gid in coverage_ids:
            errors.append(f"{prefix}: duplicate group_id")
        coverage_ids.add(gid)
        if url in coverage_urls:
            errors.append(f"{prefix}: duplicate group_url")
        coverage_urls.add(url)
        expected_url = f"https://www.facebook.com/groups/{gid}/"
        if url != expected_url:
            errors.append(f"{prefix}: group_url must be {expected_url}")
        if status not in COVERAGE_STATUSES:
            errors.append(f"{prefix}: unknown activity_status {status!r}")
        else:
            coverage_counts[status] += 1
        try:
            coverage_checked = dt.date.fromisoformat(row.get("last_checked", "").strip())
            if coverage_checked > dt.date.today():
                errors.append(f"{prefix}: last_checked cannot be in the future")
            if (dt.date.today() - coverage_checked).days > 30:
                warnings.append(
                    f"{prefix}: coverage has not been checked in more than 30 days"
                )
        except ValueError:
            errors.append(f"{prefix}: last_checked must be YYYY-MM-DD")
        if not row.get("evidence_url", "").startswith("https://"):
            errors.append(f"{prefix}: evidence_url must be an HTTPS URL")

    if len(coverage_rows) != 51:
        errors.append(f"facebook coverage must contain all 51 joined groups, found {len(coverage_rows)}")
    expected_counts = {"activity_found": 21, "no_activity_found": 30}
    if coverage_counts != expected_counts:
        errors.append(
            f"facebook coverage status counts must be {expected_counts}, found {coverage_counts}"
        )

    coverage_name_to_id = {
        row["group_name"].strip(): row["group_id"].strip() for row in coverage_rows
    }
    for prefix, target in unresolved_group_targets:
        gid = coverage_name_to_id.get(target)
        if gid:
            ledger_group_ids.add(gid)
        else:
            errors.append(f"{prefix}: cannot map target to facebook group coverage")

    activity_group_ids = {
        row["group_id"].strip()
        for row in coverage_rows
        if row["activity_status"].strip() == "activity_found"
    }
    if ledger_group_ids != activity_group_ids:
        missing = sorted(activity_group_ids - ledger_group_ids)
        extra = sorted(ledger_group_ids - activity_group_ids)
        if missing:
            errors.append("activity groups missing ledger records: " + ", ".join(missing))
        if extra:
            errors.append("ledger groups not marked activity_found: " + ", ".join(extra))

    if errors:
        print("PUBLICATION LEDGER CHECK FAILED")
        for error in errors:
            print("  -", error)
        return 1

    object_total = sum(int(row["object_count"]) for row in rows)
    facebook_rows = [row for row in rows if row["platform"] == "facebook_group"]
    facebook_objects = sum(int(row["object_count"]) for row in facebook_rows)
    print(
        f"publication ledger ok — {len(rows)} records / {object_total} objects, "
        f"{len(seen)} unique ids"
    )
    print(
        f"facebook group activity — {len(facebook_rows)} records / "
        f"{facebook_objects} objects across {len(ledger_group_ids)} groups"
    )
    print(
        "facebook coverage ok — 51 joined groups: "
        f"{coverage_counts['activity_found']} with activity, "
        f"{coverage_counts['no_activity_found']} with none found"
    )
    for warning in warnings:
        print("  warning:", warning)
    return 0


if __name__ == "__main__":
    sys.exit(main())
