#!/usr/bin/env python

# map_MagIC.py: -*- Python -*-  DESCRIPTIVE TEXT.
#
#  Copyright (c) 2014 Lori Jonestrask
#  Author: Lori Jonestrask (mintblue87@gmail.com) .

from __future__ import print_function
from __future__ import absolute_import
from builtins import zip
from builtins import str
import json
from pmagpy.data_model3 import DataModel
from . import maps


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
    for key, value in dictionary.items():
        if key in list(mapping.keys()):
            new_key = mapping[key]
            # if there is already a mapped value, try to figure out which value to use
            # (i.e., if both er_synthetic_name and er_specimen_name are in one measurement file)
            if new_key in mapped_dictionary:
                if hasattr(value,'any'):
                    if not value.any():
                        # if new value is null, leave the old value there
                        continue
                    if hasattr(mapped_dictionary,'any'):
                        if value.any() and not mapped_dictionary[new_key].any():
                            # choose the one that has a non-null value
                            mapped_dictionary[new_key] = value
                        elif value.any() and mapped_dictionary[new_key].any():
                            # if both have values, choose which one to replace and warn
                            print('-W- Two possible values found for {}'.format(new_key))
                            print('    Replacing {} with {}'.format(mapped_dictionary[new_key], value))
                            mapped_dictionary[new_key] = value
                    else:
                        if value.any() and not mapped_dictionary[new_key].any():
                            # choose the one that has a non-null value
                            mapped_dictionary[new_key] = value
                        elif value.any() and mapped_dictionary[new_key].any():
                            # if both have values, choose which one to replace and warn
                            print('-W- Two possible values found for {}'.format(new_key))
                            print('    Replacing {} with {}'.format(mapped_dictionary[new_key], value))
                            mapped_dictionary[new_key] = value
                else:
                    if not value:
                        # if new value is null, leave the old value there
                        continue
                    elif value and not mapped_dictionary[new_key]:
                        # choose the one that has a non-null value
                        mapped_dictionary[new_key] = value
                    elif value and mapped_dictionary[new_key]:
                        # if both have values, choose which one to replace and warn
                        print('-W- Two possible values found for {}'.format(new_key))
                        print('    Replacing {} with {}'.format(mapped_dictionary[new_key], value))
                        mapped_dictionary[new_key] = value
            # if there is no mapped_value already:
            else:
                mapped_dictionary[new_key] = value
        else:
            mapped_dictionary[key] = value # if this line is left in, it gives everything from the original dictionary
    return mapped_dictionary

#mapped_pars = mapping(Pint_pars.pars, a_map)

# mapping between SPD & Magic 2
spd = ['R_corr2', 'PCA_sigma_int_Free', 'PCA_sigma_max_Free', 'n_tail', 'delta_pal', 'DRAT_tail', 'MD_VDS', 'n_add', 'delta_AC', 'y_Arai_mean', 'MAD_Free', 'n_ptrm', 'DRAT', 'IZZI_MD', 'FRAC', 'CDRAT', 'Dec_Free', 'mean_DEV', 'DRATS', 'Z', 'max_DEV', 'fail_arai_beta_box_scatter', 'GAP-MAX', 'pTRM_MAD_Free', 'ptrms_dec_Free', 'MAD_Anc', 'fail_ptrm_beta_box_scatter', 'ptrms_angle_Free', 'scat_bounding_line_low', 'PCA_sigma_min_Free', 'B_anc', 'SCAT', 'R_det2', 'best_fit_vector_Free', 'specimen_b_beta', 'specimen_YT', 'delta_CK', 'lab_dc_field', 'Inc_Free', 'mean_DRAT', 'theta', 'max_ptrm_check', 'tmin', 'x_Arai_mean', 'fail_tail_beta_box_scatter', 'delta_TR', 'alpha', 'alpha_prime', 'specimen_fvds', 'specimen_b_sigma', 'specimen_b', 'specimen_g', 'specimen_f', 'tmax', 'specimen_int_n', 'specimen_q', 'DANG', 'ptrms_inc_Free', 'SSE', 'gamma', 'scat_bounding_line_high', 'specimen_k', 'specimen_int_crm', 'specimen_dt', 'specimen_k_prime', 'specimen_k_prime_SSE']

