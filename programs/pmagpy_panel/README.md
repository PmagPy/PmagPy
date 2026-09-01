# pmagpy_panel — the shared toolkit for the PmagPy Panel applications

Two of the wxPython GUIs are being rewritten as Panel applications over a
MagIC 3-native core:

| legacy GUI | successor | core | branch |
|---|---|---|---|
| Demag GUI | `programs/pmagpy_directions` | `pmagpy/demag.py` | `demag_gui_playground` |
| Thellier GUI | `programs/pmagpy_intensity` | `pmagpy/paleointensity.py`, `pmagpy/pint_stats.py`, `pmagpy/bicep.py`, `pmagpy/tdt.py` | `pmagpy_intensity` |

They are meant to be **one application in two subjects**, not two applications
that resemble each other: an analyst who has used one should already know how
the other behaves, and a fix to a shared behaviour should reach both. This
package is where that shared part lives, and this file is the contract between
the two efforts. If you are working on either application — or pointing an
agent at one — start here.

## Where code goes

| layer | where | rule |
|---|---|---|
| science | `pmagpy/demag.py`, and the paleointensity core beside it | no UI import at all; usable from a notebook or a script |
| MagIC tables | `pmagpy/magic_project.py` — on the `pmagpy_intensity` branch, not yet merged here | reading, merging and writing contributions: `merge_results`, `carry_metadata`, `trim_to_model`, `validate_directory`, taken out of `demag.py`. Shared by both cores |
| presentation | `programs/pmagpy_panel/` (**here**) | how a PmagPy Panel application looks and behaves |
| the application | `programs/<app>/` | only what is specific to that subject: its panes, its plots, its session |

Both `programs/` packages are excluded from the pip package (`setup.py` excludes
`programs.*`), so nothing here may be imported by `pmagpy`. The dependency
arrows point one way: application → toolkit → `pmagpy` → nothing of ours.

When you find yourself about to copy something out of `pmagpy_directions`,
that is the signal to move it here instead. Equally: if a thing knows what a
demagnetization step or a Thellier step *is*, it does not belong here.

## What is in the toolkit

* **`theme.py`** — the palette, the CSS, Bokeh figure styling, and
  `ComponentColors`, which keeps a component's colour the same everywhere it
  appears. Also `kpi()`, `SECTION_STYLE`, `lighten()`, `style_figure()`,
  `asset_data_uri()`.
  **Each application has its own accent**: `theme.for_app(app_id)` returns a
  `Theme` whose tabs, checkboxes, button groups, table rows and `raw_css` are
  all derived from one colour — navy for Directions, plum for Intensity, listed
  together in `ACCENTS` so a third application cannot pick one already in use.
  The module-level `TABS_CSS`, `CHECKBOX_CSS`, `TABLE_ROW_CSS`,
  `BUTTON_GROUP_CSS` and `RAW_CSS` are the default (navy) theme's, so anything
  that has not asked for its own keeps what it had. The accent is **chrome
  only**: a data mark's colour says what the data is, never which application
  drew it.
* **`widgets.py`** — the custom `JSComponent`s: `Splitter` (the vertical
  boundary between the side column and the main pane, which moves *both*),
  `HeightSplitter` (resizes the plots), `Hotkeys` (forwards key presses).
* **`nets.py`** — equal-area primitives. `net_figure()` builds a square,
  toolbar-less figure and `keep_circular()` guards it; `declutter_labels()`
  thins labels where symbols pile up.
* **`chooser.py`** — the widgets around `datasets.py`: the dataset block for the
  side column and the "open a different one" dialog (system folder chooser,
  recent list, path field, in-page browser). `modal(*extra)` takes whatever the
  application wants to add underneath — PmagPy Intensity appends a ThellierTool
  importer. It is given a session that answers `directory`, `output_dir`,
  `status` and `load(path)`, and a `count` callable, so it knows nothing about
  either science; `test_chooser.py` drives it with a stub session and asserts
  exactly that.
* **`datasets.py`** — choosing, remembering and validating a MagIC directory:
  `env()`, `looks_like_magic_dir()`, `default_output_dir()`, the recent list,
  and the native folder chooser (macOS/Linux/Windows, with a stub hook for
  tests).
* **`launch.py`** — the one-command launcher: stops a previous server, serves
  in dev mode, waits for the app to answer before opening a browser.

Nothing here holds global state. An application passes its own identity —
`AppInfo(name, app_id, env_prefixes)` — to the helpers that need it, so both
applications can be imported into one process, which the tests do.

## Starting the second application

```
programs/pmagpy_intensity/
├── __init__.py            APP_NAME
├── pmagpy_intensity.py    the served file (see below)
├── launch.py              names the app; the work is in pmagpy_panel.launch
├── conftest.py            puts programs/ and the repo root on sys.path
├── app.py, views.py, plots.py, session.py
└── assets/                its own logo and favicon
```

The served file and `conftest.py` both put `programs/` on `sys.path` so that
the app and the toolkit import as top-level packages — never through
`programs`, whose `__init__` pins a GUI matplotlib backend for the wx programs:

```python
sys.path.insert(0, os.path.dirname(_HERE))                    # programs/
sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))   # repo root, for pmagpy
```

Then `from pmagpy_panel.theme import ...` works from either application. The
launcher is a four-line wrapper:

```python
from pmagpy_panel import launch
sys.exit(launch.main(APP, env_prefix="PMAGPY_INTENSITY_", default_port=5101))
```

