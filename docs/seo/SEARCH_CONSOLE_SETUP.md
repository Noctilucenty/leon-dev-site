# Connect local Search Console reporting

The helper is implemented and tested offline. Setup is complete only after owner
consent succeeds and an actual `sync` records a private API snapshot.

## Owner setup

Use the `leondragon3798@gmail.com` account that has access to the verified
`https://leonbuilds.org/` URL-prefix property. The separate Google Cloud project
prepared for this task is `leon-builds-search-reporting`; do not reuse the active
Loqol CLI project or its account.

1. Finish the Google Auth Platform app setup in that project. Any Google policy
   acceptance belongs to the owner. Enable **Google Search Console API** for the
   same project. Configure the owner as a test user if the OAuth app is in testing.
2. Create an OAuth client with application type **Desktop app**, then download its
   client JSON to a local private location. The helper accepts that file directly;
   do not copy its contents into a command or chat. A web client, API key, service
   account key or Google password is not the Desktop client file.
3. From the production checkout, run the following command with the actual file
   path. It prints a Google authorization URL and waits up to ten minutes:

   ```sh
   python3 tools/search_console_sync.py auth-login --client-file /absolute/path/to/downloaded-desktop-client.json --timeout-seconds 600
   ```

4. Open the printed URL on this same Mac, choose the owner account, and consent
   only to Search Console read-only access. Google returns to the temporary
   `127.0.0.1` callback. The helper checks the OAuth state and S256 PKCE exchange;
   neither authorization codes nor token values are printed or logged. A denied,
   timed-out, malformed or broader grant is not saved.
5. Run `auth-status`, then the bounded report below. A configured or authorized
   status does not prove that this Google project has API/property access.

Google documents the [Desktop client and loopback authorization flow](https://developers.google.com/identity/protocols/oauth2/native-app)
and the [Search Console read-only scope](https://developers.google.com/webmaster-tools/v1/how-tos/authorizing).
The helper requests `https://www.googleapis.com/auth/webmasters.readonly`, and
never requests write access or sends indexing requests.

## Verify the connection

```sh
python3 tools/search_console_sync.py auth-status
python3 tools/search_console_sync.py sync --property https://leonbuilds.org/ --start-date 2026-08-19 --end-date 2026-09-03
python3 tools/search_console_sync.py history --property https://leonbuilds.org/
```

That initial historical window matches the saved September 5 UI baseline. It is
not a post-release result. A successful sync reads finalized property totals,
daily rows, query rows, page rows, and joint query/page rows separately, then
stores an immutable private snapshot. Privacy-hidden or capped data remain
explicit. Failed refresh/API access returns `BLOCKED` with null metrics and no
partial snapshot. Subsequent comparisons must use equal, non-overlapping windows
and the same property/surface/filters; see [SEO_METRICS.md](SEO_METRICS.md).

The local grant is `private/seo-search-console/oauth-credentials.json`, owned by
the current OS user with mode `600`; its directory is mode `700`. It contains the
client identity and refresh grant, not an access token. The entire `private/`
tree is gitignored and excluded from the static publication allowlist. Never
include this file in reports, artifacts, screenshots, or repository commits.
No scheduler or hosted credential copy is created by this flow.

## Overrides and reconnection

For a separately authorized execution environment, inject all three names
`SEO_GSC_CLIENT_ID`, `SEO_GSC_CLIENT_SECRET`, and `SEO_GSC_REFRESH_TOKEN` through
that environment's secret mechanism. A temporary `SEO_GSC_ACCESS_TOKEN` takes
precedence over both environment refresh credentials and the saved local grant;
remove an expired temporary override to use the saved grant again. A partial
refresh override blocks rather than switching identities silently.

Refresh grants can expire or be revoked under Google's consent and account rules.
An OAuth project left in testing may require renewed owner consent; its status
is not changed by this helper. Reconnect deliberately with the same `auth-login`
command and `--replace`. The prior file stays intact until Google returns the
new valid grant and an atomic replacement succeeds. The helper does not revoke
any other application's access or alter Google policy settings.

## Setup state on September 6, 2026

The dedicated project exists. Search Console API activation and Google Auth
Platform app creation are waiting for the owner's Google terms/policy acceptance.
The OAuth identity fields are prepared but not yet saved. No Desktop OAuth client
has been created or downloaded, no authorization has run, and no credential or API
snapshot has been stored for this connection. After the owner accepts those terms,
finish step 1, create the Desktop client, and run the flow above. Report connected
only after API/property access succeeds in a real sync.
