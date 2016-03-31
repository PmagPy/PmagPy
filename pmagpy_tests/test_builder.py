#!/usr/bin/env python

# pylint: disable=C0303,W0612,C0303,C0111,C0301

"""
Tests for new ErMagicBuilder
"""

import unittest
import os
import sys
import pmagpy.builder as builder
from pmagpy import validate_upload

WD = sys.prefix
data_dir = os.path.join(WD, 'pmagpy_data_files')
if not os.path.exists(data_dir):
    data_dir = os.path.join(os.getcwd(), 'data_files')
data_model = validate_upload.get_data_model()

    
class TestBuilder(unittest.TestCase):
    """
    Test ErMagicBuilder data structure
    """

    def setUp(self):
        dir_path = os.path.join(data_dir, 'copy_ErMagicBuilder')
        self.data1 = builder.ErMagicBuilder(dir_path, data_model)
        self.data1.get_data()
        #self.data2 = builder.ErMagicBuilder(WD)
        #self.data2.get_data()

    def tearDown(self):
        pass

    def test_data_creation(self):
        self.assertTrue(self.data1.specimens)

    def test_find_by_name(self):
        specimen = builder.Specimen('a', '', self.data1.data_model)
        specimen2 = builder.Specimen('b', '', self.data1.data_model)
        specimen3 = builder.Specimen('c', '', self.data1.data_model)
        lst = [specimen, specimen2]
        self.assertFalse(self.data1.find_by_name('c', lst))
        self.assertTrue(self.data1.find_by_name('b', lst))

    def test_get_magic_info_append(self):
        spec_name = '318-U1361A-001H-2-W-35'
        self.assertFalse(self.data1.find_by_name(spec_name, self.data1.specimens))
        file_name = os.path.join(data_dir, 'ani_depthplot', 'er_specimens.txt')
        self.data1.get_magic_info('specimen', 'sample', filename=file_name)
        self.assertTrue(self.data1.find_by_name(spec_name, self.data1.specimens))

    def test_get_magic_info_append_wrong_type(self):
        spec_name = 'sml0109b1'
        self.assertFalse(self.data1.find_by_name(spec_name,
                                                 self.data1.specimens))
        file_name = os.path.join(data_dir, 'misc_files',
                                 'er_specimens.txt')
        self.data1.get_magic_info('sample', 'site', filename=file_name,
                                  sort_by_file_type=True)
        specimen = self.data1.find_by_name(spec_name, self.data1.specimens)
        self.assertTrue(specimen)
        self.assertNotIn('specimen_lithology', specimen.pmag_data.keys())
        self.assertIn('specimen_lithology', specimen.er_data.keys())
        self.assertEqual(specimen.er_data['specimen_lithology'], 'Basalt')


    def test_get_magic_info_append_wrong_type_pmag_file(self):
        spec_name = 'sv07b1'
        self.assertFalse(self.data1.find_by_name(spec_name,
                                                 self.data1.specimens))
        file_name = os.path.join(data_dir, 'misc_files',
                                 'pmag_specimens.txt')
        result = self.data1.get_magic_info('sample', 'site',
                                           filename=file_name,
                                           sort_by_file_type=True)
        self.assertTrue(result)
        specimen = self.data1.find_by_name(spec_name, self.data1.specimens)
        self.assertTrue(specimen)
        self.assertNotIn('measurement_step_max', specimen.er_data.keys())
        self.assertEqual(specimen.pmag_data['measurement_step_max'], '0.18')


    def test_get_magic_info_invalid_filename(self):
        file_name = os.path.join(data_dir, 'misc_files',
                                 'pmag_specimen.txt')
        result = self.data1.get_magic_info('sample', 'site',
                                           filename=file_name,
                                           sort_by_file_type=True)
        self.assertFalse(result)

    def test_get_magic_info_invalid_file_type(self):
        file_name = os.path.join(data_dir,
                                 'plot_cdf', 'gaussian.out')
        res = self.data1.get_magic_info('sample', 'site', filename=file_name,
                                        sort_by_file_type=True)
        self.assertFalse(res)

    def test_get_lat_lon(self):
        data_model = self.data1.data_model
        loc1 = builder.Location('loc1', data_model)
        loc2 = builder.Location('loc2', data_model)
        loc3 = builder.Location('loc3', data_model)
        site1a = builder.Site('site1a', loc1, data_model)
        site1b = builder.Site('site1b', loc1, data_model)
        site2a = builder.Site('site2a', loc2, data_model)
        site2b = builder.Site('site2b', loc2, data_model)
        loc1.sites = [site1a, site1b]
        loc2.sites = [site2a, site2b]

        site1a.er_data['site_lat'], site1a.er_data['site_lon'] = 1, 10
        site1b.er_data['site_lat'], site1b.er_data['site_lon'] = 2, 20
        site2a.er_data['site_lat'], site2a.er_data['site_lon'] = 3, 30
        site2b.er_data['site_lat'], site2b.er_data['site_lon'] = 4, 40
        locations = [loc1, loc2, loc3]
        result_dict = self.data1.get_min_max_lat_lon(locations)
        self.assertIn(loc1.name, result_dict.keys())
        self.assertIn(loc2.name, result_dict.keys())
        self.assertIn(loc3.name, result_dict.keys())
        self.assertEqual(1., result_dict[loc1.name]['location_begin_lat'])
        self.assertEqual(2., result_dict[loc1.name]['location_end_lat'])
        self.assertEqual(3., result_dict[loc2.name]['location_begin_lat'])
        self.assertEqual(4., result_dict[loc2.name]['location_end_lat'])
        self.assertEqual(10., result_dict[loc1.name]['location_begin_lon'])
        self.assertEqual(20., result_dict[loc1.name]['location_end_lon'])
        self.assertEqual(30., result_dict[loc2.name]['location_begin_lon'])
        self.assertEqual(40., result_dict[loc2.name]['location_end_lon'])
        self.assertEqual('', result_dict[loc3.name]['location_begin_lat'])



