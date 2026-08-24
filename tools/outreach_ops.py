#!/usr/bin/env python3
"""Prepare one-to-one contractor teardown drafts without sending anything.

Real prospect data and generated queues live under ``private/`` and are ignored
by Git. This program intentionally has no mail, browser, CRM, or network client.
It can prepare and track review state; a person must research the recipient,
complete compliance fields, approve the copy, and send it separately.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlencode, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "private" / "prospect-candidates-2026-08-23.csv"
DEFAULT_STATE = ROOT / "private" / "outreach-state.csv"
DEFAULT_QUEUE = ROOT / "private" / "outreach-queue"
REQUIRED_FIELDS = (
    "business_name",
    "wedge",
    "city",
    "website",
    "contact_page_url",
    "observable_workflow_friction",
    "suggested_outreach_angle",
    "language_signal",
    "verified_date",
    "source_url",
)
STATE_FIELDS = (
    "candidate_id",
    "business_name",
    "website",
    "wedge",
    "queue_date",
    "status",
    "last_action_date",
    "do_not_contact",
    "notes",
)
ALLOWED_STATUSES = {
    "queued",
    "reviewed",
    "sent",
    "replied",
    "qualified",
    "closed",
    "opt_out",
}
BLOCKED_STATUSES = {"queued", "reviewed", "sent", "replied", "qualified", "closed", "opt_out"}
PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Z _-]+\]")


class OpsError(ValueError):
    pass


def parse_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise OpsError(f"invalid ISO date: {value!r}") from exc


def clean(value: object, limit: int = 1200) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())[:limit]


def public_https(value: str) -> bool:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username and not parsed.password


def candidate_id(row: dict[str, str]) -> str:
    stable = (clean(row.get("website")).lower().rstrip("/") + "|" + clean(row.get("business_name")).lower())
    return "prospect_" + hashlib.sha256(stable.encode("utf-8")).hexdigest()[:12]


def read_candidates(path: Path, run_date: dt.date) -> list[dict[str, str]]:
    if not path.is_file():
        raise OpsError(f"candidate source missing: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REQUIRED_FIELDS:
            raise OpsError("candidate CSV header changed; expected the checked private research schema")
        rows = list(reader)

    accepted: list[dict[str, str]] = []
    for line_no, raw in enumerate(rows, start=2):
        row = {key: clean(raw.get(key)) for key in REQUIRED_FIELDS}
        if row["wedge"] != "home_service_contractor":
            continue
        if not row["business_name"] or not public_https(row["website"]) or not public_https(row["source_url"]):
            raise OpsError(f"candidate line {line_no}: contractor row needs a business name and public HTTPS evidence URLs")
        if len(row["observable_workflow_friction"]) < 45 or len(row["suggested_outreach_angle"]) < 30:
            raise OpsError(f"candidate line {line_no}: observation and angle must be specific")
        verified = parse_date(row["verified_date"])
        if verified > run_date:
            raise OpsError(f"candidate line {line_no}: verified_date is in the future")
        if (run_date - verified).days > 45:
            continue
        row["candidate_id"] = candidate_id(row)
        accepted.append(row)
    if not accepted:
        raise OpsError("no current contractor candidates passed the evidence gate")
    return accepted


def read_state(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != STATE_FIELDS:
            raise OpsError("private outreach state header changed")
        rows = []
        for line_no, raw in enumerate(reader, start=2):
            row = {key: clean(raw.get(key), 500) for key in STATE_FIELDS}
            if row["status"] not in ALLOWED_STATUSES:
                raise OpsError(f"outreach state line {line_no}: invalid status {row['status']!r}")
            if row["do_not_contact"] not in {"true", "false"}:
                raise OpsError(f"outreach state line {line_no}: do_not_contact must be true or false")
            rows.append(row)
        return rows


def write_csv_atomic(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=STATE_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def source_tag(run_date: dt.date, position: int) -> str:
    return f"outreach-hs-en-{run_date:%y%m%d}-{position:02d}"


def tracked_url(run_date: dt.date, position: int) -> str:
    query = urlencode({
        "utm_source": "manual_email",
        "utm_medium": "outbound",
        "utm_campaign": "contractor-product-v1",
        "utm_term": "home_services",
        "utm_content": source_tag(run_date, position),
    })
    return "https://leonbuilds.org/missed-lead-recovery?" + query


def render_item(row: dict[str, str], run_date: dt.date, position: int) -> str:
    observation = row["observable_workflow_friction"].rstrip(".") + "."
    angle = row["suggested_outreach_angle"].rstrip(".")
    angle_for_sentence = angle[:1].lower() + angle[1:]
    return f"""## {position}. {row['business_name']}

- Candidate ID: `{row['candidate_id']}`
- Public evidence checked: {row['source_url']} on {row['verified_date']}
- Direct contact path still required: {row['contact_page_url'] or '[RESEARCH A LAWFUL BUSINESS CONTACT PATH]'}
- Observed fact: {observation}
- Possible smallest fix, not a result claim: {angle}
- Tracking link: {tracked_url(run_date, position)}

### Short teardown draft

**Subject:** quick note about your estimate path

Hi {row['business_name']} team —

I looked at the public request path on your site and noticed this: {observation}

That may make an after-hours estimate request depend on a call or a manual callback. A small first step to examine would be to {angle_for_sentence}.

If useful, I can send a short three-point teardown showing what I would keep, what I would change, and how I would track the handoff. If this is already handled behind the scenes, feel free to ignore me.

— Leon Kelvin Li
leonbuilds.org
[VALID POSTAL ADDRESS]
This is a one-to-one business outreach message. Reply “no thanks” and I will not contact you again.

