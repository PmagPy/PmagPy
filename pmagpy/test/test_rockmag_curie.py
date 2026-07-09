"""
Tests for the Curie temperature estimation functions in pmagpy.rockmag.

Synthetic curves with known analytical answers are used throughout:

* in-field Landau curves M(T) = M0 * m(tau; h), with m the physical root of
  the Landau equation of state m**3 + tau*m = h (Fabian et al., 2013,
  doi:10.1029/2012GC004440), for which the Curie temperature Tc is known
  exactly and the documented biases of the classical estimators (maximum
  curvature and two-tangent above the inflection-point Tc) must be recovered;
* susceptibility curves with an exact Curie-Weiss tail chi = C/(T - theta)
  above the transition, for which the inverse-susceptibility method must
  recover theta;
* a real measured curve (data_files/curie/curie_example.dat) for which the
  maximum-curvature estimate is checked against the legacy ipmag.curie
  result (552 C with a 10-degree smoothing window).
"""
import os

import numpy as np
import pandas as pd
import pytest

import pmagpy.rockmag as rmag

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data_files")

TC_K = 853.15  # 580 C
M0 = 1.0
H_REDUCED = 5e-4
THETA_C = 590.0  # paramagnetic Curie temperature for the chi fixture
CURIE_CONSTANT = 2e-6


def landau_curve_K(T_K, tc_K=TC_K, m0=M0, h=H_REDUCED):
    """In-field Landau magnetization curve at absolute temperatures T_K."""
    return m0 * rmag.landau_magnetization((T_K - tc_K) / tc_K, h)


@pytest.fixture
def landau_heating_C():
    """Dense in-field Landau curve through Tc, temperatures in Celsius."""
    T_K = np.linspace(323.15, 973.15, 400)
    return T_K - 273.15, landau_curve_K(T_K)


@pytest.fixture
def curie_weiss_chi():
    """chi(T) with an exact Curie-Weiss tail above the transition."""
    T = np.linspace(300.0, 700.0, 400)
    chi = np.where(
        T > THETA_C + 2.0,
        CURIE_CONSTANT / (T - THETA_C),
        1e-4 * (1.0 - 0.5 * (T / THETA_C)),
    )
    return T, chi


@pytest.fixture
def heat_cool_experiment():
    """MagIC-shaped experiment with heating and cooling branches and a
    constant holder offset."""
    T_heat = np.linspace(323.15, 973.15, 300)
    T_cool = T_heat[::-1]
    holder = 0.05
    return pd.DataFrame({
        "meas_temp": np.concatenate([T_heat, T_cool]),
        "magn_mass": np.concatenate([
            landau_curve_K(T_heat) + holder,
            0.9 * landau_curve_K(T_cool) + holder,
        ]),
        "specimen": "synthetic-01",
        "experiment": "SYN-LP-MST-1",
    })


class TestLandauMagnetization:
    def test_zero_field_square_root_form(self):
        tau = np.array([-0.75, -0.5, -0.25, -0.04])
        m = rmag.landau_magnetization(tau, 0.0)
        assert np.allclose(m, np.sqrt(-tau), atol=1e-12)

    def test_zero_field_vanishes_above_tc(self):
        m = rmag.landau_magnetization(np.array([0.01, 0.2, 1.0]), 0.0)
        assert np.allclose(m, 0.0, atol=1e-12)

    def test_field_rounds_transition(self):
        tau = np.linspace(-0.5, 0.5, 101)
        m = rmag.landau_magnetization(tau, 1e-3)
        # monotonically decreasing, positive tail above Tc
        assert np.all(np.diff(m) < 0)
        assert m[-1] > 0
        # satisfies the equation of state
        assert np.allclose(m**3 + tau * m, 1e-3, atol=1e-10)


class TestSplitWarmCool:
    def test_heating_then_cooling(self, heat_cool_experiment):
        warm_T, warm_X, cool_T, cool_X = rmag.split_warm_cool(
            heat_cool_experiment, magnetic_column="magn_mass"
        )
        assert warm_T.size == 300
        assert cool_T.size == 300
        assert warm_T[0] < warm_T[-1]
        assert cool_T[0] > cool_T[-1]

    def test_cooling_only_has_empty_heating_branch(self):
        T = np.linspace(300, 20, 57)
        df = pd.DataFrame({"meas_temp": T, "magn_mass": np.linspace(38, 42, 57)})
        warm_T, _, cool_T, _ = rmag.split_warm_cool(
            df, magnetic_column="magn_mass"
        )
        assert warm_T.size == 0
        assert cool_T.size == 57

    def test_non_finite_rows_dropped(self):
        df = pd.DataFrame({
            "meas_temp": [280.0, 290.0, np.nan, 310.0],
            "magn_mass": [1.0, np.nan, 3.0, 4.0],
        })
        warm_T, warm_X, _, _ = rmag.split_warm_cool(
            df, magnetic_column="magn_mass"
        )
        assert warm_T.size == 2
        assert np.all(np.isfinite(warm_X))

    def test_duplicate_heating_temperatures_no_phantom_cooling(self):
        # repeated furnace-stabilization temperatures on a heating-only run
        # must stay on the heating branch, not seed a spurious cooling branch
        T = np.repeat(np.arange(300.0, 901.0, 50.0), 2)
        df = pd.DataFrame({
            "meas_temp": T,
            "magn_mass": np.linspace(1.0, 0.1, T.size),
        })
        warm_T, _, cool_T, _ = rmag.split_warm_cool(
            df, magnetic_column="magn_mass"
        )
        assert cool_T.size == 0
        assert warm_T.size == T.size

    def test_noisy_heating_temperatures_no_phantom_cooling(self):
        # temperature read-noise larger than the step must not scatter heating
        # points into the cooling branch
        rng = np.random.RandomState(0)
        base = np.arange(300.0, 900.0, 3.0)
        T = base + rng.normal(0.0, 3.0, base.size)
        df = pd.DataFrame({
            "meas_temp": T,
            "magn_mass": np.linspace(1.0, 0.1, T.size),
        })
        _, _, cool_T, _ = rmag.split_warm_cool(df, magnetic_column="magn_mass")
        assert cool_T.size == 0


