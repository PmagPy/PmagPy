#!/usr/bin/env python
import sys,os
from pmagpy import pmag
from pmagpy import contribution_builder as cb
#from datacite import DataCiteMDSClient
from habanero import Crossref
import datetime
from datetime import timedelta
import time as t
import dateutil.parser

def main():
    """
    NAME
      magic_geomagia.py

    DESCRIPTION
       Takes a MagIC file and outputs data for easier input into Max Brown's GEOMAGIA database

       Requires the habanero python package to be installed. Try "pip install habanero" if you
       get a "ModuleNotFoundError: No module named 'habanero'" error.

    SYNTAX
       magic_geomagia.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -f FILE: the MagIC data file name that will be converted to GEOMAGIA files
    
    OUTPUT:
       Print to standard out the GEOMAGIA insert command for the reference and the site level data 

    EXAMPLE:
        magic_geomagia.py -f magic_contribution_16578.txt

        Nick Jarboe
    """
    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit

    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file_name=sys.argv[ind+1]
    else:
        print("MagIC file name needed. Please add the file name after the -f option.")
        sys.exit()


#   Create all the table files from the magic.txt file so they can be imported by the cb
    command = "download_magic.py -f " + file_name
    os.system(command)

    md = cb.Contribution()  #md stands for magic file data
    md.propagate_location_to_measurements()
    md.propagate_location_to_specimens()
    md.propagate_location_to_samples()
    if not md.tables:
        print('-E- No MagIC tables could be found in this directory')
        error_log("No MagIC tables found")
        return

    doi=md.tables['contribution'].df.iloc[0]['reference']
    id=md.tables['contribution'].df.iloc[0]['id']
    timestamp=md.tables['contribution'].df.iloc[0]['timestamp']
    contributor=md.tables['contribution'].df.iloc[0]['contributor']
    print("c=",contributor)
    contributor=contributor.replace('@','')
    print("c=",contributor)
   
    cr = Crossref()
    ref=cr.works(doi)
    
#    authors = "Doe J.X., Alexander,T.G."
    status= ref["status"]
    message= ref["message"]
#    print("message=",message)
    authors= message["author"]
#    print("authors=",authors)
    authorList=""
    for author in authors:
#        print ("Name:",author['given'], author['family']) 
        author_given=""
        names=author['given'].split(' ')
        for name in names:
            author_given +=name[0]+"."
        authorList += author['family'] + " " + author_given + ", " 
#    print(authorList)
    authorList=authorList[:-2]
#    print(authorList)

    title = message['title'][0]
    year = message['created']['date-parts'][0][0]
#    print(year)
    journal = message['short-container-title'][0]
    volume = message['volume']
#    print(volume)
    pages='0'
    if "page" in message.keys():
        pages = message['page']
