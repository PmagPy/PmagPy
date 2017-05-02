#!/usr/bin/env python
"""
NAME
    iodp_jr6_magic.py

DESCRIPTION
    converts shipboard .jr6 format files to magic_measurements format files

SYNTAX
    iodp_jr6_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -ID: directory for input file if not included in -f flag
    -f FILE: specify input .csv file, default is all in directory
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -lat LAT: latitude of site (also used as bounding latitude for location)
    -lon LON: longitude of site (also used as bounding longitude for location)
    -exp EXPEDITION: specify expedition name (i.e. 312)
    -site HOLE: specify hole name (i.e. U1456A)
    -A: don't average replicate measurements
    -v NUM: volume in cm^3, will be used if there is no volume in the input data (default : 15.625 cm^3 or a 2.5 cm cube)

INPUT
    JR6 .jr6 format file
"""
from __future__ import print_function
from builtins import str
import sys, os
import numpy as np
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb

def fix_separation(filename, new_filename):
    old_file = open(filename, 'r')
    new_file = open(new_filename, 'w')
    data = old_file.readlines()
    for line in data:
        ldata=line.split()
        if len(ldata[0])>10: ldata.insert(1,ldata[0][10:]); ldata[0]=ldata[0][:10]
        ldata=[ldata[0]]+[d.replace('-', ' -') for d in ldata[1:]]
        new_line = ' '.join(ldata)+'\n'
        new_file.write(new_line)
    old_file.close()
    new_file.close()
    return new_filename

def convert(**kwargs):

    # initialize some stuff
    demag="N"
    version_num=pmag.get_version()

    dir_path = kwargs.get('dir_path', '.')
    input_dir_path = kwargs.get('input_dir_path', dir_path)
    output_dir_path = dir_path
    meas_file = kwargs.get('meas_file', 'measurements.txt')
    spec_file = kwargs.get('spec_file', 'specimens.txt')
    samp_file = kwargs.get('samp_file', 'samples.txt')
    site_file = kwargs.get('site_file', 'sites.txt')
    loc_file = kwargs.get('loc_file', 'locations.txt')
    mag_file = kwargs.get('mag_file', '')
    site = kwargs.get('site', 'unknown')
    expedition = kwargs.get('expedition', 'unknown')
    lat = kwargs.get('lat', '')
    lon = kwargs.get('lon', '')
    noave = kwargs.get('noave', False) # default means DO average
    meth_code = kwargs.get('meth_code', "LP-NO")
    volume = kwargs.get('volume', 2.5**3)*1e-6#default volume is a 2.5cm cube

    meth_code=meth_code+":FS-C-DRILL-IODP:SP-SS-C:SO-V"
    meth_code=meth_code.strip(":")
    mag_file = os.path.join(input_dir_path, mag_file)

    # validate variables
    if not os.path.exists(mag_file):
        print('The input file you provided: {} does not exist.\nMake sure you have specified the correct filename AND correct input directory name.'.format(mag_file))
        return False, 'The input file you provided: {} does not exist.\nMake sure you have specified the correct filename AND correct input directory name.'.format(mag_file)

    # parse data
    temp = os.path.join(output_dir_path, 'temp.txt')
    fix_separation(mag_file, temp)
    lines = open(temp, 'r').readlines()
    try: os.remove(temp)
    except OSError: print("problem with temp file")
    citations="This Study"
    MeasRecs,SpecRecs,SampRecs,SiteRecs,LocRecs=[],[],[],[],[]
    for line in lines:
        MeasRec,SpecRec,SampRec,SiteRec,LocRec={},{},{},{},{}
        line = line.split()
        spec_text_id = line[0]
        specimen = spec_text_id
        for dem in ['-','_']:
            if dem in spec_text_id:
                sample=dem.join(spec_text_id.split(dem)[:-1]); break
        location = expedition + site

        if specimen!="" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
            SpecRec['specimen'] = specimen
            SpecRec['sample'] = sample
            SpecRec['volume'] = volume
            SpecRec['citations']=citations
            SpecRecs.append(SpecRec)
        if sample!="" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
            SampRec['sample'] = sample
            SampRec['site'] = site
            SampRec['citations']=citations
            SampRec['azimuth']=line[6]
            SampRec['dip']=line[7]
            SampRec['bed_dip_direction']=line[8]
            SampRec['bed_dip']=line[9]
            SampRec['method_codes']=meth_code
            SampRecs.append(SampRec)
        if site!="" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
            SiteRec['site'] = site
            SiteRec['location'] = location
            SiteRec['citations']= citations
            SiteRec['lat'] = lat
            SiteRec['lon'] = lon
            SiteRecs.append(SiteRec)
        if location!="" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
            LocRec['location']=location
            LocRec['citations']=citations
            LocRec['expedition_name']=expedition
            LocRec['lat_n'] = lat
            LocRec['lon_e'] = lon
            LocRec['lat_s'] = lat
            LocRec['lon_w'] = lon
            LocRecs.append(LocRec)

        MeasRec['specimen']=specimen
        MeasRec["citations"]=citations
        MeasRec['software_packages']=version_num
        MeasRec["treat_temp"]='%8.3e' % (273) # room temp in kelvin
        MeasRec["meas_temp"]='%8.3e' % (273) # room temp in kelvin
        MeasRec["quality"]='g'
        MeasRec["standard"]='u'
        MeasRec["treat_step_num"]='1'
        MeasRec["treat_ac_field"]='0'

        x = float(line[4])
        y = float(line[3])
        negz = float(line[2])
        cart=np.array([x,y,-negz]).transpose()
        direction = pmag.cart2dir(cart).transpose()
        expon = float(line[5])
        magn_volume = direction[2] * (10.0**expon)
        moment = magn_volume * volume

        MeasRec["magn_moment"]=str(moment)
        MeasRec["magn_volume"]=str(magn_volume)#str(direction[2] * (10.0 ** expon))
        MeasRec["dir_dec"]='%7.1f'%(direction[0])
        MeasRec["dir_inc"]='%7.1f'%(direction[1])

        step = line[1]
        if step == 'NRM':
            meas_type="LT-NO"
        elif step[0:2] == 'AD':
            meas_type="LT-AF-Z"
            treat=float(step[2:])
            MeasRec["treat_ac_field"]='%8.3e' %(treat*1e-3) # convert from mT to tesla
        elif step[0:2] == 'TD':
            meas_type="LT-T-Z"
            treat=float(step[2:])
            MeasRec["treat_temp"]='%8.3e'%(treat+273.) # temp in kelvin
        elif step[0:3]=='ARM': #
            meas_type="LT-AF-I"
            treat=float(row['step'][3:])
            MeasRec["treat_ac_field"]='%8.3e' %(treat*1e-3) # convert from mT to tesla
            MeasRec["treat_dc_field"]='%8.3e' %(50e-6) # assume 50uT DC field
            MeasRec["measurement_description"]='Assumed DC field - actual unknown'
        elif step[0] == 'A':
            meas_type="LT-AF-Z"
            treat=float(step[1:])
            MeasRec["treat_ac_field"]='%8.3e' %(treat*1e-3) # convert from mT to tesla
        elif step[0] == 'T':
            meas_type="LT-T-Z"
            treat=float(step[1:])
            MeasRec["treat_temp"]='%8.3e' % (treat+273.) # temp in kelvin
        elif step[0:3]=='IRM': #
            meas_type="LT-IRM"
            treat=float(step[3:])
            MeasRec["treat_dc_field"]='%8.3e' %(treat*1e-3) # convert from mT to tesla
        else:
            print('unknown treatment type for ',row)
            return False, 'unknown treatment type for ',row

        MeasRec['method_codes']=meas_type
        MeasRecs.append(MeasRec.copy())

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

    return (True, meas_file)

