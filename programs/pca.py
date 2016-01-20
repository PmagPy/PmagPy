#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
       pca.py

    DESCRIPTION
       calculates best-fit line/plane through demagnetization data

    INPUT FORMAT
       takes specimen_name treatment intensity declination inclination  in space delimited file

    SYNTAX
       pca.py [command line options][< filename]

    OPTIONS
        -h prints help and quits
        -f FILE
        -dir [L,P,F][BEG][END] specify direction type, beginning and end
          (L:line, P:plane or F:fisher mean of unit vectors)
          BEG: first step (NRM = step zero)
          END: last step (NRM = step zero)
        < filename for reading from standard input
    OUTPUT:
        specimen_name calculation_type N beg end MAD dec inc
        if calculation_type is 'p', dec and inc are pole to plane, otherwise, best-fit direction

    EXAMPLE:
        pca.py -dir L  1 5 <ex3.3
        will calculate best-fit line through demagnetization steps 1 and 5 from file ex5.1

    """
    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        data=f.readlines()
    else:
        data=sys.stdin.readlines() # read in data from standard input
    if '-dir' in sys.argv: # 
        ind=sys.argv.index('-dir')
        typ=sys.argv[ind+1]
        if typ=='L': calculation_type='DE-BFL'
        if typ=='P': calculation_type='DE-BFP'
        if typ=='F': calculation_type='DE-FM'
        beg_pca = int(sys.argv[ind+2])
        end_pca = int(sys.argv[ind+3])
#
#
    datablock= [] # set up list for data
    s=""
    ind=0
    for line in data:   # read in the data from standard input
        rec=line.split() # split each line on space to get records
        if s=="":
            s=rec[0]
            print s, calculation_type
        print ind,rec[1],rec[3],rec[4],rec[2]
        ind+=1
        datablock.append([float(rec[1]),float(rec[3]),float(rec[4]),float(rec[2]),'0']) # treatment,dec,inc,int,dummy
    mpars=pmag.domean(datablock,beg_pca,end_pca,calculation_type)
    if calculation_type=="DE-FM":
        print '%s %s %i  %6.2f %6.2f %6.1f %7.1f %7.1f' % (s,calculation_type,mpars["specimen_n"],mpars["measurement_step_min"],mpars["measurement_step_max"],mpars["specimen_a95"],mpars["specimen_dec"],mpars["specimen_inc"])
    else:
        print '%s %s %i  %6.2f %6.2f %6.1f %7.1f %7.1f' % (s,calculation_type,mpars["specimen_n"],mpars["measurement_step_min"],mpars["measurement_step_max"],mpars["specimen_mad"],mpars["specimen_dec"],mpars["specimen_inc"])

if __name__ == "__main__":
    main()
