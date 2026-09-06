"""Owner-driven Desktop OAuth consent for local read-only Search Console reports.

Only Google's fixed OAuth endpoints receive credentials. The loopback callback
never logs request URLs, authorization codes, tokens, or errors from Google.
"""
from __future__ import annotations

import base64
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import stat
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
MAX_BYTES = 64 * 1024


class AuthBlocked(ValueError):
    pass


def valid_secret(value):
    return isinstance(value, str) and 0 < len(value) <= 16384 and not re.search(r"[^\x21-\x7e]", value)


def read_json(path, private=False):
    """Bound file reads and refuse symlinks; saved refresh grants must be private."""
    try:
        path = Path(path).expanduser()
        if any(parent.is_symlink() for parent in (path, *path.parents)):
            raise AuthBlocked("OAuth files must not use symbolic links.")
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode) or (private and (info.st_uid != os.getuid() or info.st_mode & 0o077)):
                raise AuthBlocked("Saved OAuth credentials must be an owner-only regular file (mode 600).")
            data = handle.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise AuthBlocked("OAuth credential file exceeds the bounded size limit.")
        result = json.loads(data)
        if not isinstance(result, dict):
            raise AuthBlocked("OAuth credential file is malformed.")
        return result
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise AuthBlocked("Cannot read the OAuth credential file; no file contents were displayed.") from None


def desktop_client(path):
    value = read_json(path).get("installed")
    if (not isinstance(value, dict) or not valid_secret(value.get("client_id"))
            or not value["client_id"].endswith(".apps.googleusercontent.com")
            or not valid_secret(value.get("client_secret"))):
        raise AuthBlocked("Download an OAuth Desktop app client JSON from the intended Google Cloud project.")
    # Endpoints and callback hosts in downloaded input never control requests.
    return {key: value[key] for key in ("client_id", "client_secret")}


def load_credentials(path):
    value = read_json(path, private=True)
    if (value.get("version") != 1 or value.get("scope") != SCOPE
            or not all(valid_secret(value.get(key)) for key in ("client_id", "client_secret", "refresh_token"))):
        raise AuthBlocked("Saved credentials are malformed or are not the read-only Search Console grant.")
    return {key: value[key] for key in ("client_id", "client_secret", "refresh_token")}


def storage_directory(path, replace=False):
    path = Path(path)
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise AuthBlocked("OAuth storage must not use symbolic links.")
    if path.exists() and not replace:
        raise AuthBlocked("Saved credentials already exist; use --replace only to intentionally reconnect.")
    if path.exists() and (not path.is_file() or path.stat().st_uid != os.getuid()):
        raise AuthBlocked("Existing OAuth storage is not an owner-controlled regular file.")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.stat().st_uid != os.getuid():
        raise AuthBlocked("OAuth directory must belong to the current user.")
    path.parent.chmod(0o700)
    return path


def save_credentials(path, credentials, replace=False):
    fields = {"client_id", "client_secret", "refresh_token"}
    if (not isinstance(credentials, dict) or set(credentials) != fields
            or not all(valid_secret(credentials[key]) for key in fields)):
        raise AuthBlocked("Only the validated offline grant can enter private OAuth storage.")
    path = storage_directory(path, replace)
    value = {"version": 1, "scope": SCOPE, **credentials}
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=".oauth-", delete=False) as handle:
            temporary = Path(handle.name)
            os.fchmod(handle.fileno(), 0o600)
            json.dump(value, handle)
            handle.write("\n")
        if replace:
            os.replace(temporary, path)
        else:
            # Atomic create-only publication: another login must not be overwritten.
            os.link(temporary, path)
    except OSError:
        raise AuthBlocked("Could not save private OAuth credentials; no credential values were displayed.") from None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def authorization_url(client_id, redirect_uri, state, verifier):
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return AUTH_ENDPOINT + "?" + urlencode({"client_id": client_id, "redirect_uri": redirect_uri,
        "response_type": "code", "scope": SCOPE, "access_type": "offline", "prompt": "consent",
        "include_granted_scopes": "false", "state": state, "code_challenge": challenge,
        "code_challenge_method": "S256"})


