#!/usr/bin/env python3
"""Read-only, fail-closed acquisition funnel decision report.

Platform clicks/spend come from a filled copy of the ads economics CSV.
First-party sessions, inquiries, and authoritative sales stages come from the
server JSONL stores. This tool never calls an ad API or writes to an input.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


HARD_MEDIA_CAP_USD = 100.0
HARD_DURATION_CAP_DAYS = 10
VERDICTS = ("PAUSE", "ITERATE", "ELIGIBLE_TO_REVIEW")
RECEIPT_ID_RE = re.compile(
    r"^lead_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
BOOKING_UID_RE = re.compile(r"^[A-Za-z0-9._~:@+\-]{8,160}$")

PLANNING_INPUTS = (
    "average_contract_revenue",
    "direct_delivery_cost",
    "acceptable_acquisition_share",
    "expected_show_rate",
    "expected_qualification_rate",
    "expected_close_rate",
    "target_booked_calls_per_week",
    "maximum_zero_booking_spend",
    "minimum_qualified_call_rate",
    "minimum_contribution_return",
    "minimum_wins_before_profit_rule",
)
ACTUAL_INPUTS = (
    "actual_ad_spend",
    "actual_clicks",
    "actual_booked_calls",
    "actual_held_calls",
    "actual_qualified_calls",
    "actual_won_clients",
    "actual_contribution_profit",
)
SAFETY_INPUTS = (
    "approved_test_media_cap",
    "approved_test_days",
    "google_test_allocation",
    "meta_test_allocation",
)
COUNT_INPUTS = {
    "actual_clicks",
    "actual_booked_calls",
    "actual_held_calls",
    "actual_qualified_calls",
    "actual_won_clients",
    "minimum_wins_before_profit_rule",
    "approved_test_days",
}
RATE_INPUTS = {
    "acceptable_acquisition_share",
    "expected_show_rate",
    "expected_qualification_rate",
    "expected_close_rate",
    "minimum_qualified_call_rate",
}


@dataclass
class JsonlInput:
    path: Path
    available: bool
    records: list[dict[str, Any]]
    errors: list[str]


class Findings:
    def __init__(self) -> None:
        self.pause: list[str] = []
        self.iterate: list[str] = []
        self.notes: list[str] = []

    @staticmethod
    def _add(target: list[str], message: str) -> None:
        if message not in target:
            target.append(message)

    def add_pause(self, message: str) -> None:
        self._add(self.pause, message)

    def add_iterate(self, message: str) -> None:
        self._add(self.iterate, message)

    def add_note(self, message: str) -> None:
        self._add(self.notes, message)

    @property
    def verdict(self) -> str:
        if self.pause:
            return "PAUSE"
        if self.iterate:
            return "ITERATE"
        return "ELIGIBLE_TO_REVIEW"


def finite_number(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip().replace("$", "").replace(",", "")
    if not text:
        return None
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def integer_number(value: Any) -> Optional[int]:
    number = finite_number(value)
    if number is None or number < 0 or not number.is_integer():
        return None
    return int(number)


def truthy(value: Any) -> bool:
    return value is True


def normalized(value: Any) -> str:
    return str(value or "").strip().casefold()


def nested(mapping: dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def parse_day(value: Any) -> Optional[date]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def record_day(record: dict[str, Any]) -> Optional[date]:
    for key in ("occurredAt", "ts"):
        value = str(record.get(key) or "").strip()
        if not value:
            continue
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            continue
    return None


def in_window(record: dict[str, Any], start: date, end: date) -> bool:
    observed = record_day(record)
    return observed is not None and start <= observed <= end


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("top-level JSON value must be an object")
    return value


def read_jsonl(path: Path) -> JsonlInput:
    if not path.exists():
        return JsonlInput(path, False, [], [])
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        return JsonlInput(path, False, [], [f"cannot read: {error}"])
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append(f"line {line_number}: invalid JSON ({error.msg})")
            continue
        if not isinstance(value, dict):
            errors.append(f"line {line_number}: record must be an object")
            continue
        records.append(value)
    return JsonlInput(path, True, records, errors)


def read_economics(path: Path) -> tuple[dict[str, Any], list[str]]:
    values: dict[str, Any] = {}
    errors: list[str] = []
    if not path.exists():
        return values, [f"economics CSV is missing: {path}"]
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            expected = {"row_type", "key", "input"}
            if not reader.fieldnames or not expected.issubset(reader.fieldnames):
                return values, ["economics CSV must contain row_type, key, and input columns"]
            for line_number, row in enumerate(reader, start=2):
                key = str(row.get("key") or "").strip()
                if not key:
                    continue
                if key in values:
                    errors.append(f"economics CSV line {line_number}: duplicate key {key}")
                    continue
                if row.get("row_type") == "input":
                    values[key] = row.get("input")
    except (OSError, csv.Error) as error:
        errors.append(f"cannot read economics CSV: {error}")
    return values, errors


def campaign_match(record: dict[str, Any], campaign: str, source: str) -> bool:
    pairs = [
        (record.get("utmCampaign"), record.get("utmSource")),
        (record.get("campaign"), record.get("utm")),
        (record.get("firstUtmCampaign"), record.get("firstUtmSource")),
        (record.get("firstCampaign"), record.get("firstUtm")),
        (record.get("lastUtmCampaign"), record.get("lastUtmSource")),
        (record.get("lastCampaign"), record.get("lastUtm")),
    ]
    for container_name in ("attribution", "firstAttribution", "lastAttribution"):
        container = record.get(container_name)
        if isinstance(container, dict):
            pairs.append((container.get("utmCampaign"), container.get("utmSource")))
    wanted_campaign = normalized(campaign)
    wanted_source = normalized(source)
    return any(
        normalized(observed_campaign) == wanted_campaign
        and (not wanted_source or normalized(observed_source) == wanted_source)
        for observed_campaign, observed_source in pairs
    )


def scoped_records(
    records: Iterable[dict[str, Any]],
    start: date,
    end: date,
    mode: str,
    campaign: str,
    source: str,
) -> list[dict[str, Any]]:
    within = [record for record in records if in_window(record, start, end)]
    if mode == "campaign-only-files":
        return within
    return [record for record in within if campaign_match(record, campaign, source)]


def booking_replacements(records: Iterable[dict[str, Any]]) -> dict[str, str]:
    """Map each superseded Cal booking UID to its replacement.

    Cal assigns a new UID when a booking is rescheduled. The raw JSONL keeps
    both lifecycle records for auditability, but funnel reporting must treat a
    reschedule chain as one opportunity. Build the map from the complete input
    rather than only the report window so a chain that crosses the window edge
    still resolves consistently.
    """
    replacements: dict[str, str] = {}
    for record in records:
        if record.get("kind") != "funnel_stage":
            continue
        uid = str(record.get("bookingUid") or "").strip()
        context = record.get("context")
        previous_uid = (
            str(context.get("previousBookingUid") or "").strip()
            if isinstance(context, dict)
            else ""
        )
        if uid and previous_uid and uid != previous_uid:
            replacements[previous_uid] = uid
    return replacements


def canonical_booking_uid(uid: Any, replacements: dict[str, str]) -> str:
    """Follow a reschedule chain without hanging on malformed cyclic data."""
    current = str(uid or "").strip()
    seen: set[str] = set()
    while current in replacements and current not in seen:
        seen.add(current)
        current = replacements[current]
    return current


def qa_exclusion_ids(
    records: Iterable[dict[str, Any]],
) -> tuple[set[str], set[str], list[str]]:
    """Read exact append-only QA exclusions from the acquisition ledger.

    The exclusion record itself remains part of the audit trail. Invalid rows
    are reported instead of being applied silently.
    """
    receipt_ids: set[str] = set()
    booking_uids: set[str] = set()
    errors: list[str] = []
    for index, record in enumerate(records, start=1):
        if record.get("kind") != "qa_exclusion":
            continue
        has_receipt = "receiptId" in record
        has_booking = "bookingUid" in record
        receipt = record.get("receiptId") if has_receipt else ""
        booking = record.get("bookingUid") if has_booking else ""
        valid_receipt = (
            receipt
            if isinstance(receipt, str) and RECEIPT_ID_RE.fullmatch(receipt)
            else ""
        )
        valid_booking = (
            booking
            if isinstance(booking, str) and BOOKING_UID_RE.fullmatch(booking)
            else ""
        )
        if has_receipt == has_booking or (has_receipt and not valid_receipt) or (
            has_booking and not valid_booking
        ):
            errors.append(
                f"QA exclusion record {index} must contain exactly one valid receiptId or bookingUid."
            )
            continue
        expected_type = "receipt" if valid_receipt else "booking"
        expected_id = valid_receipt or valid_booking
        if record.get("targetType") not in (None, expected_type) or record.get(
            "targetId"
        ) not in (None, expected_id):
            errors.append(f"QA exclusion record {index} has inconsistent target metadata.")
            continue
        if record.get("dedupeKey") != f"qa-exclusion:{expected_type}:{expected_id}":
            errors.append(f"QA exclusion record {index} has an invalid dedupe key.")
            continue
        if valid_receipt:
            receipt_ids.add(valid_receipt)
        else:
            booking_uids.add(valid_booking)
    return receipt_ids, booking_uids, errors


def qa_session_ids(
    event_records: Iterable[dict[str, Any]],
    lead_records: Iterable[dict[str, Any]],
    acquisition_records_input: Iterable[dict[str, Any]],
    excluded_receipt_ids: set[str],
    excluded_booking_uids: set[str],
) -> set[str]:
    """Resolve only sessions explicitly tied to an excluded QA target."""
    sessions: set[str] = set()
    for lead in lead_records:
        if lead.get("receiptId") not in excluded_receipt_ids:
            continue
        session = str(lead.get("analyticsSessionId") or "").strip()
        if session:
            sessions.add(session)

    acquisition_rows = list(acquisition_records_input)
    replacements = booking_replacements(acquisition_rows)
    canonical_exclusions = {
        canonical_booking_uid(uid, replacements) for uid in excluded_booking_uids
    }
    for event in event_records:
        receipt = event.get("receipt")
        raw_booking_uid = str(event.get("bookingUid") or "").strip()
        booking_excluded = bool(raw_booking_uid) and (
            raw_booking_uid in excluded_booking_uids
            or canonical_booking_uid(raw_booking_uid, replacements)
            in canonical_exclusions
        )
        if receipt not in excluded_receipt_ids and not booking_excluded:
            continue
        session = str(event.get("sessionId") or "").strip()
        if session:
            sessions.add(session)
    return sessions


def merged_booking_attribution(
    records: Iterable[dict[str, Any]], replacements: Optional[dict[str, str]] = None
) -> dict[str, dict[str, dict[str, Any]]]:
    merged: dict[str, dict[str, dict[str, Any]]] = {}
    replacement_map = replacements or {}
    for record in records:
        uid = canonical_booking_uid(record.get("bookingUid"), replacement_map)
        if not uid:
            continue
        target = merged.setdefault(
            uid,
            {"firstAttribution": {}, "lastAttribution": {}, "attribution": {}},
        )
        for container_name in ("firstAttribution", "lastAttribution", "attribution"):
            container = record.get(container_name)
            if isinstance(container, dict):
                target[container_name].update(container)
    return merged


def acquisition_records(
    input_data: JsonlInput,
    start: date,
    end: date,
    mode: str,
    campaign: str,
    source: str,
    excluded_booking_uids: Optional[set[str]] = None,
) -> list[dict[str, Any]]:
    replacements = booking_replacements(input_data.records)
    touches = merged_booking_attribution(input_data.records, replacements)
    raw_exclusions = excluded_booking_uids or set()
    canonical_exclusions = {
        canonical_booking_uid(uid, replacements) for uid in raw_exclusions
    }
    selected: list[dict[str, Any]] = []
    for record in input_data.records:
        if record.get("kind") != "funnel_stage" or not in_window(record, start, end):
            continue
        raw_uid = str(record.get("bookingUid") or "").strip()
        uid = canonical_booking_uid(raw_uid, replacements)
        if raw_uid in raw_exclusions or uid in canonical_exclusions:
            continue
        # Cal can emit a cancellation for the superseded slot while completing
        # a reschedule. That is transport history, not a cancelled opportunity.
        if record.get("stage") == "cancelled" and raw_uid in replacements:
            continue
        enriched = dict(record)
        enriched["bookingUid"] = uid
        booking_touches = touches.get(
            uid,
            {"firstAttribution": {}, "lastAttribution": {}, "attribution": {}},
        )
        enriched["firstAttribution"] = booking_touches["firstAttribution"]
        enriched["lastAttribution"] = booking_touches["lastAttribution"]
        enriched["attribution"] = {
            **booking_touches["attribution"],
            **(record.get("attribution") if isinstance(record.get("attribution"), dict) else {}),
        }
        if mode == "campaign-only-files" or campaign_match(enriched, campaign, source):
            selected.append(enriched)
    return selected


def transition(
    name_from: str,
    count_from: Optional[int],
    name_to: str,
    count_to: Optional[int],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "from": name_from,
        "to": name_to,
        "fromCount": count_from,
        "toCount": count_to,
        "rate": None,
        "measurable": False,
    }
    if count_from is None or count_to is None:
        result["reason"] = "one or both source stages are unavailable"
    elif count_from == 0:
        result["reason"] = "upstream count is zero"
    elif count_to > count_from:
        result["reason"] = "downstream exceeds upstream; cohorts are not nested or an export is incomplete"
    else:
        result["rate"] = count_to / count_from
        result["measurable"] = True
    return result


def number_input(
    economics: dict[str, Any],
    key: str,
    findings: Findings,
    *,
    required: bool = True,
    nonnegative: bool = True,
) -> Optional[float]:
    raw = economics.get(key)
    number = finite_number(raw)
    if number is None:
        if required:
            findings.add_iterate(f"Economics input '{key}' is incomplete or not numeric.")
        return None
    if nonnegative and number < 0:
        findings.add_pause(f"Economics input '{key}' cannot be negative.")
        return None
    if key in COUNT_INPUTS and not number.is_integer():
        findings.add_pause(f"Economics input '{key}' must be a whole count.")
        return None
    return number


def build_report(
    config: dict[str, Any],
    economics: dict[str, Any],
    events: JsonlInput,
    leads: JsonlInput,
    acquisition: JsonlInput,
) -> dict[str, Any]:
    findings = Findings()
    qa_receipt_ids, qa_booking_uids, qa_exclusion_errors = qa_exclusion_ids(
        acquisition.records
    )
    qa_exclusion_records_read = sum(
        1 for record in acquisition.records if record.get("kind") == "qa_exclusion"
    )
    if qa_exclusion_errors:
        findings.add_pause(" ".join(qa_exclusion_errors))

    excluded_qa_sessions = qa_session_ids(
        events.records,
        leads.records,
        acquisition.records,
        qa_receipt_ids,
        qa_booking_uids,
    )
    qa_booking_replacements = booking_replacements(acquisition.records)
    canonical_qa_booking_uids = {
        canonical_booking_uid(uid, qa_booking_replacements)
        for uid in qa_booking_uids
    }

    def event_is_qa_excluded(record: dict[str, Any]) -> bool:
        session_id = str(record.get("sessionId") or "").strip()
        if session_id and session_id in excluded_qa_sessions:
            return True
        if record.get("receipt") in qa_receipt_ids:
            return True
        raw_booking_uid = str(record.get("bookingUid") or "").strip()
        return bool(raw_booking_uid) and (
            raw_booking_uid in qa_booking_uids
            or canonical_booking_uid(raw_booking_uid, qa_booking_replacements)
            in canonical_qa_booking_uids
        )

    reportable_event_records = [
        record
        for record in events.records
        if not event_is_qa_excluded(record)
    ]
    qa_event_records_excluded = len(events.records) - len(reportable_event_records)
    if qa_event_records_excluded:
        findings.add_note(
            f"Excluded {qa_event_records_excluded} event record(s) across "
            f"{len(excluded_qa_sessions)} exact QA session(s); source records remain append-only."
        )

    non_synthetic_lead_records = [
        record for record in leads.records if record.get("synthetic") is not True
    ]
    synthetic_leads_excluded = len(leads.records) - len(non_synthetic_lead_records)
    reportable_lead_records = [
        record
        for record in non_synthetic_lead_records
        if str(record.get("receiptId") or "").strip() not in qa_receipt_ids
    ]
    qa_lead_records_excluded = len(non_synthetic_lead_records) - len(
        reportable_lead_records
    )
    if synthetic_leads_excluded:
        findings.add_note(
            f"Excluded {synthetic_leads_excluded} synthetic lead-delivery probe "
            "record(s) from inquiry reporting."
        )
    if qa_lead_records_excluded:
        findings.add_note(
            f"Excluded {qa_lead_records_excluded} exact QA quote receipt record(s) "
            "from inquiry reporting; source records remain append-only."
        )
    if qa_booking_uids:
        findings.add_note(
            f"Configured {len(qa_booking_uids)} append-only QA booking UID exclusion(s)."
        )

    if config.get("schemaVersion") != 1:
        findings.add_pause("Run manifest schemaVersion must be 1.")

    limit_budget = finite_number(nested(config, "limits", "totalMediaBudgetUsd"))
    limit_days = integer_number(nested(config, "limits", "calendarDays"))
    if limit_budget is None or not (0 < limit_budget <= HARD_MEDIA_CAP_USD):
        findings.add_pause("Run manifest media cap must be greater than $0 and no more than $100 total.")
    if limit_days is None or not (0 < limit_days <= HARD_DURATION_CAP_DAYS):
        findings.add_pause("Run manifest duration must be 1-10 calendar days.")

    start = parse_day(nested(config, "window", "startDate"))
    end = parse_day(nested(config, "window", "endDate"))
    actual_days: Optional[int] = None
    if start is None or end is None:
        findings.add_pause("A valid startDate and endDate are required to enforce the review window.")
    elif end < start:
        findings.add_pause("endDate cannot be earlier than startDate.")
    else:
        actual_days = (end - start).days + 1
        if actual_days > HARD_DURATION_CAP_DAYS or (
            limit_days is not None and actual_days > limit_days
        ):
            findings.add_pause(f"Review window is {actual_days} calendar days, above the allowed duration.")

    mode = str(nested(config, "scope", "mode") or "").strip()
    campaign = str(nested(config, "scope", "utmCampaign") or "").strip()
    source = str(nested(config, "scope", "utmSource") or "").strip()
    if mode not in {"utm-campaign", "campaign-only-files"}:
        findings.add_pause("scope.mode must be 'utm-campaign' or 'campaign-only-files'.")
    if mode == "utm-campaign" and not campaign:
        findings.add_pause("scope.utmCampaign is required for attributed-file mode.")

    for name, input_data in (
        ("events", events),
        ("leads", leads),
        ("acquisition", acquisition),
    ):
        if input_data.errors:
            findings.add_pause(
                f"{name} JSONL failed integrity checks: {'; '.join(input_data.errors)}"
            )
        if not input_data.available:
            findings.add_iterate(
                f"{name} JSONL is unavailable; its funnel stage remains unknown."
            )
        if not truthy(nested(config, "dataReadiness", name + "Complete")):
            findings.add_iterate(f"dataReadiness.{name}Complete is not confirmed.")
        integrity_records = reportable_lead_records if name == "leads" else (
            reportable_event_records if name == "events" else input_data.records
        )
        missing_timestamps = sum(
            1 for record in integrity_records if record_day(record) is None
        )
        if missing_timestamps:
            findings.add_pause(
                f"{name} JSONL has {missing_timestamps} record(s) without a valid timestamp."
            )

    scoped_events: list[dict[str, Any]] = []
    scoped_leads: list[dict[str, Any]] = []
    scoped_acquisition: list[dict[str, Any]] = []
    valid_window = start is not None and end is not None and end >= start
    valid_scope = mode in {"utm-campaign", "campaign-only-files"}
    if valid_window and valid_scope:
        assert start is not None and end is not None
        scoped_events = scoped_records(
            reportable_event_records, start, end, mode, campaign, source
        )
        scoped_leads = scoped_records(
            reportable_lead_records, start, end, mode, campaign, source
        )
        scoped_acquisition = acquisition_records(
            acquisition,
            start,
            end,
            mode,
            campaign,
            source,
            qa_booking_uids,
        )

    page_events = [record for record in scoped_events if record.get("name") == "page_view"]
    session_ids = {
        str(record.get("sessionId") or "").strip() for record in page_events
    }
    session_ids.discard("")
    sessionless_page_views = sum(
        1 for record in page_events if not str(record.get("sessionId") or "").strip()
    )
    sessions: Optional[int] = (
        len(session_ids)
        if events.available and not events.errors and valid_window
        else None
    )
    if sessionless_page_views:
        findings.add_iterate(
            f"{sessionless_page_views} scoped page-view event(s) have no sessionId; "
            "session conversion is incomplete."
        )

    receipt_ids: set[str] = set()
    missing_receipts = 0
    for record in scoped_leads:
        receipt = str(record.get("receiptId") or "").strip()
        if receipt:
            receipt_ids.add(receipt)
        else:
            missing_receipts += 1
    inquiries: Optional[int] = (
        len(receipt_ids)
        if leads.available and not leads.errors and valid_window
        else None
    )
    if missing_receipts:
        findings.add_iterate(
            f"{missing_receipts} scoped lead record(s) lack receiptId and were not counted."
        )

    stage_sets = {
        stage: set() for stage in ("booked", "attended", "qualified", "won")
    }
    invalid_stage_records = 0
    for record in scoped_acquisition:
        stage = str(record.get("stage") or "")
        if stage not in stage_sets:
            continue
        uid = str(record.get("bookingUid") or "").strip()
        if not uid:
            invalid_stage_records += 1
            continue
        stage_sets[stage].add(uid)
    if invalid_stage_records:
        findings.add_pause(
            f"{invalid_stage_records} authoritative stage record(s) lack bookingUid."
        )
    stage_available = (
        acquisition.available and not acquisition.errors and valid_window
    )
    stage_counts: dict[str, Optional[int]] = {
        stage: len(values) if stage_available else None
        for stage, values in stage_sets.items()
    }
    for earlier, later in (
        ("booked", "attended"),
        ("attended", "qualified"),
        ("booked", "qualified"),
        ("qualified", "won"),
    ):
        before = stage_counts[earlier]
        after = stage_counts[later]
        if before is not None and after is not None and after > before:
            findings.add_iterate(
                f"Observed {later} ({after}) exceeds {earlier} ({before}); "
                "missing stages are not inferred."
            )

    econ_values: dict[str, Optional[float]] = {}
    for key in PLANNING_INPUTS + ACTUAL_INPUTS + SAFETY_INPUTS:
        econ_values[key] = number_input(economics, key, findings)
    override = number_input(
        economics,
        "maximum_cost_per_booked_call_override",
        findings,
        required=False,
    )

    for key in RATE_INPUTS:
        value = econ_values.get(key)
        if value is not None and not (0 <= value <= 1):
            findings.add_pause(f"Economics rate '{key}' must be between 0 and 1.")
    if econ_values.get("average_contract_revenue") == 0:
        findings.add_pause("average_contract_revenue must be greater than zero.")
    if econ_values.get("target_booked_calls_per_week") == 0:
        findings.add_pause("target_booked_calls_per_week must be greater than zero.")
    minimum_wins = econ_values.get("minimum_wins_before_profit_rule")
    if minimum_wins is not None and minimum_wins < 1:
        findings.add_pause("minimum_wins_before_profit_rule must be at least 1.")

    approved_cap = econ_values.get("approved_test_media_cap")
    approved_days = econ_values.get("approved_test_days")
    google_allocation = econ_values.get("google_test_allocation")
    meta_allocation = econ_values.get("meta_test_allocation")
    if approved_cap is not None and not (0 < approved_cap <= HARD_MEDIA_CAP_USD):
        findings.add_pause(
            "Economics approved_test_media_cap must be no more than $100."
        )
    if approved_days is not None and not (
        0 < approved_days <= HARD_DURATION_CAP_DAYS
    ):
        findings.add_pause("Economics approved_test_days must be no more than 10.")
    if (
        limit_budget is not None
        and approved_cap is not None
        and not math.isclose(limit_budget, approved_cap)
    ):
        findings.add_pause("Run manifest and economics media caps do not match.")
    if (
        limit_days is not None
        and approved_days is not None
        and limit_days != int(approved_days)
    ):
        findings.add_pause("Run manifest and economics duration caps do not match.")
    if None not in (google_allocation, meta_allocation, approved_cap):
        assert google_allocation is not None
        assert meta_allocation is not None
        assert approved_cap is not None
        if google_allocation + meta_allocation > approved_cap + 1e-9:
            findings.add_pause(
                "Google plus Meta allocation exceeds the approved total media cap."
            )
    if google_allocation is not None and google_allocation > HARD_MEDIA_CAP_USD:
        findings.add_pause("Google allocation cannot exceed the $100 test ceiling.")
    if meta_allocation is not None and not math.isclose(meta_allocation, 0.0):
        findings.add_pause("Meta allocation must remain $0 for this test.")

    actual_spend = econ_values.get("actual_ad_spend")
    actual_clicks_value = econ_values.get("actual_clicks")
    actual_clicks = (
        int(actual_clicks_value) if actual_clicks_value is not None else None
    )
    spend_ceiling = min(
        value
        for value in (HARD_MEDIA_CAP_USD, limit_budget, approved_cap)
        if value is not None and value > 0
    )
    if actual_spend is not None and actual_spend > spend_ceiling + 1e-9:
        findings.add_pause(
            f"Actual spend ${actual_spend:.2f} exceeds the enforced "
            f"${spend_ceiling:.2f} total ceiling."
        )

    observed_actuals: dict[str, Optional[int]] = {
        "actual_booked_calls": stage_counts["booked"],
        "actual_held_calls": stage_counts["attended"],
        "actual_qualified_calls": stage_counts["qualified"],
        "actual_won_clients": stage_counts["won"],
    }
    for key, observed in observed_actuals.items():
        declared = econ_values.get(key)
        if declared is not None and observed is not None and int(declared) != observed:
            findings.add_iterate(
                f"Economics {key}={int(declared)} does not reconcile to "
                f"authoritative JSONL count {observed}."
            )

    traffic_name = "clicks" if actual_clicks is not None else "sessions"
    traffic_count = actual_clicks if actual_clicks is not None else sessions
    transitions = [
        transition(traffic_name, traffic_count, "inquiries", inquiries),
        transition("inquiries", inquiries, "booked", stage_counts["booked"]),
        transition(
            "booked", stage_counts["booked"], "qualified", stage_counts["qualified"]
        ),
        transition(
            "qualified", stage_counts["qualified"], "won", stage_counts["won"]
        ),
    ]
    measurable = [item for item in transitions if item["measurable"]]
    weakest = min(measurable, key=lambda item: item["rate"]) if measurable else None
    for item in transitions:
        if item.get("reason", "").startswith("downstream exceeds upstream"):
            findings.add_iterate(
                f"{item['from']} -> {item['to']} is not a nested measurable cohort."
            )
    if weakest is None:
        findings.add_iterate("No complete adjacent funnel transition is measurable yet.")

    intent_completed = truthy(nested(config, "intentReview", "completed"))
    reviewed_clicks = integer_number(
        nested(config, "intentReview", "reviewedClicks")
    )
    qualified_intent_clicks = integer_number(
        nested(config, "intentReview", "qualifiedIntentClicks")
    )
    intent_minimum = finite_number(
        nested(config, "intentReview", "minimumQualifiedIntentRate")
    )
    intent_definition = str(
        nested(config, "intentReview", "definition") or ""
    ).strip()
    intent_rate: Optional[float] = None
    intent_passed = False
    if not intent_completed:
        findings.add_iterate("Qualified-intent review is not completed.")
    if not intent_definition:
        findings.add_iterate(
            "Qualified intent needs a written definition before review."
        )
    if reviewed_clicks is None or qualified_intent_clicks is None:
        findings.add_iterate(
            "Qualified-intent reviewed and qualified click counts are incomplete."
        )
    elif qualified_intent_clicks > reviewed_clicks:
        findings.add_pause("Qualified-intent clicks cannot exceed reviewed clicks.")
    elif reviewed_clicks == 0:
        findings.add_iterate(
            "Qualified intent cannot be established from zero reviewed clicks."
        )
    else:
        intent_rate = qualified_intent_clicks / reviewed_clicks
    if intent_minimum is None or not (0 <= intent_minimum <= 1):
        findings.add_pause(
            "minimumQualifiedIntentRate must be a number between 0 and 1."
        )
    if (
        actual_clicks is not None
        and reviewed_clicks is not None
        and reviewed_clicks != actual_clicks
    ):
        findings.add_iterate(
            "Intent review must reconcile to all eligible platform clicks."
        )
    if intent_rate is not None and intent_minimum is not None:
        if intent_rate < intent_minimum:
            findings.add_pause(
                f"Qualified-intent rate {intent_rate:.1%} is below the "
                f"declared {intent_minimum:.1%} minimum."
            )
        elif (
            qualified_intent_clicks
            and intent_completed
            and reviewed_clicks == actual_clicks
        ):
            intent_passed = True

    revenue = econ_values.get("average_contract_revenue")
    delivery_cost = econ_values.get("direct_delivery_cost")
    acquisition_share = econ_values.get("acceptable_acquisition_share")
    expected_show = econ_values.get("expected_show_rate")
    expected_qualification = econ_values.get("expected_qualification_rate")
    expected_close = econ_values.get("expected_close_rate")
    contribution_per_client: Optional[float] = None
    maximum_cac: Optional[float] = None
    maximum_cost_per_booking: Optional[float] = None
    if revenue is not None and delivery_cost is not None:
        contribution_per_client = revenue - delivery_cost
        if contribution_per_client <= 0:
            findings.add_pause(
                "Contribution profit per client must be greater than zero."
            )
    if contribution_per_client is not None and acquisition_share is not None:
        maximum_cac = contribution_per_client * acquisition_share
    if None not in (
        maximum_cac,
        expected_show,
        expected_qualification,
        expected_close,
    ):
        assert maximum_cac is not None
        assert expected_show is not None
        assert expected_qualification is not None
        assert expected_close is not None
        maximum_cost_per_booking = (
            maximum_cac
            * expected_show
            * expected_qualification
            * expected_close
        )
    if (
        override is not None
        and maximum_cost_per_booking is not None
        and override > maximum_cost_per_booking + 1e-9
    ):
        findings.add_pause(
            "maximum_cost_per_booked_call_override must be stricter than "
            "the calculated limit."
        )
    booking_cost_limit = (
        override if override is not None else maximum_cost_per_booking
    )

    booked = stage_counts["booked"]
    attended = stage_counts["attended"]
    qualified = stage_counts["qualified"]
    won = stage_counts["won"]
    actual_cost_per_booking = (
        actual_spend / booked
        if actual_spend is not None and booked is not None and booked > 0
        else None
    )
    actual_qualification_rate = (
        qualified / attended
        if qualified is not None and attended is not None and attended > 0
        else None
    )
    actual_contribution = econ_values.get("actual_contribution_profit")
    contribution_return = (
        actual_contribution / actual_spend
        if actual_contribution is not None
        and actual_spend is not None
        and actual_spend > 0
        else None
    )

    stop_rules: dict[str, str] = {}
    zero_booking_limit = econ_values.get("maximum_zero_booking_spend")
    if actual_spend is None or booked is None or zero_booking_limit is None:
        stop_rules["zeroBooking"] = "INPUTS_REQUIRED"
    elif booked == 0 and actual_spend >= zero_booking_limit:
        stop_rules["zeroBooking"] = "PAUSE"
        findings.add_pause(
            "Zero-booking spend reached the owner-declared pause threshold."
        )
    else:
        stop_rules["zeroBooking"] = "WITHIN_LIMIT"

    if actual_cost_per_booking is None or booking_cost_limit is None:
        stop_rules["bookingCost"] = "INPUTS_REQUIRED"
    elif actual_cost_per_booking > booking_cost_limit:
        stop_rules["bookingCost"] = "PAUSE"
        findings.add_pause(
            "Actual cost per booked call exceeds the declared economics limit."
        )
    else:
        stop_rules["bookingCost"] = "WITHIN_LIMIT"

    minimum_qualified_rate = econ_values.get("minimum_qualified_call_rate")
    if actual_qualification_rate is None or minimum_qualified_rate is None:
        stop_rules["qualification"] = "INPUTS_REQUIRED"
    elif actual_qualification_rate < minimum_qualified_rate:
        stop_rules["qualification"] = "PAUSE"
        findings.add_pause(
            "Actual held-to-qualified rate is below the declared minimum."
        )
    else:
        stop_rules["qualification"] = "WITHIN_LIMIT"

    minimum_return = econ_values.get("minimum_contribution_return")
    if won is None or minimum_wins is None:
        stop_rules["contributionReturn"] = "INPUTS_REQUIRED"
    elif won < minimum_wins:
        stop_rules["contributionReturn"] = "NOT_ENOUGH_EVIDENCE"
        findings.add_iterate(
            f"Won count {won} is below the owner-declared evidence threshold "
            f"{int(minimum_wins)}."
        )
    elif contribution_return is None or minimum_return is None:
        stop_rules["contributionReturn"] = "INPUTS_REQUIRED"
    elif contribution_return < minimum_return:
        stop_rules["contributionReturn"] = "PAUSE"
        findings.add_pause(
            "Contribution return is below the owner-declared minimum."
        )
    else:
        stop_rules["contributionReturn"] = "WITHIN_LIMIT"

    if not truthy(config.get("testComplete")):
        findings.add_iterate(
            "testComplete is not confirmed; the report is an in-progress review."
        )
    if not intent_passed:
        findings.add_iterate("Qualified-intent gate has not passed.")
    if any(value != "WITHIN_LIMIT" for value in stop_rules.values()):
        findings.add_iterate(
            "Every economics stop rule must be within its declared limit."
        )

    economics_complete = all(
        econ_values.get(key) is not None for key in PLANNING_INPUTS + ACTUAL_INPUTS
    )
    if not economics_complete:
        findings.add_iterate(
            "All required planning and actual economics inputs must be "
            "completed and reconciled."
        )

    generated = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    verdict = findings.verdict
    assert verdict in VERDICTS
    return {
        "schemaVersion": 1,
        "generatedAt": generated,
        "verdict": verdict,
        "decisionBoundary": (
            "Human review only. This report never launches, increases, "
            "or changes advertising."
        ),
        "window": {
            "startDate": start.isoformat() if start else None,
            "endDate": end.isoformat() if end else None,
            "calendarDays": actual_days,
        },
        "controls": {
            "hardMediaCapUsd": HARD_MEDIA_CAP_USD,
            "hardDurationCapDays": HARD_DURATION_CAP_DAYS,
            "manifestMediaCapUsd": limit_budget,
            "manifestDurationDays": limit_days,
            "actualSpendUsd": actual_spend,
            "enforcedSpendCeilingUsd": spend_ceiling,
        },
        "scope": {
            "mode": mode,
            "utmCampaign": campaign or None,
            "utmSource": source or None,
        },
        "funnel": {
            "clicks": actual_clicks,
            "sessions": sessions,
            "inquiries": inquiries,
            "booked": stage_counts["booked"],
            "qualified": stage_counts["qualified"],
            "won": stage_counts["won"],
            "trafficBase": traffic_name,
            "transitions": transitions,
            "weakestMeasurableTransition": weakest,
        },
        "intentReview": {
            "completed": intent_completed,
            "reviewedClicks": reviewed_clicks,
            "qualifiedIntentClicks": qualified_intent_clicks,
            "qualifiedIntentRate": intent_rate,
            "minimumQualifiedIntentRate": intent_minimum,
            "passed": intent_passed,
        },
        "economics": {
            "inputsComplete": economics_complete,
            "contributionProfitPerClientUsd": contribution_per_client,
            "maximumCustomerAcquisitionCostUsd": maximum_cac,
            "maximumCostPerBookedCallUsd": maximum_cost_per_booking,
            "effectiveCostPerBookedCallLimitUsd": booking_cost_limit,
            "actualCostPerBookedCallUsd": actual_cost_per_booking,
            "actualHeldToQualifiedRate": actual_qualification_rate,
            "actualContributionReturn": contribution_return,
            "stopRules": stop_rules,
        },
        "data": {
            "events": {
                "available": events.available,
                "recordsRead": len(events.records),
                "scopedRecords": len(scoped_events),
                "sessionlessPageViews": sessionless_page_views,
                "qaRecordsExcluded": qa_event_records_excluded,
                "qaSessionsExcluded": len(excluded_qa_sessions),
            },
            "leads": {
                "available": leads.available,
                "recordsRead": len(leads.records),
                "scopedRecords": len(scoped_leads),
                "syntheticRecordsExcluded": synthetic_leads_excluded,
                "qaRecordsExcluded": qa_lead_records_excluded,
                "qaReceiptIdsConfigured": len(qa_receipt_ids),
            },
            "acquisition": {
                "available": acquisition.available,
                "recordsRead": len(acquisition.records),
                "scopedStageRecords": len(scoped_acquisition),
                "attended": stage_counts["attended"],
                "qaExclusionRecordsRead": qa_exclusion_records_read,
                "qaExclusionTargetsConfigured": len(qa_receipt_ids)
                + len(qa_booking_uids),
                "qaBookingUidsConfigured": len(qa_booking_uids),
            },
        },
        "findings": {
            "pause": findings.pause,
            "iterate": findings.iterate,
            "notes": findings.notes,
        },
    }


def fmt_count(value: Any) -> str:
    return "unknown" if value is None else str(value)


def fmt_rate(value: Any) -> str:
    return "not measurable" if value is None else f"{float(value):.1%}"


def render_text(report: dict[str, Any]) -> str:
    funnel = report["funnel"]
    lines = [
        f"ACQUISITION DECISION: {report['verdict']}",
        report["decisionBoundary"],
        "",
        "FUNNEL",
        f"  clicks:    {fmt_count(funnel['clicks'])}",
        f"  sessions:  {fmt_count(funnel['sessions'])}",
        f"  inquiries: {fmt_count(funnel['inquiries'])}",
        f"  booked:    {fmt_count(funnel['booked'])}",
        f"  qualified: {fmt_count(funnel['qualified'])}",
        f"  won:       {fmt_count(funnel['won'])}",
        "",
        "TRANSITIONS",
    ]
    for item in funnel["transitions"]:
        detail = (
            fmt_rate(item["rate"])
            if item["measurable"]
            else item.get("reason", "not measurable")
        )
        lines.append(f"  {item['from']} -> {item['to']}: {detail}")
    weakest = funnel["weakestMeasurableTransition"]
    if weakest:
        lines.append(
            f"  weakest measurable: {weakest['from']} -> {weakest['to']} "
            f"({fmt_rate(weakest['rate'])})"
        )
    else:
        lines.append("  weakest measurable: unavailable")

    lines.extend(["", "ECONOMICS STOP RULES"])
    for key, value in report["economics"]["stopRules"].items():
        lines.append(f"  {key}: {value}")
    for heading, key in (("PAUSE", "pause"), ("ITERATE", "iterate")):
        reasons = report["findings"][key]
        if reasons:
            lines.extend(["", heading + " REASONS"])
            lines.extend(f"  - {reason}" for reason in reasons)
    return "\n".join(lines) + "\n"


def error_report(message: str) -> dict[str, Any]:
    generated = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return {
        "schemaVersion": 1,
        "generatedAt": generated,
        "verdict": "PAUSE",
        "decisionBoundary": (
            "Human review only. This report never launches, increases, "
            "or changes advertising."
        ),
        "findings": {"pause": [message], "iterate": [], "notes": []},
    }


def main(argv: Optional[list[str]] = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run", type=Path, default=root / "data/acquisition-ops-run.json"
    )
    parser.add_argument(
        "--economics",
        type=Path,
        default=root / "data/acquisition-ops-economics.csv",
    )
    parser.add_argument(
        "--events", type=Path, default=root / "data/events.jsonl"
    )
    parser.add_argument(
        "--leads", type=Path, default=root / "data/leads.jsonl"
    )
    parser.add_argument(
        "--acquisition", type=Path, default=root / "data/acquisition.jsonl"
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        config = read_json(args.run)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        report = error_report(f"Cannot read run manifest {args.run}: {error}")
    else:
        economics, economics_errors = read_economics(args.economics)
        report = build_report(
            config,
            economics,
            read_jsonl(args.events),
            read_jsonl(args.leads),
            read_jsonl(args.acquisition),
        )
        for error in economics_errors:
            if error not in report["findings"]["pause"]:
                report["findings"]["pause"].append(error)
        if economics_errors:
            report["verdict"] = "PAUSE"

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    elif "funnel" in report:
        sys.stdout.write(render_text(report))
    else:
        sys.stdout.write(
            f"ACQUISITION DECISION: PAUSE\n{report['decisionBoundary']}\n\n"
            "PAUSE REASONS\n"
            + "\n".join(
                f"  - {reason}" for reason in report["findings"]["pause"]
            )
            + "\n"
        )
    return 2 if report["verdict"] == "PAUSE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
