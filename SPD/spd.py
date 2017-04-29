#!/usr/bin/env python

#============================================================================================
# LOG HEADER:
#============================================================================================
#
#
#
#
#-------------------------
#
# Author: Lori Jonestrask / Ron Shaar
#
# Initial revision: September 2013:
#
#============================================================================================

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from builtins import object
from past.utils import old_div
import sys
import numpy
import os
#import pylab
#import scipy
#from scipy import *
#import os
import SPD.lib.lib_arai_plot_statistics as lib_arai
#import SPD.lib.lib_curvature as lib_k
import SPD.lib.leastsq_jacobian as lib_k
import SPD.lib.lib_directional_statistics as lib_direct
import SPD.lib.lib_ptrm_statistics as lib_ptrm
import SPD.lib.lib_tail_check_statistics as lib_tail
import SPD.lib.lib_additivity_check_statistics as lib_add
from pmagpy.mapping import map_magic


# Data{} is a dictionary sorted by specimen name
# i.e. Data[specine_a]={} ; Data[specine_b]={} etc.
# Each specimen data is sorted to the following "blocks":

# Arai plot:
# Data[s]['x_Arai']=[] # a list of x_i
# Data[s]['y_Arai']=[] # a list of y_i
# Data[s]['t_Arai']=[] # a list of temperatures (C? K?)
# Data[s]'steps_Arai']=[] a list of the "ZI/IZ" steps (IZ= blue ZI=red). i.e. ['ZI','IZ','ZI']

# NRMS  # temp K, dec, inc, moment, 0 or 1 (ZI=1, IZ=0)  # needs to convert to cartesian for vector operations
# PTRMS  # temp K, dec, inc, moment, 0 or 1 (ZI=1, IZ=0)

#PTRM_Checks # same same

# pTRM checks ("triangles")
#         Data[s]['x_ptrm_check']=[] # a list of x coordinates of pTRM checks
#         Data[s]['y_ptrm_check']=[] # a list of y coordinates of pTRM checks
#         Data[s]['ptrm_checks_temperatures']=[] # a list of pTRM checks temperature
#         Data[s]['x_ptrm_check_starting_point'] # a list of x coordinates of the point ehere the pTRM checks started from
#         Data[s]['y_ptrm_check_starting_point'] # a list of y coordinates of the point ehere the pTRM checks started from
#         Data[s]['ptrm_checks_starting_temperatures']=[] # a list of temperatures from which the pTRM checks started from


# pTRM tail checks ("squares")
#        Data[s]['x_tail_check']
#        Data[s]['y_tail_check']
#        Data[s]['tail_check_temperatures']
#        Data[s]['x_tail_check_starting_point']
#        Data[s]['y_tail_check_starting_point']
#        Data[s]['tail_checks_starting_temperatures']


# Zijderveld plot

# Data[s]['zijdblock']=[ [], [], []] # a list of:
#                   [treatment,declination,inclination,intensity,ZI,measurement_flag,magic_instrument_codes]
#                    treatment: temperature steps
#
# Data[s]['zij_rotated']=[[x,y,z], [x,y,z] ,[x,y,z] ]: a list of the x,y,z coordinates of the rotated Zijderveld plot
#                                                      the rotated zijderveld plot is what is plotted in Thellier Gui.
# Data[s]['zdata'] -- same as zij_rotated, but not rotated



class PintPars(object):
    """ __init__(self, Data,specimen_name,tmin,tmax,mapping=None, calculate=None)"""
    def __init__(self, Data, specimen_name, tmin, tmax, mapping=None, calculate=None,acceptance_criteria={}):
        self.acceptance_criteria=acceptance_criteria
        self.s = specimen_name
        self.mapping = mapping
        ####
        if calculate:
            self.calculate = []
            for stat in calculate:
                try:
                    ind = map_magic.magic.index('specimen_' + stat)
                    new_stat = map_magic.spd[ind]
                    self.calculate.append(new_stat)
                except ValueError:
                    print("doesn't start with 'specimen'", stat)
                    #self.calculate.append(stat)
        ####
        self.specimen_Data = Data[self.s]
        self.datablock = self.specimen_Data['datablock']

        self.x_Arai = self.specimen_Data['x_Arai']
        self.y_Arai = self.specimen_Data['y_Arai']
        self.t_Arai = self.specimen_Data['t_Arai']

        self.zdata = self.specimen_Data['zdata']

        self.x_tail_check=self.specimen_Data['x_tail_check']
        self.y_tail_check=self.specimen_Data['y_tail_check']
        self.tail_checks_temperatures = self.specimen_Data['tail_check_temperatures']
#        self.x_tail_check_starting_point = self.specimen_Data['x_tail_check_starting_point']
#        self.y_tail_check_starting_point = self.specimen_Data['y_tail_check_starting_point']
        self.tail_checks_starting_temperatures = self.specimen_Data['tail_checks_starting_temperatures']

# pTRM checks ("triangles")
        self.x_ptrm_check = self.specimen_Data['x_ptrm_check'] # a list of x coordinates of pTRM checks
        self.y_ptrm_check = self.specimen_Data['y_ptrm_check'] # a list of y coordinates of pTRM checks
        self.ptrm_checks_temperatures= self.specimen_Data['ptrm_checks_temperatures'] # a list of pTRM checks temperature
