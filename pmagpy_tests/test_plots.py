import os
import unittest
import glob
from programs import polemap_magic
from programs import dmag_magic
from pmagpy import pmag
WD = pmag.get_test_WD()



class TestDmagMagic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        glob_strings = ["*.png", "*.svg", "data_files/3_0/McMurdo/*.png"]
        for string in glob_strings:
            for fname in glob.glob(string):
                os.remove(fname)

    def test_success(self):
        res, outfiles = dmag_magic.plot(dir_path=".", input_dir_path="data_files/3_0/McMurdo", LT="T", plot_by='sit')
        self.assertTrue(res)
        for f in outfiles:
            self.assertTrue(os.path.exists(f))
        images = glob.glob("*.svg")
        self.assertEqual(len(images), 126)

    def test_alt_success(self):
        res, outfiles = dmag_magic.plot(dir_path=".", input_dir_path="data_files/3_0/McMurdo", plot_by='spc', fmt="png")
        self.assertTrue(res)
        for f in outfiles:
            self.assertTrue(os.path.exists(f))
        images = glob.glob("*.png")
        self.assertEqual(len(images), 530)

    def test_with_output_dir(self):
        res, outfiles = dmag_magic.plot(dir_path="data_files/3_0/McMurdo", plot_by='loc', fmt="png")
        self.assertTrue(res)
        for f in outfiles:
            self.assertTrue(os.path.exists(f))
        images = glob.glob("data_files/3_0/McMurdo/*.png")
        self.assertEqual(len(images), 1)




    def test_failure(self):
        res, outfiles = dmag_magic.plot(dir_path=".", input_dir_path="data_files/3_0/McMurdo", plot_by='spc',
                                        fmt="png", LT="FAKE")
        self.assertFalse(res)

    def test_alt_failure(self):
        res, outfiles = dmag_magic.plot(dir_path=".", input_dir_path="data_files/3_0/", plot_by='spc')
        self.assertFalse(res)
