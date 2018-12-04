#!/usr/bin/env python

import unittest
import os
import sys
import re
import matplotlib
import glob
from pmagpy import pmag
from pmagpy import ipmag
from pmagpy import contribution_builder as cb
from pmagpy import convert_2_magic as convert
#from pmagpy import find_pmag_dir
WD = pmag.get_test_WD()


class TestIGRF(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        os.chdir(WD)

    def test_igrf_output(self):
        result = ipmag.igrf([1999.1, 30, 20, 50])
        reference = [1.20288657e+00, 2.82331112e+01, 3.9782338913649881e+04]
        for num, item in enumerate(result):
            self.assertAlmostEqual(item, reference[num])

class TestUploadMagic(unittest.TestCase):

    def setUp(self):
        self.dir_path = os.path.join(WD, 'data_files', 'testing')

    def tearDown(self):
        tables = ['measurements', 'specimens', 'samples',
                  'sites', 'locations', 'ages', 'criteria',
                  'contribution']
        tables.extend([tname + "_errors" for tname in tables])
        possible_files = os.listdir(WD)
        for table in tables:
            fname = table + ".txt"
            if fname in possible_files:
                try:
                    print('trying to remove', os.path.join(WD, fname))
                    os.remove(os.path.join(WD, fname))
                except OSError:
                    pass
        # get rid of partial upload files
        # like: Tel-Hazor_Tel-Megiddo_14.Jun.2017-1.txt
        pattern = re.compile('.*\w*[.]\w*[.]\w*[20]\d{2}\w*.txt$')
        remove = []
        for f in possible_files:
            if pattern.match(f):
                remove.append(f)
        pmag.remove_files(remove, WD)
        # and any in core_depthplot
        core_depthplot_dir = os.path.join(WD, 'data_files', 'core_depthplot')
        possible_files = os.listdir(core_depthplot_dir)
        remove = []
        for f in possible_files:
            if pattern.match(f):
                remove.append(f)
        pmag.remove_files(remove, core_depthplot_dir)
        # return to WD
        os.chdir(WD)


    def test_empty_dir(self):
        directory = os.path.join(self.dir_path, 'empty_dir')
        outfile, error_message, errors = ipmag.upload_magic2(dir_path=directory)
        self.assertFalse(errors)
        self.assertFalse(outfile)
        self.assertEqual(error_message, "no data found, upload file not created")
        files = os.listdir(directory)
        self.assertEqual(['blank.txt'], files)

    def test_with_invalid_files(self):
        directory = os.path.join(self.dir_path, 'my_project_with_errors')
        outfile, error_message, errors = ipmag.upload_magic2(dir_path=directory)
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
        outfile, error_message, errors = ipmag.upload_magic2(dir_path=os.path.join(self.dir_path, 'my_project'))
        self.assertTrue(outfile)
        self.assertEqual(error_message, '')
        self.assertFalse(errors)
        assert os.path.isfile(outfile)
        directory = os.path.join(self.dir_path, 'my_project_with_errors')
        os.remove(os.path.join(directory, outfile))

    def test3_with_invalid_files(self):
        dir_path = os.path.join(WD, 'data_files', '3_0', 'Megiddo')
        outfile, error_message, errors, all_errors = ipmag.upload_magic(dir_path=dir_path)
        msg = "file validation has failed.  You may run into problems if you try to upload this file."
        self.assertEqual(error_message, msg)
        # delete any upload file that was partially created
        import re
        pattern = re.compile('\w*[.]\w*[.]\w*[20]\d{2}\w*.txt$')
        possible_files = os.listdir(dir_path)
        files = []
        for f in possible_files:
            if pattern.match(f):
                files.append(f)
        pmag.remove_files(files, dir_path)


    def test3_with_contribution(self):
        dir_path = os.path.join(WD, 'data_files', '3_0', 'Megiddo')
        con = cb.Contribution(directory=dir_path)
        outfile, error_message, errors, all_errors = ipmag.upload_magic(contribution=con)
        msg = "file validation has failed.  You may run into problems if you try to upload this file."
        self.assertEqual(error_message, msg)
        # delete any upload file that was partially created
        import re
        pattern = re.compile('\A[^.]*\.[a-zA-Z]*\.\d{4}\_?\d*\.txt')
        possible_files = os.listdir(dir_path)
        files = []
        for f in possible_files:
            if pattern.match(f):
                files.append(f)
        pmag.remove_files(files, dir_path)

    @unittest.skipIf(sys.platform in ['win32', 'win62'], "data file isn't properly moved on windows")
    def test_depth_propagation(self):
        dir_path = os.path.join(WD, 'data_files', 'core_depthplot')
        #con = cb.Contribution(dir_path)
        #self.assertNotIn('core_depth', con.tables['sites'].df.index)
        #con.propagate_cols(['core_depth'], 'sites', 'samples', down=False)
        #self.assertIn('core_depth', con.tables['sites'].df.columns)
        #self.assertEqual(con.tables['sites'].df.loc['15-1-013', 'core_depth'], 55.23)
        #
        outfile, error_message, errors, all_errors = ipmag.upload_magic(dir_path=dir_path)
        print('mv {} {}'.format(outfile, WD))
        os.system('mv {} {}'.format(outfile, WD))
        outfile = os.path.join(WD, os.path.split(outfile)[1])
        ipmag.download_magic(outfile)
        con = cb.Contribution(WD)
        self.assertIn('core_depth', con.tables['sites'].df.columns)
        self.assertEqual(con.tables['sites'].df.loc['15-1-013', 'core_depth'], 55.23)


class TestDownloadMagic(unittest.TestCase):

    def setUp(self):
        self.download_dir = os.path.join(WD, 'data_files', "download_magic")

    def tearDown(self):
        tables = ['measurements.txt', 'specimens.txt', 'samples.txt',
                  'locations.txt', 'ages.txt', 'criteria.txt',
                  'contribution.txt']
        pmag.remove_files(tables, self.download_dir)


    def test_all_files_are_created(self):
        files = ['locations.txt', 'sites.txt', 'samples.txt', 'specimens.txt',
                 'measurements.txt', 'contribution.txt']
        pmag.remove_files(files, self.download_dir)
        ipmag.download_magic('magic_contribution_16533.txt',
                             dir_path=self.download_dir,
                             input_dir_path=self.download_dir)
        output_files = os.listdir(self.download_dir)
        for f in files:
            self.assertIn(f, output_files)


class TestCombineMagic(unittest.TestCase):

    def setUp(self):
        self.input_dir = os.path.join(WD, 'data_files', '3_0', 'McMurdo')

    def tearDown(self):
        outfiles = ['custom_outfile.txt']
        pmag.remove_files(outfiles, self.input_dir)
        pmag.remove_files(['custom.out'], WD)


    def test_with_custom_name(self):
        outfile = os.path.join(self.input_dir, 'custom_outfile.txt')
        if os.path.exists(outfile):
            os.remove(outfile)
        flist = ['locations.txt', 'new_locations.txt']
        flist = [os.path.join(self.input_dir, fname) for fname in flist]
        #res = ipmag.combine_magic(flist, 'custom_outfile.txt', 3, 'locations')
        res = ipmag.combine_magic(flist, outfile, 3, 'locations')
        self.assertTrue(res)
        self.assertEqual(res, outfile)
        self.assertTrue(os.path.exists(outfile))

    def test_with_remove_rows(self):
        flist = ['extra_specimens.txt', 'specimens.txt']
        flist = [os.path.join(self.input_dir, fname) for fname in flist]
        #flist = [os.path.join(self.input_dir, fname) for fname in flist]
        res = ipmag.combine_magic(flist, 'custom.out', data_model=3)
        with open(os.path.join(WD, 'custom.out')) as f:
            n = len(f.readlines()) - 2
        self.assertEqual(n, 2747)



#@unittest.skipIf(sys.platform in ['darwin'], 'currently causing fatal errors on OSX')
class TestCoreDepthplot(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt', 'er_specimens.txt', 'er_samples.txt', 'my_er_samples.txt', 'er_sites.txt', 'rmag_anisotropy.txt', 'my_rmag_anisotropy.txt', 'rmag_results.txt', 'my_rmag_results.txt']
        pmag.remove_files(filelist, WD)
        os.chdir(WD)

    def test_core_depthplot_with_no_files(self):
        program_ran, error_message = ipmag.core_depthplot(data_model_num=2)
        self.assertFalse(program_ran)
        self.assertEqual("You must provide either a magic_measurements file or a pmag_specimens file", error_message)

    def test_core_depthplot_bad_params(self):
        path = os.path.join(WD, 'data_files', 'core_depthplot')
        program_ran, error_message = ipmag.core_depthplot(input_dir_path=path,
                                                          samp_file='samples.txt')
        self.assertFalse(program_ran)
        self.assertEqual('No data found to plot\nTry again with different parameters', error_message)

    def test_core_depthplot_bad_method(self):
        path = os.path.join(WD, 'data_files', 'core_depthplot')
        program_ran, error_message = ipmag.core_depthplot(input_dir_path=path, step=5, meth='NA', age_file='ages.txt')
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'method: "{}" not supported'.format('NA'))


    def test_core_depthplot_success(self):
        path = os.path.join(WD, 'data_files', 'core_depthplot')
        program_ran, plot_name = ipmag.core_depthplot(input_dir_path=path, spc_file='pmag_specimens.txt', samp_file='er_samples.txt', meth='AF', step=15, data_model_num=2)
        #program_ran, plot_name = True, 'DSDP Site 522_m:_LT-AF-Z_core-depthplot.svg'
        self.assertTrue(program_ran)
        self.assertEqual(plot_name, 'DSDP Site 522_m:_LT-AF-Z_core-depthplot.svg')

    def test_core_depthplot_with_sum_file(self):
        path = os.path.join(WD, 'data_files', 'UTESTA', 'UTESTA_MagIC')
        sum_file = 'CoreSummary_XXX_UTESTA.csv'
        program_ran, plot_name = ipmag.core_depthplot(input_dir_path=path, spc_file='pmag_specimens.txt', samp_file='er_samples.txt', meth='AF', step=15, sum_file=sum_file, data_model_num=2)
        self.assertTrue(program_ran)
        outfile = 'UTESTA_m:_LT-AF-Z_core-depthplot.svg'
        self.assertEqual(plot_name, outfile)


    def test_core_depthplot_without_full_time_options(self):
        path = os.path.join(WD, 'data_files', 'core_depthplot')
        program_ran, error_message = ipmag.core_depthplot(input_dir_path=path, spc_file='pmag_specimens.txt', samp_file='er_samples.txt', meth='AF', step=15, fmt='png', pltInc=False, logit=True, pltTime=True)#, timescale='gts12', amin=0, amax=3) # pltDec = False causes failure with these data
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "To plot time, you must provide amin, amax, and timescale")

    def test_core_depthplot_success_with_options(self):
        path = os.path.join(WD, 'data_files', 'core_depthplot')
        program_ran, plot_name = ipmag.core_depthplot(input_dir_path=path, spc_file='pmag_specimens.txt', samp_file='er_samples.txt', meth='AF', step=15, fmt='png', pltInc=False, logit=True, pltTime=True, timescale='gts12', amin=0, amax=3, data_model_num=2) # pltDec = False causes failure with these data
        self.assertTrue(program_ran)
        self.assertEqual(plot_name, 'DSDP Site 522_m:_LT-AF-Z_core-depthplot.png')

    def test_core_depthplot_success_with_other_options(self):
        path = os.path.join(WD, 'data_files', 'core_depthplot')
        program_ran, plot_name = ipmag.core_depthplot(input_dir_path=path,
                                                      spc_file='pmag_specimens.txt',
                                                      age_file='er_ages.txt',
                                                      meth='AF', step=15,
                                                      fmt='png', pltInc=False,
                                                      logit=True, pltTime=True,
                                                      timescale='gts12',
                                                      amin=0, amax=3, data_model_num=2) # pltDec = False causes failure with these data
        self.assertTrue(program_ran)
        self.assertEqual(plot_name, 'DSDP Site 522_m:_LT-AF-Z_core-depthplot.png')

    def test_core_depthplot_data_model3(self):
        path = os.path.join(WD, 'data_files', 'core_depthplot')
        program_ran, plot_name = ipmag.core_depthplot(input_dir_path=path,
                                                      spc_file='specimens.txt',
                                                      age_file='ages.txt',
                                                      meth='AF', step=15,
                                                      fmt='png', pltInc=False,
                                                      logit=True, pltTime=True,
                                                      timescale='gts12',
                                                      amin=0, amax=3, data_model_num=3)
        self.assertTrue(program_ran)
        self.assertEqual(plot_name, 'DSDP Site 522_m:_LT-AF-Z_core-depthplot.png')


    def test_core_depthplot_data_model3_options(self):
        path = os.path.join(WD, 'data_files', 'core_depthplot')
        program_ran, plot_name = ipmag.core_depthplot(input_dir_path=path, samp_file='samples.txt',
                                                      meth='AF', step=15)
        self.assertTrue(program_ran)
        self.assertEqual(plot_name, 'DSDP Site 522_m:_LT-AF-Z_core-depthplot.svg')

