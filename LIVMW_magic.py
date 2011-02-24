#!/usr/bin/env python
import string,sys,pmag

def main():
    """
    NAME
        LIVMW_magic.py
 
    DESCRIPTION
        converts Liverpool microwave format files to magic_measurements format files

    SYNTAX
        LIVMW_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -f FILE: specify liverpool format input file, required
        -usr USER:   identify user, default is ""
        -ins INST:   identify instrument, e.g., LIV-TRISTAN, LIV-OLD14GHZ, default is ""
        -loc LOCNAME : specify location/study name, required
        -F FILE: specify output file, default is magic_measurements.txt
        -Fsa FILE: specify er_samples formatted  file for appending, default is new er_samples.txt
        -spc NUM : specify number of characters to designate a  specimen, default = 1
        -sit Site_name : specify site name for this specimen
        -unc measurement units are uncalibrated (default is uAm^2)
        -B PHI THETA: dc lab field phi, theta, default is 0, 90
        -ncn NCON:  specify naming convention  - required if -sit not specified
       Sample naming convention:
            do not use if -sit option used!
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
 

    """
# initialize some stuff
    version_num=pmag.get_version()
    noave=0
    methcode,instcode="",""
    phi,theta,peakfield,labfield=0,0,0,0
    pMRM,MD,samp_con,Z,site=0,0,'6',"",""
    er_location_name=""
    citation='This study'
    args=sys.argv
    methcode="LP-NO" # NRM
    specnum,measnum=1,1
    powt_max=0
    ErSamps,Samps=[],[]
