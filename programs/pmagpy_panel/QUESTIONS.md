# Questions for Nick

Decisions I made on my own while building the hub, and questions I could not
settle from the code or the plan. Each entry says what I did in the meantime so
nothing is blocked; change the answer and I will change the code. Newest at
the bottom; struck through once settled.

## Upload page (2026-09-01)

1. **Where the upload file goes.** Pmag GUI wrote `<location>_<date>.txt` into
   the study directory and I kept that (Home's inventory recognises it, so it
   is not mistaken for a lab file). A 7 MB duplicate of the tables sitting
   beside them is untidy, though, and a second build adds `_1`, `_2` …
   *Alternative*: an `upload/` subfolder, or overwrite one `upload.txt`.
   Keep the Pmag GUI convention?

2. **Private workspace upload.** The four private-workspace functions
   (`create_private_contribution`, `upload_to_private_contribution`,
   `validate_contribution`, `delete_private_contribution`) take an EarthRef
   `username`/`password` and send them as HTTP basic auth. The page currently
   ends with a link to https://www2.earthref.org/MagIC/upload and leaves the
   last step to the browser. Is an in-app login worth building (a password
   field in a Panel page, the credential held in the server process), or is
   the hand-off fine? Also worth asking Rupert Minnett
   whether the public validate endpoint's current behaviour (≈70 s for a 7 MB
   file, the whole file in one POST) is something MagIC is happy to see from
   the hub.

3. **Offline validator vs MagIC's.** The bundled data model is the 2019 copy;
   MagIC's validator finds 33 problems on McMurdo where PmagPy's finds 2
   (mostly method codes and vocabularies that have moved on). Options: (a)
   refresh the bundled JSON on each release; (b) fetch the current data model
   at start-up when online and cache it; (c) drop the offline check and rely
   on the endpoint. I lean to (b) with (a) as the fallback. Which?

4. **Publication tables.** `ipmag.sites_extract` etc. now write into
   `publication_tables/` as `.xlsx` (or `.tsv` when openpyxl is missing) or
   LaTeX. Should openpyxl become a dependency of the apps environment? And are
   the column sets in `map_magic.convert_site_dm3_table_*` (TC, Dec, Inc, N,
   k, R, α95, VGP lat/lon; B, σ, N, VADM, VDM) still the tables people want in
   a paper, or should the page let the analyst choose columns?

5. **Upload file column policy.** `upload_magic` drops columns the data model
   does not know and folds declinations into 0–360. It says nothing about
   what it dropped. Should the page list the dropped columns (e.g. a lab's
   `notes_internal`) so the analyst knows what MagIC will not receive?

## Metadata page (2026-09-01)

6. **Age propagation.** ErMagicBuilder pushed a location-level age down to
   sites lacking one. The Metadata page does not (it fills coordinates and
   copies parent values on request). Is one-way propagation location → site
   → sample wanted, and should it write `age`/`age_unit` or an `ages.txt` row?

7. **Criteria table.** Pmag GUI edited `criteria.txt` in ErMagicBuilder with
   the selection criteria dialog. The hub has nothing for criteria yet; the
   Directions app writes its own. Where should criteria editing live — on
   Metadata as a sixth table, in each analysis app, or nowhere?

## Rock magnetism app (2026-09-01)

8. **Example data.** MagIC contribution 20427 ("RMB oxyhydroxides", Zhang et
   al., IRM; DOI 10.5281/zenodo.15588182) is bundled as
   `data_files/3_0/RMB_oxyhydroxides` (1.1 MB, 9 specimens: FC/ZFC/RTSIRM, AC
   susceptibility, χ–T, Ms–T). It is the app's default example and the test
   fixture. Fine to ship, or would a smaller one (20384 siderite, 350 KB) or
   a synthetic set be better? It has no magnetite, so the Verwey view has
   nothing real to find in it — a small contribution with a clean Verwey
   transition would make a better demonstration and a better test.

9. **Verwey defaults.** The view opens on the FC curve with the
   `verwey_estimate_interactive` defaults (background 60–250 K, excluded
   75–150 K, degree 3). Should FC be the default over ZFC? And the view flags
   "no clear loss" when the remanence loss is below 0.5 % of the curve's range
   or the estimate falls outside the excluded range — is that threshold
   sensible, or should it be tied to something physical?

10. **Orientation gap.** Home's inventory no longer reports missing sample
    azimuth/dip when the directory holds only rock-magnetic experiments (no
    demag, palaeointensity or anisotropy kinds). A study mixing both still
    reports it. Right rule?

11. **Experiment types.** `LP-X:LP-X-T:LP-X-F` (the MPMS AC sweep in
    temperature *and* frequency) is claimed by the AC-susceptibility view
    because the match order puts `LP-X-F` before `LP-X-T`; the pure `LP-X-T`
    runs go to χ–T. Should such an experiment appear in both views? And what
    is `LP-MST` in this contribution — the three Ms–T runs look like MPMS
    in-field warming curves rather than VSM Ms(T); should the Ms–T view treat
    them the same way as χ–T?

12. **Notebook switch-over.** §3 says each view lands with its notebook using
    the same object (`MpmsDcView(measurements).panel()` replaces
    `plot_mpms_dc_interactive`, `VerweyView` replaces
    `verwey_estimate_interactive`). Those notebooks live in
    `RockmagPy-notebooks`, a sibling repository I will not edit unasked. Shall
    I prepare the edited notebooks there, or write the replacement cells here
    (e.g. `programs/pmagpy_rockmag/notebooks/`) for you to move?

## Thermomagnetic views (2026-09-02)

13. **Which runs belong in the Curie view.** The χ–T and Curie tabs offer
    every χ–T (`LP-X-T`) and Ms–T (`LP-MST`, `LP-IMT`) experiment. In the
    example that includes the three MPMS in-field 10–300 K runs, on which
    Curie estimates are meaningless (they come out anyway: the estimators
    return numbers for any monotonic curve). Should the Curie tab hide runs
    whose maximum temperature is below, say, 400 K, or is showing the
    estimates with the methods' caveats enough? The unit toggle already adopts
    kelvin for such runs.

