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
        lowrie_magic.py

    DESCRIPTION
       plots intensity decay curves for Lowrie experiments

    SYNTAX 
        lowrie_magic.py -h [command line options]
    
    INPUT 
       takes magic_measurements formatted input files
    
    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file, default is magic_measurements.txt
        -N do not normalize by maximum magnetization
        -fmt [svg, pdf, eps, png] specify fmt, default is svg
        -sav saves plots and quits
    """
    fmt,plot='svg',0
    FIG={} # plot dictionary
    FIG['lowrie']=1 # demag is figure 1
    pmagplotlib.plot_init(FIG['lowrie'],6,6)
    norm=1 # default is to normalize by maximum axis
    in_file,dir_path='magic_measurements.txt','.'
    if len(sys.argv)>1:
        if '-WD' in sys.argv:
            ind=sys.argv.index('-WD')
            dir_path=sys.argv[ind+1]
        if '-h' in sys.argv:
            print main.__doc__
            sys.exit()
        if '-N' in sys.argv: norm=0 # don't normalize
        if '-sav' in sys.argv: plot=1 # don't normalize
        if '-fmt' in sys.argv: # sets input filename
            ind=sys.argv.index("-fmt")
            fmt=sys.argv[ind+1]
        if '-f' in sys.argv: # sets input filename
            ind=sys.argv.index("-f")
            in_file=sys.argv[ind+1]
    else:
        print main.__doc__
        print 'you must supply a file name'
        sys.exit() 
    in_file=dir_path+'/'+in_file
    print in_file
    PmagRecs,file_type=pmag.magic_read(in_file)
    if file_type!="magic_measurements":
         print 'bad input file'
         sys.exit()
    PmagRecs=pmag.get_dictitem(PmagRecs,'magic_method_codes','LP-IRM-3D','has') # get all 3D IRM records
    if len(PmagRecs)==0:
        print 'no records found'
        sys.exit()
    specs=pmag.get_dictkey(PmagRecs,'er_specimen_name','')
    sids=[]
    for spec in specs:
        if spec not in sids:sids.append(spec) # get list of unique specimen names
    for spc in sids:  # step through the specimen names
        print spc
        specdata=pmag.get_dictitem(PmagRecs,'er_specimen_name',spc,'T') # get all this one's data
        DIMs,Temps=[],[]
        for dat in specdata: # step through the data
            DIMs.append([float(dat['measurement_dec']),float(dat['measurement_inc']),float(dat['measurement_magn_moment'])])
            Temps.append(float(dat['treatment_temp'])-273.)
        carts=pmag.dir2cart(DIMs).transpose()
        if norm==1: # want to normalize
            nrm=(DIMs[0][2]) # normalize by NRM
            ylab="M/M_o"
        else: 
            nrm=1. # don't normalize
            ylab="Magnetic moment (Am^2)"
        xlab="Temperature (C)"
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[0])/nrm,sym='r-')
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[0])/nrm,sym='ro') # X direction
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[1])/nrm,sym='c-')
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[1])/nrm,sym='cs') # Y direction
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[2])/nrm,sym='k-')
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[2])/nrm,sym='k^',title=spc,xlab=xlab,ylab=ylab) # Z direction
        files={'lowrie':'lowrie:_'+spc+'_.'+fmt}
        if plot==0:
            pmagplotlib.drawFIGS(FIG)
            ans=raw_input('S[a]ve figure? [q]uit, <return> to continue   ')
            if ans=='a':
                pmagplotlib.saveP(FIG,files)
            elif ans=='q':
                sys.exit()
        else:
            pmagplotlib.saveP(FIG,files)
        pmagplotlib.clearFIG(FIG['lowrie'])

if __name__ == "__main__":
    main()
