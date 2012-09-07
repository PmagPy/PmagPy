#!/usr/bin/env python
import string,sys,pmag
def main():
    """
    NAME
        HUJI_magic.py
 
    DESCRIPTION
        converts Hebrew University, Jerusalem format files to magic_measurements format files

    SYNTAX
        HUJI_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -usr USER:   identify user, default is ""
        -f FILE: specify HUJI format input file, required
        -F FILE: specify output file, default is magic_measurements.txt
        -LP [colon delimited list of protocols, include all that apply]
            AF:  af demag
            T: thermal including thellier but not trm acquisition
            N: NRM only
            TRM: trm acquisition
            ANI: anisotropy experiment
            G: triple AF demag (GRM protocol)
        -spc NUM : specify number of characters to designate a  specimen, default = 0
        -loc LOCNAME : specify location/study name, must have either LOCNAME 
        -dc B PHI THETA: dc lab field (in micro tesla) and phi,theta, default is none
              NB: use PHI, THETA = -1 -1 to signal that it changes, i.e. in anisotropy experiment
        -ac B : peak AF field (in mT) for ARM acquisition, default is none
        -ncn NCON:  specify naming convention: default is #1 below
        -A: don't average replicate measurements
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
            [8] this is a synthetic sample with no site name
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.
 
    INPUT
        Best to put separate experiments (all AF, thermal, thellier, trm aquisition, Shaw, etc.) in 
           seperate files (eg. af.txt, thermal.txt, etc.)
        
        Spec: specimen name
        Treat:  treatment step
            XXX T in Centigrade
            XXX AF in mT
            for special experiments:
              Thellier:
                XXX.0  first zero field step
                XXX.1  first in field step [XXX.0 and XXX.1 can be done in any order]
                XXX.2  second in-field step at lower temperature (pTRM check)
                XXX.3  second zero-field step after infield (pTRM check step)
                       XXX.3 MUST be done in this order [XXX.0, XXX.1 [optional XXX.2] XXX.3]
              AARM:
                X.00  baseline step (AF in zero bias field - high peak field)
                X.1   ARM step (in field step)  where
                   X is the step number in the 15 position scheme 
                      (see Appendix to Lecture 13 - Lectures in Paleomagnetism, 2007)
              TRM:
                XXX.YYY  XXX is temperature step of total TRM
                         YYY is dc field in microtesla
         
         Intensity assumed to be total moment in 10^3 Am^2 (emu)
         Declination:  Declination in geographic coordinate system
         Inclination:  Declination in geographic coordinate system

    """
# initialize some stuff
    WD="."
    version_num=pmag.get_version()
    noave=0
    methcode,inst="",""
    phi,theta,peakfield,labfield=0,0,0,0
    pTRM,MD,samp_con,Z=0,0,'1',1
    dec=[315,225,180,135,45,90,270,270,270,90,180,180,0,0,0] # applied field for remanence anisotropy directions
    inc=[0,0,0,0,0,-45,-45,0,45,45,45,-45,-90,-45,45]
    demag="N"
    er_location_name=""
    citation='This study'
    args=sys.argv
    methcode="LP-NO" # NRM
    syn=0
    synfile='er_synthetics.txt'
    samp_file,site_file,ErSamps='er_samples.txt','er_sites.txt',[]
    samp_file_in=""
    meas_file="magic_measurements.txt"
    trm=0
    irm=0
    specnum=-1
