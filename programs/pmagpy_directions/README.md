# PmagPy Directions — a MagIC 3-native successor to Demag GUI

A replacement for `programs/demag_gui.py` (8,800 lines of wxPython that reads
MagIC 3, converts to the 2.5 data model internally and back again on export)
built as a small MagIC 3-native analysis core plus a Panel web application.
Everything lives on the `demag_gui_playground` branch under
the repository proper: the UI-independent core in `pmagpy/demag.py` (with
`pmagpy/demag_geo.py` and the Natural Earth data in `pmagpy/maps/`), the
Panel application in `programs/pmagpy_directions/`, and the core tests in
`pmagpy/test/`.

```
pmagpy/demag.py              UI-independent core: load → step tables → fits → means → poles → MagIC 3 tables
pmagpy/demag_geo.py          orthographic globe geometry (pure numpy)
pmagpy/maps/                 Natural Earth 110m coastline + land (public domain, compact JSON)
pmagpy/test/test_demag.py    core tests (regression against legacy-GUI interpretations)
pmagpy/test/test_demag_geo.py

programs/pmagpy_directions/
├── app.py                 assembles the template (title "PmagPy Directions", PmagPy logo, favicon)
├── views.py               Specimen · Fits · Means · Poles · Export panes
├── plots.py               Bokeh figures (Zijderveld, nets, M/M₀, globe)
├── publication.py         matplotlib publication figures
├── session.py             shared state, persistence, export policy plumbing
├── theme.py, logger.py    colours/CSS · step-logger, splitter and hotkey JS components
├── assets/                logos, favicon
├── pmagpy_directions.py   served file:  panel serve programs/pmagpy_directions/pmagpy_directions.py --show
├── launch.py              one-command launcher (dev mode, restarts, opens the browser)
├── PmagPy Directions.command   double-clickable macOS launcher
├── test_app.py            session / export / publication / logger tests
└── ui_test.py             headless-browser suite (Playwright)
```

## Running

```bash
# environment (once); run these from the root of your PmagPy clone
mamba create -n pmagpy-directions -c conda-forge python=3.12 numpy scipy pandas matplotlib requests pytest pytz packaging
mamba activate pmagpy-directions
pip install -e .                          # this clone of pmagpy, importable and editable
pip install panel bokeh watchfiles        # the app; watchfiles enables --dev auto-reload
pip install playwright && playwright install chromium    # optional: browser test suite only

# the app — one command (stops a previous instance, reloads on code changes, opens the browser)
python programs/pmagpy_directions/launch.py
python programs/pmagpy_directions/launch.py --dir /path/to/magic/dir --output /path/to/output

# or double-click "programs/pmagpy_directions/PmagPy Directions.command" in the Finder (keep it in the Dock);
# the plain form also works:
panel serve programs/pmagpy_directions/pmagpy_directions.py --show --dev
```

`launch.py` runs the server in Panel's dev mode: after a change to any of
the app's source files the server reloads itself — refresh the browser tab,
no restart needed. Running it again replaces the running instance.

`PMAGPY_DIRECTIONS_DIR` selects the MagIC directory opened at start (default
`data_files/3_0/McMurdo`); datasets can also be switched inside the app
(*Data › Change data…* at the top of the side column: *Browse with Finder…*
opens the system folder chooser and loads the directory you pick; there are
also recent directories, a path field, and an in-page browser for sessions
served from another machine). `PMAGPY_DIRECTIONS_OUTPUT` redirects everything the
app writes to `<PMAGPY_DIRECTIONS_OUTPUT>/<dataset name>/`; by default the output
directory is the data directory, as with the legacy GUI. Recently opened
directories are remembered in `~/.pmagpy_directions_recent.json` (override with
`PMAGPY_DIRECTIONS_RECENT`; the older `DEMAG_*` variable names are still
honoured). The launcher's default port is `PMAGPY_DIRECTIONS_PORT` (5100).

## What the app does

The tabs follow the analysis: *Specimen*, *Fits*, *Means*, *Poles*,
*Export*. The side column follows the active tab: specimen
navigation and the step logger on *Specimen*; an equal-area plot of the fits
the table lists on *Fits*; the list of plotted fits
(with *Go to specimen* and good/bad toggling) on *Means*; the plotted
VGPs on *Poles*; only *Export* uses the full width. It is resizable —
drag the grey handle between it and the plots: both panels follow the
cursor and the boundary stops where the plots would be squeezed
(double-click resets it). A second handle lies across the *Specimen*
pane, between the plots and the fits: dragging it scales the three plots
together, so a large screen can give the diagram more room and a small
one can take some back to bring the fits above the fold. Re-laying out
Bokeh figures costs about 100 ms, too slow to follow a cursor, so the
drag previews the new size with a CSS transform and the figures are
resized once, on release. On the Zijderveld plot, drag = zoom
box, tap = pick a step, and box-select is one click away in the toolbar.

