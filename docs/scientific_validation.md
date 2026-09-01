# Scientific validation

Every number PmagPy Intensity produces, checked against a published one, with
the deltas.

Three reference sets are used, and each answers a different question.

| set | what it proves | where |
|---|---|---|
| **SPD v1.2.0 calibration**, 20 specimens, 48 statistics each | the statistics are computed as the standard defines them | `data_files/SPD_calibration` |
| **Megiddo**, 359 published interpretations | a real study re-analysed reproduces what the legacy Thellier GUI wrote | `data_files/3_0/Megiddo` |
| **synthetic known-answer sites** | BiCEP recovers a field it was given | `pmagpy/test/test_bicep.py` |

Everything below is reproduced by the test suite; nothing here is hand-copied.

```bash
pytest pmagpy/test/test_pint_stats.py pmagpy/test/test_paleointensity.py \
       pmagpy/test/test_tdt.py pmagpy/test/test_bicep.py \
       pmagpy/test/test_intensity_environment.py -q
```

---

## 1. The SPD v1.2.0 calibration set

### What it is and where it came from

Twenty paleointensity specimens from twelve studies and fifteen localities,
published by Paterson et al. alongside the *Standard Paleointensity
Definitions* so that different software can be calibrated against each other:

> To be able to test and calibrate the calculation of paleointensity data
> across multiple platforms and software bases, we have provided a data set of
> 20 paleointensity specimens with which users can test their software.
> — SPD v1.2.0 §11

Downloaded from <https://earthref.org/PmagPy/SPD/downloads.html> on
1 September 2026 and shipped in `data_files/SPD_calibration`:

| file | what |
|---|---|
| `TT/*.tdt` (20) | the measurements, ThellierTool format |
| `SPD_reference_statistics.csv` | the published value of 48 statistics for each specimen, with the best-fit segment used |
| `SPD_reference_averages.csv` | the site-level averages of SPD Table 2 |
| `SPD_B_Lab.dat` | the laboratory field strength and direction |
| `SPD_Anis_Tensors.dat` | the six tensor elements for the four anisotropic specimens |
| `SPD_NLT_factors.dat` | A₁ and A₂ for the three non-linear specimens |

### How the comparison is run

Through the **whole pipeline**, not just the arithmetic: each `.tdt` file is
read by `pmagpy.tdt`, written as MagIC 3 tables, loaded by
`pmagpy.paleointensity.PintData`, given the published `Tmin`/`Tmax` as bounds,
and its statistics compared. A defect anywhere from the file reader to the
statistic would show up.

### Results

Δ is |ours − published|. The published table reports to 1 or 3 decimal places
depending on the statistic, so a Δ at or below half of the last published digit
means agreement to the precision the table carries.

