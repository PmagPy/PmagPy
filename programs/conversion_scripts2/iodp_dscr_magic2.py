#!/usr/bin/env python
import sys
import os
import pmagpy.pmag as pmag

def main(command_line=True, **kwargs):
    """
    NAME
        iodp_dscr_magic.py
 
    DESCRIPTION
        converts ODP LIMS discrete sample format files to magic_measurements format files


    SYNTAX
        iodp_descr_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -f FILE: specify input .csv file, default is all in directory
        -F FILE: specify output  measurements file, default is magic_measurements.txt
        -A : don't average replicate measurements
    INPUTS
 	 IODP discrete sample .csv file format exported from LIMS database
    """
    #        
    # initialize defaults
    version_num=pmag.get_version()
    meas_file='magic_measurements.txt'
    csv_file=''
    MagRecs,Specs=[],[]
    citation="This study"
    dir_path,demag='.','NRM'
    args=sys.argv
    noave=0
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

    if not command_line:
        dir_path = kwargs.get('dir_path', '.')
        input_dir_path = kwargs.get('input_dir_path', dir_path)
        output_dir_path = dir_path # rename dir_path after input_dir_path is set
        noave = kwargs.get('noave', 0) # default (0) is DO average
        csv_file = kwargs.get('csv_file', '')
        meas_file = kwargs.get('meas_file', 'magic_measurements.txt')

    # format variables

    meas_file= os.path.join(output_dir_path, meas_file)
    if csv_file=="":
        filelist=os.listdir(input_dir_path) # read in list of files to import
    else:
        csv_file = os.path.join(input_dir_path, csv_file)
        filelist=[csv_file]
    # parsing the data
    file_found = False
    for file in filelist: # parse each file
        if file[-3:].lower()=='csv':
            file_found = True
            print 'processing: ',file
            input=open(file,'rU').readlines()
            keys=input[0].replace('\n','').split(',') # splits on underscores
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
            type="Type" 
            sect_key="Sect"
            half_key="A/W"
# need to add volume_key to LORE format! 
            if "Sample volume (cm^3)" in keys:volume_key="Sample volume (cm^3)"
            if "Sample volume (cc)" in keys:volume_key="Sample volume (cc)"
            if "Sample volume (cm&sup3;)" in keys:volume_key="Sample volume (cm&sup3;)"
            for line in input[1:]:
                InRec={}
                for k in range(len(keys)):InRec[keys[k]]=line.split(',')[k]
                inst="IODP-SRM"
                MagRec={}
                expedition=InRec['Exp']
                location=InRec['Site']+InRec['Hole']
                offsets=InRec[interval_key].split('.') # maintain consistency with er_samples convention of using top interval
                if len(offsets)==1:
                    offset=int(offsets[0])
                else:
                    offset=int(offsets[0])-1
                #interval=str(offset+1)# maintain consistency with er_samples convention of using top interval
                interval=str(offset)# maintain consistency with er_samples convention of using top interval
                specimen=expedition+'-'+location+'-'+InRec['Core']+InRec[type]+"-"+InRec[sect_key]+'_'+InRec[half_key]+'_'+interval
                if specimen not in Specs:Specs.append(specimen)
                MagRec['er_expedition_name']=expedition
                MagRec['er_location_name']=location
                MagRec['er_site_name']=specimen
                MagRec['er_citation_names']=citation
                MagRec['er_specimen_name']=specimen
                MagRec['er_sample_name']=specimen
                MagRec['er_site_name']=specimen
# set up measurement record - default is NRM 
                MagRec['magic_software_packages']=version_num
                MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
                MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
                MagRec["treatment_ac_field"]='0'
                MagRec["treatment_dc_field"]='0'
                MagRec["treatment_dc_field_phi"]='0'
                MagRec["treatment_dc_field_theta"]='0'
                MagRec["measurement_flag"]='g' # assume all data are "good"
                MagRec["measurement_standard"]='u' # assume all data are "good"
                MagRec["measurement_csd"]='0' # assume all data are "good"
                volume=InRec[volume_key]
                MagRec["magic_method_codes"]='LT-NO'
                sort_by='treatment_ac_field' # set default to AF demag
                if InRec[demag_key]!="0":
                    MagRec['magic_method_codes'] = 'LT-AF-Z'
                    inst=inst+':IODP-SRM-AF' # measured on shipboard in-line 2G AF
                    treatment_value=float(InRec[demag_key].strip('"'))*1e-3 # convert mT => T
                    if sort_by =="treatment_ac_field":
                        MagRec["treatment_ac_field"]=treatment_value # AF demag in treat mT => T
                    else:
                        MagRec["treatment_ac_field"]=str(treatment_value)# AF demag in treat mT => T
                elif offline_treatment_type in InRec.keys() and InRec[offline_treatment_type]!="":
                    if "Lowrie" in InRec['Comments']:   
                        MagRec['magic_method_codes'] = 'LP-IRM-3D'
                        treatment_value=float(InRec[offline_demag_key].strip('"'))+273. # convert C => K
                        MagRec["treatment_temp"]=treatment_value 
                        MagRec["treatment_ac_field"]="0"
                        sort_by='treatment_temp'
                    elif 'Isothermal' in InRec[offline_treatment_type]:
                        MagRec['magic_method_codes'] = 'LT-IRM'
                        treatment_value=float(InRec[offline_demag_key].strip('"'))*1e-3 # convert mT => T
                        MagRec["treatment_dc_field"]=treatment_value 
                        MagRec["treatment_ac_field"]="0"
                        sort_by='treatment_dc_field'
                MagRec["measurement_standard"]='u' # assume all data are "good"
                vol=float(volume)*1e-6 # convert from cc to m^3
                if run_key in InRec.keys():
                    run_number=InRec[run_key]
                    MagRec['external_database_ids']=run_number
                    MagRec['external_database_names']='LIMS'
                else:
                    MagRec['external_database_ids']=""
                    MagRec['external_database_names']=''
                MagRec['measurement_description']='sample orientation: '+InRec['Sample orientation'] 
                MagRec['measurement_inc']=InRec[inc_key].strip('"')
                MagRec['measurement_dec']=InRec[dec_key].strip('"')
                intens= InRec[int_key].strip('"')
                MagRec['measurement_magn_moment']='%8.3e'%(float(intens)*vol) # convert intensity from A/m to Am^2 using vol
                MagRec['magic_instrument_codes']=inst
                MagRec['measurement_number']='1'
                MagRec['measurement_positions']=''
                MagRecs.append(MagRec)
    if not file_found:
        print "No .csv files were found"
        return False, "No .csv files were found"
    MagOuts=[]
    for spec in Specs:
        Speclist=pmag.get_dictitem(MagRecs,'er_specimen_name',spec,'T')
        sorted=pmag.sort_diclist(Speclist,sort_by)    
        for rec in sorted:
            for key in rec.keys(): rec[key]=str(rec[key])
            MagOuts.append(rec)
    Fixed=pmag.measurements_methods(MagOuts,noave)
    Out,keys=pmag.fillkeys(Fixed)
    if pmag.magic_write(meas_file,Out,'magic_measurements'):
        print 'data stored in ',meas_file
        return True, meas_file
    else:
        print 'no data found.  bad magfile?'
        return False, 'no data found.  bad magfile?'

def do_help():
    return main.__doc__

if __name__ == '__main__':
    main()
