#!/usr/bin/env python
import sys,os
import pandas as pd

def main():
    """
    NAME
        mit_squid_magic.py

    DESCRIPTION
        converts 2019 SQUID files into a MagIC format measurement file

    SYNTAX
        mit_squid_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.

        -d DIRECTORY: specify directory where the slide folders are located, otherwise current directory is used.

        -s: set the starting measurement sequence number. Default:1

        -location: specify location/study name

        -location_type: specify location_type (see https://www.earthref.org/vocabularies/controlled for a list of types)

        -geologic_classes: specify geologic_classes. (see https://www.earthref.org/vocabularies/controlled for a list of classes)

        -lithologies: specify lithologies. Put a colon between multiple lithologies (see https://www.earthref.org/vocabularies/controlled for a list of lithologies)

        -lat_n: specify north latitude of location bounding box.

        -lat_s: specify south latitude of location bounding box. N and S can be the same for a point location.

        -lon_w: specify west longitude of location bounding box.

        -lon_e: specify east longitude of location bounding box. E and W can be the same for a point location.

        -age: specify the age of the samples and location. (One must have an age defined. agelow and agehigh can be used in addition to or in place of age.

        -age_sigma: specify the one sigma error on the age.

        -age_low: specify the low bound for the age. 

        -age_high: specify the hig bound for the age.

        -age_unit: specify the age unit. ka, Ma, Ga are some examples. (see https://www.earthref.org/vocabularies/controlled for the full list)
        -citations: list of citations. Default: "This study". "This study" can be used for the study this MagIC contribution will be associated with. Use DOIs for other studies.

        -site_geologic_types: geologic types of the site (put a colon between types if more than one is used)

        -method_codes: method_codes used at the site, sample, and specimen level (use colon between multiple codes)

        -instrument_codes: used to identify the insturment that made the measurement. Exact insturment name prefered, not type
    
        -z_pos: distance from the surface in meters. default:0

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

    """

    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit

    if '-s' in sys.argv:
        ind=sys.argv.index('-s')
        sequence=int(sys.argv[ind+1])
        print("-s =",sys.argv[ind+1])
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
   
    if '-lat_n' in sys.argv:
        ind=sys.argv.index('-lat_n')
        lat_n=sys.argv[ind+1]
    else:
        print("The north latitude must be set with the -lat_n flag")
        exit()
   
    if '-lat_s' in sys.argv:
        ind=sys.argv.index('-lat_s')
        lat_s=sys.argv[ind+1]
    else:
        print("The south latitude must be set with the -lat_s flag")
        exit()
   
    if '-lon_w' in sys.argv:
        ind=sys.argv.index('-lon_w')
        lon_w=sys.argv[ind+1]
    else:
        print("The west longitude  must be set with the -lon_w flag")
        exit()
   
    if '-lon_e' in sys.argv:
        ind=sys.argv.index('-lon_e')
        lon_e=sys.argv[ind+1]
    else:
        print("The east longitude  must be set with the -lon_e flag")
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
        print("The age unit  must be set with the -ageunit flag")
        exit()

    if '-citations' in sys.argv:
        ind=sys.argv.index('-citations')
        citations=sys.argv[ind+1]
    else:
        citations="This study"
        exit()
   
    if '-method_codes' in sys.argv:
        ind=sys.argv.index('-method_codes')
        method_codes=sys.argv[ind+1]
    else:
        print("The method codes must be set with the -method_codes flag. Set at least the geochronology(GM-) method code.")
        exit()
   
    if '-instrument_codes' in sys.argv:
        ind=sys.argv.index('-instrument_codes')
        instrument_codes=sys.argv[ind+1]
    else:
        instrument_codes=""
   
    if '-site_geologic_types' in sys.argv:
        ind=sys.argv.index('-site_geologic_types')
        site_geologic_types=sys.argv[ind+1]
    else:
        print("The site geologic types for the site name must be set with the -site_geologic_types flag")
        exit()
   
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
#   Create the large measurement.txt files for each slide by translating the data and combining demag steps 

    print("start")

    os.system("rm locations.txt sites.txt samples.txt specimens.txt measurements.txt")
    dir_list=os.listdir()
    print(sorted(dir_list))
    slide_dir_list=[]
    for dir in sorted(dir_list):
        if dir[0] == '.':   # skip . files added by MacOS
            continue
        elif dir == 'command':   # skip command file 
            continue
        slide_dir_list.append(dir+'/demag/')
        os.chdir(dir+'/demag')     
        command='cit_magic.py -ncn ' + ncn + ' -f ' + dir + '.sam -loc "' + location + '" -mcd ' + method_codes
        print(command)
        os.system(command)

        # add info to locations table
        df=pd.read_csv("locations.txt",sep="\t",header=1)
        print(df)
        df=update_column(df,"location_type",location_type)
        df=update_column(df,"geologic_classes",geologic_classes)
        df=update_column(df,"lithologies",lithologies)
        df=update_column(df,"lat_n",lat_n)
        df=update_column(df,"lat_s",lat_s)
        df=update_column(df,"lon_w",lon_w)
        df=update_column(df,"lon_e",lon_e)
        if age!="":
            df=update_column(df,"age",age)
        if age_high!="":
            df=update_column(df,"age_high",age_high)
        if age_low!="":
            df=update_column(df,"age_low",age_low)
        df=update_column(df,"age_unit",age_unit)
        df=update_column(df,"citations",citations)
        df=update_column(df,"method_codes",method_codes)
        print(df)

        df.to_csv("locations.txt",sep='\t',index=False)
        add_head("locations")
        os.system("cp locations.txt ../..")

        # add info to sites table
        df=pd.read_csv("sites.txt",sep="\t",header=1)
        print(df)
        df=update_column(df,"geologic_classes",geologic_classes)
        df=update_column(df,"lithologies",lithologies)
        df=update_column(df,"lat",lat_n)
        df=update_column(df,"lon",lon_w)
        if age!="":
            df=update_column(df,"age",age)
        if age_high!="":
            df=update_column(df,"age_high",age_high)
        if age_low!="":
            df=update_column(df,"age_low",age_low)
        df=update_column(df,"age_unit",age_unit)
        df=update_column(df,"method_codes",method_codes)
        df=update_column(df,"citations",citations)
        df=update_column(df,"geologic_types",site_geologic_types)
        print(df)
        df.to_csv("sites.txt",sep='\t',index=False)
        add_head("sites")

        # add info to samples table
        df=pd.read_csv("samples.txt",sep="\t",header=1)
        print(df)
        df=update_column(df,"lat",lat_n)
        df=update_column(df,"lon",lon_w)
        df=append_column(df,"method_codes",method_codes)
        df=update_column(df,"citations",citations)
        print(df)
        df.to_csv("samples.txt",sep='\t',index=False)
        add_head("samples")

        # add info to samples table
        df=pd.read_csv("specimens.txt",sep="\t",header=1)
        print(df)
        df=append_column(df,"method_codes",method_codes)
        df=update_column(df,"citations",citations)
        print(df)
        df.to_csv("specimens.txt",sep='\t',index=False)
        add_head("specimens")

        # add info to measurements table
        df=pd.read_csv("measurements.txt",sep="\t",header=1)
        print(df)
        df=append_column(df,"method_codes",method_codes)
        df=update_column(df,"citations",citations)
        df=update_column(df,"instrument_codes",instrument_codes)
        print(df)
        df.to_csv("measurements.txt",sep='\t',index=False)
        add_head("measurements")

        # Create the large MagIC measurement files for the raw QDM data scans
        os.chdir('../data')     
        convert_squid_data(dir,citations,z_pos)

        os.chdir('../..')     



    print("slide dir list=",slide_dir_list)
    loc_files=""
    site_files=""
    samp_files=""
    spec_files=""
    meas_files=""
    for dir in slide_dir_list:
        print("dir=",dir)
