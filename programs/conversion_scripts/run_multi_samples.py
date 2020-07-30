#!/usr/bin/env python

import sys,os

def main():
    """
    NAME
        run_multi_samples.py
    
    DESCRIPTION
        For SQUID microscope files that have multiple samples, this program runs the 
        squidm_magic.py program using the command found in files named "commandSample_Name"
        placed in the top file directory. Then it combines the MagIC files into one MagIC 
        text file for uploading. One should run the program in the directory that has the 
        command files and the sample directories.

    SYNTAX
        run_multi_samples.py

    """

    print("start")

    os.system("rm *.txt")
    os.system("rm last_measurement_number")

    dir_list=os.listdir()
    samples=[]
    for sample in dir_list:
        if sample[0] == '.':  # skip . files added by MacOS
            continue
        if "command" in sample:
            continue
        if "readme.txt" in sample:
            continue
        samples.append(sample)
    print("samples=",samples)
    os.system("rm -rf measurements")
    os.system("rm -rf images")
    os.system("mkdir measurements")
    os.system("mkdir images")
#    os.system("")
    for sample in samples:
        os.chdir(sample)
        os.system("../command"+sample)
        os.system("mv measurements/* ../measurements")
        os.system("mv images/* ../images")
        os.system("rm -rf measurements")
        os.system("rm -rf images")

        os.chdir("..")
    loc_list=""
    site_list=""
    samp_list=""
    speci_list=""
    meas_list=""
    for sample in samples:
        loc_list=loc_list+sample+"/locations.txt "
        site_list=site_list+sample+"/sites.txt "
        samp_list=samp_list+sample+"/samples.txt "
        speci_list=speci_list+sample+"/specimens.txt "
        meas_list=meas_list+sample+"/measurements.txt "
    print("loc_list=",loc_list)
    print("site_list=",site_list)
    os.system("combine_magic.py -F locations.txt -f " + loc_list) 
    os.system("combine_magic.py -F sites.txt -f " + site_list) 
    os.system("combine_magic.py -F samples.txt -f " + samp_list) 
    os.system("combine_magic.py -F specimens.txt -f " + speci_list) 
    os.system("combine_magic.py -F measurements.txt -f " + meas_list) 
    
    os.system("upload_magic.py")
      
    for sample in samples:
        os.system("rm -rf "+sample+"/measurements")
        os.system("rm -rf "+sample+"/images")
        os.system("rm -rf "+sample+"/*.txt")

    os.system("rm locations.txt sites.txt samples.txt specimens.txt measurements.txt")
    os.system("rm last_measurement_number")

    print("end")

main()
