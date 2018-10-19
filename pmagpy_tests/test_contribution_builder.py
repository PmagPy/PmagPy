#!/usr/bin/env python

import unittest
import os
import sys
import numpy as np
import pandas as pd
from pmagpy import pmag
from pmagpy import ipmag
from pmagpy import contribution_builder as cb
from pmagpy import data_model3 as data_model
from pmagpy import controlled_vocabularies3 as cv

# set constants

WD = pmag.get_test_WD()
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
        magic_df = cb.MagicDataFrame(dtype='specimens', data=data)
        self.assertEqual(len(magic_df.df), 2)
        self.assertEqual(magic_df.dtype, 'specimens')
        self.assertEqual('specimen name', magic_df.df.index.name)
        self.assertEqual(['spec1', 'spec2'], sorted(magic_df.df.index))

    def test_init_then_add_data(self):
        magic_df = cb.MagicDataFrame(dtype='specimens')
        data = [{'specimen': 'spec1', 'sample': 'samp1'},
                {'specimen': 'spec2', 'sample': 'samp2'}]
        magic_df.add_data(data)
        self.assertEqual(len(magic_df.df), 2)
        self.assertEqual(magic_df.dtype, 'specimens')
        self.assertEqual('specimen name', magic_df.df.index.name)
        self.assertEqual(['spec1', 'spec2'], sorted(magic_df.df.index))


    def test_init_blank(self):
        magic_df = cb.MagicDataFrame()
        self.assertFalse(magic_df.df)

    def test_init_with_dtype(self):
        magic_df = cb.MagicDataFrame(dtype='specimens',
                                     dmodel=DMODEL)
        self.assertEqual('specimens', magic_df.dtype)

    def test_init_with_file(self):
        magic_df = cb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        self.assertEqual('sites', magic_df.dtype)
        self.assertEqual('1', magic_df.df.index[1])

    def test_update_row(self):
        magic_df = cb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        self.assertEqual('Lava Flow', magic_df.df.iloc[3]['geologic_types'])
        magic_df.update_row(3, {'geologic_types': 'other type',
                                'new_col': 'new_val'})
        self.assertEqual('other type', magic_df.df.iloc[3]['geologic_types'])
        self.assertIn('new_col', magic_df.df.columns)
        self.assertEqual('new_val', magic_df.df.iloc[3]['new_col'])


    def test_add_row(self):
        magic_df = cb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        old_len = len(magic_df.df)
        magic_df.add_row('new_site', {'new_col': 'new_val'})
        self.assertEqual('new_val', magic_df.df.iloc[-1]['new_col'])
        self.assertEqual(old_len + 1, len(magic_df.df))


    def test_add_blank_row(self):
        magic_df = cb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        old_len = len(magic_df.df)
        magic_df.add_blank_row('blank_site')
        self.assertIn('blank_site', magic_df.df.index)
        self.assertEqual(old_len + 1, len(magic_df.df))


    def test_delete_row(self):
        magic_df = cb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        old_len = len(magic_df.df)
        magic_df.delete_row(5)
        self.assertEqual(old_len - 1, len(magic_df.df))
        self.assertEqual('3', magic_df.df.iloc[5].name)


    def test_delete_rows(self):
        magic_df = cb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        cond = magic_df.df['description'].str.contains('VGP').astype(bool)
        # delete all rows that aren't described as VGPs
        magic_df.delete_rows(-cond)
        for descr in magic_df.df['description'].values:
            self.assertTrue('VGP' in descr)

    def test_update_record(self):
        magic_df = cb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        cond = magic_df.df['lithologies'] == 'Basalt'
        magic_df.update_record('2', new_data={'description': 'updated'},
                               condition=cond)
        self.assertIn('updated', magic_df.df.loc['2', 'description'].values)

    def test_sort_dataframe_cols(self):
        magic_df = cb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        self.assertEqual('bed_dip', magic_df.df.columns[0])
        magic_df.sort_dataframe_cols()
        self.assertEqual('site', magic_df.df.columns[0])

    def test_convert_to_pmag_data_list(self):
        magic_df = cb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        lst = magic_df.convert_to_pmag_data_list('lst')
        self.assertEqual(list, type(lst))
        self.assertEqual(dict, type(lst[0]))
        self.assertEqual('1', str(lst[0]['site']))
        #
        dct = magic_df.convert_to_pmag_data_list("dict")
        self.assertEqual(dict, type(dct))
        self.assertEqual(dict, type(dct[list(dct.keys())[0]]))
        self.assertEqual('1', str(dct['1']['site']))

    def test_get_name(self):
        magic_df = cb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
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
        magic_df = cb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
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
        magic_df = cb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
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


    def test_get_first_non_null_value(self):
        magic_df = cb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        res = magic_df.get_first_non_null_value('1', 'bed_dip_direction')
        self.assertEqual(135, res)
        magic_df.df.loc['1', 'bed_dip_direction'] = None
        res = magic_df.get_first_non_null_value('1', 'bed_dip_direction')
        self.assertTrue(pd.isnull(res))


    def test_front_and_backfill(self):
        magic_df = cb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        directions = magic_df.df.loc['1', 'bed_dip_direction']
        self.assertEqual(sorted(directions,key=lambda x,y=0: int(x-y) if (isinstance(x,float) or isinstance(x,int)) and (isinstance(y,float) or isinstance(y,int)) else -1), [None, 135, 135])
        magic_df.front_and_backfill(cols=['bed_dip_direction'])
        directions = magic_df.df.loc['1', 'bed_dip_direction']
        self.assertEqual(sorted(directions), [135, 135, 135])

    def test_drop_stub_rows(self):
        magic_df = cb.MagicDataFrame(os.path.join(PROJECT_WD, 'sites.txt'),
                                     dmodel=DMODEL)
        self.assertEqual(3, len(magic_df.df.loc['1']))
        magic_df.add_row('1', {'site': '1', 'location': 'new_loc'})
        magic_df.add_row('1', {'site': '1', 'location': 'new_loc',
                               'citations': 'real citation'})
        self.assertEqual(5, len(magic_df.df.loc['1']))
        magic_df.drop_stub_rows(['site', 'location'])
        self.assertEqual(4, len(magic_df.df.loc['1']))

    def test_meas_dataframe(self):
        meas_file = os.path.join(WD, "data_files", "3_0", "McMurdo", "measurements.txt")
        df = pd.read_table(meas_file, skiprows=[0])
        self.assertNotIn('sequence', df.columns)
        magic_df = cb.MagicDataFrame(meas_file)
        self.assertIn('sequence', magic_df.df.columns)


    def test_convert_to_pmag_list(self):
        # np.nan and None should both be converted to a string
        directory = os.path.join(WD, 'data_files', '3_0', 'Megiddo')
        fname = os.path.join(directory, "sites.txt")
        df = cb.MagicDataFrame(fname)

        df.df.loc['mgq04t1', 'age_high'] = np.nan
        df.df.loc['mgq04t1', 'age_low'] = None
        for val in df.df.loc['mgq04t1', 'age_high'].values:
            self.assertTrue(np.isnan(val))

        for val in df.df.loc['mgq04t1', 'age_low'].values:
            self.assertTrue(val is None)

        lst = df.convert_to_pmag_data_list()
        relevant_lst = pmag.get_dictitem(lst, 'site', 'mgq04t1', 'T')
        # make sure np.nan/None values are converted to ''
        for i in relevant_lst:
            self.assertEqual(i['age_high'], '')
            self.assertEqual(i['age_low'], '')
        # make sure numeric values are string-i-fied
        self.assertEqual(str, type(relevant_lst[0]['age']))



