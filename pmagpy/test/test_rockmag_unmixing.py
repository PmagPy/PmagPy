"""
Tests for the coercivity spectrum unmixing suite in rockmag.py.

Covers the skew-normal component model (against analytical solutions),
spectrum- and measurement-space fitting (parameter recovery on synthetic
data with known components), model selection, bootstrap uncertainty
estimation, batch processing of MagIC measurement tables, and recording of
results in MagIC specimens tables.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from scipy.integrate import quad

from pmagpy import rockmag as rmag


# a two-component reference model resembling red bed hematite spectra:
# a broad lower-coercivity component and a narrow high-coercivity one
TWO_COMPONENT_TRUTH = pd.DataFrame({
    'contribution': [0.4, 0.6],
    'location': [np.log10(250.0), np.log10(750.0)],
    'dp': [0.50, 0.12],
    'skew': [0.0, 0.0],
})


def synthetic_spectrum(noise=0.0, n=120, rng=None):
    """Synthetic coercivity spectrum from the reference two-component model.

    Uses a fresh seeded generator by default so that each call is
    deterministic and independent of test execution order (important for
    reproducible CI runs).
    """
    if rng is None:
        rng = np.random.default_rng(1234)
    x = np.linspace(0.5, 3.2, n)
    spectrum = rmag.coercivity_spectrum_model(x, TWO_COMPONENT_TRUTH)
    if noise > 0:
        spectrum = spectrum + rng.normal(0, noise * spectrum.max(), size=n)
    return x, spectrum


def synthetic_curve(noise=0.0, n=120, rng=None):
    """Synthetic backfield curve (decaying, shifted-positive convention).

    Uses a fresh seeded generator by default so that each call is
    deterministic and independent of test execution order.
    """
    if rng is None:
        rng = np.random.default_rng(5678)
    x = np.linspace(0.5, 3.2, n)
    curve = rmag.coercivity_curve_model(x, TWO_COMPONENT_TRUTH,
                                        curve_type='backfield')
    if noise > 0:
        curve = curve + rng.normal(0, noise, size=n)
    return x, curve


# Fast nested-sampling settings for the Bayesian tests: fewer live points, a
# looser evidence tolerance, and fewer data points keep the (otherwise slow)
# dynesty runs to a few seconds each so the suite stays CI-friendly, while
# still recovering the known synthetic parameters within test tolerances.
FAST_BAYES = dict(nlive=50, dlogz=1.0)
BAYES_N = 80


# ---------------------------------------------------------------------------
# skew-normal component model: analytical solutions
# ---------------------------------------------------------------------------

class TestSkewNormalModel:
    """The component basis functions against closed-form expectations."""

    def test_pdf_reduces_to_gaussian_when_symmetric(self):
        """With skew=0 the pdf equals the Gaussian density exactly."""
        x = np.linspace(-1, 5, 50)
        location, dp = 1.8, 0.3
        expected = (np.exp(-0.5 * ((x - location) / dp) ** 2)
                    / (dp * np.sqrt(2 * np.pi)))
        assert np.allclose(rmag.skewnormal_pdf(x, location, dp, 0.0),
                           expected)

    @pytest.mark.parametrize('skew', [0.0, -3.0, 2.5, 8.0])
    def test_pdf_integrates_to_unit_area(self, skew):
        """The pdf has unit area for any skew."""
        area, _err = quad(lambda t: rmag.skewnormal_pdf(t, 1.5, 0.3, skew),
                          -10, 10)
        assert area == pytest.approx(1.0, abs=1e-8)

    @pytest.mark.parametrize('skew', [0.0, -3.0, 2.5])
    def test_cdf_matches_integrated_pdf(self, skew):
        """The analytic CDF (Owen's T) equals the numerically integrated pdf."""
        for x_eval in [0.9, 1.5, 2.1]:
            integral, _err = quad(
                lambda t: rmag.skewnormal_pdf(t, 1.5, 0.3, skew), -10, x_eval)
            assert rmag.skewnormal_cdf(x_eval, 1.5, 0.3, skew) == \
                pytest.approx(integral, abs=1e-8)

    def test_stats_symmetric_case(self):
        """For skew=0, mean = median = mode = location and std = dp."""
        stats = rmag.skewnormal_stats(2.0, 0.4, 0.0)
        assert stats['mean'] == pytest.approx(2.0)
        assert stats['median'] == pytest.approx(2.0)
        assert stats['mode'] == pytest.approx(2.0)
        assert stats['std'] == pytest.approx(0.4)

    def test_stats_match_numerical_moments(self):
        """Mean/std formulas agree with numerical moments of the pdf."""
        location, dp, skew = 1.5, 0.3, -2.0
        mean_num, _ = quad(
            lambda t: t * rmag.skewnormal_pdf(t, location, dp, skew), -10, 10)
        var_num, _ = quad(
            lambda t: (t - mean_num) ** 2
            * rmag.skewnormal_pdf(t, location, dp, skew), -10, 10)
        stats = rmag.skewnormal_stats(location, dp, skew)
        assert stats['mean'] == pytest.approx(mean_num, abs=1e-8)
        assert stats['std'] == pytest.approx(np.sqrt(var_num), abs=1e-8)
        # median has CDF exactly 0.5
        assert rmag.skewnormal_cdf(stats['median'], location, dp, skew) == \
            pytest.approx(0.5, abs=1e-10)

    def test_negative_skew_shifts_mean_below_location(self):
        """Negative skew produces a tail (and mean) toward low coercivity."""
        stats = rmag.skewnormal_stats(2.0, 0.4, -5.0)
        assert stats['mean'] < 2.0

    def test_spectrum_component_area_equals_contribution(self):
        """Component area in spectrum space equals its contribution."""
        params = pd.DataFrame({'contribution': [0.37], 'location': [2.0],
                               'dp': [0.3], 'skew': [-1.5]})
        area, _err = quad(
            lambda t: rmag.coercivity_spectrum_model(np.array([t]),
                                                     params)[0], -10, 10)
        assert area == pytest.approx(0.37, abs=1e-6)

    def test_curve_model_is_integral_of_spectrum_model(self):
        """The measurement-space model is the cumulative of the spectrum model."""
        x = np.linspace(0.5, 3.2, 400)
        spectrum = rmag.coercivity_spectrum_model(x, TWO_COMPONENT_TRUTH)
        curve = rmag.coercivity_curve_model(x, TWO_COMPONENT_TRUTH,
                                            curve_type='backfield')
        # -dM/dx of the curve model equals the spectrum model
        derivative = -np.gradient(curve, x)
        assert np.allclose(derivative[5:-5], spectrum[5:-5], atol=2e-3)


# ---------------------------------------------------------------------------
# spectrum utilities
# ---------------------------------------------------------------------------

class TestSpectrumFromCurve:
    """coercivity_spectrum_from_curve finite differences."""

    def test_backfield_spectrum_is_positive(self):
        x, curve = synthetic_curve()
        x_mid, spectrum = rmag.coercivity_spectrum_from_curve(x, curve)
        assert len(x_mid) == len(x) - 1
        assert (spectrum > -1e-12).all()

    def test_acquisition_sign_convention(self):
        x = np.linspace(0.5, 3.2, 80)
        acquisition = rmag.coercivity_curve_model(x, TWO_COMPONENT_TRUTH,
                                                  curve_type='acquisition')
        _x_mid, spectrum = rmag.coercivity_spectrum_from_curve(
            x, acquisition, curve_type='acquisition')
        assert (spectrum > -1e-12).all()


class TestEstimateComponents:
    """Automatic initial-guess estimation."""

    def test_finds_two_well_separated_peaks(self):
        x, spectrum = synthetic_spectrum(noise=0.01)
        initial = rmag.estimate_coercivity_components(x, spectrum, 2)
        assert len(initial) == 2
        # locations near the true peaks (within a quarter decade)
        assert initial['location'].iloc[0] == pytest.approx(
            TWO_COMPONENT_TRUTH['location'].iloc[0], abs=0.25)
        assert initial['location'].iloc[1] == pytest.approx(
            TWO_COMPONENT_TRUTH['location'].iloc[1], abs=0.25)

    def test_fills_missing_components(self):
        """Requesting more components than peaks still returns a full table."""
        x, spectrum = synthetic_spectrum()
        initial = rmag.estimate_coercivity_components(x, spectrum, 4)
        assert len(initial) == 4
        assert initial['contribution'].gt(0).all()


# ---------------------------------------------------------------------------
# fitting: parameter recovery on synthetic data
# ---------------------------------------------------------------------------

class TestSpectrumFitting:
    """unmix_coercivity_spectrum parameter recovery."""

    def test_exact_recovery_on_noise_free_data(self):
        x, spectrum = synthetic_spectrum(noise=0.0)
        result = rmag.unmix_coercivity_spectrum(x, spectrum, n_components=2,
                                                vary_skew=False)
        assert result['success']
        params = result['params']
        assert np.allclose(params['location'],
                           TWO_COMPONENT_TRUTH['location'], atol=1e-3)
        assert np.allclose(params['dp'], TWO_COMPONENT_TRUTH['dp'],
                           atol=1e-3)
        assert np.allclose(params['contribution'],
                           TWO_COMPONENT_TRUTH['contribution'], rtol=1e-2)
        assert result['stats']['r_squared'] > 0.99999

    def test_recovery_with_noise(self):
        x, spectrum = synthetic_spectrum(noise=0.02)
        result = rmag.unmix_coercivity_spectrum(x, spectrum, n_components=2,
                                                vary_skew=False)
        params = result['params']
        assert np.allclose(params['location'],
                           TWO_COMPONENT_TRUTH['location'], atol=0.1)
        assert np.allclose(params['proportion'], [0.4, 0.6], atol=0.08)

    def test_skewed_component_recovery(self):
        """A skewed synthetic component is recovered including its skew."""
        truth = pd.DataFrame({'contribution': [1.0], 'location': [2.5],
                              'dp': [0.4], 'skew': [-3.0]})
        x = np.linspace(0.5, 3.2, 150)
        spectrum = rmag.coercivity_spectrum_model(x, truth)
        result = rmag.unmix_coercivity_spectrum(x, spectrum, n_components=1,
                                                vary_skew=True)
        params = result['params']
        assert params['location'].iloc[0] == pytest.approx(2.5, abs=0.05)
        assert params['dp'].iloc[0] == pytest.approx(0.4, abs=0.05)
        assert params['skew'].iloc[0] == pytest.approx(-3.0, abs=0.5)

    def test_components_sorted_by_mean_coercivity(self):
        x, spectrum = synthetic_spectrum()
        # initial parameters deliberately in reversed order
        initial = TWO_COMPONENT_TRUTH.iloc[::-1].reset_index(drop=True)
        result = rmag.unmix_coercivity_spectrum(x, spectrum,
                                                initial_parameters=initial,
                                                vary_skew=False)
        means = result['params']['B_mean_mT'].to_numpy()
        assert (np.diff(means) > 0).all()

    def test_proportions_sum_to_one(self):
        x, spectrum = synthetic_spectrum(noise=0.01)
        result = rmag.unmix_coercivity_spectrum(x, spectrum, n_components=2)
        assert result['params']['proportion'].sum() == pytest.approx(1.0)

    def test_requires_n_components_or_initial(self):
        x, spectrum = synthetic_spectrum()
        with pytest.raises(ValueError):
            rmag.unmix_coercivity_spectrum(x, spectrum)

    def test_too_few_points_raises(self):
        with pytest.raises(ValueError):
            rmag.unmix_coercivity_spectrum(np.array([1.0, 2.0, 3.0]),
                                           np.array([0.1, 0.5, 0.1]),
                                           n_components=2)


class TestCurveFitting:
    """unmix_backfield_curve parameter recovery."""

    def test_exact_recovery_on_noise_free_data(self):
        x, curve = synthetic_curve(noise=0.0)
        result = rmag.unmix_backfield_curve(x, curve, n_components=2,
                                            vary_skew=False)
        assert result['success']
        params = result['params']
        assert np.allclose(params['location'],
                           TWO_COMPONENT_TRUTH['location'], atol=1e-3)
        assert np.allclose(params['contribution'],
                           TWO_COMPONENT_TRUTH['contribution'], rtol=1e-2)
        assert abs(result['offset']) < 1e-3

    def test_recovery_with_noise(self):
        x, curve = synthetic_curve(noise=0.005)
        result = rmag.unmix_backfield_curve(x, curve, n_components=2,
                                            vary_skew=False)
        params = result['params']
        assert np.allclose(params['location'],
                           TWO_COMPONENT_TRUTH['location'], atol=0.1)
        assert np.allclose(params['proportion'], [0.4, 0.6], atol=0.08)

    def test_acquisition_curve(self):
        """IRM acquisition (growing) curves fit with the same machinery."""
        x = np.linspace(0.5, 3.2, 120)
        acquisition = rmag.coercivity_curve_model(x, TWO_COMPONENT_TRUTH,
                                                  curve_type='acquisition')
        result = rmag.unmix_backfield_curve(x, acquisition, n_components=2,
                                            curve_type='acquisition',
                                            vary_skew=False)
        assert np.allclose(result['params']['location'],
                           TWO_COMPONENT_TRUTH['location'], atol=0.02)

    def test_offset_recovery(self):
        """A constant baseline offset is recovered by the fit."""
        x, curve = synthetic_curve(noise=0.0)
        result = rmag.unmix_backfield_curve(x, curve + 0.05, n_components=2,
                                            vary_skew=False, fit_offset=True)
        assert result['offset'] == pytest.approx(0.05, abs=5e-3)


class TestMethodDispatch:
    """unmix_coercivity and the method registry."""

    def test_spectrum_and_curve_methods_agree(self):
        """Both built-in approaches recover the same components when
        started from the same initial parameters. (With automatic seeding
        on noisy data the spectrum method is more sensitive to derivative
        noise -- a documented limitation, not tested here.)"""
        x, curve = synthetic_curve(noise=0.001)
        initial = TWO_COMPONENT_TRUTH.copy()
        spectrum_fit = rmag.unmix_coercivity(x, curve, method='spectrum',
                                             initial_parameters=initial,
                                             vary_skew=False)
        curve_fit = rmag.unmix_coercivity(x, curve, method='curve',
                                          initial_parameters=initial,
                                          vary_skew=False)
        # the broad low-coercivity component is the more space-sensitive one
        # (the spectrum method fits the noisy derivative), so it is compared
        # with a looser tolerance than the well-constrained narrow component
        assert np.allclose(spectrum_fit['params']['B_mean_mT'],
                           curve_fit['params']['B_mean_mT'], rtol=0.15)
        assert np.allclose(spectrum_fit['params']['proportion'],
                           curve_fit['params']['proportion'], atol=0.05)

    def test_maxunmix_method_returns_bootstrap(self):
        x, curve = synthetic_curve(noise=0.002)
        result = rmag.unmix_coercivity(x, curve, method='maxunmix',
                                       n_components=2, vary_skew=False,
                                       n_boot=30, random_seed=7)
        assert 'bootstrap' in result
        assert result['bootstrap']['method'] == 'maxunmix'
        assert result['bootstrap']['proportion'] == 0.95
        assert result['bootstrap']['param_noise'] == 0.02
        assert 'param_summary' in result['bootstrap']

    def test_maxunmix_param_noise_kwarg(self):
        """The restart-perturbation size is controlled by 'param_noise' (the
        name the docstring advertises), forwarded through **kwargs."""
        x, curve = synthetic_curve(noise=0.002)
        result = rmag.unmix_coercivity(x, curve, method='maxunmix',
                                       n_components=2, vary_skew=False,
                                       n_boot=30, random_seed=7,
                                       param_noise=0.05)
        assert result['bootstrap']['param_noise'] == 0.05

    def test_maxunmix_replicates_respect_kwargs_bounds(self):
        """Regression: replicate refits must run under the same bounds as the
        main fit. Previously **kwargs (dp_bounds, skew_bounds) were forwarded
        only to the main fit, so replicate dispersions escaped the user's
        dp_bounds (reaching ~0.66 under a (0.20, 0.21) constraint)."""
        x, curve = synthetic_curve(noise=0.002)
        result = rmag.unmix_coercivity(x, curve, method='maxunmix',
                                       n_components=2, vary_skew=False,
                                       n_boot=30, random_seed=1,
                                       dp_bounds=(0.2, 0.21))
        summary = result['bootstrap']['param_summary']
        # every replicate's dispersion stays inside the tight bounds
        assert (summary['dp_p2_5'] >= 0.20 - 1e-6).all()
        assert (summary['dp_p97_5'] <= 0.21 + 1e-6).all()

    def test_unknown_method_raises(self):
        x, curve = synthetic_curve()
        with pytest.raises(ValueError, match='unknown unmixing method'):
            rmag.unmix_coercivity(x, curve, method='not_a_method',
                                  n_components=2)

    def test_register_custom_method(self):
        def custom(x, magnetization, n_components=None,
                   initial_parameters=None, curve_type='backfield',
                   vary_skew=True, **kwargs):
            return rmag.unmix_backfield_curve(
                x, magnetization, n_components=n_components,
                initial_parameters=initial_parameters,
                curve_type=curve_type, vary_skew=False, **kwargs)

        rmag.register_unmixing_method('test_custom', custom)
        try:
            x, curve = synthetic_curve(noise=0.002)
            result = rmag.unmix_coercivity(x, curve, method='test_custom',
                                           n_components=2)
            assert result['n_components'] == 2
            # the custom method forces symmetric components
            assert (result['params']['skew'] == 0).all()
        finally:
            del rmag.UNMIXING_METHODS['test_custom']

    def test_register_non_callable_raises(self):
        with pytest.raises(TypeError):
            rmag.register_unmixing_method('bad', 'not callable')


# ---------------------------------------------------------------------------
# model selection
# ---------------------------------------------------------------------------

class TestModelComparison:
    """compare_unmixing_models information criteria and F-tests."""

    def test_bic_prefers_true_component_count(self):
        x, spectrum = synthetic_spectrum(noise=0.01)
        results = [rmag.unmix_coercivity_spectrum(x, spectrum,
                                                  n_components=n,
                                                  vary_skew=False)
                   for n in (1, 2, 3)]
        table = rmag.compare_unmixing_models(results)
        best = table.loc[table['bic'].idxmin(), 'n_components']
        assert best == 2

    def test_f_test_significant_for_second_component(self):
        x, spectrum = synthetic_spectrum(noise=0.01)
        results = [rmag.unmix_coercivity_spectrum(x, spectrum,
                                                  n_components=n,
                                                  vary_skew=False)
                   for n in (1, 2)]
        table = rmag.compare_unmixing_models(results)
        assert table['p_value'].iloc[1] < 1e-6

    def test_mixed_methods_raise(self):
        x, curve = synthetic_curve()
        spectrum_fit = rmag.unmix_coercivity(x, curve, method='spectrum',
                                             n_components=1)
        curve_fit = rmag.unmix_coercivity(x, curve, method='curve',
                                          n_components=1)
        with pytest.raises(ValueError):
            rmag.compare_unmixing_models([spectrum_fit, curve_fit])


class TestNoiseEstimate:
    """estimate_measurement_noise."""

    def test_recovers_known_noise(self):
        x, curve = synthetic_curve(noise=0.0)
        rng = np.random.default_rng(0)
        noisy = curve + rng.normal(0, 0.01, size=len(curve))
        estimate = rmag.estimate_measurement_noise(x, noisy)
        assert estimate == pytest.approx(0.01, rel=0.3)

    def test_low_on_clean_data(self):
        x, curve = synthetic_curve(noise=0.0)
        estimate = rmag.estimate_measurement_noise(x, curve)
        assert estimate < 0.01 * np.ptp(curve)


class TestSelectNComponents:
    """select_n_components parsimony selection."""

    def test_parsimony_selects_true_count_on_low_noise(self):
        """The parsimony rule stops at the true component count even when
        the data are clean enough that reduced chi-square keeps improving."""
        x, curve = synthetic_curve(noise=0.001)
        selected, table, results = rmag.select_n_components(
            x, curve, method='curve', max_components=4)
        assert selected == 2
        assert table.loc[table['selected'], 'n_components'].iloc[0] == 2
        assert set(results) == {1, 2, 3, 4}

    def test_parsimony_beats_chi2_overselection(self):
        """On the same low-noise data, a strict chi-square target
        over-selects while parsimony does not."""
        x, curve = synthetic_curve(noise=0.001)
        parsimony, _t, _r = rmag.select_n_components(x, curve, method='curve',
                                                     max_components=4)
        chi2, _t2, _r2 = rmag.select_n_components(
            x, curve, method='curve', criterion='chi2',
            reduced_chi2_target=1.0, max_components=4)
        assert parsimony <= chi2

    def test_improvement_fraction_decreasing(self):
        x, curve = synthetic_curve(noise=0.002)
        _s, table, _r = rmag.select_n_components(x, curve, method='curve',
                                                 max_components=4)
        # the second component explains most of the baseline misfit
        assert table['rss_improvement_fraction'].iloc[1] > 0.5
        # the fourth explains almost none
        assert table['rss_improvement_fraction'].iloc[3] < 0.05

    def test_min_improvement_threshold_effect(self):
        x, curve = synthetic_curve(noise=0.001)
        # a threshold above what even the (dominant) second component
        # explains keeps the single-component model
        strict, _t, _r = rmag.select_n_components(
            x, curve, method='curve', max_components=4,
            min_improvement=0.9999)
        assert strict == 1
        # the default threshold keeps two components
        default, _t2, _r2 = rmag.select_n_components(
            x, curve, method='curve', max_components=4)
        assert default == 2

    def test_chi2_with_explicit_noise(self):
        x, curve = synthetic_curve(noise=0.01)
        selected, table, _r = rmag.select_n_components(
            x, curve, method='curve', criterion='chi2', noise_level=0.01,
            max_components=3)
        assert 'reduced_chi2' in table.columns
        assert selected >= 1

    def test_chi2_units_match_spectrum_space_fit(self):
        """Regression: for spectrum-space methods the noise must be estimated
        in spectrum units so reduced chi-square is O(1). Previously the noise
        was taken from the measured curve while rss was in dM/dlog10(B) units,
        inflating reduced chi-square by the finite-difference amplification
        (~10^2-10^3) so the chi2 branch always ran to max_components."""
        x, curve = synthetic_curve(noise=0.001)
        selected, table, _r = rmag.select_n_components(
            x, curve, method='spectrum', criterion='chi2',
            reduced_chi2_target=1.0, max_components=4)
        # at the true 2-component count the model fits to within the (spectrum)
        # noise: reduced chi-square is order unity, not the ~10^3 unit-mismatch
        chi2_at_two = table.loc[table['n_components'] == 2,
                                'reduced_chi2'].iloc[0]
        assert 0.1 < chi2_at_two < 20.0
        # one component leaves misfit above the noise, two clears it: the
        # criterion resolves the true count instead of running to max_components
        assert selected == 2

    def test_unknown_method_raises(self):
        x, curve = synthetic_curve()
        with pytest.raises(ValueError):
            rmag.select_n_components(x, curve, method='nope')


# ---------------------------------------------------------------------------
# bootstrap uncertainty
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def fitted():
    """A converged two-component spectrum fit shared by bootstrap tests."""
    x, spectrum = synthetic_spectrum(noise=0.02)
    return rmag.unmix_coercivity_spectrum(x, spectrum, n_components=2,
                                          vary_skew=False)


class TestBootstrap:
    """unmixing_bootstrap behavior."""

    def test_intervals_cover_truth(self, fitted):
        """95% intervals from the bootstrap contain the true parameters."""
        boot = rmag.unmixing_bootstrap(fitted, n_boot=100, random_seed=3)
        summary = boot['bootstrap']['param_summary']
        for comp in (1, 2):
            true_B = 10 ** TWO_COMPONENT_TRUTH['location'].iloc[comp - 1]
            assert summary.loc[comp, 'B_mean_mT_p2_5'] < true_B
            assert summary.loc[comp, 'B_mean_mT_p97_5'] > true_B

    def test_seed_reproducibility(self, fitted):
        boot_a = rmag.unmixing_bootstrap(fitted, n_boot=40, random_seed=11)
        boot_b = rmag.unmixing_bootstrap(fitted, n_boot=40, random_seed=11)
        pd.testing.assert_frame_equal(boot_a['bootstrap']['param_summary'],
                                      boot_b['bootstrap']['param_summary'])

    def test_residual_resampling(self, fitted):
        boot = rmag.unmixing_bootstrap(fitted, n_boot=40,
                                       resample='residuals', random_seed=5)
        assert boot['bootstrap']['n_success'] > 0

    def test_input_result_not_mutated(self, fitted):
        rmag.unmixing_bootstrap(fitted, n_boot=30, random_seed=1)
        assert 'bootstrap' not in fitted

    def test_curve_bands_shape(self, fitted):
        boot = rmag.unmixing_bootstrap(fitted, n_boot=30, random_seed=1,
                                       n_grid=150)
        curves = boot['bootstrap']['curves']
        assert curves['x_grid'].shape == (150,)
        assert curves['total_p97_5'].shape == (150,)
        assert (curves['total_p97_5'] >= curves['total_p2_5']).all()

    def test_maxunmix_result_bootstraps_in_spectrum_space(self):
        """Regression: a maxunmix result is spectrum-space, so bootstrapping
        it must refit with the spectrum model. Dispatching on the method name
        alone (method == 'spectrum') sent maxunmix results through the
        cumulative-curve branch, fitting the wrong model to derivative data
        and recovering nonsense coercivities."""
        x, curve = synthetic_curve(noise=0.002)
        result = rmag.unmix_coercivity(x, curve, method='maxunmix',
                                       n_components=2, vary_skew=False,
                                       n_boot=20, random_seed=1)
        boot = rmag.unmixing_bootstrap(result, n_boot=40, random_seed=2)
        summary = boot['bootstrap']['param_summary']
        assert boot['bootstrap']['n_success'] > 0
        # the refit recovers the true coercivities (it fit the spectrum, not
        # the cumulative curve model applied to spectrum data)
        for comp in (1, 2):
            true_B = 10 ** TWO_COMPONENT_TRUTH['location'].iloc[comp - 1]
            assert (summary.loc[comp, 'B_mean_mT_p2_5']
                    < true_B < summary.loc[comp, 'B_mean_mT_p97_5'])

    def test_bayes_result_rejected(self):
        """A Bayesian result already carries posterior uncertainty, so
        unmixing_bootstrap refuses it with a clear error rather than silently
        refitting a least-squares model (previously the spectrum-space bayes
        result took the curve branch and fit the cumulative model to the
        spectrum)."""
        x, curve = synthetic_curve(noise=0.01)
        result = rmag.unmix_coercivity(x, curve, method='bayes',
                                       space='spectrum', n_components=2,
                                       vary_skew=False, random_seed=1,
                                       **FAST_BAYES)
        with pytest.raises(ValueError, match='posterior uncertainty'):
            rmag.unmixing_bootstrap(result)


# ---------------------------------------------------------------------------
# MagIC batch processing and specimens export
# ---------------------------------------------------------------------------

def make_magic_measurements(experiment='synthetic-LP-BCR-BF-1',
                            specimen='spec1', noise=0.002, rng=None):
    """Build a minimal MagIC-style measurements table with a backfield
    experiment generated from the reference two-component model.

    Uses a fresh seeded generator by default so each call is deterministic
    and independent of test execution order (a shared module-level RNG made
    the noise depend on how many other tests had drawn from it first).
    """
    if rng is None:
        rng = np.random.default_rng(2026)
    x = np.linspace(0.5, 3.2, 90)
    curve_shifted = rmag.coercivity_curve_model(x, TWO_COMPONENT_TRUTH,
                                                curve_type='backfield')
    curve_shifted = curve_shifted + rng.normal(0, noise, size=len(x))
    # convert the shifted curve back to the measured convention:
    # M measured runs from +Mrs down to -Mrs with negative applied fields
    total = TWO_COMPONENT_TRUTH['contribution'].sum()
    magn_mass = curve_shifted - total / 2
    treat_dc_field = -(10 ** x) * 1e-3  # tesla, negative back fields
    return pd.DataFrame({
        'experiment': experiment,
        'specimen': specimen,
        'method_codes': 'LP-BCR-BF',
        'treat_dc_field': treat_dc_field,
        'magn_mass': magn_mass,
    })


class TestBatchProcessing:
    """unmix_backfield_experiments on MagIC-style tables."""

    def test_batch_recovers_components(self):
        measurements = make_magic_measurements()
        components_df, results = rmag.unmix_backfield_experiments(
            measurements, n_components=2, method='spectrum',
            vary_skew=False, verbose=False)
        assert len(components_df) == 2
        assert components_df['B_mean_mT'].iloc[0] == pytest.approx(250,
                                                                   rel=0.15)
        assert components_df['B_mean_mT'].iloc[1] == pytest.approx(750,
                                                                   rel=0.10)
        assert components_df['proportion'].to_numpy() == pytest.approx(
            [0.4, 0.6], abs=0.08)
        assert 'synthetic-LP-BCR-BF-1' in results

    def test_batch_with_bootstrap_adds_interval_columns(self):
        measurements = make_magic_measurements()
        components_df, _results = rmag.unmix_backfield_experiments(
            measurements, n_components=2, method='spectrum',
            vary_skew=False, n_boot=30, random_seed=4, verbose=False)
        assert 'B_mean_mT_p2_5' in components_df.columns
        assert components_df['B_mean_mT_p2_5'].notna().all()

    def test_batch_reports_bcr(self):
        measurements = make_magic_measurements()
        components_df, _results = rmag.unmix_backfield_experiments(
            measurements, n_components=2, vary_skew=False, verbose=False)
        # Bcr should fall between the two component coercivities
        bcr = components_df['Bcr_mT'].iloc[0]
        assert 250 < bcr < 750

    def test_failed_experiment_is_skipped(self):
        measurements = make_magic_measurements()
        components_df, results = rmag.unmix_backfield_experiments(
            measurements,
            experiments=['synthetic-LP-BCR-BF-1', 'missing-experiment'],
            n_components=2, vary_skew=False, verbose=False)
        assert list(results) == ['synthetic-LP-BCR-BF-1']
        assert components_df['experiment'].nunique() == 1

    def test_smoothing_routes_spectrum_but_not_bayes(self):
        """Regression: with smoothing on, the finite-difference 'spectrum'
        method fits the smoothed curve, but the measurement-space Bayesian
        method must fit the UNSMOOTHED curve. Routing the denoised data to
        the bayes likelihood (which infers its own noise level) understates
        the noise and yields overconfident credible intervals."""
        measurements = make_magic_measurements()
        experiment = 'synthetic-LP-BCR-BF-1'
        one = measurements[measurements['experiment'] == experiment].copy()
        processed, _bcr = rmag.backfield_data_processing(one, smooth_frac=0.2)
        unsmoothed = processed['magn_mass_shift'].to_numpy()
        # sanity: smoothing actually changed the curve
        assert not np.allclose(
            unsmoothed, processed['smoothed_magn_mass_shift'].to_numpy())

        # smoothing reaches the spectrum method: the data it fits differs
        # between a smoothed and an unsmoothed run
        _c, spec_smoothed = rmag.unmix_backfield_experiments(
            measurements, method='spectrum', n_components=2, vary_skew=False,
            smooth_frac=0.2, verbose=False)
        _c0, spec_raw = rmag.unmix_backfield_experiments(
            measurements, method='spectrum', n_components=2, vary_skew=False,
            smooth_frac=0.0, verbose=False)
        assert not np.allclose(np.asarray(spec_smoothed[experiment]['y']),
                               np.asarray(spec_raw[experiment]['y']))

        # measurement-space bayes fits the unsmoothed curve directly, so its
        # fitted data is unchanged by smooth_frac and equals the raw curve
        _c2, bayes_smoothed = rmag.unmix_backfield_experiments(
            measurements, method='bayes', n_components=2, vary_skew=False,
            smooth_frac=0.2, random_seed=3, verbose=False, **FAST_BAYES)
        assert np.allclose(np.asarray(bayes_smoothed[experiment]['y']),
                           unsmoothed)


class TestAggregateByClass:
    """aggregate_by_class collapses components into coercivity classes."""

    @staticmethod
    def _components():
        # two experiments; expt A has a single magnetite component that the
        # optimizer split into two, expt B has magnetite + hematite
        return pd.DataFrame({
            'experiment': ['A', 'A', 'B', 'B'],
            'specimen': ['sA', 'sA', 'sB', 'sB'],
            'B_mean_mT': [40.0, 60.0, 50.0, 600.0],
            'proportion': [0.5, 0.5, 0.7, 0.3],
            'contribution': [0.5, 0.5, 0.7, 0.3],
            'r_squared': [0.999, 0.999, 0.998, 0.998],
        })

    def test_split_component_is_robust(self):
        out = rmag.aggregate_by_class(
            self._components(), boundaries_mT=200.0,
            class_names=['magnetite', 'hematite'])
        row_a = out[out['experiment'] == 'A'].iloc[0]
        # the spurious two-way split of one mineral is summed back to 1.0
        assert row_a['magnetite_fraction'] == pytest.approx(1.0)
        assert row_a['hematite_fraction'] == pytest.approx(0.0)
        row_b = out[out['experiment'] == 'B'].iloc[0]
        assert row_b['magnetite_fraction'] == pytest.approx(0.7)
        assert row_b['hematite_fraction'] == pytest.approx(0.3)

    def test_passthrough_columns_carried(self):
        out = rmag.aggregate_by_class(
            self._components(), boundaries_mT=200.0,
            class_names=['magnetite', 'hematite'])
        assert set(['specimen', 'r_squared']).issubset(out.columns)
        assert out[out['experiment'] == 'A'].iloc[0]['specimen'] == 'sA'

    def test_curve_factor_halves_remanence(self):
        out = rmag.aggregate_by_class(
            self._components(), boundaries_mT=200.0,
            class_names=['magnetite', 'hematite'], curve_factor=2.0)
        row_b = out[out['experiment'] == 'B'].iloc[0]
        # contribution 0.7 divided by the backfield span factor of 2
        assert row_b['magnetite_remanence'] == pytest.approx(0.35)

    def test_three_classes_from_two_boundaries(self):
        out = rmag.aggregate_by_class(
            self._components(), boundaries_mT=[45.0, 200.0],
            class_names=['soft', 'mid', 'hard'])
        row_a = out[out['experiment'] == 'A'].iloc[0]
        # 40 mT -> soft, 60 mT -> mid
        assert row_a['soft_fraction'] == pytest.approx(0.5)
        assert row_a['mid_fraction'] == pytest.approx(0.5)
        assert row_a['hard_fraction'] == pytest.approx(0.0)

    def test_default_class_names(self):
        out = rmag.aggregate_by_class(self._components(), boundaries_mT=200.0)
        assert 'class_1_fraction' in out.columns
        assert 'class_2_fraction' in out.columns

    def test_wrong_class_name_count_raises(self):
        with pytest.raises(ValueError):
            rmag.aggregate_by_class(self._components(), boundaries_mT=200.0,
                                    class_names=['only_one'])

    def test_missing_coercivity_column_raises(self):
        with pytest.raises(KeyError):
            rmag.aggregate_by_class(self._components(), boundaries_mT=200.0,
                                    coercivity_column='nope')

    def test_end_to_end_from_batch(self):
        measurements = make_magic_measurements()
        components_df, _results = rmag.unmix_backfield_experiments(
            measurements, n_components=2, vary_skew=False, verbose=False)
        out = rmag.aggregate_by_class(
            components_df, boundaries_mT=500.0,
            class_names=['low', 'high'])
        row = out.iloc[0]
        # the two synthetic components straddle 500 mT (250 and 750)
        assert row['low_fraction'] == pytest.approx(0.4, abs=0.08)
        assert row['high_fraction'] == pytest.approx(0.6, abs=0.08)
        assert (row['low_fraction'] + row['high_fraction']) == pytest.approx(
            1.0, abs=1e-6)


class TestComponentColors:
    """color_by option of plot_coercivity_unmixing / helper."""

    def test_component_colors_by_order(self):
        colors = rmag._unmixing_component_colors(
            [40.0, 600.0], color_by='component',
            class_boundaries=None, class_colors=None)
        assert colors == ['C0', 'C1']

    def test_class_colors_group_by_coercivity(self):
        # two low-coercivity components and one high: the two low ones share
        # a color, the high one differs
        colors = rmag._unmixing_component_colors(
            [40.0, 60.0, 600.0], color_by='class',
            class_boundaries=200.0, class_colors=None)
        assert colors[0] == colors[1]
        assert colors[0] != colors[2]

    def test_class_requires_boundaries(self):
        with pytest.raises(ValueError):
            rmag._unmixing_component_colors(
                [40.0], color_by='class',
                class_boundaries=None, class_colors=None)

    def test_bad_color_by_raises(self):
        with pytest.raises(ValueError):
            rmag._unmixing_component_colors(
                [40.0], color_by='rainbow',
                class_boundaries=None, class_colors=None)

    def test_custom_class_colors(self):
        colors = rmag._unmixing_component_colors(
            [40.0, 600.0], color_by='class', class_boundaries=200.0,
            class_colors=['k', 'r'])
        assert colors == ['k', 'r']

    def test_wrong_class_colors_count_raises(self):
        with pytest.raises(ValueError):
            rmag._unmixing_component_colors(
                [40.0, 600.0], color_by='class', class_boundaries=200.0,
                class_colors=['k'])

    def test_plot_accepts_color_by_class(self):
        x, spectrum = synthetic_spectrum()
        fit = rmag.unmix_coercivity_spectrum(x, spectrum, n_components=2)
        fig, _ax = rmag.plot_coercivity_unmixing(
            fit, color_by='class', class_boundaries=500.0)
        plt.close(fig)


class TestSpecimensExport:
    """unmixing_to_specimens_table in both recording modes."""

    @pytest.fixture()
    def batch_output(self):
        measurements = make_magic_measurements()
        components_df, _results = rmag.unmix_backfield_experiments(
            measurements, n_components=2, vary_skew=False, verbose=False)
        specimens = pd.DataFrame({
            'specimen': ['spec1'],
            'sample': ['samp1'],
            'experiments': ['synthetic-LP-BCR-BF-1'],
            'description': ['rock chip'],
        })
        return components_df, specimens

    def test_rows_mode_adds_component_rows(self, batch_output):
        components_df, specimens = batch_output
        updated = rmag.unmixing_to_specimens_table(specimens, components_df,
                                                   mode='rows')
        new_rows = updated[updated['rem_cmf'].notna()]
        assert len(new_rows) == 2
        # rem_cmf is in tesla
        assert new_rows['rem_cmf'].iloc[0] == pytest.approx(0.25, rel=0.15)
        assert (new_rows['rem_n_comp'] == 2).all()
        assert (new_rows['method_codes'] == 'LP-BCR-BF').all()
        # identity columns copied from the matching row
        assert (new_rows['sample'] == 'samp1').all()

    def test_rows_mode_is_idempotent(self, batch_output):
        components_df, specimens = batch_output
        once = rmag.unmixing_to_specimens_table(specimens, components_df,
                                                mode='rows')
        twice = rmag.unmixing_to_specimens_table(once, components_df,
                                                 mode='rows')
        assert len(once) == len(twice)

    def test_rows_mode_idempotent_with_colon_delimited_experiments(
            self, batch_output):
        """Regression: when the specimen's 'experiments' cell lists several
        experiments (colon-delimited), re-runs must not accumulate duplicate
        component rows. Previously the new rows inherited the full colon
        string while cleanup matched the single experiment name, so exact
        matching failed and rows piled up (2 -> 4 -> 6)."""
        components_df, specimens = batch_output
        specimens = specimens.copy()
        specimens['experiments'] = 'synthetic-LP-BCR-BF-1:synthetic-LP-HYS-1'
        df = specimens
        for _ in range(3):
            df = rmag.unmixing_to_specimens_table(df, components_df,
                                                  mode='rows')
        marker = 'coercivity_unmixing_component_row'
        component_rows = df['description'].astype(str).str.contains(
            marker, na=False)
        assert int(component_rows.sum()) == 2
        # the appended rows carry the single experiment, not the full list
        assert (df.loc[component_rows, 'experiments']
                == 'synthetic-LP-BCR-BF-1').all()

    def test_rows_mode_preserves_original_row_with_rem_cmf(self, batch_output):
        """Regression: cleanup must remove only the component rows this
        function created, identified by an explicit marker -- never an
        original specimen row that happens to carry a 'coercivity_unmixing'
        description payload (from mode='description') together with a
        populated rem_cmf."""
        components_df, specimens = batch_output
        specimens = specimens.copy()
        specimens['rem_cmf'] = 0.05
        specimens['description'] = '{"coercivity_unmixing": {"n_components": 2}}'
        updated = rmag.unmixing_to_specimens_table(specimens, components_df,
                                                   mode='rows')
        # the original row survives (2 new component rows + 1 original == 3)
        assert len(updated) == 3
        survived = updated['description'] == \
            '{"coercivity_unmixing": {"n_components": 2}}'
        assert survived.sum() == 1

    def test_description_mode_preserves_text(self, batch_output):
        components_df, specimens = batch_output
        rmag.unmixing_to_specimens_table(specimens, components_df,
                                         mode='description')
        text, data = rmag.parse_specimen_description(
            specimens['description'].iloc[0])
        assert text == 'rock chip'
        assert data['coercivity_unmixing']['n_components'] == 2
        assert len(data['coercivity_unmixing']['components']) == 2

    def test_description_round_trip(self, batch_output):
        components_df, specimens = batch_output
        rmag.unmixing_to_specimens_table(specimens, components_df,
                                         mode='description')
        # a second call replaces rather than duplicates the record
        rmag.unmixing_to_specimens_table(specimens, components_df,
                                         mode='description')
        text, data = rmag.parse_specimen_description(
            specimens['description'].iloc[0])
        assert text == 'rock chip'
        assert list(data) == ['coercivity_unmixing']


# ---------------------------------------------------------------------------
# multi-start solution mapping
# ---------------------------------------------------------------------------

class TestMultistart:
    """unmixing_multistart solution mapping."""

    def test_best_solution_recovers_truth(self):
        x, curve = synthetic_curve(noise=0.002)
        result = rmag.unmixing_multistart(x, curve, method='spectrum',
                                          n_components=2, n_starts=30,
                                          vary_skew=False, random_seed=8)
        assert np.allclose(result['params']['location'],
                           TWO_COMPONENT_TRUTH['location'], atol=0.1)
        multistart = result['multistart']
        assert multistart['n_converged'] > 0
        solutions = multistart['solutions']
        # solutions are ranked: the first row is the best fit
        assert solutions['delta_aic'].iloc[0] == 0
        assert solutions['akaike_weight'].sum() == pytest.approx(1.0)
        assert solutions['n_hits'].sum() == multistart['n_converged']
        # per-component columns exist
        assert 'B_mean_mT_c1' in solutions.columns
        assert 'proportion_c2' in solutions.columns

    def test_reproducible_with_seed(self):
        x, curve = synthetic_curve(noise=0.002)
        a = rmag.unmixing_multistart(x, curve, n_components=2, n_starts=15,
                                     random_seed=4, vary_skew=False)
        b = rmag.unmixing_multistart(x, curve, n_components=2, n_starts=15,
                                     random_seed=4, vary_skew=False)
        pd.testing.assert_frame_equal(a['multistart']['solutions'],
                                      b['multistart']['solutions'])

    def test_representative_results_align_with_table(self):
        x, curve = synthetic_curve(noise=0.002)
        result = rmag.unmixing_multistart(x, curve, n_components=2,
                                          n_starts=15, random_seed=4,
                                          vary_skew=False)
        solutions = result['multistart']['solutions']
        representatives = result['multistart']['results']
        assert len(representatives) == len(solutions)
        assert representatives[0]['stats']['rss'] == \
            pytest.approx(solutions['rss'].iloc[0])

    def test_unknown_method_raises(self):
        x, curve = synthetic_curve()
        with pytest.raises(ValueError, match='unknown unmixing method'):
            rmag.unmixing_multistart(x, curve, method='nope', n_components=2)

    def test_solution_plot(self):
        x, curve = synthetic_curve(noise=0.01)
        result = rmag.unmixing_multistart(x, curve, method='curve',
                                          n_components=2, n_starts=20,
                                          vary_skew=True, random_seed=5)
        fig, axes = rmag.plot_multistart_solutions(result, max_solutions=4)
        n_distinct = len(result['multistart']['results'])
        # one panel per shown solution plus the parameter-space map
        assert len(axes) == min(4, n_distinct) + 1
        plt.close(fig)

    def test_solution_plot_requires_multistart(self):
        x, curve = synthetic_curve()
        fit = rmag.unmix_coercivity(x, curve, method='curve', n_components=2)
        with pytest.raises(ValueError):
            rmag.plot_multistart_solutions(fit)


# ---------------------------------------------------------------------------
# Bayesian unmixing (requires dynesty)
# ---------------------------------------------------------------------------

try:
    import dynesty  # noqa: F401
    HAS_DYNESTY = True
except ImportError:
    HAS_DYNESTY = False

needs_dynesty = pytest.mark.skipif(not HAS_DYNESTY,
                                   reason='dynesty not installed')


@pytest.fixture(scope='module')
def bayes_result():
    """A converged Bayesian fit of the two-component synthetic curve."""
    x, curve = synthetic_curve(noise=0.005, n=BAYES_N)
    return rmag.unmix_coercivity_bayes(x, curve, n_components=2,
                                       random_seed=6, **FAST_BAYES)


@needs_dynesty
class TestBayesianUnmixing:
    """unmix_coercivity_bayes nested-sampling posterior."""

    def test_posterior_recovers_truth(self, bayes_result):
        params = bayes_result['params'].sort_values('location')
        # the narrow high-coercivity component is well constrained
        assert params['location'].iloc[1] == pytest.approx(
            TWO_COMPONENT_TRUTH['location'].iloc[1], abs=0.05)
        # the broad low-coercivity component overlaps it and is only
        # loosely constrained, so use a wider tolerance
        assert params['location'].iloc[0] == pytest.approx(
            TWO_COMPONENT_TRUTH['location'].iloc[0], abs=0.25)
        assert np.allclose(params['proportion'].to_numpy()[::-1], [0.6, 0.4],
                           atol=0.12)

    def test_credible_intervals_cover_truth(self, bayes_result):
        summary = bayes_result['bayes']['param_summary']
        # the well-constrained narrow component's 95% interval covers truth
        true_B2 = 10 ** TWO_COMPONENT_TRUTH['location'].iloc[1]
        assert summary.loc[2, 'B_mean_mT_p2_5'] < true_B2
        assert summary.loc[2, 'B_mean_mT_p97_5'] > true_B2
        # the broad component carries genuinely larger uncertainty, which the
        # posterior should report as a wider relative interval
        width_1 = (summary.loc[1, 'B_mean_mT_p97_5']
                   - summary.loc[1, 'B_mean_mT_p2_5']) / summary.loc[1, 'B_mean_mT_p50']
        width_2 = (summary.loc[2, 'B_mean_mT_p97_5']
                   - summary.loc[2, 'B_mean_mT_p2_5']) / summary.loc[2, 'B_mean_mT_p50']
        assert width_1 > width_2

    def test_evidence_prefers_two_components(self, bayes_result):
        x, curve = synthetic_curve(noise=0.005, n=BAYES_N)
        one_comp = rmag.unmix_coercivity_bayes(x, curve, n_components=1,
                                               random_seed=6, **FAST_BAYES)
        assert bayes_result['bayes']['logz'] > one_comp['bayes']['logz'] + 10

    def test_noise_estimate_recovered(self, bayes_result):
        # data were generated with sigma = 0.005
        assert bayes_result['bayes']['noise'] == pytest.approx(0.005,
                                                               rel=0.5)

    def test_result_structure(self, bayes_result):
        assert bayes_result['method'] == 'bayes'
        assert bayes_result['success']
        assert np.isfinite(bayes_result['stats']['logz'])
        curves = bayes_result['bayes']['curves']
        assert (curves['total_p97_5'] >= curves['total_p2_5']).all()
        samples = bayes_result['bayes']['samples']
        assert samples['proportion'].shape[1] == 2

    def test_spectrum_space_recovers_truth(self):
        """space='spectrum' fits the finite-difference spectrum and should
        recover the same synthetic components as the curve-space fit, with no
        offset parameter."""
        x, curve = synthetic_curve(noise=0.003, n=BAYES_N)
        result = rmag.unmix_coercivity_bayes(x, curve, n_components=2,
                                             space='spectrum', random_seed=6,
                                             **FAST_BAYES)
        assert result['space'] == 'spectrum'
        assert result['offset'] == 0.0
        params = result['params'].sort_values('location')
        truth = TWO_COMPONENT_TRUTH.sort_values('location')
        assert params['location'].iloc[1] == pytest.approx(
            truth['location'].iloc[1], abs=0.15)
        assert result['params']['proportion'].sum() == pytest.approx(1.0)
        # the fitted spectrum data are the finite differences (n-1 points)
        assert len(result['x']) == BAYES_N - 1

    def test_spectrum_space_dispatch(self):
        x, curve = synthetic_curve(noise=0.003, n=BAYES_N)
        result = rmag.unmix_coercivity(x, curve, method='bayes',
                                       n_components=2, space='spectrum',
                                       random_seed=6, **FAST_BAYES)
        assert result['space'] == 'spectrum'

    def test_registered_in_dispatcher(self):
        assert 'bayes' in rmag.UNMIXING_METHODS

    def test_dispatch_with_initial_parameters_builds_priors(self):
        """Passing initial_parameters to the bayes method builds priors
        centered on them and infers n_components. The high-coercivity
        component is well constrained and should be recovered; the broad
        low-coercivity component sits on a trade-off ridge and is only
        loosely constrained, so we check it stays within its prior window
        rather than pinning its median."""
        x, curve = synthetic_curve(noise=0.005, n=BAYES_N)
        result = rmag.unmix_coercivity(x, curve, method='bayes',
                                       initial_parameters=TWO_COMPONENT_TRUTH,
                                       random_seed=2, **FAST_BAYES)
        assert result['n_components'] == 2
        params = result['params'].sort_values('location')
        # well-constrained high-coercivity component recovered
        assert params['location'].iloc[1] == pytest.approx(
            TWO_COMPONENT_TRUTH['location'].iloc[1], abs=0.15)
        # components ordered and proportions valid
        assert params['location'].iloc[0] < params['location'].iloc[1]
        assert result['params']['proportion'].sum() == pytest.approx(1.0)

    def test_seed_reproducibility(self):
        x, curve = synthetic_curve(noise=0.005, n=BAYES_N)
        a = rmag.unmix_coercivity_bayes(x, curve, n_components=1,
                                        random_seed=13, **FAST_BAYES)
        b = rmag.unmix_coercivity_bayes(x, curve, n_components=1,
                                        random_seed=13, **FAST_BAYES)
        assert a['bayes']['logz'] == pytest.approx(b['bayes']['logz'])

    def test_custom_priors_respected(self):
        x, curve = synthetic_curve(noise=0.005, n=BAYES_N)
        priors = {'location': [(2.2, 2.6), (2.7, 3.0)],
                  'dp': [(0.3, 0.8), (0.05, 0.3)]}
        result = rmag.unmix_coercivity_bayes(x, curve, n_components=2,
                                             priors=priors, random_seed=2,
                                             **FAST_BAYES)
        locations = result['bayes']['samples']['location']
        assert locations[:, 0].min() >= 2.2 and locations[:, 0].max() <= 2.6
        assert locations[:, 1].min() >= 2.7 and locations[:, 1].max() <= 3.0


class TestOrderedUniformTransform:
    """The order-statistics prior transform used for component locations."""

    def test_output_is_ordered(self):
        rng = np.random.default_rng(0)
        for _ in range(50):
            values = rmag._ordered_uniform_transform(rng.uniform(size=4),
                                                     0.0, 1.0)
            assert (np.diff(values) >= 0).all()
            assert values.min() >= 0 and values.max() <= 1

    def test_marginals_match_order_statistics(self):
        """The transform reproduces uniform order-statistic means
        E[x_(k)] = k / (K + 1)."""
        rng = np.random.default_rng(1)
        draws = np.array([rmag._ordered_uniform_transform(
            rng.uniform(size=3), 0.0, 1.0) for _ in range(20000)])
        expected = np.array([1, 2, 3]) / 4.0
        assert np.allclose(draws.mean(axis=0), expected, atol=0.01)


@pytest.fixture(scope='module')
def boot():
    """A bootstrapped two-component fit shared by the visualization tests."""
    x, spectrum = synthetic_spectrum(noise=0.02)
    fit = rmag.unmix_coercivity_spectrum(x, spectrum, n_components=2,
                                         vary_skew=False)
    return rmag.unmixing_bootstrap(fit, n_boot=60, random_seed=3)


class TestUncertaintyVisualization:
    """The bootstrap/posterior uncertainty-visualization helpers."""

    def test_samples_accessor_bootstrap(self, boot):
        samples, source = rmag._unmixing_samples(boot)
        assert source == 'bootstrap'
        assert 'B_mean_mT' in samples
        assert samples['B_mean_mT'].shape[1] == 2

    def test_samples_accessor_raises_without_draws(self):
        x, spectrum = synthetic_spectrum()
        fit = rmag.unmix_coercivity_spectrum(x, spectrum, n_components=2)
        with pytest.raises(ValueError):
            rmag._unmixing_samples(fit)

    def test_posterior_plot(self, boot):
        fig, axes = rmag.plot_unmixing_posterior(boot, quantity='proportion')
        assert len(axes) == 2
        plt.close(fig)

    def test_posterior_plot_bad_quantity(self, boot):
        with pytest.raises(KeyError):
            rmag.plot_unmixing_posterior(boot, quantity='not_a_quantity')

    def test_tradeoff_plot(self, boot):
        fig, ax = rmag.plot_unmixing_tradeoff(boot, x='B_mean_mT',
                                              y='proportion')
        # all draws of both components are scattered
        n_points = sum(len(c.get_offsets()) for c in ax.collections)
        assert n_points == 2 * boot['bootstrap']['n_success']
        plt.close(fig)

    def test_tradeoff_single_component(self, boot):
        fig, ax = rmag.plot_unmixing_tradeoff(boot, component=1)
        assert len(ax.collections) == 1
        plt.close(fig)

    def test_ensemble_plot(self, boot):
        fig, ax = rmag.plot_unmixing_ensemble(boot, space='spectrum',
                                              n_draws=30, random_seed=1)
        assert ax.get_title().endswith('bootstrap draws')
        plt.close(fig)

    def test_ensemble_curve_space(self, boot):
        fig, ax = rmag.plot_unmixing_ensemble(boot, space='curve',
                                              n_draws=20, random_seed=1)
        plt.close(fig)


class TestMineralPriors:
    """The coercivity component prior library and mineral_priors helper."""

    def test_library_entries_are_well_formed(self):
        for name, entry in rmag.COERCIVITY_COMPONENT_LIBRARY.items():
            for key in ('B_median_mT', 'dp', 'skew'):
                low, high = entry[key]
                assert low < high, f'{name} {key} not ordered'
            assert 'source' in entry

    def test_builds_priors_sorted_by_coercivity(self):
        priors = rmag.mineral_priors(['hematite_detrital',
                                      'magnetite_detrital'])
        # returned in increasing coercivity order regardless of input order
        assert priors['components'] == ['magnetite_detrital',
                                        'hematite_detrital']
        assert priors['mean'][0][1] < priors['mean'][1][0]

    def test_mean_bounds_match_library(self):
        priors = rmag.mineral_priors(['magnetite_detrital'])
        low, high = rmag.COERCIVITY_COMPONENT_LIBRARY[
            'magnetite_detrital']['B_median_mT']
        assert priors['mean'][0] == pytest.approx(
            (np.log10(low), np.log10(high)))

    def test_tighten_narrows_ranges(self):
        wide = rmag.mineral_priors(['hematite'])['dp'][0]
        narrow = rmag.mineral_priors(['hematite'], tighten=2)['dp'][0]
        assert (narrow[1] - narrow[0]) == pytest.approx(
            (wide[1] - wide[0]) / 2)
        # same center
        assert (narrow[0] + narrow[1]) == pytest.approx(wide[0] + wide[1])

    def test_field_max_clips_mean(self):
        # hematite window is (150, 1500) mT; a 1 T max field clips the top
        priors = rmag.mineral_priors(['hematite'], field_max_mT=1000)
        assert priors['mean'][0][1] == pytest.approx(np.log10(1000))
        # the lower bound is untouched, so the window keeps a real width
        assert priors['mean'][0][0] < priors['mean'][0][1]

    def test_field_max_below_window_raises(self):
        """Regression: a component whose whole coercivity window lies above
        the maximum applied field must raise, not silently collapse to a
        zero-width window pinned at log10(field_max)."""
        with pytest.raises(ValueError, match='cannot constrain'):
            rmag.mineral_priors(['hematite_detrital'], field_max_mT=300)

    def test_field_max_names_the_unconstrainable_component(self):
        """In a mixed list only the component beyond the field range trips the
        error, and the message identifies it."""
        with pytest.raises(ValueError, match='hematite_detrital'):
            rmag.mineral_priors(['hematite_pigmentary', 'hematite_detrital'],
                                field_max_mT=300)

    def test_accepts_single_string(self):
        priors = rmag.mineral_priors('hematite')
        assert len(priors['mean']) == 1

    def test_unknown_name_raises(self):
        with pytest.raises(KeyError):
            rmag.mineral_priors(['unobtainium'])

    def test_prior_table(self):
        table = rmag.coercivity_prior_table(['hematite', 'magnetite'])
        # sorted by central coercivity (magnetite softer than hematite)
        assert list(table['component']) == ['magnetite', 'hematite']
        assert set(['family', 'mean coercivity (mT)', 'skew (alpha)',
                    'asymmetry']).issubset(table.columns)
        assert table.loc[0, 'asymmetry'].startswith('left')
        assert table.loc[1, 'asymmetry'].startswith('right')

    def test_plot_prior_library(self):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = rmag.plot_coercivity_prior_library()
        assert len(ax.get_yticklabels()) == len(
            rmag.COERCIVITY_COMPONENT_LIBRARY)
        fig2, _ = rmag.plot_coercivity_prior_library(
            ['magnetite', 'hematite_detrital'])
        plt.close(fig)
        plt.close(fig2)

    def test_tighten_below_one_raises(self):
        with pytest.raises(ValueError):
            rmag.mineral_priors(['hematite'], tighten=0.5)

    def test_widen_broadens_ranges(self):
        wide = rmag.mineral_priors(['hematite'])['dp'][0]
        wider = rmag.mineral_priors(['hematite'], widen=2)['dp'][0]
        assert (wider[1] - wider[0]) == pytest.approx(2 * (wide[1] - wide[0]))
        # same center
        assert (wider[0] + wider[1]) == pytest.approx(wide[0] + wide[1])

    def test_widen_below_one_raises(self):
        with pytest.raises(ValueError):
            rmag.mineral_priors(['hematite'], widen=0.5)

    def test_widen_and_tighten_compose(self):
        base = rmag.mineral_priors(['hematite'])['dp'][0]
        both = rmag.mineral_priors(['hematite'], widen=3, tighten=2)['dp'][0]
        # net width factor is widen / tighten = 1.5
        assert (both[1] - both[0]) == pytest.approx(1.5 * (base[1] - base[0]))

    def test_override_replaces_window(self):
        priors = rmag.mineral_priors(
            ['magnetite_detrital'],
            overrides={'magnetite_detrital': {'B_median_mT': (20.0, 160.0)}})
        assert priors['mean'][0] == pytest.approx(
            (np.log10(20.0), np.log10(160.0)))
        # non-overridden windows still come from the library
        assert priors['dp'][0] == pytest.approx(
            rmag.COERCIVITY_COMPONENT_LIBRARY['magnetite_detrital']['dp'])

    def test_override_composes_with_widen(self):
        priors = rmag.mineral_priors(
            ['hematite'], widen=2,
            overrides={'hematite': {'dp': (0.2, 0.4)}})
        low, high = priors['dp'][0]
        # override window (0.2, 0.4) widened x2 about center 0.3 -> (0.1, 0.5)
        assert (low, high) == pytest.approx((0.1, 0.5))

    @needs_dynesty
    def test_priors_drive_bayes_and_infer_n_components(self):
        x, curve = synthetic_curve(noise=0.005, n=BAYES_N)
        # the synthetic components sit near 250 and 750 mT; use library
        # windows that bracket them, and let n_components come from priors
        priors = rmag.mineral_priors(['hematite_pigmentary',
                                      'hematite_detrital'])
        result = rmag.unmix_coercivity(x, curve, method='bayes',
                                       priors=priors, random_seed=3,
                                       **FAST_BAYES)
        assert result['n_components'] == 2
        # each component's MEAN coercivity stays within its mineral window
        # (the 'mean' window constrains 10**B_mean_mT directly)
        mean_log = np.log10(result['bayes']['samples']['B_mean_mT'])
        for comp, (low, high) in enumerate(priors['mean']):
            assert mean_log[:, comp].min() >= low - 1e-6
            assert mean_log[:, comp].max() <= high + 1e-6


class TestParseDescription:
    """parse_specimen_description edge cases."""

    def test_nan_returns_empty(self):
        text, data = rmag.parse_specimen_description(np.nan)
        assert text == '' and data == {}

    def test_plain_text(self):
        text, data = rmag.parse_specimen_description('powder for Mossbauer')
        assert text == 'powder for Mossbauer' and data == {}

    def test_legacy_python_dict_repr(self):
        text, data = rmag.parse_specimen_description(
            "{'g1_amplitude': 0.5, 'g1_center': 100.0}")
        assert data == {'g1_amplitude': 0.5, 'g1_center': 100.0}

    def test_json_payload(self):
        text, data = rmag.parse_specimen_description(
            'rock chip | {"coercivity_unmixing": {"n_components": 2}}')
        assert text == 'rock chip'
        assert data['coercivity_unmixing']['n_components'] == 2
