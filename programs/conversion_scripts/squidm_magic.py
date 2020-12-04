#!/usr/bin/env python

import sys,os
import pandas as pd
import re
import math

def main():
    """
    NAME
        squidm_magic.py
    DESCRIPTION
        Converts SQUID microscopy files into MagIC format files.
        This program currently supports only specimens from a single sample.  
        Method codes are applied to all rows in each table. To add method codes
        to individual rows, edit the MagIC file after this program creates it.
        A standard MagiC file is created for the location through specimen tables,
        along with measurement data from the model fits. The SQUID microscopy 
        measurement data is placed in individual files for each experiment in the
        compact MagIC file format. These measurement files are placed in a 
        directory called "measurements".
        
        This program requires a specific directory/file structure to function.
        The top directory should contain directories named for each of the SQUID
        microscopy scan groups. This name will be used as the specimen name in
        the MagIC specimen table that is created by this program. In each scan
        directory there should be directories labeled "demag", "data", "images". The
        data directory should contain the .bz, .inf, and .fits files for each SQUID
        microscopy scan. The .bz, .inf, and .fits files must have the same name. The 
        demag directory should have a .sam file that has the same name as the
        name of the directory 2 levels up. That is, if the main directory is ZirconRun2,
        then the .sam file should be named ZirconRun2.sam. There should also be
        the CIT formatted files with the model demag data in them along with an 
        associated _fits.txt file that has information about how well the model
        dipole fits the data. In the images directory should be any human viewable
        image files that will be uploaded to MagIC along with the data. .jpg, .png,
        .gif, .pdf, etc. type files.

        The .fits file format is: moment in emu, declination, inclination, height, residuals
        An example of the text in a .fits file:
        1.51e-10,54.36,220.92,0.000429,0.4214

        Example file directory tree:
        ZirconRun1 -- (file hierarchy) 
        ZirconRun2 -- data -- run2N_140C_100k.bz
                           -- run2N_140C_100k.fits
                           -- run2N_140C_100k.inf
                           -- run2N_173C_100k.bz
                           -- run2N_173C_100k.fits
                           -- run2N_173C_100k.inf
                   -- demag -- 57-1-3
                            -- 57-19-12
                            -- ZirconRun2.sam
                   -- images -- run2N_140C_100k.pdf
                             -- run2S_89G_1M.pdf
        ZirconRun3 -- (file hierarchy)

    SYNTAX
        mit_squid_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.

        -meas_name_num: set the starting number for the measurement name. Default:1

        -location: specify location/study name

        -location_type: specify location_type 
                        see https://www.earthref.org/vocabularies/controlled for list 

        -geologic_classes: specify geologic_classes (":" between multiple entries). 
                           see https://www.earthref.org/vocabularies/controlled for list

        -lithologies: specify lithologies. (":" between multiple entries) 
                      see https://www.earthref.org/vocabularies/controlled for list

        -lat: specify the latitude of the site.  

        -lon: specify longitude of the site.

        -age: specify the age of the site.
              One must have an age defined. age_low and age_high can be used in 
              addition to or in place of age.

        -age_sigma: specify the one sigma error on the age.

        -age_low: specify the low bound for the age. 

        -age_high: specify the high bound for the age.

        -age_unit: specify the age unit. ka, Ma, Ga are some examples.
                   see https://www.earthref.org/vocabularies/controlled for list
        -citations: list of citations (":" between entries). default: "This study". 
                    "This study" can be used for the study this MagIC contribution 
                    will be associated with. Will be added when the data is published.
                    Use DOIs for other studies.

        -site: site name for the sample that the scan slides were made from

        -geologic_types: geologic types of the site. (":" between multiple entries)
        
        -sample: sample name from which the slides were made from

        -loc_method_codes: method_codes used for all locations
                       (":" between multiple entries)
                       Recommend

        -site_method_codes: method_codes used for all sites
                       (":" between multiple entries)
                       Required

        -samp_method_codes: method_codes used for all samples
                       (":" between multiple entries)
                       Required

        -spec_method_codes: method_codes used for all specimens. Put LP-NOMAG method code last, if used.
                       (":" between multiple entries)
                       Required 

        -meas_method_codes: method_codes used for all measurements
                       (":" between multiple entries)
                       LP-SQUIDM will be automatically added to the measurements method
                       code list if not already in the provided list of codes

        -instrument_codes: used to identify the instrument that made the measurement. 
                           Exact instrument name prefered, not type. 
                           (":" between multiple entries)
    
        -model_height_name: name from the MagIC "Derived Values" controtrolled vocabulary for the model used
                            to calculate the model height.
                            Should correspond to the model_residuals_name

        -model_residuals_name: name from the MagIC "Derived Values" controtrolled vocabulary for the model used
                            to calculate the model residuals.
                            Should correspond to the model_height_name

        -model_doi: doi reference for the model used to calculate the model height, and residuals

        -A: don't average replicant measurements 

        -multi_samples: flag used to indicate to not remove the MagIC files upon finishing. This leaves the
                       MagIC files to be concatenated by another program when there are multiple samples in
                       the study.

        -meas_num: set the starting measurement name number. default:1

        -labfield: the field strength that the sample was magnetized for an in-field step 
                   in  microTesla. default:0.0

        -phi: Angle between the specimen x-y plane and the dc field direction. 
              Positive toward the positive z direction. 

        -theta: Angle of the dc field direction when projected into the x-y plane. 
                Positive x-axis is 0 and increasing toward the positive y-axis. 

        -ncn NCON: specify naming convention for the CIT sample files.

      Sample naming convention (NCON): 
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitrary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in sitename column in the orient.txt format input file -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
        NB: all others you will have to either customize your self or e-mail webmaster@earthref.org for help.

      Example command for the example data file. Data from Weiss et al., 2018 (doi:10.1130/G39938.1):
    squidm_magic.py -location "Jack Hills" -location_type "Outcrop" -geologic_classes "Metamorphic" -lithologies "Metaconglomerate" -geologic_types "Single Crystal" -lat "-26" -lon 117 -age_low 0.8 -age_high 2.6 -age_unit Ga -citations "10.1130/G39938.1" -site "Erawandoo Hill" -loc_method_codes "GM-UPB" -site_method_codes "GM-UPB" -samp_method_codes "SC-SQUIDM" -spec_method_codes "SC-SQUIDM" -geologic_types "Single Crystal" -sample RSES-57 -ncn 5 -instrument_codes "MIT SQUID microscope" -model_height_name "SQUID Microscopy Model Height Lima And Weiss 2016" -model_residuals_name "SQUID Microscopy Residuals Lima And Weiss 2016" -model_doi "10.1002/2016GC006487" -labfield 50.0 -phi 0.0 -theta 90 -A
    """

    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit

    if '-meas_name_num' in sys.argv:
        ind=sys.argv.index('-meas_name_num')
        meas_name_num=int(sys.argv[ind+1])
    else:
        meas_name_num=1

    if '-location' in sys.argv:
        ind=sys.argv.index('-location')
        location=sys.argv[ind+1]
    else:
        print("The location/study name must be set with the -location flag")
        exit()
   
    if '-location_type' in sys.argv:
        ind=sys.argv.index('-location_type')
        location_type=sys.argv[ind+1]
    else:
        print("The location_type name must be set with the -location_type flag")
        exit()
   
    if '-geologic_classes' in sys.argv:
        ind=sys.argv.index('-geologic_classes')
        geologic_classes=sys.argv[ind+1]
    else:
        print("The geologic classes must be set with the -geologic_classes flag")
        exit()
   
    if '-lithologies' in sys.argv:
        ind=sys.argv.index('-lithologies')
        lithologies=sys.argv[ind+1]
    else:
        print("The litothologies must be set with the -lithologies flag")
        exit()
   
    if '-lat' in sys.argv:
        ind=sys.argv.index('-lat')
        lat=sys.argv[ind+1]
    else:
        print("The latitude must be set with the -lat flag")
        exit()
   
    if '-lon' in sys.argv:
        ind=sys.argv.index('-lon')
        lon=sys.argv[ind+1]
    else:
        print("The longitude must be set with the -lon flag")
        exit()
   
    if '-age' in sys.argv:
        ind=sys.argv.index('-age')
        age=sys.argv[ind+1]
    else:
        age=""
   
    if '-age_sigma' in sys.argv:
        ind=sys.argv.index('-age_sigma')
        age_sigma=sys.argv[ind+1]
    else:
        age_sigma=""
   
    if '-age_low' in sys.argv:
        ind=sys.argv.index('-age_low')
        age_low=sys.argv[ind+1]
    else:
        age_low=""
   
    if '-age_high' in sys.argv:
        ind=sys.argv.index('-age_high')
        age_high=sys.argv[ind+1]
    else:
        age_high=""
   
    if '-age_unit' in sys.argv:
        ind=sys.argv.index('-age_unit')
        age_unit=sys.argv[ind+1]
    else:
        print("The age unit must be set with the -ageunit flag")
        exit()

    if '-citations' in sys.argv:
        ind=sys.argv.index('-citations')
        citations=sys.argv[ind+1]
    else:
        citations="This study"
   
    if '-loc_method_codes' in sys.argv:
        ind=sys.argv.index('-loc_method_codes')
        loc_method_codes=sys.argv[ind+1]
    else:
        loc_method_codes=""
   
    if '-site_method_codes' in sys.argv:
        ind=sys.argv.index('-site_method_codes')
        site_method_codes=sys.argv[ind+1]
    else:
        print("method code(s) for the site must be set with the -site_method_code flag")
        exit()
   
    if '-samp_method_codes' in sys.argv:
        ind=sys.argv.index('-samp_method_codes')
        samp_method_codes=sys.argv[ind+1]
    else:
        print("method code(s) for the sample must be set with the -samp_method_code flag")
        exit()
   
    if '-spec_method_codes' in sys.argv:
        ind=sys.argv.index('-spec_method_codes')
        spec_method_codes=sys.argv[ind+1]
    else:
        print("method code(s) for the specimen must be set with the -specimen_method_code flag")
        exit()
   
    if '-meas_method_codes' in sys.argv:
        ind=sys.argv.index('-meas_method_codes')
        meas_method_codes=sys.argv[ind+1]
        if 'LP-SQUIDM' not in meas_method_codes:
            meas_method_code=meas_method_codes+':LP-SQUIDM'
    else:
        meas_method_codes='LP-SQUIDM'

    if '-instrument_codes' in sys.argv:
        ind=sys.argv.index('-instrument_codes')
        instrument_codes=sys.argv[ind+1]
    else:
        instrument_codes=""
        
    if '-model_height_name' in sys.argv:
        ind=sys.argv.index('-model_height_name')
        model_height_name=sys.argv[ind+1]
    else:
        print("The model height name must be set with the -model_height_name flag")
        exit()
   
    if '-model_residuals_name' in sys.argv:
        ind=sys.argv.index('-model_residuals_name')
        model_residuals_name=sys.argv[ind+1]
    else:
        print("The model residuals name must be set with the -model_residuals_name flag")
        exit()
   
    if '-model_doi' in sys.argv:
        ind=sys.argv.index('-model_doi')
        model_doi=sys.argv[ind+1]
    else:
        print("The model doi must be set with the -model_doi flag")
        exit()
   
    if '-site' in sys.argv:
        ind=sys.argv.index('-site')
        site=sys.argv[ind+1]
    else:
        print("The site name must be set with the -site flag")
        exit()
   
    if '-geologic_types' in sys.argv:
        ind=sys.argv.index('-geologic_types')
        geologic_types=sys.argv[ind+1]
    else:
        print("The  geologic types must be set with the -geologic_types flag")
        exit()
   
    if '-sample' in sys.argv:
        ind=sys.argv.index('-sample')
        sample=sys.argv[ind+1]
    else:
        print("The site name must be set with the -sample flag")
        exit()

    if '-oe' in sys.argv:
        oe=' -oe '
    else:
        oe=''

    if '-A' in sys.argv:
        average='-A'
    else:
        average=''

    if '-multi_samples' in sys.argv:
        multi_samples=True
    else:
        multi_samples=False

    if '-meas_num' in sys.argv:
        ind=sys.argv.index('-meas_num')
        meas_num=int(sys.argv[ind+1])
    else:
        if multi_samples:
            if os.path.isfile('../last_measurement_number'):
                f=open('../last_measurement_number','r')
                meas_num=int(f.readline())
                f.close()
            else:
                meas_num=1
        else:
            meas_num=1

    if '-labfield' in sys.argv:
        ind=sys.argv.index('-labfield')
        labfield=sys.argv[ind+1]
    else:
        dc_field='0.0'

    if '-phi' in sys.argv:
        ind=sys.argv.index('-phi')
        phi=sys.argv[ind+1]
    else:
        phi='0.0'

    if '-theta' in sys.argv:
        ind=sys.argv.index('-theta')
        theta=sys.argv[ind+1]
    else:
        theta='0.0'

    if '-ncn' in sys.argv:
        ind=sys.argv.index('-ncn')
        ncn=sys.argv[ind+1]
    else:
        print("Setting the sample name convention with the -ncn flag is required")
        exit()


