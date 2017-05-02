#!/usr/bin/env python
"""
NAME
    bgc_magic.py

DESCRIPTION
    converts Berkeley Geochronology Center (BGC) format files to magic_measurements format files

SYNTAX
    bgc_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -usr USER: Colon delimited list of analysts, default is ""
    -ID: directory for input file if not included in -f flag
    -f FILE: specify .sam format input file, required
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt # LORI
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -spc NUM : specify number of characters to designate a specimen, default = 0
    -loc LOCNAME : specify location/study name
    -site SITENAME : specify site name (if site name can be generated from sample name see bellow conventions under the -ncn flag)
    -ncn NCON:  specify naming convention: default is #1 below
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
    -A: don't average replicate measurements
    -mcd [SO-MAG,SO-SUN,SO-SIGHT...] supply how these samples were oriented
    -v NUM : specify the volume in cc of the sample, default 2.5^3cc. Will use vol in data file if volume!=0 in file.
    -tz: timezone in pytz library format. list of timzones can be found at http://pytz.sourceforge.net/. (default: US/Pacific)

INPUT
    BGC paleomag format file
"""
from __future__ import division
from __future__ import print_function
from builtins import str
from past.utils import old_div
import sys, os
import numpy as np
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb
import pytz, datetime


def convert(**kwargs):
    version_num = pmag.get_version()

    user = kwargs.get('user', '')
    dir_path = kwargs.get('dir_path', '.')
    input_dir_path = kwargs.get('input_dir_path', dir_path)
    output_dir_path = dir_path
    meas_file = kwargs.get('meas_file', 'measurements.txt')
    spec_file = kwargs.get('spec_file', 'specimens.txt') # specimen outfile
    samp_file = kwargs.get('samp_file', 'samples.txt')
    site_file = kwargs.get('site_file', 'sites.txt') # site outfile
    loc_file = kwargs.get('loc_file', 'locations.txt') # Loc outfile
    mag_file = kwargs.get('mag_file') #required
    location = kwargs.get('location', 'unknown')
    site = kwargs.get('site', '')
    samp_con = kwargs.get('samp_con', '1')
    specnum = int(kwargs.get('specnum', 0))
    timezone = kwargs.get('timestamp', 'US/Pacific')
    noave = kwargs.get('noave', False) # default False means DO average
    meth_code = kwargs.get('meth_code', "LP-NO")
    volume = float(kwargs.get('volume', 0))
    if not volume: volume = 0.025**3 #default volume is a 2.5 cm cube, translated to meters cubed
    else: volume *= 1e-6 #convert cm^3 to m^3

    if specnum!=0:
        specnum=-specnum
    if "4" in samp_con:
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "option [4] must be in form 4-Z where Z is an integer"
        else:
            Z=int(samp_con.split("-")[1])
            samp_con="4"
    if "7" in samp_con:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z=int(samp_con.split("-")[1])
            samp_con="7"
    else: Z=1

    # format variables
    if not os.path.isfile(mag_file):
        print("%s is not a BGC file"%mag_file)
        return False, 'You must provide a BCG format file'
    mag_file = os.path.join(input_dir_path, mag_file)

    # Open up the BGC file and read the header information
    print('mag_file in bgc_magic', mag_file)
    pre_data = open(mag_file, 'r')
    line = pre_data.readline()
    line_items = line.split(' ')
    specimen = line_items[2]
    specimen = specimen.replace('\n', '')
    line = pre_data.readline()
    line = pre_data.readline()
    line_items = line.split('\t')
    azimuth = float(line_items[1])
    dip = float(line_items[2])
    bed_dip = line_items[3]
    sample_bed_azimuth = line_items[4]
    lon = line_items[5]
    lat = line_items[6]
    tmp_volume = line_items[7]
    if tmp_volume != 0.0:
        volume = float(tmp_volume) * 1e-6
    pre_data.close()

    data = pd.read_csv(mag_file, sep='\t', header=3, index_col=False)

    cart = np.array([data['X'], data['Y'], data['Z']]).transpose()
    direction = pmag.cart2dir(cart).transpose()

    data['dir_dec'] = direction[0]
    data['dir_inc'] = direction[1]
    data['magn_moment'] = old_div(direction[2], 1000)  # the data are in EMU - this converts to Am^2
    data['magn_volume'] = old_div((old_div(direction[2], 1000)), volume) # EMU  - data converted to A/m

    # Configure the magic_measurements table
    MeasRecs,SpecRecs,SampRecs,SiteRecs,LocRecs=[],[],[],[],[]
    for rowNum, row in data.iterrows():
        MeasRec,SpecRec,SampRec,SiteRec,LocRec = {},{},{},{},{}

        if specnum!=0:
            sample=specimen[:specnum]
        else:
            sample=specimen
        if site=='':
            site=pmag.parse_site(sample,samp_con,Z)

        if specimen!="" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
            SpecRec['specimen'] = specimen
            SpecRec['sample'] = sample
            SpecRec['volume'] = volume
            SpecRec['analysts']=user
            SpecRec['citations'] = 'This study'
            SpecRecs.append(SpecRec)
        if sample!="" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
            SampRec['sample'] = sample
            SampRec['site'] = site
            SampRec['azimuth'] = azimuth
            SampRec['dip'] = dip
            SampRec['bed_dip_direction'] = sample_bed_azimuth
            SampRec['bed_dip'] = bed_dip
            SampRec['method_codes'] = meth_code
            SampRec['analysts']=user
            SampRec['citations'] = 'This study'
            SampRecs.append(SampRec)
        if site!="" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
            SiteRec['site'] = site
            SiteRec['location'] = location
            SiteRec['lat'] = lat
            SiteRec['lon'] = lon
            SiteRec['analysts']=user
            SiteRec['citations'] = 'This study'
            SiteRecs.append(SiteRec)
        if location!="" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
            LocRec['location']=location
            LocRec['analysts']=user
            LocRec['citations'] = 'This study'
            LocRec['lat_n'] = lat
            LocRec['lon_e'] = lon
            LocRec['lat_s'] = lat
            LocRec['lon_w'] = lon
            LocRecs.append(LocRec)

        MeasRec['description'] = 'Date: ' + str(row['Date']) + ' Time: ' + str(row['Time'])
        if '.' in row['Date']: datelist = row['Date'].split('.')
        elif '/' in row['Date']: datelist = row['Date'].split('/')
        elif '-' in row['Date']: datelist = row['Date'].split('-')
        else: print("unrecogized date formating on one of the measurement entries for specimen %s"%specimen); datelist=['','','']
        if ':' in row['Time']: timelist = row['Time'].split(':')
        else: print("unrecogized time formating on one of the measurement entries for specimen %s"%specimen); timelist=['','','']
        datelist[2]='19'+datelist[2] if len(datelist[2])<=2 else datelist[2]
        dt=":".join([datelist[1],datelist[0],datelist[2],timelist[0],timelist[1],timelist[2]])
        local = pytz.timezone(timezone)
        naive = datetime.datetime.strptime(dt, "%m:%d:%Y:%H:%M:%S")
        local_dt = local.localize(naive, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        timestamp=utc_dt.strftime("%Y-%m-%dT%H:%M:%S")+"Z"
        MeasRec["timestamp"] = timestamp
        MeasRec["citations"] = "This study"
        MeasRec['software_packages'] = version_num
        MeasRec["treat_temp"] = '%8.3e' % (273) # room temp in kelvin
        MeasRec["meas_temp"] = '%8.3e' % (273) # room temp in kelvin
        MeasRec["quality"] = 'g'
        MeasRec["standard"] = 'u'
        MeasRec["treat_step_num"] = rowNum
        MeasRec["specimen"] = specimen
        MeasRec["treat_ac_field"] = '0'
        if row['DM Val'] == '0':
            meas_type = "LT-NO"
        elif int(row['DM Type']) > 0.0:
            meas_type = "LT-AF-Z"
            treat = float(row['DM Val'])
            MeasRec["treat_ac_field"] = '%8.3e' %(treat*1e-3) # convert from mT to tesla
        elif int(row['DM Type']) == -1:
            meas_type = "LT-T-Z"
            treat = float(row['DM Val'])
            MeasRec["treat_temp"] = '%8.3e' % (treat+273.) # temp in kelvin
        else:
            print("measurement type unknown:", row['DM Type'], " in row ", rowNum)
        MeasRec["magn_moment"] = str(row['magn_moment'])
        MeasRec["magn_volume"] = str(row['magn_volume'])
        MeasRec["dir_dec"] = str(row['dir_dec'])
        MeasRec["dir_inc"] = str(row['dir_inc'])
        MeasRec['method_codes'] = meas_type
        MeasRec['dir_csd'] = '0.0' # added due to magic.write error
        MeasRec['meas_n_orient'] = '1' # added due to magic.write error
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

    return True, meas_file

def do_help():
    return __doc__

def main():
    kwargs={}
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
        ind = sys.argv.index("-f")
        kwargs['mag_file'] = sys.argv[ind+1]
    if "-loc" in sys.argv:
        ind = sys.argv.index("-loc")
        kwargs['location'] = sys.argv[ind+1]
    if "-site" in sys.argv:
        ind = sys.argv.index("-site")
        kwargs['site'] = sys.argv[ind+1]
    if "-A" in sys.argv:
        kwargs['noave'] = True
    if "-mcd" in sys.argv:
        ind = sys.argv.index("-mcd")
        kwargs['meth_code'] = sys.argv[ind+1]
    if "-v" in sys.argv:
        ind = sys.argv.index("-v")
        kwargs['volume'] = sys.argv[ind+1] # enter volume in cc, convert to m^3
    if "-ncn" in sys.argv:
        ind=sys.argv.index("-ncn")
        kwargs['samp_con']=sys.argv[ind+1]
    if "-spc" in sys.argv:
        ind=sys.argv.index("-spc")
        kwargs['specnum']=int(sys.argv[ind+1])
    if '-tz' in sys.argv:
        ind=sys.argv.index("-tz")
        kwargs['timezone']=sys.argv[ind+1]

    convert(**kwargs)

if  __name__ == "__main__":
    main()
