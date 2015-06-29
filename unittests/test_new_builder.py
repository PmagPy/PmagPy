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
