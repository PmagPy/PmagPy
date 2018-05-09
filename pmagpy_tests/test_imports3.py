#!/usr/bin/env python

import unittest
import os
#import sys
from pmagpy import pmag
from pmagpy import new_builder as nb
from programs.conversion_scripts import generic_magic
from programs.conversion_scripts import sio_magic
from programs.conversion_scripts import cit_magic
from programs.conversion_scripts import _2g_bin_magic
from programs.conversion_scripts import iodp_srm_magic
from programs.conversion_scripts import iodp_dscr_magic
from programs.conversion_scripts import iodp_jr6_magic
from programs.conversion_scripts import pmd_magic
from programs.conversion_scripts import huji_magic
from programs.conversion_scripts import ldeo_magic
from programs.conversion_scripts import jr6_txt_magic
from programs.conversion_scripts import utrecht_magic
from programs.conversion_scripts import bgc_magic
WD = pmag.get_test_WD()


class TestGenericMagic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        filelist = ['generic_magic_example.magic']
        directory = os.path.join(WD, 'data_files', 'Measurement_Import',
                                 'generic_magic')
        pmag.remove_files(filelist, directory)
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt']
        pmag.remove_files(filelist, WD)
        os.chdir(WD)

    def test_generic_magic_no_exp(self):
        dir_path = os.path.join('data_files', 'Measurement_Import',
                                'generic_magic')
        options = {}
        options['magfile'] = os.path.join(dir_path, 'generic_magic_example.txt')
        options['meas_file'] = os.path.join(dir_path, 'generic_magic_example.magic')
        program_ran, error_message = generic_magic.convert(**options)
        self.assertFalse(program_ran)
        self.assertEqual("-exp is required option", error_message)

    def test_generic_magic_success(self):
        dir_path = os.path.join('data_files', 'Measurement_Import',
                        'generic_magic')
        options = {}
        options['magfile'] = os.path.join(dir_path, 'generic_magic_example.txt')
        options['meas_file'] = os.path.join(dir_path, 'generic_magic_example.magic')
        options['experiment'] = 'Demag'
        program_ran, outfile_name = generic_magic.convert(**options)
        self.assertTrue(program_ran)
        print(os.path.realpath(options['meas_file']))
        self.assertEqual(os.path.realpath(outfile_name), os.path.realpath(options['meas_file']))


class TestSioMagic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        filelist = ['sio_af_example.magic']
        directory = os.path.join(WD, 'data_files', 'Measurement_Import',
                                 'sio_magic')
        pmag.remove_files(filelist, directory)
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt']
        pmag.remove_files(filelist, WD)
        os.chdir(WD)

    def test_sio_magic_no_files(self):
        program_ran, error_message = sio_magic.convert()
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'mag_file field is required option')

    def test_sio_magic_success(self):
        options = {}
        dir_path = os.path.join('data_files', 'Measurement_Import',
                                'sio_magic')
        options['mag_file'] = os.path.join(dir_path, 'sio_af_example.dat')
        options['meas_file'] = os.path.join(dir_path, 'sio_af_example.magic')
        program_ran, file_name = sio_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(file_name),
                         os.path.realpath(options['meas_file']))
        meas_df = nb.MagicDataFrame(options['meas_file'])
        self.assertIn('sequence', meas_df.df.columns)
        self.assertEqual(0, meas_df.df.iloc[0]['sequence'])

    def test_sio_magic_success_with_wd(self):
        options = {}
        dir_path = os.path.join('data_files', 'Measurement_Import',
                                'sio_magic')
        options['mag_file'] = os.path.join('sio_af_example.dat')
        options['meas_file'] = os.path.join('sio_af_example.magic')
        options['dir_path'] = dir_path
        program_ran, file_name = sio_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(file_name),
                         os.path.realpath(os.path.join(dir_path, options['meas_file'])))



    def test_sio_magic_fail_option4(self):
        options = {}
        options['mag_file'] = os.path.join(WD, 'data_files',
                                           'Measurement_Import', 'sio_magic',
                                           'sio_af_example.dat')
        meas_file = os.path.join(WD, 'data_files', 'Measurement_Import',
                                 'sio_magic', 'sio_af_example.magic')
        options['meas_file'] = meas_file
        options['samp_con'] = '4'
        program_ran, error_message = sio_magic.convert(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "naming convention option [4] must be in form 4-Z where Z is an integer")

    def test_sio_magic_succeed_option4(self):
        options = {}
        options['mag_file'] = os.path.join(WD, 'data_files',
                                           'Measurement_Import', 'sio_magic',
                                           'sio_af_example.dat')
        meas_file = os.path.join(WD, 'data_files', 'Measurement_Import',
                                 'sio_magic', 'sio_af_example.magic')
        options['meas_file'] = meas_file
        options['samp_con'] = '4-2'
        program_ran, file_name = sio_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(file_name, meas_file)


    def test_sio_magic_fail_with_coil(self):
        options = {}
        options['mag_file'] = os.path.join(WD, 'data_files',
                                           'Measurement_Import', 'sio_magic',
                                           'sio_af_example.dat')
        meas_file = os.path.join(WD, 'data_files', 'Measurement_Import',
                                 'sio_magic', 'sio_af_example.magic')
        options['meas_file'] = meas_file
        options['coil'] = 4
        program_ran, error_message = sio_magic.convert(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, '4 is not a valid coil specification')

    def test_sio_magic_succeed_with_coil(self):
        options = {}
        options['mag_file'] = os.path.join(WD, 'data_files',
                                           'Measurement_Import', 'sio_magic',
                                           'sio_af_example.dat')
        meas_file = os.path.join(WD, 'data_files', 'Measurement_Import',
                                 'sio_magic', 'sio_af_example.magic')
        options['meas_file'] = meas_file
        options['coil'] = '1'
        program_ran, file_name = sio_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(file_name, meas_file)


