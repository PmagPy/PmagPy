#!/usr/bin/env python

import sys,os
import pandas as pd

def main():
    """
    NAME
        mit_squid_magic.py

    DESCRIPTION
        Converts 2019 SQUID files into a MagIC format measurement file.
        This program currently supports only specimens from a single sample.  
        Method codes are applied to all rows in each table. To add method codes
        to individual rows, edit the MagIC file after this program creates it.
         

    SYNTAX
        mit_squid_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.

        -d DIRECTORY: specify directory where the slide folders are located, 
                      otherwise current directory is used.

        -s: set the starting measurement sequence number. Default:1

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

        -spec_method_codes: method_codes used for all specimens
                       (":" between multiple entries)
                       Required

        -meas_method_codes: method_codes used for all measurements
                       (":" between multiple entries)
                       LP-SQUIDM will be automatically added to the SQUID microscopy measurements
                       Required

        -instrument_codes: used to identify the insturment that made the measurement. 
                           Exact insturment name prefered, not type. 
                           (":" between multiple entries)
    
        -z_pos: distance from the surface in micrometers. default:0

        -oe: flag to use cgs units for magnetic field strength(Oe) or mangnetic moment(emu) 

        -ncn NCON: specify naming convention.

      Sample naming convention (NCON): 
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in sitename column in the orient.txt format input file -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
        NB: all others you will have to either customize your
            self or e-mail ltauxe@ucsd.edu for help.

      Example command for the example data file. Data from Weiss et al., 2018 (doi:10.1130/G39938.1):
      mit_squid_magic.py -location "Jack Hills" -location_type "Outcrop" -geologic_classes "Metamorphic" -lithologies "Metaconglomerate" -geologic_types "Single Crystal" -lat "-26" -lon 117 -age_low 0.8 -age_high 2.6 -age_unit Ga -citations "10.1130/G39938.1" -site "Erawandoo Hill" -loc_method_codes "GM-UPB" -site_method_codes "GM-UPB" -samp_method_codes "SC-SQUIDM" -spec_method_codes "SC-SQUIDM" -geologic_types "Single Crystal" -sample RSES-57 -ncn 5 -instrument_codes "MIT SQIUD magnetometer" -oe -z_pos 10.0

      

    """

    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit

    if '-s' in sys.argv:
        ind=sys.argv.index('-s')
        sequence=int(sys.argv[ind+1])
    else:
        sequence=1

    if '-d' in sys.argv:
        ind=sys.argv.index('-d')
        dir_name=sys.argv[ind+1]
    else:
        dir_name="."

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
        exit()
   
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
   
    if '-samp_method_codes' in sys.argv:
        ind=sys.argv.index('-samp_method_codes')
        samp_method_codes=sys.argv[ind+1]
    else:
        print("method code(s) for the sample must be set with the -samp_method_code flag")
        samp_method_codes=""
   
    if '-spec_method_codes' in sys.argv:
        ind=sys.argv.index('-spec_method_codes')
        spec_method_codes=sys.argv[ind+1]
    else:
        print("method code(s) for the specimen must be set with the -specimen_method_code flag")
        spec_method_codes=""
   
    if '-meas_method_codes' in sys.argv:
        ind=sys.argv.index('-meas_method_codes')
        meas_method_codes=sys.argv[ind+1]
    else:
        meas_method_codes=""
   
    if '-instrument_codes' in sys.argv:
        ind=sys.argv.index('-instrument_codes')
        instrument_codes=sys.argv[ind+1]
    else:
        instrument_codes=""
        
    if '-site' in sys.argv:
        ind=sys.argv.index('-site')
        site=sys.argv[ind+1]
    else:
        print("The site name must be set with the -site flag")
   
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

    if '-oe' in sys.argv:
        oe=' -oe '
    else:
        oe=''

    if '-z_pos' in sys.argv:
        ind=sys.argv.index('-z_pos')
        z_pos=sys.argv[ind+1]
    else:
        z_pos=0.0
   
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
#    print(sorted(dir_list))
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

    meas_file_num=1
    for dir in sorted(dir_list):
        if dir[0] == '.':   # skip . files added by MacOS
            continue
        elif dir == 'command':   # skip command file 
            continue
        elif dir == 'log':   # skip log file - used during debugging
            continue
        specimen=dir
        slide_dir_list.append(dir+'/demag/')
        image_dir_list.append(dir+'/images/')
        specimen_list.append(dir)
