#!/usr/bin/env python
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag


def main():
    """
    NAME
        strip_magic.py

    DESCRIPTION
        plots various parameters versus depth or age

    SYNTAX
        strip_magic.py [command line optins]

    OPTIONS
        -h prints help message and quits
        -DM NUM: specify data model num, options 2 (legacy) or 3 (default)
        -f FILE: specify input magic format file from magic,default='pmag_results.txt'
         supported types=[pmag_specimens, pmag_samples, pmag_sites, pmag_results, magic_web]
        -obj [sit,sam,all]: specify object to site,sample,all for pmag_result table, default is all
        -fmt [svg,png,jpg], format for images - default is svg
        -x [age,pos]:  specify whether age or stratigraphic position
        -y [dec,inc,int,chi,lat,lon,vdm,vadm]
           (lat and lon are VGP lat and lon)
        -Iex: plot the expected inc at lat - only available for results with lat info in file
        -ts TS amin amax: plot the GPTS for the time interval between amin and amax (numbers in Ma)
           TS: [ck95, gts04]
        -mcd method_code, specify method code, default is first one encountered
        -sav  save plot and quit
    NOTES
        when x and/or y are not specified, a list of possibilities will be presented to the user for choosing

    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    xaxis, xplotind, yplotind = "", 0, 0  # (0 for strat pos)
    yaxis, Xinc = "", ""
    plot = 0
    obj = 'all'
    data_model_num = int(pmag.get_named_arg("-DM", 3))
    # 2.5 keys
    if data_model_num == 2:
        supported = ['pmag_specimens', 'pmag_samples',
                     'pmag_sites', 'pmag_results', 'magic_web'] # available file types
        Depth_keys = ['specimen_core_depth', 'specimen_height', 'specimen_elevation',
                      'specimen_composite_depth', 'sample_core_depth', 'sample_height',
                      'sample_elevation', 'sample_composite_depth', 'site_core_depth',
                      'site_height', 'site_elevation', 'site_composite_depth', 'average_height']
        Age_keys = ['specimen_inferred_age', 'sample_inferred_age',
                    'site_inferred_age', 'average_age']
        Unit_keys = {'specimen_inferred_age': 'specimen_inferred_age_unit',
                     'sample_inferred_age': 'sample_inferred_age_unit',
                     'site_inferred_age': 'site_inferred_age_unit', 'average_age': 'average_age_unit'}
        Dec_keys = ['measurement_dec', 'specimen_dec',
                    'sample_dec', 'site_dec', 'average_dec']
        Inc_keys = ['measurement_inc', 'specimen_inc',
                    'sample_inc', 'site_inc', 'average_inc']
        Int_keys = ['measurement_magnitude', 'measurement_magn_moment', 'measurement_magn_volume',
                    'measurement_magn_mass', 'specimen_int', 'specimen_int_rel', 'sample_int',
                    'sample_int_rel', 'site_int', 'site_int_rel', 'average_int', 'average_int_rel']
        Chi_keys = ['measurement_chi_volume', 'measurement_chi_mass']
        Lat_keys = ['sample_lat', 'site_lat', 'average_lat']
        VLat_keys = ['vgp_lat']
        VLon_keys = ['vgp_lon']
        Vdm_keys = ['vdm']
        Vadm_keys = ['vadm']
        method_col_name = "magic_method_codes"
    else:
        # 3.0 keys
        supported = ["specimens", "samples", "sites", "locations"] # available file types
        Depth_keys = [ "height", "core_depth", "elevation", "composite_depth" ]
        Age_keys = [ "age" ]
        Unit_keys = { "age": "age" }
        Chi_keys = [ "susc_chi_volume", "susc_chi_mass" ]
        Int_keys = [ "magn_moment", "magn_volume", "magn_mass", "int_abs", "int_rel" ]
        Inc_keys = [ "dir_inc" ]
        Dec_keys = [ "dir_dec" ]
        Lat_Keys = [ "lat" ]
        VLat_keys = [ "vgp_lat", "pole_lat" ]
        VLon_keys = [ "vgp_lon", "pole_lon" ]
        Vdm_keys = [ "vdm", "pdm" ]
        Vadm_keys = [ "vadm", "padm" ]
        method_col_name = "method_codes"

    #
    X_keys = [Age_keys, Depth_keys]
    Y_keys = [Dec_keys, Inc_keys, Int_keys, Chi_keys,
              VLat_keys, VLon_keys, Vdm_keys, Vadm_keys]
    method, fmt = "", 'svg'
    FIG = {'strat': 1}
    plotexp, pTS = 0, 0
    dir_path = pmag.get_named_arg("-WD", ".")
    # default files
    if data_model_num == 3:
        res_file = pmag.get_named_arg("-f", "sites.txt")
    else:
        res_file = pmag.get_named_arg("-f", "pmag_results.txt")
    res_file = pmag.resolve_file_name(res_file, dir_path)
    if '-fmt' in sys.argv:
        ind = sys.argv.index('-fmt')
        fmt = sys.argv[ind+1]
    if '-obj' in sys.argv:
        ind = sys.argv.index('-obj')
        obj = sys.argv[ind+1]
    if '-x' in sys.argv:
        ind = sys.argv.index('-x')
        xaxis = sys.argv[ind+1]
    if '-y' in sys.argv:
        ind = sys.argv.index('-y')
        yaxis = sys.argv[ind+1]
        if yaxis == 'dec':
            ykeys = Dec_keys
        if yaxis == 'inc':
            ykeys = Inc_keys
        if yaxis == 'int':
            ykeys = Int_keys
        if yaxis == 'chi':
            ykeys = Chi_keys
        if yaxis == 'lat':
            ykeys = VLat_keys
        if yaxis == 'lon':
            ykeys = VLon_keys
        if yaxis == 'vdm':
            ykeys = Vdm_keys
        if yaxis == 'vadm':
            ykeys = Vadm_keys
    if '-mcd' in sys.argv:
        ind = sys.argv.index('-mcd')
        method = sys.argv[ind+1]
    if '-ts' in sys.argv:
        ind = sys.argv.index('-ts')
        ts = sys.argv[ind+1]
        amin = float(sys.argv[ind+2])
        amax = float(sys.argv[ind+3])
        pTS = 1
    if '-Iex' in sys.argv:
        plotexp = 1
    if '-sav' in sys.argv:
        plot = 1
    #
    #
    # get data read in
    Results, file_type = pmag.magic_read(res_file)
    if file_type not in supported:
        print("Unsupported file type ({}), try again".format(file_type))
        sys.exit()
    PltObjs = ['all']
    if data_model_num == 2:
        if file_type == 'pmag_results':  # find out what to plot
            for rec in Results:
                resname = rec['pmag_result_name'].split()
                if 'Sample' in resname and 'sam' not in PltObjs:
                    PltObjs.append('sam')
                if 'Site' in resname and 'sit' not in PltObjs:
                    PltObjs.append('sit')


    methcodes = []
    # need to know all the measurement types from method_codes
    if "magic_method_codes" in list(Results[0].keys()):
        for rec in Results:
            meths = rec["magic_method_codes"].split(":")
            for meth in meths:
                if meth.strip() not in methcodes and 'LP' in meth:
                    # look for the lab treatments
                    methcodes.append(meth.strip())
    #
    # initialize some variables
    X_unit = ""  # Unit for age or depth plotting (meters if depth)
    Xplots, Yplots = [], []
    Xunits = []
    yplotind, xplotind = 0, 0
    #
    # step through possible plottable keys
    #
    if xaxis == "" or yaxis == "":
        for key in list(Results[0].keys()):
            for keys in X_keys:
                for xkeys in keys:
                    if key in xkeys:
                        for ResRec in Results:
                            if ResRec[key] != "":
                                # only plot something if there is something to plot!
                                Xplots.append(key)
                                break
            for keys in Y_keys:
                for pkeys in keys:
                    if key in pkeys:
                        for ResRec in Results:
                            if ResRec[key] != "":
                                Yplots.append(key)
                                break
        X, Y = [], []
        for plt in Xplots:
            if plt in Age_keys and 'age' not in X:
                X.append('age')
            if plt in Depth_keys and 'pos' not in X:
                X.append('pos')
        for plt in Yplots:
            if plt in Dec_keys and 'dec' not in Y:
                Y.append('dec')
            if plt in Inc_keys and 'inc' not in Y:
                Y.append('inc')
            if plt in Int_keys and 'int' not in Y:
                Y.append('int')
            if plt in Chi_keys and 'chi' not in Y:
                Y.append('chi')
            if plt in VLat_keys and 'lat' not in Y:
                Y.append('lat')
            if plt in VLon_keys and 'lon' not in Y:
                Y.append('lon')
            if plt in Vadm_keys and 'vadm' not in Y:
                Y.append('vadm')
            if plt in Vdm_keys and 'vdm' not in Y:
                Y.append('vdm')
        if file_type == 'pmag_results':
            print('available objects for plotting: ', PltObjs)
        print('available X plots: ', X)
        print('available Y plots: ', Y)
        print('available method codes: ', methcodes)
        f = open(dir_path+'/.striprc', 'w')
        for x in X:
            f.write('x:'+x+'\n')
        for y in Y:
            f.write('y:'+y+'\n')
        for m in methcodes:
            f.write('m:'+m+'\n')
        for obj in PltObjs:
            f.write('obj:'+obj+'\n')
        sys.exit()
    if plotexp == 1:
        for lkey in Lat_keys:
            for key in list(Results[0].keys()):
                if key == lkey:
                    lat = float(Results[0][lkey])
                    Xinc = [pmag.pinc(lat), -pmag.pinc(lat)]
                    break
        if Xinc == "":
            print('can not plot expected inc for site - lat unknown')
    if method != "" and method not in methcodes:
        print('your method not available, but these are:  ')
        print(methcodes)
        print('use ', methcodes[0], '? ^D to quit')
    if xaxis == 'age':
        for akey in Age_keys:
            for key in list(Results[0].keys()):
                if key == akey:
                    Xplots.append(key)
                    Xunits.append(Unit_keys[key])
    if xaxis == 'pos':
        for dkey in Depth_keys:
            for key in list(Results[0].keys()):
                if key == dkey:
                    Xplots.append(key)
    if len(Xplots) == 0:
        print('desired X axis  information not found')
        sys.exit()
    if xaxis == 'age':
        age_unit = Results[0][Xunits[0]]
    if len(Xplots) > 1:
        print('multiple X axis  keys found, using: ', Xplots[xplotind])
    for ykey in ykeys:
        for key in list(Results[0].keys()):
            if key == ykey:
                Yplots.append(key)
    if len(Yplots) == 0:
        print('desired Y axis  information not found')
        sys.exit()
    if len(Yplots) > 1:
        print('multiple Y axis  keys found, using: ', Yplots[yplotind])

    # check if age or depth info
    if len(Xplots) == 0:
        print("Must have either age or height info to plot ")
        sys.exit()
    #
    # check for variable to plot
    #
    #
    # determine X axis (age or depth)
    #
    if xaxis == "age":
        plotind = "1"
    if method == "":
        try:
            method = methcodes[0]
        except IndexError:
            method = ""
    if xaxis == 'pos':
        xlab = "Stratigraphic Height (meters)"
    else:
        xlab = "Age ("+age_unit+")"
    Xkey = Xplots[xplotind]
    Ykey = Yplots[yplotind]
    ylab = Ykey
    #
    # collect the data for plotting
    XY = []
    isign = 1.
#    if float(Results[0][Xkey])/float(Results[-1][Xkey])>0 and float(Results[0][Xkey])<0:
#        isign=-1. # x axis all same sign and negative, take positive (e.g.,for depth in core)
#        xlab="Stratigraphic Position (meters)"
#    else:
#        isign=1.
    for rec in Results:
        if "magic_method_codes" in list(rec.keys()):
            meths = rec["magic_method_codes"].split(":")
            if method in meths:  # make sure it is desired lab treatment step
                if obj == 'all' and rec[Xkey].strip() != "":
                    XY.append([isign*float(rec[Xkey]), float(rec[Ykey])])
                elif rec[Xkey].strip() != "":
                    name = rec['pmag_result_name'].split()
                    if obj == 'sit' and "Site" in name:
                        XY.append([isign*float(rec[Xkey]), float(rec[Ykey])])
                    if obj == 'sam' and "Sample" in name:
                        XY.append([isign*float(rec[Xkey]), float(rec[Ykey])])
        elif method == "":
            if obj == 'all' and rec[Xkey].strip() != "":
                XY.append([isign*float(rec[Xkey]), float(rec[Ykey])])
            elif rec[Xkey].strip() != "":
                name = rec['pmag_result_name'].split()
                if obj == 'sit' and "Site" in name:
                    XY.append([isign*float(rec[Xkey]), float(rec[Ykey])])
                if obj == 'sam' and "Sample" in name:
                    XY.append([isign*float(rec[Xkey]), float(rec[Ykey])])
        else:
            print("Something wrong with your plotting choices")
            break
    XY.sort()
    title = ""
    if "er_locations_names" in list(Results[0].keys()):
        title = Results[0]["er_location_names"]
    if "er_locations_name" in list(Results[0].keys()):
        title = Results[0]["er_location_name"]
    labels = [xlab, ylab, title]
    pmagplotlib.plot_init(FIG['strat'], 10, 5)
    pmagplotlib.plot_strat(FIG['strat'], XY, labels)  # plot them
    if plotexp == 1:
        pmagplotlib.plot_hs(FIG['strat'], Xinc, 'b', '--')
    if yaxis == 'inc' or yaxis == 'lat':
        pmagplotlib.plot_hs(FIG['strat'], [0], 'b', '-')
        pmagplotlib.plot_hs(FIG['strat'], [-90, 90], 'g', '-')
    if pTS == 1:
        FIG['ts'] = 2
        pmagplotlib.plot_init(FIG['ts'], 10, 5)
        pmagplotlib.plot_ts(FIG['ts'], [amin, amax], ts)
    files = {}
    for key in list(FIG.keys()):
        files[key] = key+'.'+fmt
    if pmagplotlib.isServer:
        black = '#000000'
        purple = '#800080'
        files = {}
        files['strat'] = xaxis+'_'+yaxis+'_.'+fmt
        files['ts'] = 'ts.'+fmt
        titles = {}
        titles['strat'] = 'Depth/Time Series Plot'
        titles['ts'] = 'Time Series Plot'
        FIG = pmagplotlib.add_borders(FIG, titles, black, purple)
        pmagplotlib.save_plots(FIG, files)
    elif plot == 1:
        pmagplotlib.save_plots(FIG, files)
    else:
        pmagplotlib.draw_figs(FIG)
        ans = input(" S[a]ve to save plot, [q]uit without saving:  ")
        if ans == "a":
            pmagplotlib.save_plots(FIG, files)


if __name__ == "__main__":
    main()
