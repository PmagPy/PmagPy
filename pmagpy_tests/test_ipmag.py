#!/usr/bin/env python

import unittest
import os
import sys
import matplotlib
import pkg_resources
import pmagpy.pmag as pmag
import pmagpy.ipmag as ipmag


#WD = os.getcwd()
WD = sys.prefix

class TestIGRF(unittest.TestCase):

    def setUp(self):
        pass

    def test_igrf_output(self):
        result = ipmag.igrf([1999.1, 30, 20, 50])
        reference = [1.20288657e+00, 2.82331112e+01, 3.9782338913649881e+04]
        for num, item in enumerate(result):
            self.assertAlmostEqual(item, reference[num])

class TestUploadMagic(unittest.TestCase):

    def setUp(self):
        self.dir_path = os.path.join(WD, 'pmagpy_data_files', 'testing')

    def test_empty_dir(self):
        directory = os.path.join(self.dir_path, 'empty_dir')
        outfile, error_message, errors = ipmag.upload_magic(dir_path=directory)
        self.assertFalse(errors)
        self.assertFalse(outfile)
        self.assertEqual(error_message, "no data found, upload file not created")

    def test_with_invalid_files(self):
        directory = os.path.join(self.dir_path, 'my_project_with_errors')
        outfile, error_message, errors = ipmag.upload_magic(dir_path=directory)
        self.assertTrue(errors)
        self.assertFalse(outfile)
        self.assertEqual(error_message, "file validation has failed.  You may run into problems if you try to upload this file.")
        directory = os.path.join(self.dir_path, 'my_project_with_errors')

        # delete any upload file that was partially created
        import re
        pattern = re.compile('\w*[.]\w*[.]\w*[20]\d{2}\w*.txt$')
        possible_files = os.listdir(directory)
        files = []
        for f in possible_files:
            if pattern.match(f):
                files.append(f)
        pmag.remove_files(files, directory)

    def test_with_valid_files(self):
        #print os.path.join(self.dir_path, 'my_project')
        outfile, error_message, errors = ipmag.upload_magic(dir_path=os.path.join(self.dir_path, 'my_project'))
        self.assertTrue(outfile)
        self.assertEqual(error_message, '')
        self.assertFalse(errors)
        assert os.path.isfile(outfile)
        directory = os.path.join(self.dir_path, 'my_project_with_errors')
        os.remove(os.path.join(directory, outfile))


class Test_iodp_samples_magic(unittest.TestCase):

    def setUp(self):
        self.input_dir = os.path.join(WD, 'pmagpy_data_files', 'Measurement_Import',
                                      'iodp_srm_magic')

    def tearDown(self):
        os.chdir(WD)
        filelist = ['er_samples.txt']
        pmag.remove_files(filelist, WD)

    def test_with_wrong_format(self):
        infile = os.path.join(self.input_dir, 'GCR_U1359_B_coresummary.csv')
        program_ran, error_message = ipmag.iodp_samples_magic(infile)
        self.assertFalse(program_ran)
        expected_error = 'Could not extract the necessary data from your input file.\nPlease make sure you are providing a correctly formated IODP samples csv file.'
        self.assertEqual(error_message, expected_error)


    def test_with_right_format(self):
        reference_file = os.path.join(WD, 'testing', 'odp_magic',
                                      'odp_magic_er_samples.txt')
        infile = os.path.join(self.input_dir, 'samples_318_U1359_B.csv')
        program_ran, outfile = ipmag.iodp_samples_magic(infile)
        self.assertTrue(program_ran)
        expected_file = os.path.join('.', 'er_samples.txt')
        self.assertEqual(outfile, expected_file)
        self.assertTrue(os.path.isfile(outfile))


    def test_content_with_right_format(self):
        reference_file = os.path.join(WD, 'pmagpy_data_files', 'testing',
                                      'odp_magic', 'odp_magic_er_samples.txt')
        infile = os.path.join(self.input_dir, 'samples_318_U1359_B.csv')
        program_ran, outfile = ipmag.iodp_samples_magic(infile)
        self.assertEqual(open(reference_file).readlines(), open(outfile).readlines())



