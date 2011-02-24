#!/usr/bin/env python
import pmag,sys
def spitout(line):
    dat=[]  # initialize list for  dec,inc,slat,slon
    rec =line.split() # split the data on a space into columns
    for element in rec : # step through dec,inc, int
        dat.append(float(element)) # append floating point variable to dat list
    plong,plat,dp,dm=pmag.dia_vgp(dat[0],dat[1],dat[2],dat[3],dat[4])  # call dia_vgp function from pmag module
    print '%7.1f %7.1f %7.1f %7.1f'%(plong,plat,dp,dm) # print out returned stuff
def main():
    """
    NAME
        dia_vgp.py
    DESCRIPTION
      converts declinationi inclination alpha95 to virtual geomagnetic pole, dp and dm
    
    SYNTAX
        dia_vgp.py [-h] [-i] [-f FILE] [< filename]
    
    OPTIONS
        -h prints help message and quits
        -i interactive data entry
        -f FILE to specify file name on the command line
    
    INPUT 
      for file entry:
        D I A95 SLAT SLON      
      where:
         D: declination
         I: inclination
         A95: alpha_95
         SLAT: site latitude (positive north)
         SLON: site longitude (positive east)
               
    OUTPUT
        PLON PLAT DP DM
        where:
             PLAT: pole latitude 
             PLON: pole longitude (positive east)
             DP: 95% confindence angle in parallel 
             DM: 95% confindence angle in meridian 
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
                ans=raw_input("Input Alpha 95:  ")
                a95 =float(ans)
                ans=raw_input("Input Site Latitude:  ")
                slat =float(ans)
                ans=raw_input("Input Site Longitude:  ")
                slong =float(ans)
                plong,plat,dp,dm=pmag.dia_vgp(Dec,Inc,a95,slat,slong)  # call dia_vgp function from pmag module
                print '%7.1f %7.1f %7.1f %7.1f'%(plong,plat,dp,dm) # print out returned stuff
            except:
                print "\n Good-bye\n"
                sys.exit()
            
    elif '-f' in sys.argv: # manual input of file name
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        input = f.readlines()  # read from standard input
        for line in input:   # read in the data (as string variable), line by line
            spitout(line)
    else:
        input = sys.stdin.readlines()  # read from standard input
        for line in input:   # read in the data (as string variable), line by line
            spitout(line)
main()
