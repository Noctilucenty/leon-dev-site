#!/usr/bin/env python3
"""Fail-closed publication state for client testimonials and supplied ratings.

The exact supplied drafts live outside the public static allowlist. A testimonial
is publishable only when the tracked release manifest contains an exact payload
digest and a receipt digest for the client's approval. Rating publication is a
separate decision and receipt. Missing or malformed state stops the build.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
DRAFTS_RELATIVE = Path("content/client-success/testimonial-drafts.json")
PUBLICATION_RELATIVE = Path("content/client-success/testimonial-publication.json")
PLACEMENT = "leonbuilds.org and related project marketing"
SHA256_RE = re.compile(r"[0-9a-f]{64}")
ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
CARD_RE = re.compile(
    r'<article\b(?=[^>]*\bdata-testimonial-id=["\']([^"\']+)["\'])[^>]*>[\s\S]*?</article>',
    re.I,
)


class TestimonialGateError(RuntimeError):
    """Publication state is missing, malformed, or internally inconsistent."""


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TestimonialGateError(f"cannot read testimonial gate file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TestimonialGateError(f"testimonial gate file must contain an object: {path}")
    return value


def testimonial_payload(draft: Mapping[str, object]) -> dict[str, object]:
    return {
        "id": draft["id"],
        "project": draft["project"],
        "attribution": draft["attribution"],
        "attribution_context": draft["attribution_context"],
        "quote": draft["quote"],
        "placement": draft["placement"],
    }


def testimonial_payload_sha256(draft: Mapping[str, object]) -> str:
    encoded = json.dumps(
        testimonial_payload(draft), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _valid_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _validate_drafts(document: dict) -> list[dict]:
    if document.get("schema_version") != 1:
        raise TestimonialGateError("testimonial drafts: unsupported schema_version")
    values = document.get("testimonials")
    if not isinstance(values, list) or len(values) != 7:
        raise TestimonialGateError("testimonial drafts: exactly seven supplied drafts are required")
    required = {
        "id",
        "project",
        "attribution",
        "attribution_context",
        "quote",
        "supplied_rating",
        "placement",
    }
    seen: set[str] = set()
    drafts: list[dict] = []
    for index, value in enumerate(values):
        if not isinstance(value, dict):
            raise TestimonialGateError(f"testimonial drafts[{index}]: must be an object")
        if set(value) != required:
            raise TestimonialGateError(f"testimonial drafts[{index}]: fields do not match the locked schema")
        testimonial_id = value.get("id")
        if not isinstance(testimonial_id, str) or not ID_RE.fullmatch(testimonial_id):
            raise TestimonialGateError(f"testimonial drafts[{index}].id: invalid")
        if testimonial_id in seen:
            raise TestimonialGateError(f"testimonial drafts: duplicate id {testimonial_id}")
        seen.add(testimonial_id)
        for field in ("project", "attribution", "attribution_context", "quote"):
            if not isinstance(value.get(field), str) or not value[field].strip():
                raise TestimonialGateError(f"testimonial drafts[{index}].{field}: required")
        if value.get("supplied_rating") != 5:
            raise TestimonialGateError(f"testimonial drafts[{index}].supplied_rating: expected supplied value 5")
        if value.get("placement") != PLACEMENT:
            raise TestimonialGateError(f"testimonial drafts[{index}].placement: unexpected placement")
        drafts.append(value)
    return drafts


def load_testimonial_release(root: Path = ROOT) -> tuple[list[dict], dict[str, dict]]:
    """Return all locked drafts and only individually publishable records."""
    publication = _read_json(root / PUBLICATION_RELATIVE)
    if publication.get("schema_version") != 1:
        raise TestimonialGateError("testimonial publication: unsupported schema_version")
    entries = publication.get("approved_testimonials")
    if not isinstance(entries, list):
        raise TestimonialGateError("testimonial publication: approved_testimonials must be a list")

    draft_path = root / DRAFTS_RELATIVE
    if not draft_path.is_file():
        if entries:
            raise TestimonialGateError(
                "testimonial drafts: private draft source is required before any release"
            )
        # The exact unapproved quotes stay local and gitignored because this
        # repository is public. A clean deployment may still prove that zero
        # testimonials are released without receiving those private drafts.
        return [], {}
    drafts = _validate_drafts(_read_json(draft_path))

    by_id = {draft["id"]: draft for draft in drafts}
    released: dict[str, dict] = {}
    required = {
        "id",
        "payload_sha256",
        "approved_at",
        "approval_evidence_sha256",
        "placement",
        "rating_approval",
    }
    for index, entry in enumerate(entries):
        label = f"testimonial publication[{index}]"
        if not isinstance(entry, dict) or set(entry) != required:
            raise TestimonialGateError(f"{label}: fields do not match the locked schema")
        testimonial_id = entry.get("id")
        if testimonial_id not in by_id:
            raise TestimonialGateError(f"{label}.id: unknown testimonial")
        if testimonial_id in released:
            raise TestimonialGateError(f"{label}.id: duplicate release")
        draft = by_id[testimonial_id]
        if entry.get("payload_sha256") != testimonial_payload_sha256(draft):
            raise TestimonialGateError(f"{label}: exact quote and attribution payload digest does not match")
        if not _valid_date(entry.get("approved_at")):
            raise TestimonialGateError(f"{label}.approved_at: valid ISO date required")
        if not isinstance(entry.get("approval_evidence_sha256"), str) or not SHA256_RE.fullmatch(
            entry["approval_evidence_sha256"]
        ):
            raise TestimonialGateError(f"{label}.approval_evidence_sha256: SHA-256 receipt required")
        if entry.get("placement") != draft["placement"]:
            raise TestimonialGateError(f"{label}.placement: must exactly match the client-reviewed placement")

        show_rating = False
        rating = entry.get("rating_approval")
        if rating is not None:
            if not isinstance(rating, dict) or set(rating) != {"value", "approved_at", "evidence_sha256"}:
                raise TestimonialGateError(f"{label}.rating_approval: fields do not match the locked schema")
            if rating.get("value") != draft["supplied_rating"]:
                raise TestimonialGateError(f"{label}.rating_approval.value: does not match the supplied rating")
            if not _valid_date(rating.get("approved_at")):
                raise TestimonialGateError(f"{label}.rating_approval.approved_at: valid ISO date required")
            if not isinstance(rating.get("evidence_sha256"), str) or not SHA256_RE.fullmatch(
                rating["evidence_sha256"]
            ):
                raise TestimonialGateError(f"{label}.rating_approval.evidence_sha256: SHA-256 receipt required")
            show_rating = True
        released[testimonial_id] = {**draft, "show_rating": show_rating}
    return drafts, released


def visible_text(source: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(source)
    parser.close()
    return " ".join(" ".join(parser.parts).split())


def testimonial_release_errors(
    documents: Mapping[str, str], root: Path = ROOT
) -> list[str]:
    """Reject any public testimonial material not authorized by the manifest."""
    drafts, released = load_testimonial_release(root)
    errors: list[str] = []
    released_ids = set(released)
    rating_ids = {key for key, value in released.items() if value["show_rating"]}

    for label, source in documents.items():
        raw_lower = source.lower()
        text_lower = visible_text(source).lower() if label.endswith(".html") else html.unescape(source).lower()
        for match in CARD_RE.finditer(source):
            testimonial_id = match.group(1)
            if testimonial_id not in released_ids:
                errors.append(f"{label}: unreleased testimonial card {testimonial_id}")
                continue
            card_text = visible_text(match.group(0)).lower()
            item = released[testimonial_id]
            if item["quote"].lower() not in card_text:
                errors.append(f"{label}: testimonial {testimonial_id} does not use the exact approved quote")
            if item["attribution"].lower() not in card_text:
                errors.append(f"{label}: testimonial {testimonial_id} does not use the approved attribution")
        for draft in drafts:
            if draft["id"] in released_ids:
                continue
            if draft["attribution"].lower() in text_lower:
                errors.append(f"{label}: unreleased testimonial attribution {draft['attribution']}")
            if draft["quote"].lower() in text_lower:
                errors.append(f"{label}: unreleased testimonial quote {draft['id']}")

        if not released_ids:
            for phrase in (
                "#testimonials",
                "direct client feedback",
                "direct client review",
                "client testimonials",
                "testimonial-card",
                "service-review",
            ):
                if phrase in raw_lower:
                    errors.append(f"{label}: testimonial publication is empty but {phrase!r} is public")
        if not rating_ids:
            for phrase in ("testimonial-stars", "5 out of 5 stars", "all 5 stars", "★★★★★"):
                if phrase in raw_lower:
                    errors.append(f"{label}: no supplied rating is approved but {phrase!r} is public")
        else:
            for match in CARD_RE.finditer(source):
                testimonial_id = match.group(1)
                card = match.group(0).lower()
                has_rating = "testimonial-stars" in card or "5 out of 5 stars" in card or "★★★★★" in card
                if has_rating and testimonial_id not in rating_ids:
                    errors.append(f"{label}: testimonial {testimonial_id} exposes an unapproved rating")
    return sorted(set(errors))


if __name__ == "__main__":
    drafts, released = load_testimonial_release()
    ratings = sum(1 for value in released.values() if value["show_rating"])
    print(f"testimonial gate: {len(drafts)} drafts preserved; {len(released)} quotes and {ratings} ratings released")
    for draft in drafts:
        state = "released" if draft["id"] in released else "withheld"
        print(f"{draft['id']}: {state} payload_sha256={testimonial_payload_sha256(draft)}")
