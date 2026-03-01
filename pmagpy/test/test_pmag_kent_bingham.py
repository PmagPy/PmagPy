"""
Tests for Kent and Bingham statistical functions in pmag.py.

Covers dokent (Kent mean and confidence ellipse) and dobingham
(Bingham mean and confidence ellipse) — directional statistics
that characterize both the mean direction and the shape of the
distribution via elliptical confidence regions.
"""
import numpy as np
from numpy.testing import assert_allclose

from pmagpy import pmag


# ---------------------------------------------------------------------------
# dokent: Kent distribution parameters
# ---------------------------------------------------------------------------

class TestDokent:
    """Tests for pmag.dokent."""

    def test_returns_expected_keys(self):
        """dokent returns all expected dictionary keys."""
        data = [[0, 45], [5, 43], [355, 47], [2, 44], [358, 46]]
        kpars = pmag.dokent(data, len(data))
        expected = {'dec', 'inc', 'n', 'Zeta', 'Zdec', 'Zinc',
                    'Eta', 'Edec', 'Einc', 'R1', 'R2'}
        assert set(kpars.keys()) == expected

    def test_mean_near_fisher_mean(self):
        """Kent mean direction is close to Fisher mean for clustered data."""
        data = [[10, 45], [12, 43], [8, 47], [11, 44], [9, 46]]
        kpars = pmag.dokent(data, len(data))
        fpars = pmag.fisher_mean(data)
        ang = pmag.angle([kpars['dec'], kpars['inc']],
                         [fpars['dec'], fpars['inc']])
        assert ang[0] < 1.0

    def test_zeta_greater_than_eta(self):
        """Major semi-axis (Zeta) >= minor semi-axis (Eta)."""
        data = [[10, 45], [12, 43], [8, 47], [11, 44], [9, 46],
                [10.5, 44.5], [9.5, 45.5]]
        kpars = pmag.dokent(data, len(data))
        assert kpars['Zeta'] >= kpars['Eta']

    def test_tight_cluster_small_ellipse(self):
        """Tightly clustered data gives small Zeta and Eta."""
        data = [[10, 45], [10.1, 44.9], [9.9, 45.1], [10.05, 45.05],
                [9.95, 44.95], [10.02, 45.02], [9.98, 44.98], [10, 45]]
        kpars = pmag.dokent(data, len(data))
        assert kpars['Zeta'] < 5.0
        assert kpars['Eta'] < 5.0

    def test_n_equals_nn(self):
        """Returned n matches the NN normalization parameter."""
        data = [[0, 45], [5, 43], [355, 47]]
        kpars = pmag.dokent(data, len(data))
        assert kpars['n'] == len(data)

    def test_nn_one_for_bootstrap(self):
        """NN=1 (bootstrap mode) produces larger ellipses than NN=N."""
        data = [[10, 45], [12, 43], [8, 47], [11, 44], [9, 46]]
        kpars_n = pmag.dokent(data, len(data))
        kpars_1 = pmag.dokent(data, 1)
        # NN=1 should give a larger confidence region
        assert kpars_1['Zeta'] > kpars_n['Zeta']

    def test_fewer_than_two_returns_empty(self):
        """Single direction returns empty dict."""
        kpars = pmag.dokent([[0, 45]], 1)
        assert kpars == {}

    def test_ellipse_axes_orthogonal_to_mean(self):
        """Ellipse axes (Zeta, Eta directions) are ~90° from the mean."""
        data = [[10, 45], [12, 43], [8, 47], [11, 44], [9, 46],
                [10.5, 44.5], [9.5, 45.5]]
        kpars = pmag.dokent(data, len(data))
        ang_z = pmag.angle([kpars['dec'], kpars['inc']],
                           [kpars['Zdec'], kpars['Zinc']])
        ang_e = pmag.angle([kpars['dec'], kpars['inc']],
                           [kpars['Edec'], kpars['Einc']])
        assert_allclose(ang_z[0], 90.0, atol=5.0)
        assert_allclose(ang_e[0], 90.0, atol=5.0)


# ---------------------------------------------------------------------------
# dobingham: Bingham distribution parameters
# ---------------------------------------------------------------------------

class TestDobingham:
    """Tests for pmag.dobingham."""

    def test_returns_expected_keys(self):
        """dobingham returns all expected dictionary keys."""
        data = [[0, 45], [5, 43], [355, 47], [2, 44]]
        bpars = pmag.dobingham(data)
        expected = {'dec', 'inc', 'n', 'Eta', 'Edec', 'Einc',
                    'Zeta', 'Zdec', 'Zinc'}
        assert set(bpars.keys()) == expected

    def test_mean_near_fisher_for_cluster(self):
        """Bingham mean is close to Fisher mean for clustered data."""
        data = [[10, 45], [12, 43], [8, 47], [11, 44], [9, 46]]
        bpars = pmag.dobingham(data)
        fpars = pmag.fisher_mean(data)
        ang = pmag.angle([bpars['dec'], bpars['inc']],
                         [fpars['dec'], fpars['inc']])
        assert ang[0] < 2.0

    def test_n_matches_input(self):
        """Returned n matches input data length."""
        data = [[0, 45], [5, 43], [355, 47]]
        bpars = pmag.dobingham(data)
        assert bpars['n'] == 3

    def test_fewer_than_two_returns_empty(self):
        """Single direction returns empty dict."""
        bpars = pmag.dobingham([[0, 45]])
        assert bpars == {}

    def test_tight_cluster_small_ellipses(self):
        """Tightly clustered data produces small ellipse semi-axes."""
        data = [[10, 45], [10.1, 44.9], [9.9, 45.1], [10.05, 45.05],
                [9.95, 44.95], [10.02, 45.02], [9.98, 44.98], [10, 45]]
        bpars = pmag.dobingham(data)
        assert bpars['Zeta'] < 10.0
        assert bpars['Eta'] < 10.0

    def test_inclination_positive(self):
        """Mean inclination is in the lower hemisphere (>= 0)."""
        data = [[0, -45], [180, 45], [90, -20], [270, 20]]
        bpars = pmag.dobingham(data)
        assert bpars['inc'] >= 0
