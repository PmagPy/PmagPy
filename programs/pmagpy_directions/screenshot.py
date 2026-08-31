"""Headless screenshot helper.

    python screenshot.py URL OUT.png [wait_ms] [width] [height] [click_text]

If ``click_text`` is given, the first element with that visible text is
clicked (e.g. a tab title) and the page is given two more seconds before
the screenshot is taken.
"""
import sys
import time

from playwright.sync_api import sync_playwright

url, out = sys.argv[1], sys.argv[2]
wait_ms = int(sys.argv[3]) if len(sys.argv) > 3 else 8000
width = int(sys.argv[4]) if len(sys.argv) > 4 else 1500
height = int(sys.argv[5]) if len(sys.argv) > 5 else 1000
click_text = sys.argv[6] if len(sys.argv) > 6 else None

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": width, "height": height})
    page.goto(url, wait_until="load", timeout=120000)
    time.sleep(wait_ms / 1000)
    if click_text:
        page.get_by_text(click_text, exact=True).first.click()
        time.sleep(3)
    page.screenshot(path=out, full_page=False)
    browser.close()
print("wrote", out)
