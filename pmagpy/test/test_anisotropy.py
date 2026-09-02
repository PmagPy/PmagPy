"""
Tests for ``pmagpy.anisotropy``: the tensor table layer over ``pmag``'s
anisotropy functions.

Anchored on closed-form cases (a diagonal tensor with known eigenvalues and
axes, shape parameters of chosen eigenvalues, a rotation by a right angle)
and on ``pmag`` itself (``doseigs``, ``dosgeo``/``dostilt``, ``dohext``,
``plot_ell``'s ellipse) and the McMurdo AARM specimens, whose stored
``aniso_ftest`` and ``aniso_v1`` were written by ``aarm_magic``.
"""
import os

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from pmagpy import anisotropy as aniso
from pmagpy import pmag

HERE = os.path.dirname(os.path.abspath(__file__))
MCMURDO = os.path.join(HERE, "..", "..", "data_files", "3_0", "McMurdo")


def read(table):
    return pd.read_csv(os.path.join(MCMURDO, table + ".txt"), sep="\t", header=1)


@pytest.fixture(scope="module")
def mcmurdo():
    return read("specimens"), read("samples")


# ----------------------------------------------------------------------------- parsing and shape
class TestParseAndShape:
    def test_aniso_s_is_parsed_whatever_the_spacing_and_formatted_back(self):
        s = aniso.parse_s("0.34:0.33 : 0.33:0.001:-0.002:0.003")
        assert_allclose(s, [0.34, 0.33, 0.33, 0.001, -0.002, 0.003])
        assert aniso.parse_s(aniso.format_s(s)).tolist() == pytest.approx(s.tolist())
        with pytest.raises(ValueError):
            aniso.parse_s("0.34:0.33")
        with pytest.raises(ValueError):
            aniso.parse_s("a:b:c:d:e:f")

    def test_shape_parameters_have_their_textbook_values(self):
        tau = np.array([0.4, 0.35, 0.25])
        p = aniso.shape_parameters(tau)
        assert p["aniso_p"] == pytest.approx(0.4 / 0.25)
        assert p["aniso_l"] == pytest.approx(0.4 / 0.35) and p["aniso_f"] == pytest.approx(0.35 / 0.25)
        assert p["aniso_ll"] == pytest.approx(np.log(0.4 / 0.35)) and p["aniso_ff"] == pytest.approx(np.log(0.35 / 0.25))
        eta = np.log(tau)
        assert p["aniso_pp"] == pytest.approx(np.exp(np.sqrt(2 * np.sum((eta - eta.mean()) ** 2))))
        assert p["aniso_t"] == pytest.approx((2 * eta[1] - eta[0] - eta[2]) / (eta[0] - eta[2]))
        assert p["aniso_vg"] == pytest.approx(np.degrees(np.arcsin(np.sqrt((0.35 - 0.25) / (0.4 - 0.25)))))
        assert p["aniso_perc"] == pytest.approx(100 * (0.4 - 0.25) / 1.0)
        assert p["aniso_total"] == pytest.approx(100 * (0.4 - 0.25) / (1.0 / 3))

    def test_a_sphere_is_neutral_and_the_shape_sign_follows_the_middle_eigenvalue(self):
        assert aniso.shape_parameters([1 / 3, 1 / 3, 1 / 3])["aniso_p"] == pytest.approx(1.0)
        assert aniso.shape_parameters([0.4, 0.39, 0.21])["aniso_t"] > 0        # oblate: tau2 near tau1
        assert aniso.shape_parameters([0.4, 0.21, 0.2])["aniso_t"] < 0         # prolate: tau2 near tau3


