"""
Browser-level checks of PmagPy Intensity with Playwright.

    python ui_test.py http://localhost:5101/pmagpy_intensity screenshots/app

What it catches that the unit tests cannot: a template that fails to build, an
equal-area net that Bokeh has squeezed into an ellipse, an Arai plot whose
coordinate scaling drifts as the window is resized, a tab that renders empty,
and the long BiCEP run blocking the interface.

It also goes once round the analysis as a tester would -- a flag inside a fit
and one on its first step, Auto, a criteria switch, the correction switches --
and exports, then checks that specimens.txt, sites.txt and measurements.txt
hold what the panes showed, and that un-flagging after an export reaches the
file. It reads the exported tables from the folder the export pane names.

Exits non-zero on failure. Running it flags steps and exports: serve a copy of
the study, or set PMAGPY_APPS_OUTPUT (or PMAGPY_INTENSITY_OUTPUT) so that the
application works on a disposable working copy of it.
"""
import json
import os
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # programs/
from pmagpy_panel.ui_checks import drag_plot_handle  # noqa: E402

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


#: a Tabulator only keeps the visible rows in the DOM; the whole column lives
#: on the model's data source
TABLE_DATA_JS = """(column) => {
  const doc = Bokeh.documents[0];
  const models = doc._all_models ?? doc.all_models;
  const list = models instanceof Map ? [...models.values()] : [...models];
  for (const m of list) {
    const data = m.source && m.source.data;
    if (data && data[column]) return [...data[column]];
  }
  return [];
}"""

#: click the table row whose text contains `needle` (a MagIC column name is
#: unique to one statistic, where a label like "n" is not)
CLICK_ROW_JS = """(needle) => {
  const rows = [];
  const walk = (root) => root.querySelectorAll('*').forEach(el => {
    if (el.shadowRoot) walk(el.shadowRoot);
    if (el.classList && el.classList.contains('tabulator-row')
        && !el.classList.contains('tabulator-group')) rows.push(el);
  });
  walk(document);
  const target = rows.find(r => r.textContent.includes(needle));
  if (!target) return false;
  target.click();
  return true;
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



# --- the analysis round trip: helpers ---------------------------------------
#: every text node of the page, shadow roots included (TEXT_JS keeps only leaf elements, which
#: misses text that shares its element with markup, such as a button's label or a note with <b>)
ALL_TEXT_JS = """() => {
  const out = [];
  const walk = (root) => {
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
    let node;
    while ((node = tw.nextNode())) {
      if (node.nodeType === 3) {
        const parent = node.parentNode;
        if (parent && ['STYLE', 'SCRIPT', 'TEMPLATE'].includes(parent.nodeName)) continue;
        const text = node.textContent.trim();
        if (text) out.push(text);
      } else if (node.shadowRoot) walk(node.shadowRoot);
    }
  };
  walk(document);
  return out.join('\\n');
}"""


def wait_for_text(page, pattern, timeout=120):
    """Poll the page's text for `pattern` (a regular expression); the match, or None."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        found = re.search(pattern, page.evaluate(ALL_TEXT_JS))
        if found:
            return found
        time.sleep(0.5)
    return None


def open_tab(page, label, marker, timeout=90):
    """Select a tab and wait until `marker` (its own control) is in the page."""
    page.evaluate(CLICK_TAB_JS, label)
    wait_for_text(page, re.escape(marker), timeout)
    time.sleep(1.5)


def click_button(page, label, timeout=60):
    deadline = time.time() + timeout
    while not page.evaluate(CLICK_BUTTON_JS, label):
        if time.time() > deadline:
            return False
        time.sleep(0.5)
    return True


def selected(page, label):
    """The text of the option a Select shows ("" when it shows none)."""
    return page.get_by_label(label, exact=True).first.evaluate(
        "s => s.selectedIndex >= 0 ? s.options[s.selectedIndex].text : ''")


def bounds_shown(page):
    return selected(page, "from"), selected(page, "to")


