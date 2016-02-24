#!/usr/bin/env python
import sys


import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag

def main():
    """
    NAME
       qqunf.py

    DESCRIPTION
       makes qq plot from input data against uniform distribution

    SYNTAX
       qqunf.py [command line options]

    OPTIONS
        -h help message
        -f FILE, specify file on command line

    """
    fmt,plot='svg',0
    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit
    elif '-f' in sys.argv: # ask for filename
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        input=f.readlines()
    Data=[]
    for line in input:
        line.replace('\n','')
        if '\t' in line:   # read in the data from standard input
            rec=line.split('\t') # split each line on space to get records
        else:
            rec=line.split() # split each line on space to get records
        Data.append(float(rec[0]))
    
#
    if len(Data) >=10: 
        QQ={'unf1':1}
        pmagplotlib.plot_init(QQ['unf1'],5,5)
        pmagplotlib.plotQQunf(QQ['unf1'],Data,'QQ-Uniform') # make plot
    else:
        print 'you need N> 10'
        sys.exit()
    pmagplotlib.drawFIGS(QQ) 
    files={}
    for key in QQ.keys():
        files[key]=key+'.'+fmt 
    if pmagplotlib.isServer:
        black     = '#000000'
        purple    = '#800080'
        titles={}
        titles['eq']='Equal Area Plot'
        EQ = pmagplotlib.addBorders(EQ,titles,black,purple)
        pmagplotlib.saveP(QQ,files)
    elif plot==1:
        files['qq']=file+'.'+fmt 
        pmagplotlib.saveP(QQ,files)
    else:
        ans=raw_input(" S[a]ve to save plot, [q]uit without saving:  ")
        if ans=="a": pmagplotlib.saveP(QQ,files)

if __name__ == "__main__":
    main()