Performance notes: the loaded dataset (interpretations included) is shared by
all browser sessions of the server process, so reloading the page or opening
a second tab takes about a second; the MagIC data model and the controlled
vocabularies are read from the copies bundled with pmagpy (`set_env.OFFLINE`)
rather than fetched from EarthRef, so loading never waits on the network;
tabs render lazily and the interpretations table is paginated.

If a page ever shows only the blue header: the browser did not get a
websocket to the server. Check the terminal for a
`Refusing websocket connection from Origin …` line (the launcher allows
`localhost`, `127.0.0.1` and this machine's hostname on the chosen port),
and reload the tab — a tab left open from an earlier server instance stays
blank until it is reloaded.

**Specimen pane** (side column + main). Specimen chooser with previous/next,
coordinate system (specimen / geographic / tilt-corrected, offered only when
the sample orientation allows it; a dataset opens in tilt-corrected
coordinates when bedding is recorded for most specimens, geographic when
only sample orientations are, specimen coordinates otherwise, and a
specimen lacking the chosen system falls back to the next one down), Zijderveld projection (x = East,
North or NRM dec, with the legacy axis labelling), step-label
density, and the *step logger*: every measurement in sequence with dec, inc,
moment and csd. Right click toggles a measurement good/bad (struck through
and tagged). Fits are edited without modes or buttons: with a fit selected,
clicking a step (in the logger, or tapping a point on the Zijderveld or
equal-area plot) moves its nearest bound and the fit recomputes at once;
box-selecting a range sets both bounds; the bound, fit-type and name fields
apply live; `[` `]` nudge the lower bound and `{` `}` the upper. *New fit*
deselects, and the next two steps clicked become a new fit (named with the
next free letter unless you type a name). `←` `→` step through specimens.
Fit types: line, anchored line, line through the origin, plane, Fisher
mean; the same fit name gets the same colour on every specimen and plot.
Fit lines carry an arrowhead at their outward end — the fitted direction is
the vector removed between the bounds, which points away from the origin.
Step labels are thinned automatically where symbols pile up ("auto"), or
shown for every step / none. The current fit's steps are tinted in the
logger, its line is drawn on the Zijderveld diagram, its direction (or great
circle) on the equal-area plot, and open circles mark its bounds on the
M/M₀ curve. The fit controls and the single, colour-coded table of fits
(dec, inc, MAD, DANG, α95, n, quality; click a row to select a fit) sit
under the plots.

**Means pane.** Sample, site or location means of the specimen fits (lines
and planes, McFadden & McElhinny) or of the next level's means (site means
over sample means, location means over site means), per component or for
all, with α95, k, R, n. Three symbols on the net: circles are the measured
directions (filled on the lower hemisphere), a square is the mean, and a
triangle sits on every great circle at the point that circle is resolved
to — the plane's best-fit vector, the direction that goes into the mean
and into `dir_bfv_*` on export. The side column lists the lines and the
planes in separate tables, the planes one only where the data has planes:
their columns are different things and reading a pole to a plane under
the same *dec/inc* heading as a line is what makes the two look alike. A
plane is listed by the pole that defines it (*pole dec*, *pole inc*) and
the vector it resolves to (*bfv dec*, *bfv inc*), which is the pair drawn
as the triangle. The VGP the mean implies is on the Poles
tab, which draws it on the globe, rather than in the statistics table.
*Statistic* offers two more ways to average the plotted directions: a Fisher
mean of each polarity mode on its own (the comparison a reversal test rests
on — the modes are split about the principal direction, so the split does
not depend on how many directions are reversed), or the Bingham mean, which
describes an axis and so does not depend on the polarity the directions are
recorded in, with its confidence ellipse (η, ζ) in place of the α95. Both
draw a star per mean on the net and follow into the PDF, which names the
statistic it shows. Download
as PDF.

**Poles pane.** Site (or sample) VGPs for a component on an orthographic
globe (Natural Earth land, 30° graticule), so that poles read as positions
on the Earth rather than as directions on a net: the Fisher mean pole with
its A95 circle, the sampling sites as a star, the paleolatitude of the
sampling area (± A95), and the share of VGPs inverted to a common polarity.
Polarity unification works about the principal axis of the VGP set (not a
Fisher mean of the raw set), so it does not depend on how many sites are
reversed; inverted VGPs are drawn open. The axis points at the majority,
so *flip polarity* reports the antipodes instead (VGPs, pole, paleolatitude
sign and the location mean direction); the choice carries into the Means
tab, the PDF map and the locations export. Centre the globe on the pole, the
sites, either geographic pole or a chosen point — or click a point on the globe.
VGPs on the far hemisphere are counted. The same map downloads as PDF.

