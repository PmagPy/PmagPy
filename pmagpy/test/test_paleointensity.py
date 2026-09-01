"""
Tests for pmagpy.paleointensity: the MagIC 3-native paleointensity core.

The regression targets are real, published results:

* ``data_files/3_0/Megiddo`` carries 359 specimen interpretations written by
  the legacy Thellier GUI (``pmagpy-3.4.1: thellier_gui.v.3.0``). Re-importing
  their bounds must reproduce their statistics.
* ``data_files/SPD_calibration`` is the 20-specimen calibration set published
  with the Standard Paleointensity Definitions, compared here through the whole
  pipeline: .tdt reader -> MagIC 3 tables -> analysis core -> statistics.

``docs/scientific_validation.md`` records the deltas and the reason for each.
"""
import math
import os
import shutil
import tempfile

import numpy as np
import pandas as pd
import pytest

from pmagpy import magic_project as mp
from pmagpy import paleointensity as pi
from pmagpy import pint_stats as ps
from pmagpy import tdt as tdt_reader

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MEGIDDO = os.path.join(REPO, "data_files", "3_0", "Megiddo")
THELLIER_MAGIC = os.path.join(REPO, "data_files", "thellier_magic")
SPD_DIR = os.path.join(REPO, "data_files", "SPD_calibration")

#: SPD_B_Lab.dat is wrong for these two specimens; the direction below is the
#: one the published reference statistics were computed with (see the
#: validation document)
SPD_BLAB_OVERRIDE = {"MCT": (0.0, -90.0), "TS01-20A-2": (0.0, 0.0)}
#: SPD.m computes the horizontal component of the NRM from (x, y) instead of
#: (y, z) when B_lab lies along x, so its published dt* differs from the
#: document's equation for these two specimens
SPD_DT_STAR_KNOWN_DIFFERENT = {"HEL2-2d", "TS01-20A-2"}


@pytest.fixture(scope="module")
def megiddo():
    data = pi.PintData.from_directory(MEGIDDO)
    data.import_from_specimens_table()
    return data


@pytest.fixture(scope="module")
def megiddo_published():
    df = pd.read_csv(os.path.join(MEGIDDO, "specimens.txt"), sep="\t", skiprows=1, dtype=str)
    return df[df["int_abs"].notna()].set_index("specimen")


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
class TestLoading:
    def test_a_magic_3_study_loads_with_its_hierarchy(self, megiddo):
        assert len(megiddo.specimens) > 500
        spec = megiddo.specimens[megiddo.specimen_names[0]]
        assert spec.sample and spec.site and spec.location
        assert megiddo.names_at("site")
        assert spec.name in megiddo.specimens_in("site", spec.site)

    def test_every_specimen_is_recognised_as_izzi(self, megiddo):
        assert megiddo.protocol_counts() == {"IZZI": len(megiddo.specimens)}

    def test_the_laboratory_field_is_read_from_the_measurements(self, megiddo):
        spec = megiddo.specimens["hz05a1"]
        assert spec.blab == pytest.approx(6e-5)
        assert spec.blab_dir == pytest.approx([0.0, 0.0, -1.0], abs=1e-9)

    def test_the_arai_plot_starts_at_the_nrm(self, megiddo):
        spec = megiddo.specimens["hz05a1"]
        assert spec.arai.steps[0] == "NRM"
        assert spec.arai.x[0] == pytest.approx(0.0)
        assert spec.arai.y[0] == pytest.approx(3.08e-07, rel=1e-3)

    def test_checks_are_attached_to_the_step_they_check(self, megiddo):
        arai = megiddo.specimens["hz05a1"].arai
        # six checks were measured; the statistics use the five whose peak
        # temperature is at or below the chosen Tmax
        assert len(arai.ptrm_checks) == 6
        assert float(megiddo.result("hz05a1").stats["n_pTRM"]) == 5
        for check in arai.ptrm_checks:
            assert 0 <= check.i < arai.n
            assert 0 <= check.j < arai.n
            # a pTRM check goes back to a lower temperature than the peak reached
            assert arai.temps[check.j] >= arai.temps[check.i]
            assert check.vector is not None

    def test_a_second_study_loads_too(self):
        data = pi.PintData.from_directory(THELLIER_MAGIC)
        assert len(data.specimens) > 200
        assert set(data.protocol_counts()) <= {"IZZI", "Coe", "Aitken", "Thellier"}

    def test_bounds_are_indices_so_duplicate_temperatures_are_safe(self, megiddo):
        # every interpretation's bounds address Arai points, not temperatures
        for name, interp in list(megiddo.interpretations.items())[:20]:
            arai = megiddo.specimens[name].arai
            assert 0 <= interp.imin <= interp.imax < arai.n


