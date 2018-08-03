#!/usr/bin/env python

"""
Test map_magic module conversions
from MagIC 2 column names --> MagIC 3 column names.
"""

import unittest
import os
from pmagpy.mapping import map_magic
from pmagpy.mapping import maps
from pmagpy.data_model3 import DataModel
from pmagpy import contribution_builder as cb
from pmagpy import pmag
DM = DataModel()
TEST_DIR = pmag.get_test_WD()


class TestMapping(unittest.TestCase):

    def test_meas_map(self):
        magic2_keys = {'er_analyst_mail_names', 'measurement_number',
                       'measurement_flag', 'treatment_temp',
                       'measurement_pos_z'}
        magic2_dict = {key: '' for key in magic2_keys}
        magic3_keys = {'analysts', 'measurement',
                       'quality', 'treat_temp',
                       'meas_pos_z'}
        output = map_magic.mapping(magic2_dict,
                                   map_magic.meas_magic2_2_magic3_map)
        # check that translation worked
        self.assertEqual(sorted(magic3_keys), sorted(output.keys()))
        # check that all output values are 3.0 valid
        for val in list(output.keys()):
            self.assertIn(val, DM.dm['measurements'].index)

    def test_spec_map(self):
        magic2_keys = {'er_specimen_name', 'er_sample_name', 'specimen_weight',
                       'result_type', 'specimen_type', 'specimen_azimuth',
                       'specimen_tilt_correction', 'specimen_int_ptrm_n'}
        magic2_dict = {key: '' for key in magic2_keys}
        magic3_keys = {'specimen', 'sample', 'weight', 'result_type',
                       'geologic_types', 'azimuth', 'dir_tilt_correction',
                       'int_n_ptrm'}
        output = map_magic.mapping(magic2_dict,
                                   map_magic.spec_magic2_2_magic3_map)
        self.assertEqual(sorted(magic3_keys), sorted(output.keys()))
        # check that all output values are 3.0 valid
        for val in list(output.keys()):
            self.assertIn(val, DM.dm['specimens'].index)

    def test_spec_name(self):
        magic2_keys = {'er_synthetic_name'}
        magic3_keys = {'specimen'}
        magic2_dict = {key: '' for key in magic2_keys}
        output = map_magic.mapping(magic2_dict,
                                   map_magic.spec_magic2_2_magic3_map)
        self.assertEqual(sorted(magic3_keys), sorted(output.keys()))
        output = map_magic.mapping(output, map_magic.spec_magic3_2_magic2_map)
        self.assertEqual(['er_specimen_name'], sorted(output.keys()))

    def test_samp_map(self):
        magic2_keys = {'er_sample_name', 'er_specimen_names', 'er_site_name',
                       'magic_method_codes', 'sample_texture',
                       'sample_bed_dip', 'sample_int_rel_sigma'}
        magic2_dict = {key: '' for key in magic2_keys}
        magic3_keys = {'sample', 'specimens', 'site', 'method_codes',
                       'texture', 'bed_dip', 'int_rel_sigma'}
        output = map_magic.mapping(magic2_dict,
                                   map_magic.samp_magic2_2_magic3_map)
        self.assertEqual(sorted(magic3_keys), sorted(output.keys()))
        # check that all output values are 3.0 valid
        for val in list(output.keys()):
            self.assertIn(val, DM.dm['samples'].index)

    def test_samp_map_with_adjusted_vocab(self):
        magic2_keys = {'er_specimen_names', 'sample_comp_name',
                       'sample_date', 'external_database_ids'}
        magic3_keys = {'specimens', 'dir_comp_name',
                       'timestamp', 'external_database_ids'}
        magic3_dict = {key: '' for key in magic3_keys}
        output = map_magic.mapping(magic3_dict,
                                   map_magic.samp_magic3_2_magic2_map)
        self.assertEqual(sorted(magic2_keys), sorted(output.keys()))

    def test_site_map(self):
        magic2_keys = {'er_site_name', 'er_sample_names',
                       'magic_experiment_names', 'site_igsn',
                       'er_citation_names', 'site_cooling_rate',
                       'site_inferred_age', 'int_rel_chi_sigma_perc',
                       'er_scientist_mail_names'}
        magic2_dict = {key: '' for key in magic2_keys}
        magic3_keys = {'site', 'samples', 'experiments', 'igsn', 'citations',
                       'cooling_rate', 'age', 'int_rel_chi_sigma_perc',
                       'scientists'}
        magic3_dict = {key: '' for key in magic3_keys}
        output = map_magic.mapping(magic2_dict,
                                   map_magic.site_magic2_2_magic3_map)
        self.assertEqual(sorted(magic3_keys), sorted(output.keys()))
        # check that all output values are 3.0 valid
        for val in list(output.keys()):
            self.assertIn(val, DM.dm['sites'].index)
        # try reverse operation (2.5 --> 3.0)
        output = map_magic.mapping(magic3_dict,
                                   map_magic.site_magic3_2_magic2_map)
        self.assertEqual(sorted(magic2_keys), sorted(output.keys()))

    def test_loc_map(self):
        magic2_keys = {'er_location_name', 'location_type', 'location_url',
                       'location_end_elevation', 'location_description'}
        magic2_dict = {key: '' for key in magic2_keys}
        magic3_keys = {'location', 'location_type', 'expedition_url',
                       'elevation_high', 'description'}
        output = map_magic.mapping(magic2_dict,
                                   map_magic.loc_magic2_2_magic3_map)
        self.assertEqual(sorted(magic3_keys), sorted(output.keys()))
        # check that all output values are 3.0 valid
        for val in list(output.keys()):
            self.assertIn(val, DM.dm['locations'].index)

    def test_all_values_in_maps(self):
        for map_type in maps.all_maps:
            values = list(maps.all_maps[map_type].values())
            for val in values:
                ignore = ['location', 'site', 'sample', 'specimen']
                for val in ignore[:]:
                    ignore.append(val + "s")
                if val not in ignore:
                    self.assertTrue(val in DM.dm[map_type].index)


