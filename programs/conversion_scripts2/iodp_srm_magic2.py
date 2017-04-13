#!/usr/bin/env python
import sys
import os
import pmagpy.pmag as pmag

def main(command_line=True, **kwargs):
    """
    NAME
        iodp_srm_magic.py
 
    DESCRIPTION
        converts IODP LIMS and LORE SRM archive half sample format files to magic_measurements format files


    SYNTAX
        iodp_srm_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -f FILE: specify input .csv file, default is all in directory
        -F FILE: specify output  measurements file, default is magic_measurements.txt
        -Fsp FILE: specify output er_specimens.txt file, default is er_specimens.txt
        -Fsa FILE: specify output er_samples.txt file, default is er_samples.txt
        -Fsi FILE: specify output er_sites.txt file, default is er_sites.txt
        -A : don't average replicate measurements
    INPUTS
 	 IODP .csv file format exported from LIMS database
    """
    #        
    # initialize defaults
    version_num=pmag.get_version()
    meas_file='magic_measurements.txt'
    spec_file='er_specimens.txt'
    samp_file='er_samples.txt'
    site_file='er_sites.txt'
    csv_file=''
    ErSpecs,ErSamps,ErSites,ErLocs,ErCits=[],[],[],[],[]
    MagRecs=[]
    citation="This study"
    dir_path,demag='.','NRM'
    args=sys.argv
    noave=0
    depth_method='a'
    # get command line args
    if command_line:
        if '-WD' in args:
            ind=args.index("-WD")
            dir_path=args[ind+1]
        if '-ID' in args:
            ind = args.index('-ID')
            input_dir_path = args[ind+1]
        else:
            input_dir_path = dir_path
        output_dir_path = dir_path
        if "-h" in args:
            print main.__doc__
            return False
        if "-A" in args: noave=1
        if '-f' in args:
            ind=args.index("-f")
            csv_file=args[ind+1] 
        if '-F' in args:
            ind=args.index("-F")
            meas_file=args[ind+1]
        if '-Fsp' in args:
            ind=args.index("-Fsp")
            spec_file = args[ind+1]
        if '-Fsi' in args:
            ind=args.index("-Fsi")
            site_file=args[ind+1]
        if '-Fsa' in args:
            ind=args.index("-Fsa")
            samp_file = args[ind+1]

    if not command_line:
        dir_path = kwargs.get('dir_path', '.')
        input_dir_path = kwargs.get('input_dir_path', dir_path)
        output_dir_path = dir_path # rename dir_path after input_dir_path is set
        noave = kwargs.get('noave', 0) # default (0) is DO average
        csv_file = kwargs.get('csv_file', '')
        meas_file = kwargs.get('meas_file', 'magic_measurements.txt')
        spec_file = kwargs.get('spec_file', 'er_specimens.txt')
        samp_file = kwargs.get('samp_file', 'er_samples.txt')
        site_file = kwargs.get('site_file', 'er_sites.txt')

    # format variables

    meas_file = os.path.join(output_dir_path, meas_file)
    spec_file = os.path.join(output_dir_path, spec_file)
    Specs,file_type = pmag.magic_read(spec_file)
    samp_file = os.path.join(output_dir_path, samp_file)
    ErSamps,file_type = pmag.magic_read(samp_file)
    site_file = os.path.join(output_dir_path, site_file)
    if csv_file=="":
        filelist=os.listdir(input_dir_path) # read in list of files to import
    else:
        csv_file = os.path.join(input_dir_path, csv_file)
        filelist=[csv_file]

    
    # parsing the data
    specimens,samples,sites=[],[],[]
    MagRecs,SpecRecs,SampRecs,SiteRecs=[],[],[],[]
    for samp in ErSamps:
        if samp['er_sample_name'] not in samples:
            samples.append(samp['er_sample_name'])
            SampRecs.append(samp)
    file_found = False
    for f in filelist: # parse each file
        if f[-3:].lower()=='csv':
            file_found = True
            print 'processing: ',f
            full_file = os.path.join(input_dir_path, f)
            file_input=open(full_file,'rU').readlines()
            keys=file_input[0].replace('\n','').split(',') # splits on underscores
            if "Interval Top (cm) on SHLF" in keys:interval_key="Interval Top (cm) on SHLF"
            if " Interval Bot (cm) on SECT" in keys:interval_key=" Interval Bot (cm) on SECT"
            if "Offset (cm)" in keys: interval_key="Offset (cm)"
            if "Top Depth (m)" in keys:depth_key="Top Depth (m)"
            if "CSF-A Top (m)" in keys:depth_key="CSF-A Top (m)" 
            if "Depth CSF-A (m)" in keys:depth_key="Depth CSF-A (m)"
            if "CSF-B Top (m)" in keys: 
                comp_depth_key="CSF-B Top (m)" # use this model if available 
            elif "Depth CSF-B (m)" in keys:
                comp_depth_key="Depth CSF-B (m)"
            else:
                comp_depth_key=""
            if "Demag level (mT)" in keys:demag_key="Demag level (mT)"
            if "Demag Level (mT)" in keys: demag_key="Demag Level (mT)"
            if "Inclination (Tray- and Bkgrd-Corrected) (deg)" in keys:inc_key="Inclination (Tray- and Bkgrd-Corrected) (deg)"
            if "Inclination background + tray corrected  (deg)" in keys:inc_key="Inclination background + tray corrected  (deg)"
            if "Inclination background + tray corrected  (\xc2\xb0)" in keys:inc_key="Inclination background + tray corrected  (\xc2\xb0)"
            if "Inclination background &amp; tray corrected (deg)" in keys:inc_key="Inclination background &amp; tray corrected (deg)"
            if "Declination (Tray- and Bkgrd-Corrected) (deg)" in keys:dec_key="Declination (Tray- and Bkgrd-Corrected) (deg)"
            if "Declination background + tray corrected (deg)" in keys:dec_key="Declination background + tray corrected (deg)"
            if "Declination background + tray corrected (\xc2\xb0)" in keys:dec_key="Declination background + tray corrected (\xc2\xb0)"
            if "Declination background &amp; tray corrected (deg)" in keys:dec_key="Declination background &amp; tray corrected (deg)"
            if "Intensity (Tray- and Bkgrd-Corrected) (A/m)" in keys:int_key="Intensity (Tray- and Bkgrd-Corrected) (A/m)"
            if "Intensity background + tray corrected  (A/m)" in keys:int_key="Intensity background + tray corrected  (A/m)"
            if "Intensity background &amp; tray corrected (A/m)" in keys:int_key="Intensity background &amp; tray corrected (A/m)"
            if "Core Type" in keys:
                core_type="Core Type"
            else: core_type="Type" 
            if 'Run Number' in keys: run_number_key='Run Number'
            if 'Test No.' in keys: run_number_key='Test No.'
            if 'Test Changed On' in keys: date_key='Test Changed On'
            if "Timestamp (UTC)" in keys: date_key="Timestamp (UTC)"
            if "Section" in keys: sect_key="Section"
            if "Sect" in keys: sect_key="Sect"
            if 'Section Half' in keys: half_key='Section Half'
            if "A/W" in keys: half_key="A/W"
            if "Text ID" in keys: text_id="Text ID"
            if "Text Id" in keys: text_id="Text Id"
            for line in file_input[1:]:
              InRec={}
              test=0
              recs=line.split(',')
              for k in range(len(keys)):
                  if len(recs)==len(keys): 
                      InRec[keys[k]]=line.split(',')[k]
              if InRec['Exp']!="": test=1 # get rid of pesky blank lines
              if test==1:
                run_number=""
                inst="IODP-SRM"
                volume='15.59' # set default volume to this
                MagRec,SpecRec,SampRec,SiteRec={},{},{},{}
                expedition=InRec['Exp']
                location=InRec['Site']+InRec['Hole']
