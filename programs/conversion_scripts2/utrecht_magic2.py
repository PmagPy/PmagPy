#!/usr/bin/env python
from __future__ import print_function
from builtins import str
from builtins import map
import pandas as pd
import sys
import os
import numpy as np
import pmagpy.pmag as pmag


def main(command_line=True, **kwargs):
    """
    NAME
        utrecht_magic.py

    DESCRIPTION
        converts Utrecht magnetometer data files to magic_measurements files

    SYNTAX
        utrecht_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -f FILE: specify  input file, or
        -F FILE: specify output file, default is magic_measurements.txt
        -Fsa: specify er_samples format file for appending, default is new er_samples.txt (Not working yet)
        -WD: output directory for MagIC files
        -ncn: Site Naming Convention
         Site to Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2: default] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name = sample name
            [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
        -spc: number of characters to remove to generate sample names from specimen names
        -dmy: European date format
        -loc LOCNAME : specify location/study name
        -lat latitude of samples
        -lon longitude of samples
        -A: don't average replicate measurements
        -mcd: [SO-MAG,SO-SUN,SO-SIGHT...] supply how these samples were oriented
        -dc: B PHI THETA: dc lab field (in microTesla), phi,and theta must be input as a tuple "(DC,PHI,THETA)". If not input user will be asked for values, this is advantagious if there are differing dc fields between steps or specimens. Note: this currently only works with the decimal IZZI naming convetion (XXX.0,1,2,3 where XXX is the treatment temperature and 0 is a zero field step, 1 is in field, and 2 is a pTRM check, 3 is a tail check). All other steps are hardcoded dc_field = 0.

    INPUT
        Utrecht magnetometer data file
    """
