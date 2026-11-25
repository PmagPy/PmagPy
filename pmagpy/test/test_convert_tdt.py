"""
Tests for convert.tdt, the converter of ThellierTool .tdt files, added with
the fix for headers with empty fields, and for pmag.sortarai on the converted
measurements.
"""
import os
import unittest

from pmagpy import pmag
from pmagpy import contribution_builder as cb
from pmagpy import convert_2_magic as convert

# the root of the repository, which holds data_files and is where the output
# of the converters is written and removed again
WD = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))


class TestTdtHeaderAndArai(unittest.TestCase):
    """
    ThellierTool .tdt files with empty header fields, and pmag.sortarai on a
    measurements table whose first magnitude column is empty for the specimen.
    """

    def setUp(self):
        os.chdir(WD)
        self.input_dir = os.path.join(WD, 'data_files',
                                      'convert_2_magic', 'tdt_magic')

    def tearDown(self):
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt', 'custom.out']
        pmag.remove_files(filelist, WD)
        pmag.remove_files(filelist, '.')
        pmag.remove_files(filelist, os.path.join(WD, 'data_files'))
        pmag.remove_files(filelist, self.input_dir)
        os.chdir(WD)

    def test_arai_with_an_empty_magnitude_column(self):
        """
        pmag.sortarai on measurements that also have a magnitude column without
        values for the specimen, as in a table that holds several experiments
        """
        import numpy as np
        import pandas as pd
        res, outfile = convert.tdt(self.input_dir)
        self.assertTrue(res)
        df = cb.MagicDataFrame(outfile).df
        specimen = df['specimen'].values[0]
        df = df[df['specimen'] == specimen]
        araiblock, field = pmag.sortarai(df, specimen, 0, version=3)
        first_Z = araiblock[0]
        self.assertFalse(np.isnan(first_Z[0][3]))
        # the moments in magn_volume, and magn_moment (the first magnitude column
        # sortarai looks at) empty for the specimen, as NaN or as None
        for empty in (np.nan, None):
            with_empty = df.rename(columns={'magn_moment': 'magn_volume'})
            with_empty.insert(0, 'magn_moment', pd.Series([empty] * len(with_empty), dtype=object,
                                                          index=with_empty.index))
            araiblock_2, field_2 = pmag.sortarai(with_empty, specimen, 0, version=3)
            self.assertEqual(field, field_2)
            self.assertEqual([row[3] for row in araiblock_2[0]], [row[3] for row in first_Z])

    def test_blank_lines_and_step_labels(self):
        """
        a line of tabs inside the data is skipped, not taken as the end of the
        file; a step label that is not a ThellierTool code stops with a message
        """
        import shutil
        import tempfile
        with open(os.path.join(self.input_dir, 'Krasa_MGH1.tdt')) as f:
            lines = f.read().splitlines()
        tmp_dir = tempfile.mkdtemp()
        try:
            shutil.copy(os.path.join(self.input_dir, 'Krasa_MGH1.tdt'), tmp_dir)
            res, outfile = convert.tdt(tmp_dir)
            self.assertTrue(res)
            expected = cb.MagicDataFrame(os.path.join(tmp_dir, 'measurements.txt')).df
            os.remove(os.path.join(tmp_dir, 'Krasa_MGH1.tdt'))
            changed = lines[:6] + ['\t\t\t\t', ''] + lines[6:]
            with open(os.path.join(tmp_dir, 'blank.tdt'), 'w') as f:
                f.write('\n'.join(changed) + '\n')
            res, outfile = convert.tdt(tmp_dir)
            self.assertTrue(res)
            df = cb.MagicDataFrame(os.path.join(tmp_dir, 'measurements.txt')).df
            self.assertEqual(len(df), len(expected))
            self.assertEqual(list(df['method_codes']), list(expected['method_codes']))
            # a step written as in a measurement session (125C) rather than as a treatment code
            fields = lines[4].split()
            changed = lines[:4] + ['\t'.join(fields[:1] + ['125C'] + fields[2:])] + lines[5:]
            with open(os.path.join(tmp_dir, 'blank.tdt'), 'w') as f:
                f.write('\n'.join(changed) + '\n')
            res, message = convert.tdt(tmp_dir)
            self.assertFalse(res)
            self.assertIn('treatment code', message)
            self.assertIn('125C', message)
        finally:
            shutil.rmtree(tmp_dir)

    def test_header_with_empty_fields(self):
        """
        files as exported from a spreadsheet: an empty line before the title,
        an empty field in the header line, and an empty column in the data rows
        """
        import shutil
        import tempfile
        with open(os.path.join(self.input_dir, 'Krasa_MGH1.tdt')) as f:
            lines = f.read().splitlines()
        header = lines[1].split()
        self.assertEqual(len(header), 5)
        tmp_dir = tempfile.mkdtemp()
        try:
            # the file as it is, converted on its own
            shutil.copy(os.path.join(self.input_dir, 'Krasa_MGH1.tdt'), tmp_dir)
            res, outfile = convert.tdt(tmp_dir)
            self.assertTrue(res)
            expected = cb.MagicDataFrame(os.path.join(tmp_dir, 'measurements.txt')).df
            os.remove(os.path.join(tmp_dir, 'Krasa_MGH1.tdt'))
            changed = ['', lines[0], '\t'.join([header[0], ''] + header[2:])]
            for line in lines[2:]:
                fields = line.split()
                changed.append('\t'.join(fields[:1] + [''] + fields[1:]) if len(fields) >= 5 else line)
            with open(os.path.join(tmp_dir, 'renamed.tdt'), 'w') as f:
                f.write('\n'.join(changed) + '\n')
            res, outfile = convert.tdt(tmp_dir)
            self.assertTrue(res)
            df = cb.MagicDataFrame(os.path.join(tmp_dir, 'measurements.txt')).df
            self.assertEqual(len(df), len(expected))
            self.assertEqual(list(df['method_codes']), list(expected['method_codes']))
            self.assertEqual(list(df['treat_dc_field']), list(expected['treat_dc_field']))
            # the specimen named after the file
            res, outfile = convert.tdt(tmp_dir, spec_name_con=2)
            self.assertTrue(res)
            df = cb.MagicDataFrame(os.path.join(tmp_dir, 'measurements.txt')).df
            self.assertEqual(set(df['specimen']), {'renamed'})
            # a header line that does not start with the lab field
            changed[2] = '\t'.join(['field', ''] + header[2:])
            with open(os.path.join(tmp_dir, 'renamed.tdt'), 'w') as f:
                f.write('\n'.join(changed) + '\n')
            res, message = convert.tdt(tmp_dir)
            self.assertFalse(res)
            self.assertIn('lab field', message)
        finally:
            shutil.rmtree(tmp_dir)


