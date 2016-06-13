#!/usr/bin/env python

import pandas as pd
import numpy as np
import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib

from pmag_env import set_env
if not set_env.isServer:
    import pmagpy.nlt as nlt

import new_builder as nb

# initialize some variables
def save_redo(SpecRecs,inspec):
    SpecRecs,keys=pmag.fillkeys(SpecRecs)
    pmag.magic_write(inspec,SpecRecs,'pmag_specimens')

def main():
    """
    NAME
        thellier_magic.py
    
    DESCRIPTION
        plots Thellier-Thellier, allowing interactive setting of bounds
        and customizing of selection criteria.  Saves and reads interpretations
        from a pmag_specimen formatted table, default: thellier_specimens.txt

    SYNTAX 
        thellier_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f MEAS, set magic_measurements input file
        -fsp PRIOR, set pmag_specimen prior interpretations file
        -fan ANIS, set rmag_anisotropy file for doing the anisotropy corrections
        -fcr CRIT, set criteria file for grading.  
        -fmt [svg,png,jpg], format for images - default is svg
        -sav,  saves plots with out review (default format)
        -spc SPEC, plots single specimen SPEC, saves plot with specified format
            with optional -b bounds adn quits
        -b BEG END: sets  bounds for calculation
           BEG: starting step for slope calculation
           END: ending step for slope calculation
        -z use only z component difference for pTRM calculation
        
    DEFAULTS
        MEAS: magic_measurements.txt
        REDO: thellier_redo
        CRIT: NONE
        PRIOR: NONE
  
    OUTPUT 
        figures:
            ALL:  numbers refer to temperature steps in command line window
            1) Arai plot:  closed circles are zero-field first/infield
                           open circles are infield first/zero-field
                           triangles are pTRM checks
                           squares are pTRM tail checks
                           VDS is vector difference sum
                           diamonds are bounds for interpretation
            2) Zijderveld plot:  closed (open) symbols are X-Y (X-Z) planes
                                 X rotated to NRM direction
            3) (De/Re)Magnetization diagram:
                           circles are NRM remaining
                           squares are pTRM gained
            4) equal area projections:
 			   green triangles are pTRM gained direction
                           red (purple) circles are lower(upper) hemisphere of ZI step directions 
                           blue (cyan) squares are lower(upper) hemisphere IZ step directions 
            5) Optional:  TRM acquisition
            6) Optional: TDS normalization
        command line window:
            list is: temperature step numbers, temperatures (C), Dec, Inc, Int (units of measuements)
                     list of possible commands: type letter followed by return to select option
                     saving of plots creates .svg format files with specimen_name, plot type as name
    """ 
#
#   initializations
#
    first=1
    inlt=0
    version_num=pmag.get_version()
    TDinit,Tinit,field,first_save=0,0,-1,1
    user,comment,AniSpec,locname="",'',"",""
    ans,specimen,recnum,start,end=0,0,0,0,0
    plots,pmag_out,samp_file,style=0,"","","svg"
    verbose=pmagplotlib.verbose 
    fmt='.'+style
#
# default acceptance criteria
#
    accept=pmag.default_criteria(0)[0] # set the default criteria
#
# parse command line options
#
    Zdiff,anis=0,0
    spc,BEG,END="","",""
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    dir_path = pmag.get_named_arg_from_sys("-WD", default_val=os.getcwd())
    meas_file = pmag.get_named_arg_from_sys("-f", default_val="measurements.txt")
    spec_file=pmag.get_named_arg_from_sys("-fsp", default_val="specimens.txt")
    crit_file=pmag.get_named_arg_from_sys("-fcr", default_val="criteria.txt")
    spec_file=os.path.join(dir_path,spec_file)
    meas_file=os.path.join(dir_path,meas_file)
    crit_file=os.path.join(dir_path,crit_file)
    fmt = pmag.get_named_arg_from_sys("-fmt", "svg")
    if '-sav' in sys.argv: plots,verbose=1,0
    if '-z' in sys.argv: Zdiff=1
    specimen=pmag.get_named_arg_from_sys("-spc",default_val="")
    if '-b' in sys.argv:
        ind=sys.argv.index('-b')
        BEG=int(sys.argv[ind+1])
        END=int(sys.argv[ind+2])
    fnames = {'measurements': meas_file, 'specimens': spec_file, 'criteria': crit_file}
    contribution = nb.Contribution(dir_path, custom_filenames=fnames, read_tables=['measurements', 'specimens', 'criteria'])
