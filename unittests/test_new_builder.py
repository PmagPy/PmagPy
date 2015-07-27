#!/usr/bin/env python

# pylint: disable=C0303,W0612,C0303,C0111,C0301

"""
Tests for new ErMagicBuilder
"""

import unittest   
import os
import builder
#import pmag    
#import ipmag
#import matplotlib
WD = os.getcwd()


class TestBuilder(unittest.TestCase):
    """
    Test ErMagicBuilder data structure
    """

    def setUp(self):
        dir_path = os.path.join(WD, 'Datafiles', 'copy_ErMagicBuilder')
        self.data1 = builder.ErMagicBuilder(dir_path)
        self.data1.get_data()
        #self.data2 = builder.ErMagicBuilder(WD)
        #self.data2.get_data()

    def tearDown(self):
        pass

    def test_data_creation(self):
        self.assertTrue(self.data1.specimens)

    def test_find_by_name(self):
        specimen = builder.Specimen('a', 'specimen', self.data1.data_model)
        specimen2 = builder.Specimen('b', 'specimen', self.data1.data_model)
        specimen3 = builder.Specimen('c', 'specimen', self.data1.data_model)
        lst = [specimen, specimen2]
        self.assertFalse(self.data1.find_by_name('c', lst))
        self.assertTrue(self.data1.find_by_name('b', lst))

