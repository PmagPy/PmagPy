import os
import unittest
import cartopy
from pmagpy import pmag
from pmagpy import pmagplotlib
WD = pmag.get_test_WD()


class TestPlotMagMap(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_success(self):
        date, mod, lon_0, alt, ghfile = 1956.0725, 'cals10k.2', 0, 0, ""  # only date is required
        Ds, Is, Bs, Brs, lons, lats = pmag.do_mag_map(
            date, mod=mod, lon_0=lon_0, alt=alt, file=ghfile)
        res_0 = pmagplotlib.plot_mag_map(
            1, Bs, lons, lats, 'B', date=date, contours=True, lon_0=10, proj="Mollweide")  # plot the field strength
        res_1 = pmagplotlib.plot_mag_map(
            2, Is, lons, lats, 'I', date=date, contours=True)  # plot the inclination
        res_2 = pmagplotlib.plot_mag_map(
            3, Ds, lons, lats, 'D', date=date, contours=True)
        if cartopy.__version__ != "0.16.0":
            for res in [res_0, res_1, res_2]:
                self.assertIsInstance(res, cartopy.mpl.geoaxes.GeoAxesSubplot)
        else:
            for res in [res_1, res_2]:
                self.assertIsInstance(res, cartopy.mpl.geoaxes.GeoAxesSubplot)
