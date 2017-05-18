#!/usr/bin/env python

#---------------------------------------------------------------------------
# Author: Ron Shaar
# Revision notes
#
# Rev 2.1 June 4th 2015.
# Fix small zero division bug.
#
# Rev 2.0 November 2014
#
# Rev 1.0 Initial revision August 2012
#
#
#---------------------------------------------------------------------------
import matplotlib
import pylab
import scipy
import os
import time
import pandas as pd
from pylab import *
from scipy import *
import wx
#import  scipy.interpolate
import gzip
#import pmag
import copy
#from scipy.optimize import curve_fit
from . import thellier_gui_lib


class thellier_auto_interpreter():

    def __init__(self, Data, Data_hierarchy, interpreter_path, acceptance_criteria, preferences, GUI_log, thermal, microwave):
        global THERMAL
        THERMAL = thermal
        global MICROWAVE
        MICROWAVE = microwave

        self.GUI_log = GUI_log
        self.WD = interpreter_path
        self.acceptance_criteria = acceptance_criteria
        self.preferences = preferences
        self.Data = Data
        self.Data_hierarchy = Data_hierarchy
        # self.run_interpreter()

    #==================================================
    # Thellier Auto Interpreter Tool
    #==================================================

    def run_interpreter(self):
        """
        Run thellier_auto_interpreter
        """

        import random
        import copy

        start_time = time.time()
        #------------------------------------------------
        # Clean work directory
        #------------------------------------------------

        # self.write_acceptance_criteria_to_file()
        try:
            shutil.rmtree(os.path.join(self.WD, "thellier_interpreter"))
        except:
            pass

        try:
            os.mkdir(os.path.join(self.WD, "thellier_interpreter"))
        except:
            pass

        #------------------------------------------------
        # Intialize interpreter output files:
        # Prepare header for "Thellier_auto_interpretation.all.txt"
        # All the acceptable interpretation are saved in this file
        #------------------------------------------------

        # sort acceptance criteria
        self.specimen_criteria = []
        for crit in list(self.acceptance_criteria.keys()):
            if 'category' in list(self.acceptance_criteria[crit].keys()):
                if self.acceptance_criteria[crit]['category'] == "IE-SPEC":
                    if self.acceptance_criteria[crit]['value'] != -999:
                        self.specimen_criteria.append(crit)

        # sort acceptance criteria
        sample_criteria = []
        for crit in list(self.acceptance_criteria.keys()):
            if 'category' in list(self.acceptance_criteria[crit].keys()):
                if self.acceptance_criteria[crit]['category'] == "IE-SAMP":
                    if self.acceptance_criteria[crit]['value'] != -999:
                        sample_criteria.append(crit)

        # sort acceptance criteria
        site_criteria = []
        for crit in list(self.acceptance_criteria.keys()):
            if 'category' in list(self.acceptance_criteria[crit].keys()):
                if self.acceptance_criteria[crit]['category'] == "thellier_gui":
                    if self.acceptance_criteria[crit]['value'] != -999:
                        site_criteria.append(crit)

        # sort acceptance criteria
        thellier_gui_criteria = []
        for crit in list(self.acceptance_criteria.keys()):
            if 'category' in list(self.acceptance_criteria[crit].keys()):
                if self.acceptance_criteria[crit]['category'] == "thellier_gui":
                    if self.acceptance_criteria[crit]['value'] != -999:
                        thellier_gui_criteria.append(crit)

        #----------------------------

        # log file
        self.thellier_interpreter_log = open(
            self.WD + "/" + "/thellier_interpreter//thellier_interpreter.log", 'w')
        self.thellier_interpreter_log.write("-I- Start auto interpreter\n")

        # "all grade A interpretation
        thellier_interpreter_all = open(
            self.WD + "/thellier_interpreter/thellier_interpreter_all.txt", 'w')
        thellier_interpreter_all.write("tab\tpmag_specimens\n")
        String = "er_specimen_name\tmeasurement_step_min\tmeasurement_step_max\tspecimen_lab_field_dc_uT\tspecimen_int_corr_anisotropy\tspecimen_int_corr_nlt\tspecimen_int_corr_cooling_rate\tspecimen_int_uT\t"
        # + ["specimen_b"] + ['specimen_cm_x'] + ['specimen_cm_y']:
        for crit in self.specimen_criteria:
            String = String + crit + "\t"
        String = String[:-1] + "\n"
        thellier_interpreter_all.write(String)

        # specimen_bound
        Fout_specimens_bounds = open(
            self.WD + "/thellier_interpreter/thellier_interpreter_specimens_bounds.txt", 'w')
        String = "acceptance criteria:\n"
        for crit in self.specimen_criteria:
            String = String + crit + "\t"
        Fout_specimens_bounds.write(String[:-1] + "\n")
        String = ""
        for crit in self.specimen_criteria:
            if type(self.acceptance_criteria[crit]['value']) == str:
                string = self.acceptance_criteria[crit]['value']
            elif type(self.acceptance_criteria[crit]['value']) == bool:
                string = str(self.acceptance_criteria[crit]['value'])
            elif type(self.acceptance_criteria[crit]['value']) == int or type(self.acceptance_criteria[crit]['value']) == float:
                if self.acceptance_criteria[crit]['decimal_points'] == -999:
                    string = "{:.3f}".format(self.acceptance_criteria[crit]['value'])
                else:
                    string = "{:.{}f}".format(self.acceptance_criteria[crit]['value'],
                                             self.acceptance_criteria[crit]['decimal_points'])

            else:
                string=""

            String=String+"%s\t"%string
        Fout_specimens_bounds.write(String[:-1]+"\n")
        Fout_specimens_bounds.write("--------------------------------\n")
        Fout_specimens_bounds.write("er_sample_name\ter_specimen_name\tspecimen_int_corr_anisotropy\tAnisotropy_code\tspecimen_int_corr_nlt\tspecimen_int_corr_cooling_rate\tspecimen_lab_field_dc_uT\tspecimen_int_min_uT\tspecimen_int_max_uT\tWARNING\n")

        #----------------------------------

        criteria_string = "acceptance criteria:\n"
        for crit in self.specimen_criteria + sample_criteria + site_criteria + thellier_gui_criteria:
            criteria_string = criteria_string + crit + "\t"
        criteria_string = criteria_string[:-1] + "\n"
        for crit in self.specimen_criteria + sample_criteria + site_criteria + thellier_gui_criteria:
            if type(self.acceptance_criteria[crit]['value']) == str:
                string = self.acceptance_criteria[crit]['value']
            elif type(self.acceptance_criteria[crit]['value']) == bool:
                string = str(self.acceptance_criteria[crit]['value'])
            elif type(self.acceptance_criteria[crit]['value']) == int or type(self.acceptance_criteria[crit]['value']) == float:
                if self.acceptance_criteria[crit]['decimal_points'] == -999:
                    string = "%.3e" % (
                        float(self.acceptance_criteria[crit]['value']))
                else:
                    string = "{:.{}f}".format(self.acceptance_criteria[crit]['value'],
                                              self.acceptance_criteria[crit]['decimal_points'])
            else:
                string = ""

            criteria_string = criteria_string + "%s\t" % string
        criteria_string = criteria_string[:-1] + "\n"
        criteria_string = criteria_string + "---------------------------------\n"

        # STDEV-OPT output files
        if self.acceptance_criteria['interpreter_method']['value'] == 'stdev_opt':
            self.Fout_STDEV_OPT_redo = open(
                self.WD + "/thellier_interpreter/thellier_interpreter_STDEV-OPT_redo", 'w')
            self.Fout_STDEV_OPT_specimens = open(
                self.WD + "/thellier_interpreter/thellier_interpreter_STDEV-OPT_specimens.txt", 'w')

            self.Fout_STDEV_OPT_specimens.write("tab\tpmag_specimens\n")
            String = "er_sample_name\ter_specimen_name\tspecimen_int_uT\tmeasurement_step_min\tmeasurement_step_min\tspecimen_lab_field_dc\tAnisotropy_correction_factor\tNLT_correction_factor\tCooling_rate_correction_factor\t"
            for crit in self.specimen_criteria:
                String = String + crit + "\t"
            self.Fout_STDEV_OPT_specimens.write(String[:-1] + "\n")

            if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
                self.Fout_STDEV_OPT_samples = open(
                    self.WD + "/thellier_interpreter/thellier_interpreter_STDEV-OPT_samples.txt", 'w')
                self.Fout_STDEV_OPT_samples.write(criteria_string)
                self.Fout_STDEV_OPT_samples.write(
                    "er_sample_name\tsample_int_n\tsample_int_uT\tsample_int_sigma_uT\tsample_int_sigma_perc\tsample_int_min_uT\tsample_int_min_sigma_uT\tsample_int_max_uT\tsample_int_max_sigma_uT\tsample_int_interval_uT\tsample_int_interval_perc\tWarning\n")
            else:
                self.Fout_STDEV_OPT_sites = open(
                    self.WD + "/thellier_interpreter/thellier_interpreter_STDEV-OPT_sites.txt", 'w')
                self.Fout_STDEV_OPT_sites.write(criteria_string)
                self.Fout_STDEV_OPT_sites.write(
                    "er_site_name\tsite_int_n\tsite_int_uT\tsite_int_sigma_uT\tsite_int_sigma_perc\tsite_int_min_uT\tsite_int_min_sigma_uT\tsite_int_max_uT\tsite_int_max_sigma_uT\tsite_int_interval_uT\tsite_int_interval_perc\tWarning\n")

        # simple bootstrap output files
        # Dont supports site yet!

        if self.acceptance_criteria['interpreter_method']['value'] == 'bs':
            Fout_BS_samples = open(
                self.WD + "/thellier_interpreter/thellier_interpreter_BS_samples.txt", 'w')
            Fout_BS_samples.write(criteria_string)
            # Fout_BS_samples.write("---------------------------------\n")
            Fout_BS_samples.write(
                "er_sample_name\tsample_int_n\tsample_int_uT\tsample_int_68_low\tsample_int_68_high\tsample_int_95_low\tsample_int_95_high\tsample_int_sigma_uT\tsample_int_sigma_perc\tWARNING\n")
        # parameteric bootstrap output files

        if self.acceptance_criteria['interpreter_method']['value'] == 'bs_par':
            Fout_BS_PAR_samples = open(
                self.WD + "/thellier_interpreter/thellier_interpreter_BS-PAR_samples.txt", 'w')
            Fout_BS_PAR_samples.write(criteria_string)
            # Fout_BS_PAR_samples.write("---------------------------------\n")
            Fout_BS_PAR_samples.write(
                "er_sample_name\tsample_int_n\tsample_int_uT\tsample_int_68_low\tsample_int_68_high\tsample_int_95_low\tsample_int_95_high\tsample_int_sigma_uT\tsample_int_sigma_perc\tWARNING\n")

        self.thellier_interpreter_log.write(
            "-I- using paleointenisty statistics:\n")
        self.thellier_interpreter_log.write(criteria_string)

        #------------------------------------------------

        specimens_list = list(self.Data.keys())
        specimens_list.sort()
        self.thellier_interpreter_log.write(
            "-I- Found %i specimens\n" % (len(specimens_list)))

        # try:
        All_grade_A_Recs = {}
        print('-I- Running through specimens:')
        for s in specimens_list:
            self.thellier_interpreter_log.write(
                "-I- doing now specimen %s\n" % s)
            self.Data[s]['pars'] = {}
            self.Data[s]['pars']['lab_dc_field'] = self.Data[s]['lab_dc_field']
            self.Data[s]['pars']['er_specimen_name'] = s
            self.Data[s]['pars']['er_sample_name'] = self.Data_hierarchy['specimens'][s]
            temperatures = self.Data[s]['t_Arai']

            # check that all temperatures are in right order:
            ignore_specimen = False
            for t in range(len(temperatures) - 1):
                if float(temperatures[t + 1]) < float(temperatures[t]):
                    self.thellier_interpreter_log.write(
                        "-W- Found problem in the temperature order of specimen %s. skipping specimen\n" % (s))
                    ignore_specimen = True
            if ignore_specimen:
                continue
            if self.acceptance_criteria['specimen_int_n']['value'] != -999:
                specimen_int_n = min(
                    3, int(self.acceptance_criteria['specimen_int_n']['value']))
            else:
                specimen_int_n = 3
            #-------------------------------------------------
            # loop through all possible tmin,tmax and check if pass criteria
            #-------------------------------------------------
            # print s
            for tmin_i in range(len(temperatures) - specimen_int_n + 1):
                # check if to include NRM
                # print temperatures
                # print  self.acceptance_criteria['include_nrm']['value']
                if self.acceptance_criteria['include_nrm']['value'] == -999:
                    # print " Its False"
                    if temperatures[tmin_i] == 273:
                        continue
                    #    print "ignoring NRM",tmin_i,temperatures[tmin_i]
                # print tmin_i
                for tmax_i in range(tmin_i + specimen_int_n - 1, len(temperatures)):
                    # print tmax_i
                    # print len(temperatures)
                    tmin = temperatures[tmin_i]
                    tmax = temperatures[tmax_i]
                    pars = thellier_gui_lib.get_PI_parameters(
                        self.Data, self.acceptance_criteria, self.preferences, s, tmin, tmax, self.GUI_log, THERMAL, MICROWAVE)
                    if not pars:  # error with getting pars
                        message_string = '-W- Problem in SPD. Could not calculate any parameters for {} with tmin: {} and tmax {}. Check data for typos, make sure temperatures are correct, etc.'.format(
                            s, tmin, tmax)
                        self.thellier_interpreter_log.write(
                            message_string + "\n")
                        continue
                    if 'NLT_specimen_correction_factor' not in list(pars.keys()):
                        # problem in get_PI_parameters (probably with
                        # tmin/zdata).  can't run specimen
                        message_string = '-W- Problem in get_PI_parameters. Could not get all parameters for {} with tmin: {} and tmax: {}. Check data for typos, make sure temperatures are correct, etc.'.format(
                            s, tmin, tmax)
                        self.thellier_interpreter_log.write(
                            message_string + "\n")
                        continue
                    pars = thellier_gui_lib.check_specimen_PI_criteria(
                        pars, self.acceptance_criteria)
                    #-------------------------------------------------
                    # check if pass the criteria
                    #-------------------------------------------------

                    if 'specimen_fail_criteria' in list(pars.keys()) and len(pars['specimen_fail_criteria']) > 0:
                        # Fail:
                        message_string = "-I- specimen %s (%.0f-%.0f) FAIL on: " % (s, float(
                            pars["measurement_step_min"]) - 273, float(pars["measurement_step_max"]) - 273)
                        for parameter in pars['specimen_fail_criteria']:
                            if "scat" not in parameter:
                                message_string = message_string + \
                                    parameter + "= %f,  " % pars[parameter]
                            else:
                                message_string = message_string + parameter + \
                                    "= %s,  " % str(pars[parameter])

                        self.thellier_interpreter_log.write(
                            message_string + "\n")
                    elif 'specimen_fail_criteria' in list(pars.keys()) and len(pars['specimen_fail_criteria']) == 0:

                        # PASS:
                        message_string = "-I- specimen %s (%.0f-%.0f) PASS" % (s, float(
                            pars["measurement_step_min"]) - 273, float(pars["measurement_step_max"]) - 273)
                        self.thellier_interpreter_log.write(
                            message_string + "\n")

                        #----------------------------------------------------
                        # Save all the grade A interpretation in thellier_interpreter_all.txt
                        #----------------------------------------------------

                        String = s + "\t"
                        String = String + \
                            "%.0f\t" % (
                                float(pars["measurement_step_min"]) - 273.)
                        String = String + \
                            "%.0f\t" % (
                                float(pars["measurement_step_max"]) - 273.)
                        String = String + \
                            "%.0f\t" % (float(pars["lab_dc_field"]) * 1e6)

                        if "Anisotropy_correction_factor" in list(pars.keys()):
                            String = String + \
                                "%.2f\t" % float(
                                    pars["Anisotropy_correction_factor"])
                        else:
                            String = String + "-\t"
                        if float(pars["NLT_specimen_correction_factor"]) != -999:
                            String = String + \
                                "%.2f\t" % float(
                                    pars["NLT_specimen_correction_factor"])
                        else:
                            String = String + "-\t"
                        if float(pars["specimen_int_corr_cooling_rate"]) != -999 and float(pars["specimen_int_corr_cooling_rate"]) != -1:
                            String = String + \
                                "%.2f\t" % float(
                                    pars["specimen_int_corr_cooling_rate"])
                        else:
                            String = String + "-\t"
                        Bancient = float(pars['specimen_int_uT'])
                        String = String + "%.1f\t" % (Bancient)
                        # + ["specimen_b"] + ["specimen_cm_x"] + ["specimen_cm_y"]:
                        for key in self.specimen_criteria:
                            if type(pars[key]) == str:
                                String = String + pars[key] + "\t"
                            else:
                                String = String + \
                                    "%.3e" % (float(pars[key])) + "\t"
                        String = String[:-1] + "\n"

                        thellier_interpreter_all.write(String)

                        #-------------------------------------------------
                        # save 'acceptable' (grade A) specimen interpretaion
                        # All_grade_A_Recs={}
                        # All_grade_A_Recs[specimen_name]["tmin,tmax"]={PI pars sorted in dictionary}
                        #-------------------------------------------------

                        if s not in list(All_grade_A_Recs.keys()):
                            All_grade_A_Recs[s] = {}
                        new_pars = {}
                        for k in list(pars.keys()):
                            new_pars[k] = pars[k]
                        TEMP = "%.0f,%.0f" % (float(
                            pars["measurement_step_min"]) - 273, float(pars["measurement_step_max"]) - 273)
                        All_grade_A_Recs[s][TEMP] = new_pars

        specimens_list = list(All_grade_A_Recs.keys())
        specimens_list.sort()
        Grade_A_samples = {}
        Grade_A_sites = {}
        Redo_data_specimens = {}

        #--------------------------------------------------------------
        # specimens bound file
        #--------------------------------------------------------------

        for s in specimens_list:

            sample = self.Data_hierarchy['specimens'][s]
            site = thellier_gui_lib.get_site_from_hierarchy(
                sample, self.Data_hierarchy)
            B_lab = float(self.Data[s]['lab_dc_field']) * 1e6
            B_min, B_max = 1e10, 0.
            NLT_factor_min, NLT_factor_max = 1e10, 0.
            all_B_tmp_array = []

            for TEMP in list(All_grade_A_Recs[s].keys()):
                pars = All_grade_A_Recs[s][TEMP]
                if "AC_anisotropy_type" in list(pars.keys()):
                    AC_correction_factor = pars["Anisotropy_correction_factor"]
                    AC_correction_type = pars["AC_anisotropy_type"]
                    WARNING = ""
                    if "AC_WARNING" in list(pars.keys()):
                        WARNING = WARNING + pars["AC_WARNING"]
                else:
                    AC_correction_factor = 1.
                    AC_correction_type = "-"
                    WARNING = "WARNING: No anisotropy correction"

                B_anc = pars['specimen_int_uT']

                if B_anc < B_min:
                    B_min = B_anc
                if B_anc > B_max:
                    B_max = B_anc
                if pars["NLT_specimen_correction_factor"] != -1:
                    NLT_f = pars['NLT_specimen_correction_factor']
                    if NLT_f < NLT_factor_min:
                        NLT_factor_min = NLT_f
                    if NLT_f > NLT_factor_max:
                        NLT_factor_max = NLT_f

                # sort by samples
                #------------------------------------------------------------

                if sample not in list(Grade_A_samples.keys()):
                    Grade_A_samples[sample] = {}
                if s not in list(Grade_A_samples[sample].keys()) and len(All_grade_A_Recs[s]) > 0:
                    Grade_A_samples[sample][s] = []

                if pd.notnull(B_anc):
                    Grade_A_samples[sample][s].append(B_anc)

                # sort by sites
                #------------------------------------------------------------

                if site not in list(Grade_A_sites.keys()):
                    Grade_A_sites[site] = {}
                if s not in list(Grade_A_sites[site].keys()) and len(All_grade_A_Recs[s]) > 0:
                    Grade_A_sites[site][s] = []
                if pd.notnull(B_anc):
                    Grade_A_sites[site][s].append(B_anc)

                # ? check
                #------------------------------------------------------------

                if s not in list(Redo_data_specimens.keys()):
                    Redo_data_specimens[s] = {}

            # write to specimen_bounds
            #----------------------------------------------------------------

            if pars["NLT_specimen_correction_factor"] != -1:
                NLT_factor = "%.2f" % (NLT_factor_max)
            else:
                NLT_factor = "-"

            if pars["specimen_int_corr_cooling_rate"] != -1 and pars["specimen_int_corr_cooling_rate"] != -999:
                CR_factor = "%.2f" % (
                    float(pars["specimen_int_corr_cooling_rate"]))
            else:
                CR_factor = "-"
            if 'cooling_rate_data' in list(self.Data[s].keys()):
                if 'CR_correction_factor_flag' in list(self.Data[s]['cooling_rate_data'].keys()):
                    if self.Data[s]['cooling_rate_data']['CR_correction_factor_flag'] != "calculated":
                        if "inferred" in self.Data[s]['cooling_rate_data']['CR_correction_factor_flag']:
                            WARNING = WARNING + ";" + "cooling rate correction inferred from sister specimens"
                        if "alteration" in self.Data[s]['cooling_rate_data']['CR_correction_factor_flag']:
                            WARNING = WARNING + ";" + "cooling rate experiment failed alteration"
                        if "bad" in self.Data[s]['cooling_rate_data']['CR_correction_factor_flag']:
                            WARNING = WARNING + ";" + "cooling rate experiment failed"

            if AC_correction_type == "-":
                AC_correction_factor_to_print = "-"
            else:
                AC_correction_factor_to_print = "%.2f" % AC_correction_factor

            String = "%s\t%s\t%s\t%s\t%s\t%s\t%.1f\t%.1f\t%.1f\t%s\n"\
                % (sample, s, AC_correction_factor_to_print, AC_correction_type, NLT_factor, CR_factor, B_lab, B_min, B_max, WARNING)
            Fout_specimens_bounds.write(String)

        #--------------------------------------------------------------
        # Find the STDEV-OPT 'best mean':
        # the interprettaions that give
        # the minimum standrad deviation (perc!)
        # not nesseserily the standrad deviation in microT
        #
        #--------------------------------------------------------------

        # Sort all grade A interpretation

        samples = list(Grade_A_samples.keys())
        samples.sort()

        sites = list(Grade_A_sites.keys())
        sites.sort()

        #--------------------------------------------------------------
        # thellier-interpreter can work by averaging specimens by sample (default)
        # or by averaging specimens by site
        #--------------------------------------------------------------

        if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
            self.Grade_A_sorted = copy.deepcopy(Grade_A_samples)

        else:
            self.Grade_A_sorted = copy.deepcopy(Grade_A_sites)

        self.clean_workspace()

        samples_or_sites = list(self.Grade_A_sorted.keys())
        samples_or_sites.sort()
        # print Grade_A_sorted
        for sample_or_site in samples_or_sites:
            if len(list(self.Grade_A_sorted[sample_or_site].keys())) == 1:
                specimen = list(self.Grade_A_sorted[sample_or_site].keys())[0]
                self.choose_interpretation_max_frac(All_grade_A_Recs, specimen)
            else:
                self.thellier_interpreter_pars = self.calc_upper_level_mean(
                    self.Grade_A_sorted, All_grade_A_Recs, sample_or_site)
                self.update_data_with_interpreter_pars(
                    self.Grade_A_sorted, All_grade_A_Recs, sample_or_site, self.thellier_interpreter_pars)
                self.update_files_with_intrepretation(
                    self.Grade_A_sorted, All_grade_A_Recs, sample_or_site, self.thellier_interpreter_pars)
        self.thellier_interpreter_log.write("-I- Statistics:\n")
        self.thellier_interpreter_log.write(
            "-I- number of specimens analzyed = %i\n" % len(specimens_list))
        self.thellier_interpreter_log.write(
            "-I- number of sucsessful 'acceptable' specimens = %i\n" % len(list(All_grade_A_Recs.keys())))

        runtime_sec = time.time() - start_time
        m, s = divmod(runtime_sec, 60)
        h, m = divmod(m, 60)
        self.thellier_interpreter_log.write(
            "-I- runtime hh:mm:ss is " + "%d:%02d:%02d\n" % (h, m, s))
        if len(specimens_list) != 0:
            self.thellier_interpreter_log.write(
                "-I- runtime per specimen: %.1f seconds" % (float(runtime_sec) / len(specimens_list)))

        self.thellier_interpreter_log.write("-I- Finished sucsessfuly.\n")
        self.thellier_interpreter_log.write("-I- DONE\n")

        # close all files

        self.thellier_interpreter_log.close()
        thellier_interpreter_all.close()
        Fout_specimens_bounds.close()
        if self.acceptance_criteria['interpreter_method']['value'] == 'stdev_opt':
            self.Fout_STDEV_OPT_redo.close()
            self.Fout_STDEV_OPT_specimens.close()
        if self.acceptance_criteria['interpreter_method']['value'] == 'stdev_opt':
            if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
                self.Fout_STDEV_OPT_samples.close()
            else:
                self.Fout_STDEV_OPT_sites.close()

        if self.acceptance_criteria['interpreter_method']['value'] == 'bs':
            Fout_BS_samples.close()

        if self.acceptance_criteria['interpreter_method']['value'] == 'bs_par':
            Fout_BS_PAR_samples.close()
        # try:
        #    os.system('\a')
        # except:
        #    pass
        return True, len(specimens_list)

    def update_data_with_interpreter_pars(self, Grade_A_sorted, All_grade_A_Recs, sample_or_site, thellier_interpreter_pars):
        for specimen in list(Grade_A_sorted[sample_or_site].keys()):
            if specimen not in list(thellier_interpreter_pars['stdev_opt_interpretations'].keys()):
                continue
            for TEMP in list(All_grade_A_Recs[specimen].keys()):
                # Best_interpretations[specimen]:
                if All_grade_A_Recs[specimen][TEMP]['specimen_int_uT'] == thellier_interpreter_pars['stdev_opt_interpretations'][specimen]:
                    self.Data[specimen]['pars'].update(
                        All_grade_A_Recs[specimen][TEMP])
                    self.Data[specimen]['pars']['saved'] = True
                    sample = self.Data_hierarchy['specimens'][specimen]
                    if sample not in list(self.Data_samples.keys()):
                        self.Data_samples[sample] = {}
                    if specimen not in list(self.Data_samples[sample].keys()):
                        self.Data_samples[sample][specimen] = {}
                    self.Data_samples[sample][specimen]['B'] = self.Data[specimen]['pars']['specimen_int_uT']
                    site = thellier_gui_lib.get_site_from_hierarchy(
                        sample, self.Data_hierarchy)
                    if site not in list(self.Data_sites.keys()):
                        self.Data_sites[site] = {}
                    if specimen not in list(self.Data_sites.keys()):
                        self.Data_sites[site][specimen] = {}
                    self.Data_sites[site][specimen]['B'] = self.Data[specimen]['pars']['specimen_int_uT']

    def choose_interpretation_max_frac(self, All_grade_A_Recs, specimen):

        #--------------------------------------------------------------
        # if only one specimen pass take the interpretation with maximum frac
        #--------------------------------------------------------------

        frac_max = 0
        for TEMP in list(All_grade_A_Recs[specimen].keys()):
            if All_grade_A_Recs[specimen][TEMP]['specimen_frac'] > frac_max:
                best_intensity = All_grade_A_Recs[specimen][TEMP]['specimen_int_uT']
        for TEMP in list(All_grade_A_Recs[specimen].keys()):
            if All_grade_A_Recs[specimen][TEMP]['specimen_int_uT'] == best_intensity:
                self.Data[specimen]['pars'].update(
                    All_grade_A_Recs[specimen][TEMP])
                self.Data[specimen]['pars']['saved'] = True
                sample = self.Data_hierarchy['specimens'][specimen]
                if sample not in list(self.Data_samples.keys()):
                    self.Data_samples[sample] = {}
                if specimen not in list(self.Data_samples[sample].keys()):
                    self.Data_samples[sample][specimen] = {}

                self.Data_samples[sample][specimen]['B'] = self.Data[specimen]['pars']['specimen_int_uT']

                site = thellier_gui_lib.get_site_from_hierarchy(
                    sample, self.Data_hierarchy)
                if site not in list(self.Data_sites.keys()):
                    self.Data_sites[site] = {}
                if specimen not in list(self.Data_sites[site].keys()):
                    self.Data_sites[site][specimen] = {}
                self.Data_sites[site][specimen]['B'] = self.Data[specimen]['pars']['specimen_int_uT']

    def clean_workspace(self):

        #--------------------------------------------------------------
        # clean workspace: delete all previous interpretation
        #--------------------------------------------------------------

        for sp in list(self.Data.keys()):
            del self.Data[sp]['pars']
            self.Data[sp]['pars'] = {}
            self.Data[sp]['pars']['lab_dc_field'] = self.Data[sp]['lab_dc_field']
            self.Data[sp]['pars']['er_specimen_name'] = self.Data[sp]['er_specimen_name']
            self.Data[sp]['pars']['er_sample_name'] = self.Data[sp]['er_sample_name']
        self.Data_samples = {}
        self.Data_sites = {}

    def calc_upper_level_mean(self, Grade_A_sorted, All_grade_A_Recs, sample_or_site):

            #--------------------------------------------------------------
            # Grade_A_sorted ={}
            # if averaging by sample:
            # Grade_A_sorted[sample][s]=[B1,B2,B3...]
            # if averaging by sites:
            # Grade_A_sorted[site][s]=[B1,B2,B3...]
            #--------------------------------------------------------------

            #--------------------------------------------------------------
            # check for anisotropy issue:
            # If the average anisotropy correction in the sample is larger than a threshold value
            # and there are enough good specimens with anisotropy correction to pass sample's criteria
            # then dont use the uncorrected specimens for sample's calculation.
            #--------------------------------------------------------------
        thellier_interpreter_pars = {}
        tmp_Grade_A_sorted = copy.deepcopy(Grade_A_sorted)
        if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
            aniso_mean_cutoff = self.acceptance_criteria['sample_aniso_mean']['value']
        else:
            aniso_mean_cutoff = self.acceptance_criteria['site_aniso_mean']['value']
        if aniso_mean_cutoff != -999:
            if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
                int_n = self.acceptance_criteria['sample_int_n']['value']
            else:
                int_n = self.acceptance_criteria['site_int_n']['value']
            if len(list(tmp_Grade_A_sorted[sample_or_site].keys())) > int_n:
                aniso_corrections = []
                for specimen in list(tmp_Grade_A_sorted[sample_or_site].keys()):
                    AC_correction_factor_1 = 0
                    for k in list(All_grade_A_Recs[specimen].keys()):
                        pars = All_grade_A_Recs[specimen][k]
                        if "AC_anisotropy_type" in list(pars.keys()):
                            if "AC_WARNING" in list(pars.keys()):
                                if "TRM" in pars["AC_WARNING"] and pars["AC_anisotropy_type"] == "ATRM" and "alteration" in pars["AC_WARNING"]:
                                    continue
                                AC_correction_factor_1 = max(
                                    AC_correction_factor_1, 100 * abs(1. - pars["Anisotropy_correction_factor"]))
                    if AC_correction_factor_1 != 0:
                        aniso_corrections.append(AC_correction_factor_1)
                if aniso_corrections != []:
                    self.thellier_interpreter_log.write("sample_or_site %s has anisotropy factor mean of %f\n" % (
                        sample_or_site, mean(aniso_corrections)))
                if mean(aniso_corrections) > aniso_mean_cutoff:
                    self.thellier_interpreter_log.write(
                        "sample_or_site %s has anisotropy factor mean > thershold of %f\n" % (sample_or_site, aniso_mean_cutoff))

                    warning_messeage = ""
                    WARNING_tmp = ""
                    # print "sample %s have anisotropy factor mean of
                    # %f"%(sample,mean(aniso_corrections))
                    for specimen in list(tmp_Grade_A_sorted[sample_or_site].keys()):
                        ignore_specimen = False
                        intenstities = list(All_grade_A_Recs[specimen].keys())
                        pars = All_grade_A_Recs[specimen][intenstities[0]]
                        if "AC_anisotropy_type" not in list(pars.keys()):
                            ignore_specimen = True
                            warning_messeage = warning_messeage + \
                                "-W- WARNING: specimen %s is excluded from sample %s because it doesn't have anisotropy correction, and other specimens are very anisotropic\n" % (
                                    specimen, sample_or_site)
                        elif "AC_WARNING" in list(pars.keys()):
                            # if "alteration check" in pars["AC_WARNING"]:
                            if pars["AC_anisotropy_type"] == "ATRM" and "TRM" in pars["AC_WARNING"] and "alteration" in pars["AC_WARNING"]:
                               # or "ARM" in pars["AC_WARNING"] and
                               # pars["AC_anisotropy_type"]== "AARM":
                                ignore_specimen = True
                                warning_messeage = warning_messeage + \
                                    "-W- WARNING: specimen %s is exluded from sample %s because it failed ATRM alteration check and other specimens are very anistropic\n" % (
                                        specimen, sample_or_site)
                        if ignore_specimen:

                            WARNING_tmp = WARNING_tmp + \
                                "excluding specimen %s; " % (specimen)
                            del tmp_Grade_A_sorted[sample_or_site][specimen]
                    #----------------------------------------------------------
                    # calculate the STDEV-OPT best mean (after possible ignoring of specimens with bad anisotropy)
                    # and check if pass after ignoring problematic anistopry specimens
                    # if pass: delete the problematic specimens from Grade_A_sorted
                    #----------------------------------------------------------

                    thellier_interpreter_pars = self.thellier_interpreter_pars_calc(
                        tmp_Grade_A_sorted[sample_or_site])
                    if thellier_interpreter_pars['pass_or_fail'] == 'pass':
                        # self.Grade_A_sorted[sample_or_site]=copy.deepcopy(tmp_Grade_A_sorted[sample_or_site])
                        Grade_A_sorted[sample_or_site] = copy.deepcopy(
                            tmp_Grade_A_sorted[sample_or_site])
                        WARNING = WARNING_tmp
                        self.thellier_interpreter_log.write(warning_messeage)
                    else:
                        # Grade_A_sorted[sample_or_site]=copy.deepcopy(tmp_Grade_A_sorted[sample_or_site])
                        #WARNING=WARNING_tmp + "sample fail criteria"
                        warning_messeage = warning_messeage + \
                            "-W- WARNING: sample doesnt pass after rejecting specimens with no ansiotropy. The program keeps these specimens\n"
                        self.thellier_interpreter_log.write(warning_messeage)

        #--------------------------------------------------------------
        # check for outlier specimens
        # Outlier check is done only if
        # (1) number of specimen >= acceptance_criteria['sample_int_n_outlier_check']
        # (2) an outlier exists if one (and only one!) specimen has an outlier result defined
        # by:
        # Bmax(specimen_1) < mean[max(specimen_2),max(specimen_3),max(specimen_3)...] - 2*sigma
        # or
        # Bmin(specimen_1) < mean[min(specimen_2),min(specimen_3),min(specimen_3)...] + 2*sigma
        # (3) 2*sigma > 5 microT
        #--------------------------------------------------------------

        WARNING = ""
        # check for outlier specimen
        exclude_specimen = ""
        exclude_specimens_list = []
        if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
            int_n_outlier_check = self.acceptance_criteria['sample_int_n_outlier_check']['value']
        else:
            int_n_outlier_check = self.acceptance_criteria['site_int_n_outlier_check']['value']

        if int_n_outlier_check == -999:
            int_n_outlier_check = 9999

        if len(list(tmp_Grade_A_sorted[sample_or_site].keys())) >= int_n_outlier_check:
            self.thellier_interpreter_log.write(
                "-I- check outlier for sample %s \n" % sample)
            all_specimens = list(tmp_Grade_A_sorted[sample_or_site].keys())
            for specimen in all_specimens:
                B_min_array, B_max_array = [], []
                for specimen_b in all_specimens:
                    if specimen_b == specimen:
                        continue
                    B_min_array.append(
                        min(tmp_Grade_A_sorted[sample_or_site][specimen_b]))
                    B_max_array.append(
                        max(tmp_Grade_A_sorted[sample_or_site][specimen_b]))
                # and 2*std(B_min_array,ddof=1) >3.:
                if max(tmp_Grade_A_sorted[sample_or_site][specimen]) < (mean(B_min_array) - 2 * std(B_min_array, ddof=1)):
                    if specimen not in exclude_specimens_list:
                        exclude_specimens_list.append(specimen)
                # and 2*std(B_max_array,ddof=1) >3 :
                if min(tmp_Grade_A_sorted[sample_or_site][specimen]) > (mean(B_max_array) + 2 * std(B_max_array, ddof=1)):
                    if specimen not in exclude_specimens_list:
                        exclude_specimens_list.append(specimen)

            if len(exclude_specimens_list) > 1:
                self.thellier_interpreter_log.write("-I- specimen %s outlier check: more than one specimen can be outlier. first ones are : %s,%s... \n" % (
                    sample, exclude_specimens_list[0], exclude_specimens_list[1]))
                exclude_specimens_list = []

            if len(exclude_specimens_list) == 1:
                # print exclude_specimens_list
                exclude_specimen = exclude_specimens_list[0]
                del tmp_Grade_A_sorted[sample_or_site][exclude_specimen]
                self.thellier_interpreter_log.write(
                    "-W- WARNING: specimen %s is exluded from sample %s because of an outlier result.\n" % (exclude_specimens_list[0], sample))
                WARNING = WARNING + \
                    "excluding specimen %s; " % (exclude_specimens_list[0])

        # if len(tmp_Grade_A_sorted[sample_or_site])>1:
        #    Grade_A_sorted[sample_or_site]=copy.deepcopy(tmp_Grade_A_sorted[sample_or_site])
        # else:
        #    Grade_A_sorted[sample_or_site]={}

        #--------------------------------------------------------------
        # calculate STDEV
        #--------------------------------------------------------------
        if self.acceptance_criteria['interpreter_method']['value'] == 'stdev_opt':
            thellier_interpreter_pars = self.thellier_interpreter_pars_calc(
                Grade_A_sorted[sample_or_site])
          # Best_interpretations,best_mean,best_std=self.find_sample_min_std(Grade_A_sorted[sample_or_site])
            # return( thellier_interpreter_pars)
        # else:
        #    self.thellier_interpreter_pars={}

        #--------------------------------------------------------------
        # calculate Bootstrap
        #--------------------------------------------------------------

        if self.acceptance_criteria['interpreter_method']['value'] == 'bs' or self.acceptance_criteria['interpreter_method']['value'] == 'bs_par':
            thellier_interpreter_pars = self.thellier_interpreter_BS_pars_calc(
                self, Grade_A_sorted[sample_or_site])
            # return(self.thellier_interpreter_pars)
        return(thellier_interpreter_pars)

    def update_files_with_intrepretation(self, Grade_A_sorted, All_grade_A_Recs, sample_or_site, thellier_interpreter_pars):

        #--------------------------------------------------------------
        # check if ATRM and cooling rate data exist
        #--------------------------------------------------------------
        WARNING = ""
        if self.acceptance_criteria['interpreter_method']['value'] == 'stdev_opt':
            n_anistropy = 0
            n_anistropy_fail = 0
            n_anistropy_pass = 0
            for specimen in list(Grade_A_sorted[sample_or_site].keys()):
                if "AniSpec" in list(self.Data[specimen].keys()):
                    n_anistropy += 1
                    if 'pars' in list(self.Data[specimen].keys()) and "AC_WARNING" in list(self.Data[specimen]['pars'].keys()):
                        if self.Data[specimen]['pars']["AC_anisotropy_type"] == 'ATRM' and "alteration" in self.Data[specimen]['pars']["AC_WARNING"]:
                            n_anistropy_fail += 1
                        else:
                            n_anistropy_pass += 1
            no_cooling_rate = True
            n_cooling_rate = 0
            n_cooling_rate_pass = 0
            n_cooling_rate_fail = 0

            for specimen in list(Grade_A_sorted[sample_or_site].keys()):
                if "cooling_rate_data" in list(self.Data[specimen].keys()):
                    n_cooling_rate += 1
                    if "CR_correction_factor" in list(self.Data[specimen]["cooling_rate_data"].keys()):
                        if self.Data[specimen]["cooling_rate_data"]["CR_correction_factor"] != -1 and self.Data[specimen]["cooling_rate_data"]["CR_correction_factor"] != -999:
                            no_cooling_rate = False
                        if 'CR_correction_factor_flag' in list(self.Data[specimen]["cooling_rate_data"].keys()):
                            if 'calculated' in self.Data[specimen]['cooling_rate_data']['CR_correction_factor_flag']:
                                n_cooling_rate_pass += 1
                            elif 'failed' in self.Data[specimen]['cooling_rate_data']['CR_correction_factor_flag']:
                                n_cooling_rate_fail += 1

            if len(list(Grade_A_sorted[sample_or_site].keys())) > 1 and "int_n" not in thellier_interpreter_pars['fail_criteria']:
                TEXT = "-I- sample %s 'STDEV-OPT interpretation: " % sample_or_site
                for ss in list(thellier_interpreter_pars['stdev_opt_interpretations'].keys()):
                    TEXT = TEXT + \
                        "%s=%.1f, " % (
                            ss, thellier_interpreter_pars['stdev_opt_interpretations'][ss])
                self.thellier_interpreter_log.write(TEXT + "\n")
                self.thellier_interpreter_log.write("-I- sample %s STDEV-OPT mean=%f, STDEV-OPT std=%f \n" % (
                    sample_or_site, thellier_interpreter_pars['stdev-opt']['B'], thellier_interpreter_pars['stdev-opt']['std']))
                self.thellier_interpreter_log.write("-I- sample %s STDEV-OPT minimum/maximum accepted interpretation  %.2f,%.2f\n" % (
                    sample_or_site, thellier_interpreter_pars['min-value']['B'], thellier_interpreter_pars['max-value']['B']))

                # check if interpretation pass criteria for samples:
                if thellier_interpreter_pars['pass_or_fail'] == 'pass':
                    # write the interpretation to a redo file
                    for specimen in list(Grade_A_sorted[sample_or_site].keys()):
                        # print Redo_data_specimens[specimen]
                        for TEMP in list(All_grade_A_Recs[specimen].keys()):
                            if All_grade_A_Recs[specimen][TEMP]['specimen_int_uT'] == thellier_interpreter_pars['stdev_opt_interpretations'][specimen]:
                                t_min = All_grade_A_Recs[specimen][TEMP]['measurement_step_min']
                                t_max = All_grade_A_Recs[specimen][TEMP]['measurement_step_max']

                                self.Fout_STDEV_OPT_redo.write(
                                    "%s\t%i\t%i\n" % (specimen, t_min, t_max))

                            # write the interpretation to the specimen file
                                B_lab = float(
                                    All_grade_A_Recs[specimen][TEMP]['lab_dc_field']) * 1e6
                                sample = All_grade_A_Recs[specimen][TEMP]['er_sample_name']
                                if "Anisotropy_correction_factor" in list(All_grade_A_Recs[specimen][TEMP].keys()):
                                    Anisotropy_correction_factor = "%.2f" % (
                                        All_grade_A_Recs[specimen][TEMP]["Anisotropy_correction_factor"])
                                    # AC_correction_type=pars["AC_anisotropy_type"]
                                # if 'AC_specimen_correction_factor' in All_grade_A_Recs[specimen][TEMP].keys():
                                #    Anisotropy_correction_factor="%.2f"%float(All_grade_A_Recs[specimen][TEMP]['AC_specimen_correction_factor'])
                                else:
                                    Anisotropy_correction_factor = "-"
                                if All_grade_A_Recs[specimen][TEMP]["NLT_specimen_correction_factor"] != -1:
                                    NLT_correction_factor = "%.2f" % float(
                                        All_grade_A_Recs[specimen][TEMP]['NLT_specimen_correction_factor'])
                                else:
                                    NLT_correction_factor = "-"

                                if All_grade_A_Recs[specimen][TEMP]["specimen_int_corr_cooling_rate"] != -999 and All_grade_A_Recs[specimen][TEMP]["specimen_int_corr_cooling_rate"] != -1:
                                    CR_correction_factor = "%.2f" % float(
                                        All_grade_A_Recs[specimen][TEMP]['specimen_int_corr_cooling_rate'])
                                else:
                                    CR_correction_factor = "-"

                                self.Fout_STDEV_OPT_specimens.write("%s\t%s\t%.2f\t%i\t%i\t%.0f\t%s\t%s\t%s\t"
                                                                    % (sample_or_site, specimen, float(thellier_interpreter_pars['stdev_opt_interpretations'][specimen]), t_min - 273, t_max - 273, B_lab, Anisotropy_correction_factor, NLT_correction_factor, CR_correction_factor))
                                String = ""
                                for key in self.specimen_criteria:
                                    if type(All_grade_A_Recs[specimen][TEMP][key]) == str:
                                        String = String + \
                                            All_grade_A_Recs[specimen][TEMP][key] + "\t"
                                    else:
                                        String = String + \
                                            "%.2f" % (
                                                All_grade_A_Recs[specimen][TEMP][key]) + "\t"
                                self.Fout_STDEV_OPT_specimens.write(
                                    String[:-1] + "\n")

                    # write the interpretation to the sample file

                    if n_anistropy == 0:
                        WARNING = WARNING + "No anisotropy corrections; "
                    else:
                        WARNING = WARNING + "%i / %i specimens pass anisotropy criteria; " % (
                            int(n_anistropy) - int(n_anistropy_fail), int(n_anistropy))

                    if no_cooling_rate:
                        WARNING = WARNING + " No cooling rate corrections; "
                    else:
                        WARNING = WARNING + "%i / %i specimens pass cooling rate criteria ;" % (
                            int(n_cooling_rate_pass), int(n_cooling_rate))

                    String = "%s\t%i\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.3f\t%.2f\t%.2f\t%s\n" %\
                        (sample_or_site, len(thellier_interpreter_pars['stdev_opt_interpretations']),
                         thellier_interpreter_pars['stdev-opt']['B'],
                         thellier_interpreter_pars['stdev-opt']['std'],
                         thellier_interpreter_pars['stdev-opt']['std_perc'],
                         thellier_interpreter_pars['min-value']['B'],
                         thellier_interpreter_pars['min-value']['std'],
                         thellier_interpreter_pars['max-value']['B'],
                         thellier_interpreter_pars['max-value']['std'],
                         thellier_interpreter_pars['sample_int_interval_uT'],
                         thellier_interpreter_pars['sample_int_interval_perc'],
                         WARNING)
                    if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
                        self.Fout_STDEV_OPT_samples.write(String)
                    else:
                        self.Fout_STDEV_OPT_sites.write(String)

                else:
                    self.thellier_interpreter_log.write("-I- sample %s FAIL on %s\n" % (
                        sample_or_site, ":".join(thellier_interpreter_pars['fail_criteria'])))

        #--------------------------------------------------------------
        #  calcuate Bootstarp and write results to files
        #--------------------------------------------------------------
        if self.acceptance_criteria['interpreter_method']['value'] == 'bs' or self.acceptance_criteria['interpreter_method']['value'] == 'bs_par':

            if self.acceptance_criteria['interpreter_method']['value'] == 'bs':
                results_file = Fout_BS_samples
            if self.acceptance_criteria['interpreter_method']['value'] == 'bs_par':
                results_file = Fout_BS_PAR_samples
            BOOTSTRAP_N = int(self.preferences['BOOTSTRAP_N'])

            String = "-I- caclulating bootstrap statistics for sample %s (N=%i)" % (
                sample, int(BOOTSTRAP_N))
            self.thellier_interpreter_log.write(String)

            sample, sample_median, sample_std = sample_or_site
            sample_median = thellier_interpreter_pars['bs_bedian']
            sample_std = thellier_interpreter_pars['bs_bedian']
            sample_68 = thellier_interpreter_pars['bs_68']
            sample_95 = thellier_interpreter_pars['bs_95']
            sample_n = thellier_interpreter_pars['bs_n']
            # WARNING=thellier_interpreter_pars['bs_n']

            thellier_interpreter_log.write(
                "-I- bootstrap mean sample %s: median=%f, std=%f\n" % (sample, sample_median, sample_std))
            String = "%s\t%i\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%s\n" %\
                (sample, sample_n, sample_median, sample_68[0], sample_68[1], sample_95[0],
                 sample_95[1], sample_std, 100 * (sample_std / sample_median), WARNING)
            results_file.write(String)

    def find_close_value(self, LIST, value):
        '''
        take a LIST and find the nearest value in LIST to 'value'
        '''
        diff = inf
        for a in LIST:
            if abs(value - a) < diff:
                diff = abs(value - a)
                result = a
        return(result)

    def find_sample_min_std(self, Intensities):
        '''
        find the best interpretation with the minimum stratard deviation (in units of percent % !)
        '''

        Best_array = []
        best_array_std_perc = inf
        Best_array_tmp = []
        Best_interpretations = {}
        Best_interpretations_tmp = {}
        for this_specimen in list(Intensities.keys()):
            for value in Intensities[this_specimen]:
                Best_interpretations_tmp[this_specimen] = value
                Best_array_tmp = [value]
                all_other_specimens = list(Intensities.keys())
                all_other_specimens.remove(this_specimen)

                for other_specimen in all_other_specimens:
                    closest_value = self.find_close_value(
                        Intensities[other_specimen], value)
                    Best_array_tmp.append(closest_value)
                    Best_interpretations_tmp[other_specimen] = closest_value

                if std(Best_array_tmp, ddof=1) / mean(Best_array_tmp) < best_array_std_perc:
                    Best_array = Best_array_tmp
                    best_array_std_perc = std(
                        Best_array, ddof=1) / mean(Best_array_tmp)
                    Best_interpretations = copy.deepcopy(
                        Best_interpretations_tmp)
                    Best_interpretations_tmp = {}
        return Best_interpretations, mean(Best_array), std(Best_array, ddof=1)

    def pass_or_fail_sigma(self, B, int_sigma_cutoff, int_sigma_perc_cutoff):
        # pass_or_fail='fail'
        B_mean = mean(B)
        B_sigma = std(B, ddof=1)
        B_sigma_perc = 100 * (B_sigma / B_mean)

        if int_sigma_cutoff == -999 and int_sigma_perc_cutoff == -999:
            return('pass')
        if B_sigma <= int_sigma_cutoff * 1e6 and int_sigma_cutoff != -999:
            pass_sigma = True
        else:
            pass_sigma = False
        if B_sigma_perc <= int_sigma_perc_cutoff and int_sigma_perc_cutoff != -999:
            pass_sigma_perc = True
        else:
            pass_sigma_perc = False
        if pass_sigma or pass_sigma_perc:
            return('pass')
        else:
            return('fail')

    def find_sample_min_max_interpretation(self, Intensities):
        '''
        find the minimum and maximum acceptable sample mean
        Intensities={}
        Intensities[specimen_name]=[] array of acceptable interpretations ( units of uT)
        '''
        # acceptance criteria
        if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
            int_n_cutoff = self.acceptance_criteria['sample_int_n']['value']
            int_sigma_cutoff = self.acceptance_criteria['sample_int_sigma']['value']
            int_sigma_perc_cutoff = self.acceptance_criteria['sample_int_sigma_perc']['value']
        else:
            int_n_cutoff = self.acceptance_criteria['site_int_n']['value']
            int_sigma_cutoff = self.acceptance_criteria['site_int_sigma']['value']
            int_sigma_perc_cutoff = self.acceptance_criteria['site_int_sigma_perc']['value']
        if int_n_cutoff == -999:
            int_n_cutoff = 2
        # if int_sigma_cutoff==-999:
        #    int_sigma_cutoff=999
        # if int_sigma_perc_cutoff==-999:
        #    int_sigma_perc_cutoff=999

        # make a new dictionary named "tmp_Intensities" with all grade A
        # interpretation sorted.
        tmp_Intensities = {}
        Acceptable_sample_min_mean, Acceptable_sample_max_mean = "", ""
        for this_specimen in list(Intensities.keys()):
            B_list = [B for B in Intensities[this_specimen]]
            if len(B_list) > 0:
                B_list.sort()
                tmp_Intensities[this_specimen] = B_list

        # find the minmum acceptable values
        while len(list(tmp_Intensities.keys())) >= int_n_cutoff:
            B_tmp = []
            B_tmp_min = 1e10
            for specimen in list(tmp_Intensities.keys()):
                B_tmp.append(min(tmp_Intensities[specimen]))
                if min(tmp_Intensities[specimen]) < B_tmp_min:
                    specimen_to_remove = specimen
                    B_tmp_min = min(tmp_Intensities[specimen])
            pass_or_fail = self.pass_or_fail_sigma(
                B_tmp, int_sigma_cutoff, int_sigma_perc_cutoff)
            if pass_or_fail == 'pass':
                Acceptable_sample_min_mean = mean(B_tmp)
                Acceptable_sample_min_std = std(B_tmp, ddof=1)
                # print "min
                # value,std,",mean(B_tmp),std(B_tmp),100*(std(B_tmp)/mean(B_tmp))
                break
            else:
                tmp_Intensities[specimen_to_remove].remove(B_tmp_min)
                if len(tmp_Intensities[specimen_to_remove]) == 0:
                    break

        tmp_Intensities = {}
        for this_specimen in list(Intensities.keys()):
            B_list = [B for B in Intensities[this_specimen]]
            if len(B_list) > 0:
                B_list.sort()
                tmp_Intensities[this_specimen] = B_list

        while len(list(tmp_Intensities.keys())) >= int_n_cutoff:
            B_tmp = []
            B_tmp_max = 0
            for specimen in list(tmp_Intensities.keys()):
                B_tmp.append(max(tmp_Intensities[specimen]))
                if max(tmp_Intensities[specimen]) > B_tmp_max:
                    specimen_to_remove = specimen
                    B_tmp_max = max(tmp_Intensities[specimen])

            pass_or_fail = self.pass_or_fail_sigma(
                B_tmp, int_sigma_cutoff, int_sigma_perc_cutoff)
            if pass_or_fail == 'pass':
                # if std(B_tmp,ddof=1)<=int_sigma_cutoff*1e6 or
                # 100*(std(B_tmp,ddof=1)/mean(B_tmp))<=int_sigma_perc_cutoff:
                Acceptable_sample_max_mean = mean(B_tmp)
                Acceptable_sample_max_std = std(B_tmp, ddof=1)
                # print "max
                # value,std,",mean(B_tmp),std(B_tmp),100*(std(B_tmp)/mean(B_tmp))

                break
            else:
                tmp_Intensities[specimen_to_remove].remove(B_tmp_max)
                if len(tmp_Intensities[specimen_to_remove]) < 1:
                    break

        if Acceptable_sample_min_mean == "" or Acceptable_sample_max_mean == "":
            return(0., 0., 0., 0.)
        return(Acceptable_sample_min_mean, Acceptable_sample_min_std, Acceptable_sample_max_mean, Acceptable_sample_max_std)

        ############
        # End function definitions
        ############

    def thellier_interpreter_pars_calc(self, Grade_As):
        '''
        calcualte sample or site STDEV-OPT paleointensities
        and statistics
        Grade_As={}

        '''
        thellier_interpreter_pars = {}
        thellier_interpreter_pars['stdev-opt'] = {}
        # thellier_interpreter_pars['stdev-opt']['B']=
        # thellier_interpreter_pars['stdev-opt']['std']=
        thellier_interpreter_pars['min-value'] = {}
        # thellier_interpreter_pars['min-value']['B']=
        # thellier_interpreter_pars['min-value']['std']=
        thellier_interpreter_pars['max-value'] = {}
        # thellier_interpreter_pars['max-value']['B']=
        # thellier_interpreter_pars['max-value']['std']=
        thellier_interpreter_pars['fail_criteria'] = []
        thellier_interpreter_pars['pass_or_fail'] = 'pass'

        # acceptance criteria
        if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
            int_n_cutoff = self.acceptance_criteria['sample_int_n']['value']
            int_sigma_cutoff = self.acceptance_criteria['sample_int_sigma']['value']
            int_sigma_perc_cutoff = self.acceptance_criteria['sample_int_sigma_perc']['value']
            int_interval_cutoff = self.acceptance_criteria['sample_int_interval_uT']['value']
            int_interval_perc_cutoff = self.acceptance_criteria['sample_int_interval_perc']['value']
        else:
            int_n_cutoff = self.acceptance_criteria['site_int_n']['value']
            int_sigma_cutoff = self.acceptance_criteria['site_int_sigma']['value']
            int_sigma_perc_cutoff = self.acceptance_criteria['site_int_sigma_perc']['value']
            int_interval_cutoff = self.acceptance_criteria['site_int_interval_uT']['value']
            int_interval_perc_cutoff = self.acceptance_criteria['site_int_interval_perc']['value']

        N = len(list(Grade_As.keys()))
        if N <= 1:
            thellier_interpreter_pars['pass_or_fail'] = 'fail'
            thellier_interpreter_pars['fail_criteria'].append("int_n")
            return(thellier_interpreter_pars)

        Best_interpretations, best_mean, best_std = self.find_sample_min_std(
            Grade_As)
        sample_acceptable_min, sample_acceptable_min_std, sample_acceptable_max, sample_acceptable_max_std = self.find_sample_min_max_interpretation(
            Grade_As)
        sample_int_interval_uT = sample_acceptable_max - sample_acceptable_min
        sample_int_interval_perc = 100 * \
            ((sample_acceptable_max - sample_acceptable_min) / best_mean)
        thellier_interpreter_pars['stdev_opt_interpretations'] = Best_interpretations
        thellier_interpreter_pars['stdev-opt']['B'] = best_mean
        thellier_interpreter_pars['stdev-opt']['std'] = best_std
        thellier_interpreter_pars['stdev-opt']['std_perc'] = 100. * \
            (best_std / best_mean)
        thellier_interpreter_pars['min-value']['B'] = sample_acceptable_min
        thellier_interpreter_pars['min-value']['std'] = sample_acceptable_min_std
        thellier_interpreter_pars['max-value']['B'] = sample_acceptable_max
        thellier_interpreter_pars['max-value']['std'] = sample_acceptable_max_std
        thellier_interpreter_pars['sample_int_interval_uT'] = sample_int_interval_uT
        thellier_interpreter_pars['sample_int_interval_perc'] = sample_int_interval_perc

        if N < int_n_cutoff:
            thellier_interpreter_pars['pass_or_fail'] = 'fail'
            thellier_interpreter_pars['fail_criteria'].append("int_n")

        pass_int_sigma, pass_int_sigma_perc = True, True
        pass_int_interval, pass_int_interval_perc = True, True

        if not (int_sigma_cutoff == -999 and int_sigma_perc_cutoff == -999):
            if best_std <= int_sigma_cutoff * 1e6 and int_sigma_cutoff != -999:
                pass_sigma = True
            else:
                pass_sigma = False
            if 100. * (best_std / best_mean) <= int_sigma_perc_cutoff and int_sigma_perc_cutoff != -999:
                pass_sigma_perc = True
            else:
                pass_sigma_perc = False
            if not (pass_sigma or pass_sigma_perc):
                thellier_interpreter_pars['pass_or_fail'] = 'fail'
                thellier_interpreter_pars['fail_criteria'].append("int_sigma")

        if not (int_interval_cutoff == -999 and int_interval_perc_cutoff == -999):
            if sample_int_interval_uT <= int_interval_perc_cutoff and int_interval_perc_cutoff != -999:
                pass_interval = True
            else:
                pass_interval = False
            if sample_int_interval_perc <= int_interval_perc_cutoff and int_interval_perc_cutoff != -999:
                pass_interval_perc = True
            else:
                pass_interval_perc = False
            if not (pass_interval or pass_interval_perc):
                thellier_interpreter_pars['pass_or_fail'] = 'fail'
                thellier_interpreter_pars['fail_criteria'].append(
                    "int_interval")

        return(thellier_interpreter_pars)

    def thellier_interpreter_BS_pars_calc(self, Grade_As):
        '''
        calcualte sample or site bootstrap paleointensities
        and statistics
        Grade_As={}
        '''
        thellier_interpreter_pars = {}
        thellier_interpreter_pars['fail_criteria'] = []
        thellier_interpreter_pars['pass_or_fail'] = 'pass'

        BOOTSTRAP_N = int(self.preferences['BOOTSTRAP_N'])
        Grade_A_samples_BS = {}
        if len(list(Grade_As.keys())) >= self.acceptance_criteria['sample_int_n']['value']:
            for specimen in list(Grade_As.keys()):
                if specimen not in list(Grade_A_samples_BS.keys()) and len(Grade_As[specimen]) > 0:
                    Grade_A_samples_BS[specimen] = []
                for B in Grade_As[specimen]:
                    Grade_A_samples_BS[specimen].append(B)
                Grade_A_samples_BS[specimen].sort()
                specimen_int_max_slope_diff = max(
                    Grade_A_samples_BS[specimen]) / min(Grade_A_samples_BS[specimen])
                if specimen_int_max_slope_diff > self.acceptance_criteria['specimen_int_max_slope_diff']:
                    self.thellier_interpreter_log.write(
                        "-I- specimen %s Failed specimen_int_max_slope_diff\n" % specimen, Grade_A_samples_BS[specimen])
                    del Grade_A_samples_BS[specimen]

        if len(list(Grade_A_samples_BS.keys())) >= self.acceptance_criteria['sample_int_n']['value']:
            BS_means_collection = []
            for i in range(BOOTSTRAP_N):
                B_BS = []
                for j in range(len(list(Grade_A_samples_BS.keys()))):
                    LIST = list(Grade_A_samples_BS.keys())
                    specimen = random.choice(LIST)
                    if self.acceptance_criteria['interpreter_method']['value'] == 'bs':
                        B = random.choice(Grade_A_samples_BS[specimen])
                    if self.acceptance_criteria['interpreter_method']['value'] == 'bs_par':
                        B = random.uniform(min(Grade_A_samples_BS[specimen]), max(
                            Grade_A_samples_BS[specimen]))
                    B_BS.append(B)
                BS_means_collection.append(mean(B_BS))

            BS_means = array(BS_means_collection)
            BS_means.sort()
            sample_median = median(BS_means)
            sample_std = std(BS_means, ddof=1)
            sample_68 = [BS_means[(0.16) * len(BS_means)],
                         BS_means[(0.84) * len(BS_means)]]
            sample_95 = [BS_means[(0.025) * len(BS_means)],
                         BS_means[(0.975) * len(BS_means)]]

        else:
            String = "-I- sample %s FAIL: not enough specimen int_n= %i < %i " % (sample, len(
                list(Grade_A_samples_BS.keys())), int(self.acceptance_criteria['sample_int_n']['value']))
            # print String
            self.thellier_interpreter_log.write(String)

        thellier_interpreter_pars['bs_bedian'] = sample_median
        thellier_interpreter_pars['bs_std'] = sample_std
        thellier_interpreter_pars['bs_68'] = sample_68
        thellier_interpreter_pars['bs_95'] = sample_95
        thellier_interpreter_pars['bs_n'] = len(
            list(Grade_A_samples_BS.keys()))
