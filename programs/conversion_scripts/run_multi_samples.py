#!/usr/bin/env python

import sys,os

def main():
    """
    NAME
        run_multi_samples.py
    
    DESCRIPTION
        This program is for SQUID microscope files that have multiple samples. The program runs the 
        squidm_magic.py program using the command found in files named "commandSample_Name"
        placed in the top file directory. Then it combines the MagIC files into one MagIC 
        text file for uploading. One should run the program in the directory that has the 
        command files and the sample directories. This program may be for other file formats in the future.

        The top directory should have the sample directories and the command files. For example:

        BorlinaEtAl2020 --> commandCong14c
                            commandD175C
                            commandD175H
                            commandD175L
                            Cong14c (sample name) --> ...
                            D175C --> ...
                            D175H --> ...
                            D175L --> 150107_h18 --> data --> F1_115C_Z_150107_h18_map1.bz   (step raw data)
                                     (specimen name)          F1_115C_Z_150107_h18_map1.inf  (step info file)
                                                              F1_115C_Z_150107_h18_map1.fits (step model fit info)
                                                     demag --> 150107_h18     (CIT data file) 
                                                               150107_h18.sam (CIT sample list)
                                                     images --> F1_115C_Z_150107_h18_map1.pdf (human viewable image)
                           
        Run the program in the directory with the commands and sample directories (in the BorlinaEtAl2020 in this example).


    SYNTAX
        run_multi_samples.py

    """

    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit

    print("start")

    os.system("rm *.txt")
    os.system("rm last_measurement_number")
    os.system("rm -rf measurements")
    os.system("rm -rf images")

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
    image_list=""
    meas_list=""
    for sample in samples:
        loc_list=loc_list+sample+"/locations.txt "
        site_list=site_list+sample+"/sites.txt "
        samp_list=samp_list+sample+"/samples.txt "
        speci_list=speci_list+sample+"/specimens.txt "
        image_list=image_list+sample+"/images.txt "
        meas_list=meas_list+sample+"/measurements.txt "
    os.system("combine_magic.py -F locations.txt -f " + loc_list) 
    os.system("combine_magic.py -F sites.txt -f " + site_list) 
    os.system("combine_magic.py -F samples.txt -f " + samp_list) 
    os.system("combine_magic.py -F specimens.txt -f " + speci_list) 
    os.system("combine_magic.py -F images.txt -f " + image_list) 
    print("image_list=", image_list)
    os.system("combine_magic.py -F measurements.txt -f " + meas_list) 
    
    os.system("upload_magic.py")
      
    for sample in samples:
        os.system("rm -rf "+sample+"/measurements")
        os.system("rm -rf "+sample+"/images")
        os.system("rm -rf "+sample+"/*.txt")

    os.system("rm locations.txt sites.txt samples.txt specimens.txt measurements.txt images.txt")
    os.system("rm last_measurement_number")

    print("end")

main()