#        Data[s]['x_ptrm_check_starting_point'] # a list of x coordinates of the point ehere the pTRM checks started from
#         Data[s]['y_ptrm_check_starting_point'] # a list of y coordinates of the point ehere the pTRM checks started from
        self.ptrm_checks_starting_temperatures = self.specimen_Data['ptrm_checks_starting_temperatures'] # a list of temperatures from which the pTRM checks started from

        # AC checks
        self.x_add_check = self.specimen_Data['x_additivity_check']
        self.y_add_check = self.specimen_Data['y_additivity_check']
        self.add_checks_temperatures = self.specimen_Data['additivity_check_temperatures']
        self.add_checks_starting_temperatures = self.specimen_Data['additivity_check_starting_temperatures']
        self.x_add_check_starting_point = self.specimen_Data['x_additivity_check_starting_point']
        self.y_add_check_starting_point = self.specimen_Data['y_additivity_check_starting_point']

        # Data in Temp/Dec/Inc/Int format
        self.PTRMS = self.specimen_Data['PTRMS']
        self.NRMS = self.specimen_Data['NRMS']
        self.NRM = self.specimen_Data['NRM']
        self.PTRM_Checks = self.specimen_Data['PTRM_Checks']
        self.TAIL_Checks = self.specimen_Data['TAIL_Checks']
        self.AC_Diffs = self.specimen_Data['AC']