#@unittest.skipIf(sys.platform in ['darwin'], 'currently causing fatal errors on OSX')
class TestAniDepthplot(unittest.TestCase):

    def setUp(self):
        self.aniso_WD = os.path.join(WD, 'data_files', 'ani_depthplot')

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt', 'er_specimens.txt', 'er_samples.txt', 'my_er_samples.txt', 'er_sites.txt', 'rmag_anisotropy.txt', 'my_rmag_anisotropy.txt', 'rmag_results.txt', 'my_rmag_results.txt', 'my_samples.txt']
        pmag.remove_files(filelist, WD)
        os.chdir(WD)

    def test_aniso_depthplot_with_no_files(self):
        program_ran, error_message = ipmag.ani_depthplot2()
        expected_file = pmag.resolve_file_name('rmag_anisotropy.txt')
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "Could not find rmag_anisotropy type file: {}.\nPlease provide a valid file path and try again".format(expected_file))

    def test_aniso_depthplot_with_files(self):
        #dir_path = os.path.join(WD, 'data_files', 'UTESTA')
        main_plot, plot_name = ipmag.ani_depthplot2(dir_path=self.aniso_WD, sum_file='CoreSummary_XXX_UTESTA.csv')
        assert(isinstance(main_plot, matplotlib.figure.Figure))
        self.assertEqual(plot_name, 'U1361A_ani_depthplot.svg')


    def test_aniso_depthplot_with_sum_file(self):
        dir_path = os.path.join(WD, 'data_files', 'UTESTA', 'UTESTA_MagIC')
        sum_file = 'CoreSummary_XXX_UTESTA.csv'
        main_plot, plot_name = ipmag.ani_depthplot2(dir_path=dir_path, sum_file=sum_file)
        assert(isinstance(main_plot, matplotlib.figure.Figure))
        self.assertEqual(plot_name, 'UTESTA_ani_depthplot.svg')

    def test_aniso_depthplot_with_age_option(self):
        main_plot, plot_name = ipmag.ani_depthplot2(age_file='er_ages.txt', dir_path=self.aniso_WD)
        assert(isinstance(main_plot, matplotlib.figure.Figure))
        self.assertEqual(plot_name, 'U1361A_ani_depthplot.svg')

    def test_aniso_depthplot_with_options(self):
        main_plot, plot_name = ipmag.ani_depthplot2(dmin=20, dmax=40, depth_scale='sample_core_depth', fmt='png', dir_path=self.aniso_WD)
        assert(isinstance(main_plot, matplotlib.figure.Figure))
        self.assertEqual(plot_name, 'U1361A_ani_depthplot.png')