magic = ['specimen_coeff_det_sq', 'specimen_PCA_sigma_int', 'specimen_PCA_sigma_max', 'specimen_int_ptrm_tail_n', 'specimen_dpal', 'specimen_tail_drat', 'specimen_md', 'specimen_ac_n', 'specimen_dac', 'specimen_cm_y', 'specimen_int_mad', 'specimen_int_ptrm_n', 'specimen_drat', 'specimen_z_md', 'specimen_frac', 'specimen_cdrat', 'specimen_dec', 'specimen_mdev', 'specimen_drats', 'specimen_z', 'specimen_maxdev', 'fail_arai_beta_box_scatter', 'specimen_gmax', 'specimen_ptrms_mad', 'specimen_ptrms_dec', 'specimen_int_mad_anc', 'fail_ptrm_beta_box_scatter', 'specimen_ptrms_angle', 'specimen_scat_bounding_line_low', 'specimen_PCA_sigma_min', 'specimen_int_uT', 'specimen_scat', 'specimen_r_sq', 'specimen_PCA_v1', 'specimen_b_beta', 'specimen_YT', 'specimen_dck', 'lab_dc_field', 'specimen_inc', 'specimen_mdrat', 'specimen_theta', 'specimen_ptrm', 'measurement_step_min', 'specimen_cm_x', 'fail_tail_beta_box_scatter', 'specimen_dtr', 'specimen_int_alpha', 'specimen_alpha_prime', 'specimen_fvds', 'specimen_b_sigma', 'specimen_b', 'specimen_g', 'specimen_f', 'measurement_step_max', 'specimen_int_n', 'specimen_q', 'specimen_int_dang', 'specimen_ptrms_inc', 'specimen_k_sse', 'specimen_gamma', 'specimen_scat_bounding_line_high', 'specimen_k', 'specimen_int_crm', 'specimen_dt', 'specimen_k_prime', 'specimen_k_prime_sse']

spd2magic_map = dict(list(zip(spd, magic)))
magic2spd_map = dict(list(zip(magic, spd)))


def cache_mappings(dir_path):
    """
    Make a full mapping for 2 --> 3 columns.
    Output the mapping to json in the specified dir_path.
    Note: This file is currently called maps.py
    and lives in PmagPy/pmagpy/mapping.
    To match the current format of maps.py,
    you will need to add `all_maps = ` at the beginning
    of the file.

    Parameters
    ----------
    dir_path : string with full file path to dump mapping json.

    Returns
    ---------
    maps : nested dictionary with format {table_name: {magic2_col_name: magic3_col_name, ...}, ...}
    """
    def get_2_to_3(dm_type, dm):
        table_names3_2_table_names2 = {'measurements': ['magic_measurements'],
                                       'locations': ['er_locations'],
                                       'sites': ['er_sites', 'pmag_sites'],
                                       'samples': ['er_samples', 'pmag_samples'],
                                       'specimens': ['er_specimens', 'pmag_specimens'],
                                       'ages': ['er_ages'],
                                       'criteria': ['pmag_criteria'],
                                       'images': ['er_images'],
                                       'contribution': []}
        table_names3 = table_names3_2_table_names2[dm_type]
        dictionary = {}
        for label, row in dm.iterrows():
            if isinstance(row['previous_columns'], list):
                for previous_values in row['previous_columns']:
                    previous_table = previous_values['table']
                    previous_value = previous_values['column']
                    #print 'previous_table', previous_table
                    if previous_table in table_names3:
                        #print label, ":", row['previous_columns'][0]['column']
                        dictionary[previous_value] = label
        return dictionary
    # begin
    data_model = DataModel()
    maps = {}
    for table_name in data_model.dm:
        dm = data_model.dm[table_name]
        new_mapping = get_2_to_3(table_name, dm)
        maps[table_name] = new_mapping
    # write maps out to file
    f = open(dir_path, 'w')
    json.dump(maps, f)
    f.close()
    return maps


