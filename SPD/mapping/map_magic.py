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

#mapped_pars = mapping(Pint_pars.pars, a_map)

# mapping between SPD & Magic 2
spd = ['R_corr2', 'PCA_sigma_int_Free', 'PCA_sigma_max_Free', 'n_tail', 'delta_pal', 'DRAT_tail', 'MD_VDS', 'n_add', 'delta_AC', 'y_Arai_mean', 'MAD_Free', 'n_ptrm', 'DRAT', 'IZZI_MD', 'FRAC', 'CDRAT', 'Dec_Free', 'mean_DEV', 'DRATS', 'Z', 'max_DEV', 'fail_arai_beta_box_scatter', 'GAP-MAX', 'pTRM_MAD_Free', 'ptrms_dec_Free', 'MAD_Anc', 'fail_ptrm_beta_box_scatter', 'ptrms_angle_Free', 'scat_bounding_line_low', 'PCA_sigma_min_Free', 'B_anc', 'SCAT', 'R_det2', 'best_fit_vector_Free', 'specimen_b_beta', 'specimen_YT', 'delta_CK', 'lab_dc_field', 'Inc_Free', 'mean_DRAT', 'theta', 'max_ptrm_check', 'tmin', 'x_Arai_mean', 'fail_tail_beta_box_scatter', 'delta_TR', 'alpha', 'specimen_fvds', 'specimen_b_sigma', 'specimen_b', 'specimen_g', 'specimen_f', 'tmax', 'specimen_int_n', 'specimen_q', 'DANG', 'ptrms_inc_Free', 'SSE', 'gamma', 'scat_bounding_line_high', 'specimen_k', 'specimen_int_crm', 'specimen_dt', 'specimen_k_prime', 'specimen_k_prime_SSE']

magic = ['specimen_coeff_det_sq', 'specimen_PCA_sigma_int', 'specimen_PCA_sigma_max', 'specimen_int_ptrm_tail_n', 'specimen_dpal', 'specimen_tail_drat', 'specimen_md', 'specimen_ac_n', 'specimen_dac', 'specimen_cm_y', 'specimen_int_mad', 'specimen_int_ptrm_n', 'specimen_drat', 'specimen_z_md', 'specimen_frac', 'specimen_cdrat', 'specimen_dec', 'specimen_mdev', 'specimen_drats', 'specimen_z', 'specimen_maxdev', 'fail_arai_beta_box_scatter', 'specimen_gmax', 'specimen_ptrms_mad', 'specimen_ptrms_dec', 'specimen_int_mad_anc', 'fail_ptrm_beta_box_scatter', 'specimen_ptrms_angle', 'specimen_scat_bounding_line_low', 'specimen_PCA_sigma_min', 'specimen_int_uT', 'specimen_scat', 'specimen_r_sq', 'specimen_PCA_v1', 'specimen_b_beta', 'specimen_YT', 'specimen_dck', 'lab_dc_field', 'specimen_inc', 'specimen_mdrat', 'specimen_theta', 'specimen_ptrm', 'measurement_step_min', 'specimen_cm_x', 'fail_tail_beta_box_scatter', 'specimen_dtr', 'specimen_int_alpha', 'specimen_fvds', 'specimen_b_sigma', 'specimen_b', 'specimen_g', 'specimen_f', 'measurement_step_max', 'specimen_int_n', 'specimen_q', 'specimen_int_dang', 'specimen_ptrms_inc', 'specimen_k_sse', 'specimen_gamma', 'specimen_scat_bounding_line_high', 'specimen_k', 'specimen_int_crm', 'specimen_dt', 'specimen_k_prime', 'specimen_k_prime_sse']

spd2magic_map = dict(zip(spd, magic))
magic2spd_map = dict(zip(magic, spd))

# mapping between magic2 and magic3
meas_magic2 = ['treatment_dc_field_theta', 'treatment_ac_field', 
          'treatment_dc_field', 'measurement_number', 
          'measurement_description', 'measurement_magn_volume', 
          'er_specimen_name', 'er_site_name', 'treatment_temp', 
          'er_sample_name', 'measurement_flag', 'measurement_inc', 
          'er_location_name', 'measurement_dec', 'magic_method_codes', 
          'magic_instrument_codes', 'treatment_dc_field_phi', 
          'measurement_magn_moment', 'measurement_magn_mass', 
          'measurement_csd']

spec_magic2 = ['er_analyst_mail_names', 'er_citation_names', 
          'magic_software_packages', 'measurement_step_max', 
          'measurement_step_min', 'measurement_step_unit', 'specimen_alpha95', 
          'specimen_comp_n', 'specimen_comp_name', 'specimen_correction', 
          'specimen_dang', 'specimen_dec', 'specimen_direction_type', 
          'specimen_flag', 'specimen_inc', 'specimen_mad', 'specimen_n', 
          'specimen_tilt_correction', 'magic_method_codes', 
          'magic_instrument_codes', 'er_specimen_name', 'er_site_name', 
          'er_sample_name', 'er_location_name']

meas_magic3 = ['treat_dc_field_theta', 'treat_ac_field', 'treat_dc_field',
          'number', 'description', 'magn_volume',
          'specimen', 'site', 'treat_temp', 'sample',
          'flag', 'dir_inc', 'location',
          'dir_dec', 'method_codes', 'instrument_codes',
          'treat_dc_field_phi', 'magn_moment',
          'magn_mass', 'dir_csd']

spec_magic3 = ['analyst_names', 'citations', 'software_packages', 
          'meas_step_max', 'meas_step_min', 'meas_step_unit', 'dir_alpha95', 
          'dir_n_comps', 'dir_comp_name', 'aniso_tilt_correction', 'dir_dang', 
          'dir_dec', 'dir_type', 'result_flag', 'dir_inc', 'dir_mad_free', 
          'dir_n_measurements', 'dir_tilt_correction', 'method_codes', 
          'instrument_codes', 'specimen', 'site', 'sample', 'location']

meas_magic3_2_magic2_map = dict(zip(meas_magic3, meas_magic2))
meas_magic2_2_magic3_map = dict(zip(meas_magic2, meas_magic3))
spec_magic3_2_magic2_map = dict(zip(spec_magic3, spec_magic2))
spec_magic2_2_magic3_map = dict(zip(spec_magic2, spec_magic3))