class TestKly4s_magic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        filelist= ['magic_measurements.txt', 'my_magic_measurements.txt', 'er_specimens.txt', 'er_samples.txt', 'er_sites.txt', 'rmag_anisotropy.txt', 'my_rmag_anisotropy.txt']
        pmag.remove_files(filelist, WD)

    def test_kly4s_without_infile(self):
        with self.assertRaises(TypeError):
            ipmag.kly4s_magic()

    def test_kly4s_with_invalid_infile(self):
        program_ran, error_message = ipmag.kly4s_magic('hello.txt')
        expected_file = os.path.join('.', 'hello.txt')
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'Error opening file: {}'.format(expected_file))

    def test_kly4s_with_valid_infile(self):
        in_dir = os.path.join(WD, 'pmagpy_data_files', 'Measurement_Import', 'kly4s_magic')
        program_ran, outfile = ipmag.kly4s_magic('KLY4S_magic_example.dat', output_dir_path=WD, input_dir_path=in_dir)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(WD, 'magic_measurements.txt'))

    def test_kly4s_fail_option4(self):
        in_dir = os.path.join(WD, 'pmagpy_data_files', 'Measurement_Import', 'kly4s_magic')
        program_ran, error_message = ipmag.kly4s_magic('KLY4S_magic_example.dat', samp_con="4", output_dir_path=WD, input_dir_path=in_dir)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "option [4] must be in form 4-Z where Z is an integer")

    def test_kly4s_succeed_option4(self):
        in_dir = os.path.join(WD, 'pmagpy_data_files', 'Measurement_Import', 'kly4s_magic')
        program_ran, outfile = ipmag.kly4s_magic('KLY4S_magic_example.dat', samp_con="4-2", output_dir_path=WD, input_dir_path=in_dir)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(WD, 'magic_measurements.txt'))
        self.assertTrue(os.path.isfile(os.path.join(WD, 'magic_measurements.txt')))

    def test_kly4s_with_options(self):
        in_dir = os.path.join(WD, 'pmagpy_data_files', 'Measurement_Import', 'kly4s_magic')
        program_ran, outfile = ipmag.kly4s_magic('KLY4S_magic_example.dat', specnum=1, locname="location", inst="instrument", samp_con=3, or_con=2, measfile='my_magic_measurements.txt', aniso_outfile="my_rmag_anisotropy.txt", output_dir_path=WD, input_dir_path=in_dir)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(WD, 'my_magic_measurements.txt'))
        self.assertTrue(os.path.isfile(os.path.join(WD, 'my_rmag_anisotropy.txt')))


class TestK15_magic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt',
                    'er_specimens.txt', 'er_samples.txt', 'my_er_samples.txt',
                    'er_sites.txt', 'rmag_anisotropy.txt',
                    'my_rmag_anisotropy.txt', 'rmag_results.txt',
                    'my_rmag_results.txt']
        pmag.remove_files(filelist, WD)

    def test_k15_with_no_files(self):
        with self.assertRaises(TypeError):
            ipmag.kly4s_magic()

    def test_k15_with_files(self):
        input_dir = os.path.join(WD, 'pmagpy_data_files',
                                 'Measurement_Import', 'k15_magic')
        program_ran, outfile  = ipmag.k15_magic('k15_example.dat',
                                                input_dir_path=input_dir)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join('.', 'magic_measurements.txt'))

    def test_k15_fail_option4(self):
        input_dir = os.path.join(WD, 'pmagpy_data_files', 'Measurement_Import',
                                 'k15_magic')
        program_ran, error_message = ipmag.k15_magic('k15_example.dat',
                                                     sample_naming_con="4",
                                                     input_dir_path=input_dir)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "option [4] must be in form 4-Z where Z is an integer")

    def test_k15_succeed_option4(self):
        input_dir = os.path.join(WD, 'pmagpy_data_files', 'Measurement_Import', 'k15_magic')
        program_ran, outfile = ipmag.k15_magic('k15_example.dat', sample_naming_con="4-2", input_dir_path=input_dir)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(".", "magic_measurements.txt"))

    def test_k15_with_options(self):
        input_dir = os.path.join(WD, 'pmagpy_data_files', 'Measurement_Import',
                                 'k15_magic')
        program_ran, outfile = ipmag.k15_magic('k15_example.dat', specnum=2,
                                               sample_naming_con="3",
                                               er_location_name="Here",
                                               measfile="my_magic_measurements.txt",
                                               sampfile="my_er_samples.txt",
                                               aniso_outfile="my_rmag_anisotropy.txt",
                                               result_file="my_rmag_results.txt",
                                               input_dir_path=input_dir)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join(".", "my_magic_measurements.txt"))


