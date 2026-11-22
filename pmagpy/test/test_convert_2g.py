"""
Tests for convert._2g_bin and convert._2g_asc, the converters of 2G Enterprises
binary (.dat) and ascii (.asc) files. Both formats store every step in
specimen, geographic and tilt-corrected coordinates, so the orientation
written to the samples table is checked against the file itself. The test
files are in data_files/convert_2_magic/2g_bin_magic and 2g_asc_magic; other
cases are made by changing copies of them.
"""
import contextlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

from pmagpy import pmag
from pmagpy import convert_2_magic as convert

WD = os.path.abspath(os.path.join(os.path.dirname(convert.__file__), os.pardir))
BIN = os.path.join(WD, 'data_files', 'convert_2_magic', '2g_bin_magic')
ASC = os.path.join(WD, 'data_files', 'convert_2_magic', '2g_asc_magic', '_2g_asc')
MN001 = os.path.join(BIN, 'mn1', 'mn001-1a.dat')


def angle(a, b):
    return pmag.angle(np.array(a), np.array(b))[0]


def table(d, name):
    return pd.read_csv(os.path.join(d, name + '.txt'), sep='\t', header=1)


def read_bytes(path):
    with open(path, 'rb') as f:
        return f.read()


def header_start(data):
    """the first byte of the (first) header record"""
    return re.search(rb'\x02[\x00 ]0[\x00 ][\x80-\x8f]', data).start() + 1


def step_starts(data):
    """the first byte of each step record (three bytes before its 0xCD marker)"""
    return [m.start() - 2 for m in re.finditer(rb'(?<=[0-9])[\x00 ]\xcd[\x00 ]', data)]


def set_field(data, start, end, value):
    """data with the field data[start:end] replaced by value, padded with NULs"""
    return data[:start] + value.ljust(end - start, b'\x00')[:end - start] + data[end:]


def relabel(data, labels):
    """data with the treatment labels of its first steps replaced, in order"""
    for start, label in zip(step_starts(data), labels):
        data = set_field(data, start + 5, start + 13, label)
    return data


