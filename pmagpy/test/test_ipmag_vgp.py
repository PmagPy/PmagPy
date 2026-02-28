"""
Tests for VGP and paleolatitude functions in ipmag.py.

Covers lat_from_inc / inc_from_lat (dipole equation), vgp_calc
(DataFrame-based VGP computation), and sb_vgp_calc (VGP scatter).
Includes cross-validation against the parallel pmag.py implementations
(pmag.plat, pmag.pinc, pmag.dia_vgp).
"""
import numpy as np
import pandas as pd
from numpy.testing import assert_allclose

from pmagpy import ipmag, pmag


# ---------------------------------------------------------------------------
# lat_from_inc / inc_from_lat: cross-validation with pmag.plat / pmag.pinc
# ---------------------------------------------------------------------------

class TestLatFromIncCrossValidation:
    """Cross-validate ipmag.lat_from_inc against pmag.plat."""

    def test_matches_pmag_plat(self):
        """ipmag.lat_from_inc gives the same result as pmag.plat."""
        incs = [0, 15, 30, 45, 60, 75, 85, -30, -60]
        for inc in incs:
            ipmag_result = ipmag.lat_from_inc(inc)
            pmag_result = float(pmag.plat(inc))
            assert_allclose(ipmag_result, pmag_result, atol=1e-10,
                            err_msg=f"Mismatch at inc={inc}")

    def test_docstring_example(self):
        """Verify the lat_from_inc docstring example."""
        result = ipmag.lat_from_inc(45)
        assert_allclose(result, 26.56505117707799, atol=1e-10)

    def test_with_a95_returns_bounds(self):
        """Verify the lat_from_inc docstring example with a95."""
        plat, plat_max, plat_min = ipmag.lat_from_inc(20, a95=5)
        assert_allclose(plat, 10.314104815618196, atol=1e-6)
        assert_allclose(plat_max, 13.12426812279171, atol=1e-6)
        assert_allclose(plat_min, 7.630740212430057, atol=1e-6)

    def test_bounds_bracket_central_value(self):
        """With a95, max > central > min for positive inclination."""
        plat, plat_max, plat_min = ipmag.lat_from_inc(40, a95=3)
        assert plat_max > plat > plat_min


class TestIncFromLatCrossValidation:
    """Cross-validate ipmag.inc_from_lat against pmag.pinc."""

    def test_matches_pmag_pinc(self):
        """ipmag.inc_from_lat gives the same result as pmag.pinc."""
        lats = [0, 15, 30, 45, 60, 75, 90, -45, -90]
        for lat in lats:
            ipmag_result = ipmag.inc_from_lat(lat)
            pmag_result = float(pmag.pinc(lat))
            assert_allclose(ipmag_result, pmag_result, atol=1e-10,
                            err_msg=f"Mismatch at lat={lat}")

    def test_docstring_example(self):
        """Verify the inc_from_lat docstring example."""
        result = ipmag.inc_from_lat(45)
        assert_allclose(result, 63.434948822922, atol=1e-6)

    def test_roundtrip_with_lat_from_inc(self):
        """lat_from_inc(inc_from_lat(lat)) recovers the original latitude."""
        lats = [0, 20, 45, 70, 90, -30, -75]
        for lat in lats:
            inc = ipmag.inc_from_lat(lat)
            recovered = ipmag.lat_from_inc(inc)
            assert_allclose(recovered, lat, atol=1e-10,
                            err_msg=f"Roundtrip failed at lat={lat}")


# ---------------------------------------------------------------------------
# vgp_calc: DataFrame-based VGP computation
# ---------------------------------------------------------------------------