class TestCitMagic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt']
        pmag.remove_files(filelist, WD)
        #loc_file = 'custom_locations.txt'
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'custom_locations.txt']
        dir_path = os.path.join(WD, 'data_files')
        pmag.remove_files(filelist, dir_path)
        samp_file  = 'custom_samples.txt'
        dir_path = os.path.join(WD, 'data_files',
                     'Measurement_Import',
                     'CIT_magic', 'PI47')
        pmag.remove_files([samp_file], dir_path)
        os.chdir(WD)

    def test_cit_with_no_files(self):
        program_ran, error_message = cit_magic.convert()
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'bad sam file name')

    def test_cit_magic_with_file(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'data_files',
                                                 'Measurement_Import',
                                                 'CIT_magic', 'PI47')
        options['magfile'] = 'PI47-.sam'
        program_ran, outfile = cit_magic.convert(**options)
        self.assertTrue(program_ran)
        expected_file = os.path.join('measurements.txt')
        self.assertEqual(outfile, expected_file)
        meas_df = nb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)


    def test_cit_magic_with_path(self):
        options = {}
        #options['input_dir_path'] = os.path.join(WD, 'data_files',
        #                                         'Measurement_Import',
        #                                         'CIT_magic', 'PI47')pppp
        options['magfile'] = os.path.join(WD, 'data_files',
                                          'Measurement_Import',
                                          'CIT_magic', 'PI47', 'PI47-.sam')
        options['loc_file'] = 'custom_locations.txt'
        options['samp_file'] = os.path.join(WD, 'data_files',
                                            'Measurement_Import',
                                            'CIT_magic', 'PI47', 'custom_samples.txt')
        options['dir_path'] = os.path.join(WD, 'data_files')
        program_ran, outfile = cit_magic.convert(**options)
        self.assertTrue(program_ran)
        expected_file = os.path.join('measurements.txt')
        self.assertEqual(outfile, expected_file)
        for fname in [os.path.join(WD, 'data_files', options['loc_file']),
                      options['samp_file'],
                      os.path.join(WD, 'data_files', 'specimens.txt')]:
            self.assertTrue(os.path.isfile(fname))


    def test_cit_magic_fail_option4(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'data_files',
                                                 'Measurement_Import',
                                                 'CIT_magic', 'PI47')
        options['magfile'] = 'PI47-.sam'
        options['samp_con'] = '4'
        program_ran, error_message = cit_magic.convert(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "naming convention option [4] must be in form 4-Z where Z is an integer")

    def test_cit_magic_succeed_option4(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'data_files',
                                                 'Measurement_Import',
                                                 'CIT_magic', 'PI47')
        options['magfile'] = 'PI47-.sam'
        options['samp_con'] = '4-3'
        program_ran, outfile = cit_magic.convert(**options)
        self.assertTrue(program_ran)
        expected_file = os.path.join('measurements.txt')
        self.assertEqual(outfile, expected_file)

    def test_cit_magic_with_options(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'data_files',
                                                 'Measurement_Import',
                                                 'CIT_magic', 'PI47')
        options['magfile'] = 'PI47-.sam'
        options['samp_con'] = '2'
        options['methods'] = ['SO-SM:SO-MAG']
        options['locname'] = 'location'
        options['avg'] = 1
        options['specnum'] = 2
        program_ran, outfile = cit_magic.convert(**options)
        self.assertTrue(program_ran)
        expected_file = os.path.join('measurements.txt')
        self.assertEqual(outfile, expected_file)

    def test_cit_magic_with_other_data(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'data_files',
                                                 'Measurement_Import',
                                                 'CIT_magic', 'PI47')
        options['magfile'] = 'PI47-.sam'
        options['samp_con'] = '1'
        options['methods'] = ['SO-SM:SO-MAG']
        options['locname'] = 'location'
        options['avg'] = 1
        options['specnum'] = 2
        program_ran, outfile = cit_magic.convert(**options)
        self.assertTrue(program_ran)
        expected_file = os.path.join('measurements.txt')
        self.assertEqual(outfile, expected_file)


