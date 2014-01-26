#!/usr/bin/env python
import pmag,sys,exceptions,numpy
def main():
    """
    NAME
       di_geo.py

    DESCRIPTION
       rotates specimen coordinate dec, inc data to geographic
       coordinates using the azimuth and plunge of the X direction

    INPUT FORMAT
        declination inclination azimuth plunge

    SYNTAX
       di_geo.py [-h][-i][-f FILE] [< filename ]

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
                Dec=float(raw_input("Declination: <cntrl-D> to quit  "))
            except EOFError:
                print "\n Good-bye\n"
                sys.exit()
            Inc=float(raw_input("Inclination: "))
            Az=float(raw_input("Azimuth: "))
            Pl=float(raw_input("Plunge: "))
            print '%7.1f %7.1f'%(pmag.dogeo(Dec,Inc,Az,Pl))
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        data=numpy.loadtxt(file)
    else:
        data=numpy.loadtxt(sys.stdin,dtype=numpy.float) # read in the data from the datafile
    D,I=pmag.dogeo_V(data)
    for k in range(len(D)):
        if ofile=="":
            print '%7.1f %7.1f'%(D[k],I[k])
        else:
            out.write('%7.1f %7.1f\n'%(D[k],I[k]))
main()
