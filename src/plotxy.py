#!/usr/bin/env python
import matplotlib,sys
matplotlib.use("TkAgg")
import pylab
pylab.ion()
import numpy
def main():
    """
    NAME
       plotXY.py

    DESCRIPTION
       Makes simple X,Y plots

    INPUT FORMAT
       X,Y data in columns

    SYNTAX
       plotxy.py [command line options] 

    OPTIONS
        -h prints this help message
        -f FILE to set file name on command line 
        -c col1 col2 specify columns to plot
        -xsig col3  specify xsigma if desired
        -ysig col4  specify xsigma if desired
        -b xmin xmax ymin ymax, sets bounds  
        -sym SYM SIZE specify symbol to plot: default is red dots, 10 pt
        -S   don't plot the symbols
        -xlab XLAB
        -ylab YLAB
        -l  connect symbols with lines
        -fmt [svg,png,pdf,eps] specify output format, default is svg
        -poly X   plot a degree X polynomial through the data
    """
    fmt='svg' 
    col1,col2=0,1
    sym,size = 'ro',50
    xlab,ylab='',''
    lines=0
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    if '-c' in sys.argv:
        ind=sys.argv.index('-c')
        col1=int(sys.argv[ind+1])-1
        col2=int(sys.argv[ind+2])-1
    if '-xsig' in sys.argv:
        ind=sys.argv.index('-xsig')
        col3=int(sys.argv[ind+1])-1
    if '-ysig' in sys.argv:
        ind=sys.argv.index('-ysig')
        col4=int(sys.argv[ind+1])-1
    if '-xlab' in sys.argv:
        ind=sys.argv.index('-xlab')
        xlab=sys.argv[ind+1]
    if '-ylab' in sys.argv:
        ind=sys.argv.index('-ylab')
        ylab=sys.argv[ind+1]
    if '-b' in sys.argv:
        ind=sys.argv.index('-b')
        xmin=float(sys.argv[ind+1])
        xmax=float(sys.argv[ind+2])
        ymin=float(sys.argv[ind+3])
        ymax=float(sys.argv[ind+4])
    if '-poly' in sys.argv:
        ind=sys.argv.index('-poly')
        degr=sys.argv[ind+1]
    if '-sym' in sys.argv:
        ind=sys.argv.index('-sym')
        sym=sys.argv[ind+1]
        size=int(sys.argv[ind+2])
    if '-l' in sys.argv: lines=1
    if '-S' in sys.argv: sym=''
    X,Y=[],[]
    Xerrs,Yerrs=[],[]
    f=open(file,'rU')
    data=f.readlines()
    for line in data:
        line.replace('\n','')
        line.replace('\t',' ')
        rec=line.split()
        X.append(float(rec[col1]))
        Y.append(float(rec[col2]))
        if '-xsig' in sys.argv:Xerrs.append(float(rec[col3]))
        if '-ysig' in sys.argv:Yerrs.append(float(rec[col4]))
    if '-poly' in sys.argv:
          coeffs=numpy.polyfit(X,Y,degr)
          polynomial=numpy.poly1d(coeffs)
          xs=numpy.linspace(numpy.min(X),numpy.max(X),10)
          ys=polynomial(xs)
          pylab.plot(xs,ys)
          print polynomial
    if sym!='':pylab.scatter(X,Y,marker=sym[1],c=sym[0],s=size)
    if '-xsig' in sys.argv and '-ysig' in sys.argv:
        pylab.errorbar(X,Y,xerr=Xerrs,yerr=Yerrs,fmt=None)
    if '-xsig' in sys.argv and '-ysig' not in sys.argv:
        pylab.errorbar(X,Y,xerr=Xerrs,fmt=None)
    if '-xsig' not in sys.argv and '-ysig' in sys.argv:
        pylab.errorbar(X,Y,yerr=Yerrs,fmt=None)
    if xlab!='':pylab.xlabel(xlab)
    if ylab!='':pylab.ylabel(ylab)
    if lines==1:pylab.plot(X,Y,'k-')
    if '-b' in sys.argv:pylab.axis([xmin,xmax,ymin,ymax])
    pylab.draw()
    ans=raw_input("S[a]ve to save figure, <Return>  to quit  ")
    if ans=='a':
        pylab.savefig('plotXY.'+fmt) 
        print 'Figure saved as: ','plotXY.'+fmt
    sys.exit()
main()
