# Connect local Search Console reporting

Local Search Console API access was verified on September 6, 2026 after owner
consent, a successful refresh-token exchange, and an actual private API snapshot.
The setup instructions below also serve as the reconnection procedure.

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
python3 tools/search_console_sync.py sync --property https://leonbuilds.org/ --start-date 2026-08-19 --end-date 2026-09-04
python3 tools/search_console_sync.py history --property https://leonbuilds.org/
```

That initial historical window matches the saved September 6 UI baseline. It is
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
Google's [refresh-token expiration rules](https://developers.google.com/identity/protocols/oauth2#expiration)
give an external app in Testing a seven-day refresh token for this scope. Moving
the app to production does not establish that an already-issued token's lifetime
has changed. Reconnect deliberately with the same `auth-login` command and
`--replace`. The prior file stays intact until Google returns the new valid grant
and an atomic replacement succeeds. Production grants remain subject to Google's
revocation, inactivity and account rules. The helper does not revoke any other
application's access or alter Google policy settings.

## Setup state on September 6, 2026

The owner approved Google's API terms and User Data Policy. The dedicated project,
Search Console API activation, OAuth app and Desktop client, and local owner grant
were completed. The first `sync` successfully refreshed the local grant and read
`https://leonbuilds.org/` with the exact read-only scope. The local connection is
verified; no hosted scheduler or credential copy was created.

Google Auth Platform's Audience page subsequently showed **In production**, a
**Back to testing** control, and **1 user out of a 100-user cap**. Publishing mode
is confirmed; Google app-verification approval has not been established. The
authorized domain, homepage and privacy URLs were saved. The public privacy
disclosure was verified live at [leonbuilds.org/privacy](https://leonbuilds.org/privacy)
from commit `76092207558548bbc2bf15a98a6343e75eb86247`; the
[search workflow](https://github.com/Noctilucenty/leon-dev-site/actions/runs/34051899626)
passed.

**Reconnection completed:** after the app moved to production, the owner completed
Google device verification and consent. `auth-login --replace` returned the exact
read-only scope and saved the replacement grant with mode `600` at
**2026-09-06T18:38:10.265143+00:00**. A subsequent real `sync` refreshed that grant
and successfully read the property again. It returned `already_recorded` with the
same snapshot hash below because the retrieved report was unchanged; the first
snapshot was preserved. This establishes refreshed API/property access after
production-mode reauthorization. It does not assume that the previous Testing
grant's expiry was extended or that the replacement is permanent or irrevocable.

First recorded API snapshot: **2026-09-06T18:22:39.672880+00:00**.
Content hash:
`1c21713c95502e117a0e595bf61a22dfa778e8ab9afa56035773d058f97a99d9`.
The grant, downloaded client file, and snapshot were confirmed owner-only with
mode `600`; private report and credential files are gitignored.

| API observation | Value |
| --- | --- |
| Scope | Web search, finalized data, all countries and devices |
| Reporting window | August 19–September 4, 2026; America/Los_Angeles |
| Property totals | 6 clicks, 58 impressions, 10.3448% CTR, average position 12.8621 |
| Returned daily coverage | 17 of 17 dates, through September 4 |
| Returned rows | 1 property summary, 17 daily, 26 page, 2 query, 2 joint query/page |
| Pagination cap reached | No, on all five surfaces |

Only aggregate results appear here. Query/page detail stays in the private
snapshot. Exhausting the returned pagination is not a complete query census:
Google can withhold queries for privacy, and each aggregation has its own scope.
These historical observations verify reporting access and agree with the dated
UI totals; they do not demonstrate post-release search or lead gains.
