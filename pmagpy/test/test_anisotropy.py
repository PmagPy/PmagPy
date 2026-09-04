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
        # the record fits a samples row and a sites row alike (the bundled model carries sites.aniso_ftest23,
        # missing from MagIC's 2025-02-26 export and reported upstream)
        assert set(record) <= set(model["tables"]["samples"]["columns"])
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


# ----------------------------------------------------------------------------- tensors from measurements
ATRM = os.path.join(HERE, "..", "..", "data_files", "atrm_magic")


@pytest.fixture(scope="module")
def mcmurdo_measurements():
    return pd.read_csv(os.path.join(MCMURDO, "measurements.txt"), sep="\t", header=1, low_memory=False)


class TestDesign:
    def test_the_standard_schemes_give_the_legacy_design(self):
        from pmagpy import ipmag
        for n in (6, 9, 15):
            A, B, H = aniso.design_matrix(aniso.POSITION_SCHEMES[n])
            legacy = ipmag.get_matrix(n)
            assert_allclose(A, legacy["A"], atol=1e-6)
            assert_allclose(B, legacy["B"], atol=1e-5)
            assert_allclose(H, legacy["tmpH"], atol=1e-6)

    def test_a_known_tensor_is_recovered_exactly_from_synthetic_moments(self):
        s = np.array([0.30, 0.35, 0.35, 0.01, -0.02, 0.005])
        a = np.array([[s[0], s[3], s[5]], [s[3], s[1], s[4]], [s[5], s[4], s[2]]])
        for n in (6, 9, 15):
            A, B, H = aniso.design_matrix(aniso.POSITION_SCHEMES[n])
            moments = 2e-6 * (H @ a.T)                                   # M_i = a · H_i, scaled
            fit = aniso.fit_tensor(moments, aniso.POSITION_SCHEMES[n])
            assert_allclose(fit["s"], s, atol=1e-12)
            assert fit["s_mean"] == pytest.approx(2e-6 / 3) and fit["nf"] == 3 * n - 6
            assert fit["sigma"] == pytest.approx(0, abs=1e-12) and fit["hext"] is None   # an exact fit has no scatter
            assert fit["tau1"] == pytest.approx(max(np.linalg.eigvalsh(a)))

    def test_too_few_or_coplanar_positions_are_refused(self):
        with pytest.raises(ValueError, match="six"):
            aniso.design_matrix(aniso.POSITION_SCHEMES[6][:5])
        with pytest.raises(ValueError, match="determine"):
            aniso.design_matrix([(d, 0.0) for d in (0, 30, 60, 90, 120, 150)])   # all in the horizontal plane
        with pytest.raises(ValueError, match="standard scheme"):
            aniso.field_directions(pd.DataFrame({"dir_dec": np.zeros(7)}))


