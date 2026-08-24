#!/usr/bin/env python3
"""Prepare one evidence-backed contractor field-note draft per ISO week.

The output is private and review-only. This script never creates a public page,
changes the sitemap, publishes, or sends anything.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "private" / "prospect-candidates-2026-08-23.csv"
DEFAULT_OUTPUT = ROOT / "private" / "content-queue"
REQUIRED = (
    "business_name", "wedge", "city", "website", "contact_page_url",
    "observable_workflow_friction", "suggested_outreach_angle",
    "language_signal", "verified_date", "source_url",
)


class ContentError(ValueError):
    pass


def clean(value: object, limit: int = 1600) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())[:limit]


def parse_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ContentError(f"invalid date {value!r}") from exc


def https_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc)


def evidence(path: Path, run_date: dt.date) -> list[dict[str, str]]:
    if not path.is_file():
        raise ContentError(f"source missing: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REQUIRED:
            raise ContentError("private research CSV header changed")
        rows = []
        for line_no, raw in enumerate(reader, start=2):
            row = {field: clean(raw.get(field)) for field in REQUIRED}
            if row["wedge"] != "home_service_contractor":
                continue
            when = parse_date(row["verified_date"])
            if when > run_date or (run_date - when).days > 45:
                continue
            if not https_url(row["source_url"]) or len(row["observable_workflow_friction"]) < 45:
                raise ContentError(f"line {line_no}: weak or invalid public evidence")
            rows.append(row)
    if len(rows) < 3:
        raise ContentError("at least three current contractor observations are required")
    return sorted(rows, key=lambda row: (row["verified_date"], row["business_name"]), reverse=True)


def prepare(args: argparse.Namespace) -> int:
    run_date = parse_date(args.date)
    rows = evidence(Path(args.source), run_date)[:3]
    iso_year, iso_week, _ = run_date.isocalendar()
    slug = f"{iso_year}-W{iso_week:02d}-contractor-estimate-paths"
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    draft_path = out_dir / f"{slug}.md"
    manifest_path = out_dir / f"{slug}.json"
    if draft_path.exists() or manifest_path.exists():
        raise ContentError(f"weekly draft already exists: {slug}; nothing overwritten")

    examples = []
    evidence_notes = []
    for number, row in enumerate(rows, start=1):
        examples.append(
            f"### Pattern {number}\n\n"
            f"Observed on a public contractor site: {row['observable_workflow_friction'].rstrip('.')}.")
        evidence_notes.append(
            f"- {row['business_name']} — {row['source_url']} — checked {row['verified_date']} — "
            f"editorial decision required before naming this business publicly"
        )

    draft = f"""# Contractor estimate-request teardown: three public patterns worth checking

**Status: PRIVATE DRAFT — FACT CHECK AND EDITORIAL APPROVAL REQUIRED — NOT PUBLISHED**

Contractors often spend money getting a visitor to the website, then make the
last step harder than it needs to be. This field note looks at three observable
estimate-request patterns and turns them into a practical checklist. It does not
estimate lost revenue or claim that a change will create more jobs.

{"\n\n".join(examples)}

## A five-part estimate-path check

1. **The next action is visible on a phone.** A visitor should not need to hunt
   for the call or estimate button.
2. **The form asks for useful job context.** Service, location, project details,
   preferred contact, and optional photos can reduce the first round of phone tag.
3. **The visitor gets a clear acknowledgment.** State what was received and what
   happens next; do not promise a response time the team cannot consistently meet.
4. **One person or queue owns the handoff.** A form is not a process unless the
   team can see which requests still need a response.
5. **The business can measure the path.** Track received, acknowledged, replied,
   booked, qualified, and won separately.

## The smallest useful implementation

A focused contractor website plus one estimate workflow can be enough: one
primary action, structured intake, acknowledgment, up to two follow-ups, an owner
handoff, and a basic event log. Existing tools should stay when they already work.

[See the fixed-scope contractor product](https://leonbuilds.org/missed-lead-recovery)

## Private evidence notes — remove or convert to approved citations before publishing

{"\n".join(evidence_notes)}

## Publication gate

- [ ] Re-open and screenshot every cited public state on publication day.
- [ ] Decide whether examples remain anonymous or are named with fair context.
- [ ] Add original screenshots only when their use is appropriate and documented.
- [ ] Have an unaffiliated cold reader check usefulness and tone.
- [ ] Run the site checks after building a real public page and before deployment.
- [ ] Publish at most one substantive industry note or approved case study this week.
"""
    draft_path.write_text(draft, encoding="utf-8")
    manifest_path.write_text(json.dumps({
        "schemaVersion": 1,
        "status": "PRIVATE_DRAFT_NOT_PUBLISHED",
        "isoWeek": f"{iso_year}-W{iso_week:02d}",
        "draft": draft_path.name,
        "publicWriteCapability": False,
        "sourceCount": len(rows),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"prepared weekly private content draft: {draft_path}")
    print("NOT PUBLISHED — fact check and editorial approval required")
    return 0


def audit(args: argparse.Namespace) -> int:
    rows = evidence(Path(args.source), parse_date(args.date))
    print(f"content ops ok — {len(rows)} current contractor observations can support one weekly draft")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "prepare"))
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    try:
        return audit(args) if args.command == "audit" else prepare(args)
    except ContentError as exc:
        print(f"content ops blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