class TestSpecimen(unittest.TestCase):

    def setUp(self):
        dir_path = os.path.join(WD, 'Datafiles', 'copy_ErMagicBuilder')
        self.data1 = builder.ErMagicBuilder(dir_path)
        self.data1.get_data()
        #self.data2 = builder.ErMagicBuilder(WD)
        #self.data2.get_data()

    def tearDown(self):
        pass

    def test_get_parent(self):
        spec_name = 'Z35.6a'
        samp_name = 'Z35.6'
        specimen = self.data1.find_by_name(spec_name, self.data1.specimens)
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        self.assertEqual(specimen.get_parent(), sample)

    def test_set_parent(self):
        spec_name = 'Z35.6a'
        samp_name = 'Z35.6'
        new_samp_name = 'Z35.2'
        specimen = self.data1.find_by_name(spec_name, self.data1.specimens)
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        new_sample = self.data1.find_by_name(new_samp_name, self.data1.samples)
        self.assertEqual(specimen.sample, sample)
        specimen.set_parent(new_sample)
        self.assertEqual(specimen.sample, new_sample)

    def test_set_parent_wrong_type(self):
        spec_name = 'Z35.6a'
        site_name = 'Z35.'
        specimen = self.data1.find_by_name(spec_name, self.data1.specimens)
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertRaises(Exception, specimen.set_parent, site)

        

    def test_update_specimen(self):
        specimen_name = 'Z35.6a'
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        location_name = 'locale'
        self.data1.change_specimen(specimen_name, 'new_specimen', new_sample_name=None, new_er_data=None)

        specimen = self.data1.find_by_name('new_specimen', self.data1.specimens)
        self.assertTrue(specimen)
        self.assertIn('new_specimen', [spec.name for spec in self.data1.specimens])
        self.assertEqual(sample_name, specimen.sample.name)
        self.assertEqual(site_name, specimen.sample.site.name)
        self.assertEqual(location_name, specimen.sample.site.location.name)

    def test_update_specimen_invalid_name(self):
        specimen_name = 'Z35.6a_fake'
        sample_name = 'Z35.6'
        result = self.data1.change_specimen(specimen_name, 'new_specimen')
        self.assertFalse(result)


    def test_update_specimen_change_sample(self):
        specimen_name = 'Z35.6a'
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        location_name = 'locale'
        new_sample_name = 'Z35.2'
        sample = self.data1.find_by_name(new_sample_name, self.data1.samples)
        self.data1.change_specimen(specimen_name, specimen_name, new_sample_name, new_er_data={'er_sample_name': 'Z35.5'})
        
        specimen = self.data1.find_by_name(specimen_name, self.data1.specimens)
        self.assertTrue(specimen)
        self.assertEqual(specimen.sample.name, new_sample_name)
        old_sample = self.data1.find_by_name(sample_name, self.data1.samples)
        new_sample = self.data1.find_by_name(new_sample_name, self.data1.samples)
        self.assertTrue(old_sample)
        self.assertNotIn(specimen, old_sample.specimens)
        self.assertTrue(new_sample)
        self.assertIn(specimen, new_sample.specimens)

    def test_update_specimen_with_er_data(self):
        specimen_name = 'Z35.6a'
        self.data1.change_specimen(specimen_name, specimen_name, new_er_data={'specimen_elevation': 12})
        specimen = self.data1.find_by_name('Z35.6a', self.data1.specimens)
        self.assertTrue(specimen)
        self.assertIn('specimen_elevation', specimen.er_data.keys())
        self.assertEqual(12, specimen.er_data['specimen_elevation'])
        # change again (should overwrite)
        self.data1.change_specimen(specimen_name, specimen_name, new_er_data={'specimen_elevation': 92})
        self.assertIn('specimen_elevation', specimen.er_data.keys())
        self.assertEqual(92, specimen.er_data['specimen_elevation'])

        
    def test_update_specimen_with_pmag_data(self):
        specimen_name = 'Z35.6a'
        specimen = self.data1.find_by_name('Z35.6a', self.data1.specimens)
        self.data1.get_pmag_magic_info('specimen', 'sample')
        self.data1.change_specimen(specimen_name, specimen_name, new_pmag_data={'er_fossil_name': 'Mr. Bone'})
        self.assertTrue(specimen)
        # make sure new data is added in 
        self.assertIn('er_fossil_name', specimen.pmag_data.keys())
        self.assertEqual('Mr. Bone', specimen.pmag_data['er_fossil_name'])
        # make sure old data hasn't disappeared
        self.assertIn('magic_experiment_names', specimen.pmag_data.keys())
        self.assertEqual('Z35.6a:LP-DIR-T', specimen.pmag_data['magic_experiment_names'])
        

    def test_update_specimen_with_invalid_sample(self):
        specimen_name = 'Z35.6a'
        site_name = 'invalid_site'
        self.data1.change_specimen(specimen_name, specimen_name, site_name) 
        specimen = self.data1.find_by_name('Z35.6a', self.data1.specimens)
        sample = self.data1.find_by_name('Z35.6', self.data1.samples)
        self.assertTrue(specimen)
        self.assertEqual(sample, specimen.sample)

        specimen.sample = ""
        self.data1.change_specimen(specimen_name, specimen_name, site_name)
        self.assertEqual('', specimen.sample)

    def test_add_specimen(self):
        spec_name = 'new specimen'
        specimen = self.data1.add_specimen(spec_name)
        #specimen = self.data1.find_by_name(spec_name, self.data1.specimens)
        self.assertTrue(specimen)
        self.assertIn(specimen, self.data1.specimens)
        self.assertEqual('', specimen.sample)
        self.assertTrue(specimen.er_data)
        self.assertTrue(specimen.pmag_reqd_headers)
        self.assertTrue(specimen.er_reqd_headers)
        
    def test_add_specimen_with_sample(self):
        spec_name = 'new specimen'
        samp_name = 'Z35.6'
        self.data1.add_specimen(spec_name, samp_name)
        specimen = self.data1.find_by_name(spec_name, self.data1.specimens)
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        self.assertTrue(specimen)
        self.assertIn(specimen, self.data1.specimens)
        self.assertTrue(sample)
        self.assertEqual(sample, specimen.sample)

    def test_add_specimen_invalid_sample(self):
        spec_name = 'new specimen'
        samp_name = 'nonexistent_sample'
        self.data1.add_specimen(spec_name, samp_name)
        specimen = self.data1.find_by_name(spec_name, self.data1.specimens)
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        self.assertTrue(specimen)
        self.assertIn(specimen, self.data1.specimens)
        self.assertFalse(sample)
        self.assertEqual('', specimen.sample)

    def test_add_specimen_with_er_data(self):
        specimen_name = 'new_spec'
        self.data1.add_specimen(specimen_name, er_data={'specimen_type': 'special', 'specimen_elevation': 22})
        
        specimen = self.data1.find_by_name(specimen_name, self.data1.specimens)

        self.assertNotIn('er_specimen_name', specimen.er_data.keys())
        self.assertNotIn('er_sample_name', specimen.er_data.keys())
        self.assertNotIn('er_site_name', specimen.er_data.keys())
        self.assertNotIn('er_location_name', specimen.er_data.keys())
        self.assertEqual('special', specimen.er_data['specimen_type'])
        self.assertIn('specimen_elevation', specimen.er_data.keys())
        self.assertEqual(22, specimen.er_data['specimen_elevation'])

    def test_add_specimen_with_pmag_data(self):
        specimen_name = 'new_spec'
        self.data1.add_specimen(specimen_name, pmag_data={'specimen_gamma': 10.5, 'specimen_description': 'cool'})
        specimen = self.data1.find_by_name(specimen_name, self.data1.specimens)

        self.assertNotIn('er_specimen_name', specimen.pmag_data.keys())
        self.assertNotIn('er_sample_name', specimen.pmag_data.keys())
        self.assertNotIn('er_site_name', specimen.pmag_data.keys())
        self.assertNotIn('er_location_name', specimen.pmag_data.keys())
        self.assertIn('specimen_gamma', specimen.pmag_data.keys())
        self.assertEqual(10.5, specimen.pmag_data['specimen_gamma'])
        self.assertIn('specimen_description', specimen.pmag_data.keys())
        self.assertEqual('cool', specimen.pmag_data['specimen_description'])


    def test_delete_specimen(self):
        specimen_name = 'Z35.6a'
        sample_name = 'Z35.6'
        self.data1.delete_specimen(specimen_name)

        specimen = self.data1.find_by_name(specimen_name, self.data1.specimens)
        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        self.assertFalse(specimen)
        self.assertTrue(sample)
        self.assertNotIn(specimen_name, [spec.name for spec in sample.specimens])
        self.assertNotIn(specimen_name, [spec.name for spec in self.data1.specimens])

    def test_er_data(self):
        spec_name = 'Z35.6a'
        specimen = self.data1.find_by_name(spec_name, self.data1.specimens)
        self.assertTrue(specimen)
        self.assertTrue(specimen.er_data)
        for key in specimen.er_data.keys():
            self.assertEqual('', specimen.er_data[key])
        #self.data1.get_spec_data()
        self.data1.get_er_magic_info('specimen', 'sample')
        self.assertEqual('This study', specimen.er_data['er_citation_names'])
        self.assertEqual('Archeologic', specimen.er_data['specimen_class'])
        self.assertEqual('s', specimen.er_data['specimen_type'])
        self.assertEqual('Baked Clay', specimen.er_data['specimen_lithology'])

    def test_pmag_data(self):
        spec_name = 'Z35.6a'
        specimen = self.data1.find_by_name(spec_name, self.data1.specimens)
        self.assertTrue(specimen)
        self.assertTrue(specimen.pmag_data)
        for key in specimen.pmag_data.keys():
            self.assertEqual('', specimen.pmag_data[key])
        self.assertIn('er_citation_names', specimen.pmag_data.keys())
        self.assertNotIn('pmag_rotation_codes', specimen.pmag_data.keys())
        
        self.data1.get_pmag_magic_info('specimen', 'sample')
        
        self.assertIn('measurement_step_max', specimen.pmag_data.keys())
        self.assertEqual(828, int(specimen.pmag_data['measurement_step_max']))
        self.assertIn('magic_experiment_names', specimen.pmag_data.keys())
        self.assertEqual('Z35.6a:LP-DIR-T', specimen.pmag_data['magic_experiment_names'])



