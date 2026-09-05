"""Offline contract tests: no Google requests or real credentials."""
import copy
import datetime as dt
import io
import json
import math
import os
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from tools import search_console_sync as sync


PROPERTY = "https://leonbuilds.org/"
TOKEN = "offline-test-credential-never-valid-for-google"


def config(**changes):
    arguments = {"property_url": PROPERTY, "start": "2026-08-01", "end": "2026-08-02",
                 "row_limit": 10, "max_pages": 2, "today": dt.date(2026, 9, 5)}
    arguments.update(changes)
    return sync.configuration(**arguments)


def row(keys=(), clicks=2, impressions=10, position=5):
    return {"keys": list(keys), "clicks": clicks, "impressions": impressions,
            "ctr": clicks / impressions if impressions else 0, "position": position}


def response(body, rows):
    return {"rows": rows, "responseAggregationType": "byPage" if "page" in body["dimensions"] else "byProperty"}


def fixture_query(property_url, body, token):
    dimensions = body["dimensions"]
    batches = {(): [row(clicks=6, impressions=56, position=13.2)],
               ("date",): [row([body["startDate"]], clicks=2, impressions=20),
                            row([body["endDate"]], clicks=4, impressions=36)],
               ("query",): [row(["small business website"], clicks=1, impressions=12)],
               ("page",): [row([property_url + "services/"], clicks=4, impressions=40)],
               ("query", "page"): [row(["small business website", property_url + "services/"], clicks=1, impressions=8)]}
    return response(body, batches[tuple(dimensions)] if not body["startRow"] else [])


def snapshot(**changes):
    return sync.collect(config(**changes), TOKEN, query=fixture_query)


class ConfigurationTests(unittest.TestCase):
    def test_allowlisted_properties_finalized_dates_and_filters(self):
        result = config(property_url="https://trycurio.app/", country="HKG", device="mobile")
        self.assertEqual(result["data_state"], "final")
        self.assertEqual(result["date_timezone"], "America/Los_Angeles")
        self.assertEqual((result["country"], result["device"]), ("hkg", "MOBILE"))
        for changes in ({"property_url": "sc-domain:leonbuilds.org"}, {"property_url": "https://example.com/"},
                        {"start": "2026-8-1"}, {"start": "2026-08-03"}, {"end": "2026-09-05"},
                        {"end": "2026-09-01"}, {"country": "HK"}, {"country": 123},
                        {"device": "watch"}, {"device": 5}, {"search_type": "generative_ai"}):
            with self.subTest(changes=changes), self.assertRaises(sync.SyncBlocked):
                config(**changes)

    def test_strict_pagination_bounds_and_maximum_month(self):
        self.assertEqual(config(end="2026-08-31")["end_date"], "2026-08-31")
        for changes in ({"row_limit": 0}, {"row_limit": 5001}, {"row_limit": True},
                        {"max_pages": 0}, {"max_pages": 9}, {"max_pages": 1.5}):
            with self.subTest(changes=changes), self.assertRaises(sync.SyncBlocked):
                config(**changes)