#        print("specimen_list",specimen_list)

        # create MagIC files from cit files
        os.chdir(dir+'/demag')     
        if spec_method_codes == "":
            command='cit_magic.py -ncn ' + ncn + oe + '-f ' + dir + '.sam -loc "' + location + '" -sn "' + site + '" -sampname "' + sample + '"'
        else:
            command='cit_magic.py -ncn ' + ncn + oe + '-f ' + dir + '.sam -loc "' + location + '" -sn "' + site + '" -sampname "' + sample + '" -mcd ' + spec_method_codes
        print(command)
        os.system(command)

        # add info to specimens table
        df=pd.read_csv("specimens.txt",sep="\t",header=1)
        df=append_column(df,"method_codes",spec_method_codes)
        df=update_column(df,"citations",citations)
        df=update_column(df,"geologic_classes",geologic_classes)
        df=update_column(df,"lithologies",lithologies)
        df=update_column(df,"geologic_types",geologic_types)
        df.to_csv("specimens.txt",sep='\t',index=False)
        add_head("specimens")

        # add info to measurements table
        df=pd.read_csv("measurements.txt",sep="\t",header=1)
        df=append_column(df,"method_codes",meas_method_codes)
        df=update_column(df,"citations",citations)
        df=update_column(df,"instrument_codes",instrument_codes)
        df.to_csv("measurements.txt",sep='\t',index=False)
        add_head("measurements")

        # Create the large MagIC measurement files for the raw QDM data scans
        os.chdir('../data')     
        os.system('rm measurements*.txt')
        meas_file_num,sequence=convert_squid_data(specimen,citations,z_pos,meas_file_num,meas_method_codes,sequence)
        os.system('mv measurements*.txt ../../') 

        os.chdir('../../')

#   move all the measurement files to one folder
    os.system("mkdir measurements")
    os.system("mv measurements[0-9]*.txt measurements")

#   Combine the images tables and put the images in one folder
    image_files=""
    for dir in image_dir_list:
        image_files+=dir+ "images.txt "
    os.system("combine_magic.py -F images.txt -f " + image_files)

    print("image dir list=",image_dir_list)
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
    os.system("rm locations.txt sites.txt samples.txt specimens.txt measurements.txt images.txt")
    os.system("rm images/sites.txt images/samples.txt images/specimens.txt images/images.txt")

    print("end")   
    return()

def convert_squid_data(specimen, citations, z_pos, meas_file_num, meas_method_codes,sequence):
#   Take the SQUID magnetometer files and make a MagIC measurement file. This data will not be uploaded 
#   in the contribution MagIC data file due is large size, but will be available for download. 
#   Each scan's data is put in a seperate measurements.txt file in its own directory.   
    
    file_list=os.listdir()
    print(sorted(file_list))

    for file in sorted(file_list):
        if file[0] == '.':   # skip . files added by MacOS
            continue
        print('file=',file)
        if '.inf' in file:       # do processing on both files in the .bz loop as we need data in both to create the measurements file
            continue

        mf=open('measurements' + str(meas_file_num) + '.txt','w')
        mf.write("tab\tmeasurements\n")
        mf.write('measurement\texperiment\tspecimen\tsequence\tstandard\tquality\tmethod_codes\tcitations\tmagn_z\tmeas_pos_x\tmeas_pos_y\tmeas_pos_z\tdescription\n')
       
        print('meas_file_num=', meas_file_num)
        meas_file_num+=1
        data_name=file
        info_name=file[:-3]+ '.inf'
        print('info_name=',info_name)
        print('info_name=',info_name)

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

        qdm_data=open(data_name,'r')
        line=qdm_data.readline() 
#        print('First data line=',line)
        y=y_start
        while line != "":
            values=line.split()
            x=x_start
            for value in values:
                measurement=specimen+ '_' +file+ '_x' +str(x)+ '_y' +str(y)
                if "LP-SQUIDM" in meas_method_codes:
                    measurement_line=measurement+ '\t' +specimen+ '_' +file+ '\t' +specimen+ '\t' +str(sequence)+ '\tu\tg\t' +meas_method_codes+ '\t' +citations+ '\t' +str(float(value)*calibration_factor)+ '\t' +str(x*x_step)+ '\t' +str(y*y_step)+ '\t' +str(z_pos)+ '\t' +comment+ '\n'
                else:
                    measurement_line=measurement+ '\t' +specimen+ '_' +file+ '\t' +specimen+ '\t' +str(sequence)+ '\tu\tg\tLP-SQUIDM:' +meas_method_codes+ '\t' +citations+ '\t' +str(float(value)*calibration_factor)+ '\t' +str(x*x_step)+ '\t' +str(y*y_step)+ '\t' +str(z_pos)+ '\t' +comment+ '\n'
#                print('measurement_line=',measurement_line) 
                mf.write(measurement_line)
                x+=1
                sequence+=1
            y+=1
            line = qdm_data.readline() 
        qdm_data.close()
        mf.close()
    return(meas_file_num,sequence)

def update_column(df,column,value):
    #add the column with all the same values to a DataFrame
    column_values = []
    for i in df.iterrows():
        column_values.append(value)    
#    print ("column=", column)
#    print ("column_values=", column_values)
    df[column] = column_values
    return(df)
        
def append_column(df,column,value):
    # add value to all of the values in column
    for index, row in df.iterrows():
        df.loc[index,column]=value + ":" + df.loc[index,column]    
    return(df)

def add_head(table):
    # Add the the magic file format header to a data file given the table name
    # Needed because I stopped trying to find a way to keep multiple header lines using pandas
    
    file_name=table+".txt" 
    f=open(file_name,"r")
    f_before=f.read()
    f.close()
    f_after="tab\t" + table+"\n"+f_before
    f=open(file_name,"w")
    f.write(f_after)
    f.close()

def do_help():
    """
    returns help string of script
    """
    return __doc__

if __name__ == "__main__":
    main()

