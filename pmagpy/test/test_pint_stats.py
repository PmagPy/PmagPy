"""
Tests for pmagpy.pint_stats: the Standard Paleointensity Definitions suite.

Three layers:

* equation-level tests, where a statistic is checked against its published
  definition on data simple enough to work out by hand;
* degeneracy and missing-data tests, which is where the -999 sentinels of the
  legacy code used to appear;
* the SPD v1.2.0 calibration data set (20 specimens, ``data_files/SPD_calibration``),
  compared against the reference statistics published with it.

The calibration comparison goes through the real pipeline -- the .tdt reader,
the MagIC 3 writer and the analysis core -- so it tests the whole path, not
just the arithmetic. Two published values are known to differ and are asserted
as such with the reason; see ``docs/scientific_validation.md``.
"""
import math
import os

import numpy as np
import pytest

from pmagpy import pint_stats as ps

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SPD_DIR = os.path.join(REPO, "data_files", "SPD_calibration")


# ---------------------------------------------------------------------------
# Typed results
# ---------------------------------------------------------------------------
class TestStat:
    def test_a_value_is_truthy_and_a_missing_one_is_not(self):
        assert ps.ok("b", 1.5)
        assert not ps.na("dTR", "no tail checks")
        assert not ps.unavailable("alpha_prime", "no independent direction")
        assert not ps.undefined("sigma_b", "n = 2")

    def test_no_statistic_is_ever_a_sentinel(self):
        for stat in (ps.na("x", ""), ps.unavailable("x", ""), ps.undefined("x", "")):
            assert stat.value is None
            assert stat.text() in ("n/a", "—", "undef.")
            assert math.isnan(float(stat))

    def test_a_non_finite_value_becomes_undefined_not_a_number(self):
        assert ps.ok("q", float("inf")).state is ps.State.UNDEFINED
        assert ps.ok("q", float("nan")).state is ps.State.UNDEFINED

    def test_the_reason_is_carried_with_the_state(self):
        stat = ps.na("delta_t_star", "no pTRM tail checks were performed")
        assert "tail checks" in stat.reason


# ---------------------------------------------------------------------------
# The paleointensity estimate
# ---------------------------------------------------------------------------
class TestYorkRegression:
    def test_a_perfect_line_has_the_exact_slope_and_no_error(self):
        x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        y = 10.0 - 2.0 * x
        fit = ps.york_regression(x, y)
        assert fit["b"] == pytest.approx(-2.0)
        assert fit["y_int"] == pytest.approx(10.0)
        assert fit["x_int"] == pytest.approx(5.0)
        assert fit["sigma_b"] == pytest.approx(0.0, abs=1e-12)

    def test_the_slope_is_the_standardized_major_axis_not_least_squares(self):
        # y-residual least squares would shrink the slope toward zero; the
        # standardized major axis is the ratio of the standard deviations
        rng = np.random.default_rng(0)
        x = np.linspace(0, 1, 12)
        y = -x + rng.normal(0, 0.05, 12)
        fit = ps.york_regression(x, y)
        expected = -np.std(y, ddof=1) / np.std(x, ddof=1)
        assert fit["b"] == pytest.approx(expected)

    def test_sigma_b_follows_spd_v1_2_and_uses_b_not_its_modulus(self):
        # SPD v1.2 change 1. With a negative slope the two forms differ, so a
        # hand evaluation of the published equation pins it down
        x = np.array([0.0, 1.0, 2.0, 3.0])
        y = np.array([3.0, 2.2, 0.9, 0.1])
        fit = ps.york_regression(x, y)
        u, v = x - x.mean(), y - y.mean()
        n = len(x)
        expected = math.sqrt((2 * np.sum(v ** 2) - 2 * fit["b"] * np.sum(u * v)) /
                             ((n - 2) * np.sum(u ** 2)))
        assert fit["sigma_b"] == pytest.approx(expected)
        wrong = math.sqrt((2 * np.sum(v ** 2) - 2 * abs(fit["b"]) * np.sum(u * v)) /
                          ((n - 2) * np.sum(u ** 2)))
        assert fit["sigma_b"] != pytest.approx(wrong)

    def test_two_points_leave_the_error_undefined_rather_than_zero(self):
        fit = ps.york_regression(np.array([0.0, 1.0]), np.array([1.0, 0.0]))
        assert fit["b"] == pytest.approx(-1.0)
        assert math.isnan(fit["sigma_b"])

    def test_a_vertical_segment_does_not_raise(self):
        fit = ps.york_regression(np.zeros(4), np.arange(4.0))
        assert math.isnan(fit["b"])