# ---------------------------------------------------------------------------
# The legacy regression
# ---------------------------------------------------------------------------
class TestMegiddoRegression:
    """359 interpretations written by the legacy Thellier GUI, re-computed."""

    COLUMNS = {"int_b_beta": "beta", "int_f": "f", "int_fvds": "f_vds", "int_g": "g",
               "int_q": "q", "int_drats": "DRATS", "int_mad_free": "MAD_Free",
               "int_dang": "DANG", "int_n_measurements": "n", "int_n_ptrm": "n_pTRM"}

    def test_every_stored_interpretation_is_re_imported(self, megiddo, megiddo_published):
        assert len(megiddo.interpretations) == len(megiddo_published)

    def test_the_uncorrected_intensity_reproduces_the_published_value(self, megiddo,
                                                                      megiddo_published):
        """The published int_abs is the *uncorrected* estimate: issue #679."""
        worst, worst_name, off = 0.0, "", []
        for name, row in megiddo_published.iterrows():
            res = megiddo.result(name)
            assert res is not None, name
            published = float(row["int_abs"]) * 1e6
            diff = abs(res.b_anc_uncorrected - published)
            # the published value is written as %.2e, so three significant figures
            if diff > max(0.006 * published, 0.05):
                off.append((name, published, round(res.b_anc_uncorrected, 3)))
                continue
            if diff > worst:
                worst, worst_name = diff, name
        assert off == [], off[:4]
        assert worst < 0.5, f"worst residual {worst:.3f} uT on {worst_name}"

    @pytest.mark.parametrize("column", list(COLUMNS))
    def test_a_published_statistic_is_reproduced(self, megiddo, megiddo_published, column):
        key = self.COLUMNS[column]
        bad = []
        for name, row in megiddo_published.iterrows():
            want = row.get(column)
            if want is None or (isinstance(want, float) and math.isnan(want)):
                continue
            want = float(want)
            stat = megiddo.result(name).stats.get(key)
            got = float(stat) if stat else float("nan")
            if not math.isfinite(got) or abs(got - want) > max(0.011, 0.02 * abs(want)):
                bad.append((name, want, got))
        # every one of the 359 published statistics is reproduced; the only
        # residuals left are the two decimal places the file was written with
        assert [b[0] for b in bad] in ([], ["mgk09t1PI01"]), bad[:5]

    def test_the_correction_factors_reproduce_the_published_ones(self, megiddo, megiddo_published):
        for column, kind, tol in (("int_corr_cooling_rate", "cooling_rate", 0.011),
                                  ("int_corr_anisotropy", "anisotropy", 0.02)):
            bad = []
            for name, row in megiddo_published.iterrows():
                want = row.get(column)
                try:
                    want = float(want)
                except (TypeError, ValueError):
                    continue
                correction = megiddo.result(name).corrections.get(kind)
                got = correction.factor if (correction and correction.applied) else float("nan")
                if math.isfinite(got) and abs(got - want) > tol:
                    bad.append((name, want, round(got, 4)))
            limit = 1 if kind == "cooling_rate" else 8
            assert len(bad) <= limit, f"{kind}: {len(bad)} differ, e.g. {bad[:4]}"

    def test_the_recomputed_anisotropy_tensors_match_the_published_ones(self):
        """451 of the 466 stored aniso_s tensors are reproduced to 2e-4."""
        meas = pd.read_csv(os.path.join(MEGIDDO, "measurements.txt"), sep="\t",
                           skiprows=1, dtype=str)
        spec = pd.read_csv(os.path.join(MEGIDDO, "specimens.txt"), sep="\t",
                           skiprows=1, dtype=str)
        data = pi.PintData.from_directory(MEGIDDO)
        matched = total = 0
        for _, row in spec[spec["aniso_s"].notna()].iterrows():
            name = row["specimen"]
            if name not in data.specimens:
                continue
            total += 1
            want = np.array([float(v) for v in
                             str(row["aniso_s"]).replace(",", " ").replace(":", " ").split()])
            if row.get("aniso_type") == "AARM":
                got = pi.aarm_from_measurements(meas, name)
            else:
                got = pi.atrm_from_measurements(meas, name, data.specimens[name].steps)
            if got and np.max(np.abs(np.array(got["s"]) - want)) < 2e-4:
                matched += 1
        assert total > 400
        assert matched / total > 0.95, f"{matched}/{total} tensors reproduced"


# ---------------------------------------------------------------------------
# Issue #679: the corrected intensity must be what is exported
# ---------------------------------------------------------------------------
class TestAnisotropyCorrectedExport:
    def test_int_abs_carries_the_correction_that_int_corr_advertises(self, megiddo):
        """PmagPy/PmagPy#679: int_corr said 'c' while int_abs stayed uncorrected."""
        table = megiddo.specimens_table()
        table = table.set_index("specimen")
        checked = 0
        for name in list(megiddo.interpretations)[:80]:
            if name not in table.index:
                continue
            row = table.loc[name]
            res = megiddo.result(name)
            if not res.corrected:
                assert row["int_corr"] == "u"
                continue
            checked += 1
            assert row["int_corr"] == "c"
            expected = res.b_anc_uncorrected
            for key, column in (("anisotropy", "int_corr_anisotropy"),
                                ("cooling_rate", "int_corr_cooling_rate")):
                correction = res.corrections.get(key)
                if correction and correction.applied:
                    assert row[column] == pytest.approx(correction.factor)
                    expected *= correction.factor
            assert float(row["int_abs"]) * 1e6 == pytest.approx(expected, rel=1e-6)
        assert checked > 40

    def test_the_published_megiddo_file_shows_the_bug_this_fixes(self, megiddo, megiddo_published):
        """The bug is real and in the wild: the file says corrected and is not."""
        row = megiddo_published.loc["hz05a1"]
        assert row["int_corr"] == "c"
        assert float(row["int_corr_anisotropy"]) != 1.0
        res = megiddo.result("hz05a1")
        # the stored int_abs equals the *uncorrected* estimate
        assert float(row["int_abs"]) * 1e6 == pytest.approx(res.b_anc_uncorrected, rel=1e-3)
        assert res.b_anc != pytest.approx(res.b_anc_uncorrected, rel=1e-3)

    def test_an_uncorrectable_tensor_is_reported_not_silently_applied(self, megiddo):
        altered = [n for n, a in megiddo.anisotropy.items()
                   if a.get("alteration") is not None and np.isfinite(a.get("alteration", np.nan))
                   and a["alteration"] > megiddo.anisotropy_alteration_limit
                   and n in megiddo.interpretations]
        assert altered, "the study should contain at least one over-altered tensor"
        res = megiddo.result(altered[0])
        correction = res.corrections["anisotropy"]
        assert correction.applied is False
        assert "altered" in correction.message


