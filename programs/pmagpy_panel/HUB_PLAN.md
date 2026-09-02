# PmagPy Apps — plan for the hub and the next applications

`programs/pmag_gui.py` is the wxPython front door to PmagPy: choose a MagIC
directory, convert magnetometer files into it, add orientation and metadata,
launch Demag GUI or Thellier GUI on it, then build the upload file. With
Directions and Intensity rewritten as Panel applications, the door needs
rewriting too — and further analysis applications (rock magnetism, anisotropy)
have no door at all yet: their interactives live in the notebooks of
`RockmagPy-notebooks` as ipywidgets.

The family is called **PmagPy Apps**: point-and-click applications for the
common workflows, served from a Python process on the analyst's machine. The
name says what it is and what it is not — the library, the notebooks and the
command line remain the other ways of using PmagPy, and Apps does not replace
them. Within the family, PmagPy Directions, PmagPy Intensity and the rest keep
their names; the front door — the pages that hold the MagIC directory, convert
into it, describe it, and hand it to an analysis application — is what this
plan calls *the hub*. It is the home of PmagPy Apps, not a separate program.

This plan describes what the hub does, what has to change in `pmagpy/` to make
its MagIC tasks reliable, in what order to build it, and how the family reaches
people who do not install Python. It follows the layering in [README.md](README.md); read that first.
Package names below (`pmagpy_apps` for the hub, `pmagpy_rockmag`,
`pmagpy_anisotropy`) are provisional except the first.

## 1. What exists

**Pmag GUI's task surface** (`programs/pmag_gui.py`, `dialogs/`):

| Pmag GUI | does the work | state |
|---|---|---|
| Change directory | `cb.Contribution(WD)` | fine |
| 1. Convert magnetometer files | `convert_2_magic.*` via 13 hand-coded wx frames, then `ipmag.combine_magic` twice | converters healthy; dialog layer hand-written per format |
| 2. Geographic / tilt-corrected directions | `ipmag.orientation_magic` | works; 8 orientation conventions, no tests |
| 3. MagIC metadata (incl. ages) | `ErMagicBuilder` + `ErMagicCheckFrame3` grids | the largest wx surface; wx-only |
| Download or unpack MagIC file | `ipmag.download_magic_from_id/_from_doi`, `download_magic` | works; `_from_doi` writes to cwd |
| Convert 2.5 directory to 3.0 | `pmag.convert_directory_2_to_3` | legacy, keep as is |
| Demag GUI / Thellier GUI | spawn wx frames | replaced by the Panel apps |
| Create upload file | `ipmag.upload_magic` → public validation endpoint | works; return arity inconsistent |
| menu: AzDip, IODP samples, kly4s/k15/sufar4, agm | `ipmag.azdip_magic`, `convert.iodp_samples/kly4s/k15/sufar4/agm` | works |
| menu: export result tables | `ipmag.sites_extract`, `specimens_extract`, `criteria_extract` | works |
| menu: depth plots | `ipmag.core_depthplot`, `ani_depthplot2` | works; matplotlib |

**Conversions.** `pmagpy/convert_2_magic.py` has 36 functions (~33 user-facing).
They are import-safe and UI-free, return `(ok, message)` (except `xpeem`, which
returns bare `True`), and report problems by *printing* — five `raise`
statements in 12,700 lines. Their keyword names are uniform by habit, not by
contract: `mag_file`/`magfile`, `location`/`locname`, `samp_con`/
`sample_naming_con`/`sample_nc`, `input_dir_path`/`input_dir`, `phi`/
`labfield_phi`. There is **no registry**: which function a format maps to, and
which arguments it takes, is written out three times — the wx `InitUI`/
`on_okButton` pairs, the `sys.argv.index()` blocks in
`programs/conversion_scripts/`, and the docstrings — and the three drift.
Example inputs exist for 24 formats under `data_files/convert_2_magic/`.

