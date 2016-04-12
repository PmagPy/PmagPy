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
        irmaq_magic.py

    DESCRIPTION
       plots IRM acquisition curves from magic_measurements file

    SYNTAX 
        irmaq_magic [command line options]
    
    INPUT 
       takes magic formatted magic_measurements.txt files
    
    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file, default is: magic_measurements.txt
        -obj OBJ: specify  object  [loc, sit, sam, spc] for plot, default is by location
        -N ; do not normalize by last point - use original units
        -fmt [png,jpg,eps,pdf] set plot file format [default is svg]
        -sav save plot[s] and quit
    NOTE
        loc: location (study); sit: site; sam: sample; spc: specimen
    """
    FIG={} # plot dictionary
    FIG['exp']=1 # exp is figure 1
    dir_path='./'
    plot,fmt=0,'svg'
    units,dmag_key='T','treatment_dc_field'
    XLP=[]
    norm=1
    in_file,plot_key,LP='magic_measurements.txt','er_location_name',"LP-IRM"
    if len(sys.argv)>1:
        if '-h' in sys.argv:
            print main.__doc__
            sys.exit()
        if '-N' in sys.argv:norm=0
        if '-sav' in sys.argv:plot=1
        if '-fmt' in sys.argv:
            ind=sys.argv.index("-fmt")
            fmt=sys.argv[ind+1]
        if '-f' in sys.argv:
            ind=sys.argv.index("-f")
            in_file=sys.argv[ind+1]
        if '-WD' in sys.argv:
            ind=sys.argv.index('-WD')
            dir_path=sys.argv[ind+1]
            in_file=dir_path+'/'+in_file
        if '-obj' in sys.argv:
            ind=sys.argv.index('-obj')
            plot_by=sys.argv[ind+1]
            if plot_by=='sit':plot_key='er_site_name'
            if plot_by=='sam':plot_key='er_sample_name'
            if plot_by=='spc':plot_key='er_specimen_name'
    data,file_type=pmag.magic_read(in_file)
    sids=pmag.get_specs(data)
    pmagplotlib.plot_init(FIG['exp'],6,6)
    #
    #
    # find desired intensity data
    #
    # get plotlist
    #
    plotlist,intlist=[],['measurement_magnitude','measurement_magn_moment','measurement_magn_volume','measurement_magn_mass']
    IntMeths=[]
    data=pmag.get_dictitem(data,'magic_method_codes',LP,'has') # get all the records with this lab protocol
    Ints={}
    NoInts,int_key=1,""
    for key in intlist:
       Ints[key]=pmag.get_dictitem(data,key,'','F') # get all non-blank data for intensity type
       if len(Ints[key])>0:
           NoInts=0 
           if int_key=="":int_key=key
    if NoInts==1:
        print 'No intensity information found'
        sys.exit()
    for  rec in Ints[int_key]:
        if rec[plot_key] not in plotlist: plotlist.append(rec[plot_key])
    plotlist.sort()
    for plt in plotlist:
        print plt
        INTblock=[]
        data=pmag.get_dictitem(Ints[int_key],plot_key,plt,'T') # get data with right intensity info whose plot_key matches plot
        sids=pmag.get_specs(data) # get a list of specimens with appropriate data
        if len(sids)>0: 
            title=data[0][plot_key]
        for s in sids:
            INTblock=[]
            sdata=pmag.get_dictitem(data,'er_specimen_name',s,'T') # get data for each specimen
            for rec in sdata:
                INTblock.append([float(rec[dmag_key]),0,0,float(rec[int_key]),1,'g'])
            pmagplotlib.plotMT(FIG['exp'],INTblock,title,0,units,norm)
        files={}
        for key in FIG.keys():
            files[key]=title+'_'+LP+'.'+fmt 
        if plot==0:
            pmagplotlib.drawFIGS(FIG)
            ans=raw_input(" S[a]ve to save plot, [q]uit,  Return to continue:  ")
            if ans=='q':sys.exit()
            if ans=="a": 
                pmagplotlib.saveP(FIG,files) 
        else:
            pmagplotlib.saveP(FIG,files) 
        pmagplotlib.clearFIG(FIG['exp'])

if __name__ == "__main__":
    main()
