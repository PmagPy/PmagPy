#!/usr/bin/env python
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pmagpy.pmagplotlib as pmagplotlib

def main():
    """
    NAME
       qqplot.py

    DESCRIPTION
       makes qq plot of input data  against a Normal distribution.  
       

    INPUT FORMAT
       takes real numbers in single column
   
    SYNTAX
       qqplot.py [-h][-i][-f FILE]

    OPTIONS
        -f FILE, specify file on command line
        -fmt [png,svg,jpg,eps] set plot output format [default is svg]
        -sav saves and quits

    OUTPUT
         calculates the K-S D and the D expected for a normal distribution 
         when D<Dc,  distribution is normal (at 95% level of confidence).

    """
    fmt,plot='svg',0
    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit
    if '-sav' in sys.argv: plot=1
    if '-fmt' in sys.argv: 
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    if '-f' in sys.argv: # ask for filename
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        data=f.readlines()
    X= [] # set up list for data
    for line in data:   # read in the data from standard input
        rec=line.split() # split each line on space to get records
        X.append(float(rec[0])) # append data to X
#
    QQ={'qq':1}
    pmagplotlib.plot_init(QQ['qq'],5,5)
    pmagplotlib.plotQQnorm(QQ['qq'],X,'Q-Q Plot') # make plot
    if plot==0:
        pmagplotlib.drawFIGS(QQ)
    files={}
    for key in QQ.keys():
        files[key]=key+'.'+fmt 
    if pmagplotlib.isServer:
        black     = '#000000'
        purple    = '#800080'
        titles={}
        titles['eq']='Q-Q Plot'
        QQ = pmagplotlib.addBorders(EQ,titles,black,purple)
        pmagplotlib.saveP(QQ,files)
    elif plot==0:
        ans=raw_input(" S[a]ve to save plot, [q]uit without saving:  ")
        if ans=="a": 
            pmagplotlib.saveP(QQ,files) 
    else:
        pmagplotlib.saveP(QQ,files) 
    #

if __name__ == "__main__":
    main()

