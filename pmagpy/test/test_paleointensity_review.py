"""
Regression tests for the pre-beta review of PmagPy Intensity's core
(``pmagpy.paleointensity`` and ``pmagpy.pint_stats``): what the analyst
decides survives flagging, re-import and export, the statistics do not
depend on the moment unit, and every value computed reaches its MagIC column.

Every study is read from ``data_files`` (read only) or from a private copy
under ``tmp_path``; nothing is written into the repository's data.
"""
import json
import math
import os
import shutil

import numpy as np
import pandas as pd
import pytest

from pmagpy import magic_project as mp
from pmagpy import paleointensity as pi
from pmagpy import pint_stats as ps

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MEGIDDO = os.path.join(REPO, "data_files", "3_0", "Megiddo")
MCMURDO = os.path.join(REPO, "data_files", "3_0", "McMurdo")
THELLIER_MAGIC = os.path.join(REPO, "data_files", "thellier_magic")
MICROWAVE = os.path.join(REPO, "data_files", "convert_2_magic", "livdb_magic", "MW_IZZI+andC++")


def read_table(path):
    return pd.read_csv(path, sep="\t", skiprows=1, dtype=str)


def write_table(df, path, name):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"tab\t{name}\n")
        df.to_csv(fh, sep="\t", index=False)


@pytest.fixture(scope="module")
def megiddo():
    data = pi.PintData.from_directory(MEGIDDO)
    data.import_from_specimens_table()
    return data


@pytest.fixture(scope="module")
def megiddo_published():
    df = read_table(os.path.join(MEGIDDO, "specimens.txt"))
    return df[df["int_abs"].notna()].set_index("specimen")


@pytest.fixture()
def small(tmp_path):
    """A private copy of a small study (measurements only)."""
    shutil.copy(os.path.join(THELLIER_MAGIC, "measurements.txt"), tmp_path)
    return pi.PintData.from_directory(str(tmp_path))


# ---------------------------------------------------------------------------
# 1. Curvature criteria are on |k| and |k'| (PmagPy/PmagPy#246, F1)
# ---------------------------------------------------------------------------
class TestCurvatureMagnitude:
    def test_a_strongly_curved_negative_k_prime_fails_ccrit(self):
        crit = next(c for c in pi.CRITERIA_SETS["CCRIT"].specimen if c.key == "k_prime")
        assert crit.test(ps.ok("k_prime", -0.546)) is False
        assert crit.test(ps.ok("k_prime", 0.546)) is False
        assert crit.test(ps.ok("k_prime", -0.1)) is True
        verdict = pi.CRITERIA_SETS["CCRIT"].evaluate({"k_prime": ps.ok("k_prime", -0.546)})
        assert any("|k'|" in f for f in verdict["failures"])

    def test_k_is_tested_on_its_magnitude_too(self):
        assert pi.Criterion("k", "<=", 0.2).test(ps.ok("k", -0.3)) is False

    def test_the_criterion_says_it_is_a_magnitude(self):
        assert pi.Criterion("k_prime", "<=", 0.164).describe() == "|k'| <= 0.164"
        assert pi.Criterion("beta", "<=", 0.1).describe() == "beta <= 0.1"


# ---------------------------------------------------------------------------
# 2. SCAT does not depend on the moment unit
# ---------------------------------------------------------------------------
def _scaled(exp: ps.Experiment, factor: float) -> ps.Experiment:
    def vec(v):
        return None if v is None else np.asarray(v, dtype=float) * factor
    return ps.Experiment(
        x=exp.x * factor, y=exp.y * factor, temps=exp.temps, nrm_vectors=vec(exp.nrm_vectors),
        trm_vectors=vec(exp.trm_vectors), steps=exp.steps, blab=exp.blab, blab_orient=exp.blab_orient,
        ptrm_checks=[ps.PtrmCheck(c.i, c.j, c.x * factor, vec(c.vector)) for c in exp.ptrm_checks],
        tail_checks=[ps.TailCheck(c.i, c.y * factor, vec(c.vector)) for c in exp.tail_checks],
        additivity_checks=[ps.AdditivityCheck(c.i, c.j, c.x * factor, vec(c.vector))
                           for c in exp.additivity_checks])


