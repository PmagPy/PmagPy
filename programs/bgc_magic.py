#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from builtins import str
from past.utils import old_div
import pandas as pd
import sys
import os
import numpy as np
import pmagpy.pmag as pmag


def main(command_line=True, **kwargs):
    """
    NAME
        bgc_magic.py

    DESCRIPTION
        converts Berkeley Geochronology Center (BGC) format files to magic_measurements format files

    SYNTAX
        bgc_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -f FILE: specify  input file, or
        -F FILE: specify output file, default is magic_measurements.txt
        -Fsa: specify er_samples format file for appending, default is new er_samples.txt (Not working yet)
        -loc LOCNAME : specify location/study name
        -site SITENAME : specify site name
        -A: don't average replicate measurements
        -mcd [SO-MAG,SO-SUN,SO-SIGHT...] supply how these samples were oriented
        -v NUM : specify the volume in cc of the sample, default 2.5^3cc. Will use vol in data file if volume!=0 in file.

    INPUT
        BGC paleomag format file
    """
# initialize some stuff
    noave = 0
    volume = 0.025**3 #default volume is a 2.5cm cube
    #inst=""
    #samp_con,Z='1',""
    #missing=1
    #demag="N"
    er_location_name = "unknown"
    er_site_name = "unknown"
    #citation='This study'
    args = sys.argv
    meth_code = "LP-NO"
    #specnum=1
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
            print(main.__doc__)
            return False
        if '-F' in args:
            ind = args.index("-F")
            meas_file = args[ind+1]
        if '-Fsa' in args:
            ind = args.index("-Fsa")
            samp_file = args[ind+1]
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
        if "-site" in args:
            ind = args.index("-site")
            er_site_name = args[ind+1]
        if "-A" in args:
            noave = 1
        if "-mcd" in args:
            ind = args.index("-mcd")
            meth_code = args[ind+1]
            #samp_con='5'
        if "-v" in args:
            ind = args.index("-v")
            volume = float(args[ind+1]) * 1e-6 # enter volume in cc, convert to m^3
    if not command_line:
        dir_path = kwargs.get('dir_path', '.')
        input_dir_path = kwargs.get('input_dir_path', dir_path)
        output_dir_path = dir_path
        meas_file = kwargs.get('meas_file', 'magic_measurements.txt')
        mag_file = kwargs.get('mag_file')
        samp_file = kwargs.get('samp_file', 'er_samples.txt')
        er_location_name = kwargs.get('er_location_name', '')
        er_site_name = kwargs.get('er_site_name', '')
        noave = kwargs.get('noave', 0) # default (0) means DO average
        meth_code = kwargs.get('meth_code', "LP-NO")
        volume = float(kwargs.get('volume', 0))
        if not volume:
            volume = 0.025**3 #default volume is a 2.5 cm cube, translated to meters cubed
        else:
            #convert cm^3 to m^3
            volume *= 1e-6

    # format variables
    if not mag_file:
        return False, 'You must provide a BCG format file'
    mag_file = os.path.join(input_dir_path, mag_file)
    meas_file = os.path.join(output_dir_path, meas_file)
    samp_file = os.path.join(output_dir_path, samp_file)

    ErSampRec = {}

    # parse data

    # Open up the BGC file and read the header information
    print('mag_file in bgc_magic', mag_file)
    pre_data = open(mag_file, 'r')
    line = pre_data.readline()
    line_items = line.split(' ')
    sample_name = line_items[2]
    sample_name = sample_name.replace('\n', '')
    line = pre_data.readline()
    line = pre_data.readline()
    line_items = line.split('\t')
    sample_azimuth = float(line_items[1])
    sample_dip = float(line_items[2])
    sample_bed_dip = line_items[3]
    sample_bed_azimuth = line_items[4]
    sample_lon = line_items[5]
    sample_lat = line_items[6]
    tmp_volume = line_items[7]
    if tmp_volume != 0.0:
        volume = float(tmp_volume) * 1e-6
    pre_data.close()

    data = pd.read_csv(mag_file, sep='\t', header=3, index_col=False)

    cart = np.array([data['X'], data['Y'], data['Z']]).transpose()
    direction = pmag.cart2dir(cart).transpose()

    data['measurement_dec'] = direction[0]
    data['measurement_inc'] = direction[1]
    data['measurement_magn_moment'] = old_div(direction[2], 1000)  # the data are in EMU - this converts to Am^2 
    data['measurement_magn_volume'] = old_div((old_div(direction[2], 1000)), volume) # EMU  - data converted to A/m
    
    # Configure the er_sample table

    ErSampRec['er_sample_name'] = sample_name
    ErSampRec['sample_azimuth'] = sample_azimuth
    ErSampRec['sample_dip'] = sample_dip
    ErSampRec['sample_bed_dip_direction'] = sample_bed_azimuth
    ErSampRec['sample_bed_dip'] = sample_bed_dip
    ErSampRec['sample_lat'] = sample_lat
    ErSampRec['sample_lon'] = sample_lon
    ErSampRec['magic_method_codes'] = meth_code
    ErSampRec['er_location_name'] = er_location_name
    ErSampRec['er_site_name'] = er_site_name
    ErSampRec['er_citation_names'] = 'This study'
    SampOuts.append(ErSampRec.copy())

    # Configure the magic_measurements table

    for rowNum, row in data.iterrows():
        MagRec = {}
        MagRec['measurement_description'] = 'Date: ' + str(row['Date']) + ' Time: ' + str(row['Time'])
        MagRec["er_citation_names"] = "This study"
        MagRec['er_location_name'] = er_location_name
        MagRec['er_site_name'] = er_site_name
        MagRec['er_sample_name'] = sample_name
        MagRec['magic_software_packages'] = version_num
        MagRec["treatment_temp"] = '%8.3e' % (273) # room temp in kelvin
        MagRec["measurement_temp"] = '%8.3e' % (273) # room temp in kelvin
        MagRec["measurement_flag"] = 'g'
        MagRec["measurement_standard"] = 'u'
        MagRec["measurement_number"] = rowNum
        MagRec["er_specimen_name"] = sample_name
        MagRec["treatment_ac_field"] = '0'
        if row['DM Val'] == '0':
            meas_type = "LT-NO"
        elif int(row['DM Type']) > 0.0:
            meas_type = "LT-AF-Z"
            treat = float(row['DM Val'])
            MagRec["treatment_ac_field"] = '%8.3e' %(treat*1e-3) # convert from mT to tesla
        elif int(row['DM Type']) == -1:
            meas_type = "LT-T-Z"
            treat = float(row['DM Val'])
            MagRec["treatment_temp"] = '%8.3e' % (treat+273.) # temp in kelvin
        else:
            print("measurement type unknown:", row['DM Type'], " in row ", rowNum)
        MagRec["measurement_magn_moment"] = str(row['measurement_magn_moment'])
        MagRec["measurement_magn_volume"] = str(row['measurement_magn_volume'])
        MagRec["measurement_dec"] = str(row['measurement_dec'])
        MagRec["measurement_inc"] = str(row['measurement_inc'])
        MagRec['magic_method_codes'] = meas_type
        MagRec['measurement_csd'] = '0.0' # added due to magic.write error
        MagRec['measurement_positions'] = '1' # added due to magic.write error
        MagRecs.append(MagRec.copy())
    pmag.magic_write(samp_file, SampOuts, 'er_samples')
    print("sample orientations put in ", samp_file)
    MagOuts = pmag.measurements_methods(MagRecs, noave)
    pmag.magic_write(meas_file, MagOuts, 'magic_measurements')
    print("results put in ", meas_file)
    return True, meas_file

def do_help():
    return main.__doc__

if  __name__ == "__main__":
    main()
