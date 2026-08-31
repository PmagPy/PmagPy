"""Check that the splitter resizes the side column: python drag_test.py URL OUT.png"""
import sys, time
from playwright.sync_api import sync_playwright
url, out = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.launch(); page = b.new_page(viewport={"width": 1680, "height": 1050})
    page.goto(url, wait_until="load", timeout=120000); page.wait_for_selector(".step-logger tr[data-i]", timeout=120000); time.sleep(3)
    before = page.locator(".step-logger").first.bounding_box()["width"]
    bar = page.get_by_title("drag to resize the side panel").bounding_box()
    page.mouse.move(bar["x"] + bar["width"] / 2, bar["y"] + 200); page.mouse.down()
    page.mouse.move(bar["x"] + 200, bar["y"] + 200, steps=10); page.mouse.up(); time.sleep(2)
    after = page.locator(".step-logger").first.bounding_box()["width"]
    print(f"logger width before {before:.0f}px, after drag {after:.0f}px")
    page.screenshot(path=out)
    b.close()
    sys.exit(0 if after > before + 100 else 1)
