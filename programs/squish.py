#!/usr/bin/env python
import sys,numpy
#
def main():
    """
    NAME
        squish.py
    
    DESCRIPTION
      takes dec/inc data and "squishes" with specified flattening factor, flt
      using formula tan(Io)=flt*tan(If)
    
    INPUT 
           declination inclination 
    OUTPUT
           "squished" declincation inclination
    
    SYNTAX
        squish.py [command line options] [< filename]
    
    OPTIONS
        -h print help and quit
        -f FILE, input file
        -F FILE, output file
        -flt FLT, flattening factor [required]
    
    """
    ofile=""
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        ofile=sys.argv[ind+1]  
        out=open(ofile,'w')
    if '-flt' in sys.argv:
        ind=sys.argv.index('-flt')
        flt=float(sys.argv[ind+1])
    else:
        print main.__doc__
        sys.exit()  
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]  
        input=numpy.loadtxt(file)
    else:
        input=numpy.loadtxt(sys.stdin,dtype=numpy.float)
# read in inclination data
    for line in input: 
        dec=float(line[0])
        inc=float(line[1])*numpy.pi/180.
        tincnew=flt*numpy.tan(inc)
        incnew=numpy.arctan(tincnew)*180./numpy.pi
        if ofile=="":
            print '%7.1f %7.1f'% (dec,incnew)
        else:
            out.write('%7.1f %7.1f'% (dec,incnew)+'\n')
if __name__ == "__main__":
    main()

