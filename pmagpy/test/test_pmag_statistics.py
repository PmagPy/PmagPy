"""
Tests for statistical and PCA functions in pmag.py.

Covers fisher_mean (49 internal calls), doprinc (17 calls), Tmatrix,
and tauV — the core statistical toolkit underpinning many paleomagnetic
analyses in PmagPy.
"""
import numpy as np
from numpy.testing import assert_allclose

from pmagpy import pmag


# ---------------------------------------------------------------------------
# Tmatrix: orientation matrix from Cartesian data
# ---------------------------------------------------------------------------

class TestTmatrix:
    """Tests for pmag.Tmatrix."""

    def test_docstring_example(self):
        """Verify the example from the docstring."""
        X = [[1., 0.8, 5.], [0.5, 0.2, 2.], [1.4, 0.6, 0.1]]
        result = pmag.Tmatrix(X)
        expected = [[3.21, 1.74, 6.14], [1.74, 1.04, 4.46], [6.14, 4.46, 29.01]]
        assert_allclose(result, expected, atol=1e-10)

    def test_symmetric(self):
        """Orientation matrix must be symmetric: T[i][j] == T[j][i]."""
        X = [[1., 2., 3.], [4., 5., 6.], [7., 8., 9.]]
        T = pmag.Tmatrix(X)
        T = np.array(T)
        assert_allclose(T, T.T, atol=1e-10)

    def test_shape_3x3(self):
        """Output is always a 3x3 matrix."""
        X = [[1., 0., 0.], [0., 1., 0.]]
        T = np.array(pmag.Tmatrix(X))
        assert T.shape == (3, 3)

    def test_single_vector(self):
        """Single unit vector along x produces T with only T[0][0] = 1."""
        T = pmag.Tmatrix([[1., 0., 0.]])
        expected = [[1., 0., 0.], [0., 0., 0.], [0., 0., 0.]]
        assert_allclose(T, expected, atol=1e-10)

    def test_orthogonal_unit_vectors(self):
        """Three orthogonal unit vectors produce the identity matrix."""
        X = [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]
        T = pmag.Tmatrix(X)
        assert_allclose(T, np.eye(3), atol=1e-10)


# ---------------------------------------------------------------------------
# tauV: eigenvalues and eigenvectors from orientation matrix
# ---------------------------------------------------------------------------

class TestTauV:
    """Tests for pmag.tauV."""

    def test_eigenvalue_sum_is_one(self):
        """Normalized eigenvalues must sum to 1."""
        X = pmag.dir2cart([[10, 45, 1], [12, 43, 1], [8, 47, 1], [11, 44, 1]])
        T = pmag.Tmatrix(X)
        t, V = pmag.tauV(T)
        assert_allclose(sum(t), 1.0, atol=1e-10)

    def test_eigenvalues_sorted_descending(self):
        """Eigenvalues are returned in descending order: tau1 >= tau2 >= tau3."""
        X = pmag.dir2cart([[0, 0, 1], [5, 2, 1], [355, -1, 1], [2, 1, 1]])
        T = pmag.Tmatrix(X)
        t, V = pmag.tauV(T)
        assert t[0] >= t[1] >= t[2]

    def test_eigenvectors_orthogonal(self):
        """Eigenvectors of a symmetric matrix must be mutually orthogonal."""
        X = pmag.dir2cart([[0, 0, 1], [90, 0, 1], [45, 45, 1], [315, 45, 1]])
        T = pmag.Tmatrix(X)
        t, V = pmag.tauV(T)
        V = np.array(V, dtype=float)
        # dot products between all pairs should be ~0
        assert_allclose(np.dot(V[0], V[1]), 0.0, atol=1e-10)
        assert_allclose(np.dot(V[0], V[2]), 0.0, atol=1e-10)
        assert_allclose(np.dot(V[1], V[2]), 0.0, atol=1e-10)

    def test_eigenvectors_unit_length(self):
        """Eigenvectors are normalized to unit length."""
        X = pmag.dir2cart([[0, 0, 1], [90, 0, 1], [45, 45, 1], [315, 45, 1]])
        T = pmag.Tmatrix(X)
        _, V = pmag.tauV(T)
        for i in range(3):
            assert_allclose(np.linalg.norm(V[i]), 1.0, atol=1e-10)

    def test_dominant_axis(self):
        """Matrix with one dominant axis puts largest eigenvalue first."""
        # 5 vectors along x, 1 along y — tau1 should dominate
        X = [[1, 0, 0]] * 5 + [[0, 1, 0]]
        T = pmag.Tmatrix(X)
        t, V = pmag.tauV(T)
        assert t[0] > 0.8
        assert t[2] < 0.01


# ---------------------------------------------------------------------------
# fisher_mean: Fisher (1953) mean direction and statistics
# ---------------------------------------------------------------------------

