"""Test the published Halifax newspaper search without contacting LOC or the search Worker."""
import asyncio
from urllib.parse import parse_qs, urlsplit
from playwright.async_api import async_playwright

BASE = "https://coolcode.ca"
ARTICLE = BASE + "/headlinevault/search/halifax-explosion-1917/"


async def verify():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(service_workers="block")
        blocked = asyncio.Event()
        release = asyncio.Event()
        requests = []

        async def restrict(route):
            url = urlsplit(route.request.url)
            if url.hostname == "coolcode-visitor-api.jeffdyer.workers.dev" and url.path == "/api/newspapers/search":
                requests.append(parse_qs(url.query))
                blocked.set()
                await release.wait()
                await route.fulfill(status=503, json={"error": {"code": "source_unavailable"}})
            elif url.hostname == "coolcode.ca" and url.path.startswith(("/headlinevault/", "/oldnews-oddities/")):
                await route.continue_()
            else:
                await route.abort()

        await page.route("**/*", restrict)
        response = await page.goto(ARTICLE)
        assert response and response.status == 200
        assert await page.locator('link[rel="canonical"]').count() == 1
        assert await page.locator('link[rel="canonical"]').get_attribute("href") == ARTICLE
        assert await page.locator("ol li a").count() == 4
        await page.get_by_role("link", name="Open and edit the Halifax newspaper search").click()
        assert await page.locator('link[rel="canonical"]').count() == 1
        assert await page.locator('link[rel="canonical"]').get_attribute("href") == BASE + "/headlinevault/"
        await page.locator("#saved-fallback li").first.wait_for()
        assert await page.locator("#saved-fallback li").count() == 4
        assert await page.locator("#query").input_value() == "Halifax"
        assert not requests
        for name in ("headlinevault", "oldnews-oddities"):
            if name == "headlinevault":
                await page.locator("#query").fill("halifax")
                await page.locator("#search-button").click()
            else:
                await page.goto(BASE + "/oldnews-oddities/")
                await page.wait_for_function("document.querySelector('#topics').children.length > 0")
                await page.locator("#query").fill("halifax")
                await page.locator("#operator").select_option("PHRASE")
                await page.locator("#fromYear").fill("1800")
                await page.locator("#toYear").fill("1930")
                await page.locator("#searchSubmit").click()
            await asyncio.wait_for(blocked.wait(), timeout=12)
            query = requests[-1]
            assert [query[key][0] for key in ("qs","ops","start_date","end_date")] == ["halifax","PHRASE","1800-01-01","1930-12-31"]
            assert await page.locator("#saved-fallback li").count() == 4
            assert await page.get_by_role("link",name="The Evening Post, front page").is_visible()
            release.set()
            await page.wait_for_function("document.querySelector('#status').textContent.includes('could not complete')")
            assert await page.locator("#saved-fallback li").count() == 4
            print(name + ": four matching scans visible while pending and after controlled refusal")
            blocked.clear()
            release.clear()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(verify())
