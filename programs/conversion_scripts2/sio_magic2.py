#!/usr/bin/env python
from __future__ import print_function
from builtins import input
from builtins import str
import sys
import pmagpy.pmag as pmag

def main(command_line=True, **kwargs):
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
        -fsa SAMPFILE : specify er_samples.txt file relating samples, site and locations names,default is none -- values in SAMPFILE will override selections for -loc (location), -spc (designate specimen), and -ncn (sample-site naming convention)
        -F FILE: specify output file, default is magic_measurements.txt
        -Fsy: specify er_synthetics file, default is er_sythetics.txt
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
            CR: cooling rate experiment.
                The treatment coding of the measurement file should be: XXX.00,XXX.10, XXX.20 ...XX.70 etc. (XXX.00 is optional)
                where XXX in the temperature and .10,.20... are running numbers of the cooling rates steps.
                XXX.00 is optional zerofield baseline. XXX.70 is alteration check.
                syntax in sio_magic is: -LP CR xxx,yyy,zzz,..... xxx -A
                where xxx, yyy, zzz...xxx  are cooling time in [K/minutes], seperated by comma, ordered at the same order as XXX.10,XXX.20 ...XX.70
                if you use a zerofield step then no need to specify the cooling rate for the zerofield
                It is important to add to the command line the -A option so the measurements will not be averaged.
                But users need to make sure that there are no duplicate measurements in the file
        -V [1,2,3] units of IRM field in volts using ASC coil #1,2 or 3
        -spc NUM : specify number of characters to designate a  specimen, default = 0
        -loc LOCNAME : specify location/study name, must have either LOCNAME or SAMPFILE or be a synthetic
        -syn INST TYPE:  sets these specimens as synthetics created at institution INST and of type TYPE
        -ins INST : specify which demag instrument was used (e.g, SIO-Suzy or SIO-Odette),default is ""
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
            [6] site is entered under a separate column NOT CURRENTLY SUPPORTED
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
                      (see Appendix to Lecture 13 - http://magician.ucsd.edu/Essentials_2)
              ATRM:
                X.00 optional baseline
                X.1 ATRM step (+X)
                X.2 ATRM step (+Y)
                X.3 ATRM step (+Z)
                X.4 ATRM step (-X)
                X.5 ATRM step (-Y)
                X.6 ATRM step (-Z)
                X.7 optional alteration check (+X)

              TRM:
                XXX.YYY  XXX is temperature step of total TRM
                         YYY is dc field in microtesla


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


    """
    # initialize some stuff
    mag_file = None
    codelist = None
    infile_type="mag"
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
    samp_infile,Samps='',[]
    trm=0
    irm=0
    specnum=0
    coil=""
    mag_file=""
#
# get command line arguments
#
    meas_file="magic_measurements.txt"
    user=""
    if not command_line:
        user = kwargs.get('user', '')
        meas_file = kwargs.get('meas_file', '')
        syn_file = kwargs.get('syn_file', '')
        mag_file = kwargs.get('mag_file', '')
        labfield = kwargs.get('labfield', '')
        if labfield:
            labfield = float(labfield) *1e-6
        else:
            labfield = 0
        phi = kwargs.get('phi', 0)
        if phi:
            phi = float(phi)
        else:
            phi = 0
        theta = kwargs.get('theta', 0)
        if theta:
            theta=float(theta)
        else:
            theta = 0
        peakfield = kwargs.get('peakfield', 0)
        if peakfield:
            peakfield=float(peakfield) *1e-3
        else:
            peakfield = 0
        specnum = kwargs.get('specnum', 0)
        samp_con = kwargs.get('samp_con', '1')
        er_location_name = kwargs.get('er_location_name', '')
        samp_infile = kwargs.get('samp_infile', '')
        syn = kwargs.get('syn', 0)
        institution = kwargs.get('institution', '')
        syntype = kwargs.get('syntype', '')
        inst = kwargs.get('inst', '')
        noave = kwargs.get('noave', 0)
        codelist = kwargs.get('codelist', '')
        coil = kwargs.get('coil', '')
        cooling_rates = kwargs.get('cooling_rates', '')
    if command_line:
        if "-h" in args:
            print(main.__doc__)
            return False
        if "-usr" in args:
            ind=args.index("-usr")
            user=args[ind+1]
        if '-F' in args:
            ind=args.index("-F")
            meas_file=args[ind+1]
        if '-Fsy' in args:
            ind=args.index("-Fsy")
            synfile=args[ind+1]
        if '-f' in args:
            ind=args.index("-f")
            mag_file=args[ind+1]
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
        if "-loc" in args:
            ind=args.index("-loc")
            er_location_name=args[ind+1]
        if "-fsa" in args:
            ind=args.index("-fsa")
            samp_infile = args[ind+1]
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
        if '-LP' in args:
            ind=args.index("-LP")
            codelist=args[ind+1]

        if "-V" in args:
            ind=args.index("-V")
            coil=args[ind+1]


    # make sure all initial values are correctly set up (whether they come from the command line or a GUI)
    if samp_infile:
        Samps, file_type = pmag.magic_read(samp_infile)
    if coil:
        coil = str(coil)
        methcode="LP-IRM"
        irmunits = "V"
        if coil not in ["1","2","3"]:
            print(main.__doc__)
            print('not a valid coil specification')
            return False, '{} is not a valid coil specification'.format(coil)
    if mag_file:
        try:
            #with open(mag_file,'r') as finput:
            #    lines = finput.readlines()
            lines=pmag.open_file(mag_file)
        except:
            print("bad mag file name")
            return False, "bad mag file name"
    if not mag_file:
        print(main.__doc__)
        print("mag_file field is required option")
        return False, "mag_file field is required option"
    if specnum!=0:
        specnum=-specnum
    #print 'samp_con:', samp_con
    if samp_con:
        if "4" == samp_con[0]:
            if "-" not in samp_con:
                print("naming convention option [4] must be in form 4-Z where Z is an integer")
                print('---------------')
                return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
            else:
                Z=samp_con.split("-")[1]
                samp_con="4"
        if "7" == samp_con[0]:
            if "-" not in samp_con:
                print("option [7] must be in form 7-Z where Z is an integer")
                return False, "option [7] must be in form 7-Z where Z is an integer"
            else:
                Z=samp_con.split("-")[1]
                samp_con="7"

    if codelist:
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
            irmunits="mT"
        if "I3d" in codes:
            methcode="LT-T-Z:LP-IRM-3D"
        if "S" in codes:
            demag="S"
            methcode="LP-PI-TRM:LP-PI-ALT-AFARM"
            trm_labfield=labfield
            ans=input("DC lab field for ARM step: [50uT] ")
            if ans=="":
                arm_labfield=50e-6
            else:
                arm_labfield=float(ans)*1e-6
            ans=input("temperature for total trm step: [600 C] ")
            if ans=="":
                trm_peakT=600+273 # convert to kelvin
            else:
                trm_peakT=float(ans)+273 # convert to kelvin
        if "G" in codes: methcode="LT-AF-G"
        if "D" in codes: methcode="LT-AF-D"
        if "TRM" in codes:
            demag="T"
            trm=1
        if "CR" in     codes:
            demag="T"
            cooling_rate_experiment=1
            if command_line:
                ind=args.index("CR")
                cooling_rates=args[ind+1]
                cooling_rates_list=cooling_rates.split(',')
            else:
                cooling_rates_list=str(cooling_rates).split(',')
    if demag=="T" and "ANI" in codes:
        methcode="LP-AN-TRM"
    if demag=="T" and "CR" in codes:
        methcode="LP-CR-TRM"
    if demag=="AF" and "ANI" in codes:
        methcode="LP-AN-ARM"
        if labfield==0: labfield=50e-6
        if peakfield==0: peakfield=.180
    SynRecs,MagRecs=[],[]
    version_num=pmag.get_version()


    ##################################

    if 1:
    #if infile_type=="SIO format":
        for line in lines:
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
                if rec[1]==".00":rec[1]="0.00"
                treat=rec[1].split('.')
                if methcode=="LP-IRM":
                    if irmunits=='mT':
                        labfield=float(treat[0])*1e-3
                    else:
                        labfield=pmag.getfield(irmunits,coil,treat[0])
                    if rec[1][0]!="-":
                        phi,theta=0.,90.
                    else:
                        phi,theta=0.,-90.
                    meas_type="LT-IRM"
                    MagRec["treatment_dc_field"]='%8.3e'%(labfield)
                    MagRec["treatment_dc_field_phi"]='%7.1f'%(phi)
                    MagRec["treatment_dc_field_theta"]='%7.1f'%(theta)
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
                    if "LP-AN-ARM" not in methcode:labfield=0
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
                    else:
                        min=str(min)
                    MagRec["measurement_date"]=yyyy+":"+mm+":"+dd+":"+hh+":"+min+":00.00"
                    MagRec["measurement_time_zone"]='SAN'
                    if inst=="":
                        if code1[6][0]=='C':
                            instcode='SIO-bubba'
                        if code1[6][0]=='G':
                            instcode='SIO-flo'
                    else:
                        instcode=''
                    if len(code1)>1:
                        MagRec["measurement_positions"]=code1[6][2]
                    else:
                        MagRec["measurement_positions"]=code1[7]   # takes care of awkward format with bubba and flo being different
                    if user=="":user=code1[5]
                    if code1[2][-1]=='C':
                        demag="T"
                        if code1[4]=='microT' and float(code1[3])!=0. and "LP-AN-ARM" not in methcode: labfield=float(code1[3])*1e-6
                    if code1[2]=='mT' and methcode!="LP-IRM":
                        demag="AF"
                        if code1[4]=='microT' and float(code1[3])!=0.: labfield=float(code1[3])*1e-6
                    if code1[4]=='microT' and labfield!=0. and meas_type!="LT-IRM":
                        phi,theta=0.,-90.
                        if demag=="T": meas_type="LT-T-I"
                        if demag=="AF": meas_type="LT-AF-I"
                        MagRec["treatment_dc_field"]='%8.3e'%(labfield)
                        MagRec["treatment_dc_field_phi"]='%7.1f'%(phi)
                        MagRec["treatment_dc_field_theta"]='%7.1f'%(theta)
                    if code1[4]=='' or labfield==0. and meas_type!="LT-IRM":
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
                    if samp_infile and Samps: # if samp_infile was provided AND yielded sample data
                        samp=pmag.get_dictitem(Samps,'er_sample_name',MagRec['er_sample_name'],'T')
                        if len(samp)>0:
                            MagRec["er_location_name"]=samp[0]["er_location_name"]
                            MagRec["er_site_name"]=samp[0]["er_site_name"]
                        else:
                            MagRec['er_location_name']=''
                            MagRec["er_site_name"]=''
                    elif int(samp_con)!=6:
                        site=pmag.parse_site(MagRec['er_sample_name'],samp_con,Z)
                        MagRec["er_site_name"]=site
                    if MagRec['er_site_name']=="":
                        print('No site name found for: ',MagRec['er_specimen_name'],MagRec['er_sample_name'])
                    if MagRec["er_location_name"]=="":
                        print('no location name for: ',MagRec["er_specimen_name"])
                else:
                    MagRec["er_specimen_name"]=rec[0]
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
                if float(rec[1])==0:
                    pass
                elif demag=="AF":
                    if methcode != "LP-AN-ARM":
                        MagRec["treatment_ac_field"]='%8.3e' %(float(rec[1])*1e-3) # peak field in tesla
                        if meas_type=="LT-AF-Z": MagRec["treatment_dc_field"]='0'
                    else: # AARM experiment
                        if treat[1][0]=='0':
                            meas_type="LT-AF-Z:LP-AN-ARM:"
                            MagRec["treatment_ac_field"]='%8.3e' %(peakfield) # peak field in tesla
                            MagRec["treatment_dc_field"]='%8.3e'%(0)
                            if labfield!=0 and methcode!="LP-AN-ARM": print("Warning - inconsistency in mag file with lab field - overriding file with 0")
                        else:
                            meas_type="LT-AF-I:LP-AN-ARM"
                            ipos=int(treat[0])-1
                            MagRec["treatment_dc_field_phi"]='%7.1f' %(dec[ipos])
                            MagRec["treatment_dc_field_theta"]='%7.1f'% (inc[ipos])
                            MagRec["treatment_dc_field"]='%8.3e'%(labfield)
                            MagRec["treatment_ac_field"]='%8.3e' %(peakfield) # peak field in tesla
                elif demag=="T" and methcode == "LP-AN-TRM":
                    MagRec["treatment_temp"]='%8.3e' % (float(treat[0])+273.) # temp in kelvin
                    if treat[1][0]=='0':
                        meas_type="LT-T-Z:LP-AN-TRM"
                        MagRec["treatment_dc_field"]='%8.3e'%(0)
                        MagRec["treatment_dc_field_phi"]='0'
                        MagRec["treatment_dc_field_theta"]='0'
                    else:
                        MagRec["treatment_dc_field"]='%8.3e'%(labfield)
                        if treat[1][0]=='7': # alteration check as final measurement
                                meas_type="LT-PTRM-I:LP-AN-TRM"
                        else:
                                meas_type="LT-T-I:LP-AN-TRM"

                        # find the direction of the lab field in two ways:
                        # (1) using the treatment coding (XX.1=+x, XX.2=+y, XX.3=+z, XX.4=-x, XX.5=-y, XX.6=-z)
                        ipos_code=int(treat[1][0])-1
                        # (2) using the magnetization
                        DEC=float(rec[4])
                        INC=float(rec[5])
                        if INC < 45 and INC > -45:
                            if DEC>315  or DEC<45: ipos_guess=0
                            if DEC>45 and DEC<135: ipos_guess=1
                            if DEC>135 and DEC<225: ipos_guess=3
                            if DEC>225 and DEC<315: ipos_guess=4
                        else:
                            if INC >45: ipos_guess=2
                            if INC <-45: ipos_guess=5
                        # prefer the guess over the code
                        ipos=ipos_guess
                        MagRec["treatment_dc_field_phi"]='%7.1f' %(tdec[ipos])
                        MagRec["treatment_dc_field_theta"]='%7.1f'% (tinc[ipos])
                        # check it
                        if ipos_guess!=ipos_code and treat[1][0]!='7':
                            print("-E- ERROR: check specimen %s step %s, ATRM measurements, coding does not match the direction of the lab field!"%(rec[0],".".join(list(treat))))


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


                # Cooling rate experient # added by rshaar
                elif demag=="T" and methcode == "LP-CR-TRM":

                    MagRec["treatment_temp"]='%8.3e' % (float(treat[0])+273.) # temp in kelvin
                    if treat[1][0]=='0':
                        meas_type="LT-T-Z:LP-CR-TRM"
                        MagRec["treatment_dc_field"]='%8.3e'%(0)
                        MagRec["treatment_dc_field_phi"]='0'
                        MagRec["treatment_dc_field_theta"]='0'
                    else:
                        MagRec["treatment_dc_field"]='%8.3e'%(labfield)
                        if treat[1][0]=='7': # alteration check as final measurement
                                meas_type="LT-PTRM-I:LP-CR-TRM"
                        else:
                                meas_type="LT-T-I:LP-CR-TRM"
                        MagRec["treatment_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                        MagRec["treatment_dc_field_theta"]='%7.1f' % (theta) # labfield theta

                        indx=int(treat[1][0])-1
                        # alteration check matjed as 0.7 in the measurement file
                        if indx==6:
                           cooling_time= cooling_rates_list[-1]
                        else:
                           cooling_time=cooling_rates_list[indx]
                        MagRec["measurement_description"]="cooling_rate"+":"+cooling_time+":"+"K/min"


                elif demag!='N':
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
                if "LP-IRM-3D" in methcode : meas_type=methcode
                #MagRec["magic_method_codes"]=methcode.strip(':')
                MagRec["magic_method_codes"]=meas_type
                MagRec["measurement_flag"]='g'
                MagRec["er_specimen_name"]=rec[0]
                if 'std' in rec[0]:
                    MagRec["measurement_standard"]='s'
                else:
                    MagRec["measurement_standard"]='u'
                MagRec["measurement_number"]='1'
                #print MagRec['treatment_temp']
                MagRecs.append(MagRec)
    MagOuts=pmag.measurements_methods(MagRecs,noave)
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print("results put in ",meas_file)
    if len(SynRecs)>0:
        pmag.magic_write(synfile,SynRecs,'er_synthetics')
        print("synthetics put in ",synfile)
    return True, meas_file

def do_help():
    return main.__doc__


if __name__ == "__main__":
    main()
