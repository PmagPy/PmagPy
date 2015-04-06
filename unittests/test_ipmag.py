#!/usr/bin/env python

import unittest
import sys
import os
import numpy as np
import ipmag

class TestIGRF(unittest.TestCase):

    def setUp(self):
        #print '!!!', os.listdir(os.getcwd())
        #print os.path.walk.__doc__#(os.path.join(os.getcwd(), 'unittests'))
        print 'unittest dir', os.path.join(os.getcwd(), 'unittests')
        print 'unittests exists?', os.path.exists(os.path.join(os.getcwd(), 'unittests'))
        print '!!!  listdir unittests', os.listdir(os.path.join(os.getcwd(), 'unittests'))
        print os.path.join(os.getcwd(), 'unittests', 'examples')
        print 'examples exists?', os.path.exists(os.path.join(os.getcwd(), 'unittests', 'examples'))
        print os.path.join(os.getcwd(), 'unittests', 'examples', 'empty_dir')
        print 'empty_dir exists?', os.path.exists(os.path.join(os.getcwd(), 'unittests', 'examples', 'empty_dir'))
        print os.path.join(os.getcwd(), 'unittests', 'examples', 'my_project')
        print 'my_project exists?', os.path.exists(os.path.join(os.getcwd(), 'unittests', 'examples', 'my_project'))

        #print 'setting up'

    def test_igrf_output(self):
        result = ipmag.igrf([1999.1, 30, 20, 50])
        reference = [  1.20288657e+00,   2.82331112e+01,   3.9782338913649881e+04]
        for num, item in enumerate(result):
            self.assertAlmostEqual(item, reference[num])

class TestUploadMagic(unittest.TestCase):

    def setUp(self):
        self.dir_path = os.path.join(os.getcwd(), 'unittests', 'examples')

    def test_empty_dir(self):
        print 'run test_empty_dir'
        print "os.path.join(self.dir_path, 'empty_dir')", os.path.join(self.dir_path, 'empty_dir')
        print 'os.getcwd()', os.getcwd()
        outfile, error_message = ipmag.upload_magic(dir_path=os.path.join(self.dir_path, 'empty_dir'))
        self.assertFalse(outfile)
        self.assertEqual(error_message, "no data found, upload file not created")

    def test_with_invalid_files(self):
        print 'run test_with_invalid_files'
        print "os.path.join(self.dir_path, 'my_project_with_errors')", os.path.join(self.dir_path, 'my_project_with_errors')
        print 'os.getcwd()', os.getcwd()
        print "os.listdir(os.path.join(self.dir_path, 'my_project_with_errors')", os.listdir(os.path.join(self.dir_path, 'my_project_with_errors'))

        outfile, error_message = ipmag.upload_magic(dir_path=os.path.join(self.dir_path, 'my_project_with_errors'))
        self.assertFalse(outfile)
        self.assertEqual(error_message, "file validation has failed.  You may run into problems if you try to upload this file.")

    def test_with_valid_files(self):
        print 'run test_with_valid_files'
        print "os.path.join(self.dir_path, 'my_project')", os.path.join(self.dir_path, 'my_project')
        print 'os.getcwd()', os.getcwd()
        print "os.listdir(os.path.join(self.dir_path, 'my_project')", os.listdir(os.path.join(self.dir_path, 'my_project'))

        print os.path.join(self.dir_path, 'my_project')
        outfile, error_message = ipmag.upload_magic(dir_path=os.path.join(self.dir_path, 'my_project'))
        self.assertTrue(outfile)
        self.assertEqual(error_message, '')
        assert os.path.isfile(outfile)


if __name__ == '__main__':
    unittest.main()

            