#   Run cit_magic.py on all slides to process the psudo-Thellier data
#   Format and combine the MagIC files from each slide into one MagIC file
#   Create measurementXX.txt files for each slide scan by translating the data into the MagIC format

    print("start")

    os.system("rm locations.txt sites.txt samples.txt specimens.txt measurements.txt")
    os.system("rm *.txt ") # for debugging
    os.system("rm -r images")
    os.system("rm -r measurements")

    dir_list=os.listdir()
    print('dir_list=',sorted(dir_list))
    slide_dir_list=[]
    image_dir_list=[]
    specimen_list=[]

    # create locations table
    df=pd.DataFrame(columns=["location","location_type","geologic_classes","lithologies","lat_n","lat_s","lon_w","lon_e","age_unit","citations","method_codes"],data=[[location,location_type,geologic_classes,lithologies,lat,lat,lon,lon,age_unit,citations,loc_method_codes]])
    if age!="":
        df["age"]=[age]
    if age_high!="":
        df["age_high"]=[age_high]
    if age_low!="":
        df["age_low"]=[age_low]
    print(df)
    df.to_csv("locations.txt",sep='\t',index=False)
    add_head("locations")

    # create sites table
    df=pd.DataFrame(columns=["site","location","geologic_classes","geologic_types","lithologies","lat","lon","age_unit","citations","method_codes"],data=[[site,location,geologic_classes,geologic_types,lithologies,lat,lon,age_unit,citations,site_method_codes]])
    if age!="":
        df["age"]=[age]
    if age_high!="":
        df["age_high"]=[age_high]
    if age_low!="":
        df["age_low"]=[age_low]
    print(df)
    df.to_csv("sites.txt",sep='\t',index=False)
    add_head("sites")

    # create samples table
    df=pd.DataFrame(columns=["sample","site","lat","lon","geologic_classes","geologic_types","lithologies","citations","method_codes"],data=[[sample,site,lat,lon,geologic_classes,geologic_types,lithologies,citations,samp_method_codes]])
    df.to_csv("samples.txt",sep='\t',index=False)
    add_head("samples")

    meas_num=meas_num
    for dir in sorted(dir_list):
        if dir[0] == '.':   # skip . files added by MacOS
            continue
        elif dir == 'command':   # skip command file 
            continue
        elif dir == 'log':   # skip log file - used during debugging
            continue
        specimen=dir
        slide_dir_list.append(dir+'/demag/')
        specimen_list.append(dir)