# initialize some stuff
    sample_lat = 0.0
    sample_lon = 0.0
    noave = 0
    er_location_name = "unknown"
    args = sys.argv
    meth_code = "LP-NO"
    version_num = pmag.get_version()
    site_num = 1

    mag_file = ""
    dir_path = '.'
    MagRecs = []
    SpecOuts = []
    SampOuts = []
    SiteOuts = []

    meas_file='magic_measurements.txt'
    spec_file='er_specimens.txt'
    samp_file='er_samples.txt'
    site_file='er_sites.txt'
    meth_code = ""
    #
    # get command line arguments
    #
    if command_line:
        if '-WD' in sys.argv:
            ind = sys.argv.index('-WD')
            dir_path = sys.argv[ind+1]
        if '-ID' in sys.argv:
            ind = sys.argv.index('-ID')
            input_dir_path = sys.argv[ind+1]
        else:
            input_dir_path = dir_path
        output_dir_path = dir_path
        if "-h" in args:
            print(main.__doc__)
            return False
        if '-F' in args:
            ind = args.index("-F")
            meas_file = args[ind+1]
        if '-Fsp' in args:
            ind=args.index("-Fsp")
            spec_file=args[ind+1]
        if '-Fsa' in args:
            ind = args.index("-Fsa")
            samp_file = args[ind+1]
        if '-Fsi' in args:   # LORI addition
            ind=args.index("-Fsi")
            site_file=args[ind+1]
            #try:
            #    open(samp_file,'r')
            #    ErSamps,file_type=pmag.magic_read(samp_file)
            #    print 'sample information will be appended to ', samp_file
            #except:
            #    print samp_file,' not found: sample information will be stored in new er_samples.txt file'
            #    samp_file = output_dir_path+'/er_samples.txt'
        if '-f' in args:
            ind = args.index("-f")
            mag_file = args[ind+1]
        if "-loc" in args:
            ind = args.index("-loc")
            er_location_name = args[ind+1]
        if "-lat" in args:
            ind = args.index("-lat")
            site_lat = args[ind+1]
        if "-lon" in args:
            ind = args.index("-lon")
            site_lon = args[ind+1]
        if "-A" in args:
            noave = 1
        if "-mcd" in args:
            ind = args.index("-mcd")
            meth_code = args[ind+1]
            #samp_con='5'
        if "-ncn" in args:
            ind=args.index("-ncn")
            samp_con=sys.argv[ind+1]
            if "4" in samp_con:
                if "-" not in samp_con:
                    print("option [4] must be in form 4-Z where Z is an integer")
                    return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
                else:
                    site_num=samp_con.split("-")[1]
                    samp_con="4"
            elif "7" in samp_con:
                if "-" not in samp_con:
                    print("option [7] must be in form 7-Z where Z is an integer")
                    return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
                else:
                    site_num=samp_con.split("-")[1]
                    samp_con="7"
        else: samp_con="1"
        if '-dc' in args:
            ind=args.index('-dc')
            DC_FIELD,DC_PHI,DC_THETA=list(map(float,args[ind+1].strip('( ) [ ]').split(',')))
            DC_FIELD *= 1e-6
            yn=''
            GET_DC_PARAMS=False
        else: DC_FIELD,DC_PHI,DC_THETA=0,0,-90
        if '-spc' in args:
            ind=args.index("-spc")
            specnum=-int(args[ind+1])
        else: specnum = 0
        if '-dmy' in args:
            ind=args.index("-dmy")
            dmy_flag=True
        else: dmy_flag=False


    if not command_line:
        dir_path = kwargs.get('dir_path', '.')
        input_dir_path = kwargs.get('input_dir_path', dir_path)
        output_dir_path = dir_path
        meas_file = kwargs.get('meas_file', 'magic_measurements.txt')
        mag_file = kwargs.get('mag_file')
        spec_file = kwargs.get('spec_file', 'er_specimens.txt') # specimen outfile
        samp_file = kwargs.get('samp_file', 'er_samples.txt')
        site_file = kwargs.get('site_file', 'er_sites.txt') # site outfile
        er_location_name = kwargs.get('location_name', '')
        site_lat = kwargs.get('site_lat', '')
        site_lon = kwargs.get('site_lon', '')
        #oave = kwargs.get('noave', 0) # default (0) means DO average
        meth_code = kwargs.get('meth_code', "LP-NO")
        specnum = -int(kwargs.get('specnum', 0))
        samp_con = kwargs.get('samp_con', '2')
        if "4" in samp_con:
            if "-" not in samp_con:
                print("option [4] must be in form 4-Z where Z is an integer")
                return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
            else:
                site_num=samp_con.split("-")[1]
                samp_con="4"
        elif "7" in samp_con:
            if "-" not in samp_con:
                print("option [7] must be in form 7-Z where Z is an integer")
                return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
            else:
                site_num=samp_con.split("-")[1]
                samp_con="7"
        DC_FIELD,DC_PHI,DC_THETA = list(map(float, kwargs.get('dc_params', (0,0,-90))))
        DC_FIELD *= 1e-6
        noave = kwargs.get('avg', True)
        dmy_flag = kwargs.get('dmy_flag', False)

    # format variables
    if not mag_file:
        return False, 'You must provide a Utrecht formated file'
    mag_file = os.path.join(input_dir_path, mag_file)
    meas_file = os.path.join(output_dir_path, meas_file)
    spec_file = os.path.join(output_dir_path, spec_file)
    samp_file = os.path.join(output_dir_path, samp_file)
    site_file = os.path.join(output_dir_path, site_file)

    # parse data

    # Open up the Utrecht file and read the header information
    print('mag_file in utrecht_file', mag_file)
    AF_or_T = mag_file.split('.')[-1]
    data = open(mag_file, 'r')
    line = data.readline()
    line_items = line.split(',')
    operator=line_items[0]
    operator=operator.replace("\"","")
    machine=line_items[1]
    machine=machine.replace("\"","")
    machine=machine.rstrip('\n')
    print("operator=", operator)
    print("machine=", machine)

    #read in measurement data
    line = data.readline()
    while line != "END" and line != '"END"':
        ErSpecRec,ErSampRec,ErSiteRec = {},{},{}
        line_items = line.split(',')
        spec_name=line_items[0]
        spec_name=spec_name.replace("\"","")
        print("spec_name=", spec_name)
        free_string=line_items[1]
        free_string=free_string.replace("\"","")
        print("free_string=", free_string)
        dec=line_items[2]
        print("dec=", dec)
        inc=line_items[3]
        print("inc=", inc)
        volume=float(line_items[4])
        volume=volume * 1e-6 # enter volume in cm^3, convert to m^3
        print("volume=", volume)
        bed_plane=line_items[5]
        print("bed_plane=", bed_plane)
        bed_tilt=line_items[6]
        print("bed_tilt=", bed_tilt)

        # Configure et er_ tables
        ErSpecRec['er_specimen_name'] = spec_name
        if specnum==0: sample_name = spec_name
        else: sample_name = spec_name[:specnum]
        ErSampRec['er_sample_name'] = sample_name
        ErSpecRec['er_sample_name'] = sample_name
        er_site_name = pmag.parse_site(sample_name,samp_con,site_num)
        ErSpecRec['er_site_name']=er_site_name
        ErSpecRec['er_location_name']=er_location_name
        ErSampRec['sample_azimuth'] = dec
        ErSampRec['sample_dip'] = str(float(inc)-90)
        ErSampRec['sample_bed_dip_direction'] = bed_plane
        ErSampRec['sample_bed_tilt'] = bed_tilt
        ErSiteRec['site_lat'] = site_lat
        ErSiteRec['site_lon'] = site_lon
        ErSpecRec['magic_method_codes'] = meth_code
        ErSampRec['er_location_name'] = er_location_name
        ErSiteRec['er_location_name'] = er_location_name
        ErSiteRec['er_site_name'] = er_site_name
        ErSampRec['er_site_name'] = er_site_name
        ErSampRec['er_citation_names'] = 'This study'
        SpecOuts.append(ErSpecRec)
        SampOuts.append(ErSampRec)
        SiteOuts.append(ErSiteRec)

        #measurement data
        line = data.readline()
        line = line.rstrip("\n")
        items = line.split(",")
        while line != '9999':
            print(line)
            step=items[0]
            step=step.split('.')
            step_value=step[0]
            step_type = ""
            if len(step) == 2:
                step_type=step[1]
            if step_type=='5':
                step_value = items[0]
            A=float(items[1])
            B=float(items[2])
            C=float(items[3])
