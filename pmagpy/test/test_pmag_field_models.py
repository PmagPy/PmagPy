"""
Tests for geomagnetic field model functions in pmag.py.

Covers doigrf (IGRF and paleomagnetic field models). Tests in test_igrf.py
cover the ipmag.igrf wrapper with reference values; these tests exercise
the lower-level pmag functions with property-based checks across multiple
dates, locations, and models.
"""
import numpy as np
import pytest
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

    def test_ggf100k_coefficients_match_reference(self):
        """ggf100k Gauss coefficients at year 0 match the reference output
        (coefs.dat) of the Fortran program distributed with the model."""
        gh = pmag.doigrf(0, 45, 0, 0, mod='ggf100k', coeffs=True)
        # g10, g11, h11, g20, g21, h21, g22, h22
        expected = [-36362.3984571547, -268.004040013219, 251.865983091505,
                    -513.389974643557, -204.141435965939, 702.245895380846,
                    19.8362032262578, 363.685173834419]
        assert_allclose(gh[:8], expected, rtol=1e-9)

    @pytest.mark.parametrize("age_ka, adm", [(40.85, 2.44), (1.5, 9.89),
                                             (0.0, 8.18)])
    def test_ggf100k_axial_dipole_moment_matches_paper(self, age_ka, adm):
        """Axial dipole moments (10^22 Am^2) stated by Panovska et al. (2018):
        the Laschamp minimum, the maximum, and the value at 0 BP."""
        date = 1950 - 1000 * age_ka
        g10 = pmag.doigrf(0, 45, 0, date, mod='ggf100k', coeffs=True)[0]
        radius = 6371.2e3  # m
        moment = 1e7 * radius**3 * abs(g10) * 1e-9  # 4 pi a^3 g10 / mu0
        assert_allclose(moment / 1e22, adm, atol=0.005)

    def test_ggf100k_field_varies_smoothly_between_knots(self):
        """The field is continuous between and across the 200 year knots."""
        dates = np.arange(1440, 1660, 10)  # spans knots at 1450 and 1650
        f = [pmag.doigrf(0, 45, 0, date, mod='ggf100k')[3] for date in dates]
        assert np.max(np.abs(np.diff(f))) < 100  # nT per decade

    @pytest.mark.parametrize("date", [-98050, 1990])
    def test_ggf100k_range_endpoints_are_valid(self, date):
        """ggf100k accepts both ends of its valid range."""
        _, _, _, f = pmag.doigrf(0, 45, 0, date, mod='ggf100k')
        assert 10000 < f < 100000

    @pytest.mark.parametrize("date", [-98051, -100001, 1991, 2050])
    def test_ggf100k_outside_valid_range_raises(self, date):
        """ggf100k is only defined from -98050 to 1990."""
        with pytest.raises(ValueError):
            pmag.doigrf(0, 45, 0, date, mod='ggf100k')

    def test_model_total_field_is_vector_magnitude(self):
        """Total field is vector magnitude for paleo models too."""
        x, y, z, f = pmag.doigrf(0, 45, 0, 1000, mod='cals10k.2')
        assert_allclose(f, np.sqrt(x**2 + y**2 + z**2), atol=1e-6)
