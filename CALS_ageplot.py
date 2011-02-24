#!/usr/bin/env python
import pmag,sys,exceptions,matplotlib
matplotlib.use("TkAgg")
import pylab
pylab.ion()
def main():
    """
    NAME 
        CALS_ageplot.py

    DESCRIPTION
        plots CALS output files versus age

    SYNTAX
        CALS_ageplot.py [command line optins]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file 
        -a min max [in kyr] age range to plot
     DEFAULTS:
         CALS file: output.dat
    """
    dir_path="./"
    if '-WD' in sys.argv: 
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    input_file=dir_path+'/output.dat'
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        input_file=dir_path+'/'+sys.argv[ind+1]
    amin,amax=-1,7000
    if '-a' in sys.argv:
        ind=sys.argv.index('-a')
        amin=float(sys.argv[ind+1])
        amax=float(sys.argv[ind+2])
    #
    #
    # get data read in
    input=open(input_file).readlines()
    Ages,Decs,Incs,Ints=[],[],[],[]
    xlab="Age (BP)"
    # collect the data for plotting declination
    maxInt=-1000
    for line in input[1:]:
        rec=line.split()
        age=1950-int(rec[0])
        if age>amin and age<amax:
            Ages.append(-age)
            Decs.append(float(rec[4]))
            Incs.append(float(rec[3]))
            Ints.append(1e-3*float(rec[5]))
            if Ints[-1]>maxInt:maxInt=Ints[-1]
    if amin==-1:
        amin,amax=Ages[0],Ages[-1]
    if len(Decs)>0 and len(Ages)>0:
        for pow in range(-10,10):
            if maxInt*10**pow>1:break
        for k in range(len(Ints)):
            Ints[k]=Ints[k]*10**pow
        pylab.figure(1,figsize=(10,8))
        pylab.subplot(1,3,1)
        pylab.plot(Decs,Ages,'ro',Decs,Ages,'k') 
#        pylab.axis([0,360,amax,amin])
        pylab.xlabel('Declination')
        pylab.ylabel('Age BP')
        pylab.subplot(1,3,2)
        pylab.plot(Incs,Ages,'bo',Incs,Ages,'k') 
#        pylab.axis([-90,90,amax,amin])
        pylab.xlabel('Inclination')
        pylab.ylabel('')
        pylab.subplot(1,3,3)
        pylab.plot(Ints,Ages,'ko',Ints,Ages,'k') 
#        pylab.axis([0,maxInt*10**pow+.1,dmax,dmin])
        pylab.xlabel('%s %i %s'%('Intensity (x 10^',pow,' Am^2)'))
        pylab.draw()
        ans=raw_input("Press return to quit  ")
        sys.exit()
    else:
        print "No data points met your criteria - try again"
main()
