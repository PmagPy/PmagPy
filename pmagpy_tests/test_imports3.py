#!/usr/bin/env python

import unittest
import os
#import sys
from pmagpy import pmag
from pmagpy import contribution_builder as cb
from pmagpy import convert_2_magic as convert
WD = pmag.get_test_WD()


class Test2g_bin_magic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        #input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
        #'IODP_jr6_magic')
        #files = ['test.magic', 'other_er_samples.txt']
        files = ['mn001-1a.magic', 'samples.txt', 'sites.txt',
                 'measurements.txt', 'locations.txt', 'specimens.txt']
        pmag.remove_files(files, WD)
        pmag.remove_files(['custom_specimens.txt', 'samples.txt',
                           'sites.txt', 'locations.txt'], 'data_files')
        pmag.remove_files(files, os.path.join(WD, 'data_files', 'convert_2_magic',
                                              '2g_bin_magic', 'mn1'))
        os.chdir(WD)

    def test_2g_with_no_files(self):
        options = {}
        program_ran, error_message = convert._2g_bin(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'mag file is required input')

    def test_2g_with_files(self):
        options = {}
        options['input_dir'] = os.path.join(WD, 'data_files', 'convert_2_magic',
                                     '2g_bin_magic', 'mn1')
        options['mag_file'] = 'mn001-1a.dat'
        program_ran, outfile = convert._2g_bin(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.split(outfile)[1], 'measurements.txt')
        self.assertTrue(os.path.isfile(outfile))
        meas_df = cb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)


    def test_2g_fail_option4(self):
        options = {}
        options['input_dir'] = os.path.join(WD, 'data_files',
                                            'convert_2_magic',
                                            '2g_bin_magic', 'mn1')
        options['mag_file'] =  'mn001-1a.dat'
        options['samp_con'] = '4'
        program_ran, error_message = convert._2g_bin(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'option [4] must be in form 4-Z where Z is an integer')

    def test_2g_succeed_option4(self):
        options = {}
        options['input_dir'] = os.path.join(WD, 'data_files', 'convert_2_magic',
                                     '2g_bin_magic', 'mn1')
        options['mag_file'] =  'mn001-1a.dat'
        options['samp_con'] = '4-3'
        program_ran, outfile = convert._2g_bin(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.split(outfile)[1], 'measurements.txt')

    def test_2g_fail_option7(self):
        options = {}
        options['input_dir'] = os.path.join(WD, 'data_files', 'convert_2_magic',
                                     '2g_bin_magic', 'mn1')
        options['mag_file'] = 'mn001-1a.dat'
        options['samp_con'] = '7'
        program_ran, error_message = convert._2g_bin(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'option [7] must be in form 7-Z where Z is an integer')

    def test_2g_succeed_option7(self):
        options = {}
        options['input_dir'] = os.path.join(WD, 'data_files', 'convert_2_magic',
                                     '2g_bin_magic', 'mn1')
        options['mag_file'] = 'mn001-1a.dat'
        options['samp_con'] = '7-3'
        program_ran, outfile = convert._2g_bin(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.split(outfile)[1], 'measurements.txt')

    def test_2g_fail_option6(self):
        options = {}
        options['input_dir'] = os.path.join(WD, 'data_files', 'convert_2_magic',
                                     '2g_bin_magic', 'mn1')
        options['mag_file'] =  'mn001-1a.dat'
        options['samp_con'] = '6'
        program_ran, error_message = convert._2g_bin(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'Naming convention option [6] not currently supported')

    def test_2g_with_bad_file(self):
        options = {}
        options['input_dir'] = os.path.join(WD, 'data_files', 'convert_2_magic',
                                     '2g_bin_magic', 'mn1')
        options['mag_file'] =  'mn001-1ax.dat'
        program_ran, error_message = convert._2g_bin(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "bad mag file")

    def test_2g_with_options(self):
        options = {}
        options['input_dir'] = os.path.join(WD, 'data_files', 'convert_2_magic',
                                     '2g_bin_magic', 'mn1')
        options['mag_file'] = 'mn001-1a.dat'
        options['meas_file'] = 'mn001-1a.magic'
        options['samp_con'] = '4-3'
        options['inst'] = 'instrument'
        options['noave'] = 0
        options['specnum'] = 2
        options['location'] = 'location'
        options['or_con'] = '4'
        options['gmeths'] = 'FS-LOC-MAP:SO-POM'
        program_ran, outfile = convert._2g_bin(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.split(outfile)[1], 'mn001-1a.magic')

    def test_2g_with_path(self):
        options = {}
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 '2g_bin_magic', 'mn1')
        #options['input_dir'] = os.path.join(WD, 'data_files', 'convert_2_magic',
        #                             '2g_bin_magic', 'mn1')
        options['mag_file'] = os.path.join(input_dir, 'mn001-1a.dat')
        options['meas_file'] = os.path.join(input_dir, 'mn001-1a.magic')
        options['spec_file'] = os.path.join('data_files', 'custom_specimens.txt')
        options['dir_path'] = 'data_files'
        program_ran, outfile = convert._2g_bin(**options)
        self.assertEqual(outfile, options['meas_file'])


class TestAgmMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt',
                    'agm_magic_example.magic', 'agm_magic_example_locations.txt',
                    'agm_magic_example_specimens.txt']
        pmag.remove_files(filelist, WD)
        os.chdir(WD)


    def test_success(self):
        input_dir = os.path.join(WD, 'data_files',
                                 'convert_2_magic', 'agm_magic')
        program_ran, filename = convert.agm('agm_magic_example.agm',
                                            meas_outfile='agm_magic_example.magic',
                                            input_dir_path=input_dir, fmt="old")
        self.assertTrue(program_ran)

    def test_backfield_success(self):
        input_dir = os.path.join(WD, 'data_files',
                                 'convert_2_magic', 'agm_magic')
        program_ran, filename = convert.agm('agm_magic_example.irm',
                                            meas_outfile='agm_magic_example.magic',
                                            input_dir_path=input_dir, fmt="old", bak=True,
                                            instrument="SIO-FLO")


class TestBgcMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)
        self.input_dir = os.path.join(WD, 'data_files',
                                      'convert_2_magic', 'bgc_magic')

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
        with self.assertRaises(TypeError):
            convert.bgc()

    def test_bgc_success(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': '96MT.05.01'}
        program_ran, outfile = convert.bgc(**options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(WD, 'measurements.txt'))
        meas_df = cb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)


    def test_bgc_with_path(self):
        options = {}
        options['mag_file'] = os.path.join(self.input_dir, '96MT.05.01')
        options['spec_file'] = os.path.join(WD, 'custom_specimens.txt')
        options['dir_path'] = 'data_files'
        program_ran, outfile = convert.bgc(**options)
        self.assertEqual(outfile, os.path.join(WD, 'data_files', 'measurements.txt'))
        self.assertTrue(os.path.isfile(options['spec_file']))
        self.assertTrue(os.path.isfile(os.path.join(WD, 'data_files', 'samples.txt')))


    def test_bgc_alternate_infile(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': 'BC0-3A'}
        program_ran, outfile = convert.bgc(**options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(WD, 'measurements.txt'))


    def test_bgc_with_append(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': 'BC0-3A'}
        program_ran, outfile = convert.bgc(**options)
        self.assertTrue(program_ran)
        options['append'] = True
        program_ran, outfile = convert.bgc(**options)
        self.assertTrue(program_ran)
        lines, file_type = pmag.magic_read(os.path.join(WD, 'specimens.txt'))
        self.assertEqual(len(lines), 2)


class TestCitMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

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
                     'convert_2_magic',
                     'cit_magic', 'PI47')
        pmag.remove_files([samp_file], dir_path)
        os.chdir(WD)

    def test_cit_with_no_files(self):
        program_ran, error_message = convert.cit()
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'bad sam file name')

    def test_cit_magic_with_file(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'data_files',
                                                 'convert_2_magic',
                                                 'cit_magic', 'PI47')
        options['magfile'] = 'PI47-.sam'
        program_ran, outfile = convert.cit(**options)
        self.assertTrue(program_ran)
        expected_file = os.path.join('measurements.txt')
        self.assertEqual(outfile, expected_file)
        meas_df = cb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)


    def test_cit_magic_with_path(self):
        options = {}
        #options['input_dir_path'] = os.path.join(WD, 'data_files',
        #                                         'convert_2_magic',
        #                                         'cit_magic', 'PI47')pppp
        options['magfile'] = os.path.join(WD, 'data_files',
                                          'convert_2_magic',
                                          'cit_magic', 'PI47', 'PI47-.sam')
        options['loc_file'] = 'custom_locations.txt'
        options['samp_file'] = os.path.join(WD, 'data_files',
                                            'convert_2_magic',
                                            'cit_magic', 'PI47', 'custom_samples.txt')
        options['dir_path'] = os.path.join(WD, 'data_files')
        program_ran, outfile = convert.cit(**options)
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
                                                 'convert_2_magic',
                                                 'cit_magic', 'PI47')
        options['magfile'] = 'PI47-.sam'
        options['samp_con'] = '4'
        program_ran, error_message = convert.cit(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "naming convention option [4] must be in form 4-Z where Z is an integer")

    def test_cit_magic_succeed_option4(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'data_files',
                                                 'convert_2_magic',
                                                 'cit_magic', 'PI47')
        options['magfile'] = 'PI47-.sam'
        options['samp_con'] = '4-3'
        program_ran, outfile = convert.cit(**options)
        self.assertTrue(program_ran)
        expected_file = os.path.join('measurements.txt')
        self.assertEqual(outfile, expected_file)

    def test_cit_magic_with_options(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'data_files',
                                                 'convert_2_magic',
                                                 'cit_magic', 'PI47')
        options['magfile'] = 'PI47-.sam'
        options['samp_con'] = '2'
        options['methods'] = ['SO-SM:SO-MAG']
        options['locname'] = 'location'
        options['noave'] = 1
        options['specnum'] = 2
        program_ran, outfile = convert.cit(**options)
        self.assertTrue(program_ran)
        expected_file = os.path.join('measurements.txt')
        self.assertEqual(outfile, expected_file)

    def test_cit_magic_with_other_data(self):
        options = {}
        options['input_dir_path'] = os.path.join(WD, 'data_files',
                                                 'convert_2_magic',
                                                 'cit_magic', 'PI47')
        options['magfile'] = 'PI47-.sam'
        options['samp_con'] = '1'
        options['methods'] = ['SO-SM:SO-MAG']
        options['locname'] = 'location'
        options['noave'] = 1
        options['specnum'] = 2
        program_ran, outfile = convert.cit(**options)
        self.assertTrue(program_ran)
        expected_file = os.path.join('measurements.txt')
        self.assertEqual(outfile, expected_file)


class TestGenericMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        filelist = ['generic_magic_example.magic']
        directory = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'generic_magic')
        pmag.remove_files(filelist, directory)
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt']
        pmag.remove_files(filelist, WD)
        os.chdir(WD)

    def test_generic_magic_no_exp(self):
        dir_path = os.path.join('data_files', 'convert_2_magic',
                                'generic_magic')
        options = {}
        options['magfile'] = os.path.join(dir_path, 'generic_magic_example.txt')
        options['meas_file'] = os.path.join(dir_path, 'generic_magic_example.magic')
        program_ran, error_message = convert.generic(**options)
        self.assertFalse(program_ran)
        no_exp_error = "Must provide experiment. Please provide experiment type of: Demag, PI, ATRM n (n of positions), CR (see help for format), NLT"
        self.assertEqual(no_exp_error, error_message)

    def test_generic_magic_success(self):
        dir_path = os.path.join('data_files', 'convert_2_magic',
                        'generic_magic')
        options = {}
        options['magfile'] = os.path.join(dir_path, 'generic_magic_example.txt')
        options['meas_file'] = os.path.join(dir_path, 'generic_magic_example.magic')
        options['experiment'] = 'Demag'
        program_ran, outfile_name = convert.generic(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(outfile_name), os.path.realpath(options['meas_file']))


class TestHujiMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        filelist = ['Massada_AF_HUJI_new_format.magic']
        directory = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'huji_magic')
        pmag.remove_files(filelist, directory)
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt',
                    'Massada_AF_HUJI_new_format.magic']
        pmag.remove_files(filelist, WD)
        os.chdir(WD)

    def test_with_bad_file(self):
        program_ran, error_msg = convert.huji()
        self.assertFalse(program_ran)
        self.assertEqual(error_msg, "mag_file field is a required option")
        program_ran, error_msg = convert.huji("fake")
        self.assertFalse(program_ran)
        self.assertEqual(error_msg, "bad mag file name")

    def test_huji_magic_success(self):
        dir_path = os.path.join('data_files', 'convert_2_magic',
                                'huji_magic')
        full_file = os.path.join(dir_path, "Massada_AF_HUJI_new_format.txt")
        options = {}
        options['input_dir_path'] = dir_path
        options['magfile'] = "Massada_AF_HUJI_new_format.txt"
        options['meas_file'] = "Massada_AF_HUJI_new_format.magic"
        options['codelist'] = 'AF'
        program_ran, outfile = convert.huji(**options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, options['meas_file'])

    def test_with_options(self):
        dir_path = os.path.join('data_files', 'convert_2_magic',
                                'huji_magic')
        options = {}
        options['dir_path'] = dir_path
        options['magfile'] = "Massada_AF_HUJI_new_format.txt"
        options['meas_file'] = "Massada_AF_HUJI_new_format.magic"
        options['codelist'] = "AF"
        options['location'] = "Massada"
        options['noave'] = True
        options['user'] = "me"
        options['labfield'] = 40
        options['phi'] = 0
        options['theta'] = 90
        program_ran, outfile = convert.huji(**options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, options['meas_file'])

    def test_with_no_exp_type(self):
        dir_path = os.path.join('data_files', 'convert_2_magic', 'huji_magic')
        mag_file = "Massada_AF_HUJI_new_format.txt"
        res, error = convert.huji(mag_file, dir_path)
        self.assertFalse(res)
        self.assertEqual(error, "Must select experiment type (codelist/-LP, options are: [AF, T, ANI, TRM, CR])")


class TestHujiSampleMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        filelist = ['samples.txt', 'sites.txt']
        directory = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'huji_magic')
        pmag.remove_files(filelist, directory)
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt',
                    'Massada_AF_HUJI_new_format.magic']
        pmag.remove_files(filelist, WD)
        os.chdir(WD)

    def test_success(self):
        res, outfile = convert.huji_sample("magdelkrum_datafile.txt",
                            dir_path=os.path.join(WD, 'data_files', 'convert_2_magic', 'huji_magic'))
        self.assertTrue(res)
        self.assertEqual(outfile, os.path.join(WD, 'data_files', 'convert_2_magic', 'huji_magic', 'samples.txt'))


class TestIodpSrmMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

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
        dir_path = os.path.join(WD, 'data_files', 'convert_2_magic', 'iodp_srm_magic')
        pmag.remove_files(filelist, dir_path)
        dir_path = WD
        pmag.remove_files(filelist, dir_path)
        os.chdir(WD)

    def test_iodp_with_no_files(self):
        program_ran, error_message = convert.iodp_srm()
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'No .csv files were found')

    #@unittest.skip("iodp_srm_magic is missing an example datafile")
    def test_iodp_with_files(self):
        options = {}
        dir_path = os.path.join(WD, 'data_files', 'convert_2_magic',
                                'iodp_srm_magic')
        options['dir_path'] = dir_path
        files = os.listdir(dir_path)
        files = ['IODP_Janus_312_U1256.csv', 'SRM_318_U1359_B_A.csv' ] # this one takes way too long: IODP_LIMS_SRMsection_344_1414A.csv
        info = []
        for f in files:
            if f.endswith('csv') and 'summary' not in f and 'discrete' not in f and 'sample' not in f:
                options['csv_file'] = f
                program_ran, outfile = convert.iodp_srm(**options)
                meas_df = cb.MagicDataFrame(pmag.resolve_file_name(outfile, dir_path))
                self.assertTrue(len(meas_df.df) > 0)

    #@unittest.skip("iodp_srm_magic is missing an example datafile")
    def test_iodp_with_one_file(self):
        options = {}
        #dir_path = os.path.join(WD, 'data_files', 'convert_2_magic',
        # 'iodp_srm_magic')
        dir_path = os.path.join(WD, 'data_files', 'UTESTA', 'SRM_data')
        options['dir_path'] = dir_path
        options['input_dir_path'] = dir_path
        options['csv_file'] = 'srmsection-XXX-UTEST-A.csv'
        program_ran, outfile = convert.iodp_srm(**options)
        self.assertEqual(program_ran, True)
        self.assertEqual(outfile, os.path.join('measurements.txt'))
        meas_df = cb.MagicDataFrame(os.path.join(dir_path, outfile))
        self.assertIn('sequence', meas_df.df.columns)


    def test_iodp_with_one_file_with_path(self):
        options = {}
        dir_path = os.path.join('data_files', 'UTESTA', 'SRM_data')
        #options['dir_path'] = dir_path
        options['dir_path'] = WD #dir_path
        options['input_dir_path'] = "fake/path"
        options['csv_file'] = os.path.join(dir_path, 'srmsection-XXX-UTEST-A.csv')
        program_ran, outfile = convert.iodp_srm(**options)
        self.assertEqual(program_ran, True)
        self.assertEqual(outfile, os.path.join('measurements.txt'))


class TestIodpDscrMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        filelist = ['measurements.txt', 'specimens.txt', 'samples.txt',
                    'sites.txt', 'locations.txt', 'custom_samples.txt']
        #directory = os.path.join(WD)
        pmag.remove_files(filelist, WD)
        pmag.remove_files(['custom_measurements.txt'], os.path.join(WD, 'data_files'))
        os.chdir(WD)

    def test_iodp_with_no_files(self):
        program_ran, error_message = convert.iodp_dscr()
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'No .csv files were found')

    #@unittest.skip("iodp_srm_magic is missing an example datafile")
    def test_iodp_with_one_file(self):
        options = {}
        #dir_path = os.path.join(WD, 'data_files', 'convert_2_magic',
        #'iodp_srm_magic')
        dir_path = os.path.join(WD, 'data_files', 'UTESTA', 'SRM_data')
        options['input_dir_path'] = dir_path
        options['csv_file'] = 'srmdiscrete-XXX-UTEST-A.csv'
        program_ran, outfile = convert.iodp_dscr(**options)
        self.assertEqual(program_ran, True)
        self.assertEqual(outfile, 'measurements.txt')

    def test_iodp_with_path(self):
        options = {}
        #dir_path = os.path.join(WD, 'data_files', 'convert_2_magic',
        #'iodp_srm_magic')
        dir_path = os.path.join(WD, 'data_files', 'UTESTA', 'SRM_data')
        #options['input_dir_path'] = dir_path
        options['csv_file'] = os.path.join('data_files', 'UTESTA', 'SRM_data', 'srmdiscrete-XXX-UTEST-A.csv')
        options['meas_file'] = os.path.join(WD, 'data_files', 'custom_measurements.txt')
        options['samp_file'] = 'custom_samples.txt'
        program_ran, outfile = convert.iodp_dscr(**options)
        self.assertEqual(program_ran, True)
        self.assertEqual(outfile, os.path.join(WD, 'data_files', 'custom_measurements.txt'))
        meas_df = cb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)