| statistic | n | max Δ | median Δ | published to |
|---|---|---|---|---|
| `n`, `n_pTRM`, `n_tail`, `n_add` | 20, 20, 20, 2 | **0** | 0 | integer |
| `b` | 20 | 0.00048 | 0.00025 | 3 d.p. |
| `σ_b` | 20 | 0.00049 | 0.00028 | 3 d.p. |
| `f` | 20 | 0.00050 | 0.00022 | 3 d.p. |
| `f_vds` | 20 | 0.00044 | 0.00027 | 3 d.p. |
| `FRAC` | 20 | 0.00048 | 0.00027 | 3 d.p. |
| `β` | 20 | 0.00048 | 0.00025 | 3 d.p. |
| `g` | 20 | 0.00049 | 0.00022 | 3 d.p. |
| `GAP-MAX` | 20 | 0.00050 | 0.00037 | 3 d.p. |
| `q` | 20 | 0.048 | 0.018 | 1 d.p. |
| `w` | 20 | 0.047 | 0.024 | 1 d.p. |
| `k` | 20 | 0.00048 | 0.00030 | 3 d.p. |
| `k′` | 20 | 0.00049 | 0.00028 | 3 d.p. |
| `SSE` | 20 | 0.00049 | 0.00027 | 3 d.p. |
| `R²_corr` | 20 | 0.00049 | 0.00023 | 3 d.p. |
| `R²_det` | 20 | 0.00050 | 0.00026 | 3 d.p. |
| `Z` | 20 | 0.050 | 0.021 | 1 d.p. |
| `Z*` | 20 | 0.048 | 0.024 | 1 d.p. |
| `IZZI_MD` | 3 | 0.00042 | 0.00039 | 3 d.p. |
| `SCAT` (β<sub>threshold</sub> = 0.1) | 20 | **exact**, 20/20 | — | boolean |
| `Dec_Anc`, `Inc_Anc`, `MAD_Anc` | 20 | 0.048, 0.046, 0.048 | 0.031, 0.011, 0.031 | 1 d.p. |
| `Dec_Free`, `Inc_Free`, `MAD_Free` | 20 | 0.049, 0.049, 0.049 | 0.024, 0.029, 0.024 | 1 d.p. |
| `α` | 20 | 0.048 | 0.026 | 1 d.p. |
| `DANG` | 20 | 0.046 | 0.025 | 1 d.p. |
| `NRM_dev` | 20 | 0.045 | 0.018 | 1 d.p. |
| `θ` | 20 | 0.049 | 0.030 | 1 d.p. |
| `γ` | 20 | 0.049 | 0.031 | 1 d.p. |
| `check(%)` | 19 | 0.049 | 0.028 | 1 d.p. |
| `δCK` | 19 | 0.045 | 0.034 | 1 d.p. |
| `DRAT` | 19 | 0.049 | 0.039 | 1 d.p. |
| `maxDEV` | 19 | 0.050 | 0.021 | 1 d.p. |
| `CDRAT`, `CDRAT′` | 19 | 0.044, 0.045 | 0.023, 0.021 | 1 d.p. |
| `DRATS`, `DRATS′` | 19 | 0.048, 0.047 | 0.031, 0.023 | 1 d.p. |
| `mean DRAT`, `mean DRAT′` | 19 | 0.049, 0.049 | 0.026, 0.034 | 1 d.p. |
| `mean DEV`, `mean DEV′` | 19 | 0.048, 0.049 | 0.026, 0.032 | 1 d.p. |
| `δpal` | 19 | 0.048 | 0.021 | 1 d.p. |
| `DRAT_tail` | 11 | 0.048 | 0.033 | 1 d.p. |
| `δTR` | 11 | 0.047 | 0.023 | 1 d.p. |
| `MD_VDS` | 11 | 0.047 | 0.025 | 1 d.p. |
| `δt*` | 11 | **1.169** — see §1.2 | 0.029 | 1 d.p. |
| `δAC` | 2 | 0.050 | 0.041 | 1 d.p. |

**Every statistic reported to 3 decimal places agrees to within 5×10⁻⁴, and
every statistic reported to 1 decimal place agrees to within 0.05** — that is,
to the last digit the published table carries — with the single documented
exception below.

`IZZI_MD` is compared for the three IZZI specimens only, because the
application reports it as *not applicable* for a Coe-protocol experiment: it
measures IZ/ZI alternation, and there is none. The bare
`pint_stats.izzi_md()` function does compute the SPD-compatible value for all
17 non-IZZI specimens as well, and matches; the gate is a presentation choice,
recorded here so a reader is not surprised.

### 1.1 The corrections

`c` is the anisotropy correction factor; `BAnc` is the published intensity,
which for these four specimens is corrected.

| specimen | published `c` | ours | published `BAnc` | ours, corrected |
|---|---|---|---|---|
| m428b1 | 0.6730 | 0.6726 | 25.1 µT | 25.10 µT |
| RS25b | 1.0010 | 1.0007 | 29.3 µT | 29.28 µT |
| RS26a | 1.0060 | 1.0062 | 63.2 µT | 63.24 µT |
| RS26e | 1.0750 | 1.0745 | 58.1 µT | 58.13 µT |

RS25b, RS26a and RS26e additionally carry the non-linear TRM correction;
`B_anc = atanh(c·|b|·tanh(A₂·B_lab)) / A₂` (SPD §9.2) with the published A₂.
For the sixteen uncorrected specimens the plain `B_anc = |b|·B_lab` matches the
published value to 0.15 µT.

**A unit trap worth recording:** SPD publishes `A₂` per *microtesla*
(0.0008164 for RS25b). The core works in tesla, so `A₂` must be multiplied by
10⁶ before it is used with a field in tesla. Getting this wrong makes the
correction vanish (`tanh` of a very small number is linear) rather than fail
loudly.

### 1.2 The two differences, and why they are the reference's

