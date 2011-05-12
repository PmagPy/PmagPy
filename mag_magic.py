#!/usr/bin/env python
import string,sys,pmag
def main():
    """
    NAME
        mag_magic.py
 
    DESCRIPTION
        converts SIO .mag format files to magic_measurements format files

    SYNTAX
        mag_magic.py [command line options]

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
            S: Shaw method
            T: thermal including thellier but not trm acquisition
            N: NRM only
            TRM: trm acquisition
            ANI: anisotropy experiment
            D: double AF demag
            G: triple AF demag (GRM protocol)
        -spc NUM : specify number of characters to designate a  specimen, default = 0
        -loc LOCNAME : specify location/study name, must have either LOCNAME or SAMPFILE or be a synthetic
        -syn INST TYPE:  sets these specimens as synthetics created at institution INST and of type TYPE
        -ins INST : specify which demag instrument was used (e.g, SIO-Suzy or SIO-Odette),default is ""
        -dc B PHI THETA: dc lab field (in micro tesla) and phi,theta, default is none
              NB: use PHI, THETA = -1 -1 to signal that it changes, i.e. in anisotropy experiment
        -ac B : peak AF field (in mT) for ARM acquisition, default is none
        -FT [SIO,LDGO] : file type.  default is SIO (.mag file format)
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
    infile_type="mag"
    noave=0
    methcode,inst="",""
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
    methcode="LP-NO"
    fmt='old'
    syn=0
    synfile='er_synthetics.txt'
    samp_file,ErSamps='',[]
    trm=0
    irm=0
    specnum=0
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
    if '-FT' in args:
        ind=args.index("-FT")
        FT=args[ind+1]
        if FT=="LDGO":infile_type="ldgo" # default is "mag"
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
                samp_con="4"
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
    SynRecs,MagRecs=[],[]
    version_num=pmag.get_version()
    if infile_type=="mag":
        for line in input.readlines():
            instcode=""
            if len(line)>2:
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
                rec=line.split()
                if len(rec)>6:
                  code1=rec[6].split(';') # break e.g., 10/15/02;7:45 indo date and time
                  if len(code1)==2: # old format with AM/PM
                    missing=0
                    code2=code1[0].split('/') # break date into mon/day/year
                    code3=rec[7].split(';') # break e.g., AM;C34;200  into time;instr/axes/measuring pos;number of measurements
                    yy=int(code2[2])
                    if yy <90:
                        yyyy=str(2000+yy)
                    else: yyyy=str(1900+yy)
                    mm=int(code2[0])
                    if mm<10:
                        mm="0"+str(mm)
                    else: mm=str(mm)
                    dd=int(code2[1])
                    if dd<10:
                        dd="0"+str(dd)
                    else: dd=str(dd)
                    time=code1[1].split(':')
                    hh=int(time[0])
                    if code3[0]=="PM":hh=hh+12
                    if hh<10:
                        hh="0"+str(hh)
                    else: hh=str(hh)
                    min=int(time[1])
                    if min<10:
                       min= "0"+str(min)
                    else: min=str(min)
                    MagRec["measurement_date"]=yyyy+":"+mm+":"+dd+":"+hh+":"+min+":00.00"
                    MagRec["measurement_time_zone"]='SAN'
                    if inst=="":
                        if code3[1][0]=='C':instcode='SIO-bubba'
                        if code3[1][0]=='G':instcode='SIO-flo'
                    else:
                        instcode=''
                    MagRec["measurement_positions"]=code3[1][2]
                  elif len(code1)>2: # newest format (cryo7 or later)
                    labfield=0
                    fmt='new'
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
                    MagRec["measurement_time_zone"]='SAN'
                    if inst=="":
                        if code1[6][0]=='C':instcode='SIO-bubba'
                        if code1[6][0]=='G':instcode='SIO-flo'
                    else:
                        instcode=''
                    if len(code1)>1:
                        MagRec["measurement_positions"]=code1[6][2]
                    else:
                        MagRec["measurement_positions"]=code1[7]   # takes care of awkward format with bubba and flo being different
                    if user=="":user=code1[5]
                    if code1[2][-1]=='C': demag="T"
                    if code1[2]=='mT':
                        if methcode=="LP-IRM":
                            labfield=float(code1[3])*1e-3
                            if rec[1][0]!="-":
                                phi,theta=0.,90.
                            else:
                                phi,theta=0.,-90.
                            meas_type="LT-IRM"
                            MagRec["treatment_dc_field"]='%8.3e'%(labfield)
                            MagRec["treatment_dc_field_phi"]='%7.1f'%(phi)
                            MagRec["treatment_dc_field_theta"]='%7.1f'%(theta)
                        else:  
                            demag="AF"
                    labfield=float(code1[3])*1e-6
                    if code1[4]=='microT' and labfield!=0.:
                        phi,theta=0.,90.
                        if demag=="T": meas_type="LT-T-I"
                        if demag=="AF": meas_type="LT-AF-I"
                        MagRec["treatment_dc_field"]='%8.3e'%(labfield)
                        MagRec["treatment_dc_field_phi"]='%7.1f'%(phi)
                        MagRec["treatment_dc_field_theta"]='%7.1f'%(theta)
                    if code1[4]=='' or labfield==0.:
                        if demag=='T':meas_type="LT-T-Z"
                        if demag=="AF":meas_type="LT-AF-Z"
                        MagRec["treatment_dc_field"]='0'
                if syn==0:
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
                else:
                    if specnum!=0:
                        MagRec["er_sample_name"]=rec[0][:specnum]
                    else:
                        MagRec["er_sample_name"]=rec[0]
                    MagRec["er_site_name"]=""
                    MagRec["er_synthetic_name"]=MagRec["er_specimen_name"]
                    SynRec["er_synthetic_name"]=MagRec["er_specimen_name"]
                    site=pmag.parse_site(MagRec['er_sample_name'],samp_con,Z)
                    SynRec["synthetic_parent_sample"]=site
                    SynRec["er_citation_names"]="This study"
                    SynRec["synthetic_institution"]=institution
                    SynRec["synthetic_type"]=syntype
                    SynRecs.append(SynRec)
                if rec[1]==".00":rec[1]="0.00"
                treat=rec[1].split('.')
                if float(rec[1])==0:
                    pass 
                elif demag=="AF":
                    if methcode != "LP-AN-ARM":
                        MagRec["treatment_ac_field"]='%8.3e' %(float(rec[1])*1e-3) # peak field in tesla
                        meas_type="LT-AF-Z"
                        MagRec["treatment_dc_field"]='0'
                    else: # AARM experiment
                        if treat[1][0]=='0':
                            meas_type="LT-AF-Z"
                            MagRec["treatment_ac_field"]='%8.3e' %(peakfield) # peak field in tesla
                            MagRec["treatment_dc_field"]='%8.3e'%(0)
                            if labfield!=0: print "Warning - inconsistency in mag file with lab field - overriding file with 0"
                        else:
                            meas_type="LT-AF-I"
                            ipos=int(treat[0])-1
                            MagRec["treatment_dc_field_phi"]='%7.1f' %(dec[ipos])
                            MagRec["treatment_dc_field_theta"]='%7.1f'% (inc[ipos])
                            MagRec["treatment_dc_field"]='%8.3e'%(labfield)
                            MagRec["treatment_ac_field"]='%8.3e' %(peakfield) # peak field in tesla
                elif demag=="T" and methcode == "LP-AN-TRM":
                    if treat[1][0]=='0':
                            meas_type="LT-T-Z"
                            MagRec["treatment_dc_field"]='%8.3e'%(0)
                    else:
                            meas_type="LT-I-I"
                            ipos=int(treat[1][0])-1
                            MagRec["treatment_dc_field_phi"]='%7.1f' %(tdec[ipos])
                            MagRec["treatment_dc_field_theta"]='%7.1f'% (tinc[ipos])
                            MagRec["treatment_temp"]='%8.3e' % (float(treat[0])+273.) # temp in kelvin
                            MagRec["treatment_dc_field"]='%8.3e'%(labfield)
                elif demag=="S": # Shaw experiment
                    if treat[1][1]=='0':
                        if  int(treat[0])!=0:
                            MagRec["treatment_ac_field"]='%8.3e' % (float(treat[0])*1e-3) # AF field in tesla
                            MagRec["treatment_dc_field"]='0'
                            meas_type="LT-AF-Z" # first AF
                        else:
                            meas_type="LT-NO"
                            MagRec["treatment_ac_field"]='0'
                            MagRec["treatment_dc_field"]='0'
                    elif treat[1][1]=='1':
                        if int(treat[0])==0:
                            MagRec["treatment_ac_field"]='%8.3e' %(peakfield) # peak field in tesla
                            MagRec["treatment_dc_field"]='%8.3e'%(arm_labfield)
                            MagRec["treatment_dc_field_phi"]='%7.1f'%(phi)
                            MagRec["treatment_dc_field_theta"]='%7.1f'%(theta)
                            meas_type="LT-AF-I"
                        else:
                            MagRec["treatment_ac_field"]='%8.3e' % ( float(treat[0])*1e-3) # AF field in tesla
                            MagRec["treatment_dc_field"]='0'
                            meas_type="LT-AF-Z"
                    elif treat[1][1]=='2':
                        if int(treat[0])==0:
                            MagRec["treatment_ac_field"]='0'
                            MagRec["treatment_dc_field"]='%8.3e'%(trm_labfield)
                            MagRec["treatment_dc_field_phi"]='%7.1f'%(phi)
                            MagRec["treatment_dc_field_theta"]='%7.1f'%(theta)
                            MagRec["treatment_temp"]='%8.3e' % (trm_peakT)
                            meas_type="LT-T-I"
                        else:
                            MagRec["treatment_ac_field"]='%8.3e' % ( float(treat[0])*1e-3) # AF field in tesla
                            MagRec["treatment_dc_field"]='0'
                            meas_type="LT-AF-Z"
                    elif treat[1][1]=='3':
                        if int(treat[0])==0:
                            MagRec["treatment_ac_field"]='%8.3e' %(peakfield) # peak field in tesla
                            MagRec["treatment_dc_field"]='%8.3e'%(arm_labfield)
                            MagRec["treatment_dc_field_phi"]='%7.1f'%(phi)
                            MagRec["treatment_dc_field_theta"]='%7.1f'%(theta)
                            meas_type="LT-AF-I"
                        else:
                            MagRec["treatment_ac_field"]='%8.3e' % ( float(treat[0])*1e-3) # AF field in tesla
                            MagRec["treatment_dc_field"]='0'
                            meas_type="LT-AF-Z"
                else: 
                  if len(treat)==1:treat.append('0')
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
                    labfield=float(treat[1])*1e-6
                    MagRec["treatment_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                    MagRec["treatment_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                    MagRec["treatment_dc_field_theta"]='%7.1f' % (theta) # labfield theta
                    meas_type="LT-T-I:LP-TRM" # trm acquisition experiment
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
                if 'std' in rec[0]:
                    MagRec["measurement_standard"]='s'
                else:
                    MagRec["measurement_standard"]='u'
                MagRec["measurement_number"]='1'
                MagRec["er_specimen_name"],meas_type
                MagRecs.append(MagRec) 
    elif infile_type=="ldgo":
#
# find start of data:
#
        Samps=[] # keeps track of sample orientations
        DIspec=[]
        Data,k=input.readlines(),0
        for k in range(len(Data)):
            rec=Data[k].split()
            if rec[0][0]=="_" or rec[0][0:2]=="!_":
                break
        start=k+1
        for k in range(start,len(Data)):
          rec=Data[k].split()
          if len(rec)>0:
            MagRec={}
            MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["treatment_ac_field"]='0'
            MagRec["treatment_dc_field"]='0'
            MagRec["treatment_dc_field_phi"]='0'
            MagRec["treatment_dc_field_theta"]='0'
            meas_type="LT-NO"
            MagRec["measurement_flag"]='g'
            MagRec["measurement_standard"]='u'
            MagRec["measurement_number"]='1'
            MagRec["er_specimen_name"]=rec[0]
            if specnum!=0:
                MagRec["er_sample_name"]=rec[0][:specnum]
            else:
                MagRec["er_sample_name"]=rec[0]
            site=pmag.parse_site(MagRec['er_sample_name'],samp_con,Z)
            MagRec["er_site_name"]=site
            MagRec["er_site_name"]=MagRec['er_sample_name'][0:-2]
            MagRec["er_location_name"]=er_location_name
            MagRec["measurement_csd"]=rec[3]
            MagRec["measurement_magn_moment"]='%10.3e'% (float(rec[4])*1e-7) # moment in Am^2 (from 10^-4 emu)
#
            if samp_file!="" and MagRec["er_sample_name"] not in Samps:        # create er_samples.txt file with these data 
                cdec,cinc=float(rec[5]),float(rec[6])
                gdec,ginc=float(rec[7]),float(rec[8])
                az,pl=pmag.get_azpl(cdec,cinc,gdec,ginc)
                bdec,binc=float(rec[9]),float(rec[10])
                if rec[7]!=rec[9] and rec[6]!=rec[8]:
                    dipdir,dip=pmag.get_tilt(gdec,ginc,bdec,binc)
                else:
                    dipdir,dip=0,0
                ErSampRec={}
                ErSampRec['er_location_name']=MagRec['er_location_name']
                ErSampRec['er_sample_name']=MagRec['er_sample_name']
                ErSampRec['er_site_name']=MagRec['er_site_name']
                ErSampRec['sample_azimuth']='%7.1f'%(az)
                ErSampRec['sample_dip']='%7.1f'%(pl)
                ErSampRec['sample_bed_dip_direction']='%7.1f'%(dipdir)
                ErSampRec['sample_bed_dip']='%7.1f'%(dip)
                ErSampRec['sample_description']='az,pl,dip_dir and dip recalculated from [c,g,b][dec,inc] in ldeo file'
                ErSampRec['magic_method_codes']='SO-REC'
                ErSamps.append(ErSampRec)
                Samps.append(ErSampRec['er_sample_name'])
            MagRec["measurement_dec"]=rec[5]
            MagRec["measurement_inc"]=rec[6]
            MagRec["magic_instrument_codes"]=rec[2]
            MagRec["er_analyst_mail_names"]=""
            MagRec["er_citation_names"]="This study"
            MagRec["magic_method_codes"]=meas_type
            if demag=="AF":
                if methcode != "LP-AN-ARM":
                    MagRec["treatment_ac_field"]='%8.3e' %(float(rec[1])*1e-3) # peak field in tesla
                    meas_type="LT-AF-Z"
                    MagRec["treatment_dc_field"]='0'
                else: # AARM experiment
                    if treat[1][0]=='0':
                        meas_type="LT-AF-Z"
                        MagRec["treatment_ac_field"]='%8.3e' %(peakfield) # peak field in tesla
                    else:
                        meas_type="LT-AF-I"
                        ipos=int(treat[0])-1
                        MagRec["treatment_dc_field_phi"]='%7.1f' %(dec[ipos])
                        MagRec["treatment_dc_field_theta"]='%7.1f'% (inc[ipos])
                        MagRec["treatment_dc_field"]='%8.3e'%(labfield)
                        MagRec["treatment_ac_field"]='%8.3e' %(peakfield) # peak field in tesla
            elif demag=="T":
                if rec[1][0]==".":rec[1]="0"+rec[1]
                treat=rec[1].split('.')
                if len(treat)==1:treat.append('0')
                MagRec["treatment_temp"]='%8.3e' % (float(rec[1])+273.) # temp in kelvin
                meas_type="LT-T-Z"
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
            MagRec['magic_method_codes']=meas_type
            MagRecs.append(MagRec) 
    MagOuts=pmag.measurements_methods(MagRecs,noave)
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print "results put in ",meas_file
    if samp_file!="":
        pmag.magic_write(samp_file,ErSamps,'er_samples')
        print "sample orientations put in ",samp_file
    if len(SynRecs)>0:
        pmag.magic_write(synfile,SynRecs,'er_synthetics')
        print "synthetics put in ",synfile
main()
