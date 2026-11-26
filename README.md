# Headline Vault

[Open Headline Vault](https://coolcode.ca/headlinevault/) — search historic newspaper pages, inspect original scans and export a research trail.

<!-- coolcode:guide -->
Search any topic with dates, publication place or a newspaper LCCN; pin useful pages and save a JSON receipt or CSV. Saved starting searches load instantly; live searches query the Library of Congress. If a browser cannot read its response, open the exact source JSON and import it locally with its search URL. OCR matches and newspaper claims need checking against the original page.
Use This day 100 years ago to browse the same calendar date a century earlier; select a reference date, newspaper or town, then search OCR words if needed. A blank query is allowed with a date or publication filter. Copy page citations with their original Library of Congress links, or copy a search link that restores filters without searching automatically. The retained collection is shared through data/newspapers.json for other CoolCode newspaper tools. Coverage remains digitized U.S. newspapers, including cross-border reporting; it is not a Canadian newspaper collection.
<!-- /coolcode:guide -->

## Use it

1. Load a saved starting search or enter your own words. Choose an exact phrase, all/any words or a proximity search.
2. Narrow dates, state/city of publication, exact newspaper title or LCCN. These fields are not restricted to a demonstration list.
3. **Search the archive** sends the form through the CoolCode newspaper endpoint to the public loc.gov API. Previous results stay available during slow/failed requests. The Library currently allows 20 JSON requests/minute; the app spaces requests at least 3.5 seconds and has a bounded 90-second timeout.
4. Open **Page & OCR** to inspect the full original. Results are newspaper *pages*, not isolated articles. An opening OCR excerpt may not contain the matched phrase.
5. Pin pages, then save a research receipt or CSV. With no pins, the export contains the current result page. Pins can span searches. Receipts preserve page links, query, retrieval date and source metadata; importing a receipt happens locally and preserves existing pins.

A source count is the Library's count for that query, not a count of verified events or all newspaper coverage. More than 100,000 matches should be narrowed before deep pagination. Do not infer absence from an empty search.

## When a live search fails

The shared service can report source errors or rate limits. Retry after the indicated interval. Earlier results and pins stay available, and both recovery links keep the **attempted query and result page**, including a failed next-page request.

Open **Bring in results from the Library website**:

1. **Open source JSON for this search** opens the exact query directly at the official Library website. If it returns JSON, save that response as a `.json` file. If it shows verification or an error, follow the Library's instructions; an HTML page is not search data.
2. Keep the complete source JSON URL with the saved file. Paste it in **Exact source JSON URL**, or choose **Use the linked search URL** when the file came from the current link, then choose **Import Library JSON**. The URL supplies the query, dates, filters, page and page size; the importer checks the response's page information against it. Unsupported or ambiguous URLs are rejected.
3. Read the imported pages, pin them, and export normally. Imports do not send file contents anywhere or clear earlier pins. Their displayed date is explicitly **import date**, not an invented source retrieval/capture time. Saved app receipts remain importable.

The API request uses the Library's documented `at=results,pagination` projection to avoid unnecessary response fields. This reduces transferred data; it cannot guarantee service availability or faster query execution. No proxy or Cloudflare change is required for the local import option.

## Expand or customize

Edit [`web/config.json`](web/config.json). `defaults` controls the initial form. The `collections` array defines convenient saved starting searches; it does **not** limit live searches or require a code change when its length changes. For example append:

```json
{"id":"halifax","label":"Halifax in 1917","description":"Contemporary U.S. reporting about Halifax.","query":"Halifax explosion","operation":"PHRASE","start":"1917-12-01","end":"1917-12-31"}
```

`state`, `city`, `title`, `lccn` and `sort` can also be set per collection. Titles must match the Library's spelling; LCCN is usually a more stable newspaper identifier. `pageSize` is configurable from 1–100; there is no fixed collection count. Keep `minimumRequestIntervalMs` at least 3000 (default 3500), and `requestTimeoutMs` at most 120000.

Changing config and pushing to `main` publishes the new starting-search choices. A newly added search works live immediately; to populate or refresh its saved capture:

```sh
python3 scripts/collect.py --collection halifax
# Or refresh every configured collection:
python3 scripts/collect.py
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -v
python3 scripts/build.py
```

Commit `web/config.json` and the generated `web/data/captures.json`, then push. Alternatively use **Actions → Headline Vault · Check and publish → Run workflow**, enable **Refresh saved searches**, and run it on `main`. Collection writes only after all selected requests succeed; a failed refresh does not overwrite the last usable file. The default build is offline. Collection is owner-triggered, not a daily archive scrape. Reload an open browser tab to see a newly published configuration/capture.

## Source, rights and privacy

- [Chronicling America](https://www.loc.gov/collections/chronicling-america/), Library of Congress / National Digital Newspaper Program. The modern loc.gov API replaced the legacy Chronicling America API in 2025. No account or key is required.
- [Official newspaper query guide](https://github.com/LibraryOfCongress/data-exploration/blob/master/loc.gov%20JSON%20API/Chronicling_America/README.md), [API rate limits](https://www.loc.gov/apis/json-and-yaml/working-within-limits/), [rights and access](https://www.loc.gov/collections/chronicling-america/about-this-collection/rights-and-access/).
- The Library believes collection newspapers are public domain or have no known restrictions. Check the individual original for reuse; the app does not provide a new blanket licence for third-party material.
- Coverage is digitized **U.S. newspapers**, potentially reporting on Canadian subjects. It is not a complete Canadian newspaper archive. Historic text can be inaccurate or offensive.
- An explicit search sends fields through the CoolCode newspaper endpoint to the Library. It shares recent results for up to an hour. Page thumbnails load from the Library. Pins and imported receipts stay in the tab.

## Development

Source: `web/`. Configuration: `web/config.json`. Saved search data: `web/data/captures.json`. Collector: `scripts/collect.py` (standard library). Tests cover parameter encoding, receipt validation, safe URLs, CSV exports, configurable collection expansion, exact raw JSON import context and timestamps, failure messages, and failure-safe collection. GitHub Actions runs the offline tests/build and a browser smoke check before GitHub Pages publication. Generated `dist/` is not committed.

## Date browsing and shared newspaper collection

Use a blank OCR query with a date, town, paper or LCCN to browse pages rather than matching an artificial word. **This day 100 years ago** uses the selected reference date minus100 calendar years, clamping February29 to February28 if needed. Its source is still Chronicling America’s U.S. newspapers; coverage and title dates vary. The selected current paper/town filters remain active.

Paper and town selectors are derived from all retained captures, not a fixed list; custom inputs accept other supported papers. Copy a page citation for the original scan, exact source date and page number, or copy the query link to reproduce its filters. Shared links restore filters but do not silently send a live search. OCR search happens at the provider; excerpts may not contain the match, and a scan should be checked before quotation.

Every offline build derives `data/newspapers.json` (`coolcode.newspaper-collection.v1`) from the actual retained captures. It exposes paper/LCCN/place metadata and absolute config/capture URLs for reuse by Old News Oddities. Consumers must retain each capture’s own `capturedAt`, source URL, query and coverage, rather than substituting the manifest maximum date. No API key or new collector schedule is needed. Update starting searches in `web/config.json`, run `python3 scripts/collect.py` or its existing manual workflow refresh, validate and publish. The generated manifest updates with that build.

## Optional Library of Congress exemption header

If the Library has issued an access-exemption User-Agent, add an **Actions repository secret** named `LOC_USER_AGENT` under **Settings → Secrets and variables → Actions → New repository secret**. The value is the exact one-line value supplied by the Library: email, one space, then the supplied token. Do not include `LOC_USER_AGENT=`, `User-Agent:`, quotes, a JSON object or a newline. Never put the value in `web/`, `config.json`, a commit, an Actions variable or a browser request.

The workflow passes this secret only to `scripts/collect.py`. `scripts/loc_http.py` sends it only to HTTPS `loc.gov` or `www.loc.gov` on the normal HTTPS port. All redirects are rejected before any private header is forwarded. Network errors use sanitized messages; raw response bodies and headers are not logged. A response echoing the header or token is discarded before it could become a published capture. Without this optional secret, the collector uses its ordinary public User-Agent; it may still encounter the provider's verification challenge.

After adding the secret, manually run the existing Pages workflow with **Refresh saved searches** (Headline Vault) or **Refresh all configured discovery shelves** (Old News Oddities) enabled. A normal code push remains an offline/config-change build and does not prove private-header collection succeeded. The existing request intervals and atomic last-good-capture behavior remain in force. For interactive searches, add the same one-line value as an encrypted Cloudflare Worker secret named `LOC_USER_AGENT` on `coolcode-visitor-api`. Deploy the Worker with its `/api/newspapers/search` route. The app sends search parameters to CoolCode. The Worker attaches the issued header to the fixed Chronicling America HTTPS endpoint, rejects redirects, and shares cached results for an hour. Original-source links and downloaded citations continue to point to the Library.

## Searchable examples

The offline build publishes selected saved searches as static pages with their own titles, original-scan citations and capture dates. Each page links to the complete tool with that capture already selected. The featured searches are declared in `scripts/topic_pages.py`.

When the provider declines or delays a search, the tool checks the currently published saved pages for the same filters and terms. It shows these partial matches separately with their original capture dates. Halifax (exact phrase, 1800–1930) is queued for the next full collector refresh.


### Verified Halifax newspaper pages

A submitted search also checks the saved collection as soon as it starts. Four individually reviewed front pages cover the Halifax explosion on December 7–8, 1917. The two New York citations open digitized PDFs at the Library of Congress. The Oregon pages link to University of Oregon Libraries’ Historic Oregon Newspapers, which marks these scans as public domain. Short excerpts support matching, and each citation displays its publication date and archive. The complete live search runs separately and its totals come from the live response. `web/verified-pages.mjs` holds this reviewed evidence separately from scheduled receipts so a later refresh preserves it.
