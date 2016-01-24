#!/usr/bin/env python
# define some variables
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME 
        update_measurements.py

    DESCRIPTION
        update the magic_measurements table with new orientation info
 
    SYNTAX
        update_measurements.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f MFILE, specify magic_measurements file; default is magic_measurements.txt
        -fsa SFILE, specify er_samples table; default is er_samples.txt
        -F OFILE, specify output file, default is same as MFILE
    """
    dir_path='.'
    meas_file='magic_measurements.txt'
    samp_file="er_samples.txt"
    out_file='magic_measurements.txt'
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        meas_file=sys.argv[ind+1]
    if '-fsa' in sys.argv:
        ind = sys.argv.index('-fsa')
        samp_file=sys.argv[ind+1]
    if '-F' in sys.argv:
        ind = sys.argv.index('-F')
        out_file=sys.argv[ind+1]
    # read in measurements file
    meas_file=dir_path+'/'+meas_file
    out_file=dir_path+'/'+out_file
    samp_file=dir_path+'/'+samp_file
    data,file_type=pmag.magic_read(meas_file)
    samps,file_type=pmag.magic_read(samp_file)
    MeasRecs=[]
    sampnames,sflag=[],0
    for rec in data:
        for samp in  samps:
            if samp['er_sample_name'].lower()==rec['er_sample_name'].lower():
                if samp['er_sample_name'] not in sampnames:sampnames.append(samp['er_sample_name'].lower())
                rec['er_site_name']=samp['er_site_name']
                rec['er_location_name']=samp['er_location_name']
                MeasRecs.append(rec)
                break
        if rec['er_sample_name'].lower() not in sampnames:
            sampnames.append(rec['er_sample_name'].lower())
            sflag=1
            SampRec={}
            for key in samps[0].keys():SampRec[key]=""
            SampRec['er_sample_name']=rec['er_sample_name']
            SampRec['er_citation_names']="This study"
            SampRec['er_site_name']='MISSING'
            SampRec['er_location_name']='MISSING'
            SampRec['sample_desription']='recorded added by update_measurements - edit as needed'
            samps.append(SampRec)
            print rec['er_sample_name'],' missing from er_samples.txt file - edit orient.txt file and re-import'
            rec['er_site_name']='MISSING'
            rec['er_location_name']='MISSING'
            MeasRecs.append(rec)
    pmag.magic_write(out_file,MeasRecs,'magic_measurements')
    print "updated measurements file stored in ", out_file
    if sflag==1:
         pmag.magic_write(samp_file,samps,'er_samples')
         print "updated sample file stored in ", samp_file

if __name__ == "__main__":
    main()
