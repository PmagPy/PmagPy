#!/usr/bin/env python
"""
NAME
    pmd_magic.py

DESCRIPTION
    converts PMD (Enkin)  format files to magic_measurements format files

SYNTAX
    pmd_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -ID: directory for input file if not included in -f flag
    -f FILE: specify infile file, required
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt # LORI
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -spc NUM : specify number of characters to designate a  specimen, default = 1
    -loc LOCNAME : specify location/study name
    -A: don't average replicate measurements
    -ncn NCON: specify naming convention
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
    -lat: Lattitude of site (if no value given assumes 0)
    -lon: Longitude of site (if no value given assumes 0)
    -mcd [SO-MAG,SO-SUN,SO-SIGHT...] supply how these samples were oriented


        NB: all others you will have to customize your self
             or e-mail ltauxe@ucsd.edu for help.

INPUT
    PMD format files
"""
from __future__ import print_function
from builtins import range
import os,sys
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb

def convert(**kwargs):
    """

    """

    #get kwargs
    dir_path = kwargs.get('dir_path', '.')
    input_dir_path = kwargs.get('input_dir_path', dir_path)
    output_dir_path = dir_path
    meas_file = kwargs.get('meas_file', 'measurements.txt')
    mag_file = kwargs.get('mag_file')
    spec_file = kwargs.get('spec_file', 'specimens.txt')
    samp_file = kwargs.get('samp_file', 'samples.txt')
    site_file = kwargs.get('site_file', 'sites.txt')
    loc_file = kwargs.get('loc_file', 'locations.txt')
    lat = kwargs.get('lat', 0)
    lon = kwargs.get('lon', 0)
    specnum = int(kwargs.get('specnum', 0))
    samp_con = kwargs.get('samp_con', '1')
    location = kwargs.get('location', 'unknown')
    noave = kwargs.get('noave', 0) # default (0) means DO average
    meth_code = kwargs.get('meth_code', "LP-NO")
    version_num=pmag.get_version()

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
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
        else:
            Z=samp_con.split("-")[1]
            samp_con="7"
    else: Z = 1

    # format variables
    mag_file = os.path.join(input_dir_path,mag_file)
    meas_file = os.path.join(output_dir_path,meas_file)
    spec_file = os.path.join(output_dir_path,spec_file)
    samp_file = os.path.join(output_dir_path,samp_file)
    site_file = os.path.join(output_dir_path,site_file)

    # parse data
    data=open(mag_file,'r').readlines() # read in data from file
    comment=data[0]
    line=data[1].strip()
    line=line.replace("=","= ")  # make finding orientations easier
    rec=line.split() # read in sample orientation, etc.
    specimen=rec[0]
    SpecRecs,SampRecs,SiteRecs,LocRecs,MeasRecs = [],[],[],[],[]
    SpecRec,SampRec,SiteRec,LocRec={},{},{},{} # make a  sample record
    if specnum!=0:
        sample=rec[0][:specnum]
    else:
        sample=rec[0]
    if int(samp_con)<6:
        site=pmag.parse_site(sample,samp_con,Z)
    else:
        if 'site' in list(SampRec.keys()):site=ErSampREc['site']
        if 'location' in list(SampRec.keys()):location=ErSampREc['location']
    az_ind=rec.index('a=')+1
    SampRec['sample']=sample
    SampRec['description']=comment
    SampRec['azimuth']=rec[az_ind]
    dip_ind=rec.index('b=')+1
    dip=-float(rec[dip_ind])
    SampRec['dip']='%7.1f'%(dip)
    strike_ind=rec.index('s=')+1
    SampRec['bed_dip_direction']='%7.1f'%(float(rec[strike_ind])+90.)
    bd_ind=rec.index('d=')+1
    SampRec['bed_dip']=rec[bd_ind]
    v_ind=rec.index('v=')+1
    vol=rec[v_ind][:-3]
    date=rec[-2]
    time=rec[-1]
    SampRec['method_codes']=meth_code
    SampRec['site']=site
    SampRec['citations']='This study'
    SampRec['method_codes']='SO-NO'

    SpecRec['specimen'] = specimen
    SpecRec['sample'] = sample
    SpecRec['citations']='This study'

    SiteRec['site'] = site
    SiteRec['location'] = location
    SiteRec['citations']='This study'
    SiteRec['lat'] = lat
    SiteRec['lon']= lon

    LocRec['location'] = location
    LocRec['citations']='This study'
    LocRec['lat_n'] = lat
    LocRec['lat_s'] = lat
    LocRec['lon_e'] = lon
    LocRec['lon_w'] = lon

    SpecRecs.append(SpecRec)
    SampRecs.append(SampRec)
    SiteRecs.append(SiteRec)
    LocRecs.append(LocRec)
    for k in range(3,len(data)): # read in data
      line=data[k]
      rec=line.split()
      if len(rec)>1: # skip blank lines at bottom
        MeasRec={}
        MeasRec['description']='Date: '+date+' '+time
        MeasRec["citations"]="This study"
        MeasRec['software_packages']=version_num
        MeasRec["treat_temp"]='%8.3e' % (273) # room temp in kelvin
        MeasRec["meas_temp"]='%8.3e' % (273) # room temp in kelvin
        MeasRec["quality"]='g'
        MeasRec["standard"]='u'
        MeasRec["treat_step_num"]='1'
        MeasRec["specimen"]=specimen
        if rec[0]=='NRM':
            meas_type="LT-NO"
        elif rec[0][0]=='M' or rec[0][0]=='H':
            meas_type="LT-AF-Z"
        elif rec[0][0]=='T':
            meas_type="LT-T-Z"
        else:
            print("measurement type unknown")
            return False, "measurement type unknown"
        X=[float(rec[1]),float(rec[2]),float(rec[3])]
        Vec=pmag.cart2dir(X)
        MeasRec["magn_moment"]='%10.3e'% (Vec[2]) # Am^2
        MeasRec["magn_volume"]=rec[4] # A/m
        MeasRec["dir_dec"]='%7.1f'%(Vec[0])
        MeasRec["dir_inc"]='%7.1f'%(Vec[1])
        MeasRec["treat_ac_field"]='0'
        if meas_type!='LT-NO':
            treat=float(rec[0][1:])
        else:
            treat=0
        if meas_type=="LT-AF-Z":
            MeasRec["treat_ac_field"]='%8.3e' %(treat*1e-3) # convert from mT to tesla
        elif meas_type=="LT-T-Z":
            MeasRec["treat_temp"]='%8.3e' % (treat+273.) # temp in kelvin
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
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        kwargs['dir_path']=sys.argv[ind+1]
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwargs['input_dir_path'] = sys.argv[ind+1]
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if '-F' in sys.argv:
        ind=sys.argv.index("-F")
        kwargs['meas_file'] = sys.argv[ind+1]
    if '-Fsp' in sys.argv:
        ind=sys.argv.index("-Fsp")
        kwargs['spec_file']=sys.argv[ind+1]
    if '-Fsa' in sys.argv:
        ind = sys.argv.index("-Fsa")
        kwargs['samp_file'] = sys.argv[ind+1]
    if '-Fsi' in sys.argv:   # LORI addition
        ind=sys.argv.index("-Fsi")
        kwargs['site_file']=sys.argv[ind+1]
    if '-Flo' in sys.argv:
        ind=sys.argv.index("-Flo")
        kwargs['loc_file']=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        kwargs['mag_file']= sys.argv[ind+1]
    if "-spc" in sys.argv:
        ind = sys.argv.index("-spc")
        kwargs['specnum'] = sys.argv[ind+1]
    if "-ncn" in sys.argv:
        ind=sys.argv.index("-ncn")
        kwargs['samp_con']=sys.argv[ind+1]
    if "-loc" in sys.argv:
        ind=sys.argv.index("-loc")
        kwargs['location']=sys.argv[ind+1]
    if "-A" in sys.argv: kwargs['noave']=1
    if "-mcd" in sys.argv:
        ind=sys.argv.index("-mcd")
        kwargs['meth_code']=sys.argv[ind+1]
    if "-lat" in sys.argv:
        ind=sys.argv.index("-lat")
        kwargs['lat']=sys.argv[ind+1]
    if "-lon" in sys.argv:
        ind=sys.argv.index("-lon")
        kwargs['lon']=sys.argv[ind+1]

    convert(**kwargs)

if __name__ == "__main__":
    main()