#        loc_files+=dir+"locations.txt "
        site_files+=dir+"sites.txt "
        samp_files+=dir+"samples.txt "
        spec_files+=dir+"specimens.txt "
        meas_files+=dir+"measurements.txt "

#    print('loc_files=',loc_files)
#    os.system("combine_magic.py -F locations.txt -f " + loc_files)
    os.system("combine_magic.py -F sites.txt -f " + site_files)
    os.system("combine_magic.py -F samples.txt -f " + samp_files)
    os.system("combine_magic.py -F specimens.txt -f " + spec_files)
    os.system("combine_magic.py -F measurements.txt -f " + meas_files)

    os.system("upload_magic.py")
    os.system("rm locations.txt sites.txt samples.txt specimens.txt measurements.txt")

    print("end")   
    return()


def convert_squid_data(specimen,citations,z_pos):
#   Take the SQUID magnetometer files and make MagIC measurement files. This data will not be uploaded 
#   in the contribution MagIC data file due is large size, but will be available for download. 
#   Each scan's data is put in a seperate measurements.txt file in its own directory.   
    
    mf=open('measurements.txt','w')
    mf.write("tab\tmeasurements\n")
    mf.write('measurement\texperiment\tspecimen\tsequence\tstandard\tquality\tmethod_codes\tcitations\tmagn_z\tmeas_pos_x\tmeas_pos_y\tmeas_pos_z\tdescription\n')

    file_list=os.listdir()
    print(sorted(file_list))
        
    for file in sorted(file_list):
        if file[0] == '.':   # skip . files added by MacOS
            continue
        if file == 'measurements.txt':   #  measurement file
            continue
        print('file=',file)
        if '.inf' in file:       # do processing on both files in the .bz loop as we need data in both to create the measurements file
            continue
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
        y=0
        while line != "":
            values=line.split()
            x=0
            sequence=1
            for value in values:
#                print('value=',value,' x=',x,' y=',y) 
#                print('sequence=',sequence)
#                if value == '':
#                    value='0' 
#                if value == '\t':
#                    value='0' 
                measurement=specimen+ '_' +file+ '_x' +str(x)+ '_y' +str(y)
                measurement_line=measurement+ '\t' +specimen+ '_' +file+ '\t' +specimen+ '\t' +str(sequence)+ '\tu\tg\tLP-SQUIDM\t' +citations+ '\t' +str(float(value)*calibration_factor)+ '\t' +str(x*x_step)+ '\t' +str(y*y_step)+ '\t' +str(z_pos)+ '\t' +comment+ '\n'
#                print('measurement_line=',measurement_line) 
                mf.write(measurement_line)
                x+=1
                sequence+=1
            y+=1
            line = qdm_data.readline() 
        qdm_data.close()
    mf.close()
    return()

def update_column(df,column,value):
    #add the column with all the same values to a DataFrame
    column_values = []
    for i in df.iterrows():
        column_values.append(value)    
    print ("column=", column)
    print ("column_values=", column_values)
    df[column] = column_values
    return(df)
        
def append_column(df,column,value):
    # add value to all of the values in column
    for index, row in df.iterrows():
        df.loc[index,column]=value + ":" + df.loc[index,column]    
    return(df)

def add_head(table):
    # Add the the magic file format header to a data file given the table name
    # Needed because I stopped trying to find a way to keep the header lines using pandas
    
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