#        print("specimen_list",specimen_list)

        # create images.txt file when images directories are present
        if os.path.isdir(dir+'/images/'): 
            image_dir_list.append(dir+'/images/')
            os.chdir(dir+'/images')
            if os.path.isfile("images.txt"):
                os.system("rm images.txt") 
            image_file_names=os.listdir()
            f_images=open('images.txt','w')
            f_images.write('tab\timages\n')
            f_images.write('specimen\tfile\ttype\ttitle\tkeywords\n')
            for file_name in image_file_names:
                title_split=file_name.split(".")
                title=title_split[0]
                f_images.write(dir+'\t'+file_name+'\tScanning SQUID Microscopy\t'+title+'\tScanning SQUID Microscopy\n')
            f_images.close()
        print("image_dir_list",image_dir_list)
        os.chdir('../..')
        
        # create MagIC files from cit files
        os.chdir(dir+'/demag')     
        command='cit_magic.py -ncn ' + ncn + ' -f ' + dir + '.sam -loc "' + location + '" -sn "' + site + '" -sampname "' + sample + '" -dc ' + labfield + ' '  + phi + ' ' + theta + ' ' + average
        if spec_method_codes != "":
            command+=' -mcd ' + spec_method_codes
        print(command)
        os.system(command)

        # add info to specimens table
        df=pd.read_csv("specimens.txt",sep="\t",header=1)
        df=append_to_column(df,"method_codes",spec_method_codes)
        df=update_column(df,"citations",citations)
        df=update_column(df,"geologic_classes",geologic_classes)
        df=update_column(df,"lithologies",lithologies)
        df=update_column(df,"geologic_types",geologic_types)
        df.to_csv("specimens.txt",sep='\t',index=False)
        add_head("specimens")

        # add info to measurements table
        df=pd.read_csv("measurements.txt",sep="\t",header=1)
        df=append_to_column(df,"method_codes",meas_method_codes)
        df=update_column(df,"citations",citations)
        df=update_column(df,"instrument_codes",instrument_codes)
        df.to_csv("measurements.txt",sep='\t',index=False)
        add_head("measurements")

        # Create the large MagIC measurement files for the raw QDM data scans
        os.chdir('../data')     
        os.system('rm measurements*.txt')
        meas_num,meas_name_num=convert_squid_data(specimen,citations,meas_num,meas_method_codes,meas_name_num,model_height_name,model_residuals_name,model_doi)
        os.system('mv measurements*.txt ../../') 

        os.chdir('../../')

