#!/usr/bin/env python
from __future__ import print_function
from builtins import input
from builtins import str
from builtins import range
import sys
import pmagpy.pmag as pmag

def main():
    """
    Welcome to the thellier-thellier experiment automatic chart maker.   
    Please select desired step interval and upper bound for which it is valid.
    e.g.,   
    50 
    500
    10 
    600
    
    a blank entry signals the end of data entry.
    which would generate steps with 50 degree intervals up to 500, followed by 10 degree intervals up to 600.   
    
    chart is stored in:  chart.txt
    """
    print(main.__doc__)
    if '-h' in sys.argv:sys.exit() 
    cont,Int,Top=1,[],[]
    while cont==1:
        try: 
            Int.append(int(input(" Enter desired treatment step interval: <return> to quit ")))
            Top.append(int(input(" Enter upper bound for this interval: ")))
        except:
            cont=0
    pmag.chart_maker(Int,Top)

if __name__ == "__main__":
    main()
