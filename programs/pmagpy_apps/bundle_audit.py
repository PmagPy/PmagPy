"""
Which of Panel's bundled components the family actually serves.

    python programs/pmagpy_apps/desktop_apps.py --no-window --port 5150      # in one terminal
    python programs/pmagpy_apps/bundle_audit.py http://localhost:5150        # in another

Drives a browser (Playwright, Chromium) through the hub, PmagPy Directions and
PmagPy Intensity on the McMurdo example — every tab, a figure preview, the
generated-code panes — while logging every static request, and prints the
``panel/dist/bundled/<component>`` folders that were asked for, the other static
files, and any request that failed. Compare the folders with
:data:`pmagpy_apps.bundle.KEEP_BUNDLED`: anything requested that is not kept
would be a 404 in the packaged build. Run it again whenever a view gains a new
kind of pane, and against a packaged build (``--no-window``) to confirm nothing
404s there.

    python programs/pmagpy_apps/bundle_audit.py --libs "dist/PmagPy Apps.app"

checks the other cut: that no shared library the trim drops is linked by an
extension module or library that is kept (that is how it was found that
matplotlib's ft2font links raqm and Pillow links xcb in conda-forge's builds).
"""
from __future__ import annotations

import collections
import os
import re
import sys
import time
from urllib.parse import quote


def walk(base: str, directory: str) -> tuple:
    """Visit every page; returns (static paths requested, bundled folders, failed requests)."""
    from playwright.sync_api import sync_playwright
    urls, fails = set(), []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1680, "height": 1050})
        page.on("request", lambda r: urls.add(r.url))
        page.on("response", lambda r: fails.append((r.status, r.url)) if r.status >= 400 else None)
        page.goto(f"{base}/", wait_until="load", timeout=120000)
        page.wait_for_selector("text=Explore the example", timeout=60000)
        page.click("text=Explore the example")
        page.wait_for_selector("text=Analyze", timeout=60000)
        page.click("text=Convert files…")
        page.wait_for_selector("text=Files to convert", timeout=30000)
        page.click("text=← Home")
        page.wait_for_selector("text=Analyze", timeout=30000)
        page.click("text=Change directory…")
        time.sleep(2)
        page.goto(f"{base}/pmagpy_directions?dir={quote(directory)}", wait_until="load", timeout=120000)
        page.wait_for_selector(".step-logger tr[data-i]", timeout=180000)
        for tab in ("Fits", "Means", "Poles", "Export"):
            page.locator(".bk-tab", has_text=re.compile(f"^{tab}$", re.I)).click()
            time.sleep(3)
        page.click("text=Preview current specimen")
        time.sleep(6)
        page.goto(f"{base}/pmagpy_intensity?dir={quote(directory)}", wait_until="load", timeout=120000)
        page.wait_for_selector("text=Arai points", timeout=180000)
        page.click("text=Show code")
        time.sleep(2)
        for tab in ("Interpretations", "Criteria & statistics", "Corrections", "Group results", "BiCEP", "Export"):
            page.locator(".bk-tab", has_text=re.compile(f"^{re.escape(tab)}$", re.I)).click()
            time.sleep(3)
        browser.close()
    static = sorted({re.sub(r"\?.*$", "", u.replace(base, "")) for u in urls if "static" in u or "_assets" in u})
    folders = collections.Counter(re.match(r".*/bundled/([^/]+)/", u).group(1) for u in static if "/bundled/" in u)
    return static, folders, fails


def check_libraries(app_dir: str) -> list:
    """Every shared library a kept binary of the build refers to that the trim would drop.

    Args:
        app_dir: the built ``.app`` (or one-folder build).

    Returns:
        ``[(library name, [binaries that link it])]``; empty when the drop list is safe.
    """
    import glob
    import subprocess
    from pmagpy_apps import bundle
    roots = [os.path.join(app_dir, "Contents", "Frameworks"), app_dir]
    root = next((r for r in roots if os.path.isdir(r)), app_dir)
    binaries = glob.glob(os.path.join(root, "**", "*.so"), recursive=True) + glob.glob(os.path.join(root, "*.dylib"))
    needed = {}
    for path in binaries:
        try:
            out = subprocess.run(["otool", "-L", path], capture_output=True, text=True).stdout
        except OSError:
            return []                                   # not macOS: nothing to check this way
        for line in out.splitlines()[1:]:
            lib = line.strip().split(" (")[0]
            if lib.startswith("@rpath") or lib.startswith("@loader_path"):
                needed.setdefault(os.path.basename(lib), set()).add(os.path.relpath(path, root))
    return [(name, sorted(users)) for name, users in sorted(needed.items()) if not bundle.keep_binary(name)]


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] == "--libs":
        problems = check_libraries(args[1] if len(args) > 1 else "dist/PmagPy Apps.app")
        for name, users in problems:
            print(f"DROPPED but linked: {name} <- {', '.join(users[:4])}")
        print("library check:", "every kept binary's libraries are kept" if not problems else f"{len(problems)} problem(s)")
        return 1 if problems else 0
    from pmagpy_panel import datasets
    base = (args[0] if args else "http://localhost:5150").rstrip("/")
    directory = args[1] if len(args) > 1 else datasets.example_dir("McMurdo")
    static, folders, fails = walk(base, directory)
    from pmagpy_apps.bundle import KEEP_BUNDLED
    print("bundled folders requested:", dict(folders))
    missing = sorted(set(folders) - set(KEEP_BUNDLED))
    print("of which NOT in bundle.KEEP_BUNDLED:", missing or "none")
    print("other static files:", [u for u in static if "/bundled/" not in u and not u.startswith("http")])
    print("failed requests:", fails or "none")
    return 1 if missing or fails else 0


if __name__ == "__main__":
    _HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(_HERE))
    sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))
    sys.exit(main())