class TestIodpSrmMagic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        filelist = ['measurements.txt', 'specimens.txt', 'samples.txt',
                    'sites.txt', 'locations.txt',
                    'IODP_LIMS_SRMsection_366_U1494.csv.magic',
                    'IODP_LIMS_SRMsection_366_U1494_locations.txt',
                    'IODP_LIMS_SRMsection_366_U1494_samples.txt',
                    'IODP_LIMS_SRMsection_366_U1494_sites.txt',
                    'IODP_LIMS_SRMsection_366_U1494_specimens.txt']
        dir_path = os.path.join(WD, 'data_files', 'UTESTA', 'SRM_data')
        #directory = os.path.join(WD)
        pmag.remove_files(filelist, dir_path)
        dir_path = os.path.join(WD, 'data_files', 'Measurement_Import', 'IODP_srm_magic')
        pmag.remove_files(filelist, dir_path)
        dir_path = WD
        pmag.remove_files(filelist, dir_path)
        os.chdir(WD)

    def test_iodp_with_no_files(self):
        program_ran, error_message = iodp_srm_magic.convert()
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'No .csv files were found')

    #@unittest.skip("iodp_srm_magic is missing an example datafile")
    def test_iodp_with_files(self):
        options = {}
        dir_path = os.path.join(WD, 'data_files', 'Measurement_Import',
                                'IODP_srm_magic')
        options['dir_path'] = dir_path
        files = os.listdir(dir_path)
        files = ['IODP_Janus_312_U1256.csv', 'SRM_318_U1359_B_A.csv' ] # this one takes way too long: IODP_LIMS_SRMsection_344_1414A.csv
        info = []
        for f in files:
            if f.endswith('csv') and 'summary' not in f and 'discrete' not in f and 'sample' not in f:
                options['csv_file'] = f
                program_ran, outfile = iodp_srm_magic.convert(**options)
                meas_df = nb.MagicDataFrame(pmag.resolve_file_name(outfile, dir_path))
                self.assertTrue(len(meas_df.df) > 0)

    #@unittest.skip("iodp_srm_magic is missing an example datafile")
    def test_iodp_with_one_file(self):
        options = {}
        #dir_path = os.path.join(WD, 'data_files', 'Measurement_Import',
        # 'iodp_srm_magic')
        dir_path = os.path.join(WD, 'data_files', 'UTESTA', 'SRM_data')
        options['dir_path'] = dir_path
        options['input_dir_path'] = dir_path
        options['csv_file'] = 'srmsection-XXX-UTEST-A.csv'
        program_ran, outfile = iodp_srm_magic.convert(**options)
        self.assertEqual(program_ran, True)
        self.assertEqual(outfile, os.path.join('measurements.txt'))
        meas_df = nb.MagicDataFrame(os.path.join(dir_path, outfile))
        self.assertIn('sequence', meas_df.df.columns)


    def test_iodp_with_one_file_with_path(self):
        options = {}
        dir_path = os.path.join('data_files', 'UTESTA', 'SRM_data')
        #options['dir_path'] = dir_path
        options['dir_path'] = WD #dir_path
        options['input_dir_path'] = "fake/path"
        options['csv_file'] = os.path.join(dir_path, 'srmsection-XXX-UTEST-A.csv')
        program_ran, outfile = iodp_srm_magic.convert(**options)
        self.assertEqual(program_ran, True)
        self.assertEqual(outfile, os.path.join('measurements.txt'))


