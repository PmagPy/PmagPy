#!/usr/bin/env python
import sys,pmag,pmagplotlib
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
    NOTE
        loc: location (study); sit: site; sam: sample; spc: specimen
    """
    FIG={} # plot dictionary
    FIG['exp']=1 # exp is figure 1
    in_file,plot_key,LP='magic_measurements.txt','er_location_name',"LP-IRM"
    units,dmag_key='T','treatment_dc_field'
    XLP=[]
    norm=1
    if len(sys.argv)>1:
        if '-h' in sys.argv:
            print main.__doc__
            sys.exit()
        if '-N' in sys.argv:norm=0
        if '-f' in sys.argv:
            ind=sys.argv.index("-f")
            in_file=sys.argv[ind+1]
        if '-obj' in sys.argv:
            ind=sys.argv.index('-obj')
            plot_by=sys.argv[ind+1]
            if plot_by=='sit':plot_key='er_site_name'
            if plot_by=='sam':plot_key='er_sample_name'
            if plot_by=='spc':plot_key='er_specimen_name'
#        if '-LP' in sys.argv:
#            ind=sys.argv.index("-LT")
#            LP='LP-'+sys.argv[ind+1] # get lab protocol for plotting
    data,file_type=pmag.magic_read(in_file)
    sids=pmag.get_specs(data)
    pmagplotlib.plot_init(FIG['exp'],6,6)
    print len(data),' records read from ',in_file
    #
    #
    # find desired intensity data
    #
    # get plotlist
    #
    plotlist,intlist=[],['measurement_magnitude','measurement_magn_moment','measurement_magn_volume','measurement_magn_mass']
    IntMeths=[]
    for  rec in data:
        meths=[]
        methcodes=rec['magic_method_codes'].split(':')
        for meth in methcodes:meths.append(meth.strip())
        for key in rec.keys():
            if key in intlist and rec[key]!="":
                if key not in IntMeths:IntMeths.append(key)
                if rec[plot_key] not in plotlist and LP in meths: plotlist.append(rec[plot_key])
        plotlist.sort()
    if len(IntMeths)==0:
        print 'No intensity information found'
        sys.exit()
    int_key=IntMeths[0] # plot first intensity method found - normalized to initial value anyway - doesn't matter which used
    for plot in plotlist:
        print plot
        for spec in sids:
            INTblock=[]
            for rec in data:
                if 'measurement_flag' not in rec.keys():rec['measurement_flag']='g'
                if rec[plot_key]==plot and int_key in rec.keys() and rec[int_key]!="" and rec['er_specimen_name']==spec:
                    meths=[]
                    methcodes=rec['magic_method_codes'].split(':')
                    for meth in methcodes:
                        LPtest=meth.split('-')
                        if XLP not in LPtest: meths.append(meth.strip())
                    if len(meths)>0 and LP in meths or 'LT-NO' in meths: 
                        title=rec[plot_key]
                        INTblock.append([float(rec[dmag_key]),0,0,float(rec[int_key]),1,rec['measurement_flag']])
            Sdata=INTblock.sort()
            if len(INTblock)>2: pmagplotlib.plotMT(FIG['exp'],INTblock,title,0,units,norm)
        ans=raw_input(" S[a]ve to save plot, [q]uit,  Return to continue:  ")
        if ans=='q':sys.exit()
        if ans=="a": 
            files={}
            for key in FIG.keys():
                files[key]=title+'_'+LP+'.svg' 
            pmagplotlib.saveP(FIG,files) 
        pmagplotlib.clearFIG(FIG['exp'])
main() 