class TestPrepareThermomagBranches:
    def test_branches_ascending_and_holder_removed(self, heat_cool_experiment):
        branches = rmag.prepare_thermomag_branches(
            heat_cool_experiment, magnetic_column="magn_mass"
        )
        for branch in ("heating", "cooling"):
            T = branches[branch]["T"]
            assert np.all(np.diff(T) >= 0)
            # holder offset (0.05) removed: branch minimum is zero
            assert branches[branch]["y"].min() == pytest.approx(0.0, abs=1e-12)

    def test_heating_only_returns_none_cooling(self):
        T = np.linspace(300, 900, 50)
        df = pd.DataFrame({"meas_temp": T, "susc_chi_mass": np.exp(-T / 300)})
        branches = rmag.prepare_thermomag_branches(df)
        assert branches["cooling"] is None
        assert branches["heating"]["T"].size == 50

    def test_duplicate_heating_temperatures_returns_none_cooling(self):
        # furnace-stabilization duplicates on a heating-only run must not
        # produce a phantom cooling branch downstream of split_warm_cool
        T = np.repeat(np.arange(300.0, 901.0, 50.0), 2)
        df = pd.DataFrame({"meas_temp": T, "susc_chi_mass": np.exp(-T / 300)})
        branches = rmag.prepare_thermomag_branches(df)
        assert branches["cooling"] is None
        assert branches["heating"] is not None

    def test_temperature_units(self, heat_cool_experiment):
        branches_C = rmag.prepare_thermomag_branches(
            heat_cool_experiment, magnetic_column="magn_mass", temp_unit="C"
        )
        branches_K = rmag.prepare_thermomag_branches(
            heat_cool_experiment, magnetic_column="magn_mass", temp_unit="K"
        )
        assert branches_K["heating"]["T"][0] - branches_C["heating"]["T"][0] == (
            pytest.approx(273.15)
        )


class TestCurieDerivativeEstimates:
    def test_inflection_at_tc_on_landau_curve(self, landau_heating_C):
        T, M = landau_heating_C
        result = rmag.curie_derivative_estimates(T, M)
        assert result["inflection_temp"] == pytest.approx(580.0, abs=2.0)

    def test_max_curvature_above_inflection(self, landau_heating_C):
        T, M = landau_heating_C
        result = rmag.curie_derivative_estimates(T, M)
        # documented bias: the maximum-curvature estimate lies above the
        # inflection-point Tc on in-field M(T) (Fabian et al., 2013)
        assert result["max_curvature_temp"] > result["inflection_temp"]
        assert result["max_curvature_temp"] - 580.0 < 25.0

    def test_duplicate_temperatures_handled(self, landau_heating_C):
        T, M = landau_heating_C
        T_dup = np.repeat(T, 2)
        M_dup = np.repeat(M, 2)
        result = rmag.curie_derivative_estimates(T_dup, M_dup)
        assert np.isfinite(result["inflection_temp"])
        assert result["inflection_temp"] == pytest.approx(580.0, abs=2.0)

    def test_too_few_points_returns_nan(self):
        result = rmag.curie_derivative_estimates([1.0, 2.0], [1.0, 0.5])
        assert np.isnan(result["inflection_temp"])
        assert np.isnan(result["max_curvature_temp"])

    def test_t_range_restricts_search(self, landau_heating_C):
        T, M = landau_heating_C
        # a second, low-temperature feature that would otherwise dominate
        M_two_phase = M + 0.5 * rmag.landau_magnetization(
            (T + 273.15 - 473.15) / 473.15, H_REDUCED
        )
        result = rmag.curie_derivative_estimates(T, M_two_phase,
                                                 t_range=(400, 700))
        assert result["inflection_temp"] == pytest.approx(580.0, abs=5.0)

    def test_tail_noise_does_not_capture_estimate(self, landau_heating_C):
        # noise confined to the flat tails must not drag the derivative
        # estimates off the field-rounded transition; both estimates are
        # anchored to the steepest descent, which the tails do not move
        T, M = landau_heating_C
        rng = np.random.RandomState(1)
        noise = np.zeros_like(M)
        # the transition sits at 580 C; keep the noise in the flat tails and
        # below the transition slope so the steepest descent still finds the
        # transition (the estimates must follow it, not the tail structure)
        tail = (T < 430) | (T > 660)
        noise[tail] = rng.normal(0.0, 0.002, int(tail.sum()))
        result = rmag.curie_derivative_estimates(T, M + noise)
        assert result["inflection_temp"] == pytest.approx(580.0, abs=3.0)
        assert result["max_curvature_temp"] > result["inflection_temp"]
        assert result["max_curvature_temp"] - 580.0 < 25.0

    def test_non_finite_values_dropped(self, landau_heating_C):
        # a single NaN must not become the steepest-descent point
        T, M = landau_heating_C
        M_nan = M.copy()
        M_nan[5] = np.nan
        result = rmag.curie_derivative_estimates(T, M_nan)
        assert result["inflection_temp"] == pytest.approx(580.0, abs=2.0)

    def test_smooth_window_stabilizes_noisy_derivative(self):
        # differentiation amplifies noise: the raw first derivative of a noisy
        # curve has a ragged minimum, so argmin can latch onto a spike offset
        # from the true inflection. smooth_window smooths the derivative and
        # recovers the transition center, without distorting a clean curve.
        T = np.linspace(300.0, 700.0, 400)
        M = (1.0 - np.tanh((T - 500.0) / 18.0)) / 2.0  # inflection at 500
        clean = rmag.curie_derivative_estimates(T, M, smooth_window=20)
        assert clean["inflection_temp"] == pytest.approx(500.0, abs=1.0)
        rng = np.random.default_rng(0)
        y = M + rng.normal(0.0, 0.013, T.size)
        raw = rmag.curie_derivative_estimates(T, y)["inflection_temp"]
        smoothed = rmag.curie_derivative_estimates(
            T, y, smooth_window=20)["inflection_temp"]
        assert abs(raw - 500.0) > 10.0  # noise displaces the raw estimate
        assert smoothed == pytest.approx(500.0, abs=3.0)


