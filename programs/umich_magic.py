#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
        umich_magic.py
 
    DESCRIPTION
        converts UMICH .mag format files to magic_measurements format files

    SYNTAX
        umich_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -usr USER:   identify user, default is ""
        -f FILE: specify .mag format input file, required
        -fsa SAMPFILE : specify er_samples.txt file relating samples, site and locations names,default is none
        -F FILE: specify output file, default is magic_measurements.txt
        -spc NUM : specify number of characters to designate a  specimen, default = 0
        -loc LOCNAME : specify location/study name, must have either LOCNAME or SAMPFILE or be a synthetic
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
            [6] site is entered under a separate column -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.
 
        Format of UMICH .mag files:   
        Spec Treat CSD Intensity Declination Inclination metadata string
        Spec: specimen name
        Treat:  treatment step
            XXX T in Centigrade
            XXX AF in mT
         Intensity assumed to be total moment in 10^3 Am^2 (emu)
         Declination:  Declination in specimen coordinate system
         Inclination:  Declination in specimen coordinate system

         metatdata string:  mm/dd/yy;hh:mm;[dC,mT];xx.xx;UNITS;USER;INST;NMEAS
             hh in 24 hours.  
             dC or mT units of treatment XXX (see Treat above) for thermal or AF respectively
             xx.xxx   DC field
             UNITS of DC field (microT, mT)
             INST:  instrument code, number of axes, number of positions (e.g., G34 is 2G, three axes, 
                    measured in four positions)
             NMEAS: number of measurements in a single position (1,3,200...)
    """
# initialize some stuff
    dir_path='.'
    infile_type="mag"
    noave=0
    methcode,inst="",""
    phi,theta,peakfield,labfield=0,0,0,0
    pTRM,MD,samp_con,Z=0,0,'1',1
    missing=1
    demag="N"
    er_location_name=""
    citation='This study'
    args=sys.argv
    methcode="LP-NO"
    samp_file,ErSamps='',[]
    specnum=0
#
# get command line arguments
#
    meas_file="magic_measurements.txt"
    user=""
    if '-WD' in args:
        ind=args.index("-WD")
        dir_path=args[ind+1]
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-usr" in args:
        ind=args.index("-usr")
        user=args[ind+1]
    if '-F' in args:
        ind=args.index("-F")
        meas_file=dir_path+'/'+args[ind+1]
    if '-f' in args:
        ind=args.index("-f")
        magfile=dir_path+'/'+args[ind+1]
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
    if "-fsa" in args:
        ind=args.index("-fsa")
        samp_file=dir_path+'/'+args[ind+1]
        Samps,file_type=pmag.magic_read(samp_file)
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
            samp_con=sys.argv[ind+1]
        if "7" in samp_con:
            if "-" not in samp_con:
                print "option [7] must be in form 7-Z where Z is an integer"
                sys.exit()
            else:
                Z=samp_con.split("-")[1]
                samp_con="7"
    MagRecs,specs=[],[]
    version_num=pmag.get_version()
    if infile_type=="mag":
        for line in input.readlines():
            instcode=""
            if len(line)>2:
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
                rec=line.split()
                labfield=0
                code1=rec[6].split(';')
                date=code1[0].split('/') # break date into mon/day/year
                yy=int(date[2])
                if yy <90:
                    yyyy=str(2000+yy)
                else: yyyy=str(1900+yy)
                mm=int(date[0])
                if mm<10:
                    mm="0"+str(mm)
                else: mm=str(mm)
                dd=int(date[1])
                if dd<10:
                    dd="0"+str(dd)
                else: dd=str(dd)
                time=code1[1].split(':')
                hh=int(time[0])
                if hh<10:
                    hh="0"+str(hh)
                else: hh=str(hh)
                min=int(time[1])
                if min<10:
                   min= "0"+str(min)
                else: min=str(min)
                MagRec["measurement_date"]=yyyy+":"+mm+":"+dd+":"+hh+":"+min+":00.00"
                MagRec["measurement_time_zone"]=''
                instcode=''
                if len(code1)>1:
                    MagRec["measurement_positions"]=code1[6][2]
                else:
                    MagRec["measurement_positions"]=code1[7]   # takes care of awkward format with bubba and flo being different
                if user=="":user=code1[5]
                if code1[2][-1]=='C': demag="T"
                if code1[2]=='mT': demag="AF"
                treat=rec[1].split('.')
                if len(treat)==1:treat.append('0')
                if demag=='T' and treat!=0:
                    meas_type="LT-T-Z"
                    MagRec["treatment_temp"]='%8.3e' % (float(treat[0])+273.) # temp in kelvin
                if demag=="AF":
                    meas_type="LT-AF-Z"
                    MagRec["treatment_ac_field"]='%8.3e' % (float(treat[0])*1e-3) # Af field in T
                MagRec["treatment_dc_field"]='0'
                MagRec["er_specimen_name"]=rec[0]
                if rec[0] not in specs:specs.append(rec[0]) # get a list of specimen names
                experiment=rec[0]+":"
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
                MagRec["measurement_csd"]=rec[2]
                MagRec["measurement_magn_moment"]='%10.3e'% (float(rec[3])*1e-3) # moment in Am^2 (from emu)
                MagRec["measurement_dec"]=rec[4]
                MagRec["measurement_inc"]=rec[5]
                MagRec["magic_instrument_codes"]=instcode
                MagRec["er_analyst_mail_names"]=user
                MagRec["er_citation_names"]=citation
                MagRec["magic_method_codes"]=meas_type
                MagRec["measurement_flag"]='g'
                MagRec["er_specimen_name"]=rec[0]
                MagRec["measurement_number"]='1'
                MagRecs.append(MagRec) 
    MagOuts=[]
    for spec in specs:  # gather all demag types for this specimen
        SpecRecs,meths,measnum=[],[],1
        for rec in MagRecs:
            if rec['er_specimen_name']==spec:
                rec['measurement_number']=str(measnum)
                measnum+=1
                if rec['magic_method_codes'] not in meths:meths.append(rec['magic_method_codes'])
                SpecRecs.append(rec)
        expname=spec
        if "LT-AF-Z" in meths:expname=expname+ ':LP-DIR-AF'
        if "LT-T-Z" in meths:expname=expname+ ':LP-DIR-T'
        for rec in SpecRecs:
            rec['magic_experiment_name']=expname
            MagOuts.append(rec)
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print "results put in ",meas_file
    
if __name__ == "__main__":
    main()
