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
