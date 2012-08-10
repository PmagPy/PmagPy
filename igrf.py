#!/usr/bin/env python
import pmag,sys,exceptions,numpy
#
def main():
    """
    NAME
        igrf.py

    DESCRIPTION
        This program calculates igrf field values for years >1945 
    using the routine of Malin and  Barraclough (1981) 
    based on dgrfs from 1945 to 1990, 1995 and igrf 2005.
    Calculates reference field vector at  specified location and time.
    Uses appropriate IGRF or DGRF for date > 1945.
    For dates prior to 1945, the GUFM1 coefficients of Jackson et al. (2000) 
    are used.

  
    SYNTAX
       igrf.py [-h] [-i] -f FILE  [< filename]

    OPTIONS:
       -h prints help message and quits
       -i for interactive data entry
       -f FILE  specify file name with input data 
       -F FILE  specify output file name
    
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
                line=""
                line=line+raw_input("Decimal year: <cntrl-D to quit> ")
                alt=raw_input("Elevation in km [0] ")
                if alt=="":alt="0"
                line=line+" "+alt
                line=line+" "+raw_input("Latitude (positive north) ")
                line=line+" "+raw_input("Longitude (positive east) ")
                x,y,z,f=pmag.doigrf(line[3]%360.,line[2],line[1],line[0])
                Dir=pmag.cart2dir((x,y,z))
                print '%7.1f %7.1f %8.0f'%(Dir[0],Dir[1],f)           
            except:
                print "\nGood-bye\n"
                sys.exit()
    else:
        input=numpy.loadtxt(sys.stdin,dtype=numpy.float)
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        outfile=sys.argv[ind+1]
        out=open(outfile,'w')
    else:outfile=""
    for line in input:
        x,y,z,f=pmag.doigrf(line[3]%360.,line[2],line[1],line[0])
        Dir=pmag.cart2dir((x,y,z))
        if outfile!="":
            out.write('%7.1f %7.1f %8.0f %7.1f %7.1f %7.1f %7.1f\n'%(Dir[0],Dir[1],f,line[0],line[1],line[2],line[3]))           
        else:
            print '%7.1f %7.1f %8.0f %7.1f %7.1f %7.1f %7.1f'%(Dir[0],Dir[1],f,line[0],line[1],line[2],line[3])           
             
main()

