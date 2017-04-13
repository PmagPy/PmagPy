#!/usr/bin/env pythonw

import sys
from os import path
import pkg_resources
command = path.split(sys.argv[0])[-1]

from program_envs import prog_env
if command.endswith(".py"):
    mpl_env = prog_env.get(command[:-3])
elif command.endswith("_a"):
    mpl_env = prog_env.get(command[:-2])
else:
    mpl_env = prog_env.get(command)

import matplotlib
if mpl_env:
    matplotlib.use(mpl_env)
else:
    matplotlib.use("TKAgg")

if "-v" in sys.argv:
    print "You are running:"
    try:
        print pkg_resources.get_distribution('pmagpy')
    except pkg_resources.DistributionNotFound:
        pass
    try:
        print pkg_resources.get_distribution('pmagpy-cli')
    except pkg_resources.DistributionNotFound:
        pass


#import generic_magic2
#import sio_magic2
#import cit_magic2
#import _2g_bin_magic2
#import huji_magic2
#import huji_magic_new2
#import ldeo_magic2
#import iodp_srm_magic2
#import iodp_dscr_magic2
#import iodp_samples_magic
#import pmd_magic2
#import tdt_magic2
#import jr6_jr6_magic2
#import jr6_txt_magic2
#import bgc_magic2


#__all__ = [generic_magic2, sio_magic2, cit_magic2, _2g_bin_magic2, huji_magic2,
#           huji_magic_new2, ldeo_magic2, iodp_srm_magic2, iodp_dscr_magic2,
#           pmd_magic2, tdt_magic2, jr6_jr6_magic2, jr6_txt_magic2, bgc_magic2,
#           iodp_samples_magic]