#  convert to MagIC coordinates
            Z=-A
            X=-B
            Y=C
            cart = np.array([X, Y, Z]).transpose()
            direction = pmag.cart2dir(cart).transpose()
            measurement_dec = direction[0]
            measurement_inc = direction[1]
            measurement_magn_moment = direction[2] * 1.0e-12 # the data are in pico-Am^2 - this converts to Am^2
            measurement_magn_volume = direction[2] * 1.0e-12 / volume # data volume normalized - converted to A/m
            print("measurement_magn_moment=", measurement_magn_moment)
            print("measurement_magn_volume=", measurement_magn_volume)
            error = items[4]
            date=items[5]
            date=date.strip('"')
            if date.count("-") > 0:
                date=date.split("-")
            elif date.count("/") > 0:
                date=date.split("/")
            else: print("date format seperator cannot be identified")
            print(date)
            time=items[6]
            time=time.strip('"')
            time=time.split(":")
            print(time)
            if dmy_flag:
                date_time = date[1] + ":" + date[0] + ":" + date[2] + ":" + time[0] + ":" + time[1] + ":" + "0.0"
            else:
                date_time = date[0] + ":" + date[1] + ":" + date[2] + ":" + time[0] + ":" + time[1] + ":" + "0.0"
            print(date_time)

            MagRec = {}
            MagRec["er_analyst_mail_names"] = operator
            MagRec["magic_instrument_codes"] = "Utrecht_" + machine
            MagRec["measurement_description"] = "free string = " + free_string
            MagRec["measurement_date"] = date_time 
            MagRec["er_citation_names"] = "This study"
            MagRec['er_location_name'] = er_location_name
            MagRec['er_site_name'] = er_site_name
            MagRec['er_sample_name'] = sample_name
            MagRec['magic_software_packages'] = version_num
            MagRec["measurement_temp"] = '%8.3e' % (273) # room temp in kelvin
            MagRec["measurement_flag"] = 'g'
            MagRec["measurement_standard"] = 'u'
            MagRec["magic_experiment_name"] = er_location_name + er_site_name + spec_name
            MagRec["measurement_number"] = er_location_name + er_site_name + spec_name + items[0]
            MagRec["er_specimen_name"] = spec_name
            # MagRec["treatment_ac_field"] = '0'
            if AF_or_T.lower() == "th":
                MagRec["treatment_temp"] = '%8.3e' % (float(step_value)+273.) # temp in kelvin
                MagRec['treatment_ac_field']='0'
                meas_type = "LP-DIR-T:LT-T-Z"
            else:
                MagRec['treatment_temp']='273'
                MagRec['treatment_ac_field']='%10.3e'%(float(step_value)*1e-3)
                meas_type = "LP-DIR-AF:LT-AF-Z"
            MagRec['treatment_dc_field']='0'
            if step_value == '0':
                meas_type = "LT-NO"
            print("step_type=", step_type)
            if step_type == '0' and AF_or_T.lower() == 'th':
                if meas_type == "":
                    meas_type = "LT-T-Z"
                else:
                    meas_type = meas_type + ":" + "LT-T-Z"
            elif step_type == '1':
                if meas_type == "":
                    meas_type = "LT-T-I"
                else:
                    meas_type = meas_type + ":" + "LT-T-I"
                MagRec['treatment_dc_field']='%1.2e'%DC_FIELD
            elif step_type == '2':
                if meas_type == "":
                    meas_type = "LT-PTRM-I"
                else:
                    meas_type = meas_type + ":" + "LT-PTRM-I"
                MagRec['treatment_dc_field']='%1.2e'%DC_FIELD
            elif step_type == '3':
                if meas_type == "" :
                    meas_type = "LT-PTRM-Z"
                else:
                    meas_type = meas_type + ":" + "LT-PTRM-Z"
            print("meas_type=", meas_type)
            MagRec['treatment_dc_field_phi'] = '%1.2f'%DC_PHI
            MagRec['treatment_dc_field_theta'] = '%1.2f'%DC_THETA
            MagRec['magic_method_codes'] = meas_type
            MagRec["measurement_magn_moment"] = measurement_magn_moment
            MagRec["measurement_magn_volume"] = measurement_magn_volume
            MagRec["measurement_dec"] = measurement_dec
            MagRec["measurement_inc"] = measurement_inc
            MagRec['measurement_csd'] = error 
#           MagRec['measurement_positions'] = '1'
            MagRecs.append(MagRec)

            line = data.readline()
            line = line.rstrip("\n")
            items = line.split(",")
        line = data.readline()
        line = line.rstrip("\n")
        items = line.split(",")

# write out the data to MagIC data files
    pmag.magic_write(spec_file, SpecOuts, 'er_specimens')
    pmag.magic_write(samp_file, SampOuts, 'er_samples')
    pmag.magic_write(site_file, SiteOuts, 'er_sites')
#    MagOuts = pmag.measurements_methods(MagRecs, noave)
#    pmag.magic_write(meas_file, MagOuts, 'magic_measurements')
    pmag.magic_write(meas_file, MagRecs, 'magic_measurements')
    print("results put in ", meas_file)
    print("exit!")
    return True, meas_file

def do_help():
    return main.__doc__

if  __name__ == "__main__":
    main()