def callback_result(path, state):
    parsed = urlsplit(path)
    if parsed.path != "/oauth2/callback" or parsed.fragment or len(path) > 16384:
        return None
    try:
        values = parse_qs(parsed.query, keep_blank_values=True, max_num_fields=12)
    except ValueError:
        return None
    received = values.get("state", [])
    if len(received) != 1 or not valid_secret(received[0]) or not secrets.compare_digest(received[0], state):
        return None
    if "error" in values:
        return {"denied": True}
    codes = values.get("code", [])
    if len(codes) != 1 or not valid_secret(codes[0]):
        return None
    return {"code": codes[0]}


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise AuthBlocked("OAuth redirect refused; credentials were not forwarded.")


def exchange_code(client, code, redirect_uri, verifier):
    request = Request(TOKEN_ENDPOINT, data=urlencode({**client, "code": code,
        "redirect_uri": redirect_uri, "grant_type": "authorization_code", "code_verifier": verifier}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with build_opener(NoRedirects()).open(request, timeout=30) as response:
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise AuthBlocked("OAuth response exceeded the bounded size limit.")
        value = json.loads(raw)
        if (not isinstance(value, dict) or value.get("scope") != SCOPE
                or str(value.get("token_type", "")).lower() != "bearer"
                or not valid_secret(value.get("refresh_token")) or not valid_secret(value.get("access_token"))):
            raise AuthBlocked("Google did not return the exact read-only offline grant; reconnect with only the documented scope.")
        return {**client, "refresh_token": value["refresh_token"]}
    except HTTPError as error:
        error.close()
        raise AuthBlocked(f"Google OAuth exchange returned HTTP {error.code}; no grant was stored.") from None
    except (OSError, URLError, UnicodeError, json.JSONDecodeError):
        raise AuthBlocked("Google OAuth exchange failed; no grant was stored.") from None


def login(client_file, credentials_file, emit, timeout_seconds=300, replace=False):
    if type(timeout_seconds) is not int or not 30 <= timeout_seconds <= 600:
        raise AuthBlocked("Authorization timeout must be 30–600 seconds.")
    client = desktop_client(client_file)
    destination = storage_directory(credentials_file, replace)
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(64)
    received = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def setup(self):
            super().setup()
            self.connection.settimeout(2)

        def do_GET(self):
            result = None
            if self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}":
                try:
                    result = callback_result(self.path, state)
                except ValueError:
                    pass
            if result:
                received.update(result)
            self.send_response(200 if result else 400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'none'")
            self.end_headers()
            self.wfile.write(b"Authorization received. Return to your Leon Builds task." if result else b"Invalid authorization callback.")

    with HTTPServer(("127.0.0.1", 0), CallbackHandler) as server:
        server.timeout = 1
        redirect_uri = f"http://127.0.0.1:{server.server_port}/oauth2/callback"
        emit({"status": "awaiting_owner_consent", "authorization_url": authorization_url(client["client_id"], redirect_uri, state, verifier),
              "scope": SCOPE, "expires_in_seconds": timeout_seconds})
        deadline = time.monotonic() + timeout_seconds
        while not received and time.monotonic() < deadline:
            server.handle_request()
    if received.get("denied"):
        raise AuthBlocked("Google consent was declined; no grant was stored.")
    if not received.get("code"):
        raise AuthBlocked("Owner authorization timed out; no grant was stored.")
    credentials = exchange_code(client, received["code"], redirect_uri, verifier)
    save_credentials(destination, credentials, replace)
    return {"status": "authorized_unverified", "mode": "local_refresh_token", "scope": SCOPE,
            "limits": ["Credentials were saved privately; run sync to verify API and property access. No account setting or search report was changed."]}
