#!/usr/bin/env python
from __future__ import print_function
from builtins import range
import sys
import pmagpy.pmag as pmag

def main(command_line=True, **kwargs):
    """
    NAME
        ldeo_magic.py
 
    DESCRIPTION
        converts LDEO  format files to magic_measurements format files

    SYNTAX
        ldeo_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -usr USER:   identify user, default is ""
        -f FILE: specify .ldeo format input file, required
        -F FILE: specify output file, default is magic_measurements.txt
        -Fsy: specify er_synthetics file, default is er_sythetics.txt
        -LP [colon delimited list of protocols, include all that apply]
            AF:  af demag
            T: thermal including thellier but not trm acquisition
            S: Shaw method
            I: IRM (acquisition)
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

        -ARM_dc # default value is 50e-6
        -ARM_temp # default is 600c

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
 
            [8] synthetic - has no site name
    INPUT
        Best to put separate experiments (all AF, thermal, thellier, trm aquisition, Shaw, etc.) in 
           seperate .mag files (eg. af.mag, thermal.mag, etc.)

        Format of LDEO files:   
isaf2.fix       
LAT:   .00  LON:    .00
    ID     TREAT  I  CD    J    CDECL CINCL  GDECL GINCL  BDECL BINCL  SUSC  M/V
________________________________________________________________________________
is031c2       .0  SD  0 461.600 163.9  17.5  337.1  74.5  319.1  74.4    .0   .0
        
        ID: specimen name
        TREAT:  treatment step
        I:  Instrument 
        CD:  Circular standard devation
        J: intensity.  assumed to be total moment in 10^-4 (emu)
        CDECL:  Declination in specimen coordinate system
        CINCL:  Declination in specimen coordinate system
        GDECL:  Declination in geographic coordinate system
        GINCL:  Declination in geographic coordinate system
        BDECL:  Declination in bedding adjusted coordinate system
        BINCL:  Declination in bedding adjusted coordinate system
        SUSC:  magnetic susceptibility (in micro SI)a
        M/V: mass or volume for nomalizing (0 won't normalize)
     
    """
# initialize some stuff
    noave=0
    codelist = ''
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
    magfile = ''
    trm=0
    irm=0
    specnum=0
    coil=""
    arm_labfield = 50e-6
    trm_peakT = 600+273
    #
    # get command line arguments
    #

    meas_file="magic_measurements.txt"
    user=""
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
            magfile=args[ind+1]
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
        if '-ARM_dc' in args:
            ind = args.index("-ARM_dc")
            arm_labfield = args[ind+1]
        if '-ARM_temp' in args:
            ind = args.index('-ARM_temp')
            trm_peakT = args[ind+1]


    if not command_line:
        user = kwargs.get('user', '')
        meas_file = kwargs.get('meas_file', 'magic_measurements.txt')
        synfile = kwargs.get('synfile', 'er_synthetics.txt')
        # rm samp_file = kwargs.get('samp_file', '')
        magfile = kwargs.get('magfile', '')
        labfield = int(kwargs.get('labfield', 0)) *1e-6
        phi = int(kwargs.get('phi', 0))
        theta = int(kwargs.get('theta', 0))
        peakfield = int(kwargs.get('peakfield', 0))*1e-3
        specnum = int(kwargs.get('specnum', 0))
        er_location_name = kwargs.get('er_location_name', '')
        # rm samp_infile = kwargs.get('samp_infile', '')
        syn = kwargs.get('syn', 0)        
        institution = kwargs.get('institution', '')
        syntype = kwargs.get('syntype', '')
        inst = kwargs.get('inst', '')
        noave = kwargs.get('noave', 0) # 0 means "do average", is default
        samp_con = kwargs.get('samp_con', '1')
        codelist = kwargs.get('codelist', '')
        coil = kwargs.get('coil', '')
        arm_labfield = kwargs.get('arm_labfield', 50e-6)
        trm_peakT = kwargs.get('trm_peakT', 600+273)


    # format/organize variables
    if magfile:
        try:
            input=open(magfile,'r')
        except:
            print("bad mag file name")
            return False, "bad mag file name"
    else: 
        print("mag_file field is required option")
        print(main.__doc__)
        return False, "mag_file field is required option"
        
    if specnum!=0:specnum=-specnum

    if "4" in samp_con:
        if "-" not in samp_con:
            print("naming convention option [4] must be in form 4-Z where Z is an integer")
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            Z=samp_con.split("-")[1]
            samp_con="4"
    if "7" in samp_con:
        if "-" not in samp_con:
            print("naming convention option [7] must be in form 7-Z where Z is an integer")
            return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
        else:
            Z=samp_con.split("-")[1]
            samp_con="4"

    codes=codelist.split(':')
    if "AF" in codes:
        demag='AF' 
        if not labfield: methcode="LT-AF-Z"
        if labfield: methcode="LT-AF-I"
    if "T" in codes:
        demag="T"
        if not labfield: methcode="LT-T-Z"
        if labfield: methcode="LT-T-I"
    if "I" in codes:
        methcode="LP-IRM"
        irmunits="mT"
    if "S" in codes: 
        demag="S"
        methcode="LP-PI-TRM:LP-PI-ALT-AFARM"
        trm_labfield=labfield
        # should use arm_labfield and trm_peakT as well, but these values are currently never asked for
    if "G" in codes: methcode="LT-AF-G"
    if "D" in codes: methcode="LT-AF-D"
    if "TRM" in codes: 
        demag="T"
        trm=1

    if coil:
        methcode="LP-IRM"
        irmunits="V"
        if coil not in ["1","2","3"]:
            print(main.__doc__)
            print('not a valid coil specification')
            return False, 'not a valid coil specification'

    if demag=="T" and "ANI" in codes:
        methcode="LP-AN-TRM"
    if demag=="AF" and "ANI" in codes:
        methcode="LP-AN-ARM"
        if labfield==0: labfield=50e-6
        if peakfield==0: peakfield=.180
    SynRecs,MagRecs=[],[]
    version_num=pmag.get_version()
    if 1: # ldeo file format