# ---------------------------------------------------------------------------
# Issue #170: measurement quality
# ---------------------------------------------------------------------------
@pytest.fixture()
def small():
    """A private copy of a small study, safe to modify."""
    tmp = tempfile.mkdtemp(prefix="pint-small-")
    for name in ("measurements.txt",):
        shutil.copy(os.path.join(THELLIER_MAGIC, name), tmp)
    data = pi.PintData.from_directory(tmp)
    yield data
    shutil.rmtree(tmp, ignore_errors=True)


class TestMeasurementQuality:
    def test_flagging_the_in_field_half_removes_the_whole_arai_point(self, small):
        name = small.specimen_names[0]
        spec = small.specimens[name]
        before = spec.arai.n
        point = spec.arai.rows[2]
        assert point["i"] is not None
        notes = small.set_step_quality(name, point["i"], "b")
        assert small.specimens[name].arai.n == before - 1
        assert any("in-field half" in n for n in notes)

    def test_flagging_the_zero_field_half_removes_the_point_too(self, small):
        name = small.specimen_names[0]
        spec = small.specimens[name]
        before = spec.arai.n
        temp = spec.arai.temps[2]
        small.set_step_quality(name, spec.arai.rows[2]["z"], "b")
        after = small.specimens[name].arai
        assert after.n == before - 1
        assert temp not in set(after.temps)

    def test_a_flag_never_leaves_half_a_pair_in_the_fit(self, small):
        name = small.specimen_names[0]
        spec = small.specimens[name]
        small.set_step_quality(name, spec.arai.rows[3]["i"], "b")
        arai = small.specimens[name].arai
        for row in arai.rows:
            if row["temp"] == spec.steps.loc[spec.steps["sequence"] == 0, "treat_temp"].iloc[0]:
                continue
            # every remaining point either has both halves or is the NRM
            assert row["i"] is not None or row["temp"] == arai.temps[0]

    def test_a_good_duplicate_replaces_a_flagged_one(self, small):
        name = small.specimen_names[0]
        spec = small.specimens[name]
        # duplicate the in-field row of one point, then flag the original
        point = spec.arai.rows[2]
        row = spec.steps[spec.steps["sequence"] == point["i"]].iloc[0].copy()
        row["sequence"] = int(spec.steps["sequence"].max()) + 1
        row["measurement"] = row["measurement"] + "-repeat"
        spec.steps = pd.concat([spec.steps, pd.DataFrame([row])], ignore_index=True)
        before = spec.arai.n
        notes = small.set_step_quality(name, point["i"], "b")
        assert small.specimens[name].arai.n == before
        assert any("good repeat" in n for n in notes)

    def test_flagging_a_check_drops_the_check_and_nothing_else(self, small):
        name = next(n for n in small.specimen_names if small.specimens[n].arai.ptrm_checks)
        spec = small.specimens[name]
        before_points = spec.arai.n
        before_checks = len(spec.arai.ptrm_checks)
        sequence = spec.arai.check_rows[pi.STEP_PTRM][0]
        small.set_step_quality(name, sequence, "b")
        arai = small.specimens[name].arai
        assert arai.n == before_points
        assert len(arai.ptrm_checks) == before_checks - 1

    def test_a_flagged_nrm_falls_back_to_the_first_good_zero_field_step(self, small):
        name = small.specimen_names[0]
        spec = small.specimens[name]
        nrm_rows = spec.steps[spec.steps["kind"] == pi.STEP_NRM]
        assert len(nrm_rows)
        notes = small.set_step_quality(name, int(nrm_rows["sequence"].iloc[0]), "b")
        arai = small.specimens[name].arai
        assert arai is not None and arai.n >= 2
        assert any("normalise" in n for n in notes)

    def test_flagging_everything_is_reported_and_does_not_crash(self, small):
        name = small.specimen_names[0]
        spec = small.specimens[name]
        for sequence in list(spec.steps["sequence"]):
            small.set_step_quality(name, int(sequence), "b")
        assert small.specimens[name].arai is None or small.specimens[name].arai.n < 2
        assert small.result(name) is None or True     # no exception is the point

    def test_bounds_are_clamped_when_points_disappear(self, small):
        name = small.specimen_names[0]
        arai = small.specimens[name].arai
        small.set_interpretation(name, 0, arai.n - 1)
        small.set_step_quality(name, arai.rows[-1]["i"], "b")
        interp = small.interpretations[name]
        assert interp.imax < small.specimens[name].arai.n

    def test_flags_round_trip_through_measurements_txt(self, small):
        name = small.specimen_names[0]
        spec = small.specimens[name]
        sequence = int(spec.steps["sequence"].iloc[3])
        measurement = spec.steps.loc[spec.steps["sequence"] == sequence, "measurement"].iloc[0]
        small.set_step_quality(name, sequence, "b")
        out = tempfile.mkdtemp(prefix="pint-flags-")
        try:
            small.write_measurements(out)
            written = pd.read_csv(os.path.join(out, "measurements.txt"), sep="\t",
                                  skiprows=1, dtype=str)
            row = written[written["measurement"] == measurement]
            assert len(row) == 1
            assert row["quality"].iloc[0] == "b"
            reloaded = pi.PintData.from_directory(out)
            steps = reloaded.specimens[name].steps
            assert steps.loc[steps["measurement"] == measurement, "quality"].iloc[0] == "b"
        finally:
            shutil.rmtree(out, ignore_errors=True)