class TestAniDepthplot3(unittest.TestCase):

    def setUp(self):
        self.aniso_WD = os.path.join(WD, 'data_files', 'ani_depthplot')

    def tearDown(self):
        filelist = ['measurements.txt', 'specimens.txt', 'samples.txt', 'sites.txt']
        pmag.remove_files(filelist, WD)
        os.chdir(WD)

    def test_aniso_depthplot_with_no_files(self):
        program_ran, error_message = ipmag.ani_depthplot()
        self.assertFalse(program_ran)
        self.assertEqual(error_message, "missing required file type: specimen")

    def test_aniso_depthplot_with_files(self):
        #dir_path = os.path.join(WD, 'data_files', 'UTESTA')
        main_plot, plot_name = ipmag.ani_depthplot(dir_path=self.aniso_WD,
                                                      meas_file="fake.txt",
                                                      sum_file='CoreSummary_XXX_UTESTA.csv')
        assert(isinstance(main_plot, matplotlib.figure.Figure))
        self.assertEqual(plot_name, 'U1361A_ani_depthplot.svg')

    def test_aniso_depthplot_with_meas_file(self):
        main_plot, plot_name = ipmag.ani_depthplot(dir_path=self.aniso_WD,
                                                      sum_file='CoreSummary_XXX_UTESTA.csv')
        assert(isinstance(main_plot, matplotlib.figure.Figure))
        self.assertEqual(plot_name, 'U1361A_ani_depthplot.svg')

    def test_aniso_depthplot_with_sum_file(self):
        dir_path = os.path.join(WD, 'data_files', 'UTESTA', 'UTESTA_MagIC3')
        sum_file = 'CoreSummary_XXX_UTESTA.csv'
        main_plot, plot_name = ipmag.ani_depthplot(dir_path=dir_path,
                                                      sum_file=sum_file,
                                                      depth_scale='core_depth')
        assert(isinstance(main_plot, matplotlib.figure.Figure))
        self.assertEqual(plot_name, 'UTESTA_ani_depthplot.svg')

    def test_aniso_depthplot_with_age_option(self):
        main_plot, plot_name = ipmag.ani_depthplot(age_file='ages.txt', dir_path=self.aniso_WD)
        assert(isinstance(main_plot, matplotlib.figure.Figure))
        self.assertEqual(plot_name, 'U1361A_ani_depthplot.svg')

    def test_aniso_depthplot_with_options(self):
        main_plot, plot_name = ipmag.ani_depthplot(dmin=20, dmax=40,
                                                      depth_scale='core_depth',
                                                      fmt='png', dir_path=self.aniso_WD)
        assert(isinstance(main_plot, matplotlib.figure.Figure))
        self.assertEqual(plot_name, 'U1361A_ani_depthplot.png')


