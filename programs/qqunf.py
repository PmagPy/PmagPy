#!/usr/bin/env python
from __future__ import print_function
from builtins import input
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
        print(main.__doc__)
        sys.exit() # graceful quit
    elif '-f' in sys.argv: # ask for filename
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'r')
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
        pmagplotlib.plot_qq_unf(QQ['unf1'],Data,'QQ-Uniform') # make plot
    else:
        print('you need N> 10')
        sys.exit()
    pmagplotlib.draw_figs(QQ) 
    files={}
    for key in list(QQ.keys()):
        files[key]=key+'.'+fmt 
    if pmagplotlib.isServer:
        black     = '#000000'
        purple    = '#800080'
        titles={}
        titles['eq']='Equal Area Plot'
        EQ = pmagplotlib.add_borders(EQ,titles,black,purple)
        pmagplotlib.save_plots(QQ,files)
    elif plot==1:
        files['qq']=file+'.'+fmt 
        pmagplotlib.save_plots(QQ,files)
    else:
        ans=input(" S[a]ve to save plot, [q]uit without saving:  ")
        if ans=="a": pmagplotlib.save_plots(QQ,files)

if __name__ == "__main__":
    main()