class TestCurieTwoTangent:
    def test_recovers_transition_on_landau_curve(self, landau_heating_C):
        T, M = landau_heating_C
        result = rmag.curie_two_tangent(T, M)
        assert np.isfinite(result["curie_temp"])
        # documented bias: at or above the true Tc
        assert result["curie_temp"] >= 580.0 - 1.0
        assert result["curie_temp"] - 580.0 < 30.0

    def test_bias_ordering(self, landau_heating_C):
        # two_tangent >= max_curvature-region estimates >= inflection ~ Tc
        T, M = landau_heating_C
        derivative = rmag.curie_derivative_estimates(T, M)
        two_tangent = rmag.curie_two_tangent(T, M)
        assert (two_tangent["curie_temp"]
                >= derivative["inflection_temp"] - 1.0)

    def test_explicit_ranges(self, landau_heating_C):
        T, M = landau_heating_C
        result = rmag.curie_two_tangent(T, M, lower_range=(540, 575),
                                        upper_range=(620, 700))
        assert np.isfinite(result["curie_temp"])
        assert result["params"]["lower_range"] == (540, 575)

    def test_insufficient_points(self):
        result = rmag.curie_two_tangent([1, 2, 3], [3, 2, 1])
        assert np.isnan(result["curie_temp"])
        assert "note" in result["params"]

    def test_reliable_flag_true_on_full_curve(self, landau_heating_C):
        # a curve that reaches a flat baseline above Tc is a reliable fit
        T, M = landau_heating_C
        result = rmag.curie_two_tangent(T, M)
        assert result["params"]["reliable"] is True

    def test_non_finite_values_dropped(self, landau_heating_C):
        T, M = landau_heating_C
        M_nan = M.copy()
        M_nan[7] = np.nan
        result = rmag.curie_two_tangent(T, M_nan)
        assert np.isfinite(result["curie_temp"])


