#!/usr/bin/env python
import sys
import os
import pmagpy.pmag as pmag

def main():
    """
    NAME
        odp_dcs_magic.py
 
    DESCRIPTION
        converts ODP discrete sample format files to magic_measurements format files

    SYNTAX
        odp_dsc_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -F FILE: specify output  measurements file, default is magic_measurements.txt
        -Fsp FILE: specify output er_specimens.txt file, default is er_specimens.txt
        -Fsa FILE: specify output er_samples.txt file for appending, default is er_samples.txt
        -Fsi FILE: specify output er_sites.txt file, default is er_sites.txt
        -dc B PHI THETA: dc lab field (in micro tesla) and phi,theta, default is none
              NB: use PHI, THETA = -1 -1 to signal that it changes, i.e. in anisotropy experiment
        -ac B : peak AF field (in mT) for ARM acquisition, default is none
        -A : don't average replicate measurements
    INPUT
        Put data from separate experiments (all AF, thermal, thellier, trm aquisition, Shaw, etc.)  in separate directory

    """
#        
#
    version_num=pmag.get_version()
    meas_file='magic_measurements.txt'
    spec_file='er_specimens.txt'
    samp_file='er_samples.txt'
    site_file='er_sites.txt'
    ErSpecs,ErSamps,ErSites,ErLocs,ErCits=[],[],[],[],[]
    MagRecs=[]
    citation="This study"
    dir_path,demag='.','NRM'
    args=sys.argv
    noave=0
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
    if '-Fsp' in args:
        ind=args.index("-Fsp")
        spec_file=args[ind+1]
    if '-Fsa' in args:
        ind=args.index("-Fsa")
        samp_file=dir_path+'/'+args[ind+1]
        ErSamps,file_type=pmag.magic_read(samp_file)
    else:
        samp_file=dir_path+'/'+samp_file
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
    spec_file=dir_path+'/'+spec_file
    site_file=dir_path+'/'+site_file
    meas_file=dir_path+'/'+meas_file
    filelist=os.listdir(dir_path) # read in list of files to import
    specimens,samples,sites=[],[],[]
    MagRecs,SpecRecs,SampRecs=[],[],[]
    for samp in ErSamps:
        if samp['er_sample_name'] not in samples:
            samples.append(samp['er_sample_name'])
            SampRecs.append(samp)
    for file in filelist: # parse each file
        if file[-3:].lower()=='dsc':
            print 'processing: ',file
            MagRec,SpecRec,SampRec={},{},{}
            treatment_type,treatment_value,user="","",""
            inst="ODP-SRM"
            input=open(dir_path+'/'+file,'rU').readlines()
            IDs=file.split('_') # splits on underscores
            pieces=IDs[0].split('-')
            expedition=pieces[0]
            location=pieces[1]
            if file[0]!='_':
                while len(pieces[2])<4:pieces[2]='0'+pieces[2] # pad core to be 3 characters
                specimen=""
            else:
                specimen="test"
            for piece in pieces:
                specimen=specimen+piece+'-'
            specimen=specimen[:-1]
            alt_spec=IDs[1] # alternate specimen is second field in field name
# set up specimen record for Er_specimens table
            SpecRec['er_expedition_name']=expedition
            SpecRec['er_location_name']=location
            SpecRec['er_site_name']=specimen
            SpecRec['er_sample_name']=specimen
            SpecRec['er_citation_names']=citation
            for key in SpecRec.keys():SampRec[key]=SpecRec[key]
            SampRec['sample_azimuth']='0'
            SampRec['sample_dip']='0'
            SampRec['magic_method_codes']='FS-C-DRILL-IODP:SP-SS-C:SO-V'
            SpecRec['er_specimen_name']=specimen
            SampRec['er_specimen_names']=specimen
            for key in SpecRec.keys():MagRec[key]=SpecRec[key]