#        self.ADD_Checks = self.specimen_Data['ADD_Checks'] # removed this from new_lj_thellier_gui

        self.zijdblock=self.specimen_Data['zijdblock']
        self.z_temperatures=self.specimen_Data['z_temp']

        self.start=self.t_Arai.index(tmin)
        self.end=self.t_Arai.index(tmax)

        self.pars={}

        self.pars['specimen_lab_dc_field'] = self.specimen_Data['pars']['lab_dc_field']
 #       self.pars['specimen_lab_ac_field'] = self.specimen_Data['pars']['lab_ac_field']
        self.B_lab_dir = [self.specimen_Data['Thellier_dc_field_phi'], self.specimen_Data['Thellier_dc_field_theta'],
                          self.specimen_Data['Thellier_dc_field_uT']]  #
        self.B_lab_cart = lib_direct.dir2cart(self.B_lab_dir)

  #      self.pars['magic_method_codes']=Data[self.s]['pars']['magic_method_codes']
        self.pars['specimen_int_n']=int(self.end-self.start+1)
        self.pars['specimen_n_total']=len(self.x_Arai)


        #LJ ADDING stats:
        self.steps_Arai = self.specimen_Data['steps_Arai']
        self.n = int(self.end-self.start+1)
        self.n_max = len(self.t_Arai)
        self.tmin = tmin
        self.tmax = tmax
        self.tmin_K = tmin - 273.
        self.tmax_K = tmax - 273
        self.x_Arai_segment = self.x_Arai[self.start:self.end+1]
        self.y_Arai_segment = self.y_Arai[self.start:self.end+1]
        self.x_Arai_mean = numpy.mean(self.x_Arai_segment)
        self.y_Arai_mean = numpy.mean(self.y_Arai_segment)
        # try
        self.pars['x_Arai_mean'] = self.x_Arai_mean
        self.pars['y_Arai_mean'] = self.y_Arai_mean
        self.pars['tmin'] = tmin
        self.pars['tmax'] = tmax
        #
        self.xy_Arai = lib_arai.get_xy_array(self.x_Arai, self.y_Arai)
        self.xy_Arai_segment = lib_arai.get_xy_array(self.x_Arai_segment, self.y_Arai_segment)


    def __repr__(self):
        index = (self.t_Arai.index(self.tmin), self.t_Arai.index(self.tmax))
        return "PintPars object, specimen: {}, tmin_K: {}, tmax_K: {}, temperature index: {} ".format(self.s, self.tmin_K, self.tmax_K, index)

    def get_segments_and_means(self):
        pass # consider making this a real deal thing.

    def York_Regression(self):
        if self.n < 3:
            print("-W- Cannot run statistics with only {} points".format(self.n))
            return None
        x_segment, y_segment = self.x_Arai_segment, self.y_Arai_segment
        x_mean, y_mean = self.x_Arai_mean, self.y_Arai_mean
        n = self.n
        lab_dc_field = float(self.pars['specimen_lab_dc_field'])
        steps_Arai = self.specimen_Data['steps_Arai']
        data = lib_arai.York_Regression(x_segment, y_segment, x_mean, y_mean, n, lab_dc_field, steps_Arai)
        self.pars['x_err'] = data['x_err']
        self.pars['y_err'] = data['y_err']
        self.pars['x_tag'] = data['x_tag']
        self.pars['y_tag'] = data['y_tag']
        self.pars['specimen_b'] = data['specimen_b']
        self.pars['specimen_b_sigma'] = data['specimen_b_sigma']
        self.pars['specimen_b_beta'] = data['specimen_b_beta']
        self.pars['specimen_YT'] = data['y_int']
        self.pars['specimen_XT'] = data['x_int']
        self.pars['x_prime'] = data['x_prime']
        self.pars['y_prime'] = data['y_prime']
        self.pars['delta_x_prime'] = data['delta_x_prime']
        self.pars['delta_y_prime'] = data['delta_y_prime']
        self.pars['specimen_f'] = data['specimen_f']
        self.pars['specimen_g'] = data['specimen_g']
        self.pars['specimen_g_lim'] = data['specimen_g_lim']
        self.pars['specimen_q'] = data['specimen_q']
        self.pars['specimen_w'] = data['specimen_w']
        self.pars['count_IZ'] = data['count_IZ']
        self.pars['count_ZI'] = data['count_ZI']
        self.pars['B_lab'] = data['B_lab']  # think I don't need this, actually
        self.pars['B_anc'] = data['B_anc']
        self.pars['B_anc_sigma'] = data['B_anc_sigma']
        self.pars['specimen_int'] = data['specimen_int']
        self.pars['specimen_int_sigma'] = data['specimen_int_sigma']
        return data

    def get_vds(self):
        zdata = self.zdata
        delta_y_prime = self.pars['delta_y_prime']
        start, end = self.start, self.end
        data = lib_arai.get_vds(zdata, delta_y_prime, start, end)
        self.pars['max_diff'] = data['max_diff']
        self.pars['vector_diffs'] = data['vector_diffs']
        self.pars['specimen_vds'] = data['specimen_vds']
        self.pars['specimen_fvds']= data['specimen_fvds']
        self.pars['vector_diffs_segment'] = data['vector_diffs_segment']
        self.pars['partial_vds'] = data['partial_vds']
        self.pars['GAP-MAX'] = data['GAP-MAX']
        return {'max_diff': data['max_diff'], 'vector_diffs': data['vector_diffs'], 'specimen_vds': data['specimen_vds'],
                'specimen_fvds': data['specimen_fvds'], 'vector_diffs_segment': data['vector_diffs_segment'],
                'partial_vds': data['partial_vds'], 'GAP-MAX': data['GAP-MAX']}

    def get_FRAC(self):
        vds = self.pars['specimen_vds']
        vector_diffs_segment = self.pars['vector_diffs_segment']
        FRAC = lib_arai.get_FRAC(vds, vector_diffs_segment)
        self.pars['FRAC'] = FRAC
        return FRAC

    def get_curve(self):
        x_Arai, y_Arai = self.x_Arai, self.y_Arai
        data = lib_k.AraiCurvature(x_Arai,y_Arai)
        self.pars['specimen_k'] = data[0]
        self.pars['SSE'] = data[3]
        return data[0], data[3]

    def get_curve_prime(self):
        """not in SPD documentation.  same as k, but using the segment instead of the full data set"""
        if len(self.x_Arai_segment) < 4:
            self.pars['specimen_k_prime'], self.pars['specimen_k_prime_sse'] = 0, 0
            return 0
        data = lib_k.AraiCurvature(self.x_Arai_segment, self.y_Arai_segment)
        self.pars['specimen_k_prime'] = data[0]
        self.pars['specimen_k_prime_sse'] = data[3]

    def get_SCAT(self):
        if (len(set(self.y_Arai_segment)) == 1): # prevents divide by zero, i.e. if all y values in segment are the same [1,1,1]
            self.pars['SCAT'] = 0 #float('nan')
            self.pars['fail_arai_beta_box_scatter'] = 0# float('nan')
            self.pars["fail_ptrm_beta_box_scatter"] = 0#float('nan')
            self.pars["fail_tail_beta_box_scatter"] = 0#float('nan')
            self.pars['scat_bounding_line_high'] = 0# float('nan')
            self.pars['scat_bounding_line_low'] = 0#float('nan')
            return 0
        slope = self.pars['specimen_b']
        x_mean, y_mean = self.x_Arai_mean, self.y_Arai_mean
        x_Arai_segment, y_Arai_segment = self.x_Arai_segment, self.y_Arai_segment
        if 'specimen_b_beta' in self.acceptance_criteria:
            box = lib_arai.get_SCAT_box(slope, x_mean, y_mean, beta_threshold=self.acceptance_criteria['specimen_b_beta']['value'])
        else:
            box = lib_arai.get_SCAT_box(slope, x_mean, y_mean)
        low_bound, high_bound, x_max, y_max, low_line, high_line = box[0], box[1], box[2], box[3], box[4], box[5]
        # getting SCAT points
        x_Arai_segment, y_Arai_segment = self.x_Arai_segment, self.y_Arai_segment
        tmin, tmax = self.tmin, self.tmax
        ptrm_checks_temps, ptrm_checks_starting_temps = self.ptrm_checks_temperatures, self.ptrm_checks_starting_temperatures
        x_ptrm_check, y_ptrm_check =  self.x_ptrm_check, self.y_ptrm_check
        tail_checks_temps, tail_checks_starting_temps =  self.tail_checks_temperatures, self.tail_checks_starting_temperatures
        x_tail_check, y_tail_check = self.x_tail_check, self.y_tail_check
        points, fancy_points = lib_arai.get_SCAT_points(x_Arai_segment, y_Arai_segment, tmin, tmax,
                                          ptrm_checks_temps, ptrm_checks_starting_temps,
                                          x_ptrm_check, y_ptrm_check, tail_checks_temps,
                                          tail_checks_starting_temps, x_tail_check, y_tail_check)
        # checking each point
        SCAT = lib_arai.get_SCAT(points, low_bound, high_bound, x_max, y_max)
        fancy_SCAT, SCATs = lib_arai.fancy_SCAT(fancy_points, low_bound, high_bound, x_max, y_max)
        #'SCAT_arai': False, 'SCAT_tail': True, 'SCAT_ptrm': True})
        self.pars['SCAT'] = fancy_SCAT
        self.pars['fail_arai_beta_box_scatter'] = SCATs['SCAT_arai']
        self.pars["fail_ptrm_beta_box_scatter"] = SCATs['SCAT_ptrm']
        self.pars["fail_tail_beta_box_scatter"] = SCATs['SCAT_tail']
        self.pars['scat_bounding_line_high'] = high_line # [y_int, slope]
        self.pars['scat_bounding_line_low'] = low_line # [y_int, slope]
        return fancy_SCAT

    def get_R_corr2(self):
        x_avg = self.x_Arai_mean
        y_avg = self.y_Arai_mean
        x_segment =self.x_Arai_segment
        y_segment =self.y_Arai_segment
        R_corr2 = lib_arai.get_R_corr2(x_avg, y_avg, x_segment, y_segment)
        self.pars['R_corr2'] = R_corr2
        return R_corr2

    def get_R_det2(self):
        y_segment = self.y_Arai_segment
        y_avg = self.y_Arai_mean
        y_prime = self.pars['y_prime']
        R_det2 = lib_arai.get_R_det2(y_segment, y_avg, y_prime)
        self.pars['R_det2'] = R_det2

    def get_Z(self):
        x_segment, y_segment = self.x_Arai_segment, self.y_Arai_segment
        x_int, y_int = self.pars['specimen_XT'], self.pars['specimen_YT']
        slope = self.pars['specimen_b']
        Z = lib_arai.get_Z(x_segment, y_segment, x_int, y_int, slope)
        self.pars['Z'] = Z
        return Z

    def get_Zstar(self):
        x_segment, y_segment = self.x_Arai_segment, self.y_Arai_segment
        x_int, y_int = self.pars['specimen_XT'], self.pars['specimen_YT']
        slope, n = self.pars['specimen_b'], self.n
        Zstar = lib_arai.get_Zstar(x_segment, y_segment, x_int, y_int, slope, n)
        self.pars['Zstar'] = Zstar
        return Zstar

    def get_IZZI_MD(self):
        import SPD.lib.lib_IZZI_MD as lib_izzi
        if ('IZ' in self.steps_Arai):
            IZZI_MD = lib_izzi.get_IZZI_MD(self.x_Arai, self.y_Arai, self.steps_Arai, self.start, self.end)
            self.pars['IZZI_MD'] = IZZI_MD
            return IZZI_MD
        else:
            IZZI_MD = float('nan')
            self.pars['IZZI_MD'] = IZZI_MD
            return IZZI_MD


    # directional statistics begin here:

    def get_dec_and_inc(self):
        Dec_Anc, Inc_Anc, best_fit_Anc, tau_Anc, V_Anc, mass_center, PCA_sigma_Anc = lib_direct.get_dec_and_inc(self.zdata,
                self.t_Arai, self.tmin, self.tmax, anchored=True)
        Dec_Free, Inc_Free, best_fit_Free, tau_Free, V_Free, mass_center, PCA_sigma_Free = lib_direct.get_dec_and_inc(self.zdata,
                self.t_Arai, self.tmin, self.tmax, anchored=False)
        self.pars['Dec_Anc'], self.pars['Dec_Free'] = Dec_Anc, Dec_Free
        self.pars['Inc_Anc'], self.pars['Inc_Free'] = Inc_Anc, Inc_Free
        self.pars['best_fit_vector_Anc'] = best_fit_Anc
        self.pars['best_fit_vector_Free'] = best_fit_Free
        self.pars['tau_Anc'], self.pars['tau_Free'] = tau_Anc, tau_Free
        self.pars['V_Anc'], self.pars['V_Free'] = V_Anc, V_Free
        self.pars['zdata_mass_center'] = mass_center
        self.pars['PCA_sigma_max_Free'] = PCA_sigma_Free[0]
        self.pars['PCA_sigma_int_Free'] = PCA_sigma_Free[1]
        self.pars['PCA_sigma_min_Free'] = PCA_sigma_Free[2]


    def get_ptrm_dec_and_inc(self):
        """not included in spd."""
        PTRMS = self.PTRMS[1:]
        CART_pTRMS_orig = numpy.array([lib_direct.dir2cart(row[1:4]) for row in PTRMS])
        #B_lab_dir = [self.B_lab_dir[0], self.B_lab_dir[1], 1.] # dir
        tmin, tmax = self.t_Arai[0], self.t_Arai[-1]
        ptrms_dec_Free, ptrms_inc_Free, ptrm_best_fit_vector_Free, ptrm_tau_Free, ptrm_v_Free, ptrm_mass_center_Free, ptrm_PCA_sigma_Free = lib_direct.get_dec_and_inc(CART_pTRMS_orig, self.t_Arai, tmin, tmax, anchored=False)
        ptrms_angle = lib_direct.get_ptrms_angle(ptrm_best_fit_vector_Free, self.B_lab_cart)
        self.pars['ptrms_dec_Free'], self.pars['ptrms_inc_Free'] = ptrms_dec_Free, ptrms_inc_Free
        self.pars['ptrms_tau_Free'] = ptrm_tau_Free
        self.pars['ptrms_angle_Free'] = ptrms_angle



    def get_MAD(self):
        MAD_Free = lib_direct.get_MAD(self.pars['tau_Free'])
        MAD_Anc = lib_direct.get_MAD(self.pars['tau_Anc'])
        self.pars['MAD_Free'], self.pars['MAD_Anc'] = MAD_Free, MAD_Anc
        return {'MAD_Free': MAD_Free, 'MAD_Anc': MAD_Anc }

    def get_ptrm_MAD(self):
        pTRM_MAD_Free = lib_direct.get_MAD(self.pars['ptrms_tau_Free'])
        self.pars['pTRM_MAD_Free'] = pTRM_MAD_Free
        return pTRM_MAD_Free


    def get_alpha(self): # need Int_Free and Int_Anc
        free = self.pars['best_fit_vector_Free']
        anc = self.pars['best_fit_vector_Anc']
        alpha = lib_direct.get_alpha(anc, free)
        self.pars['alpha'] = alpha

    def get_DANG(self):
        free = self.pars['best_fit_vector_Free']
        cm = self.pars['zdata_mass_center']
        DANG = lib_direct.get_angle_difference(free, cm)
        self.pars['DANG'] = DANG

    def get_NRM_dev(self):
        NRM_dev = lib_direct.get_NRM_dev(self.pars['DANG'], self.pars['zdata_mass_center'], self.pars['specimen_YT'])
        self.pars['NRM_dev'] = NRM_dev
        return NRM_dev

    def get_theta(self):
        b_lab_dir = [self.B_lab_dir[0], self.B_lab_dir[1], 1.]
        ChRM = self.pars['best_fit_vector_Free'] # GREIG switched to this
        theta = lib_direct.get_theta(b_lab_dir, ChRM)
        self.pars['theta'] = theta
        return theta

    def get_gamma(self):
        B_lab_dir = [self.B_lab_dir[0], self.B_lab_dir[1], 1.]
        ind = self.t_Arai.index(self.tmax)
        ptrm_dir = [self.PTRMS[ind][1], self.PTRMS[ind][2], old_div(self.PTRMS[ind][3], self.specimen_Data['NRM'])]
        ptrm_cart = lib_direct.dir2cart(ptrm_dir)
        gamma = lib_direct.get_gamma(B_lab_dir, ptrm_dir)
        self.pars['ptrm_dir'] = ptrm_dir
        self.pars['ptrm_cart'] = ptrm_cart
        self.pars['gamma'] = gamma
        return gamma