# ----------------------------------------------------------------------------- eigen and rotation
class TestEigen:
    def test_a_diagonal_tensor_gives_its_diagonal_as_eigenvalues_and_the_axes_as_eigenvectors(self):
        tau, V = aniso.eigen([0.30, 0.36, 0.34, 0, 0, 0])
        assert_allclose(tau, [0.36, 0.34, 0.30])
        # tau1 along y (east), tau2 along z (down), tau3 along x (north); lower hemisphere
        assert_allclose(V[0], [90, 0], atol=1e-9)
        assert_allclose(V[1][1], 90, atol=1e-9)
        assert_allclose(V[2], [0, 0], atol=1e-9)

    def test_eigenvalues_and_axes_agree_with_doseigs_in_float64(self, mcmurdo):
        specimens, _ = mcmurdo
        for s in specimens["aniso_s"].dropna().head(6):
            tau, V = aniso.eigen(s)
            t, v = pmag.doseigs(aniso.parse_s(s))
            assert_allclose(tau, np.real(t), rtol=1e-5)                 # doseigs works in float32
            for ours, theirs in zip(V, v):
                ang = pmag.angle(list(ours) + [1], [theirs[0], theirs[1], 1])[0]
                assert min(ang, 180 - ang) < 0.05                    # same axis, either sense
        assert aniso.eigen(s)[0].dtype == np.float64

    def test_rotation_to_geographic_and_tilt_corrected_matches_dosgeo_and_dostilt(self):
        s = np.array([0.35, 0.33, 0.32, 0.01, -0.005, 0.002])
        g = aniso.rotate_s(s, 30.0, 40.0, coordinates="g")
        assert_allclose(g, pmag.dosgeo(s, 30.0, 40.0), rtol=1e-6)
        t = aniso.rotate_s(s, 30.0, 40.0, 120.0, 25.0, coordinates="t")
        assert_allclose(t, pmag.dostilt(pmag.dosgeo(s, 30.0, 40.0), 120.0, 25.0), rtol=1e-6)
        assert_allclose(sum(g[:3]), 1.0, atol=1e-6)                  # a rotation keeps the trace

    def test_a_right_angle_rotation_moves_the_maximum_axis_where_it_should(self):
        # tau1 along specimen x; azimuth 90, dip 0 turns specimen x to geographic east
        s = np.array([0.36, 0.32, 0.32, 0, 0, 0])
        g = aniso.rotate_s(s, 90.0, 0.0, coordinates="g")
        _, V = aniso.eigen(g)
        assert_allclose(V[0], [90, 0], atol=1e-6)

    def test_missing_orientation_is_an_error(self):
        with pytest.raises(ValueError):
            aniso.rotate_s([0.34, 0.33, 0.33, 0, 0, 0], np.nan, 10.0, coordinates="g")
        with pytest.raises(ValueError):
            aniso.rotate_s([0.34, 0.33, 0.33, 0, 0, 0], 10.0, 10.0, coordinates="t")   # no bedding


# ----------------------------------------------------------------------------- the tensor table
class TestTensorTable:
    def test_mcmurdo_specimen_rows_are_taken_as_they_are(self, mcmurdo):
        specimens, samples = mcmurdo
        t = aniso.tensor_table(specimens, samples, "s")
        assert len(t) == 19 and set(t["source"]) == {"table"} and set(t["aniso_type"]) == {"AARM"}
        assert set(t["site"]) == {"mc15", "mc121", "mc142", "mc144", "mc217"}
        assert_allclose(t[["s11", "s22", "s33"]].sum(axis=1), 1.0, atol=1e-5)
        row = t[t["specimen"] == "mc121d1"].iloc[0]
        stored = specimens[(specimens["specimen"] == "mc121d1") & specimens["aniso_s"].notna()].iloc[0]
        tau1, dec, inc = (float(x) for x in stored["aniso_v1"].split(":"))
        assert row["tau1"] == pytest.approx(tau1, abs=1e-4)
        ang = pmag.angle([row["v1_dec"], row["v1_inc"], 1], [dec, inc, 1])[0]
        assert min(ang, 180 - ang) < 0.5                               # an axis: either sense of the stored vector

    def test_geographic_rows_are_rotated_from_the_sample_orientations(self, mcmurdo):
        specimens, samples = mcmurdo
        g = aniso.tensor_table(specimens, samples, "g")
        assert len(g) == 19 and set(g["source"]) == {"rotated"} and set(g["coordinates"]) == {"g"}
        s = aniso.tensor_table(specimens, samples, "s").set_index("specimen")
        row = g[g["specimen"] == "mc121d1"].iloc[0]
        orient = samples[samples["sample"] == "mc121d"].iloc[0]
        expected = pmag.dosgeo(s.loc["mc121d1", "s"], float(orient["azimuth"]), float(orient["dip"]))
        assert_allclose(row["s"], expected, rtol=1e-6)
        assert_allclose(sorted(g["tau1"]), sorted(s["tau1"]), rtol=1e-6)     # eigenvalues are rotation-invariant
        assert len(aniso.tensor_table(specimens, samples, "t")) == 0            # McMurdo has no bedding
        assert len(aniso.tensor_table(specimens, None, "g")) == 0             # and no rotation without samples

    def test_the_index_and_frame_counts(self, mcmurdo):
        specimens, samples = mcmurdo
        index = aniso.specimen_index(specimens)
        assert len(index) == 19 and set(index["frames"]) == {"s"}
        assert aniso.frames_present(specimens) == {"s": 19, "g": 0, "t": 0}

    def test_rows_already_in_the_frame_are_preferred_over_rotation(self):
        specimens = pd.DataFrame({"specimen": ["a", "a"], "sample": ["sa", "sa"], "aniso_type": ["AMS", "AMS"],
                                  "aniso_s": ["0.34:0.33:0.33:0:0:0", "0.35:0.33:0.32:0:0:0"],
                                  "aniso_tilt_correction": [-1, 0]})
        samples = pd.DataFrame({"sample": ["sa"], "azimuth": [45.0], "dip": [10.0]})
        g = aniso.tensor_table(specimens, samples, "g")
        assert len(g) == 1 and g.iloc[0]["source"] == "table"
        assert_allclose(g.iloc[0]["s"], [0.35, 0.33, 0.32, 0, 0, 0])
        assert aniso.frames_present(specimens) == {"s": 1, "g": 1, "t": 0}
        assert aniso.specimen_index(specimens).iloc[0]["frames"] == "sg"