def wait_for_bounds(page, condition, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        shown = bounds_shown(page)
        if condition(shown):
            return shown
        time.sleep(0.5)
    return bounds_shown(page)


def step_table(page):
    """The step table's rows, from its data source (only the visible rows are in the DOM)."""
    for columns in page.evaluate(TABLES_JS, "_sequence"):
        n = len(columns["_sequence"])
        return [{k: columns[k][i] for k in columns} for i in range(n)]
    return []


def click_step(page, index, field="label", timeout=60):
    """Click a cell of the step table's row `index`, scrolling the table to it first."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        page.evaluate(SCROLL_STEPS_JS, index)
        time.sleep(0.6)
        rows = page.locator(".tabulator-row").filter(has=page.locator("[tabulator-field='kind']"))
        for k in range(rows.count()):
            cell = rows.nth(k).locator("[tabulator-field='_index']")
            if cell.count() and cell.first.text_content().strip() == str(index):
                rows.nth(k).locator(f"[tabulator-field='{field}']").first.click()
                time.sleep(1.5)
                return True
        time.sleep(1)
    return False


def choose(page, label, option):
    page.get_by_label(label, exact=True).first.select_option(label=option)
    time.sleep(2)


def export_in_place(page):
    """Write MagIC tables (two clicks when it replaces the study's own); the folder written to, or None."""
    open_tab(page, "Export", "Merge policy")
    click_button(page, "Write MagIC tables")
    confirm = wait_for_text(page, r"Confirm: replace the tables", 30) is not None
    if confirm:
        click_button(page, "Confirm: replace the tables")
    written = wait_for_text(page, r"wrote \d+ files to (\S+)", 300)
    return confirm, (written.group(1) if written else None)


def read_table(directory, name):
    import pandas as pd
    return pd.read_csv(os.path.join(directory, name), sep="\t", header=1, dtype=str,
                       keep_default_na=False)


def autosave_flags(directory, specimen, timeout=30):
    """The step flags the autosave holds for `specimen` (its meas_pos), once it has been written."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with open(os.path.join(directory, "pmagpy_intensity_autosave.json"), encoding="utf-8") as fh:
                flags = [s["meas_pos"] for s in json.load(fh).get("bad_steps", []) if s["specimen"] == specimen]
            if flags:
                return flags
        except (OSError, ValueError, KeyError):
            pass
        time.sleep(1)
    return []


#: every Tabulator data source that has `column`, as {column: [values]}
TABLES_JS = """(column) => {
  const doc = Bokeh.documents[0];
  const models = doc._all_models ?? doc.all_models;
  const list = models instanceof Map ? [...models.values()] : [...models];
  const out = [];
  for (const m of list) {
    const data = m.source && m.source.data;
    if (data && data[column]) { const o = {}; for (const k of Object.keys(data)) o[k] = [...data[k]]; out.push(o); }
  }
  return out;
}"""

#: scroll the step table so that row `index` is rendered
SCROLL_STEPS_JS = """(index) => {
  const found = [];
  const walk = (root) => root.querySelectorAll('*').forEach(el => {
    if (el.shadowRoot) walk(el.shadowRoot);
    if (el.classList && el.classList.contains('tabulator-tableholder')) found.push(el);
  });
  walk(document);
  for (const h of found) if (h.querySelector("[tabulator-field='kind']")) h.scrollTop = Math.max(0, index * 28 - 80);
}"""


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": 1680, "height": 1050})
    page.goto(url, wait_until="load", timeout=180000)
    page.wait_for_function("() => window.Bokeh && Bokeh.documents.length > 0", timeout=180000)
    # the study is read before the page is built: wait for the tabs and the Arai plot, not a fixed time
    deadline = time.time() + 240
    while time.time() < deadline and not (len(page.evaluate(TABS_JS)) == 7 and arai_scaling(page)):
        time.sleep(1)
    time.sleep(3)

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

    # ---- the handle under the plots ------------------------------------
    # only a guide moves during the drag; on release the plots take the new
    # size at once, the handle lands where the guide was, and the Arai frame
    # stays square at its new size
    frame_before = arai_scaling(page)["w"]
    drag = drag_plot_handle(page, 60)
    check(drag is not None, "the plots have a resize handle under them")
    if drag:
        check(drag["moved"] <= 1, f"the plots stand still during the drag (changed {drag['moved']:.0f} px)")
        check(drag["height_after"] > drag["height_before"] + 40,
              f"dragging the handle down enlarges the plots ({drag['height_before']:.0f} -> "
              f"{drag['height_after']:.0f} px)")
        check(abs(drag["final"] - drag["dropped"]) <= 3 and drag["sizes"] == 1,
              f"the plots take the new size in one step, with the handle where the guide was let go "
              f"({drag['sizes']} size(s) shown, {abs(drag['final'] - drag['dropped']):.1f} px off)")
        check(drag["misfit"] <= 0.05,
              f"every figure is drawn to its own size (canvas off by {100 * drag['misfit']:.1f}%)")
        scaling = arai_scaling(page)
        check(scaling["w"] > frame_before and abs(scaling["w"] - scaling["h"]) <= 1,
              f"the Arai frame grew and stayed square ({scaling['w']:.0f} x {scaling['h']:.0f})")
        # dragging far past what fits beside the Arai plot must not wrap the
        # companions below it: the guide stops where the plots fill the pane
        drag = drag_plot_handle(page, 400)
        check(abs(drag["final"] - drag["dropped"]) <= 5,
              f"an oversized drag stops at the pane's width, without a jump "
              f"(landed {abs(drag['final'] - drag['dropped']):.1f} px from the guide)")
        # (the companions grow in whole tiles, so a long drag lands a few pixels from the guide)
        drag = drag_plot_handle(page, -250)
        check(drag["height_after"] < drag["height_before"] and abs(drag["final"] - drag["dropped"]) <= 5
              and drag["sizes"] == 1,
              f"dragging up shrinks the plots in one step "
              f"(landed {abs(drag['final'] - drag['dropped']):.1f} px from the guide)")
        check(drag["misfit"] <= 0.05, f"... and every figure is drawn to its own size "
                                      f"(canvas off by {100 * drag['misfit']:.1f}%)")
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
            # the dot plot joins the page once the means are computed (it is left out while
            # there is nothing to plot), so wait for it rather than for a fixed time
            deadline = time.time() + 90
            groups = frames(page, ["groups"])
            while time.time() < deadline and not (groups and groups[0]["w"] > 100):
                time.sleep(1)
                groups = frames(page, ["groups"])
            check(bool(groups) and groups[0]["w"] > 100 and groups[0]["h"] > 100,
                  f"the group dot plot rendered (got {groups})")
        page.screenshot(path=f"{prefix}_{label.split()[0].lower()}.png")

    # ---- show code: the family's rule that a view says what it ran ------
    # back to Specimen: the loop above finished on Export, and a lazy tab's
    # widgets are not in the document while another tab is showing
    page.evaluate(CLICK_TAB_JS, "Specimen")
    time.sleep(3)
    # what the pane *says* is asserted in test_app.py's TestShowCode, which also
    # runs the emitted script in a subprocess and compares its answer with the
    # panel's -- stronger than grepping a Markdown block out of the DOM. Here we
    # only want to know the control reached the page.
    check(page.evaluate(CLICK_BUTTON_JS, "Show code"), "the specimen view offers Show code")
    time.sleep(1)

    # ---- criteria: every statistic is a row, and a row explains itself ----
    page.evaluate(CLICK_TAB_JS, "Criteria & statistics")
    time.sleep(4)
    # the table virtualises its rows, so only the visible ones are in the DOM:
    # the statistics have to be read from the model rather than from the page
    listed = page.evaluate(TABLE_DATA_JS, "statistic")
    for label in ("FRAC", "DRAT", "Ziggie", "dt*", "IZZI_MD"):
        check(label in listed, f"the statistics table has a row for {label}")
    check(len(listed) > 40, f"the whole SPD set is there ({len(listed)} rows)")
    check(page.evaluate(CLICK_ROW_JS, "int_frac"), "a statistic can be selected")
    time.sleep(2)
    detail = page.evaluate(TEXT_JS)
    check("doi.org" in page.evaluate(HTML_JS), "the selected statistic cites its source")
    check("NRM fraction" in detail, "the selected statistic gives its definition")
    check("-999" not in detail, "the statistics panel shows no sentinel values")

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


    # ---- the analysis round trip: what is shown is what is written --------
    open_tab(page, "Specimen", "Flag the selected step bad/good")
    status = page.evaluate(ALL_TEXT_JS)
    header = next((line for line in status.splitlines() if "specimens from" in line), "")
    check(bool(header), f"the header names the study ({header[:80]!r})")
    # a working copy's folder carries a fingerprint (Megiddo-1a2b3c4d); the study is named, not it
    check(not re.search(r"specimens from \S+-[0-9a-f]{8}\b", header),
          "the header names the study, not its working copy's folder")
    first = selected(page, "Specimen")
    start = bounds_shown(page)
    # selecting a step to flag it leaves the fit alone
    rows = step_table(page)
    index_of = {label: i for i, label in enumerate(o for o in page.get_by_label("from", exact=True).first
                                                    .evaluate("s => [...s.options].map(o => o.text)"))}
    lo, hi = index_of.get(start[0], 0), index_of.get(start[1], 0)
    interior = [i for i, r in enumerate(rows) if lo < r["_arai"] < hi and r["kind"] == "in field"]
    check(bool(interior) and click_step(page, interior[0]) and bounds_shown(page) == start,
          f"selecting a step in the table does not move a bound ({start})")
    click_button(page, "Flag the selected step bad/good")
    time.sleep(3)
    check(bounds_shown(page) == start, f"flagging a step inside the fit keeps its bounds ({bounds_shown(page)})")
    check(step_table(page)[interior[0]]["quality"] == "⨯", "the flagged step is marked in the table")

    # a flag on the fit's first step sets the fit aside, and flagging it good restores it
    names = page.get_by_label("Specimen", exact=True).first.evaluate("s => [...s.options].map(o => o.text)")
    second = names[1]
    choose(page, "Specimen", second)
    before = wait_for_bounds(page, lambda b: all(b))
    rows = step_table(page)
    index_of = {label: i for i, label in enumerate(page.get_by_label("from", exact=True).first
                                                   .evaluate("s => [...s.options].map(o => o.text)"))}
    edge = [i for i, r in enumerate(rows) if r["_arai"] == index_of.get(before[0]) and r["kind"] == "zero field"]
    if edge and click_step(page, edge[0]):
        click_button(page, "Flag the selected step bad/good")
        check(wait_for_text(page, r"so it was set aside", 30) is not None,
              "flagging the fit's first step sets the fit aside, and says so")
        click_step(page, edge[0])
        click_button(page, "Flag the selected step bad/good")
        again = wait_for_bounds(page, lambda b: b == before)
        check(again == before, f"flagging it good again restores the fit ({before} -> {again})")
    else:
        check(False, f"the zero-field step at the lower bound of {second} can be selected")

    # Auto on a specimen with no interpretation shows its bounds in both selectors
    open_tab(page, "Interpretations", "Auto-interpret all")
    interpreted = set(page.evaluate(TABLES_JS, "verdict")[0]["specimen"])
    fresh = next((n for n in names if n not in interpreted), None)
    open_tab(page, "Specimen", "Flag the selected step bad/good")
    if fresh:
        choose(page, "Specimen", fresh)
        click_button(page, "Auto")
        shown = wait_for_bounds(page, lambda b: all(b))
        check(all(shown), f"after Auto on {fresh}, both bounds are shown ({shown})")
        click_button(page, "Clear")
        time.sleep(2)
    choose(page, "Specimen", first)

    # switching the criteria set, and back
    open_tab(page, "Interpretations", "Auto-interpret all")
    summary = wait_for_text(page, r"(\d+) accepted under ([^\n]+)")
    accepted, criteria = summary.group(1), summary.group(2).strip()
    open_tab(page, "Criteria & statistics", "Search statistics")
    choose(page, "Criteria set", "CCRIT")
    open_tab(page, "Interpretations", "Auto-interpret all")
    check(wait_for_text(page, r"\d+ accepted under CCRIT") is not None, "switching the criteria set to CCRIT re-judges")
    open_tab(page, "Criteria & statistics", "Search statistics")
    choose(page, "Criteria set", criteria)
    open_tab(page, "Interpretations", "Auto-interpret all")
    back = wait_for_text(page, r"(\d+) accepted under " + re.escape(criteria))
    check(back is not None and back.group(1) == accepted,
          f"switching back to {criteria} gives the same verdicts ({accepted} accepted)")

    # the correction switches show the current specimen's own choice (a published DA-AC reads "always")
    open_tab(page, "Specimen", "Flag the selected step bad/good")
    open_tab(page, "Corrections", "anisotropy alteration limit")
    if wait_for_text(page, r"anisotropy: applied", 20):
        check(selected(page, "anisotropy") == "always",
              f"the anisotropy switch shows the specimen's own choice ({selected(page, 'anisotropy')!r})")

    # export into the study: two clicks, and the files say what the panes say
    open_tab(page, "Specimen", "Flag the selected step bad/good")
    shown_bounds = bounds_shown(page)
    b_shown = wait_for_text(page, r"([\d.]+) ± [\d.]+ µT")
    confirm, output_dir = export_in_place(page)
    check(confirm, "an export into the study asks for a second click")
    check(output_dir is not None, f"the export writes the tables ({output_dir})")
    if output_dir:
        specimens = read_table(output_dir, "specimens.txt")
        row = specimens[(specimens["specimen"] == first) & (specimens["int_abs"] != "")].iloc[-1]
        kelvin = lambda label: 273.0 if label == "NRM" else float(label.rstrip("°C")) + 273.0
        check(abs(float(row["meas_step_min"]) - kelvin(shown_bounds[0])) < 0.6
              and abs(float(row["meas_step_max"]) - kelvin(shown_bounds[1])) < 0.6
              and abs(float(row["int_abs"]) * 1e6 - float(b_shown.group(1))) < 0.051,
              f"specimens.txt holds the bounds and B_anc shown for {first} ({shown_bounds}, {b_shown.group(1)} µT)")
        flags = autosave_flags(output_dir, first)
        measurements = read_table(output_dir, "measurements.txt")
        check(bool(flags) and all(measurements["quality"].iloc[p] == "b" for p in flags),
              "the flagged step is 'b' in measurements.txt")
        # group results as shown vs sites.txt
        open_tab(page, "Group results", "accepted specimens only")
        wait_for_text(page, r"\d+ specimens averaged")
        sites = read_table(output_dir, "sites.txt")
        sites = sites[sites.get("int_abs", "") != ""].drop_duplicates("site", keep="last").set_index("site")
        # the tab redraws once shown: poll until the means shown are the current ones
        deadline, g, mismatched = time.time() + 60, {"site": []}, ["(no table)"]
        while time.time() < deadline and mismatched:
            groups = page.evaluate(TABLES_JS, "N samples")
            if groups:
                g = groups[0]
                mismatched = [(s, b, round(float(sites.loc[s, "int_abs"]) * 1e6, 3) if s in sites.index else None)
                              for s, b in zip(g["site"], g["B (µT)"])
                              if s not in sites.index or abs(float(sites.loc[s, "int_abs"]) * 1e6 - b) > 0.006]
            time.sleep(1)
        check(not mismatched, f"sites.txt holds the {len(g['site'])} site means shown ({mismatched[:3]})")
        # un-flagging after the export reaches the file on the next export
        open_tab(page, "Specimen", "Flag the selected step bad/good")
        click_step(page, interior[0])
        click_button(page, "Flag the selected step bad/good")
        time.sleep(3)
        export_in_place(page)
        measurements = read_table(output_dir, "measurements.txt")
        check(bool(flags) and all(measurements["quality"].iloc[p] == "g" for p in flags),
              "flagging the step good after an export reaches measurements.txt")
    page.screenshot(path=f"{prefix}_round_trip.png")

    browser.close()

print()
if failures:
    print(f"{len(failures)} failure(s):")
    for failure in failures:
        print("  -", failure)
    sys.exit(1)
print("all browser checks passed")
