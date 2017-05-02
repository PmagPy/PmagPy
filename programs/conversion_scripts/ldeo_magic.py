#!/usr/bin/env python
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
    -ID: directory for input file if not included in -f flag
    -f FILE: specify  input file, required
    -mv (m or v): specify if the final value in the measurement data is volume or mass (default: v)
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output file, default is magic_measurements.txt
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt # LORI
    -Flo FILE: specify output locations.txt file, default is locations.txt
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
    -loc LOCNAME : specify location
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
from __future__ import division
from __future__ import print_function
from builtins import range
from past.utils import old_div
import sys,os
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb

def convert(**kwargs):
    # initialize some stuff
    dec=[315,225,180,135,45,90,270,270,270,90,180,180,0,0,0]
    inc=[0,0,0,0,0,-45,-45,0,45,45,45,-45,-90,-45,45]
    tdec=[0,90,0,180,270,0,0,90,0]
    tinc=[0,0,90,0,0,-90,0,0,90]
    demag="N"
    trm=0
    irm=0

    user = kwargs.get('user', '')
    dir_path = kwargs.get('dir_path', '.')
    input_dir_path = kwargs.get('input_dir_path', dir_path)
    output_dir_path = dir_path
    meas_file = kwargs.get('meas_file', 'measurements.txt')
    spec_file = kwargs.get('spec_file', 'specimens.txt') # specimen outfile
    samp_file = kwargs.get('samp_file', 'samples.txt')
    site_file = kwargs.get('site_file', 'sites.txt') # site outfile
    loc_file = kwargs.get('loc_file', 'locations.txt') # site outfile
    magfile = kwargs.get('magfile', '')
    labfield = int(kwargs.get('labfield', 0)) *1e-6
    phi = int(kwargs.get('phi', 0))
    theta = int(kwargs.get('theta', 0))
    peakfield = int(kwargs.get('peakfield', 0))*1e-3
    specnum = int(kwargs.get('specnum', 0))
    location = kwargs.get('location', 'unknown')
    noave = kwargs.get('noave', False) # 0 means "do average", is default
    samp_con = kwargs.get('samp_con', '1')
    codelist = kwargs.get('codelist', '')
    coil = kwargs.get('coil', '')
    arm_labfield = kwargs.get('arm_labfield', 50e-6)
    trm_peakT = kwargs.get('trm_peakT', 600+273)
    mv = kwargs.get('mv', 'v')

    # format/organize variables
    if magfile:
        try:
            infile=open(os.path.join(input_dir_path,magfile),'r')
        except IOError:
            print("bad mag file name")
            return False, "bad mag file name"
    else:
        print("mag_file field is required option")
        return False, "mag_file field is required option"

    if specnum!=0:specnum=-specnum

    if "4" in samp_con:
        if "-" not in samp_con:
            print("naming convention option [4] must be in form 4-Z where Z is an integer")
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            Z=samp_con.split("-")[1]
            samp_con="4"
    elif "7" in samp_con:
        if "-" not in samp_con:
            print("naming convention option [7] must be in form 7-Z where Z is an integer")
            return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
        else:
            Z=samp_con.split("-")[1]
            samp_con="4"
    else: Z=1

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
            print('not a valid coil specification')
            return False, 'not a valid coil specification'

    if demag=="T" and "ANI" in codes:
        methcode="LP-AN-TRM"
    if demag=="AF" and "ANI" in codes:
        methcode="LP-AN-ARM"
        if labfield==0: labfield=50e-6
        if peakfield==0: peakfield=.180
    MeasRecs,SpecRecs,SampRecs,SiteRecs,LocRecs=[],[],[],[],[]
    version_num=pmag.get_version()
    # find start of data:
    DIspec=[]
    Data=infile.readlines()
    infile.close()
    for k in range(len(Data)):
        rec=Data[k].split()
        if len(rec)<=2: continue
        if rec[0].upper()=="LAT:" and len(rec)>3: lat,lon=rec[1],rec[3]; continue
        elif rec[0].upper()=="ID": continue
        MeasRec,SpecRec,SampRec,SiteRec,LocRec={},{},{},{},{}
        specimen=rec[0]
        if specnum!=0:
            sample=specimen[:specnum]
        else:
            sample=specimen
        site=pmag.parse_site(sample,samp_con,Z)
        if mv=='v':
            volume = float(rec[12])
            if volume > 0: susc_chi_volume='%10.3e'%(old_div((float(rec[11])*1e-5),volume)) #convert to SI (assume Bartington, 10-5 SI)
            else: susc_chi_volume='%10.3e'%(float(rec[11])*1e-5) #convert to SI (assume Bartington, 10-5 SI)
        else:
            mass = float(rec[12])
            if mass > 0: susc_chi_mass='%10.3e'%(old_div((float(rec[11])*1e-5),mass)) #convert to SI (assume Bartington, 10-5 SI)
            else: susc_chi_mass='%10.3e'%(float(rec[11])*1e-5) #convert to SI (assume Bartington, 10-5 SI)
        print((specimen,sample,site,samp_con,Z))

        #fill tables besides measurements
        if specimen!="" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
            SpecRec['specimen'] = specimen
            SpecRec['sample'] = sample
            if mv=='v':
                SpecRec["susc_chi_volume"]=susc_chi_volume
                SpecRec["volume"]=volume
            else:
                SpecRec["susc_chi_mass"]=susc_chi_mass
                SpecRec["mass"]=mass
            SpecRecs.append(SpecRec)
        if sample!="" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
            SampRec['sample'] = sample
            SampRec['site'] = site
            SampRecs.append(SampRec)
        if site!="" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
            SiteRec['site'] = site
            SiteRec['location'] = location
            SiteRec['lat'] = lat
            SiteRec['lon'] = lon
            SiteRecs.append(SiteRec)
        if location!="" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
            LocRec['location']=location
            LocRec['lat_n'] = lat
            LocRec['lon_e'] = lon
            LocRec['lat_s'] = lat
            LocRec['lon_w'] = lon
            LocRecs.append(LocRec)

        #fill measurements
        MeasRec["treat_temp"]='%8.3e' % (273) # room temp in kelvin
        MeasRec["meas_temp"]='%8.3e' % (273) # room temp in kelvin
        MeasRec["treat_ac_field"]='0'
        MeasRec["treat_dc_field"]='0'
        MeasRec["treat_dc_field_phi"]='0'
        MeasRec["treat_dc_field_theta"]='0'
        meas_type="LT-NO"
        MeasRec["quality"]='g'
        MeasRec["standard"]='u'
        MeasRec["treat_step_num"]='1'
        MeasRec["specimen"]=specimen
