#!/usr/bin/env python

# -*- python-indent-offset: 4; -*-

import pandas as pd
import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import new_builder as nb



def save_redo(SpecRecs,inspec):
    print "Saving changes to specimen file"
    pmag.magic_write(inspec,SpecRecs,'specimens')

def main():
    """
    NAME
        zeq_magic.py

    DESCRIPTION
        reads in magic_measurements formatted file, makes plots of remanence decay
        during demagnetization experiments.  Reads in prior interpretations saved in 
        a pmag_specimens formatted file and  allows re-interpretations of best-fit lines
        and planes and saves (revised or new) interpretations in a pmag_specimens file.  
        interpretations are saved in the coordinate system used. Also allows judicious editting of
        measurements to eliminate "bad" measurements.  These are marked as such in the magic_measurements
        input file.  they are NOT deleted, just ignored. 

    SYNTAX
        zeq_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f  MEASFILE: sets measurements format input file, default: measurements.txt
        -fsp SPECFILE: sets specimens format file with prior interpreations, default: specimens.txt
        -fsa SAMPFILE: sets samples format file with prior interpreations, default: samples.txt
        -Fp PLTFILE: sets filename for saved plot, default is name_type.fmt (where type is zijd, eqarea or decay curve)
        -crd [s,g,t]: sets coordinate system,  g=geographic, t=tilt adjusted, default: specimen coordinate system
        -spc SPEC  plots single specimen SPEC, saves plot with specified format 
              with optional -dir settings and quits
        -dir [L,P,F][beg][end]: sets calculation type for principal component analysis, default is none
             beg: starting step for PCA calculation
             end: ending step for PCA calculation
             [L,P,F]: calculation type for line, plane or fisher mean
             must be used with -spc option
        -fmt FMT: set format of saved plot [png,svg,jpg]
        -A:  suppresses averaging of  replicate measurements, default is to average
        -sav: saves all plots without review
    SCREEN OUTPUT:
        Specimen, N, a95, StepMin, StepMax, Dec, Inc, calculation type

    """
    # initialize some variables
    doave,e,b=1,0,0 # average replicates, initial end and beginning step
    intlist = ['magn_moment', 'magn_volume', 'magn_mass']
    plots,coord=0,'s'
    noorient=0
    version_num=pmag.get_version()
    verbose=pmagplotlib.verbose
    calculation_type,fmt="","svg"
    user,spec_keys,locname="",[],''
    sfile=""
    geo,tilt,ask=0,0,0
    PriorRecs=[] # empty list for prior interpretations
    backup=0
    specimen="" # can skip everything and just plot one specimen with bounds e,b
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    dir_path = pmag.get_named_arg_from_sys("-WD", default_val=os.getcwd())
    meas_file = pmag.get_named_arg_from_sys("-f", default_val="measurements.txt") 
    #full_meas_file=os.path.join(dir_path,meas_file)
    spec_file=pmag.get_named_arg_from_sys("-fsp", default_val="specimens.txt")
    samp_file=pmag.get_named_arg_from_sys("-fsa",default_val="")
    if samp_file!="":sfile='ok'
    samp_file=os.path.join(dir_path,samp_file)
    plot_file=pmag.get_named_arg_from_sys("-Fp",default_val="")
    crd = pmag.get_named_arg_from_sys("-crd", default_val="g")
    if crd == "s":
        coord = "-1"
    elif crd == "t":
        coord = "100"
    else:
        coord = "0"
    fmt = pmag.get_named_arg_from_sys("-fmt", "svg")
    specimen=pmag.get_named_arg_from_sys("-spc",default_val="")
    beg_pca,end_pca,direction_type="","",'L'
    if '-dir' in sys.argv:
        ind=sys.argv.index('-dir')
        direction_type=sys.argv[ind+1]
        beg_pca=int(sys.argv[ind+2])
        end_pca=int(sys.argv[ind+3])
        if direction_type=='L':calculation_type='DE-BFL'
        if direction_type=='P':calculation_type='DE-BFP'
        if direction_type=='F':calculation_type='DE-FM'
    if '-A' in sys.argv: doave=0
    if '-sav' in sys.argv: plots,verbose=1,0
    #
    first_save=1
    fnames = {'measurements': meas_file, 'specimens': spec_file, 'samples': samp_file}
    contribution = nb.Contribution(dir_path, custom_filenames=fnames, read_tables=['measurements', 'specimens', 'samples'])
#
#   import  specimens
#
    if 'specimens' in contribution.tables:
#        contribution.propagate_name_down('sample_name','measurements')
        spec_container = contribution.tables['specimens']
        spec_data=spec_container.get_records_for_code('DE-',strict_match=False) # look up all prior directional interpretations
#
#  tie sample names to measurement data
#
    else:
       	spec_container, spec_data = None, []


#
#   import samples  for orientation info
#
    if 'samples' in contribution.tables:
#        contribution.propagate_name_down('site_name','measurements')
        contribution.propagate_cols_down(col_names=['azimuth','dip','orientation_flag'],target_df_name='measurements',source_df_name='samples')
#
#   create measurement dataframe
#
    meas_container = contribution.tables['measurements']
    meas_data = meas_container.df
