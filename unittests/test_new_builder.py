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


    def test_update_specimen(self):
        specimen_name = 'Z35.6a'
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        location_name = 'locale'
        self.data1.change_specimen(specimen_name, 'new_specimen', new_sample_name=None, new_specimen_data={})

        specimen = self.data1.find_by_name('new_specimen', self.data1.specimens)
        self.assertTrue(specimen)
        self.assertIn('new_specimen', [spec.name for spec in self.data1.specimens])
        self.assertEqual(sample_name, specimen.sample.name)
        self.assertEqual(site_name, specimen.sample.site.name)
        self.assertEqual(location_name, specimen.sample.site.location.name)

    def test_update_specimen_change_sample(self):
        specimen_name = 'Z35.6a'
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        location_name = 'locale'
        new_sample_name = 'Z35.2'
        sample = self.data1.find_by_name(new_sample_name, self.data1.samples)
        self.data1.change_specimen(specimen_name, specimen_name, new_sample_name, new_specimen_data={'er_sample_name': 'Z35.5'})
        
        specimen = self.data1.find_by_name(specimen_name, self.data1.specimens)
        self.assertTrue(specimen)
        self.assertEqual(specimen.sample.name, new_sample_name)
        old_sample = self.data1.find_by_name(sample_name, self.data1.samples)
        new_sample = self.data1.find_by_name(new_sample_name, self.data1.samples)
        self.assertTrue(old_sample)
        self.assertNotIn(specimen, old_sample.specimens)
        self.assertTrue(new_sample)
        self.assertIn(specimen, new_sample.specimens)

    def test_update_specimen_with_data(self):
        specimen_name = 'Z35.6a'
        self.data1.change_specimen(specimen_name, specimen_name, new_specimen_data={'specimen_elevation': 12})
        specimen = self.data1.find_by_name('Z35.6a', self.data1.specimens)
        self.assertTrue(specimen)
        self.assertIn('specimen_elevation', specimen.data.keys())
        self.assertEqual(12, specimen.data['specimen_elevation'])
        # change again (should overwrite)
        self.data1.change_specimen(specimen_name, specimen_name, new_specimen_data={'specimen_elevation': 92})
        self.assertIn('specimen_elevation', specimen.data.keys())
        self.assertEqual(92, specimen.data['specimen_elevation'])

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
        self.assertTrue(specimen.data)
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

    def test_add_specimen_with_data(self):
        specimen_name = 'new_spec'
        self.data1.add_specimen(specimen_name, spec_data={'specimen_type': 'special', 'specimen_elevation': 22})
        
        specimen = self.data1.find_by_name(specimen_name, self.data1.specimens)

        self.assertNotIn('er_specimen_name', specimen.data.keys())
        self.assertNotIn('er_sample_name', specimen.data.keys())
        self.assertNotIn('er_site_name', specimen.data.keys())
        self.assertNotIn('er_location_name', specimen.data.keys())
        self.assertEqual('special', specimen.data['specimen_type'])
        self.assertIn('specimen_elevation', specimen.data.keys())
        self.assertEqual(22, specimen.data['specimen_elevation'])
        

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


