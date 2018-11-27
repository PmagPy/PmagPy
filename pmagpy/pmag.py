from past.utils import old_div
import codecs
import numpy as np
import string
import sys
from numpy import random
from numpy import linalg
import os
import time
import math
import pandas as pd
from .mapping import map_magic
from pmagpy import contribution_builder as cb
from . import find_pmag_dir
from pmag_env import set_env

WARNINGS = {'basemap': False, 'cartopy': False}


def get_version():
    """
    Determines the version of PmagPy installed on your machine.

    Returns
    ---------
    version : string of pmagpy version, such as "pmagpy-3.8.8"
    """
    version = find_pmag_dir.get_version()
    return version


def sort_diclist(undecorated, sort_on):
    """
    Sort a list of dictionaries by the value in each
    dictionary for the sorting key

    Parameters
    ----------
    undecorated : list of dicts
    sort_on : str, numeric
        key that is present in all dicts to sort on

    Returns
    ---------
    ordered list of dicts

    Examples
    ---------
    >>> lst = [{'key1': 10, 'key2': 2}, {'key1': 1, 'key2': 20}]
    >>> sort_diclist(lst, 'key1')
    [{'key2': 20, 'key1': 1}, {'key2': 2, 'key1': 10}]
    >>> sort_diclist(lst, 'key2')
    [{'key2': 2, 'key1': 10}, {'key2': 20, 'key1': 1}]
    """
    decorated = [(len(dict_[sort_on]) if hasattr(dict_[sort_on], '__len__') else dict_[
                  sort_on], index) for (index, dict_) in enumerate(undecorated)]
    decorated.sort()
    return[undecorated[index] for (key, index) in decorated]


def get_dictitem(In, k, v, flag, float_to_int=False):
    """ returns a list of dictionaries from list In with key,k  = value, v . CASE INSENSITIVE # allowed keywords:
        requires that the value of k in the dictionaries contained in In be castable to string and requires that v be castable to a string if flag is T,F
        ,has or not and requires they be castable to float if flag is eval, min, or max.
        float_to_int goes through the relvant values in In and truncates them,
        (like "0.0" to "0") for evaluation, default is False

    Parameters
    __________
        In : list of dictionaries to work on
        k : key to test
        v : key value to test
        flag : [T,F,has, or not]
        float_to int : if True, truncates to integer
    Returns
    ______
        list of dictionaries that meet condition
    """
    if float_to_int:
        try:
            v = str(math.trunc(float(v)))
        except ValueError:  # catches non floatable strings
            pass
        except TypeError:  # catches None
            pass
        fixed_In = []
        for dictionary in In:
            if k in dictionary:
                val = dictionary[k]
                try:
                    val = str(math.trunc(float(val)))
                except ValueError:  # catches non floatable strings
                    pass
                except TypeError:  # catches None
                    pass
                dictionary[k] = val
            fixed_In.append(dictionary)
        In = fixed_In
    if flag == "T":
        # return that which is
        return [dictionary for dictionary in In if k in list(dictionary.keys()) and str(dictionary[k]).lower() == str(v).lower()]
    if flag == "F":
        # return that which is not
        return [dictionary for dictionary in In if k in list(dictionary.keys()) and str(dictionary[k]).lower() != str(v).lower()]
    if flag == "has":
        # return that which is contained
        return [dictionary for dictionary in In if k in list(dictionary.keys()) and str(v).lower() in str(dictionary[k]).lower()]
    if flag == "not":
        # return that which is not contained
        return [dictionary for dictionary in In if k in list(dictionary.keys()) and str(v).lower() not in str(dictionary[k]).lower()]
    if flag == "eval":
        A = [dictionary for dictionary in In if k in list(dictionary.keys(
        )) and dictionary[k] != '']  # find records with no blank values for key
        # return that which is
        return [dictionary for dictionary in A if k in list(dictionary.keys()) and float(dictionary[k]) == float(v)]
    if flag == "min":
        A = [dictionary for dictionary in In if k in list(dictionary.keys(
        )) and dictionary[k] != '']  # find records with no blank values for key
        # return that which is greater than
        return [dictionary for dictionary in A if k in list(dictionary.keys()) and float(dictionary[k]) >= float(v)]
    if flag == "max":
        A = [dictionary for dictionary in In if k in list(dictionary.keys(
        )) and dictionary[k] != '']  # find records with no blank values for key
        # return that which is less than
        return [dictionary for dictionary in A if k in list(dictionary.keys()) and float(dictionary[k]) <= float(v)]
    if flag == 'not_null':
        return [dictionary for dictionary in In if dictionary[k]]


def get_dictkey(In, k, dtype):
    """
        returns list of given key (k)  from input list of dictionaries (In) in data type dtype.  uses command:
        get_dictkey(In,k,dtype).  If dtype =="", data are strings; if "int", data are integers; if "f", data are floats.
    """

    Out = []
    for d in In:
        if dtype == '':
            Out.append(d[k])
        if dtype == 'f':
            if d[k] == "":
                Out.append(0)
            elif d[k] == None:
                Out.append(0)
            else:
                Out.append(float(d[k]))
        if dtype == 'int':
            if d[k] == "":
                Out.append(0)
            elif d[k] == None:
                Out.append(0)
            else:
                Out.append(int(d[k]))
    return Out


def find(f, seq):
    for item in seq:
        if f in item:
            return item
    return ""


def get_orient(samp_data, er_sample_name, **kwargs):
    # set orientation priorities
    EX = ["SO-ASC", "SO-POM"]
    samp_key, az_key, dip_key = 'er_sample_name', 'sample_azimuth', 'sample_dip'
    disc_key, or_key, meth_key = 'sample_description', 'sample_orientation_flag',\
        'magic_method_codes'
    if 'data_model' in list(kwargs.keys()) and kwargs['data_model'] == 3:
        samp_key, az_key, dip_key = 'sample', 'azimuth', 'dip'
        disc_key, or_key, meth_key = 'description', 'orientation_quality',\
            'method_codes'
    orient = {samp_key: er_sample_name, az_key: "",
              dip_key: "", disc_key: ""}
    # get all the orientation data for this sample
    orients = get_dictitem(samp_data, samp_key, er_sample_name, 'T')
    if len(orients) > 0 and or_key in list(orients[0].keys()):
        # exclude all samples with bad orientation flag
        orients = get_dictitem(orients, or_key, 'b', 'F')
    if len(orients) > 0:
        orient = orients[0]  # re-initialize to first one
    methods = get_dictitem(orients, meth_key, 'SO-', 'has')
    # get a list of all orientation methods for this sample
    methods = get_dictkey(methods, meth_key, '')
    SO_methods = []
    for methcode in methods:
        meths = methcode.split(":")
        for meth in meths:
            if meth.strip() not in EX:
                SO_methods.append(meth.strip())
    # find top priority orientation method
    if len(SO_methods) == 0:
        print("no orientation data for sample ", er_sample_name)
        # preserve meta-data anyway even though orientation is bad
# get all the orientation data for this sample
        orig_data = get_dictitem(samp_data, samp_key, er_sample_name, 'T')
        if len(orig_data) > 0:
            orig_data = orig_data[0]
        else:
            orig_data = []
        az_type = "SO-NO"
    else:
        SO_priorities = set_priorities(SO_methods, 0)
        az_type = SO_methods[SO_methods.index(SO_priorities[0])]
        orient = get_dictitem(orients, meth_key, az_type, 'has')[
            0]  # re-initialize to best one
    return orient, az_type


def EI(inc):
    """
    Given a mean inclination value of a distribution of directions, this
    function calculates the expected elongation of this distribution using a
    best-fit polynomial of the TK03 GAD secular variation model (Tauxe and
    Kent, 2004).

    Parameters
    ----------
    inc : inclination in degrees (int or float)

    Returns
    ---------
    elongation : float

    Examples
    ---------
    >>> pmag.EI(20)
    2.4863973732
    >>> pmag.EI(90)
    1.0241570135500004
    """
    poly_tk03 = [3.15976125e-06,  -3.52459817e-04,  -
                 1.46641090e-02,   2.89538539e+00]
    return poly_tk03[0] * inc**3 + poly_tk03[1] * inc**2 + poly_tk03[2] * inc + poly_tk03[3]


def find_f(data):
    """
    Given a distribution of directions, this function determines parameters
    (elongation, inclination, flattening factor, and elongation direction) that
    are consistent with the TK03 secular variation model.

    Parameters
    ----------
    data : array of declination, inclination pairs
        (e.g. np.array([[140,21],[127,23],[142,19],[136,22]]))

    Returns
    ---------
    Es : list of elongation values
    Is : list of inclination values
    Fs : list of flattening factors
    V2s : list of elongation directions (relative to the distribution)

    The function will return a zero list ([0]) for each of these parameters if the directions constitute a pathological distribution.

    Examples
    ---------
    >>> directions = np.array([[140,21],[127,23],[142,19],[136,22]])
    >>> Es, Is, Fs, V2s = pmag.find_f(directions)
    """
    rad = np.pi/180.
    Es, Is, Fs, V2s = [], [], [], []
    ppars = doprinc(data)
    D = ppars['dec']
    Decs, Incs = data.transpose()[0], data.transpose()[1]
    Tan_Incs = np.tan(Incs * rad)
    for f in np.arange(1., .2, -.01):
        U = old_div(np.arctan((old_div(1., f)) * Tan_Incs), rad)
        fdata = np.array([Decs, U]).transpose()
        ppars = doprinc(fdata)
        Fs.append(f)
        Es.append(old_div(ppars["tau2"], ppars["tau3"]))
        ang = angle([D, 0], [ppars["V2dec"], 0])
        if 180. - ang < ang:
            ang = 180. - ang
        V2s.append(ang)
        Is.append(abs(ppars["inc"]))
        if EI(abs(ppars["inc"])) <= Es[-1]:
            del Es[-1]
            del Is[-1]
            del Fs[-1]
            del V2s[-1]
            if len(Fs) > 0:
                for f in np.arange(Fs[-1], .2, -.005):
                    U = old_div(np.arctan((old_div(1., f)) * Tan_Incs), rad)
                    fdata = np.array([Decs, U]).transpose()
                    ppars = doprinc(fdata)
                    Fs.append(f)
                    Es.append(old_div(ppars["tau2"], ppars["tau3"]))
                    Is.append(abs(ppars["inc"]))
                    ang = angle([D, 0], [ppars["V2dec"], 0])
                    if 180. - ang < ang:
                        ang = 180. - ang
                    V2s.append(ang)
                    if EI(abs(ppars["inc"])) <= Es[-1]:
                        return Es, Is, Fs, V2s
    return [0], [0], [0], [0]


def cooling_rate(SpecRec, SampRecs, crfrac, crtype):
    CrSpecRec, frac, crmcd = {}, 0, 'DA-CR'
    for key in list(SpecRec.keys()):
        CrSpecRec[key] = SpecRec[key]
    if len(SampRecs) > 0:
        frac = .01 * float(SampRecs[0]['cooling_rate_corr'])
        if 'DA-CR' in SampRecs[0]['cooling_rate_mcd']:
            crmcd = SampRecs[0]['cooling_rate_mcd']
        else:
            crmcd = 'DA-CR'
    elif crfrac != 0:
        frac = crfrac
        crmcd = crtype
    if frac != 0:
        inten = frac * float(CrSpecRec['specimen_int'])
        # adjust specimen intensity by cooling rate correction
        CrSpecRec["specimen_int"] = '%9.4e ' % (inten)
        CrSpecRec['magic_method_codes'] = CrSpecRec['magic_method_codes'] + ':crmcd'
        CrSpecRec["specimen_correction"] = 'c'
        return CrSpecRec
    else:
        return []


def convert_lat(Recs):
    """
    uses lat, for age<5Ma, model_lat if present, else tries to use average_inc to estimate plat.
    """
    New = []
    for rec in Recs:
        if 'model_lat' in list(rec.keys()) and rec['model_lat'] != "":
            New.append(rec)
        elif 'average_age' in list(rec.keys()) and rec['average_age'] != "" and float(rec['average_age']) <= 5.:
            if 'site_lat' in list(rec.keys()) and rec['site_lat'] != "":
                rec['model_lat'] = rec['site_lat']
                New.append(rec)
        elif 'average_inc' in list(rec.keys()) and rec['average_inc'] != "":
            rec['model_lat'] = '%7.1f' % (plat(float(rec['average_inc'])))
            New.append(rec)
    return New


def convert_ages(Recs, data_model=3):
    """
    converts ages to Ma
    Parameters
    _________
    Recs : list of dictionaries in data model by data_model
    data_model : MagIC data model (default is 3)
    """
    if data_model == 3:
        site_key = 'site'
        agekey = "age"
        keybase = ""
    else:
        site_key = 'er_site_names'
        agekey = find('age', list(rec.keys()))
        if agekey != "":
            keybase = agekey.split('_')[0] + '_'

    New = []
    for rec in Recs:
        age = ''
        if rec[keybase + 'age'] != "":
            age = float(rec[keybase + "age"])
        elif rec[keybase + 'age_low'] != "" and rec[keybase + 'age_high'] != '':
            age = np.mean([rec[keybase + 'age_high'],
                           rec[keybase + "age_low"]])
            # age = float(rec[keybase + 'age_low']) + old_div(
            #    (float(rec[keybase + 'age_high']) - float(rec[keybase + 'age_low'])), 2.)
        if age != '':
            rec[keybase + 'age_unit']
            if rec[keybase + 'age_unit'] == 'Ma':
                rec[keybase + 'age'] = '%10.4e' % (age)
            elif rec[keybase + 'age_unit'] == 'ka' or rec[keybase + 'age_unit'] == 'Ka':
                rec[keybase + 'age'] = '%10.4e' % (age * .001)
            elif rec[keybase + 'age_unit'] == 'Years AD (+/-)':
                rec[keybase + 'age'] = '%10.4e' % ((2011 - age) * 1e-6)
            elif rec[keybase + 'age_unit'] == 'Years BP':
                rec[keybase + 'age'] = '%10.4e' % ((age) * 1e-6)
            rec[keybase + 'age_unit'] = 'Ma'
            New.append(rec)
        else:
            if 'site_key' in list(rec.keys()):
                print('problem in convert_ages:', rec['site_key'])
            elif 'er_site_name' in list(rec.keys()):
                print('problem in convert_ages:', rec['site_key'])
            else:
                print('problem in convert_ages:', rec)
        if len(New) == 0:
            print('no age key:', rec)
    return New


# Converting from 2.5 --> 3.0

def convert_meas_2_to_3(meas_data_2):
    NewMeas = []
# step through records
    for rec in meas_data_2:
        NewMeas.append(map_magic.convert_meas('magic3', rec))
    return NewMeas


def convert_items(data, mapping):
    """
    Input: list of dicts (each dict a record for one item),
    mapping with column names to swap into the records.
    Output: updated list of dicts.
    """
    new_recs = []
    for rec in data:
        new_rec = map_magic.mapping(rec, mapping)
        new_recs.append(new_rec)
    return new_recs


def convert_directory_2_to_3(meas_fname="magic_measurements.txt", input_dir=".",
                             output_dir=".", meas_only=False, data_model=None):
    """
    Convert 2.0 measurements file into 3.0 measurements file.
    Merge and convert specimen, sample, site, and location data.
    Also translates criteria data.

    Parameters
    ----------
    meas_name : name of measurement file (do not include full path,
        default is "magic_measurements.txt")
    input_dir : name of input directory (default is ".")
    output_dir : name of output directory (default is ".")
    meas_only : boolean, convert only measurement data (default is False)
    data_model : data_model3.DataModel object (default is None)

    Returns
    ---------
    NewMeas : 3.0 measurements data (output of pmag.convert_items)
    upgraded : list of files successfully upgraded to 3.0
    no_upgrade: list of 2.5 files not upgraded to 3.0
    """
    convert = {'specimens': map_magic.spec_magic2_2_magic3_map,
               'samples': map_magic.samp_magic2_2_magic3_map,
               'sites': map_magic.site_magic2_2_magic3_map,
               'locations': map_magic.loc_magic2_2_magic3_map,
               'ages': map_magic.age_magic2_2_magic3_map}
    full_name = os.path.join(input_dir, meas_fname)
    if not os.path.exists(full_name):
        print("-W- {} is not a file".format(full_name))
        return False, False, False
    # read in data model 2.5 measurements file
    data2, filetype = magic_read(full_name)
    # convert list of dicts to 3.0
    NewMeas = convert_items(data2, map_magic.meas_magic2_2_magic3_map)
    # write 3.0 output to file
    ofile = os.path.join(output_dir, 'measurements.txt')
    magic_write(ofile, NewMeas, 'measurements')
    upgraded = []
    if os.path.exists(ofile):
        print("-I- 3.0 format measurements file was successfully created: {}".format(ofile))
        upgraded.append("measurements.txt")
    else:
        print("-W- 3.0 format measurements file could not be created")
    #
    no_upgrade = []
    if not meas_only:
        # try to convert specimens, samples, sites, & locations
        for dtype in ['specimens', 'samples', 'sites', 'locations', 'ages']:
            mapping = convert[dtype]
            res = convert_and_combine_2_to_3(
                dtype, mapping, input_dir, output_dir, data_model)
            if res:
                upgraded.append(res)
        # try to upgrade criteria file
        if os.path.exists(os.path.join(input_dir, 'pmag_criteria.txt')):
            crit_file = convert_criteria_file_2_to_3(input_dir=input_dir,
                                                     output_dir=output_dir,
                                                     data_model=data_model)[0]
            if crit_file:
                upgraded.append(crit_file)
            else:
                no_upgrade.append("pmag_criteria.txt")
        # create list of all un-upgradeable files
        for fname in os.listdir(input_dir):
            if fname in ['measurements.txt', 'specimens.txt', 'samples.txt',
                         'sites.txt', 'locations.txt']:
                continue
            elif 'rmag' in fname:
                no_upgrade.append(fname)
            elif fname in ['pmag_results.txt', 'er_synthetics.txt', 'er_images.txt',
                           'er_plots.txt']:
                no_upgrade.append(fname)

    return NewMeas, upgraded, no_upgrade


def convert_and_combine_2_to_3(dtype, map_dict, input_dir=".", output_dir=".", data_model=None):
    """
    Read in er_*.txt file and pmag_*.txt file in working directory.
    Combine the data, then translate headers from 2.5 --> 3.0.
    Last, write out the data in 3.0.

    Parameters
    ----------
    dtype : string for input type (specimens, samples, sites, etc.)
    map_dict : dictionary with format {header2_format: header3_format, ...} (from mapping.map_magic module)
    input_dir : input directory, default "."
    output_dir : output directory, default "."
    data_model : data_model3.DataModel object, default None

    Returns
    ---------
    output_file_name with 3.0 format data (or None if translation failed)
    """
    # read in er_ data & make DataFrame
    er_file = os.path.join(input_dir, 'er_{}.txt'.format(dtype))
    er_data, er_dtype = magic_read(er_file)
    if len(er_data):
        er_df = pd.DataFrame(er_data)
        if dtype == 'ages':
            pass
            # remove records with blank ages
            #er_data = get_dictitem(er_data, 'age', '', "F")
            #er_df = pd.DataFrame(er_data)
        else:
            er_df.index = er_df['er_{}_name'.format(dtype[:-1])]
    else:
        er_df = pd.DataFrame()
    #
    if dtype == 'ages':
        full_df = er_df
    else:
        # read in pmag_ data & make DataFrame
        pmag_file = os.path.join(input_dir, 'pmag_{}.txt'.format(dtype))
        pmag_data, pmag_dtype = magic_read(pmag_file)
        if len(pmag_data):
            pmag_df = pd.DataFrame(pmag_data)
            pmag_df.index = pmag_df['er_{}_name'.format(dtype[:-1])]
        else:
            pmag_df = pd.DataFrame()
        # combine the two Dataframes
        full_df = pd.concat([er_df, pmag_df], sort=True)
        # sort the DataFrame so that all records from one item are together
        full_df.sort_index(inplace=True)

    # fix the column names to be 3.0
    full_df.rename(columns=map_dict, inplace=True)
    # create a MagicDataFrame object, providing the dataframe and the data type
    new_df = cb.MagicDataFrame(dtype=dtype, df=full_df, dmodel=data_model)
    # write out the data to file
    if len(new_df.df):
        new_df.write_magic_file(dir_path=output_dir)
        return dtype + ".txt"
    else:
        print("-I- No {} data found.".format(dtype))
        return None


def convert_criteria_file_2_to_3(fname="pmag_criteria.txt", input_dir=".",
                                 output_dir=".", data_model=None):
    """
    Convert a criteria file from 2.5 to 3.0 format and write it out to file

    Parameters
    ----------
    fname : string of filename (default "pmag_criteria.txt")
    input_dir : string of input directory (default ".")
    output_dir : string of output directory (default ".")
    data_model : data_model.DataModel object (default None)

    Returns
    ---------
    outfile : string output criteria filename, or False
    crit_container : cb.MagicDataFrame with 3.0 criteria table
    """
    # get criteria from infile
    fname = os.path.join(input_dir, fname)
    if not os.path.exists(fname):
        return False, None
    orig_crit, warnings = read_criteria_from_file(fname, initialize_acceptance_criteria(),
                                                  data_model=2, return_warnings=True)
    converted_crit = {}
    # get data model including criteria map
    if not data_model:
        from . import data_model3 as dm3
        DM = dm3.DataModel()
    else:
        DM = data_model
    crit_map = DM.crit_map
    # drop all empty mappings
    stripped_crit_map = crit_map.dropna(axis='rows')
    # go through criteria and get 3.0 name and criterion_operation
    for crit in orig_crit:
        if orig_crit[crit]['value'] in [-999, '-999', -999.]:
            continue
        if crit in stripped_crit_map.index:
            criterion_operation = stripped_crit_map.loc[crit]['criteria_map']['criterion_operation']
            table_col = stripped_crit_map.loc[crit]['criteria_map']['table_column']
            orig_crit[crit]['criterion_operation'] = criterion_operation
            converted_crit[table_col] = orig_crit[crit]
        else:
            print('-W- Could not convert {} to 3.0, skipping'.format(crit))
    # switch axes
    converted_df = pd.DataFrame(converted_crit).transpose()
    # name the index
    converted_df.index.name = "table_column"
    # rename columns to 3.0 values
    # 'category' --> criterion (uses defaults from initalize_default_criteria)
    # 'pmag_criteria_code' --> criterion (uses what's actually in the translated file)
    converted_df.rename(columns={'pmag_criteria_code': 'criterion', 'er_citation_names': 'citations',
                                 'criteria_definition': 'description', 'value': 'criterion_value'},
                        inplace=True)
    # drop unused columns
    valid_cols = DM.dm['criteria'].index
    drop_cols = set(converted_df.columns) - set(valid_cols)
    converted_df.drop(drop_cols, axis='columns', inplace=True)
    # move 'table_column' from being the index to being a column
    converted_df['table_column'] = converted_df.index
    crit_container = cb.MagicDataFrame(dtype='criteria', df=converted_df)
    crit_container.write_magic_file(dir_path=output_dir)
    return "criteria.txt", crit_container


def getsampVGP(SampRec, SiteNFO, data_model=2.5):
    if float(data_model) == 3.0:
        site = get_dictitem(SiteNFO, 'site', SampRec['site'], 'T')
        if len(site) > 1:
            lat, lon, i = None, None, 0
            while lat == None or lon == None or i >= len(site):
                if site[i]['lat'] != None:
                    lat = float(site[i]['lat'])
                if site[i]['lon'] != None:
                    lon = float(site[i]['lon'])
                i += 1
        else:
            lat = float(site[0]['lat'])
            lon = float(site[0]['lon'])
        dec = float(SampRec['dir_dec'])
        inc = float(SampRec['dir_inc'])
        if SampRec['dir_alpha95'] != "":
            a95 = float(SampRec['dir_alpha95'])
        else:
            a95 = 0
        plon, plat, dp, dm = dia_vgp(dec, inc, a95, lat, lon)
        ResRec = {}
        ResRec['result_name'] = 'VGP Sample: ' + SampRec['sample']
        ResRec['location'] = SampRec['location']
        ResRec['citations'] = "This study"
        ResRec['site'] = SampRec['site']
        ResRec['dir_dec'] = SampRec['dir_dec']
        ResRec['dir_inc'] = SampRec['dir_inc']
        ResRec['dir_alpha95'] = SampRec['dir_alpha95']
        ResRec['dir_tilt_correction'] = SampRec['dir_tilt_correction']
        ResRec['dir_comp_name'] = SampRec['dir_comp_name']
        ResRec['vgp_lat'] = '%7.1f' % (plat)
        ResRec['vgp_lon'] = '%7.1f' % (plon)
        ResRec['vgp_dp'] = '%7.1f' % (dp)
        ResRec['vgp_dm'] = '%7.1f' % (dm)
        ResRec['method_codes'] = SampRec['method_codes'] + ":DE-DI"
        return ResRec
    else:
        site = get_dictitem(SiteNFO, 'er_site_name',
                            SampRec['er_site_name'], 'T')
        if len(site) > 1:
            lat, lon, i = None, None, 0
            while lat == None or lon == None or i >= len(site):
                if site[i]['site_lat'] != None:
                    lat = float(site[i]['site_lat'])
                if site[i]['site_lon'] != None:
                    lon = float(site[i]['site_lon'])
                i += 1
        else:
            lat = float(site[0]['site_lat'])
            lon = float(site[0]['site_lon'])
        dec = float(SampRec['sample_dec'])
        inc = float(SampRec['sample_inc'])
        if SampRec['sample_alpha95'] != "":
            a95 = float(SampRec['sample_alpha95'])
        else:
            a95 = 0
        plon, plat, dp, dm = dia_vgp(dec, inc, a95, lat, lon)
        ResRec = {}
        ResRec['pmag_result_name'] = 'VGP Sample: ' + SampRec['er_sample_name']
        ResRec['er_location_names'] = SampRec['er_location_name']
        ResRec['er_citation_names'] = "This study"
        ResRec['er_site_name'] = SampRec['er_site_name']
        ResRec['average_dec'] = SampRec['sample_dec']
        ResRec['average_inc'] = SampRec['sample_inc']
        ResRec['average_alpha95'] = SampRec['sample_alpha95']
        ResRec['tilt_correction'] = SampRec['sample_tilt_correction']
        ResRec['pole_comp_name'] = SampleRec['sample_comp_name']
        ResRec['vgp_lat'] = '%7.1f' % (plat)
        ResRec['vgp_lon'] = '%7.1f' % (plon)
        ResRec['vgp_dp'] = '%7.1f' % (dp)
        ResRec['vgp_dm'] = '%7.1f' % (dm)
        ResRec['magic_method_codes'] = SampRec['magic_method_codes'] + ":DE-DI"
        return ResRec


def getsampVDM(SampRec, SampNFO):
    samps = get_dictitem(SampNFO, 'er_sample_name',
                         SampRec['er_sample_name'], 'T')
    if len(samps) > 0:
        samp = samps[0]
        lat = float(samp['sample_lat'])
        int = float(SampRec['sample_int'])
        vdm = b_vdm(int, lat)
        if 'sample_int_sigma' in list(SampRec.keys()) and SampRec['sample_int_sigma'] != "":
            sig = b_vdm(float(SampRec['sample_int_sigma']), lat)
            sig = '%8.3e' % (sig)
        else:
            sig = ""
    else:
        print('could not find sample info for: ', SampRec['er_sample_name'])
        return {}
    ResRec = {}
    ResRec['pmag_result_name'] = 'V[A]DM Sample: ' + SampRec['er_sample_name']
    ResRec['er_location_names'] = SampRec['er_location_name']
    ResRec['er_citation_names'] = "This study"
    ResRec['er_site_names'] = SampRec['er_site_name']
    ResRec['er_sample_names'] = SampRec['er_sample_name']
    if 'sample_dec' in list(SampRec.keys()):
        ResRec['average_dec'] = SampRec['sample_dec']
    else:
        ResRec['average_dec'] = ""
    if 'sample_inc' in list(SampRec.keys()):
        ResRec['average_inc'] = SampRec['sample_inc']
    else:
        ResRec['average_inc'] = ""
    ResRec['average_int'] = SampRec['sample_int']
    ResRec['vadm'] = '%8.3e' % (vdm)
    ResRec['vadm_sigma'] = sig
    ResRec['magic_method_codes'] = SampRec['magic_method_codes']
    ResRec['model_lat'] = samp['sample_lat']
    return ResRec


def getfield(irmunits, coil, treat):
    # calibration of ASC Impulse magnetizer
    if coil == "3":
        m, b = 0.0071, -0.004  # B=mh+b where B is in T, treat is in Volts
    if coil == "2":
        m, b = 0.00329, -0.002455  # B=mh+b where B is in T, treat is in Volts
    if coil == "1":
        m, b = 0.0002, -0.0002  # B=mh+b where B is in T, treat is in Volts
    return float(treat) * m + b


def sortbykeys(input, sort_list):
    Output = []
    List = []  # get a list of what to be sorted by second key
    for rec in input:
        if rec[sort_list[0]] not in List:
            List.append(rec[sort_list[0]])
    for current in List:  # step through input finding all records of current
        Currents = []
        for rec in input:
            if rec[sort_list[0]] == current:
                Currents.append(rec)
        Current_sorted = sort_diclist(Currents, sort_list[1])
        for rec in Current_sorted:
            Output.append(rec)
    return Output


def get_list(data, key):  # return a colon delimited list of unique key values
    keylist = []
    for rec in data:
        keys = rec[key].split(':')
        for k in keys:
            if k not in keylist:
                keylist.append(k)
    keystring = ""
    if len(keylist) == 0:
        return keystring
    for k in keylist:
        keystring = keystring + ':' + k
    return keystring[1:]


def ParseSiteFile(site_file):
    Sites, file_type = magic_read(site_file)
    LocNames, Locations = [], []
    for site in Sites:
        if site['er_location_name'] not in LocNames:  # new location name
            LocNames.append(site['er_location_name'])
            # get all sites for this loc
            sites_locs = get_dictitem(
                Sites, 'er_location_name', site['er_location_name'], 'T')
            # get all the latitudes as floats
            lats = get_dictkey(sites_locs, 'site_lat', 'f')
            # get all the longitudes as floats
            lons = get_dictkey(sites_locs, 'site_lon', 'f')
            LocRec = {'er_citation_names': 'This study',
                      'er_location_name': site['er_location_name'], 'location_type': ''}
            LocRec['location_begin_lat'] = str(min(lats))
            LocRec['location_end_lat'] = str(max(lats))
            LocRec['location_begin_lon'] = str(min(lons))
            LocRec['location_end_lon'] = str(max(lons))
            Locations.append(LocRec)
    return Locations


def ParseMeasFile(measfile, sitefile, instout, specout):  # fix up some stuff for uploading
    #
    # read in magic_measurements file to get specimen, and instrument names
    #
    master_instlist = []
    InstRecs = []
    meas_data, file_type = magic_read(measfile)
    if file_type != 'magic_measurements':
        print(file_type, "This is not a valid magic_measurements file ")
        return
    # read in site data
    if sitefile != "":
        SiteNFO, file_type = magic_read(sitefile)
        if file_type == "bad_file":
            print("Bad  or no er_sites file - lithology, etc will not be imported")
    else:
        SiteNFO = []
    # define the Er_specimen records to create a new er_specimens.txt file
    #
    suniq, ErSpecs = [], []
    for rec in meas_data:
        # fill in some potentially missing fields
        if "magic_instrument_codes" in list(rec.keys()):
            lst = (rec["magic_instrument_codes"])
            lst.strip()
            tmplist = lst.split(":")
            for inst in tmplist:
                if inst not in master_instlist:
                    master_instlist.append(inst)
                    InstRec = {}
                    InstRec["magic_instrument_code"] = inst
                    InstRecs.append(InstRec)
        if "measurement_standard" not in list(rec.keys()):
            # make this an unknown if not specified
            rec['measurement_standard'] = 'u'
        if rec["er_specimen_name"] not in suniq and rec["measurement_standard"] != 's':  # exclude standards
            suniq.append(rec["er_specimen_name"])
            ErSpecRec = {}
            ErSpecRec["er_citation_names"] = "This study"
            ErSpecRec["er_specimen_name"] = rec["er_specimen_name"]
            ErSpecRec["er_sample_name"] = rec["er_sample_name"]
            ErSpecRec["er_site_name"] = rec["er_site_name"]
            ErSpecRec["er_location_name"] = rec["er_location_name"]
    #
    # attach site litho, etc. to specimen if not already there
            sites = get_dictitem(SiteNFO, 'er_site_name',
                                 rec['er_site_name'], 'T')
            if len(sites) == 0:
                site = {}
                print('site record in er_sites table not found for: ',
                      rec['er_site_name'])
            else:
                site = sites[0]
            if 'site_class' not in list(site.keys()) or 'site_lithology' not in list(site.keys()) or 'site_type' not in list(site.keys()):
                site['site_class'] = 'Not Specified'
                site['site_lithology'] = 'Not Specified'
                site['site_type'] = 'Not Specified'
            if 'specimen_class' not in list(ErSpecRec.keys()):
                ErSpecRec["specimen_class"] = site['site_class']
            if 'specimen_lithology' not in list(ErSpecRec.keys()):
                ErSpecRec["specimen_lithology"] = site['site_lithology']
            if 'specimen_type' not in list(ErSpecRec.keys()):
                ErSpecRec["specimen_type"] = site['site_type']
            if 'specimen_volume' not in list(ErSpecRec.keys()):
                ErSpecRec["specimen_volume"] = ""
            if 'specimen_weight' not in list(ErSpecRec.keys()):
                ErSpecRec["specimen_weight"] = ""
            ErSpecs.append(ErSpecRec)
    #
    #
    # save the data
    #
    magic_write(specout, ErSpecs, "er_specimens")
    print(" Er_Specimen data (with updated info from site if necessary)  saved in ", specout)
    #
    # write out the instrument list
    if len(InstRecs) > 0:
        magic_write(instout, InstRecs, "magic_instruments")
        print(" Instruments data saved in ", instout)
    else:
        print("No instruments found")


# take care of re-ordering sample table, putting used orientations first
def ReorderSamples(specfile, sampfile, outfile):
    UsedSamps, RestSamps = [], []
    Specs, filetype = magic_read(specfile)  # read in specimen file
    Samps, filetype = magic_read(sampfile)  # read in sample file
    for rec in Specs:  # hunt through specimen by specimen
        meths = rec['magic_method_codes'].strip().strip('\n').split(':')
        for meth in meths:
            methtype = meth.strip().strip('\n').split('-')
            if 'SO' in methtype:
                SO_meth = meth  # find the orientation method code
        samprecs = get_dictitem(Samps, 'er_sample_name',
                                rec['er_sample_name'], 'T')
        used = get_dictitem(samprecs, 'magic_method_codes', SO_meth, 'has')
        if len(used) > 0:
            UsedSamps.append(used[0])
        else:
            print('orientation not found for: ', rec['er_specimen_name'])
        rest = get_dictitem(samprecs, 'magic_method_codes', SO_meth, 'not')
        for rec in rest:
            RestSamps.append(rec)
    for rec in RestSamps:
        UsedSamps.append(rec)  # append the unused ones to the end of the file
    magic_write(outfile, UsedSamps, 'er_samples')


def orient(mag_azimuth, field_dip, or_con):
    """
    uses specified orientation convention to convert user supplied orientations
    to laboratory azimuth and plunge
    """
    or_con = str(or_con)
    if mag_azimuth == -999:
        return "", ""
    if or_con == "1":  # lab_mag_az=mag_az;  sample_dip = -dip
        return mag_azimuth, -field_dip
    if or_con == "2":
        return mag_azimuth - 90., -field_dip
    if or_con == "3":  # lab_mag_az=mag_az;  sample_dip = 90.-dip
        return mag_azimuth, 90. - field_dip
    if or_con == "4":  # lab_mag_az=mag_az;  sample_dip = dip
        return mag_azimuth, field_dip
    if or_con == "5":  # lab_mag_az=mag_az;  sample_dip = dip-90.
        return mag_azimuth, field_dip - 90.
    if or_con == "6":  # lab_mag_az=mag_az-90.;  sample_dip = 90.-dip
        return mag_azimuth - 90., 90. - field_dip
    if or_con == "7":  # lab_mag_az=mag_az;  sample_dip = 90.-dip
        return mag_azimuth - 90., 90. - field_dip
    print("Error in orientation convention")


def get_Sb(data):
    """
    returns vgp scatter for data set
    """
    Sb, N = 0., 0.
    for rec in data:
        delta = 90. - abs(rec['vgp_lat'])
        if rec['average_k'] != 0:
            k = rec['average_k']
            L = rec['average_lat'] * np.pi / 180.  # latitude in radians
            Nsi = rec['average_nn']
            K = old_div(k, (2. * (1. + 3. * np.sin(L)**2) /
                            (5. - 3. * np.sin(L)**2)))
            Sw = old_div(81., np.sqrt(K))
        else:
            Sw, Nsi = 0, 1.
        Sb += delta**2. - old_div((Sw**2), Nsi)
        N += 1.
    return np.sqrt(old_div(Sb, float(N - 1.)))


def get_sb_df(df, mm97=False):
    """
    Calculates Sf for a dataframe with VGP Lat., and optional Fisher's k, site latitude and N information can be used to correct for within site scatter (McElhinny & McFadden, 1997)

    Parameters
    _________
    df : Pandas Dataframe with columns
        REQUIRED:
        vgp_lat :  VGP latitude
        ONLY REQUIRED for MM97 correction:
        dir_k : Fisher kappa estimate
        dir_n : number of specimens (samples) per site
        lat : latitude of the site
    mm97 : if True, will do the correction for within site scatter

    Returns:
    _______
    Sf : Sf
    """
    df['delta'] = 90.-df.vgp_lat
    Sp2 = np.sum(df.delta**2)/(df.shape[0]-1)
    if 'dir_k' in df.columns and mm97:
        ks = df.dir_k
        Ns = df.dir_n
        Ls = np.radians(df.lat)
        A95s = 140./np.sqrt(ks*Ns)
        Sw2_n = 0.335*(A95s**2)*(2.*(1.+3.*np.sin(Ls)**2) /
                                 (5.-3.*np.sin(Ls)**2))
        return np.sqrt(Sp2-Sw2_n.mean())
    else:
        return np.sqrt(Sp2)


def default_criteria(nocrit):
    Crits = {}
    critkeys = ['magic_experiment_names', 'measurement_step_min', 'measurement_step_max', 'measurement_step_unit', 'specimen_polarity', 'specimen_nrm', 'specimen_direction_type', 'specimen_comp_nmb', 'specimen_mad', 'specimen_alpha95', 'specimen_n', 'specimen_int_sigma', 'specimen_int_sigma_perc', 'specimen_int_rel_sigma', 'specimen_int_rel_sigma_perc', 'specimen_int_mad', 'specimen_int_n', 'specimen_w', 'specimen_q', 'specimen_f', 'specimen_fvds', 'specimen_b_sigma', 'specimen_b_beta', 'specimen_g', 'specimen_dang', 'specimen_md', 'specimen_ptrm', 'specimen_drat', 'specimen_drats', 'specimen_rsc', 'specimen_viscosity_index', 'specimen_magn_moment', 'specimen_magn_volume', 'specimen_magn_mass', 'specimen_int_dang', 'specimen_int_ptrm_n', 'specimen_delta', 'specimen_theta', 'specimen_gamma', 'specimen_frac', 'specimen_gmax', 'specimen_scat', 'sample_polarity', 'sample_nrm', 'sample_direction_type', 'sample_comp_nmb', 'sample_sigma', 'sample_alpha95', 'sample_n', 'sample_n_lines', 'sample_n_planes',
                'sample_k', 'sample_r', 'sample_tilt_correction', 'sample_int_sigma', 'sample_int_sigma_perc', 'sample_int_rel_sigma', 'sample_int_rel_sigma_perc', 'sample_int_n', 'sample_magn_moment', 'sample_magn_volume', 'sample_magn_mass', 'site_polarity', 'site_nrm', 'site_direction_type', 'site_comp_nmb', 'site_sigma', 'site_alpha95', 'site_n', 'site_n_lines', 'site_n_planes', 'site_k', 'site_r', 'site_tilt_correction', 'site_int_sigma', 'site_int_sigma_perc', 'site_int_rel_sigma', 'site_int_rel_sigma_perc', 'site_int_n', 'site_magn_moment', 'site_magn_volume', 'site_magn_mass', 'average_age_min', 'average_age_max', 'average_age_sigma', 'average_age_unit', 'average_sigma', 'average_alpha95', 'average_n', 'average_nn', 'average_k', 'average_r', 'average_int_sigma', 'average_int_rel_sigma', 'average_int_rel_sigma_perc', 'average_int_n', 'average_int_nn', 'vgp_dp', 'vgp_dm', 'vgp_sigma', 'vgp_alpha95', 'vgp_n', 'vdm_sigma', 'vdm_n', 'vadm_sigma', 'vadm_n', 'criteria_description', 'er_citation_names']
    for key in critkeys:
        Crits[key] = ''  # set up dictionary with all possible
    Crits['pmag_criteria_code'] = 'ACCEPT'
    Crits['criteria_definition'] = 'acceptance criteria for study'
    Crits['er_citation_names'] = 'This study'
    if nocrit == 0:  # use default criteria
        #
        # set some sort of quasi-reasonable default criteria
        #
        Crits['specimen_mad'] = '5'
        Crits['specimen_dang'] = '10'
        Crits['specimen_int_n'] = '4'
        Crits['specimen_int_ptrm_n'] = '2'
        Crits['specimen_drats'] = '20'
        Crits['specimen_b_beta'] = '0.1'
        Crits['specimen_md'] = '15'
        Crits['specimen_fvds'] = '0.7'
        Crits['specimen_q'] = '1.0'
        Crits['specimen_int_dang'] = '10'
        Crits['specimen_int_mad'] = '10'
        Crits['sample_alpha95'] = '5'
        Crits['site_int_n'] = '2'
        Crits['site_int_sigma'] = '5e-6'
        Crits['site_int_sigma_perc'] = '15'
        Crits['site_n'] = '5'
        Crits['site_n_lines'] = '4'
        Crits['site_k'] = '50'
    return [Crits]


def grade(PmagRec, ACCEPT, type, data_model=2.5):
    """
    Finds the 'grade' (pass/fail; A/F) of a record (specimen,sample,site) given the acceptance criteria
    """
    GREATERTHAN = ['specimen_q', 'site_k', 'site_n', 'site_n_lines', 'site_int_n', 'measurement_step_min', 'specimen_int_ptrm_n', 'specimen_fvds', 'specimen_frac', 'specimen_f', 'specimen_n', 'specimen_int_n', 'sample_int_n', 'average_age_min', 'average_k', 'average_r', 'specimen_magn_moment',
                   'specimen_magn_volume', 'specimen_rsc', 'sample_n', 'sample_n_lines', 'sample_n_planes', 'sample_k', 'sample_r', 'site_magn_moment', 'site_magn_volume', 'site_magn_mass', 'site_r']  # these statistics must be exceede to pass, all others must be less than (except specimen_scat, which must be true)
    ISTRUE = ['specimen_scat']
    kill = []  # criteria that kill the record
    sigma_types = ['sample_int_sigma', 'sample_int_sigma_perc', 'site_int_sigma',
                   'site_int_sigma_perc', 'average_int_sigma', 'average_int_sigma_perc']
    sigmas = []
    accept = {}
    if type == 'specimen_int':
        USEKEYS = ['specimen_q', 'measurement_step_min', 'measurement_step_max', 'specimen_int_ptrm_n', 'specimen_fvds', 'specimen_frac', 'specimen_f', 'specimen_int_n', 'specimen_magn_moment',
                   'specimen_magn_volume', 'specimen_rsc', 'specimen_scat', 'specimen_drats', 'specimen_int_mad', 'specimen_int_dang', 'specimen_md', 'specimen_b_beta', 'specimen_w', 'specimen_gmax']
        if data_model == 3.0:
            USEKEYS = [map_magic.spec_magic2_2_magic3_map[k] for k in USEKEYS]
    elif type == 'specimen_dir':
        USEKEYS = ['measurement_step_min', 'measurement_step_max', 'specimen_mad',
                   'specimen_n', 'specimen_magn_moment', 'specimen_magn_volume']
        if data_model == 3.0:
            USEKEYS = [map_magic.spec_magic2_2_magic3_map[k] for k in USEKEYS]
    elif type == 'sample_int':
        USEKEYS = ['sample_int_n', 'sample_int_sigma', 'sample_int_sigma_perc']
        if data_model == 3.0:
            USEKEYS = [map_magic.samp_magic2_2_magic3_map[k] for k in USEKEYS]
    elif type == 'sample_dir':
        USEKEYS = ['sample_alpha95', 'sample_n', 'sample_n_lines',
                   'sample_n_planes', 'sample_k', 'sample_r']
        if data_model == 3.0:
            USEKEYS = [map_magic.samp_magic2_2_magic3_map[k] for k in USEKEYS]
    elif type == 'site_int':
        USEKEYS = ['site_int_sigma', 'site_int_sigma_perc', 'site_int_n']
        if data_model == 3.0:
            USEKEYS = [map_magic.site_magic2_2_magic3_map[k] for k in USEKEYS]
    elif type == 'site_dir':
        USEKEYS = ['site_alpha95', 'site_k', 'site_n',
                   'site_n_lines', 'site_n_planes', 'site_r']
        if data_model == 3.0:
            USEKEYS = [map_magic.site_magic2_2_magic3_map[k] for k in USEKEYS]

    for key in list(ACCEPT.keys()):
        if ACCEPT[key] != "" and key in USEKEYS:
            if key in ISTRUE and ACCEPT[key] == 'TRUE' or ACCEPT[key] == 'True':
                # this is because Excel always capitalizes True to TRUE and
                # python doesn't recognize that as a boolean.  never mind
                ACCEPT[key] = '1'
            elif ACCEPT[key] == 'FALSE' or ACCEPT[key] == 'False':
                ACCEPT[key] = '0'
            elif eval(ACCEPT[key]) == 0:
                ACCEPT[key] = ""
            accept[key] = ACCEPT[key]
    for key in sigma_types:
        if key in USEKEYS and key in list(accept.keys()) and key in list(PmagRec.keys()):
            sigmas.append(key)
    if len(sigmas) > 1:
        if PmagRec[sigmas[0]] == "" or PmagRec[sigmas[1]] == "":
            kill.append(sigmas[0])
            kill.append(sigmas[1])
        elif eval(PmagRec[sigmas[0]]) > eval(accept[sigmas[0]]) and eval(PmagRec[sigmas[1]]) > eval(accept[sigmas[1]]):
            kill.append(sigmas[0])
            kill.append(sigmas[1])
    elif len(sigmas) == 1 and sigmas[0] in list(accept.keys()):
        if PmagRec[sigmas[0]] > accept[sigmas[0]]:
            kill.append(sigmas[0])
    for key in list(accept.keys()):
        if accept[key] != "":
            if key not in list(PmagRec.keys()) or PmagRec[key] == '':
                kill.append(key)
            elif key not in sigma_types:
                if key in ISTRUE:  # boolean must be true
                    if PmagRec[key] != '1':
                        kill.append(key)
                if key in GREATERTHAN:
                    if eval(str(PmagRec[key])) < eval(str(accept[key])):
                        kill.append(key)
                else:
                    if eval(str(PmagRec[key])) > eval(str(accept[key])):
                        kill.append(key)
    return kill

#


def flip(di_block, combine=False):
    """
    determines principle direction and calculates the antipode of
    the reverse mode
    Parameters
    ___________
    di_block : nested list of directions
    Return
    D1 : normal mode
    D2 : flipped reverse mode as two DI blocks
    combine : if True return combined D1, D2, nested D,I pairs
    """
    ppars = doprinc(di_block)  # get principle direction
    if combine:
        D3 = []
    D1, D2 = [], []
    for rec in di_block:
        ang = angle([rec[0], rec[1]], [ppars['dec'], ppars['inc']])
        if ang > 90.:
            d, i = (rec[0] - 180.) % 360., -rec[1]
            D2.append([d, i])
            if combine:
                D3.append([d, i])
        else:
            D1.append([rec[0], rec[1]])
            if combine:
                D3.append([rec[0], rec[1]])
    if combine:
        return D3
    else:
        return D1, D2
#


def dia_vgp(*args):  # new function interface by J.Holmes, SIO, 6/1/2011
    """
    Converts directional data (declination, inclination, alpha95) at a given
    location (Site latitude, Site longitude) to pole position (pole longitude,
    pole latitude, dp, dm)

    Parameters
    ----------
    Takes input as (Dec, Inc, a95, Site latitude, Site longitude)
    Input can be as individual values (5 parameters)
    or
    as a list of lists: [[Dec, Inc, a95, lat, lon],[Dec, Inc, a95, lat, lon]]

    Returns
    ----------
    if input is individual values for one pole the return is:
    pole longitude, pole latitude, dp, dm

    if input is list of lists the return is:
    list of pole longitudes, list of pole latitude, list of dp, list of dm
    """
    # test whether arguments are one 2-D list or 5 floats
    if len(args) == 1:  # args comes in as a tuple of multi-dim lists.
        largs = list(args).pop()  # scrap the tuple.
        # reorganize the lists so that we get columns of data in each var.
        (decs, dips, a95s, slats, slongs) = list(zip(*largs))
    else:
        # When args > 1, we are receiving five floats. This usually happens when the invoking script is
        # executed in interactive mode.
        (decs, dips, a95s, slats, slongs) = (args)

    # We send all incoming data to numpy in an array form. Even if it means a
    # 1x1 matrix. That's OKAY. Really.
    (dec, dip, a95, slat, slong) = (np.array(decs), np.array(dips), np.array(a95s),
                                    np.array(slats), np.array(slongs))  # package columns into arrays
    rad = old_div(np.pi, 180.)  # convert to radians
    dec, dip, a95, slat, slong = dec * rad, dip * \
        rad, a95 * rad, slat * rad, slong * rad
    p = np.arctan2(2.0, np.tan(dip))
    plat = np.arcsin(np.sin(slat) * np.cos(p) +
                     np.cos(slat) * np.sin(p) * np.cos(dec))
    beta = old_div((np.sin(p) * np.sin(dec)), np.cos(plat))

    # -------------------------------------------------------------------------
    # The deal with "boolmask":
    # We needed a quick way to assign matrix values based on a logic decision, in this case setting boundaries
    # on out-of-bounds conditions. Creating a matrix of boolean values the size of the original matrix and using
    # it to "mask" the assignment solves this problem nicely. The downside to this is that Numpy complains if you
    # attempt to mask a non-matrix, so we have to check for array type and do a normal assignment if the type is
    # scalar. These checks are made before calculating for the rest of the function.
    # -------------------------------------------------------------------------

    boolmask = beta > 1.  # create a mask of boolean values
    if isinstance(beta, np.ndarray):
        beta[boolmask] = 1.  # assigns 1 only to elements that mask TRUE.
    # Numpy gets upset if you try our masking trick with a scalar or a 0-D
    # matrix.
    else:
        if boolmask:
            beta = 1.
    boolmask = beta < -1.
    if isinstance(beta, np.ndarray):
        beta[boolmask] = -1.  # assigns -1 only to elements that mask TRUE.
    else:
        if boolmask:
            beta = -1.

    beta = np.arcsin(beta)
    plong = slong + np.pi - beta
    if (np.cos(p) > np.sin(slat) * np.sin(plat)).any():
        boolmask = (np.cos(p) > (np.sin(slat) * np.sin(plat)))
        if isinstance(plong, np.ndarray):
            plong[boolmask] = (slong + beta)[boolmask]
        else:
            if boolmask:
                plong = slong + beta

    boolmask = (plong < 0)
    if isinstance(plong, np.ndarray):
        plong[boolmask] = plong[boolmask] + 2 * np.pi
    else:
        if boolmask:
            plong = plong + 2 * np.pi

    boolmask = (plong > 2 * np.pi)
    if isinstance(plong, np.ndarray):
        plong[boolmask] = plong[boolmask] - 2 * np.pi
    else:
        if boolmask:
            plong = plong - 2 * np.pi

    dm = np.rad2deg(a95 * (old_div(np.sin(p), np.cos(dip))))
    dp = np.rad2deg(a95 * (old_div((1 + 3 * (np.cos(p)**2)), 2)))
    plat = np.rad2deg(plat)
    plong = np.rad2deg(plong)
    return plong.tolist(), plat.tolist(), dp.tolist(), dm.tolist()


def int_pars(x, y, vds, **kwargs):
    """
     calculates York regression and Coe parameters (with Tauxe Fvds)
    """
    # first do linear regression a la York
    # do Data Model 3 way:
    if 'version' in list(kwargs.keys()) and kwargs['version'] == 3:
        n_key = 'int_n_measurements'
        b_key = 'int_b'
        sigma_key = 'int_b_sigma'
        f_key = 'int_f'
        fvds_key = 'int_fvds'
        g_key = 'int_g'
        q_key = 'int_q'
        b_beta_key = 'int_b_beta'

    else:  # version 2
        n_key = 'specimen_int_n'
        b_key = 'specimen_b'
        sigma_key = 'specimen_b_sigma'
        f_key = 'specimen_f'
        fvds_key = 'specimen_fvds'
        g_key = 'specimen_g'
        q_key = 'specimen_q'
        b_beta_key = 'specimen_b_beta'

    xx, yer, xer, xyer, yy, xsum, ysum, xy = 0., 0., 0., 0., 0., 0., 0., 0.
    xprime, yprime = [], []
    pars = {}
    pars[n_key] = len(x)
    n = float(len(x))
    if n <= 2:
        print("shouldn't be here at all!")
        return pars, 1
    for i in range(len(x)):
        xx += x[i]**2.
        yy += y[i]**2.
        xy += x[i] * y[i]
        xsum += x[i]
        ysum += y[i]
    xsig = np.sqrt(old_div((xx - (old_div(xsum**2., n))), (n - 1.)))
    ysig = np.sqrt(old_div((yy - (old_div(ysum**2., n))), (n - 1.)))
    sum = 0
    for i in range(int(n)):
        yer += (y[i] - old_div(ysum, n))**2.
        xer += (x[i] - old_div(xsum, n))**2.
        xyer += (y[i] - old_div(ysum, n)) * (x[i] - old_div(xsum, n))
    slop = -np.sqrt(old_div(yer, xer))
    pars[b_key] = slop
    s1 = 2. * yer - 2. * slop * xyer
    s2 = (n - 2.) * xer
    sigma = np.sqrt(old_div(s1, s2))
    pars[sigma_key] = sigma
    s = old_div((xy - (xsum * ysum / n)), (xx - old_div((xsum**2.), n)))
    r = old_div((s * xsig), ysig)
    pars["specimen_rsc"] = r**2.
    ytot = abs(old_div(ysum, n) - slop * xsum / n)
    for i in range(int(n)):
        xprime.append(old_div((slop * x[i] + y[i] - ytot), (2. * slop)))
        yprime.append((old_div((slop * x[i] + y[i] - ytot), 2.)) + ytot)
    sumdy, dy = 0, []
    dyt = abs(yprime[0] - yprime[int(n) - 1])
    for i in range((int(n) - 1)):
        dy.append(abs(yprime[i + 1] - yprime[i]))
        sumdy += dy[i]**2.
    f = old_div(dyt, ytot)
    pars[f_key] = f
    pars["specimen_ytot"] = ytot
    ff = old_div(dyt, vds)
    pars[fvds_key] = ff
    ddy = (old_div(1., dyt)) * sumdy
    g = 1. - old_div(ddy, dyt)
    pars[g_key] = g
    q = abs(slop) * f * g / sigma
    pars[q_key] = q
    pars[b_beta_key] = old_div(-sigma, slop)
    return pars, 0


def dovds(data):
    """
     calculates vector difference sum for demagnetization data
    """
    vds, X = 0, []
    for rec in data:
        X.append(dir2cart(rec))
    for k in range(len(X) - 1):
        xdif = X[k + 1][0] - X[k][0]
        ydif = X[k + 1][1] - X[k][1]
        zdif = X[k + 1][2] - X[k][2]
        vds += np.sqrt(xdif**2 + ydif**2 + zdif**2)
    vds += np.sqrt(X[-1][0]**2 + X[-1][1]**2 + X[-1][2]**2)
    return vds


def vspec_magic(data):
    """
    Takes average vector of replicate measurements
    """
    vdata, Dirdata, step_meth = [], [], ""
    if len(data) == 0:
        return vdata
    treat_init = ["treatment_temp", "treatment_temp_decay_rate", "treatment_temp_dc_on", "treatment_temp_dc_off", "treatment_ac_field", "treatment_ac_field_decay_rate", "treatment_ac_field_dc_on",
                  "treatment_ac_field_dc_off", "treatment_dc_field", "treatment_dc_field_decay_rate", "treatment_dc_field_ac_on", "treatment_dc_field_ac_off", "treatment_dc_field_phi", "treatment_dc_field_theta"]
    treats = []
#
# find keys that are used
#
    for key in treat_init:
        if key in list(data[0].keys()):
            treats.append(key)  # get a list of keys
    stop = {}
    stop["er_specimen_name"] = "stop"
    for key in treats:
        stop[key] = ""  # tells program when to quit and go home
    data.append(stop)
#
# set initial states
#
    DataState0, newstate = {}, 0
    for key in treats:
        DataState0[key] = data[0][key]  # set beginning treatment
    k, R = 1, 0
    for i in range(k, len(data)):
        FDirdata, Dirdata, DataStateCurr, newstate = [], [], {}, 0
        for key in treats:  # check if anything changed
            DataStateCurr[key] = data[i][key]
            if DataStateCurr[key].strip() != DataState0[key].strip():
                newstate = 1  # something changed
        if newstate == 1:
            if i == k:  # sample is unique
                vdata.append(data[i - 1])
            else:  # measurement is not unique
                # print "averaging: records " ,k,i
                for l in range(k - 1, i):
                    if 'orientation' in data[l]['measurement_description']:
                        data[l]['measurement_description'] = ""
                    Dirdata.append([float(data[l]['measurement_dec']), float(
                        data[l]['measurement_inc']), float(data[l]['measurement_magn_moment'])])
                    FDirdata.append(
                        [float(data[l]['measurement_dec']), float(data[l]['measurement_inc'])])
                dir, R = vector_mean(Dirdata)
                Fpars = fisher_mean(FDirdata)
                vrec = data[i - 1]
                vrec['measurement_dec'] = '%7.1f' % (dir[0])
                vrec['measurement_inc'] = '%7.1f' % (dir[1])
                vrec['measurement_magn_moment'] = '%8.3e' % (
                    old_div(R, (i - k + 1)))
                vrec['measurement_csd'] = '%7.1f' % (Fpars['csd'])
                vrec['measurement_positions'] = '%7.1f' % (Fpars['n'])
                vrec['measurement_description'] = 'average of multiple measurements'
                if "magic_method_codes" in list(vrec.keys()):
                    meths = vrec["magic_method_codes"].strip().split(":")
                    if "DE-VM" not in meths:
                        meths.append("DE-VM")
                    methods = ""
                    for meth in meths:
                        methods = methods + meth + ":"
                    vrec["magic_method_codes"] = methods[:-1]
                else:
                    vrec["magic_method_codes"] = "DE-VM"
                vdata.append(vrec)
# reset state to new one
            for key in treats:
                DataState0[key] = data[i][key]  # set beginning treatment
            k = i + 1
            if data[i]["er_specimen_name"] == "stop":
                del data[-1]  # get rid of dummy stop sign
                return vdata, treats  # bye-bye


def vspec_magic3(data):
    """
    Takes average vector of replicate measurements
    """
    vdata, Dirdata, step_meth = [], [], ""
    if len(data) == 0:
        return vdata
    treat_init = ["treat_temp", "treat_temp_decay_rate", "treat_temp_dc_on", "treat_temp_dc_off", "treat_ac_field", "treat_ac_field_decay_rate", "treat_ac_field_dc_on",
                  "treat_ac_field_dc_off", "treat_dc_field", "treat_dc_field_decay_rate", "treat_dc_field_ac_on", "treat_dc_field_ac_off", "treat_dc_field_phi", "treat_dc_field_theta"]
    treats = []
#
# find keys that are used
#
    for key in treat_init:
        if key in list(data[0].keys()):
            treats.append(key)  # get a list of keys
    stop = {}
    stop["specimen"] = "stop"
    for key in treats:
        stop[key] = ""  # tells program when to quit and go home
    data.append(stop)
#
# set initial states
#
    DataState0, newstate = {}, 0
    for key in treats:
        DataState0[key] = data[0][key]  # set beginning treatment
    k, R = 1, 0
    for i in range(k, len(data)):
        FDirdata, Dirdata, DataStateCurr, newstate = [], [], {}, 0
        for key in treats:  # check if anything changed
            DataStateCurr[key] = data[i][key]
            DataStateCurr[key] = str(DataStateCurr[key])
            DataState0[key] = str(DataState0[key])
            if DataStateCurr[key].strip() != DataState0[key].strip():
                newstate = 1  # something changed
        if newstate == 1:
            if i == k:  # sample is unique
                vdata.append(data[i - 1])
            else:  # measurement is not unique
                # print "averaging: records " ,k,i
                for l in range(k - 1, i):
                    if 'orientation' in data[l]['description']:
                        data[l]['description'] = ""
                    Dirdata.append([float(data[l]['dir_dec']), float(
                        data[l]['dir_inc']), float(data[l]['magn_moment'])])
                    FDirdata.append(
                        [float(data[l]['dir_dec']), float(data[l]['dir_inc'])])
                dir, R = vector_mean(Dirdata)
                Fpars = fisher_mean(FDirdata)
                vrec = data[i - 1]
                vrec['dir_dec'] = '%7.1f' % (dir[0])
                vrec['dir_inc'] = '%7.1f' % (dir[1])
                vrec['magn_moment'] = '%8.3e' % (old_div(R, (i - k + 1)))
                vrec['dir_csd'] = '%7.1f' % (Fpars['csd'])
                vrec['meas_n_orient'] = '%7.1f' % (Fpars['n'])
                vrec['description'] = 'average of multiple measurements'
                if "method_codes" in list(vrec.keys()):
                    meths = vrec["method_codes"].strip().split(":")
                    if "DE-VM" not in meths:
                        meths.append("DE-VM")
                    methods = ""
                    for meth in meths:
                        methods = methods + meth + ":"
                    vrec["method_codes"] = methods[:-1]
                else:
                    vrec["method_codes"] = "DE-VM"
                vdata.append(vrec)
# reset state to new one
            for key in treats:
                DataState0[key] = data[i][key]  # set beginning treatment
            k = i + 1
            if data[i]["specimen"] == "stop":
                del data[-1]  # get rid of dummy stop sign
                return vdata, treats  # bye-bye


def get_specs(data):
    """
    Takes a magic format file and returns a list of unique specimen names
    """
    # sort the specimen names
    speclist = []
    for rec in data:
        try:
            spec = rec["er_specimen_name"]
        except KeyError as e:
            spec = rec["specimen"]
        if spec not in speclist:
            speclist.append(spec)
    speclist.sort()
    return speclist


def vector_mean(data):
    """
    calculates the vector mean of a given set of vectors
    Parameters
    __________
    data :  nested array of [dec,inc,intensity]

    Returns
    _______
    dir : array of [dec, inc, 1]
    R : resultant vector length

    """
    Xbar = np.zeros((3))
    X = dir2cart(data).transpose()
    for i in range(3):
        Xbar[i] = X[i].sum()
    R = np.sqrt(Xbar[0]**2+Xbar[1]**2+Xbar[2]**2)
    Xbar = Xbar/R
    dir = cart2dir(Xbar)
    return dir, R


def mark_dmag_rec(s, ind, data):
    """
    Edits demagnetization data to mark "bad" points with measurement_flag
    """
    datablock = []
    for rec in data:
        if rec['er_specimen_name'] == s:
            meths = rec['magic_method_codes'].split(':')
            if 'LT-NO' in meths or 'LT-AF-Z' in meths or 'LT-T-Z' in meths:
                datablock.append(rec)
    dmagrec = datablock[ind]
    for k in range(len(data)):
        meths = data[k]['magic_method_codes'].split(':')
        if 'LT-NO' in meths or 'LT-AF-Z' in meths or 'LT-T-Z' in meths:
            if data[k]['er_specimen_name'] == s:
                if data[k]['treatment_temp'] == dmagrec['treatment_temp'] and data[k]['treatment_ac_field'] == dmagrec['treatment_ac_field']:
                    if data[k]['measurement_dec'] == dmagrec['measurement_dec'] and data[k]['measurement_inc'] == dmagrec['measurement_inc'] and data[k]['measurement_magn_moment'] == dmagrec['measurement_magn_moment']:
                        if data[k]['measurement_flag'] == 'g':
                            flag = 'b'
                        else:
                            flag = 'g'
                        data[k]['measurement_flag'] = flag
                        break
    return data


def mark_samp(Samps, data, crd):

    return Samps


def find_dmag_rec(s, data, **kwargs):
    """
    Returns demagnetization data for specimen s from the data. Excludes other
    kinds of experiments and "bad" measurements

    Parameters
    __________
    s : specimen name
    data : DataFrame with measurement data
    **kwargs :
        version : if not 3, assume data model = 2.5
    Returns
    ________
    datablock : nested list of data for zijderveld plotting
         [[tr, dec, inc, int, ZI, flag],...]
         tr : treatment step
         dec : declination
         inc : inclination
         int : intensity
         ZI : whether zero-field first or infield-first step
         flag : g or b , default is set to 'g'
     units : list of units found ['T','K','J'] for tesla, kelvin or joules
    """
    if 'version' in list(kwargs.keys()) and kwargs['version'] == 3:
        # convert dataframe to list of dictionaries
        data = data.to_dict('records')
        spec_key, dec_key, inc_key = 'specimen', 'dir_dec', 'dir_inc'
        flag_key, temp_key, ac_key = 'flag', 'treat_temp', 'treat_ac_field'
        meth_key = 'method_codes'
        power_key, time_key = 'treat_mw_power', 'treat_mw_time'
        Mkeys = ['magn_moment', 'magn_volume', 'magn_mass', 'magnitude']
        # just look in the intensity column
        inst_key = 'instrument_codes'
    else:
        spec_key, dec_key, inc_key = 'er_specimen_name', 'measurement_dec', 'measurement_inc'
        flag_key = 'measurement_flag'
        flag_key, temp_key, ac_key = 'measurement_flag', 'treatment_temp', 'treatment_ac_field'
        meth_key = 'magic_method_codes'
        power_key, time_key = 'treatment_mw_power', 'treatment_mw_time'
        Mkeys = ['measurement_magn_moment', 'measurement_magn_volume',
                 'measurement_magn_mass', 'measurement_magnitude']
        inst_key = 'magic_instrument_codes'

    EX = ["LP-AN-ARM", "LP-AN-TRM", "LP-ARM-AFD", "LP-ARM2-AFD", "LP-TRM-AFD",
          "LP-TRM", "LP-TRM-TD", "LP-X"]  # list of excluded lab protocols
    INC = ["LT-NO", "LT-AF-Z", "LT-T-Z",
           "LT-M-Z", "LP-PI-TRM-IZ", "LP-PI-M-IZ"]
    datablock, tr = [], ""
    therm_flag, af_flag, mw_flag = 0, 0, 0
    units = []
    spec_meas = get_dictitem(data, spec_key, s, 'T')
    for rec in spec_meas:
        if flag_key not in list(rec.keys()):
            rec[flag_key] = 'g'
        skip = 1
        tr = ""
        meths = rec[meth_key].split(":")
        methods = []
        for m in meths:
            methods.append(m.strip())  # get rid of the stupid spaces!
        for meth in methods:
            if meth.strip() in INC:
                skip = 0
        for meth in EX:
            if meth in methods:
                skip = 1
        if skip == 0:
            if "LT-NO" in methods:
                tr = float(rec[temp_key])
            if "LT-AF-Z" in methods:
                af_flag = 1
                try:
                    tr = float(rec[ac_key])
                except (KeyError, ValueError):
                    tr = 0
                if "T" not in units:
                    units.append("T")
            if "LT-T-Z" in methods:
                therm_flag = 1
                tr = float(rec[temp_key])
                if "K" not in units:
                    units.append("K")
            if "LT-M-Z" in methods:
                mw_flag = 1
                tr = float(rec[power_key]) * float(rec[time_key])
                if "J" not in units:
                    units.append("J")
            # looking for in-field first thellier or microwave data -
            # otherwise, just ignore this
            if "LP-PI-TRM-IZ" in methods or "LP-PI-M-IZ" in methods:
                ZI = 0
            else:
                ZI = 1
            if tr != "":
                dec, inc, int = "", "", ""
                if dec_key in list(rec.keys()) and cb.not_null(rec[dec_key], False):
                    dec = float(rec[dec_key])
                if inc_key in list(rec.keys()) and cb.not_null(rec[inc_key], False):
                    inc = float(rec[inc_key])
                for key in Mkeys:
                    if key in list(rec.keys()) and cb.not_null(rec[key], False):
                        int = float(rec[key])
                if inst_key not in list(rec.keys()):
                    rec[inst_key] = ''
                datablock.append(
                    [tr, dec, inc, int, ZI, rec[flag_key], rec[inst_key]])
    if therm_flag == 1:
        for k in range(len(datablock)):
            if datablock[k][0] == 0.:
                datablock[k][0] = 273.
    if af_flag == 1:
        for k in range(len(datablock)):
            if datablock[k][0] >= 273 and datablock[k][0] <= 323:
                datablock[k][0] = 0.
    meas_units = ""
    if len(units) > 0:
        for u in units:
            meas_units = meas_units + u + ":"
        meas_units = meas_units[:-1]
    return datablock, meas_units


def open_file(infile, verbose=True):
    """
    Open file and return a list of the file's lines.
    Try to use utf-8 encoding, and if that fails use Latin-1.

    Parameters
    ----------
    infile : str
        full path to file

    Returns
    ----------
    data: list
        all lines in the file
    """
    try:
        with codecs.open(infile, "r", "utf-8") as f:
            lines = list(f.readlines())
    # file might not exist
    except FileNotFoundError:
        if verbose:
            print(
                '-W- You are trying to open a file: {} that does not exist'.format(infile))
        return []
    # encoding might be wrong
    except UnicodeDecodeError:
        try:
            with codecs.open(infile, "r", "Latin-1") as f:
                print(
                    '-I- Using less strict decoding for {}, output may have formatting errors'.format(infile))
                lines = list(f.readlines())
        # if file exists, and encoding is correct, who knows what the problem is
        except Exception as ex:
            print("-W- ", type(ex), ex)
            return []
    except Exception as ex:
        print("-W- ", type(ex), ex)
        return []
    # don't leave a blank line at the end
    i = 0
    while i < 10:
        if not len(lines[-1].strip("\n").strip("\t")):
            lines = lines[:-1]
            i += 1
        else:
            i = 10
    return lines


def magic_read(infile, data=None, return_keys=False, verbose=False):
    """
    Reads  a Magic template file, returns  data in a list of dictionaries.

    Parameters
    ___________
        Required:
            infile : the MagIC formatted tab delimited data file
                first line contains 'tab' in the first column and the data file type in the second (e.g., measurements, specimen, sample, etc.)
        Optional:
            data : data read in with, e.g., file.readlines()
    Returns
    _______
        list of dictionaries, file type
    """
    if infile:
        if not os.path.exists(infile):
            if return_keys:
                return [], 'empty_file', []
            return [], 'empty_file'
    hold, magic_data, magic_record, magic_keys = [], [], {}, []
    if data:
        lines = list(data)
    elif (not data) and (not infile):
        if return_keys:
            return [], 'empty_file', []
        return [], 'empty_file'
    else:
        # if the file doesn't exist, end here
        if not os.path.exists(infile):
            if return_keys:
                return [], 'bad_file', []
            return [], 'bad_file'
        # use custom pmagpy open_file
        lines = open_file(infile, verbose=verbose)
    if not lines:
        if return_keys:
            return [], 'bad_file', []
        return [], 'bad_file'
    d_line = lines[0][:-1].strip('\n').strip('\r').strip('\t')
    if not d_line:
        if return_keys:
            return [], 'empty_file', []
        return [], 'empty_file'
    if d_line[0] == "s" or d_line[1] == "s":
        delim = 'space'
    elif d_line[0] == "t" or d_line[1] == "t":
        delim = 'tab'
    else:
        print('-W- error reading {}. Check that this is a MagIC-format file'.format(infile))
        if return_keys:
            return [], 'bad_file', []
        return [], 'bad_file'
    if delim == 'space':
        file_type = d_line.split()[1]
    if delim == 'tab':
        file_type = d_line.split('\t')[1]
    if file_type == 'delimited':
        if delim == 'space':
            file_type = d_line.split()[2]
        if delim == 'tab':
            file_type = d_line.split('\t')[2]
    line = lines[1].strip('\n').strip('\r')
    if delim == 'space':
        line = line.split()  # lines[1][:-1].split()
    if delim == 'tab':
        line = line.split('\t')  # lines[1][:-1].split('\t')
    for key in line:
        magic_keys.append(key)
    lines = lines[2:]
    if len(lines) < 1:
        if return_keys:
            return [], 'empty_file', []
        return [], 'empty_file'
    for line in lines[:-1]:
        line.replace('\n', '')
        if delim == 'space':
            rec = line[:-1].split()
        if delim == 'tab':
            rec = line[:-1].split('\t')
        hold.append(rec)
    line = lines[-1].replace('\n', '').replace('\r', '')
    if delim == 'space':
        rec = line[:-1].split()
    if delim == 'tab':
        rec = line.split('\t')
    hold.append(rec)
    for rec in hold:
        magic_record = {}
        if len(magic_keys) > len(rec):
            # pad rec with empty strings if needed
            for i in range(len(magic_keys) - len(rec)):
                rec.append('')
        if len(magic_keys) != len(rec):
            # ignores this warning when reading the dividers in an upload.txt
            # composite file
            if rec != ['>>>>>>>>>>'] and 'delimited' not in rec[0]:
                print("Warning: Uneven record lengths detected in {}: ".format(infile))
                print('keys:', magic_keys)
                print('record:', rec)
        # modified by Ron Shaar:
        # add a health check:
        # if len(magic_keys) > len(rec): take rec
        # if len(magic_keys) < len(rec): take magic_keys
        # original code: for k in range(len(rec)):
        # channged to: for k in range(min(len(magic_keys),len(rec))):
        for k in range(min(len(magic_keys), len(rec))):
            magic_record[magic_keys[k]] = rec[k].strip('\n').strip('\r')
        magic_data.append(magic_record)
    magictype = file_type.lower().split("_")
    Types = ['er', 'magic', 'pmag', 'rmag']
    if magictype in Types:
        file_type = file_type.lower()
    if return_keys:
        return magic_data, file_type, magic_keys
    return magic_data, file_type


def magic_read_dict(path, data=None, sort_by_this_name=None, return_keys=False):
    """
    Read a magic-formatted tab-delimited file and return a dictionary of
    dictionaries, with this format:
    {'Z35.5a': {'specimen_weight': '1.000e-03', 'er_citation_names': 'This study', 'specimen_volume': '', 'er_location_name': '', 'er_site_name': 'Z35.', 'er_sample_name': 'Z35.5', 'specimen_class': '', 'er_specimen_name': 'Z35.5a', 'specimen_lithology': '', 'specimen_type': ''}, ....}
    return data, file_type, and keys (if return_keys is true)
    """
    DATA = {}
    #fin = open(path, 'r')
    #first_line = fin.readline()
    lines = open_file(path)
    if not lines:
        if return_keys:
            return {}, 'empty_file', None
        else:
            return {}, 'empty_file'
    first_line = lines.pop(0)
    if first_line[0] == "s" or first_line[1] == "s":
        delim = ' '
    elif first_line[0] == "t" or first_line[1] == "t":
        delim = '\t'
    else:
        print('-W- error reading ', path)
        if return_keys:
            return {}, 'bad_file', None
        else:
            return {}, 'bad_file'

    file_type = first_line.strip('\n').strip('\r').split(delim)[1]

    item_type = file_type
    #item_type = file_type.split('_')[1][:-1]
    if sort_by_this_name:
        pass
    elif item_type == 'age':
        sort_by_this_name = "by_line_number"
    else:
        sort_by_this_name = item_type
    line = lines.pop(0)
    header = line.strip('\n').strip('\r').split(delim)
    counter = 0
    for line in lines:
        tmp_data = {}
        tmp_line = line.strip('\n').strip('\r').split(delim)
        for i in range(len(header)):
            if i < len(tmp_line):
                tmp_data[header[i]] = tmp_line[i].strip()
            else:
                tmp_data[header[i]] = ""
        if sort_by_this_name == "by_line_number":
            DATA[counter] = tmp_data
            counter += 1
        else:
            if tmp_data[sort_by_this_name] != "":
                DATA[tmp_data[sort_by_this_name]] = tmp_data
    if return_keys:
        return DATA, file_type, header
    else:
        return DATA, file_type


def sort_magic_data(magic_data, sort_name):
    '''
    Sort magic_data by header (like er_specimen_name for example)
    '''
    magic_data_sorted = {}
    for rec in magic_data:
        name = rec[sort_name]
        if name not in list(magic_data_sorted.keys()):
            magic_data_sorted[name] = []
        magic_data_sorted[name].append(rec)
    return magic_data_sorted


def upload_read(infile, table):
    """
    Reads a table from a MagIC upload (or downloaded) txt file, puts data in a
    list of dictionaries
    """
    delim = 'tab'
    hold, magic_data, magic_record, magic_keys = [], [], {}, []
    f = open(infile, "r")
#
# look for right table
#
    line = f.readline()[:-1]
    file_type = line.split('\t')[1]
    if file_type == 'delimited':
        file_type = line.split('\t')[2]
    if delim == 'tab':
        line = f.readline()[:-1].split('\t')
    else:
        f.close()
        print("only tab delimitted files are supported now")
        return
    while file_type != table:
        while line[0][0:5] in f.readlines() != ">>>>>":
            pass
        line = f.readline()[:-1]
        file_type = line.split('\t')[1]
        if file_type == 'delimited':
            file_type = line.split('\t')[2]
        ine = f.readline()[:-1].split('\t')
    while line[0][0:5] in f.readlines() != ">>>>>":
        for key in line:
            magic_keys.append(key)
        for line in f.readlines():
            rec = line[:-1].split('\t')
            hold.append(rec)
        for rec in hold:
            magic_record = {}
            if len(magic_keys) != len(rec):
                print("Uneven record lengths detected: ", rec)
                input("Return to continue.... ")
            for k in range(len(magic_keys)):
                magic_record[magic_keys[k]] = rec[k]
            magic_data.append(magic_record)
    f.close()
    return magic_data


def putout(ofile, keylist, Rec):
    """
    writes out a magic format record to ofile
    """
    pmag_out = open(ofile, 'a')
    outstring = ""
    for key in keylist:
        try:
            outstring = outstring + '\t' + str(Rec[key]).strip()
        except:
            print(key, Rec[key])
            # raw_input()
    outstring = outstring + '\n'
    pmag_out.write(outstring[1:])
    pmag_out.close()


def first_rec(ofile, Rec, file_type):
    """
    opens the file ofile as a magic template file with headers as the keys to Rec
    """
    keylist = []
    opened = False
    # sometimes Windows needs a little extra time to open a file
    # or else it throws an error
    while not opened:
        try:
            pmag_out = open(ofile, 'w')
            opened = True
        except IOError:
            time.sleep(1)
    outstring = "tab \t" + file_type + "\n"
    pmag_out.write(outstring)
    keystring = ""
    for key in list(Rec.keys()):
        keystring = keystring + '\t' + key.strip()
        keylist.append(key)
    keystring = keystring + '\n'
    pmag_out.write(keystring[1:])
    pmag_out.close()
    return keylist


def magic_write_old(ofile, Recs, file_type):
    """
    writes out a magic format list of dictionaries to ofile

    Parameters
    _________
    ofile : path to output file
    Recs : list of dictionaries in MagIC format
    file_type : MagIC table type (e.g., specimens)

    Effects :
        writes a MagIC formatted file from Recs
    """

    if len(Recs) < 1:
        return
    pmag_out = open(ofile, 'w')
    outstring = "tab \t" + file_type + "\n"
    pmag_out.write(outstring)
    keystring = ""
    keylist = []
    for key in list(Recs[0].keys()):
        keylist.append(key)
    keylist.sort()
    for key in keylist:
        keystring = keystring + '\t' + key.strip()
    keystring = keystring + '\n'
    pmag_out.write(keystring[1:])
    for Rec in Recs:
        outstring = ""
        for key in keylist:
            try:
                outstring = outstring + '\t' + str(Rec[key].strip())
            except:
                if 'er_specimen_name' in list(Rec.keys()):
                    print(Rec['er_specimen_name'])
                elif 'er_specimen_names' in list(Rec.keys()):
                    print(Rec['er_specimen_names'])
                print(key, Rec[key])
                # raw_input()
        outstring = outstring + '\n'
        pmag_out.write(outstring[1:])
    pmag_out.close()


def magic_write(ofile, Recs, file_type):
    """
    Parameters
    _________
    ofile : path to output file
    Recs : list of dictionaries in MagIC format
    file_type : MagIC table type (e.g., specimens)

    Return :
    [True,False] : True if successful
    ofile : same as input

    Effects :
        writes a MagIC formatted file from Recs

    """
    if len(Recs) < 1:
        return False, 'No records to write to file {}'.format(ofile)
    else:
        print(len(Recs), ' records written to file ', ofile)
    if os.path.split(ofile)[0] != "" and not os.path.isdir(os.path.split(ofile)[0]):
        os.mkdir(os.path.split(ofile)[0])
    pmag_out = open(ofile, 'w+', errors="backslashreplace")
    outstring = "tab \t" + file_type
    outstring = outstring.strip("\n").strip(
        "\r") + "\n"  # make sure it's clean for Windows
    pmag_out.write(outstring)
    keystring = ""
    keylist = []
    for key in list(Recs[0].keys()):
        keylist.append(key)
    keylist.sort()
    for key in keylist:
        keystring = keystring + '\t' + key.strip()
    keystring = keystring + '\n'
    pmag_out.write(keystring[1:])
    for Rec in Recs:
        outstring = ""
        for key in keylist:
            try:
                outstring = outstring + '\t' + str(Rec[key]).strip()
            except KeyError:
                if 'er_specimen_name' in list(Rec.keys()):
                    print(Rec['er_specimen_name'])
                elif 'specimen' in list(Rec.keys()):
                    print(Rec['specimen'])
                elif 'er_specimen_names' in list(Rec.keys()):
                    print('specimen names:', Rec['er_specimen_names'])
                print("No data for %s" % key)
                # just skip it:
                outstring = outstring + "\t"
                # raw_input()
        outstring = outstring + '\n'
        pmag_out.write(outstring[1:])
    pmag_out.close()
    return True, ofile


def dotilt(dec, inc, bed_az, bed_dip):
    """
    Does a tilt correction on a direction (dec,inc) using bedding dip direction
    and bedding dip.

    Parameters
    ----------
    dec : declination directions in degrees
    inc : inclination direction in degrees
    bed_az : bedding dip direction
    bed_dip : bedding dip

    Returns
    -------
    dec,inc : a tuple of rotated dec, inc values

    Examples
    -------
    >>> pmag.dotilt(91.2,43.1,90.0,20.0)
    (90.952568837153436, 23.103411670066617)
    """
    rad = old_div(np.pi, 180.)  # converts from degrees to radians
    X = dir2cart([dec, inc, 1.])  # get cartesian coordinates of dec,inc
# get some sines and cosines of new coordinate system
    sa, ca = -np.sin(bed_az * rad), np.cos(bed_az * rad)
    cdp, sdp = np.cos(bed_dip * rad), np.sin(bed_dip * rad)
# do the rotation
    xc = X[0] * (sa * sa + ca * ca * cdp) + X[1] * \
        (ca * sa * (1. - cdp)) + X[2] * sdp * ca
    yc = X[0] * ca * sa * (1. - cdp) + X[1] * \
        (ca * ca + sa * sa * cdp) - X[2] * sa * sdp
    zc = X[0] * ca * sdp - X[1] * sdp * sa - X[2] * cdp
# convert back to direction:
    Dir = cart2dir([xc, yc, -zc])
    # return declination, inclination of rotated direction
    return Dir[0], Dir[1]


def dotilt_V(indat):
    """
    Does a tilt correction on an array with rows of dec,inc bedding dip direction and dip.

    Parameters
    ----------
    input : declination, inclination, bedding dip direction and bedding dip
    nested array of [[dec1, inc1, bed_az1, bed_dip1],[dec2,inc2,bed_az2,bed_dip2]...]

    Returns
    -------
    dec,inc : arrays of rotated declination, inclination
    """
    indat = indat.transpose()
    # unpack input array into separate arrays
    dec, inc, bed_az, bed_dip = indat[0], indat[1], indat[2], indat[3]
    rad = old_div(np.pi, 180.)  # convert to radians
    Dir = np.array([dec, inc]).transpose()
    X = dir2cart(Dir).transpose()  # get cartesian coordinates
    N = np.size(dec)

# get some sines and cosines of new coordinate system
    sa, ca = -np.sin(bed_az * rad), np.cos(bed_az * rad)
    cdp, sdp = np.cos(bed_dip * rad), np.sin(bed_dip * rad)
# do the rotation
    xc = X[0] * (sa * sa + ca * ca * cdp) + X[1] * \
        (ca * sa * (1. - cdp)) + X[2] * sdp * ca
    yc = X[0] * ca * sa * (1. - cdp) + X[1] * \
        (ca * ca + sa * sa * cdp) - X[2] * sa * sdp
    zc = X[0] * ca * sdp - X[1] * sdp * sa - X[2] * cdp
# convert back to direction:
    cart = np.array([xc, yc, -zc]).transpose()
    Dir = cart2dir(cart).transpose()
    # return declination, inclination arrays of rotated direction
    return Dir[0], Dir[1]


def dogeo(dec, inc, az, pl):
    """
    Rotates declination and inclination into geographic coordinates using the
    azimuth and plunge of the X direction (lab arrow) of a specimen.

    Parameters
    ----------
    dec : declination in specimen coordinates
    inc : inclination in specimen coordinates

    Returns
    -------
    rotated_direction : tuple of declination, inclination in geographic coordinates

    Examples
    --------
    >>> pmag.dogeo(0.0,90.0,0.0,45.5)
    (180.0, 44.5)
    """
    A1, A2, A3 = [], [], []  # set up lists for rotation vector
    # put dec inc in direction list and set  length to unity
    Dir = [dec, inc, 1.]
    X = dir2cart(Dir)  # get cartesian coordinates
#
#   set up rotation matrix
#
    A1 = dir2cart([az, pl, 1.])
    A2 = dir2cart([az + 90., 0, 1.])
    A3 = dir2cart([az - 180., 90. - pl, 1.])
#
# do rotation
#
    xp = A1[0] * X[0] + A2[0] * X[1] + A3[0] * X[2]
    yp = A1[1] * X[0] + A2[1] * X[1] + A3[1] * X[2]
    zp = A1[2] * X[0] + A2[2] * X[1] + A3[2] * X[2]
#
# transform back to dec,inc
#
    Dir_geo = cart2dir([xp, yp, zp])
    return Dir_geo[0], Dir_geo[1]    # send back declination and inclination


def dogeo_V(indat):
    """
    Rotates declination and inclination into geographic coordinates using the
    azimuth and plunge of the X direction (lab arrow) of a specimen.

    Parameters
    ----------
    indat: nested list of [dec, inc, az, pl] data

    Returns
    -------
    rotated_directions : arrays of Declinations and Inclinations


    """
    indat = indat.transpose()
    # unpack input array into separate arrays
    dec, inc, az, pl = indat[0], indat[1], indat[2], indat[3]
    Dir = np.array([dec, inc]).transpose()
    X = dir2cart(Dir).transpose()  # get cartesian coordinates
    N = np.size(dec)
    A1 = dir2cart(np.array([az, pl, np.ones(N)]).transpose()).transpose()
    A2 = dir2cart(
        np.array([az + 90., np.zeros(N), np.ones(N)]).transpose()).transpose()
    A3 = dir2cart(
        np.array([az - 180., 90. - pl, np.ones(N)]).transpose()).transpose()

# do rotation
#
    xp = A1[0] * X[0] + A2[0] * X[1] + A3[0] * X[2]
    yp = A1[1] * X[0] + A2[1] * X[1] + A3[1] * X[2]
    zp = A1[2] * X[0] + A2[2] * X[1] + A3[2] * X[2]
    cart = np.array([xp, yp, zp]).transpose()
#
# transform back to dec,inc
#
    Dir_geo = cart2dir(cart).transpose()
    # send back declination and inclination arrays
    return Dir_geo[0], Dir_geo[1]


def dodirot(D, I, Dbar, Ibar):
    """
    Rotate a direction (declination, inclination) by the difference between
    dec=0 and inc = 90 and the provided desired mean direction

    Parameters
    ----------
    D : declination to be rotated
    I : inclination to be rotated
    Dbar : declination of desired mean
    Ibar : inclination of desired mean

    Returns
    ----------
    drot, irot : rotated declination and inclination
    """
    d, irot = dogeo(D, I, Dbar, 90. - Ibar)
    drot = d - 180.
    if drot < 360.:
        drot = drot + 360.
    if drot > 360.:
        drot = drot - 360.
    return drot, irot


def dodirot_V(di_block, Dbar, Ibar):
    """
    Rotate an array of dec/inc pairs to coordinate system with Dec,Inc as 0,90

    Parameters
    ___________________
    di_block : array of [[Dec1,Inc1],[Dec2,Inc2],....]
    Dbar : declination of desired center
    Ibar : inclination of desired center

    Returns
    __________
    array of rotated decs and incs: [[rot_Dec1,rot_Inc1],[rot_Dec2,rot_Inc2],....]
    """
    N = di_block.shape[0]
    DipDir, Dip = np.ones(N, dtype=np.float).transpose(
    )*(Dbar-180.), np.ones(N, dtype=np.float).transpose()*(90.-Ibar)
    di_block = di_block.transpose()
    data = np.array([di_block[0], di_block[1], DipDir, Dip]).transpose()
    drot, irot = dotilt_V(data)
    drot = (drot-180.) % 360.  #
    return np.column_stack((drot, irot))


def find_samp_rec(s, data, az_type):
    """
    find the orientation info for samp s
    """
    datablock, or_error, bed_error = [], 0, 0
    orient = {}
    orient["sample_dip"] = ""
    orient["sample_azimuth"] = ""
    orient['sample_description'] = ""
    for rec in data:
        if rec["er_sample_name"].lower() == s.lower():
            if 'sample_orientation_flag' in list(rec.keys()) and rec['sample_orientation_flag'] == 'b':
                orient['sample_orientation_flag'] = 'b'
                return orient
            if "magic_method_codes" in list(rec.keys()) and az_type != "0":
                methods = rec["magic_method_codes"].replace(" ", "").split(":")
                if az_type in methods and "sample_azimuth" in list(rec.keys()) and rec["sample_azimuth"] != "":
                    orient["sample_azimuth"] = float(rec["sample_azimuth"])
                if "sample_dip" in list(rec.keys()) and rec["sample_dip"] != "":
                    orient["sample_dip"] = float(rec["sample_dip"])
                if "sample_bed_dip_direction" in list(rec.keys()) and rec["sample_bed_dip_direction"] != "":
                    orient["sample_bed_dip_direction"] = float(
                        rec["sample_bed_dip_direction"])
                if "sample_bed_dip" in list(rec.keys()) and rec["sample_bed_dip"] != "":
                    orient["sample_bed_dip"] = float(rec["sample_bed_dip"])
            else:
                if "sample_azimuth" in list(rec.keys()):
                    orient["sample_azimuth"] = float(rec["sample_azimuth"])
                if "sample_dip" in list(rec.keys()):
                    orient["sample_dip"] = float(rec["sample_dip"])
                if "sample_bed_dip_direction" in list(rec.keys()):
                    orient["sample_bed_dip_direction"] = float(
                        rec["sample_bed_dip_direction"])
                if "sample_bed_dip" in list(rec.keys()):
                    orient["sample_bed_dip"] = float(rec["sample_bed_dip"])
                if 'sample_description' in list(rec.keys()):
                    orient['sample_description'] = rec['sample_description']
        if orient["sample_azimuth"] != "":
            break
    return orient


def vspec(data):
    """
    Takes the vector mean of replicate measurements at a given step
    """
    vdata, Dirdata, step_meth = [], [], []
    tr0 = data[0][0]  # set beginning treatment
    data.append("Stop")
    k, R = 1, 0
    for i in range(k, len(data)):
        Dirdata = []
        if data[i][0] != tr0:
            if i == k:  # sample is unique
                vdata.append(data[i - 1])
                step_meth.append(" ")
            else:  # sample is not unique
                for l in range(k - 1, i):
                    Dirdata.append([data[l][1], data[l][2], data[l][3]])
                dir, R = vector_mean(Dirdata)
                vdata.append([data[i - 1][0], dir[0], dir[1],
                              old_div(R, (i - k + 1)), '1', 'g'])
                step_meth.append("DE-VM")
            tr0 = data[i][0]
            k = i + 1
            if tr0 == "stop":
                break
    del data[-1]
    return step_meth, vdata


def Vdiff(D1, D2):
    """
    finds the vector difference between two directions D1,D2
    """
    A = dir2cart([D1[0], D1[1], 1.])
    B = dir2cart([D2[0], D2[1], 1.])
    C = []
    for i in range(3):
        C.append(A[i] - B[i])
    return cart2dir(C)


def angle(D1, D2):
    """
    Calculate the angle between two directions.

    Parameters
    ----------
    D1 : Direction 1 as an array of [declination, inclination] pair or pairs
    D2 : Direction 2 as an array of [declination, inclination] pair or pairs

    Returns
    -------
    angle : angle between the directions as a single-element array

    Examples
    --------
    >>> pmag.angle([350.0,10.0],[320.0,20.0])
    array([ 30.59060998])
    """
    D1 = np.array(D1)
    if len(D1.shape) > 1:
        D1 = D1[:, 0:2]  # strip off intensity
    else:
        D1 = D1[:2]
    D2 = np.array(D2)
    if len(D2.shape) > 1:
        D2 = D2[:, 0:2]  # strip off intensity
    else:
        D2 = D2[:2]
    X1 = dir2cart(D1)  # convert to cartesian from polar
    X2 = dir2cart(D2)
    angles = []  # set up a list for angles
    for k in range(X1.shape[0]):  # single vector
        angle = np.arccos(np.dot(X1[k], X2[k])) * \
            180. / np.pi  # take the dot product
        angle = angle % 360.
        angles.append(angle)
    return np.array(angles)


def cart2dir(cart):
    """
    Converts a direction in cartesian coordinates into declination, inclinations

    Parameters
    ----------
    cart : input list of [x,y,z] or list of lists [[x1,y1,z1],[x2,y2,z2]...]

    Returns
    -------
    direction_array : returns an array of [declination, inclination, intensity]

    Examples
    --------
    >>> pmag.cart2dir([0,1,0])
    array([ 90.,   0.,   1.])
    """
    cart = np.array(cart)
    rad = old_div(np.pi, 180.)  # constant to convert degrees to radians
    if len(cart.shape) > 1:
        Xs, Ys, Zs = cart[:, 0], cart[:, 1], cart[:, 2]
    else:  # single vector
        Xs, Ys, Zs = cart[0], cart[1], cart[2]
    if np.iscomplexobj(Xs):
        Xs = Xs.real
    if np.iscomplexobj(Ys):
        Ys = Ys.real
    if np.iscomplexobj(Zs):
        Zs = Zs.real
    Rs = np.sqrt(Xs**2 + Ys**2 + Zs**2)  # calculate resultant vector length
    # calculate declination taking care of correct quadrants (arctan2) and
    # making modulo 360.
    Decs = (old_div(np.arctan2(Ys, Xs), rad)) % 360.
    try:
        # calculate inclination (converting to degrees) #
        Incs = old_div(np.arcsin(old_div(Zs, Rs)), rad)
    except:
        print('trouble in cart2dir')  # most likely division by zero somewhere
        return np.zeros(3)

    return np.array([Decs, Incs, Rs]).transpose()  # return the directions list


def tauV(T):
    """
    Gets the eigenvalues (tau) and eigenvectors (V) from matrix T
    """
    t, V, tr = [], [], 0.
    ind1, ind2, ind3 = 0, 1, 2
    evalues, evectmps = linalg.eig(T)
    # to make compatible with Numeric convention
    evectors = np.transpose(evectmps)
    for tau in evalues:
        tr += tau
    if tr != 0:
        for i in range(3):
            evalues[i] = old_div(evalues[i], tr)
    else:
        return t, V
# sort evalues,evectors
    t1, t2, t3 = 0., 0., 1.
    for k in range(3):
        if evalues[k] > t1:
            t1, ind1 = evalues[k], k
        if evalues[k] < t3:
            t3, ind3 = evalues[k], k
    for k in range(3):
        if evalues[k] != t1 and evalues[k] != t3:
            t2, ind2 = evalues[k], k
    V.append(evectors[ind1])
    V.append(evectors[ind2])
    V.append(evectors[ind3])
    t.append(t1)
    t.append(t2)
    t.append(t3)
    return t, V


def Tmatrix(X):
    """
    gets the orientation matrix (T) from data in X
    """
    T = [[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]]
    for row in X:
        for k in range(3):
            for l in range(3):
                T[k][l] += row[k] * row[l]
    return T


def dir2cart(d):
    """
    Converts a list or array of vector directions in degrees (declination,
    inclination) to an array of the direction in cartesian coordinates (x,y,z)

    Parameters
    ----------
    d : list or array of [dec,inc] or [dec,inc,intensity]

    Returns
    -------
    cart : array of [x,y,z]

    Examples
    --------
    >>> pmag.dir2cart([200,40,1])
    array([-0.71984631, -0.26200263,  0.64278761])
    """
    ints = np.ones(len(d)).transpose(
    )  # get an array of ones to plug into dec,inc pairs
    d = np.array(d)
    rad = np.pi/180.
    if len(d.shape) > 1:  # array of vectors
        decs, incs = d[:, 0] * rad, d[:, 1] * rad
        if d.shape[1] == 3:
            ints = d[:, 2]  # take the given lengths
    else:  # single vector
        decs, incs = np.array(float(d[0])) * rad, np.array(float(d[1])) * rad
        if len(d) == 3:
            ints = np.array(d[2])
        else:
            ints = np.array([1.])
    cart = np.array([ints * np.cos(decs) * np.cos(incs), ints *
                     np.sin(decs) * np.cos(incs), ints * np.sin(incs)]).transpose()
    return cart


def dms2dd(d):
    # converts list or array of degree, minute, second locations to array of
    # decimal degrees
    d = np.array(d)
    if len(d.shape) > 1:  # array of angles
        degs, mins, secs = d[:, 0], d[:, 1], d[:, 2]
        print(degs, mins, secs)
    else:  # single vector
        degs, mins, secs = np.array(d[0]), np.array(d[1]), np.array(d[2])
        print(degs, mins, secs)
    dd = np.array(degs + old_div(mins, 60.) + old_div(secs, 3600.)).transpose()
    return dd


def findrec(s, data):
    """
    finds all the records belonging to s in data
    """
    datablock = []
    for rec in data:
        if s == rec[0]:
            datablock.append([rec[1], rec[2], rec[3], rec[4]])
    return datablock


def domean(data, start, end, calculation_type):
    """
    Gets average direction using Fisher or principal component analysis (line
    or plane) methods

    Parameters
    ----------
    data : nest list of data: [[treatment,dec,inc,int,quality],...]
    start : step being used as start of fit (often temperature minimum)
    end : step being used as end of fit (often temperature maximum)
    calculation_type : string describing type of calculation to be made
    'DE-BFL' (line), 'DE-BFL-A' (line-anchored), 'DE-BFL-O' (line-with-origin),
    'DE-BFP' (plane), 'DE-FM' (Fisher mean)

    Returns
    -------
    mpars : dictionary with the keys "specimen_n","measurement_step_min",
    "measurement_step_max","specimen_mad","specimen_dec","specimen_inc"
    """
    mpars = {}
    datablock = []
    start0, end0 = start, end
    # indata = [rec.append('g') if len(rec)<6 else rec for rec in indata] #
    # this statement doesn't work!
    indata = []
    for rec in data:
        if len(rec) < 6:
            rec.append('g')
        indata.append(rec)
    if indata[start0][5] == 'b':
        print("Can't select 'bad' point as start for PCA")
    flags = [x[5] for x in indata]
    bad_before_start = flags[:start0].count('b')
    bad_in_mean = flags[start0:end0 + 1].count('b')
    start = start0 - bad_before_start
    end = end0 - bad_before_start - bad_in_mean
    datablock = [x for x in indata if x[5] == 'g']
    if indata[start0] != datablock[start]:
        print('problem removing bad data in pmag.domean start of datablock shifted:\norigional: %d\nafter removal: %d' % (
            start0, indata.index(datablock[start])))
    if indata[end0] != datablock[end]:
        print('problem removing bad data in pmag.domean end of datablock shifted:\norigional: %d\nafter removal: %d' % (
            end0, indata.index(datablock[end])))
    mpars["calculation_type"] = calculation_type
    rad = old_div(np.pi, 180.)
    if end > len(datablock) - 1 or end < start:
        end = len(datablock) - 1
    control, data, X, Nrec = [], [], [], float(end - start + 1)
    cm = [0., 0., 0.]
#
#  get cartesian coordinates
#
    fdata = []
    for k in range(start, end + 1):
        if calculation_type == 'DE-BFL' or calculation_type == 'DE-BFL-A' or calculation_type == 'DE-BFL-O':  # best-fit line
            data = [datablock[k][1], datablock[k][2], datablock[k][3]]
        else:
            data = [datablock[k][1], datablock[k][2], 1.0]  # unit weight
        fdata.append(data)
        cart = dir2cart(data)
        X.append(cart)
    if calculation_type == 'DE-BFL-O':  # include origin as point
        X.append([0., 0., 0.])
        # pass
    if calculation_type == 'DE-FM':  # for fisher means
        fpars = fisher_mean(fdata)
        mpars["specimen_direction_type"] = 'l'
        mpars["specimen_dec"] = fpars["dec"]
        mpars["specimen_inc"] = fpars["inc"]
        mpars["specimen_alpha95"] = fpars["alpha95"]
        mpars["specimen_n"] = fpars["n"]
        mpars["specimen_r"] = fpars["r"]
        mpars["measurement_step_min"] = indata[start0][0]
        mpars["measurement_step_max"] = indata[end0][0]
        mpars["center_of_mass"] = cm
        mpars["specimen_dang"] = -1
        return mpars
#
#   get center of mass for principal components (DE-BFL or DE-BFP)
#
    for cart in X:
        for l in range(3):
            cm[l] += old_div(cart[l], Nrec)
    mpars["center_of_mass"] = cm

#
#   transform to center of mass (if best-fit line)
#
    if calculation_type != 'DE-BFP':
        mpars["specimen_direction_type"] = 'l'
    if calculation_type == 'DE-BFL' or calculation_type == 'DE-BFL-O':  # not for planes or anchored lines
        for k in range(len(X)):
            for l in range(3):
                X[k][l] = X[k][l] - cm[l]
    else:
        mpars["specimen_direction_type"] = 'p'

#
#   put in T matrix
#
    T = np.array(Tmatrix(X))
#
#   get sorted evals/evects
#
    t, V = tauV(T)
    if t == []:
        mpars["specimen_direction_type"] = "Error"
        print("Error in calculation")
        return mpars
    v1, v3 = V[0], V[2]
    if t[2] < 0:
        t[2] = 0  # make positive
    if calculation_type == 'DE-BFL-A':
        Dir, R = vector_mean(fdata)
        mpars["specimen_direction_type"] = 'l'
        mpars["specimen_dec"] = Dir[0]
        mpars["specimen_inc"] = Dir[1]
        mpars["specimen_n"] = len(fdata)
        mpars["measurement_step_min"] = indata[start0][0]
        mpars["measurement_step_max"] = indata[end0][0]
        mpars["center_of_mass"] = cm
        s1 = np.sqrt(t[0])
        MAD = old_div(np.arctan(old_div(np.sqrt(t[1] + t[2]), s1)), rad)
        if np.iscomplexobj(MAD):
            MAD = MAD.real
        # I think this is how it is done - i never anchor the "PCA" - check
        mpars["specimen_mad"] = MAD
        return mpars
    if calculation_type != 'DE-BFP':
        #
        #   get control vector for principal component direction
        #
        rec = [datablock[start][1], datablock[start][2], datablock[start][3]]
        P1 = dir2cart(rec)
        rec = [datablock[end][1], datablock[end][2], datablock[end][3]]
        P2 = dir2cart(rec)
#
#   get right direction along principal component
##
        for k in range(3):
            control.append(P1[k] - P2[k])
        # changed by rshaar
        # control is taken as the center of mass
        # control=cm

        dot = 0
        for k in range(3):
            dot += v1[k] * control[k]
        if dot < -1:
            dot = -1
        if dot > 1:
            dot = 1
        if np.arccos(dot) > old_div(np.pi, 2.):
            for k in range(3):
                v1[k] = -v1[k]
#   get right direction along principal component
#
        s1 = np.sqrt(t[0])
        Dir = cart2dir(v1)
        MAD = old_div(np.arctan(old_div(np.sqrt(t[1] + t[2]), s1)), rad)
        if np.iscomplexobj(MAD):
            MAD = MAD.real
    if calculation_type == "DE-BFP":
        Dir = cart2dir(v3)
        MAD = old_div(
            np.arctan(np.sqrt(old_div(t[2], t[1]) + old_div(t[2], t[0]))), rad)
        if np.iscomplexobj(MAD):
            MAD = MAD.real
#
#   get angle with  center of mass
#
    CMdir = cart2dir(cm)
    Dirp = [Dir[0], Dir[1], 1.]
    dang = angle(CMdir, Dirp)
    mpars["specimen_dec"] = Dir[0]
    mpars["specimen_inc"] = Dir[1]
    mpars["specimen_mad"] = MAD
    # mpars["specimen_n"]=int(Nrec)
    mpars["specimen_n"] = len(X)
    mpars["specimen_dang"] = dang[0]
    mpars["measurement_step_min"] = indata[start0][0]
    mpars["measurement_step_max"] = indata[end0][0]
    return mpars


def circ(dec, dip, alpha):
    """
    function to calculate points on an circle about dec,dip with angle alpha
    """
    rad = old_div(np.pi, 180.)
    D_out, I_out = [], []
    dec, dip, alpha = dec * rad, dip * rad, alpha * rad
    dec1 = dec + old_div(np.pi, 2.)
    isign = 1
    if dip != 0:
        isign = (old_div(abs(dip), dip))
    dip1 = (dip - isign * (old_div(np.pi, 2.)))
    t = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    v = [0, 0, 0]
    t[0][2] = np.cos(dec) * np.cos(dip)
    t[1][2] = np.sin(dec) * np.cos(dip)
    t[2][2] = np.sin(dip)
    t[0][1] = np.cos(dec) * np.cos(dip1)
    t[1][1] = np.sin(dec) * np.cos(dip1)
    t[2][1] = np.sin(dip1)
    t[0][0] = np.cos(dec1)
    t[1][0] = np.sin(dec1)
    t[2][0] = 0
    for i in range(101):
        psi = float(i) * np.pi / 50.
        v[0] = np.sin(alpha) * np.cos(psi)
        v[1] = np.sin(alpha) * np.sin(psi)
        v[2] = np.sqrt(abs(1. - v[0]**2 - v[1]**2))
        elli = [0, 0, 0]
        for j in range(3):
            for k in range(3):
                elli[j] = elli[j] + t[j][k] * v[k]
        Dir = cart2dir(elli)
        D_out.append(Dir[0])
        I_out.append(Dir[1])
    return D_out, I_out


def PintPars(datablock, araiblock, zijdblock, start, end, accept, **kwargs):
    """
     calculate the paleointensity magic parameters  make some definitions
    """
    if 'version' in list(kwargs.keys()) and kwargs['version'] == 3:
        meth_key = 'method_codes'
        beta_key = 'int_b_beta'
        temp_key, min_key, max_key = 'treat_temp', 'meas_step_min', 'meas_step_max'
        dc_theta_key, dc_phi_key = 'treat_dc_field_theta', 'treat_dc_field_phi'
        # convert dataframe to list of dictionaries
        datablock = datablock.to_dict('records')
        z_key = 'int_z'
        drats_key = 'int_drats'
        drat_key = 'int_drat'
        md_key = 'int_md'
        dec_key = 'dir_dec'
        inc_key = 'dir_inc'
        mad_key = 'int_mad_free'
        dang_key = 'int_dang'
        ptrm_key = 'int_n_ptrm'
        theta_key = 'int_theta'
        gamma_key = 'int_gamma'
        delta_key = 'int_delta'
        frac_key = 'int_frac'
        gmax_key = 'int_gmax'
        scat_key = 'int_scat'
    else:
        beta_key = 'specimen_b_beta'
        meth_key = 'magic_method_codes'
        temp_key, min_key, max_key = 'treatment_temp', 'measurement_step_min', 'measurement_step_max'
        z_key = 'specimen_z'
        drats_key = 'specimen_drats'
        drat_key = 'specimen_drat'
        md_key = 'specimen_md'
        dec_key = 'specimen_dec'
        inc_key = 'specimen_inc'
        mad_key = 'specimen_int_mad'
        dang_key = 'specimen_dang'
        ptrm_key = 'specimen_int_ptrm_n'
        theta_key = 'specimen_theta'
        gamma_key = 'specimen_gamma'
        delta_key = 'specimen_delta'
        frac_key = 'specimen_frac'
        gmax_key = 'specimen_gmax'
        scat_key = 'specimen_scat'

    first_Z, first_I, zptrm_check, ptrm_check, ptrm_tail = [], [], [], [], []
    methcode, ThetaChecks, DeltaChecks, GammaChecks = "", "", "", ""
    zptrm_check = []
    first_Z, first_I, ptrm_check, ptrm_tail, zptrm_check, GammaChecks = araiblock[
        0], araiblock[1], araiblock[2], araiblock[3], araiblock[4], araiblock[5]
    if len(araiblock) > 6:
        # used only for perpendicular method of paleointensity
        ThetaChecks = araiblock[6]
        # used only for perpendicular  method of paleointensity
        DeltaChecks = araiblock[7]
    xi, yi, diffcum = [], [], 0
    xiz, xzi, yiz, yzi = [], [], [], []
    Nptrm, dmax = 0, -1e-22
# check if even zero and infield steps
    if len(first_Z) > len(first_I):
        maxe = len(first_I) - 1
    else:
        maxe = len(first_Z) - 1
    if end == 0 or end > maxe:
        end = maxe
# get the MAD, DANG, etc. for directional data
    bstep = araiblock[0][start][0]
    estep = araiblock[0][end][0]
    zstart, zend = 0, len(zijdblock)
    for k in range(len(zijdblock)):
        zrec = zijdblock[k]
        if zrec[0] == bstep:
            zstart = k
        if zrec[0] == estep:
            zend = k
    PCA = domean(zijdblock, zstart, zend, 'DE-BFL')
    D, Diz, Dzi, Du = [], [], [], []  # list of NRM vectors, and separated by zi and iz
    for rec in zijdblock:
        D.append((rec[1], rec[2], rec[3]))
        Du.append((rec[1], rec[2]))
        if rec[4] == 1:
            Dzi.append((rec[1], rec[2]))  # if this is ZI step
        else:
            Diz.append((rec[1], rec[2]))  # if this is IZ step
# calculate the vector difference sum
    vds = dovds(D)
    b_zi, b_iz = [], []
# collect data included in ZigZag calculation
    if end + 1 >= len(first_Z):
        stop = end - 1
    else:
        stop = end
    for k in range(start, end + 1):
        for l in range(len(first_I)):
            irec = first_I[l]
            if irec[0] == first_Z[k][0]:
                xi.append(irec[3])
                yi.append(first_Z[k][3])
    pars, errcode = int_pars(xi, yi, vds)
    if errcode == 1:
        return pars, errcode
#    for k in range(start,end+1):
    for k in range(len(first_Z) - 1):
        for l in range(k):
            # only go down to 10% of NRM.....
            if old_div(first_Z[k][3], vds) > 0.1:
                irec = first_I[l]
                if irec[4] == 1 and first_I[l + 1][4] == 0:  # a ZI step
                    xzi = irec[3]
                    yzi = first_Z[k][3]
                    xiz = first_I[l + 1][3]
                    yiz = first_Z[k + 1][3]
                    slope = np.arctan2((yzi - yiz), (xiz - xzi))
                    r = np.sqrt((yzi - yiz)**2 + (xiz - xzi)**2)
                    if r > .1 * vds:
                        b_zi.append(slope)  # suppress noise
                elif irec[4] == 0 and first_I[l + 1][4] == 1:  # an IZ step
                    xiz = irec[3]
                    yiz = first_Z[k][3]
                    xzi = first_I[l + 1][3]
                    yzi = first_Z[k + 1][3]
                    slope = np.arctan2((yiz - yzi), (xzi - xiz))
                    r = np.sqrt((yiz - yzi)**2 + (xzi - xiz)**2)
                    if r > .1 * vds:
                        b_iz.append(slope)  # suppress noise
#
    ZigZag, Frat, Trat = -1, 0, 0
    if len(Diz) > 2 and len(Dzi) > 2:
        ZigZag = 0
        dizp = fisher_mean(Diz)  # get Fisher stats on IZ steps
        dzip = fisher_mean(Dzi)  # get Fisher stats on ZI steps
        dup = fisher_mean(Du)  # get Fisher stats on all steps
#
# if directions are TOO well grouped, can get false positive for ftest, so
# angles must be > 3 degrees apart.
#
        if angle([dizp['dec'], dizp['inc']], [dzip['dec'], dzip['inc']]) > 3.:
            F = (dup['n'] - 2.) * (dzip['r'] + dizp['r'] - dup['r']) / \
                (dup['n'] - dzip['r'] - dizp['r']
                 )  # Watson test for common mean
            nf = 2. * (dup['n'] - 2.)  # number of degees of freedom
            ftest = fcalc(2, nf)
            Frat = old_div(F, ftest)
            if Frat > 1.:
                ZigZag = Frat  # fails zigzag on directions
                methcode = "SM-FTEST"
# now do slopes
    if len(b_zi) > 2 and len(b_iz) > 2:
        bzi_m, bzi_sig = gausspars(b_zi)  # mean, std dev
        biz_m, biz_sig = gausspars(b_iz)
        n_zi = float(len(b_zi))
        n_iz = float(len(b_iz))
        b_diff = abs(bzi_m - biz_m)  # difference in means
#
# avoid false positives - set 3 degree slope difference here too
        if b_diff > 3 * np.pi / 180.:
            nf = n_zi + n_iz - 2.  # degrees of freedom
            svar = old_div(((n_zi - 1.) * bzi_sig**2 +
                            (n_iz - 1.) * biz_sig**2), nf)
            T = old_div((b_diff), np.sqrt(
                svar * (old_div(1.0, n_zi) + old_div(1.0, n_iz))))  # student's t
            ttest = tcalc(nf, .05)  # t-test at 95% conf.
            Trat = old_div(T, ttest)
            if Trat > 1 and Trat > Frat:
                ZigZag = Trat  # fails zigzag on directions
                methcode = "SM-TTEST"
    pars[z_key] = ZigZag
    pars[meth_key] = methcode
# do drats
    if len(ptrm_check) != 0:
        diffcum, drat_max = 0, 0
        for prec in ptrm_check:
            step = prec[0]
            endbak = end
            zend = end
            while zend > len(zijdblock) - 1:
                zend = zend - 2  # don't count alteration that happens after this step
            if step < zijdblock[zend][0]:
                Nptrm += 1
                for irec in first_I:
                    if irec[0] == step:
                        break
                diffcum += prec[3] - irec[3]
                if abs(prec[3] - irec[3]) > drat_max:
                    drat_max = abs(prec[3] - irec[3])
        pars[drats_key] = (100 * abs(diffcum) / first_I[zend][3])
        pars[drat_key] = (100 * abs(drat_max) / first_I[zend][3])
    elif len(zptrm_check) != 0:
        diffcum = 0
        for prec in zptrm_check:
            step = prec[0]
            endbak = end
            zend = end
            while zend > len(zijdblock) - 1:
                zend = zend - 1
            if step < zijdblock[zend][0]:
                Nptrm += 1
                for irec in first_I:
                    if irec[0] == step:
                        break
                diffcum += prec[3] - irec[3]
        pars[drats_key] = (100 * abs(diffcum) / first_I[zend][3])
    else:
        pars[drats_key] = -1
        pars[drat_key] = -1
# and the pTRM tails
    if len(ptrm_tail) != 0:
        for trec in ptrm_tail:
            step = trec[0]
            for irec in first_I:
                if irec[0] == step:
                    break
            if abs(trec[3]) > dmax:
                dmax = abs(trec[3])
        pars[md_key] = (100 * dmax / vds)
    else:
        pars[md_key] = -1
    pars[min_key] = bstep
    pars[max_key] = estep
    pars[dec_key] = PCA["specimen_dec"]
    pars[inc_key] = PCA["specimen_inc"]
    pars[mad_key] = PCA["specimen_mad"]
    pars[dang_key] = PCA["specimen_dang"]
    pars[ptrm_key] = Nptrm
# and the ThetaChecks
    if ThetaChecks != "":
        t = 0
        for theta in ThetaChecks:
            if theta[0] >= bstep and theta[0] <= estep and theta[1] > t:
                t = theta[1]
        pars[theta_key] = t
    else:
        pars[theta_key] = -1
# and the DeltaChecks
    if DeltaChecks != "":
        d = 0
        for delta in DeltaChecks:
            if delta[0] >= bstep and delta[0] <= estep and delta[1] > d:
                d = delta[1]
        pars[delta_key]
    else:
        pars[delta_key] = -1
    pars[gamma_key] = -1
    if GammaChecks != "":
        for gamma in GammaChecks:
            if gamma[0] <= estep:
                pars['specimen_gamma'] = gamma[1]

    # --------------------------------------------------------------
    # From here added By Ron Shaar 11-Dec 2012
    # New parameters defined in Shaar and Tauxe (2012):
    # FRAC (specimen_frac) - ranges from 0. to 1.
    # SCAT (specimen_scat) - takes 1/0
    # gap_max (specimen_gmax) - ranges from 0. to 1.
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    # FRAC is similar to Fvds, but the numerator is the vds fraction:
    # FRAC= [ vds (start,end)] / total vds ]
    # gap_max= max [ (vector difference) /  vds (start,end)]
    # --------------------------------------------------------------

    # collect all zijderveld data to arrays and calculate VDS

    z_temperatures = [row[0] for row in zijdblock]
    zdata = []                # array of zero-fields measurements in Cartezian coordinates
    # array of vector differences (for vds calculation)
    vector_diffs = []
    NRM = zijdblock[0][3]     # NRM

    for k in range(len(zijdblock)):
        DIR = [zijdblock[k][1], zijdblock[k][2], old_div(zijdblock[k][3], NRM)]
        cart = dir2cart(DIR)
        zdata.append(np.array([cart[0], cart[1], cart[2]]))
        if k > 0:
            vector_diffs.append(
                np.sqrt(sum((np.array(zdata[-2]) - np.array(zdata[-1]))**2)))
    # last vector difference: from the last point to the origin.
    vector_diffs.append(np.sqrt(sum(np.array(zdata[-1])**2)))
    vds = sum(vector_diffs)  # vds calculation
    zdata = np.array(zdata)
    vector_diffs = np.array(vector_diffs)

    # calculate the vds within the chosen segment
    vector_diffs_segment = vector_diffs[zstart:zend]
    # FRAC calculation
    FRAC = old_div(sum(vector_diffs_segment), vds)
    pars[frac_key] = FRAC

    # gap_max calculation
    max_FRAC_gap = max(
        old_div(vector_diffs_segment, sum(vector_diffs_segment)))
    pars[gmax_key] = max_FRAC_gap

    # ---------------------------------------------------------------------
    # Calculate the "scat box"
    # all data-points, pTRM checks, and tail-checks, should be inside a "scat box"
    # ---------------------------------------------------------------------

    # intialization
    # fail scat due to arai plot data points
    pars["fail_arai_beta_box_scatter"] = False
    pars["fail_ptrm_beta_box_scatter"] = False  # fail scat due to pTRM checks
    pars["fail_tail_beta_box_scatter"] = False  # fail scat due to tail checks
    pars[scat_key] = "1"  # Pass by default

    # --------------------------------------------------------------
    # collect all Arai plot data points in arrays

    x_Arai, y_Arai, t_Arai, steps_Arai = [], [], [], []
    NRMs = araiblock[0]
    PTRMs = araiblock[1]
    ptrm_checks = araiblock[2]
    ptrm_tail = araiblock[3]

    PTRMs_temperatures = [row[0] for row in PTRMs]
    NRMs_temperatures = [row[0] for row in NRMs]
    NRM = NRMs[0][3]

    for k in range(len(NRMs)):
        index_pTRMs = PTRMs_temperatures.index(NRMs[k][0])
        x_Arai.append(old_div(PTRMs[index_pTRMs][3], NRM))
        y_Arai.append(old_div(NRMs[k][3], NRM))
        t_Arai.append(NRMs[k][0])
        if NRMs[k][4] == 1:
            steps_Arai.append('ZI')
        else:
            steps_Arai.append('IZ')
    x_Arai = np.array(x_Arai)
    y_Arai = np.array(y_Arai)

    # --------------------------------------------------------------
    # collect all pTRM check to arrays

    x_ptrm_check, y_ptrm_check, ptrm_checks_temperatures, = [], [], []
    x_ptrm_check_starting_point, y_ptrm_check_starting_point, ptrm_checks_starting_temperatures = [], [], []

    for k in range(len(ptrm_checks)):
        if ptrm_checks[k][0] in NRMs_temperatures:
            # find the starting point of the pTRM check:
            for i in range(len(datablock)):
                rec = datablock[i]
                if "LT-PTRM-I" in rec[meth_key] and float(rec[temp_key]) == ptrm_checks[k][0]:
                    starting_temperature = (float(datablock[i - 1][temp_key]))
                    try:
                        index = t_Arai.index(starting_temperature)
                        x_ptrm_check_starting_point.append(x_Arai[index])
                        y_ptrm_check_starting_point.append(y_Arai[index])
                        ptrm_checks_starting_temperatures.append(
                            starting_temperature)

                        index_zerofield = zerofield_temperatures.index(
                            ptrm_checks[k][0])
                        x_ptrm_check.append(old_div(ptrm_checks[k][3], NRM))
                        y_ptrm_check.append(
                            old_div(zerofields[index_zerofield][3], NRM))
                        ptrm_checks_temperatures.append(ptrm_checks[k][0])

                        break
                    except:
                        pass

    x_ptrm_check_starting_point = np.array(x_ptrm_check_starting_point)
    y_ptrm_check_starting_point = np.array(y_ptrm_check_starting_point)
    ptrm_checks_starting_temperatures = np.array(
        ptrm_checks_starting_temperatures)
    x_ptrm_check = np.array(x_ptrm_check)
    y_ptrm_check = np.array(y_ptrm_check)
    ptrm_checks_temperatures = np.array(ptrm_checks_temperatures)

    # --------------------------------------------------------------
    # collect tail checks to arrays

    x_tail_check, y_tail_check, tail_check_temperatures = [], [], []
    x_tail_check_starting_point, y_tail_check_starting_point, tail_checks_starting_temperatures = [], [], []

    for k in range(len(ptrm_tail)):
        if ptrm_tail[k][0] in NRMs_temperatures:

            # find the starting point of the pTRM check:
            for i in range(len(datablock)):
                rec = datablock[i]
                if "LT-PTRM-MD" in rec[meth_key] and float(rec[temp_key]) == ptrm_tail[k][0]:
                    starting_temperature = (float(datablock[i - 1][temp_key]))
                    try:

                        index = t_Arai.index(starting_temperature)
                        x_tail_check_starting_point.append(x_Arai[index])
                        y_tail_check_starting_point.append(y_Arai[index])
                        tail_checks_starting_temperatures.append(
                            starting_temperature)

                        index_infield = infield_temperatures.index(
                            ptrm_tail[k][0])
                        x_tail_check.append(
                            old_div(infields[index_infield][3], NRM))
                        y_tail_check.append(
                            old_div(ptrm_tail[k][3], NRM) + old_div(zerofields[index_infield][3], NRM))
                        tail_check_temperatures.append(ptrm_tail[k][0])

                        break
                    except:
                        pass

    x_tail_check = np.array(x_tail_check)
    y_tail_check = np.array(y_tail_check)
    tail_check_temperatures = np.array(tail_check_temperatures)
    x_tail_check_starting_point = np.array(x_tail_check_starting_point)
    y_tail_check_starting_point = np.array(y_tail_check_starting_point)
    tail_checks_starting_temperatures = np.array(
        tail_checks_starting_temperatures)

    # --------------------------------------------------------------
    # collect the chosen segment in the Arai plot to arrays

    x_Arai_segment = x_Arai[start:end + 1]  # chosen segent in the Arai plot
    y_Arai_segment = y_Arai[start:end + 1]  # chosen segent in the Arai plot

    # --------------------------------------------------------------
    # collect pTRM checks in segment to arrays
    # notice, this is different than the conventional DRATS.
    # for scat calculation we take only the pTRM checks which were carried out
    # before reaching the highest temperature in the chosen segment

    x_ptrm_check_for_SCAT, y_ptrm_check_for_SCAT = [], []
    for k in range(len(ptrm_checks_temperatures)):
        if ptrm_checks_temperatures[k] >= pars[min_key] and ptrm_checks_starting_temperatures <= pars[max_key]:
            x_ptrm_check_for_SCAT.append(x_ptrm_check[k])
            y_ptrm_check_for_SCAT.append(y_ptrm_check[k])

    x_ptrm_check_for_SCAT = np.array(x_ptrm_check_for_SCAT)
    y_ptrm_check_for_SCAT = np.array(y_ptrm_check_for_SCAT)

    # --------------------------------------------------------------
    # collect Tail checks in segment to arrays
    # for scat calculation we take only the tail checks which were carried out
    # before reaching the highest temperature in the chosen segment

    x_tail_check_for_SCAT, y_tail_check_for_SCAT = [], []

    for k in range(len(tail_check_temperatures)):
        if tail_check_temperatures[k] >= pars[min_key] and tail_checks_starting_temperatures[k] <= pars[max_key]:
            x_tail_check_for_SCAT.append(x_tail_check[k])
            y_tail_check_for_SCAT.append(y_tail_check[k])

    x_tail_check_for_SCAT = np.array(x_tail_check_for_SCAT)
    y_tail_check_for_SCAT = np.array(y_tail_check_for_SCAT)

    # --------------------------------------------------------------
    # calculate the lines that define the scat box:

    # if threshold value for beta is not defined, then scat cannot be calculated (pass)
    # in this case, scat pass
    if beta_key in list(accept.keys()) and accept[beta_key] != "":
        b_beta_threshold = float(accept[beta_key])
        b = pars[b_key]             # best fit line
        cm_x = np.mean(np.array(x_Arai_segment))  # x center of mass
        cm_y = np.mean(np.array(y_Arai_segment))  # y center of mass
        a = cm_y - b * cm_x

        # lines with slope = slope +/- 2*(specimen_b_beta)

        two_sigma_beta_threshold = 2 * b_beta_threshold
        two_sigma_slope_threshold = abs(two_sigma_beta_threshold * b)

        # a line with a  shallower  slope  (b + 2*beta*b) passing through the center of mass
        # y=a1+b1x
        b1 = b + two_sigma_slope_threshold
        a1 = cm_y - b1 * cm_x

        # bounding line with steeper  slope (b - 2*beta*b) passing through the center of mass
        # y=a2+b2x
        b2 = b - two_sigma_slope_threshold
        a2 = cm_y - b2 * cm_x

        # lower bounding line of the 'beta box'
        # y=intercept1+slop1x
        slop1 = old_div(a1, ((old_div(a2, b2))))
        intercept1 = a1

        # higher bounding line of the 'beta box'
        # y=intercept2+slop2x

        slop2 = old_div(a2, ((old_div(a1, b1))))
        intercept2 = a2

        pars['specimen_scat_bounding_line_high'] = [intercept2, slop2]
        pars['specimen_scat_bounding_line_low'] = [intercept1, slop1]

        # --------------------------------------------------------------
        # check if the Arai data points are in the 'box'

        # the two bounding lines
        ymin = intercept1 + x_Arai_segment * slop1
        ymax = intercept2 + x_Arai_segment * slop2

        # arrays of "True" or "False"
        check_1 = y_Arai_segment > ymax
        check_2 = y_Arai_segment < ymin

        # check if at least one "True"
        if (sum(check_1) + sum(check_2)) > 0:
            pars["fail_arai_beta_box_scatter"] = True

        # --------------------------------------------------------------
        # check if the pTRM checks data points are in the 'box'

        if len(x_ptrm_check_for_SCAT) > 0:

            # the two bounding lines
            ymin = intercept1 + x_ptrm_check_for_SCAT * slop1
            ymax = intercept2 + x_ptrm_check_for_SCAT * slop2

            # arrays of "True" or "False"
            check_1 = y_ptrm_check_for_SCAT > ymax
            check_2 = y_ptrm_check_for_SCAT < ymin

            # check if at least one "True"
            if (sum(check_1) + sum(check_2)) > 0:
                pars["fail_ptrm_beta_box_scatter"] = True

        # --------------------------------------------------------------
        # check if the tail checks data points are in the 'box'

        if len(x_tail_check_for_SCAT) > 0:

            # the two bounding lines
            ymin = intercept1 + x_tail_check_for_SCAT * slop1
            ymax = intercept2 + x_tail_check_for_SCAT * slop2

            # arrays of "True" or "False"
            check_1 = y_tail_check_for_SCAT > ymax
            check_2 = y_tail_check_for_SCAT < ymin

            # check if at least one "True"
            if (sum(check_1) + sum(check_2)) > 0:
                pars["fail_tail_beta_box_scatter"] = True

        # --------------------------------------------------------------
        # check if specimen_scat is PASS or FAIL:

        if pars["fail_tail_beta_box_scatter"] or pars["fail_ptrm_beta_box_scatter"] or pars["fail_arai_beta_box_scatter"]:
            pars[scat_key] = '0'
        else:
            pars[scat_key] = '1'

    return pars, 0


def getkeys(table):
    """
    customize by commenting out unwanted keys
    """
    keys = []
    if table == "ER_expedition":
        pass
    if table == "ER_citations":
        keys.append("er_citation_name")
        keys.append("long_authors")
        keys.append("year")
        keys.append("title")
        keys.append("citation_type")
        keys.append("doi")
        keys.append("journal")
        keys.append("volume")
        keys.append("pages")
        keys.append("book_title")
        keys.append("book_editors")
        keys.append("publisher")
        keys.append("city")
    if table == "ER_locations":
        keys.append("er_location_name")
        keys.append("er_scientist_mail_names")
#        keys.append("er_location_alternatives" )
        keys.append("location_type")
        keys.append("location_begin_lat")
        keys.append("location_begin_lon")
#        keys.append("location_begin_elevation" )
        keys.append("location_end_lat")
        keys.append("location_end_lon")
#        keys.append("location_end_elevation" )
        keys.append("continent_ocean")
        keys.append("country")
        keys.append("region")
        keys.append("plate_block")
        keys.append("terrane")
        keys.append("tectonic_setting")
#        keys.append("er_citation_names")
    if table == "ER_Formations":
        keys.append("er_formation_name")
        keys.append("formation_class")
        keys.append("formation_lithology")
        keys.append("formation_paleo_environment")
        keys.append("formation_thickness")
        keys.append("formation_description")
    if table == "ER_sections":
        keys.append("er_section_name")
        keys.append("er_section_alternatives")
        keys.append("er_expedition_name")
        keys.append("er_location_name")
        keys.append("er_formation_name")
        keys.append("er_member_name")
        keys.append("section_definition")
        keys.append("section_class")
        keys.append("section_lithology")
        keys.append("section_type")
        keys.append("section_n")
        keys.append("section_begin_lat")
        keys.append("section_begin_lon")
        keys.append("section_begin_elevation")
        keys.append("section_begin_height")
        keys.append("section_begin_drill_depth")
        keys.append("section_begin_composite_depth")
        keys.append("section_end_lat")
        keys.append("section_end_lon")
        keys.append("section_end_elevation")
        keys.append("section_end_height")
        keys.append("section_end_drill_depth")
        keys.append("section_end_composite_depth")
        keys.append("section_azimuth")
        keys.append("section_dip")
        keys.append("section_description")
        keys.append("er_scientist_mail_names")
        keys.append("er_citation_names")
    if table == "ER_sites":
        keys.append("er_location_name")
        keys.append("er_site_name")
#        keys.append("er_site_alternatives")
#        keys.append("er_formation_name")
#        keys.append("er_member_name")
#        keys.append("er_section_name")
        keys.append("er_scientist_mail_names")
        keys.append("site_class")
#        keys.append("site_type")
#        keys.append("site_lithology")
#        keys.append("site_height")
#        keys.append("site_drill_depth")
#        keys.append("site_composite_depth")
#        keys.append("site_lithology")
#        keys.append("site_description")
        keys.append("site_lat")
        keys.append("site_lon")
#        keys.append("site_location_precision")
#        keys.append("site_elevation")
    if table == "ER_samples":
        keys.append("er_location_name")
        keys.append("er_site_name")
#       keys.append("er_sample_alternatives")
        keys.append("sample_azimuth")
        keys.append("sample_dip")
        keys.append("sample_bed_dip")
        keys.append("sample_bed_dip_direction")
#       keys.append("sample_cooling_rate")
#       keys.append("sample_type")
#       keys.append("sample_lat")
#       keys.append("sample_lon")
        keys.append("magic_method_codes")
    if table == "ER_ages":
        #       keys.append("er_location_name")
        #       keys.append("er_site_name")
        #       keys.append("er_section_name")
        #       keys.append("er_formation_name")
        #       keys.append("er_member_name")
        #       keys.append("er_site_name")
        #       keys.append("er_sample_name")
        #       keys.append("er_specimen_name")
        #       keys.append("er_fossil_name")
        #       keys.append("er_mineral_name")
        #       keys.append("tiepoint_name")
        keys.append("age")
        keys.append("age_sigma")
        keys.append("age_unit")
        keys.append("age_range_low")
        keys.append("age_range_hi")
        keys.append("timescale_eon")
        keys.append("timescale_era")
        keys.append("timescale_period")
        keys.append("timescale_epoch")
        keys.append("timescale_stage")
        keys.append("biostrat_zone")
        keys.append("conodont_zone")
        keys.append("magnetic_reversal_chron")
        keys.append("astronomical_stage")
#       keys.append("age_description")
#       keys.append("magic_method_codes")
#       keys.append("er_timescale_citation_names")
#       keys.append("er_citation_names")
    if table == "MAGIC_measurements":
        keys.append("er_location_name")
        keys.append("er_site_name")
        keys.append("er_sample_name")
        keys.append("er_specimen_name")
        keys.append("measurement_positions")
        keys.append("treatment_temp")
        keys.append("treatment_ac_field")
        keys.append("treatment_dc_field")
        keys.append("treatment_dc_field_phi")
        keys.append("treatment_dc_field_theta")
        keys.append("magic_experiment_name")
        keys.append("magic_instrument_codes")
        keys.append("measurement_temp")
        keys.append("magic_method_codes")
        keys.append("measurement_inc")
        keys.append("measurement_dec")
        keys.append("measurement_magn_moment")
        keys.append("measurement_csd")
    return keys


def getnames():
    """
    get mail names
    """
    namestring = ""
    addmore = 1
    while addmore:
        scientist = input("Enter  name  - <Return> when done ")
        if scientist != "":
            namestring = namestring + ":" + scientist
        else:
            namestring = namestring[1:]
            addmore = 0
    return namestring


def magic_help(keyhelp):
    """
    returns a help message for a give magic key
    """
    helpme = {}
    helpme["er_location_name"] = "Name for location or drill site"
    helpme["er_location_alternatives"] = "Colon-delimited list of alternative names and abbreviations"
    helpme["location_type"] = "Location type"
    helpme["location_begin_lat"] = "Begin of section or core or outcrop -- latitude"
    helpme["location_begin_lon"] = "Begin of section or core or outcrop -- longitude"
    helpme["location_begin_elevation"] = "Begin of section or core or outcrop -- elevation relative to sealevel"
    helpme["location_end_lat"] = "Ending of section or core -- latitude "
    helpme["location_end_lon"] = "Ending of section or core -- longitude "
    helpme["location_end_elevation"] = "Ending of section or core -- elevation relative to sealevel"
    helpme["location_geoid"] = "Geoid used in determination of latitude and longitude:  WGS84, GEOID03, USGG2003, GEOID99, G99SSS , G99BM, DEFLEC99 "
    helpme["continent_ocean"] = "Name for continent or ocean island region"
    helpme["ocean_sea"] = "Name for location in an ocean or sea"
    helpme["country"] = "Country name"
    helpme["region"] = "Region name"
    helpme["plate_block"] = "Plate or tectonic block name"
    helpme["terrane"] = "Terrane name"
    helpme["tectonic_setting"] = "Tectonic setting"
    helpme["location_description"] = "Detailed description"
    helpme["location_url"] = "Website URL for the location explicitly"
    helpme["er_scientist_mail_names"] = "Colon-delimited list of names for scientists who described location"
    helpme["er_citation_names"] = "Colon-delimited list of citations"
    helpme["er_formation_name"] = "Name for formation"
    helpme["er_formation_alternatives"] = "Colon-delimited list of alternative names and abbreviations"
    helpme["formation_class"] = "General lithology class: igneous, metamorphic or sedimentary"
    helpme["formation_lithology"] = "Lithology: e.g., basalt, sandstone, etc."
    helpme["formation_paleo_enviroment"] = "Depositional environment"
    helpme["formation_thickness"] = "Formation thickness"
    helpme["er_member_name"] = "Name for member"
    helpme["er_member_alternatives"] = "Colon-delimited list of alternative names and abbreviations"
    helpme["er_formation_name"] = "Name for formation"
    helpme["member_class"] = "General lithology type"
    helpme["member_lithology"] = "Lithology"
    helpme["member_paleo_environment"] = "Depositional environment"
    helpme["member_thickness"] = "Member thickness"
    helpme["member_description"] = "Detailed description"
    helpme["er_section_name"] = "Name for section or core"
    helpme["er_section_alternatives"] = "Colon-delimited list of alternative names and abbreviations"
    helpme["er_expedition_name"] = "Name for seagoing or land expedition"
    helpme["er_location_name"] = "Name for location or drill site"
    helpme["er_formation_name"] = "Name for formation"
    helpme["er_member_name"] = "Name for member"
    helpme["section_definition"] = "General definition of section"
    helpme["section_class"] = "General lithology type"
    helpme["section_lithology"] = "Section lithology or archeological classification"
    helpme["section_type"] = "Section type"
    helpme["section_n"] = "Number of subsections included composite (stacked) section"
    helpme["section_begin_lat"] = "Begin of section or core -- latitude"
    helpme["section_begin_lon"] = "Begin of section or core -- longitude"
    helpme["section_begin_elevation"] = "Begin of section or core -- elevation relative to sealevel"
    helpme["section_begin_height"] = "Begin of section or core -- stratigraphic height"
    helpme["section_begin_drill_depth"] = "Begin of section or core -- depth in MBSF as used by ODP"
    helpme["section_begin_composite_depth"] = "Begin of section or core -- composite depth in MBSF as used by ODP"
    helpme["section_end_lat"] = "End of section or core -- latitude "
    helpme["section_end_lon"] = "End of section or core -- longitude "
    helpme["section_end_elevation"] = "End of section or core -- elevation relative to sealevel"
    helpme["section_end_height"] = "End of section or core -- stratigraphic height"
    helpme["section_end_drill_depth"] = "End of section or core -- depth in MBSF as used by ODP"
    helpme["section_end_composite_depth"] = "End of section or core -- composite depth in MBSF as used by ODP"
    helpme["section_azimuth"] = "Section azimuth as measured clockwise from the north"
    helpme["section_dip"] = "Section dip as measured into the outcrop"
    helpme["section_description"] = "Detailed description"
    helpme["er_site_name"] = "Name for site"
    helpme["er_site_alternatives"] = "Colon-delimited list of alternative names and abbreviations"
    helpme["er_expedition_name"] = "Name for seagoing or land expedition"
    helpme["er_location_name"] = "Name for location or drill site"
    helpme["er_section_name"] = "Name for section or core"
    helpme["er_formation_name"] = "Name for formation"
    helpme["er_member_name"] = "Name for member"
    helpme["site_definition"] = "General definition of site"
    helpme["site_class"] = "[A]rchaeologic,[E]xtrusive,[I]ntrusive,[M]etamorphic,[S]edimentary"
    helpme["site_lithology"] = "Site lithology or archeological classification"
    helpme["site_type"] = "Site type: slag, lava flow, sediment layer, etc."
    helpme["site_lat"] = "Site location -- latitude"
    helpme["site_lon"] = "Site location -- longitude"
    helpme["site_location_precision"] = "Site location -- precision in latitude and longitude"
    helpme["site_elevation"] = "Site location -- elevation relative to sealevel"
    helpme["site_height"] = "Site location -- stratigraphic height"
    helpme["site_drill_depth"] = "Site location -- depth in MBSF as used by ODP"
    helpme["site_composite_depth"] = "Site location -- composite depth in MBSF as used by ODP"
    helpme["site_description"] = "Detailed description"
    helpme["magic_method_codes"] = "Colon-delimited list of method codes"
    helpme["er_sample_name"] = "Name for sample"
    helpme["er_sample_alternatives"] = "Colon-delimited list of alternative names and abbreviations"
    helpme["er_expedition_name"] = "Name for seagoing or land expedition"
    helpme["er_location_name"] = "Name for location or drill site"
    helpme["er_section_name"] = "Name for section or core"
    helpme["er_formation_name"] = "Name for formation"
    helpme["er_member_name"] = "Name for member"
    helpme["er_site_name"] = "Name for site"
    helpme["sample_class"] = "General lithology type"
    helpme["sample_lithology"] = "Sample lithology or archeological classification"
    helpme["sample_type"] = "Sample type"
    helpme["sample_texture"] = "Sample texture"
    helpme["sample_alteration"] = "Sample alteration grade"
    helpme["sample_alteration_type"] = "Sample alteration type"
    helpme["sample_lat"] = "Sample location -- latitude"
    helpme["sample_lon"] = "Sample location -- longitude"
    helpme["sample_location_precision"] = "Sample location -- precision in latitude and longitude"
    helpme["sample_elevation"] = "Sample location -- elevation relative to sealevel"
    helpme["sample_height"] = "Sample location -- stratigraphic height"
    helpme["sample_drill_depth"] = "Sample location -- depth in MBSF as used by ODP"
    helpme["sample_composite_depth"] = "Sample location -- composite depth in MBSF as used by ODP"
    helpme["sample_date"] = "Sampling date"
    helpme["sample_time_zone"] = "Sampling time zone"
    helpme["sample_azimuth"] = "Sample azimuth as measured clockwise from the north"
    helpme["sample_dip"] = "Sample dip as measured into the outcrop"
    helpme["sample_bed_dip_direction"] = "Direction of the dip of a paleo-horizontal plane in the bedding"
    helpme["sample_bed_dip"] = "Dip of the bedding as measured to the right of strike direction"
    helpme["sample_cooling_rate"] = "Estimated ancient in-situ cooling rate per Ma"
    helpme["er_specimen_name"] = "Name for specimen"
    helpme["er_specimen_alternatives"] = "Colon-delimited list of alternative names and abbreviations"
    helpme["er_expedition_name"] = "Name for seagoing or land expedition"
    helpme["er_location_name"] = "Name for location or drill site"
    helpme["er_section_name"] = "Name for section or core"
    helpme["er_formation_name"] = "Name for formation"
    helpme["er_member_name"] = "Name for member"
    helpme["er_site_name"] = "Name for site"
    helpme["er_sample_name"] = "Name for sample"
    helpme["specimen_class"] = "General lithology type"
    helpme["specimen_lithology"] = "Specimen lithology or archeological classification"
    helpme["specimen_type"] = "Specimen type"
    helpme["specimen_texture"] = "Specimen texture"
    helpme["specimen_alteration"] = "Specimen alteration grade"
    helpme["specimen_alteration_type"] = "Specimen alteration type"
    helpme["specimen_elevation"] = "Specimen location -- elevation relative to sealevel"
    helpme["specimen_height"] = "Specimen location -- stratigraphic height"
    helpme["specimen_drill_depth"] = "Specimen location -- depth in MBSF as used by ODP"
    helpme["specimen_composite_depth"] = "Specimen location -- composite depth in MBSF as used by ODP"
    helpme["specimen_azimuth"] = "Specimen azimuth as measured clockwise from the north"
    helpme["specimen_dip"] = "Specimen dip as measured into the outcrop"
    helpme["specimen_volume"] = "Specimen volume"
    helpme["specimen_weight"] = "Specimen weight"
    helpme["specimen_density"] = "Specimen density"
    helpme["specimen_size"] = "Specimen grain size fraction"
    helpme["er_expedition_name"] = "Name for seagoing or land expedition"
    helpme["er_location_name"] = "Name for location or drill site"
    helpme["er_formation_name"] = "Name for formation"
    helpme["er_member_name"] = "Name for member"
    helpme["er_site_name"] = "Name for site"
    helpme["er_sample_name"] = "Name for sample"
    helpme["er_specimen_name"] = "Name for specimen"
    helpme["er_fossil_name"] = "Name for fossil"
    helpme["er_mineral_name"] = "Name for mineral"
    helpme["GM-ALPHA"] = "Age determination by using alpha counting"
    helpme["GM-ARAR"] = "40Ar/39Ar age determination"
    helpme["GM-ARAR-AP"] = "40Ar/39Ar age determination: Age plateau"
    helpme["GM-ARAR-II"] = "40Ar/39Ar age determination: Inverse isochron"
    helpme["GM-ARAR-NI"] = "40Ar/39Ar age determination: Normal isochron"
    helpme["GM-ARAR-TF"] = "40Ar/39Ar age determination: Total fusion or recombined age"
    helpme["GM-C14"] = "Radiocarbon age determination"
    helpme["GM-C14-AMS"] = "Radiocarbon age determination: AMS"
    helpme["GM-C14-BETA"] = "Radiocarbon age determination: Beta decay counting"
    helpme["GM-C14-CAL"] = "Radiocarbon age determination: Calibrated"
    helpme["GM-CC"] = "Correlation chronology"
    helpme["GM-CC-ARCH"] = "Correlation chronology: Archeology"
    helpme["GM-CC-ARM"] = "Correlation chronology: ARM"
    helpme["GM-CC-ASTRO"] = "Correlation chronology: Astronomical"
    helpme["GM-CC-CACO3"] = "Correlation chronology: Calcium carbonate"
    helpme["GM-CC-COLOR"] = "Correlation chronology: Color or reflectance"
    helpme["GM-CC-GRAPE"] = "Correlation chronology: Gamma Ray Polarimeter Experiment"
    helpme["GM-CC-IRM"] = "Correlation chronology: IRM"
    helpme["GM-CC-ISO"] = "Correlation chronology: Stable isotopes"
    helpme["GM-CC-REL"] = "Correlation chronology: Relative chronology other than stratigraphic successions"
    helpme["GM-CC-STRAT"] = "Correlation chronology: Stratigraphic succession"
    helpme["GM-CC-TECT"] = "Correlation chronology: Tectites and microtectites"
    helpme["GM-CC-TEPH"] = "Correlation chronology: Tephrochronology"
    helpme["GM-CC-X"] = "Correlation chronology: Susceptibility"
    helpme["GM-CHEM"] = "Chemical chronology"
    helpme["GM-CHEM-AAR"] = "Chemical chronology: Amino acid racemization"
    helpme["GM-CHEM-OH"] = "Chemical chronology: Obsidian hydration"
    helpme["GM-CHEM-SC"] = "Chemical chronology: Stoan coatings CaCO3"
    helpme["GM-CHEM-TH"] = "Chemical chronology: Tephra hydration"
    helpme["GM-COSMO"] = "Cosmogenic age determination"
    helpme["GM-COSMO-AL26"] = "Cosmogenic age determination: 26Al"
    helpme["GM-COSMO-AR39"] = "Cosmogenic age determination: 39Ar"
    helpme["GM-COSMO-BE10"] = "Cosmogenic age determination: 10Be"
    helpme["GM-COSMO-C14"] = "Cosmogenic age determination: 14C"
    helpme["GM-COSMO-CL36"] = "Cosmogenic age determination: 36Cl"
    helpme["GM-COSMO-HE3"] = "Cosmogenic age determination: 3He"
    helpme["GM-COSMO-KR81"] = "Cosmogenic age determination: 81Kr"
    helpme["GM-COSMO-NE21"] = "Cosmogenic age determination: 21Ne"
    helpme["GM-COSMO-NI59"] = "Cosmogenic age determination: 59Ni"
    helpme["GM-COSMO-SI32"] = "Cosmogenic age determination: 32Si"
    helpme["GM-DENDRO"] = "Dendrochronology"
    helpme["GM-ESR"] = "Electron Spin Resonance"
    helpme["GM-FOSSIL"] = "Age determined from fossil record"
    helpme["GM-FT"] = "Fission track age determination"
    helpme["GM-HIST"] = "Historically recorded geological event"
    helpme["GM-INT"] = "Age determination through interpolation between at least two geological units of known age"
    helpme["GM-INT-L"] = "Age determination through interpolation between at least two geological units of known age: Linear"
    helpme["GM-INT-S"] = "Age determination through interpolation between at least two geological units of known age: Cubic spline"
    helpme["GM-ISO"] = "Age determined by isotopic dating, but no further details available"
    helpme["GM-KAR"] = "40K-40Ar age determination"
    helpme["GM-KAR-I"] = "40K-40Ar age determination: Isochron"
    helpme["GM-KAR-MA"] = "40K-40Ar age determination: Model age"
    helpme["GM-KCA"] = "40K-40Ca age determination"
    helpme["GM-KCA-I"] = "40K-40Ca age determination: Isochron"
    helpme["GM-KCA-MA"] = "40K-40Ca age determination: Model age"
    helpme["GM-LABA"] = "138La-138Ba age determination"
    helpme["GM-LABA-I"] = "138La-138Ba age determination: Isochron"
    helpme["GM-LABA-MA"] = "138La-138Ba age determination: Model age"
    helpme["GM-LACE"] = "138La-138Ce age determination"
    helpme["GM-LACE-I"] = "138La-138Ce age determination: Isochron"
    helpme["GM-LACE-MA"] = "138La-138Ce age determination: Model age"
    helpme["GM-LICHE"] = "Lichenometry"
    helpme["GM-LUHF"] = "176Lu-176Hf age determination"
    helpme["GM-LUHF-I"] = "176Lu-176Hf age determination: Isochron"
    helpme["GM-LUHF-MA"] = "176Lu-176Hf age determination: Model age"
    helpme["GM-LUM"] = "Luminescence"
    helpme["GM-LUM-IRS"] = "Luminescence: Infrared stimulated luminescence"
    helpme["GM-LUM-OS"] = "Luminescence: Optically stimulated luminescence"
    helpme["GM-LUM-TH"] = "Luminescence: Thermoluminescence"
    helpme["GM-MOD"] = "Model curve fit to available age dates"
    helpme["GM-MOD-L"] = "Model curve fit to available age dates: Linear"
    helpme["GM-MOD-S"] = "Model curve fit to available age dates: Cubic spline"
    helpme["GM-MORPH"] = "Geomorphic chronology"
    helpme["GM-MORPH-DEF"] = "Geomorphic chronology: Rate of deformation"
    helpme["GM-MORPH-DEP"] = "Geomorphic chronology: Rate of deposition"
    helpme["GM-MORPH-POS"] = "Geomorphic chronology: Geomorphology position"
    helpme["GM-MORPH-WEATH"] = "Geomorphic chronology: Rock and mineral weathering"
    helpme["GM-NO"] = "Unknown geochronology method"
    helpme["GM-O18"] = "Oxygen isotope dating"
    helpme["GM-PBPB"] = "207Pb-206Pb age determination"
    helpme["GM-PBPB-C"] = "207Pb-206Pb age determination: Common Pb"
    helpme["GM-PBPB-I"] = "207Pb-206Pb age determination: Isochron"
    helpme["GM-PLEO"] = "Pleochroic haloes"
    helpme["GM-PMAG-ANOM"] = "Paleomagnetic age determination: Magnetic anomaly identification"
    helpme["GM-PMAG-APWP"] = "Paleomagnetic age determination: Comparing paleomagnetic data to APWP"
    helpme["GM-PMAG-ARCH"] = "Paleomagnetic age determination: Archeomagnetism"
    helpme["GM-PMAG-DIR"] = "Paleomagnetic age determination: Directions"
    helpme["GM-PMAG-POL"] = "Paleomagnetic age determination: Polarities"
    helpme["GM-PMAG-REGSV"] = "Paleomagnetic age determination: Correlation to a regional secular variation curve"
    helpme["GM-PMAG-RPI"] = "Paleomagnetic age determination: Relative paleointensity"
    helpme["GM-PMAG-VEC"] = "Paleomagnetic age determination: Full vector"
    helpme["GM-RATH"] = "226Ra-230Th age determination"
    helpme["GM-RBSR"] = "87Rb-87Sr age determination"
    helpme["GM-RBSR-I"] = "87Rb-87Sr age determination: Isochron"
    helpme["GM-RBSR-MA"] = "87Rb-87Sr age determination: Model age"
    helpme["GM-REOS"] = "187Re-187Os age determination"
    helpme["GM-REOS-I"] = "187Re-187Os age determination: Isochron"
    helpme["GM-REOS-MA"] = "187Re-187Os age determination: Model age"
    helpme["GM-REOS-PT"] = "187Re-187Os age determination: Pt normalization of 186Os"
    helpme["GM-SCLERO"] = "Screlochronology"
    helpme["GM-SHRIMP"] = "SHRIMP age dating"
    helpme["GM-SMND"] = "147Sm-143Nd age determination"
    helpme["GM-SMND-I"] = "147Sm-143Nd age determination: Isochron"
    helpme["GM-SMND-MA"] = "147Sm-143Nd age determination: Model age"
    helpme["GM-THPB"] = "232Th-208Pb age determination"
    helpme["GM-THPB-I"] = "232Th-208Pb age determination: Isochron"
    helpme["GM-THPB-MA"] = "232Th-208Pb age determination: Model age"
    helpme["GM-UPA"] = "235U-231Pa age determination"
    helpme["GM-UPB"] = "U-Pb age determination"
    helpme["GM-UPB-CC-T0"] = "U-Pb age determination: Concordia diagram age, upper intersection"
    helpme["GM-UPB-CC-T1"] = "U-Pb age determination: Concordia diagram age, lower intersection"
    helpme["GM-UPB-I-206"] = "U-Pb age determination: 238U-206Pb isochron"
    helpme["GM-UPB-I-207"] = "U-Pb age determination: 235U-207Pb isochron"
    helpme["GM-UPB-MA-206"] = "U-Pb age determination: 238U-206Pb model age"
    helpme["GM-UPB-MA-207"] = "U-Pb age determination: 235U-207Pb model age"
    helpme["GM-USD"] = "Uranium series disequilibrium age determination"
    helpme["GM-USD-PA231-TH230"] = "Uranium series disequilibrium age determination: 231Pa-230Th"
    helpme["GM-USD-PA231-U235"] = "Uranium series disequilibrium age determination: 231Pa-235U"
    helpme["GM-USD-PB210"] = "Uranium series disequilibrium age determination: 210Pb"
    helpme["GM-USD-RA226-TH230"] = "Uranium series disequilibrium age determination: 226Ra-230Th"
    helpme["GM-USD-RA228-TH232"] = "Uranium series disequilibrium age determination: 228Ra-232Th"
    helpme["GM-USD-TH228-TH232"] = "Uranium series disequilibrium age determination: 228Th-232Th"
    helpme["GM-USD-TH230"] = "Uranium series disequilibrium age determination: 230Th"
    helpme["GM-USD-TH230-TH232"] = "Uranium series disequilibrium age determination: 230Th-232Th"
    helpme["GM-USD-TH230-U234"] = "Uranium series disequilibrium age determination: 230Th-234U"
    helpme["GM-USD-TH230-U238"] = "Uranium series disequilibrium age determination: 230Th-238U"
    helpme["GM-USD-U234-U238"] = "Uranium series disequilibrium age determination: 234U-238U"
    helpme["GM-UTH"] = "238U-230Th age determination"
    helpme["GM-UTHHE"] = "U-Th-He age determination"
    helpme["GM-UTHPB"] = "U-Th-Pb age determination"
    helpme["GM-UTHPB-CC-T0"] = "U-Th-Pb age determination: Concordia diagram intersection age, upper intercept"
    helpme["GM-UTHPB-CC-T1"] = "U-Th-Pb age determination: Concordia diagram intersection age, lower intercept"
    helpme["GM-VARVE"] = "Age determined by varve counting"
    helpme["tiepoint_name"] = "Name for tiepoint horizon"
    helpme["tiepoint_alternatives"] = "Colon-delimited list of alternative names and abbreviations"
    helpme["tiepoint_height"] = "Tiepoint stratigraphic height relative to reference tiepoint"
    helpme["tiepoint_height_sigma"] = "Tiepoint stratigraphic height uncertainty"
    helpme["tiepoint_elevation"] = "Tiepoint elevation relative to sealevel"
    helpme["tiepoint_type"] = "Tiepoint type"
    helpme["age"] = "Age"
    helpme["age_sigma"] = "Age -- uncertainty"
    helpme["age_range_low"] = "Age -- low range"
    helpme["age_range_high"] = "Age -- high range"
    helpme["age_unit"] = "Age -- unit"
    helpme["timescale_eon"] = "Timescale eon"
    helpme["timescale_era"] = "Timescale era"
    helpme["timescale_period"] = "Timescale period"
    helpme["timescale_epoch"] = "Timescale epoch"
    helpme["timescale_stage"] = "Timescale stage"
    helpme["biostrat_zone"] = "Biostratigraphic zone"
    helpme["conodont_zone"] = "Conodont zone"
    helpme["magnetic_reversal_chron"] = "Magnetic reversal chron"
    helpme["astronomical_stage"] = "Astronomical stage name"
    helpme["oxygen_stage"] = "Oxygen stage name"
    helpme["age_culture_name"] = "Age culture name"
    return helpme[keyhelp]


def dosundec(sundata):
    """
    returns the declination for a given set of suncompass data
    Parameters
    __________
      sundata : dictionary with these keys:
          date: time string with the format 'yyyy:mm:dd:hr:min'
          delta_u: time to SUBTRACT from local time for Universal time
          lat: latitude of location (negative for south)
          lon: longitude of location (negative for west)
          shadow_angle: shadow angle of the desired direction with respect to the sun.
    Returns
    ________
       sunaz : the declination of the desired direction wrt true north.
    """
    iday = 0
    timedate = sundata["date"]
    timedate = timedate.split(":")
    year = int(timedate[0])
    mon = int(timedate[1])
    day = int(timedate[2])
    hours = float(timedate[3])
    min = float(timedate[4])
    du = int(sundata["delta_u"])
    hrs = hours - du
    if hrs > 24:
        day += 1
        hrs = hrs - 24
    if hrs < 0:
        day = day - 1
        hrs = hrs + 24
    julian_day = julian(mon, day, year)
    utd = old_div((hrs + old_div(min, 60.)), 24.)
    greenwich_hour_angle, delta = gha(julian_day, utd)
    H = greenwich_hour_angle + float(sundata["lon"])
    if H > 360:
        H = H - 360
    lat = float(sundata["lat"])
    if H > 90 and H < 270:
        lat = -lat
# now do spherical trig to get azimuth to sun
    lat = np.radians(lat)
    delta = np.radians(delta)
    H = np.radians(H)
    ctheta = np.sin(lat) * np.sin(delta) + np.cos(lat) * \
        np.cos(delta) * np.cos(H)
    theta = np.arccos(ctheta)
    beta = np.cos(delta) * np.sin(H) / np.sin(theta)
#
#       check which beta
#
    beta = np.degrees(np.arcsin(beta))
    if delta < lat:
        beta = 180 - beta
    sunaz = 180 - beta
    sunaz = (sunaz + float(sundata["shadow_angle"])) % 360.  # mod 360
    return sunaz


def gha(julian_day, f):
    """
    returns greenwich hour angle
    """
    rad = old_div(np.pi, 180.)
    d = julian_day - 2451545.0 + f
    L = 280.460 + 0.9856474 * d
    g = 357.528 + 0.9856003 * d
    L = L % 360.
    g = g % 360.
# ecliptic longitude
    lamb = L + 1.915 * np.sin(g * rad) + .02 * np.sin(2 * g * rad)
# obliquity of ecliptic
    epsilon = 23.439 - 0.0000004 * d
# right ascension (in same quadrant as lambda)
    t = (np.tan(old_div((epsilon * rad), 2)))**2
    r = old_div(1, rad)
    rl = lamb * rad
    alpha = lamb - r * t * np.sin(2 * rl) + \
        (old_div(r, 2)) * t * t * np.sin(4 * rl)
#       alpha=mod(alpha,360.0)
# declination
    delta = np.sin(epsilon * rad) * np.sin(lamb * rad)
    delta = old_div(np.arcsin(delta), rad)
# equation of time
    eqt = (L - alpha)
#
    utm = f * 24 * 60
    H = old_div(utm, 4) + eqt + 180
    H = H % 360.0
    return H, delta


def julian(mon, day, year):
    """
    returns julian day
    """
    ig = 15 + 31 * (10 + 12 * 1582)
    if year == 0:
        print("Julian no can do")
        return
    if year < 0:
        year = year + 1
    if mon > 2:
        julian_year = year
        julian_month = mon + 1
    else:
        julian_year = year - 1
        julian_month = mon + 13
    j1 = int(365.25 * julian_year)
    j2 = int(30.6001 * julian_month)
    j3 = day + 1720995
    julian_day = j1 + j2 + j3
    if day + 31 * (mon + 12 * year) >= ig:
        jadj = int(0.01 * julian_year)
        julian_day = julian_day + 2 - jadj + int(0.25 * jadj)
    return julian_day


def fillkeys(Recs):
    """
    reconciles keys of dictionaries within Recs.
    """
    keylist, OutRecs = [], []
    for rec in Recs:
        for key in list(rec.keys()):
            if key not in keylist:
                keylist.append(key)
    for rec in Recs:
        for key in keylist:
            if key not in list(rec.keys()):
                rec[key] = ""
        OutRecs.append(rec)
    return OutRecs, keylist


def fisher_mean(data):
    """
    Calculates the Fisher mean and associated parameter from a di_block

    Parameters
    ----------
    di_block : a nested list of [dec,inc] or [dec,inc,intensity]

    Returns
    -------
    fpars : dictionary containing the Fisher mean and statistics
        dec : mean declination
        inc : mean inclination
        r : resultant vector length
        n : number of data points
        k : Fisher k value
        csd : Fisher circular standard deviation
        alpha95 : Fisher circle of 95% confidence
    """
    R, Xbar, X, fpars = 0, [0, 0, 0], [], {}
    N = len(data)
    if N < 2:
        return fpars
    X = dir2cart(data)
    for i in range(len(X)):
        for c in range(3):
            Xbar[c] += X[i][c]
    for c in range(3):
        R += Xbar[c]**2
    R = np.sqrt(R)
    for c in range(3):
        Xbar[c] = Xbar[c]/R
    dir = cart2dir(Xbar)
    fpars["dec"] = dir[0]
    fpars["inc"] = dir[1]
    fpars["n"] = N
    fpars["r"] = R
    if N != R:
        k = (N - 1.) / (N - R)
        fpars["k"] = k
        csd = 81./np.sqrt(k)
    else:
        fpars['k'] = 'inf'
        csd = 0.
    b = 20.**(1./(N - 1.)) - 1
    a = 1 - b * (N - R) / R
    if a < -1:
        a = -1
    a95 = np.degrees(np.arccos(a))
    fpars["alpha95"] = a95
    fpars["csd"] = csd
    if a < 0:
        fpars["alpha95"] = 180.0
    return fpars


def gausspars(data):
    """
    calculates gaussian statistics for data
    """
    N, mean, d = len(data), 0., 0.
    if N < 1:
        return "", ""
    if N == 1:
        return data[0], 0
    for j in range(N):
        mean += old_div(data[j], float(N))
    for j in range(N):
        d += (data[j] - mean)**2
    stdev = np.sqrt(d * (1./(float(N - 1))))
    return mean, stdev


def weighted_mean(data):
    """
    calculates weighted mean of data
    """
    W, N, mean, d = 0, len(data), 0, 0
    if N < 1:
        return "", ""
    if N == 1:
        return data[0][0], 0
    for x in data:
        W += x[1]  # sum of the weights
    for x in data:
        mean += old_div((float(x[1]) * float(x[0])), float(W))
    for x in data:
        d += (old_div(float(x[1]), float(W))) * (float(x[0]) - mean)**2
    stdev = np.sqrt(d * (old_div(1., (float(N - 1)))))
    return mean, stdev


def lnpbykey(data, key0, key1):  # calculate a fisher mean of key1 data for a group of key0
    PmagRec = {}
    if len(data) > 1:
        for rec in data:
            rec['dec'] = float(rec[key1 + '_dec'])
            rec['inc'] = float(rec[key1 + '_inc'])
        fpars = dolnp(data, key1 + '_direction_type')
        PmagRec[key0 + "_dec"] = fpars["dec"]
        PmagRec[key0 + "_inc"] = fpars["inc"]
        PmagRec[key0 + "_n"] = (fpars["n_total"])
        PmagRec[key0 + "_n_lines"] = fpars["n_lines"]
        PmagRec[key0 + "_n_planes"] = fpars["n_planes"]
        PmagRec[key0 + "_r"] = fpars["R"]
        PmagRec[key0 + "_k"] = fpars["K"]
        PmagRec[key0 + "_alpha95"] = fpars["alpha95"]
        if int(PmagRec[key0 + "_n_planes"]) > 0:
            PmagRec["magic_method_codes"] = "DE-FM-LP"
        elif int(PmagRec[key0 + "_n_lines"]) > 2:
            PmagRec["magic_method_codes"] = "DE-FM"
    elif len(data) == 1:
        PmagRec[key0 + "_dec"] = data[0][key1 + '_dec']
        PmagRec[key0 + "_inc"] = data[0][key1 + '_inc']
        PmagRec[key0 + "_n"] = '1'
        if data[0][key1 + '_direction_type'] == 'l':
            PmagRec[key0 + "_n_lines"] = '1'
            PmagRec[key0 + "_n_planes"] = '0'
        if data[0][key1 + '_direction_type'] == 'p':
            PmagRec[key0 + "_n_planes"] = '1'
            PmagRec[key0 + "_n_lines"] = '0'
        PmagRec[key0 + "_alpha95"] = ""
        PmagRec[key0 + "_r"] = ""
        PmagRec[key0 + "_k"] = ""
        PmagRec[key0 + "_direction_type"] = "l"
    return PmagRec


def fisher_by_pol(data):
    """
    input:    as in dolnp (list of dictionaries with 'dec' and 'inc')
    description: do fisher mean after splitting data into two polarity domains.
    output: three dictionaries:
        'A'= polarity 'A'
        'B = polarity 'B'
        'ALL'= switching polarity of 'B' directions, and calculate fisher mean of all data
    code modified from eqarea_ell.py b rshaar 1/23/2014
    """
    FisherByPoles = {}
    DIblock, nameblock, locblock = [], [], []
    for rec in data:
        if 'dec' in list(rec.keys()) and 'inc' in list(rec.keys()):
            # collect data for fisher calculation
            DIblock.append([float(rec["dec"]), float(rec["inc"])])
        else:
            continue
        if 'name' in list(rec.keys()):
            nameblock.append(rec['name'])
        else:
            nameblock.append("")
        if 'loc' in list(rec.keys()):
            locblock.append(rec['loc'])
        else:
            locblock.append("")

    ppars = doprinc(np.array(DIblock))  # get principal directions
    # choose the northerly declination principe component ("normal")
    reference_DI = [ppars['dec'], ppars['inc']]
    # make reference direction in northern hemisphere
    if reference_DI[0] > 90 and reference_DI[0] < 270:
        reference_DI[0] = (reference_DI[0] + 180.) % 360
        reference_DI[1] = reference_DI[1] * -1.
    nDIs, rDIs, all_DI, npars, rpars = [], [], [], [], []
    nlist, rlist, alllist = "", "", ""
    nloclist, rloclist, allloclist = "", "", ""
    for k in range(len(DIblock)):
        if angle([DIblock[k][0], DIblock[k][1]], reference_DI) > 90.:
            rDIs.append(DIblock[k])
            rlist = rlist + ":" + nameblock[k]
            if locblock[k] not in rloclist:
                rloclist = rloclist + ":" + locblock[k]
            all_DI.append([(DIblock[k][0] + 180.) % 360., -1. * DIblock[k][1]])
            alllist = alllist + ":" + nameblock[k]
            if locblock[k] not in allloclist:
                allloclist = allloclist + ":" + locblock[k]
        else:
            nDIs.append(DIblock[k])
            nlist = nlist + ":" + nameblock[k]
            if locblock[k] not in nloclist:
                nloclist = nloclist + ":" + locblock[k]
            all_DI.append(DIblock[k])
            alllist = alllist + ":" + nameblock[k]
            if locblock[k] not in allloclist:
                allloclist = allloclist + ":" + locblock[k]

    for mode in ['A', 'B', 'All']:
        if mode == 'A' and len(nDIs) > 2:
            fpars = fisher_mean(nDIs)
            fpars['sites'] = nlist.strip(':')
            fpars['locs'] = nloclist.strip(':')
            FisherByPoles[mode] = fpars
        elif mode == 'B' and len(rDIs) > 2:
            fpars = fisher_mean(rDIs)
            fpars['sites'] = rlist.strip(':')
            fpars['locs'] = rloclist.strip(':')
            FisherByPoles[mode] = fpars
        elif mode == 'All' and len(all_DI) > 2:
            fpars = fisher_mean(all_DI)
            fpars['sites'] = alllist.strip(':')
            fpars['locs'] = allloclist.strip(':')
            FisherByPoles[mode] = fpars
    return FisherByPoles


def dolnp3_0(Data):
    """
    DEPRECATED!!  USE dolnp()
    Desciption: takes a list of dicts with the controlled vocabulary of 3_0 and calls dolnp on them after reformating for compatibility.
    Parameters
    __________
    Data : nested list of dictionarys with keys
        dir_dec
        dir_inc
        dir_tilt_correction
        method_codes

    Returns
    -------
        ReturnData : dictionary with keys
            dec : fisher mean dec of data in Data
            inc : fisher mean inc of data in Data
            n_lines : number of directed lines [method_code = DE-BFL or DE-FM]
            n_planes : number of best fit planes [method_code = DE-BFP]
            alpha95  : fisher confidence circle from Data
            R : fisher R value of Data
            K : fisher k value of Data
    Effects
        prints to screen in case of no data
    """
    if len(Data) == 0:
        print("This function requires input Data have at least 1 entry")
        return {}
    if len(Data) == 1:
        ReturnData = {}
        ReturnData["dec"] = Data[0]['dir_dec']
        ReturnData["inc"] = Data[0]['dir_inc']
        ReturnData["n_total"] = '1'
        if "DE-BFP" in Data[0]['method_codes']:
            ReturnData["n_lines"] = '0'
            ReturnData["n_planes"] = '1'
        else:
            ReturnData["n_planes"] = '0'
            ReturnData["n_lines"] = '1'
        ReturnData["alpha95"] = ""
        ReturnData["R"] = ""
        ReturnData["K"] = ""
        return ReturnData
    else:
        LnpData = []
        for n, d in enumerate(Data):
            LnpData.append({})
            LnpData[n]['dec'] = d['dir_dec']
            LnpData[n]['inc'] = d['dir_inc']
            LnpData[n]['tilt_correction'] = d['dir_tilt_correction']
            if 'method_codes' in list(d.keys()):
                if "DE-BFP" in d['method_codes']:
                    LnpData[n]['dir_type'] = 'p'
                else:
                    LnpData[n]['dir_type'] = 'l'
        # get a sample average from all specimens
        ReturnData = dolnp(LnpData, 'dir_type')
        return ReturnData


def dolnp(data, direction_type_key):
    """
    Returns fisher mean, a95 for data  using method of Mcfadden and Mcelhinny '88 for lines and planes

    Parameters
    __________
    Data : nested list of dictionaries with keys
        Data model 3.0:
            dir_dec
            dir_inc
            dir_tilt_correction
            method_codes
        Data model 2.5:
            dec
            inc
            tilt_correction
            magic_method_codes
         direction_type_key :  ['specimen_direction_type']
    Returns
    -------
        ReturnData : dictionary with keys
            dec : fisher mean dec of data in Data
            inc : fisher mean inc of data in Data
            n_lines : number of directed lines [method_code = DE-BFL or DE-FM]
            n_planes : number of best fit planes [method_code = DE-BFP]
            alpha95  : fisher confidence circle from Data
            R : fisher R value of Data
            K : fisher k value of Data
    Effects
        prints to screen in case of no data
    """

    if 'dir_dec' in data[0].keys():
        tilt_key = 'dir_tilt_correction'  # this is data model 3.0
    else:
        tilt_key = 'tilt_correction'  # this is data model 3.0
    if tilt_key in list(data[0].keys()):
        tc = str(data[0][tilt_key])
    else:
        tc = '-1'
    dirV = [0, 0, 0]
    fpars = {}

    # sort data  into lines and planes and collect cartesian coordinates
    fdata, n_lines, L, n_planes, E = process_data_for_mean(
        data, direction_type_key)
# set up initial points on the great circles
    V, XV = [], []
    if n_planes != 0:
        if n_lines == 0:
            # set the initial direction arbitrarily
            V = dir2cart([180., -45., 1.])
        else:
            R = np.sqrt(E[0]**2 + E[1]**2 + E[2]**2)
            for c in E:
                # set initial direction as mean of lines
                V.append(old_div(c, R))
        XV = calculate_best_fit_vectors(L, E, V, n_planes)
# calculating overall mean direction and R
        U = E[:]
        for dir in XV:
            for c in range(3):
                U[c] = U[c] + dir[c]
        R = np.sqrt(U[0]**2 + U[1]**2 + U[2]**2)
        for c in range(3):
            U[c] = old_div(U[c], R)
# get dec and inc of solution points on gt circles
        dirV = cart2dir(U)
# calculate modified Fisher stats fo fit
        n_total = n_lines + n_planes
        NP = n_lines + 0.5 * n_planes
        if NP < 1.1:
            NP = 1.1
        if n_total - R != 0:
            K = old_div((NP - 1.), (n_total - R))
            fac = (20.**(old_div(1., (NP - 1.))) - 1.)
            fac = fac * (NP - 1.) / K
            a = 1. - old_div(fac, R)
            a95 = a
            if abs(a) > 1.0:
                a95 = 1.
            if a < 0:
                a95 = -a95
            a95 = np.arccos(a95) * 180. / np.pi
        else:
            a95 = 0.
            K = 'inf'
    else:
        fdir = fisher_mean(fdata)
        n_total, R, K, a95 = fdir["n"], fdir["r"], fdir["k"], fdir["alpha95"]
        dirV[0], dirV[1] = fdir["dec"], fdir["inc"]
    fpars["tilt_correction"] = tc
    fpars["n_total"] = '%i ' % (n_total)
    fpars["n_lines"] = '%i ' % (n_lines)
    fpars["n_planes"] = '%i ' % (n_planes)
    fpars["R"] = '%5.4f ' % (R)
    if K != 'inf':
        fpars["K"] = '%6.0f ' % (K)
    else:
        fpars["K"] = K
    fpars["alpha95"] = '%7.1f ' % (a95)
    fpars["dec"] = '%7.1f ' % (dirV[0])
    fpars["inc"] = '%7.1f ' % (dirV[1])
    return fpars


def vclose(L, V):
    """
    gets the closest vector
    """
    lam, X = 0, []
    for k in range(3):
        lam = lam + V[k] * L[k]
    beta = np.sqrt(1. - lam**2)
    for k in range(3):
        X.append((old_div((V[k] - lam * L[k]), beta)))
    return X


def calculate_best_fit_vectors(L, E, V, n_planes):
    """
    Calculates the best fit vectors for a set of plane interpretations used in fisher mean calculations
    @param: L - a list of the "EL, EM, EN" array of MM88 or the cartisian form of dec and inc of the plane interpretation
    @param: E - the sum of the cartisian coordinates of all the line fits to be used in the mean
    @param: V - inital direction to start iterating from to get plane best fits
    @returns: nested list of n_plane by 3 dimension where the 3 are the cartisian dimension of the best fit vector
    """

    U, XV = E[:], []  # make a copy of E to prevent mutation
    for pole in L:
        XV.append(vclose(pole, V))  # get some points on the great circle
        for c in range(3):
            U[c] = U[c] + XV[-1][c]
# iterate to find best agreement
    angle_tol = 1.
    while angle_tol > 0.1:
        angles = []
        for k in range(n_planes):
            for c in range(3):
                U[c] = U[c] - XV[k][c]
            R = np.sqrt(U[0]**2 + U[1]**2 + U[2]**2)
            for c in range(3):
                V[c] = old_div(U[c], R)
            XX = vclose(L[k], V)
            ang = XX[0] * XV[k][0] + XX[1] * XV[k][1] + XX[2] * XV[k][2]
            angles.append(np.arccos(ang) * 180. / np.pi)
            for c in range(3):
                XV[k][c] = XX[c]
                U[c] = U[c] + XX[c]
            amax = -1
            for ang in angles:
                if ang > amax:
                    amax = ang
            angle_tol = amax

    return XV


def process_data_for_mean(data, direction_type_key):
    """
    takes list of dicts with dec and inc as well as direction_type if possible or method_codes and sorts the data into lines and planes and process it for fisher means

    @param: data - list of dicts with dec inc and some manner of PCA type info
    @param: direction_type_key - key that indicates the direction type variable in the dictionaries of data
    @return: tuple with values - (
                                list of lists with [dec, inc, 1.] for all lines
                                number of line
                                list of lists with [EL,EM,EN] of all planes
                                number of planes
                                list of sum of the cartezian components of all lines
                                )
    """
    dec_key, inc_key, meth_key = 'dec', 'inc', 'magic_method_codes'  # data model 2.5
    if 'dir_dec' in data[0].keys():  # this is data model 3.0
        dec_key, inc_key, meth_key = 'dir_dec', 'dir_inc', 'method_codes'

    n_lines, n_planes = 0, 0
    L, fdata = [], []
    E = [0, 0, 0]

    # sort data  into lines and planes and collect cartesian coordinates
    for rec in data:
        cart = dir2cart([float(rec[dec_key]), float(rec[inc_key])])[0]
        if direction_type_key in list(rec.keys()):
            if rec[direction_type_key] == 'p':  # this is a pole to a plane
                n_planes += 1
                L.append(cart)  # this is the "EL, EM, EN" array of MM88
            else:  # this is a line
                n_lines += 1
                # collect data for fisher calculation
                fdata.append([float(rec[dec_key]), float(rec[inc_key]), 1.])
                E[0] += cart[0]
                E[1] += cart[1]
                E[2] += cart[2]
        elif 'method_codes' in list(rec.keys()):
            if "DE-BFP" in rec[meth_key]:  # this is a pole to a plane
                n_planes += 1
                L.append(cart)  # this is the "EL, EM, EN" array of MM88
            else:  # this is a line
                n_lines += 1
                # collect data for fisher calculation
                fdata.append([rec[dec_key], rec[inc_key], 1.])
                E[0] += cart[0]
                E[1] += cart[1]
                E[2] += cart[2]
        elif meth_key in list(rec.keys()):
            if "DE-BFP" in rec[meth_key]:  # this is a pole to a plane
                n_planes += 1
                L.append(cart)  # this is the "EL, EM, EN" array of MM88
            else:  # this is a line
                n_lines += 1
                # collect data for fisher calculation
                fdata.append([rec[dec_key], rec[inc_key], 1.])
                E[0] += cart[0]
                E[1] += cart[1]
                E[2] += cart[2]
        else:
                # EVERYTHING IS A LINE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            n_lines += 1
            # collect data for fisher calculation
            fdata.append([rec[dec_key], rec[inc_key], 1.])
            E[0] += cart[0]
            E[1] += cart[1]
            E[2] += cart[2]

    return fdata, n_lines, L, n_planes, E


def scoreit(pars, PmagSpecRec, accept, text, verbose):
    """
    gets a grade for a given set of data, spits out stuff
    """
    s = PmagSpecRec["er_specimen_name"]
    PmagSpecRec["measurement_step_min"] = '%8.3e' % (
        pars["measurement_step_min"])
    PmagSpecRec["measurement_step_max"] = '%8.3e' % (
        pars["measurement_step_max"])
    PmagSpecRec["measurement_step_unit"] = pars["measurement_step_unit"]
    PmagSpecRec["specimen_int_n"] = '%i' % (pars["specimen_int_n"])
    PmagSpecRec["specimen_lab_field_dc"] = '%8.3e' % (
        pars["specimen_lab_field_dc"])
    PmagSpecRec["specimen_int"] = '%8.3e ' % (pars["specimen_int"])
    PmagSpecRec["specimen_b"] = '%5.3f ' % (pars["specimen_b"])
    PmagSpecRec["specimen_q"] = '%5.1f ' % (pars["specimen_q"])
    PmagSpecRec["specimen_f"] = '%5.3f ' % (pars["specimen_f"])
    PmagSpecRec["specimen_fvds"] = '%5.3f' % (pars["specimen_fvds"])
    PmagSpecRec["specimen_b_beta"] = '%5.3f' % (pars["specimen_b_beta"])
    PmagSpecRec["specimen_int_mad"] = '%7.1f' % (pars["specimen_int_mad"])
    PmagSpecRec["specimen_dec"] = '%7.1f' % (pars["specimen_dec"])
    PmagSpecRec["specimen_inc"] = '%7.1f' % (pars["specimen_inc"])
    PmagSpecRec["specimen_int_dang"] = '%7.1f ' % (pars["specimen_int_dang"])
    PmagSpecRec["specimen_drats"] = '%7.1f ' % (pars["specimen_drats"])
    PmagSpecRec["specimen_int_ptrm_n"] = '%i ' % (pars["specimen_int_ptrm_n"])
    PmagSpecRec["specimen_rsc"] = '%6.4f ' % (pars["specimen_rsc"])
    PmagSpecRec["specimen_md"] = '%i ' % (int(pars["specimen_md"]))
    PmagSpecRec["specimen_b_sigma"] = '%5.3f ' % (pars["specimen_b_sigma"])
    if 'specimen_scat' in list(pars.keys()):
        PmagSpecRec['specimen_scat'] = pars['specimen_scat']
    if 'specimen_gmax' in list(pars.keys()):
        PmagSpecRec['specimen_gmax'] = '%5.3f' % (pars['specimen_gmax'])
    if 'specimen_frac' in list(pars.keys()):
        PmagSpecRec['specimen_frac'] = '%5.3f' % (pars['specimen_frac'])
    # PmagSpecRec["specimen_Z"]='%7.1f'%(pars["specimen_Z"])
  # check score
    #
    kill = grade(PmagSpecRec, accept, 'specimen_int')
    Grade = ""
    if len(kill) == 0:
        Grade = 'A'
    else:
        Grade = 'F'
    pars["specimen_grade"] = Grade
    if verbose == 0:
        return pars, kill
    diffcum = 0
    if pars['measurement_step_unit'] == 'K':
        outstr = "specimen     Tmin  Tmax  N  lab_field  B_anc  b  q  f(coe)  Fvds  beta  MAD  Dang  Drats  Nptrm  Grade  R  MD%  sigma  Gamma_max \n"
        pars_out = (s, (pars["measurement_step_min"] - 273), (pars["measurement_step_max"] - 273), (pars["specimen_int_n"]), 1e6 * (pars["specimen_lab_field_dc"]), 1e6 * (pars["specimen_int"]), pars["specimen_b"], pars["specimen_q"], pars["specimen_f"], pars["specimen_fvds"],
                    pars["specimen_b_beta"], pars["specimen_int_mad"], pars["specimen_int_dang"], pars["specimen_drats"], pars["specimen_int_ptrm_n"], pars["specimen_grade"], np.sqrt(pars["specimen_rsc"]), int(pars["specimen_md"]), pars["specimen_b_sigma"], pars['specimen_gamma'])
        outstring = '%s %4.0f %4.0f %i %4.1f %4.1f %5.3f %5.1f %5.3f %5.3f %5.3f  %7.1f %7.1f %7.1f %s %s %6.3f %i %5.3f %7.1f' % pars_out + '\n'
    elif pars['measurement_step_unit'] == 'J':
        outstr = "specimen     Wmin  Wmax  N  lab_field  B_anc  b  q  f(coe)  Fvds  beta  MAD  Dang  Drats  Nptrm  Grade  R  MD%  sigma  ThetaMax DeltaMax GammaMax\n"
        pars_out = (s, (pars["measurement_step_min"]), (pars["measurement_step_max"]), (pars["specimen_int_n"]), 1e6 * (pars["specimen_lab_field_dc"]), 1e6 * (pars["specimen_int"]), pars["specimen_b"], pars["specimen_q"], pars["specimen_f"], pars["specimen_fvds"], pars["specimen_b_beta"],
                    pars["specimen_int_mad"], pars["specimen_int_dang"], pars["specimen_drats"], pars["specimen_int_ptrm_n"], pars["specimen_grade"], np.sqrt(pars["specimen_rsc"]), int(pars["specimen_md"]), pars["specimen_b_sigma"], pars["specimen_theta"], pars["specimen_delta"], pars["specimen_gamma"])
        outstring = '%s %4.0f %4.0f %i %4.1f %4.1f %5.3f %5.1f %5.3f %5.3f %5.3f  %7.1f %7.1f %7.1f %s %s %6.3f %i %5.3f %7.1f %7.1f %7.1f' % pars_out + '\n'
    if pars["specimen_grade"] != "A":
        print('\n killed by:')
        for k in kill:
            print(k, ':, criterion set to: ',
                  accept[k], ', specimen value: ', pars[k])
        print('\n')
    print(outstr)
    print(outstring)
    return pars, kill


def b_vdm(B, lat):
    """
    Converts a magnetic field value (input in units of tesla) to a virtual
    dipole moment (VDM) or a virtual axial dipole moment (VADM); output
    in units of Am^2)

    Parameters
    ----------
    B: local magnetic field strength in tesla
    lat: latitude of site in degrees

    Returns
    ----------
    V(A)DM in units of Am^2

    Examples
    --------
    >>> pmag.b_vdm(33e-6,22)*1e-21

    71.58815974511788
    """
    # changed radius of the earth from 3.367e6 3/12/2010
    fact = ((6.371e6)**3) * 1e7
    colat = np.radians(90. - lat)
    return fact * B / (np.sqrt(1 + 3 * (np.cos(colat)**2)))


def vdm_b(vdm, lat):
    """
    Converts a virtual dipole moment (VDM) or a virtual axial dipole moment
    (VADM; input in units of Am^2) to a local magnetic field value (output in
    units of tesla)

    Parameters
    ----------
    vdm : V(A)DM in units of Am^2
    lat: latitude of site in degrees

    Returns
    -------
    B: local magnetic field strength in tesla
    """
    rad = old_div(np.pi, 180.)
    # changed radius of the earth from 3.367e6 3/12/2010
    fact = ((6.371e6)**3) * 1e7
    colat = (90. - lat) * rad
    return vdm * (np.sqrt(1 + 3 * (np.cos(colat)**2))) / fact


def binglookup(w1i, w2i):
    """
    Bingham statistics lookup table.
    """
    K = {'0.06': {'0.02': ['-25.58', '-8.996'], '0.06': ['-9.043', '-9.043'], '0.04': ['-13.14', '-9.019']}, '0.22': {'0.08': ['-6.944', '-2.644'], '0.02': ['-25.63', '-2.712'], '0.20': ['-2.649', '-2.354'], '0.06': ['-9.027', '-2.673'], '0.04': ['-13.17', '-2.695'], '0.14': ['-4.071', '-2.521'], '0.16': ['-3.518', '-2.470'], '0.10': ['-5.658', '-2.609'], '0.12': ['-4.757', '-2.568'], '0.18': ['-3.053', '-2.414'], '0.22': ['-2.289', '-2.289']}, '0.46': {'0.02': ['-25.12', '-0.250'], '0.08': ['-6.215', '0.000'], '0.06': ['-8.371', '-0.090'], '0.04': ['-12.58', '-0.173']}, '0.44': {'0.08': ['-6.305', '-0.186'], '0.02': ['-25.19', '-0.418'], '0.06': ['-8.454', '-0.270'], '0.04': ['-12.66', '-0.347'], '0.10': ['-4.955', '-0.097'], '0.12': ['-3.992', '0.000']}, '0.42': {'0.08': ['-6.388', '-0.374'], '0.02': ['-25.5', '-0.589'], '0.06': ['-8.532', '-0.452'], '0.04': ['-12.73', '-0.523'], '0.14': ['-3.349', '-0.104'], '0.16': ['-2.741', '0.000'], '0.10': ['-5.045', '-0.290'], '0.12': ['-4.089', '-0.200']}, '0.40': {'0.08': ['-6.466', '-0.564'], '0.02': ['-25.31', '-0.762'], '0.20': ['-1.874', '-0.000'], '0.06': ['-8.604', '-0.636'], '0.04': ['-12.80', '-0.702'], '0.14': ['-3.446', '-0.312'], '0.16': ['-2.845', '-0.215'], '0.10': ['-5.126', '-0.486'], '0.12': ['-4.179', '-0.402'], '0.18': ['-2.330', '-0.111']}, '0.08': {'0.02': ['-25.6', '-6.977'], '0.08': ['-7.035', '-7.035'], '0.06': ['-9.065', '-7.020'], '0.04': ['-13.16', '-6.999']}, '0.28': {'0.08': ['-6.827', '-1.828'], '0.28': ['-1.106', '-1.106'], '0.02': ['-25.57', '-1.939'], '0.20': ['-2.441', '-1.458'], '0.26': ['-1.406', '-1.203'], '0.24': ['-1.724', '-1.294'], '0.06': ['-8.928', '-1.871'], '0.04': ['-13.09', '-1.908'], '0.14': ['-3.906', '-1.665'], '0.16': ['-3.338', '-1.601'], '0.10': ['-5.523', '-1.779'], '0.12': ['-4.606', '-1.725'], '0.18': ['-2.859', '-1.532'], '0.22': ['-2.066', '-1.378']}, '0.02': {'0.02': ['-25.55', '-25.55']}, '0.26': {'0.08': ['-6.870', '-2.078'], '0.02': ['-25.59', '-2.175'], '0.20': ['-2.515', '-1.735'], '0.26': ['-1.497', '-1.497'], '0.24': ['-1.809', '-1.582'], '0.06': ['-8.96 6', '-2.117'], '0.04': ['-13.12', '-2.149'], '0.14': ['-3.965', '-1.929'], '0.16': ['-3.403', '-1.869'], '0.10': ['-5.573', '-2.034'], '0.12': ['-4.661', '-1.984'], '0.18': ['-2.928', '-1.805'], '0.22': ['-2.1 46', '-1.661']}, '0.20': {'0.08': ['-6.974', '-2.973'], '0.02': ['-25.64', '-3.025'], '0.20': ['-2.709', '-2.709'], '0.06': ['-9.05', '-2.997'], '0.04': ['-13.18', '-3.014'], '0.14': ['-4.118', '-2.863'], '0.1 6': ['-3.570', '-2.816'], '0.10': ['-5.694', '-2.942'], '0.12': ['-4.799', '-2.905'], '0.18': ['-3.109', '-2.765']}, '0.04': {'0.02': ['-25.56', '-13.09'], '0.04': ['-13.11', '-13.11']}, '0.14': {'0.08': ['-7.  033', '-4.294'], '0.02': ['-25.64', '-4.295'], '0.06': ['-9.087', '-4.301'], '0.04': ['-13.20', '-4.301'], '0.14': ['-4.231', '-4.231'], '0.10': ['-5.773', '-4.279'], '0.12': ['-4.896', '-4.258']}, '0.16': {'0 .08': ['-7.019', '-3.777'], '0.02': ['-25.65', '-3.796'], '0.06': ['-9.081', '-3.790'], '0.04': ['-13.20', '-3.796'], '0.14': ['-4.198', '-3.697'], '0.16': ['-3.659', '-3.659'], '0.10': ['-5.752', '-3.756'], ' 0.12': ['-4.868', '-3.729']}, '0.10': {'0.02': ['-25.62', '-5.760'],
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     '0.08': ['-7.042', '-5.798'], '0.06': ['-9.080', '-5.791'], '0.10': ['-5.797', '-5.797'], '0.04': ['-13.18', '-5.777']}, '0.12': {'0.08': [' -7.041', '-4.941'], '0.02': ['-25.63', '-4.923'], '0.06': ['-9.087', '-4.941'], '0.04': ['-13.19', '-4.934'], '0.10': ['-5.789', '-4.933'], '0.12': ['-4.917', '-4.917']}, '0.18': {'0.08': ['-6.999', '-3.345'], '0.02': ['-25.65', '-3.381'], '0.06': ['-9.068', '-3.363'], '0.04': ['-13.19', '-3.375'], '0.14': ['-4.160', '-3.249'], '0.16': ['-3.616', '-3.207'], '0.10': ['-5.726', '-3.319'], '0.12': ['-4.836', '-3.287'], '0.18': ['-3.160', '-3.160']}, '0.38': {'0.08': ['-6.539', '-0.757'], '0.02': ['-25.37', '-0.940'], '0.20': ['-1.986', '-0.231'], '0.24': ['-1.202', '0.000'], '0.06': ['-8.670', '-0.824'], '0.04': ['-12.86', '-0.885'], '0.14': ['-3.536', '-0.522'], '0.16': ['-2.941', '-0.432'], '0.10': ['-5.207', '-0.684'], '0.12': ['-4.263', '-0.606'], '0.18': ['-2.434', '-0.335'], '0.22': ['-1.579', '-0.120']}, '0.36': {'0.08': ['-6.606', '-9.555'], '0.28': ['-0.642', '0.000'], '0.02': ['-25.42', '-1.123'], '0.20': ['-2.089', '-0.464'], '0.26': ['-0.974', '-0.129'], '0.24': ['-1.322', '-0.249'], '0.06': ['-8.731', '-1.017'], '0.04': ['-12.91', '-1.073'], '0.14': ['-3.620', '-0.736'], '0.16': ['-3.032', '-0.651'], '0.10': ['-5.280', '-0.887'], '0.12': ['-4.342', '-0.814'], '0.18': ['-2.531', '-0.561'], '0.22': ['-1.690', '-0.360']}, '0.34 ': {'0.08': ['-6.668', '-1.159'], '0.28': ['-0.771', '-0.269'], '0.02': ['-25.46', '-1.312'], '0.20': ['-2.186', '-0.701'], '0.26': ['-1.094', '-0.389'], '0.24': ['-1.433', '-0.500'], '0.06': ['-8.788', '-1.21 6'], '0.32': ['-0.152', '0.000'], '0.04': ['-12.96', '-1.267'], '0.30': ['-0.459', '-0.140'], '0.14': ['-3.699', '-0.955'], '0.16': ['-3.116', '-0.876'], '0.10': ['-5.348', '-1.096'], '0.12': ['-4.415', '-1.02 8'], '0.18': ['-2.621', '-0.791'], '0.22': ['-1.794', '-0.604']}, '0.32': {'0.08': ['-6.725', '-1.371'], '0.28': ['-0.891', '-0.541'], '0.02': ['-25.50', '-1.510'], '0.20': ['-2.277', '-0.944'], '0.26': ['-1.2 06', '-0.653'], '0.24': ['-1.537', '-0.756'], '0.06': ['-8.839', '-1.423'], '0.32': ['-0.292', '-0.292'], '0.04': ['-13.01', '-1.470'], '0.30': ['-0.588', '-0.421'], '0.14': ['-3.773', '-1.181'], '0.16': ['-3.  195', '-1.108'], '0.10': ['-5.411', '-1.313'], '0.12': ['-4.484', '-1.250'], '0.18': ['-2.706', '-1.028'], '0.22': ['-1.891', '-0.853']}, '0.30': {'0.08': ['-6.778', '-1.596'], '0.28': ['-1.002', '-0.819'], '0 .02': ['-25.54', '-1.718'], '0.20': ['-2.361', '-1.195'], '0.26': ['-1.309', '-0.923'], '0.24': ['-1.634', '-1.020'], '0.06': ['-8.886', '-1.641'], '0.04': ['-13.05', '-1.682'], '0.30': ['-0.708', '-0.708'], ' 0.14': ['-3.842', '-1.417'], '0.16': ['-3.269', '-1.348'], '0.10': ['-5.469', '-1.540'], '0.12': ['-4.547', '-1.481'], '0.18': ['-2.785', '-1.274'], '0.22': ['-1.981', '-1.110']}, '0.24': {'0.08': ['-6.910', ' -2.349'], '0.02': ['-25.61', '-2.431'], '0.20': ['-2.584', '-2.032'], '0.24': ['-1.888', '-1.888'], '0.06': ['-8.999', '-2.382'], '0.04': ['-23.14', '-2.410'], '0.14': ['-4.021', '-2.212'], '0.16': ['-3.463', '-2.157'], '0.10': ['-5.618', '-2.309'], '0.12': ['-4.711', '-2.263'], '0.18': ['-2.993', '-2.097'], '0.22': ['-2.220', '-1.963']}}
    w1, w2 = 0., 0.
    wstart, incr = 0.01, 0.02
    if w1i < wstart:
        w1 = '%4.2f' % (wstart + old_div(incr, 2.))
    if w2i < wstart:
        w2 = '%4.2f' % (wstart + old_div(incr, 2.))
    wnext = wstart + incr
    while wstart < 0.5:
        if w1i >= wstart and w1i < wnext:
            w1 = '%4.2f' % (wstart + old_div(incr, 2.))
        if w2i >= wstart and w2i < wnext:
            w2 = '%4.2f' % (wstart + old_div(incr, 2.))
        wstart += incr
        wnext += incr
    k1, k2 = float(K[w2][w1][0]), float(K[w2][w1][1])
    return k1, k2


def cdfout(data, file):
    """
    spits out the cdf for data to file
    """
    f = open(file, "w")
    data.sort()
    for j in range(len(data)):
        y = old_div(float(j), float(len(data)))
        out = str(data[j]) + ' ' + str(y) + '\n'
        f.write(out)
    f.close()


def dobingham(di_block):
    """
    Calculates the Bingham mean and associated statistical parameters from
    directions that are input as a di_block

    Parameters
    ----------
    di_block : a nested list of [dec,inc] or [dec,inc,intensity]

    Returns
    -------
    bpars : dictionary containing the Bingham mean and associated statistics
    dictionary keys
        dec : mean declination
        inc : mean inclination
        n : number of datapoints
        Eta : major ellipse
        Edec : declination of major ellipse axis
        Einc : inclination of major ellipse axis
        Zeta : minor ellipse
        Zdec : declination of minor ellipse axis
        Zinc : inclination of minor ellipse axis

    """
    control, X, bpars = [], [], {}
    N = len(di_block)
    if N < 2:
        return bpars
#
#  get cartesian coordinates
#
    for rec in di_block:
        X.append(dir2cart([rec[0], rec[1], 1.]))
#
#   put in T matrix
#
    T = np.array(Tmatrix(X))
    t, V = tauV(T)
    w1, w2, w3 = t[2], t[1], t[0]
    k1, k2 = binglookup(w1, w2)
    PDir = cart2dir(V[0])
    EDir = cart2dir(V[1])
    ZDir = cart2dir(V[2])
    if PDir[1] < 0:
        PDir[0] += 180.
        PDir[1] = -PDir[1]
    PDir[0] = PDir[0] % 360.
    bpars["dec"] = PDir[0]
    bpars["inc"] = PDir[1]
    bpars["Edec"] = EDir[0]
    bpars["Einc"] = EDir[1]
    bpars["Zdec"] = ZDir[0]
    bpars["Zinc"] = ZDir[1]
    bpars["n"] = N
#
#  now for Bingham ellipses.
#
    fac1, fac2 = -2 * N * (k1) * (w3 - w1), -2 * N * (k2) * (w3 - w2)
    sig31, sig32 = np.sqrt(old_div(1., fac1)), np.sqrt(old_div(1., fac2))
    bpars["Zeta"], bpars["Eta"] = 2.45 * sig31 * \
        180. / np.pi, 2.45 * sig32 * 180. / np.pi
    return bpars


def doflip(dec, inc):
    """
    flips lower hemisphere data to upper hemisphere
    """
    if inc < 0:
        inc = -inc
        dec = (dec + 180.) % 360.
    return dec, inc


def doincfish(inc):
    """
    gets fisher mean inc from inc only data
    input: list of inclination values
    output: dictionary of
        'n' : number of inclination values supplied
        'ginc' : gaussian mean of inclinations
        'inc' : estimated Fisher mean
        'r' : estimated Fisher R value
        'k' : estimated Fisher kappa
        'alpha95' : estimated fisher alpha_95
        'csd' : estimated circular standard deviation
    """
    rad, SCOi, SSOi = old_div(np.pi, 180.), 0., 0.  # some definitions
    abinc = []
    for i in inc:
        abinc.append(abs(i))
    MI, std = gausspars(abinc)  # get mean inc and standard deviation
    fpars = {}
    N = len(inc)  # number of data
    fpars['n'] = N
    fpars['ginc'] = MI
    if MI < 30:
        fpars['inc'] = MI
        fpars['k'] = 0
        fpars['alpha95'] = 0
        fpars['csd'] = 0
        fpars['r'] = 0
        print('WARNING: mean inc < 30, returning gaussian mean')
        return fpars
    for i in inc:  # sum over all incs (but take only positive inc)
        coinc = (90. - abs(i)) * rad
        SCOi += np.cos(coinc)
        SSOi += np.sin(coinc)
    Oo = (90.0 - MI) * rad  # first guess at mean
    SCFlag = -1  # sign change flag
    epsilon = float(N) * np.cos(Oo)  # RHS of zero equations
    epsilon += (np.sin(Oo)**2 - np.cos(Oo)**2) * SCOi
    epsilon -= 2. * np.sin(Oo) * np.cos(Oo) * SSOi
    while SCFlag < 0:  # loop until cross zero
        if MI > 0:
            Oo -= (.01 * rad)  # get steeper
        if MI < 0:
            Oo += (.01 * rad)  # get shallower
        prev = epsilon
        epsilon = float(N) * np.cos(Oo)  # RHS of zero equations
        epsilon += (np.sin(Oo)**2. - np.cos(Oo)**2.) * SCOi
        epsilon -= 2. * np.sin(Oo) * np.cos(Oo) * SSOi
        if abs(epsilon) > abs(prev):
            MI = -1 * MI  # reverse direction
        if epsilon * prev < 0:
            SCFlag = 1  # changed sign
    S, C = 0., 0.  # initialize for summation
    for i in inc:
        coinc = (90. - abs(i)) * rad
        S += np.sin(Oo - coinc)
        C += np.cos(Oo - coinc)
    k = old_div((N - 1.), (2. * (N - C)))
    Imle = 90. - (old_div(Oo, rad))
    fpars["inc"] = Imle
    fpars["r"], R = 2. * C - N, 2 * C - N
    fpars["k"] = k
    f = fcalc(2, N - 1)
    a95 = 1. - (0.5) * (old_div(S, C))**2 - (old_div(f, (2. * C * k)))
#    b=20.**(1./(N-1.)) -1.
#    a=1.-b*(N-R)/R
#    a95=np.arccos(a)*180./np.pi
    csd = old_div(81., np.sqrt(k))
    fpars["alpha95"] = a95
    fpars["csd"] = csd
    return fpars


def dokent(data, NN):
    """
    gets Kent  parameters for data
    Parameters
    ___________________
    data :  nested pairs of [Dec,Inc]
    NN  : normalization
        NN is the number of data for Kent ellipse
        NN is 1 for Kent ellipses of bootstrapped mean directions

    Return
    kpars dictionary keys
        dec : mean declination
        inc : mean inclination
        n : number of datapoints
        Eta : major ellipse
        Edec : declination of major ellipse axis
        Einc : inclination of major ellipse axis
        Zeta : minor ellipse
        Zdec : declination of minor ellipse axis
        Zinc : inclination of minor ellipse axis
    """
    X, kpars = [], {}
    N = len(data)
    if N < 2:
        return kpars
#
#  get fisher mean and convert to co-inclination (theta)/dec (phi) in radians
#
    fpars = fisher_mean(data)
    pbar = fpars["dec"] * np.pi / 180.
    tbar = (90. - fpars["inc"]) * np.pi / 180.
#
#   initialize matrices
#
    H = [[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]]
    w = [[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]]
    b = [[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]]
    gam = [[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]]
    xg = []
#
#  set up rotation matrix H
#
    H = [[np.cos(tbar) * np.cos(pbar), -np.sin(pbar), np.sin(tbar) * np.cos(pbar)], [np.cos(tbar)
                                                                                     * np.sin(pbar), np.cos(pbar), np.sin(pbar) * np.sin(tbar)], [-np.sin(tbar), 0., np.cos(tbar)]]
#
#  get cartesian coordinates of data
#
    for rec in data:
        X.append(dir2cart([rec[0], rec[1], 1.]))
#
#   put in T matrix
#
    T = Tmatrix(X)
    for i in range(3):
        for j in range(3):
            T[i][j] = old_div(T[i][j], float(NN))
#
# compute B=H'TH
#
    for i in range(3):
        for j in range(3):
            for k in range(3):
                w[i][j] += T[i][k] * H[k][j]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                b[i][j] += H[k][i] * w[k][j]
#
# choose a rotation w about North pole to diagonalize upper part of B
#
    psi = 0.5 * np.arctan(2. * b[0][1] / (b[0][0] - b[1][1]))
    w = [[np.cos(psi), -np.sin(psi), 0],
         [np.sin(psi), np.cos(psi), 0], [0., 0., 1.]]
    for i in range(3):
        for j in range(3):
            gamtmp = 0.
            for k in range(3):
                gamtmp += H[i][k] * w[k][j]
            gam[i][j] = gamtmp
    for i in range(N):
        xg.append([0., 0., 0.])
        for k in range(3):
            xgtmp = 0.
            for j in range(3):
                xgtmp += gam[j][k] * X[i][j]
            xg[i][k] = xgtmp
# compute asymptotic ellipse parameters
#
    xmu, sigma1, sigma2 = 0., 0., 0.
    for i in range(N):
        xmu += xg[i][2]
        sigma1 = sigma1 + xg[i][0]**2
        sigma2 = sigma2 + xg[i][1]**2
    xmu = old_div(xmu, float(N))
    sigma1 = old_div(sigma1, float(N))
    sigma2 = old_div(sigma2, float(N))
    g = -2.0 * np.log(0.05) / (float(NN) * xmu**2)
    if np.sqrt(sigma1 * g) < 1:
        eta = np.arcsin(np.sqrt(sigma1 * g))
    if np.sqrt(sigma2 * g) < 1:
        zeta = np.arcsin(np.sqrt(sigma2 * g))
    if np.sqrt(sigma1 * g) >= 1.:
        eta = old_div(np.pi, 2.)
    if np.sqrt(sigma2 * g) >= 1.:
        zeta = old_div(np.pi, 2.)
#
#  convert Kent parameters to directions,angles
#
    kpars["dec"] = fpars["dec"]
    kpars["inc"] = fpars["inc"]
    kpars["n"] = NN
    ZDir = cart2dir([gam[0][1], gam[1][1], gam[2][1]])
    EDir = cart2dir([gam[0][0], gam[1][0], gam[2][0]])
    kpars["Zdec"] = ZDir[0]
    kpars["Zinc"] = ZDir[1]
    kpars["Edec"] = EDir[0]
    kpars["Einc"] = EDir[1]
    if kpars["Zinc"] < 0:
        kpars["Zinc"] = -kpars["Zinc"]
        kpars["Zdec"] = (kpars["Zdec"] + 180.) % 360.
    if kpars["Einc"] < 0:
        kpars["Einc"] = -kpars["Einc"]
        kpars["Edec"] = (kpars["Edec"] + 180.) % 360.
    kpars["Zeta"] = zeta * 180. / np.pi
    kpars["Eta"] = eta * 180. / np.pi
    return kpars


def doprinc(data):
    """
    Gets principal components from data in form of a list of [dec,inc] data.

    Parameters
    ----------
    data : nested list of dec, inc directions

    Returns
    -------
    ppars : dictionary with the principal components
        dec : principal directiion declination
        inc : principal direction inclination
        V2dec : intermediate eigenvector declination
        V2inc : intermediate eigenvector inclination
        V3dec : minor eigenvector declination
        V3inc : minor eigenvector inclination
        tau1 : major eigenvalue
        tau2 : intermediate eigenvalue
        tau3 : minor eigenvalue
        N  : number of points
        Edir : elongation direction [dec, inc, length]
    """
    ppars = {}
    rad = old_div(np.pi, 180.)
    X = dir2cart(data)
    # for rec in data:
    #    dir=[]
    #    for c in rec: dir.append(c)
    #    cart= (dir2cart(dir))
    #    X.append(cart)
#   put in T matrix
#
    T = np.array(Tmatrix(X))
#
#   get sorted evals/evects
#
    t, V = tauV(T)
    Pdir = cart2dir(V[0])
    ppars['Edir'] = cart2dir(V[1])  # elongation direction
    dec, inc = doflip(Pdir[0], Pdir[1])
    ppars['dec'] = dec
    ppars['inc'] = inc
    ppars['N'] = len(data)
    ppars['tau1'] = t[0]
    ppars['tau2'] = t[1]
    ppars['tau3'] = t[2]
    Pdir = cart2dir(V[1])
    dec, inc = doflip(Pdir[0], Pdir[1])
    ppars['V2dec'] = dec
    ppars['V2inc'] = inc
    Pdir = cart2dir(V[2])
    dec, inc = doflip(Pdir[0], Pdir[1])
    ppars['V3dec'] = dec
    ppars['V3inc'] = inc
    return ppars


def pt_rot(EP, Lats, Lons):
    """
    Rotates points on a globe by an Euler pole rotation using method of
    Cox and Hart 1986, box 7-3.

    Parameters
    ----------
    EP : Euler pole list [lat,lon,angle]
    Lats : list of latitudes of points to be rotated
    Lons : list of longitudes of points to be rotated

    Returns
    _________
    RLats : rotated latitudes
    RLons : rotated longitudes
    """
# gets user input of Rotation pole lat,long, omega for plate and converts
# to radians
    E = dir2cart([EP[1], EP[0], 1.])  # EP is pole lat,lon omega
    omega = EP[2] * np.pi / 180.  # convert to radians
    RLats, RLons = [], []
    for k in range(len(Lats)):
        if Lats[k] <= 90.:  # peel off delimiters
            # converts to rotation pole to cartesian coordinates
            A = dir2cart([Lons[k], Lats[k], 1.])
# defines cartesian coordinates of the pole A
            R = [[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]]
            R[0][0] = E[0] * E[0] * (1 - np.cos(omega)) + np.cos(omega)
            R[0][1] = E[0] * E[1] * (1 - np.cos(omega)) - E[2] * np.sin(omega)
            R[0][2] = E[0] * E[2] * (1 - np.cos(omega)) + E[1] * np.sin(omega)
            R[1][0] = E[1] * E[0] * (1 - np.cos(omega)) + E[2] * np.sin(omega)
            R[1][1] = E[1] * E[1] * (1 - np.cos(omega)) + np.cos(omega)
            R[1][2] = E[1] * E[2] * (1 - np.cos(omega)) - E[0] * np.sin(omega)
            R[2][0] = E[2] * E[0] * (1 - np.cos(omega)) - E[1] * np.sin(omega)
            R[2][1] = E[2] * E[1] * (1 - np.cos(omega)) + E[0] * np.sin(omega)
            R[2][2] = E[2] * E[2] * (1 - np.cos(omega)) + np.cos(omega)
# sets up rotation matrix
            Ap = [0, 0, 0]
            for i in range(3):
                for j in range(3):
                    Ap[i] += R[i][j] * A[j]
# does the rotation
            Prot = cart2dir(Ap)
            RLats.append(Prot[1])
            RLons.append(Prot[0])
        else:  # preserve delimiters
            RLats.append(Lats[k])
            RLons.append(Lons[k])
    return RLats, RLons


def dread(infile, cols):
    """
     reads in specimen, tr, dec, inc int into data[].  position of
     tr, dec, inc, int determined by cols[]
    """
    data = []
    f = open(infile, "r")
    for line in f.readlines():
        tmp = line.split()
        rec = (tmp[0], float(tmp[cols[0]]), float(tmp[cols[1]]), float(tmp[cols[2]]),
               float(tmp[cols[3]]))
        data.append(rec)
    f.close()
    return data


def fshdev(k):
    """
    Generate a random draw from a Fisher distribution with mean declination
    of 0 and inclination of 90 with a specified kappa.

    Parameters
    ----------
    k : kappa (precision parameter) of the distribution
        k can be a single number or an array of values

    Returns
    ----------
    dec, inc : declination and inclination of random Fisher distribution draw
               if k is an array, dec, inc are returned as arrays, otherwise, single values
    """
    k = np.array(k)
    if len(k.shape) != 0:
        n = k.shape[0]
    else:
        n = 1
    R1 = random.random(size=n)
    R2 = random.random(size=n)
    L = np.exp(-2 * k)
    a = R1 * (1 - L) + L
    fac = np.sqrt(-np.log(a)/(2 * k))
    inc = 90. - np.degrees(2 * np.arcsin(fac))
    dec = np.degrees(2 * np.pi * R2)
    if n == 1:
        return dec[0], inc[0]  # preserve backward compatibility
    else:
        return dec, inc


def lowes(data):
    """
    gets Lowe's power spectrum  from gauss coefficients

    Parameters
    _________
    data : nested list of [[l,m,g,h],...] as from pmag.unpack()

    Returns
    _______
    Ls : list of degrees (l)
    Rs : power at  degree l

    """
    lmax = data[-1][0]
    Ls = list(range(1, lmax+1))
    Rs = []
    recno = 0
    for l in Ls:
        pow = 0
        for m in range(0, l + 1):
            pow += (l + 1) * ((1e-3 * data[recno][2])
                              ** 2 + (1e-3 * data[recno][3])**2)
            recno += 1
        Rs.append(pow)
    return Ls, Rs


def magnetic_lat(inc):
    """
    returns magnetic latitude from inclination
    """
    rad = old_div(np.pi, 180.)
    paleo_lat = old_div(np.arctan(0.5 * np.tan(inc * rad)), rad)
    return paleo_lat


def check_F(AniSpec):
    s = np.zeros((6), 'f')
    s[0] = float(AniSpec["anisotropy_s1"])
    s[1] = float(AniSpec["anisotropy_s2"])
    s[2] = float(AniSpec["anisotropy_s3"])
    s[3] = float(AniSpec["anisotropy_s4"])
    s[4] = float(AniSpec["anisotropy_s5"])
    s[5] = float(AniSpec["anisotropy_s6"])
    chibar = old_div((s[0] + s[1] + s[2]), 3.)
    tau, Vdir = doseigs(s)
    t2sum = 0
    for i in range(3):
        t2sum += tau[i]**2
    if 'anisotropy_sigma' in list(AniSpec.keys()) and 'anisotropy_n' in list(AniSpec.keys()):
        if AniSpec['anisotropy_type'] == 'AMS':
            nf = int(AniSpec["anisotropy_n"]) - 6
        else:
            nf = 3 * int(AniSpec["anisotropy_n"]) - 6
        sigma = float(AniSpec["anisotropy_sigma"])
        F = 0.4 * (t2sum - 3 * chibar**2) / (sigma**2)
        Fcrit = fcalc(5, nf)
        if F > Fcrit:  # anisotropic
            chi = np.array(
                [[s[0], s[3], s[5]], [s[3], s[1], s[4]], [s[5], s[4], s[2]]])
            chi_inv = linalg.inv(chi)
            # trace=chi_inv[0][0]+chi_inv[1][1]+chi_inv[2][2] # don't normalize twice
            # chi_inv=3.*chi_inv/trace
        else:  # isotropic
            # make anisotropy tensor identity tensor
            chi_inv = np.array([[1., 0, 0], [0, 1., 0], [0, 0, 1.]])
            chi = chi_inv
    else:  # no sigma key available - just do the correction
        print('WARNING: NO FTEST ON ANISOTROPY PERFORMED BECAUSE OF MISSING SIGMA - DOING CORRECTION ANYWAY')
        chi = np.array(
            [[s[0], s[3], s[5]], [s[3], s[1], s[4]], [s[5], s[4], s[2]]])
        chi_inv = linalg.inv(chi)
    return chi, chi_inv


def Dir_anis_corr(InDir, AniSpec):
    """
    takes the 6 element 's' vector and the Dec,Inc 'InDir' data,
    performs simple anisotropy correction. returns corrected Dec, Inc
    """
    Dir = np.zeros((3), 'f')
    Dir[0] = InDir[0]
    Dir[1] = InDir[1]
    Dir[2] = 1.
    chi, chi_inv = check_F(AniSpec)
    if chi[0][0] == 1.:
        return Dir  # isotropic
    X = dir2cart(Dir)
    M = np.array(X)
    H = np.dot(M, chi_inv)
    return cart2dir(H)


def doaniscorr(PmagSpecRec, AniSpec):
    """
    takes the 6 element 's' vector and the Dec,Inc, Int 'Dir' data,
    performs simple anisotropy correction. returns corrected Dec, Inc, Int
    """
    AniSpecRec = {}
    for key in list(PmagSpecRec.keys()):
        AniSpecRec[key] = PmagSpecRec[key]
    Dir = np.zeros((3), 'f')
    Dir[0] = float(PmagSpecRec["specimen_dec"])
    Dir[1] = float(PmagSpecRec["specimen_inc"])
    Dir[2] = float(PmagSpecRec["specimen_int"])
# check if F test passes!  if anisotropy_sigma available
    chi, chi_inv = check_F(AniSpec)
    if chi[0][0] == 1.:  # isotropic
        cDir = [Dir[0], Dir[1]]  # no change
        newint = Dir[2]
    else:
        X = dir2cart(Dir)
        M = np.array(X)
        H = np.dot(M, chi_inv)
        cDir = cart2dir(H)
        Hunit = [old_div(H[0], cDir[2]), old_div(H[1], cDir[2]), old_div(
            H[2], cDir[2])]  # unit vector parallel to Banc
        Zunit = [0, 0, -1.]  # unit vector parallel to lab field
        Hpar = np.dot(chi, Hunit)  # unit vector applied along ancient field
        Zpar = np.dot(chi, Zunit)  # unit vector applied along lab field
        # intensity of resultant vector from ancient field
        HparInt = cart2dir(Hpar)[2]
        # intensity of resultant vector from lab field
        ZparInt = cart2dir(Zpar)[2]
        newint = Dir[2] * ZparInt / HparInt
        if cDir[0] - Dir[0] > 90:
            cDir[1] = -cDir[1]
            cDir[0] = (cDir[0] - 180.) % 360.
    AniSpecRec["specimen_dec"] = '%7.1f' % (cDir[0])
    AniSpecRec["specimen_inc"] = '%7.1f' % (cDir[1])
    AniSpecRec["specimen_int"] = '%9.4e' % (newint)
    AniSpecRec["specimen_correction"] = 'c'
    if 'magic_method_codes' in list(AniSpecRec.keys()):
        methcodes = AniSpecRec["magic_method_codes"]
    else:
        methcodes = ""
    if methcodes == "":
        methcodes = "DA-AC-" + AniSpec['anisotropy_type']
    if methcodes != "":
        methcodes = methcodes + ":DA-AC-" + AniSpec['anisotropy_type']
    if chi[0][0] == 1.:  # isotropic
        # indicates anisotropy was checked and no change necessary
        methcodes = methcodes + ':DA-AC-ISO'
    AniSpecRec["magic_method_codes"] = methcodes.strip(":")
    return AniSpecRec


def vfunc(pars_1, pars_2):
    """
    Calculate the Watson Vw test statistic. Calculated as 2*(Sw-Rw)

    Parameters
    ----------
    pars_1 : dictionary of Fisher statistics from population 1
    pars_2 : dictionary of Fisher statistics from population 2

    Returns
    -------
    Vw : Watson's Vw statistic
    """
    cart_1 = dir2cart([pars_1["dec"], pars_1["inc"], pars_1["r"]])
    cart_2 = dir2cart([pars_2['dec'], pars_2['inc'], pars_2["r"]])
    Sw = pars_1['k'] * pars_1['r'] + pars_2['k'] * pars_2['r']  # k1*r1+k2*r2
    xhat_1 = pars_1['k'] * cart_1[0] + pars_2['k'] * cart_2[0]  # k1*x1+k2*x2
    xhat_2 = pars_1['k'] * cart_1[1] + pars_2['k'] * cart_2[1]  # k1*y1+k2*y2
    xhat_3 = pars_1['k'] * cart_1[2] + pars_2['k'] * cart_2[2]  # k1*z1+k2*z2
    Rw = np.sqrt(xhat_1**2 + xhat_2**2 + xhat_3**2)
    return 2 * (Sw - Rw)


def vgp_di(plat, plong, slat, slong):
    """
    Converts a pole position (pole latitude, pole longitude) to a direction
    (declination, inclination) at a given location (slat, slong) assuming a
    dipolar field.

    Parameters
    ----------
    plat : latitude of pole (vgp latitude)
    plong : longitude of pole (vgp longitude)
    slat : latitude of site
    slong : longitude of site

    Returns
    ----------
    dec,inc : tuple of declination and inclination
    """
    plong = plong % 360
    slong = slong % 360
    signdec = 1.
    delphi = abs(plong - slong)
    if delphi != 0:
        signdec = (plong - slong) / delphi
    if slat == 90.:
        slat = 89.99
    thetaS = np.radians(90. - slat)
    thetaP = np.radians(90. - plat)
    delphi = np.radians(delphi)
    cosp = np.cos(thetaS) * np.cos(thetaP) + np.sin(thetaS) * \
        np.sin(thetaP) * np.cos(delphi)
    thetaM = np.arccos(cosp)
    cosd = old_div((np.cos(thetaP) - np.cos(thetaM) *
                    np.cos(thetaS)), (np.sin(thetaM) * np.sin(thetaS)))
    C = abs(1. - cosd**2)
    if C != 0:
        dec = -np.arctan(cosd/np.sqrt(abs(C))) + (np.pi/2.)
    else:
        dec = np.arccos(cosd)
    if -np.pi < signdec * delphi and signdec < 0:
        dec = 2. * np.pi - dec  # checking quadrant
    if signdec * delphi > np.pi:
        dec = 2. * np.pi - dec
    dec = np.degrees(dec) % 360.
    inc = np.degrees(np.arctan2(2. * np.cos(thetaM), np.sin(thetaM)))
    return dec, inc


def watsonsV(Dir1, Dir2):
    """
    calculates Watson's V statistic for two sets of directions
    """
    counter, NumSims = 0, 500
#
# first calculate the fisher means and cartesian coordinates of each set of Directions
#
    pars_1 = fisher_mean(Dir1)
    pars_2 = fisher_mean(Dir2)
#
# get V statistic for these
#
    V = vfunc(pars_1, pars_2)
#
# do monte carlo simulation of datasets with same kappas, but common mean
#
    Vp = []  # set of Vs from simulations
    print("Doing ", NumSims, " simulations")
    for k in range(NumSims):
        counter += 1
        if counter == 50:
            print(k + 1)
            counter = 0
        Dirp = []
# get a set of N1 fisher distributed vectors with k1, calculate fisher stats
        for i in range(pars_1["n"]):
            Dirp.append(fshdev(pars_1["k"]))
        pars_p1 = fisher_mean(Dirp)
# get a set of N2 fisher distributed vectors with k2, calculate fisher stats
        Dirp = []
        for i in range(pars_2["n"]):
            Dirp.append(fshdev(pars_2["k"]))
        pars_p2 = fisher_mean(Dirp)
# get the V for these
        Vk = vfunc(pars_p1, pars_p2)
        Vp.append(Vk)
#
# sort the Vs, get Vcrit (95th one)
#
    Vp.sort()
    k = int(.95 * NumSims)
    return V, Vp[k]


def dimap(D, I):
    """
    Function to map directions  to x,y pairs in equal area projection

    Parameters
    ----------
    D : list or array of declinations (as float)
    I : list or array or inclinations (as float)

    Returns
    -------
    XY : x, y values of directions for equal area projection [x,y]
    """
    try:
        D = float(D)
        I = float(I)
    except TypeError:  # is an array
        return dimap_V(D, I)
# DEFINE FUNCTION VARIABLES
    # initialize equal area projection x,y
    XY = [0., 0.]

# GET CARTESIAN COMPONENTS OF INPUT DIRECTION
    X = dir2cart([D, I, 1.])

# CHECK IF Z = 1 AND ABORT
    if X[2] == 1.0:
        return XY                       # return [0,0]

# TAKE THE ABSOLUTE VALUE OF Z
    if X[2] < 0:
        # this only works on lower hemisphere projections
        X[2] = -X[2]

# CALCULATE THE X,Y COORDINATES FOR THE EQUAL AREA PROJECTION
    # from Collinson 1983
    R = old_div(np.sqrt(1. - X[2]), (np.sqrt(X[0]**2 + X[1]**2)))
    XY[1], XY[0] = X[0] * R, X[1] * R

# RETURN XY[X,Y]
    return XY


def dimap_V(D, I):
    """
    FUNCTION TO MAP DECLINATION, INCLINATIONS INTO EQUAL AREA PROJECTION, X,Y

    Usage:     dimap_V(D, I)
        D and I are both numpy arrays

    """
# GET CARTESIAN COMPONENTS OF INPUT DIRECTION
    DI = np.array([D, I]).transpose()
    X = dir2cart(DI).transpose()
# CALCULATE THE X,Y COORDINATES FOR THE EQUAL AREA PROJECTION
    # from Collinson 1983
    R = np.sqrt(1. - abs(X[2]))/(np.sqrt(X[0]**2 + X[1]**2))
    XY = np.array([X[1] * R, X[0] * R]).transpose()

# RETURN XY[X,Y]
    return XY


def getmeths(method_type):
    """
    returns MagIC  method codes available for a given type
    """
    meths = []
    if method_type == 'GM':
        meths.append('GM-PMAG-APWP')
        meths.append('GM-ARAR')
        meths.append('GM-ARAR-AP')
        meths.append('GM-ARAR-II')
        meths.append('GM-ARAR-NI')
        meths.append('GM-ARAR-TF')
        meths.append('GM-CC-ARCH')
        meths.append('GM-CC-ARCHMAG')
        meths.append('GM-C14')
        meths.append('GM-FOSSIL')
        meths.append('GM-FT')
        meths.append('GM-INT-L')
        meths.append('GM-INT-S')
        meths.append('GM-ISO')
        meths.append('GM-KAR')
        meths.append('GM-PMAG-ANOM')
        meths.append('GM-PMAG-POL')
        meths.append('GM-PBPB')
        meths.append('GM-RATH')
        meths.append('GM-RBSR')
        meths.append('GM-RBSR-I')
        meths.append('GM-RBSR-MA')
        meths.append('GM-SMND')
        meths.append('GM-SMND-I')
        meths.append('GM-SMND-MA')
        meths.append('GM-CC-STRAT')
        meths.append('GM-LUM-TH')
        meths.append('GM-UPA')
        meths.append('GM-UPB')
        meths.append('GM-UTH')
        meths.append('GM-UTHHE')
    else:
        pass
    return meths


def first_up(ofile, Rec, file_type):
    """
    writes the header for a MagIC template file
    """
    keylist = []
    pmag_out = open(ofile, 'a')
    outstring = "tab \t" + file_type + "\n"
    pmag_out.write(outstring)
    keystring = ""
    for key in list(Rec.keys()):
        keystring = keystring + '\t' + key
        keylist.append(key)
    keystring = keystring + '\n'
    pmag_out.write(keystring[1:])
    pmag_out.close()
    return keylist


# returns dictionary with average intensities from list of arbitrary
# dictinaries.
def average_int(data, keybase, outkey):
    Ints, DataRec = [], {}
    for r in data:
        Ints.append(float(r[keybase + '_int']))
    if len(Ints) > 1:
        b, sig = gausspars(Ints)
        sigperc = 100. * sig / b
        DataRec[outkey + "_int_sigma"] = '%8.3e ' % (sig)
        DataRec[outkey + "_int_sigma_perc"] = '%5.1f ' % (sigperc)
    else:  # if only one, just copy over specimen data
        b = Ints[0]
        DataRec[outkey + "_int_sigma"] = ''
        DataRec[outkey + "_int_sigma_perc"] = ''
    DataRec[outkey + "_int"] = '%8.3e ' % (b)
    DataRec[outkey + "_int_n"] = '%i ' % (len(data))
    return DataRec


def get_age(Rec, sitekey, keybase, Ages, DefaultAge):
    """
    finds the age record for a given site
    """
    site = Rec[sitekey]
    gotone = 0
    if len(Ages) > 0:
        for agerec in Ages:
            if agerec["er_site_name"] == site:
                if "age" in list(agerec.keys()) and agerec["age"] != "":
                    Rec[keybase + "age"] = agerec["age"]
                    gotone = 1
                if "age_unit" in list(agerec.keys()):
                    Rec[keybase + "age_unit"] = agerec["age_unit"]
                if "age_sigma" in list(agerec.keys()):
                    Rec[keybase + "age_sigma"] = agerec["age_sigma"]
    if gotone == 0 and len(DefaultAge) > 1:
        sigma = 0.5 * (float(DefaultAge[1]) - float(DefaultAge[0]))
        age = float(DefaultAge[0]) + sigma
        Rec[keybase + "age"] = '%10.4e' % (age)
        Rec[keybase + "age_sigma"] = '%10.4e' % (sigma)
        Rec[keybase + "age_unit"] = DefaultAge[2]
    return Rec
#


def adjust_ages(AgesIn):
    """
    Function to adjust ages to a common age_unit
    """
# get a list of age_units first
    age_units, AgesOut, factors, factor, maxunit, age_unit = [], [], [], 1, 1, "Ma"
    for agerec in AgesIn:
        if agerec[1] not in age_units:
            age_units.append(agerec[1])
            if agerec[1] == "Ga":
                factors.append(1e9)
                maxunit, age_unit, factor = 1e9, "Ga", 1e9
            if agerec[1] == "Ma":
                if maxunit == 1:
                    maxunit, age_unt, factor = 1e6, "Ma", 1e6
                factors.append(1e6)
            if agerec[1] == "Ka":
                factors.append(1e3)
                if maxunit == 1:
                    maxunit, age_unit, factor = 1e3, "Ka", 1e3
            if "Years" in agerec[1].split():
                factors.append(1)
    if len(age_units) == 1:  # all ages are of same type
        for agerec in AgesIn:
            AgesOut.append(agerec[0])
    elif len(age_units) > 1:
        for agerec in AgesIn:  # normalize all to largest age unit
            if agerec[1] == "Ga":
                AgesOut.append(agerec[0] * 1e9 / factor)
            if agerec[1] == "Ma":
                AgesOut.append(agerec[0] * 1e6 / factor)
            if agerec[1] == "Ka":
                AgesOut.append(agerec[0] * 1e3 / factor)
            if "Years" in agerec[1].split():
                if agerec[1] == "Years BP":
                    AgesOut.append(old_div(agerec[0], factor))
                if agerec[1] == "Years Cal BP":
                    AgesOut.append(old_div(agerec[0], factor))
                if agerec[1] == "Years AD (+/-)":
                    # convert to years BP first
                    AgesOut.append(old_div((1950 - agerec[0]), factor))
                if agerec[1] == "Years Cal AD (+/-)":
                    AgesOut.append(old_div((1950 - agerec[0]), factor))
    return AgesOut, age_unit
#


def gaussdev(mean, sigma, N=1):
    """
    returns a number randomly drawn from a gaussian distribution with the given mean, sigma
    Parmeters:
    _____________________________
    mean : mean of the gaussian distribution from which to draw deviates
    sigma : standard deviation of same
    N : number of deviates desired

    Returns
    -------

    N deviates from the normal distribution from
.
    """
    return random.normal(mean, sigma, N)  # return gaussian deviate
#


def get_unf(N=100):
    """
    Generates N uniformly distributed directions
    using the way described in Fisher et al. (1987).
    Parameters
    __________
    N : number of directions, default is 100

    Returns
    ______
    array of nested dec,inc pairs
    """
#
# get uniform directions  [dec,inc]
    z = random.uniform(-1., 1., size=N)
    t = random.uniform(0., 360., size=N)  # decs
    i = np.arcsin(z) * 180. / np.pi  # incs
    return np.array([t, i]).transpose()

# def get_unf(N): #Jeff's way
    """
     subroutine to retrieve N uniformly distributed directions
    """
#    nmax,k=5550,66   # initialize stuff for uniform distribution
#    di,xn,yn,zn=[],[],[],[]
##
# get uniform direcctions (x,y,z)
#    for  i in range(1,k):
#        m = int(2*float(k)*np.sin(np.pi*float(i)/float(k)))
#        for j in range(m):
#            x=np.sin(np.pi*float(i)/float(k))*np.cos(2.*np.pi*float(j)/float(m))
#            y=np.sin(np.pi*float(i)/float(k))*np.sin(2.*np.pi*float(j)/float(m))
#            z=np.cos(np.pi*float(i)/float(k))
#            r=np.sqrt(x**2+y**2+z**2)
#            xn.append(x/r)
#            yn.append(y/r)
#            zn.append(z/r)
##
# select N random phi/theta from unf dist.
#
#    while len(di)<N:
#        ind=random.randint(0,len(xn)-1)
#        dir=cart2dir((xn[ind],yn[ind],zn[ind]))
#        di.append([dir[0],dir[1]])
#    return di
##


def s2a(s):
    """
     convert 6 element "s" list to 3,3 a matrix (see Tauxe 1998)
    """
    a = np.zeros((3, 3,), 'f')  # make the a matrix
    for i in range(3):
        a[i][i] = s[i]
    a[0][1], a[1][0] = s[3], s[3]
    a[1][2], a[2][1] = s[4], s[4]
    a[0][2], a[2][0] = s[5], s[5]
    return a
#


def a2s(a):
    """
     convert 3,3 a matrix to 6 element "s" list  (see Tauxe 1998)
    """
    s = np.zeros((6,), 'f')  # make the a matrix
    for i in range(3):
        s[i] = a[i][i]
    s[3] = a[0][1]
    s[4] = a[1][2]
    s[5] = a[0][2]
    return s


def doseigs(s):
    """
    convert s format for eigenvalues and eigenvectors

    Parameters
    __________
    s=[x11,x22,x33,x12,x23,x13] : the six tensor elements

    Return
    __________
        tau : [t1,t2,t3]
           tau is an list of eigenvalues in decreasing order:
        V : [[V1_dec,V1_inc],[V2_dec,V2_inc],[V3_dec,V3_inc]]
            is an list of the eigenvector directions
    """
#
    A = s2a(s)  # convert s to a (see Tauxe 1998)
    tau, V = tauV(A)  # convert to eigenvalues (t), eigenvectors (V)
    Vdirs = []
    for v in V:  # convert from cartesian to direction
        Vdir = cart2dir(v)
        if Vdir[1] < 0:
            Vdir[1] = -Vdir[1]
            Vdir[0] = (Vdir[0] + 180.) % 360.
        Vdirs.append([Vdir[0], Vdir[1]])
    return tau, Vdirs
#
#


def doeigs_s(tau, Vdirs):
    """
     get elements of s from eigenvaulues - note that this is very unstable
     Input:
         tau,V:
           tau is an list of eigenvalues in decreasing order:
              [t1,t2,t3]
           V is an list of the eigenvector directions
              [[V1_dec,V1_inc],[V2_dec,V2_inc],[V3_dec,V3_inc]]
    Output:
        The six tensor elements as a list:
          s=[x11,x22,x33,x12,x23,x13]

    """
    t = np.zeros((3, 3,), 'f')  # initialize the tau diagonal matrix
    V = []
    for j in range(3):
        t[j][j] = tau[j]  # diagonalize tau
    for k in range(3):
        V.append(dir2cart([Vdirs[k][0], Vdirs[k][1], 1.0]))
    V = np.transpose(V)
    tmp = np.dot(V, t)
    chi = np.dot(tmp, np.transpose(V))
    return a2s(chi)

#
#


def fcalc(col, row):
    """
  looks up an F-test stastic from F tables F(col,row), where row is number of degrees of freedom - this is 95% confidence (p=0.05).

    Parameters
    _________
        col : degrees of freedom column
        row : degrees of freedom row

    Returns
        F : value for 95% confidence from the F-table
    """
#
    if row > 200:
        row = 200
    if col > 20:
        col = 20
    ftest = np.array([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
                      [1, 161.469, 199.493, 215.737, 224.5, 230.066, 234.001, 236.772, 238.949, 240.496, 241.838,
                       242.968, 243.88, 244.798, 245.26, 245.956, 246.422, 246.89, 247.36, 247.596, 248.068],
                      [2, 18.5128, 18.9995, 19.1642, 19.2467, 19.2969, 19.3299, 19.3536, 19.371, 19.3852, 19.3963,
                       19.4043, 19.4122, 19.4186, 19.425, 19.4297, 19.4329, 19.4377, 19.4409, 19.4425, 19.4457],
                      [3, 10.1278, 9.5522, 9.2767, 9.1173, 9.0133, 8.9408, 8.8868, 8.8452, 8.8124, 8.7857,
                       8.7635, 8.7446, 8.7287, 8.715, 8.7028, 8.6923, 8.683, 8.6745, 8.667, 8.6602],
                      [4, 7.7087, 6.9444, 6.5915, 6.3882, 6.2561, 6.1631, 6.0943, 6.0411, 5.9988, 5.9644,
                       5.9359, 5.9117, 5.8912, 5.8733, 5.8578, 5.844, 5.8319, 5.8211, 5.8113, 5.8025],
                      [5, 6.608, 5.7861, 5.4095, 5.1922, 5.0503, 4.9503, 4.8759, 4.8184, 4.7725, 4.735,
                       4.7039, 4.6777, 4.6552, 4.6358, 4.6187, 4.6038, 4.5904, 4.5785, 4.5679, 4.5581],
                      [6, 5.9874, 5.1433, 4.757, 4.5337, 4.3874, 4.2838, 4.2067, 4.1468, 4.099, 4.06,
                       4.0275, 3.9999, 3.9764, 3.956, 3.9381, 3.9223, 3.9083, 3.8957, 3.8844, 3.8742],
                      [7, 5.5914, 4.7374, 4.3469, 4.1204, 3.9715, 3.866, 3.787, 3.7257, 3.6767, 3.6366,
                       3.603, 3.5747, 3.5504, 3.5292, 3.5107, 3.4944, 3.4799, 3.4669, 3.4552, 3.4445],
                      [8, 5.3177, 4.459, 4.0662, 3.8378, 3.6875, 3.5806, 3.5004, 3.4381, 3.3881, 3.3472,
                       3.313, 3.2839, 3.259, 3.2374, 3.2184, 3.2017, 3.1867, 3.1733, 3.1613, 3.1503],
                      [9, 5.1174, 4.2565, 3.8626, 3.6331, 3.4817, 3.3738, 3.2928, 3.2296, 3.1789, 3.1373,
                       3.1025, 3.0729, 3.0475, 3.0255, 3.0061, 2.989, 2.9737, 2.96, 2.9476, 2.9365],
                      [10, 4.9647, 4.1028, 3.7083, 3.4781, 3.3258, 3.2171, 3.1355, 3.0717, 3.0204, 2.9782,
                       2.9429, 2.913, 2.8872, 2.8648, 2.845, 2.8276, 2.812, 2.7981, 2.7855, 2.774],
                      [11, 4.8443, 3.9823, 3.5875, 3.3567, 3.2039, 3.0946, 3.0123, 2.948, 2.8962, 2.8536,
                       2.8179, 2.7876, 2.7614, 2.7386, 2.7186, 2.7009, 2.6851, 2.6709, 2.6581, 2.6464],
                      [12, 4.7472, 3.8853, 3.4903, 3.2592, 3.1059, 2.9961, 2.9134, 2.8486, 2.7964, 2.7534,
                       2.7173, 2.6866, 2.6602, 2.6371, 2.6169, 2.5989, 2.5828, 2.5684, 2.5554, 2.5436],
                      [13, 4.6672, 3.8055, 3.4106, 3.1791, 3.0255, 2.9153, 2.8321, 2.7669, 2.7144, 2.6711,
                       2.6347, 2.6037, 2.5769, 2.5536, 2.5331, 2.5149, 2.4987, 2.4841, 2.4709, 2.4589],
                      [14, 4.6001, 3.7389, 3.3439, 3.1122, 2.9582, 2.8477, 2.7642, 2.6987, 2.6458, 2.6021,
                       2.5655, 2.5343, 2.5073, 2.4837, 2.463, 2.4446, 2.4282, 2.4134, 2.4, 2.3879],
                      [15, 4.543, 3.6824, 3.2874, 3.0555, 2.9013, 2.7905, 2.7066, 2.6408, 2.5877, 2.5437,
                       2.5068, 2.4753, 2.4481, 2.4244, 2.4034, 2.3849, 2.3683, 2.3533, 2.3398, 2.3275],
                      [16, 4.494, 3.6337, 3.2389, 3.0069, 2.8524, 2.7413, 2.6572, 2.5911, 2.5377, 2.4935,
                       2.4564, 2.4247, 2.3973, 2.3733, 2.3522, 2.3335, 2.3167, 2.3016, 2.288, 2.2756],
                      [17, 4.4513, 3.5916, 3.1968, 2.9647, 2.81, 2.6987, 2.6143, 2.548, 2.4943, 2.4499,
                       2.4126, 2.3807, 2.3531, 2.329, 2.3077, 2.2888, 2.2719, 2.2567, 2.2429, 2.2303],
                      [18, 4.4139, 3.5546, 3.1599, 2.9278, 2.7729, 2.6613, 2.5767, 2.5102, 2.4563, 2.4117,
                       2.3742, 2.3421, 2.3143, 2.29, 2.2686, 2.2496, 2.2325, 2.2172, 2.2033, 2.1906],
                      [19, 4.3808, 3.5219, 3.1274, 2.8951, 2.7401, 2.6283, 2.5435, 2.4768, 2.4227, 2.378,
                       2.3402, 2.308, 2.28, 2.2556, 2.2341, 2.2149, 2.1977, 2.1823, 2.1683, 2.1555],
                      [20, 4.3512, 3.4928, 3.0984, 2.8661, 2.7109, 2.599, 2.514, 2.4471, 2.3928, 2.3479,
                       2.31, 2.2776, 2.2495, 2.2249, 2.2033, 2.184, 2.1667, 2.1511, 2.137, 2.1242],
                      [21, 4.3248, 3.4668, 3.0725, 2.8401, 2.6848, 2.5727, 2.4876, 2.4205, 2.3661, 2.3209,
                       2.2829, 2.2504, 2.2222, 2.1975, 2.1757, 2.1563, 2.1389, 2.1232, 2.109, 2.096],
                      [22, 4.3009, 3.4434, 3.0492, 2.8167, 2.6613, 2.5491, 2.4638, 2.3965, 2.3419, 2.2967,
                       2.2585, 2.2258, 2.1975, 2.1727, 2.1508, 2.1313, 2.1138, 2.098, 2.0837, 2.0707],
                      [23, 4.2794, 3.4221, 3.028, 2.7955, 2.64, 2.5276, 2.4422, 2.3748, 2.3201, 2.2747,
                       2.2364, 2.2036, 2.1752, 2.1503, 2.1282, 2.1086, 2.091, 2.0751, 2.0608, 2.0476],
                      [24, 4.2597, 3.4029, 3.0088, 2.7763, 2.6206, 2.5082, 2.4226, 2.3551, 2.3003, 2.2547,
                       2.2163, 2.1834, 2.1548, 2.1298, 2.1077, 2.088, 2.0703, 2.0543, 2.0399, 2.0267],
                      [25, 4.2417, 3.3852, 2.9913, 2.7587, 2.603, 2.4904, 2.4047, 2.3371, 2.2821, 2.2365,
                       2.1979, 2.1649, 2.1362, 2.1111, 2.0889, 2.0691, 2.0513, 2.0353, 2.0207, 2.0075],
                      [26, 4.2252, 3.369, 2.9752, 2.7426, 2.5868, 2.4741, 2.3883, 2.3205, 2.2655, 2.2197,
                       2.1811, 2.1479, 2.1192, 2.094, 2.0716, 2.0518, 2.0339, 2.0178, 2.0032, 1.9898],
                      [27, 4.21, 3.3542, 2.9603, 2.7277, 2.5719, 2.4591, 2.3732, 2.3053, 2.2501, 2.2043,
                       2.1656, 2.1323, 2.1035, 2.0782, 2.0558, 2.0358, 2.0179, 2.0017, 1.987, 1.9736],
                      [28, 4.196, 3.3404, 2.9467, 2.7141, 2.5581, 2.4453, 2.3592, 2.2913, 2.236, 2.1901,
                       2.1512, 2.1179, 2.0889, 2.0636, 2.0411, 2.021, 2.0031, 1.9868, 1.972, 1.9586],
                      [29, 4.1829, 3.3276, 2.9341, 2.7014, 2.5454, 2.4324, 2.3463, 2.2783, 2.2229, 2.1768,
                       2.1379, 2.1045, 2.0755, 2.05, 2.0275, 2.0074, 1.9893, 1.973, 1.9582, 1.9446],
                      [30, 4.1709, 3.3158, 2.9223, 2.6896, 2.5335, 2.4205, 2.3343, 2.2662, 2.2107, 2.1646,
                       2.1255, 2.0921, 2.0629, 2.0374, 2.0148, 1.9946, 1.9765, 1.9601, 1.9452, 1.9317],
                      [31, 4.1597, 3.3048, 2.9113, 2.6787, 2.5225, 2.4094, 2.3232, 2.2549, 2.1994, 2.1531,
                       2.1141, 2.0805, 2.0513, 2.0257, 2.003, 1.9828, 1.9646, 1.9481, 1.9332, 1.9196],
                      [32, 4.1491, 3.2945, 2.9011, 2.6684, 2.5123, 2.3991, 2.3127, 2.2444, 2.1888, 2.1425,
                       2.1033, 2.0697, 2.0404, 2.0147, 1.992, 1.9717, 1.9534, 1.9369, 1.9219, 1.9083],
                      [33, 4.1392, 3.2849, 2.8915, 2.6589, 2.5027, 2.3894, 2.303, 2.2346, 2.1789, 2.1325,
                       2.0933, 2.0596, 2.0302, 2.0045, 1.9817, 1.9613, 1.943, 1.9264, 1.9114, 1.8977],
                      [34, 4.13, 3.2759, 2.8826, 2.6499, 2.4936, 2.3803, 2.2938, 2.2253, 2.1696, 2.1231,
                       2.0838, 2.05, 2.0207, 1.9949, 1.972, 1.9516, 1.9332, 1.9166, 1.9015, 1.8877],
                      [35, 4.1214, 3.2674, 2.8742, 2.6415, 2.4851, 2.3718, 2.2852, 2.2167, 2.1608, 2.1143,
                       2.0749, 2.0411, 2.0117, 1.9858, 1.9629, 1.9424, 1.924, 1.9073, 1.8922, 1.8784],
                      [36, 4.1132, 3.2594, 2.8663, 2.6335, 2.4771, 2.3637, 2.2771, 2.2085, 2.1526, 2.1061,
                       2.0666, 2.0327, 2.0032, 1.9773, 1.9543, 1.9338, 1.9153, 1.8986, 1.8834, 1.8696],
                      [37, 4.1055, 3.2519, 2.8588, 2.6261, 2.4696, 2.3562, 2.2695, 2.2008, 2.1449, 2.0982,
                       2.0587, 2.0248, 1.9952, 1.9692, 1.9462, 1.9256, 1.9071, 1.8904, 1.8752, 1.8613],
                      [38, 4.0981, 3.2448, 2.8517, 2.619, 2.4625, 2.349, 2.2623, 2.1935, 2.1375, 2.0909,
                       2.0513, 2.0173, 1.9877, 1.9617, 1.9386, 1.9179, 1.8994, 1.8826, 1.8673, 1.8534],
                      [39, 4.0913, 3.2381, 2.8451, 2.6123, 2.4558, 2.3422, 2.2555, 2.1867, 2.1306, 2.0839,
                       2.0442, 2.0102, 1.9805, 1.9545, 1.9313, 1.9107, 1.8921, 1.8752, 1.8599, 1.8459],
                      [40, 4.0848, 3.2317, 2.8388, 2.606, 2.4495, 2.3359, 2.249, 2.1802, 2.124, 2.0773,
                       2.0376, 2.0035, 1.9738, 1.9476, 1.9245, 1.9038, 1.8851, 1.8682, 1.8529, 1.8389],
                      [41, 4.0786, 3.2257, 2.8328, 2.6, 2.4434, 2.3298, 2.2429, 2.174, 2.1178, 2.071,
                       2.0312, 1.9971, 1.9673, 1.9412, 1.9179, 1.8972, 1.8785, 1.8616, 1.8462, 1.8321],
                      [42, 4.0727, 3.2199, 2.8271, 2.5943, 2.4377, 2.324, 2.2371, 2.1681, 2.1119, 2.065,
                       2.0252, 1.991, 1.9612, 1.935, 1.9118, 1.8909, 1.8722, 1.8553, 1.8399, 1.8258],
                      [43, 4.067, 3.2145, 2.8216, 2.5888, 2.4322, 2.3185, 2.2315, 2.1625, 2.1062, 2.0593,
                       2.0195, 1.9852, 1.9554, 1.9292, 1.9059, 1.885, 1.8663, 1.8493, 1.8338, 1.8197],
                      [44, 4.0617, 3.2093, 2.8165, 2.5837, 2.4271, 2.3133, 2.2262, 2.1572, 2.1009, 2.0539,
                       2.014, 1.9797, 1.9499, 1.9236, 1.9002, 1.8794, 1.8606, 1.8436, 1.8281, 1.8139],
                      [45, 4.0566, 3.2043, 2.8115, 2.5787, 2.4221, 2.3083, 2.2212, 2.1521, 2.0958, 2.0487,
                       2.0088, 1.9745, 1.9446, 1.9182, 1.8949, 1.874, 1.8551, 1.8381, 1.8226, 1.8084],
                      [46, 4.0518, 3.1996, 2.8068, 2.574, 2.4174, 2.3035, 2.2164, 2.1473, 2.0909, 2.0438,
                       2.0039, 1.9695, 1.9395, 1.9132, 1.8898, 1.8688, 1.85, 1.8329, 1.8173, 1.8031],
                      [47, 4.0471, 3.1951, 2.8024, 2.5695, 2.4128, 2.299, 2.2118, 2.1427, 2.0862, 2.0391,
                       1.9991, 1.9647, 1.9347, 1.9083, 1.8849, 1.8639, 1.845, 1.8279, 1.8123, 1.798],
                      [48, 4.0426, 3.1907, 2.7981, 2.5653, 2.4085, 2.2946, 2.2074, 2.1382, 2.0817, 2.0346,
                       1.9946, 1.9601, 1.9301, 1.9037, 1.8802, 1.8592, 1.8402, 1.8231, 1.8075, 1.7932],
                      [49, 4.0384, 3.1866, 2.7939, 2.5611, 2.4044, 2.2904, 2.2032, 2.134, 2.0774, 2.0303,
                       1.9902, 1.9558, 1.9257, 1.8992, 1.8757, 1.8547, 1.8357, 1.8185, 1.8029, 1.7886],
                      [50, 4.0343, 3.1826, 2.79, 2.5572, 2.4004, 2.2864, 2.1992, 2.1299, 2.0734, 2.0261,
                       1.9861, 1.9515, 1.9214, 1.8949, 1.8714, 1.8503, 1.8313, 1.8141, 1.7985, 1.7841],
                      [51, 4.0303, 3.1788, 2.7862, 2.5534, 2.3966, 2.2826, 2.1953, 2.126, 2.0694, 2.0222,
                       1.982, 1.9475, 1.9174, 1.8908, 1.8673, 1.8462, 1.8272, 1.8099, 1.7942, 1.7798],
                      [52, 4.0266, 3.1752, 2.7826, 2.5498, 2.3929, 2.2789, 2.1916, 2.1223, 2.0656, 2.0184,
                       1.9782, 1.9436, 1.9134, 1.8869, 1.8633, 1.8422, 1.8231, 1.8059, 1.7901, 1.7758],
                      [53, 4.023, 3.1716, 2.7791, 2.5463, 2.3894, 2.2754, 2.1881, 2.1187, 2.062, 2.0147,
                       1.9745, 1.9399, 1.9097, 1.8831, 1.8595, 1.8383, 1.8193, 1.802, 1.7862, 1.7718],
                      [54, 4.0196, 3.1683, 2.7757, 2.5429, 2.3861, 2.272, 2.1846, 2.1152, 2.0585, 2.0112,
                       1.971, 1.9363, 1.9061, 1.8795, 1.8558, 1.8346, 1.8155, 1.7982, 1.7825, 1.768],
                      [55, 4.0162, 3.165, 2.7725, 2.5397, 2.3828, 2.2687, 2.1813, 2.1119, 2.0552, 2.0078,
                       1.9676, 1.9329, 1.9026, 1.876, 1.8523, 1.8311, 1.812, 1.7946, 1.7788, 1.7644],
                      [56, 4.0129, 3.1618, 2.7694, 2.5366, 2.3797, 2.2656, 2.1781, 2.1087, 2.0519, 2.0045,
                       1.9642, 1.9296, 1.8993, 1.8726, 1.8489, 1.8276, 1.8085, 1.7912, 1.7753, 1.7608],
                      [57, 4.0099, 3.1589, 2.7665, 2.5336, 2.3767, 2.2625, 2.1751, 2.1056, 2.0488, 2.0014,
                       1.9611, 1.9264, 1.896, 1.8693, 1.8456, 1.8244, 1.8052, 1.7878, 1.772, 1.7575],
                      [58, 4.0069, 3.1559, 2.7635, 2.5307, 2.3738, 2.2596, 2.1721, 2.1026, 2.0458, 1.9983,
                       1.958, 1.9233, 1.8929, 1.8662, 1.8424, 1.8212, 1.802, 1.7846, 1.7687, 1.7542],
                      [59, 4.0039, 3.1531, 2.7608, 2.5279, 2.371, 2.2568, 2.1693, 2.0997, 2.0429, 1.9954,
                       1.9551, 1.9203, 1.8899, 1.8632, 1.8394, 1.8181, 1.7989, 1.7815, 1.7656, 1.751],
                      [60, 4.0012, 3.1504, 2.7581, 2.5252, 2.3683, 2.254, 2.1665, 2.097, 2.0401, 1.9926,
                       1.9522, 1.9174, 1.887, 1.8603, 1.8364, 1.8151, 1.7959, 1.7784, 1.7625, 1.748],
                      [61, 3.9985, 3.1478, 2.7555, 2.5226, 2.3657, 2.2514, 2.1639, 2.0943, 2.0374, 1.9899,
                       1.9495, 1.9146, 1.8842, 1.8574, 1.8336, 1.8122, 1.793, 1.7755, 1.7596, 1.745],
                      [62, 3.9959, 3.1453, 2.753, 2.5201, 2.3631, 2.2489, 2.1613, 2.0917, 2.0348, 1.9872,
                       1.9468, 1.9119, 1.8815, 1.8547, 1.8308, 1.8095, 1.7902, 1.7727, 1.7568, 1.7422],
                      [63, 3.9934, 3.1428, 2.7506, 2.5176, 2.3607, 2.2464, 2.1588, 2.0892, 2.0322, 1.9847,
                       1.9442, 1.9093, 1.8789, 1.852, 1.8282, 1.8068, 1.7875, 1.77, 1.754, 1.7394],
                      [64, 3.9909, 3.1404, 2.7482, 2.5153, 2.3583, 2.244, 2.1564, 2.0868, 2.0298, 1.9822,
                       1.9417, 1.9068, 1.8763, 1.8495, 1.8256, 1.8042, 1.7849, 1.7673, 1.7514, 1.7368],
                      [65, 3.9885, 3.1381, 2.7459, 2.513, 2.356, 2.2417, 2.1541, 2.0844, 2.0274, 1.9798,
                       1.9393, 1.9044, 1.8739, 1.847, 1.8231, 1.8017, 1.7823, 1.7648, 1.7488, 1.7342],
                      [66, 3.9862, 3.1359, 2.7437, 2.5108, 2.3538, 2.2395, 2.1518, 2.0821, 2.0251, 1.9775,
                       1.937, 1.902, 1.8715, 1.8446, 1.8207, 1.7992, 1.7799, 1.7623, 1.7463, 1.7316],
                      [67, 3.9841, 3.1338, 2.7416, 2.5087, 2.3516, 2.2373, 2.1497, 2.0799, 2.0229, 1.9752,
                       1.9347, 1.8997, 1.8692, 1.8423, 1.8183, 1.7968, 1.7775, 1.7599, 1.7439, 1.7292],
                      [68, 3.9819, 3.1317, 2.7395, 2.5066, 2.3496, 2.2352, 2.1475, 2.0778, 2.0207, 1.973,
                       1.9325, 1.8975, 1.867, 1.84, 1.816, 1.7945, 1.7752, 1.7576, 1.7415, 1.7268],
                      [69, 3.9798, 3.1297, 2.7375, 2.5046, 2.3475, 2.2332, 2.1455, 2.0757, 2.0186, 1.9709,
                       1.9303, 1.8954, 1.8648, 1.8378, 1.8138, 1.7923, 1.7729, 1.7553, 1.7393, 1.7246],
                      [70, 3.9778, 3.1277, 2.7355, 2.5027, 2.3456, 2.2312, 2.1435, 2.0737, 2.0166, 1.9689,
                       1.9283, 1.8932, 1.8627, 1.8357, 1.8117, 1.7902, 1.7707, 1.7531, 1.7371, 1.7223],
                      [71, 3.9758, 3.1258, 2.7336, 2.5007, 2.3437, 2.2293, 2.1415, 2.0717, 2.0146, 1.9669,
                       1.9263, 1.8912, 1.8606, 1.8336, 1.8096, 1.7881, 1.7686, 1.751, 1.7349, 1.7202],
                      [72, 3.9739, 3.1239, 2.7318, 2.4989, 2.3418, 2.2274, 2.1397, 2.0698, 2.0127, 1.9649,
                       1.9243, 1.8892, 1.8586, 1.8316, 1.8076, 1.786, 1.7666, 1.7489, 1.7328, 1.7181],
                      [73, 3.9721, 3.1221, 2.73, 2.4971, 2.34, 2.2256, 2.1378, 2.068, 2.0108, 1.9631,
                       1.9224, 1.8873, 1.8567, 1.8297, 1.8056, 1.784, 1.7646, 1.7469, 1.7308, 1.716],
                      [74, 3.9703, 3.1204, 2.7283, 2.4954, 2.3383, 2.2238, 2.1361, 2.0662, 2.009, 1.9612,
                       1.9205, 1.8854, 1.8548, 1.8278, 1.8037, 1.7821, 1.7626, 1.7449, 1.7288, 1.714],
                      [75, 3.9685, 3.1186, 2.7266, 2.4937, 2.3366, 2.2221, 2.1343, 2.0645, 2.0073, 1.9595,
                       1.9188, 1.8836, 1.853, 1.8259, 1.8018, 1.7802, 1.7607, 1.7431, 1.7269, 1.7121],
                      [76, 3.9668, 3.117, 2.7249, 2.4921, 2.3349, 2.2204, 2.1326, 2.0627, 2.0055, 1.9577,
                       1.917, 1.8819, 1.8512, 1.8241, 1.8, 1.7784, 1.7589, 1.7412, 1.725, 1.7102],
                      [77, 3.9651, 3.1154, 2.7233, 2.4904, 2.3333, 2.2188, 2.131, 2.0611, 2.0039, 1.956,
                       1.9153, 1.8801, 1.8494, 1.8223, 1.7982, 1.7766, 1.7571, 1.7394, 1.7232, 1.7084],
                      [78, 3.9635, 3.1138, 2.7218, 2.4889, 2.3318, 2.2172, 2.1294, 2.0595, 2.0022, 1.9544,
                       1.9136, 1.8785, 1.8478, 1.8206, 1.7965, 1.7749, 1.7554, 1.7376, 1.7214, 1.7066],
                      [79, 3.9619, 3.1123, 2.7203, 2.4874, 2.3302, 2.2157, 2.1279, 2.0579, 2.0006, 1.9528,
                       1.912, 1.8769, 1.8461, 1.819, 1.7948, 1.7732, 1.7537, 1.7359, 1.7197, 1.7048],
                      [80, 3.9604, 3.1107, 2.7188, 2.4859, 2.3287, 2.2142, 2.1263, 2.0564, 1.9991, 1.9512,
                       1.9105, 1.8753, 1.8445, 1.8174, 1.7932, 1.7716, 1.752, 1.7342, 1.718, 1.7032],
                      [81, 3.9589, 3.1093, 2.7173, 2.4845, 2.3273, 2.2127, 2.1248, 2.0549, 1.9976, 1.9497,
                       1.9089, 1.8737, 1.8429, 1.8158, 1.7916, 1.77, 1.7504, 1.7326, 1.7164, 1.7015],
                      [82, 3.9574, 3.1079, 2.716, 2.483, 2.3258, 2.2113, 2.1234, 2.0534, 1.9962, 1.9482,
                       1.9074, 1.8722, 1.8414, 1.8143, 1.7901, 1.7684, 1.7488, 1.731, 1.7148, 1.6999],
                      [83, 3.956, 3.1065, 2.7146, 2.4817, 2.3245, 2.2099, 2.122, 2.052, 1.9947, 1.9468,
                       1.906, 1.8707, 1.8399, 1.8127, 1.7886, 1.7669, 1.7473, 1.7295, 1.7132, 1.6983],
                      [84, 3.9546, 3.1051, 2.7132, 2.4803, 2.3231, 2.2086, 2.1206, 2.0506, 1.9933, 1.9454,
                       1.9045, 1.8693, 1.8385, 1.8113, 1.7871, 1.7654, 1.7458, 1.728, 1.7117, 1.6968],
                      [85, 3.9532, 3.1039, 2.7119, 2.479, 2.3218, 2.2072, 2.1193, 2.0493, 1.9919, 1.944,
                       1.9031, 1.8679, 1.8371, 1.8099, 1.7856, 1.7639, 1.7443, 1.7265, 1.7102, 1.6953],
                      [86, 3.9519, 3.1026, 2.7106, 2.4777, 2.3205, 2.2059, 2.118, 2.048, 1.9906, 1.9426,
                       1.9018, 1.8665, 1.8357, 1.8085, 1.7842, 1.7625, 1.7429, 1.725, 1.7088, 1.6938],
                      [87, 3.9506, 3.1013, 2.7094, 2.4765, 2.3193, 2.2047, 2.1167, 2.0467, 1.9893, 1.9413,
                       1.9005, 1.8652, 1.8343, 1.8071, 1.7829, 1.7611, 1.7415, 1.7236, 1.7073, 1.6924],
                      [88, 3.9493, 3.1001, 2.7082, 2.4753, 2.318, 2.2034, 2.1155, 2.0454, 1.9881, 1.94,
                       1.8992, 1.8639, 1.833, 1.8058, 1.7815, 1.7598, 1.7401, 1.7223, 1.706, 1.691],
                      [89, 3.9481, 3.0988, 2.707, 2.4741, 2.3169, 2.2022, 2.1143, 2.0442, 1.9868, 1.9388,
                       1.8979, 1.8626, 1.8317, 1.8045, 1.7802, 1.7584, 1.7388, 1.7209, 1.7046, 1.6896],
                      [90, 3.9469, 3.0977, 2.7058, 2.4729, 2.3157, 2.2011, 2.1131, 2.043, 1.9856, 1.9376,
                       1.8967, 1.8613, 1.8305, 1.8032, 1.7789, 1.7571, 1.7375, 1.7196, 1.7033, 1.6883],
                      [91, 3.9457, 3.0965, 2.7047, 2.4718, 2.3146, 2.1999, 2.1119, 2.0418, 1.9844, 1.9364,
                       1.8955, 1.8601, 1.8292, 1.802, 1.7777, 1.7559, 1.7362, 1.7183, 1.702, 1.687],
                      [92, 3.9446, 3.0955, 2.7036, 2.4707, 2.3134, 2.1988, 2.1108, 2.0407, 1.9833, 1.9352,
                       1.8943, 1.8589, 1.828, 1.8008, 1.7764, 1.7546, 1.735, 1.717, 1.7007, 1.6857],
                      [93, 3.9435, 3.0944, 2.7025, 2.4696, 2.3123, 2.1977, 2.1097, 2.0395, 1.9821, 1.934,
                       1.8931, 1.8578, 1.8269, 1.7996, 1.7753, 1.7534, 1.7337, 1.7158, 1.6995, 1.6845],
                      [94, 3.9423, 3.0933, 2.7014, 2.4685, 2.3113, 2.1966, 2.1086, 2.0385, 1.981, 1.9329,
                       1.892, 1.8566, 1.8257, 1.7984, 1.7741, 1.7522, 1.7325, 1.7146, 1.6982, 1.6832],
                      [95, 3.9412, 3.0922, 2.7004, 2.4675, 2.3102, 2.1955, 2.1075, 2.0374, 1.9799, 1.9318,
                       1.8909, 1.8555, 1.8246, 1.7973, 1.7729, 1.7511, 1.7314, 1.7134, 1.6971, 1.682],
                      [96, 3.9402, 3.0912, 2.6994, 2.4665, 2.3092, 2.1945, 2.1065, 2.0363, 1.9789, 1.9308,
                       1.8898, 1.8544, 1.8235, 1.7961, 1.7718, 1.75, 1.7302, 1.7123, 1.6959, 1.6809],
                      [97, 3.9392, 3.0902, 2.6984, 2.4655, 2.3082, 2.1935, 2.1054, 2.0353, 1.9778, 1.9297,
                       1.8888, 1.8533, 1.8224, 1.7951, 1.7707, 1.7488, 1.7291, 1.7112, 1.6948, 1.6797],
                      [98, 3.9381, 3.0892, 2.6974, 2.4645, 2.3072, 2.1925, 2.1044, 2.0343, 1.9768, 1.9287,
                       1.8877, 1.8523, 1.8213, 1.794, 1.7696, 1.7478, 1.728, 1.71, 1.6936, 1.6786],
                      [99, 3.9371, 3.0882, 2.6965, 2.4636, 2.3062, 2.1916, 2.1035, 2.0333, 1.9758, 1.9277,
                       1.8867, 1.8513, 1.8203, 1.7929, 1.7686, 1.7467, 1.7269, 1.709, 1.6926, 1.6775],
                      [100, 3.9361, 3.0873, 2.6955, 2.4626, 2.3053, 2.1906, 2.1025, 2.0323, 1.9748, 1.9267,
                       1.8857, 1.8502, 1.8193, 1.7919, 1.7675, 1.7456, 1.7259, 1.7079, 1.6915, 1.6764],
                      [101, 3.9352, 3.0864, 2.6946, 2.4617, 2.3044, 2.1897, 2.1016, 2.0314, 1.9739, 1.9257,
                       1.8847, 1.8493, 1.8183, 1.7909, 1.7665, 1.7446, 1.7248, 1.7069, 1.6904, 1.6754],
                      [102, 3.9342, 3.0854, 2.6937, 2.4608, 2.3035, 2.1888, 2.1007, 2.0304, 1.9729, 1.9248,
                       1.8838, 1.8483, 1.8173, 1.7899, 1.7655, 1.7436, 1.7238, 1.7058, 1.6894, 1.6744],
                      [103, 3.9333, 3.0846, 2.6928, 2.4599, 2.3026, 2.1879, 2.0997, 2.0295, 1.972, 1.9238,
                       1.8828, 1.8474, 1.8163, 1.789, 1.7645, 1.7427, 1.7229, 1.7048, 1.6884, 1.6733],
                      [104, 3.9325, 3.0837, 2.692, 2.4591, 2.3017, 2.187, 2.0989, 2.0287, 1.9711, 1.9229,
                       1.8819, 1.8464, 1.8154, 1.788, 1.7636, 1.7417, 1.7219, 1.7039, 1.6874, 1.6723],
                      [105, 3.9316, 3.0828, 2.6912, 2.4582, 2.3009, 2.1861, 2.098, 2.0278, 1.9702, 1.922,
                       1.881, 1.8455, 1.8145, 1.7871, 1.7627, 1.7407, 1.7209, 1.7029, 1.6865, 1.6714],
                      [106, 3.9307, 3.082, 2.6903, 2.4574, 2.3, 2.1853, 2.0971, 2.0269, 1.9694, 1.9212,
                       1.8801, 1.8446, 1.8136, 1.7862, 1.7618, 1.7398, 1.72, 1.702, 1.6855, 1.6704],
                      [107, 3.9299, 3.0812, 2.6895, 2.4566, 2.2992, 2.1845, 2.0963, 2.0261, 1.9685, 1.9203,
                       1.8792, 1.8438, 1.8127, 1.7853, 1.7608, 1.7389, 1.7191, 1.7011, 1.6846, 1.6695],
                      [108, 3.929, 3.0804, 2.6887, 2.4558, 2.2984, 2.1837, 2.0955, 2.0252, 1.9677, 1.9195,
                       1.8784, 1.8429, 1.8118, 1.7844, 1.7599, 1.738, 1.7182, 1.7001, 1.6837, 1.6685],
                      [109, 3.9282, 3.0796, 2.6879, 2.455, 2.2976, 2.1828, 2.0947, 2.0244, 1.9669, 1.9186,
                       1.8776, 1.8421, 1.811, 1.7835, 1.7591, 1.7371, 1.7173, 1.6992, 1.6828, 1.6676],
                      [110, 3.9274, 3.0788, 2.6872, 2.4542, 2.2968, 2.1821, 2.0939, 2.0236, 1.9661, 1.9178,
                       1.8767, 1.8412, 1.8102, 1.7827, 1.7582, 1.7363, 1.7164, 1.6984, 1.6819, 1.6667],
                      [111, 3.9266, 3.0781, 2.6864, 2.4535, 2.2961, 2.1813, 2.0931, 2.0229, 1.9653, 1.917,
                       1.8759, 1.8404, 1.8093, 1.7819, 1.7574, 1.7354, 1.7156, 1.6975, 1.681, 1.6659],
                      [112, 3.9258, 3.0773, 2.6857, 2.4527, 2.2954, 2.1806, 2.0924, 2.0221, 1.9645, 1.9163,
                       1.8751, 1.8396, 1.8085, 1.7811, 1.7566, 1.7346, 1.7147, 1.6967, 1.6802, 1.665],
                      [113, 3.9251, 3.0766, 2.6849, 2.452, 2.2946, 2.1798, 2.0916, 2.0213, 1.9637, 1.9155,
                       1.8744, 1.8388, 1.8077, 1.7803, 1.7558, 1.7338, 1.7139, 1.6958, 1.6793, 1.6642],
                      [114, 3.9243, 3.0758, 2.6842, 2.4513, 2.2939, 2.1791, 2.0909, 2.0206, 1.963, 1.9147,
                       1.8736, 1.8381, 1.8069, 1.7795, 1.755, 1.733, 1.7131, 1.695, 1.6785, 1.6633],
                      [115, 3.9236, 3.0751, 2.6835, 2.4506, 2.2932, 2.1784, 2.0902, 2.0199, 1.9623, 1.914,
                       1.8729, 1.8373, 1.8062, 1.7787, 1.7542, 1.7322, 1.7123, 1.6942, 1.6777, 1.6625],
                      [116, 3.9228, 3.0744, 2.6828, 2.4499, 2.2925, 2.1777, 2.0895, 2.0192, 1.9615, 1.9132,
                       1.8721, 1.8365, 1.8054, 1.7779, 1.7534, 1.7314, 1.7115, 1.6934, 1.6769, 1.6617],
                      [117, 3.9222, 3.0738, 2.6821, 2.4492, 2.2918, 2.177, 2.0888, 2.0185, 1.9608, 1.9125,
                       1.8714, 1.8358, 1.8047, 1.7772, 1.7527, 1.7307, 1.7108, 1.6927, 1.6761, 1.6609],
                      [118, 3.9215, 3.0731, 2.6815, 2.4485, 2.2912, 2.1763, 2.0881, 2.0178, 1.9601, 1.9118,
                       1.8707, 1.8351, 1.804, 1.7765, 1.752, 1.7299, 1.71, 1.6919, 1.6754, 1.6602],
                      [119, 3.9208, 3.0724, 2.6808, 2.4479, 2.2905, 2.1757, 2.0874, 2.0171, 1.9594, 1.9111,
                       1.87, 1.8344, 1.8032, 1.7757, 1.7512, 1.7292, 1.7093, 1.6912, 1.6746, 1.6594],
                      [120, 3.9202, 3.0718, 2.6802, 2.4472, 2.2899, 2.175, 2.0868, 2.0164, 1.9588, 1.9105,
                       1.8693, 1.8337, 1.8026, 1.775, 1.7505, 1.7285, 1.7085, 1.6904, 1.6739, 1.6587],
                      [121, 3.9194, 3.0712, 2.6795, 2.4466, 2.2892, 2.1744, 2.0861, 2.0158, 1.9581, 1.9098,
                       1.8686, 1.833, 1.8019, 1.7743, 1.7498, 1.7278, 1.7078, 1.6897, 1.6732, 1.6579],
                      [122, 3.9188, 3.0705, 2.6789, 2.446, 2.2886, 2.1737, 2.0855, 2.0151, 1.9575, 1.9091,
                       1.868, 1.8324, 1.8012, 1.7736, 1.7491, 1.727, 1.7071, 1.689, 1.6724, 1.6572],
                      [123, 3.9181, 3.0699, 2.6783, 2.4454, 2.288, 2.1731, 2.0849, 2.0145, 1.9568, 1.9085,
                       1.8673, 1.8317, 1.8005, 1.773, 1.7484, 1.7264, 1.7064, 1.6883, 1.6717, 1.6565],
                      [124, 3.9176, 3.0693, 2.6777, 2.4448, 2.2874, 2.1725, 2.0842, 2.0139, 1.9562, 1.9078,
                       1.8667, 1.831, 1.7999, 1.7723, 1.7478, 1.7257, 1.7058, 1.6876, 1.6711, 1.6558],
                      [125, 3.9169, 3.0687, 2.6771, 2.4442, 2.2868, 2.1719, 2.0836, 2.0133, 1.9556, 1.9072,
                       1.866, 1.8304, 1.7992, 1.7717, 1.7471, 1.725, 1.7051, 1.6869, 1.6704, 1.6551],
                      [126, 3.9163, 3.0681, 2.6765, 2.4436, 2.2862, 2.1713, 2.083, 2.0126, 1.955, 1.9066,
                       1.8654, 1.8298, 1.7986, 1.771, 1.7464, 1.7244, 1.7044, 1.6863, 1.6697, 1.6544],
                      [127, 3.9157, 3.0675, 2.6759, 2.443, 2.2856, 2.1707, 2.0824, 2.0121, 1.9544, 1.906,
                       1.8648, 1.8291, 1.7979, 1.7704, 1.7458, 1.7237, 1.7038, 1.6856, 1.669, 1.6538],
                      [128, 3.9151, 3.0669, 2.6754, 2.4424, 2.285, 2.1701, 2.0819, 2.0115, 1.9538, 1.9054,
                       1.8642, 1.8285, 1.7974, 1.7698, 1.7452, 1.7231, 1.7031, 1.685, 1.6684, 1.6531],
                      [129, 3.9145, 3.0664, 2.6749, 2.4419, 2.2845, 2.1696, 2.0813, 2.0109, 1.9532, 1.9048,
                       1.8636, 1.828, 1.7967, 1.7692, 1.7446, 1.7225, 1.7025, 1.6843, 1.6677, 1.6525],
                      [130, 3.914, 3.0659, 2.6743, 2.4414, 2.2839, 2.169, 2.0807, 2.0103, 1.9526, 1.9042,
                       1.863, 1.8273, 1.7962, 1.7685, 1.744, 1.7219, 1.7019, 1.6837, 1.6671, 1.6519],
                      [131, 3.9134, 3.0653, 2.6737, 2.4408, 2.2834, 2.1685, 2.0802, 2.0098, 1.9521, 1.9037,
                       1.8624, 1.8268, 1.7956, 1.768, 1.7434, 1.7213, 1.7013, 1.6831, 1.6665, 1.6513],
                      [132, 3.9129, 3.0648, 2.6732, 2.4403, 2.2829, 2.168, 2.0796, 2.0092, 1.9515, 1.9031,
                       1.8619, 1.8262, 1.795, 1.7674, 1.7428, 1.7207, 1.7007, 1.6825, 1.6659, 1.6506],
                      [133, 3.9123, 3.0642, 2.6727, 2.4398, 2.2823, 2.1674, 2.0791, 2.0087, 1.951, 1.9026,
                       1.8613, 1.8256, 1.7944, 1.7668, 1.7422, 1.7201, 1.7001, 1.6819, 1.6653, 1.65],
                      [134, 3.9118, 3.0637, 2.6722, 2.4392, 2.2818, 2.1669, 2.0786, 2.0082, 1.9504, 1.902,
                       1.8608, 1.8251, 1.7939, 1.7662, 1.7416, 1.7195, 1.6995, 1.6813, 1.6647, 1.6494],
                      [135, 3.9112, 3.0632, 2.6717, 2.4387, 2.2813, 2.1664, 2.0781, 2.0076, 1.9499, 1.9015,
                       1.8602, 1.8245, 1.7933, 1.7657, 1.7411, 1.719, 1.6989, 1.6808, 1.6641, 1.6488],
                      [136, 3.9108, 3.0627, 2.6712, 2.4382, 2.2808, 2.1659, 2.0775, 2.0071, 1.9494, 1.901,
                       1.8597, 1.824, 1.7928, 1.7651, 1.7405, 1.7184, 1.6984, 1.6802, 1.6635, 1.6483],
                      [137, 3.9102, 3.0622, 2.6707, 2.4378, 2.2803, 2.1654, 2.077, 2.0066, 1.9488, 1.9004,
                       1.8592, 1.8235, 1.7922, 1.7646, 1.74, 1.7178, 1.6978, 1.6796, 1.663, 1.6477],
                      [138, 3.9098, 3.0617, 2.6702, 2.4373, 2.2798, 2.1649, 2.0766, 2.0061, 1.9483, 1.8999,
                       1.8586, 1.823, 1.7917, 1.7641, 1.7394, 1.7173, 1.6973, 1.6791, 1.6624, 1.6471],
                      [139, 3.9092, 3.0613, 2.6697, 2.4368, 2.2794, 2.1644, 2.0761, 2.0056, 1.9478, 1.8994,
                       1.8581, 1.8224, 1.7912, 1.7635, 1.7389, 1.7168, 1.6967, 1.6785, 1.6619, 1.6466],
                      [140, 3.9087, 3.0608, 2.6692, 2.4363, 2.2789, 2.1639, 2.0756, 2.0051, 1.9473, 1.8989,
                       1.8576, 1.8219, 1.7907, 1.763, 1.7384, 1.7162, 1.6962, 1.678, 1.6613, 1.646],
                      [141, 3.9083, 3.0603, 2.6688, 2.4359, 2.2784, 2.1634, 2.0751, 2.0046, 1.9469, 1.8984,
                       1.8571, 1.8214, 1.7901, 1.7625, 1.7379, 1.7157, 1.6957, 1.6775, 1.6608, 1.6455],
                      [142, 3.9078, 3.0598, 2.6683, 2.4354, 2.2779, 2.163, 2.0747, 2.0042, 1.9464, 1.8979,
                       1.8566, 1.8209, 1.7897, 1.762, 1.7374, 1.7152, 1.6952, 1.6769, 1.6603, 1.645],
                      [143, 3.9073, 3.0594, 2.6679, 2.435, 2.2775, 2.1625, 2.0742, 2.0037, 1.9459, 1.8975,
                       1.8562, 1.8204, 1.7892, 1.7615, 1.7368, 1.7147, 1.6946, 1.6764, 1.6598, 1.6444],
                      [144, 3.9068, 3.0589, 2.6675, 2.4345, 2.277, 2.1621, 2.0737, 2.0033, 1.9455, 1.897,
                       1.8557, 1.82, 1.7887, 1.761, 1.7364, 1.7142, 1.6941, 1.6759, 1.6592, 1.6439],
                      [145, 3.9064, 3.0585, 2.667, 2.4341, 2.2766, 2.1617, 2.0733, 2.0028, 1.945, 1.8965,
                       1.8552, 1.8195, 1.7882, 1.7605, 1.7359, 1.7137, 1.6936, 1.6754, 1.6587, 1.6434],
                      [146, 3.906, 3.0581, 2.6666, 2.4337, 2.2762, 2.1612, 2.0728, 2.0024, 1.9445, 1.8961,
                       1.8548, 1.819, 1.7877, 1.7601, 1.7354, 1.7132, 1.6932, 1.6749, 1.6582, 1.6429],
                      [147, 3.9055, 3.0576, 2.6662, 2.4332, 2.2758, 2.1608, 2.0724, 2.0019, 1.9441, 1.8956,
                       1.8543, 1.8186, 1.7873, 1.7596, 1.7349, 1.7127, 1.6927, 1.6744, 1.6578, 1.6424],
                      [148, 3.9051, 3.0572, 2.6657, 2.4328, 2.2753, 2.1604, 2.072, 2.0015, 1.9437, 1.8952,
                       1.8539, 1.8181, 1.7868, 1.7591, 1.7344, 1.7123, 1.6922, 1.6739, 1.6573, 1.6419],
                      [149, 3.9046, 3.0568, 2.6653, 2.4324, 2.2749, 2.1599, 2.0716, 2.0011, 1.9432, 1.8947,
                       1.8534, 1.8177, 1.7864, 1.7587, 1.734, 1.7118, 1.6917, 1.6735, 1.6568, 1.6414],
                      [150, 3.9042, 3.0564, 2.6649, 2.4319, 2.2745, 2.1595, 2.0711, 2.0006, 1.9428, 1.8943,
                       1.853, 1.8172, 1.7859, 1.7582, 1.7335, 1.7113, 1.6913, 1.673, 1.6563, 1.641],
                      [151, 3.9038, 3.056, 2.6645, 2.4315, 2.2741, 2.1591, 2.0707, 2.0002, 1.9424, 1.8939,
                       1.8526, 1.8168, 1.7855, 1.7578, 1.7331, 1.7109, 1.6908, 1.6726, 1.6558, 1.6405],
                      [152, 3.9033, 3.0555, 2.6641, 2.4312, 2.2737, 2.1587, 2.0703, 1.9998, 1.942, 1.8935,
                       1.8521, 1.8163, 1.785, 1.7573, 1.7326, 1.7104, 1.6904, 1.6721, 1.6554, 1.64],
                      [153, 3.903, 3.0552, 2.6637, 2.4308, 2.2733, 2.1583, 2.0699, 1.9994, 1.9416, 1.8931,
                       1.8517, 1.8159, 1.7846, 1.7569, 1.7322, 1.71, 1.6899, 1.6717, 1.6549, 1.6396],
                      [154, 3.9026, 3.0548, 2.6634, 2.4304, 2.2729, 2.1579, 2.0695, 1.999, 1.9412, 1.8926,
                       1.8513, 1.8155, 1.7842, 1.7565, 1.7318, 1.7096, 1.6895, 1.6712, 1.6545, 1.6391],
                      [155, 3.9021, 3.0544, 2.6629, 2.43, 2.2725, 2.1575, 2.0691, 1.9986, 1.9407, 1.8923,
                       1.8509, 1.8151, 1.7838, 1.7561, 1.7314, 1.7091, 1.6891, 1.6708, 1.654, 1.6387],
                      [156, 3.9018, 3.054, 2.6626, 2.4296, 2.2722, 2.1571, 2.0687, 1.9982, 1.9403, 1.8918,
                       1.8505, 1.8147, 1.7834, 1.7557, 1.7309, 1.7087, 1.6886, 1.6703, 1.6536, 1.6383],
                      [157, 3.9014, 3.0537, 2.6622, 2.4293, 2.2717, 2.1568, 2.0684, 1.9978, 1.94, 1.8915,
                       1.8501, 1.8143, 1.7829, 1.7552, 1.7305, 1.7083, 1.6882, 1.6699, 1.6532, 1.6378],
                      [158, 3.901, 3.0533, 2.6618, 2.4289, 2.2714, 2.1564, 2.068, 1.9974, 1.9396, 1.8911,
                       1.8497, 1.8139, 1.7826, 1.7548, 1.7301, 1.7079, 1.6878, 1.6695, 1.6528, 1.6374],
                      [159, 3.9006, 3.0529, 2.6615, 2.4285, 2.271, 2.156, 2.0676, 1.997, 1.9392, 1.8907,
                       1.8493, 1.8135, 1.7822, 1.7544, 1.7297, 1.7075, 1.6874, 1.6691, 1.6524, 1.637],
                      [160, 3.9002, 3.0525, 2.6611, 2.4282, 2.2706, 2.1556, 2.0672, 1.9967, 1.9388, 1.8903,
                       1.8489, 1.8131, 1.7818, 1.754, 1.7293, 1.7071, 1.687, 1.6687, 1.6519, 1.6366],
                      [161, 3.8998, 3.0522, 2.6607, 2.4278, 2.2703, 2.1553, 2.0669, 1.9963, 1.9385, 1.8899,
                       1.8485, 1.8127, 1.7814, 1.7537, 1.7289, 1.7067, 1.6866, 1.6683, 1.6515, 1.6361],
                      [162, 3.8995, 3.0518, 2.6604, 2.4275, 2.27, 2.155, 2.0665, 1.9959, 1.9381, 1.8895,
                       1.8482, 1.8124, 1.781, 1.7533, 1.7285, 1.7063, 1.6862, 1.6679, 1.6511, 1.6357],
                      [163, 3.8991, 3.0515, 2.6601, 2.4271, 2.2696, 2.1546, 2.0662, 1.9956, 1.9377, 1.8892,
                       1.8478, 1.812, 1.7806, 1.7529, 1.7282, 1.7059, 1.6858, 1.6675, 1.6507, 1.6353],
                      [164, 3.8987, 3.0512, 2.6597, 2.4268, 2.2693, 2.1542, 2.0658, 1.9953, 1.9374, 1.8888,
                       1.8474, 1.8116, 1.7803, 1.7525, 1.7278, 1.7055, 1.6854, 1.6671, 1.6503, 1.6349],
                      [165, 3.8985, 3.0508, 2.6594, 2.4264, 2.2689, 2.1539, 2.0655, 1.9949, 1.937, 1.8885,
                       1.8471, 1.8112, 1.7799, 1.7522, 1.7274, 1.7052, 1.685, 1.6667, 1.6499, 1.6345],
                      [166, 3.8981, 3.0505, 2.6591, 2.4261, 2.2686, 2.1536, 2.0651, 1.9945, 1.9367, 1.8881,
                       1.8467, 1.8109, 1.7795, 1.7518, 1.727, 1.7048, 1.6846, 1.6663, 1.6496, 1.6341],
                      [167, 3.8977, 3.0502, 2.6587, 2.4258, 2.2683, 2.1533, 2.0648, 1.9942, 1.9363, 1.8878,
                       1.8464, 1.8105, 1.7792, 1.7514, 1.7266, 1.7044, 1.6843, 1.6659, 1.6492, 1.6338],
                      [168, 3.8974, 3.0498, 2.6584, 2.4254, 2.268, 2.1529, 2.0645, 1.9939, 1.936, 1.8874,
                       1.846, 1.8102, 1.7788, 1.7511, 1.7263, 1.704, 1.6839, 1.6656, 1.6488, 1.6334],
                      [169, 3.8971, 3.0495, 2.6581, 2.4251, 2.2676, 2.1526, 2.0641, 1.9936, 1.9357, 1.8871,
                       1.8457, 1.8099, 1.7785, 1.7507, 1.7259, 1.7037, 1.6835, 1.6652, 1.6484, 1.633],
                      [170, 3.8967, 3.0492, 2.6578, 2.4248, 2.2673, 2.1523, 2.0638, 1.9932, 1.9353, 1.8868,
                       1.8454, 1.8095, 1.7781, 1.7504, 1.7256, 1.7033, 1.6832, 1.6648, 1.6481, 1.6326],
                      [171, 3.8965, 3.0488, 2.6575, 2.4245, 2.267, 2.152, 2.0635, 1.9929, 1.935, 1.8864,
                       1.845, 1.8092, 1.7778, 1.75, 1.7252, 1.703, 1.6828, 1.6645, 1.6477, 1.6323],
                      [172, 3.8961, 3.0485, 2.6571, 2.4242, 2.2667, 2.1516, 2.0632, 1.9926, 1.9347, 1.8861,
                       1.8447, 1.8088, 1.7774, 1.7497, 1.7249, 1.7026, 1.6825, 1.6641, 1.6473, 1.6319],
                      [173, 3.8958, 3.0482, 2.6568, 2.4239, 2.2664, 2.1513, 2.0628, 1.9923, 1.9343, 1.8858,
                       1.8443, 1.8085, 1.7771, 1.7493, 1.7246, 1.7023, 1.6821, 1.6638, 1.647, 1.6316],
                      [174, 3.8954, 3.0479, 2.6566, 2.4236, 2.266, 2.151, 2.0626, 1.9919, 1.934, 1.8855,
                       1.844, 1.8082, 1.7768, 1.749, 1.7242, 1.7019, 1.6818, 1.6634, 1.6466, 1.6312],
                      [175, 3.8952, 3.0476, 2.6563, 2.4233, 2.2658, 2.1507, 2.0622, 1.9916, 1.9337, 1.8852,
                       1.8437, 1.8078, 1.7764, 1.7487, 1.7239, 1.7016, 1.6814, 1.6631, 1.6463, 1.6309],
                      [176, 3.8948, 3.0473, 2.6559, 2.423, 2.2655, 2.1504, 2.0619, 1.9913, 1.9334, 1.8848,
                       1.8434, 1.8075, 1.7761, 1.7483, 1.7236, 1.7013, 1.6811, 1.6628, 1.646, 1.6305],
                      [177, 3.8945, 3.047, 2.6556, 2.4227, 2.2652, 2.1501, 2.0616, 1.991, 1.9331, 1.8845,
                       1.8431, 1.8072, 1.7758, 1.748, 1.7232, 1.7009, 1.6808, 1.6624, 1.6456, 1.6302],
                      [178, 3.8943, 3.0467, 2.6554, 2.4224, 2.2649, 2.1498, 2.0613, 1.9907, 1.9328, 1.8842,
                       1.8428, 1.8069, 1.7755, 1.7477, 1.7229, 1.7006, 1.6805, 1.6621, 1.6453, 1.6298],
                      [179, 3.8939, 3.0465, 2.6551, 2.4221, 2.2646, 2.1495, 2.0611, 1.9904, 1.9325, 1.8839,
                       1.8425, 1.8066, 1.7752, 1.7474, 1.7226, 1.7003, 1.6801, 1.6618, 1.645, 1.6295],
                      [180, 3.8936, 3.0462, 2.6548, 2.4218, 2.2643, 2.1492, 2.0608, 1.9901, 1.9322, 1.8836,
                       1.8422, 1.8063, 1.7749, 1.7471, 1.7223, 1.7, 1.6798, 1.6614, 1.6446, 1.6292],
                      [181, 3.8933, 3.0458, 2.6545, 2.4216, 2.264, 2.149, 2.0605, 1.9899, 1.9319, 1.8833,
                       1.8419, 1.806, 1.7746, 1.7468, 1.7219, 1.6997, 1.6795, 1.6611, 1.6443, 1.6289],
                      [182, 3.8931, 3.0456, 2.6543, 2.4213, 2.2638, 2.1487, 2.0602, 1.9896, 1.9316, 1.883,
                       1.8416, 1.8057, 1.7743, 1.7465, 1.7217, 1.6994, 1.6792, 1.6608, 1.644, 1.6286],
                      [183, 3.8928, 3.0453, 2.654, 2.421, 2.2635, 2.1484, 2.0599, 1.9893, 1.9313, 1.8827,
                       1.8413, 1.8054, 1.774, 1.7462, 1.7214, 1.6991, 1.6789, 1.6605, 1.6437, 1.6282],
                      [184, 3.8925, 3.045, 2.6537, 2.4207, 2.2632, 2.1481, 2.0596, 1.989, 1.9311, 1.8825,
                       1.841, 1.8051, 1.7737, 1.7459, 1.721, 1.6987, 1.6786, 1.6602, 1.6434, 1.6279],
                      [185, 3.8923, 3.0448, 2.6534, 2.4205, 2.263, 2.1479, 2.0594, 1.9887, 1.9308, 1.8822,
                       1.8407, 1.8048, 1.7734, 1.7456, 1.7208, 1.6984, 1.6783, 1.6599, 1.643, 1.6276],
                      [186, 3.892, 3.0445, 2.6531, 2.4202, 2.2627, 2.1476, 2.0591, 1.9885, 1.9305, 1.8819,
                       1.8404, 1.8045, 1.7731, 1.7453, 1.7205, 1.6981, 1.678, 1.6596, 1.6428, 1.6273],
                      [187, 3.8917, 3.0442, 2.6529, 2.4199, 2.2624, 2.1473, 2.0588, 1.9882, 1.9302, 1.8816,
                       1.8401, 1.8042, 1.7728, 1.745, 1.7202, 1.6979, 1.6777, 1.6593, 1.6424, 1.627],
                      [188, 3.8914, 3.044, 2.6526, 2.4197, 2.2621, 2.1471, 2.0586, 1.9879, 1.9299, 1.8814,
                       1.8399, 1.804, 1.7725, 1.7447, 1.7199, 1.6976, 1.6774, 1.659, 1.6421, 1.6267],
                      [189, 3.8912, 3.0437, 2.6524, 2.4195, 2.2619, 2.1468, 2.0583, 1.9877, 1.9297, 1.8811,
                       1.8396, 1.8037, 1.7722, 1.7444, 1.7196, 1.6973, 1.6771, 1.6587, 1.6418, 1.6264],
                      [190, 3.8909, 3.0435, 2.6521, 2.4192, 2.2617, 2.1466, 2.0581, 1.9874, 1.9294, 1.8808,
                       1.8393, 1.8034, 1.772, 1.7441, 1.7193, 1.697, 1.6768, 1.6584, 1.6416, 1.6261],
                      [191, 3.8906, 3.0432, 2.6519, 2.4189, 2.2614, 2.1463, 2.0578, 1.9871, 1.9292, 1.8805,
                       1.8391, 1.8032, 1.7717, 1.7439, 1.719, 1.6967, 1.6765, 1.6581, 1.6413, 1.6258],
                      [192, 3.8903, 3.043, 2.6516, 2.4187, 2.2611, 2.1461, 2.0575, 1.9869, 1.9289, 1.8803,
                       1.8388, 1.8029, 1.7714, 1.7436, 1.7188, 1.6964, 1.6762, 1.6578, 1.641, 1.6255],
                      [193, 3.8901, 3.0427, 2.6514, 2.4184, 2.2609, 2.1458, 2.0573, 1.9866, 1.9286, 1.88,
                       1.8385, 1.8026, 1.7712, 1.7433, 1.7185, 1.6961, 1.6759, 1.6575, 1.6407, 1.6252],
                      [194, 3.8899, 3.0425, 2.6512, 2.4182, 2.2606, 2.1456, 2.057, 1.9864, 1.9284, 1.8798,
                       1.8383, 1.8023, 1.7709, 1.7431, 1.7182, 1.6959, 1.6757, 1.6572, 1.6404, 1.6249],
                      [195, 3.8896, 3.0422, 2.6509, 2.418, 2.2604, 2.1453, 2.0568, 1.9861, 1.9281, 1.8795,
                       1.838, 1.8021, 1.7706, 1.7428, 1.7179, 1.6956, 1.6754, 1.657, 1.6401, 1.6247],
                      [196, 3.8893, 3.042, 2.6507, 2.4177, 2.2602, 2.1451, 2.0566, 1.9859, 1.9279, 1.8793,
                       1.8377, 1.8018, 1.7704, 1.7425, 1.7177, 1.6953, 1.6751, 1.6567, 1.6399, 1.6244],
                      [197, 3.8891, 3.0418, 2.6504, 2.4175, 2.26, 2.1448, 2.0563, 1.9856, 1.9277, 1.879,
                       1.8375, 1.8016, 1.7701, 1.7423, 1.7174, 1.6951, 1.6748, 1.6564, 1.6396, 1.6241],
                      [198, 3.8889, 3.0415, 2.6502, 2.4173, 2.2597, 2.1446, 2.0561, 1.9854, 1.9274, 1.8788,
                       1.8373, 1.8013, 1.7699, 1.742, 1.7172, 1.6948, 1.6746, 1.6562, 1.6393, 1.6238],
                      [199, 3.8886, 3.0413, 2.65, 2.417, 2.2595, 2.1444, 2.0558, 1.9852, 1.9272, 1.8785,
                       1.837, 1.8011, 1.7696, 1.7418, 1.7169, 1.6946, 1.6743, 1.6559, 1.6391, 1.6236],
                      [200, 3.8883, 3.041, 2.6497, 2.4168, 2.2592, 2.1441, 2.0556, 1.9849, 1.9269, 1.8783, 1.8368, 1.8008, 1.7694, 1.7415, 1.7166, 1.6943, 1.6741, 1.6557, 1.6388, 1.62]])
    return ftest[int(row)][int(col)]


def tcalc(nf, p):
    """
     t-table for nf degrees of freedom (95% confidence)
    """
#
    if p == .05:
        if nf > 2:
            t = 4.3027
        if nf > 3:
            t = 3.1824
        if nf > 4:
            t = 2.7765
        if nf > 5:
            t = 2.5706
        if nf > 6:
            t = 2.4469
        if nf > 7:
            t = 2.3646
        if nf > 8:
            t = 2.3060
        if nf > 9:
            t = 2.2622
        if nf > 10:
            t = 2.2281
        if nf > 11:
            t = 2.2010
        if nf > 12:
            t = 2.1788
        if nf > 13:
            t = 2.1604
        if nf > 14:
            t = 2.1448
        if nf > 15:
            t = 2.1315
        if nf > 16:
            t = 2.1199
        if nf > 17:
            t = 2.1098
        if nf > 18:
            t = 2.1009
        if nf > 19:
            t = 2.0930
        if nf > 20:
            t = 2.0860
        if nf > 21:
            t = 2.0796
        if nf > 22:
            t = 2.0739
        if nf > 23:
            t = 2.0687
        if nf > 24:
            t = 2.0639
        if nf > 25:
            t = 2.0595
        if nf > 26:
            t = 2.0555
        if nf > 27:
            t = 2.0518
        if nf > 28:
            t = 2.0484
        if nf > 29:
            t = 2.0452
        if nf > 30:
            t = 2.0423
        if nf > 31:
            t = 2.0395
        if nf > 32:
            t = 2.0369
        if nf > 33:
            t = 2.0345
        if nf > 34:
            t = 2.0322
        if nf > 35:
            t = 2.0301
        if nf > 36:
            t = 2.0281
        if nf > 37:
            t = 2.0262
        if nf > 38:
            t = 2.0244
        if nf > 39:
            t = 2.0227
        if nf > 40:
            t = 2.0211
        if nf > 41:
            t = 2.0195
        if nf > 42:
            t = 2.0181
        if nf > 43:
            t = 2.0167
        if nf > 44:
            t = 2.0154
        if nf > 45:
            t = 2.0141
        if nf > 46:
            t = 2.0129
        if nf > 47:
            t = 2.0117
        if nf > 48:
            t = 2.0106
        if nf > 49:
            t = 2.0096
        if nf > 50:
            t = 2.0086
        if nf > 51:
            t = 2.0076
        if nf > 52:
            t = 2.0066
        if nf > 53:
            t = 2.0057
        if nf > 54:
            t = 2.0049
        if nf > 55:
            t = 2.0040
        if nf > 56:
            t = 2.0032
        if nf > 57:
            t = 2.0025
        if nf > 58:
            t = 2.0017
        if nf > 59:
            t = 2.0010
        if nf > 60:
            t = 2.0003
        if nf > 61:
            t = 1.9996
        if nf > 62:
            t = 1.9990
        if nf > 63:
            t = 1.9983
        if nf > 64:
            t = 1.9977
        if nf > 65:
            t = 1.9971
        if nf > 66:
            t = 1.9966
        if nf > 67:
            t = 1.9960
        if nf > 68:
            t = 1.9955
        if nf > 69:
            t = 1.9949
        if nf > 70:
            t = 1.9944
        if nf > 71:
            t = 1.9939
        if nf > 72:
            t = 1.9935
        if nf > 73:
            t = 1.9930
        if nf > 74:
            t = 1.9925
        if nf > 75:
            t = 1.9921
        if nf > 76:
            t = 1.9917
        if nf > 77:
            t = 1.9913
        if nf > 78:
            t = 1.9908
        if nf > 79:
            t = 1.9905
        if nf > 80:
            t = 1.9901
        if nf > 81:
            t = 1.9897
        if nf > 82:
            t = 1.9893
        if nf > 83:
            t = 1.9890
        if nf > 84:
            t = 1.9886
        if nf > 85:
            t = 1.9883
        if nf > 86:
            t = 1.9879
        if nf > 87:
            t = 1.9876
        if nf > 88:
            t = 1.9873
        if nf > 89:
            t = 1.9870
        if nf > 90:
            t = 1.9867
        if nf > 91:
            t = 1.9864
        if nf > 92:
            t = 1.9861
        if nf > 93:
            t = 1.9858
        if nf > 94:
            t = 1.9855
        if nf > 95:
            t = 1.9852
        if nf > 96:
            t = 1.9850
        if nf > 97:
            t = 1.9847
        if nf > 98:
            t = 1.9845
        if nf > 99:
            t = 1.9842
        if nf > 100:
            t = 1.9840
        return t
#
    elif p == .01:
        if nf > 2:
            t = 9.9250
        if nf > 3:
            t = 5.8408
        if nf > 4:
            t = 4.6041
        if nf > 5:
            t = 4.0321
        if nf > 6:
            t = 3.7074
        if nf > 7:
            t = 3.4995
        if nf > 8:
            t = 3.3554
        if nf > 9:
            t = 3.2498
        if nf > 10:
            t = 3.1693
        if nf > 11:
            t = 3.1058
        if nf > 12:
            t = 3.0545
        if nf > 13:
            t = 3.0123
        if nf > 14:
            t = 2.9768
        if nf > 15:
            t = 2.9467
        if nf > 16:
            t = 2.9208
        if nf > 17:
            t = 2.8982
        if nf > 18:
            t = 2.8784
        if nf > 19:
            t = 2.8609
        if nf > 20:
            t = 2.8453
        if nf > 21:
            t = 2.8314
        if nf > 22:
            t = 2.8188
        if nf > 23:
            t = 2.8073
        if nf > 24:
            t = 2.7970
        if nf > 25:
            t = 2.7874
        if nf > 26:
            t = 2.7787
        if nf > 27:
            t = 2.7707
        if nf > 28:
            t = 2.7633
        if nf > 29:
            t = 2.7564
        if nf > 30:
            t = 2.7500
        if nf > 31:
            t = 2.7440
        if nf > 32:
            t = 2.7385
        if nf > 33:
            t = 2.7333
        if nf > 34:
            t = 2.7284
        if nf > 35:
            t = 2.7238
        if nf > 36:
            t = 2.7195
        if nf > 37:
            t = 2.7154
        if nf > 38:
            t = 2.7116
        if nf > 39:
            t = 2.7079
        if nf > 40:
            t = 2.7045
        if nf > 41:
            t = 2.7012
        if nf > 42:
            t = 2.6981
        if nf > 43:
            t = 2.6951
        if nf > 44:
            t = 2.6923
        if nf > 45:
            t = 2.6896
        if nf > 46:
            t = 2.6870
        if nf > 47:
            t = 2.6846
        if nf > 48:
            t = 2.6822
        if nf > 49:
            t = 2.6800
        if nf > 50:
            t = 2.6778
        if nf > 51:
            t = 2.6757
        if nf > 52:
            t = 2.6737
        if nf > 53:
            t = 2.6718
        if nf > 54:
            t = 2.6700
        if nf > 55:
            t = 2.6682
        if nf > 56:
            t = 2.6665
        if nf > 57:
            t = 2.6649
        if nf > 58:
            t = 2.6633
        if nf > 59:
            t = 2.6618
        if nf > 60:
            t = 2.6603
        if nf > 61:
            t = 2.6589
        if nf > 62:
            t = 2.6575
        if nf > 63:
            t = 2.6561
        if nf > 64:
            t = 2.6549
        if nf > 65:
            t = 2.6536
        if nf > 66:
            t = 2.6524
        if nf > 67:
            t = 2.6512
        if nf > 68:
            t = 2.6501
        if nf > 69:
            t = 2.6490
        if nf > 70:
            t = 2.6479
        if nf > 71:
            t = 2.6469
        if nf > 72:
            t = 2.6458
        if nf > 73:
            t = 2.6449
        if nf > 74:
            t = 2.6439
        if nf > 75:
            t = 2.6430
        if nf > 76:
            t = 2.6421
        if nf > 77:
            t = 2.6412
        if nf > 78:
            t = 2.6403
        if nf > 79:
            t = 2.6395
        if nf > 80:
            t = 2.6387
        if nf > 81:
            t = 2.6379
        if nf > 82:
            t = 2.6371
        if nf > 83:
            t = 2.6364
        if nf > 84:
            t = 2.6356
        if nf > 85:
            t = 2.6349
        if nf > 86:
            t = 2.6342
        if nf > 87:
            t = 2.6335
        if nf > 88:
            t = 2.6329
        if nf > 89:
            t = 2.6322
        if nf > 90:
            t = 2.6316
        if nf > 91:
            t = 2.6309
        if nf > 92:
            t = 2.6303
        if nf > 93:
            t = 2.6297
        if nf > 94:
            t = 2.6291
        if nf > 95:
            t = 2.6286
        if nf > 96:
            t = 2.6280
        if nf > 97:
            t = 2.6275
        if nf > 98:
            t = 2.6269
        if nf > 99:
            t = 2.6264
        if nf > 100:
            t = 2.6259
        return t
        return t
    else:
        return 0
#


def sbar(Ss):
    """
    calculate average s,sigma from list of "s"s.
    """
    if type(Ss) == list:
        Ss = np.array(Ss)
    npts = Ss.shape[0]
    Ss = Ss.transpose()

    avd, avs = [], []
    # D=np.array([Ss[0],Ss[1],Ss[2],Ss[3]+0.5*(Ss[0]+Ss[1]),Ss[4]+0.5*(Ss[1]+Ss[2]),Ss[5]+0.5*(Ss[0]+Ss[2])]).transpose()
    D = np.array([Ss[0], Ss[1], Ss[2], Ss[3] + 0.5 * (Ss[0] + Ss[1]),
                  Ss[4] + 0.5 * (Ss[1] + Ss[2]), Ss[5] + 0.5 * (Ss[0] + Ss[2])])
    for j in range(6):
        avd.append(np.average(D[j]))
        avs.append(np.average(Ss[j]))
    D = D.transpose()
    # for s in Ss:
    #    print 'from sbar: ',s
    #    D.append(s[:]) # append a copy of s
    #    D[-1][3]=D[-1][3]+0.5*(s[0]+s[1])
    #    D[-1][4]=D[-1][4]+0.5*(s[1]+s[2])
    #    D[-1][5]=D[-1][5]+0.5*(s[0]+s[2])
    #    for j in range(6):
    #        avd[j]+=(D[-1][j])/float(npts)
    #        avs[j]+=(s[j])/float(npts)
#   calculate sigma
    nf = (npts - 1) * 6  # number of degrees of freedom
    s0 = 0
    Dels = (D - avd)**2
    s0 = np.sum(Dels)
    sigma = np.sqrt(s0/float(nf))
    return nf, sigma, avs


def dohext(nf, sigma, s):
    """
    calculates hext parameters for nf, sigma and s

    Parameters
    __________
    nf :  number of degrees of freedom (measurements - 6)
    sigma : the sigma of the measurements
    s : [x11,x22,x33,x12,x23,x13] - the six tensor elements

    Return
    hpars : dictionary of Hext statistics with keys:
        'F_crit' : critical value for anisotropy
        'F12_crit' : critical value for tau1>tau2, tau2>3
        'F' : value of F
        'F12' : value of F12
        'F23' : value of F23
        'v1_dec': declination of principal eigenvector
        'v1_inc': inclination of principal eigenvector
        'v2_dec': declination of major eigenvector
        'v2_inc': inclination of major eigenvector
        'v3_dec': declination of minor eigenvector
        'v3_inc': inclination of minor eigenvector
        't1': principal eigenvalue
        't2': major eigenvalue
        't3': minor eigenvalue
        'e12': angle of confidence ellipse of principal eigenvector in direction of major eigenvector
        'e23': angle of confidence ellipse of major eigenvector in direction of minor eigenvector
        'e13': angle of confidence ellipse of principal eigenvector in direction of minor eigenvector

    If working with data set with no sigmas and the average is desired, use nf,sigma,avs=pmag.sbar(Ss) as input

    """

#
    hpars = {}
    hpars['F_crit'] = '0'
    hpars['F12_crit'] = '0'
    hpars["F"] = 0
    hpars["F12"] = 0
    hpars["F23"] = 0
    hpars["v1_dec"] = -1
    hpars["v1_inc"] = -1
    hpars["v2_dec"] = -1
    hpars["v2_inc"] = -1
    hpars["v3_dec"] = -1
    hpars["v3_inc"] = -1
    hpars["t1"] = -1
    hpars["t2"] = -1
    hpars["t3"] = -1
    hpars["e12"] = -1
    hpars["e23"] = -1
    hpars["e13"] = -1
    if nf < 0 or sigma == 0:
        return hpars
    f = np.sqrt(2. * fcalc(2, nf))
    t2sum = 0
    tau, Vdir = doseigs(s)
    for i in range(3):
        t2sum += tau[i]**2
    chibar = old_div((s[0] + s[1] + s[2]), 3.)
    hpars['F_crit'] = '%s' % (fcalc(5, nf))
    hpars['F12_crit'] = '%s' % (fcalc(2, nf))
    hpars["F"] = 0.4 * (t2sum - 3 * chibar**2) / (sigma**2)
    hpars["F12"] = 0.5 * (old_div((tau[0] - tau[1]), sigma))**2
    hpars["F23"] = 0.5 * (old_div((tau[1] - tau[2]), sigma))**2
    hpars["v1_dec"] = Vdir[0][0]
    hpars["v1_inc"] = Vdir[0][1]
    hpars["v2_dec"] = Vdir[1][0]
    hpars["v2_inc"] = Vdir[1][1]
    hpars["v3_dec"] = Vdir[2][0]
    hpars["v3_inc"] = Vdir[2][1]
    hpars["t1"] = tau[0]
    hpars["t2"] = tau[1]
    hpars["t3"] = tau[2]
    hpars["e12"] = np.arctan(
        old_div((f * sigma), (2 * abs(tau[0] - tau[1])))) * 180. / np.pi
    hpars["e23"] = np.arctan(
        old_div((f * sigma), (2 * abs(tau[1] - tau[2])))) * 180. / np.pi
    hpars["e13"] = np.arctan(
        old_div((f * sigma), (2 * abs(tau[0] - tau[2])))) * 180. / np.pi
    return hpars
#
#


def design(npos):
    """
     make a design matrix for an anisotropy experiment
    """
    if npos == 15:
        #
        # rotatable design of Jelinek for kappabridge (see Tauxe, 1998)
        #
        A = np.array([[.5, .5, 0, -1., 0, 0], [.5, .5, 0, 1., 0, 0], [1, .0, 0, 0, 0, 0], [.5, .5, 0, -1., 0, 0], [.5, .5, 0, 1., 0, 0], [0, .5, .5, 0, -1., 0], [0, .5, .5, 0, 1., 0], [0, 1., 0, 0, 0, 0],
                      [0, .5, .5, 0, -1., 0], [0, .5, .5, 0, 1., 0], [.5, 0, .5, 0, 0, -1.], [.5, 0, .5, 0, 0, 1.], [0, 0, 1., 0, 0, 0], [.5, 0, .5, 0, 0, -1.], [.5, 0, .5, 0, 0, 1.]])  # design matrix for 15 measurment positions
    elif npos == 6:
        A = np.array([[1., 0, 0, 0, 0, 0], [0, 1., 0, 0, 0, 0], [0, 0, 1., 0, 0, 0], [.5, .5, 0, 1., 0, 0], [
                     0, .5, .5, 0, 1., 0], [.5, 0, .5, 0, 0, 1.]])  # design matrix for 6 measurment positions

    else:
        print("measurement protocol not supported yet ")
        return
    B = np.dot(np.transpose(A), A)
    B = linalg.inv(B)
    B = np.dot(B, np.transpose(A))
    return A, B
#
#


def dok15_s(k15):
    """
    calculates least-squares matrix for 15 measurements from Jelinek [1976]
    """
#
    A, B = design(15)  # get design matrix for 15 measurements
    sbar = np.dot(B, k15)  # get mean s
    t = (sbar[0] + sbar[1] + sbar[2])  # trace
    bulk = old_div(t, 3.)  # bulk susceptibility
    Kbar = np.dot(A, sbar)  # get best fit values for K
    dels = k15 - Kbar  # get deltas
    dels, sbar = old_div(dels, t), old_div(sbar, t)  # normalize by trace
    So = sum(dels**2)
    sigma = np.sqrt(old_div(So, 9.))  # standard deviation
    return sbar, sigma, bulk
#


def cross(v, w):
    """
     cross product of two vectors
    """
    x = v[1] * w[2] - v[2] * w[1]
    y = v[2] * w[0] - v[0] * w[2]
    z = v[0] * w[1] - v[1] * w[0]
    return [x, y, z]
#


def dosgeo(s, az, pl):
    """
    rotates  matrix a to az,pl returns  s
    Parameters
    __________
    s : [x11,x22,x33,x12,x23,x13] - the six tensor elements
    az : the azimuth of the specimen X direction
    pl : the plunge (inclination) of the specimen X direction

    Return
    s_rot : [x11,x22,x33,x12,x23,x13] - after rotation
    """
#
    a = s2a(s)  # convert to 3,3 matrix
#  first get three orthogonal axes
    X1 = dir2cart((az, pl, 1.))
    X2 = dir2cart((az + 90, 0., 1.))
    X3 = cross(X1, X2)
    A = np.transpose([X1, X2, X3])
    b = np.zeros((3, 3,), 'f')  # initiale the b matrix
    for i in range(3):
        for j in range(3):
            dum = 0
            for k in range(3):
                for l in range(3):
                    dum += A[i][k] * A[j][l] * a[k][l]
            b[i][j] = dum
    s_rot = a2s(b)  # afer rotation
    return s_rot
#
#


def dostilt(s, bed_az, bed_dip):
    """
    Rotates "s" tensor to stratigraphic coordinates

    Parameters
    __________
    s : [x11,x22,x33,x12,x23,x13] - the six tensor elements
    bed_az : bedding dip direction
    bed_dip :  bedding dip

    Return
    s_rot : [x11,x22,x33,x12,x23,x13] - after rotation

    """
    tau, Vdirs = doseigs(s)
    Vrot = []
    for evec in Vdirs:
        d, i = dotilt(evec[0], evec[1], bed_az, bed_dip)
        Vrot.append([d, i])
    s_rot = doeigs_s(tau, Vrot)
    return s_rot
#
#


def apseudo(Ss, ipar, sigma):
    """
     draw a bootstrap sample of Ss
    """
#
    Is = random.randint(0, len(Ss) - 1, size=len(Ss))  # draw N random integers
    #Ss = np.array(Ss)
    if ipar == 0:
        BSs = Ss[Is]
    else:  # need to recreate measurement - then do the parametric stuffr
        A, B = design(6)  # get the design matrix for 6 measurementsa
        K, BSs = [], []
        for k in range(len(Ss)):
            K.append(np.dot(A, Ss[k][0:6]))
        Pars = np.random.normal(K, sigma)
        for k in range(len(Ss)):
            BSs.append(np.dot(B, Pars[k]))
    return np.array(BSs)
#


def sbootpars(Taus, Vs):
    """
     get bootstrap parameters for s data
    """
#
    Tau1s, Tau2s, Tau3s = [], [], []
    V1s, V2s, V3s = [], [], []
    nb = len(Taus)
    bpars = {}
    for k in range(nb):
        Tau1s.append(Taus[k][0])
        Tau2s.append(Taus[k][1])
        Tau3s.append(Taus[k][2])
        V1s.append(Vs[k][0])
        V2s.append(Vs[k][1])
        V3s.append(Vs[k][2])
    x, sig = gausspars(Tau1s)
    bpars["t1_sigma"] = sig
    x, sig = gausspars(Tau2s)
    bpars["t2_sigma"] = sig
    x, sig = gausspars(Tau3s)
    bpars["t3_sigma"] = sig
    V1s=flip(V1s,combine=True)
    kpars = dokent(V1s, len(V1s))
    bpars["v1_dec"] = kpars["dec"]
    bpars["v1_inc"] = kpars["inc"]
    bpars["v1_zeta"] = (kpars["Zeta"] * np.sqrt(nb)) % 360.
    bpars["v1_eta"] = (kpars["Eta"] * np.sqrt(nb)) % 360.
    bpars["v1_zeta_dec"] = kpars["Zdec"]
    bpars["v1_zeta_inc"] = kpars["Zinc"]
    bpars["v1_eta_dec"] = kpars["Edec"]
    bpars["v1_eta_inc"] = kpars["Einc"]
    V2s=flip(V2s,combine=True)
    kpars = dokent(V2s, len(V2s))
    bpars["v2_dec"] = kpars["dec"]
    bpars["v2_inc"] = kpars["inc"]
    bpars["v2_zeta"] = (kpars["Zeta"] * np.sqrt(nb)) % 360.
    bpars["v2_eta"] = (kpars["Eta"] * np.sqrt(nb)) % 360.
    bpars["v2_zeta_dec"] = kpars["Zdec"]
    bpars["v2_zeta_inc"] = kpars["Zinc"]
    bpars["v2_eta_dec"] = kpars["Edec"]
    bpars["v2_eta_inc"] = kpars["Einc"]
    V3s=flip(V3s,combine=True)
    kpars = dokent(V3s, len(V3s))
    bpars["v3_dec"] = kpars["dec"]
    bpars["v3_inc"] = kpars["inc"]
    bpars["v3_zeta"] = (kpars["Zeta"] * np.sqrt(nb)) % 360.
    bpars["v3_eta"] = (kpars["Eta"] * np.sqrt(nb)) % 360.
    bpars["v3_zeta_dec"] = kpars["Zdec"]
    bpars["v3_zeta_inc"] = kpars["Zinc"]
    bpars["v3_eta_dec"] = kpars["Edec"]
    bpars["v3_eta_inc"] = kpars["Einc"]
    return bpars
#
#


def s_boot(Ss, ipar=0, nb=1000):
    """
    Returns bootstrap parameters for S data

    Parameters
    __________
    Ss : nested array of [[x11 x22 x33 x12 x23 x13],....] data
    ipar : if True, do a parametric bootstrap
    nb : number of bootstraps

    Returns
    ________
    Tmean : average eigenvalues
    Vmean : average eigvectors
    Taus : bootstrapped eigenvalues
    Vs :  bootstrapped eigenvectors

    """
    #npts = len(Ss)
    Ss = np.array(Ss)
    npts = Ss.shape[0]
# get average s for whole dataset
    nf, Sigma, avs = sbar(Ss)
    Tmean, Vmean = doseigs(avs)  # get eigenvectors of mean tensor
#
# now do bootstrap to collect Vs and taus of bootstrap means
#
    Taus, Vs = [], []  # number of bootstraps, list of bootstrap taus and eigenvectors
#
    for k in range(int(float(nb))):  # repeat nb times
        #        if k%50==0:print k,' out of ',nb
        # get a pseudosample - if ipar=1, do a parametric bootstrap
        BSs = apseudo(Ss, ipar, Sigma)
        nf, sigma, avbs = sbar(BSs)  # get bootstrap mean s
        tau, Vdirs = doseigs(avbs)  # get bootstrap eigenparameters
        Taus.append(tau)
        Vs.append(Vdirs)
    return Tmean, Vmean, Taus, Vs

#


def designAARM(npos):
    #
    """
    calculates B matrix for AARM calculations.
    """
    if npos != 9:
        print('Sorry - only 9 positions available')
        return
    Dec = [315., 225., 180., 135., 45., 90., 270.,
           270., 270., 90., 0., 0., 0., 180., 180.]
    Dip = [0., 0., 0., 0., 0., -45., -45., 0.,
           45., 45., 45., -45., -90., -45., 45.]
    index9 = [0, 1, 2, 5, 6, 7, 10, 11, 12]
    H = []
    for ind in range(15):
        Dir = [Dec[ind], Dip[ind], 1.]
        H.append(dir2cart(Dir))  # 15 field directionss
#
# make design matrix A
#
    A = np.zeros((npos * 3, 6), 'f')
    tmpH = np.zeros((npos, 3), 'f')  # define tmpH
    if npos == 9:
        for i in range(9):
            k = index9[i]
            ind = i * 3
            A[ind][0] = H[k][0]
            A[ind][3] = H[k][1]
            A[ind][5] = H[k][2]
            ind = i * 3 + 1
            A[ind][3] = H[k][0]
            A[ind][1] = H[k][1]
            A[ind][4] = H[k][2]
            ind = i * 3 + 2
            A[ind][5] = H[k][0]
            A[ind][4] = H[k][1]
            A[ind][2] = H[k][2]
            for j in range(3):
                tmpH[i][j] = H[k][j]
        At = np.transpose(A)
        ATA = np.dot(At, A)
        ATAI = linalg.inv(ATA)
        B = np.dot(ATAI, At)
    else:
        print("B matrix not yet supported")
        return
    return B, H, tmpH
#


def designATRM(npos):
    #
    """
    calculates B matrix for ATRM calculations.
    """
    # if npos!=6:
    #    print 'Sorry - only 6 positions available'
    Dec = [0, 0,  0, 90, 180, 270, 0]  # for shuhui only
    Dip = [90, -90, 0, 0, 0, 0, 90]
    Dec = [0, 90, 0, 180, 270, 0, 0, 90, 0]
    Dip = [0, 0, 90, 0, 0, -90, 0, 0, 90]
    H = []
    for ind in range(6):
        Dir = [Dec[ind], Dip[ind], 1.]
        H.append(dir2cart(Dir))  # 6 field directionss
#
# make design matrix A
#
    A = np.zeros((npos * 3, 6), 'f')
    tmpH = np.zeros((npos, 3), 'f')  # define tmpH
    # if npos == 6:
    #    for i in range(6):
    for i in range(6):
        ind = i * 3
        A[ind][0] = H[i][0]
        A[ind][3] = H[i][1]
        A[ind][5] = H[i][2]
        ind = i * 3 + 1
        A[ind][3] = H[i][0]
        A[ind][1] = H[i][1]
        A[ind][4] = H[i][2]
        ind = i * 3 + 2
        A[ind][5] = H[i][0]
        A[ind][4] = H[i][1]
        A[ind][2] = H[i][2]
        for j in range(3):
            tmpH[i][j] = H[i][j]
    At = np.transpose(A)
    ATA = np.dot(At, A)
    ATAI = linalg.inv(ATA)
    B = np.dot(ATAI, At)
    # else:
    #    print "B matrix not yet supported"
    return B, H, tmpH

#


def domagicmag(file, Recs):
    """
    converts a magic record back into the SIO mag format
    """
    for rec in Recs:
        type = ".0"
        meths = []
        tmp = rec["magic_method_codes"].split(':')
        for meth in tmp:
            meths.append(meth.strip())
        if 'LT-T-I' in meths:
            type = ".1"
        if 'LT-PTRM-I' in meths:
            type = ".2"
        if 'LT-PTRM-MD' in meths:
            type = ".3"
        treatment = float(rec["treatment_temp"]) - 273
        tr = '%i' % (treatment) + type
        inten = '%8.7e ' % (float(rec["measurement_magn_moment"]) * 1e3)
        outstring = rec["er_specimen_name"] + " " + tr + " " + rec["measurement_csd"] + \
            " " + inten + " " + rec["measurement_dec"] + \
            " " + rec["measurement_inc"] + "\n"
        file.write(outstring)
#
#


def cleanup(first_I, first_Z):
    """
     cleans up unbalanced steps
     failure can be from unbalanced final step, or from missing steps,
     this takes care of  missing steps
    """
    cont = 0
    Nmin = len(first_I)
    if len(first_Z) < Nmin:
        Nmin = len(first_Z)
    for kk in range(Nmin):
        if first_I[kk][0] != first_Z[kk][0]:
            print("\n WARNING: ")
            if first_I[kk] < first_Z[kk]:
                del first_I[kk]
            else:
                del first_Z[kk]
            print("Unmatched step number: ", kk + 1, '  ignored')
            cont = 1
        if cont == 1:
            return first_I, first_Z, cont
    return first_I, first_Z, cont
#
#


def sortarai(datablock, s, Zdiff, **kwargs):
    """
     sorts data block in to first_Z, first_I, etc.

    Parameters
    _________
    datablock : Pandas DataFrame with Thellier-Tellier type data
    s : specimen name
    Zdiff : if True, take difference in Z values instead of vector difference
            NB:  this should always be False
    **kwargs :
        version : data model.  if not 3, assume data model = 2.5

    Returns
    _______
    araiblock : [first_Z, first_I, ptrm_check,
                 ptrm_tail, zptrm_check, GammaChecks]
    field : lab field (in tesla)
    """
    if 'version' in list(kwargs.keys()) and kwargs['version'] == 3:
        dec_key, inc_key = 'dir_dec', 'dir_inc'
        Mkeys = ['magn_moment', 'magn_volume', 'magn_mass', 'magnitude']
        meth_key = 'method_codes'
        temp_key, dc_key = 'treat_temp', 'treat_dc_field'
        dc_theta_key, dc_phi_key = 'treat_dc_field_theta', 'treat_dc_field_phi'
        # convert dataframe to list of dictionaries
        datablock = datablock.to_dict('records')
    else:
        dec_key, inc_key = 'measurement_dec', 'measurement_inc'
        Mkeys = ['measurement_magn_moment', 'measurement_magn_volume',
                 'measurement_magn_mass', 'measurement_magnitude']
        meth_key = 'magic_method_codes'
        temp_key, dc_key = 'treatment_temp', 'treatment_dc_field'
        dc_theta_key, dc_phi_key = 'treatment_dc_field_theta', 'treatment_dc_field_phi'
    first_Z, first_I, zptrm_check, ptrm_check, ptrm_tail = [], [], [], [], []
    field, phi, theta = "", "", ""
    starthere = 0
    Treat_I, Treat_Z, Treat_PZ, Treat_PI, Treat_M = [], [], [], [], []
    ISteps, ZSteps, PISteps, PZSteps, MSteps = [], [], [], [], []
    GammaChecks = []  # comparison of pTRM direction acquired and lab field
    rec = datablock[0]
    for key in Mkeys:
        if key in list(rec.keys()) and rec[key] != "":
            momkey = key
            break
# first find all the steps
    for k in range(len(datablock)):
        rec = datablock[k]
        temp = float(rec[temp_key])
        methcodes = []
        tmp = rec[meth_key].split(":")
        for meth in tmp:
            methcodes.append(meth.strip())
        if 'LT-T-I' in methcodes and 'LP-TRM' not in methcodes and 'LP-PI-TRM' in methcodes:
            Treat_I.append(temp)
            ISteps.append(k)
            if field == "":
                field = float(rec[dc_key])
            if phi == "":
                phi = float(rec[dc_phi_key])
                theta = float(rec[dc_theta_key])
# stick  first zero field stuff into first_Z
        if 'LT-NO' in methcodes:
            Treat_Z.append(temp)
            ZSteps.append(k)
        if 'LT-T-Z' in methcodes:
            Treat_Z.append(temp)
            ZSteps.append(k)
        if 'LT-PTRM-Z' in methcodes:
            Treat_PZ.append(temp)
            PZSteps.append(k)
        if 'LT-PTRM-I' in methcodes:
            Treat_PI.append(temp)
            PISteps.append(k)
        if 'LT-PTRM-MD' in methcodes:
            Treat_M.append(temp)
            MSteps.append(k)
        if 'LT-NO' in methcodes:
            dec = float(rec[dec_key])
            inc = float(rec[inc_key])
            str = float(rec[momkey])
            first_I.append([273, 0., 0., 0., 1])
            first_Z.append([273, dec, inc, str, 1])  # NRM step
    for temp in Treat_I:  # look through infield steps and find matching Z step
        if temp in Treat_Z:  # found a match
            istep = ISteps[Treat_I.index(temp)]
            irec = datablock[istep]
            methcodes = []
            tmp = irec[meth_key].split(":")
            for meth in tmp:
                methcodes.append(meth.strip())
            # take last record as baseline to subtract
            brec = datablock[istep - 1]
            zstep = ZSteps[Treat_Z.index(temp)]
            zrec = datablock[zstep]
    # sort out first_Z records
            if "LP-PI-TRM-IZ" in methcodes:
                ZI = 0
            else:
                ZI = 1
            dec = float(zrec[dec_key])
            inc = float(zrec[inc_key])
            str = float(zrec[momkey])
            first_Z.append([temp, dec, inc, str, ZI])
    # sort out first_I records
            idec = float(irec[dec_key])
            iinc = float(irec[inc_key])
            istr = float(irec[momkey])
            X = dir2cart([idec, iinc, istr])
            BL = dir2cart([dec, inc, str])
            I = []
            for c in range(3):
                I.append((X[c] - BL[c]))
            if I[2] != 0:
                iDir = cart2dir(I)
                if Zdiff == 0:
                    first_I.append([temp, iDir[0], iDir[1], iDir[2], ZI])
                else:
                    first_I.append([temp, 0., 0., I[2], ZI])
                gamma = angle([iDir[0], iDir[1]], [phi, theta])
            else:
                first_I.append([temp, 0., 0., 0., ZI])
                gamma = 0.0
# put in Gamma check (infield trm versus lab field)
            if 180. - gamma < gamma:
                gamma = 180. - gamma
            GammaChecks.append([temp - 273., gamma])
    for temp in Treat_PI:  # look through infield steps and find matching Z step
        step = PISteps[Treat_PI.index(temp)]
        rec = datablock[step]
        dec = float(rec[dec_key])
        inc = float(rec[inc_key])
        str = float(rec[momkey])
        brec = datablock[step - 1]  # take last record as baseline to subtract
        pdec = float(brec[dec_key])
        pinc = float(brec[inc_key])
        pint = float(brec[momkey])
        X = dir2cart([dec, inc, str])
        prevX = dir2cart([pdec, pinc, pint])
        I = []
        for c in range(3):
            I.append(X[c] - prevX[c])
        dir1 = cart2dir(I)
        if Zdiff == 0:
            ptrm_check.append([temp, dir1[0], dir1[1], dir1[2]])
        else:
            ptrm_check.append([temp, 0., 0., I[2]])
# in case there are zero-field pTRM checks (not the SIO way)
    for temp in Treat_PZ:
        step = PZSteps[Treat_PZ.index(temp)]
        rec = datablock[step]
        dec = float(rec[dec_key])
        inc = float(rec[inc_key])
        str = float(rec[momkey])
        brec = datablock[step - 1]
        pdec = float(brec[dec_key])
        pinc = float(brec[inc_key])
        pint = float(brec[momkey])
        X = dir2cart([dec, inc, str])
        prevX = dir2cart([pdec, pinc, pint])
        I = []
        for c in range(3):
            I.append(X[c] - prevX[c])
        dir2 = cart2dir(I)
        zptrm_check.append([temp, dir2[0], dir2[1], dir2[2]])
    # get pTRM tail checks together -
    for temp in Treat_M:
        # tail check step - just do a difference in magnitude!
        step = MSteps[Treat_M.index(temp)]
        rec = datablock[step]
        str = float(rec[momkey])
        if temp in Treat_Z:
            step = ZSteps[Treat_Z.index(temp)]
            brec = datablock[step]
            pint = float(brec[momkey])
#        X=dir2cart([dec,inc,str])
#        prevX=dir2cart([pdec,pinc,pint])
#        I=[]
#        for c in range(3):I.append(X[c]-prevX[c])
#        d=cart2dir(I)
#        ptrm_tail.append([temp,d[0],d[1],d[2]])
            # difference - if negative, negative tail!
            ptrm_tail.append([temp, 0, 0, str - pint])
        else:
            print(
                s, '  has a tail check with no first zero field step - check input file! for step', temp - 273.)
#
# final check
#
    if len(first_Z) != len(first_I):
        print(len(first_Z), len(first_I))
        print(" Something wrong with this specimen! Better fix it or delete it ")
        input(" press return to acknowledge message")
    araiblock = (first_Z, first_I, ptrm_check,
                 ptrm_tail, zptrm_check, GammaChecks)
    return araiblock, field


def sortmwarai(datablock, exp_type):
    """
     sorts microwave double heating data block in to first_Z, first_I, etc.
    """
    first_Z, first_I, ptrm_check, ptrm_tail, zptrm_check = [], [], [], [], []
    field, phi, theta = "", "", ""
    POWT_I, POWT_Z, POWT_PZ, POWT_PI, POWT_M = [], [], [], [], []
    ISteps, ZSteps, PZSteps, PISteps, MSteps = [], [], [], [], []
    rad = old_div(np.pi, 180.)
    ThetaChecks = []
    DeltaChecks = []
    GammaChecks = []
# first find all the steps
    for k in range(len(datablock)):
        rec = datablock[k]
        powt = int(float(rec["treatment_mw_energy"]))
        methcodes = []
        tmp = rec["magic_method_codes"].split(":")
        for meth in tmp:
            methcodes.append(meth.strip())
        if 'LT-M-I' in methcodes and 'LP-MRM' not in methcodes:
            POWT_I.append(powt)
            ISteps.append(k)
            if field == "":
                field = float(rec['treatment_dc_field'])
            if phi == "":
                phi = float(rec['treatment_dc_field_phi'])
                theta = float(rec['treatment_dc_field_theta'])
        if 'LT-M-Z' in methcodes:
            POWT_Z.append(powt)
            ZSteps.append(k)
        if 'LT-PMRM-Z' in methcodes:
            POWT_PZ.append(powt)
            PZSteps.append(k)
        if 'LT-PMRM-I' in methcodes:
            POWT_PI.append(powt)
            PISteps.append(k)
        if 'LT-PMRM-MD' in methcodes:
            POWT_M.append(powt)
            MSteps.append(k)
        if 'LT-NO' in methcodes:
            dec = float(rec["measurement_dec"])
            inc = float(rec["measurement_inc"])
            str = float(rec["measurement_magn_moment"])
            first_I.append([0, 0., 0., 0., 1])
            first_Z.append([0, dec, inc, str, 1])  # NRM step
    if exp_type == "LP-PI-M-D":
        # now look trough infield steps and  find matching Z step
        for powt in POWT_I:
            if powt in POWT_Z:
                istep = ISteps[POWT_I.index(powt)]
                irec = datablock[istep]
                methcodes = []
                tmp = irec["magic_method_codes"].split(":")
                for meth in tmp:
                    methcodes.append(meth.strip())
                # take last record as baseline to subtract
                brec = datablock[istep - 1]
                zstep = ZSteps[POWT_Z.index(powt)]
                zrec = datablock[zstep]
    # sort out first_Z records
                if "LP-PI-M-IZ" in methcodes:
                    ZI = 0
                else:
                    ZI = 1
                dec = float(zrec["measurement_dec"])
                inc = float(zrec["measurement_inc"])
                str = float(zrec["measurement_magn_moment"])
                first_Z.append([powt, dec, inc, str, ZI])
    # sort out first_I records
                idec = float(irec["measurement_dec"])
                iinc = float(irec["measurement_inc"])
                istr = float(irec["measurement_magn_moment"])
                X = dir2cart([idec, iinc, istr])
                BL = dir2cart([dec, inc, str])
                I = []
                for c in range(3):
                    I.append((X[c] - BL[c]))
                iDir = cart2dir(I)
                first_I.append([powt, iDir[0], iDir[1], iDir[2], ZI])
# put in Gamma check (infield trm versus lab field)
                gamma = angle([iDir[0], iDir[1]], [phi, theta])
                GammaChecks.append([powt, gamma])
    elif exp_type == "LP-PI-M-S":
        # find last zero field step before first infield step
        lzrec = datablock[ISteps[0] - 1]
        irec = datablock[ISteps[0]]
        ndec = float(lzrec["measurement_dec"])
        ninc = float(lzrec["measurement_inc"])
        nstr = float(lzrec["measurement_magn_moment"])
        NRM = dir2cart([ndec, ninc, nstr])
        fdec = float(irec["treatment_dc_field_phi"])
        finc = float(irec["treatment_dc_field_theta"])
        Flab = dir2cart([fdec, finc, 1.])
        for step in ISteps:
            irec = datablock[step]
            rdec = float(irec["measurement_dec"])
            rinc = float(irec["measurement_inc"])
            rstr = float(irec["measurement_magn_moment"])
            theta1 = angle([ndec, ninc], [rdec, rinc])
            theta2 = angle([rdec, rinc], [fdec, finc])
            powt = int(float(irec["treatment_mw_energy"]))
            ThetaChecks.append([powt, theta1 + theta2])
            p = (180. - (theta1 + theta2))
            nstr = rstr * (old_div(np.sin(theta2 * rad), np.sin(p * rad)))
            tmstr = rstr * (old_div(np.sin(theta1 * rad), np.sin(p * rad)))
            first_Z.append([powt, ndec, ninc, nstr, 1])
            first_I.append([powt, dec, inc, tmstr, 1])
# check if zero field steps are parallel to assumed NRM
        for step in ZSteps:
            zrec = datablock[step]
            powt = int(float(zrec["treatment_mw_energy"]))
            zdec = float(zrec["measurement_dec"])
            zinc = float(zrec["measurement_inc"])
            delta = angle([ndec, ninc], [zdec, zinc])
            DeltaChecks.append([powt, delta])
    # get pTRMs together - take previous record and subtract
    for powt in POWT_PI:
        step = PISteps[POWT_PI.index(powt)]
        rec = datablock[step]
        dec = float(rec["measurement_dec"])
        inc = float(rec["measurement_inc"])
        str = float(rec["measurement_magn_moment"])
        brec = datablock[step - 1]  # take last record as baseline to subtract
        pdec = float(brec["measurement_dec"])
        pinc = float(brec["measurement_inc"])
        pint = float(brec["measurement_magn_moment"])
        X = dir2cart([dec, inc, str])
        prevX = dir2cart([pdec, pinc, pint])
        I = []
        for c in range(3):
            I.append(X[c] - prevX[c])
        dir1 = cart2dir(I)
        ptrm_check.append([powt, dir1[0], dir1[1], dir1[2]])
    # get zero field pTRM  checks together
    for powt in POWT_PZ:
        step = PZSteps[POWT_PZ.index(powt)]
        rec = datablock[step]
        dec = float(rec["measurement_dec"])
        inc = float(rec["measurement_inc"])
        str = float(rec["measurement_magn_moment"])
        brec = datablock[step - 1]
        pdec = float(brec["measurement_dec"])
        pinc = float(brec["measurement_inc"])
        pint = float(brec["measurement_magn_moment"])
        X = dir2cart([dec, inc, str])
        prevX = dir2cart([pdec, pinc, pint])
        I = []
        for c in range(3):
            I.append(X[c] - prevX[c])
        dir2 = cart2dir(I)
        zptrm_check.append([powt, dir2[0], dir2[1], dir2[2]])
    # get pTRM tail checks together -
    for powt in POWT_M:
        step = MSteps[POWT_M.index(powt)]  # tail check step
        rec = datablock[step]
#        dec=float(rec["measurement_dec"])
#        inc=float(rec["measurement_inc"])
        str = float(rec["measurement_magn_moment"])
        step = ZSteps[POWT_Z.index(powt)]
        brec = datablock[step]
#        pdec=float(brec["measurement_dec"])
#        pinc=float(brec["measurement_inc"])
        pint = float(brec["measurement_magn_moment"])
#        X=dir2cart([dec,inc,str])
#        prevX=dir2cart([pdec,pinc,pint])
#        I=[]
#        for c in range(3):I.append(X[c]-prevX[c])
#        d=cart2dir(I)
 #       ptrm_tail.append([powt,d[0],d[1],d[2]])
        # just do absolute magnitude difference # not vector diff
        ptrm_tail.append([powt, 0, 0, str - pint])
    #  check
    #
        if len(first_Z) != len(first_I):
            print(len(first_Z), len(first_I))
            print(" Something wrong with this specimen! Better fix it or delete it ")
            input(" press return to acknowledge message")
            print(MaxRec)
    araiblock = (first_Z, first_I, ptrm_check, ptrm_tail,
                 zptrm_check, GammaChecks, ThetaChecks, DeltaChecks)
    return araiblock, field

    #


def docustom(lon, lat, alt, gh):
    """
    Passes the coefficients to the Malin and Barraclough
    routine (function pmag.magsyn) to calculate the field from the coefficients.

    Parameters:
    -----------
    lon  = east longitude in degrees (0 to 360 or -180 to 180)
    lat   = latitude in degrees (-90 to 90)
    alt   = height above mean sea level in km (itype = 1 assumed)
    """
    model, date, itype = 0, 0, 1
    sv = np.zeros(len(gh))
    colat = 90. - lat
    x, y, z, f = magsyn(gh, sv, model, date, itype, alt, colat, lon)
    return x, y, z, f


def doigrf(lon, lat, alt, date, **kwargs):
    """
    Calculates the interpolated (<2015) or extrapolated (>2015) main field and
    secular variation coefficients and passes them to the Malin and Barraclough
    routine (function pmag.magsyn) to calculate the field from the coefficients.

    Parameters:
    -----------
    lon  : east longitude in degrees (0 to 360 or -180 to 180)
    lat   : latitude in degrees (-90 to 90)
    alt   : height above mean sea level in km (itype = 1 assumed)
    date  : Required date in years and decimals of a year (A.D.)

    Optional Parameters:
    -----------
    coeffs : if True, then return the gh coefficients
    mod  : model to use ('arch3k','cals3k','pfm9k','hfm10k','cals10k.2','cals10k.1b','shadif14k')
        arch3k (Korte et al., 2009)
        cals3k (Korte and Constable, 2011)
        cals10k.1b (Korte et al., 2011)
        pfm9k  (Nilsson et al., 2014)
        hfm.OL1.A1 (Constable et al., 2016)
        cals10k.2 (Constable et al., 2016)
        shadif14k (Pavon-Carrasco et al. (2014)
          NB : the first four of these models, are constrained to agree
               with gufm1 (Jackson et al., 2000) for the past four centuries
    Return
    -----------
    x : north component of the magnetic field in nT
    y : east component of the magnetic field in nT
    z : downward component of the magnetic field in nT
    f : total magnetic field in nT

    By default, igrf12 coefficients are used between 1900 and 2020
    from http://www.ngdc.noaa.gov/IAGA/vmod/igrf.html.


    To check the results you can run the interactive program at the NGDC
    www.ngdc.noaa.gov/geomag-web
    """
    from . import coefficients as cf
    gh, sv = [], []
    colat = 90. - lat
#! convert to colatitude for MB routine
    if lon < 0:
        lon = lon + 360.
# ensure all positive east longitudes
    itype = 1
    models, igrf12coeffs = cf.get_igrf12()
    if 'mod' in list(kwargs.keys()):
        if kwargs['mod'] == 'arch3k':
            psvmodels, psvcoeffs = cf.get_arch3k()  # use ARCH3k coefficients
        elif kwargs['mod'] == 'cals3k':
            # use CALS3K_4b coefficients between -1000,1940
            psvmodels, psvcoeffs = cf.get_cals3k()
        elif kwargs['mod'] == 'pfm9k':
            # use PFM9k (Nilsson et al., 2014), coefficients from -7000 to 1900
            psvmodels, psvcoeffs = cf.get_pfm9k()
        elif kwargs['mod'] == 'hfm10k':
            # use HFM.OL1.A1 (Constable et al., 2016), coefficients from -8000
            # to 1900
            psvmodels, psvcoeffs = cf.get_hfm10k()
        elif kwargs['mod'] == 'cals10k.2':
            # use CALS10k.2 (Constable et al., 2016), coefficients from -8000
            # to 1900
            psvmodels, psvcoeffs = cf.get_cals10k_2()
        elif kwargs['mod'] == 'shadif14k':
            # use CALS10k.2 (Constable et al., 2016), coefficients from -8000
            # to 1900
            psvmodels, psvcoeffs = cf.get_shadif14k()
        else:
            # Korte and Constable, 2011;  use prior to -1000, back to -8000
            psvmodels, psvcoeffs = cf.get_cals10k()
# use geodetic coordinates
    if 'models' in kwargs:
        if 'mod' in list(kwargs.keys()):
            return psvmodels, psvcoeffs
        else:
            return models, igrf12coeffs
    if date < -12000:
        print('too old')
        return
    if 'mod' in list(kwargs.keys()) and kwargs['mod'] == 'shadif14k':
        if date < -10000:
            incr = 100
        else:
            incr = 50
        model = date - date % incr
        gh = psvcoeffs[psvmodels.index(int(model))]
        sv = old_div(
            (psvcoeffs[psvmodels.index(int(model + incr))] - gh), float(incr))
        x, y, z, f = magsyn(gh, sv, model, date, itype, alt, colat, lon)
    elif date < -1000:
        incr = 10
        model = date - date % incr
        gh = psvcoeffs[psvmodels.index(int(model))]
        sv = old_div(
            (psvcoeffs[psvmodels.index(int(model + incr))] - gh), float(incr))
        x, y, z, f = magsyn(gh, sv, model, date, itype, alt, colat, lon)
    elif date < 1900:
        if kwargs['mod'] == 'cals10k':
            incr = 50
        else:
            incr = 10
        model = date - date % incr
        gh = psvcoeffs[psvmodels.index(model)]
        if model + incr < 1900:
            sv = old_div(
                (psvcoeffs[psvmodels.index(model + incr)] - gh), float(incr))
        else:
            field2 = igrf12coeffs[models.index(1940)][0:120]
            sv = old_div((field2 - gh), float(1940 - model))
        x, y, z, f = magsyn(gh, sv, model, date, itype, alt, colat, lon)
    else:
        model = date - date % 5
        if date < 2015:
            gh = igrf12coeffs[models.index(model)]
            sv = old_div((igrf12coeffs[models.index(model + 5)] - gh), 5.)
            x, y, z, f = magsyn(gh, sv, model, date, itype, alt, colat, lon)
        else:
            gh = igrf12coeffs[models.index(2015)]
            sv = igrf12coeffs[models.index(2015.20)]
            x, y, z, f = magsyn(gh, sv, model, date, itype, alt, colat, lon)
    if 'coeffs' in list(kwargs.keys()):
        return gh
    else:
        return x, y, z, f
#


def unpack(gh):
    """
    unpacks gh list into l m g h type list

    Parameters
    _________
    gh : list of gauss coefficients (as returned by, e.g., doigrf)

    Returns
   data : nested list of [[l,m,g,h],...]

    """
    data = []
    k, l = 0, 1
    while k + 1 < len(gh):
        for m in range(l + 1):
            if m == 0:
                data.append([l, m, gh[k], 0])
                k += 1
            else:
                data.append([l, m, gh[k], gh[k + 1]])
                k += 2
        l += 1
    return data


def magsyn(gh, sv, b, date, itype, alt, colat, elong):
    """
# Computes x, y, z, and f for a given date and position, from the
# spherical harmonic coefficients of the International Geomagnetic
# Reference Field (IGRF).
# From Malin and Barraclough (1981), Computers and Geosciences, V.7, 401-405.
#
# Input:
#       date  = Required date in years and decimals of a year (A.D.)
#       itype = 1, if geodetic coordinates are used, 2 if geocentric
#       alt   = height above mean sea level in km (if itype = 1)
#       alt   = radial distance from the center of the earth (itype = 2)
#       colat = colatitude in degrees (0 to 180)
#       elong = east longitude in degrees (0 to 360)
#               gh        = main field values for date (calc. in igrf subroutine)
#               sv        = secular variation coefficients (calc. in igrf subroutine)
#               begin = date of dgrf (or igrf) field prior to required date
#
# Output:
#       x     - north component of the magnetic force in nT
#       y     - east component of the magnetic force in nT
#       z     - downward component of the magnetic force in nT
#       f     - total magnetic force in nT
#
#       NB: the coordinate system for x,y, and z is the same as that specified
#       by itype.
#
# Modified 4/9/97 to use DGRFs from 1945 to 1990 IGRF
# Modified 10/13/06 to use  1995 DGRF, 2005 IGRF and sv coefficient
# for extrapolation beyond 2005. Coefficients from Barton et al. PEPI, 97: 23-26
# (1996), via web site for NOAA, World Data Center A. Modified to use
#degree and
# order 10 as per notes in Malin and Barraclough (1981).
# coefficients for DGRF 1995 and IGRF 2005 are from http://nssdcftp.gsfc.nasa.gov/models/geomagnetic/igrf/fortran_code/
# igrf subroutine calculates
# the proper main field and secular variation coefficients (interpolated between
# dgrf values or extrapolated from 1995 sv values as appropriate).
    """
#
#       real gh(120),sv(120),p(66),q(66),cl(10),sl(10)
#               real begin,dateq
    p = np.zeros((66), 'f')
    q = np.zeros((66), 'f')
    cl = np.zeros((10), 'f')
    sl = np.zeros((10), 'f')
    begin = b
    t = date - begin
    r = alt
    one = colat * 0.0174532925
    ct = np.cos(one)
    st = np.sin(one)
    one = elong * 0.0174532925
    cl[0] = np.cos(one)
    sl[0] = np.sin(one)
    x, y, z = 0.0, 0.0, 0.0
    cd, sd = 1.0, 0.0
    l, ll, m, n = 1, 0, 1, 0
    if itype != 2:
        #
        # if required, convert from geodectic to geocentric
        a2 = 40680925.0
        b2 = 40408585.0
        one = a2 * st * st
        two = b2 * ct * ct
        three = one + two
        rho = np.sqrt(three)
        r = np.sqrt(alt * (alt + 2.0 * rho) +
                    old_div((a2 * one + b2 * two), three))
        cd = old_div((alt + rho), r)
        sd = (a2 - b2) / rho * ct * st / r
        one = ct
        ct = ct * cd - st * sd
        st = st * cd + one * sd
    ratio = old_div(6371.2, r)
    rr = ratio * ratio
#
# compute Schmidt quasi-normal coefficients p and x(=q)
    p[0] = 1.0
    p[2] = st
    q[0] = 0.0
    q[2] = ct
    for k in range(1, 66):
        if n < m:   # else go to 2
            m = 0
            n = n + 1
            rr = rr * ratio
            fn = n
            gn = n - 1
# 2
        fm = m
        if k != 2:  # else go to 4
            if m == n:   # else go to 3
                one = np.sqrt(1.0 - old_div(0.5, fm))
                j = k - n - 1
                p[k] = one * st * p[j]
                q[k] = one * (st * q[j] + ct * p[j])
                cl[m - 1] = cl[m - 2] * cl[0] - sl[m - 2] * sl[0]
                sl[m - 1] = sl[m - 2] * cl[0] + cl[m - 2] * sl[0]
            else:
                # 3
                gm = m * m
                one = np.sqrt(fn * fn - gm)
                two = old_div(np.sqrt(gn * gn - gm), one)
                three = old_div((fn + gn), one)
                i = k - n
                j = i - n + 1
                p[k] = three * ct * p[i] - two * p[j]
                q[k] = three * (ct * q[i] - st * p[i]) - two * q[j]
#
# synthesize x, y, and z in geocentric coordinates.
# 4
        #print (l,ll,t,rr)
        one = (gh[l - 1] + sv[ll + l - 1] * t) * rr
        if m != 0:  # else go to 7
            two = (gh[l] + sv[ll + l] * t) * rr
            three = one * cl[m - 1] + two * sl[m - 1]
            x = x + three * q[k]
            z = z - (fn + 1.0) * three * p[k]
            if st != 0.0:  # else go to 5
                y = y + (one * sl[m - 1] - two * cl[m - 1]) * fm * p[k] / st
            else:
                # 5
                y = y + (one * sl[m - 1] - two * cl[m - 1]) * q[k] * ct
            l = l + 2
        else:
            # 7
            x = x + one * q[k]
            z = z - (fn + 1.0) * one * p[k]
            l = l + 1
        m = m + 1
#
# convert to coordinate system specified by itype
    one = x
    x = x * cd + z * sd
    z = z * cd - one * sd
    f = np.sqrt(x * x + y * y + z * z)
#
    return x, y, z, f
#
#


def measurements_methods(meas_data, noave):
    """
    get list of unique specs
    """
#
    version_num = get_version()
    sids = get_specs(meas_data)
# list  of measurement records for this specimen
#
# step through spec by spec
#
    SpecTmps, SpecOuts = [], []
    for spec in sids:
        TRM, IRM3D, ATRM, CR = 0, 0, 0, 0
        expcodes = ""
# first collect all data for this specimen and do lab treatments
        # list  of measurement records for this specimen
        SpecRecs = get_dictitem(meas_data, 'er_specimen_name', spec, 'T')
        for rec in SpecRecs:
            if 'measurement_flag' not in list(rec.keys()):
                rec['measurement_flag'] = 'g'
            tmpmeths = rec['magic_method_codes'].split(":")
            meths = []
            if "LP-TRM" in tmpmeths:
                TRM = 1  # catch these suckers here!
            if "LP-IRM-3D" in tmpmeths:
                IRM3D = 1  # catch these suckers here!
            elif "LP-AN-TRM" in tmpmeths:
                ATRM = 1  # catch these suckers here!
            elif "LP-CR-TRM" in tmpmeths:
                CR = 1  # catch these suckers here!
#
# otherwise write over existing method codes
#
# find NRM data (LT-NO)
#
            elif float(rec["measurement_temp"]) >= 273. and float(rec["measurement_temp"]) < 323.:
                # between 0 and 50C is room T measurement
                if ("measurement_dc_field" not in list(rec.keys()) or float(rec["measurement_dc_field"]) == 0 or rec["measurement_dc_field"] == "") and ("measurement_ac_field" not in list(rec.keys()) or float(rec["measurement_ac_field"]) == 0 or rec["measurement_ac_field"] == ""):
                    # measurement done in zero field!
                    if "treatment_temp" not in list(rec.keys()) or rec["treatment_temp"].strip() == "" or (float(rec["treatment_temp"]) >= 273. and float(rec["treatment_temp"]) < 298.):
                        # between 0 and 50C is room T treatment
                        if "treatment_ac_field" not in list(rec.keys()) or rec["treatment_ac_field"] == "" or float(rec["treatment_ac_field"]) == 0:
                            # no AF
                            # no IRM!
                            if "treatment_dc_field" not in list(rec.keys()) or rec["treatment_dc_field"] == "" or float(rec["treatment_dc_field"]) == 0:
                                if "LT-NO" not in meths:
                                    meths.append("LT-NO")
                            elif "LT-IRM" not in meths:
                                meths.append("LT-IRM")  # it's an IRM
#
# find AF/infield/zerofield
#
                        # no ARM
                        elif "treatment_dc_field" not in list(rec.keys()) or rec["treatment_dc_field"] == "" or float(rec["treatment_dc_field"]) == 0:
                            if "LT-AF-Z" not in meths:
                                meths.append("LT-AF-Z")
                        else:  # yes ARM
                            if "LT-AF-I" not in meths:
                                meths.append("LT-AF-I")
#
# find Thermal/infield/zerofield
#
                    elif float(rec["treatment_temp"]) >= 323:  # treatment done at  high T
                        if TRM == 1:
                            if "LT-T-I" not in meths:
                                # TRM - even if zero applied field!
                                meths.append("LT-T-I")
                        # no TRM
                        elif "treatment_dc_field" not in list(rec.keys()) or rec["treatment_dc_field"] == "" or float(rec["treatment_dc_field"]) == 0.:
                            if "LT-T-Z" not in meths:
                                # don't overwrite if part of a TRM experiment!
                                meths.append("LT-T-Z")
                        else:  # yes TRM
                            if "LT-T-I" not in meths:
                                meths.append("LT-T-I")
#
# find low-T infield,zero field
#
                    else:  # treatment done at low T
                        # no field
                        if "treatment_dc_field" not in list(rec.keys()) or rec["treatment_dc_field"] == "" or float(rec["treatment_dc_field"]) == 0:
                            if "LT-LT-Z" not in meths:
                                meths.append("LT-LT-Z")
                        else:  # yes field
                            if "LT-LT-I" not in meths:
                                meths.append("LT-LT-I")
                if "measurement_chi_volume" in list(rec.keys()) or "measurement_chi_mass" in list(rec.keys()):
                    if "LP-X" not in meths:
                        meths.append("LP-X")
                # measurement in presence of dc field and not susceptibility;
                # hysteresis!
                elif "measurement_lab_dc_field" in list(rec.keys()) and rec["measurement_lab_dc_field"] != 0:
                    if "LP-HYS" not in meths:
                        hysq = input("Is this a hysteresis experiment? [1]/0")
                        if hysq == "" or hysq == "1":
                            meths.append("LP-HYS")
                        else:
                            metha = input(
                                "Enter the lab protocol code that best describes this experiment ")
                            meths.append(metha)
                methcode = ""
                for meth in meths:
                    methcode = methcode + meth.strip() + ":"
                rec["magic_method_codes"] = methcode[:-1]  # assign them back
#
# done with first pass, collect and assign provisional method codes
            if "measurement_description" not in list(rec.keys()):
                rec["measurement_description"] = ""
            rec["er_citation_names"] = "This study"
            SpecTmps.append(rec)
# ready for second pass through, step through specimens, check whether ptrm, ptrm tail checks, or AARM, etc.
#
    for spec in sids:
        MD, pTRM, IZ, ZI = 0, 0, 0, 0  # these are flags for the lab protocol codes
        expcodes = ""
        NewSpecs, SpecMeths = [], []
        experiment_name, measnum = "", 1
        if IRM3D == 1:
            experiment_name = "LP-IRM-3D"
        if ATRM == 1:
            experiment_name = "LP-AN-TRM"
        if CR == 1:
            experiment_name = "LP-CR"
        NewSpecs = get_dictitem(SpecTmps, 'er_specimen_name', spec, 'T')
#
# first look for replicate measurements
#
        Ninit = len(NewSpecs)
        if noave != 1:
            # averages replicate measurements, returns treatment keys that are
            # being used
            vdata, treatkeys = vspec_magic(NewSpecs)
            if len(vdata) != len(NewSpecs):
                # print spec,'started with ',Ninit,' ending with ',len(vdata)
                NewSpecs = vdata
                # print "Averaged replicate measurements"
#
# now look through this specimen's records - try to figure out what experiment it is
#
        if len(NewSpecs) > 1:  # more than one meas for this spec - part of an unknown experiment
            SpecMeths = get_list(NewSpecs, 'magic_method_codes').split(":")
            # TRM steps, could be TRM acquisition, Shaw or a Thellier
            # experiment or TDS experiment
            if "LT-T-I" in SpecMeths and experiment_name == "":
                #
                # collect all the infield steps and look for changes in dc field vector
                #
                Steps, TI = [], 1
                for rec in NewSpecs:
                    methods = get_list(
                        NewSpecs, 'magic_method_codes').split(":")
                    if "LT-T-I" in methods:
                        Steps.append(rec)  # get all infield steps together
                rec_bak = Steps[0]
                if "treatment_dc_field_phi" in list(rec_bak.keys()) and "treatment_dc_field_theta" in list(rec_bak.keys()):
                    # at least there is field orientation info
                    if rec_bak["treatment_dc_field_phi"] != "" and rec_bak["treatment_dc_field_theta"] != "":
                        phi0, theta0 = rec_bak["treatment_dc_field_phi"], rec_bak["treatment_dc_field_theta"]
                        for k in range(1, len(Steps)):
                            rec = Steps[k]
                            phi, theta = rec["treatment_dc_field_phi"], rec["treatment_dc_field_theta"]
                            if phi != phi0 or theta != theta0:
                                ANIS = 1   # if direction changes, is some sort of anisotropy experiment
                if "LT-AF-I" in SpecMeths and "LT-AF-Z" in SpecMeths:  # must be Shaw :(
                    experiment_name = "LP-PI-TRM:LP-PI-ALT-AFARM"
                elif TRM == 1:
                    experiment_name = "LP-TRM"
            else:
                TI = 0  # no infield steps at all
            if "LT-T-Z" in SpecMeths and experiment_name == "":  # thermal demag steps
                if TI == 0:
                    experiment_name = "LP-DIR-T"  # just ordinary thermal demag
                elif TRM != 1:  # heart pounding - could be some  kind of TRM normalized paleointensity or LP-TRM-TD experiment
                    Temps = []
                    for step in Steps:  # check through the infield steps - if all at same temperature, then must be a demag of a total TRM with checks
                        if step['treatment_temp'] not in Temps:
                            Temps.append(step['treatment_temp'])
                    if len(Temps) > 1:
                        experiment_name = "LP-PI-TRM"  # paleointensity normalized by TRM
                    else:
                        # thermal demag of a lab TRM (could be part of a
                        # LP-PI-TDS experiment)
                        experiment_name = "LP-TRM-TD"
                TZ = 1
            else:
                TZ = 0  # no zero field steps at all
            if "LT-AF-I" in SpecMeths:  # ARM steps
                Steps = []
                for rec in NewSpecs:
                    tmp = rec["magic_method_codes"].split(":")
                    methods = []
                    for meth in tmp:
                        methods.append(meth.strip())
                    if "LT-AF-I" in methods:
                        Steps.append(rec)  # get all infield steps together
                rec_bak = Steps[0]
                if "treatment_dc_field_phi" in list(rec_bak.keys()) and "treatment_dc_field_theta" in list(rec_bak.keys()):
                    # at least there is field orientation info
                    if rec_bak["treatment_dc_field_phi"] != "" and rec_bak["treatment_dc_field_theta"] != "":
                        phi0, theta0 = rec_bak["treatment_dc_field_phi"], rec_bak["treatment_dc_field_theta"]
                        ANIS = 0
                        for k in range(1, len(Steps)):
                            rec = Steps[k]
                            phi, theta = rec["treatment_dc_field_phi"], rec["treatment_dc_field_theta"]
                            if phi != phi0 or theta != theta0:
                                ANIS = 1   # if direction changes, is some sort of anisotropy experiment
                        if ANIS == 1:
                            experiment_name = "LP-AN-ARM"
                if experiment_name == "":  # not anisotropy of ARM - acquisition?
                    field0 = rec_bak["treatment_dc_field"]
                    ARM = 0
                    for k in range(1, len(Steps)):
                        rec = Steps[k]
                        field = rec["treatment_dc_field"]
                        if field != field0:
                            ARM = 1
                    if ARM == 1:
                        experiment_name = "LP-ARM"
                AFI = 1
            else:
                AFI = 0  # no ARM steps at all
            if "LT-AF-Z" in SpecMeths and experiment_name == "":  # AF demag steps
                if AFI == 0:
                    experiment_name = "LP-DIR-AF"  # just ordinary AF demag
                else:  # heart pounding - a pseudothellier?
                    experiment_name = "LP-PI-ARM"
                AFZ = 1
            else:
                AFZ = 0  # no AF demag at all
            if "LT-IRM" in SpecMeths:  # IRM
                Steps = []
                for rec in NewSpecs:
                    tmp = rec["magic_method_codes"].split(":")
                    methods = []
                    for meth in tmp:
                        methods.append(meth.strip())
                    if "LT-IRM" in methods:
                        Steps.append(rec)  # get all infield steps together
                rec_bak = Steps[0]
                if "treatment_dc_field_phi" in list(rec_bak.keys()) and "treatment_dc_field_theta" in list(rec_bak.keys()):
                    # at least there is field orientation info
                    if rec_bak["treatment_dc_field_phi"] != "" and rec_bak["treatment_dc_field_theta"] != "":
                        phi0, theta0 = rec_bak["treatment_dc_field_phi"], rec_bak["treatment_dc_field_theta"]
                        ANIS = 0
                        for k in range(1, len(Steps)):
                            rec = Steps[k]
                            phi, theta = rec["treatment_dc_field_phi"], rec["treatment_dc_field_theta"]
                            if phi != phi0 or theta != theta0:
                                ANIS = 1   # if direction changes, is some sort of anisotropy experiment
                        if ANIS == 1:
                            experiment_name = "LP-AN-IRM"
                if experiment_name == "":  # not anisotropy of IRM - acquisition?
                    field0 = rec_bak["treatment_dc_field"]
                    IRM = 0
                    for k in range(1, len(Steps)):
                        rec = Steps[k]
                        field = rec["treatment_dc_field"]
                        if field != field0:
                            IRM = 1
                    if IRM == 1:
                        experiment_name = "LP-IRM"
                IRM = 1
            else:
                IRM = 0  # no IRM at all
            if "LP-X" in SpecMeths:  # susceptibility run
                Steps = get_dictitem(
                    NewSpecs, 'magic_method_codes', 'LT-X', 'has')
                if len(Steps) > 0:
                    rec_bak = Steps[0]
                    if "treatment_dc_field_phi" in list(rec_bak.keys()) and "treatment_dc_field_theta" in list(rec_bak.keys()):
                        # at least there is field orientation info
                        if rec_bak["treatment_dc_field_phi"] != "" and rec_bak["treatment_dc_field_theta"] != "":
                            phi0, theta0 = rec_bak["treatment_dc_field_phi"], rec_bak["treatment_dc_field_theta"]
                            ANIS = 0
                            for k in range(1, len(Steps)):
                                rec = Steps[k]
                                phi, theta = rec["treatment_dc_field_phi"], rec["treatment_dc_field_theta"]
                                if phi != phi0 or theta != theta0:
                                    ANIS = 1   # if direction changes, is some sort of anisotropy experiment
                            if ANIS == 1:
                                experiment_name = "LP-AN-MS"
            else:
                CHI = 0  # no susceptibility at all
    #
    # now need to deal with special thellier experiment problems - first clear up pTRM checks and  tail checks
    #
            if experiment_name == "LP-PI-TRM":  # is some sort of thellier experiment
                rec_bak = NewSpecs[0]
                tmp = rec_bak["magic_method_codes"].split(":")
                methbak = []
                for meth in tmp:
                    methbak.append(meth.strip())  # previous steps method codes
                for k in range(1, len(NewSpecs)):
                    rec = NewSpecs[k]
                    tmp = rec["magic_method_codes"].split(":")
                    meths = []
                    for meth in tmp:
                        # get this guys method codes
                        meths.append(meth.strip())
    #
    # check if this is a pTRM check
    #
                    if float(rec["treatment_temp"]) < float(rec_bak["treatment_temp"]):  # went backward
                        if "LT-T-I" in meths and "LT-T-Z" in methbak:  # must be a pTRM check after first z
                            #
                            # replace LT-T-I method code with LT-PTRM-I
                            #
                            methcodes = ""
                            for meth in meths:
                                if meth != "LT-T-I":
                                    methcode = methcode + meth.strip() + ":"
                            methcodes = methcodes + "LT-PTRM-I"
                            meths = methcodes.split(":")
                            pTRM = 1
                        elif "LT-T-Z" in meths and "LT-T-I" in methbak:  # must be pTRM check after first I
                            #
                            # replace LT-T-Z method code with LT-PTRM-Z
                            #
                            methcodes = ""
                            for meth in meths:
                                if meth != "LT-T-Z":
                                    methcode = methcode + meth + ":"
                            methcodes = methcodes + "LT-PTRM-Z"
                            meths = methcodes.split(":")
                            pTRM = 1
                    methcodes = ""
                    for meth in meths:
                        methcodes = methcodes + meth.strip() + ":"
                    # attach new method code
                    rec["magic_method_codes"] = methcodes[:-1]
                    rec_bak = rec  # next previous record
                    tmp = rec_bak["magic_method_codes"].split(":")
                    methbak = []
                    for meth in tmp:
                        # previous steps method codes
                        methbak.append(meth.strip())
    #
    # done with assigning pTRM checks.  data should be "fixed" in NewSpecs
    #
    # now let's find out which steps are infield zerofield (IZ) and which are zerofield infield (ZI)
    #
                rec_bak = NewSpecs[0]
                tmp = rec_bak["magic_method_codes"].split(":")
                methbak = []
                for meth in tmp:
                    methbak.append(meth.strip())  # previous steps method codes
                if "LT-NO" not in methbak:  # first measurement is not NRM
                    if "LT-T-I" in methbak:
                        IZorZI = "LP-PI-TRM-IZ"  # first pair is IZ
                    if "LT-T-Z" in methbak:
                        IZorZI = "LP-PI-TRM-ZI"  # first pair is ZI
                    if IZorZI not in methbak:
                        methbak.append(IZorZI)
                    methcode = ""
                    for meth in methbak:
                        methcode = methcode + meth + ":"
                    # fix first heating step when no NRM
                    NewSpecs[0]["magic_method_codes"] = methcode[:-1]
                else:
                    IZorZI = ""  # first measurement is NRM and not one of a pair
                for k in range(1, len(NewSpecs)):  # hunt through measurements again
                    rec = NewSpecs[k]
                    tmp = rec["magic_method_codes"].split(":")
                    meths = []
                    for meth in tmp:
                        # get this guys method codes
                        meths.append(meth.strip())
    #
    # check if this start a new temperature step of a infield/zerofield pair
    #
                    if float(rec["treatment_temp"]) > float(rec_bak["treatment_temp"]) and "LT-PTRM-I" not in methbak:  # new pair?
                        if "LT-T-I" in meths:  # infield of this pair
                            IZorZI = "LP-PI-TRM-IZ"
                            IZ = 1  # at least one IZ pair
                        elif "LT-T-Z" in meths:  # zerofield
                            IZorZI = "LP-PI-TRM-ZI"
                            ZI = 1  # at least one ZI pair
                    # new pair after out of sequence PTRM check?
                    elif float(rec["treatment_temp"]) > float(rec_bak["treatment_temp"]) and "LT-PTRM-I" in methbak and IZorZI != "LP-PI-TRM-ZI":
                        if "LT-T-I" in meths:  # infield of this pair
                            IZorZI = "LP-PI-TRM-IZ"
                            IZ = 1  # at least one IZ pair
                        elif "LT-T-Z" in meths:  # zerofield
                            IZorZI = "LP-PI-TRM-ZI"
                            ZI = 1  # at least one ZI pair
                    # stayed same temp
                    if float(rec["treatment_temp"]) == float(rec_bak["treatment_temp"]):
                        if "LT-T-Z" in meths and "LT-T-I" in methbak and IZorZI == "LP-PI-TRM-ZI":  # must be a tail check
                            #
                            # replace LT-T-Z method code with LT-PTRM-MD
                            #
                            methcodes = ""
                            for meth in meths:
                                if meth != "LT-T-Z":
                                    methcode = methcode + meth + ":"
                            methcodes = methcodes + "LT-PTRM-MD"
                            meths = methcodes.split(":")
                            MD = 1
    # fix method codes
                    if "LT-PTRM-I" not in meths and "LT-PTRM-MD" not in meths and IZorZI not in meths:
                        meths.append(IZorZI)
                    newmeths = []
                    for meth in meths:
                        if meth not in newmeths:
                            newmeths.append(meth)  # try to get uniq set
                    methcode = ""
                    for meth in newmeths:
                        methcode = methcode + meth + ":"
                    rec["magic_method_codes"] = methcode[:-1]
                    rec_bak = rec  # moving on to next record, making current one the backup
                    # get last specimen's method codes in a list
                    methbak = rec_bak["magic_method_codes"].split(":")

    #
    # done with this specimen's records, now  check if any pTRM checks or MD checks
    #
                if pTRM == 1:
                    experiment_name = experiment_name + ":LP-PI-ALT-PTRM"
                if MD == 1:
                    experiment_name = experiment_name + ":LP-PI-BT-MD"
                if IZ == 1 and ZI == 1:
                    experiment_name = experiment_name + ":LP-PI-BT-IZZI"
                if IZ == 1 and ZI == 0:
                    experiment_name = experiment_name + ":LP-PI-IZ"  # Aitken method
                if IZ == 0 and ZI == 1:
                    experiment_name = experiment_name + ":LP-PI-ZI"  # Coe method
                IZ, ZI, pTRM, MD = 0, 0, 0, 0  # reset these for next specimen
                for rec in NewSpecs:  # fix the experiment name for all recs for this specimen and save in SpecOuts
                    # assign an experiment name to all specimen measurements
                    # from this specimen
                    if experiment_name != "":
                        rec["magic_method_codes"] = rec["magic_method_codes"] + \
                            ":" + experiment_name
                    rec["magic_experiment_name"] = spec + ":" + experiment_name
                    rec['measurement_number'] = '%i' % (
                        measnum)  # assign measurement numbers
                    measnum += 1
                    #rec['sequence'] = '%i'%(seqnum)
                    #seqnum += 1
                    SpecOuts.append(rec)
            elif experiment_name == "LP-PI-TRM:LP-PI-ALT-AFARM":  # is a Shaw experiment!
                ARM, TRM = 0, 0
                for rec in NewSpecs:  # fix the experiment name for all recs for this specimen and save in SpecOuts
                    # assign an experiment name to all specimen measurements from this specimen
                    # make the second ARM in Shaw experiments LT-AF-I-2, stick
                    # in the AF of ARM and TRM codes
                    meths = rec["magic_method_codes"].split(":")
                    if ARM == 1:
                        if "LT-AF-I" in meths:
                            del meths[meths.index("LT-AF-I")]
                            meths.append("LT-AF-I-2")
                            ARM = 2
                        if "LT-AF-Z" in meths and TRM == 0:
                            meths.append("LP-ARM-AFD")
                    if TRM == 1 and ARM == 1:
                        if "LT-AF-Z" in meths:
                            meths.append("LP-TRM-AFD")
                    if ARM == 2:
                        if "LT-AF-Z" in meths:
                            meths.append("LP-ARM2-AFD")
                    newcode = ""
                    for meth in meths:
                        newcode = newcode + meth + ":"
                    rec["magic_method_codes"] = newcode[:-1]
                    if "LT-AF-I" in meths:
                        ARM = 1
                    if "LT-T-I" in meths:
                        TRM = 1
                    rec["magic_method_codes"] = rec["magic_method_codes"] + \
                        ":" + experiment_name
                    rec["magic_experiment_name"] = spec + ":" + experiment_name
                    rec['measurement_number'] = '%i' % (
                        measnum)  # assign measurement numbers
                    #rec['sequence'] = '%i'%(seqnum)
                    #seqnum += 1
                    measnum += 1
                    SpecOuts.append(rec)
            else:  # not a Thellier-Thellier  or a Shaw experiemnt
                for rec in NewSpecs:
                    if experiment_name == "":
                        rec["magic_method_codes"] = "LT-NO"
                        rec["magic_experiment_name"] = spec + ":LT-NO"
                        rec['measurement_number'] = '%i' % (
                            measnum)  # assign measurement numbers
                        #rec['sequence'] = '%i'%(seqnum)
                        #seqnum += 1
                        measnum += 1
                    else:
                        if experiment_name not in rec['magic_method_codes']:
                            rec["magic_method_codes"] = rec["magic_method_codes"] + \
                                ":" + experiment_name
                            rec["magic_method_codes"] = rec["magic_method_codes"].strip(
                                ':')
                        rec['measurement_number'] = '%i' % (
                            measnum)  # assign measurement numbers
                        #rec['sequence'] = '%i'%(seqnum)
                        #seqnum += 1
                        measnum += 1
                        rec["magic_experiment_name"] = spec + \
                            ":" + experiment_name
                    rec["magic_software_packages"] = version_num
                    SpecOuts.append(rec)
        else:
            NewSpecs[0]["magic_experiment_name"] = spec + ":" + \
                NewSpecs[0]['magic_method_codes'].split(':')[0]
            NewSpecs[0]["magic_software_packages"] = version_num
            # just copy over the single record as is
            SpecOuts.append(NewSpecs[0])
    return SpecOuts


def measurements_methods3(meas_data, noave):
    """
    add necessary method codes, experiment names, sequence, etc.
    """
#
    if noave:
        noave = 1
    else:
        noave = 0
    version_num = get_version()
    seqnum = 0
    sids = get_specs(meas_data)
# list  of measurement records for this specimen
#
# step through spec by spec
#
    SpecTmps, SpecOuts = [], []
    for spec in sids:
        TRM, IRM3D, ATRM, CR, AC = 0, 0, 0, 0, 0
        expcodes = ""
# first collect all data for this specimen and do lab treatments
        # list  of measurement records for this specimen
        SpecRecs = get_dictitem(meas_data, 'specimen', spec, 'T')
        for rec in SpecRecs:
            if 'quality' not in list(rec.keys()):
                rec['quality'] = 'g'
            tmpmeths = rec['method_codes'].split(":")
            meths = []
            if 'LP-HYS' in tmpmeths:
                HYS = 1  # catch these!
            if "LP-TRM" in tmpmeths:
                TRM = 1  # catch these suckers here!
            if "LP-IRM-3D" in tmpmeths:
                IRM3D = 1  # catch these suckers here!
            elif "LP-AN-TRM" in tmpmeths:
                ATRM = 1  # catch these suckers here!
            elif "LP-CR-TRM" in tmpmeths:
                CR = 1  # catch these suckers here!
            elif "LT-PTRM-AC" in tmpmeths:
                AC = 1  # catch these suckers here!
#
# otherwise write over existing method codes
#
# find NRM data (LT-NO)
#
            elif float(rec["meas_temp"]) >= 273. and float(rec["meas_temp"]) < 323.:
                # between 0 and 50C is room T measurement
                if ("meas_dc_field" not in list(rec.keys()) or float(rec["meas_dc_field"]) == 0 or rec["meas_dc_field"] == "") and ("meas_ac_field" not in list(rec.keys()) or float(rec["meas_ac_field"]) == 0 or rec["meas_ac_field"] == ""):
                    # measurement done in zero field!
                    if "treat_temp" not in list(rec.keys()) or str(rec["treat_temp"]).strip() == "" or (float(rec["treat_temp"]) >= 273. and float(rec["treat_temp"]) < 298.):
                        # between 0 and 50C is room T treatment
                        if "treat_ac_field" not in list(rec.keys()) or str(rec["treat_ac_field"]) == "" or float(rec["treat_ac_field"]) == 0:
                            # no AF
                            # no IRM!
                            if "treat_dc_field" not in list(rec.keys()) or str(rec["treat_dc_field"]) == "" or float(rec["treat_dc_field"]) == 0:
                                if "LT-NO" not in meths:
                                    meths.append("LT-NO")
                            elif "LT-IRM" not in meths:
                                meths.append("LT-IRM")  # it's an IRM
#
# find AF/infield/zerofield
#
                        # no ARM
                        elif "treat_dc_field" not in list(rec.keys()) or rec["treat_dc_field"] == "" or float(rec["treat_dc_field"]) == 0:
                            if "LT-AF-Z" not in meths:
                                meths.append("LT-AF-Z")
                        else:  # yes ARM
                            if "LT-AF-I" not in meths:
                                meths.append("LT-AF-I")
#
# find Thermal/infield/zerofield
#
                    elif float(rec["treat_temp"]) >= 323:  # treatment done at  high T
                        if TRM == 1:
                            if "LT-T-I" not in meths:
                                # TRM - even if zero applied field!
                                meths.append("LT-T-I")
                        # no TRM
                        elif "treat_dc_field" not in list(rec.keys()) or rec["treat_dc_field"] == "" or float(rec["treat_dc_field"]) == 0.:
                            if "LT-T-Z" not in meths:
                                # don't overwrite if part of a TRM experiment!
                                meths.append("LT-T-Z")
                        else:  # yes TRM
                            if "LT-T-I" not in meths:
                                meths.append("LT-T-I")
#
# find low-T infield,zero field
#
                    else:  # treatment done at low T
                        # no field
                        if "treat_dc_field" not in list(rec.keys()) or rec["treat_dc_field"] == "" or float(rec["treat_dc_field"]) == 0:
                            if "LT-LT-Z" not in meths:
                                meths.append("LT-LT-Z")
                        else:  # yes field
                            if "LT-LT-I" not in meths:
                                meths.append("LT-LT-I")

                if "susc_chi_volume" in list(rec.keys()) or "susc_chi_mass" in list(rec.keys()):
                    if "LP-X" not in meths:
                        meths.append("LP-X")
                # measurement in presence of dc field and not susceptibility;
                # hysteresis!
                elif "meas_lab_dc_field" in list(rec.keys()) and rec["meas_lab_dc_field"] != 0:
                    # if "LP-HYS" not in meths:
                    #    hysq = input("Is this a hysteresis experiment? [1]/0")
                    #    if hysq == "" or hysq == "1":
                    #        meths.append("LP-HYS")
                    #    else:
                    #        metha = input(
                    #            "Enter the lab protocol code that best describes this experiment ")
                    #        meths.append(metha)
                    if HYS:
                        meths.append("LP-HYS")
                methcode = ""
                for meth in meths:
                    methcode = methcode + meth.strip() + ":"
                rec["method_codes"] = methcode[:-1]  # assign them back
#
# done with first pass, collect and assign provisional method codes
            if "description" not in list(rec.keys()):
                rec["description"] = ""
            if "standard" not in list(rec.keys()):
                rec["standard"] = "s"
            rec["citations"] = "This study"
            SpecTmps.append(rec)
# ready for second pass through, step through specimens, check whether ptrm, ptrm tail checks, or AARM, etc.
#
    for spec in sids:
        MD, pTRM, IZ, ZI = 0, 0, 0, 0  # these are flags for the lab protocol codes
        expcodes = ""
        NewSpecs, SpecMeths = [], []
        experiment_name, measnum = "", 0
        if IRM3D == 1:
            experiment_name = "LP-IRM-3D"
        if ATRM == 1:
            experiment_name = "LP-AN-TRM"
        if CR == 1:
            experiment_name = "LP-CR"
        NewSpecs = get_dictitem(SpecTmps, 'specimen', spec, 'T')
#
# first look for replicate measurements
#
        Ninit = len(NewSpecs)
        if noave != 1:
            # averages replicate measurements, returns treatment keys that are
            # being used
            vdata, treatkeys = vspec_magic3(NewSpecs)
            if len(vdata) != len(NewSpecs):
                # print spec,'started with ',Ninit,' ending with ',len(vdata)
                NewSpecs = vdata
                # print "Averaged replicate measurements"
#
# now look through this specimen's records - try to figure out what experiment it is
#
        if len(NewSpecs) > 1:  # more than one meas for this spec - part of an unknown experiment
            SpecMeths = get_list(NewSpecs, 'method_codes').split(":")
            # TRM steps, could be TRM acquisition, Shaw or a Thellier
            # experiment or TDS experiment
            if "LT-T-I" in SpecMeths and experiment_name == "":
                #
                # collect all the infield steps and look for changes in dc field vector
                #
                Steps, TI = [], 1
                for rec in NewSpecs:
                    methods = get_list(NewSpecs, 'method_codes').split(":")
                    if "LT-T-I" in methods:
                        Steps.append(rec)  # get all infield steps together
                rec_bak = Steps[0]
                if "treat_dc_field_phi" in list(rec_bak.keys()) and "treat_dc_field_theta" in list(rec_bak.keys()):
                    # at least there is field orientation info
                    if rec_bak["treat_dc_field_phi"] != "" and rec_bak["treat_dc_field_theta"] != "":
                        phi0, theta0 = rec_bak["treat_dc_field_phi"], rec_bak["treat_dc_field_theta"]
                        for k in range(1, len(Steps)):
                            rec = Steps[k]
                            phi, theta = rec["treat_dc_field_phi"], rec["treat_dc_field_theta"]
                            if phi != phi0 or theta != theta0:
                                ANIS = 1   # if direction changes, is some sort of anisotropy experiment
                if "LT-AF-I" in SpecMeths and "LT-AF-Z" in SpecMeths:  # must be Shaw :(
                    experiment_name = "LP-PI-TRM:LP-PI-ALT-AFARM"
                elif TRM == 1:
                    experiment_name = "LP-TRM"
            else:
                TI = 0  # no infield steps at all
            if ("LT-T-Z" in SpecMeths or "LT-LT-Z" in SpecMeths)and experiment_name == "":  # thermal demag steps
                if TI == 0:
                    experiment_name = "LP-DIR-T"  # just ordinary thermal demag
                elif TRM != 1:  # heart pounding - could be some  kind of TRM normalized paleointensity or LP-TRM-TD experiment
                    Temps = []
                    for step in Steps:  # check through the infield steps - if all at same temperature, then must be a demag of a total TRM with checks
                        if step['treat_temp'] not in Temps:
                            Temps.append(step['treat_temp'])
                    if len(Temps) > 1:
                        experiment_name = "LP-PI-TRM"  # paleointensity normalized by TRM
                    else:
                        # thermal demag of a lab TRM (could be part of a
                        # LP-PI-TDS experiment)
                        experiment_name = "LP-TRM-TD"
                TZ = 1
            else:
                TZ = 0  # no zero field steps at all
            if "LT-AF-I" in SpecMeths:  # ARM steps
                Steps = []
                for rec in NewSpecs:
                    tmp = rec["method_codes"].split(":")
                    methods = []
                    for meth in tmp:
                        methods.append(meth.strip())
                    if "LT-AF-I" in methods:
                        Steps.append(rec)  # get all infield steps together
                rec_bak = Steps[0]
                if "treat_dc_field_phi" in list(rec_bak.keys()) and "treat_dc_field_theta" in list(rec_bak.keys()):
                    # at least there is field orientation info
                    if rec_bak["treat_dc_field_phi"] != "" and rec_bak["treat_dc_field_theta"] != "":
                        phi0, theta0 = rec_bak["treat_dc_field_phi"], rec_bak["treat_dc_field_theta"]
                        ANIS = 0
                        for k in range(1, len(Steps)):
                            rec = Steps[k]
                            phi, theta = rec["treat_dc_field_phi"], rec["treat_dc_field_theta"]
                            if phi != phi0 or theta != theta0:
                                ANIS = 1   # if direction changes, is some sort of anisotropy experiment
                        if ANIS == 1:
                            experiment_name = "LP-AN-ARM"
                if experiment_name == "":  # not anisotropy of ARM - acquisition?
                    field0 = rec_bak["treat_dc_field"]
                    ARM = 0
                    for k in range(1, len(Steps)):
                        rec = Steps[k]
                        field = rec["treat_dc_field"]
                        if field != field0:
                            ARM = 1
                    if ARM == 1:
                        experiment_name = "LP-ARM"
                AFI = 1
            else:
                AFI = 0  # no ARM steps at all
            if "LT-AF-Z" in SpecMeths and experiment_name == "":  # AF demag steps
                if AFI == 0:
                    experiment_name = "LP-DIR-AF"  # just ordinary AF demag
                else:  # heart pounding - a pseudothellier?
                    experiment_name = "LP-PI-ARM"
                AFZ = 1
            else:
                AFZ = 0  # no AF demag at all
            if "LT-IRM" in SpecMeths:  # IRM
                Steps = []
                for rec in NewSpecs:
                    tmp = rec["method_codes"].split(":")
                    methods = []
                    for meth in tmp:
                        methods.append(meth.strip())
                    if "LT-IRM" in methods:
                        Steps.append(rec)  # get all infield steps together
                rec_bak = Steps[0]
                if "treat_dc_field_phi" in list(rec_bak.keys()) and "treat_dc_field_theta" in list(rec_bak.keys()):
                    # at least there is field orientation info
                    if rec_bak["treat_dc_field_phi"] != "" and rec_bak["treat_dc_field_theta"] != "":
                        phi0, theta0 = rec_bak["treat_dc_field_phi"], rec_bak["treat_dc_field_theta"]
                        ANIS = 0
                        for k in range(1, len(Steps)):
                            rec = Steps[k]
                            phi, theta = rec["treat_dc_field_phi"], rec["treat_dc_field_theta"]
                            if phi != phi0 or theta != theta0:
                                ANIS = 1   # if direction changes, is some sort of anisotropy experiment
                        if ANIS == 1:
                            experiment_name = "LP-AN-IRM"
                if experiment_name == "":  # not anisotropy of IRM - acquisition?
                    field0 = rec_bak["treat_dc_field"]
                    IRM = 0
                    for k in range(1, len(Steps)):
                        rec = Steps[k]
                        field = rec["treat_dc_field"]
                        if field != field0:
                            IRM = 1
                    if IRM == 1:
                        experiment_name = "LP-IRM"
                IRM = 1
            else:
                IRM = 0  # no IRM at all
            if "LP-X" in SpecMeths:  # susceptibility run
                Steps = get_dictitem(NewSpecs, 'method_codes', 'LT-X', 'has')
                if len(Steps) > 0:
                    rec_bak = Steps[0]
                    if "treat_dc_field_phi" in list(rec_bak.keys()) and "treat_dc_field_theta" in list(rec_bak.keys()):
                        # at least there is field orientation info
                        if rec_bak["treat_dc_field_phi"] != "" and rec_bak["treat_dc_field_theta"] != "":
                            phi0, theta0 = rec_bak["treat_dc_field_phi"], rec_bak["treat_dc_field_theta"]
                            ANIS = 0
                            for k in range(1, len(Steps)):
                                rec = Steps[k]
                                phi, theta = rec["treat_dc_field_phi"], rec["treat_dc_field_theta"]
                                if phi != phi0 or theta != theta0:
                                    ANIS = 1   # if direction changes, is some sort of anisotropy experiment
                            if ANIS == 1:
                                experiment_name = "LP-AN-MS"
            else:
                CHI = 0  # no susceptibility at all
    #
    # now need to deal with special thellier experiment problems - first clear up pTRM checks and  tail checks
    #
            if experiment_name == "LP-PI-TRM":  # is some sort of thellier experiment
                rec_bak = NewSpecs[0]
                tmp = rec_bak["method_codes"].split(":")
                methbak = []
                for meth in tmp:
                    methbak.append(meth.strip())  # previous steps method codes
                for k in range(1, len(NewSpecs)):
                    rec = NewSpecs[k]
                    tmp = rec["method_codes"].split(":")
                    meths = []
                    for meth in tmp:
                        # get this guys method codes
                        meths.append(meth.strip())
    #
    # check if this is a pTRM check
    #
                    if float(rec["treat_temp"]) < float(rec_bak["treat_temp"]):  # went backward
                        if "LT-PTRM-AC" in rec['method_codes']:
                            methcodes = methcodes + "LT-PTRM-AC"
                        elif "LT-T-I" in meths and "LT-T-Z" in methbak:  # must be a pTRM check after first z
                            #
                            # replace LT-T-I method code with LT-PTRM-I
                            #
                            methcodes = ""
                            for meth in meths:
                                if meth != "LT-T-I":
                                    methcode = methcode + meth.strip() + ":"
                            methcodes = methcodes + "LT-PTRM-I"
                            meths = methcodes.split(":")
                            pTRM = 1
                        elif "LT-T-Z" in meths and "LT-T-I" in methbak:  # must be pTRM check after first I
                            #
                            # replace LT-T-Z method code with LT-PTRM-Z
                            #
                            methcodes = ""
                            for meth in meths:
                                if meth != "LT-T-Z":
                                    methcode = methcode + meth + ":"
                            methcodes = methcodes + "LT-PTRM-Z"
                            meths = methcodes.split(":")
                            pTRM = 1
                    methcodes = ""
                    for meth in meths:
                        methcodes = methcodes + meth.strip() + ":"
                    # attach new method code
                    rec["method_codes"] = methcodes[:-1]
                    rec_bak = rec  # next previous record
                    tmp = rec_bak["method_codes"].split(":")
                    methbak = []
                    for meth in tmp:
                        # previous steps method codes
                        methbak.append(meth.strip())
    #
    # done with assigning pTRM checks.  data should be "fixed" in NewSpecs
    #
    # now let's find out which steps are infield zerofield (IZ) and which are zerofield infield (ZI)
    #
                rec_bak = NewSpecs[0]
                tmp = rec_bak["method_codes"].split(":")
                methbak = []
                for meth in tmp:
                    methbak.append(meth.strip())  # previous steps method codes
                if "LT-NO" not in methbak:  # first measurement is not NRM
                    if "LT-T-I" in methbak:
                        IZorZI = "LP-PI-TRM-IZ"  # first pair is IZ
                    if "LT-T-Z" in methbak:
                        IZorZI = "LP-PI-TRM-ZI"  # first pair is ZI
                    if IZorZI not in methbak:
                        methbak.append(IZorZI)
                    methcode = ""
                    for meth in methbak:
                        methcode = methcode + meth + ":"
                    # fix first heating step when no NRM
                    NewSpecs[0]["method_codes"] = methcode[:-1]
                else:
                    IZorZI = ""  # first measurement is NRM and not one of a pair
                for k in range(1, len(NewSpecs)):  # hunt through measurements again
                    rec = NewSpecs[k]
                    tmp = rec["method_codes"].split(":")
                    meths = []
                    for meth in tmp:
                        # get this guys method codes
                        meths.append(meth.strip())
    #
    # check if this start a new temperature step of a infield/zerofield pair
    #
                    # new pair?
                    if float(rec["treat_temp"]) > float(rec_bak["treat_temp"]) and "LT-PTRM-I" not in methbak:
                        if "LT-T-I" in meths:  # infield of this pair
                            IZorZI = "LP-PI-TRM-IZ"
                            IZ = 1  # at least one IZ pair
                        elif "LT-T-Z" in meths:  # zerofield
                            IZorZI = "LP-PI-TRM-ZI"
                            ZI = 1  # at least one ZI pair
                    # new pair after out of sequence PTRM check?
                    elif float(rec["treat_temp"]) > float(rec_bak["treat_temp"]) and "LT-PTRM-I" in methbak and IZorZI != "LP-PI-TRM-ZI":
                        if "LT-T-I" in meths:  # infield of this pair
                            IZorZI = "LP-PI-TRM-IZ"
                            IZ = 1  # at least one IZ pair
                        elif "LT-T-Z" in meths:  # zerofield
                            IZorZI = "LP-PI-TRM-ZI"
                            ZI = 1  # at least one ZI pair
                    if float(rec["treat_temp"]) == float(rec_bak["treat_temp"]):  # stayed same temp
                        if "LT-T-Z" in meths and "LT-T-I" in methbak and IZorZI == "LP-PI-TRM-ZI":  # must be a tail check
                            #
                            # replace LT-T-Z method code with LT-PTRM-MD
                            #
                            methcodes = ""
                            for meth in meths:
                                if meth != "LT-T-Z":
                                    methcode = methcode + meth + ":"
                            methcodes = methcodes + "LT-PTRM-MD"
                            meths = methcodes.split(":")
                            MD = 1
    # fix method codes
                    if "LT-PTRM-I" not in meths and "LT-PTRM-MD" not in meths and IZorZI not in meths:
                        meths.append(IZorZI)
                    newmeths = []
                    for meth in meths:
                        if meth not in newmeths:
                            newmeths.append(meth)  # try to get uniq set
                    methcode = ""
                    for meth in newmeths:
                        methcode = methcode + meth + ":"
                    rec["method_codes"] = methcode[:-1]
                    rec_bak = rec  # moving on to next record, making current one the backup
                    # get last specimen's method codes in a list
                    methbak = rec_bak["method_codes"].split(":")

    #
    # done with this specimen's records, now  check if any pTRM checks or MD checks
    #
                if pTRM == 1:
                    experiment_name = experiment_name + ":LP-PI-ALT-PTRM"
                if MD == 1:
                    experiment_name = experiment_name + ":LP-PI-BT-MD"
                if IZ == 1 and ZI == 1:
                    experiment_name = experiment_name + ":LP-PI-BT-IZZI"
                if IZ == 1 and ZI == 0:
                    experiment_name = experiment_name + ":LP-PI-IZ"  # Aitken method
                if IZ == 0 and ZI == 1:
                    experiment_name = experiment_name + ":LP-PI-ZI"  # Coe method
                IZ, ZI, pTRM, MD = 0, 0, 0, 0  # reset these for next specimen
                for rec in NewSpecs:  # fix the experiment name for all recs for this specimen and save in SpecOuts
                    # assign an experiment name to all specimen measurements
                    # from this specimen
                    if experiment_name != "":
                        rec["method_codes"] = rec["method_codes"] + \
                            ":" + experiment_name
                    rec["experiment"] = spec + ":" + experiment_name
                    rec['treat_step_num'] = '%i' % (
                        measnum)  # assign measurement numbers
                    rec['sequence'] = '%i' % (seqnum)
                    seqnum += 1
                    measnum += 1
                    SpecOuts.append(rec)
            elif experiment_name == "LP-PI-TRM:LP-PI-ALT-AFARM":  # is a Shaw experiment!
                ARM, TRM = 0, 0
                for rec in NewSpecs:  # fix the experiment name for all recs for this specimen and save in SpecOuts
                    # assign an experiment name to all specimen measurements from this specimen
                    # make the second ARM in Shaw experiments LT-AF-I-2, stick
                    # in the AF of ARM and TRM codes
                    meths = rec["method_codes"].split(":")
                    if ARM == 1:
                        if "LT-AF-I" in meths:
                            del meths[meths.index("LT-AF-I")]
                            meths.append("LT-AF-I-2")
                            ARM = 2
                        if "LT-AF-Z" in meths and TRM == 0:
                            meths.append("LP-ARM-AFD")
                    if TRM == 1 and ARM == 1:
                        if "LT-AF-Z" in meths:
                            meths.append("LP-TRM-AFD")
                    if ARM == 2:
                        if "LT-AF-Z" in meths:
                            meths.append("LP-ARM2-AFD")
                    newcode = ""
                    for meth in meths:
                        newcode = newcode + meth + ":"
                    rec["method_codes"] = newcode[:-1]
                    if "LT-AF-I" in meths:
                        ARM = 1
                    if "LT-T-I" in meths:
                        TRM = 1
                    rec["method_codes"] = rec["method_codes"] + \
                        ":" + experiment_name
                    rec["experiment"] = spec + ":" + experiment_name
                    rec['treat_step_num'] = '%i' % (
                        measnum)  # assign measurement numbers
                    rec['sequence'] = '%i' % (seqnum)
                    seqnum += 1
                    measnum += 1
                    SpecOuts.append(rec)
            else:  # not a Thellier-Thellier  or a Shaw experiemnt
                for rec in NewSpecs:
                    if experiment_name == "":
                        rec["method_codes"] = "LT-NO"
                        rec["experiment"] = spec + ":LT-NO"
                        rec['treat_step_num'] = '%i' % (
                            measnum)  # assign measurement numbers
                        rec['sequence'] = '%i' % (seqnum)
                        seqnum += 1
                        measnum += 1
                    else:
                        if experiment_name not in rec['method_codes']:
                            rec["method_codes"] = rec["method_codes"] + \
                                ":" + experiment_name
                            rec["method_codes"] = rec["method_codes"].strip(
                                ':')
                        rec['treat_step_num'] = '%i' % (
                            measnum)  # assign measurement numbers
                        rec['sequence'] = '%i' % (seqnum)
                        seqnum += 1
                        measnum += 1
                        rec["experiment"] = spec + ":" + experiment_name
                    rec["software_packages"] = version_num
                    SpecOuts.append(rec)
        else:
            NewSpecs[0]["experiment"] = spec + ":" + \
                NewSpecs[0]['method_codes'].split(':')[0]
            NewSpecs[0]["software_packages"] = version_num
            # just copy over the single record as is
            SpecOuts.append(NewSpecs[0])
    return SpecOuts


def mw_measurements_methods(MagRecs):
    # first collect all data for this specimen and do lab treatments
    MD, pMRM, IZ, ZI = 0, 0, 0, 0  # these are flags for the lab protocol codes
    expcodes = ""
    NewSpecs, SpecMeths = [], []
    experiment_name = ""
    phi, theta = "", ""
    Dec, Inc = "", ""  # NRM direction
    ZI, IZ, MD, pMRM = "", "", "", ""
    k = -1
    POWT_I, POWT_Z = [], []
    ISteps, ZSteps = [], []
    k = -1
    for rec in MagRecs:
        k += 1
# ready for pass through, step through specimens, check whether ptrm, ptrm tail checks, or AARM, etc.
#
#
# collect all the experimental data for this specimen
# and look through this specimen's records - try to figure out what experiment it is
#
        meths = rec["magic_method_codes"].split(":")
        powt = int(float(rec["treatment_mw_energy"]))
        for meth in meths:
            if meth not in SpecMeths:
                # collect all the methods for this experiment
                SpecMeths.append(meth)
        if "LT-M-I" in meths:  # infield step
            POWT_I.append(powt)
            ISteps.append(k)
            if phi == "":  # first one
                phi = float(rec["treatment_dc_field_phi"])
                theta = float(rec["treatment_dc_field_theta"])
        if "LT-M-Z" in meths:  # zero field  step
            POWT_Z.append(powt)
            ZSteps.append(k)
            if phi == "":  # first one
                Dec = float(rec["measurement_dec"])
                Inc = float(rec["measurement_inc"])
    if "LT-M-I" not in SpecMeths:  # just microwave demag
        experiment_name = "LP-DIR-M"
    else:  # Microwave infield steps , some sort of LP-PI-M experiment
        experiment_name = "LP-PI-M"
        if "LT-PMRM-Z" in SpecMeths or "LT-PMRM-I" in SpecMeths:  # has pTRM checks
            experiment_name = experiment_name + ":LP-PI-ALT-PMRM"
        if Dec != "" and phi != "":
            # angle between applied field and NRM
            ang = angle([Dec, Inc], [phi, theta])
            if ang >= 0 and ang < 2:
                experiment_name = experiment_name + ":LP-NRM-PAR"
            if ang > 88 and ang < 92:
                experiment_name = experiment_name + ":LP-NRM-PERP"
            if ang > 178 and ang < 182:
                experiment_name = experiment_name + ":LP-NRM-APAR"
#
# now check whether there are z pairs for all I steps or is this a single heating experiment
#
        noZ = 0
        for powt in POWT_I:
            if powt not in POWT_Z:
                noZ = 1  # some I's missing their Z's
        if noZ == 1:
            meths = experiment_name.split(":")
            if "LP-NRM-PERP" in meths:  # this is a single  heating experiment
                experiment_name = experiment_name + ":LP-PI-M-S"
            else:
                print("Trouble interpreting file - missing zerofield steps? ")
                return
        else:  # this is a double heating experiment
            experiment_name = experiment_name + ":LP-PI-M-D"
  # check for IZ or ZI pairs
            for istep in ISteps:  # look for first zerofield step with this power
                rec = MagRecs[istep]
                powt_i = int(float(rec["treatment_mw_energy"]))
                IZorZI, step = "", -1
                while IZorZI == "" and step < len(ZSteps) - 1:
                    step += 1
                    zstep = ZSteps[step]
                    zrec = MagRecs[zstep]
                    powt_z = int(float(zrec["treatment_mw_energy"]))
                    if powt_i == powt_z:  # found a match
                        if zstep < istep:  # zero field first
                            IZorZI = "LP-PI-M-ZI"
                            ZI = 1  # there is at least one ZI step
                            break
                        else:  # in field first
                            IZorZI = "LP-PI-M-IZ"
                            IZ = 1  # there is at least one ZI step
                            break
                if IZorZI != "":
                    MagRecs[istep]['magic_method_codes'] = MagRecs[istep]['magic_method_codes'] + ':' + IZorZI
                    MagRecs[zstep]['magic_method_codes'] = MagRecs[zstep]['magic_method_codes'] + ':' + IZorZI
            print(POWT_Z)
            print(POWT_I)
            for istep in ISteps:  # now look for MD checks (zero field)
                # only if there is another step to consider
                if istep + 2 < len(MagRecs):
                    irec = MagRecs[istep]
                    powt_i = int(float(irec["treatment_mw_energy"]))
                    print(istep, powt_i, ZSteps[POWT_Z.index(powt_i)])
                    # if there is a previous zero field step at same  power
                    if powt_i in POWT_Z and ZSteps[POWT_Z.index(powt_i)] < istep:
                        nrec = MagRecs[istep + 1]  # next step
                        nmeths = nrec['magic_method_codes'].split(":")
                        powt_n = int(float(nrec["treatment_mw_energy"]))
                        if 'LT-M-Z' in nmeths and powt_n == powt_i:  # the step after this infield was a zero field at same energy
                            MD = 1  # found a second zero field  match
                            mdmeths = MagRecs[istep +
                                              1]['magic_method_codes'].split(":")
                            # replace method code with tail check code
                            mdmeths[0] = "LT-PMRM-MD"
                            methods = ""
                            for meth in mdmeths:
                                methods = methods + ":" + meth
                            MagRecs[istep + 1]['magic_method_codes'] = methods[1:]
            if MD == 1:
                experiment_name = experiment_name + ":LP-PI-BT-MD"
            if IZ == 1:
                if ZI == 1:
                    experiment_name = experiment_name + ":LP-PI-BT-IZZI"
                else:
                    experiment_name = experiment_name + ":LP-PI-M-IZ"
            else:
                if ZI == 1:
                    experiment_name = experiment_name + ":LP-PI-M-ZI"
                else:
                    print(
                        "problem in measurements_methods - no ZI or IZ in double heating experiment")
                    return
    for rec in MagRecs:
        if 'er_synthetic_name' in list(rec.keys()) and rec['er_synthetic_name'] != "":
            rec['magic_experiment_name'] = rec['er_synthetic_name'] + \
                ":" + experiment_name
        else:
            rec['magic_experiment_name'] = rec['er_specimen_name'] + \
                ":" + experiment_name
        rec['magic_method_codes'] = rec['magic_method_codes'] + \
            ":" + experiment_name
    return MagRecs


def parse_site(sample, convention, Z):
    """
    parse the site name from the sample name using the specified convention
    """
    convention = str(convention)
    site = sample  # default is that site = sample
#
#
# Sample is final letter on site designation eg:  TG001a (used by SIO lab
# in San Diego)
    if convention == "1":
        return sample[:-1]  # peel off terminal character
#
# Site-Sample format eg:  BG94-1  (used by PGL lab in Beijing)
#
    if convention == "2":
        parts = sample.strip('-').split('-')
        return parts[0]
#
# Sample is XXXX.YY where XXX is site and YY is sample
#
    if convention == "3":
        parts = sample.split('.')
        return parts[0]
#
# Sample is XXXXYYY where XXX is site desgnation and YYY is Z long integer
#
    if convention == "4":
        k = int(Z) - 1
        return sample[0:-k]  # peel off Z characters from site

    if convention == "5":  # sample == site
        return sample

    if convention == "6":  # should be names in orient.txt
        print("-W- Finding names in orient.txt is not currently supported")

    if convention == "7":  # peel off Z characters for site
        k = int(Z)
        return sample[0:k]

    if convention == "8":  # peel off Z characters for site
        return ""

    if convention == "9":  # peel off Z characters for site
        return sample

    print("Error in site parsing routine")
    return


def get_samp_con():
    """
     get sample naming  convention
    """
#
    samp_con, Z = "", ""
    while samp_con == "":
        samp_con = input("""
        Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site is entered under a separate column
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.
            select one:
""")
    #
        if samp_con == "" or samp_con == "1":
            samp_con, Z = "1", 1
        if "4" in samp_con:
            if "-" not in samp_con:
                print("option [4] must be in form 4-Z where Z is an integer")
                samp_con = ""
            else:
                Z = samp_con.split("-")[1]
                samp_con = "4"
        if "7" in samp_con:
            if "-" not in samp_con:
                print("option [7] must be in form 7-Z where Z is an integer")
                samp_con = ""
            else:
                Z = samp_con.split("-")[1]
                samp_con = "7"
        if samp_con.isdigit() == False or int(samp_con) > 7:
            print("Try again\n ")
            samp_con = ""
    return samp_con, Z


def get_tilt(dec_geo, inc_geo, dec_tilt, inc_tilt):
    """
    Function to return the dip direction and dip that would yield the tilt
    corrected direction if applied to the uncorrected direction (geographic
    coordinates)

    Parameters
    ----------
    dec_geo : declination in geographic coordinates
    inc_geo : inclination in geographic coordinates
    dec_tilt : declination in tilt-corrected coordinates
    inc_tilt : inclination in tilt-corrected coordinates

    Returns
    -------
    DipDir, Dip : tuple of dip direction and dip
    """
# strike is horizontal line equidistant from two input directions
    SCart = [0, 0, 0]  # cartesian coordites of Strike
    SCart[2] = 0.  # by definition
    # cartesian coordites of Geographic D
    GCart = dir2cart([dec_geo, inc_geo, 1.])
    TCart = dir2cart([dec_tilt, inc_tilt, 1.])  # cartesian coordites of Tilt D
    X = old_div((TCart[1] - GCart[1]), (GCart[0] - TCart[0]))
    SCart[1] = np.sqrt(old_div(1, (X**2 + 1.)))
    SCart[0] = SCart[1] * X
    SDir = cart2dir(SCart)
    DipDir = (SDir[0] - 90.) % 360.
    DipDir = (SDir[0] + 90.) % 360.
# D is creat circle distance between geo direction and strike
# theta is GCD between geo and tilt (on unit sphere).  use law of cosines
# to get small cirlce between geo and tilt (dip)
    cosd = GCart[0] * SCart[0] + GCart[1] * \
        SCart[1]  # cosine of angle between two
    d = np.arccos(cosd)
    cosTheta = GCart[0] * TCart[0] + GCart[1] * TCart[1] + GCart[2] * TCart[2]
    Dip = (old_div(180., np.pi)) * \
        np.arccos(-(old_div((cosd**2 - cosTheta), np.sin(d)**2)))
    if Dip > 90:
        Dip = -Dip
    return DipDir, Dip
#


def get_azpl(cdec, cinc, gdec, ginc):
    """
     gets azimuth and pl from specimen dec inc (cdec,cinc) and gdec,ginc (geographic)  coordinates
    """
    TOL = 1e-4
    rad = old_div(np.pi, 180.)
    Xp = dir2cart([gdec, ginc, 1.])
    X = dir2cart([cdec, cinc, 1.])
    # find plunge first
    az, pl, zdif, ang = 0., -90., 1., 360.
    while zdif > TOL and pl < 180.:
        znew = X[0] * np.sin(pl * rad) + X[2] * np.cos(pl * rad)
        zdif = abs(Xp[2] - znew)
        pl += .01

    while ang > 0.1 and az < 360.:
        d, i = dogeo(cdec, cinc, az, pl)
        ang = angle([gdec, ginc], [d, i])
        az += .01
    return az - .01, pl - .01


def set_priorities(SO_methods, ask):
    """
     figure out which sample_azimuth to use, if multiple orientation methods
    """
    # if ask set to 1, then can change priorities
    SO_methods = [meth.strip() for meth in SO_methods]
    SO_defaults = ['SO-SUN', 'SO-GPS-DIFF', 'SO-SUN-SIGHT', 'SO-SIGHT', 'SO-SIGHT-BS',
                   'SO-CMD-NORTH', 'SO-MAG', 'SO-SM', 'SO-REC', 'SO-V', 'SO-CORE', 'SO-NO']
    SO_priorities, prior_list = [], []
    if len(SO_methods) >= 1:
        for l in range(len(SO_defaults)):
            if SO_defaults[l] in SO_methods:
                SO_priorities.append(SO_defaults[l])
    pri, change = 0, "1"
    if ask == 1:
        print("""These methods of sample orientation were found:
      They have been assigned a provisional priority (top = zero, last = highest number) """)
        for m in range(len(SO_defaults)):
            if SO_defaults[m] in SO_methods:
                SO_priorities[SO_methods.index(SO_defaults[m])] = pri
                pri += 1
        while change == "1":
            prior_list = SO_priorities
            for m in range(len(SO_methods)):
                print(SO_methods[m], SO_priorities[m])
            change = input("Change these?  1/[0] ")
            if change != "1":
                break
        SO_priorities = []
        for l in range(len(SO_methods)):
            print(SO_methods[l])
            print(" Priority?   ", prior_list)
            pri = int(input())
            SO_priorities.append(pri)
            del prior_list[prior_list.index(pri)]
    return SO_priorities
#
#


def get_EOL(file):
    """
     find EOL of input file (whether mac,PC or unix format)
    """
    f = open(file, 'r')
    firstline = f.read(350)
    EOL = ""
    for k in range(350):
        if firstline[k:k + 2] == "\r\n":
            print(file, ' appears to be a dos file')
            EOL = '\r\n'
            break
    if EOL == "":
        for k in range(350):
            if firstline[k] == "\r":
                print(file, ' appears to be a mac file')
                EOL = '\r'
    if EOL == "":
        print(file, " appears to be a  unix file")
        EOL = '\n'
    f.close()
    return EOL
#


def sortshaw(s, datablock):
    """
     sorts data block in to ARM1,ARM2 NRM,TRM,ARM1,ARM2=[],[],[],[]
     stick  first zero field stuff into first_Z
    """
    for rec in datablock:
        methcodes = rec["magic_method_codes"].split(":")
        step = float(rec["treatment_ac_field"])
        str = float(rec["measurement_magn_moment"])
        if "LT-NO" in methcodes:
            NRM.append([0, str])
        if "LT-T-I" in methcodes:
            TRM.append([0, str])
            field = float(rec["treatment_dc_field"])
        if "LT-AF-I" in methcodes:
            ARM1.append([0, str])
        if "LT-AF-I-2" in methcodes:
            ARM2.append([0, str])
        if "LT-AF-Z" in methcodes:
            if "LP-ARM-AFD" in methcodes:
                ARM1.append([step, str])
            elif "LP-TRM-AFD" in methcodes:
                TRM.append([step, str])
            elif "LP-ARM2-AFD" in methcodes:
                ARM2.append([step, str])
            else:
                NRM.append([step, str])
    cont = 1
    while cont == 1:
        if len(NRM) != len(TRM):
            print("Uneven NRM/TRM steps: ")
            NRM, TRM, cont = cleanup(TRM, NRM)
        else:
            cont = 0
    cont = 1
    while cont == 1:
        if len(ARM1) != len(ARM2):
            print("Uneven ARM1/ARM2 steps: ")
            ARM1, ARM2, cont = cleanup(ARM2, ARM1)
        else:
            cont = 0
#
# final check
#
    if len(NRM) != len(TRM) or len(ARM1) != len(ARM2):
        print(len(NRM), len(TRM), len(ARM1), len(ARM2))
        print(" Something wrong with this specimen! Better fix it or delete it ")
        input(" press return to acknowledge message")
# now do the ratio to "fix" NRM/TRM data
# a
    TRM_ADJ = []
    for kk in range(len(TRM)):
        step = TRM[kk][0]
        for k in range(len(ARM1)):
            if ARM1[k][0] == step:
                TRM_ADJ.append([step, TRM[kk][1] * ARM1[k][1] / ARM2[k][1]])
                break
    shawblock = (NRM, TRM, ARM1, ARM2, TRM_ADJ)
    return shawblock, field
#
#


def makelist(List):
    """
     makes a colon delimited list from List
    """
    clist = ""
    for element in List:
        clist = clist + element + ":"
    return clist[:-1]


def getvec(gh, lat, lon):
    """
    Evaluates the vector at a given latitude and longitude for a specified
    set of coefficients

    Parameters
    ----------
    gh : a list of gauss coefficients
    lat : latitude of location
    long : longitude of location

    Returns
    -------
    vec : direction in [dec, inc, intensity]
    """
    sv = []
    pad = 120 - len(gh)
    for x in range(pad):
        gh.append(0.)
    for x in range(len(gh)):
        sv.append(0.)
#! convert to colatitude for MB routine
    itype = 1
    colat = 90. - lat
    date, alt = 2000., 0.  # use a dummy date and altitude
    x, y, z, f = magsyn(gh, sv, date, date, itype, alt, colat, lon)
    vec = cart2dir([x, y, z])
    vec[2] = f
    return vec


def s_l(l, alpha):
    """
    get sigma as a function of degree l from Constable and Parker (1988)
    """
    a2 = alpha**2
    c_a = 0.547
    s_l = np.sqrt(old_div(((c_a**(2. * l)) * a2), ((l + 1.) * (2. * l + 1.))))
    return s_l
#


def mktk03(terms, seed, G2, G3):
    """
    generates a list of gauss coefficients drawn from the TK03.gad distribution
    """
# random.seed(n)
    p = 0
    n = seed
    gh = []
    g10, sfact, afact = -18e3, 3.8, 2.4
    g20 = G2 * g10
    g30 = G3 * g10
    alpha = old_div(g10, afact)
    s1 = s_l(1, alpha)
    s10 = sfact * s1
    gnew = random.normal(g10, s10)
    if p == 1:
        print(1, 0, gnew, 0)
    gh.append(gnew)
    gh.append(random.normal(0, s1))
    gnew = gh[-1]
    gh.append(random.normal(0, s1))
    hnew = gh[-1]
    if p == 1:
        print(1, 1, gnew, hnew)
    for l in range(2, terms + 1):
        for m in range(l + 1):
            OFF = 0.0
            if l == 2 and m == 0:
                OFF = g20
            if l == 3 and m == 0:
                OFF = g30
            s = s_l(l, alpha)
            j = (l - m) % 2
            if j == 1:
                s = s * sfact
            gh.append(random.normal(OFF, s))
            gnew = gh[-1]
            if m == 0:
                hnew = 0
            else:
                gh.append(random.normal(0, s))
                hnew = gh[-1]
            if p == 1:
                print(l, m, gnew, hnew)
    return gh
#
#


def pinc(lat):
    """
    calculate paleoinclination from latitude using dipole formula: tan(I) = 2tan(lat)
    Parameters
    ________________

    lat : either a single value or an array of latitudes

    Returns
    -------

    array of inclinations
    """
    tanl = np.tan(np.radians(lat))
    inc = np.arctan(2. * tanl)
    return np.degrees(inc)
#


def plat(inc):
    """
    calculate paleolatitude from inclination using dipole formula: tan(I) = 2tan(lat)
    Parameters
    ________________

    inc : either a single value or an array of inclinations

    Returns
    -------

    array of latitudes
    """
    tani = np.tan(np.radians(inc))
    lat = np.arctan(tani/2.)
    return np.degrees(lat)
#
#


def pseudo(DIs, random_seed=None):
    """
    Draw a bootstrap sample of directions returning as many bootstrapped samples
    as in the input directions

    Parameters
    ----------
    DIs : nested list of dec, inc lists (known as a di_block)
    random_seed : set random seed for reproducible number generation (default is None)

    Returns
    -------
    Bootstrap_directions : nested list of dec, inc lists that have been
    bootstrapped resampled
    """
    if random_seed != None:
        np.random.seed(random_seed)
    Inds = np.random.randint(len(DIs), size=len(DIs))
    D = np.array(DIs)
    return D[Inds]


def di_boot(DIs, nb=5000):
    """
     returns bootstrap means  for Directional data
     Parameters
     _________________
     DIs : nested list of Dec,Inc pairs
     nb : number of bootstrap pseudosamples

     Returns
    -------
     BDIs:   nested list of bootstrapped mean Dec,Inc pairs
    """
#
# now do bootstrap to collect BDIs  bootstrap means
#
    BDIs = []  # number of bootstraps, list of bootstrap directions
#

    for k in range(nb):  # repeat nb times
        #        if k%50==0:print k,' out of ',nb
        pDIs = pseudo(DIs)  # get a pseudosample
        bfpars = fisher_mean(pDIs)  # get bootstrap mean bootstrap sample
        BDIs.append([bfpars['dec'], bfpars['inc']])
    return BDIs


def dir_df_boot(dir_df, nb=5000, par=False):
    """
    Performs a bootstrap for direction DataFrame with optional parametric bootstrap

    Parameters
    _________
    dir_df : Pandas DataFrame with columns:
        dir_dec : mean declination
        dir_inc : mean inclination
      Required for parametric bootstrap
        dir_n : number of data points in mean
        dir_k : Fisher k statistic for mean
    nb : number of bootstraps, default is 5000
    par : if True, do a parameteric bootstrap

    Returns
     _______
     BDIs:   nested list of bootstrapped mean Dec,Inc pairs
    """
    N = dir_df.dir_dec.values.shape[0]  # number of data points
    BDIs = []
    for k in range(nb):
        pdir_df = dir_df.sample(n=N, replace=True)  # bootstrap pseudosample
        pdir_df.reset_index(inplace=True)  # reset the index
        if par:  # do a parametric bootstrap
            for i in pdir_df.index:  # set through the pseudosample
                n = pdir_df.loc[i, 'dir_n']  # get number of samples/site
                # get ks for each sample
                ks = np.ones(shape=n)*pdir_df.loc[i, 'dir_k']
                # draw a fisher distributed set of directions
                decs, incs = fshdev(ks)
                di_block = np.column_stack((decs, incs))
                #  rotate them to the mean
                di_block = dodirot_V(
                    di_block, pdir_df.loc[i, 'dir_dec'], pdir_df.loc[i, 'dir_inc'])
                # get the new mean direction for the pseudosample
                fpars = fisher_mean(di_block)
                # replace the pseudo sample mean direction
                pdir_df.loc[i, 'dir_dec'] = fpars['dec']
                pdir_df.loc[i, 'dir_inc'] = fpars['inc']
        # get bootstrap mean bootstrap sample
        bfpars = dir_df_fisher_mean(pdir_df)
        BDIs.append([bfpars['dec'], bfpars['inc']])
    return BDIs


def dir_df_fisher_mean(dir_df):
    """
    calculates fisher mean for Pandas data frame

    Parameters
    __________
    dir_df: pandas data frame with columns:
        dir_dec : declination
        dir_inc : inclination
    Returns
    -------
    fpars : dictionary containing the Fisher mean and statistics
        dec : mean declination
        inc : mean inclination
        r : resultant vector length
        n : number of data points
        k : Fisher k value
        csd : Fisher circular standard deviation
        alpha95 : Fisher circle of 95% confidence
    """
    N = dir_df.dir_dec.values.shape[0]  # number of data points
    fpars = {}
    if N < 2:
        return fpars
    dirs = dir_df[['dir_dec', 'dir_inc']].values
    X = dir2cart(dirs).transpose()
    Xbar = np.array([X[0].sum(), X[1].sum(), X[2].sum()])
    R = np.sqrt(Xbar[0]**2+Xbar[1]**2+Xbar[2]**2)
    Xbar = Xbar/R
    dir = cart2dir(Xbar)
    fpars["dec"] = dir[0]
    fpars["inc"] = dir[1]
    fpars["n"] = N
    fpars["r"] = R
    if N != R:
        k = (N - 1.) / (N - R)
        fpars["k"] = k
        csd = 81./np.sqrt(k)
    else:
        fpars['k'] = 'inf'
        csd = 0.
    b = 20.**(1./(N - 1.)) - 1
    a = 1 - b * (N - R) / R
    if a < -1:
        a = -1
    a95 = np.degrees(np.arccos(a))
    fpars["alpha95"] = a95
    fpars["csd"] = csd
    if a < 0:
        fpars["alpha95"] = 180.0
    return fpars


def pseudosample(x):
    """
     draw a bootstrap sample of x
    """
#
    BXs = []
    for k in range(len(x)):
        ind = random.randint(0, len(x) - 1)
        BXs.append(x[ind])
    return BXs


def get_plate_data(plate):
    """
    returns the pole list for a given plate

    Parameters
    ----------
    plate : string (options: AF, ANT, AU, EU, GL, IN, NA, SA)

    Returns
    ---------
    apwp : string with format
        0.0        90.00    0.00
        1.0        88.38  182.20
        2.0        86.76  182.20
        ...

    """
    from . import poles
    apwp = poles.get_apwp(plate)
    return apwp
#


def bc02(data):
    """
    get APWP from Besse and Courtillot 2002 paper

    Parameters
    ----------
    Takes input as [plate, site_lat, site_lon, age]
    plate : string (options: AF, ANT, AU, EU, GL, IN, NA, SA)
    site_lat : float
    site_lon : float
    age : float in Myr

    Returns
    ----------

    """

    plate, site_lat, site_lon, age = data[0], data[1], data[2], data[3]
    apwp = get_plate_data(plate)
    recs = apwp.split()
    #
    # put it into  usable form in plate_data
    #
    k, plate_data = 0, []
    while k < len(recs) - 3:
        rec = [float(recs[k]), float(recs[k + 1]), float(recs[k + 2])]
        plate_data.append(rec)
        k = k + 3

    #
    # find the right pole for the age
    #
    for i in range(len(plate_data)):
        if age >= plate_data[i][0] and age <= plate_data[i + 1][0]:
            if (age - plate_data[i][0]) < (plate_data[i][0] - age):
                rec = i
            else:
                rec = i + 1
            break
    pole_lat = plate_data[rec][1]
    pole_lon = plate_data[rec][2]
    return pole_lat, pole_lon


def linreg(x, y):
    """
    does a linear regression
    """
    if len(x) != len(y):
        print('x and y must be same length')
        return
    xx, yy, xsum, ysum, xy, n, sum = 0, 0, 0, 0, 0, len(x), 0
    linpars = {}
    for i in range(n):
        xx += x[i] * x[i]
        yy += y[i] * y[i]
        xy += x[i] * y[i]
        xsum += x[i]
        ysum += y[i]
        xsig = np.sqrt(old_div((xx - old_div(xsum**2, n)), (n - 1.)))
        ysig = np.sqrt(old_div((yy - old_div(ysum**2, n)), (n - 1.)))
    linpars['slope'] = old_div(
        (xy - (xsum * ysum / n)), (xx - old_div((xsum**2), n)))
    linpars['b'] = old_div((ysum - linpars['slope'] * xsum), n)
    linpars['r'] = old_div((linpars['slope'] * xsig), ysig)
    for i in range(n):
        a = y[i] - linpars['b'] - linpars['slope'] * x[i]
        sum += a
    linpars['sigma'] = old_div(sum, (n - 2.))
    linpars['n'] = n
    return linpars


def squish(incs, f):
    """
    returns 'flattened' inclination, assuming factor, f and King (1955) formula:
    tan (I_o) = f tan (I_f)

    Parameters
    __________
    incs : array of inclination (I_f)  data to flatten
    f : flattening factor

    Returns
    _______
    I_o :  inclinations after flattening
    """
    incs = np.radians(incs)
    I_o = f * np.tan(incs)  # multiply tangent by flattening factor
    return np.degrees(np.arctan(I_o))


def unsquish(incs, f):
    """
    returns 'unflattened' inclination, assuming factor, f and King (1955) formula:
    tan (I_o) = tan (I_f)/f

    Parameters
    __________
    incs : array of inclination (I_f)  data to unflatten
    f : flattening factor

    Returns
    _______
    I_o :  inclinations after unflattening
    """
    incs = np.radians(incs)
    I_o = np.tan(incs)/f  # divide tangent by flattening factor
    return np.degrees(np.arctan(I_o))


def get_ts(ts):
    """
    returns GPTS timescales.
    options are:  ck95, gts04, and gts12
    returns timescales and Chron labels
    """
    if ts == 'ck95':
        TS = [0, 0.780, 0.990, 1.070, 1.770, 1.950, 2.140, 2.150, 2.581, 3.040, 3.110, 3.220, 3.330, 3.580, 4.180, 4.290, 4.480, 4.620, 4.800, 4.890, 4.980, 5.230, 5.894, 6.137, 6.269, 6.567, 6.935, 7.091, 7.135, 7.170, 7.341, 7.375, 7.432, 7.562, 7.650, 8.072, 8.225, 8.257, 8.699, 9.025, 9.230, 9.308, 9.580, 9.642, 9.740, 9.880, 9.920, 10.949, 11.052, 11.099, 11.476, 11.531, 11.935, 12.078, 12.184, 12.401, 12.678, 12.708, 12.775, 12.819, 12.991, 13.139, 13.302, 13.510, 13.703, 14.076, 14.178, 14.612, 14.800, 14.888, 15.034, 15.155, 16.014, 16.293, 16.327, 16.488, 16.556, 16.726, 17.277, 17.615, 18.281, 18.781, 19.048, 20.131, 20.518, 20.725, 20.996, 21.320, 21.768, 21.859, 22.151, 22.248, 22.459, 22.493, 22.588,
              22.750, 22.804, 23.069, 23.353, 23.535, 23.677, 23.800, 23.999, 24.118, 24.730, 24.781, 24.835, 25.183, 25.496, 25.648, 25.823, 25.951, 25.992, 26.554, 27.027, 27.972, 28.283, 28.512, 28.578, 28.745, 29.401, 29.662, 29.765, 30.098, 30.479, 30.939, 33.058, 33.545, 34.655, 34.940, 35.343, 35.526, 35.685, 36.341, 36.618, 37.473, 37.604, 37.848, 37.920, 38.113, 38.426, 39.552, 39.631, 40.130, 41.257, 41.521, 42.536, 43.789, 46.264, 47.906, 49.037, 49.714, 50.778, 50.946, 51.047, 51.743, 52.364, 52.663, 52.757, 52.801, 52.903, 53.347, 55.904, 56.391, 57.554, 57.911, 60.920, 61.276, 62.499, 63.634, 63.976, 64.745, 65.578, 67.610, 67.735, 68.737, 71.071, 71.338, 71.587, 73.004, 73.291, 73.374, 73.619, 79.075, 83.000]
        Labels = [['C1n', 0], ['C1r', 0.78], ['C2', 1.77], ['C2An', 2.581], ['C2Ar', 3.58], ['C3n', 4.18], ['C3r', 5.23], ['C3An', 5.894], ['C3Ar', 6.567], ['C3Bn', 6.935], ['C3Br', 7.091], ['C4n', 7.432], ['C4r', 8.072], ['C4An', 8.699], ['C4Ar', 9.025], ['C5n', 9.74], ['C5r', 10.949], ['C5An', 11.935], ['C5Ar', 12.401], ['C5AAn', 12.991], ['C5AAr', 13.139], ['C5ABn', 13.302], ['C5ABr', 13.51], ['C5ACn', 13.703], ['C5ACr', 14.076], ['C5ADn', 14.178], ['C5ADr', 14.612], ['C5Bn', 14.8], ['C5Br', 15.155], ['C5Cn', 16.014], ['C5Cr', 16.726], ['C5Dn', 17.277], ['C5Dr', 17.615], ['C5En', 18.281], ['C5Er', 18.781], ['C6n', 19.048], ['C6r', 20.131], ['C6An', 20.518], ['C6Ar', 21.32], ['C6AAn', 21.768], ['C6AAr', 21.859], ['C6Bn', 22.588], ['C6Br', 23.069], ['C6Cn', 23.353], ['C6Cr', 24.118], ['C7n', 24.73], ['C7r', 25.183], ['C7A', 25.496], ['C8n', 25.823], ['C8r', 26.554], [
            'C9n', 27.027], ['C9r', 27.972], ['C10n', 28.283], ['C10r', 28.745], ['C11n', 29.401], ['C11r', 30.098], ['C12n', 30.479], ['C12r', 30.939], ['C13n', 33.058], ['C13r', 33.545], ['C15n', 34.655], ['C15r', 34.94], ['C16n', 35.343], ['C16r', 36.341], ['C17n', 36.618], ['C17r', 38.113], ['C18n', 38.426], ['C18r', 40.13], ['C19n', 41.257], ['C19r', 41.521], ['C20n', 42.536], ['C20r', 43.789], ['C21n', 46.264], ['C21r', 47.906], ['C22n', 49.037], ['C22r', 49.714], ['C23n', 50.778], ['C23r', 51.743], ['C24n', 52.364], ['C24r', 53.347], ['C25n', 55.904], ['C25r', 56.391], ['C26n', 57.554], ['C26r', 57.911], ['C27n', 60.92], ['C27r', 61.276], ['C28n', 62.499], ['C28r', 63.634], ['C29n', 63.976], ['C29r', 64.745], ['C30n', 65.578], ['C30r', 67.61], ['C31n', 67.735], ['C31r', 68.737], ['C32n', 71.071], ['C32r', 73.004], ['C33n', 73.619], ['C33r', 79.075], ['C34n', 83]]
        return TS, Labels
    if ts == 'gts04':
        TS = [0, 0.781, 0.988, 1.072, 1.778, 1.945, 2.128, 2.148, 2.581, 3.032, 3.116, 3.207, 3.33, 3.596, 4.187, 4.3, 4.493, 4.631, 4.799, 4.896, 4.997, 5.235, 6.033, 6.252, 6.436, 6.733, 7.14, 7.212, 7.251, 7.285, 7.454, 7.489, 7.528, 7.642, 7.695, 8.108, 8.254, 8.3, 8.769, 9.098, 9.312, 9.409, 9.656, 9.717, 9.779, 9.934, 9.987, 11.04, 11.118, 11.154, 11.554, 11.614, 12.014, 12.116, 12.207, 12.415, 12.73, 12.765, 12.82, 12.878, 13.015, 13.183, 13.369, 13.605, 13.734, 14.095, 14.194, 14.581, 14.784, 14.877, 15.032, 15.16, 15.974, 16.268, 16.303, 16.472, 16.543, 16.721, 17.235, 17.533, 17.717, 17.74, 18.056, 18.524, 18.748, 20, 20.04, 20.213, 20.439, 20.709, 21.083, 21.159, 21.403, 21.483, 21.659, 21.688, 21.767,
              21.936, 21.992, 22.268, 22.564, 22.754, 22.902, 23.03, 23.249, 23.375, 24.044, 24.102, 24.163, 24.556, 24.915, 25.091, 25.295, 25.444, 25.492, 26.154, 26.714, 27.826, 28.186, 28.45, 28.525, 28.715, 29.451, 29.74, 29.853, 30.217, 30.627, 31.116, 33.266, 33.738, 34.782, 35.043, 35.404, 35.567, 35.707, 36.276, 36.512, 37.235, 37.345, 37.549, 37.61, 37.771, 38.032, 38.975, 39.041, 39.464, 40.439, 40.671, 41.59, 42.774, 45.346, 47.235, 48.599, 49.427, 50.73, 50.932, 51.057, 51.901, 52.648, 53.004, 53.116, 53.167, 53.286, 53.808, 56.665, 57.18, 58.379, 58.737, 61.65, 61.983, 63.104, 64.128, 64.432, 65.118, 65.861, 67.696, 67.809, 68.732, 70.961, 71.225, 71.474, 72.929, 73.231, 73.318, 73.577, 79.543, 84]
        Labels = [['C1n', 0.000], ['C1r', 0.781], ['C2', 1.778], ['C2An', 2.581], ['C2Ar', 3.596], ['C3n', 4.187], ['C3r', 5.235], ['C3An', 6.033], ['C3Ar', 6.733], ['C3Bn', 7.140], ['C3Br', 7.212], ['C4n', 7.528], ['C4r', 8.108], ['C4An', 8.769], ['C4Ar', 9.098], ['C5n', 9.779], ['C5r', 11.040], ['C5An', 12.014], ['C5Ar', 12.415], ['C5AAn', 13.015], ['C5AAr', 13.183], ['C5ABn', 13.369], ['C5ABr', 13.605], ['C5ACn', 13.734], ['C5ACr', 14.095], ['C5ADn', 14.194], ['C5ADr', 14.581], ['C5Bn', 14.784], ['C5Br', 15.160], ['C5Cn', 15.974], ['C5Cr', 16.721], ['C5Dn', 17.235], ['C5Dr', 17.533], ['C5En', 18.056], ['C5Er', 18.524], ['C6n', 18.748], ['C6r', 19.772], ['C6An', 20.040], ['C6Ar', 20.709], ['C6AAn', 21.083], ['C6AAr', 21.159], ['C6Bn', 21.767], ['C6Br', 22.268], ['C6Cn', 22.564], ['C6Cr', 23.375], ['C7n', 24.044], ['C7r', 24.556], ['C7A', 24.919], ['C8n', 25.295], [
            'C8r', 26.154], ['C9n', 26.714], ['C9r', 27.826], ['C10n', 28.186], ['C11n', 29.451], ['C11r', 30.217], ['C12n', 30.627], ['C12r', 31.116], ['C13n', 33.266], ['C13r', 33.738], ['C15n', 34.782], ['C15r', 35.043], ['C16n', 35.404], ['C16r', 36.276], ['C17n', 36.512], ['C17r', 37.771], ['C18n', 38.032], ['C18r', 39.464], ['C19n', 40.439], ['C19r', 40.671], ['C20n', 41.590], ['C20r', 42.774], ['C21n', 45.346], ['C21r', 47.235], ['C22n', 48.599], ['C22r', 49.427], ['C23n', 50.730], ['C23r', 51.901], ['C24n', 52.648], ['C24r', 53.808], ['C25n', 56.665], ['C25r', 57.180], ['C26n', 58.379], ['C26r', 58.737], ['C27n', 61.650], ['C27r', 61.938], ['C28n', 63.104], ['C28r', 64.128], ['C29n', 64.432], ['C29r', 65.118], ['C30n', 65.861], ['C30r', 67.696], ['C31n', 67.809], ['C31r', 68.732], ['C32n', 70.961], ['C32r', 72.929], ['C33n', 73.577], ['C33r', 79.543], ['C34n', 84.000]]
        return TS, Labels
    if ts == 'gts12':
        TS = [0, 0.781, 0.988, 1.072, 1.173, 1.185, 1.778, 1.945, 2.128, 2.148, 2.581, 3.032, 3.116, 3.207, 3.330, 3.596, 4.187, 4.300, 4.493, 4.631, 4.799, 4.896, 4.997, 5.235, 6.033, 6.252, 6.436, 6.733, 7.140, 7.212, 7.251, 7.285, 7.454, 7.489, 7.528, 7.642, 7.695, 8.108, 8.254, 8.300, 8.771, 9.105, 9.311, 9.426, 9.647, 9.721, 9.786, 9.937, 9.984, 11.056, 11.146, 11.188, 11.592, 11.657, 12.049, 12.174, 12.272, 12.474, 12.735, 12.770, 12.829, 12.887, 13.032, 13.183, 13.363, 13.608, 13.739, 14.070, 14.163, 14.609, 14.775, 14.870, 15.032, 15.160, 15.974, 16.268, 16.303, 16.472, 16.543, 16.721, 17.235, 17.533, 17.717, 17.740, 18.056, 18.524, 18.748, 19.722, 20.040, 20.213, 20.439, 20.709, 21.083, 21.159, 21.403, 21.483, 21.659,
              21.688, 21.767, 21.936, 21.992, 22.268, 22.564, 22.754, 22.902, 23.030, 23.233, 23.295, 23.962, 24.000, 24.109, 24.474, 24.761, 24.984, 25.099, 25.264, 25.304, 25.987, 26.420, 27.439, 27.859, 28.087, 28.141, 28.278, 29.183, 29.477, 29.527, 29.970, 30.591, 31.034, 33.157, 33.705, 34.999, 35.294, 35.706, 35.892, 36.051, 36.700, 36.969, 37.753, 37.872, 38.093, 38.159, 38.333, 38.615, 39.627, 39.698, 40.145, 41.154, 41.390, 42.301, 43.432, 45.724, 47.349, 48.566, 49.344, 50.628, 50.835, 50.961, 51.833, 52.620, 53.074, 53.199, 53.274, 53.416, 53.983, 57.101, 57.656, 58.959, 59.237, 62.221, 62.517, 63.494, 64.667, 64.958, 65.688, 66.398, 68.196, 68.369, 69.269, 71.449, 71.689, 71.939, 73.649, 73.949, 74.049, 74.309, 79.900, 83.64]
        Labels = [['C1n', 0.000], ['C1r', 0.781], ['C2n', 1.778], ['C2r', 1.945], ['C2An', 2.581], ['C2Ar', 3.596], ['C3n', 4.187], ['C3r', 5.235], ['C3An', 6.033], ['C3Ar', 6.733], ['C3Bn', 7.140], ['C3Br', 7.212], ['C4n', 7.528], ['C4r', 8.108], ['C4An', 8.771], ['C4Ar', 9.105], ['C5n', 9.786], ['C5r', 11.056], ['C5An', 12.049], ['C5Ar', 12.474], ['C5AAn', 13.032], ['C5AAr', 13.183], ['C5ABn', 13.363], ['C5ABr', 13.608], ['C5ACn', 13.739], ['C5ACr', 14.070], ['C5ADn', 14.163], ['C5ADr', 14.609], ['C5Bn', 14.775], ['C5Br', 15.160], ['C5Cn', 15.974], ['C5Cr', 16.721], ['C5Dn', 17.235], ['C5Dr', 17.533], ['C5En', 18.056], ['C5Er', 18.524], ['C6n', 18.748], ['C6r', 19.722], ['C6An', 20.040], ['C6Ar', 20.709], ['C6AAn', 21.083], ['C6AAr', 21.159], ['C6Bn', 21.767], ['C6Br', 22.268], ['C6Cn', 22.564], ['C6Cr', 23.295], ['C7n', 23.962], ['C7r', 24.474], ['C7An', 24.761], ['C7Ar', 24.984], ['C8n', 25.099], [
            'C8r', 25.987], ['C9n', 26.420], ['C9r', 27.439], ['C10n', 27.859], ['C10r', 28.278], ['C11n', 29.183], ['C11r', 29.970], ['C12n', 30.591], ['C12r', 31.034], ['C13n', 33.157], ['C13r', 33.705], ['C15n', 34.999], ['C15r', 35.294], ['C16n', 35.706], ['C16r', 36.700], ['C17n', 36.969], ['C17r', 38.333], ['C18n', 38.615], ['C18r', 40.145], ['C19n', 41.154], ['C19r', 41.390], ['C20n', 42.301], ['C20r', 43.432], ['C21n', 45.724], ['C21r', 47.349], ['C22n', 48.566], ['C22r', 49.344], ['C23n', 50.628], ['C23r', 51.833], ['C24n', 52.620], ['C24r', 53.983], ['C25n', 57.101], ['C25r', 57.656], ['C26n', 58.959], ['C26r', 59.237], ['C27n', 62.221], ['C27r', 62.517], ['C28n', 63.494], ['C28r', 64.667], ['C29n', 64.958], ['C29r', 65.688], ['C30n', 66.398], ['C30r', 68.196], ['C31n', 68.369], ['C31r', 69.269], ['C32n', 71.449], ['C32r', 73.649], ['C33n', 74.309], ['C33r', 79.900], ['C34n', 83.64]]
        return TS, Labels
    print("Time Scale Option Not Available")
    return


def execute(st, **kwargs):
    """
    Work around for Python3 exec function which doesn't allow changes to the local namespace because of scope.
    This breaks a lot of the old functionality in the code which was origionally in Python2. So this function
    runs just like exec except that it returns the output of the input statement to the local namespace. It may
    break if you start feeding it multiline monoliths of statements (haven't tested) but you shouldn't do that
    anyway (bad programming).

    Parameters
    -----------
    st : the statement you want executed and for which you want the return
    kwargs : anything that may need to be in this namespace to execute st

    Returns
    -------
    The return value of executing the input statement
    """
    namespace = kwargs
    exec("b = {}".format(st), namespace)
    return namespace['b']

# Functions for dealing with acceptance criteria


def initialize_acceptance_criteria(**kwargs):
    '''
    initialize acceptance criteria with NULL values for thellier_gui and demag_gui

    acceptance criteria format is doctionaries:

    acceptance_criteria={}
        acceptance_criteria[crit]={}
            acceptance_criteria[crit]['category']=
            acceptance_criteria[crit]['criterion_name']=
            acceptance_criteria[crit]['value']=
            acceptance_criteria[crit]['threshold_type']
            acceptance_criteria[crit]['decimal_points']

   'category':
       'DE-SPEC','DE-SAMP'..etc
   'criterion_name':
       MagIC name
   'value':
        a number (for 'regular criteria')
        a string (for 'flag')
        1 for True (if criteria is bullean)
        0 for False (if criteria is bullean)
        -999 means N/A
   'threshold_type':
       'low'for low threshold value
       'high'for high threshold value
        [flag1.flag2]: for flags
        'bool' for boolean flags (can be 'g','b' or True/Flase or 1/0)
   'decimal_points':
       number of decimal points in rounding
       (this is used in displaying criteria in the dialog box)
       -999 means Exponent with 3 descimal points for floats and string for string
    '''

    acceptance_criteria = {}
    # --------------------------------
    # 'DE-SPEC'
    # --------------------------------
    # low cutoff value
    category = 'DE-SPEC'
    for crit in ['specimen_n']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        acceptance_criteria[crit]['decimal_points'] = 0

    # high cutoff value
    category = 'DE-SPEC'
    for crit in ['specimen_mad', 'specimen_dang', 'specimen_alpha95']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "high"
        acceptance_criteria[crit]['decimal_points'] = 1

    # flag
    for crit in ['specimen_direction_type']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        if crit == 'specimen_direction_type':
            acceptance_criteria[crit]['threshold_type'] = ['l', 'p']
        if crit == 'specimen_polarity':
            acceptance_criteria[crit]['threshold_type'] = [
                'n', 'r', 't', 'e', 'i']
        acceptance_criteria[crit]['decimal_points'] = -999

    # --------------------------------
    # 'DE-SAMP'
    # --------------------------------

    # low cutoff value
    category = 'DE-SAMP'
    for crit in ['sample_n', 'sample_n_lines', 'sample_n_planes']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        acceptance_criteria[crit]['decimal_points'] = 0

    # high cutoff value
    category = 'DE-SAMP'
    for crit in ['sample_r', 'sample_alpha95', 'sample_sigma', 'sample_k', 'sample_tilt_correction']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "high"
        if crit in ['sample_tilt_correction']:
            acceptance_criteria[crit]['decimal_points'] = 0
        elif crit in ['sample_alpha95']:
            acceptance_criteria[crit]['decimal_points'] = 1
        else:
            acceptance_criteria[crit]['decimal_points'] = -999

    # flag
    for crit in ['sample_direction_type', 'sample_polarity']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        if crit == 'sample_direction_type':
            acceptance_criteria[crit]['threshold_type'] = ['l', 'p']
        if crit == 'sample_polarity':
            acceptance_criteria[crit]['threshold_type'] = [
                'n', 'r', 't', 'e', 'i']
        acceptance_criteria[crit]['decimal_points'] = -999

    # --------------------------------
    # 'DE-SITE'
    # --------------------------------

    # low cutoff value
    category = 'DE-SITE'
    for crit in ['site_n', 'site_n_lines', 'site_n_planes']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        acceptance_criteria[crit]['decimal_points'] = 0

    # high cutoff value
    for crit in ['site_k', 'site_r', 'site_alpha95', 'site_sigma', 'site_tilt_correction']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "high"
        if crit in ['site_tilt_correction']:
            acceptance_criteria[crit]['decimal_points'] = 0
        else:
            acceptance_criteria[crit]['decimal_points'] = 1

    # flag
    for crit in ['site_direction_type', 'site_polarity']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        if crit == 'site_direction_type':
            acceptance_criteria[crit]['threshold_type'] = ['l', 'p']
        if crit == 'site_polarity':
            acceptance_criteria[crit]['threshold_type'] = [
                'n', 'r', 't', 'e', 'i']
        acceptance_criteria[crit]['decimal_points'] = -999

    # --------------------------------
    # 'DE-STUDY'
    # --------------------------------
    category = 'DE-STUDY'
    # low cutoff value
    for crit in ['average_k', 'average_n', 'average_nn', 'average_nnn', 'average_r']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        if crit in ['average_n', 'average_nn', 'average_nnn']:
            acceptance_criteria[crit]['decimal_points'] = 0
        elif crit in ['average_alpha95']:
            acceptance_criteria[crit]['decimal_points'] = 1
        else:
            acceptance_criteria[crit]['decimal_points'] = -999

    # high cutoff value
    for crit in ['average_alpha95', 'average_sigma']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "high"
        if crit in ['average_alpha95']:
            acceptance_criteria[crit]['decimal_points'] = 1
        else:
            acceptance_criteria[crit]['decimal_points'] = -999

    # --------------------------------
    # 'IE-SPEC' (a long list from SPD.v.1.0)
    # --------------------------------
    category = 'IE-SPEC'

    # low cutoff value
    for crit in ['specimen_int_n', 'specimen_f', 'specimen_fvds', 'specimen_frac', 'specimen_q', 'specimen_w', 'specimen_r_sq', 'specimen_int_ptrm_n',
                 'specimen_int_ptrm_tail_n', 'specimen_ac_n']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        acceptance_criteria[crit]['decimal_points'] = 0
        if crit in ['specimen_int_n', 'specimen_int_ptrm_n', 'specimen_int_ptrm_tail_n', 'specimen_ac_n']:
            acceptance_criteria[crit]['decimal_points'] = 0
        elif crit in ['specimen_f', 'specimen_fvds', 'specimen_frac', 'specimen_q']:
            acceptance_criteria[crit]['decimal_points'] = 2
        else:
            acceptance_criteria[crit]['decimal_points'] = -999

    # high cutoff value
    for crit in ['specimen_b_sigma', 'specimen_b_beta', 'specimen_g', 'specimen_gmax', 'specimen_k', 'specimen_k_sse', 'specimen_k_prime', 'specimen_k_prime_sse',
                 'specimen_coeff_det_sq', 'specimen_z', 'specimen_z_md', 'specimen_int_mad', 'specimen_int_mad_anc', 'specimen_int_alpha', 'specimen_alpha', 'specimen_alpha_prime',
                 'specimen_theta', 'specimen_int_dang', 'specimen_int_crm', 'specimen_ptrm', 'specimen_dck', 'specimen_drat', 'specimen_maxdev', 'specimen_cdrat',
                 'specimen_drats', 'specimen_mdrat', 'specimen_mdev', 'specimen_dpal', 'specimen_tail_drat', 'specimen_dtr', 'specimen_md', 'specimen_dt', 'specimen_dac', 'specimen_gamma']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "high"
        if crit in ['specimen_int_mad', 'specimen_int_mad_anc', 'specimen_int_dang', 'specimen_drat', 'specimen_cdrat', 'specimen_drats', 'specimen_tail_drat', 'specimen_dtr', 'specimen_md', 'specimen_dac', 'specimen_gamma']:
            acceptance_criteria[crit]['decimal_points'] = 1
        elif crit in ['specimen_gmax']:
            acceptance_criteria[crit]['decimal_points'] = 2
        elif crit in ['specimen_b_sigma', 'specimen_b_beta', 'specimen_g', 'specimen_k', 'specimen_k_prime']:
            acceptance_criteria[crit]['decimal_points'] = 3
        else:
            acceptance_criteria[crit]['decimal_points'] = -999

    # flags
    for crit in ['specimen_scat']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = 'bool'
        acceptance_criteria[crit]['decimal_points'] = -999

    # --------------------------------
    # 'IE-SAMP'
    # --------------------------------
    category = 'IE-SAMP'

    # low cutoff value
    for crit in ['sample_int_n']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        acceptance_criteria[crit]['decimal_points'] = 0

    # high cutoff value
    for crit in ['sample_int_rel_sigma', 'sample_int_rel_sigma_perc', 'sample_int_sigma', 'sample_int_sigma_perc']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "high"
        if crit in ['sample_int_rel_sigma_perc', 'sample_int_sigma_perc']:
            acceptance_criteria[crit]['decimal_points'] = 1
        else:
            acceptance_criteria[crit]['decimal_points'] = -999

    # --------------------------------
    # 'IE-SITE'
    # --------------------------------
    category = 'IE-SITE'

    # low cutoff value
    for crit in ['site_int_n']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        acceptance_criteria[crit]['decimal_points'] = 0

    # high cutoff value
    for crit in ['site_int_rel_sigma', 'site_int_rel_sigma_perc', 'site_int_sigma', 'site_int_sigma_perc']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "high"
        if crit in ['site_int_rel_sigma_perc', 'site_int_sigma_perc']:
            acceptance_criteria[crit]['decimal_points'] = 1
        else:
            acceptance_criteria[crit]['decimal_points'] = -999

    # --------------------------------
    # 'IE-STUDY'
    # --------------------------------
    category = 'IE-STUDY'
    # low cutoff value
    for crit in ['average_int_n', 'average_int_n', 'average_int_nn', 'average_int_nnn', ]:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        acceptance_criteria[crit]['decimal_points'] = 0

    # high cutoff value
    for crit in ['average_int_rel_sigma', 'average_int_rel_sigma_perc', 'average_int_sigma']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "high"
        if crit in ['average_int_rel_sigma_perc']:
            acceptance_criteria[crit]['decimal_points'] = 1
        else:
            acceptance_criteria[crit]['decimal_points'] = -999

    # --------------------------------
    # 'NPOLE'
    # --------------------------------
    category = 'NPOLE'
    # flags
    for crit in ['site_polarity']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = ['n', 'r']
        acceptance_criteria[crit]['decimal_points'] = -999

    # --------------------------------
    # 'NPOLE'
    # --------------------------------
    category = 'RPOLE'
    # flags
    for crit in ['site_polarity']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = ['n', 'r']
        acceptance_criteria[crit]['decimal_points'] = -999

    # --------------------------------
    # 'VADM'
    # --------------------------------
    category = 'VADM'
    # low cutoff value
    for crit in ['vadm_n']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        if crit in ['vadm_n']:
            acceptance_criteria[crit]['decimal_points'] = 0
        else:
            acceptance_criteria[crit]['decimal_points'] = -999

    # --------------------------------
    # 'VADM'
    # --------------------------------
    category = 'VADM'
    # low cutoff value
    for crit in ['vadm_n']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        acceptance_criteria[crit]['decimal_points'] = 0

    # high cutoff value
    for crit in ['vadm_sigma']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        acceptance_criteria[crit]['decimal_points'] = -999

    # --------------------------------
    # 'VADM'
    # --------------------------------
    category = 'VDM'
    # low cutoff value
    for crit in ['vdm_n']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        acceptance_criteria[crit]['decimal_points'] = 0

    # high cutoff value
    for crit in ['vdm_sigma']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        acceptance_criteria[crit]['decimal_points'] = -999

    # --------------------------------
    # 'VGP'
    # --------------------------------
    category = 'VDM'
    # low cutoff value
    for crit in ['vgp_n']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        acceptance_criteria[crit]['decimal_points'] = 0

    # high cutoff value
    for crit in ['vgp_alpha95', 'vgp_dm', 'vgp_dp', 'vgp_sigma']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        if crit in ['vgp_alpha95']:
            acceptance_criteria[crit]['decimal_points', 'vgp_dm', 'vgp_dp'] = 1
        else:
            acceptance_criteria[crit]['decimal_points'] = -999

    # --------------------------------
    # 'AGE'
    # --------------------------------
    category = 'AGE'
    # low cutoff value
    for crit in ['average_age_min']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "low"
        acceptance_criteria[crit]['decimal_points'] = -999

    # high cutoff value
    for crit in ['average_age_max', 'average_age_sigma']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "high"
        acceptance_criteria[crit]['decimal_points'] = -999

    # flags
    for crit in ['average_age_unit']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = [
            'Ga', 'Ka', 'Ma', 'Years AD (+/-)', 'Years BP', 'Years Cal AD (+/-)', 'Years Cal BP']
        acceptance_criteria[crit]['decimal_points'] = -999

    # --------------------------------
    # 'ANI'
    # --------------------------------
    category = 'ANI'
    # high cutoff value
    for crit in ['anisotropy_alt', 'sample_aniso_mean', 'site_aniso_mean']:  # value is in precent
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = "high"
        acceptance_criteria[crit]['decimal_points'] = 3

    # flags

    for crit in ['specimen_aniso_ftest_flag']:
        acceptance_criteria[crit] = {}
        acceptance_criteria[crit]['category'] = category
        acceptance_criteria[crit]['criterion_name'] = crit
        acceptance_criteria[crit]['value'] = -999
        acceptance_criteria[crit]['threshold_type'] = 'bool'
        acceptance_criteria[crit]['decimal_points'] = -999

    return(acceptance_criteria)


def read_criteria_from_file(path, acceptance_criteria, **kwargs):
    '''
    Read accceptance criteria from magic criteria file
    # old format:
    multiple lines.  pmag_criteria_code defines the type of criteria

    to deal with old format this function reads all the lines and ignore empty cells.
    i.e., the program assumes that in each column there is only one value (in one of the lines)

    special case in the old format:
        specimen_dang has a value and pmag_criteria_code is IE-specimen.
        The program assumes that the user means specimen_int_dang
    # New format for thellier_gui and demag_gui:
    one long line. pmag_criteria_code=ACCEPT

    path is the full path to the criteria file

    the function takes exiting acceptance_criteria
    and updtate it with criteria from file

    output:
    acceptance_criteria={}
    acceptance_criteria[MagIC Variable Names]={}
    acceptance_criteria[MagIC Variable Names]['value']:
        a number for acceptance criteria value
        -999 for N/A
        1/0 for True/False or Good/Bad
    acceptance_criteria[MagIC Variable Names]['threshold_type']:
        "low":  lower cutoff value i.e. crit>=value pass criteria
        "high": high cutoff value i.e. crit<=value pass criteria
        [string1,string2,....]: for flags
    acceptance_criteria[MagIC Variable Names]['decimal_points']:number of decimal points in rounding
            (this is used in displaying criteria in the dialog box)

    '''
    warnings = []
    acceptance_criteria_list = list(acceptance_criteria.keys())
    if 'data_model' in list(kwargs.keys()) and kwargs['data_model'] == 3:
        crit_data = acceptance_criteria  # data already read in
    else:
        crit_data, file_type = magic_read(path)
        if 'criteria' not in file_type:
            if 'empty' in file_type:
                print('-W- No criteria found: {} '.format(path))
            else:
                print(
                    '-W- {} could not be read and may be improperly formatted...'.format(path))
    for rec in crit_data:
        # gather metadata
        metadata_dict = {'pmag_criteria_code': '',
                         'criteria_definition': '', 'er_citation_names': ''}
        for metadata in metadata_dict:
            if metadata in rec:
                metadata_dict[metadata] = rec[metadata]
        # check each record for correct name and compatibility
        for crit in list(rec.keys()):
            if crit == 'anisotropy_ftest_flag' and crit not in list(rec.keys()):
                crit = 'specimen_aniso_ftest_flag'  # convert legacy criterion to 2.5
            rec[crit] = rec[crit].strip('\n')
            if crit in ['pmag_criteria_code', 'criteria_definition', 'magic_experiment_names', 'er_citation_names']:
                continue
            elif rec[crit] == "":
                continue

            # this catches all the ones that are being overwritten
            if crit in acceptance_criteria:
                if acceptance_criteria[crit]['value'] not in [-999, '-999', -999]:

                    print(
                        "-W- You have multiple different criteria that both use column: {}.\nThe last will be used:\n{}.".format(crit, rec))
                    warn_string = 'multiple criteria for column: {} (only last will be used)'.format(
                        crit)
                    if warn_string not in warnings:
                        warnings.append(warn_string)
            if crit == "specimen_dang" and "pmag_criteria_code" in list(rec.keys()) and "IE-SPEC" in rec["pmag_criteria_code"]:
                crit = "specimen_int_dang"
                print("-W- Found backward compatibility problem with selection criteria specimen_dang. Cannot be associated with IE-SPEC. Program assumes that the statistic is specimen_int_dang")
                if 'specimen_int_dang' not in acceptance_criteria:
                    acceptance_criteria["specimen_int_dang"] = {}
                acceptance_criteria["specimen_int_dang"]['value'] = float(
                    rec["specimen_dang"])

            elif crit not in acceptance_criteria_list:
                print(
                    "-W- WARNING: criteria code %s is not supported by PmagPy GUI. please check" % crit)
                acceptance_criteria[crit] = {}
                acceptance_criteria[crit]['value'] = rec[crit]
                acceptance_criteria[crit]['threshold_type'] = "inherited"
                acceptance_criteria[crit]['decimal_points'] = -999
                acceptance_criteria[crit]['category'] = None
            # boolean flag
            elif acceptance_criteria[crit]['threshold_type'] == 'bool':
                if str(rec[crit]) in ['1', 'g', 'True', 'TRUE']:
                    acceptance_criteria[crit]['value'] = True
                else:
                    acceptance_criteria[crit]['value'] = False

            # criteria as flags
            elif type(acceptance_criteria[crit]['threshold_type']) == list:
                if str(rec[crit]) in acceptance_criteria[crit]['threshold_type']:
                    acceptance_criteria[crit]['value'] = str(rec[crit])
                else:
                    print(
                        "-W- WARNING: data %s from criteria code  %s and is not supported by PmagPy GUI. please check" % (crit, rec[crit]))
            elif float(rec[crit]) == -999:
                pass
            else:
                acceptance_criteria[crit]['value'] = float(rec[crit])
            # add in metadata to each record
            acceptance_criteria[crit].update(metadata_dict)
    if "return_warnings" in kwargs:
        return (acceptance_criteria, warnings)
    else:
        return(acceptance_criteria)


def write_criteria_to_file(path, acceptance_criteria, **kwargs):
    bad_vals = ['-999', -999, -999.]
    acceptance_criteria = {k: v for k, v in list(acceptance_criteria.items(
    )) if v.get('value') and v.get('value') not in bad_vals}
    crit_list = list(acceptance_criteria.keys())
    crit_list.sort()
    if 'data_model' in list(kwargs.keys()) and kwargs['data_model'] == 3:
        code_key = 'criterion'
        definition_key = 'description'
        citation_key = 'citations'
    else:
        code_key = 'pmag_criteria_code'
        definition_key = 'criteria_definition'
        citation_key = 'er_citation_names'
    recs = []  # data_model 3 has a list of dictionaries, data_model 2.5 has just one record
    rec = {}
    rec[code_key] = "ACCEPT"
    rec[definition_key] = "acceptance criteria for study"
    rec[citation_key] = "This study"
    for crit in crit_list:
        if 'category' in list(acceptance_criteria[crit].keys()):
            # ignore criteria that are not in MagIc model 2.5 or 3.0
            if acceptance_criteria[crit]['category'] != 'thellier_gui':
                # need to make a list of these dictionaries
                if 'data_model' in list(kwargs.keys()) and kwargs['data_model'] == 3:
                    rec = {}
                    rec[definition_key] = "acceptance criteria for study"
                    rec[citation_key] = "This study"
                    rec[code_key] = "IE-SPEC"
                    if 'sample' in crit:
                        rec[code_key] = "IE-SAMP"
                    if 'site' in crit:
                        rec[code_key] = "IE-SITE"
                    rec[definition_key] = "acceptance criteria for study"
                    rec[citation_key] = "This study"
                    crit3_0 = map_magic.convert_intensity_criteria(
                        'magic3', crit)
                    rec['table_column'] = crit3_0
                    if acceptance_criteria[crit]['threshold_type'] == 'low':
                        op = '>='
                    elif acceptance_criteria[crit]['threshold_type'] == 'high':
                        op = '<='
                    elif acceptance_criteria[crit]['threshold_type'] == 'bool':
                        op = '='
                    else:
                        op = '?'
                    rec['criterion_operation'] = op
                    value_key = 'criterion_value'
                else:
                    value_key = crit

        # fix True/False typoes
                if type(acceptance_criteria[crit]["value"]) == str:
                    if acceptance_criteria[crit]["value"] == "TRUE":
                        acceptance_criteria[crit]["value"] = "True"
                    if acceptance_criteria[crit]["value"] == "FALSE":
                        acceptance_criteria[crit]["value"] = "False"
                if type(acceptance_criteria[crit]["value"]) == str:
                    if acceptance_criteria[crit]["value"] != "-999" and acceptance_criteria[crit]['value'] != "":
                        rec[value_key] = acceptance_criteria[crit]['value']
                elif type(acceptance_criteria[crit]["value"]) == int:
                    if acceptance_criteria[crit]["value"] != -999:
                        rec[value_key] = "%.i" % (
                            acceptance_criteria[crit]["value"])
                    elif type(acceptance_criteria[crit]["value"]) == float:
                        if float(acceptance_criteria[crit]["value"]) == -999:
                            continue
                if 'decimal_points' in acceptance_criteria[crit] in list(acceptance_criteria[crit].keys()):
                    decimal_points = acceptance_criteria[crit]['decimal_points']
                    if decimal_points != -999:
                        val = acceptance_criteria[crit]['value']
                        rec[value_key] = str(round(val, int(decimal_points)))
                        # command="rec[value_key]='%%.%sf'%%(acceptance_criteria[crit]['value'])"%(decimal_points)
                        # exec command
                else:
                    rec[value_key] = str(acceptance_criteria[crit]["value"])
                if type(acceptance_criteria[crit]["value"]) == bool:
                    rec[value_key] = str(acceptance_criteria[crit]["value"])
                # need to make a list of these dictionaries
                if 'data_model' in list(kwargs.keys()) and kwargs['data_model'] == 3:
                    if eval(rec[value_key]) != -999:
                        recs.append(rec)
            else:
                print("-W- WARNING: statistic {} not written to file".format(crit))
    # need to make a list of these dictionaries
    if 'data_model' in list(kwargs.keys()) and kwargs['data_model'] == 3:
        if 'prior_crits' in list(kwargs.keys()):
            prior_crits = kwargs['prior_crits']
            included = {rec['table_column'] for rec in recs}
            for rec in prior_crits:
                if 'criterion' in list(rec.keys()) and 'IE-' not in rec['criterion']:
                    if rec['criterion'] == 'ACCEPT' and rec['table_column'] in included:
                        # ignore intensity criteria converted from ACCEPT to
                        # IE-*
                        pass
                    else:
                        # preserve non-intensity related criteria
                        recs.append(rec)
        magic_write(path, recs, 'criteria')
    else:
        magic_write(path, [rec], 'pmag_criteria')


# Helpers for command-line programs

def add_flag(var, flag):
    """
    for use when calling command-line scripts from withing a program.
    if a variable is present, add its proper command_line flag.
    return a string.
    """
    if var:
        var = flag + " " + str(var)
    else:
        var = ""
    return var


def get_named_arg(name, default_val=None, reqd=False):
    """
    Extract the value after a command-line flag such as '-f' and return it.
    If the command-line flag is missing, return default_val.
    If reqd == True and the command-line flag is missing, throw an error.

    Parameters
    ----------
    name : str
        command line flag, e.g. "-f"
    default_val
        value to use if command line flag is missing, e.g. "measurements.txt"
        default is None
    reqd : bool
        throw error if reqd==True and command line flag is missing.
        if reqd == True, default_val will be ignored.
        default is False.

    Returns
    ---------
    Desired value from sys.argv if available, otherwise default_val.
    """
    if name in sys.argv:  # if the command line flag is found in sys.argv
        ind = sys.argv.index(name)
        return sys.argv[ind + 1]
    if reqd:  # if arg is required but not present
        raise MissingCommandLineArgException(name)
    return default_val  # if arg is not provided but has a default value, return that value


def get_flag_arg_from_sys(name, true=True, false=False):
    if name in sys.argv:
        return true
    else:
        return false


# Miscellaneous helpers

def merge_recs_headers(recs):
    '''
    take a list of recs [rec1,rec2,rec3....], each rec is a dictionary.
    make sure that all recs have the same headers.
    '''
    headers = []
    for rec in recs:
        keys = list(rec.keys())
        for key in keys:
            if key not in headers:
                headers.append(key)
    for rec in recs:
        for header in headers:
            if header not in list(rec.keys()):
                rec[header] = ""
    return recs


def resolve_file_name(fname, dir_path='.'):
    """
    Parse file name information and output full path.
    Allows input as:
    fname == /path/to/file.txt
    or
    fname == file.txt, dir_path == /path/to
    Either way, returns /path/to/file.txt.
    Used in conversion scripts.

    Parameters
    ----------
    fname : str
        short filename or full path to file
    dir_path : str
        directory, optional

    Returns
    ----------
    full_file : str
        full path/to/file.txt
    """
    if not fname:
        return ''
    file_dir_path, file_name = os.path.split(fname)
    if (not file_dir_path) or (file_dir_path == '.'):
        full_file = os.path.join(dir_path, fname)
    else:
        full_file = fname
    return os.path.realpath(full_file)


def remove_files(file_list, WD='.'):
    for f in file_list:
        full_file = os.path.join(WD, f)
        if os.path.isfile(full_file):
            os.remove(full_file)


def get_attr(obj, attr='name'):
    try:
        name = obj.__getattribute__(attr)
    except AttributeError:
        name = str(obj)
    return name


def adjust_val_to_360(val):
    """
    Take in a single numeric (or null) argument.
    Return argument adjusted to be between
    0 and 360 degrees.
    """
    if not val and (val != 0):
        return None
    else:
        try:
            return float(val) % 360
        except ValueError:
            return val


def adjust_to_360(val, key):
    """
    Take in a value and a key.  If the key is of the type:
    declination/longitude/azimuth/direction, adjust it to be within
    the range 0-360 as required by the MagIC data model
    """
    CheckDec = ['_dec', '_lon', '_azimuth', 'dip_direction']
    adjust = False
    for dec_key in CheckDec:
        if dec_key in key:
            if key.endswith(dec_key) or key.endswith('_'):
                adjust = True
    if not val:
        return ''
    elif not adjust:
        return val
    elif adjust:
        new_val = float(val) % 360
        if new_val != float(val):
            print('-I- adjusted {} {} to 0=>360.: {}'.format(key, val, new_val))
        return new_val


def adjust_all_to_360(dictionary):
    """
    Take a dictionary and check each key/value pair.
    If this key is of type: declination/longitude/azimuth/direction,
    adjust it to be within 0-360 as required by the MagIC data model
    """
    for key in dictionary:
        dictionary[key] = adjust_to_360(dictionary[key], key)
    return dictionary


def get_test_WD():
    """
    Find proper working directory to run tests.
    With developer install, tests should be run from PmagPy directory.
    Otherwise, assume pip install, and run tests from sys.prefix,
    where data_files are installed by setuptools.
    """
    WD = os.getcwd()
    if 'PmagPy' not in WD:
        WD = sys.prefix
    return WD


class MissingCommandLineArgException(Exception):

    def __init__(self, message):
        self.message = "{} is a required option! Please provide this information and try again".format(
            message)

    def __str__(self):
        return self.message


def do_mag_map(date, lon_0=0, alt=0, file="", mod="cals10k"):
    """
    returns lists of declination, inclination and intensities for lat/lon grid for
    desired model and date.

    Parameters:
    _________________
    date = Required date in decimal years (Common Era, negative for Before Common Era)

    Optional Parameters:
    ______________
    mod  = model to use ('arch3k','cals3k','pfm9k','hfm10k','cals10k.2','shadif14k','cals10k.1b','custom')
    file = l m g h formatted filefor custom model
    lon_0 : central longitude for Hammer projection

    alt  = altitude

    Returns:
    ______________
    Bdec=list of declinations
    Binc=list of inclinations
    B = list of total field intensities in nT
    Br = list of radial field intensities
    lons = list of longitudes evaluated
    lats = list of latitudes evaluated

    """
    incr = 10  # we can vary to the resolution of the model
    if lon_0 == 180:
        lon_0 = 179.99
    if lon_0 > 180:
        lon_0 = lon_0-360.
    # get some parameters for our arrays of lat/lon
    lonmax = (lon_0 + 180.) % 360 + incr
    lonmin = (lon_0 - 180.)
    latmax = 90 + incr
    # make a 1D array of longitudes (like elons)
    lons = np.arange(lonmin, lonmax, incr)
    # make a 1D array of longitudes (like elats)
    lats = np.arange(-90, latmax, incr)
    # set up some containers for the field elements
    B = np.zeros((len(lats), len(lons)))
    Binc = np.zeros((len(lats), len(lons)))
    Bdec = np.zeros((len(lats), len(lons)))
    Brad = np.zeros((len(lats), len(lons)))
    if mod == 'custom' and file != '':
        gh = []
        lmgh = np.loadtxt(file).transpose()
        gh.append(lmgh[2][0])
        for i in range(1, lmgh.shape[1]):
            gh.append(lmgh[2][i])
            if lmgh[1][i] != 0:
                gh.append(lmgh[3][i])
    for j in range(len(lats)):  # step through the latitudes
        for i in range(len(lons)):  # and the longitudes
            # get the field elements
            if mod == 'custom':
                x, y, z, f = docustom(lons[i], lats[j], alt, gh)
            else:
                x, y, z, f = doigrf(
                    lons[i], lats[j], alt, date, mod=mod, file=file)
            # turn them into polar coordinates
            Dec, Inc, Int = cart2dir([x, y, z])
            if mod != 'custom':
                # convert the string to microtesla (from nT)
                B[j][i] = Int * 1e-3
            else:
                B[j][i] = Int  # convert the string to microtesla (from nT)
            Binc[j][i] = Inc  # store the inclination value
            if Dec > 180:
                Dec = Dec-360.
            Bdec[j][i] = Dec  # store the declination value
            if mod != 'custom':
                Brad[j][i] = z*1e-3
            else:
                Brad[j][i] = z
    return Bdec, Binc, B, Brad, lons, lats  # return the arrays.


def doeqdi(x, y, UP=False):
    """
    Takes digitized x,y, data and returns the dec,inc, assuming an
    equal area projection
    Parameters
    __________________
        x : array of digitized x from point on equal area projection
        y : array of  igitized y from point on equal area projection
        UP : if True, is an upper hemisphere projection
    Output :
        dec : declination
        inc : inclination
    """
    xp, yp = y, x  # need to switch into geographic convention
    r = np.sqrt(xp**2+yp**2)
    z = 1.-r**2
    t = np.arcsin(z)
    if UP == 1:
        t = -t
    p = np.arctan2(yp, xp)
    dec, inc = np.degrees(p) % 360, np.degrees(t)
    return dec, inc


def separate_directions(di_block):
    """
    Separates set of directions into two modes based on principal direction

    Parameters
    _______________
    di_block : block of nested dec,inc pairs

    Return
    mode_1_block,mode_2_block :  two lists of nested dec,inc pairs
    """
    ppars = doprinc(di_block)
    di_df = pd.DataFrame(di_block)  # turn into a data frame for easy filtering
    di_df.columns = ['dec', 'inc']
    di_df['pdec'] = ppars['dec']
    di_df['pinc'] = ppars['inc']
    di_df['angle'] = angle(di_df[['dec', 'inc']].values,
                           di_df[['pdec', 'pinc']].values)
    mode1_df = di_df[di_df['angle'] <= 90]
    mode2_df = di_df[di_df['angle'] > 90]
    mode1 = mode1_df[['dec', 'inc']].values.tolist()
    mode2 = mode2_df[['dec', 'inc']].values.tolist()
    return mode1, mode2


def dovandamme(vgp_df):
    """
    determine the S_b value for VGPs using the Vandamme (1994) method
    for determining cutoff value for "outliers".
    Parameters
    ___________
    vgp_df : pandas DataFrame with required column "vgp_lat"
             This should be in the desired coordinate system and assumes one polarity

    Returns
    _________
    vgp_df : after applying cutoff
    cutoff : colatitude cutoff
    S_b : S_b of vgp_df  after applying cutoff
    """
    vgp_df['delta'] = 90.-vgp_df['vgp_lat'].values
    ASD = np.sqrt(np.sum(vgp_df.delta**2)/(vgp_df.shape[0]-1))
    A = 1.8 * ASD + 5.
    delta_max = vgp_df.delta.max()
    while delta_max > A:
        delta_max = vgp_df.delta.max()
        if delta_max < A:
            return vgp_df, A, ASD
        vgp_df = vgp_df[vgp_df.delta < delta_max]
        ASD = np.sqrt(np.sum(vgp_df.delta**2)/(vgp_df.shape[0]-1))
        A = 1.8 * ASD + 5.


def scalc_vgp_df(vgp_df, anti=0, rev=0, cutoff=180., kappa=0, n=0, spin=0, v=0, boot=0, mm97=0, nb=1000):
    """
    Calculates Sf for a dataframe with VGP Lat., and optional Fisher's k, site latitude and N information can be used to correct for within site scatter (McElhinny & McFadden, 1997)

    Parameters
    _________
    df : Pandas Dataframe with columns
        REQUIRED:
        vgp_lat :  VGP latitude
        ONLY REQUIRED for MM97 correction:
        dir_k : Fisher kappa estimate
        dir_n_samples : number of samples per site
        lat : latitude of the site
        mm97 : if True, will do the correction for within site scatter
        OPTIONAL:
        boot : if True. do bootstrap
        nb : number of bootstraps, default is 1000

    Returns
    _____________
        N : number of VGPs used in calculation
        S : S
        low : 95% confidence lower bound [0 if boot=0]
        high  95% confidence upper bound [0 if boot=0]
        cutoff : cutoff used in calculation of  S
    """
    vgp_df['delta'] = 90.-vgp_df.vgp_lat.values
    # filter by cutoff, kappa, and n
    vgp_df = vgp_df[vgp_df.delta <= cutoff]
    vgp_df = vgp_df[vgp_df.dir_k >= kappa]
    vgp_df = vgp_df[vgp_df.dir_n_samples >= n]
    if spin:  # do transformation to pole
        Pvgps = vgp_df[['vgp_lon', 'vgp_lat']].values
        ppars = doprinc(Pvgps)
        Bdirs = np.full((Pvgps.shape[0]), ppars['dec']-180.)
        Bdips = np.full((Pvgps.shape[0]), 90.-ppars['inc'])
        Pvgps = np.column_stack((Pvgps, Bdirs, Bdips))
        lons, lats = dotilt_V(Pvgps)
        vgp_df['vgp_lon'] = lons
        vgp_df['vgp_lat'] = lats
        vgp_df['delta'] = 90.-vgp_df.vgp_lat
    if anti:
        print('flipping reverse')
        vgp_rev = vgp_df[vgp_df.vgp_lat < 0]
        vgp_norm = vgp_df[vgp_df.vgp_lat >= 0]
        vgp_anti = vgp_rev
        vgp_anti['vgp_lat'] = -vgp_anti['vgp_lat']
        vgp_anti['vgp_lon'] = (vgp_anti['vgp_lon']-180) % 360
        vgp_df = pd.concat([vgp_norm, vgp_anti], sort=True)
    if rev:
        vgp_df = vgp_df[vgp_df.vgp_lat < 0]  # use only reverse data
    if v:
        vgp_df, cutoff, S_v = dovandamme(vgp_df)  # do vandamme cutoff
    S_B = get_sb_df(vgp_df, mm97=mm97)  # get
    N = vgp_df.shape[0]
    SBs, low, high = [], 0, 0
    if boot:
        for i in range(nb):  # now do bootstrap
            bs_df = vgp_df.sample(n=N, replace=True)
            Sb_bs = get_sb_df(bs_df)
            SBs.append(Sb_bs)
        SBs.sort()
        low = SBs[int(.025 * nb)]
        high = SBs[int(.975 * nb)]
    return N, S_B, low, high, cutoff


def watsons_f(DI1, DI2):
    """
    calculates Watson's F statistic (equation 11.16 in Essentials text book).

    Parameters
    _________
    DI1 : nested array of [Dec,Inc] pairs
    DI2 : nested array of [Dec,Inc] pairs

    Returns
    _______
    F : Watson's F
    Fcrit : critical value from F table
    """
    # first calculate R for the combined data set, then R1 and R2 for each individually.
    # create a new array from two smaller ones
    DI = np.concatenate((DI1, DI2), axis=0)
    fpars = fisher_mean(DI)  # re-use our functionfrom problem 1b
    fpars1 = fisher_mean(DI1)
    fpars2 = fisher_mean(DI2)
    N = fpars['n']
    R = fpars['r']
    R1 = fpars1['r']
    R2 = fpars2['r']
    F = (N-2.)*((R1+R2-R)/(N-R1-R2))
    Fcrit = fcalc(2, 2*(N-2))
    return F, Fcrit


def apwp(data, print_results=False):
    """
    calculates expected pole positions and directions for given plate, location and age
    Parameters
    _________
        data : [plate,lat,lon,age]
            plate : [NA, SA, AF, IN, EU, AU, ANT, GL]
                NA : North America
                SA : South America
                AF : Africa
                IN : India
                EU : Eurasia
                AU : Australia
                ANT: Antarctica
                GL : Greenland
             lat/lon : latitude/longitude in degrees N/E
             age : age in millions of years
        print_results : if True will print out nicely formatted results
    Returns
    _________
        if print_results is False, [Age,Paleolat, Dec, Inc, Pole_lat, Pole_lon]
    """
    pole_lat, pole_lon = bc02(data)  # get the pole for these parameters
    # get the declination and inclination for that pole
    ExpDec, ExpInc = vgp_di(pole_lat, pole_lon, data[1], data[2])
    # convert the inclination to paleo latitude
    paleo_lat = magnetic_lat(ExpInc)
    if print_results:
        # print everything out
        print(' Age   Paleolat.   Dec.   Inc.   Pole_lat.  Pole_Long.')
        print('%7.1f %7.1f %7.1f %7.1f %7.1f  %7.1f\n'
              % (data[3], paleo_lat, ExpDec, ExpInc, pole_lat, pole_lon))

    else:
        return [data[3], paleo_lat, ExpDec, ExpInc, pole_lat, pole_lon]


def chart_maker(Int, Top, start=100, outfile='chart.txt'):
    """
    Makes a chart for performing IZZI experiments. Print out the file and
    tape it to the oven.  This chart will help keep track of the different
    steps.
    Z : performed in zero field - enter the temperature XXX.0 in the sio
        formatted measurement file created by the LabView program
    I : performed in the lab field written at the top of the form
    P : a pTRM step - performed at the temperature and in the lab field.

    Parameters
    __________
    Int : list of intervals [e.g., 50,10,5]
    Top : list of upper bounds for each interval [e.g., 500, 550, 600]
    start : first temperature step, default is 100
    outfile : name of output file, default is 'chart.txt'

    Output
    _________
    creates a file with:
         file:  write down the name of the measurement file
         field:  write down the lab field for the infield steps (in uT)
         the type of step (Z: zerofield, I: infield, P: pTRM step
         temperature of the step and code for SIO-like treatment steps
             XXX.0   [zero field]
             XXX.1   [in field]
             XXX.2   [pTRM check] - done in a lab field
         date : date the step was performed
         run # : an optional run number
         zones I-III : field in the zones in the oven
         start : time the run was started
         sp :  time the setpoint was reached
         cool : time cooling started

    """
    low, k, iz = start, 0, 0
    Tzero = []
    f = open('chart.txt', 'w')
    vline = '\t%s\n' % (
        '   |      |        |         |          |       |    |      |')
    hline = '______________________________________________________________________________\n'
    f.write('file:_________________    field:___________uT\n\n\n')
    f.write('%s\n' % (
        '               date | run# | zone I | zone II | zone III | start | sp | cool|'))
    f.write(hline)
    f.write('\t%s' % ('   0.0'))
    f.write(vline)
    f.write(hline)
    for k in range(len(Top)):
        for t in range(low, Top[k]+Int[k], Int[k]):
            if iz == 0:
                Tzero.append(t)  # zero field first step
                f.write('%s \t %s' % ('Z', str(t)+'.'+str(iz)))
                f.write(vline)
                f.write(hline)
                if len(Tzero) > 1:
                    f.write('%s \t %s' % ('P', str(Tzero[-2])+'.'+str(2)))
                    f.write(vline)
                    f.write(hline)
                iz = 1
                # infield after zero field first
                f.write('%s \t %s' % ('I', str(t)+'.'+str(iz)))
                f.write(vline)
                f.write(hline)

#                f.write('%s \t %s'%('T',str(t)+'.'+str(3))) # print second zero field (tail check)
#                f.write(vline)
#                f.write(hline)

            elif iz == 1:
                # infield first step
                f.write('%s \t %s' % ('I', str(t)+'.'+str(iz)))
                f.write(vline)
                f.write(hline)
                iz = 0
                # zero field step (after infield)
                f.write('%s \t %s' % ('Z', str(t)+'.'+str(iz)))
                f.write(vline)
                f.write(hline)
        try:
            low = Top[k]+Int[k+1]  # increment to next temp step
        except:
            f.close()
    print("output stored in: chart.txt")


def import_basemap():
    """
    Try to import Basemap and print out a useful help message
    if Basemap is either not installed or is missing required
    environment variables.

    Returns
    ---------
    has_basemap : bool
    Basemap : Basemap package if possible else None
    """

    Basemap = None
    has_basemap = True
    has_cartopy = import_cartopy()[0]
    try:
        from mpl_toolkits.basemap import Basemap
        WARNINGS['has_basemap'] = True
    except ImportError:
        has_basemap = False
        # if they have installed cartopy, no warning is needed
        if has_cartopy:
            return has_basemap, False
        # if they haven't installed Basemap or cartopy, they need to be warned
        if not WARNINGS['basemap']:
            print(
                "-W- You haven't installed a module for plotting maps (cartopy or Basemap)")
            print("    Recommended: install cartopy.  With conda:")
            print("    conda install cartopy")
            print(
                "    For more information, see http://earthref.org/PmagPy/Cookbook#getting_python")
    except (KeyError, FileNotFoundError):
        has_basemap = False
        # if cartopy is installed, no warning is needed
        if has_cartopy:
            return has_basemap, False
        if not WARNINGS['basemap']:
            print('-W- Basemap is installed but could not be imported.')
            print('    You are probably missing a required environment variable')
            print(
                '    If you need to use Basemap, you will need to run this program or notebook in a conda env.')
            print('    For more on how to create a conda env, see: https://conda.io/docs/user-guide/tasks/manage-environments.html')
            print(
                '    Recommended alternative: install cartopy for plotting maps.  With conda:')
            print('    conda install cartopy')
    if has_basemap and not has_cartopy:
        print("-W- You have installed Basemap but not cartopy.")
        print("    In the future, Basemap will no longer be supported.")
        print("    To continue to make maps, install using conda:")
        print('    conda install cartopy')

    WARNINGS['basemap'] = True
    return has_basemap, Basemap


def import_cartopy():
    """
    Try to import cartopy and print out a help message
    if it is not installed

    Returns
    ---------
    has_cartopy : bool
    cartopy : cartopy package if available else None
    """
    cartopy = None
    has_cartopy = True
    try:
        import cartopy
        WARNINGS['has_cartopy'] = True
    except ImportError:
        has_cartopy = False
        if not WARNINGS['cartopy']:
            print('-W- cartopy is not installed')
            print('    If you want to make maps, install using conda:')
            print('    conda install cartopy')
    WARNINGS['cartopy'] = True
    return has_cartopy, cartopy


def age_to_BP(age, age_unit):
    """
    Convert an age value into the equivalent in time Before Present(BP) where Present is 1950

    Returns
    ---------
    ageBP : number
    """
    ageBP = -1e9
    if age_unit == "Years AD (+/-)" or age_unit == "Years Cal AD (+/-)":
        if age < 0:
            age = age+1  # to correct for there being no 0 AD
        ageBP = 1950-age
    elif age_unit == "Years BP" or age_unit == "Years Cal BP":
        ageBP = age
    elif age_unit == "ka":
        ageBP = age*1000
    elif age_unit == "Ma":
        ageBP = age*1e6
    elif age_unit == "Ga":
        ageBP = age*1e9
    else:
        print("Age unit invalid. Age set to -1.0e9")

    return ageBP


def vocab_convert(vocab, standard, key=''):
    """
    Converts MagIC database terms (method codes, geologic_types, etc) to other standards.
    May not be comprehensive for each standard. Terms added to standards as people need them
    and may not be up-to-date.

    'key' can be used to distinguish vocab terms that exist in two different lists.

    Returns:
    value of the MagIC vocab in the standard requested

    Example:
    vocab_convert('Egypt','GEOMAGIA') will return '1'
    """
	
    places_to_geomagia = {
        'Egypt':                 "1",
        'Japan':                 "2",
        'France':                "3",
        'Ukraine':               "5",
        'India':                 "6",
        'China':                 "7",
        'Finland':               "8",
        'Greece':                "9",
        'Italy':                 "11",
        'Switzerland':           "12",
        'Bulgaria':              "13",
        'Syria':                 "14",
        'Hungary':               "15",
        'East Pacific Ridge':    "17",
        'Hawaii':                "18",
        'Morocco':               "19",
        'Australia':             "20",
        'Georgia':               "21",
        'Azerbaijan':            "22",
        'Spain':                 "24",
        'England':               "25",
        'Czech Republic':        "26",
        'Mexico':                "27",
        'Iraq':                  "28",
        'Israel':                "29",
        'Iran':                  "30",
        'Uzbekistan':            "31",
        'Turkmenistan':          "32",
        'Mongolia':              "33",
        'Iceland':               "34",
        'New Zealand':           "35",
        'Amsterdam Island':      "36",
        'Guadeloupe':            "37",
        'Mid Atlantic Ridge':    "38",
        'Austria':               "39",
        'Belgium':               "40",
        'Romania':               "41",
        'Guatemala':             "42",
        'El Salvador':           "43",
        'Canary Islands':        "45",
        'Moldova':               "46",
        'Latvia':                "47",
        'Lithuania':             "48",
        'Russia':                "49",
        'Germany':               "51",
        'Martinique':            "52",
        'Netherlands':           "53",
        'Turkey':                "54",
        'Denmark':               "55",
        'Cameroon':              "56",
        'Honduras':              "57",
        'Jordan':                "58",
        'Brazil':                "59",
        'Estonia':               "61",
        'Sweden':                "62",
        'Peru':                  "63",
        'Bolivia':               "64",
        'Ecuador':               "65",
        'Ontario':               "66",
        'New Mexico':            "67",
        'Arizona':               "68",
        'California':            "69",
        'Colorado':              "70",
        'Utah':                  "71",
        'Washington':            "72",
        'Oregon':                "73",
        'British Columbia':      "74",
        'Idaho':                 "75",
        'Arkansas':              "76",
        'Tennessee':             "78",
        'Serbia':                "79",
        'Kosovo':                "80",
        'Portugal':              "81",
        'Thailand':              "82",
        'South Korea':           "83",
        'Kazakhstan':            "84",
        'Nebraska':              "85",
        'La Reunion':            "86",
        'Cyprus':                "87",
        'Papua New Guinea':      "88",
        'Vanuatu':               "89",
        'Fiji':                  "90",
        'Argentina':             "91",
        'Tunisia':               "92",
        'Mali':                  "93",
        'Senegal':               "95",
        'Alaska':                "96",
        'North Atlantic':        "97",
        'South Atlantic':        "98",
        'Beaufort Sea':          "99",
        'Chukchi Sea':           "100",
        'Kyrgyzstan':            "101",
        'Indonesia':             "102",
        'Azores':                "103",
        'Quebec':                "104",
        'Norway':                "105",
        'Northern Ireland':      "106",
        'Wales':                 "107",
        'Scotland':              "108",
        'Virginia':              "109",
        'North West Pacific':    "110",
        'Mediterranean':         "111",
        'Slovakia':              "121",
        'Poland':                "124"
    }

    geologic_types_to_geomagia = {
        "Baked Clay":                                  "2",
        "Tile":                                        "3",
        "Lava":                                        "4",
        "Pottery":                                     "5",
        "Sun Dried Object":                            "6",
        "Porcelain":                                   "7",
        "Ceramic":                                     "8",
        "Kiln":                                        "9",
        "Oven or Hearth (GEOMAGIA Only)":              "10",
        "Mixed Archeological Objects":                 "11",
        "Slag":                                        "12",
        "Baked Rock":                                  "13",
        "Fresco":                                      "14",
        "Mosaic":                                      "15",
        "Wall":                                        "16",
        "Bath":                                        "17",
        "Burnt Floor":                                 "18",
        "Funeral Pyre":                                "19",
        "Hypocaust":                                   "20",
        "Burnt Pit":                                   "21",
        "Bell Mould":                                  "22",
        "Smoking Chamber":                             "23",
        "Baked Mud":                                   "24",
        "Volcanic Ash":                                "25",
        "Burnt Structure":                             "26",
        "Burnt Castle Wall":                           "27",
        "Charcoal Pile":                               "28",
        "Burnt Earth":                                 "29",
        "Vitrified Object":                            "30",
        "Unbaked Sediment":                            "31",
        "Tuyere":                                      "32",
        "Sauna":                                       "33",
        "Pit Structure":                               "35",
        "Room":                                        "36",
        "Pit House":                                   "37",
        "Salt Kiln":                                   "38",
        "Burnt Sediment":                              "39",
        "Archeological Ashes":                         "40",
        "Volcanic Other or Undefined (GEOMAGIA Only)": "41",
        "Mural":                                       "42",
        "Vitrified Stone":                             "43",
        "Soil":                                        "44",
        "Kamadogu":                                    "45",
        "Foundry":                                     "46",
        "Obsidian":                                    "47",
        "Chert":                                       "48",
        "Burnt daub":                                  "49",
        "Amphora":                                     "50",
        "Granite":                                     "51",
        "Volcanic Glass":                              "52",
        "Furnace":                                     "53",
        "Roasting Pit":                                "54"

    }

#   Some of the simple method code mappings are done here

    method_codes_to_geomagia = {
        "GM-NO":        "0",
        "GM-CC-ARCH":   "101",
        "GM-C14-CAL":   "102",
        "GM-C14-UNCAL": "103",
        "GM-LUM-TH":    "104",
        "GM-HIST":      "105",
        "GM-PMAG-ARCH": "106",
        "GM-ARAR":      "107",
        "GM-CC-TEPH":   "108",
        "GM-CC-STRAT":  "109",
        "GM-CC-REL":    "110",
        "GM-DENDRO":    "111",
        "GM-RATH":      "112",
        "GM-KAR":       "113",
        "GM-UTH":       "114",
        "GM-FT":        "115",
        "GM-C14-AMS":   "116",
        "GM-LUM-OS":    "117",
        "GM-HE3":       "118",
        "GM-VARVE":     "119",
        "GM-CS137":     "120",
        "GM-USD-PB210": "121",
        "GM-C14-BETA":  "122",
        "GM-O18":       "123",
        "GM-PA":        "124"
    }

    standard = standard.lower()
    standard_value = ""
    if standard == "geomagia":
        if vocab in places_to_geomagia.keys():
            standard_value = places_to_geomagia[vocab]
        if vocab in geologic_types_to_geomagia.keys():
            standard_value = geologic_types_to_geomagia[vocab]
        if vocab in method_codes_to_geomagia.keys():
            standard_value = method_codes_to_geomagia[vocab]
    if standard_value == "":
        print("Magic vocab ", vocab, " not found for standard ", standard)
        return(vocab)
    return standard_value


def main():
    print("Full PmagPy documentation is available at: https://earthref.org/PmagPy/cookbook/")
