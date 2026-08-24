#!/usr/bin/env python3
"""Fail-closed Google Business Profile eligibility gate.

This tool never opens, creates, edits, or verifies a Business Profile. It checks
a private eligibility record against the core in-person/storefront/service-area
conditions so an online-only business cannot accidentally proceed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "private" / "google-business-profile.json"
TEMPLATE = {
    "schemaVersion": 1,
    "businessName": "Leon Builds",
    "inPersonCustomerContactDuringStatedHours": False,
    "mode": "online_only",
    "travelsToCustomerLocations": False,
    "customersVisitBusinessAddress": False,
    "addressIsPoBoxOrMailbox": False,
    "addressIsVirtualOffice": False,
    "locationStaffedDuringStatedHours": False,
    "permanentOnSiteSignage": False,
    "privateAddressDetailsVerified": False,
    "serviceAreas": [],
    "ownerApprovedProfileCreation": False,
    "notes": "Default is blocked because remote online-only work is not eligible. Do not put the street address in this tracked template.",
}


class GateError(ValueError):
    pass


def initialize(path: Path) -> int:
    if path.exists():
        raise GateError(f"config already exists; nothing overwritten: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(TEMPLATE, indent=2) + "\n", encoding="utf-8")
    print(f"created private blocked-by-default eligibility record: {path}")
    return 0


def load(path: Path) -> dict:
    if not path.is_file():
        raise GateError(f"private eligibility record missing: {path}; run init")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read eligibility record: {exc}") from exc
    for key in TEMPLATE:
        if key not in value:
            raise GateError(f"eligibility record missing {key!r}")
    if value["mode"] not in {"online_only", "storefront", "service_area", "hybrid"}:
        raise GateError("mode must be online_only, storefront, service_area, or hybrid")
    if not isinstance(value["serviceAreas"], list) or len(value["serviceAreas"]) > 20:
        raise GateError("serviceAreas must be a list of no more than 20 specific areas")
    return value


def decision(value: dict) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if not value["inPersonCustomerContactDuringStatedHours"]:
        blockers.append("business does not currently make in-person customer contact during stated hours")
    if value["mode"] == "online_only":
        blockers.append("online-only businesses are not eligible")
    if value["addressIsPoBoxOrMailbox"] or value["addressIsVirtualOffice"]:
        blockers.append("P.O. boxes, mailboxes, and unstaffed virtual offices are not valid business locations")
    if not value["privateAddressDetailsVerified"]:
        blockers.append("required business address details have not been privately verified")
    if value["mode"] in {"storefront", "hybrid"}:
        if not value["customersVisitBusinessAddress"]:
            blockers.append("storefront/hybrid mode requires customers to visit the address")
        if not value["locationStaffedDuringStatedHours"]:
            blockers.append("storefront/hybrid location is not confirmed staffed during stated hours")
        if not value["permanentOnSiteSignage"]:
            blockers.append("storefront/hybrid location lacks confirmed permanent signage")
    if value["mode"] == "service_area":
        if not value["travelsToCustomerLocations"]:
            blockers.append("service-area mode requires traveling to customers in person")
        if value["customersVisitBusinessAddress"]:
            blockers.append("service-area-only mode should not claim customers visit the address")
        if not value["serviceAreas"]:
            blockers.append("specific truthful service areas are required")
    if value["mode"] == "hybrid" and not value["travelsToCustomerLocations"]:
        blockers.append("hybrid mode requires both a staffed customer location and in-person travel/delivery")
    if not value["ownerApprovedProfileCreation"]:
        blockers.append("owner has not approved the exact live profile creation")
    return ("ELIGIBLE_FOR_MANUAL_REVIEW" if not blockers else "BLOCKED", blockers)


def check(path: Path) -> int:
    value = load(path)
    status, blockers = decision(value)
    print(f"Google Business Profile gate: {status}")
    for blocker in blockers:
        print(f"- {blocker}")
    print("No Google account or Business Profile action was performed.")
    return 0 if status == "ELIGIBLE_FOR_MANUAL_REVIEW" else 3


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "check"))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()
    try:
        return initialize(Path(args.config)) if args.command == "init" else check(Path(args.config))
    except GateError as exc:
        print(f"Google Business Profile gate blocked: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
