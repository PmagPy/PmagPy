#!/usr/bin/env python
import sys


import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag

def main():
    """
    NAME
       zeq.py
  
    DESCRIPTION
       plots demagnetization data. The equal area projection has the X direction (usually North in geographic coordinates)
          to the top.  The red line is the X axis of the Zijderveld diagram.  Solid symbols are lower hemisphere. 
          The solid (open) symbols in the Zijderveld diagram are X,Y (X,Z) pairs.  The demagnetization diagram plots the
          fractional remanence remaining after each step. The green line is the fraction of the total remaence removed 
          between each step.        

    INPUT FORMAT
       takes specimen_name treatment intensity declination inclination  in space
 delimited file

    SYNTAX
        zeq.py [command line options

    OPTIONS
        -f FILE for reading from command line
        -u [mT,C] specify units of mT OR C, default is unscaled
    """
    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit
    else:
        if '-f' in sys.argv:
            ind=sys.argv.index('-f')
            file=sys.argv[ind+1]
        else:
            print main.__doc__
            sys.exit()
        if '-u' in sys.argv:
            ind=sys.argv.index('-u')
            units=sys.argv[ind+1]
            if units=="C":SIunits="K"
            if units=="mT":SIunits="T"
        else:
            units="U"
            SIunits="U"
    f=open(file,'rU')
    data=f.readlines()
#
    datablock= [] # set up list for data
    fmt='svg' # default image format
    s="" # initialize specimen name
    angle=0.
    for line in data:   # read in the data from standard input
        rec=line.split() # split each line on space to get records
        if angle=="":angle=float(rec[3])
        if s=="":s=rec[0]
        if units=='mT':datablock.append([float(rec[1])*1e-3,float(rec[3]),float(rec[4]),1e-3*float(rec[2]),'','g']) # treatment, dec, inc, int # convert to T and Am^2 (assume emu)
        if units=='C':datablock.append([float(rec[1])+273.,float(rec[3]),float(rec[4]),1e-3*float(rec[2]),'','g']) # treatment, dec, inc, int, convert to K and Am^2, assume emu
        if units=='U':datablock.append([float(rec[1]),float(rec[3]),float(rec[4]),float(rec[2]),'','g']) # treatment, dec, inc, int, using unscaled units 
# define figure numbers in a dictionary for equal area, zijderveld,  
#  and intensity vs. demagnetiztion step respectively
    ZED={}
    ZED['eqarea'],ZED['zijd'],  ZED['demag']=1,2,3 
    pmagplotlib.plot_init(ZED['eqarea'],5,5) # initialize plots
    pmagplotlib.plot_init(ZED['zijd'],5,5)
    pmagplotlib.plot_init(ZED['demag'],5,5)
#
#
    pmagplotlib.plotZED(ZED,datablock,angle,s,SIunits) # plot the data
    pmagplotlib.drawFIGS(ZED)
    while 1:

#
# print out data for this sample to screen
#
        recnum=0
        for plotrec in datablock:
            if units=='mT':print '%i  %7.1f %8.3e %7.1f %7.1f ' % (recnum,plotrec[0]*1e3,plotrec[3],plotrec[1],plotrec[2])
            if units=='C':print '%i  %7.1f %8.3e %7.1f %7.1f ' % (recnum,plotrec[0]-273.,plotrec[3],plotrec[1],plotrec[2])
            if units=='U':print '%i  %7.1f %8.3e %7.1f %7.1f ' % (recnum,plotrec[0],plotrec[3],plotrec[1],plotrec[2])
            recnum += 1
        end_pca=len(datablock)-1 # initialize end_pca, beg_pca to first and last measurement
        beg_pca=0
        ans=raw_input(" s[a]ve plot, [b]ounds for pca and calculate, change [h]orizontal projection angle, [q]uit:   ")
        if ans =='q':
            sys.exit() 
        if  ans=='a':
            files={}
            for key in ZED.keys():
                files[key]=s+'_'+key+'.'+fmt 
            pmagplotlib.saveP(ZED,files)
        if ans=='h':
            angle=float(raw_input(" Declination to project onto horizontal axis? "))
            pmagplotlib.plotZED(ZED,datablock,angle,s,SIunits) # plot the data
        if ans=='b':
            GoOn=0
            while GoOn==0: # keep going until reasonable bounds are set
                print 'Enter index of first point for pca: ','[',beg_pca,']'
                answer=raw_input('return to keep default  ')
                if answer != "":beg_pca=int(answer)
                print 'Enter index  of last point for pca: ','[',end_pca,']'
                answer=raw_input('return to keep default  ')
                if answer != "":
                    end_pca=int(answer) 
                if beg_pca >=0 and beg_pca<=len(datablock)-2 and end_pca>0 and end_pca<len(datablock): 
                    GoOn=1
                else:
                    print "Bad entry of indices - try again"
                    end_pca=len(datablock)-1
                    beg_pca=0
            GoOn=0
            while GoOn==0:
                ct=raw_input('Enter Calculation Type: best-fit line,  plane or fisher mean [l]/p/f :  ' )
                if ct=="" or ct=="l": 
                    calculation_type="DE-BFL"
                    GoOn=1 # all good
                elif ct=='p':
                    calculation_type="DE-BFP"
                    GoOn=1 # all good
                elif ct=='f':
                    calculation_type="DE-FM"
                    GoOn=1 # all good
                else: 
                    print "bad entry of calculation type: try again. " # keep going
            pmagplotlib.plotZED(ZED,datablock,angle,s,SIunits) # plot the data
            mpars=pmag.domean(datablock,beg_pca,end_pca,calculation_type) # get best-fit direction/great circle
            pmagplotlib.plotDir(ZED,mpars,datablock,angle) # plot the best-fit direction/great circle
            print 'Specimen, calc_type, N, min, max, MAD, dec, inc'
            if units=='mT':print '%s %s %i  %6.2f %6.2f %6.1f %7.1f %7.1f' % (s,calculation_type,mpars["specimen_n"],mpars["measurement_step_min"]*1e3,mpars["measurement_step_max"]*1e3,mpars["specimen_mad"],mpars["specimen_dec"],mpars["specimen_inc"])
            if units=='C':print '%s %s %i  %6.2f %6.2f %6.1f %7.1f %7.1f' % (s,calculation_type,mpars["specimen_n"],mpars["measurement_step_min"]-273,mpars["measurement_step_max"]-273,mpars["specimen_mad"],mpars["specimen_dec"],mpars["specimen_inc"])
            if units=='U':print '%s %s %i  %6.2f %6.2f %6.1f %7.1f %7.1f' % (s,calculation_type,mpars["specimen_n"],mpars["measurement_step_min"],mpars["measurement_step_max"],mpars["specimen_mad"],mpars["specimen_dec"],mpars["specimen_inc"])

if __name__ == "__main__":
    main()  # run the main program