class TestSUFAR_asc_magic(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt', 'er_specimens.txt', 'er_samples.txt', 'my_er_samples.txt', 'er_sites.txt', 'rmag_anisotropy.txt', 'my_rmag_anisotropy.txt', 'rmag_results.txt', 'my_rmag_results.txt']
        pmag.remove_files(filelist, WD)

    def test_SUFAR4_with_no_files(self):
        with self.assertRaises(TypeError):
            ipmag.SUFAR4_magic()

    def test_SUFAR4_with_invalid_file(self):
        input_dir = os.path.join(WD, 'pmagpy_data_files',
                                 'Measurement_Import', 'SUFAR_asc_magic')
        infile = 'fake_sufar4-asc_magic_example.txt'
        program_ran, error_message = ipmag.SUFAR4_magic(infile,
                                                        input_dir_path=input_dir)
        self.assertFalse(program_ran)
        self.assertEqual(error_message,
                         'Error opening file: {}'.format(os.path.join(input_dir,
                                                                      infile)))


    def test_SUFAR4_with_infile(self):
        input_dir = os.path.join(WD, 'pmagpy_data_files', 'Measurement_Import',
                                 'SUFAR_asc_magic')
        infile = 'sufar4-asc_magic_example.txt'
        program_ran, outfile = ipmag.SUFAR4_magic(infile,
                                                  input_dir_path=input_dir)
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join('.', 'magic_measurements.txt'))

    def test_SUFAR4_fail_option4(self):
        input_dir = os.path.join(WD, 'pmagpy_data_files',
                                 'Measurement_Import', 'SUFAR_asc_magic')
        infile = 'sufar4-asc_magic_example.txt'
        program_ran, error_message = ipmag.SUFAR4_magic(infile,
                                                        input_dir_path=input_dir,
                                                        sample_naming_con='4')
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "option [4] must be in form 4-Z where Z is an integer")

    def test_SUFAR4_succeed_option4(self):
        input_dir = os.path.join(WD, 'pmagpy_data_files', 'Measurement_Import',
                                 'SUFAR_asc_magic')
        print 'WD', WD
        print 'input_dir', input_dir
        infile = 'sufar4-asc_magic_example.txt'
        ofile = 'my_magic_measurements.txt'
        program_ran, outfile = ipmag.SUFAR4_magic(infile,
                                                  meas_output=ofile,
                                                  input_dir_path=input_dir,
                                                  sample_naming_con='4-2')
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join('.', ofile))

    def test_SUFAR4_with_options(self):
        input_dir = os.path.join(WD, 'pmagpy_data_files',
                                 'Measurement_Import', 'SUFAR_asc_magic')
        infile = 'sufar4-asc_magic_example.txt'
        program_ran, outfile = ipmag.SUFAR4_magic(infile, meas_output='my_magic_measurements.txt', aniso_output="my_rmag_anisotropy.txt", specnum=2, locname="Here", instrument="INST", static_15_position_mode=True, input_dir_path=input_dir, sample_naming_con='5')
        self.assertTrue(program_ran)
        self.assertEqual(outfile, os.path.join('.', 'my_magic_measurements.txt'))

class TestAgmMagic(unittest.TestCase):
    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt', 'er_specimens.txt', 'er_samples.txt', 'my_er_samples.txt', 'er_sites.txt', 'rmag_anisotropy.txt', 'my_rmag_anisotropy.txt', 'rmag_results.txt', 'my_rmag_results.txt', 'agm_magic_example.magic']
        pmag.remove_files(filelist, WD)

    def test_agm_with_no_files(self):
        with self.assertRaises(TypeError):
            ipmag.agm_magic()

    def test_agm_with_bad_file(self):
        program_ran, error_message = ipmag.agm_magic('bad_file.txt')
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'You must provide a valid agm file')

    def test_agm_success(self):
        input_dir = os.path.join(WD, 'pmagpy_data_files',
                                 'Measurement_Import', 'agm_magic')
        program_ran, filename = ipmag.agm_magic('agm_magic_example.agm',
                                                outfile='agm_magic_example.magic',
                                                input_dir_path=input_dir)
        self.assertTrue(program_ran)
        self.assertEqual(filename, os.path.join('.', 'agm_magic_example.magic'))