14. **Curie table columns.** The view shows branch, method, T_C ± stderr and
    the method note from the function (its literature caveats). The
    `params` column (fit ranges, slopes) is left out; should it be shown, or
    only in the exported table? And when results go to `specimens.txt`,
    `add_curie_estimates_to_specimens_table` writes one method/branch —
    inflection on heating by default. Is that the right default for the app's
    "save" button, with the choice recorded in `description` as the function
    already does?

15. **Method fit ranges.** `curie_temperature_estimates` takes
    `method_kwargs` (a `fit_range` for Curie–Weiss, Landau and Ms²; tangent
    ranges for two-tangent). The view does not expose them yet — the
    estimates use each method's automatic range. A range slider per method is
    a lot of chrome; one shared "fit range" slider applied to every method
    that takes one would be simpler. Preference?


## Hysteresis view (2026-09-02)

16. **A second example dataset.** `RMB_oxyhydroxides` has no hysteresis,
    backfield or FORC data, and the SSRM2024C contribution the notebooks use
    is private (fetched with a share key), so I did not copy it. Instead
    `data_files/3_0/ECMB_rockmag/` is the rock-magnetic subset of your public
    ECMB contribution (MagIC 20213: 5 VSM loops, 3 backfield curves, the MPMS
    runs of 3 specimens; 690 kB), with a README and the `make_subset.py` that
    rebuilds it from an unpacked copy. Is that the right choice, or would you
    rather ship a different public contribution — one with FORC data too, so
    the FORC view can be tested on shipped data? (The Jackson 2012 MagIC 16460
    contribution has a ten-loop hysteresis experiment and MPMS runs but no
    backfield or FORC.)

17. **The hysteresis view's controls.** The view exposes `process_hyst_loop`'s
    four switches (centering protocol, forced non-linear high-field fit, and
    the two decision-tree overrides). It does not expose the internal
    thresholds (the saturation-test cutoffs, the closure test's SNR/HAR
    limits, the 0.6 high-field window of the non-linear fit) because the
    function does not take them either. Should any of them become arguments,
    or is the decision tree meant to be fixed as in Jackson & Solheid (2010)?

18. **Units in the KPI row.** Fields are shown in mT (Bc = 14.3 mT) while
    MagIC stores tesla and the emitted code returns tesla; Ms/Mr carry the
    unit implied by the column processed (`magn_mass` → Am²/kg, `magn_volume`
    → A/m, `magn_moment` → Am²). Fine, or should the app stick to SI as
    stored to avoid any confusion when results are saved to `specimens.txt`?

19. **Backfield smoothing needs statsmodels.** `process_backfield_data`'s
    default `smooth_mode='lowess'` imports statsmodels, which is not a PmagPy
    dependency (nor installed in the apps environment). For the backfield view
    I plan to offer LOWESS only when statsmodels is importable and default to
    `'spline'` otherwise — or should statsmodels join the `apps` extra in
    `setup.py`?

## Backfield and unmixing views (2026-09-02)