class TestReduce:
    def test_aarm_from_mcmurdo_matches_the_stored_tensors(self, mcmurdo, mcmurdo_measurements):
        specimens, _ = mcmurdo
        tensors, problems = aniso.reduce_measurements(mcmurdo_measurements, "AARM")
        assert problems == {} and len(tensors) == 18                     # mc15c2 has a tensor but no measurements
        stored = specimens[specimens["aniso_s"].notna()].set_index("specimen")
        for _, row in tensors.iterrows():
            if row["specimen"] == "mc15h":                                # 8 positions measured: see below
                continue
            assert_allclose(aniso.parse_s(row["aniso_s"]), aniso.parse_s(stored.loc[row["specimen"], "aniso_s"]),
                            atol=1e-6)
            assert row["aniso_s_sigma"] == pytest.approx(float(stored.loc[row["specimen"], "aniso_s_sigma"]), abs=2e-6)
            assert row["aniso_ftest"] == pytest.approx(float(stored.loc[row["specimen"], "aniso_ftest"]), abs=1e-3)
            assert row["aniso_s_n_measurements"] == 9 and row["aniso_s_mean"] == pytest.approx(
                float(stored.loc[row["specimen"], "aniso_s_mean"]), rel=5e-3)          # stored to 3 figures
        row = tensors.set_index("specimen").loc["mc121d1"]
        assert row["method_codes"] == "LP-AN-ARM:AE-H" and row["aniso_ftest_quality"] == "g"
        assert row["aniso_v1"] == "0.356621:275.2:62.3" and row["description"] == "Critical F: 2.6848"
        assert row["experiments"] == "mc121d1-LP-AN-ARM" and row["aniso_s_unit"] == "Am^2"
        assert row["aniso_tilt_correction"] == -1 and "aniso_alt" not in tensors.columns
        # mc15h lacks the ninth position: its eight field directions are fit as measured
        h = tensors.set_index("specimen").loc["mc15h"]
        assert h["aniso_s_n_measurements"] == 8
        fit = aniso.specimen_tensor(mcmurdo_measurements[mcmurdo_measurements["specimen"] == "mc15h"], "AARM")
        assert fit["nf"] == 18 and fit["n_baselines"] == 8

    def test_the_baseline_is_the_zero_field_step_before_each_position(self, mcmurdo_measurements):
        rows = mcmurdo_measurements[mcmurdo_measurements["specimen"] == "mc121d1"]
        with_baseline = aniso.specimen_tensor(rows, "AARM")
        without = aniso.specimen_tensor(rows, "AARM", baseline=False)
        assert with_baseline["n_baselines"] == 9 and without["n_baselines"] == 0
        assert not np.allclose(with_baseline["s"], without["s"], atol=1e-4)
        # by hand: pair each LT-AF-I row with the LT-AF-Z row before it
        arm = rows[rows["method_codes"].str.contains("LP-AN-ARM")].sort_values("treat_step_num")
        xyz = np.array([pmag.dir2cart(list(v)) for v in arm[["dir_dec", "dir_inc", "magn_moment"]].to_numpy(float)])
        moments = xyz[1::2] - xyz[0::2]
        directions = arm.iloc[1::2][["treat_dc_field_phi", "treat_dc_field_theta"]].to_numpy(float)
        assert_allclose(with_baseline["s"], aniso.fit_tensor(moments, directions)["s"], atol=1e-12)
        with pytest.raises(ValueError, match="at least six"):
            aniso.specimen_tensor(arm.iloc[:8], "AARM")
        with pytest.raises(ValueError, match="no LP-AN-TRM"):
            aniso.specimen_tensor(rows, "ATRM")

    def test_atrm_without_baseline_matches_atrm_magic_and_with_it_gains_its_scatter(self):
        measurements = pd.read_csv(os.path.join(ATRM, "measurements.txt"), sep="\t", header=1, low_memory=False)
        stored = pd.read_csv(os.path.join(ATRM, "specimens.txt"), sep="\t", header=1).set_index("specimen")
        legacy, problems = aniso.reduce_measurements(measurements, "ATRM", baseline=False)
        assert problems == {} and len(legacy) == 30
        for _, row in legacy.iterrows():
            assert_allclose(aniso.parse_s(row["aniso_s"]), aniso.parse_s(stored.loc[row["specimen"], "aniso_s"]),
                            atol=1e-7)
            assert row["aniso_ftest"] == pytest.approx(float(stored.loc[row["specimen"], "aniso_ftest"]), abs=1e-3)
        assert "aniso_alt" not in legacy.columns and (stored["aniso_alt"] == 0).all()   # no checks: nothing to report
        assert legacy.iloc[0]["method_codes"] == "LP-AN-TRM:AE-H" and legacy.iloc[0]["aniso_s_n_measurements"] == 6
        # the six antipodal positions cancel a constant offset in the tensor but not in the residuals
        tensors, _ = aniso.reduce_measurements(measurements, "ATRM", baseline=True)
        a, b = tensors.set_index("specimen").loc["ak01a"], legacy.set_index("specimen").loc["ak01a"]
        assert_allclose(aniso.parse_s(a["aniso_s"]), aniso.parse_s(b["aniso_s"]), atol=1e-7)
        assert a["aniso_s_sigma"] < b["aniso_s_sigma"] / 3 and a["aniso_ftest"] > b["aniso_ftest"]
        fit = aniso.specimen_tensor(measurements[measurements["specimen"] == "ak01a"], "ATRM")
        assert fit["n_baselines"] == 6                                    # one zero-field heating serves all six
        # a chosen subset, and a protocol the table does not have
        some, _ = aniso.reduce_measurements(measurements, "ATRM", specimens=["ak01a", "nope"])
        assert list(some["specimen"]) == ["ak01a"]
        none, problems = aniso.reduce_measurements(measurements, "AARM")
        assert none.empty and problems == {}
        with pytest.raises(ValueError, match="AIRM"):
            aniso.reduce_measurements(measurements, "AIRM")

    def test_an_alteration_check_becomes_aniso_alt(self):
        megiddo = os.path.join(HERE, "..", "..", "data_files", "3_0", "Megiddo")
        measurements = pd.read_csv(os.path.join(megiddo, "measurements.txt"), sep="\t", header=1, low_memory=False)
        rows = measurements[measurements["specimen"] == "hz05a1"]
        fit = aniso.specimen_tensor(rows, "ATRM")
        stored = pd.read_csv(os.path.join(megiddo, "specimens.txt"), sep="\t", header=1)
        stored = stored[(stored["specimen"] == "hz05a1") & (stored["aniso_type"] == "ATRM")].iloc[0]
        assert_allclose(fit["s"], aniso.parse_s(stored["aniso_s"]), atol=2e-6)      # the offset cancels in s
        # the repeated first position (LT-PTRM-I) against its first measurement, in percent of their mean
        first, again = 2.12e-07, 2.09e-07
        assert fit["alteration"] == pytest.approx(100 * abs(first - again) / np.mean([first, again]), rel=1e-6)
        record = aniso.tensor_record(fit, "ATRM")
        assert record["aniso_alt"] == pytest.approx(fit["alteration"], abs=0.01) and record["aniso_s_n_measurements"] == 6