#   move all the measurement files to one folder
    os.system("mkdir measurements")
    os.system("mv measurements[0-9]*.txt measurements")

#   Combine the images tables and put the images in one folder
    image_files=""
    print("XXXXXXXXXXXXXXXXXXXXXXXXXXX")
    print("image dir list=",image_dir_list)
    print("XXXXXXXXXXXXXXXXXXXXXXXXXXX")
    for dir in image_dir_list:
        image_files+=dir+ "images.txt "
    os.system("combine_magic.py -F images.txt -f " + image_files)
    os.mkdir("images")
    for dir in image_dir_list:
        os.system("cp " + dir + "* images")

#   Create files for combining into sites and samples tables for the image info
    tab="\t"
    geologic_types=geologic_types

    f=open("images/sites.txt","w")
    f.write("tab\tsites\n")
    f.write("site\tlocation\tlat\tlon\tcitations\tgeologic_classes\tlithologies\tage_high\tage_low\tage_unit\tmethod_codes\tgeologic_types\n")
    f.write(site + tab + location + tab + lat + tab + lon + tab + citations + tab + geologic_classes + tab + lithologies + tab +age_high + tab + age_low + tab + age_unit + tab + site_method_codes + tab + geologic_types + "\n")
    f.close()

    f=open("images/samples.txt","w")
    f.write("tab\tsamples\n")
    f.write("sample\tsite\tgeologic_classes\tgeologic_types\tlithologies\tcitations\tmethod_codes\tlat\tlon\n")
    f.write(sample + tab + site + tab + geologic_classes + tab + geologic_types + tab + lithologies + tab + citations + tab + samp_method_codes + tab + lat + tab + lon + "\n")
    f.close()

    print("Creating specimens header file for images specimens")
    f=open("images/specimens.txt","w")
    f.write("tab\tspecimens\n")
    f.write("specimen\tsample\tcitations\tmethod_codes\tgeologic_classes\tgeologic_types\tlithologies\n")
    f.close()

