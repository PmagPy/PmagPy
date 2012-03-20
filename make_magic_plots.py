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
        -p make the plots, default is to just list available plots
        -fmt [png,eps,svg,jpg] specify format, default is png
    """
    dir_path='.'
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
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
    if 'magic_measurements.txt' in filelist: # start with measurement data
        print 'working on measurements data'
        data,file_type=pmag.magic_read('magic_measurements.txt') # read in data
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
            os.system('zeq_magic.py -sav -fmt png')
        # looking for  thellier_magic possibilities
        if len(pmag.get_dictitem(data,'magic_method_codes','LP-PI-TRM','has'))>0:
            os.system('thellier_magic.py -sav -fmt png')
    if 'pmag_results.txt' in filelist: # start with measurement data
        print 'working on results'
        data,file_type=pmag.magic_read('pmag_results.txt') # read in data
        SiteDIs=pmag.get_dictitem(data,'average_dec','','F') # find decs
        SiteDIs=pmag.get_dictitem(SiteDIs,'average_inc','','F') # find decs and incs
        SiteDIs=pmag.get_dictitem(SiteDIs,'data_type','i','T') # only individual results - not poles
        coords=pmag.get_dictitem(SiteDIs,'tilt_correction','','F')
        if len(coords)>0: # there are coordinate systems specified
            SiteDIs_s=pmag.get_dictitem(SiteDIs,'tilt_correction','-1','T')# sample coordinates
            os.system('eqarea_magic.py -sav -crd s -fmt png')
            SiteDIs_g=pmag.get_dictitem(SiteDIs,'tilt_correction','0','T')# geographic coordinates
            os.system('eqarea_magic.py -sav -crd 0 -fmt png')
            SiteDIs_t=pmag.get_dictitem(SiteDIs,'tilt_correction','100','T')# tilt corrected coordinates
            os.system('eqarea_magic.py -sav -crd 100 -fmt png')
            
            
        
        
main()
