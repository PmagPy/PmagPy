"""
Tests for VGP, paleolatitude, and field intensity functions in pmag.py.

Covers dia_vgp (direction → VGP), vgp_di (VGP → direction), pinc/plat
(dipole formula), and b_vdm/vdm_b (field ↔ dipole moment conversions).
"""
import numpy as np
from numpy.testing import assert_allclose

from pmagpy import pmag


# ---------------------------------------------------------------------------
# pinc / plat: dipole inclination–latitude relationship
# ---------------------------------------------------------------------------

class TestPincPlat:
    """Tests for pmag.pinc and pmag.plat (dipole formula pair)."""

    def test_pinc_docstring_example(self):
        """Verify the pinc docstring example."""
        lats = [45, 40, 60, 80, -30, 55]
        result = np.round(pmag.pinc(lats), 1)
        expected = [63.4, 59.2, 73.9, 85.0, -49.1, 70.7]
        assert_allclose(result, expected, atol=0.05)

    def test_plat_docstring_example(self):
        """Verify the plat docstring example."""
        incs = [63.4, 59.2, 73.9, 85, -49.1, 70.7]
        result = np.round(pmag.plat(incs))
        expected = [45., 40., 60., 80., -30., 55.]
        assert_allclose(result, expected, atol=0.5)

    def test_roundtrip(self):
        """plat(pinc(lat)) recovers the original latitude."""
        lats = np.array([0, 15, 30, 45, 60, 75, 90, -45, -90])
        recovered = pmag.plat(pmag.pinc(lats))
        assert_allclose(recovered, lats, atol=1e-10)

    def test_equator(self):
        """Latitude 0 gives inclination 0 (horizontal field at equator)."""
        assert_allclose(pmag.pinc(0), 0.0, atol=1e-10)

    def test_poles(self):
        """Latitude ±90 gives inclination ±90 (vertical field at poles)."""
        assert_allclose(pmag.pinc(90), 90.0, atol=1e-10)
        assert_allclose(pmag.pinc(-90), -90.0, atol=1e-10)

    def test_dipole_formula(self):
        """Verify tan(I) = 2·tan(lat) for a non-trivial latitude."""
        lat = 35.0
        inc = pmag.pinc(lat)
        assert_allclose(np.tan(np.radians(inc)),
                        2.0 * np.tan(np.radians(lat)), atol=1e-10)


# ---------------------------------------------------------------------------
# dia_vgp: direction + site location → VGP
# ---------------------------------------------------------------------------

class TestDiaVgp:
    """Tests for pmag.dia_vgp."""

    def test_docstring_example(self):
        """Verify the example from the docstring."""
        plong, plat, dp, dm = pmag.dia_vgp(4, 41, 0, 33, -117)
        assert_allclose(plong, 41.68629415047637, atol=1e-6)
        assert_allclose(plat, 79.86259998889103, atol=1e-6)
        assert_allclose(dp, 0.0, atol=1e-10)
        assert_allclose(dm, 0.0, atol=1e-10)

    def test_polar_site_vertical_inc(self):
        """North Pole site with vertical-down inclination → VGP at geographic pole."""
        plong, plat, dp, dm = pmag.dia_vgp(0, 90, 0, 90, 0)
        assert_allclose(plat, 90.0, atol=1e-6)

    def test_equatorial_site_axial_dipole(self):
        """Equatorial site with Dec=0, Inc=0 → VGP at geographic north pole."""
        # A horizontal northward direction at the equator is the expected
        # field from an axial geocentric dipole
        plong, plat, dp, dm = pmag.dia_vgp(0, 0, 0, 0, 0)
        assert_allclose(plat, 90.0, atol=1e-6)

    def test_list_input_matches_scalar(self):
        """List-of-lists input matches individual scalar calls."""
        rows = [[4, 41, 2, 33, -117],
                [350, 55, 3, 45, 10],
                [180, -30, 1, -20, 120]]
        plongs, plats, dps, dms = pmag.dia_vgp(rows)
        for i, row in enumerate(rows):
            plong_s, plat_s, dp_s, dm_s = pmag.dia_vgp(*row)
            assert_allclose(plongs[i], plong_s, atol=1e-10,
                            err_msg=f"plong mismatch at row {i}")
            assert_allclose(plats[i], plat_s, atol=1e-10,
                            err_msg=f"plat mismatch at row {i}")