Pick a different default port from Directions' 5100 so the two can run at once.

## Conventions worth keeping identical

These are what make the two feel like one program.

* **Symbols on a net.** Circles are measured directions, filled on the lower
  hemisphere and open on the upper; a **square** is a mean; a **triangle** is a
  direction that was worked out rather than measured (the best-fit vector of a
  plane). Derived symbols take the dark edge (`#2b2b2b`); the mean is drawn on
  top of what it averages.
* **Colour carries identity, not category.** A component keeps its colour in
  every table, plot and exported figure (`ComponentColors`). The *chrome*
  accent is the exception and the point: it says which application you are in,
  and it is the only colour that differs between the two.
* **Layout.** A side column of controls and context, a drag handle, then the
  main pane; only a tab that plots nothing takes the full width. The main pane
  is inset from the handle so text set flush left does not run into it.
* **Tables.** Use `TABLE_ROW_CSS` on any table whose rows can be hovered or
  selected. Give a table the height of what it holds rather than a fixed
  height, and do not stretch a handful of statistics across the whole pane.
* **Say what a number is.** Columns that hold different quantities belong in
  different tables — a pole to a plane under a `dec`/`inc` heading reads as a
  direction and is not one.

## Gotchas that cost real time here

Each of these was found the hard way in Directions; none is obvious.

* **Panel's `--dev` reload does not push an edited `_esm` string to the
  browser.** Param defaults reload, so a change looks half-applied while the
  old JavaScript keeps running. Restart the server after touching any
  component's JS.
* **Bokeh renders every model into its own shadow root.** A component's host
  element therefore has `parentElement === null` — walk up with
  `el.parentElement || el.parentNode.host`. Sibling lookups
  (`previousElementSibling`) do work. A wrapper lookup written as plain
  `parentElement` fails *silently*. Browser probes need a recursive
  `shadowRoot` walk to find anything.
* **Re-laying out a Bokeh figure costs ~100 ms**, whether the request comes
  from Python (~230 ms end to end) or from JavaScript against the models
  (90–120 ms). Nothing can follow a cursor at frame rate: preview a resize with
  a CSS transform and do the real resize once, on release.
* **Equal-area nets go elliptical** when Bokeh aligns the frames of plots that
  share a layout. Build them with `net_figure()` (which sets
  `frame_align=False` and installs `keep_circular`) and assert circularity in
  the browser suite.
* **Tabulator header filters** only reach Python under `pagination="local"`;
  under `"remote"` they are applied in the browser and `current_view` never
  sees them. Even then Panel updates `filters` with watchers suppressed, so a
  filter typed in the browser arrives silently — poll it while the tab is on
  show.
* **Tabulator turns hovered and selected row text white**, which is unreadable
  on pale row colours. `TABLE_ROW_CSS` fixes both states.
* **Assets belong to an application, not to the toolkit.** `asset_data_uri()`
  takes a full path for exactly this reason.
* **Test the assembly, not only the pieces.** Every piece of the theme was
  covered when the logo path broke; only the browser suite noticed. Build the
  template in a unit test.
* **Bokeh sizes every container to its content and writes the answer in
  pixels.** A `stretch_width` `FlexBox` inside one therefore never re-measures,
  and `flex-wrap` never fires however the window is resized — the pane scrolls
  instead. Size a block of figures for the width you expect to have and give
  the analyst a handle, a size slider or both; do not expect CSS wrapping to
  rescue a layout that does not fit.
* **A figure's chrome is not a constant you can guess.** Bokeh fits the frame
  into whatever the declared outer box leaves after the axes, labels, toolbar
  and legend — so an allowance that is too small *silently squashes the frame*
  rather than failing. `pmagpy_intensity/plots.py` keeps a measured
  `CHROME_W`/`CHROME_H` per figure class for exactly this reason.

## Tests

```bash
pytest pmagpy/test/test_demag.py pmagpy/test/test_demag_geo.py -q   # cores (run in CI)
pytest programs/pmagpy_panel/test_chooser.py -q                     # the toolkit itself
pytest programs/pmagpy_directions/test_app.py -q                    # app (needs panel/bokeh)
# browser suite: serve the app, then
python ui_test.py http://localhost:5100/pmagpy_directions screenshots/app
```

The browser suite is worth writing for the second application too: it is what
catches the things unit tests cannot — circularity, drag behaviour, a template
that fails to build. Note that running it leaves a gitignored
`*_autosave.redo` in the data directory; delete it afterwards so a throwaway
interpretation is not restored on the next load.

## Working on the shared branch

Both efforts land on `demag_gui_playground`, so commits arrive from more than
one stream.

* `git fetch` and `git pull --rebase` before pushing; **never force-push**. A
  rejected push here means someone else's work landed, not that anything went
  wrong.
* Run the suites *after* pulling as well as before pushing. The cores call into
  `pmagpy/pmag.py` (`dolnp`, `domean`, `dobingham`, `doprinc`,
  `separate_directions`, `calculate_best_fit_vectors`, `dia_vgp`,
  `fisher_mean` …), which other streams do edit — a change there will not
  conflict, it will quietly alter results.
* Keep a commit inside one layer where you can. Changing the toolkit affects
  both applications: say so in the message, and check the other application
  still builds.
* If you need something from the other application's package, that is a sign it
  belongs here instead. Move it, with its tests.
