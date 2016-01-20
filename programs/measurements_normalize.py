#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag
#
#
def main():
    """
    NAME
        measurements_normalize.py
   
    DESCRIPTION
        takes magic_measurements file and normalized moment by sample_weight and sample_volume in the er_specimens table
 
    SYNTAX
        measurements_normalize.py [command line options]

    OPTIONS
        -f FILE: specify input file, default is: magic_measurements.txt
        -fsp FILE: specify input specimen file, default is: er_specimens.txt 
        -F FILE: specify output measurements, default is to overwrite input file

    """
    #
    # initialize variables
    #
    #
    #
    dir_path='.'
    if "-WD" in sys.argv:
        ind=sys.argv.index("-WD")
        dir_path=sys.argv[ind+1]
    meas_file,spec_file= dir_path+"/magic_measurements.txt",dir_path+"/er_specimens.txt"
    out_file=meas_file
    MeasRecs,SpecRecs=[],[]
    OutRecs=[]
    if "-h" in sys.argv:
        print main.__doc__
        sys.exit()
    if "-f" in sys.argv:
        ind=sys.argv.index("-f")
        meas_file=dir_path+'/'+sys.argv[ind+1]
    if "-fsp" in sys.argv:
        ind=sys.argv.index("-fsp")
        spec_file=dir_path+'/'+sys.argv[ind+1]
    if "-F" in sys.argv:
        ind=sys.argv.index("-F")
        out_file=dir_path+'/'+sys.argv[ind+1]
    MeasRecs,file_type=pmag.magic_read(meas_file)
    Specs,file_type=pmag.magic_read(spec_file)
    for rec in MeasRecs:
        if 'measurement_magn_moment' in rec.keys() and rec['measurement_magn_moment'] != "":
            for spec in Specs:
                if spec['er_specimen_name']==rec['er_specimen_name']:
                    if 'specimen_weight' in spec.keys() and spec['specimen_weight']!="":
                        rec['measurement_magn_mass']='%e'%(float(rec['measurement_magn_moment'])/float(spec['specimen_weight']))
                    if 'specimen_volume' in spec.keys() and spec['specimen_volume']!="":
                        rec['measurement_magn_volume']='%e'%(float(rec['measurement_magn_moment'])/float(spec['specimen_volume']))
                    break
        if 'measurement_magn_volume' not in rec.keys(): rec['measurement_magn_volume']=''
        if 'measurement_magn_mass' not in rec.keys(): rec['measurement_magn_mass']=''
        OutRecs.append(rec) 
    pmag.magic_write(out_file,OutRecs,"magic_measurements")
    print "Data saved in ", out_file

if __name__ == "__main__":
    main()
