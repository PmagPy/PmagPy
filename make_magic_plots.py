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
        -fmt [png,eps,svg,jpg,pdf] specify format, default is png
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
            os.system('zeq_magic.py -sav -fmt '+fmt)
        # looking for  thellier_magic possibilities
        if len(pmag.get_dictitem(data,'magic_method_codes','LP-PI-TRM','has'))>0:
            os.system('thellier_magic.py -sav -fmt '+fmt)
        # looking for hysteresis possibilities
        if len(pmag.get_dictitem(data,'magic_method_codes','LP-HYS','has'))>0: # find hyst experiments
            os.system('hysteresis_magic.py -sav -fmt '+fmt)
    if 'pmag_results.txt' in filelist: # start with measurement data
        print 'working on pmag_results'
        data,file_type=pmag.magic_read('pmag_results.txt') # read in data
        SiteDIs=pmag.get_dictitem(data,'average_dec','','F') # find decs
        SiteDIs=pmag.get_dictitem(SiteDIs,'average_inc','','F') # find decs and incs
        SiteDIs=pmag.get_dictitem(SiteDIs,'data_type','i','T') # only individual results - not poles
        coords=pmag.get_dictitem(SiteDIs,'tilt_correction','','F')
        if len(coords)>0: # there are coordinate systems specified
            SiteDIs_s=pmag.get_dictitem(SiteDIs,'tilt_correction','-1','T')# sample coordinates
            os.system('eqarea_magic.py -sav -crd s -fmt '+fmt)
            SiteDIs_g=pmag.get_dictitem(SiteDIs,'tilt_correction','0','T')# geographic coordinates
            os.system('eqarea_magic.py -sav -crd 0 -fmt '+fmt)
            SiteDIs_t=pmag.get_dictitem(SiteDIs,'tilt_correction','100','T')# tilt corrected coordinates
            os.system('eqarea_magic.py -sav -crd 100 -fmt '+fmt)
    if 'rmag_hysteresis.txt' in filelist: # start with measurement data
        print 'working on rmag_hysteresis'
        data,file_type=pmag.magic_read('rmag_hysteresis.txt') # read in data
        hdata=pmag.get_dictitem(data,'hysteresis_bcr','','F')
        hdata=pmag.get_dictitem(hdata,'hysteresis_mr_moment','','F')
        hdata=pmag.get_dictitem(hdata,'hysteresis_bcr','','F')
        hdata=pmag.get_dictitem(hdata,'hysteresis_bc','','F') # there are data for a dayplot
        if len(hdata)>0:
            os.system('dayplot_magic.py -sav -fmt '+fmt) 
    if 'er_sites.txt' in filelist: # start with measurement data
        print 'working on er_sites'
        os.system('basemap_magic.py -sav -fmt '+fmt)
        
        
main()