class TestPmagResultsExtract(unittest.TestCase):

    def setUp(self):
        self.result_WD = os.path.join(WD, 'data_files', 'download_magic')
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
        os.chdir(WD)

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


class TestAarmMagic(unittest.TestCase):
    def setUp(self):
        self.aarm_WD = os.path.join(WD, 'data_files', 'aarm_magic')

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt',
                    'er_samples.txt', 'my_er_samples.txt',
                    'er_sites.txt', 'rmag_anisotropy.txt']
        pmag.remove_files(filelist, self.aarm_WD)
        os.chdir(WD)

    def test_aarm_success(self):
        convert.sio('arm_magic_example.dat', self.aarm_WD, meas_file="aarm_measurements.txt")
        res, outfile = ipmag.aarm_magic('aarm_measurements.txt', self.aarm_WD,
                                        spec_file='custom_specimens.txt')
        self.assertTrue(res)
        self.assertEqual(outfile, os.path.join(self.aarm_WD, 'custom_specimens.txt'))


class TestAtrmMagic(unittest.TestCase):
    def setUp(self):
        self.atrm_WD = os.path.join(WD, 'data_files', 'atrm_magic')

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt',
                    'custom_specimens.txt', 'er_samples.txt', 'my_er_samples.txt',
                    'er_sites.txt', 'rmag_anisotropy.txt']
        pmag.remove_files(filelist, self.atrm_WD)
        os.chdir(WD)

    def test_atrm_success(self):
        res, outfile = ipmag.atrm_magic('atrm_measurements3.txt', self.atrm_WD,
                                        input_spec_file='orig_specimens.txt',
                                        output_spec_file='custom_specimens.txt')
        self.assertTrue(res)
        self.assertEqual(outfile, os.path.join(self.atrm_WD, 'custom_specimens.txt'))
        # check that samples are there from input specimen file
        df = cb.MagicDataFrame(outfile)
        self.assertTrue(any(df.df['sample']))


