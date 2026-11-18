"""
Tests for convert._2g_bin and convert._2g_asc, the converters of 2G Enterprises
binary (.dat) and ascii (.asc) files. Both formats store every step in
specimen, geographic and tilt-corrected coordinates, so the orientation
written to the samples table is checked against the file itself. The test
files are in data_files/convert_2_magic/2g_bin_magic and 2g_asc_magic.
"""
import contextlib
import io
import os
import shutil
import tempfile
import unittest

import numpy as np
import pandas as pd

from pmagpy import pmag
from pmagpy import convert_2_magic as convert

WD = os.path.abspath(os.path.join(os.path.dirname(convert.__file__), os.pardir))
BIN = os.path.join(WD, 'data_files', 'convert_2_magic', '2g_bin_magic')
ASC = os.path.join(WD, 'data_files', 'convert_2_magic', '2g_asc_magic', '_2g_asc')


def angle(a, b):
    return pmag.angle(np.array(a), np.array(b))[0]


def table(d, name):
    return pd.read_csv(os.path.join(d, name + '.txt'), sep='\t', header=1)


class Test2gBin(unittest.TestCase):

    def setUp(self):
        self.out = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.out)

    def convert(self, folder, name):
        shutil.copy(os.path.join(BIN, folder, name), self.out)
        ok, msg = convert._2g_bin(dir_path=self.out, input_dir=self.out, mag_file=name)
        self.assertTrue(ok, msg)
        return table(self.out, 'measurements'), table(self.out, 'samples').iloc[0]

    def check_orientation(self, folder, name):
        """the samples table reproduces the stored geographic and tilt-corrected directions"""
        meas, samp = self.convert(folder, name)
        header, steps = convert._2g_bin_read(os.path.join(BIN, folder, name))
        self.assertEqual(len(meas), len(steps))
        for (_, m), s in zip(meas.iterrows(), steps):
            geo = pmag.dogeo(m.dir_dec, m.dir_inc, samp.azimuth, samp.dip)
            self.assertLess(angle(geo, (float(s['geo_dec']), float(s['geo_inc']))), 0.5)
            tilt = pmag.dotilt(geo[0], geo[1], samp.bed_dip_direction, samp.bed_dip)
            self.assertLess(angle(tilt, (float(s['tilt_dec']), float(s['tilt_inc']))), 0.5)
        return meas, samp, steps

    def test_comment_without_digits(self):
        # the header comment has no number: the fields used to shift by one
        self.check_orientation('mn1', 'mn001-1a.dat')
        self.check_orientation('KodamaFiles', '165A.dat')

    def test_declination_correction(self):
        # correction 7 degrees; it is added to the azimuth and the bedding
        meas, samp, steps = self.check_orientation('MolinaFiles', 'ton1ab.dat')
        self.assertAlmostEqual(samp.azimuth_dec_correction, 7)

    def test_one_digit_azimuth(self):
        # azimuth 4 followed by a leftover byte; correction -0.9
        meas, samp, steps = self.check_orientation('mn1', 'mn017-1b.dat')
        self.assertAlmostEqual(samp.azimuth - samp.azimuth_dec_correction, 4, places=5)

    def test_units(self):
        meas, samp, steps = self.check_orientation('mn1', 'mn001-1a.dat')
        self.assertAlmostEqual(meas.magn_moment[0], float(steps[0]['moment']) * 1e-3)  # emu -> Am2
        self.assertAlmostEqual(meas.magn_volume[0], float(steps[0]['moment_volume']) * 1e3)  # emu/cc -> A/m
        self.assertAlmostEqual(meas.magn_x_sigma[0], float(steps[0]['x_sigma']) * 1e-3)

    def test_overturned_bed(self):
        # the file flags the bed as overturned: dip direction + 180, dip 180 - dip
        header, steps = convert._2g_bin_read(os.path.join(BIN, 'Calvin2026', 'ES16-4A.dat'))
        self.assertTrue(header['overturned'])
        meas, samp, steps = self.check_orientation('Calvin2026', 'ES16-4A.dat')
        self.assertAlmostEqual(samp.bed_dip, 180 - float(header['bed_dip']), places=5)
        self.assertAlmostEqual(samp.bed_dip_direction,
                               (float(header['bed_dip_direction']) + 180) % 360, places=5)
        # no declination correction in the file: no SO-CMD-NORTH
        self.assertNotIn('SO-CMD-NORTH', samp.method_codes)

    def test_decimal_volume_and_long_name(self):
        # a decimal volume (21.4 cm3) and a name the file keeps to 8 characters (GTX08020)
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            meas, samp, steps = self.check_orientation('Vernet2026', 'GTX080201A.dat')
        self.assertEqual(meas.specimen[0], 'GTX08020')
        self.assertIn('use specname=True', printed.getvalue())
        spec = table(self.out, 'specimens').iloc[0]
        self.assertAlmostEqual(spec.volume, 21.4e-6)
        # named after the file
        ok, msg = convert._2g_bin(dir_path=self.out, input_dir=self.out, mag_file='GTX080201A.dat',
                                  specname=True)
        self.assertTrue(ok, msg)
        self.assertEqual(table(self.out, 'measurements').specimen[0], 'GTX080201A')

    def test_step_without_value(self):
        # a step labelled 'mT' without a value is left out, with a warning
        with open(os.path.join(BIN, 'mn1', 'mn001-1a.dat'), 'rb') as f:
            data = f.read()
        first = data.index(b'\xcd', data.index(b'\xcd') + 1) - 3  # the second step
        label = data[first + 5:first + 13]
        changed = data[:first + 5] + b'mT'.ljust(len(label), b'\x00') + data[first + 13:]
        with open(os.path.join(self.out, 'changed.dat'), 'wb') as f:
            f.write(changed)
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            ok, msg = convert._2g_bin(dir_path=self.out, input_dir=self.out, mag_file='changed.dat')
        self.assertTrue(ok, msg)
        self.assertIn("step(s) 2 ('mT') have no treatment value and are left out", printed.getvalue())
        header, steps = convert._2g_bin_read(os.path.join(BIN, 'mn1', 'mn001-1a.dat'))
        self.assertEqual(len(table(self.out, 'measurements')), len(steps) - 1)


class Test2gAsc(unittest.TestCase):

    def setUp(self):
        self.out = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.out)

    def test_orientation_and_moment(self):
        name = 'DR3B.asc'
        shutil.copy(os.path.join(ASC, name), self.out)
        ok, msg = convert._2g_asc(dir_path=self.out, input_dir=self.out, mag_file=name)
        self.assertTrue(ok, msg)
        meas = table(self.out, 'measurements')
        samp = table(self.out, 'samples').iloc[0]
        raw = pd.read_csv(os.path.join(ASC, name), sep='\t', skiprows=4, header=None).iloc[:, :10]
        raw.columns = ['n', 'DEMAG', 'CD', 'CI', 'ISD', 'ISI', 'RD', 'RI', 'M', 'J']
        for r in raw.itertuples():
            geo = pmag.dogeo(r.CD, r.CI, samp.azimuth, samp.dip)
            self.assertLess(angle(geo, (r.ISD, r.ISI)), 0.2)
            tilt = pmag.dotilt(geo[0], geo[1], samp.bed_dip_direction, samp.bed_dip)
            self.assertLess(angle(tilt, (r.RD, r.RI)), 0.2)
        # NRM: M is the moment in emu
        self.assertAlmostEqual(meas.magn_moment[0], raw.M[0] * 1e-3)


if __name__ == '__main__':
    unittest.main()
