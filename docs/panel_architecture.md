# What PmagPy Intensity shares with the rest of the family

PmagPy's wxPython GUIs are being replaced by Panel applications over MagIC
3-native cores, served together by a hub:

| legacy | successor | subject |
|---|---|---|
| `pmag_gui.py` | `programs/pmagpy_apps` | the hub: a directory, its inventory, import, download, and the doors to the rest |
| `demag_gui.py` | `programs/pmagpy_directions` | demagnetization: directions, components, means |
| `thellier_gui.py` | `programs/pmagpy_intensity` | Thellier-type paleointensity |

Rock magnetism, FORC and anisotropy have their colours and their doors on the
hub but are not built yet. The applications are meant to be one program in
several subjects rather than several programs that happen to resemble each
other. This note says which code Intensity shares, which is deliberately its
own, and how a change in one reaches the others.

---

## The layers

```
   hub          programs/pmagpy_apps/  (1722 lines)
                home · inventory · convert · download          mounts a Body
                            │                                        ▲
   application  ┌───────────┴───────────┐                            │
                pmagpy_directions       pmagpy_intensity  ───────────┘
                ├── session.py          ├── session.py
                ├── views.py            ├── views.py
                ├── plots.py            ├── plots.py
                ├── publication.py      ├── publication.py
                └── app.py, launch.py   └── app.py, launch.py
                (4092 lines)            (3946 lines)
                            └───────────┬───────────┘
                                        ▼
   presentation             programs/pmagpy_panel/   (2056 lines)
                            theme · APP_COLORS · shell · widgets · nets
                            chooser · datasets · runtime · launch
                                        │
                                        ▼
   MagIC 3 project          pmagpy/magic_project.py  (805 lines)
                            tables · hierarchy · metadata · merge · validate
                            backup · find and download a contribution
                                        │
                     ┌──────────────────┴──────────────────┐
                     ▼                                     ▼
   science           pmagpy/demag.py                pmagpy/paleointensity.py
                     (1617)                         pmagpy/pint_stats.py
                                                    pmagpy/bicep.py, tdt.py  (5483)
                                        │
                                        ▼
                            pmagpy/pmag.py, contribution_builder, convert_registry
```

The arrows point one way and there is no arrow between two applications.
`programs/` is excluded from the pip package (`setup.py` excludes
`programs.*`), so nothing under `programs/` may be imported by `pmagpy`, and no
application may import another. Both rules are enforced by tests, and the
second is the one that matters day to day: when one application needs something
another has, the answer is never to import it, it is to move it down a layer.

The hub is the one exception in shape rather than in direction: it does not
import an application's *code*, it mounts the `shell.Body` the application
builds. An application never knows whether its host is the hub or a page of its
own.

---

## Layer 1 — `pmagpy/magic_project.py`, shared verbatim

805 lines. The first 535 were extracted from `demag.py` when the second core
needed them — `demag.py` lost 324 lines and behaves identically — and the rest
is finding and downloading a public MagIC contribution, which the hub added.
Both cores import it and neither has its
own copy.

| what | why it is shared |
|---|---|
| `read_contribution`, `MagicProject` | one way in: `contribution_builder`, canonical MagIC 3 names, the same handling of a missing or partial table |
| `build_hierarchy`, `build_site_coords` | specimen → sample → site → location is not a directions idea or an intensity idea |
| `is_null`, `to_float`, `split_codes`, `join_codes`, `natural_key`, `first_valid` | the MagIC file conventions: empty strings, `None`, `nan`, colon-joined method codes, `spec12` sorting after `spec2` |
| `display_value`, `step_label` | a treatment step in SI turned into 350 °C or 20 mT, the same way in both |
| `Orientation`, `build_orientation` | specimen → geographic → tilt-corrected, including the `SO-ASC`/`SO-POM` non-primary codes |
| `data_model`, `model_columns`, `trim_to_model` | the offline data model, and dropping columns MagIC will reject |
| `is_metadata_column`, `carry_metadata`, `directional_rows`, `intensity_rows`, `merge_results(…, owns=)` | **the export policy.** A row this analysis produced is replaced; everything else on the same row is inherited. `owns=` is what makes one policy serve two applications: Directions owns the `dir_` results, Intensity owns the `int_` ones, and neither can overwrite the other's |
| `stamp`, `software_tag(app_id)`, `backup_originals`, `write_table` | provenance and the copy-before-you-overwrite rule, with the application's own identity passed in |
| `validate_directory` | cell-level validation, table by table |

The `owns=` parameter is the interesting one. Both applications write into the
same `specimens.txt`, often the same rows. Because the merge is one function
told which columns belong to the caller, a study analysed in both applications
keeps both sets of results, and neither application has to know the other
exists.