# Mappings between magic2 and magic3


add_to_all = {'er_location_name': 'location', 'er_site_name': 'site',
              'er_sample_name': 'sample', 'er_specimen_name': 'specimen',
              'er_sample_names': 'samples', 'er_specimen_names': 'specimens'}

#measurement data translation measurements.txt -> magic_measurements.txt
meas_magic2_2_magic3_map = maps.all_maps['measurements']
meas_magic2_2_magic3_map.update(add_to_all)
#measurement data translation magic_measurements.txt -> measurements.txt
meas_magic3_2_magic2_map = {v:k for k,v in list(meas_magic2_2_magic3_map.items())}
measurements = {'timestamp': 'measurement_date',
                'specimen': 'er_specimen_name',
                'number': 'measurement_number'}
meas_magic3_2_magic2_map.update(measurements)

#specimen data translation pmag_speciemns,er_specimens -> specimens.txt
spec_magic2_2_magic3_map = maps.all_maps['specimens']
spec_magic2_2_magic3_map.update(add_to_all)
spec_magic3_2_magic2_map = {v:k for k,v in list(spec_magic2_2_magic3_map.items())}
specimens = {'external_database_ids': 'external_database_ids',
             'dir_comp': 'specimen_comp_name', 'specimen': 'er_specimen_name'}
spec_magic3_2_magic2_map.update(specimens)

# sample data translation pmag_samples/er_samples => samples
samp_magic2_2_magic3_map = maps.all_maps['samples']
samp_magic2_2_magic3_map.update(add_to_all)
#sample data translation samples => pmag_samples/er_samples
samp_magic3_2_magic2_map = {v:k for k,v in list(samp_magic2_2_magic3_map.items())}
samples = {'specimens': 'er_specimen_names', 'dir_comp_name': 'sample_comp_name',
           'timestamp': 'sample_date', 'external_database_ids': 'external_database_ids'}
samp_magic3_2_magic2_map.update(samples)

#site data translation pmag_sites,er_sites -> sites.txt
site_magic2_2_magic3_map = maps.all_maps['sites']
site_magic2_2_magic3_map.update(add_to_all)
# site data translation er_sites/pmag_sites --> sites
site_magic3_2_magic2_map = {v: k for k, v in list(site_magic2_2_magic3_map.items())}
sites = {'dir_comp_name': 'site_comp_name', 'specimens': 'er_specimen_names'}
site_magic3_2_magic2_map.update(sites)

# location data translation er_locations -> locations
loc_magic2_2_magic3_map = maps.all_maps['locations']
loc_magic2_2_magic3_map.update(add_to_all)
locations = {'location_begin_lat': 'lat_s', 'location_begin_lon': 'lon_e',
             'location_end_lat': 'lat_n', 'location_end_lon': 'lon_w'}
loc_magic2_2_magic3_map.update(locations)
# location data translation locations -> er_locations
loc_magic3_2_magic2_map = {v: k for k, v in list(loc_magic2_2_magic3_map.items())}
locations = {'lat_s': 'location_begin_lat', 'lat_n': 'location_end_lat',
             'lon_e': 'location_begin_lon', 'lon_w': 'location_end_lon'}
loc_magic3_2_magic2_map.update(locations)

# anisotropy mapping
aniso_magic3_2_magic2_map={'specimen':'er_specimen_name', 'aniso_type':'anisotropy_type', 'description':'result_description', 'aniso_ftest':'anisotropy_ftest', 'aniso_ftest12':'anisotropy_ftest12', 'aniso_ftest23':'anisotropy_ftest23', 'aniso_s_mean':'anisotropy_mean', 'aniso_s_n_measurements':'anisotropy_n', 'aniso_s_sigma':'anisotropy_sigma', 'aniso_s_unit':'anisotropy_unit', 'aniso_tilt_correction':'anisotropy_tilt_correction',"aniso_alt":'anisotropy_alt','experiments':'magic_experiment_names'}