# ----------------------------------------------------------------------------- statistics
class TestStatistics:
    def test_specimen_hext_reproduces_the_stored_f_statistic(self, mcmurdo):
        specimens, _ = mcmurdo
        rows = specimens[specimens["aniso_s"].notna()]
        for _, r in rows.head(5).iterrows():
            h = aniso.specimen_hext(r["aniso_s"], r["aniso_s_sigma"], r["aniso_s_n_measurements"])
            assert h["F"] == pytest.approx(r["aniso_ftest"], rel=0.02)
            assert h["F12"] == pytest.approx(r["aniso_ftest12"], rel=0.02, abs=0.02)
            assert isinstance(h["F"], float)                       # not the complex64 dohext hands back

    def test_group_statistics_are_real_valued_seeded_and_carry_the_mean(self, mcmurdo):
        specimens, samples = mcmurdo
        g = aniso.tensor_table(specimens, samples, "g")
        site = g[g["site"] == "mc121"]
        stats = aniso.group_statistics(list(site["s"]), bootstrap=True, n_bootstraps=200, random_seed=1)
        assert stats["n"] == 5 and stats["nf"] == 24                          # (n - 1) * 6
        assert_allclose(stats["s"], np.mean(np.vstack(site["s"]), axis=0), rtol=1e-6)
        assert stats["hext"]["F"] > float(stats["hext"]["F_crit"])            # the dike fabric is anisotropic
        assert all(isinstance(v, float) for k, v in stats["hext"].items() if not k.endswith("_crit"))
        boot = stats["bootstrap"]
        assert boot["taus"].shape == (200, 3) and boot["vectors"].shape == (200, 3, 2)
        assert boot["taus"].dtype == np.float64 and not boot["parametric"]
        again = aniso.group_statistics(list(site["s"]), bootstrap=True, n_bootstraps=200, random_seed=1)
        assert_allclose(again["bootstrap"]["taus"], boot["taus"])
        bounds = aniso.bootstrap_eigenvalue_bounds(boot["taus"])
        assert bounds["tau1"][0] < stats["tau1"] < bounds["tau1"][1]
        assert bounds["tau3"][0] < stats["tau3"] < bounds["tau3"][1]

    def test_a_group_needs_two_tensors_and_strings_are_accepted(self):
        with pytest.raises(ValueError):
            aniso.group_statistics([[0.34, 0.33, 0.33, 0, 0, 0]])
        stats = aniso.group_statistics(["0.34:0.33:0.33:0:0:0", "0.35:0.33:0.32:0.001:0:0"], hext=True)
        assert stats["n"] == 2 and stats["bootstrap"] is None and "F" in stats["hext"]

    def test_the_ellipse_is_plot_ells(self):
        pars = dict(pdec=40.0, pinc=30.0, beta=12.0, bdec=130.0, binc=0.0, gamma=6.0, gdec=220.0, ginc=60.0)
        ours = aniso.ellipse(**pars, n=201)
        from pmagpy import pmagplotlib
        pmag_pts = np.array(pmagplotlib.plot_ell(0, [pars[k] for k in ("pdec", "pinc", "beta", "bdec", "binc",
                                                                       "gamma", "gdec", "ginc")], plot=False))
        rad = np.pi / 180
        assert ours.shape == pmag_pts.shape == (201, 2)
        assert_allclose(ours[:, 1], pmag_pts[:, 1], atol=1e-9)
        assert_allclose(np.cos(ours[:, 0] * rad), np.cos(pmag_pts[:, 0] * rad), atol=1e-9)
        # a folded (over-wide) ellipse too
        wide = dict(pars, beta=120.0, gamma=100.0)
        ours = aniso.ellipse(**wide, n=201)
        pmag_pts = np.array(pmagplotlib.plot_ell(0, [wide[k] for k in ("pdec", "pinc", "beta", "bdec", "binc",
                                                                       "gamma", "gdec", "ginc")], plot=False))
        assert_allclose(ours[:, 1], pmag_pts[:, 1], atol=1e-9)

    def test_hext_and_bootstrap_ellipses_have_their_semi_axes_along_the_other_eigenvectors(self):
        # orthogonal axes: V1 north-horizontal, V2 east-horizontal, V3 down
        hpars = {"v1_dec": 0.0, "v1_inc": 0.0, "v2_dec": 90.0, "v2_inc": 0.0, "v3_dec": 0.0, "v3_inc": 90.0,
                 "e12": 10.0, "e13": 5.0, "e23": 8.0}
        def angular_extent(pts, centre):
            angles = np.array([pmag.angle([d, i, 1], centre + [1])[0] for d, i in pts])
            return angles.min(), angles.max()

        ells = aniso.hext_ellipses(hpars)
        lo, hi = angular_extent(ells["v1"], [0.0, 0.0])
        # a semi-angle e is exactly e degrees from the centre along its axis
        assert hi == pytest.approx(10.0, abs=1e-6)
        assert lo == pytest.approx(5.0, abs=1e-6)
        first = ells["v1"][0]                                  # phi = 0: 10 degrees from north towards V2 (east)
        assert first[0] == pytest.approx(10.0, abs=1e-6) and first[1] == pytest.approx(0.0, abs=1e-6)
        lo, hi = angular_extent(ells["v3"], [0.0, 90.0])
        assert hi == pytest.approx(8.0, abs=1e-6)              # V3: e13 along V1, e23 along V2
        bpars = {f"{v}_zeta": 6.0 for v in ("v1", "v2", "v3")}
        bpars.update({f"{v}_eta": 3.0 for v in ("v1", "v2", "v3")})
        bpars.update({"v1_zeta_dec": 90.0, "v1_zeta_inc": 0.0, "v1_eta_dec": 0.0, "v1_eta_inc": 90.0,
                      "v2_zeta_dec": 0.0, "v2_zeta_inc": 90.0, "v2_eta_dec": 0.0, "v2_eta_inc": 0.0,
                      "v3_zeta_dec": 0.0, "v3_zeta_inc": 0.0, "v3_eta_dec": 90.0, "v3_eta_inc": 0.0})
        boot = aniso.bootstrap_ellipses(hpars, bpars)
        lo, hi = angular_extent(boot["v2"], [90.0, 0.0])
        assert hi == pytest.approx(6.0, abs=1e-6)
        assert lo == pytest.approx(3.0, abs=1e-6)


