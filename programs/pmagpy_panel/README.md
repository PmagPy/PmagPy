# pmagpy_panel — the shared toolkit for the PmagPy Panel applications

Two of the wxPython GUIs are being rewritten as Panel applications over a
MagIC 3-native core:

| legacy GUI | successor | core | branch |
|---|---|---|---|
| Demag GUI | `programs/pmagpy_directions` | `pmagpy/demag.py` | `demag_gui_playground` |
| Thellier GUI | `programs/pmagpy_intensity` (also called `pmagpy_paleointensity`; the two names are still settling) | to come | `pmagpy_intensity` |

They are meant to be **one application in two subjects**, not two applications
that resemble each other: an analyst who has used one should already know how
the other behaves, and a fix to a shared behaviour should reach both. This
package is where that shared part lives, and this file is the contract between
the two efforts. If you are working on either application — or pointing an
agent at one — start here. The family is called **PmagPy Apps**; the plan for
its next members — the hub that replaces `pmag_gui.py`, and rock-magnetism and
anisotropy applications — is in [HUB_PLAN.md](HUB_PLAN.md).

## Where code goes

| layer | where | rule |
|---|---|---|
| science | `pmagpy/demag.py`, and the paleointensity core beside it | no UI import at all; usable from a notebook or a script |
| MagIC tables | `pmagpy/magic_project.py` | reading, merging and writing contributions: `MagicProject`, `merge_results`, `trim_to_model`, `validate_directory`, taken out of `demag.py`. Shared by both cores; this branch is its home, the intensity branch adopts it from here |
| presentation | `programs/pmagpy_panel/` (**here**) | how a PmagPy Panel application looks and behaves |
| the application | `programs/<app>/` | only what is specific to that subject: its panes, its plots, its session |

The `programs/` packages install as top-level packages (`setup.py` maps
`pmagpy_panel`, `pmagpy_apps` and `pmagpy_directions` to their directories;
the wx programs stay excluded), and nothing here may be imported by `pmagpy`.
The dependency arrows point one way: hub → application → toolkit → `pmagpy` →
nothing of ours.

When you find yourself about to copy something out of `pmagpy_directions`,
that is the signal to move it here instead. Equally: if a thing knows what a
demagnetization step or a Thellier step *is*, it does not belong here.

## What is in the toolkit

* **`theme.py`** — the palette, the CSS, Bokeh figure styling, and
  `ComponentColors`, which keeps a component's colour the same everywhere it
  appears. Also `kpi()`, `SECTION_STYLE`, `lighten()`, `style_figure()`,
  `asset_data_uri()`.
* **`widgets.py`** — the custom `JSComponent`s: `Splitter` (the vertical
  boundary between the side column and the main pane, which moves *both*),
  `HeightSplitter` (resizes the plots), `Hotkeys` (forwards key presses).
* **`nets.py`** — equal-area primitives. `net_figure()` builds a square,
  toolbar-less figure and `keep_circular()` guards it; `declutter_labels()`
  thins labels where symbols pile up.
* **`shell.py`** — the page every application is built on. An application
  returns a `Body` (its side column, main pane, header line and modal); a host
  wraps it — `shell.template()` for a standalone page, the hub when it mounts
  the application — and fills the body's `open_modal`/`close_modal`/`show_side`
  hooks. `Workspace` is the side column + drag handle + main pane;
  `status_line()` follows a session's `status`; `asset_url()` names a file in
  the application's static directory (the favicon must be a URL, not a data URI).
* **`runtime.py`** — the one place that knows *how* the family is running:
  `query_param()` (the `?dir=` of this session), `is_local_session()`, the
  system folder dialog as a blocking call (`native_choose_directory`) and as a
  coroutine (`choose_directory`, for `async` widget callbacks — no thread),
  `hub_url()` and `open_ui()`. A packaged build (HUB_PLAN.md §8) changes this
  file and nothing else.