class TestMeasurement(unittest.TestCase):

    def setUp(self):
        self.dir_path = os.path.join(data_dir,
                                     'copy_ErMagicBuilder')
        self.data1 = builder.ErMagicBuilder(self.dir_path, data_model)
        self.data1.get_data()

    def tearDown(self):
        pass

    def test_measurements_created(self):
        #return
        self.assertIn('measurements', dir(self.data1))
        self.assertTrue(self.data1.measurements)
        meas = self.data1.find_by_name('Z35.6a:LP-DIR-T_20',
                                       self.data1.measurements)
        self.assertTrue(meas)
        self.assertEqual(meas.experiment_name, 'Z35.6a:LP-DIR-T')
        self.assertEqual(meas.meas_number, '20')
        for attr in ['specimen', 'er_data']:
            self.assertTrue(meas.__getattribute__(attr))
        for attr in ['er_specimen_name', 'er_sample_name', 'er_site_name',
                     'er_location_name', 'magic_experiment_name',
                     'measurement_number']:
            self.assertNotIn(attr, meas.er_data.keys())

    def test_measurement_headers(self):
        self.data1.init_default_headers()
        self.data1.init_actual_headers()
        for lst in self.data1.headers['measurement']['er']:
            self.assertTrue(lst)

    def test_write_measurements_file(self):
        self.data1.init_default_headers()
        self.data1.init_actual_headers()
        result = self.data1.write_measurements_file()
        self.assertTrue(result)
        result_file = os.path.join(self.dir_path, 'magic_measurements.txt')
        self.assertTrue(os.path.isfile(result_file))

    def test_measurement_is_updated(self):
        spec_name = 'Z35.1a'
        specimen = self.data1.find_by_name(spec_name, self.data1.specimens)
        meas_name = 'Z35.1a:LP-DIR-T_1'
        measurement = self.data1.find_by_name(meas_name, self.data1.measurements)
        samp_name = 'Z35.1'
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        self.data1.change_sample(samp_name, samp_name, 'Z35.')
        self.assertEqual(measurement.specimen.name, spec_name)
        self.assertEqual(measurement.specimen.sample.name, 'Z35.1')
        self.assertEqual(measurement.specimen.sample.site.name, 'Z35.')

        self.data1.change_specimen(spec_name, 'new_name', 'MGH1')
        self.assertEqual(measurement.specimen.name, 'new_name')
        self.assertEqual(measurement.specimen.sample.name, 'MGH1')
        self.assertEqual(measurement.specimen.sample.site.name, 'MGH1')


