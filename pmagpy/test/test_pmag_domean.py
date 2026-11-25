"""
Tests for pmag.domean — the core direction-fitting function.

Covers Fisher mean (DE-FM), best-fit line (DE-BFL), anchored line (DE-BFL-A),
origin-line (DE-BFL-O), vector mean (DE-VM) and best-fit plane (DE-BFP)
calculation types.

Data format: [[treatment, dec, inc, intensity, quality], ...]
where quality flag 'g' = good, 'b' = bad.
"""
import numpy as np
from numpy.testing import assert_allclose

from pmagpy import pmag


def _make_datablock(decs, incs, intensities=None, treatments=None):
    """Helper to build a domean-compatible data block."""
    n = len(decs)
    if intensities is None:
        intensities = [1.0] * n
    if treatments is None:
        treatments = list(range(n))
    return [[treatments[i], decs[i], incs[i], intensities[i], 'g']
            for i in range(n)]


def _block(steps):
    """Data block from (dec, inc, intensity) steps."""
    decs, incs, intensities = zip(*steps)
    return _make_datablock(decs, incs, intensities)


def _angle(mpars, dec, inc):
    """Angle (degrees) between a fit and a direction."""
    fit = pmag.dir2cart([mpars['specimen_dec'], mpars['specimen_inc'], 1.])
    direction = pmag.dir2cart([dec, inc, 1.])
    return np.degrees(np.arccos(np.clip(np.dot(fit, direction), -1., 1.)))


def _noisy_steps():
    """Two-component demagnetization data with measurement noise.

    Returns the steps as (dec, inc, intensity) and as an array of x, y, z.
    """
    rng = np.random.default_rng(963)
    chrm = np.array(pmag.dir2cart([20., 40., 1.]))
    overprint = np.array(pmag.dir2cart([355., 70., 1.]))
    temps = np.array([300, 350, 400, 450, 500, 525, 550, 565, 580])
    steps = [3e-5 * np.clip((585 - t) / 235, 0, 1) * chrm +
             1.2e-5 * np.clip((470 - t) / 370, 0, 1) * overprint +
             rng.normal(0, 4e-7, 3) for t in temps]
    return [pmag.cart2dir(x) for x in steps], np.array(steps)


# ---------------------------------------------------------------------------
# DE-FM: Fisher mean
# ---------------------------------------------------------------------------

class TestDomeanFisherMean:
    """Tests for domean with calculation_type='DE-FM'."""

    def test_returns_expected_keys(self):
        """Fisher mean returns expected dictionary keys."""
        data = _make_datablock([0, 5, 355], [45, 43, 47])
        mpars = pmag.domean(data, 0, 2, 'DE-FM')
        assert 'specimen_dec' in mpars
        assert 'specimen_inc' in mpars
        assert 'specimen_n' in mpars
        assert 'specimen_alpha95' in mpars

    def test_mean_of_identical_directions(self):
        """Fisher mean of identical directions is that direction."""
        data = _make_datablock([10, 10, 10, 10], [45, 45, 45, 45])
        mpars = pmag.domean(data, 0, 3, 'DE-FM')
        assert_allclose(mpars['specimen_dec'], 10.0, atol=1e-6)
        assert_allclose(mpars['specimen_inc'], 45.0, atol=1e-6)

    def test_n_matches_range(self):
        """specimen_n equals the number of points in the range."""
        data = _make_datablock([0, 5, 10, 15, 20], [45, 45, 45, 45, 45])
        mpars = pmag.domean(data, 1, 3, 'DE-FM')
        assert mpars['specimen_n'] == 3

    def test_step_min_max(self):
        """Step min and max reflect the treatment values."""
        data = _make_datablock(
            [0, 5, 10], [45, 45, 45],
            treatments=[100, 200, 300]
        )
        mpars = pmag.domean(data, 0, 2, 'DE-FM')
        assert mpars['measurement_step_min'] == 100
        assert mpars['measurement_step_max'] == 300

    def test_calculation_type_recorded(self):
        """Calculation type is recorded in the output."""
        data = _make_datablock([0, 5, 10], [45, 43, 47])
        mpars = pmag.domean(data, 0, 2, 'DE-FM')
        assert mpars['calculation_type'] == 'DE-FM'


