#!/usr/bin/env python

import  numpy,string,sys
from numpy import random
import numpy.linalg
import exceptions
import os
import check_updates
import scipy
from scipy import array,sqrt,mean

def get_pmag_dir():
    """
    Searches user's path and returns directory in which PmagPy is installed
    """
    path = ''
    for p in os.environ['PATH'].split(':'):
        #print "p", p
        if 'Pmag' in p:
            return p + '/'
    raise Exception("Can't find PmagPy in path")
        #print "path + page", path+page