K15 = os.path.join(HERE, "..", "..", "data_files", "convert_2_magic", "k15_magic", "k15_example.dat")


@pytest.fixture(scope="module")
def k15_tables(tmp_path_factory):
    """The k15 example converted by ``k15_magic``: 8 specimens × 15 Kappabridge positions in
    measurements.txt, and the tensors ``pmag.dok15_s`` wrote to specimens.txt."""
    from pmagpy import convert_registry as reg
    d = str(tmp_path_factory.mktemp("k15"))
    result = reg.convert_files(reg.FORMATS["k15"], [K15], {"location": "Trinidad"}, d, record=False)
    assert result.ok, result.message
    m = pd.read_csv(os.path.join(d, "measurements.txt"), sep="\t", header=1, dtype=str)
    sp = pd.read_csv(os.path.join(d, "specimens.txt"), sep="\t", header=1, dtype=str)
    return m, sp


class TestSusceptibility:
    def test_the_fifteen_position_design_is_jelineks(self):
        A, B, H = aniso.susceptibility_design(aniso.POSITION_SCHEMES[15])
        legacy_A, legacy_B = pmag.design(15)
        assert_allclose(A, legacy_A, atol=1e-12)
        assert_allclose(B, legacy_B, atol=1e-12)
        assert A.shape == (15, 6) and B.shape == (6, 15)
        with pytest.raises(ValueError, match="six"):
            aniso.susceptibility_design(aniso.POSITION_SCHEMES[15][:5])
        with pytest.raises(ValueError, match="determine"):
            aniso.susceptibility_design([(d, 0.0) for d in (0, 30, 60, 90, 120, 150)])

    def test_a_known_tensor_is_recovered_from_scalar_susceptibilities(self):
        s = np.array([0.30, 0.35, 0.35, 0.01, -0.02, 0.005])
        a = np.array([[s[0], s[3], s[5]], [s[3], s[1], s[4]], [s[5], s[4], s[2]]])
        # six positions must not pair up antipodally: k(h) = k(-h), so the remanence 6-scheme is rank 3
        six = [(0., 0.), (90., 0.), (0., 90.), (45., 0.), (90., 45.), (0., 45.)]
        assert_allclose(aniso.susceptibility_design(six)[0], pmag.design(6)[0], atol=1e-12)
        with pytest.raises(ValueError, match="determine"):
            aniso.susceptibility_design(aniso.POSITION_SCHEMES[6])
        for scheme in (aniso.POSITION_SCHEMES[15], six):
            A, B, H = aniso.susceptibility_design(scheme)
            chi = 3e-3 * np.einsum("ij,jk,ik->i", H, a, H)                    # k_i = h_i · a · h_i, scaled
            fit = aniso.fit_susceptibility_tensor(chi, scheme)
            assert_allclose(fit["s"], s, atol=1e-12)
            assert fit["s_mean"] == pytest.approx(3e-3 / 3) and fit["nf"] == len(scheme) - 6
            assert fit["hext"] is None
            if fit["nf"]:
                assert fit["sigma"] == pytest.approx(0, abs=1e-12)
            else:
                assert np.isnan(fit["sigma"])                                # six positions leave no residual
        with pytest.raises(ValueError, match="15 measurement positions"):
            aniso.fit_susceptibility_tensor(np.ones(14), aniso.POSITION_SCHEMES[15])

    def test_k15_measurements_reduce_to_the_tensors_dok15_s_wrote(self, k15_tables):
        m, sp = k15_tables
        assert aniso.protocol_counts(m) == {"AMS": 8}
        assert list(m["experiment"].unique()[:2]) == ["tr245f:LP-AN-MS", "tr245g:LP-AN-MS"]     # not "998.:LP-AN-MS"
        tensors, problems = aniso.reduce_measurements(m, "AMS")
        assert problems == {} and len(tensors) == 8
        stored = sp[sp["aniso_s"].notna() & (sp["aniso_tilt_correction"] == "-1")].set_index("specimen")
        for _, row in tensors.iterrows():
            ref = stored.loc[row["specimen"]]
            assert_allclose(aniso.parse_s(row["aniso_s"]), aniso.parse_s(ref["aniso_s"]), atol=1e-8)
            assert row["aniso_s_sigma"] == pytest.approx(float(ref["aniso_s_sigma"]), abs=1e-8)
            assert row["aniso_s_mean"] == pytest.approx(float(ref["aniso_s_mean"]), rel=1e-6)   # bulk susceptibility
        first = tensors.iloc[0]
        assert first["aniso_type"] == "AMS" and first["aniso_s_unit"] == "SI" and first["aniso_s_n_measurements"] == 15
        assert first["method_codes"] == "LP-AN-MS:AE-H" and first["aniso_tilt_correction"] == -1
        assert "aniso_alt" not in tensors.columns
        # the rows are put back in position order, and the scheme stands in for missing directions
        shuffled, _ = aniso.reduce_measurements(m.sample(frac=1, random_state=1), "AMS")
        assert list(shuffled.set_index("specimen").loc[tensors["specimen"], "aniso_s"]) == list(tensors["aniso_s"])
        unoriented, _ = aniso.reduce_measurements(m.drop(columns=["meas_orient_phi", "meas_orient_theta"]), "AMS")
        assert list(unoriented["aniso_s"]) == list(tensors["aniso_s"])
        # baseline means nothing for a Kappabridge; a subset is a subset
        assert aniso.specimen_tensor(m[m["specimen"] == "tr245f"], "AMS", baseline=False)["n_baselines"] == 0
        some, _ = aniso.reduce_measurements(m, "AMS", specimens=["tr245g"])
        assert list(some["specimen"]) == ["tr245g"]

    def test_hext_uses_the_susceptibility_degrees_of_freedom(self, k15_tables):
        m, sp = k15_tables
        assert aniso.degrees_of_freedom(15, "AMS") == 9 and aniso.degrees_of_freedom(9, "AARM") == 21
        assert aniso.degrees_of_freedom(15) == 39
        tensors, _ = aniso.reduce_measurements(m, "AMS")
        row = tensors.iloc[0]
        by_type = aniso.specimen_hext(row["aniso_s"], row["aniso_s_sigma"], 15, "AMS")
        as_k15 = pmag.dohext(9, float(row["aniso_s_sigma"]), list(aniso.parse_s(row["aniso_s"])))
        assert float(by_type["F_crit"]) == pytest.approx(float(as_k15["F_crit"]))
        assert by_type["e12"] == pytest.approx(float(as_k15["e12"]))
        assert row["description"] == f"Critical F: {float(as_k15['F_crit']):.4f}"
        # read as a remanence (3n - 6 = 39) the same scatter would look tighter
        remanence = aniso.specimen_hext(row["aniso_s"], row["aniso_s_sigma"], 15)
        assert float(remanence["F_crit"]) < float(by_type["F_crit"]) and remanence["e12"] < by_type["e12"]
        with pytest.raises(ValueError, match="more positions"):
            aniso.specimen_hext(row["aniso_s"], row["aniso_s_sigma"], 6, "AMS")

    def test_a_bulk_susceptibility_row_is_not_an_anisotropy(self):
        # KLY4S / SUFAR files carry the instrument's tensor and one bulk measurement flagged LP-AN-MS
        bulk = pd.DataFrame({"specimen": ["a", "a"], "method_codes": ["LP-X:AE-H:LP-AN-MS", "LP-X"],
                             "susc_chi_volume": ["1e-3", "1.1e-3"]})
        assert len(aniso.ams_rows(bulk)) == 1 and aniso.protocol_counts(bulk) == {}
        tensors, problems = aniso.reduce_measurements(bulk, "AMS")
        assert tensors.empty and problems == {"a": "1 susceptibility positions; a tensor needs at least six"}
        seven = pd.DataFrame({"specimen": ["b"] * 7, "experiment": ["b:LP-AN-MS"] * 7, "susc_chi_volume": ["1e-3"] * 7})
        with pytest.raises(ValueError, match="fifteen-position"):
            aniso.specimen_tensor(seven, "AMS")
        assert aniso.protocol_counts(pd.DataFrame({"specimen": []})) == {} and aniso.protocol_counts(None) == {}
        mass = pd.DataFrame({"specimen": ["c"], "experiment": ["c:LP-AN-MS"], "susc_chi_mass": ["2e-6"],
                             "susc_chi_volume": [""]})
        assert aniso.susceptibility_values(mass).iloc[0] == 2e-6