class TestSample(unittest.TestCase):

    def setUp(self):
        dir_path = os.path.join(WD, 'Datafiles', 'copy_ErMagicBuilder')
        self.data1 = builder.ErMagicBuilder(dir_path)
        self.data1.get_data()


    def test_get_parent(self):
        samp_name = 'Z35.6'
        site_name = 'Z35.'
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertEqual(sample.get_parent(), site)

    def test_set_parent(self):
        samp_name = 'Z35.6'
        site_name = 'Z35.'
        new_site_name = 'Z35.2'
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        site = self.data1.find_by_name(site_name, self.data1.sites)
        new_site = self.data1.find_by_name(new_site_name, self.data1.sites)
        self.assertEqual(sample.site, site)
        sample.set_parent(new_site)
        self.assertEqual(sample.site, new_site)

    def test_set_parent_wrong_type(self):
        spec_name = 'Z35.6a'
        samp_name = 'Z35.6'
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        specimen = self.data1.find_by_name(spec_name, self.data1.specimens)
        self.assertRaises(Exception, sample.set_parent, specimen)


    def test_update_sample(self):
        specimen_name = 'Z35.6a'
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        location_name = 'locale'
        self.data1.change_sample(sample_name, 'new_sample', new_site_name=None, new_er_data=None)

        specimen = self.data1.find_by_name(specimen_name, self.data1.specimens)
        sample = self.data1.find_by_name('new_sample', self.data1.samples)
        self.assertTrue(sample)
        self.assertIn(sample, self.data1.samples)
        self.assertEqual('new_sample', sample.name)
        self.assertEqual(specimen.sample, sample)
        self.assertIn(specimen, sample.specimens)
        self.assertEqual(site_name, sample.site.name)
        self.assertEqual(location_name, sample.site.location.name)

    def test_update_sample_change_site(self):
        specimen_name = 'Z35.6a'
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        location_name = 'locale'
        new_site_name = 'MGH1'
        
        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        
        self.data1.change_sample(sample_name, sample_name, new_site_name=new_site_name, new_er_data=None)

        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        new_site = self.data1.find_by_name(new_site_name, self.data1.sites)
        old_site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertTrue(sample)
        self.assertTrue(new_site)
        self.assertTrue(old_site)
        self.assertEqual(new_site, sample.site)
        self.assertIn(sample, new_site.samples)
        self.assertNotIn(sample, old_site.samples)


    def test_update_sample_with_er_data(self):
        sample_name = 'Z35.6'
        sample = self.data1.find_by_name(sample_name, self.data1.samples)

        self.data1.change_sample(sample_name, sample_name, new_er_data={'sample_type': 'awesome', 'sample_alteration_type': 'awesomer'})
        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        self.assertTrue(sample)
        self.assertIn('sample_alteration_type', sample.er_data.keys())
        self.assertEqual('awesomer', sample.er_data['sample_alteration_type'])
        self.assertEqual('awesome', sample.er_data['sample_type'])
        # change again (should overwrite)
        self.data1.change_sample(sample_name, sample_name, new_er_data={'sample_type': 'cool'})
        self.assertEqual('cool', sample.er_data['sample_type'])

    def test_update_sample_with_pmag_data(self):
        sample_name = 'Z35.6'
        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        self.data1.get_pmag_magic_info('sample', 'site')
        self.assertIn('magic_instrument_codes', sample.pmag_data.keys())
        self.assertNotIn('er_mineral_names', sample.pmag_data.keys())
        self.data1.change_sample(sample_name, sample_name, new_pmag_data={'er_mineral_names': 'awesome', 'magic_instrument_codes': '12345'})
        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        self.assertTrue(sample)
        # make sure new data is added in
        self.assertIn('er_mineral_names', sample.pmag_data.keys())
        self.assertEqual('awesome', sample.pmag_data['er_mineral_names'])
        self.assertIn('magic_instrument_codes', sample.pmag_data.keys())
        self.assertEqual('12345', sample.pmag_data['magic_instrument_codes'])

        
    def test_update_sample_with_invalid_site(self):
        sample_name = 'Z35.6'
        site_name = 'invalid site name'
        #self.assertRaises(Exception, self.data1.add_sample, sample, site, {'new_key': 'new value'})
        self.data1.change_sample(sample_name, sample_name, new_site_name=site_name, new_er_data=None)
        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        self.assertTrue(sample)
        self.assertEqual('Z35.', sample.site.name)

    def test_add_sample(self):
        samp_name = 'new_sample'
        sample = self.data1.add_sample(samp_name)
        self.assertTrue(sample)
        self.assertEqual('', sample.site)
        self.assertIn(sample, self.data1.samples)
        self.assertTrue(sample.er_data)
        self.assertTrue(sample.pmag_reqd_headers)
        self.assertTrue(sample.er_reqd_headers)

    def test_add_sample_with_site(self):
        samp_name = 'new_samp'
        site_name = 'MGH1'
        sample = self.data1.add_sample(samp_name, site_name)
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertTrue(sample)
        self.assertTrue(site)
        self.assertEqual(site, sample.site)

    def test_add_sample_invalid_site(self):
        samp_name = 'new_samp'
        site_name = 'invalid_site'
        sample = self.data1.add_sample(samp_name, site_name)
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertTrue(sample)
        self.assertFalse(site)
        self.assertEqual('', sample.site)

    def test_add_sample_with_er_data(self):
        samp_name = 'new_samp'
        site_name = 'MGH1'
        sample = self.data1.add_sample(samp_name, site_name, {'sample_type': 'excellent', 'sample_texture': 'rough'})
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertTrue(sample)
        self.assertTrue(site)
        self.assertIn('sample_type', sample.er_data.keys())
        self.assertEqual('excellent', sample.er_data['sample_type'])
        self.assertIn('rough', sample.er_data['sample_texture'])

    def test_add_sample_with_pmag_data(self):
        samp_name = 'new_samp'
        site_name = 'MGH1'
        sample = self.data1.add_sample(samp_name, site_name, pmag_data={'er_mineral_names': 'awesome', 'magic_instrument_codes': '12345'})
        self.assertTrue(sample)
        self.assertIn('er_mineral_names', sample.pmag_data.keys())
        self.assertEqual('awesome', sample.pmag_data['er_mineral_names'])
        self.assertIn('magic_instrument_codes', sample.pmag_data.keys())
        self.assertEqual('12345', sample.pmag_data['magic_instrument_codes'])


    def test_delete_sample(self):
        specimen_name = 'Z35.6a'
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        self.data1.delete_sample(sample_name)

        specimen = self.data1.find_by_name(specimen_name, self.data1.specimens)
        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertTrue(specimen)
        self.assertFalse(sample)
        self.assertTrue(site)
        self.assertEqual('', specimen.sample)
        self.assertNotIn(sample_name, [samp.name for samp in site.samples])
        
        self.assertNotIn(sample_name, [samp.name for samp in self.data1.samples])

    def test_er_data(self):
        samp_name = 'Z35.6'
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        self.assertTrue(sample)
        self.assertTrue(sample.er_data)
        for key in sample.er_data.keys():
            self.assertEqual('', sample.er_data[key])
        self.data1.get_er_magic_info('sample', 'site')
        self.assertEqual('This study', sample.er_data['er_citation_names'])
        self.assertEqual('Archeologic', sample.er_data['sample_class'])
        self.assertEqual('s', sample.er_data['sample_type'])
        self.assertEqual('Baked Clay', sample.er_data['sample_lithology'])

    def test_pmag_data(self):
        samp_name = 'Z35.6'
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        self.assertTrue(sample)
        data = sample.pmag_data.copy()
        self.assertTrue(sample.pmag_data)
        for key in sample.pmag_data.keys():
            self.assertEqual('', sample.pmag_data[key])
        self.data1.get_pmag_magic_info('sample', 'site')
        data2 = sample.pmag_data
        self.assertEqual(data, data2)

        

