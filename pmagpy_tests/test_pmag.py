#!/usr/bin/env python

import unittest
import pmagpy.pmag as pmag
#import os
#import sys
#WD = sys.prefix

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