#
#   import  prior interpretations  from specimen file
#
    specimen_cols = ['analyst_names', 'aniso_ftest', 'aniso_ftest12', 'aniso_ftest23', 'aniso_s', 'aniso_s_mean', 'aniso_s_n_measurements', 'aniso_s_sigma', 'aniso_s_unit', 'aniso_tilt_correction', 'aniso_type', 'aniso_v1', 'aniso_v2', 'aniso_v3', 'citations', 'description', 'dir_alpha95', 'dir_comp_name', 'dir_dec', 'dir_inc', 'dir_mad_free', 'dir_n_measurements', 'dir_tilt_correction', 'experiment_names', 'geologic_classes', 'geologic_types', 'hyst_bc', 'hyst_bcr', 'hyst_mr_moment', 'hyst_ms_moment', 'int_abs', 'int_b', 'int_b_beta', 'int_b_sigma', 'int_corr', 'int_dang', 'int_drats', 'int_f', 'int_fvds', 'int_gamma', 'int_mad_free', 'int_md', 'int_n_measurements', 'int_n_ptrm', 'int_q', 'int_rsc', 'int_treat_dc_field', 'lithologies', 'meas_step_max', 'meas_step_min', 'meas_step_unit', 'method_codes', 'sample_name', 'software_packages', 'specimen_name']
    if 'specimens' in contribution.tables:
#        contribution.propagate_name_down('sample_name','measurements')
        spec_container = contribution.tables['specimens']
        prior_spec_data=spec_container.get_records_for_code('LP-PI-TRM',strict_match=False) # look up all prior intensity interpretations
#
#  tie sample names to measurement data
#
    else:
           spec_container, prior_spec_data = None, []
    backup=0
    #
    intlist = ['magn_moment', 'magn_volume', 'magn_mass']
#
#   create measurement dataframe
#
    meas_container = contribution.tables['measurements']
    meas_data = meas_container.df
#
    meas_data['method_codes']=meas_data['method_codes'].str.replace(" ","") # get rid of nasty spaces
    meas_data= meas_data[meas_data['method_codes'].str.contains('LP-PI-TRM|LP-TRM|LP-TRM-TD')==True] # fish out zero field steps for plotting
    intensity_types = [col_name for col_name in meas_data.columns if col_name in intlist]
    int_key = intensity_types[0] # plot first intensity method found - normalized to initial value anyway - doesn't matter which used
    meas_data = meas_data[meas_data[int_key].notnull()] # get all the non-null intensity records of the same type
    if 'flag' not in meas_data.columns: meas_data['flag'] = 'g' # set the default flag to good
    meas_data = meas_data[meas_data['flag'].str.contains('g')==True] # only the 'good' measurements
    thel_data = meas_data[meas_data['method_codes'].str.contains('LP-PI-TRM')==True] # get all the Thellier data
    trm_data = meas_data[meas_data['method_codes'].str.contains('LP-TRM')==True] # get all the TRM acquisition data
    td_data = meas_data[meas_data['method_codes'].str.contains('LP-TRM-TD')==True] # get all the TD data
    anis_data = meas_data[meas_data['method_codes'].str.contains('LP-AN')==True] # get all the anisotropy data
#
# get list of unique specimen names from measurement data
#
    specimen_names= meas_data.specimen_name.unique() # this is a list of all the specimen names
    specimen_names= specimen_names.tolist()
    specimen_names.sort()
#
# set up new DataFrame for this sessions specimen interpretations
#
    data_container = nb.MagicDataFrame(dtype='specimens', columns=specimen_cols)
    current_spec_data = data_container.df # this is for interpretations from this session
    locname='LookItUp'
    if specimen=="":
        k = 0
    else:
        k=specimen_names.index(specimen)
    # define figure numbers for arai, zijderveld and 
    #   de-,re-magnetization diagrams
    AZD={}
    AZD['deremag'], AZD['zijd'],AZD['arai'],AZD['eqarea']=1,2,3,4
    pmagplotlib.plot_init(AZD['arai'],5,5)
    pmagplotlib.plot_init(AZD['zijd'],5,5)
    pmagplotlib.plot_init(AZD['deremag'],5,5)
    pmagplotlib.plot_init(AZD['eqarea'],5,5)
    if len(trm_data)>0: 
        AZD['TRM']=5
        pmagplotlib.plot_init(AZD['TRM'],5,5)
    if len(td_data)>0: 
        AZD['TDS']=6
        pmagplotlib.plot_init(AZD['TDS'],5,5)
    #
    while k < len(specimen_names):
        this_specimen=specimen_names[k] # set the current specimen for plotting
        if verbose and  this_specimen!="":print this_specimen, k+1 , 'out of ',len(specimen_names)