# ptrm statistics begin here

    def get_n_ptrm(self):
        tmin, tmax = self.tmin, self.tmax
        ptrm_temps, ptrm_starting_temps = self.ptrm_checks_temperatures, self.ptrm_checks_starting_temperatures
        n, steps = lib_ptrm.get_n_ptrm(tmin, tmax, ptrm_temps, ptrm_starting_temps)
        self.pars['n_ptrm'] = n
        self.pars['ptrm_checks_included_temps'] = steps

    def get_max_ptrm_check(self):
        ptrm_checks_included_temps = self.pars['ptrm_checks_included_temps']
        ptrm_checks = self.ptrm_checks_temperatures
        ptrm_x = self.x_ptrm_check
        x_Arai, t_Arai = self.x_Arai, self.t_Arai
        ptrm_checks, max_ptrm_check, sum_ptrm_checks, check_percent, sum_abs_ptrm_checks = lib_ptrm.get_max_ptrm_check(ptrm_checks_included_temps,
            ptrm_checks, ptrm_x, t_Arai, x_Arai)
        self.pars['ptrm_checks'] = ptrm_checks
        self.pars['max_ptrm_check_percent'] = check_percent
        self.pars['max_ptrm_check'] = max_ptrm_check
        self.pars['sum_ptrm_checks'] = sum_ptrm_checks
        self.pars['sum_abs_ptrm_checks'] = sum_abs_ptrm_checks
        return max_ptrm_check

    def get_delta_CK(self):
