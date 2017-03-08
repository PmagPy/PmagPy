#!/usr/bin/env python

import unittest
import os
import pandas as pd
from pmagpy import new_builder as nb
from pmagpy import data_model3 as data_model
from pmagpy import controlled_vocabularies3 as cv

# set constants
WD = os.getcwd()
PROJECT_WD = os.path.join(WD, 'data_files', '3_0', 'Osler')
#vocab = cv.Vocabulary()
#VOCABULARY, possible_vocabulary = vocab.get_controlled_vocabularies()
DMODEL = data_model.DataModel()


class TestMagicDataFrame(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        os.chdir(WD)

    def test_init_with_data(self):
        data = [{'specimen': 'spec1', 'sample': 'samp1'},
                {'specimen': 'spec2', 'sample': 'samp2'}]
        magic_df = nb.MagicDataFrame(dtype='specimens', data=data)
        self.assertEqual(len(magic_df.df), 2)
        self.assertEqual(magic_df.dtype, 'specimens')
        self.assertEqual('specimen', magic_df.df.index.name)
        self.assertEqual(['spec1', 'spec2'], sorted(magic_df.df.index))

    def test_init_then_add_data(self):
        magic_df = nb.MagicDataFrame(dtype='specimens')
        data = [{'specimen': 'spec1', 'sample': 'samp1'},
                {'specimen': 'spec2', 'sample': 'samp2'}]
        magic_df.add_data(data)
        self.assertEqual(len(magic_df.df), 2)
        self.assertEqual(magic_df.dtype, 'specimens')
        self.assertEqual('specimen', magic_df.df.index.name)
        self.assertEqual(['spec1', 'spec2'], sorted(magic_df.df.index))


    def test_init_blank(self):
        magic_df = nb.MagicDataFrame()
        self.assertFalse(magic_df.df)

    def test_init_with_dtype(self):
        magic_df = nb.MagicDataFrame(dtype='specimens',
                                     dmodel=DMODEL)
        self.assertEqual('specimens', magic_df.dtype)

    def test_init_with_file(self):
        magic_df = nb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        self.assertEqual('sites', magic_df.dtype)
        self.assertEqual('1', magic_df.df.index[1])

    def test_update_row(self):
        magic_df = nb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        self.assertEqual('Lava Flow', magic_df.df.iloc[3]['geologic_types'])
        magic_df.update_row(3, {'geologic_types': 'other type',
                                'new_col': 'new_val'})
        self.assertEqual('other type', magic_df.df.iloc[3]['geologic_types'])
        self.assertIn('new_col', magic_df.df.columns)
        self.assertEqual('new_val', magic_df.df.iloc[3]['new_col'])


    def test_add_row(self):
        magic_df = nb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        old_len = len(magic_df.df)
        magic_df.add_row('new_site', {'new_col': 'new_val'})
        self.assertEqual('new_val', magic_df.df.iloc[-1]['new_col'])
        self.assertEqual(old_len + 1, len(magic_df.df))


    def test_add_blank_row(self):
        magic_df = nb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        old_len = len(magic_df.df)
        magic_df.add_blank_row('blank_site')
        self.assertIn('blank_site', magic_df.df.index)
        self.assertEqual(old_len + 1, len(magic_df.df))


    def test_delete_row(self):
        magic_df = nb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        old_len = len(magic_df.df)
        magic_df.delete_row(5)
        self.assertEqual(old_len - 1, len(magic_df.df))
        self.assertEqual('3', magic_df.df.iloc[5].name)


    def test_delete_rows(self):
        magic_df = nb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        cond = magic_df.df['description'].str.contains('VGP').astype(bool)
        # delete all rows that aren't described as VGPs
        magic_df.delete_rows(-cond)
        for descr in magic_df.df['description'].values:
            self.assertTrue('VGP' in descr)

    def test_update_record(self):
        magic_df = nb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        cond = magic_df.df['lithologies'] == 'Basalt'
        magic_df.update_record('2', new_data={'description': 'updated'},
                               condition=cond)
        self.assertIn('updated', magic_df.df.loc['2', 'description'].values)

    def test_convert_to_pmag_data_list(self):
        magic_df = nb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
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
        magic_df = nb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        val = magic_df.get_name('description')
        self.assertEqual('VGP:Site 1', val)
        df_slice = magic_df.df.iloc[10:20]
        val = magic_df.get_name('description', df_slice)
        self.assertEqual('VGP:Site 4', val)
        index_names = ['21', '22']
        val = magic_df.get_name('description', index_names=index_names)
        self.assertEqual('VGP:Site 21', val)

    def test_get_di_block(self):
        magic_df = nb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        di_block = magic_df.get_di_block(df_slice='all')
        self.assertEqual([289.8, 43.6], di_block[0])
        di_block = magic_df.get_di_block(do_index=True, item_names=['1', '2'])
        self.assertEqual([289.8, 43.6], di_block[0])
        self.assertEqual(2, len(di_block))
        magic_df.df.loc['2', 'method_codes'] = 'fake_code'
        di_block = magic_df.get_di_block(do_index=True, item_names=['1', '2'],
                                         excl=['fake_code'])
        self.assertEqual(1, len(di_block))

    def test_get_records_for_code(self):
        magic_df = nb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        results = magic_df.get_records_for_code('LP-DC2')
        self.assertEqual(87, len(results))
        #
        magic_df.df.loc['1', 'method_codes'] = 'LP-NEW'
        results = magic_df.get_records_for_code('LP', strict_match=False)
        self.assertEqual(89, len(results))
        #
        df_slice = magic_df.df.head()
        results = magic_df.get_records_for_code('LP-DC2', use_slice=True,
                                                sli=df_slice)
        self.assertEqual(1, len(results))


class TestContribution(unittest.TestCase):

    def setUp(self):
        self.directory = os.path.join(WD, 'data_files', '3_0', 'Megiddo')
        self.con = nb.Contribution(self.directory, dmodel=DMODEL)

    def tearDown(self):
        os.chdir(WD)

    def test_init_empty(self):
        con = nb.Contribution(WD, dmodel=DMODEL)
        self.assertEqual(0, len(con.tables))

    def test_init(self):
        self.assertEqual(type(self.con), nb.Contribution)
        self.assertEqual(set(self.con.tables),
                         set(['measurements', 'specimens', 'samples',
                              'sites', 'locations', 'ages', 'criteria',
                              'contribution']))

    def test_vocabulary_is_created(self):
        """
        Make sure all expected components of vocabulary are initialized
        """
        self.assertEqual(type(self.con.vocab), cv.Vocabulary)
        for item in [self.con.vocab.vocabularies, self.con.vocab.suggested,
                     self.con.vocab.all_codes, self.con.vocab.code_types,
                     self.con.vocab.methods, self.con.vocab.age_methods]:
            self.assertTrue(len(item))


    def test_add_custom_filenames(self):
        self.con.add_custom_filenames({'specimens': 'custom_specimens.txt'})
        self.assertEqual('custom_specimens.txt', self.con.filenames['specimens'])

    def test_add_magic_table_from_data(self):
        data = [{'specimen': 'spec1', 'sample': 'samp1'},
                {'specimen': 'spec2', 'sample': 'samp2'}]
        self.con.add_magic_table_from_data('specimens', data)
        magic_df = self.con.tables['specimens']
        self.assertEqual(len(magic_df.df), 2)
        self.assertEqual(magic_df.dtype, 'specimens')
        self.assertEqual('specimen', magic_df.df.index.name)
        self.assertEqual(['spec1', 'spec2'], sorted(magic_df.df.index))



    def test_add_empty_magic_table(self):
        con = nb.Contribution(self.directory, read_tables=['specimens'],
                              dmodel=DMODEL)
        self.assertEqual(set(['specimens']), set(con.tables.keys()))
        con.add_empty_magic_table('samples')
        self.assertEqual(set(['specimens', 'samples']), set(con.tables.keys()))
        self.assertEqual(0, len(con.tables['samples'].df))

    def test_add_magic_table(self):
        con = nb.Contribution(self.directory, read_tables=['specimens'],
                              dmodel=DMODEL)
        self.assertEqual(set(['specimens']), set(con.tables.keys()))
        con.add_magic_table('samples')
        self.assertEqual(set(['specimens', 'samples']), set(con.tables.keys()))
        self.assertGreater(len(con.tables['samples'].df), 0)
        con.add_magic_table('unknown', 'sites.txt')
        self.assertEqual(set(['specimens', 'samples', 'sites']),
                         set(con.tables.keys()))
        self.assertGreater(len(con.tables['sites'].df), 0)

    def test_get_parent_and_child(self):
        parent_name, child_name = self.con.get_parent_and_child("samples")
        self.assertEqual("sites", parent_name)
        self.assertEqual("specimens", child_name)
        # handle incorrect input table name
        parent_name, child_name = self.con.get_parent_and_child("fake")
        self.assertIsNone(parent_name)
        self.assertIsNone(child_name)

    def test_propagate_all_tables_info_missing_tables(self):
        self.con.tables.pop("specimens")
        self.con.tables.pop("locations")
        self.con.propagate_all_tables_info(write=False)

    def test_propagate_all_tables_info_missing_row(self):
        # test by removing a value
        self.con.tables['sites'].delete_rows(self.con.tables['sites'].df.index == 'hz06')
        self.assertNotIn("hz06", self.con.tables['sites'].df.index)
        self.con.propagate_all_tables_info(write=False)
        self.assertIn("hz06", self.con.tables['sites'].df.index)
        self.assertEqual("hz06", self.con.tables['sites'].df.ix['hz06']['site'])

    def test_get_min_max_lat_lon(self):
        site_container = nb.MagicDataFrame(dtype='sites')
        site_container.add_row('site1', {'lat': 10, 'lon': 4, 'location': 'location1'})
        site_container.add_row('site2', {'lat': 10.2, 'lon': 5, 'location': 'location1'})
        site_container.add_row('site3', {'lat': 20, 'lon': '15', 'location': 'location2'})
        site_container.add_row('site4', {'lat': None, 'location': 'location1'})
        loc_container = nb.MagicDataFrame(dtype='locations', columns=['lat_n', 'lat_s', 'lon_e', 'lon_w', 'location'])
        site_container.df
        loc_container.add_row('location1', {})
        loc_container.add_row('location2', {})
        con = nb.Contribution(".", read_tables=['images'])
        con.tables['sites'] = site_container
        con.tables['locations'] = loc_container
        con.get_min_max_lat_lon()
        self.assertEqual(10., con.tables['locations'].df.ix['location1', 'lat_s'])
        self.assertEqual(15., con.tables['locations'].df.ix['location2', 'lon_e'])

    def test_sites_only_propagation(self):
        """
        Make sure propagation works correclty with limited tables provided
        """
        directory = os.path.join(WD, 'data_files', '3_0', 'McMurdo')
        con = nb.Contribution(directory, dmodel=DMODEL, read_tables=['sites'],
                              custom_filenames={'locations': '_locations.txt',
                                                'samples': '_samples.txt'})
        self.assertEqual(['sites'], con.tables.keys())
        con.propagate_all_tables_info()
        self.assertEqual(sorted(['samples', 'sites', 'locations']), sorted(con.tables.keys()))
        for fname in ['_locations.txt', '_samples.txt']:
            os.remove(os.path.join(directory, fname))
        #
        con = nb.Contribution(directory, dmodel=DMODEL, read_tables=['sites'],
                              custom_filenames={'locations': '_locations.txt',
                                                'samples': '_samples.txt'})
        samp_df = pd.DataFrame(index=['mc01b'], columns=['sample', 'site'], data=[['mc01b', 'fake site']])
        samp_df = nb.MagicDataFrame(dtype='samples', df=samp_df)
        con.tables['samples'] = samp_df
        self.assertEqual('fake site', con.tables['samples'].df.ix['mc01b', 'site'])
        con.propagate_all_tables_info()
        self.assertEqual(sorted(['samples', 'sites', 'locations']), sorted(con.tables.keys()))
        # mc01b does not update b/c sample_df value trumps value from sites table
        self.assertEqual('fake site', con.tables['samples'].df.ix['mc01b', 'site'])
        # however, additional samples should be added
        self.assertIn('mc01d', con.tables['samples'].df.index)
        for fname in ['_locations.txt', '_samples.txt']:
            os.remove(os.path.join(directory, fname))
        #
        con = nb.Contribution(self.directory, dmodel=DMODEL, read_tables=['sites'],
                              custom_filenames={'locations': '_locations.txt',
                                                'samples': '_samples.txt'})
        self.assertEqual(['sites'], con.tables.keys())
        con.propagate_all_tables_info()
        self.assertEqual(sorted(['sites', 'locations']), sorted(con.tables.keys()))
        for fname in ['_locations.txt']: # no samples available this time
            os.remove(os.path.join(self.directory, fname))



if __name__ == '__main__':
    unittest.main()
