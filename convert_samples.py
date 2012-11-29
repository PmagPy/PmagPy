#!/usr/bin/env python
import string,sys,pmag,exceptions
#
#
def main():
    """
    NAME
        convert_samples.py
   
    DESCRIPTION
        takes an er_samples.txt file and creates an orient.txt file
 
    SYNTAX
        convert_samples.py [command line options]

    OPTIONS
        -f FILE: specify input file, default is er_samples.txt
        -F FILE: specify output file, default is: orient_LOCATION.txt 

    INPUT FORMAT
        er_samples.txt formatted file
    OUTPUT
        orient.txt formatted file
    """
    #
    # initialize variables
    #
    version_num=pmag.get_version()
    orient_file,samp_file = "orient","er_samples.txt"
    args=sys.argv
    dir_path,out_path='.','.'
    #
    #
    if '-WD' in args:
        ind=args.index('-WD')
        dir_path=args[ind+1]
    if '-OD' in args:
        ind=args.index('-OD')
        out_path=args[ind+1]
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-F" in args:
        ind=args.index("-F")
        orient_file=sys.argv[ind+1]
    if "-f" in args:
        ind=args.index("-f")
        samp_file=sys.argv[ind+1]
    orient_file=out_path+'/'+orient_file
    samp_file=dir_path+'/'+samp_file
    #
    # read in file to convert
    #
    Samps,file_type=pmag.magic_read(samp_file)
    Locs=[]
    OrKeys=['sample_name','mag_azimuth','field_dip','sample_class','sample_type','sample_lithology','lat','long','stratigraphic_height','method_codes','site_name','site_description']
    SampKeys=['er_sample_name','sample_azimuth','sample_dip','sample_class','sample_type','sample_lithology','sample_lat','sample_lon','sample_height','magic_method_codes','er_site_name','er_sample_description']

    for samp in Samps:
        if samp['er_location_name'] not in Locs:Locs.append(samp['er_location_name']) # get all the location names
    for location_name in Locs:
        OrOut=[]
        for samp in Samps:
            if samp['er_location_name']==location_name:
                OrRec={}
                if 'sample_date' in samp.keys() and samp['sample_date'].strip()!="":
                    date=samp['sample_date'].split(':')
                    OrRec['date']=date[1]+'/'+date[2]+'/'+date[0][2:4]
                for i in range(len(SampKeys)): 
                   if SampKeys[i] in samp.keys():OrRec[OrKeys[i]]=samp[SampKeys[i]]
                OrOut.append(OrRec)
        loc=location_name.replace(" ","_") 
        #if '-F'!=args:outfile=orient_file+'_'+loc+'.txt'
        outfile=orient_file+'_'+loc+'.txt'
        pmag.magic_write(outfile,OrOut,location_name)
        print "Data saved in: ", outfile
main()
