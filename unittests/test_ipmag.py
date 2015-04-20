#!/usr/bin/env python

import unittest
import sys
import os
import numpy as np
import pmag
import ipmag
WD = os.getcwd()

class TestIGRF(unittest.TestCase):

    def setUp(self):
        pass

    def test_igrf_output(self):
        result = ipmag.igrf([1999.1, 30, 20, 50])
        reference = [  1.20288657e+00,   2.82331112e+01,   3.9782338913649881e+04]
        for num, item in enumerate(result):
            self.assertAlmostEqual(item, reference[num])

class TestUploadMagic(unittest.TestCase):

    def setUp(self):
        self.dir_path = os.path.join(os.getcwd(), 'unittests', 'examples')

    def test_empty_dir(self):
        outfile, error_message = ipmag.upload_magic(dir_path=os.path.join(self.dir_path, 'empty_dir'))
        self.assertFalse(outfile)
        self.assertEqual(error_message, "no data found, upload file not created")

    def test_with_invalid_files(self):
        outfile, error_message = ipmag.upload_magic(dir_path=os.path.join(self.dir_path, 'my_project_with_errors'))
        self.assertFalse(outfile)
        self.assertEqual(error_message, "file validation has failed.  You may run into problems if you try to upload this file.")
        directory = os.path.join(self.dir_path, 'my_project_with_errors')
        string = directory + '/' + '*.20*.txt'
        os.system('rm ' + string)

    def test_with_valid_files(self):
        print os.path.join(self.dir_path, 'my_project')
        outfile, error_message = ipmag.upload_magic(dir_path=os.path.join(self.dir_path, 'my_project'))
        self.assertTrue(outfile)
        self.assertEqual(error_message, '')
        assert os.path.isfile(outfile)
        directory = os.path.join(self.dir_path, 'my_project_with_errors')
        os.system('rm {}'.format(os.path.join(directory, outfile)))


class TestIODP_samples_magic(unittest.TestCase):

    def setUp(self):
        self.input_dir = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'IODP_srm_magic')

    def tearDown(self):
        os.chdir(WD)
        if os.path.isfile('./er_samples.txt'):
            os.system('rm er_samples.txt')
        
    def test_with_wrong_format(self):
        infile = os.path.join(self.input_dir, 'GCR_U1359_B_coresummary.csv')
        program_ran, error_message = ipmag.IODP_samples_magic(infile)
        self.assertFalse(program_ran)
        expected_error = 'Could not extract the necessary data from your input file.\nPlease make sure you are providing a correctly formated ODP samples csv file.'
        self.assertEqual(error_message, expected_error)


    def test_with_right_format(self):
        reference_file = os.path.join(WD, 'unittests', 'examples', 'ODP_magic_er_samples.txt')
        infile = os.path.join(self.input_dir, 'samples_318_U1359_B.csv')
        program_ran, outfile = ipmag.IODP_samples_magic(infile)
        self.assertTrue(program_ran)
        expected_file = os.path.join('.', 'er_samples.txt')
        self.assertEqual(outfile, expected_file)
        self.assertTrue(os.path.isfile(outfile))


    def test_content_with_right_format(self):
        reference_file = os.path.join(WD, 'unittests', 'examples', 'ODP_magic_er_samples.txt')
        infile = os.path.join(self.input_dir, 'samples_318_U1359_B.csv')
        program_ran, outfile = ipmag.IODP_samples_magic(infile)
        self.assertEqual(open(reference_file).readlines(), open(outfile).readlines())
        
        