class TestSite(unittest.TestCase):

    def setUp(self):
        dir_path = os.path.join(WD, 'Datafiles', 'copy_ErMagicBuilder')
        self.data1 = builder.ErMagicBuilder(dir_path)
        self.data1.get_data()


    def test_get_parent(self):
        site_name = 'Z35.'
        loc_name = 'locale'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        location = self.data1.find_by_name(loc_name, self.data1.locations)
        self.assertEqual(site.get_parent(), location)

    def test_set_parent(self):
        site_name = 'Z35.'
        loc_name = 'locale'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        location = self.data1.find_by_name(loc_name, self.data1.locations)
        new_location = builder.Location('new_location', None, data_model=self.data1.data_model)
        self.assertEqual(site.location, location)
        site.set_parent(new_location)
        self.assertEqual(site.location, new_location)


    def test_set_parent_wrong_type(self):
        site_name = 'MGH1'
        samp_name = 'Z35.6'
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertRaises(Exception, site.set_parent, sample)

        
    def test_update_site(self):
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        location_name = 'locale'

        site = self.data1.find_by_name(site_name, self.data1.sites)
        samples = site.samples
        self.data1.change_site(site_name, 'new_site', new_location_name=None)
        site = self.data1.find_by_name('new_site', self.data1.sites)
        location = self.data1.find_by_name(location_name, self.data1.locations)
        self.assertTrue(site)
        self.assertTrue(location)
        self.assertEqual(site.location, location)
        for samp in site.samples:
            self.assertIn(samp, samples)
        for samp in samples:
            self.assertEqual(samp.site, site)
        # see that old site no longer exists
        old_site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertFalse(old_site)

    def test_update_site_change_location(self):
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        location_name = 'locale'
        new_location_name = 'Munich'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        old_location = self.data1.find_by_name(location_name, self.data1.locations)
        location = self.data1.find_by_name(new_location_name, self.data1.locations)
        
        self.data1.change_site(site_name, 'new_site', new_location_name=new_location_name, new_er_data=None)
        self.assertTrue(site)
        self.assertTrue(old_location)
        self.assertTrue(location)
        self.assertEqual(site.location, location)
        self.assertIn(site, location.sites)
        self.assertNotIn(site, old_location.sites)
        

    def test_update_site_with_er_data(self):
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        location_name = 'locale'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        location = self.data1.find_by_name(location_name, self.data1.locations)
        self.assertIn('site_type', site.er_data.keys())
        self.assertEqual('', site.er_data['site_type'])
        self.data1.change_site(site_name, 'new_site', new_er_data={'site_type': 'great', 'site_elevation': 10})

        self.assertTrue(site)
        self.assertEqual(site.name, 'new_site')
        self.assertIn('site_type', site.er_data.keys())
        self.assertEqual('great', site.er_data['site_type'])
        self.assertIn('site_elevation', site.er_data.keys())
        self.assertEqual(10, site.er_data['site_elevation'])

        self.data1.change_site('new_site', 'new_site', new_er_data={'site_type': 'great', 'site_elevation': 99})
        self.assertEqual(99, site.er_data['site_elevation'])

    def test_update_site_with_pmag_data(self):
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        location_name = 'locale'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        location = self.data1.find_by_name(location_name, self.data1.locations)
        self.assertIn('magic_method_codes', site.pmag_data.keys())
        self.assertFalse(site.pmag_data['magic_method_codes'])
        self.assertNotIn('site_sigma', site.pmag_data.keys())
        self.data1.change_site(site_name, 'new_site', new_pmag_data={'site_sigma': 3, 'magic_method_codes': 'code'})

        self.assertIn('site_sigma', site.pmag_data.keys())
        self.assertEqual(3, site.pmag_data['site_sigma'])
        self.assertIn('magic_method_codes', site.pmag_data.keys())
        self.assertEqual('code', site.pmag_data['magic_method_codes'])


        
    def test_update_site_invalid_location(self):
        site_name = 'Z35.'
        location_name = 'locale'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        location = self.data1.find_by_name(location_name, self.data1.locations)
        self.data1.change_site(site_name, 'new_name', new_location_name='invalid_location')
        self.assertTrue(site)
        self.assertEqual(site.name, 'new_name')
        self.assertEqual(site.location, location)

    def test_add_site(self):
        site_name = 'new_site'
        site = self.data1.add_site(site_name)
        self.assertTrue(site)
        self.assertIn(site, self.data1.sites)

    def test_add_site_with_location(self):
        location = self.data1.find_by_name('Munich', self.data1.locations)
        self.assertTrue(location)
        site_name = 'new_site'
        site = self.data1.add_site(site_name, location.name)
        self.assertTrue(site)
        self.assertIn(site, self.data1.sites)
        self.assertIn(site, location.sites)


    def test_add_site_invalid_location(self):
        site_name = 'new_site'
        site = self.data1.add_site(site_name, 'non_existent_location')
        self.assertTrue(site)
        self.assertIn(site, self.data1.sites)
        self.assertEqual('', site.location)

    def test_add_site_with_er_data(self):
        site_name = 'new_site'
        site = self.data1.add_site(site_name, 'Munich', {'site_type': 'great', 'site_elevation': 99})
        self.assertTrue(site)
        self.assertIn('site_type', site.er_data.keys())
        self.assertEqual('great', site.er_data['site_type'])
        self.assertIn('site_elevation', site.er_data.keys())
        self.assertEqual(99, site.er_data['site_elevation'])

    def test_add_site_with_er_data(self):
        site_name = 'new_site'
        site = self.data1.add_site(site_name, 'Munich', pmag_data={'site_sigma': 3, 'magic_method_codes': 'code'})
        self.assertTrue(site)
        self.assertIn('site_sigma', site.pmag_data.keys())
        self.assertEqual(3, site.pmag_data['site_sigma'])
        self.assertIn('magic_method_codes', site.pmag_data.keys())
        self.assertEqual('code', site.pmag_data['magic_method_codes'])


    def test_delete_site(self):
        site_name = 'Z35.'
        location_name = 'locale'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        location = self.data1.find_by_name(location_name, self.data1.locations)
        self.data1.delete_site(site.name)
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertFalse(site)
        self.assertNotIn(site_name, [site.name for site in self.data1.sites])
        self.assertNotIn(site_name, [site.name for site in location.sites])

    def test_er_data(self):
        site_name = 'MGH1'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertTrue(site)
        self.assertTrue(site.er_data)
        for key in site.er_data.keys():
            self.assertEqual('', site.er_data[key])
        self.data1.get_er_magic_info('site', 'location')
        self.assertEqual('This study', site.er_data['er_citation_names'])
        self.assertEqual('Archeologic', site.er_data['site_class'])
        self.assertEqual('Baked Clay', site.er_data['site_type'])
        self.assertEqual('Mafic Dike', site.er_data['site_lithology'])

    def test_pmag_data(self):
        site_name = 'MGH1'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertTrue(site)
        data = site.pmag_data.copy()
        self.assertTrue(site.pmag_data)
        for key in site.pmag_data.keys():
            self.assertEqual('', site.pmag_data[key])
        self.data1.get_pmag_magic_info('site', 'location')
        data2 = site.pmag_data
        self.assertEqual(data, data2)


