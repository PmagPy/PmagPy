import os
import unittest
import glob
from programs import polemap_magic
from pmagpy import pmag
WD = pmag.get_test_WD()


class TestPlotPoleMap(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        for fname in glob.glob("*.png"):
            os.remove(fname)

    def test_success(self):
        res, outfiles = polemap_magic.plot(dir_path="data_files/polemap_magic", do_plot=True, fmt="png")
        self.assertTrue(res)
        for f in outfiles:
            self.assertTrue(os.path.exists(f))