# Maintain backward compatibility for the ever-changing LIMS format (Argh!)
                while len(InRec['Core'])<3:
                    InRec['Core']='0'+InRec['Core']
                if "Last Tray Measurment" in InRec.keys() and "SHLF" not in InRec[text_id] or 'dscr' in csv_file :  # assume discrete sample
                    specimen=expedition+'-'+location+'-'+InRec['Core']+InRec[core_type]+"-"+InRec[sect_key]+'-'+InRec[half_key]+'-'+str(InRec[interval_key])
                else: # mark as continuous measurements
                    specimen=expedition+'-'+location+'-'+InRec['Core']+InRec[core_type]+"_"+InRec[sect_key]+InRec[half_key]+'-'+str(InRec[interval_key])
                SpecRec['er_expedition_name']=expedition
                SpecRec['er_location_name']=location
                SpecRec['er_site_name']=specimen
                SpecRec['er_citation_names']=citation
                for key in SpecRec.keys():SampRec[key]=SpecRec[key]
                for key in SpecRec.keys():SiteRec[key]=SpecRec[key]
                SampRec['sample_azimuth']='0'
                SampRec['sample_dip']='0'
                SampRec['sample_core_depth']=InRec[depth_key]
                if comp_depth_key!='':
                    SampRec['sample_composite_depth']=InRec[comp_depth_key]
                if "SHLF" not in InRec[text_id]: 
                    SampRec['magic_method_codes']='FS-C-DRILL-IODP:SP-SS-C:SO-V'
                else:
                    SampRec['magic_method_codes']='FS-C-DRILL-IODP:SO-V'
                SpecRec['er_specimen_name']=specimen
                SpecRec['er_sample_name']=specimen
                SampRec['er_sample_name']=specimen
                SampRec['er_specimen_names']=specimen
                SiteRec['er_specimen_names']=specimen

                for key in SpecRec.keys():MagRec[key]=SpecRec[key]
