#!/usr/bin/env python

import unittest
import os
import sys
from pmagpy import pmag
from pmagpy import find_pmag_dir
WD = pmag.get_test_WD()


class TestFindPmagDir(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        os.chdir(WD)

    def test_local(self):
        dir1 = find_pmag_dir.get_pmag_dir()
        os.chdir('..')
        os.chdir('..')
        dir2 = find_pmag_dir.get_pmag_dir()
        os.chdir(dir2)
        dir3 = find_pmag_dir.get_pmag_dir()
        self.assertEqual(dir1, dir2)
        self.assertEqual(dir2, dir3)
        if WD != sys.prefix:
            self.assertIn('PmagPy', dir1)
