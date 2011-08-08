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
                print '%7.1f %7.1f'%(output[0][i],output[1][i])
        else:
            print '%7.1f %7.1f'%(output[0],output[1]) 

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
                ans   = raw_input("Input Declination: <cntrl-D to quit>  ")
                Dec   = float(ans)  # assign input to Dec, after conversion to floating point
                ans   = raw_input("Input Inclination:  ")
                Inc   = float(ans)
                ans   = raw_input("Input Site Latitude:  ")
                slat  = float(ans)
                ans   = raw_input("Input Site Longitude:  ")
                slong = float(ans)                

                spitout(Dec,Inc,0.,slat,slong)
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
            i = 0
            # loop over the elements, split by whitespace
            for el in line.split():
                i = i+1
                if i%3 == 0: # append '0' for a95
                    inlist[-1].append(float(0))
                inlist[-1].append(float(el))
        spitout(inlist)
    else:
        input = sys.stdin.readlines()  # read from standard input
        inlist  = []
        for line in input:   # read in the data (as string variable), line by line
            inlist.append([])
            i = 0
            # loop over the elements, split by whitespace
            for el in line.split():
                i = i+1
                if i%3 == 0: # append '0' for a95
                    inlist[-1].append(float(0))
                inlist[-1].append(float(el))
        spitout(inlist)
main()