class TestSpecimen(unittest.TestCase):

    def setUp(self):
        dir_path = os.path.join(data_dir, 'copy_ErMagicBuilder')
        self.data1 = builder.ErMagicBuilder(dir_path, data_model)
        self.data1.get_data()
        #self.data2 = builder.ErMagicBuilder(WD)
        #self.data2.get_data()

    def tearDown(self):
        pass

    def test_propagate_data(self):
        spec_name = 'Z35.6a'
        samp_name = 'Z35.6'
        specimen = self.data1.find_by_name(spec_name, self.data1.specimens)
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        sample.er_data['sample_lithology'] = "Basalt"
        specimen.er_data['specimen_lithology'] = "Not Specified"
        self.assertNotEqual("Basalt", specimen.er_data['specimen_lithology'])
        specimen.propagate_data()
        self.assertEqual("Basalt", specimen.er_data['specimen_lithology'])

    def test_not_propagate_data(self):
        spec_name = 'Z35.6a'
        samp_name = 'Z35.6'
        specimen = self.data1.find_by_name(spec_name, self.data1.specimens)
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        sample.er_data['sample_lithology'] = "Basalt"
        specimen.er_data['specimen_lithology'] = "Something else"
        self.assertNotEqual("Basalt", specimen.er_data['specimen_lithology'])
        specimen.propagate_data()
        self.assertEqual("Something else", specimen.er_data['specimen_lithology'])


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
        self.data1.change_specimen(specimen_name, 'new_specimen',
                                   new_sample_name=None, new_er_data=None)

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
        self.data1.change_specimen(specimen_name, specimen_name, new_sample_name,
                                   new_er_data={'er_sample_name': 'Z35.5'})

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
        self.data1.get_magic_info('specimen', 'sample', 'pmag')
        self.data1.change_specimen(specimen_name, specimen_name, new_pmag_data={'er_fossil_name': 'Mr. Bone'})
        self.assertTrue(specimen)
        # make sure new data is added in
        self.assertIn('er_fossil_name', specimen.pmag_data.keys())
        self.assertEqual('Mr. Bone', specimen.pmag_data['er_fossil_name'])
        # make sure old data hasn't disappeared
        self.assertIn('magic_experiment_names', specimen.pmag_data.keys())
        self.assertEqual('Z35.6a:LP-DIR-T', specimen.pmag_data['magic_experiment_names'])

    def test_update_specimen_with_pmag_data_overwrite(self):
        specimen_name = 'Z35.6a'
        specimen = self.data1.find_by_name('Z35.6a', self.data1.specimens)
        self.data1.get_magic_info('specimen', 'sample', 'pmag')
        self.data1.change_specimen(specimen_name, specimen_name,
                                   new_pmag_data={'er_fossil_name': 'Mr. Bone'}, replace_data=True)
        self.assertTrue(specimen)
        # make sure new data is added in
        self.assertIn('er_fossil_name', specimen.pmag_data.keys())
        self.assertEqual('Mr. Bone', specimen.pmag_data['er_fossil_name'])
        # make sure old data has disappeared
        self.assertNotIn('magic_experiment_names', specimen.pmag_data.keys())


    #def test_update_specimen_with_invalid_sample(self):
    #    specimen_name = 'Z35.6a'
    #    sample_name = 'invalid_sample'
    #    self.data1.change_specimen(specimen_name, specimen_name, sample_name)
    #    specimen = self.data1.find_by_name('Z35.6a', self.data1.specimens)
    #    sample = self.data1.find_by_name('Z35.6', self.data1.samples)
    #    self.assertTrue(specimen)
    #    self.assertEqual(sample, specimen.sample)
    #    specimen.sample = ""
    #    self.data1.change_specimen(specimen_name, specimen_name, sample_name)
    #    self.assertEqual('', specimen.sample)

    def test_update_specimen_without_sample(self):
        specimen_name = 'Z35.6a'
        sample_name = 'Z35.6'
        specimen = self.data1.find_by_name(specimen_name, self.data1.specimens)
        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        specimen.sample = ''
        self.assertFalse(specimen.sample)
        self.data1.change_specimen(specimen_name, specimen_name, sample_name)
        self.assertTrue(specimen.sample)
        self.assertEqual(specimen.sample, sample)
        self.assertIn(specimen, sample.specimens)

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

    #def test_add_specimen_invalid_sample(self):
    #    spec_name = 'new specimen'
    #    samp_name = 'nonexistent_sample'
    #    self.data1.add_specimen(spec_name, samp_name)
    #    specimen = self.data1.find_by_name(spec_name, self.data1.specimens)
    #    sample = self.data1.find_by_name(samp_name, self.data1.samples)
    #    self.assertTrue(specimen)
    #    self.assertIn(specimen, self.data1.specimens)
    #    self.assertFalse(sample)
    #    self.assertEqual('', specimen.sample)

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
            if key == 'er_citation_names':
                self.assertEqual('This study', specimen.er_data[key])
            else:
                self.assertEqual('', specimen.er_data[key])
        #self.data1.get_spec_data()
        #self.data1.get_magic_info('specimen', 'sample', 'er')
        self.data1.get_magic_info('specimen', 'sample', 'er')

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
            if key == 'er_citation_names':
                self.assertEqual('This study', specimen.pmag_data[key])
            else:
                self.assertEqual('', specimen.pmag_data[key])
        self.assertIn('er_citation_names', specimen.pmag_data.keys())
        self.assertNotIn('pmag_rotation_codes', specimen.pmag_data.keys())

        #self.data1.get_magic_info('specimen', 'sample', 'pmag')
        self.data1.get_magic_info('specimen', 'sample', 'pmag')

        self.assertIn('measurement_step_max', specimen.pmag_data.keys())
        self.assertEqual(828, int(specimen.pmag_data['measurement_step_max']))
        self.assertIn('magic_experiment_names', specimen.pmag_data.keys())
        self.assertEqual('Z35.6a:LP-DIR-T', specimen.pmag_data['magic_experiment_names'])

    def test_write_magic_file(self):
        self.data1.get_all_magic_info()
        self.data1.init_default_headers()
        self.data1.init_actual_headers()

        er_outfile, pmag_outfile = self.data1.write_magic_file('specimen')
        self.assertTrue(er_outfile)
        self.assertTrue(pmag_outfile)

    def test_add_specimen_new_sample(self):
        spec_name = 'new specimen'
        specimen = self.data1.add_specimen(spec_name, 'new_samp')
        sample = self.data1.find_by_name('new_samp', self.data1.samples)
        self.assertTrue(specimen)
        self.assertIn(specimen, self.data1.specimens)
        self.assertTrue(sample)
        self.assertIn(sample, self.data1.samples)
        self.assertIn(specimen, sample.specimens)

    def test_update_specimen_new_sample(self):
        specimen_name = 'Z35.6a'
        sample_name = 'new_sample'
        specimen = self.data1.find_by_name(specimen_name, self.data1.specimens)
        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        self.assertFalse(sample)
        self.data1.change_specimen(specimen_name, specimen_name, sample_name)
        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        self.assertTrue(sample)
        self.assertIn(specimen, sample.specimens)