#    print(pages)
    url = "https://earthref.org/MagIC/doi/" + doi

    print("REFS") 
    print("Insert into REFS values(NULL,'", authorList, "','", title, "', ", year, ", '", journal, "', ", volume, ", '", pages, "', '", doi, "', '", url, "');", sep='')
    
    print()
    print("ARCHEODIJ") 
    
    sites=md.tables['sites'].df
    locations=md.tables['locations'].df

    print("UID,NUM_SAMPLES,NUM_ACC_SPEC,NUM_MEAS_SPEC,BA,SIGMA_BA,AGE, AGE_MIN,AGE_MAX,NUM_SIGMAS,AGE_ERROR_TYPE_ID,SITE_LAT, SITE_LON,VADM,SIGMA_VADM,SITE_ID,PI_METHODS_ID,AC_ID,MD_CK_ ID,AN_CORR_ID,CR_CORR_ID,DM_METHOD_ID,AF_STEP,T_STEP,DM_ ANALYSIS_ID,SPECIMEN_TYPE_ID,MATERIAL_ID,REFERENCE_ID,NUM_ C14_SAMPLES,C14_ID,CALIB_C14_AGE,CALIB_C14_AGE_SIGMA_MIN, CALIB_C14_AGE_SIGMA_MAX,NUM_C14_SIGMAS,CALC_CALIB_C14_AGE, CALC_CALIB_C14_AGE_SIGMA_MIN,CALC_CALIB_C14_AGE_SIGMA_MAX, C14_CALIB_SOFTWARE_ID,CALC_C14_CALIB_SOFTWARE_ID,C14_CALIB_DATASET_ID,CALC_C14_ CALIB_DATASET_ID,DENDRO_ID,TOT_NUM_DENDRO,NUM_DENDRO_ USED,DATING_METHOD_ID,NUM_DIR_SAMPLES,NUM_DIR_SPECIMENS,NUM_ DIR_SPEC_COLLECTED,DECL,INCL,ALPHA_95,K,VDM,SIGMA_VDM,SAMPLE_ID,c_csv,SITE_NAME, SITE_HORIZON,1000,1001,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,1012,1013,1014, SUPERSEEDED,UPLOAD_YEAR,UPLOAD_MONTH,UPLOADER,EDITOR,EDIT_DATE,NOTES")

    for index, row in sites.iterrows():
        int_n_samples,int_n_specimens,int_n_total_specimens,int_abs,int_abs_sigma=-1,-1,-1,-1,-1
        if 'int_n_samples' in sites.columns.values: 
            int_n_samples=row['int_n_samples']
        if 'int_n_specimens' in sites.columns.values: 
            int_n_specimens=row['int_n_specimens']
        if 'int_n_total_specimens' in sites.columns.values: 
            int_n_total_specimens=row['int_n_total_specimens']

        if int_n_specimens == -1 and int_n_samples >0:
            int_n_spcimens = int_n_samples

        if 'int_abs' in sites.columns.values: 
            int_abs=row['int_abs']
            if int_abs is not None:
                int_abs=round(int_abs*1e6,1)
        if 'int_abs_sigma' in sites.columns.values: 
            int_abs_sigma=row['int_abs_sigma']
            if int_abs_sigma is not None:
                int_abs_sigma=round(row['int_abs_sigma']*1e6,1)

        age,age_high,age_low=-1e9,-1e9,-1e9
        age_error_type='0'  #  
        
        if 'age_unit' not in sites.columns.values: 
            print("Malformed Magic sites data table. Required column row 'age_unit' is missing")
            sys.exit()
        age_unit=row['age_unit']
        if 'age' in sites.columns.values: 
            age=row['age'] 
            age=pmag.age_to_BP(age,age_unit)
        if 'age_high' in sites.columns.values: 
            age_high=row['age_high'] 
            age_high=pmag.age_to_BP(age_high,age_unit)
        if 'age_low' in sites.columns.values: 
            age_low=row['age_low'] 
            age_low=pmag.age_to_BP(age_low,age_unit)
        if 'age_sigma' in sites.columns.values: 
            age_sigma=row['age_sigma'] 
            age_sigma=pmag.age_to_BP(age_sigma,age_unit)
            age_high=age+age_sigma
            age_low=age-age_sigma
            age_error_type='5'  #Magic is one sigma for all sigma state/province column to data modelages

        if age_low > age_high: # MagIC lets age_high and age_low be in any order. Fix that for GEOMAGIA 
            temp=age_high
            age_high=age_low
            age_low=temp
        if age == -1e9:               # If only age_low and age_high are in the MagIC file then calculate the age.
            age=(age_high+age_low)/2
            age_error_type='8'  #If MagIC age only high and low then error type is "range"

        age_min=age-age_low  # GEOMAGIA has the max and min as differences from the age, not absolute. 
        age_max=age_high-age
        age_BP=age
        age=1950-age  #GEOMAGIA want +-AD/BC so convert BP to AD/-BC

        lat=row['lat']
        lon=row['lon']

        vadm,vadm_sigma=-1,-1
             
        if 'vadm' in sites.columns.values: 
            vadm=row['vadm'] 
            vadm=vadm/1e22
        if 'vadm_sigma' in sites.columns.values: 
            vadm=row['vadm'] 
            vadm=vadm/1e22

        site_name=row['site'] 
        
#       For paleointensity codes just give the method code list and Max will decide on the right 
#       GEOMAGIA code.
        method_codes="No MagIC method codes available"
        if 'method_codes' in sites.columns.values: 
            method_codes=row['method_codes']