class TestVectorDifferenceSum:
    def test_a_straight_decay_sums_to_the_starting_length(self):
        v = np.array([[0.0, 0.0, 4.0], [0.0, 0.0, 3.0], [0.0, 0.0, 1.0], [0.0, 0.0, 0.0]])
        assert ps.vector_difference_sum(v) == pytest.approx(4.0)

    def test_a_direction_change_adds_to_the_sum(self):
        v = np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 0.0]])
        assert ps.vector_difference_sum(v) == pytest.approx(math.sqrt(2) + 1.0)


# ---------------------------------------------------------------------------
# Arai statistics
# ---------------------------------------------------------------------------
def straight_experiment(n=8, slope=-1.0, nrm=1.0, blab=40.0):
    """An ideal Arai plot: a straight line from (0, NRM) to (NRM/|b|, 0)."""
    x = np.linspace(0.0, nrm / abs(slope), n)
    y = nrm + slope * x
    temps = np.linspace(293.0, 873.0, n)
    nrm_vectors = np.column_stack([np.zeros(n), np.zeros(n), y])
    trm_vectors = np.column_stack([np.zeros(n), np.zeros(n), -x])
    steps = ["NRM"] + ["ZI" if i % 2 else "IZ" for i in range(1, n)]
    return ps.Experiment(x=x, y=y, temps=temps, nrm_vectors=nrm_vectors,
                         trm_vectors=trm_vectors, steps=steps, blab=blab,
                         blab_orient=np.array([0.0, 0.0, -1.0]))


