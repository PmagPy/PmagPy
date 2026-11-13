"""
Tests for convert.vftb, the converter of variable field translation balance
(VFTB) files: IRM acquisition, back-field, hysteresis and thermomagnetic
curves. The test files are in data_files/convert_2_magic/vftb_magic.
"""
import os
import unittest

from pmagpy import pmag
from pmagpy import contribution_builder as cb
from pmagpy import convert_2_magic as convert

# the root of the repository, which holds data_files and is where the output
# of the converters is written and removed again
WD = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))


class TestVftbMagic(unittest.TestCase):
    """
    VFTB files of one sample, one per kind of curve; the expected values are
    read off the files (see data_files/convert_2_magic/vftb_magic/README.md).
    """

    def setUp(self):
        os.chdir(WD)
        self.input_dir = os.path.join(WD, 'data_files', 'convert_2_magic', 'vftb_magic')
        self.filelist = ['measurements.txt', 'specimens.txt', 'samples.txt', 'sites.txt', 'locations.txt']

    def tearDown(self):
        pmag.remove_files(self.filelist, WD)
        pmag.remove_files(['PRG1-2.irm.tmp'], WD)
        os.chdir(WD)

    def convert(self, vftb_file, **kwargs):
        program_ran, outfile = convert.vftb(vftb_file, dir_path=WD, input_dir_path=self.input_dir,
                                            meas_outfile='measurements.txt', spec_outfile='specimens.txt',
                                            samp_outfile='samples.txt', site_outfile='sites.txt',
                                            loc_outfile='locations.txt', samp_con='2', location='place',
                                            **kwargs)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(outfile), os.path.join(WD, 'measurements.txt'))
        return cb.MagicDataFrame(os.path.join(WD, 'measurements.txt')).df

    def test_vftb_with_no_file(self):
        program_ran, error_message = convert.vftb('missing.irm', dir_path=WD, input_dir_path=self.input_dir)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'you must provide a valid vftb_file')

    def test_vftb_irm(self):
        df = self.convert('PRG1-2.irm')
        self.assertEqual(len(df), 13)
        self.assertEqual(set(df['method_codes']), {'LP-IRM'})
        self.assertEqual(set(df['experiment']), {'PRG1-2_LP-IRM'})
        self.assertEqual(set(df['specimen']), {'PRG1-2'})
        # fields in Oe to tesla; magnetization in emu/g (Am^2/kg)
        self.assertAlmostEqual(float(df.iloc[0]['treat_dc_field']), 0.2e-4)
        self.assertAlmostEqual(float(df.iloc[0]['magn_mass']), -1.908613566e-4)
        self.assertAlmostEqual(float(df.iloc[-1]['treat_dc_field']), 0.983)
        self.assertAlmostEqual(float(df.iloc[-1]['magn_mass']), 0.1098064644)
        self.assertAlmostEqual(float(df.iloc[0]['meas_temp']), 22 + 273)
        self.assertEqual(set(df['meas_field_dc'].astype(float)), {0})
        site_df = cb.MagicDataFrame(os.path.join(WD, 'sites.txt')).df
        self.assertEqual(list(site_df.index), ['PRG1'])
        # the weight in the first line of the file (503 mg), in kg
        spec_df = cb.MagicDataFrame(os.path.join(WD, 'specimens.txt')).df
        self.assertAlmostEqual(float(spec_df.loc['PRG1-2', 'weight']), 5.03e-4)
        self.assertEqual(spec_df.loc['PRG1-2', 'method_codes'], 'LP-IRM')

    def test_vftb_backfield(self):
        df = self.convert('PRG1-2.coe')
        self.assertEqual(len(df), 18)
        self.assertEqual(set(df['method_codes']), {'LP-IRM-DCD'})
        self.assertAlmostEqual(float(df.iloc[0]['treat_dc_field']), 0)
        self.assertAlmostEqual(float(df.iloc[0]['magn_mass']), 0.109407304)
        self.assertAlmostEqual(float(df.iloc[1]['treat_dc_field']), -55.2e-4)
        self.assertAlmostEqual(float(df.iloc[-1]['treat_dc_field']), -0.949)
        self.assertAlmostEqual(float(df.iloc[-1]['magn_mass']), -0.1055780866)

    def test_vftb_hysteresis(self):
        df = self.convert('PRG1-2.hys')
        self.assertEqual(len(df), 46)
        self.assertEqual(set(df['method_codes']), {'LP-HYS'})
        # the magnetization is measured in the field
        self.assertAlmostEqual(float(df.iloc[0]['meas_field_dc']), 9.82e-4)
        self.assertAlmostEqual(float(df.iloc[0]['magn_mass']), 0.1120269406)
        self.assertEqual(set(df['treat_dc_field'].astype(float)), {0})

    def test_vftb_thermomagnetic(self):
        df = self.convert('PRG1-2.rmp')
        self.assertEqual(len(df), 577)
        # heating to the highest temperature (709 C, the 290th of 577 rows), then cooling
        self.assertEqual(df.iloc[0]['method_codes'], 'LP-IMT:LP-MW')
        self.assertEqual(df.iloc[-1]['method_codes'], 'LP-IMT:LP-MC')
        self.assertAlmostEqual(float(df['treat_temp'].astype(float).max()), 709 + 273)
        self.assertEqual(int(df['treat_temp'].astype(float).values.argmax()), 289)
        self.assertAlmostEqual(float(df.iloc[0]['treat_dc_field']), 84e-4)
        self.assertAlmostEqual(float(df.iloc[0]['magn_mass']), 0.1803644476)

    def test_vftb_measurement_names(self):
        # every measurement has a name, from its experiment and step number
        df = self.convert('PRG1-2.irm')
        self.assertEqual(df['measurement'].iloc[0], 'PRG1-2_LP-IRM-1')
        self.assertEqual(df['measurement'].iloc[-1], 'PRG1-2_LP-IRM-13')
        self.assertEqual(df['measurement'].nunique(), len(df))

    def test_vftb_fields_without_residue(self):
        # -55.2 Oe is written as -0.00552 T (the file as the converter writes it;
        # self.convert reads it with MagicDataFrame, which writes it again)
        import pandas as pd
        program_ran, outfile = convert.vftb('PRG1-2.coe', dir_path=WD, input_dir_path=self.input_dir,
                                            meas_outfile='measurements.txt', spec_outfile='specimens.txt',
                                            samp_outfile='samples.txt', site_outfile='sites.txt',
                                            loc_outfile='locations.txt', samp_con='2')
        self.assertTrue(program_ran)
        raw = pd.read_csv(outfile, sep='\t', header=1, dtype=str)
        self.assertEqual(raw['treat_dc_field'].iloc[1], '-0.00552')

    def test_vftb_units(self):
        """
        the units of the column names are used; without column names, units
        decides the field unit, and temperatures are in kelvin either way
        """
        import shutil
        import tempfile
        with open(os.path.join(self.input_dir, 'PRG1-2.irm'), encoding='latin-1') as f:
            lines = f.read().splitlines()
        self.assertTrue(lines[3].startswith(' field / Oe'))
        tmp_dir = tempfile.mkdtemp()
        try:
            def convert_copy(lines, **kwargs):
                with open(os.path.join(tmp_dir, 'PRG1-2.irm'), 'w', encoding='latin-1') as f:
                    f.write('\n'.join(lines) + '\n')
                self.input_dir = tmp_dir
                return self.convert('PRG1-2.irm', **kwargs)
            # field in mT in the column names; units is not used
            df = convert_copy(lines[:3] + [lines[3].replace('field / Oe', 'field / mT')] + lines[4:],
                              units='SI')
            self.assertAlmostEqual(float(df.iloc[-1]['treat_dc_field']), 9.830)
            # no column names: the field in tesla with units='SI', in Oe otherwise
            df = convert_copy(lines[:3] + lines[4:], units='SI')
            self.assertAlmostEqual(float(df.iloc[-1]['treat_dc_field']), 9830)
            self.assertAlmostEqual(float(df.iloc[0]['meas_temp']), 22 + 273)
            df = convert_copy(lines[:3] + lines[4:])
            self.assertAlmostEqual(float(df.iloc[-1]['treat_dc_field']), 0.983)
        finally:
            shutil.rmtree(tmp_dir)

    def test_vftb_experiment_type(self):
        # the kind of curve given, not taken from the extension
        df = self.convert('PRG1-2.coe', experiment_type='irm')
        self.assertEqual(set(df['method_codes']), {'LP-IRM'})
        program_ran, error_message = convert.vftb('PRG1-2.coe', dir_path=WD, input_dir_path=self.input_dir,
                                                  experiment_type='other')
        self.assertFalse(program_ran)
        self.assertIn('experiment_type must be one of', error_message)
