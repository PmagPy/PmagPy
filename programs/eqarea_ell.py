#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from builtins import input
from past.utils import old_div
import sys
import numpy
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib

def main():
    """
    NAME
        eqarea_ell.py

    DESCRIPTION
       makes equal area projections from declination/inclination data
       and plot ellipses

    SYNTAX 
        eqarea_ell.py -h [command line options]
    
    INPUT 
       takes space delimited Dec/Inc data
    
    OPTIONS
        -h prints help message and quits
        -f FILE
        -fmt [svg,png,jpg] format for output plots
        -sav  saves figures and quits
        -ell [F,K,B,Be,Bv] plot Fisher, Kent, Bingham, Bootstrap ellipses or Boostrap eigenvectors
    """
    FIG={} # plot dictionary
    FIG['eq']=1 # eqarea is figure 1
    fmt,dist,mode,plot='svg','F',1,0
    sym={'lower':['o','r'],'upper':['o','w'],'size':10}
    plotE=0
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    pmagplotlib.plot_init(FIG['eq'],5,5)
    if '-sav' in sys.argv:plot=1
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        title=sys.argv[ind+1]
        data=numpy.loadtxt(title).transpose()
    if '-ell' in sys.argv:
        plotE=1
        ind=sys.argv.index('-ell')
        ell_type=sys.argv[ind+1]
        if ell_type=='F':dist='F' 
        if ell_type=='K':dist='K' 
        if ell_type=='B':dist='B' 
        if ell_type=='Be':dist='BE' 
        if ell_type=='Bv':
            dist='BV' 
            FIG['bdirs']=2
            pmagplotlib.plot_init(FIG['bdirs'],5,5)
    if '-fmt' in sys.argv:
        ind=sys.argv.index("-fmt")
        fmt=sys.argv[ind+1]
    DIblock=numpy.array([data[0],data[1]]).transpose()
    if len(DIblock)>0: 
        pmagplotlib.plotEQsym(FIG['eq'],DIblock,title,sym)
        if plot==0:pmagplotlib.drawFIGS(FIG)
    else:
        print("no data to plot")
        sys.exit()
    if plotE==1:
        ppars=pmag.doprinc(DIblock) # get principal directions
        nDIs,rDIs,npars,rpars=[],[],[],[]
        for rec in DIblock:
            angle=pmag.angle([rec[0],rec[1]],[ppars['dec'],ppars['inc']])
            if angle>90.:
                rDIs.append(rec)
            else:
                nDIs.append(rec)
        if dist=='B': # do on whole dataset
            etitle="Bingham confidence ellipse"
            bpars=pmag.dobingham(DIblock)
            for key in list(bpars.keys()):
                if key!='n' and pmagplotlib.verbose:print("    ",key, '%7.1f'%(bpars[key]))
                if key=='n' and pmagplotlib.verbose:print("    ",key, '       %i'%(bpars[key]))
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
            if len(nDIs)>3:
                fpars=pmag.fisher_mean(nDIs)
                for key in list(fpars.keys()):
                    if key!='n' and pmagplotlib.verbose:print("    ",key, '%7.1f'%(fpars[key]))
                    if key=='n' and pmagplotlib.verbose:print("    ",key, '       %i'%(fpars[key]))
                mode+=1
                npars.append(fpars['dec']) 
                npars.append(fpars['inc'])
                npars.append(fpars['alpha95']) # Beta
                npars.append(fpars['dec']) 
                isign=old_div(abs(fpars['inc']),fpars['inc']) 
                npars.append(fpars['inc']-isign*90.) #Beta inc
                npars.append(fpars['alpha95']) # gamma 
                npars.append(fpars['dec']+90.) # Beta dec
                npars.append(0.) #Beta inc
            if len(rDIs)>3:
                fpars=pmag.fisher_mean(rDIs)
                if pmagplotlib.verbose:print("mode ",mode)
                for key in list(fpars.keys()):
                    if key!='n' and pmagplotlib.verbose:print("    ",key, '%7.1f'%(fpars[key]))
                    if key=='n' and pmagplotlib.verbose:print("    ",key, '       %i'%(fpars[key]))
                mode+=1
                rpars.append(fpars['dec']) 
                rpars.append(fpars['inc'])
                rpars.append(fpars['alpha95']) # Beta
                rpars.append(fpars['dec']) 
                isign=old_div(abs(fpars['inc']),fpars['inc']) 
                rpars.append(fpars['inc']-isign*90.) #Beta inc
                rpars.append(fpars['alpha95']) # gamma 
                rpars.append(fpars['dec']+90.) # Beta dec
                rpars.append(0.) #Beta inc
        if dist=='K':
            etitle="Kent confidence ellipse"
            if len(nDIs)>3:
                kpars=pmag.dokent(nDIs,len(nDIs))
                if pmagplotlib.verbose:print("mode ",mode)
                for key in list(kpars.keys()):
                    if key!='n' and pmagplotlib.verbose:print("    ",key, '%7.1f'%(kpars[key]))
                    if key=='n' and pmagplotlib.verbose:print("    ",key, '       %i'%(kpars[key]))
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
                if pmagplotlib.verbose:print("mode ",mode)
                for key in list(kpars.keys()):
                    if key!='n' and pmagplotlib.verbose:print("    ",key, '%7.1f'%(kpars[key]))
                    if key=='n' and pmagplotlib.verbose:print("    ",key, '       %i'%(kpars[key]))
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
            if len(nDIs)<10 and len(rDIs)<10:
                print('too few data points for bootstrap')
                sys.exit()
            if dist=='BE':
                print('Be patient for bootstrap...')
                if len(nDIs)>=10:
                    BnDIs=pmag.di_boot(nDIs)
                    Bkpars=pmag.dokent(BnDIs,1.)
                    if pmagplotlib.verbose:print("mode ",mode)
                    for key in list(Bkpars.keys()):
                        if key!='n' and pmagplotlib.verbose:print("    ",key, '%7.1f'%(Bkpars[key]))
                        if key=='n' and pmagplotlib.verbose:print("    ",key, '       %i'%(Bkpars[key]))
                    mode+=1
                    npars.append(Bkpars['dec']) 
                    npars.append(Bkpars['inc'])
                    npars.append(Bkpars['Zeta']) 
                    npars.append(Bkpars['Zdec']) 
                    npars.append(Bkpars['Zinc'])
                    npars.append(Bkpars['Eta']) 
                    npars.append(Bkpars['Edec']) 
                    npars.append(Bkpars['Einc'])
                if len(rDIs)>=10:
                    BrDIs=pmag.di_boot(rDIs)
                    Bkpars=pmag.dokent(BrDIs,1.)
                    if pmagplotlib.verbose:print("mode ",mode)
                    for key in list(Bkpars.keys()):
                        if key!='n' and pmagplotlib.verbose:print("    ",key, '%7.1f'%(Bkpars[key]))
                        if key=='n' and pmagplotlib.verbose:print("    ",key, '       %i'%(Bkpars[key]))
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
                print('Be patient for bootstrap...')
                vsym={'lower':['+','k'],'upper':['x','k'],'size':5}
                if len(nDIs)>5:
                    BnDIs=pmag.di_boot(nDIs)
                    pmagplotlib.plotEQsym(FIG['bdirs'],BnDIs,'Bootstrapped Eigenvectors',vsym)
                if len(rDIs)>5:
                    BrDIs=pmag.di_boot(rDIs)
                    if len(nDIs)>5:  # plot on existing plots
                        pmagplotlib.plotDIsym(FIG['bdirs'],BrDIs,vsym)
                    else:
                        pmagplotlib.plotEQ(FIG['bdirs'],BrDIs,'Bootstrapped Eigenvectors',vsym)
        if dist=='B':
            if len(nDIs)> 3 or len(rDIs)>3: pmagplotlib.plotCONF(FIG['eq'],etitle,[],npars,0)
        elif len(nDIs)>3 and dist!='BV':
            pmagplotlib.plotCONF(FIG['eq'],etitle,[],npars,0)
            if len(rDIs)>3:
                pmagplotlib.plotCONF(FIG['eq'],etitle,[],rpars,0)
        elif len(rDIs)>3 and dist!='BV':
            pmagplotlib.plotCONF(FIG['eq'],etitle,[],rpars,0)
        if plot==0:pmagplotlib.drawFIGS(FIG)
    if plot==0:pmagplotlib.drawFIGS(FIG)
        #
    files={}
    for key in list(FIG.keys()):
        files[key]=title+'_'+key+'.'+fmt 
    if pmagplotlib.isServer:
        black     = '#000000'
        purple    = '#800080'
        titles={}
        titles['eq']='Equal Area Plot'
        FIG = pmagplotlib.addBorders(FIG,titles,black,purple)
        pmagplotlib.saveP(FIG,files)
    elif plot==0:
        ans=input(" S[a]ve to save plot, [q]uit, Return to continue:  ")
        if ans=="q": sys.exit()
        if ans=="a": 
            pmagplotlib.saveP(FIG,files) 
    else:
        pmagplotlib.saveP(FIG,files)

if __name__ == "__main__":
    main() 