class TestKly4s_magic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        for f in ['magic_measurements.txt', 'my_magic_measurements.txt', 'er_specimens.txt', 'er_samples.txt', 'er_sites.txt', 'rmag_anisotropy.txt', 'my_rmag_anisotropy.txt']:
            full_file = os.path.join(WD, f)
            if os.path.isfile(full_file):
                os.system('rm {}'.format(full_file))

    def test_kly4s_without_infile(self):
        with self.assertRaises(TypeError):
            ipmag.kly4s_magic()

    def test_kly4s_with_invalid_infile(self):
        program_ran, error_message = ipmag.kly4s_magic('hello.txt')
        expected_file = os.path.join('.', 'hello.txt')
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'Error opening file: {}'.format(expected_file))

    def test_kly4s_with_valid_infile(self):
        in_dir = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'kly4s_magic')
        program_ran, outfile = ipmag.kly4s_magic('KLY4S_magic_example.dat', output_dir_path=WD, input_dir_path=in_dir)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(WD, 'magic_measurements.txt'))

    def test_kly4s_fail_option4(self):
        in_dir = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'kly4s_magic')
        program_ran, error_message = ipmag.kly4s_magic('KLY4S_magic_example.dat', samp_con="4", output_dir_path=WD, input_dir_path=in_dir)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "option [4] must be in form 4-Z where Z is an integer")

    def test_kly4s_succeed_option4(self):
        in_dir = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'kly4s_magic')
        program_ran, outfile = ipmag.kly4s_magic('KLY4S_magic_example.dat', samp_con="4-2", output_dir_path=WD, input_dir_path=in_dir)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(WD, 'magic_measurements.txt'))
        self.assertTrue(os.path.isfile(os.path.join(WD, 'magic_measurements.txt')))

    def test_kly4s_with_options(self):
        in_dir = os.path.join(WD, 'Datafiles', 'Measurement_Import', 'kly4s_magic')
        program_ran, outfile = ipmag.kly4s_magic('KLY4S_magic_example.dat', specnum=1, locname="location", inst="instrument", samp_con=3, or_con=2, measfile='my_magic_measurements.txt', aniso_outfile="my_rmag_anisotropy.txt", output_dir_path=WD, input_dir_path=in_dir)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(WD, 'my_magic_measurements.txt'))
        self.assertTrue(os.path.isfile(os.path.join(WD, 'my_rmag_anisotropy.txt')))
        

class TestK15_magic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt', 'er_specimens.txt', 'er_samples.txt', 'my_er_samples.txt', 'er_sites.txt', 'rmag_anisotropy.txt', 'my_rmag_anisotropy.txt', 'rmag_results.txt', 'my_rmag_results.txt']
        pmag.remove_files(filelist, WD)

    def test_k15_with_no_files(self):
        with self.assertRaises(TypeError):
            ipmag.kly4s_magic()

    def test_k15_with_files(self):
        input_dir = os.path.join('Datafiles', 'Measurement_Import', 'k15_magic')
        program_ran, outfile  = ipmag.k15_magic('k15_example.dat', input_dir_path=input_dir)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join('.', 'magic_measurements.txt'))

    def test_k15_fail_option4(self):
        input_dir = os.path.join('Datafiles', 'Measurement_Import', 'k15_magic')
        program_ran, error_message = ipmag.k15_magic('k15_example.dat', sample_naming_con="4", input_dir_path=input_dir)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "option [4] must be in form 4-Z where Z is an integer")

    def test_k15_succeed_option4(self):
        input_dir = os.path.join('Datafiles', 'Measurement_Import', 'k15_magic')
        program_ran, outfile = ipmag.k15_magic('k15_example.dat', sample_naming_con="4-2", input_dir_path=input_dir)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(".", "magic_measurements.txt"))

    def test_k15_with_options(self):
        input_dir = os.path.join('Datafiles', 'Measurement_Import', 'k15_magic')
        program_ran, outfile = ipmag.k15_magic('k15_example.dat', specnum=2, sample_naming_con="3", er_location_name="Here", measfile="my_magic_measurements.txt", sampfile="my_er_samples.txt", aniso_outfile="my_rmag_anisotropy.txt", result_file="my_rmag_results.txt", input_dir_path=input_dir)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(".", "my_magic_measurements.txt"))
    

    

if __name__ == '__main__':
    unittest.main()

            
