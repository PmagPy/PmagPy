# PmagPy Intensity

A Panel application for Thellier-type paleointensity, built on MagIC Data
Model 3 and on the Standard Paleointensity Definitions. It is the successor to
`thellier_gui.py`, and it is the paleointensity half of a pair: PmagPy
Directions does demagnetization, this does intensity, and the two share a
toolkit so that an analyst who knows one already knows the other. Each
application in the family has a colour — this one is `#F4633A`, the header you
see and its door on the PmagPy Apps hub — and they are told apart by that and
by nothing else, which is the intention.

```bash
python programs/pmagpy_intensity/launch.py --dir data_files/3_0/Megiddo
```

That starts a server on <http://localhost:5101/pmagpy_intensity> and opens a
browser at it. There is no build step and nothing to install beyond PmagPy's
own dependencies; the science runs in the same Python that serves the page.

Or start the whole family at once and pick a dataset there:

```bash
pmagpy-apps
```

That serves the **PmagPy Apps** hub at <http://localhost:5010/> with this
application beside it, so a directory is opened once and every application
works on it. The hub takes the inventory of a directory and only opens the
doors the measurements support — Intensity's door opens when the directory has
Thellier experiments in it.

* **[What it does](#what-it-does)** · [Tabs](#the-seven-tabs) ·
  [Keyboard](#keyboard) · [Files it writes](#files-it-writes)
* **[Coming from Thellier GUI](#coming-from-thellier-gui)** —
  [what is the same](#what-you-can-carry-over) ·
  [what changed](#what-behaves-differently-and-why) ·
  [what is new](#what-is-new)
* **[Using the core without the GUI](#using-the-core-without-the-gui)**
* **[Developing](#developing)**

---

## What it does

You give it a MagIC 3 directory — anything with a `measurements.txt`, whether
converted from a lab format, downloaded from MagIC, or produced by another
PmagPy program. It reads the contribution through `contribution_builder`,
works out from the method codes which experiment each specimen was given, and
builds an Arai plot, a Zijderveld plot, an equal-area net, a decay curve and a
check plot for each one.

You then choose a temperature interval, on the plot or with the sliders, and it
computes the full set of SPD v1.2.0 statistics, applies whichever of the three
corrections the study supports, tells you which criteria the interpretation
passes and why, averages the accepted specimens by sample, site or location,
and writes MagIC 3 tables that validate against the data model.

### The parts

| | |
|---|---|
| **Input** | MagIC 3 contributions; ThellierTool `.tdt` files (imported through the data dialog); legacy `thellier_gui.redo` files; interpretations already in a `specimens.txt` |
| **Protocols** | IZZI, Coe (ZI), Aitken (IZ), original Thellier–Thellier (antiparallel pairs), microwave; with pTRM checks, pTRM tail checks and additivity checks |
| **Statistics** | the SPD v1.2.0 set, in full: Arai-fit, directional, pTRM-check, tail-check, additivity and anisotropy categories, plus Ziggie (Tully & Paterson, 2025) |
| **Corrections** | anisotropy (ATRM or AARM tensor, with Hext statistics), non-linear TRM, cooling rate |
| **Criteria** | CCRIT, RCRIT, TTA, TTB and their modified forms, PICRIT03, SELCRIT2, the study's own `criteria.txt`, or none — each with its citation |
| **Grouping** | sample, site and location means, unweighted or 1/σ²-weighted, with VADM where the site has coordinates |
| **BiCEP** | Cych et al. (2021) hierarchical curvature-bias correction, per site, in the application |
| **Output** | `specimens.txt`, `sites.txt`/`samples.txt`, `criteria.txt`, `measurements.txt`, a session file, a `.redo`, and publication figures as PDF, SVG or PNG |

Nothing needs the internet after installation.

---

## The seven tabs

The side column changes with the tab; the main pane holds the work. Drag the
handle between them to give either more room, and the handle under the plots to
resize the plots themselves.

### Specimen

Where an interpretation is made. The Arai plot on the left, at the size you set;
beside it a 2 × 2 block of the four companions — **Zijderveld**, **equal area**,
**NRM and pTRM** decay, **alteration checks** — each captioned, all four the
same width so the block reads as one thing. The step table is in the side
column and the current result runs along the bottom.

The whole tab fits a 1440-wide window without scrolling. Narrower than that and
the pane scrolls sideways; drag the handle between the columns, or pull the
**plot size** slider down — it scales the companions with the Arai plot.

* **Choosing the interval.** Box-select two points on the Arai plot to set both
  bounds, click one point to move the nearer bound, use the `T min`/`T max`
  sliders, or click a row in the step table. `[` `]` and `{` `}` nudge the lower
  and upper bound by one step; ← and → move to the previous or next specimen.
* **The step table** lists every measurement with its treatment, its Arai index
  and whether it is inside the interval. Select a row and press *Flag the
  selected step bad/good* to exclude a measurement. Flagging one half of a
  zero-field/in-field pair removes the whole Arai point, and the application
  says so rather than silently dropping it.
* **The result block** gives B, its uncertainty, the corrections that were
  applied and the verdict of the active criteria, with the failing statistics
  named.
* **Normalise** rescales the Arai plot by the NRM; **checks** draws the pTRM,
  tail and additivity checks as triangles, squares and diamonds anchored to
  the point they are compared with.

### Interpretations

Every interpretation in the study in one filterable table: bounds, n, B, β,
FRAC, k′, MAD, DANG, SCAT, the corrections applied, the quality flag and the
verdict with the reason it failed. Select rows to go to a specimen, flag it,
delete the interpretation, or auto-interpret. *Auto-interpret all* scores every
interval of at least four points on every specimen, prefers the ones that pass
the active criteria and, among those, takes the largest FRAC × n — the most of
the NRM over the most steps. Where nothing passes it offers the segment with
the fewest failures and says which they are. It reports progress while it runs,
and the interface stays responsive.

### Criteria & statistics

Every statistic the current specimen has, as **one sortable table** — statistic,
value, units, the criterion that tests it, the verdict, and the MagIC column it
is written to — under collapsible headings for the SPD categories. Sort by
verdict to bring the failures to the top, search by name, filter by category, or
tick *only the ones the criteria test*. The line above it says how many criteria
were met and names what failed.

Selecting a row explains that one statistic underneath the table: its
definition, its equation, its value, the threshold being applied, the MagIC
column and the paper it comes from, with a DOI link. A statistic that cannot be
computed says which of the three reasons applies:

| shown | means |
|---|---|
| *not applicable* | the experiment cannot produce it (IZZI_MD on a Coe experiment; a tail statistic where no tail check was done) |
| *unavailable* | the data needed is missing (an anisotropy correction with no tensor) |
| *undefined* | the arithmetic has no answer here (a curvature on three collinear points) |

None of these is a number, and none of them is `-999`.

The set itself is chosen here. The panel above the table names it, quotes its
description and links its DOI, and lists each threshold with the specimen's
value beside it. *Add Ziggie ≤ 0.1* adds Tully & Paterson's criterion to
whichever set is active.

### Corrections

The three corrections and their provenance. For each specimen: the uncorrected
intensity, the corrected one, and each correction's factor — or, when it was
not applied, the reason. The detail block for the current specimen gives the
tensor's eigenvalues, its Hext statistics, the alteration check and the
positions it was measured in.

Each correction can be set to *use if available*, *always* (fail the specimen
where it is missing) or *never*. The anisotropy alteration limit defaults to
5%, and Hext's F-test can be required.

### Group results

Sample, site and location means of the accepted specimens, with the number
averaged, the scatter in µT and per cent, δB_N, and a VADM where there are
coordinates. A dot plot shows every specimen in the selected group against the
mean and its band, so an outlier is visible before it is argued about. The
members list says which specimens were used and which were rejected, and why.

### BiCEP

Cych et al.'s (2021) hierarchical model, per site, fed from the interpretations
you have saved — not from a separate notebook and not from a re-analysis.

Choose a site, review its specimens, exclude any (with a note, which is kept as
an audit trail), and run. Sampler, draws, warm-up, chains, seed and the σ_B
prior are all exposed; the seed makes a run reproducible. It runs off the server
thread with a progress bar and a working *Cancel*, and the result is cached, so
returning to a site you have already run is instant.

What comes back: the posterior site intensity with its 95% credible interval,
the specimen curvature-versus-intensity relationship the model is built on, R-hat,
the effective sample size, the divergence count and a posterior predictive check.
*Save posterior* writes the draws next to the data. The methods block gives the
sentence to put in a paper and the citation to go with it.

If CmdStan is installed the model is sampled with it; if not, the built-in
Metropolis-within-Gibbs sampler gives the same posterior more slowly, and the
panel says which was used and how to install the other. Neither needs the
internet at run time.

### Export

A preview of exactly what will be written — specimens, sites or criteria — with
the merge policy stated above it, then *Validate*, then *Write MagIC tables*.
Validation is cell-level: it names the table, the row and the column of every
failure. Nothing is written to the data directory until the originals have been
copied to a backup folder.

Also here: save and load a session, save and load a `.redo`, import
interpretations from an existing `specimens.txt`, and save publication figures
(a specimen Arai plot, one with the checks, a site summary or a study summary)
as PDF, SVG or PNG.

---

## Keyboard

| key | does |
|---|---|
| ← → | previous / next specimen |
| `[` `]` | move the lower bound down / up one step |
| `{` `}` | move the upper bound down / up one step |

---

## Files it writes

Everything goes to the output directory, which is the data directory unless
`PMAGPY_INTENSITY_OUTPUT` says otherwise.

| file | when | what |
|---|---|---|
| `pmagpy_intensity_autosave.json` | after every change | the interpretations, so a reload or a crash loses nothing |
| `pmagpy_intensity_session.json` | on *Save session* and on export | the whole session: interpretations, flags, criteria, correction switches — human-readable JSON |
| `pmagpy_intensity.redo` | on *Save .redo* and on export | the legacy bounds format, so the old GUI can read the interpretations back |
| `specimens.txt` | on export | interpretations merged into the existing rows |
| `sites.txt`, `samples.txt` | on export | the group means |
| `criteria.txt` | on export | the criteria set the results were produced under |
| `measurements.txt` | on export, optional | the measurements with the quality flags |
| `backup_before_pmagpy_intensity/` | before the first in-place export | the original tables, copied once |

On opening a directory it restores, in this order: the autosave if there is
one, then a legacy `thellier_gui.redo` if there is one, then whatever
interpretations `specimens.txt` already holds. It says which it used.

### Settings

The directory can also be asked for on the URL — `?dir=/path/to/study` — which
is how the hub opens this application, and what a reload or a bookmark comes
back to.

| variable | does |
|---|---|
| `PMAGPY_INTENSITY_DIR` | the directory to open at start-up |
| `PMAGPY_INTENSITY_OUTPUT` | write under `<this>/<dataset name>` instead of into the data directory |
| `PMAGPY_INTENSITY_PORT` | the port (default 5101) |
| `PMAGPY_INTENSITY_RECENT` | where the recent-directory list is kept |

`THELLIER_DIR`, `THELLIER_OUTPUT` and `THELLIER_RECENT` work too, for anyone
with the old habit; the port is read from `PMAGPY_INTENSITY_PORT` only, or from
`--port`.

---

## Coming from Thellier GUI

The legacy `thellier_gui.py` is untouched and still installed. Nothing here
requires you to stop using it, and the two can read each other's
interpretations.

### What you can carry over

| | |
|---|---|
| **Your data** | the same MagIC 3 directory. No conversion, no re-import. |
| **Your interpretations** | a `thellier_gui.redo` is read as it stands. So is a `specimens.txt` that already has `meas_step_min`/`meas_step_max`, through *Import from specimens.txt*. |
| **Your criteria** | the study's own `criteria.txt` is picked up automatically and appears in the criteria list as *This study*. The named sets (CCRIT, RCRIT, TTA, TTB, PICRIT03, SELCRIT2 …) are the same ones. |
| **Your habits** | ← → to move between specimens; the Arai plot as the place where the interval is chosen; auto-interpretation over the whole study; export to `specimens.txt` and `sites.txt`. |

Interpretations written by PmagPy Intensity can be read back by the legacy GUI
through the `.redo` it writes on export.

### What behaves differently, and why

**Bounds are stored as indices and step identifiers, not as temperatures.** The
legacy format matched a bound to a step by comparing floating-point
temperatures, which is why a bound could silently land on the wrong step in a
file whose temperatures were written to a different precision. A `.redo` you
load is matched to steps once, on load, and reported if a bound does not match.

**A zero-field step with no in-field partner is not an Arai point.** The legacy
GUI plotted it at x = 0, which pulls the fit towards the origin. It is dropped,
with a note saying so. One Megiddo specimen (`mgk09t1PI01`) therefore has
n = 11 rather than 12 — which is what the published table for that study says.

**`-999` is gone.** A statistic that has no value says which kind of no-value it
is, in words, and the criteria evaluation reports *not tested* rather than
comparing a sentinel against a threshold.

**The intensity written to `specimens.txt` is the corrected one.** In the legacy
GUI, `int_abs` could be the uncorrected value while `int_corr` said `c`
([#679](https://github.com/PmagPy/PmagPy/issues/679)); the shipped Megiddo data
still shows it. Here the corrected intensity is what is written, the correction
factors are written beside it, and the method codes record which corrections
were applied.

**Export never clobbers what it did not compute.** The rows this study measured
have their intensity results replaced; directional and rock-magnetic results on
the same specimens, anisotropy tensors, ages, lithologies and every other table
are inherited unchanged. Only MagIC 3 columns are written, and the first
in-place export backs the originals up first.

**A group scattered wider than its own mean leaves `int_abs_sigma_perc`
empty.** The data model caps that column at 100 %, so a site whose specimens
disagree by more than their mean cannot put the number there at all. The
absolute `int_abs_sigma` — which is not capped — carries the same information,
and the row's description says what the percentage was. Clipping it to 100
would be a different claim.

**Curvature has no universal threshold.** `k` and `k′` are shown signed, with
their SSE, and the presets that exist in the literature are offered by name and
citation rather than one being imposed.

**It is a web application.** It runs in a browser against a local server, so it
resizes with the window, works over SSH with port forwarding, and does not need
wxPython. Only one thing is genuinely lost: there is no native menu bar, so the
file operations live in the Export tab and the data dialog.

### What is new

* **The full SPD v1.2.0 set**, validated specimen-by-specimen against the
  published calibration data — see [`docs/scientific_validation.md`](../../docs/scientific_validation.md).
* **Ziggie** (Tully & Paterson, 2025) as a first-class statistic and an
  optional criterion.
* **BiCEP** in the application, per site, from your saved interpretations.
* **Every statistic explains itself** — definition, equation, citation, DOI, and
  the threshold it is being tested against.
* **Cell-level validation** before export, so a rejected upload is diagnosed
  here rather than at MagIC.
* **ThellierTool `.tdt` import** that says what is wrong with a file instead of
  raising ([#818](https://github.com/PmagPy/PmagPy/issues/818)), and that reads
  original Thellier–Thellier antiparallel pairs.
* **Autosave**, so closing the tab does not lose an afternoon.
* **A session file you can read**, diff and put in a repository.
* **Publication figures without the GUI** — `publication.py` is importable from a
  script or a notebook.

### What is not here yet

| | |
|---|---|
| Microwave-specific plots | the statistics work on microwave data (the treatment is read as an equivalent step), but there is no power/time axis |
| Multi-specimen (MSP-DSC) methods | out of scope for this rewrite; use `pmag.py`'s routines |
| Editing measurements | this reads measurements and flags them; it does not change them |

---

## Using the core without the GUI

None of the science is in the application. Everything the panels show can be
computed from a script:

```python
import pmagpy.paleointensity as pint

data = pint.PintData.from_directory("data_files/3_0/Megiddo")
data.auto_interpret_all()                      # or set_interpretation(name, imin, imax)
result = data.result("mgk09t1PI01")
print(result.b_anc, result.passed, result.failures)

frame = data.group_results(level="site")       # a DataFrame of site means
data.write_specimens("out/")                   # MagIC 3 tables
```

The statistics alone, with no MagIC in sight:

```python
from pmagpy import pint_stats as ps

exp = pint.experiment(data.specimens["mgk09t1PI01"])
stats = ps.all_statistics(exp, 2, 9)           # the segment, by Arai index
print(stats["FRAC"].value, stats["FRAC"].text())
spec = ps.describe("k_prime")                  # definition, equation, citation, DOI
print(spec.label, spec.definition, spec.citation)
```

And a figure:

```python
from pmagpy_intensity.publication import specimen_figure, all_specimen_figures

spec = data.specimens["mgk09t1PI01"]
res = data.result("mgk09t1PI01")
fig = specimen_figure(spec, (res.imin, res.imax), res.stats, res)
fig.savefig("mgk09t1PI01.pdf")

all_specimen_figures(data, "figures/", fmt="pdf")   # or the whole study at once
```

| module | holds |
|---|---|
| `pmagpy/pint_stats.py` | the SPD statistics, York regression, curvature, Hext, the corrections. No MagIC, no UI. |
| `pmagpy/paleointensity.py` | MagIC 3: experiments, interpretations, criteria, grouping, export. |
| `pmagpy/bicep.py` | the BiCEP model and its samplers. |
| `pmagpy/tdt.py` | ThellierTool files. |
| `pmagpy/magic_project.py` | the MagIC 3 project layer, shared with PmagPy Directions. |

---

## Developing

Read [`programs/pmagpy_panel/README.md`](../pmagpy_panel/README.md) first: it is
the contract between this application and PmagPy Directions, and it says where
code belongs.

```bash
# the cores
pytest pmagpy/test/test_pint_stats.py pmagpy/test/test_paleointensity.py \
       pmagpy/test/test_tdt.py pmagpy/test/test_bicep.py \
       pmagpy/test/test_intensity_environment.py -q

# the application, and the shared toolkit and hub it now sits in
pytest programs/pmagpy_intensity/test_app.py -q
pytest programs/pmagpy_panel programs/pmagpy_apps -q

# the browser suite: start the app, then
python programs/pmagpy_intensity/ui_test.py \
       http://localhost:5101/pmagpy_intensity screenshots/intensity
```

The browser suite is what catches the things unit tests cannot: that the nets
stay circular and the Arai plot keeps its coordinate scaling after repeated
resizing, that the template builds, that the tabs draw only when they are
opened, and that nothing prints a sentinel. Running it leaves a gitignored
autosave in the data directory; delete it afterwards.

| file | holds |
|---|---|
| `session.py` | the reactive state and the persistence policy. No science. |
| `views.py` | the tabs. |
| `plots.py` | the Bokeh figures. |
| `publication.py` | the matplotlib figures, callable without the GUI. |
| `app.py` | `build_body(session)` — the `shell.Body` the hub mounts — and `create_app()`, which wraps the same body in a page of its own. |
| `launch.py` | four lines over `pmagpy_panel.launch`. |

`build_body` is the contract: anything that only works inside `create_app` will
not work under the hub.