#       Just give Max all the method codes for him to decide for now
        paleointensity_procedure=method_codes
        
        alteration_monitor="0"
        alteration_monitor=method_codes_to_geomagia(method_codes,'ALTERATION_MONIT_CORR')
        multidomain_check="0" 
        multidomain_check=method_codes_to_geomagia(method_codes,'MD_CHECKS')
        anisotropy_correction="0"
        anisotropy_correction=method_codes_to_geomagia(method_codes,'ANISOTROPY_CORRECTION')
        cooling_rate="0"
        cooling_rate=method_codes_to_geomagia(method_codes,'COOLING_RATE')
        demag_method="0"
        demag_method=method_codes_to_geomagia(method_codes,'DM_METHODS')
        demag_analysis="0"
        demag_analysis=method_codes_to_geomagia(method_codes,'DM_ANALYSIS')
        specimen_shape="0"
        specimen_shape=method_codes_to_geomagia(method_codes,'SPECIMEN_TYPE_ID')
        
        materials="" 
        geologic_types="" 
        if 'geologic_types' in sites.columns.values: 
            geologic_types=row['geologic_types'] 
        if ":" in geologic_types:
            gtypes=geologic_types.split(":")
            for gtype in gtypes:
                materials=materials+pmag.vocab_convert(gtype,"geomagia")+":"
            materials=materials[:-1]
        else:
            materials=pmag.vocab_convert(geologic_types,"geomagia")
       
        geochron_codes="" 
        if ":" in method_codes:
            gcodes=method_codes.split(":")
            for gcode in gcodes:
                if "GM-" == gcode[:3]:
                    geochron_codes=geochron_codes+pmag.vocab_convert(gcode,"geomagia")+":"
            geochron_codes=geochron_codes[:-1]
        else:
            geochron_codes=pmag.vocab_convert(geochron_codes,"geomagia")
        if geochron_codes == "": 
            geochron_codes="0"

        dir_n_samples="-1"
        if 'dir_n_samples' in sites.columns.values: 
            dir_n_samples=row['dir_n_samples']
 
        dir_n_samples="-1"
        if 'dir_n_samples' in sites.columns.values: 
            dir_n_samples=row['dir_n_samples']

#       Not in MagIC
        dir_n_specimens="-1"

#       using total number of samples for total specimen number
        dir_n_total_samples="-1"
        if 'dir_n_total_samples' in sites.columns.values: 
            dir_n_total_samples=row['dir_n_total_samples']

        dir_dec="999"
        if 'dir_dec' in sites.columns.values: 
            dir_dec=row['dir_dec']

        dir_inc="999"
        if 'dir_inc' in sites.columns.values: 
            dir_inc=row['dir_inc']

        dir_alpha95="-1"
        if 'dir_alpha95' in sites.columns.values: 
            dir_alpha95=row['dir_alpha95']

        dir_k="-1"
        if 'dir_k' in sites.columns.values: 
            dir_k=row['dir_k']

        vdm=-1
        if 'vdm' in sites.columns.values: 
            vdm=float(row['vdm'])
            vdm=vdm/1e22

        vdm_sigma=-1
        if 'vdm_sigma' in sites.columns.values: 
            vdm_sigma=float(row['vdm_sigma'])
            vdm_sigma=vdm_sigma/1e22

# Could try and get sample names from samples table (using Contribution object) but just taking the list 
# if it exists for now.
        sample_list="-1"
        if 'samples' in sites.columns.values: 
            sample_list=row['samples']

# c_csv is in GEOMAGIA insert. What it is I don't know. Max said set to 0
        c_csv='0'

# This place_id is SITE_ID in GEOMAGIA

        place_id="0"
        location=row['location']
        if 'state_province' in locations.columns.values: 
            place=locations.loc[location,'state_province']
            if place != "":
                place_id=pmag.vocab_convert(place,'GEOMAGIA')
        if place_id == "0":
            if 'country' in locations.columns.values: 
                place=locations.loc[location,'country']
                if place != "":
                    place_id=pmag.vocab_convert(place,'GEOMAGIA')
        if place_id == "0":
            if 'continent_ocean' in locations.columns.values: 
                place_id=locations.loc[location,'continent_ocean']
                if place != "":
                    place_id=pmag.vocab_convert(place,'GEOMAGIA')

        site=row['site']
        dt=dateutil.parser.parse(timestamp)

        description="-1" 
        if 'description' in sites.columns.values: 
            description=row['description'] 

        if age_BP <= 50000:
            print("0",int_n_samples,int_n_specimens,int_n_total_specimens,int_abs,int_abs_sigma,age,age_min,age_max,"1",age_error_type,lat,lon,vadm,vadm_sigma,place_id,paleointensity_procedure,alteration_monitor,multidomain_check,anisotropy_correction,cooling_rate,demag_method,"0","0",demag_analysis,specimen_shape,materials,doi,"-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1",geochron_codes,dir_n_samples,dir_n_samples,dir_n_total_samples,dir_dec,dir_inc,dir_alpha95,dir_k,vdm,vdm_sigma,sample_list,c_csv,location,site,"-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1","-1",dt.year,dt.month,contributor,"-1,-1",description,sep=',')
    #end for loop

