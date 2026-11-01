"""Drive the live page from a real Chrome running in Browserbase's cloud.

Opens the site, runs the possession and the exorcism, books an exorcist, and
checks each result. Uses a fixed Playwright script, so it spends browser time
only and no model tokens. Prints the full session link so the run can be
replayed in the Browserbase dashboard.

Run: python scripts/cloud_check.py [url]
"""

import os
import sys
from pathlib import Path

from browserbase import Browserbase
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "docs" / "cloud-check"
PARIS = "The capital of France is Paris."
GHOST = "was always"


def load_env():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip())


def output_has(page, text, timeout=20000):
    page.wait_for_function(
        "t => document.getElementById('output').innerText.includes(t)", arg=text, timeout=timeout
    )


def main():
    load_env()
    url = sys.argv[1] if len(sys.argv) > 1 else "https://the-possession.vercel.app"
    client = Browserbase(api_key=os.environ["BROWSERBASE_API_KEY"])
    session = client.sessions.create(timeout=180)
    print(f"Session: https://www.browserbase.com/sessions/{session.id}")

    SHOTS.mkdir(parents=True, exist_ok=True)
    results = []

    def check(name, passed):
        results.append((name, passed))
        print(("PASS " if passed else "FAIL ") + name)

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(session.connect_url)
        page = browser.contexts[0].pages[0]
        page.set_viewport_size({"width": 1280, "height": 860})
        try:
            page.goto(url, wait_until="networkidle")
            page.get_by_role("button", name="What is the capital of France?").click()
            output_has(page, PARIS)
            check("clean model answers Paris", True)

            page.evaluate(
                "() => { const s = document.getElementById('strength'); s.value = 3; s.dispatchEvent(new Event('input')); }"
            )
            output_has(page, GHOST)
            check("possession changes the answer", PARIS not in page.inner_text("#output"))
            page.screenshot(path=str(SHOTS / "possessed.png"))

            page.click("#exorcise")
            output_has(page, PARIS)
            check("exorcism restores Paris", True)
            page.screenshot(path=str(SHOTS / "exorcised.png"))

            page.locator(".exorcist button").first.click()
            checkout = page.locator("#checkout")
            checkout.wait_for(state="visible")
            check("booking shows a 90/10 split", "$13.50" in checkout.inner_text() and "$1.50" in checkout.inner_text())
        except Exception as error:
            check(f"run completed ({type(error).__name__})", False)
        finally:
            browser.close()

    print(f"Replay: https://www.browserbase.com/sessions/{session.id}")
    failed = [name for name, passed in results if not passed]
    print(f"{len(results) - len(failed)} of {len(results)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
