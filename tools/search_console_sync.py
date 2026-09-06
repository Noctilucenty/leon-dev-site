#!/usr/bin/env python3
"""Bounded, read-only Search Analytics ingestion into private immutable history.

OAuth uses owner-authorized local or environment-injected credentials. auth-login
stores only the offline grant privately; sync keeps access tokens in memory.
No browser/session extraction, indexing, account changes, scheduler, or paid provider.
API contract: https://developers.google.com/webmaster-tools/v1/searchanalytics/query
Data limits: https://developers.google.com/webmaster-tools/v1/how-tos/all-your-data
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zoneinfo import ZoneInfo

try:
    from . import search_console_auth as auth
except ImportError:
    import search_console_auth as auth

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "private" / "seo-search-console"
AUTH_FILE = PRIVATE_ROOT / "oauth-credentials.json"
PROPERTIES = {"https://leonbuilds.org/": "leonbuilds", "https://trycurio.app/": "curio"}
VIEWS = {"summary": [], "daily": ["date"], "query": ["query"],
         "page": ["page"], "query_page": ["query", "page"]}
TOKEN_ENV = "SEO_GSC_ACCESS_TOKEN"
REFRESH_ENV = ("SEO_GSC_CLIENT_ID", "SEO_GSC_CLIENT_SECRET", "SEO_GSC_REFRESH_TOKEN")
OAUTH_ENDPOINT = "https://oauth2.googleapis.com/token"
READONLY_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
MAX_TOKEN_RESPONSE_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_PAGES = 8
LIMITS = [
    "Google may omit anonymized queries and returns top rows, not a complete query census.",
    "Property summary, query, page and joint query/page aggregations are separate; never join their totals.",
    "Missing rows or days are not evidence of zero traffic or complete data availability.",
    "Finalized Web/Image/Video/News API data is not a separate generative-AI report or a conversion report.",
    "Contact-like query and page values are withheld before storage; this is conservative filtering, not a guarantee that all personal data can be recognized.",
]


class SyncBlocked(ValueError):
    """Safe operator-facing reason; never include HTTP bodies or credentials."""


def iso_day(value):
    try:
        day = dt.date.fromisoformat(value)
    except (ValueError, TypeError):
        raise SyncBlocked("Dates must be YYYY-MM-DD.") from None
    if day.isoformat() != value:
        raise SyncBlocked("Dates must be YYYY-MM-DD.")
    return day


def configuration(property_url, start, end, country=None, device=None, search_type="web",
                  row_limit=1000, max_pages=4, today=None):
    if property_url not in PROPERTIES:
        raise SyncBlocked("Only the two explicitly allowed URL-prefix properties are supported.")
    first, last = iso_day(start), iso_day(end)
    today = today or dt.datetime.now(ZoneInfo("America/Los_Angeles")).date()
    if first > last or (last - first).days >= 31:
        raise SyncBlocked("Use an inclusive window of 1–31 days.")
    if last >= today:
        raise SyncBlocked("End before today in Pacific time; the API requests finalized data only.")
    if search_type not in {"web", "image", "video", "news"}:
        raise SyncBlocked("Unsupported search type; do not relabel this API as a generative-AI report.")
    if type(row_limit) is not int or not 1 <= row_limit <= 5000 or type(max_pages) is not int or not 1 <= max_pages <= MAX_PAGES:
        raise SyncBlocked("Pagination must use 1–5000 rows and 1–8 pages per view.")
    if country is not None and (not isinstance(country, str) or not re.fullmatch(r"[A-Za-z]{3}", country)):
        raise SyncBlocked("Country must be an ISO alpha-3 code.")
    if device is not None and (not isinstance(device, str) or device.upper() not in {"DESKTOP", "MOBILE", "TABLET"}):
        raise SyncBlocked("Unsupported device filter.")
    return {"property": property_url, "start_date": start, "end_date": end,
            "date_timezone": "America/Los_Angeles", "data_state": "final", "search_type": search_type,
            "country": country.lower() if country else None, "device": device.upper() if device else None,
            "row_limit": row_limit, "max_pages": max_pages}


def request_body(config, dimensions, start_row=0):
    filters = [{"dimension": name, "operator": "equals", "expression": config[name]}
               for name in ("country", "device") if config[name]]
    body = {"startDate": config["start_date"], "endDate": config["end_date"],
            "dataState": "final", "type": config["search_type"], "dimensions": dimensions,
            "aggregationType": "auto" if "page" in dimensions else "byProperty",
            "rowLimit": config["row_limit"], "startRow": start_row}
    if filters:
        body["dimensionFilterGroups"] = [{"groupType": "and", "filters": filters}]
    return body


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SyncBlocked("Search API redirect refused; credentials were not forwarded.")


def credential_value(value):
    return auth.valid_secret(value)


def local_credentials():
    try:
        return auth.load_credentials(AUTH_FILE)
    except auth.AuthBlocked as error:
        raise SyncBlocked(str(error)) from None


def authentication_status(env=None):
    """Configuration inventory only: never validates access or prints values."""
    env = os.environ if env is None else env
    if env.get(TOKEN_ENV):
        if not credential_value(env[TOKEN_ENV]):
            raise SyncBlocked("SEO_GSC_ACCESS_TOKEN is malformed; no credential values were displayed.")
        return {"status": "configured_unverified", "mode": "access_token", "missing_env": [],
                "limits": ["A supplied access token takes precedence and may expire; configuration is not API access proof."]}
    missing = [name for name in REFRESH_ENV if not env.get(name)]
    if missing:
        if len(missing) == len(REFRESH_ENV) and (AUTH_FILE.exists() or AUTH_FILE.is_symlink()):
            local_credentials()
            return {"status": "configured_unverified", "mode": "local_refresh_token", "missing_env": [],
                    "limits": ["Saved owner consent is available; sync must still verify API and property access."]}
        return {"status": "not_configured", "mode": "refresh_token", "missing_env": missing,
                "limits": ["No Google request was made; missing authorization is not zero search traffic."]}
    if not all(credential_value(env[name]) for name in REFRESH_ENV):
        raise SyncBlocked("Refresh credential environment values are malformed; no values were displayed.")
    return {"status": "configured_unverified", "mode": "refresh_token", "missing_env": [],
            "limits": ["A fresh access token is requested only during sync; configuration is not property access proof."]}


def access_token(env=None):
    """Exchange owner-provided refresh credentials once; retain tokens in memory."""
    env = os.environ if env is None else env
    state = authentication_status(env)
    if state["status"] == "not_configured":
        raise SyncBlocked("OAuth unavailable: supply SEO_GSC_ACCESS_TOKEN or all refresh credential variables; run auth-status for names.")
    if state["mode"] == "access_token":
        return env[TOKEN_ENV]
    credentials = local_credentials() if state["mode"] == "local_refresh_token" else dict(zip(
        ("client_id", "client_secret", "refresh_token"), (env[name] for name in REFRESH_ENV)))
    body = urlencode({**credentials, "grant_type": "refresh_token"})
    request = Request(OAUTH_ENDPOINT, data=body.encode(), method="POST",
                      headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with build_opener(NoRedirects()).open(request, timeout=30) as response:
            raw = response.read(MAX_TOKEN_RESPONSE_BYTES + 1)
        if len(raw) > MAX_TOKEN_RESPONSE_BYTES:
            raise SyncBlocked("OAuth response exceeded the bounded size limit.")
        value = json.loads(raw)
        if (not isinstance(value, dict) or not credential_value(value.get("access_token"))
                or str(value.get("token_type", "")).lower() != "bearer"):
            raise SyncBlocked("OAuth response did not contain a valid bearer token.")
        if "scope" in value and value["scope"] != READONLY_SCOPE:
            raise SyncBlocked("OAuth grant must contain only Search Console read-only access; authorize the documented scope.")
        return value["access_token"]
    except HTTPError as error:
        error.close()
        if error.code in {400, 401, 403}:
            raise SyncBlocked("OAuth refresh was denied or expired; complete owner authorization again. No search values were recorded.") from None
        raise SyncBlocked(f"OAuth refresh returned HTTP {error.code}; no search values were recorded.") from None
    except (URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError):
        raise SyncBlocked("OAuth refresh transport or response failed; credentials were not saved.") from None


def api_query(property_url, body, token):
    if property_url not in PROPERTIES:
        raise SyncBlocked("Property not allowed.")
    if not isinstance(token, str) or not token.strip() or re.search(r"[\s\x00-\x1f]", token):
        raise SyncBlocked("Supply a valid OAuth access token through SEO_GSC_ACCESS_TOKEN.")
    endpoint = "https://www.googleapis.com/webmasters/v3/sites/" + quote(property_url, safe="") + "/searchAnalytics/query"
    request = Request(endpoint, data=json.dumps(body).encode(), method="POST",
                      headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with build_opener(NoRedirects()).open(request, timeout=30) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise SyncBlocked("Search API response exceeded the bounded size limit.")
        return json.loads(raw)
    except HTTPError as error:
        error.close()
        if error.code in {401, 403}:
            raise SyncBlocked("OAuth token or property access was denied; no search values were recorded.") from None
        raise SyncBlocked(f"Search API returned HTTP {error.code}; no partial snapshot was stored.") from None
    except (URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError):
        raise SyncBlocked("Search API transport or response failed; no partial snapshot was stored.") from None


def sensitive_text(value):
    return (len(value) > 1024 or "@" in value or re.search(r"(?:\d[\s()+.-]*){7,}", value)
            or re.search(r"https?://|bearer\s|access[_ -]?token|api[_ -]?key|password|receiptid|bookinguid", value, re.I))


def sanitize_row(row, dimensions, property_url):
    if not isinstance(row, dict):
        raise SyncBlocked("Malformed Search Analytics row.")
    keys = row.get("keys", [])
    if not isinstance(keys, list) or len(keys) != len(dimensions) or any(not isinstance(key, str) for key in keys):
        raise SyncBlocked("Search Analytics row dimensions do not match the request.")
    values = dict(zip(dimensions, keys))
    for name, value in values.items():
        if name == "query" and (not value.strip() or sensitive_text(value)):
            return None
        if name == "page":
            try:
                parsed = urlsplit(value)
            except ValueError:
                return None
            decoded_path = unquote(parsed.path)
            if (parsed.scheme != "https" or parsed.netloc != urlsplit(property_url).netloc
                    or parsed.query or parsed.fragment or "@" in decoded_path
                    or not re.fullmatch(r"/[A-Za-z0-9/_.%~-]*", parsed.path)
                    or re.search(r"(?:\d[\s()+.-]*){7,}|token|receipt|session|password", decoded_path, re.I)):
                return None
        if name == "date":
            iso_day(value)
    metrics = {name: row.get(name) for name in ("clicks", "impressions", "ctr", "position")}
    if any(type(value) not in (float, int) or not math.isfinite(value) for value in metrics.values()):
        raise SyncBlocked("Search metrics must be finite numbers.")
    clicks, impressions = metrics["clicks"], metrics["impressions"]
    if clicks < 0 or impressions < clicks or not float(clicks).is_integer() or not float(impressions).is_integer() or not 0 <= metrics["ctr"] <= 1 or metrics["position"] < 0:
        raise SyncBlocked("Invalid Search Analytics counts or rates.")
    if impressions and abs(metrics["ctr"] - clicks / impressions) > .00001:
        raise SyncBlocked("Search Analytics CTR does not match its own row counts.")
    return {"keys": keys, "clicks": int(clicks), "impressions": int(impressions),
            "ctr": clicks / impressions if impressions else None,
            "position": metrics["position"] if impressions else None}


def collect(config, token, query=None, secret_values=()):
    if not token or not isinstance(token, str) or re.search(r"[\s\x00-\x1f]", token):
        raise SyncBlocked("OAuth unavailable: supply SEO_GSC_ACCESS_TOKEN; missing authorization is not zero traffic.")
    validate_scope(config)
    query = query or api_query
    secrets = [value for value in (token, *secret_values) if isinstance(value, str) and value]
    views = {}
    for name, dimensions in VIEWS.items():
        rows, seen, received, withheld, requests = [], set(), 0, 0, 0
        exhausted = False
        aggregation = "byPage" if "page" in dimensions else "byProperty"
        for index in range(config["max_pages"]):
            result = query(config["property"], request_body(config, dimensions, index * config["row_limit"]), token)
            requests += 1
            if not isinstance(result, dict) or result.get("responseAggregationType") != aggregation:
                raise SyncBlocked("API aggregation differs from the requested measurement surface.")
            raw_rows = result.get("rows", [])
            if not isinstance(raw_rows, list) or len(raw_rows) > config["row_limit"]:
                raise SyncBlocked("API returned an invalid row batch.")
            received += len(raw_rows)
            for raw in raw_rows:
                # The token is never persisted even if a malformed response echoes it.
                if any(value in json.dumps(raw, ensure_ascii=False) for value in secrets):
                    withheld += 1
                    continue
                row = sanitize_row(raw, dimensions, config["property"])
                if row is None:
                    withheld += 1
                    continue
                key = tuple(row["keys"])
                if key in seen:
                    raise SyncBlocked("Duplicate paginated keys; retry later rather than double-count.")
                seen.add(key)
                rows.append(row)
            if len(raw_rows) < config["row_limit"]:
                exhausted = True
                break
        if name == "summary" and len(rows) > 1:
            raise SyncBlocked("Property summary must not contain several aggregate rows.")
        if name == "daily" and any(not config["start_date"] <= row["keys"][0] <= config["end_date"] for row in rows):
            raise SyncBlocked("Daily data falls outside the requested window.")
        views[name] = {"dimensions": dimensions, "aggregation_type": aggregation,
                       "rows": sorted(rows, key=lambda row: row["keys"]), "api_rows_received": received,
                       "privacy_withheld_rows": withheld, "requests": requests,
                       "pagination_exhausted": exhausted, "bounded_cap_reached": not exhausted}
    return {"version": 1, "source": "Google Search Console Search Analytics API", "scope": config,
            "views": views, "limits": LIMITS, "conversions": None, "generative_ai_report": None}


def encoded(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def payload_digest(data):
    return hashlib.sha256(encoded(data)).hexdigest()


def validate_scope(scope):
    try:
        expected = configuration(scope["property"], scope["start_date"], scope["end_date"],
                                 scope["country"], scope["device"], scope["search_type"],
                                 scope["row_limit"], scope["max_pages"])
    except (KeyError, TypeError, AttributeError):
        raise SyncBlocked("Snapshot measurement scope is malformed.") from None
    if scope != expected:
        raise SyncBlocked("Snapshot scope must retain finalized data, Pacific dates and normalized filters.")


def validate_snapshot(data):
    """Validate imported history as data, not as proof of provenance or completeness."""
    try:
        if data["version"] != 1 or set(data["views"]) != set(VIEWS):
            raise SyncBlocked("Snapshot measurement surfaces are invalid.")
        scope = data["scope"]
        validate_scope(scope)
        for name, dimensions in VIEWS.items():
            view = data["views"][name]
            aggregation = "byPage" if "page" in dimensions else "byProperty"
            if view["dimensions"] != dimensions or view["aggregation_type"] != aggregation or not isinstance(view["rows"], list):
                raise SyncBlocked("Snapshot aggregation or rows are invalid.")
            for key in ("api_rows_received", "privacy_withheld_rows", "requests"):
                if type(view[key]) is not int or view[key] < 0:
                    raise SyncBlocked("Snapshot pagination counts are invalid.")
            if (not 1 <= view["requests"] <= scope["max_pages"]
                    or view["api_rows_received"] > view["requests"] * scope["row_limit"]
                    or len(view["rows"]) + view["privacy_withheld_rows"] != view["api_rows_received"]
                    or type(view["pagination_exhausted"]) is not bool or type(view["bounded_cap_reached"]) is not bool
                    or view["pagination_exhausted"] == view["bounded_cap_reached"]):
                raise SyncBlocked("Snapshot pagination accounting is inconsistent.")
            seen = set()
            for stored in view["rows"]:
                raw = dict(stored)
                if raw.get("impressions") == 0:
                    raw.update(ctr=0, position=0)
                sanitized = sanitize_row(raw, dimensions, scope["property"])
                if sanitized != stored or tuple(stored["keys"]) in seen:
                    raise SyncBlocked("Snapshot rows violate privacy, uniqueness or metric validation.")
                seen.add(tuple(stored["keys"]))
                if name == "daily" and not scope["start_date"] <= stored["keys"][0] <= scope["end_date"]:
                    raise SyncBlocked("Snapshot dates fall outside the measured window.")
            if name == "summary" and len(view["rows"]) > 1:
                raise SyncBlocked("Snapshot property summary is not a single aggregate.")
    except (KeyError, TypeError, AttributeError):
        raise SyncBlocked("Snapshot structure is malformed.") from None


def load_snapshot(path):
    try:
        if Path(path).is_symlink():
            raise SyncBlocked("Snapshot must not be a symbolic link.")
        envelope = json.loads(Path(path).read_text(encoding="utf-8"))
        data, digest = envelope["data"], envelope["sha256"]
        if payload_digest(data) != digest or Path(path).stem != digest:
            raise SyncBlocked("Snapshot integrity check failed.")
        validate_snapshot(data)
        return envelope
    except (OSError, ValueError, KeyError, TypeError):
        raise SyncBlocked("Cannot read a valid content-addressed private snapshot.") from None


def store_snapshot(data, private_root=PRIVATE_ROOT):
    validate_snapshot(data)
    property_name = PROPERTIES.get(data["scope"]["property"])
    if not property_name:
        raise SyncBlocked("Snapshot property is not allowed.")
    digest = payload_digest(data)
    private_root = Path(private_root)
    directory = private_root / property_name
    if any(path.is_symlink() for path in (private_root.parent, private_root, directory)):
        raise SyncBlocked("Private storage must not redirect through a symbolic link.")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / (digest + ".json")
    if path.is_symlink():
        raise SyncBlocked("Snapshot must not redirect through a symbolic link.")
    if path.exists():
        if load_snapshot(path)["data"] != data:
            raise SyncBlocked("Existing snapshot does not match; refusing to overwrite it.")
        return {"status": "already_recorded", "path": str(path), "sha256": digest}
    envelope = {"sha256": digest, "first_recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(), "data": data}
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded(envelope) + b"\n")
    except FileExistsError:
        if load_snapshot(path)["data"] != data:
            raise SyncBlocked("Concurrent snapshot differs; refusing to overwrite it.") from None
        return {"status": "already_recorded", "path": str(path), "sha256": digest}
    return {"status": "recorded", "path": str(path), "sha256": digest}


def summary_values(data):
    rows = data["views"]["summary"]["rows"]
    return {key: rows[0][key] if len(rows) == 1 else None for key in ("clicks", "impressions", "ctr", "position")}


def returned_date_coverage(data):
    """Describe observed dates without treating an omitted date as a zero."""
    scope = data["scope"]
    first, last = iso_day(scope["start_date"]), iso_day(scope["end_date"])
    dates = sorted(row["keys"][0] for row in data["views"]["daily"]["rows"])
    requested_count = (last - first).days + 1
    return {"requested_days": requested_count, "returned_days": len(dates),
            "first_returned_date": dates[0] if dates else None,
            "last_returned_date": dates[-1] if dates else None,
            "every_requested_date_returned": len(dates) == requested_count,
            "missing_date_meaning": "unknown: absent rows may reflect no observations, privacy, or unavailable data"}


def compare_windows(previous, current):
    a, b = previous["scope"], current["scope"]
    for key in ("property", "date_timezone", "data_state", "search_type", "country", "device"):
        if a[key] != b[key]:
            raise SyncBlocked("Comparison requires the same property, finalized surface and filters.")
    first_a, last_a, first_b, last_b = map(iso_day, (a["start_date"], a["end_date"], b["start_date"], b["end_date"]))
    if last_a - first_a != last_b - first_b or last_a >= first_b:
        raise SyncBlocked("Compare equal-length, non-overlapping windows in chronological order.")
    before, after = summary_values(previous), summary_values(current)
    delta = {key: after[key] - before[key] if after[key] is not None and before[key] is not None else None
             for key in before}
    return {"status": "compared" if before["impressions"] is not None and after["impressions"] is not None else "insufficient_summary_data",
            "previous_period": [a["start_date"], a["end_date"]], "current_period": [b["start_date"], b["end_date"]],
            "adjacent_windows": first_b == last_a + dt.timedelta(days=1), "before": before, "after": after,
            "date_coverage": {"before": returned_date_coverage(previous), "after": returned_date_coverage(current)},
            "absolute_delta": delta, "ctr_delta_percentage_points": delta["ctr"] * 100 if delta["ctr"] is not None else None,
            "detail_capped": any(view["bounded_cap_reached"] for data in (previous, current) for view in data["views"].values()),
            "limits": LIMITS + ["Observed differences are not proof this release caused a change. Missing dates are not filled with zeros."]}


def history(private_root=PRIVATE_ROOT, property_url="https://leonbuilds.org/", limit=50):
    if property_url not in PROPERTIES or type(limit) is not int or not 1 <= limit <= 500:
        raise SyncBlocked("Choose an allowed property and history limit of 1–500.")
    directory = Path(private_root) / PROPERTIES[property_url]
    paths = sorted(directory.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)[:limit]
    records = []
    for path in paths:
        item = load_snapshot(path)
        if item["data"]["scope"]["property"] != property_url:
            raise SyncBlocked("History directory contains another property.")
        records.append({"sha256": item["sha256"], "first_recorded_at": item["first_recorded_at"],
                        "scope": item["data"]["scope"], "summary": summary_values(item["data"])})
    return {"status": "available" if records else "no_snapshots", "records": records,
            "limit": limit, "limits": ["No snapshots means no imported evidence, not zero search traffic."]}


def private_snapshot_path(value):
    path = Path(value).resolve()
    if not path.is_relative_to(PRIVATE_ROOT.resolve()):
        raise SyncBlocked("Compare only snapshots inside private/seo-search-console.")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("auth-status", help="List configured authentication mode and missing variable names; no Google request")
    login = sub.add_parser("auth-login", help="Authorize a downloaded Desktop OAuth client through a private loopback callback")
    login.add_argument("--client-file", required=True)
    login.add_argument("--timeout-seconds", type=int, default=300)
    login.add_argument("--replace", action="store_true", help="Intentionally replace an existing local grant after consent")
    sync = sub.add_parser("sync", help="Read finalized API data; requires explicitly supplied OAuth")
    sync.add_argument("--property", choices=PROPERTIES, required=True)
    sync.add_argument("--start-date", required=True)
    sync.add_argument("--end-date", required=True)
    sync.add_argument("--country")
    sync.add_argument("--device")
    sync.add_argument("--type", choices=("web", "image", "video", "news"), default="web")
    sync.add_argument("--row-limit", type=int, default=1000)
    sync.add_argument("--max-pages", type=int, default=4)
    listing = sub.add_parser("history", help="Read local private snapshot metadata; no API request")
    listing.add_argument("--property", choices=PROPERTIES, required=True)
    listing.add_argument("--limit", type=int, default=50)
    comparison = sub.add_parser("compare", help="Read two content-addressed private snapshots")
    comparison.add_argument("--previous", required=True)
    comparison.add_argument("--current", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "sync":
            config = configuration(args.property, args.start_date, args.end_date, args.country, args.device, args.type, args.row_limit, args.max_pages)
            state = authentication_status()
            token = access_token()
            secrets = list(local_credentials().values()) if state["mode"] == "local_refresh_token" else [os.environ.get(name) for name in REFRESH_ENV]
            result = store_snapshot(collect(config, token, secret_values=secrets))
        elif args.command == "auth-status":
            result = authentication_status()
        elif args.command == "auth-login":
            result = auth.login(args.client_file, AUTH_FILE,
                                emit=lambda value: print(json.dumps(value), flush=True),
                                timeout_seconds=args.timeout_seconds, replace=args.replace)
        elif args.command == "history":
            result = history(property_url=args.property, limit=args.limit)
        else:
            previous = load_snapshot(private_snapshot_path(args.previous))["data"]
            current = load_snapshot(private_snapshot_path(args.current))["data"]
            result = compare_windows(previous, current)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (SyncBlocked, auth.AuthBlocked, OSError) as error:
        # Only our bounded messages are surfaced. An OS error can contain private
        # paths, so do not echo its raw detail; HTTP bodies never reach this layer.
        reason = str(error) if isinstance(error, (SyncBlocked, auth.AuthBlocked)) else "Private snapshot or authorization storage unavailable."
        print(json.dumps({"status": "BLOCKED", "reason": reason, "metrics": None}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