class TestVgpCalc:
    """Tests for ipmag.vgp_calc."""

    def _make_dataframe(self, decs, incs, site_lats, site_lons):
        """Helper to build a DataFrame with tilt-corrected columns."""
        return pd.DataFrame({
            'dec_tc': decs,
            'inc_tc': incs,
            'site_lat': site_lats,
            'site_lon': site_lons,
        })

    def test_adds_expected_columns(self):
        """vgp_calc adds paleolatitude, vgp_lat, vgp_lon, and reversed columns."""
        df = self._make_dataframe([0], [45], [30], [0])
        result = ipmag.vgp_calc(df)
        for col in ['paleolatitude', 'vgp_lat', 'vgp_lon',
                     'vgp_lat_rev', 'vgp_lon_rev']:
            assert col in result.columns, f"Missing column: {col}"

    def test_paleolatitude_matches_lat_from_inc(self):
        """Paleolatitude column matches ipmag.lat_from_inc."""
        incs = [20, 45, 60, -30]
        df = self._make_dataframe([0]*4, incs, [0]*4, [0]*4)
        result = ipmag.vgp_calc(df)
        for i, inc in enumerate(incs):
            expected = ipmag.lat_from_inc(inc)
            assert_allclose(result['paleolatitude'].iloc[i], expected, atol=1e-10,
                            err_msg=f"Paleolatitude mismatch at inc={inc}")

    def test_vgp_lat_matches_dia_vgp(self):
        """VGP latitude from vgp_calc matches pmag.dia_vgp."""
        decs = [4.0, 350.0, 180.0]
        incs = [41.0, 55.0, -30.0]
        site_lats = [33.0, 45.0, -20.0]
        site_lons = [-117.0, 10.0, 120.0]
        df = self._make_dataframe(decs, incs, site_lats, site_lons)
        result = ipmag.vgp_calc(df)
        for i in range(len(decs)):
            _, plat_pmag, _, _ = pmag.dia_vgp(decs[i], incs[i], 0,
                                               site_lats[i], site_lons[i])
            assert_allclose(result['vgp_lat'].iloc[i], plat_pmag, atol=1e-6,
                            err_msg=f"VGP lat mismatch at row {i}")

    def test_reversed_poles_are_antipodal(self):
        """Reversed VGP columns are the antipode of the normal columns."""
        df = self._make_dataframe([10, 200], [50, -40], [40, -30], [0, 100])
        result = ipmag.vgp_calc(df)
        assert_allclose(result['vgp_lat_rev'], -result['vgp_lat'], atol=1e-10)
        assert_allclose(result['vgp_lon_rev'],
                        (result['vgp_lon'] - 180.) % 360., atol=1e-10)

    def test_axial_dipole_at_equator(self):
        """Dec=0, Inc=0 at the equator → VGP at geographic north pole."""
        df = self._make_dataframe([0], [0], [0], [0])
        result = ipmag.vgp_calc(df)
        assert_allclose(result['vgp_lat'].iloc[0], 90.0, atol=1e-6)

    def test_tilt_correction_no(self):
        """tilt_correction='no' uses dec_is/inc_is columns."""
        df = pd.DataFrame({
            'dec_is': [4.0],
            'inc_is': [41.0],
            'site_lat': [33.0],
            'site_lon': [-117.0],
        })
        result = ipmag.vgp_calc(df, tilt_correction='no')
        # Should match the same calculation using tilt-corrected path
        _, plat_expected, _, _ = pmag.dia_vgp(4.0, 41.0, 0, 33.0, -117.0)
        assert_allclose(result['vgp_lat'].iloc[0], plat_expected, atol=1e-6)


# ---------------------------------------------------------------------------
# sb_vgp_calc: VGP scatter (Sb)
# ---------------------------------------------------------------------------

class TestSbVgpCalc:
    """Tests for ipmag.sb_vgp_calc."""

    def _make_sb_dataframe(self, decs, incs, site_lats, site_lons,
                           vgp_lats, vgp_lons, ks, ns):
        """Helper to build a DataFrame for sb_vgp_calc."""
        return pd.DataFrame({
            'dec_tc': decs,
            'inc_tc': incs,
            'site_lat': site_lats,
            'site_lon': site_lons,
            'vgp_lat': vgp_lats,
            'vgp_lon': vgp_lons,
            'k': ks,
            'n': ns,
        })

    def test_tight_cluster_small_sb(self):
        """Tightly clustered VGPs produce small Sb (no site correction)."""
        decs = [10, 11, 9, 10.5, 9.5]
        incs = [50, 51, 49, 50.5, 49.5]
        slats = [45]*5
        slons = [10]*5
        df = pd.DataFrame({
            'dec_tc': decs, 'inc_tc': incs,
            'site_lat': slats, 'site_lon': slons,
            'k': [200]*5, 'n': [8]*5,
        })
        df = ipmag.vgp_calc(df)
        Sb = ipmag.sb_vgp_calc(df, site_correction='no')
        assert Sb < 5.0

    def test_more_scatter_larger_sb(self):
        """More dispersed VGPs produce larger Sb than tightly clustered ones."""
        slats = [45]*5
        slons = [10]*5
        # Tight cluster
        df_tight = pd.DataFrame({
            'dec_tc': [10, 11, 9, 10.5, 9.5],
            'inc_tc': [50, 51, 49, 50.5, 49.5],
            'site_lat': slats, 'site_lon': slons,
            'k': [100]*5, 'n': [8]*5,
        })
        df_tight = ipmag.vgp_calc(df_tight)
        # Dispersed cluster
        df_wide = pd.DataFrame({
            'dec_tc': [10, 30, 350, 20, 0],
            'inc_tc': [50, 40, 60, 30, 70],
            'site_lat': slats, 'site_lon': slons,
            'k': [100]*5, 'n': [8]*5,
        })
        df_wide = ipmag.vgp_calc(df_wide)
        Sb_tight = ipmag.sb_vgp_calc(df_tight, site_correction='no')
        Sb_wide = ipmag.sb_vgp_calc(df_wide, site_correction='no')
        assert Sb_wide > Sb_tight

    def test_returns_scalar(self):
        """sb_vgp_calc returns a single scalar value."""
        decs = [0, 5, 355]
        incs = [45, 43, 47]
        slats = [30]*3
        slons = [0]*3
        df = pd.DataFrame({
            'dec_tc': decs, 'inc_tc': incs,
            'site_lat': slats, 'site_lon': slons,
            'k': [150]*3, 'n': [5]*3,
        })
        df = ipmag.vgp_calc(df)
        Sb = ipmag.sb_vgp_calc(df)
        assert isinstance(Sb, (int, float, np.floating))