# ----------------------------------------------------------------------------- MagIC rows
class TestMeanRecord:
    def test_the_record_uses_data_model_columns_and_the_frame_code(self, mcmurdo):
        import json
        specimens, samples = mcmurdo
        g = aniso.tensor_table(specimens, samples, "g")
        stats = aniso.group_statistics(list(g[g["site"] == "mc121"]["s"]))
        record = aniso.mean_record(stats, "AARM", "g")
        assert record["aniso_tilt_correction"] == 0 and record["aniso_type"] == "AARM"
        tau1, dec, inc = (float(x) for x in record["aniso_v1"].split(":"))
        # the cell rounds tau to six decimals and the direction to a tenth of a degree
        assert tau1 == pytest.approx(stats["tau1"], abs=5e-7) and dec == pytest.approx(stats["v1_dec"], abs=0.05)
        assert inc == pytest.approx(stats["v1_inc"], abs=0.05)
        assert record["aniso_ftest_quality"] == "g" and record["aniso_ftest"] == pytest.approx(stats["hext"]["F"], abs=1e-4)
        assert record["method_codes"] == "LP-AN-ARM:AE-H"
        text, payload = record["description"].split(" | ", 1)
        detail = json.loads(payload)
        assert text == "mean AARM tensor of 5 specimens" and detail["n_specimens"] == 5 and detail["nf"] == stats["nf"]
        np.testing.assert_allclose(detail["s"], stats["s"], atol=1e-8)
        assert detail["hext"]["F_crit"] == float(stats["hext"]["F_crit"]) and "bootstrap" not in detail
        with open(os.path.join(HERE, "..", "data_model", "data_model.json"), encoding="utf-8-sig") as fh:
            model = json.load(fh)
        site_columns = set(model["tables"]["sites"]["columns"])
        assert set(record) <= site_columns
        # with specimens and a bootstrap
        boot = aniso.group_statistics(list(g[g["site"] == "mc121"]["s"]), bootstrap=True, parametric=True,
                                      n_bootstraps=200, random_seed=1)
        record = aniso.mean_record(boot, "AARM", "g", specimens=list(g[g["site"] == "mc121"]["specimen"]))
        assert record["method_codes"] == "LP-AN-ARM:AE-H:AE-BS-P" and record["specimens"].startswith("mc121d1:")
        detail = json.loads(record["description"].split(" | ", 1)[1])
        assert detail["bootstrap"]["n_bootstraps"] == 200 and detail["bootstrap"]["parametric"]
        assert detail["bootstrap"]["v1_zeta"] == pytest.approx(boot["bootstrap"]["params"]["v1_zeta"], abs=0.01)
        lo, hi = detail["bootstrap"]["tau1_95"]
        assert lo < boot["tau1"] < hi
        assert set(record) <= site_columns
        assert aniso.mean_record(boot, "AMS", "s")["method_codes"].startswith("LP-AN-MS:")

    def test_the_mean_gets_a_row_of_its_own_and_is_replaced_on_a_re_save(self, mcmurdo):
        specimens, samples = mcmurdo
        sites = pd.read_csv(os.path.join(HERE, "..", "..", "data_files", "3_0", "McMurdo", "sites.txt"), sep="\t",
                            skiprows=1)
        g = aniso.tensor_table(specimens, samples, "g")
        stats = aniso.group_statistics(list(g[g["site"] == "mc121"]["s"]))
        record = aniso.mean_record(stats, "AARM", "g")
        before = len(sites)
        n_mc121 = int((sites["site"] == "mc121").sum())
        out = aniso.add_mean_to_table(sites, "site", "mc121", record)
        assert len(out) == before + 1 and len(sites) == before                     # a new row; the input untouched
        row = out.iloc[-1]
        assert row["site"] == "mc121" and row["location"] == "McMurdo" and row["citations"] == "This study"
        assert row["aniso_v1"] == record["aniso_v1"] and float(row["aniso_tilt_correction"]) == 0
        assert pd.isna(row["dir_dec"])                                              # nothing borrowed from the direction row
        assert (out["site"] == "mc121").sum() == n_mc121 + 1
        # the other rows are as they were
        for column in sites.columns:
            assert (out.iloc[:before][column].fillna("").astype(str).to_numpy()
                    == sites[column].fillna("").astype(str).to_numpy()).all(), column
        # same site, type and frame: replaced, not added; a save without Hext clears the F tests
        no_hext = aniso.mean_record(aniso.group_statistics(list(g[g["site"] == "mc121"]["s"]), hext=False), "AARM", "g")
        again = aniso.add_mean_to_table(out, "site", "mc121", no_hext)
        assert len(again) == before + 1 and pd.isna(again.iloc[-1]["aniso_ftest"])
        assert again.iloc[-1]["method_codes"] == "LP-AN-ARM"
        # another frame is another row
        s_stats = aniso.group_statistics(list(aniso.tensor_table(specimens, samples, "s").query("site == 'mc121'")["s"]))
        third = aniso.add_mean_to_table(again, "site", "mc121", aniso.mean_record(s_stats, "AARM", "s"))
        assert len(third) == before + 2

    def test_a_mean_can_start_a_table_and_a_sample_mean_names_its_site(self, mcmurdo):
        specimens, samples = mcmurdo
        g = aniso.tensor_table(specimens, samples, "g")
        stats = aniso.group_statistics(list(g[g["site"] == "mc121"]["s"]))
        record = aniso.mean_record(stats, "AARM", "g")
        fresh = aniso.add_mean_to_table(None, "site", "mc121", record, parent={"location": "McMurdo"})
        assert len(fresh) == 1 and fresh.iloc[0]["location"] == "McMurdo" and fresh.iloc[0]["site"] == "mc121"
        k = g[g["sample"] == "mc121k"]
        record = aniso.mean_record(aniso.group_statistics(list(k["s"])), "AARM", "g", specimens=list(k["specimen"]))
        out = aniso.add_mean_to_table(samples, "sample", "mc121k", record)
        row = out.iloc[-1]
        assert row["sample"] == "mc121k" and row["site"] == "mc121" and row["specimens"] == "mc121k1:mc121k2"
        with pytest.raises(ValueError):
            aniso.add_mean_to_table(samples, "location", "McMurdo", record)
        with pytest.raises(ValueError):
            aniso.add_mean_to_table(pd.DataFrame({"specimen": ["a"]}), "site", "mc121", record)