class CollectionTests(unittest.TestCase):
    def test_separate_surfaces_share_dates_and_filters_without_joining_totals(self):
        calls = []

        def query(property_url, body, token):
            calls.append((property_url, copy.deepcopy(body), token))
            return fixture_query(property_url, body, token)

        result = sync.collect(config(country="USA", device="desktop"), TOKEN, query=query)
        self.assertEqual(len(calls), 5)
        self.assertEqual([item[1]["dimensions"] for item in calls], list(sync.VIEWS.values()))
        for property_url, body, token in calls:
            self.assertEqual(property_url, PROPERTY)
            self.assertEqual(token, TOKEN)
            self.assertEqual((body["startDate"], body["endDate"], body["dataState"], body["type"]),
                             ("2026-08-01", "2026-08-02", "final", "web"))
            self.assertEqual(body["dimensionFilterGroups"], [{"groupType": "and", "filters": [
                {"dimension": "country", "operator": "equals", "expression": "usa"},
                {"dimension": "device", "operator": "equals", "expression": "DESKTOP"}]}])
            self.assertEqual(body["aggregationType"], "auto" if "page" in body["dimensions"] else "byProperty")
        self.assertEqual(sync.summary_values(result)["impressions"], 56)
        self.assertEqual(result["views"]["query"]["rows"][0]["impressions"], 12)
        self.assertEqual(result["views"]["page"]["rows"][0]["impressions"], 40)
        self.assertEqual(result["views"]["query_page"]["rows"][0]["impressions"], 8)
        self.assertIsNone(result["conversions"])
        self.assertIsNone(result["generative_ai_report"])
        self.assertNotIn(TOKEN, json.dumps(result))

    def test_pagination_has_explicit_cap_and_distinct_offsets(self):
        calls = []

        def query(property_url, body, token):
            calls.append((tuple(body["dimensions"]), body["startRow"]))
            if body["dimensions"] == ["query"]:
                return response(body, [row([f"topic {body['startRow']}"])])
            return response(body, [])

        result = sync.collect(config(row_limit=1, max_pages=2), TOKEN, query=query)
        self.assertEqual([offset for dimensions, offset in calls if dimensions == ("query",)], [0, 1])
        self.assertEqual(len(calls), 6)
        self.assertTrue(result["views"]["query"]["bounded_cap_reached"])
        self.assertFalse(result["views"]["query"]["pagination_exhausted"])
        self.assertTrue(result["views"]["summary"]["pagination_exhausted"])
        self.assertIsNone(sync.summary_values(result)["impressions"])

    def test_duplicate_page_keys_and_wrong_aggregation_fail_closed(self):
        def repeated(property_url, body, token):
            return response(body, [row(["same query"])]) if body["dimensions"] == ["query"] else response(body, [])

        with self.assertRaisesRegex(sync.SyncBlocked, "Duplicate"):
            sync.collect(config(row_limit=1), TOKEN, query=repeated)
        with self.assertRaisesRegex(sync.SyncBlocked, "aggregation"):
            sync.collect(config(), TOKEN, query=lambda *args: {"rows": [], "responseAggregationType": "byPage"})

    def test_missing_authorization_never_calls_provider(self):
        query = Mock()
        for token in (None, "", " ", "two tokens", "line\nbreak"):
            with self.subTest(token=token), self.assertRaises(sync.SyncBlocked):
                sync.collect(config(), token, query=query)
        query.assert_not_called()

    def test_echoed_token_is_withheld_and_untrusted_metadata_not_stored(self):
        def query(property_url, body, token):
            raw = [dict(row([token]), unexpected_secret=token)] if body["dimensions"] == ["query"] else []
            return dict(response(body, raw), unsafe_metadata=token)

        result = sync.collect(config(), TOKEN, query=query)
        self.assertEqual(result["views"]["query"]["privacy_withheld_rows"], 1)
        self.assertEqual(result["views"]["query"]["rows"], [])
        self.assertNotIn(TOKEN, json.dumps(result))

    def test_out_of_window_daily_data_is_rejected(self):
        def query(property_url, body, token):
            return response(body, [row(["2026-07-31"])]) if body["dimensions"] == ["date"] else response(body, [])

        with self.assertRaisesRegex(sync.SyncBlocked, "outside"):
            sync.collect(config(), TOKEN, query=query)

    def test_direct_collection_cannot_bypass_finalized_scope_or_bounds(self):
        for key, value in (("data_state", "all"), ("max_pages", 100), ("date_timezone", "UTC"),
                           ("property", "https://example.invalid/")):
            scope = dict(config(), **{key: value})
            query = Mock()
            with self.subTest(key=key), self.assertRaises(sync.SyncBlocked):
                sync.collect(scope, TOKEN, query=query)
            query.assert_not_called()