#        def get_delta_CK(max_ptrm_check, x_int):
        delta_CK = lib_ptrm.get_delta_CK(self.pars['max_ptrm_check'], self.pars['specimen_XT'])
        self.pars['delta_CK'] = delta_CK
        return delta_CK

    def get_DRAT(self):
#        def get_DRAT(delta_y_prime, delta_x_prime, max_ptrm_check):
        DRAT, L = lib_ptrm.get_DRAT(self.pars['delta_x_prime'], self.pars['delta_y_prime'], self.pars['max_ptrm_check'])
        self.pars['DRAT'] = DRAT
        self.pars['length_best_fit_line'] = L
        return DRAT

    def get_length_best_fit_line(self):
        L = lib_ptrm.get_length_best_fit_line(self.pars['delta_x_prime'], self.pars['delta_y_prime'])
        self.pars['length_best_fit_line'] = L
        return L

    def get_max_DEV(self):
        max_DEV = lib_ptrm.get_max_DEV(self.pars['delta_x_prime'], self.pars['max_ptrm_check'])
        self.pars['max_DEV'] = max_DEV
        return max_DEV

    def get_CDRAT(self):
        CDRAT, CDRAT_prime = lib_ptrm.get_CDRAT(self.pars['length_best_fit_line'], self.pars['sum_ptrm_checks'],
                                                self.pars['sum_abs_ptrm_checks'])
        self.pars['CDRAT'], self.pars['CDRAT_prime'] = CDRAT, CDRAT_prime
        return CDRAT, CDRAT_prime

    def get_DRATS(self):
        DRATS, DRATS_prime = lib_ptrm.get_DRATS(self.pars['sum_ptrm_checks'], self.pars['sum_abs_ptrm_checks'], self.x_Arai, self.end)
        self.pars['DRATS'] = DRATS
        self.pars['DRATS_prime'] = DRATS_prime
        return DRATS

    def get_mean_DRAT(self):
        mean_DRAT, mean_DRAT_prime = lib_ptrm.get_mean_DRAT(self.pars['sum_ptrm_checks'], self.pars['sum_abs_ptrm_checks'],
                                                            self.pars['n_ptrm'], self.pars['length_best_fit_line'])
        self.pars['mean_DRAT'] = mean_DRAT
        self.pars['mean_DRAT_prime'] = mean_DRAT_prime
        return mean_DRAT, mean_DRAT_prime

    def get_mean_DEV(self):
        mean_DEV, mean_DEV_prime = lib_ptrm.get_mean_DEV(self.pars['sum_ptrm_checks'], self.pars['sum_abs_ptrm_checks'],
                                                         self.pars['n_ptrm'], self.pars['delta_x_prime'])
        self.pars['mean_DEV'] = mean_DEV
        self.pars['mean_DEV_prime'] = mean_DEV_prime

    def get_delta_pal(self):
        if self.pars['n_ptrm'] == 0: # otherwise will error if no ptrm checks
            self.pars['delta_pal'] = 0
            return 0
        ptrms_segment, checks_segment = lib_ptrm.get_segments(self.PTRMS, self.PTRM_Checks, self.tmax)
        delta_pal = lib_ptrm.get_full_delta_pal(self.PTRMS, self.PTRM_Checks, self.NRM, self.pars['y_err'],
                                                self.y_Arai_mean, self.pars['specimen_b'], self.start, self.end,
                                                self.y_Arai_segment)
        self.pars['delta_pal'] = delta_pal


        # tail check statistics

    def get_n_tail(self):
        if len(self.tail_checks_temperatures) > 0:
            n_tail = lib_tail.get_n_tail(self.tmax, self.tail_checks_temperatures)
        else:
            n_tail = 0
        self.pars['n_tail'] = n_tail
        return n_tail

    def get_max_tail_check(self):
        if len(self.y_tail_check) > 0:
            tail_check_max, tail_check_diffs = lib_tail.get_max_tail_check(self.y_Arai, self.y_tail_check, self.t_Arai,
                                                                           self.tail_checks_temperatures, self.pars['n_tail'])
        else:
            tail_check_max, tail_check_diffs = 0, [0]
        self.pars['tail_check_max'], self.pars['tail_check_diffs'] = tail_check_max, tail_check_diffs
        return tail_check_max, tail_check_diffs

    def get_DRAT_tail(self):
        DRAT_tail = lib_tail.get_DRAT_tail(self.pars['tail_check_max'], self.pars['length_best_fit_line'])
        self.pars['DRAT_tail'] = DRAT_tail
        return DRAT_tail

    def get_delta_TR(self):
    #    def get_delta_TR(tail_check_max, y_int)
        delta_TR = lib_tail.get_delta_TR(self.pars['tail_check_max'], self.pars['specimen_YT'])
        self.pars['delta_TR'] = delta_TR
        return delta_TR

    def get_MD_VDS(self):
        MD_VDS = lib_tail.get_MD_VDS(self.pars['tail_check_max'], self.pars['specimen_vds'])
        self.pars['MD_VDS'] = MD_VDS
        return MD_VDS


    # additivity check statistics start here

    def get_n_add(self):
        n_add = lib_add.get_n_add(self.add_checks_temperatures, self.add_checks_starting_temperatures, self.tmax)[1]
        self.pars['n_add'] = n_add
        return n_add

    def get_delta_AC(self):
        delta_AC, incl_AC_checks = lib_add.get_delta_AC(self.pars['n_add'], self.AC_Diffs, self.pars['specimen_XT'])
        self.pars['delta_AC'] = delta_AC
        self.pars['AC_Checks_segment'] = incl_AC_checks
        return delta_AC

    # statistics that require an independent paleointensity study

    def get_alpha_prime(self):
        self.pars['specimen_alpha_prime'] = -999.

    def get_CRM_percent(self):
        self.pars['specimen_int_crm'] = -999.

    def get_delta_t_star(self):
        self.pars['specimen_dt'] = -999.

    # two methods for running the statistics

    def calculate_all_statistics(self):
        #print "calling calculate_all_statistics in spd.py"
        if self.n < 3:
            print("-W- Cannot run statistics with only {} points".format(self.n))
            self.pars = {}
            return None
        self.York_Regression()
        self.get_vds()
        self.get_FRAC()
        self.get_curve()
        self.get_curve_prime()
        self.get_SCAT()
        self.get_R_corr2()
        self.get_R_det2()
        self.get_Z()
        self.get_Zstar()
        self.get_IZZI_MD()
        # directional statistics
        self.get_dec_and_inc()
        self.get_ptrm_dec_and_inc()
        self.get_MAD()
        self.get_ptrm_MAD()
        self.get_alpha()
        self.get_DANG()
        self.get_NRM_dev()
        self.get_theta()
        self.get_gamma()
        # ptrm check statistics
        self.get_n_ptrm()
        if self.pars['n_ptrm'] == 0:
            self.pars['max_ptrm_check'], self.pars['delta_CK'], self.pars['get_DRAT'], self.pars['DRAT'], self.pars['DRATS'], self.pars['CDRAT'], self.pars['mean_DRAT'], self.pars['mean_DEV'], self.pars['max_DEV'], self.pars['delta_pal'] = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
            self.get_length_best_fit_line()
        else:
            self.get_max_ptrm_check()
            self.get_delta_CK()
            self.get_DRAT()
            self.get_max_DEV()
            self.get_CDRAT()
            self.get_DRATS()
            self.get_mean_DRAT()
            self.get_mean_DEV()
            self.get_delta_pal()
        # tail check statistics
        self.get_n_tail()
        self.get_max_tail_check()
        self.get_DRAT_tail()
        self.get_delta_TR()
        self.get_MD_VDS()
        # additivity check statistics
        self.get_n_add()
        self.get_delta_AC()
        # stats that require an independent chrm or are not yet coded
        self.get_alpha_prime()
        self.get_CRM_percent()
        self.get_delta_t_star()
        if self.mapping == 'magic':
            self.pars = map_magic.mapping(self.pars, map_magic.spd2magic_map)



    statistics = {
        'alpha': get_alpha,
        'alpha_prime': get_alpha_prime,
        'R_corr2': get_R_corr2,
        'PCA_sigma_int_Free': get_dec_and_inc,
        'PCA_sigma_max_Free': get_dec_and_inc,
        'n_tail': get_n_tail,
        'delta_pal': get_delta_pal,
        'DRAT_tail': get_DRAT_tail,
        'MD_VDS': get_MD_VDS,
        'n_add': get_n_add,
        'delta_AC': get_delta_AC,
        'y_Arai_mean': None,
        'MAD_Free': get_MAD,
        'n_ptrm': get_n_ptrm,
        'DRAT': get_DRAT,
        'IZZI_MD': get_IZZI_MD,
        'FRAC': get_FRAC,
        'CDRAT': get_CDRAT,
        'Dec_Free': get_dec_and_inc,
        'mean_DEV': get_mean_DEV,
        'DRATS': get_DRATS,
        'Z': get_Z,
        'max_DEV': get_max_DEV,
        'fail_arai_beta_box_scatter': get_SCAT,
        'GAP-MAX': get_vds,
        'pTRM_MAD_Free': get_ptrm_MAD,
        'ptrms_dec_Free': get_ptrm_dec_and_inc,
        'MAD_Anc': get_MAD,
        'fail_ptrm_beta_box_scatter': get_SCAT,
        'ptrms_angle_Free': get_ptrm_dec_and_inc,
        'scat_bounding_line_low': get_SCAT,
        'PCA_sigma_min_Free': get_dec_and_inc,
        'B_anc': York_Regression,
        'SCAT': get_SCAT,
        'R_det2': get_R_det2,
        'best_fit_vector_Free': get_dec_and_inc,
        'specimen_b_beta': York_Regression,
        'specimen_YT': York_Regression,
        'delta_CK': get_delta_CK,
        'lab_dc_field': None,
        'Inc_Free': get_dec_and_inc,
        'mean_DRAT': get_mean_DRAT,
        'theta': get_theta,
        'max_ptrm_check': get_max_ptrm_check,
        'tmin': None,
        'x_Arai_mean': None,
        'fail_tail_beta_box_scatter': get_SCAT,
        'delta_TR': get_delta_TR,
        'alpha': get_alpha,
        'specimen_fvds': get_vds,
        'specimen_b_sigma': York_Regression,
        'specimen_b': York_Regression,
        'specimen_g': York_Regression,
        'specimen_f': York_Regression,
        'tmax': None,
        'specimen_int_n': None,
        'specimen_q': York_Regression,
        'DANG': get_DANG,
        'ptrms_inc_Free': get_ptrm_dec_and_inc,
        'SSE': get_curve,
        'gamma': get_gamma,
        'scat_bounding_line_high': get_SCAT,
        'specimen_k': get_curve,
        'specimen_int_crm': get_CRM_percent,
        'specimen_dt': get_delta_t_star,
        'specimen_k_prime': get_curve_prime,
        'specimen_k_prime_SSE': get_curve_prime
    }

    dependencies = {
        'get_alpha': (York_Regression, get_dec_and_inc),
        'get_curve': (York_Regression,),
        'get_curve_prime': (York_Regression,),
        'get_R_corr2': (York_Regression,),
        'York_Regression': (None,),
        'get_dec_and_inc': (None,),
        'get_n_tail': (None,),
        'get_DRATS': (get_n_ptrm, get_max_ptrm_check),
        'get_FRAC': (York_Regression, get_vds),
        'get_vds': (York_Regression,),
        'get_SCAT': (York_Regression,),
        'get_Z': (York_Regression,),
        'get_R_det2': (York_Regression,),
        'get_MAD': (get_dec_and_inc,),
        'get_DANG': (get_dec_and_inc,),
        'get_theta': (get_dec_and_inc,),
        'get_max_ptrm_check': (get_n_ptrm,),
        'get_DRAT': (York_Regression, get_n_ptrm, get_max_ptrm_check),
        'get_CDRAT': (York_Regression, get_n_ptrm, get_max_ptrm_check, get_DRAT),
        'get_mean_DRAT': (York_Regression, get_n_ptrm, get_max_ptrm_check, get_DRAT),
        'get_delta_CK': (York_Regression, get_n_ptrm, get_max_ptrm_check),
        'get_max_DEV': (York_Regression, get_n_ptrm, get_max_ptrm_check),
        'get_mean_DEV': (York_Regression, get_n_ptrm, get_max_ptrm_check),
        'get_delta_pal': (York_Regression,),
        'get_MD_VDS': (York_Regression, get_vds, get_n_tail, get_max_tail_check),
        'get_DRAT_tail': (York_Regression, get_n_ptrm, get_max_ptrm_check, get_DRAT, get_n_tail, get_max_tail_check),
        'get_delta_TR': (York_Regression, get_n_tail, get_max_tail_check),
        'get_delta_AC': (York_Regression, get_n_add,),
}

    def reqd_stats(self):
        #print 'do REQD STATS'
        if self.n < 3:
            print("-W- Cannot run statistics with only {} points".format(self.n))
            self.pars = {}
            return None
        stats_run = []
        #print 'self.calculate: ', self.calculate
        if 'best_fit_vector_Free' not in self.calculate:
            self.calculate.append('best_fit_vector_Free')
        for stat in self.calculate: # iterate through all stats that should be calculated
            func = self.statistics[stat]
            #print 'func', func
            if func: # sometimes this will be none, since statistics like tmin are generated during __init__ and don't require a function to be run
                if func.__name__ == 'York_Regression':
                    #print 'York_Regression'
                    if 'York_Regression' not in stats_run:
                        func(self)
                        stats_run.append(func.__name__)
                elif func.__name__ in self.dependencies:
                    for d in self.dependencies[func.__name__]:
                        if d == None: continue
                        #print 'd: ', d,
                        if d.__name__ not in stats_run: # if the dependency has not already been run, run it
                            d(self)
                            stats_run.append(d.__name__)
                    if func.__name__ not in stats_run:
                        func(self) # all dependencies have been satisfied, so run the main function
                        stats_run.append(func.__name__)
                else:
                    #print 'alert: did not find dependencies, now attempting to run'
                    try:
                        func(self) # this will work if the function has no dependencies
                        stats_run.append(func.__name__)
                    except:
                        self.calculate_all_statistics() # if no dependency info can be found, just run all statistics
                        return 0 # since all possible statistics have been run, the function ends
        #print 'stats run: ', stats_run
        if self.mapping == 'magic':
            self.pars = map_magic.mapping(self.pars, map_magic.spd2magic_map)
        if len(stats_run) != len(set(stats_run)):
            raise Exception('lengths were off')


