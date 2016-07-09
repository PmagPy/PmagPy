#!/usr/bin/env python
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
        -loc LOCNAME : specify location/study name
        -site SITENAME : specify site name
        -lat latitude of samples
        -lon longitude of samples
        -A: don't average replicate measurements
        -mcd [SO-MAG,SO-SUN,SO-SIGHT...] supply how these samples were oriented

    INPUT
        Utrecht magnetometer data file
    """
# initialize some stuff
    sample_lat = 0.0
    sample_lon = 0.0
    noave = 0
    er_location_name = "unknown"
    er_site_name = "unknown"
    args = sys.argv
    meth_code = "LP-NO"
    version_num = pmag.get_version()

    mag_file = ""
    dir_path = '.'
    MagRecs = []
    SampOuts = []

    samp_file = 'er_samples.txt'
    meas_file = 'magic_measurements.txt'
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
            print main.__doc__
            return False
        if '-F' in args:
            ind = args.index("-F")
            meas_file = args[ind+1]
        if '-Fsa' in args:
            ind = args.index("-Fsa")
            samp_file = args[ind+1]
            #try:
            #    open(samp_file,'rU')
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
            sample_lat = args[ind+1]
        if "-lon" in args:
            ind = args.index("-lon")
            sample_lon = args[ind+1]
        if "-site" in args:
            ind = args.index("-site")
            er_site_name = args[ind+1]
        if "-A" in args:
            noave = 1
        if "-mcd" in args:
            ind = args.index("-mcd")
            meth_code = args[ind+1]
            #samp_con='5'

    if not command_line:
        dir_path = kwargs.get('dir_path', '.')
        input_dir_path = kwargs.get('input_dir_path', dir_path)
        output_dir_path = dir_path
        meas_file = kwargs.get('meas_file', 'magic_measurements.txt')
        mag_file = kwargs.get('mag_file')
        samp_file = kwargs.get('samp_file', 'er_samples.txt')
        er_location_name = kwargs.get('er_location_name', '')
        er_site_name = kwargs.get('er_site_name', '')
        sample_lat = kwargs.get('sample_lat', '')
        sample_lon = kwargs.get('sample_lon', '')
        #oave = kwargs.get('noave', 0) # default (0) means DO average
        meth_code = kwargs.get('meth_code', "LP-NO")

    # format variables
    if not mag_file:
        return False, 'You must provide a Utrecht formated file'
    mag_file = os.path.join(input_dir_path, mag_file)
    meas_file = os.path.join(output_dir_path, meas_file)
    samp_file = os.path.join(output_dir_path, samp_file)

    ErSampRec = {}

    # parse data

    # Open up the Utrecht file and read the header information
    print 'mag_file in utrecht_file', mag_file
    data = open(mag_file, 'rU')
    line = data.readline()
    line_items = line.split(',')
    operator=line_items[0]
    operator=operator.replace("\"","")
    machine=line_items[1]
    machine=machine.replace("\"","")
    machine=machine.rstrip('\n')
    print "operator=", operator
    print "machine=", machine
    line = data.readline()
    while line != '"END"' :
        line_items = line.split(',')
        sample_name=line_items[0]
        sample_name=sample_name.replace("\"","")
        print "sample_name=", sample_name
        free_string=line_items[1]
        free_string=free_string.replace("\"","")
        print "free_string=", free_string
        dec=line_items[2]
        print "dec=", dec
        inc=line_items[3]
        print "inc=", inc
        volume=float(line_items[4])
        volume=volume * 1e-6 # enter volume in cm^3, convert to m^3
        print "volume=", volume
        bed_plane=line_items[5]
        print "bed_plane=", bed_plane
        bed_tilt=line_items[6]
        print "bed_tilt=", bed_tilt

        # Configure et er_samples table
        ErSampRec['er_sample_name'] = sample_name
        ErSampRec['sample_azimuth'] = dec
        ErSampRec['sample_dip'] = inc
        ErSampRec['sample_bed_dip_direction'] = bed_plane
        ErSampRec['sample_bed_tilt'] = bed_tilt
        ErSampRec['sample_lat'] = sample_lat
        ErSampRec['sample_lon'] = sample_lon
        ErSampRec['magic_method_codes'] = meth_code
        ErSampRec['er_location_name'] = er_location_name
        ErSampRec['er_site_name'] = er_site_name
        ErSampRec['er_citation_names'] = 'This study'
        SampOuts.append(ErSampRec.copy())
        
        line = data.readline()
        line = line.rstrip("\n")
        items = line.split(",")
    #    exit()
        while line != '9999' :
            print line
            step=items[0]
            step=step.split('.')
            step_value=step[0]
            step_type = ""
            if len(step) == 2:
                step_type=step[1]
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
            print "measurement_magn_moment=", measurement_magn_moment
            print "measurement_magn_volume=", measurement_magn_volume
            error = items[4]
            date=items[5]
            date=date.strip('"')
            date=date.split("-")
            print date
            time=items[6]
            time=time.strip('"')
            time=time.split(":")
            print time
            date_time = date[0] + ":" + date[1] + ":" + date[2] + ":" + time[0] + ":" + time[1] + ":" + "0.0"   
            print date_time

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
            MagRec["magic_experiment_name"] = er_location_name + er_site_name + sample_name
            MagRec["measurement_number"] = er_location_name + er_site_name + sample_name + items[0]
            MagRec["er_specimen_name"] = sample_name
            # MagRec["treatment_ac_field"] = '0'
            MagRec["treatment_temp"] = '%8.3e' % (float(step_value)+273.) # temp in kelvin
            meas_type = "LP-DIR-T"
            if step_value == '0':
                meas_type = "LT-NO"
            print "step_type=", step_type
            if step_type == '0':
                if meas_type == "" : 
                    meas_type = "LT-T-Z" 
                else:
                    meas_type = meas_type + ":" + "LT-T-Z" 
            elif step_type == '1':
                if meas_type == "" : 
                    meas_type = "LT-T-I" 
                else:
                    meas_type = meas_type + ":" + "LT-T-I" 
            elif step_type == '2':
                if meas_type == "" : 
                    meas_type = "LT-PTRM-I" 
                else:
                    meas_type = meas_type + ":" + "LT-PTRM-I" 
            elif step_type == '3':
                if meas_type == "" : 
                    meas_type = "LT-PTRM-Z" 
                else:
                    meas_type = meas_type + ":" + "LT-PTRM-Z" 
            print "meas_type=", meas_type
            MagRec['magic_method_codes'] = meas_type
            MagRec["measurement_magn_moment"] = measurement_magn_moment
            MagRec["measurement_magn_volume"] = measurement_magn_volume
            MagRec["measurement_dec"] = measurement_dec
            MagRec["measurement_inc"] = measurement_inc
            MagRec['measurement_csd'] = error 
#           MagRec['measurement_positions'] = '1'
            MagRecs.append(MagRec.copy())

            line = data.readline()
            line = line.rstrip("\n")
            items = line.split(",")
        line = data.readline()
        line = line.rstrip("\n")
        items = line.split(",")

# write out the data to MagIC data files
    pmag.magic_write(samp_file, SampOuts, 'er_samples')
    print "sample orientations put in ", samp_file
#    MagOuts = pmag.measurements_methods(MagRecs, noave)
#    pmag.magic_write(meas_file, MagOuts, 'magic_measurements')
    pmag.magic_write(meas_file, MagRecs, 'magic_measurements')
    print "results put in ", meas_file
    print "exit!"
    return True, meas_file

def do_help():
    return main.__doc__

if  __name__ == "__main__":
    main()