class TestCurieInverseSusceptibility:
    def test_exact_recovery_of_theta(self, curie_weiss_chi):
        T, chi = curie_weiss_chi
        result = rmag.curie_inverse_susceptibility(T, chi,
                                                   fit_range=(620, 700))
        assert result["curie_temp"] == pytest.approx(THETA_C, abs=0.5)
        assert result["params"]["r_squared"] == pytest.approx(1.0, abs=1e-6)
        assert result["params"]["curie_constant"] == pytest.approx(
            CURIE_CONSTANT, rel=1e-3
        )

    def test_window_below_transition_degrades_fit(self, curie_weiss_chi):
        T, chi = curie_weiss_chi
        clean = rmag.curie_inverse_susceptibility(T, chi,
                                                  fit_range=(620, 700))
        contaminated = rmag.curie_inverse_susceptibility(
            T, chi, fit_range=(400, 700)
        )
        assert (contaminated["params"]["r_squared"]
                < clean["params"]["r_squared"])

    def test_default_window_is_top_quintile(self, curie_weiss_chi):
        T, chi = curie_weiss_chi
        result = rmag.curie_inverse_susceptibility(T, chi)
        lo, hi = result["params"]["fit_range"]
        assert lo == pytest.approx(T.min() + 0.8 * (T.max() - T.min()))
        assert hi == pytest.approx(T.max())

    def test_insufficient_points_noted(self, curie_weiss_chi):
        T, chi = curie_weiss_chi
        result = rmag.curie_inverse_susceptibility(T, chi,
                                                   fit_range=(699, 700))
        assert np.isnan(result["curie_temp"])
        assert "note" in result["params"]

    def test_quantized_tail_warns_and_min_chi_recovers(self):
        """A resolution-limited tail (susceptibility pinned at integer counts
        of the meter) flattens the fit and biases theta low; the function
        must warn, and excluding sub-resolution points with min_chi must
        recover theta."""
        step = 5e-9  # one instrument count
        T = np.linspace(600, 700, 60)
        chi_true = CURIE_CONSTANT / (T - THETA_C)
        chi_quantized = np.round(chi_true / step) * step  # pinned counts tail
        contaminated = rmag.curie_inverse_susceptibility(
            T, chi_quantized, fit_range=(600, 700))
        assert "warning" in contaminated["params"]
        assert contaminated["curie_temp"] < THETA_C  # biased low
        screened = rmag.curie_inverse_susceptibility(
            T, chi_quantized, fit_range=(600, 700), min_chi=10 * step)
        assert "warning" not in screened["params"]
        assert screened["curie_temp"] == pytest.approx(THETA_C, abs=2.0)
        assert screened["params"]["n_points"] < contaminated["params"]["n_points"]

    def test_clean_data_has_no_warning(self, curie_weiss_chi):
        T, chi = curie_weiss_chi
        result = rmag.curie_inverse_susceptibility(T, chi,
                                                   fit_range=(620, 700))
        assert "warning" not in result["params"]

    def test_stderr_matches_monte_carlo(self):
        # the reported 1-sigma on theta must match the actual spread of theta
        # under noise, which requires the slope-intercept covariance term in
        # the delta-method propagation; omitting it inflates the value ~12x
        # because slope and intercept are almost perfectly anti-correlated
        theta, C = 590.0, 2e-6
        T = np.linspace(620, 700, 40)
        inv_true = (T - theta) / C
        sigma = 0.01 * inv_true.max()  # homoscedastic noise in 1/chi
        rng = np.random.default_rng(12345)
        chi0 = 1.0 / (inv_true + rng.normal(0, sigma, T.size))
        reported = rmag.curie_inverse_susceptibility(
            T, chi0, fit_range=(620, 700))["curie_temp_stderr"]
        recovered = [
            rmag.curie_inverse_susceptibility(
                T, 1.0 / (inv_true + rng.normal(0, sigma, T.size)),
                fit_range=(620, 700))["curie_temp"]
            for _ in range(1500)
        ]
        assert reported == pytest.approx(np.std(recovered), rel=0.5)
        # guard the covariance cross-term explicitly: without it the reported
        # value would be several times the true spread
        (slope, intercept), cov = np.polyfit(T, 1.0 / chi0, 1, cov=True)
        naive = np.sqrt((intercept / slope**2)**2 * cov[0, 0]
                        + (1.0 / slope)**2 * cov[1, 1])
        assert reported < 0.5 * naive

    def test_min_points_below_three_is_graceful(self, curie_weiss_chi):
        # a covariance line fit needs more than two points; the function must
        # return a note rather than let np.polyfit(cov=True) raise
        T, chi = curie_weiss_chi
        result = rmag.curie_inverse_susceptibility(
            T, chi, fit_range=(699, 700), min_points=2)
        assert np.isnan(result["curie_temp"])
        assert "note" in result["params"]