# ---------------------------------------------------------------------------
# DE-BFL: best-fit line (PCA)
# ---------------------------------------------------------------------------

class TestDomeanBFL:
    """Tests for domean with calculation_type='DE-BFL'."""

    def test_collinear_points_low_mad(self):
        """Collinear points along a single direction give small MAD."""
        # Points along D=0, I=45 at different intensities
        decs = [0, 0, 0, 0, 0]
        incs = [45, 45, 45, 45, 45]
        ints = [1.0, 0.8, 0.6, 0.4, 0.2]
        data = _make_datablock(decs, incs, ints)
        mpars = pmag.domean(data, 0, 4, 'DE-BFL')
        assert mpars['specimen_mad'] < 1.0
        assert_allclose(mpars['specimen_dec'], 0.0, atol=2.0)
        assert_allclose(mpars['specimen_inc'], 45.0, atol=2.0)

    def test_direction_type_is_line(self):
        """BFL returns direction type 'l' for line."""
        data = _make_datablock([0, 0, 0], [45, 45, 45], [1.0, 0.5, 0.1])
        mpars = pmag.domean(data, 0, 2, 'DE-BFL')
        assert mpars['specimen_direction_type'] == 'l'

    def test_scattered_points_larger_mad(self):
        """Scattered points produce larger MAD than collinear points."""
        # Collinear
        data_good = _make_datablock([0, 0, 0, 0], [45, 45, 45, 45],
                                    [1.0, 0.75, 0.5, 0.25])
        mpars_good = pmag.domean(data_good, 0, 3, 'DE-BFL')
        # Scattered
        data_bad = _make_datablock([0, 30, 340, 15], [45, 60, 30, 50],
                                   [1.0, 0.75, 0.5, 0.25])
        mpars_bad = pmag.domean(data_bad, 0, 3, 'DE-BFL')
        assert mpars_bad['specimen_mad'] > mpars_good['specimen_mad']


class TestDomeanBFLEigenvector:
    """The free line against an independent eigen-decomposition."""

    def test_matches_eigenvector_about_centre_of_mass(self):
        """Direction equals the principal axis about the centre of mass,
        pointing along the vector removed between the first and last steps."""
        directions, X = _noisy_steps()
        mpars = pmag.domean(_block(directions), 0, len(X) - 1, 'DE-BFL')
        Xc = X - X.mean(axis=0)
        tau, V = np.linalg.eigh(Xc.T @ Xc)
        v1 = V[:, -1] * np.sign(V[:, -1] @ (X[0] - X[-1]))
        expected = pmag.cart2dir(v1)
        assert _angle(mpars, expected[0], expected[1]) < 1e-6


# ---------------------------------------------------------------------------
# DE-BFL-A: anchored best-fit line
# ---------------------------------------------------------------------------