class TestHysteresisMagic(unittest.TestCase):
    def setUp(self):
        self.hyst_WD = os.path.join(WD, 'data_files', 'hysteresis_magic')

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt',
                    'custom_specimens.txt', 'er_samples.txt', 'my_er_samples.txt',
                    'er_sites.txt', 'rmag_anisotropy.txt']
        pmag.remove_files(filelist, self.hyst_WD)
        glob_strings = ['*.svg', '*.png', "{}/*.svg".format(self.hyst_WD),
                        "{}/*.png".format(self.hyst_WD)]
        for string in glob_strings:
            files = glob.glob(string)
            for fname in files:
                os.remove(fname)
        os.chdir(WD)

    def test_hysteresis_no_figs(self):
        res, outfiles = ipmag.hysteresis_magic(input_dir_path=self.hyst_WD,
                                               spec_file='custom_specimens.txt', make_plots=False)
        self.assertTrue(res)
        self.assertEqual(outfiles[0], os.path.realpath(os.path.join(".", "custom_specimens.txt")))
        fnames = glob.glob("*.svg")
        self.assertFalse(fnames)

    def test_hysteresis_with_figs(self):
        res, outfiles = ipmag.hysteresis_magic(input_dir_path=self.hyst_WD,
                                               spec_file='custom_specimens.txt', make_plots=True)
        self.assertTrue(res)
        self.assertEqual(outfiles[0], os.path.realpath(os.path.join(".", "custom_specimens.txt")))
        fnames = glob.glob("*.svg")
        self.assertEqual(len(fnames), 32)

    def test_hysteresis_bad_file(self):
        res, outfiles = ipmag.hysteresis_magic(self.hyst_WD, meas_file="fake.txt",
                                               spec_file='custom_specimens.txt',
                                               save_plots=True)
        self.assertFalse(res)

    def test_hysteresis_success(self):
        res, outfiles = ipmag.hysteresis_magic(output_dir_path=self.hyst_WD, spec_file='custom_specimens.txt',
                                               save_plots=True, fmt="png")
        self.assertTrue(res)
        for f in outfiles:
            print('f', f)
            self.assertTrue(os.path.exists(f))
        fstring = '{}/*.png'.format(self.hyst_WD)
        files = glob.glob(fstring)
        self.assertEqual(len(files), 32)


