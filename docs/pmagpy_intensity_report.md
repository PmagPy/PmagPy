# PmagPy Intensity — final report

The successor to `thellier_gui.py`: a MagIC 3-native paleointensity
application, the pure core underneath it, the validation against published
numbers, and an honest account of what is and is not done.

**Branch:** `pmagpy_intensity`, derived from `origin/demag_gui_playground` with
`origin/master` integrated. `demag_gui_playground` has not been rewritten,
force-pushed to, or committed to directly. **No pull request has been opened.**

**Where things are**

| | |
|---|---|
| the application | [`programs/pmagpy_intensity/`](../programs/pmagpy_intensity) — start it with `python programs/pmagpy_intensity/launch.py` |
| user guide and migration guide | [`programs/pmagpy_intensity/README.md`](../programs/pmagpy_intensity/README.md) |
| the science | `pmagpy/pint_stats.py`, `pmagpy/paleointensity.py`, `pmagpy/bicep.py`, `pmagpy/tdt.py` |
| shared with PmagPy Directions | `pmagpy/magic_project.py`, `programs/pmagpy_panel/` — see [`docs/panel_architecture.md`](panel_architecture.md) |
| issue audit | [`docs/thellier_issue_audit.md`](thellier_issue_audit.md) |
| literature audit | [`docs/paleointensity_literature_audit.md`](paleointensity_literature_audit.md) |
| numerical validation | [`docs/scientific_validation.md`](scientific_validation.md) |

**In numbers**

| | |
|---|---|
| new core | 5 483 lines across four modules, no UI import anywhere |
| shared MagIC 3 layer | 535 lines, extracted from `demag.py`, which lost 324 |
| application | 3 673 lines |
| tests | 283 core, 63 application, 14 toolkit, 43 browser checks — all passing |
| statistics | the SPD v1.2.0 set in full, plus Ziggie |
| validated against | 20 SPD calibration specimens × 48 statistics; 359 published Megiddo interpretations; synthetic known-field BiCEP sites |

---

## 1. Already fixed before this work

Three of the seven open Thellier issues were partly or wholly answered by other
people before this branch started. They are recorded here because the audit had
to establish it, and because two of them are why #769 can be closed.