class Test2gBin(unittest.TestCase):

    def setUp(self):
        self.out = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.out)

    def write(self, data, name='changed.dat'):
        with open(os.path.join(self.out, name), 'wb') as f:
            f.write(data)
        return name

    def run_2g(self, name, **kwargs):
        """convert a file in the output directory; returns (ok, message, what was printed)"""
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            ok, msg = convert._2g_bin(dir_path=self.out, input_dir=self.out, mag_file=name, **kwargs)
        return ok, msg, printed.getvalue()

    def convert(self, folder, name, **kwargs):
        shutil.copy(os.path.join(BIN, folder, name), self.out)
        ok, msg, self.printed = self.run_2g(name, noave=True, **kwargs)
        self.assertTrue(ok, msg)
        # the samples file of the output directory keeps the samples converted before
        sample = str(table(self.out, 'specimens')['sample'].iloc[0])
        samples = table(self.out, 'samples')
        return table(self.out, 'measurements'), samples[samples['sample'].astype(str) == sample].iloc[0]

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

    # --- the header

    def test_comment_without_digits(self):
        # the header comment has no number: the fields used to shift by one
        self.check_orientation('mn1', 'mn001-1a.dat')
        self.check_orientation('KodamaFiles', '165A.dat')

    def test_declination_correction(self):
        # correction 7 degrees; it is added to the azimuth and the bedding
        meas, samp, steps = self.check_orientation('MolinaFiles', 'ton1ab.dat')
        self.assertAlmostEqual(samp.azimuth_dec_correction, 7)
        self.assertIn('SO-CMD-NORTH', samp.method_codes)

    def test_one_digit_azimuth(self):
        # azimuth 4 followed by a leftover byte; correction -0.9
        meas, samp, steps = self.check_orientation('mn1', 'mn017-1b.dat')
        self.assertAlmostEqual(samp.azimuth - samp.azimuth_dec_correction, 4, places=5)

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
        meas, samp, steps = self.check_orientation('Vernet2026', 'GTX080201A.dat')
        self.assertEqual(meas.specimen[0], 'GTX08020')
        self.assertIn('use specname=True', self.printed)
        spec = table(self.out, 'specimens').iloc[0]
        self.assertAlmostEqual(spec.volume, 21.4e-6)
        # named after the file
        ok, msg, printed = self.run_2g('GTX080201A.dat', specname=True)
        self.assertTrue(ok, msg)
        self.assertEqual(table(self.out, 'measurements').specimen[0], 'GTX080201A')

    def test_name_with_a_space(self):
        data = read_bytes(MN001)
        start = header_start(data)
        self.write(set_field(data, start + 5, start + 14, b'MN 01-1A'))
        ok, msg, printed = self.run_2g('changed.dat')
        self.assertTrue(ok, msg)
        self.assertEqual(table(self.out, 'specimens').specimen[0], 'MN 01-1A')

    def test_0xcd_before_the_steps(self):
        # a 0xCD byte (latin-1 'Í') in the header comment, and as the step count (205 steps):
        # neither is taken for a step, and the orientation is still read
        data = read_bytes(MN001)
        start = header_start(data)
        changed = set_field(data, start + 50, start + 60, b'Mart\xcdnez')
        changed = changed[:7] + b'\xcd' + changed[8:]
        self.write(changed)
        ok, msg, printed = self.run_2g('changed.dat', noave=True)
        self.assertTrue(ok, msg)
        header, steps = convert._2g_bin_read(os.path.join(self.out, 'changed.dat'))
        self.assertEqual((header['azimuth'], header['dip']), ('17', '42'))
        self.assertEqual(len(table(self.out, 'measurements')), len(convert._2g_bin_read(MN001)[1]))

    def test_empty_orientation(self):
        # empty azimuth and dip fields are missing values, not 0
        data = read_bytes(MN001)
        start = header_start(data)
        self.write(set_field(set_field(data, start + 101, start + 106, b''), start + 106, start + 110, b''))
        ok, msg, printed = self.run_2g('changed.dat')
        self.assertTrue(ok, msg)
        self.assertIn('the header gives no sample orientation', printed)
        samp = table(self.out, 'samples').iloc[0]
        self.assertTrue('azimuth' not in samp or pd.isna(samp.azimuth))
        self.assertAlmostEqual(samp.bed_dip_direction, (341 - 0.9) % 360, places=5)

    def test_two_headers(self):
        # measurements added in a second session, after a second header with another
        # orientation: the first is used, with a warning
        data = read_bytes(MN001)
        start = header_start(data)
        second = set_field(data[start - 1:start + 137], 102, 107, b'99')
        last = step_starts(data)[-1]
        self.write(data[:last - 1] + second + data[last - 1:])
        ok, msg, printed = self.run_2g('changed.dat', noave=True)
        self.assertTrue(ok, msg)
        self.assertIn('the file holds 2 headers (measurement sessions, or a header repeated)', printed)
        self.assertIn('17/42', printed)
        self.assertIn('99/42', printed)
        header, steps = convert._2g_bin_read(os.path.join(self.out, 'changed.dat'))
        self.assertEqual(steps[-1]['session'], 1)
        self.assertEqual(len(steps), len(convert._2g_bin_read(MN001)[1]))

    def test_full_header_after_the_steps(self):
        # the first header record holds only the name, and the full header follows the steps (as in
        # MA05-4A of Durán-Oreja et al.): the full header is read
        data = read_bytes(MN001)
        start = header_start(data)
        full = data[start - 1:start + 137]
        name_only = data[start:start + 14] + b'\x00' * 123
        self.write(data[:start] + name_only + data[start + 137:] + full)
        header, steps = convert._2g_bin_read(os.path.join(self.out, 'changed.dat'))
        self.assertEqual(len(header['headers']), 2)
        self.assertEqual((header['azimuth'], header['dip'], header['date']), ('17', '42', 'Apr 23 2006'))
        self.assertEqual(len(steps), len(convert._2g_bin_read(MN001)[1]))
        ok, msg, printed = self.run_2g('changed.dat', noave=True)
        self.assertTrue(ok, msg)
        self.assertIn('The orientation of the first complete header (with a date) is used', printed)
        samp = table(self.out, 'samples').iloc[0]
        self.assertAlmostEqual(samp.azimuth, (17 - 0.9) % 360, places=5)

    def test_unusual_header(self):
        # a header whose fields are not where they are in other 2G files (here two bytes are
        # inserted after the volume, as in one known file, 160-1 of Paleomagnetism.org issue 72):
        # it is not read, and the conversion stops with a message, rather than guessing
        data = read_bytes(MN001)
        start = header_start(data)
        head = data[start:start + 137]
        unusual = head[:3] + b'\x88' + head[4:19] + b'\x00\x00' + head[19:] + b'\x00\x00'
        self.write(data[:start] + unusual + data[start + 137:])
        with self.assertRaises(convert._TwoGBinHeaderError):
            convert._2g_bin_read(os.path.join(self.out, 'changed.dat'))
        ok, msg, printed = self.run_2g('changed.dat')
        self.assertFalse(ok)
        self.assertIn('the header of this file is not laid out as in other 2G binary files', msg)
        self.assertFalse(os.path.exists(os.path.join(self.out, 'measurements.txt')))
        # a file that is not a 2G binary file is still a "bad mag file"
        self.write(b'not a 2G file', 'other.dat')
        ok, msg, printed = self.run_2g('other.dat')
        self.assertEqual((ok, msg), (False, 'bad mag file'))

    # --- the measurements

    def test_units(self):
        meas, samp, steps = self.check_orientation('mn1', 'mn001-1a.dat')
        self.assertAlmostEqual(meas.magn_moment[0], float(steps[0]['moment']) * 1e-3)  # emu -> Am2
        # moment / volume: 10 cm3 in the header
        self.assertAlmostEqual(meas.magn_volume[0] / (float(steps[0]['moment']) * 1e-3 / 10e-6), 1, places=6)
        self.assertAlmostEqual(meas.magn_x_sigma[0], float(steps[0]['x_sigma']) * 1e-3)
        self.assertEqual(meas.meas_temp[0], 273)

    def test_volume_differs_from_stored_ratio(self):
        # the header volume changed after measuring: magn_volume follows the header volume
        data = read_bytes(MN001)
        start = header_start(data)
        self.write(set_field(data, start + 14, start + 19, b'12.5'))
        ok, msg, printed = self.run_2g('changed.dat', noave=True)
        self.assertTrue(ok, msg)
        self.assertIn('was not computed with the volume of the header (12.5 cc)', printed)
        meas = table(self.out, 'measurements')
        self.assertAlmostEqual(meas.magn_volume[0] / (meas.magn_moment[0] / 12.5e-6), 1, places=3)

    def test_step_without_value(self):
        # a step labelled 'mT' without a value is left out, with a warning
        self.write(relabel(read_bytes(MN001), [b'NRM', b'mT']))
        ok, msg, printed = self.run_2g('changed.dat', noave=True)
        self.assertTrue(ok, msg)
        self.assertIn("step(s) 2 ('mT') have no treatment value and are left out", printed)
        self.assertEqual(len(table(self.out, 'measurements')), len(convert._2g_bin_read(MN001)[1]) - 1)

    def test_demagnetization_steps(self):
        # alternating field with a decimal, thermal with and without a unit; both protocols
        self.write(relabel(read_bytes(MN001), [b'NRM', b'2.5mT', b'10mT', b'150', b'200C']))
        ok, msg, printed = self.run_2g('changed.dat', noave=True)
        self.assertTrue(ok, msg)
        meas = table(self.out, 'measurements')
        self.assertEqual(list(meas.method_codes[:5]),
                         ['LT-NO:LP-DIR-T:LP-DIR-AF', 'LT-AF-Z:LP-DIR-T:LP-DIR-AF', 'LT-AF-Z:LP-DIR-T:LP-DIR-AF',
                          'LT-T-Z:LP-DIR-T:LP-DIR-AF', 'LT-T-Z:LP-DIR-T:LP-DIR-AF'])
        self.assertAlmostEqual(meas.treat_ac_field[1], 0.0025)
        self.assertAlmostEqual(meas.treat_temp[3], 423)
        self.assertEqual(meas.experiment[0], 'MN001-1A_LP-DIR-T_LP-DIR-AF')

    def test_replicates(self):
        # mn004-2b measures the NRM twice: all kept by default (noave=True), averaged with
        # noave=False, the last kept with savelast
        name = 'mn004-2b.dat'
        shutil.copy(os.path.join(BIN, 'mn1', name), self.out)
        header, steps = convert._2g_bin_read(os.path.join(self.out, name))
        self.assertEqual([s['treatment'] for s in steps[:2]], ['NRM', 'NRM'])
        moments = [float(s['moment']) * 1e-3 for s in steps[:2]]
        self.run_2g(name)
        meas = table(self.out, 'measurements')
        self.assertEqual(len(meas), len(steps))
        self.assertFalse(meas.method_codes.str.contains('DE-VM').any())
        self.run_2g(name, noave=False)
        meas = table(self.out, 'measurements')
        self.assertIn('DE-VM', meas.method_codes[0])
        self.assertTrue(min(moments) < meas.magn_moment[0] < max(moments))
        self.assertAlmostEqual(meas.magn_volume[0] / (meas.magn_moment[0] / 10e-6), 1, places=6)
        self.assertTrue('magn_x_sigma' not in meas or pd.isna(meas.magn_x_sigma[0]))
        self.run_2g(name, savelast=True)
        meas = table(self.out, 'measurements')
        self.assertAlmostEqual(meas.magn_moment[0], moments[1])

    def test_paleointensity(self):
        labels = [b'NRM', b'100.0C', b'100.1C', b'150.1C', b'150.0C', b'150.2C', b'200.0C', b'200.3C', b'250C']
        self.write(relabel(read_bytes(MN001), labels))
        # in-field steps need the lab field
        ok, msg, printed = self.run_2g('changed.dat', experiment='PI', noave=True)
        self.assertFalse(ok)
        self.assertIn('labfield is needed', msg)
        ok, msg, printed = self.run_2g('changed.dat', experiment='PI', labfield=40, labfield_phi=0,
                                       labfield_theta=90, noave=True)
        self.assertTrue(ok, msg)
        meas = table(self.out, 'measurements')
        lt = [codes.split(':')[0] for codes in meas.method_codes[:9]]
        self.assertEqual(lt, ['LT-NO', 'LT-T-Z', 'LT-T-I', 'LT-T-I', 'LT-T-Z', 'LT-PTRM-I', 'LT-T-Z',
                              'LT-PTRM-MD', 'LT-T-Z'])
        self.assertTrue(meas.method_codes.str.contains('LP-PI-TRM').all())
        self.assertAlmostEqual(meas.treat_dc_field[2], 40e-6)
        self.assertAlmostEqual(meas.treat_dc_field_theta[2], 90)
        self.assertEqual(meas.treat_dc_field[1], 0)
        self.assertEqual(meas.treat_dc_field[7], 0)  # tail check in zero field
        self.assertAlmostEqual(meas.treat_temp[8], 523)  # 250C without a code: zero field

    def test_anisotropy_of_trm_and_arm(self):
        labels = [b'500.0C', b'500.1C', b'500.2C', b'500.3C', b'500.4C', b'500.5C', b'500.6C', b'500.7C']
        self.write(relabel(read_bytes(MN001), labels))
        ok, msg, printed = self.run_2g('changed.dat', experiment='ATRM 6', labfield=40, noave=True)
        self.assertTrue(ok, msg)
        meas = table(self.out, 'measurements')
        self.assertTrue(meas.method_codes[:8].str.contains('LP-AN-TRM').all())
        self.assertEqual([c.split(':')[0] for c in meas.method_codes[:8]],
                         ['LT-T-Z'] + ['LT-T-I'] * 6 + ['LT-PTRM-I'])
        self.assertEqual(list(meas.treat_dc_field_phi[1:7]), [0, 90, 0, 180, 270, 0])
        self.assertEqual(list(meas.treat_dc_field_theta[1:7]), [0, 0, 90, 0, 0, -90])
        # AARM: a baseline before each in-field step, as ipmag.aarm_magic and thellier_gui pair them
        labels = [b'%d.%dmT' % (field, code) for field in (80, 90) for k in range(1, 7) for code in (0, k)]
        self.assertEqual(len(labels), len(step_starts(read_bytes(MN001))))
        self.write(relabel(read_bytes(MN001), labels))
        ok, msg, printed = self.run_2g('changed.dat', experiment='AARM 6', labfield=50, noave=True)
        self.assertTrue(ok, msg)
        self.assertNotIn('needs a baseline', printed)
        meas = table(self.out, 'measurements')
        self.assertEqual([c.split(':')[0] for c in meas.method_codes[:12]], ['LT-AF-Z', 'LT-AF-I'] * 6)
        self.assertTrue(meas.method_codes[:12].str.contains('LP-AN-ARM').all())
        self.assertAlmostEqual(meas.treat_ac_field[3], 0.08)
        self.assertAlmostEqual(meas.treat_dc_field[3], 50e-6)
        self.assertEqual(list(meas.treat_dc_field_phi[1:12:2]), [0, 90, 0, 180, 270, 0])
        # a single baseline: a warning
        labels = [b'80.0mT', b'80.1mT', b'80.2mT', b'80.3mT', b'80.4mT', b'80.5mT', b'80.6mT']
        self.write(relabel(read_bytes(MN001), labels))
        ok, msg, printed = self.run_2g('changed.dat', experiment='AARM 6', labfield=50, noave=True)
        self.assertTrue(ok, msg)
        self.assertIn('an AARM experiment needs a baseline (XXX.0) before each in-field step', printed)
        # other numbers of positions are not supported
        ok, msg, printed = self.run_2g('changed.dat', experiment='AARM 9', labfield=50)
        self.assertFalse(ok)

    def test_cooling_rate(self):
        self.write(relabel(read_bytes(MN001), [b'500.0C', b'500.1C', b'500.2C', b'500.7C']))
        ok, msg, printed = self.run_2g('changed.dat', experiment='CR', labfield=40)
        self.assertFalse(ok)
        self.assertIn('cooling_times_list', msg)
        ok, msg, printed = self.run_2g('changed.dat', experiment='CR', labfield=40,
                                       cooling_times_list='10,1', noave=True)
        self.assertTrue(ok, msg)
        meas = table(self.out, 'measurements')
        self.assertEqual([c.split(':')[0] for c in meas.method_codes[:4]],
                         ['LT-T-Z', 'LT-T-I', 'LT-T-I', 'LT-PTRM-I'])
        # the form thellier_gui reads (cooling_rate:<rate>:K/min)
        self.assertEqual(list(meas.description[1:4]),
                         ['cooling_rate:10:K/min', 'cooling_rate:1:K/min', 'cooling_rate:1:K/min'])
        # averaged replicates keep the rate at the end of the description
        self.write(relabel(read_bytes(MN001), [b'500.0C', b'500.1C', b'500.1C', b'500.7C']))
        ok, msg, printed = self.run_2g('changed.dat', experiment='CR', labfield=40,
                                       cooling_times_list='10,1', noave=False)
        self.assertTrue(ok, msg)
        meas = table(self.out, 'measurements')
        self.assertEqual(meas.description[1], 'mean of 2 measurements; cooling_rate:10:K/min')
        description = meas.description[1].split(':')
        self.assertEqual(float(description[description.index('K/min') - 1]), 10)
        # non-linear TRM is not supported
        ok, msg, printed = self.run_2g('changed.dat', experiment='NLT', labfield=40)
        self.assertFalse(ok)

    # --- names and files

    def test_naming_convention_8(self):
        shutil.copy(MN001, os.path.join(self.out, 'S1_A_1.dat'))
        ok, msg, printed = self.run_2g('S1_A_1.dat', samp_con='8')
        self.assertFalse(ok)  # the name in the file, MN001-1A, has no underscores
        ok, msg, printed = self.run_2g('S1_A_1.dat', samp_con='8', specname=True)
        self.assertTrue(ok, msg)
        samp = table(self.out, 'samples').iloc[0]
        self.assertEqual((samp['sample'], samp.site), ('S1_A', 'S1'))

    def test_samples_file_of_the_output_directory(self):
        # samples already in the output directory are kept
        shutil.copy(os.path.join(BIN, 'mn1', 'mn017-1b.dat'), self.out)
        self.run_2g('mn017-1b.dat')
        shutil.copy(MN001, self.out)
        self.run_2g('mn001-1a.dat')
        self.assertEqual(sorted(table(self.out, 'samples')['sample']), ['MN001-1A', 'MN017-1B'])
        # a sample converted again: the fields the file gives are updated, its other columns kept
        samples = table(self.out, 'samples')
        samples['lat'], samples['lithologies'] = 45.5, 'Basalt'
        samples.loc[samples['sample'] == 'MN001-1A', 'azimuth'] = 999
        with open(os.path.join(self.out, 'samples.txt'), 'w') as f:
            f.write('tab\tsamples\n')
            samples.to_csv(f, sep='\t', index=False)
        self.run_2g('mn001-1a.dat')
        samples = table(self.out, 'samples').set_index('sample')
        self.assertEqual(len(samples), 2)
        self.assertAlmostEqual(samples.loc['MN001-1A', 'azimuth'], (17 - 0.9) % 360, places=5)
        self.assertEqual((samples.loc['MN001-1A', 'lat'], samples.loc['MN001-1A', 'lithologies']), (45.5, 'Basalt'))
        # a file without an orientation leaves the orientation of the row as it is
        data = read_bytes(MN001)
        start = header_start(data)
        self.write(set_field(data, start + 101, start + 106, b''), 'mn001-1a.dat')
        self.run_2g('mn001-1a.dat')
        samples = table(self.out, 'samples').set_index('sample')
        self.assertAlmostEqual(samples.loc['MN001-1A', 'azimuth'], (17 - 0.9) % 360, places=5)

    def test_rejected_remeasurement(self):
        # a step whose stored geographic direction does not follow from the header orientation,
        # unlike the other steps, is marked b with a note
        data = read_bytes(MN001)
        third = step_starts(data)[2]
        geo_dec = float(data[third + 25:third + 31].split(b'\x00')[0])
        self.write(set_field(data, third + 25, third + 31, b'%.1f' % ((geo_dec + 30) % 360)))
        ok, msg, printed = self.run_2g('changed.dat')
        self.assertTrue(ok, msg)
        self.assertIn('1 step(s) have a stored geographic direction that does not follow from the header', printed)
        meas = table(self.out, 'measurements')
        self.assertEqual(list(meas.quality[:4]), ['g', 'g', 'b', 'g'])
        self.assertIn('probably a rejected remeasurement', meas.description[2])
        # when most steps do not follow from it, the orientation is in doubt: a warning, no b
        start = header_start(data)
        self.write(set_field(data, start + 101, start + 106, b'47'))
        ok, msg, printed = self.run_2g('changed.dat')
        self.assertIn('the orientation may have been changed after the measurements', printed)
        self.assertTrue((table(self.out, 'measurements').quality == 'g').all())

    def cli(self, *args):
        script = os.path.join(WD, 'programs', 'conversion_scripts', '_2g_bin_magic.py')
        return subprocess.run([sys.executable, script, '-ID', self.out, '-WD', self.out] + list(args),
                              capture_output=True, text=True, env=dict(os.environ, PYTHONPATH=WD))

    def test_command_line(self):
        shutil.copy(MN001, self.out)
        result = self.cli('-f', 'mn001-1a.dat', '-fn')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        meas = table(self.out, 'measurements')
        self.assertEqual(meas.specimen[0], 'mn001-1a')
        self.assertEqual(len(meas), len(convert._2g_bin_read(MN001)[1]))
        # replicates: all kept by default (and with -A), averaged with -ave, the last kept with -sav
        shutil.copy(os.path.join(BIN, 'mn1', 'mn004-2b.dat'), self.out)
        labels = [s['treatment'] for s in convert._2g_bin_read(os.path.join(self.out, 'mn004-2b.dat'))[1]]
        n_steps = len(labels)
        n_runs = sum(1 for k, label in enumerate(labels) if k == 0 or labels[k - 1] != label)
        self.assertLess(n_runs, n_steps)
        for flags, n in (([], n_steps), (['-A'], n_steps), (['-ave'], n_runs), (['-sav'], n_runs)):
            result = self.cli('-f', 'mn004-2b.dat', *flags)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(len(table(self.out, 'measurements')), n, flags)
        # an experiment with a lab field and cooling rates; without the rates it fails with status 1
        self.write(relabel(read_bytes(MN001), [b'500.0C', b'500.1C', b'500.2C', b'500.7C']))
        result = self.cli('-f', 'changed.dat', '-exp', 'CR', '-dc', '40', '0', '90', '-cr', '10,1')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        meas = table(self.out, 'measurements')
        self.assertAlmostEqual(meas.treat_dc_field[1], 40e-6)
        self.assertEqual(meas.treat_dc_field_theta[1], 90)
        self.assertEqual(meas.description[1], 'cooling_rate:10:K/min')
        result = self.cli('-f', 'changed.dat', '-exp', 'CR', '-dc', '40', '0', '90')
        self.assertEqual(result.returncode, 1)
        self.assertIn('cooling_times_list', result.stdout)


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
        self.assertEqual(os.path.realpath(msg), os.path.realpath(os.path.join(self.out, 'measurements.txt')))
        # sampling method codes on the samples, lab protocols on the specimens
        self.assertEqual(samp.method_codes, 'FS-FD:SO-POM')
        self.assertIn('LP-DIR', table(self.out, 'specimens').method_codes[0])

    def test_alternating_field_and_savelast(self):
        name = 'OK3_15af.asc'
        shutil.copy(os.path.join(ASC, name), self.out)
        ok, msg = convert._2g_asc(dir_path=self.out, input_dir=self.out, mag_file=name)
        self.assertTrue(ok, msg)
        meas = table(self.out, 'measurements')
        self.assertTrue(meas.method_codes[1:].str.startswith('LT-AF-Z').all())
        self.assertTrue((meas.treat_ac_field[1:] > 0).all())
        # the last of replicate steps
        name = 'DR3B.asc'
        shutil.copy(os.path.join(ASC, name), self.out)
        ok, msg = convert._2g_asc(dir_path=self.out, input_dir=self.out, mag_file=name, savelast=True)
        self.assertTrue(ok, msg)
        self.assertGreater(len(table(self.out, 'measurements')), 0)

    def test_declination_and_overturned_bed(self):
        # MD is added to the azimuths; O flags an overturned bed
        with open(os.path.join(ASC, 'DR3B.asc'), encoding='latin-1') as f:
            lines = f.read().split('\n')
        names, values = lines[1].split('\t'), lines[2].split('\t')
        values[names.index('MD')] = '5'
        values[names.index('O')] = '1'
        lines[2] = '\t'.join(values)
        with open(os.path.join(self.out, 'DR3B.asc'), 'w', encoding='latin-1') as f:
            f.write('\n'.join(lines))
        ok, msg = convert._2g_asc(dir_path=self.out, input_dir=self.out, mag_file='DR3B.asc')
        self.assertTrue(ok, msg)
        samp = table(self.out, 'samples').iloc[0]
        self.assertAlmostEqual(samp.azimuth, (257 + 5) % 360)
        self.assertAlmostEqual(samp.bed_dip_direction, (76 + 5 + 180) % 360)
        self.assertAlmostEqual(samp.bed_dip, 180 - 50)
        self.assertIn('SO-CMD-NORTH', samp.method_codes)


if __name__ == '__main__':
    unittest.main()