# set up measurement record - default is NRM 
                #MagRec['er_analyst_mail_names']=InRec['Test Entered By']
                MagRec['magic_software_packages']=version_num
                MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
                MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
                MagRec["treatment_ac_field"]=0
                MagRec["treatment_dc_field"]='0'
                MagRec["treatment_dc_field_phi"]='0'
                MagRec["treatment_dc_field_theta"]='0'
                MagRec["measurement_flag"]='g' # assume all data are "good"
                MagRec["measurement_standard"]='u' # assume all data are "good"
                SpecRec['er_specimen_alternatives']=InRec[text_id]
                if 'Sample Area (cm?)' in InRec.keys() and  InRec['Sample Area (cm?)']!= "": volume=InRec['Sample Area (cm?)']
                if InRec[run_number_key]!= "": run_number=InRec[run_number_key]
                datestamp=InRec[date_key].split() # date time is second line of file
                if '/' in datestamp[0]:
                    mmddyy=datestamp[0].split('/') # break into month day year
                    if len(mmddyy[0])==1: mmddyy[0]='0'+mmddyy[0] # make 2 characters
                    if len(mmddyy[1])==1: mmddyy[1]='0'+mmddyy[1] # make 2 characters
                    if len(datestamp[1])==1: datestamp[1]='0'+datestamp[1] # make 2 characters
                    date='20'+mmddyy[2]+':'+mmddyy[0]+":"+mmddyy[1] +':' +datestamp[1]+":00.00"
                if '-' in datestamp[0]:
                    mmddyy=datestamp[0].split('-') # break into month day year
                    date=mmddyy[0]+':'+mmddyy[1]+":"+mmddyy[2] +':' +datestamp[1]+":00.00"
                MagRec["measurement_date"]=date
                MagRec["magic_method_codes"]='LT-NO'
                if InRec[demag_key]!="0":
                    MagRec['magic_method_codes'] = 'LT-AF-Z'
                    inst=inst+':IODP-SRM-AF' # measured on shipboard in-line 2G AF
                    treatment_value=float(InRec[demag_key].strip('"'))*1e-3 # convert mT => T
                    MagRec["treatment_ac_field"]=treatment_value # AF demag in treat mT => T
                if 'Treatment Type' in InRec.keys() and InRec['Treatment Type']!="":
                    if 'Alternating Frequency' in InRec['Treatment Type']:
                        MagRec['magic_method_codes'] = 'LT-AF-Z'
                        inst=inst+':I`ODP-DTECH' # measured on shipboard Dtech D2000
                        treatment_value=float(InRec['Treatment Value'])*1e-3 # convert mT => T
                        MagRec["treatment_ac_field"]=treatment_value # AF demag in treat mT => T
                    elif 'Thermal' in InRec['Treatment Type']:
                        MagRec['magic_method_codes'] = 'LT-T-Z'
                        inst=inst+':IODP-TDS' # measured on shipboard Schonstedt thermal demagnetizer
                        treatment_value=float(InRec['Treatment Value'])+273 # convert C => K
                        MagRec["treatment_temp"]='%8.3e'%(treatment_value) # 
                MagRec["measurement_standard"]='u' # assume all data are "good"
                vol=float(volume)*1e-6 # convert from cc to m^3
                if run_number!="":
                    MagRec['external_database_ids']=run_number
                    MagRec['external_database_names']='LIMS'
                else:
                    MagRec['external_database_ids']=""
                    MagRec['external_database_names']=''
                MagRec['measurement_inc']=InRec[inc_key].strip('"')
                MagRec['measurement_dec']=InRec[dec_key].strip('"')
                intens= InRec[int_key].strip('"')
                MagRec['measurement_magn_moment']='%8.3e'%(float(intens)*vol) # convert intensity from A/m to Am^2 using vol
                MagRec['magic_instrument_codes']=inst
                MagRec['measurement_number']='1'
                MagRec['measurement_csd']=''
                MagRec['measurement_positions']=''
                MagRecs.append(MagRec)
                if specimen not in specimens:
                    specimens.append(specimen)
                    SpecRecs.append(SpecRec)
                if MagRec['er_sample_name']  not in samples:
                    samples.append(MagRec['er_sample_name'])
                    SampRecs.append(SampRec)
                if MagRec['er_site_name']  not in sites:
                    sites.append(MagRec['er_site_name'])
                    SiteRecs.append(SiteRec)
              #except:
              #   print 'Boo-boo somewhere - no idea where'
    if not file_found:
        print "No .csv files were found"
        return False, "No .csv files were found"
    if len(SpecRecs)>0:
        print 'spec_file', spec_file
        pmag.magic_write(spec_file,SpecRecs,'er_specimens')
        #print 'specimens stored in ',spec_file
    if len(SampRecs)>0:
        SampOut,keys=pmag.fillkeys(SampRecs)
        pmag.magic_write(samp_file,SampOut,'er_samples')
        #print 'samples stored in ',samp_file
    if len(SiteRecs)>0:
        pmag.magic_write(site_file,SiteRecs,'er_sites')
        #print 'sites stored in ',site_file
    MagSort=pmag.sortbykeys(MagRecs,["er_specimen_name","treatment_ac_field"])
    MagOuts=[]
    for MagRec in MagSort:
       MagRec["treatment_ac_field"]='%8.3e'%(MagRec['treatment_ac_field']) # convert to string
       MagOuts.append(MagRec)
    Fixed=pmag.measurements_methods(MagOuts,noave)
    if pmag.magic_write(meas_file,Fixed,'magic_measurements'):
        print 'data stored in ',meas_file
        return True, meas_file
    else:
        print 'no data found.  bad magfile?'
        return False, 'no data found.  bad magfile?'

def do_help():
    return main.__doc__

if __name__ == '__main__':
    main()
