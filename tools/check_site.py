#!/usr/bin/env python3
"""Fail on broken site metadata/links; warn on search-snippet length drift.

The site is generated and hand-edited in different places, so this deliberately
checks the rendered HTML rather than trusting the page generator's inputs.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_ORIGIN = "https://leonbuilds.org"
INTERNAL_HOSTS = {"leonbuilds.org", "www.leonbuilds.org"}
# Generated publish output mirrors every canonical source page and must never
# be counted as another source tree when developers preview a production build.
SKIP_PARTS = {".git", "dist", "node_modules"}
VERIFICATION_FILE = re.compile(r"^google[a-z0-9]+\.html$", re.I)


@dataclass
class Link:
    href: str
    line: int
    action: bool = False


@dataclass
class Page:
    file: Path
    lang: str = ""
    ids: set[str] = field(default_factory=set)
    h1_lines: list[int] = field(default_factory=list)
    h1_texts: list[str] = field(default_factory=list)
    descriptions: list[tuple[str, int]] = field(default_factory=list)
    canonicals: list[tuple[str, int]] = field(default_factory=list)
    alternates: list[tuple[str, str, int]] = field(default_factory=list)
    schemas: list[tuple[str, int]] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)

    @property
    def label(self) -> str:
        return self.file.relative_to(ROOT).as_posix()


class SiteHTMLParser(HTMLParser):
    def __init__(self, file: Path):
        super().__init__(convert_charrefs=True)
        self.page = Page(file=file)
        self._schema_parts: list[str] | None = None
        self._schema_line = 0
        self._h1_parts: list[str] | None = None

    def handle_starttag(self, tag: str, raw_attrs: list[tuple[str, str | None]]) -> None:
        attrs = {name.lower(): (value or "") for name, value in raw_attrs}
        line = self.getpos()[0]
        tag = tag.lower()

        if attrs.get("id"):
            self.page.ids.add(attrs["id"])
        if tag == "html":
            self.page.lang = attrs.get("lang", "").strip()
        elif tag == "h1":
            self.page.h1_lines.append(line)
            self._h1_parts = []
        elif tag == "meta" and attrs.get("name", "").lower() == "description":
            self.page.descriptions.append((attrs.get("content", "").strip(), line))
        elif tag == "link":
            rels = {part.lower() for part in attrs.get("rel", "").split()}
            href = attrs.get("href", "").strip()
            if "canonical" in rels:
                self.page.canonicals.append((href, line))
            if "alternate" in rels and attrs.get("hreflang"):
                self.page.alternates.append((attrs["hreflang"].strip(), href, line))
        elif tag == "a" and attrs.get("href"):
            self.page.links.append(Link(
                href=attrs["href"].strip(),
                line=line,
                action="data-copy" in attrs,
            ))
        elif tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self._schema_parts = []
            self._schema_line = line

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if self._schema_parts is not None:
            self._schema_parts.append(data)
        if self._h1_parts is not None:
            self._h1_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._schema_parts is not None:
            self.page.schemas.append(("".join(self._schema_parts).strip(), self._schema_line))
            self._schema_parts = None
        if tag.lower() == "h1" and self._h1_parts is not None:
            self.page.h1_texts.append(" ".join("".join(self._h1_parts).split()))
            self._h1_parts = None


def html_files() -> list[Path]:
    return sorted(
        file for file in ROOT.rglob("*.html")
        if not any(part in SKIP_PARTS for part in file.relative_to(ROOT).parts)
        and not VERIFICATION_FILE.match(file.name)
    )


def parse_page(file: Path, errors: list[str]) -> Page:
    parser = SiteHTMLParser(file)
    try:
        parser.feed(file.read_text(encoding="utf-8"))
        parser.close()
    except (OSError, UnicodeError) as exc:
        errors.append(f"{file.relative_to(ROOT)}: cannot read HTML: {exc}")
    return parser.page


def canonical_path(url: str) -> str | None:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return None
    if parsed.scheme != "https" or parsed.netloc != "leonbuilds.org":
        return None
    if parsed.query or parsed.fragment:
        return None
    return urllib.parse.unquote(parsed.path or "/")


def route_aliases(page: Page, canonical: str) -> set[str]:
    rel = page.file.relative_to(ROOT).as_posix()
    aliases = {canonical_path(canonical) or "/", "/" + rel}
    if rel == "index.html":
        aliases.add("/")
    elif rel.endswith("/index.html"):
        directory = "/" + rel[: -len("index.html")]
        aliases.update({directory, directory.rstrip("/")})
    elif rel.endswith(".html"):
        aliases.add("/" + rel[:-5])

    for value in list(aliases):
        if value != "/":
            aliases.add(value.rstrip("/"))
            aliases.add(value.rstrip("/") + "/")
    return aliases


def language_matches(document_lang: str, hreflang: str) -> bool:
    document = document_lang.lower()
    alternate = hreflang.lower()
    if document.startswith("zh") and alternate == "zh":
        return True
    return document == alternate or document.split("-", 1)[0] == alternate


def validate_pages(pages: list[Page], errors: list[str], warnings: list[str]) -> dict[str, Page]:
    by_canonical: dict[str, Page] = {}
    for page in pages:
        if not page.lang:
            errors.append(f"{page.label}: <html> is missing lang")
        if len(page.h1_lines) != 1:
            errors.append(f"{page.label}: expected exactly one H1; found {len(page.h1_lines)}")
        elif not page.h1_texts or not page.h1_texts[0]:
            errors.append(f"{page.label}:{page.h1_lines[0]}: H1 has no text")

        if len(page.descriptions) != 1:
            errors.append(f"{page.label}: expected exactly one meta description; found {len(page.descriptions)}")
        else:
            description, line = page.descriptions[0]
            length = len(description)
            if not description:
                errors.append(f"{page.label}:{line}: meta description is empty")
            elif length > 240:
                errors.append(f"{page.label}:{line}: meta description is {length} characters (hard maximum 240)")
            elif length > 165:
                warnings.append(f"{page.label}:{line}: meta description is {length} characters; target <=165")
            elif length < 50:
                warnings.append(f"{page.label}:{line}: meta description is only {length} characters; target >=50")

        if len(page.canonicals) != 1:
            errors.append(f"{page.label}: expected exactly one canonical; found {len(page.canonicals)}")
        else:
            canonical, line = page.canonicals[0]
            path = canonical_path(canonical)
            if path is None:
                errors.append(f"{page.label}:{line}: canonical must be clean HTTPS leonbuilds.org URL: {canonical!r}")
            elif canonical in by_canonical:
                errors.append(
                    f"{page.label}:{line}: canonical duplicates {by_canonical[canonical].label}: {canonical}"
                )
            else:
                by_canonical[canonical] = page

        if not page.schemas:
            errors.append(f"{page.label}: missing application/ld+json schema")
        for schema, line in page.schemas:
            if not schema:
                errors.append(f"{page.label}:{line}: empty JSON-LD schema")
                continue
            try:
                value = json.loads(schema)
            except json.JSONDecodeError as exc:
                errors.append(f"{page.label}:{line}: invalid JSON-LD: {exc.msg} at JSON line {exc.lineno}")
                continue
            values = value if isinstance(value, list) else [value]
            if not values or not all(isinstance(item, dict) for item in values):
                errors.append(f"{page.label}:{line}: JSON-LD root must be an object or list of objects")
            elif not any("@context" in item for item in values):
                errors.append(f"{page.label}:{line}: JSON-LD has no @context")

    return by_canonical


def validate_sitemap(by_canonical: dict[str, Page], errors: list[str]) -> None:
    sitemap = ROOT / "sitemap.xml"
    try:
        tree = ET.parse(sitemap)
    except (OSError, ET.ParseError) as exc:
        errors.append(f"sitemap.xml: cannot parse: {exc}")
        return

    locations = [
        (element.text or "").strip()
        for element in tree.getroot().iter()
        if element.tag.rsplit("}", 1)[-1] == "loc"
    ]
    duplicates = sorted({url for url in locations if locations.count(url) > 1})
    for url in duplicates:
        errors.append(f"sitemap.xml: duplicate <loc> {url}")

    sitemap_urls = set(locations)
    canonical_urls = set(by_canonical)
    for url in sorted(canonical_urls - sitemap_urls):
        errors.append(f"sitemap.xml: missing canonical {url}")
    for url in sorted(sitemap_urls - canonical_urls):
        errors.append(f"sitemap.xml: URL has no canonical HTML page {url}")


def validate_hreflang(by_canonical: dict[str, Page], errors: list[str]) -> None:
    for canonical, page in by_canonical.items():
        if not page.alternates:
            continue
        mapping: dict[str, str] = {}
        for language, url, line in page.alternates:
            key = language.lower()
            if key in mapping:
                errors.append(f"{page.label}:{line}: duplicate hreflang {language}")
            mapping[key] = url
            if url not in by_canonical:
                errors.append(f"{page.label}:{line}: hreflang target is not a site canonical: {url}")

        if "x-default" not in mapping:
            errors.append(f"{page.label}: hreflang cluster is missing x-default")
        matching = [url for language, url in mapping.items() if language_matches(page.lang, language)]
        if canonical not in matching:
            errors.append(f"{page.label}: hreflang cluster has no self-reference for lang={page.lang!r}")

        for target_url in set(mapping.values()):
            target = by_canonical.get(target_url)
            if not target:
                continue
            target_mapping = {language.lower(): url for language, url, _ in target.alternates}
            if target_mapping != mapping:
                errors.append(
                    f"{page.label}: hreflang cluster differs from reciprocal target {target.label}"
                )


def validate_links(pages: list[Page], by_canonical: dict[str, Page], errors: list[str]) -> None:
    routes: dict[str, Page] = {}
    for canonical, page in by_canonical.items():
        for route in route_aliases(page, canonical):
            existing = routes.get(route)
            if existing and existing is not page:
                errors.append(f"internal route {route!r} maps to both {existing.label} and {page.label}")
            routes[route] = page

    for canonical, page in by_canonical.items():
        for link in page.links:
            href = link.href
            if not href or href.startswith(("mailto:", "tel:", "sms:", "javascript:")):
                continue
            try:
                target_url = urllib.parse.urljoin(canonical, href)
                parsed = urllib.parse.urlsplit(target_url)
            except ValueError:
                errors.append(f"{page.label}:{link.line}: malformed link {href!r}")
                continue
            if parsed.scheme not in {"http", "https"} or parsed.hostname not in INTERNAL_HOSTS:
                continue
            if parsed.scheme != "https":
                errors.append(f"{page.label}:{link.line}: internal link must use HTTPS: {href!r}")

            route = urllib.parse.unquote(parsed.path or "/")
            target = routes.get(route) or routes.get(route.rstrip("/") or "/")
            if not target:
                disk_target = (ROOT / route.lstrip("/")).resolve()
                inside_root = disk_target == ROOT or ROOT in disk_target.parents
                if inside_root and disk_target.is_file():
                    continue
                errors.append(f"{page.label}:{link.line}: broken internal link {href!r}")
                continue

            fragment = urllib.parse.unquote(parsed.fragment)
            if fragment and fragment not in target.ids and not link.action:
                errors.append(
                    f"{page.label}:{link.line}: link {href!r} targets missing #{fragment} in {target.label}"
                )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    pages = [parse_page(file, errors) for file in html_files()]
    if not pages:
        errors.append("no indexable HTML files found")

    by_canonical = validate_pages(pages, errors, warnings)
    validate_sitemap(by_canonical, errors)
    validate_hreflang(by_canonical, errors)
    validate_links(pages, by_canonical, errors)

    for warning in sorted(set(warnings)):
        print(f"site check warning: {warning}")
    for error in sorted(set(errors)):
        print(f"site check failed: {error}", file=sys.stderr)
    if errors:
        print(f"site check: {len(set(errors))} error(s), {len(set(warnings))} warning(s)", file=sys.stderr)
        return 1
    print(
        f"site check passed: {len(pages)} HTML pages, {len(by_canonical)} canonicals, "
        f"{len(warnings)} description warning(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
