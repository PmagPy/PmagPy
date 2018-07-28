#!/usr/bin/env/pythonw

import sys
import os
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb
from functools import reduce
import pytz
import datetime
import copy
import scipy
import numpy as np
import pandas as pd


# _2g_bin_magic conversion

def _2g_bin(dir_path=".", mag_file="", meas_file='measurements.txt',
            spec_file="specimens.txt", samp_file="samples.txt", site_file="sites.txt",
            loc_file="locations.txt", or_con='3', specnum=0, samp_con='2', corr='1',
            gmeths="FS-FD:SO-POM", location="unknown", inst="", user="", noave=0, input_dir="",
            lat="", lon=""):

    def skip(N, ind, L):
        for b in range(N):
            ind += 1
            while L[ind] == "":
                ind += 1
        ind += 1
        while L[ind] == "":
            ind += 1
        return ind

    #
    # initialize variables
    #
    bed_dip, bed_dip_dir = "", ""
    sclass, lithology, _type = "", "", ""
    DecCorr = 0.
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # format and fix variables
    if specnum != 0:
        specnum = -specnum
    if input_dir:
        input_dir_path = input_dir
    else:
        input_dir_path = dir_path

    if samp_con:
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
            # Z=1
            # try:
            #    SampRecs,file_type=pmag.magic_read(os.path.join(input_dir_path, 'er_samples.txt'))
            # except:
            #    print("there is no er_samples.txt file in your input directory - you can't use naming convention #6")
            #    return False, "there is no er_samples.txt file in your input directory - you can't use naming convention #6"
            # if file_type == 'bad_file':
            #    print("there is no er_samples.txt file in your input directory - you can't use naming convention #6")
            #    return False, "there is no er_samples.txt file in your input directory - you can't use naming convention #6"
        # else: Z=1

    if not mag_file:
        print("mag file is required input")
        return False, "mag file is required input"
    output_dir_path = dir_path
    mag_file = os.path.join(input_dir_path, mag_file)

    samplist = []
    try:
        SampRecs, file_type = pmag.magic_read(samp_file)
    except:
        SampRecs = []
    MeasRecs, SpecRecs, SiteRecs, LocRecs = [], [], [], []
    try:
        f = open(mag_file, 'br')
        input = str(f.read()).strip("b '")
        f.close()
    except Exception as ex:
        print('ex', ex)
        print("bad mag file")
        return False, "bad mag file"
    firstline, date = 1, ""
    d = input.split('\\xcd')
    for line in d:
        rec = line.split('\\x00')
        if firstline == 1:
            firstline = 0
            spec, vol = "", 1
            el = 51
            while line[el:el+1] != "\\":
                spec = spec+line[el]
                el += 1
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
            specname = spec.lower()
            print('importing ', specname)
            el += 8
            while rec[el].isdigit() == False:
                comments.append(rec[el])
                el += 1
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
            if rec[el] != "" and rec[el] != '\\x02' and rec[el] != '\\x01':
                deccorr = float(rec[el])
                az += deccorr
                bed_dip_dir += deccorr
                fold_az += deccorr
                if bed_dip_dir >= 360:
                    bed_dip_dir = bed_dip_dir-360.
                if az >= 360.:
                    az = az-360.
                if fold_az >= 360.:
                    fold_az = fold_az-360.
            else:
                deccorr = 0
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
                SampRecs.append(SampRec)

            if site != "" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
                SiteRec['site'] = site
                SiteRec['location'] = location
                SiteRec['lat'] = lat
                SiteRec['lon'] = lon
                SiteRec["geologic_classes"] = sclass
                SiteRec["lithologies"] = lithology
                SiteRec["geologic_types"] = _type
                SiteRecs.append(SiteRec)

            if location != "" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
                LocRec['location'] = location
                LocRec['lat_n'] = lat
                LocRec['lon_e'] = lon
                LocRec['lat_s'] = lat
                LocRec['lon_w'] = lon
                # LocRec["geologic_classes"]=sclass
                # LocRec["lithologies"]=lithology
                # LocRec["geologic_types"]=_type
                LocRecs.append(LocRec)

        else:
            MeasRec = {}
            MeasRec["treat_temp"] = '%8.3e' % (273)  # room temp in kelvin
            MeasRec["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
            MeasRec["treat_ac_field"] = '0'
            MeasRec["treat_dc_field"] = '0'
            MeasRec["treat_dc_field_phi"] = '0'
            MeasRec["treat_dc_field_theta"] = '0'
            meas_type = "LT-NO"
            MeasRec["quality"] = 'g'
            MeasRec["standard"] = 'u'
            MeasRec["treat_step_num"] = '1'
            MeasRec["specimen"] = specname
            el, demag = 1, ''
            treat = rec[el]
            if treat[-1] == 'C':
                demag = 'T'
            elif treat != 'NRM':
                demag = 'AF'
            el += 1
            while rec[el] == "":
                el += 1
            MeasRec["dir_dec"] = rec[el]
            cdec = float(rec[el])
            el += 1
            while rec[el] == "":
                el += 1
            MeasRec["dir_inc"] = rec[el]
            cinc = float(rec[el])
            el += 1
            while rec[el] == "":
                el += 1
            gdec = rec[el]
            el += 1
            while rec[el] == "":
                el += 1
            ginc = rec[el]
            el = skip(2, el, rec)  # skip bdec,binc
#                el=skip(4,el,rec) # skip gdec,ginc,bdec,binc
#                print 'moment emu: ',rec[el]
            MeasRec["magn_moment"] = '%10.3e' % (
                float(rec[el])*1e-3)  # moment in Am^2 (from emu)
            MeasRec["magn_volume"] = '%10.3e' % (
                float(rec[el])*1e-3/vol)  # magnetization in A/m
            el = skip(2, el, rec)  # skip to xsig
            MeasRec["magn_x_sigma"] = '%10.3e' % (
                float(rec[el])*1e-3)  # convert from emu
            el = skip(3, el, rec)  # skip to ysig
            MeasRec["magn_y_sigma"] = '%10.3e' % (
                float(rec[el])*1e-3)  # convert from emu
            el = skip(3, el, rec)  # skip to zsig
            MeasRec["magn_z_sigma"] = '%10.3e' % (
                float(rec[el])*1e-3)  # convert from emu
            el += 1  # skip to positions
            MeasRec["meas_n_orient"] = rec[el]
#                    el=skip(5,el,rec) # skip to date
#                    mm=str(months.index(date[0]))
#                    if len(mm)==1:
#                        mm='0'+str(mm)
#                    else:
#                        mm=str(mm)
#                    dstring=date[2]+':'+mm+':'+date[1]+":"+date[3]
#                    MeasRec['measurement_date']=dstring
            MeasRec["instrument_codes"] = inst
            MeasRec["analysts"] = user
            MeasRec["citations"] = "This study"
            MeasRec["method_codes"] = meas_type
            if demag == "AF":
                MeasRec["treat_ac_field"] = '%8.3e' % (
                    float(treat[:-2])*1e-3)  # peak field in tesla
                meas_type = "LT-AF-Z"
                MeasRec["treat_dc_field"] = '0'
            elif demag == "T":
                MeasRec["treat_temp"] = '%8.3e' % (
                    float(treat[:-1])+273.)  # temp in kelvin
                meas_type = "LT-T-Z"
            MeasRec['method_codes'] = meas_type
            MeasRecs.append(MeasRec)

    con = nb.Contribution(output_dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.write_table_to_file('specimens', custom_name=spec_file)
    con.write_table_to_file('samples', custom_name=samp_file)
    con.write_table_to_file('sites', custom_name=site_file)
    con.write_table_to_file('locations', custom_name=loc_file)
    con.write_table_to_file('measurements', custom_name=meas_file)
    return True, meas_file

# AGM magic conversion


def agm(agm_file, output_dir_path=".", input_dir_path="",
        meas_outfile="", spec_outfile="", samp_outfile="",
        site_outfile="", loc_outfile="", spec_infile="",
        samp_infile="", site_infile="",
        specimen="", specnum=0, samp_con="1", location="unknown",
        instrument="", institution="", bak=False, syn=False, syntype="",
        units="cgs", fmt='new'):
    """
    Parameters
    ----------
    Fmt: str, options ('new', 'old', 'xy', default 'new')
    """
    # initialize some stuff
    citations = 'This study'
    meth = "LP-HYS"
    version_num = pmag.get_version()
    Samps, Sites = [], []
    #noave = 1

    # get args
    if not input_dir_path:
        input_dir_path = output_dir_path
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
        MeasRec['institution'] = institution
        MeasRec['method_codes'] = meth
        MeasRec['experiment'] = specimen + ':' + meth
        if fmt == 'xy':
            rec = list(line.strip('\n').split())
        else:
            rec = list(line.strip('\n').strip('\r').split(','))
        #print (rec)
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
    con = nb.Contribution(output_dir_path, read_tables=[])

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
        meth_code="LP-NO", volume=0, user="", timezone='US/Pacific', noave=False):
    version_num = pmag.get_version()
    output_dir_path = dir_path
    if not input_dir_path:
        input_dir_path = output_dir_path
    samp_con = str(samp_con)
    specnum = - int(specnum)
    if not volume:
        volume = 0.025**3  # default volume is a 2.5 cm cube, translated to meters cubed
    else:
        volume *= 1e-6  # convert cm^3 to m^3

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
                "unrecogized date formating on one of the measurement entries for specimen %s" % specimen)
            datelist = ['', '', '']
        if ':' in row['Time']:
            timelist = row['Time'].split(':')
        else:
            print(
                "unrecogized time formating on one of the measurement entries for specimen %s" % specimen)
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

    con = nb.Contribution(output_dir_path, read_tables=[])

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
        sitename="", methods=['SO-MAG'], specnum=0, samp_con='3',
        norm='cc', oersted=False, noave=False, meas_n_orient='8',
        labfield=0, phi=0, theta=0):
    """
    Converts CIT formated Magnetometer data into MagIC format for Analysis and contribution to the MagIC database

    Parameters
    -----------
    dir_path : directory to output files to (default : current directory)
    user : colon delimited list of analysts (default : "")
    magfile : magnetometer file (.sam) to convert to MagIC (required)
    meas_file : measurement file name to output (default : measurements.txt)
    spec_file : specimen file name to output (default : specimens.txt)
    samp_file : sample file name to output (default : samples.txt)
    site_file : site file name to output (default : site.txt)
    loc_file : location file name to output (default : locations.txt)
    locname : location name
    methods : colon delimited list of sample method codes. full list here (https://www2.earthref.org/MagIC/method-codes) (default : SO-MAG
    specnum : number of terminal characters that identify a specimen
    norm : is volume or mass normalization using cgs or si units (options : cc,m3,g,kg) (default : cc)
    oersted : demag step vales are in Oersted
    noave : average measurement data or not. False is average, True is don't average. (default : False)
    samp_con : sample naming convention options as follows:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in sitename column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
    input_dir_path : if you did not supply a full path with magfile you can put the directory the magfile is in here
    meas_n_orient : Number of different orientations in measurement (default : 8)
    labfield : DC_FIELD in microTesla (default : 0)
    phi : DC_PHI in degrees (default : 0)
    theta : DC_THETA in degrees (default : 0)

    Returns
    -----------
    type - Tuple : (True or False indicating if conversion was sucessful, meas_file name written)
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

    if not input_dir_path:
        try:
            input_dir_path = os.path.split(magfile)[0]
        except IndexError:
            input_dir_path = dir_path

    output_dir_path = dir_path
    try:
        DC_FIELD = float(labfield) * 1e-6
        DC_PHI = float(phi)
        DC_THETA = float(theta)
    except ValueError:
        raise ValueError(
            'problem with your dc parameters. please provide a labfield in microTesla and a phi and theta in degrees.')
    yn = ''
    if DC_FIELD == 0 and DC_PHI == 0 and DC_THETA == 0:
        print('-I- Required values for labfield, phi, and theta not provided!  Will try to get these interactively')
        GET_DC_PARAMS = True
    else:
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
    if input_dir_path == '':
        input_dir_path = '.'
    magfile = os.path.join(input_dir_path, magfile)
    FIRST_GET_DC = True
    try:
        file_input = open(magfile, 'r')
    except IOError as ex:
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
        if specnum != 0:
            sample = specimen[:specnum]
        else:
            sample = specimen
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

    con = nb.Contribution(output_dir_path, read_tables=[])

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
            location="unknown", lat="", lon="", noave=False):

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
        avarage replicate measurements.
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
    labfield = float(labfield)
    labfield_phi = float(labfield_phi)
    labfield_theta = float(labfield_theta)

    if magfile:
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

    if experiment == 'ATRM':
        if command_line:
            ind = sys.argv.index("ATRM")
            atrm_n_pos = int(sys.argv[ind+1])
        else:
            atrm_n_pos = 6

    if experiment == 'AARM':
        if command_line:
            ind = sys.argv.index("AARM")
            aarm_n_pos = int(sys.argv[ind+1])
        else:
            aarm_n_pos = 6

    if experiment == 'CR':
        if command_line:
            ind = sys.argv.index("CR")
            cooling_times = sys.argv[ind+1]
            cooling_times_list = cooling_times.split(',')
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
                    "Dont support yet NLT rate experiment file. Contact rshaar@ucsd.edu")

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

    con = nb.Contribution(dir_path, read_tables=[])

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


### HUJI_magic conversion

def huji(magfile="", dir_path=".", input_dir_path="", datafile="", codelist="",
         meas_file="measurements.txt", spec_file="specimens.txt",
         samp_file="samples.txt", site_file="sites.txt", loc_file="locations.txt",
         user="", specnum=0, samp_con="1", labfield=0, phi=0, theta=0, peakfield=0,
         location="", CR_cooling_times=None, noave=False):

    # format and validate variables
    specnum = int(specnum)
    labfield = float(labfield) * 1e-6
    phi = int(theta)
    theta = int(theta)
    peakfield = float(peakfield)*1e-3
    if not input_dir_path:
        input_dir_path = dir_path

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

    con = nb.Contribution(dir_path, read_tables=[])

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


### HUJI_sample_magic conversion

def huji_sample(orient_file, meths='FS-FD:SO-POM:SO-SUN', location_name='unknown',
                samp_con="1", Z=1, ignore_dip=True, data_model_num=3,
                samp_file="samples.txt", site_file="sites.txt",
                dir_path=".", input_dir_path=""):
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


    if not input_dir_path:
        input_dir_path = dir_path
    samp_file = pmag.resolve_file_name(samp_file, dir_path)
    site_file = pmag.resolve_file_name(site_file, dir_path)
    print('dir path', dir_path)
    print(input_dir_path)
    print(orient_file)
    orient_file = pmag.resolve_file_name(orient_file, input_dir_path)
    print(orient_file)
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

def iodp_dscr(csv_file="", dir_path=".", input_dir_path="",
              meas_file="measurements.txt", spec_file="specimens.txt",
              samp_file="samples.txt", site_file="sites.txt", loc_file="locations.txt",
              lat='', lon='', volume=2.5**3, noave=False):
    # initialize defaults
    version_num = pmag.get_version()
    # format variables
    if not input_dir_path:
        input_dir_path = dir_path
    output_dir_path = dir_path  # rename dir_path after input_dir_path is set
    # default volume is a 2.5cm cube
    volume = volume * 1e-6
    if csv_file == "":
        # read in list of files to import
        filelist = os.listdir(input_dir_path)
    else:
        csv_file = os.path.join(input_dir_path, csv_file)
        filelist = [csv_file]

    # parsing the data
    file_found, citations = False, "This Study"
    MeasRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    for fin in filelist:  # parse each file
        if fin[-3:].lower() == 'csv':
            file_found = True
            print('processing: ', fin)
            infile = open(fin, 'r')
            indata = infile.readlines()
            infile.close()
            keys = indata[0].replace('\n', '').split(
                ',')  # splits on underscores
            keys = [k.strip('"') for k in keys]
            interval_key = "Offset (cm)"
            if "Treatment Value (mT or \xc2\xb0C)" in keys:
                demag_key = "Treatment Value (mT or \xc2\xb0C)"
            elif "Treatment Value" in keys:
                demag_key = "Treatment Value"
            elif "Treatment Value (mT or &deg;C)" in keys:
                demag_key = "Treatment Value (mT or &deg;C)"
            elif "Demag level (mT)" in keys:
                demag_key = "Demag level (mT)"
            else:
                print("couldn't find demag level")
            if "Treatment type" in keys:
                treatment_type = "Treatment type"
            elif "Treatment Type" in keys:
                treatment_type = "Treatment Type"
            else:
                treatment_type = ""
            run_key = "Test No."
            if "Inclination background + tray corrected  (deg)" in keys:
                inc_key = "Inclination background + tray corrected  (deg)"
            elif "Inclination background &amp; tray corrected (deg)" in keys:
                inc_key = "Inclination background &amp; tray corrected (deg)"
            elif "Inclination background & tray corrected (deg)" in keys:
                inc_key = "Inclination background & tray corrected (deg)"
            elif "Inclination background & drift corrected (deg)" in keys:
                inc_key = "Inclination background & drift corrected (deg)"
            else:
                print("couldn't find inclination")
            if "Declination background + tray corrected (deg)" in keys:
                dec_key = "Declination background + tray corrected (deg)"
            elif "Declination background &amp; tray corrected (deg)" in keys:
                dec_key = "Declination background &amp; tray corrected (deg)"
            elif "Declination background & tray corrected (deg)" in keys:
                dec_key = "Declination background & tray corrected (deg)"
            elif "Declination background & drift corrected (deg)" in keys:
                dec_key = "Declination background & drift corrected (deg)"
            else:
                print("couldn't find declination")
            if "Intensity background + tray corrected  (A/m)" in keys:
                int_key = "Intensity background + tray corrected  (A/m)"
            elif "Intensity background &amp; tray corrected (A/m)" in keys:
                int_key = "Intensity background &amp; tray corrected (A/m)"
            elif "Intensity background & tray corrected (A/m)" in keys:
                int_key = "Intensity background & tray corrected (A/m)"
            elif "Intensity background & drift corrected (A/m)" in keys:
                int_key = "Intensity background & drift corrected (A/m)"
            else:
                print("couldn't find magnetic moment")
            type_val = "Type"
            sect_key = "Sect"
            half_key = "A/W"
# need to add volume_key to LORE format!
            if "Sample volume (cm^3)" in keys:
                volume_key = "Sample volume (cm^3)"
            elif "Sample volume (cc)" in keys:
                volume_key = "Sample volume (cc)"
            elif "Sample volume (cm&sup3;)" in keys:
                volume_key = "Sample volume (cm&sup3;)"
            elif "Sample volume (cm\xc2\xb3)" in keys:
                volume_key = "Sample volume (cm\xc2\xb3)"
            elif "Sample volume (cm{})".format(chr(0x00B2)) in keys:
                volume_key = "Sample volume (cm{})".format(chr(0x00B2))
            elif "Sample volume (cm\xb3)" in keys:
                volume_key = "Sample volume (cm\xb3)"
            else:
                volume_key = ""
            for line in indata[1:]:
                InRec = {}
                MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}
                for k in range(len(keys)):
                    InRec[keys[k]] = line.split(',')[k].strip('"')
                inst = "IODP-SRM"
                expedition = InRec['Exp']
                location = InRec['Site']+InRec['Hole']
                # maintain consistency with er_samples convention of using top interval
                offsets = InRec[interval_key].split('.')
                if len(offsets) == 1:
                    offset = int(offsets[0])
                else:
                    offset = int(offsets[0])-1
                # interval=str(offset+1)# maintain consistency with er_samples convention of using top interval
                # maintain consistency with er_samples convention of using top interval
                interval = str(offset)
                specimen = expedition+'-'+location+'-' + \
                    InRec['Core']+InRec[type_val]+"-"+InRec[sect_key] + \
                    '-'+InRec[half_key]+'-'+str(InRec[interval_key])
                sample = expedition+'-'+location + \
                    '-'+InRec['Core']+InRec[type_val]
                site = expedition+'-'+location
                if volume_key in list(InRec.keys()):
                    volume = InRec[volume_key]

                if not InRec[dec_key].strip(""" " ' """) or not InRec[inc_key].strip(""" " ' """):
                    print("No dec or inc found for specimen %s, skipping" % specimen)

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
                    SampRec['azimuth'] = '0'
                    SampRec['dip'] = '0'
                    SampRec['method_codes'] = 'FS-C-DRILL-IODP:SO-V'
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
# set up measurement record - default is NRM
                MeasRec['software_packages'] = version_num
                MeasRec["treat_temp"] = '%8.3e' % (273)  # room temp in kelvin
                MeasRec["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
                MeasRec["treat_ac_field"] = '0'
                MeasRec["treat_dc_field"] = '0'
                MeasRec["treat_dc_field_phi"] = '0'
                MeasRec["treat_dc_field_theta"] = '0'
                MeasRec["quality"] = 'g'  # assume all data are "good"
                MeasRec["standard"] = 'u'  # assume all data are "good"
                MeasRec["dir_csd"] = '0'  # assume all data are "good"
                MeasRec["method_codes"] = 'LT-NO'
                sort_by = 'treat_ac_field'  # set default to AF demag
                if treatment_type in list(InRec.keys()) and InRec[treatment_type] != "":
                    if "AF" in InRec[treatment_type].upper():
                        MeasRec['method_codes'] = 'LT-AF-Z'
                        inst = inst+':IODP-SRM-AF'  # measured on shipboard in-line 2G AF
                        treatment_value = float(
                            InRec[demag_key].strip('"'))*1e-3  # convert mT => T
                        MeasRec["treat_ac_field"] = str(
                            treatment_value)  # AF demag in treat mT => T
                    elif "T" in InRec[treatment_type].upper():
                        MeasRec['method_codes'] = 'LT-T-Z'
                        inst = inst+':IODP-TDS'  # measured on shipboard Schonstedt thermal demagnetizer
                        treatment_value = float(
                            InRec[demag_key].strip('"'))+273  # convert C => K
                        MeasRec["treat_temp"] = str(treatment_value)
                    elif "Lowrie" in InRec['Comments']:
                        MeasRec['method_codes'] = 'LP-IRM-3D'
                        treatment_value = float(
                            InRec[demag_key].strip('"'))+273.  # convert C => K
                        MeasRec["treat_temp"] = str(treatment_value)
                        MeasRec["treat_ac_field"] = "0"
                        sort_by = 'treat_temp'
                    elif 'Isothermal' in InRec[treatment_type]:
                        MeasRec['method_codes'] = 'LT-IRM'
                        treatment_value = float(
                            InRec[demag_key].strip('"'))*1e-3  # convert mT => T
                        MeasRec["treat_dc_field"] = str(treatment_value)
                        MeasRec["treat_ac_field"] = "0"
                        sort_by = 'treat_dc_field'
                # Assume AF if there is no Treatment typ info
                elif InRec[demag_key] != "0" and InRec[demag_key] != "":
                    MeasRec['method_codes'] = 'LT-AF-Z'
                    inst = inst+':IODP-SRM-AF'  # measured on shipboard in-line 2G AF
                    treatment_value = float(
                        InRec[demag_key].strip('"'))*1e-3  # convert mT => T
                    # AF demag in treat mT => T
                    MeasRec["treat_ac_field"] = treatment_value
                MeasRec["standard"] = 'u'  # assume all data are "good"
                try:
                    vol = float(volume)
                except ValueError:
                    print('-W- No volume information provided, guessing 2.5cm cube')
                    vol = (2.5**3)*1e-6  # default volume is a 2.5cm cube
                if run_key in list(InRec.keys()):
                    run_number = InRec[run_key]
                    MeasRec['external_database_ids'] = {'LIMS': run_number}
                else:
                    MeasRec['external_database_ids'] = ""
                MeasRec['description'] = 'sample orientation: ' + \
                    InRec['Sample orientation']
                MeasRec['dir_inc'] = InRec[inc_key].strip('"')
                MeasRec['dir_dec'] = InRec[dec_key].strip('"')
                intens = InRec[int_key].strip('"')
                # convert intensity from A/m to Am^2 using vol
                MeasRec['magn_moment'] = '%8.3e' % (float(intens)*vol)
                MeasRec['instrument_codes'] = inst
                MeasRec['treat_step_num'] = '1'
                MeasRec['meas_n_orient'] = ''
                MeasRecs.append(MeasRec)
    if not file_found:
        print("No .csv files were found")
        return False, "No .csv files were found"

    con = nb.Contribution(output_dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasSort = sorted(MeasRecs, key=lambda x: (
        x['specimen'], float(x[sort_by])))
    MeasFixed = pmag.measurements_methods3(MeasSort, noave)
    MeasOuts, keys = pmag.fillkeys(MeasFixed)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.tables['specimens'].write_magic_file(custom_name=spec_file)
    con.tables['samples'].write_magic_file(custom_name=samp_file)
    con.tables['sites'].write_magic_file(custom_name=site_file)
    con.tables['locations'].write_magic_file(custom_name=loc_file)
    con.tables['measurements'].write_magic_file(custom_name=meas_file)

    return True, meas_file

### IODP_jr6_magic

def iodp_jr6(mag_file, dir_path=".", input_dir_path="",
             meas_file="measurements.txt", spec_file="specimens.txt",
             samp_file="samples.txt", site_file="sites.txt", loc_file="locations.txt",
             site="unknown", expedition="unknown", lat="", lon="",
             noave=False, volume=2.5**2, meth_code="LP-NO"):

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

    if not input_dir_path:
        input_dir_path = dir_path
    output_dir_path = dir_path
    # default volume is a 2.5cm cube
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
    citations = "This Study"
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
            treat = float(row['step'][3:])
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

    con = nb.Contribution(output_dir_path, read_tables=[])

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

    return (True, meas_file)



### IODP_srm_magic conversion

def iodp_srm(csv_file="", dir_path=".", input_dir_path="",
             meas_file="measurements.txt", spec_file="specimens.txt",
             samp_file="samples.txt", site_file="sites.txt", loc_file="locations.txt",
             lat="", lon="", noave=0):

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

    if not input_dir_path:
        input_dir_path = dir_path
    output_dir_path = dir_path

    # format variables
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
                MeasRec['treat_step_num'] = '1'
                MeasRec['dir_csd'] = '0'
                MeasRec['meas_n_orient'] = ''
                MeasRecs.append(MeasRec)
    if not file_found:
        print("No .csv files were found")
        return (False, "No .csv files were found")

    con = nb.Contribution(output_dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    #MeasSort=sorted(MeasRecs,key=lambda x: (x['specimen'], float(x['treat_ac_field'])))
    #MeasSort=sorted(MeasRecs,key=lambda x: float(x['treat_ac_field']))
    # MeasOuts=pmag.measurements_methods3(MeasSort,noave)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.write_table_to_file('specimens', custom_name=spec_file)
    con.write_table_to_file('samples', custom_name=samp_file)
    con.write_table_to_file('sites', custom_name=site_file)
    con.write_table_to_file('locations', custom_name=loc_file)
    con.write_table_to_file('measurements', custom_name=meas_file)

    return (True, meas_file)


### JR6_jr6_magic conversion

def jr6_jr6(mag_file, dir_path=".", input_dir_path="",
            meas_file="measurements.txt", spec_file="specimens.txt",
            samp_file="samples.txt", site_file="sites.txt", loc_file="locations.txt",
            specnum=1, samp_con='1', location='unknown', lat='', lon='',
            noave=False, meth_code="LP-NO", volume=2.5, JR=False, user=""):

    version_num = pmag.get_version()
    if not input_dir_path:
        input_dir_path = output_dir_path
    output_dir_path = dir_path
    specnum = - int(specnum)
    samp_con = str(samp_con)
    volume = float(volume) * 1e-6

    if JR:
        if meth_code == "LP-NO":
            meth_code = ""
        meth_code = meth_code+":FS-C-DRILL-IODP:SP-SS-C:SO-V"
        meth_code = meth_code.strip(":")
        samp_con = '5'

    # format variables
    tmp_file = mag_file.split(os.extsep)[0]+os.extsep+'tmp'
    mag_file = os.path.join(input_dir_path, mag_file)
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
    data['dip'] = -data['dip']

    data['specimen']
    # put data into magic tables
    MagRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    for rowNum, row in data.iterrows():
        MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}
        specimen = row['specimen']
        if specnum != 0:
            sample = specimen[:specnum]
        else:
            sample = specimen
        site = pmag.parse_site(sample, samp_con, Z)
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
        MeasRec["treat_step_num"] = '1'
        MeasRec["treat_ac_field"] = '0'
        if row['step'] == 'NRM':
            meas_type = "LT-NO"
        elif 'step_unit' in row and row['step_unit'] == 'C':
            meas_type = "LT-T-Z"
            treat = float(row['step'])
            MeasRec["treat_temp"] = '%8.3e' % (treat+273.)  # temp in kelvin
        elif row['step'][0:2] == 'AD':
            meas_type = "LT-AF-Z"
            treat = float(row['step'][2:])
            MeasRec["treat_ac_field"] = '%8.3e' % (
                treat*1e-3)  # convert from mT to tesla
        elif row['step'][0] == 'A':
            meas_type = "LT-AF-Z"
            treat = float(row['step'][1:])
            MeasRec["treat_ac_field"] = '%8.3e' % (
                treat*1e-3)  # convert from mT to tesla
        elif row['step'][0] == 'TD':
            meas_type = "LT-T-Z"
            treat = float(row['step'][2:])
            MeasRec["treat_temp"] = '%8.3e' % (treat+273.)  # temp in kelvin
        elif row['step'][0] == 'T':
            meas_type = "LT-T-Z"
            treat = float(row['step'][1:])
            MeasRec["treat_temp"] = '%8.3e' % (treat+273.)  # temp in kelvin
        else:  # need to add IRM, and ARM options
            print("measurement type unknown", row['step'])
            return False, "measurement type unknown"
        MeasRec["magn_moment"] = str(row['magn_moment'])
        MeasRec["magn_volume"] = str(row['magn_volume'])
        MeasRec["dir_dec"] = str(row['dir_dec'])
        MeasRec["dir_inc"] = str(row['dir_inc'])
        MeasRec['method_codes'] = meas_type
        MagRecs.append(MeasRec)

    con = nb.Contribution(output_dir_path, read_tables=[])

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
            noave=False, volume=2.5, timezone="UTC", meth_code="LP-NO"):

    version_num = pmag.get_version()
    if not input_dir_path:
        mag_file = pmag.resolve_file_name(mag_file, dir_path)
        input_dir_path = os.path.split(mag_file)[0]
    output_dir_path = dir_path
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
        MeasRec["treat_step_num"] = '1'
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

        # ignore all the rest of the special characters. Some data files not consistantly formatted.
        n += 1
        while ((len(data[n]) <= 5 and data[n] != '') or data[n].startswith('----')):
            n += 1
            if n >= len(data):
                break
        if n >= len(data):
            # we're done!
            end = True

        # end of data while loop

    con = nb.Contribution(output_dir_path, read_tables=[])

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


def k15(k15file, specnum=0, sample_naming_con='1', location="unknown",
        measfile='measurements.txt', sampfile="samples.txt",
        aniso_outfile='specimens.txt', result_file="rmag_results.txt",
        input_dir_path='', output_dir_path='.', data_model_num=3):
    """

    NAME
        k15_magic.py

    DESCRIPTION
        converts .k15 format data to magic_measurements  format.
        assums Jelinek Kappabridge measurement scheme

    SYNTAX
        k15_magic.py [-h] [command line options]

    OPTIONS
        -h prints help message and quits
        -f KFILE: specify .k15 format input file
        -F MFILE: specify magic_measurements format output file
        -Fsa SFILE, specify er_samples format file for output
        -Fa AFILE, specify anisotropy file for output # default rmag_anisotropy for data model 2, specimens file for data model 3
        -Fr RFILE, specify rmag_results format file for output # data model 2 only
        -loc LOC: specify location name for study
    #-ins INST: specify instrument that measurements were made on # not implemented
        -spc NUM: specify number of digits for specimen ID, default is 0
        -ncn NCOM: specify naming convention (default is #1)
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXXYYY:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.


    DEFAULTS
        MFILE: k15_measurements.txt
        SFILE: er_samples.txt
        AFILE: rmag_anisotropy.txt
        RFILE: rmag_results.txt
        LOC: unknown
        INST: unknown

    INPUT
      name [az,pl,strike,dip], followed by
      3 rows of 5 measurements for each specimen

    """
    #
    # initialize some variables
    #
    if not input_dir_path:
        input_dir_path = output_dir_path
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
        if measfile == 'measurements.txt':
            measfile = 'magic_measurements.txt'
        if sampfile == 'samples.txt':
            sampfile = 'er_samples.txt'
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
    sampfile = os.path.join(output_dir_path, sampfile)
    measfile = os.path.join(output_dir_path, measfile)
    aniso_outfile = os.path.join(output_dir_path, aniso_outfile)
    result_file = os.path.join(output_dir_path, result_file)
    k15file = os.path.join(input_dir_path, k15file)
    if not os.path.exists(k15file):
        print(k15file)
        return False, "You must provide a valid k15 format file"
    try:
        SampRecs, filetype = pmag.magic_read(
            sampfile)  # append new records to existing
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
    pmag.magic_write(sampfile, SampRecs, samp_table_name)
    # specimens / rmag_anisotropy / rmag_results
    if data_model_num == 3:
        AnisRecs.extend(ResRecs)
        SpecRecs = AnisRecs.copy()
        SpecRecs, keys = pmag.fillkeys(SpecRecs)
        pmag.magic_write(aniso_outfile, SpecRecs, 'specimens')
        flist = [measfile, aniso_outfile, sampfile]
    else:
        pmag.magic_write(aniso_outfile, AnisRecs, 'rmag_anisotropy')  # add to specimens?
        pmag.magic_write(result_file, ResRecs, 'rmag_results') # added to specimens (NOT sites)
        flist = [measfile, sampfile, aniso_outfile, result_file]
    # measurements
    pmag.magic_write(measfile, MeasRecs, meas_table_name)

    print("Data saved to: " + ", ".join(flist))
    return True, measfile




### LDEO_magic conversion

def ldeo(magfile, output_dir_path=".", input_dir_path="",
         meas_file="measurements.txt", spec_file="specimens.txt",
         samp_file="samples.txt", site_file="sites.txt", loc_file="locations.txt",
         specnum=0, samp_con="1", location="unknown", codelist="",
         coil="", arm_labfield=50e-6, trm_peakT=873., peakfield=0,
         labfield=0, phi=0, theta=0, mass_or_vol="v", noave=0):
    # initialize some stuff
    dec = [315, 225, 180, 135, 45, 90, 270, 270, 270, 90, 180, 180, 0, 0, 0]
    inc = [0, 0, 0, 0, 0, -45, -45, 0, 45, 45, 45, -45, -90, -45, 45]
    tdec = [0, 90, 0, 180, 270, 0, 0, 90, 0]
    tinc = [0, 0, 90, 0, 0, -90, 0, 0, 90]
    demag = "N"
    trm = 0
    irm = 0

    # format/organize variables
    if not input_dir_path:
        input_dir_path = output_dir_path
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
                susc_chi_volume = '%10.3e' % (
                    float(rec[11])*1e-5) / volume
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
                SpecRec["mass"] = mass
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
        MeasRec["treat_temp"] = '%8.3e' % (273)  # room temp in kelvin
        MeasRec["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
        MeasRec["treat_ac_field"] = '0'
        MeasRec["treat_dc_field"] = '0'
        MeasRec["treat_dc_field_phi"] = '0'
        MeasRec["treat_dc_field_theta"] = '0'
        meas_type = "LT-NO"
        MeasRec["quality"] = 'g'
        MeasRec["standard"] = 'u'
        MeasRec["treat_step_num"] = '1'
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

    con = nb.Contribution(output_dir_path, read_tables=[])

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


# MINI_magic conversion

def mini(magfile, dir_path='.', meas_file='measurements.txt',
         data_model_num=3, volume=10, noave=0,
         inst="", user="", demag='N', methcode="LP-NO"):
    # initialize
    citation = 'This study'
    MagRecs = []
    version_num = pmag.get_version()
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
        meas_name_col = "measurement"

    # go through the measurements
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
        con = nb.Contribution(dir_path, read_tables=['measurements'],
                              custom_filenames={'measurements': meas_file})
        con.propagate_measurement_info()
        for table in con.tables:
            con.write_table_to_file(table)
    print("results put in ", meas_file)
    return True, meas_file

### MsT_magic conversion

def mst(infile, spec_name, dir_path=".", input_dir_path="",
        meas_file="measurements.txt", samp_infile="samples.txt",
        user="", specnum=0, samp_con="1", labfield=0.5,
        location='', syn=False, data_model_num=3):

    # deal with input files
    if not input_dir_path:
        input_dir_path = dir_path

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
        meas_magnitude_col = "magn_moment" # but this may be wrong...
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
                            MagRec[loc_col] = samp[loc_col]
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
        if data_model_num == 3:
            rec[meas_name_col] = rec[experiment_col] + "_" + rec[meas_name_col]
        new_MagRecs.append(rec)

    pmag.magic_write(meas_file, new_MagRecs, meas_file_type)
    print("results put in ", meas_file)
    # try to extract location/site/sample/specimen info into tables
    con = nb.Contribution(dir_path)
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
        lat=0, lon=0, specnum=0, samp_con='1', location="unknown",
        noave=0, meth_code="LP-NO"):
    """

    """
    if not input_dir_path:
        input_dir_path = dir_path
    output_dir_path = dir_path
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
    SampRec['description'] = comment
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
            MeasRec["treat_step_num"] = '1'
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

    con = nb.Contribution(output_dir_path, read_tables=[])

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


### SIO_magic conversion

def sio(mag_file, dir_path=".", input_dir_path="",
        meas_file="measurements.txt", spec_file="specimens.txt",
        samp_file="samples.txt", site_file="sites.txt", loc_file="locations.txt",
        samp_infile="", institution="", syn=False, syntype="", instrument="",
        labfield=0, phi=0, theta=0, peakfield=0,
        specnum=0, samp_con='1', location="unknown", lat="", lon="",
        noave=False, codelist="", coil="", cooling_rates="", timezone="UTC",
        user=""):

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
    output_dir_path = dir_path
    if not input_dir_path:
        input_dir_path = dir_path
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
    specnum = -int(specnum)
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
            try:
                float(rec[0])
                print("No specimen name for line #%d in the measurement file" %
                      lines.index(line))
                continue
            except ValueError:
                pass
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
                    if code3[0] == "PM":
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
            MeasRec["treat_step_num"] = '1'
            # print MeasRec['treat_temp']
            MeasRecs.append(MeasRec)

    con = nb.Contribution(output_dir_path, read_tables=[])

    # create MagIC tables
    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)
    # write MagIC tables to file
    con.tables['specimens'].write_magic_file(custom_name=spec_file)
    con.tables['samples'].write_magic_file(custom_name=samp_file)
    con.tables['sites'].write_magic_file(custom_name=site_file)
    con.tables['locations'].write_magic_file(custom_name=loc_file)
    meas_file = con.tables['measurements'].write_magic_file(
        custom_name=meas_file)
    return True, meas_file