`KELVIN_OFFSET`, `LEVELS`, `INTENSITY_COLUMNS` and the coordinate-system codes
live here too, so the two cores cannot drift on what "site" or "geographic"
means.

## Layer 2 — `programs/pmagpy_panel/`, shared verbatim

1185 lines of presentation with no science in it at all — a test strips the
docstrings and comments and asserts that the code never says *specimen*,
*demag*, *Arai* or *Thellier*.

| module | what both applications get |
|---|---|
| `theme.py` | the palette, the CSS, Bokeh figure styling, `ComponentColors` (a component keeps its colour in every table, plot and figure), `kpi()`, `lighten()`, `style_figure()`, `asset_data_uri()` |
| `__init__.py` | `AppInfo` (name, `app_id`, env prefixes, colour), `FAMILY_COLOR`, and **`APP_COLORS`** — one colour per application, read by `AppInfo.color`, so neither an application nor the hub names a hex value |
| `shell.py` | the page: an application builds a `Body` (info, main, side, header, modal) and a host wraps it — `template()` for a page of its own, the hub for a mounted one. `Workspace` is the side column, drag handle and main pane, with the heights that let the two scroll independently |
| `runtime.py` | how the family is running: the session's URL, the system folder dialog, where the hub is — the only platform-specific code |
| `widgets.py` | the `JSComponent`s: `Splitter` (the side-column boundary, which moves both panes), `HeightSplitter` (resizes the plots), `Hotkeys` (forwards key presses) |
| `nets.py` | `net_figure()` — a square, toolbar-less equal-area figure with `frame_align=False` — `keep_circular()`, and `declutter_labels()` |
| `chooser.py` | the dataset block in the side column and the "open a different one" dialog: system folder chooser, recent list, path field, in-page browser |
| `datasets.py` | `env()`, `looks_like_magic_dir()`, `default_output_dir()`, the recent list, the native folder dialog on three platforms |
| `launch.py` | the one-command launcher: stop the previous server, serve in dev mode, wait for the app to answer, open a browser. It also serves the whole family on one port, one served file per importable application on the hub's Analyze list |

Nothing here holds global state. An application passes its own identity —
`AppInfo(name, app_id, env_prefixes)` — to whatever needs it, which is why both
can be imported into one process; the test suites do exactly that.

`chooser.py` is the clearest case of the rule working. PmagPy Intensity needed
the directory dialog that PmagPy Directions already had. Copying it would have
been a hundred lines and two futures; instead it moved here, with
`test_chooser.py` driving it from a stub session that has four attributes and a
`load()`, and both applications now compose it. Intensity's ThellierTool
importer is passed to `modal(*extra)` and appended underneath, so the shared
dialog never learns what a `.tdt` file is.

## Layer 3 — the conventions, shared by agreement

These are not code, and they are what actually makes the two feel like one
program. They are written down in
[`programs/pmagpy_panel/README.md`](../programs/pmagpy_panel/README.md) and
asserted in both browser suites.

* **Symbols mean the same thing.** Circles are measured directions, filled on
  the lower hemisphere and open on the upper. A square is a mean. A triangle is
  a direction that was computed rather than measured. Derived symbols take the
  dark edge; a mean is drawn on top of what it averages.
* **Colour carries identity, not category** — a component keeps its colour
  everywhere it appears. The one colour that differs between applications is
  the *chrome*: `APP_COLORS` gives each one its own — Directions `#00A8C8`,
  Intensity `#F4633A`, Rock magnetism `#A8CF3A`, FORC `#FFB627`, Anisotropy
  `#8E6BBE` — and `shell.template` paints the header with it (white or dark
  text by luminance), the same colour as that application's door on the hub.
  **Buttons keep the family blue everywhere**, so a control looks the same
  whichever application you are in, and a data mark's colour never says which
  application drew it.
* **Layout.** A side column that changes with the task, a drag handle, then the
  main pane; only a tab that plots nothing takes the full width.
* **Tables** get the height of what they hold, use `TABLE_ROW_CSS` so hovered
  and selected rows stay readable, and never mix quantities under one heading.
* **Every pathway documents itself** (HUB_PLAN §3). A view can emit the Python
  that reproduces its current result from the core functions — `code.CodePane`
  shows it on request — and every export writes the same script beside the file
  through `code.write_beside`. It is a real constraint on the core, not a
  presentation flourish: a script that runs is only possible because the
  science takes no UI object as an argument.
* **A number that cannot be computed says so in words.** Neither application
  prints `-999`; both distinguish *not applicable* from *unavailable* from
  *undefined*, and both browser suites fail if a sentinel appears on screen.
