#!/usr/bin/env python
import pmag,sys,os,exceptions
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
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    for loc in dirlist:
        print 'working on: ',loc
        os.chdir(loc) # change working directories to each location
        crd='s'
        if 'er_samples.txt' in filelist: # find coordinate systems
            samps,file_type=pmag.magic_read('er_samples.txt') # read in data
            Srecs=pmag.get_dictitem(samps,'sample_azimuth','','F')# get all none blank sample orientations
            if len(Srecs)>0: 
                crd='g'
        if 'magic_measurements.txt' in filelist: # start with measurement data
            print 'working on measurements data'
            data,file_type=pmag.magic_read('magic_measurements.txt') # read in data
            if loc == './': data=pmag.get_dictitem(data,'er_location_name','','T') # get all the blank location names from data file
            # looking for  zeq_magic possibilities
            AFZrecs=pmag.get_dictitem(data,'magic_method_codes','LT-AF-Z','has')# get all none blank method codes
            TZrecs=pmag.get_dictitem(data,'magic_method_codes','LT-T-Z','has')# get all none blank method codes
            MZrecs=pmag.get_dictitem(data,'magic_method_codes','LT-M-Z','has')# get all none blank method codes
            Drecs=pmag.get_dictitem(data,'measurement_dec','','F') # get all dec measurements
            Irecs=pmag.get_dictitem(data,'measurement_inc','','F') # get all dec measurements
            Mkeys=['measurement_magnitude','measurement_magn_moment','measurement_magn_volume','measurement_magn_mass']
            for key in Mkeys:
                Mrecs=pmag.get_dictitem(data,key,'','F') # get intensity data
                if len(Mrecs)>0:break
            if len(AFZrecs)>0 or len(TZrecs)>0 or len(MZrecs)>0 and len(Drecs)>0 and len(Irecs)>0 and len(Mrecs)>0: # potential for stepwise demag curves 
                print 'zeq_magic.py -sav -fmt '+fmt+' -crd '+crd
                os.system('zeq_magic.py -sav -fmt '+fmt+' -crd '+crd )
                #pass
            # looking for  thellier_magic possibilities
            if len(pmag.get_dictitem(data,'magic_method_codes','LP-PI-TRM','has'))>0:
                print 'thellier_magic.py -sav -fmt '+fmt
                os.system('thellier_magic.py -sav -fmt '+fmt)
                #pass
            # looking for hysteresis possibilities
            if len(pmag.get_dictitem(data,'magic_method_codes','LP-HYS','has'))>0: # find hyst experiments
                print 'quick_hyst.py -sav -fmt '+fmt
                os.system('quick_hyst.py -sav -fmt '+fmt)
                #pass
        if 'pmag_results.txt' in filelist: # start with measurement data
            print 'working on pmag_results'
            data,file_type=pmag.magic_read('pmag_results.txt') # read in data
            if loc == './': data=pmag.get_dictitem(data,'er_location_name','','T') # get all the blank location names from data file
            SiteDIs=pmag.get_dictitem(data,'average_dec','','F') # find decs
            SiteDIs=pmag.get_dictitem(SiteDIs,'average_inc','','F') # find decs and incs
            SiteDIs=pmag.get_dictitem(SiteDIs,'data_type','i','T') # only individual results - not poles
            coords=pmag.get_dictitem(SiteDIs,'tilt_correction','','F')
            if len(coords)>0: # there are coordinate systems specified
                SiteDIs_s=pmag.get_dictitem(SiteDIs,'tilt_correction','-1','T')# sample coordinates
                print 'eqarea_magic.py -sav -crd s -fmt '+fmt
                os.system('eqarea_magic.py -sav -crd s -fmt '+fmt)
                SiteDIs_g=pmag.get_dictitem(SiteDIs,'tilt_correction','0','T')# geographic coordinates
                os.system('eqarea_magic.py -sav -crd g -fmt '+fmt)
                SiteDIs_t=pmag.get_dictitem(SiteDIs,'tilt_correction','100','T')# tilt corrected coordinates
                os.system('eqarea_magic.py -sav -crd t -fmt '+fmt)
        if 'rmag_hysteresis.txt' in filelist: # start with measurement data
            print 'working on rmag_hysteresis'
            data,file_type=pmag.magic_read('rmag_hysteresis.txt') # read in data
            if loc == './': data=pmag.get_dictitem(data,'er_location_name','','T') # get all the blank location names from data file
            hdata=pmag.get_dictitem(data,'hysteresis_bcr','','F')
            hdata=pmag.get_dictitem(hdata,'hysteresis_mr_moment','','F')
            hdata=pmag.get_dictitem(hdata,'hysteresis_ms_moment','','F')
            hdata=pmag.get_dictitem(hdata,'hysteresis_bc','','F') # there are data for a dayplot
            if len(hdata)>0:
                print 'dayplot_magic.py -sav -fmt '+fmt
                os.system('dayplot_magic.py -sav -fmt '+fmt) 
    #if 'er_sites.txt' in filelist: # start with measurement data
        #    print 'working on er_sites'
            #os.system('basemap_magic.py -sav -fmt '+fmt)
        if 'rmag_anisotropy.txt' in filelist: # do anisotropy plots if possible
            print 'working on rmag_anisotropy'
            data,file_type=pmag.magic_read('rmag_anisotropy.txt') # read in data
            if loc == './': data=pmag.get_dictitem(data,'er_location_name','','T') # get all the blank location names from data file
            sdata=pmag.get_dictitem(data,'anisotropy_tilt_correction','-1','T') # get specimen coordinates
            gdata=pmag.get_dictitem(data,'anisotropy_tilt_correction','0','T') # get specimen coordinates
            tdata=pmag.get_dictitem(data,'anisotropy_tilt_correction','100','T') # get specimen coordinates
            if len(sdata)>3:
                print 'aniso_magic.py -x -B -crd s -sav -fmt '+fmt
                os.system('aniso_magic.py -x -B -crd s -sav -fmt '+fmt)
            if len(gdata)>3:
                os.system('aniso_magic.py -x -B -crd g -sav -fmt '+fmt)
            if len(tdata)>3:
                os.system('aniso_magic.py -x -B -crd t -sav -fmt '+fmt)
        if loc!='./':os.chdir('..') # change working directories to each location
        
main()