* **`datasets.py`** — a MagIC directory as a thing to choose, remember and
  validate: `env()`, `looks_like_magic_dir()`, `default_output_dir()`,
  `session_directory()` (`?dir=` → environment → default), the recent list
  shared by every application (`~/.pmagpy/recent_magic_dirs.json`, seeded once
  from the old per-application files), `example_dir()`.
* **`chooser.py`** — `DirectoryChooser`: the "which dataset is open" block for
  a side column and the open-a-directory dialog (system folder chooser, recent
  list, path field, in-page browser). Given any session that answers
  `directory`, `status` and `load(path) -> bool`; `require_measurements=False`
  for the hub, which opens empty directories too. Began as Yiming Zhang's on
  the intensity branch.
* **`forms.py`** — `Form`: widgets generated from `pmagpy.convert_registry.Field`
  descriptions and read back as one dict (`values()`, `missing()` for required
  fields left blank). The Convert page is built from it, so a converter added to
  the registry gets its form without any UI code; Orientation will use it for
  its conventions too.
* **`launch.py`** — the one-command launcher: stops a previous server, serves
  in dev mode with each application's `assets/` as a static directory, waits
  for the app to answer before opening a browser. With `index=True` it serves
  the family under a hub and tells the applications where the hub is.
* **`conftest.py`** — puts `programs/` and the repo root on `sys.path` for the
  toolkit's own tests (`test_shell.py`).

Nothing here holds global state. An application passes its own identity —
`AppInfo(name, app_id, env_prefixes)` — to the helpers that need it, so both
applications can be imported into one process, which the tests do.

## Running the family

```bash
pip install -e '.[apps]'      # once per environment, from the checkout
pmagpy-apps                   # serves the hub at / with every application beside it
```

`pmagpy-apps` is `programs/pmagpy_apps/launch.py`; the hub is on port 5010 and
opens an application with `/pmagpy_directions?dir=<directory>`. Each
application still runs on its own (`python programs/pmagpy_directions/launch.py`,
port 5100). The editable install is what lets the group test an unmerged
branch without a PyPI release — HUB_PLAN.md §8, rung 0.

The hub's Home (`pmagpy_apps/home.py`) is drawn from `pmagpy_apps/inventory.py`,
which describes a directory with no UI attached — counts, experiment kinds from
the LP- method codes, the contribution's id and DOI, what has been interpreted,
metadata gaps, and a guess at the format of lab files awaiting conversion. To
list a new application on Home add an `Application` to `home.APPLICATIONS` with
the experiment kinds it opens; the door opens once its package imports.

"Download from MagIC…" (`pmagpy_apps/download.py`) fills a folder with a public
contribution given its ID or the paper's DOI and reopens Home on it. The
EarthRef calls are in `pmagpy.magic_project` (`find_contributions`,
`fetch_contribution`, `unpack_contribution`, `download_contribution`) and work
from a script too:

```python
from pmagpy import magic_project as mp
mp.download_contribution("10.1130/G53450.1", "~/MagIC/Ordovician_Eastern_Laurentia", report=print)
```

"Convert files…" turns the page over to Convert (`pmagpy_apps/convert.py`):
the format the inventory guessed is preselected, the files that format takes
are chosen, and the form is generated from the registry's `fields`. The run
happens off the event loop; the converters' output sits under the result, and
Home fills in when the tables are written. Every converter is described once in
`pmagpy/convert_registry.py` — the function, its keywords, what to ask, an
example file — and the same call works from a script:

```python
from pmagpy import convert_registry as reg
result = reg.convert_files(reg.FORMATS["jr6_jr6"], ["AF.jr6", "TRM.jr6"],
                           {"location": "Negev", "samp_con": "1"}, dir_path="~/MagIC/Negev", report=print)
result.ok, result.tables      # True, {'measurements': 1154, 'specimens': 98, 'samples': 30, 'sites': 10, 'locations': 1}
```

