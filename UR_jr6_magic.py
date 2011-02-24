#!/usr/bin/env python
import pmag,sys,os
def main():
    """
    NAME
        UR_jr6_magic.py
 
    DESCRIPTION
        converts University of Rome JR6 format files to magic_measurements format files

    SYNTAX
        UR_jr6_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -F FILE: specify output  measurements file, default is magic_measurements.txt
        -Fsa FILE: specify output er_samples.txt file for appending, default is er_samples.txt
        -dc B PHI THETA: dc lab field (in micro tesla) and phi,theta, default is none
              NB: use PHI, THETA = -1 -1 to signal that it changes, i.e. in anisotropy experiment
        -ac B : peak AF field (in mT) for ARM acquisition, default is none
        -A : don't average replicate measurements
        -spc NUM : specify number of characters to designate a  specimen, default = 0
        -loc LOCNAME : specify location/study name, must have either LOCNAME or SAMPFILE or be a synthetic
        -mcd: specify sampling method codes as a colon delimited string:  [default is: FS-FD:SO-POM:SO-SUN]
             FS-FD field sampling done with a drill
             FS-H field sampling done with hand samples
             FS-LOC-GPS  field location done with GPS
             FS-LOC-MAP  field location done with map
             SO-POM   a Pomeroy orientation device was used 
             SO-SUN   orientations are from a sun compass
             SO-MAG   orientations are from a magnetic compass
             SO-MAG-CMD   orientations declination corrected magnetic compass
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

            [8] synthetic - has no site name
            [9] ODP naming convention


    INPUT
        Put data from separate experiments (all AF, thermal, thellier, trm aquisition, Shaw, etc.)  in separate directory

    """