aniso_magic2_2_magic3_map={'anisotropy_ftest23': 'aniso_ftest23', 'anisotropy_ftest': 'aniso_ftest', 'anisotropy_sigma': 'aniso_s_sigma', 'anisotropy_type': 'aniso_type', 'anisotropy_ftest12': 'aniso_ftest12', 'anisotropy_tilt_correction': 'aniso_tilt_correction', 'er_specimen_name': 'specimen', 'anisotropy_unit': 'aniso_s_unit', 'anisotropy_mean': 'aniso_s_mean', 'result_description': 'description', 'anisotropy_n': 'aniso_s_n_measurements','pmag_criteria_codes':'criteria','result_quality':'result_quality','anisotropy_alt':'aniso_alt','magic_method_codes':'method_codes','magic_experiment_names':'experiments'}

# images data translation er_images -> images
image_magic2_2_magic3_map = maps.all_maps['images']
# images data translation images -> er_images
image_magic2_2_magic_3_map = {v: k for (k, v) in list(image_magic2_2_magic3_map.items())}
images = {'specimen': 'er_specimen_name', 'description': 'image_description',
          'timestamp': 'image_date'}
image_magic2_2_magic3_map.update(images)

# ages data translation er_ages -> ages
age_magic2_2_magic3_map = maps.all_maps['ages']
# images data translation images -> er_images
age_magic2_2_magic_3_map = {v: k for (k, v) in list(age_magic2_2_magic3_map.items())}
#images = {'specimen': 'er_specimen_name', 'description': 'image_description',
#          'timestamp': 'image_date'}
#image_magic2_2_magic3_map.update(images)


## translation orientation format --> 3.0.
# orientation headers: not all have a 3.0 sample equivalent (like mag_azimuth, for instance)
#site_name sample_name mag_azimuth field_dip date lat long sample_lithology sample_type sample_class shadow_angle hhmm stratigraphic_height bedding_dip_direction bedding_dip GPS_baseline image_name image_look image_photographer participants method_codes site_description sample_description GPS_Az, sample_igsn, sample_texture, sample_cooling_rate, cooling_rate_corr, cooling_rate_mcd

orient_magic_2_magic3_map = {"sample_name": "sample", "site_name": "site", "long": "lon",
                             "sample_lithology": "lithologies", "sample_type": "geologic_types",
                             "sample_class": "geologic_classes"}
# 3.0 --> orientation format
magic3_2_orient_magic_map = {v: k for (k, v) in list(orient_magic_2_magic3_map.items())}

meas_magic2 = list(meas_magic3_2_magic2_map.values())
spec_magic2 = list(spec_magic3_2_magic2_map.values())
samp_magic2 = list(samp_magic3_2_magic2_map.values())
site_magic2 = list(site_magic3_2_magic2_map.values())

#meas_magic3 = meas_magic3_2_magic2_map.keys()  # why are these here?
spec_magic3 = list(spec_magic2_2_magic3_map.keys())
#samp_magic3 = samp_magic3_2_magic2_map.keys()
site_magic3 = list(site_magic3_2_magic2_map.keys())


# Data conversion for specific types of data

