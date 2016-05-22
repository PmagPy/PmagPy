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
        dmag_magic.py

    DESCRIPTION
       plots intensity decay curves for demagnetization experiments

    SYNTAX
        dmag_magic -h [command line options]

    INPUT 
       takes magic formatted magic_measurements.txt files

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file, default is: magic_measurements.txt
        -obj OBJ: specify  object  [loc, sit, sam, spc] for plot, default is by location
        -LT [AF,T,M]: specify lab treatment type, default AF
        -XLP [PI]: exclude specific  lab protocols (for example, method codes like LP-PI)
        -N do not normalize by NRM magnetization
        -sav save plots silently and quit
        -fmt [svg,jpg,png,pdf] set figure format [default is svg]
    NOTE
        loc: location (study); sit: site; sam: sample; spc: specimen
    """
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    # initialize variables
    FIG = {} # plot dictionary
    FIG['demag'] = 1 # demag is figure 1
    in_file = pmag.get_named_arg_from_sys("-f", default_val="measurements.txt")
    plot_by = pmag.get_named_arg_from_sys("-obj", default_val="loc")
    name_dict = {'loc': 'location_name', 'sit': 'site_name',
                 'sam': 'samp_name', 'spc': 'specimen_name'}
    plot_key = name_dict[plot_by]
    LT = "LT-" + pmag.get_named_arg_from_sys("-LP", "AF") + "-Z"
    if LT == "LT-T-Z":
        units, dmag_key = 'K', 'treatment_temp'
    elif LT == "LT-AF-Z":
        units, dmag_key = 'T', 'treatment_ac_field'
    elif  LT == 'LT-M-Z':
        units, dmag_key = 'J', 'treatment_mw_energy'
    else:
        units = 'U'

    # returns True if -N present
    no_norm = pmag.get_flag_arg_from_sys("-N")
    norm = 0 if no_norm else 1

    no_plot = pmag.get_flag_arg_from_sys("-sav")
    plot = 1 if no_plot else 0

    fmt = pmag.get_named_arg_from_sys("-fmt", "svg")
    XLP = pmag.get_named_arg_from_sys("-XLP", "")

    print 'in_file', in_file
    print 'plot_key', plot_key
    print 'LT', LT
    print 'norm', norm
    print 'fmt', fmt
    print 'plot', plot
    print 'units, dmag_key', units, dmag_key
    print "XLP", XLP

    return
    
    data,file_type=pmag.magic_read(in_file)
    sids=pmag.get_specs(data)
    pmagplotlib.plot_init(FIG['demag'],5,5)
    print len(data),' records read from ',in_file
    #
    #
    # find desired intensity data
    #
    #
    plotlist,intlist=[],['measurement_magnitude','measurement_magn_moment','measurement_magn_volume','measurement_magn_mass']
    IntMeths=[]
    FixData=[]
    for  rec in data:
        meths=[]
        methcodes=rec['magic_method_codes'].split(':')
        for meth in methcodes:meths.append(meth.strip())
        for key in rec.keys():
            if key in intlist and rec[key]!="":
                if key not in IntMeths:IntMeths.append(key)
                if rec[plot_key] not in plotlist and LT in meths: plotlist.append(rec[plot_key])
                if 'measurement_flag' not in rec.keys():rec['measurement_flag']='g'
                FixData.append(rec)
        plotlist.sort()
    if len(IntMeths)==0:
        print 'No intensity information found'
        sys.exit()
    data=FixData
    int_key=IntMeths[0] # plot first intensity method found - normalized to initial value anyway - doesn't matter which used
    for plt in plotlist:
        if plot: print plt,'plotting by: ',plot_key
        PLTblock=pmag.get_dictitem(data,plot_key,plt,'T') # fish out all the data for this type of plot
        PLTblock=pmag.get_dictitem(PLTblock,'magic_method_codes',LT,'has') # fish out all the dmag for this experiment type
        PLTblock=pmag.get_dictitem(PLTblock,int_key,'','F') # get all with this intensity key non-blank
        if XLP!="":PLTblock=pmag.get_dictitem(PLTblock,'magic_method_codes',XLP,'not') # reject data with XLP in method_code
        if len(PLTblock)>2:
            title=PLTblock[0][plot_key]
            spcs=[]
            for rec in PLTblock:
                if rec['er_specimen_name'] not in spcs:spcs.append(rec['er_specimen_name'])
            for spc in spcs:
                SPCblock=pmag.get_dictitem(PLTblock,'er_specimen_name',spc,'T') # plot specimen by specimen
                INTblock=[]
                for rec in SPCblock:
                    INTblock.append([float(rec[dmag_key]),0,0,float(rec[int_key]),1,rec['measurement_flag']])
                if len(INTblock)>2:
                    pmagplotlib.plotMT(FIG['demag'],INTblock,title,0,units,norm)
            if not plot:
                files={}
                for key in FIG.keys():
                    files[key]=title+'_'+LT+'.'+fmt
                pmagplotlib.saveP(FIG,files) 
                sys.exit()
            else:
                pmagplotlib.drawFIGS(FIG)
                ans=raw_input(" S[a]ve to save plot, [q]uit,  Return to continue:  ")
                if ans=='q':sys.exit()
                if ans=="a": 
                    files={}
                    for key in FIG.keys():
                        files[key]=title+'_'+LT+'.svg' 
                    pmagplotlib.saveP(FIG,files) 
            pmagplotlib.clearFIG(FIG['demag'])

if __name__ == "__main__":
    main()