**MagIC tooling.** `contribution_builder.Contribution`/`MagicDataFrame` is the
MagIC 3 table layer (read, propagate up and down, ages, write);
`data_model3.DataModel` answers "which columns, which required, which
vocabulary"; `validate_upload3` validates offline; `ipmag` holds the EarthRef
API (download by ID/DOI, public validation, private workspace). Their 49-test
suite lives in `pmagpy_tests/test_contribution_builder.py`, which `pytest.ini`
does not run. Known breakage a web app would hit at once:
`upload_to_private_contribution` opens a file in binary mode with `encoding=`
(always raises); `upload_magic3` forwards its arguments into the wrong
positions; `validate_contribution` discards its result and returns `None`;
`download_magic_from_doi` has no output directory; `validate_magic` references
an undefined name. `pmagpy/magic_project.py` (Yiming Zhang's, now on this branch)
is a clean, typed, UI-free layer over `Contribution` (`MagicProject`,
`trim_to_model`, `merge_results`, `validate_directory`) and is the right base
for the hub.

**Rock magnetism.** `pmagpy/rockmag.py` already plots with Bokeh for most
experiment types (`plot_mpms_dc`, `plot_mpms_ac`, `plot_M_T`, `plot_chi_T`,
`plot_hyst_loop`, `plot_backfield_data`), and nearly all of them take
`show_plot=False, return_figure=True` — so a Panel view can wrap the returned
figure without touching the science. The ipywidgets `*_interactive` functions
(MPMS DC browser, Verwey fit, goethite removal, signal blender, coercivity
unmixing initial guess) are thin: each collects slider values and calls a pure
function (`calc_verwey_estimate`, `goethite_removal`, `mpms_signal_blender`,
`estimate_coercivity_components` → `unmix_coercivity_spectrum`). Experiments
are indexed with `make_experiment_df()` and selected with
`experiment_selection()`. Two functions used to call Bokeh `show()`
unconditionally (`_show_hyst_summary_table`,
`curie_inverse_susceptibility_interactive`; fixed 2026-09-02, §4) and
`forc.py` is matplotlib-only with no interactive layer. Nothing in `pmagpy` or
the notebooks imports Panel.

**The two Panel apps** share `pmagpy_panel` (theme, splitters, nets, datasets,
launcher, `chooser.DirectoryChooser`). Each
reads its MagIC directory from an environment variable at module load, keeps
its own recent list (`~/.<app_id>_recent.json`), and is served alone on its own
port (5100, 5101).

**Portability.** The PyPI `pmagpy` wheel is pure Python (`py3-none-any`); its
hard dependencies are numpy, scipy, matplotlib, pandas, pytz and packaging;
cartopy is a lazy optional extra; `requests` is import-guarded; the pole map's
coastlines are bundled JSON. Nothing in the apps uses a thread or a subprocess
except the native folder chooser. All of that keeps every distribution route
in §8 open — including, one day, a build that runs in the browser.

## 2. Shape of the thing

### Served first; the browser kept cheap

The family runs as a local web server — `panel serve` on the analyst's
machine, opened in a browser or in a native window (§8) — with the analyst's
own MagIC directory as the working directory: autosaved `.redo` files, written
tables and figures land beside the data, as they do in Directions today. A
build that runs entirely in the browser through Pyodide (`panel convert`) is
**not** a target of this plan. It is worth having one day — for teaching, and
for an "open in PmagPy" button on MagIC — but its file model is upload and
download (only Chromium can mount a real directory), its first load is 15–30 s,
and numerical work runs 2–5× slower; that is the wrong trade for the primary
tool.

What we do now is keep the browser build *cheap to add later*. Five rules, four
of which the hub wants anyway:

1. The shell separates *body* from *template* (next section).
2. Applications reach data only through `MagicProject` against a directory
   path — never through a dialog, an environment variable or a URL directly.
   (Pyodide's virtual file system is POSIX, so this alone makes an application
   browser-clean.)
3. No threads or subprocesses in shared code: long work is an async callback;
   the native folder chooser and the launcher live in the toolkit's runtime
   layer and nowhere else.
4. Every network call goes through the few download/validate functions in
   `ipmag`, so one `fetch` shim can replace `requests` later.
5. The toolkit and the applications are installable as a wheel (§5) — needed
   for any distribution, not only this one.

Held to these, the browser build later costs an upload mode on the chooser, a
save-as-zip, the `fetch` shim, and a `panel convert` job in CI — weeks, not a
rewrite. Broken — threads in views, `osascript` called from an application,
`requests` scattered about, a hub built as separate pages linked by URL — it
becomes one.

### One page: the hub is the template, the applications are bodies

The family is **one page**: the hub owns the template
(header, status line, modal), and each application contributes a *body* — its
side column and main pane — which the hub mounts when its card is clicked and
keeps thereafter. Nothing loads twice; the dataset is shared because it is the
same process.

This needs the shell to separate body from template, which is the `shell.py`
extraction anyway:

```python
class Body(Protocol):
    def side(self) -> pn.viewable.Viewable: ...
    def main(self) -> pn.viewable.Viewable: ...
    info: AppInfo

shell.template(body, ...)             # standalone: wrap one body
pmagpy_apps.mount(body)               # in PmagPy Apps: swap the body in
```

Served, the hub page works the same way; and a served process may *also* offer
each application at its own path (`/pmagpy_directions?dir=…`) for bookmarks
and for scripts that open a dataset directly.

**Every application still launches on its own.** The hub is additive, not a
gateway. `programs/pmagpy_directions/pmagpy_directions.py` stays the served
file, `programs/pmagpy_directions/launch.py` (and the double-click
`PmagPy Directions.command`) stay the standalone entry points, and
`python programs/pmagpy_directions/launch.py --dir /path` keeps doing exactly
what it does today, on port 5100, with no hub in the process. Nothing in an
analysis application imports the hub or knows whether it is being served.
The one visible difference under the hub is the link back to it in the header,
rendered only when there is a hub to go back to.

### The MagIC directory is the unit of state

As in Pmag GUI: a project *is* a MagIC directory. The hub holds one per session
and every page and every mounted application acts on it. It is chosen through
the toolkit's `DirectoryChooser` — the same block and dialog the analysis
applications use (native folder dialog, recent list, path field, in-page
browser for a session served from another machine) — or filled by downloading
a contribution from MagIC by ID or DOI. The recent list becomes **one file for
all applications** (`~/.pmagpy/recent_magic_dirs.json`), so a directory opened
in the hub is already in Directions' list.

### The hub's pages follow the MagIC workflow

Pmag GUI's four boxes, reorganised in the order an analyst works. All of these
are *pages in the hub*, not applications:

| page | tasks | replaces |
|---|---|---|
| **Home** | the dataset: which tables, how many rows, which experiment types; the workflow strip with state per stage; the analysis cards (§ Design) | box 0, the launch buttons |
| **Import** | *Convert* (registry-driven form, queue of files, run, log, then combine); *Orientation* (`orientation_magic`, form built from its conventions, AzDip as the simple case); *Download / unpack* (by ID, by DOI, from a `.txt` on disk or uploaded); *Legacy 2.5 → 3.0* | box 1, Import menu |
| **Metadata** | what ErMagicBuilder does: the locations / sites / samples / specimens / ages tables in grids, columns and controlled vocabularies from the data model, names propagated between levels via `Contribution`; the criteria table | box 1 step 3 (`ErMagicBuilder`, `ErMagicCheckFrame3`) |
| **Analyze** | the cards on Home: Directions, Intensity, Rock magnetism, Anisotropy — each mounts its body; disabled with a reason when the data cannot support it (no measurements; no `LP-DIR-*` steps; no `LP-PI-*`; no rock-mag or anisotropy method codes) | box 2 |
| **Upload** | validate (offline `validate_upload3.validate_table` per table, and the public endpoint); build `upload.txt` (`upload_magic`); private workspace once its function is fixed; export result tables (`*_extract`) | box 3, Export menu |

### Design: the hub must be the best-looking page in PmagPy

It is the first thing every analyst sees, and it is forms and tables rather
than plots, so it has nothing to hide behind. Rules for it:

* **One screen, the dataset as its subject.** Home says in plain words what is
  loaded — "McMurdo · 3 locations · 62 sites · 412 specimens · demagnetization
  steps, Thellier experiments, hysteresis loops" — not a list of file names.
* **The workflow is visible as a strip**, Import → Metadata → Analyze → Upload,
  each stage showing its state (done, something missing, not started) so the
  page answers "what next?" without being asked.
* **Analysis cards state facts, not labels**: "Directions — 412 specimens with
  demagnetization steps, 118 interpreted"; "Intensity — no Thellier experiments
  in this dataset" (disabled). A card is a door with a window in it.
* **No form on Home.** Forms live on their pages; Home is orientation.
* **Mock first.** A static mock of Home and of Convert, reviewed as screenshots
  on a laptop-sized viewport, before any Panel code. Playwright screenshots are
  then the review loop, as they were for Directions.

## 3. Analysis applications

### Which application, and when to split

An application answers one kind of question, with its own plots and its own
columns in the results tables. Experiment types that share plots and result
columns are tabs within one application; those that do not are another
application. By that test:

| application | question | core |
|---|---|---|
| Directions (exists) | what direction does this specimen record | `pmagpy/demag.py` |
| Intensity (in progress) | what field intensity | `paleointensity.py`, `pint_stats.py`, `bicep.py`, `tdt.py` |
| **Anisotropy** (new) | what is the fabric — AMS, ATRM, AARM; Hext and bootstrap statistics; the anisotropy columns of `specimens` | `pmag.doaniso*`, `ipmag.aniso_magic_nb`, `plot_aniso` |
| **Rock magnetism** (new) | what minerals, what grain sizes — one view per experiment type | `rockmag.py`, `forc.py` |

Rock magnetism starts as one application with a view per experiment type; FORC
is the candidate to split out later if its weight (its own pipeline, its own
smoothing controls, matplotlib figures) starts to crowd the others. Decide when
the tab count hurts, not before.

### Rock magnetism

Side column = the dataset block plus the experiment index
(`make_experiment_df`, grouped by type from the method codes: `LP-HYS`,
`LP-BCR-BF`, `LP-IRM`, `LP-FC`/`LP-ZFC`/`LP-CW-SIRM`, `LP-X-T`/`LP-X-F`, AC
susceptibility). Main pane = a view per type, each a Bokeh figure from the
existing `plot_*` function plus the controls the corresponding `*_interactive`
exposes today, now as Panel widgets driving the same pure function:

| view | plot | controls → core |
|---|---|---|
| MPMS DC (FC/ZFC/RTSIRM) | `plot_mpms_dc` | specimen; normalisation |
| Verwey | `plot_mpms_dc` + derivative | background range, excluded range, polynomial degree → `calc_verwey_estimate` |
| Goethite | — | fit range, degree → `goethite_removal` |
| AC susceptibility | `plot_mpms_ac` | frequency set |
| χ–T and Curie | `plot_chi_T` | two draggable fit endpoints → `_inverse_susceptibility`; `curie_temperature_estimates` |
| Hysteresis | `plot_hyst_loop`, summary table | corrections → `process_hyst_loop` |
| Backfield and unmixing | `plot_backfield_data` | component sliders (B, proportion, DP, skew) → `estimate_coercivity_components`, `unmix_*` |
| FORC | `pn.pane.Matplotlib` over `forc.py` | smoothing factor, profiles |

Results go back to the specimens table the way `add_Bcr_to_specimens_table`
already does, through `MagicProject.write_table`.

### Every pathway documents itself

A rule for the contract, applying to every analysis pathway in every
application, existing ones included:

1. **The view renders in a notebook.** Panel objects display inline in Jupyter
   under `pn.extension()`, so a `VerweyView(measurements)` built for the app is
   also the cell that replaces `verwey_estimate_interactive` in
   `MPMS_verwey_fit.ipynb`. The notebook in `RockmagPy-notebooks` (or the
   PmagPy notebooks, for directions and intensity) is the documented workflow,
   and it uses the same object as the GUI — never a second implementation. The
   ipywidgets `*_interactive` functions stay until each notebook has switched.
2. **Show code.** Every view can emit the Python that reproduces its current
   result from the core functions — the specimen, the parameters the analyst
   set, the call. It is shown on request and written beside every export, so a
   figure or a results table always comes with the lines that made it.
3. **The output says who made it.** Results written to MagIC tables carry the
   method codes and the software tag (`magic_project.software_tag`), as
   Directions and Intensity already do.

## 4. What has to change in `pmagpy/`

None of this imports Panel; all of it is usable from a script.

### A conversion registry — `pmagpy/convert_registry.py`

The single most valuable piece, because it collapses the triplication:

```python
@dataclass(frozen=True)
class Field:
    name: str            # canonical: mag_file, samp_con, location, labfield, phi, theta, lat, lon, noave, specnum, user …
    kind: str            # file | files | dir | text | int | float | bool | choice | naming_convention | lab_field
    label: str
    help: str = ""
    default: object = None
    required: bool = False
    choices: tuple = ()

@dataclass(frozen=True)
class Format:
    key: str             # "sio"
    label: str           # "SIO"
    function: Callable   # convert_2_magic.sio
    fields: tuple[Field, ...]
    kwargs: dict = field(default_factory=dict)   # canonical name → this function's keyword, where they differ
    examples: tuple[str, ...] = ()               # data_files/convert_2_magic/sio_magic/…

COMMON = (…)   # the block nearly every converter shares: input, dir_path/input_dir_path,
               # output table names, specnum, samp_con, location, lat, lon, noave, user
FORMATS: dict[str, Format]

def run(fmt: Format, values: dict, dir_path: str) -> ConversionResult   # ok, message, log, outputs
```

`run()` maps canonical names through `fmt.kwargs` (`cit`: `mag_file→magfile`,
`location→locname`; `k15`: `samp_con→sample_naming_con`; `_2g_bin`:
`input_dir_path→input_dir`, `phi→labfield_phi` …), captures what the converter
prints into `log`, and normalises the return (`xpeem`). Three consumers then
read one source: the hub's Convert page is *generated* from `fields`; the CLI
wrappers in `programs/conversion_scripts/` can be regenerated from it later
(they have no `argparse` today — two hand-rolled idioms across 30 files); and
`pmagpy/test/test_convert_registry.py` iterates `FORMATS` over `examples` and
asserts each run succeeds and yields a measurements table the data model
accepts. Start with the 13 formats Pmag GUI offers plus the IRM instruments
(`agm`, `vftb`, `irm`), then the rest.

### Fixes in the MagIC layer

* `magic_project.py` landed here 2026-09-01; the hub reads and writes
  through `MagicProject`.
* Keep every EarthRef call inside the few functions that make them today
  (`download_magic_from_id`, `download_magic_from_doi`,
  `validate_with_public_endpoint`, the private-workspace four) so the HTTP
  client can be swapped in one place later (§2, rule 4).
* `download_magic_from_doi(dir_path=…)` done; `upload_magic3` forwards
  correctly and `upload_magic` has one return shape (2026-09-01). Done
  2026-09-02: `upload_to_private_contribution` opens the file in binary mode
  and reports a failed request instead of raising; `validate_contribution`
  returns `(passing, {table: validate_table result})`; `validate_magic`
  downloads by DOI or by id + share key into `<top_dir>/MagIC` and returns
  `(magic_dir, upload_file)` — tests in `test_ipmag_upload.py` and
  `test_magic_upload.py`.
* `pmagpy/test/test_contribution_builder.py` (2026-09-02): the 49 legacy
  tests, now cwd-independent and valid under pandas 3 (`np.nan`, not `''`,
  for a missing float). They surfaced three library bugs, fixed:
  `MagicDataFrame.update_row` assigned a Series positionally through `iloc`
  (the values landed in the wrong columns) and could not widen a float column
  for a string; `propagate_cols`, `propagate_lithology_cols` and
  `propagate_ages` decided "target has a value" with `np.where(column, …)`,
  and NaN is truthy — under pandas 3 a `None` written into a string column
  becomes NaN, so nothing propagated up into an emptied column. The legacy
  copy in `pmagpy_tests/` still exists for the wx-era runner.
* `pmagpy/test/test_ipmag_magic_files.py` (2026-09-02): `download_magic`
  (file, `txt=…`, `separate_locs`, split directories), `combine_magic`
  (sequence, duplicates, non-measurement tables, refusals) and
  `orientation_magic` against `data_files/orientation_magic/` with the
  IGRF and sun-compass azimuths checked against `pmag.doigrf` /
  `pmag.dosundec`. `orientation_magic` fixes: sites get their `location`
  (a stale loop variable had been the key), blank `bedding_dip_direction`
  inherits like `bedding_dip`, `average_bedding` actually averages; the
  example's `site_class`-style headers are accepted (QUESTIONS 44).
  `azdip_magic` is still untested.
* `rockmag.py` (2026-09-02): `_show_hyst_summary_table` now returns the
  `DataTable` and shows it only when asked, and `process_hyst_loop` results
  carry `summary` (the numbers as a dict) and `summary_table` at all three
  exits — the hub can embed the table instead of re-deriving it.
  `curie_inverse_susceptibility_interactive` gained `show_plot` /
  `return_figure` like its siblings and returns the `column(plot, Div)`
  layout. Nothing in `pmagpy` calls Bokeh `show()` unconditionally any more.
* Keep imports lean in what the apps import: an app that needs `pmagpy.demag`
  should not pull `ipmag` (and with it all of `matplotlib.pyplot`) along. It
  is start-up time in a desktop bundle, and load time in any browser build.
  Measured 2026-09-02 (apps imported as top-level packages, the way the
  launchers do): none of the four apps imports `ipmag`; only the rockmag app
  imports pyplot, and it needs it. Two module-level costs were removed:
  `pmagpy.pmag` imported `SPD.lib.leastsq_jacobian` (→ `scipy.optimize`,
  ~0.25 s, a third of the module's import time) for the one Arai-curvature
  call — now imported inside `get_curve`; `programs/__init__.py` called
  `matplotlib.get_backend()`, which resolves the automatic backend by
  importing pyplot and probing the GUI toolkits (~0.15 s and a GUI probe in a
  server process) — it now reads the raw rcParams entry and, as its comment
  always said, leaves an explicitly set backend (`MPLBACKEND`, matplotlibrc,
  `matplotlib.use`) alone. `pmagpy/test/test_import_cost.py` holds the
  contracts. What remains is `pmagpy.pmag` itself (~0.5 s, pandas and the
  MagIC data model) — a floor every app shares.

## 5. What has to change in the toolkit

* **`shell.py`** — the template assembly now duplicated in each `app.py`
  (header, status line, side column + `Splitter` + main pane, modal wiring,
  `pn.extension` called once), split into *body* and *template* as in §2 so
  the hub can mount bodies.
* **`runtime.py`** — the one place that knows how the family is running: is a
  native folder dialog available (and which one — `osascript`, `zenity`,
  PowerShell, or the native window's own dialog when packaged, §8); how to run
  long work (async callbacks — no threads in shared code; the serialisation of
  print-happy conversions lives here too). Everything platform-specific goes
  here and nowhere else.
* **`chooser.py`** — a `describe()` of the loaded contribution (tables, counts,
  experiment types) that Home and the cards use.
* **`forms.py`** — render a sequence of `Field`s as widgets and read them back
  as a dict. Used by Convert, and by Orientation for its convention choices.
* **`log.py`** — a pane that shows captured output from a legacy function,
  with the detail Pmag GUI's `redirect=True` console gave.
* **`code.py`** — the "show code" support: a view registers the call it
  represents; the pane renders it and exports write it alongside.
* **`launch.py`** — accept several app files and an index page; keep the
  one-app form.
* **Packaging, now rather than later.** Every distribution route in §8 starts
  from an installable wheel, so the toolkit and the apps must be in one. No
  directory moves: `setup.py` maps them with `package_dir` (`'pmagpy_panel':
  'programs/pmagpy_panel'`, and one entry per app), puts `panel` in a
  `pmagpy[apps]` extra, and adds a `pmagpy-apps` console script; the apps go on
  importing as top-level packages, as they do now.

## 6. Order of work

Each step lands as its own commit(s) with tests, and each says which Pmag GUI
feature it retires. Steps 2, 3, 4 and 5 are independent of one another and can
run as parallel streams on the shared branch, which is how Directions and
Intensity were built.

0. **Foundations** (not gated on the intensity merge; that stream is at its own
   pace). Ask the other developer to land `magic_project.py` and `chooser.py`
   on `demag_gui_playground` ahead of the intensity app — both are independent
   of it. Then: `shell.py` with the body/template split; the per-session
   directory (query string → environment → default); `runtime.py`;
   `package_dir` and the `pmagpy-apps` entry point, accepted when
   `pip install -e '.[apps]'` in a fresh conda environment gives a working
   `pmagpy-apps` from a branch checkout (§8, rung 0); the shared recent file.
   *Retires nothing yet; settles the questions everything else depends on.*
   **Built 2026-09-01**: `shell.py`, `runtime.py`, `datasets.session_directory`
   / `shared_recent_file` / `example_dir`, `setup.py` `package_dir` + `apps`
   extra + `pmagpy-apps`, `programs/pmagpy_apps/` with a placeholder Home
   (port 5010; Directions opens from it with `?dir=`); Directions rebuilt on the
   shell with its suite unchanged. **Later the same day** `magic_project.py`
   and `chooser.py` came over from the intensity branch (Yiming Zhang's; the
   chooser now awaits `runtime.choose_directory` instead of running a thread,
   and takes `require_measurements=False` for the hub). This branch is
   canonical for both; the intensity app adopts them from here.
1. **Hub: Home and Analyze, then Download/unpack.** Design mock first (§2).
   *Retires Pmag GUI's box 0, box 2, and "Download or unpack".* From here the
   hub is the way to start the analysis applications.
   **Home built 2026-09-01** from the approved mock: `pmagpy_apps/inventory.py`
   reads a directory without any UI (counts, experiment kinds from the LP-
   method codes, contribution id/DOI, what is interpreted, metadata gaps
   ranked, lab-file format guess); `home.py` renders its three faces (MagIC
   contribution / lab files awaiting conversion / empty directory) with the
   workflow strip, the Analyze list (a door per application, shut with its
   reason when the directory has nothing for it or the application is not
   built), and an aside of tables or files. Recent directories show only on
   the landing, before a directory is picked; the "Change directory…" dialog
   keeps the list. Metadata on Home names the single largest gap and counts
   the rest.
   **Download/unpack built 2026-09-01.** The EarthRef calls live UI-free in
   `pmagpy/magic_project.py` (`find_contributions` by reference DOI through the
   FIESTA search API, `fetch_contribution` from `/data`, `unpack_contribution`
   over `ipmag.download_magic`, `download_contribution` tying them together
   with a `report` callback; served files carry a BOM and CRLF, and some older
   contributions have no id in their `contribution` row, so the id they were
   fetched by is written in). `pmagpy_apps/download.py` is the "Download from
   MagIC…" dialog: ID or DOI, an "Into folder" field prefilled with the
   session's directory, network and unpacking off the event loop, never over an
   existing MagIC directory (it offers `MagIC_<id>` beside it instead), Home
   reopening on the result. Verified live on six of the group's contributions
   (20340, 20549, 19314, 18693, 20614 via its DOI — two versions, the latest
   taken — and 16403, the no-id case). `ipmag.download_magic_from_doi` was
   fixed on the way (it wrote to the cwd and had a broken error return).
2. **Conversion registry, then the Convert page.** Formats in order of demand:
   SIO, CIT, 2g, generic, JR6, IODP, then IRM instruments, then the rest.
   *Retires box 1 step 1 and the Import menu's converters.*
   **Registry built 2026-09-01**: `pmagpy/convert_registry.py` describes twenty
   converters once each (`Field`/`Format`; `build_kwargs` maps canonical field
   names onto each function's own keywords by signature; `convert_files` runs
   each input in a scratch directory and combines the tables — replacing or
   appending — through `magic_project.magic_write`; `guess_format` reads a
   directory). Every registered format has an example under
   `data_files/convert_2_magic` that `pmagpy/test/test_convert_registry.py`
   converts, including the IODP chain (LIMS samples → SRM/DSCR/JR6 appended).
   Five converter bugs fell out on the way (`iodp_samples_csv`, `mini`,
   `jr6_jr6` thermal steps, `iodp_jr6_lore` pandas dtypes, and
   `MagicDataFrame.add_measurement_names` writing into the cwd).
   **Convert page built 2026-09-01**: `pmagpy_panel/forms.py` turns a format's
   `fields` into widgets (text/int/float/bool/choice/codes, and the naming
   convention with its Z count shown only for codes 4 and 7); `pmagpy_apps/
   convert.py` is the page — format preselected from the inventory's guess,
   the files the format takes chosen, the generated form, "Add to the tables
   already here" when the directory is already MagIC, the run off the event
   loop with each file reported, the converters' log under the result, and
   the session reloaded so Home fills in. A MagIC contribution file on disk
   unpacks from the same page. Home's "Convert files…" is the primary button
   when the directory holds lab files and no tables; the page turns between
   Home and Convert without leaving the URL.
   *Still to do here*: the CLI programs (`programs/conversion_scripts`) do not
   yet read the registry; the anisotropy inputs from measurements (`atrm`/
   `aarm`) are Anisotropy's Reduce tab rather than Formats — the Kappabridge
   ones and `livdb` (Liverpool's thermal and microwave paleointensity exports;
   a directory format guessed from `.livdb`/`.livdb.csv`, whose
   character-delimited site convention raised a TypeError until 2026-09-02)
   are registered since 2026-09-02; nothing records which files a
   directory's tables came from (Home says only "N files beside the tables").
   Some of `data_files/convert_2_magic` is old — the next round should track
   down current instrument exports and test with the labs that use them; the
   community converter at https://beta.paleomagnetism.org/converter/ (MIT) is
   worth reading for format details, though PmagPy keeps its own. The
   registry is instrument-agnostic on purpose: the MagIC grant proposes
   converters for rock-magnetic instruments (Lakeshore VSM and the like), and
   they join as a function in `convert_2_magic` plus one `Format`.
3. **Metadata and Upload pages.** *Retires ErMagicBuilder, box 3, Export
   menu.*
   **Metadata built 2026-09-01**: `pmagpy/magic_metadata.py` is the UI-free
   layer — the data model as `Column` records (label, group, type, required,
   unit, bounds, controlled and suggested vocabulary, examples), the editor's
   column order (name, parent, required columns whether present or not, the
   rest in model order, unknown columns last so nothing is lost), an
   `editor_frame` that adds the rows a table is owed by the table beneath it
   (a site the samples name, a specimen only in measurements), `save_table`
   through `magic_write` (blank rows and empty columns dropped, the original
   copied once to `backup_before_pmagpy_apps/`), Pmag GUI's row defaults,
   location bounds from the site coordinates, copy-down from the parent table,
   and `check_table` turning `validate_upload3` into cell findings (the
   validator's `value_pass_lat_checkMax` names are reduced to `lat` in
   `magic_project.plain_column_name`). `pmagpy_apps/metadata.py` is the page:
   one table at a time in a Tabulator with list editors for vocabulary
   columns, the stub rows and failing cells painted, column help on the right,
   Save reloading the session so Home's gaps follow, Check on the saved file.
   Home's "Metadata…" is the primary button when the contribution has gaps.
   *Still to do here*: propagating a saved age down the hierarchy the way
   ErMagicBuilder did (the inventory already counts a site dated in `ages.txt`
   as dated); a newer data model than the bundled 2019 copy (the page reads
   whatever `data_model(True)` returns).
   **Criteria built 2026-09-02** (step 5's last row): `criteria` joined
   `magic_metadata.TABLES`, so the same grid edits it — `table_column` picks
   from every column of the MagIC tables (`table_columns`), `criterion` from
   the names PmagPy's tools use (`DE-SPEC` … `RPOLE`), the operation from the
   data model's vocabulary. *Add default criteria* appends
   `magic_metadata.default_criteria()` — `pmag.default_criteria` written in
   the 3.0 vocabulary through the data model's `criteria_map`, checked
   against it in the tests — skipping rows already there. *Check* evaluates
   each criterion on the table it names (`check_criteria` → `CriterionCheck`:
   rows, passing, blank, or the problem — table missing, column missing,
   value not a number, table named in the singular as older files have) and
   lists the scores beside the validator's findings. `passing_rows(table_df,
   criteria, table, criterion=, blank_fails=True)` is the piece Directions'
   export can use to apply criteria (QUESTIONS 49). A blank cell fails a
   criterion, as `pmag.grade` has always ruled; `blank_fails=False` lets it
   through.
   **Upload built 2026-09-01**: `pmagpy/magic_upload.py` is the UI-free layer
   — `check_offline` (every table through `magic_metadata.check_table`),
   `build_upload_file` (`ipmag.upload_magic`, the file landing in the study
   directory as `<location>_<date>.txt` the way Pmag GUI left it),
   `validate_online` (`ipmag.validate_with_public_endpoint` → an
   `OnlineReport` of `Issue(table, column, message, rows)`; MagIC's validator
   runs the current data model and finds more than the bundled one: 33 vs 2 on
   McMurdo), and `export_tables` (`ipmag.*_extract` into
   `publication_tables/`, never beside the MagIC tables since a tab-delimited
   `specimens.txt` there would overwrite the real one). The inventory
   recognises an upload file beside the tables (`Inventory.uploads`) so Home's
   Import line no longer calls it a file to convert and the Upload stage
   reports it with its date. `pmagpy_apps/upload.py` is the page: four steps
   down the page (check, build, validate, publication tables), the slow ones
   off the event loop (MagIC takes ~70 s on McMurdo), a link to MagIC's upload
   page for the hand-off. ipmag fixes on the way: `validate_with_public_endpoint`
   crashed on any non-200 reply (`validation_results` typo); `upload_magic3`
   forwarded its arguments into the wrong positions; `upload_magic` now always
   returns the four-tuple and still hands back the file when validation could
   not reach MagIC; the `*_extract` functions wrote `.xls` (no pandas writer
   since 1.2), called `dropna('columns')`, wrote literal `\n` into the LaTeX
   preamble, referenced an undefined `out_file`, and crashed on a sites table
   without directions or a specimens table without `int_abs`
   (`map_magic.convert_site_dm3_table_*`); the directions table now comes out
   in publication column order rather than the file's. *Still to do here*:
   the private workspace (`upload_to_private_contribution` needs a MagIC
   login the hub does not hold — see `QUESTIONS.md`); openpyxl is not in the
   environment, so Excel export falls back to `.tsv` with a note.
   `validate_contribution` and `validate_magic` were fixed 2026-09-02 (§4).
4. **Rock magnetism, then Anisotropy.** One experiment type at a time, MPMS DC
   first (pure Bokeh already, simplest), then χ–T/Curie, hysteresis + backfield
   + unmixing, FORC. Each view lands with its notebook switched over and its
   "show code" (§3).
   **Rock magnetism started 2026-09-01** — `programs/pmagpy_rockmag/`, served
   by the hub as `/pmagpy_rockmag?dir=` and lit on Home's card once the package
   imports. `session.py`: `EXPERIMENT_TYPES` (whole-method-code matching, in
   view order), `experiment_index`, a `Session` with the shared `specimen`.
   `views.py`: the side column (`DataView`, `ExperimentIndex`) and the views,
   each buildable from a measurements DataFrame for a notebook. `MpmsDcView`
   is `plot_mpms_dc` (Bokeh branch; the lone-panel grid layout and the
   derivative legends were fixed in core). `VerweyView` is
   `calc_verwey_estimate` with the range/degree sliders, Bokeh panels in
   `plots.py` from the function's own return values, a KPI line, and a note
   when the residual has no clear loss inside the excluded range (the example
   has no magnetite); `calc_zero_crossing` no longer indexes past the start
   when the residual peaks at an end of the fit range. Show code (§3 item 2)
   is `pmagpy_panel/code.py` — `call`/`assign`/`script` write real Python
   from live values, `CodePane` is the toggle, `write_beside` puts the `.py`
   next to an export — and the emitted text is `exec`-tested. Example data:
   MagIC contribution 20427 as `data_files/3_0/RMB_oxyhydroxides` (mpms_dc,
   mpms_ac, χ–T, Ms–T; 1.1 MB).

   **Views added 2026-09-02** — `GoethiteView` (`calc_goethite_removal`, split
   out of `goethite_removal` so the app draws its own Bokeh panels; the
   function's fit range and degree are the controls), `AcSusceptibilityView`
   (`plot_mpms_ac` with its `phase`/`frequency` arguments; the frequency list
   is read from the run), and the two thermomagnetic views over the shared
   `ThermomagView` base (experiment picker across χ–T and in-field M–T runs,
   `temp_unit`/`smooth_window`/`remove_holder` as `prepare_thermomag_branches`
   takes them; kelvin is adopted for a run staying below 320 K): `ChiTView` is
   `plot_chi_T` (given a `show_plot` argument and y labels that follow the
   column), `CurieView` is `curie_temperature_estimates` as a table plus
   `plot_curie_estimates` in a Matplotlib pane, the method set following the
   data type the way the function's defaults do (a missing colour for
   `ms_squared_extrapolation` was fixed in core).
   `HysteresisView` is `process_hyst_loop` (the IRM decision tree: its
   `centering_protocol`, `NL_fit`, `fit_open_loop`, `fit_linear_loop` are the
   controls; the function's own Bokeh figure, a KPI row of Ms/Mr/Bc/Brh/σ/χHF
   and the Jackson & Solheid quality statistics beside it; the early exits are
   explained in prose). It needed loops to show, so a second example landed:
   `data_files/3_0/ECMB_rockmag`, the rock-magnetic subset (VSM loops,
   backfield, MPMS) of Nick's public MagIC 20213, with the script that rebuilds
   it (QUESTIONS 16). `BackfieldView` and `UnmixingView` share a
   `BackfieldBase` (experiment picker over the `LP-BCR` runs and
   `process_backfield_data`'s `smooth_mode`/`smooth_frac`/`drop_first`; LOWESS
   offered only when statsmodels is importable, QUESTIONS 19; the SIRM point of
   a curve starting at zero field is dropped for it, since the function only
   does that for a positive first field). The first is Bcr and the function's
   three-panel Bokeh grid (`plot_backfield_data(interactive=True)`); the second
   is `unmix_coercivity` (method, `n_components`, `vary_skew`; Bayes offered
   only with dynesty) with a "Choose n" button running `select_n_components`,
   a table of the components and `plot_coercivity_unmixing` in a Matplotlib
   pane; the emitted code carries the selection call only while the rule's
   count is the one shown (QUESTIONS 20–21). `ForcView` is the FORCme
   pipeline (`forc.py`) on an `LP-FORC` experiment: the pipeline was
   file-based, so core gained `process_forc_dataframe` (the measurements
   already in pandas, through the MagIC reader) and a third example landed,
   `data_files/3_0/FORC_example` — the repo's own raw MicroMag example run
   exported to a MagIC table by `export_magic_measurements_from_raw`
   (QUESTIONS 23). The controls are the smoothing (LOESS with its strength, or
   VARIFORC with a `variforc_settings` preset and smoothing factor), a square
   diagram window in mT, the colour scale, contours and regridding; the
   measured curves are drawn in Bokeh beside the pipeline's own ρ figure; the
   KPI row is curves, field step, drift correction, the LOESS spans or the
   VARIFORC preset, and the major loop's Bc. The window starts at the extent
   of the finite ρ rather than the pipeline's header default, because a MagIC
   table's header is the run's field range (QUESTIONS 24). The tab bar was
   full at ten views, so "AC susceptibility" became "χ AC". Results go back
   to `specimens.txt` through `results.SpecimenSave`, one block under the
   result of the Hysteresis, Backfield, Unmixing and Curie views: the view
   hands it the core writer (`add_hyst_stats_to_specimens_table`,
   `add_Bcr_to_specimens_table`, `coercivity_components_table` +
   `add_unmixing_to_specimens_table`, `add_curie_estimates_to_specimens_table`)
   as a function of the specimens table together with the notebook lines it
   stands for; the button runs it through `MagicProject` (one backup of the
   original into `backup_before_pmagpy_rockmag/`, `write_table`, the
   contribution re-read), stamps the rows it added or altered with the
   software tag, appends the analysis and the save's lines to `specimens.py`
   beside the table (a replayable log of every save) and shows them in the
   code block — exec'ing that code in a notebook reproduces the table. The
   Curie view adds an "Estimate to save" picker (heating first; the pick
   carries across experiments); loops in moment or volume go to
   `hyst_ms_moment`/`_volume` through a new `magnetization` argument of the
   hysteresis writer, which also takes a single result dict now. In a notebook
   session or a directory without `specimens.txt` the block says why it is
   disabled; a writer's refusal (no row for the experiment) is shown in red
   and nothing is written (QUESTIONS 27–32).
   *Anisotropy built* (2026-09-02): `programs/pmagpy_anisotropy/` over a new
   UI-free `pmagpy/anisotropy.py` — `tensor_table` (the `aniso_s` rows of
   `specimens.txt` in one frame, rotating specimen tensors to geographic and
   tilt-corrected with the sample orientations when the table has no row in
   that frame; `source` says which), `eigen`/`eigenparameters` in float64
   (`pmag.doseigs` works in float32), `specimen_hext`, `group_statistics`
   (Hext 1963 and the `pmag.s_boot`/`sbootpars` bootstrap, seeded),
   `hext_ellipses`/`bootstrap_ellipses` (the same construction as
   `pmagplotlib.plot_ell`, tested against it), `mean_record` (a
   sites/samples row with `aniso_v1..v3` cells and `aniso_tilt_correction`).
   Side column: dataset (a directory needs only `specimens.txt`), selection
   (group by site/sample/location, frame with counts and a `*` for rotated,
   type when there are several), tensor inventory. Tabs: **Eigenvectors**
   (specimen net; mean net with Hext solid / bootstrap dashed ellipses,
   bootstrap cloud, comparison direction; eigenvalue CDFs; F tests with the
   verdict; one specimen gets the Hext statistics of its own σ, n),
   **Shape** (Jelinek P′–T, Flinn; the mean tensor's shape parameters with
   the specimens' ranges), **Specimens** (the tensor table). The hub counts
   `aniso_s` rows as an Anisotropy kind, so a specimens-only directory opens
   there. *Mean save built* (2026-09-02): the "Save to <table>.txt" step is
   now the toolkit's `pmagpy_panel/results.py: TableSave` (any table; the
   rockmag `SpecimenSave` is its specimens-only subclass) and the
   Eigenvectors tab offers it for one site or sample: `mean_record` (the
   `aniso_*` cells, `method_codes` `LP-AN-ARM:AE-H[:AE-BS[-P]]`, the
   `specimens` list, the mean tensor and bootstrap parameters as JSON in
   `description`) → `add_mean_to_table`, a row of its own on `sites.txt` /
   `samples.txt` replaced on a re-save of the same type and frame; the
   calls are appended to `sites.py`. *Reduce built* (2026-09-02): the
   **Reduce** tab fits one tensor per specimen from the directory's
   `LP-AN-ARM`/`LP-AN-TRM` steps (`anisotropy.reduce_measurements` →
   `design_matrix`/`fit_tensor`, the field directions from
   `treat_dc_field_phi/theta` or the 6/9/15-position schemes, the zero-field
   step before each position as baseline, `LT-PTRM-I` → `aniso_alt`; Hext
   statistics per specimen) and saves them to `specimens.txt` through
   `TableSave` (`add_tensors_to_specimens_table`: replace the same
   type+frame, else a row), after which the session re-reads its tables
   (`Session.version`) and every tab follows. A directory with anisotropy
   measurements and no `specimens.txt` now opens, on that tab. Reproduces
   `aarm_magic` (McMurdo, 17/18) and `atrm_magic` (30 specimens) to 1e-7;
   differences are logged in QUESTIONS 43. Not yet: the 15-position AMS
   reduction of Kappabridge measurements without `aniso_s`. The §4
   MagIC-layer fixes landed 2026-09-02. *Next*: the notebook switch-over in
   RockmagPy-notebooks (QUESTIONS 12).
5. **The rest of Pmag GUI, one decision at a time** — see the table below.
   *Retires `pmag_gui.py`.* *Built (first row, 2026-09-02)*: the field
   notebook is a conversion like any other, so there is no separate
   Orientation page — `orientation_magic` and `azdip_magic` are Formats
   `orient` and `azdip` in `convert_registry` (via `Deferred`, so the
   registry still loads without `ipmag`/pyplot) and the Convert page serves
   them: `guess_format` recognises a notebook by its header
   (`sample_name` + `mag_azimuth`), the form asks the orientation and
   declination-correction conventions, bedding, GMT offset, method codes, and
   the result reads "24 samples · 2 sites". `Format.replaces` is the one new
   idea: in a directory where a measurement converter already wrote
   placeholder sample rows (CIT: azimuth 90, dip −90, `SO-MAG`), the
   notebook's rows *replace* those rows by name, all of them
   (`orientation_magic` writes one row per orientation method), while
   converter-only knowledge in non-orientation columns is carried over
   (QUESTIONS 46 for the choices).
   *Built (Kappabridge row, 2026-09-02)*: `k15`, `kly4s`, `sufar4` and the LORE
   `iodp_kly4s` export are Formats; none is guessed (`.dat`/`.txt` are every
   instrument's extensions), the analyst picks them from the menu. The
   inventory's susceptibility kind now needs `LP-X-T`/`-F`/`-H` — a bare `LP-X`
   is the bulk value the Kappabridge writes beside a tensor, and the Rock
   magnetism door stays shut on it while Anisotropy opens on the `aniso_s`
   rows. `kly4s` wrote samples/sites into the cwd (fixed); `pmag.tauV` keeps
   real eigenvalues real (numpy 2 `eig` returns complex, and every `dostilt`
   raised a ComplexWarning). QUESTIONS 47 for the choices.
   *Built (2.5 → 3.0, 2026-09-02)*: `convert_registry.upgrade_2_to_3` wraps
   `pmag.convert_directory_2_to_3` as the `legacy` Format (takes the directory,
   no fields); `guess_format` names a directory `legacy` from its 2.5 table
   names (`magic_measurements`, `er_*`, `pmag_*`, `rmag_*`) ahead of anything
   else beside them, and tells a 2.5 contribution file from a 3.0 one so Home
   can say that unpacking it is only the first of two steps. `ages` and
   `criteria` joined `MAGIC_TABLES`, so the combine step carries them. The 2.5
   files stay beside the new tables ("17 MagIC 2.5 tables beside the 3.0
   tables"); `rmag_*`, `pmag_results` and images are not translated — the log
   says so and points at MagIC's upgrade tool. QUESTIONS 48.

### Pmag GUI features still to decide

| feature | recommendation | why |
|---|---|---|
| `orientation_magic` | **done** (2026-09-02), as the `orient` format on Convert | the step between field notebook and MagIC; nothing else does it; form-driven from its conventions |
| `azdip_magic` | **done** (2026-09-02), as the `azdip` format on Convert | same job, plainer input |
| IODP sample summaries | **done**, as the `iodp_*` formats (LIMS samples, SRM section/discrete, JR6, and KLY4S from 2026-09-02) | they are conversions |
| kly4s / k15 / sufar4 | **done** (2026-09-02), as the `k15`/`kly4s`/`sufar4` formats; the directory opens Anisotropy | conversions |
| legacy 2.5 → 3.0 | **done** (2026-09-02), as the `legacy` format on Convert, guessed from the 2.5 table names | cheap; old datasets still arrive |
| export result tables (`*_extract`) | **done** (step 3, 2026-09-01): `magic_upload.export_tables` on Upload, Excel or LaTeX | publication tables; cheap |
| criteria editor (`CustomizeCriteria`, unreachable today) | **done** (2026-09-02), as the criteria grid on Metadata with defaults and a per-criterion check | criteria need a home; Directions' export can apply them through `magic_metadata.passing_rows` |
| depth plots (`core_depthplot`, `ani_depthplot2`) | **defer** | matplotlib, niche; revisit when a stratigraphic user asks |
| `ZeqMagic` (unreachable today) | **drop** | Directions covers it |
| private MagIC workspace | **defer** until its function is fixed | cannot work today |

## 7. Decisions to make early

* **Names — decided.** The family is *PmagPy Apps*; the package is
  `pmagpy_apps`, the console script `pmagpy-apps`, the URL path
  `/pmagpy_apps`, and the title bar reads "PmagPy Apps". Considered and set
  aside: "PmagPy" alone (it is the module), "Studio" (RStudio and Android
  Studio are *the* way to use their languages, a claim this family does not
  make), "Desktop" (misdescribes a browser build), "Hub" (fine as the role of
  the home pages, which is how this plan uses the word, but not a name people
  would say). Analysis applications keep their subject names.
* **Long-running work.** Async callbacks, decided once in `runtime.py` in step
  0, so nothing written later needs a thread.
* **Where the signing identity lives** (§8): an individual Apple Developer
  enrollment, or the university's organisational one. Decide before the first
  desktop bundle, not before the code.

## 8. Reaching people who do not install Python

A Panel application is a local web server and a window, and that shape gives a
ladder of distributions, each one cheaper than the last is to move up from. The
code does not change between rungs; only the wrapper does.

0. **A developer install, from the start.** The group tests from clones on
   unmerged branches, not from releases, so the first thing the packaging in
   step 0 has to deliver is that a developer install of a checkout yields the
   command. In a conda environment:

   ```
   git clone https://github.com/PmagPy/PmagPy && cd PmagPy
   git switch demag_gui_playground
   pip install -e '.[apps]'
   pmagpy-apps
   ```

   Editable installs honour `package_dir`, so `pmagpy_apps`, `pmagpy_panel` and
   the analysis apps import from `programs/` exactly as they do now, and the
   console script tracks the working tree — `git pull` is the upgrade. A group
   member who does not want a clone gets the same branch with one line,
   `pip install 'pmagpy[apps] @ git+https://github.com/PmagPy/PmagPy@demag_gui_playground'`.
   This is also the acceptance test for step 0: if `pip install -e .` on a
   fresh environment does not produce a working `pmagpy-apps`, the packaging
   is not done. (It replaces the `sys.path.insert` lines in each served file
   and `conftest.py` in the long run; they stay until every environment in
   the group has been reinstalled.)

1. **PyPI, at the first release.** The same wheel, published: `pmagpy[apps]`
   with the `pmagpy-apps` console script. In the conda environments our group
   and most of the community use, the family is two lines and no signing
   anywhere:

   ```
   pip install 'pmagpy[apps]'
   pmagpy-apps
   ```

   (`uvx --from 'pmagpy[apps]' pmagpy-apps` does the same in one line for
   anyone who has `uv`; it is not the path we document first.) Covers every
   analyst who can open a terminal — and a `.command`/`.bat` that runs those
   lines covers many who would rather not.

2. **A signed desktop bundle** for everyone else, and the successor to the
   PyInstaller standalones PmagPy has shipped before. Two recommendations:
   * **`pywebview` for the window.** It shows the Panel page in the system's
     web view (WebKit on macOS, WebView2 on Windows, GTK on Linux), so the
     result is an application, not a browser tab — and it provides *native*
     file and folder dialogs on all three systems, which retires the
     `osascript`/`zenity`/PowerShell chooser in `datasets.py` wherever the
     family runs packaged. That is a functional gain, not only cosmetic.
   * **Briefcase (BeeWare) before PyInstaller.** It builds `.app`/`.dmg`,
     `.msi` and Linux packages and carries code signing and Apple notarization
     inside its own workflow, which is where PyInstaller bundles have
     traditionally cost the most time (every shared library signed, hardened
     runtime entitlements for Python). If it fights the scientific stack,
     PyInstaller with a signing script is the well-trodden fallback;
     `constructor` (a conda installer) is a very reliable third option at the
     price of a 500 MB installer rather than an app.
   * **Signing.** macOS notarization needs Apple Developer Program membership
     ($99/yr) and a Developer ID certificate; Windows needs a code-signing
     certificate to pass SmartScreen — Azure Trusted Signing is now the
     inexpensive route. The Apple membership is the same one that publishes
     an iOS app, so one enrollment serves both this and any field application.
     An *individual* enrollment is fast and personal; an *organisational* one
     needs a legal entity with a D-U-N-S number — for us the university's
     account, with the administration that implies. PmagPy as a GitHub
     organisation is not a legal entity and cannot enrol itself.

3. **A browser build (Pyodide)**, when there is a teaching or MagIC reason —
   see §2 for what it costs and why the code is kept ready for it.

### A field application, later

The natural one records sample orientation — site and sample names, azimuth,
plunge and bedding, GPS, timestamps, photographs, sun-compass shadow angle —
and writes MagIC `samples.txt`/`sites.txt` that the hub's Orientation page
reads, so nothing is transcribed from paper. Two design points: the value is
structured, geolocated, timestamped provenance around readings still taken
with real instruments (a phone magnetometer is not a Brunton; a sun compass
from GPS and time is, and `orientation_magic` already handles it); and a
*progressive web app* needs no App Store — device orientation, geolocation,
camera and offline storage are all available to a web app installed from
Safari or Chrome, and it can share the toolkit's look. Native (Swift, or
BeeWare now that Python has official iOS support) only if App Store presence
or sensor fidelity demands it. StraboSpot and FieldMove Clino are the prior art
to study first.
