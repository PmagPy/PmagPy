#!/usr/bin/env python

"""
Test map_magic module conversions
from MagIC 2 column names --> MagIC 3 column names.
"""

import unittest
from pmagpy.mapping import map_magic
from pmagpy.mapping import maps
from pmagpy.data_model3 import DataModel
DM = DataModel()


class TestMapping(unittest.TestCase):

    def test_meas_map(self):
        magic2_keys = {'er_analyst_mail_names', 'measurement_number',
                       'measurement_flag', 'treatment_temp',
                       'measurement_pos_z'}
        magic2_dict = {key: '' for key in magic2_keys}
        magic3_keys = {'analysts', 'treat_step_num',
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
