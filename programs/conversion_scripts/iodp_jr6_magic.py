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
    -f FILE: specify  input file, or
    -F FILE: specify output file, default is magic_measurements.txt
    -loc HOLE : specify hole name (U1456A)
    -A: don't average replicate measurements

INPUT
    JR6 .jr6 format file
"""
import sys, os
import numpy as np
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb
from pandas import DataFrame

def fix_separation(filename, new_filename):
    old_file = open(filename, 'rU')
    data = old_file.readlines()
    new_data = []
    for line in data:
        new_line = line.replace('-', ' -')
        new_line = new_line.replace('  ', ' ')
        new_data.append(new_line)
    new_file = open(new_filename, 'w')
    for s in new_data:
        new_file.write(s)
    old_file.close()
    new_file.close()
    return new_filename

def old_fix_separation(filename, new_filename):
    old_file = open(filename, 'rU')
    data = old_file.readlines()
    new_data = []
    for line in data:
        new_line = []
        for i in line.split():
            if '-' in i[1:]:
                lead_char = '-' if i[0] == '-' else ''
                if lead_char:
                    v = i[1:].split('-')
                else:
                    v = i.split('-')
                new_line.append(lead_char + v[0])
                new_line.append('-' + v[1])
            else:
                new_line.append(i)
        new_line = (' '.join(new_line)) + '\n'
        new_data.append(new_line)
    new_file = open(new_filename, 'w')
    for s in new_data:
        new_file.write(s)
    new_file.close()
    old_file.close()
    return new_filename

def main(**kwargs):

    # initialize some stuff
    demag="N"
    version_num=pmag.get_version()

    dir_path = kwsys.argv.get('dir_path', '.')
    input_dir_path = kwsys.argv.get('input_dir_path', dir_path)
    output_dir_path = dir_path
    meas_file = kwsys.argv.get('meas_file', 'magic_measurements.txt')
    mag_file = kwsys.argv.get('mag_file', '')
    specnum = kwsys.argv.get('specnum', 1)
    samp_con = kwsys.argv.get('samp_con', '1')
    location = kwsys.argv.get('location', 'unknown')
    noave = kwsys.argv.get('noave', False) # default means DO average
    meth_code = kwsys.argv.get('meth_code', "LP-NO")
    volume = kwsys.argv.get('volume', 2.5**3)#default volume is a 2.5cm cube

    # format variables
    if specnum!=0:
        specnum=-specnum
    if "4" in samp_con:
        if "-" not in samp_con:
            print "option [4] must be in form 4-Z where Z is an integer"
            return False, "option [4] must be in form 4-Z where Z is an integer"
        else:
            Z=int(samp_con.split("-")[1])
            samp_con="4"
    if "7" in samp_con:
        if "-" not in samp_con:
            print "option [7] must be in form 7-Z where Z is an integer"
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z=int(samp_con.split("-")[1])
            samp_con="7"
    else: Z=1

    meth_code=meth_code+":FS-C-DRILL-IODP:SP-SS-C:SO-V"
    meth_code=meth_code.strip(":")
    mag_file = os.path.join(input_dir_path, mag_file)

    # validate variables
    if not os.path.exists(mag_file):
        print 'The input file you provided: {} does not exist.\nMake sure you have specified the correct filename AND correct input directory name.'.format(mag_file)
        return False, 'The input file you provided: {} does not exist.\nMake sure you have specified the correct filename AND correct input directory name.'.format(mag_file)

    # parse data
    temp = os.path.join(output_dir_path, 'temp.txt')
    fix_separation(mag_file, temp)
    samples,filetype = pmag.magic_read(samp_file)
    lines = open(temp, 'rU').readlines()
    os.remove(temp)
    MeasRecs,SpecRecs,SampRecs,SiteRecs,LocRecs=[],[],[],[],[]
    for line in lines:
        MeasRec,SpecRec,SampRec,SiteRec,LocRec={},{},{},{},{}
        line = line.split()
        spec_text_id = line[0].split('_')[1]

        if specimen!="" and specimen not in map(lambda x: x['specimen'] if 'specimen' in x.keys() else "", SpecRecs):
            SpecRec['specimen'] = specimen
            SpecRec['sample'] = sample
            SpecRec['citations']=citation
            SpecRec['specimen_alternatives']=InRec[text_id]
            SpecRecs.append(SpecRec)
        if sample!="" and sample not in map(lambda x: x['sample'] if 'sample' in x.keys() else "", SampRecs):
            SampRec['sample'] = sample
            SampRec['site'] = site
            SampRec['citations']=citation
            SampRec['azimuth']='0'
            SampRec['dip']='0'
            SampRec['core_depth']=InRec[depth_key]
            if comp_depth_key!='':
                SampRec['composite_depth']=InRec[comp_depth_key]
            if "SHLF" not in InRec[text_id]:
                SampRec['method_codes']='FS-C-DRILL-IODP:SP-SS-C:SO-V'
            else:
                SampRec['method_codes']='FS-C-DRILL-IODP:SO-V'
            SampRecs.append(SampRec)
        if site!="" and site not in map(lambda x: x['site'] if 'site' in x.keys() else "", SiteRecs):
            SiteRec['site'] = site
            SiteRec['location'] = location
            SiteRec['citations']=citation
            SiteRec['lat'] = lat
            SiteRec['lon'] = lon
            SiteRecs.append(SiteRec)
        if location!="" and location not in map(lambda x: x['location'] if 'location' in x.keys() else "", LocRecs):
            LocRec['location']=location
            LocRec['citations']=citation
            LocRec['expedition_name']=expedition
            LocRec['lat_n'] = lat
            LocRec['lon_e'] = lon
            LocRec['lat_s'] = lat
            LocRec['lon_w'] = lon
            LocRecs.append(LocRec)

        MeasRec['er_sample_name']=MeasRec['er_specimen_name']
        MeasRec["er_citation_names"]="This study"
        MeasRec['magic_software_packages']=version_num
        MeasRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
        MeasRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
        MeasRec["measurement_flag"]='g'
        MeasRec["measurement_standard"]='u'
        MeasRec["measurement_number"]='1'
        MeasRec["treatment_ac_field"]='0'

        volume=float(SampRecs[0]['sample_volume'])
        x = float(line[4])
        y = float(line[3])
        negz = float(line[2])
        cart=np.array([x,y,-negz]).transpose()
        direction = pmag.cart2dir(cart).transpose()
        expon = float(line[5])
        magn_volume = direction[2] * (10.0**expon)
        moment = magn_volume * volume

        MeasRec["measurement_magn_moment"]=str(moment)
        MeasRec["measurement_magn_volume"]=str(magn_volume)#str(direction[2] * (10.0 ** expon))
        MeasRec["measurement_dec"]='%7.1f'%(direction[0])
        MeasRec["measurement_inc"]='%7.1f'%(direction[1])

        step = line[1]
        if step == 'NRM':
            meas_type="LT-NO"
        elif step[0:2] == 'AD':
            meas_type="LT-AF-Z"
            treat=float(step[2:])
            MeasRec["treatment_ac_field"]='%8.3e' %(treat*1e-3) # convert from mT to tesla
        elif step[0:2] == 'TD':
            meas_type="LT-T-Z"
            treat=float(step[2:])
            MeasRec["treatment_temp"]='%8.3e' % (treat+273.) # temp in kelvin
        elif step[0:3]=='ARM': #
            meas_type="LT-AF-I"
            treat=float(row['step'][3:])
            MeasRec["treatment_ac_field"]='%8.3e' %(treat*1e-3) # convert from mT to tesla
            MeasRec["treatment_dc_field"]='%8.3e' %(50e-6) # assume 50uT DC field
            MeasRec["measurement_description"]='Assumed DC field - actual unknown'
        elif step[0:3]=='IRM': #
            meas_type="LT-IRM"
            treat=float(step[3:])
            MeasRec["treatment_dc_field"]='%8.3e' %(treat*1e-3) # convert from mT to tesla
        else:
            print 'unknown treatment type for ',row
            return False, 'unknown treatment type for ',row

        MeasRec['magic_method_codes']=meas_type
        MeasRecs.append(MeasRec.copy())

    MagOuts=pmag.measurements_methods(MeasRecs,noave)
    file_created, error_message = pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    if file_created:
        return True, meas_file
    else:
        return False, 'Results not written to file'


if __name__ == '__main__':
    kwsys.argv={}
    # get command line arguments
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        kwsys.argv['dir_path']=sys.argv[ind+1]
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwsys.argv['input_dir_path'] = sys.argv[ind+1]
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if '-F' in sys.argv:
        ind=sys.argv.index("-F")
        kwsys.argv['meas_file'] = sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        kwsys.argv['mag_file']= sys.argv[ind+1]
    if "-loc" in sys.argv:
        ind=sys.argv.index("-loc")
        kwsys.argv['location']=sys.argv[ind+1]
    if "-A" in sys.argv:
        kwsys.argv['noave']=True
    if "-v" in sys.argv:
        ind=sys.argv.index("-v")
        kwsys.argv['volume']=sys.argv[ind+1]

    main(**kwsys.argv)
