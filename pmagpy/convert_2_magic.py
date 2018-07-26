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


# HUJI_magic conversion

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
