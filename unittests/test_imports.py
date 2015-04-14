#!/usr/bin/env python

import unittest
import sys
import os
import numpy as np
import ipmag
import sio_magic
import IODP_csv_magic
import IODP_jr6_magic
WD = os.getcwd()

class TestSIO_magic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)
        #import sio_magic
        #pass

    def tearDown(self):
        meas_file = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'sio_magic', 'sio_af_example.magic')
        if os.path.isfile(meas_file):
            os.system('rm {}'.format(meas_file))

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

    
class TestIODP_csv_magic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        pass
        #meas_file = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'sio_magic', 'sio_af_example.magic')
        #if os.path.isfile(meas_file):
        #    os.system('rm {}'.format(meas_file))


    def test_IODP_with_no_files(self):
        program_ran, error_message = IODP_csv_magic.main(False)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'No .csv files were found')

    @unittest.skip("IODP_csv_magic must be fixed to accomodate old format, or the test must be changed to use the new format")
    def test_IODP_with_files(self):
        options = {}
        dir_path = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'IODP_csv_magic')
        options['dir_path'] = dir_path
        program_ran, outfile = IODP_csv_magic.main(False, **options)
        self.assertTrue(program_ran)

    @unittest.skip("IODP_csv_magic must be fixed to accomodate old format, or the test must be changed to use the new format")
    def test_IODP_with_one_file(self):
        options = {}
        dir_path = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'IODP_csv_magic')
        options['dir_path'] = dir_path
        options['csv_file'] = 'SRM_318_U1359_B_A.csv'
        program_ran, outfile = IODP_csv_magic.main(False, **options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, 'SRM_318_U1359_B_A.csv.magic')


class TestIODP_jr6_magic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        input_dir = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'IODP_jr6_magic')
        outfile = os.path.join(WD, 'test.magic')
        if os.path.isfile(outfile):
            os.system('rm {}'.format(outfile))

    def test_IODP_jr6_with_no_files(self):
        options = {}
        program_ran, error_message = IODP_jr6_magic.main(False, **options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "You must provide an IODP_jr6 format file")

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

    def test_IODP_jr6_with_magfile_but_hidden_sampfile(self):
        options = {}
        input_dir = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'IODP_jr6_magic')
        samp_file = os.path.join(input_dir, 'er_samples.txt')
        hidden_samp_file = os.path.join(input_dir, 'hidden_er_samples.txt')
        os.system('mv {} {}'.format(samp_file, hidden_samp_file))
        options['input_dir_path'] = input_dir
        mag_file = 'test.jr6'
        options['mag_file'] = mag_file
        program_ran, error_message = IODP_jr6_magic.main(False, **options)
        msg = "Your input directory:\n{}\nmust contain an er_samples.txt file".format(input_dir)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, msg)
        os.system('mv {} {}'.format(hidden_samp_file, samp_file))
