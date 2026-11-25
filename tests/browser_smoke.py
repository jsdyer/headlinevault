"""Exercise the built starter at a project subpath in Chromium."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / "dist", Path(temporary) / "example-tool")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=temporary))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": 1280, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}/example-tool/")
                page.wait_for_selector(".record")
                initial = page.locator(".record").count()
                assert initial > 0
                assert page.locator('#browse-paper option').count() > 1
                assert page.locator('#browse-town option').count() > 1
                assert page.get_by_role('button',name='Copy page citation').count() == initial
                page.locator('#reference-date').fill('2000-02-29')
                page.route('https://www.loc.gov/**',lambda route:route.fulfill(json={'results':[],'pagination':{'of':0}}))
                page.locator('#century-search').click()
                page.wait_for_function("document.querySelector('#status').textContent.includes('Loaded 0')")
                assert page.locator('#start').input_value() == '1900-02-28'
                assert page.locator('#query').input_value() == ''
                page.locator('#load-capture').click()
                page.unroute('https://www.loc.gov/**')
                page.locator(".record button").first.click()
                assert page.locator("#pin-count").inner_text() == "1"
                page.locator("#pinned-only").check()
                assert page.locator(".record").count() == 1
                page.locator("#pinned-only").uncheck()
                page.locator("#query").fill("Halifax explosion")
                assert "qs=Halifax" in page.locator("#source-search").get_attribute("href")
                with page.expect_download() as download:
                    page.locator("#export-json").click()
                assert download.value.suggested_filename.endswith(".json")
                page.locator("#recovery summary").click()
                assert page.locator("#source-json-url").input_value() == ""
                page.locator("#start").fill("1917-12-06")
                page.locator("#end").fill("1917-12-31")
                page.locator("#use-source-json").click()
                source = page.locator("#source-json-url").input_value()
                assert "qs=Halifax" in source
                raw = {"results": [{"id": "https://www.loc.gov/resource/sn12345678/1917-12-10/ed-1/?sp=2", "url": "https://www.loc.gov/resource/sn12345678/1917-12-10/ed-1/?sp=2", "title": "Imported Halifax report", "date": "1917-12-10"}], "pagination": {"current": 1, "perpage": 12, "of": 18, "next": source.replace("sp=1", "sp=2")}}
                page.locator("#source-json-url").fill(source.replace("www.loc.gov", "evil.example"))
                page.locator("#source-import").set_input_files({"name": "source.json", "mimeType": "application/json", "buffer": json.dumps(raw).encode()})
                page.wait_for_function("document.querySelector('#status').textContent.includes('Could not import source JSON')")
                assert page.locator(".record").count() == initial
                assert page.locator("#pin-count").inner_text() == "1"
                page.locator("#use-source-json").click()
                page.locator("#source-import").set_input_files({"name": "source.json", "mimeType": "application/json", "buffer": json.dumps(raw).encode()})
                page.wait_for_function("document.querySelector('#mode').textContent === 'IMPORTED SOURCE JSON'")
                assert page.locator(".record").count() == 1
                assert page.locator(".record h3").inner_text() == "Imported Halifax report"
                assert page.locator("#date-kind").inner_text() == "import date (UTC)"
                assert page.locator("#pin-count").inner_text() == "1"
                # Change the form, then paginate the imported query: recovery must describe the attempted page.
                page.locator("#query").fill("unrelated form edit")
                assert page.locator("#source-json-url").input_value() == source
                def declined(route):
                    assert page.locator("#source-import").is_disabled()
                    assert page.locator("#import").is_disabled()
                    route.fulfill(status=403, content_type="text/html", body="declined")
                page.route("https://www.loc.gov/**", declined)
                page.locator("#next").click()
                page.wait_for_function("document.querySelector('#status').textContent.includes('HTTP 403')")
                assert "sp=2" in page.locator("#source-json").get_attribute("href")
                assert "qs=Halifax" in page.locator("#source-json").get_attribute("href")
                assert "sp=2" in page.locator("#source-search").get_attribute("href")
                assert page.locator(".record").count() == 1
                assert page.locator(".record h3").inner_text() == "Imported Halifax report"
                assert page.locator("#pin-count").inner_text() == "1"
                page.locator("#pinned-only").check()
                assert page.locator(".record").count() == 1
                assert page.locator(".record h3").inner_text() != "Imported Halifax report"
                page.locator("#pinned-only").uncheck()
                page.screenshot(path=str(screenshots / "desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
                assert not errors, errors
                browser.close()
            print("Browser checks passed: project subpath, real saved pages, pins, export, custom query, raw source import/rejection, recovery pagination, failure retention and mobile layout")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