#
# get command line arguments
#
    dirpath='.'
    meas_file,samp_file=dirpath+"/magic_measurements.txt",dirpath+"/er_samples.txt"
    user=""
    unc=0
    if "-WD" in args:
        ind=args.index("-WD")
        dirpath=args[ind+1]
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-usr" in args:
        ind=args.index("-usr")
        user=args[ind+1]
    if "-ins" in args:
        ind=args.index("-ins")
        instcode=args[ind+1]
    if '-F' in args:
        ind=args.index("-F")
        meas_file=dirpath+'/'+args[ind+1]
    if '-Fsa' in args:
        ind=args.index("-Fsa")
        samp_file=args[ind+1]
        samp_file=dirpath+'/'+samp_file
        try:
            open(samp_file,'rU')
            ErSamps,file_type=pmag.magic_read(samp_file)
            print 'sample information will be appended to new er_samples.txt file'
        except:
            print 'er_samples.txt file does not exist'
            print 'sample information will be stored in new er_samples.txt file'
    if '-f' in args:
        ind=args.index("-f")
        magfile=args[ind+1]
        magfile=dirpath+'/'+magfile
        try:
            input=open(magfile,'rU')
        except:
            print "bad mag file name"
            sys.exit()
    else: 
        print "mag_file field is required option"
        print main.__doc__
        sys.exit()
    if "-B" in args:
        ind=args.index("-B")
        phi=args[ind+1]
        theta=args[ind+2]
    else:
        phi,theta='0.','90.'
    if "-spc" in args:
        ind=args.index("-spc")
        specnum=int(args[ind+1])
        if specnum!=0:specnum=-specnum
    if "-loc" in args:
        ind=args.index("-loc")
        er_location_name=args[ind+1]
    if "-unc" in args: unc=1
    if "-sit" in args:
        ind=args.index("-sit")
        site=args[ind+1]
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
    if samp_con=='6' and site=="":
        print "you must either specify a naming convention, or a site name"
        print main.__doc__
        sys.exit()
    MagRecs=[]
    if len(ErSamps)>1:
        for samp in ErSamps: 
            if samp['er_sample_name'] not in Samps: Samps.append(samp['er_sample_name'])
    Data=input.readlines()
    if 1:  # never mind
        for line in Data:
            if len(line)>1:
                rec=line.split(',')
                MagRec={}
                MagRec['er_citation_names']='This study'
                MagRec['er_location_name']=er_location_name
                MagRec['magic_software_packages']=version_num
                MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
                MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
                MagRec["treatment_ac_field"]='0'
                MagRec["treatment_dc_field"]='0'
                MagRec["treatment_dc_field_phi"]=''
                MagRec["treatment_dc_field_theta"]=''
                MagRec["treatment_mw_integral"]=""
                meas_type="LT-NO"
                MagRec["er_specimen_name"]=rec[0][1:-1]
                MagRec["er_location_name"]=er_location_name
                if specnum!=0:
                    MagRec["er_sample_name"]=rec[0][1:-1][:specnum]
                else:
                   MagRec["er_sample_name"]=rec[0][1:-1]
                if site=="": site=pmag.parse_site(MagRec['er_sample_name'],samp_con,Z)
                MagRec["er_site_name"]=site
                MagRec["treatment_mw_power"]=rec[2]
                MagRec["treatment_mw_time"]=rec[3]
                powt=int(float(MagRec["treatment_mw_power"])*(float(MagRec["treatment_mw_time"])))
                MagRec["treatment_mw_energy"]='%7.1f'%(powt)
                if powt>powt_max:powt_max=powt
                treat=rec[1].strip('"').upper()
                if treat=="Z":  #  in zero field
                        meas_type="LT-M-Z" #  as opposed to LT-MV-Z
                        if powt<powt_max: meas_type="LT-PMRM-Z"
                elif treat=="A":  #  in zero field
                        meas_type="LT-M-I" #  as opposed to LT-MV-I
                        labfield=float(rec[10])*1e-6 # assuming uT, convert to T
                        MagRec["treatment_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                        MagRec["treatment_dc_field_phi"]=phi # labfield phi
                        MagRec["treatment_dc_field_theta"]=theta # labfield theta
                        if powt<powt_max: meas_type="LT-PMRM-I"
                if len(rec)>10: MagRec["treatment_mw_integral"]=rec[10]
                if unc==0:MagRec["measurement_magn_moment"]='%10.3e'% (float(rec[4])*1e-6) # moment in Am^2 (from uAm^2)
                if unc==1:MagRec["measurement_magnitude"]=rec[4] # uncalibrated moment 
                cart=[]
                cart.append(float(rec[7])) 
                cart.append(float(rec[8])) 
                cart.append(float(rec[9])) 
                dir=pmag.cart2dir(cart)
                MagRec["measurement_dec"]='%9.3f'%(dir[0])
                MagRec["measurement_inc"]='%9.3f'%(dir[1])
                MagRec["magic_instrument_codes"]=instcode
                MagRec["magic_method_codes"]=meas_type
                MagRec["measurement_flag"]='g'
                MagRec["measurement_standard"]='u'
                MagRec["measurement_number"]='%i'%(measnum)
                MagRec["magic_experiment_name"]=MagRec['er_specimen_name']+":"+methcode
                measnum+=1
                MagRecs.append(MagRec) 
                if MagRec["er_sample_name"] not in Samps: # add this puppy to the list in er_samples.txt
                    Samps.append(MagRec["er_sample_name"])
                    ErSamp={}
                    ErSamp['er_sample_name']=Samps[-1]
                    ErSamp['er_location_name']=MagRec['er_location_name']
                    ErSamp['er_site_name']=site
                    ErSamp['er_citation_names']='This study'
                    gdec=float(rec[5])
                    ginc=float(rec[6])
                    az,pl=pmag.get_azpl(dir[0],dir[1],gdec,ginc)
                    ErSamp['sample_azimuth']='%7.1f'%az
                    ErSamp['sample_dip']='%7.1f'%pl
                    ErSamps.append(ErSamp)
    MagOuts=pmag.mw_measurements_methods(MagRecs)
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print "measurements put in ",meas_file
    pmag.magic_write(samp_file,ErSamps,'er_samples')
    print "sample names put in ",samp_file
main()