class TestAddTensors:
    def test_tensors_replace_or_join_the_specimens_table(self, mcmurdo, mcmurdo_measurements):
        specimens, samples = mcmurdo
        tensors, _ = aniso.reduce_measurements(mcmurdo_measurements, "AARM")
        out = aniso.add_tensors_to_specimens_table(specimens, tensors)
        assert len(out) == len(specimens)                                  # every specimen already had an AARM row
        got = out[out["aniso_s"].notna()].set_index("specimen")
        assert got.loc["mc121d1", "aniso_s"] == tensors.set_index("specimen").loc["mc121d1", "aniso_s"]
        assert got.loc["mc121d1", "sample"] == "mc121d" and got.loc["mc121d1", "method_codes"] == "LP-AN-ARM:AE-H"
        assert got.loc["mc121d1", "aniso_s_mean"] == pytest.approx(5.973e-05, rel=1e-3)
        untouched = specimens[(specimens["specimen"] == "mc15c2") & specimens["aniso_s"].notna()]["aniso_s"].iloc[0]
        assert out[(out["specimen"] == "mc15c2") & out["aniso_s"].notna()]["aniso_s"].iloc[0] == untouched
        # a specimen with rows but no tensor gets a row; an unknown specimen gets one with its sample looked up
        bare = specimens[specimens["aniso_s"].isna()]
        out = aniso.add_tensors_to_specimens_table(bare, tensors.iloc[:2], samples)
        assert len(out) == len(bare) + 2
        assert out.iloc[-2]["specimen"] == "mc121d1" and out.iloc[-2]["sample"] == "mc121d"
        assert out.iloc[-2]["citations"] == "This study" and out.iloc[-2]["aniso_type"] == "AARM"
        assert "sample" not in tensors.columns                              # McMurdo's measurements have no sample column
        named = mcmurdo_measurements.assign(sample=mcmurdo_measurements["specimen"].str[:-1])
        named, _ = aniso.reduce_measurements(named, "AARM", specimens=["mc121d1"])
        assert list(named.columns[:2]) == ["specimen", "sample"] and named.iloc[0]["sample"] == "mc121d"
        fresh = aniso.add_tensors_to_specimens_table(None, named)
        assert len(fresh) == 1 and fresh.iloc[0]["sample"] == "mc121d"     # the measurements name the sample
        nameless = tensors.iloc[:1]
        listed = pd.DataFrame({"sample": ["mc121d"], "specimens": ["mc121d1:mc121d2"]})
        fresh = aniso.add_tensors_to_specimens_table(None, nameless, listed)
        assert fresh.iloc[0]["sample"] == "mc121d"                          # or a samples table listing its specimens
        alone = aniso.add_tensors_to_specimens_table(None, nameless)
        assert pd.isna(alone.iloc[0]["sample"])
        with pytest.raises(ValueError):
            aniso.add_tensors_to_specimens_table(pd.DataFrame({"sample": ["a"]}), tensors)
