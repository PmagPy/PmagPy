#!/usr/bin/env python
import numpy
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
       di_tilt.py

    DESCRIPTION
       rotates geographic coordinate dec, inc data to stratigraphic
       coordinates using the dip and dip direction (strike+90, dip if dip to right of strike)

    INPUT FORMAT
        declination inclination dip_direction  dip

    SYNTAX
       di_tilt.py [-h][-i][-f FILE] [< filename ]

    OPTIONS
        -h prints help message and quits
        -i for interactive data entry
        -f FILE command line entry of file name
        -F OFILE, specify output file, default is standard output


    OUTPUT:
        declination inclination
 """
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        ofile=sys.argv[ind+1]
        out=open(ofile,'w')
        print ofile, ' opened for output'
    else: ofile=""
    if '-i' in sys.argv: # interactive flag
        while 1:
            try:
                Dec=float(raw_input("Declination: <cntl-D> to quit "))
            except:
                print "\n Good-bye\n"
                sys.exit()
            Inc=float(raw_input("Inclination: "))
            Dip_dir=float(raw_input("Dip direction: "))
            Dip=float(raw_input("Dip: "))
            print '%7.1f %7.1f'%(pmag.dotilt(Dec,Inc,Dip_dir,Dip))
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        data=numpy.loadtxt(file)
    else:
        data=numpy.loadtxt(sys.stdin,dtype=numpy.float) # read in the data from the datafile
    D,I=pmag.dotilt_V(data)
    for k in range(len(D)):
        if ofile=="":
            print '%7.1f %7.1f'%(D[k],I[k])
        else:
            out.write('%7.1f %7.1f\n'%(D[k],I[k]))

if __name__ == "__main__":
    main()
