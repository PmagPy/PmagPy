#!/usr/bin/env/python

"""
tests for validations
"""

import unittest
import os
import re
import sys
import pmagpy.validate_upload as validate_upload
import pmagpy.pmag as pmag

WD = sys.prefix

class TestValidation(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        # delete any upload file that was partially created
        directory = os.path.join(WD, 'pmagpy_data_files', 'testing', 'validation')
        pattern = re.compile('\w*[.]\w*[.]\w*[20]\d{2}\w*.txt$')
        possible_files = os.listdir(directory)
        files = []
        for f in possible_files:
            if f not in ['location1_30.Dec.2015.txt', 'location1_30.Dec.2015_1.txt']:
                if pattern.match(f):
                    files.append(f)
        pmag.remove_files(files, directory)

    def test_controlled_vocab(self):
        upfile = os.path.join(WD, 'pmagpy_data_files', 'testing',
                              'validation', 'location1_30.Dec.2015.txt')
        ran, errors = validate_upload.read_upload(upfile)
        self.assertFalse(ran)

        # site errors
        self.assertIn('site', errors)
        for sitename in ['site1', 'site2', 'site3']:
            self.assertIn(sitename, errors['site'])
            self.assertIn('vocab_problem', errors['site'][sitename])
        self.assertIn('class', errors['site']['site1']['vocab_problem'])
        self.assertIn('lithology', errors['site']['site2']['vocab_problem'])
        self.assertIn('type', errors['site']['site3']['vocab_problem'])

    def test_lat_lon(self):
        upfile = os.path.join(WD, 'pmagpy_data_files', 'testing',
                              'validation', 'location1_30.Dec.2015.txt')
        ran, errors = validate_upload.read_upload(upfile)
        self.assertFalse(ran)
        print errors
        self.assertIn('location', errors)
        self.assertIn('location1', errors['location'])
        self.assertIn('coordinates', errors['location']['location1'])
        self.assertIn('location_end_lat', errors['location']['location1']['coordinates'])
        self.assertIn('location_end_lon', errors['location']['location1']['coordinates'])
        self.assertIn('location_begin_lat', errors['location']['location1']['coordinates'])


    def test_missing_data(self):
        upfile = os.path.join(WD, 'pmagpy_data_files', 'testing',
                              'validation', 'location1_30.Dec.2015_1.txt')
        ran, errors = validate_upload.read_upload(upfile)
        self.assertFalse(ran)
        self.assertIn('site', errors)
        self.assertIn('site1', errors['site'])
        self.assertIn('missing_data', errors['site']['site1'])
        self.assertIn('site_type', errors['site']['site1']['missing_data'])


