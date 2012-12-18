#!/usr/bin/env python
import pmag,sys,numpy,exceptions
#
def main():
    """
    NAME
        igrf.py

    DESCRIPTION
        This program calculates igrf field values 
    using the routine of Malin and  Barraclough (1981) 
    based on d/igrfs from 1900 to 2010.
    Prior to 1900, it uses CALS3K.4 and prior to 2000BCE, it uses CALS10k-4b
    Calculates reference field vector at  specified location and time.

  
    SYNTAX
       igrf.py [-h] [-i] -f FILE  [< filename]

    OPTIONS:
       -h prints help message and quits
       -i for interactive data entry
       -f FILE  specify file name with input data 
       -F FILE  specify output file name
       -ages MIN MAX INCR: specify age minimum in years (+/- AD), maximum and increment, default is line by line
       -loc LAT LON;  specify location, default is line by line
       -alt ALT;  specify altitude in km, default is sealevel (0)
       -plt; make a plot of the time series
       -fmt [pdf,jpg,eps,svg]  specify format for output figure  (default is svg)
    
    INPUT FORMAT 
      interactive entry:
           date: decimal year
           alt:  altitude in km
           lat: positive north
           lon: positive east
       for file entry:
           space delimited string: date  alt   lat long

    OUTPUT  FORMAT
        Declination Inclination Intensity (nT) date alt lat long
    """
    plt,fmt=0,'svg'
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    if len(sys.argv)!=0 and '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        input=numpy.loadtxt(file)
    elif '-i' in sys.argv:
        while 1:
          try:
            line=[]
            line.append(float(raw_input("Decimal year: <cntrl-D to quit> ")))
            alt=raw_input("Elevation in km [0] ")
            if alt=="":alt="0"
            line.append(float(alt))
            line.append(float(raw_input("Latitude (positive north) ")))
            line.append(float(raw_input("Longitude (positive east) ")))
            x,y,z,f=pmag.doigrf(line[3]%360.,line[2],line[1],line[0])
            Dir=pmag.cart2dir((x,y,z))
            print '%7.1f %7.1f %8.0f'%(Dir[0],Dir[1],f)           
          except EOFError:
            print "\n Good-bye\n"
            sys.exit()
    elif '-ages' in sys.argv:
        ind=sys.argv.index('-ages')
        agemin=float(sys.argv[ind+1])
        agemax=float(sys.argv[ind+2])
        ageincr=float(sys.argv[ind+3])
        if '-loc' in sys.argv:
            ind=sys.argv.index('-loc')
            lat=float(sys.argv[ind+1])
            lon=float(sys.argv[ind+2])
        else: 
            print "must specify lat/lon if using age range option"
            sys.exit()
        if '-alt' in sys.argv:
            ind=sys.argv.index('-alt')
            alt=float(sys.argv[ind+1])
        else: alt=0
        ages=numpy.arange(agemin,agemax,ageincr)
        lats=numpy.ones(len(ages))*lat
        lons=numpy.ones(len(ages))*lon
        alts=numpy.ones(len(ages))*alt
        input=numpy.array([ages,alts,lats,lons]).transpose()
    else:
        input=numpy.loadtxt(sys.stdin,dtype=numpy.float)
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        outfile=sys.argv[ind+1]
        out=open(outfile,'w')
    else:outfile=""
    if '-plt' in sys.argv:
        plt=1
        import matplotlib
        matplotlib.use("TkAgg")
        import pylab
        pylab.ion()
        Ages,Decs,Incs,Ints=[],[],[],[]
    for line in input:
        x,y,z,f=pmag.doigrf(line[3]%360.,line[2],line[1],line[0])
        Dir=pmag.cart2dir((x,y,z))
        if outfile!="":
            out.write('%7.1f %7.1f %8.0f %7.1f %7.1f %7.1f %7.1f\n'%(Dir[0],Dir[1],f,line[0],line[1],line[2],line[3]))           
        elif plt:
            Ages.append(line[0])
            if Dir[0]>180: Dir[0]=Dir[0]-360.0
            Decs.append(Dir[0])
            Incs.append(Dir[1])
            Ints.append(f*1e-3)
        else:
            print '%7.1f %7.1f %8.0f %7.1f %7.1f %7.1f %7.1f'%(Dir[0],Dir[1],f,line[0],line[1],line[2],line[3])           
    if plt:
        fig=pylab.figure(num=1,figsize=(7,5))
        fig.add_subplot(311)
        pylab.plot(Ages,Decs)
        fig.add_subplot(312)
        pylab.plot(Ages,Incs)
        fig.add_subplot(313)
        pylab.plot(Ages,Ints)
        pylab.xlabel('Ages')
        pylab.draw()
        ans=raw_input("S[a]ve to save figure, <Return>  to quit  ")
        if ans=='a':
            pylab.savefig('igrf.'+fmt)
            print 'Figure saved as: ','igrf.'+fmt
        sys.exit()
main()

