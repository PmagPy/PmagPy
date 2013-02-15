#!/usr/bin/env python
import string,sys,pmag
def main():
    """
    NAME
        sio_magic.py
 
    DESCRIPTION
        converts SIO .mag format files to magic_measurements format files

    SYNTAX
        sio_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -usr USER:   identify user, default is ""
        -f FILE: specify .mag format input file, required
        -fsa SAMPFILE : specify er_samples.txt file relating samples, site and locations names,default is none
        -F FILE: specify output file, default is magic_measurements.txt
        -Fsy: specify er_synthetics file, default is er_sythetics.txt
        -Fsa: specify output er_samples file, default is NONE (only for LDGO formatted files)
        -LP [colon delimited list of protocols, include all that apply]
            AF:  af demag
            T: thermal including thellier but not trm acquisition
            S: Shaw method
            I: IRM (acquisition)
            I3d: 3D IRM experiment
            N: NRM only
            TRM: trm acquisition
            ANI: anisotropy experiment
            D: double AF demag
            G: triple AF demag (GRM protocol)
        -V [1,2,3] units of IRM field in volts using ASC coil #1,2 or 3
        -spc NUM : specify number of characters to designate a  specimen, default = 0
        -loc LOCNAME : specify location/study name, must have either LOCNAME or SAMPFILE or be a synthetic
        -syn INST TYPE:  sets these specimens as synthetics created at institution INST and of type TYPE
        -ins INST : specify which demag instrument was used (e.g, SIO-Suzy or SIO-Odette),default is ""
        -dc B PHI THETA: dc lab field (in micro tesla) and phi,theta, default is none
              NB: use PHI, THETA = -1 -1 to signal that it changes, i.e. in anisotropy experiment
        -ac B : peak AF field (in mT) for ARM acquisition, default is none
        -nfcn NCON:  specify naming convention: default is #1 below
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
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.
 
            [8] synthetic - has no site name
            [9] ODP naming convention 
    INPUT
        Best to put separate experiments (all AF, thermal, thellier, trm aquisition, Shaw, etc.) in 
           seperate .mag files (eg. af.mag, thermal.mag, etc.)

        Format of SIO .mag files:   
        Spec Treat CSD Intensity Declination Inclination [optional metadata string]
        
        
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

              Shaw:
                XXX.YY   XXX is AF field
                    YY=00 is AF of NRM
                    YY=01 is AF of ARM1
                    YY=02 is AF of TRM
                    YY=03 is AF of ARM2
                specify temperature and field of Total TRM step on command line
         
         Intensity assumed to be total moment in 10^3 Am^2 (emu)
         Declination:  Declination in specimen coordinate system
         Inclination:  Declination in specimen coordinate system

         Optional metatdata string:  mm/dd/yy;hh:mm;[dC,mT];xx.xx;UNITS;USER;INST;NMEAS
             hh in 24 hours.  
             dC or mT units of treatment XXX (see Treat above) for thermal or AF respectively
             xx.xxx   DC field
             UNITS of DC field (microT, mT)
             INST:  instrument code, number of axes, number of positions (e.g., G34 is 2G, three axes, 
                    measured in four positions)
             NMEAS: number of measurements in a single position (1,3,200...)
       
      Format of LDGO files:   
        SPEC TREAT INST CSD Intensity CDECL CINCL [GDECL GINCL BDECL BINCL SUSC ]
     
    """
# initialize some stuff
    #infile_type="mag"
    noave=0
    methcode,inst="LP-NO",""
    phi,theta,peakfield,labfield=0,0,0,0
    pTRM,MD,samp_con,Z=0,0,'1',1
    dec=[315,225,180,135,45,90,270,270,270,90,180,180,0,0,0]
    inc=[0,0,0,0,0,-45,-45,0,45,45,45,-45,-90,-45,45]
    tdec=[0,90,0,180,270,0,0,90,0]
    tinc=[0,0,90,0,0,-90,0,0,90]
    missing=1
    demag="N"
    er_location_name=""
    citation='This study'
    args=sys.argv
    fmt='old'
    syn=0
    synfile='er_synthetics.txt'
    samp_file,ErSamps='',[]
    trm=0
    irm=0
    specnum=0
    coil=""
