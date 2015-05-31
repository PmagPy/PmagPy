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
        specimen = 'Z35.5a'
        self.data1.change_sample('new_name', 'Z35.5', {'new_key': 'new value', 'er_location_name': 'different location'})
        self.assertEqual(self.data1.Data_hierarchy['sample_of_specimen'][specimen], 'new_name')
        self.assertEqual(self.data1.Data_hierarchy['specimens'][specimen], 'new_name')
        self.assertIn('new_name', self.data1.Data_hierarchy['samples'].keys())
        self.assertEqual(self.data1.Data_hierarchy['site_of_sample']['new_name'], 'Z35.')   
        self.assertIn('new_name', self.data1.Data_hierarchy['sites']['Z35.'])
        self.assertEqual(self.data1.Data_hierarchy['location_of_sample']['new_name'], 'locale')   
        output_dict = {'new_key': 'new value', 'sample_bed_dip_direction': '444.5', 'er_citation_names': 'This study', 'sample_lithology': '', 'er_site_name': 'Z35.', 'sample_dip': '-82.0', 'magic_method_codes': 'SO-CMD-NORTH', 'sample_lat': '47.1', 'sample_bed_dip': '55.0', 'er_location_name': 'different location', 'sample_declination_correction': '0.5', 'sample_height': '148.25', 'sample_type': '', 'er_sample_name': 'new_name', 'sample_azimuth': '5.5', 'sample_lon': '95.4', 'sample_class': ''}
        
        self.assertEqual(output_dict, self.data1.data_er_samples['new_name'])
        self.assertEqual('new_name', self.data1.data_er_samples['new_name']['er_sample_name'])
        self.assertEqual('new_name', self.data1.data_er_specimens[specimen]['er_sample_name'])

    def test_update_site(self):
        specimen = 'Z35.1a'
        sample = 'Z35.1'
        site = 'MGH1'
        
        self.data1.change_site('new_site', site, {'new_key': 'new value', 'site_lon': 99.})
        
        self.assertIn('new_site', self.data1.Data_hierarchy['sites'].keys())
        self.assertEqual(self.data1.Data_hierarchy['site_of_sample'][sample], 'new_site')
        self.assertEqual(self.data1.Data_hierarchy['site_of_specimen'][specimen], 'new_site')
        self.assertIn('new_site', self.data1.Data_hierarchy['locations']['locale'])
        self.assertIn('new_site', self.data1.Data_hierarchy['location_of_site'].keys())
        self.assertEqual('locale', self.data1.Data_hierarchy['location_of_site']['new_site'])
        
        self.assertEqual('new value', self.data1.data_er_sites['new_site']['new_key'])
        self.assertAlmostEqual(99., self.data1.data_er_sites['new_site']['site_lon'])
        self.assertEqual('new_site', self.data1.data_er_sites['new_site']['er_site_name'])
        self.assertEqual('new_site', self.data1.data_er_samples[sample]['er_site_name'])
        self.assertEqual('new_site', self.data1.data_er_specimens[specimen]['er_site_name'])
        
    def test_update_location(self):
        location = 'locale'
        sites = self.data1.Data_hierarchy['locations']['locale']
        site = 'Z35.'
        samples = self.data1.Data_hierarchy['sites'][site]
        sample = 'Z35.1'
        specimens = self.data1.Data_hierarchy['samples'][sample]
        specimen = 'Z35.1a'
        
        self.data1.change_location('new_location', location, {'new_key': 'new value', 'location_type': 'new type'})

        # locations
        self.assertIn('new_location', self.data1.Data_hierarchy['locations'].keys())
        self.assertEqual(sites, self.data1.Data_hierarchy['locations']['new_location'])

        # location_of_site
        self.assertEqual('new_location', self.data1.Data_hierarchy['location_of_site'][site])

        # location_of_sample
        self.assertEqual('new_location', self.data1.Data_hierarchy['location_of_sample'][sample])

        # location_of_specimen
        self.assertEqual('new_location', self.data1.Data_hierarchy['location_of_specimen'][specimen])

        #new data
        self.assertIn('new_key', self.data1.data_er_locations['new_location'].keys())
        self.assertEqual('new type', self.data1.data_er_locations['new_location']['location_type'])
        self.assertEqual('new_location', self.data1.data_er_locations['new_location']['er_location_name'])
        self.assertEqual('new_location', self.data1.data_er_sites[site]['er_location_name'])
        self.assertEqual('new_location', self.data1.data_er_samples[sample]['er_location_name'])
        self.assertEqual('new_location', self.data1.data_er_specimens[specimen]['er_location_name'])


        #Data_hierarchy looks like this: {'sample_of_specimen': {}, 'site_of_sample': {}, 'location_of_specimen', 'locations': {}, 'sites': {}, 'site_of_specimen': {}, 'samples': {}, 'location_of_sample': {}, 'location_of_site': {}, 'specimens': {}}
