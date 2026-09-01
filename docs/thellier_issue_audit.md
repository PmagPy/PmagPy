# Thellier issue audit

Every open issue that the live query
<https://github.com/PmagPy/PmagPy/issues?q=is%3Aissue%20state%3Aopen%20thellier>
returned, audited against the code, reproduced where a reproduction was
possible, and answered in the rewrite.

**Query run:** 1 September 2026. Seven open issues: #170, #246, #679, #769,
#789, #818, #858. Nothing in the query has been left out.

Legend for **Can it be closed?**

| | |
|---|---|
| **yes** | the reported behaviour is fixed and a test would catch a regression |
| **yes, with a caveat** | fixed here, but something outside this branch still has to happen |
| **partly** | the part this rewrite owns is done; another part belongs elsewhere |

---

## Summary

| Issue | Title | Reproduced? | Fixed in | Can it be closed? |
|---|---|---|---|---|
| [#679](https://github.com/PmagPy/PmagPy/issues/679) | anisotropy-corrected `int_abs` not exported | **yes**, in published data | `pmagpy/paleointensity.py` | yes |
| [#170](https://github.com/PmagPy/PmagPy/issues/170) | measurement quality flags in Thellier GUI | yes (the handler refuses) | `pmagpy/paleointensity.py` | yes |
| [#246](https://github.com/PmagPy/PmagPy/issues/246) | wrong `dpal`, `dt`, `alpha`; statistics UI | **yes** for `dt` (`-999`) | `pmagpy/pint_stats.py` | yes |
| [#818](https://github.com/PmagPy/PmagPy/issues/818) | `.tdt` files Thellier GUI cannot read | **yes**, all four files | `pmagpy/tdt.py`, `convert_2_magic.py`, `pmagpy/pmag.py` | yes |
| [#858](https://github.com/PmagPy/PmagPy/issues/858) | obsolete cookbook links | yes | `programs/thellier_gui.py` | partly |
| [#789](https://github.com/PmagPy/PmagPy/issues/789) | remove Data Model 2 from `ipmag` | n/a | new core has none; guarded by tests | partly |
| [#769](https://github.com/PmagPy/PmagPy/issues/769) | pmag_gui / Thellier GUI does not respond | the `past` import no longer reproduces | already fixed by #875, #904 | yes, with a caveat |

---

## #679 — anisotropy-corrected `int_abs`

> after running the anisotropy calculations and the autointerpreter, I attempted
> to save the data to the MagIC tables. Files were saved, but the anisotropy
> corrections were not applied to the int_abs field although the int_corr,
> int_corr_aniso flags were set to 'c'

**Reproduction.** The bug is not merely reproducible, it is *in the repository's
own example data*. `data_files/3_0/Megiddo/specimens.txt` was written by
`pmagpy-3.4.1: thellier_gui.v.3.0` and holds 359 interpretations. Specimen
`hz05a1` records

```
int_abs 9.61E-05      int_corr c
int_corr_anisotropy 0.97      int_corr_cooling_rate 0.95
```

Recomputing that interpretation from the measurements gives an **uncorrected**
estimate of 96.08 µT — that is, `9.61E-05 T` is the *uncorrected* value, while
the row claims to be corrected and supplies the two factors that were never
applied. The corrected value is 96.08 × 0.9668 × 0.9456 = **87.85 µT**, 8.6 %
lower. Across all 359 interpretations the stored `int_abs` matches the
uncorrected estimate to within the file's own three significant figures.

**Current status.** Commit `d15e4266` (January 2023) changed the legacy GUI's
save to write `specimen_int_uT * 1e-6` instead of `specimen_int`, which is the
right fix for the legacy code path. It postdates the Megiddo file, so the
published data still shows the defect, and nothing in the repository tested it.

**Evidence.** `pmagpy/test/test_paleointensity.py::TestAnisotropyCorrectedExport`

* `test_the_published_megiddo_file_shows_the_bug_this_fixes` asserts the defect
  is present in the shipped file, so the regression target cannot be lost.
* `test_int_abs_carries_the_correction_that_int_corr_advertises` checks, for
  every exported specimen, that `int_abs` equals the uncorrected estimate times
  each applied factor, that `int_corr` is `c` exactly when a correction was
  applied and `u` when none was, and that `int_corr_anisotropy` and
  `int_corr_cooling_rate` hold the factors actually used.
* `test_an_uncorrectable_tensor_is_reported_not_silently_applied` checks a
  tensor that failed its alteration check leaves `int_corr = u` with the reason
  visible in the Corrections pane.

**Implementation.** `PintResult` carries `b_anc_uncorrected` and `b_anc`
separately, and each `Correction` records its factor, its MagIC method code, its
source and — when it was *not* applied — why. The export writes `b_anc`, so the
number and the flag cannot disagree. The Corrections pane shows both columns
side by side for every specimen.

**Can it be closed?** Yes. The rewrite exports the corrected value with a test;
the legacy GUI was fixed in 2023. Worth adding to the issue: the published
Megiddo example still contains uncorrected values under a `c` flag, and any
study exported by Thellier GUI before January 2023 may too.

---

## #170 — measurement quality

> Thellier GUI cannot handle data marked bad yet so this function does not work.

**Reproduction.** `programs/thellier_gui.py:1345`:

```python
def on_right_click_listctrl(self, event):
    self.user_warning("Thellier GUI cannot handle data marked bad yet ...")
    return
```

Everything after the `return` is unreachable. Measurements flagged `b` in
`measurements.txt` are read as good.

**What the issue asked for.** Kevin Gaastra's 2017 comment set out the cases,
and Lisa Tauxe's 2019 comment added one more (a study that starts at 500 °C and
so has no NRM step). Each is implemented and tested.

| Case from the issue | Behaviour | Test |
|---|---|---|
| Z or I flagged, a good duplicate at the same treatment exists | the duplicate is used and the point kept | `test_a_good_duplicate_replaces_a_flagged_one` |
| Z or I flagged, no duplicate | the **whole** Arai point is dropped: half a pair cannot define one | `test_flagging_the_in_field_half_removes_the_whole_arai_point`, `test_flagging_the_zero_field_half_removes_the_point_too` |
| pTRM, tail, additivity check flagged | just that check is dropped; the Arai points are untouched | `test_flagging_a_check_drops_the_check_and_nothing_else` |
| NRM flagged | analysis continues; the first good zero-field step normalises | `test_a_flagged_nrm_falls_back_to_the_first_good_zero_field_step` |
| everything flagged | reported, no exception, no result | `test_flagging_everything_is_reported_and_does_not_crash` |
| a bound falls off the end | bounds are clamped to what remains | `test_bounds_are_clamped_when_points_disappear` |
| persistence | written to the `quality` column of `measurements.txt` and read back | `test_flags_round_trip_through_measurements_txt` |

**"Never silently leave an invalid half-pair in a fit."** `build_arai()` is the
only place Arai points are made, and it constructs a point only from a Z/I pair
(or from an antiparallel pair, for the original Thellier–Thellier protocol).
There is no code path that can produce a half-pair. Every drop is appended to
`AraiData.dropped` and shown under the step table, so the analyst sees the
consequence of a flag rather than a silently shorter plot.

**Can it be closed?** Yes for the rewrite. The legacy GUI's handler is
unchanged — the legacy GUI is kept as it is until parity is demonstrated (see
the final report), so the issue should be closed against
`programs/pmagpy_intensity` rather than against `thellier_gui.py`.

---

## #246 — incorrect `dpal`, `dt`, `alpha`, and the statistics UI

Four separate claims. Taken one at a time.

### `dt` (δt\*) reads −999

**Reproduced.** `SPD/spd.py:595`:

```python
def get_delta_t_star(self):
    self.pars['specimen_dt'] = -999.
```

It is grouped under "statistics that require an independent paleointensity
study", alongside `alpha_prime` and `CRM_percent`. **That grouping is wrong.**
SPD v1.2.0 §6 defines δt\* from the NRM vectors, the pTRM tail-check vectors,
the laboratory field direction, `b`, `Y_Int` and `X_Int` — all of which the
experiment already provides. No independent study is needed; the statistic was
simply never implemented. The SPD calibration table publishes a δt\* for every
specimen that has tail checks, which settles the point.

**Fixed.** `pmagpy/pint_stats.py::_delta_t_star` implements the piecewise
definition, including the ThellierTool v4.22 angular limits
(0.175 rad and 2.968 rad) that SPD adopts, and the redefinition of "horizontal"
and "vertical" for a laboratory field along x or y. It reproduces the published
value for every calibration specimen except two, where the *reference
implementation* has an index slip — see `docs/scientific_validation.md`.

It is not applicable rather than −999 when there are no tail checks, when the
tail-check vectors were not recorded, or when the laboratory field is not along
a specimen axis. The panel shows `n/a` with the reason as a tooltip.

**What independent data would be required** — for the statistics that genuinely
need it:

| statistic | what it needs |
|---|---|
| α′ | a characteristic direction measured in a separate demagnetisation experiment, or a known reference direction |
| CRM(%) | the same independent ChRM direction (Coe et al., 1984) |

Both are reported as `unavailable` with that sentence, and both become
computable the moment `Experiment.chrm` is supplied — which the core accepts and
`pmagpy/test/test_pint_stats.py::test_they_become_available_once_a_direction_is_supplied`
checks.

### `dpal` is wrong

**Not reproduced as stated** — but a real ambiguity was found. SPD v1.2.0 §5.3
prints the vector difference as `δpTRM = TRM_l − pTRM check_l`, the opposite way
round from the scalar `δpTRM = check − x` used everywhere else in the document.
Implementing the printed form gives 25.4 for calibration specimen 187A against a
published 41.4; implementing `check − TRM` gives 41.37. The same holds for all
20 specimens. The SPD reference MATLAB and the published table use
`check − TRM`, and so does this implementation, with the discrepancy recorded in
`docs/paleointensity_literature_audit.md`.

`delta_pal` is verified against all 20 calibration specimens
(`test_a_published_statistic_is_reproduced[delta_pal]`).

### `alpha` is wrong (differs from ThellierTool)

**Not reproduced.** α is the angle between the anchored and free-floating
directions. The implementation reproduces the published value for all 20
calibration specimens to within the table's own rounding. If ThellierTool
disagrees it is not because of this code; the value here is SPD-conformant and
independently checked.

### The statistics UI: k and k′ grey out the rest; Windows check-box trouble

Lori Jonestrask reported both fixed in October 2017 (comment on the issue), and
the reporter confirmed the UI problems were gone, leaving only `dt = -999`.
That last symptom is the one addressed above.

The rewrite does not reproduce the *class* of problem: the Criteria & statistics
pane renders every statistic in the catalogue whatever the criteria set
contains, with its value, its pass/fail, its equation, its units and its
citation. Selecting a criterion cannot hide a statistic, because the two are
rendered from the same catalogue rather than from a list the criteria drive.
The browser suite asserts that `FRAC`, `DRAT`, `Ziggie`, `dt*` and `IZZI_MD` are
all present with the curvature criteria active.

**Can it be closed?** Yes, with the note that `dt` is now computed rather than
returning −999, and that `SPD/spd.py` still returns −999 for it — the legacy
module is unchanged, and the new core does not use it.

---

## #818 — `.tdt` files Thellier GUI could not read

> which is the format for a .tdt file in order for ThellierGUI to read it
> properly?

Four files were attached. All four now import; three separate defects were
behind them.

### Defect 1 — the original Thellier–Thellier protocol loses its method codes

`Tdt_no1s.txt` and `dt_w0.txt` use `.1`/`.5` pairs: the original Thellier and
Thellier (1959) protocol, in which each temperature is measured twice with the
laboratory field reversed. There is no zero-field step at all.

`convert_2_magic.tdt` classifies both halves correctly (`LT-T-I`, with the field
direction reversed for `.5`, and the `LP-PI-II` protocol code), and then hands
the records to `pmag.measurements_methods3`, which rebuilds the method codes
from the treatments. That function keys the Thellier protocol on the presence of
`LT-T-Z`; with no zero-field step it recognises nothing and writes **`LT-NO`**
for every row.

Reduced to three records, the failure is exact:

```python
>>> pmag.measurements_methods3([nrm, infield_plus, infield_minus], noave=True)
273. | LT-NO | S_LT-NO
373. | LT-NO | S_LT-NO
373. | LT-NO | S_LT-NO
```

`LT-NO` rows read as a plain demagnetisation experiment — which is exactly why
the reporter's screenshots show Demag GUI opening the data and Thellier GUI
finding nothing.

*Fixed* in `pmagpy/convert_2_magic.py`: a file whose records carry `LP-PI-II`
keeps the codes the converter assigned instead of having them rebuilt. And in
`pmagpy/paleointensity.py`: a temperature measured twice in antiparallel fields
with no zero-field step becomes one Arai point, with
`NRM = (M₁ + M₂)/2` and `pTRM = (M₁ − M₂)/2`. The reporter's specimen gives
B = 27.8 µT over the full range, β = 0.008, FRAC = 0.97.

### Defect 2 — `SPECIMEN.TDT` is silently skipped

`convert_2_magic.tdt` matched `files.endswith(".tdt")`. A file saved with an
upper-case extension — which the SPD calibration set itself contains
(`283A.TDT`) — was skipped without a word. Now matched case-insensitively;
`pmagpy.tdt.find_tdt_files` does the same, and
`test_the_uppercase_extension_is_found` checks it.

### Defect 3 — an unreadable treatment code crashes

`tdt_exp.txt` carries six rows with two-digit codes `440.81`–`440.86` — a
six-position anisotropy block written into the paleointensity file. The old
reader printed

```
-E- ERROR in treatment  440.82
... exiting until you fix the problem
```

and then died with `KeyError: 'method_codes'` several hundred lines later. It
now names the file, the specimen, the measurement and the code, explains what
the code position means, and returns cleanly.

### The import wizard

`pmagpy/tdt.py` is the documented reader the issue asked for, and the *Change
data…* dialog exposes it. `read()` parses without judging; `validate()` returns
one `Issue` per problem with `level`, `line`, `specimen`, `message` and a `hint`
saying what to do; `to_magic()` refuses to write anything while an error stands.
The checks cover the header, the laboratory field and its units, the moment
units and the volume they need, the specimen naming convention, the treatment
sequence, Z/I pairing (and antiparallel pairing for `LP-PI-II`), duplicate
steps, checks at temperatures the experiment never reached, non-monotonic
heating, out-of-range inclinations that betray swapped columns, and anisotropy
records.

The four attachments, after the fixes:

| file | protocol | verdict |
|---|---|---|
| `Tdt_no1s.txt` | Thellier–Thellier | no errors; one note (the specimen is named `THR_14A` in the rows and `Tdt_no1s` by the file) |
| `dt_w0.txt` | Thellier–Thellier | no errors; same note |
| `tdt_exp.txt` | Thellier–Thellier | no errors; **warning**: six steps at 440 °C use two-digit `.8n` codes that look like a six-position anisotropy experiment written into the paleointensity file |
| `tdt_working_fake.txt` | Coe | no errors; note that eleven steps use `.5` (an antiparallel field) beside zero-field steps |

The `.8n` codes are **not** part of the documented format. They are recognised
and reported rather than silently converted; importing them as ATRM positions is
opt-in (`import_anisotropy=True`), because guessing the position order silently
corrupts a correction. With the analyst's confirmation, `tdt_exp` gains an
anisotropy correction of ×1.337.

**Fixtures.** The attachments are a reader's unpublished measurements posted
while asking for help, with no licence. They are **not** redistributed. The
failure modes are reproduced instead by fixtures written inside
`pmagpy/test/test_tdt.py`, and the twenty real `.tdt` files of the SPD
calibration set — published by their authors for exactly this purpose — are
shipped in `data_files/SPD_calibration/TT`.

**Can it be closed?** Yes. The three defects are fixed with tests, the format is
documented in `pmagpy/tdt.py`'s module docstring and in the app's README, and
the reporter's own files import.

---

## #858 — obsolete cookbook links

**Partly.** Nick Swanson-Hysell is working the issue on the
`cookbook_link_updates` branch, which has so far updated `README.md`,
`CONTRIBUTING.md` and one line of `pmagpy/pmag.py`. The Thellier-specific links
the issue lists were still present and are updated here:

| location | was | is |
|---|---|---|
| `programs/thellier_gui.py:9`, `:291` | `earthref.org/PmagPy/cookbook/` | `https://pmagpy.github.io/PmagPy-docs/programs/thellier_gui.html` |
| `programs/thellier_gui.py:309` | `http://earthref.org/PmagPy/cookbook/` | the same page |
| `programs/thellier_gui.py:4747` (Help menu) | `.../cookbook/#x1-560005.1.2` | the same page |
| `programs/thellier_gui.py:4750` (Help menu) | `http://earthref.org/PmagPy/cookbook/` | `https://pmagpy.github.io/PmagPy-docs/` |
| the Help menu item | "PmagPy Cookbook" | "PmagPy documentation" |

Both targets were checked and return 200.

The **new** documentation page the issue asks for is
`programs/pmagpy_intensity/README.md`, which is the user guide and migration
guide for the successor, plus this audit,
`docs/paleointensity_literature_audit.md` and
`docs/scientific_validation.md`.

Left for the other branch: `pmag_gui.py`, `demag_gui.py`, `magic_gui.py`,
`dialogs/`, the `#field_info` anchors in `convert_2_magic.py` and `ipmag.py`
(which have no replacement page yet — option 2 in the issue), and the notebooks.

---

## #789 — removing Data Model 2

> thellier_gui uses Data Model 2 functions (annoyingly). so make sure that
> doesn't break. — @ltauxe

The rewrite removes the reason for the worry: **the new core never touches Data
Model 2**, so retiring the DM2 helpers from `ipmag` cannot break it.

The legacy `thellier_gui.py` reads MagIC 3 and converts to 2.5 internally: it
carries `magic_method_codes`, `measurement_magn_moment`, `er_specimen_name`,
`pmag_specimens` and `specimen_int_uT` throughout, and calls
`map_magic.mapping` with the 3→2.5 maps. The new core carries `method_codes`,
`magn_moment`, `specimen`, `specimens` and `int_abs` — MagIC 3 names from input
through export.

**Guarded by tests** so it stays true:

* `pmagpy/test/test_intensity_environment.py::TestNoLegacyDependency` walks the
  abstract syntax tree of each of the five new modules and fails if any imports
  `builder2`, `validate_upload2`, `controlled_vocabularies2`,
  `convert_2_magic2`, `map_magic` or `SPD`, or calls `upload_magic2`,
  `chi_magic2`, `hysteresis_magic2`, `ani_depthplot2`, `aarm_magic_dm2`,
  `atrm_magic_dm2` or `magic_read_dict`. The application package is scanned too.
* `pmagpy/test/test_paleointensity.py::TestNoDataModel2` additionally fails if a
  2.5 *column name* appears as a string literal anywhere in the new core, and if
  a loaded contribution ever builds an `er_`, `pmag_` or `rmag_` table.
* `test_the_core_does_not_need_the_legacy_spd_package` imports the whole core in
  a fresh interpreter with `past` and `future` blocked at the meta-path, and
  passes.

**Can it be closed?** Not by this work — the issue is about `ipmag.py`, which
this branch does not change. What this branch supplies is the answer to the
blocker in the thread: the paleointensity successor has no DM2 dependency, and a
test will fail if one is introduced. The `ipmag` clean-up can proceed.

---

## #769 — pmag_gui does not respond

A long thread with three distinct problems.

### The original traceback

```
File ".../SPD/spd.py", line 22, in <module>
    from past.utils import old_div
ModuleNotFoundError: No module named 'past'
```

`pmagpy/pmag.py` imports `SPD.lib.leastsq_jacobian` at module level, which
executes `SPD/__init__.py`, which imports `SPD.spd`. `past` comes from the
`future` package and is **not** in `install_requires`.

**No longer reproduces.** `SPD/spd.py` line 22 now reads
`from builtins import object`; the `past` import is gone from the whole
repository. Verified by importing the entire new core with `past` and `future`
blocked at the meta-path.

### `dia_vgp` producing a blank file

Fixed by @apivarunas in the commit referenced in the thread. Outside this
rewrite's scope; a separate program.

### pmagpy and pmagpy-cli out of sync

> Basically, `pmagpy` and `pmagpy-cli` get out of sync, and then the programs
> don't work as intended. — @apivarunas, August 2026

Fixed by PR #904, which makes `pmagpy-cli` pin `pmagpy==<exact version>` built
from the shared version string, with `pmagpy/test/test_packaging.py` guarding
it. PR #875 fixed the Thellier GUI failure the reporter hit after that.

### Clean-environment launch tests

`pmagpy/test/test_intensity_environment.py`, 23 tests. Each new module imports
in a fresh interpreter; nothing outside `setup.py`'s `install_requires` is
*required* — whatever an installed environment happens to pull in (pandas
reaches for `pyarrow`, and pmagpy's own `pmag_env` asks IPython whether it is
running in a notebook) is discovered, blocked at the meta-path, and the core
still imports and computes without it; an end-to-end analysis runs in a
subprocess; statistics compute with a deliberately broken matplotlib backend,
so a headless machine never needs a display to analyse data.

**Verified for real on macOS arm64**: a fresh `python -m venv`, `pip install -e .`,
then — run from `/tmp`, outside the repository — all five modules import, a
Megiddo-format study loads and is interpreted, the twenty calibration `.tdt`
files read and validate, and BiCEP runs. Adding `panel` and `bokeh`,
`programs/pmagpy_intensity/launch.py --port 5199 --no-show` serves the
application and it answers HTTP 200.

**Can it be closed? Yes, with a caveat.** Everything the thread reports is
fixed, and there are now tests that would catch each of them coming back. The
caveat is honest: **the clean-environment verification was run on macOS arm64
only.** No Windows or Linux machine was available in this environment. The tests
are written to be platform-independent (subprocess imports and source scans, no
compiled artefacts) and should be run in CI on all three before the issue is
closed. See "Remaining risks" in the final report.

---

## What each issue would need to be reopened

| Issue | The regression test that would fail |
|---|---|
| #679 | `TestAnisotropyCorrectedExport::test_int_abs_carries_the_correction_that_int_corr_advertises` |
| #170 | any of the eight tests in `TestMeasurementQuality` |
| #246 | `TestSpdCalibration::test_a_published_statistic_is_reproduced[delta_pal]`, `test_delta_t_star_matches_except_where_the_reference_code_slips`, and the browser check that the statistics panel lists `dt*` |
| #818 | `test_tdt.py::TestConversion::test_the_thellier_thellier_pair_becomes_one_arai_point`, `test_the_uppercase_extension_is_found`, `test_conversion_stops_on_an_error_unless_told_otherwise` |
| #858 | no automated test; the links are checked by hand and recorded above |
| #789 | `TestNoLegacyDependency` (five modules × two scans) and `TestNoDataModel2` |
| #769 | the 23 tests in `test_intensity_environment.py`, and `test_packaging.py` |
