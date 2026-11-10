"""
Tests for convert.rs3, the converter of Remasoft .rs3 files: the measurements,
the orientation conventions (parameters P1 to P4) and their check against the
directions stored in each file, and the stored fits written to the specimens
table. The test files are in data_files/convert_2_magic/rs3_magic.
"""
import os
import unittest

from pmagpy import pmag
from pmagpy import contribution_builder as cb
from pmagpy import convert_2_magic as convert

# the root of the repository, which holds data_files and is where the output
# of the converters is written and removed again
WD = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))


class TestRs3Magic(unittest.TestCase):
    """
    Remasoft .rs3 files; the expected values are read off the test files
    (see data_files/convert_2_magic/rs3_magic/README.md).
    """

    def setUp(self):
        os.chdir(WD)
        self.input_dir = os.path.join(WD, 'data_files', 'convert_2_magic', 'rs3_magic')
        self.filelist = ['specimens.txt', 'samples.txt', 'sites.txt', 'locations.txt',
                         'measurements.txt', 'custom_meas.txt', 'changed_P2.rs3',
                         'agico_6_0_6_0.rs3', 'fiducial_3.rs3']

    def tearDown(self):
        pmag.remove_files(self.filelist, WD)
        os.chdir(WD)

    def read(self, table):
        return cb.MagicDataFrame(os.path.join(WD, table + '.txt')).df

    def raw(self, table):
        """a table as written, every value as text"""
        import pandas as pd
        return pd.read_csv(os.path.join(WD, table + '.txt'), sep='\t', header=1, dtype=str)

    def fit(self, specimen, component, tilt_correction):
        """one row of the specimens table"""
        df = self.read('specimens')
        rows = df[(df['specimen'] == specimen) & (df['dir_comp'] == component)
                  & (df['dir_tilt_correction'].astype(float) == tilt_correction)]
        self.assertEqual(len(rows), 1)
        return rows.iloc[0]

    def test_rs3_with_no_files(self):
        # a directory without .rs3 files
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic', 'pmd_magic')
        program_ran, error_message = convert.rs3(input_dir_path=input_dir)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'no .rs3 files found')
        # a directory that does not exist
        program_ran, error_message = convert.rs3(input_dir_path=os.path.join(input_dir, 'missing'))
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'no .rs3 files found')

    def test_rs3_success(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': 'PRG2-1C.rs3'}
        program_ran, outfile = convert.rs3(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(outfile), os.path.join(WD, 'measurements.txt'))
        meas_df = self.read('measurements')
        self.assertIn('sequence', meas_df.columns)
        # 13 alternating field steps, NRM to 90 mT, in A/m and specimen coordinates
        self.assertEqual(len(meas_df), 13)
        first, last = meas_df.iloc[0], meas_df.iloc[-1]
        self.assertIn('LT-NO', first['method_codes'])
        self.assertAlmostEqual(float(first['magn_volume']), 0.0005168)
        self.assertAlmostEqual(float(first['dir_dec']), 146.9)
        self.assertAlmostEqual(float(first['dir_inc']), 34.2)
        self.assertIn('LT-AF-Z', last['method_codes'])
        self.assertAlmostEqual(float(last['treat_ac_field']), 0.09)

    def test_rs3_thermal_steps(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': 'BO14-9-3.rs3'}
        program_ran, outfile = convert.rs3(**options)
        self.assertTrue(program_ran)
        meas_df = self.read('measurements')
        self.assertEqual(len(meas_df), 18)
        last = meas_df.iloc[-1]
        self.assertIn('LT-T-Z', last['method_codes'])
        self.assertAlmostEqual(float(last['treat_temp']), 663 + 273)

    def test_rs3_directory(self):
        # no mag_file: every .rs3 file in the input directory
        program_ran, outfile = convert.rs3(input_dir_path=self.input_dir, samp_con='2')
        self.assertTrue(program_ran)
        meas_df = self.read('measurements')
        self.assertEqual(sorted(meas_df['specimen'].unique()),
                         ['BO14-9-3', 'BO6-6-3', 'PRG1-6B', 'PRG2-1C', 'PRG6-2A', 'PRG7-8A'])
        site_df = self.read('sites')
        self.assertEqual(sorted(site_df.index), ['BO14', 'BO6', 'PRG1', 'PRG2', 'PRG6', 'PRG7'])

    def test_rs3_repeated_step(self):
        # PRG7-8A has 16 rows, two of them at 30 mT
        options = {'input_dir_path': self.input_dir, 'mag_file': 'PRG7-8A.rs3'}
        program_ran, outfile = convert.rs3(**options)
        self.assertTrue(program_ran)
        meas_df = self.read('measurements')
        self.assertEqual(len(meas_df), 16)
        self.assertEqual(sum(abs(meas_df['treat_ac_field'].astype(float) - 0.03) < 1e-9), 2)
        # averaged on request
        program_ran, outfile = convert.rs3(noave=False, **options)
        self.assertTrue(program_ran)
        meas_df = self.read('measurements')
        self.assertEqual(len(meas_df), 15)
        averaged = meas_df[abs(meas_df['treat_ac_field'].astype(float) - 0.03) < 1e-9]
        self.assertEqual(len(averaged), 1)
        self.assertIn('DE-VM', averaged.iloc[0]['method_codes'])
        self.assertIn('magn_volume', meas_df.columns)
        self.assertNotIn('magn_moment', meas_df.columns)
        # the fit from 30 to 90 mT has six rows in the file and five averaged steps
        self.assertEqual(self.raw('specimens')['dir_n_measurements'].iloc[0], '5')

    def test_rs3_mixed_treatments(self):
        """
        PRG6-2A: one heating to 480 C, then alternating field steps from 0 mT.
        Each row keeps its own treatment, and the experiment has both protocols.
        """
        options = {'input_dir_path': self.input_dir, 'mag_file': 'PRG6-2A.rs3'}
        program_ran, outfile = convert.rs3(**options)
        self.assertTrue(program_ran)
        meas_df = self.raw('measurements')
        self.assertEqual(set(meas_df['experiment']), {'PRG6-2A_LP-DIR-T_LP-DIR-AF'})
        self.assertEqual(meas_df['method_codes'].iloc[0], 'LT-T-Z:LP-DIR-T:LP-DIR-AF')
        self.assertAlmostEqual(float(meas_df['treat_temp'].iloc[0]), 480 + 273)
        # the 0 mT step after the heating is an AF step, not an untreated NRM
        self.assertEqual(meas_df['method_codes'].iloc[1], 'LT-AF-Z:LP-DIR-T:LP-DIR-AF')
        self.assertAlmostEqual(float(meas_df['treat_ac_field'].iloc[1]), 0)
        self.assertEqual(set(meas_df['method_codes'].iloc[1:]), {'LT-AF-Z:LP-DIR-T:LP-DIR-AF'})
        self.assertEqual(list(meas_df['measurement'][:2]),
                         ['PRG6-2A_LP-DIR-T_LP-DIR-AF-1', 'PRG6-2A_LP-DIR-T_LP-DIR-AF-2'])
        self.assertEqual(list(meas_df['treat_step_num']), [str(k) for k in range(1, len(meas_df) + 1)])
        self.assertEqual(meas_df['measurement'].nunique(), len(meas_df))
        # the fit is over alternating field steps; the specimen names its experiment
        spec_df = self.raw('specimens')
        self.assertEqual(set(spec_df['experiments']), {'PRG6-2A_LP-DIR-T_LP-DIR-AF'})
        self.assertEqual(self.fit('PRG6-2A', 'CA', 0)['method_codes'], 'DE-BFL-A:LP-DIR-AF:DA-DIR-GEO')

    def test_rs3_specimens_without_fits(self):
        # the record of a specimen without stored fits names its experiment and protocol
        program_ran, outfile = convert.rs3(input_dir_path=self.input_dir)
        self.assertTrue(program_ran)
        spec_df = self.raw('specimens')
        row = spec_df[spec_df['specimen'] == 'BO14-9-3'].iloc[0]
        self.assertEqual(row['method_codes'], 'LP-DIR-T')
        self.assertEqual(row['experiments'], 'BO14-9-3_LP-DIR-T')
        # also with interpretations=False: every record has its method codes
        program_ran, outfile = convert.rs3(input_dir_path=self.input_dir, interpretations=False)
        self.assertTrue(program_ran)
        spec_df = self.raw('specimens')
        self.assertFalse(spec_df['method_codes'].isnull().any())
        self.assertEqual(spec_df.set_index('specimen').loc['PRG2-1C', 'method_codes'], 'LP-DIR-AF')

    def test_rs3_whole_numbers(self):
        # integer columns are written without a decimal point, also when some
        # records (here of BO14-9-3, which has no stored fits) leave them empty
        program_ran, outfile = convert.rs3(input_dir_path=self.input_dir)
        self.assertTrue(program_ran)
        spec_df = self.raw('specimens')
        rows = spec_df[spec_df['specimen'] == 'PRG2-1C']
        self.assertEqual(sorted(set(rows['dir_n_measurements'])), ['11', '3'])
        self.assertEqual(sorted(set(spec_df['dir_tilt_correction'].dropna())), ['-1', '0'])
        self.assertTrue(spec_df['dir_tilt_correction'].isnull().any())

    def test_rs3_naming_convention_7(self):
        # 7-Z is convention 7 (site = first Z characters), not convention 4
        program_ran, outfile = convert.rs3(input_dir_path=self.input_dir, mag_file='BO14-9-3.rs3',
                                           samp_con='7-4')
        self.assertTrue(program_ran)
        self.assertEqual(self.read('samples').loc['BO14-9-3', 'site'], 'BO14')

    def test_rs3_utf8(self):
        """
        a file saved again as UTF-8: the degree sign of the thermal limits takes
        two bytes, and the result is the same as for the file as written
        """
        import shutil
        import tempfile
        program_ran, outfile = convert.rs3(input_dir_path=self.input_dir, mag_file='PRG1-6B.rs3')
        self.assertTrue(program_ran)
        expected = self.raw('specimens')
        with open(os.path.join(self.input_dir, 'PRG1-6B.rs3'), encoding='latin-1') as f:
            text = f.read()
        self.assertIn('\xb0C', text)
        tmp_dir = tempfile.mkdtemp()
        try:
            with open(os.path.join(tmp_dir, 'PRG1-6B.rs3'), 'w', encoding='utf-8', newline='') as f:
                f.write(text)
            program_ran, outfile = convert.rs3(input_dir_path=tmp_dir, dir_path=WD)
            self.assertTrue(program_ran)
            self.assertTrue(self.raw('specimens').equals(expected))
        finally:
            shutil.rmtree(tmp_dir)

    def test_rs3_fiducial_at_3_oclock(self):
        """
        P1 = 3: a copy of PRG2-1C with the fiducial mark at 3 o'clock, its
        declinations in specimen coordinates 90 degrees smaller. They are
        rotated back to the 12 o'clock line, which the descriptions say.
        """
        with open(os.path.join(self.input_dir, 'PRG2-1C.rs3'), encoding='latin-1') as f:
            lines = f.read().splitlines()
        self.assertIn('12 90 12 90', lines[1])
        changed = lines[:1] + [lines[1].replace('12 90 12 90', '3  90 12 90'), lines[2]]
        for line in lines[3:]:
            dsp = float(line[27:33])
            changed.append(line[:27] + '%6.1f' % ((dsp - 90) % 360) + line[33:])
        with open(os.path.join(WD, 'fiducial_3.rs3'), 'w', encoding='latin-1') as f:
            f.write('\n'.join(changed) + '\n')
        program_ran, outfile = convert.rs3(mag_file='fiducial_3.rs3', input_dir_path=WD)
        self.assertTrue(program_ran)
        meas_df = self.raw('measurements')
        self.assertAlmostEqual(float(meas_df['dir_dec'].iloc[0]), 146.9)
        self.assertTrue(all('P1 = 3' in d for d in meas_df['description']))
        self.assertIn('P1 = 3', self.fit('PRG2-1C', 'CA', -1)['description'])
        self.assertAlmostEqual(float(self.fit('PRG2-1C', 'CA', -1)['dir_dec']), 153.7)
        self.assertTrue(self.raw('specimens').query("dir_tilt_correction == '0'")['description'].isnull().all())

    def test_rs3_orientation(self):
        """
        both settings of the AGICO parameter P2: the header orientation in the
        MagIC convention, and the rotation to the geographic direction in the file
        """
        program_ran, outfile = convert.rs3(input_dir_path=self.input_dir)
        self.assertTrue(program_ran)
        samp_df = self.read('samples')
        meas_df = self.read('measurements')
        # specimen: (SDec, SInc, P2), first step in specimen and geographic coordinates
        expected = {'PRG2-1C': ((288, 5, 90), (146.9, 34.2), (330.1, 47.7)),
                    'BO14-9-3': ((337, 57, 0), (133.1, 52.5), (22.4, 51.3))}
        for specimen, ((sdec, sinc, P2), spec_dir, geo_dir) in expected.items():
            azimuth = float(samp_df.loc[specimen, 'azimuth'])
            dip = float(samp_df.loc[specimen, 'dip'])
            self.assertAlmostEqual(azimuth, sdec)
            self.assertAlmostEqual(dip, sinc - 90 if P2 == 90 else -sinc)
            first = meas_df[meas_df['specimen'] == specimen].iloc[0]
            self.assertAlmostEqual(float(first['dir_dec']), spec_dir[0])
            self.assertAlmostEqual(float(first['dir_inc']), spec_dir[1])
            dec, inc = pmag.dogeo(spec_dir[0], spec_dir[1], azimuth, dip)
            self.assertLess(pmag.angle([dec, inc], list(geo_dir))[0], 0.1)

    def test_rs3_agico_orientation(self):
        """
        P1-P4 = 6 0 6 0: the fiducial mark and the measured azimuth at 6 o'clock,
        SInc the dip of the frontal side. Header and first three steps of
        JR109/1A, one of the example files distributed with Remasoft.
        """
        lines = [
            "Name      Site      Latitude  Longitude  Height    Rock           Age  Fm SDec  SInc  BDec  BInc  FDec  FInc  P1 P2 P3 P4 Note",
            "JR109/1A                                                                  180   50                            6  0  6  0      ",
            "ID Step[\xb0C]         M[A/m]   Dsp   Isp   Dge   Ige   Dtc   Itc   Dfc   Ifc   Prec    K[e-06 SI] Limit1    Limit2    Note      ",
            "N  0               35.07492 184.4 -22.1  13.1 -71.7                           1.0",
            "T  80              35.59368 183.7 -23.0  11.4 -72.7                           1.0",
            "T  120             35.67982 183.5 -22.9  10.8 -72.7                           1.0"]
        with open(os.path.join(WD, 'agico_6_0_6_0.rs3'), 'w', encoding='latin-1') as f:
            f.write('\n'.join(lines) + '\n')
        program_ran, outfile = convert.rs3(mag_file='agico_6_0_6_0.rs3', input_dir_path=WD)
        self.assertTrue(program_ran)
        samp_df = self.read('samples')
        azimuth, dip = float(samp_df.loc['JR109/1A', 'azimuth']), float(samp_df.loc['JR109/1A', 'dip'])
        self.assertAlmostEqual(azimuth, 180)
        self.assertAlmostEqual(dip, 50)
        meas_df = self.read('measurements')
        self.assertEqual(len(meas_df), 3)
        # specimen coordinates as in the file; geographic direction of the file recovered
        first = meas_df.iloc[0]
        self.assertAlmostEqual(float(first['dir_dec']), 184.4)
        self.assertAlmostEqual(float(first['dir_inc']), -22.1)
        dec, inc = pmag.dogeo(float(first['dir_dec']), float(first['dir_inc']), azimuth, dip)
        self.assertLess(pmag.angle([dec, inc], [13.1, -71.7])[0], 0.1)

    def test_rs3_orientation_mismatch(self):
        # with P2 changed in the header, the geographic directions in the file no longer follow
        with open(os.path.join(self.input_dir, 'PRG2-1C.rs3'), encoding='latin-1') as f:
            text = f.read()
        self.assertIn('12 90 12 90', text)
        with open(os.path.join(WD, 'changed_P2.rs3'), 'w', encoding='latin-1') as f:
            f.write(text.replace('12 90 12 90', '12 0  12 90'))
        program_ran, error_message = convert.rs3(mag_file='changed_P2.rs3', input_dir_path=WD)
        self.assertFalse(program_ran)
        self.assertIn('geographic directions', error_message)
        self.assertFalse(os.path.exists(os.path.join(WD, 'measurements.txt')))

    def test_rs3_interpretations(self):
        program_ran, outfile = convert.rs3(input_dir_path=self.input_dir)
        self.assertTrue(program_ran)
        spec_df = self.read('specimens')
        # a specimen without stored fits has one record
        self.assertEqual(len(spec_df[spec_df['specimen'] == 'BO14-9-3']), 1)
        # anchored line, 8 to 90 mT
        geo = self.fit('PRG2-1C', 'CA', 0)
        self.assertEqual(geo['method_codes'], 'DE-BFL-A:LP-DIR-AF:DA-DIR-GEO')
        self.assertAlmostEqual(float(geo['dir_dec']), 321.7)
        self.assertAlmostEqual(float(geo['dir_inc']), 50.1)
        self.assertAlmostEqual(float(geo['dir_mad_anc']), 2.7)
        self.assertAlmostEqual(float(geo['meas_step_min']), 0.008)
        self.assertAlmostEqual(float(geo['meas_step_max']), 0.09)
        self.assertEqual(geo['meas_step_unit'], 'T')
        self.assertEqual(int(float(geo['dir_n_measurements'])), 11)
        spec = self.fit('PRG2-1C', 'CA', -1)
        self.assertEqual(spec['method_codes'], 'DE-BFL-A:LP-DIR-AF:DA-DIR')
        self.assertAlmostEqual(float(spec['dir_dec']), 153.7)
        self.assertAlmostEqual(float(spec['dir_inc']), 36.8)
        # free line from the NRM to 8 mT
        geo = self.fit('PRG2-1C', 'CB', 0)
        self.assertEqual(geo['method_codes'], 'DE-BFL:LP-DIR-AF:DA-DIR-GEO')
        self.assertAlmostEqual(float(geo['dir_mad_free']), 0.4)
        self.assertAlmostEqual(float(geo['meas_step_min']), 0)
        self.assertAlmostEqual(float(geo['meas_step_max']), 0.008)
        self.assertEqual(int(float(geo['dir_n_measurements'])), 3)
        # thermal limits in kelvin
        geo = self.fit('PRG1-6B', 'CA1', 0)
        self.assertEqual(geo['method_codes'], 'DE-BFL-A:LP-DIR-T:DA-DIR-GEO')
        self.assertAlmostEqual(float(geo['meas_step_min']), 300 + 273)
        self.assertAlmostEqual(float(geo['meas_step_max']), 580 + 273)
        self.assertEqual(geo['meas_step_unit'], 'K')
        self.assertEqual(int(float(geo['dir_n_measurements'])), 8)
        # great circle: the pole of the plane; component names can hold spaces
        geo = self.fit('BO6-6-3', 'GW', 0)
        self.assertEqual(geo['method_codes'], 'DE-BFP:LP-DIR-AF:DA-DIR-GEO')
        self.assertAlmostEqual(float(geo['dir_dec']), 339.7)
        self.assertAlmostEqual(float(geo['dir_inc']), -28.2)
        self.assertAlmostEqual(float(geo['dir_mad_free']), 10.0)
        self.fit('BO6-6-3', 'C2 sinor', 0)

    def test_rs3_copies_of_a_specimen(self):
        import shutil
        import tempfile
        with open(os.path.join(self.input_dir, 'BO6-6-3.rs3'), encoding='latin-1') as f:
            lines = f.read().splitlines()
        without_fits = [line for line in lines if line[:2].strip() not in ('C', 'G')]
        self.assertEqual(len(lines) - len(without_fits), 5)
        tmp_dir = tempfile.mkdtemp()
        try:
            shutil.copy(os.path.join(self.input_dir, 'BO6-6-3.rs3'), tmp_dir)
            # a copy without the stored fits, read first: the fits of the other file are kept
            with open(os.path.join(tmp_dir, 'BO6-6-3 (2).rs3'), 'w', encoding='latin-1') as f:
                f.write('\n'.join(without_fits) + '\n')
            program_ran, outfile = convert.rs3(input_dir_path=tmp_dir, dir_path=WD)
            self.assertTrue(program_ran)
            self.assertEqual(len(self.read('measurements')), 18)
            spec_df = self.read('specimens')
            self.assertEqual(spec_df['dir_comp'].nunique(), 5)
            # a copy with a different measurement: the conversion stops
            changed = list(without_fits)
            changed[3] = changed[3][:27] + ' 111.1' + changed[3][33:]
            with open(os.path.join(tmp_dir, 'BO6-6-3 (2).rs3'), 'w', encoding='latin-1') as f:
                f.write('\n'.join(changed) + '\n')
            program_ran, error_message = convert.rs3(input_dir_path=tmp_dir, dir_path=WD)
            self.assertFalse(program_ran)
            self.assertIn('both hold specimen BO6-6-3', error_message)
        finally:
            shutil.rmtree(tmp_dir)

    def test_rs3_without_interpretations(self):
        program_ran, outfile = convert.rs3(input_dir_path=self.input_dir, interpretations=False)
        self.assertTrue(program_ran)
        spec_df = self.read('specimens')
        self.assertEqual(len(spec_df), 6)
        self.assertNotIn('dir_comp', spec_df.columns)

    def test_rs3_options(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': ['PRG1-6B.rs3', 'PRG2-1C.rs3']}
        options['lat'], options['lon'] = 5, 10
        options['specnum'] = 1
        options['samp_con'] = '2'
        options['location'] = 'place'
        options['meth_code'] = 'SO-MAG'
        options['instrument'] = 'instrument'
        options['meas_file'] = 'custom_meas.txt'
        program_ran, outfile = convert.rs3(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(outfile), os.path.join(WD, 'custom_meas.txt'))
        loc_df = self.read('locations')
        self.assertEqual(loc_df.index.values[0], 'place')
        samp_df = self.read('samples')
        self.assertEqual(sorted(samp_df.index), ['PRG1-6', 'PRG2-1'])
        self.assertEqual(samp_df.loc['PRG1-6', 'site'], 'PRG1')
        self.assertEqual(samp_df.loc['PRG1-6', 'method_codes'], 'SO-MAG')
        site_df = self.read('sites')
        self.assertAlmostEqual(float(site_df.loc['PRG1', 'lat']), 5)
        self.assertAlmostEqual(float(site_df.loc['PRG1', 'lon']), 10)
        meas_df = cb.MagicDataFrame(os.path.join(WD, 'custom_meas.txt')).df
        self.assertEqual(set(meas_df['instrument_codes']), {'instrument'})
