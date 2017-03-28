#! /usr/bin/env python
from __future__ import division
from __future__ import print_function
from builtins import range
from past.utils import old_div
import numpy as np
deg2rad = old_div(np.pi,180.) # remember conversion to radians
for theta in range(90): # short form of range, returns [0,1,2...89]
   ctheta = np.cos(theta*deg2rad) # define ctheta as cosine of theta
   stheta = np.sin(theta*deg2rad)# define stheta as  sine of theta
   ttheta = np.tan(theta*deg2rad)   # define ttheta as tangent of theta
   print('%5.1f %8.4f %8.4f %8.4f' %(theta, ctheta, stheta, ttheta)) 

