"""Exercise the built starter at a project subpath in Chromium."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
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
                page.route("https://www.loc.gov/**", lambda route: route.fulfill(status=503, body="unavailable"))
                page.locator("#search-button").click()
                page.wait_for_function("document.querySelector('#status').classList.contains('error')")
                assert page.locator(".record").count() == initial
                page.screenshot(path=str(screenshots / "desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
                assert not errors, errors
                browser.close()
            print("Browser checks passed: project subpath, real saved pages, pins, export, custom query, failure retention and mobile layout")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
