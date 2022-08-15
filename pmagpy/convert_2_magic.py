#!/usr/bin/env/pythonw

import copy
import datetime
from functools import reduce
import math
import os
import sys

import pytz
import scipy
import numpy as np
import pandas as pd
import pmagpy.pmag as pmag
import pmagpy.contribution_builder as cb


### _2g_bin_magic conversion

def _2g_bin(dir_path=".", mag_file="", dec_corr=True,meas_file='measurements.txt',
            spec_file="specimens.txt", samp_file="samples.txt", site_file="sites.txt",
            loc_file="locations.txt", or_con='3', specnum=0, samp_con='2', corr='1',specname=False,
            gmeths="FS-FD:SO-POM", location="unknown", inst="", user="", noave=False, input_dir="",
            savelast=False,lat="", lon="",labfield=0, labfield_phi=0, labfield_theta=0,
            experiment="Demag", cooling_times_list=[]):

    """
    Convert 2G binary format file to MagIC file(s)

    Parameters
    ----------
    dir_path : str
        output directory, default "."
    mag_file : str
        input file name
    dec_corr : bool
        if True, declination correction to true north provided
    meas_file : str
        output measurement file name, default "measurements.txt"
    spec_file : str
        output specimen file name, default "specimens.txt"
    samp_file: str
        output sample file name, default "samples.txt"
    site_file : str
        output site file name, default "sites.txt"
    loc_file : str
        output location file name, default "locations.txt"
    or_con : number
        orientation convention, default '3', see info below
    specnum : int
        number of characters to designate a specimen, default 0
    specname : bool
        if True, use file name stem for specimen name, if False, read from within file, default = False
    samp_con : str
        (specimen/)sample/site naming convention, default '2', see info below
    corr: str
        default '1'
    gmeths : str
        sampling method codes, default "FS-FD:SO-POM", see info below
    location : str
        location name, default "unknown"
    inst : str
        instrument, default ""
    user : str
        user name, default ""
    noave : bool
       do not average duplicate measurements, default False (so by default, DO average)
    savelast : bool
       take the last measurement if replicates at treatment step, default is False
    input_dir : str
        input file directory IF different from dir_path, default ""
    lat : float
        latitude, default ""
    lon : float
        longitude, default ""
    labfield : float
        dc lab field (in micro tesla)
    labfield_phi : float
        declination 0-360
    labfield_theta : float
        inclination -90 - 90
    experiment : str
        experiment type, see info below;  default is Demag
    cooling_times_list : list
        cooling times in [K/minutes] seperated by comma,
        ordered at the same order as XXX.10,XXX.20 ...XX.70

    Returns
    ---------
    Tuple : (True or False indicating if conversion was successful, meas_file name written)


    Info
    ----------
    Orientation convention:
        [1] Lab arrow azimuth= mag_azimuth; Lab arrow dip=-field_dip
            i.e., field_dip is degrees from vertical down - the hade [default]
        [2] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = -field_dip
            i.e., mag_azimuth is strike and field_dip is hade
        [3] Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip
            i.e.,  lab arrow same as field arrow, but field_dip was a hade.
        [4] lab azimuth and dip are same as mag_azimuth, field_dip
        [5] lab azimuth is same as mag_azimuth,lab arrow dip=field_dip-90
        [6] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = 90-field_dip
        [7] all others you will have to either customize your
            self or e-mail ltauxe@ucsd.edu for help.

   Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
       [8] siteName_sample_specimen: the three are differentiated with '_'

    Sampling method codes:
         FS-FD field sampling done with a drill
         FS-H field sampling done with hand samples
         FS-LOC-GPS  field location done with GPS
         FS-LOC-MAP  field location done with map
         SO-POM   a Pomeroy orientation device was used
         SO-ASC   an ASC orientation device was used
         SO-MAG   orientation with magnetic compass
         SO-SUN   orientation with sun compass

    Experiment type:
        Demag:
            AF and/or Thermal
        PI:
            paleointenisty thermal experiment (ZI/IZ/IZZI)
        ATRM n:

            ATRM in n positions (n=6)

        AARM n:
            AARM in n positions
        CR:
            cooling rate experiment
            The treatment coding of the measurement file should be: XXX.00,XXX.10, XXX.20 ...XX.70 etc. (XXX.00 is optional)
            where XXX in the temperature and .10,.20... are running numbers of the cooling rates steps.
            XXX.00 is optional zerofield baseline. XXX.70 is alteration check.
            if using this type, you must also provide cooling rates in [K/minutes] in cooling_times_list
            separated by comma, ordered at the same order as XXX.10,XXX.20 ...XX.70

            No need to specify the cooling rate for the zerofield
            But users need to make sure that there are no duplicate meaurements in the file

        NLT:
            non-linear-TRM experiment



    """

    #
    # initialize variables
    #
    bed_dip, bed_dip_dir = "", ""
    sclass, lithology, _type = "", "", ""
    DecCorr = 0.
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # format and fix variables
    specnum = int(specnum)
    specnum = -specnum
    input_dir_path, dir_path = pmag.fix_directories(input_dir, dir_path)

    if samp_con:
        samp_con=str(samp_con)
        Z = 1
        if "4" in samp_con:
            if "-" not in samp_con:
                print("option [4] must be in form 4-Z where Z is an integer")
                return False, "option [4] must be in form 4-Z where Z is an integer"
            else:
                Z = samp_con.split("-")[1]
                samp_con = "4"
        if "7" in samp_con:
            if "-" not in samp_con:
                print("option [7] must be in form 7-Z where Z is an integer")
                return False, "option [7] must be in form 7-Z where Z is an integer"
            else:
                Z = samp_con.split("-")[1]
                samp_con = "7"
        if "6" in samp_con:
            print('Naming convention option [6] not currently supported')
            False, 'Naming convention option [6] not currently supported'
    if not mag_file:
        print("mag file is required input")
        return False, "mag file is required input"
    output_dir_path = dir_path
    mag_file_path = pmag.resolve_file_name(mag_file, input_dir_path)

    samplist = []
    try:
        SampRecs, file_type = pmag.magic_read(samp_file)
    except:
        SampRecs = []
    MeasRecs, SpecRecs, SiteRecs, LocRecs = [], [], [], []
    try:
        f = open(mag_file_path, 'br')
        input = str(f.read()).strip("b '")
        f.close()
    except Exception as ex:
        print('ex', ex)
        print("bad mag file")
        return False, "bad mag file"
    firstline, date,firststep = 1, "",1
    d = input.split('\\xcd')
    for line in d:
        rec = line.split('\\x00')
        # skip nearly empty lines
        rec_not_null = [i for i in rec if i]
        if len(rec_not_null) < 5:
            continue
        LPcode=""
        if firstline == 1:
            firstline = 0
            spec, vol = "", 1
            el = 51
            #while line[el:el+1] != "\\":
            #    spec = spec+line[el]
            #    el += 1
            spec = rec[7]
            # check for bad sample name
            test = spec.split('.')
            date = ""
            if len(test) > 1:
                spec = test[0]
                kk = 24
                while line[kk] != '\\x01' and line[kk] != '\\x00':
                    kk += 1
                vcc = line[24:kk]
                el = 10
                while rec[el].strip() != '':
                    el += 1
                date, comments = rec[el+7], []
            else:
                el = 9
                while rec[el] != '\\x01':
                    el += 1
                vcc, date, comments = rec[el-3], rec[el+7], []
            if specname:
                specname=mag_file.split('.')[0]
            else:
                specname = spec.lower()
            print('importing ', specname)
            el += 8
            while rec[el].isdigit() == False:
                comments.append(rec[el])
                el += 1
            if dec_corr: # ADDED 3/3/21
                if rec[el].isdigit(): 
                    deccorr=float(rec[el])
            else:
                deccorr=0
            el+=1
            while rec[el] == "":
                el += 1
            az = float(rec[el])
            el += 1
            while rec[el] == "":
                el += 1
            pl = float(rec[el])
            el += 1
            while rec[el] == "":
                el += 1
            bed_dip_dir = float(rec[el])
            el += 1
            while rec[el] == "":
                el += 1
            bed_dip = float(rec[el])
            el += 1
            while rec[el] == "":
                el += 1
            if rec[el] == '\\x01':
                bed_dip = 180.-bed_dip
                el += 1
                while rec[el] == "":
                    el += 1
            fold_az = float(rec[el])
            el += 1
            while rec[el] == "":
                el += 1
            fold_pl = rec[el]
            el += 1
            while rec[el] == "":
                el += 1
            #if rec[el] != "" and rec[el] != '\\x02' and rec[el] != '\\x01':
            #if deccorr!=0:
               # #deccorr = float(rec[el])
               # az += deccorr
               # if bed_dip!=0:bed_dip_dir += deccorr
               # fold_az += deccorr
               # if bed_dip_dir >= 360:
               #     bed_dip_dir = bed_dip_dir-360.
               # if az >= 360.:
               #     az = az-360.
               # if fold_az >= 360.:
               #     fold_az = fold_az-360.
            #else:
            #    deccorr = 0
            if specnum != 0:
                sample = specname[:specnum]
            else:
                sample = specname
            methods = gmeths.split(':')
            if deccorr != "0":
                if 'SO-MAG' in methods:
                    del methods[methods.index('SO-MAG')]
                methods.append('SO-CMD-NORTH')
            meths = reduce(lambda x, y: x+':'+y, methods)
            method_codes = meths
            # parse out the site name
            if samp_con=='8':
                sss = pmag.parse_site(specname, samp_con, Z)
                sample=sss[1]
                site=sss[2]
            else: 
                site = pmag.parse_site(sample, samp_con, Z)
            SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}
            SpecRec["specimen"] = specname
            SpecRec["sample"] = sample
            if vcc.strip() != "":
                vol = float(vcc)*1e-6  # convert to m^3 from cc
            SpecRec["volume"] = '%10.3e' % (vol)
            SpecRec["geologic_classes"] = sclass
            SpecRec["lithologies"] = lithology
            SpecRec["geologic_types"] = _type
            SpecRec["citations"] = "This study"
            SpecRec["method_codes"] = ""
            SpecRecs.append(SpecRec)

            if sample != "" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
                SampRec["sample"] = sample
                SampRec["site"] = site
                # convert to labaz, labpl
                labaz, labdip = pmag.orient(az, pl, or_con)
                SampRec["bed_dip"] = '%7.1f' % (bed_dip)
                SampRec["bed_dip_direction"] = '%7.1f' % (bed_dip_dir)
                SampRec["dip"] = '%7.1f' % (labdip)
                SampRec["azimuth"] = '%7.1f' % (labaz)
                SampRec["azimuth_dec_correction"] = '%7.1f' % (deccorr)
                SampRec["geologic_classes"] = sclass
                SampRec["lithologies"] = lithology
                SampRec["geologic_types"] = _type
                SampRec["method_codes"] = method_codes
                SampRec["citations"] = "This study"
                SampRecs.append(SampRec)
            if site != "" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
                SiteRec['site'] = site
                SiteRec['location'] = location
                SiteRec['lat'] = lat
                SiteRec['lon'] = lon
                SiteRec["geologic_classes"] = sclass
                SiteRec["lithologies"] = lithology
                SiteRec["geologic_types"] = _type
                SiteRec["age"] ="" 
                SiteRec["age_low"] ="" 
                SiteRec["age_high"] ="" 
                SiteRec["age_unit"] ="" 
                SiteRec["method_codes"] ="" 
                SiteRec["citations"] ="This study" 
                SiteRecs.append(SiteRec)

            if location != "" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
                LocRec['location'] = location
                LocRec['lat_n'] = lat
                LocRec['lon_e'] = lon
                LocRec['lat_s'] = lat
                LocRec['lon_w'] = lon
                LocRec["geologic_classes"]=sclass
                LocRec["lithologies"]=lithology
                LocRec["age"]=""
                LocRec["age_high"]=""
                LocRec["age_low"]=""
                LocRec["age_unit"]=""
                LocRec["citations"]="This study"
                LocRec["method_codes"]=""
                LocRec["location_type"]=""
                LocRecs.append(LocRec)

        else:
            rec_no_spaces=[]
            for k in range(len(rec)):
                if rec[k]!="":
                    rec_no_spaces.append(rec[k])
            if firststep:               
                input_df=pd.DataFrame([rec_no_spaces])
                firststep=0
            else:
                tmp_df=pd.DataFrame([rec_no_spaces])
                input_df=pd.concat([input_df,tmp_df])
    columns=['treat_temp','treat_ac_field','treat_dc_field','treat_dc_field_phi',
             'treat_dc_field_theta','method_codes','treat_type','aniso_type']
    meas_df=pd.DataFrame()
    treat_df=pd.DataFrame(columns=columns)

    meas_df['treat_step_num']=range(len(input_df))
    meas_df['specimen']=specname
    meas_df['quality']='g'
    meas_df['standard']='u'

    treatments=input_df[0].tolist()

    for t in treatments:
        this_treat_df=pd.DataFrame(columns=columns)
        this_treat_df['method_codes']=['LT-NO']
        this_treat_df['treat_ac_field']=[0]
        this_treat_df['treat_temp']=[273]
        this_treat_df['treat_type']=0
        this_treat_df['treat_dc_field']=0
        this_treat_df['treat_dc_field_phi']=0
        this_treat_df['treat_dc_field_theta']=0
        this_treat_df['aniso_type']=""
        if 'mT' in t:        
            treat_code=t.strip('mT').split('.')
            this_treat_df['treat_ac_field']=[float(treat_code[0])*1e-3] # convert to tesla
            if len(treat_code)>1:this_treat_df['treat_type']=int(treat_code[1])
            this_treat_df['treat_temp']=[273]
            if int(treat_code[0])==0:
                this_treat_df['method_codes']=['LT-NO']
            elif labfield==0:
                this_treat_df['method_codes']=['LT-AF-Z']
            elif labfield:
                this_treat_df['method_codes']=['LT-AF-I']
                this_treat_df['treat_dc_field']=labfield*1e-3 # convert to tesla
                this_treat_df['treat_dc_field_phi']=labfield_phi
                this_treat_df['treat_dc_field_theta']=labfield_theta




        elif 'C' in t or t!='NRM' and float(t.split('.')[0])!=0: # assume thermal
            treat_code=t.strip('C').split('.')
            if len(treat_code)>1:this_treat_df['treat_type']=int(treat_code[1])
            this_treat_df['method_codes']=['LT-T-Z']
            this_treat_df['treat_ac_field']=0 # convert to tesla
            this_treat_df['treat_temp']=[float(treat_code[0])+273] # convert to kelvin
            if labfield:
                LPcode='LP-PI-TRM'
                if int(treat_code[1])==3:
                    this_treat_df['method_codes']=['LT-T-Z:LT-PTRM-MD']
                elif int(treat_code[1])==1: 
                    this_treat_df['method_codes']=['LT-T-I']
                    this_treat_df['treat_dc_field']=labfield*1e-3 # convert to tesla
                    this_treat_df['treat_dc_field_phi']=labfield_phi
                    this_treat_df['treat_dc_field_theta']=labfield_theta


                elif int(treat_code[1])==2: 
                    this_treat_df['method_codes']=['LT-T-I:LT-PTRM-I']
                    this_treat_df['treat_dc_field']=labfield*1e-3 # convert to tesla
                    this_treat_df['treat_dc_field_phi']=labfield_phi
                    this_treat_df['treat_dc_field_theta']=labfield_theta
            else:
                LPcode='LP-DIR-T'

        treat_df=pd.concat([treat_df,this_treat_df])
    
    treat_df['treat_step_num']=range(len(input_df))
    meths=treat_df['method_codes'].unique()
    LPcode=""
    if 'LT-AF-Z' in meths:
        if labfield:
            LPcode='LP-PI-ARM'
            treat_df['aniso_type']='AARM'
        else:
            LPcode='LP-DIR-AF'
    elif 'LT-T-Z' in meths:
        if labfield:
            LPcode='LP-PI-TRM'
        else:
            LPcode='LP-DIR-T'
        
    if experiment:
        if 'ATRM' in experiment:
            LPcode='LP-AN-TRM'
            treat_df['aniso_type']='ATRM'
        if 'AARM' in experiment:
            LPcode='LP-AN-AARM'
        if experiment == 'CR':
            if command_line:
                cooling_times = sys.argv[ind+1]
                cooling_times_list = cooling_times.split(',')
            noave = True
            
    meas_df=pd.merge(meas_df,treat_df,on='treat_step_num')
    meas_df['dir_dec']=input_df[1].values # specimen coordinates
    meas_df['dir_inc']=input_df[2].values
    meas_df['magn_moment']=input_df[7].astype('float').values*1e-3 # moment in Am^2 (from emu)
    meas_df['magn_volume']=input_df[8].astype('float').values*1e-3/vol # moment in A/m (from emu)
    meas_df['magn_x_sigma']=input_df[9].astype('float').values*1e-3 # moment in Am^2 (from emu)
    meas_df['magn_y_sigma']=input_df[10].astype('float').values*1e-3 # moment in Am^2 (from emu)
    meas_df['magn_z_sigma']=input_df[11].astype('float').values*1e-3 # moment in Am^2 (from emu
    meas_df['meas_n_orient']=input_df[19].values
    meas_df['citations']='This study'
    meas_df['analysts']=user
    meas_df['instrument_codes']=inst
    meas_df['method_codes']=meas_df['method_codes']+':'+LPcode
    meas_df['measurement']=meas_df['treat_step_num'].astype('str')
    meas_df['experiment']=specname+'_'+LPcode
    meas_df.drop(columns=['treat_type'],inplace=True)
    meas_df.fillna("",inplace=True)
    meas_dicts = meas_df.to_dict('records')                                              
    pmag.magic_write(output_dir_path+'/'+meas_file, meas_dicts, 'measurements')

# save to files
    con = cb.Contribution(output_dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    #MeasOuts = pmag.measurements_methods3(meas_dicts, noave,savelast=False)
    #con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)
    con.write_table_to_file('specimens', custom_name=spec_file)
    con.write_table_to_file('samples', custom_name=samp_file)
    con.write_table_to_file('sites', custom_name=site_file)
    con.write_table_to_file('locations', custom_name=loc_file)
    #con.write_table_to_file('measurements', custom_name=meas_file)
    return True, meas_file

# 2G ascii file conversion


def _2g_asc(dir_path=".", mag_file="", meas_file='measurements.txt',
            spec_file="specimens.txt", samp_file="samples.txt", site_file="sites.txt",
            loc_file="locations.txt", lat="",lon="",or_con='3', specnum=0, samp_con='2',
            gmeths="FS-FD:SO-POM", location="Not Specified", inst="", user="", noave=False, input_dir="",
            savelast=False,experiment="Demag"):

    """
    Convert 2G ascii format file to MagIC file(s)

    Parameters
    ----------
    dir_path : str
        output directory, default "."
    mag_file : str
        input file name
    meas_file : str
        output measurement file name, default "measurements.txt"
    spec_file : str
        output specimen file name, default "specimens.txt"
    samp_file: str
        output sample file name, default "samples.txt"
    site_file : str
        output site file name, default "sites.txt"
    loc_file : str
        output location file name, default "locations.txt"
    or_con : number
        orientation convention, default '3', see info below
    specnum : int
        number of characters to designate a specimen, default 0
    samp_con : str
        (specimen/)sample/site naming convention, default '2', see info below
    gmeths : str
        sampling method codes, default "FS-FD:SO-POM", see info below
    location : str
        location name, default "unknown"
    lat : float
        latitude of site
    lon : float
        longitude of site
    inst : str
        instrument, default ""
    user : str
        user name, default ""
    noave : bool
       do not average duplicate measurements, default False (so by default, DO average)
    savelast : bool
       take the last measurement if replicates at treatment step, default is False
    input_dir : str
        input file directory IF different from dir_path, default ""
    experiment : str
        experiment type, see info below;  default is Demag
    cooling_times_list : list
        cooling times in [K/minutes] seperated by comma,
        ordered at the same order as XXX.10,XXX.20 ...XX.70

    Returns
    ---------
    Tuple : (True or False indicating if conversion was successful, meas_file name written)


    Info
    ----------
    Orientation convention:
        [1] Lab arrow azimuth= mag_azimuth; Lab arrow dip=-field_dip
            i.e., field_dip is degrees from vertical down - the hade [default]
        [2] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = -field_dip
            i.e., mag_azimuth is strike and field_dip is hade
        [3] Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip
            i.e.,  lab arrow same as field arrow, but field_dip was a hade.
        [4] lab azimuth and dip are same as mag_azimuth, field_dip
        [5] lab azimuth is same as mag_azimuth,lab arrow dip=field_dip-90
        [6] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = 90-field_dip
        [7] all others you will have to either customize your
            self or e-mail ltauxe@ucsd.edu for help.

   Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
       [8] siteName_sample_specimen: the three are differentiated with '_'

    Sampling method codes:
         FS-FD field sampling done with a drill
         FS-H field sampling done with hand samples
         FS-LOC-GPS  field location done with GPS
         FS-LOC-MAP  field location done with map
         SO-POM   a Pomeroy orientation device was used
         SO-ASC   an ASC orientation device was used
         SO-MAG   orientation with magnetic compass
         SO-SUN   orientation with sun compass

    Experiment type:
        Demag:
            AF and/or Thermal
        NOTE: no other experiment types supported yet - please post request on github.org/PmagPy/PmagPy
    """
    from functools import reduce
    # format and fix variables

    if mag_file.split('.')[-1].lower()!='asc':
        print ('file name must have .asc termination')
        return False, 'file name must have .asc termination'
    else:
        specname=""
        for part in mag_file.split('.')[0:-1]:
            specname=specname+'.'+part
        specname=specname.strip('.')
        print ('importing ',specname)
        specnum = int(specnum)
    specnum = -specnum
    input_dir_path, dir_path = pmag.fix_directories(input_dir, dir_path)

    if samp_con:
        samp_con=str(samp_con)
        Z = 1
        if "4" in samp_con:
            if "-" not in samp_con:
                print("option [4] must be in form 4-Z where Z is an integer")
                return False, "option [4] must be in form 4-Z where Z is an integer"
            else:
                Z = samp_con.split("-")[1]
                samp_con = "4"
        if "7" in samp_con:
            if "-" not in samp_con:
                print("option [7] must be in form 7-Z where Z is an integer")
                return False, "option [7] must be in form 7-Z where Z is an integer"
            else:
                Z = samp_con.split("-")[1]
                samp_con = "7"
        if "6" in samp_con:
            print('Naming convention option [6] not currently supported')
            return False, 'Naming convention option [6] not currently supported'
    if not mag_file:
        print("mag file is required input")
        return False, "mag file is required input"
    output_dir_path = dir_path
    mag_file_path = pmag.resolve_file_name(mag_file, input_dir_path)
    version_num=pmag.get_version()
    try:
        SampRecs, file_type = pmag.magic_read(samp_file)
    except:
        SampRecs = []
    meas_reqd_columns=['specimen','quality','method_codes',\
                       'citations','standard',\
                       'treat_temp','treat_ac_field','treat_dc_field',\
                      'treat_dc_field_phi','treat_dc_field_theta','meas_temp',\
                      'dir_dec','dir_inc','magn_moment','software_packages']
    spec_reqd_columns=['specimen','sample','method_codes','volume',\
                       'citations',]
    samp_reqd_columns=['sample','site','method_codes',\
                       'citations','azimuth','azimuth_dec_correction','dip',\
                      'bed_dip','bed_dip_direction']
    site_reqd_columns=['site','location','lat','lon','geologic_classes','geologic_types','lithologies',\
                      'citations','method_codes']
    loc_reqd_columns=['location','location_type','geologic_classes','geologic_types','lithologies',\
                      'citations','method_codes','lat_s','lat_n','lon_w','lon_e','age_low','age_high',\
                     'age_unit']
    meta_dict={}
    try:
        lines=pmag.open_file(mag_file_path)
        if not lines:
            print("you must provide a valid mag_file")
            return False, "you must provide a valid mag_file"
        line1=lines[1].split()
        if 'NAME' in line1[0]: # this is a file with meta data
            skiprows=1
            line2=lines[2].split('\t')
            skiprows=4      
            for k in range(len(line1)):
                meta_dict[line1[k]]=line2[k]
            columns=['#','DEMAG','CD','CI','ISD','ISI','RD','RI','M','J']
            meas_df = pd.read_csv(mag_file_path, sep='\t',\
                              skiprows=skiprows,header=None,usecols=range(len(columns)))
            meas_df.columns=columns
        else:
            meas_df=pd.read_csv(mag_file_path,delim_whitespace=True,header=0) # no meta data

    except Exception as ex:
        print('ex', ex)
        print("bad asc file")
        return False, "bad asc file"

    if specnum != 0:
        sample = specname[:specnum]
    else:
        sample = specname
    methods = gmeths.split(':')
    # parse out the site name
    sample=specname
    if samp_con=='8':
        sss = pmag.parse_site(specname, samp_con, Z)
        sample=sss[1]
        site=sss[2]
    else: 
        site = pmag.parse_site(sample, samp_con, Z)
        if specnum!=0:
            sample=specname[:specnum]
    if meta_dict and meta_dict['GM']!='0': # declination correction provided
        if 'SO-MAG' in methods:
            del methods[methods.index('SO-MAG')]
        methods.append('SO-CMD-NORTH')
        meths = reduce(lambda x, y: x+':'+y, methods)
        method_codes = meths
# start by creating the measurements table
    meas_magic_df=pd.DataFrame(columns=meas_reqd_columns)
    meas_magic_df['dir_dec']=meas_df['CD'].values
    meas_magic_df['dir_inc']=meas_df['CI'].values
    meas_magic_df['magn_moment']=meas_df['J'].astype('float')*1e-3 # convert from emu to Am2
    meas_magic_df.fillna("",inplace=True)
    meas_magic_df['treat_dc_field']=0
    meas_magic_df['treat_dc_field_phi']=0
    meas_magic_df['treat_dc_field_theta']=0
    meas_magic_df['treat_ac_field']=0
    meas_magic_df['meas_temp']=273
    meas_magic_df['specimen']=specname
    meas_magic_df['standard']='u'
#    meas_magic_df['measurement']=range(len(meas_df))
#    meas_magic_df['sequence']=range(len(meas_df))
    meas_magic_df['quality']='g'
    meas_magic_df['citations']='This study'
    meas_magic_df['DEMAG']=meas_df['DEMAG'].values
    meas_magic_df['method_codes']=""
    meas_magic_df['software_packages']=pmag.get_version()
    meas_magic_df.loc[meas_magic_df['DEMAG'].str.contains('NRM'),'method_codes']='LT-NO' # NRM step
    meas_magic_df.loc[meas_magic_df['DEMAG'].str.contains('NRM'),'treat_temp']=273
    if experiment=='Demag':
        # pick out thermal demag
        therm_df=meas_magic_df[meas_magic_df['DEMAG'].str.contains('C')]
        meas_magic_df=meas_magic_df[meas_magic_df['DEMAG'].str.contains('C')==False]
        therm_df['method_codes']='LT-T-Z'
        temps=therm_df['DEMAG'].str.strip('C')
        therm_df['treat_temp']=temps.astype('float')+273 # convert to Kelvin
        meas_magic_df=pd.concat([meas_magic_df,therm_df])
        # pick out AF demag
        af_df=meas_magic_df[meas_magic_df['DEMAG'].str.contains('mT')]
        meas_magic_df=meas_magic_df[meas_magic_df['DEMAG'].str.contains('mT')==False]
        af_df['method_codes']='LT-AF-Z'
        afs=af_df['DEMAG'].str.strip('mT')
        af_df['treat_ac_field']=afs.astype('float')*1e-3 # convert to tesla
        meas_magic_df=pd.concat([meas_magic_df,af_df])
    else:
        print ('experiment ',experiment,' not supported yet - email ltauxe@ucsd.edu for support')
    meths=list(meas_magic_df['method_codes'].unique())
    if 'LT-T-Z' in meths and experiment=='Demag':
        meths.append('LP-DIR-T')
    if 'LT-AF-Z' in meths and experiment=='Demag':
        meths.append('LP-DIR-AF')


    exp_methods,methods="",""
    for meth in meths:
        exp_methods=exp_methods+"_"+meth
        methods=methods+':'+meth
    methods=methods.strip(':')
    meas_magic_df['experiment']=specname+exp_methods
    meas_magic_df.drop(columns=['DEMAG'],inplace=True)
    meas_dicts=meas_magic_df.to_dict('records')
    dicts=pmag.measurements_methods3(meas_dicts,noave)
    
    pmag.magic_write(dir_path+'/'+meas_file,dicts,'measurements')
# now do specimens table
    spec_dict={}
    for col in spec_reqd_columns:
        spec_dict[col]="" # initialize specimen dictionary
    spec_dict['specimen']=specname
    spec_dict['sample']=sample
    spec_dict['method_codes']=methods
    spec_dict['citations']='This study'
    if meta_dict:
        spec_dict['volume']=float(meta_dict['SIZE'])*1e-6 # convert to m^3
    pmag.magic_write(dir_path+'/'+spec_file,[spec_dict],'specimens')
    # sample table
    samp_dict={}
    for col in samp_reqd_columns:
        samp_dict[col]="" # initialize specimen dictionary
    samp_dict['site']=site
    samp_dict['sample']=sample
    samp_dict['method_codes']=methods
    samp_dict['citations']='This study'
    if meta_dict:
        labaz, labdip = pmag.orient(float(meta_dict['CA']), float(meta_dict['CP']), or_con)
        samp_dict['azimuth']=labaz
        samp_dict['dip']=labdip
        samp_dict['bed_dip_direction']=meta_dict['DA']
        samp_dict['bed_dip']=meta_dict['DP']
    pmag.magic_write(dir_path+'/'+samp_file,[samp_dict],'samples')
    # sites table
    site_dict={}
    for col in site_reqd_columns:
        site_dict[col]="" # initialize specimen dictionary
    site_dict['site']=site
    site_dict['location']=location
    site_dict['method_codes']=methods
    site_dict['citations']='This study'
    pmag.magic_write(dir_path+'/'+site_file,[site_dict],'sites')
    # locations table
    loc_dict={}
    for col in loc_reqd_columns:
        loc_dict[col]="" # initialize specimen dictionary
    loc_dict['location']=location
    loc_dict['method_codes']=methods
    loc_dict['citations']='This study'
    pmag.magic_write(dir_path+'/'+loc_file,[loc_dict],'locations')
    return True, meas_file


    






# AGM magic conversion






def agm(agm_file, dir_path=".", input_dir_path="",
        meas_outfile="", spec_outfile="", samp_outfile="",
        site_outfile="", loc_outfile="", spec_infile="",
        samp_infile="", site_infile="",
        specimen="", specnum=0, samp_con="1", location="unknown",
        instrument="", bak=False, syn=False, syntype="",
        units="cgs", fmt='new', user='',phi='0',theta='0'):
    """
    Convert AGM format file to MagIC file(s)

    Parameters
    ----------
    agm_file : str
        input file name
    dir_path : str
        working directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    meas_outfile : str
        output measurement file name, default ""
        (default output is SPECNAME.magic)
    spec_outfile : str
        output specimen file name, default ""
        (default output is SPEC_specimens.txt)
    samp_outfile: str
        output sample file name, default ""
        (default output is SPEC_samples.txt)
    site_outfile : str
        output site file name, default ""
        (default output is SPEC_sites.txt)
    loc_outfile : str
        output location file name, default ""
        (default output is SPEC_locations.txt)
    samp_infile : str
        existing sample infile (not required), default ""
    site_infile : str
        existing site infile (not required), default ""
    specimen : str
        specimen name, default ""
        (default is to take base of input file name, e.g. SPEC.agm)
    specnum : int
        number of characters to designate a specimen, default 0
    samp_con : str
        sample/site naming convention, default '1', see info below
    location : str
        location name, default "unknown"
    instrument : str
        instrument name, default ""
    bak : bool
       IRM backfield curve, default False
    syn : bool
       synthetic, default False
    syntype : str
       synthetic type, default ""
    units : str
       units, ['cgs','SI']  default "cgs"
    phi : str
       phi, orientation of applied field to sample ,default='0'
    theta : str
       theta, orientation of applied field to sample ,default='0'
    fmt: str
        input format, options: ('new', 'old', 'xy', default 'new')
    user : user name

    Returns
    ---------
    Tuple : (True or False indicating if conversion was successful, meas_file name written)

    Info
    --------
    Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY


    """
    # initialize some stuff
    citations = 'This study'
    meth = "LP-HYS"
    version_num = pmag.get_version()
    Samps, Sites = [], []
    #noave = 1

    # get args
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    specnum = - int(specnum)
    if not specimen:
        # grab the specimen name from the input file name
        specimen = agm_file.split('.')[0]
    if not meas_outfile:
        meas_outfile = specimen + '.magic'
    if not spec_outfile:
        spec_outfile = specimen + '_specimens.txt'
    if not samp_outfile:
        samp_file = specimen + '_samples.txt'
    if not site_outfile:
        site_file = specimen + '_sites.txt'
    if not loc_outfile:
        loc_outfile = specimen + '_locations.txt'
    if bak:
        meth = "LP-IRM-DCD"
        output = output_dir_path + "/irm.magic"
    if "4" == samp_con[0]:
        if "-" not in samp_con:
            print(
                "naming convention option [4] must be in form 4-Z where Z is an integer")
            print('---------------')
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "4"
    if "7" == samp_con[0]:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "7"
    else:
        Z = 0

    # read stuff in
    if site_infile:
        Sites, file_type = pmag.magic_read(site_infile)
    if samp_infile:
        Samps, file_type = pmag.magic_read(samp_infile)
    if spec_infile:
        Specs, file_type = pmag.magic_read(spec_infile)
    if agm_file:
        agm_file = pmag.resolve_file_name(agm_file, input_dir_path)
        Data = pmag.open_file(agm_file)
        if not Data:
            print("you must provide a valid agm_file")
            return False, "you must provide a valid agm_file"
    if not agm_file:
        print(__doc__)
        print("agm_file field is required option")
        return False, "agm_file field is required option"
    if "ASCII" not in Data[0] and fmt != 'xy':
        fmt = 'new'
    measnum, start, end = 1, 0, 0
    if fmt == 'new':  # new Micromag formatted file
        end = 2
        for skip in range(len(Data)):
            line = Data[skip]
            rec = line.strip('\n').strip('\r').split()
            if 'Units' in line:
                units = rec[-1]
            if 'Orientation' in line:
                phi = rec[-1]
            if "Raw" in rec:
                start = skip + 2
            if ("Field" in rec) and ("Moment" in rec) and (not start):
                start = skip + 2
                break
    elif fmt == 'old':
        start = 2
        end = 1

    MeasRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    version_num = pmag.get_version()

    ##################################
    # parse data
    stop = len(Data) - end
    for line in Data[start:stop]:  # skip header stuff
        MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}
        # take care of some paper work
        if not syn:
            MeasRec["specimen"] = specimen
            if specnum != 0:
                sample = specimen[:specnum]
            else:
                sample = specimen
            if samp_infile and Samps:  # if samp_infile was provided AND yielded sample data
                samp = pmag.get_dictitem(Samps, 'sample', sample, 'T')
                if len(samp) > 0:
                    site = samp[0]["site"]
                else:
                    site = ''
            if site_infile and Sites:  # if samp_infile was provided AND yielded sample data
                sites = pmag.get_dictitem(Sites, 'sample', sample, 'T')
                if len(sites) > 0:
                    site = sites[0]["site"]
                else:
                    site = ''
            else:
                site = pmag.parse_site(sample, samp_con, Z)
            if location != '' and location not in [x['location'] if 'location' in list(x.keys()) else '' for x in LocRecs]:
                LocRec['location'] = location
                LocRecs.append(LocRec)
            if site != '' and site not in [x['site'] if 'site' in list(x.keys()) else '' for x in SiteRecs]:
                SiteRec['location'] = location
                SiteRec['site'] = site
                SiteRecs.append(SiteRec)
            if sample != '' and sample not in [x['sample'] if 'sample' in list(x.keys()) else '' for x in SampRecs]:
                SampRec['site'] = site
                SampRec['sample'] = sample
                SampRecs.append(SampRec)
            if specimen != '' and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else '' for x in SpecRecs]:
                SpecRec["specimen"] = specimen
                SpecRec['sample'] = sample
                SpecRecs.append(SpecRec)
        else:
            SampRec["material_type"] = syntype
            MeasRec["specimen"] = specimen
            MeasRec["user"] = user
            if specnum != 0:
                sample = specimen[:specnum]
            else:
                sample = specimen
            site = pmag.parse_site(sample, samp_con, Z)
            if location != '' and location not in [x['location'] if 'location' in list(x.keys()) else '' for x in LocRecs]:
                LocRec['location'] = location
                LocRecs.append(LocRec)
            if site != '' and site not in [x['site'] if 'site' in list(x.keys()) else '' for x in SiteRecs]:
                SiteRec['location'] = location
                SiteRec['site'] = site
                SiteRecs.append(SiteRec)
            if sample != '' and sample not in [x['sample'] if 'sample' in list(x.keys()) else '' for x in SampRecs]:
                SampRec['site'] = site
                SampRec['sample'] = sample
                SampRecs.append(SampRec)
            if specimen != '' and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else '' for x in SpecRecs]:
                SpecRec["specimen"] = specimen
                SpecRec['sample'] = sample
                SpecRecs.append(SpecRec)
        MeasRec['instrument_codes'] = instrument
        MeasRec['method_codes'] = meth
        if phi!='0':
            MeasRec["treat_dc_field_phi"] = phi
        if theta!='0':
            MeasRec["treat_dc_field_theta"] = theta
        MeasRec['experiment'] = specimen + ':' + meth
        if fmt == 'xy':
            rec = list(line.strip('\n').split())
        else:
            rec = list(line.strip('\n').strip('\r').split(','))
        if rec[0] != "":
            if units == 'cgs':
                field = float(rec[0]) * 1e-4  # convert from oe to tesla
            else:
                field = float(rec[0])  # field in tesla
            if meth == "LP-HYS":
                MeasRec['meas_field_dc'] = '%10.3e' % (field)
                MeasRec['treat_dc_field'] = '0'
            else:
                MeasRec['meas_field_dc'] = '0'
                MeasRec['treat_dc_field'] = '%10.3e' % (field)
            if units == 'cgs':
                MeasRec['magn_moment'] = '%10.3e' % (
                    float(rec[1]) * 1e-3)  # convert from emu to Am^2
            else:
                MeasRec['magn_moment'] = '%10.3e' % (float(rec[1]))  # Am^2
            MeasRec['treat_temp'] = '273'  # temp in kelvin
            MeasRec['meas_temp'] = '273'  # temp in kelvin
            MeasRec['quality'] = 'g'
            MeasRec['standard'] = 'u'
            MeasRec['treat_step_num'] = '%i' % (measnum)
            MeasRec['measurement'] = specimen + ":" + meth + '%i' % (measnum)
            measnum += 1
            MeasRec['software_packages'] = version_num
            MeasRec['description'] = ""
            MeasRecs.append(MeasRec)
    # we have to relabel LP-HYS method codes.  initial loop is LP-IMT, minor
    # loops are LP-M  - do this in measurements_methods function
    if meth == 'LP-HYS':
        recnum = 0
        while float(MeasRecs[recnum]['meas_field_dc']) < float(MeasRecs[recnum + 1]['meas_field_dc']) and recnum + 1 < len(MeasRecs):  # this is LP-IMAG
            MeasRecs[recnum]['method_codes'] = 'LP-IMAG'
            MeasRecs[recnum]['experiment'] = MeasRecs[recnum]['specimen'] + \
                ":" + 'LP-IMAG'
            recnum += 1
#
    con = cb.Contribution(output_dir_path, read_tables=[])

    # create MagIC tables
    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    # MeasOuts=pmag.measurements_methods3(MeasRecs,noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasRecs)
    # write MagIC tables to file
    con.write_table_to_file('specimens', custom_name=spec_outfile)
    con.write_table_to_file('samples', custom_name=samp_outfile)
    con.write_table_to_file('sites', custom_name=site_outfile)
    con.write_table_to_file('locations', custom_name=loc_outfile)
    con.write_table_to_file('measurements', custom_name=meas_outfile)

    return True, meas_outfile

# BGC_magic conversion


def bgc(mag_file, dir_path=".", input_dir_path="",
        meas_file='measurements.txt', spec_file='specimens.txt', samp_file='samples.txt',
        site_file='sites.txt', loc_file='locations.txt', append=False,
        location="unknown", site="", samp_con='1', specnum=0,
        meth_code="LP-NO", volume=12, user="", timezone='US/Pacific', noave=False):

    """
    Convert BGC format file to MagIC file(s)

    Parameters
    ----------
    mag_file : str
        input file name
    dir_path : str
        working directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    meas_file : str
        output measurement file name, default "measurements.txt"
    spec_file : str
        output specimen file name, default "specimens.txt"
    samp_file: str
        output sample file name, default "samples.txt"
    site_file : str
        output site file name, default "sites.txt"
    loc_file : str
        output location file name, default "locations.txt"
    append : bool
        append output files to existing files instead of overwrite, default False
    location : str
        location name, default "unknown"
    site : str
        site name, default ""
    samp_con : str
        sample/site naming convention, default '1', see info below
    specnum : int
        number of characters to designate a specimen, default 0
    meth_code : str
        orientation method codes, default "LP-NO"
        e.g. [SO-MAG, SO-SUN, SO-SIGHT, ...]
    volume : float
        volume in ccs, default 12.
    user : str
        user name, default ""
    timezone : str
        timezone in pytz library format, default "US/Pacific"
        list of timezones can be found at http://pytz.sourceforge.net/
    noave : bool
       do not average duplicate measurements, default False (so by default, DO average)

    Returns
    ---------
    Tuple : (True or False indicating if conversion was successful, meas_file name written)

    Info
    --------
    Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name same as sample
        [6] site is entered under a separate column -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY

    """

    version_num = pmag.get_version()
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    samp_con = str(samp_con)
    specnum = - int(specnum)
    volume *= 1e-6  # convert cc to m^3

    if "4" in samp_con:
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = int(samp_con.split("-")[1])
            samp_con = "4"
    if "7" in samp_con:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = int(samp_con.split("-")[1])
            samp_con = "7"
    else:
        Z = 1

    # format variables
    mag_file = os.path.join(input_dir_path, mag_file)
    if not os.path.isfile(mag_file):
        print("%s is not a BGC file" % mag_file)
        return False, 'You must provide a BCG format file'

    # Open up the BGC file and read the header information
    print('mag_file in bgc_magic', mag_file)
    pre_data = open(mag_file, 'r')
    line = pre_data.readline()
    line_items = line.split(' ')
    specimen = line_items[2]
    specimen = specimen.replace('\n', '')
    line = pre_data.readline()
    line = pre_data.readline()
    line_items = line.split('\t')
    azimuth = float(line_items[1])
    dip = float(line_items[2])
    bed_dip = line_items[3]
    sample_bed_azimuth = line_items[4]
    lon = line_items[5]
    lat = line_items[6]
    tmp_volume = line_items[7]
    if tmp_volume != 0.0:
        volume = float(tmp_volume) * 1e-6
    pre_data.close()

    data = pd.read_csv(mag_file, sep='\t', header=3, index_col=False)

    cart = np.array([data['X'], data['Y'], data['Z']]).transpose()
    direction = pmag.cart2dir(cart).transpose()

    data['dir_dec'] = direction[0]
    data['dir_inc'] = direction[1]
    # the data are in EMU - this converts to Am^2
    data['magn_moment'] = direction[2] / 1000
    data['magn_volume'] = (direction[2] / 1000) / \
        volume  # EMU  - data converted to A/m

    # Configure the magic_measurements table
    MeasRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    for rowNum, row in data.iterrows():
        MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}

        if specnum != 0:
            sample = specimen[:specnum]
        else:
            sample = specimen
        if site == '':
            site = pmag.parse_site(sample, samp_con, Z)

        if specimen != "" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
            SpecRec['specimen'] = specimen
            SpecRec['sample'] = sample
            SpecRec['volume'] = volume
            SpecRec['analysts'] = user
            SpecRec['citations'] = 'This study'
            SpecRecs.append(SpecRec)
        if sample != "" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
            SampRec['sample'] = sample
            SampRec['site'] = site
            SampRec['azimuth'] = azimuth
            SampRec['dip'] = dip
            SampRec['bed_dip_direction'] = sample_bed_azimuth
            SampRec['bed_dip'] = bed_dip
            SampRec['method_codes'] = meth_code
            SampRec['analysts'] = user
            SampRec['citations'] = 'This study'
            SampRecs.append(SampRec)
        if site != "" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
            SiteRec['site'] = site
            SiteRec['location'] = location
            SiteRec['lat'] = lat
            SiteRec['lon'] = lon
            SiteRec['analysts'] = user
            SiteRec['citations'] = 'This study'
            SiteRecs.append(SiteRec)
        if location != "" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
            LocRec['location'] = location
            LocRec['analysts'] = user
            LocRec['citations'] = 'This study'
            LocRec['lat_n'] = lat
            LocRec['lon_e'] = lon
            LocRec['lat_s'] = lat
            LocRec['lon_w'] = lon
            LocRecs.append(LocRec)

        MeasRec['description'] = 'Date: ' + \
            str(row['Date']) + ' Time: ' + str(row['Time'])
        if '.' in row['Date']:
            datelist = row['Date'].split('.')
        elif '/' in row['Date']:
            datelist = row['Date'].split('/')
        elif '-' in row['Date']:
            datelist = row['Date'].split('-')
        else:
            print(
                "unrecognized date formatting on one of the measurement entries for specimen %s" % specimen)
            datelist = ['', '', '']
        if ':' in row['Time']:
            timelist = row['Time'].split(':')
        else:
            print(
                "unrecognized time formatting on one of the measurement entries for specimen %s" % specimen)
            timelist = ['', '', '']
        datelist[2] = '19' + \
            datelist[2] if len(datelist[2]) <= 2 else datelist[2]
        dt = ":".join([datelist[1], datelist[0], datelist[2],
                       timelist[0], timelist[1], timelist[2]])
        local = pytz.timezone(timezone)
        naive = datetime.datetime.strptime(dt, "%m:%d:%Y:%H:%M:%S")
        local_dt = local.localize(naive, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        timestamp = utc_dt.strftime("%Y-%m-%dT%H:%M:%S")+"Z"
        MeasRec["timestamp"] = timestamp
        MeasRec["citations"] = "This study"
        MeasRec['software_packages'] = version_num
        MeasRec["treat_temp"] = '%8.3e' % (273)  # room temp in kelvin
        MeasRec["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
        MeasRec["quality"] = 'g'
        MeasRec["standard"] = 'u'
        MeasRec["treat_step_num"] = rowNum
        MeasRec["specimen"] = specimen
        MeasRec["treat_ac_field"] = '0'
        if row['DM Val'] == '0':
            meas_type = "LT-NO"
        elif int(row['DM Type']) > 0.0:
            meas_type = "LT-AF-Z"
            treat = float(row['DM Val'])
            MeasRec["treat_ac_field"] = '%8.3e' % (
                treat*1e-3)  # convert from mT to tesla
        elif int(row['DM Type']) == -1:
            meas_type = "LT-T-Z"
            treat = float(row['DM Val'])
            MeasRec["treat_temp"] = '%8.3e' % (treat+273.)  # temp in kelvin
        else:
            print("measurement type unknown:",
                  row['DM Type'], " in row ", rowNum)
        MeasRec["magn_moment"] = str(row['magn_moment'])
        MeasRec["magn_volume"] = str(row['magn_volume'])
        MeasRec["dir_dec"] = str(row['dir_dec'])
        MeasRec["dir_inc"] = str(row['dir_inc'])
        MeasRec['method_codes'] = meas_type
        MeasRec['dir_csd'] = '0.0'  # added due to magic.write error
        MeasRec['meas_n_orient'] = '1'  # added due to magic.write error
        MeasRecs.append(MeasRec.copy())

    con = cb.Contribution(output_dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.write_table_to_file('specimens', custom_name=spec_file, append=append)
    con.write_table_to_file('samples', custom_name=samp_file, append=append)
    con.write_table_to_file('sites', custom_name=site_file, append=append)
    con.write_table_to_file('locations', custom_name=loc_file, append=append)
    meas_file = con.write_table_to_file(
        'measurements', custom_name=meas_file, append=append)

    return True, meas_file


### CIT_magic conversion

def cit(dir_path=".", input_dir_path="", magfile="", user="", meas_file="measurements.txt",
        spec_file="specimens.txt", samp_file="samples.txt",
        site_file="sites.txt", loc_file="locations.txt", locname="unknown",
        sitename="", sampname="", methods=['SO-MAG'], specnum=0, samp_con='3',
        norm='cc', noave=False, meas_n_orient='8',
        labfield=0, phi=0, theta=0):
    """
    Converts CIT formatted Magnetometer data into MagIC format for Analysis and contribution to the MagIC database

    Parameters
    -----------
    dir_path : directory to output files to (default : current directory)
    input_dir_path : directory to input files (only needed if different from dir_path!)
    magfile : magnetometer file (.sam) to convert to MagIC (required)
    user : colon delimited list of analysts (default : "")
    meas_file : measurement file name to output (default : measurements.txt)
    spec_file : specimen file name to output (default : specimens.txt)
    samp_file : sample file name to output (default : samples.txt)
    site_file : site file name to output (default : site.txt)
    loc_file : location file name to output (default : locations.txt)
    locname : location name
    sitename : site name set by user instead of using samp_con
    sampname : sample name set by user instead of using samp_con
    methods : colon delimited list of sample method codes. full list here (https://www2.earthref.org/MagIC/method-codes) (default : SO-MAG)
    specnum : number of terminal characters that identify a specimen
    norm : is volume or mass normalization using cgs or si units (options : cc,m3,g,kg) (default : cc)
    oersted : demag step values are in Oersted
    noave : average measurement data or not. False is average, True is don't average. (default : False)
    samp_con : sample naming convention options as follows:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in sitename column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
    meas_n_orient : Number of different orientations in measurement (default : 8)
    labfield : DC_FIELD in microTesla (default : 0)
    phi : DC_PHI in degrees (default : 0)
    theta : DC_THETA in degrees (default : 0)

    Returns
    -----------
    type - Tuple : (True or False indicating if conversion was successful, meas_file name written)
    """

    def get_dc_params(FIRST_GET_DC, specimen, treat_type, yn):
        """
        Prompts user for DC field data if not provided, just an encapsulation function for the above program and should not be used elsewhere.

        Parameters
        -----------
        FIRST_GET_DC : is this the first time you are asking for DC data?
        specimen : what specimen do you want DC data for?
        treat_type : what kind of step was it? PTM, Tail, in field, zero field?
        yn : is DC field constant or varrying? (y = constant, n = varrying)

        Returns
        -----------
        GET_DC_PARAMS : weather or not to rerun this function
        FIRST_GET_DC : same as above
        yn : same as above
        DC_FIELD : field strength in Tesla
        DC_PHI : field azimuth
        DC_THETA : field polar angle
        """
        if FIRST_GET_DC:
            yn = input(
                "Is the DC field used in this IZZI study constant or does it varry between specimen or step? (y=const) [y/N]: ")
            FIRST_GET_DC = False
        if "y" == yn:
            DC_FIELD, DC_PHI, DC_THETA = list(map(float, eval(input(
                "What DC field, Phi, and Theta was used for all steps? (float (in microTesla),float,float): "))))
            GET_DC_PARAMS = False
        else:
            DC_FIELD, DC_PHI, DC_THETA = list(map(float, eval(input(
                "What DC field, Phi, and Theta was used for specimen %s and step %s? (float (in microTesla),float,float): " % (str(specimen), str(treat_type))))))
        return GET_DC_PARAMS, FIRST_GET_DC, yn, DC_FIELD*1e-6, DC_PHI, DC_THETA

    specnum = - int(specnum)
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    DC_FIELD = float(labfield) * 1e-6
    DC_PHI = float(phi)
    DC_THETA = float(theta)
    #try:
    #    DC_FIELD = float(labfield) * 1e-6
    #    DC_PHI = float(phi)
    #    DC_THETA = float(theta)
#    except ValueError:
#        raise ValueError(
#            'problem with your dc parameters. please provide a labfield in microTesla and a phi and theta in degrees.')
#    yn = ''
#    if DC_FIELD == 0 and DC_PHI == 0 and DC_THETA == 0:
#        print('-I- Required values for labfield, phi, and theta not provided!  Will try to get these interactively')
#        GET_DC_PARAMS = True
#    else:
#        GET_DC_PARAMS = False

# With the above commented out( GET_DC_PARAMS does not get set and this function fails below so setting it here. NAJ
    GET_DC_PARAMS = False
    if locname == '' or locname == None:
        locname = 'unknown'
    if "4" in samp_con:
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "4"
    elif "7" in samp_con:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "7"
    else:
        Z = 1

    # get file names and open magfile to start reading data
    magfile = pmag.resolve_file_name(magfile, input_dir_path)
    input_dir_path = os.path.split(magfile)[0]
    FIRST_GET_DC = True
    try:
        file_input = open(magfile, 'r')
    except IOError as ex:
        print(ex)
        print(("bad sam file name: ", magfile))
        return False, "bad sam file name"
    File = file_input.readlines()
    file_input.close()
    if len(File) == 1:
        File = File[0].split('\r')
        File = [x+"\r\n" for x in File]

    # define initial variables
    SpecRecs, SampRecs, SiteRecs, LocRecs, MeasRecs = [], [], [], [], []
    sids, ln, format, citations = [], 0, 'CIT', "This study"
    formats = ['CIT', '2G', 'APP', 'JRA']

    if File[ln].strip() == 'CIT':
        ln += 1
    LocRec = {}
    LocRec["location"] = locname
    LocRec["citations"] = citations
    LocRec['analysts'] = user
    comment = File[ln]
    if comment == 'CIT':
        format = comment
        ln += 1
    comment = File[ln]
    print(comment)
    ln += 1
    specimens, samples, sites = [], [], []
    if format == 'CIT':
        line = File[ln].split()
        site_lat = line[0]
        site_lon = line[1]
        LocRec["lat_n"] = site_lat
        LocRec["lon_e"] = site_lon
        LocRec["lat_s"] = site_lat
        LocRec["lon_w"] = site_lon
        LocRecs.append(LocRec)
        Cdec = float(line[2])
        for k in range(ln+1, len(File)):
            line = File[k]
            rec = line.split()
            if rec == []:
                continue
            specimen = rec[0]
            specimens.append(specimen)
    for specimen in specimens:
        SpecRec, SampRec, SiteRec = {}, {}, {}
        if sampname == "":
            if specnum != 0:
               sample = specimen[:specnum]
            else:
               sample = specimen
        else:
            sample=sampname
        if sitename:
            site = sitename
        else:
            site = pmag.parse_site(sample, samp_con, Z)
        SpecRec['specimen'] = specimen
        SpecRec['sample'] = sample
        SpecRec['citations'] = citations
        SpecRec['analysts'] = user
        SampRec['sample'] = sample
        SampRec['site'] = site
        SampRec['citations'] = citations
        SampRec['method_codes'] = methods
        SampRec['azimuth_dec_correction'] = '%7.1f' % (Cdec)
        SampRec['analysts'] = user
        SiteRec['site'] = site
        SiteRec['location'] = locname
        SiteRec['citations'] = citations
        SiteRec['lat'] = site_lat
        SiteRec['lon'] = site_lon
        SiteRec['analysts'] = user
        f = open(os.path.join(input_dir_path, specimen), 'r')
        Lines = f.readlines()
        f.close()
        comment = ""
        line = Lines[0].split()
        if len(line) > 2:
            comment = line[2]
        info = Lines[1].split()
        volmass = float(info[-1])
        if volmass == 1.0:
            print('Warning: Specimen volume set to 1.0.')
            print('Warning: If volume/mass really is 1.0, set volume/mass to 1.001')
            print('Warning: specimen method code LP-NOMAG set.')
            SpecRec['weight'] = ""
            SpecRec['volume'] = ""
            SpecRec['method_codes'] = 'LP-NOMAG'
        elif norm == "gm":
            SpecRec['volume'] = ''
            SpecRec['weight'] = '%10.3e' % volmass*1e-3
        elif norm == "kg":
            SpecRec['volume'] = ''
            SpecRec['weight'] = '%10.3e'*volmass
        elif norm == "cc":
            SpecRec['weight'] = ""
            SpecRec['volume'] = '%10.3e' % (volmass*1e-6)
        elif norm == "m3":
            SpecRec['weight'] = ""
            SpecRec['volume'] = '%10.3e' % (volmass)
        else:
            print('Warning: Unknown normalization unit ',
                  norm, '. Using default of cc')
            SpecRec['weight'] = ""
            SpecRec['volume'] = '%10.3e' % (volmass*1e-6)
        dip = float(info[-2])
        dip_direction = float(info[-3])+Cdec+90.
        sample_dip = -float(info[-4])
        sample_azimuth = float(info[-5])+Cdec-90.
        if len(info) > 5:
            SampRec['height'] = info[-6]
        else:
            SampRec['height'] = '0'
        SampRec['azimuth'] = '%7.1f' % (sample_azimuth)
        SampRec['dip'] = '%7.1f' % (sample_dip)
        SampRec['bed_dip'] = '%7.1f' % (dip)
        SampRec['bed_dip_direction'] = '%7.1f' % (dip_direction)
        SampRec['geologic_classes'] = ''
        SampRec['geologic_types'] = ''
        SampRec['lithologies'] = ''
        if Cdec != 0 or Cdec != "":
            SampRec['method_codes'] = 'SO-CMD-NORTH'
        else:
            SampRec['method_codes'] = 'SO-MAG'
        for line in Lines[2:len(Lines)]:
            if line == '\n':
                continue
            MeasRec = SpecRec.copy()
            MeasRec.pop('sample')
            MeasRec['analysts'] = user
#           Remove volume and weight as they do not exits in the magic_measurement table
            del MeasRec["volume"]
            del MeasRec["weight"]
            # USGS files have blank for an AF demag value when measurement is the NRM. njarboe
            if line[0:6] == 'AF    ':
                line = 'NRM' + line[3:]
            treat_type = line[0:3]
            if treat_type[1] == '.':
                treat_type = 'NRM'
            treat = line[2:6]
            try:
                float(treat)
            except ValueError:
                treat = line[3:6]
                if treat.split() == '':
                    treat = '0'
                try:
                    float(treat)
                except ValueError:
                    treat = line.split()[1]
            if treat_type.startswith('NRM'):
                MeasRec['method_codes'] = 'LT-NO'
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = '273'
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
            elif treat_type.startswith('LT') or treat_type.upper().startswith('LN2'):
                MeasRec['method_codes'] = 'LT-LT-Z'
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = '77'
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
            elif treat_type.startswith('AF') or treat_type.startswith('MAF'):
                MeasRec['method_codes'] = 'LT-AF-Z'
                if treat_type.startswith('AFz'):
                    MeasRec['method_codes'] = 'LT-AF-Z-Z'
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = '273'
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                if treat.strip() == '':
                    MeasRec['treat_ac_field'] = '0'
                else:
                    try:
                        MeasRec['treat_ac_field'] = '%10.3e' % (
                            float(treat)*1e-3)
                    except ValueError as e:
                        print(os.path.join(input_dir_path, specimen))
                        raise e
                if MeasRec['treat_ac_field'] != '0':
                    MeasRec['treat_ac_field'] = '%10.3e' % (
                        float(MeasRec['treat_ac_field'])/10)
            elif treat_type.startswith('ARM'):
                MeasRec['method_codes'] = "LP-ARM"
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = '273'
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                if treat.strip() == '':
                    MeasRec['treat_ac_field'] = '0'
                else:
                    MeasRec['method_codes'] = "LP-ARM-AFD"
                    MeasRec['treat_ac_field'] = '%10.3e' % (float(treat)*1e-3)
            # ARM with bias field defined in first 6 charachters for Scott Bogue
            elif treat_type.startswith('B'):      # "B" code for Scott Bogue.
                # The first two digits after B is the AF demag level in mT and the next 3 are the bias field in uT.
                # Need to straighten out the treatment value.
                AC_DEMAG_FIELD = float(treat_type[1:2])*1e-3  # treat_type contains the AF treatment value in this case
                DC_FIELD=float(treat)*1e-6 # treat is what is normally the last 3 digits of the demag code
                if treat_type[1:2] == '00':
                    MeasRec['method_codes'] = "LP-ARM:LT-NO:LP-DIR-AF"
                else:
                    MeasRec['method_codes'] = "LP-ARM-AFD:LT-AF-Z:LP-DIR-AF"
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = '273'
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '%10.3e' % (AC_DEMAG_FIELD)
                MeasRec['treat_dc_field'] = '%1.2e' % DC_FIELD
            # ARM with bias field defined in first 6 charachters for Scott Bogue
            elif treat_type.startswith('D'): # "D" code for Scott Bogue
                # The first two digits after D is the bias field in uT and the next three are the demag level in orestead (divided by to get mT).
                DC_FIELD=float(treat_type[1:2])*1e-6 # treat is what is normally the last 3 digits of the demag code. In this case used for bias field in uT.
                AC_DEMAG_FIELD = float(treat)*1e-4  # Convert to Tesla. treat_type contains the AF treatment value in oe 
                if treat == '000':
                    MeasRec['method_codes'] = "LP-ARM:LT-NO:LP-DIR-AF"
                else:
                    MeasRec['method_codes'] = "LP-ARM-AFD:LT-AF-Z:LP-DIR-AF"
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = '273'
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '%10.3e' % (AC_DEMAG_FIELD)
                MeasRec['treat_dc_field'] = '%1.2e' % DC_FIELD
            elif treat_type.startswith('IRM'):
                if GET_DC_PARAMS:
                    GET_DC_PARAMS, FIRST_GET_DC, yn, DC_FIELD, DC_PHI, DC_THETA = get_dc_params(
                        FIRST_GET_DC, specimen, treat_type, yn)
                MeasRec['method_codes'] = "LT-IRM"
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = '273'
                MeasRec['treat_dc_field'] = '%1.2e' % DC_FIELD
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
            elif treat_type.startswith('TT'):
                MeasRec['method_codes'] = 'LT-T-Z'
                MeasRec['meas_temp'] = '273'
                if treat.strip() == '':
                    MeasRec['treat_temp'] = '273'
                else:
                    MeasRec['treat_temp'] = '%7.1f' % (float(treat)+273)
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
                #for MIT paleointensity format
                if treat_type[2] == 'I':
                    MeasRec['method_codes'] = 'LT-T-I'
                    MeasRec['treat_dc_field'] = '%1.2e' % DC_FIELD
                elif treat_type[2] == 'P':
                    MeasRec['method_codes'] = 'LT-PTRM-I'
                    MeasRec['treat_dc_field'] = '%1.2e' % DC_FIELD

            elif line[4] == '0':  # assume decimal IZZI format 0 field thus can hardcode the dc fields
                MeasRec['method_codes'] = 'LT-T-Z'
                MeasRec['meas_temp'] = '273'
                try:
                    MeasRec['treat_temp'] = str(int(treat_type) + 273)
                except ValueError as e:
                    print(specimen)
                    raise e
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
            elif line[4] == '1':  # assume decimal IZZI format in constant field
                if GET_DC_PARAMS:
                    GET_DC_PARAMS, FIRST_GET_DC, yn, DC_FIELD, DC_PHI, DC_THETA = get_dc_params(
                        FIRST_GET_DC, specimen, treat_type, yn)
                MeasRec['method_codes'] = 'LT-T-I'
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = str(int(treat_type) + 273)
                MeasRec['treat_dc_field'] = '%1.2e' % DC_FIELD
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
            elif line[4] == '2':  # assume decimal IZZI format PTRM step
                if GET_DC_PARAMS:
                    GET_DC_PARAMS, FIRST_GET_DC, yn, DC_FIELD, DC_PHI, DC_THETA = get_dc_params(
                        FIRST_GET_DC, specimen, treat_type, yn)
                MeasRec['method_codes'] = 'LT-PTRM-I'
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = str(int(treat_type) + 273)
                MeasRec['treat_dc_field'] = '%1.2e' % DC_FIELD
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
            elif line[4] == '3':  # assume decimal IZZI format PTRM tail check
                if GET_DC_PARAMS:
                    GET_DC_PARAMS, FIRST_GET_DC, yn, DC_FIELD, DC_PHI, DC_THETA = get_dc_params(
                        FIRST_GET_DC, specimen, treat_type, yn)
                MeasRec['method_codes'] = 'LT-PTRM-Z'
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = str(int(treat_type) + 273)
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
            else:
                print("trouble with your treatment steps")
            MeasRec['dir_dec'] = line[46:51]
            MeasRec['dir_inc'] = line[52:58]
#           Some MIT files have and extra digit in the exponent of the magnetude.
#           That makes those files not compliant with the cit measurement file spec.
#           Not sure if we should just print an error message and exit. For now we accept the file and fix it.
#           The first digit of the exponent, which should always be zero, is cut out of the line if column 39 is not ' '
            if line[39] != ' ':
                line = line[0:37] + line[38:]
            M = '%8.2e' % (float(line[31:39])*volmass*1e-3)  # convert to Am2
            MeasRec['magn_moment'] = M
            MeasRec['dir_csd'] = '%7.1f' % (eval(line[41:46]))
            MeasRec["meas_n_orient"] = meas_n_orient
            MeasRec['standard'] = 'u'
            if len(line) > 60:
                MeasRec['instrument_codes'] = line[85:].strip('\n \r \t "')
                MeasRec['magn_x_sigma'] = '%8.2e' % (
                    float(line[58:67])*1e-8)  # (convert e-5emu to Am2)
                MeasRec['magn_y_sigma'] = '%8.2e' % (float(line[67:76])*1e-8)
                MeasRec['magn_z_sigma'] = '%8.2e' % (float(line[76:85])*1e-8)
            MeasRecs.append(MeasRec)
        SpecRecs.append(SpecRec)
        if sample not in samples:
            samples.append(sample)
            SampRecs.append(SampRec)
        if site not in sites:
            sites.append(site)
            SiteRecs.append(SiteRec)

    con = cb.Contribution(output_dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.tables['specimens'].write_magic_file(
        custom_name=spec_file, dir_path=output_dir_path)
    con.tables['samples'].write_magic_file(
        custom_name=samp_file, dir_path=output_dir_path)
    con.tables['sites'].write_magic_file(
        custom_name=site_file, dir_path=output_dir_path)
    con.tables['locations'].write_magic_file(
        custom_name=loc_file, dir_path=output_dir_path)
    con.tables['measurements'].write_magic_file(
        custom_name=meas_file, dir_path=output_dir_path)

    return True, meas_file


# generic_magic conversion

def generic(magfile="", dir_path=".", meas_file="measurements.txt",
            spec_file="specimens.txt", samp_file="samples.txt", site_file="sites.txt",
            loc_file="locations.txt", user="", labfield=0, labfield_phi=0, labfield_theta=0,
            experiment="", cooling_times_list=[], sample_nc=[1, 0], site_nc=[1, 0],
            location="unknown", lat="", lon="", noave=False, input_dir_path=""):

    """
    Convert generic file to MagIC file(s)

    Parameters
    ----------
    mag_file : str
        input file name
    dir_path : str
        output directory, default "."
    meas_file : str
        output measurement file name, default "measurements.txt"
    spec_file : str
        output specimen file name, default "specimens.txt"
    samp_file: str
        output sample file name, default "samples.txt"
    site_file : str
        output site file name, default "sites.txt"
    loc_file : str
        output location file name, default "locations.txt"
    user : str
        user name, default ""
    labfield : float
        dc lab field (in micro tesla)
    labfield_phi : float
        declination 0-360
    labfield_theta : float
        inclination -90 - 90
    experiment : str
        experiment type, see info below
    cooling_times_list : list
        cooling times in [K/minutes] separated by comma,
        ordered at the same order as XXX.10,XXX.20 ...XX.70
    sample_nc : list
        sample naming convention, default [1, 0], see info below
    site_nc : list
        site naming convention, default [1, 0], see info below
    location : str
        location name, default "unknown"
    lat : float
        latitude, default ""
    lon : float
        longitude, default ""
    noave : bool
       do not average duplicate measurements, default False (so by default, DO average)
    input_dir_path : str
        input file directory IF different from dir_path, default ""


    Info
    --------
    Experiment type:
        Demag:
            AF and/or Thermal
        PI:
            paleointenisty thermal experiment (ZI/IZ/IZZI)
        ATRM n:

            ATRM in n positions (n=6)

        AARM n:
            AARM in n positions
        CR:
            cooling rate experiment
            The treatment coding of the measurement file should be: XXX.00,XXX.10, XXX.20 ...XX.70 etc. (XXX.00 is optional)
            where XXX in the temperature and .10,.20... are running numbers of the cooling rates steps.
            XXX.00 is optional zerofield baseline. XXX.70 is alteration check.
            if using this type, you must also provide cooling rates in [K/minutes] in cooling_times_list
            separated by comma, ordered at the same order as XXX.10,XXX.20 ...XX.70

            No need to specify the cooling rate for the zerofield
            But users need to make sure that there are no duplicate meaurements in the file

        NLT:
            non-linear-TRM experiment

    Specimen-sample naming convention:
        X determines which kind of convention (initial characters, terminal characters, or delimiter
        Y determines how many characters to remove to go from specimen --> sample OR which delimiter to use
        X=0 Y=n: specimen is distinguished from sample by n initial characters.
                 (example: generic(sample_nc=[0, 4], ...)
                  if n=4 then and specimen = mgf13a then sample = mgf13)
        X=1 Y=n: specimen is distiguished from sample by n terminate characters.
                 (example: generic(sample_nc=[1, 1], ...))
                  if n=1 then and specimen = mgf13a then sample = mgf13)
        X=2 Y=c: specimen is distinguishing from sample by a delimiter.
                 (example: generic(sample_nc=[2, "-"]))
                  if c=- then and specimen = mgf13-a then sample = mgf13)
        default: sample is the same as specimen name

    Sample-site naming convention:
        X determines which kind of convention (initial characters, terminal characters, or delimiter
        Y determines how many characters to remove to go from sample --> site OR which delimiter to use
        X=0 Y=n: sample is distiguished from site by n initial characters.
                 (example: generic(site_nc=[0, 3]))
                  if n=3 then and sample = mgf13 then sample = mgf)
        X=1 Y=n: sample is distiguished from site by n terminate characters.
                 (example: generic(site_nc=[1, 2]))
                  if n=2 and sample = mgf13 then site = mgf)
        X=2 Y=c: specimen is distiguishing from sample by a delimiter.
                 (example: generic(site_nc=[2, "-"]))
                  if c='-' and sample = 'mgf-13' then site = mgf)
        default: site name is the same as sample name


    """

    # --------------------------------------
    # functions
    # --------------------------------------

    def sort_magic_file(path, ignore_lines_n, sort_by_this_name):
        '''
        reads a file with headers. Each line is stored as a dictionary following the headers.
        Lines are sorted in DATA by the sort_by_this_name header
        DATA[sort_by_this_name]=[dictionary1,dictionary2,...]
        '''
        DATA = {}
        fin = open(path, 'r')
        # ignore first lines
        for i in range(ignore_lines_n):
            fin.readline()
        # header
        line = fin.readline()
        header = line.strip('\n').split('\t')
        # print header
        for line in fin.readlines():
            if line[0] == "#":
                continue
            tmp_data = {}
            tmp_line = line.strip('\n').split('\t')
            # print tmp_line
            for i in range(len(tmp_line)):
                if i >= len(header):
                    continue
                tmp_data[header[i]] = tmp_line[i]
            DATA[tmp_data[sort_by_this_name]] = tmp_data
        fin.close()
        return(DATA)

    def read_generic_file(path, average_replicates):
        '''
        reads a generic file format. If average_replicates==True average replicate measurements.
        Rrturns a Data dictionary with measurements line sorted by specimen
        Data[specimen_name][dict1,dict2,...]
        '''
        Data = {}
        Fin = open(path, 'r')
        header = Fin.readline().strip('\n').split('\t')
        duplicates = []
        for line in Fin.readlines():
            tmp_data = {}
            # found_duplicate=False
            l = line.strip('\n').split('\t')
            for i in range(min(len(header), len(l))):
                tmp_data[header[i]] = l[i]
            specimen = tmp_data['specimen']
            if specimen not in list(Data.keys()):
                Data[specimen] = []
            Data[specimen].append(tmp_data)
        Fin.close()
        # search from duplicates
        for specimen in list(Data.keys()):
            x = len(Data[specimen])-1
            new_data = []
            duplicates = []
            for i in range(1, x):
                while i < len(Data[specimen]) and Data[specimen][i]['treatment'] == Data[specimen][i-1]['treatment'] and Data[specimen][i]['treatment_type'] == Data[specimen][i-1]['treatment_type']:
                    duplicates.append(Data[specimen][i])
                    del(Data[specimen][i])
                if len(duplicates) > 0:
                    if average_replicates:
                        duplicates.append(Data[specimen][i-1])
                        Data[specimen][i-1] = average_duplicates(duplicates)
                        print("-W- WARNING: averaging %i duplicates for specimen %s treatmant %s" %
                              (len(duplicates), specimen, duplicates[-1]['treatment']))
                        duplicates = []
                    else:
                        Data[specimen][i-1] = duplicates[-1]
                        print("-W- WARNING: found %i duplicates for specimen %s treatmant %s. Taking the last measurement only" %
                              (len(duplicates), specimen, duplicates[-1]['treatment']))
                        duplicates = []

                if i == len(Data[specimen])-1:
                    break

        return(Data)

    def average_duplicates(duplicates):
        '''
        average replicate measurements.
        '''
        carts_s, carts_g, carts_t = [], [], []
        for rec in duplicates:
            moment = float(rec['moment'])
            if 'dec_s' in list(rec.keys()) and 'inc_s' in list(rec.keys()):
                if rec['dec_s'] != "" and rec['inc_s'] != "":
                    dec_s = float(rec['dec_s'])
                    inc_s = float(rec['inc_s'])
                    cart_s = pmag.dir2cart([dec_s, inc_s, moment])
                    carts_s.append(cart_s)
            if 'dec_g' in list(rec.keys()) and 'inc_g' in list(rec.keys()):
                if rec['dec_g'] != "" and rec['inc_g'] != "":
                    dec_g = float(rec['dec_g'])
                    inc_g = float(rec['inc_g'])
                    cart_g = pmag.dir2cart([dec_g, inc_g, moment])
                    carts_g.append(cart_g)
            if 'dec_t' in list(rec.keys()) and 'inc_t' in list(rec.keys()):
                if rec['dec_t'] != "" and rec['inc_t'] != "":
                    dec_t = float(rec['dec_t'])
                    inc_t = float(rec['inc_t'])
                    cart_t = pmag.dir2cart([dec_t, inc_t, moment])
                    carts_t.append(cart_t)
        if len(carts_s) > 0:
            carts = scipy.array(carts_s)
            x_mean = scipy.mean(carts[:, 0])
            y_mean = scipy.mean(carts[:, 1])
            z_mean = scipy.mean(carts[:, 2])
            mean_dir = pmag.cart2dir([x_mean, y_mean, z_mean])
            mean_dec_s = "%.2f" % mean_dir[0]
            mean_inc_s = "%.2f" % mean_dir[1]
            mean_moment = "%10.3e" % mean_dir[2]
        else:
            mean_dec_s, mean_inc_s = "", ""
        if len(carts_g) > 0:
            carts = scipy.array(carts_g)
            x_mean = scipy.mean(carts[:, 0])
            y_mean = scipy.mean(carts[:, 1])
            z_mean = scipy.mean(carts[:, 2])
            mean_dir = pmag.cart2dir([x_mean, y_mean, z_mean])
            mean_dec_g = "%.2f" % mean_dir[0]
            mean_inc_g = "%.2f" % mean_dir[1]
            mean_moment = "%10.3e" % mean_dir[2]
        else:
            mean_dec_g, mean_inc_g = "", ""

        if len(carts_t) > 0:
            carts = scipy.array(carts_t)
            x_mean = scipy.mean(carts[:, 0])
            y_mean = scipy.mean(carts[:, 1])
            z_mean = scipy.mean(carts[:, 2])
            mean_dir = pmag.cart2dir([x_mean, y_mean, z_mean])
            mean_dec_t = "%.2f" % mean_dir[0]
            mean_inc_t = "%.2f" % mean_dir[1]
            mean_moment = "%10.3e" % mean_dir[2]
        else:
            mean_dec_t, mean_inc_t = "", ""

        meanrec = {}
        for key in list(duplicates[0].keys()):
            if key in ['dec_s', 'inc_s', 'dec_g', 'inc_g', 'dec_t', 'inc_t', 'moment']:
                continue
            else:
                meanrec[key] = duplicates[0][key]
        meanrec['dec_s'] = mean_dec_s
        meanrec['dec_g'] = mean_dec_g
        meanrec['dec_t'] = mean_dec_t
        meanrec['inc_s'] = mean_inc_s
        meanrec['inc_g'] = mean_inc_g
        meanrec['inc_t'] = mean_inc_t
        meanrec['moment'] = mean_moment
        return meanrec

    def get_upper_level_name(name, nc):
        '''
        get sample/site name from specimen/sample using naming convention
        '''
        if float(nc[0]) == 0:
            if float(nc[1]) != 0:
                number_of_char = int(nc[1])
                high_name = name[:number_of_char]
            else:
                high_name = name
        elif float(nc[0]) == 1:
            if float(nc[1]) != 0:
                number_of_char = int(nc[1])*-1
                high_name = name[:number_of_char]
            else:
                high_name = name
        elif float(nc[0]) == 2:
            d = str(nc[1])
            name_splitted = name.split(d)
            if len(name_splitted) == 1:
                high_name = name_splitted[0]
            else:
                high_name = d.join(name_splitted[:-1])
        else:
            high_name = name
        return high_name

    def merge_pmag_recs(old_recs):
        recs = {}
        recs = copy.deepcopy(old_recs)
        headers = []
        for rec in recs:
            for key in list(rec.keys()):
                if key not in headers:
                    headers.append(key)
        for rec in recs:
            for header in headers:
                if header not in list(rec.keys()):
                    rec[header] = ""
        return recs

    # --------------------------------------
    # start conversion from generic
    # --------------------------------------

    # format and validate variables

    input_dir_path, dir_path = pmag.fix_directories(input_dir_path, dir_path)
    labfield = float(labfield)
    labfield_phi = float(labfield_phi)
    labfield_theta = float(labfield_theta)

    if magfile:
        magfile = pmag.resolve_file_name(magfile, input_dir_path)
        try:
            input = open(magfile, 'r')
        except:
            print("bad mag file:", magfile)
            return False, "bad mag file"
    else:
        print("mag_file field is required option")
        return False, "mag_file field is required option"

    if not experiment:
        print("-E- Must provide experiment. Please provide experiment type of: Demag, PI, ATRM n (n of positions), CR (see below for format), NLT")
        return False, "Must provide experiment. Please provide experiment type of: Demag, PI, ATRM n (n of positions), CR (see help for format), NLT"

    if 'ATRM' in experiment:
        try:
            experiment, atrm_n_pos = experiment.split()
            atrm_n_pos = int(atrm_n_pos)
        except:
            experiment = 'ATRM'
            atrm_n_pos = 6
    if 'AARM' in experiment:
        try:
            experiment, aarm_n_pos = experiment.split()
            aarm_n_pos = int(aarm_n_pos)
        except:
            experiment = 'AARM'
            aarm_n_pos = 6

    if experiment == 'CR':
        if command_line:
            ind = sys.argv.index("CR")
            cooling_times = sys.argv[ind+1]
            cooling_times_list = cooling_times.split(',')
        noave = True
        # if not command line, cooling_times_list is already set

    # --------------------------------------
    # read data from generic file
    # --------------------------------------

    mag_data = read_generic_file(magfile, not noave)

    # --------------------------------------
    # for each specimen get the data, and translate it to MagIC format
    # --------------------------------------

    MeasRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    specimens_list = sorted(mag_data.keys())
    for specimen in specimens_list:
        measurement_running_number = 0
        this_specimen_treatments = []  # a list of all treatments
        MeasRecs_this_specimen = []
        LP_this_specimen = []  # a list of all lab protocols
        IZ, ZI = 0, 0  # counter for IZ and ZI steps

        for meas_line in mag_data[specimen]:

            # ------------------
            # trivial MeasRec data
            # ------------------

            MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}

            specimen = meas_line['specimen']
            sample = get_upper_level_name(specimen, sample_nc)
            site = get_upper_level_name(sample, site_nc)
            sample_method_codes = ""
            azimuth, dip, DipDir, Dip = "", "", "", ""

            MeasRec['citations'] = "This study"
            MeasRec["specimen"] = specimen
            MeasRec['analysts'] = user
            MeasRec["instrument_codes"] = ""
            MeasRec["quality"] = 'g'
            MeasRec["treat_step_num"] = "%i" % measurement_running_number
            MeasRec["magn_moment"] = '%10.3e' % (
                float(meas_line["moment"])*1e-3)  # in Am^2
            MeasRec["meas_temp"] = '273.'  # room temp in kelvin

            # ------------------
            #  decode treatments from treatment column in the generic file
            # ------------------

            treatment = []
            treatment_code = str(meas_line['treatment']).split(".")
            treatment.append(float(treatment_code[0]))
            if len(treatment_code) == 1:
                treatment.append(0)
            else:
                treatment.append(float(treatment_code[1]))

            # ------------------
            #  lab field direction
            # ------------------

            if experiment in ['PI', 'NLT', 'CR']:
                if float(treatment[1]) in [0., 3.]:  # zerofield step or tail check
                    MeasRec["treat_dc_field"] = "0"
                    MeasRec["treat_dc_field_phi"] = "0"
                    MeasRec["treat_dc_field_theta"] = "0"
                elif not labfield:
                    print(
                        "-W- WARNING: labfield (-dc) is a required argument for this experiment type")
                    return False, "labfield (-dc) is a required argument for this experiment type"
                else:
                    MeasRec["treat_dc_field"] = '%8.3e' % (float(labfield))
                    MeasRec["treat_dc_field_phi"] = "%.2f" % (
                        float(labfield_phi))
                    MeasRec["treat_dc_field_theta"] = "%.2f" % (
                        float(labfield_theta))
            else:
                MeasRec["treat_dc_field"] = ""
                MeasRec["treat_dc_field_phi"] = ""
                MeasRec["treat_dc_field_theta"] = ""

            # ------------------
            # treatment temperature/peak field
            # ------------------

            if experiment == 'Demag':
                if meas_line['treatment_type'] == 'A':
                    MeasRec['treat_temp'] = "273."
                    MeasRec["treat_ac_field"] = "%.3e" % (treatment[0]*1e-3)
                elif meas_line['treatment_type'] == 'N':
                    MeasRec['treat_temp'] = "273."
                    MeasRec["treat_ac_field"] = ""
                else:
                    MeasRec['treat_temp'] = "%.2f" % (treatment[0]+273.)
                    MeasRec["treat_ac_field"] = ""
            else:
                MeasRec['treat_temp'] = "%.2f" % (treatment[0]+273.)
                MeasRec["treat_ac_field"] = ""

            # ---------------------
            # Lab treatment
            # Lab protocol
            # ---------------------

            # ---------------------
            # Lab treatment and lab protocoal for NRM:
            # ---------------------

            if float(meas_line['treatment']) == 0:
                LT = "LT-NO"
                LP = ""  # will be filled later after finishing reading all measurements line

            # ---------------------
            # Lab treatment and lab protocoal for paleointensity experiment
            # ---------------------

            elif experiment == 'PI':
                LP = "LP-PI-TRM"
                if treatment[1] == 0:
                    LT = "LT-T-Z"
                elif treatment[1] == 1 or treatment[1] == 10:  # infield
                    LT = "LT-T-I"
                elif treatment[1] == 2 or treatment[1] == 20:  # pTRM check
                    LT = "LT-PTRM-I"
                    LP = LP+":"+"LP-PI-ALT-PTRM"
                elif treatment[1] == 3 or treatment[1] == 30:  # Tail check
                    LT = "LT-PTRM-MD"
                    LP = LP+":"+"LP-PI-BT-MD"
                elif treatment[1] == 4 or treatment[1] == 40:  # Additivity check
                    LT = "LT-PTRM-AC"
                    LP = LP+":"+"LP-PI-BT-MD"
                else:
                    print("-E- unknown measurement code specimen %s treatmemt %s" %
                          (meas_line['specimen'], meas_line['treatment']))
                    MeasRec = {}
                    continue
                # save all treatment in a list
                # we will use this later to distinguidh between ZI / IZ / and IZZI

                this_specimen_treatments.append(float(meas_line['treatment']))
                if LT == "LT-T-Z":
                    if float(treatment[0]+0.1) in this_specimen_treatments:
                        LP = LP+":"+"LP-PI-IZ"
                if LT == "LT-T-I":
                    if float(treatment[0]+0.0) in this_specimen_treatments:
                        LP = LP+":"+"LP-PI-ZI"
            # ---------------------
            # Lab treatment and lab protocoal for demag experiment
            # ---------------------

            elif "Demag" in experiment:
                if meas_line['treatment_type'] == 'A':
                    LT = "LT-AF-Z"
                    LP = "LP-DIR-AF"
                else:
                    LT = "LT-T-Z"
                    LP = "LP-DIR-T"

            # ---------------------
            # Lab treatment and lab protocoal for ATRM experiment
            # ---------------------

            elif experiment in ['ATRM', 'AARM']:

                if experiment == 'ATRM':
                    LP = "LP-AN-TRM"
                    n_pos = atrm_n_pos
                    if n_pos != 6:
                        print(
                            "the program does not support ATRM in %i position." % n_pos)
                        continue

                if experiment == 'AARM':
                    LP = "LP-AN-ARM"
                    n_pos = aarm_n_pos
                    if n_pos != 6:
                        print(
                            "the program does not support AARM in %i position." % n_pos)
                        continue

                if treatment[1] == 0:
                    if experiment == 'ATRM':
                        LT = "LT-T-Z"
                        MeasRec['treat_temp'] = "%.2f" % (treatment[0]+273.)
                        MeasRec["treat_ac_field"] = ""

                    else:
                        LT = "LT-AF-Z"
                        MeasRec['treat_temp'] = "273."
                        MeasRec["treat_ac_field"] = "%.3e" % (
                            treatment[0]*1e-3)
                    MeasRec["treat_dc_field"] = '0'
                    MeasRec["treat_dc_field_phi"] = '0'
                    MeasRec["treat_dc_field_theta"] = '0'
                else:
                    if experiment == 'ATRM':
                        # alteration check as final measurement
                        if float(treatment[1]) == 70 or float(treatment[1]) == 7:
                            LT = "LT-PTRM-I"
                        else:
                            LT = "LT-T-I"
                    else:
                        LT = "LT-AF-I"
                    MeasRec["treat_dc_field"] = '%8.3e' % (float(labfield))

                    # find the direction of the lab field in two ways:

                    # (1) using the treatment coding (XX.1=+x, XX.2=+y, XX.3=+z, XX.4=-x, XX.5=-y, XX.6=-z)
                    tdec = [0, 90, 0, 180, 270, 0, 0, 90, 0]
                    tinc = [0, 0, 90, 0, 0, -90, 0, 0, 90]
                    if treatment[1] < 10:
                        ipos_code = int(treatment[1]) - 1
                    else:
                        ipos_code = int(treatment[1] / 10) - 1

                    # (2) using the magnetization
                    if meas_line["dec_s"] != "":
                        DEC = float(meas_line["dec_s"])
                        INC = float(meas_line["inc_s"])
                    elif meas_line["dec_g"] != "":
                        DEC = float(meas_line["dec_g"])
                        INC = float(meas_line["inc_g"])
                    elif meas_line["dec_t"] != "":
                        DEC = float(meas_line["dec_t"])
                        INC = float(meas_line["inc_t"])
                    if DEC < 0 and DEC > -359:
                        DEC = 360.+DEC

                    if INC < 45 and INC > -45:
                        if DEC > 315 or DEC < 45:
                            ipos_guess = 0
                        if DEC > 45 and DEC < 135:
                            ipos_guess = 1
                        if DEC > 135 and DEC < 225:
                            ipos_guess = 3
                        if DEC > 225 and DEC < 315:
                            ipos_guess = 4
                    else:
                        if INC > 45:
                            ipos_guess = 2
                        if INC < -45:
                            ipos_guess = 5
                    # prefer the guess over the code
                    ipos = ipos_guess
                    # check it
                    if treatment[1] != 7 and treatment[1] != 70:
                        if ipos_guess != ipos_code:
                            print("-W- WARNING: check specimen %s step %s, anistropy measurements, coding does not match the direction of the lab field" % (
                                specimen, meas_line['treatment']))
                    MeasRec["treat_dc_field_phi"] = '%7.1f' % (tdec[ipos])
                    MeasRec["treat_dc_field_theta"] = '%7.1f' % (tinc[ipos])

            # ---------------------
            # Lab treatment and lab protocoal for cooling rate experiment
            # ---------------------

            elif experiment == "CR":

                cooling_times_list
                LP = "LP-CR-TRM"
                MeasRec["treat_temp"] = '%8.3e' % (
                    float(treatment[0])+273.)  # temp in kelvin

                if treatment[1] == 0:
                    LT = "LT-T-Z"
                    MeasRec["treat_dc_field"] = "0"
                    MeasRec["treat_dc_field_phi"] = '0'
                    MeasRec["treat_dc_field_theta"] = '0'
                else:
                    if treatment[1] == 7:  # alteration check as final measurement
                        LT = "LT-PTRM-I"
                    else:
                        LT = "LT-T-I"
                    MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                    MeasRec["treat_dc_field_phi"] = '%7.1f' % (
                        labfield_phi)  # labfield phi
                    MeasRec["treat_dc_field_theta"] = '%7.1f' % (
                        labfield_theta)  # labfield theta

                    indx = int(treatment[1])-1
                    # alteration check matjed as 0.7 in the measurement file
                    if indx == 6:
                        cooling_time = cooling_times_list[-1]
                    else:
                        cooling_time = cooling_times_list[indx]
                    MeasRec["measurement_description"] = "cooling_rate" + \
                        ":"+cooling_time+":"+"K/min"

            # ---------------------
            # Lab treatment and lab protocoal for NLT experiment
            # ---------------------

            elif 'NLT' in experiment:
                print(
                    "Do not support yet NLT rate experiment file. Contact rshaar@ucsd.edu")

            # ---------------------
            # method_codes for this measurement only
            # LP will be fixed after all measurement lines are read
            # ---------------------

            MeasRec["method_codes"] = LT+":"+LP

            # --------------------
            # deal with specimen orientation and different coordinate system
            # --------------------

            found_s, found_geo, found_tilt = False, False, False
            if "dec_s" in list(meas_line.keys()) and "inc_s" in list(meas_line.keys()):
                if meas_line["dec_s"] != "" and meas_line["inc_s"] != "":
                    found_s = True
                MeasRec["dir_dec"] = meas_line["dec_s"]
                MeasRec["dir_inc"] = meas_line["inc_s"]
            if "dec_g" in list(meas_line.keys()) and "inc_g" in list(meas_line.keys()):
                if meas_line["dec_g"] != "" and meas_line["inc_g"] != "":
                    found_geo = True
            if "dec_t" in list(meas_line.keys()) and "inc_t" in list(meas_line.keys()):
                if meas_line["dec_t"] != "" and meas_line["inc_t"] != "":
                    found_tilt = True

            # -----------------------------
            # specimen coordinates: no
            # geographic coordinates: yes
            # -----------------------------

            if found_geo and not found_s:
                MeasRec["dir_dec"] = meas_line["dec_g"]
                MeasRec["dir_inc"] = meas_line["inc_g"]
                azimuth = "0"
                dip = "0"

            # -----------------------------
            # specimen coordinates: no
            # geographic coordinates: no
            # -----------------------------
            if not found_geo and not found_s:
                print("-E- ERROR: sample %s does not have dec_s/inc_s or dec_g/inc_g. Ignore specimen %s " %
                      (sample, specimen))
                break

            # -----------------------------
            # specimen coordinates: yes
            # geographic coordinates: yes
            #
            # commant: Ron, this need to be tested !!
            # -----------------------------
            if found_geo and found_s:
                cdec, cinc = float(meas_line["dec_s"]), float(
                    meas_line["inc_s"])
                gdec, ginc = float(meas_line["dec_g"]), float(
                    meas_line["inc_g"])
                az, pl = pmag.get_azpl(cdec, cinc, gdec, ginc)
                azimuth = "%.1f" % az
                dip = "%.1f" % pl

            # -----------------------------
            # specimen coordinates: yes
            # geographic coordinates: no
            # -----------------------------
            if not found_geo and found_s and "Demag" in experiment:
                print("-W- WARNING: missing dip or azimuth for sample %s" % sample)

            # -----------------------------
            # tilt-corrected coordinates: yes
            # geographic coordinates: no
            # -----------------------------
            if found_tilt and not found_geo:
                print(
                    "-E- ERROR: missing geographic data for sample %s. Ignoring tilt-corrected data " % sample)

            # -----------------------------
            # tilt-corrected coordinates: yes
            # geographic coordinates: yes
            # -----------------------------
            if found_tilt and found_geo:
                dec_geo, inc_geo = float(
                    meas_line["dec_g"]), float(meas_line["inc_g"])
                dec_tilt, inc_tilt = float(
                    meas_line["dec_t"]), float(meas_line["inc_t"])
                if dec_geo == dec_tilt and inc_geo == inc_tilt:
                    DipDir, Dip = 0., 0.
                else:
                    DipDir, Dip = pmag.get_tilt(
                        dec_geo, inc_geo, dec_tilt, inc_tilt)

            # -----------------------------
            # samples method codes
            # geographic coordinates: no
            # -----------------------------
            if found_tilt or found_geo:
                sample_method_codes = "SO-NO"

            if specimen != "" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
                SpecRec['specimen'] = specimen
                SpecRec['sample'] = sample
                SpecRec['citations'] = "This study"
                SpecRecs.append(SpecRec)
            if sample != "" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
                SampRec['sample'] = sample
                SampRec['site'] = site
                SampRec['citations'] = "This study"
                SampRec['azimuth'] = azimuth
                SampRec['dip'] = dip
                SampRec['bed_dip_direction'] = DipDir
                SampRec['bed_dip'] = Dip
                SampRec['method_codes'] = sample_method_codes
                SampRecs.append(SampRec)
            if site != "" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
                SiteRec['site'] = site
                SiteRec['location'] = location
                SiteRec['citations'] = "This study"
                SiteRec['lat'] = lat
                SiteRec['lon'] = lon
                SiteRecs.append(SiteRec)
            if location != "" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
                LocRec['location'] = location
                LocRec['citations'] = "This study"
                LocRec['lat_n'] = lat
                LocRec['lon_e'] = lon
                LocRec['lat_s'] = lat
                LocRec['lon_w'] = lon
                LocRecs.append(LocRec)

            MeasRecs_this_specimen.append(MeasRec)
            measurement_running_number += 1
            # -------

        # -------
        # after reading all the measurements lines for this specimen
        # 1) add experiments
        # 2) fix method_codes with the correct lab protocol
        # -------
        LP_this_specimen = []
        for MeasRec in MeasRecs_this_specimen:
            method_codes = MeasRec["method_codes"].split(":")
            for code in method_codes:
                if "LP" in code and code not in LP_this_specimen:
                    LP_this_specimen.append(code)
        # check IZ/ZI/IZZI
        if "LP-PI-ZI" in LP_this_specimen and "LP-PI-IZ" in LP_this_specimen:
            LP_this_specimen.remove("LP-PI-ZI")
            LP_this_specimen.remove("LP-PI-IZ")
            LP_this_specimen.append("LP-PI-BT-IZZI")

        # add the right LP codes and fix experiment name
        for MeasRec in MeasRecs_this_specimen:
            # MeasRec["experiment"]=MeasRec["specimen"]+":"+":".join(LP_this_specimen)
            method_codes = MeasRec["method_codes"].split(":")
            LT = ""
            for code in method_codes:
                if code[:3] == "LT-":
                    LT = code
                    break
            MeasRec["method_codes"] = LT+":"+":".join(LP_this_specimen)
            MeasRec["method_codes"] = MeasRec["method_codes"].strip(":")
            MeasRecs.append(MeasRec)

    # --
    # write tables to file
    # --

    con = cb.Contribution(dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.tables['specimens'].write_magic_file(custom_name=spec_file,dir_path=dir_path)
    con.tables['samples'].write_magic_file(custom_name=samp_file,dir_path=dir_path)
    con.tables['sites'].write_magic_file(custom_name=site_file,dir_path=dir_path)
    con.tables['locations'].write_magic_file(custom_name=loc_file,dir_path=dir_path)
    con.tables['measurements'].write_magic_file(custom_name=meas_file,dir_path=dir_path)

    return True, meas_file


### HUJI_magic conversion

def huji(magfile="", dir_path=".", input_dir_path="", datafile="", codelist="",
         meas_file="measurements.txt", spec_file="specimens.txt",
         samp_file="samples.txt", site_file="sites.txt", loc_file="locations.txt",
         user="", specnum=0, samp_con="1", labfield=0, phi=0, theta=0,
         location="", CR_cooling_times=None, noave=False):
    """
    Convert HUJI format file to MagIC file(s)

    Parameters
    ----------
    magfile : str
       input file name
    dir_path : str
        working directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    datafile : str
       HUJI datafile with sample orientations, default ""
    codelist : str
        colon-delimited protocols, include all that apply
        see info below
    meas_file : str
        output measurement file name, default "measurements.txt"
    spec_file : str
        output specimen file name, default "specimens.txt"
    samp_file: str
        output sample file name, default "samples.txt"
    site_file : str
        output site file name, default "sites.txt"
    loc_file : str
        output location file name, default "locations.txt"
    user : str
        user name, default ""
    specnum : int
        number of characters to designate a specimen, default 0
    samp_con : str
        sample/site naming convention, default '1', see info below
    labfield : float
        dc lab field (in micro tesla)
    labfield_phi : float
        declination 0-360
    labfield_theta : float
        inclination -90 - 90
    location : str
        location name, default "unknown"
    CR_cooling_times : list
        default None
        cooling times in [K/minutes] separated by comma,
        ordered at the same order as XXX.10,XXX.20 ...XX.70
    noave : bool
       do not average duplicate measurements, default False (so by default, DO average)

    Info
    --------
    Code list:
        AF:  af demag
        T: thermal including thellier but not trm acquisition
        N: NRM only
        TRM: trm acquisition
        ANI: anisotropy experiment
        CR: cooling rate experiment.
            The treatment coding of the measurement file should be: XXX.00,XXX.10, XXX.20 ...XX.70 etc. (XXX.00 is optional)
            where XXX in the temperature and .10,.20... are running numbers of the cooling rates steps.
            XXX.00 is optional zerofield baseline. XXX.70 is alteration check.
            syntax in sio_magic is: -LP CR xxx,yyy,zzz,.....xx
            where xx, yyy,zzz...xxx  are cooling time in [K/minutes], separated by comma, ordered at the same order as XXX.10,XXX.20 ...XX.70
            if you use a zerofield step then no need to specify the cooling rate for the zerofield

    Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY


    """

    # format and validate variables
    specnum = int(specnum)
    labfield = float(labfield) * 1e-6
    phi = int(theta)
    theta = int(theta)
    input_dir_path, dir_path = pmag.fix_directories(input_dir_path, dir_path)
    if magfile:
        try:
            fname = pmag.resolve_file_name(magfile, input_dir_path)
            infile = open(fname, 'r')
        except IOError as ex:
            print(ex)
            print("bad mag file name")
            return False, "bad mag file name"
    else:
        print("mag_file field is a required option")
        return False, "mag_file field is a required option"

    if specnum != 0:
        specnum = -specnum
    if "4" in samp_con:
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = int(samp_con.split("-")[1])
            samp_con = "4"
    if "7" in samp_con:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = int(samp_con.split("-")[1])
            samp_con = "7"
    else:
        Z = 1

    if codelist:
        codes = codelist.split(':')
    else:
        print(
            "-E- Must select experiment type (codelist/-LP, options are: [AF, T, ANI, TRM, CR])")
        return False, "Must select experiment type (codelist/-LP, options are: [AF, T, ANI, TRM, CR])"
    if "AF" in codes:
        demag = 'AF'
        LPcode = "LP-DIR-AF"
    if "T" in codes:
        demag = "T"
        if not labfield:
            LPcode = "LP-DIR-T"
        if labfield:
            LPcode = "LP-PI-TRM"
        if "ANI" in codes:
            if not labfield:
                print("missing lab field option")
                return False, "missing lab field option"
            LPcode = "LP-AN-TRM"

    if "TRM" in codes:
        demag = "T"
        LPcode = "LP-TRM"
        # trm=1

    if "CR" in codes:
        demag = "T"
        # dc should be in the code
        if not labfield:
            print("missing lab field option")
            return False, "missing lab field option"

        LPcode = "LP-CR-TRM"  # TRM in different cooling rates
        if command_line:
            ind = sys.argv.index("-LP")
            CR_cooling_times = sys.argv[ind+2].split(",")

    version_num = pmag.get_version()

    # --------------------------------------
    # Read the file
    # Assumption:
    # 1. different lab protocolsa are in different files
    # 2. measurements are in the correct order
    # --------------------------------------

    Data = {}
    line_no = 0
    for line in infile.readlines():
        line_no += 1
        this_line_data = {}
        line_no += 1
        instcode = ""
        if len(line) < 2:
            continue
        if line[0] == "#":  # HUJI way of marking bad data points
            continue

        rec = line.strip('\n').split()
        specimen = rec[0]
        date = rec[2].split("/")
        hour = rec[3].split(":")
        treatment_type = rec[4]
        treatment = rec[5].split(".")
        dec_core = rec[6]
        inc_core = rec[7]
        moment_emu = float(rec[-1])

        if specimen not in list(Data.keys()):
            Data[specimen] = []

        # check duplicate treatments:
        # if yes, delete the first and use the second

        if len(Data[specimen]) > 0:
            if treatment == Data[specimen][-1]['treatment']:
                del(Data[specimen][-1])
                print("-W- Identical treatments in file %s magfile line %i: specimen %s, treatment %s ignoring the first. " %
                      (magfile, line_no, specimen, ".".join(treatment)))

        this_line_data = {}
        this_line_data['specimen'] = specimen
        this_line_data['date'] = date
        this_line_data['hour'] = hour
        this_line_data['treatment_type'] = treatment_type
        this_line_data['treatment'] = treatment
        this_line_data['dec_core'] = dec_core
        this_line_data['inc_core'] = inc_core
        this_line_data['moment_emu'] = moment_emu
        this_line_data['azimuth'] = ''
        this_line_data['dip'] = ''
        this_line_data['bed_dip_direction'] = ''
        this_line_data['bed_dip'] = ''
        this_line_data['lat'] = ''
        this_line_data['lon'] = ''
        this_line_data['volume'] = ''
        Data[specimen].append(this_line_data)
    infile.close()
    print("-I- done reading file %s" % magfile)

    if datafile:
        dinfile = open(datafile)
        for line in dinfile.readlines():
            data = line.split()
            if len(data) < 8 or data[0] == '':
                continue
            elif data[0] in list(Data.keys()):
                for i in range(len(Data[data[0]])):
                    Data[data[0]][i]['azimuth'] = data[1]
                    Data[data[0]][i]['dip'] = data[2]
                    try:
                        Data[data[0]][i]['bed_dip_direction'] = float(
                            data[3])+90
                    except ValueError:
                        Data[data[0]][i]['bed_dip_direction'] = ''
                    Data[data[0]][i]['bed_dip'] = data[4]
                    Data[data[0]][i]['lat'] = data[5]
                    Data[data[0]][i]['lon'] = data[6]
                    Data[data[0]][i]['volume'] = data[7]
            else:
                print(
                    "no specimen %s found in magnetometer data file when reading specimen orientation data file, or data file record for specimen too short" % data[0])
        dinfile.close()

    # --------------------------------------
    # Convert to MagIC
    # --------------------------------------

    specimens_list = list(Data.keys())
    specimens_list.sort()

    MeasRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    for specimen in specimens_list:
        for i in range(len(Data[specimen])):
            this_line_data = Data[specimen][i]
            methcode = ""
            MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}
            specimen = this_line_data['specimen']
            if specnum != 0:
                sample = this_line_data['specimen'][:specnum]
            else:
                sample = this_line_data['specimen']
            site = pmag.parse_site(sample, samp_con, Z)
            if not location:
                location = site
            if specimen != "" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
                SpecRec['specimen'] = specimen
                SpecRec['sample'] = sample
                SpecRecs.append(SpecRec)
            if sample != "" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
                SampRec['sample'] = sample
                SampRec['site'] = site
                SampRec['azimuth'] = this_line_data['azimuth']
                SampRec['dip'] = this_line_data['dip']
                SampRec['bed_dip_direction'] = this_line_data['bed_dip_direction']
                SampRec['bed_dip'] = this_line_data['bed_dip']
                SampRecs.append(SampRec)
            if site != "" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
                SiteRec['site'] = site
                SiteRec['location'] = location
                SiteRec['lat'] = this_line_data['lat']
                SiteRec['lon'] = this_line_data['lon']
                SiteRecs.append(SiteRec)
            if location != "" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
                LocRec['location'] = location
                LocRec['lat_n'] = this_line_data['lat']
                LocRec['lon_e'] = this_line_data['lon']
                LocRec['lat_s'] = this_line_data['lat']
                LocRec['lon_w'] = this_line_data['lon']
                LocRecs.append(LocRec)

            MeasRec['specimen'] = specimen
            MeasRec["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
            MeasRec["magn_moment"] = '%10.3e' % (
                float(this_line_data['moment_emu'])*1e-3)  # moment in Am^2 (from emu)
            MeasRec["dir_dec"] = this_line_data['dec_core']
            MeasRec["dir_inc"] = this_line_data['inc_core']

            date = this_line_data['date']
            hour = this_line_data['hour']
            if len(date[2]) < 4 and float(date[2]) >= 70:
                yyyy = "19"+date[2]
            elif len(date[2]) < 4 and float(date[2]) < 70:
                yyyy = "20"+date[2]
            else:
                yyyy = date[2]
            if len(date[0]) == 1:
                date[0] = "0"+date[0]
            if len(date[1]) == 1:
                date[1] = "0"+date[1]
            dt = ":".join([date[0], date[1], yyyy, hour[0], hour[1], "0"])
            local = pytz.timezone("America/New_York")
            naive = datetime.datetime.strptime(dt, "%m:%d:%Y:%H:%M:%S")
            local_dt = local.localize(naive, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            timestamp = utc_dt.strftime("%Y-%m-%dT%H:%M:%S")+"Z"

            MeasRec['analysts'] = user
            MeasRec["citations"] = "This study"
            MeasRec["instrument_codes"] = "HUJI-2G"
            MeasRec["quality"] = "g"
            MeasRec["meas_n_orient"] = "1"
            MeasRec["standard"] = "u"
            MeasRec["description"] = ""

            # ----------------------------------------
            # AF demag
            # do not support AARM yet
            # ----------------------------------------

            if demag == "AF":
                treatment_type = this_line_data['treatment_type']
                # demag in zero field
                if LPcode != "LP-AN-ARM":
                    MeasRec["treat_ac_field"] = '%8.3e' % (
                        float(this_line_data['treatment'][0])*1e-3)  # peak field in tesla
                    MeasRec["treat_dc_field"] = '0'
                    MeasRec["treat_dc_field_phi"] = '0'
                    MeasRec["treat_dc_field_theta"] = '0'
                    if treatment_type == "N":
                        methcode = "LP-DIR-AF:LT-NO"
                    elif treatment_type == "A":
                        methcode = "LP-DIR-AF:LT-AF-Z"
                    else:
                        print(
                            "ERROR in treatment field line %i... exiting until you fix the problem" % line_no)
                        print(this_line_data)
                        return False, "ERROR in treatment field line %i... exiting until you fix the problem" % line_no
                # AARM experiment
                else:
                    print("Don't support AARM in HUJI format yet. sorry... ")
                MeasRec["method_codes"] = methcode
                MeasRec["experiment"] = specimen + ":" + LPcode
                MeasRec["treat_step_num"] = "%i" % i
                MeasRec["description"] = ""

                MeasRecs.append(MeasRec)

            # ----------------------------------------
            # Thermal:
            # Thellier experiment: "IZ", "ZI", "IZZI", pTRM checks
            # Thermal demag
            # Thermal cooling rate experiment
            # Thermal NLT
            # ----------------------------------------

            if demag == "T":

                treatment = this_line_data['treatment']
                treatment_type = this_line_data['treatment_type']

                # ----------------------------------------
                # Thellier experimet
                # ----------------------------------------

                if LPcode == "LP-PI-TRM":  # Thelllier experiment
                    MeasRec["experiment"] = specimen + ":" + LPcode
                    methcode = LPcode
                    if treatment_type == "N" or ((treatment[1] == '0' or treatment[1] == '00') and float(treatment[0]) == 0):
                        LT_code = "LT-NO"
                        MeasRec["treat_dc_field_phi"] = '0'
                        MeasRec["treat_dc_field_theta"] = '0'
                        MeasRec["treat_dc_field"] = '0'
                        MeasRec["treat_temp"] = '273.'

                    elif treatment[1] == '0' or treatment[1] == '00':
                        LT_code = "LT-T-Z"
                        MeasRec["treat_dc_field_phi"] = '0'
                        MeasRec["treat_dc_field_theta"] = '0'
                        MeasRec["treat_dc_field"] = '%8.3e' % (0)
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatment[0])+273.)  # temp in kelvin

                        # check if this is ZI or IZ:
                        #  check if the same temperature already measured:
                        methcode = "LP-PI-TRM:LP-PI-TRM-ZI"
                        for j in range(0, i):
                            if Data[specimen][j]['treatment'][0] == treatment[0]:
                                if Data[specimen][j]['treatment'][1] == '1' or Data[specimen][j]['treatment'][1] == '10':
                                    methcode = "LP-PI-TRM:LP-PI-TRM-IZ"
                                else:
                                    methcode = "LP-PI-TRM:LP-PI-TRM-ZI"

                    elif treatment[1] == '1' or treatment[1] == '10':
                        LT_code = "LT-T-I"
                        # labfield in tesla (convert from microT)
                        MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                        MeasRec["treat_dc_field_phi"] = '%7.1f' % (
                            phi)  # labfield phi
                        MeasRec["treat_dc_field_theta"] = '%7.1f' % (
                            theta)  # labfield theta
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatment[0])+273.)  # temp in kelvin

                        # check if this is ZI or IZ:
                        #  check if the same temperature already measured:
                        methcode = "LP-PI-TRM:LP-PI-TRM-IZ"
                        for j in range(0, i):
                            if Data[specimen][j]['treatment'][0] == treatment[0]:
                                if Data[specimen][j]['treatment'][1] == '0' or Data[specimen][j]['treatment'][1] == '00':
                                    methcode = "LP-PI-TRM:LP-PI-TRM-ZI"
                                else:
                                    methcode = "LP-PI-TRM:LP-PI-TRM-IZ"
                    elif treatment[1] == '2' or treatment[1] == '20':
                        LT_code = "LT-PTRM-I"
                        # labfield in tesla (convert from microT)
                        MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                        MeasRec["treat_dc_field_phi"] = '%7.1f' % (
                            phi)  # labfield phi
                        MeasRec["treat_dc_field_theta"] = '%7.1f' % (
                            theta)  # labfield theta
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatment[0])+273.)  # temp in kelvin
                        methcode = "LP-PI-TRM:LP-PI-TRM-IZ"

                    else:
                        print(
                            "ERROR in treatment field line %i... exiting until you fix the problem" % line_no)
                        return False, "ERROR in treatment field line %i... exiting until you fix the problem" % line_no
                    MeasRec["method_codes"] = LT_code+":"+methcode
                    MeasRec["treat_step_num"] = "%i" % i
                    MeasRec["description"] = ""
                    MeasRecs.append(MeasRec)

                # ----------------------------------------
                # demag experimet
                # ----------------------------------------

                if LPcode == "LP-DIR-T":
                    MeasRec["experiment"] = specimen + ":" + LPcode
                    methcode = LPcode
                    if treatment_type == "N":
                        LT_code = "LT-NO"
                    else:
                        LT_code = "LT-T-Z"
                        methcode = LPcode+":"+"LT-T-Z"
                    MeasRec["treat_dc_field_phi"] = '0'
                    MeasRec["treat_dc_field_theta"] = '0'
                    MeasRec["treat_dc_field"] = '%8.3e' % (0)
                    MeasRec["treat_temp"] = '%8.3e' % (
                        float(treatment[0])+273.)  # temp in kelvin
                    MeasRec["method_codes"] = LT_code+":"+methcode
                    MeasRec["treat_step_num"] = "%i" % i
                    MeasRec["description"] = ""
                    MeasRecs.append(MeasRec)
                    # continue

                # ----------------------------------------
                # ATRM measurements
                # The direction of the magnetization is used to determine the
                # direction of the lab field.
                # ----------------------------------------

                if LPcode == "LP-AN-TRM":
                    MeasRec["experiment"] = specimen + ":" + LPcode
                    methcode = LPcode

                    if float(treatment[1]) == 0:
                        MeasRec["method_codes"] = "LP-AN-TRM:LT-T-Z"
                        MeasRec["treat_dc_field_phi"] = '0'
                        MeasRec["treat_dc_field_theta"] = '0'
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatment[0])+273.)  # temp in kelvin
                        MeasRec["treat_dc_field"] = '0'
                    else:
                        if float(treatment[1]) == 7:
                            # alteration check
                            methcode = "LP-AN-TRM:LT-PTRM-I"
                            MeasRec["treat_step_num"] = '7'  # -z
                        else:
                            MeasRec["method_codes"] = "LP-AN-TRM:LT-T-I"
                            inc = float(MeasRec["dir_inc"])
                            dec = float(MeasRec["dir_dec"])
                            if abs(inc) < 45 and (dec < 45 or dec > 315):  # +x
                                tdec, tinc = 0, 0
                                MeasRec["treat_step_num"] = '1'
                            if abs(inc) < 45 and (dec < 135 and dec > 45):
                                tdec, tinc = 90, 0
                                MeasRec["treat_step_num"] = '2'  # +y
                            if inc > 45:
                                tdec, tinc = 0, 90
                                MeasRec["treat_step_num"] = '3'  # +z
                            if abs(inc) < 45 and (dec < 225 and dec > 135):
                                tdec, tinc = 180, 0
                                MeasRec["treat_step_num"] = '4'  # -x
                            if abs(inc) < 45 and (dec < 315 and dec > 225):
                                tdec, tinc = 270, 0
                                MeasRec["treat_step_num"] = '5'  # -y
                            if inc < -45:
                                tdec, tinc = 0, -90
                                MeasRec["treat_step_num"] = '6'  # -z

                        MeasRec["treat_dc_field_phi"] = '%7.1f' % (tdec)
                        MeasRec["treat_dc_field_theta"] = '%7.1f' % (tinc)
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatment[0])+273.)  # temp in kelvin
                        MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                    MeasRec["description"] = ""
                    MeasRecs.append(MeasRec)
                    # continue

                # ----------------------------------------
                # NLT measurements
                # or TRM acquisistion experiment
                # ----------------------------------------

                if LPcode == "LP-TRM":
                    MeasRec["experiment"] = specimen + ":" + LPcode
                    MeasRec["method_codes"] = "LP-TRM:LT-T-I"
                    if float(treatment[1]) == 0:
                        labfield = 0
                    else:
                        labfield = float(float(treatment[1]))*1e-6
                    MeasRec["treat_temp"] = '%8.3e' % (
                        float(treatment[0])+273.)  # temp in kelvin
                    # labfield in tesla (convert from microT)
                    MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                    MeasRec["treat_dc_field_phi"] = '%7.1f' % (
                        phi)  # labfield phi
                    MeasRec["treat_dc_field_theta"] = '%7.1f' % (
                        theta)  # labfield theta
                    MeasRec["treat_step_num"] = "%i" % i
                    MeasRec["description"] = ""
                    MeasRecs.append(MeasRec)
                    # continue

                # ----------------------------------------
                # Cooling rate experiments
                # ----------------------------------------

                if LPcode == "LP-CR-TRM":
                    index = int(treatment[1][0])
                    # print index,"index"
                    # print CR_cooling_times,"CR_cooling_times"
                    # print CR_cooling_times[index-1]
                    # print CR_cooling_times[0:index-1]
                    if index == 7 or index == 70:  # alteration check as final measurement
                        meas_type = "LT-PTRM-I:LP-CR-TRM"
                        CR_cooling_time = CR_cooling_times[-1]
                    else:
                        meas_type = "LT-T-I:LP-CR-TRM"
                        CR_cooling_time = CR_cooling_times[index-1]
                    MeasRec["method_codes"] = meas_type
                    MeasRec["experiment"] = specimen + ":" + LPcode
                    MeasRec["treat_temp"] = '%8.3e' % (
                        float(treatment[0])+273.)  # temp in kelvin
                    # labfield in tesla (convert from microT)
                    MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                    MeasRec["treat_dc_field_phi"] = '%7.1f' % (
                        phi)  # labfield phi
                    MeasRec["treat_dc_field_theta"] = '%7.1f' % (
                        theta)  # labfield theta
                    MeasRec["treat_step_num"] = "%i" % index
                    MeasRec["description"] = "cooling_rate" + \
                        ":"+CR_cooling_time+":"+"K/min"
                    #MeasRec["description"]="%.1f minutes per cooling time"%int(CR_cooling_time)
                    MeasRecs.append(MeasRec)
                    # continue

    con = cb.Contribution(dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.tables['specimens'].write_magic_file(custom_name=spec_file,dir_path=dir_path)
    con.tables['samples'].write_magic_file(custom_name=samp_file,dir_path=dir_path)
    con.tables['sites'].write_magic_file(custom_name=site_file,dir_path=dir_path)
    con.tables['locations'].write_magic_file(custom_name=loc_file,dir_path=dir_path)
    con.tables['measurements'].write_magic_file(custom_name=meas_file,dir_path=dir_path)

    return True, meas_file


### HUJI_sample_magic conversion

def huji_sample(orient_file, meths='FS-FD:SO-POM:SO-SUN', location_name='unknown',
                samp_con="1", ignore_dip=True, data_model_num=3,
                samp_file="samples.txt", site_file="sites.txt",
                dir_path=".", input_dir_path=""):
    """
    Convert HUJI sample file to MagIC file(s)

    Parameters
    ----------
    orient_file : str
        input file name
    meths : str
       colon-delimited sampling methods, default FS-FD:SO-POM:SO-SUN
       for more options, see info below
    location : str
        location name, default "unknown"
    samp_con : str
        sample/site naming convention, default '1', see info below
    ignore_dip : bool
        set sample az/dip to 0, default True
    data_model_num : int
        MagIC data model 2 or 3, default 3
    samp_file : str
        sample file name to output (default : samples.txt)
    site_file : str
        site file name to output (default : site.txt)
    dir_path : str
        output directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful, file name written)

    Info
    --------
    Sampling method codes:
        FS-FD field sampling done with a drill
        FS-H field sampling done with hand samples
        FS-LOC-GPS  field location done with GPS
        FS-LOC-MAP  field location done with map
        SO-POM   a Pomeroy orientation device was used
        SO-ASC   an ASC orientation device was used
        SO-MAG   orientation with magnetic compass

     Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY


    """

    try:
        samp_con, Z = samp_con.split("-")
    except ValueError:
        samp_con = samp_con
        Z = 1

    version_num = pmag.get_version()
    if data_model_num == 2:
        loc_col = "er_location_name"
        site_col = "er_site_name"
        samp_col = "er_sample_name"
        citation_col = "er_citation_names"
        class_col = "site_class"
        lithology_col = "site_lithology"
        definition_col = "site_definition"
        type_col = "site_type"
        sample_bed_dip_direction_col = "sample_bed_dip_direction"
        sample_bed_dip_col = "sample_bed_dip"
        site_bed_dip_direction_col = "site_bed_dip_direction"
        site_bed_dip_col = "site_bed_dip"
        sample_dip_col = "sample_dip"
        sample_az_col = "sample_azimuth"
        sample_lat_col = "sample_lat"
        sample_lon_col = "sample_lon"
        site_lat_col = "site_lat"
        site_lon_col = "site_lon"
        meth_col = "magic_method_codes"
        software_col = "magic_software_packages"
    else:
        loc_col = "location"
        site_col = "site"
        samp_col = "sample"
        citation_col = "citations"
        class_col = "class"
        lithology_col = "lithology"
        definition_col = "definition"
        type_col = "type"
        sample_bed_dip_direction_col = 'bed_dip_direction'
        sample_bed_dip_col = 'bed_dip'
        site_bed_dip_direction_col = 'bed_dip_direction'
        site_bed_dip_col = "bed_dip"
        sample_dip_col = "dip"
        sample_az_col = "azimuth"
        sample_lat_col = "lat"
        sample_lon_col = "lon"
        site_lat_col = "lat"
        site_lon_col = "lon"
        meth_col = "method_codes"
        software_col = "software_packages"

    input_dir_path, dir_path = pmag.fix_directories(input_dir_path, dir_path)
    samp_file = pmag.resolve_file_name(samp_file, dir_path)
    site_file = pmag.resolve_file_name(site_file, dir_path)
    orient_file = pmag.resolve_file_name(orient_file, input_dir_path)
    print("-I- reading in: {}".format(orient_file))
    #
    # read in file to convert
    #
    with open(orient_file, 'r') as azfile:
        AzDipDat = azfile.readlines()
    SampOut = []
    SiteOut = []
    for line in AzDipDat[1:]:
        orec = line.split()
        if len(orec) > 1:
            labaz, labdip = pmag.orient(float(orec[1]), float(orec[2]), '3')
            bed_dip_dir = (orec[3])
            bed_dip = (orec[4])
            SampRec = {}
            SiteRec = {}
            SampRec[loc_col] = location_name
            SampRec[citation_col] = "This study"
            SiteRec[loc_col] = location_name
            SiteRec[citation_col] = "This study"
            SiteRec[class_col] = ""
            SiteRec[lithology_col] = ""
            SiteRec[type_col] = ""
            SiteRec[definition_col] = "s"
    #
    # parse information common to all orientation methods
    #
            SampRec[samp_col] = orec[0]
            SampRec[sample_bed_dip_direction_col] = orec[3]
            SampRec[sample_bed_dip_col] = orec[4]
            SiteRec[site_bed_dip_direction_col] = orec[3]
            SiteRec[site_bed_dip_col] = orec[4]
            if not ignore_dip:
                SampRec[sample_dip_col] = '%7.1f' % (labdip)
                SampRec[sample_az_col] = '%7.1f' % (labaz)
            else:
                SampRec[sample_dip_col] = '0'
                SampRec[sample_az_col] = '0'
            SampRec[sample_lat_col] = orec[5]
            SampRec[sample_lon_col] = orec[6]
            SiteRec[site_lat_col] = orec[5]
            SiteRec[site_lon_col] = orec[6]
            SampRec[meth_col] = meths
            # parse out the site name
            site = pmag.parse_site(orec[0], samp_con, Z)
            SampRec[site_col] = site
            SampRec[software_col] = version_num
            SiteRec[site_col] = site
            SiteRec[software_col] = version_num
            SampOut.append(SampRec)
            SiteOut.append(SiteRec)
    if data_model_num == 2:
        pmag.magic_write(samp_file, SampOut, "er_samples")
        pmag.magic_write(site_file, SiteOut, "er_sites")
    else:
        pmag.magic_write(samp_file, SampOut, "samples")
        pmag.magic_write(site_file, SiteOut, "sites")

    print("Sample info saved in ", samp_file)
    print("Site info saved in ", site_file)
    return True, samp_file


### IODP_dscr_magic conversion
def iodp_dscr_lore(dscr_file,dscr_ex_file="", dir_path=".", input_dir_path="",volume=7,noave=False,
                   meas_file="measurements.txt", offline_meas_file="",spec_file="specimens.txt"):
    """
    Convert IODP discrete measurement files into MagIC file(s). This program
    assumes that you have created the specimens, samples, sites and location
    files using convert_2_magic.iodp_samples_csv from files downloaded from the LIMS online
    repository and that all samples are in that file.

    If there are offline treatments, you will also need the extended version of the SRM discrete
    download file from LORE.

    Parameters
    ----------
    dscr_file : str
        input csv file downloaded from LIMS online repository
    dscr_ex_file : str
        input extended csv file downloaded from LIMS online repository
    dir_path : str
        output directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    meas_file : str
        output measurement file name, default "measurements.txt"
    offline_meas_file : str
        output measurement file for offline measurements , default "". must be specified if dscr_ex_file supplied
    spec_file : str
        specimens file name created by, for example, convert_2_magic.iodp_samples_csv, default "specimens.txt"
        file should already be in dir_path
    volume : float
        volume in cm^3 assumed during measurement on SRM.  The so-called "Japanese" cubes have a volume of 7cc
    noave : Boolean
         if False, average replicate measurements

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful, meas_file name written)
    """
    # initialize defaults
    version_num = pmag.get_version()
    # format variables
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    # convert cc to m^3
    volume = float(volume) * 1e-6
    meas_reqd_columns=['specimen','measurement','experiment','sequence','quality','method_codes',\
                       'instrument_codes','citations',\
                       'treat_temp','treat_ac_field','treat_dc_field',\
                      'treat_dc_field_phi','treat_dc_field_theta','meas_temp',\
                      'dir_dec','dir_inc','magn_moment','magn_volume',\
                       'description','timestamp','software_packages',\
                       'external_database_ids','treat_step_num','meas_n_orient']
    dscr_file = pmag.resolve_file_name(dscr_file, input_dir_path)
    if dscr_ex_file:dscr_ex_file = pmag.resolve_file_name(dscr_ex_file, input_dir_path)
    spec_file = pmag.resolve_file_name(spec_file, dir_path)
    # just in case, check if the specimen file is in the input directory instead
    if not os.path.exists(spec_file):
        spec_file = pmag.resolve_file_name(os.path.split(spec_file)[1], input_dir_path)
    specimens_df=pd.read_csv(spec_file,sep='\t',header=1)
    if len(specimens_df)==0:
        print ('you must download and process the samples table from LORE prior to using this')
        print ('see convert_2_magic.iodp_samples_csv for help')
        return False, ""
    LORE_specimens=list(specimens_df.specimen.unique())
    in_df=pd.read_csv(dscr_file)
    in_df['offline_treatment']=""
    if dscr_ex_file:
        ex_df=pd.read_csv(dscr_ex_file)
        ex_df['Test No.']=ex_df['test test_number']
        ex_df['offline_treatment']=ex_df['comments']
        ex_df=ex_df[['Test No.','offline_treatment']]
        in_df=in_df.merge(ex_df,on='Test No.')
        in_df['offline_treatment']=in_df['offline_treatment_y']
        in_df['offline_treatment'].fillna("",inplace=True)
    in_df.drop_duplicates(inplace=True)
    if len(in_df)==0:
        print ('you must download a csv file from the LIMS database and place it in your input_dir_path')
        return False, ""
    in_df.sort_values(by='Test No.',inplace=True)
    in_df.reset_index(inplace=True)
    measurements_df=pd.DataFrame(columns=meas_reqd_columns)
    meas_out = os.path.join(output_dir_path, meas_file)
    if offline_meas_file:
        offline_meas_out = os.path.join(output_dir_path, offline_meas_file)
    if dscr_ex_file and not offline_meas_file:
        print ("You must specify an output file for the offline measurements with dscr_ex_file")
        return False, ""
    hole,srm_specimens=iodp_sample_names(in_df)
    for spec in list(srm_specimens.unique()):
        if spec not in LORE_specimens:
            print (' -W- ',spec, ' not found in specimens table ')
            print ( 'check your sample name or add to specimens table by hand\n')
    # set up defaults
    measurements_df['specimen']=srm_specimens
    measurements_df['comment']=in_df['Comments'] # temporary column
    measurements_df['offline_treatment']=in_df['offline_treatment']
    measurements_df['sequence']=in_df['Test No.']
    measurements_df['offline_list']=""
    measurements_df['quality']='g'
    measurements_df['citations']='This study'
    measurements_df['meas_temp']=273
    measurements_df['software_packages']=version_num
    measurements_df["treat_temp"] = '%8.3e' % (273)  # room temp in kelvin
    measurements_df["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
    measurements_df['meas_n_orient']=1 # at least one orientation
    measurements_df["treat_ac_field"] = '0'
    measurements_df["treat_dc_field"] = '0'
    measurements_df["treat_dc_field_phi"] = '0'
    measurements_df["treat_dc_field_theta"] = '0'
    measurements_df["treat_step_num"] = '1'
    measurements_df["standard"] = 'u'  # assume all data are "good"
    measurements_df["dir_csd"] = '0'  # assume all data are "good"
    measurements_df["method_codes"] = 'LT-NO' # assume all are NRMs
    measurements_df['instrument_codes']="IODP-SRM" # assume all measurements on shipboard 2G
    measurements_df['timestamp']=pd.to_datetime(\
                               in_df['Timestamp (UTC)']).dt.strftime("%Y-%m-%dT%H:%M:%S")+'Z'
    measurements_df['dir_dec']=in_df['Declination background & drift corrected (deg)'] # declination
    measurements_df['dir_inc']=in_df['Inclination background & drift corrected (deg)'] # inclination
    measurements_df['magn_volume']=in_df['Intensity background & drift corrected (A/m)'] # magnetization
    measurements_df['magn_moment']=measurements_df['magn_volume']*volume # moment in Am^2
    measurements_df['description']=in_df['Treatment Type'] # temporary column
    measurements_df['treat_ac_field']=in_df['Treatment Value']*1e-3 # assume all treatments are AF
    measurements_df.loc[measurements_df['description']=='IN-LINE AF DEMAG',\
                        'method_codes']='LT-AF-Z'
    measurements_df.loc[measurements_df['description']=='IN-LINE AF DEMAG',\
                        'instrument_codes']='IODP-SRM:IODP-SRM-AF'
    measurements_df['external_database_ids']='LORE['+in_df['Test No.'].astype('str')+']'
    measurements_df.fillna("",inplace=True)
    measurements_df.sort_values(by='sequence',inplace=True)
    if dscr_ex_file:
        meas_df=measurements_df[measurements_df.offline_treatment==""] # all the records with no offline treatments
        offline_df=pd.DataFrame(columns=meas_df.columns) # make a container for offline measurements
        arm_df=measurements_df[measurements_df['offline_treatment'].str.contains('ARM')]
        if len(arm_df)>0: # there are ARM treatment steps
           arm_df['offline_list']=arm_df['offline_treatment'].str.split(":")
           arm_list=arm_df.specimen.unique()
           for spc in arm_list: # get all the ARM treated specimens
               spc_df=arm_df[arm_df.specimen.str.match(spc)] # get all the measurements for this specimen
               seq_no=spc_df[spc_df.specimen.str.match(spc)].sequence.values[0] # get the sequence number of the ARM step
               end_seq_no=spc_df[spc_df.specimen.str.match(spc)].sequence.values[-1] # get the sequence number of the last ARM demag step
               arm_df.loc[arm_df.sequence==seq_no,'method_codes']='LT-AF-I:LP-ARM-AFD' # label the ARM record
               arm_df.loc[arm_df.sequence==seq_no,'experiment']=spc+'_LT-AF-I_LT-AF-Z_LP-ARM-AFD' # label the ARM record
               arm_df.loc[arm_df.sequence==seq_no,'treat_ac_field']=arm_df['offline_list'].str.get(1).astype('float')*1e-3 # AF peak field in mT converted to tesla
               arm_df.loc[arm_df.sequence==seq_no,'treat_dc_field']=arm_df['offline_list'].str.get(2).astype('float')*1e-3 # AF peak field in mT converted to tesla
               arm_df.loc[arm_df.sequence==seq_no,'instrument_codes']='IODP-SRM:IODP-DTECH'
               arm_df.loc[(arm_df.specimen.str.match(spc)) &
                          (arm_df.sequence>seq_no) &
                          (arm_df.sequence<=end_seq_no),'method_codes']= 'LT-AF-Z:LP-ARM-AFD'
               arm_df.loc[(arm_df.specimen.str.match(spc)) &
                          (arm_df.sequence>seq_no) &
                          (arm_df.sequence<=end_seq_no),'experiment']= spc+'LT-AF-I_LT-AF-Z_LP-ARM-AFD'
               arm_df.loc[(arm_df.specimen.str.match(spc)) &
                          (arm_df.sequence>seq_no) &
                          (arm_df.sequence<=end_seq_no),'instrument_codes']= 'IODP-SRM:IODP-SRM-AF'
           strings=[]
           for i in range(len(arm_df)):strings.append(str(i))
           arm_df['measurement']=arm_df['experiment']+strings
           arm_df['description']=arm_df['offline_treatment']
           offline_df=pd.concat([offline_df,arm_df])  # put the arm data into the offline dataframe
        irm_in_df=measurements_df[measurements_df['offline_treatment'].str.contains('IRM')]
        if len(irm_in_df)>0: # there are IRM treatment steps
           irm_in_df['offline_list']=irm_in_df['offline_treatment'].str.split(":")
           irm_list=irm_in_df.specimen.unique()
           irm_out_df=pd.DataFrame(columns=irm_in_df.columns) # make an output container
           for spc in irm_list: # get all the IRM treated specimens
               # first do IRM acquisition steps
               spc_df=irm_in_df[irm_in_df.specimen.str.match(spc)] # get all the measurements for this specimen
               spc_acq_df=spc_df[spc_df.treat_ac_field==0] # IRM acquisition step
               spc_acq_df['method_codes']='LT-IRM:LP-IRM' # label the IRM records
               spc_acq_df['experiment']=spc+'_LT-IRM_LP-IRM' # label the IRM experiment
               spc_acq_df['treat_dc_field']=spc_acq_df['offline_list'].str.get(1).astype('float')*1e-3 # IRM field in mT converted to tesla
               spc_acq_df['instrument_codes']='IODP-SRM:IODP-IM-10'
               # do the AF demag of the IRM
               sirm_seq_no=spc_acq_df[spc_acq_df.specimen.str.match(spc)].sequence.values[-1] # get the sequence number of the last IRM step
               spc_afd_df=spc_df[(spc_df.treat_ac_field!=0)] #
               spc_afd_df['method_codes']= 'LP-IRM:LP-IRM-AFD'
               spc_afd_df['experiment']= spc+'LP-IRM:LP-IRM-AFD'
               spc_afd_df['instrument_codes']= 'IODP-SRM:IODP-SRM-AFD'
               irm_out_df=pd.concat([irm_out_df,spc_acq_df,spc_afd_df])
           strings=[]
           for i in range(len(irm_out_df)):strings.append(str(i))
           irm_out_df['measurement']=irm_out_df['experiment']+strings
           irm_out_df['description']=irm_out_df['offline_treatment']
           offline_df=pd.concat([offline_df,irm_out_df])  # put the irm data into the offline dataframe
    if dscr_ex_file:
        offline_df.drop(columns=['offline_list'],inplace=True)
        offline_df.drop(columns=['offline_treatment'],inplace=True)
        offline_df.sort_values(by='sequence',inplace=True)
        offline_df.drop_duplicates(subset=['sequence'],inplace=True)
        offline_df.fillna("",inplace=True)
        offline_dicts = offline_df.to_dict('records')
        pmag.magic_write(offline_meas_out, offline_dicts, 'measurements')
        measurements_df=meas_df # put all the non-offline treatments back into measurements_df
    if 'offline_treatment' in measurements_df.columns:
        measurements_df.drop(columns=['offline_treatment'],inplace=True)
    if 'offline_list' in measurements_df.columns:
        measurements_df.drop(columns=['offline_list'],inplace=True)
    measurements_df.sort_values(by='sequence',inplace=True)
    measurements_df.drop_duplicates(subset=['sequence'],inplace=True)
    measurements_df['treat_step_num']=measurements_df['sequence']
    measurements_df.fillna("",inplace=True)
    measurements_df['description']=measurements_df['description']+':'+measurements_df['comment']
    measurements_df.drop(columns=['comment'],inplace=True)
    meas_dicts = measurements_df.to_dict('records')
    meas_dicts=pmag.measurements_methods3(meas_dicts,noave=noave)
    pmag.magic_write(meas_out, meas_dicts, 'measurements')

    return True, meas_out

### IODP_jr6_magic

def iodp_jr6_lore(jr6_file, dir_path=".", input_dir_path="",volume=7,noave=False,dc_field=50e-6,
                  meas_file="measurements.txt", spec_file="specimens.txt"):
    """
    Convert IODP JR6 measurement files in MagIC file(s). This program
    assumes that you have created the specimens, samples, sites and location
    files using convert_2_magic.iodp_samples_csv from files downloaded from the LIMS online
    repository and that all samples are in that file.

    Parameters
    ----------
    jr6_file : str
        input csv file downloaded from LIMS online repository
    dir_path : str
        output directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    meas_file : str
        output measurement file name, default "measurements.txt"
    spec_file : str
        specimens file name created by, for example, convert_2_magic.iodp_samples_csv, default "specimens.txt"
        file should already be in dir_path
    volume : float
        volume in cm^3 assumed during measurement on SRM.  The so-called "Japanese" cubes have a volume of 7cc
    noave : Boolean
         if False, average replicate measurements
    dc_field : float
        if ARM measurements are in the file, this was the DC bias field applied

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful, meas_file name written)
    """
    # initialize defaults
    version_num = pmag.get_version()
    # format variables
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    # convert cc to m^3
    volume = float(volume) * 1e-6
    meas_reqd_columns=['specimen','measurement','experiment','sequence','quality','method_codes',\
                       'instrument_codes','citations',\
                       'treat_temp','treat_ac_field','treat_dc_field',\
                      'treat_dc_field_phi','treat_dc_field_theta','meas_temp',\
                      'dir_dec','dir_inc','magn_moment','magn_volume',\
                       'description','timestamp','software_packages',\
                       'external_database_ids','treat_step_num','meas_n_orient']
    jr6_file = pmag.resolve_file_name(jr6_file, input_dir_path)
    spec_file = pmag.resolve_file_name(spec_file, dir_path)
    specimens_df=pd.read_csv(spec_file,sep='\t',header=1)
    if len(specimens_df)==0:
        print ('you must download and process the samples table from LORE prior to using this')
        print ('see convert_2_magic.iodp_samples_csv for help')
        return False, ""
    LORE_specimens=list(specimens_df.specimen.unique())
    measurements_df=pd.DataFrame(columns=meas_reqd_columns)
    meas_out = os.path.join(output_dir_path, meas_file)
    citations = "This study"
    in_df=pd.read_csv(jr6_file)
    if len(in_df)==0:
        print ('you must download a csv file from the LIMS database and place it in your input_dir_path')
        return False, ""
    in_df.sort_values(by='Treatment value (mT or °C or ex. B14)',inplace=True)
    hole,jr6_specimens=iodp_sample_names(in_df)
    for spec in list(jr6_specimens.unique()):
        if spec not in LORE_specimens:
            print (spec, ' not found in sample table')
    # set up defaults
    measurements_df['specimen']=jr6_specimens
    measurements_df['quality']='g'
    measurements_df['citations']='This study'
    measurements_df['meas_temp']=273
    measurements_df['software_packages']=version_num
    measurements_df["treat_temp"] = '%8.3e' % (273)  # room temp in kelvin
    measurements_df["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
    measurements_df["treat_ac_field"] = '0'
    measurements_df["treat_dc_field"] = '0'
    measurements_df["treat_dc_field_phi"] = '0'
    measurements_df["treat_dc_field_theta"] = '0'
    measurements_df["treat_step_num"] = 1
    measurements_df['meas_n_orient'] = 3
    measurements_df["standard"] = 'u'  # assume all data are "good"
    measurements_df["dir_csd"] = '0'  # assume all data are "good"
    measurements_df["method_codes"] = 'LT-NO' # assume all are NRMs
    measurements_df['instrument_codes']="IODP-JR6" # assume all measurements on shipboard JR6
    measurements_df['timestamp']=pd.to_datetime(\
                               in_df['Timestamp (UTC)']).dt.strftime("%Y-%m-%dT%H:%M:%S")+'Z'
    # use the sample coordinates, assume was placed correctly in the JR6 and use az=0,pl=-90 to
    # put into 'geographic' coordinates
    incs=in_df['Inclination (°)'].values
    decs=in_df['Declination (°)'].values
    azs=np.ones(len(decs))*0
    pls=np.ones(len(decs))*-90
    geo=np.vstack((decs,incs,azs,pls)).transpose()
    drot,irot=pmag.dogeo_V(geo)

    measurements_df['dir_dec']=drot # declination
    measurements_df['dir_inc']=irot # inclination
    measurements_df['magn_volume']=in_df['Intensity raw (A/m)'] # magnetization
    measurements_df['magn_moment']=measurements_df['magn_volume']*volume # moment in Am^2
    measurements_df['description']=in_df['Treatment type']
    measurements_df['treat_ac_field']=in_df['Treatment value (mT or °C or ex. B14)']*1e-3 # initialize all treatments to AF in mT
    measurements_df.loc[measurements_df['description']=='AD',\
                        'method_codes']='LT-AF-Z'
    measurements_df.loc[measurements_df['description']=='AD',\
                        'instrument_codes']='IODP-JR6:IODP-D2000'
    measurements_df.loc[measurements_df['description']=='ARM',\
                        'method_codes']='LT-AF-I'
    measurements_df.loc[measurements_df['description']=='ARM',\
                        'instrument_codes']='IODP-JR6:IODP-D2000'
    measurements_df.loc[measurements_df['description']=='ARM',"treat_dc_field"] = dc_field #
    measurements_df['external_database_ids']='LORE['+in_df['Test No.'].astype('str')+']'
# add these later when controlled vocabs implemented
    measurements_df.loc[measurements_df['description']=='TD','method_codes']='LT-T-Z'
    measurements_df.loc[measurements_df['description']=='TD',\
                        'instrument_codes']='IODP-SRM:IODP-TDS'
    measurements_df.loc[measurements_df['description']=='TD',"treat_temp"] =\
                        in_df['Treatment value (mT or °C or ex. B14)']+273
    #measurements_df.loc[measurements_df['description']=='IRM','method_codes']='LT-IRM'
    #measurements_df.loc[measurements_df['description']=='IRM',\
       #                 'instrument_codes']='IODP-SRM:IODP-IRM'

    measurements_df.fillna("",inplace=True)
    meas_dicts = measurements_df.to_dict('records')
    meas_dicts=pmag.measurements_methods3(meas_dicts,noave=noave)
    pmag.magic_write(meas_out, meas_dicts, 'measurements')

    return True, meas_out


def iodp_kly4s_lore(kly4s_file, meas_out='measurements.txt',
                    spec_infile='specimens.txt', spec_out='specimens.txt',
                    instrument='IODP-KLY4S', actual_volume="",dir_path='.', input_dir_path=''):
    """
    Converts ascii files generated by SUFAR ver.4.0 and downloaded from the LIMS online
    repository to MagIC (datamodel 3) files

    Parameters
    ----------
    kly4s_file : str
        input LORE downloaded csv file, required
    meas_output : str
        measurement output filename, default "measurements.txt"
    spec_infile : str
        specimen infile, default specimens.txt
        [file created by iodp_samples_csv from LORE downloaded sample file]
    spec_outfile : str
        specimen outfile, default "kly4s_specimens.txt"
    instrument : str
        instrument name, default ""
    actual_volume : float
        the nominal volume is assumed to be 8cc or even 10cc, depending on the shipboard
        software used, actual_vol is the  actual specimen volume in cc
    dir_path : str
        output directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful, file name written)

    """
    # initialize defaults
    version_num = pmag.get_version()
    # format variables
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    # set up required columns
    meas_reqd_columns=['specimen','measurement','experiment','sequence','quality','method_codes',\
                       'instrument_codes','citations',\
                       'treat_temp','treat_ac_field','treat_dc_field',\
                      'treat_dc_field_phi','treat_dc_field_theta','meas_temp',\
                      'dir_dec','dir_inc','magn_moment','magn_volume',\
                       'description','timestamp','software_packages',\
                       'external_database_ids','experiments','treat_step_num']
    spec_reqd_columns=['specimen','sample','result_quality','method_codes','volume',\
                       'specimen_name_alternatives','citations',\
                      'aniso_type','aniso_s_n_measurements',\
                      'azimuth','dip','aniso_s_sigma',\
                      'aniso_s_unit','aniso_tilt_correction',]
    # sort out file paths
    kly4s_file = pmag.resolve_file_name(kly4s_file, input_dir_path)
    spec_out = pmag.resolve_file_name(spec_out, dir_path)
    spec_file=pmag.resolve_file_name(spec_infile, dir_path)
    meas_out = pmag.resolve_file_name(meas_out, dir_path)
    # read in necessary data:
    if not os.path.exists(spec_file):
        return False, "you must download and process the samples table from LORE before importing a KLY4S file"
    specs=pd.read_csv(spec_file,sep='\t',header=1) # read in existing specimen table
    if len(specs)==0:
        print ('you must download and process the samples table from LORE prior to using this')
        print ('see convert_2_magic.iodp_samples_csv for help')
        return False, ""
    LORE_specimens=list(specs.specimen.unique())
    in_df=pd.read_csv(kly4s_file)
    if len(in_df)==0:
        print ('you must download a csv file from the LIMS database and place it in your input_dir_path')
        return False, ""
    measurements_df=pd.DataFrame(columns=meas_reqd_columns)
    specimens_df=pd.DataFrame(columns=spec_reqd_columns)
    hole,kly4s_specimens=iodp_sample_names(in_df)
    for spec in list(kly4s_specimens.unique()):
        if spec not in LORE_specimens:
            print (spec, ' not found in specimen table')

    # set up defaults
        # specimens table defaults
    specimens_df['specimen']=kly4s_specimens
    specimens_df['sample']=kly4s_specimens
    specimens_df['result_quality']='g'
    specimens_df['citations']='This study'
    specimens_df['aniso_type']='AMS'
    specimens_df['azimuth']=0
    specimens_df['dip']=0
    specimens_df['aniso_s_n_measurements']=192
    specimens_df['aniso_tilt_correction']=0
    specimens_df['aniso_s_unit']='SI'
    specimens_df['aniso_s_sigma']=''
    specimens_df['method_codes']= "LP-X:AE-H:LP-AN-MS"
    specimens_df['experiments']=specimens_df['specimen'].astype('str')+'_'+ "LP-AN-MS"
        # measurements table
    measurements_df['specimen']=kly4s_specimens
    measurements_df['quality']='g'
    measurements_df['citations']='This study'
    measurements_df['meas_temp']=273
    measurements_df['software_packages']=version_num
    measurements_df["treat_temp"] = '%8.3e' % (273)  # room temp in kelvin
    measurements_df["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
    measurements_df["treat_ac_field"] = '0'
    measurements_df["treat_dc_field"] = '0'
    measurements_df["treat_dc_field_phi"] = '0'
    measurements_df["treat_dc_field_theta"] = '0'
    measurements_df["treat_step_num"] = '1'
    measurements_df["standard"] = 'u'  # assume all data are "good"
    measurements_df['instrument_codes']="IODP-KLY4S" # assume all measurements on shipboard KLY4S
    measurements_df['description']='Bulk sucsecptibility measurement'
    measurements_df['method_codes']='LP-X'
    measurements_df['experiment']=measurements_df['specimen'].astype('str')+'_'+\
                                  measurements_df['method_codes'].astype('str')
    meas_num=range(len(kly4s_specimens))
    measurements_df['sequence']=meas_num
    measurements_df['measurement']=measurements_df['experiment'].astype('str')+'-'+\
                                   measurements_df['sequence'].astype('str')
# parse the measurement data into  columns
    nominal_volume=in_df['Sample volume (CC)']*1e-6 # convert cc to m^3
    if actual_volume:
        actual_volume=(1e-6*actual_volume)
        factor=nominal_volume/actual_volume
    else:
        actual_volume=nominal_volume
        factor=1
    measurements_df['susc_chi_volume']=in_df['Bulk susceptibility(SI)']*factor
    measurements_df['external_database_ids']='LORE['+in_df['Test No.'].astype('str')+']'
# parse specimen data into columns
    specimens_df['specimen_name_alternatives']=in_df['Text ID']
    specimens_df['volume']=actual_volume
    s1=in_df['Normalized tensor K11']
    s2=in_df['Normalized tensor K22']
    s3=in_df['Normalized tensor K33']
    s4=in_df['Normalized tensor K12']
    s5=in_df['Normalized tensor K23']
    s6=in_df['Normalized tensor K13']
    if 'Standard deviation(SI)' in in_df.columns:
        specimens_df['aniso_s_sigma']=in_df['Standard deviation(SI)']
    #if (s1+s2+s3)>.35: # AGICO format
    #    s1=s1/3
    #    s2=s2/3
    #    s3=s3/3
    #    s4=s4/3
    #    s5=s5/3
    #    s6=s6/3
    specimens_df['aniso_s'] = s1.astype('str')+':'+ s2.astype('str')+':'+s3.astype('str')+':'+\
                              s4.astype('str')+':'+ s5.astype('str')+':'+ s6.astype('str')
    tau1=in_df['Kmax susceptibility (SI)']/3
    v1_dec=in_df['Kmax dec (deg)']
    v1_inc=in_df['Kmax inc (deg)']
    specimens_df['aniso_v1']=tau1.astype('str')+":"+v1_dec.astype('str')+":"+v1_inc.astype('str')
    tau2=in_df['Kint susceptibility (SI)']/3
    v2_dec=in_df['Kint dec (deg)']
    v2_inc=in_df['Kint inc (deg)']
    specimens_df['aniso_v2']=tau2.astype('str')+":"+v2_dec.astype('str')+":"+v2_inc.astype('str')
    tau3=in_df['Kmin susceptibility (SI)']/3
    v3_dec=in_df['Kmin dec (deg)']
    v3_inc=in_df['Kmin inc (deg)']
    specimens_df['aniso_v3']=tau3.astype('str')+":"+v3_dec.astype('str')+":"+v3_inc.astype('str')


# output data files
    measurements_df.fillna("",inplace=True)
    meas_dicts = measurements_df.to_dict('records')

    pmag.magic_write(meas_out, meas_dicts, 'measurements')
    specimens_df.fillna("",inplace=True)
    spec_dicts = specimens_df.to_dict('records')
    pmag.magic_write(spec_out, spec_dicts, 'specimens')

    return True, meas_out



def iodp_jr6(mag_file, dir_path=".", input_dir_path="",
             meas_file="measurements.txt", spec_file="specimens.txt",
             samp_file="samples.txt", site_file="sites.txt", loc_file="locations.txt",
             site="unknown", expedition="unknown", lat="", lon="",
             noave=False, volume=12, meth_code="LP-NO"):

    """
    Conversion for IODP jr6 format files into MagIC file(s)

    Parameters
    ----------
    mag_file : str
        input file name
    dir_path : str
        working directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    meas_file : str
        output measurement file name, default "measurements.txt"
    spec_file : str
        output specimen file name, default "specimens.txt"
    samp_file: str
        output sample file name, default "samples.txt"
    site_file : str
        output site file name, default "sites.txt"
    loc_file : str
        output location file name, default "locations.txt"
    site : str
        hole name (i.e., U1456A), default "unknown"
    expedition : str
        expedition name, (i.e. 312), default "unknown"
    lat : float
        latitude, default ""
    lon : float
        longitude, default ""
    noave : bool
       do not average duplicate measurements, default False (so by default, DO average)
    volume : float
        volume in ccs, default 12
    meth_code : str
        default "LP-NO"
        NB: additional codes "FS-C-DRILL-IODP:SP-SS-C:SO-V" will be added automatically

    Returns
    ---------
    Tuple : (True or False indicating if conversion was successful, meas_file name written)

    """

    def fix_separation(filename, new_filename):
        old_file = open(filename, 'r')
        new_file = open(new_filename, 'w')
        data = old_file.readlines()
        for line in data:
            ldata = line.split()
            if len(ldata[0]) > 10:
                ldata.insert(1, ldata[0][10:])
                ldata[0] = ldata[0][:10]
            ldata = [ldata[0]]+[d.replace('-', ' -') for d in ldata[1:]]
            new_line = ' '.join(ldata)+'\n'
            new_file.write(new_line)
        old_file.close()
        new_file.close()
        return new_filename

    # initialize some stuff
    demag = "N"
    version_num = pmag.get_version()
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    # convert cc to m^3
    volume = volume * 1e-6
    meth_code = meth_code+":FS-C-DRILL-IODP:SP-SS-C:SO-V"
    meth_code = meth_code.strip(":")
    if not mag_file:
        print("-W- You must provide an IODP_jr6 format file")
        return False, "You must provide an IODP_jr6 format file"

    mag_file = pmag.resolve_file_name(mag_file, input_dir_path)

    # validate variables
    if not os.path.isfile(mag_file):
        print('The input file you provided: {} does not exist.\nMake sure you have specified the correct filename AND correct input directory name.'.format(mag_file))
        return False, 'The input file you provided: {} does not exist.\nMake sure you have specified the correct filename AND correct input directory name.'.format(mag_file)

    # parse data
    temp = os.path.join(output_dir_path, 'temp.txt')
    fix_separation(mag_file, temp)
    infile = open(temp, 'r')
    lines = infile.readlines()
    infile.close()
    try:
        os.remove(temp)
    except OSError:
        print("problem with temp file")
    citations = "This study"
    MeasRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    for line in lines:
        MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}
        line = line.split()
        spec_text_id = line[0]
        specimen = spec_text_id
        for dem in ['-', '_']:
            if dem in spec_text_id:
                sample = dem.join(spec_text_id.split(dem)[:-1])
                break
        location = expedition + site

        if specimen != "" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
            SpecRec['specimen'] = specimen
            SpecRec['sample'] = sample
            SpecRec['volume'] = volume
            SpecRec['citations'] = citations
            SpecRecs.append(SpecRec)
        if sample != "" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
            SampRec['sample'] = sample
            SampRec['site'] = site
            SampRec['citations'] = citations
            SampRec['azimuth'] = line[6]
            SampRec['dip'] = line[7]
            SampRec['bed_dip_direction'] = line[8]
            SampRec['bed_dip'] = line[9]
            SampRec['method_codes'] = meth_code
            SampRecs.append(SampRec)
        if site != "" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
            SiteRec['site'] = site
            SiteRec['location'] = location
            SiteRec['citations'] = citations
            SiteRec['lat'] = lat
            SiteRec['lon'] = lon
            SiteRecs.append(SiteRec)
        if location != "" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
            LocRec['location'] = location
            LocRec['citations'] = citations
            LocRec['expedition_name'] = expedition
            LocRec['lat_n'] = lat
            LocRec['lon_e'] = lon
            LocRec['lat_s'] = lat
            LocRec['lon_w'] = lon
            LocRecs.append(LocRec)

        MeasRec['specimen'] = specimen
        MeasRec["citations"] = citations
        MeasRec['software_packages'] = version_num
        MeasRec["treat_temp"] = '%8.3e' % (273)  # room temp in kelvin
        MeasRec["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
        MeasRec["quality"] = 'g'
        MeasRec["standard"] = 'u'
        MeasRec["treat_step_num"] = '1'
        MeasRec["treat_ac_field"] = '0'

        x = float(line[4])
        y = float(line[3])
        negz = float(line[2])
        cart = np.array([x, y, -negz]).transpose()
        direction = pmag.cart2dir(cart).transpose()
        expon = float(line[5])
        magn_volume = direction[2] * (10.0**expon)
        moment = magn_volume * volume

        MeasRec["magn_moment"] = str(moment)
        # str(direction[2] * (10.0 ** expon))
        MeasRec["magn_volume"] = str(magn_volume)
        MeasRec["dir_dec"] = '%7.1f' % (direction[0])
        MeasRec["dir_inc"] = '%7.1f' % (direction[1])

        step = line[1]
        if step == 'NRM':
            meas_type = "LT-NO"
        elif step[0:2] == 'AD':
            meas_type = "LT-AF-Z"
            treat = float(step[2:])
            MeasRec["treat_ac_field"] = '%8.3e' % (
                treat*1e-3)  # convert from mT to tesla
        elif step[0:2] == 'TD':
            meas_type = "LT-T-Z"
            treat = float(step[2:])
            MeasRec["treat_temp"] = '%8.3e' % (treat+273.)  # temp in kelvin
        elif step[0:3] == 'ARM':
            meas_type = "LT-AF-I"
            treat = float(step[3:])
            MeasRec["treat_ac_field"] = '%8.3e' % (
                treat*1e-3)  # convert from mT to tesla
            MeasRec["treat_dc_field"] = '%8.3e' % (
                50e-6)  # assume 50uT DC field
            MeasRec["measurement_description"] = 'Assumed DC field - actual unknown'
        elif step[0] == 'A':
            meas_type = "LT-AF-Z"
            treat = float(step[1:])
            MeasRec["treat_ac_field"] = '%8.3e' % (
                treat*1e-3)  # convert from mT to tesla
        elif step[0] == 'T':
            meas_type = "LT-T-Z"
            treat = float(step[1:])
            MeasRec["treat_temp"] = '%8.3e' % (treat+273.)  # temp in kelvin
        elif step[0:3] == 'IRM':
            meas_type = "LT-IRM"
            treat = float(step[3:])
            MeasRec["treat_dc_field"] = '%8.3e' % (
                treat*1e-3)  # convert from mT to tesla
        else:
            print('unknown treatment type for ', row)
            return False, 'unknown treatment type for ', row

        MeasRec['method_codes'] = meas_type
        MeasRecs.append(MeasRec.copy())

    con = cb.Contribution(output_dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.tables['specimens'].write_magic_file(custom_name=spec_file,dir_path=dir_path)
    con.tables['samples'].write_magic_file(custom_name=samp_file,dir_path=dir_path)
    con.tables['sites'].write_magic_file(custom_name=site_file,dir_path=dir_path)
    con.tables['locations'].write_magic_file(custom_name=loc_file,dir_path=dir_path)
    con.tables['measurements'].write_magic_file(custom_name=meas_file,dir_path=dir_path)

    return (True, meas_file)

### IODP_samples_magic conversion


def iodp_samples(samp_file, output_samp_file=None, output_dir_path='.',
                 input_dir_path='', data_model_num=3):
    """
    Convert IODP samples data file into MagIC samples file.
    Default is to overwrite samples.txt in your working directory.

    Parameters
    ----------
    samp_file : str
        path to IODP sample file to convert
    output_samp_file : str
        MagIC-format samples file to append to, default None
    output_dir_path : str
        output file directory, default "."
    input_dir_path : str
        input file directory IF different from output_dir_path, default ""
    data_model_num : int
        MagIC data model [2, 3], default 3

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful, samp_file name written)

    """
    samp_file_name = "samples.txt"
    sample_alternatives = "sample_alternatives"
    method_codes = "method_codes"
    sample_name = "sample"
    site_name = "site"
    expedition_name = "expedition_name"
    location_name = "location"
    citation_name = "citation"
    dip = "dip"
    azimuth = "azimuth"
    core_depth = "core_depth"
    composite_depth = "composite_depth"
    timestamp = "timestamp"
    file_type = "samples"
    data_model_num = int(float(data_model_num))
    if data_model_num == 2:
        samp_file_name = "er_samples.txt"
        sample_alternatives = "er_sample_alternatives"
        method_codes = "magic_method_codes"
        sample_name = "er_sample_name"
        site_name = "er_site_name"
        expedition_name = "er_expedition_name"
        location_name = "er_location_name"
        citation_name = "er_citation_names"
        dip = "sample_dip"
        azimuth = "sample_azimuth"
        core_depth = "sample_core_depth"
        composite_depth = "sample_composite_depth"
        timestamp = "sample_date"
        file_type = "er_samples"


    text_key = None
    comp_depth_key = ""
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, output_dir_path)
    samp_file = pmag.resolve_file_name(samp_file, input_dir_path)
    Samps = []
    samp_out = os.path.join(output_dir_path, samp_file_name)
    if output_samp_file:
        if os.path.exists(output_samp_file):
            samp_out = os.path.join(output_dir_path, output_samp_file)
            Samps, file_type = pmag.magic_read(samp_out)
            print(len(Samps), ' read in from: ', samp_out)
    fin = open(samp_file, "r")
    file_input = fin.readlines()
    fin.close()
    keys = file_input[0].replace('\n', '').split(',')
    if "CSF-B Top (m)" in keys:
        comp_depth_key = "CSF-B Top (m)"
    elif "Top depth CSF-B (m)" in keys:
        comp_depth_key = "Top depth CSF-B (m)"
    # incorporate changes to LIMS data model, while maintaining backward
    # compatibility
    keys = [key.strip('"').strip("'") for key in keys]
    if "Top Depth (m)" in keys:
        depth_key = "Top Depth (m)"
    elif "CSF-A Top (m)" in keys:
        depth_key = "CSF-A Top (m)"
    elif "Top depth CSF-A (m)" in keys:
        depth_key = "Top depth CSF-A (m)"
    if "Text Id" in keys:
        text_key = "Text Id"
    elif "Text identifier" in keys:
        text_key = "Text identifier"
    elif "Text ID" in keys:
        text_key = "Text ID"
    if "Sample Date Logged" in keys:
        date_key = "Sample Date Logged"
    elif "Sample date logged" in keys:
        date_key = "Sample date logged"
    elif "Date sample logged" in keys:
        date_key = "Date sample logged"
    elif "Timestamp (UTC)" in keys:
        date_key = "Timestamp (UTC)"
    if 'Volume (cc)' in keys:
        volume_key = 'Volume (cc)'
    if 'Volume (cm^3)' in keys:
        volume_key = 'Volume (cm^3)'
    if 'Volume (cm3)' in keys:
        volume_key = 'Volume (cm3)'
    if not text_key:
        return False, "Could not extract the necessary data from your input file.\nPlease make sure you are providing a correctly formatted IODP samples csv file."
    ErSamples, samples, file_format = [], [], 'old'
    for line in file_input[1:]:
        if line[0] != '0':
            ODPRec, SampRec = {}, {}
            interval, core = "", ""
            rec = line.replace('\n', '').split(',')
            if len(rec) < 2:
                print("Error in csv file, blank columns")
                break
            for k in range(len(keys)):
                ODPRec[keys[k]] = rec[k].strip('"')
            SampRec[sample_alternatives] = ODPRec[text_key]
            if "Label Id" in keys:  # old format
                label = ODPRec['Label Id'].split()
                if len(label) > 1:
                    interval = label[1].split('/')[0]
                    pieces = label[0].split('-')
                    core = pieces[2]
                while len(core) < 4:
                    core = '0' + core  # my way
            else:  # new format
                file_format = 'new'
                pieces = [ODPRec['Exp'], ODPRec['Site'] + ODPRec['Hole'],
                          ODPRec['Core'] + ODPRec['Type'], ODPRec['Sect'], ODPRec['A/W']]
                interval = ODPRec['Top offset (cm)'].split(
                    '.')[0].strip()  # only integers allowed!
                core = ODPRec['Core'] + ODPRec['Type']
            if core != "" and interval != "":
                SampRec[method_codes] = 'FS-C-DRILL-IODP:SP-SS-C:SO-V'
                if file_format == 'old':
                    SampRec[sample_name] = pieces[0] + '-' + pieces[1] + \
                        '-' + core + '-' + pieces[3] + \
                        '-' + pieces[4] + '-' + interval
                else:
                    SampRec[sample_name] = pieces[0] + '-' + pieces[1] + '-' + core + '-' + \
                        pieces[3] + '_' + pieces[4] + '_' + \
                        interval  # change in sample name convention
                SampRec[site_name] = SampRec[sample_name]
                # pieces=SampRec['er_sample_name'].split('-')
                SampRec[expedition_name] = pieces[0]
                SampRec[location_name] = pieces[1]
                SampRec[citation_name] = "This study"
                SampRec[dip] = "0"
                SampRec[azimuth] = "0"
                SampRec[core_depth] = ODPRec[depth_key]
                if ODPRec[volume_key] != "":
                    SampRec['sample_volume'] = str(
                        float(ODPRec[volume_key]) * 1e-6)
                else:
                    SampRec['sample_volume'] = '1'
                if comp_depth_key != "":
                    SampRec[composite_depth] = ODPRec[comp_depth_key]
                dates = ODPRec[date_key].split()
                if '/' in dates[0]:  # have a date
                    mmddyy = dates[0].split('/')
                    yyyy = '20' + mmddyy[2]
                    mm = mmddyy[0]
                    if len(mm) == 1:
                        mm = '0' + mm
                    dd = mmddyy[1]
                    if len(dd) == 1:
                        dd = '0' + dd
                    date = yyyy + ':' + mm + ':' + \
                        dd + ':' + dates[1] + ":00.00"
                else:
                    date = ""
                SampRec[timestamp] = date
                ErSamples.append(SampRec)
                samples.append(SampRec[sample_name])
    if len(Samps) > 0:
        for samp in Samps:
            if samp[sample_name] not in samples:
                ErSamples.append(samp)
    Recs, keys = pmag.fillkeys(ErSamples)
    pmag.magic_write(samp_out, Recs, file_type)
    print('sample information written to: ', samp_out)
    return True, samp_out


def iodp_sample_names(df):
    """
    Convert expedition, hole, section, type, interval to sample name in format:
    exp-hole-type-sect-interval

    Parameters
    ___________
    df : Pandas DataFrame
         dataframe read in from .csv file downloaded from LIMS online database

    Returns
    --------------

    holes : list
           IODP Holes name in format U999A

    specimens : pandas Series
            series with sample names, e.g. 999-U999A-1H-1-W-1


    """
    if 'Top offset (cm)' in df.columns:
        offset_key='Top offset (cm)'
    elif 'Offset (cm)' in df.columns:
        offset_key='Offset (cm)'
    else:
        print ('No offset key found')
        return False,[]
    interval=df[offset_key].astype('float').astype('str')
    holes=df['Site'].astype('str')+df['Hole']
    specimens=df['Exp'].astype('str')+'-'+holes +'-'+df['Core'].astype('str')+df['Type'].astype('str')+\
              '-'+df['Sect'].astype('str')+ '-' + df['A/W']+'-'+ interval
    return holes, specimens

def iodp_samples_csv(lims_sample_file, spec_file='specimens.txt',samp_file="samples.txt",
                     site_file="sites.txt",loc_file="locations.txt",dir_path='.',
                     input_dir_path='',comp_depth_key="",lat="",lon="",
                     exp_name="",exp_desc="",age_low=0,age_high=200e6):
    """
    Convert IODP samples data file downloaded from LIMS as .csv file into datamodel 3.0 MagIC samples file.
    Default is to overwrite samples.txt in your working directory.

    Parameters
    ----------
    lims_sample_file : str
        path to IODP sample file to convert
    dir_path : str
        working directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""

    spec_file : str
        output specimens.txt file name
    samp_file : str
        output samples.txt file name
    site_file : str
        output sites.txt file name
    loc_file : str
        output locations.txt name
    comp_depth_key : str
        if not "", there is a composite depth model, for example 'Top depth CSF-B (m)'
    lat : float
        latitude of hole location
    lon : float
        longitude of hole location
    exp_name : str
        expedition number (e.g., 382)
    exp_description :str
        expedition nick name (e.g., Iceberg Alley)
    age_high : float
        maximum age of hole in Ma
    age_low : float
        minimum age of hole in Ma

    NOTE:  all output files will overwrite existing files.

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful,file names written)

    """
    # define required columns for samples, sites, locations (holes).
    spec_reqd_columns=['specimen','sample','result_quality','method_codes','volume',\
                       'specimen_name_alternatives','citations']
    samp_reqd_columns=['sample','site','result_type','result_quality',\
                       'azimuth','dip','azimuth_correction','method_codes','citations']
    site_reqd_columns=['site','location','lat','lon','result_type','result_quality','method_codes',\
                       'core_depth','composite_depth',\
                       'geologic_types','geologic_classes','lithologies',\
                      'age','age_low','age_high','age_unit','citations']
    loc_reqd_columns=['location', 'expedition_name','expedition_ship','expedition_description','lat_s','lat_n',\
                      'geologic_classes','lithologies','location_type',\
                      'lon_w','lon_e','age_low','age_high','age_unit','citations']
    # fix the path names for input and output directories (if different)
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    # find the input sample file name downloaded from LORE
    samp_file_name = pmag.resolve_file_name(lims_sample_file, input_dir_path)
    # set the output file names
    spec_out = os.path.join(output_dir_path, spec_file)
    samp_out = os.path.join(output_dir_path, samp_file)
    site_out = os.path.join(output_dir_path, site_file)
    loc_out = os.path.join(output_dir_path, loc_file)
    # read in the data from the downloaded .csv file
    iodp_sample_data=pd.read_csv(samp_file_name)
    # get rid of incomplete sample rows
    iodp_sample_data.dropna(subset=['Hole','Type','Sect','Top offset (cm)','Top depth CSF-A (m)','A/W'],
                            inplace=True)

    # replace the 'nan' values with blanks
    iodp_sample_data.fillna('',inplace=True)
    # check if there are data
    if len(iodp_sample_data)==0:
        return False, "Could not extract the necessary data from your input file.\nPlease make sure you are providing a correctly formatted IODP samples csv file."
    # create the MagIC data model 3.0 DataFrames with the required column
    specimens_df=pd.DataFrame(columns = spec_reqd_columns)
    samples_df=pd.DataFrame(columns = samp_reqd_columns)
    sites_df=pd.DataFrame(columns = site_reqd_columns)
    # set some column headers for the sample master .csv file
    depth_key = "Top depth CSF-A (m)"
    text_key = "Text ID"
    date_key = "Date sample logged"
    volume_key = 'Volume (cm3)'
    if volume_key not in iodp_sample_data.columns:
        volume_key = 'Sample volume (CC)'
    # convert the meta data in the sample master to MagIC datamodel 3
    # construct the sample name
    holes,specimens=iodp_sample_names(iodp_sample_data)
    # put the sample name in the specimen, sample, site
    specimens_df['specimen']=specimens
    specimens_df['sample']=specimens
    samples_df['sample']=specimens
    samples_df['site']=specimens

    # add required meta-data for each hole to the locations table
    unique_holes=list(holes.unique())
    loc_dicts=[]
    for hole in unique_holes:
        loc_dict={}
        print (hole)
        loc_dict['location']=hole
        loc_dict['expedition_name']=exp_name
        loc_dict['expedition_ship']='JOIDES Resolution'
        loc_dict['expedition_description']=exp_desc
        loc_dict['lat_s']=lat
        loc_dict['lat_n']=lat
        loc_dict['lon_w']=lon
        loc_dict['lon_e']=lon
        loc_dict['location_type']="Drill Site"
        loc_dict['citations']='This study'
        loc_dict['age_high']=age_high
        loc_dict['age_low']=age_low
        loc_dict['age_unit']='Ma'

        loc_dicts.append(loc_dict)
    # add in the rest to the sites table
    sites_df['site']=specimens
    sites_df['core_depth']=iodp_sample_data['Top depth CSF-A (m)']
    sites_df['lat']=lat
    sites_df['lon']=lon
    sites_df['result_type']='i'
    sites_df['result_quality']='g'
    sites_df['method_codes']='FS-C-DRILL-IODP'
    sites_df['location']=hole
    sites_df['citations']="This study"
    if comp_depth_key: sites_df['composite_depth']=iodp_sample_data[comp_depth_key]
    # now do the samples

    samples_df['method_codes']='FS-C-DRILL-IODP:SP-SS-C:SO-V' # could put in sampling tool...
    samples_df['site']=specimens # same as sample and specimen name
    samples_df['result_type']='i'
    samples_df['result_type']='g'
    samples_df['azimuth']='0'
    samples_df['dip']='0'
    samples_df['citations']='This study'

    # NEED TO ADD TIMESTAMP FROM TIMESTAMP KEY SOMEDAY
    # and the specimens
    specimens_df['specimen_name_alternatives']=iodp_sample_data[text_key]
    specimens_df['result_quality']='g'
    specimens_df['method_codes']='FS-C-DRILL-IODP:SP-SS-C:SO-V'
    specimens_df['volume']=iodp_sample_data[volume_key]*1e-6 # convert from cm^3 to m^3
    specimens_df['citations']='This study'
    # fill in the np.nan with blanks
    specimens_df.fillna("",inplace=True)
    # make specimen_df format compatible with MagicDataFrame
    specimens_df.index = specimens_df['specimen']
    specimens_df.index.name = 'specimen name'
    # combine with old specimen records if available
    if os.path.exists(spec_file):
        old_specimens = cb.MagicDataFrame(spec_file)
        old_specimens.df = old_specimens.merge_dfs(specimens_df)
        old_specimens.write_magic_file(spec_file)
    else:
        spec_dicts = specimens_df.to_dict('records')
        pmag.magic_write(spec_out, spec_dicts, 'specimens')

    # fill in the np.nan with blanks
    samples_df.fillna("",inplace=True)
    sites_df.fillna("",inplace=True)
    # save the files in the designated spots samp_out, site_out and loc_out
    samp_dicts = samples_df.to_dict('records')
    pmag.magic_write(samp_out, samp_dicts, 'samples')
    site_dicts = sites_df.to_dict('records')
    pmag.magic_write(site_out, site_dicts, 'sites')
    pmag.magic_write(loc_out, loc_dicts, 'locations')
    return True, samp_out


def iodp_samples_srm(df, spec_file='specimens.txt',samp_file="samples.txt",site_file="sites.txt",dir_path='.',
                 input_dir_path='',comp_depth_key="",lat="",lon=""):
    """
    Convert IODP samples data generated from the SRM measurements file into datamodel 3.0 MagIC samples file.
    Default is to overwrite the output files in your working directory.

    Parameters
    ----------
    df : str
        Pandas DataFrame of SRM Archive data
    dir_path : str
        working directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""

    spec_file : str
        output specimens.txt file name
    samp_file : str
        output samples.txt file name
    site_file : str
        output sites.txt file name
    comp_depth_key : str
        if not "", there is a composite depth model, for example 'Depth CSF-B (m)'
    lat : float
        latitude of hole location
    lon : float
        longitude of hole location

    NOTE:  all output files will overwrite existing files.

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful,file names written)

    """
    # define required columns for samples, sites, locations (holes).
    spec_reqd_columns=['specimen','sample','result_quality','method_codes','volume',\
                       'specimen_name_alternatives','citations']
    samp_reqd_columns=['sample','site','result_type','result_quality',\
                       'azimuth','dip','azimuth_correction','method_codes','citations','core_depth','composite_depth']
    site_reqd_columns=['site','location','lat','lon','result_type','result_quality','method_codes',\
                       'core_depth','composite_depth',\
                       'geologic_types','geologic_classes','lithologies',\
                      'age','age_low','age_high','age_unit','citations']
    # fix the path names for input and output directories (if different)
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    # find the input sample file name downloaded from LORE
    # set the output file names
    spec_out = os.path.join(output_dir_path, spec_file)
    samp_out = os.path.join(output_dir_path, samp_file)
    site_out = os.path.join(output_dir_path, site_file)
    # read in the data from the downloaded .csv file
    # create the MagIC data model 3.0 DataFrames with the required column
    specimens_df=pd.DataFrame(columns = spec_reqd_columns)
    samples_df=pd.DataFrame(columns = samp_reqd_columns)
    sites_df=pd.DataFrame(columns = site_reqd_columns)
    # set some column headers for the sample master .csv file
    depth_key = "Depth CSF-A (m)"
    text_key = "Text ID"
    date_key = "Date sample logged"
    volume_key = 'Volume (cm3)'
    # convert the meta data in the sample master to MagIC datamodel 3
    # construct the sample name

    holes,specimens=iodp_sample_names(df)
    # put the sample name in the specimen, sample, site
    specimens_df['specimen']=specimens
    specimens_df['sample']=specimens
    samples_df['sample']=specimens
    samples_df['site']=specimens
    samples_df['core_depth']=df[depth_key]
    if comp_depth_key: samples_df['composite_depth']=df[comp_depth_key]

    # add in the rest to the sites table
    sites_df['site']=specimens
    sites_df['core_depth']=df[depth_key]
    sites_df['lat']=lat
    sites_df['lon']=lon
    sites_df['result_type']='i'
    sites_df['result_quality']='g'
    sites_df['method_codes']='FS-C-DRILL-IODP'
    sites_df['location']=holes[0]
    sites_df['citations']="This study"
    if comp_depth_key: sites_df['composite_depth']=df[comp_depth_key]
    # now do the samples

    samples_df['method_codes']='FS-C-DRILL-IODP:SP-SS-C:SO-V' # could put in sampling tool...
    samples_df['site']=specimens # same as sample and specimen name
    samples_df['result_type']='i'
    samples_df['result_type']='g'
    samples_df['azimuth']='0'
    samples_df['dip']='0'
    samples_df['citations']='This study'

    # NEED TO ADD TIMESTAMP FROM TIMESTAMP KEY SOMEDAY
    # and the specimens
    specimens_df['result_quality']='g'
    specimens_df['method_codes']='FS-C-DRILL-IODP'
    specimens_df['citations']='This study'
    # fill in the np.nan with blanks
    specimens_df.fillna("",inplace=True)
    samples_df.fillna("",inplace=True)
    sites_df.fillna("",inplace=True)
    # save the files in the designated spots spec_out, samp_out, site_out and loc_out
    spec_dicts = specimens_df.to_dict('records')
    pmag.magic_write(spec_out, spec_dicts, 'specimens')
    samp_dicts = samples_df.to_dict('records')
    pmag.magic_write(samp_out, samp_dicts, 'samples')
    site_dicts = sites_df.to_dict('records')
    pmag.magic_write(site_out, site_dicts, 'sites')

    return holes[0],specimens

def iodp_srm_lore(srm_file, dir_path=".", input_dir_path="",noave=False,comp_depth_key='Depth CSF-B (m)',\
                  meas_file="srm_arch_measurements.txt", spec_file="srm_arch_specimens.txt",\
                  samp_file='srm_arch_samples.txt',site_file='srm_arch_sites.txt',lat="",lon=""):
    """
    Convert IODP archive half measurement files into MagIC file(s).

    Parameters
    ----------
    srm_file : str
        input csv file downloaded from LIMS online repository
    dir_path : str
        output directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    meas_file : str
        output measurement file name, default "measurements.txt"
    spec_file : str
        specimens file name as output file - these specimens are not already in the specimen table
        created by iodp_samples_csv
    samp_file : str
       samples file name as output file - these  are not already in the specimen table
        created by iodp_samples_csv
    site_file : str
        sites file name as output file - these are not already in the samples table
    noave : Boolean
        if False, average replicate measurements

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful, meas_file name written)
    """
    # initialize defaults
    version_num = pmag.get_version()
    # format variables
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    # convert cc to m^3
    meas_reqd_columns=['specimen','measurement','experiment','sequence','quality','method_codes',\
                       'instrument_codes','citations',\
                       'treat_temp','treat_ac_field','treat_dc_field',\
                      'treat_dc_field_phi','treat_dc_field_theta','meas_temp',\
                      'dir_dec','dir_inc','magn_moment','magn_volume',\
                       'description','timestamp','software_packages',\
                       'external_database_ids','treat_step_num','meas_n_orient']
    srm_file = pmag.resolve_file_name(srm_file, input_dir_path)
    spec_file = pmag.resolve_file_name(spec_file, dir_path)
    in_df=pd.read_csv(srm_file,header=0)
    in_df.drop_duplicates(inplace=True)
    in_df.sort_values(by='Treatment Value',inplace=True)
    if len(in_df)==0:
        print ('you must download a csv file from the LIMS database and place it in your input_dir_path')
        return False, 'you must download a csv file from the LIMS database and place it in your input_dir_path'
    measurements_df=pd.DataFrame(columns=meas_reqd_columns)
    meas_out = os.path.join(output_dir_path, meas_file)
    hole,srm_specimens=iodp_samples_srm(in_df, spec_file=spec_file,samp_file=samp_file,site_file=site_file,\
                                        dir_path=dir_path,input_dir_path=input_dir_path,\
                                        comp_depth_key=comp_depth_key,lat=lat,lon=lon)
    # assume only one hole
    # set up defaults
    measurements_df['specimen']=srm_specimens
    if 'Comments' in in_df.columns: measurements_df['comment']=in_df['Comments'] # temporary column
    measurements_df['quality']='g'
    measurements_df['citations']='This study'
    measurements_df['meas_temp']=273
    measurements_df['software_packages']=version_num
    measurements_df["treat_temp"] = '%8.3e' % (273)  # room temp in kelvin
    measurements_df["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
    measurements_df["treat_ac_field"] = '0'
    measurements_df["treat_dc_field"] = '0'
    measurements_df["treat_dc_field_phi"] = '0'
    measurements_df["treat_dc_field_theta"] = '0'
    measurements_df["standard"] = 'u'  # assume all data are "good"
    measurements_df["dir_csd"] = '0'  # assume all data are "good"
    measurements_df["method_codes"] = 'LT-NO' # assume all are NRMs
    measurements_df['instrument_codes']="IODP-SRM" # assume all measurements on shipboard 2G
    measurements_df['treat_step_num']='0' # assign a number
    measurements_df['meas_n_orient']=1 # at least one orientation
    measurements_df['timestamp']=pd.to_datetime(\
                               in_df['Timestamp (UTC)']).dt.strftime("%Y-%m-%dT%H:%M:%S")+'Z'
    measurements_df['dir_dec']=in_df['Declination background & drift corrected (deg)'] # declination
    measurements_df['dir_inc']=in_df['Inclination background & drift corrected (deg)'] # inclination
    measurements_df['magn_volume']=in_df['Intensity background & drift corrected (A/m)'] # magnetization
    Xs=in_df['Magnetic moment x (Am²)']
    Ys=in_df['Magnetic moment y (Am²)']
    Zs=in_df['Magnetic moment z (Am²)']
    magn_moment=np.sqrt(Xs**2+Ys**2+Zs**2)
    measurements_df['magn_moment']=magn_moment # moment in Am^2
    measurements_df['description']=in_df['Treatment Type'] # temporary column
    measurements_df['treat_ac_field']=in_df['Treatment Value']*1e-3 # assume all treatments are AF
    measurements_df.loc[measurements_df['description']=='IN-LINE AF DEMAG',\
                        'method_codes']='LT-AF-Z'
    measurements_df.loc[measurements_df['description']=='IN-LINE AF DEMAG',\
                        'instrument_codes']='IODP-SRM:IODP-SRM-AF'
    measurements_df['external_database_ids']='LORE['+in_df['Test No.'].astype('str')+']'

    measurements_df.fillna("",inplace=True)
    measurements_df['description']=measurements_df['description']+':'+measurements_df['comment']
    measurements_df.drop(columns=['comment'],inplace=True)

    meas_dicts = measurements_df.to_dict('records')
    meas_dicts=pmag.measurements_methods3(meas_dicts,noave=noave)
    pmag.magic_write(meas_out, meas_dicts, 'measurements')
    return True, meas_out


### IODP_srm_magic conversion (old)

def iodp_srm(csv_file="", dir_path=".", input_dir_path="",
             meas_file="measurements.txt", spec_file="specimens.txt",
             samp_file="samples.txt", site_file="sites.txt", loc_file="locations.txt",
             lat="", lon="", noave=0):

    """
    Converts IODP LIMS and LORE SRM archive half sample format files
    to measurements format files.

    Parameters
    ----------
    csv_file : str
        input csv file, default ""
        if no file name is provided, find any .csv files in the provided dir_path
    dir_path : str
        working directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    meas_file : str
        output measurement file name, default "measurements.txt"
    spec_file : str
        output specimen file name, default "specimens.txt"
    samp_file: str
        output sample file name, default "samples.txt"
    site_file : str
        output site file name, default "sites.txt"
    loc_file : str
        output location file name, default "locations.txt"
    lat : float
        latitude, default ""
    lon : float
        longitude, default ""
    noave : bool
       do not average duplicate measurements, default False (so by default, DO average)

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful, meas_file name written)

    """

    # helper function

    def pad_year(date, ind, warn=False, fname=''):
        """
        Parameters
        ----------
        Date: str
            date as colon-delimited string, i.e. 04:10:2015:06:45:00
        ind: int
            index of year position
        warn : bool (default False)
            verbose or not
        fname: str (default '')
            filename for more informative warning

        Returns
        ---------
        new_date: str
           date as colon-delimited,
           with year padded if it wasn't before
        """
        date_list = date.split(':')
        year = date_list[ind]
        if len(year) == 2:
            padded_year = '20' + year
            date_list[ind] = padded_year
            if warn:
                print('-W- Ambiguous year "{}" in {}.'.format(year, fname))
                print('    Assuming {}.'.format(padded_year))
        new_date = ':'.join(date_list)
        if new_date != date and warn:
            print('    Date translated to {}'.format(new_date))
        return new_date


    # initialize defaults
    version_num = pmag.get_version()
    citations = "This study"
    demag = 'NRM'
    depth_method = 'a'
    # format variables
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    if csv_file == "":
        # read in list of files to import
        filelist = os.listdir(input_dir_path)
    else:
        filelist = [csv_file]

    # parsing the data
    MeasRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    file_found = False
    for f in filelist:  # parse each file
        year_warning = True
        if f[-3:].lower() == 'csv':
            print('processing:', f)
            file_found = True
            # get correct full filename and read data
            fname = pmag.resolve_file_name(f, input_dir_path)
            full_file = open(fname)
            file_input = full_file.readlines()
            full_file.close()
            keys = file_input[0].replace('\n', '').split(
                ',')  # splits on underscores
            keys = [k.strip('"') for k in keys]
            if "Interval Top (cm) on SHLF" in keys:
                interval_key = "Interval Top (cm) on SHLF"
            elif " Interval Bot (cm) on SECT" in keys:
                interval_key = " Interval Bot (cm) on SECT"
            elif "Offset (cm)" in keys:
                interval_key = "Offset (cm)"
            else:
                print("couldn't find interval or offset amount")
            # get depth key
            if "Top Depth (m)" in keys:
                depth_key = "Top Depth (m)"
            elif "CSF-A Top (m)" in keys:
                depth_key = "CSF-A Top (m)"
            elif "Depth CSF-A (m)" in keys:
                depth_key = "Depth CSF-A (m)"
            else:
                print("couldn't find depth")
            # get comp depth key
            if "CSF-B Top (m)" in keys:
                comp_depth_key = "CSF-B Top (m)"  # use this model if available
            elif "Depth CSF-B (m)" in keys:
                comp_depth_key = "Depth CSF-B (m)"
            else:
                comp_depth_key = ""
                print("couldn't find composite depth")
            if "Demag level (mT)" in keys:
                demag_key = "Demag level (mT)"
            elif "Demag Level (mT)" in keys:
                demag_key = "Demag Level (mT)"
            elif "Treatment Value" in keys:
                demag_key = "Treatment Value"
            else:
                print("couldn't find demag type")
            # Get inclination key
            if "Inclination (Tray- and Bkgrd-Corrected) (deg)" in keys:
                inc_key = "Inclination (Tray- and Bkgrd-Corrected) (deg)"
            elif "Inclination background + tray corrected  (deg)" in keys:
                inc_key = "Inclination background + tray corrected  (deg)"
            elif "Inclination background + tray corrected  (\xc2\xb0)" in keys:
                inc_key = "Inclination background + tray corrected  (\xc2\xb0)"
            elif "Inclination background &amp; tray corrected (deg)" in keys:
                inc_key = "Inclination background &amp; tray corrected (deg)"
            elif "Inclination background & tray corrected (deg)" in keys:
                inc_key = "Inclination background & tray corrected (deg)"
            elif "Inclination background & drift corrected (deg)" in keys:
                inc_key = "Inclination background & drift corrected (deg)"
            elif "Inclination background + tray corrected  (\N{DEGREE SIGN})" in keys:
                inc_key = "Inclination background + tray corrected  (\N{DEGREE SIGN})"
            else:
                print("couldn't find inclination")
            # get declination key
            if "Declination (Tray- and Bkgrd-Corrected) (deg)" in keys:
                dec_key = "Declination (Tray- and Bkgrd-Corrected) (deg)"
            elif "Declination background + tray corrected (\N{DEGREE SIGN})" in keys:
                dec_key = "Declination background + tray corrected (\N{DEGREE SIGN})"
            elif "Declination background + tray corrected (deg)" in keys:
                dec_key = "Declination background + tray corrected (deg)"
            elif "Declination background + tray corrected (\xc2\xb0)" in keys:
                dec_key = "Declination background + tray corrected (\xc2\xb0)"
            elif "Declination background &amp; tray corrected (deg)" in keys:
                dec_key = "Declination background &amp; tray corrected (deg)"
            elif "Declination background & tray corrected (deg)" in keys:
                dec_key = "Declination background & tray corrected (deg)"
            elif "Declination background & drift corrected (deg)" in keys:
                dec_key = "Declination background & drift corrected (deg)"
            else:
                print("couldn't find declination")
            if "Intensity (Tray- and Bkgrd-Corrected) (A/m)" in keys:
                int_key = "Intensity (Tray- and Bkgrd-Corrected) (A/m)"
            elif "Intensity background + tray corrected  (A/m)" in keys:
                int_key = "Intensity background + tray corrected  (A/m)"
            elif "Intensity background &amp; tray corrected (A/m)" in keys:
                int_key = "Intensity background &amp; tray corrected (A/m)"
            elif "Intensity background & tray corrected (A/m)" in keys:
                int_key = "Intensity background & tray corrected (A/m)"
            elif "Intensity background & drift corrected (A/m)" in keys:
                int_key = "Intensity background & drift corrected (A/m)"
            else:
                print("couldn't find magnetic moment")
            if "Core Type" in keys:
                core_type = "Core Type"
            elif "Type" in keys:
                core_type = "Type"
            else:
                print("couldn't find core type")
            if 'Run Number' in keys:
                run_number_key = 'Run Number'
            elif 'Test No.' in keys:
                run_number_key = 'Test No.'
            else:
                print("couldn't find run number")
            if 'Test Changed On' in keys:
                date_key = 'Test Changed On'
            elif "Timestamp (UTC)" in keys:
                date_key = "Timestamp (UTC)"
            else:
                print("couldn't find timestamp")
            if "Section" in keys:
                sect_key = "Section"
            elif "Sect" in keys:
                sect_key = "Sect"
            else:
                print("couldn't find section number")
            if 'Section Half' in keys:
                half_key = 'Section Half'
            elif "A/W" in keys:
                half_key = "A/W"
            else:
                print("couldn't find half number")
            if "Text ID" in keys:
                text_id = "Text ID"
            elif "Text Id" in keys:
                text_id = "Text Id"
            else:
                print("couldn't find ID number")
            for line in file_input[1:]:
                InRec = {}
                test = 0
                recs = line.split(',')
                for k in range(len(keys)):
                    if len(recs) == len(keys):
                        InRec[keys[k]] = line.split(',')[k].strip(""" " ' """)
                if 'Exp' in list(InRec.keys()) and InRec['Exp'] != "":
                    # get rid of pesky blank lines (why is this a thing?)
                    test = 1
                if not test:
                    continue
                run_number = ""
                inst = "IODP-SRM"
                volume = '15.59'  # set default volume to this
                if 'Sample Area (cm?)' in list(InRec.keys()) and InRec['Sample Area (cm?)'] != "":
                    volume = InRec['Sample Area (cm?)']
                MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}
                expedition = InRec['Exp']
                location = InRec['Site']+InRec['Hole']
# Maintain backward compatibility for the ever-changing LIMS format (Argh!)
                while len(InRec['Core']) < 3:
                    InRec['Core'] = '0'+InRec['Core']
                # assume discrete sample
                if "Last Tray Measurment" in list(InRec.keys()) and "SHLF" not in InRec[text_id] or 'dscr' in csv_file:
                    specimen = expedition+'-'+location+'-' + \
                        InRec['Core']+InRec[core_type]+"-"+InRec[sect_key] + \
                        '-'+InRec[half_key]+'-'+str(InRec[interval_key])
                else:  # mark as continuous measurements
                    specimen = expedition+'-'+location+'-' + \
                        InRec['Core']+InRec[core_type]+"_"+InRec[sect_key] + \
                        InRec[half_key]+'-'+str(InRec[interval_key])
                sample = expedition+'-'+location + \
                    '-'+InRec['Core']+InRec[core_type]
                site = expedition+'-'+location

                if not InRec[dec_key] or not InRec[inc_key]:
                    print("No dec or inc found for specimen %s, skipping" % specimen)
                    continue

                if specimen != "" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
                    SpecRec['specimen'] = specimen
                    SpecRec['sample'] = sample
                    SpecRec['citations'] = citations
                    SpecRec['volume'] = volume
                    SpecRec['specimen_alternatives'] = InRec[text_id]
                    SpecRecs.append(SpecRec)
                if sample != "" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
                    SampRec['sample'] = sample
                    SampRec['site'] = site
                    SampRec['citations'] = citations
                    SampRec['azimuth'] = '0'
                    SampRec['dip'] = '0'
                    SampRec['core_depth'] = InRec[depth_key]
                    if comp_depth_key != '':
                        SampRec['composite_depth'] = InRec[comp_depth_key]
                        SiteRec['composite_depth'] = InRec[comp_depth_key]
                    if "SHLF" not in InRec[text_id]:
                        SampRec['method_codes'] = 'FS-C-DRILL-IODP:SP-SS-C:SO-V'
                    else:
                        SampRec['method_codes'] = 'FS-C-DRILL-IODP:SO-V'
                    SampRecs.append(SampRec)
                if site != "" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
                    SiteRec['site'] = site
                    SiteRec['location'] = location
                    SiteRec['citations'] = citations
                    SiteRec['lat'] = lat
                    SiteRec['lon'] = lon
                    SiteRecs.append(SiteRec)
                    SiteRec['core_depth'] = InRec[depth_key]
                if location != "" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
                    LocRec['location'] = location
                    LocRec['citations'] = citations
                    LocRec['expedition_name'] = expedition
                    LocRec['lat_n'] = lat
                    LocRec['lon_e'] = lon
                    LocRec['lat_s'] = lat
                    LocRec['lon_w'] = lon
                    LocRecs.append(LocRec)

                MeasRec['specimen'] = specimen
                MeasRec['software_packages'] = version_num
                MeasRec["treat_temp"] = '%8.3e' % (273)  # room temp in kelvin
                MeasRec["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
                MeasRec["treat_ac_field"] = 0
                MeasRec["treat_dc_field"] = '0'
                MeasRec["treat_dc_field_phi"] = '0'
                MeasRec["treat_dc_field_theta"] = '0'
                MeasRec["quality"] = 'g'  # assume all data are "good"
                MeasRec["standard"] = 'u'  # assume all data are "good"
                if run_number_key in list(InRec.keys()) and InRec[run_number_key] != "":
                    run_number = InRec[run_number_key]
                # date time is second line of file
                datestamp = InRec[date_key].split()
                if '/' in datestamp[0]:
                    # break into month day year
                    mmddyy = datestamp[0].split('/')
                    if len(mmddyy[0]) == 1:
                        mmddyy[0] = '0'+mmddyy[0]  # make 2 characters
                    if len(mmddyy[1]) == 1:
                        mmddyy[1] = '0'+mmddyy[1]  # make 2 characters
                    if len(mmddyy[2]) == 1:
                        mmddyy[2] = '0'+mmddyy[2]  # make 2 characters
                    if len(datestamp[1]) == 1:
                        datestamp[1] = '0'+datestamp[1]  # make 2 characters
                    hour, minute = datestamp[1].split(':')
                    if len(hour) == 1:
                        hour = '0' + hour
                    date = mmddyy[0]+':'+mmddyy[1]+":" + \
                        mmddyy[2] + ':' + hour + ":" + minute + ":00"
                    #date=mmddyy[2] + ':'+mmddyy[0]+":"+mmddyy[1] +':' + hour + ":" + minute + ":00"
                if '-' in datestamp[0]:
                    # break into month day year
                    mmddyy = datestamp[0].split('-')
                    date = mmddyy[0]+':'+mmddyy[1]+":" + \
                        mmddyy[2] + ':' + datestamp[1]+":0"
                if len(date.split(":")) > 6:
                    date = date[:-2]
                # try with month:day:year
                try:
                    utc_dt = datetime.datetime.strptime(
                        date, "%m:%d:%Y:%H:%M:%S")
                except ValueError:
                    # try with year:month:day
                    try:
                        utc_dt = datetime.datetime.strptime(
                            date, "%Y:%m:%d:%H:%M:%S")
                    except ValueError:
                        # if all else fails, assume the year is in the third position
                        # and try padding with '20'
                        new_date = pad_year(
                            date, ind=2, warn=year_warning, fname=os.path.split(f)[1])
                        utc_dt = datetime.datetime.strptime(
                            new_date, "%m:%d:%Y:%H:%M:%S")
                        # only give warning once per csv file
                        year_warning = False
                MeasRec['timestamp'] = utc_dt.strftime("%Y-%m-%dT%H:%M:%S")+"Z"
                MeasRec["method_codes"] = 'LT-NO'
                if 'Treatment Type' in list(InRec.keys()) and InRec['Treatment Type'] != "":
                    if "AF" in InRec['Treatment Type'].upper():
                        MeasRec['method_codes'] = 'LT-AF-Z'
                        inst = inst+':IODP-SRM-AF'  # measured on shipboard in-line 2G AF
                        treatment_value = float(
                            InRec[demag_key].strip('"'))*1e-3  # convert mT => T
                        # AF demag in treat mT => T
                        MeasRec["treat_ac_field"] = treatment_value
                    elif "T" in InRec['Treatment Type'].upper():
                        MeasRec['method_codes'] = 'LT-T-Z'
                        inst = inst+':IODP-TDS'  # measured on shipboard Schonstedt thermal demagnetizer
                        try:
                            treatment_value = float(
                                InRec['Treatment Value'])+273  # convert C => K
                        except KeyError:
                            try:
                                treatment_value = float(
                                    InRec["Treatment value<br> (mT or \N{DEGREE SIGN}C)"]) + 273
                            except KeyError:
                                print([k for k in InRec.keys() if 'treat' in k.lower()])
                                print("-W- Couldn't find column for Treatment Value")
                                treatment_value = ""
                        MeasRec["treat_temp"] = str(treatment_value)
                    elif 'Alternating Frequency' in InRec['Treatment Type']:
                        MeasRec['method_codes'] = 'LT-AF-Z'
                        inst = inst+':IODP-DTECH'  # measured on shipboard Dtech D2000
                        treatment_value = float(
                            InRec[demag_key])*1e-3  # convert mT => T
                        # AF demag in treat mT => T
                        MeasRec["treat_ac_field"] = treatment_value
                    elif 'Thermal' in InRec['Treatment Type']:
                        MeasRec['method_codes'] = 'LT-T-Z'
                        inst = inst+':IODP-TDS'  # measured on shipboard Schonstedt thermal demagnetizer
                        treatment_value = float(
                            InRec[demag_key])+273  # convert C => K
                        MeasRec["treat_temp"] = '%8.3e' % (treatment_value)
                elif InRec[demag_key] != "0":
                    MeasRec['method_codes'] = 'LT-AF-Z'
                    inst = inst+':IODP-SRM-AF'  # measured on shipboard in-line 2G AF
                    try:
                        treatment_value = float(
                            InRec[demag_key])*1e-3  # convert mT => T
                    except ValueError:
                        print("Couldn't determine treatment value was given treatment value of %s and demag key %s; setting to blank you will have to manually correct this (or fix it)" % (
                            InRec[demag_key], demag_key))
                        treatment_value = ''
                    # AF demag in treat mT => T
                    MeasRec["treat_ac_field"] = treatment_value
                MeasRec["standard"] = 'u'  # assume all data are "good"
                vol = float(volume)*1e-6  # convert from cc to m^3
                if run_number != "":
                    MeasRec['external_database_ids'] = {'LIMS': run_number}
                else:
                    MeasRec['external_database_ids'] = ""
                MeasRec['dir_inc'] = InRec[inc_key]
                MeasRec['dir_dec'] = InRec[dec_key]
                intens = InRec[int_key]
                try:
                    # convert intensity from A/m to Am^2 using vol
                    MeasRec['magn_moment'] = '%8.3e' % (float(intens)*vol)
                except ValueError:
                    print("couldn't find magnetic moment for specimen %s and int_key %s; leaving this field blank you'll have to fix this manually" % (
                        specimen, int_key))
                    MeasRec['magn_moment'] = ''
                MeasRec['instrument_codes'] = inst
                MeasRec['treat_step_num'] = 0
                MeasRec['dir_csd'] = '0'
                MeasRec['meas_n_orient'] = ''
                MeasRecs.append(MeasRec)
    if not file_found:
        print("No .csv files were found")
        return (False, "No .csv files were found")

    con = cb.Contribution(output_dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    #MeasSort=sorted(MeasRecs,key=lambda x: (x['specimen'], float(x['treat_ac_field'])))
    #MeasSort=sorted(MeasRecs,key=lambda x: float(x['treat_ac_field']))
    # MeasOuts=pmag.measurements_methods3(MeasSort,noave)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.write_table_to_file('specimens', custom_name=spec_file,dir_path=dir_path)
    con.write_table_to_file('samples', custom_name=samp_file,dir_path=dir_path)
    con.write_table_to_file('sites', custom_name=site_file,dir_path=dir_path)
    con.write_table_to_file('locations', custom_name=loc_file,dir_path=dir_path)
    con.write_table_to_file('measurements', custom_name=meas_file,dir_path=dir_path)

    return (True, meas_file)

### IRM_magic conversion

def irm(mag_file, output_dir_path="./", input_dir_path="./", citation="This study",
        meas_file="measurements", spec_file="specimens", samp_file="samples.txt", 
        site_file="sites.txt", loc_file="locations.txt", MPMSdc_type=0):

    """
    Convert a IRM excel data export file to MagIC file(s)

    Parameters
    ----------
    mag_file : str
        input file name
    dir_path : str
        working directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    meas_file : str
        output measurement file name, default "measurements.txt"
    spec_file : str
        output specimen file name, default "specimens.txt"
    samp_file: str
        output sample file name, default "samples.txt"
    site_file : str
        output site file name, default "sites.txt"
    loc_file : str
        output location file name, default "locations.txt"

    """
    print("start")

    f = pd.ExcelFile(mag_file)
    sequence=1
    meas=pd.DataFrame()
    meas_file_list=""
    speci_file_list=""
    for sheet_name in f.sheet_names:
        # create specimens table 
        if sheet_name == "Specimen Info":
            print("Sheet Name:",sheet_name)
            spec_info = f.parse(sheet_name=sheet_name)
            spec_info.drop(0,inplace=True)
# not needed?            specId=spec_info['Specimen_ID']
            # Set up columns in the order as they appear in the IRM 'Specimen Info' worksheet
            SpecRecs=pd.DataFrame()
            SpecRecs['specimen']=spec_info['Specimen_ID']
            SpecRecs['specimen_alternatives']=spec_info['Key']
            SpecRecs['sample']=spec_info['Sample']
            SpecRecs['analysts']=spec_info['Specimen_owner']
            SpecRecs['description']=spec_info['Specimen_description']
            SpecRecs['']=spec_info['Specimen_azimuth'] # need to check orientation parameters from IRM
            SpecRecs['']=[90-element for element in spec_info['Specimen_plunge']] # need to check orientation parameters from IRM
            SpecRecs['volume']=[element*1e-6 for element in spec_info['Specimen_volume']]
            SpecRecs['weight']=[element*1e-3 for element in spec_info['Specimen_mass[g]']]
        # Other columns in the IRM worksheet currently not used
        #    SpecRecs['']=spec_info['Expedition']
        #    SpecRecs['']=spec_info['Z_coordinate']
        #    SpecRecs['']=spec_info['Batch_ID']
        #    SpecRecs['']=spec_info['synthetic_material']
        #    SpecRecs['']=spec_info['mineral']
        #    SpecRecs['']=spec_info['Specimen_length[cm]']
        #    SpecRecs['']=spec_info['Specimen_area[cm2]']
        #    SpecRecs['igsn_parent']=spec_info['IGSN_parent']
            SpecRecs['igsn']=spec_info['IGSN']
            SpecRecs['method_codes']=['Add method codes here'] * len(spec_info.index)
            SpecRecs['citations']=[citation] * len(spec_info.index)
            df=pd.DataFrame(data=SpecRecs)
            file=open(spec_file+"_SpecInfo.txt","w")
            file.write("tab\tspecimens\n")
            file.close()
            speci_file_list=speci_file_list + spec_file +"_SpecInfo.txt "
            df.to_csv(spec_file+"_SpecInfo.txt",sep='\t',index=False,mode='a')

        #   create and write out samples table
            temp_dict={}
            temp_dict['sample']=spec_info['Sample']
            temp_dict['site']=spec_info['Site']
            temp_dict['citations']=SpecRecs['citations']
            temp_dict['method_codes']=SpecRecs['method_codes']
            samp_info=pd.DataFrame(data=temp_dict)
            samp_info.drop_duplicates(inplace=True)
            file=open(samp_file,"w")
            file.write("tab\tsamples\n")
            file.close()
            samp_info.to_csv(samp_file,sep='\t',index=False,mode='a')

        #   create and write out sites table

            del temp_dict['sample']
            temp_dict['location']=spec_info['Locality']
            temp_dict['geologic_classes']=[''] * len(spec_info.index)
            temp_dict['geologic_types']=[''] * len(spec_info.index)
            temp_dict['lithologies']=[''] * len(spec_info.index)
            temp_dict['lat']=[''] * len(spec_info.index)
            temp_dict['lon']=[''] * len(spec_info.index)
            temp_dict['age']=[''] * len(spec_info.index)
            temp_dict['age_sigma']=[''] * len(spec_info.index)
            temp_dict['age_unit']=[''] * len(spec_info.index)
            temp_dict['age_low']=[''] * len(spec_info.index)
            temp_dict['age_high']=[''] * len(spec_info.index)
            temp_dict['citations']=SpecRecs['citations']
            temp_dict['method_codes']=SpecRecs['method_codes']
            site_info=pd.DataFrame(data=temp_dict)
            site_info.drop_duplicates(inplace=True)
            file=open(site_file,"w")
            file.write("tab\tsites\n")
            file.close()
            site_info.to_csv(site_file,sep='\t',index=False,mode='a')

        #   create and write out locations table

            del temp_dict['site']
            del temp_dict['geologic_types']
            del temp_dict['lat']
            del temp_dict['lon']
            temp_dict['location_type']=[''] * len(spec_info.index)
            temp_dict['lat_n']=[''] * len(spec_info.index)
            temp_dict['lat_s']=[''] * len(spec_info.index)
            temp_dict['lon_w']=[''] * len(spec_info.index)
            temp_dict['lon_e']=[''] * len(spec_info.index)
            loc_info=pd.DataFrame(data=temp_dict)
            loc_info.drop_duplicates(inplace=True)
            file=open(loc_file,"w")
            file.write("tab\tlocations\n")
            file.close()
            loc_info.to_csv(loc_file,sep='\t',index=False,mode='a')

        # Create additional specimens table 
        if sheet_name == "hysteresis properties":
            print("Sheet Name:",sheet_name)
            info = f.parse(sheet_name=sheet_name)
            info.drop(0,inplace=True)
            SpecRecs=pd.DataFrame()
            SpecRecs['specimen']=info['specimen']
            SpecRecs['sample']=info['specimen']
            # Set up columns in the order as they appear in the IRM 'hysteresis properties' worksheet
            SpecRecs['hyst_ms_mass']=info['Ms [Am/kg]']
            SpecRecs['hyst_mr_mass']=info['Mr [Am/kg]']
            SpecRecs['hyst_bc']=[element*1e-3 for element in info['Bc [mT]']]
            SpecRecs['hyst_bcr']=[element*1e-3 for element in info['Bcr [mT]']]
            SpecRecs['hyst_xhf']=info['Xhf [m3/kg]']
            SpecRecs['meas_temp']=info['T [K]']
            SpecRecs['hyst_bc_offset']=info['loop offset [Am/kg]']
            SpecRecs['instrument_codes']=info['Instrument']
            SpecRecs['description']=info['loop_comment']
            SpecRecs['method_codes']=['LP-X'] * len(info.index)
            SpecRecs['citations']=[citation] * len(info.index)
            df=pd.DataFrame(data=SpecRecs)
            file=open(spec_file+"_hyster_prop.txt","w")
            file.write("tab\tspecimens\n")
            file.close()
            speci_file_list=speci_file_list + spec_file +"_hyster_prop.txt "
            df.to_csv(spec_file+"_hyster_prop.txt",sep='\t',index=False,mode='a')


        if sheet_name == "measurement_history":
            print("Sheet Name:", sheet_name)
            # This table could be used to add date/time to the measurements, but not straight forward
            # Skip for now

        if sheet_name == "Magnon_suscep":
            temp_dict=pd.DataFrame()
            print("Sheet Name:", sheet_name)
            info = f.parse(sheet_name=sheet_name)
            info.drop(0,inplace=True) #remove blank line under headers

            prev_speci="" 
            meas_list=[]
            for row in range(len(info.index)):
                if info.iloc[row,0] != prev_speci:
                    meas_num=1
                    prev_speci=info.iloc[row,0]
                meas_str=str(meas_num)
                meas_list.append(meas_str)
                meas_num+=1
            measdf=pd.DataFrame(data=meas_list,columns=['measurement'])
            info['measlist']=measdf
            
            temp_dict['sequence']= range(sequence,sequence+len(info.index))
            sequence=sequence+len(info.index)+1
            measdf.drop([0],inplace=True) # remove line to match with the Excel DataFrame

            temp_dict['measurement']= info['Specimen'] + "_" + info['Instrument'] + "_" + info['measlist'] 
            temp_dict['experiment']= info['Specimen'] + "_" + info['Instrument']
            temp_dict['specimen']= info['Specimen']
            temp_dict['susc_chi_mass']= info['X [m3/kg]']
            temp_dict['treat_temp']= info['T [K]']
            temp_dict['meas_freq']= info['f [Hz]']
            temp_dict['meas_field_dc']= [element*1e-3 for element in info['Hac [A/m]']]
            temp_dict['quality']='g'
            temp_dict['standard']= 'u'
            temp_dict['method_codes']='LP-X-F'
            temp_dict['instrument_codes']= info['Instrument']
            temp_dict['citations']= citation
            temp_dict['description']= "X` [m3/kg]=" + info["X` [m3/kg]"].astype({"X` [m3/kg]": str}) + ", " +  info['Comment']
#            temp_dict['description']= "X` [m3/kg]= " + str(info["X` [m3/kg]"]) + ", " + info['Comment']
            temp_dict['treat_step_num']= info['measlist']
            temp_dict.drop([0],inplace=True) # remove wierd extra top line NEED TO FIND BETTER FIX 
            meas_info=pd.DataFrame(data=temp_dict)
            file=open(meas_file + "_Magnon.txt","w")
            file.write("tab\tmeasurements\n")
            file.close()
            meas_info.to_csv(meas_file + "_Magnon.txt",sep='\t',index=False,mode="a")
            meas_file_list= meas_file_list + meas_file + "_Magnon.txt " 

        # add to measurements table

        if "hysteresis measurements" in sheet_name:
            temp_dict=pd.DataFrame()
            print("Sheet Name:", sheet_name)
            info = f.parse(sheet_name=sheet_name)
            columns=info.columns
            temperatures=info.iloc[0]
            decs=info.iloc[1]
            incs=info.iloc[2]
            speci_name=columns[1]
            Bapp_col_name="specimen"
            M_BKcor_name='Unnamed: 2'
            Mf_BKcor_name='Unnamed: 3'
            treat_temp=temperatures[1]
            info.drop([0,1,2,3,4],inplace=True) # after getting info in header remove them
            temp_dict['treat_dc_field']= [element*1e-3 for element in info[Bapp_col_name]]  
            temp_dict['magn_mass']= info[M_BKcor_name]  
            temp_dict.dropna(inplace=True)
            temp_dict['description']="Mf_BKcor_name=" + info[Mf_BKcor_name].astype({Mf_BKcor_name: str})
            temp_dict['treat_temp']= treat_temp  
            num_rows=len(temp_dict.index)
            meas_num=[]
            for i in range(1,num_rows+1):
                meas_num.append(str(i))
            temp_dict["meas_num"]=meas_num
            temp_dict['sequence']= range(sequence,sequence+num_rows)
            temp_dict['measurement']= speci_name + "_hysteresis_" + temp_dict['meas_num'] 
            temp_dict['experiment']=  speci_name + "_hysteresis" 
            temp_dict['specimen']= speci_name
            temp_dict['quality']='g'
            temp_dict['standard']= 'u'
            temp_dict['method_codes']='LP-HYS-T'
#            temp_dict['instrument_codes']= ""  # Could get this from measurement history table
            temp_dict['citations']= citation
            sequence=sequence+num_rows+1
            temp_dict['treat_step_num']=temp_dict['meas_num']
            temp_dict.drop(columns=['meas_num'], inplace=True)
            meas_info=pd.DataFrame(data=temp_dict)
            file_sheet_name=sheet_name.replace(' ','_')
            file=open(meas_file + '_' + file_sheet_name + '.txt',"w")
            file.write("tab\tmeasurements\n")
            file.close()
            meas_info.to_csv(meas_file + '_' + file_sheet_name + '.txt',sep='\t',index=False,mode='a')
            meas_file_list= meas_file_list + meas_file + '_' + file_sheet_name + '.txt ' 

            for column_num in range(6,len(columns)-1,6):
                temp_dict=pd.DataFrame()
                speci_name=columns[column_num+1]
                Bapp_col_name="specimen." + str(int(column_num/6))
                M_BKcor_name='Unnamed: ' + str(int(column_num+3))
                Mf_BKcor_name='Unnamed: ' + str(int(column_num+4))
                treat_temp=temperatures[column_num+1]
                temp_dict['treat_dc_field']= info[Bapp_col_name]  
                temp_dict['magn_mass']= info[M_BKcor_name]  
                temp_dict.dropna(inplace=True)
                temp_dict['description']="Mf_BKcor_name=" + info[Mf_BKcor_name].astype({Mf_BKcor_name: str})
                temp_dict['treat_temp']= treat_temp  
                num_rows=len(temp_dict.index)
                meas_num=[]
                for i in range(1,num_rows+1):
                    meas_num.append(str(i))
                temp_dict["meas_num"]=meas_num
                temp_dict['sequence']= range(sequence,sequence+num_rows)
                temp_dict['measurement']= speci_name + "_hysteresis_" + temp_dict['meas_num'] 
                temp_dict['experiment']=  speci_name + "_hysteresis" 
                temp_dict['specimen']= speci_name
                temp_dict['quality']='g'
                temp_dict['standard']= 'u'
                temp_dict['method_codes']='LP-HYS-T'
#                temp_dict['instrument_codes']= ""  # Could get this from measurement history table
                temp_dict['citations']= citation
                sequence=sequence+num_rows+1
                temp_dict['treat_step_num']=temp_dict['meas_num']
                temp_dict.drop(columns=['meas_num'], inplace=True)
                meas_info=pd.DataFrame(data=temp_dict)
                meas_info.to_csv(meas_file + '_hysteresis.txt',sep='\t',index=False,mode='a',header=False)
           
        if "VSM backfield measurements" in sheet_name:
            temp_dict=pd.DataFrame()
            print("Sheet Name:", sheet_name)
            info = f.parse(sheet_name=sheet_name)
            columns=info.columns
            temperatures=info.iloc[0]
            decs=info.iloc[1]
            incs=info.iloc[2]
            speci_name=columns[1]
            Bapp_col="specimen"
            M_col=speci_name
            treat_temp=temperatures[1]
            info.drop([0,1,2,3,4],inplace=True) # after getting info in header remove them
            temp_dict['treat_dc_field']= [element*1e-3 for element in info[Bapp_col]]  
            temp_dict['magn_mass']= info[M_col]  
            temp_dict.dropna(inplace=True)
            temp_dict['treat_temp']= treat_temp  
            num_rows=len(temp_dict.index)
            meas_num=[]
            for i in range(1,num_rows+1):
                meas_num.append(str(i))
            temp_dict["meas_num"]=meas_num
            temp_dict['sequence']= range(sequence,sequence+num_rows)
            temp_dict['measurement']= speci_name + "_VSM_backfield_" + temp_dict['meas_num'] 
            temp_dict['experiment']=  speci_name + "VSM_backfield" 
            temp_dict['specimen']= speci_name
            temp_dict['quality']='g'
            temp_dict['standard']= 'u'
            temp_dict['method_codes']='LP-BCR-BF'
#            temp_dict['instrument_codes']= ""  # Could get this from measurement history table
            temp_dict['citations']= citation
            sequence=sequence+num_rows+1
            temp_dict['treat_step_num']=temp_dict['meas_num']
            temp_dict.drop(columns=['meas_num'], inplace=True)
            meas_info=pd.DataFrame(data=temp_dict)
            file_sheet_name=sheet_name.replace(' ','_')
            file=open(meas_file + '_' + file_sheet_name + '.txt',"w")
            file.write("tab\tmeasurements\n")
            file.close()
            meas_info.to_csv(meas_file + '_' + file_sheet_name + '.txt',sep='\t',index=False,mode='a')
            meas_file_list= meas_file_list + meas_file + '_' + file_sheet_name + '.txt ' 
            for column_num in range(3,len(columns)-1,3):
                temp_dict=pd.DataFrame()
                speci_name=columns[column_num+1]
                Bapp_col="specimen"
                M_col=speci_name
                treat_temp=temperatures[1]
                temp_dict['treat_dc_field']= [element*1e-3 for element in info[Bapp_col]]
                temp_dict['magn_mass']= info[M_col]
                temp_dict.dropna(inplace=True)
                temp_dict['treat_temp']= treat_temp
                num_rows=len(temp_dict.index)
                meas_num=[]
                for i in range(1,num_rows+1):
                    meas_num.append(str(i))
                temp_dict["meas_num"]=meas_num
                temp_dict['sequence']= range(sequence,sequence+num_rows)
                temp_dict['measurement']= speci_name + "_VSM_backfield_" + temp_dict['meas_num']
                temp_dict['experiment']=  speci_name + "VSM_backfield"
                temp_dict['specimen']= speci_name
                temp_dict['quality']='g'
                temp_dict['standard']= 'u'
                temp_dict['method_codes']='LP-BCR-BF'
#                temp_dict['instrument_codes']= ""  # Could get this from measurement history table
                temp_dict['citations']= citation
                sequence=sequence+num_rows+1
                temp_dict['treat_step_num']=temp_dict['meas_num']
                temp_dict.drop(columns=['meas_num'], inplace=True)
                meas_info=pd.DataFrame(data=temp_dict)
                meas_info.to_csv(meas_file + '_' + file_sheet_name + '.txt',sep='\t',index=False,mode='a')

        if sheet_name == "high_T susceptibility":
            temp_dict=pd.DataFrame()
            print("Sheet Name:", sheet_name)
            info = f.parse(sheet_name=sheet_name)
            info.drop(0,inplace=True) #remove units line under headers
            info.drop(1,inplace=True) #remove blank line under headers
            columns=info.columns
            speci_name=columns[1]
            T_col_name="Specimen"
            k_col_name=speci_name
            temp_dict['treat_temp']= info[T_col_name]  
            temp_dict['susc_chi_mass']= info[k_col_name]  
            temp_dict.dropna(inplace=True)
            num_rows=len(temp_dict.index)
            meas_num=[]
            for i in range(1,num_rows+1):
                meas_num.append(str(i))
            temp_dict["meas_num"]=meas_num
            temp_dict['sequence']= range(sequence,sequence+num_rows)
            temp_dict['measurement']= speci_name + "_high_T_k_" + temp_dict['meas_num'] 
            temp_dict['experiment']=  speci_name + "_high_T_k" 
            temp_dict['specimen']= speci_name
            temp_dict['quality']='g'
            temp_dict['standard']= 'u'
            temp_dict['method_codes']='LP-X-T'
            temp_dict['instrument_codes']= "IRM Kappabridge" 
            temp_dict['citations']= citation
            sequence=sequence+num_rows+1
            temp_dict['treat_step_num']=temp_dict['meas_num']
            temp_dict.drop(columns=['meas_num'], inplace=True)
            meas_info=pd.DataFrame(data=temp_dict)
            file=open(meas_file + "_high_T.txt","w")
            file.write("tab\tmeasurements\n")
            file.close()
            meas_info.to_csv(meas_file + "_high_T.txt",sep='\t',index=False,mode='a')
            meas_file_list= meas_file_list + meas_file + '_high_T.txt ' 

            for column_num in range(3,len(columns)-1,3):
                temp_dict=pd.DataFrame()
                speci_name=columns[column_num+1]
                T_col_name="Specimen." + str(int(column_num/3))
                k_col_name=speci_name
                
                temp_dict['treat_temp']= info[T_col_name]  
                temp_dict['susc_chi_mass']= info[k_col_name]  
                temp_dict.dropna(inplace=True)
                num_rows=len(temp_dict.index)
                meas_num=[]
                for i in range(1,num_rows+1):
                    meas_num.append(str(i))
                temp_dict["meas_num"]=meas_num
                temp_dict['sequence']= range(sequence,sequence+num_rows)
                temp_dict['measurement']= speci_name + "_high_T_k_" + temp_dict['meas_num']
                #  * num_rows + [str(range(sequence,sequence+num_rows))] 
                temp_dict['experiment']=  speci_name + "_high_T_k" 
                temp_dict['specimen']= speci_name
                temp_dict['quality']='g'
                temp_dict['standard']= 'u'
                temp_dict['method_codes']='LP-X-T'
                temp_dict['instrument_codes']= "IRM Kappabridge" 
                temp_dict['citations']= citation
                sequence=sequence+num_rows+1
                temp_dict['treat_step_num']=temp_dict['meas_num']
                temp_dict.drop(columns=['meas_num'], inplace=True)

                meas_info=pd.DataFrame(data=temp_dict)
                meas_info.to_csv(meas_file + "_high_T.txt",sep='\t',index=False, mode='a', header=False)

        if sheet_name == "remanence measurements":
            print("Sheet Name:", sheet_name)
            temp_dict=pd.DataFrame()
            info = f.parse(sheet_name=sheet_name)
            columns=info.columns
            prev_speci=""
            meas_num=1
            meas_list=[]
            for row in range(len(info.index)):
                if info.iloc[row,0] != prev_speci:
                    meas_num=1
                    prev_speci=info.iloc[row,0]
                meas_str=str(meas_num)
                meas_list.append(meas_str)
                meas_num+=1
            measdf=pd.DataFrame(data=meas_list,columns=['measurement'])
            info['measlist']=measdf
            info.drop([0],inplace=True) # remove blank line
            measdf.drop([0],inplace=True) # remove line to match with the Excel DataFrame
            temp_dict['measurement']=info["specimen"] + "_remanence_" + info['measlist']
            temp_dict['experiment']=  info["specimen"] + "_remanence" 
            temp_dict['specimen']= info["specimen"]
            temp_dict['magn_x']= info['Mx [Am2]']  
            temp_dict['magn_y']= info['My [Am2]']  
            temp_dict['magn_z']= info['Mz [Am2]']  
            temp_dict['magn_moment']= info['Mtot [Am2]']  
            temp_dict['dir_dec']= info['Dec [deg]']  
            temp_dict['dir_inc']= info['Inc [deg]']  
            temp_dict['magn_mass']= info['Jarm [Am2/kg]']  
            temp_dict['treat_ac_field']= [element*1e-3 for element in info['AF [mT]']]
            temp_dict['treat_temp']=[element+273.15 for element in info['T [C]']]
            temp_dict['treat_dc_field']= info['Hdc [mT]']  
            temp_dict['treat_dc_field_phi']= [90-element for element in info['Hdc inc [deg]']] # These need to be checked by the IRM  
            temp_dict['treat_dc_field_theta']= [90-element for element in info['Hdc inc [deg]']] # These need to be checked by the IRM
            temp_dict['description']='Description='
            temp_dict['treat_step_num']=info['measlist']
            #,+info['Description']
            #+'date='+info['date']+', time='+info['time']+', series='+info['series']+', position[cm]='+info['position[cm]']+', Drift_ratio='+info['Drift_ratio']+' run#='+info['run#']+', Mode=', info['Mode']+', Type=',+info['Type']
            temp_dict['treat_temp']= info['Meas_T [K]']
            num_rows=len(temp_dict.index)
            temp_dict['sequence']= range(sequence,sequence+num_rows)
            temp_dict['quality']='g'
            temp_dict['standard']= 'u'
            temp_dict['method_codes']='place method codes here'
#            temp_dict['instrument_codes']= ""  # Could get this from measurement history table
            temp_dict['citations']= citation
            sequence=sequence+num_rows+1
            meas_info=pd.DataFrame(data=temp_dict)
            file=open(meas_file + '_remanence.txt',"w")
            file.write("tab\tmeasurements\n")
            file.close()
            meas_info.to_csv(meas_file + '_remanence.txt',sep='\t',index=False,mode='a')
            meas_file_list= meas_file_list + meas_file + '_remanence.txt ' 
            
        if "MPMSdc measurements" in sheet_name:
            print("Sheet Name:", sheet_name)

            # create magic table header
            file_sheet_name=sheet_name.replace(' ','_')
            file=open(meas_file + '_' + file_sheet_name + '.txt',"w")
            file.write("tab\tmeasurements\n")
            file.close()

            meas_file_list= meas_file_list + meas_file + "_" + file_sheet_name +".txt "  

            info=pd.DataFrame()
            temp_dict=pd.DataFrame()
            info = f.parse(sheet_name=sheet_name)
            columns=info.columns
            
            if MPMSdc_type == '1':  # needed for different IRM file formats. Format 1 is from Courtny Sprain's data
                speci_name=columns[1]
                T_name="specimen"
                Bapp_name=speci_name
                M_name='Unnamed: 2'
                reg_fit='Unnamed: 3'
                timestamp_name='Unnamed: 4'
                info.drop([0,1,2,3,4],inplace=True) # remove rows before data
            else: # this format is the default and the current IRM download 2021-07-07. From Leonard Ohenhen
                speci_name=columns[0]
                T_name=speci_name
                Bapp_name=speci_name+".1"
                M_name=speci_name+".2"
                reg_fit=speci_name+".3"
                timestamp_name=speci_name+".4"
                info.drop([0,1,2,3],inplace=True) # remove rows before data

            temp_dict['meas_temp']= info[T_name]  
            temp_dict['meas_field_dc']= info[Bapp_name]  
            temp_dict['magn_mass']= info[M_name]
            temp_dict['description']="reg fit=" + info[reg_fit].astype({reg_fit: str})
            temp_dict['timestamp']= info[timestamp_name]  
            num_rows=len(temp_dict.index)
            meas_num=[]
            for i in range(1,num_rows+1):
                meas_num.append(str(i))
            temp_dict['meas_num']=meas_num
            temp_dict['sequence']= range(sequence,sequence+num_rows)
            temp_dict['measurement']= speci_name + "_MPMSdc" + temp_dict['meas_num'] 
            temp_dict['experiment']=  speci_name + "_MPMSdc" 
            temp_dict['specimen']= speci_name
            temp_dict['quality']='g'
            temp_dict['standard']= 'u'
            temp_dict['method_codes']='LP-MRT'
#            temp_dict['instrument_codes']= ""  # Could get this from measurement history table
            temp_dict['citations']= citation
            temp_dict.dropna(inplace=True)
            sequence=sequence+num_rows+1
            temp_dict['treat_step_num']=temp_dict['meas_num']
#            temp_dict.drop(columns=['meas_num'], inplace=True)
            temp_dict.to_csv(meas_file + "_" + file_sheet_name + ".txt",sep='\t',index=False,mode='a')

            if MPMSdc_type == '1':  # needed for different IRM file formats. Format 1 is from Courtny Sprain data
                for column_num in range(6,len(columns)-1,6):
                    speci_name=columns[column_num+1]
                    T_name="specimen." + str(int(column_num/6))
                    Bapp_name=speci_name
                    M_name='Unnamed: ' + str(int(column_num+2))
                    reg_fit='Unnamed: ' + str(int(column_num+3))
                    timestamp_name='Unnamed: ' + str(int(column_num+4))

                    temp_dict['meas_temp']= info[T_name]
                    temp_dict['meas_field_dc']= info[Bapp_name]
                    temp_dict['magn_mass']= info[M_name]
                    temp_dict['description']="reg fit=" + info[reg_fit].astype({reg_fit: str})
                    temp_dict['timestamp']= info[timestamp_name]
                    num_rows=len(temp_dict.index)
                    meas_num=[]
                    for i in range(1,num_rows+1):
                        meas_num.append(str(i))
                    temp_dict["meas_num"]=meas_num
                    temp_dict['sequence']= range(sequence,sequence+num_rows)
                    temp_dict['measurement']= speci_name + "_MPMSdc" + temp_dict['meas_num']
                    temp_dict['experiment']=  speci_name + "_MPMSdc"
                    temp_dict['specimen']= speci_name
                    temp_dict['quality']='g'
                    temp_dict['standard']= 'u'
                    temp_dict['method_codes']='LP-MRT'
#                    temp_dict['instrument_codes']= ""  # Could get this from measurement history table
                    temp_dict['citations']= citation
                    temp_dict.dropna(inplace=True)
                    sequence=sequence+num_rows+1
                    temp_dict['treat_step_num']=temp_dict['meas_num']
                    meas_info=pd.DataFrame(data=temp_dict)
                    meas_info.to_csv(meas_file + "_" + file_sheet_name + ".txt",sep='\t',index=False,mode='a',header=False)

            else: # this format is the default and the current IRM download 2021-07-07. From Leonard Ohenhen
                column_num=0
                prev_speci_name=speci_name
                speci_name_num=0
                while column_num < len(columns):
                    speci_name=columns[column_num]
                    if "Unnamed" in speci_name: # skip extra blank column between specimen names
                        column_num+=1
                        speci_name=columns[column_num]
                    split=speci_name.split(".")
                    speci_name=split[0]
                    if speci_name != prev_speci_name:
                        speci_name_num=0
                    if speci_name_num == 0:
                        T_name=speci_name
                    else:
                        T_name=speci_name+"."+str(speci_name_num*5)
                    Bapp_name=speci_name+"."+str(speci_name_num*5+1)
                    M_name=speci_name+"."+str(speci_name_num*5+2)
                    reg_fit=speci_name+"."+str(speci_name_num*5+3)
                    timestamp_name=speci_name+"."+str(speci_name_num*5+4)
                    speci_name_num += 1
                    column_num += 6

                    temp_dict['meas_temp']= info[T_name]
                    temp_dict['meas_field_dc']= info[Bapp_name]
                    temp_dict['magn_mass']= info[M_name]
                    temp_dict['description']="reg fit=" + info[reg_fit].astype({reg_fit: str})
                    temp_dict['timestamp']= info[timestamp_name]
                    num_rows=len(temp_dict.index)
                    meas_num=[]
                    for i in range(1,num_rows+1):
                        meas_num.append(str(i))
                    temp_dict["meas_num"]=meas_num
                    temp_dict['sequence']= range(sequence,sequence+num_rows)
                    temp_dict['measurement']= speci_name + "_MPMSdc" + temp_dict['meas_num']
                    temp_dict['experiment']=  speci_name + "_MPMSdc"
                    temp_dict['specimen']= speci_name
                    temp_dict['quality']='g'
                    temp_dict['standard']= 'u'
                    temp_dict['method_codes']='LP-MRT'
#                    temp_dict['instrument_codes']= ""  # Could get this from measurement history table
                    temp_dict['citations']= citation
                    temp_dict.dropna(inplace=True)
                    sequence=sequence+num_rows+1
                    temp_dict['treat_step_num']=temp_dict['meas_num']
                    meas_info=pd.DataFrame(data=temp_dict)
                    meas_info.to_csv(meas_file + "_" + file_sheet_name + ".txt",sep='\t',index=False,mode='a',header=False)


    #combine specimen and measurement tables
    # do this at the end - may not be needed           dfSpec.fillna('', inplace=True) # replace "NaN"s with blanks 
    print("speci_file_list=",speci_file_list)
    os.system("combine_magic.py -F specimens.txt -f " + speci_file_list)
    print("meas_file_list=",meas_file_list)
    os.system("combine_magic.py -F measurements.txt -f " + meas_file_list)
    print("end")
    return(True, meas_file)


### JR6_jr6_magic conversion

def jr6_jr6(mag_file, dir_path=".", input_dir_path="",
            meas_file="measurements.txt", spec_file="specimens.txt",
            samp_file="samples.txt", site_file="sites.txt", loc_file="locations.txt",
            specnum=1, samp_con='1', location='unknown', lat='', lon='',
            noave=False, meth_code="LP-NO", volume=12, JR=False, user=""):

    """
    Convert JR6 .jr6 files to MagIC file(s)

    Parameters
    ----------
    mag_file : str
        input file name
    dir_path : str
        working directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    meas_file : str
        output measurement file name, default "measurements.txt"
    spec_file : str
        output specimen file name, default "specimens.txt"
    samp_file: str
        output sample file name, default "samples.txt"
    site_file : str
        output site file name, default "sites.txt"
    loc_file : str
        output location file name, default "locations.txt"
    specnum : int
        number of characters to designate a specimen, default 0
    samp_con : str
        sample/site naming convention, default '1', see info below
    location : str
        location name, default "unknown"
    lat : float
        latitude, default ""
    lon : float
        longitude, default ""
    noave : bool
       do not average duplicate measurements, default False (so by default, DO average)
    meth_code : str
        colon-delimited method codes to describe experiment
        default:  "LP-NO"
        if AF demag, meth_code='LP-DIR-AF'
        if thermal demag, meth_code='LP-DIR-T'
    volume : float
        volume in ccs, default 12
    JR : bool
        IODP samples were measured on the JOIDES RESOLUTION, default False
    user : str
        user name, default ""

    Returns
    ---------
    Tuple : (True or False indicating if conversion was successful, meas_file name written)

    Info
    --------
    Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name same as sample
        [6] site is entered under a separate column -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY


    """

    version_num = pmag.get_version()
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    if specnum:
        specnum = - int(specnum)
    else:
        specnum=0
    samp_con = str(samp_con)
    volume = float(volume) * 1e-6
    # need to add these
    meas_file = pmag.resolve_file_name(meas_file, output_dir_path)
    spec_file = pmag.resolve_file_name(spec_file, output_dir_path)
    samp_file = pmag.resolve_file_name(samp_file, output_dir_path)
    site_file = pmag.resolve_file_name(site_file, output_dir_path)
    loc_file = pmag.resolve_file_name(loc_file, output_dir_path)
    mag_file = pmag.resolve_file_name(mag_file, input_dir_path)

    if JR:
        if meth_code == "LP-NO":
            meth_code = ""
        meth_code = meth_code+":FS-C-DRILL-IODP:SP-SS-C:SO-V"
        meth_code = meth_code.strip(":")
        samp_con = '5'

    # format variables
    tmp_file = mag_file.split(os.extsep)[0]+os.extsep+'tmp'
    mag_file = pmag.resolve_file_name(mag_file, input_dir_path)
    if samp_con.startswith("4"):
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "4"
    elif samp_con.startswith("7"):
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "7"
    else:
        Z = 1

    # parse data
    # fix .jr6 file so that there are spaces between all the columns.
    pre_data = open(mag_file, 'r')
    tmp_data = open(tmp_file, 'w')
    if samp_con != '2':
        fixed_data = pre_data.read().replace('-', ' -')
    else:
        fixed_data = ""
        for line in pre_data.readlines():
            entries = line.split()
            if len(entries) < 2:
                continue
            fixed_line = entries[0] + ' ' + reduce(
                lambda x, y: x+' '+y, [x.replace('-', ' -') for x in entries[1:]])
            fixed_data += fixed_line+os.linesep
    tmp_data.write(fixed_data)
    tmp_data.close()
    pre_data.close()

    if not JR:
        column_names = ['specimen', 'step', 'x', 'y', 'z', 'expon', 'azimuth', 'dip', 'bed_dip_direction',
                        'bed_dip', 'bed_dip_dir2', 'bed_dip2', 'param1', 'param2', 'param3', 'param4', 'dir_csd']
    else:  # measured on the Joides Resolution JR6
        column_names = ['specimen', 'step', 'negz', 'y', 'x', 'expon', 'azimuth', 'dip', 'bed_dip_direction',
                        'bed_dip', 'bed_dip_dir2', 'bed_dip2', 'param1', 'param2', 'param3', 'param4', 'dir_csd']
    data = pd.read_csv(tmp_file, delim_whitespace=True,
                       names=column_names, index_col=False)
    if isinstance(data['x'][0], str):
        column_names = ['specimen', 'step', 'step_unit', 'x', 'y', 'z', 'expon', 'azimuth', 'dip', 'bed_dip_direction',
                        'bed_dip', 'bed_dip_dir2', 'bed_dip2', 'param1', 'param2', 'param3', 'param4', 'dir_csd']
        data = pd.read_csv(tmp_file, delim_whitespace=True,
                           names=column_names, index_col=False)
    if JR:
        data['z'] = -data['negz']
        
    cart = np.array([data['x'], data['y'], data['z']]).transpose()
    dir_dat = pmag.cart2dir(cart).transpose()
    data['dir_dec'] = dir_dat[0]
    data['dir_inc'] = dir_dat[1]
    # the data are in A/m - this converts to Am^2
    data['magn_moment'] = dir_dat[2]*(10.0**data['expon'])*volume
    data['magn_volume'] = dir_dat[2] * \
        (10.0**data['expon'])  # A/m  - data in A/m

    # put data into magic tables
    MagRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    for rowNum, row in data.iterrows():
        MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}
        specimen = row['specimen']
        if specnum:
            sample = specimen[:specnum]
        else:
            sample = specimen
        site = pmag.parse_site(sample, samp_con, Z)
        #azimuth=float(row['azimuth'])
        #dip=float(row['dip'])
        if specimen != "" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
            SpecRec['specimen'] = specimen
            SpecRec['sample'] = sample
            SpecRec["citations"] = "This study"
            SpecRec["analysts"] = user
            SpecRec['volume'] = volume
            SpecRecs.append(SpecRec)
        if sample != "" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
            SampRec['sample'] = sample
            SampRec['site'] = site
            SampRec["citations"] = "This study"
            SampRec["analysts"] = user
            if row['param3']==3:
                row['azimuth']=(row['azimuth']+90)%360
            if row['param3']==9:
                row['azimuth']=(row['azimuth']-90)%360
            if row['param3']==12:
                row['azimuth']=(row['azimuth']-180)%360
            if row['param2']==90:
                row['dip']=90-row['dip']
            SampRec['azimuth'] = row['azimuth']
            SampRec['dip'] = row['dip']
            SampRec['bed_dip_direction'] = row['bed_dip_direction']
            SampRec['bed_dip'] = row['bed_dip']
            SampRec['method_codes'] = meth_code
            SampRecs.append(SampRec)
        if site != "" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
            SiteRec['site'] = site
            SiteRec['location'] = location
            SiteRec["citations"] = "This study"
            SiteRec["analysts"] = user
            SiteRec['lat'] = lat
            SiteRec['lon'] = lon
            SiteRecs.append(SiteRec)
        if location != "" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
            LocRec['location'] = location
            LocRec["citations"] = "This study"
            LocRec["analysts"] = user
            LocRec['lat_n'] = lat
            LocRec['lon_e'] = lon
            LocRec['lat_s'] = lat
            LocRec['lon_w'] = lon
            LocRecs.append(LocRec)
        MeasRec["citations"] = "This study"
        MeasRec["analysts"] = user
        MeasRec["specimen"] = specimen
        MeasRec['software_packages'] = version_num
        MeasRec["treat_temp"] = '%8.3e' % (273)  # room temp in kelvin
        MeasRec["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
        MeasRec["quality"] = 'g'
        MeasRec["standard"] = 'u'
        MeasRec["treat_step_num"] = 0
        MeasRec["treat_ac_field"] = '0'
        if row['step'] == 'NRM' or row['step']=='0':
            meas_type = "LT-NO"
        elif 'step_unit' in row and row['step_unit'] == 'C' or meth_code=='LP-DIR-T':
            meas_type = "LT-T-Z"
            treat = float(row['step'])
            MeasRec["treat_temp"] = '%8.3e' % (treat+273.)  # temp in kelvin
        elif 'AD' in str(row['step']):
            meas_type = "LT-AF-Z"
            treat = float(row['step'][2:])
            MeasRec["treat_ac_field"] = '%8.3e' % (
                treat*1e-3)  # convert from mT to tesla
        elif str(row['step'])[0] == 'A':
            meas_type = "LT-AF-Z"
            treat = float(row['step'][1:])
            MeasRec["treat_ac_field"] = '%8.3e' % (
                treat*1e-3)  # convert from mT to tesla
        elif str(row['step'])[0] == 'TD':
            meas_type = "LT-T-Z"
            treat = float(row['step'][2:])
            MeasRec["treat_temp"] = '%8.3e' % (treat+273.)  # temp in kelvin
        elif str(row['step'])[0] == 'T':
            meas_type = "LT-T-Z"
            treat = float(row['step'][1:])
            MeasRec["treat_temp"] = '%8.3e' % (treat+273.)  # temp in kelvin
        elif meth_code=='LP-DIR-AF':
            meas_type = "LT-AF-Z"
            treat = float(row['step'])
            MeasRec["treat_ac_field"] = '%8.3e' % (
                treat*1e-3)  # convert from mT to tesla
        else:  # need to add IRM, and ARM options
            print("measurement type unknown", row['step'])
            return False, "measurement type unknown"
        MeasRec["magn_moment"] = str(row['magn_moment'])
        MeasRec["magn_volume"] = str(row['magn_volume'])
        if row['param1']==3: 
            row['dir_dec']=(row['dir_dec']-90)%360
        if row['param1']==6: 
            row['dir_dec']=(row['dir_dec']-180)%360
        if row['param1']==9: 
            row['dir_dec']=(row['dir_dec']+90)%360
        MeasRec["dir_dec"] = str(row['dir_dec'])
        MeasRec["dir_inc"] = str(row['dir_inc'])
        MeasRec['method_codes'] = meas_type
        MagRecs.append(MeasRec)

    con = cb.Contribution(output_dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts = pmag.measurements_methods3(MagRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.tables['specimens'].write_magic_file(custom_name=spec_file)
    con.tables['samples'].write_magic_file(custom_name=samp_file)
    con.tables['sites'].write_magic_file(custom_name=site_file)
    con.tables['locations'].write_magic_file(custom_name=loc_file)
    con.tables['measurements'].write_magic_file(custom_name=meas_file)

    try:
        os.remove(tmp_file)
    except (OSError, IOError) as e:
        print("couldn't remove temperary fixed JR6 file %s" % tmp_file)

    return True, meas_file



### JR6_txt_magic conversion

def jr6_txt(mag_file, dir_path=".", input_dir_path="",
            meas_file="measurements.txt", spec_file="specimens.txt",
            samp_file="samples.txt", site_file="sites.txt", loc_file="locations.txt",
            user="", specnum=1, samp_con='1', location='unknown', lat='', lon='',
            noave=False, volume=12, timezone="UTC", meth_code="LP-NO"):

    """
    Converts JR6 .txt format files to MagIC measurements format files.

    Parameters
    ----------
    mag_file : str
        input file name
    dir_path : str
        working directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    meas_file : str
        output measurement file name, default "measurements.txt"
    spec_file : str
        output specimen file name, default "specimens.txt"
    samp_file: str
        output sample file name, default "samples.txt"
    site_file : str
        output site file name, default "sites.txt"
    loc_file : str
        output location file name, default "locations.txt"
    user : str
        user name, default ""
    specnum : int
        number of characters to designate a specimen, default 0
    samp_con : str
        sample/site naming convention, default '1', see info below
    location : str
        location name, default "unknown"
    lat : float
        latitude, default ""
    lon : float
        longitude, default ""
    noave : bool
       do not average duplicate measurements, default False (so by default, DO average)
    volume : float
        volume in ccs, default 12
    timezone : timezone of date/time string in comment string, default UTC
    meth_code : str
        default "LP-NO"

    Returns
    ---------
    Tuple : (True or False indicating if conversion was successful, meas_file name written)

    """

    version_num = pmag.get_version()
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    mag_file = pmag.resolve_file_name(mag_file, input_dir_path)
    input_dir_path = os.path.split(mag_file)[0]
    specnum = - int(specnum)
    samp_con = str(samp_con)
    volume = float(volume) * 1e-6

    # format variables
    mag_file = pmag.resolve_file_name(mag_file, input_dir_path)
    if samp_con.startswith("4"):
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "4"
    elif samp_con.startswith("7"):
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "7"
    else:
        Z = 1

    # create data holders
    MeasRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []

    data = pmag.open_file(mag_file)
    # remove garbage/blank lines
    data = [i for i in data if len(i) >= 5]
    if not len(data):
        print('No data')
        return

    n = 0
    end = False
    # loop through records
    while not end:
        first_line = data[n].split()
        sampleName = first_line[0]
        demagLevel = first_line[2]
        date = first_line[3] + ":0:0:0"
        n += 2
        third_line = data[n].split()
        if not third_line[0].startswith('SPEC.ANGLES'):
            print('third line of a block should start with SPEC.ANGLES')
            print(third_line)
            return
        specimenAngleDec = third_line[1]
        specimenAngleInc = third_line[2]
        n += 4
        while not data[n].startswith('MEAN'):
            n += 1
        mean_line = data[n]
        Mx = mean_line[1]
        My = mean_line[2]
        Mz = mean_line[3]
        n += 1
        precision_line = data[n].split()
        if not precision_line[0].startswith('Modulus'):
            print('precision line should start with "Modulus"')
            return
        splitExp = precision_line[2].split('A')
        intensityVolStr = precision_line[1] + splitExp[0]
        intensityVol = float(intensityVolStr)
        # check and see if Prec is too big and messes with the parcing.
        precisionStr = ''
        if len(precision_line) == 6:  # normal line
            precisionStr = precision_line[5][0:-1]
        else:
            precisionStr = precision_line[4][0:-1]

        precisionPer = float(precisionStr)
        precision = intensityVol * precisionPer/100

        while not data[n].startswith('SPEC.'):
            n += 1
        specimen_line = data[n].split()
        specimenDec = specimen_line[2]
        specimenInc = specimen_line[3]
        n += 1
        geographic_line = data[n]
        if not geographic_line.startswith('GEOGR'):
            geographic_dec = ''
            geographic_inc = ''
        else:
            geographic_line = geographic_line.split()
            geographicDec = geographic_line[1]
            geographicInc = geographic_line[2]
        # Add data to various MagIC data tables.
        specimen = sampleName
        if specnum != 0:
            sample = specimen[:specnum]
        else:
            sample = specimen
        site = pmag.parse_site(sample, samp_con, Z)

        MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}

        if specimen != "" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
            SpecRec['specimen'] = specimen
            SpecRec['sample'] = sample
            SpecRec["citations"] = "This study"
            SpecRec["analysts"] = user
            SpecRec['volume'] = volume
            SpecRecs.append(SpecRec)
        if sample != "" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
            SampRec['sample'] = sample
            SampRec['site'] = site
            SampRec["citations"] = "This study"
            SampRec["analysts"] = user
            SampRec['azimuth'] = specimenAngleDec
            # convert to magic orientation
            sample_dip = str(float(specimenAngleInc)-90.0)
            SampRec['dip'] = sample_dip
            SampRec['method_codes'] = meth_code
            SampRecs.append(SampRec)
        if site != "" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
            SiteRec['site'] = site
            SiteRec['location'] = location
            SiteRec["citations"] = "This study"
            SiteRec["analysts"] = user
            SiteRec['lat'] = lat
            SiteRec['lon'] = lon
            SiteRecs.append(SiteRec)
        if location != "" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
            LocRec['location'] = location
            LocRec["citations"] = "This study"
            LocRec["analysts"] = user
            LocRec['lat_n'] = lat
            LocRec['lon_e'] = lon
            LocRec['lat_s'] = lat
            LocRec['lon_w'] = lon
            LocRecs.append(LocRec)

        local = pytz.timezone(timezone)
        naive = datetime.datetime.strptime(date, "%m-%d-%Y:%H:%M:%S")
        local_dt = local.localize(naive, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        timestamp = utc_dt.strftime("%Y-%m-%dT%H:%M:%S")+"Z"
        MeasRec["specimen"] = specimen
        MeasRec["timestamp"] = timestamp
        MeasRec['description'] = ''
        MeasRec["citations"] = "This study"
        MeasRec['software_packages'] = version_num
        MeasRec["treat_temp"] = '%8.3e' % (273)  # room temp in kelvin
        MeasRec["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
        MeasRec["quality"] = 'g'
        MeasRec["standard"] = 'u'
        MeasRec["treat_step_num"] = 0
        MeasRec["treat_ac_field"] = '0'
        if demagLevel == 'NRM':
            meas_type = "LT-NO"
        elif demagLevel[0] == 'A':
            if demagLevel[:2] == 'AD':
                treat = float(demagLevel[2:])
            else:
                treat = float(demagLevel[1:])
            meas_type = "LT-AF-Z"
            MeasRec["treat_ac_field"] = '%8.3e' % (
                treat*1e-3)  # convert from mT to tesla
        elif demagLevel[0] == 'T':
            meas_type = "LT-T-Z"
            treat = float(demagLevel[1:])
            MeasRec["treat_temp"] = '%8.3e' % (treat+273.)  # temp in kelvin
        else:
            print("measurement type unknown", demagLevel)
            return False, "measurement type unknown"

        MeasRec["magn_moment"] = str(intensityVol*volume)  # Am^2
        MeasRec["magn_volume"] = intensityVolStr  # A/m
        MeasRec["dir_dec"] = specimenDec
        MeasRec["dir_inc"] = specimenInc
        MeasRec['method_codes'] = meas_type
        MeasRecs.append(MeasRec)

        # ignore all the rest of the special characters. Some data files not consistently formatted.
        n += 1
        while ((len(data[n]) <= 5 and data[n] != '') or data[n].startswith('----')):
            n += 1
            if n >= len(data):
                break
        if n >= len(data):
            # we're done!
            end = True

        # end of data while loop

    con = cb.Contribution(output_dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.tables['specimens'].write_magic_file(custom_name=spec_file,dir_path=dir_path)
    con.tables['samples'].write_magic_file(custom_name=samp_file,dir_path=dir_path)
    con.tables['sites'].write_magic_file(custom_name=site_file,dir_path=dir_path)
    con.tables['locations'].write_magic_file(custom_name=loc_file,dir_path=dir_path)
    con.tables['measurements'].write_magic_file(custom_name=meas_file,dir_path=dir_path)

    return True, meas_file


def k15(k15file, dir_path='.', input_dir_path='',
        meas_file='measurements.txt', aniso_outfile='specimens.txt',
        samp_file="samples.txt", result_file ="rmag_anisotropy.txt",
        specnum=0, sample_naming_con='1', location="unknown",
        data_model_num=3):
    """
    converts .k15 format data to MagIC  format.
    assumes Jelinek Kappabridge measurement scheme.

    Parameters
    ----------
    k15file : str
        input file name
    dir_path : str
        output file directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    meas_file : str
        output measurement file name, default "measurements.txt"
    aniso_outfile : str
        output specimen file name, default "specimens.txt"
    samp_file: str
        output sample file name, default "samples.txt"
    aniso_results_file : str
        output result file name, default "rmag_results.txt", data model 2 only
    specnum : int
        number of characters to designate a specimen, default 0
    samp_con : str
        sample/site naming convention, default '1', see info below
    location : str
        location name, default "unknown"
    data_model_num : int
        MagIC data model [2, 3], default 3

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful, samp_file name written)


    Info
    --------
      Infile format:
          name [az,pl,strike,dip], followed by
          3 rows of 5 measurements for each specimen

       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
            [4-Z] XXXXYYY:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.

    """
    #
    # initialize some variables
    #
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    version_num = pmag.get_version()
    syn = 0
    itilt, igeo, linecnt, key = 0, 0, 0, ""
    first_save = 1
    k15 = []
    citation = 'This study'

    data_model_num = int(float(data_model_num))

    # set column names for MagIC 3
    spec_name_col = 'specimen'  #
    samp_name_col = 'sample'   #
    site_name_col = 'site'   #
    loc_name_col = 'location' #
    citation_col = 'citations'
    method_col = 'method_codes'
    site_description_col = 'description'
    expedition_col = 'expedition_name'
    instrument_col = 'instrument_codes'
    experiment_col = 'experiments'
    analyst_col = 'analysts'
    quality_col = 'quality'
    aniso_quality_col = 'result_quality'
    meas_standard_col = 'standard'
    meas_description_col = 'description'
    aniso_type_col = 'aniso_type'
    aniso_unit_col = 'aniso_s_unit'
    aniso_n_col = 'aniso_s_n_measurements'
    azimuth_col = 'azimuth'
    spec_volume_col = 'volume'
    samp_dip_col = 'dip'
    bed_dip_col = 'bed_dip'
    bed_dip_direction_col = 'bed_dip_direction'
    chi_vol_col = 'susc_chi_volume'
    aniso_sigma_col = 'aniso_s_sigma'
    aniso_unit_col = 'aniso_s_unit'
    aniso_tilt_corr_col = 'aniso_tilt_correction'
    meas_table_name = 'measurements'
    spec_table_name = 'specimens'
    samp_table_name = 'samples'
    site_table_name = 'sites'
    meas_name_col = 'measurement'
    meas_time_col = 'timestamp'
    meas_ac_col = 'meas_field_ac'
    meas_temp_col = "meas_temp"
    #
    software_col = 'software_packages'
    description_col = 'description' # sites.description
    treat_temp_col = 'treat_temp'
    meas_orient_phi_col = "meas_orient_phi"
    meas_orient_theta_col = "meas_orient_theta"
    aniso_mean_col = 'aniso_s_mean'
    result_description_col = "description"

    # set defaults correctly for MagIC 2
    if data_model_num == 2:
        if meas_file == 'measurements.txt':
            meas_file = 'magic_measurements.txt'
        if samp_file == 'samples.txt':
            samp_file = 'er_samples.txt'
        if aniso_outfile == 'specimens.txt':
            aniso_outfile = 'rmag_anisotropy.txt'

    # set column names for MagIC 2
    if data_model_num == 2:
        spec_name_col = 'er_specimen_name'
        samp_name_col = 'er_sample_name'
        site_name_col = 'er_site_name'
        loc_name_col = 'er_location_name'
        citation_col = 'er_citation_names'
        method_col = 'magic_method_codes'
        site_description_col = 'site_description'
        expedition_col = 'er_expedition_name'
        instrument_col = 'magic_instrument_codes'
        experiment_col = 'magic_experiment_names'
        analyst_col = 'er_analyst_mail_names'
        quality_col = 'measurement_flag'
        aniso_quality_col = 'anisotropy_flag'
        meas_standard_col = 'measurement_standard'
        meas_description_col = 'measurement_description'
        aniso_type_col = 'anisotropy_type'
        aniso_unit_col = 'anisotropy_unit'
        aniso_n_col = 'anisotropy_n'
        azimuth_col = 'sample_azimuth'
        spec_volume_col = 'specimen_volume'
        samp_dip_col = 'sample_dip'
        bed_dip_col = 'sample_bed_dip'
        bed_dip_direction_col = 'sample_bed_dip_direction'
        chi_vol_col = 'measurement_chi_volume'
        aniso_sigma_col = 'anisotropy_sigma'
        aniso_unit_col = 'anisotropy_unit'
        aniso_tilt_corr_col = 'anisotropy_tilt_correction'
        meas_table_name = 'magic_measurements'
        spec_table_name = 'er_specimens'
        samp_table_name = 'er_samples'
        site_table_name = 'er_sites'
        meas_name_col = 'measurement_number'
        meas_time_col = 'measurement_date'
        meas_ac_col = 'measurement_lab_field_ac'
        meas_temp_col = "measurement_temp"
        #
        software_col = 'magic_software_packages'
        description_col = 'rmag_result_name'
        treat_temp_col = 'treatment_temp'
        meas_temp_col = "measurement_temp"
        meas_orient_phi_col = "measurement_orient_phi"
        meas_orient_theta_col = "measurement_orient_theta"
        aniso_mean_col = 'anisotropy_mean'
        result_description_col = "result_description"


# pick off stuff from command line
    Z = ""
    if "4" in sample_naming_con:
        if "-" not in sample_naming_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = sample_naming_con.split("-")[1]
            sample_naming_con = "4"
    if sample_naming_con == '6':
        Samps, filetype = pmag.magic_read(
            os.path.join(input_dir_path, samp_table_name + ".txt"))
    samp_file = pmag.resolve_file_name(samp_file, output_dir_path)
    meas_file = pmag.resolve_file_name(meas_file, output_dir_path)
    aniso_outfile = pmag.resolve_file_name(aniso_outfile, output_dir_path)
    result_file = pmag.resolve_file_name(result_file, output_dir_path)
    k15file = pmag.resolve_file_name(k15file, input_dir_path)
    if not os.path.exists(k15file):
        print(k15file)
        return False, "You must provide a valid k15 format file"
    try:
        SampRecs, filetype = pmag.magic_read(
            samp_file)  # append new records to existing
        samplist = []
        for samp in SampRecs:
            if samp[samp_name_col] not in samplist:
                samplist.append(samp[samp_name_col])
    except IOError:
        SampRecs = []
    # measurement directions for Jelinek 1977 protocol:
    Decs = [315, 225, 180, 135, 45, 90, 270, 270, 270, 90, 180, 180, 0, 0, 0]
    Incs = [0, 0, 0, 0, 0, -45, -45, 0, 45, 45, 45, -45, -90, -45, 45]
    # some defaults to read in  .k15 file format
    # list of measurements and default number of characters for specimen ID
# some magic default definitions
    #
    # read in data
    with open(k15file, 'r') as finput:
        lines = finput.readlines()
    MeasRecs, SpecRecs, AnisRecs, ResRecs = [], [], [], []
    # read in data
    MeasRec, SpecRec, SampRec, SiteRec, AnisRec, ResRec = {}, {}, {}, {}, {}, {}
    for line in lines:
        linecnt += 1
        rec = line.split()
        if linecnt == 1:
            MeasRec[method_col] = ""
            SpecRec[method_col] = ""
            SampRec[method_col] = ""
            AnisRec[method_col] = ""
            SiteRec[method_col] = ""
            ResRec[method_col] = ""
            MeasRec[software_col] = version_num
            SpecRec[software_col] = version_num
            SampRec[software_col] = version_num
            AnisRec[software_col] = version_num
            SiteRec[software_col] = version_num
            ResRec[software_col] = version_num
            MeasRec[method_col] = "LP-X"
            MeasRec[quality_col] = "g"
            MeasRec[meas_standard_col] = "u"
            MeasRec[citation_col] = "This study"
            SpecRec[citation_col] = "This study"
            SampRec[citation_col] = "This study"
            AnisRec[citation_col] = "This study"
            ResRec[citation_col] = "This study"
            MeasRec[spec_name_col] = rec[0]
            MeasRec[experiment_col] = rec[0] + ":LP-AN-MS"
            AnisRec[experiment_col] = rec[0] + ":AMS"
            ResRec[experiment_col] = rec[0] + ":AMS"
            SpecRec[spec_name_col] = rec[0]
            AnisRec[spec_name_col] = rec[0]
            SampRec[spec_name_col] = rec[0]
            if data_model_num == 2:
                ResRec[description_col] = rec[0]
            if data_model_num == 3:
                ResRec[spec_name_col] = rec[0]
            specnum = int(specnum)
            if specnum != 0:
                MeasRec[samp_name_col] = rec[0][:-specnum]
            if specnum == 0:
                MeasRec[samp_name_col] = rec[0]
            SampRec[samp_name_col] = MeasRec[samp_name_col]
            SpecRec[samp_name_col] = MeasRec[samp_name_col]
            AnisRec[samp_name_col] = MeasRec[samp_name_col]
            if data_model_num == 3:
                ResRec[samp_name_col] = MeasRec[samp_name_col]
            else:
                ResRec[samp_name_col + "s"] = MeasRec[samp_name_col]
            if sample_naming_con == "6":
                for samp in Samps:
                    if samp[samp_name_col] == AnisRec[samp_name_col]:
                        sitename = samp[site_name_col]
                        location = samp[loc_name_col]
            elif sample_naming_con != "":
                sitename = pmag.parse_site(
                    AnisRec[samp_name_col], sample_naming_con, Z)
            MeasRec[site_name_col] = sitename
            MeasRec[loc_name_col] = location
            SampRec[site_name_col] = MeasRec[site_name_col]
            SpecRec[site_name_col] = MeasRec[site_name_col]
            AnisRec[site_name_col] = MeasRec[site_name_col]
            ResRec[loc_name_col] = location
            ResRec[site_name_col] = MeasRec[site_name_col]
            if data_model_num == 2:
                ResRec[site_name_col + "s"] = MeasRec[site_name_col]
            SampRec[loc_name_col] = MeasRec[loc_name_col]
            SpecRec[loc_name_col] = MeasRec[loc_name_col]
            AnisRec[loc_name_col] = MeasRec[loc_name_col]
            if data_model_num == 2 :
                ResRec[loc_name_col + "s"] = MeasRec[loc_name_col]
            if len(rec) >= 3:
                SampRec[azimuth_col], SampRec[samp_dip_col] = rec[1], rec[2]
                az, pl, igeo = float(rec[1]), float(rec[2]), 1
            if len(rec) == 5:
                SampRec[bed_dip_direction_col], SampRec[bed_dip_col] = '%7.1f' % (
                    90. + float(rec[3])), (rec[4])
                bed_az, bed_dip, itilt, igeo = 90. + \
                    float(rec[3]), float(rec[4]), 1, 1
        else:
            for i in range(5):
                # assume measurements in micro SI
                k15.append(1e-6 * float(rec[i]))
            if linecnt == 4:
                sbar, sigma, bulk = pmag.dok15_s(k15)
                hpars = pmag.dohext(9, sigma, sbar)
                MeasRec[treat_temp_col] = '%8.3e' % (
                    273)  # room temp in kelvin
                MeasRec[meas_temp_col] = '%8.3e' % (
                    273)  # room temp in kelvin
                for i in range(15):
                    NewMeas = copy.deepcopy(MeasRec)
                    NewMeas[meas_orient_phi_col] = '%7.1f' % (Decs[i])
                    NewMeas[meas_orient_theta_col] = '%7.1f' % (Incs[i])
                    NewMeas[chi_vol_col] = '%12.10f' % (k15[i])
                    NewMeas[meas_name_col] = '%i' % (i + 1)
                    if data_model_num == 2:
                        NewMeas["magic_experiment_name"] = rec[0] + ":LP-AN-MS"
                    else:
                        NewMeas["experiment"] = rec[0] + ":LP-AN-MS"
                    MeasRecs.append(NewMeas)
                if SampRec[samp_name_col] not in samplist:
                    SampRecs.append(SampRec)
                    samplist.append(SampRec[samp_name_col])
                SpecRecs.append(SpecRec)
                AnisRec[aniso_type_col] = "AMS"
                ResRec[aniso_type_col] = "AMS"
                s1_val = '{:12.10f}'.format(sbar[0])
                s2_val = '{:12.10f}'.format(sbar[1])
                s3_val = '{:12.10f}'.format(sbar[2])
                s4_val = '{:12.10f}'.format(sbar[3])
                s5_val = '{:12.10f}'.format(sbar[4])
                s6_val = '{:12.10f}'.format(sbar[5])
                # MAgIC 2
                if data_model_num == 2:
                    AnisRec["anisotropy_s1"] = s1_val
                    AnisRec["anisotropy_s2"] = s2_val
                    AnisRec["anisotropy_s3"] = s3_val
                    AnisRec["anisotropy_s4"] = s4_val
                    AnisRec["anisotropy_s5"] = s5_val
                    AnisRec["anisotropy_s6"] = s6_val
                # MagIC 3
                else:
                    vals = [s1_val, s2_val, s3_val, s4_val, s5_val, s6_val]
                    AnisRec['aniso_s'] = ":".join([str(v).strip() for v in vals])
                AnisRec[aniso_mean_col] = '%12.10f' % (bulk)
                AnisRec[aniso_sigma_col] = '%12.10f' % (sigma)
                AnisRec[aniso_mean_col] = '{:12.10f}'.format(bulk)
                AnisRec[aniso_sigma_col] = '{:12.10f}'.format(sigma)
                AnisRec[aniso_unit_col] = 'SI'
                AnisRec[aniso_n_col] = '15'
                AnisRec[aniso_tilt_corr_col] = '-1'
                AnisRec[method_col] = 'LP-X:AE-H:LP-AN-MS'
                AnisRecs.append(AnisRec)
                ResRec[method_col] = 'LP-X:AE-H:LP-AN-MS'
                ResRec[aniso_tilt_corr_col] = '-1'

                if data_model_num == 3:
                    aniso_v1 = ':'.join([str(i) for i in (hpars['t1'], hpars['v1_dec'], hpars['v1_inc'],  hpars['v2_dec'], hpars['v2_inc'], hpars['e12'], hpars['v3_dec'], hpars['v3_inc'], hpars['e13'])])
                    aniso_v2 = ':'.join([str(i) for i in (hpars['t2'], hpars['v2_dec'], hpars['v2_inc'], hpars['v1_dec'], hpars['v1_inc'], hpars['e12'], hpars['v3_dec'], hpars['v3_inc'], hpars['e23'])])
                    aniso_v3 = ':'.join([str(i) for i in (hpars['t3'], hpars['v3_dec'], hpars['v3_inc'], hpars['v1_dec'], hpars['v1_inc'], hpars['e13'], hpars['v2_dec'], hpars['v2_inc'], hpars['e23'])])
                    ResRec['aniso_v1'] = aniso_v1
                    ResRec['aniso_v2'] = aniso_v2
                    ResRec['aniso_v3'] = aniso_v3
                else: # data model 2
                    ResRec["anisotropy_t1"] = '%12.10f' % (hpars['t1'])
                    ResRec["anisotropy_t2"] = '%12.10f' % (hpars['t2'])
                    ResRec["anisotropy_t3"] = '%12.10f' % (hpars['t3'])
                    ResRec["anisotropy_fest"] = '%12.10f' % (hpars['F'])
                    ResRec["anisotropy_ftest12"] = '%12.10f' % (hpars['F12'])
                    ResRec["anisotropy_ftest23"] = '%12.10f' % (hpars['F23'])
                    ResRec["anisotropy_v1_dec"] = '%7.1f' % (hpars['v1_dec'])
                    ResRec["anisotropy_v2_dec"] = '%7.1f' % (hpars['v2_dec'])
                    ResRec["anisotropy_v3_dec"] = '%7.1f' % (hpars['v3_dec'])
                    ResRec["anisotropy_v1_inc"] = '%7.1f' % (hpars['v1_inc'])
                    ResRec["anisotropy_v2_inc"] = '%7.1f' % (hpars['v2_inc'])
                    ResRec["anisotropy_v3_inc"] = '%7.1f' % (hpars['v3_inc'])
                    ResRec['anisotropy_v1_eta_dec'] = ResRec['anisotropy_v2_dec']
                    ResRec['anisotropy_v1_eta_inc'] = ResRec['anisotropy_v2_inc']
                    ResRec['anisotropy_v1_zeta_dec'] = ResRec['anisotropy_v3_dec']
                    ResRec['anisotropy_v1_zeta_inc'] = ResRec['anisotropy_v3_inc']
                    ResRec['anisotropy_v2_eta_dec'] = ResRec['anisotropy_v1_dec']
                    ResRec['anisotropy_v2_eta_inc'] = ResRec['anisotropy_v1_inc']
                    ResRec['anisotropy_v2_zeta_dec'] = ResRec['anisotropy_v3_dec']
                    ResRec['anisotropy_v2_zeta_inc'] = ResRec['anisotropy_v3_inc']
                    ResRec['anisotropy_v3_eta_dec'] = ResRec['anisotropy_v1_dec']
                    ResRec['anisotropy_v3_eta_inc'] = ResRec['anisotropy_v1_inc']
                    ResRec['anisotropy_v3_zeta_dec'] = ResRec['anisotropy_v2_dec']
                    ResRec['anisotropy_v3_zeta_inc'] = ResRec['anisotropy_v2_inc']
                    ResRec["anisotropy_v1_eta_semi_angle"] = '%7.1f' % (
                        hpars['e12'])
                    ResRec["anisotropy_v1_zeta_semi_angle"] = '%7.1f' % (
                        hpars['e13'])
                    ResRec["anisotropy_v2_eta_semi_angle"] = '%7.1f' % (
                        hpars['e12'])
                    ResRec["anisotropy_v2_zeta_semi_angle"] = '%7.1f' % (
                        hpars['e23'])
                    ResRec["anisotropy_v3_eta_semi_angle"] = '%7.1f' % (
                        hpars['e13'])
                    ResRec["anisotropy_v3_zeta_semi_angle"] = '%7.1f' % (
                        hpars['e23'])
                ResRec[result_description_col] = 'Critical F: ' + hpars["F_crit"] + ';Critical F12/F13: ' + hpars["F12_crit"]
                #
                ResRecs.append(ResRec)
                if igeo == 1:
                    sbarg = pmag.dosgeo(sbar, az, pl)
                    hparsg = pmag.dohext(9, sigma, sbarg)
                    AnisRecG = copy.copy(AnisRec)
                    ResRecG = copy.copy(ResRec)
                    if data_model_num == 3:
                        AnisRecG["aniso_s"] = ":".join('{:12.10f}'.format(i) for i in sbarg)
                    if data_model_num == 2:
                        AnisRecG["anisotropy_s1"] = '%12.10f' % (sbarg[0])
                        AnisRecG["anisotropy_s2"] = '%12.10f' % (sbarg[1])
                        AnisRecG["anisotropy_s3"] = '%12.10f' % (sbarg[2])
                        AnisRecG["anisotropy_s4"] = '%12.10f' % (sbarg[3])
                        AnisRecG["anisotropy_s5"] = '%12.10f' % (sbarg[4])
                        AnisRecG["anisotropy_s6"] = '%12.10f' % (sbarg[5])

                    AnisRecG[aniso_tilt_corr_col] = '0'
                    ResRecG[aniso_tilt_corr_col] = '0'

                    if data_model_num == 3:
                        aniso_v1 = ':'.join([str(i) for i in (hparsg['t1'], hparsg['v1_dec'], hparsg['v1_inc'],  hparsg['v2_dec'], hparsg['v2_inc'], hparsg['e12'], hparsg['v3_dec'], hparsg['v3_inc'], hparsg['e13'])])
                        aniso_v2 = ':'.join([str(i) for i in (hparsg['t2'], hparsg['v2_dec'], hparsg['v2_inc'], hparsg['v1_dec'], hparsg['v1_inc'], hparsg['e12'], hparsg['v3_dec'], hparsg['v3_inc'], hparsg['e23'])])
                        aniso_v3 = ':'.join([str(i) for i in (hparsg['t3'], hparsg['v3_dec'], hparsg['v3_inc'], hparsg['v1_dec'], hparsg['v1_inc'], hparsg['e13'], hparsg['v2_dec'], hparsg['v2_inc'], hparsg['e23'])])
                        ResRecG['aniso_v1'] = aniso_v1
                        ResRecG['aniso_v2'] = aniso_v2
                        ResRecG['aniso_v3'] = aniso_v3
                    #
                    if data_model_num == 2:
                        ResRecG["anisotropy_v1_dec"] = '%7.1f' % (hparsg['v1_dec'])
                        ResRecG["anisotropy_v2_dec"] = '%7.1f' % (hparsg['v2_dec'])
                        ResRecG["anisotropy_v3_dec"] = '%7.1f' % (hparsg['v3_dec'])
                        ResRecG["anisotropy_v1_inc"] = '%7.1f' % (hparsg['v1_inc'])
                        ResRecG["anisotropy_v2_inc"] = '%7.1f' % (hparsg['v2_inc'])
                        ResRecG["anisotropy_v3_inc"] = '%7.1f' % (hparsg['v3_inc'])
                        ResRecG['anisotropy_v1_eta_dec'] = ResRecG['anisotropy_v2_dec']
                        ResRecG['anisotropy_v1_eta_inc'] = ResRecG['anisotropy_v2_inc']
                        ResRecG['anisotropy_v1_zeta_dec'] = ResRecG['anisotropy_v3_dec']
                        ResRecG['anisotropy_v1_zeta_inc'] = ResRecG['anisotropy_v3_inc']
                        ResRecG['anisotropy_v2_eta_dec'] = ResRecG['anisotropy_v1_dec']
                        ResRecG['anisotropy_v2_eta_inc'] = ResRecG['anisotropy_v1_inc']
                        ResRecG['anisotropy_v2_zeta_dec'] = ResRecG['anisotropy_v3_dec']
                        ResRecG['anisotropy_v2_zeta_inc'] = ResRecG['anisotropy_v3_inc']
                        ResRecG['anisotropy_v3_eta_dec'] = ResRecG['anisotropy_v1_dec']
                        ResRecG['anisotropy_v3_eta_inc'] = ResRecG['anisotropy_v1_inc']
                        ResRecG['anisotropy_v3_zeta_dec'] = ResRecG['anisotropy_v2_dec']
                        ResRecG['anisotropy_v3_zeta_inc'] = ResRecG['anisotropy_v2_inc']
                    #
                    ResRecG[result_description_col] = 'Critical F: ' + \
                        hpars["F_crit"] + ';Critical F12/F13: ' + \
                        hpars["F12_crit"]
                    ResRecs.append(ResRecG)
                    AnisRecs.append(AnisRecG)
                if itilt == 1:
                    sbart = pmag.dostilt(sbarg, bed_az, bed_dip)
                    hparst = pmag.dohext(9, sigma, sbart)
                    AnisRecT = copy.copy(AnisRec)
                    ResRecT = copy.copy(ResRec)
                    if data_model_num == 3:
                        aniso_v1 = ':'.join([str(i) for i in (hparst['t1'], hparst['v1_dec'], hparst['v1_inc'],  hparst['v2_dec'], hparst['v2_inc'], hparst['e12'], hparst['v3_dec'], hparst['v3_inc'], hparst['e13'])])
                        aniso_v2 = ':'.join([str(i) for i in (hparst['t2'], hparst['v2_dec'], hparst['v2_inc'], hparst['v1_dec'], hparst['v1_inc'], hparst['e12'], hparst['v3_dec'], hparst['v3_inc'], hparst['e23'])])
                        aniso_v3 = ':'.join([str(i) for i in (hparst['t3'], hparst['v3_dec'], hparst['v3_inc'], hparst['v1_dec'], hparst['v1_inc'], hparst['e13'], hparst['v2_dec'], hparst['v2_inc'], hparst['e23'])])
                        ResRecT['aniso_v1'] = aniso_v1
                        ResRecT['aniso_v2'] = aniso_v2
                        ResRecT['aniso_v3'] = aniso_v3
                    #
                    if data_model_num == 2:
                        AnisRecT["anisotropy_s1"] = '%12.10f' % (sbart[0])
                        AnisRecT["anisotropy_s2"] = '%12.10f' % (sbart[1])
                        AnisRecT["anisotropy_s3"] = '%12.10f' % (sbart[2])
                        AnisRecT["anisotropy_s4"] = '%12.10f' % (sbart[3])
                        AnisRecT["anisotropy_s5"] = '%12.10f' % (sbart[4])
                        AnisRecT["anisotropy_s6"] = '%12.10f' % (sbart[5])
                        AnisRecT["anisotropy_tilt_correction"] = '100'
                        ResRecT["anisotropy_v1_dec"] = '%7.1f' % (hparst['v1_dec'])
                        ResRecT["anisotropy_v2_dec"] = '%7.1f' % (hparst['v2_dec'])
                        ResRecT["anisotropy_v3_dec"] = '%7.1f' % (hparst['v3_dec'])
                        ResRecT["anisotropy_v1_inc"] = '%7.1f' % (hparst['v1_inc'])
                        ResRecT["anisotropy_v2_inc"] = '%7.1f' % (hparst['v2_inc'])
                        ResRecT["anisotropy_v3_inc"] = '%7.1f' % (hparst['v3_inc'])
                        ResRecT['anisotropy_v1_eta_dec'] = ResRecT['anisotropy_v2_dec']
                        ResRecT['anisotropy_v1_eta_inc'] = ResRecT['anisotropy_v2_inc']
                        ResRecT['anisotropy_v1_zeta_dec'] = ResRecT['anisotropy_v3_dec']
                        ResRecT['anisotropy_v1_zeta_inc'] = ResRecT['anisotropy_v3_inc']
                        ResRecT['anisotropy_v2_eta_dec'] = ResRecT['anisotropy_v1_dec']
                        ResRecT['anisotropy_v2_eta_inc'] = ResRecT['anisotropy_v1_inc']
                        ResRecT['anisotropy_v2_zeta_dec'] = ResRecT['anisotropy_v3_dec']
                        ResRecT['anisotropy_v2_zeta_inc'] = ResRecT['anisotropy_v3_inc']
                        ResRecT['anisotropy_v3_eta_dec'] = ResRecT['anisotropy_v1_dec']
                        ResRecT['anisotropy_v3_eta_inc'] = ResRecT['anisotropy_v1_inc']
                        ResRecT['anisotropy_v3_zeta_dec'] = ResRecT['anisotropy_v2_dec']
                        ResRecT['anisotropy_v3_zeta_inc'] = ResRecT['anisotropy_v2_inc']
                    #
                    ResRecT[aniso_tilt_corr_col] = '100'
                    ResRecT[result_description_col] = 'Critical F: ' + \
                        hparst["F_crit"] + ';Critical F12/F13: ' + \
                        hparst["F12_crit"]
                    ResRecs.append(ResRecT)
                    AnisRecs.append(AnisRecT)
                k15, linecnt = [], 0
                MeasRec, SpecRec, SampRec, SiteRec, AnisRec = {}, {}, {}, {}, {}

    # samples
    pmag.magic_write(samp_file, SampRecs, samp_table_name)
    # specimens / rmag_anisotropy / rmag_results
    if data_model_num == 3:
        AnisRecs.extend(ResRecs)
        SpecRecs = AnisRecs.copy()
        SpecRecs, keys = pmag.fillkeys(SpecRecs)
        pmag.magic_write(aniso_outfile, SpecRecs, 'specimens')
        flist = [meas_file, aniso_outfile, samp_file]
    else:
        pmag.magic_write(aniso_outfile, AnisRecs, 'rmag_anisotropy')  # add to specimens?
        pmag.magic_write(result_file, ResRecs, 'rmag_results') # added to specimens (NOT sites)
        flist = [meas_file, samp_file, aniso_outfile, result_file]
    # measurements
    pmag.magic_write(meas_file, MeasRecs, meas_table_name)

    print("Data saved to: " + ", ".join(flist))
    return True, meas_file


### kly4s_magic conversion

def kly4s(infile, specnum=0, locname="unknown", inst='SIO-KLY4S',
          samp_con="1", or_con='3', user='', measfile='measurements.txt',
          aniso_outfile='rmag_anisotropy.txt', samp_infile='', spec_infile='',
          spec_outfile='specimens.txt', azdip_infile='', dir_path='.',
          input_dir_path='', data_model_num=3, samp_outfile='samples.txt',
          site_outfile='sites.txt'):
    """

    converts files generated by SIO kly4S labview program to MagIC formatted

    Parameters
    ----------
    infile :  str
        input file name
    specnum : int
        number of characters to designate a specimen, default 0
    locname : str
        location name, default "unknown"
    samp_con : str
        sample/site naming convention, default '1', see info below
    or_con : number
        orientation convention, default '3', see info below
    user : str
        user name, default ""
    measfile : str
        output measurement file name, default "measurements.txt"
    aniso_outfile : str
        output anisotropy file name, default "rmag_anisotropy.txt", data model 2 only
    samp_infile : str
        existing sample infile (not required), default ""
    spec_infile : str
        existing site infile (not required), default ""
    spec_outfile : str
        output specimen file name, default "specimens.txt"
    azdip_infile : str
        AZDIP file with orientations, will create sample output file
    dir_path : str
        output directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    data_model_num : int
        MagIC data model 2 or 3, default 3
    samp_outfile : str
        sample output filename, default "samples.txt"
    site_outfile : str
        site output filename, default "sites.txt"

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful, meas_file name written)


    Info
    ----------
    Orientation convention:
        [1] Lab arrow azimuth= mag_azimuth; Lab arrow dip=-field_dip
            i.e., field_dip is degrees from vertical down - the hade [default]
        [2] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = -field_dip
            i.e., mag_azimuth is strike and field_dip is hade
        [3] Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip
            i.e.,  lab arrow same as field arrow, but field_dip was a hade.
        [4] lab azimuth and dip are same as mag_azimuth, field_dip
        [5] lab azimuth is same as mag_azimuth,lab arrow dip=field_dip-90
        [6] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = 90-field_dip
        [7] all others you will have to either customize your
            self or e-mail ltauxe@ucsd.edu for help.

   Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY


    """

    # initialize variables
    # not used: #cont=0
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    data_model_num = int(float(data_model_num))
    ask = 0
    Z = 1
    AniRecs, SpecRecs, SampRecs, MeasRecs = [], [], [], []
    AppSpec = 0

    # set defaults for MagIC 2
    if data_model_num == 2:
        if measfile == 'measurements.txt':
            measfile = 'magic_measurements.txt'
        if spec_outfile == 'specimens.txt':
            spec_outfile = 'er_specimens.txt'

    # format variables
    specnum = int(specnum)
    samp_con = str(samp_con)
    or_con = str(or_con)
    if azdip_infile:
        azdip_infile = os.path.join(input_dir_path, azdip_infile)
        azfile = open(azdip_infile, 'r')
        AzDipDat = azfile.readlines()
        azfile.close()
    amsfile = os.path.join(input_dir_path, infile)
    if spec_infile:
        spec_infile = os.path.join(input_dir_path, spec_infile)
        AppSpec = 1
    else:
        spec_outfile = os.path.join(output_dir_path, spec_outfile)
        AppSpec = 0
    if samp_infile:
        samp_infile = os.path.join(input_dir_path, samp_infile)
    measfile = os.path.join(output_dir_path, measfile)
    anisfile = os.path.join(output_dir_path, aniso_outfile)

    # set column names for MagIC 3
    spec_name_col = 'specimen'  #
    samp_name_col = 'sample'   #
    site_name_col = 'site'   #
    loc_name_col = 'location' #
    citation_col = 'citations'
    method_col = 'method_codes'
    site_description_col = 'description'
    expedition_col = 'expedition_name'
    instrument_col = 'instrument_codes'
    experiment_col = 'experiments'
    analyst_col = 'analysts'
    quality_col = 'quality'
    aniso_quality_col = 'result_quality'
    meas_standard_col = 'standard'
    meas_description_col = 'description'
    aniso_type_col = 'aniso_type'
    aniso_unit_col = 'aniso_s_unit'
    aniso_n_col = 'aniso_s_n_measurements'
    azimuth_col = 'azimuth'
    spec_volume_col = 'volume'
    samp_dip_col = 'dip'
    bed_dip_col = 'bed_dip'
    bed_dip_direction_col = 'bed_dip_direction'
    chi_vol_col = 'susc_chi_volume'
    aniso_sigma_col = 'aniso_s_sigma'
    aniso_unit_col = 'aniso_s_unit'
    aniso_tilt_corr_col = 'aniso_tilt_correction'
    meas_table_name = 'measurements'
    spec_table_name = 'specimens'
    samp_table_name = 'samples'
    site_table_name = 'sites'
    #
    meas_name_col = 'measurement'
    meas_time_col = 'timestamp'
    meas_ac_col = 'meas_field_ac'
    meas_temp_col = "meas_temp"

    # set column names for MagIC 2
    if data_model_num == 2:
        spec_name_col = 'er_specimen_name'
        samp_name_col = 'er_sample_name'
        site_name_col = 'er_site_name'
        loc_name_col = 'er_location_name'
        citation_col = 'er_citation_names'
        method_col = 'magic_method_codes'
        site_description_col = 'site_description'
        expedition_col = 'er_expedition_name'
        instrument_col = 'magic_instrument_codes'
        experiment_col = 'magic_experiment_names'
        analyst_col = 'er_analyst_mail_names'
        quality_col = 'measurement_flag'
        aniso_quality_col = 'anisotropy_flag'
        meas_standard_col = 'measurement_standard'
        meas_description_col = 'measurement_description'
        aniso_type_col = 'anisotropy_type'
        aniso_unit_col = 'anisotropy_unit'
        aniso_n_col = 'anisotropy_n'
        azimuth_col = 'sample_azimuth'
        spec_volume_col = 'specimen_volume'
        samp_dip_col = 'sample_dip'
        bed_dip_col = 'sample_bed_dip'
        bed_dip_direction_col = 'sample_bed_dip_direction'
        chi_vol_col = 'measurement_chi_volume'
        aniso_sigma_col = 'anisotropy_sigma'
        aniso_unit_col = 'anisotropy_unit'
        aniso_tilt_corr_col = 'anisotropy_tilt_correction'
        meas_table_name = 'magic_measurements'
        spec_table_name = 'er_specimens'
        samp_table_name = 'er_samples'
        site_table_name = 'er_sites'
        #
        meas_name_col = 'measurement_number'
        meas_time_col = 'measurement_date'
        meas_ac_col = 'measurement_lab_field_ac'
        meas_temp_col = "measurement_temp"

    # validate variables
    if "4" in samp_con[0]:
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "4"
    if "7" in samp_con[0]:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "7"

    try:
        file_input = open(amsfile, 'r')
    except:
        print('Error opening file: ', amsfile)
        return False, 'Error opening file: {}'.format(amsfile)

    # parse file
    SpecRecs, speclist = [], []
    if AppSpec == 1:
        try:
            SpecRecs, filetype = pmag.magic_read(
                spec_infile)  # append new records to existing
            if len(SpecRecs) > 0:
                for spec in SpecRecs:
                    if spec[spec_name_col] not in speclist:
                        speclist.append(spec[spec_name_col])
        except IOError:
            print('trouble opening ', spec_infile)
    Data = file_input.readlines()
    file_input.close()
    samps = []
    if samp_infile:
        samps, file_type = pmag.magic_read(samp_infile)
        SO_methods = []
        for rec in samps:
            if "magic_method_codes" in list(rec.keys()):
                methlist = rec["magic_method_codes"].replace(
                    " ", "").split(":")
                for meth in methlist:
                    if "SO" in meth and "SO-POM" not in meth and "SO-GT5" not in meth and "SO-ASC" not in meth and "SO-BAD" not in meth:
                        if meth not in SO_methods:
                            SO_methods.append(meth)
    #
        SO_priorities = pmag.set_priorities(SO_methods, ask)
    for line in Data:
        rec = line.split()
        if len(rec) > 0:
            AniRec, SpecRec, SampRec, SiteRec, MeasRec = {}, {}, {}, {}, {}
            specname = rec[0]
            if specnum != 0:
                sampname = specname[:-specnum]
            else:
                sampname = specname
            site = pmag.parse_site(sampname, samp_con, Z)
            AniRec[loc_name_col] = locname
            AniRec[citation_col] = "This study"
            AniRec[instrument_col] = inst
            method_codes = ['LP-X', 'AE-H', 'LP-AN-MS']
            AniRec[experiment_col] = specname + ":" + "LP-AN-MS"
            AniRec[analyst_col] = user
            AniRec[site_name_col] = site
            AniRec[samp_name_col] = sampname
            AniRec[spec_name_col] = specname
            labaz, labdip, bed_dip_direction, bed_dip = "", "", "", ""
            if azdip_infile:
                for key in list(AniRec.keys()):
                    SampRec[key] = AniRec[key]
                for oline in AzDipDat:  # look for exact match first
                    orec = oline.replace('\n', '').split()
                    if orec[0].upper() in specname.upper():  # we have a match
                        labaz, labdip = pmag.orient(
                            float(orec[1]), float(orec[2]), or_con)
                        bed_dip_direction = float(
                            orec[3]) - 90.  # assume dip to right of strike
                        bed_dip = float(orec[4])
                        break
                if labaz == "":  # found no exact match - now look at sample level
                    for oline in AzDipDat:
                        orec = oline.split()
                        if orec[0].upper() == sampname.upper():  # we have a match
                            labaz, labdip = pmag.orient(
                                float(orec[1]), float(orec[2]), or_con)
                            bed_dip_direction = float(
                                orec[3]) - 90.  # assume dip to right of strike
                            bed_dip = float(orec[4])
                            break
                if labaz == "":  # found no exact match - now look at sample level
                    print('found no orientation data - will use specimen coordinates')
                    #raw_input("<return> to continue")
                else:
                    for key in list(AniRec.keys()):
                        SampRec[key] = AniRec[key]
                    SampRec[azimuth_col] = '%7.1f' % (labaz)
                    SampRec[dip_col] = '%7.1f' % (labdip)
                    SampRec[bed_dip_direction_col] = '%7.1f' % (
                        bed_dip_direction)
                    SampRec[bed_dip_col] = '%7.1f' % (bed_dip)
                    SampRecs.append(SampRec)
            elif samp_infile:
                redo, p = 1, 0
                orient = {}
                if len(SO_methods) == 1:
                    az_type = SO_methods[0]
                    orient = pmag.find_samp_rec(
                        AniRec[samp_name_col], samps, az_type)
                    if orient[azimuth_col] != "":
                        method_codes.append(az_type)
                    else:
                        print("no orientation data for ",
                              AniRec[samp_name_col], labaz)
                        orient[azimuth_col] = ""
                        orient[dip_col] = ""
                        orient[bed_dip_direction_col] = ""
                        orient[dip_col] = ""
                        noorient = 1
                        method_codes.append("SO-NO")
                        redo = 0
                    redo = 0
                while redo == 1:
                    if p >= len(SO_priorities):
                        print("no orientation data for ",
                              AniRec[samp_name_col], labaz)
                        orient[azimuth_col] = ""
                        orient[dip_col] = ""
                        orient[bed_dip_direction_col] = ""
                        orient[bed_dip_col] = ""
                        noorient = 1
                        method_codes.append("SO-NO")
                        redo = 0
                    else:
                        az_type = SO_methods[SO_methods.index(
                            SO_priorities[p])]
                        orient = pmag.find_samp_rec(
                            AniRec[samp_name_col], samps, az_type)
                        if orient[azimuth_col] != "":
                            method_codes.append(az_type)
                            redo = 0
                        noorient = 0
                    p += 1
                if orient[azimuth_col] != "":
                    labaz = float(orient[azimuth_col])
                if orient[dip_col] != "":
                    labdip = float(orient[dip_col])
                if dip_direction_col in list(orient.keys()) and orient[dip_direction_col] != "":
                    bed_dip_direction = float(
                        orient[dip_direction_col])
                if dip_col in list(orient.keys()) and orient[dip_col] != "":
                    sample_bed_dip = float(orient[dip_col])
            for key in list(AniRec.keys()):
                SpecRec[key] = AniRec[key]
            for key in list(AniRec.keys()):
                MeasRec[key] = AniRec[key]
            AniRec[aniso_type_col] = "AMS"
            AniRec[aniso_n_col] = "192"
            s1_val = rec[1]
            s2_val = rec[2]
            s3_val = rec[3]
            s4_val = rec[4]
            s5_val = rec[5]
            s6_val = rec[6]
            if data_model_num == 2:
                AniRec['anisotropy_s1'] = s1_val
                AniRec['anisotropy_s2'] = s2_val
                AniRec['anisotropy_s3'] = s3_val
                AniRec['anisotropy_s4'] = s4_val
                AniRec['anisotropy_s5'] = s5_val
                AniRec['anisotropy_s6'] = s6_val
            else:
                vals = [s1_val, s2_val, s3_val, s4_val, s5_val, s6_val]
                AniRec['aniso_s'] = ":".join([val.strip() for val in vals])
            AniRec[aniso_sigma_col] = rec[7]
            AniRec[aniso_tilt_corr_col] = '-1'
            AniRec[aniso_unit_col] = 'Normalized by trace'
            SpecRec[spec_volume_col] = '%8.3e' % (
                1e-6 * float(rec[12]))  # volume from cc to m^3
            MeasRec[quality_col] = 'g'  # good
            MeasRec[meas_standard_col] = 'u'  # unknown
            date = rec[14].split('/')
            if int(date[2]) > 80:
                date[2] = '19' + date[2]
            else:
                date[2] = '20' + date[2]
            datetime = date[2] + ':' + date[0] + ':' + date[1] + ":"
            datetime = datetime + rec[15]
            MeasRec[meas_name_col] = '1'
            MeasRec[meas_time_col] = datetime
            MeasRec[meas_ac_col] = '%8.3e' % (
                4 * np.pi * 1e-7 * float(rec[11]))  # convert from A/m to T
            MeasRec[meas_temp_col] = "300"  # assumed room T in kelvin
            MeasRec[chi_vol_col] = rec[8]
            MeasRec[meas_description_col] = 'Bulk measurement'
            MeasRec[method_col] = 'LP-X'
            # remove keys that aren't valid in MagIC 2.5
            if data_model_num == 2:
                for remove_key in ['magic_instrument_codes', 'magic_experiment_names']:
                    if remove_key in SpecRec:
                        val = SpecRec.pop(remove_key)
                #for remove_key in ['magic_experiment_name']:
                #    if remove_key in AniRec:
                #        AniRec.pop(remove_key)
                MeasRec['magic_experiment_name'] = AniRec.get('magic_experiment_names', '')
                if 'magic_experiment_names' in MeasRec:
                    MeasRec.pop('magic_experiment_names')
            else:
                MeasRec['experiment'] = AniRec.get('experiments', '')
                if 'experiments' in MeasRec:
                    MeasRec.pop('experiments')
            #
            if SpecRec[spec_name_col] not in speclist:  # add to list
                speclist.append(SpecRec[spec_name_col])
                SpecRecs.append(SpecRec)
            MeasRecs.append(MeasRec)
            methods = ""
            for meth in method_codes:
                methods = methods + meth + ":"
            # get rid of annoying spaces in Anthony's export files
            AniRec[method_col] = methods.strip()
            AniRecs.append(AniRec)
            if labaz != "":  # have orientation info
                AniRecG, AniRecT = {}, {}
                for key in list(AniRec.keys()):
                    AniRecG[key] = AniRec[key]
                for key in list(AniRec.keys()):
                    AniRecT[key] = AniRec[key]
                sbar = []
                sbar.append(float(s1_val))
                sbar.append(float(s2_val))
                sbar.append(float(s3_val))
                sbar.append(float(s4_val))
                sbar.append(float(s5_val))
                sbar.append(float(s6_val))
                sbarg = pmag.dosgeo(sbar, labaz, labdip)
                if data_model_num == 2:
                    AniRecG["anisotropy_s1"] = '%12.10f' % (sbarg[0])
                    AniRecG["anisotropy_s2"] = '%12.10f' % (sbarg[1])
                    AniRecG["anisotropy_s3"] = '%12.10f' % (sbarg[2])
                    AniRecG["anisotropy_s4"] = '%12.10f' % (sbarg[3])
                    AniRecG["anisotropy_s5"] = '%12.10f' % (sbarg[4])
                    AniRecG["anisotropy_s6"] = '%12.10f' % (sbarg[5])
                else:
                    AniRecG['aniso_s'] = ":".join([str(a) for a in sbarg])
                AniRecG[aniso_tilt_corr_col] = '0'
                AniRecs.append(AniRecG)
                if bed_dip != "" and bed_dip != 0:  # have tilt correction
                    sbart = pmag.dostilt(sbarg, bed_dip_direction, bed_dip)
                    if data_model_num == 2:
                        AniRecT["anisotropy_s1"] = '%12.10f' % (sbart[0])
                        AniRecT["anisotropy_s2"] = '%12.10f' % (sbart[1])
                        AniRecT["anisotropy_s3"] = '%12.10f' % (sbart[2])
                        AniRecT["anisotropy_s4"] = '%12.10f' % (sbart[3])
                        AniRecT["anisotropy_s5"] = '%12.10f' % (sbart[4])
                        AniRecT["anisotropy_s6"] = '%12.10f' % (sbart[5])
                    else:
                        AniRecT['aniso_s'] = ":".join([str(a) for a in sbart])
                    AniRecT[aniso_tilt_corr_col] = '100'
                    AniRecs.append(AniRecT)

    # for MagIC 2, anisotropy records go in rmag_anisotropy
    if data_model_num == 2:
        pmag.magic_write(anisfile, AniRecs, 'rmag_anisotropy')
        print("anisotropy data saved in ", anisfile)
    # for MagIC 3, anisotropy records go in specimens
    else:
        full_SpecRecs = []
        SampRecs = []
        SiteRecs = []
        spec_list = []
        samp_list = []
        site_list = []
        for rec in SpecRecs:
            full_SpecRecs.append(rec)
            spec_name = rec[spec_name_col]
            samp_name = rec.get(samp_name_col, '')
            site_name = rec.get(site_name_col, '')
            loc_name = rec.get(loc_name_col, '')
            if spec_name not in spec_list:
                ani_recs = pmag.get_dictitem(AniRecs, spec_name_col, spec_name, 'T')
                full_SpecRecs.extend(ani_recs)
                if (samp_name not in samp_list) and (samp_name):
                    samp_list.append(samp_name)
                    SampRecs.append({samp_name_col: samp_name, site_name_col: site_name})
                    if (site_name not in site_list) and (site_name):
                        SiteRecs.append({site_name_col: site_name, loc_name_col: loc_name})
        full_SpecRecs, keys = pmag.fillkeys(full_SpecRecs)
        SpecRecs = full_SpecRecs
        print('anisotropy data added to specimen records')
    if AppSpec:
        pmag.magic_write(spec_infile, SpecRecs, spec_table_name)
        print('specimen information appended to {}'.format(spec_infile))
    else:
        pmag.magic_write(spec_outfile, SpecRecs, spec_table_name)
        print('specimen information written to new file: {}'.format(spec_outfile))
    pmag.magic_write(measfile, MeasRecs, meas_table_name)
    print('measurement data saved in ', measfile)
    if azdip_infile:
        sampfile = 'er_samples.txt'
        pmag.magic_write(sampfile, SampRecs, samp_table_name)
        print('sample data saved in ', sampfile)
    if data_model_num == 3:
        if not azdip_infile:
            if SampRecs:
                pmag.magic_write(samp_outfile, SampRecs, samp_table_name)
        if SiteRecs:
            pmag.magic_write(site_outfile, SiteRecs, site_table_name)
    return True, measfile


### LDEO_magic conversion

def ldeo(magfile, dir_path=".", input_dir_path="",
         meas_file="measurements.txt", spec_file="specimens.txt",
         samp_file="samples.txt", site_file="sites.txt", loc_file="locations.txt",
         specnum=0, samp_con="1", location="unknown", codelist="",
         coil="", arm_labfield=50e-6, trm_peakT=873., peakfield=0,
         labfield=0, phi=0, theta=0, mass_or_vol="v", noave=0):
    """
    converts Lamont Doherty Earth Observatory measurement files to MagIC data base model 3.0

    Parameters
    _________
    magfile : input measurement file
    dir_path : output directory path, default "."
    input_dir_path : input file directory IF different from dir_path, default ""
    meas_file : output file measurement file name, default "measurements.txt"
    spec_file : output file specimen file name, default "specimens.txt"
    samp_file : output file sample file name, default "samples.txt"
    site_file : output file site file name, default "sites.txt"
    loc_file : output file location file name, default "locations.txt"
    specnum : number of terminal characters distinguishing specimen from sample, default 0
    samp_con :  sample/site naming convention, default "1"
            "1" XXXXY: where XXXX is an arbitr[ary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            "2" XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
            "3" XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
            "4-Z" XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            "5" site name same as sample
            "6" site is entered under a separate column NOT CURRENTLY SUPPORTED
            "7-Z" [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.

            "8" synthetic - has no site name
            "9" ODP naming convention

    codelist : colon delimited string of lab protocols (e.g., codelist="AF"), default ""
        AF:  af demag
        T: thermal including thellier but not trm acquisition
        S: Shaw method
        I: IRM (acquisition)
        N: NRM only
        TRM: trm acquisition
        ANI: anisotropy experiment
        D: double AF demag
        G: triple AF demag (GRM protocol)
    coil : 1,2, or 3 unist of IRM field in volts using ASC coil #1,2 or 3, default ""
    arm_labfield : dc field for ARM in tesla, default 50e-6
    peakfield : peak af field for ARM, default 873.
    trm_peakT : peak temperature for TRM, default 0
    labfield : lab field in tesla for TRM, default 0
    phi, theta : direction of lab field, default 0, 0
    mass_or_vol : is the parameter in the file mass 'm' or volume 'v', default "v"
    noave : boolean, if False, average replicates, default False

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful, meas_file name written)

    Effects
    _______
    creates MagIC formatted tables
    """
    # initialize some stuff
    dec = [315, 225, 180, 135, 45, 90, 270, 270, 270, 90, 180, 180, 0, 0, 0]
    inc = [0, 0, 0, 0, 0, -45, -45, 0, 45, 45, 45, -45, -90, -45, 45]
    tdec = [0, 90, 0, 180, 270, 0, 0, 90, 0]
    tinc = [0, 0, 90, 0, 0, -90, 0, 0, 90]
    demag = "N"
    trm = 0
    irm = 0

    # format/organize variables
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    labfield = int(labfield) * 1e-6
    phi = int(phi)
    theta = int(theta)
    specnum = - int(specnum)

    if magfile:
        try:
            fname = pmag.resolve_file_name(magfile, input_dir_path)
            infile = open(fname, 'r')
        except IOError:
            print("bad mag file name")
            return False, "bad mag file name"
    else:
        print("mag_file field is required option")
        return False, "mag_file field is required option"

    samp_con = str(samp_con)
    if "4" in samp_con:
        if "-" not in samp_con:
            print(
                "naming convention option [4] must be in form 4-Z where Z is an integer")
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "4"
    elif "7" in samp_con:
        if "-" not in samp_con:
            print(
                "naming convention option [7] must be in form 7-Z where Z is an integer")
            return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "4"
    else:
        Z = 1

    codes = codelist.split(':')
    if "AF" in codes:
        demag = 'AF'
        if not labfield:
            methcode = "LT-AF-Z"
        if labfield:
            methcode = "LT-AF-I"
    if "T" in codes:
        demag = "T"
        if not labfield:
            methcode = "LT-T-Z"
        if labfield:
            methcode = "LT-T-I"
    if "I" in codes:
        methcode = "LP-IRM"
        irmunits = "mT"
    if "S" in codes:
        demag = "S"
        methcode = "LP-PI-TRM:LP-PI-ALT-AFARM"
        trm_labfield = labfield
        # should use arm_labfield and trm_peakT as well, but these values are currently never asked for
    if "G" in codes:
        methcode = "LT-AF-G"
    if "D" in codes:
        methcode = "LT-AF-D"
    if "TRM" in codes:
        demag = "T"
        trm = 1

    if coil:
        methcode = "LP-IRM"
        irmunits = "V"
        if coil not in ["1", "2", "3"]:
            print('not a valid coil specification')
            return False, 'not a valid coil specification'

    if demag == "T" and "ANI" in codes:
        methcode = "LP-AN-TRM"
    if demag == "AF" and "ANI" in codes:
        methcode = "LP-AN-ARM"
        if labfield == 0:
            labfield = 50e-6
        if peakfield == 0:
            peakfield = .180
    MeasRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    version_num = pmag.get_version()
    # find start of data:
    DIspec = []
    Data = infile.readlines()
    infile.close()
    for k in range(len(Data)):
        rec = Data[k].split()
        if len(rec) <= 2:
            continue
        if rec[0].upper() == "LAT:" and len(rec) > 3:
            lat, lon = rec[1], rec[3]
            continue
        elif rec[0].upper() == "ID":
            continue
        MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}
        specimen = rec[0]
        if specnum != 0:
            sample = specimen[:specnum]
        else:
            sample = specimen
        site = pmag.parse_site(sample, samp_con, Z)
        if mass_or_vol == 'v':
            volume = float(rec[12])
            if volume > 0:
                # convert to SI (assume Bartington, 10-5 SI)
                susc_chi_volume = '%10.3e' % (float(rec[11])*1e-5 / volume)
            else:
                # convert to SI (assume Bartington, 10-5 SI)
                susc_chi_volume = '%10.3e' % (float(rec[11])*1e-5)
        else:
            mass = float(rec[12])
            if mass > 0:
                # convert to SI (assume Bartington, 10-5 SI)
                susc_chi_mass = '%10.3e' % (
                    float(rec[11])*1e-5) / mass
            else:
                # convert to SI (assume Bartington, 10-5 SI)
                susc_chi_mass = '%10.3e' % (float(rec[11])*1e-5)
        # print((specimen,sample,site,samp_con,Z))

        # fill tables besides measurements
        if specimen != "" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
            SpecRec['specimen'] = specimen
            SpecRec['sample'] = sample
            if mass_or_vol == 'v':
                SpecRec["susc_chi_volume"] = susc_chi_volume
                SpecRec["volume"] = volume
            else:
                SpecRec["susc_chi_mass"] = susc_chi_mass
                SpecRec["magn_mass"] = mass
            SpecRecs.append(SpecRec)
        if sample != "" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
            SampRec['sample'] = sample
            SampRec['site'] = site
            SampRecs.append(SampRec)
        if site != "" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
            SiteRec['site'] = site
            SiteRec['location'] = location
            SiteRec['lat'] = lat
            SiteRec['lon'] = lon
            SiteRecs.append(SiteRec)
        if location != "" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
            LocRec['location'] = location
            LocRec['lat_n'] = lat
            LocRec['lon_e'] = lon
            LocRec['lat_s'] = lat
            LocRec['lon_w'] = lon
            LocRecs.append(LocRec)

        # fill measurements
        if mass_or_vol == 'v':
            MeasRec["susc_chi_volume"] = susc_chi_volume
        else:
            SpecRec["susc_chi_mass"] = susc_chi_mass
        MeasRec["treat_temp"] = '%8.3e' % (273)  # room temp in kelvin
        MeasRec["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
        MeasRec["treat_ac_field"] = '0'
        MeasRec["treat_dc_field"] = '0'
        MeasRec["treat_dc_field_phi"] = '0'
        MeasRec["treat_dc_field_theta"] = '0'
        meas_type = "LT-NO"
        MeasRec["quality"] = 'g'
        MeasRec["standard"] = 'u'
        MeasRec["treat_step_num"] = 0
        MeasRec["specimen"] = specimen
#        if mass_or_vol=='v': MeasRec["susc_chi_volume"]=susc_chi_volume
#        else: MeasRec["susc_chi_mass"]=susc_chi_mass
        try:
            float(rec[3])
            MeasRec["dir_csd"] = rec[3]
        except ValueError:
            MeasRec["dir_csd"] = ''
        MeasRec["magn_moment"] = '%10.3e' % (float(rec[4])*1e-7)
        MeasRec["dir_dec"] = rec[5]
        MeasRec["dir_inc"] = rec[6]
        MeasRec["citations"] = "This study"
        if demag == "AF":
            if methcode != "LP-AN-ARM":
                MeasRec["treat_ac_field"] = '%8.3e' % (
                    float(rec[1])*1e-3)  # peak field in tesla
                meas_type = "LT-AF-Z"
                MeasRec["treat_dc_field"] = '0'
            else:  # AARM experiment
                if treat[1][0] == '0':
                    meas_type = "LT-AF-Z"
                    MeasRec["treat_ac_field"] = '%8.3e' % (
                        peakfield)  # peak field in tesla
                else:
                    meas_type = "LT-AF-I"
                    ipos = int(treat[0])-1
                    MeasRec["treat_dc_field_phi"] = '%7.1f' % (dec[ipos])
                    MeasRec["treat_dc_field_theta"] = '%7.1f' % (inc[ipos])
                    MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                    MeasRec["treat_ac_field"] = '%8.3e' % (
                        peakfield)  # peak field in tesla
        elif demag == "T":
            if rec[1][0] == ".":
                rec[1] = "0"+rec[1]
            treat = rec[1].split('.')
            if len(treat) == 1:
                treat.append('0')
            MeasRec["treat_temp"] = '%8.3e' % (
                float(rec[1])+273.)  # temp in kelvin
            meas_type = "LT-T-Z"
            MeasRec["treat_temp"] = '%8.3e' % (
                float(treat[0])+273.)  # temp in kelvin
            if trm == 0:  # demag=T and not trmaq
                if treat[1][0] == '0':
                    meas_type = "LT-T-Z"
                else:
                    # labfield in tesla (convert from microT)
                    MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                    MeasRec["treat_dc_field_phi"] = '%7.1f' % (
                        phi)  # labfield phi
                    MeasRec["treat_dc_field_theta"] = '%7.1f' % (
                        theta)  # labfield theta
                    if treat[1][0] == '1':
                        meas_type = "LT-T-I"  # in-field thermal step
                    if treat[1][0] == '2':
                        meas_type = "LT-PTRM-I"  # pTRM check
                        pTRM = 1
                    if treat[1][0] == '3':
                        # this is a zero field step
                        MeasRec["treat_dc_field"] = '0'
                        meas_type = "LT-PTRM-MD"  # pTRM tail check
            else:
                meas_type = "LT-T-I"  # trm acquisition experiment
        MeasRec['method_codes'] = meas_type
        MeasRecs.append(MeasRec)
    # need to add these
    meas_file = pmag.resolve_file_name(meas_file, output_dir_path)
    spec_file = pmag.resolve_file_name(spec_file, output_dir_path)
    samp_file = pmag.resolve_file_name(samp_file, output_dir_path)
    site_file = pmag.resolve_file_name(site_file, output_dir_path)
    loc_file = pmag.resolve_file_name(loc_file, output_dir_path)

    con = cb.Contribution(output_dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.tables['specimens'].write_magic_file(custom_name=spec_file)
    con.tables['samples'].write_magic_file(custom_name=samp_file)
    con.tables['sites'].write_magic_file(custom_name=site_file)
    con.tables['locations'].write_magic_file(custom_name=loc_file)
    con.tables['measurements'].write_magic_file(custom_name=meas_file)

    return True, meas_file


## LIVDB conversion

def livdb(input_dir_path, output_dir_path=".", meas_out="measurements.txt",
          spec_out="specimens.txt", samp_out="samples.txt",
          site_out="sites.txt", loc_out="locations.txt",
          samp_name_con='sample=specimen', samp_num_chars=0,
          site_name_con='site=sample', site_num_chars=0, location_name="", data_model_num=3):

    """

    Search input directory for Livdb .csv or .livdb files
    and convert them to MagIC format.
    Input directory should contain only input files for one location.

    Parameters
    ----------
    input_dir_path : str
        input directory with .csv or .livdb files to import
    output_dir_path : str
        directory to output files, default "."
    meas_out : str
        output measurement file name, default "measurements.txt"
    spec_out : str
        output specimen file name, default "specimens.txt"
    samp_out: str
        output sample file name, default "samples.txt"
    site_out : str
        output site file name, default "sites.txt"
    loc_out : str
        output location file name, default "locations.txt"
    samp_name_con : str
        specimen --> sample naming convention, default 'sample=specimen'
        options: {1: 'sample=specimen', 2: 'no. of terminate characters', 3: 'character delimited'}
    samp_num_chars : int or str
        if using 'no. of terminate characters' or 'character delimited',
        provide the number of characters or the character delimiter
    site_name_con : str
        sample --> site naming convention, default 'site=sample'
        options: {1: 'site=sample', 2: 'no. of terminate characters', 3: 'character delimited'}
    site_num_chars : int or str
        if using 'no. of terminate characters' or 'character delimited',
        provide the number of characters or the character delimiter
    locname : str
        location name, default ""
    data_model_num : int
        MagIC data model 2 or 3, default 3

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful, file name written)


    Input file format
    -----------------
    # --------------------------------------
    # Read the file
    #
    # Livdb Database structure
    #
    # HEADER:
    # 1) First line is the header.
    #    The header includes 19 fields delimited by comma (',')
    #    Notice: space is not a delimiter !
    #    In the list below the delimiter is not used, and the conversion script assumes comma delimited file
    #
    # Header fields:
    # Sample code (string): (delimiter = space+)
    # Sample Dip (degrees): (delimiter = space)
    # Sample Dec (degrees): (delimiter = space)
    # Height (meters): (delimiter = space)
    # Position (no units): (delimiter = space)
    # Thickness (meters): (delimiter = space)
    # Unit Dip (aka tilt) (degrees): (delimiter = space)
    # Unit Dip Direction (aka Direction) (degrees): (delimiter = space)
    # Site Latitude (decimal degrees): (delimiter = space)
    # Site Longitude (decimal degrees): (delimiter = space)
    # Experiment Type (string): (delimiter = |)
    # Name of measurer (string): (delimiter = |)
    # Magnetometer name  (string): (delimiter = |)
    # Demagnetiser name  (string): (delimiter = |)
    # Specimen/Experiment Comment  (string): (delimiter = |)
    # Database version (integer): (delimiter = |)
    # Conversion Version (string): (delimiter = |)
    # Sample Volume (cc): (delimiter = |)
    # Sample Density  (kg/m^3): (delimiter = |)
    #
    #
    # BODY:
    # 1) Body includes 22 fields delimited by comma (',')
    # 2) Body ends with an "END" statement
    #
    # Body fields:
    # Treatment (aka field) (mT / deg C / 10-2 W): (delimiter = space)
    # Microwave Power (W) : (delimiter = space)
    # Microwave Time (s) : (delimiter = space)
    # X (nAm^2): (delimiter = space)
    # Y (nAm^2): (delimiter = space)
    # Z (nAm^2): (delimiter = space)
    # Mass g: (delimiter = space)
    # Applied field intensity (micro_T): (delimiter = space)
    # Applied field Dec (degrees): (delimiter = space)
    # Applied Field Inc (degrees): (delimiter = space)
    # Measurement Date (DD-MM-YYYY)  or (DD/MM/YYYY) #### CHECK !! ## (delimiter = |)
    # Measurement Time (HH:SS:MM) (delimiter = |)
    # Measurement Remark (string) (delimiter = |)
    # Step Number (integer) (delimiter = |)
    # Step Type (string) (Z/I/P/T/O/NRM) (delimiter = |)
    # Tristan Gain (integer) (delimiter = |)
    # Microwave Power Integral (W.s) (delimiter = |)
    # JR6 Error(percent %) (delimiter = |)
    # FiT Smm (?) (delimiter = |)
    # Utrecht Error (percent %) (delimiter = |)
    # AF Demag/Remag Peak Field (mT) (delimiter = |)
    # TH Demag/Remag Peak Temperature (deg C) (delimiter = |)
    # -------------------------------------------------------------

    # --------------------------------------
    # Important assumptions:
    # (1) The program checks if the same treatment appears more than once (a measurement is repeated twice).
    #       If yes, then it takes only the second one and ignores the first.
    # (2) –99 and 999 are codes for N/A
    # (3) The "treatment step" for Thermal Thellier experiment is taken from the "TH Demag/Remag Peak Temperature"
    # (4) The "treatment step" for Microwave Thellier experiment is taken from the "Step Number"
    # (5) As there might be contradiction between the expected treatment (i.e. Z,I,P,T,A assumed by the experiment type)
    #       and "Step Type" field due to typos or old file formats:
    #       The program concludes the expected treatment from the following:
    #       ("Experiment Type) + ("Step Number" or "TH Demag/Remag Peak Temperature") + (the order of the measurements).
    #       The conversion script will spit out a WARNING message in a case of contradiction.
    # (6) If the program finds AF demagnetization before the infield to zerofield steps:
    #       then assumes that this is an AFD step domne before the experiment.
    # (7) The program ignores microwave fields (aka field,Microwave Power,Microwave Time) in Thermal experiments. And these fields will not be converted
    #     to MagIC.
    # (8) NRM step: NRM step is regonized either by "Applied field intensity"=0 and "Applied field Dec" =0 and "Applied Field Inc"=0
    #               or if "Step Type" = NRM
    #
    #
    #
    # -------------------------------------------------------------

    # --------------------------------------
    # Script was tested on the following protocols:
    # TH-PI-IZZI+ [November 2013, rshaar]
    # MW-PI-C++ [November 2013, rshaar]
    # MW-PI-IZZI+ ]November 2013, rshaar]
    #
    # Other protocols should be tested before use.
    #
    #
    #
    # -------------------------------------------------------------
    """

    def get_sample_name(specimen, sample_naming_convention):
        """
        Parse out sample name from specimen name and naming convention
        """
        specimen = specimen.strip()
        if sample_naming_convention[0] == "sample=specimen":
            sample = specimen
        elif sample_naming_convention[0] == "no. of terminate characters":
            n = - int(sample_naming_convention[1])
            sample = specimen[:n]
        elif sample_naming_convention[0] == "character delimited":
            d = sample_naming_convention[1]
            sample_splitted = specimen.split(d)
            if len(sample_splitted) == 1:
                sample = sample_splitted[0]
            else:
                sample = d.join(sample_splitted[:-1])
        return sample

    def get_site_name(sample, site_naming_convention):
        """
        Parse out site name from sample name and naming convention
        """
        sample = sample.strip()
        if site_naming_convention[0] == "site=sample":
            site = sample
        elif site_naming_convention[0] == "no. of terminate characters":
            n = int(site_naming_convention[1])*-1
            site = sample[:n]
        elif site_naming_convention[0] == "character delimited":
            d = site_naming_convention[1]
            site_splitted = sample.split(d)
            if len(site_splitted == 1):
                site = site_splitted[0]
            else:
                site = d.join(site_splitted[:-1])

        return site


    if data_model_num == 2:
        loc_col = "er_location_name"
        site_col = "er_site_name"
        samp_col = "er_sample_name"
        spec_col = "er_specimen_name"
        citation_col = "er_citation_names"
        analyst_col = "er_analyst_mail_names"
        instrument_col = "magic_instrument_codes"
        quality_col = "measurement_flag"
        standard_col = "measurement_standard"
        step_col = "measurement_number"
        experiment_col = "magic_experiment_name"
        methods_col = "magic_method_codes"
        dec_col = "measurement_dec"
        inc_col = "measurement_inc"
        moment_col = "measurement_magn_moment"
        meas_temp_col = "measurement_temp"
        dc_field_col = "treatment_dc_field"
        dc_field_phi_col = "treatment_dc_field_phi"
        dc_field_theta_col = "treatment_dc_field_theta"
        mw_power_col = "treatment_mw_power"
        mw_time_col = "treatment_mw_time"
        mw_integral_col = "treatment_mw_integral"
        meas_descr_col = "measurement_description"
        treat_temp_col = "treatment_temp"
        ac_field_col = "treatment_ac_field"
        spec_type_col = "specimen_type"
        spec_lithology_col = "specimen_lithology"
        spec_class_col = "specimen_class"
        spec_dip_col = "specimen_dip"
        spec_azimuth_col = "specimen_azimuth"
        spec_height_col = "specimen_height"
        spec_descr_col = "specimen_description"
        spec_vol_col = "specimen_volume"
        spec_density_col = "specimen_density"
        date_col = "measurement_date"
        if meas_out == "measurements.txt":
            meas_out = "magic_measurements.txt"
        if spec_out == "specimens.txt":
            spec_out = "er_specimens.txt"
        meas_type = "magic_measurements"
        spec_type = "er_specimens"
    else:
        loc_col = "location"
        site_col = "site"
        samp_col = "sample"
        spec_col = "specimen"
        citation_col = "citations"
        analyst_col = "analysts"
        instrument_col = "instrument_codes"
        quality_col = "quality"
        standard_col = "standard"
        step_col = "treat_step_num"
        experiment_col = "experiment"
        methods_col = "method_codes"
        dec_col = "dir_dec"
        inc_col = "dir_inc"
        moment_col = "magn_moment"
        meas_temp_col = "meas_temp"
        dc_field_col = "treat_dc_field"
        dc_field_phi_col = "treat_dc_field_phi"
        dc_field_theta_col = "treat_dc_field_theta"
        mw_power_col = "treat_mw_power"
        mw_time_col = "treat_mw_time"
        mw_integral_col = "treat_mw_integral"
        meas_descr_col = "description"
        treat_temp_col = "treat_temp"
        ac_field_col = "treat_ac_field"
        spec_type_col = "geologic_types"
        spec_lithology_col = "lithologies"
        spec_class_col = "geologic_classes"
        spec_dip_col = "dip"
        spec_azimuth_col = "azimuth"
        spec_height_col = "height"
        spec_descr_col = "description"
        spec_vol_col = "volume"
        spec_density_col = "density"
        date_col = "timestamp"
        meas_type = "measurements"
        spec_type = "specimens"

    specimen_headers = []
    seqnum = 1
    MagRecs = []
    measurement_headers = []
    ErRecs = []
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, output_dir_path)

    samp_name_cons = {1: 'sample=specimen', 2: 'no. of terminate characters', 3: 'character delimited'}
    if samp_name_con not in samp_name_cons.values():
        samp_name_con =  samp_name_cons.get(int(samp_name_con), 'sample=specimen')
    if samp_name_con == 'no. of terminate characters' and not samp_num_chars:
        print("-W- You have selected the sample naming convention: 'no. of terminate characters',\n    but have provided the number of characters as 0.\n    Defaulting to use 'sample=specimen' instead.")
        samp_name_con = 'sample=specimen'

    site_name_cons =  {1: 'site=sample', 2: 'no. of terminate characters', 3: 'character delimited'}
    if site_name_con not in site_name_cons.values():
        site_name_con = site_name_cons.get(int(site_name_con), 'site=sample')
    if site_name_con == 'no. of terminate characters' and not site_num_chars:
        print("-W- You have selected the site naming convention: 'no. of terminate characters',\n    but have provided the number of characters as 0.\n    Defaulting to use 'site=sample' instead.")
        site_name_con = 'site=sample'

    # -----------------------------------
    # Read file and sort data by specimen
    # -----------------------------------

    for files in os.listdir(input_dir_path):
        if files.endswith(".livdb") or files.endswith(".livdb.csv") or files.endswith(".csv"):
            fname = os.path.join(input_dir_path, files)
            print("Open file: ", fname)
            fin = open(fname, 'r')
            Data = {}
            header_codes = ['Sample code', 'Sample Dip', 'Sample Dec', 'Height', 'Position', 'Thickness', 'Unit Dip', 'Unit Dip Direction', 'Site Latitude',
                            'Site Longitude', 'Experiment Type', 'Name of measurer', 'Magnetometer name', 'Demagnetiser name', 'Specimen/Experiment Comment',
                            'Database version', 'Conversion Version', 'Sample Volume', 'Sample Density']

            meas_codes = ['Treatment (aka field)', 'Microwave Power', 'Microwave Time', 'moment_X', 'moment_Y', 'moment_Z', 'Mass', 'Applied field Intensity', 'Applied field Dec',
                          'Applied field Inc', 'Measurement Date', 'Measurement Time', 'Measurement Remark', 'Step Number', 'Step Type', 'Tristan Gain', 'Microwave Power Integral',
                          'JR6 Error', 'FiT Smm', 'Utrecht Error', 'AF Demag/Remag Peak Field', 'TH Demag/Remag Peak Temperature']

            line_number = 0
            continue_reading = True
            while continue_reading:
                # first line is the header
                this_specimen = True
                while this_specimen == True:
                    line = fin.readline()
                    line_number += 1
                    if not line:
                        continue_reading = False
                        break

                    # -------------------------------
                    # Read information from Header and body
                    # The data is stored in a dictionary:
                    # Data[specimen][Experiment_Type]['header_data']=tmp_header_data  --> a dictionary with header data
                    # Data[specimen][Experiment_Type]['meas_data']=[dict1, dict2, ...] --> a list of dictionaries with measurement data
                    # -------------------------------

                    header = line.strip('\n').split(",")
                    #header=str(this_line[0]).split()+ this_line[1:-1]

                    # header consists of fields separated by spaces and "|"

            # if len (header) > 15:
            ##                this_line_data[14:]=" ".join(this_line_data[14:])
            # del(this_line_data[15:])

                    # warning if missing info.

                    if len(header) < 19:
                        print("missing data in header.Line %i" %
                              line_number)
                        print(header)
                    # read header and sort in a dictionary
                    tmp_header_data = {}

                    for i in range(len(header_codes)):
                        tmp_header_data[header_codes[i]] = header[i]
                    specimen = tmp_header_data['Sample code']
                    Experiment_Type = tmp_header_data['Experiment Type']

                    if specimen not in list(Data.keys()):
                        Data[specimen] = {}
                    if Experiment_Type in list(Data[specimen].keys()):
                        print(
                            "-E- specimen %s has duplicate Experimental type %s. check it!" % (specimen, Experiment_Type))

                    Data[specimen][Experiment_Type] = {}
                    Data[specimen][Experiment_Type]['header_data'] = tmp_header_data
                    Data[specimen][Experiment_Type]['meas_data'] = []

                    # ---------------------------------------------------
                    # Read information from body and sort in dictonaries
                    # ---------------------------------------------------

                    while this_specimen:
                        line = fin.readline()
                        line_number += 1
                        # each specimen ends with "END" statement
                        if "END" in line:
                            this_specimen = False
                            break
                        # this_line=line.strip('\n').split("|")
                        #this_line_data=str(this_line[0]).split()+ this_line[1:-1]
                        this_line_data = line.strip('\n').split(",")
                        if len(this_line_data) < 22:
                            print("missing data in Line %i" %
                                  line_number)
                            print(this_line_data)
                            all_null = True
                            for i in this_line_data:
                                if i:
                                    all_null = False
                            if all_null:
                                this_specimen = False
                                break

                        tmp_data = {}
                        for i in range(len(this_line_data)):
                            tmp_data[meas_codes[i]] = this_line_data[i]
                        Data[specimen][Experiment_Type]['meas_data'].append(
                            tmp_data)

            # -----------------------------------
            # Convert to MagIC
            # -----------------------------------

            specimens_list = list(Data.keys())
            specimens_list.sort()
            for specimen in specimens_list:
                Experiment_Types_list = list(Data[specimen].keys())
                Experiment_Types_list.sort()
                for Experiment_Type in Experiment_Types_list:

                    # -----------------------------------
                    # Assuming that the first line is NRM always
                    # MW-PI-OT+:
                    #  Microwave Thellier Thellier protocol
                    # MW-PI-P:
                    #  Perpendicular method
                    #  demagnetizations until overprint is removed
                    #  then remagnetization perpendicular to the remaining NRM direction
                    # -----------------------------------

                    supported_experiments = ['MW-PI-OT+', 'MW-PI-P', 'MW-PI-C', 'MW-PI-C+', 'MW-PI-C++', 'MW-PI-IZZI', 'MW-PI-IZZI+', 'MW-PI-IZZI++', 'MW-PI-A', 'MW-PI-A+',
                                             'TH-PI-OT+', 'TH-PI-P', 'TH-PI-C', 'TH-PI-C+', 'TH-PI-C++', 'TH-PI-IZZI', 'TH-PI-IZZI+', 'TH-PI-IZZI++', 'TH-PI-A', 'TH-PI-A+',
                                             'TH-D', 'AF-D']
                    if Experiment_Type in supported_experiments:

                        header_line = Data[specimen][Experiment_Type]['header_data']
                        experiment_treatments, lab_treatments = [], []
                        measurement_running_number = 0
                        for i in range(len(Data[specimen][Experiment_Type]['meas_data'])):
                            meas_line = Data[specimen][Experiment_Type]['meas_data'][i]

                            # check if the same treatment appears more than once. If yes, assuming that the measurements is repeated twice,
                            # ignore the first, and take only the second one

                            if i < (len(Data[specimen][Experiment_Type]['meas_data'])-2):
                                Repeating_measurements = True
                                for key in ["Treatment (aka field)", "Microwave Power", "Microwave Time", "AF Demag/Remag Peak Field", "Applied field Intensity",
                                            "Applied field Dec", "Applied field Inc", "Step Type", "TH Demag/Remag Peak Temperature"]:
                                    if Data[specimen][Experiment_Type]['meas_data'][i][key] != Data[specimen][Experiment_Type]['meas_data'][i+1][key]:
                                        Repeating_measurements = False
                                if Repeating_measurements == True:
                                    print("Found a repeating measurement at line %i, sample %s. taking the last one" % (
                                        i, specimen))
                                    continue
                            # ------------------

                            MagRec = {}
                            # make sure ac field is set
                            MagRec[ac_field_col] = ''
                            # add sequence
                            if data_model_num == 3:
                                MagRec['sequence'] = seqnum
                                seqnum += 1
                            # header_data
                            MagRec[citation_col] = "This study"
                            MagRec[spec_col] = header_line['Sample code'].strip()
                            MagRec[samp_col] = get_sample_name(
                                MagRec[spec_col], [samp_name_con, samp_num_chars])
                            #print('mag rec samp col', MagRec[samp_col])
                            MagRec[site_col] = get_site_name(
                                MagRec[samp_col], [site_name_con, site_num_chars])
                            MagRec[loc_col] = location_name
                            MagRec[analyst_col] = header_line['Name of measurer']
                            MagRec[instrument_col] = header_line['Magnetometer name'] + \
                                ":"+header_line['Demagnetiser name']

                            # meas data
                            MagRec[quality_col] = 'g'
                            MagRec[standard_col] = 'u'
                            MagRec[step_col] = "%i" % measurement_running_number
                            CART = np.array([1e-9*float(meas_line['moment_X']), 1e-9*float(
                                meas_line['moment_Y']), 1e-9*float(meas_line['moment_Z'])])  # Am^2
                            DIR = pmag.cart2dir(CART)
                            MagRec[dec_col] = "%.2f" % DIR[0]
                            MagRec[inc_col] = "%.2f" % DIR[1]
                            MagRec[moment_col] = '%10.3e' % (
                                math.sqrt(sum(CART**2)))
                            # room temp in kelvin
                            MagRec[meas_temp_col] = '273.'

                            # Date and time
                            if "-" in meas_line['Measurement Date']:
                                date = meas_line['Measurement Date'].strip(
                                    "\"").split('-')
                            elif "/" in meas_line['Measurement Date']:
                                date = meas_line['Measurement Date'].strip(
                                    "\"").split('/')
                            else:
                                print(
                                    "-E- ERROR: line no. %i please use one of the following convention for date: MM-DD-YYYY or MM/DD/YYYY" % i)
                            yyyy = date[2]
                            dd = date[1]
                            mm = date[0]
                            hour = meas_line['Measurement Time'].strip(
                                "\"")
                            MagRec[date_col] = yyyy + \
                                ':'+mm+":"+dd+":"+hour

                            # lab field data: distinguish between PI experiments to AF/Thermal
                            if Experiment_Type == "TH-D" or Experiment_Type == "AF-D":
                                MagRec[dc_field_col] = '0'
                                MagRec[dc_field_phi_col] = '0'
                                MagRec[dc_field_theta_col] = '0'
                            else:
                                labfield = float(
                                    meas_line['Applied field Intensity'])*1e-6
                                MagRec[dc_field_col] = '%8.3e' % (
                                    labfield)
                                MagRec[dc_field_phi_col] = meas_line['Applied field Dec']
                                MagRec[dc_field_theta_col] = meas_line['Applied field Inc']

                            # treatment (MW or Thermal)
                            if "MW-" in Experiment_Type:
                                MagRec[mw_power_col] = meas_line['Microwave Power']
                                MagRec[mw_time_col] = meas_line['Microwave Time']
                                MagRec[mw_integral_col] = meas_line['Microwave Power Integral']
                                MagRec[meas_descr_col] = "Step Type"+"-" + \
                                    meas_line['Step Type']+":Step Number-" + \
                                    "%i" % int(
                                        meas_line['Step Number'])
                                # Ron CHECK !!
                                treatment = meas_line['Step Number']
                            elif "TH-" in Experiment_Type:
                                MagRec[treat_temp_col] = "%.2f" % (
                                    float(meas_line['TH Demag/Remag Peak Temperature'])+273)
                                treatment = meas_line['TH Demag/Remag Peak Temperature']
                            elif "AF-" in Experiment_Type:
                                MagRec[ac_field_col] = '%8.3e' % (
                                    float(meas_line['TH Demag/Remag Peak Temperature'])*1e-3)  # peak field in tesla
                                treatment = meas_line['AF Demag/Remag Peak Field']

                            # -----------------------------------
                            # notice future problems with the first line because "NRM" will not be in the Step Type field
                            # -----------------------------------
                            lab_treatment = ""
                            if len(experiment_treatments) == 0:
                                if float(MagRec[dc_field_col]) == 0 and float(MagRec[dc_field_phi_col]) == 0 and MagRec[dc_field_theta_col] == 0:
                                    lab_treatment = "LT-NO"
                                    experiment_treatments.append('0')
                                    IZorZI = ""
                                elif "NRM" in meas_line['Step Type']:
                                    lab_treatment = "LT-NO"
                                    experiment_treatments.append(
                                        MagRec[dc_field_col])
                                    IZorZI = ""

                            # -----------------------------------
                            # Detect AFD in the first lines of Thelier Type experiments
                            # -----------------------------------

                            no_treatments_yet = True
                            for t in experiment_treatments:
                                t = float(t.strip())
                                if t > 50:
                                    no_treatments_yet=False
                            if no_treatments_yet:
                                if meas_line['AF Demag/Remag Peak Field'] != "" and \
                                   float(meas_line['AF Demag/Remag Peak Field']) != 999 and \
                                   float(meas_line['AF Demag/Remag Peak Field']) != -99 and \
                                   float(meas_line['AF Demag/Remag Peak Field']) != 0:
                                    lab_treatment = "LT-AF-Z"
                                    MagRec[ac_field_col] = '%8.3e' % (
                                        float(meas_line['AF Demag/Remag Peak Field'])*1e-3)  # peak field in tesla

                            # -----------------------------------
                            # Thellier-Thellier protocol:
                            # -----------------------------------

                            if Experiment_Type in ['MW-PI-OT', 'MW-PI-OT+', 'TH-PI-OT', 'TH-PI-OT+']:
                                if Experiment_Type == 'MW-PI-OT+':
                                    lab_protocols_string = "LP-PI-M:LP-PI-II:LP-PI-M-II:LP-PI-ALT-PMRM"
                                elif Experiment_Type == 'MW-PI-OT':
                                    lab_protocols_string = "LP-PI-M:LP-PI-II:LP-PI-M-II"
                                # first line
                                if len(experiment_treatments) == 0 and lab_treatment == "":
                                    lab_treatment = "LT-NO"
                                # PMRM check
                                elif labfield != 0 and float(treatment) < float(experiment_treatments[-1]):
                                    lab_treatment = "LT-PMRM-I"
                                    if Experiment_Type != 'MW-PI-OT+':
                                        print("-W- WARNING sample %s: Check Experiment_Type ! it is %s, but a pTRM check is found."
                                              % (MagRec[spec_col], Experiment_Type))
                                else:
                                    lab_treatment = "LT-M-I"
                                # experiment_treatments.append(treatment)

                            # -----------------------------------
                            # Coe/Aitken/IZZI protocols:
                            # Coe: N/ZI/.../ZPI/.../ZIT/.../ZPIT/
                            # Aitken: N/IZ/.../IZP/.../ITZ/.../ITZP/
                            # IZZI: N/IZ/ZI/../ZPI/...ITZ/.../ZPIT/.../ITZP/...
                            # -----------------------------------

                            if Experiment_Type in ['MW-PI-C', 'MW-PI-C+', 'MW-PI-C++', 'MW-PI-IZZI', 'MW-PI-IZZI+', 'MW-PI-IZZI++', 'MW-PI-A', 'MW-PI-A+',
                                                   'TH-PI-C', 'TH-PI-C+', 'TH-PI-C++', 'TH-PI-IZZI', 'TH-PI-IZZI+', 'TH-PI-IZZI++', 'TH-PI-A', 'TH-PI-A+']:

                                if Experiment_Type == 'MW-PI-C++':
                                    lab_protocols_string = "LP-PI-M:LP-PI-ZI:LP-PI-M-ZI:LP-PI-ALT-PMRM:LP-PI-BT-MD"
                                elif Experiment_Type == 'MW-PI-C+':
                                    lab_protocols_string = "LP-PI-M:LP-PI-ZI:LP-PI-M-ZI:LP-PI-ALT-PMRM"
                                elif Experiment_Type == 'MW-PI-C':
                                    lab_protocols_string = "LP-PI-M:LP-PI-ZI:LP-PI-M-ZI"
                                elif Experiment_Type == 'MW-PI-IZZI++':
                                    lab_protocols_string = "LP-PI-M:LP-PI-BT-IZZI:LP-PI-ALT-PMRM:LP-PI-BT-MD"
                                elif Experiment_Type == 'MW-PI-IZZI+':
                                    lab_protocols_string = "LP-PI-M:LP-PI-BT-IZZI:LP-PI-ALT-PMRM"
                                elif Experiment_Type == 'MW-PI-IZZI':
                                    lab_protocols_string = "LP-PI-M:LP-PI-BT-IZZI"
                                elif Experiment_Type == 'MW-PI-A+':
                                    lab_protocols_string = "LP-PI-M:LP-PI-IZ:LP-PI-M-IZ:LP-PI-ALT-PMRM"
                                elif Experiment_Type == 'MW-PI-A':
                                    lab_protocols_string = "LP-PI-M:LP-PI-IZ:LP-PI-M-IZ"
                                elif Experiment_Type == 'TH-PI-C++':
                                    lab_protocols_string = "LP-PI-TRM:LP-PI-ZI:LP-PI-TRM-ZI:LP-PI-ALT-PTRM:LP-PI-BT-MD"
                                elif Experiment_Type == 'TH-PI-C+':
                                    lab_protocols_string = "LP-PI-TRM:LP-PI-ZI:LP-PI-TRM-ZI:LP-PI-ALT-PTRM"
                                elif Experiment_Type == 'TH-PI-C':
                                    lab_protocols_string = "LP-PI-TRM:LP-PI-ZI:LP-PI-TRM-ZI"
                                elif Experiment_Type == 'TH-PI-IZZI++':
                                    lab_protocols_string = "LP-PI-TRM:LP-PI-BT-IZZI:LP-PI-ALT-PTRM:LP-PI-BT-MD"
                                elif Experiment_Type == 'TH-PI-IZZI+':
                                    lab_protocols_string = "LP-PI-TRM:LP-PI-BT-IZZI:LP-PI-ALT-PTRM"
                                elif Experiment_Type == 'TH-PI-IZZI':
                                    lab_protocols_string = "LP-PI-TRM:LP-PI-BT-IZZI"
                                elif Experiment_Type == 'TH-PI-A+':
                                    lab_protocols_string = "LP-PI-TRM:LP-PI-IZ:LP-PI-TRM-IZ:LP-PI-ALT-PMRM"
                                elif Experiment_Type == 'TH-PI-A':
                                    lab_protocols_string = "LP-PI-TRM:LP-PI-IZ:LP-PI-TRM-IZ"
                                else:
                                    "-E- ERROR: cant understand protocol type"

                                if "TH-PI" in Experiment_Type:
                                    TH = True
                                    MW = False
                                else:
                                    TH = False
                                    MW = True

                                # -------------------------------------
                                # Special treatment for first line
                                # -------------------------------------

                                if len(experiment_treatments) == 0:
                                    if lab_treatment == "":
                                        lab_treatment = "LT-NO"
                                    elif float(lab_treatment) < 50:
                                        lab_treatment = "LT-NO"
                                    else:
                                        pass

                                # -------------------------------------
                                # Assigning Lab Treatment
                                # -------------------------------------

                                    # a flag for the current state (Z,I,ZP,T)
                                    IZorZI = ""
                                    # Coe:
                                else:
                                    if float(treatment) != 0:
                                        if labfield == 0 and treatment not in experiment_treatments:
                                            lab_treatment = "LT-M-Z"*MW + "LT-T-Z"*TH
                                            IZorZI = "Z"

                                        elif labfield == 0 and treatment in experiment_treatments:
                                            if IZorZI == 'I':
                                                lab_treatment = "LT-M-Z"*MW + "LT-T-Z"*TH
                                                IZorZI = ""
                                            else:
                                                lab_treatment = "LT-PMRM-MD"*MW + "LT-PTRM-MD"*TH

                                        elif labfield != 0 and treatment not in experiment_treatments:
                                            lab_treatment = "LT-M-I"*MW + "LT-T-I"*TH
                                            IZorZI = "I"

                                        elif labfield != 0 and treatment in experiment_treatments:
                                            # if IZorZI=='Z' or IZorZI=='':

                                            prev_treatment = treatment
                                            # print lab_treatments,"lab_treatments"
                                            # print experiment_treatments,"experiment_treatments"
                                            if len(experiment_treatments) > 2 and len(lab_treatments) > 2:
                                                for j in range(len(lab_treatments)-1, 0, -1):
                                                    if "LT-PTRM-I" in lab_treatments[j] or "LT-PMRM-I" in lab_treatments[j]:
                                                        continue
                                                    prev_treatment = experiment_treatments[j]
                                                    break
                                            # print "prev_treatment",prev_treatment
                                            # print "treatment",treatment

                                            if float(treatment) < float(prev_treatment):
                                                lab_treatment = "LT-PMRM-I"*MW + "LT-PTRM-I"*TH
                                                IZorZI == ''
                                            else:
                                                lab_treatment = "LT-M-I"*MW + "LT-T-I"*TH
                                                IZorZI = ""

                                        else:
                                            print("-E- ERROR. specimen %s. Cant relate step %s to the protocol" %
                                                  (MagRec[spec_col], treatment))

                                # check Step Type in the file and the deduced step from the program
                                if ((lab_treatment == "LT-M-I" or lab_treatment == "LT-T-I") and meas_line['Step Type'] != "I") or \
                                   ((lab_treatment == "LT-M-Z" or lab_treatment == "LT-T-Z") and meas_line['Step Type'] != "Z") or \
                                   ((lab_treatment == "LT-PMRM-I" or lab_treatment == "LT-PTRM-I") and meas_line['Step Type'] != "P") or \
                                   ((lab_treatment == "LT-PMRM-MD" or lab_treatment == "LT-PTRM-MD") and meas_line['Step Type'] != "T"):
                                    print("-W- WARNING sample %s treatment=%s. Step Type is %s but the program assumes %s"
                                          % (MagRec[spec_col], treatment, meas_line['Step Type'], lab_treatment))

                                # experiment_treatments.append(treatment)
                                lab_treatments.append(lab_treatment)
                            # -----------------------------------
                            # Perpendicular method: MW-PI-P :
                            # -----------------------------------

                            if Experiment_Type == 'MW-PI-P':
                                lab_protocols_string = "LP-PI-M:LP-PI-M-PERP"
                                if len(experiment_treatments) == 0:
                                    lab_treatment = "LT-NO"
                                if labfield == 0:
                                    lab_treatment = "LT-M-Z"
                                else:
                                    lab_treatment = "LT-M-I:LT-NRM-PERP"

                                # experiment_treatments.append(treatment)

                            # -----------------------------------
                            # MW demagnetization
                            # -----------------------------------

                            if Experiment_Type in ['MW-D']:
                                # first line
                                if len(experiment_treatments) == 0 and lab_treatment == "":
                                    if float(treatment) == 0:
                                        lab_treatment = "LT-NO"
                                    else:
                                        lab_treatment = "LT-M-Z"
                                else:
                                    lab_protocols_string = "LP-DIR-M"
                                    lab_treatment = "LT-M-Z"

                                # experiment_treatments.append(treatment)

                            # -----------------------------------
                            # Thermal demagnetization
                            # -----------------------------------

                            if Experiment_Type in ['TH-D']:
                                # first line
                                if len(experiment_treatments) == 0 and lab_treatment == "":
                                    if float(treatment) == 0:
                                        lab_treatment = "LT-NO"
                                    else:
                                        lab_treatment = "LT-T-Z"
                                else:
                                    lab_protocols_string = "LP-DIR-T"
                                    lab_treatment = "LT-T-Z"

                                # experiment_treatments.append(treatment)

                            # -----------------------------------
                            # AF demagnetization
                            # -----------------------------------

                            if Experiment_Type in ['AF-D']:
                                # first line
                                if len(experiment_treatments) == 0 and lab_treatment == "":
                                    if float(treatment) == 0:
                                        lab_treatment = "LT-NO"
                                    else:
                                        lab_treatment = "LT-AF-Z"
                                else:
                                    lab_protocols_string = "LP-DIR-AF"
                                    lab_treatment = "LT-AF-Z"

                            experiment_treatments.append(treatment)

                            # -----------------------------------

                            MagRec[methods_col] = lab_treatment + \
                                ":"+lab_protocols_string
                            MagRec[methods_col] = MagRec[methods_col].strip(':')
                            MagRec[experiment_col] = specimen + \
                                ":"+lab_protocols_string
                            if data_model_num == 3:
                                MagRec['measurement'] = MagRec[experiment_col] + "_" + MagRec[step_col]
                            MagRecs.append(MagRec)
                            measurement_running_number += 1
                            headers = list(MagRec.keys())
                            for key in headers:
                                if key not in measurement_headers:
                                    measurement_headers.append(
                                        key)

                    else:
                        print(
                            "-W- livdb.py does not support this experiment type yet.\n    Please report your issue on https://github.com/PmagPy/PmagPy/issues")

            # -----------------------------------
            # Convert Headers data to specimens
            # -----------------------------------

            for specimen in specimens_list:
                #print(specimen)
                Experiment_Types_list = list(Data[specimen].keys())
                Experiment_Types_list.sort()
                for Experiment_Type in Experiment_Types_list:
                    #print(Experiment_Type)
                    if Experiment_Type in supported_experiments:
                        header_line = Data[specimen][Experiment_Type]['header_data']
                        meas_first_line = Data[specimen][Experiment_Type]['meas_data'][0]
                        ErRec = {}
                        ErRec[citation_col] = "This study"
                        ErRec[spec_col] = header_line["Sample code"]
                        ErRec[samp_col] = get_sample_name(
                            ErRec[spec_col], [samp_name_con, samp_num_chars])
                        ErRec[site_col] = get_site_name(
                            ErRec[samp_col], [site_name_con, site_num_chars])
                        ErRec[loc_col] = location_name

                        ErRec[spec_type_col] = "Not Specified"
                        ErRec[spec_lithology_col] = "Not Specified"
                        ErRec[spec_class_col] = "Not Specified"

                        ErRec[spec_dip_col] = header_line['Sample Dip']
                        if float(ErRec[spec_dip_col]) == 99:
                            ErRec[spec_dip_col] = ""
                        ErRec[spec_azimuth_col] = header_line['Sample Dec']
                        if float(ErRec[spec_azimuth_col]) == 999:
                            ErRec[spec_azimuth_col] = ""
                        ErRec[spec_height_col] = header_line['Height']
                        ErRec[spec_descr_col] = header_line['Specimen/Experiment Comment']
                        try:
                            ErRec[spec_vol_col] = "%f" % float(
                                header_line['Sample Volume'])*1e-6
                        except:
                            ErRec[spec_vol_col] = ""

                        ErRec[spec_density_col] = header_line['Sample Density']

                        ErRecs.append(ErRec)
                        headers = list(ErRec.keys())
                        for key in headers:
                            if key not in specimen_headers:
                                specimen_headers.append(key)


    fin.close()
    # -------------------------------------------
    #  measurements.txt
    # -------------------------------------------

    meas_out = pmag.resolve_file_name(meas_out, output_dir_path)
    pmag.magic_write(meas_out, MagRecs, meas_type)

    # -------------------------------------------
    #  specimens.txt
    # -------------------------------------------

    spec_out = pmag.resolve_file_name(spec_out, output_dir_path)
    pmag.magic_write(spec_out, ErRecs, spec_type)

    # propagate samples/specimens/sites/locations to their own files
    custom_filenames = {'measurements': meas_out, 'specimens': spec_out,
                        'samples': samp_out, 'sites': site_out,
                        'locations': loc_out}
    con = cb.Contribution(output_dir_path, custom_filenames=custom_filenames)
    con.propagate_measurement_info()
    # remove invalid columns
    con.remove_non_magic_cols()
    # write all data out to file
    for dtype in con.tables:
        con.write_table_to_file(dtype)

    return True, meas_out

    # -------------------------------------------



# MINI_magic conversion

def mini(magfile, dir_path='.', meas_file='measurements.txt',
         data_model_num=3, volume=12, noave=0,
         inst="", user="", methcode="LP-NO", input_dir_path=""):
    """
    Convert the Yale minispin format to MagIC format files

    Parameters
    ----------
    magfile : str
        input file name, required
    dir_path : str
        working directory, default "."
    meas_file : str
        output measurement file name, default "measurements.txt"
    data_model_num : int
        MagIC data model 2 or 3, default 3
    volume : float
        volume in ccs, default 12.
    noave : bool
       do not average duplicate measurements, default False (so by default, DO average)
    inst : str
        instrument, default ""
    user : str
        user name, default ""
    methcode : str
        colon-delimited protocols, include all that apply
        default "LP-NO"
        options include "AF" for demag and "T" for thermal
    input_dir_path : str,
        input file directory IF different from dir_path, default ""

    Returns
    ---------
    Tuple : (True or False indicating if conversion was successful, meas_file name written)

    """

    codes = methcode.split(':')
    demag = "N"
    if "AF" in codes:
        demag = 'AF'
        methcode = "LT-AF-Z"
    if "T" in codes:
        demag = "T"
        methcode = "LP-TRM-TD"

    # initialize
    citation = 'This study'
    MagRecs = []
    version_num = pmag.get_version()
    input_dir_path, dir_path = pmag.fix_directories(input_dir_path, dir_path)
    magfile = pmag.resolve_file_name(magfile, input_dir_path)
    input_dir_path = os.path.split(magfile)[0]
    try:
        with open(magfile, 'r') as finput:
            lines = finput.readlines()
    except OSError:
        print("bad mag file name")
        return False, "bad mag file name"
    # convert volume
    volume = 1e-6 * float(volume)
    # set col names based on MagIC 2 or 3
    if data_model_num == 2:
        spec_col = "er_specimen_name"
        loc_col = "er_location_name"
        site_col = "er_site_col"
        samp_col = "er_sample_name"
        software_col = "magic_software_packages"
        treat_temp_col = "treatment_temp"
        meas_temp_col = "measurement_temp"
        treat_ac_col = "treatment_ac_field"
        treat_dc_col = "treatment_dc_field"
        treat_dc_phi_col = "treatment_dc_field_phi"
        treat_dc_theta_col = "treatment_dc_field_theta"
        moment_col = "measurement_magn_moment"
        dec_col = "measurement_dec"
        inc_col = "measurement_inc"
        instrument_col = "magic_instrument_codes"
        analyst_col = "er_analyst_mail_names"
        citations_col = "er_citation_names"
        methods_col = "magic_method_codes"
        quality_col = "measurement_flag"
        meas_standard_col = "measurement_standard"
        meas_name_col = "measurement_number"
    else:
        spec_col = "specimen"
        loc_col = "location"
        site_col = "site"
        samp_col = "sample"
        software_col = "software_packages"
        treat_temp_col = "treat_temp"
        meas_temp_col = "meas_temp"
        treat_ac_col = "treat_ac_field"
        treat_dc_col = "treat_dc_field"
        treat_dc_phi_col = "treat_dc_field_phi"
        treat_dc_theta_col = "treat_dc_field_theta"
        moment_col = "magn_moment"
        dec_col = "dir_dec"
        inc_col = "dir_inc"
        instrument_col = "instrument_codes"
        analyst_col = "analysts"
        citations_col = "citations"
        methods_col = "method_codes"
        quality_col = "quality"
        meas_standard_col = "standard"
        meas_name_col = "experiment"
        meas_seq_col = "sequence"

    # go through the measurements
    seq=1
    for line in lines:
        rec = line.split(',')
        if len(rec) > 1:
            MagRec = {}
            IDs = rec[0].split('_')
            treat = IDs[1]
            MagRec[spec_col] = IDs[0]
            # print(MagRec[spec_col])
            sids = IDs[0].split('-')
            MagRec[loc_col] = sids[0]
            MagRec[site_col] = sids[0]+'-'+sids[1]
            if len(sids) == 2:
                MagRec[samp_col] = IDs[0]
            else:
                MagRec[samp_col] = sids[0]+'-'+sids[1]+'-'+sids[2]
            # print(MagRec)
            MagRec[software_col] = version_num
            MagRec[treat_temp_col] = '%8.3e' % (273)  # room temp in kelvin
            MagRec[meas_temp_col] = '%8.3e' % (273)  # room temp in kelvin
            MagRec[treat_ac_col] = '0'
            MagRec[treat_dc_col] = '0'
            MagRec[treat_dc_phi_col] = '0'
            MagRec[treat_dc_theta_col] = '0'
            meas_type = "LT-NO"
            if demag == "AF":
                MagRec[treat_ac_col] = '%8.3e' % (
                    float(treat)*1e-3)  # peak field in tesla
            if demag == "T":
                meas_type = "LT-T-Z"
                MagRec[treat_dc_col] = '%8.3e' % (0)
                MagRec[treat_ac_col] = '0'
                MagRec[treat_temp_col] = '%8.3e' % (
                    float(treat)+273.)  # temp in kelvin
            if demag == "N":
                meas_type = "LT-NO"
                MagRec[treat_ac_col] = '0'
                MagRec[treat_dc_col] = '0'
            MagRec[moment_col] = '%10.3e' % (
                volume*float(rec[3])*1e-3)  # moment in Am2 (from mA/m)
            MagRec[dec_col] = rec[1]
            MagRec[inc_col] = rec[2]
            MagRec[instrument_col] = inst
            MagRec[analyst_col] = user
            MagRec[citations_col] = citation
            MagRec[methods_col] = methcode.strip(':')
            MagRec[quality_col] = 'g'
            MagRec[meas_standard_col] = 'u'
            MagRec[meas_name_col] = '1'
            MagRecs.append(MagRec)

    if data_model_num == 2:
        MagOuts = pmag.measurements_methods(MagRecs, noave)
        pmag.magic_write(meas_file, MagOuts, 'magic_measurements')
    else:
        MagOuts = pmag.measurements_methods3(MagRecs, noave)
        pmag.magic_write(meas_file, MagOuts, 'measurements')
        # nicely parse all the specimen/sample/site/location data
        # and write it to file as well
        dir_path = os.path.split(meas_file)[0]
        con = cb.Contribution(dir_path, read_tables=['measurements'],
                              custom_filenames={'measurements': meas_file})
        con.propagate_measurement_info()
        for table in con.tables:
            con.write_table_to_file(table)
    print("results put in ", meas_file)
    return True, meas_file

### MsT_magic conversion

def mst(infile, spec_name='unknown', dir_path=".", input_dir_path="",
        meas_file="measurements.txt", samp_infile="samples.txt",
        user="", specnum=0, samp_con="1", labfield=0.5,
        location='unknown', syn=False, data_model_num=3):
    """
    Convert MsT data (T,M) to MagIC measurements format files

    Parameters
    ----------
    infile : str
        input file name
    specimen : str
        specimen name, default "unknown"
    dir_path : str
        working directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    meas_file : str
        output measurement file name, default "measurements.txt"
    samp_infile : str
        existing sample infile (not required), default "samples.txt"
    user : str
        user name, default ""
    specnum : int
        number of characters to designate a specimen, default 0
    samp_con : str
        sample/site naming convention, default '1', see info below
    labfield : float
        DC_FIELD in Tesla, default : .5
    location : str
        location name, default "unknown"
    syn : bool
       synthetic, default False
    data_model_num : int
        MagIC data model 2 or 3, default 3

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful, file name written)


    Info
    --------
    Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY

    """

    # deal with input files
    input_dir_path, dir_path = pmag.fix_directories(input_dir_path, dir_path)
    try:
        infile = pmag.resolve_file_name(infile, input_dir_path)
        with open(infile, 'r') as finput:
            data = finput.readlines()
    except (IOError, FileNotFoundError) as ex:
        print(ex)
        print("bad mag file name")
        return False, "bad mag file name"

    samp_file = pmag.resolve_file_name(samp_infile, input_dir_path)
    if os.path.exists(samp_file):
        Samps, file_type = pmag.magic_read(samp_file)
    else:
        Samps = []

    # parse out samp_con
    if "4" in samp_con:
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "4"
    if "7" in samp_con:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "7"

    # initialize some stuff
    specnum = - int(specnum)
    Z = "0"
    citation = 'This study'
    measnum = 1
    MagRecs, specs = [], []
    version_num = pmag.get_version()

    if data_model_num == 2:
        loc_col = "er_location_name"
        software_col = "magic_software_packages"
        treat_dc_col = "treatment_dc_field"
        meas_temp_col = "measurement_temp"
        meth_codes_col = "magic_method_codes"
        meas_magnitude_col = "measurement_magnitude"
        spec_col = "er_specimen_name"
        samp_col = "er_sample_name"
        site_col = "er_site_name"
        synthetic_name_col = "er_synthetic_name"
        inst_col = "magic_instrument_codes"
        analyst_col = "er_analyst_mail_names"
        citation_col = "er_citation_names"
        quality_col = "measurement_flag"
        meas_name_col = "measurement_number"
        experiment_col = "magic_experiment_name"
        meas_file_type = "magic_measurements"
        if meas_file == "measurements.txt":
            meas_file = "magic_measurements.txt"
    else:
        loc_col = "location"
        software_col = "software_packages"
        treat_dc_col = "treat_dc_field"
        meas_temp_col = "meas_temp"
        meth_codes_col = "method_codes"
        meas_magnitude_col = "magn_uncal"
        spec_col = "specimen"
        samp_col = "sample"
        site_col = "site"
        synthetic_name_col = "specimen"
        inst_col = "instrument_codes"
        analyst_col = "analysts"
        citation_col = "citations"
        quality_col = "quality"
        meas_name_col = "measurement"
        experiment_col = "experiment"
        meas_file_type = "measurements"

    meas_file = pmag.resolve_file_name(meas_file, dir_path)
    dir_path = os.path.split(meas_file)[0]

    T0 = float(data[0].split()[0])
    for line in data:
        instcode = ""
        if len(line) > 1:
            MagRec = {}
            if syn == 0:
                MagRec[loc_col] = location
            MagRec[software_col] = version_num
            MagRec[treat_dc_col] = labfield
            rec = line.split()
            T = float(rec[0])
            MagRec[meas_temp_col] = '%8.3e' % (
                float(rec[0])+273.)  # temp in kelvin
            if T > T0:
                MagRec[meth_codes_col] = 'LP-MW-I'
            elif T < T0:
                MagRec[meth_codes_col] = 'LP-MC-I'
                T0 = T
            elif data.index(line) == 0: # NRM step
                MagRec[meth_codes_col] = "LP-NO"
            else:
                print('skipping repeated temperature step')
                MagRec[meth_codes_col] = ''
            T0 = T
            MagRec[meas_magnitude_col] = '%10.3e' % (
                float(rec[1]))  # uncalibrated magnitude
            if syn == 0:
                MagRec[spec_col] = spec_name
                MagRec[site_col] = ""
                if specnum != 0:
                    MagRec[samp_col] = spec_name[:specnum]
                else:
                    MagRec[samp_col] = spec_name
                if Samps:
                    for samp in Samps:
                        if samp[samp_col] == MagRec[samp_col]:
                            MagRec[loc_col] = samp.get(loc_col, location)
                            MagRec[site_col] = samp[site_col]
                            break
                elif int(samp_con) != 6:
                    site = pmag.parse_site(
                        MagRec[samp_col], samp_con, Z)
                    MagRec[site_col] = site
                if MagRec[site_col] == "":
                    print('No site name found for: ',
                          MagRec[spec_col], MagRec[samp_col])
                if not MagRec[loc_col]:
                    print('no location name for: ', MagRec[spec_col])
            else: # synthetic
                MagRec[loc_col] = ""
                MagRec[samp_col] = ""
                MagRec[site_col] = ""
                MagRec[spec_col] = ""
                MagRec[synthetic_name_col] = spec_name

            MagRec[inst_col] = instcode
            MagRec[analyst_col] = user
            MagRec[citation_col] = citation
            MagRec[quality_col] = 'g'
            MagRec[meas_name_col] = str(measnum)
            if data_model_num == 3:
                MagRec['sequence'] = measnum
            MagRecs.append(MagRec)
            measnum += 1
    new_MagRecs = []
    for rec in MagRecs:  # sort out the measurements by experiment type
        rec[experiment_col] = spec_name
        if rec[meth_codes_col] == 'LP-MW-I':
            rec[experiment_col] = spec_name + ':LP-MW-I:Curie'
        elif rec[meth_codes_col] == 'LP-MC-I':
            rec[experiment_col] = spec_name +':LP-MC-I'
        elif rec[meth_codes_col] == "LP-NO":
            rec[experiment_col] = spec_name + ":LP-NO"
        if data_model_num == 3:
            rec[meas_name_col] = rec[experiment_col] + "_" + rec[meas_name_col]
        new_MagRecs.append(rec)

    pmag.magic_write(meas_file, new_MagRecs, meas_file_type)
    print("results put in ", meas_file)
    # try to extract location/site/sample/specimen info into tables
    con = cb.Contribution(dir_path)
    con.propagate_measurement_info()
    for table in con.tables:
        if table in ['samples', 'sites', 'locations']:
            # add in location name by hand
            if table == 'sites':
                con.tables['sites'].df['location'] = location
            con.write_table_to_file(table)

    return True, meas_file



### PMD_magic conversion

def pmd(mag_file, dir_path=".", input_dir_path="",
        meas_file="measurements.txt", spec_file='specimens.txt',
        samp_file='samples.txt', site_file="sites.txt", loc_file="locations.txt",
        lat="", lon="", specnum=0, samp_con='1', location="unknown",
        noave=0, meth_code="LP-NO"):
    """
    converts PMD (Enkin)  format files to MagIC format files

    Parameters
    ----------
    mag_file : str
        input file name, required
    dir_path : str
        working directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    spec_file : str
        output specimen file name, default "specimens.txt"
    samp_file: str
        output sample file name, default "samples.txt"
    site_file : str
        output site file name, default "sites.txt"
    loc_file : str
        output location file name, default "locations.txt"
    lat : float or str
        latitude, default ""
    lon : float or str
        longitude, default ""
    specnum : int
        number of characters to designate a specimen, default 0
    samp_con : str
        sample/site naming convention, default '1', see info below
    location : str
        location name, default "unknown"
    noave : bool
       do not average duplicate measurements, default False (so by default, DO average)
    meth_code : str
        default "LP-NO"
        e.g. [SO-MAG, SO-SUN, SO-SIGHT, ...]

    Returns
    ---------
    Tuple : (True or False indicating if conversion was successful, file name written)


    Info
    --------
    Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY


    """
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    specnum = - int(specnum)
    samp_con = str(samp_con)
    version_num = pmag.get_version()

    if "4" in samp_con:
        if "-" not in samp_con:
            print(
                "naming convention option [4] must be in form 4-Z where Z is an integer")
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "4"
    elif "7" in samp_con:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "7"
    else:
        Z = 1

    # format variables
    mag_file = pmag.resolve_file_name(mag_file, input_dir_path)
    meas_file = pmag.resolve_file_name(meas_file, output_dir_path)
    spec_file = pmag.resolve_file_name(spec_file, output_dir_path)
    samp_file = pmag.resolve_file_name(samp_file, output_dir_path)
    site_file = pmag.resolve_file_name(site_file, output_dir_path)

    # parse data
    try:
        with open(mag_file, 'r') as f:
            data = f.readlines()
    except IOError:
        print('mag_file field is required option')
        return False, 'mag_file field is required option'
    comment = data[0]
    line = data[1].strip()
    line = line.replace("=", "= ")  # make finding orientations easier
    rec = line.split()  # read in sample orientation, etc.
    specimen = rec[0]
    SpecRecs, SampRecs, SiteRecs, LocRecs, MeasRecs = [], [], [], [], []
    SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}  # make a  sample record
    if specnum != 0:
        sample = rec[0][:specnum]
    else:
        sample = rec[0]
    if int(samp_con) < 6:
        site = pmag.parse_site(sample, samp_con, Z)
    else:
        if 'site' in list(SampRec.keys()):
            site = ErSampREc['site']
        if 'location' in list(SampRec.keys()):
            location = ErSampREc['location']
    az_ind = rec.index('a=')+1
    SampRec['sample'] = sample
    SampRec['description'] = comment.replace('\n', '').replace('\t', '')
    SampRec['azimuth'] = rec[az_ind]
    dip_ind = rec.index('b=')+1
    dip = -float(rec[dip_ind])
    SampRec['dip'] = '%7.1f' % (dip)
    strike_ind = rec.index('s=')+1
    SampRec['bed_dip_direction'] = '%7.1f' % (float(rec[strike_ind])+90.)
    bd_ind = rec.index('d=')+1
    SampRec['bed_dip'] = rec[bd_ind]
    v_ind = rec.index('v=')+1
    vol = rec[v_ind][:-3]
    date = rec[-2]
    time = rec[-1]
    SampRec['method_codes'] = meth_code
    SampRec['site'] = site
    SampRec['citations'] = 'This study'
    SampRec['method_codes'] = 'SO-NO'

    SpecRec['specimen'] = specimen
    SpecRec['sample'] = sample
    SpecRec['citations'] = 'This study'

    SiteRec['site'] = site
    SiteRec['location'] = location
    SiteRec['citations'] = 'This study'
    SiteRec['lat'] = lat
    SiteRec['lon'] = lon

    LocRec['location'] = location
    LocRec['citations'] = 'This study'
    LocRec['lat_n'] = lat
    LocRec['lat_s'] = lat
    LocRec['lon_e'] = lon
    LocRec['lon_w'] = lon

    SpecRecs.append(SpecRec)
    SampRecs.append(SampRec)
    SiteRecs.append(SiteRec)
    LocRecs.append(LocRec)
    for k in range(3, len(data)):  # read in data
        line = data[k]
        rec = line.split()
        if len(rec) > 1:  # skip blank lines at bottom
            MeasRec = {}
            MeasRec['description'] = 'Date: '+date+' '+time
            MeasRec["citations"] = "This study"
            MeasRec['software_packages'] = version_num
            MeasRec["treat_temp"] = '%8.3e' % (273)  # room temp in kelvin
            MeasRec["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
            MeasRec["quality"] = 'g'
            MeasRec["standard"] = 'u'
            MeasRec["treat_step_num"] = 0
            MeasRec["specimen"] = specimen
            if rec[0] == 'NRM':
                meas_type = "LT-NO"
            elif rec[0][0] == 'M' or rec[0][0] == 'H':
                meas_type = "LT-AF-Z"
            elif rec[0][0] == 'T':
                meas_type = "LT-T-Z"
            else:
                print("measurement type unknown")
                return False, "measurement type unknown"
            X = [float(rec[1]), float(rec[2]), float(rec[3])]
            Vec = pmag.cart2dir(X)
            MeasRec["magn_moment"] = '%10.3e' % (Vec[2])  # Am^2
            MeasRec["magn_volume"] = rec[4]  # A/m
            MeasRec["dir_dec"] = '%7.1f' % (Vec[0])
            MeasRec["dir_inc"] = '%7.1f' % (Vec[1])
            MeasRec["treat_ac_field"] = '0'
            if meas_type != 'LT-NO':
                treat = float(rec[0][1:])
            else:
                treat = 0
            if meas_type == "LT-AF-Z":
                MeasRec["treat_ac_field"] = '%8.3e' % (
                    treat*1e-3)  # convert from mT to tesla
            elif meas_type == "LT-T-Z":
                MeasRec["treat_temp"] = '%8.3e' % (
                    treat+273.)  # temp in kelvin
            MeasRec['method_codes'] = meas_type
            MeasRecs.append(MeasRec)

    con = cb.Contribution(output_dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.tables['specimens'].write_magic_file(custom_name=spec_file,dir_path=dir_path)
    con.tables['samples'].write_magic_file(custom_name=samp_file,dir_path=dir_path)
    con.tables['sites'].write_magic_file(custom_name=site_file,dir_path=dir_path)
    con.tables['locations'].write_magic_file(custom_name=loc_file,dir_path=dir_path)
    con.tables['measurements'].write_magic_file(custom_name=meas_file,dir_path=dir_path)

    return True, meas_file


### SIO_magic conversion

def sio(mag_file, dir_path=".", input_dir_path="",
        meas_file="measurements.txt", spec_file="specimens.txt",
        samp_file="samples.txt", site_file="sites.txt", loc_file="locations.txt",
        samp_infile="", institution="", syn=False, syntype="", instrument="",
        labfield=0, phi=0, theta=0, peakfield=0,
        specnum=0, samp_con='1', location="unknown", lat="", lon="",
        noave=False, codelist="", cooling_rates="", coil='', timezone="UTC",
        user=""):
    """
    converts Scripps Institution of Oceanography measurement files to MagIC data base model 3.0

    Parameters
    _________
    magfile : input measurement file
    dir_path : output directory path, default "."
    input_dir_path : input file directory IF different from dir_path, default ""
    meas_file : output file measurement file name, default "measurements.txt"
    spec_file : output file specimen file name, default "specimens.txt"
    samp_file : output file sample file name, default "samples.tt"
    site_file : output file site file name, default "sites.txt"
    loc_file : output file location file name, default "locations.txt"
    samp_infile : output file to append to, default ""
    syn : if True, this is a synthetic specimen, default False
    syntype :  sample material type, default ""
    instrument : instrument on which the measurements were made (e.g., "SIO-2G"), default ""
    labfield : lab field in microtesla for TRM, default 0
    phi, theta : direction of lab field [-1,-1 for anisotropy experiments], default 0, 0
    peakfield : peak af field in mT for ARM, default 0
    specnum : number of terminal characters distinguishing specimen from sample, default 0
    samp_con :  sample/site naming convention, default '1'
            "1" XXXXY: where XXXX is an arbitr[ary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            "2" XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
            "3" XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
            "4-Z" XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            "5" site name same as sample
            "6" site is entered under a separate column NOT CURRENTLY SUPPORTED
            "7-Z" [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.

            "8" synthetic - has no site name
            "9" ODP naming convention
    location : location name for study, default "unknown"
    lat : latitude of sites, default ""
    lon : longitude of sites, default ""
    noave : boolean, if False, average replicates, default False
    codelist : colon delimited string of lab protocols (e.g., codelist="AF"), default ""
        AF:  af demag
        T: thermal including thellier but not trm acquisition
        S: Shaw method
        I: IRM (acquisition)
        N: NRM only
        TRM: trm acquisition
        ANI: anisotropy experiment
        D: double AF demag
        G: triple AF demag (GRM protocol)
        CR: cooling rate experiment.
            The treatment coding of the measurement file should be: XXX.00,XXX.10, XXX.20 ...XX.70 etc. (XXX.00 is optional)
            where XXX in the temperature and .10,.20... are running numbers of the cooling rates steps.
            XXX.00 is optional zerofield baseline. XXX.70 is alteration check.
            syntax in sio_magic is: -LP CR xxx,yyy,zzz,..... xxx -A
            where xxx, yyy, zzz...xxx  are cooling time in [K/minutes], separated by comma, ordered at the same order as XXX.10,XXX.20 ...XX.70
            if you use a zerofield step then no need to specify the cooling rate for the zerofield
            It is important to add to the command line the -A option so the measurements will not be averaged.
            But users need to make sure that there are no duplicate measurements in the file
    cooling_rates :  cooling rate in K/sec for cooling rate dependence studies (K/minutes)
            in comma separated list for each cooling rate (e.g., "43.6,1.3,43.6")
    coil : 1,2, or 3 unist of IRM field in volts using ASC coil #1,2 or 3
        the fast and slow experiments in comma separated string (e.g., fast:  43.6 K/min,  slow:  1.3 K/min)
    timezone : timezone of date/time string in comment string, default "UTC"
    user : analyst, default ""

    Effects
    _______
    creates MagIC formatted tables
    """

    # initialize some stuff
    methcode = "LP-NO"
    pTRM, MD = 0, 0
    dec = [315, 225, 180, 135, 45, 90, 270, 270, 270, 90, 180, 180, 0, 0, 0]
    inc = [0, 0, 0, 0, 0, -45, -45, 0, 45, 45, 45, -45, -90, -45, 45]
    tdec = [0, 90, 0, 180, 270, 0, 0, 90, 0]
    tinc = [0, 0, 90, 0, 0, -90, 0, 0, 90]
    missing = 1
    demag = "N"
    citations = 'This study'
    fmt = 'old'
    Samps = []
    trm = 0
    irm = 0

    # get args
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    # measurement outfile
    meas_file = pmag.resolve_file_name(meas_file, output_dir_path)
    spec_file = pmag.resolve_file_name(spec_file, output_dir_path)
    samp_file = pmag.resolve_file_name(samp_file, output_dir_path)
    site_file = pmag.resolve_file_name(site_file, output_dir_path)
    loc_file = pmag.resolve_file_name(loc_file, output_dir_path)
    mag_file = pmag.resolve_file_name(mag_file, input_dir_path)
    labfield = float(labfield) * 1e-6
    phi = float(phi)
    theta = float(theta)
    peakfield = float(peakfield) * 1e-3
    specnum = int(specnum)
    samp_con = str(samp_con)

    # make sure all initial values are correctly set up (whether they come from the command line or a GUI)
    if samp_infile:
        Samps, file_type = pmag.magic_read(samp_infile)
    if coil:
        coil = str(coil)
        methcode = "LP-IRM"
        irmunits = "V"
        if coil not in ["1", "2", "3"]:
            print(__doc__)
            print('not a valid coil specification')
            return False, '{} is not a valid coil specification'.format(coil)
    if mag_file:
        lines = pmag.open_file(mag_file)
        if not lines:
            print("you must provide a valid mag_file")
            return False, "you must provide a valid mag_file"
    if not mag_file:
        print(__doc__)
        print("mag_file field is required option")
        return False, "mag_file field is required option"
    if specnum != 0:
        specnum = -specnum
    if "4" == samp_con[0]:
        if "-" not in samp_con:
            print(
                "naming convention option [4] must be in form 4-Z where Z is an integer")
            print('---------------')
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "4"
    if "7" == samp_con[0]:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "7"
    else:
        Z = 0

    if codelist:
        codes = codelist.split(':')
        if "AF" in codes:
            demag = 'AF'
            if'-dc' not in sys.argv:
                methcode = "LT-AF-Z"
            if'-dc' in sys.argv:
                methcode = "LT-AF-I"
        if "T" in codes:
            demag = "T"
            if '-dc' not in sys.argv:
                methcode = "LT-T-Z"
            if '-dc' in sys.argv:
                methcode = "LT-T-I"
        if "I" in codes:
            methcode = "LP-IRM"
            irmunits = "mT"
        if "I3d" in codes:
            methcode = "LT-T-Z:LP-IRM-3D"
        if "S" in codes:
            demag = "S"
            methcode = "LP-PI-TRM:LP-PI-ALT-AFARM"
            trm_labfield = labfield
            ans = input("DC lab field for ARM step: [50uT] ")
            if ans == "":
                arm_labfield = 50e-6
            else:
                arm_labfield = float(ans)*1e-6
            ans = input("temperature for total trm step: [600 C] ")
            if ans == "":
                trm_peakT = 600+273  # convert to kelvin
            else:
                trm_peakT = float(ans)+273  # convert to kelvin
        if "G" in codes:
            methcode = "LT-AF-G"
        if "D" in codes:
            methcode = "LT-AF-D"
        if "TRM" in codes:
            demag = "T"
            trm = 1
        if "CR" in codes:
            demag = "T"
            cooling_rate_experiment = 1
            # command_line does not exist in this code
            cooling_rates_list = cooling_rates.split(',')
            # if command_line:
            #    ind=sys.argv.index("CR")
            #    cooling_rates=sys.argv[ind+1]
            #    cooling_rates_list=cooling_rates.split(',')
            # else:
            #    cooling_rates_list=str(cooling_rates).split(',')
    if demag == "T" and "ANI" in codes:
        methcode = "LP-AN-TRM"
    if demag == "T" and "CR" in codes:
        methcode = "LP-CR-TRM"
    if demag == "AF" and "ANI" in codes:
        methcode = "LP-AN-ARM"
        if labfield == 0:
            labfield = 50e-6
        if peakfield == 0:
            peakfield = .180

    MeasRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    version_num = pmag.get_version()

    ##################################

    for line in lines:
        instcode = ""
        if len(line) > 2:
            MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}
            MeasRec['software_packages'] = version_num
            MeasRec["description"] = ""
            MeasRec["treat_temp"] = '%8.3e' % (273)  # room temp in kelvin
            MeasRec["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
            MeasRec["treat_ac_field"] = '0'
            MeasRec["treat_dc_field"] = '0'
            MeasRec["treat_dc_field_phi"] = '0'
            MeasRec["treat_dc_field_theta"] = '0'
            meas_type = "LT-NO"
            rec = line.split()
            #try:
            #    float(rec[0])
            #    print("No specimen name for line #%d in the measurement file" %
            #          lines.index(line))
            #    continue
            #except ValueError:
            #    pass
            if rec[1] == ".00":
                rec[1] = "0.00"
            treat = rec[1].split('.')
            if methcode == "LP-IRM":
                if irmunits == 'mT':
                    labfield = float(treat[0])*1e-3
                else:
                    labfield = pmag.getfield(irmunits, coil, treat[0])
                if rec[1][0] != "-":
                    phi, theta = 0., 90.
                else:
                    phi, theta = 0., -90.
                meas_type = "LT-IRM"
                MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                MeasRec["treat_dc_field_phi"] = '%7.1f' % (phi)
                MeasRec["treat_dc_field_theta"] = '%7.1f' % (theta)
            if len(rec) > 6:
                # break e.g., 10/15/02;7:45 indo date and time
                code1 = rec[6].split(';')
                if len(code1) == 2:  # old format with AM/PM
                    missing = 0
                    code2 = code1[0].split('/')  # break date into mon/day/year
                    # break e.g., AM;C34;200  into time;instr/axes/measuring pos;number of measurements
                    code3 = rec[7].split(';')
                    yy = int(code2[2])
                    if yy < 90:
                        yyyy = str(2000+yy)
                    else:
                        yyyy = str(1900+yy)
                    mm = int(code2[0])
                    if mm < 10:
                        mm = "0"+str(mm)
                    else:
                        mm = str(mm)
                    dd = int(code2[1])
                    if dd < 10:
                        dd = "0"+str(dd)
                    else:
                        dd = str(dd)
                    time = code1[1].split(':')
                    hh = int(time[0])
                    if code3[0] == "PM" and hh<12:
                        hh = hh+12
                    if hh < 10:
                        hh = "0"+str(hh)
                    else:
                        hh = str(hh)
                    min = int(time[1])
                    if min < 10:
                        min = "0"+str(min)
                    else:
                        min = str(min)
                    dt = yyyy+":"+mm+":"+dd+":"+hh+":"+min+":00"
                    local = pytz.timezone(timezone)
                    naive = datetime.datetime.strptime(dt, "%Y:%m:%d:%H:%M:%S")
                    local_dt = local.localize(naive, is_dst=None)
                    utc_dt = local_dt.astimezone(pytz.utc)
                    MeasRec["timestamp"] = utc_dt.strftime(
                        "%Y-%m-%dT%H:%M:%S")+"Z"
                    if instrument == "":
                        if code3[1][0] == 'C':
                            instcode = 'SIO-bubba'
                        if code3[1][0] == 'G':
                            instcode = 'SIO-flo'
                    else:
                        instcode = ''
                    MeasRec["meas_n_orient"] = code3[1][2]
                elif len(code1) > 2:  # newest format (cryo7 or later)
                    if "LP-AN-ARM" not in methcode:
                        labfield = 0
                    fmt = 'new'
                    date = code1[0].split('/')  # break date into mon/day/year
                    yy = int(date[2])
                    if yy < 90:
                        yyyy = str(2000+yy)
                    else:
                        yyyy = str(1900+yy)
                    mm = int(date[0])
                    if mm < 10:
                        mm = "0"+str(mm)
                    else:
                        mm = str(mm)
                    dd = int(date[1])
                    if dd < 10:
                        dd = "0"+str(dd)
                    else:
                        dd = str(dd)
                    time = code1[1].split(':')
                    hh = int(time[0])
                    if hh < 10:
                        hh = "0"+str(hh)
                    else:
                        hh = str(hh)
                    min = int(time[1])
                    if min < 10:
                        min = "0"+str(min)
                    else:
                        min = str(min)
                    dt = yyyy+":"+mm+":"+dd+":"+hh+":"+min+":00"
                    local = pytz.timezone(timezone)
                    naive = datetime.datetime.strptime(dt, "%Y:%m:%d:%H:%M:%S")
                    local_dt = local.localize(naive, is_dst=None)
                    utc_dt = local_dt.astimezone(pytz.utc)
                    MeasRec["timestamp"] = utc_dt.strftime(
                        "%Y-%m-%dT%H:%M:%S")+"Z"
                    if instrument == "":
                        if code1[6][0] == 'C':
                            instcode = 'SIO-bubba'
                        if code1[6][0] == 'G':
                            instcode = 'SIO-flo'
                    else:
                        instcode = ''
                    if len(code1) > 1:
                        MeasRec["meas_n_orient"] = code1[6][2]
                    else:
                        # takes care of awkward format with bubba and flo being different
                        MeasRec["meas_n_orient"] = code1[7]
                    if user == "":
                        user = code1[5]
                    if code1[2][-1].upper() == 'C':
                        demag = "T"
                        if code1[4] == 'microT' and float(code1[3]) != 0. and "LP-AN-ARM" not in methcode:
                            labfield = float(code1[3])*1e-6
                    if code1[2] == 'mT' and methcode != "LP-IRM":
                        demag = "AF"
                        if code1[4] == 'microT' and float(code1[3]) != 0.:
                            labfield = float(code1[3])*1e-6
                    if code1[4] == 'microT' and labfield != 0. and meas_type != "LT-IRM":
                        phi, theta = 0., -90.
                        if demag == "T":
                            meas_type = "LT-T-I"
                        if demag == "AF":
                            meas_type = "LT-AF-I"
                        MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                        MeasRec["treat_dc_field_phi"] = '%7.1f' % (phi)
                        MeasRec["treat_dc_field_theta"] = '%7.1f' % (theta)
                    if code1[4] == '' or labfield == 0. and meas_type != "LT-IRM":
                        if demag == 'T':
                            meas_type = "LT-T-Z"
                        if demag == "AF":
                            meas_type = "LT-AF-Z"
                        MeasRec["treat_dc_field"] = '0'
            if not syn:
                specimen = rec[0]
                MeasRec["specimen"] = specimen
                if specnum != 0:
                    sample = rec[0][:specnum]
                else:
                    sample = rec[0]
                if samp_infile and Samps:  # if samp_infile was provided AND yielded sample data
                    samp = pmag.get_dictitem(Samps, 'sample', sample, 'T')
                    if len(samp) > 0:
                        location = samp[0]["location"]
                        site = samp[0]["site"]
                    else:
                        location = ''
                        site = ''
                else:
                    site = pmag.parse_site(sample, samp_con, Z)
                if location != '' and location not in [x['location'] if 'location' in list(x.keys()) else '' for x in LocRecs]:
                    LocRec['location'] = location
                    LocRec['lat_n'] = lat
                    LocRec['lat_s'] = lat
                    LocRec['lon_e'] = lon
                    LocRec['lon_w'] = lon
                    LocRecs.append(LocRec)
                if site != '' and site not in [x['site'] if 'site' in list(x.keys()) else '' for x in SiteRecs]:
                    SiteRec['location'] = location
                    SiteRec['site'] = site
                    SiteRec['lat'] = lat
                    SiteRec['lon'] = lon
                    SiteRecs.append(SiteRec)
                if sample != '' and sample not in [x['sample'] if 'sample' in list(x.keys()) else '' for x in SampRecs]:
                    SampRec['site'] = site
                    SampRec['sample'] = sample
                    SampRecs.append(SampRec)
                if specimen != '' and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else '' for x in SpecRecs]:
                    SpecRec["specimen"] = specimen
                    SpecRec['sample'] = sample
                    SpecRecs.append(SpecRec)
            else:
                specimen = rec[0]
                MeasRec["specimen"] = specimen
                if specnum != 0:
                    sample = rec[0][:specnum]
                else:
                    sample = rec[0]
                site = pmag.parse_site(sample, samp_con, Z)
                if location != '' and location not in [x['location'] if 'location' in list(x.keys()) else '' for x in LocRecs]:
                    LocRec['location'] = location
                    LocRec['lat_n'] = lat
                    LocRec['lat_s'] = lat
                    LocRec['lon_e'] = lon
                    LocRec['lon_w'] = lon
                    LocRecs.append(LocRec)
                if site != '' and site not in [x['site'] if 'site' in list(x.keys()) else '' for x in SiteRecs]:
                    SiteRec['location'] = location
                    SiteRec['site'] = site
                    SiteRec['lat'] = lat
                    SiteRec['lon'] = lon
                    SiteRecs.append(SiteRec)
                if sample != '' and sample not in [x['sample'] if 'sample' in list(x.keys()) else '' for x in SampRecs]:
                    SampRec['site'] = site
                    SampRec['sample'] = sample
                    SampRecs.append(SampRec)
                if specimen != '' and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else '' for x in SpecRecs]:
                    SpecRec["specimen"] = specimen
                    SpecRec['sample'] = sample
                    SpecRecs.append(SpecRec)
                SampRec["institution"] = institution
                SampRec["material_type"] = syntype
            # MeasRec["sample"]=sample
            if float(rec[1]) == 0:
                pass
            elif demag == "AF":
                if methcode != "LP-AN-ARM":
                    MeasRec["treat_ac_field"] = '%8.3e' % (
                        float(rec[1])*1e-3)  # peak field in tesla
                    if meas_type == "LT-AF-Z":
                        MeasRec["treat_dc_field"] = '0'
                else:  # AARM experiment
                    if treat[1][0] == '0':
                        meas_type = "LT-AF-Z:LP-AN-ARM:"
                        MeasRec["treat_ac_field"] = '%8.3e' % (
                            peakfield)  # peak field in tesla
                        MeasRec["treat_dc_field"] = '%8.3e' % (0)
                        if labfield != 0 and methcode != "LP-AN-ARM":
                            print(
                                "Warning - inconsistency in mag file with lab field - overriding file with 0")
                    else:
                        meas_type = "LT-AF-I:LP-AN-ARM"
                        ipos = int(treat[0])-1
                        MeasRec["treat_dc_field_phi"] = '%7.1f' % (dec[ipos])
                        MeasRec["treat_dc_field_theta"] = '%7.1f' % (inc[ipos])
                        MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                        MeasRec["treat_ac_field"] = '%8.3e' % (
                            peakfield)  # peak field in tesla
            elif demag == "T" and methcode == "LP-AN-TRM":
                MeasRec["treat_temp"] = '%8.3e' % (
                    float(treat[0])+273.)  # temp in kelvin
                if treat[1][0] == '0':
                    meas_type = "LT-T-Z:LP-AN-TRM"
                    MeasRec["treat_dc_field"] = '%8.3e' % (0)
                    MeasRec["treat_dc_field_phi"] = '0'
                    MeasRec["treat_dc_field_theta"] = '0'
                else:
                    MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                    if treat[1][0] == '7':  # alteration check as final measurement
                        meas_type = "LT-PTRM-I:LP-AN-TRM"
                    else:
                        meas_type = "LT-T-I:LP-AN-TRM"

                    # find the direction of the lab field in two ways:
                    # (1) using the treatment coding (XX.1=+x, XX.2=+y, XX.3=+z, XX.4=-x, XX.5=-y, XX.6=-z)
                    ipos_code = int(treat[1][0])-1
                    # (2) using the magnetization
                    DEC = float(rec[4])
                    INC = float(rec[5])
                    if INC < 45 and INC > -45:
                        if DEC > 315 or DEC < 45:
                            ipos_guess = 0
                        if DEC > 45 and DEC < 135:
                            ipos_guess = 1
                        if DEC > 135 and DEC < 225:
                            ipos_guess = 3
                        if DEC > 225 and DEC < 315:
                            ipos_guess = 4
                    else:
                        if INC > 45:
                            ipos_guess = 2
                        if INC < -45:
                            ipos_guess = 5
                    # prefer the guess over the code
                    ipos = ipos_guess
                    MeasRec["treat_dc_field_phi"] = '%7.1f' % (tdec[ipos])
                    MeasRec["treat_dc_field_theta"] = '%7.1f' % (tinc[ipos])
                    # check it
                    if ipos_guess != ipos_code and treat[1][0] != '7':
                        print("-E- ERROR: check specimen %s step %s, ATRM measurements, coding does not match the direction of the lab field!" %
                              (rec[0], ".".join(list(treat))))

            elif demag == "S":  # Shaw experiment
                if treat[1][1] == '0':
                    if int(treat[0]) != 0:
                        MeasRec["treat_ac_field"] = '%8.3e' % (
                            float(treat[0])*1e-3)  # AF field in tesla
                        MeasRec["treat_dc_field"] = '0'
                        meas_type = "LT-AF-Z"  # first AF
                    else:
                        meas_type = "LT-NO"
                        MeasRec["treat_ac_field"] = '0'
                        MeasRec["treat_dc_field"] = '0'
                elif treat[1][1] == '1':
                    if int(treat[0]) == 0:
                        MeasRec["treat_ac_field"] = '%8.3e' % (
                            peakfield)  # peak field in tesla
                        MeasRec["treat_dc_field"] = '%8.3e' % (arm_labfield)
                        MeasRec["treat_dc_field_phi"] = '%7.1f' % (phi)
                        MeasRec["treat_dc_field_theta"] = '%7.1f' % (theta)
                        meas_type = "LT-AF-I"
                    else:
                        MeasRec["treat_ac_field"] = '%8.3e' % (
                            float(treat[0])*1e-3)  # AF field in tesla
                        MeasRec["treat_dc_field"] = '0'
                        meas_type = "LT-AF-Z"
                elif treat[1][1] == '2':
                    if int(treat[0]) == 0:
                        MeasRec["treat_ac_field"] = '0'
                        MeasRec["treat_dc_field"] = '%8.3e' % (trm_labfield)
                        MeasRec["treat_dc_field_phi"] = '%7.1f' % (phi)
                        MeasRec["treat_dc_field_theta"] = '%7.1f' % (theta)
                        MeasRec["treat_temp"] = '%8.3e' % (trm_peakT)
                        meas_type = "LT-T-I"
                    else:
                        MeasRec["treat_ac_field"] = '%8.3e' % (
                            float(treat[0])*1e-3)  # AF field in tesla
                        MeasRec["treat_dc_field"] = '0'
                        meas_type = "LT-AF-Z"
                elif treat[1][1] == '3':
                    if int(treat[0]) == 0:
                        MeasRec["treat_ac_field"] = '%8.3e' % (
                            peakfield)  # peak field in tesla
                        MeasRec["treat_dc_field"] = '%8.3e' % (arm_labfield)
                        MeasRec["treat_dc_field_phi"] = '%7.1f' % (phi)
                        MeasRec["treat_dc_field_theta"] = '%7.1f' % (theta)
                        meas_type = "LT-AF-I"
                    else:
                        MeasRec["treat_ac_field"] = '%8.3e' % (
                            float(treat[0])*1e-3)  # AF field in tesla
                        MeasRec["treat_dc_field"] = '0'
                        meas_type = "LT-AF-Z"

            # Cooling rate experient # added by rshaar
            elif demag == "T" and methcode == "LP-CR-TRM":
                MeasRec["treat_temp"] = '%8.3e' % (
                    float(treat[0])+273.)  # temp in kelvin
                if treat[1][0] == '0':
                    meas_type = "LT-T-Z:LP-CR-TRM"
                    MeasRec["treat_dc_field"] = '%8.3e' % (0)
                    MeasRec["treat_dc_field_phi"] = '0'
                    MeasRec["treat_dc_field_theta"] = '0'
                else:
                    MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                    if treat[1][0] == '7':  # alteration check as final measurement
                        meas_type = "LT-PTRM-I:LP-CR-TRM"
                    else:
                        meas_type = "LT-T-I:LP-CR-TRM"
                    MeasRec["treat_dc_field_phi"] = '%7.1f' % (
                        phi)  # labfield phi
                    MeasRec["treat_dc_field_theta"] = '%7.1f' % (
                        theta)  # labfield theta

                    indx = int(treat[1][0])-1
                    # alteration check matjed as 0.7 in the measurement file
                    if indx == 6:
                        cooling_time = cooling_rates_list[-1]
                    else:
                        cooling_time = cooling_rates_list[indx]
                    MeasRec["description"] = "cooling_rate" + \
                        ":"+cooling_time+":"+"K/min"
                    noave = 1
            elif demag != 'N':
                if len(treat) == 1:
                    treat.append('0')
                MeasRec["treat_temp"] = '%8.3e' % (
                    float(treat[0])+273.)  # temp in kelvin
                if trm == 0:  # demag=T and not trmaq
                    if treat[1][0] == '0':
                        meas_type = "LT-T-Z"
                    else:
                        # labfield in tesla (convert from microT)
                        MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                        MeasRec["treat_dc_field_phi"] = '%7.1f' % (
                            phi)  # labfield phi
                        MeasRec["treat_dc_field_theta"] = '%7.1f' % (
                            theta)  # labfield theta
                        if treat[1][0] == '1':
                            meas_type = "LT-T-I"  # in-field thermal step
                        if treat[1][0] == '2':
                            meas_type = "LT-PTRM-I"  # pTRM check
                            pTRM = 1
                        if treat[1][0] == '3':
                            # this is a zero field step
                            MeasRec["treat_dc_field"] = '0'
                            meas_type = "LT-PTRM-MD"  # pTRM tail check
                else:
                    labfield = float(treat[1])*1e-6
                    # labfield in tesla (convert from microT)
                    MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                    MeasRec["treat_dc_field_phi"] = '%7.1f' % (
                        phi)  # labfield phi
                    MeasRec["treat_dc_field_theta"] = '%7.1f' % (
                        theta)  # labfield theta
                    meas_type = "LT-T-I:LP-TRM"  # trm acquisition experiment

            MeasRec["dir_csd"] = rec[2]
            MeasRec["magn_moment"] = '%10.3e' % (
                float(rec[3])*1e-3)  # moment in Am^2 (from emu)
            MeasRec["dir_dec"] = rec[4]
            MeasRec["dir_inc"] = rec[5]
            MeasRec["instrument_codes"] = instcode
            MeasRec["analysts"] = user
            MeasRec["citations"] = citations
            if "LP-IRM-3D" in methcode:
                meas_type = methcode
            # MeasRec["method_codes"]=methcode.strip(':')
            MeasRec["method_codes"] = meas_type
            MeasRec["quality"] = 'g'
            if 'std' in rec[0]:
                MeasRec["standard"] = 's'
            else:
                MeasRec["standard"] = 'u'
            MeasRec["treat_step_num"] = 0
            # print MeasRec['treat_temp']
            MeasRecs.append(MeasRec)

    con = cb.Contribution(output_dir_path, read_tables=[])

    # create MagIC tables
    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    #for rec in MeasRecs: 
    #    print (float(rec['treat_temp'])-273,rec['method_codes'])
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave=False)
    #for rec in MeasOuts:
    #    print (float(rec['treat_temp'])-273,rec['method_codes'])

#    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)
    # write MagIC tables to file
    con.tables['specimens'].write_magic_file(custom_name=spec_file,dir_path=dir_path)
    con.tables['samples'].write_magic_file(custom_name=samp_file,dir_path=dir_path)
    con.tables['sites'].write_magic_file(custom_name=site_file,dir_path=dir_path)
    con.tables['locations'].write_magic_file(custom_name=loc_file,dir_path=dir_path)
    meas_file = con.tables['measurements'].write_magic_file(
        custom_name=meas_file,dir_path=dir_path)
    return True, meas_file


### s_magic conversion

def s_magic(sfile, anisfile="specimens.txt", dir_path=".", atype="AMS",
            coord_type="s", sigma=False, samp_con="1", specnum=0,
            location="unknown", spec="unknown", sitename="unknown",
            user="", data_model_num=3, name_in_file=False, input_dir_path=""):
    """
    converts .s format data to measurements  format.

    Parameters
    ----------
    sfile : str
       .s format file, required
    anisfile : str
        specimen filename, default 'specimens.txt'
    dir_path : str
        output directory, default "."
    atype : str
        anisotropy type (AMS, AARM, ATRM, default AMS)
    coord_type : str
       coordinate system ('s' for specimen, 't' for tilt-corrected,
       or 'g' for geographic, default 's')
    sigma : bool
       if True, last column has sigma, default False
    samp_con : str
        sample/site naming convention, default '1', see info below
    specnum : int
        number of characters to designate a specimen, default 0
    location : str
        location name, default "unknown"
    spec : str
        specimen name, default "unknown"
    sitename : str
        site name, default "unknown"
    user : str
        user name, default ""
    data_model_num : int
        MagIC data model 2 or 3, default 3
    name_in_file : bool
        first entry of each line is specimen name, default False
    input_dir_path : input directory path IF different from dir_path, default ""

    Returns
    ---------
    Tuple : (True or False indicating if conversion was successful, meas_file name written)


    Input format
    --------
        X11,X22,X33,X12,X23,X13  (.s format file)
        X11,X22,X33,X12,X23,X13,sigma (.s format file with -sig option)
        SID, X11,X22,X33,X12,X23,X13  (.s format file with -n option)

    Info
    --------
    Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY


    """
    con, Z = "", 1
    if samp_con:
        samp_con = str(samp_con)
        if "4" in samp_con:
            if "-" not in samp_con:
                print("option [4] must be in form 4-Z where Z is an integer")
                return False, "option [4] must be in form 4-Z where Z is an integer"
            else:
                Z = samp_con.split("-")[1]
                samp_con = "4"
        if samp_con == '6':
            print("option [6] is not currently supported")
            return
    else:
        samp_con = con


    coord_dict = {'s': '-1', 't': '100', 'g': '0'}
    coord = coord_dict.get(coord_type, '-1')
    specnum = -specnum

    if data_model_num == 2:
        specimen_col = "er_specimen_name"
        sample_col = "er_sample_name"
        site_col = "er_site_name"
        loc_col = "er_location_name"
        citation_col = "er_citation_names"
        analyst_col = "er_analyst_mail_names"
        aniso_type_col = "anisotropy_type"
        experiment_col = "magic_experiment_names"
        sigma_col = "anisotropy_sigma"
        unit_col = "anisotropy_unit"
        tilt_corr_col = "anisotropy_tilt_correction"
        method_col = "magic_method_codes"
        outfile_type = "rmag_anisotropy"
    else:
        specimen_col = "specimen"
        sample_col = "sample"
        site_col = "site"
        loc_col = "location"
        citation_col = "citations"
        analyst_col = "analysts"
        aniso_type_col = "aniso_type"
        experiment_col = "experiments"
        sigma_col = "aniso_s_sigma"
        unit_col = "aniso_s_unit"
        tilt_corr_col = "aniso_tilt_correction"
        method_col = "method_codes"
        outfile_type = "specimens"
    # get down to bidness
    input_dir_path, dir_path = pmag.fix_directories(input_dir_path, dir_path)
    sfile = pmag.resolve_file_name(sfile, input_dir_path)
    anisfile = pmag.resolve_file_name(anisfile, dir_path)
    try:
        with open(sfile, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return False, "No such file: {}".format(sfile)
    AnisRecs = []
    citation = "This study"
    # read in data
    for line in lines:
        AnisRec = {}
        rec = line.split()
        if name_in_file:
            k = 1
            spec = rec[0]
        else:
            k = 0
        trace = float(rec[k])+float(rec[k+1])+float(rec[k+2])
        s1 = '%10.9e' % (float(rec[k]) / trace)
        s2 = '%10.9e' % (float(rec[k+1]) / trace)
        s3 = '%10.9e' % (float(rec[k+2]) / trace)
        s4 = '%10.9e' % (float(rec[k+3]) / trace)
        s5 = '%10.9e' % (float(rec[k+4]) / trace)
        s6 = '%10.9e' % (float(rec[k+5]) / trace)
        AnisRec[citation_col] = citation
        AnisRec[specimen_col] = spec
        if specnum != 0:
            AnisRec[sample_col] = spec[:specnum]
        else:
            AnisRec[sample_col] = spec
        # if samp_con == "6":
        #    for samp in Samps:
        #        if samp['er_sample_name'] == AnisRec["er_sample_name"]:
        #            sitename = samp['er_site_name']
        #            location = samp['er_location_name']
        if samp_con != "":
            sitename = pmag.parse_site(AnisRec[sample_col], samp_con, Z)
        AnisRec[loc_col] = location
        AnisRec[site_col] = sitename
        AnisRec[analyst_col] = user
        if atype == 'AMS':
            AnisRec[aniso_type_col] = "AMS"
            AnisRec[experiment_col] = spec+":LP-X"
        else:
            AnisRec[aniso_type_col] = atype
            AnisRec[experiment_col] = spec+":LP-"+atype
        if data_model_num != 3:
            AnisRec["anisotropy_s1"] = s1
            AnisRec["anisotropy_s2"] = s2
            AnisRec["anisotropy_s3"] = s3
            AnisRec["anisotropy_s4"] = s4
            AnisRec["anisotropy_s5"] = s5
            AnisRec["anisotropy_s6"] = s6
        else:
            AnisRec['aniso_s'] = ":".join(
                [str(s) for s in [s1, s2, s3, s4, s5, s6]])
        if sigma:
            AnisRec[sigma_col] = '%10.8e' % (
                float(rec[k+6]) / trace)
            AnisRec[unit_col] = 'SI'
            AnisRec[tilt_corr_col] = coord
            AnisRec[method_col] = 'LP-' + atype
        AnisRecs.append(AnisRec)
    pmag.magic_write(anisfile, AnisRecs, outfile_type)
    print('data saved in ', anisfile)
    # try to extract location/site/sample info into tables
    con = cb.Contribution(dir_path, custom_filenames={"specimens": anisfile})
    con.propagate_all_tables_info()
    for table in con.tables:
        if table in ['samples', 'sites', 'locations']:
            # add in location name by hand
            if table == 'sites':
                con.tables['sites'].df['location'] = location
            con.write_table_to_file(table)
    return True, anisfile


### SUFAR 4 ASC conversion

def sufar4(ascfile, meas_output='measurements.txt', spec_infile=None, 
           spec_outfile='specimens.txt', samp_outfile='samples.txt',
           site_outfile='sites.txt', specnum=0, sample_naming_con='1', user="",
           locname="unknown", instrument='', static_15_position_mode=False,
           dir_path='.', input_dir_path='', or_con=False,specname=False,
           preserve_case=False):
    """
    Converts ascii files generated by SUFAR ver.4.0 to MagIC files
    for data model 2 output use sufar4_dm2()

    Parameters
    ----------
    ascfile : str
        input ASC file, required
    meas_output : str
        measurement output filename, default "measurements.txt"
    spec_infile : str
        specimen infile, default None
    specname : bool
        if True, use file name stem for specimen name, if False, read from within file, default = False
    spec_outfile : str
        specimen outfile, default "specimens.txt"
    samp_outfile : str
        sample outfile, default "samples.txt"
    site_outfile : str
        site outfile, default "sites.txt"
    specnum : int
        number of characters to designate a specimen, default 0
    sample_naming_con : str
        sample/site naming convention, default '1', see info below
    user : str
        user name, default ""
    locname : str
        location name, default "unknown"
    instrument : str
        instrument name, default ""
    static_15_position_mode : bool
        specify static 15 position mode - default False (is spinning)
    dir_path : str
        output directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    or_con : int
        Orientation convention, default is False
    preserve_case : bool
        the default is to put names into lower case

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful, file name written)

    Info
    --------
    Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY

    orientation conventions:
        [1] Standard Pomeroy convention of azimuth and hade (degrees from vertical down)
             of the drill direction (field arrow).  lab arrow azimuth= sample_azimuth = mag_azimuth;
             lab arrow dip = sample_dip =-field_dip. i.e. the lab arrow dip is minus the hade.
        [2] Field arrow is the strike  of the plane orthogonal to the drill direction,
             Field dip is the hade of the drill direction.  Lab arrow azimuth = mag_azimuth-90
             Lab arrow dip = -field_dip
        [3] Lab arrow is the same as the drill direction;
             hade was measured in the field.
             Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip
        [4] lab azimuth and dip are same as mag_azimuth, field_dip : use this for unoriented samples too
        [5] Same as AZDIP convention explained below -
            azimuth and inclination of the drill direction are mag_azimuth and field_dip;
            lab arrow is as in [1] above.
            lab azimuth is same as mag_azimuth,lab arrow dip=field_dip-90
        [6] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = 90-field_dip
        [7] see http://earthref.org/PmagPy/cookbook/#field_info for more information.  You can customize other format yourself, or email ltauxe@ucsd.edu for help.
        [8] Lab arrow azimuth = mag_azimuth-180; Lab arrow dip = 90-field_dip


    """

    citation = 'This study'
    cont = 0
    Z = 1
    AniRecSs, AniRecs, SpecRecs, SampRecs, SiteRecs, MeasRecs = [], [], [], [], [], []
    isspec = '0'
    spin = 0


    # set column names for MagIC 3
    spec_name_col = 'specimen'
    samp_name_col = 'sample'
    site_name_col = 'site'
    loc_name_col = 'location'
    citation_col = 'citations'
    method_col = 'method_codes'
    site_description_col = 'description'
    expedition_col = 'expedition_name'
    instrument_col = 'instrument_codes'
    experiment_col = 'experiments'
    analyst_col = 'analysts'
    quality_col = 'quality'
    aniso_quality_col = 'result_quality'
    meas_standard_col = 'standard'
    meas_description_col = 'description'
    aniso_type_col = 'aniso_type'
    aniso_unit_col = 'aniso_s_unit'
    aniso_n_col = 'aniso_s_n_measurements'
    azimuth_col = 'azimuth'
    spec_volume_col = 'volume'
    samp_dip_col = 'dip'
    bed_dip_col = 'bed_dip'
    bed_dip_direction_col = 'bed_dip_direction'
    chi_vol_col = 'susc_chi_volume'
    aniso_sigma_col = 'aniso_s_sigma'
    aniso_unit_col = 'aniso_s_unit'
    aniso_tilt_corr_col = 'aniso_tilt_correction'
    meas_table_name = 'measurements'
    spec_table_name = 'specimens'
    samp_table_name = 'samples'
    site_table_name = 'sites'

    # create full path for files
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    ascfile_path = os.path.join(input_dir_path, ascfile)
    # initialized but not used
    meas_output = os.path.join(output_dir_path, meas_output)

    spec_outfile = os.path.join(output_dir_path, spec_outfile)
    samp_outfile = os.path.join(output_dir_path, samp_outfile)
    site_outfile = os.path.join(output_dir_path, site_outfile)

    if "4" in sample_naming_con:
        if "-" not in sample_naming_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = sample_naming_con.split("-")[1]
            sample_naming_con = "4"
    if "7" in sample_naming_con:
        if "-" not in sample_naming_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = sample_naming_con.split("-")[1]
            sample_naming_con = "7"

    if static_15_position_mode:
        spin = 0

    if spec_infile:
        if os.path.isfile(os.path.join(input_dir_path, str(spec_infile))):
            # means an er_specimens.txt file has been provided with sample,
            # site, location (etc.) info
            isspec = '1'

    specnum = int(specnum)

    if isspec == "1":
        specs, file_type = pmag.magic_read(spec_infile)

    specnames, sampnames, sitenames = [], [], []

    try:
        file_input = open(ascfile_path, 'r')
    except:
        print('Error opening file: ', ascfile_path)
        return False, 'Error opening file: {}'.format(ascfile_path)
    Data = file_input.readlines()
    file_input.close()
    k = 0
    while k < len(Data):
        line = Data[k]
        words = line.split()
        if "ANISOTROPY" in words:  # first line of data for the spec
            MeasRec, AniRec, SpecRec, SampRec, SiteRec = {}, {}, {}, {}, {}
            if specname:
                if preserve_case:
                    specimen = ascfile.split('.')[0]+words[0]
                else:
                    specimen = ascfile.split('.')[0].lower()+words[0].lower()
            else:
                if preserve_case:
                    specimen = words[0]
                else:
                    specimen = words[0].lower()
            AniRec[spec_name_col] = specimen
            if isspec == "1":
                for spec in specs:
                    if spec[spec_name_col] == specimen:
                        AniRec[samp_name_col] = spec[samp_name_col]
                        break
            elif isspec == "0":
                if specnum != 0:
                    sampname = specimen[:-specnum]
                else:
                    sampname = specimen
                AniRec[samp_name_col] = sampname
                SpecRec[spec_name_col] = specimen
                SpecRec[samp_name_col] = sampname
                SampRec[samp_name_col] = sampname
                SiteRec[samp_name_col] = sampname
                SiteRec[site_description_col] = 's'
                if sample_naming_con != "9":
                    SampRec[site_name_col] = pmag.parse_site(
                        AniRec[samp_name_col], sample_naming_con, Z)
                    SiteRec[site_name_col] = pmag.parse_site(
                        AniRec[samp_name_col], sample_naming_con, Z)
                else:
                    SampRec[site_name_col] = specimen
                    SiteRec[site_name_col] = specimen
                    pieces = specimen.split('-')
                    SiteRec[expedition_col] = pieces[0]
                    location = pieces[1]
                SiteRec[loc_name_col] = locname
                AniRec[citation_col] = "This study"
                SpecRec[citation_col] = "This study"
                SampRec[citation_col] = "This study"
                SiteRec[citation_col] = "This study"
            AniRec[citation_col] = "This study"
            AniRec[instrument_col] = instrument
            AniRec[method_col] = "LP-X:AE-H:LP-AN-MS"
            AniRec[experiment_col] = specimen + "_" + "LP-AN-MS"
            AniRec[analyst_col] = user
            for key in list(AniRec.keys()):
                MeasRec[key] = AniRec[key]
            MeasRec['experiment'] = AniRec.get('experiments', '')
            if 'experiments' in MeasRec:
                MeasRec.pop('experiments')
            MeasRec[quality_col] = 'g'
            AniRec[aniso_quality_col] = 'g'
            MeasRec[meas_standard_col] = 'u'
            MeasRec[meas_description_col] = 'Bulk sucsecptibility measurement'
            AniRec[aniso_type_col] = "AMS"
            AniRec[aniso_unit_col] = "Normalized by trace"
            if spin == 1:
                AniRec[aniso_n_col] = "192"
            else:
                AniRec[aniso_n_col] = "15"
        if 'Azi' in words and isspec == '0':
            az = float(words[1])
            P1 = float(words[4])
            P2 = float(words[5])
            P3 = float(words[6])
            # P4 relates to a fabric or bedding measurement -- not dealt with
            # here
            P4 = float(words[7])
            az = az + P1 * 360. / 12. - P3 * 360. / 12.
            if az >= 360:
                az = az - 360
            elif az <= -360:
                az = az + 360
            labaz = az
            if not or_con:SampRec[azimuth_col] = str(round(az, 1))
        if 'Dip' in words:
            # convert actual volume to m^3 from cm^3
            SpecRec[spec_volume_col] = '%8.3e' % (float(words[10]) * 1e-6)
            dip = float(words[1])
            if P2 == 90:
                dip = dip - 90.
            labdip = dip
            if not or_con:SampRec[samp_dip_col] = str(round(dip, 1))
        if 'T1' in words and 'F1' in words:
            k += 2  # read in fourth line down
            line = Data[k]
            rec = line.split()
            dd = rec[1].split('/')
            dip_direction = int(dd[0]) + 90
            SampRec[bed_dip_direction_col] = '%i' % (dip_direction)
            SampRec[bed_dip_col] = dd[1]
            bed_dip = float(dd[1])
        if "Mean" in words:
            k += 4  # read in fourth line down
            line = Data[k]
            rec = line.split()
            MeasRec[chi_vol_col] = rec[1]
            sigma = .01 * float(rec[2]) / 3.
            AniRec[aniso_sigma_col] = '%7.4f' % (sigma)
            AniRec[aniso_unit_col] = 'SI'
        if "factors" in words:
            k += 4  # read in second line down
            line = Data[k]
            rec = line.split()
        if "Specimen" in words:  # first part of specimen data
            # eigenvalues sum to unity - not 3
            s1_val = '%7.4f' % (float(words[5]) / 3.)
            s2_val = '%7.4f' % (float(words[6]) / 3.)
            s3_val = '%7.4f' % (float(words[7]) / 3.)
            k += 1
            line = Data[k]
            rec = line.split()
            # eigenvalues sum to unity - not 3
            s4_val= '%7.4f' % (float(rec[5]) / 3.)
            s5_val = '%7.4f' % (float(rec[6]) / 3.)
            s6_val = '%7.4f' % (float(rec[7]) / 3.)
            vals = (s1_val, s2_val, s3_val, s4_val, s5_val, s6_val)
            AniRec['aniso_s'] = ":".join([v.strip() for v in vals])
            #
            AniRec[aniso_tilt_corr_col] = '-1'
            AniRecs.append(AniRec)
            AniRecG, AniRecT = {}, {}
            for key in list(AniRec.keys()):
                AniRecG[key] = AniRec[key]
            for key in list(AniRec.keys()):
                AniRecT[key] = AniRec[key]
            if or_con: 
                az,dip=pmag.orient(labaz,labdip,or_con)
                SampRec[samp_dip_col]=str(round(dip,1))
                SampRec[azimuth_col]=str(round(az,1))
                labaz = az
                labdip = dip
            sbar = []
            sbar.append(float(s1_val))
            sbar.append(float(s2_val))
            sbar.append(float(s3_val))
            sbar.append(float(s4_val))
            sbar.append(float(s5_val))
            sbar.append(float(s6_val))
            sbarg = pmag.dosgeo(sbar, labaz, labdip)
            s1_g = '%12.10f' % (sbarg[0])
            s2_g = '%12.10f' % (sbarg[1])
            s3_g = '%12.10f' % (sbarg[2])
            s4_g = '%12.10f' % (sbarg[3])
            s5_g = '%12.10f' % (sbarg[4])
            s6_g = '%12.10f' % (sbarg[5])
            vals = (s1_g, s2_g, s3_g, s4_g, s5_g, s6_g)
            AniRecG['aniso_s'] = ":".join([v.strip() for v in vals])
            AniRecG[aniso_tilt_corr_col] = '0'
            AniRecs.append(AniRecG)
            if bed_dip != "" and bed_dip != 0:  # have tilt correction
                sbart = pmag.dostilt(sbarg, dip_direction, bed_dip)
                s1_t = '%12.10f' % (sbart[0])
                s2_t = '%12.10f' % (sbart[1])
                s3_t = '%12.10f' % (sbart[2])
                s4_t = '%12.10f' % (sbart[3])
                s5_t = '%12.10f' % (sbart[4])
                s6_t = '%12.10f' % (sbart[5])
                vals = (s1_t, s2_t, s3_t, s4_t, s5_t, s6_t)
                AniRecT["aniso_s"] = ":".join([v.strip() for v in vals])
                AniRecT[aniso_tilt_corr_col] = '100'
                AniRecs.append(AniRecT)
            for key in ['site','sample']:
                if key in MeasRec.keys():del MeasRec[key]
            for key in ['site']:
                if key in SpecRec.keys():del SpecRec[key]
            for key in ['sample']:
                if key in SiteRec.keys():del SiteRec[key]
            MeasRecs.append(MeasRec)
            if SpecRec[spec_name_col] not in specnames:
                SpecRecs.append(SpecRec)
                specnames.append(SpecRec[spec_name_col])
            if SampRec[samp_name_col] not in sampnames:
                SampRecs.append(SampRec)
                sampnames.append(SampRec[samp_name_col])
            if SiteRec[site_name_col] not in sitenames:
                SiteRecs.append(SiteRec)
                sitenames.append(SiteRec[site_name_col])
        k += 1  # skip to next specimen

    pmag.magic_write(meas_output, MeasRecs, meas_table_name)
    print("bulk measurements put in ", meas_output)
    # if isspec=="0":
    SpecOut, keys = pmag.fillkeys(SpecRecs)
    #
    full_SpecOut = []
    spec_list = []
    for rec in SpecOut:
        full_SpecOut.append(rec)
        spec_name = rec[spec_name_col]
        if spec_name not in spec_list:
            spec_list.append(spec_name)
            ani_recs = pmag.get_dictitem(AniRecs, spec_name_col, spec_name, 'T')
            full_SpecOut.extend(ani_recs)

        # FILL KEYS
            full_SpecOut, keys = pmag.fillkeys(full_SpecOut)
        else:
            full_SpecOut = SpecOut
    pmag.magic_write(spec_outfile, full_SpecOut, spec_table_name)
    print("specimen/anisotropy info put in ", spec_outfile)
    SampOut, keys = pmag.fillkeys(SampRecs)
    pmag.magic_write(samp_outfile, SampOut, samp_table_name)
    print("sample info put in ", samp_outfile)
    SiteOut, keys = pmag.fillkeys(SiteRecs)
    pmag.magic_write(site_outfile, SiteOut, site_table_name)
    print("site info put in ", site_outfile)
    return True, meas_output

def sufar4_dm2(ascfile, meas_output='measurements.txt', aniso_output='rmag_anisotropy.txt',
           spec_infile=None, spec_outfile='specimens.txt', samp_outfile='samples.txt',
           site_outfile='sites.txt', specnum=0, sample_naming_con='1', user="",
           locname="unknown", instrument='', static_15_position_mode=False,
           dir_path='.', input_dir_path='', data_model_num=2,or_con=False):
    """
    Converts ascii files generated by SUFAR ver.4.0 to MagIC files

    Parameters
    ----------
    ascfile : str
        input ASC file, required
    meas_output : str
        measurement output filename, default "measurements.txt"
    aniso_output : str
        anisotropy output filename, MagIC 2 only, "rmag_anisotropy.txt"
    spec_infile : str
        specimen infile, default None
    spec_outfile : str
        specimen outfile, default "specimens.txt"
    samp_outfile : str
        sample outfile, default "samples.txt"
    site_outfile : str
        site outfile, default "sites.txt"
    specnum : int
        number of characters to designate a specimen, default 0
    sample_naming_con : str
        sample/site naming convention, default '1', see info below
    user : str
        user name, default ""
    locname : str
        location name, default "unknown"
    instrument : str
        instrument name, default ""
    static_15_position_mode : bool
        specify static 15 position mode - default False (is spinning)
    dir_path : str
        output directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    data_model_num : int
        MagIC data model 2 or 3, default 3
    or_con : int
        Orientation convention, default is False

    Returns
    --------
    type - Tuple : (True or False indicating if conversion was successful, file name written)

    Info
    --------
    Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY

    orientation conventions:
        [1] Standard Pomeroy convention of azimuth and hade (degrees from vertical down)
             of the drill direction (field arrow).  lab arrow azimuth= sample_azimuth = mag_azimuth;
             lab arrow dip = sample_dip =-field_dip. i.e. the lab arrow dip is minus the hade.
        [2] Field arrow is the strike  of the plane orthogonal to the drill direction,
             Field dip is the hade of the drill direction.  Lab arrow azimuth = mag_azimuth-90
             Lab arrow dip = -field_dip
        [3] Lab arrow is the same as the drill direction;
             hade was measured in the field.
             Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip
        [4] lab azimuth and dip are same as mag_azimuth, field_dip : use this for unoriented samples too
        [5] Same as AZDIP convention explained below -
            azimuth and inclination of the drill direction are mag_azimuth and field_dip;
            lab arrow is as in [1] above.
            lab azimuth is same as mag_azimuth,lab arrow dip=field_dip-90
        [6] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = 90-field_dip
        [7] see http://earthref.org/PmagPy/cookbook/#field_info for more information.  You can customize other format yourself, or email ltauxe@ucsd.edu for help.
        [8] Lab arrow azimuth = mag_azimuth-180; Lab arrow dip = 90-field_dip


    """

    citation = 'This study'
    cont = 0
    Z = 1
    AniRecSs, AniRecs, SpecRecs, SampRecs, SiteRecs, MeasRecs = [], [], [], [], [], []
    isspec = '0'
    spin = 0
    data_model_num = int(float(data_model_num))

    # set defaults for MagIC 2
    if data_model_num == 2:
        if meas_output == 'measurements.txt':
            meas_output = 'magic_measurements.txt'
        if spec_outfile == 'specimens.txt':
            spec_outfile = 'er_specimens.txt'
        if samp_outfile == 'samples.txt':
            samp_outfile = 'er_samples.txt'
        if site_outfile == 'sites.txt':
            site_outfile = 'er_sites.txt'

    # set column names for MagIC 3
    spec_name_col = 'specimen'
    samp_name_col = 'sample'
    site_name_col = 'site'
    loc_name_col = 'location'
    citation_col = 'citations'
    method_col = 'method_codes'
    site_description_col = 'description'
    expedition_col = 'expedition_name'
    instrument_col = 'instrument_codes'
    experiment_col = 'experiments'
    analyst_col = 'analysts'
    quality_col = 'quality'
    aniso_quality_col = 'result_quality'
    meas_standard_col = 'standard'
    meas_description_col = 'description'
    aniso_type_col = 'aniso_type'
    aniso_unit_col = 'aniso_s_unit'
    aniso_n_col = 'aniso_s_n_measurements'
    azimuth_col = 'azimuth'
    spec_volume_col = 'volume'
    samp_dip_col = 'dip'
    bed_dip_col = 'bed_dip'
    bed_dip_direction_col = 'bed_dip_direction'
    chi_vol_col = 'susc_chi_volume'
    aniso_sigma_col = 'aniso_s_sigma'
    aniso_unit_col = 'aniso_s_unit'
    aniso_tilt_corr_col = 'aniso_tilt_correction'
    meas_table_name = 'measurements'
    spec_table_name = 'specimens'
    samp_table_name = 'samples'
    site_table_name = 'sites'

    # set column names for MagIC 2
    if data_model_num == 2:
        spec_name_col = 'er_specimen_name'
        samp_name_col = 'er_sample_name'
        site_name_col = 'er_site_name'
        loc_name_col = 'er_location_name'
        citation_col = 'er_citation_names'
        method_col = 'magic_method_codes'
        site_description_col = 'site_description'
        expedition_col = 'er_expedition_name'
        instrument_col = 'magic_instrument_codes'
        experiment_col = 'magic_experiment_names'
        analyst_col = 'er_analyst_mail_names'
        quality_col = 'measurement_flag'
        aniso_quality_col = 'anisotropy_flag'
        meas_standard_col = 'measurement_standard'
        meas_description_col = 'measurement_description'
        aniso_type_col = 'anisotropy_type'
        aniso_unit_col = 'anisotropy_unit'
        aniso_n_col = 'anisotropy_n'
        azimuth_col = 'sample_azimuth'
        spec_volume_col = 'specimen_volume'
        samp_dip_col = 'sample_dip'
        bed_dip_col = 'sample_bed_dip'
        bed_dip_direction_col = 'sample_bed_dip_direction'
        chi_vol_col = 'measurement_chi_volume'
        aniso_sigma_col = 'anisotropy_sigma'
        aniso_unit_col = 'anisotropy_unit'
        aniso_tilt_corr_col = 'anisotropy_tilt_correction'
        meas_table_name = 'magic_measurements'
        spec_table_name = 'er_specimens'
        samp_table_name = 'er_samples'
        site_table_name = 'er_sites'

    # create full path for files
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    ascfile = os.path.join(input_dir_path, ascfile)
    aniso_output = os.path.join(output_dir_path, aniso_output)
    # initialized but not used
    meas_output = os.path.join(output_dir_path, meas_output)

    spec_outfile = os.path.join(output_dir_path, spec_outfile)
    samp_outfile = os.path.join(output_dir_path, samp_outfile)
    site_outfile = os.path.join(output_dir_path, site_outfile)

    if "4" in sample_naming_con:
        if "-" not in sample_naming_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = sample_naming_con.split("-")[1]
            sample_naming_con = "4"
    if "7" in sample_naming_con:
        if "-" not in sample_naming_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = sample_naming_con.split("-")[1]
            sample_naming_con = "7"

    if static_15_position_mode:
        spin = 0

    if spec_infile:
        if os.path.isfile(os.path.join(input_dir_path, str(spec_infile))):
            # means an er_specimens.txt file has been provided with sample,
            # site, location (etc.) info
            isspec = '1'

    specnum = int(specnum)

    if isspec == "1":
        specs, file_type = pmag.magic_read(spec_infile)

    specnames, sampnames, sitenames = [], [], []

    try:
        file_input = open(ascfile, 'r')
    except:
        print('Error opening file: ', ascfile)
        return False, 'Error opening file: {}'.format(ascfile)
    Data = file_input.readlines()
    file_input.close()
    k = 0
    while k < len(Data):
        line = Data[k]
        words = line.split()
        if "ANISOTROPY" in words:  # first line of data for the spec
            MeasRec, AniRec, SpecRec, SampRec, SiteRec = {}, {}, {}, {}, {}
            specname = words[0]
            AniRec[spec_name_col] = specname
            if isspec == "1":
                for spec in specs:
                    if spec[spec_name_col] == specname:
                        AniRec[samp_name_col] = spec[samp_name_col]
                        AniRec[site_name_col] = spec[site_name_col]
                        AniRec[loc_name_col] = spec[loc_name_col]
                        break
            elif isspec == "0":
                if specnum != 0:
                    sampname = specname[:-specnum]
                else:
                    sampname = specname
                AniRec[samp_name_col] = sampname
                SpecRec[spec_name_col] = specname
                SpecRec[samp_name_col] = sampname
                SampRec[samp_name_col] = sampname
                SiteRec[samp_name_col] = sampname
                SiteRec[site_description_col] = 's'
                if sample_naming_con != "9":
                    AniRec[site_name_col] = pmag.parse_site(
                        AniRec[samp_name_col], sample_naming_con, Z)
                    SpecRec[site_name_col] = pmag.parse_site(
                        AniRec[samp_name_col], sample_naming_con, Z)
                    SampRec[site_name_col] = pmag.parse_site(
                        AniRec[samp_name_col], sample_naming_con, Z)
                    SiteRec[site_name_col] = pmag.parse_site(
                        AniRec[samp_name_col], sample_naming_con, Z)
                else:
                    AniRec[site_name_col] = specname
                    SpecRec[site_name_col] = specname
                    SampRec[site_name_col] = specname
                    SiteRec[site_name_col] = specname
                    pieces = specname.split('-')
                    AniRec[expedition_col] = pieces[0]
                    SpecRec[expedition_col] = pieces[0]
                    SampRec[expedition_col] = pieces[0]
                    SiteRec[expedition_col] = pieces[0]
                    location = pieces[1]
                AniRec[loc_name_col] = locname
                SpecRec[loc_name_col] = locname
                SampRec[loc_name_col] = locname
                SiteRec[loc_name_col] = locname
                AniRec[citation_col] = "This study"
                SpecRec[citation_col] = "This study"
                SampRec[citation_col] = "This study"
                SiteRec[citation_col] = "This study"
            AniRec[citation_col] = "This study"
            AniRec[instrument_col] = instrument
            AniRec[method_col] = "LP-X:AE-H:LP-AN-MS"
            AniRec[experiment_col] = specname + ":" + "LP-AN-MS"
            AniRec[analyst_col] = user
            for key in list(AniRec.keys()):
                MeasRec[key] = AniRec[key]
            if data_model_num == 2:
                MeasRec['magic_experiment_name'] = AniRec.get('magic_experiment_names', '')
                if 'magic_experiment_names' in MeasRec:
                    MeasRec.pop('magic_experiment_names')
            if data_model_num == 3:
                MeasRec['experiment'] = AniRec.get('experiments', '')
                if 'experiments' in MeasRec:
                    MeasRec.pop('experiments')
            MeasRec[quality_col] = 'g'
            AniRec[aniso_quality_col] = 'g'
            MeasRec[meas_standard_col] = 'u'
            MeasRec[meas_description_col] = 'Bulk sucsecptibility measurement'
            AniRec[aniso_type_col] = "AMS"
            AniRec[aniso_unit_col] = "Normalized by trace"
            if spin == 1:
                AniRec[aniso_n_col] = "192"
            else:
                AniRec[aniso_n_col] = "15"
        if 'Azi' in words and isspec == '0':
            az = float(words[1])
            P1 = float(words[4])
            P2 = float(words[5])
            P3 = float(words[6])
            # P4 relates to a fabric or bedding measurement -- not dealt with
            # here
            P4 = float(words[7])
            az = az + P1 * 360. / 12. - P3 * 360. / 12.
            if az >= 360:
                az = az - 360
            elif az <= -360:
                az = az + 360
            labaz = az
            if not or_con:SampRec[azimuth_col] = str(round(az, 1))
        if 'Dip' in words:
            # convert actual volume to m^3 from cm^3
            SpecRec[spec_volume_col] = '%8.3e' % (float(words[10]) * 1e-6)
            dip = float(words[1])
            if P2 == 90:
                dip = dip - 90.
            labdip = dip
            if not or_con:SampRec[samp_dip_col] = str(round(dip, 1))
        if 'T1' in words and 'F1' in words:
            k += 2  # read in fourth line down
            line = Data[k]
            rec = line.split()
            dd = rec[1].split('/')
            dip_direction = int(dd[0]) + 90
            SampRec[bed_dip_direction_col] = '%i' % (dip_direction)
            SampRec[bed_dip_col] = dd[1]
            bed_dip = float(dd[1])
        if "Mean" in words:
            k += 4  # read in fourth line down
            line = Data[k]
            rec = line.split()
            MeasRec[chi_vol_col] = rec[1]
            sigma = .01 * float(rec[2]) / 3.
            AniRec[aniso_sigma_col] = '%7.4f' % (sigma)
            AniRec[aniso_unit_col] = 'SI'
        if "factors" in words:
            k += 4  # read in second line down
            line = Data[k]
            rec = line.split()
        if "Specimen" in words:  # first part of specimen data
            # eigenvalues sum to unity - not 3
            s1_val = '%7.4f' % (float(words[5]) / 3.)
            s2_val = '%7.4f' % (float(words[6]) / 3.)
            s3_val = '%7.4f' % (float(words[7]) / 3.)
            k += 1
            line = Data[k]
            rec = line.split()
            # eigenvalues sum to unity - not 3
            s4_val= '%7.4f' % (float(rec[5]) / 3.)
            s5_val = '%7.4f' % (float(rec[6]) / 3.)
            s6_val = '%7.4f' % (float(rec[7]) / 3.)
            # parse for data model 2
            if data_model_num == 2:
                AniRec['anisotropy_s1'] = s1_val
                AniRec['anisotropy_s2'] = s2_val
                AniRec['anisotropy_s3'] = s3_val
                AniRec['anisotropy_s4'] = s4_val
                AniRec['anisotropy_s5'] = s5_val
                AniRec['anisotropy_s6'] = s6_val
            # parse for data model 3
            else:
                vals = (s1_val, s2_val, s3_val, s4_val, s5_val, s6_val)
                AniRec['aniso_s'] = ":".join([v.strip() for v in vals])
            #
            AniRec[aniso_tilt_corr_col] = '-1'
            AniRecs.append(AniRec)
            AniRecG, AniRecT = {}, {}
            for key in list(AniRec.keys()):
                AniRecG[key] = AniRec[key]
            for key in list(AniRec.keys()):
                AniRecT[key] = AniRec[key]
            if or_con: 
                az,dip=pmag.orient(labaz,labdip,or_con)
                SampRec[samp_dip_col]=str(round(dip,1))
                SampRec[azimuth_col]=str(round(az,1))
                labaz = az
                labdip = dip
            sbar = []
            sbar.append(float(s1_val))
            sbar.append(float(s2_val))
            sbar.append(float(s3_val))
            sbar.append(float(s4_val))
            sbar.append(float(s5_val))
            sbar.append(float(s6_val))
            sbarg = pmag.dosgeo(sbar, labaz, labdip)
            s1_g = '%12.10f' % (sbarg[0])
            s2_g = '%12.10f' % (sbarg[1])
            s3_g = '%12.10f' % (sbarg[2])
            s4_g = '%12.10f' % (sbarg[3])
            s5_g = '%12.10f' % (sbarg[4])
            s6_g = '%12.10f' % (sbarg[5])
            if data_model_num == 2:
                AniRecG["anisotropy_s1"] = s1_g
                AniRecG["anisotropy_s2"] = s2_g
                AniRecG["anisotropy_s3"] = s3_g
                AniRecG["anisotropy_s4"] = s4_g
                AniRecG["anisotropy_s5"] = s5_g
                AniRecG["anisotropy_s6"] = s6_g
            else:
                vals = (s1_g, s2_g, s3_g, s4_g, s5_g, s6_g)
                AniRecG['aniso_s'] = ":".join([v.strip() for v in vals])
            AniRecG[aniso_tilt_corr_col] = '0'
            AniRecs.append(AniRecG)
            if bed_dip != "" and bed_dip != 0:  # have tilt correction
                sbart = pmag.dostilt(sbarg, dip_direction, bed_dip)
                s1_t = '%12.10f' % (sbart[0])
                s2_t = '%12.10f' % (sbart[1])
                s3_t = '%12.10f' % (sbart[2])
                s4_t = '%12.10f' % (sbart[3])
                s5_t = '%12.10f' % (sbart[4])
                s6_t = '%12.10f' % (sbart[5])
                if data_model_num == 2:
                    AniRecT["anisotropy_s1"] = s1_t
                    AniRecT["anisotropy_s2"] = s2_t
                    AniRecT["anisotropy_s3"] = s3_t
                    AniRecT["anisotropy_s4"] = s4_t
                    AniRecT["anisotropy_s5"] = s5_t
                    AniRecT["anisotropy_s6"] = s6_t
                else:
                    vals = (s1_t, s2_t, s3_t, s4_t, s5_t, s6_t)
                    AniRecT["aniso_s"] = ":".join([v.strip() for v in vals])
                AniRecT[aniso_tilt_corr_col] = '100'
                AniRecs.append(AniRecT)
            MeasRecs.append(MeasRec)
            if SpecRec[spec_name_col] not in specnames:
                SpecRecs.append(SpecRec)
                specnames.append(SpecRec[spec_name_col])
            if SampRec[samp_name_col] not in sampnames:
                SampRecs.append(SampRec)
                sampnames.append(SampRec[samp_name_col])
            if SiteRec[site_name_col] not in sitenames:
                SiteRecs.append(SiteRec)
                sitenames.append(SiteRec[site_name_col])
        k += 1  # skip to next specimen

    pmag.magic_write(meas_output, MeasRecs, meas_table_name)
    print("bulk measurements put in ", meas_output)
    # if isspec=="0":
    SpecOut, keys = pmag.fillkeys(SpecRecs)
    #
    # for MagIC 2, anisotropy records go in rmag_anisotropy
    if data_model_num == 2:
        pmag.magic_write(aniso_output, AniRecs, 'rmag_anisotropy')
        print("anisotropy tensors put in ", aniso_output)
    # for MagIC 3, anisotropy records go in specimens
    if data_model_num == 3:
        full_SpecOut = []
        spec_list = []
        for rec in SpecOut:
            full_SpecOut.append(rec)
            spec_name = rec[spec_name_col]
            if spec_name not in spec_list:
                spec_list.append(spec_name)
                ani_recs = pmag.get_dictitem(AniRecs, spec_name_col, spec_name, 'T')
                full_SpecOut.extend(ani_recs)


        # FILL KEYS
        full_SpecOut, keys = pmag.fillkeys(full_SpecOut)
    else:
        full_SpecOut = SpecOut
    pmag.magic_write(spec_outfile, full_SpecOut, spec_table_name)
    print("specimen/anisotropy info put in ", spec_outfile)
    SampOut, keys = pmag.fillkeys(SampRecs)
    pmag.magic_write(samp_outfile, SampOut, samp_table_name)
    print("sample info put in ", samp_outfile)
    SiteOut, keys = pmag.fillkeys(SiteRecs)
    pmag.magic_write(site_outfile, SiteOut, site_table_name)
    print("site info put in ", site_outfile)
    return True, meas_output


def tdt(input_dir_path, experiment_name="Thellier", meas_file_name="measurements.txt",
        spec_file_name="specimens.txt", samp_file_name="samples.txt",
        site_file_name="sites.txt", loc_file_name="locations.txt",
        user="", location="", lab_dec=0, lab_inc=90, moment_units="mA/m",spec_name_con=1,
        samp_name_con="sample=specimen", samp_name_chars=0,
        site_name_con="site=sample", site_name_chars=0, volume=12.,
        output_dir_path="",verbose=False):

    """
    converts TDT formatted files to measurements format files

    Parameters
    ----------
    input_dir_path : str
        directory with one or more .tdt files
    experiment: str
        one of: ["Thellier", "ATRM 6 pos", "NLT"], default "Thellier"
    meas_file_name : str
        default "measurements.txt"
    spec_file_name : str
        default "specimens.txt"
    samp_file_name : str
        default "samples.txt"
    site_file_name : str
        default "sites.txt"
    loc_file_name : str
        default "locations.txt"
    user : str
        default ""
    location : str
        default ""
    lab_dec: int
        default: 0
    lab_inc: int
        default 90
    moment_units : str
        must be one of: ["mA/m", "emu", "Am^2"], default "mA/m"
    spec_name_con : int 
        1 : specimen=spec_name, where "spec_name" is the first column in the file
        2 : specimen=filename, where filename is the name of the file without the extension '.tdt' of 'TDT'
        default = 1
    samp_name_con : str or int
        {1: "sample=specimen", 2: "no. of terminate characters", 3: "character delimited"}
    samp_name_chars : str or int
        number of characters to remove for sample name, (or delimiting character), default 0
    site_name_con : str or int
        {1: "site=sample", 2: "no. of terminate characters", 3: "character delimited"}
    site_name_chars : str or int
        number of characters to remove for site name, (or delimiting character), default 0
    volume : float
        volume in cc, default 12
    output_dir_path : str
        path for file output, defaults to input_dir_path


    Returns
    ---------
    tuple : (True if program ran else False, measurement outfile name or error message if failed)
    """

    # --------------------------------------
    # Read the files
    #
    # Database structure
    # Thellier_type experiment:
    #
    # 1) Each file contains the data one specimen
    # 2) First line is the header: "Thellier-tdt"
    # 3) Second line in header inlucdes 4 fields:
    #    [Blab] ,[unknown_1] , [unknown_2] , [unknown_3] , [unknown_4]
    # 4) Body includes 5 fields
    #    [specimen_name], [treatments], [moment],[meas_dec],[meas_dec
    # Tretment: XXX.0 (zerofield)
    #           XXX.1 (infield)
    #           XXX.2 (pTRM check)
    #           XXX.3 (Tail check)
    #           XXX.4 (Additivity check; Krasa et al., 2003)
    #           XXX.5 (Original Thellier-Thellier protocol. )
    #                 (where .5 is for the second direction and .1 in the first)
    # XXX = temperature in degrees
    #
    #
    # IMPORTANT ASSUMPTION:
    # (1) lab field is always in Z direction (theta=0, phi=90)
    # (2) Thermal demagnetization - NO MICROWAVE
    # (3) if if XXX <50 then assuming that this is NRM (273K)
    #
    # -------------------------------------
    #
    #   ATRM in six positions
    #
    # Treatment: XXX.0 zerofield
    #           XXX.1 +x
    #           XXX.2 +y
    #           XXX.3 +z
    #           XXX.4 -x
    #           XXX.5 -y
    #           XXX.6 -z
    #           XXX.7 alteration check
    #   IMPORTANT REMARKS:
    #
    # (1) If the program check if the direction of the magnetization fits the coding above
    # if not, an error message will appear
    # (2) Alteration ckeck can be in any direction
    # (3) the order of the measurements is not important
    #


    def get_sample_name(specimen, sample_naming_convention):
        if sample_naming_convention[0] == "sample=specimen":
            sample = specimen
        elif sample_naming_convention[0] == "no. of terminate characters":
            n = int(sample_naming_convention[1])*-1
            sample = specimen[:n]
        elif sample_naming_convention[0] == "charceter delimited":
            d = sample_naming_convention[1]
            sample_splitted = specimen.split(d)
            if len(sample_splitted) == 1:
                sample = sample_splitted[0]
            else:
                sample = d.join(sample_splitted[:-1])
        return sample

    def get_site_name(sample, site_naming_convention):
        if site_naming_convention[0] == "site=sample":
            site = sample
        elif site_naming_convention[0] == "no. of terminate characters":
            n = int(site_naming_convention[1])*-1
            site = sample[:n]
        elif site_naming_convention[0] == "charceter delimited":
            d = site_naming_convention[1]
            site_splitted = sample.split(d)
            if len(site_splitted) == 1:
                site = site_splitted[0]
            else:
                site = d.join(site_splitted[:-1])
        return site

    ## format some variables

    # convert volume from cc to m^3
    volume = float(volume) * 1e-6
    if not output_dir_path:
        output_dir_path = input_dir_path
    samp_name_cons = {1: 'sample=specimen', 2: 'no. of terminate characters', 3: 'character delimited'}
    if not samp_name_con:
        samp_name_con = "sample=specimen"
    elif samp_name_con not in samp_name_cons.values():
        try:
            samp_name_con =  samp_name_cons.get(int(samp_name_con), 'sample=specimen')
        except ValueError:
            samp_name_con="sample=specimen"
    if samp_name_con == 'no. of terminate characters' and not samp_name_chars:
        print("-W- You have selected the sample naming convention: 'no. of terminate characters',\n    but have provided the number of characters as 0.\n    Defaulting to use 'sample=specimen' instead.")
        samp_name_con = 'sample=specimen'

    site_name_cons =  {1: 'site=sample', 2: 'no. of terminate characters', 3: 'character delimited'}
    if not site_name_con:
        site_name_con = "site=sample"
    elif site_name_con not in site_name_cons.values():
        try:
            site_name_con = site_name_cons.get(int(site_name_con), 'site=sample')
        except ValueError:
            site_name_con = "site=sample"
    if site_name_con == 'no. of terminate characters' and not site_name_chars:
        print("-W- You have selected the site naming convention: 'no. of terminate characters',\n    but have provided the number of characters as 0.\n    Defaulting to use 'site=sample' instead.")
        site_name_con = 'site=sample'

    Data = {}

    # -----------------------------------
    # First, read all files and sort data by specimen and by Experiment type
    # -----------------------------------

    for files in os.listdir(input_dir_path):
        if files.endswith(".tdt"):
            fname = os.path.join(input_dir_path, files)
            if verbose:print("Open file: ", fname)
            fin = open(fname, 'r')
            header_codes = ['labfield', 'core_azimuth',
                            'core_plunge', 'bedding_dip_direction', 'bedding_dip']
            body_codes = ['specimen_name',
                          'treatment', 'moment', 'dec', 'inc']
            tmp_body = []
            tmp_header_data = {}
            line_number = 0
            continue_reading = True
            line = fin.readline()  # ignore first line
            lines = fin.readlines()
            fin.close()
            for line in lines:

                if "END" in line:
                    break

                if line.strip('\n') == "":
                    break

                this_line = line.strip('\n').split()

                if len(this_line) < 5:
                    continue

                # ---------------------------------------------------
                # fix muxworthy funky data format
                # ---------------------------------------------------
                if len(this_line) < 5 and line_number != 0:
                    new_line = []
                    for i in range(len(this_line)):
                        if i > 1 and "-" in this_line[i]:
                            tmp = this_line[i].replace("-", " -")
                            tmp1 = tmp.split()
                            for i in range(len(tmp1)):
                                new_line.append(tmp1[i])
                        else:
                            new_line.append(this_line[i])
                    this_line = list(copy(new_line))

                # -------------------------------
                # Read information from Header and body
                # The data is stored in a dictionary:
                # Data[specimen][Experiment_Type]['header_data']=tmp_header_data  --> a dictionary with header data
                # Data[specimen][Experiment_Type]['meas_data']=[dict1, dict2, ...] --> a list of dictionaries with measurement data
                # -------------------------------

                # ---------------------------------------------------
                # header
                # ---------------------------------------------------
                if line_number == 0:

                    for i in range(len(this_line)):
                        tmp_header_data[header_codes[i]] = this_line[i]

                    line_number += 1

                # ---------------------------------------------------
                # body
                # ---------------------------------------------------

                else:
                    tmp_data = {}
                    for i in range(min(len(this_line), len(body_codes))):
                        tmp_data[body_codes[i]] = this_line[i]
                    tmp_body.append(tmp_data)

                    # ------------

                    if spec_name_con==1:
                        specimen = tmp_body[0]['specimen_name']
                    else:
                        if 'TDT' in fname:
                            specimen=fname.split("/")[-1].strip('.TDT')
                        elif 'tdt' in fname:
                            specimen=fname.split("/")[-1].strip('.tdt')
                    line_number += 1

            if specimen not in list(Data.keys()):
                Data[specimen] = {}
            Experiment_Type = experiment_name
            if Experiment_Type not in list(Data[specimen].keys()):
                Data[specimen][Experiment_Type] = {}
            Data[specimen][Experiment_Type]['meas_data'] = tmp_body
            Data[specimen][Experiment_Type]['header_data'] = tmp_header_data
            Data[specimen][Experiment_Type]['sample_naming_convention'] = [samp_name_con, samp_name_chars]
            Data[specimen][Experiment_Type]['site_naming_convention'] = [site_name_con, site_name_chars]
            Data[specimen][Experiment_Type]['location'] = location
            Data[specimen][Experiment_Type]['user_name'] = user
            Data[specimen][Experiment_Type]['volume'] = volume
            Data[specimen][Experiment_Type]['moment_units'] = moment_units
            Data[specimen][Experiment_Type]['labfield_DI'] = [lab_dec, lab_inc]

    # -----------------------------------
    # Convert Data{} to MagIC
    # -----------------------------------
    MeasRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    specimens_list = list(Data.keys())
    specimens_list.sort()
    for specimen in specimens_list:
        Experiment_Types_list = list(Data[specimen].keys())
        Experiment_Types_list.sort()
        for Experiment_Type in Experiment_Types_list:
            if Experiment_Type in ["Thellier"]:

                tmp_MeasRecs = []

                # IMORTANT:
                # phi and theta of lab field are not defined
                # defaults are defined here:
                phi, theta = '0.', '90.'

                header_line = Data[specimen][Experiment_Type]['header_data']
                experiment_treatments = []
                measurement_running_number = 0
                # start to make a list of the methcodes. and later will merge it to one string
                methcodes = ["LP-PI-TRM"]

                for i in range(len(Data[specimen][Experiment_Type]['meas_data'])):
                    meas_line = Data[specimen][Experiment_Type]['meas_data'][i]

                    # ------------------
                    # check if the same treatment appears more than once. If yes, assuming that the measurements is repeated twice,
                    # ignore the first, and take only the second one
                    # ------------------

                    if i < (len(Data[specimen][Experiment_Type]['meas_data'])-2):
                        Repeating_measurements = True
                        for key in ['treatment', 'specimen_name']:
                            if Data[specimen][Experiment_Type]['meas_data'][i][key] != Data[specimen][Experiment_Type]['meas_data'][i+1][key]:
                                Repeating_measurements = False
                        if Repeating_measurements == True:
                            "Found a repeating measurement at line %i, sample %s. taking the last one" % (
                                i, specimen)
                            continue
                    # ------------------
                    # Special treatment for first line (NRM data).
                    # ------------------

                    if i == 0:
                        if "." not in meas_line['treatment']:
                            meas_line['treatment'] = "0.0"
                        # if NRM is in the form of ".0" instead of "0.0"
                        elif meas_line['treatment'].split(".")[0] == "" and meas_line['treatment'].split(".")[1] == '0':
                            meas_line['treatment'] = "0.0"
                        # if NRM is in the form of "20.0" instead of "0.0"
                        elif float(meas_line['treatment'].split(".")[0]) < 50 and float(meas_line['treatment'].split(".")[-1]) == 0:
                            meas_line['treatment'] = "0.0"

                    # ------------------
                    # fix line in format of XX instead of XX.YY
                    # ------------------
                    if "." not in meas_line['treatment']:
                        meas_line['treatment'] = meas_line['treatment']+".0"
                    if meas_line['treatment'].split(".")[1] == "":
                        meas_line['treatment'] = meas_line['treatment']+"0"

                    # ------------------
                    # init names and dictionaries
                    # ------------------

                    MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}

                    # convert from microT to Tesla
                    labfield = float(header_line['labfield'])*1e-6
                    sample = get_sample_name(
                        specimen, Data[specimen][Experiment_Type]['sample_naming_convention'])
                    site = get_site_name(
                        sample, Data[specimen][Experiment_Type]['site_naming_convention'])
                    location = Data[specimen][Experiment_Type]['location']
                    if location == '':
                        location = 'unknown'

                    # ------------------
                    # Fill data
                    # ------------------

                    # Start with S'tables and Loc Table
                    if specimen != "" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
                        SpecRec['specimen'] = specimen
                        SpecRec['sample'] = sample
                        SpecRec['volume'] = Data[specimen][Experiment_Type]['volume']
                        SpecRec['citations'] = "This study"
                        SpecRec['analysts'] = Data[specimen][Experiment_Type]['user_name']
                        SpecRecs.append(SpecRec)
                    if sample != "" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
                        SampRec['sample'] = sample
                        SampRec['site'] = site
                        SampRec['citations'] = "This study"
                        SampRec['analysts'] = Data[specimen][Experiment_Type]['user_name']
                        SampRecs.append(SampRec)
                    if site != "" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
                        SiteRec['site'] = site
                        SiteRec['location'] = location
                        SiteRec['citations'] = "This study"
                        SiteRec['analysts'] = Data[specimen][Experiment_Type]['user_name']
                        SiteRecs.append(SiteRec)
                    if location != "" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
                        LocRec['location'] = location
                        LocRec['citations'] = "This study"
                        LocRec['analysts'] = Data[specimen][Experiment_Type]['user_name']
                        LocRecs.append(LocRec)

                    # now the measurement Rec
                    MeasRec['citations'] = "This study"
                    # experiment is set in pmag.measurements_methods3
                    # MeasRec["experiments"]=""
                    MeasRec["specimen"] = specimen
                    MeasRec['analysts'] = Data[specimen][Experiment_Type]['user_name']
                    MeasRec["quality"] = 'g'
                    MeasRec["standard"] = 'u'
                    MeasRec["treat_step_num"] = "%i" % measurement_running_number
                    MeasRec["dir_dec"] = meas_line['dec']
                    MeasRec["dir_inc"] = meas_line['inc']
                    if Data[specimen][Experiment_Type]['moment_units'] == 'mA/m':
                        MeasRec["magn_moment"] = "%5e" % (float(meas_line['moment'])*1e-3*float(
                            Data[specimen][Experiment_Type]['volume']))  # converted to Am^2
                    if Data[specimen][Experiment_Type]['moment_units'] == 'emu':
                        MeasRec["magn_moment"] = "%5e" % (
                            float(meas_line['moment'])*1e-3)  # converted to Am^2
                    if Data[specimen][Experiment_Type]['moment_units'] == 'Am^2':
                        MeasRec["magn_moment"] = "%5e" % (
                            float(meas_line['moment']))  # converted to Am^2
                    MeasRec["meas_temp"] = '273.'  # room temp in kelvin

                    # Date and time
##                                    date=meas_line['Measurement Date'].strip("\"").split('-')
# yyyy=date[2];dd=date[1];mm=date[0]
##                                    hour=meas_line['Measurement Time'].strip("\"")
# MeasRec["measurement_date"]=yyyy+':'+mm+":"+dd+":"+hour

                    # lab field data: distinguish between PI experiments to AF/Thermal
                    treatments = meas_line['treatment'].split(".")
                    if float(treatments[1]) == 0:
                        MeasRec["treat_dc_field"] = '0'
                        MeasRec["treat_dc_field_phi"] = '0'
                        MeasRec["treat_dc_field_theta"] = '0'
                    else:
                        MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                        MeasRec["treat_dc_field_phi"] = Data[specimen][Experiment_Type]['labfield_DI'][0]
                        MeasRec["treat_dc_field_theta"] = Data[specimen][Experiment_Type]['labfield_DI'][1]

                    # ------------------
                    # Lab Treatments
                    # ------------------

                    # NRM
                    if float(treatments[0]) == 0 and float(treatments[1]) == 0:
                        MeasRec["method_codes"] = "LT-NO"
                        experiment_treatments.append('0')
                        MeasRec["treat_temp"] = '273.'
                        IZorZI = ""

                    # Zerofield step
                    elif float(treatments[1]) == 0:
                        MeasRec["method_codes"] = "LT-T-Z"
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatments[0])+273.)  # temp in kelvin

                        #  check if this is ZI or IZ:
                        for j in range(0, i):
                            previous_lines = Data[specimen][Experiment_Type]['meas_data'][j]
                            if previous_lines['treatment'].split(".")[0] == meas_line['treatment'].split(".")[0]:
                                if float(previous_lines['treatment'].split(".")[1]) == 1 or float(previous_lines['treatment'].split(".")[1]) == 10:
                                    if "LP-PI-TRM-IZ" not in methcodes:
                                        methcodes.append("LP-PI-TRM-IZ")
                                    IZorZI = ""
                                else:
                                    IZorZI = "Z"

                    # Infield step
                    elif float(treatments[1]) == 1 or float(treatments[1]) == 10 or float(treatments[1]) == 11:
                        MeasRec["method_codes"] = "LT-T-I"
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatments[0])+273.)  # temp in kelvin

                        # check if this is ZI,IZ:
                        for j in range(0, i):
                            previous_lines = Data[specimen][Experiment_Type]['meas_data'][j]
                            if previous_lines['treatment'].split(".")[0] == meas_line['treatment'].split(".")[0]:
                                if float(previous_lines['treatment'].split(".")[1]) == 0:
                                    if "LP-PI-TRM-ZI" not in methcodes:
                                        methcodes.append("LP-PI-TRM-ZI")
                                        IZorZI = ""
                                else:
                                    IZorZI = "I"
                    # pTRM check step
                    elif float(treatments[1]) == 2 or float(treatments[1]) == 20 or float(treatments[1]) == 12:
                        MeasRec["method_codes"] = "LT-PTRM-I"
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatments[0])+273.)  # temp in kelvin
                        if "LP-PI-ALT" not in methcodes:
                            methcodes.append("LP-PI-ALT")

                    # Tail check step
                    elif float(treatments[1]) == 3 or float(treatments[1]) == 30 or float(treatments[1]) == 13:
                        MeasRec["method_codes"] = "LT-PTRM-MD"
                        MeasRec["treat_dc_field"] = "0"
                        MeasRec["treat_dc_field_phi"] = "0"
                        MeasRec["treat_dc_field_theta"] = "0"
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatments[0])+273.)  # temp in kelvin
                        if "LP-PI-BT-MD" not in methcodes:
                            methcodes.append("LP-PI-BT-MD")
                            MeasRec["treat_dc_field"] = "0"
                            MeasRec["treat_dc_field_phi"] = "0"
                            MeasRec["treat_dc_field_theta"] = "0"

                    # Additivity check step
                    elif float(treatments[1]) == 4 or float(treatments[1]) == 40 or float(treatments[1]) == 14:
                        MeasRec["method_codes"] = "LT-PTRM-AC"
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatments[0])+273.)  # temp in kelvin
                        if "LP-PI-BT" not in methcodes:
                            methcodes.append("LP-PI-BT")

                    # Thellier Thellier protocol (1 for one direction and 5 for the antiparallel)
                    # Lab field direction of 1 is as put in the GUI dialog box
                    # Lab field direction of 5 is the anti-parallel direction of 1

                    elif float(treatments[1]) == 5 or float(treatments[1]) == 50:
                        MeasRec["method_codes"] = "LT-T-I"
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatments[0])+273.)  # temp in kelvin
                        MeasRec["treat_dc_field_phi"] = "%.2f" % (
                            (float(Data[specimen][Experiment_Type]['labfield_DI'][0])+180.) % 360.)
                        MeasRec["treat_dc_field_theta"] = "%.2f" % (
                            float(Data[specimen][Experiment_Type]['labfield_DI'][1])*-1.)
                        if "LP-PI-II" not in methcodes:
                            methcodes.append("LP-PI-II")

                    else:
                        print("-E- ERROR in file %s" % Experiment_Type)
                        print("-E- ERROR in treatment ",
                              meas_line['treatment'])
                        print("... exiting until you fix the problem")

                    # -----------------------------------

                    # MeasRec["method_codes"]=lab_treatment+":"+lab_protocols_string
                    # MeasRec["experiments"]=specimen+":"+lab_protocols_string

                    tmp_MeasRecs.append(MeasRec)
                    measurement_running_number += 1

                # arrange method_codes and experiments:
                method_codes = "LP-PI-TRM"
                # Coe mothod
                if "LP-PI-TRM-ZI" in methcodes and "LP-PI-TRM-IZ" not in methcodes and "LP-PI-II" not in methcodes:
                    method_codes = method_codes+":LP-PI-TRM-ZI"
                if "LP-PI-TRM-ZI" not in methcodes and "LP-PI-TRM-IZ" in methcodes and "LP-PI-II" not in methcodes:
                    method_codes = method_codes+":LP-PI-TRM-IZ"
                if "LP-PI-TRM-ZI" in methcodes and "LP-PI-TRM-IZ" in methcodes and "LP-PI-II" not in methcodes:
                    method_codes = method_codes+":LP-PI-BT-IZZI"
                if "LP-PI-II" in methcodes:
                    method_codes = method_codes+":LP-PI-II"
                if "LP-PI-ALT" in methcodes:
                    method_codes = method_codes+":LP-PI-ALT"
                if "LP-PI-BT-MD" in methcodes:
                    method_codes = method_codes+":LP-PI-BT-MD"
                if "LP-PI-BT" in methcodes:
                    method_codes = method_codes+":LP-PI-BT"
                for i in range(len(tmp_MeasRecs)):
                    STRING = ":".join(
                        [tmp_MeasRecs[i]["method_codes"], method_codes])
                    tmp_MeasRecs[i]["method_codes"] = STRING
                    # experiment is set in pmag.measurements_methods3
                    # STRING=":".join([tmp_MeasRecs[i]["specimen"],method_codes])
                    # tmp_MeasRecs[i]["experiments"]=STRING
                    MeasRecs.append(tmp_MeasRecs[i])

            elif Experiment_Type in ["ATRM 6 positions"]:

                tmp_MeasRecs = []

                header_line = Data[specimen][Experiment_Type]['header_data']
                experiment_treatments = []
                measurement_running_number = 0
                # start to make a list of the methcodes. and later will merge it to one string
                methcodes = ["LP-AN-TRM"]

                for i in range(len(Data[specimen][Experiment_Type]['meas_data'])):
                    meas_line = Data[specimen][Experiment_Type]['meas_data'][i]

                    # ------------------
                    # check if the same treatment appears more than once. If yes, assuming that the measurements is repeated twice,
                    # ignore the first, and take only the second one
                    # ------------------

                    if i < (len(Data[specimen][Experiment_Type]['meas_data'])-2):
                        Repeating_measurements = True
                        for key in ['treatment', 'specimen_name']:
                            if Data[specimen][Experiment_Type]['meas_data'][i][key] != Data[specimen][Experiment_Type]['meas_data'][i+1][key]:
                                Repeating_measurements = False
                        if Repeating_measurements == True:
                            "Found a repeating measurement at line %i, sample %s. taking the last one" % (
                                i, specimen)
                            continue

                    # ------------------
                    # fix line in format of XX instead of XX.0
                    # ------------------
                    if "." not in meas_line['treatment']:
                        meas_line['treatment'] = meas_line['treatment']+".0"
                    if meas_line['treatment'].split(".")[1] == "":
                        meas_line['treatment'] = meas_line['treatment']+"0"

                    # ------------------
                    # init names and dictionaries
                    # ------------------

                    MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}

                    # convert from microT to Tesla
                    labfield = float(header_line['labfield'])*1e-6
                    sample = get_sample_name(
                        specimen, Data[specimen][Experiment_Type]['sample_naming_convention'])
                    site = get_site_name(
                        sample, Data[specimen][Experiment_Type]['site_naming_convention'])
                    location = Data[specimen][Experiment_Type]['location']

                    # ------------------
                    # Fill data
                    # ------------------

                    # Start with S'tables and Loc Table
                    if specimen != "" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
                        SpecRec['specimen'] = specimen
                        SpecRec['sample'] = sample
                        SpecRec['volume'] = Data[specimen][Experiment_Type]['volume']
                        SpecRec['citations'] = "This study"
                        SpecRec['analysts'] = Data[specimen][Experiment_Type]['user_name']
                        SpecRecs.append(SpecRec)
                    if sample != "" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
                        SampRec['sample'] = sample
                        SampRec['site'] = site
                        SampRec['citations'] = "This study"
                        SampRec['analysts'] = Data[specimen][Experiment_Type]['user_name']
                        SampRecs.append(SampRec)
                    if site != "" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
                        SiteRec['site'] = site
                        SiteRec['location'] = location
                        SiteRec['citations'] = "This study"
                        SiteRec['analysts'] = Data[specimen][Experiment_Type]['user_name']
                        SiteRecs.append(SiteRec)
                    if location != "" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
                        LocRec['location'] = location
                        LocRec['citations'] = "This study"
                        LocRec['analysts'] = Data[specimen][Experiment_Type]['user_name']
                        LocRecs.append(LocRec)

                    # Meas data now
                    MeasRec["specimen"] = specimen
                    MeasRec['analysts'] = Data[specimen][Experiment_Type]['user_name']
                    MeasRec['citations'] = "This study"
                    MeasRec["quality"] = 'g'
                    MeasRec["standard"] = 'u'
                    MeasRec["treat_step_num"] = "%i" % measurement_running_number
                    MeasRec["dir_dec"] = meas_line['dec']
                    MeasRec["dir_inc"] = meas_line['inc']
                    MeasRec["magn_moment"] = "%5e" % (float(meas_line['moment'])*1e-3*float(
                        Data[specimen][Experiment_Type]['volume']))  # converted to Am^2
                    MeasRec["meas_temp"] = '273.'  # room temp in kelvin

                    treatments = meas_line['treatment'].split(".")
                    if len(treatments[1]) > 1:
                        treatments[1] = treatments[1][0]

                    MeasRec["treat_temp"] = '%8.3e' % (
                        float(treatments[0])+273.)  # temp in kelvin

                    # labfield direction
                    if float(treatments[1]) == 0:
                        MeasRec["treat_dc_field"] = '0'
                        MeasRec["treat_dc_field_phi"] = '0'
                        MeasRec["treat_dc_field_theta"] = '0'
                        MeasRec["method_codes"] = "LT-T-Z:LP-AN-TRM"
                    else:

                        MeasRec["treat_dc_field"] = '%8.3e' % (labfield)

                        # alteration check as final measurement
                        if float(treatments[1]) == 7 or float(treatments[1]) == 70:
                            MeasRec["method_codes"] = "LT-PTRM-I:LP-AN-TRM"
                        else:
                            MeasRec["method_codes"] = "LT-T-I:LP-AN-TRM"

                        # find the direction of the lab field in two ways:
                        # (1) using the treatment coding (XX.1=+x, XX.2=+y, XX.3=+z, XX.4=-x, XX.5=-y, XX.6=-z)
                        # atrm declination/inlclination order
                        tdec = [0, 90, 0, 180, 270, 0, 0, 90, 0]
                        # atrm declination/inlclination order
                        tinc = [0, 0, 90, 0, 0, -90, 0, 0, 90]

                        ipos_code = int(treatments[1])-1
                        # (2) using the magnetization
                        DEC = float(MeasRec["dir_dec"])
                        INC = float(MeasRec["dir_inc"])
                        if INC < 45 and INC > -45:
                            if DEC > 315 or DEC < 45:
                                ipos_guess = 0
                            if DEC > 45 and DEC < 135:
                                ipos_guess = 1
                            if DEC > 135 and DEC < 225:
                                ipos_guess = 3
                            if DEC > 225 and DEC < 315:
                                ipos_guess = 4
                        else:
                            if INC > 45:
                                ipos_guess = 2
                            if INC < -45:
                                ipos_guess = 5
                        # prefer the guess over the code
                        ipos = ipos_guess
                        MeasRec["treat_dc_field_phi"] = '%7.1f' % (
                            tdec[ipos])
                        MeasRec["treat_dc_field_theta"] = '%7.1f' % (
                            tinc[ipos])
                        # check it
                        if ipos_guess != ipos_code and treatments[1] != '7':
                            print("-E- ERROR: check specimen %s step %s, ATRM measurements, coding does not match the direction of the lab field!" % (
                                MeasRec["specimen"], ".".join(list(treatments))))

                    MeasRecs.append(MeasRec)
                    measurement_running_number += 1

            else:
                print(
                    "-E- ERROR. sorry, file format %s is not supported yet. Please contact rshaar@ucsd.edu" % Experiment_Type)

    # -------------------------------------------
    #  measurements.txt
    # -------------------------------------------

    con = cb.Contribution(output_dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    #MeasOuts = pmag.measurements_methods3(MeasRecs, noave=False)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave=True)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)
    con.write_table_to_file('specimens', spec_file_name)
    con.write_table_to_file('samples', samp_file_name)
    con.write_table_to_file('sites', site_file_name)
    con.write_table_to_file('locations', loc_file_name)
    meas_file = con.write_table_to_file('measurements', meas_file_name)
    return True, meas_file

    # -------------------------------------------


### Utrecht conversion

def utrecht(mag_file, dir_path=".",  input_dir_path="", meas_file="measurements.txt",
            spec_file="specimens.txt", samp_file="samples.txt", site_file="sites.txt",
            loc_file="locations.txt", location="unknown", lat="", lon="", dmy_flag=False,
            noave=False, meas_n_orient=8, meth_code="LP-NO", specnum=1, samp_con='2',
            labfield=0, phi=0, theta=0):
    """
    Converts Utrecht magnetometer data files to MagIC files

    Parameters
    ----------
    mag_file : str
        input file name
    dir_path : str
        working directory, default "."
    input_dir_path : str
        input file directory IF different from dir_path, default ""
    spec_file : str
        output specimen file name, default "specimens.txt"
    samp_file: str
        output sample file name, default "samples.txt"
    site_file : str
        output site file name, default "sites.txt"
    loc_file : str
        output location file name, default "locations.txt"
    append : bool
        append output files to existing files instead of overwrite, default False
    location : str
        location name, default "unknown"
    lat : float
        latitude, default ""
    lon : float
        longitude, default ""
    dmy_flag : bool
        default False
    noave : bool
       do not average duplicate measurements, default False (so by default, DO average)
    meas_n_orient : int
        Number of different orientations in measurement (default : 8)
    meth_code : str
        sample method codes, default "LP-NO"
        e.g. [SO-MAG, SO-SUN, SO-SIGHT, ...]
    specnum : int
        number of characters to designate a specimen, default 0
    samp_con : str
        sample/site naming convention, default '2', see info below
    labfield : float
        DC_FIELD in microTesla (default : 0)
    phi : float
        DC_PHI in degrees (default : 0)
    theta : float
        DC_THETA in degrees (default : 0)

    Returns
    ----------
    type - Tuple : (True or False indicating if conversion was successful, meas_file name written)

    Info
    ---------
    Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY


    """
    # initialize some stuff
    version_num = pmag.get_version()
    MeasRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, dir_path)
    specnum = -int(specnum)
    if "4" in samp_con:
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            site_num = samp_con.split("-")[1]
            samp_con = "4"
    elif "7" in samp_con:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
        else:
            site_num = samp_con.split("-")[1]
            samp_con = "7"
    else:
        site_num = 1
    try:
        DC_FIELD = float(labfield)*1e-6
        DC_PHI = float(phi)
        DC_THETA = float(theta)
    except ValueError:
        raise ValueError(
            'problem with your dc parameters. please provide a labfield in microTesla and a phi and theta in degrees.')

    # format variables
    if not mag_file:
        return False, 'You must provide a Utrecht format file'
    mag_file = pmag.resolve_file_name(mag_file, input_dir_path)
    # need to add these
    meas_file = pmag.resolve_file_name(meas_file, output_dir_path)
    spec_file = pmag.resolve_file_name(spec_file, output_dir_path)
    samp_file = pmag.resolve_file_name(samp_file, output_dir_path)
    site_file = pmag.resolve_file_name(site_file, output_dir_path)
    loc_file = pmag.resolve_file_name(loc_file, output_dir_path)


    # parse data

    # Open up the Utrecht file and read the header information
    AF_or_T = mag_file.split('.')[-1]
    data = open(mag_file, 'r')
    line = data.readline()
    line_items = line.split(',')
    operator = line_items[0]
    operator = operator.replace("\"", "")
    machine = line_items[1]
    machine = machine.replace("\"", "")
    machine = machine.rstrip('\n')
#    print("operator=", operator)
#    print("machine=", machine)

    # read in measurement data
    line = data.readline()
    while line != "END" and line != '"END"':
        SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}
        line_items = line.split(',')
        spec_name = line_items[0]
        spec_name = spec_name.replace("\"", "")
#        print("spec_name=", spec_name)
        free_string = line_items[1]
        free_string = free_string.replace("\"", "")
#        print("free_string=", free_string)
        dec = line_items[2]
#        print("dec=", dec)
        inc = line_items[3]
#        print("inc=", inc)
        volume = float(line_items[4])
        volume = volume * 1e-6  # enter volume in cm^3, convert to m^3
#        print("volume=", volume)
        bed_plane = line_items[5]
#        print("bed_plane=", bed_plane)
        bed_dip = line_items[6]
#        print("bed_dip=", bed_dip)

        # Configure et er_ tables
        if specnum == 0:
            sample_name = spec_name
        else:
            sample_name = spec_name[:specnum]
        site = pmag.parse_site(sample_name, samp_con, site_num)
        SpecRec['specimen'] = spec_name
        SpecRec['sample'] = sample_name
        if volume != 0:
            SpecRec['volume'] = volume
        SpecRecs.append(SpecRec)
        if sample_name != "" and sample_name not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
            SampRec['sample'] = sample_name
            SampRec['azimuth'] = dec
            SampRec['dip'] = str(float(inc)-90)
            SampRec['bed_dip_direction'] = bed_plane
            SampRec['bed_dip'] = bed_dip
            SampRec['method_codes'] = meth_code
            SampRec['site'] = site
            SampRecs.append(SampRec)
        if site != "" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
            SiteRec['site'] = site
            SiteRec['location'] = location
            SiteRec['lat'] = lat
            SiteRec['lon'] = lon
            SiteRecs.append(SiteRec)
        if location != "" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
            LocRec['location'] = location
            LocRec['lat_n'] = lat
            LocRec['lon_e'] = lon
            LocRec['lat_s'] = lat
            LocRec['lon_w'] = lon
            LocRecs.append(LocRec)

        # measurement data
        line = data.readline()
        line = line.rstrip("\n")
        items = line.split(",")
        while line != '9999':
            step = items[0]
            step = step.split('.')
            step_value = step[0]
            step_type = ""
            if len(step) == 2:
                step_type = step[1]
            if step_type == '5':
                step_value = items[0]
            A = float(items[1])
            B = float(items[2])
            C = float(items[3])
#  convert to MagIC coordinates
            Z = -A
            X = -B
            Y = C
            cart = np.array([X, Y, Z]).transpose()
            direction = pmag.cart2dir(cart).transpose()
            measurement_dec = direction[0]
            measurement_inc = direction[1]
            # the data are in pico-Am^2 - this converts to Am^2
            magn_moment = direction[2] * 1.0e-12
            if volume != 0:
                # data volume normalized - converted to A/m
                magn_volume = direction[2] * 1.0e-12 / volume
#            print("magn_moment=", magn_moment)
#            print("magn_volume=", magn_volume)
            error = items[4]
            date = items[5]
            date = date.strip('"').replace(' ', '')
            if date.count("-") > 0:
                date = date.split("-")
            elif date.count("/") > 0:
                date = date.split("/")
            else:
                print("date format separator cannot be identified")
#            print(date)
            time = items[6]
            time = time.strip('"').replace(' ', '')
            time = time.split(":")
#            print(time)
            dt = date[0] + ":" + date[1] + ":" + date[2] + \
                ":" + time[0] + ":" + time[1] + ":" + "0"
            local = pytz.timezone("Europe/Amsterdam")
            try:
                if dmy_flag:
                    naive = datetime.datetime.strptime(dt, "%d:%m:%Y:%H:%M:%S")
                else:
                    naive = datetime.datetime.strptime(dt, "%m:%d:%Y:%H:%M:%S")
            except ValueError:
                try:
                    naive = datetime.datetime.strptime(dt, "%Y:%m:%d:%H:%M:%S")
                except ValueError:
                    print('-W- Could not parse date format')
                    return False, 'Could not parse date format'
            local_dt = local.localize(naive, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            timestamp = utc_dt.strftime("%Y-%m-%dT%H:%M:%S")+"Z"
#            print(timestamp)

            MeasRec = {}
            MeasRec["timestamp"] = timestamp
            MeasRec["analysts"] = operator
            MeasRec["instrument_codes"] = "Utrecht_" + machine
            MeasRec["description"] = "free string = " + free_string
            MeasRec["citations"] = "This study"
            MeasRec['software_packages'] = version_num
            MeasRec["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
            MeasRec["quality"] = 'g'
            MeasRec["standard"] = 'u'
            # will be overwritten by measurements_methods3
            MeasRec["experiment"] = location + site + spec_name
            MeasRec["treat_step_num"] = location + site + spec_name + items[0]
            MeasRec["specimen"] = spec_name
            # MeasRec["treat_ac_field"] = '0'
            if AF_or_T.lower() == "th":
                MeasRec["treat_temp"] = '%8.3e' % (
                    float(step_value)+273.)  # temp in kelvin
                MeasRec['treat_ac_field'] = '0'
                lab_treat_type = "T"
            else:
                MeasRec['treat_temp'] = '273'
                MeasRec['treat_ac_field'] = '%10.3e' % (float(step_value)*1e-3)
                lab_treat_type = "AF"
            MeasRec['treat_dc_field'] = '0'
            if step_value == '0':
                meas_type = "LT-NO"
#            print("step_type=", step_type)
            if step_type == '0' or step_type == '00':
                meas_type = "LT-%s-Z" % lab_treat_type
            elif step_type == '1' or step_type == '11':
                meas_type = "LT-%s-I" % lab_treat_type
                MeasRec['treat_dc_field'] = '%1.2e' % DC_FIELD
            elif step_type == '2' or step_type == '12':
                meas_type = "LT-PTRM-I"
                MeasRec['treat_dc_field'] = '%1.2e' % DC_FIELD
            elif step_type == '3' or step_type == '13':
                meas_type = "LT-PTRM-Z"
#            print("meas_type=", meas_type)
            MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
            MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
            MeasRec['method_codes'] = meas_type
            MeasRec["magn_moment"] = magn_moment
            if volume != 0:
                MeasRec["magn_volume"] = magn_volume
            MeasRec["dir_dec"] = measurement_dec
            MeasRec["dir_inc"] = measurement_inc
            MeasRec['dir_csd'] = error
            MeasRec['meas_n_orient'] = meas_n_orient
#            print(MeasRec)
            MeasRecs.append(MeasRec)

            line = data.readline()
            line = line.rstrip("\n")
            items = line.split(",")
        line = data.readline()
        line = line.rstrip("\n")
        items = line.split(",")

    data.close()

    con = cb.Contribution(output_dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    # figures out method codes for measuremet data
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.tables['specimens'].write_magic_file(custom_name=spec_file)
    con.tables['samples'].write_magic_file(custom_name=samp_file)
    con.tables['sites'].write_magic_file(custom_name=site_file)
    con.tables['locations'].write_magic_file(custom_name=loc_file)
    con.tables['measurements'].write_magic_file(custom_name=meas_file)

    return True, meas_file


### XPEEM experiments

def xpeem(output_dir_path="", input_dir_path="", spec_name="", spec_id="", spec_type="", citation="", spec_age="", spec_age_1s="", dating_method="", dating_unit="", method="", sitenames=[''], nb_samples=[''], paleoint=[''], paleoint_1s=[''], x_spacing=float(), y_spacing=float(), meas_num=int(), exp_num=int()):
    """
    Creates MagIC header file and converts average XPEEM text files into MagIC format for contribution to the MagIC database. The input text files are created from XPEEM average images and must be labelled as follows:
            identifier for the meteorite + interface + location (2 digit) + "-" + rotation (starting with "r") + energy level (on/off) + polarization (L/R)
            
            Example: TeA01-r1offR.txt

    Parameters
    -----------
    output_dir_path : str
        directory to output files to (default : current directory)
    input_dir_path : str
        directory to input files (default : current directory)
    spec_name : str
        specimen full name
    spec_id : str
        specimen short name, identifier
    spec_type : str
        specimen type
    citation : str
        citation (default : This study)
    spec_age : str
        age of the specimen
    spec_age_1s : str
        1 sigma uncertainty on the age of the specimen
    dating_method : str
        dating method (default : GM-ARAR)
    dating_unit : str
        dating unit (default : Ga)
    method : str
        experiment method (default : LP-XPEEM-3)
    sitenames : list of str
        list of names of sites (corresponds to the K-T interfaces)
    nb_samples : list of str
        list of numbers of samples for each site (corresponds to the locations on each K-T interfaces)
    paleoint : list of str
        list of paleointensities for each site
    paleoint_1s : list of str
        list of 1 sigma uncertainties in paleointensity for each site
    x_spacing : float
        set the x spacing of the measurement in meters. Default (LBNL ALS): 9.488e-9 m
    y_spacing : float
        set the y spacing of the measurement in meters. Default (LBNL ALS): 9.709e-9 m
    meas_num: int
        set the starting number for labeling measurement files. Default: 1
    exp_num: int
        set the starting number for labeling measurement files. Default: 1

    Returns
    -----------
    type - int : True or False indicating if conversion was successful
    """

    Header = dict()
    Header["name"] = spec_name
    Header["loc"] = spec_id
    Header["type"] = spec_type
    Header["citation"] = citation
    Header["age"] = spec_age
    Header["age_1s"] = spec_age_1s
    Header["datingmethod"] = dating_method
    Header["datingunit"] = dating_unit
    Header["methodcode"] = method
    Header["sites"] = sitenames
    Header["nbsamples"] = list(map(int,nb_samples))
    Header["paleoint"] = paleoint
    Header["paleoint_1s"] = paleoint_1s
    Header["samples"] = [[str(k).zfill(2) for k in np.arange(1,Header["nbsamples"][j]+1)] for j in np.arange(len(Header["nbsamples"]))]

    fp_header = open(output_dir_path+'/'+Header["name"]+'_MagIC_header.txt','w')
    ## Tab delimited locations ##
    fp_header.write('tab delimited'+'\t'+'locations'+'\n')
    fp_header.write('location'+'\t'+'location_type'+'\t'+'geologic_classes'+'\t'+'lithologies'+'\t'+'lat_s'+'\t'+'lat_n'+'\t'+'lon_w'+'\t'+'lon_e'+'\t'+'method_codes'+'\t'+'age'+'\t'+'age_sigma'+'\t'+'age_unit'+'\n')
    fp_header.write(Header["name"]+'\t'+'Meteorite'+'\t'+'Meteorite'+'\t'+Header["type"]+'\t'+'0'+'\t'+'0'+'\t'+'0'+'\t'+'0'+'\t'+Header["datingmethod"]+'\t'+Header["age"]+'\t'+Header["age_1s"]+'\t'+Header["datingunit"]+'\n')
    fp_header.write('>>>>>>>>>>'+'\n')
    
    ## Tab delimited sites ##
    fp_header.write('tab delimited'+'\t'+'sites'+'\n')
    fp_header.write('site'+'\t'+'location'+'\t'+'result_type'+'\t'+'result_quality'+'\t'+'citations'+'\t'+'geologic_classes'+'\t'+'geologic_types'+'\t'+'lithologies'+'\t'+'lat'+'\t'+'lon'+'\t'+'method_codes'+'\t'+'int_abs'+'\t'+'int_abs_sigma'+'\n')
    for ii in np.arange(len(Header["sites"])):
        fp_header.write('Interface '+Header["sites"][ii]+'\t'+Header["name"]+'\t'+'i'+'\t'+'g'+'\t'+Header["citation"]+'\t'+'Meteorite'+'\t'+'Meteorite'+'\t'+Header["type"]+'\t'+'0'+'\t'+'0'+'\t'+Header["methodcode"]+'\t'+Header["paleoint"][ii]+'\t'+Header["paleoint_1s"][ii]+'\n')
    fp_header.write('>>>>>>>>>>'+'\n')

    ## Tab delimited samples ##
    fp_header.write('tab delimited'+'\t'+'samples'+'\n')
    fp_header.write('sample'+'\t'+'site'+'\t'+'result_type'+'\t'+'result_quality'+'\t'+'method_codes'+'\t'+'citations'+'\t'+'geologic_classes'+'\t'+'geologic_types'+'\t'+'lithologies'+'\n')

    for ii in np.arange(len(Header["sites"])):
        for jj in np.arange(len(Header["samples"][ii])):
            col1 = Header["loc"]+Header["sites"][ii]+Header["samples"][ii][jj]
            col2 = 'Interface '+Header["sites"][ii]
            col3 = 'i'
            col4 = 'g'
            col5 = Header["methodcode"]
            col6 = Header["citation"]
            col7 = 'Meteorite'
            col8 = 'Meteorite'
            col9 = Header["type"]
            fp_header.write(col1+'\t'+col2+'\t'+col3+'\t'+col4+'\t'+col5+'\t'+col6+'\t'+col7+'\t'+col8+'\t'+col9+'\n')
    fp_header.write('>>>>>>>>>>'+'\n')

    ## Tab delimited specimens ##
    fp_header.write('tab delimited'+'\t'+'specimens'+'\n')
    fp_header.write('specimen'+'\t'+'sample'+'\t'+'result_quality'+'\t'+'method_codes'+'\t'+'citations'+'\t'+'geologic_classes'+'\t'+'geologic_types'+'\t'+'lithologies'+'\n')

    for ii in np.arange(len(Header["sites"])):
        for jj in np.arange(len(Header["samples"][ii])):
            col1 = Header["loc"]+Header["sites"][ii]+Header["samples"][ii][jj]
            col2 = Header["loc"]+Header["sites"][ii]+Header["samples"][ii][jj]
            col3 = 'g'
            col4 = Header["methodcode"]
            col5 = Header["citation"]
            col6 = 'Meteorite'
            col7 = 'Meteorite'
            col8 = Header["type"]
            fp_header.write(col1+'\t'+col2+'\t'+col3+'\t'+col4+'\t'+col5+'\t'+col6+'\t'+col7+'\t'+col8+'\n')
    fp_header.close()

    text_files_list=os.listdir(input_dir_path)
    if '.DS_Store' in text_files_list:
        text_files_list.remove('.DS_Store')
    if 'measurements' in text_files_list:
        text_files_list.remove('measurements')
    if Header["name"]+'_MagIC_header.txt' in text_files_list:
        text_files_list.remove(Header["name"]+'_MagIC_header.txt')
    if not os.path.exists(output_dir_path+'/measurements'):
        os.mkdir(output_dir_path+'/measurements')

    for file in sorted(text_files_list):
        if file.split('.')[1] == 'txt':
            experiment_name=file.split('.')[0]
            print(("file=",file))
            specimen=file.split('-')[0]
            mf=open(output_dir_path+'/measurements/measurements'+str(exp_num)+'.txt','w')
            mf.write('tab\tmeasurements\n')
            mf.write('* experiment\t'+experiment_name+'\n')
            mf.write('* specimen\t'+ specimen+'\n')
            mf.write('* standard\tu\n')
            mf.write('* quality\tg\n')
            mf.write('* method_codes\t'+ Header["methodcode"]+'\n')
            mf.write('* citations\t'+ Header["citation"]+'\n')
            mf.write('* derived_value\t'+ 'XPEEM,*,10.1088/1742-6596/430/1/012127\n')
            mf.write('measurement\tderived_value\tmeas_pos_x\tmeas_pos_y\n')
            xf=open(output_dir_path+'/'+file,'r')
            line = xf.readline()
            if ',' in line:
                split_char=','
            elif '\t' in line:
                split_char='\t'
            elif '  ' in line:
                split_char='  '
            else:
                print('The separator between values is not a comma, tab, or two spaces. Exiting.')
                exit()
            y=0
            while line != "":
                line=line[:-1]  #remove newline
                values=line.split(split_char)
                x=0
                for value in values:
                    mline=str(meas_num)+'\t'+value+'\t'+str.format("{0:.7e}",x*x_spacing)+'\t'+str.format("{0:.7e}",y*y_spacing)+'\n'
                    mf.write(mline)
                    x+=1
                    meas_num+=1
                y+=1
                line = xf.readline()
            exp_num+=1
            xf.close()
            mf.close()

    return True
