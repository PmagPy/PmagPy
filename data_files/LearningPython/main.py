#!/usr/bin/env python
from __future__ import print_function
from builtins import range
from numpy import arange # gives us arange()
def myfunc(Xs):
    """ returns a list of doubled values"""
    Ys=[]
    for x in Xs:
        Ys.append(2*x)
    return Ys
def main():
    """This program prints doubled values!"""
    import numpy
    X=arange(.1,10.1,.2) #make a list of numbers
    Y=myfunc(X) # calls myfunc with argument X
    for i in range(len(X)):
        print(X[i],Y[i])
main()  # runs the main program