#
# get command line arguments
#
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
    if '-Fsa' in args:
        ind=args.index("-Fsa")
        samp_file=args[ind+1]
        try:
            open(samp_file,'rU')
            ErSamps,file_type=pmag.magic_read(samp_file)
            print 'sample information will be appended to new er_samples.txt file'
        except:
            print 'sample information will be stored in new er_samples.txt file'
    if '-f' in args:
        ind=args.index("-f")
        magfile=args[ind+1]
        try:
            input=open(magfile,'rU')
        except:
            print "bad input file name"
            sys.exit()
    else: 
        print "mag_file field is required option"
        print main.__doc__
        sys.exit()
    if "-dc" in args:
        ind=args.index("-dc")
        labfield=float(args[ind+1])*1e-6
        phi=float(args[ind+2])
        theta=float(args[ind+3])
    if "-ac" in args:
        ind=args.index("-ac")
        peakfield=float(args[ind+1])*1e-3
    if "-spc" in args:
        ind=args.index("-spc")
        specnum=int(args[ind+1])
        if specnum!=0:specnum=-specnum
    if "-loc" in args:
        ind=args.index("-loc")
        er_location_name=args[ind+1]
    if '-syn' in args:
        syn=1
        ind=args.index("-syn")
        institution=args[ind+1]
        syntype=args[ind+2]
        if '-fsy' in args:
            ind=args.index("-fsy")
            synfile=args[ind+1]
    if "-A" in args: noave=1
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
                print "option [7] must be in form 7-Z where Z is an integer"
                sys.exit()
            else:
                Z=samp_con.split("-")[1]
                samp_con="7"
    if '-LP' in args:
        ind=args.index("-LP")
        codelist=args[ind+1]
        codes=codelist.split(':')
        if "AF" in codes:
            demag='AF' 
            if'-dc' not in args: methcode="LT-AF-Z"
            if'-dc' in args: methcode="LT-AF-I"
        if "T" in codes:
            demag="T"
            if '-dc' not in args: methcode="LT-T-Z"
            if '-dc' in args: methcode="LT-T-I"
        if "I" in codes:
            methcode="LP-IRM"
        if "G" in codes: methcode="LT-AF-G"
        if "TRM" in codes: 
            trm=1
            noave=1
    if demag=="T" and "ANI" in codes:
        methcode="LP-AN-TRM"
    if demag=="AF" and "ANI" in codes:
        methcode="LP-AN-ARM"
        if labfield==0: labfield=50e-6
        if peakfield==0: peakfield=180
    SynRecs,MagRecs=[],[]
    Data=input.readlines()
    for line in Data:
        instcode="HUJI-2G"
        if len(line)>1:
            rec=line.split()
            if rec[0][0]!='#': # HUJI way of marking bad data points
                SynRec={}
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
                mmddyy=rec[2].split('/') # break date into mon/day/year
                hhmm=rec[3]
                yyyy=mmddyy[2]
                mm=int(mmddyy[0])
                if mm<10:
                    mm="0"+str(mm)
                else: 
                    mm=str(mm)
                dd=int(mmddyy[1])
                if dd<10:
                    dd="0"+str(dd)
                else: 
                    dd=str(dd)
                    time=mmddyy[1].split(':')
                MagRec["measurement_date"]=yyyy+":"+mm+":"+dd+":"+hhmm+":00.00"
                MagRec["measurement_time_zone"]='30'
                MagRec["measurement_positions"]='1'
                if rec[4]=='T': demag="T"
                if rec[4]=='A': demag="AF"
                MagRec["er_specimen_name"]=rec[0]
                if specnum!=0:
                    MagRec["er_sample_name"]=rec[0][:specnum]
                else:
                    MagRec["er_sample_name"]=rec[0]
                if int(samp_con)!=6:
                    site=pmag.parse_site(MagRec['er_sample_name'],samp_con,Z)
                    MagRec["er_site_name"]=site
                    MagRec["er_location_name"]=er_location_name
                else: 
                    MagRec["er_site_name"]=""
                    MagRec["er_location_name"]=""
                    MagRec["er_synthetic_name"]=rec[0]
                treat=rec[5].split('.')
                if len(treat)==1:treat.append('.0')
                if demag=="AF":
                    if methcode != "LP-AN-ARM":
                        MagRec["treatment_ac_field"]='%8.3e' %(float(treat[0])*1e-3) # peak field in tesla
                        meas_type="LT-AF-Z"
                        MagRec["treatment_dc_field"]='0'
                    else: # AARM experiment
                        if treat[1][0]=='0':
                            meas_type="LT-AF-Z"
                            MagRec["treatment_ac_field"]='%8.3e' %(peakfield) # peak field in tesla
                            MagRec["treatment_dc_field"]='%8.3e'%(0)
                            if labfield!=0: print "inconsistency in mag file with lab field"
                        else:
                            meas_type="LT-AF-I"
                            ipos=int(treat[0])-1
                            MagRec["treatment_dc_field_phi"]='%7.1f' %(dec[ipos])
                            MagRec["treatment_dc_field_theta"]='%7.1f'% (inc[ipos])
                            MagRec["treatment_dc_field"]='%8.3e'%(labfield)
                            MagRec["treatment_ac_field"]='%8.3e' %(peakfield) # peak field in tesla
                else:  # thermal treatment
                  MagRec["treatment_temp"]='%8.3e' % (float(treat[0])+273.) # temp in kelvin
                  if trm==0:  # demag=T and not trmaq
                    if treat[1][0]=='0':
                        meas_type="LT-T-Z"
                    else: 
                        MagRec["treatment_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                        MagRec["treatment_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                        MagRec["treatment_dc_field_theta"]='%7.1f' % (theta) # labfield theta
                        if treat[1][0]=='1':meas_type="LT-T-I" # in-field thermal step
                        if treat[1][0]=='2':
                            meas_type="LT-PTRM-I" # pTRM check
                            pTRM=1
                        if treat[1][0]=='3':
                            MagRec["treatment_dc_field"]='0'  # this is a zero field step
                            meas_type="LT-PTRM-MD" # pTRM tail check
                  else: 
                    meas_type="LT-T-I" # trm acquisition experiment
                    MagRec["treatment_dc_field"]='%8.3e' % (float(treat[1])*1e-6) # labfield in tesla (convert from microT)
                MagRec["measurement_magn_moment"]='%10.3e'% (float(rec[10])*1e-3) # moment in Am^2 (from emu)
                MagRec["measurement_dec"]=rec[6]
                MagRec["measurement_inc"]=rec[7]
                MagRec["magic_instrument_codes"]=instcode
                MagRec["er_citation_names"]=citation
                MagRec["magic_method_codes"]=meas_type
                MagRec["measurement_flag"]='g'
                MagRec["measurement_standard"]='u'
                MagRec["measurement_number"]='1'
                MagRecs.append(MagRec) 
            else:
                print 'skipping: ',rec[0]
    MagOuts=pmag.measurements_methods(MagRecs,noave)
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print "results put in ",meas_file
main()