#
# get command line arguments
#
    meas_file="magic_measurements.txt"
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
    if '-Fsy' in args:
        ind=args.index("-Fsy")
        synfile=args[ind+1]
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
            print "bad mag file name"
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
    if "-fsa" in args:
        ind=args.index("-fsa")
        Samps,file_type=pmag.magic_read(args[ind+1])
    if '-syn' in args:
        syn=1
        ind=args.index("-syn")
        institution=args[ind+1]
        syntype=args[ind+2]
        if '-fsy' in args:
            ind=args.index("-fsy")
            synfile=args[ind+1]
    if "-ins" in args:
        ind=args.index("-ins")
        inst=args[ind+1]
    if "-A" in args: noave=1
    if "-ncn" in args:
        ind=args.index("-ncn")
        samp_con=sys.argv[ind+1]
        if "4" in samp_con:
            if "-" not in samp_con:
                print "option [4] must be in form 4-Z where Z is an integer"
                sys.exit()
            else:
                Z=int(samp_con.split("-")[1])
                samp_con="4"
        if "7" in samp_con:
            if "-" not in samp_con:
                print "option [7] must be in form 7-Z where Z is an integer"
                sys.exit()
            else:
                Z=int(samp_con.split("-")[1])
                samp_con="7"
                
    # lab process:
    if '-LP' in args:
        ind=args.index("-LP")
        codelist=args[ind+1]
        codes=codelist.split(':')
        if "AF" in codes:
            demag='AF' 
            #if'-dc' not in args: methcode="LT-AF-Z" #not supported yet
            #if'-dc' in args: methcode="LT-AF-I"  #not supported yet
        if "T" in codes:
            demag="T"
            if '-dc' not in args: methcode="LT-T-Z"
            if '-dc' in args: methcode="LT-T-I"
        if "TRM" in codes: 
            demag="T"
            trm=1
    if demag=="T" and "ANI" in codes:
        methcode="LP-AN-TRM"
        
