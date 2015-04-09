#!/usr/bin/env python

import unittest
import sys
import os
import numpy as np
import ipmag
import sio_magic
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

    

    


    