class PrivacyAndTransportTests(unittest.TestCase):
    def test_contact_queries_and_private_page_identifiers_are_withheld(self):
        for query in ("person@example.com", "call +1 (415) 555-1212", "password help", "https://private.example/path", " "):
            with self.subTest(query=query):
                self.assertIsNone(sync.sanitize_row(row([query]), ["query"], PROPERTY))
        for page in (PROPERTY + "contact?email=person@example.com", PROPERTY + "about#email",
                     PROPERTY + "person%40example.com", PROPERTY + "session/private",
                     PROPERTY + "%31%32%33%34%35%36%37", "https://other.example/about", "https://["):
            with self.subTest(page=page):
                self.assertIsNone(sync.sanitize_row(row([page]), ["page"], PROPERTY))
        safe = sync.sanitize_row(row([PROPERTY + "services/ai-automation"]), ["page"], PROPERTY)
        self.assertIsNotNone(safe)

    def test_malformed_metrics_and_dimensions_are_rejected(self):
        for change in ({"clicks": True}, {"position": math.inf}, {"ctr": math.nan}, {"clicks": -1},
                       {"impressions": 1}, {"clicks": 1.5}, {"ctr": .7}, {"keys": []}):
            raw = dict(row(["website help"]), **change)
            with self.subTest(change=change), self.assertRaises(sync.SyncBlocked):
                sync.sanitize_row(raw, ["query"], PROPERTY)
        empty = sync.sanitize_row(row([], clicks=0, impressions=0, position=0), [], PROPERTY)
        self.assertIsNone(empty["ctr"])
        self.assertIsNone(empty["position"])

    def test_api_endpoint_is_allowlisted_read_only_and_credential_not_returned(self):
        payload = json.dumps({"responseAggregationType": "byProperty", "rows": []}).encode()
        stream = Mock()
        stream.__enter__ = Mock(return_value=stream)
        stream.__exit__ = Mock(return_value=False)
        stream.read.return_value = payload
        opener = Mock()
        opener.open.return_value = stream
        with patch.object(sync, "build_opener", return_value=opener):
            result = sync.api_query(PROPERTY, sync.request_body(config(), []), TOKEN)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://www.googleapis.com/webmasters/v3/sites/https%3A%2F%2Fleonbuilds.org%2F/searchAnalytics/query")
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.get_header("Authorization"), "Bearer " + TOKEN)
        self.assertNotIn(TOKEN, json.dumps(result))
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 30)

    def test_http_errors_and_redirects_do_not_echo_or_forward_credentials(self):
        for error in (HTTPError("https://example.invalid/" + TOKEN, 403, TOKEN, {}, io.BytesIO(TOKEN.encode())),
                      HTTPError("https://example.invalid/", 429, TOKEN, {}, None), URLError(TOKEN)):
            with self.subTest(error=type(error).__name__), patch.object(sync, "build_opener") as opener:
                opener.return_value.open.side_effect = error
                with self.assertRaises(sync.SyncBlocked) as caught:
                    sync.api_query(PROPERTY, {}, TOKEN)
                self.assertNotIn(TOKEN, str(caught.exception))
        with self.assertRaisesRegex(sync.SyncBlocked, "not forwarded"):
            sync.NoRedirects().redirect_request(None, None, 302, "", {}, "https://example.invalid/")


