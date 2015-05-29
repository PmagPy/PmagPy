#!/usr/bin/env python

# pylint: disable=C0303,W0612,C0303,C0111,C0301



"""
Tests for ErMagicBuilder
"""

import unittest   
import os
import ErMagicBuilder    
#import pmag    
#import ipmag
#import matplotlib
WD = os.getcwd()


class TestBuilder(unittest.TestCase):
    """
    Test ErMagicBuilder data structure
    """

    def setUp(self):
        dir_path = os.path.join(WD, 'Datafiles', 'ErMagicBuilder')
        self.data1 = ErMagicBuilder.ErMagicBuilder(dir_path)


    def tearDown(self):
        pass

    def test_data_creation(self):
        self.assertTrue(self.data1)

    def test_update_sample(self):
        samples = self.data1.data_er_samples.keys()
        self.data1.change_sample('new_name', 'Z35.5', {'new_key': 'new value', 'er_location_name': 'different location'})
        self.assertEqual(self.data1.Data_hierarchy['sample_of_specimen']['Z35.5a'], 'new_name')
        self.assertEqual(self.data1.Data_hierarchy['specimens']['Z35.5a'], 'new_name')
        self.assertIn('new_name', self.data1.Data_hierarchy['samples'].keys())
        self.assertEqual(self.data1.Data_hierarchy['site_of_sample']['new_name'], 'Z35.')   
        self.assertIn('new_name', self.data1.Data_hierarchy['sites']['Z35.'])
        self.assertEqual(self.data1.Data_hierarchy['location_of_sample']['new_name'], 'locale')   
        output_dict = {'new_key': 'new value', 'sample_bed_dip_direction': '444.5', 'er_citation_names': 'This study', 'sample_lithology': '', 'er_site_name': 'Z35.', 'sample_dip': '-82.0', 'magic_method_codes': 'SO-CMD-NORTH', 'sample_lat': '47.1', 'sample_bed_dip': '55.0', 'er_location_name': 'different location', 'sample_declination_correction': '0.5', 'sample_height': '148.25', 'sample_type': '', 'er_sample_name': 'Z35.5', 'sample_azimuth': '5.5', 'sample_lon': '95.4', 'sample_class': ''}
        self.assertEqual(output_dict, self.data1.data_er_samples['new_name'])   
