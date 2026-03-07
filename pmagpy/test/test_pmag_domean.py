"""
Tests for pmag.domean — the core direction-fitting function.

Covers Fisher mean (DE-FM), best-fit line (DE-BFL), anchored line (DE-BFL-A),
origin-line (DE-BFL-O), and best-fit plane (DE-BFP) calculation types.

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

class TestDomeanBFLO:
    """Tests for domean with calculation_type='DE-BFL-O'.

    DE-BFL-O forces the best-fit line through the origin, appropriate when
    NRM is completely overprinted and the demagnetization path should trend
    toward the origin.
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

    def test_n_includes_origin_point(self):
        """specimen_n includes the added origin point."""
        data = _make_datablock([0, 0, 0], [45, 45, 45], [1.0, 0.5, 0.1])
        mpars = pmag.domean(data, 0, 2, 'DE-BFL-O')
        # DE-BFL-O adds origin as extra point, so n = 3 data + 1 origin = 4
        assert mpars['specimen_n'] == 4


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