class TestIodpDscrMagic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        filelist = ['measurements.txt', 'specimens.txt', 'samples.txt',
                    'sites.txt', 'locations.txt', 'custom_samples.txt']
        #directory = os.path.join(WD)
        pmag.remove_files(filelist, WD)
        pmag.remove_files(['custom_measurements.txt'], os.path.join(WD, 'data_files'))
        os.chdir(WD)

    def test_iodp_with_no_files(self):
        program_ran, error_message = iodp_dscr_magic.convert()
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'No .csv files were found')

    #@unittest.skip("iodp_srm_magic is missing an example datafile")
    def test_iodp_with_one_file(self):
        options = {}
        #dir_path = os.path.join(WD, 'data_files', 'Measurement_Import',
        #'iodp_srm_magic')
        dir_path = os.path.join(WD, 'data_files', 'UTESTA', 'SRM_data')
        options['input_dir_path'] = dir_path
        options['csv_file'] = 'srmdiscrete-XXX-UTEST-A.csv'
        program_ran, outfile = iodp_dscr_magic.convert(**options)
        self.assertEqual(program_ran, True)
        self.assertEqual(outfile, 'measurements.txt')

    def test_iodp_with_path(self):
        options = {}
        #dir_path = os.path.join(WD, 'data_files', 'Measurement_Import',
        #'iodp_srm_magic')
        dir_path = os.path.join(WD, 'data_files', 'UTESTA', 'SRM_data')
        #options['input_dir_path'] = dir_path
        options['csv_file'] = os.path.join('data_files', 'UTESTA', 'SRM_data', 'srmdiscrete-XXX-UTEST-A.csv')
        options['meas_file'] = os.path.join(WD, 'data_files', 'custom_measurements.txt')
        options['samp_file'] = 'custom_samples.txt'
        program_ran, outfile = iodp_dscr_magic.convert(**options)
        self.assertEqual(program_ran, True)
        self.assertEqual(outfile, os.path.join(WD, 'data_files', 'custom_measurements.txt'))
        meas_df = nb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)


class TestPmdMagic(unittest.TestCase):

    def setUp(self):
        self.input_dir = os.path.join(WD, 'data_files',
                                      'Measurement_Import', 'PMD_magic', 'PMD', )

    def tearDown(self):
        filelist = ['specimens.txt', 'samples.txt', 'sites.txt',
                    'locations.txt', 'custom_specimens.txt', 'measurements.txt']
        pmag.remove_files(filelist, WD)
        pmag.remove_files(filelist, ".")
        os.chdir(WD)

    def test_pmd_with_no_files(self):
        program_ran, error_message = pmd_magic.convert()
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'mag_file field is required option')

    def test_pmd_success(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': 'ss0207a.pmd'}
        program_ran, outfile = pmd_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(outfile), os.path.join(WD, 'measurements.txt'))
        meas_df = nb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)



class TestJr6TxtMagic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        files = ['test.magic', 'other_er_samples.txt',
                 'custom_locations.txt', 'samples.txt', 'sites.txt']
        pmag.remove_files(files, WD)

    def test_success(self):
        input_dir = os.path.join(WD, 'data_files', 'Measurement_Import',
                                 'JR6_magic')
        output = jr6_txt_magic.convert(**{'mag_file': 'AP12.txt', 'input_dir_path': input_dir})
        self.assertTrue(output[0])
        self.assertEqual(output[1], 'measurements.txt')


