import os
import unittest
import glob
from programs import polemap_magic
from programs import eqarea_magic
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




class TestEqareaMagic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        glob_strings = ['data_files/eqarea_magic/*.png']
        for string in glob_strings:
            for fname in glob.glob(string):
                os.remove(fname)

    def test_success(self):
        res, outfiles = eqarea_magic.plot_eq(dir_path="data_files/eqarea_magic", save_plots=True, fmt="png", plot_by="sit")
        self.assertTrue(res)
        for f in outfiles:
            self.assertTrue(os.path.exists(f))
        figs = glob.glob('data_files/eqarea_magic/*.png')
        self.assertEqual(len(figs), 133)


    def test_failure(self):
        res, outfiles = eqarea_magic.plot_eq(dir_path="data_files/", save_plots=True, fmt="png", plot_by="sit")
        self.assertFalse(res)
