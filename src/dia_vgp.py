#!/usr/bin/env python
import pmag,sys

def spitout(*input):
    output = []
    if len(input) > 1:
        (dec,inc,a95,slat,slon) = (input)
        output = pmag.dia_vgp(dec,inc,a95,slat,slon)
    else:
        input = input[0]
        output = pmag.dia_vgp(input)
    return printout(output)

def printout(output): # print out returned stuff
    if len(output) > 1:
        if isinstance(output[0],list):        
            for i in range(len(output[0])):
                print '%7.1f %7.1f %7.1f %7.1f'%(output[0][i],output[1][i],output[2][i],output[3][i])
        else:
            print '%7.1f %7.1f %7.1f %7.1f'%(output[0],output[1],output[2],output[3])     

def main():
    """
    NAME
        dia_vgp.py
    DESCRIPTION
      converts declination inclination alpha95 to virtual geomagnetic pole, dp and dm
    
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
             DP: 95% confidence angle in parallel 
             DM: 95% confidence angle in meridian 
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
                spitout(Dec,Inc,a95,slat,slong)  # call dia_vgp function from pmag module
                print '%7.1f %7.1f %7.1f %7.1f'%(plong,plat,dp,dm) # print out returned stuff
            except:
                print "\n Good-bye\n"
                sys.exit()
            
    elif '-f' in sys.argv: # manual input of file name
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        inlist  = []
        for line in f.readlines():
            inlist.append([])
            # loop over the elements, split by whitespace
            for el in line.split():
                inlist[-1].append(float(el))
        spitout(inlist)

    else:
        input = sys.stdin.readlines()  # read from standard input
        inlist  = []
        for line in input:   # read in the data (as string variable), line by line
            inlist.append([])
            # loop over the elements, split by whitespace
            for el in line.split():
                inlist[-1].append(float(el))
        spitout(inlist)
main()