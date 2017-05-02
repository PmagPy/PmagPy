#!/usr/bin/env python
"""
NAME
    _2g_bin_magic.py

DESCRIPTION
    takes the binary 2g format magnetometer files and converts them to magic_measurements, er_samples.txt and er_sites.txt file

SYNTAX
    2g_bin_magic.py [command line options]

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
    -ncn NCON:  specify naming convention: default is #2 below
    -ocn OCON:  specify orientation convention, default is #5 below
    -mcd: specify sampling method codes as a colon delimited string:  [default is: FS-FD:SO-POM]
         FS-FD field sampling done with a drill
         FS-H field sampling done with hand samples
         FS-LOC-GPS  field location done with GPS
         FS-LOC-MAP  field location done with map
         SO-POM   a Pomeroy orientation device was used
         SO-ASC   an ASC orientation device was used
         SO-MAG   orientation with magnetic compass
         SO-SUN   orientation with sun compass
    -loc: location name, default="unknown"
    -lat latitude of site (also used as bounding latitude for location)
    -lon longitude of site (also used as bounding longitude for location)
    -spc NUM : specify number of characters to designate a  specimen, default = 0
    -ins INST : specify instsrument name
    -A: average replicate measurements

INPUT FORMAT
    Input files are horrible mag binary format (who knows why?)
    Orientation convention:
        [1] Lab arrow azimuth= mag_azimuth; Lab arrow dip=-field_dip
            i.e., field_dip is degrees from vertical down - the hade [default]
        [2] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = -field_dip
            i.e., mag_azimuth is strike and field_dip is hade
        [3] Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip
            i.e.,  lab arrow same as field arrow, but field_dip was a hade.
        [4] lab azimuth and dip are same as mag_azimuth, field_dip
        [5] lab azimuth is same as mag_azimuth,lab arrow dip=field_dip-90
        [6] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = 90-field_dip
        [7] all others you will have to either customize your
            self or e-mail ltauxe@ucsd.edu for help.

     Magnetic declination convention:
         Az will use supplied declination to correct azimuth

   Sample naming convention:
    [1] XXXXY: where XXXX is an arbitrary length site designation and Y
        is the single character sample designation.  e.g., TG001a is the
        first sample from site TG001.    [default]
    [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
    [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
    [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
    [5] site name = sample name
    [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
    [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
    NB: all others you will have to either customize your
        self or e-mail ltauxe@ucsd.edu for help.

OUTPUT
        output saved in magic_measurements.txt & er_samples.txt formatted files
          will overwrite any existing files
"""
from __future__ import print_function
from builtins import range
import sys, os
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb
from functools import reduce

def skip(N,ind,L):
    for b in range(N):
        ind+=1
        while L[ind]=="":ind+=1
    ind+=1
    while L[ind]=="":ind+=1
    return ind