class TestTdtGarrotxa(unittest.TestCase):
    """
    Two files of Vernet et al. (2026), La Garrotxa: the extension .TDT, a
    specimen name with a space, moments in A/m, and the published Arai fits
    (Table III of the paper) recalculated from the converted measurements.
    """

    def setUp(self):
        import tempfile
        self.input_dir = os.path.join(WD, 'data_files', 'convert_2_magic', 'tdt_magic', 'garrotxa')
        self.out_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.out_dir)
        os.chdir(WD)

    def convert(self, **kwargs):
        res, outfile = convert.tdt(self.input_dir, output_dir_path=self.out_dir, lab_dec=0, lab_inc=-90,
                                   **kwargs)
        self.assertTrue(res, outfile)
        return cb.MagicDataFrame(outfile).df

    def file_rows(self, name):
        with open(os.path.join(self.input_dir, name), encoding='latin-1') as f:
            return [line for line in f.read().splitlines()[2:] if line.strip()]

    def test_files_with_the_extension_in_capitals(self):
        """both .TDT files are read, each specimen named after its file"""
        df = self.convert(spec_name_con=2)
        self.assertEqual(sorted(df['specimen'].unique()), ['GTX0206B1', 'LTD_GTX02061'])
        for name in ('GTX0206B1', 'LTD_GTX02061'):
            self.assertEqual((df['specimen'] == name).sum(), len(self.file_rows(name + '.TDT')))

    def test_specimen_name_with_a_space(self):
        """the name column "45. GTX02061" is one field, and the step, moment and direction follow it"""
        df = self.convert(spec_name_con=1)
        self.assertIn('45. GTX02061', set(df['specimen']))
        rows = df[df['specimen'] == '45. GTX02061']
        fields = self.file_rows('LTD_GTX02061.TDT')[3].split('\t')
        self.assertEqual(len(rows), len(self.file_rows('LTD_GTX02061.TDT')))
        self.assertAlmostEqual(float(rows['dir_dec'].iloc[3]), float(fields[3]))
        self.assertAlmostEqual(float(rows['dir_inc'].iloc[3]), float(fields[4]))
        self.assertEqual(float(rows['treat_temp'].iloc[3]), float(fields[1].split('.')[0]) + 273)
        self.assertIn('LT-T-I', rows['method_codes'].iloc[2])

    def test_moments_in_a_per_m(self):
        """moment_units="A/m": the values go to magn_volume unchanged, and no volume is assumed"""
        df = self.convert(spec_name_con=2, moment_units='A/m')
        rows = df[df['specimen'] == 'GTX0206B1']
        self.assertTrue('magn_moment' not in df.columns or df['magn_moment'].isna().all())
        values = [float(line.split('\t')[2]) for line in self.file_rows('GTX0206B1.TDT')]
        self.assertEqual([float(v) for v in rows['magn_volume']], values)
        specimens = cb.MagicDataFrame(os.path.join(self.out_dir, 'specimens.txt')).df
        self.assertTrue('volume' not in specimens.columns or specimens['volume'].isna().all())

    def test_published_arai_fits(self):
        """B, N, beta, f and q of Table III of the paper, from the converted measurements"""
        df = self.convert(spec_name_con=2, moment_units='A/m')
        published = {'GTX0206B1': (200, 540, 12, 30.10, 0.074, 0.71, 8.29),
                     'LTD_GTX02061': (200, 520, 11, 26.91, 0.037, 0.78, 17.61)}
        for specimen, (t_min, t_max, n, b, beta, f, q) in published.items():
            block = df[df['specimen'] == specimen]
            araiblock, field = pmag.sortarai(block, specimen, 0, version=3)
            zijdblock, _ = pmag.find_dmag_rec(specimen, block, version=3)
            self.assertAlmostEqual(field, 40e-6)
            temperatures = [step[0] - 273 for step in araiblock[0]]
            start, end = temperatures.index(t_min), temperatures.index(t_max)
            pars, _ = pmag.PintPars(block, araiblock, zijdblock, start, end, {}, version=3)
            self.assertEqual(pars['int_n_measurements'], n)
            self.assertAlmostEqual(abs(pars['int_b']) * field * 1e6, b, delta=0.01)
            self.assertAlmostEqual(pars['int_b_beta'], beta, delta=0.0005)
            self.assertAlmostEqual(pars['int_f'], f, delta=0.005)
            self.assertAlmostEqual(pars['int_q'], q, delta=0.005)