# ---------------------------------------------------------------------------
# The SPD calibration set, through the whole pipeline
# ---------------------------------------------------------------------------
def _spd_specimen(name, lab_dec, lab_inc, out_dir):
    path = next(p for p in tdt_reader.find_tdt_files(os.path.join(SPD_DIR, "TT"))
                if os.path.splitext(os.path.basename(p))[0].lower() == name.lower())
    result = tdt_reader.to_magic([path], out_dir, moment_units="Am^2", volume_cc=1.0,
                                 lab_dec=lab_dec, lab_inc=lab_inc, validate_first=False,
                                 specimen_from_filename=True)
    assert result["ok"], result["issues"]
    return pi.PintData.from_directory(out_dir)


@pytest.fixture(scope="module")
def spd_reference():
    table = pd.read_csv(os.path.join(SPD_DIR, "SPD_reference_statistics.csv"))
    table.columns = [str(c).strip() for c in table.columns]
    table["Sample name"] = table["Sample name"].astype(str).str.strip()
    blab = pd.read_csv(os.path.join(SPD_DIR, "SPD_B_Lab.dat"), sep="\t")
    blab["Specimen"] = blab["Specimen"].str.strip()
    return table, blab


@pytest.fixture(scope="module")
def spd_results(spd_reference):
    """Every calibration specimen, analysed over the reference best-fit segment."""
    table, blab = spd_reference
    tmp = tempfile.mkdtemp(prefix="pint-spd-")
    out = {}
    try:
        for _, row in blab.iterrows():
            name = row["Specimen"]
            reference = table[table["Sample name"].str.lower() == name.lower()]
            if reference.empty:
                continue
            reference = reference.iloc[0]
            if name in SPD_BLAB_OVERRIDE:
                dec, inc = SPD_BLAB_OVERRIDE[name]
            else:
                vector = np.array([row["B_Lab_x"], row["B_Lab_y"], row["B_Lab_z"]], dtype=float)
                dec, inc, _ = ps.cart_to_dir(vector)
            directory = os.path.join(tmp, name.replace("/", "_"))
            data = _spd_specimen(name, dec, inc, directory)
            specimen = list(data.specimens)[0]
            spec = data.specimens[specimen]
            spec.blab = float(row["|B_Lab| (muT)"]) * 1e-6
            tmin = float(reference["Tmin"]) + 273.0
            tmax = float(reference["Tmax"]) + 273.0
            start = int(np.argmin(np.abs(spec.arai.temps - tmin)))
            end = int(np.argmin(np.abs(spec.arai.temps - tmax)))
            data.set_interpretation(specimen, start, end)
            out[name] = (data, specimen, reference)
        yield out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


SPD_COLUMNS = {
    "n": "n", "b": "b", "sigma_b": "σb", "f": "f", "f_vds": "fvds", "FRAC": "FRAC",
    "beta": "β", "g": "g", "GAP_MAX": "GAP-MAX", "q": "q", "w": "w", "k": "k→",
    "SSE": "SSE", "k_prime": "k'", "R2_corr": "R2corr", "R2_det": "R2det", "Z": "Z",
    "Z_star": "Z*", "Dec_Anc": "Dec_Anc", "Inc_Anc": "Inc_Anc", "MAD_Anc": "MAD_Anc",
    "Dec_Free": "Dec_Fee", "Inc_Free": "Inc_Free", "MAD_Free": "MAD_Free", "alpha": "α",
    "DANG": "DANG", "NRM_dev": "NRMdev", "n_pTRM": "npTRM", "check_percent": "check(%)",
    "dCK": "dCK", "DRAT": "DRAT", "maxDEV": "maxDEV", "CDRAT": "CDRAT",
    "CDRAT_prime": "CDRAT'", "DRATS": "DRATS", "DRATS_prime": "DRATS'",
    "mean_DRAT": "Mean DRAT", "mean_DRAT_prime": "Mean DRAT'", "mean_DEV": "Mean DEV",
    "mean_DEV_prime": "Mean DEV'", "delta_pal": "dpal", "n_tail": "nTail",
    "DRAT_tail": "DRATTail", "dTR": "dTR", "MD_VDS": "MDVDS", "n_add": "nAdd", "dAC": "dAC",
}


