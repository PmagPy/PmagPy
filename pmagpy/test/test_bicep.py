"""
Tests for pmagpy.bicep, the Bias Corrected Estimation of Paleointensity.

The known-answer tests are synthetic sites built so that the bias really is
linear in the Arai curvature, which is the assumption the method rests on: the
sampler has to recover the field the site was given. The convergence tests
check that the diagnostics are honest -- that a run which has not converged
says so rather than reporting a confident wrong number.
"""
import math
import os
import tempfile

import numpy as np
import pytest

from pmagpy import bicep
from pmagpy import pint_stats as ps


def curved_site(truth: float = 45.0, blab: float = 40.0, bias_slope: float = 60.0,
                curvatures=(0.0, 0.05, 0.1, 0.2, 0.3), noise: float = 1e-3,
                n_points: int = 12, seed: int = 0):
    """Arai plots whose intensity is ``truth - bias_slope * |k|`` by construction."""
    rng = np.random.default_rng(seed)
    out = []
    for j, k in enumerate(curvatures):
        slope = (truth - bias_slope * k) / blab
        x = np.linspace(0.0, 1.0, n_points)
        y = (1.0 - x) * slope + k * 2.0 * x * (1.0 - x)
        out.append((f"s{j}", x, y + noise * rng.normal(size=n_points), blab))
    return bicep.prepare(out)


class TestScaling:
    def test_a_plot_is_scaled_by_its_largest_ptrm(self):
        x, y, problem = bicep.scale_arai([0.0, 1.0, 2.0, 4.0], [4.0, 3.0, 2.0, 0.0])
        assert problem == ""
        assert x.max() == pytest.approx(1.0)
        assert x.min() == pytest.approx(0.0)
        assert y.min() == pytest.approx(0.0)

    def test_a_specimen_that_kept_most_of_its_nrm_is_refused(self):
        _, _, problem = bicep.scale_arai([0.0, 1.0, 2.0], [1.0, 0.9, 0.8])
        assert "remaining NRM" in problem

    def test_too_few_points_is_refused(self):
        _, _, problem = bicep.scale_arai([0.0, 1.0], [1.0, 0.0])
        assert "three" in problem

    def test_prepare_marks_the_refused_specimens_without_dropping_them(self):
        prepared = bicep.prepare([("good", np.linspace(0, 1, 8), np.linspace(1, 0, 8), 40.0),
                                  ("bad", [0.0, 1.0], [1.0, 0.0], 40.0)])
        assert [p.name for p in prepared] == ["good", "bad"]
        assert prepared[0].included and not prepared[1].included
        assert prepared[1].note


class TestGeometry:
    def test_the_intensity_of_a_straight_plot_is_the_ordinary_slope(self):
        # a straight Arai plot with slope -b: the tangent construction must give
        # the same answer as the line fit
        for slope in (0.5, 1.0, 1.7):
            phi = math.atan2(1.0, slope)
            assert bicep.circle_intensity(phi, 40.0) == pytest.approx(slope * 40.0)

    def test_a_circle_reduces_to_its_tangent_line_as_the_radius_grows(self):
        x = np.linspace(0, 1, 10)
        y = 1 - x
        distances = bicep.circle_distances(x, y, math.pi / 4, math.sqrt(0.5), 0.0)
        assert np.allclose(distances, 0.0, atol=1e-12)

    def test_the_distance_is_continuous_through_zero_curvature(self):
        x = np.linspace(0, 1, 8)
        y = 1 - x
        straight = bicep.circle_distances(x, y, math.pi / 4, math.sqrt(0.5), 0.0)
        nearly = bicep.circle_distances(x, y, math.pi / 4, math.sqrt(0.5), 1e-9)
        assert np.allclose(straight, nearly, atol=1e-7)

    def test_the_centre_lies_where_the_parameters_say(self):
        phi, dist, k = 0.9, 0.4, 0.5
        cx, cy, r = bicep.circle_centre(phi, dist, k)
        assert math.hypot(cx, cy) == pytest.approx(dist + r)
        assert math.atan2(cy, cx) == pytest.approx(phi)

    def test_a_starting_point_is_found_for_a_straight_plot(self):
        spec = bicep.prepare([("s", np.linspace(0, 1, 8), np.linspace(1, 0, 8), 40.0)])[0]
        phi, dist, k = bicep.specimen_start(spec)
        assert 0 < phi < math.pi / 2
        assert dist >= 0
        assert abs(k) < bicep.K_LIMIT


