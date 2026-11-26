"""Build readable topic pages from the current saved newspaper records."""
from html import escape
import json
from urllib.parse import urlsplit


def library_page(url):
    parts = urlsplit(str(url))
    return (parts.scheme == 'https' and parts.netloc in {'loc.gov', 'www.loc.gov'}
            and parts.path.startswith(('/resource/', '/item/')))


def topic_page(tool, folder, slug, title, intro, topic, records, source_date, source_total, source_query, start, end):
    site = f"https://coolcode.ca/{tool['id']}/"
    canonical = f"{site}{folder}/{slug}/"
    citations = []
    for record in records:
        if not library_page(record.get('url', '')) or not record.get('title'):
            continue
        place = ', '.join(part.title() for part in (record.get('city'), record.get('state')) if part)
        stamp = ' · '.join(part for part in (record.get('date'), place) if part)
        citations.append(f'<li><span>{escape(stamp)}</span><a href="{escape(record["url"], quote=True)}">'
                         f'{escape(record["title"])}</a></li>')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · CoolCode</title><meta name="description" content="{escape(intro,quote=True)}">
<link rel="canonical" href="{canonical}"><link rel="stylesheet" href="../../topics.css">
<script defer src="/assets/tool-metrics.js" referrerpolicy="no-referrer"></script></head>
<body data-tool="{tool['id']}"><main><nav><a href="../../">{escape(tool['title'])}</a> · <a href="https://coolcode.ca/">CoolCode</a></nav>
<h1>{escape(title)}</h1><p>{escape(intro)}</p><a class="action" href="../../?capture={topic}#search">Open this search and change filters</a>
<h2>Newspaper pages</h2><p>Search phrase <strong>{escape(source_query)}</strong> · {escape(start)} to {escape(end)}.
The Library reported {int(source_total):,} matches on {escape(source_date[:10])}. This capture includes {len(citations)} linked pages.</p>
<ol>{''.join(citations)}</ol><p>Searches cover digitized U.S. newspapers. Open the scan to check the OCR and see the report in context.</p></main></body></html>'''


def write_examples(stage, tool):
    if tool['id'] != APP_ID:
        return ''
    links = []
    for folder, slug, topic, title, intro, records, stamp, total, query, start, end in saved_examples(stage):
        dest = stage / folder / slug
        dest.mkdir(parents=True, exist_ok=True)
        html = topic_page(tool, folder, slug, title, intro, topic, records, stamp, total, query, start, end)
        (dest / 'index.html').write_text(html, encoding='utf-8')
        links.append(f'<li><a href="./{folder}/{slug}/">{escape(title)}</a></li>')
    if not links:
        return ''
    return '<section aria-labelledby="read-examples"><h2 id="read-examples">Browse historical newspaper pages</h2><ul>' + ''.join(links) + '</ul></section>'

APP_ID = 'headlinevault'
EXAMPLES = {
    'canada': ('canadian-railways-1900', 'Canadian Railways in U.S. Newspapers in 1900',
               'Read digitized American newspaper pages that mention Canadian railways in 1900. Follow each citation to its original scan.'),
    'wireless': ('wireless-telegraph-1900', 'Wireless Telegraph Reports in 1900',
                 'Explore contemporary newspaper coverage of wireless telegraphy, with dated American newspaper scans and OCR.'),
    'fraud': ('bank-fraud-1900', 'Bank Fraud Reports in U.S. Newspapers in 1900',
              'Read the original newspaper pages found for the phrase “bank fraud” in 1900. Inspect the scan and publication date before citing a report.'),
}


EXPECTED_PHRASES = {'canada': 'Canadian railway', 'wireless': 'wireless telegraph', 'fraud': 'bank fraud'}


def saved_examples(stage):
    bundle = json.loads((stage / 'data/captures.json').read_text())
    for key, (slug, title, intro) in EXAMPLES.items():
        capture = bundle['captures'].get(key)
        if not capture or not capture.get('records'):
            continue
        query = capture['query']
        if query.get('query') != EXPECTED_PHRASES[key]:
            continue
        if not (query.get('start') == '1900-01-01' and query.get('end') == '1900-12-31'):
            continue
        yield ('search', slug, key, title, intro, capture['records'], capture['capturedAt'],
               capture['total'], query['query'], query['start'], query['end'])
