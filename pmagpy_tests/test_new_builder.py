#!/usr/bin/env python

import unittest
import os
import wx
import sys
from pmagpy import new_builder as nb
from pmagpy import check_updates
WD = os.path.join(check_updates.get_pmag_dir(), '3_0', 'Osler')


class TestMagicDataFrame(unittest.TestCase):

    def setUp(self):

        pass

    def tearDown(self):
        pass

    def test_init_blank(self):
        magic_df = nb.MagicDataFrame()
        self.assertFalse(magic_df.df)

    def test_init_with_dtype(self):
        magic_df = nb.MagicDataFrame(dtype='specimens')
        self.assertEqual('specimens', magic_df.dtype)
        print magic_df.df.columns

    def test_init_with_file(self):
        magic_df = nb.MagicDataFrame(os.path.join(WD, 'sites.txt'))
        self.assertEqual('sites', magic_df.dtype)
        self.assertEqual('1', magic_df.df.index[1])

    def test_update_row(self):
        magic_df = nb.MagicDataFrame(os.path.join(WD, 'sites.txt'))
        self.assertEqual('Lava Flow', magic_df.df.iloc[3]['geologic_types'])
        magic_df.update_row(3, {'geologic_types': 'other type', 'new_col': 'new_val'})
        self.assertEqual('other type', magic_df.df.iloc[3]['geologic_types'])
        self.assertIn('new_col', magic_df.df.columns)
        self.assertEqual('new_val', magic_df.df.iloc[3]['new_col'])



if __name__ == '__main__':
    unittest.main()