| what | who | evidence |
|---|---|---|
| **The `past` import that made `pmag_gui` and Thellier GUI hang** (#769's original traceback). `pmagpy/pmag.py` imports `SPD.lib.leastsq_jacobian` at module level, which ran `SPD/spd.py`'s `from past.utils import old_div`; `past` is not in `install_requires`. | fixed in the repository before this branch — `SPD/spd.py:22` now reads `from builtins import object`, and `past` appears nowhere | verified by importing the entire new core in a fresh interpreter with `past` and `future` blocked at the meta-path (`test_intensity_environment.py`) |
| **`pmagpy` and `pmagpy-cli` drifting out of sync**, the second failure in the #769 thread | [PR #904](https://github.com/PmagPy/PmagPy/pull/904) — `pmagpy-cli` now pins `pmagpy==<exact version>` from a shared version string | `pmagpy/test/test_packaging.py` guards it |
| **The Thellier GUI failure the #769 reporter hit after installing** | [PR #875](https://github.com/PmagPy/PmagPy/pull/875) | — |
| **`dia_vgp` writing a blank file**, the third failure in the #769 thread | @apivarunas, in the commit referenced in the thread | a separate program; outside this rewrite |
| **Some cookbook links** (#858) | Nick Swanson-Hysell's `cookbook_link_updates` branch: `README.md`, `CONTRIBUTING.md`, one line of `pmagpy/pmag.py` | the Thellier-specific links were still stale and are fixed here |

Nothing in this list was reproduced as a live defect; each was checked and found
already fixed, which is itself a result the audit needed.

---

## 2. Fixed during this rewrite

### 2.1 The open issues

| issue | what was wrong | what was done |
|---|---|---|
| **[#679](https://github.com/PmagPy/PmagPy/issues/679)** — anisotropy-corrected `int_abs` not exported | Reproduced **in the shipped Megiddo data**: 68 specimens carry `int_corr='c'` and an `int_corr_aniso` factor, but `int_abs` is the *uncorrected* value. Anyone reading that file gets intensities up to 33 % wrong while the file says they are corrected. | `int_abs` is now the corrected intensity; the uncorrected value, each correction factor and the method codes that produced them are written beside it. Regression test: `TestAnisotropyCorrectedExport::test_int_abs_carries_the_correction_that_int_corr_advertises`. |
| **[#170](https://github.com/PmagPy/PmagPy/issues/170)** — measurement quality flags | The legacy handler refuses: a measurement cannot be flagged bad from the GUI. | Any step can be flagged from the step table. A flag is written to `measurements.txt` as `quality='b'`, survives a reload, and is honoured by every statistic. Flagging one half of a zero-field/in-field pair removes the whole Arai point, and the consequence is reported rather than applied silently. Eight tests in `TestMeasurementQuality`. |
| **[#246](https://github.com/PmagPy/PmagPy/issues/246)** — wrong `dpal`, `dt`, `alpha`; statistics UI | `dt` (δt\*) read `-999`; `dpal` and `alpha` disagreed with ThellierTool; `k`/`k′` greyed out the rest of the statistics panel; check-boxes misbehaved on Windows. | All four statistics are computed from the SPD equations and validated against the published calibration table (§4). `-999` does not exist in the new core: a statistic that has no value says whether it is *not applicable*, *unavailable* or *undefined*, and the criteria evaluation reports *not tested*. The statistics panel shows every statistic at once with its definition, equation, citation and DOI; there is no mode in which one statistic hides another, and no native check-box to misbehave. |
| **[#818](https://github.com/PmagPy/PmagPy/issues/818)** — `.tdt` files Thellier GUI cannot read | **Three distinct defects**, all reproduced on the reporter's four files. (1) `pmag.measurements_methods3` collapses the antiparallel `.1`/`.5` steps of the original Thellier–Thellier protocol to `LT-NO`, destroying the experiment. (2) A file named `SPECIMEN.TDT` is skipped — the extension test was case-sensitive. (3) An unrecognised treatment code raises out of the converter, leaving a half-written file. | (1) `measurements_methods3` is skipped for `LP-PI-II` files, whose codes the converter has already assigned correctly. (2) The extension test is case-insensitive. (3) An unknown code produces a named error and a clean return. All four reporter files now import; their Thellier–Thellier specimen gives B = 27.8 µT, β = 0.008, FRAC = 0.97. A new reader, `pmagpy/tdt.py`, validates a file before converting it and lists what is wrong with it. |
| **[#858](https://github.com/PmagPy/PmagPy/issues/858)** — obsolete cookbook links | Five stale `earthref.org/PmagPy/cookbook/` links in `thellier_gui.py`, including two Help-menu items. | All five now point at `https://pmagpy.github.io/PmagPy-docs/...`; both targets return 200. The Help item is renamed "PmagPy documentation". The new page the issue asks for is `programs/pmagpy_intensity/README.md`. |
| **[#789](https://github.com/PmagPy/PmagPy/issues/789)** — remove Data Model 2 from `ipmag` | The blocker in the thread is "thellier_gui uses Data Model 2 functions (annoyingly)". | The new core never touches Data Model 2 — MagIC 3 names from input through export — so retiring the DM2 helpers cannot break it. Guarded three ways: an AST walk of all five modules for DM2 imports and calls, a scan for 2.5 column names as string literals, and a check that a loaded contribution never builds an `er_`, `pmag_` or `rmag_` table. |
| **[#769](https://github.com/PmagPy/PmagPy/issues/769)** — GUIs do not respond | see §1 — everything reported is fixed | 23 clean-environment tests added, plus a real verification: fresh venv, `pip install -e .`, run from outside the repository — all modules import, a study loads and interprets, the calibration files read, BiCEP runs, and the application answers HTTP 200. macOS arm64 only; see §5. |

### 2.2 Defects found in the *reference* material

Not PmagPy's, but found by implementing the standard and failing a test. Each is
documented where a reader will meet it.

| where | what |
|---|---|
| **SPD v1.2.0 §6, `δt*`** | The document's equation and its own reference `SPD.m` disagree when `B_lab` lies along **x**. `SPD.m` takes the NRM term in the (x, y) plane and the tail term in the (y, z) plane — the two halves of one difference in different planes. Implementing the document gives 1.169 and 2.247 for two specimens; implementing the index slip reproduces the published 0.00 and 2.89. The document's equation is implemented, and both values are recorded. |
| **SPD v1.2.0 §5.3, `δpal`** | The printed *vector* difference is `TRM − check`, the opposite way round from the *scalar* `check − x` used everywhere else. The printed form gives 25.4 for specimen 187A against a published 41.4; `check − TRM` gives 41.37, which is what the reference MATLAB and the published table use. `check − TRM` is implemented and documented. |
| **SPD v1.2.0 §3, `S`** | The printed equation weights by the variance *of the data*, under which `S′` is ~5×10⁻⁴ for a good fit rather than ≈ 1, and the χ² test it supports cannot work. York (1966) and Yu et al. (2000) weight by *measurement* uncertainty. SPD's printed form is the default, so values match other SPD-conformant software; supplying measurement uncertainties switches to York's weighting. Both are tested. |
| **`SPD_B_Lab.dat`** | Two defects in the calibration set's own auxiliary file: the MCT specimens' field direction should be −z, and TS01-20A-2's is a zero vector where it should be +x. Corrected copies ship with the reason recorded. |
| **the legacy `.tdt` converter** | It writes `dir_dec`/`dir_inc` to one decimal place. That moves the small vector differences the pTRM-check statistics are built from: `CDRAT`, `check(%)` and `δpal` drift by several percent. The new reader writes the precision the file carried. |

### 2.3 Behaviour corrected against the legacy GUI

| | |
|---|---|
| **A zero-field step with no in-field partner is not an Arai point.** The legacy GUI plots it at x = 0, which pulls the fit toward the origin. It is now dropped with a note. Megiddo's `mgk09t1PI01` therefore has n = 11 rather than 12 — and then reproduces the published `n`, `int_abs`, β, f and q exactly. | `build_arai` |
| **Bounds are stored as indices and step identifiers**, not as floating-point temperatures matched by comparison, so a `.redo` cannot silently land on the wrong step. A bound that does not match is reported on load. | `read_redo` |
| **A pTRM check is compared against the most recent zero-field remanence**, which may be a tail check — not against the peak zero-field step. | all check statistics |
| **An additivity check is compared against the in-field vector at the peak temperature**, not the previous measurement. | `additivity_check_statistics` |
| **A check performed after a temperature with no Arai point** is compared against the nearest point at or below the peak, rather than against itself. | `peak_index` |
| **Anisotropy: the zero-field baseline is subtracted from each ATRM position** before the tensor is fitted. Getting this wrong changed 68 of Megiddo's correction factors. AARM is preferred where both exist; the 5 % alteration limit is applied; Hext's F-test is available. | `fit_anisotropy_tensor` |
| **`A₂` is published per microtesla.** Used against a field in tesla it must be scaled by 10⁶, or the non-linear correction silently vanishes instead of failing. | `nlt_correction` |
| **`IZZI_MD` is reported as *not applicable* outside IZZI**, rather than as a number that means nothing. The bare function still computes SPD's unsigned value for any protocol. | `arai_statistics` |
| **Export inherits what it did not compute.** Intensity results on measured specimens are replaced; directional and rock-magnetic results on the same rows, tensors, ages, lithologies and every other table are preserved. Only MagIC 3 columns are written, and the first in-place export backs up the originals. | `merge_results(…, owns=)` |
| **A group scattered wider than its own mean leaves `int_abs_sigma_perc` empty.** The data model caps that column at 100 %, so a site whose specimens disagree by more than their mean cannot express the number there — Megiddo's `mgf13` is 122 %. The uncapped `int_abs_sigma` carries the same information and the description says what the percentage was; clipping it to 100 would be a different claim. Site rows also now carry `result_type = a`. | `sites_table` |
| **A `.redo` bound that is not a step of the specimen is reported.** Nearest-temperature matching is how a bound silently lands on the wrong step. The interpretation is still made — the nearest step is nearly always the intended one — but the mismatch is named. | `read_redo`, `REDO_STEP_TOLERANCE` |
| **Validation failures arrive as cells, not as a frame.** `validate_upload3` hands back a DataFrame whose truthiness raises; it is normalised to one `{row, column, problem}` per failing cell, which is what the Export tab shows. The validator also no longer drops a `<table>_errors.txt` into the study directory to say so. | `failing_cells`, `validate_directory` |

### 2.4 What was added

**The complete SPD v1.2.0 statistic set**, in all ten categories, each with its
definition, equation, units, citation, DOI and MagIC column in a machine-readable
catalogue that the UI renders rather than restates. Corrected σ_b; the anisotropy
design matrix audited against Hext (1963); `Pck`, `S`, `S′` and `pχ²` added;
signed `k` and `k′` with their SSE.

**No universal curvature threshold.** Paterson (2011)'s strict (0.164) and
relaxed (0.270) values are offered as named presets with their calibration
domain and citation, because Tauxe et al. (2021) showed curvature in lavas is
partly *fragile* — it grows over months of ageing and vanishes on a fresh TRM —
so a threshold from laboratory grain-size series does not transfer unchanged.

**Ziggie** (Tully & Paterson, 2025), with the `1/|k′| ≥ 1000` line fallback and
the ≤ 0.1 criterion, opt-in on any preset. Tested for the property the paper
argues for: invariance to scaling either axis — with a test beside it showing
`IZZI_MD` is not.

**`Z`, `Z*`, `IZZI_MD`, β and SCAT retained**, with the panel explaining what
each measures and where it overlaps another, since several of them answer the
same question in different currencies.

**BiCEP as a first-class panel** — not an iframe, a notebook or a launcher. Fed
from saved interpretations, grouped by site, with priors, sampler, draws,
warm-up, chains and seed exposed; asynchronous with a progress bar and a working
cancel; cached; deterministic under its seed. It returns the posterior site
intensity with a 95 % credible interval, the specimen curvature-bias
relationship, R-hat, ESS, divergences and a posterior predictive check, and
saves its draws. Specimens can be excluded with a note that is kept as an audit
trail. CmdStan is optional: without it the built-in Metropolis-within-Gibbs
sampler gives the same posterior more slowly, and the panel says which ran and
how to install the other. The Stan model is packaged for offline use.

**A ThellierTool reader** that validates before it converts and says what is
wrong with a file, including the original Thellier–Thellier antiparallel
protocol.

**Typed statistics.** `State.OK / NOT_APPLICABLE / UNAVAILABLE / UNDEFINED`
replaces `-999` everywhere, and the browser suite fails if a sentinel reaches
the screen.

**Autosave, a human-readable session file, and the legacy `.redo`** still
written and still read.

**Publication figures callable without the GUI**, and cell-level validation
before export.

### 2.6 The panels, after a first read-through

Three changes made on the strength of using it rather than testing it.

**The specimen plots are a block, not a column.** A plain `Row` put the Arai
plot beside a single column of four companions 1 185 px tall — three of them
below the fold on any laptop. They are now a captioned 2 × 2 block of equal
tiles beside the Arai plot, and the whole tab fits a 1440-wide window. Two
Bokeh traps came out of it, both recorded in the toolkit's README: a container
sized to its content is written in pixels, so CSS `flex-wrap` inside one never
fires; and a figure's chrome is not a constant you can guess — an allowance
that is too small silently *squashes the frame* instead of failing, which is
what had left the decay and check plots with 70 px of frame inside a 204 px
box.

**Criteria & statistics is a table.** Forty-eight statistics as a stack of
paragraphs cannot be scanned, compared or sorted. They are now one sortable
table — statistic, value, units, criterion, verdict, MagIC column — under
collapsible SPD category headings, with the prose that belongs to one statistic
(definition, equation, threshold, citation, or the reason it has no value)
shown for the row you select.

**The two applications are told apart by colour.** `theme.for_app(app_id)`
derives a whole application's chrome from one accent: navy for PmagPy
Directions, plum for PmagPy Intensity, listed together in `theme.ACCENTS` so a
third cannot collide. Chrome only — a data mark's colour still says what the
data is, never which application drew it.

### 2.5 What was shared rather than duplicated

`pmagpy/magic_project.py` — 535 lines of MagIC 3 project infrastructure — was
extracted from `demag.py` rather than written twice; `demag.py` lost 324 lines
and behaves identically. The export merge is one function told which columns the
caller owns, so both applications can write the same `specimens.txt` without
either overwriting the other.

`programs/pmagpy_panel/chooser.py` was moved out of PmagPy Directions when this
application needed the same dialog, with its own tests driving it from a stub
session — and a test asserting the toolkit's code never learns what a specimen
or a Thellier step is. PmagPy Directions now uses the moved version.

Details in [`docs/panel_architecture.md`](panel_architecture.md).

---

## 3. Intentionally deferred, with justification

### 3.1 Statistics and methods

| deferred | why |
|---|---|
| **QPI** (Biggin & Paterson, 2014) | QPI scores a *study*, not an interpretation: age control, dating method, alteration monitoring, domain state, magnetostatic interactions, whether the data were published. Several criteria are answered by information a measurements file does not carry. A QPI panel should read the `ages` and `contribution` tables; scoring it from measurements alone would produce a confident number that means nothing. Natural next step. |
| **ThellierCoolPy** (Muxworthy & Baker, 2021) | Models the blocking-temperature spectrum instead of extrapolating a TRM-versus-log-rate line, and needs rock-magnetic input (a hysteresis-derived grain distribution) that a Thellier measurements file does not contain. The line extrapolation implemented here is what the legacy GUI applied and what Megiddo's published factors were computed with, so it is what a re-analysis must reproduce. |
| **RESET** (Cych et al., 2021) | An experimental protocol with its own measurement sequence, not a statistic over the standard one. Supporting it means teaching the step classifier a new protocol — a well-defined extension, not a small one. |
| **Jeong et al. (2021) criteria** | Thresholds on statistics already implemented; a preset, not new mathematics. Can be added once the table has been transcribed from the paper and checked. |
| **Multispecimen (MSP-DSC) and Shaw-family methods** | Different experiments (`LP-PI-MULT`, `LP-PI-ALT-AFARM`). Out of scope for a Thellier-type successor. The core excludes them explicitly rather than mis-reading them. |
| **Machine-learning selection** | Nothing in the surveyed literature proposes a validated ML selector for Thellier data with published thresholds and a reference implementation. Nothing to implement. |
| **Microwave-specific plots** | Microwave data analyses correctly — the treatment is read as an equivalent step — but there is no power/time axis. Cosmetic for the statistics, real for a microwave specialist. |

### 3.2 Engineering

| deferred | why |
|---|---|
| **A shared "analysis session" base class** for the two applications | The two sessions look alike in outline but differ at every field. A base class would make one application's requirement into the other's constraint. What they genuinely share is *policy* — where output goes, what is backed up, what autosave means — and that is in `magic_project.py` and `datasets.py`, testable without either GUI. |
| **Sharing the Zijderveld plot** between the applications | Both draw one, but in Directions it is the object of study and here it is a check on the direction a segment gives. Different axes, interaction and selection model. Sharing them would have produced a configurable widget serving neither. |
| **Retiring `thellier_gui.py`** | The brief asks for the legacy GUI to be preserved until parity is demonstrated. It is untouched (beyond the #858 link fixes) and still installed. The two read each other's interpretations through the `.redo`. Retirement is a decision for after this branch has been used on real studies. |
| **Editing measurements** | This reads measurements and flags them; it does not change values. Changing measurement data belongs in the conversion step, not the interpretation step. |

### 3.3 Not done, and not deferrable to a good reason

Listed here rather than dressed up (see §5 for the risk each carries):

* **Windows and Linux verification.** No such machine was available. The tests
  are written to be platform-independent — subprocess imports and source scans,
  no compiled artefacts — but they were run on macOS arm64 only.
* **Standalone packaging smoke tests.** A clean-venv `pip install -e .` install
  and launch was verified; a frozen/standalone bundle was not built.
* **Performance profiling on a large contribution.** Megiddo (359 specimens) is
  responsive, and the caching design means one bound change recomputes one
  specimen, not the study — but no profile was taken on a contribution of
  thousands of specimens.
* **BiCEP against the published 30-site compilation.** Blocked by a licence
  conflict; see §5.

---

## 4. Issues ready to close

The live query
<https://github.com/PmagPy/PmagPy/issues?q=is%3Aissue+state%3Aopen+thellier>
was run on 1 September 2026 and returned seven open issues. All seven were
audited; none was left out.

| issue | close? | on what evidence | the test that would reopen it |
|---|---|---|---|
| **#679** anisotropy-corrected `int_abs` | **yes** | reproduced in shipped published data, fixed, and the corrected value validated against Megiddo's own published factors | `TestAnisotropyCorrectedExport::test_int_abs_carries_the_correction_that_int_corr_advertises` |
| **#170** measurement quality | **yes** | flags can be set, are written to `measurements.txt`, survive reload and change the statistics | any of the eight tests in `TestMeasurementQuality` |
| **#246** `dpal`, `dt`, `alpha`, statistics UI | **yes** | all four validated against the SPD calibration table; `-999` eliminated; the panel shows everything at once | `TestSpdCalibration::test_a_published_statistic_is_reproduced[delta_pal]`, `test_delta_t_star_matches_except_where_the_reference_code_slips`, and the browser check that the panel lists `dt*` |
| **#818** unreadable `.tdt` files | **yes** | all four reporter files import; three separate root causes fixed | `test_tdt.py::TestConversion::test_the_thellier_thellier_pair_becomes_one_arai_point`, `test_the_uppercase_extension_is_found`, `test_conversion_stops_on_an_error_unless_told_otherwise` |
| **#769** GUIs do not respond | **yes, with a caveat** | every failure in the thread is fixed (two of them before this branch); a clean-environment install and launch was verified end to end | the 23 tests in `test_intensity_environment.py`, and `test_packaging.py` — **but run them in CI on Windows and Linux first** |
| **#858** obsolete cookbook links | **partly** | the five Thellier-specific links are fixed and both targets return 200; the new documentation page the issue asks for exists | no automated test; links checked by hand |
| **#789** remove Data Model 2 | **partly** | not this branch's to close — the issue is about `ipmag.py`. What this branch supplies is the answer to the blocker in the thread: the paleointensity successor has no DM2 dependency, and three tests fail if one is introduced. The `ipmag` clean-up can proceed. | `TestNoLegacyDependency`, `TestNoDataModel2` |

**Recommended:** close #679, #170, #246 and #818 now. Close #769 once CI has run
`test_intensity_environment.py` on Windows and Linux. Leave #858 and #789 open
for the parts that belong to other branches, with a comment recording what is
done.

---

## 5. Remaining risks

Ordered by how much they should worry a reader.

### 5.1 BiCEP is not validated against the published compilation

**The risk.** `pmagpy/bicep.py` is validated against synthetic known-answer
sites (45.2 µT recovered against a true 45.0; R-hat 1.005, ESS 7 972) and runs
sensibly on a real site (Megiddo hz05, 38 specimens: 78.8 µT, 95 % credible
76.3–81.2, R-hat 1.004, ESS 718, no divergences, against a classical
75.7 ± 7.7 µT). It has **not** been checked against the 30-site compilation of
Cych et al. (2021), which is the strongest available test.

**Why.** The reference repository's licence is self-contradictory — CC BY-SA 4.0
in the repository and README, MIT in the package metadata. Redistributing its
example MagIC files into PmagPy would inherit that ambiguity. Per the brief, no
code and no data were taken; the module is written from the paper's §2.1,
§2.2.1, equation 17 of §2.2.2 and §2.2.3, and says so in its docstring.

**What would close it.** Either the authors clarifying the licence, or obtaining
the same 30 sites from the MagIC database directly, which carries no such
ambiguity. The comparison is then a script and an afternoon. Until then, a user
running BiCEP here gets a correct implementation of a published model that has
not been checked against that model's own published outputs, and the panel does
not currently say so — **worth adding a line to the methods block.**

### 5.2 One platform

**The risk.** Everything — the 394 tests, the browser suite, the clean-venv
install, the application itself — was verified on macOS arm64 only. Panel,
Bokeh, the native folder chooser and the `.tdt` reader's newline handling are
all places where Windows in particular differs.

**Mitigation in place.** The environment tests avoid compiled artefacts and use
subprocess imports and source scans; the folder chooser has three platform
branches and a test stub; file reading is newline-agnostic. But mitigation is
not verification.

**What would close it.** Running the four suites in CI on `windows-latest` and
`ubuntu-latest`. This is the single highest-value thing left, and it is cheap.

### 5.3 Two SPD values that differ from the published table

**The risk.** `δt*` for two specimens (HEL2-2d and TS01-20A-2) differs from the
published calibration table, because SPD's reference MATLAB takes the two halves
of one vector difference in different planes and the document's equation does
not. We implement the document. A user comparing our output against another
SPD-conformant package, or against the published table, will see a difference
and may reasonably conclude we are wrong.

**Mitigation.** Documented in `docs/scientific_validation.md` §1.2 with both
values, and the test asserts the discrepancy rather than tolerating it, so it
cannot drift unnoticed.

**What would close it.** Reporting it to the SPD maintainers. Same for `S`
(§2.2) and `δpal` (§2.2). All three are worth a message to the authors; none is
worth changing our implementation for on our own authority.

### 5.4 Performance at a scale not tested

**The risk.** No contribution larger than Megiddo's 359 specimens was profiled.
Auto-interpretation is O(n²) in Arai points per specimen — every segment of at
least four points is scored — which is fine at 12 points and would not be at 60.

**Mitigation in place.** Results are cached per specimen and invalidated
narrowly, so changing one bound recomputes one specimen. Auto-interpretation and
BiCEP run off the server thread with progress and cancellation. Tabs draw only
when opened.

**What would close it.** A profile on a MagIC contribution of a few thousand
specimens, and a cap or a coarse-to-fine search in `auto_interpret` if it turns
out to matter.

### 5.5 Ziggie is new

**The risk.** Tully & Paterson (2025) is a 2025 paper. Its ≤ 0.1 threshold is
calibrated on IZZI simulations and 201 known-field specimens, which is a good
foundation, but it has not had years of use.

**Mitigation.** Off by default, opt-in on any preset, with its citation shown in
the panel and carried into the export. Nobody gets it without asking.

### 5.6 Two divergences from other software, by choice

* **`IZZI_MD` is *not applicable* outside IZZI** in the panel, though the
  function computes SPD's value for any protocol. A user comparing against
  software that always prints a number will see a gap. Recorded in the
  validation document.
* **`Z*` follows SPD**, not the Ziggie reference implementation, which uses a
  different weighting. SPD and its reference MATLAB agree with each other and
  the published table was computed with them. A study reporting `Z*` should say
  which definition it used.

### 5.7 The shared layer is not yet on the other branch

`pmagpy/magic_project.py`, `pmagpy_panel/chooser.py` and `test_chooser.py` exist
on this branch only. Until they land on `demag_gui_playground`, that branch's
`demag.py` carries the 324 lines this one extracted, and the two will conflict
in a way that is easy to resolve badly. **This should be merged early**, not at
the end.

---

## What to review first

1. `pmagpy/pint_stats.py` and `docs/scientific_validation.md` together — the
   statistics and the evidence that they are right.
2. `docs/thellier_issue_audit.md` — whether each issue's answer is the answer
   you would give.
3. The application itself, on your own data:
   `python programs/pmagpy_intensity/launch.py --dir <your MagIC directory>`.
4. `docs/panel_architecture.md` — whether the shared/not-shared line is drawn
   where you want it, since moving it later is expensive.
