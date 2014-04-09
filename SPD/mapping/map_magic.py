#!/usr/bin/env python

# map_MagIC.py: -*- Python -*-  DESCRIPTIVE TEXT.
# 
#  Copyright (c) 2014 Lori Jonestrask
#  Author: Lori Jonestrask (mintblue87@gmail.com) .


def mapping(dictionary, mapping):
    """
    takes in a dictionary and a mapping which contains new key names,
    and returns a new dictionary with the updated key names, i.e.:
    dictionary = {'a': 1, 'b': 2, 'c': 3}
    mapping = {'a': 'aa', 'c': 'cc'}
    mapped_dictionary = mapping(dictionary, mapping)
    mapped_dictionary = {'aa': 1, b, 2, 'cc': 3}
    """
    mapped_dictionary = {}
    for key, value in dictionary.iteritems():
        if key in mapping.keys():
            new_key = mapping[key]
            mapped_dictionary[new_key] = value
        else:
            mapped_dictionary[key] = value # if this line is left in, it gives everything from the original dictionary
    return mapped_dictionary


a_map = {'fail_ptrm_beta_box_scatter': 'fail_ptrm_beta_box_scatter', 'scat_bounding_line_low': 'specimen_scat_bounding_line_low', 'fail_tail_beta_box_scatter': 'fail_tail_beta_box_scatter', 'MD_VDS': 'specimen_md', 'B_anc': 'specimen_int_uT', 'FRAC': 'specimen_frac', 'Inc_Free': 'specimen_inc', 'best_fit_vector_Free': 'specimen_PCA_v1', 'specimen_b_sigma': 'specimen_b_sigma', 'specimen_YT': 'specimen_YT', 'y_Arai_mean': 'specimen_cm_y', 'SCAT': 'specimen_scat', 'MAD_Free': 'specimen_int_mad', 'MAD_Anc': 'specimen_int_mad_anc', 'n_ptrm': 'specimen_int_ptrm_n', 'tmin': 'measurement_step_min', 'x_Arai_mean': 'specimen_cm_x', 'Dec_Free': 'specimen_dec', 'DRATS': 'specimen_drats', 'specimen_fvds': 'specimen_fvds', 'specimen_b_beta': 'specimen_b_beta', 'specimen_b': 'specimen_b', 'specimen_g': 'specimen_g', 'fail_arai_beta_box_scatter': 'fail_arai_beta_box_scatter', 'specimen_f': 'specimen_f', 'tmax': 'measurement_step_max', 'specimen_n': 'specimen_int_n', 'specimen_q': 'specimen_q', 'lab_dc_field': 'lab_dc_field', 'GAP-MAX': 'specimen_gmax', 'DANG': 'specimen_int_dang', 'ptrms_angle_Free': 'specimen_ptrms_angle', 'scat_bounding_line_high': 'specimen_scat_bounding_line_high', 'PCA_sigma_max_Free': "specimen_PCA_sigma_max" , 'PCA_sigma_int_Free': 'specimen_PCA_sigma_int', 'PCA_sigma_min_Free': 'specimen_PCA_sigma_min', 'ptrms_dec_Free': 'specimen_ptrms_dec', 'ptrms_inc_Free': 'specimen_ptrms_inc', 'pTRM_MAD_Free': 'specimen_ptrms_mad', 'theta': 'specimen_theta', 'gamma': 'specimen_gamma', 'delta_TR': 'specimen_dtr', 'delta_AC': 'specimen_dac', 'SSE': 'specimen_k_sse', 'Z': 'specimen_z', 'IZZI_MD': 'specimen_z_md', 'R_det2': 'specimen_r_sq', 'R_corr2': 'specimen_coeff_det_sq', 'alpha': 'specimen_int_alpha', 'max_ptrm_check': 'specimen_ptrm', 'DRAT': 'specimen_drat', 'CDRAT': 'specimen_cdrat', 'mean_DRAT': 'specimen_mdrat', 'delta_CK': 'specimen_dck', 'max_DEV': 'specimen_maxdev', 'mean_DEV': 'specimen_mdev', 'delta_pal': 'specimen_dpal', 'n_tail': 'specimen_int_ptrm_tail_n', 'MD_VDS': 'specimen_md', 'DRAT_tail': 'specimen_tail_drat', 'delta_AC': 'specimen_dac', 'n_add' : 'specimen_ac_n'} # spd name: thellier_gui name 

#mapped_pars = mapping(Pint_pars.pars, a_map)
