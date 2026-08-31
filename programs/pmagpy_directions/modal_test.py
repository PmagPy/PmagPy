"""Open the data modal, switch to another dataset, verify the app reloads: python modal_test.py URL OUT_PREFIX NEW_DIR"""
import sys, time
from playwright.sync_api import sync_playwright
url, prefix, new_dir = sys.argv[1], sys.argv[2], sys.argv[3]
with sync_playwright() as p:
    b = p.chromium.launch(); page = b.new_page(viewport={"width": 1680, "height": 1050})
    page.goto(url, wait_until="load", timeout=120000); page.wait_for_selector(".step-logger tr[data-i]", timeout=120000); time.sleep(3)
    page.get_by_role("button", name="Change data…").click(); time.sleep(2)
    page.screenshot(path=f"{prefix}_modal.png")
    box = page.get_by_role("textbox", name="MagIC directory (must contain measurements.txt)")
    box.fill(new_dir); box.press("Enter"); time.sleep(0.5)
    page.get_by_role("button", name="Load", exact=True).click()
    time.sleep(40)
    switched = page.get_by_text("specimens from Fairchild2017").count()
    n_rows = page.locator(".step-logger tr[data-i]").count()
    print("switched:", switched, "logger rows after switch:", n_rows)
    page.screenshot(path=f"{prefix}_switched.png")
    b.close()
    sys.exit(0 if switched and n_rows > 0 else 1)
