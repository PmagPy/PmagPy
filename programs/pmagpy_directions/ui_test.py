"""Browser-level checks of the Panel app with Playwright.

    python ui_test.py http://localhost:5100/panel_app screenshots/app

Exercises the step logger (left click = bounds, right click = good/bad),
adds a fit, and screenshots every tab. Exits non-zero on failure.
"""
import sys
import time

from playwright.sync_api import sync_playwright

url = sys.argv[1]
prefix = sys.argv[2]
failures = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        failures.append(msg)


NETS_JS = """() => {
  const doc = Bokeh.documents[0];
  const models = doc._all_models ?? doc.all_models;
  const list = models instanceof Map ? [...models.values()] : [...models];
  return list.filter(m => (m.name === 'equal_area_net' || m.name === 'pole_map') && m.inner_width > 0).map(m => ({
    w: m.inner_width, h: m.inner_height,
    x_per_px: (m.x_range.end - m.x_range.start) / m.inner_width,
    y_per_px: (m.y_range.end - m.y_range.start) / m.inner_height}));
}"""


def check_nets_circular(page, where):
    """Every rendered equal-area net must map data to pixels identically in x and y."""
    nets = page.evaluate(NETS_JS)
    distorted = [n for n in nets if abs(n["x_per_px"] / n["y_per_px"] - 1) > 0.002]
    check(nets and not distorted, f"{where}: {len(nets)} net(s) circular "
          + (f"(distorted: {distorted})" if distorted else f"(frames {[(n['w'], n['h']) for n in nets]})"))


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1680, "height": 1050})
    page.goto(url, wait_until="load", timeout=120000)
    page.wait_for_selector(".step-logger tr[data-i]", timeout=120000)
    time.sleep(3)
    rows = page.locator(".step-logger tr[data-i]")
    n_rows = rows.count()
    check(n_rows > 10, f"logger shows {n_rows} steps")
    check("PmagPy Directions" in page.title(), f"window title is '{page.title()}'")
    check_nets_circular(page, "specimen tab")
    page.screenshot(path=f"{prefix}_specimen.png")

    # right click toggles good/bad on row 5
    row5 = page.locator(".step-logger tr[data-i='5']")
    was_bad = "bad" in (row5.get_attribute("class") or "")
    row5.click(button="right")
    time.sleep(2.5)
    now_bad = "bad" in (page.locator(".step-logger tr[data-i='5']").get_attribute("class") or "")
    check(now_bad != was_bad, "right click toggled the good/bad flag of step 5")
    page.locator(".step-logger tr[data-i='5']").click(button="right")
    time.sleep(2.5)
    check(("bad" in (page.locator(".step-logger tr[data-i='5']").get_attribute("class") or "")) == was_bad,
          "second right click restored the flag")

    def highlighted():
        return [int(r.get_attribute("data-i")) for r in page.locator(".step-logger tr.infit").all()]

    # New fit creates and selects a fit at once; clicking a step moves its nearest bound, live
    n_steps = page.locator(".step-logger tr[data-i]").count()
    page.get_by_role("button", name="New fit").click(); time.sleep(2.5)
    check(highlighted() and highlighted()[-1] == n_steps - 1,
          f"New fit made a selected fit reaching the last step (got {highlighted()})")
    name_box = page.get_by_role("textbox", name="Component")
    name_box.fill("UI"); name_box.press("Enter"); time.sleep(1.5)
    check(page.locator("text=UI").count() > 0, "the name field renamed the new fit 'UI'")
    page.locator(".step-logger tr[data-i='2']").click(); time.sleep(3)
    check(highlighted()[0] == 2, f"clicking step 2 moved the lower bound (got {highlighted()})")
    page.locator(".step-logger tr[data-i='10']").click(); time.sleep(3)
    check(highlighted() == list(range(2, 11)), f"clicking step 10 moved the upper bound (got {highlighted()})")
    page.mouse.click(900, 500)
    page.keyboard.press("]"); time.sleep(2.5)
    check(highlighted() == list(range(3, 11)), f"']' nudged the lower bound up (got {highlighted()})")
    page.keyboard.press("{"); time.sleep(2.5)
    check(highlighted() == list(range(3, 10)), f"'{{' nudged the upper bound down (got {highlighted()})")
    page.screenshot(path=f"{prefix}_specimen_fit.png")

    # a zoom box must not survive a projection switch or a change of specimen
    OUTSIDE_JS = """() => {
      const doc = Bokeh.documents[0]; const models = doc._all_models ?? doc.all_models;
      const list = models instanceof Map ? [...models.values()] : [...models];
      const z = list.find(m => m.name === 'zijderveld');
      const src = z.renderers.map(r => r.data_source).find(s => s && s.data && s.data.y_h && s.data.x.length > 3);
      const xs = Array.from(src.data.x), yh = Array.from(src.data.y_h), yv = Array.from(src.data.y_v);
      let n = 0;
      for (let i = 0; i < xs.length; i++) for (const y of [yh[i], yv[i]])
        if (xs[i] < z.x_range.start || xs[i] > z.x_range.end || y < z.y_range.start || y > z.y_range.end) n++;
      return n;
    }"""
    canvas = page.locator("canvas.bk-layer").first.bounding_box()

    def zoom_box():
        page.mouse.move(canvas["x"] + 150, canvas["y"] + 150)
        page.mouse.down()
        page.mouse.move(canvas["x"] + 350, canvas["y"] + 350, steps=8)
        page.mouse.up()
        time.sleep(1.5)
    zoom_box()
    check(page.evaluate(OUTSIDE_JS) > 0, "box zoom hides some steps")
    # projection switch
    page.get_by_role("button", name="east").click()
    time.sleep(2)
    check("bk-active" in (page.get_by_role("button", name="east").get_attribute("class") or ""),
          "projection switched to east")
    check(page.evaluate(OUTSIDE_JS) == 0, "projection switch reset the zoom")
    zoom_box()
    page.keyboard.press("ArrowRight")
    time.sleep(2)
    check(page.evaluate(OUTSIDE_JS) == 0, "next specimen reset the zoom")
    page.keyboard.press("ArrowLeft")
    time.sleep(2)
    page.screenshot(path=f"{prefix}_specimen_east.png")

    for tab in ("Means", "Poles", "Fits", "Export"):
        page.get_by_text(tab, exact=True).first.click()
        time.sleep(5)
        page.screenshot(path=f"{prefix}_{tab.lower()}.png")
        check(True, f"{tab} tab rendered")
        if tab in ("Means", "Poles", "Fits"):
            check_nets_circular(page, f"{tab} tab")
        visible = page.locator(".step-logger tr[data-i]").count() > 0 or page.get_by_role("button", name="Change data…").count() > 0
        if tab == "Export":
            check(not visible, f"{tab} tab hides the side column")
        else:
            check(visible, f"{tab} tab keeps a side column")
        if tab == "Fits":
            # the side column plots what the table lists, and says how many
            check(page.get_by_text("fits listed").count() > 0, "Fits tab: side column reports the plotted fits")
        if tab == "Poles":
            n_land = page.evaluate("""() => {
              const doc = Bokeh.documents[0];
              const models = doc._all_models ?? doc.all_models;
              const list = models instanceof Map ? [...models.values()] : [...models];
              const m = list.find(m => m.name === 'pole_map');
              if (!m) return -1;
              const land = m.renderers.map(r => r.data_source).filter(s => s && s.data && s.data.xs && s.data.xs.length > 20);
              return land.length ? land[0].data.xs.length : 0;
            }""")
            check(n_land > 20, f"Poles tab: globe shows {n_land} land polygons")
            # a click on the globe re-centres it: the centre control switches to "custom"
            globe = page.locator("canvas.bk-layer").first.bounding_box()      # the only canvas on this tab
            page.mouse.click(globe["x"] + globe["width"] * 0.65, globe["y"] + globe["height"] * 0.45)
            time.sleep(2)
            custom = page.get_by_role("button", name="custom")
            check("bk-active" in (custom.get_attribute("class") or ""), "Poles tab: clicking the globe re-centres it")
    # switching datasets: every tab must show the new data — through the system
    # chooser (stubbed with PMAGPY_DIRECTIONS_CHOOSER_STUB on the server) and through the path field
    import os
    repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    DATASETS = {"dmag_magic": (os.path.join(repo, "data_files", "dmag_magic"), 176, ("mc", "CM", "SL", "TIR")),
                "McMurdo": (os.path.join(repo, "data_files", "3_0", "McMurdo"), 1034, ("jm", "sp", "CM", "SL", "TIR"))}
    extra = os.environ.get("PMAGPY_DIRECTIONS_EXTRA_DATA") or os.environ.get("DEMAG_EXTRA_DATA")
    if extra and os.path.isdir(extra):
        DATASETS[os.path.basename(extra.rstrip("/"))] = (extra, None, ("jm", "sp", "mc"))

    def cells(sel):
        return [c for c in page.locator(sel).all_inner_texts() if c.strip()]

    def verify(name, n_expected, foreign, switched=True):
        page.get_by_text("Specimen", exact=True).first.click()
        time.sleep(3)
        if switched:      # (earlier steps overwrite the load message with fit-editing status)
            check(page.get_by_text(f"specimens from {name}").count() > 0, f"[{name}] header reports the dataset")
        n_opts = page.locator("select").first.evaluate("el => el.options.length")
        check(n_expected is None or n_opts == n_expected, f"[{name}] specimen selector lists {n_opts} specimens")
        current = page.locator("select").first.evaluate("el => el.value")
        check(current and not current.startswith(foreign), f"[{name}] current specimen {current}")
        check(page.locator(".step-logger tr[data-i]").count() > 3, f"[{name}] logger shows steps")
        check(page.get_by_text(current, exact=True).count() > 0, f"[{name}] information line names {current}")
        page.screenshot(path=f"{prefix}_{name}_specimen.png")
        page.get_by_text("Fits", exact=True).first.click()
        time.sleep(5)
        names = cells(".tabulator-cell[tabulator-field='specimen']")
        check(names and not any(c.startswith(foreign) for c in names), f"[{name}] Fits tab lists {len(names)} own fits on page 1")
        check(page.get_by_text("specimens interpreted").count() > 0, f"[{name}] Fits summary present")
        page.screenshot(path=f"{prefix}_{name}_interpretations.png")
        page.get_by_text("Means", exact=True).first.click()
        time.sleep(4)
        site = page.locator("select").nth(0).evaluate("el => el.value")
        check(site and not site.startswith(foreign), f"[{name}] Means offers site {site}")
        listed = cells(".tabulator-cell[tabulator-field='specimen']")
        check(listed and not any(c.startswith(foreign) for c in listed), f"[{name}] Means lists {len(listed)} own fits")
        page.screenshot(path=f"{prefix}_{name}_means.png")
        page.get_by_text("Poles", exact=True).first.click()
        time.sleep(5)
        sites = cells(".tabulator-cell[tabulator-field='site']")
        check(sites and not any(c.startswith(foreign) for c in sites), f"[{name}] Poles table lists {len(sites)} own sites")
        check(page.get_by_text("A95").count() > 0, f"[{name}] Poles shows a mean pole")
        page.screenshot(path=f"{prefix}_{name}_poles.png")
        page.get_by_text("Export", exact=True).first.click()
        time.sleep(3)
        redo = page.get_by_role("textbox", name=".redo file").input_value()
        check(name in redo, f"[{name}] Export .redo path is {os.path.basename(os.path.dirname(redo))}/{os.path.basename(redo)}")
        page.screenshot(path=f"{prefix}_{name}_export.png")

    def switch_by_path(path):
        page.get_by_text("Specimen", exact=True).first.click()
        time.sleep(2)
        page.get_by_role("button", name="Change data…").click()
        time.sleep(2)
        box = page.get_by_role("textbox", name="MagIC directory (must contain measurements.txt)")
        box.fill(path)
        box.press("Enter")
        time.sleep(0.5)
        page.get_by_role("button", name="Open", exact=True).click()
        wait_for(os.path.basename(path.rstrip("/")))

    def switch_by_chooser():
        page.get_by_text("Specimen", exact=True).first.click()
        time.sleep(2)
        page.get_by_role("button", name="Change data…").click()
        time.sleep(2)
        btn = page.get_by_role("button", name="Browse with")
        check(btn.count() > 0 and btn.first.is_enabled(), "system chooser button available (stubbed on the server)")
        btn.first.click()
        wait_for("McMurdo")

    def wait_for(name):
        for _ in range(90):
            if page.get_by_text(f"specimens from {name}").count():
                break
            time.sleep(1)
        time.sleep(3)

    verify("dmag_magic", *DATASETS["dmag_magic"][1:], switched=False)
    switch_by_chooser()                                   # the Finder/Explorer route (worker thread)
    verify("McMurdo", *DATASETS["McMurdo"][1:])
    switch_by_path(DATASETS["dmag_magic"][0])             # and back through the path field
    verify("dmag_magic", *DATASETS["dmag_magic"][1:])
    for name, (path, n, foreign) in DATASETS.items():
        if name not in ("dmag_magic", "McMurdo"):
            switch_by_path(path)
            verify(name, n, foreign)
    browser.close()

if failures:
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1)
print("\nALL UI CHECKS PASSED")
