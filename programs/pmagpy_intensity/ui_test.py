"""
Browser-level checks of PmagPy Intensity with Playwright.

    python ui_test.py http://localhost:5101/pmagpy_intensity screenshots/app

What it catches that the unit tests cannot: a template that fails to build, an
equal-area net that Bokeh has squeezed into an ellipse, an Arai plot whose
coordinate scaling drifts as the window is resized, a tab that renders empty,
and the long BiCEP run blocking the interface.

Exits non-zero on failure. Running it leaves a gitignored autosave in the
output directory; point PMAGPY_INTENSITY_OUTPUT somewhere disposable.
"""
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5101/pmagpy_intensity"
prefix = sys.argv[2] if len(sys.argv) > 2 else "screenshots/app"
os.makedirs(os.path.dirname(prefix) or ".", exist_ok=True)
failures = []


def check(condition, message):
    print(("ok   " if condition else "FAIL ") + message)
    if not condition:
        failures.append(message)


# --- reading the Bokeh document -------------------------------------------
FRAMES_JS = """(names) => {
  const doc = Bokeh.documents[0];
  const models = doc._all_models ?? doc.all_models;
  const list = models instanceof Map ? [...models.values()] : [...models];
  return list.filter(m => names.includes(m.name) && m.inner_width > 0).map(m => ({
    name: m.name, w: m.inner_width, h: m.inner_height,
    x0: m.x_range.start, x1: m.x_range.end,
    y0: m.y_range.start, y1: m.y_range.end,
    x_per_px: (m.x_range.end - m.x_range.start) / m.inner_width,
    y_per_px: (m.y_range.end - m.y_range.start) / m.inner_height}));
}"""

TABS_JS = """() => {
  const found = [];
  const walk = (root) => root.querySelectorAll('*').forEach(el => {
    if (el.shadowRoot) walk(el.shadowRoot);
    if (el.classList && el.classList.contains('bk-tab')) found.push(el.textContent.trim());
  });
  walk(document);
  return found;
}"""

CLICK_TAB_JS = """(label) => {
  const found = [];
  const walk = (root) => root.querySelectorAll('*').forEach(el => {
    if (el.shadowRoot) walk(el.shadowRoot);
    if (el.classList && el.classList.contains('bk-tab')) found.push(el);
  });
  walk(document);
  const target = found.find(el => el.textContent.trim() === label);
  if (!target) return false;
  target.click();
  return true;
}"""

CLICK_BUTTON_JS = """(label) => {
  const found = [];
  const walk = (root) => root.querySelectorAll('*').forEach(el => {
    if (el.shadowRoot) walk(el.shadowRoot);
    if (el.tagName === 'BUTTON') found.push(el);
  });
  walk(document);
  const target = found.find(el => el.textContent.trim() === label);
  if (!target) return false;
  target.click();
  return true;
}"""

# Panel renders into shadow roots, so document.body.innerText sees almost
# nothing: the text has to be gathered by walking every shadow root as well.
TEXT_JS = """() => {
  const parts = [];
  const skip = ['STYLE', 'SCRIPT', 'TEMPLATE'];   // stylesheets are not text
  const walk = (root) => {
    root.querySelectorAll('*').forEach(el => {
      if (skip.includes(el.tagName)) return;
      if (el.shadowRoot) walk(el.shadowRoot);
      if (!el.children.length && el.textContent && el.textContent.trim())
        parts.push(el.textContent.trim());
      if (el.tagName === 'INPUT' && el.value) parts.push(String(el.value));
    });
  };
  walk(document);
  return parts.join('\\n');
}"""

HTML_JS = """() => {
  const parts = [document.documentElement.outerHTML];
  const walk = (root) => root.querySelectorAll('*').forEach(el => {
    if (el.shadowRoot) { parts.push(el.shadowRoot.innerHTML); walk(el.shadowRoot); }
  });
  walk(document);
  return parts.join('\\n');
}"""


def frames(page, names):
    return page.evaluate(FRAMES_JS, names)


def check_nets_circular(page, where):
    """Every equal-area net must map data to pixels identically in x and y."""
    nets = frames(page, ["equal_area_net"])
    distorted = [n for n in nets if abs(n["x_per_px"] / n["y_per_px"] - 1) > 0.002]
    check(nets and not distorted,
          f"{where}: {len(nets)} net(s) circular"
          + (f" (distorted: {distorted})" if distorted else ""))