class TestIodpJr6Magic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        files = ['test.magic', 'other_er_samples.txt',
                 'custom_locations.txt', 'samples.txt', 'sites.txt']
        pmag.remove_files(files, WD)
        # then, make sure that hidden_er_samples.txt has been successfully renamed to er_samples.txt
        input_dir = os.path.join(WD, 'data_files', 'Measurement_Import',
                                 'IODP_jr6_magic')
        hidden_sampfile = os.path.join(input_dir, 'hidden_er_samples.txt')
        sampfile = os.path.join(input_dir, 'er_samples.txt')
        if os.path.exists(hidden_sampfile):
            os.rename(hidden_sampfile, sampfile)
        pmag.remove_files(['custom_specimens.txt'], 'data_files')
        os.chdir(WD)

    def test_iodp_jr6_with_no_files(self):
        options = {}
        program_ran, error_message = iodp_jr6_magic.convert(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "You must provide an IODP_jr6 format file")

    def test_iodp_jr6_with_invalid_mag_file(self):
        options = {'mag_file': 'fake'}
        program_ran, error_message = iodp_jr6_magic.convert(**options)
        expected_msg = 'The input file you provided: {} does not exist.\nMake sure you have specified the correct filename AND correct input directory name.'.format(os.path.join('.', 'fake'))
        self.assertFalse(program_ran)
        self.assertEqual(error_message, expected_msg)


    #@unittest.skipIf('win32' in sys.platform or 'win62' in sys.platform, "Requires up to date version of pandas")
    def test_iodp_jr6_with_magfile(self):
        options = {}
        input_dir = os.path.join(WD, 'data_files', 'Measurement_Import',
                                 'IODP_jr6_magic')
        options['input_dir_path'] = input_dir
        mag_file = 'test.jr6'
        options['mag_file'] = 'test.jr6'
        meas_file = 'test.magic'
        options['meas_file'] = meas_file
        program_ran, outfile = iodp_jr6_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, meas_file)
        meas_df = nb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)


    def test_iodp_jr6_with_path(self):
        options = {}
        input_dir = os.path.join(WD, 'data_files', 'Measurement_Import',
                                 'IODP_jr6_magic')
        #options['input_dir_path'] = input_dir
        mag_file = os.path.join('data_files', 'Measurement_Import', 'IODP_jr6_magic', 'test.jr6')
        options['mag_file'] = mag_file #'test.jr6'
        options['spec_file'] = os.path.join('data_files', 'custom_specimens.txt')
        options['loc_file'] = 'custom_locations.txt'
        meas_file = 'test.magic'
        options['meas_file'] = meas_file
        program_ran, outfile = iodp_jr6_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, meas_file)
        for fname in [options['loc_file'], options['spec_file']]:
            self.assertTrue(os.path.isfile(fname))


    #@unittest.skipIf('win32' in sys.platform or 'win62' in sys.platform, "Requires up to date version of pandas")
    def test_iodp_jr6_with_options(self):
        options = {}
        input_dir = os.path.join(WD, 'data_files', 'Measurement_Import',
                                 'IODP_jr6_magic')
        options['input_dir_path'] = input_dir
        mag_file = 'test.jr6'
        options['mag_file'] = 'test.jr6'
        meas_file = 'test.magic'
        options['meas_file'] = meas_file
        options['noave'] = 1
        program_ran, outfile = iodp_jr6_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, meas_file)