A conversion that wrote tables is appended to `pmagpy_conversions.json` beside
them — when, which format, which files, the fields given, whether it appended,
the rows written, the files that failed — so the directory remembers what its
tables came from (`reg.read_conversions(dir_path)`; `record=False` leaves no
entry). Home reads it: the Import line says "converted from 10 CIT files ·
2 Sep 2026" rather than counting the files beside the tables, and the aside
marks the files that were converted. Unpacking a contribution file on the
Convert page is recorded the same way (format `magic`).

The same registry is a command. `pmagpy-convert` (installed by `setup.py`; or
`python -m pmagpy.convert_cli`) lists the formats, `pmagpy-convert sio --help`
prints SIO's fields as options — dashes for underscores, `--no-<name>` to turn
off a flag that defaults on, naming codes and choices spelled out, the shipped
example as an `Example:` line — and

```
pmagpy-convert sio af.dat thermal.dat --codelist AF T --location Hawaii --dir ~/MagIC/Hawaii
pmagpy-convert tdt --dir ~/MagIC/ATPI           # a directory format reads --dir itself
pmagpy-convert cit PI47-.sam --samp-con 2 --specnum 1 --append --log
```

is the same `convert_files` call the page makes, so it leaves the same tables
and the same log entry (`--no-record` to leave none; exit 0 converted, 1 the
conversion failed, 2 bad usage). The older `programs/conversion_scripts/`
keep their own flags and are untouched. `pmagpy/test/test_convert_cli.py`
builds a parser for every format and runs SIO, TDT and a failing JR6.

To add an instrument: write its converter in `pmagpy/convert_2_magic.py`, put an
example file under `data_files/convert_2_magic/`, and register one `Format` —
`pmagpy/test/test_convert_registry.py` converts every example, and the Convert
page offers the format the next time it loads.

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

Each application has a colour, kept in `pmagpy_panel.APP_COLORS` by `app_id`
(Directions `#00A8C8`, Intensity `#F4633A`, Rock magnetism `#A8CF3A`, FORC
`#FFB627`, Anisotropy `#8E6BBE`); `AppInfo.color` reads it, `shell.template`
paints the header with it (white or dark text as the colour needs — a light
header wants a dark logo, so ship one), and the hub's Analyze door for the
application is the same colour. Buttons keep the family blue everywhere.

`app.py` should expose `build_body(session) -> shell.Body` and a `create_app()`
that wraps it with `shell.template(body, logo=LOGO, hub_url=runtime.hub_url())`
— see `pmagpy_directions/app.py`. The body is what the hub will mount; anything
that only works inside `create_app` will not work under the hub. Do not write a
"which dataset is open" block or an open-directory dialog: subclass or compose
`chooser.DirectoryChooser`, giving it your session and a `count` callable
(Directions' `DataView` is eleven lines), and hang anything subject-specific —
an importer for another program's files — off `modal(*extra)`. To appear in
the hub, add the served file to `pmagpy_apps/launch.py::application_files()`
and an `Application` to `pmagpy_apps/home.py::APPLICATIONS`.

## Conventions worth keeping identical

These are what make the two feel like one program.

* **Symbols on a net.** Circles are measured directions, filled on the lower
  hemisphere and open on the upper; a **square** is a mean; a **triangle** is a
  direction that was worked out rather than measured (the best-fit vector of a
  plane). Derived symbols take the dark edge (`#2b2b2b`); the mean is drawn on
  top of what it averages.
* **Colour carries identity, not category.** A component keeps its colour in
  every table, plot and exported figure (`ComponentColors`).
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

## Tests

```bash
pytest pmagpy/test/test_demag.py pmagpy/test/test_demag_geo.py -q   # cores (run in CI)
pytest programs/pmagpy_panel programs/pmagpy_apps -q                # toolkit and hub (needs panel/bokeh)
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
