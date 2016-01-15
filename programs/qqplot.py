#!/usr/bin/env python
import sys,pmagplotlib
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
        -i for interactive filename entry
        -f FILE, specify file on command line

    OUTPUT
         calculates the K-S D and the D expected for a normal distribution 
         when D<Dc,  distribution is normal (at 95% level of confidence).

    """
    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit
    if '-i' in sys.argv: # ask for filename
        file=raw_input("Enter file name with dec, inc data: ")
        f=open(file,'rU')
        data=f.readlines()
    elif '-f' in sys.argv: # ask for filename
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
    pmagplotlib.drawFIGS(QQ)
    files,fmt={},'svg'
    for key in QQ.keys():
        files[key]=key+'.'+fmt 
    if pmagplotlib.isServer:
        black     = '#000000'
        purple    = '#800080'
        titles={}
        titles['eq']='Q-Q Plot'
        QQ = pmagplotlib.addBorders(EQ,titles,black,purple)
        pmagplotlib.saveP(QQ,files)
    else:
        ans=raw_input(" S[a]ve to save plot, [q]uit without saving:  ")
        if ans=="a": pmagplotlib.saveP(QQ,files) 
    #
main()