def convert_intensity_criteria(direction,crit):
    magic2 = ['specimen_coeff_det_sq', 'specimen_int_ptrm_tail_n', 'specimen_dpal', 'specimen_tail_drat', 'specimen_md', 'specimen_ac_n', 'specimen_dac',  'specimen_int_mad', 'specimen_int_ptrm_n', 'specimen_drat', 'specimen_z_md', 'specimen_frac', 'specimen_cdrat', 'specimen_dec', 'specimen_mdev', 'specimen_drats', 'specimen_z', 'specimen_maxdev', 'specimen_gmax', 'specimen_int_mad_anc', 'specimen_scat', 'specimen_r_sq', 'specimen_b_beta', 'specimen_dck', 'lab_dc_field', 'specimen_inc', 'specimen_mdrat', 'specimen_theta', 'specimen_ptrm', 'measurement_step_min', 'specimen_dtr', 'specimen_int_alpha', 'specimen_fvds', 'specimen_b_sigma', 'specimen_b', 'specimen_g', 'specimen_f', 'measurement_step_max', 'specimen_int_n', 'specimen_q', 'specimen_int_dang', 'specimen_k_sse', 'specimen_gamma', 'specimen_k', 'specimen_int_crm', 'specimen_dt', 'specimen_k_prime', 'specimen_k_prime_sse','sample_int_n','sample_int_sigma_perc','sample_int_sigma','site_int_n','site_int_sigma_perc','site_int_sigma','pmag_criteria_code','sample_aniso_mean','specimen_aniso_ftest_flag','anisotropy_alt','site_aniso_mean']

    magic3 = ['specimens.int_r2_det', 'specimens.int_n_ptrm_tail', 'specimens.int_dpal', 'specimens.int_drat_tail', 'specimens.int_md', 'specimens.int_n_ac', 'specimens.int_dac', 'specimens.int_mad_free', 'specimens.int_n_ptrm', 'specimens.int_drat', 'specimens.int_z_md', 'specimens.int_frac', 'specimens.int_cdrat', 'specimens.dir_dec', 'specimens.int_mdev', 'specimens.int_drats', 'specimens.int_z', 'specimens.int_maxdev', 'specimens.int_gmax', 'specimens.int_mad_anc', 'specimens.int_scat', 'specimens.int_r2_corr', 'specimens.int_b_beta', 'specimens.int_dck', 'specimens.treat_dc_field', 'specimens.dir_inc', 'specimens.int_mdrat', 'specimens.int_theta', 'specimens.int_ptrm', 'specimens.meas_step_min', 'specimens.int_dtr', 'specimens.int_alpha', 'specimens.int_fvds', 'specimens.int_b_sigma', 'specimens.int_b', 'specimens.int_g', 'specimens.int_f', 'specimens.meas_step_max', 'specimens.int_n_measurements', 'specimens.int_q', 'specimens.int_dang',  'specimens.int_k_sse', 'specimens.int_gamma', 'specimens.int_k', 'specimens.int_crm', 'specimens.int_dt', 'specimens.int_k_prime', 'specimens.int_k_prime_sse','samples.int_n_specimens','samples.int_abs_sigma_perc','samples.int_abs_sigma','sites.int_n_specimens','sites.int_abs_sigma_perc','sites.int_abs_sigma','criterion','samples.int_corr_aniso_mean','specimens.aniso_ftest_flag','specimens.aniso_alt','sites.int_corr_aniso_mean']
    if direction=='magic2':
        if crit in magic3:
            return magic2[magic3.index(crit)]
        else:
            return ""
    else:
        if crit in magic2:
            return magic3[magic2.index(crit)]
        else:
            return crit

def convert_direction_criteria(direction,crit):
    if direction=='magic2':
        try:
            if 'specimens.' in crit:
                return spec_magic3_2_magic2_map[crit.lstrip('specimens.')]
            elif 'samples.' in crit:
                return samp_magic3_2_magic2_map[crit.lstrip('samples.')]
            elif 'sites.' in crit:
                return site_magic3_2_magic2_map[crit.lstrip('sites.')]
            else:
                return ""
        except KeyError as e: return ""
    else:
        try:
            if 'specimen' in crit:
                return 'specimens.' + spec_magic2_2_magic3_map[crit]
            elif 'sample' in crit:
                return 'samples.' + samp_magic2_2_magic3_map[crit]
            elif 'site' in crit:
                return 'sites.' + site_magic2_2_magic3_map[crit]
            else:
                return ""
        except KeyError as e: return ""

def convert_meas(direction,Rec):
    if direction=='magic3':
        columns=meas_magic2_2_magic3_map
        MeasRec={}
        for key in columns:
            if key in list(Rec.keys()):
                MeasRec[columns[key]]=Rec[key] # transfer info and change column name to data model 3.0
        return MeasRec
    else: # haven't added this way yet
        pass