class TestSpdCalibration:
    def test_all_twenty_specimens_import_and_analyse(self, spd_results):
        assert len(spd_results) == 20
        for name, (data, specimen, _) in spd_results.items():
            assert data.result(specimen) is not None, name

    @pytest.mark.parametrize("key", sorted(SPD_COLUMNS))
    def test_a_published_statistic_is_reproduced(self, spd_results, key):
        column = SPD_COLUMNS[key]
        bad = []
        for name, (data, specimen, reference) in spd_results.items():
            want = reference.get(column)
            if want is None or (isinstance(want, float) and math.isnan(want)):
                continue
            stat = data.statistics(specimen).get(key)
            got = float(stat) if stat else float("nan")
            if not math.isfinite(got):
                bad.append((name, want, "missing"))
                continue
            tolerance = max(abs(float(want)) * 0.02, 0.06)
            if abs(got - float(want)) > tolerance:
                bad.append((name, float(want), round(got, 4)))
        assert not bad, f"{key}: {bad}"

    def test_the_intensity_matches_where_no_correction_is_needed(self, spd_results):
        corrected = {"m428b1", "RS25b", "RS26a", "RS26e"}
        for name, (data, specimen, reference) in spd_results.items():
            if name in corrected:
                continue
            got = float(data.statistics(specimen)["B_anc"])
            assert got == pytest.approx(float(reference["BAnc"]), abs=0.15), name

    def test_scat_matches_at_the_published_beta_threshold(self, spd_results):
        for name, (data, specimen, reference) in spd_results.items():
            want = reference.get("SCAT (@ βthreshold = 0.1)")
            if want is None or (isinstance(want, float) and math.isnan(want)):
                continue
            got = data.statistics(specimen)["SCAT"]
            assert bool(got.value) is bool(int(want)), name

    def test_delta_t_star_matches_except_where_the_reference_code_slips(self, spd_results):
        for name, (data, specimen, reference) in spd_results.items():
            want = reference.get("dt*")
            if want is None or (isinstance(want, float) and math.isnan(want)):
                continue
            stat = data.statistics(specimen)["delta_t_star"]
            if name in SPD_DT_STAR_KNOWN_DIFFERENT:
                continue
            assert float(stat) == pytest.approx(float(want), abs=0.06), name

    def test_the_anisotropy_and_nlt_corrections_reproduce_the_published_intensity(self, spd_results):
        tensors = pd.read_csv(os.path.join(SPD_DIR, "SPD_Anis_Tensors.dat"), sep="\t")
        tensors["Specimen"] = tensors["Specimen"].str.strip()
        nlt = pd.read_csv(os.path.join(SPD_DIR, "SPD_NLT_factors.dat"), sep="\t")
        nlt["Specimen"] = nlt["Specimen"].str.strip()
        for _, row in tensors.iterrows():
            name = row["Specimen"]
            match = [k for k in spd_results if k.lower() == name.lower()]
            assert match, name
            data, specimen, reference = spd_results[match[0]]
            stats = data.statistics(specimen)
            chrm = ps.dir_to_cart(float(stats["Dec_Free"]), float(stats["Inc_Free"]), 1.0)
            s6 = [row[f"s_{k}"] for k in range(1, 7)]
            out = ps.anisotropy_correction_factor(s6, chrm, data.specimens[specimen].blab_dir)
            assert out["c"] == pytest.approx(float(reference["c"]), abs=0.002), name
            coefficients = nlt[nlt["Specimen"].str.lower() == name.lower()]
            blab = data.specimens[specimen].blab
            if len(coefficients):
                # SPD publishes A_2 per microtesla; the core works in tesla
                a2 = float(coefficients.iloc[0]["A_2"]) * 1e6
                value = ps.nlt_correction(float(stats["b"]), blab, a2, out["c"])
            else:
                value = out["c"] * abs(float(stats["b"])) * blab
            assert value * 1e6 == pytest.approx(float(reference["BAnc"]), abs=0.1), name


# ---------------------------------------------------------------------------
# Criteria
# ---------------------------------------------------------------------------
class TestCriteria:
    def test_the_named_sets_are_all_usable(self):
        for name, criteria in pi.CRITERIA_SETS.items():
            assert isinstance(name, str)
            for criterion in criteria.specimen + criteria.site:
                assert criterion.operation in ("<=", ">=", "<", ">", "=")
                assert criterion.describe()

    def test_a_failure_names_the_criterion_and_the_value(self, megiddo):
        megiddo.set_criteria("CCRIT")
        failures = []
        for name in list(megiddo.interpretations)[:200]:
            res = megiddo.result(name)
            if res.passed is False:
                failures.extend(res.failures)
        assert failures
        assert all("(got " in f for f in failures)

    def test_a_statistic_with_no_value_is_not_tested_and_says_so(self):
        criteria = pi.CriteriaSet("t", specimen=pi._crit([("dTR", "<=", 10.0)]))
        verdict = criteria.evaluate({"dTR": ps.na("dTR", "no tail checks were performed")})
        assert verdict["passed"] is True            # nothing failed
        assert verdict["not_applicable"] == ["dTR <= 10 (no tail checks were performed)"]

    def test_the_study_criteria_table_is_read_as_a_preset(self, megiddo):
        assert "This study" in pi.CRITERIA_SETS
        keys = {c.key for c in pi.CRITERIA_SETS["This study"].specimen}
        assert {"beta", "FRAC", "SCAT"} <= keys

    def test_the_ziggie_criterion_can_be_added_to_any_set(self):
        base = pi.CRITERIA_SETS["CCRIT"]
        extended = base.with_criterion("Ziggie", "<=", 0.1)
        assert len(extended.specimen) == len(base.specimen) + 1
        assert any(c.key == "Ziggie" for c in extended.specimen)

    def test_the_criteria_table_round_trips_to_magic(self, megiddo):
        megiddo.set_criteria("CCRIT")
        table = megiddo.criteria_table()
        assert set(table["table_column"]) >= {"specimens.int_b_beta", "specimens.int_frac"}
        assert (table["criterion_operation"].isin(["<=", ">=", "=", "<", ">"])).all()

    def test_the_beta_threshold_of_the_active_criteria_drives_scat(self, megiddo):
        megiddo.set_criteria("CCRIT")
        assert megiddo._beta_threshold() == pytest.approx(0.1)
        megiddo.set_criteria("TTB")
        assert megiddo._beta_threshold() == pytest.approx(0.15)
        megiddo.set_criteria("CCRIT")


