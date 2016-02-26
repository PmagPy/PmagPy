#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
        odp_spn_magic.py
 
    DESCRIPTION
        converts ODP's Molspin's .spn format files to magic_measurements format files

    SYNTAX
        odp_spn_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -f FILE: specify .spn format input file, required
        -F FILE: specify output file, default is magic_measurements.txt
        -LP [AF, T, A FIELD, I N] specify one (FIELD is DC field in uT) 
            AF:  af demag
            T: thermal 
            A: anhysteretic remanence 
            I: isothermal remanence 
            N: NRM only
        -v  vol , specify volume used in MolSpin program in cm^3
        -A: don't average replicate measurements
 
    INPUT
        Best to put separate experiments (all AF, thermal, ARM, etc. files in
           seperate .spn files 

        Format of  .spn files:   
        header with: 
       Leg Sit H Cor T Sec Top Bot      Dec     Inc     Intens   Demag. Stage
followed by data
        Leg: Expedition number 
        Sit: is ODP Site
        H: Hole letter 
        Cor: Core number
        T:  Core type (R,H,X,etc.)
        Sec: section number
        top:  top of sample interval
        bot: bottom of sample interval
        Intens in mA/m
        Demag Stage:
            XXX T in Centigrade
            XXX AF in mT
    """
# initialize some stuff
    noave=0
    methcode,inst="",""
    phi,theta,peakfield,labfield=0,0,0,0
    dec=[315,225,180,135,45,90,270,270,270,90,180,180,0,0,0]
    inc=[0,0,0,0,0,-45,-45,0,45,45,45,-45,-90,-45,45]
    missing=1
    demag="N"
    er_location_name=""
    citation='This study'
    args=sys.argv
    methcode="LP-NO"
    trm=0
    irm=0
    dc="0"
    dir_path='.'
#
# get command line arguments
#
    meas_file="magic_measurements.txt"
    user=""
    if "-WD" in args:
        ind=args.index("-WD")
        dir_path=args[ind+1]
    samp_file=dir_path+'/'+'er_samples.txt'
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if '-F' in args:
        ind=args.index("-F")
        meas_file=args[ind+1]
    if '-f' in args:
        ind=args.index("-f")
        mag_file=dir_path+'/'+args[ind+1]
        try:
            input=open(mag_file,'rU')
        except:
            print "bad mag file name"
            sys.exit()
    else: 
        print "spn_file field is required option"
        print main.__doc__
        sys.exit()
    vol=10.5e-6 # default for spinner program
    if "-V" in args:
        ind=args.index("-V")
        vol=float(args[ind+1])*1e-6 # convert volume to m^3
    if "-A" in args: noave=1
    if '-LP' in args:
        ind=args.index("-LP")
        codelist=args[ind+1]
        codes=codelist.split(':')
        if "AF" in codes:
            demag='AF' 
            methcode="LT-AF-Z"
        if "T" in codes:
            demag="T"
            methcode="LT-T-Z"
        if "I" in codes:
            methcode="LP-IRM"
        if "A" in codes:
            methcode="LT-AF-I"
            dc='%10.3e'%(1e-3*float(args[ind+1]))
    MagRecs=[]
    version_num=pmag.get_version()
    meas_file=dir_path+'/'+meas_file
    for line in input.readlines():
        instcode="ODP-MSPN"
        rec=line.split()
        if len(rec)>2 and "Leg" not in line:
            MagRec={}
            MagRec['er_expedition_name']=rec[0]
            MagRec['er_location_name']=rec[1]+rec[2]
            MagRec["er_specimen_name"]=rec[0]+'-'+'U'+rec[1]+rec[2].upper()+"-"+rec[3]+rec[4].upper()+'-'+rec[5]+'-'+'W'+'-'+rec[6]
            MagRec["er_site_name"]=MagRec['er_specimen_name']
            MagRec["er_sample_name"]=MagRec['er_specimen_name']
            MagRec['magic_software_packages']=version_num
            MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["treatment_ac_field"]='0'
            MagRec["treatment_dc_field"]=dc
            MagRec["treatment_dc_field_phi"]='0'
            MagRec["treatment_dc_field_theta"]='0'
            meas_type="LT-NO"
            if float(rec[11])==0:
                pass 
            elif demag=="AF":
                MagRec["treatment_ac_field"]='%8.3e' %(float(rec[11])*1e-3) # peak field in tesla
                meas_type="LT-AF-Z"
                MagRec["treatment_dc_field"]='0'
            else: 
              MagRec["treatment_temp"]='%8.3e' % (float(rec[11])+273.) # temp in kelvin
              meas_type="LT-T-Z"
            intens=1e-3*float(rec[10])*vol # convert mA/m to Am^2
            MagRec["measurement_magn_moment"]='%10.3e'% (intens)
            MagRec["measurement_dec"]=rec[8]
            MagRec["measurement_inc"]=rec[9]
            MagRec["magic_instrument_codes"]="ODP-MSPN"
            MagRec["er_analyst_mail_names"]=user
            MagRec["er_citation_names"]=citation
            MagRec["magic_method_codes"]=meas_type
            MagRec["measurement_flag"]='g'
	    MagRec["measurement_csd"]=''
            MagRec["measurement_number"]='1'
            MagRecs.append(MagRec) 
    MagOuts=pmag.measurements_methods(MagRecs,noave)
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print "results put in ",meas_file

if __name__ == "__main__":
    main()
