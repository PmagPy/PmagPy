#!/usr/bin/env python
import pmag,sys
def spitout(line):
    dat=[]  # initialize list for  dec,inc,slat,slon
    line.replace('\t',' ')
    rec=line.split() # split each line on space to get records 
    for element in rec : # step through dec,inc, int
        dat.append(float(element)) # append floating point variable to dat list
    plong,plat,dp,dm=pmag.dia_vgp(dat[0],dat[1],0.,dat[2],dat[3])  # call dia_vgp function from pmag module
    print '%7.1f %7.1f'%(plong,plat) # print out returned stuff
    return plong,plat,dp,dm
def main():
    """
    NAME
        di_vgp.py
    DESCRIPTION
      converts declination/inclination to virtual geomagnetic pole
    
    SYNTAX
        di_vgp.py [-h] [-i] [-f FILE] [< filename]
    
    OPTIONS
        -h prints help message and quits
        -i interactive data entry
        -f FILE to specify file name on the command line
    
    INPUT 
      for file entry:
        D I SLAT SLON      
      where:
         D: declination
         I: inclination
         SLAT: site latitude (positive north)
         SLON: site longitude (positive east)
               
    OUTPUT
        PLON PLAT
        where:
             PLAT: pole latitude 
             PLON: pole longitude (positive east)
    """
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-i' in sys.argv: # if one is -i
        while 1:
            try:
                ans=raw_input("Input Declination: <cntrl-D to quit>  ")
                Dec=float(ans)  # assign input to Dec, after conversion to floating point
                ans=raw_input("Input Inclination:  ")
                Inc =float(ans)
                ans=raw_input("Input Site Latitude:  ")
                slat =float(ans)
                ans=raw_input("Input Site Longitude:  ")
                slong =float(ans)
                plong,plat,dp,dm=pmag.dia_vgp(Dec,Inc,0.,slat,slong)  # call dia_vgp function from pmag module
                print '%7.1f %7.1f'%(plong,plat) # print out returned stuff
            except:
                print "\n Good-bye\n"
                sys.exit()
            
    elif '-f' in sys.argv: # manual input of file name
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        input = f.readlines()  # read from standard input
        for line in input:   # read in the data (as string variable), line by line
            plong,plat,dp,dm= spitout(line)
    else:
        input = sys.stdin.readlines()  # read from standard input
        for line in input:   # read in the data (as string variable), line by line
            spitout(line)
main()