class TestLocation(unittest.TestCase):

    def setUp(self):
        dir_path = os.path.join(WD, 'Datafiles', 'copy_ErMagicBuilder')
        self.data1 = builder.ErMagicBuilder(dir_path)
        self.data1.get_data()

    def test_parent(self):
        loc_name = 'locale'
        location = self.data1.find_by_name(loc_name, self.data1.locations)
        self.assertFalse(location.get_parent())
        self.assertFalse(location.set_parent())

    def test_update_location(self):
        site_name = 'Z35.'
        location_name = 'locale'
        new_location_name = 'new_location'

        location = self.data1.find_by_name(location_name, self.data1.locations)
        sites = location.sites
        
        self.data1.change_location(location_name, new_location_name, new_er_data=None, new_pmag_data=None)
        location = self.data1.find_by_name(new_location_name, self.data1.locations)
        self.assertTrue(location)
        self.assertIn(location, self.data1.locations)
        for site in sites:
            self.assertEqual(site.location, location)

    def test_update_location_with_invalid_name(self):
        location_name = 'nonexistent'
        result = self.data1.change_location(location_name, location_name)
        self.assertFalse(result)

    def test_update_location_with_er_data(self):
        location_name = 'locale'
        location = self.data1.find_by_name(location_name, self.data1.locations)
        self.assertIn('location_type', location.er_data.keys())
        self.assertEqual('', location.er_data['location_type'])
        self.data1.change_location(location_name, location_name, new_er_data={'location_type': 'great', 'continent_ocean': 'Indian'})
        self.assertIn('location_type', location.er_data.keys())
        self.assertEqual('great', location.er_data['location_type'])
        self.assertIn('continent_ocean', location.er_data.keys())
        self.assertEqual('Indian', location.er_data['continent_ocean'])

        self.data1.change_location(location_name, location_name, {'continent_ocean': 'Atlantic'})
        self.assertEqual('Atlantic', location.er_data['continent_ocean'])

    def test_update_location_with_data_and_name_change(self):
        location_name = 'locale'
        new_location_name = 'new_locale'
        location = self.data1.find_by_name(location_name, self.data1.locations)
        self.assertIn('location_type', location.er_data.keys())
        self.assertEqual('', location.er_data['location_type'])
        self.data1.change_location(location_name, new_location_name, new_er_data={'location_type': 'great', 'continent_ocean': 'Indian'})

        self.assertFalse(self.data1.find_by_name(location_name, self.data1.locations))
        location = self.data1.find_by_name(new_location_name, self.data1.locations)
        self.assertIn('location_type', location.er_data.keys())
        self.assertEqual('great', location.er_data['location_type'])
        self.assertIn('continent_ocean', location.er_data.keys())
        self.assertEqual('Indian', location.er_data['continent_ocean'])

        self.data1.change_location(new_location_name, new_location_name, {'continent_ocean': 'Atlantic'})
        self.assertEqual('Atlantic', location.er_data['continent_ocean'])

    def test_add_location(self):
        location_name = 'new_location'
        location = self.data1.add_location(location_name)
        self.assertTrue(location)
        self.assertIn(location, self.data1.locations)

    def test_add_location_with_data(self):
        location_name = 'new_location'
        location = self.data1.add_location(location_name, er_data={'location_type': 'great', 'continent_ocean': 'Indian'})
        self.assertTrue(location)
        self.assertIn('location_type', location.er_data.keys())
        self.assertEqual('great', location.er_data['location_type'])
        self.assertIn('continent_ocean', location.er_data.keys())
        self.assertEqual('Indian', location.er_data['continent_ocean'])

    def test_delete_location(self):
        location_name = 'Munich'
        location = self.data1.find_by_name(location_name, self.data1.locations)
        sites = location.sites
        self.data1.delete_location(location_name)
        location = self.data1.find_by_name(location_name, self.data1.locations)
        self.assertFalse(location)
        self.assertNotIn(location_name, [loc.name for loc in self.data1.locations])

    def test_location_data(self):
        location_name = 'locale'
        location = self.data1.find_by_name(location_name, self.data1.locations)
        self.assertTrue(location)
        self.assertTrue(location.er_data)
        for key in location.er_data.keys():
            self.assertEqual('', location.er_data[key])
        self.data1.get_er_magic_info('location')
        self.assertEqual('This study', location.er_data['er_citation_names'])
        self.assertEqual('Lake Core', location.er_data['location_type'])
        self.assertEqual(47.1, float(location.er_data['location_begin_lat']))
        self.assertEqual(47.1, float(location.er_data['location_end_lat']))