class Test2g_bin_magic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        #input_dir = os.path.join(WD, 'data_files', 'Measurement_Import',
        #'IODP_jr6_magic')
        #files = ['test.magic', 'other_er_samples.txt']
        files = ['mn001-1a.magic', 'samples.txt', 'sites.txt',
                 'measurements.txt', 'locations.txt', 'specimens.txt']
        pmag.remove_files(files, WD)
        pmag.remove_files(['custom_specimens.txt', 'samples.txt',
                           'sites.txt', 'locations.txt'], 'data_files')
        pmag.remove_files(files, os.path.join(WD, 'data_files', 'Measurement_Import',
                                              '2G_bin_magic', 'mn1'))
        os.chdir(WD)

    def test_2g_with_no_files(self):
        options = {}
        program_ran, error_message = _2g_bin_magic.convert(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'mag file is required input')

    def test_2g_with_files(self):
        options = {}
        options['ID'] = os.path.join(WD, 'data_files', 'Measurement_Import',
                                     '2G_bin_magic', 'mn1')
        options['mag_file'] = 'mn001-1a.dat'
        program_ran, outfile = _2g_bin_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.split(outfile)[1], 'measurements.txt')
        self.assertTrue(os.path.isfile(outfile))
        meas_df = nb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)


    def test_2g_fail_option4(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'data_files',
                                                 'Measurement_Import',
                                                 '2G_bin_magic', 'mn1')
        options['magfile'] =  'mn001-1a.dat'
        options['samp_con'] = '4'
        program_ran, error_message = _2g_bin_magic.convert(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'option [4] must be in form 4-Z where Z is an integer')

    def test_2g_succeed_option4(self):
        options = {}
        options['ID'] = os.path.join(WD, 'data_files', 'Measurement_Import',
                                     '2G_bin_magic', 'mn1')
        options['mag_file'] =  'mn001-1a.dat'
        options['samp_con'] = '4-3'
        program_ran, outfile = _2g_bin_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.split(outfile)[1], 'measurements.txt')

    def test_2g_fail_option7(self):
        options = {}
        options['ID'] = os.path.join(WD, 'data_files', 'Measurement_Import',
                                     '2G_bin_magic', 'mn1')
        options['mag_file'] = 'mn001-1a.dat'
        options['samp_con'] = '7'
        program_ran, error_message = _2g_bin_magic.convert(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'option [7] must be in form 7-Z where Z is an integer')

    def test_2g_succeed_option7(self):
        options = {}
        options['ID'] = os.path.join(WD, 'data_files', 'Measurement_Import',
                                     '2G_bin_magic', 'mn1')
        options['mag_file'] = 'mn001-1a.dat'
        options['samp_con'] = '7-3'
        program_ran, outfile = _2g_bin_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.split(outfile)[1], 'measurements.txt')

    def test_2g_fail_option6(self):
        options = {}
        options['ID'] = os.path.join(WD, 'data_files', 'Measurement_Import',
                                     '2G_bin_magic', 'mn1')
        options['mag_file'] =  'mn001-1a.dat'
        options['samp_con'] = '6'
        program_ran, error_message = _2g_bin_magic.convert(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'Naming convention option [6] not currently supported')

    def test_2g_with_bad_file(self):
        options = {}
        options['ID'] = os.path.join(WD, 'data_files', 'Measurement_Import',
                                     '2G_bin_magic', 'mn1')
        options['mag_file'] =  'mn001-1ax.dat'
        program_ran, error_message = _2g_bin_magic.convert(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "bad mag file")

    def test_2g_with_options(self):
        options = {}
        options['ID'] = os.path.join(WD, 'data_files', 'Measurement_Import',
                                     '2G_bin_magic', 'mn1')
        options['mag_file'] = 'mn001-1a.dat'
        options['meas_file'] = 'mn001-1a.magic'
        options['samp_con'] = '4-3'
        options['inst'] = 'instrument'
        options['noave'] = 0
        options['specnum'] = 2
        options['location_name'] = 'location'
        options['or_con'] = '4'
        options['gmeths'] = 'FS-LOC-MAP:SO-POM'
        program_ran, outfile = _2g_bin_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.split(outfile)[1], 'mn001-1a.magic')

    def test_2g_with_path(self):
        options = {}
        input_dir = os.path.join(WD, 'data_files', 'Measurement_Import',
                                 '2G_bin_magic', 'mn1')
        #options['ID'] = os.path.join(WD, 'data_files', 'Measurement_Import',
        #                             '2G_bin_magic', 'mn1')
        options['mag_file'] = os.path.join(input_dir, 'mn001-1a.dat')
        options['meas_file'] = os.path.join(input_dir, 'mn001-1a.magic')
        options['spec_file'] = os.path.join('data_files', 'custom_specimens.txt')
        options['dir_path'] = 'data_files'
        program_ran, outfile = _2g_bin_magic.convert(**options)
        self.assertEqual(outfile, options['meas_file'])


class TestHujiMagic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        filelist = ['generic_magic_example.magic']
        directory = os.path.join(WD, 'data_files', 'Measurement_Import',
                                 'generic_magic')
        pmag.remove_files(filelist, directory)
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt']
        pmag.remove_files(filelist, WD)
        os.chdir(WD)

    def test_huji_magic_success(self):
        dir_path = os.path.join('data_files', 'Measurement_Import',
                                'HUJI_magic')
        options = {}
        options['input_dir_path'] = dir_path
        options['magfile'] = "Massada_AF_HUJI_new_format.txt"
        options['meas_file'] = "Massada_AF_HUJI_new_format.magic"
        options['codelist'] = 'AF'
        program_ran, outfile = huji_magic.convert(**options)
        self.assertTrue(program_ran)