class TestThellierGUIMapping(unittest.TestCase):

    def setUp(self):
        self.magic_file = os.path.join(TEST_DIR, 'data_files', '3_0',
                                       'McMurdo', 'measurements.txt')

    def test_get_thellier_gui_meas_mapping(self):
        # MagIC 3 --> 2 with 'treat_step_num'
        meas_data3_0 = cb.MagicDataFrame(self.magic_file).df
        meas_data3_0.iloc[0, meas_data3_0.columns.get_loc('measurement')] = 'custom'
        meas_data2_5 = map_magic.convert_meas_df_thellier_gui(meas_data3_0, output=2)
        self.assertEqual('custom',
                         meas_data2_5.iloc[0, meas_data2_5.columns.get_loc('measurement')])
        self.assertEqual(1,
                         meas_data2_5.iloc[0, meas_data2_5.columns.get_loc('measurement_number')])

        # and back
        meas_data3_again = map_magic.convert_meas_df_thellier_gui(meas_data2_5, output=3)
        self.assertEqual('custom',
                         meas_data3_again.iloc[0, meas_data3_again.columns.get_loc('measurement')])
        self.assertEqual(1,
                         meas_data3_again.iloc[0, meas_data3_again.columns.get_loc('treat_step_num')])

        # MagIC 3 --> 2 without 'treat_step_num'
        del meas_data3_0['treat_step_num']
        self.assertEqual('custom',
                         meas_data3_0.iloc[0, meas_data3_0.columns.get_loc('measurement')])
        meas_data2_5 = map_magic.convert_meas_df_thellier_gui(meas_data3_0, output=2)
        self.assertIn('measurement_number', meas_data2_5.columns)
        self.assertEqual('custom',
                 meas_data2_5.iloc[0, meas_data2_5.columns.get_loc('measurement')])
        self.assertEqual('custom',
                         meas_data2_5.iloc[0, meas_data2_5.columns.get_loc('measurement_number')])

        # and back to 3
        meas_data3_0_again = map_magic.convert_meas_df_thellier_gui(meas_data2_5, output=3)
        self.assertEqual('custom',
                         meas_data3_0_again.iloc[0, meas_data2_5.columns.get_loc('measurement')])
        self.assertNotIn('treat_step_num', meas_data3_0_again.columns)


    def test_with_numeric_measurement_name(self):
        # set up meas df with numeric measurement names
        meas_data3 = cb.MagicDataFrame(self.magic_file).df
        del meas_data3['treat_step_num']
        meas_names = range(1001, len(meas_data3) + 1001)
        meas_data3['measurement'] = meas_names
        # convert from MagIC 3 --> MagIC 2.5
        meas_data2 = map_magic.convert_meas_df_thellier_gui(meas_data3, output=2)
        self.assertEqual(1001,
                         meas_data2.iloc[0, meas_data2.columns.get_loc('measurement')])
        self.assertEqual(1001,
                         meas_data2.iloc[0, meas_data2.columns.get_loc('measurement_number')])
        # and back
        meas_data3_again = map_magic.convert_meas_df_thellier_gui(meas_data2, output=3)
        self.assertNotIn('treat_step_num', meas_data3_again.columns)
        self.assertEqual(1001,
                         meas_data3_again.iloc[0, meas_data3_again.columns.get_loc('measurement')])