def method_codes_to_geomagia(magic_method_codes,geomagia_table):
    """
    Looks at the MagIC method code list and returns the correct GEOMAGIA code number depending 
    on the method code list and the GEOMAGIA table specified. Returns O, GEOMAGIA's "Not specified" value, if no match.

    When mutiple codes are matched they are separated with -

    """
    codes=magic_method_codes
    geomagia=geomagia_table.lower()
    geomagia_code='0'
   
    if geomagia=='alteration_monit_corr':
        if  "DA-ALT-V" or "LP-PI-ALT-PTRM" or "LP-PI-ALT-PMRM" in codes:
            geomagia_code='1' 
        elif "LP-PI-ALT-SUSC" in codes:
            geomagia_code='2' 
        elif "DA-ALT-RS" or "LP-PI-ALT-AFARM" in codes:
            geomagia_code='3' 
        elif "LP-PI-ALT-WALTON" in codes:
            geomagia_code='4' 
        elif "LP-PI-ALT-TANGUY" in codes:
            geomagia_code='5' 
        elif "DA-ALT" in codes:
            geomagia_code='6'   #at end to fill generic if others don't exist
        elif "LP-PI-ALT-FABIAN" in codes:
            geomagia_code='7' 

    if geomagia=='md_checks':
        if ("LT-PTRM-MD" in codes) or ("LT-PMRM-MD" in codes):
            geomagia_code='1:' 
        if ("LP-PI-BT-LT" in codes) or ("LT-LT-Z" in codes):
            if "0" in geomagia_code: 
                geomagia_code="23:"
            else:
                geomagia_code+='2:' 
        geomagia_code=geomagia_code[:-1] 

    if geomagia=='anisotropy_correction':
        if  "DA-AC-AMS" in codes:
            geomagia_code='1' 
        elif "DA-AC-AARM" in codes:
            geomagia_code='2' 
        elif "DA-AC-ATRM" in codes:
            geomagia_code='3' 
        elif "LT-NRM-PAR" in codes:
            geomagia_code='4' 
        elif "DA-AC-AIRM" in codes:
            geomagia_code='6' 
        elif "DA-AC" in codes:  #at end to fill generic if others don't exist
            geomagia_code='5' 

    if geomagia=='cooling_rate':
        if  "DA-CR" in codes:  #all current CR codes but CR-EG are a 1 but may change in the future 
            geomagia_code='1' 
        if "DA-CR-EG" in codes:
            geomagia_code='2' 

    if geomagia=='dm_methods':
        if  "LP-DIR-AF" in codes:
            geomagia_code='1' 
        elif "LT-AF-D" in codes:
            geomagia_code='1' 
        elif "LT-AF-G" in codes:
            geomagia_code='1' 
        elif "LT-AF-Z" in codes:
            geomagia_code='1' 
        elif "LP-DIR-T" in codes:
            geomagia_code='2' 
        elif "LT-AF-Z" in codes:
            geomagia_code='2' 
        elif "LP-DIR-M" in codes:
            geomagia_code='5' 
        elif "LT-M-Z" in codes:
            geomagia_code='5' 

    if geomagia=='dm_analysis':
        if  "DE-BFL" in codes:
            geomagia_code='1' 
        elif "DE-BLANKET" in codes:
            geomagia_code='2' 
        elif "DE-FM" in codes:
            geomagia_code='3' 
        elif "DE-NRM" in codes:
            geomagia_code='6' 

    if geomagia=='specimen_type_id':
        if  "SC-TYPE-CYC" in codes:
            geomagia_code='1' 
        elif  "SC-TYPE-CUBE" in codes:
            geomagia_code='2' 
        elif  "SC-TYPE-MINI" in codes:
            geomagia_code='3' 
        elif  "SC-TYPE-SC" in codes:
            geomagia_code='4' 
        elif  "SC-TYPE-UC" in codes:
            geomagia_code='5' 
        elif  "SC-TYPE-LARGE" in codes:
            geomagia_code='6' 

    return geomagia_code 

if __name__ == "__main__":
    main()

