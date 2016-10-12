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

    def test_update_record(self):
        magic_df = nb.MagicDataFrame(os.path.join(WD, 'sites.txt'), dmodel=dmodel)
        print magic_df.df.index
        cond = magic_df.df['lithologies'] == 'Basalt'
        print magic_df.df.loc['2'][['lithologies', 'description']]
        magic_df.update_record('2', new_data={'description': 'updated'}, condition=cond)
        print magic_df.df.loc['2'][['lithologies', 'description']]
        self.assertIn('updated', magic_df.df.loc['2', 'description'].values)

    def test_convert_to_pmag_data_list(self):
        magic_df = nb.MagicDataFrame(os.path.join(WD, 'sites.txt'), dmodel=dmodel)
        lst = magic_df.convert_to_pmag_data_list('lst')
        self.assertEqual(list, type(lst))
        self.assertEqual(dict, type(lst[0]))
        self.assertEqual('1', str(lst[0]['site']))
        #
        dct = magic_df.convert_to_pmag_data_list("dict")
        self.assertEqual(dict, type(dct))
        self.assertEqual(dict, type(dct[dct.keys()[0]]))
        self.assertEqual('1', str(dct['1']['site']))

    def test_get_name(self):
        magic_df = nb.MagicDataFrame(os.path.join(WD, 'sites.txt'), dmodel=dmodel)
        val = magic_df.get_name('description')
        self.assertEqual('VGP:Site 1', val)
        df_slice = magic_df.df.iloc[10:20]
        val = magic_df.get_name('description', df_slice)
        self.assertEqual('VGP:Site 4', val)
        index_names = ['21', '22']
        val = magic_df.get_name('description', index_names=index_names)
        self.assertEqual('VGP:Site 21', val)


    def test_get_di_block(self):
        magic_df = nb.MagicDataFrame(os.path.join(WD, 'sites.txt'), dmodel=dmodel)
        di_block = magic_df.get_di_block(df_slice='all')
        self.assertEqual([289.8, 43.6], di_block[0])
        di_block = magic_df.get_di_block(do_index=True, item_names=['1', '2'])
        self.assertEqual([289.8, 43.6], di_block[0])
        self.assertEqual(2, len(di_block))
        print di_block
        magic_df.df.loc['2', 'method_codes'] = 'fake_code'
        di_block = magic_df.get_di_block(do_index=True, item_names=['1', '2'], excl=['fake_code'])
        self.assertEqual(1, len(di_block))
        # do a test with exclude codes or different tilt_corr



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
