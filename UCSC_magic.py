#!/usr/bin/env python
import string,sys,pmag
def convert2meters(alt,units):
    if alt=="0.0000000":return ""
    if units=="meters":
        return alt
    elif units=="feet":
        return str(.3048*float(alt))
def getrec(line):
    c=0
    while line[c]!="<": c+=1
    c1=c
    while line[c1]!=">": c1+=1
    key=line[c+1:c1]
    c2=c1+1
    while line[c2]!="<": c2+=1
    value=line[c1+1:c2]
    return key,value

def parsedate(InDate):
    date_time=InDate.split() # split date into date and time
    d=date_time[0].split('/') # split date into mm dd yyyy
    return d[2]+":"+d[0]+":"+d[1]+":"+date_time[1]+':00.00' # convert to yyyy:mm:dd:hh:mm:ss.ss

def parseloc():
    global k,Data
    while '<locality>' not in Data[k]:k+=1   # look for start of locality
    k+=1
    LocRec={}
    while '<site>' not in Data[k]:  # peel stuff off for locality before first site
        key,value=getrec(Data[k]) # evaluate key for location dictionary
        LocRec[key]=value
        k+=1
    return LocRec

def parsesite():
    global k,Data
    SiteRec={}
    while '<site>' not in Data[k]: 
        k+=1
        if '</locality>' in Data[k]: return 'done'
    k+=1
    while '<sample>' not in Data[k]:
        key,value=getrec(Data[k])
        SiteRec[key]=value
        k+=1
    return SiteRec

def parsespec():
    global k,Data
    k+=1
    SpecRec={}
    while '<step>' not in Data[k]:
        key,value=getrec(Data[k])
        SpecRec[key]=value
        k+=1
    return SpecRec

def parsesteps():
    global k,Data
    MeasRecs=[]
    while '</sample>' not in Data[k]:
        while '<step>' not in Data[k]:k+=1
        k+=1
        MeasRec={}
        while '</step>' not in Data[k]:
            key,value=getrec(Data[k])
            MeasRec[key]=value
            k+=1
        MeasRecs.append(MeasRec)    
        k+=1
    k+=1 
    return MeasRecs

def main():
    """
    NAME
        UCSC_magic.py
 
    DESCRIPTION
        converts UCSC  format files to MagIC formatted files

    SYNTAX
        UCSC_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -f FILE: specify UCSC format input file, required
        -F FILE: specify output file, default is magic_measurements.txt
        -A: don't average replicate measurements
    """
    global k,Data
    k,Data,measNum=0,[],0
    ErLocs,ErSites,ErSamps,ErSpecs,MagRecs=[],[],[],[],[] # MagIC formatted info
# initialize some stuff
    noave=0
    args=sys.argv
    ErLocs,ErSites,ErSamps,ErSpecs,MagicMeas=[],[],[],[],[] # MagIC formatted info
    dir_path='.'
#
# get command line arguments
#
    if '-WD' in args: # set working directory (only for within MagIC.py GUI)
        ind=args.index("-WD")
        dir_path=args[ind+1]
    loc_file,site_file,samp_file,spec_file,meas_file=dir_path+"/er_locations.txt",dir_path+"/er_sites.txt",dir_path+"/er_samples.txt",dir_path+"/er_specimens.txt",dir_path+"/magic_measurements.txt"
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if '-F' in args:
        ind=args.index("-F")
        meas_file=dir_path+'/'+args[ind+1]
    if '-f' in args:
        ind=args.index("-f")
        magfile=dir_path+'/'+args[ind+1]
        try:
            input=open(magfile,'rU')
        except:
            print "bad mag file name"
            sys.exit()
    else: 
        print "mag_file field is required option"
        print main.__doc__
        sys.exit()
    if "-A" in args: noave=1
    InData=input.readlines()
    Data=[]
    for line in InData:
        if line!="\n" and line!="":
            Data.append(line) # strip out annoying blank lines
    LocRec=parseloc() # peel off the location info
    ErLoc={}
    ErLoc['er_location_name']=LocRec['name']
    ErLoc['er_citation_name']="This study"
    ErLoc['location_type']="outcrop"
    ErLoc['location_begin_lat']=LocRec['northLatitude']
    ErLoc['location_begin_lon']=LocRec['eastLongitude']
    ErLoc['location_begin_elevation']=convert2meters(LocRec['altitude'],LocRec['altitudeUnits'])
    ErLoc['location_description']=LocRec['comments']
    ErLocs.append(ErLoc)
    while "</locality>" not in Data[k]:
        ErSite={}
        SiteRec=parsesite()
        if  SiteRec=='done': break
        print SiteRec['name']
        ErSite['er_citation_name']="This study"
        ErSite['er_location_name']=ErLoc['er_location_name']
        ErSite['site_definition']='s' # this means a single site as opposed to composite site
        ErSite['er_site_name']=SiteRec['name']
        ErSite['site_type']=""
        ErSite['site_class']=""
        ErSite['site_lithology']=""
        ErSite['site_lat']=SiteRec['northLatitude']
        ErSite['site_lon']=SiteRec['eastLongitude']
        ErSite['site_elevation']=convert2meters(SiteRec['altitude'],SiteRec['altitudeUnits'])
        ErSite['site_description']=SiteRec['comments']
        ErSites.append(ErSite)
        samples=[] # this is a list for unique sample names
        while '</site>' not in Data[k] and k<len(Data): 
            ErSpec={}
            SpecRec=parsespec()
            print SpecRec['name']
            ErSpec['er_specimen_name']=SpecRec['name']
            ErSpec['er_citation_name']="This study"
            ErSpec['er_location_name']=ErLoc['er_location_name']
            ErSpec['er_citation_names']="This study"
            ErSpec['er_site_name']=ErSite['er_site_name']
            er_sample_name=ErSpec['er_specimen_name'][:-1]
            ErSpec['er_sample_name']=er_sample_name
            ErSpec['specimen_volume']=SpecRec['volume'] # volume in m^3
            ErSpecs.append(ErSpec)
            MeasRecs=parsesteps()
            print len(MeasRecs),' measurements'
            if  er_sample_name not in samples: # new sample name
                samples.append(er_sample_name)
                ErSamp={}
                ErSamp['er_sample_name']=er_sample_name
                ErSamp['er_citation_name']="This study"
                ErSamp['er_location_name']=ErLoc['er_location_name']
                ErSamp['er_site_name']=ErSite['er_site_name']
                ErSamp['sample_lat']=ErSite['site_lat']
                ErSamp['sample_lon']=ErSite['site_lon']
                ErSamp['sample_elevation']=ErSite['site_elevation']
                ErSamp['sample_date']=parsedate(SpecRec['dateCollected'])