#   Create files lists for combining the MagIC data files

    print("slide dir list=",slide_dir_list)
    site_files="sites.txt images/sites.txt "
    samp_files="samples.txt images/samples.txt "
    spec_files="specimens.txt images/specimens.txt "
    meas_files=""
    for dir in slide_dir_list:
        spec_files+=dir+"specimens.txt "
        meas_files+=dir+"measurements.txt "

#       Also add the specimen names for the scan slides to the specimen table
    for fdf in specimen_list:
        f=open("images/specimens.txt","a")
        f.write(fdf + tab + sample + tab + citations + tab + spec_method_codes + tab + geologic_classes + tab + geologic_types + tab + lithologies + "\n")
        f.close()

    os.system("combine_magic.py -F specimens.txt -f " + spec_files)
    os.system("combine_magic.py -F measurements.txt -f " + meas_files)

    os.system("upload_magic.py")

#   Remove MagIC files
    for dir in slide_dir_list:
        os.system("rm " + dir + "locations.txt")
        os.system("rm " + dir + "sites.txt")
        os.system("rm " + dir + "samples.txt")
        os.system("rm " + dir + "specimens.txt")
        os.system("rm " + dir + "measurements.txt")
    print("multi_samples=",multi_samples)
    if multi_samples == False: 
        os.system("rm locations.txt sites.txt samples.txt specimens.txt measurements.txt images.txt")
        os.system("rm images/sites.txt images/samples.txt images/specimens.txt images/images.txt")

    f=open("../last_measurement_number","w")
    f.write(str(meas_num))
    f.close()
    print("end")   
    return()

