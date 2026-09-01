# Paleointensity literature audit

What the statistics panel of PmagPy Intensity implements, why, and what it
deliberately does not.

---

## 1. How the search was done

**Search date:** 1 September 2026. Everything below reflects the literature as
of that date.

### Databases and exact queries

| Source | Query | Result |
|---|---|---|
| earthref.org/PmagPy/SPD | downloaded `SPD_v1.2.0.pdf`, `SPD_v1.1.pdf`, `SPD_v1.0.pdf`, `SPD_Test_data.zip`, `SPD_Example_Code.zip`, `SPD_Test_Data_Table.xlsx`, `AraiCurvature.zip` | the current standard, its version history, its reference MATLAB implementation, and its 20-specimen calibration set with published statistics |
| Crossref REST | `api.crossref.org/works/10.1029/2025JB031608` and the other baseline DOIs | canonical citation, licence, issue and page for each |
| OpenAlex | `works?filter=cites:W2148016566,from_publication_date:2014-01-01` — every work citing Paterson et al. (2014) | 231 citing works; 39 methodological after keyword filtering on `select\|criteri\|statistic\|curvature\|zig\|Arai\|protocol\|IZZI\|Thellier\|bias\|uncertaint\|domain\|tail\|anisotrop\|non-linear\|cooling rate\|software\|BiCEP\|Bayes\|machine learn\|neural\|automat\|correction\|validation\|reproduc\|calibrat\|standard` |
| OpenAlex | ten free-text searches from 2014: *paleointensity selection criteria*; *palaeointensity selection statistic*; *Thellier paleointensity software*; *Arai plot curvature*; *paleointensity uncertainty Bayesian*; *archaeointensity anisotropy correction TRM*; *cooling rate correction paleointensity*; *non-linear TRM paleointensity correction*; *paleointensity multidomain tail check*; *paleointensity machine learning selection* | 288 unique works, 109 subject-relevant |
| Web search | *Ziggie statistic paleointensity Tully Paterson code github*; *CCRIT selection criteria Cromwell 2015*; *ThellierTool Leonhardt 2004 class A class B criteria*; *ThellierTool tdt file format treatment code anisotropy* | reference implementations, criteria tables |
| GitHub | `search/repositories q=Ziggie paleointensity`; `repos/bcych/BiCEP_GUI` | the reference implementations and their licences |
| Full text | AGU (Wiley), EarthArXiv/eScholarship, University of Liverpool repository | equations and thresholds read from the papers themselves, not from abstracts |

Publication years covered: **2014 through 1 September 2026**. Nothing was taken
from memory: every equation implemented here was read from the source named
beside it, and every threshold from the table it is published in.

### What "reference implementation" means below

Where a reference implementation exists it was read to *check numbers*, not
copied. Two carry licence problems, recorded in §5.

---

## 2. The authoritative baseline

