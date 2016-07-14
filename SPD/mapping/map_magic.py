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

#measurement data translation magic_measurements.txt -> measurements.txt
meas_magic3_2_magic2_map = {'treat_dc_field_theta': 'treatment_dc_field_theta', 'sample': 'er_sample_name', 'treat_dc_field': 'treatment_dc_field', 'instrument_codes': 'magic_instrument_codes', 'description': 'measurement_description', 'magn_volume': 'measurement_magn_volume', 'specimen': 'er_specimen_name', 'treat_dc_field_phi': 'treatment_dc_field_phi', 'number': 'measurement_number', 'site': 'er_site_name', 'treat_ac_field': 'treatment_ac_field', 'flag': 'measurement_flag', 'dir_inc': 'measurement_inc', 'location': 'er_location_name', 'dir_dec': 'measurement_dec', 'method_codes': 'magic_method_codes', 'treat_temp': 'treatment_temp', 'magn_moment': 'measurement_magn_moment', 'magn_mass': 'measurement_magn_mass', 'dir_csd': 'measurement_csd'}

meas_magic2_2_magic3_map = {v:k for k,v in meas_magic3_2_magic2_map.items()}

#specimen data translation pmag_speciemns,er_specimens -> specimens.txt
spec_magic3_2_magic2_map = {'int_drats': 'specimen_drats', 'site': 'er_site_name', 'int_mad': 'specimen_int_mad', 'sample': 'er_sample_name', 'measurement_step_max': 'meas_step_max', 'specimen_n': 'dir_n_measurements', 'int_n_measurements': 'specimen_int_n', 'int_corr': 'specimen_correction', 'int_rsc': 'specimen_rsc', 'analyst_names': 'er_analyst_mail_names', 'int_scat': 'specimen_scat', 'int_ptrm_n': 'specimen_int_ptrm_n', 'citations': 'er_citation_names', 'int_gmax': 'specimen_gmax', 'int_dang': 'specimen_int_dang', 'dir_tilt_correction': 'specimen_tilt_correction', 'location': 'er_location_name', 'dir_comp': 'specimen_comp_name', 'specimen_magn_moment': 'magn_moment', 'int_w': 'specimen_w', 'specimen': 'er_specimen_name', 'int_q': 'specimen_q', 'int_fvds': 'specimen_fvds', 'specimen_mad': 'dir_mad_free', 'int_frac': 'specimen_frac', 'meas_step_min': 'measurement_step_min', 'int_f': 'specimen_f', 'software_packages': 'magic_software_packages', 'dir_mad_free': 'specimen_mad', 'magn_moment': 'specimen_magn_moment', 'instrument_codes': 'magic_instrument_codes', 'int_b_beta': 'specimen_b_beta', 'dir_n_comps': 'specimen_comp_n', 'int_md': 'specimen_md', 'dir_n_measurements': 'specimen_n', 'dir_inc': 'specimen_inc', 'specimen_magn_volumn': 'magn_volumn', 'meas_step_max': 'measurement_step_max', 'dir_alpha95': 'specimen_alpha95', 'magn_volumne': 'specimen_magn_volumn', 'measurement_step_min': 'meas_step_min', 'meas_step_unit': 'measurement_step_unit', 'dir_dec': 'specimen_dec', 'method_codes': 'magic_method_codes', 'result_quality': 'specimen_flag', 'dir_dang': 'specimen_dang'}

spec_magic2_2_magic3_map = {v:k for k,v in spec_magic3_2_magic2_map.items()}

#sample data translation pmag_samples,er_samples -> samples.txt
samp_magic3_2_magic2_map = {'int_n_specimens' : 'sample_int_n', 'int_abs_sigma' : 'sample_int_sigma', 'int_abs_sigma_perc' : 'sample_int_sigma_perc', 'dir_alpha95' : 'sample_alpha95', 'dir_n_specimens' : 'sample_n', 'dir_n_specimens_lines' : 'sample_n_lines', 'dir_n_specimens_planes' : 'sample_n_planes', 'dir_k' : 'sample_k', 'dir_r' : 'sample_r'}

samp_magic2_2_magic3_map = {v:k for k,v in samp_magic3_2_magic2_map.items()}

#site data translation pmag_sites,er_sites -> sites.txt
site_magic3_2_magic2_map = {'int_abs_sigma' : 'site_int_sigma', 'int_abs_sigma_perc' : 'site_int_sigma_perc', 'int_n_samples' : 'site_int_n', 'dir_alpha95' : 'site_alpha95', 'dir_k' : 'site_k', 'dir_n_samples' : 'site_n', 'dir_n_specimens_lines' : 'site_n_lines', 'dir_n_specimens_planes' : 'site_n_planes', 'dir_r' : 'site_r'}

site_magic2_2_magic3_map = {v:k for k,v in site_magic3_2_magic2_map.items()}

meas_magic2 = meas_magic3_2_magic2_map.values()
spec_magic2 = spec_magic3_2_magic2_map.values()
samp_magic2 = samp_magic3_2_magic2_map.values()
site_magic2 = site_magic3_2_magic2_map.values()
meas_magic3 = meas_magic3_2_magic2_map.keys()
spec_magic3 = spec_magic3_2_magic2_map.keys()
samp_magic3 = samp_magic3_2_magic2_map.keys()
site_magic3 = site_magic3_2_magic2_map.keys()