#        if mv=='v': MeasRec["susc_chi_volume"]=susc_chi_volume
#        else: MeasRec["susc_chi_mass"]=susc_chi_mass
        MeasRec["dir_csd"]=rec[3]
        MeasRec["magn_moment"]='%10.3e'% (float(rec[4])*1e-7)
        MeasRec["dir_dec"]=rec[5]
        MeasRec["dir_inc"]=rec[6]
        MeasRec["citations"]="This study"
        if demag=="AF":
            if methcode != "LP-AN-ARM":
                MeasRec["treat_ac_field"]='%8.3e' %(float(rec[1])*1e-3) # peak field in tesla
                meas_type="LT-AF-Z"
                MeasRec["treat_dc_field"]='0'
            else: # AARM experiment
                if treat[1][0]=='0':
                    meas_type="LT-AF-Z"
                    MeasRec["treat_ac_field"]='%8.3e' %(peakfield) # peak field in tesla
                else:
                    meas_type="LT-AF-I"
                    ipos=int(treat[0])-1
                    MeasRec["treat_dc_field_phi"]='%7.1f' %(dec[ipos])
                    MeasRec["treat_dc_field_theta"]='%7.1f'% (inc[ipos])
                    MeasRec["treat_dc_field"]='%8.3e'%(labfield)
                    MeasRec["treat_ac_field"]='%8.3e' %(peakfield) # peak field in tesla
        elif demag=="T":
            if rec[1][0]==".":rec[1]="0"+rec[1]
            treat=rec[1].split('.')
            if len(treat)==1:treat.append('0')
            MeasRec["treat_temp"]='%8.3e' % (float(rec[1])+273.) # temp in kelvin
            meas_type="LT-T-Z"
            MeasRec["treat_temp"]='%8.3e' % (float(treat[0])+273.) # temp in kelvin
            if trm==0:  # demag=T and not trmaq
                if treat[1][0]=='0':
                    meas_type="LT-T-Z"
                else:
                    MeasRec["treat_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                    MeasRec["treat_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                    MeasRec["treat_dc_field_theta"]='%7.1f' % (theta) # labfield theta
                    if treat[1][0]=='1':meas_type="LT-T-I" # in-field thermal step
                    if treat[1][0]=='2':
                        meas_type="LT-PTRM-I" # pTRM check
                        pTRM=1
                    if treat[1][0]=='3':
                        MeasRec["treat_dc_field"]='0'  # this is a zero field step
                        meas_type="LT-PTRM-MD" # pTRM tail check
            else:
                meas_type="LT-T-I" # trm acquisition experiment
        MeasRec['method_codes']=meas_type
        MeasRecs.append(MeasRec)

    con = nb.Contribution(output_dir_path,read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts=pmag.measurements_methods3(MeasRecs,noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.tables['specimens'].write_magic_file(custom_name=spec_file)
    con.tables['samples'].write_magic_file(custom_name=samp_file)
    con.tables['sites'].write_magic_file(custom_name=site_file)
    con.tables['locations'].write_magic_file(custom_name=loc_file)
    con.tables['measurements'].write_magic_file(custom_name=meas_file)

    return True, meas_file

def do_help():
    return __doc__

def main():
    kwargs = {}
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if "-usr" in sys.argv:
        ind=sys.argv.index("-usr")
        kwargs['user']=sys.argv[ind+1]
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        kwargs['dir_path'] = sys.argv[ind+1]
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwargs['input_dir_path'] = sys.argv[ind+1]
    if '-F' in sys.argv:
        ind = sys.argv.index("-F")
        kwargs['meas_file'] = sys.argv[ind+1]
    if '-Fsp' in sys.argv:
        ind=sys.argv.index("-Fsp")
        kwargs['spec_file']=sys.argv[ind+1]
    if '-Fsa' in sys.argv:
        ind = sys.argv.index("-Fsa")
        kwargs['samp_file'] = sys.argv[ind+1]
    if '-Fsi' in sys.argv: # LORI addition
        ind=sys.argv.index("-Fsi")
        kwargs['site_file']=sys.argv[ind+1]
    if '-Flo' in sys.argv: # Kevin addition
        ind=sys.argv.index("-Flo")
        kwargs['loc_file']=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        kwargs['magfile']=sys.argv[ind+1]
    if "-dc" in sys.argv:
        ind=sys.argv.index("-dc")
        kwargs['labfield']=float(sys.argv[ind+1])
        kwargs['phi']=float(sys.argv[ind+2])
        kwargs['theta']=float(sys.argv[ind+3])
    if "-ac" in sys.argv:
        ind=sys.argv.index("-ac")
        kwargs['peakfield']=sys.argv[ind+1]
    if "-spc" in sys.argv:
        ind=sys.argv.index("-spc")
        kwargs['specnum']=int(sys.argv[ind+1])
    if "-loc" in sys.argv:
        ind=sys.argv.index("-loc")
        kwargs['location']=sys.argv[ind+1]
    if "-A" in sys.argv: kwargs['noave']=True
    if "-ncn" in sys.argv:
        ind=sys.argv.index("-ncn")
        kwargs['samp_con']=sys.argv[ind+1]
    if '-LP' in sys.argv:
        ind=sys.argv.index("-LP")
        kwargs['codelist']=sys.argv[ind+1]
    if "-V" in sys.argv:
        ind=sys.argv.index("-V")
        kwargs['coil']=sys.argv[ind+1]
    if '-ARM_dc' in sys.argv:
        ind = sys.argv.index("-ARM_dc")
        kwargs['arm_labfield'] = sys.argv[ind+1]
    if '-ARM_temp' in sys.argv:
        ind = sys.argv.index('-ARM_temp')
        kwargs['trm_peakT'] = sys.argv[ind+1]
    if '-mv' in sys.argv:
        ind = sys.argv.index('-mv')
        kwargs['mv'] = sys.argv[ind+1]

    convert(**kwargs)

if __name__ == '__main__':
    main()