| # | Work | DOI | Role here |
|---|---|---|---|
| 1 | Paterson, G. A., L. Tauxe, A. J. Biggin, R. Shaar & L. C. Jonestrask (2014), On improving the selection of Thellier-type paleointensity data, *G-cubed* **15**, 1180–1192 | [10.1002/2013GC005135](https://doi.org/10.1002/2013GC005135) | the framework; Table 2 supplies PICRIT03, SELCRIT2, TTA, TTB and their modified forms |
| 2 | *Standard Paleointensity Definitions* v1.2.0, February 2021 | <https://earthref.org/PmagPy/SPD/DL/SPD_v1.2.0.pdf> | the definitions implemented, section by section |
| 3 | Paterson, G. A. (2011), A simple test for the presence of multidomain behaviour during paleointensity experiments, *JGR* **116**, B10104 | [10.1029/2011JB008369](https://doi.org/10.1029/2011JB008369) | curvature *k*, its circle fit, and the two published thresholds |
| 4 | Tauxe, L., C. N. Santos, B. Cych, X. Zhao, A. P. Roberts & L. Nagy (2021), Understanding nonideal paleointensity recording in igneous rocks … "fragile" curvature in Arai plots, *G-cubed* **22**, e2020GC009423 | [10.1029/2020GC009423](https://doi.org/10.1029/2020GC009423) | why curvature must be reported and why no threshold is universal |
| 5 | Tully, A. W. & G. A. Paterson (2025), Another simple test for the presence of multidomain behavior during paleointensity experiments, *JGR Solid Earth* **130**, e2025JB031608 | [10.1029/2025JB031608](https://doi.org/10.1029/2025JB031608) | Ziggie |
| 6 | Béguin, A., G. A. Paterson, A. J. Biggin & L. V. de Groot (2020), Paleointensity.org: an online, open source application for the interpretation of paleointensity data, *G-cubed* **21**, e2019GC008791 | [10.1029/2019GC008791](https://doi.org/10.1029/2019GC008791) | the other SPD-conformant application; a cross-check target |
| 7 | Cych, B., M. Morzfeld & L. Tauxe (2021), Bias Corrected Estimation of Paleointensity (BiCEP), *G-cubed* **22**, e2021GC009755 | [10.1029/2021GC009755](https://doi.org/10.1029/2021GC009755) | the BiCEP panel |

Note on #4: OpenAlex and Crossref give the publication year as 2020 (online) in
the *G-cubed* volume 22 issue dated January 2021. It is cited here as
Tauxe et al. (2021) to match the issue, with the DOI given.

---

## 3. SPD v1.2.0 coverage

The task set was **full SPD v1.2.0 coverage, or a scientifically justified
reason for each omission.** Coverage by section:

### §3 Arai plot — complete

`n`, `n_max`, `T_min`, `T_max`, `b`, `σ_b`, `B_anc`, `σ_B`, `Y_Int`, `X_Int`,
`VDS`, `x′`/`y′`, `Δx′`, `Δy′`, `f`, `f_vds`, `FRAC`, `β`, `g`, `g_lim`,
`GAP-MAX`, `q`, `w`, `k`, `k′`, `SSE`, `SCAT`, `R²_corr`, `R²_det`, `Z`, `Z*`,
`S`, `S′`, `pχ²`, `IZZI_MD`.

Three of these are **new in v1.2** and were absent from every PmagPy code path:

* **σ_b corrected to use `b` and not `|b|`** (v1.2 change 1).
  `σ_b = √[(2·Σ(y−ȳ)² − 2b·Σ(x−x̄)(y−ȳ)) / ((n−2)·Σ(x−x̄)²)]`.
  Tested against a hand evaluation of the printed equation, and against the
  wrong `|b|` form, which it must *not* equal
  (`test_sigma_b_follows_spd_v1_2_and_uses_b_not_its_modulus`).
* **`Pck`** (v1.2 change 3; Carvallo et al., 2004,
  [10.1029/2003GC000638](https://doi.org/10.1029/2003GC000638)):
  `Pck = 100·max|δpTRM| / x_end`. Implemented, verified on all 20 calibration
  specimens.
* **`S`, `S′` and `pχ²`** (v1.2 change 4; York, 1966; Yu et al., 2000).
  Implemented — with a caveat, see §6.

### §4 Directional — complete, two need outside data

`Dec_Free`, `Inc_Free`, `MAD_Free`, `Dec_Anc`, `Inc_Anc`, `MAD_Anc`, `α`, `θ`,
`DANG`, `NRM_dev`, `γ`, and `α′`, `CRM(%)` which need an independently measured
characteristic direction. Those two are reported as **unavailable** with the
sentence saying what is missing, and compute as soon as
`Experiment.chrm` is supplied.

### §5 pTRM checks — complete

`n_pTRM`, `check(%)`, `δCK`, `DRAT`, `maxDEV`, `Pck`, `CDRAT`, `CDRAT′`,
`DRATS`, `DRATS′`, `mean DRAT`, `mean DRAT′`, `mean DEV`, `mean DEV′`, `δpal`.

### §6 pTRM tail checks — complete

`n_tail`, `DRAT_tail`, `δTR`, `MD_VDS`, **`δt*`**. The last was `-999` in every
PmagPy code path; see the issue audit for #246.

### §7 Additivity — complete

`n_add`, `δAC`.

### §8 Anisotropic TRM — complete

The corrected design matrix (v1.2 change 2: row 6's last two elements are
`P2,2` and `P2,1`, not `P3,3` and `P3,1`) is implemented and asserted directly
in `test_the_design_matrix_matches_spd_v1_2`. The tensor is fitted from the
six-position ATRM or the 6-, 9- or 15-position AARM block; the correction factor
follows Veitch et al. (1984) as SPD recommends over Selkin et al. (2000);
`δTRM_anis` is the alteration check; Hext's σ, F, F₁₂ and F₂₃ with the F
critical value are reported.

### §9 Non-linear TRM — complete

`TRM = A₁·tanh(A₂·B)` fitted from the `LP-TRM` acquisition block; the combined
anisotropy-and-non-linearity correction of §9.2,
`B_anc = atanh(c·|b|·tanh(A₂·B_lab)) / A₂`; `δTRM_NLT`.

### §10 Multiple estimates — complete

`N`, `m`, `s`, `m_w`, `s_w`, `δB(%)`, `δB_N(%)`, `pδB`, `p_s`. The noncentral-t
and χ² distributions are implemented directly (Lenth, 1989 series; continued
fractions) so the core has no SciPy dependency for them; verified against the
value SPD's own numerical tip quotes (−1.193) and against the published
`δB_N = 66.3 %` for the 20-specimen set.

### §11 Calibration data set — shipped

`data_files/SPD_calibration`. See `docs/scientific_validation.md`.

### Omissions

**None.** Every statistic defined in SPD v1.2.0 is implemented. Two (`α′`,
`CRM(%)`) require data the paleointensity experiment does not itself produce and
are reported as unavailable until it is supplied; that is the definition's
property, not an omission.

---

## 4. Post-2014 work assessed

Ordered by what was decided.

### 4.1 Implemented now

#### Ziggie — Tully & Paterson (2025)

* **DOI** [10.1029/2025JB031608](https://doi.org/10.1029/2025JB031608), *JGR
  Solid Earth* 130, e2025JB031608, CC BY 4.0.
* **What it is.** A statistic specific to Arai-plot zig-zag:
  `Ziggie = ln(cumulative line length / length of the best-fit arc)`, both
  measured over the selected segment after normalising x by its own maximum and
  y by its own maximum. The arc uses the same circle fit as `k′`; when
  `1/|k′| ≥ 1000` the data are better described by a line and the length of the
  best-fit line is used instead, which also keeps the arc length numerically
  stable. Zero for a perfectly straight monotonic segment; grows with zig-zag.
* **Proposed threshold.** `Ziggie ≤ 0.1`, from the paper's §2.2. The SD
  simulations put the *lower* usable bound at 0.061 and the MD simulations the
  *upper* at 0.255, so 0.1 sits inside the window; it corresponds to a segment
  about 10 % longer than its best-fit arc.
* **Calibration domain.** IZZI experiments. The paper's Data Sets 2 and 3 are
  50 000 SD and 50 000 MD simulations with the ancient and laboratory fields of
  equal strength; the real-data test is 201 specimens from 16 known-field sites
  (Cromwell & Zhang 2021; Paterson et al. 2010; Santos & Tauxe 2019; Shaar
  et al. 2010, 2011).
* **Interactions.** The paper is explicit: *Ziggie cannot detect curvature*
  (the arc absorbs it), so it must be used **with** `k′`. It has negligible
  curvature dependence — which is the point — and is invariant to scaling both
  axes, which `IZZI_MD` is not.
* **Limitations.** It can be slightly negative when the circle fit is poor;
  the RMS misfit of that fit is reported alongside so the reader can see why.
  When the data fit neither a line nor a circle, Ziggie cannot quantify the
  zig-zag — and, as the paper says, such data are unlikely to be usable at all.
* **Reference software.** <https://github.com/ATully98/Ziggie>, Zenodo
  [10.5281/zenodo.12887405](https://doi.org/10.5281/zenodo.12887405).
  **The repository carries a `CITATION.cff` but no licence file** — see §5.
* **Decision: implement now**, as an opt-in criterion (`Ziggie ≤ 0.1`) that can
  be added to any preset, off by default, with the citation shown in the panel
  and carried into the export's citation block.
* **Tests.** `test_pint_stats.py::TestZiggie`: zero for a straight segment; the
  line fallback fires below `|k′| = 10⁻³`; an arc is used for curved data and
  gives ≈ 0 for a pure arc; the value rises monotonically with imposed zig-zag
  and crosses 0.1; **invariant to scaling either axis** — and, beside it, a test
  that `IZZI_MD` is *not*, which is the paper's central criticism.

#### The signed curvature `k`, the segment curvature `k′`, and `SSE`

* Paterson (2011), [10.1029/2011JB008369](https://doi.org/10.1029/2011JB008369).
* Circle fitting by Taubin's algebraic fit refined with the Chernov & Lesort
  (2005) Levenberg–Marquardt geometric fit, which SPD recommends over standard
  non-linear fitters because they converge poorly when the data are a small arc
  of a large circle. Both axes are normalised by their own maxima so that the
  value does not depend on `B_lab` or the NRM.
* **No universal threshold.** Paterson (2011) proposed a strict `|k| ≤ 0.164`
  and a relaxed `|k| ≤ 0.270`, from 38 specimens of known grain size, and
  Paterson et al. (2014) tested the relaxed one as an addition to the standard
  sets. Tauxe et al. (2021) then showed that curvature in lavas is partly
  *fragile* — it disappears when the specimen is given a fresh TRM and grows
  back over months of ageing — so it is not a fixed property of the material,
  and a threshold calibrated on laboratory grain-size series does not transfer
  unchanged to natural specimens.
  The application therefore exposes **named presets with their calibration
  domain and citation** (`CURVATURE_PRESETS`), never a single default:
  `strict (|k| ≤ 0.164)` — Paterson (2011), 38 specimens of known grain size,
  adopted by CCRIT for glassy basalt; `relaxed (|k| ≤ 0.270)` — used by RCRIT
  and by the modified sets of Paterson et al. (2014); and `none`.
* **Decision: implement, with presets rather than a default threshold.**

#### BiCEP — Cych, Morzfeld & Tauxe (2021)

Covered in §7.

### 4.2 Assessed and deferred, with the reason

| Work | DOI | Why not now |
|---|---|---|
| **Biggin & Paterson (2014), QPI** — a set of qualitative reliability criteria for *databases* | [10.3389/feart.2014.00024](https://doi.org/10.3389/feart.2014.00024) | QPI scores a **study**, not an interpretation: age control, TRM origin, dating, alteration monitoring, anisotropy, cooling rate, domain state, magnetostatic interactions, reversal/field-strength checks, published data availability. Several criteria are answered by information the MagIC contribution does not carry (how the age was obtained, whether the data were published). A QPI panel is a natural next step and should read the `ages` and `contribution` tables; scoring it from measurements alone would be misleading. |
| **Jeong et al. (2021)**, new criteria from the 1960 Kılauea flows | [10.1186/s40623-021-01473-6](https://doi.org/10.1186/s40623-021-01473-6) | proposes thresholds on statistics already implemented; a preset, not new mathematics. Can be added as a named set once its table has been transcribed from the paper and checked. |
| **Cromwell & Zhang (2021)**, and the CCRIT/RCRIT family | CCRIT: [10.1016/j.pepi.2014.12.007](https://doi.org/10.1016/j.pepi.2014.12.007) | **implemented as presets**, see §8 |
| **Muxworthy & Baker (2021), ThellierCoolPy** | [10.1029/2021GC010145](https://doi.org/10.1029/2021GC010145) | a cooling-rate correction that models the blocking-temperature spectrum rather than extrapolating a TRM-versus-log-rate line. It needs rock-magnetic input (a hysteresis-derived grain distribution) that a Thellier measurements file does not contain. The line-extrapolation correction implemented here is the one the legacy GUI applied and the one Megiddo's published factors were computed with, so it is what a re-analysis must reproduce. ThellierCoolPy belongs as an alternative once the extra input can be read. |
| **Santos & Tauxe (2019)**, accuracy, precision and cooling-rate dependence of laboratory TRMs | [10.1029/2018GC007946](https://doi.org/10.1029/2018GC007946) | evidence for *why* the cooling-rate correction matters, and a source of ground-truth data; no new statistic. |
| **RESET (Cych et al., 2021)**, monitoring thermoremanent alteration | [10.1029/2020GL091617](https://doi.org/10.1029/2020GL091617) | an experimental protocol with its own measurement sequence, not a statistic over the standard one. Supporting it means recognising a new protocol on load; deferred, and noted as a natural extension of the step classifier. |
| **Paterson et al. (2015)**, Thellier data from multidomain specimens | [10.1016/j.pepi.2015.06.003](https://doi.org/10.1016/j.pepi.2015.06.003) | the MD simulation set behind the Ziggie thresholds; used as evidence, not implemented. |
| **Yu (2012)'s own `Z`/`Z*`** as clarified for Tully & Paterson (2025) | — | the Ziggie reference implementation computes `Z` with an `x_i/x_end` weight and a `1/√(n−1)` normalisation, and `Z*` differs from SPD's printed form. SPD v1.2.0 and its reference MATLAB agree with each other, and the published calibration table was computed with them, so **SPD's form is implemented** and this divergence is recorded here. A study reporting `Z*` should say which definition it used. |
| **Machine-learning selection** (e.g. the 2023 comparative-classifier literature that cites Paterson et al. 2014) | — | nothing in the surveyed set proposes a validated ML selector for Thellier data with published thresholds and a reference implementation. Nothing to implement. |
| **Multispecimen (MSP-DSC) criteria**, as tabulated by Sánchez-Moreno et al. (2025) | [10.1029/2023GC011382](https://doi.org/10.1029/2023GC011382) | a different experiment (`LP-PI-MULT`), out of scope for a Thellier-type successor. The core excludes `LP-PI-MULT` explicitly rather than mis-reading it. |
| **Shaw-family corrections** (e.g. the 2024 Shaw-protocol bias paper) | [10.1029/2024GL109930](https://doi.org/10.1029/2024GL109930) | a different experimental family again (`LP-PI-ALT-AFARM`); out of scope. |

### 4.3 Not a statistic, but it shaped the design

**Tauxe et al. (2021), fragile curvature**
([10.1029/2020GC009423](https://doi.org/10.1029/2020GC009423)). Ageing
experiments on lava specimens show that Arai-plot curvature grows over two
years regardless of the strength or direction of the ageing field, and vanishes
when a fresh TRM is given. Curved plots — fragile or multidomain — are biased
low. The paper's conclusions 4 and 5 are why this application (a) always
computes and shows `k` and `k′`, (b) offers curvature presets with their
provenance instead of one number, and (c) computes the additivity check `δAC`,
which the authors identify as a detector of the additivity failure behind the
low-field bias.

---

## 5. Licensing of the reference implementations

| Implementation | Declared licence | What was done |
|---|---|---|
| SPD reference MATLAB (`SPD.m`), calibration data, AraiCurvature C++/MATLAB | published at earthref.org for cross-platform calibration; the test data's own README asks that problems be reported to the author | read to check numbers; the **data** are shipped in `data_files/SPD_calibration` with attribution, which is the use they were published for. No MATLAB was translated. |
| `SPD/` inside this repository | ships under PmagPy's licence | the new core does **not** import it; it is python-2-era code and was the source of #769's traceback. The curvature fit was written afresh in `pmagpy/pint_stats.py`. |
| Ziggie — <https://github.com/ATully98/Ziggie> | **no licence file**; `CITATION.cff` only | read to check the numerical conventions of a published algorithm; **no code copied**. Ziggie here is written from equation 2 and §2.2 of the paper, using PmagPy's own circle fit. |
| BiCEP GUI — <https://github.com/bcych/BiCEP_GUI> | **CC BY-SA 4.0 in the repository, MIT in the package metadata** — the conflict the brief flagged | not resolved by us, and not ours to resolve. **No code was taken.** `pmagpy/bicep.py` is written from the paper: the model of §2.1, the reparameterisation of §2.2.1, equation 17 of §2.2.2 and the site model of §2.2.3. The module docstring says so, and the citation is carried into the panel, the methods block and the exported rows. If the authors clarify the licence and prefer their implementation to be used, that is a one-line change of sampler backend. |

---

## 6. Two places where SPD v1.2.0's printed text and its own reference disagree

Both were found by implementing the printed equation and failing the
calibration test. Both are recorded so a reader can decide which they want.

### 6.1 `δpal`: the sign of the vector difference

§5.3 prints `δpTRM_l,j = TRM_l − pTRM check_l,j` for the *vector* difference,
the opposite way round from the *scalar* `δpTRM = check − x` used throughout the
rest of the document. The printed form gives 25.4 for specimen 187A against a
published 41.4; `check − TRM` gives 41.37. The reference MATLAB and the
published table use `check − TRM`. **Implemented:** `check − TRM`. Documented in
the function's docstring.

### 6.2 `S`: data variance or measurement variance

§3 prints `S = (1/(b²σ_x² + σ_y²))·Σ(y − bx − Y_Int)²` and then defines `σ_x²`
and `σ_y²` as the variances *of the data*. With that reading, `S′` is
vanishingly small for a good fit rather than averaging one, and the χ² test it
is meant to support cannot work: for ten Arai points with 1 % noise, `S′ ≈
5×10⁻⁴` rather than ≈ 1. York (1966) and Yu et al. (2000) weight by the
*measurement* uncertainties, and only that form is χ² distributed.

**Implemented:** SPD's printed form by default, so the value matches other
SPD-conformant software; supplying `Experiment.sigma_x` and `sigma_y` switches
to York's weighting. Both are tested —
`test_s_follows_the_equation_spd_prints` against a hand evaluation, and
`test_york_weighting_gives_s_prime_an_expectation_of_one` over 60 noise
realisations. Worth reporting to the SPD maintainers.

---

## 7. BiCEP

* **Citation.** Cych, B., M. Morzfeld & L. Tauxe (2021), Bias Corrected
  Estimation of Paleointensity (BiCEP): An improved methodology for obtaining
  paleointensity estimates, *G-cubed* **22**, e2021GC009755,
  [10.1029/2021GC009755](https://doi.org/10.1029/2021GC009755).
* **What it does.** Instead of accepting or rejecting specimens one at a time,
  every specimen of a site is fitted at once under the constraint that its
  intensity estimate is linear in its Arai curvature,
  `B_j = B_site + c·k_j + ε_j`, `ε ~ N(0, σ_B)`; the site paleointensity is the
  intercept at `k = 0`. A specimen whose plot is poorly described by a line
  *or* a circle has an uncertain `k_j` and little influence on the fit.
* **Equations implemented.** §2.2.1's scaling (pTRM by its maximum; the minimum
  pTRM and minimum remaining NRM subtracted; specimens whose remaining NRM never
  drops below 25 % of the initial NRM excluded); §2.2.1's reparameterisation
  after Chernov & Lesort (2005) into (angle to the centre, distance to the
  circle, signed curvature), which makes the posterior unimodal; equation 8's
  analytic marginalisation of the per-specimen noise under `p(σ) ∝ 1/σ`;
  equation 17, `B_j = B_lab / tan φ` — the tangent to the circle where the line
  from the origin to the centre meets it; and §2.2.3's site model with
  `B_site ~ U(0, 250 µT)` and `σ_B ~ half-normal(5 µT)`, the paper's preferred
  "Linear, 5 µT" model.
* **Calibration domain.** 30 sites of known field (IGRF, Arch3k.1, or a
  laboratory TRM), Table 1 of the paper. On that set the preferred model scores
  better than CCRIT, modified PICRIT and modified SELCRIT on the paper's own
  accuracy metrics.
* **Limitations.** The linear relation between bias and curvature is empirical,
  not theoretical — the authors say so. Zig-zag bias is not curvature bias, and
  the method leans on the uncertainty in `k_j` to down-weight such specimens
  rather than detecting them; using Ziggie alongside is sensible. A site needs
  at least two specimens, and realistically more.
* **Decision: implement now, as a first-class panel** — not an iframe, not a
  notebook, not a launcher for another program.
* **Validation.** Known-answer synthetic sites whose bias is linear in curvature
  by construction; the sampler recovers 45.2 µT against a true 45.0 with
  R-hat 1.005, and 70 µT and 52 µT sites likewise. On the real Megiddo site
  hz05 (38 specimens) it gives 78.8 µT [76.3, 81.2] against a classical mean of
  75.7 ± 7.7 µT.

---

## 8. Criteria presets, and where each threshold comes from

Every preset is transcribed from a published table. None was invented.

| Preset | Source of the thresholds |
|---|---|
| `CCRIT` | Cromwell, Tauxe, Staudigel & Ron (2015), [10.1016/j.pepi.2014.12.007](https://doi.org/10.1016/j.pepi.2014.12.007), as tabulated by Sánchez-Moreno et al. (2025) Table 2, [10.1029/2023GC011382](https://doi.org/10.1029/2023GC011382): n ≥ 4, FRAC ≥ 0.78, β ≤ 0.1, \|k′\| ≤ 0.164, MAD ≤ 5, DANG ≤ 10, n_pTRM ≥ 2, SCAT true; site N ≥ 3, s ≤ 6 µT, s ≤ 15 % |
| `RCRIT` | the same table's relaxed companion: FRAC ≥ 0.60, GAP-MAX ≤ 0.6, \|k′\| ≤ 0.300, MAD ≤ 12 |
| `TTA`, `TTB` | Leonhardt, Heunemann & Krása (2004), ThellierTool v4.22 defaults, [10.1029/2004GC000807](https://doi.org/10.1029/2004GC000807), as tabulated in Paterson et al. (2014) Table 2 |
| `TTA (modified)`, `TTB (modified)` | Paterson et al. (2014) Table 2 — thresholds relaxed to the 95th (A) and 99th (B) percentiles of ideal single-domain behaviour under realistic noise, plus the relaxed curvature criterion the paper tests |
| `PICRIT03`, `PICRIT03 (modified)` | Kissel & Laj (2004), [10.1016/j.pepi.2003.11.006](https://doi.org/10.1016/j.pepi.2003.11.006); modified per Paterson et al. (2014). The α′ ≤ 15° criterion is **omitted**, exactly as Paterson et al. omit it, because it needs an independent direction |
| `SELCRIT2`, `SELCRIT2 (modified)` | Biggin, Perrin & Dekkers (2007), [10.1016/j.epsl.2007.05.016](https://doi.org/10.1016/j.epsl.2007.05.016); modified per Paterson et al. (2014), minimum NRM fraction raised to 0.35 |
| `This study` | read from the loaded contribution's own `criteria.txt`, so a re-analysis starts from the study's published rule |
| `None` | no criteria; every interpretation is listed as it is |
| + Ziggie | any preset above, with `Ziggie ≤ 0.1` added — Tully & Paterson (2025) |

Paterson et al. (2014)'s three requirements for any criteria set — thresholds
grounded in a quantitative understanding of statistic behaviour, efficacy
demonstrated on an independent data set, and no better than random rejected —
are the reason the presets are named and cited rather than merged into one
house default.

---

## 9. Test plan and provenance

| What | Where | Provenance of the expected value |
|---|---|---|
| every equation | `pmagpy/test/test_pint_stats.py`, 69 tests | hand evaluation of the equation as printed in the source named in `CATALOG[...].citation` |
| degeneracies (n < 3, zero slope, zero VDS, no checks, missing field, missing direction) | the same file | the state and reason are asserted, so no path can produce a sentinel |
| the 20-specimen SPD calibration set, 48 statistics each | `pmagpy/test/test_paleointensity.py::TestSpdCalibration` | `data_files/SPD_calibration/SPD_reference_statistics.csv`, published with SPD v1.2.0 |
| the group statistics of that set | `test_the_spd_calibration_averages_are_reproduced` | SPD v1.2.0 Table 2 |
| anisotropy + non-linear TRM corrections | `test_the_anisotropy_and_nlt_corrections_reproduce_the_published_intensity` | the published `c` and `BAnc` for m428b1, RS25b, RS26a, RS26e |
| 359 legacy interpretations | `TestMegiddoRegression` | `data_files/3_0/Megiddo/specimens.txt`, written by `pmagpy-3.4.1: thellier_gui.v.3.0` |
| Ziggie | `TestZiggie` | equation 2 and §2.2/§2.3 of Tully & Paterson (2025), including the scaling-invariance property the paper uses to reject IZZI_MD |
| BiCEP | `pmagpy/test/test_bicep.py`, 34 tests | synthetic sites whose bias is linear in curvature by construction, plus the paper's own model properties |
| distributions | `TestDistributions` | χ² and F table values; SPD's own quoted noncentral-t value of −1.193 |

Numerical deltas, and the three places where this implementation deliberately
differs from a published number, are in `docs/scientific_validation.md`.
