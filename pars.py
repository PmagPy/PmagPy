# pars.py: -*- Python -*-  DESCRIPTIVE TEXT.
# 
#  Copyright (c) 2014 Lori Jonestrask
#  Author: Lori Jonestrask (mintblue87@gmail.com) .

# spd name: thellier_gui name

mapping = {0: 'specimen_polarity', 1: 'specimen_nrm', 
'FRAC': 'specimen_frac', 
2: 'specimen_correction', 3: 'specimen_direction_type', 4: 'specimen_flag', 5: 'specimen_comp_nmb', 6: 'specimen_comp_n', 7: 'specimen_comp_name', 8: 'specimen_inferred_age', 9: 'specimen_inferred_age_sigma', 10: 'specimen_inferred_age_low', 11: 'specimen_inferred_age_high', 12: 'specimen_inferred_age_unit', 
'Inc_Free': 'specimen_inc', 
'Dec_Free': 'specimen_dec', 
13: 'specimen_alpha95', 
'specimen_n': 'specimen_n', 
'specimen_n_total': 'specimen_n_total', 
14: 'specimen_tilt_correction', 
'specimen_int': 'specimen_int', 
'B_anc_sigma?': 'specimen_int_sigma', 
15: 'specimen_int_sigma_perc', 16: 'specimen_int_rel', 17: 'specimen_int_rel_sigma', 18: 'specimen_int_rel_sigma_perc', 19: 'specimen_int_n', 20: 'specimen_alpha_prime', 
21: 'specimen_alpha', 
'alpha': 'specimen_int_alpha', 
'MAD_Free': 'specimen_mad', 
'MAD_Anc': 'specimen_mad_anc', 
22: 'specimen_int_mad', 23:'specimen_int_mad_anc', 
'specimen_w': 'specimen_w', 
'specimen_q': 'specimen_q', 
'specimen_f': 'specimen_f', 
'specimen_fvds': 'specimen_fvds', 
'specimen_b': 'specimen_b', 
'specimen_b_sigma': 'specimen_b_sigma', 
'specimen_b_beta': 'specimen_b_beta', 
'specimen_g': 'specimen_g', 
'GAP-MAX': 'specimen_gmax', 
'R_det2': 'specimen_r_sq', 
'R_corr2': 'specimen_coeff_det_sq', 
'DANG': 'specimen_dang', 
24: 'specimen_int_dang', 25: 'specimen_int_crm', 
'n_tail': 'specimen_int_ptrm_tail_n', 
'MD_VDS': 'specimen_md', 
'DRAT_tail': 'specimen_tail_drat', 
'delta_TR': 'specimen_dtr', 
'n_ptrm': 'specimen_int_ptrm_n', 
'max_ptrm_check': 'specimen_ptrm', 
'delta_CK': 'specimen_dck', 
'max_DEV': 'specimen_maxdev', 
'DRAT': 'specimen_drat', 
'mean_DRAT': 'specimen_mdrat', 
'CDRAT': 'specimen_cdrat', 
'DRATS': 'specimen_drats', 
'mean_DEV': 'specimen_mdev', 
'delta_pal': 'specimen_dpal', 
26: 'specimen_dt', 
'delta_AC': 'specimen_dac', 
'n_add' : 'specimen_ac_n', 
'specimen_k': 'specimen_k', 
'SSE': 'specimen_k_sse', 
'Z': 'specimen_z', 
'IZZI_MD': 'specimen_z_md', 
'SCAT': 'specimen_scat', 
27: 'specimen_viscosity_index', 28: 'specimen_lab_field_dc', 29: 'specimen_lab_field_ac', 30: 'specimen_magn_moment', 31: 'specimen_magn_volume', 32: 'specimen_magn_mass', 33: 'specimen_int_corr_cooling_rate', 34: 'specimen_int_corr_anisotropy', 35: 'specimen_int_corr_nlt', 
36: 'specimen_delta', 
'theta': 'specimen_theta', 
'gamma': 'specimen_gamma'}

