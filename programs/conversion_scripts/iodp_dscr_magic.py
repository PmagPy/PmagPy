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
    -loc HOLE : specify hole name (U1456A)
    -lat LAT: latitude of site (also used as bounding latitude for location)
    -lon LON: longitude of site (also used as bounding longitude for location)
    -A: don't average replicate measurements
INPUTS
     IODP discrete sample .csv file format exported from LIMS database
"""
import sys, os
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb
from pandas import DataFrame

def main(**kwargs):
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

    # format variables
    if csv_file=="":
        filelist=os.listdir(input_dir_path) # read in list of files to import
    else:
        csv_file = os.path.join(input_dir_path, csv_file)
        filelist=[csv_file]

    # parsing the data
    file_found = False
    MeasRecs,SpecRecs,SampRecs,SiteRecs,LocRecs=[],[],[],[],[]
    for fin in filelist: # parse each file
        if fin[-3:].lower()=='csv':
            file_found = True
            print 'processing: ',fin
            indata=open(fin,'rU').readlines()
            keys=indata[0].replace('\n','').split(',') # splits on underscores
            interval_key="Offset (cm)"
            demag_key="Demag level (mT)"
            offline_demag_key="Treatment Value (mT or &deg;C)"
            offline_treatment_type="Treatment type"
            run_key="Test No."
            if "Inclination background + tray corrected  (deg)" in keys: inc_key="Inclination background + tray corrected  (deg)"
            if "Inclination background &amp; tray corrected (deg)" in keys: inc_key="Inclination background &amp; tray corrected (deg)"
            if "Declination background + tray corrected (deg)" in keys: dec_key="Declination background + tray corrected (deg)"
            if "Declination background &amp; tray corrected (deg)" in keys: dec_key="Declination background &amp; tray corrected (deg)"
            if "Intensity background + tray corrected  (A/m)" in keys: int_key="Intensity background + tray corrected  (A/m)"
            if "Intensity background &amp; tray corrected (A/m)" in keys: int_key="Intensity background &amp; tray corrected (A/m)"
            type_val="Type"
            sect_key="Sect"
            half_key="A/W"
# need to add volume_key to LORE format!
            if "Sample volume (cm^3)" in keys:volume_key="Sample volume (cm^3)"
            if "Sample volume (cc)" in keys:volume_key="Sample volume (cc)"
            if "Sample volume (cm&sup3;)" in keys:volume_key="Sample volume (cm&sup3;)"
            for line in indata[1:]:
                InRec={}
                MeasRec,SpecRec,SampRec,SiteRec,LocRec={},{},{},{},{}
                for k in range(len(keys)):InRec[keys[k]]=line.split(',')[k]
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
                specimen=expedition+'-'+location+'-'+InRec['Core']+InRec[type_val]+"-"+InRec[sect_key]+'_'+InRec[half_key]+'_'+interval
                sample = expedition+'-'+location+'-'+InRec['Core']+InRec[type_val]+"_"+InRec[sect_key]+InRec[half_key]
                site = expedition+'-'+location

                if not InRec[dec_key].strip(""" " ' """) or not InRec[inc_key].strip(""" " ' """):
                    print("No dec or inc found for specimen %s, skipping"%specimen)

                if specimen!="" and specimen not in map(lambda x: x['specimen'] if 'specimen' in x.keys() else "", SpecRecs):
                    SpecRec['specimen'] = specimen
                    SpecRec['sample'] = sample
                    SpecRec['citations']=citation
                    SpecRecs.append(SpecRec)
                if sample!="" and sample not in map(lambda x: x['sample'] if 'sample' in x.keys() else "", SampRecs):
                    SampRec['sample'] = sample
                    SampRec['site'] = site
                    SampRec['citations']=citation
                    SampRec['azimuth']='0'
                    SampRec['dip']='0'
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
                volume=InRec[volume_key]
                MeasRec["method_codes"]='LT-NO'
                sort_by='treat_ac_field' # set default to AF demag
                if InRec[demag_key]!="0":
                    MeasRec['method_codes'] = 'LT-AF-Z'
                    inst=inst+':IODP-SRM-AF' # measured on shipboard in-line 2G AF
                    treatment_value=float(InRec[demag_key].strip('"'))*1e-3 # convert mT => T
                    if sort_by =="treat_ac_field":
                        MeasRec["treat_ac_field"]=treatment_value # AF demag in treat mT => T
                    else:
                        MeasRec["treat_ac_field"]=str(treatment_value)# AF demag in treat mT => T
                elif offline_treatment_type in InRec.keys() and InRec[offline_treatment_type]!="":
                    if "Lowrie" in InRec['Comments']:
                        MeasRec['method_codes'] = 'LP-IRM-3D'
                        treatment_value=float(InRec[offline_demag_key].strip('"'))+273. # convert C => K
                        MeasRec["treat_temp"]=treatment_value
                        MeasRec["treat_ac_field"]="0"
                        sort_by='treat_temp'
                    elif 'Isothermal' in InRec[offline_treatment_type]:
                        MeasRec['method_codes'] = 'LT-IRM'
                        treatment_value=float(InRec[offline_demag_key].strip('"'))*1e-3 # convert mT => T
                        MeasRec["treat_dc_field"]=treatment_value
                        MeasRec["treat_ac_field"]="0"
                        sort_by='treat_dc_field'
                MeasRec["standard"]='u' # assume all data are "good"
                vol=float(volume)*1e-6 # convert from cc to m^3
                if run_key in InRec.keys():
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
                MeasRec['number']='1'
                MeasRec['meas_n_orient']=''
                MeasRecs.append(MeasRec)
    if not file_found:
        print "No .csv files were found"
        return False, "No .csv files were found"

    MagOuts=[]
    for spec in Specs:
        Speclist=pmag.get_dictitem(MeasRecs,'specimen',spec,'T')
        sortedSpeclist=pmag.sort_diclist(Speclist,sort_by)
        for rec in sortedSpeclist:
            for key in rec.keys(): rec[key]=str(rec[key])
            MagOuts.append(rec)
    Fixed=pmag.measurements_methods3(MagOuts,noave)
    Out,keys=pmag.fillkeys(Fixed)

    con = nb.Contribution(output_dir_path,read_tables=[])

    con.add_empty_magic_table('specimens')
    con.add_empty_magic_table('samples')
    con.add_empty_magic_table('sites')
    con.add_empty_magic_table('locations')
    con.add_empty_magic_table('measurements')

    con.tables['specimens'].df = DataFrame(SpecRecs)
    con.tables['samples'].df = DataFrame(SampRecs)
    con.tables['sites'].df = DataFrame(SiteRecs)
    con.tables['locations'].df = DataFrame(LocRecs)
    con.tables['measurements'].df = DataFrame(Out)

    con.tables['specimens'].write_magic_file(custom_name=spec_file)
    con.tables['samples'].write_magic_file(custom_name=samp_file)
    con.tables['sites'].write_magic_file(custom_name=site_file)
    con.tables['locations'].write_magic_file(custom_name=loc_file)
    con.tables['measurements'].write_magic_file(custom_name=meas_file)

    return True, meas_file

def do_help():
    return __doc__

if __name__ == '__main__':
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

    main(**kwargs)