class TestDomeanBFLA:
    """Tests for domean with calculation_type='DE-BFL-A'."""

    def test_returns_direction(self):
        """Anchored line returns a valid direction."""
        data = _make_datablock([10, 10, 10], [45, 45, 45], [1.0, 0.5, 0.1])
        mpars = pmag.domean(data, 0, 2, 'DE-BFL-A')
        assert 'specimen_dec' in mpars
        assert 'specimen_inc' in mpars

    def test_direction_type_is_line(self):
        """Anchored line returns direction type 'l'."""
        data = _make_datablock([10, 10, 10], [45, 45, 45], [1.0, 0.5, 0.1])
        mpars = pmag.domean(data, 0, 2, 'DE-BFL-A')
        assert mpars['specimen_direction_type'] == 'l'

    def test_analytic_two_steps(self):
        """The anchored line is the principal axis about the origin (issue #963).

        For steps (1, 0, 0) and (0, 0.5, 0) the orientation tensor about the
        origin is diag(1, 0.25, 0): the anchored axis is x (dec 0), whereas the
        vector mean of the two steps is at dec atan(0.5) = 26.57.
        """
        mpars = pmag.domean(_block([(0., 0., 1.), (90., 0., 0.5)]), 0, 1, 'DE-BFL-A')
        assert _angle(mpars, 0., 0.) < 1e-6
        assert_allclose(mpars['specimen_mad'], np.degrees(np.arctan(0.5)), atol=1e-6)

    def test_collinear_with_origin(self):
        """Steps decaying along one direction give that direction, not its antipode."""
        steps = [(30., 45., m) for m in (5., 4., 2.5, 1., 0.2)]
        mpars = pmag.domean(_block(steps), 0, 4, 'DE-BFL-A')
        assert _angle(mpars, 30., 45.) < 1e-6
        assert mpars['specimen_mad'] < 1e-6

    def test_points_toward_steps(self):
        """An anchored line points toward its steps, whichever of the first and
        last steps is the larger; a free line points along the vector removed."""
        rising = [(30., 45., m) for m in (1.0, 1.1, 1.2)]
        assert _angle(pmag.domean(_block(rising), 0, 2, 'DE-BFL-A'), 30., 45.) < 1e-6
        assert _angle(pmag.domean(_block(rising), 0, 2, 'DE-BFL'), 210., -45.) < 1e-6
        # weak steps near the origin, the last one the largest
        weak = [(30., 45., 0.05), (25., 50., 0.04), (36., 41., 0.06)]
        anchored = pmag.domean(_block(weak), 0, 2, 'DE-BFL-A')
        assert _angle(anchored, 30., 45.) < 5.
        vector_mean = pmag.domean(_block(weak), 0, 2, 'DE-VM')
        assert _angle(anchored, vector_mean['specimen_dec'],
                      vector_mean['specimen_inc']) < 90.

    def test_single_step(self):
        """A single step gives its own direction."""
        mpars = pmag.domean(_block([(30., 45., 5.), (200., -10., 2.)]), 0, 0, 'DE-BFL-A')
        assert _angle(mpars, 30., 45.) < 1e-6

    def test_matches_eigenvector_about_origin(self):
        """Direction and MAD equal an independent eigen-decomposition about the origin."""
        directions, X = _noisy_steps()
        mpars = pmag.domean(_block(directions), 0, len(X) - 1, 'DE-BFL-A')
        tau, V = np.linalg.eigh(X.T @ X)
        v1 = V[:, -1] * np.sign(V[:, -1] @ X.sum(axis=0))  # toward the steps
        expected = pmag.cart2dir(v1)
        assert _angle(mpars, expected[0], expected[1]) < 1e-6
        tau = tau[::-1] / tau.sum()
        mad = np.degrees(np.arctan(np.sqrt(tau[1] + tau[2]) / np.sqrt(tau[0])))
        assert_allclose(mpars['specimen_mad'], mad, atol=1e-6)
        assert 'specimen_dang' not in mpars


# ---------------------------------------------------------------------------
# DE-VM: vector mean
# ---------------------------------------------------------------------------

class TestDomeanVM:
    """Tests for domean with calculation_type='DE-VM'."""

    def test_direction_of_vector_sum(self):
        """The vector mean of (1, 0, 0) and (0, 0.5, 0) is at dec atan(0.5)."""
        mpars = pmag.domean(_block([(0., 0., 1.), (90., 0., 0.5)]), 0, 1, 'DE-VM')
        assert _angle(mpars, np.degrees(np.arctan(0.5)), 0.) < 1e-6
        assert mpars['specimen_direction_type'] == 'l'
        assert mpars['specimen_n'] == 2

    def test_no_mad_or_dang(self):
        """A vector mean has no MAD, and its DANG is the placeholder -1."""
        mpars = pmag.domean(_block([(0., 0., 1.), (90., 0., 0.5)]), 0, 1, 'DE-VM')
        assert 'specimen_mad' not in mpars
        assert mpars['specimen_dang'] == -1


# ---------------------------------------------------------------------------
# DE-BFP: best-fit plane (great circle)
# ---------------------------------------------------------------------------