**Fits pane.** Every fit in the study with filters (means are
interpretations too, hence the name); go to a
specimen, delete or flag in bulk, copy the current fit's bounds to all
specimens of the site or of the study. One colour picker per fit name:
fits with the same name share a colour everywhere (logger, plots, tables,
exported figures), and the choice is kept in the `.redo` file.
The side column plots what the table shows on an equal-area net, in the
fits' own colours: the rows ticked for a bulk action, or — with none
ticked — every fit the header filters leave listed, so that filtering by
site or component draws that set as you type. Planes are drawn as great
circles and fits flagged bad are left out, both reported under the net.
Symbols thin and circles fade as the set grows, so a whole study stays
readable. The table paginates locally: a header filter typed in the
browser is only visible to the application that way.

**Export pane.** Writes MagIC 3 `specimens.txt` (one row per coordinate
system chosen, plane fits carrying the `dir_bfv_*` direction their site's
lines resolve them to), `measurements.txt` with the good/bad flags, `samples.txt`
and `sites.txt` means (site rows with VGPs, `DE-DI`, `dir_polarity`,
`dir_n_samples`, `LP-DC4` for PCA-based means), `locations.txt` with the
mean direction and the paleomagnetic pole of every component (`pole_*`,
`paleolat`, `pole_reversed_perc`, `DE-VGP`), and a `.redo`. Means, VGPs
and poles are written for every coordinate system ticked — geographic and
tilt-corrected side by side by default, as the legacy GUI wrote them — and
the polarity axis is taken from the whole study so that every location is
reported in one polarity (flip it on the Poles tab).
The merge policy is stated on the pane: the directional results of the
specimens, samples, sites and locations the dataset has measurements for
are replaced by the current interpretations; every other row (intensity
results — which also carry a `dir_dec` — and entities without demag data)
and all descriptive metadata (coordinates, ages, lithologies, …) are
inherited by the new rows; measured specimens without an interpretation
keep a minimal row so that the table hierarchy stays intact; only MagIC 3
columns are written; an optional analyst name goes into `analysts`. Every
export is checked with pmagpy's MagIC validator and the per-table report
(✓/✗ with the first failing cells) is shown in the pane. Save/load `.redo`
files; import interpretations from `specimens.txt`; preview and save
publication figures for the current specimen or for every interpreted
specimen (PDF/SVG/PNG; panel, inset or Zijderveld-only layout), a
"directions for all specimens" overview (one net per component) and the
VGP maps.

### Persistence model

Fits are the light-weight, coordinate-independent part of the
work, so they are kept in the legacy `.redo` format (specimen, fit type,
lower/upper treatment in K or T, name, colour, flag) — human readable and
interchangeable with the old GUI. The app auto-saves
`pmagpy_directions_autosave.redo` after every change and restores it on the next
load (falling back to `demag_gui.redo`, then to `specimens.txt`). Writing
the full MagIC tables is the explicit, deliberate step. Measurement
good/bad flags live where MagIC keeps them, in the `quality` column of
`measurements.txt`, and are written on export. The app never rewrites the
files it was loaded from unless the output directory is the data directory
(the MagIC workflow of building the contribution in place); in that case
the original tables are copied once to `backup_before_pmagpy_directions/` before
the first export.

### Publication figures

`publication.py` follows Slotznick et al. (2023) and Fairchild
et al. (2017): open circles (horizontal projection) and squares (vertical)
joined by thin lines, least-squares fits as translucent coloured bands with
an arrowhead pointing away from the origin and the component name beside
them, step labels thinned where they pile up (and kept clear of the
origin), `N, Up` / `S, Down` / `E` / `W` axis labels, the NRM, coordinate
system and "divisions are 10⁻ⁿ Am²" note as a title block, a
"vector component symbols" legend, an equal-area panel with the fitted
directions (lower hemisphere filled, upper open) and an M/NRM curve with a
labelled bracket over the steps of every fit. The default *panel* layout
puts the two small plots beside the diagram so nothing ever overlaps; the
*inset* layout reproduces the papers' compact style. `directions_figure`
draws the "directions for all specimens" nets with the component title,
coordinate caption and Fisher statistics inside the net (in its emptiest
corners); `components_overview_figure` lines up one such net per
component; `vgp_map_figure` draws VGPs, the mean pole with A95 and the
study location on an orthographic globe with Natural Earth land, as in
Swanson-Hysell et al. (2025, Geology, Fig. 2D). The globe geometry lives
in `demag_geo.py` (pure numpy: hemisphere clipping of polygons with rim
arcs, graticules, small circles, paleolatitude) with the 1:110m Natural
Earth coastline and land polygons bundled as 150 KB of JSON — no cartopy,
so the same code runs in scripts, the Bokeh views and a Pyodide build.
The module has no Panel/Bokeh dependency and can be used from notebooks.