class TestSample(unittest.TestCase):

    def setUp(self):
        self.dir_path = os.path.join(data_dir, 'copy_ErMagicBuilder')
        self.data1 = builder.ErMagicBuilder(self.dir_path)
        self.data1.get_data()


    def test_propagate_data(self):
        samp_name = 'Z35.6'
        site_name = 'Z35.'
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        site = self.data1.find_by_name(site_name, self.data1.sites)
        site.er_data['site_lithology'] = "Basalt"
        sample.er_data['sample_lithology'] = "Not Specified"
        sample.propagate_data()
        self.assertEqual(sample.er_data['sample_lithology'], site.er_data['site_lithology'])

    def test_not_propagate_data(self):
        samp_name = 'Z35.6'
        site_name = 'Z35.'
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        site = self.data1.find_by_name(site_name, self.data1.sites)
        site.er_data['site_lithology'] = "Basalt"
        sample.er_data['sample_lithology'] = "Fake type of lithology"
        sample.propagate_data()
        self.assertNotEqual(sample.er_data['sample_lithology'], site.er_data['site_lithology'])

        
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

    def test_update_sample_with_er_data_overwrite(self):
        sample_name = 'Z35.6'
        sample = self.data1.find_by_name(sample_name, self.data1.samples)

        self.data1.change_sample(sample_name, sample_name, new_er_data={'sample_type': 'awesome', 'sample_alteration_type': 'awesomer'})
        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        self.assertTrue(sample)
        self.assertIn('sample_alteration_type', sample.er_data.keys())
        self.assertEqual('awesomer', sample.er_data['sample_alteration_type'])
        self.assertEqual('awesome', sample.er_data['sample_type'])
        # make sure data is overwritten
        self.data1.change_sample(sample_name, sample_name,
                                 new_er_data={'sample_lithology': 'good'}, replace_data=True)
        self.assertNotIn('sample_alteration_type', sample.er_data.keys())

    def test_update_sample_with_pmag_data(self):
        sample_name = 'Z35.6'
        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        self.data1.get_magic_info('sample', 'site', 'pmag')
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

    #def test_update_sample_with_invalid_site(self):
    #    sample_name = 'Z35.6'
    #    site_name = 'invalid site name'
    #    #self.assertRaises(Exception, self.data1.add_sample, sample, site, {'new_key': 'new value'})
    #    self.data1.change_sample(sample_name, sample_name, new_site_name=site_name, new_er_data=None)
    #    sample = self.data1.find_by_name(sample_name, self.data1.samples)
    #    self.assertTrue(sample)
    #    self.assertEqual('Z35.', sample.site.name)

    def test_update_sample_without_site(self):
        sample_name = 'Z35.6'
        site_name = 'MGH1'
        sample = self.data1.find_by_name(sample_name, self.data1.samples)
        site = self.data1.find_by_name(site_name, self.data1.sites)
        sample.site = ''
        self.assertFalse(sample.site)
        self.data1.change_sample(sample_name, sample_name, new_site_name=site_name, new_er_data=None)
        self.assertTrue(sample.site)
        self.assertEqual(sample.site, site)
        self.assertIn(sample, site.samples)

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

    #def test_add_sample_invalid_site(self):
    #    samp_name = 'new_samp'
    #    site_name = 'invalid_site'
    #    sample = self.data1.add_sample(samp_name, site_name)
    #    site = self.data1.find_by_name(site_name, self.data1.sites)
    #    self.assertTrue(sample)
    #    self.assertFalse(site)
    #    self.assertEqual('', sample.site)

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
            if key == 'er_citation_names':
                self.assertEqual('This study', sample.er_data[key])
            else:
                self.assertEqual('', sample.er_data[key])
        self.data1.get_magic_info('sample', 'site', 'er')
        self.assertEqual('This study', sample.er_data['er_citation_names'])
        self.assertEqual('Archeologic', sample.er_data['sample_class'])
        self.assertEqual('s', sample.er_data['sample_type'])
        self.assertEqual('Baked Clay', sample.er_data['sample_lithology'])

    def test_pmag_data(self):
        samp_name = 'Z35.6'
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        samp_name2 = 'MGH1'
        sample2 = self.data1.find_by_name(samp_name2, self.data1.samples)
        self.assertTrue(sample)
        self.assertTrue(sample2)
        self.assertTrue(sample.pmag_data)
        self.assertTrue(sample2.pmag_data)
        for key in sample.pmag_data.keys():
            if key == 'er_citation_names':
                self.assertEqual('This study', sample.pmag_data[key])
            else:
                self.assertEqual('', sample.pmag_data[key])
        for key in sample2.pmag_data.keys():
            if key == 'er_citation_names':
                self.assertEqual('This study', sample2.pmag_data[key])
            else:
                self.assertEqual('', sample2.pmag_data[key])
        self.data1.get_magic_info('sample', 'site', 'pmag')
        self.assertEqual('This study', sample.pmag_data['er_citation_names'])
        self.assertEqual('fake_instrument_code', sample.pmag_data['magic_instrument_codes'])

        magic_file = os.path.join(self.dir_path, 'pmag_samples.txt')
        magic_name = 'er_sample_name'
        data_dict, header, file_type = self.data1.read_magic_file(magic_file, magic_name)

        # sample should have been written to pmag_sites.txt
        # site2 should NOT (since it had no real pmag data)
        self.assertIn(sample.name, data_dict)
        self.assertNotIn(sample2.name, data_dict)


    def test_write_magic_file(self):
        self.data1.get_all_magic_info()
        self.data1.init_default_headers()
        self.data1.init_actual_headers()

        er_outfile, pmag_outfile = self.data1.write_magic_file('sample')
        self.assertTrue(er_outfile)
        self.assertTrue(pmag_outfile)

    def test_add_sample_new_site(self):
        samp_name = 'new_sample'
        site = self.data1.find_by_name('new_site', self.data1.sites)
        self.assertFalse(site)
        sample = self.data1.add_sample(samp_name, 'new_site')
        site = self.data1.find_by_name('new_site', self.data1.sites)
        self.assertTrue(sample)
        self.assertIn(sample, self.data1.samples)
        self.assertTrue(site)
        self.assertIn(site, self.data1.sites)
        self.assertIn(sample, site.samples)

    def test_update_sample_new_site(self):
        samp_name = 'Z35.6'
        site_name = 'new_site'
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertFalse(site)
        self.data1.change_sample(samp_name, samp_name, site_name)
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.assertTrue(site)
        self.assertIn(sample, site.samples)