def convert_squid_data(specimen,citations,meas_num,meas_method_codes,meas_name_num,model_height_name,model_residuals_name,model_doi):
#   Take the SQUID magnetometer files and make a MagIC measurement file. This data will not be uploaded 
#   in the contribution MagIC data file due is large size, but will be available for download. 
#   These have to be uploaded by hand for now.
#   Each scan's data is put in a seperate measurements.txt file and the files are put in a 
#   separate directory.   
    
    file_list=os.listdir()
    print(sorted(file_list))

    for file in sorted(file_list):
        if file[0] == '.':  # skip . files added by MacOS
            continue
        if '.inf' in file:  # skip .inf files process all files in the .bz loop as we need all the data to create the measurements file
            continue
        if '.fits' in file: # skip .inf files process all files in the .bz loop as we need all the data to create the measurements file
            continue

        print('file=',file)
        data_name=file
        info_name=file[:-3]+ '.inf'

#   Parse the .inf file
        info = open(info_name, encoding="utf8", errors='ignore') # data files have some non-utf8 characters that are ignored    
        line=info.readline() 
        line=info.readline() 
        line=info.readline() 
        initial_corner=line.split('(')
        x_start=float(initial_corner[1].split()[0])
        y_start=float(initial_corner[1].split()[2])
        x_start=1e-3*x_start  # convert mm to meters
        y_start=1e-3*y_start  # convert mm to meters
        print("x_start=",x_start)
        print("y_start=",y_start)
        line=info.readline() 
        end_corner=line.split('(')
        x_end=float(end_corner[1].split()[0])
        y_end=float(end_corner[1].split()[2])
        x_end=1e-3*x_end  # convert mm to meters
        y_end=1e-3*y_end  # convert mm to meters
        print("x_end=",x_end)
        print("y_end=",y_end)
        line=info.readline() 
        line=info.readline() 
        line=info.readline() 
        line=info.readline() 
        x_step_line=line.split()
        x_step=float(x_step_line[3]) 
        x_step=1e-6*x_step  #convert micrometers to meters
        print("x_step",x_step) 
        line=info.readline() 
        y_step_line=line.split()
        y_step=float(y_step_line[3]) 
        y_step=1e-6*y_step  #convert micrometers to meters
        print("y_step",y_step) 
        line=info.readline() 
        line=info.readline() 
        comment=line[4:-1]
        line=info.readline() 
        comment=comment+", "+line[4:-1]
        line=info.readline() 
        comment=comment+", "+line[4:-1]
        line=info.readline() 
        line=info.readline() 
        comment=comment+", "+line[4:-1]
        line=info.readline() 
        num_points_line=line.split()
        num_points=float(num_points_line[3])
        comment=comment+", "+line[4:-1]
        print ("num_points=",num_points)
        line=info.readline() 
        line=info.readline() 
        line=info.readline() 
        line=info.readline() 
        comment=comment+", "+line[4:-1]
        line=info.readline() 
        line=info.readline() 
        comment=comment+", "+line[4:-1]
        line=info.readline() 
        line=info.readline() 
        line=info.readline() 
        line=info.readline() 
        calibration_factor_line=line.split()
        calibration_factor=float(calibration_factor_line[2])
        calibration_factor=1e-9*calibration_factor  # convert nanoTesla to Tesla
        comment=comment+", "+line[4:-1]
        print ("calibration_factor=",calibration_factor)
        line=info.readline() 
        line=info.readline() 
        line=info.readline() 
        line=info.readline() 
        comment=comment+", "+line[4:-1]
        line=info.readline() 
        comment=comment+", "+line[4:-1]
        line=info.readline() 
        comment=comment+", "+line[4:-1]
        print ("comment=",comment)
        line=info.readline() 
        info.close()

        experiment_name=file.split('.')
        experiment_name=experiment_name[0]