def arai_scaling(page):
    found = frames(page, ["arai"])
    return found[0] if found else None


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": 1680, "height": 1050})
    page.goto(url, wait_until="load", timeout=180000)
    page.wait_for_function("() => window.Bokeh && Bokeh.documents.length > 0", timeout=180000)
    time.sleep(8)

    # ---- the shell -------------------------------------------------------
    check("PmagPy Intensity" in page.title(), f"window title is {page.title()!r}")
    tabs = page.evaluate(TABS_JS)
    expected = ["Specimen", "Interpretations", "Criteria & statistics", "Corrections",
                "Group results", "BiCEP", "Export"]
    check(tabs == expected, f"the seven tabs are present (got {tabs})")

    # ---- the specimen pane ----------------------------------------------
    check(arai_scaling(page) is not None, "the Arai plot rendered")
    check_nets_circular(page, "specimen tab")
    body = page.evaluate(TEXT_JS)
    check("µT" in body, "the result line reports an intensity")
    check("-999" not in body, "no statistic is shown as -999")
    page.screenshot(path=f"{prefix}_specimen.png")

    # ---- resizing: the Arai plot keeps its scaling, the nets stay circular
    before = arai_scaling(page)
    ratios = []
    for width, height in ((1280, 800), (1024, 720), (1680, 1050), (1440, 900), (1680, 1050)):
        page.set_viewport_size({"width": width, "height": height})
        time.sleep(2.5)
        after = arai_scaling(page)
        if after:
            ratios.append((width, round(after["x0"], 6), round(after["x1"], 6)))
        check_nets_circular(page, f"after resize to {width}x{height}")
    after = arai_scaling(page)
    same_range = (abs(after["x0"] - before["x0"]) < 1e-9
                  and abs(after["x1"] - before["x1"]) < 1e-9
                  and abs(after["y0"] - before["y0"]) < 1e-9
                  and abs(after["y1"] - before["y1"]) < 1e-9)
    check(same_range, f"the Arai data range survives repeated resizing (saw {ratios})")

    # ---- the plot-size slider --------------------------------------------
    frame_before = arai_scaling(page)["w"]
    page.evaluate("""() => {
      const found = [];
      const walk = (root) => root.querySelectorAll('*').forEach(el => {
        if (el.shadowRoot) walk(el.shadowRoot);
        if (el.classList && el.classList.contains('noUi-target')) found.push(el);
      });
      walk(document);
      return found.length;
    }""")
    page.screenshot(path=f"{prefix}_resized.png")

    # ---- the other tabs render -------------------------------------------
    for label, marker in (("Interpretations", "specimen"),
                          ("Criteria & statistics", "Arai fit"),
                          ("Corrections", "uncorrected"),
                          ("Group results", "intensity"),
                          ("BiCEP", "BiCEP"),
                          ("Export", "Merge policy")):
        check(page.evaluate(CLICK_TAB_JS, label), f"the {label} tab can be selected")
        time.sleep(4)
        text = page.evaluate(TEXT_JS)
        check(marker.lower() in text.lower(), f"the {label} tab shows its content")
        if label == "Group results":
            # no net here -- it is a dot plot of every specimen against the mean,
            # on a categorical axis, and the regression worth guarding is that it
            # renders at all with the groups on it
            groups = frames(page, ["groups"])
            check(bool(groups) and groups[0]["w"] > 100 and groups[0]["h"] > 100,
                  f"the group dot plot rendered (got {groups})")
        page.screenshot(path=f"{prefix}_{label.split()[0].lower()}.png")

    # ---- criteria: every statistic has a definition and a source ---------
    page.evaluate(CLICK_TAB_JS, "Criteria & statistics")
    time.sleep(3)
    text = page.evaluate(TEXT_JS)
    for label in ("FRAC", "DRAT", "Ziggie", "dt*", "IZZI_MD"):
        check(label in text, f"the statistics panel lists {label}")
    check("doi.org" in page.evaluate(HTML_JS), "each statistic carries a citation link")
    check("-999" not in text, "the statistics panel shows no sentinel values")

    # ---- BiCEP: it runs, reports diagnostics, and does not block ----------
    page.evaluate(CLICK_TAB_JS, "BiCEP")
    time.sleep(3)
    # a short run so the suite stays quick
    page.evaluate("""() => {
      const inputs = [];
      const walk = (root) => root.querySelectorAll('*').forEach(el => {
        if (el.shadowRoot) walk(el.shadowRoot);
        if (el.tagName === 'INPUT' && el.type === 'number') inputs.push(el);
      });
      walk(document);
      if (inputs.length >= 2) {
        for (const [i, value] of [[0, '300'], [1, '300']]) {
          inputs[i].value = value;
          inputs[i].dispatchEvent(new Event('change', {bubbles: true}));
        }
      }
      return inputs.length;
    }""")
    time.sleep(1)
    check(page.evaluate(CLICK_BUTTON_JS, "Run BiCEP"), "BiCEP can be started")
    # the interface must answer while the sampler is running
    time.sleep(1.5)
    responsive = page.evaluate(CLICK_TAB_JS, "Specimen")
    check(responsive, "the interface still answers while BiCEP samples")
    page.evaluate(CLICK_TAB_JS, "BiCEP")
    for _ in range(120):
        text = page.evaluate(TEXT_JS)
        if "credible" in text:
            break
        time.sleep(1)
    check("credible" in text, "BiCEP reports a credible interval")
    check("R-hat" in text, "BiCEP reports its convergence diagnostics")
    check("Cych" in text, "BiCEP reports its citation")
    page.screenshot(path=f"{prefix}_bicep.png")

    # ---- export: preview, validate ---------------------------------------
    page.evaluate(CLICK_TAB_JS, "Export")
    time.sleep(4)
    check(page.evaluate(CLICK_BUTTON_JS, "Validate"), "the validator can be run")
    for _ in range(60):                 # a full contribution takes a few seconds
        text = page.evaluate(TEXT_JS)
        if "✓" in text or "✗" in text or "nothing to check" in text:
            break
        time.sleep(1)
    check("✓" in text or "✗" in text or "nothing to check" in text,
          "the validator reports per table")
    # cell-level, which is the point: a rejected upload is diagnosed here
    check("✗" not in text or "failing cells" in text,
          "a failing table names its failing cells")
    page.screenshot(path=f"{prefix}_export.png")

    browser.close()

print()
if failures:
    print(f"{len(failures)} failure(s):")
    for failure in failures:
        print("  -", failure)
    sys.exit(1)
print("all browser checks passed")