class TestAraiStatistics:
    def test_an_ideal_line_gives_a_perfect_fit(self):
        exp = straight_experiment()
        s = ps.arai_statistics(exp, 0, 7)
        assert float(s["b"]) == pytest.approx(-1.0)
        assert float(s["B_anc"]) == pytest.approx(40.0)
        assert float(s["f"]) == pytest.approx(1.0)
        assert float(s["FRAC"]) == pytest.approx(1.0)
        assert float(s["beta"]) == pytest.approx(0.0, abs=1e-7)
        assert float(s["R2_corr"]) == pytest.approx(1.0)
        assert s["SCAT"].value is True

    def test_the_gap_factor_reaches_its_limit_for_evenly_spaced_points(self):
        exp = straight_experiment(n=6)
        s = ps.arai_statistics(exp, 0, 5)
        assert float(s["g"]) == pytest.approx(float(s["g_lim"]))

    def test_q_is_f_times_g_over_beta(self):
        exp = straight_experiment(n=7)
        exp.y = exp.y + np.array([0, 0.01, -0.01, 0.02, -0.015, 0.005, 0])
        s = ps.arai_statistics(exp, 0, 6)
        assert float(s["q"]) == pytest.approx(float(s["f"]) * float(s["g"]) / float(s["beta"]))

    def test_w_is_q_over_root_n_minus_two(self):
        exp = straight_experiment(n=7)
        exp.y = exp.y + np.array([0, 0.01, -0.01, 0.02, -0.015, 0.005, 0])
        s = ps.arai_statistics(exp, 0, 6)
        assert float(s["w"]) == pytest.approx(float(s["q"]) / math.sqrt(5))

    def test_fewer_than_three_points_is_undefined_not_wrong(self):
        exp = straight_experiment()
        s = ps.arai_statistics(exp, 0, 1)
        assert s["b"].state is ps.State.UNDEFINED
        assert "3" in s["b"].reason

    def test_a_missing_laboratory_field_makes_the_intensity_unavailable(self):
        exp = straight_experiment()
        exp.blab = float("nan")
        s = ps.arai_statistics(exp, 0, 7)
        assert s["B_anc"].state is ps.State.UNAVAILABLE
        assert float(s["b"]) == pytest.approx(-1.0)     # the slope is still fine

    def test_s_follows_the_equation_spd_prints(self):
        exp = straight_experiment(n=6)
        exp.y = exp.y + np.array([0, 0.02, -0.02, 0.02, -0.02, 0])
        s = ps.arai_statistics(exp, 0, 5)
        fit = ps.york_regression(exp.x, exp.y)
        n = 6
        var_x = float(np.sum((exp.x - exp.x.mean()) ** 2)) / (n - 1)
        var_y = float(np.sum((exp.y - exp.y.mean()) ** 2)) / (n - 1)
        resid = exp.y - fit["b"] * exp.x - fit["y_int"]
        expected = float(np.sum(resid ** 2)) / (fit["b"] ** 2 * var_x + var_y)
        assert float(s["S"]) == pytest.approx(expected)
        assert float(s["S_prime"]) == pytest.approx(expected / (n - 2))
        assert 0.0 <= float(s["p_chi2"]) <= 1.0

    def test_york_weighting_gives_s_prime_an_expectation_of_one(self):
        """With the measurement uncertainties supplied, S' is chi-squared per dof.

        SPD prints the *data* variances in the denominator of S, which makes S'
        vanishingly small for a good fit rather than averaging one; York's own
        weighting needs the measurement uncertainties, and the Experiment can
        carry them.
        """
        values = []
        for seed in range(60):
            rng = np.random.default_rng(seed)
            exp = straight_experiment(n=10)
            exp.y = exp.y + rng.normal(0, 0.01, 10)
            exp.nrm_vectors = np.column_stack([np.zeros(10), np.zeros(10), exp.y])
            exp.sigma_x, exp.sigma_y = 1e-9, 0.01
            s = ps.arai_statistics(exp, 0, 9)
            values.append(float(s["S_prime"]))
            assert 0.0 <= float(s["p_chi2"]) <= 1.0
        assert 0.6 < float(np.mean(values)) < 1.6

    def test_a_scattered_segment_fails_scat_and_a_clean_one_passes(self):
        clean = straight_experiment(n=6)
        assert ps.arai_statistics(clean, 0, 5)["SCAT"].value is True
        noisy = straight_experiment(n=6)
        noisy.y = noisy.y + np.array([0, 0.25, -0.25, 0.25, -0.25, 0])
        assert ps.arai_statistics(noisy, 0, 5)["SCAT"].value is False

    def test_scat_includes_a_check_that_falls_outside_the_box(self):
        exp = straight_experiment(n=6)
        assert ps.arai_statistics(exp, 0, 5)["SCAT"].value is True
        exp.ptrm_checks = [ps.PtrmCheck(i=2, j=4, x=exp.x[2] + 0.5)]
        assert ps.arai_statistics(exp, 0, 5)["SCAT"].value is False

    def test_izzi_md_is_not_applicable_to_a_coe_experiment(self):
        exp = straight_experiment(n=6)
        exp.steps = ["NRM"] + ["ZI"] * 5
        assert ps.arai_statistics(exp, 0, 5)["IZZI_MD"].state is ps.State.NOT_APPLICABLE

    def test_izzi_md_is_zero_for_a_perfectly_straight_izzi_plot(self):
        exp = straight_experiment(n=8)
        assert abs(ps.izzi_md(exp.x, exp.y, exp.steps)) < 1e-9

    def test_izzi_md_grows_with_zig_zag(self):
        small = straight_experiment(n=9)
        small.y = small.y + np.array([0, .01, -.01, .01, -.01, .01, -.01, .01, 0])
        big = straight_experiment(n=9)
        big.y = big.y + np.array([0, .05, -.05, .05, -.05, .05, -.05, .05, 0])
        assert abs(ps.izzi_md(big.x, big.y, big.steps)) > abs(ps.izzi_md(small.x, small.y, small.steps))


