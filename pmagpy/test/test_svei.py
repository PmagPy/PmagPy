"""Regression tests for SVEI sampling and find_flat output."""

import matplotlib.pyplot as plt
import numpy as np
from numpy.testing import assert_allclose

from pmagpy import pmag, svei


def _legacy_mc_distributions(model, lat, n, degree, num_sims):
    """Small reference implementation of the former scalar MC loop."""
    v2_decs, elongations = [], []
    for _ in range(num_sims):
        directions = svei.GGPrand(model, lat, n, degree)
        pars = pmag.doprinc(directions)
        v2_dec = pars['V2dec']
        if v2_dec < 90 or v2_dec > 270:
            v2_dec = (v2_dec - 180) % 360
        v2_decs.append(v2_dec)
        elongations.append(pars['tau2'] / pars['tau3'])
    return np.array(v2_decs), np.array(elongations)


def _legacy_cdfs(model, lat, degree, kappa, n):
    """Small reference implementation of the former repeated CDF scans."""
    mean = svei.m_TAF(model, lat)
    covariance = svei.Cov_modelo(model, lat, degree)
    xyz = np.random.multivariate_normal(mean, covariance, n) * 1000
    xyz /= np.linalg.norm(xyz, axis=1, keepdims=True)
    if kappa > 0:
        xyz += np.random.multivariate_normal(
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
        np.random.seed(42)
        expected_inc, expected_dec = _legacy_cdfs(
            model, lat=35, degree=8, kappa=50, n=10_000
        )
        np.random.seed(42)
        inc_cdf, dec_cdf = svei.GGP_vMF_cdfs(
            model, lat=35, degree=8, kappa=50, n=10_000
        )
        inclination_grid = np.deg2rad(np.linspace(-90, 90, 181))
        declination_grid = np.deg2rad(np.linspace(-180, 180, 361))
        assert_allclose(inc_cdf(inclination_grid), expected_inc)
        assert_allclose(dec_cdf(declination_grid), expected_dec)

    def test_batched_mc_matches_legacy_without_kappa(self):
        model = svei.GGPmodels('THG24')
        np.random.seed(123)
        expected_v2, expected_e = _legacy_mc_distributions(
            model, lat=35, n=20, degree=8, num_sims=25
        )
        np.random.seed(123)
        actual_v2, actual_e = svei._GGP_mc_distributions(
            model, lat=35, n=20, degree=8, num_sims=25,
            kappa=-1, batch_size=7,
        )
        assert_allclose(actual_v2, expected_v2, atol=1e-10)
        assert_allclose(actual_e, expected_e, atol=1e-10)

    def test_batched_fisher_mc_returns_valid_distributions(self):
        model = svei.GGPmodels('THG24')
        v2_decs, elongations = svei._GGP_mc_distributions(
            model, lat=35, n=20, degree=8, num_sims=25,
            kappa=50, batch_size=10,
        )
        assert v2_decs.shape == (25,)
        assert elongations.shape == (25,)
        assert np.all((v2_decs >= 90) & (v2_decs <= 270))
        assert np.all(elongations >= 1)


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
        sim_batch_size=4,
    )

    assert summary_path.exists()
    assert (tmp_path / 'speed_svei_test.pdf').exists()
    assert len(calls) == len(np.arange(1, .3, -.05))
    assert calls[0]['plot'] is True
    assert calls[0]['show'] is False
    assert all(call['cdf_samples'] == 5000 for call in calls)
    assert all(call['sim_batch_size'] == 4 for call in calls)
    assert_allclose(result['V2max'], 210.0)
    plt.close('all')