# set up measurement record - default is NRM 
            MagRec['er_analyst_mail_names']=user
            MagRec['magic_method_codes']='LT-NO'
            MagRec['magic_software_packages']=version_num
            MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["treatment_ac_field"]=0.
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
            for k in range(len(input)):
                fields= input[k].split("=")
                if 'treatment_type' in fields[0]:
                    if "Alternating Frequency Demagnetization" in fields[1]:
                        MagRec['magic_method_codes'] = 'LT-AF-Z'
                        inst=inst+':ODP-DTECH' # measured on shipboard AF DTECH D2000
                        treatment_type="AF"
                    if "Anhysteretic Remanent Magnetization" in fields[1]:
                        MagRec['magic_method_codes'] = 'LT-AF-I'
                        inst=inst+':ODP-DTECH' # measured on shipboard AF DTECH D2000
                        treatment_type="ARM"
                    if "Isothermal Remanent Magnetization" in fields[1]:
                        MagRec['magic_method_codes'] = 'LT-IRM'
                        inst=inst+':ODP-IMP' # measured on shipboard ASC IMPULSE magnetizer
                        treatment_type="IRM"
                if "treatment_value" in fields[0]:
                    values=fields[1].split(',')
                    value=values[0]
                    if value!=" \n":
                        if treatment_type=="AF":
                            treatment_value=float(value)*1e-3
                            MagRec["treatment_ac_field"]=treatment_value # AF demag in treat mT => T
                        elif treatment_type=="IRM":
                            treatment_value=float(value)*1e-3
                            MagRec["treatment_dc_field"]='%8.3e'%(treatment_value) # IRM treat mT => T
                        if treatment_type=="ARM":
                            treatment_value=float(value)*1e-3
                            dc_value=float(values[1])*1e-3
                            MagRec["treatment_ac_field"]=treatment_value # AF demag in treat mT => T
                            MagRec["treatment_dc_field"]='%8.3e'%(dc_value) # DC mT => T
                if 'user' in fields[0]: 
                    user=fields[-1]
                    MagRec["er_analyst_mail_names"]=user
                if 'sample_orientation' in fields[0]: 
                    MagRec["measurement_description"]=fields[-1]
                MagRec["measurement_standard"]='u' # assume all data are "good"
                if 'sample_area' in fields[0]:  vol=float(fields[1])*1e-6 # takes volume (cc) and converts to m^3
                if 'run_number' in fields[0]:  
                    MagRec['external_database_ids']=fields[1] # run number is the LIMS measurement number
                    MagRec['external_database_names']='LIMS'
                if input[k][0:7]=='<MULTI>':
                    rec=input[k+1].split(',') # list of data
                    for item in rec:
                        items=item.split('=')
                        if items[0].strip()=='demag_level' and  treatment_value=="" :
                            treat= float(items[1])
                            if treat!=0:
                                MagRec['magic_method_codes']='LT-AF-Z'
                                inst=inst+':ODP-SRM-AF'
                                MagRec["treatment_ac_field"]=treat*1e-3 # AF demag in treat mT => T
                        if items[0].strip()=='inclination_w_tray_w_bkgrd': MagRec['measurement_inc']=items[1]
                        if items[0].strip()=='declination_w_tray_w_bkgrd': MagRec['measurement_dec']=items[1]
                        if items[0].strip()=='intensity_w_tray_w_bkgrd': MagRec['measurement_magn_moment']='%8.3e'%(float(items[1])*vol) # convert intensity from A/m to Am^2 using vol
                        if items[0].strip()=='x_stdev':MagRec['measurement_x_sd']=items[1]
                        if items[0].strip()=='y_stdev':MagRec['measurement_y_sd']=items[1]
                        if items[0].strip()=='z_stdev':MagRec['measurement_sd_z']=items[1]
                        MagRec['magic_instrument_codes']=inst
                        MagRec['measurement_number']='1'
                        MagRec['measurement_positions']=''
            MagRecs.append(MagRec)
            if specimen not in specimens:
                specimens.append(specimen)
                SpecRecs.append(SpecRec)
            if MagRec['er_sample_name'] not in samples:
                samples.append(MagRec['er_sample_name'])
                SampRecs.append(SampRec)
    MagOuts=pmag.sort_diclist(MagRecs,'treatment_ac_field')
    for MagRec in MagOuts:
        MagRec["treatment_ac_field"]='%8.3e'%(MagRec["treatment_ac_field"]) # convert to string
    pmag.magic_write(spec_file,SpecRecs,'er_specimens')
    if len(SampRecs)>0:
        SampOut,keys=pmag.fillkeys(SampRecs)
        pmag.magic_write(samp_file,SampOut,'er_samples')
        print 'samples stored in ',samp_file
    pmag.magic_write(samp_file,SampRecs,'er_samples')
    print 'specimens stored in ',spec_file
    
    Fixed=pmag.measurements_methods(MagOuts,noave)
    pmag.magic_write(meas_file,Fixed,'magic_measurements')
    print 'data stored in ',meas_file

if __name__ == "__main__":
    main()