class TestCurvature:
    def test_a_straight_line_has_almost_no_curvature(self):
        x = np.linspace(0, 1, 10)
        curv = ps.arai_curvature(x, 1 - x)
        assert abs(curv["k"]) < 1e-3

    def test_a_known_circle_is_recovered(self):
        # an arc of the unit circle centred on the origin. SPD normalises each
        # axis by its own maximum before fitting, so the radius comes back
        # scaled by 1/max(x) = 1/cos(0.05)
        t = np.linspace(0.05, math.pi / 2 - 0.05, 12)
        x, y = np.cos(t), np.sin(t)
        curv = ps.arai_curvature(x, y)
        assert curv["r"] == pytest.approx(1.0 / math.cos(0.05), abs=1e-6)
        assert curv["sse"] == pytest.approx(0.0, abs=1e-9)
        assert abs(curv["k"]) == pytest.approx(math.cos(0.05), abs=1e-6)

    def test_the_sign_says_which_way_the_plot_bends(self):
        x = np.linspace(0, 1, 12)
        convex = ps.arai_curvature(x, np.sqrt(np.clip(1 - x ** 2, 0, None)))
        concave = ps.arai_curvature(x, 1 - np.sqrt(np.clip(1 - (1 - x) ** 2, 0, None)))
        assert convex["k"] * concave["k"] < 0

    def test_too_few_points_returns_nan_rather_than_raising(self):
        curv = ps.arai_curvature([0.0, 1.0], [1.0, 0.0])
        assert math.isnan(curv["k"])


class TestZiggie:
    def test_a_straight_monotonic_segment_is_zero(self):
        x = np.linspace(0, 1, 9)
        out = ps.ziggie(x, 1 - x)
        assert out["ziggie"] == pytest.approx(0.0, abs=1e-6)

    def test_it_falls_back_to_a_line_when_the_circle_is_enormous(self):
        x = np.linspace(0, 1, 9)
        out = ps.ziggie(x, 1 - x)
        assert out["model"] == "line"
        assert abs(out["k_prime"]) <= ps.ZIGGIE_LINE_FALLBACK_K

    def test_it_uses_an_arc_when_the_plot_is_curved(self):
        t = np.linspace(0.1, math.pi / 2 - 0.1, 12)
        out = ps.ziggie(np.cos(t), np.sin(t))
        assert out["model"] == "arc"
        assert out["ziggie"] == pytest.approx(0.0, abs=2e-3)

    def test_it_grows_with_zig_zag_and_crosses_the_proposed_criterion(self):
        x = np.linspace(0, 1, 11)
        base = 1 - x
        previous = -np.inf
        crossed = False
        for delta in (0.0, 0.01, 0.02, 0.04, 0.08):
            y = base + delta * np.array([0, 1, -1, 1, -1, 1, -1, 1, -1, 1, 0])
            value = ps.ziggie(x, y)["ziggie"]
            assert value > previous
            previous = value
            crossed = crossed or value > ps.ZIGGIE_CRITERION
        assert crossed, "Ziggie should exceed 0.1 for a strongly zig-zagged plot"

    def test_it_is_invariant_to_scaling_the_axes(self):
        # the property Tully & Paterson (2025) show IZZI_MD lacks
        x = np.linspace(0, 1, 11)
        y = 1 - x + 0.03 * np.array([0, 1, -1, 1, -1, 1, -1, 1, -1, 1, 0])
        base = ps.ziggie(x, y)["ziggie"]
        for fx, fy in ((0.5, 1.0), (2.0, 1.0), (1.0, 0.5), (2.0, 0.5)):
            assert ps.ziggie(x * fx, y * fy)["ziggie"] == pytest.approx(base, abs=1e-9)

    def test_izzi_md_is_not_invariant_to_scaling_which_is_why_ziggie_exists(self):
        x = np.linspace(0, 1, 11)
        y = 1 - x + 0.03 * np.array([0, 1, -1, 1, -1, 1, -1, 1, -1, 1, 0])
        steps = ["NRM"] + ["ZI" if i % 2 else "IZ" for i in range(1, 11)]
        base = ps.izzi_md(x, y, steps)
        scaled = ps.izzi_md(x * 2, y, steps)
        assert abs(scaled - base) > 0.1 * abs(base)


