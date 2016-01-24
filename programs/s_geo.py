#!/usr/bin/env python
#
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
        s_geo.py

    DESCRIPTION
       rotates .s data into geographic coordinates using azimuth and plunge
  
    SYNTAX
        s_geo.py [-h][options]

    OPTIONS
        -h prints help message and quits
        -i allows interactive entry of file name
        -f file specifies filename on command line
        -F FILE specifies output file on command line
        < filename, reads from standard input (Unix like operating systems only)

    INPUT      
        x11 x22 x33 x12 x23 x13 az pl
   
    OUTPUT
        x11 x22 x33 x12 x23 x13
    """
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
# read in the data
    elif '-i' in sys.argv:
        file=raw_input("Enter filename for processing: ")
        f=open(file,'rU')
        data=f.readlines()
        f.close()
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1] 
        f=open(file,'rU')
        data=f.readlines()
        f.close()
    else: 
        data=sys.stdin.readlines()
    ofile = ""
    if '-F' in sys.argv:
        ind = sys.argv.index('-F')
        ofile= sys.argv[ind+1]
        out = open(ofile, 'w + a')
    for line in data:
        s=[]
        rec=line.split()
        for i in range(6):
            s.append(float(rec[i]))
        az,pl=float(rec[6]),float(rec[7])
        s_rot=pmag.dosgeo(s,az,pl)
        outstring=""
        for s in s_rot:outstring+='%10.8f '%(s)
        if ofile == "":
            print outstring
        else:
            out.write(outstring+"\n")
#
if __name__ == "__main__":
    main()