#       get the model height and residuals information from the .fits file

        fits_name=file[:-3]+ '.fits'
        f=open(fits_name,'r')
        line=f.readline()
        line_split=line.split(",")
        # fit file values are moment (emu), inc, dec, height and residuals
        height=line_split[3]
        residuals=line_split[4]
        residuals=residuals.strip()

# open the measurement file for writing and put the compressed headers in
        mf=open('measurements'+str(meas_num)+'.txt','w')
        mf.write("tab\tmeasurements\n")
        mf.write('* experiment\t'+experiment_name+'\n')
        mf.write('* specimen\t'+specimen+'\n')
        mf.write('* standard\tu\n')
        mf.write('* quality\tg\n')
        mf.write('* method_codes\t'+meas_method_codes+'\n')
        mf.write('* citations\t'+citations+'\n')
        mf.write('* description\t'+comment+'\n')
        mf.write('* derived_value\t'+model_height_name+','+height+','+model_doi+';'+model_residuals_name+','+residuals+','+model_doi+'\n')

        mf.write('measurement\tmagn_z\tmeas_pos_x\tmeas_pos_y\n')
        print('meas_num=', meas_num)
        print('')
        meas_num+=1

        prog = re.compile("\d*[.]\d*([0]{5,100}|[9]{5,100})\d*\Z") #for rounding
        
        qdm_data=open(data_name,'r')
        line=qdm_data.readline() 
        y=y_start
        while line != "":
            str_y=stringify(y*y_step)
            str_y=remove_extra_digits(str_y, prog) #fix float to str problems
            values=line.split()
            x=x_start
            for value in values:
                str_x=stringify(x*x_step)
                str_x=remove_extra_digits(str_x, prog)
                value=float(value)*calibration_factor 
