#!/usr/bin/env python

import unittest
import os
import wx
import sys
from pmagpy import new_builder as nb
from pmagpy import check_updates
from pmagpy import data_model3 as data_model
from pmagpy import controlled_vocabularies3 as cv
pmag_dir = check_updates.get_pmag_dir()
WD = os.path.join(pmag_dir, '3_0', 'Osler')
vocab = cv.Vocabulary()
vocabulary, possible_vocabulary = vocab.get_controlled_vocabularies()
dmodel = data_model.DataModel()


class TestMagicDataFrame(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        os.chdir(pmag_dir)


    def test_init_blank(self):
        magic_df = nb.MagicDataFrame()
        self.assertFalse(magic_df.df)

    def test_init_with_dtype(self):
        magic_df = nb.MagicDataFrame(dtype='specimens',
                                     dmodel=dmodel)
        self.assertEqual('specimens', magic_df.dtype)

    def test_init_with_file(self):
        magic_df = nb.MagicDataFrame(os.path.join(WD, 'sites.txt'),
                                     dmodel=dmodel)
        self.assertEqual('sites', magic_df.dtype)
        self.assertEqual('1', magic_df.df.index[1])

    def test_update_row(self):
        magic_df = nb.MagicDataFrame(os.path.join(WD, 'sites.txt'), dmodel=dmodel)
        self.assertEqual('Lava Flow', magic_df.df.iloc[3]['geologic_types'])
        magic_df.update_row(3, {'geologic_types': 'other type', 'new_col': 'new_val'})
        self.assertEqual('other type', magic_df.df.iloc[3]['geologic_types'])
        self.assertIn('new_col', magic_df.df.columns)
        self.assertEqual('new_val', magic_df.df.iloc[3]['new_col'])


    def test_add_row(self):
        magic_df = nb.MagicDataFrame(os.path.join(WD, 'sites.txt'), dmodel=dmodel)
        old_len = len(magic_df.df)
        magic_df.add_row('new_site', {'new_col': 'new_val'})
        self.assertEqual('new_val', magic_df.df.iloc[-1]['new_col'])
        self.assertEqual(old_len + 1, len(magic_df.df))


    def test_add_blank_row(self):
        magic_df = nb.MagicDataFrame(os.path.join(WD, 'sites.txt'), dmodel=dmodel)
        old_len = len(magic_df.df)
        magic_df.add_blank_row('blank_site')
        self.assertIn('blank_site', magic_df.df.index)
        self.assertEqual(old_len + 1, len(magic_df.df))


    def test_delete_row(self):
        magic_df = nb.MagicDataFrame(os.path.join(WD, 'sites.txt'), dmodel=dmodel)
        old_len = len(magic_df.df)
        magic_df.delete_row(5)
        self.assertEqual(old_len - 1, len(magic_df.df))
        self.assertEqual('3', magic_df.df.iloc[5].name)


    def test_delete_rows(self):
        magic_df = nb.MagicDataFrame(os.path.join(WD, 'sites.txt'), dmodel=dmodel)
        cond = magic_df.df['description'].str.contains('VGP').astype(bool)
        # delete all rows that aren't described as VGPs
        magic_df.delete_rows(cond)
        for descr in magic_df.df['description'].values:
            self.assertTrue('VGP' in descr)

class TestContribution(unittest.TestCase):

    def setUp(self):
        directory = os.path.join(check_updates.get_pmag_dir(),
                                 '3_0', 'Megiddo')
        self.con = nb.Contribution(directory, vocabulary=vocabulary,
                                   dmodel=dmodel)

    def tearDown(self):
        os.chdir(pmag_dir)

    def test_init_empty(self):
        con = nb.Contribution(pmag_dir, dmodel=dmodel)
        self.assertEqual(0, len(con.tables))

    def test_init(self):
        self.assertEqual(type(self.con), nb.Contribution)
        self.assertEqual(set(self.con.tables),
                         set(['measurements', 'specimens', 'samples',
                              'sites', 'locations', 'ages', 'criteria',
                              'contribution']))


if __name__ == '__main__':
    unittest.main()