## Tests

```bash
pytest pmagpy/test/test_demag.py pmagpy/test/test_demag_geo.py -q        # core (runs in pmagpy CI)
pytest programs/pmagpy_directions/test_app.py -q                          # app (needs panel/bokeh)
DEMAG_EXTRA_DATA=/path/to/Fairchild2017 pytest pmagpy/test/test_demag.py -q   # optional external regression
cd programs/pmagpy_directions
PMAGPY_DIRECTIONS_DIR=$PWD/../../data_files/dmag_magic \
PMAGPY_DIRECTIONS_CHOOSER_STUB=$PWD/../../data_files/3_0/McMurdo panel serve pmagpy_directions.py --port 5100 &
PMAGPY_DIRECTIONS_EXTRA_DATA=/path/to/Fairchild2017 python ui_test.py http://localhost:5100/pmagpy_directions screenshots/app
```

`ui_test.py` drives the served app in a headless browser: fit editing,
zoom reset, net/globe circularity, and a dataset round trip
(dmag_magic → McMurdo through the *Browse with Finder…* button, which the
`PMAGPY_DIRECTIONS_CHOOSER_STUB` variable answers on the server, → back
through the path field → the optional external dataset) checking every
tab after each switch.

`ui_test.py` also asserts a rendering invariant: every equal-area net maps
data to pixels identically in x and y (a true circle). Bokeh 3 aligns the
frames of plots that share a layout (`frame_align`), which once squeezed the
specimen net to the M/M₀ plot's axis border and drew it as an ellipse; nets
are now built with `frame_align=False` plus a BokehJS guard
(`plots.keep_circular`) that rescales the x range whenever the frame's pixel
shape changes. Check both Chromium and WebKit after layout changes.

Regression targets are interpretations already stored by the legacy GUI:
the core re-imports them (SI bounds → step indices) and must reproduce
dec/inc/MAD/n.

| dataset | interpretations | result |
|---|---|---|
| `data_files/3_0/McMurdo` (AF + thermal, lines + planes) | 992 | 992/992 identical |
| Fairchild et al. 2017 (thermal, LT-LT-Z, bedding tilt, 440 `quality=b` rows) | 926 × 3 coordinate systems | identical, except fits whose bounds enclose a `b`-flagged step: the legacy v3 path ignored `quality`, the core honours it |
| `data_files/dmag_magic` | 330 | 84 % identical; the residuals are one step at a bound and trace to defects in the example file (see below) |

Fairchild's `demag_last_session.redo` re-imports to the same bounds as its
`specimens.txt`; its site means and VGPs match `sites.txt` (119/120; the
exception is a single-specimen site whose published direction predates a
re-interpretation).

## The core (`pmagpy/demag.py`)

* `DemagData.from_directory(path)` reads the contribution with
  `cb.Contribution` and builds one tidy step table per specimen
  (`SpecimenData.steps`): `sequence`, `treat_type`, `treat_value` (SI),
  `label`, `dec_s/inc_s`, `dec_g/inc_g`, `dec_t/inc_t`, `moment`,
  `moment_norm`, `csd`, `quality`. Multi-row samples tables are handled;
  `orientation_quality == 'b'` rows are skipped.
* `Component` bounds are step indices, so duplicate treatment values and
  unit conversions never bite; `DirectionResult` carries MagIC 3 names.
* `fit()` (cached) delegates to `pmag.domean`; `mean_directions()` to
  `pmag.dolnp` (and re-uses it for means of means, carrying pure-plane
  sample means as planes); `mean_pole()` to `pmag.fisher_mean`; VGPs to
  `pmag.dia_vgp`.
* `fisher_means_by_polarity()` averages each polarity mode on its own
  (`pmag.separate_directions`) and `bingham_mean()` returns the axial mean
  with its ellipse; both take plain (dec, inc) pairs and are used by the
  Means tab's *Statistic* control.