class TestSamplers:
    def test_the_bootstrap_recovers_the_intercept(self):
        result = bicep.run(curved_site(), site="synthetic", method="bootstrap", seed=1)
        assert result.b_site == pytest.approx(45.0, abs=1.5)
        assert result.slope > 0
        assert "approximation" in " ".join(result.warnings)

    def test_the_mcmc_sampler_recovers_the_known_field(self):
        result = bicep.run(curved_site(), site="synthetic", method="mcmc", seed=1)
        assert result.b_site == pytest.approx(45.0, abs=1.5)
        assert result.ci_low < 45.0 < result.ci_high
        assert result.converged, f"R-hat {result.r_hat}, ESS {result.ess}"

    def test_a_site_with_no_curvature_still_returns_the_mean(self):
        flat = curved_site(truth=52.0, curvatures=(0.0, 0.0, 0.0, 0.0), bias_slope=0.0, seed=4)
        result = bicep.run(flat, site="flat", method="mcmc", seed=2)
        assert result.b_site == pytest.approx(52.0, abs=1.5)

    def test_a_different_true_field_is_recovered_too(self):
        site = curved_site(truth=70.0, blab=50.0, bias_slope=80.0, seed=5)
        result = bicep.run(site, site="hot", method="mcmc", seed=3)
        assert result.b_site == pytest.approx(70.0, abs=2.0)

    def test_the_same_seed_gives_the_same_answer(self):
        site = curved_site()
        first = bicep.run(site, method="mcmc", seed=11, draws=400, warmup=400)
        second = bicep.run(site, method="mcmc", seed=11, draws=400, warmup=400)
        assert first.b_site == pytest.approx(second.b_site)
        assert np.allclose(first.samples, second.samples)

    def test_a_different_seed_gives_a_consistent_but_not_identical_answer(self):
        site = curved_site()
        first = bicep.run(site, method="mcmc", seed=11)
        second = bicep.run(site, method="mcmc", seed=12)
        assert first.b_site != second.b_site
        assert abs(first.b_site - second.b_site) < 1.5

    def test_one_specimen_is_refused_with_a_reason(self):
        site = curved_site(curvatures=(0.1,))
        result = bicep.run(site, method="mcmc")
        assert not np.isfinite(result.b_site)
        assert "at least two" in " ".join(result.warnings)

    def test_an_excluded_specimen_is_left_out_and_recorded(self):
        site = curved_site()
        site[0].included = False
        site[0].note = "excluded by the analyst"
        result = bicep.run(site, method="bootstrap", seed=1)
        assert site[0].name not in result.specimens
        assert result.excluded[site[0].name] == "excluded by the analyst"

    def test_sampling_can_be_cancelled(self):
        calls = {"n": 0}

        def cancel():
            calls["n"] += 1
            return calls["n"] > 20
        result = bicep.run(curved_site(), method="mcmc", seed=1, cancel=cancel)
        assert any("cancelled" in w for w in result.warnings)

    def test_progress_is_reported(self):
        seen = []
        bicep.run(curved_site(), method="mcmc", seed=1, draws=200, warmup=200,
                  progress=lambda f, m: seen.append(f))
        assert seen and 0 <= seen[0] <= 1 and seen[-1] <= 1

    def test_an_unknown_method_is_an_error(self):
        with pytest.raises(ValueError, match="unknown BiCEP method"):
            bicep.run(curved_site(), method="wishful")

    def test_auto_falls_back_when_stan_is_missing(self):
        result = bicep.run(curved_site(), method="auto", seed=1, draws=200, warmup=200)
        assert result.method in ("stan", "mcmc")