Both are in `δt*`, and both affect only specimens whose laboratory field lies
along the **x** axis.

| specimen | B_lab | published `δt*` | ours | agreement with SPD.m's own code |
|---|---|---|---|---|
| HEL2-2d | +x | 0.0 | **1.169** | SPD.m gives 0.00 |
| TS01-20A-2 | +x (see below) | 2.9 | **2.247** | SPD.m gives 2.89 |
| BR06-4F | +x | 0.0 | 0.00 | 0.00 — the two agree here |
| everything else | ±z | matches to 0.05 | | |

SPD v1.2.0 §6 says that when `B_lab` lies along **x**, "horizontal" and
"vertical" are redefined so that the field is vertical:

> δH_i = √(N²_y,i + N²_z,i) − √(T²_y,i + T²_z,i),  δZ_i = N_x,i − T_x,i

The reference implementation `SPD.m` writes that branch as

```matlab
dH = sqrt(sum(NRMvec(j,2:3).^2)) - sqrt(MDy^2 + MDz^2);
```

`NRMvec(j,2:3)` is (x, y) — the *original* horizontal plane — while the tail
term uses (y, z), the redefined one. The two halves of the difference are taken
in different planes. Implementing the document's equation gives 1.169 and 2.247;
implementing SPD.m's index slip reproduces the published 0.00 and 2.89 exactly.
That is asserted directly in the test suite, so if the reference is corrected
the difference will be visible rather than silently absorbed.

**Decision.** The document's equation is implemented, because it is the one that
is physically meaningful. The two published values are treated as known
differences with the reason above.

### 1.3 Two defects in the calibration set's own auxiliary file

Found while reproducing `θ` and `γ`, and worked around with the values recorded
in the test file.

| specimen | `SPD_B_Lab.dat` says | the published statistics require |
|---|---|---|
| MCT | `0 0 1` (+z) | **−z**: with +z, θ = 12.6° and γ = 5.4°; the table gives 167.4° and 174.6°, and −z reproduces both exactly, and δt\* = 30.0 with it |
| TS01-20A-2 | `0 0 0` — a zero vector, no direction at all | **+x**: gives θ = 76.2° and γ = 8.7°, both as published |

Neither can be right as published: a zero vector has no direction, and MCT's
sign is contradicted by two independent statistics. These are reported here so
that the next person calibrating software against this set does not spend the
afternoon we did.

### 1.4 The group statistics

SPD v1.2.0 Table 2, the averages of the twenty:

| | published | ours |
|---|---|---|
| N | 20 | 20 |
| m | 49.4 µT | 49.41 |
| s | 24.2 µT | 24.17 |
| δB(%) | 48.9 | 48.91 |
| δB_N(%) | 66.3 | 66.06 |

δB_N requires the noncentral-t quantile; the implementation here is a Lenth
(1989) series with an incomplete-beta continued fraction, and it reproduces
SPD's own worked value (−1.193 for ν = 1, δ = 1 at the 5 % level) to 0.02.

---

## 2. Megiddo: 359 published interpretations

### What it is

`data_files/3_0/Megiddo` is an archaeomagnetic study of 590 specimens, all
IZZI, with ATRM and AARM anisotropy, TRM-acquisition and cooling-rate
experiments. Its `specimens.txt` carries 359 interpretations stamped
`software_packages = pmagpy-3.4.1: thellier_gui.v.3.0` — written by the legacy
Thellier GUI this application replaces. Re-importing their bounds and
recomputing is the regression test that the rewrite reproduces the program it
succeeds.

### Results, all 359 specimens

| published column | statistic | n | max Δ | median Δ | outside the file's own rounding |
|---|---|---|---|---|---|
| `int_abs` (as the **uncorrected** estimate) | `B_anc` | 359 | 4.9×10⁻⁷ T (0.49 µT) | 2.7×10⁻⁸ T | **0** |
| `int_b_beta` | β | 359 | 0.0050 | 0.0024 | **0** |
| `int_f` | f | 359 | 0.0050 | 0.0026 | **0** |
| `int_fvds` | f_vds | 359 | 0.0052 | 0.0025 | **0** |
| `int_g` | g | 359 | 0.0050 | 0.0026 | **0** |
| `int_q` | q | 359 | 0.0050 | 0.0025 | **0** |
| `int_n_measurements` | n | 359 | **0** | 0 | **0** |
| `int_drats` | DRATS | 359 | 0.221 | 0.0025 | 1 |
| `int_mad_free` | MAD_Free | 359 | 0.239 | 0.0028 | 1 |
| `int_dang` | DANG | 359 | 1.15 | 0.0023 | 1 |
| `int_n_ptrm` | n_pTRM | 359 | 1 | 0 | 1 |
| `int_corr_cooling_rate` | cooling-rate factor | 353 | 0.0050 | 0.0024 | **0** |
| `int_corr_anisotropy` | anisotropy factor | 315 | 0.156 | 0.0024 | 7 |

