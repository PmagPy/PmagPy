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
    norm=1 # default is to normalize by maximum axis
    if len(sys.argv)>1:
        if '-h' in sys.argv:
            print main.__doc__
            sys.exit()
        if '-N' in sys.argv: norm=0 # don't normalize
        if '-f' in sys.argv: # sets input filename
            ind=sys.argv.index("-f")
            in_file=sys.argv[ind+1]
        else:
            print main.__doc__
            print 'you must supply a file name'
            sys.exit() 
    else:
        print main.__doc__
        print 'you must supply a file name'
        sys.exit() 
    data=open(in_file).readlines() # open the SIO format file
    PmagRecs=[] # set up a list for the results
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
        if norm==1: # want to normalize
            nrm=max(max(abs(carts[0])),max(abs(carts[1])),max(abs(carts[2]))) # by maximum of x,y,z values
        else: nrm=1. # don't normalize
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[0])/nrm,sym='r-')
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[0])/nrm,sym='ro') # X direction
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[1])/nrm,sym='c-')
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[1])/nrm,sym='cs') # Y direction
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[2])/nrm,sym='k-')
        pmagplotlib.plotXY(FIG['lowrie'],Temps,abs(carts[2])/nrm,sym='k^',title=spc) # Z direction
        pmagplotlib.drawFIGS(FIG)
        ans=raw_input('Save figure? y/[n]')
        if ans=='y':
            files={'lowrie':spc+'.pdf'}
            pmagplotlib.saveP(FIG,files)
        pmagplotlib.clearFIG(FIG['lowrie'])
main() 
