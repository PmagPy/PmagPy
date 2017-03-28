#!/usr/bin/env python
from __future__ import print_function
import sys
import os


import pmagpy.pmag as pmag

def main():
    """
    NAME
        make_magic_plots.py

    DESCRIPTION
    inspects magic directory for available plots.

    SYNTAX
        make_magic_plots.py [command line options]

    INPUT
        magic files

    OPTIONS
        -h prints help message and quits
        -f FILE specifies input file name
        -fmt [png,eps,svg,jpg,pdf] specify format, default is png
        -DM [2,3] define data model
    """
    dirlist=['./']
    dir_path=os.getcwd()
    names=os.listdir(dir_path)
    for n in names:
        if 'Location' in n:
            dirlist.append(n)
    if '-fmt' in sys.argv:
        ind=sys.argv.index("-fmt")
        fmt=sys.argv[ind+1]
    else: fmt='png'
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        filelist=[sys.argv[ind+1]]
    else:
        filelist=os.listdir(dir_path)
    new_model=0
    if '-DM' in sys.argv:
        ind=sys.argv.index("-DM")
        data_model=sys.argv[ind+1]
        if data_model=='3': new_model=1
    if new_model:
            samp_file='samples.txt'
            azimuth_key='azimuth'
            meas_file='measurements.txt'
            loc_key='location'
            method_key='method_codes'
            dec_key='dir_dec'
            inc_key='dir_inc'
            Mkeys=['magnitude','magn_moment','magn_volume','magn_mass']
            results_file='sites.txt'
            tilt_key='direction_tilt_correction'
            hyst_file='specimens.txt'
            aniso_file='specimens.txt'
    else:
            new_model=0
            samp_file='er_samples.txt'
            azimuth_key='sample_azimuth'
            meas_file='magic_measurements.txt'
            loc_key='er_location_name'
            method_key='magic_method_codes'
            dec_key='measurement_dec'
            inc_key='measurement_inc'
            Mkeys=['measurement_magnitude','measurement_magn_moment','measurement_magn_volume','measurement_magn_mass']
            results_file='pmag_results.txt'
            tilt_key='tilt_correction'
            hyst_file='rmag_hysteresis'
            aniso_file='rmag_anisotropy'
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    for loc in dirlist:
        print('working on: ',loc)
        os.chdir(loc) # change working directories to each location
        crd='s'
        print(samp_file)
        if samp_file in filelist: # find coordinate systems
            print('found sample file')
            samps,file_type=pmag.magic_read(samp_file) # read in data
            Srecs=pmag.get_dictitem(samps,azimuth_key,'','F')# get all none blank sample orientations
            if len(Srecs)>0:
                crd='g'
        if meas_file in filelist: # start with measurement data
            print('working on measurements data')
            data,file_type=pmag.magic_read(meas_file) # read in data
            if loc == './': data=pmag.get_dictitem(data,loc_key,'','T') # get all the blank location names from data file
            # looking for  zeq_magic possibilities
            AFZrecs=pmag.get_dictitem(data,method_key,'LT-AF-Z','has')# get all none blank method codes
            TZrecs=pmag.get_dictitem(data,method_key,'LT-T-Z','has')# get all none blank method codes
            MZrecs=pmag.get_dictitem(data,method_key,'LT-M-Z','has')# get all none blank method codes
            Drecs=pmag.get_dictitem(data,dec_key,'','F') # get all dec measurements
            Irecs=pmag.get_dictitem(data,inc_key,'','F') # get all inc measurements
            for key in Mkeys:
                Mrecs=pmag.get_dictitem(data,key,'','F') # get intensity data
                if len(Mrecs)>0:break
            if len(AFZrecs)>0 or len(TZrecs)>0 or len(MZrecs)>0 and len(Drecs)>0 and len(Irecs)>0 and len(Mrecs)>0: # potential for stepwise demag curves
                if new_model:
                    CMD = 'zeq_magic3.py -fsp specimens.txt -sav -fmt '+fmt+' -crd '+crd
                else:
                    CMD='zeq_magic.py -fsp pmag_specimens.txt -sav -fmt '+fmt+' -crd '+crd
                print(CMD)
                os.system(CMD)
            # looking for  thellier_magic possibilities
            if len(pmag.get_dictitem(data,method_key,'LP-PI-TRM','has'))>0:
                if new_model:
                    CMD= 'thellier_magic3.py -fsp specimens.txt -sav -fmt '+fmt
                else:
                    CMD= 'thellier_magic.py -fsp pmag_specimens.txt -sav -fmt '+fmt
                print(CMD)
                os.system(CMD)
            # looking for hysteresis possibilities
            if len(pmag.get_dictitem(data,method_key,'LP-HYS','has'))>0: # find hyst experiments
                if new_model:
                    CMD= 'quick_hyst3.py -sav -fmt '+fmt
                else:
                    CMD= 'quick_hyst.py -sav -fmt '+fmt
                print(CMD)
                os.system(CMD)
        if results_file in filelist: # start with measurement data
            data,file_type=pmag.magic_read(results_file) # read in data
            print('number of datapoints: ',len(data))
            if loc == './': data=pmag.get_dictitem(data,loc_key,':','has') # get all the concatenated location names from data file
            print('number of datapoints: ',len(data) ,loc)
            if new_model:
                print('working on site directions')
                dec_key='dir_dec'
                inc_key='dir_inc'
                int_key='int_abs'
            else:
                print('working on results directions')
                dec_key='average_dec'
                inc_key='average_inc'
                int_key='average_int'
            SiteDIs=pmag.get_dictitem(data,dec_key,"",'F') # find decs
            SiteDIs=pmag.get_dictitem(SiteDIs,inc_key,"",'F') # find decs and incs
            SiteDIs=pmag.get_dictitem(SiteDIs,'data_type','i','has') # only individual results - not poles
            print('number of directions: ',len(SiteDIs))
            SiteDIs_t=pmag.get_dictitem(SiteDIs,tilt_key,'100','T')# tilt corrected coordinates
            print('number of tilt corrected directions: ',len(SiteDIs))
            SiteDIs_g=pmag.get_dictitem(SiteDIs,tilt_key,'0','T')# geographic coordinates
            SiteDIs_s=pmag.get_dictitem(SiteDIs,'tilt_correction','-1','T')# sample coordinates
            SiteDIs_x=pmag.get_dictitem(SiteDIs,'tilt_correction','','T')# no coordinates
            if len(SiteDIs_t)>0 or len(SiteDIs_g) >0 or len(SiteDIs_s)>0 or len(SiteDIs_x)>0:
                CRD=""
                if len(SiteDIs_t)>0:
                    CRD=' -crd t'
                elif len(SiteDIs_g )>0:
                    CRD=' -crd g'
                elif len(SiteDIs_s )>0:
                    CRD=' -crd s'
                if new_model:
                    CMD= 'eqarea_magic3.py -sav -crd t -fmt '+fmt +CRD
                else:
                    CMD= 'eqarea_magic.py -sav -crd t -fmt '+fmt +CRD
                print(CMD)
                os.system(CMD)
            print('working on VGP map')
            VGPs=pmag.get_dictitem(SiteDIs,'vgp_lat',"",'F') # are there any VGPs?
            if len(VGPs)>0:  # YES!
                os.system('vgpmap_magic.py -prj moll -res c -sym ro 5 -sav -fmt png')
            print('working on intensities')
            if not new_model:
                CMD='magic_select.py -f '+results_file+' -key data_type i T -F tmp.txt'
                os.system(CMD)
                infile=' tmp.txt'
            else: infile=results_file
            print(int_key)
            CMD='magic_select.py  -key '+int_key +' 0. has -F tmp1.txt -f '+infile
            os.system(CMD)
            CMD="grab_magic_key.py -f tmp1.txt -key "+int_key+ " | awk '{print $1*1e6}' >tmp2.txt"
            os.system(CMD)
            data,file_type=pmag.magic_read('tmp1.txt') # read in data
            if new_model:
                locations=pmag.get_dictkey(data,loc_key,"")
            else:
                locations=pmag.get_dictkey(data,loc_key+'s',"")
            histfile='LO:_'+locations[0]+'_intensities_histogram:_.'+fmt
            os.system("histplot.py -b 1 -xlab 'Intensity (uT)' -sav -f tmp2.txt -F " +histfile)
            print("histplot.py -b 1 -xlab 'Intensity (uT)' -sav -f tmp2.txt -F " +histfile)
            os.system('rm tmp*.txt')
        if hyst_file in filelist: # start with measurement data
            print('working on hysteresis')
            data,file_type=pmag.magic_read(hyst_file) # read in data
            if loc == './': data=pmag.get_dictitem(data,loc_key,'','T') # get all the blank location names from data file
            hdata=pmag.get_dictitem(data,'hysteresis_bcr','','F')
            hdata=pmag.get_dictitem(hdata,'hysteresis_mr_moment','','F')
            hdata=pmag.get_dictitem(hdata,'hysteresis_ms_moment','','F')
            hdata=pmag.get_dictitem(hdata,'hysteresis_bc','','F') # there are data for a dayplot
            if len(hdata)>0:
                print('dayplot_magic.py -sav -fmt '+fmt)
                os.system('dayplot_magic.py -sav -fmt '+fmt)
        if aniso_file in filelist: # do anisotropy plots if possible
            print('working on anisotropy')
            data,file_type=pmag.magic_read(aniso_file) # read in data
            if loc == './': data=pmag.get_dictitem(data,loc_key,'','T') # get all the blank location names from data file
            sdata=pmag.get_dictitem(data,'anisotropy_tilt_correction','-1','T') # get specimen coordinates
            gdata=pmag.get_dictitem(data,'anisotropy_tilt_correction','0','T') # get specimen coordinates
            tdata=pmag.get_dictitem(data,'anisotropy_tilt_correction','100','T') # get specimen coordinates
            CRD=""
            if new_model:
                CMD= 'aniso_magic3.py -x -B -sav -fmt '+fmt
            else:
                CMD= 'aniso_magic.py -x -B -sav -fmt '+fmt
            if len(sdata)>3:
                CMD=CMD+' -crd s'
                print(CMD)
                os.system(CMD)
            if len(gdata)>3:
                CMD=CMD+' -crd g'
                print(CMD)
                os.system(CMD)
            if len(tdata)>3:
                CMD=CMD+' -crd t'
                print(CMD)
                os.system(CMD)
        if loc!='./':os.chdir('..') # change working directories to each location

if __name__ == "__main__":
    main()