class TestLdeoMagic(unittest.TestCase):

    def setUp(self):
        self.input_dir = os.path.join(WD, 'data_files',
                                      'Measurement_Import', 'LDEO_magic')

    def tearDown(self):
        #filelist = ['measurements.txt', 'specimens.txt',
        #            'samples.txt', 'sites.txt']
        #pmag.remove_files(filelist, self.input_dir)
        filelist = ['specimens.txt', 'samples.txt', 'sites.txt',
                    'locations.txt', 'custom_specimens.txt', 'measurements.txt']
        pmag.remove_files(filelist, WD)
        #pmag.remove_files(filelist, os.path.join(WD, 'data_files'))
        os.chdir(WD)

    def test_ldeo_with_no_files(self):
        program_ran, error_message = ldeo_magic.convert()
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'mag_file field is required option')

    def test_ldeo_success(self):
        options = {'input_dir_path': self.input_dir, 'magfile': 'ldeo_magic_example.dat'}
        program_ran, outfile = ldeo_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(outfile), os.path.join(WD, 'measurements.txt'))
        meas_df = nb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)


class TestBgcMagic(unittest.TestCase):

    def setUp(self):
        self.input_dir = os.path.join(WD, 'data_files',
                                      'Measurement_Import', 'BGC_magic')

    def tearDown(self):
        filelist = ['96MT.05.01.magic', 'BC0-3A.magic',
                    'measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt']
        pmag.remove_files(filelist, self.input_dir)
        filelist = ['specimens.txt', 'samples.txt', 'sites.txt',
                    'locations.txt', 'custom_specimens.txt', 'measurements.txt']
        pmag.remove_files(filelist, WD)
        pmag.remove_files(filelist, os.path.join(WD, 'data_files'))
        os.chdir(WD)

    def test_bgc_with_no_files(self):
        program_ran, error_message = bgc_magic.convert()
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'You must provide a BCG format file')

    def test_bgc_success(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': '96MT.05.01'}
        program_ran, outfile = bgc_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(WD, 'measurements.txt'))
        meas_df = nb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)


    def test_bgc_with_path(self):
        options = {}
        options['mag_file'] = os.path.join(self.input_dir, '96MT.05.01')
        options['spec_file'] = os.path.join(WD, 'custom_specimens.txt')
        options['dir_path'] = 'data_files'
        program_ran, outfile = bgc_magic.convert(**options)
        self.assertEqual(outfile, os.path.join(WD, 'data_files', 'measurements.txt'))
        self.assertTrue(os.path.isfile(options['spec_file']))
        self.assertTrue(os.path.isfile(os.path.join(WD, 'data_files', 'samples.txt')))


    def test_bgc_alternate_infile(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': 'BC0-3A'}
        program_ran, outfile = bgc_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(WD, 'measurements.txt'))


    def test_bgc_with_append(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': 'BC0-3A'}
        program_ran, outfile = bgc_magic.convert(**options)
        self.assertTrue(program_ran)
        options['append'] = True
        program_ran, outfile = bgc_magic.convert(**options)
        self.assertTrue(program_ran)
        lines, file_type = pmag.magic_read(os.path.join(WD, 'specimens.txt'))
        self.assertEqual(len(lines), 2)



class TestUtrechtMagic(unittest.TestCase):

    def setUp(self):
        self.input_dir = os.path.join(WD, 'data_files',
                                      'Measurement_Import', 'UTRECHT_magic')

    def tearDown(self):
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt', 'custom.out']
        pmag.remove_files(filelist, WD)
        #filelist = ['specimens.txt', 'samples.txt', 'sites.txt',
        #            'locations.txt', 'custom_specimens.txt', 'measurements.txt']
        pmag.remove_files(filelist, '.')
        pmag.remove_files(filelist, os.path.join(WD, 'data_files'))
        os.chdir(WD)

    def test_utrecht_with_no_files(self):
        program_ran, error_message = utrecht_magic.convert()
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'You must provide a Utrecht format file')

    def test_utrecht_success(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': 'Utrecht_Example.af'}
        program_ran, outfile = utrecht_magic.convert(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(outfile), os.path.join(WD, 'measurements.txt'))
        meas_df = nb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)
