#!/usr/bin/env python
import sys,pmag,pmagplotlib
def main():
    """
    NAME
       plotdi_a.py

    DESCRIPTION
       plots equal area projection  from dec inc data and fisher mean, cone of confidence

    INPUT FORMAT
       takes dec, inc, alpha95 as first three columns in space delimited file

    SYNTAX
       plotdi_a.py [-i][-f FILE] 

    OPTIONS
        -i for interactive filename entry
        -f FILE to read file name from command line

    """
    fmt='svg'
    if len(sys.argv) > 0:
        if '-h' in sys.argv: # check if help is needed
            print main.__doc__
            sys.exit() # graceful quit
        if '-i' in sys.argv: # ask for filename
            file=raw_input("Enter file name with dec, inc data: ")
            f=open(file,'rU')
            data=f.readlines()
        elif '-f' in sys.argv:
            ind=sys.argv.index('-f')
            file=sys.argv[ind+1]
            f=open(file,'rU')
            data=f.readlines()
        else:
            data=sys.stdin.readlines() # read in data from standard input
    DIs,Pars=[],[]
    for line in data:   # read in the data from standard input
        pars=[]
        rec=line.split() # split each line on space to get records
        DIs.append([float(rec[0]),float(rec[1])])
        pars.append(float(rec[0]))
        pars.append(float(rec[1]))
        pars.append(float(rec[2]))
        pars.append(float(rec[0]))
        isign=abs(float(rec[1]))/float(rec[1])
        pars.append(float(rec[1])-isign*90.) #Beta inc
        pars.append(float(rec[2])) # gamma
        pars.append(float(rec[0])+90.) # Beta dec
        pars.append(0.) #Beta inc
        Pars.append(pars)
#
    EQ={'eq':1} # make plot dictionary
    pmagplotlib.plot_init(EQ['eq'],5,5)
    title='Equal area projection'
    pmagplotlib.plotEQ(EQ['eq'],DIs,title)# plot directions
    for k in range(len(Pars)):
        pmagplotlib.plotELL(EQ['eq'],Pars[k],'b',0,1) # plot ellipses
    pmagplotlib.drawFIGS(EQ)
    files={}
    for key in EQ.keys():
        files[key]=key+'.'+fmt 
    if pmagplotlib.isServer:
        black     = '#000000'
        purple    = '#800080'
        titles={}
        titles['eq']='Equal Area Plot'
        EQ = pmagplotlib.addBorders(EQ,titles,black,purple)
        pmagplotlib.saveP(EQ,files)
    else:
        ans=raw_input(" S[a]ve to save plot, [q]uit, Return to continue:  ")
        if ans=="q": sys.exit()
        if ans=="a": 
            pmagplotlib.saveP(EQ,files) 
    #
main()