class TestIodpJr6Magic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        files = ['test.magic', 'other_er_samples.txt',
                 'custom_locations.txt', 'samples.txt', 'sites.txt',
                 'locations.txt', 'measurements.txt', 'specimens.txt']
        pmag.remove_files(files, WD)
        # then, make sure that hidden_er_samples.txt has been successfully renamed to er_samples.txt
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'iodp_jr6_magic')
        hidden_sampfile = os.path.join(input_dir, 'hidden_er_samples.txt')
        sampfile = os.path.join(input_dir, 'er_samples.txt')
        if os.path.exists(hidden_sampfile):
            os.rename(hidden_sampfile, sampfile)
        pmag.remove_files(['custom_specimens.txt'], 'data_files')
        os.chdir(WD)

    def test_iodp_jr6_with_no_files(self):
        with self.assertRaises(TypeError):
            convert.iodp_jr6()

    def test_iodp_jr6_with_invalid_mag_file(self):
        options = {'mag_file': 'fake'}
        program_ran, error_message = convert.iodp_jr6(**options)
        expected_msg = 'The input file you provided: {} does not exist.\nMake sure you have specified the correct filename AND correct input directory name.'.format(os.path.realpath(os.path.join('.', 'fake')))
        self.assertFalse(program_ran)
        self.assertEqual(error_message, expected_msg)


    #@unittest.skipIf('win32' in sys.platform or 'win62' in sys.platform, "Requires up to date version of pandas")
    def test_iodp_jr6_with_magfile(self):
        options = {}
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'iodp_jr6_magic')
        options['input_dir_path'] = input_dir
        mag_file = 'test.jr6'
        options['mag_file'] = 'test.jr6'
        meas_file = 'test.magic'
        options['meas_file'] = meas_file
        program_ran, outfile = convert.iodp_jr6(**options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, meas_file)
        meas_df = cb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)


    def test_iodp_jr6_with_path(self):
        options = {}
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'iodp_jr6_magic')
        #options['input_dir_path'] = input_dir
        mag_file = os.path.join('data_files', 'convert_2_magic', 'iodp_jr6_magic', 'test.jr6')
        options['mag_file'] = mag_file #'test.jr6'
        options['spec_file'] = os.path.join('data_files', 'custom_specimens.txt')
        options['loc_file'] = 'custom_locations.txt'
        meas_file = 'test.magic'
        options['meas_file'] = meas_file
        program_ran, outfile = convert.iodp_jr6(**options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, meas_file)
        for fname in [options['loc_file'], options['spec_file']]:
            self.assertTrue(os.path.isfile(fname))


    #@unittest.skipIf('win32' in sys.platform or 'win62' in sys.platform, "Requires up to date version of pandas")
    def test_iodp_jr6_with_options(self):
        options = {}
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'iodp_jr6_magic')
        options['input_dir_path'] = input_dir
        mag_file = 'test.jr6'
        options['mag_file'] = 'test.jr6'
        meas_file = 'test.magic'
        options['meas_file'] = meas_file
        options['noave'] = 1
        options['lat'] = 3
        options['lon'] = 5
        options['volume'] = 3
        program_ran, outfile = convert.iodp_jr6(**options)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, meas_file)


class TestIodpSamplesMagic(unittest.TestCase):

    def setUp(self):
        self.input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                      'iodp_srm_magic')

    def tearDown(self):
        os.chdir(WD)
        filelist = ['er_samples.txt']
        pmag.remove_files(filelist, WD)

    def test_with_wrong_format(self):
        infile = os.path.join(self.input_dir, 'GCR_U1359_B_coresummary.csv')
        program_ran, error_message = convert.iodp_samples(infile)
        self.assertFalse(program_ran)
        expected_error = 'Could not extract the necessary data from your input file.\nPlease make sure you are providing a correctly formated IODP samples csv file.'
        self.assertEqual(error_message, expected_error)


    def test_with_right_format(self):
        reference_file = os.path.join(WD, 'testing', 'odp_magic',
                                      'odp_magic_er_samples.txt')
        infile = os.path.join(self.input_dir, 'samples_318_U1359_B.csv')
        program_ran, outfile = convert.iodp_samples(infile, data_model_num=2)
        self.assertTrue(program_ran)
        expected_file = os.path.join('.', 'er_samples.txt')
        self.assertEqual(outfile, expected_file)
        self.assertTrue(os.path.isfile(outfile))


    def test_content_with_right_format(self):
        reference_file = os.path.join(WD, 'data_files', 'testing',
                                      'odp_magic', 'odp_magic_er_samples.txt')
        infile = os.path.join(self.input_dir, 'samples_318_U1359_B.csv')
        program_ran, outfile = convert.iodp_samples(infile, data_model_num=2)
        with open(reference_file) as ref_file:
            ref_lines = ref_file.readlines()
        with open(outfile) as out_file:
            out_lines = out_file.readlines()
        self.assertTrue(program_ran)
        self.assertEqual(ref_lines, out_lines)

    def test_with_data_model3(self):
        infile = os.path.join(self.input_dir, 'samples_318_U1359_B.csv')
        program_ran, outfile = convert.iodp_samples(infile, data_model_num=3)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath('samples.txt'), os.path.realpath(outfile))


class TestJr6TxtMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        files = ['test.magic', 'other_er_samples.txt',
                 'custom_locations.txt', 'samples.txt', 'sites.txt',
                 'measurements.txt', 'locations.txt', 'specimens.txt']
        pmag.remove_files(files, WD)

    def test_success(self):
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'jr6_magic')
        output = convert.jr6_txt(**{'mag_file': 'AP12.txt', 'input_dir_path': input_dir})
        self.assertTrue(output[0])
        self.assertEqual(output[1], 'measurements.txt')

    def test_with_options(self):
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'jr6_magic')
        options = {'mag_file': 'AP12.txt', 'input_dir_path': input_dir}
        options['meas_file'] = "test.magic"
        options['lat'] = 1
        options['lon'] = 2
        options['noave'] = True
        output = convert.jr6_txt(**options)
        self.assertTrue(output[0])
        self.assertEqual(output[1], 'test.magic')
        site_df = cb.MagicDataFrame(os.path.join(WD, 'sites.txt'))
        self.assertEqual(1, site_df.df.lat.values[0])