class TestDomeanBFP:
    """Tests for domean with calculation_type='DE-BFP'."""

    def test_returns_pole_direction(self):
        """Plane fit returns a direction (pole to the plane)."""
        # Points spread in a great circle (horizontal plane, varying dec)
        data = _make_datablock([0, 90, 180, 270], [0, 0, 0, 0])
        mpars = pmag.domean(data, 0, 3, 'DE-BFP')
        assert 'specimen_dec' in mpars
        assert 'specimen_inc' in mpars

    def test_direction_type_is_plane(self):
        """BFP returns direction type 'p' for plane."""
        data = _make_datablock([0, 90, 180, 270], [0, 0, 0, 0])
        mpars = pmag.domean(data, 0, 3, 'DE-BFP')
        assert mpars['specimen_direction_type'] == 'p'

    def test_horizontal_circle_pole_near_vertical(self):
        """Points in a horizontal great circle have a near-vertical pole."""
        data = _make_datablock([0, 60, 120, 180, 240, 300],
                               [0, 0, 0, 0, 0, 0])
        mpars = pmag.domean(data, 0, 5, 'DE-BFP')
        # Pole should be near vertical (inc near ±90)
        assert abs(mpars['specimen_inc']) > 80.0


# ---------------------------------------------------------------------------
# DE-BFL-O: origin-anchored best-fit line
# ---------------------------------------------------------------------------

class TestDomeanTwoSteps:
    """A free line through two steps: the MAD is 0, not NaN."""

    def test_two_step_lines_have_zero_mad(self):
        """Two thermal steps of GTX0102A.rs3 (150 and 200 °C, specimen coordinates) of the La Garrotxa
        archive (Vernet Tarragó, 2026, Zenodo, https://doi.org/10.5281/zenodo.20326424, CC BY 4.0), for
        which rounding made an eigenvalue that should be 0 slightly negative and the free-line MAD NaN."""
        import warnings
        data = _make_datablock([186.1, 167.7], [62.4, 49.8], [0.316, 0.3072], [150, 200])
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            mpars = pmag.domean([list(r) for r in data], 0, 1, 'DE-BFL')
            assert np.isfinite(mpars['specimen_mad'])
            assert mpars['specimen_mad'] < 1e-3
            # an anchored line, or one with the origin as a point, is fit to points that are not
            # collinear (the origin with the two steps): a MAD, but not 0
            for calculation_type in ('DE-BFL-A', 'DE-BFL-O'):
                mpars = pmag.domean([list(r) for r in data], 0, 1, calculation_type)
                assert np.isfinite(mpars['specimen_mad'])
                assert mpars['specimen_mad'] > 1


