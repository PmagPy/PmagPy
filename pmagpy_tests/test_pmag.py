#!/usr/bin/env python

from __future__ import print_function
from builtins import str
import os
import unittest
import pmagpy.pmag as pmag
WD = pmag.get_test_WD()
PROJECT_WD = os.path.join(WD, "data_files", "2_5", "McMurdo")

class TestLonAdjust(unittest.TestCase):

    def setUp(self):
        pass

    def test_adjust(self):
        result = pmag.adjust_to_360(str(361.), 'location_end_lon')
        self.assertAlmostEqual(1., result)
        result = pmag.adjust_to_360(361., 'location_end_lon')
        self.assertAlmostEqual(1., result)
        result = pmag.adjust_to_360(12., 'site_azimuth')
        self.assertAlmostEqual(12., result)
        result = pmag.adjust_to_360(-10, 'site_dec')
        self.assertAlmostEqual(350., result)
        result = pmag.adjust_to_360(None, 'dip_direction')
        self.assertEqual('', result)
        result = pmag.adjust_to_360('value', 'ocean_sea')
        self.assertEqual('value', result)
        result = pmag.adjust_to_360(700, 'treatment_temp_decay_rate')
        self.assertEqual(700, result)

class TestConvert2To3(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        os.chdir(WD)
        for fname in ["measurements.txt", "specimens.txt", "samples.txt",
                      "sites.txt", "locations.txt", "criteria.txt"]:
            full_file = os.path.join(PROJECT_WD, fname)
            if os.path.exists(full_file):
                os.remove(full_file)

    def test_upgrade(self):
        meas, upgraded, no_upgrade = pmag.convert_directory_2_to_3(input_dir=PROJECT_WD,
                                                                   output_dir=PROJECT_WD)
        expect_out = ['measurements.txt', 'specimens.txt', 'samples.txt',
                      'sites.txt', 'locations.txt', 'criteria.txt', 'ages.txt']
        self.assertEqual(sorted(expect_out), sorted(upgraded))
        expect_not_out = ['pmag_results.txt',
                          'rmag_hysteresis.txt', 'rmag_anisotropy.txt',
                          'rmag_results.txt', 'er_images.txt']
        self.assertEqual(sorted(expect_not_out), sorted(no_upgrade))

    def test_upgrade_criteria(self):
        outfile, output = pmag.convert_criteria_file_2_to_3(input_dir=PROJECT_WD, output_dir=PROJECT_WD)
        self.assertEqual('criteria.txt', outfile)
        print(output.df.head())


class TestGetPlateData(unittest.TestCase):

    def test_get_plate_data(self):
        res = pmag.get_plate_data('AF')
        expected_out =  """
0.0        90.00    0.00
1.0        88.38  182.20
2.0        86.76  182.20
"""
        length = len(expected_out)
        self.assertEqual(expected_out, res[:length])


class TestMagicRead(unittest.TestCase):

    def test_magic_read_success(self):
        fname = os.path.join(WD, "data_files", "3_0", "McMurdo", "sites.txt")
        data, ftype = pmag.magic_read(fname)
        self.assertEqual(ftype, 'sites')
        self.assertEqual(len(data), 388)
        data, ftype, magic_keys = pmag.magic_read(fname,
                                                  return_keys=True)
        self.assertEqual(magic_keys[-1], 'vgp_n_samples')

    def test_open_file_non_unicode(self):
        fname = os.path.join(WD, 'data_files', 'lowrie', 'lowrie_example.dat')
        data = pmag.open_file(fname)
        self.assertTrue(len(data) >= 465)

    def test_open_file_unicode(self):
        fname = os.path.join(WD, 'data_files', '3_0', 'Megiddo', 'sites.txt')
        data = pmag.open_file(fname)
        print(len(data))
        self.assertEqual(len(data), 41)


    def test_magic_read_no_such_file(self):
        fname = os.path.join(PROJECT_WD, 'no_sites.txt')
        data, ftype = pmag.magic_read(fname)
        self.assertEqual(ftype, 'empty_file')
        self.assertEqual(len(data), 0)
