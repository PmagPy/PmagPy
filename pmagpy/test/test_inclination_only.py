"""Tests for the inclination-only mean routine doincfish and its two methods.

Anchored on the numerical example of Arason and Levi (2010,
doi:10.1111/j.1365-246X.2010.04671.x, Table 2): the nine Icelandic lava-flow
inclinations of Fisher (1953), for which the table lists results from every
inclination-only method. Additional tests cover cross-method agreement,
recovery of known parameters from synthetic Fisher-distributed data, and the
steep-data regime where the McFadden and Reid fitness function has no zero.
"""
import numpy as np
import pytest

from pmagpy import pmag

# nine specimens from an Icelandic lava flow (Fisher, 1953), the numerical
# example of Arason and Levi (2010, Table 1)
ICELAND = [66.10, 68.70, 70.10, 82.10, 79.50, 73.00, 69.30, 58.80, 51.40]

# steep, scattered plunges for which the McFadden and Reid fitness function
# has no zero (oblate-specimen V3 axes from a Duluth Complex drill core)
STEEP = [5.9, 9.7, 44.8, 47.5, 48.5, 53.8, 57.9, 63.3, 64.5, 65.7, 66.6,
         67.5, 68.4, 69.5, 72.6, 75.0, 77.9, 79.8]


def test_mcfadden_reid_matches_published_modified_estimate():
    """The default method reproduces the 'McFadden & Reid modified' row of
    Arason and Levi (2010, Table 2): Im = 70.95, kappa = 34.62."""
    out = pmag.doincfish(ICELAND)
    assert out['inc'] == pytest.approx(70.95, abs=0.01)
    assert out['k'] == pytest.approx(34.62, abs=0.05)


def test_mcfadden_reid_moderate_reference():
    """Regression values for the normal (root-found) McFadden & Reid path."""
    out = pmag.doincfish([70, 75, 80, 65, 72])
    assert out['inc'] == pytest.approx(73.14, abs=0.01)
    assert out['alpha95'] == pytest.approx(6.72, abs=0.01)


def test_mcfadden_reid_steep_fallback_returns_a_result():
    """The no-zero fallback previously raised IndexError: np.argmin hands it
    a scalar index where np.argwhere gives an (n, 1) array."""
    out = pmag.doincfish(STEEP)
    assert np.isfinite(out['inc'])
    assert 0 <= out['inc'] <= 90


def test_arason_levi_matches_published_example():
    """The arason_levi method reproduces the Arason and Levi (2010, Table 2)
    result exactly: Im = 71.85, kappa = 32.45, alpha95 = 9.17."""
    out = pmag.doincfish(ICELAND, method='arason_levi')
    assert out['inc'] == pytest.approx(71.85, abs=0.02)
    assert out['k'] == pytest.approx(32.45, rel=0.01)
    assert out['alpha95'] == pytest.approx(9.17, abs=0.02)


def test_methods_agree_in_moderate_regime():
    """Where the McFadden & Reid root exists, the two methods coincide."""
    moderate = [70, 75, 80, 65, 72]
    mr = pmag.doincfish(moderate)
    al = pmag.doincfish(moderate, method='arason_levi')
    assert al['inc'] == pytest.approx(mr['inc'], abs=0.5)


def test_arason_levi_recovers_known_fisher_parameters():
    """Inclinations drawn from a Fisher distribution with known mean and
    precision are recovered within sampling uncertainty."""
    rng = np.random.default_rng(42)
    incs = []
    for _ in range(100):
        dec, inc = pmag.fshdev(30., random_seed=rng)
        _, i = pmag.dodirot(dec, inc, 0., 80.)
        incs.append(i)
    out = pmag.doincfish(incs, method='arason_levi')
    assert out['inc'] == pytest.approx(80, abs=4)
    assert out['k'] == pytest.approx(30, rel=0.35)
    assert (out['profile_lower_confidence_limit'] <= out['inc']
            <= out['profile_upper_confidence_limit'])


def test_arason_levi_handles_steep_data_where_mcfadden_reid_fails():
    """The likelihood maximum exists for steep scattered data, and the MLE
    corrects the shallowing bias of the arithmetic mean."""
    out = pmag.doincfish(STEEP, method='arason_levi')
    assert (out['profile_lower_confidence_limit'] <= out['inc']
            <= out['profile_upper_confidence_limit'])
    assert out['inc'] >= out['ginc']


def test_mcfadden_reid_works_for_shallow_data():
    """Shallow mean inclinations previously short-circuited to the gaussian
    mean with zero-filled statistics and no alpha95 key; the McFadden and
    Reid root search is valid there (Arason and Levi, 2010, note the
    modified method is reasonable below 60 degrees) and now runs for all
    data."""
    shallow = [20., 15., 25., 18., 22., 12., 28.]
    out = pmag.doincfish(shallow)
    al = pmag.doincfish(shallow, method='arason_levi')
    assert out['inc'] == pytest.approx(al['inc'], abs=0.5)
    assert out['k'] > 0
    assert np.isfinite(out['alpha95']) and out['alpha95'] > 0


def test_mcfadden_reid_selects_true_root_of_two():
    """For shallow data the fitness function has a second, spurious steep
    root; the curvature test of McFadden and Reid (1982, eq. 19a) must
    select the true likelihood maximum. This scattered shallow set has
    roots at 62.0 and 12.2 degrees, and the pre-fix sec-squared criterion
    (in place of the paper's cosec-squared) selected the spurious steep
    root."""
    incs = [41.3, 0.1, 6.0, -0.1]
    out = pmag.doincfish(incs)
    al = pmag.doincfish(incs, method='arason_levi')
    assert out['inc'] == pytest.approx(al['inc'], abs=0.5)
    assert out['inc'] < 30  # not the spurious root near 62 degrees


def test_arason_levi_warns_for_edge_solution(capsys):
    """Steep dispersed data drive the likelihood maximum to the vertical,
    where a unique solution does not exist (Arason and Levi, 2010,
    Section 7); the function warns and the profile likelihood limits
    bound the plausible inclination range."""
    out = pmag.doincfish([50., 90., 88., 60., 89., 70., 85.],
                         method='arason_levi')
    assert out['inc'] == pytest.approx(90., abs=0.01)
    assert 'unique solution' in capsys.readouterr().out
    assert out['profile_upper_confidence_limit'] == pytest.approx(90., abs=0.01)
    assert out['profile_lower_confidence_limit'] < out['inc']


def test_unknown_method_raises():
    with pytest.raises(ValueError):
        pmag.doincfish([50, 60, 70], method='kono')
