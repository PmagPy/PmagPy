#!/usr/bin/env python
"""
NAME
    iodp_dscr_magic.py

DESCRIPTION
    converts ODP LIMS discrete sample format files to magic_measurements format files

SYNTAX
    iodp_descr_magic.py [command line options]

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
    -A: don't average replicate measurements
    -v NUM: volume in cm^3, will be used if there is no volume in the input data (default : 15.625 cm^3 or a 2.5 cm cube)

INPUTS
     IODP discrete sample .csv file format exported from LIMS database
"""
from __future__ import print_function
from builtins import str
from builtins import range
import sys, os
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb

def convert(**kwargs):
    # initialize defaults
    version_num=pmag.get_version()

    dir_path = kwargs.get('dir_path', '.')
    input_dir_path = kwargs.get('input_dir_path', dir_path)
    output_dir_path = dir_path # rename dir_path after input_dir_path is set
    noave = kwargs.get('noave', False) # default is DO average
    csv_file = kwargs.get('csv_file', '')
    meas_file = kwargs.get('meas_file', 'measurements.txt')
    spec_file = kwargs.get('spec_file', 'specimens.txt')
    samp_file = kwargs.get('samp_file', 'samples.txt')
    site_file = kwargs.get('site_file', 'sites.txt')
    loc_file = kwargs.get('loc_file', 'locations.txt')
    lat = kwargs.get('lat', '')
    lon = kwargs.get('lon', '')
    volume = kwargs.get('volume', 2.5**3)*1e-6#default volume is a 2.5cm cube

    # format variables
    if csv_file=="":
        filelist=os.listdir(input_dir_path) # read in list of files to import
    else:
        csv_file = os.path.join(input_dir_path, csv_file)
        filelist=[csv_file]

    # parsing the data
    file_found,citations = False,"This Study"
    MeasRecs,SpecRecs,SampRecs,SiteRecs,LocRecs=[],[],[],[],[]
    for fin in filelist: # parse each file
        if fin[-3:].lower()=='csv':
            file_found = True
            print('processing: ',fin)
            indata=open(fin,'r').readlines()
            keys=indata[0].replace('\n','').split(',') # splits on underscores
            keys=[k.strip('"') for k in keys]
            interval_key="Offset (cm)"
            if "Treatment Value (mT or \xc2\xb0C)" in keys:demag_key="Treatment Value (mT or \xc2\xb0C)"
            elif "Treatment Value" in keys:demag_key="Treatment Value"
            elif "Treatment Value (mT or &deg;C)" in keys:demag_key="Treatment Value (mT or &deg;C)"
            elif "Demag level (mT)" in keys:demag_key="Demag level (mT)"
            else: print("couldn't find demag level")
            if "Treatment type" in keys:treatment_type="Treatment type"
            elif "Treatment Type" in keys:treatment_type="Treatment Type"
            else: treatment_type=""
            run_key="Test No."
            if "Inclination background + tray corrected  (deg)" in keys: inc_key="Inclination background + tray corrected  (deg)"
            elif "Inclination background &amp; tray corrected (deg)" in keys: inc_key="Inclination background &amp; tray corrected (deg)"
            elif "Inclination background & tray corrected (deg)" in keys:inc_key="Inclination background & tray corrected (deg)"
            elif "Inclination background & drift corrected (deg)" in keys:inc_key="Inclination background & drift corrected (deg)"
            else: print("couldn't find inclination")
            if "Declination background + tray corrected (deg)" in keys: dec_key="Declination background + tray corrected (deg)"
            elif "Declination background &amp; tray corrected (deg)" in keys: dec_key="Declination background &amp; tray corrected (deg)"
            elif "Declination background & tray corrected (deg)" in keys:dec_key="Declination background & tray corrected (deg)"
            elif "Declination background & drift corrected (deg)" in keys:dec_key="Declination background & drift corrected (deg)"
            else: print("couldn't find declination")
            if "Intensity background + tray corrected  (A/m)" in keys: int_key="Intensity background + tray corrected  (A/m)"
            elif "Intensity background &amp; tray corrected (A/m)" in keys: int_key="Intensity background &amp; tray corrected (A/m)"
            elif "Intensity background & tray corrected (A/m)" in keys:int_key="Intensity background & tray corrected (A/m)"
            elif "Intensity background & drift corrected (A/m)" in keys:int_key="Intensity background & drift corrected (A/m)"
            else: print("couldn't find magnetic moment")
            type_val="Type"
            sect_key="Sect"
            half_key="A/W"