class TestSite(unittest.TestCase):

    def setUp(self):
        self.dir_path = os.path.join(data_dir, 'copy_ErMagicBuilder')
        self.data1 = builder.ErMagicBuilder(self.dir_path, data_model)
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

    def test_update_site_with_pmag_data_overwrite(self):
        sample_name = 'Z35.6'
        site_name = 'Z35.'
        location_name = 'locale'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        location = self.data1.find_by_name(location_name, self.data1.locations)
        self.assertIn('magic_method_codes', site.pmag_data.keys())
        self.assertFalse(site.pmag_data['magic_method_codes'])
        self.assertNotIn('site_sigma', site.pmag_data.keys())
        self.data1.change_site(site_name, 'new_site', new_pmag_data={'site_sigma': 3}, replace_data=True)

        self.assertIn('site_sigma', site.pmag_data.keys())
        self.assertEqual(3, site.pmag_data['site_sigma'])
        self.assertNotIn('magic_method_codes', site.pmag_data.keys())


    #def test_update_site_invalid_location(self):
    #    site_name = 'Z35.'
    #    location_name = 'locale'
    #    site = self.data1.find_by_name(site_name, self.data1.sites)
    #    location = self.data1.find_by_name(location_name, self.data1.locations)
    #    self.data1.change_site(site_name, 'new_name', new_location_name='invalid_location')
    #    self.assertTrue(site)
    #    self.assertEqual(site.name, 'new_name')
    #    self.assertEqual(site.location, location)

    def test_update_site_without_location(self):
        site_name = 'Z35.'
        new_site_name = 'new_name'
        location_name = 'locale'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        location = self.data1.find_by_name(location_name, self.data1.locations)
        site.location = ''
        self.assertFalse(site.location)
        self.data1.change_site(site_name, new_site_name, location_name)
        self.assertTrue(site.location)
        self.assertIn(site, location.sites)

    def test_add_site(self):
        site_name = 'new_site'
        site = self.data1.add_site(site_name)
        self.assertTrue(site)
        self.assertIn(site, self.data1.sites)
        self.assertFalse(site.location)

    def test_add_site_with_location(self):
        location = self.data1.find_by_name('Munich', self.data1.locations)
        self.assertTrue(location)
        site_name = 'new_site'
        site = self.data1.add_site(site_name, location.name)
        self.assertTrue(site)
        self.assertIn(site, self.data1.sites)
        self.assertIn(site, location.sites)


    #def test_add_site_invalid_location(self):
    #    site_name = 'new_site'
    #    site = self.data1.add_site(site_name, 'non_existent_location')
    #    self.assertTrue(site)
    #    self.assertIn(site, self.data1.sites)
    #    self.assertEqual('', site.location)

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
            if key == 'er_citation_names':
                self.assertEqual('This study', site.er_data[key])
            else:
                self.assertEqual('', site.er_data[key])
        self.data1.get_magic_info('site', 'location', 'er')
        self.assertEqual('This study', site.er_data['er_citation_names'])
        self.assertEqual('Archeologic', site.er_data['site_class'])
        self.assertEqual('Baked Clay', site.er_data['site_type'])
        self.assertEqual('Mafic Dike', site.er_data['site_lithology'])

    def test_pmag_data(self):
        site_name = 'MGH1'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        site_name2 = 'Z35.'
        site2 = self.data1.find_by_name(site_name2, self.data1.sites)
        self.assertTrue(site)
        self.assertTrue(site2)
        self.assertTrue(site.pmag_data)
        self.assertTrue(site2.pmag_data)
        for key in site.pmag_data.keys():
            if key == 'er_citation_names':
                self.assertEqual('This study', site.pmag_data[key])
            else:
                self.assertEqual('', site.pmag_data[key])
        for key in site2.pmag_data.keys():
            if key == 'er_citation_names':
                self.assertEqual('This study', site.pmag_data[key])
            else:
                self.assertEqual('', site.pmag_data[key])

        self.data1.get_magic_info('site', 'location', 'pmag')
        self.assertEqual('This study', site.pmag_data['er_citation_names'])

        magic_file = os.path.join(self.dir_path, 'pmag_sites.txt')
        magic_name = 'er_site_name'
        data_dict, header, file_type = self.data1.read_magic_file(magic_file, magic_name)

        # site should have been written to pmag_sites.txt
        # site2 should NOT (since it had no real pmag data)
        self.assertIn(site.name, data_dict)
        self.assertNotIn(site2.name, data_dict)




    def test_write_magic_file(self):
        self.data1.get_all_magic_info()
        self.data1.init_default_headers()
        self.data1.init_actual_headers()
        er_outfile, pmag_outfile = self.data1.write_magic_file('site')
        self.assertTrue(er_outfile)
        self.assertTrue(pmag_outfile)

    def test_add_site_new_location(self):
        site_name = 'new_site'
        location = self.data1.find_by_name('new_loc', self.data1.locations)
        self.assertFalse(location)
        site = self.data1.add_site(site_name, 'new_loc')
        loc = self.data1.find_by_name('new_loc', self.data1.locations)
        self.assertTrue(site)
        self.assertIn(site, self.data1.sites)
        self.assertTrue(loc)
        self.assertIn(loc, self.data1.locations)
        self.assertIn(site, loc.sites)

    def test_update_site_new_location(self):
        site_name = 'Z35.'
        loc_name = 'new_location'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        location = self.data1.find_by_name(loc_name, self.data1.locations)
        self.assertFalse(location)
        self.data1.change_site(site_name, site_name, loc_name)
        location = self.data1.find_by_name(loc_name, self.data1.locations)
        self.assertTrue(location)
        self.assertIn(site, location.sites)



class TestLocation(unittest.TestCase):

    def setUp(self):
        dir_path = os.path.join(data_dir, 'copy_ErMagicBuilder')
        self.data1 = builder.ErMagicBuilder(dir_path, data_model)
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
        self.data1.change_location(location_name, location_name,
                                   new_er_data={'location_type': 'great', 'continent_ocean': 'Indian'})
        self.assertIn('location_type', location.er_data.keys())
        self.assertEqual('great', location.er_data['location_type'])
        self.assertIn('continent_ocean', location.er_data.keys())
        self.assertEqual('Indian', location.er_data['continent_ocean'])

        self.data1.change_location(location_name, location_name,
                                   new_er_data={'continent_ocean': 'Atlantic'})
        self.assertEqual('Atlantic', location.er_data['continent_ocean'])


    def test_update_location_with_er_data_overwrite(self):
        location_name = 'locale'
        location = self.data1.find_by_name(location_name, self.data1.locations)
        self.assertIn('location_type', location.er_data.keys())
        self.assertEqual('', location.er_data['location_type'])
        self.data1.change_location(location_name, location_name,
                                   new_er_data={'continent_ocean': 'Indian'},
                                   replace_data=True)
        self.assertNotIn('location_type', location.er_data.keys())
        self.assertIn('continent_ocean', location.er_data.keys())
        self.assertEqual('Indian', location.er_data['continent_ocean'])


    def test_update_location_with_data_and_name_change(self):
        location_name = 'locale'
        new_location_name = 'new_locale'
        location = self.data1.find_by_name(location_name, self.data1.locations)
        self.assertIn('location_type', location.er_data.keys())
        self.assertEqual('', location.er_data['location_type'])
        self.data1.change_location(location_name, new_location_name,
                                   new_er_data={'location_type': 'great', 'continent_ocean': 'Indian'})

        self.assertFalse(self.data1.find_by_name(location_name, self.data1.locations))
        location = self.data1.find_by_name(new_location_name, self.data1.locations)
        self.assertIn('location_type', location.er_data.keys())
        self.assertEqual('great', location.er_data['location_type'])
        self.assertIn('continent_ocean', location.er_data.keys())
        self.assertEqual('Indian', location.er_data['continent_ocean'])

        self.data1.change_location(new_location_name, new_location_name,
                                   new_er_data={'continent_ocean': 'Atlantic'})
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
            if key == 'er_citation_names':
                self.assertEqual('This study', location.er_data[key])
            else:
                self.assertEqual('', location.er_data[key])
        self.data1.get_magic_info('location', attr='er')
        self.assertEqual('This study', location.er_data['er_citation_names'])
        self.assertEqual('Lake Core', location.er_data['location_type'])
        self.assertEqual(47.1, float(location.er_data['location_begin_lat']))
        self.assertEqual(47.1, float(location.er_data['location_end_lat']))

    def test_write_magic_file(self):
        self.data1.get_all_magic_info()
        self.data1.init_default_headers()
        self.data1.init_actual_headers()
        er_outfile, pmag_outfile = self.data1.write_magic_file('location')
        self.assertTrue(er_outfile)
        self.assertFalse(pmag_outfile)