class TestFisherMean:
    """Tests for pmag.fisher_mean."""

    def test_docstring_example(self):
        """Verify the example from the docstring."""
        data = [[150, -45], [151, -46], [145, -38], [146, -41]]
        result = pmag.fisher_mean(data)
        assert_allclose(result['dec'], 147.87247771265734, atol=1e-6)
        assert_allclose(result['inc'], -42.52872729473035, atol=1e-6)
        assert_allclose(result['n'], 4)
        assert_allclose(result['r'], 3.9916088992115832, atol=1e-6)
        assert_allclose(result['k'], 357.52162626162925, atol=1e-4)
        assert_allclose(result['alpha95'], 4.865886096375297, atol=1e-4)
        assert_allclose(result['csd'], 4.283846101842065, atol=1e-4)

    def test_identical_directions_large_k(self):
        """Identical directions give infinite k (perfect clustering)."""
        data = [[0, 0], [0, 0], [0, 0]]
        result = pmag.fisher_mean(data)
        assert result['k'] == 'inf'
        assert_allclose(result['dec'], 0.0, atol=1e-10)
        assert_allclose(result['inc'], 0.0, atol=1e-10)

    def test_n_equals_1(self):
        """Single direction returns only dec and inc, no statistics."""
        result = pmag.fisher_mean([[42.5, -30.0]])
        assert_allclose(result['dec'], 42.5, atol=1e-10)
        assert_allclose(result['inc'], -30.0, atol=1e-10)
        assert 'k' not in result
        assert 'alpha95' not in result

    def test_n_equals_2(self):
        """Two directions yield valid Fisher statistics with one degree of freedom."""
        data = [[0, 45], [10, 50]]
        result = pmag.fisher_mean(data)
        assert result['n'] == 2
        assert_allclose(result['k'], 186.4827619455194, atol=1e-4)
        assert_allclose(result['alpha95'], 18.392014184223896, atol=1e-4)

    def test_tight_cluster_small_alpha95(self):
        """Tightly clustered directions have small alpha95."""
        data = [[10, 45], [10.5, 44.8], [9.8, 45.3], [10.2, 45.1],
                [10.1, 44.9], [9.9, 45.2], [10.3, 44.7], [10.0, 45.0]]
        result = pmag.fisher_mean(data)
        assert result['alpha95'] < 2.0

    def test_csd_k_consistency(self):
        """Circular standard deviation satisfies csd = 81 / sqrt(k)."""
        data = [[10, 45], [12, 43], [8, 47], [11, 44], [9, 46]]
        result = pmag.fisher_mean(data)
        assert_allclose(result['csd'], 81.0 / np.sqrt(result['k']), atol=1e-10)

    def test_scattered_directions_alpha95_is_180(self):
        """Uniformly scattered directions produce alpha95 = 180° (no constraint)."""
        data = [[0, 0], [90, 0], [180, 0], [270, 0]]
        result = pmag.fisher_mean(data)
        assert_allclose(result['alpha95'], 180.0, atol=1e-10)

    def test_r_less_than_n(self):
        """Resultant length r is always <= n."""
        data = [[0, 0], [90, 0], [180, 0], [270, 0]]
        result = pmag.fisher_mean(data)
        assert result['r'] <= result['n']

    def test_ignores_intensity(self):
        """Fisher mean uses unit vectors regardless of supplied intensity."""
        data_no_int = [[10, 45], [12, 43]]
        data_with_int = [[10, 45, 50000], [12, 43, 30000]]
        r1 = pmag.fisher_mean(data_no_int)
        r2 = pmag.fisher_mean(data_with_int)
        assert_allclose(r1['dec'], r2['dec'], atol=1e-10)
        assert_allclose(r1['inc'], r2['inc'], atol=1e-10)


# ---------------------------------------------------------------------------
# doprinc: principal component analysis of directional data
# ---------------------------------------------------------------------------

class TestDoprinc:
    """Tests for pmag.doprinc."""

    def test_returns_correct_keys(self):
        """doprinc returns all expected dictionary keys."""
        data = [[0, 0], [5, 2], [355, -1], [2, 1]]
        result = pmag.doprinc(data)
        expected_keys = {'dec', 'inc', 'V2dec', 'V2inc', 'V3dec', 'V3inc',
                         'tau1', 'tau2', 'tau3', 'N'}
        assert set(result.keys()) == expected_keys

    def test_tight_cluster_tau1_near_one(self):
        """Tightly clustered data has tau1 >> tau2, tau3."""
        data = [[10, 45], [10.5, 44.8], [9.8, 45.3], [10.2, 45.1],
                [10.1, 44.9], [9.9, 45.2]]
        result = pmag.doprinc(data)
        assert result['tau1'] > 0.95
        assert result['tau3'] < 0.02

    def test_eigenvalue_sum_is_one(self):
        """Eigenvalues from doprinc must sum to 1."""
        data = [[0, 0], [90, 0], [45, 45], [315, 45], [180, 0]]
        result = pmag.doprinc(data)
        total = result['tau1'] + result['tau2'] + result['tau3']
        assert_allclose(total, 1.0, atol=1e-10)

    def test_girdle_distribution(self):
        """Girdle (great-circle) distribution has tau1 ≈ tau2 >> tau3."""
        # Directions along a great circle (equatorial plane)
        data = [[0, 0], [45, 0], [90, 0], [135, 0], [180, 0],
                [225, 0], [270, 0], [315, 0]]
        result = pmag.doprinc(data)
        assert result['tau1'] - result['tau2'] < 0.05  # tau1 ≈ tau2
        assert result['tau2'] > 5 * result['tau3']     # tau2 >> tau3

    def test_principal_direction_near_mean(self):
        """Principal direction of a cluster is near the Fisher mean."""
        data = [[10, 45], [12, 43], [8, 47], [11, 44], [9, 46]]
        ppars = pmag.doprinc(data)
        fpars = pmag.fisher_mean(data)
        angular_dist = pmag.angle([ppars['dec'], ppars['inc']],
                                  [fpars['dec'], fpars['inc']])
        assert angular_dist[0] < 2.0

    def test_n_count(self):
        """N in output matches number of input directions."""
        data = [[0, 0], [90, 0], [180, 0]]
        result = pmag.doprinc(data)
        assert result['N'] == 3

    def test_inclinations_positive(self):
        """All returned inclinations are in the lower hemisphere (>= 0)."""
        data = [[0, -45], [180, 45], [90, -20], [270, 20]]
        result = pmag.doprinc(data)
        assert result['inc'] >= 0
        assert result['V2inc'] >= 0
        assert result['V3inc'] >= 0