#: statistics that carry the moment unit (everything else is a ratio or an angle)
MOMENT_UNIT_STATS = {"Y_int", "X_int", "VDS", "IZZI_MD"}
#: fitted iteratively (the circle of k), so reproduced to the fit's tolerance only
ITERATIVE_STATS = {"k", "k_prime", "SSE", "SSE_prime", "Ziggie", "Ziggie_rms"}


class TestScatIsUnitFree:
    @pytest.mark.parametrize("factor", [1e-4, 1e4])
    def test_scaling_every_moment_changes_no_verdict_and_no_statistic(self, factor):
        data = pi.PintData.from_directory(THELLIER_MAGIC)
        compared = scat_true = 0
        for name in data.specimen_names[:80]:
            exp = pi.experiment(data.specimens[name])
            n = exp.nmax
            if n < 5:
                continue
            for start, end in {(0, n - 1), (1, n - 2), (0, n // 2 + 1), (n // 3, n - 1)}:
                if end - start < 3:
                    continue
                base = ps.all_statistics(exp, start, end)
                scaled = ps.all_statistics(_scaled(exp, factor), start, end)
                assert bool(scaled["SCAT"].value) == bool(base["SCAT"].value), (name, start, end)
                scat_true += bool(base["SCAT"].value)
                for key, stat in base.items():
                    if key in MOMENT_UNIT_STATS or not stat or isinstance(stat.value, bool):
                        continue
                    other = scaled[key]
                    assert other, (name, key)
                    rel = 1e-3 if key in ITERATIVE_STATS else 1e-6
                    assert float(other) == pytest.approx(float(stat), rel=rel, abs=1e-9), (name, key)
                compared += 1
        assert compared > 100 and 0 < scat_true < compared

    def test_a_point_just_outside_the_box_is_outside_at_any_scale(self):
        # an ideal line, and one tail check 0.3% of the NRM below the lower edge of
        # the box: the SPD box test says it is outside; an absolute tolerance on
        # moment products called it "on the edge" once moments were small
        x = np.linspace(0.0, 0.8, 9)
        y = 1.0 - x
        temps = np.linspace(373.0, 853.0, 9)
        nrm = np.column_stack([y, np.zeros(9), np.zeros(9)])
        trm = np.column_stack([np.zeros(9), np.zeros(9), x])
        exp = ps.Experiment(x=x, y=y, temps=temps, nrm_vectors=nrm, trm_vectors=trm)
        stats = ps.all_statistics(exp, 0, 8)
        b = float(stats["b"])
        xbar, ybar = x.mean(), y.mean()
        # the box's inner edge joins the lower y intercept to the lower x intercept
        a2 = ybar - (b + 0.2 * abs(b)) * xbar
        a4 = -(ybar - (b - 0.2 * abs(b)) * xbar) / (b - 0.2 * abs(b))
        lower = a2 - a2 / a4 * x[4]
        exp.tail_checks = [ps.TailCheck(4, lower - 0.003 * y[0], None)]
        assert ps.all_statistics(exp, 0, 8)["SCAT"].value is False
        exp.tail_checks = [ps.TailCheck(4, lower + 0.003 * y[0], None)]
        assert ps.all_statistics(exp, 0, 8)["SCAT"].value is True
        exp.tail_checks = [ps.TailCheck(4, lower - 0.003 * y[0], None)]
        for factor in (1.0, 1e-9, 1e-12, 1e6):
            assert ps.all_statistics(_scaled(exp, factor), 0, 8)["SCAT"].value is False, factor


# ---------------------------------------------------------------------------
# 14. delta_pal leaves the first point as it is (SPD v1.2.0, section 5.3; issue246 F3)
# ---------------------------------------------------------------------------
class TestDeltaPalFirstPoint:
    def test_the_first_corrected_ptrm_is_the_first_ptrm(self):
        # a study whose first Arai point already carries a pTRM (no NRM step)
        x = np.array([0.1, 0.25, 0.4, 0.55, 0.7])
        y = np.array([0.95, 0.8, 0.62, 0.45, 0.3])
        trm = np.column_stack([np.zeros(5), np.zeros(5), x])
        nrm = np.column_stack([y, np.zeros(5), np.zeros(5)])
        check = ps.PtrmCheck(i=1, j=2, x=0.27, vector=np.array([0.0, 0.0, 0.27]))
        exp = ps.Experiment(x=x, y=y, temps=np.arange(5) * 50.0 + 473.0, nrm_vectors=nrm,
                            trm_vectors=trm, ptrm_checks=[check])
        got = float(ps.ptrm_check_statistics(exp, 0, 4)["delta_pal"])
        # by hand: TRM*_1 = TRM_1; the check difference accumulated from step 2 on
        # is added to the pTRMs after it (the reference implementation's C_{i-1})
        to_sum = np.zeros_like(trm)
        to_sum[1] = check.vector - trm[1]
        cumulative = np.cumsum(to_sum, axis=0)
        corr = np.array([np.linalg.norm(trm[0])] +
                        [np.linalg.norm(trm[j] + cumulative[j - 1]) for j in range(1, 5)])
        b = ps.york_regression(x, y)["b"]
        b_star = ps.york_regression(corr, y)["b"]
        assert got == pytest.approx(abs(100 * (b - b_star) / b), rel=1e-10)
        assert corr[0] == pytest.approx(0.1)

    def test_an_experiment_starting_at_the_nrm_is_unchanged(self, megiddo):
        # the first point is the NRM (pTRM zero), so the fix changes nothing there
        stat = megiddo.result("hz05a1").stats["delta_pal"]
        assert stat and np.isfinite(float(stat))
        assert megiddo.specimens["hz05a1"].arai.x[0] == 0.0


# ---------------------------------------------------------------------------
# 3. Flagging a step keeps the analyst's Tmin and Tmax
# ---------------------------------------------------------------------------
class TestFlaggingKeepsTheFit:
    def _setup(self, small):
        name = next(n for n in small.specimen_names if small.specimens[n].arai.n >= 10)
        arai = small.specimens[name].arai
        small.set_interpretation(name, 3, 8)
        return name, (float(arai.temps[3]), float(arai.temps[8]))

    def _bounds(self, small, name):
        arai, interp = small.specimens[name].arai, small.interpretations[name]
        return float(arai.temps[interp.imin]), float(arai.temps[interp.imax])

    def test_a_step_outside_the_fit(self, small):
        name, bounds = self._setup(small)
        before_n = small.result(name).stats["n"].value
        small.set_step_quality(name, small.specimens[name].arai.rows[1]["i"], "b")
        assert self._bounds(small, name) == bounds
        assert small.result(name).stats["n"].value == before_n

    def test_a_step_inside_the_fit(self, small):
        name, bounds = self._setup(small)
        before_n = small.result(name).stats["n"].value
        small.set_step_quality(name, small.specimens[name].arai.rows[5]["i"], "b")
        assert self._bounds(small, name) == bounds
        assert small.result(name).stats["n"].value == before_n - 1

    def test_a_step_at_the_edge_sets_the_fit_aside_and_back(self, small):
        name, bounds = self._setup(small)
        sequence = small.specimens[name].arai.rows[3]["z"]
        notes = small.set_step_quality(name, sequence, "b")
        assert name not in small.interpretations and any("set aside" in n for n in notes)
        small.set_step_quality(name, sequence, "g")
        assert self._bounds(small, name) == bounds

    def test_a_fit_set_aside_survives_the_session_file(self, small):
        name, bounds = self._setup(small)
        sequence = small.specimens[name].arai.rows[3]["z"]
        small.set_step_quality(name, sequence, "b")
        fresh = pi.PintData.from_directory(small.directory)
        fresh.from_json(small.to_json())
        assert name not in fresh.interpretations
        fresh.set_step_quality(name, sequence, "g")
        assert self._bounds(fresh, name) == bounds

    def test_a_new_choice_replaces_the_one_set_aside(self, small):
        name, bounds = self._setup(small)
        sequence = small.specimens[name].arai.rows[3]["z"]
        small.set_step_quality(name, sequence, "b")
        small.set_interpretation(name, 0, 4)
        new = self._bounds(small, name)
        small.set_step_quality(name, sequence, "g")
        assert self._bounds(small, name) == new


# ---------------------------------------------------------------------------
# 4. Re-import keeps the analyst's decisions
# ---------------------------------------------------------------------------
class TestImportKeepsDecisions:
    def test_a_rejected_result_comes_back_rejected(self, tmp_path):
        for name in ("measurements.txt", "specimens.txt", "samples.txt", "sites.txt", "criteria.txt"):
            shutil.copy(os.path.join(MEGIDDO, name), tmp_path)
        spec = read_table(os.path.join(MEGIDDO, "specimens.txt"))
        target = spec.index[spec["int_abs"].notna()][0]
        name = spec.loc[target, "specimen"]
        spec.loc[target, "result_quality"] = "b"
        write_table(spec, os.path.join(tmp_path, "specimens.txt"), "specimens")
        data = pi.PintData.from_directory(str(tmp_path))
        data.import_from_specimens_table()
        assert data.interpretations[name].quality == "b"
        assert not data.is_accepted(data.result(name))
        row = data.specimens_table().set_index("specimen").loc[name]
        assert row["result_quality"] == "b"

    def test_the_published_correction_choices_are_reproduced(self, megiddo, megiddo_published):
        """Megiddo: which corrections each published result carries, re-imported and exported.

        The legacy GUI wrote DA-AC-* also where it then applied a factor of
        1.00 (an altered tensor); the factor is the record of what was done.
        """
        exported = megiddo.specimens_table().set_index("specimen")
        wrong = []
        for name, row in megiddo_published.iterrows():
            codes = set(str(row["method_codes"]).split(":"))
            aniso = float(row["int_corr_anisotropy"]) if pd.notna(row["int_corr_anisotropy"]) else np.nan
            cooling = float(row["int_corr_cooling_rate"]) if pd.notna(row["int_corr_cooling_rate"]) else np.nan
            want = set()
            if codes & {"DA-AC-ATRM", "DA-AC-AARM"} and aniso != 1.0:
                want |= codes & {"DA-AC-ATRM", "DA-AC-AARM"}
            if "DA-CR" in codes and cooling != 1.0:
                want.add("DA-CR")
            if "DA-NL" in codes:
                want.add("DA-NL")
            got = {c for c in str(exported.loc[name, "method_codes"]).split(":") if c.startswith("DA-")}
            if got != want:
                wrong.append((name, sorted(want), sorted(got)))
        assert wrong == [], wrong[:5]

    def test_a_row_that_says_nothing_keeps_the_defaults(self, megiddo):
        interp = pi.Interpretation("x")
        assert megiddo._import_corrections(interp, pd.Series({"method_codes": "LP-PI-TRM"})) == []
        assert (interp.use_anisotropy, interp.use_nlt, interp.use_cooling_rate) == (None, None, None)

    def test_an_uncorrected_row_switches_every_correction_off(self, megiddo):
        interp = pi.Interpretation("hz05a1")
        megiddo._import_corrections(interp, pd.Series({"method_codes": "LP-PI-TRM", "int_corr": "u"}))
        assert (interp.use_anisotropy, interp.use_nlt, interp.use_cooling_rate) == (False, False, False)


# ---------------------------------------------------------------------------
# 5. Every value written has a MagIC column
# ---------------------------------------------------------------------------
class TestMagicColumns:
    def test_every_catalogue_column_is_in_the_data_model(self):
        specimens, sites = mp.model_columns("specimens"), mp.model_columns("sites")
        for key, spec in ps.CATALOG.items():
            if not spec.magic_column:
                continue
            model = sites if spec.category == "Group" else specimens
            assert spec.magic_column in model, (key, spec.magic_column)

    def test_the_names_the_review_found_wrong(self):
        assert ps.describe("c").magic_column == "int_corr_aniso"
        assert ps.describe("n_tail").magic_column == "int_n_ptrm_tail"
        assert ps.describe("n_add").magic_column == "int_n_ac"
        # int_z_md is the IZZI MD area (data model: "Paleointensity IZZI MD"), not Z*
        assert ps.describe("IZZI_MD").magic_column == "int_z_md"
        assert ps.describe("Z_star").magic_column == ""
        assert ps.describe("theta").magic_column == "int_theta"
        assert ps.describe("gamma").magic_column == "int_gamma"

    def test_nothing_the_export_computes_is_dropped_by_trim_to_model(self, megiddo):
        specimens = megiddo.specimens_table()
        assert "int_corr_aniso" in specimens.columns and specimens["int_corr_aniso"].notna().any()
        dropped = set(specimens.columns) - mp.model_columns("specimens")
        assert dropped == set(), dropped
        for level in ("site", "sample"):
            table = megiddo.sites_table(level=level)
            dropped = set(table.columns) - mp.model_columns(level + "s")
            assert dropped == set(), (level, dropped)
        warnings = []
        mp.trim_to_model(megiddo.merged_specimens_table(), "specimens", warnings)
        assert not any("int_" in w for w in warnings), warnings


# ---------------------------------------------------------------------------
# 6. Stored anisotropy tensors
# ---------------------------------------------------------------------------
TENSOR = [0.34, 0.33, 0.33, 0.004, -0.003, 0.002]


class TestStoredAnisotropy:
    @pytest.mark.parametrize("text", ["0.34:0.33:0.33:0.004:-0.003:0.002",
                                      "0.34 : 0.33 : 0.33 : 0.004 : -0.003 : 0.002",
                                      "0.34 0.33 0.33 0.004 -0.003 0.002",
                                      "[0.34, 0.33, 0.33, 0.004, -0.003, 0.002]"])
    def test_aniso_s_is_read_in_every_form(self, text):
        assert pi.parse_aniso_s(text) == pytest.approx(TENSOR)
        table = pd.DataFrame([{"specimen": "a", "aniso_s": text, "aniso_type": "AARM"}])
        tensor = pi.anisotropy_from_specimens_table(table, "a")
        assert tensor["s"] == pytest.approx(TENSOR) and tensor["type"] == "AARM"

    def test_both_stored_tensors_are_kept(self):
        table = pd.DataFrame([{"specimen": "a", "aniso_s": "1:1:1:0:0:0", "aniso_type": "ATRM"},
                              {"specimen": "a", "aniso_s": ":".join(map(str, TENSOR)), "aniso_type": "AARM"}])
        tensor = pi.anisotropy_from_specimens_table(table, "a")
        assert tensor["type"] == "AARM" and "ATRM" in tensor["alternatives"]

    @staticmethod
    def _aarm_block(with_step_numbers: bool, shuffle: bool = False) -> pd.DataFrame:
        """A 9-position AARM experiment of a known tensor, as a MagIC download writes it."""
        k = ps.anisotropy_tensor(TENSOR)
        positions = list(enumerate(ps.ANISOTROPY_POSITIONS[9]))
        if shuffle:
            positions = positions[::-1]
        rows, n = [], 0
        for _, (dec, inc) in positions:
            base = np.array([1e-7, -2e-7, 5e-8])
            arm = k @ ps.dir_to_cart(dec, inc, 1.0) * 5e-5 + base
            for vec, field, codes in ((base, 0.0, "LT-AF-Z:LP-AN-ARM"), (arm, 5e-5, "LT-AF-I:LP-AN-ARM")):
                d, i, m = ps.cart_to_dir(vec)
                n += 1
                rows.append({"specimen": "s1", "method_codes": codes, "dir_dec": d, "dir_inc": i,
                             "magn_moment": m, "treat_dc_field": field, "treat_ac_field": 0.18,
                             "treat_dc_field_phi": dec if field else 0.0,
                             "treat_dc_field_theta": inc if field else 90.0,
                             "measurement": str(n)})
                if with_step_numbers:
                    rows[-1]["treat_step_num"] = n
        return pd.DataFrame(rows)

    @pytest.mark.parametrize("with_step_numbers,shuffle", [(True, False), (False, False), (False, True)])
    def test_aarm_is_fitted_with_or_without_step_numbers(self, with_step_numbers, shuffle):
        tensor = pi.aarm_from_measurements(self._aarm_block(with_step_numbers, shuffle), "s1")
        assert tensor is not None and tensor["n_positions"] == 9
        expected = np.array(TENSOR) / sum(TENSOR[:3])
        assert tensor["s"] == pytest.approx(expected, abs=1e-6)


# ---------------------------------------------------------------------------
# 7. The laboratory field
# ---------------------------------------------------------------------------
class TestLabField:
    def _study(self, tmp_path, change):
        meas = read_table(os.path.join(THELLIER_MAGIC, "measurements.txt"))
        meas = change(meas)
        write_table(meas, os.path.join(tmp_path, "measurements.txt"), "measurements")
        return pi.PintData.from_directory(str(tmp_path))

    def test_a_field_recorded_in_microtesla_is_reported(self, tmp_path):
        def to_uT(meas):
            field = pd.to_numeric(meas["treat_dc_field"], errors="coerce")
            meas["treat_dc_field"] = (field * 1e6).astype(object).where(field.notna(), meas["treat_dc_field"])
            return meas
        data = self._study(tmp_path, to_uT)
        assert any("cannot be in tesla" in w for w in data.warnings)

    def test_a_missing_field_direction_is_unknown_not_plus_x(self, tmp_path):
        data = self._study(tmp_path, lambda m: m.drop(columns=["treat_dc_field_phi",
                                                               "treat_dc_field_theta"]))
        assert any("field direction" in w for w in data.warnings)
        name = data.specimen_names[0]
        assert data.specimens[name].blab_dir is None
        data.set_interpretation(name, 0, data.specimens[name].arai.n - 1)
        stats = data.statistics(name)
        for key in ("theta", "gamma", "delta_t_star"):
            assert not stats[key] and stats[key].state is not ps.State.OK, key
        assert stats["b"] and stats["B_anc"]


# ---------------------------------------------------------------------------
# 9. Flags identify one row, even where measurement names repeat
# ---------------------------------------------------------------------------
class TestFlagsByRow:
    def _duplicated_names(self, tmp_path):
        meas = read_table(os.path.join(THELLIER_MAGIC, "measurements.txt"))
        # every specimen's steps named 1, 2, 3 ... as in a MagIC download
        meas["measurement"] = meas.groupby("specimen").cumcount().add(1).astype(str)
        write_table(meas, os.path.join(tmp_path, "measurements.txt"), "measurements")
        return str(tmp_path)

    def test_a_flag_restores_onto_its_own_row_only(self, tmp_path):
        directory = self._duplicated_names(tmp_path)
        data = pi.PintData.from_directory(directory)
        name = data.specimen_names[0]
        sequence = int(data.specimens[name].steps["sequence"].iloc[4])
        data.set_step_quality(name, sequence, "b")
        text = data.to_json()
        fresh = pi.PintData.from_directory(directory)
        fresh.from_json(text)
        flagged = {n: int((s.steps["quality"] == "b").sum()) for n, s in fresh.specimens.items()}
        assert flagged[name] == 1
        assert sum(flagged.values()) == 1

    def test_an_old_session_is_still_read(self, tmp_path):
        directory = self._duplicated_names(tmp_path)
        data = pi.PintData.from_directory(directory)
        name = data.specimen_names[0]
        measurement = str(data.specimens[name].steps["measurement"].iloc[4])
        payload = json.loads(data.to_json())
        payload.pop("bad_steps")
        payload.pop("step_flag_changes", None)           # a version 1 file has neither
        payload["version"] = 1
        payload["bad_measurements"] = [measurement]
        data.from_json(json.dumps(payload))
        assert (data.specimens[name].steps["quality"] == "b").sum() == 1
        # the name is shared by other specimens' steps: all are flagged, and that is said
        assert any("more than one step" in w for w in data.warnings)


# ---------------------------------------------------------------------------
# 8 and 10. McMurdo: criteria.txt and the site means
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def mcmurdo(tmp_path_factory):
    directory = tmp_path_factory.mktemp("mcmurdo")
    for name in ("measurements.txt", "specimens.txt", "samples.txt", "sites.txt", "criteria.txt",
                 "locations.txt"):
        shutil.copy(os.path.join(MCMURDO, name), directory)
    data = pi.PintData.from_directory(str(directory))
    data.import_from_specimens_table()
    return data


class TestCriteriaTable:
    def test_the_study_s_site_criteria_are_read(self, mcmurdo):
        site = {c.key: c for c in pi.CRITERIA_SETS["This study"].site}
        assert site["N_samples"].value == 2 and site["dB_percent"].value == 15
        # sites.int_abs_sigma is in tesla; the statistic is in microtesla
        assert site["sd"].value == pytest.approx(-1e6)

    def test_an_export_keeps_every_criterion_it_does_not_own(self, mcmurdo, tmp_path):
        before = read_table(os.path.join(MCMURDO, "criteria.txt"))
        mcmurdo.set_criteria("CCRIT")
        try:
            path = mcmurdo.write_criteria(str(tmp_path))
        finally:
            mcmurdo.set_criteria(pi.CRITERIA_SETS["This study"])
        after = read_table(path)
        foreign = before[~before["criterion"].isin(["IE-SPEC", "IE-SITE"])]
        kept = after.merge(foreign, on=["criterion", "table_column", "criterion_operation",
                                        "criterion_value"])
        assert len(kept) == len(foreign) == 13          # DE-*, IE-SAMP, NPOLE, RPOLE
        spec = after[after["criterion"] == "IE-SPEC"]
        assert set(spec["table_column"]) == {f"specimens.{ps.describe(c.key).magic_column}"
                                             for c in pi.CRITERIA_SETS["CCRIT"].specimen}
        site = after[after["criterion"] == "IE-SITE"].set_index("table_column")
        assert float(site.loc["sites.int_abs_sigma", "criterion_value"]) == pytest.approx(6e-6)

    def test_the_legacy_either_or_on_the_scatter(self):
        cs = pi.CriteriaSet("t", site=(pi.Criterion("sd", "<=", -1e6), pi.Criterion("dB_percent", "<=", 15)))
        ok = cs.evaluate({"sd": ps.ok("sd", 3.0), "dB_percent": ps.ok("dB_percent", 10.0)}, "site")
        assert ok["passed"] is True
        bad = cs.evaluate({"sd": ps.ok("sd", 3.0), "dB_percent": ps.ok("dB_percent", 20.0)}, "site")
        assert bad["passed"] is False


class TestSiteMeans:
    def test_every_interpreted_site_is_written(self, mcmurdo):
        mcmurdo.set_criteria("CCRIT")
        try:
            table = mcmurdo.sites_table()
        finally:
            mcmurdo.set_criteria(pi.CRITERIA_SETS["This study"])
        interpreted = {mcmurdo.specimens[n].site for n in mcmurdo.interpretations}
        assert set(table["site"]) == interpreted
        failing = table[table["result_quality"] == "b"]
        assert len(failing) > 10
        assert failing["description"].str.contains("not accepted|fails").all()

    def test_the_published_means_survive_the_merge(self, mcmurdo):
        published = read_table(os.path.join(MCMURDO, "sites.txt"))
        published = published[mp.intensity_rows(published)]
        merged = mcmurdo.merged_group_table("site")
        merged = merged[mp.intensity_rows(merged)]
        assert set(published["site"]) <= set(merged["site"])

    def test_vadm_sigma_and_the_numbers_of_samples(self, mcmurdo):
        table = mcmurdo.sites_table()
        with_vadm = table[pd.to_numeric(table["vadm"], errors="coerce").notna()]
        assert len(with_vadm)
        row = with_vadm.iloc[0]
        sd, mean = float(row["int_abs_sigma"]), float(row["int_abs"])
        assert float(row["vadm_sigma"]) == pytest.approx(float(row["vadm"]) * sd / mean, rel=1e-9)
        assert (pd.to_numeric(table["int_n_samples"]) >= 1).all()
        assert (pd.to_numeric(table["int_n_samples"]) <= pd.to_numeric(table["int_n_specimens"])).all()

    def test_the_vdm_is_the_vadm_at_the_dipole_latitude_of_the_inclination(self):
        # an inclination of I gives the VADM of the dipole latitude atan(tan(I)/2)
        inc = 60.0
        plat = math.degrees(math.atan(math.tan(math.radians(inc)) / 2.0))
        assert pi.vdm(40.0, inc) == pytest.approx(pi.vadm(40.0, plat), rel=1e-12)


# ---------------------------------------------------------------------------
# 12. Microwave data are refused with the reason
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not os.path.isdir(MICROWAVE), reason="the livdb microwave example is not shipped")
def test_a_microwave_study_is_refused_with_the_reason():
    with pytest.raises(ValueError, match="microwave"):
        pi.PintData.from_directory(MICROWAVE)