class TestAge(unittest.TestCase):

    def setUp(self):
        self.dir_path = os.path.join(data_dir, 'copy_ErMagicBuilder')
        self.data1 = builder.ErMagicBuilder(self.dir_path, data_model)
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

        self.data1.get_age_info()
        #self.assertTrue(self.data1.ages)
        self.assertTrue(site.age_data)
        self.assertEqual(3, int(site.age_data['age']))
        self.assertEqual('GM-ARAR', site.age_data['magic_method_codes'])

    def test_change_age(self):
        site_name = 'MGH1'
        site = self.data1.find_by_name(site_name, self.data1.sites)
        self.data1.get_age_info()
        self.assertTrue(site.age_data)
        self.assertEqual(3, int(site.age_data['age']))
        self.data1.change_age(site_name, {'age': 5, 'er_fossil_name': 'Joe'})
        self.assertEqual(5, int(site.age_data['age']))
        self.assertIn('er_fossil_name', site.age_data.keys())
        self.assertEqual('Joe', site.age_data['er_fossil_name'])

    def test_write_magic_file(self):
        self.data1.get_all_magic_info()
        self.data1.init_default_headers()
        self.data1.init_actual_headers()
        outfile = self.data1.write_age_file()
        self.assertTrue(outfile)

    def test_add_age(self):
        self.data1.init_default_headers()
        site = self.data1.find_by_name('MGH1', self.data1.sites)
        self.assertEqual('site', self.data1.age_type)
        self.assertFalse(self.data1.write_ages)
        self.assertNotIn('age', site.age_data.keys())
        self.data1.add_age('MGH1', {'age': 10})

        self.assertTrue(self.data1.write_ages)
        self.assertIn('age', site.age_data.keys())
        self.assertIn('magic_method_codes', site.age_data.keys())
        self.assertEqual(10, site.age_data['age'])

    def test_add_age_nonexistent_site(self):
        self.data1.init_default_headers()
        result = self.data1.add_age('fake_site', {'age': 10})
        self.assertFalse(result)

    def test_add_age_type_sample(self):
        self.data1.init_default_headers()
        samp_name = 'Z35.6'
        sample = self.data1.find_by_name(samp_name, self.data1.samples)
        self.assertNotIn('age', sample.age_data.keys())
        self.assertFalse(self.data1.write_ages)

        self.data1.age_type = 'sample'
        self.data1.add_age(samp_name, {'age': 10})

        self.assertIn('age', sample.age_data.keys())
        self.assertIn('magic_method_codes', sample.age_data.keys())
        self.assertEqual(10, sample.age_data['age'])


    def test_import_age_info(self):
        self.data1.get_age_info(filename=os.path.join(self.dir_path, 'weird_er_ages.txt'))
        specimen = self.data1.find_by_name('new_specimen', self.data1.specimens)
        sample = self.data1.find_by_name('new_sample', self.data1.samples)
        site = self.data1.find_by_name('new_site', self.data1.sites)
        location = self.data1.find_by_name('new_location', self.data1.locations)
        for pmag_item in (specimen, sample, site, location):
            self.assertTrue(pmag_item)
            self.assertEqual(pmag_item.age_data['age'], '3')
            self.assertFalse(pmag_item.get_parent())
        specimen = self.data1.find_by_name('specimen1', self.data1.specimens)
        sample = self.data1.find_by_name('sample1', self.data1.samples)
        site = self.data1.find_by_name('site1', self.data1.sites)
        for pmag_item in (specimen, sample, site):
            self.assertTrue(pmag_item)
            self.assertTrue(pmag_item.get_parent(), str(pmag_item) + ' has no parent')
            self.assertEqual(pmag_item.age_data['age'], '3')
        specimen2 = self.data1.find_by_name('specimen2', self.data1.specimens)
        specimen3 = self.data1.find_by_name('specimen3', self.data1.specimens)
        for pmag_item in (specimen2, specimen3):
            self.assertTrue(pmag_item)
            self.assertTrue(pmag_item.get_parent(), str(pmag_item) + ' has no parent')


    def test_delete_age(self):
        pass


class TestResult(unittest.TestCase):

    def setUp(self):
        dir_path = os.path.join(data_dir, 'mk_redo')
        self.data1 = builder.ErMagicBuilder(dir_path, data_model)
        #self.data1.get_data()

        self.data1.get_magic_info('specimen', 'sample', 'er')
        self.data1.get_magic_info('specimen', 'sample', 'pmag')

        self.data1.get_magic_info('sample', 'site', 'er')
        self.data1.get_magic_info('sample', 'site', 'pmag')

        self.data1.get_magic_info('site', 'location', 'er')
        self.data1.get_magic_info('site', 'location', 'pmag')

        self.data1.get_magic_info('location', attr='er')
        self.data1.get_age_info()

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

    def test_write_magic_file(self):
        self.data1.get_all_magic_info()
        self.data1.init_default_headers()
        self.data1.init_actual_headers()
        outfile = self.data1.write_result_file()
        self.assertTrue(outfile)


