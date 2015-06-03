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

    ### test specimens ###
        
    def test_update_specimen(self):
        specimen = 'Z35.6a'
        sample = 'Z35.6'
        site = 'Z35.'
        location = 'locale'
        self.data1.change_specimen('new_specimen', specimen, new_specimen_data={})

        # test Data_hierarchy
        self.assertIn('new_specimen', self.data1.Data_hierarchy['specimens'].keys())
        self.assertEqual(sample, self.data1.Data_hierarchy['sample_of_specimen']['new_specimen'])
        self.assertIn('new_specimen', self.data1.Data_hierarchy['samples'][sample])
        self.assertIn('new_specimen', self.data1.Data_hierarchy['site_of_specimen'].keys())
        self.assertEqual(site, self.data1.Data_hierarchy['site_of_specimen']['new_specimen'])
        self.assertIn('new_specimen', self.data1.Data_hierarchy['location_of_specimen'].keys())
        self.assertEqual(location, self.data1.Data_hierarchy['location_of_specimen']['new_specimen'])

        # test data_er_specimens
        self.assertIn('new_specimen', self.data1.data_er_specimens.keys())
        self.assertEqual('new_specimen', self.data1.data_er_specimens['new_specimen']['er_specimen_name'])

    def test_update_specimen_change_sample(self):
        specimen = 'Z35.6a'
        sample = 'Z35.6'
        site = 'Z35.'
        location = 'locale'
        print "self.data1.Data_hierarchy['samples']", self.data1.Data_hierarchy['samples']
        self.data1.change_specimen(specimen, specimen, new_specimen_data={'er_sample_name': 'Z35.5'})
        print "after: self.data1.Data_hierarchy['samples']", self.data1.Data_hierarchy['samples']
        self.assertIn(specimen, self.data1.Data_hierarchy['samples']['Z35.5'])
        self.assertFalse(self.data1.Data_hierarchy['samples']['Z35.6']) # should be empty, no more specimens
        self.assertEqual('Z35.5', self.data1.Data_hierarchy['sample_of_specimen'][specimen])
        #print self.data1.Data_hierarchy['sample_of_specimen'][specimen]

    def test_add_specimen(self):
        specimen = 'new_specimen_name'
        sample = 'Z35.6'
        self.data1.add_specimen(specimen, sample)

        self.assertIn(specimen, self.data1.Data_hierarchy['specimens'].keys())
        self.assertIn(specimen, self.data1.data_er_specimens.keys())
        self.assertEqual(sample, self.data1.data_er_specimens[specimen]['er_sample_name'])
        self.assertIn(specimen, self.data1.Data_hierarchy['samples'][sample])
        self.assertEqual(sample, self.data1.Data_hierarchy['sample_of_specimen'])
        

    def test_add_specimen_invalid_sample(self):
        specimen = 'new_specimen_name'
        sample = 'invalid sample'
        self.assertRaises(Exception, self.data1.add_specimen, specimen, sample, {'new_key': 'new value'})
        
        
    def test_add_specimen_with_data(self):
        specimen = 'new_specimen_name'
        sample = 'Z35.6'
        self.data1.add_specimen(specimen, 'Z35.6', {'new_key': 'new value'})

        self.assertIn(specimen, self.data1.data_er_specimens.keys())
        self.assertEqual('new value', self.data1.data_er_specimens[specimen]['new_key'])
        for key in self.data1.er_specimens_header:
            self.assertIn(key, self.data1.data_er_specimens[specimen].keys())

            
    #### test samples ####
    
    def test_update_sample(self):
        # set up
        samples = self.data1.data_er_samples.keys()
        specimen = 'Z35.5a'
        self.data1.change_sample('new_name', 'Z35.5', {'new_key': 'new value', 'er_location_name': 'different location'})

        # test Data_hierarchy
        self.assertEqual(self.data1.Data_hierarchy['sample_of_specimen'][specimen], 'new_name')
        self.assertEqual(self.data1.Data_hierarchy['specimens'][specimen], 'new_name')
        self.assertIn('new_name', self.data1.Data_hierarchy['samples'].keys())
        self.assertEqual(self.data1.Data_hierarchy['site_of_sample']['new_name'], 'Z35.')   
        self.assertIn('new_name', self.data1.Data_hierarchy['sites']['Z35.'])
        self.assertEqual(self.data1.Data_hierarchy['location_of_sample']['new_name'], 'locale')

        # test data_er_samples/data_er_specimens
        output_dict = {'new_key': 'new value', 'sample_bed_dip_direction': '444.5', 'er_citation_names': 'This study', 'sample_lithology': '', 'er_site_name': 'Z35.', 'sample_dip': '-82.0', 'magic_method_codes': 'SO-CMD-NORTH', 'sample_lat': '47.1', 'sample_bed_dip': '55.0', 'er_location_name': 'different location', 'sample_declination_correction': '0.5', 'sample_height': '148.25', 'sample_type': '', 'er_sample_name': 'new_name', 'sample_azimuth': '5.5', 'sample_lon': '95.4', 'sample_class': ''}
        
        self.assertEqual(output_dict, self.data1.data_er_samples['new_name'])
        self.assertEqual('new_name', self.data1.data_er_samples['new_name']['er_sample_name'])
        self.assertEqual('new_name', self.data1.data_er_specimens[specimen]['er_sample_name'])
        

    def test_update_sample_change_site(self):
        # set up
        sample = 'Z35.5'
        old_site = 'Z35.'
        new_site = 'MGH1'
        specimen = 'Z35.5a'
        self.data1.change_sample(sample, sample, {'er_site_name': new_site})

        self.assertNotIn('Z35.5', self.data1.Data_hierarchy['sites'][old_site])
        self.assertIn('Z35.5', self.data1.Data_hierarchy['sites'][new_site])
        self.assertNotIn('Z35.5', self.data1.Data_hierarchy['sites'][old_site])
        self.assertEqual(new_site, self.data1.Data_hierarchy['site_of_sample'][sample])
        self.assertEqual(new_site, self.data1.Data_hierarchy['site_of_specimen'][specimen])
        
    def test_add_sample(self):
        new_sample = 'new sample'
        site = 'Z35.'
        self.data1.add_sample(new_sample, site)
        
        self.assertIn(new_sample, self.data1.Data_hierarchy['samples'].keys())
        self.assertIn(new_sample, self.data1.data_er_samples.keys())
        self.assertIn(new_sample, self.data1.Data_hierarchy['sites'][site])
        self.assertEqual(site, self.data1.data_er_samples[new_sample]['er_site_name'])
        self.assertEqual(site, self.data1.Data_hierarchy['site_of_sample'][new_sample])

    def test_add_sample_invalid_site(self):
        sample = 'new_sample_name'
        site = 'invalid site name'
        self.assertRaises(Exception, self.data1.add_site, sample, site, {'new_key': 'new value'})

    def test_add_sample_with_data(self):
        sample = 'new sample name'
        site = 'Z35.'
        self.data1.add_sample(sample, site, {'new_key': 'new value'})

        self.assertIn(sample, self.data1.data_er_samples.keys())
        self.assertEqual('new value', self.data1.data_er_samples[sample]['new_key'])
        for key in self.data1.er_samples_header:
            self.assertIn(key, self.data1.data_er_samples[sample].keys())
                      
    ### test sites ###

    def test_update_site(self):
        # set up
        specimen = 'Z35.1a'
        sample = 'Z35.1'
        site = 'MGH1'
        self.data1.change_site('new_site', site, {'new_key': 'new value', 'site_lon': 99.})

        # test Data_hierarchy
        self.assertIn('new_site', self.data1.Data_hierarchy['sites'].keys())
        self.assertEqual(self.data1.Data_hierarchy['site_of_sample'][sample], 'new_site')
        self.assertEqual(self.data1.Data_hierarchy['site_of_specimen'][specimen], 'new_site')
        self.assertIn('new_site', self.data1.Data_hierarchy['locations']['locale'])
        self.assertIn('new_site', self.data1.Data_hierarchy['location_of_site'].keys())
        self.assertEqual('locale', self.data1.Data_hierarchy['location_of_site']['new_site'])

        # test data_er_sites, data_er_ages, data_er_samples, data_er_specimens
        self.assertEqual('new value', self.data1.data_er_sites['new_site']['new_key'])
        self.assertAlmostEqual(99., self.data1.data_er_sites['new_site']['site_lon'])
        self.assertEqual('new_site', self.data1.data_er_sites['new_site']['er_site_name'])
        self.assertEqual('new_site', self.data1.data_er_samples[sample]['er_site_name'])
        self.assertEqual('new_site', self.data1.data_er_specimens[specimen]['er_site_name'])
        self.assertIn('new_site', self.data1.data_er_ages.keys())
        self.assertEqual('new_site', self.data1.data_er_ages['new_site']['er_site_name'])

        
    def test_update_site_change_location(self):
        # set up
        specimen = 'Z35.1a'
        sample = 'Z35.1'
        site = 'MGH1'
        self.data1.add_location('new_location')
        self.data1.change_site(site, site, {'er_location_name': 'new_location'})
        new_loc = 'new_location'
        old_loc = 'locale'

        self.assertNotIn(site, self.data1.Data_hierarchy['locations'][old_loc])
        self.assertIn(site, self.data1.Data_hierarchy['locations'][new_loc])
        self.assertEqual(new_loc, self.data1.Data_hierarchy['location_of_site'][site])
        self.assertEqual(new_loc, self.data1.Data_hierarchy['location_of_sample'][sample])
        self.assertEqual(new_loc, self.data1.data_er_samples[sample]['er_location_name'])
        self.assertEqual(new_loc, self.data1.Data_hierarchy['location_of_specimen'][specimen])
        if 'er_location_name' in self.data1.data_er_specimens[specimen].keys():
            self.assertEqual(new_loc, self.data1.data_er_specimens[specimen]['er_location_name'])


    def test_add_site(self):
        site = 'new_site_name'
        location = 'locale'
        self.data1.add_site(site, location)

        self.assertIn(site, self.data1.Data_hierarchy['sites'].keys())
        self.assertIn(site, self.data1.Data_hierarchy['locations'][location])
        self.assertIn(site, self.data1.data_er_sites.keys())
        self.assertEqual(location, self.data1.data_er_sites[site]['er_location_name'])
        self.assertEqual(location, self.data1.Data_hierarchy['location_of_site'][site])

    def test_add_site_invalid_location(self):
        site = 'new_site_name'
        location = 'invalid location'
        self.assertRaises(Exception, self.data1.add_site, site, location)

    def test_add_site_with_data(self):
        site = 'new_site_name'
        location = 'locale'
        self.data1.add_site(site, location, {'new_key': 'new value', 'site_type': 'type1'})

        self.assertIn(site, self.data1.data_er_sites.keys())
        self.assertIn('new_key', self.data1.data_er_sites[site].keys())
        self.assertEqual('new value', self.data1.data_er_sites[site]['new_key'])
        self.assertEqual('type1', self.data1.data_er_sites[site]['site_type'])
        for key in self.data1.er_sites_header:
            self.assertIn(key, self.data1.data_er_sites[site].keys())
                            
    ### test locations ###
        
    def test_update_location(self):
        # set up
        location = 'locale'
        sites = self.data1.Data_hierarchy['locations']['locale']
        site = 'Z35.'
        samples = self.data1.Data_hierarchy['sites'][site]
        sample = 'Z35.1'
        specimens = self.data1.Data_hierarchy['samples'][sample]
        specimen = 'Z35.1a'
        self.data1.change_location('new_location', location, {'new_key': 'new value', 'location_type': 'new type'})

        # test Data_hierarchy
        # locations
        self.assertIn('new_location', self.data1.Data_hierarchy['locations'].keys())
        self.assertEqual(sites, self.data1.Data_hierarchy['locations']['new_location'])

        # location_of_site
        self.assertEqual('new_location', self.data1.Data_hierarchy['location_of_site'][site])

        # location_of_sample
        self.assertEqual('new_location', self.data1.Data_hierarchy['location_of_sample'][sample])

        # location_of_specimen
        self.assertEqual('new_location', self.data1.Data_hierarchy['location_of_specimen'][specimen])

        #test data_er_locations, data_er_sites, data_er_specimens
        self.assertIn('new_key', self.data1.data_er_locations['new_location'].keys())
        self.assertEqual('new type', self.data1.data_er_locations['new_location']['location_type'])
        self.assertEqual('new_location', self.data1.data_er_locations['new_location']['er_location_name'])
        self.assertEqual('new_location', self.data1.data_er_sites[site]['er_location_name'])
        self.assertEqual('new_location', self.data1.data_er_samples[sample]['er_location_name'])
        self.assertEqual('new_location', self.data1.data_er_specimens[specimen]['er_location_name'])

    def test_add_location(self):
        location = 'new_location_name'
        print self.data1.er_locations_header
        self.data1.add_location(location)

        self.assertIn(location, self.data1.Data_hierarchy['locations'].keys())
        self.assertIn(location, self.data1.data_er_locations.keys())
        for key in self.data1.er_locations_header:
            self.assertIn(key, self.data1.data_er_locations[location].keys())

    def test_add_location_with_data(self):
        location = 'new_location_name'
        self.data1.add_location(location, {'new_key': 'new value'})
        
        self.assertIn('new_key', self.data1.data_er_locations[location].keys())
        self.assertEqual('new value', self.data1.data_er_locations[location]['new_key'])


    ### test ages ###
        
    def test_change_age(self):
        # set up
        site = 'Z35.'
        self.data1.change_age('new_site_name', site, {'age_unit': 'new unit', 'new_key': 'new value'})

        # test data_er_ages
        self.assertIn('new_site_name', self.data1.data_er_ages.keys())
        self.assertEqual('new_site_name', self.data1.data_er_ages['new_site_name']['er_site_name'])
        self.assertIn('new_key', self.data1.data_er_ages['new_site_name'].keys())
        self.assertEqual('new value', self.data1.data_er_ages['new_site_name']['new_key'])

        #{'Z35.': {'er_citation_names': 'This study', 'er_site_name': 'Z35.', 'magic_method_codes': 'GM-ARAR', 'age_description': '', 'age_unit': 'Ma', 'er_location_name': 'locale', 'age': '3'}, 'MGH1': {'er_citation_names': 'This study', 'er_site_name': 'MGH1', 'magic_method_codes': 'GM-ARAR', 'age_description': '', 'age_unit': 'Ga', 'er_location_name': 'locale', 'age': '3'}}
        

    def test_age_no_name_change(self):
        site = 'Z35.'
        self.data1.change_age(site, site, {'age': '4', 'new_key': 'new value'})

        self.assertIn('Z35.', self.data1.data_er_ages.keys())
        self.assertEqual('Z35.', self.data1.data_er_ages[site]['er_site_name'])
        self.assertEqual('4', self.data1.data_er_ages[site]['age'])
        self.assertIn('new_key', self.data1.data_er_ages[site].keys())
        self.assertEqual('new value', self.data1.data_er_ages[site]['new_key'])
