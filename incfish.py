#!/usr/bin/env python
import pmag,sys
def main():
    """
    NAME
       incfish.py

    DESCRIPTION
       calculates fisher parameters from inc only data

    INPUT FORMAT
       takes inc data 

    SYNTAX
       incfish.py [-h][-i][-f FILE]  [< filename]

    OPTIONS
        -h prints help message and quits
        -i for interactive filename entry
        -f FILE, specify input file name
        < filename for reading from standard input
   
    OUTPUT
       mean inc,Fisher inc, N, R, k, a95

    NOTES
        takes the absolute value of inclinations (to take into account reversals),
        but returns gaussian mean if < 50.0, because of polarity ambiguity and 
        lack of bias.

    """
    inc=[]
    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit
    if '-i' in sys.argv: # ask for filename
        file=raw_input("Enter file name with inc data: ")
        f=open(file,'rU`')
        data=f.readlines()
    elif '-f' in sys.argv:
        dat=[]
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU`')
        data=f.readlines()
    else:
        data = sys.stdin.readlines()  # read from standard input
    for line in data:
       rec=line.split()
       inc.append(float(rec[0]))
    #
    #get doincfish to do the dirty work:
    fpars= pmag.doincfish(inc)
    outstring='%7.1f %7.1f  %i %8.1f %7.1f %7.1f'%(fpars['ginc'],fpars['inc'],fpars['n'],fpars['r'],fpars['k'],fpars['alpha95'])
    print outstring
main()