# ---------------------------------------------------------------------------
# vgp_di: VGP + site location → direction
# ---------------------------------------------------------------------------

class TestVgpDi:
    """Tests for pmag.vgp_di."""

    def test_north_pole_vgp_equatorial_site(self):
        """Axial dipole (VGP at north pole) gives Dec=0, Inc=0 at the equator."""
        dec, inc = pmag.vgp_di(90, 0, 0, 0)
        assert_allclose(dec % 360., 0.0, atol=1e-6)
        assert_allclose(inc, 0.0, atol=1e-6)

    def test_north_pole_vgp_matches_pinc(self):
        """Axial dipole at mid-latitude site gives Inc matching dipole formula."""
        slat = 45.0
        dec, inc = pmag.vgp_di(90, 0, slat, 0)
        expected_inc = float(pmag.pinc(slat))
        assert_allclose(dec % 360., 0.0, atol=2e-6)
        assert_allclose(inc, expected_inc, atol=2e-6)

    def test_roundtrip_with_dia_vgp(self):
        """dia_vgp → vgp_di recovers the original direction."""
        dec, inc = 30.0, 45.0
        slat, slong = 40.0, -100.0
        plong, plat_out, _, _ = pmag.dia_vgp(dec, inc, 0.0, slat, slong)
        dec_rec, inc_rec = pmag.vgp_di(plat_out, plong, slat, slong)
        assert_allclose(dec_rec, dec, atol=1e-6)
        assert_allclose(inc_rec, inc, atol=1e-6)

    def test_roundtrip_southern_hemisphere(self):
        """Roundtrip works for a southern-hemisphere site."""
        dec, inc = 185.0, -40.0
        slat, slong = -35.0, 150.0
        plong, plat_out, _, _ = pmag.dia_vgp(dec, inc, 0.0, slat, slong)
        dec_rec, inc_rec = pmag.vgp_di(plat_out, plong, slat, slong)
        assert_allclose(dec_rec, dec, atol=1e-6)
        assert_allclose(inc_rec, inc, atol=1e-6)


# ---------------------------------------------------------------------------
# b_vdm / vdm_b: field intensity ↔ dipole moment
# ---------------------------------------------------------------------------

class TestBvdmVdmB:
    """Tests for pmag.b_vdm and pmag.vdm_b."""

    def test_b_vdm_docstring_example(self):
        """Verify the b_vdm docstring example."""
        result = pmag.b_vdm(33e-6, 22) * 1e-21
        assert_allclose(result, 71.58815974511788, atol=1e-6)

    def test_vdm_b_docstring_example(self):
        """Verify the vdm_b docstring example."""
        result = pmag.vdm_b(65, 20)
        assert_allclose(result, 2.9215108300460446e-26, atol=1e-30)

    def test_roundtrip(self):
        """vdm_b(b_vdm(B, lat), lat) recovers the original field strength."""
        B = 45e-6  # typical crustal field in tesla
        lat = 35.0
        vdm = pmag.b_vdm(B, lat)
        B_rec = pmag.vdm_b(vdm, lat)
        assert_allclose(B_rec, B, atol=1e-15)

    def test_equator_vs_pole_factor_of_two(self):
        """Same B at the equator implies twice the VDM compared to the pole.

        At the pole the field geometry is strongest (factor 2), so a given B
        requires half the dipole moment compared to the equator (factor 1).
        """
        B = 50e-6
        vdm_eq = pmag.b_vdm(B, 0)
        vdm_pole = pmag.b_vdm(B, 90)
        assert_allclose(vdm_eq / vdm_pole, 2.0, atol=1e-10)
