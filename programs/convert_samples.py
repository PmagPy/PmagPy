#!/usr/bin/env python
from __future__ import print_function
from builtins import range
import sys
import pmagpy.pmag as pmag
#
#
def main():
    """
    NAME
        convert_samples.py
   
    DESCRIPTION
        takes an er_samples or magic_measurements format file and creates an orient.txt template
 
    SYNTAX
        convert_samples.py [command line options]

    OPTIONS
        -f FILE: specify input file, default is er_samples.txt
        -F FILE: specify output file, default is: orient_LOCATION.txt 

    INPUT FORMAT
        er_samples.txt or magic_measurements format file
    OUTPUT
        orient.txt format file
    """
    #
    # initialize variables
    #
    version_num=pmag.get_version()
    orient_file,samp_file = "orient","er_samples.txt"
    args=sys.argv
    dir_path,out_path='.','.'
    default_outfile = True
    #
    #
    if '-WD' in args:
        ind=args.index('-WD')
        dir_path=args[ind+1]
    if '-OD' in args:
        ind=args.index('-OD')
        out_path=args[ind+1]
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    if "-F" in args:
        ind=args.index("-F")
        orient_file=sys.argv[ind+1]
        default_outfile = False
    if "-f" in args:
        ind=args.index("-f")
        samp_file=sys.argv[ind+1]
    orient_file=out_path+'/'+orient_file
    samp_file=dir_path+'/'+samp_file
    #
    # read in file to convert
    #
    ErSamples=[]
    Required=['sample_class','sample_type','sample_lithology','lat','long']
    Samps,file_type=pmag.magic_read(samp_file)
    Locs=[]
    OrKeys=['sample_name','site_name','mag_azimuth','field_dip','sample_class','sample_type','sample_lithology','lat','long','stratigraphic_height','method_codes','site_description']
    print("file_type", file_type) # LJ
    if file_type.lower()=='er_samples':
        SampKeys=['er_sample_name','er_site_name','sample_azimuth','sample_dip','sample_class','sample_type','sample_lithology','sample_lat','sample_lon','sample_height','magic_method_codes','er_sample_description']
    elif file_type.lower()=='magic_measurements':
        SampKeys=['er_sample_name','er_site_name']
    else:
        print('wrong file format; must be er_samples or magic_measurements only')
    for samp in Samps:
            if samp['er_location_name'] not in Locs:Locs.append(samp['er_location_name']) # get all the location names
    for location_name in Locs:
        loc_samps=pmag.get_dictitem(Samps,'er_location_name',location_name,'T')
        OrOut=[]
        for samp in loc_samps:
            if samp['er_sample_name'] not in ErSamples:
                ErSamples.append(samp['er_sample_name'])
                OrRec={}
                if 'sample_date' in list(samp.keys()) and samp['sample_date'].strip()!="":
                    date=samp['sample_date'].split(':')
                    OrRec['date']=date[1]+'/'+date[2]+'/'+date[0][2:4]
                for i in range(len(SampKeys)): 
                    if SampKeys[i] in list(samp.keys()):OrRec[OrKeys[i]]=samp[SampKeys[i]]
                for key in Required:
                    if key not in list(OrRec.keys()):OrRec[key]="" # fill in blank required keys 
                OrOut.append(OrRec)
        loc=location_name.replace(" ","_") 
        if default_outfile:
            outfile=orient_file+'_'+loc+'.txt'
        else:
            outfile=orient_file
        pmag.magic_write(outfile,OrOut,location_name)
        print("Data saved in: ", outfile)

if __name__ == "__main__":
    main()
