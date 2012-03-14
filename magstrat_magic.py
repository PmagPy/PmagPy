#!/usr/bin/env python
import pmagplotlib,pmag,sys,exceptions
def main():
    """
    NAME 
        magstrat_magic.py

    DESCRIPTION
        plots various parameters versus depth or age with optional time scale

    SYNTAX
        magstrat_magic.py [-h] [-i] [command line optins]

    OPTIONS
        -h prints help message and quits
        -i allows interactive entry of options
        -f FILE: specify input magic  format file from magic,default='pmag_results.txt'
         supported types=[pmag_specimens, pmag_samples, pmag_sites, pmag_results]
        -X [age,pos]:  specify whether age or stratigraphic position
        -Y [dec,inc,int,lat,lon,vdm,vadm]
           (lat and lon are VGP lat and lon)
        -Iex: plot the expected inc at average_lat - only available for pmag_results
        -ts TS: plot the GPTS for the time interval shown (only for age option)
           TS: [ck95, gts04] 
        -mcd method_code, specify method code, default is first one encountered
    NOTES
        when X and/or Y are not specified, a list of possibilities will be presented to the user for choosing

    """
    res_file='pmag_results.txt'
    xaxis,xplotind,yplotind="",0,"" # (0 for strat pos)
    yaxis=""  
    supported=['pmag_specimens', 'pmag_samples', 'pmag_sites', 'pmag_results','magic_web']
    method,fignum="",1
    plotexp,pTS=0,0
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        res_file=sys.argv[ind+1]
    if '-X' in sys.argv:
        ind=sys.argv.index('-X')
        xaxis=sys.argv[ind+1]
    if '-Y' in sys.argv:
        ind=sys.argv.index('-Y')
        yaxis=sys.argv[ind+1]
    if '-mcd' in sys.argv:
        ind=sys.argv.index('-mcd')
        method=sys.argv[ind+1]
    if '-ts' in sys.argv:
        ind=sys.argv.index('-ts')
        ts=sys.argv[ind+1]
        pTS=1
        if xaxis=='pos':
            print "Time scale option for age only, time scale will not be plotted"
            pTS=0
    if '-Iex' in sys.argv: plotexp=1
    if '-i' in sys.argv:
        yaxis,xaxis=="",""
    #
    # get name of file from command line
    #
        res_file=raw_input("Input pmag_results  file name? [pmag_results.txt]   ")
        if res_file=="":res_file="pmag_results.txt"
    #
    #
    # get data read in
    Results,file_type=pmag.magic_read(res_file) 
    if file_type not in supported:
        print "Unsupported file type, try again"
        sys.exit()
    methcodes=[]
    if "magic_method_codes" in Results[0].keys(): # need to know all the measurement types from method_codes
        for rec in Results:
            meths=rec["magic_method_codes"]
            if meths not in methcodes: methcodes.append(meths.strip()) # look for the lab treatments
    #
    # initialize some variables
    age_unit="" # Unit for age or depth plotting (meters if depth)
    Xplots,Yplots,Xplotind,Yplotind=[],[],0,""
    #
    # step through possible file formats
    #
    if file_type=="pmag_results":
        if "average_age" in Results[0].keys():
            Xplots.append("average_age")
            age_unit=Results[0]["average_age_unit"]
        if "average_height" in Results[0].keys(): Xplots.append("average_height")
        if plotexp==1:
             if "average_lat" in Results[0].keys():
                 lat=float(Results[0]['average_lat'])
                 Xinc=[pmag.pinc(lat),-pmag.pinc(lat)]
             else:
                 print 'can not plot expected inc for site - lat unknown'
        if xaxis=="pos":
            xplotind=Xplots.index("average_height")
        else: 
            xplotind=Xplots.index("average_age")
        if "average_dec" in Results[0].keys():Yplots.append("average_dec")
        if "average_inc" in Results[0].keys():Yplots.append("average_inc")
        if "average_int" in Results[0].keys():Yplots.append("average_int")
        if "average_int_rel" in Results[0].keys():Yplots.append("average_int_rel")
        if "vgp_lat" in Results[0].keys():Yplots.append("vgp_lat")
        if "vgp_lon" in Results[0].keys():Yplots.append("vgp_lon")
        if "vdm" in Results[0].keys():Yplots.append("vdm")
        if "vadm" in Results[0].keys():Yplots.append("vadm")
        if yaxis=="dec" and "average_dec" in Yplots:yplotind=Yplots.index("average_dec")
        if yaxis=="inc" and "average_inc" in Yplots:yplotind=Yplots.index("average_inc")
        if yaxis=="int" and "average_int_rel" in Yplots:yplotind=Yplots.index("average_int_rel")
        if yaxis=="int" and "average_int" in Yplots:yplotind=Yplots.index("average_int")
        if yaxis=="lat" and "vgp_lat" in Yplots:yplotind=Yplots.index("vgp_lat")
        if yaxis=="lon" and "vgp_lon" in Yplots:yplotind=Yplots.index("vgp_lon")
        if yaxis=="vdm" and "vdm" in Yplots:yplotind=Yplots.index("vdm")
        if yaxis=="vadm" and "vadm" in Yplots:yplotind=Yplots.index("vadm")
        if yplotind=="":
            print 'your choice not available, but these are: '
            print Yplots
            sys.exit()
    else:
        xplotind,plotexp=0,0
        if xaxis=="pos":
            print "Only age available for these types of files - try pmag_results "
            sys.exit()
    if file_type=="pmag_sites":
        if "site_inferred_age" in Results[0].keys():
            Xplots.append("site_inferred_age")
            age_unit=Results[0]["site_inferred_age_unit"]
        if "site_dec" in Results[0].keys():Yplots.append("site_dec")
        if "site_inc" in Results[0].keys():Yplots.append("site_inc")
        if "site_int" in Results[0].keys():Yplots.append("site_int")
        if "site_int_rel" in Results[0].keys():Yplots.append("site_int_rel")
        if yaxis=="dec" and "site_dec" in Yplots:yplotind=Yplots.index("site_dec")
        if yaxis=="inc" and "site_inc" in Yplots:yplotind=Yplots.index("site_inc")
        if yaxis=="int" and "site_int_rel" in Yplots:yplotind=Yplots.index("site_int_rel")
        if yaxis=="int" and "site_int" in Yplots:yplotind=Yplots.index("site_int")
    if file_type=="pmag_samples":
        if "sample_inferred_age" in Results[0].keys():
            Xplots.append("sample_inferred_age")
            age_unit=Results[0]["sample_inferred_age_unit"]
        if "sample_dec" in Results[0].keys():Yplots.append("sample_dec")
        if "sample_inc" in Results[0].keys():Yplots.append("sample_inc")
        if "sample_int" in Results[0].keys():Yplots.append("sample_int")
        if "sample_int_rel" in Results[0].keys():Yplots.append("sample_int_rel")
        if yaxis=="dec" and "sample_dec" in Yplots:yplotind=Yplots.index("sample_dec")
        if yaxis=="inc" and "sample_inc" in Yplots:yplotind=Yplots.index("sample_inc")
        if yaxis=="int" and "sample_int_rel" in Yplots:yplotind=Yplots.index("sample_int_rel")
        if yaxis=="int" and "sample_int" in Yplots:yplotind=Yplots.index("sample_int")
    if file_type=="pmag_specimens":
        if "specimen_inferred_age" in Results[0].keys():
            Xplots.append("specimen_inferred_age")
            age_unit=Results[0]["specimen_inferred_age_unit"]
        if "specimen_dec" in Results[0].keys():Yplots.append("specimen_dec")
        if "specimen_inc" in Results[0].keys():Yplots.append("specimen_inc")
        if "specimen_int" in Results[0].keys():Yplots.append("specimen_int")
        if "specimen_int_rel" in Results[0].keys():Yplots.append("specimen_int_rel")
        if yaxis=="dec" and "specimen_dec" in Yplots:yplotind=Yplots.index("specimen_dec")
        if yaxis=="inc" and "specimen_inc" in Yplots:yplotind=Yplots.index("specimen_inc")
        if yaxis=="int" and "specimen_int_rel" in Yplots:yplotind=Yplots.index("specimen_int_rel")
        if yaxis=="int" and "specimen_int" in Yplots:yplotind=Yplots.index("specimen_int")
    if yplotind=="":
        print 'your choice not available, but these are: '
        print Yplots
        sys.exit()
    #
    # check if age or depth info        
    if len(Xplots)==0:
        print "Must have either age or height info to plot "
        sys.exit()
    #
    # check for variable to plot
    #
    if len(Yplots)==0:
        print "Must have something to plot! "
        sys.exit()
    #
    # determine X axis (age or depth)
    #
    if '-i' in sys.argv:
        if len(Xplots)==2:
            print "0: ",Xplots[0],"1: ",Xplots[1]
            plotind=raw_input("Which type of plot [0]/1 " )
            xplotind=int(plotind)
            if xplotind==1:xaxis='age'
    # inquire about which lab treatment step desired
        method=methcodes[0]
        if len(methcodes)>1:
            print " There are several different  experiments. " 
            print " Select type you want to plot. "
            for k in range(len(methcodes)):
                print methcodes[k], " [",k,"] "
            ans=int(raw_input())
            method=methcodes[ans]
    # now get Y axis (whatever)
        if len(Yplots)>1:
            for yplotind in range(len(Yplots)):
                print yplotind, Yplots[yplotind]
    #        if len(methcodes)>1: print "Be careful to select the one that goes with your lab treatment! "
            yplotind=raw_input("Which type of plot [0] " )
            if yplotind=="":yplotind=0
            yplotind=int(yplotind)
    else:
        if xaxis=="age": plotind="1"
        if method=="":method=methcodes[0]
    if xaxis=='pos':
        xlab="Stratigraphic Height (meters)" 
    else:
        xlab="Age ("+age_unit+")"
    Xkey=Xplots[xplotind]
    Ykey=Yplots[yplotind]
    ylab=Ykey
         
    #
    # collect the data for plotting
    X,Y=[],[]
    if float(Results[0][Xkey])/float(Results[-1][Xkey])>0 and float(Results[0][Xkey])<0: 
        isign=-1. # x axis all same signa and negative, take positive (e.g.,for depth in core)
        xlab="Stratigraphic Depth (meters)" 
    else:
        isign=1.
    for rec in Results:
        if "magic_method_codes" in rec.keys():
            meths=rec["magic_method_codes"]
            if method == meths: # make sure it is desired lab treatment step
                X.append(isign*float(rec[Xkey]))
                Y.append(float(rec[Ykey]))
        elif method =="":
            X.append(isign*float(rec[Xkey]))
            Y.append(float(rec[Ykey]))
        else:  
            print "Something wrong with your plotting choices"
            break
    data=[X,Y]   # pack them up for shipping
    title=""
    if "er_locations_names" in Results[0].keys(): title=Results[0]["er_location_names"]
    if "er_locations_name" in Results[0].keys(): title=Results[0]["er_location_name"]
    labels=[xlab,ylab,title]
    pmagplotlib.plotSTRAT(fignum,data,labels) # plot them
    if plotexp==1: pmagplotlib.plotHs(fignum,Xinc,'b','--')
    if yaxis=='inc' or yaxis=='lat':
        pmagplotlib.plotHs(fignum,[0],'b','-')
        pmagplotlib.plotHs(fignum,[-90,90],'g','-')
    if pTS==1: pmagplotlib.plotTS(fignum+1,[X[0],X[-1]],ts)
    raw_input()
main()