class TestContribution(unittest.TestCase):

    def setUp(self):
        self.directory = os.path.join(WD, 'data_files', '3_0', 'Megiddo')
        self.con = cb.Contribution(self.directory, dmodel=DMODEL)

    def tearDown(self):
        os.chdir(WD)

    def test_init_empty(self):
        tables = ['measurements', 'specimens', 'samples',
                  'sites', 'locations', 'ages', 'criteria',
                  'contribution']
        files = os.listdir(WD)
        for table in tables:
            fname = table + ".txt"
            if fname in files:
                try:
                    print(os.path.join(WD, fname))
                    os.remove(os.path.join(WD, fname))
                except OSError:
                    print("error when removing files for empty directory test in test_contribution_builder")
        con = cb.Contribution(WD, dmodel=DMODEL)
        self.assertEqual(0, len(con.tables))

    def test_init(self):
        self.assertEqual(type(self.con), cb.Contribution)
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
        self.assertEqual('specimen name', magic_df.df.index.name)
        self.assertEqual(['spec1', 'spec2'], sorted(magic_df.df.index))



    def test_add_empty_magic_table(self):
        con = cb.Contribution(self.directory, read_tables=['specimens'],
                              dmodel=DMODEL)
        self.assertEqual(set(['specimens']), set(con.tables.keys()))
        con.add_empty_magic_table('samples')
        self.assertEqual(set(['specimens', 'samples']), set(con.tables.keys()))
        self.assertEqual(0, len(con.tables['samples'].df))

    def test_add_magic_table(self):
        con = cb.Contribution(self.directory, read_tables=['specimens'],
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
        self.assertEqual("hz06", self.con.tables['sites'].df.loc['hz06']['site'])

    def test_get_min_max_lat_lon(self):
        site_container = cb.MagicDataFrame(dtype='sites')
        site_container.add_row('site1', {'lat': 10, 'lon': 4, 'location': 'location1'})
        site_container.add_row('site2', {'lat': 10.2, 'lon': 5, 'location': 'location1'})
        site_container.add_row('site3', {'lat': 20, 'lon': '15', 'location': 'location2'})
        site_container.add_row('site4', {'lat': None, 'location': 'location1'})
        loc_container = cb.MagicDataFrame(dtype='locations', columns=['lat_n', 'lat_s', 'lon_e', 'lon_w', 'location'])
        site_container.df
        loc_container.add_row('location1', {})
        loc_container.add_row('location2', {})
        con = cb.Contribution(".", read_tables=['images'])
        con.tables['sites'] = site_container
        con.tables['locations'] = loc_container
        con.get_min_max_lat_lon()
        self.assertEqual(10., con.tables['locations'].df.loc['location1', 'lat_s'])
        self.assertEqual(15., con.tables['locations'].df.loc['location2', 'lon_e'])
        os.remove(os.path.join(".", "locations.txt"))

    def test_propagate_lithology_cols(self):
        self.con.tables['specimens'].df.loc[:, 'geologic_classes'] = None
        res = self.con.tables['specimens'].df['geologic_classes'].unique()
        self.assertEqual([None], res)
        self.con.propagate_lithology_cols()
        res = self.con.tables['specimens'].df['geologic_classes'].unique()
        self.assertEqual(res, ['Archeologic'])
        #
        self.con.tables['specimens'].df.loc[:, 'geologic_types'] = ""
        res = self.con.tables['specimens'].df['geologic_types'].unique()
        self.assertEqual([""], res)
        self.con.tables['samples'].df.loc['mgh12t101', 'geologic_types'] = "Oven"
        self.con.propagate_lithology_cols()
        res = self.con.tables['specimens'].df['geologic_types'].unique()
        self.assertEqual(sorted(res), ['Mixed Archeological Objects', 'Oven'])
        res = self.con.tables['specimens'].df.loc['mgh12t101', 'geologic_types']
        self.assertEqual('Oven', res)


    def test_sites_only_propagation(self):
        """
        Make sure propagation works correclty with limited tables provided
        """
        directory = os.path.join(WD, 'data_files', '3_0', 'McMurdo')
        con = cb.Contribution(directory, dmodel=DMODEL, read_tables=['sites'],
                              custom_filenames={'locations': '_locations.txt',
                                                'samples': '_samples.txt'})
        self.assertEqual(['sites'], list(con.tables.keys()))
        con.propagate_all_tables_info()
        self.assertEqual(sorted(['samples', 'sites', 'locations']), sorted(con.tables.keys()))
        for fname in ['_locations.txt', '_samples.txt']:
            os.remove(os.path.join(directory, fname))
        #
        con = cb.Contribution(directory, dmodel=DMODEL, read_tables=['sites'],
                              custom_filenames={'locations': '_locations.txt',
                                                'samples': '_samples.txt'})
        samp_df = pd.DataFrame(index=['mc01b'], columns=['sample', 'site'], data=[['mc01b', 'fake site']])
        samp_df = cb.MagicDataFrame(dtype='samples', df=samp_df)
        con.tables['samples'] = samp_df
        self.assertEqual('fake site', con.tables['samples'].df.loc['mc01b', 'site'])
        con.propagate_all_tables_info()
        self.assertEqual(sorted(['samples', 'sites', 'locations']), sorted(con.tables.keys()))
        # mc01b does not update b/c sample_df value trumps value from sites table
        self.assertEqual('fake site', con.tables['samples'].df.loc['mc01b', 'site'])
        # however, additional samples should be added
        self.assertIn('mc01d', con.tables['samples'].df.index)
        for fname in ['_locations.txt', '_samples.txt']:
            os.remove(os.path.join(directory, fname))
        #
        con = cb.Contribution(self.directory, dmodel=DMODEL, read_tables=['sites'],
                              custom_filenames={'locations': '_locations.txt',
                                                'samples': '_samples.txt'})
        self.assertEqual(['sites'], list(con.tables.keys()))
        con.propagate_all_tables_info()
        self.assertEqual(sorted(['sites', 'locations']), sorted(con.tables.keys()))
        for fname in ['_locations.txt']: # no samples available this time
            os.remove(os.path.join(self.directory, fname))

    def test_propagate_cols_up_old(self):
        directory = os.path.join(WD, 'data_files', '3_0', 'McMurdo')
        con = cb.Contribution(directory, dmodel=DMODEL,
                              read_tables=['sites', 'samples'])
        con.tables['sites'].df.loc[:, 'lithologies'] = None
        con.tables['sites'].df.loc[:, 'geologic_types'] = 'your type'
        con.tables['samples'].df.loc[:, 'geologic_types'] = 'my_type'
        con.propagate_cols(['lithologies', 'geologic_types'], 'sites',
                           'samples', down=False)
        self.assertEqual('Basalt', con.tables['sites'].get_first_non_null_value('mc50', 'lithologies'))
        self.assertEqual('your type', con.tables['sites'].get_first_non_null_value('mc50', 'geologic_types'))

    def test_propagate_cols_up(self):
        directory = os.path.join('data_files', '3_0', 'McMurdo')
        con = cb.Contribution(directory, read_tables=['sites', 'samples'],
                              custom_filenames={'locations': '_locations.txt'})
        con.tables['samples'].df.loc['mc01a', 'lithologies'] = 'other:Trachyte'
        ind = con.tables['samples'].df.columns.get_loc('lithologies')
        con.tables['samples'].df.iloc[2, ind] = None
        con.tables['samples'].df.iloc[3, ind] = np.nan
        con.tables['samples'].df.iloc[4, ind] = ''
        con.tables['sites'].df.loc['mc01', 'lithologies'] = ''
        con.tables['sites'].df[:10][['lithologies', 'geologic_types']]
        cols = ['lithologies', 'geologic_types']
        con.propagate_cols_up(cols, 'sites', 'samples')
        self.assertEqual('Other:Trachyte', con.tables['sites'].df.loc['mc01', 'lithologies'].unique()[0])
        self.assertEqual('Basalt', con.tables['sites'].df.loc['mc02', 'lithologies'].unique()[0])
        self.assertTrue(all(con.tables['sites'].df['lithologies']))
        # fail gracefully
        con = cb.Contribution(directory, read_tables=['sites'])
        con.propagate_cols_up(cols, 'sites', 'samples')


    def test_propagate_average_up(self):
        directory = os.path.join('data_files', '3_0', 'McMurdo')
        con = cb.Contribution(directory, read_tables=['sites', 'samples'])
        con.tables['sites'].df.drop(['lat', 'lon'], axis='columns',
                                    inplace=True)
        con.tables['samples'].df.loc['mc01a', 'lat'] = -60.
        # test basic function
        con.propagate_average_up()
        self.assertTrue(all(con.tables['sites'].df[['lat', 'lon']].values.ravel()))
        self.assertEqual([-75.61875], con.tables['sites'].df.loc['mc01', 'lat'].unique())
        # make sure does not overwrite existing values
        con = cb.Contribution(directory, read_tables=['sites', 'samples'])
        con.tables['sites'].df.loc['mc01', 'lon'] = 12
        con.propagate_average_up()
        self.assertEqual([12], con.tables['sites'].df.loc['mc01', 'lon'].unique())
        self.assertNotIn('new_lat', con.tables['sites'].df.columns)
        self.assertNotIn('new_lon', con.tables['sites'].df.columns)
        # make sure works with only some sample data available
        con = cb.Contribution(directory, read_tables=['sites', 'samples'])
        con.tables['samples'].df.drop(['lon'], axis='columns', inplace=True)
        con.propagate_average_up()
        # fails gracefully?
        con = cb.Contribution(directory, read_tables=['sites', 'samples'])
        con.tables['samples'].df.drop(['site'], axis='columns', inplace=True)
        con.tables['sites'].df.loc['mc01', 'lat'] = ''
        con.propagate_average_up()
        # fails gracefully?
        con = cb.Contribution(directory, read_tables=['sites', 'samples'],
                              custom_filenames={'samples': '_samples.txt'})
        res = con.propagate_average_up()
        self.assertIsNone(res)
        # fails gracefully?
        res = con.propagate_average_up(target_df_name='samples', source_df_name='sites')
        self.assertIsNone(res)
        # fails gracefully?
        res = con.propagate_average_up(target_df_name='sites', source_df_name='specimens')
        self.assertIsNone(res)


    def test_get_age_levels(self):
        # mess with data
        self.con.tables['ages'].df['sample'] = None
        self.con.tables['ages'].df['specimen'] = None
        self.con.tables['ages'].df.loc['1', 'sample'] = 'a_sample'
        self.con.tables['ages'].df.loc['2', 'specimen'] = 'a_specimen'
        self.con.tables['ages'].df.loc['3', 'sample'] = 'a_sample'
        self.con.tables['ages'].df.loc['3', 'specimen'] = 'a_specimen'
        self.con.tables['ages'].df.loc['5', 'site'] = ''
        self.con.tables['ages'].df.loc['6', 'site'] = None
        # do level calculation
        self.con.get_age_levels()
        # results
        self.assertEqual('sample', self.con.tables['ages'].df.loc['1', 'level'])
        self.assertEqual('specimen', self.con.tables['ages'].df.loc['2', 'level'])
        self.assertEqual('specimen', self.con.tables['ages'].df.loc['3', 'level'])
        self.assertEqual('site', self.con.tables['ages'].df.loc['4', 'level'])
        self.assertEqual('location', self.con.tables['ages'].df.loc['5', 'level'])
        self.assertEqual('location', self.con.tables['ages'].df.loc['6', 'level'])

    def test_propagate_ages(self):
        # mess up data
        self.con.tables['ages'].df['sample'] = None
        self.con.tables['ages'].df['specimen'] = ''
        self.con.tables['ages'].df.loc['1', 'site'] = None
        self.con.tables['ages'].df.loc['2', 'sample'] = 'mgq05t2a2'
        self.con.tables['ages'].df.loc['3', 'sample'] = 'mgq05t2a2'
        self.con.tables['ages'].df.loc['3', 'specimen'] = 'hz05a1'
        self.con.tables['sites'].df.loc['hz10', 'age'] = 999
        self.con.tables['sites'].df.loc['hz11', 'age'] = ''
        # do propagation
        self.con.propagate_ages()
        # results
        res = self.con.tables['locations'].df.loc['Tel Hazor', 'age_high']
        self.assertEqual(-732, res)
        res = self.con.tables['sites'].df.loc['hz05', 'age']
        self.assertEqual(-740, res)
        # these two are checks failing.
        # this is because there are no valid age headers at the
        # sample/specimen level
        # fails b/c this line in propagate_ages:
        # age_headers = self.data_model.get_group_headers(table_name, 'Age')
        #res = self.con.tables['samples'].df.loc['mgq05t2a2', 'age_unit']
        #self.assertEqual('Years Cal AD (+/-)', res)
        #res = self.con.tables['specimens'].df.loc['hz05a1', 'age'].unique()[0]
        #self.assertEqual(-950, res)
        res = self.con.tables['sites'].df.loc['hz10', 'age']
        self.assertEqual(999, res)
        res = self.con.tables['sites'].df.loc['hz11', 'age']
        self.assertEqual(-1050, res)

    def test_propagate_ages_other_contribution(self):
        directory = os.path.join(WD, 'data_files', '3_0', 'McMurdo')
        con = cb.Contribution(directory)
        con.propagate_ages()

    def test_propagate_ages_location_component(self):
        self.con.propagate_min_max_up(min_suffix='lowest', max_suffix='highest')
        res = self.con.tables['locations'].df.loc[['Tel Hazor'], 'age_lowest'].values[0]
        self.assertEqual(-2700, res)
        res = self.con.tables['locations'].df.loc[['Tel Megiddo'], 'age_highest'].values[0]
        self.assertEqual(-740, res)
        # test don't overwrite
        self.con.tables['locations'].df.loc['Tel Hazor', 'age_high'] = 10
        self.con.propagate_min_max_up()
        res = self.con.tables['locations'].df.loc[['Tel Hazor'], 'age_high'].values[0]
        self.assertEqual(10, res)
        res = self.con.tables['locations'].df.loc[['Tel Megiddo'], 'age_high'].values[0]
        self.assertEqual(-740, res)
        res = self.con.tables['locations'].df.loc[['Tel Megiddo'], 'age_low'].values[0]
        self.assertEqual(-3000, res)
        # test graceful fail
        self.con.tables['sites'].df.drop(['age'], axis='columns', inplace=True)
        res = self.con.propagate_min_max_up(min_suffix='lowest', max_suffix='highest')

    def test_propagate_ages_extra_location_rows(self):
        directory = os.path.join(WD, 'data_files', '3_0', 'McMurdo')
        con = cb.Contribution(directory)
        con.tables['locations'].add_row('McMurdo2', {})
        con.tables['sites'].df.loc['mc01', 'location'] = 'McMurdo2'
        con.propagate_ages()

    def test_propagate_name_down(self):
        directory = os.path.join(WD, 'data_files', 'convert_2_magic', 'cit_magic', 'PI47')
        con = cb.Contribution(directory)
        self.assertNotIn('location', con.tables['measurements'].df.columns)
        # need to actually test this
        con.propagate_name_down('sample', 'measurements')
        con.propagate_name_down('site', 'measurements')
        con.propagate_name_down('location', 'measurements')
        self.assertIn('location', con.tables['measurements'].df.columns)

    def test_propagate_name_down_fail(self):
        """fail gracefully"""
        directory = os.path.join(WD, 'data_files', 'convert_2_magic', 'cit_magic', 'PI47')
        con = cb.Contribution(directory)
        self.assertNotIn('sample', con.tables['measurements'].df.columns)
        self.assertNotIn('location', con.tables['measurements'].df.columns)
        # missing link:
        del con.tables['samples'].df['site']
        meas_df = con.propagate_location_to_measurements()
        self.assertIn('sample', con.tables['measurements'].df.columns)
        self.assertNotIn('location', meas_df.columns)


    def test_find_missing_items(self):
        for table in self.con.tables:
            self.assertEqual(set(), self.con.find_missing_items(table))

        self.con.tables['sites'].delete_row(0)
        missing = self.con.find_missing_items('sites')
        self.assertEqual(set(['hz05']), missing)

        con = cb.Contribution(PROJECT_WD)
        for table in con.tables:
            self.assertEqual(set(), con.find_missing_items(table))

        directory = os.path.join(WD, 'data_files', '3_0', 'McMurdo')
        con = cb.Contribution(directory)
        for table in con.tables:
            self.assertEqual(set(), con.find_missing_items(table))



class TestNotNull(unittest.TestCase):

    def test_values(self):
        vals = [1, 0, True, False, 'string', '', ['a'], [], ('t',), (),
                pd.DataFrame(['val1']), pd.DataFrame([]),
                pd.Series(['s']), pd.Series([]),
                3., np.nan]
        for num, val in enumerate(vals):
            res = cb.not_null(val)
            # all evens should be True, all odds should be False
            correct = (num % 2) == 0
            self.assertEqual(correct, res)
        self.assertTrue(cb.not_null(0, False))


class TestMungeForPlotting(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        #dmag_dir = os.path.join(WD, 'data_files', 'dmag_magic')
        #tables = ['specimens.txt', 'samples.txt',
        #          'sites.txt', 'locations.txt', 'ages.txt', 'criteria.txt',
        #          'contribution.txt', 'images.txt']
        #pmag.remove_files(tables, dmag_dir)
        orientation_dir = os.path.join(WD, 'data_files', 'orientation_magic')
        pmag.remove_files(['samples.txt', 'sites.txt'], orientation_dir)
        os.chdir(WD)

    def test_group_by_site(self):
        dmag_dir = os.path.join(WD, 'data_files', 'dmag_magic')
        status, meas_data = cb.add_sites_to_meas_table(dmag_dir)
        self.assertTrue(status)
        self.assertIn('site', meas_data.columns)
        osler_dir = os.path.join(WD, 'data_files', '3_0', 'Osler')
        status, warning = cb.add_sites_to_meas_table(osler_dir)
        self.assertFalse(status)
        self.assertEqual(warning, "You are missing measurements, specimens, samples tables")
        mcmurdo_dir = os.path.join(WD, 'data_files', '3_0', 'McMurdo')
        status, meas_data = cb.add_sites_to_meas_table(mcmurdo_dir)
        self.assertTrue(status)
        self.assertIn('site', meas_data.columns)
        orientation_dir = os.path.join(WD, 'data_files', 'orientation_magic')
        ipmag.orientation_magic(orient_file='orient_example.txt',
                                output_dir_path=orientation_dir,
                                input_dir_path=orientation_dir)
        status, warning = cb.add_sites_to_meas_table(orientation_dir)
        self.assertFalse(status)
        self.assertEqual(warning, "You are missing measurements, specimens tables")


    def test_prep_for_intensity_plot(self):
        dmag_dir = os.path.join(WD, 'data_files', 'dmag_magic')
        # method code to plot
        meth_code = "LT-AF-Z"
        # columns that must not be null
        dropna = ['treat_ac_field'] #, magn_col]
        # columns that must be present for plotting
        reqd_cols = ['specimen', 'site', 'treat_ac_field','quality']
        # add site column to measurement data
        status, meas_data = cb.add_sites_to_meas_table(dmag_dir)
        # do the test
        status, meas_data = cb.prep_for_intensity_plot(meas_data, meth_code, dropna, reqd_cols)
        self.assertTrue(status)
        self.assertTrue(all(meas_data['method_codes'].str.contains('LT-AF-Z')))


if __name__ == '__main__':
    unittest.main()