#                ErSamp['sample_time_zone']=LocRec['gmtOffset']+"+GMT"
                ErSamp['sample_bed_dip_direction']=str(float(SpecRec['strike'])+90.)
                ErSamp['sample_bed_dip']=SpecRec['dip']
                ErSamp['sample_height']=SpecRec['stratigraphicLevel']
                ErSamp['sample_description']=SpecRec['comments']
                ErSamp['sample_declination_correction']=LocRec['regionalDeclination']
                if 'calculatedSunAz' in SpecRec.keys():
                    ErSamp['sample_azimuth']=SpecRec['calculatedSunAz']
                    ErSamp['magic_method_codes']='SO-SUN'
                az,pl=pmag.get_azpl(float(MeasRecs[0]['coreDec']),float(MeasRecs[0]['coreInc']),float(MeasRecs[0]['geoDec']),float(MeasRecs[0]['geoInc']))
                ErSamp['sample_azimuth']=str(az)
                ErSamp['sample_dip']=str(pl)
                ErSamps.append(ErSamp)
            for MeasRec in MeasRecs:
                MagRec={}
                measNum+=1
                MagRec['er_citation_names']="This study"
                MagRec['measurement_number']='%i'%(measNum)
                MagRec['er_location_name']=ErSpec['er_location_name']
                MagRec['er_site_name']=ErSpec['er_site_name']
                MagRec['er_sample_name']=ErSpec['er_sample_name']
                MagRec['er_specimen_name']=ErSpec['er_specimen_name']
                MagRec['measurement_date']=parsedate(MeasRec['date'])
                MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
                MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
                MagRec["treatment_ac_field"]='0'
                MagRec["treatment_dc_field"]='0'
                MagRec["treatment_dc_field_phi"]='0'
                MagRec["treatment_dc_field_theta"]='0'
                step=MeasRec['stepType']
                if step=='AF':
                    MagRec["magic_method_codes"]="LT-AF-Z" # lab treatment, af in zero field
                    MagRec['magic_experiment_name']=MagRec['er_specimen_name']+":LT-AF-Z"
                elif step=="TH": # I'm guessing here
                    MagRec["magic_method_codes"]="LT-T-Z" # this is "lab treatment, thermal in zero field
                    MagRec['magic_experiment_name']=MagRec['er_specimen_name']+":LT-T-Z"
                else:
                    MagRec["magic_method_codes"]="LT-NO" # no lab treatment - NRM
                    MagRec['magic_experiment_name']=MagRec['er_specimen_name']+":LT-NO"
                MagRec['measurement_dec']=MeasRec['coreDec']
                MagRec['measurement_inc']=MeasRec['coreInc']
                MagRec['measurement_magn_volume']=MeasRec['J'] # intensity in A/m
                MagRec['measurement_magn_moment']=str(float(MeasRec['J'])*float(ErSpec['specimen_volume'])) # intensity in Am^2
                MagRec['measurement_chi_volume']=MeasRec['susceptibility'] # assuming dimensionless SI CHECK THIS
                MagRec['magic_software_packages']=MeasRec['measuringRoutine'] # 
                if step=="AF": MagRec["treatment_ac_field"]=str(1e-3*float(MeasRec['stepLevel'])) # stepLevel in tesla
                if step=="TH": 
                    stepLevel=float(MeasRec['stepLevel']) +273
                    MagRec["treatment_temp"]='%8.3e' % (stepLevel) # treatment step in kelvin
                MagRec["measurement_csd"]=MeasRec['Q_95'] # I think this is the csd
                MagRec["magic_instrument_codes"]='UCSC-'+MeasRec['instrument']
                MagRec["er_analyst_mail_names"]=MeasRec['operator'] 
                MagRec["measurement_flag"]='g' # good measurement flag
                MagRec["measurement_standard"]='u' # # unknown - as opposed to standard
                MagRecs.append(MagRec) 
    pmag.magic_write(loc_file,ErLocs,'er_locations')
    print "results put in ",loc_file
    pmag.magic_write(site_file,ErSites,'er_sites')
    print "results put in ",site_file
    pmag.magic_write(samp_file,ErSamps,'er_samples')
    print "results put in ",samp_file
    pmag.magic_write(spec_file,ErSpecs,'er_specimens')
    print "results put in ",spec_file
    pmag.magic_write(meas_file,MagRecs,'magic_measurements')
    print "results put in ",meas_file
main()