class TestTdtFieldWithTwoValues(unittest.TestCase):
    """
    BOA3A.tdt (Nawrocki, 2023, CC BY 4.0): tab-separated, and the moment field
    of some rows holds two values ("4.116564E-02 1"). Split on spaces the
    declination would be 1 and the inclination the declination, so the
    converter stops with a message naming the field.
    """

    def test_field_with_two_values_stops_the_conversion(self):
        import shutil
        import tempfile
        out = tempfile.mkdtemp()
        try:
            input_dir = tempfile.mkdtemp(dir=out)
            shutil.copy(os.path.join(WD, 'data_files', 'convert_2_magic', 'tdt_magic', 'nawrocki', 'BOA3A.tdt'),
                        input_dir)
            res, message = convert.tdt(input_dir, output_dir_path=out)
            self.assertFalse(res)
            self.assertIn('BOA3A.tdt: the moment field of this data row holds more than one value', message)
            self.assertIn("'4.116564E-02 1'", message)
            self.assertFalse(os.path.exists(os.path.join(out, 'measurements.txt')))
        finally:
            shutil.rmtree(out)


class TestTdtTailChecksOfMT4(unittest.TestCase):
    """
    BIE2A.tdt (Nawrocki, 2023, CC BY 4.0), the MT4 protocol of ThellierTool: each
    pTRM tail check (.13) follows an additivity check (.14) at a lower
    temperature rather than the in-field step at its own. The tail checks keep
    the code the converter gives them (pmag.measurements_methods3 used to tell
    them from the order of the steps and made them LT-T-Z).
    """

    def test_tail_checks_after_additivity_checks(self):
        import shutil
        import tempfile
        out = tempfile.mkdtemp()
        try:
            input_dir = tempfile.mkdtemp(dir=out)
            shutil.copy(os.path.join(WD, 'data_files', 'convert_2_magic', 'tdt_magic', 'nawrocki', 'BIE2A.tdt'),
                        input_dir)
            res, outfile = convert.tdt(input_dir, output_dir_path=out)
            self.assertTrue(res, outfile)
            df = cb.MagicDataFrame(outfile).df.reset_index(drop=True)
            first = df['method_codes'].str.split(':').str[0]
            tails = df[first == 'LT-PTRM-MD']
            self.assertEqual(sorted(tails['treat_temp'].astype(float) - 273), [200, 300, 400, 500, 600])
            self.assertEqual((first == 'LT-PTRM-AC').sum(), 5)
            for k in tails.index:
                self.assertTrue(df.loc[k - 1, 'method_codes'].startswith('LT-PTRM-AC'))
            self.assertTrue(df['experiment'].str.contains('LP-PI-BT-MD').all())
            # the Arai plot has the five tail checks, and the same zero-field steps as before
            araiblock, field = pmag.sortarai(df, df['specimen'].iloc[0], 0, version=3)
            self.assertEqual(len(araiblock[3]), 5)
            self.assertEqual(len(araiblock[0]), (first.isin(['LT-NO', 'LT-T-Z'])).sum())
        finally:
            shutil.rmtree(out)
