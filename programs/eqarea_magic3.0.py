#!/usr/bin/env python
import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import new_builder as nb

def main():
    """
    NAME
        eqarea_magic.py

    DESCRIPTION
       makes equal area projections from declination/inclination data

    SYNTAX 
        eqarea_magic.py [command line options]
    
    INPUT 
       takes magic formatted pmag_results, pmag_sites, pmag_samples or pmag_specimens
    
    OPTIONS
        -h prints help message and quits
        -f FILE: specify input magic format file from magic,default='pmag_results.txt'
         supported types=[magic_measurements,pmag_specimens, pmag_samples, pmag_sites, pmag_results, magic_web]
        -obj OBJ: specify  level of plot  [all, sit, sam, spc], default is all
        -crd [s,g,t]: specify coordinate system, [s]pecimen, [g]eographic, [t]ilt adjusted
                default is geographic, unspecified assumed geographic
        -fmt [svg,png,jpg] format for output plots
        -ell [F,K,B,Be,Bv] plot Fisher, Kent, Bingham, Bootstrap ellipses or Boostrap eigenvectors
        -c plot as colour contour 
        -sav save plot and quit quietly
    NOTE
        all: entire file; sit: site; sam: sample; spc: specimen
    """
    # initialize some default variables
    FIG = {} # plot dictionary
    FIG['eqarea'] = 1 # eqarea is figure 1
    plotE = 0
    plt = 0  # default to not plotting
    verbose = pmagplotlib.verbose
    # extract arguments from sys.argv
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    dir_path = pmag.get_named_arg_from_sys("-WD", default_val=os.getcwd())
    pmagplotlib.plot_init(FIG['eqarea'],5,5)
    in_file = os.path.join(dir_path, pmag.get_named_arg_from_sys("-f", default_val="sites.txt"))
    plot_by = pmag.get_named_arg_from_sys("-obj", default_val="all").lower()
    if plot_by == 'all':
        plot_key = 'all'
    if plot_by == 'sit':
        plot_key = 'site_name'
    if plot_by == 'sam':
        plot_key = 'sample_name'
    if plot_by == 'spc':
        plot_key = 'specimen_name'
    if '-c' in sys.argv:
        contour = 1
    else:
        contour = 0
    if '-sav' in sys.argv: 
        plt = 1
        verbose = 0
    if '-ell' in sys.argv:
        plotE = 1
        ind = sys.argv.index('-ell')
        ell_type = sys.argv[ind+1]
        ell_type = pmag.get_named_arg_from_sys("-ell", "F")
        dist = ell_type.upper()
        # if dist type is unrecognized, use Fisher
        if dist not in ['F', 'K', 'B', 'BE', 'BV']:
            dist = 'F'
        if dist == "BV":
            FIG['bdirs'] = 2
            pmagplotlib.plot_init(FIG['bdirs'],5,5)
    crd = pmag.get_named_arg_from_sys("-crd", default_val="g")
    if crd == 's':
        coord = "-1"
    elif crd == 't':
        coord="100"
    else: 
        coord = "0"
    fmt = pmag.get_named_arg_from_sys("-fmt", "svg")
        
    # all of these are probs wrong....
    Dec_keys=['site_dec','sample_dec','specimen_dec','measurement_dec','average_dec','none']
    Dec_keys = ['dir_dec']
    Inc_keys=['site_inc','sample_inc','specimen_inc','measurement_inc','average_inc','none']
    Inc_keys = ['dir_inc']
    Tilt_keys=['tilt_correction','site_tilt_correction','sample_tilt_correction','specimen_tilt_correction','none']
    Tilt_keys=['dir_tilt_correction']
    Dir_type_keys=['','site_direction_type','sample_direction_type','specimen_direction_type']

    data_container = nb.MagicDataFrame(in_file)
    data = data_container.df
    
    if verbose:    
        print len(data),' records read from ',in_file
    #

    # find desired dec,inc data:
    dir_type_key=''
    #
    # get plotlist if not plotting all records
    #
    plotlist=[]
    if plot_key!="all":
        # return all where plot_key is not blank
        plots = data[data[plot_key].notnull()]
        plotlist = list(plots.index.unique()) # grab unique index
    else:
        plotlist.append('All')

    for plot in plotlist:
        if verbose:
            print plot
        if plot == 'All':
            plot_data = data
        else:
            plot_data = data.ix[plot]
      
        DIblock = []
        GCblock = []
        SLblock, SPblock = [], []
        title = plot
        mode = 1
        k = 0
        
        # get all records where dec & inc values exist
        dec_key = Dec_keys[0]
        inc_key = Inc_keys[0]
        plot_data = plot_data[plot_data[dec_key].notnull() & plot_data[inc_key].notnull()]

        # add tilt key into DataFrame columns if it isn't there already
        tilt_key = Tilt_keys[0] # 'tilt_correction'
        if tilt_key not in plot_data.columns:
            plot_data[tilt_key] = ''

        if coord =='0':  # geographic, use blank records
            plot_data = plot_data[(plot_data[tilt_key] == coord) | (plot_data[tilt_key] == '')]
        else:  # not geographic coordinates, use only records with correct tilt_key
            plot_data = plot_data[plot_data[tilt_key] == coord]

        # get metadata for naming the plot file
        locations = data_container.get_name(plot_data, 'location_name')
        site = data_container.get_name(plot_data, 'site_name')
        sample = data_container.get_name(plot_data, 'sample_name')
        specimen = data_container.get_name(plot_data, 'specimen_name')

        DIblock = [[float(row[dec_key]), float(row[inc_key])] for ind, row in plot_data.iterrows()]
        # make sure magic_method_codes is in plot_data
        if 'magic_method_codes' not in plot_data.columns:
            plot_data['magic_method_codes'] = ''

        SLblock = [[ind, row['magic_method_codes']] for ind, row in plot_data.iterrows()]

        cond = plot_data[tilt_key] == coord # LJ ADD to this cond: rec[dir_type_key] != 'l'.  just don't know what dir_type_key is in 3.0 yet
        GCblock = [[float(row[dec_key]), float(row[inc_key])] for ind, row in  plot_data[cond].iterrows()]
        #GCblock = []  # LJ GCblock is being incorrectly filled in above.  problem is probably the [dir_type_key] != 'l' issue
        SPblock = [[ind, row['magic_method_codes']] for ind, row in plot_data[cond].iterrows()]


        if len(DIblock) > 0:
            if contour == 0:
                pmagplotlib.plotEQ(FIG['eqarea'], DIblock, title)
            else:
                pmagplotlib.plotEQcont(FIG['eqarea'], DIblock)
        else:
            pmagplotlib.plotNET(FIG['eqarea'])


        if len(GCblock)>0:
            for rec in GCblock:
                pmagplotlib.plotC(FIG['eqarea'],rec,90.,'g')


        if len(DIblock) == 0 and len(GCblock) == 0:
            if verbose:
                print "no records for plotting"
            sys.exit()
                
        if plotE == 1:
            ppars = pmag.doprinc(DIblock) # get principal directions
            nDIs, rDIs, npars, rpars = [], [], [], []
            for rec in DIblock:
                angle=pmag.angle([rec[0],rec[1]],[ppars['dec'],ppars['inc']])
                if angle>90.:
                    rDIs.append(rec)
                else:
                    nDIs.append(rec)
            if dist=='B': # do on whole dataset
                etitle="Bingham confidence ellipse"
                bpars=pmag.dobingham(DIblock)
                for key in bpars.keys():
                    if key!='n' and verbose:print "    ",key, '%7.1f'%(bpars[key])
                    if key=='n' and verbose:print "    ",key, '       %i'%(bpars[key])
                npars.append(bpars['dec']) 
                npars.append(bpars['inc'])
                npars.append(bpars['Zeta']) 
                npars.append(bpars['Zdec']) 
                npars.append(bpars['Zinc'])
                npars.append(bpars['Eta']) 
                npars.append(bpars['Edec']) 
                npars.append(bpars['Einc'])
            if dist=='F':
                etitle="Fisher confidence cone"
                if len(nDIs)>2:
                    fpars=pmag.fisher_mean(nDIs)
                    for key in fpars.keys():
                        if key!='n' and verbose:print "    ",key, '%7.1f'%(fpars[key])
                        if key=='n' and verbose:print "    ",key, '       %i'%(fpars[key])
                    mode+=1
                    npars.append(fpars['dec']) 
                    npars.append(fpars['inc'])
                    npars.append(fpars['alpha95']) # Beta
                    npars.append(fpars['dec']) 
                    isign=abs(fpars['inc'])/fpars['inc'] 
                    npars.append(fpars['inc']-isign*90.) #Beta inc
                    npars.append(fpars['alpha95']) # gamma 
                    npars.append(fpars['dec']+90.) # Beta dec
                    npars.append(0.) #Beta inc
                if len(rDIs)>2:
                    fpars=pmag.fisher_mean(rDIs)
                    if verbose:print "mode ",mode
                    for key in fpars.keys():
                        if key!='n' and verbose:print "    ",key, '%7.1f'%(fpars[key])
                        if key=='n' and verbose:print "    ",key, '       %i'%(fpars[key])
                    mode+=1
                    rpars.append(fpars['dec']) 
                    rpars.append(fpars['inc'])
                    rpars.append(fpars['alpha95']) # Beta
                    rpars.append(fpars['dec']) 
                    isign=abs(fpars['inc'])/fpars['inc'] 
                    rpars.append(fpars['inc']-isign*90.) #Beta inc
                    rpars.append(fpars['alpha95']) # gamma 
                    rpars.append(fpars['dec']+90.) # Beta dec
                    rpars.append(0.) #Beta inc
            if dist=='K':
                etitle="Kent confidence ellipse"
                if len(nDIs)>3:
                    kpars=pmag.dokent(nDIs,len(nDIs))
                    if verbose:print "mode ",mode
                    for key in kpars.keys():
                        if key!='n' and verbose:print "    ",key, '%7.1f'%(kpars[key])
                        if key=='n' and verbose:print "    ",key, '       %i'%(kpars[key])
                    mode+=1
                    npars.append(kpars['dec']) 
                    npars.append(kpars['inc'])
                    npars.append(kpars['Zeta']) 
                    npars.append(kpars['Zdec']) 
                    npars.append(kpars['Zinc'])
                    npars.append(kpars['Eta']) 
                    npars.append(kpars['Edec']) 
                    npars.append(kpars['Einc'])
                if len(rDIs)>3:
                    kpars=pmag.dokent(rDIs,len(rDIs))
                    if verbose:print "mode ",mode
                    for key in kpars.keys():
                        if key!='n' and verbose:print "    ",key, '%7.1f'%(kpars[key])
                        if key=='n' and verbose:print "    ",key, '       %i'%(kpars[key])
                    mode+=1
                    rpars.append(kpars['dec']) 
                    rpars.append(kpars['inc'])
                    rpars.append(kpars['Zeta']) 
                    rpars.append(kpars['Zdec']) 
                    rpars.append(kpars['Zinc'])
                    rpars.append(kpars['Eta']) 
                    rpars.append(kpars['Edec']) 
                    rpars.append(kpars['Einc'])
            else: # assume bootstrap
                if dist=='BE':
                    if len(nDIs)>5:
                        BnDIs=pmag.di_boot(nDIs)
                        Bkpars=pmag.dokent(BnDIs,1.)
                        if verbose:print "mode ",mode
                        for key in Bkpars.keys():
                            if key!='n' and verbose:print "    ",key, '%7.1f'%(Bkpars[key])
                            if key=='n' and verbose:print "    ",key, '       %i'%(Bkpars[key])
                        mode+=1
                        npars.append(Bkpars['dec']) 
                        npars.append(Bkpars['inc'])
                        npars.append(Bkpars['Zeta']) 
                        npars.append(Bkpars['Zdec']) 
                        npars.append(Bkpars['Zinc'])
                        npars.append(Bkpars['Eta']) 
                        npars.append(Bkpars['Edec']) 
                        npars.append(Bkpars['Einc'])
                    if len(rDIs)>5:
                        BrDIs=pmag.di_boot(rDIs)
                        Bkpars=pmag.dokent(BrDIs,1.)
                        if verbose:print "mode ",mode
                        for key in Bkpars.keys():
                            if key!='n' and verbose:print "    ",key, '%7.1f'%(Bkpars[key])
                            if key=='n' and verbose:print "    ",key, '       %i'%(Bkpars[key])
                        mode+=1
                        rpars.append(Bkpars['dec']) 
                        rpars.append(Bkpars['inc'])
                        rpars.append(Bkpars['Zeta']) 
                        rpars.append(Bkpars['Zdec']) 
                        rpars.append(Bkpars['Zinc'])
                        rpars.append(Bkpars['Eta']) 
                        rpars.append(Bkpars['Edec']) 
                        rpars.append(Bkpars['Einc'])
                    etitle="Bootstrapped confidence ellipse"
                elif dist=='BV':
                    sym={'lower':['o','c'],'upper':['o','g'],'size':3,'edgecolor':'face'}
                    if len(nDIs)>5:
                        BnDIs=pmag.di_boot(nDIs)
                        pmagplotlib.plotEQsym(FIG['bdirs'],BnDIs,'Bootstrapped Eigenvectors', sym)
                    if len(rDIs)>5:
                        BrDIs=pmag.di_boot(rDIs)
                        if len(nDIs)>5:  # plot on existing plots
                            pmagplotlib.plotDIsym(FIG['bdirs'],BrDIs,sym)
                        else:
                            pmagplotlib.plotEQ(FIG['bdirs'],BrDIs,'Bootstrapped Eigenvectors')
            if dist=='B':
                if len(nDIs)> 3 or len(rDIs)>3: pmagplotlib.plotCONF(FIG['eqarea'],etitle,[],npars,0)
            elif len(nDIs)>3 and dist!='BV':
                pmagplotlib.plotCONF(FIG['eqarea'],etitle,[],npars,0)
                if len(rDIs)>3:
                    pmagplotlib.plotCONF(FIG['eqarea'],etitle,[],rpars,0)
            elif len(rDIs)>3 and dist!='BV':
                pmagplotlib.plotCONF(FIG['eqarea'],etitle,[],rpars,0)

        for key in FIG.keys():
            files = {}
            filename = pmag.get_named_arg_from_sys('-fname')
            if filename:
                filename+= '.' + fmt
            else:
                filename='LO:_'+locations+'_SI:_'+site+'_SA:_'+sample+'_SP:_'+specimen+'_CO:_'+crd+'_TY:_'+key+'_.'+fmt
            files[key]=filename

        if pmagplotlib.isServer:
            black     = '#000000'
            purple    = '#800080'
            titles={}
            titles['eq']='Equal Area Plot'
            FIG = pmagplotlib.addBorders(FIG,titles,black,purple)
            pmagplotlib.saveP(FIG,files)

        if plt:
            pmagplotlib.saveP(FIG,files)
            continue
        if verbose:
            pmagplotlib.drawFIGS(FIG)
            ans=raw_input(" S[a]ve to save plot, [q]uit, Return to continue:  ")
            if ans == "q":
                sys.exit()
            if ans == "a":
                pmagplotlib.saveP(FIG,files) 

        continue
        

if __name__ == "__main__":
    main() 