class TestDiagnostics:
    def test_r_hat_is_one_for_identical_chains(self):
        # with no between-chain variance the classical statistic is
        # sqrt((n-1)/n), which tends to one as the chains lengthen
        rng = np.random.default_rng(0)
        for n in (200, 2000):
            chains = np.tile(rng.normal(size=n), (4, 1))
            assert bicep.gelman_rubin(chains) == pytest.approx(math.sqrt((n - 1) / n), abs=1e-9)
        assert bicep.gelman_rubin(np.tile(rng.normal(size=20000), (4, 1))) == \
            pytest.approx(1.0, abs=1e-4)

    def test_r_hat_is_large_for_chains_that_disagree(self):
        rng = np.random.default_rng(0)
        chains = np.array([rng.normal(offset, 0.1, 200) for offset in (0, 5, 10, 15)])
        assert bicep.gelman_rubin(chains) > 2.0

    def test_the_effective_sample_size_falls_with_autocorrelation(self):
        rng = np.random.default_rng(1)
        independent = rng.normal(size=(4, 500))
        correlated = np.cumsum(rng.normal(size=(4, 500)), axis=1) * 0.1
        assert bicep.effective_sample_size(independent) > \
            bicep.effective_sample_size(correlated)

    def test_a_short_run_is_reported_as_not_converged(self):
        result = bicep.run(curved_site(), method="mcmc", seed=1, draws=20, warmup=5, chains=2)
        assert not result.converged

    def test_the_posterior_predictive_check_is_reported(self):
        result = bicep.run(curved_site(), method="mcmc", seed=1)
        assert result.ppc["n"] == 5
        assert result.ppc["rms_residual"] >= 0
        assert result.ppc["r_squared"] <= 1.0


class TestPersistence:
    def test_a_result_round_trips_through_json(self):
        result = bicep.run(curved_site(), site="synthetic", method="mcmc", seed=1,
                           draws=200, warmup=200)
        with tempfile.TemporaryDirectory() as tmp:
            path = bicep.save(result, os.path.join(tmp, "r.json"))
            back = bicep.load(path)
        assert back.site == result.site
        assert back.b_site == pytest.approx(result.b_site)
        assert len(back.samples) == len(result.samples)
        assert back.specimens == result.specimens

    def test_netcdf_falls_back_to_json_when_xarray_is_missing(self):
        result = bicep.run(curved_site(), site="synthetic", method="bootstrap", seed=1)
        with tempfile.TemporaryDirectory() as tmp:
            path = bicep.save(result, os.path.join(tmp, "r.nc"))
            assert path.endswith((".nc", ".json"))
            back = bicep.load(path)
        assert back.b_site == pytest.approx(result.b_site)


class TestReporting:
    def test_the_methods_block_names_the_sampler_the_seed_and_the_citation(self):
        result = bicep.run(curved_site(), site="synthetic", method="mcmc", seed=99,
                           draws=200, warmup=200)
        text = result.methods_block()
        assert "Cych" in text and bicep.DOI in text
        assert "seed 99" in text
        assert "Metropolis" in text

    def test_the_bootstrap_block_says_it_is_an_approximation(self):
        result = bicep.run(curved_site(), site="synthetic", method="bootstrap", seed=1)
        assert "approximation" in result.methods_block()

    def test_magic_rows_never_overwrite_a_specimen_interpretation(self):
        result = bicep.run(curved_site(), site="LV6", method="bootstrap", seed=1)
        rows = bicep.sites_rows([result], analysts="A Tester")
        assert len(rows) == 1
        row = rows[0]
        assert row["site"] == "LV6"
        assert "specimen" not in row
        assert row["int_abs"] == pytest.approx(result.b_site * 1e-6)
        assert "DE-BS" in row["method_codes"]
        assert bicep.DOI in row["citations"]


class TestStanAvailability:
    def test_the_status_says_what_to_install(self):
        status = bicep.stan_status()
        assert set(status) >= {"available", "reason", "hint"}
        if not status["available"]:
            assert "cmdstan" in status["hint"].lower()

    def test_the_model_is_written_where_cmdstan_can_find_it(self):
        path = bicep.model_path()
        assert path.endswith("bicep.stan")
        with open(path) as fh:
            text = fh.read()
        assert "b_site" in text and "slope" in text
        # the model keeps the sign of the curvature and picks the intersection
        # on the same side as the data, as the python model does
        assert "x_mid" in text and "y_mid" in text

    @pytest.mark.skipif(not bicep.stan_status()["available"], reason="CmdStan is not installed")
    def test_stan_and_the_builtin_sampler_agree(self):
        site = curved_site()
        stan = bicep.run(site, method="stan", seed=1, draws=1000, warmup=1000)
        mine = bicep.run(site, method="mcmc", seed=1)
        assert stan.b_site == pytest.approx(mine.b_site, abs=1.5)