#
#    set up datablocks
#
        thelblock= thel_data[thel_data['specimen_name'].str.contains(this_specimen)==True] # fish out this specimen
        trmblock= trm_data[trm_data['specimen_name'].str.contains(this_specimen)==True] # fish out this specimen
        tdsrecs= td_data[td_data['specimen_name'].str.contains(this_specimen)==True] # fish out this specimen
        anisblock= anis_data[anis_data['specimen_name'].str.contains(this_specimen)==True] # fish out the anisotropy data
        prior_specimen_interpretations= prior_spec_data[prior_spec_data['specimen_name'].str.contains(this_specimen)==True] # fish out prior interpretation 
#
# sort data into types
#
        araiblock,field=pmag.sortarai(thelblock,this_specimen,Zdiff,version=3)
        first_Z=araiblock[0]
        GammaChecks=araiblock[5]
        if len(first_Z)<3:
           if backup==0:
                   k+=1
                   if verbose:
                       print 'skipping specimen - moving forward ', this_specimen
           else:
                   k-=1
                   if verbose:
                       print 'skipping specimen - moving backward ', this_specimen
        else:
               backup=0
               zijdblock,units=pmag.find_dmag_rec(this_specimen,thelblock,version=3)
               if BEG=="" and len(prior_specimen_interpretations)>0:
                   if verbose: print 'Looking up saved interpretation....'
#
# get prior interpretation steps
#
                   beg_int=pd.to_numeric(prior_specimen_interpretations.meas_step_min.values).tolist()[0] 
                   end_int=pd.to_numeric(prior_specimen_interpretations.meas_step_max.values).tolist()[0]
               else: beg_int,end_int="",""
               recnum=0
               if verbose: print "index step Dec   Inc  Int       Gamma"
               for plotrec in zijdblock:
                   if plotrec[0]==beg_int:start=recnum # while we are at it, collect these bounds
                   if plotrec[0]==end_int:end=recnum
                   if verbose:
                       if GammaChecks!="":
                           gamma=""
                           for g in GammaChecks:
                               if g[0]==plotrec[0]-273:
                                   gamma=g[1]
                                   break
                       if gamma!="":
                           print '%i     %i %7.1f %7.1f %8.3e %7.1f' % (recnum,plotrec[0]-273,plotrec[1],plotrec[2],plotrec[3],gamma)
                       else:
                           print '%i     %i %7.1f %7.1f %8.3e ' % (recnum,plotrec[0]-273,plotrec[1],plotrec[2],plotrec[3])
                   recnum += 1
               for fig in AZD.keys():pmagplotlib.clearFIG(AZD[fig]) # clear all figures
               pmagplotlib.plotAZ(AZD,araiblock,zijdblock,this_specimen,units[0])
               if verbose:pmagplotlib.drawFIGS(AZD)
               print beg_int,end_int
               raw_input()
#
# work on TDS data later - no example available yet
#
    #           if len(tdsrecs)>2: # a TDS experiment
    #               tdsblock=[] # make a list for the TDS  data
    #               mkey,k="",0
    #               while mkey=="" and k<len(intlist)-1: # find which type of intensity
    #                   key= intlist[k]
    #                   if key in tdsrecs[0].keys() and tdsrecs[0][key]!="": mkey=key
    #                   k+=1
    #               if mkey=="":break # get outta here
    #               Tnorm=""
    #               for tdrec in tdsrecs:
    #                   meths=tdrec['method_codes'].split(":")
    #                   if  'LT-T-I' in meths and Tnorm=="": # found first total TRM 
    #                       Tnorm=float(tdrec[mkey]) # normalize by total TRM 
    #                       tdsblock.append([273,zijdblock[0][3]/Tnorm,1.]) # put in the zero step
    #                   if  'LT-T-Z' in meths and Tnorm!="": # found a LP-TRM-TD demag step, now need complementary LT-T-Z from zijdblock
    #                       step=float(tdrec['treatment_temp'])
    #                       Tint=""
    #                       if mkey!="":
    #                           Tint=float(tdrec[mkey])
    #                       if Tint!="":
    #                           for zrec in zijdblock:
    #                               if zrec[0]==step:  # found matching
    #                                   tdsblock.append([step,zrec[3]/Tnorm,Tint/Tnorm])
    #                                   break
    #               if len(tdsblock)>2: 
    #                   pmagplotlib.plotTDS(AZD['TDS'],tdsblock,s+':LP-PI-TDS:')
    #                   if verbose:pmagplotlib(drawFIGS(AZD)) 
    #               else: 
    #                   print "Something wrong here"
               if len(anisblock)>0:  # this specimen has anisotropy data
                           if verbose: print 'Found anisotropy record...'
#
# put in container for saving later
#
#

if __name__ == "__main__":
    main()
            
