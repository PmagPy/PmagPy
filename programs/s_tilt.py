#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
        s_tilt.py

    DESCRIPTION
       rotates .s data into stratigraphic coordinates using strike and dip
  
    SYNTAX
        s_tilt.py [-h][options]

    OPTIONS
        -h prints help message and quits
        -i allows interactive entry of file name
        -f file specifies filename on command line
        -F FILE specifies output filename on command line
        < filename, reads from standard input (Unix like operating systems only)

    INPUT      
        x11 x22 x33 x12 x23 x13 strike dip
   
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
        bed_az,bed_dip=float(rec[6])+90.,float(rec[7]) #dip direction,dip
#
# get eigenvectors
#
        s_rot=pmag.dostilt(s,bed_az,bed_dip)
        outstring=""
        for s in s_rot:outstring+='%10.8f '%(s)
        if ofile == "":
            print outstring
        else:
            out.write(outstring+"\n")
#
if __name__ == "__main__":
    main()
