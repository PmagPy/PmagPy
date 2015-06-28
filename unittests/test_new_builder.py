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
        self.assertFalse(self.data1.find_by_name(lst, 'c'))
        self.assertTrue(self.data1.find_by_name(lst, 'b'))

    def test_update_specimen(self):
        specimen_name = 'Z35.6a'
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        location_name = 'locale'
        print 'self.data1.specimens', self.data1.specimens
        for spec in self.data1.specimens:
            print type(spec)
        specimen = self.data1.find_by_name(self.data1.specimens, specimen_name)
        self.data1.change_specimen(specimen, 'new_specimen', new_sample=None, new_specimen_data={})

        # test Data_hierarchy
        #specimen_object = self.data1.find_by_name('new specimen', self.data1.specimens)
        self.assertTrue(specimen)
        self.assertIn('new_specimen', [spec.name for spec in self.data1.specimens])
        self.assertEqual(sample_name, specimen.sample.name)
        self.assertEqual(site_name, specimen.sample.site.name)
        self.assertEqual(location_name, specimen.sample.site.location.name)
        #self.assertEqual(sample, self.data1.Data_hierarchy['sample_of_specimen']['new_specimen'])
        #self.assertIn('new_specimen', self.data1.Data_hierarchy['samples'][sample])
        #self.assertIn('new_specimen', self.data1.Data_hierarchy['site_of_specimen'].keys())
        #self.assertEqual(site, self.data1.Data_hierarchy['site_of_specimen']['new_specimen'])
        #self.assertIn('new_specimen', self.data1.Data_hierarchy['location_of_specimen'].keys())
        #self.assertEqual(location, self.data1.Data_hierarchy['location_of_specimen']['new_specimen'])

        # test data_er_specimens
        #self.assertIn('new_specimen', self.data1.data_er_specimens.keys())
        #self.assertEqual('new_specimen', self.data1.data_er_specimens['new_specimen']['er_specimen_name'])