class TestSample(unittest.TestCase):

    def setUp(self):
        dir_path = os.path.join(WD, 'Datafiles', 'copy_ErMagicBuilder')
        self.data1 = builder.ErMagicBuilder(dir_path)
        self.data1.get_data()

    def test_update_sample(self):
        specimen_name = 'Z35.6a'
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        location_name = 'locale'
        self.data1.change_sample(sample_name, 'new_sample', new_site_name=None, new_sample_data={})

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
        
        self.data1.change_sample(sample_name, sample_name, new_site_name=new_site_name, new_sample_data={})

        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        new_site = self.data1.find_by_name(new_site_name, self.data1.sites)
        old_site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertTrue(sample)
        self.assertTrue(new_site)
        self.assertTrue(old_site)
        self.assertEqual(new_site, sample.site)
        self.assertIn(sample, new_site.samples)
        self.assertNotIn(sample, old_site.samples)


    def test_update_sample_with_data(self):
        sample_name = 'Z35.6'
        sample = self.data1.find_by_name(sample_name, self.data1.samples)

        self.data1.change_sample(sample_name, sample_name, new_sample_data={'sample_type': 'awesome', 'sample_alteration_type': 'awesomer'})
        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        self.assertTrue(sample)
        self.assertIn('sample_alteration_type', sample.data.keys())
        self.assertEqual('awesomer', sample.data['sample_alteration_type'])
        self.assertEqual('awesome', sample.data['sample_type'])
        # change again (should overwrite)
        self.data1.change_sample(sample_name, sample_name, new_sample_data={'sample_type': 'cool'})
        self.assertEqual('cool', sample.data['sample_type'])

        
    def test_update_sample_with_invalid_site(self):
        sample_name = 'Z35.6'
        site_name = 'invalid site name'
        #self.assertRaises(Exception, self.data1.add_sample, sample, site, {'new_key': 'new value'})
        self.data1.change_sample(sample_name, sample_name, new_site_name=site_name, new_sample_data={})
        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        self.assertTrue(sample)
        self.assertEqual('Z35.', sample.site.name)

    def test_add_sample(self):
        samp_name = 'new_sample'
        sample = self.data1.add_sample(samp_name)
        self.assertTrue(sample)
        self.assertEqual('', sample.site)
        self.assertIn(sample, self.data1.samples)
        self.assertTrue(sample.data)
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

    def test_add_sample_with_data(self):
        samp_name = 'new_samp'
        site_name = 'MGH1'
        sample = self.data1.add_sample(samp_name, site_name, {'sample_type': 'excellent', 'sample_texture': 'rough'})
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertTrue(sample)
        self.assertTrue(site)
        self.assertIn('sample_type', sample.data.keys())
        self.assertEqual('excellent', sample.data['sample_type'])
        self.assertIn('rough', sample.data['sample_texture'])
        

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

class TestSite(unittest.TestCase):

    def setUp(self):
        dir_path = os.path.join(WD, 'Datafiles', 'copy_ErMagicBuilder')
        self.data1 = builder.ErMagicBuilder(dir_path)
        self.data1.get_data()

    def test_update_site(self):
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        location_name = 'locale'

        site = self.data1.find_by_name(site_name, self.data1.sites)
        samples = site.samples
        self.data1.change_site(site_name, 'new_site', new_location_name=None, new_site_data={})
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
        
        self.data1.change_site(site_name, 'new_site', new_location_name=new_location_name, new_site_data={})
        self.assertTrue(site)
        self.assertTrue(old_location)
        self.assertTrue(location)
        self.assertEqual(site.location, location)
        self.assertIn(site, location.sites)
        self.assertNotIn(site, old_location.sites)
        

    def test_update_site_with_data(self):
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        location_name = 'locale'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        location = self.data1.find_by_name(location_name, self.data1.locations)
        self.assertIn('site_type', site.data.keys())
        self.assertEqual('', site.data['site_type'])
        self.data1.change_site(site_name, 'new_site', new_site_data={'site_type': 'great', 'site_elevation': 10})

        self.assertTrue(site)
        self.assertEqual(site.name, 'new_site')
        self.assertIn('site_type', site.data.keys())
        self.assertEqual('great', site.data['site_type'])
        self.assertIn('site_elevation', site.data.keys())
        self.assertEqual(10, site.data['site_elevation'])

        self.data1.change_site('new_site', 'new_site', new_site_data={'site_type': 'great', 'site_elevation': 99})
        self.assertEqual(99, site.data['site_elevation'])

        
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

    def test_add_site_with_data(self):
        site_name = 'new_site'
        site = self.data1.add_site(site_name, 'Munich', {'site_type': 'great', 'site_elevation': 99})
        self.assertTrue(site)
        self.assertIn('site_type', site.data.keys())
        self.assertEqual('great', site.data['site_type'])
        self.assertIn('site_elevation', site.data.keys())
        self.assertEqual(99, site.data['site_elevation'])


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