### s_magic conversion

def s_magic(sfile, anisfile="specimens.txt", dir_path=".", atype="AMS",
            coord_type="s", sigma=False, samp_con="1", Z=1, specnum=0,
            location="unknown", spec="unknown", sitename="unknown",
            user="", data_model_num=3, name_in_file=False):

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
    sfile = pmag.resolve_file_name(sfile, dir_path)
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
    con = nb.Contribution(dir_path, custom_filenames={"specimens": anisfile})
    con.propagate_all_tables_info()
    for table in con.tables:
        if table in ['samples', 'sites', 'locations']:
            # add in location name by hand
            if table == 'sites':
                con.tables['sites'].df['location'] = location
            con.write_table_to_file(table)
    return True, anisfile


### Utrecht conversion

def utrecht(mag_file, dir_path=".",  input_dir_path="", meas_file="measurements.txt",
            spec_file="specimens.txt", samp_file="samples.txt", site_file="sites.txt",
            loc_file="locations.txt", location="unknown", lat="", lon="", dmy_flag=False,
            noave=False, meas_n_orient='8', meth_code="LP-NO", specnum=1, samp_con='2',
            labfield=0, phi=0, theta=0):
    # initialize some stuff
    version_num = pmag.get_version()
    MeasRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    output_dir_path = dir_path
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
                print("date format seperator cannot be identified")
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

    con = nb.Contribution(output_dir_path, read_tables=[])

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