##    if demag=="AF" and "ANI" in codes:
##        methcode="LP-AN-ARM"
##        if labfield==0: labfield=50e-6
##        if peakfield==0: peakfield=.180

    version_num=pmag.get_version()

    MagRecs=[]
    
    #--------------------------------------
    # Read the file
    #--------------------------------------

    for line in input.readlines():
        instcode=""
        if len(line)>2:
            rec=line.split()
            #print rec

            if rec[0][0]=='#': # HUJI way of marking bad data points
                continue
            specimen=rec[0]
            date=rec[2].split("/")
            hour=rec[3].split(":")
            treatment_type=rec[4]
            treatment=rec[5].split(".")
            dec=rec[6]
            inc=rec[7]
            dec_tilted=rec[8]
            inc_tilted=rec[9]
            moment_emu=float(rec[10])

            MagRec={}
            MagRec['er_location_name']=er_location_name
            MagRec['magic_software_packages']=version_num
            MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["treatment_ac_field"]='0'
            MagRec["treatment_dc_field"]='0'
            MagRec["treatment_dc_field_phi"]='0'
            MagRec["treatment_dc_field_theta"]='0'
            MagRec["er_specimen_name"]=specimen
            MagRec["measurement_magn_moment"]='%10.3e'% (moment_emu*1e-3) # moment in Am^2 (from emu)
            MagRec["measurement_dec"]=dec
            MagRec["measurement_inc"]=inc

            MagRec["measurement_csd"]=""
            MagRec["measurement_positions"]=""
            if specnum!=0:
                MagRec["er_sample_name"]=specimen[:specnum]
            else:
                MagRec["er_sample_name"]=rec[0]
            if samp_con=="1":
                MagRec["er_site_name"]=MagRec["er_sample_name"][:-1]
            elif samp_con=="2":
                MagRec["er_site_name"]=MagRec["er_sample_name"].split("-")[0]
            elif samp_con=="3":
                MagRec["er_site_name"]=MagRec["er_sample_name"].split(".")[0]
            # samp_con 4 to be done !
            elif samp_con=="4":
                MagRec["er_site_name"]=MagRec["er_sample_name"][:Z]
            elif samp_con=="5":
                MagRec["er_site_name"]=MagRec["er_sample_name"]
            elif samp_con=="6":
                MagRec["er_site_name"]=MagRec["er_sample_name"]              
            else:    
                MagRec["er_site_name"]=MagRec["er_sample_name"]  # site need to be done"

            if float(date[2])>80:
                yyyy="19"+date[2]
            else:
                yyyy="20"+date[2]
            MagRec["measurement_date"]=":".join([yyyy,date[0],date[1],hour[0],hour[1],"00.00"])
            MagRec["measurement_time_zone"]='JER'
            if treatment_type =="N":
                meas_type="LT-NO"
            if treatment_type =="A":
                demag="AF"
                #meas_type="LT-AF-I"
            if treatment_type =="T":
                demag="T"
                #meas_type="LT-T-I"


            #---------------------------------------
            # NRM
            #----------------------------------------


            #-LT-NO---------------------------------------
            # AF demag
            # So far support only AF demag
            # do not support AARM
            #----------------------------------------
            if demag=="AF":
                
                # demag in zero field
                if methcode != "LP-AN-ARM":                        
                    MagRec["treatment_ac_field"]='%8.3e' %(float(treatment[0])*1e-3) # peak field in tesla
                    MagRec["treatment_dc_field"]='0'
                    
                # AARM experiment    
                else:
                    print "Dont supprot AARM in HUJI format yet. sorry..."

            #----------------------------------------
            # Thermal demag and Thellier experiment
            # So far support only: "IZ", "ZI", "IZZI", pTRM checks
            # do not support AARM
            #----------------------------------------

            if demag=="T" in codes and "ANI" not in codes:
                if treatment[1]=='0' or  treatment[1]=='00':
                        #meas_type="LT-T-Z"
                        MagRec["treatment_dc_field"]='%8.3e'%(0)
                        MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin
                elif treatment[1]=='1' or  treatment[1]=='10':
                        #meas_type="LT-T-I"
                        MagRec["treatment_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                        MagRec["treatment_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                        MagRec["treatment_dc_field_theta"]='%7.1f' % (theta) # labfield theta
                        MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin
                        
                elif treatment[1]=='2' or  treatment[1]=='20':
                        #meas_type="LT-PTRM-I"
                        MagRec["treatment_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                        MagRec["treatment_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                        MagRec["treatment_dc_field_theta"]='%7.1f' % (theta) # labfield theta
                        MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin


            #----------------------------------------
            # ATRM measurements
            # The direction of the magnetization is used to determine the
            # direction of the field.
            #----------------------------------------


            if demag=="T" in codes and "ANI" in codes:
                    methcode="LP-AN-TRM"
                    if treatment[1]=='0' or treatment[1]=='00':
                            #meas_type="LT-T-Z"
                            MagRec["treatment_dc_field"]='%8.3e'%(0)
                            MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin
                    else:
                            inc=float(inc);dec=float(dec)
                            if abs(inc)<45 and (dec<45 or dec>315):
                                tdec,tinc=0,0
                            if abs(inc)<45 and (dec<135 and dec>45):
                                tdec,tinc=90,0
                            if inc>45 :
                                tdec,tinc=0,90
                            if abs(inc)<45 and (dec<225 and dec>135):
                                tdec,tinc=180,0
                            if abs(inc)<45 and (dec<315 and dec>225):
                                tdec,tinc=270,0
                            if inc<-45 :
                                tdec,tinc=0,-90
                            
                            MagRec["treatment_dc_field_phi"]='%7.1f' %(tdec)
                            MagRec["treatment_dc_field_theta"]='%7.1f'% (tinc)
                            MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin
                            MagRec["treatment_dc_field"]='%8.3e'%(labfield)

            #----------------------------------------
            # ATRM measurements
            # The direction of the magnetization is used to determine the
            # direction of the field.
            #----------------------------------------


            if "TRM" in codes:
                        
                labfield=float(treatment[1])*1e-6
                MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin                
                MagRec["treatment_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                MagRec["treatment_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                MagRec["treatment_dc_field_theta"]='%7.1f' % (theta) # labfield theta
                meas_type="LT-T-I:LP-TRM" # trm acquisition experiment


            MagRec["measurement_number"]='1'            
            MagRec["magic_method_codes"]=methcode.strip(':')
            MagRecs.append(MagRec)
    #print MagRecs
    #print len(MagRecs)
    MagOuts=pmag.measurements_methods(MagRecs,noave)
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print "results put in ",meas_file
    if samp_file!="":
        pmag.magic_write(samp_file,ErSamps,'er_samples')
        print "sample orientations put in ",samp_file
                
                    

main()
