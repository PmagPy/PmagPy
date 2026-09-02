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