* `best_fit_vectors()` reports where each plane's direction falls once its
  site's lines pin it down — the point of the great circle closest to the
  lines-and-planes mean, which MM88 finds by iteration and `pmag.dolnp`
  discards after using it. `plane_best_fit_vectors()` repeats that set-up to
  return the points themselves; `specimens_table()` writes them as
  `dir_bfv_dec`/`dir_bfv_inc`, resolved separately in each coordinate system.
* `mean_pole()` unifies polarity about the principal axis
  (`unify_polarity`) and reports the inverted share, the mean sampling
  location and its paleolatitude; location-level `mean_directions()` does
  the same for site means (sample and site means are never unified — mixed
  polarity within a site must stay visible).
* `write_specimens()`, `write_means()`, `write_locations()`,
  `write_measurements()` produce MagIC 3 files inside the requested
  directory only, under one export policy (`merge_results`,
  `carry_metadata`, `trim_to_model`, see the Export pane above);
  `validate_directory()` wraps pmagpy's MagIC validator.
* `read_redo()` / `write_redo()` implement the legacy `.redo` format;
  `load_components_from_specimens_table()` imports prior interpretations
  from whichever coordinate system stores them (directional rows only —
  paleointensity rows also carry `meas_step_*` and `DE-BFL`).
* Steps without an intensity are skipped with a warning rather than given
  a made-up moment.
* Projection semantics (`projection_rotation`, `axis_labels`) and plot
  geometry (`zijderveld_xy`, `equal_area_xy`, `great_circle_xy`,
  `fit_line_segment`) are here so that every front end draws the same thing.

The core lives in `pmagpy/demag.py` with its tests in `pmagpy/test/`, so
it ships with the library and runs in its CI; the app package is excluded
from the pip `pmagpy` package (as the wx GUIs are) and needs only
`pip install panel bokeh` on top of pmagpy.

## Known differences and limitations

Worth knowing before relying on the app:

* **Flagged steps at fit bounds.** The legacy Demag GUI kept a measurement
  flagged bad (`quality = 'b'`) when it sat at a fit *endpoint* (while
  skipping flagged steps inside the range); this app excludes flagged steps
  wherever they are, so such fits reproduce the legacy values minus that
  step. This is the only systematic difference found in full regressions
  against the published interpretations of two studies (Oman: 3 of 522
  fits; Jacobsville: 20 of 578).
* **Not yet carried over from the legacy GUI:** acceptance-criteria
  filtering on export, the ages dialog, `images.txt` records,
  auto-interpretation and LSQ import.
* **The polarity modes are not labelled normal and reversed.** Which mode is
  which follows from the polarity of its VGP, not from the directions — in
  the southern hemisphere normal polarity is the steeply *negative* mode, as
  McMurdo shows. The modes are reported largest first; the Poles tab settles
  polarity from the site coordinates. Bingham statistics have no MagIC
  columns for the ellipse, so both statistics are reported in the
  application and its figures, and the exported tables keep the Fisher mean.
* **Platforms.** Developed and tested on macOS; the *Browse with Finder…*
  system chooser is untested on Windows/Linux (the path field, recent
  directories and the in-page browser work everywhere).

## Framework comparison (kept for the record)

Three prototypes were built on the same core before choosing Panel:
Panel + Bokeh (server-side object model, Python callbacks, Bokeh
selection tools), Plotly Dash (stateless callbacks, state in the browser)
and marimo (reactive notebook that also runs as an app; WASM export
possible). Panel was chosen for the readability of its analysis loop, its
selection tools, continuity with `rockmag.py`, and because the same
components render in a notebook. The Dash and marimo prototypes have been
removed.

## Data-file notes discovered along the way

* `data_files/dmag_magic/measurements.txt`: 1,056 rows are column-shifted
  (method codes sit in the `quality` column); 265 of its 441 specimens have
  no readable demag steps in *any* reader.
* Specimens tables mix directional rows with paleointensity rows that also
  carry `meas_step_min/max` and a `DE-BFL` code; importers must key on
  `dir_dec` (or exclude `LP-PI*`).

* `data_files/3_0/McMurdo/specimens.txt` has ten hysteresis rows whose
  `experiments` are not in `measurements.txt`; the validator flags them and
  the app leaves them untouched.
* pmagpy's `validate_upload3` crashed on empty integer cells
  (`math.trunc(nan)`) and on empty cells in cross-table lookups (`isIn`);
  fixed upstream in [PmagPy/PmagPy#914](https://github.com/PmagPy/PmagPy/pull/914)
  (issue [#913](https://github.com/PmagPy/PmagPy/issues/913)), merged.