def convert(**kwargs):
    #
    # initialize variables
    #
    bed_dip,bed_dip_dir="",""
    sclass,lithology,_type="","",""
    DecCorr=0.
    months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

    dir_path = kwargs.get('dir_path', '.')
    mag_file = kwargs.get('mag_file', '')
    meas_file = kwargs.get('meas_file', 'measurements.txt')
    spec_file = kwargs.get('spec_file', 'specimens.txt')
    samp_file = kwargs.get('samp_file', 'samples.txt')
    site_file = kwargs.get('site_file', 'sites.txt')
    loc_file = kwargs.get('loc_file', 'locations.txt')
    or_con = kwargs.get('or_con', '3')
    samp_con = kwargs.get('samp_con', '2')
    corr = kwargs.get('corr', '1')
    gmeths = kwargs.get('gmeths', 'FS-FD:SO-POM')
    location = kwargs.get('location', 'unknown')
    specnum = int(kwargs.get('specnum', 0))
    inst = kwargs.get('inst', '')
    user = kwargs.get('user', '')
    noave = kwargs.get('noave', 0) # default is DO average
    ID = kwargs.get('ID', '')
    lat = kwargs.get('lat', '')
    lon = kwargs.get('lon', '')

    # format and fix variables acquired from command line sys.argv or input with **kwargs
    if specnum!=0:specnum=-specnum

    if ID:
        input_dir_path = ID
    else:
        input_dir_path = dir_path

    if samp_con:
        if "4" in samp_con:
            if "-" not in samp_con:
                print("option [4] must be in form 4-Z where Z is an integer")
                return False, "option [4] must be in form 4-Z where Z is an integer"
            else:
                Z=samp_con.split("-")[1]
                samp_con="4"
        if "7" in samp_con:
            if "-" not in samp_con:
                print("option [7] must be in form 7-Z where Z is an integer")
                return False, "option [7] must be in form 7-Z where Z is an integer"
            else:
                Z=samp_con.split("-")[1]
                samp_con="7"
        if "6" in samp_con:
            Z=1
            try:
                SampRecs,file_type=pmag.magic_read(os.path.join(input_dir_path, 'er_samples.txt'))
            except:
                print("there is no er_samples.txt file in your input directory - you can't use naming convention #6")
                return False, "there is no er_samples.txt file in your input directory - you can't use naming convention #6"
            if file_type == 'bad_file':
                print("there is no er_samples.txt file in your input directory - you can't use naming convention #6")
                return False, "there is no er_samples.txt file in your input directory - you can't use naming convention #6"
        else: Z=1

    if not mag_file:
        print("mag file is required input")
        return False, "mag file is required input"
    output_dir_path = dir_path
    mag_file = os.path.join(input_dir_path, mag_file)
    meas_file= os.path.join(output_dir_path, meas_file)
    spec_file= os.path.join(output_dir_path, spec_file)
    samp_file = os.path.join(output_dir_path, samp_file)
    site_file = os.path.join(output_dir_path, site_file)
    loc_file= os.path.join(output_dir_path, loc_file)

    samplist=[]
    try:
        SampRecs,file_type=pmag.magic_read(samp_file)
    except:
        SampRecs=[]
    MeasRecs,SpecRecs,SiteRecs,LocRecs=[],[],[],[]
    try:
        f=open(mag_file,'brU')
        input=str(f.read()).strip("b '")
        f.close()
    except Exception as ex:
        print('ex', ex)
        print("bad mag file")
        return False, "bad mag file"
    firstline,date=1,""
    d=input.split('\\xcd')
    for line in d:
        rec=line.split('\\x00')
        if firstline==1:
            firstline=0
            spec,vol="",1
            el=51
            while line[el:el+1]!="\\": spec=spec+line[el];el+=1
            # check for bad sample name
            test=spec.split('.')
            date=""
            if len(test)>1:
                spec=test[0]
                kk=24
                while line[kk]!='\\x01' and line[kk]!='\\x00':
                    kk+=1
                vcc=line[24:kk]
                el=10
                while rec[el].strip()!='':el+=1
                date,comments=rec[el+7],[]
            else:
                el=9
                while rec[el]!='\\x01':el+=1
                vcc,date,comments=rec[el-3],rec[el+7],[]
            specname=spec.lower()
            print('importing ',specname)
            el+=8
            while rec[el].isdigit()==False:
                comments.append(rec[el])
                el+=1
            while rec[el]=="":el+=1
            az=float(rec[el])
            el+=1
            while rec[el]=="":el+=1
            pl=float(rec[el])
            el+=1
            while rec[el]=="":el+=1
            bed_dip_dir=float(rec[el])
            el+=1
            while rec[el]=="":el+=1
            bed_dip=float(rec[el])
            el+=1
            while rec[el]=="":el+=1
            if rec[el]=='\\x01':
                bed_dip=180.-bed_dip
                el+=1
                while rec[el]=="":el+=1
            fold_az=float(rec[el])
            el+=1
            while rec[el]=="":el+=1
            fold_pl=rec[el]
            el+=1
            while rec[el]=="":el+=1
            if rec[el]!="" and rec[el]!='\\x02' and rec[el]!='\\x01':
                deccorr=float(rec[el])
                az+=deccorr
                bed_dip_dir+=deccorr
                fold_az+=deccorr
                if bed_dip_dir>=360:bed_dip_dir=bed_dip_dir-360.
                if az>=360.:az=az-360.
                if fold_az>=360.:fold_az=fold_az-360.
            else:
                deccorr=0
            if specnum!=0:
                sample=specname[:specnum]
            else:
                sample=specname

            methods=gmeths.split(':')
            if deccorr!="0":
                if 'SO-MAG' in methods:del methods[methods.index('SO-MAG')]
                methods.append('SO-CMD-NORTH')
            meths = reduce(lambda x,y: x+':'+y, methods)
            method_codes=meths
            site=pmag.parse_site(sample,samp_con,Z) # parse out the site name
            SpecRec,SampRec,SiteRec,LocRec={},{},{},{}
            SpecRec["specimen"]=specname
            SpecRec["sample"]=sample
            if vcc.strip()!="":vol=float(vcc)*1e-6 # convert to m^3 from cc
            SpecRec["volumne"]='%10.3e'%(vol) #
            SpecRec["geologic_classes"]=sclass
            SpecRec["lithologies"]=lithology
            SpecRec["geologic_types"]=_type
            SpecRecs.append(SpecRec)

            if sample!="" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
                SampRec["sample"]=sample
                SampRec["site"]=site
                labaz,labdip=pmag.orient(az,pl,or_con) # convert to labaz, labpl
                SampRec["bed_dip"]='%7.1f'%(bed_dip)
                SampRec["bed_dip_direction"]='%7.1f'%(bed_dip_dir)
                SampRec["dip"]='%7.1f'%(labdip)
                SampRec["azimuth"]='%7.1f'%(labaz)
                SampRec["azimuth_dec_correction"]='%7.1f'%(deccorr)
                SampRec["geologic_classes"]=sclass
                SampRec["lithologies"]=lithology
                SampRec["geologic_types"]=_type
                SampRec["method_codes"]=method_codes
                SampRecs.append(SampRec)

            if site!="" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
                SiteRec['site'] = site
                SiteRec['location'] = location
                SiteRec['lat'] = lat
                SiteRec['lon'] = lon
                SiteRec["geologic_classes"]=sclass
                SiteRec["lithologies"]=lithology
                SiteRec["geologic_types"]=_type
                SiteRecs.append(SiteRec)

            if location!="" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
                LocRec['location']=location
                LocRec['lat_n'] = lat
                LocRec['lon_e'] = lon
                LocRec['lat_s'] = lat
                LocRec['lon_w'] = lon
                LocRec["geologic_classes"]=sclass
                LocRec["lithologies"]=lithology
                LocRec["geologic_types"]=_type
                LocRecs.append(LocRec)

        else:
            MeasRec={}
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
            MeasRec["specimen"]=specname
            el,demag=1,''
            treat=rec[el]
            if treat[-1]=='C':
                demag='T'
            elif treat!='NRM':
                demag='AF'
            el+=1
            while rec[el]=="":el+=1
            MeasRec["dir_dec"]=rec[el]
            cdec=float(rec[el])
            el+=1
            while rec[el]=="":el+=1
            MeasRec["dir_inc"]=rec[el]
            cinc=float(rec[el])
            el+=1
            while rec[el]=="":el+=1
            gdec=rec[el]
            el+=1
            while rec[el]=="":el+=1
            ginc=rec[el]
            el=skip(2,el,rec) # skip bdec,binc
