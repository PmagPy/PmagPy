#!/usr/bin/env python
import pmag,sys,exceptions
def spitout(line):
    rec=line.split()  # split each line on the spaces
    Dec=float(rec[0]) # assign first column to dec - convert to floating point
    Inc=float(rec[1]) # 2nd column => inc
    Az=float(rec[2])  # 3rd column => azimuth
    Pl=float(rec[3]) # 4th column => plunge
    dec,inc=pmag.dogeo(Dec,Inc,Az,Pl) # call dogeo from pmag module
    print '%7.1f %7.1f '%(dec,inc)
    return dec,inc

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
         otherwise put data in input format in space delimited file
    OUTPUT:
        declination inclination
 """
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
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
            #print pmag.dogeo(Dec,Inc,Az,Pl)
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        data=f.readlines()
    else:
        data=sys.stdin.readlines() # read in the data from the datafile
    for line in data: # step through line by line
        dec,inc=spitout(line)
main()