class TestCurieLandauFit:
    def test_exact_recovery_noiseless(self, landau_heating_C):
        T, M = landau_heating_C
        result = rmag.curie_landau_fit(T, M, temp_unit="C")
        assert result["curie_temp"] == pytest.approx(580.0, abs=1.0)
        assert result["params"]["M0"] == pytest.approx(M0, rel=0.05)
        assert result["params"]["h"] == pytest.approx(H_REDUCED, rel=0.05)
        assert not result["params"]["extrapolation"]

    def test_recovery_with_noise(self, landau_heating_C):
        T, M = landau_heating_C
        rng = np.random.default_rng(42)
        M_noisy = M + rng.normal(0, 0.005, M.size)
        result = rmag.curie_landau_fit(T, M_noisy, temp_unit="C")
        assert result["curie_temp"] == pytest.approx(580.0, abs=5.0)
        assert np.isfinite(result["curie_temp_stderr"])
        assert result["curie_temp_stderr"] > 0

    def test_kelvin_input(self, landau_heating_C):
        T_C, M = landau_heating_C
        result = rmag.curie_landau_fit(T_C + 273.15, M, temp_unit="K")
        assert result["curie_temp"] == pytest.approx(TC_K, abs=1.0)

    def test_extrapolation_mode_flags_and_inflates_uncertainty(self):
        # truncate far below Tc: with measurement noise the extrapolated Tc
        # is weakly constrained and the formal uncertainty must reflect that
        rng = np.random.default_rng(7)
        T_through = np.linspace(20, 520, 100)
        M_through = (landau_curve_K(T_through, tc_K=480.0, h=1e-3)
                     + rng.normal(0, 0.002, T_through.size))
        T_trunc = np.linspace(20, 300, 57)
        M_trunc = (landau_curve_K(T_trunc, tc_K=480.0, h=1e-3)
                   + rng.normal(0, 0.002, T_trunc.size))
        through = rmag.curie_landau_fit(T_through, M_through, temp_unit="K")
        truncated = rmag.curie_landau_fit(T_trunc, M_trunc, temp_unit="K")
        assert truncated["params"]["extrapolation"]
        assert not through["params"]["extrapolation"]
        assert (truncated["curie_temp_stderr"]
                > 10 * through["curie_temp_stderr"])

    def test_fit_range_restricts_points(self, landau_heating_C):
        T, M = landau_heating_C
        result = rmag.curie_landau_fit(T, M, fit_range=(200, 700),
                                       temp_unit="C")
        assert result["params"]["n_points"] < T.size
        assert result["curie_temp"] == pytest.approx(580.0, abs=2.0)

    def test_insufficient_points_noted(self):
        result = rmag.curie_landau_fit([100, 200, 300], [1.0, 0.9, 0.8],
                                       temp_unit="K")
        assert np.isnan(result["curie_temp"])
        assert "note" in result["params"]

    def test_stderr_matches_monte_carlo(self):
        # the reported 1-sigma on Tc must match the spread of Tc under noise
        # for a curve measured through the transition
        tc_K = 853.15
        T_K = np.linspace(600, 1000, 80)
        M0 = landau_curve_K(T_K, tc_K=tc_K, h=1e-3)
        sigma = 0.004
        rng = np.random.default_rng(2024)
        reported = rmag.curie_landau_fit(
            T_K, M0 + rng.normal(0, sigma, T_K.size), temp_unit="K"
        )["curie_temp_stderr"]
        recovered = [
            rmag.curie_landau_fit(
                T_K, M0 + rng.normal(0, sigma, T_K.size), temp_unit="K"
            )["curie_temp"]
            for _ in range(200)
        ]
        assert reported == pytest.approx(np.std(recovered), rel=0.4)


class TestCurieTemperatureEstimates:
    def test_tidy_table_shape_and_defaults_magnetization(
            self, heat_cool_experiment):
        estimates = rmag.curie_temperature_estimates(
            heat_cool_experiment, magnetic_column="magn_mass"
        )
        assert list(estimates.columns) == [
            "specimen", "experiment", "branch", "method", "curie_temp",
            "curie_temp_stderr", "temp_unit", "params", "notes",
        ]
        # magnetization defaults: 4 methods x 2 branches
        assert len(estimates) == 8
        assert set(estimates["method"]) == {
            "inflection", "max_curvature", "two_tangent", "landau",
        }

    def test_susceptibility_defaults(self, curie_weiss_chi):
        T, chi = curie_weiss_chi
        df = pd.DataFrame({
            "meas_temp": T + 273.15,
            "susc_chi_mass": chi,
            "specimen": "chi-syn",
            "experiment": "SYN-LP-X-T-1",
        })
        estimates = rmag.curie_temperature_estimates(df, remove_holder=False)
        assert set(estimates["method"]) == {
            "inflection", "max_curvature", "inverse_susceptibility",
        }

    def test_bias_ordering_documented(self, heat_cool_experiment):
        estimates = rmag.curie_temperature_estimates(
            heat_cool_experiment, magnetic_column="magn_mass"
        )
        heating = estimates[estimates["branch"] == "heating"].set_index("method")
        tc = heating["curie_temp"]
        assert tc["inflection"] <= tc["max_curvature"] + 1.0
        assert tc["inflection"] <= tc["two_tangent"] + 1.0
        assert tc["landau"] == pytest.approx(580.0, abs=2.0)

    def test_bias_ordering_strict_separation(self, heat_cool_experiment):
        # the estimators must be genuinely separated, not collapsed onto one
        # another: two_tangent > max_curvature > inflection (Fabian et al.,
        # 2013). A slack `<= x + 1` check would pass a degenerate estimator.
        estimates = rmag.curie_temperature_estimates(
            heat_cool_experiment, magnetic_column="magn_mass"
        )
        heating = estimates[estimates["branch"] == "heating"].set_index("method")
        tc = heating["curie_temp"]
        assert tc["max_curvature"] > tc["inflection"] + 3.0
        assert tc["two_tangent"] > tc["max_curvature"] + 3.0

    def test_cooling_branch_recovers_tc(self, heat_cool_experiment):
        # the cooling branch (scaled Landau curve, same Tc) must yield a
        # correct Curie temperature, not merely a well-shaped table row
        estimates = rmag.curie_temperature_estimates(
            heat_cool_experiment, magnetic_column="magn_mass"
        )
        cooling = estimates[estimates["branch"] == "cooling"].set_index("method")
        assert cooling.loc["inflection", "curie_temp"] == pytest.approx(
            580.0, abs=3.0)
        assert cooling.loc["landau", "curie_temp"] == pytest.approx(
            580.0, abs=2.0)

    def test_method_kwargs_forwarding(self, curie_weiss_chi):
        T, chi = curie_weiss_chi
        df = pd.DataFrame({
            "meas_temp": T + 273.15,
            "susc_chi_mass": chi,
            "specimen": "chi-syn",
            "experiment": "SYN-LP-X-T-1",
        })
        estimates = rmag.curie_temperature_estimates(
            df,
            methods=("inverse_susceptibility",),
            remove_holder=False,
            method_kwargs={"inverse_susceptibility":
                           {"fit_range": (620, 700)}},
        )
        row = estimates.iloc[0]
        assert row["params"]["fit_range"] == (620.0, 700.0)
        assert row["curie_temp"] == pytest.approx(THETA_C, abs=0.5)

    def test_chi_caveat_notes(self, curie_weiss_chi):
        T, chi = curie_weiss_chi
        df = pd.DataFrame({
            "meas_temp": T + 273.15,
            "susc_chi_mass": chi,
            "specimen": "chi-syn",
            "experiment": "SYN-LP-X-T-1",
        })
        estimates = rmag.curie_temperature_estimates(
            df, methods=("two_tangent",), remove_holder=False
        )
        assert "lacks a rigorous physical basis" in estimates.iloc[0]["notes"]

    def test_unknown_method_raises(self, heat_cool_experiment):
        with pytest.raises(ValueError, match="unknown method"):
            rmag.curie_temperature_estimates(
                heat_cool_experiment, methods=("kink_point",),
                magnetic_column="magn_mass",
            )

    def test_smooth_window_forwarded_to_derivative(self):
        # the wrapper must pass its smoothing window through to the derivative
        # estimator so the recommended path is robust to derivative noise
        T_K = np.linspace(300.0, 700.0, 400) + 273.15
        M = (1.0 - np.tanh((T_K - (500.0 + 273.15)) / 18.0)) / 2.0
        rng = np.random.default_rng(0)
        df = pd.DataFrame({
            "meas_temp": T_K,
            "magn_mass": M + rng.normal(0.0, 0.013, T_K.size),
            "specimen": "syn", "experiment": "SYN-1",
        })
        est = rmag.curie_temperature_estimates(
            df, magnetic_column="magn_mass", smooth_window=20,
            methods=("inflection",))
        infl = float(est[est["branch"] == "heating"].iloc[0]["curie_temp"])
        assert infl == pytest.approx(500.0, abs=4.0)

    def test_heating_only_yields_heating_rows(self):
        T = np.linspace(323.15, 973.15, 200)
        df = pd.DataFrame({
            "meas_temp": T,
            "magn_mass": landau_curve_K(T),
            "specimen": "syn", "experiment": "SYN-1",
        })
        estimates = rmag.curie_temperature_estimates(
            df, magnetic_column="magn_mass"
        )
        assert set(estimates["branch"]) == {"heating"}