def make_thing():
    """ makes example PintPars object """
    cwd = os.getcwd()
    main_dir = cwd + '/SPD'
    try:
        import new_lj_thellier_gui_spd as tgs
        gui = tgs.Arai_GUI('/magic_measurements.txt', main_dir)
        specimens = list(gui.Data.keys())
        thing = PintPars(gui.Data, '0238x6011044', 473., 623.)
        thing.calculate_all_statistics()
        #new_thing = PintPars(gui.Data, '0238x5721062', 100. + 273., 525. + 273.)
        #new_thing.calculate_all_statistics()
        gui2 = tgs.Arai_GUI('/magic_measurements.txt', '/Users/nebula/Desktop/MagIC_experiments/ODP-SBG_1')
        thing2 = PintPars(gui2.Data, '0335x1031411', 273., 743.)
        return thing, thing2
    except Exception as ex:
        print('could not make standard specimen objects')
        print(ex)


#thing2 = PintPars(gui.Data, specimens[0], 473., 623.)
#thing2.calculate_all_statistics()
#thing3 = PintPars(gui.Data, specimens[1], 473., 623.)
#thing3.calculate_all_statistics()
#thing4 = PintPars(gui.Data, specimens[2], 473., 623.)
#thing4.calculate_all_statistics()
#thing5 = PintPars(gui.Data, specimens[3], 473., 623.)
#thing5.calculate_all_statistics()
#thing6 = PintPars(gui.Data, specimens[4], 473., 623.)
#thing6.calculate_all_statistics()


#gui2 = tgs.Arai_GUI('new_magic_measurements.txt')
#gui3 = tgs.Arai_GUI('consistency_tests/Bowles_etal_2006_magic_measurements.txt')
#gui4 = tgs.Arai_GUI('consistency_tests/Donadini_etal_2007_magic_measurements.txt')
#gui5 = tgs.Arai_GUI('consistency_tests/Krasa_2000_magic_measurements.txt')
#gui6 = tgs.Arai_GUI('consistency_tests/Muxworthy_etal_2011_magic_measurements.txt')
#gui7 = tgs.Arai_GUI('consistency_tests/Paterson_etal_2010_magic_measurements.txt')
#gui8 = tgs.Arai_GUI('consistency_tests/Selkin_etal_2000_magic_measurements.txt')
#gui10 = tgs.Arai_GUI('consistency_tests/Yamamoto_etal_2003_magic_measurements.txt')