class TestJr6Jr6Magic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        files = ['test.magic', 'other_er_samples.txt',
                 'custom_locations.txt', 'samples.txt', 'sites.txt',
                 'measurements.txt', 'locations.txt', 'specimens.txt']
        pmag.remove_files(files, WD)

    def test_success(self):
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'jr6_magic')
        output = convert.jr6_jr6(**{'mag_file': 'AF.jr6', 'input_dir_path': input_dir})
        self.assertTrue(output[0])
        self.assertEqual(os.path.realpath(output[1]), os.path.realpath('measurements.txt'))

    def test_with_options(self):
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'jr6_magic')
        options = {'mag_file': 'SML07.JR6', 'input_dir_path': input_dir}
        options['meas_file'] = "test.magic"
        options['lat'] = 1
        options['lon'] = 2
        options['noave'] = True
        output = convert.jr6_jr6(**options)
        self.assertTrue(output[0])
        self.assertEqual(os.path.realpath(output[1]), os.path.realpath('test.magic'))
        site_df = cb.MagicDataFrame(os.path.join(WD, 'sites.txt'))
        self.assertEqual(1, site_df.df.lat.values[0])


class TestKly4sMagic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        filelist= ['magic_measurements.txt', 'my_magic_measurements.txt', 'er_specimens.txt', 'er_samples.txt', 'er_sites.txt', 'rmag_anisotropy.txt', 'my_rmag_anisotropy.txt']
        pmag.remove_files(filelist, WD)
        os.chdir(WD)

    def test_kly4s_without_infile(self):
        with self.assertRaises(TypeError):
            convert.kly4s()

    def test_kly4s_with_invalid_infile(self):
        program_ran, error_message = convert.kly4s('hello.txt')
        expected_file = os.path.join('.', 'hello.txt')
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'Error opening file: {}'.format(expected_file))

    def test_kly4s_with_valid_infile(self):
        in_dir = os.path.join(WD, 'data_files', 'convert_2_magic', 'kly4s_magic')
        program_ran, outfile = convert.kly4s('KLY4S_magic_example.dat', dir_path=WD,
                                                 input_dir_path=in_dir, data_model_num=2)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(WD, 'magic_measurements.txt'))

    def test_kly4s_fail_option4(self):
        in_dir = os.path.join(WD, 'data_files', 'convert_2_magic', 'kly4s_magic')
        program_ran, error_message = convert.kly4s('KLY4S_magic_example.dat', samp_con="4",
                                                   dir_path=WD, input_dir_path=in_dir,
                                                   data_model_num=2)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "option [4] must be in form 4-Z where Z is an integer")

    def test_kly4s_succeed_option4(self):
        in_dir = os.path.join(WD, 'data_files', 'convert_2_magic', 'kly4s_magic')
        program_ran, outfile = convert.kly4s('KLY4S_magic_example.dat', samp_con="4-2",
                                             dir_path=WD, input_dir_path=in_dir,
                                                 data_model_num=2)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(WD, 'magic_measurements.txt'))
        self.assertTrue(os.path.isfile(os.path.join(WD, 'magic_measurements.txt')))

    def test_kly4s_with_options(self):
        in_dir = os.path.join(WD, 'data_files', 'convert_2_magic', 'kly4s_magic')
        program_ran, outfile = convert.kly4s('KLY4S_magic_example.dat', specnum=1,
                                             locname="location", inst="instrument",
                                             samp_con=3, or_con=2,
                                             measfile='my_magic_measurements.txt',
                                             aniso_outfile="my_rmag_anisotropy.txt",
                                             dir_path=WD, input_dir_path=in_dir,
                                             data_model_num=2)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(WD, 'my_magic_measurements.txt'))
        self.assertTrue(os.path.isfile(os.path.join(WD, 'my_rmag_anisotropy.txt')))


    def test_kly4s_with_valid_infile_data_model3(self):
        in_dir = os.path.join(WD, 'data_files', 'convert_2_magic', 'kly4s_magic')
        program_ran, outfile = convert.kly4s('KLY4S_magic_example.dat', dir_path=WD,
                                             input_dir_path=in_dir, data_model_num=3)

        con = cb.Contribution(WD)
        self.assertEqual(['measurements', 'samples', 'sites', 'specimens'], sorted(con.tables))


class TestK15Magic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt',
                    'er_specimens.txt', 'er_samples.txt', 'my_er_samples.txt',
                    'er_sites.txt', 'rmag_anisotropy.txt',
                    'my_rmag_anisotropy.txt', 'rmag_results.txt',
                    'my_rmag_results.txt']
        pmag.remove_files(filelist, WD)
        os.chdir(WD)


    def test_k15_with_files(self):
        input_dir = os.path.join(WD, 'data_files',
                                 'convert_2_magic', 'k15_magic')
        program_ran, outfile  = convert.k15('k15_example.dat',
                                                input_dir_path=input_dir,
                                                data_model_num=2)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.realpath('magic_measurements.txt'))

    def test_k15_fail_option4(self):
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'k15_magic')
        program_ran, error_message = convert.k15('k15_example.dat',
                                                     sample_naming_con="4",
                                                     input_dir_path=input_dir,
                                                     data_model_num=2)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "option [4] must be in form 4-Z where Z is an integer")

    def test_k15_succeed_option4(self):
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic', 'k15_magic')
        program_ran, outfile = convert.k15('k15_example.dat', sample_naming_con="4-2",
                                               input_dir_path=input_dir,
                                               data_model_num=2)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.realpath("magic_measurements.txt"))

    def test_k15_with_options(self):
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'k15_magic')
        program_ran, outfile = convert.k15('k15_example.dat', specnum=2,
                                               sample_naming_con="3",
                                               location="Here",
                                               meas_file="my_magic_measurements.txt",
                                               samp_file="my_er_samples.txt",
                                               aniso_outfile="my_rmag_anisotropy.txt",
                                               result_file="my_rmag_results.txt",
                                               input_dir_path=input_dir,
                                                   data_model_num=2)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.realpath("my_magic_measurements.txt"))

    def test_data_model3(self):
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'k15_magic')
        program_ran, outfile = convert.k15('k15_example.dat', specnum=2,
                                               input_dir_path=input_dir)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath('./measurements.txt'), os.path.realpath(outfile))


class TestLdeoMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)
        self.input_dir = os.path.join(WD, 'data_files',
                                      'convert_2_magic', 'ldeo_magic')

    def tearDown(self):
        #filelist = ['measurements.txt', 'specimens.txt',
        #            'samples.txt', 'sites.txt']
        #pmag.remove_files(filelist, self.input_dir)
        filelist = ['specimens.txt', 'samples.txt', 'sites.txt',
                    'locations.txt', 'custom_specimens.txt', 'measurements.txt',
                    'custom_measurements.txt']
        pmag.remove_files(filelist, WD)
        #pmag.remove_files(filelist, os.path.join(WD, 'data_files'))
        os.chdir(WD)

    def test_ldeo_with_no_files(self):
        with self.assertRaises(TypeError):
            convert.ldeo()

    def test_ldeo_success(self):
        options = {'input_dir_path': self.input_dir, 'magfile': 'ldeo_magic_example.dat'}
        program_ran, outfile = convert.ldeo(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(outfile), os.path.join(WD, 'measurements.txt'))
        meas_df = cb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)

    def test_ldeo_options(self):
        options = {'input_dir_path': self.input_dir, 'magfile': 'ldeo_magic_example.dat'}
        options['noave'] = 1
        options['specnum'] = 2
        options['samp_con'] = 2
        options['meas_file'] = "custom_measurements.txt"
        options['location'] = "new place"
        options['labfield'], options['phi'], options['theta'] = 40, 0, 90
        program_ran, outfile = convert.ldeo(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(options['meas_file']), os.path.realpath(outfile))


class TestLivdbMagic(unittest.TestCase):
    def setUp(self):
        os.chdir(WD)
        self.input_dir = os.path.join(WD, 'data_files',
                                      'convert_2_magic', 'livdb_magic')

    def tearDown(self):
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt']
        pmag.remove_files(filelist, WD)
        #filelist = ['specimens.txt', 'samples.txt', 'sites.txt',
        #            'locations.txt', 'custom_specimens.txt', 'measurements.txt']
        #pmag.remove_files(filelist, '.')
        #pmag.remove_files(filelist, os.path.join(WD, 'data_files'))
        os.chdir(WD)


    def test_livdb_success(self):
        res, meas_file = convert.livdb(os.path.join(self.input_dir, "TH_IZZI+"))
        self.assertTrue(res)
        self.assertEqual(meas_file, os.path.realpath("measurements.txt"))

    def test_livdb_all_experiment_types(self):
        for folder in ["TH_IZZI+", "MW_C+", "MW_IZZI+andC++", "MW_OT+", "MW_P"]:
            res, meas_file = convert.livdb(os.path.join(self.input_dir, folder))
            self.assertTrue(res)
            self.assertEqual(meas_file, os.path.realpath("measurements.txt"))

    def test_with_options(self):
        # naming con 1
        res, meas_file = convert.livdb(os.path.join(self.input_dir, "TH_IZZI+"),
                                       location_name="place", samp_name_con=1, meas_out="custom.txt")
        self.assertTrue(res)
        self.assertEqual(meas_file, os.path.realpath("custom.txt"))
        df = cb.MagicDataFrame(os.path.join(WD, "specimens.txt"))
        self.assertEqual("ATPIPV04-1A", df.df.loc["ATPIPV04-1A"]['sample'])
        # naming con 2 without chars
        res, meas_file = convert.livdb(os.path.join(self.input_dir, "TH_IZZI+"),
                                       location_name="place", samp_name_con=2, site_name_con=2,
                                       meas_out="custom.txt")
        self.assertTrue(res)
        self.assertEqual(meas_file, os.path.realpath("custom.txt"))
        df = cb.MagicDataFrame(os.path.join(WD, "specimens.txt"))
        self.assertEqual("ATPIPV04-1A", df.df.loc['ATPIPV04-1A']['sample'])
        df = cb.MagicDataFrame(os.path.join(WD, "samples.txt"))
        self.assertEqual("ATPIPV04-1A", df.df.loc['ATPIPV04-1A']['site'])


    def test_naming_con_2(self):
        res, meas_file = convert.livdb(os.path.join(self.input_dir, "TH_IZZI+"),
                                       location_name="place", samp_name_con=2, samp_num_chars=1,
                                       meas_out="custom.txt")
        self.assertTrue(res)
        self.assertEqual(meas_file, os.path.realpath("custom.txt"))
        df = cb.MagicDataFrame(os.path.join(WD, "specimens.txt"))
        self.assertEqual("ATPIPV04-1", df.df.loc["ATPIPV04-1A"]['sample'])

    def test_naming_con_3(self):
        res, meas_file = convert.livdb(os.path.join(self.input_dir, "TH_IZZI+"),
                                       location_name="place", samp_name_con=3, samp_num_chars="-",
                                       meas_out="custom.txt")
        self.assertTrue(res)
        self.assertEqual(meas_file, os.path.realpath("custom.txt"))
        df = cb.MagicDataFrame(os.path.join(WD, "specimens.txt"))
        self.assertEqual(df.df.loc['ATPIPV04-1A']['sample'], 'ATPIPV04')
        df = cb.MagicDataFrame(os.path.join(WD, "samples.txt"))
        self.assertEqual(df.df.loc['ATPIPV04']['site'], "ATPIPV04")



class TestMstMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)
        self.input_dir = os.path.join(WD, 'data_files',
                                      'convert_2_magic', 'mst_magic')

    def tearDown(self):
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt', 'custom.out']
        pmag.remove_files(filelist, WD)
        #filelist = ['specimens.txt', 'samples.txt', 'sites.txt',
        #            'locations.txt', 'custom_specimens.txt', 'measurements.txt']
        pmag.remove_files(filelist, '.')
        pmag.remove_files(filelist, os.path.join(WD, 'data_files'))
        os.chdir(WD)

    def test_mst_with_no_files(self):
        with self.assertRaises(TypeError):
            convert.mst()

    def test_mst_success(self):
        options = {'input_dir_path': self.input_dir, 'infile': 'curie_example.dat'}
        options['spec_name'] = 'abcde'
        options['location'] = 'place'
        program_ran, outfile = convert.mst(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(outfile), os.path.join(WD, 'measurements.txt'))
        meas_df = cb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)
        self.assertEqual(meas_df.df.location.values[0], 'place')
        con = cb.Contribution(WD)
        for table in ['measurements', 'specimens', 'samples', 'sites', 'locations']:
            self.assertIn(table, con.tables)

    def test_mst_synthetic(self):
        options = {'input_dir_path': self.input_dir, 'infile': 'curie_example.dat'}
        options['spec_name'] = 'abcde'
        options['syn'] = True
        program_ran, outfile = convert.mst(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(outfile), os.path.join(WD, 'measurements.txt'))


class TestMiniMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)
        self.input_dir = os.path.join(WD, 'data_files',
                              'convert_2_magic', 'mini_magic')

    def tearDown(self):
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt', 'custom.out']
        pmag.remove_files(filelist, WD)

    def test_bad_file(self):
        program_ran, error = convert.mini('fake_file')
        self.assertFalse(program_ran)
        self.assertEqual(error, "bad mag file name")

    def test_success(self):
        magfile = os.path.join(self.input_dir, "Peru_rev1.txt")
        program_ran, outfile = convert.mini(magfile)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, "measurements.txt")


    def test_options(self):
        magfile = os.path.join(self.input_dir, "Peru_rev1.txt")
        program_ran, outfile = convert.mini(magfile, meas_file="custom.out",
                                            user="me", noave=1, volume=15,
                                            methcode="LP:FAKE")
        self.assertTrue(program_ran)
        self.assertEqual(outfile, "custom.out")

    def test_dm_2(self):
        magfile = os.path.join(self.input_dir, "Peru_rev1.txt")
        program_ran, outfile = convert.mini(magfile, meas_file="custom.out",
                                            user="me", noave=1, volume=15,
                                            methcode="LP:FAKE", data_model_num=2)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, "custom.out")


class TestPmdMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)
        self.input_dir = os.path.join(WD, 'data_files',
                                      'convert_2_magic', 'pmd_magic', 'PMD', )

    def tearDown(self):
        filelist = ['specimens.txt', 'samples.txt', 'sites.txt',
                    'locations.txt', 'custom_specimens.txt', 'measurements.txt',
                    'custom_meas.txt']
        pmag.remove_files(filelist, WD)
        pmag.remove_files(filelist, ".")
        os.chdir(WD)

    def test_pmd_with_no_files(self):
        with self.assertRaises(TypeError):
            convert.pmd()

    def test_pmd_success(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': 'ss0207a.pmd'}
        program_ran, outfile = convert.pmd(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(outfile), os.path.join(WD, 'measurements.txt'))
        meas_df = cb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)


    def test_pmd_options(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': 'ss0207a.pmd'}
        options['lat'], options['lon'] = 5, 10
        options['specnum'] = 2
        options['location'] = 'place'
        options['meas_file'] = 'custom_meas.txt'
        program_ran, outfile = convert.pmd(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(outfile), os.path.join(WD, 'custom_meas.txt'))
        loc_df = cb.MagicDataFrame(os.path.join(WD, 'locations.txt'))
        self.assertEqual(loc_df.df.index.values[0], 'place')


class TestSioMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        filelist = ['sio_af_example.magic']
        directory = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'sio_magic')
        pmag.remove_files(filelist, directory)
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt']
        pmag.remove_files(filelist, WD)
        os.chdir(WD)

    def test_sio_magic_no_files(self):
        with self.assertRaises(TypeError):
            convert.sio()

    def test_sio_magic_success(self):
        options = {}
        dir_path = os.path.join('data_files', 'convert_2_magic',
                                'sio_magic')
        options['mag_file'] = os.path.join(dir_path, 'sio_af_example.dat')
        options['meas_file'] = os.path.join(dir_path, 'sio_af_example.magic')
        program_ran, file_name = convert.sio(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(file_name),
                         os.path.realpath(options['meas_file']))
        meas_df = cb.MagicDataFrame(os.path.realpath(options['meas_file']))
        self.assertIn('sequence', meas_df.df.columns)
        self.assertEqual(0, meas_df.df.iloc[0]['sequence'])

    def test_sio_magic_success_with_wd(self):
        options = {}
        dir_path = os.path.join('data_files', 'convert_2_magic',
                                'sio_magic')
        options['mag_file'] = os.path.join('sio_af_example.dat')
        options['meas_file'] = os.path.join('sio_af_example.magic')
        options['dir_path'] = dir_path
        program_ran, file_name = convert.sio(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(file_name),
                         os.path.realpath(os.path.join(dir_path, options['meas_file'])))



    def test_sio_magic_fail_option4(self):
        options = {}
        options['mag_file'] = os.path.join(WD, 'data_files',
                                           'convert_2_magic', 'sio_magic',
                                           'sio_af_example.dat')
        meas_file = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'sio_magic', 'sio_af_example.magic')
        options['meas_file'] = meas_file
        options['samp_con'] = '4'
        program_ran, error_message = convert.sio(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "naming convention option [4] must be in form 4-Z where Z is an integer")

    def test_sio_magic_succeed_option4(self):
        options = {}
        options['mag_file'] = os.path.join(WD, 'data_files',
                                           'convert_2_magic', 'sio_magic',
                                           'sio_af_example.dat')
        meas_file = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'sio_magic', 'sio_af_example.magic')
        options['meas_file'] = meas_file
        options['samp_con'] = '4-2'
        program_ran, file_name = convert.sio(**options)
        self.assertTrue(program_ran)
        self.assertEqual(file_name, meas_file)


    def test_sio_magic_fail_with_coil(self):
        options = {}
        options['mag_file'] = os.path.join(WD, 'data_files',
                                           'convert_2_magic', 'sio_magic',
                                           'sio_af_example.dat')
        meas_file = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'sio_magic', 'sio_af_example.magic')
        options['meas_file'] = meas_file
        options['coil'] = 4
        program_ran, error_message = convert.sio(**options)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, '4 is not a valid coil specification')

    def test_sio_magic_succeed_with_coil(self):
        options = {}
        options['mag_file'] = os.path.join(WD, 'data_files',
                                           'convert_2_magic', 'sio_magic',
                                           'sio_af_example.dat')
        meas_file = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'sio_magic', 'sio_af_example.magic')
        options['meas_file'] = meas_file
        options['coil'] = '1'
        program_ran, file_name = convert.sio(**options)
        self.assertTrue(program_ran)
        self.assertEqual(file_name, meas_file)


class TestSMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)
        self.input_dir = os.path.join(WD, 'data_files', 'convert_2_magic', 's_magic')

    def tearDown(self):
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt', 'custom.out']
        pmag.remove_files(filelist, WD)
        pmag.remove_files(filelist, self.input_dir)

    def test_with_invalid_file(self):
        res, error_msg = convert.s_magic('fake.txt')
        self.assertFalse(res)
        expected_file = os.path.join(WD, "fake.txt")
        self.assertEqual(error_msg, "No such file: {}".format(expected_file))

    def test_success(self):
        res, outfile = convert.s_magic("s_magic_example.dat", dir_path=self.input_dir)
        self.assertTrue(res)
        self.assertEqual(outfile, os.path.join(self.input_dir, "specimens.txt"))

    def test_with_options(self):

        res, outfile = convert.s_magic("s_magic_example.dat", dir_path=self.input_dir,
                                       specnum=1, location="place", spec="abcd-efg",
                                       user="me", samp_con=2)
        self.assertTrue(res)
        self.assertEqual(outfile, os.path.join(self.input_dir, "specimens.txt"))
        self.assertTrue(os.path.exists(os.path.join(self.input_dir, "sites.txt")))
        con = cb.Contribution(self.input_dir)
        self.assertIn('sites', con.tables)
        self.assertEqual('place', con.tables['sites'].df.loc[:, 'location'].values[0])


class TestSufarAscMagic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt',
                    'er_specimens.txt', 'er_samples.txt', 'my_er_samples.txt',
                    'er_sites.txt', 'rmag_anisotropy.txt', 'my_rmag_anisotropy.txt',
                    'rmag_results.txt', 'my_rmag_results.txt', 'measurements.txt',
                    'specimens.txt', 'samples.txt', 'sites.txt', 'locations.txt']
        pmag.remove_files(filelist, WD)
        os.chdir(WD)


    def test_sufar4_with_no_files(self):
        with self.assertRaises(TypeError):
            convert.sufar4()

    def test_sufar4_with_invalid_file(self):
        input_dir = os.path.join(WD, 'data_files',
                                 'convert_2_magic', 'sufar_asc_magic')
        infile = 'fake_sufar4-asc_magic_example.txt'
        program_ran, error_message = convert.sufar4(infile,
                                                    input_dir_path=input_dir,
                                                    data_model_num=2)
        self.assertFalse(program_ran)
        self.assertEqual(error_message,
                         'Error opening file: {}'.format(os.path.join(input_dir,
                                                                      infile)))


    def test_sufar4_with_infile(self):
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'sufar_asc_magic')
        infile = 'sufar4-asc_magic_example.txt'
        program_ran, outfile = convert.sufar4(infile,
                                              input_dir_path=input_dir,
                                              data_model_num=2)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join('.', 'magic_measurements.txt'))
        with open(outfile, 'r') as ofile:
            lines = ofile.readlines()
            self.assertEqual(292, len(lines))


    def test_sufar4_succeed_data_model3(self):
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'sufar_asc_magic')
        infile = 'sufar4-asc_magic_example.txt'
        program_ran, outfile = convert.sufar4(infile,
                                              input_dir_path=input_dir)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join('.', 'measurements.txt'))
        with open(outfile, 'r') as ofile:
            lines = ofile.readlines()
            self.assertEqual(292, len(lines))
            self.assertEqual('measurements', lines[0].split('\t')[1].strip())
        con = cb.Contribution(WD)
        self.assertEqual(sorted(con.tables),
                         sorted(['measurements', 'specimens',
                                 'samples', 'sites']))


    def test_sufar4_fail_option4(self):
        input_dir = os.path.join(WD, 'data_files',
                                 'convert_2_magic', 'sufar_asc_magic')
        infile = 'sufar4-asc_magic_example.txt'
        program_ran, error_message = convert.sufar4(infile,
                                                    input_dir_path=input_dir,
                                                    sample_naming_con='4',
                                                    data_model_num=2)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "option [4] must be in form 4-Z where Z is an integer")

    def test_sufar4_succeed_option4(self):
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic',
                                 'sufar_asc_magic')
        infile = 'sufar4-asc_magic_example.txt'
        ofile = 'my_magic_measurements.txt'
        program_ran, outfile = convert.sufar4(infile,
                                              meas_output=ofile,
                                              input_dir_path=input_dir,
                                              sample_naming_con='4-2',
                                              data_model_num=2)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join('.', ofile))

    def test_sufar4_with_options(self):
        input_dir = os.path.join(WD, 'data_files',
                                 'convert_2_magic', 'sufar_asc_magic')
        infile = 'sufar4-asc_magic_example.txt'
        program_ran, outfile = convert.sufar4(infile, meas_output='my_magic_measurements.txt',
                                              aniso_output="my_rmag_anisotropy.txt",
                                              specnum=2, locname="Here", instrument="INST",
                                              static_15_position_mode=True, input_dir_path=input_dir,
                                              sample_naming_con='5',
                                              data_model_num=2)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join('.', 'my_magic_measurements.txt'))


class TestTdtMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)
        self.input_dir = os.path.join(WD, 'data_files',
                                      'convert_2_magic', 'tdt_magic')

    def tearDown(self):
        filelist = ['measurements.txt', 'specimens.txt',
                    'samples.txt', 'sites.txt', 'locations.txt', 'custom.out']
        pmag.remove_files(filelist, WD)
        pmag.remove_files(filelist, '.')
        pmag.remove_files(filelist, os.path.join(WD, 'data_files'))
        os.chdir(WD)

    def test_success(self):
        res, outfile = convert.tdt(self.input_dir)
        self.assertTrue(res)
        self.assertEqual(outfile, os.path.join(self.input_dir, "measurements.txt"))

    def test_with_options(self):
        res, outfile = convert.tdt(self.input_dir, meas_file_name="custom.out", location="here",
                                   user="me", samp_name_con=2, samp_name_chars=1, site_name_con=2,
                                   site_name_chars=1, volume=15., lab_inc=-90)
        self.assertTrue(res)
        self.assertEqual(outfile, os.path.join(self.input_dir, "custom.out"))
        df = cb.MagicDataFrame(os.path.join(self.input_dir, "samples.txt"))
        self.assertEqual("MG", df.df["site"].values[0])
        self.assertEqual("MGH", df.df["sample"].values[0])


class TestUtrechtMagic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)
        self.input_dir = os.path.join(WD, 'data_files',
                                      'convert_2_magic', 'utrecht_magic')

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
        with self.assertRaises(TypeError):
            convert.utrecht()


    def test_utrecht_success(self):
        options = {'input_dir_path': self.input_dir, 'mag_file': 'Utrecht_Example.af'}
        program_ran, outfile = convert.utrecht(**options)
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(outfile), os.path.join(WD, 'measurements.txt'))
        meas_df = cb.MagicDataFrame(outfile)
        self.assertIn('sequence', meas_df.df.columns)
