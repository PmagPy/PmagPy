"""Regression tests for SVEI sampling and find_flat output."""

import matplotlib.pyplot as plt
import numpy as np
from numpy.testing import assert_allclose
from scipy import stats

from pmagpy import ipmag, pmag, svei


def _legacy_mc_distributions(model, lat, n, degree, num_sims, kappa=-1,
                             random_seed=None):
    """Small reference implementation of the former scalar MC loop."""
    rng = pmag._resolve_rng(random_seed)
    v2_decs, elongations = [], []
    for _ in range(num_sims):
        directions = svei.GGPrand(model, lat, n, degree, random_seed=rng)
        if kappa > 0:
            decs, incs = directions.T[0], directions.T[1]
            fisher_directions = []
            for k in range(n):
                di_block = ipmag.fishrot(
                    k=kappa, n=4, dec=decs[k], inc=incs[k], di_block=True,
                    random_seed=rng,
                )
                pars = pmag.fisher_mean(di_block)
                fisher_directions.append([pars['dec'], pars['inc']])
            directions = fisher_directions
        pars = pmag.doprinc(directions)
        v2_dec = pars['V2dec']
        if v2_dec < 90 or v2_dec > 270:
            v2_dec = (v2_dec - 180) % 360
        v2_decs.append(v2_dec)
        elongations.append(pars['tau2'] / pars['tau3'])
    return np.array(v2_decs), np.array(elongations)


def _legacy_cdfs(model, lat, degree, kappa, n, random_seed=None):
    """Small reference implementation of the former repeated CDF scans."""
    rng = pmag._resolve_rng(random_seed)
    mean = svei.m_TAF(model, lat)
    covariance = svei.Cov_modelo(model, lat, degree)
    xyz = rng.multivariate_normal(mean, covariance, n) * 1000
    xyz /= np.linalg.norm(xyz, axis=1, keepdims=True)
    if kappa > 0:
        xyz += rng.multivariate_normal(
            [0, 0, 0], np.eye(3) / kappa, n
        )
        xyz /= np.linalg.norm(xyz, axis=1, keepdims=True)
    directions = pmag.cart2dir(xyz)
    directions[directions[:, 0] > 180, 0] -= 360
    inclinations = np.linspace(-90, 90, 181)
    declinations = np.linspace(-180, 180, 361)
    inc_cdf = np.array([
        np.sum(directions[:, 1] <= inc) / n for inc in inclinations
    ])
    dec_cdf = np.array([
        np.sum(directions[:, 0] <= dec) / n for dec in declinations
    ])
    return inc_cdf, dec_cdf


class TestOptimizedSampling:

    def test_cdf_grid_matches_repeated_scans(self):
        model = svei.GGPmodels('THG24')
        expected_inc, expected_dec = _legacy_cdfs(
            model, lat=35, degree=8, kappa=50, n=10_000, random_seed=42
        )
        inc_cdf, dec_cdf = svei.GGP_vMF_cdfs(
            model, lat=35, degree=8, kappa=50, n=10_000, random_seed=42
        )
        inclination_grid = np.deg2rad(np.linspace(-90, 90, 181))
        declination_grid = np.deg2rad(np.linspace(-180, 180, 361))
        assert_allclose(inc_cdf(inclination_grid), expected_inc)
        assert_allclose(dec_cdf(declination_grid), expected_dec)

    def test_batched_mc_matches_legacy_without_kappa(self):
        model = svei.GGPmodels('THG24')
        expected_v2, expected_e = _legacy_mc_distributions(
            model, lat=35, n=20, degree=8, num_sims=25, random_seed=123
        )
        actual_v2, actual_e = svei._GGP_mc_distributions(
            model, lat=35, n=20, degree=8, num_sims=25,
            kappa=-1, batch_size=7, random_seed=123,
        )
        assert_allclose(actual_v2, expected_v2, atol=1e-10)
        assert_allclose(actual_e, expected_e, atol=1e-10)

    def test_batching_does_not_change_results(self):
        """Batch size is an implementation detail, not a sampling choice."""
        model = svei.GGPmodels('THG24')
        reference = svei._GGP_mc_distributions(
            model, lat=35, n=20, degree=8, num_sims=30,
            kappa=-1, batch_size=1, random_seed=5,
        )
        for batch_size in (7, 30, None):
            batched = svei._GGP_mc_distributions(
                model, lat=35, n=20, degree=8, num_sims=30,
                kappa=-1, batch_size=batch_size, random_seed=5,
            )
            assert_allclose(batched[0], reference[0], atol=1e-10)
            assert_allclose(batched[1], reference[1], atol=1e-10)

    def test_batched_fisher_mc_returns_valid_distributions(self):
        model = svei.GGPmodels('THG24')
        v2_decs, elongations = svei._GGP_mc_distributions(
            model, lat=35, n=20, degree=8, num_sims=25,
            kappa=50, batch_size=10, random_seed=9,
        )
        assert v2_decs.shape == (25,)
        assert elongations.shape == (25,)
        assert np.all((v2_decs >= 90) & (v2_decs <= 270))
        assert np.all(elongations >= 1)

    def test_batched_fisher_mc_matches_legacy_distribution(self):
        """The vectorized kappa>0 path must sample the same distribution as
        the former fishrot/fisher_mean loop.

        The two implementations consume the random stream in a different
        order, so they are compared distributionally rather than elementwise.
        """
        model = svei.GGPmodels('THG24')
        expected_v2, expected_e = _legacy_mc_distributions(
            model, lat=35, n=20, degree=8, num_sims=250, kappa=50,
            random_seed=2024,
        )
        actual_v2, actual_e = svei._GGP_mc_distributions(
            model, lat=35, n=20, degree=8, num_sims=250,
            kappa=50, random_seed=2024,
        )
        assert stats.ks_2samp(actual_v2, expected_v2).pvalue > 0.01
        assert stats.ks_2samp(actual_e, expected_e).pvalue > 0.01