#
    meas_data= meas_data[meas_data['method_codes'].str.contains('LT-NO|LT-AF-Z|LT-T-Z|LT-M-Z')==True] # fish out zero field steps for plotting 
    meas_data= meas_data[meas_data['method_codes'].str.contains('AN|ARM|LP-TRM|LP-PI-ARM')==False] # strip out unwanted experiments
    intensity_types = [col_name for col_name in meas_data.columns if col_name in intlist]
    int_key = intensity_types[0] # plot first intensity method found - normalized to initial value anyway - doesn't matter which used
    meas_data = meas_data[meas_data[int_key].notnull()] # get all the non-null intensity records of the same type
    if 'flag' not in meas_data.columns: meas_data['flag'] = 'g' # set the default flag to good
    meas_data['treatment'] = meas_data['treat_ac_field'].where(cond=meas_data['treat_ac_field'] != '0', other=meas_data['treat_temp'])
    print meas_data['treat_ac_field'].head()
    print meas_data['treat_temp'].head()
    print meas_data['treatment'][:20]
    #meas_data.ix[meas_data.treatment==0,'treatment']=meas_data.treat_temp # make it treat_temp if treat_ac_field is 0
####  need to treat LP-NO specially - for af data, treatment should be zero, otherwise 273.
    meas_data['ZI']=1 # initialize these to one
    meas_data['instrument_codes']="" # initialize these to blank
#   for unusual case of microwave power....
    if 'treatment_mw_power' in meas_data.columns:
        meas_data.ix[meas_data.treatment_mw_power!=0,'treatment']=meas_data.treatment_mw_power*meas_data.treatment_mw_time # 
#
# get list of unique specimen names from measurement data
#
    specimen_names= meas_data.specimen_name.unique() # this is a list of all the specimen names
    specimen_names= specimen_names.tolist()
#
# define figure numbers for equal area, zijderveld,  
#  and intensity vs. demagnetiztion step respectively
    ZED={}
    ZED['eqarea'],ZED['zijd'],  ZED['demag']=1,2,3 
    pmagplotlib.plot_init(ZED['eqarea'],6,6)
    pmagplotlib.plot_init(ZED['zijd'],6,6)
    pmagplotlib.plot_init(ZED['demag'],6,6)
#    save_pca=0
    angle,direction_type,setangle="","",0
    if specimen=="":
        k = 0
    else:
        k=specimen_names.index(specimen)
    # let's look at the data now
    while k < len(specimen_names):
        this_specimen=specimen_names[k] # set the current specimen for plotting
        if verbose and  this_specimen!="":print this_specimen, k+1 , 'out of ',len(specimen_names)
        if setangle==0:angle=""
        this_specimen_measurements= meas_data[meas_data['specimen_name'].str.contains(this_specimen)==True] # fish out this specimen
#        this_specimen_measurements= this_specimen_measurements[this_specimen_measurements['flag'].str.contains('g')==True] # fish out this specimen
        if len(this_specimen_measurements)!=0:  # if there are measurements
#
#    set up datablock [[treatment,dec, inc, int, direction_type],[....]]
#
            tr=pd.to_numeric(this_specimen_measurements.treatment).tolist()
            print tr
            decs=pd.to_numeric(this_specimen_measurements.dir_dec).tolist()
            if angle=="":angle=decs[0]
            incs=pd.to_numeric(this_specimen_measurements.dir_inc).tolist()
            ints=pd.to_numeric(this_specimen_measurements[int_key]).tolist()
            ZI=this_specimen_measurements.ZI.tolist()
            flags=this_specimen_measurements.flag.tolist()
            codes=this_specimen_measurements.instrument_codes.tolist()
            datalist=[tr,decs,incs,ints,ZI,flags,codes]
            datablock=map(list,zip(*datalist)) # this transposes the columns and rows of the list of lists
            meths= this_specimen_measurements.method_codes.unique() # this is a list of all the specimen names
            units,methods="",""
            for m in meths: 
                if 'LT-AF-Z' in m: units='T' # units include tesla
                if 'LT-T-Z' in m: units=units+":K" # units include kelvin
                if 'LT-M-Z' in m: units=units+':J' # units include joules
                units=units.strip(':') # strip off extra colons
                #methods=methods.strip(':') # strip off extra colons
            print units
            pmagplotlib.plotZED(ZED,datablock,angle,this_specimen,units)
            pmagplotlib.drawFIGS(ZED)
#
        # create a new specimen record for the interpreation for this specimen
#        this_specimen_interpretation={col: "" for col in cols}
#        this_specimen_interpretation["analyst_mail_names"]=user
#        this_specimen_interpretation['software_packages']=version_num
#        this_specimen_interpretation['specimen_name']=version_num
#        this_specimen_interpretation["method_codes"]= methods
#        this_specimen_interpretation["meas_step_unit"]= units
#    #
#    #  collect info for current_specimen_interpretation dictionary
#    #
#    #
#    # find prior interpretation
#    #
#            if len(current_spec_data)==0: # no interpretations yet for this session
#                print "no current interpretation"
#                beg_pca,end_pca="",""
#                calculation_type=""
#                if len(prior_spec_data)!=0:
#                  if verbose: print "    looking up previous interpretations..."
#                  prior_specimen_interpretations= prior_spec_data[prior_spec_data['specimen_name'].str.contains(this_specimen)==True] # fish out prior interpretations 
#                  prior_spec_data= prior_spec_data[prior_spec_data['specimen_name'].str.contains(this_specimen)==False] # remove them from prior recs 
#         # get the ones that meet the current coordinate system
#                  print 'prior: ',prior_specimen_interpretations['meas_step_min']
#                  #    beg_pca=prior_specimen_interpretations.meas_step_min
#                  #    end_pca=prior_specimen_interpretations.meas_step_max
#                  #    print beg_pca,end_pca,prior_specimen_interpretations.tilt_correction
#                  raw_input()
#            else:
##                 print current_spec_data
        else:
             print "no data"
        raw_input('Ready for next specimen  ')
        k+=1
#
if __name__ == "__main__":
    main()