#@unittest.skipIf(sys.platform in ['darwin'], 'currently causing fatal errors on OSX')
class TestCoreDepthplot(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt', 'er_specimens.txt', 'er_samples.txt', 'my_er_samples.txt', 'er_sites.txt', 'rmag_anisotropy.txt', 'my_rmag_anisotropy.txt', 'rmag_results.txt', 'my_rmag_results.txt']
        pmag.remove_files(filelist, WD)

    def test_core_depthplot_with_no_files(self):
        program_ran, error_message = ipmag.core_depthplot()
        self.assertFalse(program_ran)
        self.assertEqual("You must provide either a magic_measurements file or a pmag_specimens file", error_message)

    def test_core_depthplot_bad_params(self):
        path = os.path.join(WD, 'pmagpy_data_files', 'core_depthplot')
        program_ran, error_message = ipmag.core_depthplot(input_dir_path=path)
        self.assertFalse(program_ran)
        self.assertEqual('No data found to plot\nTry again with different parameters', error_message)

    def test_core_depthplot_bad_method(self):
        path = os.path.join(WD, 'pmagpy_data_files', 'core_depthplot')
        program_ran, error_message = ipmag.core_depthplot(input_dir_path=path, step=5, meth='NA')
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'method: "{}" not supported'.format('NA'))


    def test_core_depthplot_success(self):
        path = os.path.join(WD, 'pmagpy_data_files', 'core_depthplot')
        program_ran, plot_name = ipmag.core_depthplot(input_dir_path=path, spc_file='pmag_specimens.txt', samp_file='er_samples.txt', meth='AF', step=15)
        #program_ran, plot_name = True, 'DSDP Site 522_m:_LT-AF-Z_core-depthplot.svg'
        self.assertTrue(program_ran)
        self.assertEqual(plot_name, 'DSDP Site 522_m:_LT-AF-Z_core-depthplot.svg')

    def test_core_depthplot_with_sum_file(self):
        path = os.path.join(WD, 'pmagpy_data_files', 'UTESTA', 'UTESTA_MagIC')
        sum_file = 'CoreSummary_XXX_UTESTA.csv'
        program_ran, plot_name = ipmag.core_depthplot(input_dir_path=path, spc_file='pmag_specimens.txt', samp_file='er_samples.txt', meth='AF', step=15, sum_file=sum_file)
        self.assertTrue(program_ran)
        outfile = 'UTESTA_m:_LT-AF-Z_core-depthplot.svg'
        self.assertEqual(plot_name, outfile)


    def test_core_depthplot_without_full_time_options(self):
        path = os.path.join(WD, 'pmagpy_data_files', 'core_depthplot')
        program_ran, error_message = ipmag.core_depthplot(input_dir_path=path, spc_file='pmag_specimens.txt', samp_file='er_samples.txt', meth='AF', step=15, fmt='png', pltInc=False, logit=True, pltTime=True)#, timescale='gts12', amin=0, amax=3) # pltDec = False causes failure with these data
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "To plot time, you must provide amin, amax, and timescale")

    def test_core_depthplot_success_with_options(self):
        path = os.path.join(WD, 'pmagpy_data_files', 'core_depthplot')
        program_ran, plot_name = ipmag.core_depthplot(input_dir_path=path, spc_file='pmag_specimens.txt', samp_file='er_samples.txt', meth='AF', step=15, fmt='png', pltInc=False, logit=True, pltTime=True, timescale='gts12', amin=0, amax=3) # pltDec = False causes failure with these data
        self.assertTrue(program_ran)
        self.assertEqual(plot_name, 'DSDP Site 522_m:_LT-AF-Z_core-depthplot.png')

    def test_core_depthplot_success_with_other_options(self):
        path = os.path.join(WD, 'pmagpy_data_files', 'core_depthplot')
        program_ran, plot_name = ipmag.core_depthplot(input_dir_path=path, spc_file='pmag_specimens.txt', age_file='er_ages.txt', meth='AF', step=15, fmt='png', pltInc=False, logit=True, pltTime=True, timescale='gts12', amin=0, amax=3) # pltDec = False causes failure with these data
        self.assertTrue(program_ran)
        self.assertEqual(plot_name, 'DSDP Site 522_m:_LT-AF-Z_core-depthplot.png')