class TestRealDataRegression:
    def test_max_curvature_matches_legacy_ipmag_curie(self):
        """The legacy ipmag.curie estimate on curie_example.dat (552 C with a
        10-degree Bartlett window) is a maximum-curvature estimate; the
        rockmag implementation must agree within a few degrees despite the
        different smoothing kernel."""
        path = os.path.join(DATA_DIR, "curie", "curie_example.dat")
        if not os.path.exists(path):
            pytest.skip("curie_example.dat not available")
        T, M = np.loadtxt(path, unpack=True)
        sT, sM = rmag.smooth_moving_avg(T, M, 10)
        result = rmag.curie_derivative_estimates(sT, sM)
        assert result["max_curvature_temp"] == pytest.approx(552.0, abs=5.0)


class TestAddCurieEstimatesToSpecimensTable:
    def test_writes_kelvin_and_vocab(self, heat_cool_experiment):
        estimates = rmag.curie_temperature_estimates(
            heat_cool_experiment, magnetic_column="magn_mass"
        )
        specimens = pd.DataFrame({
            "specimen": ["synthetic-01"],
            "experiments": ["SYN-LP-MST-1"],
            "description": [np.nan],
        })
        rmag.add_curie_estimates_to_specimens_table(
            specimens, "SYN-LP-MST-1", estimates, method="landau"
        )
        row = specimens.iloc[0]
        expected_K = (
            estimates.set_index(["method", "branch"])
            .loc[("landau", "heating"), "curie_temp"] + 273.15
        )
        assert row["critical_temp"] == pytest.approx(expected_K, abs=0.01)
        assert row["critical_temp_type"] == "Curie"
        assert "curie_method" in row["description"]

    def test_missing_method_raises(self, heat_cool_experiment):
        estimates = rmag.curie_temperature_estimates(
            heat_cool_experiment, magnetic_column="magn_mass"
        )
        specimens = pd.DataFrame({
            "specimen": ["synthetic-01"],
            "experiments": ["SYN-LP-MST-1"],
            "description": [np.nan],
        })
        with pytest.raises(ValueError, match="no estimate"):
            rmag.add_curie_estimates_to_specimens_table(
                specimens, "SYN-LP-MST-1", estimates,
                method="inverse_susceptibility",
            )

    def test_specimen_fallback_when_experiment_names_differ(
            self, heat_cool_experiment):
        """Real contributions may abbreviate experiment names in the
        specimens table; the helper falls back to matching the specimen."""
        estimates = rmag.curie_temperature_estimates(
            heat_cool_experiment, magnetic_column="magn_mass"
        )
        specimens = pd.DataFrame({
            "specimen": ["synthetic-01"],
            "experiments": ["SYN-1"],  # abbreviated, no exact/substring match
            "description": [np.nan],
        })
        rmag.add_curie_estimates_to_specimens_table(
            specimens, "SYN-LP-MST-1", estimates
        )
        assert specimens.iloc[0]["critical_temp_type"] == "Curie"

    def test_missing_experiment_raises(self, heat_cool_experiment):
        estimates = rmag.curie_temperature_estimates(
            heat_cool_experiment, magnetic_column="magn_mass"
        )
        specimens = pd.DataFrame({
            "specimen": ["other"],
            "experiments": ["OTHER-EXP"],
            "description": [np.nan],
        })
        with pytest.raises(ValueError, match="not found"):
            rmag.add_curie_estimates_to_specimens_table(
                specimens, "SYN-LP-MST-1", estimates
            )

    def test_nan_experiments_rows_are_skipped(self, heat_cool_experiment):
        """Real specimens tables include rows with no experiments recorded
        (NaN in a string-dtype column); the colon-token match must skip them
        rather than raise when it splits the cell."""
        estimates = rmag.curie_temperature_estimates(
            heat_cool_experiment, magnetic_column="magn_mass"
        )
        specimens = pd.DataFrame({
            "specimen": ["synthetic-01", "blank-holder"],
            "experiments": pd.array(
                ["OTHER-EXP:SYN-LP-MST-1", pd.NA], dtype="string"),
            "description": [np.nan, np.nan],
        })
        rmag.add_curie_estimates_to_specimens_table(
            specimens, "SYN-LP-MST-1", estimates, method="landau"
        )
        # matched the colon-delimited token on row 0; NaN row 1 left untouched
        assert specimens.loc[0, "critical_temp_type"] == "Curie"
        assert pd.isna(specimens.loc[1, "critical_temp"])


