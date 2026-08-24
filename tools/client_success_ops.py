#!/usr/bin/env python3
"""Fail-closed case-study, review-request, and referral draft operations.

This tool has deliberately no delivery integration. A completed project creates
three local queue drafts; a person must review and send them elsewhere.

    python3 tools/client_success_ops.py check
    python3 tools/client_success_ops.py case-study-status
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SLOTS = ROOT / "content" / "client-success" / "case-study-slots.json"
DEFAULT_STATE = ROOT / "data" / "client-success.json"
DEFAULT_QUEUE = ROOT / "data" / "client-success-queue.json"

SCHEMA_VERSION = 1
SLOT_STATUSES = {"EMPTY", "INTAKE", "AWAITING_CLIENT_APPROVAL", "APPROVED"}
APPROVAL_STATUSES = {"NOT_REQUESTED", "REQUESTED", "APPROVED"}
PROJECT_STATUSES = {"ACTIVE", "COMPLETED"}
REQUEST_KINDS = (
    "GOOGLE_REVIEW_REQUEST",
    "LINKEDIN_RECOMMENDATION_REQUEST",
    "REFERRAL_REQUEST",
)
QUEUE_STATUSES = {
    "BLOCKED_MISSING_VERIFIED_URL",
    "DRAFT_READY_FOR_MANUAL_REVIEW",
}
INCENTIVE_WORDS = ("discount", "incentive", "gift", "credit", "coupon", "compensation", "refund")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class OpsError(Exception):
    """A user-correctable validation or workflow error."""


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise OpsError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise OpsError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise OpsError(f"top level must be an object: {path}")
    return value


def write_json_atomic(path: Path, value: dict) -> None:
    """Write local state atomically; never touch testimonial source drafts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temp_name = handle.name
    try:
        with handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def nonblank(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def valid_date_or_datetime(value: object) -> bool:
    if not nonblank(value):
        return False
    text = str(value).strip()
    try:
        if len(text) == 10:
            date.fromisoformat(text)
        else:
            datetime.fromisoformat(text.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def evidence_file(value: object) -> Path | None:
    if not nonblank(value):
        return None
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path


def require_evidence(value: object, label: str, errors: list[str]) -> None:
    path = evidence_file(value)
    if path is None:
        errors.append(f"{label}: evidence path is required")
    elif not path.is_file():
        errors.append(f"{label}: evidence file does not exist: {value}")


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def publication_digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def validate_url(value: str, kind: str) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        return f"{kind} URL must be a verified https URL without embedded credentials"
    if kind == "google":
        valid = host in {
            "google.com",
            "www.google.com",
            "maps.google.com",
            "search.google.com",
            "maps.app.goo.gl",
            "g.page",
        }
        if not valid:
            return "Google review URL must use a verified Google or g.page host"
    elif kind == "linkedin":
        if host != "linkedin.com" and not host.endswith(".linkedin.com"):
            return "LinkedIn recommendation URL must use a verified linkedin.com host"
    return None


def expected_slot_approval_status(slot_status: str) -> str:
    return {
        "EMPTY": "NOT_REQUESTED",
        "INTAKE": "NOT_REQUESTED",
        "AWAITING_CLIENT_APPROVAL": "REQUESTED",
        "APPROVED": "APPROVED",
    }.get(slot_status, "")


def validate_fact_block(block: object, label: str, errors: list[str]) -> None:
    if not isinstance(block, dict):
        errors.append(f"{label}: must be an object")
        return
    if not nonblank(block.get("fact")):
        errors.append(f"{label}: fact is required")
    if not valid_date_or_datetime(block.get("observed_at")):
        errors.append(f"{label}: observed_at must be an ISO date or datetime")
    paths = block.get("evidence_paths")
    if not isinstance(paths, list) or not paths:
        errors.append(f"{label}: at least one evidence path is required")
    else:
        for index, path in enumerate(paths):
            require_evidence(path, f"{label}.evidence_paths[{index}]", errors)


def validate_metric(metric: object, label: str, errors: list[str]) -> None:
    if not isinstance(metric, dict):
        errors.append(f"{label}: must be an object")
        return
    for field in ("name", "unit", "before", "after"):
        if not nonblank(metric.get(field)):
            errors.append(f"{label}.{field}: required when a metric is included")
    paths = metric.get("evidence_paths")
    if not isinstance(paths, list) or not paths:
        errors.append(f"{label}: metric evidence is required")
    else:
        for index, path in enumerate(paths):
            require_evidence(path, f"{label}.evidence_paths[{index}]", errors)


def validate_ready_slot(slot: dict, label: str, errors: list[str]) -> None:
    for field in ("project_id", "project_label", "client_display_label"):
        if not nonblank(slot.get(field)):
            errors.append(f"{label}.{field}: required after intake begins")
    if nonblank(slot.get("project_id")) and not SLUG_RE.fullmatch(str(slot["project_id"])):
        errors.append(f"{label}.project_id: use a lowercase hyphenated slug")

    validate_fact_block(slot.get("before"), f"{label}.before", errors)
    validate_fact_block(slot.get("after"), f"{label}.after", errors)

    metrics = slot.get("metrics")
    if not isinstance(metrics, list):
        errors.append(f"{label}.metrics: must be a list")
    else:
        for index, metric in enumerate(metrics):
            validate_metric(metric, f"{label}.metrics[{index}]", errors)

    screenshots = slot.get("screenshots")
    usable_screenshots: list[dict] = []
    if not isinstance(screenshots, list):
        errors.append(f"{label}.screenshots: must be a list")
    else:
        for index, screenshot in enumerate(screenshots):
            if not isinstance(screenshot, dict):
                errors.append(f"{label}.screenshots[{index}]: must be an object")
                continue
            if not any(nonblank(screenshot.get(key)) for key in ("path", "caption", "captured_at")):
                continue
            usable_screenshots.append(screenshot)
            if screenshot.get("stage") not in {"before", "after", "result", "process"}:
                errors.append(f"{label}.screenshots[{index}].stage: invalid stage")
            for field in ("path", "caption", "captured_at", "permission_evidence_path"):
                if not nonblank(screenshot.get(field)):
                    errors.append(f"{label}.screenshots[{index}].{field}: required")
            if nonblank(screenshot.get("captured_at")) and not valid_date_or_datetime(screenshot["captured_at"]):
                errors.append(f"{label}.screenshots[{index}].captured_at: invalid ISO date")
            require_evidence(screenshot.get("path"), f"{label}.screenshots[{index}].path", errors)
            require_evidence(
                screenshot.get("permission_evidence_path"),
                f"{label}.screenshots[{index}].permission_evidence_path",
                errors,
            )
    if not usable_screenshots:
        errors.append(f"{label}: at least one evidenced, permission-cleared screenshot is required")

    approval = slot.get("approval")
    if not isinstance(approval, dict):
        errors.append(f"{label}.approval: must be an object")
        return
    draft = approval.get("draft_publication")
    if not isinstance(draft, dict):
        errors.append(f"{label}.approval.draft_publication: must be an object")
        return
    for field in ("title", "before_fact", "after_fact", "quote", "attribution", "placement"):
        if not nonblank(draft.get(field)):
            errors.append(f"{label}.approval.draft_publication.{field}: required")
    if isinstance(slot.get("before"), dict) and draft.get("before_fact") != slot["before"].get("fact"):
        errors.append(f"{label}: draft before_fact must exactly match the evidenced intake fact")
    if isinstance(slot.get("after"), dict) and draft.get("after_fact") != slot["after"].get("fact"):
        errors.append(f"{label}: draft after_fact must exactly match the evidenced intake fact")
    screenshot_paths = draft.get("screenshot_paths")
    expected_paths = sorted(
        screenshot.get("path", "") for screenshot in usable_screenshots if nonblank(screenshot.get("path"))
    )
    if not isinstance(screenshot_paths, list) or sorted(screenshot_paths) != expected_paths:
        errors.append(f"{label}: draft screenshot_paths must exactly list the evidenced screenshots")


def validate_approved_slot(slot: dict, label: str, errors: list[str]) -> None:
    approval = slot.get("approval")
    if not isinstance(approval, dict):
        return
    draft = approval.get("draft_publication")
    approved = approval.get("approved_publication")
    if not isinstance(draft, dict) or not isinstance(approved, dict):
        errors.append(f"{label}: draft and approved publication packages must be objects")
        return
    if approved != draft:
        errors.append(f"{label}: approved publication must exactly equal the client-reviewed draft")
    expected_digest = publication_digest(draft)
    if approval.get("packet_sha256") != expected_digest:
        errors.append(f"{label}: packet_sha256 does not match the exact approved publication")
    if not valid_date_or_datetime(approval.get("approved_at")):
        errors.append(f"{label}.approval.approved_at: valid ISO approval date is required")
    require_evidence(
        approval.get("approval_evidence_path"),
        f"{label}.approval.approval_evidence_path",
        errors,
    )
    if nonblank(draft.get("rating")):
        require_evidence(
            approval.get("rating_evidence_path"),
            f"{label}.approval.rating_evidence_path",
            errors,
        )


def validate_slots(document: dict) -> tuple[list[str], dict[str, bool]]:
    errors: list[str] = []
    ready: dict[str, bool] = {}
    if document.get("schema_version") != SCHEMA_VERSION:
        errors.append("case-study slots: unsupported schema_version")
    slots = document.get("slots")
    if not isinstance(slots, list) or not 2 <= len(slots) <= 3:
        errors.append("case-study slots: exactly two or three intake slots are required")
        return errors, ready
    ids: set[str] = set()
    for index, slot in enumerate(slots):
        label = f"slots[{index}]"
        if not isinstance(slot, dict):
            errors.append(f"{label}: must be an object")
            continue
        slot_id = slot.get("slot_id")
        if not nonblank(slot_id) or not SLUG_RE.fullmatch(str(slot_id)):
            errors.append(f"{label}.slot_id: use a lowercase hyphenated slug")
            slot_id = label
        elif slot_id in ids:
            errors.append(f"{label}.slot_id: duplicate {slot_id}")
        ids.add(str(slot_id))
        status = slot.get("status")
        if status not in SLOT_STATUSES:
            errors.append(f"{label}.status: invalid status")
            ready[str(slot_id)] = False
            continue
        approval = slot.get("approval")
        approval_status = approval.get("status") if isinstance(approval, dict) else None
        if approval_status not in APPROVAL_STATUSES:
            errors.append(f"{label}.approval.status: invalid status")
        expected = expected_slot_approval_status(str(status))
        if approval_status != expected:
            errors.append(f"{label}: {status} requires approval.status {expected}")
        before = len(errors)
        if status in {"AWAITING_CLIENT_APPROVAL", "APPROVED"}:
            validate_ready_slot(slot, label, errors)
        if status == "APPROVED":
            validate_approved_slot(slot, label, errors)
        ready[str(slot_id)] = status == "APPROVED" and len(errors) == before
    return errors, ready


def find_project(state: dict, project_id: str) -> dict:
    for project in state.get("projects", []):
        if isinstance(project, dict) and project.get("project_id") == project_id:
            return project
    raise OpsError(f"unknown project_id: {project_id}")


def validate_state(state: dict) -> list[str]:
    errors: list[str] = []
    if state.get("schema_version") != SCHEMA_VERSION:
        errors.append("client-success state: unsupported schema_version")
    projects = state.get("projects")
    if not isinstance(projects, list):
        return errors + ["client-success state: projects must be a list"]
    ids: set[str] = set()
    for index, project in enumerate(projects):
        label = f"projects[{index}]"
        if not isinstance(project, dict):
            errors.append(f"{label}: must be an object")
            continue
        project_id = project.get("project_id")
        if not nonblank(project_id) or not SLUG_RE.fullmatch(str(project_id)):
            errors.append(f"{label}.project_id: use a lowercase hyphenated slug")
        elif project_id in ids:
            errors.append(f"{label}.project_id: duplicate {project_id}")
        ids.add(str(project_id))
        for field in ("project_label", "client_first_name", "contact_ref", "created_at"):
            if not nonblank(project.get(field)):
                errors.append(f"{label}.{field}: required")
        if nonblank(project.get("created_at")) and not valid_date_or_datetime(project["created_at"]):
            errors.append(f"{label}.created_at: invalid ISO date")
        status = project.get("status")
        if status not in PROJECT_STATUSES:
            errors.append(f"{label}.status: invalid status")
        review_urls = project.get("review_urls")
        if not isinstance(review_urls, dict):
            errors.append(f"{label}.review_urls: must be an object")
        else:
            for kind in ("google", "linkedin"):
                value = review_urls.get(kind, "")
                if not isinstance(value, str):
                    errors.append(f"{label}.review_urls.{kind}: must be a string")
                elif value:
                    url_error = validate_url(value, kind)
                    if url_error:
                        errors.append(f"{label}.review_urls.{kind}: {url_error}")
        if status == "COMPLETED":
            if not valid_date_or_datetime(project.get("completed_at")):
                errors.append(f"{label}.completed_at: valid completion date is required")
            require_evidence(
                project.get("completion_evidence_path"),
                f"{label}.completion_evidence_path",
                errors,
            )
            if not valid_date_or_datetime(project.get("requests_triggered_at")):
                errors.append(f"{label}.requests_triggered_at: required for completed projects")
    return errors


def request_url(project: dict, kind: str) -> str:
    urls = project.get("review_urls", {})
    if kind == "GOOGLE_REVIEW_REQUEST":
        return str(urls.get("google", ""))
    if kind == "LINKEDIN_RECOMMENDATION_REQUEST":
        return str(urls.get("linkedin", ""))
    return ""


def request_copy(project: dict, kind: str) -> tuple[str, str, int]:
    name = project["client_first_name"]
    project_label = project["project_label"]
    url = request_url(project, kind)
    if kind == "GOOGLE_REVIEW_REQUEST":
        link = url or "[VERIFIED_GOOGLE_REVIEW_URL_REQUIRED]"
        return (
            f"An honest Google review for {project_label}",
            f"Hi {name} — now that {project_label} is complete, would you be willing to leave "
            "an honest Google review about the work and process? Positive, mixed, or critical "
            f"feedback is welcome. {link} No pressure, and please describe only your direct experience.",
            2,
        )
    if kind == "LINKEDIN_RECOMMENDATION_REQUEST":
        link = url or "[VERIFIED_LINKEDIN_RECOMMENDATION_URL_REQUIRED]"
        return (
            f"An honest LinkedIn recommendation for {project_label}",
            f"Hi {name} — if it is useful, would you be willing to write an honest LinkedIn "
            f"recommendation about our work on {project_label}? Positive, mixed, or critical "
            f"feedback is welcome. {link} No pressure, and please describe only your direct experience.",
            9,
        )
    return (
        f"One introduction after {project_label}",
        f"Hi {name} — if one person comes to mind who has a problem similar to the one we addressed "
        f"in {project_label}, and you genuinely think we would be a fit, would you be comfortable "
        "making one introduction? No pressure at all; a simple reply is enough, and I will take it from there.",
        16,
    )


def build_queue_item(project: dict, kind: str, created_at: str) -> dict:
    url = request_url(project, kind)
    subject, body, delay = request_copy(project, kind)
    needs_url = kind != "REFERRAL_REQUEST"
    return {
        "queue_id": f"{project['project_id']}--{kind.lower().replace('_', '-')}",
        "project_id": project["project_id"],
        "kind": kind,
        "trigger": "PROJECT_COMPLETED",
        "status": (
            "BLOCKED_MISSING_VERIFIED_URL"
            if needs_url and not url
            else "DRAFT_READY_FOR_MANUAL_REVIEW"
        ),
        "suggested_delay_days": delay,
        "recipient_contact_ref": project["contact_ref"],
        "verified_url": url,
        "draft_subject": subject,
        "draft_body": body,
        "created_at": created_at,
        "delivery_mode": "DRAFT_ONLY",
        "manual_review_required": True,
        "incentive_attached": False,
        "send_authorized": False,
        "sent_at": "",
    }


def upsert_project_queue(queue: dict, project: dict, created_at: str) -> None:
    items = queue.setdefault("items", [])
    existing = {
        item.get("queue_id"): index
        for index, item in enumerate(items)
        if isinstance(item, dict)
    }
    for kind in REQUEST_KINDS:
        item = build_queue_item(project, kind, created_at)
        index = existing.get(item["queue_id"])
        if index is None:
            items.append(item)
        else:
            original_created_at = items[index].get("created_at") or created_at
            item["created_at"] = original_created_at
            items[index] = item


def validate_queue(queue: dict, state: dict) -> list[str]:
    errors: list[str] = []
    if queue.get("schema_version") != SCHEMA_VERSION:
        errors.append("client-success queue: unsupported schema_version")
    items = queue.get("items")
    if not isinstance(items, list):
        return errors + ["client-success queue: items must be a list"]
    projects = {
        project.get("project_id"): project
        for project in state.get("projects", [])
        if isinstance(project, dict)
    }
    ids: set[str] = set()
    by_project: dict[str, list[dict]] = {}
    for index, item in enumerate(items):
        label = f"queue.items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label}: must be an object")
            continue
        queue_id = item.get("queue_id")
        if not nonblank(queue_id) or queue_id in ids:
            errors.append(f"{label}.queue_id: missing or duplicate")
        ids.add(str(queue_id))
        project = projects.get(item.get("project_id"))
        if project is None:
            errors.append(f"{label}: unknown project_id")
            continue
        by_project.setdefault(str(item.get("project_id")), []).append(item)
        kind = item.get("kind")
        if kind not in REQUEST_KINDS:
            errors.append(f"{label}.kind: invalid request kind")
            continue
        if item.get("trigger") != "PROJECT_COMPLETED":
            errors.append(f"{label}.trigger: must be PROJECT_COMPLETED")
        if item.get("delivery_mode") != "DRAFT_ONLY":
            errors.append(f"{label}.delivery_mode: must remain DRAFT_ONLY")
        if item.get("manual_review_required") is not True:
            errors.append(f"{label}: manual review must remain required")
        if item.get("incentive_attached") is not False:
            errors.append(f"{label}: reviews and referrals may never carry an incentive")
        if item.get("send_authorized") is not False or item.get("sent_at") != "":
            errors.append(f"{label}: this queue may never authorize or record sending")
        if item.get("status") not in QUEUE_STATUSES:
            errors.append(f"{label}.status: invalid queue status")
        if not valid_date_or_datetime(item.get("created_at")):
            errors.append(f"{label}.created_at: invalid ISO date")
        if not isinstance(item.get("suggested_delay_days"), int):
            errors.append(f"{label}.suggested_delay_days: must be an integer")
        if not nonblank(item.get("draft_subject")) or not nonblank(item.get("draft_body")):
            errors.append(f"{label}: draft subject and body are required")
        body = str(item.get("draft_body", ""))
        if "five-star" in body.lower() or "positive review" in body.lower():
            errors.append(f"{label}: review requests may not condition sentiment")
        present_incentives = [word for word in INCENTIVE_WORDS if word in body.lower()]
        if present_incentives:
            errors.append(
                f"{label}: request copy must stay separate from incentive terms: {present_incentives}"
            )
        expected_url = request_url(project, str(kind))
        if item.get("verified_url") != expected_url:
            errors.append(f"{label}: verified_url must match the user-supplied project URL")
        needs_url = kind != "REFERRAL_REQUEST"
        expected_status = (
            "BLOCKED_MISSING_VERIFIED_URL"
            if needs_url and not expected_url
            else "DRAFT_READY_FOR_MANUAL_REVIEW"
        )
        if item.get("status") != expected_status:
            errors.append(f"{label}: incorrect fail-closed queue status")
        if needs_url and expected_url and expected_url not in body:
            errors.append(f"{label}: draft must contain the exact verified URL")
        if needs_url and not expected_url and "https://" in body:
            errors.append(f"{label}: draft contains a URL that was not supplied and verified")
        if kind == "REFERRAL_REQUEST" and item.get("verified_url"):
            errors.append(f"{label}: referral request must not invent or require a URL")

    for project_id, project in projects.items():
        project_items = by_project.get(str(project_id), [])
        if project.get("status") == "COMPLETED":
            kinds = [item.get("kind") for item in project_items]
            if sorted(kinds) != sorted(REQUEST_KINDS):
                errors.append(
                    f"project {project_id}: completion must queue exactly Google, LinkedIn, and one referral draft"
                )
        elif project_items:
            errors.append(f"project {project_id}: active projects may not have completion drafts")
    return errors


def all_checks(slots_path: Path, state_path: Path, queue_path: Path) -> tuple[list[str], dict[str, bool]]:
    slots = load_json(slots_path)
    state = load_json(state_path)
    queue = load_json(queue_path)
    slot_errors, ready = validate_slots(slots)
    return slot_errors + validate_state(state) + validate_queue(queue, state), ready


def command_check(args: argparse.Namespace) -> int:
    errors, ready = all_checks(args.slots, args.state, args.queue)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    ready_count = sum(ready.values())
    print(
        "client-success check passed — "
        f"{len(ready)} case-study slots, {ready_count} publication-ready; queue is draft-only"
    )
    return 0


def command_init(args: argparse.Namespace) -> int:
    """Create ignored runtime state without overwriting an existing queue."""
    created: list[str] = []
    for path, value in (
        (args.state, {"schema_version": SCHEMA_VERSION, "projects": []}),
        (args.queue, {"schema_version": SCHEMA_VERSION, "items": []}),
    ):
        if path.exists():
            load_json(path)
            continue
        write_json_atomic(path, value)
        created.append(str(path))
    errors, _ = all_checks(args.slots, args.state, args.queue)
    if errors:
        raise OpsError("initialized files are invalid:\n- " + "\n- ".join(errors))
    if created:
        print(f"initialized {len(created)} ignored runtime file(s); no projects or drafts created")
    else:
        print("runtime files already exist and were left unchanged")
    return 0


def command_case_study_status(args: argparse.Namespace) -> int:
    document = load_json(args.slots)
    errors, ready = validate_slots(document)
    for slot in document.get("slots", []):
        if isinstance(slot, dict):
            slot_id = slot.get("slot_id", "unknown")
            print(f"{slot_id}: {slot.get('status', 'INVALID')} — publish_ready={str(ready.get(slot_id, False)).lower()}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


def command_approval_packet(args: argparse.Namespace) -> int:
    document = load_json(args.slots)
    slots = document.get("slots", [])
    slot = next(
        (value for value in slots if isinstance(value, dict) and value.get("slot_id") == args.slot_id),
        None,
    )
    if slot is None:
        raise OpsError(f"unknown slot_id: {args.slot_id}")
    errors: list[str] = []
    validate_ready_slot(slot, f"slot {args.slot_id}", errors)
    if errors:
        raise OpsError("approval packet is blocked:\n- " + "\n- ".join(errors))
    draft = slot["approval"]["draft_publication"]
    digest = publication_digest(draft)
    print("CUSTOMER APPROVAL REQUIRED — NOTHING IS APPROVED BY THIS COMMAND")
    print(json.dumps(draft, ensure_ascii=False, indent=2))
    print(f"packet_sha256: {digest}")
    print(
        "Ask the client to approve this exact title, facts, quote, attribution, rating, "
        "screenshots, and placement. Save their reply privately before marking APPROVED."
    )
    return 0


def command_add_project(args: argparse.Namespace) -> int:
    state = load_json(args.state)
    queue = load_json(args.queue)
    if validate_state(state) or validate_queue(queue, state):
        raise OpsError("existing state or queue is invalid; run check before adding a project")
    if not SLUG_RE.fullmatch(args.project_id):
        raise OpsError("project-id must be a lowercase hyphenated slug")
    if any(project.get("project_id") == args.project_id for project in state["projects"]):
        raise OpsError(f"project already exists: {args.project_id}")
    for kind, value in (("google", args.google_review_url), ("linkedin", args.linkedin_url)):
        if value:
            error = validate_url(value, kind)
            if error:
                raise OpsError(error)
    state["projects"].append(
        {
            "project_id": args.project_id,
            "project_label": args.project_label.strip(),
            "client_first_name": args.client_first_name.strip(),
            "contact_ref": args.contact_ref.strip(),
            "status": "ACTIVE",
            "created_at": now_utc(),
            "completed_at": "",
            "completion_evidence_path": "",
            "requests_triggered_at": "",
            "review_urls": {
                "google": args.google_review_url,
                "linkedin": args.linkedin_url,
            },
        }
    )
    errors = validate_state(state)
    if errors:
        raise OpsError("project is invalid:\n- " + "\n- ".join(errors))
    write_json_atomic(args.state, state)
    print(f"added active project {args.project_id}; no requests queued before completion")
    return 0


def command_set_review_links(args: argparse.Namespace) -> int:
    if not args.google_review_url and not args.linkedin_url:
        raise OpsError("supply at least one verified review URL")
    state = load_json(args.state)
    queue = load_json(args.queue)
    project = find_project(state, args.project_id)
    updates = (
        ("google", args.google_review_url),
        ("linkedin", args.linkedin_url),
    )
    for kind, value in updates:
        if not value:
            continue
        error = validate_url(value, kind)
        if error:
            raise OpsError(error)
        project["review_urls"][kind] = value
    if project.get("status") == "COMPLETED":
        upsert_project_queue(queue, project, project["requests_triggered_at"])
    errors = validate_state(state) + validate_queue(queue, state)
    if errors:
        raise OpsError("updated state is invalid:\n- " + "\n- ".join(errors))
    write_json_atomic(args.state, state)
    write_json_atomic(args.queue, queue)
    print(f"stored verified review link(s) for {args.project_id}; drafts remain unsent")
    return 0


def command_complete_project(args: argparse.Namespace) -> int:
    if not valid_date_or_datetime(args.completed_at):
        raise OpsError("completed-at must be an ISO date or datetime")
    evidence = evidence_file(args.completion_evidence)
    if evidence is None or not evidence.is_file():
        raise OpsError("completion-evidence must point to an existing evidence file")
    state = load_json(args.state)
    queue = load_json(args.queue)
    project = find_project(state, args.project_id)
    triggered_at = project.get("requests_triggered_at") or now_utc()
    if project.get("status") == "COMPLETED":
        if project.get("completed_at") != args.completed_at:
            raise OpsError("project is already completed with a different completion date")
        if project.get("completion_evidence_path") != args.completion_evidence:
            raise OpsError("project is already completed with a different evidence path")
    else:
        project["status"] = "COMPLETED"
        project["completed_at"] = args.completed_at
        project["completion_evidence_path"] = args.completion_evidence
        project["requests_triggered_at"] = triggered_at
    upsert_project_queue(queue, project, triggered_at)
    errors = validate_state(state) + validate_queue(queue, state)
    if errors:
        raise OpsError("completion is blocked:\n- " + "\n- ".join(errors))
    # Queue first: if the second replace fails, rerunning is idempotent and repairs state.
    write_json_atomic(args.queue, queue)
    write_json_atomic(args.state, state)
    project_items = [item for item in queue["items"] if item["project_id"] == args.project_id]
    blocked = sum(item["status"] == "BLOCKED_MISSING_VERIFIED_URL" for item in project_items)
    print(
        f"completion recorded for {args.project_id}; 3 local drafts queued, {blocked} blocked "
        "for missing verified URLs, 0 sent"
    )
    return 0


def path_arg(value: str) -> Path:
    return Path(value).expanduser().resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slots", type=path_arg, default=DEFAULT_SLOTS)
    parser.add_argument("--state", type=path_arg, default=DEFAULT_STATE)
    parser.add_argument("--queue", type=path_arg, default=DEFAULT_QUEUE)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="validate slots, state, and fail-closed queue")
    check.set_defaults(handler=command_check)

    init = subparsers.add_parser("init", help="create empty ignored runtime state if missing")
    init.set_defaults(handler=command_init)

    status = subparsers.add_parser("case-study-status", help="show computed publication readiness")
    status.set_defaults(handler=command_case_study_status)

    packet = subparsers.add_parser("approval-packet", help="print exact client approval payload")
    packet.add_argument("--slot-id", required=True)
    packet.set_defaults(handler=command_approval_packet)

    add = subparsers.add_parser("add-project", help="add an active project without queuing requests")
    add.add_argument("--project-id", required=True)
    add.add_argument("--project-label", required=True)
    add.add_argument("--client-first-name", required=True)
    add.add_argument("--contact-ref", required=True)
    add.add_argument("--google-review-url", default="")
    add.add_argument("--linkedin-url", default="")
    add.set_defaults(handler=command_add_project)

    links = subparsers.add_parser("set-review-links", help="store user-verified review URLs")
    links.add_argument("--project-id", required=True)
    links.add_argument("--google-review-url", default="")
    links.add_argument("--linkedin-url", default="")
    links.set_defaults(handler=command_set_review_links)

    complete = subparsers.add_parser(
        "complete-project",
        help="record evidenced completion and queue three unsent drafts",
    )
    complete.add_argument("--project-id", required=True)
    complete.add_argument("--completed-at", required=True)
    complete.add_argument("--completion-evidence", required=True)
    complete.set_defaults(handler=command_complete_project)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except OpsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