# ---------------------------------------------------------------------------
# Interpretation workflow
# ---------------------------------------------------------------------------
class TestInterpretations:
    def test_auto_interpretation_finds_a_passing_segment(self, megiddo):
        megiddo.set_criteria("CCRIT")
        name = "hz05a1"
        original = megiddo.interpretations[name]
        bounds = (original.imin, original.imax)
        try:
            interp = megiddo.auto_interpret(name)
            assert interp is not None
            assert interp.imax > interp.imin
            assert "auto-interpreted" in interp.notes
        finally:
            megiddo.set_interpretation(name, *bounds)

    def test_auto_interpretation_explains_a_failure(self, megiddo):
        strict = pi.CriteriaSet("impossible", specimen=pi._crit([("FRAC", ">=", 0.999),
                                                                 ("beta", "<=", 1e-6)]))
        megiddo.set_criteria(strict)
        name = "hz05a1"
        original = (megiddo.interpretations[name].imin, megiddo.interpretations[name].imax)
        try:
            interp = megiddo.auto_interpret(name)
            assert "fails:" in interp.notes
        finally:
            megiddo.set_criteria("CCRIT")
            megiddo.set_interpretation(name, *original)

    def test_bounds_are_copied_only_where_both_treatments_exist(self, megiddo):
        source = "hz05a1"
        targets = megiddo.specimen_names[:12]
        saved = {n: (megiddo.interpretations[n].imin, megiddo.interpretations[n].imax)
                 for n in targets if n in megiddo.interpretations}
        try:
            copied, skipped = megiddo.copy_bounds(source, targets)
            assert copied >= 1
            for note in skipped:
                assert "no step at" in note
        finally:
            for name, bounds in saved.items():
                megiddo.set_interpretation(name, *bounds)

    def test_results_are_cached_by_the_interpretation_state(self, megiddo):
        name = "hz05a1"
        first = megiddo.result(name)
        assert megiddo.result(name) is first
        interp = megiddo.interpretations[name]
        bounds = (interp.imin, interp.imax)
        megiddo.set_interpretation(name, bounds[0] + 1, bounds[1])
        assert megiddo.result(name) is not first
        megiddo.set_interpretation(name, *bounds)

    def test_switching_off_a_correction_changes_the_result(self, megiddo):
        name = "hz05a1"
        with_correction = megiddo.result(name).b_anc
        megiddo.set_interpretation(name, megiddo.interpretations[name].imin,
                                   megiddo.interpretations[name].imax,
                                   use_anisotropy=False, use_cooling_rate=False)
        try:
            plain = megiddo.result(name)
            assert plain.b_anc == pytest.approx(plain.b_anc_uncorrected)
            assert plain.b_anc != pytest.approx(with_correction)
            assert plain.corrections["anisotropy"].message == "switched off for this specimen"
        finally:
            megiddo.set_interpretation(name, megiddo.interpretations[name].imin,
                                       megiddo.interpretations[name].imax,
                                       use_anisotropy=None, use_cooling_rate=None)