class TestAge(unittest.TestCase):

    def setUp(self):
        dir_path = os.path.join(WD, 'Datafiles', 'copy_ErMagicBuilder')
        self.data1 = builder.ErMagicBuilder(dir_path)
        self.data1.get_data()

    def test_initialize_age_data_structures(self):
        site_name = 'MGH1'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertTrue(site.age_data)
        self.assertIn('magic_method_codes', site.age_data.keys())
        self.assertNotIn('conodont_zone', site.age_data.keys())
        self.assertNotIn('er_location_name', site.age_data.keys())

    def test_get_age_data(self):
        site_name = 'MGH1'
        site = self.data1.find_by_name(site_name, self.data1.sites)

        self.data1.get_age_info('site')
        #self.assertTrue(self.data1.ages)
        self.assertTrue(site.age_data)
        self.assertEqual(3, int(site.age_data['age']))
        self.assertEqual('GM-ARAR', site.age_data['magic_method_codes'])


class TestResult(unittest.TestCase):

    def setUp(self):
        dir_path = os.path.join(WD, 'Datafiles', 'mk_redo')
        self.data1 = builder.ErMagicBuilder(dir_path)
        #self.data1.get_data()

        self.data1.get_er_magic_info('specimen', 'sample')
        self.data1.get_pmag_magic_info('specimen', 'sample')
        
        self.data1.get_er_magic_info('sample', 'site')
        self.data1.get_pmag_magic_info('sample', 'site')
        
        self.data1.get_er_magic_info('site', 'location')
        self.data1.get_pmag_magic_info('site', 'location')
        
        self.data1.get_er_magic_info('location')
        self.data1.get_age_info('site')

        self.data1.get_results_info()

    def test_results_are_created(self):
        result = self.data1.find_by_name('sr03', self.data1.results)
        specimen = self.data1.find_by_name('sr03a1', self.data1.specimens)
        site = self.data1.find_by_name('sr03', self.data1.sites)
        location = self.data1.find_by_name('Snake River', self.data1.locations)
        self.assertTrue(result)
        self.assertTrue(result.specimens)
        self.assertIn(specimen, result.specimens)
        self.assertFalse(result.samples)
        self.assertTrue(result.sites)
        self.assertIn(site, result.sites)
        self.assertTrue(result.locations)
        self.assertIn(location, result.locations)

    def test_with_change_specimen(self):
        result = self.data1.find_by_name('sr03', self.data1.results)
        specimen = self.data1.find_by_name('sr03a1', self.data1.specimens)
        site = self.data1.find_by_name('sr03', self.data1.sites)
        location = self.data1.find_by_name('Snake River', self.data1.locations)
        self.assertTrue(result)
        self.assertTrue(result.specimens)
        self.assertIn(specimen, result.specimens)
        self.data1.change_specimen('sr03a1', 'new_name')
        self.assertEqual(specimen.name, 'new_name')
        self.assertIn(specimen, result.specimens)
        
    def test_delete_result(self):
        result = self.data1.find_by_name('sr03', self.data1.results)
        self.assertIn(result, self.data1.results)
        self.data1.delete_result(result.name)
        self.assertNotIn(result, self.data1.results)
        
    def test_update_result_name(self):
        result = self.data1.find_by_name('sr03', self.data1.results)
        self.assertIn(result, self.data1.results)
        self.data1.change_result(result.name, 'new_name')
        self.assertEqual(result.name, 'new_name')
        old_result = self.data1.find_by_name('sr03', self.data1.results)
        new_result = self.data1.find_by_name('new_name', self.data1.results)
        self.assertFalse(old_result)
        self.assertTrue(new_result)

    def test_update_result_items(self):
        result = self.data1.find_by_name('sr03', self.data1.results)
        samp_names = 'sr27c', 'sr27a'
        samples = [self.data1.find_by_name(name, self.data1.samples) for name in samp_names]
        site_name = 'sr27'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertFalse(result.samples)
        self.data1.change_result('sr03', 'sr03', None, None, spec_names=None, samp_names=samp_names, site_names=[site_name], loc_names=None)
        self.assertFalse(result.specimens)
        self.assertTrue(result.samples)
        for samp in samples:
            self.assertIn(samp, result.samples)
        self.assertTrue(result.sites)
        self.assertIn(site, result.sites)
        self.assertFalse(result.locations)