# need to add volume_key to LORE format!
            if "Sample volume (cm^3)" in keys:volume_key="Sample volume (cm^3)"
            elif "Sample volume (cc)" in keys:volume_key="Sample volume (cc)"
            elif "Sample volume (cm&sup3;)" in keys:volume_key="Sample volume (cm&sup3;)"
            elif "Sample volume (cm\xc2\xb3)" in keys:volume_key="Sample volume (cm\xc2\xb3)"
            else: volume_key=""
            for line in indata[1:]:
                InRec={}
                MeasRec,SpecRec,SampRec,SiteRec,LocRec={},{},{},{},{}
                for k in range(len(keys)):InRec[keys[k]]=line.split(',')[k].strip('"')
                inst="IODP-SRM"
                expedition=InRec['Exp']
                location=InRec['Site']+InRec['Hole']
                offsets=InRec[interval_key].split('.') # maintain consistency with er_samples convention of using top interval
                if len(offsets)==1:
                    offset=int(offsets[0])
                else:
                    offset=int(offsets[0])-1
                #interval=str(offset+1)# maintain consistency with er_samples convention of using top interval
                interval=str(offset)# maintain consistency with er_samples convention of using top interval
                specimen=expedition+'-'+location+'-'+InRec['Core']+InRec[type_val]+"-"+InRec[sect_key]+'-'+InRec[half_key]+'-'+str(InRec[interval_key])
                sample = expedition+'-'+location+'-'+InRec['Core']+InRec[type_val]
                site = expedition+'-'+location
                if volume_key in list(InRec.keys()): volume=InRec[volume_key]

                if not InRec[dec_key].strip(""" " ' """) or not InRec[inc_key].strip(""" " ' """):
                    print("No dec or inc found for specimen %s, skipping"%specimen)

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
                    SampRec['azimuth']='0'
                    SampRec['dip']='0'
                    SampRec['method_codes']='FS-C-DRILL-IODP:SO-V'
                    SampRecs.append(SampRec)
                if site!="" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
                    SiteRec['site'] = site
                    SiteRec['location'] = location
                    SiteRec['citations']=citations
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
# set up measurement record - default is NRM
                MeasRec['software_packages']=version_num
                MeasRec["treat_temp"]='%8.3e' % (273) # room temp in kelvin
                MeasRec["meas_temp"]='%8.3e' % (273) # room temp in kelvin
                MeasRec["treat_ac_field"]='0'
                MeasRec["treat_dc_field"]='0'
                MeasRec["treat_dc_field_phi"]='0'
                MeasRec["treat_dc_field_theta"]='0'
                MeasRec["quality"]='g' # assume all data are "good"
                MeasRec["standard"]='u' # assume all data are "good"
                MeasRec["dir_csd"]='0' # assume all data are "good"
                MeasRec["method_codes"]='LT-NO'
                sort_by='treat_ac_field' # set default to AF demag
                if treatment_type in list(InRec.keys()) and InRec[treatment_type]!="":
                    if "AF" in InRec[treatment_type].upper():
                        MeasRec['method_codes'] = 'LT-AF-Z'
                        inst=inst+':IODP-SRM-AF' # measured on shipboard in-line 2G AF
                        treatment_value=float(InRec[demag_key].strip('"'))*1e-3 # convert mT => T
                        MeasRec["treat_ac_field"]=str(treatment_value) # AF demag in treat mT => T
                    elif "T" in InRec[treatment_type].upper():
                        MeasRec['method_codes'] = 'LT-T-Z'
                        inst=inst+':IODP-TDS' # measured on shipboard Schonstedt thermal demagnetizer
                        treatment_value=float(InRec[demag_key].strip('"'))+273 # convert C => K
                        MeasRec["treat_temp"]=str(treatment_value)
                    elif "Lowrie" in InRec['Comments']:
                        MeasRec['method_codes'] = 'LP-IRM-3D'
                        treatment_value=float(InRec[demag_key].strip('"'))+273. # convert C => K
                        MeasRec["treat_temp"]=str(treatment_value)
                        MeasRec["treat_ac_field"]="0"
                        sort_by='treat_temp'
                    elif 'Isothermal' in InRec[treatment_type]:
                        MeasRec['method_codes'] = 'LT-IRM'
                        treatment_value=float(InRec[demag_key].strip('"'))*1e-3 # convert mT => T
                        MeasRec["treat_dc_field"]=str(treatment_value)
                        MeasRec["treat_ac_field"]="0"
                        sort_by='treat_dc_field'
                elif InRec[demag_key]!="0" and InRec[demag_key]!="": #Assume AF if there is no Treatment typ info
                    MeasRec['method_codes'] = 'LT-AF-Z'
                    inst=inst+':IODP-SRM-AF' # measured on shipboard in-line 2G AF
                    treatment_value=float(InRec[demag_key].strip('"'))*1e-3 # convert mT => T
                    MeasRec["treat_ac_field"]=treatment_value # AF demag in treat mT => T
                MeasRec["standard"]='u' # assume all data are "good"
                vol=float(volume)
                if run_key in list(InRec.keys()):
                    run_number=InRec[run_key]
                    MeasRec['external_database_ids']={'LIMS':run_number}
                else:
                    MeasRec['external_database_ids']=""
                MeasRec['description']='sample orientation: '+InRec['Sample orientation']
                MeasRec['dir_inc']=InRec[inc_key].strip('"')
                MeasRec['dir_dec']=InRec[dec_key].strip('"')
                intens= InRec[int_key].strip('"')
                MeasRec['magn_moment']='%8.3e'%(float(intens)*vol) # convert intensity from A/m to Am^2 using vol
                MeasRec['instrument_codes']=inst
                MeasRec['treat_step_num']='1'
                MeasRec['meas_n_orient']=''
                MeasRecs.append(MeasRec)
    if not file_found:
        print("No .csv files were found")
        return False, "No .csv files were found"

    con = nb.Contribution(output_dir_path,read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasSort=sorted(MeasRecs, lambda x,y=None: int(round(float(x[sort_by])-float(y[sort_by]))) if y!=None else 0)
    MeasFixed=pmag.measurements_methods3(MeasSort,noave)
    MeasOuts,keys=pmag.fillkeys(MeasFixed)
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
    # get command line sys.argv

    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwargs['input_dir_path'] = sys.argv[ind+1]
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        kwargs['csv_file']=sys.argv[ind+1]
    if '-WD' in sys.argv:
        ind=sys.argv.index("-WD")
        kwargs['dir_path']=sys.argv[ind+1]
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
    if "-A" in sys.argv: kwargs['noave']=True
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
