#!/usr/bin/env python
import sys,pmag,pmagplotlib
def main():
    """
    NAME
        lowrie.py

    DESCRIPTION
       plots intensity decay curves for Lowrie experiments

    SYNTAX 
        lowrie -h [command line options]
    
    INPUT 
       takes SIO formatted input files
    
    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file
        -N do not normalize by maximum magnetization
    """
    FIG={} # plot dictionary
    FIG['lowrie']=1 # demag is figure 1
    pmagplotlib.plot_init(FIG['lowrie'],6,6)
    XLP=""
    norm=1
    if len(sys.argv)>1:
        if '-h' in sys.argv:
            print main.__doc__
            sys.exit()
        if '-N' in sys.argv: norm=0
        if '-f' in sys.argv:
            ind=sys.argv.index("-f")
            in_file=sys.argv[ind+1]
    data=open(in_file).readlines()
    PmagRecs=[]
    keys=['specimen','treatment','csd','M','dec','inc']
    for line in data:
        PmagRec={}
        rec=line.replace('\n','').split()
        for k in range(len(keys)): 
            PmagRec[keys[k]]=rec[k]
        PmagRecs.append(PmagRec)
    specs=pmag.get_dictkey(PmagRecs,'specimen','')
    sids=[]
    for spec in specs:
        if spec not in sids:sids.append(spec) # get list of unique specimen names
    for spc in sids:  # step through the specimen names
        print spc
        specdata=pmag.get_dictitem(PmagRecs,'specimen',spc,'T') # get all this one's data
        DIMs,Temps=[],[]
        for dat in specdata: # step through the data
            DIMs.append([float(dat['dec']),float(dat['inc']),float(dat['M'])])
            Temps.append(float(dat['treatment']))
        carts=pmag.dir2cart(DIMs).transpose()
        if norm==1:
            nrm=0
            m1,m2,m3=max(abs(carts[0])),max(abs(carts[1])),max(abs(carts[2]))
            if m1>m2:nrm=m1
            if m2>nrm:nrm=m2
            if m3>nrm:nrm=m3
        else: nrm=1.
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[0])/nrm,sym='r-')
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[0])/nrm,sym='ro')
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[1])/nrm,sym='b-')
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[1])/nrm,sym='bs')
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[2])/nrm,sym='m-')
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[2])/nrm,sym='m^',title=spc)
        pmagplotlib.drawFIGS(FIG)
        ans=raw_input('Save figure? y/[n]')
        if ans=='y':
            files={'lowrie':spc+'.pdf'}
            pmagplotlib.saveP(FIG,files)
        pmagplotlib.clearFIG(FIG['lowrie'])
main() 
