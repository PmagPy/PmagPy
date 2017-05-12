#!/usr/bin/env python
from __future__ import print_function
from builtins import str
from builtins import range
import pandas as pd
import sys
import numpy as np
import pmagpy.pmag as pmag

def main(command_line=True, **kwargs):
    """
    NAME
        jr6_jr6_magic.py
 
    DESCRIPTION
        converts JR6 .jr6 format files to magic_measurements format files

    SYNTAX
        jr6_jr6_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -f FILE: specify  input file, or
        -F FILE: specify output file, default is magic_measurements.txt
        -Fsa: specify er_samples format file for appending, default is new er_samples.txt (Not working yet)
        -spc NUM : specify number of characters to designate a  specimen, default = 1
        -loc LOCNAME : specify location/study name
        -A: don't average replicate measurements
        -ncn NCON: specify sample naming convention (6 and 7 not yet implemented)
        -mcd [SO-MAG,SO-SUN,SO-SIGHT...] supply how these samples were oriented
        -JR  IODP samples measured on the JOIDES RESOLUTION
        -v NUM : specify the volume in cc of the sample, default 2.5^3cc
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site is entered under a separate column -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.
 
    INPUT
        JR6 .jr6 format file
    """
# initialize some stuff
    noave=0
    #volume=2.5**3 #default volume is a 2.5cm cube
    volume = 2.5 * 1e-6 #default volume is a 2.5 cm cube, translated to meters cubed
    inst=""
    samp_con,Z='1',""
    missing=1
    demag="N"
    er_location_name="unknown"
    citation='This study'
    args=sys.argv
    meth_code="LP-NO"
    specnum=1
    version_num=pmag.get_version()
    Samps=[] # keeps track of sample orientations

    user=""
    mag_file=""
    dir_path='.'
    MagRecs=[]
    ErSamps=[]
    SampOuts=[]

    samp_file = 'er_samples.txt'
    meas_file = 'magic_measurements.txt'
    tmp_file= "fixed.jr6"
    meth_code,JR="",0
    #
    # get command line arguments
    #
    
    if command_line:
        if '-WD' in sys.argv:
            ind = sys.argv.index('-WD')
            dir_path=sys.argv[ind+1]
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
            ind=args.index("-F")
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
            mag_file= args[ind+1]
        if "-spc" in args:
            ind = args.index("-spc")
            specnum = int(args[ind+1])
        if "-ncn" in args:
            ind=args.index("-ncn")
            samp_con=sys.argv[ind+1]
        if "-loc" in args:
            ind=args.index("-loc")
            er_location_name=args[ind+1]
        if "-A" in args: noave=1
        if "-mcd" in args: 
            ind=args.index("-mcd")
            meth_code=args[ind+1]
        if "-JR" in args: 
            meth_code=meth_code+":FS-C-DRILL-IODP:SP-SS-C:SO-V"
            meth_code=meth_code.strip(":")
            JR=1
            samp_con='5'
        if "-v" in args: 
            ind=args.index("-v")
            volume=float(args[ind+1])*1e-6 # enter volume in cc, convert to m^3
    if not command_line:
        dir_path = kwargs.get('dir_path', '.')
        input_dir_path = kwargs.get('input_dir_path', dir_path)
        output_dir_path = dir_path
        meas_file = kwargs.get('meas_file', 'magic_measurements.txt')
        mag_file = kwargs.get('mag_file')
        samp_file = kwargs.get('samp_file', 'er_samples.txt')
        specnum = kwargs.get('specnum', 1)
        samp_con = kwargs.get('samp_con', '1')
        er_location_name = kwargs.get('er_location_name', '')
        noave = kwargs.get('noave', 0) # default (0) means DO average
        meth_code = kwargs.get('meth_code', "LP-NO")
        volume = float(kwargs.get('volume', 0))
        if not volume:
            volume = 2.5 * 1e-6 #default volume is a 2.5 cm cube, translated to meters cubed
        else:
            #convert cm^3 to m^3
            volume *= 1e-6
        JR = kwargs.get('JR', 0)
        if JR:
            if meth_code == "LP-NO":
                meth_code = ""
            meth_code=meth_code+":FS-C-DRILL-IODP:SP-SS-C:SO-V"
            meth_code=meth_code.strip(":")
            samp_con='5'

    # format variables
    mag_file = input_dir_path+"/" + mag_file
    meas_file = output_dir_path+"/" + meas_file
    samp_file = output_dir_path+"/" + samp_file
    tmp_file = output_dir_path+"/" + tmp_file
    if specnum!=0:
        specnum=-specnum
    if "4" in samp_con:
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "option [4] must be in form 4-Z where Z is an integer"
        else:
            Z=samp_con.split("-")[1]
            samp_con="4"
    if "7" in samp_con:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z=samp_con.split("-")[1]
            samp_con="7"

    ErSampRec,ErSiteRec={},{}

    # parse data

    # fix .jr6 file so that there are spaces between all the columns.
    pre_data=open(mag_file, 'r')
    tmp_data=open(tmp_file, 'w')
    line=pre_data.readline()
    while line !='':
        line=line.replace('-',' -')
        #print "line=", line
        tmp_data.write(line)
        line=pre_data.readline()
    tmp_data.close()
    pre_data.close()

    data=pd.read_csv(tmp_file, delim_whitespace=True,header=None)

    if JR==0: #
        data.columns=['er_specimen_name','step','x','y','z','expon','sample_azimuth','sample_dip',              'sample_bed_dip_direction','sample_bed_dip','bed_dip_dir2','bed_dip2','param1','param2','param3','param4','measurement_csd']
        cart=np.array([data['x'],data['y'],data['z']]).transpose()
    else: # measured on the Joides Resolution JR6
        data.columns=['er_specimen_name','step','negz','y','x','expon','sample_azimuth','sample_dip',              'sample_bed_dip_direction','sample_bed_dip','bed_dip_dir2','bed_dip2','param1','param2','param3','param4','measurement_csd']
        cart=np.array([data['x'],data['y'],-data['negz']]).transpose()
    dir= pmag.cart2dir(cart).transpose()
    data['measurement_dec']=dir[0]
    data['measurement_inc']=dir[1]
    data['measurement_magn_moment']=dir[2]*(10.0**data['expon'])*volume # the data are in A/m - this converts to Am^2
    data['measurement_magn_volume']=dir[2]*(10.0**data['expon']) # A/m  - data in A/m
    data['sample_dip']=-data['sample_dip']
    DGEOs,IGEOs=[],[]
    for ind in range(len(data)):
        dgeo,igeo=pmag.dogeo(data.iloc[ind]['measurement_dec'],data.iloc[ind]['measurement_inc'],data.iloc[ind]['sample_azimuth'],data.iloc[ind]['sample_dip'])
        DGEOs.append(dgeo)
        IGEOs.append(igeo)
    data['specimen_dec']=DGEOs
    data['specimen_inc']=IGEOs
    data['specimen_tilt']='1'
    if specnum!=0:
        data['er_sample_name']=data['er_specimen_name'][:specnum]
    else:
        data['er_sample_name']=data['er_specimen_name']

    if int(samp_con) in [1, 2, 3, 4, 5, 7]:
        data['er_site_name']=pmag.parse_site(data['er_sample_name'],samp_con,Z)
    # else:
    #     if 'er_site_name' in ErSampRec.keys():er_site_name=ErSampRec['er_site_name']
    #     if 'er_location_name' in ErSampRec.keys():er_location_name=ErSampRec['er_location_name']

    # Configure the er_sample table        

    for rowNum, row in data.iterrows():
        sampleFlag=0
        for sampRec in SampOuts:
            if sampRec['er_sample_name'] == row['er_sample_name']:
                sampleFlag=1
                break
        if sampleFlag == 0:
            ErSampRec['er_sample_name']=row['er_sample_name']
            ErSampRec['sample_azimuth']=str(row['sample_azimuth'])
            ErSampRec['sample_dip']=str(row['sample_dip'])
            ErSampRec['magic_method_codes']=meth_code 
            ErSampRec['er_location_name']=er_location_name
            ErSampRec['er_site_name']=row['er_site_name']
            ErSampRec['er_citation_names']='This study'
            SampOuts.append(ErSampRec.copy())

    # Configure the magic_measurements table

    for rowNum, row in data.iterrows():
        MagRec={}