# ---------------------------------------------------------------------------
# Directional statistics
# ---------------------------------------------------------------------------
class TestDirectional:
    def test_pca_recovers_a_known_direction(self):
        direction = ps.dir_to_cart(30.0, 45.0, 1.0)
        vectors = np.array([direction * m for m in (1.0, 0.8, 0.6, 0.4, 0.2)])
        free = ps.pca(vectors)
        assert free["dec"] == pytest.approx(30.0)
        assert free["inc"] == pytest.approx(45.0)
        assert free["mad"] == pytest.approx(0.0, abs=1e-6)

    def test_alpha_is_zero_when_the_component_goes_to_the_origin(self):
        direction = ps.dir_to_cart(10.0, -20.0, 1.0)
        vectors = np.array([direction * m for m in (1.0, 0.75, 0.5, 0.25)])
        exp = straight_experiment(n=4)
        exp.nrm_vectors = vectors
        s = ps.directional_statistics(exp, 0, 3)
        assert float(s["alpha"]) == pytest.approx(0.0, abs=1e-6)
        assert float(s["DANG"]) == pytest.approx(0.0, abs=1e-6)

    def test_dang_is_the_angle_to_the_centre_of_mass(self):
        vectors = np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 0.5], [0.0, 0.2, 0.2]])
        exp = straight_experiment(n=3)
        exp.nrm_vectors = vectors
        s = ps.directional_statistics(exp, 0, 2)
        free = ps.pca(vectors)
        expected = ps._angle(free["direction"], vectors.mean(axis=0))
        assert float(s["DANG"]) == pytest.approx(expected)

    def test_statistics_that_need_an_independent_direction_say_so(self):
        exp = straight_experiment()
        s = ps.directional_statistics(exp, 0, 7)
        assert s["alpha_prime"].state is ps.State.UNAVAILABLE
        assert s["CRM_percent"].state is ps.State.UNAVAILABLE
        assert "independent" in s["alpha_prime"].reason

    def test_they_become_available_once_a_direction_is_supplied(self):
        exp = straight_experiment()
        exp.chrm = ps.dir_to_cart(90.0, 45.0, 1.0)
        s = ps.directional_statistics(exp, 0, 7)
        assert s["alpha_prime"].is_value
        assert s["CRM_percent"].is_value

    def test_theta_is_the_angle_between_the_nrm_and_the_laboratory_field(self):
        exp = straight_experiment()
        # the NRM is along -z and so is B_lab, so theta is zero
        assert float(ps.directional_statistics(exp, 0, 7)["theta"]) == pytest.approx(180.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
class TestChecks:
    def test_no_checks_is_not_applicable_rather_than_zero(self):
        exp = straight_experiment()
        p = ps.ptrm_check_statistics(exp, 0, 7)
        assert float(p["n_pTRM"]) == 0
        assert p["DRAT"].state is ps.State.NOT_APPLICABLE
        t = ps.tail_check_statistics(exp, 0, 7)
        assert t["dTR"].state is ps.State.NOT_APPLICABLE
        assert t["delta_t_star"].state is ps.State.NOT_APPLICABLE
        a = ps.additivity_check_statistics(exp, 0, 7)
        assert a["dAC"].state is ps.State.NOT_APPLICABLE

    def test_drat_is_the_worst_check_over_the_length_of_the_fit(self):
        exp = straight_experiment(n=6)
        exp.ptrm_checks = [ps.PtrmCheck(i=1, j=3, x=exp.x[1] + 0.05),
                           ps.PtrmCheck(i=2, j=4, x=exp.x[2] - 0.02)]
        fit = ps.york_regression(exp.x, exp.y)
        p = ps.ptrm_check_statistics(exp, 0, 5)
        assert float(p["DRAT"]) == pytest.approx(100 * 0.05 / fit["line_length"])
        assert float(p["n_pTRM"]) == 2

    def test_a_check_above_tmax_is_left_out(self):
        exp = straight_experiment(n=6)
        exp.ptrm_checks = [ps.PtrmCheck(i=1, j=5, x=exp.x[1] + 0.05)]
        assert float(ps.ptrm_check_statistics(exp, 0, 3)["n_pTRM"]) == 0
        assert float(ps.ptrm_check_statistics(exp, 0, 5)["n_pTRM"]) == 1

    def test_pck_normalises_by_the_ptrm_at_tmax(self):
        exp = straight_experiment(n=6)
        exp.ptrm_checks = [ps.PtrmCheck(i=1, j=3, x=exp.x[1] + 0.05)]
        p = ps.ptrm_check_statistics(exp, 0, 5)
        assert float(p["Pck"]) == pytest.approx(100 * 0.05 / exp.x[5])

    def test_delta_pal_needs_the_check_vectors(self):
        exp = straight_experiment(n=6)
        exp.ptrm_checks = [ps.PtrmCheck(i=1, j=3, x=exp.x[1] + 0.05)]
        assert ps.ptrm_check_statistics(exp, 0, 5)["delta_pal"].state is ps.State.NOT_APPLICABLE

    def test_delta_pal_is_zero_when_the_checks_reproduce_exactly(self):
        exp = straight_experiment(n=6)
        exp.ptrm_checks = [ps.PtrmCheck(i=k, j=k + 1, x=exp.x[k],
                                        vector=exp.trm_vectors[k].copy()) for k in (1, 2)]
        assert float(ps.ptrm_check_statistics(exp, 0, 5)["delta_pal"]) == pytest.approx(0.0, abs=1e-9)

    def test_delta_t_star_is_zero_when_the_tail_check_reproduces_the_nrm(self):
        exp = straight_experiment(n=6)
        exp.tail_checks = [ps.TailCheck(i=k, y=exp.y[k], vector=exp.nrm_vectors[k].copy())
                           for k in (1, 2, 3)]
        t = ps.tail_check_statistics(exp, 0, 5)
        assert float(t["dTR"]) == pytest.approx(0.0)
        assert float(t["delta_t_star"]) == pytest.approx(0.0)

    def test_delta_t_star_is_positive_for_a_real_tail(self):
        exp = straight_experiment(n=6)
        # the NRM is along -z and so is B_lab, so tilt the NRM to give theta a
        # value in the range where dt* is defined
        direction = ps.dir_to_cart(0.0, -45.0, 1.0)
        exp.nrm_vectors = np.array([direction * m for m in exp.y])
        tail = exp.nrm_vectors[2].copy()
        tail[2] -= 0.05 * abs(tail[2])                    # a tail along the field axis
        exp.tail_checks = [ps.TailCheck(i=2, y=float(np.linalg.norm(tail)), vector=tail)]
        assert float(ps.tail_check_statistics(exp, 0, 5)["delta_t_star"]) > 0

    def test_delta_t_star_needs_a_field_along_a_specimen_axis(self):
        exp = straight_experiment(n=6)
        exp.blab_orient = ps.dir_to_cart(37.0, 12.0, 1.0)
        exp.tail_checks = [ps.TailCheck(i=2, y=exp.y[2], vector=exp.nrm_vectors[2].copy())]
        stat = ps.tail_check_statistics(exp, 0, 5)["delta_t_star"]
        assert stat.state is ps.State.NOT_APPLICABLE
        assert "specimen axis" in stat.reason

    def test_additivity_checks_normalise_by_the_total_trm(self):
        exp = straight_experiment(n=6)
        exp.additivity_checks = [ps.AdditivityCheck(i=2, j=4, x=exp.x[2] + 0.03)]
        fit = ps.york_regression(exp.x, exp.y)
        a = ps.additivity_check_statistics(exp, 0, 5)
        assert float(a["dAC"]) == pytest.approx(100 * 0.03 / abs(fit["x_int"]))


# ---------------------------------------------------------------------------
# Corrections
# ---------------------------------------------------------------------------
class TestCorrections:
    def test_an_isotropic_tensor_needs_no_correction(self):
        out = ps.anisotropy_correction_factor([1 / 3, 1 / 3, 1 / 3, 0, 0, 0],
                                              ps.dir_to_cart(12.0, 34.0), [0, 0, -1])
        assert out["c"] == pytest.approx(1.0)
        assert out["degree"] == pytest.approx(1.0)

    def test_the_design_matrix_matches_spd_v1_2(self):
        a = ps.anisotropy_design_matrix()
        p = np.array([ps.dir_to_cart(d, i, 1.0) for d, i in ps.ANISOTROPY_POSITIONS[6]])
        # row 6 (index 5) is the corrected one: 0 0 P2,3 0 P2,2 P2,1
        assert a[5] == pytest.approx([0.0, 0.0, p[1, 2], 0.0, p[1, 1], p[1, 0]])
        assert a.shape == (18, 6)

    def test_a_tensor_round_trips_through_the_design_matrix(self):
        s = np.array([0.36, 0.31, 0.33, 0.02, -0.01, 0.015])
        chi = ps.anisotropy_tensor(s)
        positions = ps.ANISOTROPY_POSITIONS[6]
        moments = np.array([chi @ ps.dir_to_cart(d, i, 1.0) for d, i in positions])
        assert ps.fit_anisotropy_tensor(moments, positions) == pytest.approx(s)

    def test_the_correction_follows_the_easy_axis(self):
        # chi = diag(0.5, 0.25, 0.25): the easy axis is x. A ChRM along the easy
        # axis means the specimen recorded more than the laboratory field would
        # suggest, so the ancient field was weaker: c < 1. A ChRM along a hard
        # axis with B_lab along the easy one is the other way round.
        s = [0.5, 0.25, 0.25, 0.0, 0.0, 0.0]
        assert ps.anisotropy_correction_factor(s, [1, 0, 0], [0, 0, -1])["c"] == pytest.approx(0.5)
        assert ps.anisotropy_correction_factor(s, [0, 0, 1], [0, 0, -1])["c"] == pytest.approx(1.0)
        assert ps.anisotropy_correction_factor(s, [0, 0, 1], [1, 0, 0])["c"] == pytest.approx(2.0)

    def test_hext_f_grows_with_the_degree_of_anisotropy(self):
        weak = ps.hext_statistics([0.34, 0.33, 0.33, 0, 0, 0], 0.001, 12)
        strong = ps.hext_statistics([0.50, 0.25, 0.25, 0, 0, 0], 0.001, 12)
        assert strong["F"] > weak["F"]
        assert strong["passes_ftest"] is True

    def test_nlt_reduces_to_the_linear_estimate_when_a2_is_zero(self):
        assert ps.nlt_correction(-0.8, 40e-6, 0.0) == pytest.approx(0.8 * 40e-6)

    def test_nlt_coefficients_round_trip(self):
        fields = np.array([10e-6, 20e-6, 40e-6, 60e-6, 80e-6])
        a1, a2 = 3.2, 8.0e3
        moments = a1 * np.tanh(a2 * fields)
        got1, got2 = ps.fit_nlt_coefficients(fields, moments)
        assert got1 == pytest.approx(a1, rel=1e-4)
        assert got2 == pytest.approx(a2, rel=1e-4)

    def test_the_nlt_correction_inverts_its_own_model(self):
        a2 = 8.0e3
        blab, banc = 40e-6, 55e-6
        b = math.tanh(a2 * banc) / math.tanh(a2 * blab)      # the slope such a specimen gives
        assert ps.nlt_correction(b, blab, a2) == pytest.approx(banc)

    def test_the_cooling_rate_factor_is_one_when_the_rates_match(self):
        out = ps.cooling_rate_factor([1.0, 0.1, 0.01], [1.0, 1.0, 1.0], 1.0,
                                     alteration_check=(1.0, 1.0))
        assert out["factor"] == pytest.approx(1.0)
        assert out["flag"] == "calculated"

    def test_a_slower_ancient_cooling_rate_lowers_the_intensity(self):
        # TRM rises as cooling slows, so the ancient field must have been weaker
        out = ps.cooling_rate_factor([1.0, 0.1, 0.01], [1.0, 1.1, 1.2], 1e-6,
                                     alteration_check=(1.0, 1.0))
        assert 0 < out["factor"] < 1

    def test_an_altered_cooling_rate_experiment_yields_no_factor(self):
        out = ps.cooling_rate_factor([1.0, 0.1, 0.01], [1.0, 1.1, 1.2], 0.001,
                                     alteration_check=(1.0, 1.5))
        assert out["flag"] == "altered"
        assert math.isnan(out["factor"])
        assert out["alteration"] > ps.COOLING_RATE_ALTERATION_LIMIT


# ---------------------------------------------------------------------------
# Group statistics
# ---------------------------------------------------------------------------
class TestGroupStatistics:
    def test_the_mean_and_scatter_of_a_known_set(self):
        s = ps.group_statistics([40.0, 44.0, 48.0])
        assert float(s["mean"]) == pytest.approx(44.0)
        assert float(s["sd"]) == pytest.approx(4.0)
        assert float(s["dB_percent"]) == pytest.approx(100 * 4.0 / 44.0)

    def test_one_estimate_leaves_the_scatter_undefined(self):
        s = ps.group_statistics([42.0])
        assert float(s["N"]) == 1
        assert s["sd"].state is ps.State.UNDEFINED

    def test_the_weighted_mean_leans_toward_the_precise_estimate(self):
        s = ps.group_statistics([40.0, 60.0], weights=[9.0, 1.0])
        assert float(s["weighted_mean"]) == pytest.approx(42.0)

    def test_the_upper_bound_on_scatter_exceeds_the_scatter_itself(self):
        s = ps.group_statistics([40.0, 44.0, 48.0])
        assert float(s["dBN_percent"]) > float(s["dB_percent"])

    def test_the_spd_calibration_averages_are_reproduced(self):
        """SPD v1.2.0 Table 2: N = 20, m = 49.4, s = 24.2, dB = 48.9, dBN = 66.3."""
        import pandas as pd
        path = os.path.join(SPD_DIR, "SPD_reference_averages.csv")
        table = pd.read_csv(path).head(20)          # the sheet's own summary rows follow
        values = pd.to_numeric(table.iloc[:, 2], errors="coerce").dropna().tolist()
        assert len(values) == 20
        s = ps.group_statistics(values)
        assert float(s["mean"]) == pytest.approx(49.4, abs=0.05)
        assert float(s["sd"]) == pytest.approx(24.2, abs=0.05)
        assert float(s["dB_percent"]) == pytest.approx(48.9, abs=0.1)
        assert float(s["dBN_percent"]) == pytest.approx(66.3, abs=0.5)


class TestDistributions:
    def test_the_chi_squared_tail_matches_known_values(self):
        assert ps._chi2_sf(3.841, 1) == pytest.approx(0.05, abs=1e-3)
        assert ps._chi2_sf(11.070, 5) == pytest.approx(0.05, abs=1e-3)
        assert ps._chi2_sf(0.0, 4) == pytest.approx(1.0)

    def test_the_f_critical_value_matches_a_table(self):
        assert ps.f_critical(5, 12) == pytest.approx(3.106, abs=5e-3)
        assert ps.f_critical(2, 30) == pytest.approx(3.316, abs=5e-3)

    def test_the_noncentral_t_matches_the_value_spd_quotes(self):
        # SPD numerical tip: for N-1 = 1 and a noncentrality parameter of 1 the
        # 95% noncentral t critical value is -1.193 at the 5% level, i.e. the
        # 0.05 quantile
        lo, hi = -50.0, 50.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if ps._noncentral_t_cdf(mid, 1, 1.0) < 0.05:
                lo = mid
            else:
                hi = mid
        assert (lo + hi) / 2 == pytest.approx(-1.193, abs=0.02)
