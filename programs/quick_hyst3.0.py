#!/usr/bin/env python
import sys
import os
import numpy
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import new_builder as nb

def main():
    """
    NAME
        quick_hyst.py

    DESCRIPTION
        makes plots of hysteresis data

    SYNTAX
        quick_hyst.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f: specify input file, default is magic_measurements.txt
        -spc SPEC: specify specimen name to plot and quit
        -sav save all plots and quit
        -fmt [png,svg,eps,jpg]
    """
    args = sys.argv
    if "-h" in args:
        print main.__doc__
        sys.exit()
    plots = 0
    pltspec = ""
    verbose=pmagplotlib.verbose
    version_num=pmag.get_version()
    dir_path = pmag.get_named_arg_from_sys('-WD', '.')
    dir_path = os.path.realpath(dir_path)
    meas_file = pmag.get_named_arg_from_sys('-f', 'measurements.txt')
    fmt = pmag.get_named_arg_from_sys('-fmt', 'png')
    if '-sav' in args:
        verbose = 0
        plots = 1
    if '-spc' in args:
        ind = args.index("-spc")
        pltspec = args[ind+1]
        verbose = 0
        plots = 1
    print 'verbose?', verbose
    #
    #
    print pltspec, verbose, plots, meas_file, dir_path, fmt

    con = nb.Contribution(dir_path, read_tables=['measurements'],
                          custom_filenames={'measurements': meas_file})
    con.propagate_name_down('location_name', 'measurements')

    if 'measurements' not in con.tables:
        print main.__doc__
        print 'bad file'
        sys.exit()
    meas_container = con.tables['measurements']
    meas_df = meas_container.df

    #
    # initialize some variables
    # define figure numbers for hyst,deltaM,DdeltaM curves
    HystRecs, RemRecs = [], []
    HDD = {}
    HDD['hyst'] = 1
    pmagplotlib.plot_init(HDD['hyst'], 5, 5)
    #
    # get list of unique experiment names and specimen names
    #
    experiment_names, sids = [], []
    #hyst_data = pmag.get_dictitem(meas_data,'magic_method_codes','LP-HYS','has') # get all hysteresis data
    hyst_data = meas_container.get_records_for_code('LP-HYS')
    print len(hyst_data)
  

    #'specimen_name' should be synthetic name if synthetic_name
    
    experiment_names = hyst_data['experiment_name'].unique()
    print experiment_names
    sids = hyst_data['specimen_name'].unique()
    print '-'
    print sids
    print '-'
    hyst_data['treat_temp'].where(hyst_data['treat_temp'], '300', inplace=True)
    #print list(hyst_data['treat_temp'].ix[0:30].values)
    #
    k = 0
    if pltspec!="":
        k=sids.index(pltspec)
    intlist = ['magn_moment', 'magn_volume', 'magn_mass']
    
    while k < len(sids):
        locname, site, sample, synth = '', '', '', ''
        s = sids[k]
        hmeths = []
        if verbose:
            print s, k+1 , 'out of ',len(sids)
    #
    #
        B, M = [], [] #B,M for hysteresis, Bdcd,Mdcd for irm-dcd data
        spec = hyst_data[hyst_data['specimen_name'] == s]
        #spec = pmag.get_dictitem(hyst_data,'er_specimen_name',s,'T') # get all measurements for this specimen
        print 'specimen_name', s
        print len(spec)
        print '!!!'

        if 'location_name' in spec:
            locname = spec['location_name'][0]
        if 'site_name' in spec:
            site = spec['sample_name'][0]
        if 'sample_name' in spec:
            sample = spec['sample_name'][0]
        # ignore these names for now:
        #if 'er_location_name' in spec[0].keys():
        #    locname=spec[0]['er_location_name']
        #if 'er_site_name' in spec[0].keys():
        #    site=spec[0]['er_site_name']
        #if 'er_sample_name' in spec[0].keys():
        #    sample=spec[0]['er_sample_name']
        #if 'er_synthetic_name' in spec[0].keys():
        #    synth=spec[0]['er_synthetic_name']

        # get all records with non-blank values in any intlist column
        
        #for m in intlist:
        #    meas_data=pmag.get_dictitem(spec,m,'','F') # get all non-blank data for this specimen
        #    if len(meas_data)>0: break

        #meas_data = spec[spec[intlist].any(axis=1)]

        for int_column in intlist:
            if int_column in spec.columns:
                int_col = int_column
                break

        meas_data = spec[spec[int_column].notnull()]

        if len(meas_data) == 0:
            break

        c = ['k-', 'b-', 'c-', 'g-', 'm-', 'r-', 'y-']
        cnum = 0
        Temps = []
        xlab, ylab, title = '', '', ''
        Temps = meas_data['treat_temp'].unique()
        print "Temps"
        print Temps
        for t in Temps:
            print 'working on t: ',t
            t_data = meas_data[meas_data['treat_temp'] == t]
            print len(t_data)

            m = int_col
            ## !!!!!!! theoretically should be meas_field_dc
            B = t_data['meas_field_ac'].astype(float).values
            M = t_data[m].astype(float).values
            print m
            print B[:5]
            print M[:5]
  # now plot the hysteresis curve(s)
  #
            if len(B) > 0: 
                  B = numpy.array(B)
                  M = numpy.array(M)
                  if t == Temps[-1]:
                      xlab = 'Field (T)'
                      ylab = m
                      title = 'Hysteresis: ' + s
                  if t == Temps[0]:
                      pmagplotlib.clearFIG(HDD['hyst'])
                  pmagplotlib.plotXY(HDD['hyst'],B,M,sym=c[cnum],xlab=xlab,ylab=ylab,title=title) 
                  pmagplotlib.plotXY(HDD['hyst'],[1.1*B.min(),1.1*B.max()],[0,0],sym='k-',xlab=xlab,ylab=ylab,title=title) 
                  pmagplotlib.plotXY(HDD['hyst'],[0,0],[1.1*M.min(),1.1*M.max()],sym='k-',xlab=xlab,ylab=ylab,title=title) 
                  if verbose:pmagplotlib.drawFIGS(HDD)
                  cnum+=1
                  if cnum==len(c):cnum=0
  #
        files={}
        if plots:
            if pltspec!="":s=pltspec
            files={}
            for key in HDD.keys():
                if synth=='':
                    files[key]="LO:_"+locname+'_SI:_'+site+'_SA:_'+sample+'_SP:_'+s+'_TY:_'+key+'_.'+fmt
                else:
                    files[key]='SY:_'+synth+'_TY:_'+key+'_.'+fmt
            pmagplotlib.saveP(HDD,files)
            if pltspec != "":
                sys.exit()
        if verbose:
            pmagplotlib.drawFIGS(HDD)
            ans=raw_input("S[a]ve plots, [s]pecimen name, [q]uit, <return> to continue\n ")
            if ans=="a":
                files={}
                for key in HDD.keys():
                    files[key]="LO:_"+locname+'_SI:_'+site+'_SA:_'+sample+'_SP:_'+s+'_TY:_'+key+'_.'+fmt
                pmagplotlib.saveP(HDD,files)
            if ans=='':k+=1
            if ans=="p":
                del HystRecs[-1]
                k-=1
            if  ans=='q': 
                print "Good bye"
                sys.exit()
            if ans=='s':
                keepon=1
                specimen=raw_input('Enter desired specimen name (or first part there of): ')
                while keepon==1:
                    try:
                        k =sids.index(specimen)
                        keepon=0
                    except:
                        tmplist=[]
                        for qq in range(len(sids)):
                            if specimen in sids[qq]:tmplist.append(sids[qq])
                        print specimen," not found, but this was: "
                        print tmplist
                        specimen=raw_input('Select one or try again\n ')
                        k =sids.index(specimen)
        else:
            k+=1
        if len(B)==0:
            if verbose:print 'skipping this one - no hysteresis data'
            k+=1

if __name__ == "__main__":
    main()