#        MagRec['measurement_description']='Date: '+date
        MagRec["er_citation_names"]="This study"
        MagRec['er_location_name']=er_location_name
        MagRec['er_site_name']=row['er_site_name']
        MagRec['er_sample_name']=row['er_sample_name']
        MagRec['magic_software_packages']=version_num
        MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
        MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
        MagRec["measurement_flag"]='g'
        MagRec["measurement_standard"]='u'
        MagRec["measurement_number"]='1'
        MagRec["er_specimen_name"]=row['er_specimen_name']
        MagRec["treatment_ac_field"]='0'
        if row['step'] == 'NRM':
            meas_type="LT-NO"
        elif row['step'][0:2] == 'AD':
            meas_type="LT-AF-Z"
            treat=float(row['step'][2:])
            MagRec["treatment_ac_field"]='%8.3e' %(treat*1e-3) # convert from mT to tesla
        elif row['step'][0] == 'TD':
            meas_type="LT-T-Z"
            treat=float(row['step'][2:])
            MagRec["treatment_temp"]='%8.3e' % (treat+273.) # temp in kelvin
        else: # need to add IRM, and ARM options
            print("measurement type unknown", row['step'])
            return False, "measurement type unknown"
        MagRec["measurement_magn_moment"]=str(row['measurement_magn_moment'])
        MagRec["measurement_magn_volume"]=str(row['measurement_magn_volume'])
        MagRec["measurement_dec"]=str(row['measurement_dec'])
        MagRec["measurement_inc"]=str(row['measurement_inc'])
        MagRec['magic_method_codes']=meas_type
        MagRecs.append(MagRec.copy())
    pmag.magic_write(samp_file,SampOuts,'er_samples')
    print("sample orientations put in ",samp_file)
    MagOuts=pmag.measurements_methods(MagRecs,noave)
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print("results put in ",meas_file)
    print("exit!")
    return True, meas_file

def do_help():
    return main.__doc__

if  __name__ == "__main__":
    main()
