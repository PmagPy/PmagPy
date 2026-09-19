"""
Tests for the inclination-shallowing Kent tools in ipmag.py.

Covers ipmag.find_compilation_kent (Fisher resampling of a mean pole over a
compilation of flattening factors), the PIERCE2022_F_COMPILATION default,
ipmag.plot_pole_ellipse, and the hemisphere handling of
pmagplotlib.plot_ell that it relies on.

Regression tests for PmagPy/PmagPy#903: the resampling loop iterated over
the length of the f compilation rather than over n, and the Kent ellipse
of a southern-hemisphere mean pole was drawn at its antipode.
"""
import matplotlib.pyplot as plt
import numpy as np
import pytest

from pmagpy import ipmag, pmagplotlib

# A mean pole in the southern hemisphere observed from a southern site, so
# that the corrected poles and their Kent ellipse have negative latitudes.
SOUTHERN_POLE = dict(plon=300.0, plat=-60.0, A95=5.0, slon=250.0, slat=-30.0)

# Kent parameters of a southern-hemisphere mean (dec, inc = pole lon, lat)
# with major and minor axes lying in the plane perpendicular to the mean.
SOUTHERN_KENT = {
    'dec': 280.0, 'inc': -54.0,
    'Zeta': 14.0, 'Zdec': 220.0, 'Zinc': 20.0,
    'Eta': 5.0, 'Edec': 320.0, 'Einc': 28.0,
}


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close('all')


def _ellipse_points(kent, lower):
    pars = [kent['dec'], kent['inc'], kent['Zeta'], kent['Zdec'],
            kent['Zinc'], kent['Eta'], kent['Edec'], kent['Einc']]
    return np.array(pmagplotlib.plot_ell(1, pars, lower=lower, plot=False))


# ---------------------------------------------------------------------------
# find_compilation_kent: resample count
# ---------------------------------------------------------------------------

class TestFindCompilationKentResampling:

    def test_default_compilation_is_pierce2022(self):
        # Pierce et al. (2022) Table S1 compiles 70 measured f factors
        assert len(ipmag.PIERCE2022_F_COMPILATION) == 70
        assert all(0 < f <= 1 for f in ipmag.PIERCE2022_F_COMPILATION)

    def test_n_below_compilation_length_runs(self):
        # the loop used to index n resampled inclinations with the
        # compilation length (70), which raised IndexError for n < 70
        pytest.importorskip("cartopy")
        lons, lats, kent = ipmag.find_compilation_kent(
            **SOUTHERN_POLE, n=50, n_fish=10, return_poles=True,
            random_seed=1)
        # one Fisher resample of n_fish poles per resampled f factor
        assert len(lons) == len(lats) == 50 * 10
        assert kent['n'] == 500

    def test_n_controls_number_of_resampled_poles(self):
        # n above 70 used to be silently truncated to the compilation length
        pytest.importorskip("cartopy")
        lons, lats, paleolats = ipmag.find_compilation_kent(
            **SOUTHERN_POLE, n=80, n_fish=3, return_poles=True,
            return_kent_stats=False, return_paleolats=True, random_seed=1)
        assert len(lons) == 80 * 3
        assert len(paleolats) == 80

    def test_custom_compilation_is_used(self):
        # a single-valued compilation gives a single corrected inclination,
        # so every resampled paleolatitude is identical
        pytest.importorskip("cartopy")
        paleolats = ipmag.find_compilation_kent(
            **SOUTHERN_POLE, f_from_compilation=[0.6], n=20, n_fish=2,
            return_kent_stats=False, return_paleolats=True, random_seed=1)
        assert len(paleolats) == 20
        assert np.ptp(paleolats) == 0

    def test_kent_mean_stays_in_pole_hemisphere(self):
        # the resampled poles scatter about the unflattened pole, which for
        # a southern pole and site remains in the southern hemisphere
        pytest.importorskip("cartopy")
        kent = ipmag.find_compilation_kent(
            **SOUTHERN_POLE, n=30, n_fish=10, random_seed=1)
        assert kent['inc'] < 0


# ---------------------------------------------------------------------------
# plot_ell / plot_pole_ellipse: ellipse hemisphere
# ---------------------------------------------------------------------------

class TestKentEllipseHemisphere:

    def test_plot_ell_lower_true_reflects_southern_mean(self):
        # lower=True is the equal-area stereonet convention: a mean with
        # negative inclination is reflected to the antipode
        pts = _ellipse_points(SOUTHERN_KENT, lower=True)
        assert np.all(pts[:, 1] > 0)

    def test_plot_ell_lower_false_keeps_southern_mean(self):
        # on a map the ellipse must surround the mean pole itself
        pts = _ellipse_points(SOUTHERN_KENT, lower=False)
        assert np.all(pts[:, 1] < 0)
        # the ellipse is centered on the mean, so its latitude range brackets
        # the mean latitude by roughly the semi-axis angles
        assert pts[:, 1].min() < SOUTHERN_KENT['inc'] < pts[:, 1].max()

    def test_plot_ell_hemisphere_choices_are_antipodal(self):
        # the two hemisphere choices trace the same ellipse reflected
        # through the origin (the points are traversed in a different
        # order, so compare the point sets rather than index by index)
        upper = _ellipse_points(SOUTHERN_KENT, lower=True)
        lower = _ellipse_points(SOUTHERN_KENT, lower=False)
        antipodes = np.column_stack(((lower[:, 0] + 180.0) % 360.0,
                                     -lower[:, 1]))
        for lon, lat in antipodes:
            dlon = (upper[:, 0] - lon + 180.0) % 360.0 - 180.0
            assert np.min(np.hypot(dlon, upper[:, 1] - lat)) < 1e-6

    def test_plot_pole_ellipse_draws_ellipse_at_mean(self):
        # the default draws the ellipse in the hemisphere of the mean pole,
        # where the mean symbol has always been plotted
        pytest.importorskip("cartopy")
        map_axis = ipmag.make_orthographic_map(SOUTHERN_KENT['dec'],
                                               SOUTHERN_KENT['inc'])
        n_lines = len(map_axis.get_lines())
        ipmag.plot_pole_ellipse(map_axis, SOUTHERN_KENT)
        ellipse = map_axis.get_lines()[n_lines:]
        assert len(ellipse) == 1
        lats = np.asarray(ellipse[0].get_ydata(), dtype=float)
        assert np.all(lats < 0)
        # the mean symbol is at the pole itself
        symbol = map_axis.collections[-1].get_offsets()
        assert symbol[0][1] == pytest.approx(SOUTHERN_KENT['inc'])
