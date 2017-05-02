#!/usr/bin/env python
"""
NAME
    utrecht_magic.py

DESCRIPTION
    converts Utrecht magnetometer data files to magic_measurements files

SYNTAX
    utrecht_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -ID: directory for input file if not included in -f flag
    -f FILE: specify  input file, required
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -ncn: Site Naming Convention
     Site to Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2: default] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
    -spc: number of characters to remove to generate sample names from specimen names
    -loc LOCNAME : specify location/study name
    -lat LAT: latitude of site (also used as bounding latitude for location)
    -lon LON: longitude of site (also used as bounding longitude for location)
    -A: don't average replicate measurements
    -mcd: [SO-MAG,SO-SUN,SO-SIGHT...] supply how these samples were oriented
    -dc B PHI THETA: dc lab field (in microTesla), phi,and theta (in degrees) must be spaced after flag (i.e -dc 30 0 -90)
    -mno: number of orientations measured (default=8)

INPUT
    Utrecht magnetometer data file
"""
from __future__ import print_function
from builtins import str
import os,sys
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb
from numpy import array
import pytz, datetime


def convert(**kwargs):

    # initialize some stuff
    version_num = pmag.get_version()
    MeasRecs,SpecRecs,SampRecs,SiteRecs,LocRecs = [],[],[],[],[]

    dir_path = kwargs.get('dir_path', '.')
    input_dir_path = kwargs.get('input_dir_path', dir_path)
    output_dir_path = dir_path
    meas_file = kwargs.get('meas_file', 'measurements.txt')
    mag_file = kwargs.get('mag_file')
    spec_file = kwargs.get('spec_file', 'specimens.txt') # specimen outfile
    samp_file = kwargs.get('samp_file', 'samples.txt')
    site_file = kwargs.get('site_file', 'sites.txt') # site outfile
    loc_file = kwargs.get('loc_file', 'locations.txt') # site outfile
    location = kwargs.get('location', 'unknown')
    dmy_flag = kwargs.get('dmy_flag', False)
    lat = kwargs.get('lat', '')
    lon = kwargs.get('lon', '')
    #oave = kwargs.get('noave', 0) # default (0) means DO average
    meth_code = kwargs.get('meth_code', "LP-NO")
    specnum = -int(kwargs.get('specnum', 0))
    samp_con = kwargs.get('samp_con', '2')
    if "4" in samp_con:
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            site_num=samp_con.split("-")[1]
            samp_con="4"
    elif "7" in samp_con:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
        else:
            site_num=samp_con.split("-")[1]
            samp_con="7"
    else: site_num=1
    try:
        DC_FIELD = float(kwargs.get('labfield',0))*1e-6
        DC_PHI = float(kwargs.get('phi',0))
        DC_THETA = float(kwargs.get('theta',0))
    except ValueError: raise ValueError('problem with your dc parameters. please provide a labfield in microTesla and a phi and theta in degrees.')
    noave = kwargs.get('noave', False)
    dmy_flag = kwargs.get('dmy_flag', False)
    meas_n_orient = kwargs.get('meas_n_orient', '8')

    # format variables
    if not mag_file:
        return False, 'You must provide a Utrecht formated file'
    mag_file = os.path.join(input_dir_path, mag_file)

    # parse data

    # Open up the Utrecht file and read the header information
    AF_or_T = mag_file.split('.')[-1]
    data = open(mag_file, 'r')
    line = data.readline()
    line_items = line.split(',')
    operator=line_items[0]
    operator=operator.replace("\"","")
    machine=line_items[1]
    machine=machine.replace("\"","")
    machine=machine.rstrip('\n')
#    print("operator=", operator)
#    print("machine=", machine)

    #read in measurement data
    line = data.readline()
    while line != "END" and line != '"END"':
        SpecRec,SampRec,SiteRec,LocRec = {},{},{},{}
        line_items = line.split(',')
        spec_name=line_items[0]
        spec_name=spec_name.replace("\"","")
#        print("spec_name=", spec_name)
        free_string=line_items[1]
        free_string=free_string.replace("\"","")
#        print("free_string=", free_string)
        dec=line_items[2]
#        print("dec=", dec)
        inc=line_items[3]
#        print("inc=", inc)
        volume=float(line_items[4])
        volume=volume * 1e-6 # enter volume in cm^3, convert to m^3
#        print("volume=", volume)
        bed_plane=line_items[5]
#        print("bed_plane=", bed_plane)
        bed_dip=line_items[6]
#        print("bed_dip=", bed_dip)

        # Configure et er_ tables
        if specnum==0: sample_name = spec_name
        else: sample_name = spec_name[:specnum]
        site = pmag.parse_site(sample_name,samp_con,site_num)
        SpecRec['specimen'] = spec_name
        SpecRec['sample'] = sample_name
        if volume!=0: SpecRec['volume']=volume
        SpecRecs.append(SpecRec)
        if sample_name!="" and sample_name not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
            SampRec['sample'] = sample_name
            SampRec['azimuth'] = dec
            SampRec['dip'] = str(float(inc)-90)
            SampRec['bed_dip_direction'] = bed_plane
            SampRec['bed_dip'] = bed_dip
            SampRec['method_codes'] = meth_code
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

        #measurement data
        line = data.readline()
        line = line.rstrip("\n")
        items = line.split(",")
        while line != '9999':
            step=items[0]
            step=step.split('.')
            step_value=step[0]
            step_type = ""
            if len(step) == 2:
                step_type=step[1]
            if step_type=='5':
                step_value = items[0]
            A=float(items[1])
            B=float(items[2])
            C=float(items[3])