def convert_spec(direction,Rec):
    if direction=='magic3':
        columns=spec_magic2_2_magic3_map
        SpecRec={}
        for key in columns:
            if key in list(Rec.keys()):
                SpecRec[columns[key]]=Rec[key] # transfer info and change column name to data model 3.0
        return SpecRec
    else: # haven't added this way yet
        pass

def convert_samp(direction,Rec):
    if direction=='magic3':
        columns=samp_magic2_2_magic3_map
        SampRec={}
        for key in columns:
            if key in list(Rec.keys()):
                SampRec[columns[key]]=Rec[key] # transfer info and change column name to data model 3.0
        return SampRec
    else: # haven't added this way yet
        pass

def convert_site(direction,Rec):
    if direction=='magic3':
        columns=site_magic2_2_magic3_map
        SiteRec={}
        for key in columns:
            if key in list(Rec.keys()):
                SiteRec[columns[key]]=Rec[key] # transfer info and change column name to data model 3.0
        return SiteRec
    else: # haven't added this way yet
        pass


def convert_aniso(direction,AniSpec):
    if direction=='magic2':
        columns=aniso_magic3_2_magic2_map
        AniRec={}
        s_data=AniSpec['aniso_s'].split(':')
        for key in columns:
            if key in list(AniSpec.keys()):
                AniRec[columns[key]]=AniSpec[key] # transfer info and change column name to data model 2.5
        AniRec['anisotropy_s1']=s_data[0]# need to add these things
        AniRec['anisotropy_s2']=s_data[1]
        AniRec['anisotropy_s3']=s_data[2]
        AniRec['anisotropy_s4']=s_data[3]
        AniRec['anisotropy_s5']=s_data[4]
        AniRec['anisotropy_s6']=s_data[5]
        AniRec['anisotropy_F_crit']=""
        if 'result_description'  in list(AniSpec.keys()):
            result_description=AniSpec['result_description'].split(";")
            for description in result_description:
              if "Critical F" in description:
                 desc=description.split(":")
                 AniRec['anisotropy_F_crit']=float(desc[1])
        return AniRec # converted to 2.5
    else:  # upgrade to 3.0
        columns=aniso_magic2_2_magic3_map
        # first fix aniso_s
        AniRec={}
        for key in columns:
            if key in list(AniSpec.keys()):
                AniRec[columns[key]]=AniSpec[key] # transfer info and change column name to data model 3.0
        s_string=""
        s_string=s_string+ str(AniSpec['anisotropy_s1']) +' : '
        s_string=s_string+ str(AniSpec['anisotropy_s2']) +' : '
        s_string=s_string+ str(AniSpec['anisotropy_s3']) +' : '
        s_string=s_string+ str(AniSpec['anisotropy_s4']) +' : '
        s_string=s_string+ str(AniSpec['anisotropy_s5']) +' : '
        s_string=s_string+ str(AniSpec['anisotropy_s6'])
        AniRec['aniso_s']=s_string
        # do V1, etc.  here
#V1:  Anisotropy eigenparameters for the maximum eigenvalue (T1), a colon-delimited list of tau (T1), dec, inc, confidence ellipse type, and confidence ellipse parameters
        v_string=AniSpec['anisotropy_t1']+" : "+AniSpec['anisotropy_v1_dec']+" : "+AniSpec['anisotropy_v1_inc']
        AniRec['aniso_v1']=v_string
        v_string=AniSpec['anisotropy_t2']+" : "+AniSpec['anisotropy_v2_dec']+" : "+AniSpec['anisotropy_v2_inc']
        AniRec['aniso_v2']=v_string
        v_string=AniSpec['anisotropy_t3']+" : "+AniSpec['anisotropy_v3_dec']+" : "+AniSpec['anisotropy_v3_inc']
        AniRec['aniso_v3']=v_string
        return AniRec
