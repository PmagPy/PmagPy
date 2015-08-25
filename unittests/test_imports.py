#!/usr/bin/env python

import unittest
#import sys
import os
#import numpy as np
import pmag
#import ipmag
import sio_magic
import CIT_magic
import IODP_srm_magic
import IODP_dscr_magic
import IODP_jr6_magic
import _2G_bin_magic
import BGC_magic
WD = os.getcwd()

class TestSIO_magic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        filelist = ['sio_af_example.magic']
        directory = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'sio_magic')
        pmag.remove_files(filelist, directory)

    def test_SIO_magic_no_files(self):
        program_ran, error_message = sio_magic.main(False)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'mag_file field is required option')
        
    def test_SIO_magic_success(self):
        options = {}
        options['mag_file'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'sio_magic', 'sio_af_example.dat')
        meas_file = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'sio_magic', 'sio_af_example.magic')
        options['meas_file'] = meas_file
        program_ran, file_name = sio_magic.main(False, **options)
        self.assertTrue(program_ran)
        self.assertEqual(file_name, meas_file)

    def test_SIO_magic_fail_option4(self):
        options = {}
        options['mag_file'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'sio_magic', 'sio_af_example.dat')
        meas_file = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'sio_magic', 'sio_af_example.magic')
        options['meas_file'] = meas_file
        options['samp_con'] = '4'
        program_ran, error_message = sio_magic.main(False, **options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "naming convention option [4] must be in form 4-Z where Z is an integer")

    def test_SIO_magic_succeed_option4(self):
        options = {}
        options['mag_file'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'sio_magic', 'sio_af_example.dat')
        meas_file = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'sio_magic', 'sio_af_example.magic')
        options['meas_file'] = meas_file
        options['samp_con'] = '4-2'
        program_ran, file_name = sio_magic.main(False, **options)
        self.assertTrue(program_ran)
        self.assertEqual(file_name, meas_file)


    def test_SIO_magic_fail_with_coil(self):
        options = {}
        options['mag_file'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'sio_magic', 'sio_af_example.dat')
        meas_file = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'sio_magic', 'sio_af_example.magic')
        options['meas_file'] = meas_file
        options['coil'] = 4
        program_ran, error_message = sio_magic.main(False, **options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, '4 is not a valid coil specification')

    def test_SIO_magic_succeed_with_coil(self):
        options = {}
        options['mag_file'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'sio_magic', 'sio_af_example.dat')
        meas_file = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'sio_magic', 'sio_af_example.magic')
        options['meas_file'] = meas_file
        options['coil'] = '1'
        program_ran, file_name = sio_magic.main(False, **options)
        self.assertTrue(program_ran)
        self.assertEqual(file_name, meas_file)


class TestCIT_magic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        filelist= ['magic_measurements.txt', 'er_specimens.txt', 'er_samples.txt', 'er_sites.txt']
        pmag.remove_files(filelist, WD)

    def test_CIT_with_no_files(self):
        program_ran, error_message = CIT_magic.main(False)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'bad sam file name')

    def test_CIT_magic_with_file(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'CIT_magic', 'MP18')
        options['magfile'] = 'bMP.sam'
        program_ran, outfile = CIT_magic.main(False, **options)
        self.assertTrue(program_ran)
        expected_file = os.path.join('.', 'magic_measurements.txt')
        self.assertEqual(outfile, expected_file)

    def test_CIT_magic_fail_option4(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'CIT_magic', 'MP18')
        options['magfile'] = 'bMP.sam'
        options['samp_con'] = '4'
        program_ran, error_message = CIT_magic.main(False, **options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "naming convention option [4] must be in form 4-Z where Z is an integer")

    def test_CIT_magic_succeed_option4(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'CIT_magic', 'MP18')
        options['magfile'] = 'bMP.sam'
        options['samp_con'] = '4-3'
        program_ran, outfile = CIT_magic.main(False, **options)
        self.assertTrue(program_ran)
        expected_file = os.path.join('.', 'magic_measurements.txt')
        self.assertEqual(outfile, expected_file)

    def test_CIT_magic_with_options(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'CIT_magic', 'MP18')
        options['magfile'] = 'bMP.sam'
        options['samp_con'] = '2'
        options['methods'] = ['SO-SM:SO-MAG']
        options['locname'] = 'location'
        options['avg'] = 1
        options['specnum'] = 2
        program_ran, outfile = CIT_magic.main(False, **options)
        self.assertTrue(program_ran)
        expected_file = os.path.join('.', 'magic_measurements.txt')
        self.assertEqual(outfile, expected_file)

    def test_CIT_magic_with_other_data(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'CIT_magic', 'Z35')
        options['magfile'] = 'Z35.sam'
        options['samp_con'] = '1'
        options['methods'] = ['SO-SM:SO-MAG']
        options['locname'] = 'location'
        options['avg'] = 1
        options['specnum'] = 2
        program_ran, outfile = CIT_magic.main(False, **options)
        self.assertTrue(program_ran)
        expected_file = os.path.join('.', 'magic_measurements.txt')
        self.assertEqual(outfile, expected_file)

        