class TestRandomSeed:
    """Coverage for the random_seed plumbing (issue #825)."""

    def test_ggprand_is_reproducible(self):
        model = svei.GGPmodels('THG24')
        first = svei.GGPrand(model, 35, 50, random_seed=17)
        second = svei.GGPrand(model, 35, 50, random_seed=17)
        assert_allclose(first, second)
        assert not np.allclose(
            first, svei.GGPrand(model, 35, 50, random_seed=18)
        )

    def test_cdfs_are_reproducible(self):
        model = svei.GGPmodels('THG24')
        grid = np.deg2rad(np.linspace(-90, 90, 181))
        first = svei.GGP_vMF_cdfs(
            model, 35, 8, kappa=50, n=5000, random_seed=17)[0](grid)
        second = svei.GGP_vMF_cdfs(
            model, 35, 8, kappa=50, n=5000, random_seed=17)[0](grid)
        assert_allclose(first, second)

    def test_mc_distributions_reproducible_for_both_kappa_paths(self):
        model = svei.GGPmodels('THG24')
        for kappa in (-1, 50):
            first = svei._GGP_mc_distributions(
                model, 35, 20, 8, 25, kappa=kappa, random_seed=11)
            second = svei._GGP_mc_distributions(
                model, 35, 20, 8, 25, kappa=kappa, random_seed=11)
            assert_allclose(first[0], second[0])
            assert_allclose(first[1], second[1])

    def test_generator_and_int_seed_agree(self):
        model = svei.GGPmodels('THG24')
        from_int = svei.GGPrand(model, 35, 25, random_seed=3)
        from_generator = svei.GGPrand(
            model, 35, 25, random_seed=np.random.default_rng(3))
        assert_allclose(from_int, from_generator)

    def test_svei_test_is_reproducible(self):
        model_directions = svei.GGPrand(
            svei.GGPmodels('THG24'), 35, 30, random_seed=1)[:, :2]
        kwargs = dict(model_name='THG24', num_sims=50, cdf_samples=5000,
                      kappa=50, random_seed=77)
        first = svei.svei_test(model_directions, **kwargs)
        second = svei.svei_test(model_directions, **kwargs)
        assert first == second

    def test_unseeded_calls_differ(self):
        """Default behaviour stays non-deterministic, as before."""
        model = svei.GGPmodels('THG24')
        first = svei.GGPrand(model, 35, 50)
        second = svei.GGPrand(model, 35, 50)
        assert not np.allclose(first, second)


def test_find_flat_saves_both_figures_and_reuses_initial_result(
        monkeypatch, tmp_path):
    calls = []

    def fake_svei_test(*args, **kwargs):
        calls.append(kwargs)
        if kwargs['plot']:
            figure = plt.figure()
            if kwargs['saveto']:
                figure.savefig(kwargs['saveto'])
        return {
            'kappa': kwargs['kappa'], 'lat': 35.0,
            'A2D': 4.0, 'A2I': 4.0, 'pID': 0.01, 'H': 1,
            'V2dec': 180.0, 'V2sim_min': 150.0,
            'V2sim_max': 210.0, 'E': 1.5, 'Esim_min': 1.1,
            'Esim_max': 2.0, 'V2_result': 0, 'E_result': 0,
        }

    monkeypatch.setattr(svei, 'svei_test', fake_svei_test)
    monkeypatch.setattr(svei.ipmag, 'plot_net', lambda *a, **k: None)
    monkeypatch.setattr(svei.ipmag, 'plot_di', lambda *a, **k: None)

    directions = np.array([
        [0, 45], [5, 50], [355, 40], [180, -45],
        [185, -50], [175, -40], [10, 42], [190, -42],
    ])
    summary_path = tmp_path / 'speed.pdf'
    result = svei.find_flat(
        directions, save=True, plot=False, quick=True,
        saveto=summary_path, num_sims=10, cdf_samples=5000,
        sim_batch_size=4, random_seed=5,
    )

    assert summary_path.exists()
    assert (tmp_path / 'speed_svei_test.pdf').exists()
    assert len(calls) == len(np.arange(1, .3, -.05))
    assert calls[0]['plot'] is True
    assert calls[0]['show'] is False
    assert all(call['cdf_samples'] == 5000 for call in calls)
    assert all(call['sim_batch_size'] == 4 for call in calls)
    # one Generator is threaded through the whole scan, so a single seed
    # reproduces every unflattening factor
    assert isinstance(calls[0]['random_seed'], np.random.Generator)
    assert all(call['random_seed'] is calls[0]['random_seed']
               for call in calls)
    assert_allclose(result['V2max'], 210.0)
    plt.close('all')