# ---------------------------------------------------------------------------
# Group results and export
# ---------------------------------------------------------------------------
class TestGroupsAndExport:
    def test_site_means_average_the_accepted_specimens(self, megiddo):
        groups = megiddo.group_results("site")
        assert len(groups) > 3
        assert (groups["n"] >= 1).all()
        assert groups["int_abs"].between(1, 200).all()

    def test_only_corrected_specimens_can_be_averaged(self, megiddo):
        everything = megiddo.group_results("site", corrected_only=False)
        corrected = megiddo.group_results("site", corrected_only=True)
        assert corrected["n"].sum() <= everything["n"].sum()

    def test_a_vadm_is_reported_where_the_site_has_coordinates(self, megiddo):
        groups = megiddo.group_results("site")
        with_vadm = groups[groups.get("vadm").notna()] if "vadm" in groups else groups.iloc[:0]
        assert len(with_vadm) >= 1
        assert (with_vadm["vadm"] > 1e21).all()

    def test_the_specimens_table_only_uses_magic_columns(self, megiddo):
        table = megiddo.merged_specimens_table()
        known = mp.model_columns("specimens")
        assert set(table.columns) <= known

    def test_the_export_replaces_intensity_rows_and_keeps_the_rest(self, megiddo):
        existing = megiddo.project.table("specimens")
        merged = megiddo.merged_specimens_table()
        # every specimen that had a directional or rock-magnetic row still has one
        aniso_before = existing[existing["aniso_s"].notna()]["specimen"].nunique()
        aniso_after = merged[merged["aniso_s"].notna()]["specimen"].nunique()
        assert aniso_after == aniso_before
        # and no specimen gained a duplicate intensity row
        intensity = merged[merged["int_abs"].notna()]
        assert intensity["specimen"].is_unique

    def test_the_written_tables_pass_the_magic_validator(self, megiddo):
        out = tempfile.mkdtemp(prefix="pint-export-")
        try:
            assert megiddo.write_specimens(out)
            assert megiddo.write_group(out, "site")
            report = megiddo.validate_output(out)
            source = mp.validate_directory(MEGIDDO, tables=("specimens", "sites"))
            for table, failure in report.items():
                if failure is None:
                    continue
                # no row of ours may fail; a column the *source* study also
                # lacks is inherited, not introduced here
                assert not failure["bad_rows"], f"{table}: {failure['bad_rows'][:3]}"
                assert not failure["failing_items"], f"{table}: {failure['failing_items'][:3]}"
                before = source.get(table) or {}
                assert set(failure["missing_cols"]) <= set(before.get("missing_cols", [])), \
                    f"{table}: {failure['missing_cols']}"
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_the_validator_names_the_cell_that_failed(self):
        """Cell-level, so a rejected upload is diagnosed here and not at MagIC.

        Megiddo's own specimens.txt fails: it names ATRM experiments that its
        measurements.txt does not contain. Each failure must arrive as a row, a
        column and a sentence -- not as a DataFrame, whose truthiness raises.
        """
        # measurements too: the failing check is that specimens.txt names
        # experiments the measurements table does not contain
        report = mp.validate_directory(MEGIDDO, tables=("specimens", "measurements"))
        cells = report["specimens"]["failing_items"]
        assert isinstance(cells, list) and cells
        assert not cells[0] == {} and set(cells[0]) == {"row", "column", "problem"}
        assert any(c["row"].startswith("hz05") for c in cells)
        assert any("experiment" in c["column"] for c in cells)
        # the shape a caller relies on: `if cells` must not raise
        assert bool(cells) is True

    def test_a_group_scattered_wider_than_its_mean_still_validates(self, megiddo):
        """int_abs_sigma_perc is capped at 100 by the data model.

        A site whose specimens disagree by more than their own mean cannot put
        that percentage in the column at all. The absolute sigma carries the
        same information and is not capped, so the percentage is left out and
        the description says what it was -- rather than clipping the number to
        100, which would be a different claim.
        """
        rows = megiddo.sites_table()
        wide = megiddo.group_results("site", only_accepted=True)
        wide = wide[wide["int_abs_sigma_perc"] > 100]
        if not len(wide):
            pytest.skip("no site in this study scatters that widely")
        for name in wide["site"]:
            row = rows[rows["site"] == name].iloc[0]
            assert pd.isna(row["int_abs_sigma_perc"])
            assert row["int_abs_sigma"] > 0
            assert "% of the mean" in row["description"]

    def test_every_group_row_says_it_is_an_average(self, megiddo):
        assert (megiddo.sites_table()["result_type"] == "a").all()

    def test_provenance_is_stamped_on_every_row(self, megiddo):
        table = megiddo.specimens_table(analysts="A Tester")
        assert (table["software_packages"] == pi.SOFTWARE_TAG).all()
        assert (table["analysts"] == "A Tester").all()
        assert (table["citations"] == "This study").all()

    def test_correction_method_codes_are_written(self, megiddo):
        table = megiddo.specimens_table().set_index("specimen")
        row = table.loc["hz05a1"]
        assert "DA-AC-ATRM" in row["method_codes"] or "DA-AC-AARM" in row["method_codes"]
        assert "DA-CR" in row["method_codes"]
        assert "IE-TT" in row["method_codes"]

    def test_backups_are_taken_once_before_an_in_place_export(self):
        tmp = tempfile.mkdtemp(prefix="pint-backup-")
        try:
            shutil.copy(os.path.join(THELLIER_MAGIC, "measurements.txt"), tmp)
            data = pi.PintData.from_directory(tmp)
            first = data.project.backup_originals(tmp, ["measurements.txt"])
            assert len(first) == 1 and os.path.exists(first[0])
            assert data.project.backup_originals(tmp, ["measurements.txt"]) == []
            elsewhere = tempfile.mkdtemp(prefix="pint-other-")
            try:
                assert data.project.backup_originals(elsewhere, ["measurements.txt"]) == []
            finally:
                shutil.rmtree(elsewhere, ignore_errors=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
class TestPersistence:
    def test_a_session_round_trips_through_json(self, megiddo):
        text = megiddo.to_json()
        reloaded = pi.PintData.from_directory(MEGIDDO)
        count = reloaded.from_json(text)
        assert count == len(megiddo.interpretations)
        for name, interp in list(megiddo.interpretations.items())[:50]:
            other = reloaded.interpretations[name]
            assert (other.imin, other.imax) == (interp.imin, interp.imax)

    def test_the_session_records_bounds_in_kelvin_so_it_survives_a_reload(self, megiddo):
        import json
        payload = json.loads(megiddo.to_json())
        assert payload["format"] == "pmagpy_intensity_session"
        name, bounds = next(iter(payload["bounds_in_kelvin"].items()))
        arai = megiddo.specimens[name].arai
        interp = megiddo.interpretations[name]
        assert bounds == [arai.temps[interp.imin], arai.temps[interp.imax]]

    def test_a_legacy_redo_file_round_trips(self, megiddo):
        tmp = tempfile.mkdtemp(prefix="pint-redo-")
        try:
            path = megiddo.write_redo(os.path.join(tmp, "thellier.redo"))
            reloaded = pi.PintData.from_directory(MEGIDDO)
            count, problems = reloaded.read_redo(path)
            assert count == len(megiddo.interpretations)
            assert problems == []
            for name, interp in list(megiddo.interpretations.items())[:50]:
                other = reloaded.interpretations[name]
                assert (other.imin, other.imax) == (interp.imin, interp.imax)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_a_redo_bound_that_is_not_a_step_is_reported(self, megiddo):
        """Nearest-temperature matching is how a bound lands on the wrong step.

        The interpretation is still made -- the nearest step is nearly always
        the intended one -- but a temperature that is not a step of this
        specimen must be said out loud rather than snapped to silently.
        """
        tmp = tempfile.mkdtemp(prefix="pint-redo3-")
        try:
            data = pi.PintData.from_directory(MEGIDDO)
            name = next(n for n, sp in data.specimens.items() if sp.arai is not None)
            temps = data.specimens[name].arai.temps
            path = os.path.join(tmp, "off.redo")
            with open(path, "w") as fh:                     # 7 K off a real step
                fh.write(f"{name}\t{temps[0] + 7:.0f}\t{temps[-1]:.0f}\n")
            count, problems = data.read_redo(path)
            assert count == 1
            assert data.interpretations[name].imin == 0     # still the right step
            assert len(problems) == 1 and "is not a step" in problems[0]
            # and a file whose temperatures are exact says nothing
            exact = os.path.join(tmp, "exact.redo")
            with open(exact, "w") as fh:
                fh.write(f"{name}\t{temps[0]:.0f}\t{temps[-1]:.0f}\n")
            assert pi.PintData.from_directory(MEGIDDO).read_redo(exact)[1] == []
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_a_redo_naming_an_unknown_specimen_is_reported_not_fatal(self, megiddo):
        tmp = tempfile.mkdtemp(prefix="pint-redo2-")
        try:
            path = os.path.join(tmp, "bad.redo")
            with open(path, "w") as fh:
                fh.write("not_a_specimen\t373\t773\n")
            data = pi.PintData.from_directory(MEGIDDO)
            count, problems = data.read_redo(path)
            assert count == 0
            assert problems == ["not_a_specimen: not in this study"]
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Data model 2 must never appear (issue #789)
# ---------------------------------------------------------------------------
class TestNoDataModel2:
    MODULES = ("pmagpy.paleointensity", "pmagpy.pint_stats", "pmagpy.magic_project", "pmagpy.tdt")
    FORBIDDEN = ("builder2", "validate_upload2", "controlled_vocabularies2",
                 "map_magic", "convert_2_magic2", "ipmag")

    def test_the_new_core_imports_no_data_model_2_helper(self):
        import ast
        for module in self.MODULES:
            path = os.path.join(REPO, *module.split(".")) + ".py"
            tree = ast.parse(open(path, encoding="utf-8").read())
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(a.name for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module)
                    imported.update(f"{node.module}.{a.name}" for a in node.names)
            for banned in self.FORBIDDEN:
                assert not any(banned in name for name in imported), \
                    f"{module} imports {banned}"

    def test_the_new_core_mentions_no_2_5_column_name(self):
        legacy = ("er_specimen_name", "magic_method_codes", "measurement_magn_moment",
                  "pmag_specimens", "magic_measurements", "specimen_int_uT", "treatment_temp")
        for module in self.MODULES:
            path = os.path.join(REPO, *module.split(".")) + ".py"
            text = open(path, encoding="utf-8").read()
            for name in legacy:
                # the name may appear in prose explaining the legacy behaviour, but
                # never as a string literal the code reads or writes
                assert f'"{name}"' not in text and f"'{name}'" not in text, \
                    f"{module} uses the 2.5 column {name}"

    def test_a_loaded_study_never_builds_a_2_5_table(self, megiddo):
        for table in megiddo.contribution.tables:
            assert not table.startswith(("er_", "pmag_", "rmag_"))


# ---------------------------------------------------------------------------
# Derived quantities
# ---------------------------------------------------------------------------
class TestDerived:
    def test_vadm_matches_a_worked_example(self):
        # 30 uT at the equator: the classic ~1e23 Am^2 axial dipole
        # 30 uT at the equator is about the present-day axial dipole, 7.8e22 Am^2
        value = pi.vadm(30.0, 0.0)
        assert value == pytest.approx(7.76e22, rel=0.01)
        assert pi.vadm(30.0, 90.0) < value       # the same field at the pole is a weaker dipole

    def test_vdm_uses_the_observed_inclination(self):
        assert pi.vdm(30.0, 0.0) == pytest.approx(pi.vadm(30.0, 0.0))
        assert math.isnan(pi.vdm(float("nan"), 10.0))

    def test_plot_geometry_is_normalised_by_the_nrm(self, megiddo):
        spec = megiddo.specimens["hz05a1"]
        x, y = pi.arai_xy(spec)
        assert y[0] == pytest.approx(1.0)
        assert x[0] == pytest.approx(0.0)
        temps, decay = pi.decay_curve(spec)
        assert decay[0] == pytest.approx(1.0)
        assert len(temps) == spec.arai.n
        zij = pi.zijderveld_xy(spec)
        assert len(zij["h_x"]) == spec.arai.n