class TestDomeanBFLO:
    """Tests for domean with calculation_type='DE-BFL-O'.

    DE-BFL-O is a free best-fit line through the selected steps with the
    origin added as a point (Kirschvink, 1980): unlike an anchored line
    (DE-BFL-A) it need not pass through the origin, but the origin pulls it
    toward itself. The centre of mass is the mean of the N steps and the
    origin, N + 1 points (#1047).
    """

    def test_returns_direction(self):
        """Origin line returns a valid direction."""
        data = _make_datablock([10, 10, 10], [45, 45, 45], [1.0, 0.5, 0.1])
        mpars = pmag.domean(data, 0, 2, 'DE-BFL-O')
        assert 'specimen_dec' in mpars
        assert 'specimen_inc' in mpars

    def test_direction_type_is_line(self):
        """Origin line returns direction type 'l'."""
        data = _make_datablock([10, 10, 10], [45, 45, 45], [1.0, 0.5, 0.1])
        mpars = pmag.domean(data, 0, 2, 'DE-BFL-O')
        assert mpars['specimen_direction_type'] == 'l'

    def test_collinear_through_origin_low_mad(self):
        """Points along a single direction decaying to origin give small MAD."""
        decs = [0, 0, 0, 0, 0]
        incs = [45, 45, 45, 45, 45]
        ints = [1.0, 0.8, 0.6, 0.4, 0.2]
        data = _make_datablock(decs, incs, ints)
        mpars = pmag.domean(data, 0, 4, 'DE-BFL-O')
        assert mpars['specimen_mad'] < 1.0
        assert_allclose(mpars['specimen_dec'], 0.0, atol=2.0)
        assert_allclose(mpars['specimen_inc'], 45.0, atol=2.0)

    @staticmethod
    def _origin_line(decs, incs, ints):
        """Independent calculation: principal axis and MAD of the steps and the origin, centred on
        their mean (N + 1 points)."""
        X = np.array([pmag.dir2cart([d, i, m]) for d, i, m in zip(decs, incs, ints)] + [[0., 0., 0.]])
        Y = X - X.mean(axis=0)
        values, vectors = np.linalg.eigh(Y.T @ Y)
        dec, inc, _ = pmag.cart2dir(vectors[:, -1])
        mad = np.degrees(np.arctan(np.sqrt((values[0] + values[1]) / values[2])))
        return dec, inc, mad

    @staticmethod
    def _axis_angle(dec1, inc1, dec2, inc2):
        """Angle between two lines, whatever their sense."""
        a = pmag.angle([dec1, inc1], [dec2, inc2])[0]
        return min(a, 180. - a)

    def test_origin_is_one_of_the_points(self):
        """Direction and MAD are those of a principal component fit to the steps and the origin."""
        decs = [212., 220., 229., 236., 242.]
        incs = [-30., -33., -34., -37., -34.]
        ints = [0.039, 0.036, 0.032, 0.030, 0.028]
        data = _make_datablock(decs, incs, ints)
        mpars = pmag.domean(data, 0, 4, 'DE-BFL-O')
        dec, inc, mad = self._origin_line(decs, incs, ints)
        assert self._axis_angle(mpars['specimen_dec'], mpars['specimen_inc'], dec, inc) < 1e-6
        assert_allclose(mpars['specimen_mad'], mad, rtol=1e-9)

    def test_line_stored_by_remasoft(self):
        """A line "including the origin" stored by Remasoft (AGICO) is reproduced.

        amf1601.rs3, fit Cpca3 (flag O, 450-525 °C, three steps), from Michalski, K., Manby, G. M.,
        Nejbert, K., Domańska-Siuda, J., & Burzyński, M. (2022), figshare,
        https://doi.org/10.6084/m9.figshare.21641594.v1 (CC BY 4.0). The steps are in specimen
        coordinates, as in the file. Remasoft stored 247.8 / -28.8, MAD 18.6; with the centre of
        mass of the steps alone (before #1047) the line was 2.5 degrees away and the MAD 1.2 too low.
        """
        decs, incs, ints = [244.5, 242.9, 215.2], [-28.4, -23.7, -6.4], [0.02365, 0.01989, 0.01287]
        mpars = pmag.domean(_make_datablock(decs, incs, ints), 0, 2, 'DE-BFL-O')
        assert self._axis_angle(mpars['specimen_dec'], mpars['specimen_inc'], 247.8, -28.8) < 0.1
        assert abs(mpars['specimen_mad'] - 18.6) < 0.06

    def test_n_counts_the_steps_not_the_origin(self):
        """specimen_n (dir_n_measurements) is the number of steps; the origin is not a measurement."""
        data = _make_datablock([0, 0, 0], [45, 45, 45], [1.0, 0.5, 0.1])
        mpars = pmag.domean(data, 0, 2, 'DE-BFL-O')
        assert mpars['specimen_n'] == 3
        assert mpars['specimen_n'] == pmag.domean(data, 0, 2, 'DE-BFL')['specimen_n']


# ---------------------------------------------------------------------------
# Bad-data handling
# ---------------------------------------------------------------------------

class TestDomeanBadData:
    """Tests for domean's handling of 'b' (bad) flagged data."""

    def test_bad_points_excluded(self):
        """Points flagged 'b' are excluded from the calculation."""
        # Quality flag must be at index 5 (6-element records)
        data = [
            [0, 10, 45, 1.0, '', 'g'],
            [1, 10, 45, 0.8, '', 'g'],
            [2, 90, 0, 0.6, '', 'b'],  # outlier, flagged bad
            [3, 10, 45, 0.4, '', 'g'],
            [4, 10, 45, 0.2, '', 'g'],
        ]
        mpars = pmag.domean(data, 0, 4, 'DE-FM')
        # The bad point at D=90, I=0 should not affect the mean
        assert_allclose(mpars['specimen_dec'], 10.0, atol=1.0)
        assert_allclose(mpars['specimen_inc'], 45.0, atol=1.0)
