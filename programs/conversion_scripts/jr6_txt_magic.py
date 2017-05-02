#!/usr/bin/env python
"""
NAME
    jr6_txt_magic.py

DESCRIPTION
    converts JR6 .txt format files to magic_measurements format files

SYNTAX
    jr6_txt_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -usr USER: Colon delimited list of analysts, default is ""
    -ID: directory for input file if not included in -f flag
    -f FILE: specify  input file, required
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt # LORI
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -spc NUM : specify number of characters to designate a  specimen, default = 1
    -loc LOCNAME : specify location/study name
    -lat latitude of site (also used as bounding latitude for location)
    -lon longitude of site (also used as bounding longitude for location)
    -A: don't average replicate measurements
    -ncn NCON: specify sample naming convention (6 and 7 not yet implemented)
    -mcd [SO-MAG,SO-SUN,SO-SIGHT...] supply how these samples were oriented
    -v NUM : specify the volume in cc of the sample, default 2.5^3cc
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
    -tz: timezone in pytz library format. list of timzones can be found at http://pytz.sourceforge.net/. (default: UTC)

INPUT
    JR6 .txt format file
"""
from __future__ import print_function
from builtins import str
import sys, os
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb
import pytz, datetime

def convert(**kwargs):

    version_num=pmag.get_version()
    dir_path = kwargs.get('dir_path', '.')
    input_dir_path = kwargs.get('input_dir_path', dir_path)
    output_dir_path = dir_path
    user = kwargs.get('user', '')
    meas_file = kwargs.get('meas_file', 'measurements.txt') # outfile
    spec_file = kwargs.get('spec_file', 'specimens.txt') # specimen outfile
    samp_file = kwargs.get('samp_file', 'samples.txt') # sample outfile
    site_file = kwargs.get('site_file', 'sites.txt') # site outfile
    loc_file = kwargs.get('loc_file', 'locations.txt') # location outfile
    mag_file = kwargs.get('mag_file')
    specnum = kwargs.get('specnum', 1)
    samp_con = kwargs.get('samp_con', '1')
    location = kwargs.get('location', 'unknown')
    lat = kwargs.get('lat', '')
    lon = kwargs.get('lon', '')
    noave = kwargs.get('noave', 0) # default (0) means DO average
    meth_code = kwargs.get('meth_code', "LP-NO")
    volume = float(kwargs.get('volume', 2.5))* 1e-6
    timezone = kwargs.get('timestamp', 'UTC')

    # format variables
    mag_file = os.path.join(input_dir_path, mag_file)
    if specnum!=0: specnum=-int(specnum)
    if samp_con.startswith("4"):
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            Z=samp_con.split("-")[1]
            samp_con="4"
    elif samp_con.startswith("7"):
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
        else:
            Z=samp_con.split("-")[1]
            samp_con="7"
    else: Z=1

    #create data holders
    MeasRecs,SpecRecs,SampRecs,SiteRecs,LocRecs=[],[],[],[],[]

    # parse data
    data=open(mag_file,'r')
    line=data.readline()
    line=data.readline()
    line=data.readline()
    while line !='':
        parsedLine=line.split()
        if len(parsedLine)>=4:
            sampleName=parsedLine[0]
            demagLevel=parsedLine[2]
            date=parsedLine[3] + ":0:0:0"
            line=data.readline()
            line=data.readline()
            line=data.readline()
            line=data.readline()
            parsedLine=line.split()
            specimenAngleDec=parsedLine[1]
            specimenAngleInc=parsedLine[2]
            while parsedLine[0] != 'MEAN' :
                line=data.readline()
                parsedLine=line.split()
                if len(parsedLine) == 0:
                    parsedLine=["Hello"]
            Mx=parsedLine[1]
            My=parsedLine[2]
            Mz=parsedLine[3]
            line=data.readline()
            line=data.readline()
            parsedLine=line.split()
            splitExp = parsedLine[2].split('A')
            intensityVolStr=parsedLine[1] + splitExp[0]
            intensityVol = float(intensityVolStr)

            # check and see if Prec is too big and messes with the parcing.
            precisionStr=''
            if len(parsedLine) == 6:  #normal line
                precisionStr=parsedLine[5][0:-1]
            else:
                precisionStr=parsedLine[4][0:-1]

            precisionPer = float(precisionStr)
            precision=intensityVol*precisionPer/100

            while parsedLine[0] != 'SPEC.' :
                line=data.readline()
                parsedLine=line.split()
                if len(parsedLine) == 0:
                    parsedLine=["Hello"]

            specimenDec=parsedLine[2]
            specimenInc=parsedLine[3]
            line=data.readline()
            line=data.readline()
            parsedLine=line.split()
            geographicDec=parsedLine[1]
            geographicInc=parsedLine[2]

            # Add data to various MagIC data tables.
            specimen = sampleName
            if specnum!=0: sample=specimen[:specnum]
            else: sample=specimen
            site=pmag.parse_site(sample,samp_con,Z)

            MeasRec,SpecRec,SampRec,SiteRec,LocRec={},{},{},{},{}

            if specimen!="" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
                SpecRec['specimen'] = specimen
                SpecRec['sample'] = sample
                SpecRec["citations"]="This study"
                SpecRec["analysts"]=user
                SpecRec['volume'] = volume
                SpecRecs.append(SpecRec)
            if sample!="" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
                SampRec['sample'] = sample
                SampRec['site'] = site
                SampRec["citations"]="This study"
                SampRec["analysts"]=user
                SampRec['azimuth'] = specimenAngleDec
                sample_dip=str(float(specimenAngleInc)-90.0) #convert to magic orientation
                SampRec['dip'] = sample_dip
                SampRec['method_codes']=meth_code
                SampRecs.append(SampRec)
            if site!="" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
                SiteRec['site'] = site
                SiteRec['location'] = location
                SiteRec["citations"]="This study"
                SiteRec["analysts"]=user
                SiteRec['lat'] = lat
                SiteRec['lon'] = lon
                SiteRecs.append(SiteRec)
            if location!="" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
                LocRec['location']=location
                LocRec["citations"]="This study"
                LocRec["analysts"]=user
                LocRec['lat_n'] = lat
                LocRec['lon_e'] = lon
                LocRec['lat_s'] = lat
                LocRec['lon_w'] = lon
                LocRecs.append(LocRec)

            local = pytz.timezone(timezone)
            naive = datetime.datetime.strptime(date, "%m-%d-%Y:%H:%M:%S")
            local_dt = local.localize(naive, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            timestamp=utc_dt.strftime("%Y-%m-%dT%H:%M:%S")+"Z"
            MeasRec["specimen"]=specimen
            MeasRec["timestamp"] = timestamp
            MeasRec['description']=''
            MeasRec["citations"]="This study"
            MeasRec['software_packages']=version_num
            MeasRec["treat_temp"]='%8.3e' % (273) # room temp in kelvin
            MeasRec["meas_temp"]='%8.3e' % (273) # room temp in kelvin
            MeasRec["quality"]='g'
            MeasRec["standard"]='u'
            MeasRec["treat_step_num"]='1'
            MeasRec["treat_ac_field"]='0'
            if demagLevel == 'NRM':
                meas_type="LT-NO"
            elif demagLevel[0] == 'A':
                meas_type="LT-AF-Z"
                treat=float(demagLevel[1:])
                MeasRec["treat_ac_field"]='%8.3e' %(treat*1e-3) # convert from mT to tesla
            elif demagLevel[0] == 'T':
                meas_type="LT-T-Z"
                treat=float(demagLevel[1:])
                MeasRec["treat_temp"]='%8.3e' % (treat+273.) # temp in kelvin
            else:
                print("measurement type unknown", demag_level)
                return False, "measurement type unknown"

            MeasRec["magn_moment"]=str(intensityVol*volume) # Am^2
            MeasRec["magn_volume"]=intensityVolStr # A/m
            MeasRec["dir_dec"]=specimenDec
            MeasRec["dir_inc"]=specimenInc
            MeasRec['method_codes']=meas_type
            MeasRecs.append(MeasRec)

        #read lines till end of record
        line=data.readline()
        line=data.readline()
        line=data.readline()
        line=data.readline()
        line=data.readline()

        # read all the rest of the special characters. Some data files not consistantly formatted.
        while (len(line) <=3 and line!=''):
            line=data.readline()
        #end of data while loop

    data.close()

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
        kwargs['dir_path']=sys.argv[ind+1]
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwargs['input_dir_path'] = sys.argv[ind+1]
    if '-F' in sys.argv:
        ind=sys.argv.index("-F")
        kwargs['meas_file']=sys.argv[ind+1]
    if '-Fsp' in sys.argv:
        ind=sys.argv.index("-Fsp")
        kwargs['spec_file']=sys.argv[ind+1]
    if '-Fsa' in sys.argv:
        ind=sys.argv.index("-Fsa")
        kwargs['samp_file']=sys.argv[ind+1]
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
    if "-lat" in sys.argv:
        ind = sys.argv.index("-lat")
        kwargs['lat'] = sys.argv[ind+1]
    if "-lon" in sys.argv:
        ind = sys.argv.index("-lon")
        kwargs['lon'] = sys.argv[ind+1]
    if "-A" in sys.argv: kwargs['noave']=True
    if "-mcd" in sys.argv:
        ind=sys.argv.index("-mcd")
        kwargs['meth_code']=sys.argv[ind+1]
    if "-v" in sys.argv:
        ind=sys.argv.index("-v")
        kwargs['volume']=sys.argv[ind+1] # enter volume in cc, convert to m^3
    if '-tz' in sys.argv:
        ind=sys.argv.index("-tz")
        kwargs['timezone']=sys.argv[ind+1]

    convert(**kwargs)

if __name__ == "__main__":
    main()