class TestSitesExtract(unittest.TestCase):
    def setUp(self):
        self.WD_0 = os.path.join(WD, 'data_files', '3_0', 'McMurdo')
        self.WD_1 = os.path.join(WD, 'data_files', '3_0', 'Megiddo')

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt',
            'custom_specimens.txt', 'er_samples.txt', 'my_er_samples.txt',
            'er_sites.txt', 'rmag_anisotropy.txt']

        patterns = [os.path.join(self.WD_0, "*.tex"), os.path.join(self.WD_0, "*.xls"),
                    os.path.join(self.WD_1, "*.tex"), os.path.join(self.WD_1, "*.xls"),
                    os.path.join(self.WD_0, "*.aux"), os.path.join(self.WD_0, "*.dvi"),
                    os.path.join(self.WD_1, "*.aux"), os.path.join(self.WD_1, "*.dvi"),
                    os.path.join(self.WD_0, "*.gz"), os.path.join(self.WD_1, "*.gz")]

        for pattern in patterns:
            for fname in glob.glob(pattern):
                os.remove(fname)


    def test_McMurdo(self):
        res, outfiles = ipmag.sites_extract(site_file='sites.txt', output_dir_path=self.WD_0, latex=False)
        self.assertTrue(res)
        for f in outfiles:
            self.assertTrue(os.path.exists(f))

    def test_Megiddo(self):
        res, outfiles = ipmag.sites_extract(site_file='sites.txt', output_dir_path=self.WD_1, latex=True)
        self.assertTrue(res)
        self.assertEqual(len(outfiles), 2)
        for fname in outfiles:
            self.assertTrue(os.path.exists(fname))
            self.assertTrue(fname.endswith('.tex'))


class TestSpecimensExtract(unittest.TestCase):
    def setUp(self):
        self.WD_0 = os.path.join(WD, 'data_files', '3_0', 'McMurdo')
        self.WD_1 = os.path.join(WD, 'data_files', '3_0', 'Megiddo')

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt',
            'custom_specimens.txt', 'er_samples.txt', 'my_er_samples.txt',
            'er_sites.txt', 'rmag_anisotropy.txt']

        patterns = [os.path.join(self.WD_0, "*.tex"), os.path.join(self.WD_0, "*.xls"),
                    os.path.join(self.WD_1, "*.tex"), os.path.join(self.WD_1, "*.xls"),
                    os.path.join(self.WD_0, "*.aux"), os.path.join(self.WD_0, "*.dvi"),
                    os.path.join(self.WD_1, "*.aux"), os.path.join(self.WD_1, "*.dvi"),
                    os.path.join(self.WD_0, "*.gz"), os.path.join(self.WD_1, "*.gz")]

        for pattern in patterns:
            for fname in glob.glob(pattern):
                os.remove(fname)


    def test_McMurdo(self):
        res, outfiles = ipmag.specimens_extract(spec_file='specimens.txt', output_dir_path=self.WD_0, latex=False)
        self.assertTrue(res)
        for f in outfiles:
            self.assertTrue(os.path.exists(f))

    def test_Megiddo(self):
        res, outfiles = ipmag.specimens_extract(spec_file='specimens.txt', output_dir_path=self.WD_1, latex=True)
        self.assertTrue(res)
        self.assertEqual(len(outfiles), 1)
        for fname in outfiles:
            self.assertTrue(os.path.exists(fname))
            self.assertTrue(fname.endswith('.tex'))



