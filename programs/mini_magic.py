#!/usr/bin/env python
from __future__ import print_function
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
        mini_magic.py
 
    DESCRIPTION
        converts the Yale minispin format to magic_measurements format files

    SYNTAX
        mini_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -usr USER:   identify user, default is ""
        -f FILE: specify input file, required
        -F FILE: specify output file, default is magic_measurements.txt
        -LP [colon delimited list of protocols, include all that apply]
            AF:  af demag
            T: thermal including thellier but not trm acquisition
        -spc NUM : specify number of characters to designate a  specimen, default = 0
        -ncn NCON:  specify naming convention: default is #1 below
        -A: don't average replicate measurements
        -vol: volume assumed for measurement in cm^3
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site is entered under a separate column NOT CURRENTLY SUPPORTED
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.
 
            [8] synthetic - has no site name
            [9] ODP naming convention 
            [10] LL-SI-SA-SP_STEP where LL is location, SI is site, SA is sample and SP is specimen and STEP is demagnetization step

    INPUT
        Must put separate experiments (all AF, thermal,  etc.) in 
           seperate files 

        Format of Yale MINI files:   
        LL-SI-SP_STEP, Declination, Inclination, Intensity (mA/m), X,Y,Z
        
     
    """
# initialize some stuff
    noave=0
    methcode,inst="LP-NO",""
    samp_con,Z='10',1
    demag="N"
    er_location_name=""
    citation='This study'
    args=sys.argv
    coil=""
    volume=10e-6 # assume a volume of 10cc
#
# get command line arguments
#
    user=""
    dir_path='./'
    if '-WD' in args:
        ind=args.index('-WD')
        dir_path=args[ind+1]
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    if "-usr" in args:
        ind=args.index("-usr")
        user=args[ind+1]
    if '-F' in args:
        ind=args.index("-F")
        meas_file=dir_path+args[ind+1]
    else:
        meas_file=dir_path+'magic_measurements.txt'
    if '-f' in args:
        ind=args.index("-f")
        magfile=dir_path+args[ind+1]
        try:
            input=open(magfile,'r')
        except:
            print("bad mag file name")
            sys.exit()
    else: 
        print("mag_file field is required option")
        print(main.__doc__)
        sys.exit()
    specnum=0
    if "-spc" in args:
        ind=args.index("-spc")
        specnum=int(args[ind+1])
        if specnum!=0:specnum=-specnum
    if "-loc" in args:
        ind=args.index("-loc")
        er_location_name=args[ind+1]
    if "-ins" in args:
        ind=args.index("-ins")
        inst=args[ind+1]
    if "-vol" in args:
        ind=args.index("-vol")
        volume=1e-6*float(args[ind+1])
    if "-A" in args: noave=1
    if "-ncn" in args:
        ind=args.index("-ncn")
        samp_con=sys.argv[ind+1]
        if "4" in samp_con:
            if "-" not in samp_con:
                print("option [4] must be in form 4-Z where Z is an integer")
                sys.exit()
            else:
                Z=samp_con.split("-")[1]
                samp_con="4"
        if "7" in samp_con:
            if "-" not in samp_con:
                print("option [7] must be in form 7-Z where Z is an integer")
                sys.exit()
            else:
                Z=samp_con.split("-")[1]
                samp_con="4"
    if '-LP' in args:
        ind=args.index("-LP")
        codelist=args[ind+1]
        codes=codelist.split(':')
        if "AF" in codes:
            demag='AF' 
            methcode="LT-AF-Z"
        if "T" in codes:
            demag="T"
    MagRecs=[]
    version_num=pmag.get_version()
    for line in input.readlines():
        rec=line.split(',')
        if len(rec)>1:
            MagRec={}
            IDs=rec[0].split('_')
            treat=IDs[1]
            MagRec["er_specimen_name"]=IDs[0]
            print(MagRec['er_specimen_name'])
            sids=IDs[0].split('-')
            MagRec['er_location_name']=sids[0]
            MagRec['er_site_name']=sids[0]+'-'+sids[1]
            if len(sids)==2:
                MagRec["er_sample_name"]=IDs[0]
            else:
                MagRec["er_sample_name"]=sids[0]+'-'+sids[1]+'-'+sids[2]
            print(MagRec)
            MagRec['magic_software_packages']=version_num
            MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["treatment_ac_field"]='0'
            MagRec["treatment_dc_field"]='0'
            MagRec["treatment_dc_field_phi"]='0'
            MagRec["treatment_dc_field_theta"]='0'
            meas_type="LT-NO"
            if demag=="AF":
                MagRec["treatment_ac_field"]='%8.3e' %(float(treat)*1e-3) # peak field in tesla
            if demag=="T":
                meas_type="LT-T-Z"
                MagRec["treatment_dc_field"]='%8.3e'%(0)
                MagRec["treatment_temp"]='%8.3e' % (float(treat)+273.) # temp in kelvin
            if demag=="N":
                meas_type="LT-NO"
                MagRec["treatment_ac_field"]='0'
                MagRec["treatment_dc_field"]='0'
            MagRec["measurement_magn_moment"]='%10.3e'% (volume*float(rec[3])*1e-3) # moment in Am2 (from mA/m)
            MagRec["measurement_dec"]=rec[1]
            MagRec["measurement_inc"]=rec[2]
            MagRec["magic_instrument_codes"]=inst
            MagRec["er_analyst_mail_names"]=user
            MagRec["er_citation_names"]=citation
            MagRec["magic_method_codes"]=methcode.strip(':')
            MagRec["measurement_flag"]='g'
            MagRec["measurement_standard"]='u'
            MagRec["measurement_number"]='1'
            MagRecs.append(MagRec) 
    MagOuts=pmag.measurements_methods(MagRecs,noave)
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print("results put in ",meas_file)

if __name__ == "__main__":
    main()
