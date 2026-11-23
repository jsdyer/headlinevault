# Headline Vault

[Open Headline Vault](https://coolcode.ca/headlinevault/) — search historic newspaper pages, inspect original scans and export a research trail.

<!-- coolcode:guide -->
Search any topic with dates, publication place or a newspaper LCCN; pin useful pages and save a JSON receipt or CSV. Saved starting searches load instantly, while live searches query the Library of Congress; OCR matches and newspaper claims need checking against the original page.
<!-- /coolcode:guide -->

## Use it

1. Load a saved starting search or enter your own words. Choose an exact phrase, all/any words or a proximity search.
2. Narrow dates, state/city of publication, exact newspaper title or LCCN. These fields are not restricted to a demonstration list.
3. **Search the archive** makes an on-demand request to the public loc.gov API. Previous results stay available during slow/failed requests. The Library currently allows 20 JSON requests/minute; the app spaces requests at least 3.5 seconds and has a bounded 90-second timeout.
4. Open **Page & OCR** to inspect the full original. Results are newspaper *pages*, not isolated articles. An opening OCR excerpt may not contain the matched phrase.
5. Pin pages, then save a research receipt or CSV. With no pins, the export contains the current result page. Pins can span searches. Receipts preserve page links, query, retrieval date and source metadata; importing a receipt happens locally.

A source count is the Library's count for that query, not a count of verified events or all newspaper coverage. More than 100,000 matches should be narrowed before deep pagination. Do not infer absence from an empty search.

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
- Search fields are sent directly to loc.gov only on explicit search/pagination. Remote page thumbnails load from Library of Congress. Pins and imported receipts stay in memory; export to retain them. No account, personal API key, proxy or secret is needed.

## Development

Source: `web/`. Configuration: `web/config.json`. Saved search data: `web/data/captures.json`. Collector: `scripts/collect.py` (standard library). Tests cover parameter encoding, receipt validation, safe URLs, CSV exports, configurable collection expansion and failure-safe collection. GitHub Actions runs the offline tests/build and a browser smoke check before GitHub Pages publication. Generated `dist/` is not committed.
