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
       plotdi_e.py

    DESCRIPTION
       plots equal area projection  from dec inc data and cones of confidence
           (Fisher, kent or Bingham or bootstrap).

    INPUT FORMAT
       takes dec/inc as first two columns in space delimited file

    SYNTAX
       plotdi_e.py [command line options]

    OPTIONS
        -h prints help message and quits
        -i for interactive parameter entry
        -f FILE, sets input filename on command line
        -Fish plots unit vector mean direction, alpha95
        -Bing plots Principal direction, Bingham confidence ellipse
        -Kent plots unit vector mean direction, confidence ellipse
        -Boot E plots unit vector mean direction, bootstrapped confidence ellipse
        -Boot V plots  unit vector mean direction, distribution of bootstrapped means

    """
    dist='F' # default distribution is Fisherian
    mode=1
    title=""
    EQ={'eq':1}
    if len(sys.argv) > 0:
        if '-h' in sys.argv: # check if help is needed
            print(main.__doc__)
            sys.exit() # graceful quit
        if '-i' in sys.argv: # ask for filename
            file=input("Enter file name with dec, inc data: ")
            dist=input("Enter desired distrubution: [Fish]er, [Bing]ham, [Kent] [Boot] [default is Fisher]: ")
            if dist=="":dist="F"
            if dist=="Bing":dist="B"
            if dist=="Kent":dist="K"
            if dist=="Boot":
                 type=input(" Ellipses or distribution of vectors? [E]/V ")
                 if type=="" or type=="E":
                     dist="BE"
                 else:
                     dist="BE"
        else:
#
            if '-f' in sys.argv:
                ind=sys.argv.index('-f')
                file=sys.argv[ind+1]
            else:
                print('you must specify a file name')
                print(main.__doc__)
                sys.exit()
            if '-Bing' in sys.argv:dist='B'
            if '-Kent' in sys.argv:dist='K'
            if '-Boot' in sys.argv:
                ind=sys.argv.index('-Boot')
                type=sys.argv[ind+1]
                if type=='E':
                    dist='BE'
                elif type=='V':
                    dist='BV'
                    EQ['bdirs']=2
                    pmagplotlib.plot_init(EQ['bdirs'],5,5)
                else:
                    print(main.__doc__)
                    sys.exit()
    pmagplotlib.plot_init(EQ['eq'],5,5)
#
# get to work
    f=open(file,'r')
    data=f.readlines()
#
    DIs= [] # set up list for dec inc data
    DiRecs=[]
    pars=[]
    nDIs,rDIs,npars,rpars=[],[],[],[]
    mode =1
    for line in data:   # read in the data from standard input
        DiRec={}
        rec=line.split() # split each line on space to get records
        DIs.append((float(rec[0]),float(rec[1]),1.))
        DiRec['dec']=rec[0]
        DiRec['inc']=rec[1]
        DiRec['direction_type']='l'
        DiRecs.append(DiRec)
    # split into two modes
    ppars=pmag.doprinc(DIs) # get principal directions
    for rec in DIs:
        angle=pmag.angle([rec[0],rec[1]],[ppars['dec'],ppars['inc']])
        if angle>90.:
            rDIs.append(rec)
        else:
            nDIs.append(rec)
    if dist=='B': # do on whole dataset
        title="Bingham confidence ellipse"
        bpars=pmag.dobingham(DIs)
        for key in list(bpars.keys()):
            if key!='n':print("    ",key, '%7.1f'%(bpars[key]))
            if key=='n':print("    ",key, '       %i'%(bpars[key]))
        npars.append(bpars['dec'])
        npars.append(bpars['inc'])
        npars.append(bpars['Zeta'])
        npars.append(bpars['Zdec'])
        npars.append(bpars['Zinc'])
        npars.append(bpars['Eta'])
        npars.append(bpars['Edec'])
        npars.append(bpars['Einc'])
    if dist=='F':
        title="Fisher confidence cone"
        if len(nDIs)>3:
            fpars=pmag.fisher_mean(nDIs)
            print("mode ",mode)
            for key in list(fpars.keys()):
                if key!='n':print("    ",key, '%7.1f'%(fpars[key]))
                if key=='n':print("    ",key, '       %i'%(fpars[key]))
            mode+=1
            npars.append(fpars['dec'])
            npars.append(fpars['inc'])
            npars.append(fpars['alpha95']) # Beta
            npars.append(fpars['dec'])
            isign=abs(fpars['inc']) / fpars['inc']
            npars.append(fpars['inc']-isign*90.) #Beta inc
            npars.append(fpars['alpha95']) # gamma
            npars.append(fpars['dec']+90.) # Beta dec
            npars.append(0.) #Beta inc
        if len(rDIs)>3:
            fpars=pmag.fisher_mean(rDIs)
            print("mode ",mode)
            for key in list(fpars.keys()):
                if key!='n':print("    ",key, '%7.1f'%(fpars[key]))
                if key=='n':print("    ",key, '       %i'%(fpars[key]))
            mode+=1
            rpars.append(fpars['dec'])
            rpars.append(fpars['inc'])
            rpars.append(fpars['alpha95']) # Beta
            rpars.append(fpars['dec'])
            isign=abs(fpars['inc']) / fpars['inc']
            rpars.append(fpars['inc']-isign*90.) #Beta inc
            rpars.append(fpars['alpha95']) # gamma
            rpars.append(fpars['dec']+90.) # Beta dec
            rpars.append(0.) #Beta inc
    if dist=='K':
        title="Kent confidence ellipse"
        if len(nDIs)>3:
            kpars=pmag.dokent(nDIs,len(nDIs))
            print("mode ",mode)
            for key in list(kpars.keys()):
                if key!='n':print("    ",key, '%7.1f'%(kpars[key]))
                if key=='n':print("    ",key, '       %i'%(kpars[key]))
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
            print("mode ",mode)
            for key in list(kpars.keys()):
                if key!='n':print("    ",key, '%7.1f'%(kpars[key]))
                if key=='n':print("    ",key, '       %i'%(kpars[key]))
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
                print("mode ",mode)
                for key in list(Bkpars.keys()):
                    if key!='n':print("    ",key, '%7.1f'%(Bkpars[key]))
                    if key=='n':print("    ",key, '       %i'%(Bkpars[key]))
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
                print("mode ",mode)
                for key in list(Bkpars.keys()):
                    if key!='n':print("    ",key, '%7.1f'%(Bkpars[key]))
                    if key=='n':print("    ",key, '       %i'%(Bkpars[key]))
                mode+=1
                rpars.append(Bkpars['dec'])
                rpars.append(Bkpars['inc'])
                rpars.append(Bkpars['Zeta'])
                rpars.append(Bkpars['Zdec'])
                rpars.append(Bkpars['Zinc'])
                rpars.append(Bkpars['Eta'])
                rpars.append(Bkpars['Edec'])
                rpars.append(Bkpars['Einc'])
            title="Bootstrapped confidence ellipse"
        elif dist=='BV':
            if len(nDIs)>5:
                pmagplotlib.plot_eq(EQ['eq'],nDIs,'Data')
                BnDIs=pmag.di_boot(nDIs)
                pmagplotlib.plot_eq(EQ['bdirs'],BnDIs,'Bootstrapped Eigenvectors')
            if len(rDIs)>5:
                BrDIs=pmag.di_boot(rDIs)
                if len(nDIs)>5:  # plot on existing plots
                    pmagplotlib.plot_di(EQ['eq'],rDIs)
                    pmagplotlib.plot_di(EQ['bdirs'],BrDIs)
                else:
                    pmagplotlib.plot_eq(EQ['eq'],rDIs,'Data')
                    pmagplotlib.plot_eq(EQ['bdirs'],BrDIs,'Bootstrapped Eigenvectors')
            pmagplotlib.draw_figs(EQ)
            ans=input('s[a]ve, [q]uit ')
            if ans=='q':sys.exit()
            if ans=='a':
                files={}
                for key in list(EQ.keys()):
                    files[key]='BE_'+key+'.svg'
                pmagplotlib.save_plots(EQ,files)
            sys.exit()
    if len(nDIs)>5:
        pmagplotlib.plot_conf(EQ['eq'],title,DiRecs,npars,1)
        if len(rDIs)>5 and dist!='B':
            pmagplotlib.plot_conf(EQ['eq'],title,[],rpars,0)
    elif len(rDIs)>5 and dist!='B':
        pmagplotlib.plot_conf(EQ['eq'],title,DiRecs,rpars,1)
    pmagplotlib.draw_figs(EQ)
    ans=input('s[a]ve, [q]uit ')
    if ans=='q':sys.exit()
    if ans=='a':
        files={}
        for key in list(EQ.keys()):
            files[key]=key+'.svg'
        pmagplotlib.save_plots(EQ,files)
    #

if __name__ == "__main__":
    main()
