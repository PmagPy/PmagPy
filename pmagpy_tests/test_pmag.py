#!/usr/bin/env python

import os
import unittest
import numpy as np
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


class TestDomean(unittest.TestCase):
    """Principal component fits of demagnetization data (Kirschvink, 1980)."""

    @staticmethod
    def block(directions):
        """[treatment, dec, inc, intensity, quality] records from (dec, inc, intensity)."""
        return [[i, dec, inc, intensity, 'g'] for i, (dec, inc, intensity) in enumerate(directions)]

    @staticmethod
    def angle(mpars, dec, inc):
        return pmag.angle([mpars['specimen_dec'], mpars['specimen_inc']], [dec, inc])[0]

    @staticmethod
    def noisy_steps():
        """Two-component demagnetization data with measurement noise."""
        rng = np.random.default_rng(963)
        chrm = np.array(pmag.dir2cart([20., 40., 1.]))
        overprint = np.array(pmag.dir2cart([355., 70., 1.]))
        temps = np.array([300, 350, 400, 450, 500, 525, 550, 565, 580])
        steps = [3e-5 * np.clip((585 - t) / 235, 0, 1) * chrm +
                 1.2e-5 * np.clip((470 - t) / 370, 0, 1) * overprint +
                 rng.normal(0, 4e-7, 3) for t in temps]
        return [pmag.cart2dir(x) for x in steps], np.array(steps)

    def test_anchored_line_analytic(self):
        # T = diag(1, 0.25, 0): the anchored principal axis is x (dec 0),
        # whereas the vector mean of the two steps is at dec atan(0.5) = 26.57
        mpars = pmag.domean(self.block([(0., 0., 1.), (90., 0., 0.5)]), 0, 1, 'DE-BFL-A')
        self.assertLess(self.angle(mpars, 0., 0.), 1e-6)
        self.assertAlmostEqual(mpars['specimen_mad'], np.degrees(np.arctan(0.5)), places=6)

    def test_anchored_line_collinear_with_origin(self):
        # steps decaying along one direction: the fit is that direction (not its antipode)
        steps = [(30., 45., m) for m in (5., 4., 2.5, 1., 0.2)]
        mpars = pmag.domean(self.block(steps), 0, 4, 'DE-BFL-A')
        self.assertLess(self.angle(mpars, 30., 45.), 1e-6)
        self.assertLess(mpars['specimen_mad'], 1e-6)

    def test_anchored_line_single_step(self):
        mpars = pmag.domean(self.block([(30., 45., 5.), (200., -10., 2.)]), 0, 0, 'DE-BFL-A')
        self.assertLess(self.angle(mpars, 30., 45.), 1e-6)

    def test_anchored_line_matches_eigenvector_about_origin(self):
        directions, X = self.noisy_steps()
        mpars = pmag.domean(self.block(directions), 0, len(X) - 1, 'DE-BFL-A')
        tau, V = np.linalg.eigh(X.T @ X)
        v1 = V[:, -1] * np.sign(V[:, -1] @ (X[0] - X[-1]))
        expected = pmag.cart2dir(v1)
        self.assertLess(self.angle(mpars, expected[0], expected[1]), 1e-6)
        tau = tau[::-1] / tau.sum()
        mad = np.degrees(np.arctan(np.sqrt(tau[1] + tau[2]) / np.sqrt(tau[0])))
        self.assertAlmostEqual(mpars['specimen_mad'], mad, places=6)

    def test_vector_mean(self):
        # DE-VM is the direction of the sum of the steps: atan(0.5) for the two steps
        mpars = pmag.domean(self.block([(0., 0., 1.), (90., 0., 0.5)]), 0, 1, 'DE-VM')
        self.assertLess(self.angle(mpars, np.degrees(np.arctan(0.5)), 0.), 1e-6)
        self.assertEqual(mpars['specimen_direction_type'], 'l')
        self.assertEqual(mpars['specimen_n'], 2)
        self.assertEqual(mpars['specimen_dang'], -1)
        self.assertNotIn('specimen_mad', mpars)

    def test_free_line_matches_eigenvector_about_centre_of_mass(self):
        directions, X = self.noisy_steps()
        mpars = pmag.domean(self.block(directions), 0, len(X) - 1, 'DE-BFL')
        Xc = X - X.mean(axis=0)
        tau, V = np.linalg.eigh(Xc.T @ Xc)
        v1 = V[:, -1] * np.sign(V[:, -1] @ (X[0] - X[-1]))
        expected = pmag.cart2dir(v1)
        self.assertLess(self.angle(mpars, expected[0], expected[1]), 1e-6)
