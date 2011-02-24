#!/usr/bin/env python
import pmag,sys,math
def main():
    """
    NAME
        di_rot.py

    DESCRIPTION
        rotates set of directions to new coordinate system

    SYNTAX
        di_rot.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f specify input file, default is standard input
        -F specify output file, default is standard output
        -D D specify  Dec of new coordinate system, default is 0
        -I I specify  Inc of new coordinate system, default is 90
    INTPUT/OUTPUT
        dec  inc   [space delimited]  


    """
    D,I=0.,90.
    outfile=""
    infile=""
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        infile=sys.argv[ind+1]
        f=open(infile,'rU')
        data=f.readlines()
    else:
        data=sys.stdin.readlines()
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        outfile=sys.argv[ind+1]
        out=open(outfile,'w')
    if '-D' in sys.argv:
        ind=sys.argv.index('-D')
        D=float(sys.argv[ind+1])
    if '-I' in sys.argv:
        ind=sys.argv.index('-I')
        I=float(sys.argv[ind+1])
    Decs,Incs=[],[]
    for k in range(len(data)):
        line=data[k]
        if '\t' in line:
            di=line.split('\t') # split each line on space to get records
        else:
            di=line.split()
        drot,irot=pmag.dotilt(float(di[0]),float(di[1]),D-180.,90.-I)
        drot=drot-180.
        if drot<0:drot+=360.
        if outfile=="":
            print '%7.1f %7.1f ' % (drot,irot)
        elif k==len(data)-1:
            out.write('%7.1f %7.1f' % (drot,irot))
        else:
            out.write('%7.1f %7.1f \n ' % (drot,irot))
    if outfile!="":out.close()
main()