class TestValidation(unittest.TestCase):


    def setUp(self):
        dir_path = os.path.join(data_dir, 'copy_ErMagicBuilder')
        result_dir_path = os.path.join(data_dir, 'mk_redo')
        self.data1 = builder.ErMagicBuilder(dir_path, data_model)
        self.data1.get_all_magic_info()
        self.data2 = builder.ErMagicBuilder(result_dir_path, data_model)

    def test_result_validation(self):
        self.data2.get_all_magic_info()
        result = self.data2.find_by_name('sr24', self.data2.results)
        result.specimens.append('string_not_specimen')
        fake_specimen = builder.Specimen('not_in_er_magic_specimen', None)
        result.specimens.append(fake_specimen)
        site0 = self.data2.find_by_name('sr24', self.data2.sites)
        site0.set_parent('')

        result2 = self.data2.find_by_name('Reverse pole', self.data2.results)
        site = self.data2.find_by_name('sr21', self.data2.sites)
        site.set_parent('')

        result3 = self.data2.find_by_name('sr09', self.data2.results)
        site1 = result3.sites[0]
        site1.samples.append('fake_sample')

        result_warnings = self.data2.validate_results(self.data2.results)

        self.assertIn(result.name, result_warnings.keys())
        self.assertNotIn(result2.name, result_warnings.keys())
        self.assertNotIn(result3.name, result_warnings.keys())

        self.assertIn('specimen', result_warnings[result.name].keys())
        self.assertIn('string_not_specimen', result_warnings[result.name]['specimen'])
        self.assertIn(fake_specimen.name, result_warnings[result.name]['specimen'])


    def test_validation(self):
        # set up some invalid data
        specimen = self.data1.find_by_name('Z35.2a', self.data1.specimens)
        specimen.set_parent('')
        specimen2 = 'I\'m not a real specimen'
        self.data1.specimens.append(specimen2)
        sample = self.data1.find_by_name('Z35.7', self.data1.samples)
        sample.set_parent('')
        sample.children.append('fake_specimen')
        sample2 = self.data1.find_by_name('Z35.6', self.data1.samples)
        extra_site = builder.Site('a_site', None)
        sample2.set_parent(extra_site)
        site = self.data1.find_by_name('MGH1', self.data1.sites)
        site.set_parent('')
        site.children.append('fake_sample')
        location = self.data1.find_by_name('locale', self.data1.locations)
        location.children.append('fake_site')

        # then make sure validation function catches the bad data
        spec_warnings, samp_warnings, site_warnings, loc_warnings = self.data1.validate_data()

        # structure:
        # sample_warnings dictionary
        # {sample1: {'parent': [warning1, warning2, warning3], 'child': [warning1, warning2]},
        #  sample2: {'child': [warning1], 'type': [warning1, warning2]},
        #  ...}

        self.assertIn(specimen.name, spec_warnings)
        self.assertIn(specimen2, spec_warnings)
        self.assertIn(sample.name, samp_warnings)
        self.assertIn(sample2.name, samp_warnings)
        self.assertIn(site.name, site_warnings)
        self.assertIn(location.name, loc_warnings)

        self.assertIn('parent', spec_warnings[specimen.name].keys())
        ex = spec_warnings[specimen.name]['parent'][0]
        self.assertEqual('missing parent', ex.message)
        self.assertIn('type', spec_warnings["I'm not a real specimen"].keys())
        ex = spec_warnings["I'm not a real specimen"]['type'][0]
        self.assertEqual('wrong type', ex.message)

        self.assertIn('parent', samp_warnings[sample.name].keys())
        ex = samp_warnings[sample.name]['parent'][0]
        self.assertFalse(ex.obj)
        self.assertEqual('missing parent', ex.message)

        self.assertIn('parent', samp_warnings[sample2.name].keys())
        ex = samp_warnings[sample2.name]['parent'][0]
        self.assertTrue(ex.obj)
        self.assertEqual('a_site', ex.obj.name)
        self.assertEqual('parent not in data object', ex.message)

        self.assertIn('parent', site_warnings[site.name].keys())
        ex = site_warnings[site.name]['parent'][0]
        self.assertEqual('missing parent', ex.message)

        self.assertIn('children', site_warnings[site.name].keys())
        exes = site_warnings[site.name]['children']
        self.assertEqual('child has wrong type', exes[0].message)
        self.assertEqual('child not in data object', exes[1].message)
        self.assertEqual('fake_sample', exes[0].obj)
        self.assertEqual('fake_sample', exes[1].obj)

        self.assertIn('children', loc_warnings[location.name].keys())
        exes = loc_warnings[location.name]['children']
        self.assertEqual('child has wrong type', exes[0].message)
        self.assertEqual('fake_site', exes[0].obj)

    def test_measurement_validation(self):
        # set up some invalidate data
        meas_name = 'Z35.7a:LP-DIR-T_30'
        meas = self.data1.find_by_name(meas_name, self.data1.measurements)
        meas.specimen = ''
        #
        meas_name2 = 'Z35.4a:LP-DIR-T_7'
        meas2 = self.data1.find_by_name(meas_name2, self.data1.measurements)
        specimen2 = builder.Specimen('fake_specimen', None)
        meas2.specimen = specimen2
        # then make sure all invalid things are caught
        meas_warnings = self.data1.validate_measurements(self.data1.measurements)

        self.assertIn(meas, meas_warnings.keys())
        self.assertIn('parent', meas_warnings[meas].keys())
        ex = meas_warnings[meas]['parent'][0]
        self.assertEqual('missing parent', ex.message)

        self.assertIn(meas2, meas_warnings.keys())
        self.assertIn('parent', meas_warnings[meas2].keys())
        ex = meas_warnings[meas2]['parent'][0]
        self.assertEqual('parent not in data object', ex.message)


