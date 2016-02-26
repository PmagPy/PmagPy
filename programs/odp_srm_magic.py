#!/usr/bin/env python
import sys
import os
import pmagpy.pmag as pmag

def main():
    """
    NAME
        odp_srm_magic.py
 
    DESCRIPTION
        converts ODP measurement format files to magic_measurements format files

    SYNTAX
        odp_srm_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -F FILE: specify output  measurements file, default is magic_measurements.txt
        -Fsa FILE: specify output er_sample.txt file, default is er_sample.txt
        -A : don't average replicate measurements
    INPUT
        put data from a single core into a directory. depths will be below core top

    """
#        
#
    version_num=pmag.get_version()
    meas_file='magic_measurements.txt'
    samp_file='er_samples.txt'
    ErSpecs,ErSamps,ErSites,ErLocs,ErCits=[],[],[],[],[]
    MagRecs=[]
    citation="This study"
    dir_path,demag='.','NRM'
    args=sys.argv
    noave=0,
    if '-WD' in args:
        ind=args.index("-WD")
        dir_path=args[ind+1]
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-A" in args: noave=1
    if '-F' in args:
        ind=args.index("-F")
        meas_file=args[ind+1]
    if '-Fsa' in args:
        ind=args.index("-Fsa")
        samp_file=args[ind+1]
    if '-LP' in args:
        ind=args.index("-LP")
        codelist=args[ind+1]
        codes=codelist.split(':')
        if "AF" in codes:
            demag='AF' 
            if'-dc' not in args: methcode="LT-AF-Z"
            if'-dc' in args: methcode="LT-AF-I"
        if "T" in codes:
            demag="T"
            if '-dc' not in args: methcode="LT-T-Z"
            if '-dc' in args: methcode="LT-T-I"
        if "I" in codes:
            methcode="LP-IRM"
        if "S" in codes: 
            demag="S"
            methcode="LP-PI-TRM:LP-PI-ALT-AFARM"
            trm_labfield=labfield
            ans=raw_input("DC lab field for ARM step: [50uT] ")
            if ans=="":
                arm_labfield=50e-6
            else: 
                arm_labfield=float(ans)*1e-6
            ans=raw_input("temperature for total trm step: [600 C] ")
            if ans=="":
                trm_peakT=600+273 # convert to kelvin
            else: 
                trm_peakT=float(ans)+273 # convert to kelvin
        if "G" in codes: methcode="LT-AF-G"
	if "D" in codes: methcode="LT-AF-D"
        if "TRM" in codes: 
            demag="T"
            trm=1
    if demag=="T" and "ANI" in codes:
        methcode="LP-AN-TRM"
    if demag=="AF" and "ANI" in codes:
        methcode="LP-AN-ARM"
        if labfield==0: labfield=50e-6
        if peakfield==0: peakfield=.180
    samp_file=dir_path+'/'+samp_file
    meas_file=dir_path+'/'+meas_file
    filelist=os.listdir(dir_path) # read in list of files to import
    specimens,samples,sites=[],[],[]
    MagRecs,SpecRecs,SampRecs=[],[],[]
    for file in filelist: # parse each file
        if file[-3:].lower()=='srm':
            print 'processing: ',file
            Nfo=file.split('_')[0].split('-')
            try:
                sect=int(Nfo[3][:-1])
            except:
                sect=1
            input=open(file,'rU').readlines()
            MagRec,SpecRec,SampRec={},{},{}
            alt_spec,treatment_type,treatment_value,user="","","",""
            inst="ODP-SRM"
            SampRec['sample_azimuth']='0'
            SampRec['sample_dip']='0'
            SampRec['magic_method_code']='FS-C-DRILL-IODP:SP-SS-C'
            MagRec['er_analyst_mail_names']=user
            MagRec['magic_method_codes']='LT-NO'
            MagRec['magic_software_packages']=version_num
            MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["treatment_ac_field"]='0'
            MagRec["treatment_dc_field"]='0'
            MagRec["treatment_dc_field_phi"]='0'
            MagRec["treatment_dc_field_theta"]='0'
            MagRec["measurement_flag"]='g' # assume all data are "good"
            MagRec["measurement_standard"]='u' # assume all data are "good"
            MagRec["measurement_csd"]='' # set csd to blank
            SpecRec['er_specimen_alternatives']=alt_spec
            vol=7e-6 # assume 7 cc samples
            datestamp=input[1].split() # date time is second line of file
            mmddyy=datestamp[0].split('/') # break into month day year
            date=mmddyy[2]+':'+mmddyy[0]+":"+mmddyy[1] +':' +datestamp[1]
            MagRec["measurement_date"]=date
            treatment_value,inst="","ODP-SRM"
            k=0
            while 1:
                fields= input[k].replace('\n','').split("=")
                if 'treatment_type' in fields[0]:
                    if "Alternating Frequency Demagnetization" in fields[1]:
                        MagRec['magic_method_codes'] = 'LT-AF-Z'
                        inst=inst+':ODP-DTECH' # measured on shipboard AF DTECH D2000
                if "treatment_value" in fields[0]:
                    value=fields[1]
                    if value!=" ":
                        treatment_value=float(value)*1e-3
                        MagRec["treatment_ac_field"]='%8.3e'%(treatment_value) # AF demag in treat mT => T
                if 'user' in fields[0]: 
                    user=fields[-1]
                    MagRec["er_analyst_mail_names"]=user
                MagRec["measurement_standard"]='u' # assume all data are "good"
                if 'sample_area' in fields[0]:  vol=float(fields[1])*1e-6 # takes volume (cc) and converts to m^3
                if 'run_number' in fields[0]:  
                    MagRec['external_database_ids']=fields[1] # run number is the LIMS measurement number
                    MagRec['external_database_names']='LIMS'
                k+=1
                if input[k][0:7]=='<MULTI>': 
                    break 
            while 1:
                k+=1
                line = input[k]
                if line[0:5]=='<RAW>': 
                    break 
                treatment_value=""
                rec=line.replace('\n','').split(',') # list of data
                if len(rec)>2:
                    MeasRec,SampRec={},{'core_depth':'0','er_sample_name':'0','er_site_name':'0','er_location_name':'location'}
                    for key in MagRec.keys():MeasRec[key]=MagRec[key]
                    for item in rec:
                             items=item.split('=')
                             if 'demag_level' in items[0]:
                                treat= float(items[1])
                                if treat!=0:
                                    MeasRec['magic_method_codes']='LT-AF-Z'
                                    inst=inst+':ODP-SRM-AF'
                                    MeasRec["treatment_ac_field"]='%8.3e'%(treat*1e-3) # AF demag in treat mT => T
                             if 'inclination_w_tray_w_bkgrd' in items[0]: MeasRec['measurement_inc']=items[1]
                             if 'declination_w_tray_w_bkgrd' in items[0]: MeasRec['measurement_dec']=items[1]
                             if 'intensity_w_tray_w_bkgrd' in items[0]: MeasRec['measurement_magn_moment']='%8.3e'%(float(items[1])*vol) # convert intensity from A/m to Am^2 using vol
                             MeasRec['magic_instrument_codes']=inst
                             if 'offset' in items[0]:
                                 depth='%7.3f'%(float(sect-1)*1.5+float(items[1]))
                                 SampRec['core_depth']=depth
                                 MeasRec['er_specimen_name']=depth
                                 MeasRec['er_sample_name']=depth
                                 MeasRec['er_site_name']=depth
                                 MeasRec['er_location_name']='location'
                                 SampRec['er_sample_name']=depth
                                 SampRec['er_site_name']=depth
                                 SampRec['er_location_name']='location'
                                 MeasRec['measurement_number']='1'
                    SampRecs.append(SampRec)
                    MagRecs.append(MeasRec)
    pmag.magic_write(samp_file,SampRecs,'er_samples')
    print 'samples stored in ',samp_file
    Fixed=pmag.measurements_methods(MagRecs,noave)
    pmag.magic_write(meas_file,Fixed,'magic_measurements')
    print 'data stored in ',meas_file

if __name__ == "__main__":
    main()