#  convert to MagIC coordinates
            Z=-A
            X=-B
            Y=C
            cart = array([X, Y, Z]).transpose()
            direction = pmag.cart2dir(cart).transpose()
            measurement_dec = direction[0]
            measurement_inc = direction[1]
            magn_moment = direction[2] * 1.0e-12 # the data are in pico-Am^2 - this converts to Am^2
            if volume!=0:
                magn_volume = direction[2] * 1.0e-12 / volume # data volume normalized - converted to A/m
#            print("magn_moment=", magn_moment)
#            print("magn_volume=", magn_volume)
            error = items[4]
            date=items[5]
            date=date.strip('"').replace(' ','')
            if date.count("-") > 0:
                date=date.split("-")
            elif date.count("/") > 0:
                date=date.split("/")
            else: print("date format seperator cannot be identified")
#            print(date)
            time=items[6]
            time=time.strip('"').replace(' ','')
            time=time.split(":")
#            print(time)
            dt = date[0] + ":" + date[1] + ":" + date[2] + ":" + time[0] + ":" + time[1] + ":" + "0"
            local = pytz.timezone("Europe/Amsterdam")
            try:
                if dmy_flag: naive = datetime.datetime.strptime(dt, "%d:%m:%Y:%H:%M:%S")
                else: naive = datetime.datetime.strptime(dt, "%m:%d:%Y:%H:%M:%S")
            except ValueError:
                naive = datetime.datetime.strptime(dt, "%Y:%m:%d:%H:%M:%S")
            local_dt = local.localize(naive, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            timestamp=utc_dt.strftime("%Y-%m-%dT%H:%M:%S")+"Z"
#            print(timestamp)

            MeasRec = {}
            MeasRec["timestamp"]=timestamp
            MeasRec["analysts"] = operator
            MeasRec["instrument_codes"] = "Utrecht_" + machine
            MeasRec["description"] = "free string = " + free_string
            MeasRec["citations"] = "This study"
            MeasRec['software_packages'] = version_num
            MeasRec["meas_temp"] = '%8.3e' % (273) # room temp in kelvin
            MeasRec["quality"] = 'g'
            MeasRec["standard"] = 'u'
            MeasRec["experiments"] = location + site + spec_name
            MeasRec["treat_step_num"] = location + site + spec_name + items[0]
            MeasRec["specimen"] = spec_name
            # MeasRec["treat_ac_field"] = '0'
            if AF_or_T.lower() == "th":
                MeasRec["treat_temp"] = '%8.3e' % (float(step_value)+273.) # temp in kelvin
                MeasRec['treat_ac_field']='0'
                lab_treat_type = "T"
            else:
                MeasRec['treat_temp']='273'
                MeasRec['treat_ac_field']='%10.3e'%(float(step_value)*1e-3)
                lab_treat_type = "AF"
            MeasRec['treat_dc_field']='0'
            if step_value == '0':
                meas_type = "LT-NO"
#            print("step_type=", step_type)
            if step_type == '0' or step_type == '00':
                meas_type = "LT-%s-Z"%lab_treat_type
            elif step_type == '1' or step_type == '11':
                meas_type = "LT-%s-I"%lab_treat_type
                MeasRec['treat_dc_field']='%1.2e'%DC_FIELD
            elif step_type == '2' or step_type == '12':
                meas_type = "LT-PTRM-I"
                MeasRec['treat_dc_field']='%1.2e'%DC_FIELD
            elif step_type == '3' or step_type == '13':
                meas_type = "LT-PTRM-Z"
#            print("meas_type=", meas_type)
            MeasRec['treat_dc_field_phi'] = '%1.2f'%DC_PHI
            MeasRec['treat_dc_field_theta'] = '%1.2f'%DC_THETA
            MeasRec['method_codes'] = meas_type
            MeasRec["magn_moment"] = magn_moment
            if volume!=0: MeasRec["magn_volume"] = magn_volume
            MeasRec["dir_dec"] = measurement_dec
            MeasRec["dir_inc"] = measurement_inc
            MeasRec['dir_csd'] = error
            MeasRec['meas_n_orient'] = meas_n_orient
#            print(MeasRec)
            MeasRecs.append(MeasRec)

            line = data.readline()
            line = line.rstrip("\n")
            items = line.split(",")
        line = data.readline()
        line = line.rstrip("\n")
        items = line.split(",")

    data.close()

    con = nb.Contribution(output_dir_path,read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts=pmag.measurements_methods3(MeasRecs,noave) #figures out method codes for measuremet data
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
    # get command line arguments
    kwargs={}
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
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
    if "-lat" in sys.argv:
        ind = sys.argv.index("-lat")
        kwargs['lat'] = sys.argv[ind+1]
    if "-lon" in sys.argv:
        ind = sys.argv.index("-lon")
        kwargs['lon'] = sys.argv[ind+1]
    if "-A" in sys.argv:
        kwargs['noave'] = True
    if "-mcd" in sys.argv:
        ind = sys.argv.index("-mcd")
        kwargs['meth_code'] = sys.argv[ind+1]
    if "-ncn" in sys.argv:
        ind=sys.argv.index("-ncn")
        kwargs['samp_con']=sys.argv[ind+1]
    if '-dc' in sys.argv:
        ind=sys.argv.index('-dc')
        kwargs['labfield']=sys.argv[ind+1]
        kwargs['phi']=sys.argv[ind+2]
        kwargs['theta']=sys.argv[ind+3]
    if '-spc' in sys.argv:
        ind=sys.argv.index("-spc")
        kwargs['specnum']=sys.argv[ind+1]
    if '-mno' in sys.argv:
        ind=sys.argv.index('-mno')
        kwargs['meas_n_orient']=sys.argv[ind+1]
    if 'dmy' in sys.argv:
        kwargs['dmy_flag']=True

    convert(**kwargs)

if  __name__ == "__main__":
    main()