class TestOddImport(unittest.TestCase):

    def setUp(self):
        result_dir_path = os.path.join(data_dir, 'mk_redo')
        self.data2 = builder.ErMagicBuilder(result_dir_path, data_model)
        self.data2.get_all_magic_info()

    def test_samp_import(self):
        sample = self.data2.find_by_name('sr37g', self.data2.samples)

        samps = ['sr01a', 'sr01a', 'sr01c', 'sr01d', 'sr01e', 'sr01f', 'sr01g', 'sr01i',
                 'sr03a', 'sr03c', 'sr03e', 'sr03f', 'sr03g', 'sr03h', 'sr03k', 'sr04d',
                 'sr04e', 'sr04f', 'sr04g', 'sr04h', 'sr09b', 'sr09c', 'sr09e', 'sr09f',
                 'sr09g', 'sr09i', 'sr11a', 'sr11b', 'sr11c', 'sr11e', 'sr11g', 'sr12a',
                 'sr12b', 'sr12c', 'sr12e', 'sr12h', 'sr16a', 'sr16b', 'sr16c', 'sr16d',
                 'sr16e', 'sr16f', 'sr16g', 'sr19b', 'sr19e', 'sr19h', 'sr20c', 'sr20d',
                 'sr20e', 'sr20f', 'sr20g', 'sr20i', 'sr20i', 'sr20j', 'sr21b', 'sr21d',
                 'sr21g', 'sr21h', 'sr21j', 'sr22b', 'sr22d', 'sr22e', 'sr22f', 'sr22g',
                 'sr22i', 'sr23a', 'sr23b', 'sr23d', 'sr23g', 'sr24a', 'sr24b', 'sr24c',
                 'sr24d', 'sr24i', 'sr25b', 'sr25d', 'sr25e', 'sr25f', 'sr25h', 'sr26a',
                 'sr26b', 'sr26c', 'sr26e', 'sr26f', 'sr26i', 'sr27c', 'sr27d', 'sr28a',
                 'sr28b', 'sr28c', 'sr28c', 'sr28e', 'sr28f', 'sr28g', 'sr28h', 'sr29a',
                 'sr29a', 'sr29b', 'sr29c', 'sr29e', 'sr29g', 'sr29g', 'sr29h', 'sr30a',
                 'sr30a', 'sr30b', 'sr30c', 'sr30d', 'sr30e', 'sr30i', 'sr31a', 'sr31a',
                 'sr31b', 'sr31b', 'sr31c', 'sr31d', 'sr31f', 'sr31h', 'sr34a', 'sr34c',
                 'sr34f', 'sr34i', 'sr34j', 'sr34k', 'sr36a', 'sr36b', 'sr36c', 'sr36d',
                 'sr36e', 'sr36i', 'sr37a', 'sr37i', 'sr37j', 'sr39a', 'sr39b', 'sr39g',
                 'sr39h', 'sr39i', 'sr39j', 'sr40a', 'sr40c', 'sr40e', 'sr40f', 'sr40g',
                 'sr42b', 'sr42c', 'sr42f', 'sr42h', 'sr42j', 'sr09f', 'sr11f', 'sr11i',
                 'sr19a', 'sr22a', 'sr23f', 'sr26e', 'sr27a', 'sr27c', 'sr27e', 'sr34f',
                 'sr37j', 'sr01a', 'sr01d', 'sr30a', 'sr34k', 'sr37j']
        for samp in samps:
            sample = self.data2.find_by_name(samp, self.data2.samples)
            self.assertTrue(sample)
            self.assertTrue(sample.get_parent())
            self.assertTrue(sample.site)

        sites = ['sr01', 'sr03', 'sr04', 'sr09', 'sr11', 'sr12', 'sr16', 'sr19', 'sr20',
                 'sr21', 'sr22', 'sr23', 'sr24', 'sr25', 'sr26', 'sr27', 'sr28', 'sr29',
                 'sr30', 'sr31', 'sr34', 'sr36', 'sr37', 'sr39', 'sr40', 'sr42', 'sr09',
                 'sr11', 'sr19', 'sr22', 'sr23', 'sr26', 'sr27', 'sr34', 'sr37', 'sr01',
                 'sr01', 'sr30', 'sr34', 'sr37']
        for site_name in sites:
            site = self.data2.find_by_name(site_name, self.data2.sites)
            self.assertTrue(site)
            self.assertTrue(site.get_parent())
            self.assertTrue(site.location)

        warnings = self.data2.validate_data()

class TestPmagObject(unittest.TestCase):
    """
    Make sure automatic Pmag object stuff happens
    """

    def setUp(self):
        self.data3 = builder.ErMagicBuilder(WD, data_model)


    def test_adjust_to_360(self):
        """
        Make sure appropriate values (longitudes/azimuths/declinations)
        are corrected to be 0-360
        """
        er_data = {'site_dec': 370., 'site_lon': 280., 'site_decay': 700}
        site = self.data3.add_site('new_site', er_data=er_data)
        self.assertIn(site, self.data3.sites)
        self.assertAlmostEqual(10., site.er_data['site_dec'])
        self.assertAlmostEqual(280., site.er_data['site_lon'])
        self.assertAlmostEqual(700., site.er_data['site_decay'])

        self.data3.change_site('new_site', 'new_site', new_er_data={'site_azimuth': 3000,
                                                                    'site_other_azimuth': 30})
        self.assertAlmostEqual(120., site.er_data['site_azimuth'])
        self.assertAlmostEqual(30., site.er_data['site_other_azimuth'])


    def test_result_adjust_to_360(self):
        pmag_data = {'something_lon': 390., 'something_dec': 355.}
        res = self.data3.add_result('new_res', pmag_data=pmag_data)
        self.assertAlmostEqual(30., res.pmag_data['something_lon'])
        self.assertAlmostEqual(355., res.pmag_data['something_dec'])

        self.data3.change_result('new_res', 'new_res', new_pmag_data={'new_lon': 370.,
                                                                      'result_azimuth': 220.})
        self.assertAlmostEqual(30., res.pmag_data['something_lon'])
        self.assertAlmostEqual(355., res.pmag_data['something_dec'])
        self.assertAlmostEqual(10., res.pmag_data['new_lon'])
        self.assertAlmostEqual(220., res.pmag_data['result_azimuth'])
