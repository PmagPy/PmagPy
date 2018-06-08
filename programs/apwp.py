#!/usr/bin/env python
from __future__ import print_function
from builtins import input
from builtins import range
import sys
import pmagpy.pmag as pmag

def spitout(data):
    pole_lat,pole_lon=pmag.bc02(data)
    dec,inc=pmag.vgp_di(pole_lat,pole_lon,data[1],data[2])
    paleo_lat=pmag.magnetic_lat(inc)
    return ' %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f\n' %(data[3],paleo_lat,dec,inc,pole_lat,pole_lon)
def main():
    """
    NAME
        apwp.py

    DESCRIPTION
        returns predicted paleolatitudes, directions and pole latitude/longitude
        from apparent polar wander paths of Besse and Courtillot (2002).

    SYNTAX
        apwp.py [command line options][< filename]

    OPTIONS
        -h prints help message and quits
        -i allows interactive data entry
        f file: read plate, lat, lon, age data from file
        -F output_file: write output to output_file 
        -P [NA, SA, AF, IN, EU, AU, ANT, GL] plate
        -lat LAT specify present latitude (positive = North; negative=South)
        -lon LON specify present longitude (positive = East, negative=West)
        -age AGE specify Age in Ma

     Note:  must have all -P, -lat, -lon, -age or none.

     OUTPUT
        Age  Paleolat.  Dec.  Inc.  Pole_lat.  Pole_Long. 

    """
    infile,outfile,data,indata="","",[],[]
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        outfile=sys.argv[ind+1]
        out=open(outfile,'w')
    if '-i' in sys.argv:
        print("Welcome to paleolatitude calculator\n")
        while 1:
            data=[]
            print("pick a plate: NA, SA, AF, IN, EU, AU, ANT, GL \n   cntl-D to quit")
            try:
                plate=input("Plate\n").upper()
            except:
                print("Goodbye \n")
                sys.exit()
            lat=float(input( "Site latitude\n"))
            lon=float(input(" Site longitude\n"))
            age=float(input(" Age\n"))
            data=[plate,lat,lon,age]
            print("Age  Paleolat.  Dec.  Inc.  Pole_lat.  Pole_Long.")
            print(spitout(data))
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        infile=sys.argv[ind+1]
        f=open(infile,'r')
        inp=f.readlines()
    elif '-P' in sys.argv:
        ind=sys.argv.index('-P')
        plate=sys.argv[ind+1].upper()
        if '-lat' in sys.argv:
            ind=sys.argv.index('-lat')
            lat=float(sys.argv[ind+1])
        else:
            print(main.__doc__)
            sys.exit()
        if '-lon' in sys.argv:
            ind=sys.argv.index('-lon')
            lon=float(sys.argv[ind+1])
        else:
            print(main.__doc__)
            sys.exit()
        if '-age' in sys.argv:
            ind=sys.argv.index('-age')
            age=float(sys.argv[ind+1])
        else:
            print(main.__doc__)
            sys.exit()
        data=[plate,lat,lon,age]
        outstring=spitout(data)
        if outfile=="": 
            print("Age  Paleolat.  Dec.  Inc.  Pole_lat.  Pole_Long.")
            print(outstring)
        else:
            out.write(outstring)
        sys.exit()
    else:
        inp=sys.stdin.readlines() # read from standard input
    if len(inp)>0:
      for line in inp:
        data=[]
        rec=line.split()
        data.append(rec[0])
        for k in range(1,4): data.append(float(rec[k]))
        indata.append(data) 
      if len(indata)>0:
        for line in indata:
            outstring=spitout(line)
            if outfile=="": 
                print(outstring)
            else:
                out.write(outstring)
    else:
       print('no input data')
       sys.exit()

if __name__ == "__main__":
    main()