#
# find start of data:
#
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
            MagRec["er_location_name"]=er_location_name
            MagRec["measurement_csd"]=rec[3]
            MagRec["measurement_magn_moment"]='%10.3e'% (float(rec[4])*1e-7) # moment in Am^2 (from 10^-4 emu)
#
            #if samp_file!="" and MagRec["er_sample_name"] not in Samps:        # create er_samples.txt file with these data 
            #    cdec,cinc=float(rec[5]),float(rec[6])
            #    gdec,ginc=float(rec[7]),float(rec[8])
            #    az,pl=pmag.get_azpl(cdec,cinc,gdec,ginc)
            #    bdec,binc=float(rec[9]),float(rec[10])
            #    if rec[7]!=rec[9] and rec[6]!=rec[8]:
            #        dipdir,dip=pmag.get_tilt(gdec,ginc,bdec,binc)
            #    else:
            #        dipdir,dip=0,0
            #    ErSampRec={}
            #    ErSampRec['er_location_name']=MagRec['er_location_name']
            #    ErSampRec['er_sample_name']=MagRec['er_sample_name']
            #    ErSampRec['er_site_name']=MagRec['er_site_name']
            #    ErSampRec['sample_azimuth']='%7.1f'%(az)
            #    ErSampRec['sample_dip']='%7.1f'%(pl)
            #    ErSampRec['sample_bed_dip_direction']='%7.1f'%(dipdir)
            #    ErSampRec['sample_bed_dip']='%7.1f'%(dip)
            #    ErSampRec['sample_description']='az,pl,dip_dir and dip recalculated from [c,g,b][dec,inc] in ldeo file'
            #    ErSampRec['magic_method_codes']='SO-REC'
            #    ErSamps.append(ErSampRec)
            #    Samps.append(ErSampRec['er_sample_name'])
            MagRec["measurement_dec"]=rec[5]
            MagRec["measurement_inc"]=rec[6]
            MagRec["measurement_chi"]='%10.3e'%(float(rec[11])*1e-5)#convert to SI (assume Bartington, 10-5 SI)
            #MagRec["magic_instrument_codes"]=rec[2]
            #MagRec["er_analyst_mail_names"]=""
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
    print("results put in ",meas_file)
    if len(SynRecs)>0:
        pmag.magic_write(synfile,SynRecs,'er_synthetics')
        print("synthetics put in ",synfile)
    return True, meas_file

def do_help():
    return main.__doc__

if __name__ == '__main__':
    main()
