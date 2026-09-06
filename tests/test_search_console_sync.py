"""Offline contract tests: no Google requests or real credentials."""
import copy
import base64
import datetime as dt
import hashlib
import io
import json
import math
import os
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit

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


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.env = dict(zip(sync.REFRESH_ENV, ("offline-client", "offline-client-secret", "offline-refresh")))
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        patcher = patch.object(sync, "AUTH_FILE", Path(temporary.name).resolve() / "oauth-credentials.json")
        patcher.start()
        self.addCleanup(patcher.stop)

    def oauth_response(self, value):
        opener = Mock()
        response = Mock()
        response.read.return_value = json.dumps(value).encode()
        opener.open.return_value.__enter__ = Mock(return_value=response)
        opener.open.return_value.__exit__ = Mock(return_value=False)
        return opener

    def test_inventory_prints_only_names_without_network_or_credentials(self):
        output = io.StringIO()
        with patch.dict(os.environ, self.env, clear=True), patch.object(sync, "build_opener") as network, redirect_stdout(output):
            self.assertEqual(sync.main(["auth-status"]), 0)
        state = json.loads(output.getvalue())
        self.assertEqual((state["status"], state["mode"]), ("configured_unverified", "refresh_token"))
        self.assertEqual(state["missing_env"], [])
        for secret in self.env.values():
            self.assertNotIn(secret, output.getvalue())
        network.assert_not_called()
        partial = sync.authentication_status({sync.REFRESH_ENV[0]: "offline-client"})
        self.assertEqual(partial["status"], "not_configured")
        self.assertEqual(partial["missing_env"], list(sync.REFRESH_ENV[1:]))

    def test_explicit_access_token_precedes_refresh_without_network(self):
        with patch.object(sync, "build_opener") as network:
            self.assertEqual(sync.access_token({**self.env, sync.TOKEN_ENV: TOKEN}), TOKEN)
        network.assert_not_called()

    def test_missing_or_malformed_credentials_do_not_make_a_request(self):
        for env in ({}, {sync.REFRESH_ENV[0]: "offline-client"},
                    {**self.env, sync.REFRESH_ENV[2]: "line\nbreak"},
                    {**self.env, sync.TOKEN_ENV: "invalid token"}):
            with self.subTest(env=env), patch.object(sync, "build_opener") as network, self.assertRaises(sync.SyncBlocked):
                sync.access_token(env)
            network.assert_not_called()

    def test_refresh_posts_only_to_google_and_keeps_access_token_in_memory(self):
        opener = self.oauth_response({"access_token": TOKEN, "token_type": "Bearer", "scope": sync.READONLY_SCOPE})
        with patch.object(sync, "build_opener", return_value=opener) as build:
            self.assertEqual(sync.access_token(self.env), TOKEN)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://oauth2.googleapis.com/token")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Content-type"), "application/x-www-form-urlencoded")
        self.assertIsNone(request.get_header("Authorization"))
        self.assertEqual(parse_qs(request.data.decode()), {"client_id": ["offline-client"],
            "client_secret": ["offline-client-secret"], "refresh_token": ["offline-refresh"], "grant_type": ["refresh_token"]})
        self.assertIsInstance(build.call_args.args[0], sync.NoRedirects)
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 30)

    def test_refresh_response_rejects_invalid_tokens_or_broader_reported_scopes(self):
        for value in ([], {}, {"access_token": "bad token", "token_type": "Bearer"},
                      {"access_token": TOKEN, "token_type": "Unknown"},
                      {"access_token": TOKEN, "token_type": "Bearer", "scope": "https://www.googleapis.com/auth/webmasters"},
                      {"access_token": TOKEN, "token_type": "Bearer", "scope": sync.READONLY_SCOPE + " email"}):
            with self.subTest(value=value), patch.object(sync, "build_opener", return_value=self.oauth_response(value)), self.assertRaises(sync.SyncBlocked):
                sync.access_token(self.env)
        # OAuth does not require a refresh response to repeat unchanged scope.
        with patch.object(sync, "build_opener", return_value=self.oauth_response({"access_token": TOKEN, "token_type": "Bearer"})):
            self.assertEqual(sync.access_token(self.env), TOKEN)

    def test_refresh_errors_never_expose_response_or_credentials(self):
        for error in (HTTPError(sync.OAUTH_ENDPOINT, 400, "offline-refresh", {}, io.BytesIO(b'offline-client-secret')),
                      HTTPError(sync.OAUTH_ENDPOINT, 503, "offline-refresh", {}, None),
                      URLError("offline-client-secret")):
            opener = Mock()
            opener.open.side_effect = error
            with patch.object(sync, "build_opener", return_value=opener), self.assertRaises(sync.SyncBlocked) as caught:
                sync.access_token(self.env)
            self.assertNotIn("offline-refresh", str(caught.exception))
            self.assertNotIn("offline-client-secret", str(caught.exception))

    def test_refresh_response_is_bounded_and_malformed_json_is_sanitized(self):
        for raw in (b'x' * (sync.MAX_TOKEN_RESPONSE_BYTES + 1), b'{offline-refresh', b'\xff'):
            opener = self.oauth_response({})
            opener.open.return_value.__enter__.return_value.read.return_value = raw
            with patch.object(sync, "build_opener", return_value=opener), self.assertRaises(sync.SyncBlocked) as caught:
                sync.access_token(self.env)
            self.assertNotIn("offline-refresh", str(caught.exception))

    def test_cli_refresh_denial_does_not_collect_or_store(self):
        output = io.StringIO()
        with patch.dict(os.environ, self.env, clear=True), patch.object(sync, "access_token", side_effect=sync.SyncBlocked("OAuth refresh denied.")), \
                patch.object(sync, "collect") as collect, patch.object(sync, "store_snapshot") as storage, redirect_stdout(output):
            self.assertEqual(sync.main(["sync", "--property", PROPERTY, "--start-date", "2026-08-01", "--end-date", "2026-08-02"]), 2)
        self.assertIsNone(json.loads(output.getvalue())["metrics"])
        collect.assert_not_called()
        storage.assert_not_called()

    def test_refresh_credentials_echoed_by_malformed_api_data_are_not_saved(self):
        def query(property_url, body, token):
            if body["dimensions"] == ["query"]:
                return response(body, [row(["offline-refresh"]), row(["offline-client-secret"]), row(["small business website"])])
            return fixture_query(property_url, body, token)
        data = sync.collect(config(), TOKEN, query=query, secret_values=self.env.values())
        self.assertEqual(data["views"]["query"]["privacy_withheld_rows"], 2)
        self.assertNotIn("offline-refresh", json.dumps(data))
        self.assertNotIn("offline-client-secret", json.dumps(data))


class OwnerConsentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.client = {"client_id": "offline-client.apps.googleusercontent.com", "client_secret": "offline-secret"}
        self.credentials = {**self.client, "refresh_token": "offline-refresh"}
        self.client_file = self.root / "desktop-client.json"
        self.client_file.write_text(json.dumps({"installed": {**self.client,
            "auth_uri": "https://untrusted.example/auth", "token_uri": "https://untrusted.example/token"}}))
        self.saved = self.root / "private" / "oauth-credentials.json"

    def test_desktop_file_does_not_control_oauth_endpoints(self):
        self.assertEqual(sync.auth.desktop_client(self.client_file), self.client)
        self.client_file.write_text(json.dumps({"web": self.client}))
        with self.assertRaises(sync.auth.AuthBlocked):
            sync.auth.desktop_client(self.client_file)

    def test_authorization_url_requests_only_readonly_offline_scope_with_pkce(self):
        url = sync.auth.authorization_url(self.client["client_id"], "http://127.0.0.1:1234/oauth2/callback", "offline-state", "v" * 64)
        parsed = urlsplit(url)
        self.assertEqual((parsed.scheme, parsed.netloc, parsed.path), ("https", "accounts.google.com", "/o/oauth2/v2/auth"))
        params = parse_qs(parsed.query)
        self.assertEqual(params["scope"], [sync.READONLY_SCOPE])
        self.assertEqual(params["include_granted_scopes"], ["false"])
        self.assertEqual(params["access_type"], ["offline"])
        self.assertEqual(params["code_challenge_method"], ["S256"])
        self.assertEqual(params["code_challenge"], [base64.urlsafe_b64encode(hashlib.sha256(b"v" * 64).digest()).rstrip(b"=").decode()])
        self.assertNotIn("offline-secret", url)

    def test_callback_rejects_state_forgery_duplicates_wrong_paths_and_non_ascii(self):
        accepted = "/oauth2/callback?state=offline-state&code=offline-code"
        self.assertEqual(sync.auth.callback_result(accepted, "offline-state"), {"code": "offline-code"})
        for path in (accepted.replace("offline-state", "other-state"), accepted + "&code=second", "/other?state=offline-state&code=offline-code",
                     accepted + "&state=offline-state", accepted.replace("offline-state", "%E4%B8%AD"), accepted + "#fragment"):
            with self.subTest(path=path):
                self.assertIsNone(sync.auth.callback_result(path, "offline-state"))
        self.assertEqual(sync.auth.callback_result("/oauth2/callback?state=offline-state&error=access_denied", "offline-state"), {"denied": True})

    def test_private_grant_storage_is_atomic_owner_only_and_keeps_access_tokens_out(self):
        with self.assertRaises(sync.auth.AuthBlocked):
            sync.auth.save_credentials(self.saved, {**self.credentials, "access_token": TOKEN})
        self.assertFalse(self.saved.exists())
        sync.auth.save_credentials(self.saved, self.credentials)
        self.assertEqual(stat.S_IMODE(self.saved.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.saved.parent.stat().st_mode), 0o700)
        self.assertEqual(sync.auth.load_credentials(self.saved), self.credentials)
        self.assertNotIn("access_token", self.saved.read_text())
        original = self.saved.read_bytes()
        with self.assertRaises(sync.auth.AuthBlocked):
            sync.auth.save_credentials(self.saved, {**self.credentials, "refresh_token": "changed"})
        self.assertEqual(self.saved.read_bytes(), original)
        sync.auth.save_credentials(self.saved, {**self.credentials, "refresh_token": "reconnected"}, replace=True)
        self.assertEqual(sync.auth.load_credentials(self.saved)["refresh_token"], "reconnected")

    def test_credentials_reject_readable_permissions_symlink_and_wrong_scope(self):
        sync.auth.save_credentials(self.saved, self.credentials)
        self.saved.chmod(0o644)
        with self.assertRaises(sync.auth.AuthBlocked):
            sync.auth.load_credentials(self.saved)
        self.saved.chmod(0o600)
        alias = self.root / "alias.json"
        alias.symlink_to(self.saved)
        with self.assertRaises(sync.auth.AuthBlocked):
            sync.auth.load_credentials(alias)
        value = json.loads(self.saved.read_text()); value["scope"] = "https://www.googleapis.com/auth/webmasters"
        self.saved.write_text(json.dumps(value))
        with self.assertRaises(sync.auth.AuthBlocked):
            sync.auth.load_credentials(self.saved)

    def test_saved_grant_is_loaded_when_environment_is_absent_but_not_when_partial(self):
        sync.auth.save_credentials(self.saved, self.credentials)
        with patch.object(sync, "AUTH_FILE", self.saved):
            self.assertEqual(sync.authentication_status({})["mode"], "local_refresh_token")
            self.assertEqual(sync.authentication_status({sync.REFRESH_ENV[0]: "override"})["status"], "not_configured")
            opener = AuthenticationTests.oauth_response(self, {"access_token": TOKEN, "token_type": "Bearer", "scope": sync.READONLY_SCOPE})
            with patch.object(sync, "build_opener", return_value=opener):
                self.assertEqual(sync.access_token({}), TOKEN)
            self.assertEqual(parse_qs(opener.open.call_args.args[0].data.decode())["refresh_token"], ["offline-refresh"])

    def test_exchange_pins_endpoint_uses_pkce_and_never_saves_access_token(self):
        opener = AuthenticationTests.oauth_response(self, {"access_token": TOKEN, "refresh_token": "offline-refresh",
            "token_type": "Bearer", "scope": sync.READONLY_SCOPE})
        with patch.object(sync.auth, "build_opener", return_value=opener) as build:
            value = sync.auth.exchange_code(self.client, "offline-code", "http://127.0.0.1:1234/oauth2/callback", "v" * 64)
        self.assertEqual(value, self.credentials)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, sync.OAUTH_ENDPOINT)
        self.assertEqual(parse_qs(request.data.decode())["code_verifier"], ["v" * 64])
        self.assertIsInstance(build.call_args.args[0], sync.auth.NoRedirects)

    def test_exchange_rejects_missing_offline_grant_and_error_bodies_are_hidden(self):
        for body in ({"access_token": TOKEN, "token_type": "Bearer", "scope": sync.READONLY_SCOPE},
                     {"access_token": TOKEN, "refresh_token": "offline-refresh", "token_type": "Bearer", "scope": "email"}):
            opener = AuthenticationTests.oauth_response(self, body)
            with patch.object(sync.auth, "build_opener", return_value=opener), self.assertRaises(sync.auth.AuthBlocked):
                sync.auth.exchange_code(self.client, "offline-code", "http://127.0.0.1:1234/oauth2/callback", "v" * 64)
        opener.open.side_effect = HTTPError(sync.OAUTH_ENDPOINT, 400, "offline-code", {}, io.BytesIO(b"offline-secret"))
        with patch.object(sync.auth, "build_opener", return_value=opener), self.assertRaises(sync.auth.AuthBlocked) as caught:
            sync.auth.exchange_code(self.client, "offline-code", "http://127.0.0.1:1234/oauth2/callback", "v" * 64)
        self.assertNotIn("offline-code", str(caught.exception))
        self.assertNotIn("offline-secret", str(caught.exception))

    def test_login_binds_loopback_handles_consent_and_stores_only_after_valid_callback(self):
        emitted = []
        handled = []
        def server_factory(address, handler_class):
            self.assertEqual(address, ("127.0.0.1", 0))
            server = MagicMock(); server.server_port = 4242
            server.__enter__.return_value = server
            def handle():
                params = parse_qs(urlsplit(emitted[0]["authorization_url"]).query)
                handler = object.__new__(handler_class)
                handler.server = server; handler.headers = {"Host": "forged.example:4242" if not handled else "127.0.0.1:4242"}
                handler.path = "/oauth2/callback?" + urlencode({"state": params["state"][0], "code": "offline-code"})
                handler.send_response = Mock(); handler.send_header = Mock(); handler.end_headers = Mock(); handler.wfile = io.BytesIO()
                handler.do_GET()
                handler.send_response.assert_called_once_with(400 if not handled else 200)
                handled.append(True)
                self.assertNotIn(b"offline-code", handler.wfile.getvalue())
            server.handle_request.side_effect = handle
            return server
        with patch.object(sync.auth, "HTTPServer", side_effect=server_factory), \
                patch.object(sync.auth, "exchange_code", return_value=self.credentials) as exchange:
            result = sync.auth.login(self.client_file, self.saved, emit=emitted.append)
        self.assertEqual(result["status"], "authorized_unverified")
        self.assertEqual(len(handled), 2)
        self.assertEqual(sync.auth.load_credentials(self.saved), self.credentials)
        self.assertEqual(exchange.call_args.args[:3], (self.client, "offline-code", "http://127.0.0.1:4242/oauth2/callback"))
        self.assertNotIn("offline-secret", json.dumps(emitted + [result]))
        self.assertNotIn("offline-refresh", json.dumps(emitted + [result]))
        self.assertNotIn("offline-code", json.dumps(emitted + [result]))

    def test_consent_timeout_closes_listener_without_exchange_or_saved_grant(self):
        server = MagicMock(); server.server_port = 4242; server.__enter__.return_value = server
        with patch.object(sync.auth, "HTTPServer", return_value=server), \
                patch.object(sync.auth.time, "monotonic", side_effect=[0, 601]), \
                patch.object(sync.auth, "exchange_code") as exchange, self.assertRaisesRegex(sync.auth.AuthBlocked, "timed out"):
            sync.auth.login(self.client_file, self.saved, emit=lambda value: None)
        exchange.assert_not_called()
        self.assertFalse(self.saved.exists())
        server.__exit__.assert_called_once()


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
                patch.object(sync, "AUTH_FILE", Path("/nonexistent-offline-test/oauth-credentials.json")), \
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