class StorageAndComparisonTests(unittest.TestCase):
    def test_content_addressed_history_is_private_immutable_and_idempotent(self):
        data = snapshot()
        with tempfile.TemporaryDirectory() as temporary:
            first = sync.store_snapshot(data, temporary)
            path = Path(first["path"])
            original = path.read_bytes()
            second = sync.store_snapshot(copy.deepcopy(data), temporary)
            self.assertEqual(first["status"], "recorded")
            self.assertEqual(second["status"], "already_recorded")
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(sync.load_snapshot(path)["data"], data)
            updated = snapshot(start="2026-08-03", end="2026-08-04")
            newer = sync.store_snapshot(updated, temporary)
            self.assertNotEqual(first["sha256"], newer["sha256"])
            self.assertEqual(path.read_bytes(), original)
            listing = sync.history(temporary, PROPERTY)
            self.assertEqual(len(listing["records"]), 2)
            self.assertNotIn("small business website", json.dumps(listing))
            self.assertEqual(sync.history(temporary, "https://trycurio.app/")["status"], "no_snapshots")

    def test_corrupted_existing_snapshot_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = snapshot()
            first = sync.store_snapshot(data, temporary)
            path = Path(first["path"])
            path.write_text('{"corrupt":true}')
            with self.assertRaises(sync.SyncBlocked):
                sync.store_snapshot(data, temporary)
            self.assertEqual(path.read_text(), '{"corrupt":true}')

    def test_invalid_scope_or_privacy_rows_cannot_be_saved_even_with_valid_hash(self):
        modifications = [lambda data: data["scope"].update(data_state="all"),
                         lambda data: data["views"]["page"].update(aggregation_type="byProperty"),
                         lambda data: data["views"]["query"]["rows"][0].update(keys=["person@example.com"]),
                         lambda data: data["views"]["query"].update(api_rows_received=999999),
                         lambda data: data["views"]["summary"]["rows"][0].update(ctr=.99)]
        with tempfile.TemporaryDirectory() as temporary:
            for modify in modifications:
                data = snapshot()
                modify(data)
                with self.assertRaises(sync.SyncBlocked):
                    sync.store_snapshot(data, temporary)
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_private_storage_rejects_symlink_redirect(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "public").mkdir()
            (root / "private").symlink_to(root / "public", target_is_directory=True)
            with self.assertRaisesRegex(sync.SyncBlocked, "symbolic"):
                sync.store_snapshot(snapshot(), root / "private")
            self.assertEqual(list((root / "public").iterdir()), [])

    def test_comparison_uses_summary_not_detail_and_preserves_unknowns(self):
        before = snapshot()
        after = snapshot(start="2026-08-03", end="2026-08-04")
        after["views"]["summary"]["rows"] = [row(clicks=9, impressions=60, position=12)]
        result = sync.compare_windows(before, after)
        self.assertEqual(result["before"]["impressions"], 56)
        self.assertEqual(result["absolute_delta"]["impressions"], 4)
        self.assertEqual(result["absolute_delta"]["clicks"], 3)
        self.assertTrue(result["adjacent_windows"])
        self.assertTrue(result["date_coverage"]["after"]["every_requested_date_returned"])
        after["views"]["summary"]["rows"] = []
        after["views"]["daily"]["rows"] = []
        result = sync.compare_windows(before, after)
        self.assertEqual(result["status"], "insufficient_summary_data")
        self.assertIsNone(result["absolute_delta"]["clicks"])
        self.assertIsNone(result["after"]["impressions"])
        self.assertIsNone(result["date_coverage"]["after"]["last_returned_date"])
        self.assertFalse(result["date_coverage"]["after"]["every_requested_date_returned"])

    def test_comparison_rejects_different_surfaces_filters_and_unequal_periods(self):
        before = snapshot()
        for changes in ({"start": "2026-08-03", "end": "2026-08-05"},
                        {"start": "2026-08-02", "end": "2026-08-03"},
                        {"start": "2026-08-03", "end": "2026-08-04", "country": "USA"},
                        {"start": "2026-08-03", "end": "2026-08-04", "search_type": "image"},
                        {"start": "2026-08-03", "end": "2026-08-04", "property_url": "https://trycurio.app/"}):
            with self.subTest(changes=changes), self.assertRaises(sync.SyncBlocked):
                sync.compare_windows(before, snapshot(**changes))

    def test_cli_missing_auth_is_blocked_not_zero_and_does_not_store(self):
        output = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), patch.object(sync, "api_query") as query, \
                patch.object(sync, "store_snapshot") as storage, redirect_stdout(output):
            status = sync.main(["sync", "--property", PROPERTY, "--start-date", "2026-08-01", "--end-date", "2026-08-02"])
        self.assertEqual(status, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "BLOCKED")
        self.assertIsNone(json.loads(output.getvalue())["metrics"])
        query.assert_not_called()
        storage.assert_not_called()

    def test_compare_paths_cannot_read_arbitrary_files(self):
        with self.assertRaises(sync.SyncBlocked):
            sync.private_snapshot_path("/tmp/not-a-private-snapshot.json")


if __name__ == "__main__":
    unittest.main()