20. **Unmixing defaults and the noisy raw spectrum.** The unmixing view
    follows `coercivity_unmixing.ipynb`: the raw shifted curve
    (`magn_mass_shift` against `log_dc_field`, not the smoothed columns) goes
    to `unmix_coercivity` with `method='spectrum'`, `n_components=2`,
    `vary_skew=False` (the function's own default is `vary_skew=True`). On the
    ECMB backfield curves the raw spectrum is noisy enough (r² ≈ 0.88–0.97 for
    one component) that on two of the three the two-component spectrum fit
    spends its second component on a single low-field point (NED2-8c: 2 % at
    0.6 mT with DP 0.025 — the lower `dp_bounds` limit is 0.01), while the
    `curve` method gives r² > 0.999 and sensible pairs. Three things you may want to decide:
    (a) should the view (and notebook) default to `curve`, or feed the
    smoothed curve to the spectrum method; (b) is a wider minimum dispersion
    (say DP ≥ 0.05, i.e. a component narrower than the field spacing is not
    physical) the right guard against one-point components; (c) `vary_skew`
    False (notebook) or True (function default) as the app's default?

21. **The parsimony rule stops early.** `select_n_components` stops adding
    components at the first one that improves the residual by less than
    `min_improvement` (2 %). On the two ECMB spectra above a second component
    adds 0.1–0.2 % (the one-point component) while a third adds 11–24 %, so
    the rule returns 1. That is the rule as written; should it instead look
    ahead one step (skip a useless k if k+1 helps), or is a returned 1 with
    the table beside it (the view shows each step's improvement) the honest
    answer?

22. **Bcr at the SIRM point.** A backfield run that starts with a zero-field
    SIRM measurement (field 0.0 rather than a positive field) makes
    `process_backfield_data` take log10(0): the function drops the first
    point on its own only when the first field is positive. The view drops it
    for either case and disables the checkbox while that experiment is shown.
    Should the function do the same (`if experiment[field].iloc[0] >= 0`)?

## FORC view (2026-09-02)

23. **The shipped FORC example.** No public MagIC contribution with an
    `LP-FORC` run was small enough to ship (the Baraboo tables are 22–23 MB;
    SSRM2024C is private; Egli's VARIFORC test data is CC BY-NC). The view's
    example, `data_files/3_0/FORC_example` (1.3 MB), is PmagPy's own raw
    MicroMag file `data_files/forc_diagram/conventional_example.forc`
    (120 curves, measured 2016-04-13, in the repo since 2018) exported to a
    MagIC measurements table by `forc.export_magic_measurements_from_raw`.
    Nothing is recorded about the sample. Do you know where it came from (added
    by "Lori J" in 2018), so the README can say — or is there a small run of
    yours (IRM, a few hundred kB) you would rather ship as the example?

24. **The diagram window a MagIC table gives.** A raw MicroMag header carries
    the analyst's window (`Hb1`/`Hb2`/`Hc1`/`Hc2`: ±0.1 T × 0–0.1 T for the
    example) and `process_forc` frames the diagram with it when no limits are
    given. The MagIC export has nowhere to put those, so the reader
    synthesizes them from the field range of the run (±0.218 × 0.237 T for
    the example) and a diagram from a MagIC table comes out mostly blank. The
    view therefore starts at a square window out to the Bc extent of the
    finite ρ (0.12 T here) and writes `Bu_min`/`Bu_max`/`Bc_max` into the
    code. Should the export carry the header window somewhere (the
    `description` column of the measurements, or `specimens.txt`), so the
    round trip preserves the analyst's framing? And is a square window the
    right default, or Bu ± half of Bc max, as some prefer?

25. **FORC smoothing defaults.** The view offers LOESS at strength 1 (the
    pipeline's default: spans set for `target_n_eff=60`) and VARIFORC through
    `variforc_settings` (presets regular / central ridge / vertical ridge /
    both ridges, smoothing factor 3–15, default 7). Egli's published analyses
    use factors 7–11. Should the app default to VARIFORC `regular` sf 7, as
    the FORCme notebooks lean towards, or stay on the pipeline's LOESS
    default? VARIFORC takes ~1–2 s on the example without numba (regridding
    adds ~8 s); numba is not in the apps environment — should it be?

26. **Bc from the FORC grid.** The KPI row reports `find_coercive_field` on
    the interpolated M(Ha, Hb) grid — the field where the lowest reversal curve
    crosses zero moment — as "Bc". On the example it is 2.5 mT. It is the
    major-loop Bc only when the deepest reversal saturates the sample; is it
    worth showing at all, or should the row report the ρ peak position
    (`find_bounded_peak_rho` — on the example it sits at Bc ≈ 0, which is why
    it is not shown) or nothing?


27. **Writers that refuse versus writers that add a row.** Of the four
    specimens-table writers the app calls, `add_hyst_stats_to_specimens_table`
    and `add_unmixing_to_specimens_table` create a row when no row carries the
    experiment (the unmixing writer adds one row per component by design), while
    `add_Bcr_to_specimens_table` raises "no specimens row matches" and
    `add_curie_estimates_to_specimens_table` falls back to a specimen match and
    writes nothing when that fails too. The app shows the refusal in red. Should
    the Bcr and Curie writers create the row instead, as the other two do, or
    should the hysteresis writer stop creating rows? The current split means a
    table described only on the Metadata page (one row per specimen, no
    `experiments` values) takes hysteresis and unmixing results but not Bcr.

28. **`specimens.py` as an appended log.** Every save appends its block
    (`# ----- Bcr: NED2-8c`, the analysis, the writer call, the write) to
    `specimens.py` beside the table, so the file replays the history of the
    table including saves later superseded (a re-save of the same experiment
    appends again; the writers themselves replace, so replaying is idempotent).
    The alternative is one block per (experiment, result) kept current, which
    reads as a script rather than a log but loses the record of what was tried.
    Which do you want to see in a MagIC directory?

29. **Method codes and software on the hysteresis row.** The unmixing writer
    sets `method_codes` (`LP-BCR-BF`) and `software_packages` on the rows it
    adds; the hysteresis, Bcr and Curie writers set neither, and the app stamps
    only `software_packages` (with `pmagpy-<version>:pmagpy_rockmag`) on the
    rows it touches. Should the app (or the writers) also add `LP-HYS`,
    `LP-BCR-BF` and `LP-MST`/`LP-X-T` to `method_codes` of a row that gains
    those results, or is `method_codes` on `specimens.txt` reserved for the
    interpretation codes MagIC expects there?

30. **Two `description` conventions.** `add_hyst_stats_to_specimens_table` and
    `add_unmixing_to_specimens_table` write JSON (`text | {json}`) into
    `description`; `add_curie_estimates_to_specimens_table` writes a Python dict
    literal (`{'curie_method': 'inflection', 'curie_branch': 'cooling',
    'curie_temp_K': 55.7}`). A reader parsing one convention fails on the other.
    Move the Curie writer to the JSON convention (changing what the notebooks
    have written so far), or leave both?

31. **The Curie estimate that is saved.** `critical_temp` holds one value per
    row, so the view has an "Estimate to save" picker over the finite estimates
    (heating branch first, methods in the table's order), defaulting to the
    first and keeping the pick when the experiment changes (so a batch of
    specimens saves the same method/branch). Is heating-inflection the right
    default, and should the pick carry across experiments or reset to the
    default each time?

32. **`hyst_xhf` for loops in moment or volume.** The hysteresis writer now
    takes `magnetization=` and sends Ms/Mr of a `magn_moment` or `magn_volume`
    loop to `hyst_ms_moment`/`hyst_ms_volume`, but `hyst_xhf` has a single
    column, and the data model gives it the unit m³ (a moment per A/m). The
    writer has always put the high-field slope in the loop's own units per
    tesla there (Am²/kg/T for a mass loop, which is what the notebooks wrote),
    and the view does the same for moment and volume loops. Convert to the
    data model's unit, record the unit in `description`, or leave the column
    as the notebooks have used it?

## Anisotropy application (2026-09-02)

33. **Which frame a directory opens in.** The session opens in the frame
    most of the table's tensor rows are in (McMurdo: specimen coordinates,
    since `aarm_magic` wrote `aniso_tilt_correction = -1`), and the picker
    offers every frame with a count, starring the ones reached by rotating
    here. `aniso_magic_nb` defaults to geographic. Should the app open in
    geographic whenever the sample orientations allow it, since that is the
    frame the fabric is interpreted in, or start where the data are?

34. **Rotating on the fly vs requiring rows.** `tensor_table(coordinates='g')`
    rotates a specimen-frame tensor with `azimuth`/`dip` from `samples.txt`
    when the table has no geographic row for that specimen (and applies
    `bed_dip_direction`/`bed_dip` for 't'), marking the row `source =
    'rotated'`; a stored row in the frame always wins. `aniso_magic_nb`
    instead requires the rows to exist (as `aarm_magic -crd g` writes them).
    Is rotating in the app acceptable, given nothing is written unless a mean
    is saved (item 36), or should the app ask the user to re-run the
    reduction in the wanted frame?

35. **Bootstrap defaults.** Off by default (Hext only), 1000 draws,
    non-parametric, seed 0 shown in the code block; parametric needs
    `aniso_s_sigma > 0` on every row. `aniso_magic_nb` uses 1000 and
    non-parametric too. Fine, or should bootstrap be on by default for
    groups of ≥ 5–6 tensors, where Constable & Tauxe (1990) argue it is the
    better description?

36. **Where the mean tensor goes.** `mean_record` builds a row with the data
    model's `aniso_*` columns of `sites` (`aniso_v1..v3` as `tau:dec:inc`,
    `aniso_tilt_correction`, `aniso_type`, `aniso_ftest*`); the same columns
    exist in `samples`. The plan is a `TableSave` (generalising the rockmag
    `SpecimenSave`) that writes the row of a site-level selection to
    `sites.txt`, a sample-level one to `samples.txt`, and refuses a location
    or an "all specimens" selection. Should a mean also be written for the
    specimen-frame tensors of one sample, and how should the bootstrap
    parameters be recorded — the data model has no ζ/η columns for sites, so
    the `description` JSON convention of the rockmag writers (QUESTIONS 30)
    is the candidate?

37. **A single specimen's Hext statistics.** With one tensor selected the
    view shows the Hext ellipses of that specimen's measurement scatter
    (`aniso_s_sigma`, `aniso_s_n_measurements`, ν = 3n − 6), as `aniso_magic_nb`
    does per specimen. It is only meaningful when σ was estimated from ≥ 3
    measurement positions (n ≥ 3 for ν > 0; `aarm_magic` writes n = 9 for the
    9-position scheme). Show it always, or only when the specimen's `aniso_ftest`
    says the tensor is anisotropic?

38. **`aniso_sigma` in `ipmag.aniso_magic_nb`.** `pmagpy/ipmag.py:11382`
    checks for `aniso_s_sigma` but fills a column named `aniso_sigma` when it
    is missing, so a table without σ then fails a few lines later on the
    parametric bootstrap and on the Hext statistics. The app's own layer does
    not use this path; fix the typo in `ipmag.py` in the same commit series,
    or leave the legacy function as it is until the notebooks switch?

39. **AARM vs ARM in the hub's inventory.** Measurements with `LP-AN-ARM`
    read as anisotropy of **ARM** from the method code, while `specimens.txt`
    labels the tensors `aniso_type = AARM` (as `aarm_magic` writes). The hub
    now lets the specimens table's label win when tensors exist, and shows
    the method-code label only for a directory with measurements but no
    tensors yet. Is `AARM`/`ATRM`/`AMS` the vocabulary the chip should
    always use?

40. **Reducing measurements to tensors in the app.** A *Reduce* view would
    run `ipmag.aarm_magic`/`atrm_magic` (and the 15-position AMS reduction
    for Kappabridge measurements without `aniso_s`) on the directory's
    `measurements.txt` and write `specimens.txt`, so the fabric can be looked
    at without a CLI step. Those functions write files rather than returning
    tables and take the whole directory; refactor them into UI-free
    functions that return the specimen rows (the writer being the app's
    `TableSave`), or call them as they are and re-read the directory?

41. **JSON in `description` is CSV-quoted on disk.** The mean tensor and the
    bootstrap parameters ride in the `description` cell as
    `mean AARM tensor of 5 specimens | {"s": [...], "hext": {...}, ...}` (the
    `text | {json}` convention the rock-magnetic writers already use).
    `MagicProject.write_table` → pandas `to_csv` wraps a cell containing `"`
    in quotes and doubles the inner ones (`""s""`), which pandas and
    `contribution_builder` read back correctly. Does the MagIC upload
    validator accept quoted cells in a tab-separated table, or should the
    detail be written without double quotes (single-quoted keys are not JSON;
    a `key=value;...` form would be)? Applies to the rockmag results too.

42. **One row per mean, or the existing site row?** A MagIC site usually has
    several rows (a direction, an intensity…), so `add_mean_to_table` gives
    the mean tensor a row of its own — `site`, `location`, `citations` ("This
    study"), the `aniso_*` cells, `method_codes`, `specimens` — and replaces
    it on a re-save of the same `aniso_type` and `aniso_tilt_correction`;
    a mean in another frame is another row. The alternative is to fill the
    `aniso_*` columns of the site's existing direction row. Which do you
    want uploaded? Also: `specimens` on that row lists the specimens the mean
    was taken over (colon-joined), which is the `specimens` column's meaning
    on sites rows — confirm that this is right for a fabric mean.

43. **Reducing measurements to tensors — the choices made** (answering 40:
    refactored, not wrapped). `pmagpy/anisotropy.py` now has
    `design_matrix`/`fit_tensor`/`specimen_tensor`/`reduce_measurements`
    /`tensor_record`/`add_tensors_to_specimens_table`, and the app's
    **Reduce** tab runs them. They reproduce `aarm_magic` on McMurdo (17 of
    18 specimens to 1e-8) and `atrm_magic` on its example (30 specimens to
    5e-8), with these differences to confirm:
    - *Field directions come from the table.* `treat_dc_field_phi/theta` are
      used when present; the fixed 6/9/15-position schemes only when they are
      missing (aarm_magic assumes the scheme from the count; atrm_magic
      requires phi/theta). The 18th McMurdo specimen, `mc15h`, has 8
      positions — aarm_magic refuses it, the new code fits it (nf = 18);
      a table's own directions seem the right authority. Agree?
    - *The zero-field baseline is subtracted by default for both protocols.*
      aarm_magic subtracts the AF-demagnetized remanence before each ARM step;
      atrm_magic does not subtract the `LT-T-Z` step. For the antipodal
      6-position ATRM design a constant offset cancels in `s`, so the
      tensors are identical either way, but it stays in the residuals:
      atrm_magic's σ is ~3× larger and its F tests are biased low. The
      Reduce tab has a checkbox (on by default); for AARM turning it off
      fits the residual ARM as if acquired in the field — a different
      tensor. Keep the checkbox, or hide it and always subtract?
    - *`aniso_alt`.* Written only when there is an `LT-PTRM-I` check, as
      atrm_magic's 100·|m₁ − m₂| / mean of the scalar moments (repeat of
      the first position). Megiddo `hz05a1` gives 1.43 % this way; the stored
      row (from thellier_gui) says 2.13. Which definition should `aniso_alt`
      carry (scalar vs vector difference; percent of what)? atrm_magic
      writes `aniso_alt = 0` when there is no check — the new code leaves
      the cell empty, since 0 % alteration was not measured.
    - *A baseline serves the in-field steps that follow it* until the next
      zero-field step (ATRM: one `LT-T-Z` for six positions; AARM: one
      `LT-AF-Z` per position). Fine for the standard protocols; an ARM
      experiment with a single leading demagnetization would be treated as
      ATRM is.
    - *`aniso_s_n_measurements`* counts positions (9 for McMurdo), as the
      legacy code does, not measurement rows (18 with baselines).
    - *`sample` on a new specimen row* comes from the specimen's other rows,
      else from the measurements' `sample` column, else from a samples table
      whose `specimens` column lists it (McMurdo's has no such column).

44. **`orientation_magic` — what the new tests found (2026-09-02).**
    `pmagpy/test/test_ipmag_magic_files.py` checks the function against
    `data_files/orientation_magic/orient_example.txt` and `pmag.doigrf` /
    `pmag.dosundec`. Three fixes went in; two choices are yours.
    - *Fixed*: sites came out with no `location` column and a stray
      `sample_type` column (a stale loop variable was used as the key);
      `bedding_dip_direction` was not inherited by the samples that leave it
      blank although `bedding_dip` was, so a site's second sample lost its
      bedding; `average_bedding=True` never averaged (tested against an
      empty `fpars` inside the loop).
    - *The example file uses the old column names* `site_class`,
      `site_lithology`, `site_type`, `sample_flag`, `magic_method_codes`;
      the docstring (and pmag_gui's template) say `sample_class`,
      `sample_lithology`, `sample_type`, `sample_orientation_flag`,
      `method_codes`. I made `site_*` fall back to `sample_*` so the example's
      geology reaches the sites table; `sample_flag` and `magic_method_codes`
      are still ignored, so `mc137a`'s `b` flag and `SO-GT5` code are lost.
      Update the example file to the documented headers, or alias those too?
    - *Inheritance crosses sites*: a blank bedding (or date, or lat/lon) takes
      the last recorded value even when the previous row was another site —
      `mc137` inherits `mc123`'s bedding in the example. That is the
      documented behaviour ("leave the field blank and the program will fill
      in the last recorded information"), kept as is. Should the hub's
      Convert page warn when an inherited value crosses a site boundary?

45. **`programs/__init__.py` now respects a preset matplotlib backend
    (2026-09-02).** The package pins `TKAgg` (or `WXAgg` for the wx GUIs) for
    the command-line programs. It used to decide by calling
    `matplotlib.get_backend()`, which resolves the automatic backend by
    importing `matplotlib.pyplot` and probing the GUI toolkits — ~0.15 s on
    every `import programs`, and a GUI probe inside a server process — and,
    because it compared against `'TKAgg'` while matplotlib canonicalises to
    `'TkAgg'`, it overrode nearly everything, including `MPLBACKEND=Agg` on
    a headless machine. It now reads the raw rcParams entry and leaves any
    explicitly set backend (`MPLBACKEND`, a matplotlibrc, an earlier
    `matplotlib.use`) alone, which is what its comment always said it did.
    The one behavioural change: a user with `MPLBACKEND=MacOSX` in their
    shell who runs `demag_gui` no longer gets `WXAgg` forced on them. The wx
    GUIs embed their canvases through `backend_wxagg` directly, so I expect
    that to be harmless, but I have not run the wx GUIs (no wx in the apps
    env). Fine, or should the wx programs keep forcing `WXAgg`?

46. **Field notebooks as Convert formats (2026-09-02) — three decisions
    to check.** `orientation_magic` and `azdip_magic` are now the `orient`
    and `azdip` formats in `convert_registry`, so the Convert page serves
    them (no separate Orientation page; HUB_PLAN step 5). Three things I
    decided on the way:
    - *Several rows per sample.* `orientation_magic` writes one sample row
      per orientation method — for `mc123a` in the example: `FS-FD:SO-MAG`
      with the raw compass azimuth (258.0), `FS-FD:SO-CMD-NORTH` with the
      declination-corrected azimuth (48.3, `azimuth_dec_correction` 150.3),
      `FS-FD:SO-SUN` with the sun-compass azimuth (200.1). I kept that
      output as is. But `magic_project.build_orientation` (the Directions
      app) takes the *first* row with an azimuth and dip, i.e. the raw
      compass reading, never the corrected or sun-compass one. Should it
      prefer `SO-SUN`, then `SO-CMD-NORTH`, then `SO-MAG` (a raw compass
      azimuth is never the one to use when a corrected one is in the
      table)? Or should `orient` write one row per sample carrying the best
      azimuth with the full method code string, as most MagIC 3
      contributions do? (Aside: in the McMurdo example the sun azimuth and
      the IGRF-corrected azimuth differ by ~150°, which at -78° latitude
      says the compass reading is not to be trusted — plausible, and a good
      argument for the app preferring `SO-SUN`.)
    - *Replacing placeholders.* A measurement converter (CIT: azimuth 90,
      dip −90, bed dip 0, height 0, `SO-MAG`) writes placeholder sample
      rows. When a notebook is converted into such a directory with
      "append", its rows replace every earlier row of the same sample or
      site (`Format.replaces`), all of them; a column the notebook rows
      leave blank takes the earlier value *except* the orientation columns
      and `height` (`convert_registry.ORIENTATION_COLUMNS`), because those
      are exactly the placeholders. So a CIT `.sam` lat/lon on the site row
      survives, a CIT height 0 does not. The other way round (notebook
      first, measurements later) the measurement converter's placeholders
      would be appended beside the notebook rows and `build_orientation`
      would still pick the notebook row (it comes first). Is "the notebook
      wins" the rule you want, or should a converted directory refuse the
      notebook when its samples already have real (non-placeholder)
      orientations?
    - *`azdip_magic` bedding.* The AzDip file gives bedding as strike and
      dip; `azdip_magic` sets `bed_dip_direction = strike − 90` with the
      comment "assume dip to right of strike". By the right-hand rule the
      dip direction is `strike + 90`; "to the right of strike" when looking
      along the strike is also `+90`. Is the −90 a long-standing PmagPy
      convention the example files rely on (the Iceland example has strike
      149, dip 5 → dip direction 59), or a bug to fix? I left it alone and
      the format's note says the file's own conventions apply.
    - *`azdip_magic` dip convention.* Its docstring says "field_dip is
      degrees from horizontal of drill direction" and "Lab arrow dip =
      90 − field_dip", and it calls `pmag.orient(..., or_con=3)` — whose
      own docstring says convention 3 is for a *hade* measured in the
      field. `pmag.orient`'s convention 5, labelled "AZDIP", is different
      again (lab dip = field_dip − 90). The Iceland example's `is001a 183
      14` becomes azimuth 183, dip 76, which is right if 14 is a hade and
      wrong (sign and value) if it is an inclination from horizontal. Which
      is the AzDip file format's meaning? The Convert note now just states
      what the converter does (convention 3) rather than either docstring.

47. **Kappabridge converters as Convert formats** (2026-09-02). `k15`,
    `kly4s`, `sufar4` and the LORE `iodp_kly4s` export are registry Formats;
    a directory converted from any of them opens Anisotropy. Choices made
    without you:
    - *`sufar4` keeps the case of names by default.* The command-line
      converter lower-cases specimen, sample and site names unless
      `preserve_case` is given (the IODP example becomes
      `318-u1356a-1r-1-w-83`). In the hub the default is the other way, so
      the names join the tables other converters write; the checkbox "Keep
      the case of names" unticks back to the CLI behaviour. Fine, or should
      the CLI default change too?
    - *`sufar4` orientation convention.* The converter's `or_con` defaults
      to `False` = take the file's azimuth and dip as written; the form
      offers "as written in the file" plus conventions 1–6. Left as written.
    - *The bulk `LP-X` measurement no longer counts as a susceptibility
      experiment.* The inventory's "Susceptibility" kind (Rock magnetism
      door) now needs `LP-X-T`, `LP-X-F` or `LP-X-H`; the bare `LP-X` the
      Kappabridge converters write for the bulk value is not something the
      Rock magnetism app can plot, and before this change a Kappabridge-only
      directory offered Rock magnetism as well as Anisotropy. Any `LP-X`
      data you would want that door open for?
    - *Example names.* `kly4s_magic/KLY4S_magic_example.dat` has IODP names
      (`318-U1359B-011H-1-W-75`) and the example runs with naming convention
      1, giving 26 sites of one sample each with site = sample minus its
      last character. It converts; it is just a poor demonstration of the
      naming. Is there a non-IODP KLY4S file worth shipping as the example
      (SIO's own LabView output), or a convention that fits IODP names?
    - *`k15` writes a `specimen` column into samples.txt* (the converter
      builds the sample row from the specimen record). Left alone; the
      `_drop_redundant` step does not touch it. Worth dropping in the
      converter?
    - *Fixed on the way*, tell me if either is wrong: `kly4s` wrote
      `samples.txt`/`sites.txt` into the working directory instead of
      `dir_path` (`samp_outfile`/`site_outfile` were never joined); and
      `pmag.tauV` now takes the real part of the eigen-decomposition when
      the imaginary parts are all zero — numpy 2's `eig` returns complex
      arrays for a symmetric tensor, so every `dostilt` (hence every
      tilt-corrected AMS tensor) raised a ComplexWarning while discarding
      the zero imaginary part anyway. Values are unchanged (the `dostilt`
      docstring example reproduces to the last digit).

48. **MagIC 2.5 → 3.0 as the `legacy` Convert format** (2026-09-02). A
    directory of 2.5 tables is guessed from the names (`magic_measurements`,
    `er_*`, `pmag_*`, `rmag_*`, `magic_methods`), the Convert page preselects
    "MagIC 2.5 tables (upgrade)" with the file list disabled, and one click
    runs `pmag.convert_directory_2_to_3` (the `data_files/2_5/McMurdo`
    example: 25,470 measurements, specimens, samples, sites, locations, 99
    ages, 23 criteria in ~3 s). Decisions to check:
    - *The 2.5 files stay.* The 3.0 tables are written beside them and Home
      then reads "17 MagIC 2.5 tables beside the 3.0 tables". Nothing is
      deleted or moved; the analyst can. Would you rather they went into a
      `magic_2_5/` subfolder so the directory is tidy for upload?
    - *`rmag_anisotropy`, `rmag_hysteresis`, `rmag_results`, `pmag_results`,
      `er_images` are not translated* — `convert_directory_2_to_3` never did;
      the log names them and points at MagIC's upgrade tool
      (earthref.org/MagIC/upgrade). For the rock-magnetism side the
      `rmag_anisotropy` → `specimens.aniso_*` and `rmag_hysteresis` →
      `specimens.hyst_*` translations would be a bounded piece of work
      (`map_magic` has no maps for them today). Worth doing here, or is
      MagIC's tool the answer for legacy rock-magnetic tables?
    - *A 2.5 contribution file* (one text file, `tab delimited\ter_locations`
      first) is recognised as such; unpacking it gives the 2.5 tables, and
      the upgrade is the next click. Two steps rather than one; a single
      "unpack and upgrade" seemed not worth a special path. Agree?
    - *A directory with `er_*` tables but no `magic_measurements.txt`* is
      refused ("no magic_measurements.txt in the directory") because
      `convert_directory_2_to_3` returns False without one; the level
      tables alone could be upgraded (`convert_and_combine_2_to_3` per
      table). Rare enough to leave?

49. **The criteria table on Metadata** (2026-09-02). `criteria.txt` is edited
    in the same grid as the level tables; *Add default criteria* appends
    PmagPy's defaults; *Check* scores every criterion against the table it
    names ("913 of 1,374 pass, 385 blank"). Decisions to check:
    - *The default values are `pmag.default_criteria(0)` translated through
      the data model's `criteria_map`* — so `specimens.dir_mad_free <= 5`,
      `samples.dir_alpha95 <= 5`, `sites.dir_n_samples >= 5`,
      `sites.dir_n_specimens_lines >= 4`, `sites.dir_k >= 50`, and the
      Thellier set (`int_n_measurements >= 4`, `int_n_ptrm >= 2`,
      `int_drats <= 20`, `int_b_beta <= 0.1`, `int_maxdev <= 15`,
      `int_fvds >= 0.7`, `int_q >= 1`, `int_dang <= 10`,
      `int_mad_free <= 10`; sites `int_n_samples >= 2`,
      `int_abs_sigma <= 5e-6`, `int_abs_sigma_perc <= 15`). Two things fall
      out of the translation: MagIC's map sends the 2.5 `specimen_dang` to
      `specimens.int_dang`, so there is *no directional DANG default*
      (`specimens.dir_dang <= 10` would be the Pmag GUI intent), and there is
      no `dir_n_measurements` default at all (the McMurdo study uses `>= 4`).
      Add either or both? The Thellier thresholds are the old `-dcr` ones;
      a second set built on the Standard Paleointensity Definitions (FRAC,
      SCAT, GAP-MAX — the statistics Thellier GUI's criteria dialog offers)
      could be added if you name the set you want.
    - *A blank cell fails a criterion* (`pmag.grade`'s rule: a record
      without the statistic is killed). The check reports blanks apart from
      failures, and `passing_rows(..., blank_fails=False)` exists for the
      other reading. Which should Directions' export use when it starts
      applying criteria — on McMurdo's own table, `DE-SPEC` with
      `specimens.dir_alpha95 <= 180` fails every fit (only 3 of 1,374
      specimens carry a `dir_alpha95`) under the strict rule and passes 1,298
      under the lenient one.
    - *Directions' export does not yet apply criteria* (its README says so;
      the plan's table row had it the other way). `magic_metadata.passing_rows`
      is written for that; wiring it into the Directions export as a
      "criteria" option — `DE-SPEC` on the specimen fits, `DE-SITE` on the
      site means — is a small next piece. Do it, or leave the export
      unfiltered and let MagIC's tools apply the criteria?
    - *`site.dir_polarity`* (singular) in McMurdo's `criteria.txt` — the
      check reads it as `sites` and says so, rather than refusing; the
      validator does not object to it either. Fine, or should the check
      insist on the data model's `table.column` form?

50. **Livdb on Convert (2026-09-02).** `livdb` is a registry Format now, a
    directory format like `tdt` (the converter reads every `.livdb`,
    `.livdb.csv` *and plain `.csv`* file in the directory), guessed from
    `.livdb`/`.livdb.csv` names. Two things to know:
    - The plain-`.csv` rule is the converter's own (`data_files/…/MW_P/
      perp.csv` is one), so a directory that also holds an unrelated CSV
      (a sample list, an orientation sheet) would be fed to the Livdb parser
      and probably fail the whole run. The registry does not guess `livdb`
      from a bare `.csv`, but it does not stop the converter reading one
      either. Should the converter check the first line for the Livdb header
      before parsing a `.csv`, or is "one Livdb export per directory" the
      working rule at Liverpool anyway?
    - The Format's examples are the shipped `TH_IZZI+`, `MW_IZZI+andC++` and
      `MW_P` directories (all five shipped sets convert; `MW_C+` and `MW_OT+`
      also carry `*_different_delimiters`/`*_old_delimiters` files that the
      extension rule skips). The character-delimited *site* convention raised
      `TypeError` (`len(site_splitted == 1)`) before today — nobody had used
      it through the CLI, so if you know a Liverpool user whose names need
      it, it is worth a real-data check.

51. **`requests` as a dependency (2026-09-02).** The library imports it guarded
    (`ipmag`, `data_model3`, `controlled_vocabularies3` fall back to `None`),
    but the hub's Download and Upload pages cannot work without it and it was
    in no requirement list — a fresh `pip install pmagpy[apps]` would have
    installed fine and failed at the first download. I put it in the `apps`
    extra (and `environment.yml`) rather than `install_requires`, so the
    library's core dependency list is unchanged. Would you rather it were a
    core requirement? `data_model3` fetches the data model with it when the
    local copy is absent, so the case exists.

    *Update to 49, criteria on export (2026-09-02)*: the export now applies criteria, **opt-in** (a
    checkbox on Directions' Export pane, off by default, disabled when the
    directory has no `criteria.txt` with DE-* rows). Choices made, all
    reversible: (a) a fit failing DE-SPEC is written `result_quality` 'b'
    and left out of the means — as a fit you flag by hand is — rather than
    dropped from the table; (b) a sample/site mean failing DE-SAMP/DE-SITE is
    written 'b' and left out of the level above (site means over samples,
    location means, poles); (c) blank statistics do **not** fail
    (`blank_fails=False`) — `pmag.grade` for `specimen_dir` never looked at
    alpha95 at all (its USEKEYS were MAD, n, moment, step range), so the old
    strict rule and this lenient one agree on the classic criteria and differ
    only where a criterion names a statistic the fit type lacks; (d) the
    Means and Poles tabs follow the checkbox, so the display is the export.
    On McMurdo: 76 of 992 fits fail (MAD > 5 or n < 4), 7 of 135 site means
    fail after that (k, n_samples, n_lines), the pole goes from N = 135 to
    128. Should the checkbox default to *on* when a criteria.txt exists?

52. **Ages on the Metadata page (2026-09-02).** *Fill ages* on the sites and
    locations tables does what ErMagicBuilder's age propagation did, without
    overwriting: an undated site takes its row in `ages.txt` (a row dates the
    lowest level it names, so a sample-dated row is not a site age), else its
    location's age; an undated location takes its row in `ages.txt`, else
    the span of its dated sites -- `age_low` = min of the sites' `age_low`,
    `age` and `age - age_sigma`, `age_high` the matching max -- when the
    sites agree on `age_unit` (no conversion between Ma, ka, Years BP ...;
    a mixed location is named in the message and left alone). The five age
    cells travel together, so a row with an `age` never gets someone else's
    `age_unit`. Decisions to confirm: (a) when a site has several rows in
    `ages.txt` (two dating methods) the *first in the file* wins, as
    `contribution_builder.propagate_ages` has always done -- would you rather
    it took the row with the smallest `age_sigma`, or left the site alone
    and asked?; (b) is `age ± age_sigma` the right contribution of a
    single-age site to the location span, or should the span use `age`
    alone (MagIC's own `propagate_min_max_up` uses `age` only)?; (c) samples
    and specimens carry no age in MagIC 3, so nothing is written below the
    site -- Pmag GUI 2.5 did copy ages onto samples; is anything lost?

53. **A conversion log beside the tables (2026-09-02).** `convert_files` now
    writes `pmagpy_conversions.json` into the MagIC directory: one entry per
    conversion that wrote tables (when, format, files, the fields given,
    append or replace, rows per table, files that failed), and Home says
    "converted from 10 CIT files · 2 Sep 2026" from it instead of counting
    what lies beside the tables. It is the second thing the apps leave in a
    data directory (with `backup_before_pmagpy_apps/`); MagIC's upload
    ignores both. Decisions to confirm: (a) a JSON sidecar, or would you
    rather the provenance lived inside MagIC — `measurements.description` or
    the contribution table has no column for a source file, so it would be a
    convention of ours; (b) the name — `pmagpy_conversions.json` is
    deliberate so a stranger can tell what left it; (c) scripts calling
    `convert_files` get the log too unless they pass `record=False` — right
    default for reproducibility, or should scripts be silent?

54. **`pmagpy-convert` — a new command rather than regenerated scripts**
    (2026-09-02). The registry now drives a command: `pmagpy-convert sio
    af.dat --codelist AF --location Hawaii --dir ~/MagIC/Hawaii`, with
    `pmagpy-convert FORMAT --help` generated from the fields. I chose a
    single new command over regenerating the 30 `programs/conversion_scripts`
    (`sio_magic.py -f … -loc …`): those keep flags people have in shell
    histories and cookbook notebooks, and rewriting them would change the
    flags' names (`-ncn` → `--samp-con`) without changing what they do. So
    the old scripts are untouched and the new command is the one with the
    page's names. Decisions: (a) is that the right split, or should the old
    scripts eventually print a one-line "also: pmagpy-convert sio …" hint
    and be deprecated? (b) option names are the registry field names with
    dashes (`--samp-con`, `--specnum`, `--labfield`), so they differ from
    the old `-ncn`/`-spc`/`-dc`; keep them as the canonical names or add the
    old short forms as aliases? (c) `--dir` defaults to the working
    directory and files not found there are looked for in `--dir` — the
    scripts' `-WD`/`-ID` split is collapsed into that; fine?

55. **AMS reduced from Kappabridge positions** (2026-09-02; closes the "not
    yet" in HUB_PLAN step 4). `anisotropy.reduce_measurements(m, "AMS")` fits
    the `LP-AN-MS` rows — one scalar susceptibility per `meas_orient_phi/
    theta` — with Jelinek's design (`pmag.design(15)` for the standard order;
    any six or more non-antipodal directions otherwise) and reproduces the
    tensors `k15_magic` wrote with `pmag.dok15_s` to 1e-8; the Reduce tab
    offers "AMS" when a directory has them and greys out the baseline box.
    Things I changed or chose along the way:
    - *Degrees of freedom by type.* `specimen_hext` used 3n − 6 for every
      tensor (right for a remanence: three components per position). For AMS
      a position is one number, so nf = n − 6 (as `dok15_s`, `aniso_magic`
      and Safyr use). A stored 15-position AMS tensor's F-critical and
      confidence ellipses were therefore ~13 % too small in the Eigenvectors
      tab for a single specimen; `specimen_hext(..., aniso_type)` now picks
      nf from `aniso_type`. Are there AMS tensors in MagIC whose
      `aniso_s_n_measurements` counts something other than positions (e.g.
      KLY4S files reporting 15 with Safyr's own σ) that this would misjudge?
    - *k15_magic fixes.* Each position's `method_codes` is now
      `LP-X:LP-AN-MS` (was `LP-X`, so the hub could not tell an AMS run from
      a bulk reading), and `experiment` is `specimen:LP-AN-MS` (it was
      `998.:LP-AN-MS` — `rec[0]` of the last data line, a susceptibility).
      The `measurement` names are still `1`…`15` per specimen (not unique
      across the table, which MagIC's validator dislikes) — rename to
      `specimen:LP-AN-MS-1` etc.?
    - *Method codes on a reduced AMS row*: `LP-AN-MS:AE-H`, like the AARM/ATRM
      rows (`LP-AN-ARM:AE-H`); k15_magic wrote `LP-X:AE-H:LP-AN-MS`. Add
      `LP-X`?
    - *Only the fifteen-position scheme is assumed* when `meas_orient_*` are
      blank; a 6- or 9-row susceptibility table without directions is
      refused (the remanence 6-scheme is antipodal and rank-3 for scalars).
    - Rotation to geographic/tilt coordinates of the reduced tensor is left
      to the table layer as for AARM/ATRM (k15_magic writes -1, 0 and 100
      rows itself); the Reduce tab writes only the specimen-frame row.
