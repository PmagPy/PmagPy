#!/usr/bin/env python
import sys


import pmagpy.pmag as pmag
import pylab
pylab.ion()

def main():
    """
    NAME
       plotxy_magic.py

    DESCRIPTION
       Makes simple X,Y plots 

    INPUT FORMAT
       Any MagIC formatted file

    SYNTAX
       plotxy_magic.py [command line options] 

    OPTIONS
        -h prints this help message
        -f FILE to set file name on command rec 
        -c col1 col2 specify columns names to plot
        -sym SYM SIZE specify symbol and size to plot: default is red dots
        -S   don't plot symbols
        -xlab XLAB
        -ylab YLAB
        -l  connect symbols with lines
        -b xmin xmax ymin ymax, sets bounds
#        -b [key:max:min,key:max:min,etc.] leave or min blank for no cutoff
    """
    col1,col2=0,1
    sym,size = 'ro',20
    xlab,ylab='',''
    lines=0
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
    else:
        '-f option is a required field'
        print main.__doc__
        sys.exit()
    if '-c' in sys.argv:
        ind=sys.argv.index('-c')
        col1=sys.argv[ind+1]
        col2=sys.argv[ind+2]
    else:
        'Column headers a required field'
        print main.__doc__
        sys.exit()
    if '-xlab' in sys.argv:
        ind=sys.argv.index('-xlab')
        xlab=sys.argv[ind+1]
    if '-ylab' in sys.argv:
        ind=sys.argv.index('-ylab')
        ylab=sys.argv[ind+1]
#    if '-b' in sys.argv:
#        ind=sys.argv.index('-b')
#        bounds=sys.argv[ind+1].split(',')
    if '-b' in sys.argv:
        ind=sys.argv.index('-b')
        xmin=float(sys.argv[ind+1])
        xmax=float(sys.argv[ind+2])
        ymin=float(sys.argv[ind+3])
        ymax=float(sys.argv[ind+4])
    if '-sym' in sys.argv:
        ind=sys.argv.index('-sym')
        sym=sys.argv[ind+1]
        size=int(sys.argv[ind+2])
    if '-l' in sys.argv: lines=1
    if '-S' in sys.argv: sym=''
    X,Y=[],[]
    data,file_type=pmag.magic_read(file)
    print file_type
    for rec in data:
        if col1 not in rec.keys() or col2 not in rec.keys():
            print col1,' and/or ',col2, ' not in file headers'
            print 'try again'
            sys.exit()
        if rec[col1]!='' and rec[col2]!='':
            skip=0
            if '-crit' in sys.argv:
                for crit in bounds:
                    crits=crit.split(':')
                    crit_key=crits[0]
                    crit_min=crits[1]
                    crit_max=crits[2]
                    if rec[crit_key]=="":
                        skip=1
                    else:
                        if crit_min!="" and float(rec[crit_key])<float(crit_min):skip=1
                        if crit_max!="" and float(rec[crit_key])>float(crit_min):skip=1
            if skip==0:
                X.append(float(rec[col1]))
                Y.append(float(rec[col2]))
    if len(X)==0:
            print col1,' and/or ',col2, ' have no data '
            print 'try again'
            sys.exit()
    else:
        print len(X),' data points'
    if sym!='':pylab.scatter(X,Y,c=sym[0],marker=sym[1],s=size)
    if xlab!='':pylab.xlabel(xlab)
    if ylab!='':pylab.ylabel(ylab)
    if lines==1:pylab.plot(X,Y,'k-')
    if '-b' in sys.argv:pylab.axis([xmin,xmax,ymin,ymax])
    pylab.draw()
    ans=raw_input("Press return to quit  ")
    sys.exit()

if __name__ == "__main__":
    main()