class TestIODP_srm_magic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'er_specimens.txt', 'er_samples.txt', 'er_sites.txt', 'er_locations.txt']
        #directory = os.path.join(WD)
        pmag.remove_files(filelist, WD)

    def test_IODP_with_no_files(self):
        program_ran, error_message = IODP_srm_magic.main(False)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'No .csv files were found')

    @unittest.skip("IODP_srm_magic is missing an example datafile")
    def test_IODP_with_files(self):
        options = {}
        dir_path = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'IODP_srm_magic')
        options['dir_path'] = dir_path
        program_ran, outfile = IODP_srm_magic.main(False, **options)
        self.assertTrue(program_ran)

    #@unittest.skip("IODP_srm_magic is missing an example datafile")
    def test_IODP_with_one_file(self):
        options = {}
        #dir_path = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'IODP_srm_magic')
        dir_path = os.path.join(WD, 'Datafiles', 'UTESTA', 'SRM_data')
        options['input_dir_path'] = dir_path
        options['csv_file'] = 'srmsection-XXX-UTEST-A.csv'
        program_ran, outfile = IODP_srm_magic.main(False, **options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join('.', 'magic_measurements.txt'))


class TestIODP_dscr_magic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'er_specimens.txt', 'er_samples.txt', 'er_sites.txt', 'er_locations.txt']
        #directory = os.path.join(WD)
        pmag.remove_files(filelist, WD)

    def test_IODP_with_no_files(self):
        program_ran, error_message = IODP_dscr_magic.main(False)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'No .csv files were found')

    #@unittest.skip("IODP_srm_magic is missing an example datafile")
    def test_IODP_with_one_file(self):
        options = {}
        #dir_path = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'IODP_srm_magic')
        dir_path = os.path.join(WD, 'Datafiles', 'UTESTA', 'SRM_data')
        options['input_dir_path'] = dir_path
        options['csv_file'] = 'srmdiscrete-XXX-UTEST-A.csv'
        program_ran, outfile = IODP_dscr_magic.main(False, **options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join('.', 'magic_measurements.txt'))



class TestIODP_jr6_magic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        files = ['test.magic', 'other_er_samples.txt']
        pmag.remove_files(files, WD)
        # then, make sure that hidden_er_samples.txt has been successfully renamed to er_samples.txt
        input_dir = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'IODP_jr6_magic')
        hidden_sampfile = os.path.join(input_dir, 'hidden_er_samples.txt')
        sampfile = os.path.join(input_dir, 'er_samples.txt')
        if os.path.exists(hidden_sampfile):
            os.rename(hidden_sampfile, sampfile)

    def test_IODP_jr6_with_no_files(self):
        options = {}
        program_ran, error_message = IODP_jr6_magic.main(False, **options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "You must provide an IODP_jr6 format file")

    #@unittest.skipIf('win32' in sys.platform or 'win62' in sys.platform, "Requires up to date version of pandas")
    def test_IODP_jr6_with_magfile(self):
        options = {}
        input_dir = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'IODP_jr6_magic')
        options['input_dir_path'] = input_dir
        mag_file = 'test.jr6'
        options['mag_file'] = 'test.jr6'
        meas_file = 'test.magic'
        options['meas_file'] = meas_file
        program_ran, outfile = IODP_jr6_magic.main(False, **options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join('.', meas_file))

    #@unittest.skipIf('win32' in sys.platform or 'win62' in sys.platform, "Requires up to date version of pandas")
    def test_IODP_jr6_with_options(self):
        options = {}
        input_dir = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'IODP_jr6_magic')
        options['input_dir_path'] = input_dir
        mag_file = 'test.jr6'
        options['mag_file'] = 'test.jr6'
        meas_file = 'test.magic'
        options['meas_file'] = meas_file
        options['noave'] = 1
        program_ran, outfile = IODP_jr6_magic.main(False, **options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join('.', meas_file))

    #@unittest.skipIf('win32' in sys.platform or 'win62' in sys.platform, "Requires up to date version of pandas")
    def test_IODP_jr6_with_magfile_but_hidden_sampfile(self):
        options = {}
        input_dir = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'IODP_jr6_magic')
        samp_file = os.path.join(input_dir, 'er_samples.txt')
        hidden_samp_file = os.path.join(input_dir, 'hidden_er_samples.txt')
        os.rename(samp_file, hidden_samp_file)
        options['input_dir_path'] = input_dir
        mag_file = 'test.jr6'
        options['mag_file'] = mag_file
        program_ran, error_message = IODP_jr6_magic.main(False, **options)
        msg = "Your input directory:\n{}\nmust contain an er_samples.txt file, or you must explicitly provide one".format(input_dir)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, msg)
        os.rename(hidden_samp_file, samp_file)