#>>> SPD.spd.thing.pars.keys()
['AC_Checks_segment', 'B_anc', 'B_anc_sigma', 'B_lab', 'CDRAT', 'CDRAT_prime', 'DANG', 'DRAT', 'DRATS', 'DRATS_prime', 'DRAT_tail', 'Dec_Anc', 'Dec_Free', 'FRAC', 'GAP-MAX', 'IZZI_MD', 'Inc_Anc', 'Inc_Free', 'MAD_Anc', 'MAD_Free', 'MD_VDS', 'NRM_dev', 'PCA_sigma_int_Free', 'PCA_sigma_max_Free', 'PCA_sigma_min_Free', 'R_corr2', 'R_det2', 'SCAT', 'SSE', 'V_Anc', 'V_Free', 'Z', 'Zstar', 'alpha', 'best_fit_vector_Anc', 'best_fit_vector_Free', 'count_IZ', 'count_ZI', 'delta_AC', 'delta_CK', 'delta_TR', 'delta_pal', 'delta_x_prime', 'delta_y_prime', 'fail_arai_beta_box_scatter', 'fail_ptrm_beta_box_scatter', 'fail_tail_beta_box_scatter', 'gamma', 'lab_dc_field', 'length_best_fit_line', 'max_DEV', 'max_diff', 'max_ptrm_check', 'max_ptrm_check_percent', 'mean_DEV', 'mean_DEV_prime', 'mean_DRAT', 'mean_DRAT_prime', 'n_add', 'n_ptrm', 'n_tail', 'pTRM_MAD_Free', 'partial_vds', 'ptrm_cart', 'ptrm_checks', 'ptrm_checks_included_temps', 'ptrm_dir', 'ptrms_angle_Free', 'ptrms_dec_Free', 'ptrms_inc_Free', 'ptrms_tau_Free', 'scat_bounding_line_high', 'scat_bounding_line_low', 'specimen_XT', 'specimen_YT', 'specimen_b', 'specimen_b_beta', 'specimen_b_sigma', 'specimen_f', 'specimen_fvds', 'specimen_g', 'specimen_g_lim', 'specimen_int', 'specimen_k', 'specimen_n', 'specimen_q', 'specimen_vds', 'specimen_w', 'sum_abs_ptrm_checks', 'sum_ptrm_checks', 'tail_check_diffs', 'tail_check_max', 'tau_Anc', 'tau_Free', 'theta', 'tmax', 'tmin', 'vector_diffs', 'vector_diffs_segment', 'x_Arai_mean', 'x_err', 'x_prime', 'x_tag', 'y_Arai_mean', 'y_err', 'y_prime', 'y_tag', 'zdata_mass_center']


a_map = {'fail_ptrm_beta_box_scatter': 'fail_ptrm_beta_box_scatter', 'scat_bounding_line_low': 'specimen_scat_bounding_line_low', 'fail_tail_beta_box_scatter': 'fail_tail_beta_box_scatter', 'MD_VDS': 'specimen_md', 'B_anc': 'specimen_int_uT', 'FRAC': 'specimen_frac', 'Inc_Free': 'specimen_inc', 'best_fit_vector_Free': 'specimen_PCA_v1', 'specimen_b_sigma': 'specimen_b_sigma', 'specimen_YT': 'specimen_YT', 'y_Arai_mean': 'specimen_cm_y', 'SCAT': 'specimen_scat', 'MAD_Free': 'specimen_int_mad', 'n_ptrm': 'specimen_int_ptrm_n', 'tmin': 'measurement_step_min', 'x_Arai_mean': 'specimen_cm_x', 'Dec_Free': 'specimen_dec', 'DRATS': 'specimen_drats', 'specimen_fvds': 'specimen_fvds', 'specimen_b_beta': 'specimen_b_beta', 'specimen_b': 'specimen_b', 'specimen_g': 'specimen_g', 'fail_arai_beta_box_scatter': 'fail_arai_beta_box_scatter', 'specimen_f': 'specimen_f', 'tmax': 'measurement_step_max', 'specimen_n': 'specimen_int_n', 'specimen_q': 'specimen_q', 'lab_dc_field': 'lab_dc_field', 'GAP-MAX': 'specimen_gmax', 'DANG': 'specimen_int_dang', 'ptrms_angle_Free': 'specimen_ptrms_angle', 'scat_bounding_line_high': 'specimen_scat_bounding_line_high', 'PCA_sigma_max_Free': "specimen_PCA_sigma_max" , 'PCA_sigma_int_Free': 'specimen_PCA_sigma_int', 'PCA_sigma_min_Free': 'specimen_PCA_sigma_min', 'ptrms_dec_Free': 'specimen_ptrms_dec', 'ptrms_inc_Free': 'specimen_ptrms_inc', 'pTRM_MAD_Free': 'specimen_ptrms_mad'}