#        
#
    version_num=pmag.get_version()
    er_location_name=""
    ErSpecs,ErSamps,ErSites,ErLocs,ErCits=[],[],[],[],[]
    MagRecs=[]
    citation="This study"
    dir_path,demag='.','NRM'
    args=sys.argv
    noave=0
    specnum=0
    sampmeths='FS-FD:SO-POM:SO-SUN'
    samp_con,Z="4","2"
    if '-WD' in args:
        ind=args.index("-WD")
        dir_path=args[ind+1]
    meas_file=dir_path+'/'+'magic_measurements.txt'
    samp_file=dir_path+'/'+'er_samples.txt'
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-A" in args: noave=1
    if '-F' in args:
        ind=args.index("-F")
        meas_file=dir_path+'/'+args[ind+1]
    if '-Fsa' in args:
        ind=args.index("-Fsa")
        samp_file=dir_path+'/'+args[ind+1]
        ErSamps,file_type=pmag.magic_read(samp_file)
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
    if "-mcd" in args:
        ind=args.index("-mcd")
        sampmeths=(sys.argv[ind+1])
    if "-loc" in args:
        ind=args.index("-loc")
        er_location_name=args[ind+1]
    if "-spc" in args:
        ind=args.index("-spc")
        specnum=int(args[ind+1])
        if specnum!=0:specnum=-specnum
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
        if "S" in codes: 
            demag="S"
            methcode="LP-PI-TRM:LP-PI-ALT-AFARM"
            trm_labfield=labfield
            ans=raw_input("DC lab field for ARM step: [50uT] ")
            if ans=="":
                arm_labfield=50e-6
            else: 
                arm_labfield=float(ans)*1e-6
            ans=raw_input("temperature for total trm step: [600 C] ")
            if ans=="":
                trm_peakT=600+273 # convert to kelvin
            else: 
                trm_peakT=float(ans)+273 # convert to kelvin
        if "G" in codes: methcode="LT-AF-G"
	if "D" in codes: methcode="LT-AF-D"
        if "TRM" in codes: 
            demag="T"
            trm=1
    if demag=="T" and "ANI" in codes:
        methcode="LP-AN-TRM"
    if demag=="AF" and "ANI" in codes:
        methcode="LP-AN-ARM"
        if labfield==0: labfield=50e-6
        if peakfield==0: peakfield=.180
    filelist=os.listdir(dir_path) # read in list of files to import
    samples=[]
    MagRecs,SampRecs=[],[]
    for samp in ErSamps:
        if samp['er_sample_name'] not in samples:
            samples.append(samp['er_sample_name'])
            SampRecs.append(samp)
    for file in filelist: # parse each file
        parts=file.split('.')
        if parts[1].upper()=='JR6':
            print 'processing: ',file
            treatment_type,treatment_value,user="","",""
            inst="UR-JR6"
            input=open(dir_path+'/'+file,'rU').readlines()
            for line in input:
                newline=line.replace('-',' -')
                rec=newline.split()
                MagRec,SampRec={},{}
                specimen=rec[0]
                if specnum!=0:
                    SampRec['er_sample_name']=specimen[:specnum]
                else:
                    SampRec['er_sample_name']=specimen
                er_site_name=pmag.parse_site(SampRec['er_sample_name'],samp_con,Z)
                SampRec['er_site_name']=er_site_name
                SampRec['er_location_name']=er_location_name
                for key in SampRec.keys():MagRec[key]=SampRec[key]
                SampRec['sample_azimuth']=rec[7]
                SampRec['sample_dip']='-'+rec[8]
                SampRec['sample_bed_dip_direction']=rec[9]
                SampRec['sample_bed_dip']=rec[10]
                SampRec['magic_method_codes']=sampmeths
                MagRec['er_specimen_name']=specimen
                MagRec['er_analyst_mail_names']=user
                MagRec['magic_software_packages']=version_num
                MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
                MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
                MagRec["treatment_ac_field"]='0'
                MagRec["treatment_dc_field"]='0'
                MagRec["treatment_dc_field_phi"]='0'
                MagRec["treatment_dc_field_theta"]='0'
                MagRec["measurement_flag"]='g' # assume all data are "good"
                MagRec["measurement_standard"]='u' # assume all data are "good"
                MagRec["measurement_csd"]='' # set csd to blank
                MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
                MagRec['magic_method_codes']='LT-NO'
                if rec[2]=='C':
                    temp=float(rec[1])+273.     
                    if temp>298: 
                        MagRec["treatment_temp"]='%8.3e' % (temp) # room temp in kelvin
                        MagRec['magic_method_codes']='LT-T-Z'
                else: # measurement is in oe
                    AC=float(rec[1])*1e-4 # convert to tesla
                    if AC!=0.:
                        MagRec["treatment_ac_field"]='%8.3e' %(AC)
                        MagRec['magic_method_codes']='LT-AF-Z'
                vol=10.8*1e-6 # standard Roma lab volume
                MagRec['magic_instrument_codes']=inst
                MagRec['measurement_number']='1'
                mexp=10**(float(rec[6]))
                x,y,z=mexp*float(rec[3]),mexp*float(rec[4]),mexp*float(rec[5])
                Cart=[x,y,z]
                Dir=pmag.cart2dir(Cart)
                MagRec['measurement_dec']='%7.1f'%(Dir[0])
                MagRec['measurement_inc']='%7.1f'%(Dir[1])
                MagRec['measurement_magn_volume']='%8.3e'%(Dir[2])
                MagRec['measurement_magn_moment']='%8.3e'%(Dir[2]*vol)
                MagRec['measurement_description']='converted A/m to Am^2 using volume of '+str(vol)+' m^3'
                MagRecs.append(MagRec)
                if MagRec['er_sample_name'] not in samples:
                    samples.append(MagRec['er_sample_name'])
                    SampRecs.append(SampRec)
    if len(SampRecs)>0:
        SampOut,keys=pmag.fillkeys(SampRecs)
        pmag.magic_write(samp_file,SampOut,'er_samples')
        print 'samples stored in ',samp_file
    Fixed=pmag.measurements_methods(MagRecs,noave)
    pmag.magic_write(meas_file,Fixed,'magic_measurements')
    print 'data stored in ',meas_file
main()