# fix rounding problems with exponentials and zeros
                str_value=str(value)
                if 'e' in str_value: 
                    split_value=str_value.split('e')
                    str_val_num=split_value[0]
                    if '0000000' in str_value:
                        str_val_num_split=str_val_num.split('0000000')
                        if str_val_num_split[1] == '': str_val_num_split[1]='0'
                        if int(str_val_num_split[1]) < 10:
                            str_value=str_val_num_split[0]+'e'+ split_value[1]
                measurement_line=str(meas_name_num)+'\t'+str_value+'\t'+str_x+'\t'+str_y+'\n'
                mf.write(measurement_line)
                x+=1
                meas_name_num+=1
            y+=1
            line = qdm_data.readline() 
        qdm_data.close()
        mf.close()
    return(meas_num,meas_name_num)

def update_column(df,column,value):
    #add the column with all the same values to a DataFrame
    column_values = []
    for i in df.iterrows():
        column_values.append(value)    
#    print ("column=", column)
#    print ("column_values=", column_values)
    df[column] = column_values
    return(df)
        
def append_to_column(df,column,value):
    # add value to all of the values in column except when the value already is in the original value
    for index, row in df.iterrows():
        value_list = value.split(':')
        for method_code in value_list:
            if method_code not in df.loc[index,column]:
                df.loc[index,column]= method_code + ":" + df.loc[index,column]
    return(df)

def add_head(table):
    # Add the the magic file format header to a data file given the table name
    
    file_name=table+".txt" 
    f=open(file_name,"r")
    f_before=f.read()
    f.close()
    f_after="tab\t" + table+"\n"+f_before
    f=open(file_name,"w")
    f.write(f_after)
    f.close()

def stringify(x):
    # float --> string,
    # truncating floats like 3.0 --> 3
    if isinstance(x, float):
        if x.is_integer():
            #print('{} --> {}'.format(x, str(x).rstrip('0').rstrip('.')))
            return str(x).rstrip('0').rstrip('.')
        return(str(x))
    # keep strings as they are,
    # unless it is a string like "3.0",
    # in which case truncate that too
    if isinstance(x, str):
        try:
            float(x)
            if x.endswith('0'):
                if x.rstrip('0').endswith('.'):
                    #print('{} --> {}'.format(x, x.rstrip('0').rstrip('.')))
                    return x.rstrip('0').rstrip('.')
        except (ValueError, TypeError):
            pass
    # integer --> string
    if isinstance(x, int):
        return str(x)
    # if it is not int/str/float, just return as is
    return x

def remove_extra_digits(x, prog):
    """
    Remove extra digits
    x is a string,
    prog is always the following '_sre.SRE_Pattern':
    prog = re.compile("\d*[.]\d*([0]{5,100}|[9]{5,100})\d*\Z").
    However, it is compiled outside of this sub-function
    for performance reasons.
    """
    if not isinstance(x, str):
        return x
    result = prog.match(x)
    if result:
        decimals = result.string.split('.')[1]
        result = result.string
        if decimals[-3] == '0':
            result = x[:-2].rstrip('0')
        if decimals[-3] == '9':
            result = x[:-2].rstrip('9')
            try:
                last_digit = int(result[-1])
                result = result[:-1] + str(last_digit + 1)
            except ValueError:
                result = float(result[:-1]) + 1
        #if result != x:
        #    print('changing {} to {}'.format(x, result))
        return result
    return x
    
def do_help():
    """
    returns help string of script
    """
    return __doc__

if __name__ == "__main__":
    main()
