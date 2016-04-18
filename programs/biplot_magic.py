#!/usr/bin/env python
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")
import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib


def main():
    """
    NAME
        biplot_magic.py

    DESCRIPTION
        makes a biplot of specified variables from magic_measurements.txt format file
  
    SYNTAX
        biplot_magic.py [-h] [-i] [command line options]

    INPUT 
        takes magic formated magic_measurments file

    OPTIONS
        -h prints help message and quits
        -i interactively set filename and axes for plotting
        -f FILE: specifies file name, default: magic_measurements.txt
        -fmt [svg,png,jpg], format for images - default is svg
        -sav figure and quit
        -x XMETH:key:step, specify method code for X axis (optional key and treatment values)
        -y YMETH:key:step, specify method code for X axis
        -obj OBJ: specify object [loc, sit, sam, spc] for plot, default is whole file
        -n [V,M] plot volume or mass normalized data only
    NOTES
        if nothing is specified for x and y, the user will be presented with options
        key = ['treatment_ac_field','treatment_dc_field',treatment_temp'] 
        step in mT for fields, K for temperatures
           """ 
    #
    file='magic_measurements.txt'
    methx,methy,fmt="","",'.svg'
    plot_key=''
    norm_by=""
    #plot=0
    no_plot = pmag.get_flag_arg_from_sys('-sav')
    if not no_plot:
        do_plot = True
    else:
        do_plot = False
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt='.'+sys.argv[ind+1]
    if '-n' in sys.argv:
        ind=sys.argv.index('-n')
        norm_by=sys.argv[ind+1]
    xtreat_key,ytreat_key,xstep,ystep="","","",""
    if '-x' in sys.argv:
        ind=sys.argv.index('-x')
        meths=sys.argv[ind+1].split(':')
        methx=meths[0]
        if len(meths)>1:
            xtreat_key=meths[1]
            xstep=float(meths[2])
    if '-y' in sys.argv:
        ind=sys.argv.index('-y')
        meths=sys.argv[ind+1].split(':')
        methy=meths[0]
        if len(meths)>1:
            ytreat_key=meths[1]
            ystep=float(meths[2])
    if '-obj' in sys.argv: 
        ind=sys.argv.index('-obj')
        plot_by=sys.argv[ind+1]
        if plot_by=='loc':plot_key='er_location_name'
        if plot_by=='sit':plot_key='er_site_name'
        if plot_by=='sam':plot_key='er_sample_name'
        if plot_by=='spc':plot_key='er_specimen_name'
    if '-h' in sys.argv:
        do_plot = False
    if '-i' in sys.argv: 
    #
    # get name of file from command line
    #
        file=raw_input("Input magic_measurments file name? [magic_measurements.txt] ")
        if file=="":file="magic_measurements.txt"
    #
    #
    FIG={'fig':1}
    pmagplotlib.plot_init(FIG['fig'],5,5)
    data,file_type=pmag.magic_read(file)
    if file_type!="magic_measurements":
        print file_type,' not correct format for magic_measurments file'
        sys.exit()
    #
    # collect method codes
    methods,plotlist=[],[]
    for rec in  data:
        if plot_key!="":
            if rec[plot_key] not in plotlist:plotlist.append(rec[plot_key])
        elif len(plotlist)==0:
            plotlist.append('All')
        meths=rec['magic_method_codes'].split(':')
        for meth in meths:
            if meth.strip() not in methods and meth.strip()!="LP-":
                methods.append(meth.strip())
    #
    if '-i' in sys.argv:
        print methods
    elif methx =="" or methy=="": 
	print methods
        sys.exit()
    GoOn=1
    while GoOn==1:
        if '-i' in sys.argv:methx=raw_input('Select method for x axis: ')
        if methx not in methods:
            if '-i' in sys.argv:
                print 'try again! method not available'
            else: 
                print main.__doc__
                print '\n must specify X axis method\n'
                sys.exit()
        else:
            if pmagplotlib.verbose: print methx, ' selected for X axis'
            GoOn=0
    GoOn=1
    while GoOn==1:
        if '-i' in sys.argv:methy=raw_input('Select method for y axis: ')
        if methy not in methods:
            if '-i' in sys.argv:
                print 'try again! method not available'
            else: 
                print main.__doc__
                print '\n must specify Y axis method\n'
                sys.exit()
        else:
            if pmagplotlib.verbose: print methy, ' selected for Y axis'
            GoOn=0
    if norm_by=="":
        measkeys=['measurement_magn_mass','measurement_magn_volume','measurement_magn_moment','measurement_magnitude','measurement_chi_volume','measurement_chi_mass','measurement_chi']
    elif norm_by=="V":
        measkeys=['measurement_magn_volume','measurement_chi_volume']
    elif norm_by=="M":
        measkeys=['measurement_magn_mass','measurement_chi_mass']
    xmeaskey,ymeaskey="",""
    plotlist.sort()
    for plot in plotlist: # go through objects
        if pmagplotlib.verbose:
            print plot
        X,Y=[],[]
        x,y='',''
        for rec in data:
            if plot_key!="" and rec[plot_key]!=plot:
                pass
            else:
                meths=rec['magic_method_codes'].split(':')
                for meth in meths:
                    if meth.strip()==methx:
                        if xmeaskey=="":
                            for key in measkeys:
                                if key in rec.keys() and rec[key]!="":
                                    xmeaskey=key
                                    if pmagplotlib.verbose:
                                        print xmeaskey,' being used for plotting X.'
                                    break 
                    if meth.strip()==methy:
                        if ymeaskey=="":
                            for key in measkeys:
                                if key in rec.keys() and rec[key]!="":
                                    ymeaskey=key
                                    if pmagplotlib.verbose:
                                        print ymeaskey,' being used for plotting Y'
                                    break 
        if ymeaskey!="" and xmeaskey!="":
            for rec in data:
                x,y='',''
                spec=rec['er_specimen_name'] # get the ydata for this specimen
                if rec[ymeaskey]!="" and methy in rec['magic_method_codes'].split(':'): 
                    if ytreat_key=="" or (ytreat_key in rec.keys() and float(rec[ytreat_key])==ystep):
                        y=float(rec[ymeaskey])
                        for rec in data: # now find the xdata 
                            if rec['er_specimen_name']==spec and rec[xmeaskey]!="" and methx in rec['magic_method_codes'].split(':'): 
                                if xtreat_key=="" or (xtreat_key in rec.keys() and float(rec[xtreat_key])==xstep):
                                    x=float(rec[xmeaskey])
                if x != '' and y!= '':
                    X.append(x)
                    Y.append(y)
        if len(X)>0:
            pmagplotlib.clearFIG(FIG['fig'])
            pmagplotlib.plotXY(FIG['fig'],X,Y,sym='ro',xlab=methx,ylab=methy,title=plot+':Biplot')
            if not pmagplotlib.isServer and do_plot:
                pmagplotlib.drawFIGS(FIG)
                ans=raw_input('S[a]ve plots, [q]uit,  Return for next plot ' )
                if ans=='a':
                    files={}
                    for key in FIG.keys(): files[key]=plot+'_'+key+fmt
                    pmagplotlib.saveP(FIG,files)
                if ans=='q':
                    print "Good-bye\n"
                    sys.exit()
            else:
                files={}
                for key in FIG.keys(): files[key]=plot+'_'+key+fmt
                if pmagplotlib.isServer:
                    black     = '#000000'
                    purple    = '#800080'
                    titles={}
                    titles['fig']='X Y Plot'
                    FIG = pmagplotlib.addBorders(FIG,titles,black,purple)
                pmagplotlib.saveP(FIG,files)
        else:
            print 'nothing to plot for ',plot

if __name__ == "__main__":
    main()