class Test2G_bin_magic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        #input_dir = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'IODP_jr6_magic')
        #files = ['test.magic', 'other_er_samples.txt']
        files = ['mn001-1a.magic', 'er_samples.txt', 'er_sites.txt', 'magic_measurements.txt']
        pmag.remove_files(files, WD)

    def test_2G_with_no_files(self):
        options = {}
        program_ran, error_message = _2G_bin_magic.main(False, **options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'mag file is required input')

    def test_2G_with_files(self):
        options = {}
        options['ID'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', '2G_bin_magic', 'mn1')
        options['mag_file'] = 'mn001-1a.dat'
        program_ran, outfile = _2G_bin_magic.main(False, **options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, './magic_measurements.txt')
        self.assertTrue(os.path.isfile(outfile))


    def test_2G_fail_option4(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', '2G_bin_magic', 'mn1')
        options['magfile'] =  'mn001-1a.dat'
        options['samp_con'] = '4'
        program_ran, error_message = _2G_bin_magic.main(False, **options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'option [4] must be in form 4-Z where Z is an integer')

    def test_2G_succeed_option4(self):
        options = {}
        options['ID'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', '2G_bin_magic', 'mn1')
        options['mag_file'] =  'mn001-1a.dat'
        options['samp_con'] = '4-3'
        program_ran, outfile = _2G_bin_magic.main(False, **options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, './magic_measurements.txt')

    def test_2G_fail_option7(self):
        options = {}
        options['ID'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', '2G_bin_magic', 'mn1')
        options['mag_file'] = 'mn001-1a.dat'
        options['samp_con'] = '7'
        program_ran, error_message = _2G_bin_magic.main(False, **options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'option [7] must be in form 7-Z where Z is an integer')

    def test_2G_succeed_option7(self):
        options = {}
        options['ID'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', '2G_bin_magic', 'mn1')
        options['mag_file'] = 'mn001-1a.dat'
        options['samp_con'] = '7-3'
        program_ran, outfile = _2G_bin_magic.main(False, **options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, './magic_measurements.txt')

    def test_2G_fail_option6(self):
        options = {}
        options['ID'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', '2G_bin_magic', 'mn1')
        options['mag_file'] =  'mn001-1a.dat'
        options['samp_con'] = '6'
        program_ran, error_message = _2G_bin_magic.main(False, **options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "there is no er_samples.txt file in your input directory - you can't use naming convention #6")

    def test_2G_with_bad_file(self):
        options = {}
        options['ID'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', '2G_bin_magic', 'mn1')
        options['mag_file'] =  'mn001-1ax.dat'
        program_ran, error_message = _2G_bin_magic.main(False, **options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "bad mag file")

    def test_2G_with_options(self):
        options = {}
        options['ID'] = os.path.join(WD, 'Datafiles', 'Measurement_Import', '2G_bin_magic', 'mn1')
        options['mag_file'] = 'mn001-1a.dat'
        options['meas_file'] = 'mn001-1a.magic'
        options['samp_con'] = '4-3'
        options['inst'] = 'instrument'
        options['noave'] = 0
        options['specnum'] = 2
        options['location_name'] = 'location'
        options['or_con'] = '4'
        options['gmeths'] = 'FS-LOC-MAP:SO-POM'
        program_ran, outfile = _2G_bin_magic.main(False, **options)
        self.assertTrue(program_ran)
        
        
class TestBGC_magic(unittest.TestCase):

    def setUp(self):
        self.input_dir = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'BGC_magic')
        os.chdir(WD)

    def tearDown(self):
        filelist = ['96MT.05.01.magic', 'BC0-3A.magic', 'magic_measurements.txt', 'er_specimens.txt', 'er_samples.txt', 'er_sites.txt']
        pmag.remove_files(filelist, self.input_dir)

    def test_BGC_with_no_files(self):
        program_ran, error_message = BGC_magic.main(False)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'You must provide a BCG format file')

    def test_BGC_success(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': '96MT.05.01'}
        program_ran, outfile = BGC_magic.main(False, **options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join('.', 'magic_measurements.txt'))
        
    def test_BGC_alternate_infile(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': 'BC0-3A'}
        program_ran, outfile = BGC_magic.main(False, **options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join('.', 'magic_measurements.txt'))

