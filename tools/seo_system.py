#!/usr/bin/env python3
"""Offline SEO intent ownership, fail-closed publication and GSC CSV analysis.

No network, paid model calls, account access or automatic publication. Generated
reports stay outside the public allowlist. Search demand is never fabricated.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import io
import json
import math
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://leonbuilds.org"
DIMENSIONS = ("SearchIntentMatch", "InformationGain", "SourceQuality", "Originality", "Completeness",
              "Readability", "Curiosity", "FactualConfidence", "DuplicateSafety", "ConversionFit")
# This is the historical live inventory, not an extensible allowlist. Changing
# it is a reviewed policy change; a normal new page must use the review path.
LEGACY_PATHS_SHA256 = "c2476849e7b28f08cd93629421bd79e0a1172b737c6b18405e39d4ca6ac967d9"


def read_json(name):
    return json.loads((ROOT / "content" / "seo" / name).read_text(encoding="utf-8"))


def normalize_query(value):
    return " ".join(re.sub(r"[^\w\s]", " ", unicodedata.normalize("NFKC", value).casefold()).split())


def safe_path(path):
    if not isinstance(path, str):
        return False
    parsed = urlsplit(path)
    return (isinstance(path, str) and path.startswith("/") and not path.startswith("//")
            and not parsed.scheme and not parsed.netloc and not parsed.query and not parsed.fragment
            and not re.search(r"[\\\x00-\x20]", path) and ".." not in path.split("/"))


def sitemap_paths():
    return [urlsplit(node.text).path for node in ET.parse(ROOT / "sitemap.xml").getroot().iter()
            if node.tag.rsplit("}", 1)[-1] == "loc"]


def assert_publication_paths(paths, publication=None, root=ROOT, check_rendered=False):
    publication = publication or read_json("publication.json")
    legacy = set(publication["legacy_paths"])
    if len(legacy) != len(publication["legacy_paths"]):
        raise ValueError("duplicate legacy paths")
    legacy_hash = hashlib.sha256(json.dumps(sorted(legacy), separators=(",", ":")).encode()).hexdigest()
    if legacy_hash != LEGACY_PATHS_SHA256:
        raise ValueError("historical legacy inventory is frozen; new pages need review")
    approved = set(legacy)
    reviewed = set()
    for review in publication["reviews"]:
        path = review["path"]
        if path in reviewed:
            raise ValueError(f"duplicate publication review: {path}")
        reviewed.add(path)
        if review["decision"] != "INDEX":
            approved.discard(path)
            continue
        if not review.get("rationale") or not review.get("reviewed_at"):
            raise ValueError(f"missing review evidence: {path}")
        producer = review.get("producer", "")
        reviewer = review.get("reviewer", "")
        if (not isinstance(producer, str) or not isinstance(reviewer, str)
                or not producer.strip() or not reviewer.strip()
                or producer.strip().casefold() == reviewer.strip().casefold()):
            raise ValueError(f"distinct named producer and reviewer required: {path}")
        try:
            reviewed_at = datetime.date.fromisoformat(review["reviewed_at"])
        except (ValueError, TypeError):
            raise ValueError(f"invalid review date: {path}") from None
        if reviewed_at > datetime.date.today():
            raise ValueError(f"review date cannot be in the future: {path}")
        scores = review.get("scores", {})
        if any(type(scores.get(key)) not in (int, float) or not 9 <= scores[key] <= 10 for key in DIMENSIONS):
            raise ValueError(f"all editorial dimensions must score at least 9: {path}")
        source = (root / review["source_file"]).resolve()
        if not source.is_relative_to(root.resolve() / "content" / "seo") or not source.is_file():
            raise ValueError(f"invalid review source: {path}")
        if hashlib.sha256(source.read_bytes()).hexdigest() != review["sha256"]:
            raise ValueError(f"content changed; review again before indexing: {path}")
        if check_rendered:
            rendered = (root / review.get("rendered_file", "")).resolve()
            if (not rendered.is_relative_to(root.resolve()) or not rendered.is_file()
                    or rendered.suffix != ".html"
                    or hashlib.sha256(rendered.read_bytes()).hexdigest() != review.get("rendered_sha256")):
                raise ValueError(f"rendered page changed; review its exact HTML before publishing: {path}")
        approved.add(path)
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate sitemap path")
    for path in paths:
        if not safe_path(path) or path not in approved:
            raise ValueError(f"new route requires an explicit publication review: {path}")


def validate_topics(data=None, paths=None):
    data = data or read_json("topics.json")
    paths = set(paths or sitemap_paths())
    ownership, identities = {}, set()
    for topic in data["topics"]:
        if topic["id"] in identities:
            raise ValueError(f"duplicate topic ID: {topic['id']}")
        identities.add(topic["id"])
        if topic["canonical_path"] not in paths:
            raise ValueError(f"topic targets a noncanonical path: {topic['id']}")
        for query in [topic["primary_query"], *topic["aliases"], *topic["question_queries"]]:
            key = (topic["language"], normalize_query(query))
            if not key[1]:
                raise ValueError("empty query")
            previous = ownership.setdefault(key, topic["canonical_path"])
            if previous != topic["canonical_path"]:
                raise ValueError(f"query has competing canonical owners: {query}")
        for relation in topic["relationships"]:
            if relation["path"] not in paths or relation["path"] == topic["canonical_path"]:
                raise ValueError(f"invalid related path: {relation['path']}")
            if relation["type"] not in {"prerequisite", "comparison", "example", "deeper_dive"} or not relation["label"]:
                raise ValueError("relationship requires a supported type and useful label")
    return len(ownership)


def related_html(path):
    topic = next((row for row in read_json("topics.json")["topics"] if row["canonical_path"] == path), None)
    if not topic or not topic["relationships"]:
        return ""
    links = "".join(f'<p class="sub business-copy"><a href="{escape(row["path"], quote=True)}" '
                    f'data-evt="seo_related_click">{escape(row["label"])}</a></p>' for row in topic["relationships"])
    return f'<aside class="proofcard seo-next-step" aria-label="A guide for this decision">{links}</aside>'


def source_for(path):
    if path == "/":
        return ROOT / "homepage/index.html"
    base = ROOT / path.lstrip("/")
    file_page = base.with_suffix(".html")
    return file_page if not path.endswith("/") and file_page.is_file() else base / "index.html"


def opportunities():
    data = read_json("topics.json")
    owners = {row["canonical_path"]: row for row in data["topics"]}
    rows = []
    for path in sitemap_paths():
        html = source_for(path).read_text(encoding="utf-8")
        title = re.search(r"<title>(.*?)</title>", html, re.S).group(1)
        from html import unescape
        title = unescape(title).split(" | Leon Builds")[0]
        topic = owners.get(path)
        conversion = "navigation" if path in {"/privacy", "/about", "/reviews"} else "qualify inquiry"
        rows.append(dict(topic=title, primary_query=topic["primary_query"] if topic else "unmapped: validate search intent",
                         alternative_queries="; ".join(topic["aliases"] + topic["question_queries"]) if topic else "unknown",
                         intent="; ".join(topic["search_intents"]) if topic else "existing page inventory",
                         cluster=topic["cluster"] if topic else (path.strip("/").split("/")[0] or "brand"),
                         existing_curio_content="not applicable; existing Leon Builds page",
                         search_potential="unknown; no current query-volume evidence", curio_fit="not applicable",
                         competition_estimate="unknown", conversion_potential=conversion,
                         quality_score="unscored legacy" if path in read_json("publication.json")["legacy_paths"] else "editorial minimum 9; not measured performance",
                         recommended_action="measure; improve existing canonical" if topic else "map intent before expansion",
                         priority="P1" if topic else "P2", canonical_url=ORIGIN + path,
                         leon_builds_fit="existing service, proof, trust or conversion surface", evidence_state="CONFIRMED inventory; demand UNKNOWN"))
    existing_intents = {(row["canonical_url"], normalize_query(row["primary_query"])) for row in rows}
    for candidate in data["candidates"]:
        if (ORIGIN + candidate["canonical_path"], normalize_query(candidate["primary_query"])) in existing_intents:
            continue
        rows.append(dict(topic=candidate["topic"], primary_query=candidate["primary_query"], alternative_queries="research needed",
                         intent="buyer decision", cluster=candidate["cluster"], existing_curio_content="not applicable",
                         search_potential="unknown", curio_fit="not applicable", competition_estimate="unknown",
                         conversion_potential="plausible; unmeasured", quality_score="not reviewed",
                         recommended_action=candidate["action"] + ": " + candidate["reason"], priority="P2",
                         canonical_url=ORIGIN + candidate["canonical_path"], leon_builds_fit="candidate fits current services",
                         evidence_state="EXPERIMENTAL topic hypothesis; not authorized to index"))
    return rows


def analyze_search_csv(text, start_date, end_date, minimum_impressions=20):
    start, end = datetime.date.fromisoformat(start_date), datetime.date.fromisoformat(end_date)
    if start > end:
        raise ValueError("start date must not follow end date")
    if minimum_impressions < 1:
        raise ValueError("minimum impressions must be positive")
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    required = {"query", "page", "clicks", "impressions", "position"}
    names = {key.strip().lower(): key for key in reader.fieldnames or []}
    if not required <= names.keys():
        raise ValueError("export must contain Query, Page, Clicks, Impressions, Position together; separate query and page totals cannot be joined")
    combined = defaultdict(lambda: {"clicks": 0, "impressions": 0, "weighted_position": 0.0})
    withheld = 0
    for row in reader:
        query = row[names["query"]].strip()
        page = row[names["page"]].strip()
        parsed = urlsplit(page)
        if parsed.scheme != "https" or parsed.netloc != "leonbuilds.org" or parsed.query or parsed.fragment:
            raise ValueError("page values must be canonical HTTPS Leon Builds URLs without query strings")
        if (parsed.path or "/") not in set(sitemap_paths()):
            raise ValueError("page export includes an unknown canonical; inspect it before ingestion")
        # Query exports can contain personal searches. Do not persist obvious contacts.
        if not query or "@" in query or re.search(r"(?:\d[\s()+.-]*){7,}", query):
            withheld += 1
            continue
        clicks, impressions = float(row[names["clicks"]]), float(row[names["impressions"]])
        position = float(row[names["position"]])
        if (not all(math.isfinite(n) for n in (clicks, impressions, position))
                or clicks < 0 or impressions < clicks or not clicks.is_integer() or not impressions.is_integer()
                or position < 1):
            raise ValueError("invalid or non-finite Search Console metrics")
        bucket = combined[(normalize_query(query), page)]
        bucket["clicks"] += int(clicks)
        bucket["impressions"] += int(impressions)
        bucket["weighted_position"] += position * impressions
    output, pages_by_query = [], defaultdict(set)
    for (query, page), bucket in sorted(combined.items()):
        impressions = bucket["impressions"]
        position = bucket["weighted_position"] / impressions if impressions else None
        ctr = bucket["clicks"] / impressions if impressions else None
        flags = []
        if impressions >= minimum_impressions:
            if position is not None and 8 <= position <= 20:
                flags.append("review page usefulness at position 8-20")
            if ctr is not None and ctr < .02:
                flags.append("review snippet/intent; 2% is a triage threshold, not a universal CTR target")
            pages_by_query[query].add(page)
        output.append({"query": query, "page": page, "clicks": bucket["clicks"], "impressions": impressions,
                       "ctr": ctr, "average_position": position, "flags": flags})
    return {"period": {"start": start_date, "end": end_date, "source": "operator-supplied export window"},
            "source": "Search Console CSV; no account connection", "privacy_withheld_rows": withheld,
            "minimum_impressions": minimum_impressions, "rows": output,
            "possible_cannibalization": [{"query": query, "pages": sorted(pages), "action": "inspect intent; multiple URLs are not proof of harm"}
                for query, pages in sorted(pages_by_query.items()) if len(pages) > 1],
            "qualified_inquiries": None, "bookings": None, "won_work": None,
            "limits": "Missing queries may be withheld by Google. No volume, ranking forecast, conversion or AI citation inference."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "opportunities", "report"])
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--output", type=Path, help="Optional private docs/seo CSV output for opportunities")
    args = parser.parse_args()
    if args.command == "check":
        paths = sitemap_paths()
        assert_publication_paths(paths, check_rendered=True)
        print(f"SEO gate passed: {len(paths)} canonical URLs; {validate_topics(paths=paths)} owned query variants.")
    elif args.command == "opportunities":
        rows = opportunities()
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        if args.output:
            output = args.output.resolve()
            if not output.is_relative_to(ROOT / "docs" / "seo") or output.suffix != ".csv":
                raise ValueError("opportunity output must be a CSV inside private docs/seo")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(buffer.getvalue(), encoding="utf-8")
            print(f"Wrote {len(rows)} evidenced inventory/candidate rows to {output.name}; not padded to 100.")
        else:
            print(buffer.getvalue(), end="")
    else:
        if not args.csv or not args.start_date or not args.end_date:
            parser.error("report requires --csv, --start-date and --end-date")
        print(json.dumps(analyze_search_csv(args.csv.read_text(encoding="utf-8"), args.start_date, args.end_date), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        print(f"SEO system blocked: {error}", file=sys.stderr)
        sys.exit(1)
