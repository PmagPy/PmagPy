#!/usr/bin/env python
from __future__ import print_function
from builtins import input
def DoubleOrNothing(variable):
    if variable >= 10: # tests variable against 10
        return 2.0*variable # returns double
    else:  
       return 0.

def main():
    var=input('Enter number:  ')
    result=DoubleOrNothing(float(var))
    if result==0.:
        print('You get nothing!')
    else:
        print('You win!  your answer is: ',result)
main()