### Human review checklist

- [ ] Re-open the evidence URL and confirm the observation is still true.
- [ ] Find and verify an appropriate public business contact path; never guess or scrape it.
- [ ] Confirm the business is not suppressed and has not opted out.
- [ ] Replace the postal-address placeholder after the required compliance review.
- [ ] Edit the draft in Leon's own voice and decide whether to send it manually.
"""


def prepare(args: argparse.Namespace) -> int:
    run_date = parse_date(args.date)
    if run_date.weekday() >= 5:
        raise OpsError("weekday queue not created: the selected date is Saturday or Sunday")
    candidates = read_candidates(Path(args.source), run_date)
    state_rows = read_state(Path(args.state))
    state_by_id = {row["candidate_id"]: row for row in state_rows}
    eligible = [
        row for row in candidates
        if row["candidate_id"] not in state_by_id
        or (
            state_by_id[row["candidate_id"]]["status"] not in BLOCKED_STATUSES
            and state_by_id[row["candidate_id"]]["do_not_contact"] != "true"
        )
    ]
    eligible.sort(key=lambda row: (row["verified_date"], row["business_name"]), reverse=True)
    selected = eligible[: args.limit]
    if not selected:
        raise OpsError("no contractor candidate is eligible; review private state or refresh evidence")

    queue_dir = Path(args.queue_dir) / run_date.isoformat()
    queue_path = queue_dir / "review-packet.md"
    manifest_path = queue_dir / "manifest.json"
    if queue_path.exists() or manifest_path.exists():
        raise OpsError(f"queue already exists for {run_date}; existing drafts were not overwritten")
    queue_dir.mkdir(parents=True, exist_ok=False)

    header = f"""# Contractor teardown review queue — {run_date.isoformat()}

**Status: DRAFT — REVIEW REQUIRED — NOTHING SENT**

This packet contains public-business observations and copy drafts only. It has
no recipient address and cannot send. Every item requires a fresh evidence check,
lawful contact-path research, suppression check, compliance completion, and a
manual decision by Leon.

"""
    queue_path.write_text(header + "\n".join(
        render_item(row, run_date, position)
        for position, row in enumerate(selected, start=1)
    ), encoding="utf-8")
    manifest = {
        "schemaVersion": 1,
        "status": "DRAFT_REVIEW_REQUIRED_NOT_SENT",
        "queueDate": run_date.isoformat(),
        "count": len(selected),
        "candidateIds": [row["candidate_id"] for row in selected],
        "sendCapability": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    today = run_date.isoformat()
    for row in selected:
        state_by_id[row["candidate_id"]] = {
            "candidate_id": row["candidate_id"],
            "business_name": row["business_name"],
            "website": row["website"],
            "wedge": row["wedge"],
            "queue_date": today,
            "status": "queued",
            "last_action_date": today,
            "do_not_contact": "false",
            "notes": "draft generated; no send authorization",
        }
    write_csv_atomic(Path(args.state), sorted(state_by_id.values(), key=lambda row: row["candidate_id"]))
    print(f"prepared {len(selected)} contractor teardown draft(s): {queue_path}")
    print("NOT SENT — manual research, compliance completion and approval still required")
    return 0


def audit(args: argparse.Namespace) -> int:
    run_date = parse_date(args.date)
    candidates = read_candidates(Path(args.source), run_date)
    state = read_state(Path(args.state))
    blocked = sum(row["status"] in BLOCKED_STATUSES or row["do_not_contact"] == "true" for row in state)
    print(f"outreach audit ok — {len(candidates)} current contractor candidates / {len(state)} state rows / {blocked} blocked from a new draft")
    return 0


def record(args: argparse.Namespace) -> int:
    if args.status not in ALLOWED_STATUSES:
        raise OpsError(f"invalid status: {args.status}")
    action_date = parse_date(args.date).isoformat()
    path = Path(args.state)
    rows = read_state(path)
    found = False
    for row in rows:
        if row["candidate_id"] != args.candidate_id:
            continue
        found = True
        row["status"] = args.status
        row["last_action_date"] = action_date
        if args.status == "opt_out":
            row["do_not_contact"] = "true"
        if args.note:
            row["notes"] = clean(args.note, 500)
    if not found:
        raise OpsError("candidate ID not found in private outreach state")
    write_csv_atomic(path, rows)
    print(f"recorded {args.candidate_id}: {args.status}; no external action performed")
    return 0


def parser() -> argparse.ArgumentParser:
    out = argparse.ArgumentParser(description=__doc__)
    sub = out.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--date", default=dt.date.today().isoformat())
    common.add_argument("--source", default=str(DEFAULT_SOURCE))
    common.add_argument("--state", default=str(DEFAULT_STATE))

    check = sub.add_parser("audit", parents=[common])
    check.set_defaults(func=audit)

    prep = sub.add_parser("prepare", parents=[common])
    prep.add_argument("--limit", type=int, default=3, choices=range(1, 6), metavar="1..5")
    prep.add_argument("--queue-dir", default=str(DEFAULT_QUEUE))
    prep.set_defaults(func=prepare)

    status = sub.add_parser("record")
    status.add_argument("candidate_id")
    status.add_argument("status", choices=sorted(ALLOWED_STATUSES))
    status.add_argument("--date", default=dt.date.today().isoformat())
    status.add_argument("--state", default=str(DEFAULT_STATE))
    status.add_argument("--note", default="")
    status.set_defaults(func=record)
    return out


def main() -> int:
    try:
        args = parser().parse_args()
        return args.func(args)
    except OpsError as exc:
        print(f"outreach ops blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