class TestCriteriaExtract(unittest.TestCase):
    def setUp(self):
        self.WD_0 = os.path.join(WD, 'data_files', '3_0', 'McMurdo')
        self.WD_1 = os.path.join(WD, 'data_files', '3_0', 'Megiddo')

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt',
            'custom_specimens.txt', 'er_samples.txt', 'my_er_samples.txt',
            'er_sites.txt', 'rmag_anisotropy.txt']

        patterns = [os.path.join(self.WD_0, "*.tex"), os.path.join(self.WD_0, "*.xls"),
                    os.path.join(self.WD_1, "*.tex"), os.path.join(self.WD_1, "*.xls"),
                    os.path.join(self.WD_0, "*.aux"), os.path.join(self.WD_0, "*.dvi"),
                    os.path.join(self.WD_1, "*.aux"), os.path.join(self.WD_1, "*.dvi"),
                    os.path.join(self.WD_0, "*.gz"), os.path.join(self.WD_1, "*.gz")]

        for pattern in patterns:
            for fname in glob.glob(pattern):
                os.remove(fname)


    def test_McMurdo(self):
        res, outfiles = ipmag.criteria_extract('criteria.txt', output_dir_path=self.WD_0, latex=False)
        self.assertTrue(res)
        for f in outfiles:
            self.assertTrue(os.path.exists(f))

    def test_Megiddo(self):
        res, outfiles = ipmag.criteria_extract('criteria.txt', output_dir_path=self.WD_1, latex=True)
        self.assertTrue(res)
        self.assertEqual(len(outfiles), 1)
        for fname in outfiles:
            self.assertTrue(os.path.exists(fname))
            self.assertTrue(fname.endswith('.tex'))


class TestThellierMagic(unittest.TestCase):
    def setUp(self):
        self.thel_WD = os.path.join(WD, 'data_files', 'thellier_magic')

    def tearDown(self):
        filelist = ['magic_measurements.txt', 'my_magic_measurements.txt',
                    'custom_specimens.txt', 'er_samples.txt', 'my_er_samples.txt',
                    'er_sites.txt', 'rmag_anisotropy.txt']
        pmag.remove_files(filelist, self.thel_WD)
        glob_strings = ['*.svg', '*.png', os.path.join(self.thel_WD, "*.svg"),
                        os.path.join(self.thel_WD, "*.png")]
        for string in glob_strings:
            files = glob.glob(string)
            for fname in files:
                os.remove(fname)
        os.chdir(WD)

    def test_success(self):
        res, outfiles = ipmag.thellier_magic(input_dir_path=self.thel_WD, n_specs=5)
        self.assertTrue(res)
        self.assertEqual(len(glob.glob("*.svg")), 20)

    def test_success_all_specs(self):
        res, outfiles = ipmag.thellier_magic(input_dir_path=self.thel_WD, fmt="png")
        self.assertTrue(res)
        self.assertEqual(len(glob.glob("*.png")), 1076)

    def test_one_spec(self):
        for fname in glob.glob("*.png"):
            os.remove(fname)
        res, outfiles = ipmag.thellier_magic(input_dir_path=self.thel_WD, spec="s2s0-03",
                                             save_plots=True, fmt="png")
        self.assertTrue(res)
        self.assertEqual(len(glob.glob("*.png")), 4)
        self.assertTrue(os.path.exists("s2s0-03_arai.png"))

    def test_one_spec_with_output_dir(self):
        res, outfiles = ipmag.thellier_magic(dir_path=self.thel_WD, spec="s2s0-03",
                                             save_plots=True, fmt="png")
        self.assertTrue(res)
        self.assertEqual(len(glob.glob(os.path.join(self.thel_WD, "*.png"))), 4)
        self.assertTrue(os.path.exists(os.path.join(self.thel_WD, "s2s0-03_arai.png")))




if __name__ == '__main__':
    unittest.main()