The published file stores these to two decimal places, so a Δ of 0.005 is
exact agreement. **Every specimen agrees on n, the intensity, β, f, f_vds, g
and q, and every cooling-rate factor agrees.**

### 2.1 The one specimen that differs, and what it taught us

`mgk09t1PI01` has, at 623 K, a zero-field step with **no in-field step**. The
first version of this core made an Arai point of it at x = 0, which dragged the
fit: n = 12 against the published 11, and β 0.10 against 0.04.

That was our defect, and it is fixed: a zero-field step whose temperature was
never measured in field has no pTRM to plot against and is not an Arai point at
all. Only the NRM legitimately sits at x = 0. The drop is reported under the
step table ("350 °C: a zero-field step with no in-field step, so there is no
pTRM to plot it against"), and the specimen now reproduces n = 11 and its
intensity, β, f, g and q exactly.

Four residuals remain on this one specimen:

| | published | ours | why |
|---|---|---|---|
| `n_pTRM` | 3 | 4 | the specimen has five pTRM checks; the one to 623 K is correctly skipped because that temperature has no Arai point, leaving four with both temperatures ≤ T_max. Which fourth the legacy GUI dropped is not recoverable from the file |
| `DRATS` | 2.34 | 2.12 | follows from the check count |
| `MAD_Free` | 4.97 | 4.73 | SPD §4 defines the direction "over the same range of points used for the paleointensity estimates". The 623 K zero-field direction is not one of those points, so it is excluded; the legacy GUI's PCA block is built from all zero-field steps regardless of pairing |
| `DANG` | 5.63 | 4.48 | the same one direction |

We believe the SPD-conformant reading is the right one, and say so rather than
matching the legacy behaviour for its own sake.

### 2.2 The seven anisotropy factors that differ

315 of 322 anisotropy factors agree to the file's rounding. The seven that do
not fall into two groups.

**Three (hz05h4, hz05h5, hz15b2)** where the published factor is exactly 1.00 —
the legacy GUI applied no correction — while we compute one. hz15b2's tensor
fails Hext's F-test (F = 2.8 against a critical 3.11); hz05h4 altered by 4.8 %
and hz05h5 by 2.9 %, both under the 5 % limit. The legacy GUI's rejection rule
is driven by criteria the study set interactively and did not record in
`criteria.txt`, so it cannot be reconstructed from the files.

**Two (mgk06d03, mgk08e03)** where both an ATRM and an AARM tensor exist. This
application prefers AARM, as the legacy GUI's own code comment says it does;
its selection logic contains a no-op comparison (`TYPE=='AARM'` where an
assignment was meant), so which tensor it actually used in a given run is not
determinable from the source.

**Two (mgh07e01, mgh09k04)** where the recomputed tensor itself differs slightly
from the stored `aniso_s` — see below.

Rather than reverse-engineer an unrecorded rule, this application makes the
policy explicit and visible: **the alteration limit is a setting** (5 % by
default, the widely used value and the one Megiddo's rejections are consistent
with), **Hext's F-test is an optional gate**, and **AARM is preferred over ATRM
when both exist**, all stated on the Corrections pane along with the reason a
tensor was not applied.

### 2.3 The anisotropy tensors themselves

Independently of which tensor is *applied*, the tensors are *recomputed* from
the six-position measurements and compared with the `aniso_s` the study
published: **451 of 466 agree to better than 2×10⁻⁴**, twelve differ by
0.005–0.03 and one (mgh03h07) by 0.66. Reproducing them at all requires
subtracting the zero-field baseline from every position, which is what the
legacy GUI does and what a naive fit omits — omitting it moved 68 correction
factors.

---

## 3. Issue #679 in the wild

The Megiddo file is itself the evidence for the anisotropy-export bug. For
`hz05a1`:

| | |
|---|---|
| stored `int_abs` | 9.61×10⁻⁵ T = 96.1 µT |
| stored `int_corr` | `c` — corrected |
| stored `int_corr_anisotropy` | 0.97 |
| stored `int_corr_cooling_rate` | 0.95 |
| our **uncorrected** estimate | 96.08 µT — the stored value |
| our **corrected** estimate | 87.85 µT |

The stored value is the uncorrected one under a flag that says otherwise, an
8.6 % overestimate. The same holds across all 359 rows. This is asserted as a
property of the shipped file
(`test_the_published_megiddo_file_shows_the_bug_this_fixes`) so the regression
target cannot be lost, and the export is asserted to be self-consistent for
every specimen.

---

## 4. BiCEP

### Known-answer synthetic sites

Sites are built so the assumption BiCEP rests on is exactly true: specimen
intensity is `truth − slope × |k|`, with Gaussian noise on the Arai points.

| site | true field | recovered | 95 % credible | R-hat | ESS |
|---|---|---|---|---|---|
| 5 specimens, k from 0 to 0.30 | 45.0 µT | **45.2** | 44.7–46.0 | 1.005 | 7 972 |
| 4 specimens, no curvature | 52.0 µT | **52.0** | — | converged | — |
| 5 specimens, B_lab 50 µT | 70.0 µT | **70.0** | — | converged | — |
| 20 specimens, random k | 52.0 µT | **52.7** | 52.2–53.3 | 1.018 | 70 |

The same seed gives the same draws to the last bit; different seeds agree to
better than 1.5 µT.

### A real site

Megiddo hz05, 38 specimens, in the application:

| | |
|---|---|
| classical site mean of the accepted specimens | 75.7 ± 7.7 µT (N = 38) |
| BiCEP | **78.8 µT**, 95 % credible 76.3–81.2 |
| slope | −26.6 µT per unit k |
| diagnostics | R-hat 1.004, ESS 718, 0 divergences, 8 000 draws |
| posterior predictive | RMS residual 6.38 µT, R² 0.157 |
| time | 10.0 s |

### What is *not* validated

The published BiCEP examples (`example_magic_files` in the reference GUI
repository) are **not** used, because that repository's licence is
self-contradictory — CC BY-SA 4.0 in the repository, MIT in the package
metadata — and redistributing its data into PmagPy would inherit the problem.
Validating against the paper's 30-site compilation would be the strongest
possible check and is recommended as follow-up; it needs those MagIC files or
their MagIC-database equivalents. This is listed under remaining risks.

---

## 5. ThellierTool import

| check | result |
|---|---|
| all 20 calibration `.tdt` files parse | no parse errors |
| all 20 validate | no errors; notes only |
| protocols recognised | RS25b, RS26a, RS26e as IZZI; the rest Coe/Aitken — as SPD Table 1 records |
| statistics after the round trip | identical to §1, so nothing is lost between the `.tdt` file and the analysis |

A precision trap found here: writing `dir_dec` and `dir_inc` to one decimal
place — as the legacy converter does — moves the small vector differences the
pTRM-check statistics are built from, and `CDRAT`, `check(%)` and `δpal` drift
by several percent. The reader now writes the precision the file carried.

---

## 6. Reproducing all of this

```bash
# the core suites (no Panel needed)
pytest pmagpy/test/test_pint_stats.py -q            #  69 tests
pytest pmagpy/test/test_paleointensity.py -q        # 116 tests
pytest pmagpy/test/test_tdt.py -q                   #  37 tests
pytest pmagpy/test/test_bicep.py -q                 #  34 tests
pytest pmagpy/test/test_intensity_environment.py -q #  23 tests

# the application (needs panel and bokeh)
pytest programs/pmagpy_intensity/test_app.py -q     #  60 tests
pytest programs/pmagpy_panel/test_chooser.py -q     #  14 tests

# the browser suite (needs playwright)
python programs/pmagpy_intensity/launch.py --port 5101 --no-show &
python programs/pmagpy_intensity/ui_test.py http://localhost:5101/pmagpy_intensity screenshots/app
```

The numbers in this document come from those tests; the per-statistic tables in
§1 and §2 were produced by the same comparison the tests run, printed rather
than asserted.