class TestPlotCurieEstimates:
    def test_returns_figure_and_axes(self, heat_cool_experiment):
        fig, axes = rmag.plot_curie_estimates(
            heat_cool_experiment, magnetic_column="magn_mass",
            return_figure=True,
        )
        assert len(axes) == 2  # main + derivative panel
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_inverse_panel_for_susceptibility(self, curie_weiss_chi):
        T, chi = curie_weiss_chi
        df = pd.DataFrame({
            "meas_temp": T + 273.15,
            "susc_chi_mass": chi,
            "specimen": "chi-syn",
            "experiment": "SYN-LP-X-T-1",
        })
        fig, axes = rmag.plot_curie_estimates(
            df, remove_holder=False, return_figure=True,
            method_kwargs={"inverse_susceptibility":
                           {"fit_range": (620, 700)}},
        )
        assert len(axes) == 3  # main + derivative + 1/chi panels
        import matplotlib.pyplot as plt
        plt.close(fig)


class TestReviewFixes:
    """Regression tests for issues found in pre-commit review."""

    def test_description_free_text_preserved(self, heat_cool_experiment):
        estimates = rmag.curie_temperature_estimates(
            heat_cool_experiment, magnetic_column="magn_mass"
        )
        specimens = pd.DataFrame({
            "specimen": ["synthetic-01"],
            "experiments": ["SYN-LP-MST-1"],
            "description": ["chip from the north margin; oxidized rind"],
        })
        rmag.add_curie_estimates_to_specimens_table(
            specimens, "SYN-LP-MST-1", estimates
        )
        description = specimens.iloc[0]["description"]
        assert "chip from the north margin" in description
        assert "curie_method" in description

    def test_experiment_matching_no_substring_overmatch(
            self, heat_cool_experiment):
        estimates = rmag.curie_temperature_estimates(
            heat_cool_experiment, magnetic_column="magn_mass"
        )
        specimens = pd.DataFrame({
            "specimen": ["other-spec", "other-spec-2"],
            "experiments": ["SYN-LP-MST-10", "SYN-LP-MST-11"],
            "description": [np.nan, np.nan],
        })
        # 'SYN-LP-MST-1' is a substring of both rows but must match neither
        with pytest.raises(ValueError, match="not found"):
            rmag.add_curie_estimates_to_specimens_table(
                specimens, "SYN-LP-MST-1", estimates
            )

    def test_experiment_matching_colon_delimited_token(
            self, heat_cool_experiment):
        estimates = rmag.curie_temperature_estimates(
            heat_cool_experiment, magnetic_column="magn_mass"
        )
        specimens = pd.DataFrame({
            "specimen": ["other-spec", "synthetic-01"],
            "experiments": ["SYN-LP-MST-10", "SYN-HYS-1:SYN-LP-MST-1"],
            "description": [np.nan, np.nan],
        })
        rmag.add_curie_estimates_to_specimens_table(
            specimens, "SYN-LP-MST-1", estimates
        )
        assert specimens.iloc[1]["critical_temp_type"] == "Curie"
        assert pd.isna(specimens.iloc[0]["critical_temp"])

    def test_negative_slope_rejected_with_note(self):
        T = np.linspace(600, 700, 50)
        chi = 1.0 / np.linspace(2e5, 1e5, 50)  # 1/chi DECREASES with T
        result = rmag.curie_inverse_susceptibility(T, chi,
                                                   fit_range=(600, 700))
        assert np.isnan(result["curie_temp"])
        assert "non-positive slope" in result["params"]["note"]

    def test_unknown_method_kwargs_key_raises(self, heat_cool_experiment):
        with pytest.raises(ValueError, match="unknown method_kwargs"):
            rmag.curie_temperature_estimates(
                heat_cool_experiment, magnetic_column="magn_mass",
                method_kwargs={"inverse_suceptibility": {}},  # typo
            )

    def test_per_method_derivative_kwargs_forwarded(self):
        # a second low-temperature transition that t_range must exclude
        T_K = np.linspace(323.15, 973.15, 400)
        M = (landau_curve_K(T_K)
             + 0.5 * rmag.landau_magnetization((T_K - 473.15) / 473.15,
                                               H_REDUCED))
        df = pd.DataFrame({
            "meas_temp": T_K, "magn_mass": M,
            "specimen": "two-phase", "experiment": "SYN-2PH-1",
        })
        estimates = rmag.curie_temperature_estimates(
            df, magnetic_column="magn_mass", methods=("inflection",),
            remove_holder=False,
            method_kwargs={"inflection": {"t_range": (400, 700)}},
        )
        assert estimates.iloc[0]["curie_temp"] == pytest.approx(580.0, abs=5.0)

    def test_data_type_inference_accepts_chi_columns(self, curie_weiss_chi):
        T, chi = curie_weiss_chi
        df = pd.DataFrame({
            "meas_temp": T + 273.15,
            "chi_corrected": chi,  # susceptibility column without 'susc'
            "specimen": "chi-syn", "experiment": "SYN-LP-X-T-1",
        })
        estimates = rmag.curie_temperature_estimates(
            df, magnetic_column="chi_corrected", remove_holder=False
        )
        assert "inverse_susceptibility" in set(estimates["method"])

    def test_data_type_override_and_validation(self, heat_cool_experiment):
        estimates = rmag.curie_temperature_estimates(
            heat_cool_experiment, magnetic_column="magn_mass",
            data_type="susceptibility",
        )
        assert "inverse_susceptibility" in set(estimates["method"])
        with pytest.raises(ValueError, match="data_type"):
            rmag.curie_temperature_estimates(
                heat_cool_experiment, magnetic_column="magn_mass",
                data_type="susceptometry",
            )

    def test_return_method_results_carries_diagnostics(
            self, heat_cool_experiment):
        estimates, method_results = rmag.curie_temperature_estimates(
            heat_cool_experiment, magnetic_column="magn_mass",
            return_method_results=True,
        )
        landau_result = method_results[("heating", "landau")]
        assert "model_T" in landau_result["diagnostics"]
        assert len(method_results) >= len(estimates)

    def test_prepare_dedupes_duplicate_temperatures(self):
        T_K = np.repeat(np.linspace(323.15, 973.15, 200), 2)
        M = np.repeat(landau_curve_K(np.linspace(323.15, 973.15, 200)), 2)
        df = pd.DataFrame({"meas_temp": T_K, "magn_mass": M})
        branches = rmag.prepare_thermomag_branches(
            df, magnetic_column="magn_mass"
        )
        T = branches["heating"]["T"]
        assert np.all(np.diff(T) > 0)  # strictly increasing after dedupe

    def test_two_tangent_truncated_curve_flagged(self):
        # run ends well below Tc: still steeply descending at max T
        T_K = np.linspace(323.15, 723.15, 200)
        M = landau_curve_K(T_K)  # Tc = 853.15 K, curve truncated at 723 K
        result = rmag.curie_two_tangent(T_K, M)
        assert "note" in result["params"]
        assert "descending limb" in result["params"]["note"]
        assert result["params"]["reliable"] is False

    def test_inverse_susceptibility_helper_masks_nonpositive(self):
        chi = np.array([2.0, 0.0, -1.0, 4.0])
        inv = rmag._inverse_susceptibility(chi)
        assert inv[0] == pytest.approx(0.5)
        assert np.isnan(inv[1]) and np.isnan(inv[2])
        assert inv[3] == pytest.approx(0.25)


class TestThermomagPlots:
    def test_plot_x_t_matplotlib_returns_figures(self, heat_cool_experiment):
        import matplotlib.pyplot as plt
        figs = rmag.plot_X_T(
            heat_cool_experiment, magnetic_column="magn_mass",
            interactive=False, return_figure=True,
            plot_derivative=True, plot_inverse=True,
        )
        assert isinstance(figs, tuple) and len(figs) >= 1
        assert all(isinstance(f, plt.Figure) for f in figs)
        plt.close("all")

    def test_interactive_inverse_susceptibility_missing_branch_raises(self):
        pytest.importorskip("bokeh")
        T = np.linspace(323.15, 973.15, 100)  # heating-only run
        df = pd.DataFrame({
            "meas_temp": T,
            "susc_chi_mass": np.exp(-T / 300),
            "specimen": "syn",
        })
        with pytest.raises(ValueError):
            rmag.interactive_curie_inverse_susceptibility(df, branch="cooling")