def do_help():
    return __doc__

def main():
    kwargs={}
    # get command line arguments
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
        kwargs['meas_file']=sys.argv[ind+1]
    if '-Fsp' in sys.argv:
        ind=sys.argv.index("-Fsp")
        kwargs['spec_file'] = sys.argv[ind+1]
    if '-Fsa' in sys.argv:
        ind=sys.argv.index("-Fsa")
        kwargs['samp_file'] = sys.argv[ind+1]
    if '-Fsi' in sys.argv:
        ind=sys.argv.index("-Fsi")
        kwargs['site_file']=sys.argv[ind+1]
    if '-Flo' in sys.argv: # Kevin addition
        ind=sys.argv.index("-Flo")
        kwargs['loc_file']=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        kwargs['mag_file']= sys.argv[ind+1]
    if "-exp" in sys.argv:
        ind=sys.argv.index("-exp")
        kwargs['expedition']=sys.argv[ind+1]
    if "-site" in sys.argv:
        ind=sys.argv.index("-site")
        kwargs['site']=sys.argv[ind+1]
    if "-A" in sys.argv:
        kwargs['noave']=True
    if "-lat" in sys.argv:
        ind = sys.argv.index("-lat")
        kwargs['lat'] = sys.argv[ind+1]
    if "-lon" in sys.argv:
        ind = sys.argv.index("-lon")
        kwargs['lon'] = sys.argv[ind+1]
    if "-v" in sys.argv:
        ind=sys.argv.index("-v")
        kwargs['volume']=sys.argv[ind+1]

    convert(**kwargs)

if __name__ == '__main__':
    main()
