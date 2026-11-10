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
