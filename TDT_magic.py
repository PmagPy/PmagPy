#!/usr/bin/env python
import string,sys,pmag
def main():
    """
    NAME
        TDT_magic.py
 
    DESCRIPTION
        converts ThellierTool format files to magic_measurements format files

    SYNTAX
        TDT_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -usr USER:   identify user, default is ""
        -f FILE: specify .tdt format input file, required
        -F FILE: specify output file, default is magic_measurements.txt
        -spc NUM : specify number of characters to designate a  specimen, default = 0
        -loc LOCNAME : specify location/study name, must have either LOCNAME or SAMPFILE or be a synthetic
        -ncn NCON:  specify naming convention: default is #1 below
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
 
 
    INPUT
        Format of ThellierTool  files:   
   2 line header:
   Thellier-tdt
   XX.0  (field in microtesla)
   blank line indicates new specimen
   Data:
   Spec Treat Intensity Declination Inclination
        
        Spec: specimen name
        Treat:  treatment step
                XXX.00  first zero field step
                XXX.11 (or .1)  first in field step [XXX.0 and XXX.1 can be done in any order]
                XXX.12 (or .2)second in-field step at lower temperature (pTRM check)
                XXX.13 (or .3) second zero-field step after infield (pTRM check step)
                       XXX.13 MUST be done in this order [XXX.00, XXX.11 [optional XXX.12] XXX.13]
         
         Intensity assumed to be magnetization in mA/m
         Declination:  Declination in specimen coordinate system
         Inclination:  Declination in specimen coordinate system

    """
# initialize some stuff
    noave=0
    methcode,inst="",""
    phi,theta,labfield=0,90,0
    pTRM,MD,samp_con,Z=0,0,'1',1
    demag="N"
    er_location_name=""
    citation='This study'
    args=sys.argv
    methcode="LP-NO"
    specnum=0
#
# get command line arguments
#
    meas_file,samp_file="magic_measurements.txt","er_samples.txt"
    user=""
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-usr" in args:
        ind=args.index("-usr")
        user=args[ind+1]
    if '-F' in args:
        ind=args.index("-F")
        meas_file=args[ind+1]
    if '-f' in args:
        ind=args.index("-f")
        magfile=args[ind+1]
        try:
            input=open(magfile,'rU')
        except:
            print "bad mag file name"
            sys.exit()
    else: 
        print "mag_file field is required option"
        print main.__doc__
        sys.exit()
    if "-spc" in args:
        ind=args.index("-spc")
        specnum=int(args[ind+1])
        if specnum!=0:specnum=-specnum
    if "-loc" in args:
        ind=args.index("-loc")
        er_location_name=args[ind+1]
    if "-ncn" in args:
        ind=args.index("-ncn")
        samp_con=sys.argv[ind+1]
        if "4" in samp_con:
            if "-" not in samp_con:
                print "option [4] must be in form 4-Z where Z is an integer"
                sys.exit()
            else:
                Z=samp_con.split("-")[1]
                samp_con="4"
        if "7" in samp_con:
            if "-" not in samp_con:
                print "option [4] must be in form 7-Z where Z is an integer"
                sys.exit()
            else:
                Z=samp_con.split("-")[1]
                samp_con="4"
    MagRecs=[]
    demag="T"
    version_num=pmag.get_version()
    data=input.readlines()
    rec=data[1].split()
    labfield=float(rec[0])*1e-6
    ind=2
    for line in data[ind:]:
      if line!="":
        rec=line.split()
        if len(rec)>2:
            MagRec={}
            MagRec['er_location_name']=er_location_name
            MagRec['magic_software_packages']=version_num
            MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["treatment_ac_field"]='0'
            MagRec["treatment_dc_field"]='0'
            MagRec["treatment_dc_field_phi"]='0'
            MagRec["treatment_dc_field_theta"]='0'
            meas_type="LT-NO"
            MagRec["er_specimen_name"]=rec[0]
            MagRec["er_synthetic_name"]=""
            MagRec["er_site_name"]=""
            if specnum!=0:
                MagRec["er_sample_name"]=rec[0][:specnum]
            else:
                MagRec["er_sample_name"]=rec[0]
            if "-fsa" in args:
                for samp in Samps:
                    if samp["er_sample_name"] == MagRec["er_sample_name"]: 
                        MagRec["er_location_name"]=samp["er_location_name"]
                        MagRec["er_site_name"]=samp["er_site_name"]
                        break
            elif int(samp_con)!=6:
                site=pmag.parse_site(MagRec['er_sample_name'],samp_con,Z)
                MagRec["er_site_name"]=site
            if MagRec['er_site_name']=="":
                print 'No site name found for: ',MagRec['er_specimen_name'],MagRec['er_sample_name']
            if MagRec["er_location_name"]=="":
                print 'no location name for: ',MagRec["er_specimen_name"] 
            if rec[1]==".00":rec[1]="0.00"
            treat=rec[1].split('.')
            if float(rec[1])==0:
                pass 
            if len(treat)==1:treat.append('0')
            MagRec["treatment_temp"]='%8.3e' % (float(treat[0])+273.) # temp in kelvin
            if treat[1][0]=='0':
                meas_type="LT-T-Z"
            else: 
                MagRec["treatment_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                MagRec["treatment_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                MagRec["treatment_dc_field_theta"]='%7.1f' % (theta) # labfield theta
                if treat[1][-1]=='1':meas_type="LT-T-I" # in-field thermal step
                if treat[1][-1]=='2':
                    meas_type="LT-PTRM-I" # pTRM check
                    pTRM=1
                if treat[1][-1]=='3':
                    MagRec["treatment_dc_field"]='0'  # this is a zero field step
                    meas_type="LT-PTRM-MD" # pTRM tail check
            MagRec["measurement_magn_moment"]='%10.3e'% (float(rec[2])*1e-3) # magnetization in Am^2 (from mA/m)
            MagRec["measurement_dec"]=rec[3]
            MagRec["measurement_inc"]=rec[4]
            MagRec["er_analyst_mail_names"]=user
            MagRec["er_citation_names"]=citation
            MagRec["magic_method_codes"]=meas_type
            MagRec["measurement_flag"]='g'
            MagRec["measurement_standard"]='u'
            MagRec["measurement_number"]='1'
            MagRecs.append(MagRec) 
      else: # new specimen
        rec=data[ind+2].split()
        labfield=float(rec[0])*1e-6
        ind+=3
    MagOuts=pmag.measurements_methods(MagRecs,noave)
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print "results put in ",meas_file
main()