#@unittest.skipIf(sys.platform in ['darwin'], 'currently causing fatal errors on OSX')
class TestAnisoDepthplot(unittest.TestCase):

    def setUp(self):
        os.chdir(WD)
        self.aniso_WD = os.path.join(WD, 'pmagpy_data_files', 'ani_depthplot')

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt', 'er_specimens.txt', 'er_samples.txt', 'my_er_samples.txt', 'er_sites.txt', 'rmag_anisotropy.txt', 'my_rmag_anisotropy.txt', 'rmag_results.txt', 'my_rmag_results.txt', 'my_samples.txt']
        pmag.remove_files(filelist, WD)

    def test_aniso_depthplot_with_no_files(self):
        program_ran, error_message = ipmag.aniso_depthplot()
        expected_file = os.path.join('.', 'rmag_anisotropy.txt')
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "Could not find rmag_anisotropy type file: {}.\nPlease provide a valid file path and try again".format(expected_file))

    def test_aniso_depthplot_with_files(self):
        #dir_path = os.path.join(WD, 'pmagpy_data_files', 'UTESTA')
        main_plot, plot_name = ipmag.aniso_depthplot(dir_path=self.aniso_WD, sum_file='CoreSummary_XXX_UTESTA.csv')
        assert(isinstance(main_plot, matplotlib.figure.Figure))
        self.assertEqual(plot_name, 'U1361A_ani_depthplot.svg')


    def test_aniso_depthplot_with_sum_file(self):
        dir_path = os.path.join(WD, 'pmagpy_data_files', 'UTESTA', 'UTESTA_MagIC')
        sum_file = 'CoreSummary_XXX_UTESTA.csv'
        main_plot, plot_name = ipmag.aniso_depthplot(dir_path=dir_path, sum_file=sum_file)
        assert(isinstance(main_plot, matplotlib.figure.Figure))
        self.assertEqual(plot_name, 'UTESTA_ani_depthplot.svg')

    def test_aniso_depthplot_with_age_option(self):
        main_plot, plot_name = ipmag.aniso_depthplot(age_file='er_ages.txt', dir_path=self.aniso_WD)
        assert(isinstance(main_plot, matplotlib.figure.Figure))
        self.assertEqual(plot_name, 'U1361A_ani_depthplot.svg')

    def test_aniso_depthplot_with_options(self):
        main_plot, plot_name = ipmag.aniso_depthplot(dmin=20, dmax=40, depth_scale='sample_core_depth', fmt='png', dir_path=self.aniso_WD)
        assert(isinstance(main_plot, matplotlib.figure.Figure))
        self.assertEqual(plot_name, 'U1361A_ani_depthplot.png')


class TestPmagResultsExtract(unittest.TestCase):
    def setUp(self):
        self.result_WD = os.path.join(WD, 'pmagpy_data_files', 'download_magic')
        os.chdir(self.result_WD)

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt',
                    'er_specimens.txt', 'er_samples.txt', 'my_er_samples.txt',
                    'er_sites.txt', 'rmag_anisotropy.txt',
                    'my_rmag_anisotropy.txt', 'rmag_results.txt',
                    'my_rmag_results.txt', 'my_samples.txt', 'Directions.txt',
                    'Directions.tex', 'Intensities.txt', 'Intensities.tex',
                    'SiteNfo.txt', 'SiteNfo.tex', 'Specimens.txt',
                    'Specimens.tex', 'Criteria.txt', 'Criteria.tex']
        pmag.remove_files(filelist, self.result_WD)

    def test_extract(self):
        direction_file = os.path.join(self.result_WD, 'Directions.txt')
        intensity_file = os.path.join(self.result_WD, 'Intensities.txt')
        site_file = os.path.join(self.result_WD, 'SiteNfo.txt')
        specimen_file = os.path.join(self.result_WD, 'Specimens.txt')
        crit_file = os.path.join(self.result_WD, 'Criteria.txt')
        files = [direction_file, intensity_file, site_file, specimen_file,
                 crit_file]
        for f in files:
            self.assertFalse(os.path.exists(f))
        res, outfiles = ipmag.pmag_results_extract()
        self.assertTrue(res)
        files = [os.path.join(self.result_WD, f) for f in outfiles]
        for f in files:
            self.assertTrue(os.path.exists(f))

    def test_extract_latex(self):
        direction_file = os.path.join(self.result_WD, 'Directions.tex')
        intensity_file = os.path.join(self.result_WD, 'Intensities.tex')
        site_file = os.path.join(self.result_WD, 'SiteNfo.tex')
        specimen_file = os.path.join(self.result_WD, 'Specimens.tex')
        crit_file = os.path.join(self.result_WD, 'Criteria.tex')
        files = [direction_file, intensity_file, site_file, specimen_file,
                 crit_file]
        for f in files:
            self.assertFalse(os.path.exists(f))
        res, outfiles = ipmag.pmag_results_extract(latex=True)
        self.assertTrue(res)
        files = [os.path.join(self.result_WD, f) for f in outfiles]
        for f in files:
            self.assertTrue(os.path.exists(f))

    
        


if __name__ == '__main__':
    unittest.main()
