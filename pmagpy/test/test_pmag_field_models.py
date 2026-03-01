"""
Tests for geomagnetic field model functions in pmag.py.

Covers doigrf (IGRF and paleomagnetic field models). Tests in test_igrf.py
cover the ipmag.igrf wrapper with reference values; these tests exercise
the lower-level pmag functions with property-based checks across multiple
dates, locations, and models.
"""
import numpy as np
from numpy.testing import assert_allclose

from pmagpy import pmag


# ---------------------------------------------------------------------------
# doigrf: IGRF field calculations
# ---------------------------------------------------------------------------

class TestDoigrf:
    """Tests for pmag.doigrf."""

    def test_total_field_is_vector_magnitude(self):
        """Total field f equals sqrt(x² + y² + z²)."""
        x, y, z, f = pmag.doigrf(-120, 45, 0, 2000)
        assert_allclose(f, np.sqrt(x**2 + y**2 + z**2), atol=1e-6)

    def test_field_at_north_pole(self):
        """At the geographic north pole, the field is nearly vertical down."""
        x, y, z, f = pmag.doigrf(0, 90, 0, 2000)
        # z (downward) should dominate; x and y should be small relative to f
        assert abs(z) > 0.95 * f

    def test_field_at_equator(self):
        """At the magnetic equator, the vertical component is small."""
        # Near the magnetic equator (roughly 0°N, 30°E in ~2000)
        x, y, z, f = pmag.doigrf(30, 0, 0, 2000)
        # Horizontal components should dominate over vertical
        horizontal = np.sqrt(x**2 + y**2)
        assert horizontal > abs(z)

    def test_multiple_dates(self):
        """Field values change with date (secular variation)."""
        _, _, _, f1 = pmag.doigrf(0, 45, 0, 1950)
        _, _, _, f2 = pmag.doigrf(0, 45, 0, 2000)
        # Field intensity changes over 50 years — values should differ
        assert f1 != f2

    def test_altitude_dependence(self):
        """Field weakens with altitude (inverse cube law for dipole)."""
        _, _, _, f_surface = pmag.doigrf(0, 45, 0, 2000)
        _, _, _, f_high = pmag.doigrf(0, 45, 100, 2000)
        assert f_surface > f_high

    def test_negative_longitude_accepted(self):
        """Negative longitude (western hemisphere) produces valid results."""
        x1, y1, z1, f1 = pmag.doigrf(-90, 45, 0, 2000)
        x2, y2, z2, f2 = pmag.doigrf(270, 45, 0, 2000)
        # -90° and 270° are the same location
        assert_allclose(f1, f2, atol=1e-6)

    def test_coeffs_flag_returns_array(self):
        """coeffs=True returns an array of Gauss coefficients."""
        result = pmag.doigrf(30, 70, 10, 2022, coeffs=True)
        assert isinstance(result, np.ndarray)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# doigrf with paleomagnetic field models
# ---------------------------------------------------------------------------

class TestDoigrfPaleoModels:
    """Tests for pmag.doigrf with alternative field models."""

    def test_cals10k_returns_valid_field(self):
        """CALS10k.2 model returns valid field for Holocene date."""
        x, y, z, f = pmag.doigrf(0, 45, 0, 0, mod='cals10k.2')
        # Field should be non-zero and reasonable (10,000–100,000 nT)
        assert 10000 < f < 100000

    def test_arch3k_returns_valid_field(self):
        """ARCH3k model returns valid field for historical date."""
        x, y, z, f = pmag.doigrf(0, 45, 0, 500, mod='arch3k')
        assert 10000 < f < 100000

    def test_model_total_field_is_vector_magnitude(self):
        """Total field is vector magnitude for paleo models too."""
        x, y, z, f = pmag.doigrf(0, 45, 0, 1000, mod='cals10k.2')
        assert_allclose(f, np.sqrt(x**2 + y**2 + z**2), atol=1e-6)