* **Nets stay circular and plots keep their aspect ratio** after repeated
  resizing, asserted in the browser rather than assumed.
* **Keyboard.** ← → move between specimens in both.
* **Persistence.** Autosave next to the data, a human-readable session file, and
  the legacy `.redo` still written and still read.

## Layer 4 — what is deliberately not shared

| | Directions | Intensity |
|---|---|---|
| the science | `pmagpy/demag.py` | `pmagpy/paleointensity.py`, `pint_stats.py`, `bicep.py`, `tdt.py` |
| the session | components, fits, coordinate system | interpretations, bounds, criteria, correction switches |
| the plots | Zijderveld, equal-area, decay, means net | Arai, Zijderveld, net, decay, checks, group dot plot |
| the tabs | its own | its own |
| the port | 5100 | 5101 (5010 for the family on one port) |
| identity | `pmagpy_directions` | `pmagpy_intensity` |
| colour | `#00A8C8` | `#F4633A` |

A shared "analysis session" base class was considered and rejected. The two
sessions look similar in outline — a directory, a current specimen, a version
counter, autosave — but what they hold differs at every field, and a base class
would have made one application's requirement into the other's constraint. What
they genuinely share is the *policy* (where output goes, what is backed up, what
autosave means), and that lives in `magic_project.py` and `datasets.py` where it
can be tested without either GUI.

The plots are likewise not shared beyond the net primitives. Both draw a
Zijderveld diagram, but Directions' is the object of study and Intensity's is a
check on the direction that comes out of a segment; the axes, the interaction and
the selection model are different. Sharing them would have produced a
configurable widget serving neither.

---

## How a change travels

**A change in `pmagpy/` reaches both cores.** This is the reason the suites are
run *after* pulling as well as before pushing: both cores call into `pmag.py`
(`dolnp`, `domean`, `doprinc`, `fisher_mean`, `dia_vgp`, …), and an edit there
will not conflict, it will quietly change results.

**A change in `pmagpy_panel/` reaches both applications.** Say so in the commit
message and check the other one still builds. The two `test_app.py` suites and
the two browser suites are the check.

**A change in `programs/<app>/` reaches one application** and is the normal case.

**Needing something from the other application is the signal to move it down.**
That is the rule this architecture rests on, and the commit message should say
that it now affects both.

---

## Testing, by layer

| layer | suite | count |
|---|---|---|
| science, directions | `pmagpy/test/test_demag.py`, `test_demag_geo.py` | in CI |
| science, intensity | `test_pint_stats.py` (69), `test_paleointensity.py` (120), `test_tdt.py` (37), `test_bicep.py` (34), `test_intensity_environment.py` (23) | 283 |
| toolkit and hub | `programs/pmagpy_panel/`, `programs/pmagpy_apps/` | 73 |
| application | `programs/pmagpy_directions/test_app.py` (43), `programs/pmagpy_intensity/test_app.py` (63) | 106 |
| browser | `ui_test.py` in each application | 43 checks (intensity) |

The core suites need no Panel and no browser; they are the ones that must stay
in CI. The application suites need `panel`; the browser suites need a running
server and Playwright.

---

## Where the toolkit came from, and where it is going

`pmagpy_panel` was extracted from PmagPy Directions one module at a time, each
time a second application needed something the first already had: `theme`, then
`widgets`, then `nets`, then `datasets` and `launch`, then `chooser`. Nothing
was designed for reuse in advance and nothing was moved speculatively.

It has since moved twice more, and the second time in the other direction.
`magic_project.py`, `chooser.py` and the validator's cell-level report were
taken *from* this branch onto the shared one, which is now canonical for them;
and the shared branch's own additions — the `pmagpy_apps` hub, `shell`,
`runtime`, and one colour per application — came back here. Two things are
worth keeping from that:

* **`shell.Body` is the contract that made the hub possible.** An application
  builds a body — its identity, its main pane, its side column, its status
  line, its dialog — and a host wraps it: `shell.template()` for a page of its
  own, the hub for a mounted one. Nothing in an application knows which it has,
  so `build_body` is where an application's page must be assembled and
  `create_app` may hold nothing but the wrapping.
* **Adopting the shared layer cost this application one test.** The chooser's
  system dialog became a coroutine; `app.py` became `build_body` plus four
  lines. That is the return on the arrangement, and the argument for moving the
  next thing down rather than copying it.

Two candidates remain, and both are waiting for a third use to say what the
shared shape is: the plot-resize handle wiring, which both applications spell
out at about fifteen lines each, and the "flag a row good/bad" table idiom.