#                el=skip(4,el,rec) # skip gdec,ginc,bdec,binc
#                print 'moment emu: ',rec[el]
            MeasRec["magn_moment"]='%10.3e'% (float(rec[el])*1e-3) # moment in Am^2 (from emu)
            MeasRec["magn_volume"]='%10.3e'% (float(rec[el])*1e-3/vol) # magnetization in A/m
            el=skip(2,el,rec) # skip to xsig
            MeasRec["magn_x_sigma"]='%10.3e'% (float(rec[el])*1e-3) # convert from emu
            el=skip(3,el,rec) # skip to ysig
            MeasRec["magn_y_sigma"]='%10.3e'% (float(rec[el])*1e-3) # convert from emu
            el=skip(3,el,rec) # skip to zsig
            MeasRec["magn_z_sigma"]='%10.3e'% (float(rec[el])*1e-3) # convert from emu
            el+=1 # skip to positions
            MeasRec["meas_n_orient"]=rec[el]
#                    el=skip(5,el,rec) # skip to date
#                    mm=str(months.index(date[0]))
#                    if len(mm)==1:
#                        mm='0'+str(mm)
#                    else:
#                        mm=str(mm)
#                    dstring=date[2]+':'+mm+':'+date[1]+":"+date[3]
#                    MeasRec['measurement_date']=dstring
            MeasRec["instrument_codes"]=inst
            MeasRec["analysts"]=user
            MeasRec["citations"]="This study"
            MeasRec["method_codes"]=meas_type
            if demag=="AF":
                MeasRec["treat_ac_field"]='%8.3e' %(float(treat[:-2])*1e-3) # peak field in tesla
                meas_type="LT-AF-Z"
                MeasRec["treat_dc_field"]='0'
            elif demag=="T":
                MeasRec["treat_temp"]='%8.3e' % (float(treat[:-1])+273.) # temp in kelvin
                meas_type="LT-T-Z"
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
    kwargs={}
    if '-WD' in sys.argv:
        ind=sys.argv.index("-WD")
        kwargs['dir_path']=sys.argv[ind+1]
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if "-usr" in sys.argv:
        ind=sys.argv.index("-usr")
        kwargs['user']=sys.argv[ind+1]
    if "-f" in sys.argv:
        ind=sys.argv.index("-f")
        kwargs['mag_file']=sys.argv[ind+1]
    if "-F" in sys.argv:
        ind=sys.argv.index("-F")
        kwargs['meas_file']=sys.argv[ind+1]
    if "-Fsp" in sys.argv:
        ind=sys.argv.index("-Fsp")
        kwargs['spec_file']=sys.argv[ind+1]
    if "-Fsa" in sys.argv:
        ind=sys.argv.index("-Fsa")
        kwargs['samp_file']=sys.argv[ind+1]
    if "-Fsi" in sys.argv:
        ind=sys.argv.index("-Fsi")
        kwargs['site_file']=sys.argv[ind+1]
    if "-Flo" in sys.argv:
        ind=sys.argv.index("-Flo")
        kwargs['loc_file']=sys.argv[ind+1]
    if "-ocn" in sys.argv:
        ind=sys.argv.index("-ocn")
        kwargs['or_con']=sys.argv[ind+1]
    if "-ncn" in sys.argv:
        ind=sys.argv.index("-ncn")
        kwargs['samp_con']=sys.argv[ind+1]
    if "-mcd" in sys.argv:
        ind=sys.argv.index("-mcd")
        kwargs['gmeths']=(sys.argv[ind+1])
    if "-loc" in sys.argv:
        ind=sys.argv.index("-loc")
        kwargs['location']=(sys.argv[ind+1])
    if "-spc" in sys.argv:
        ind=sys.argv.index("-spc")
        kwargs['specnum']=int(sys.argv[ind+1])
    if "-ins" in sys.argv:
        ind=sys.argv.index("-ins")
        kwargs['inst']=sys.argv[ind+1]
    if "-A" in sys.argv:
        kwargs['noave']=1
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwargs['ID'] = sys.argv[ind+1]
    if "-lat" in sys.argv:
        ind = sys.argv.index("-lat")
        kwargs['lat'] = sys.argv[ind+1]
    if "-lon" in sys.argv:
        ind = sys.argv.index("-lon")
        kwargs['lon'] = sys.argv[ind+1]

    convert(**kwargs)

if __name__ == "__main__":
    main()
