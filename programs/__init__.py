#!/usr/bin/env pythonw

import sys
from os import path
import pkg_resources
command = path.split(sys.argv[0])[-1]

from program_envs import prog_env
mpl_env = prog_env.get(command[:-3])
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


import generic_magic
import sio_magic
import cit_magic
import _2g_bin_magic
import huji_magic
import huji_magic_new
import ldeo_magic
import iodp_srm_magic
import iodp_dscr_magic
import iodp_samples_magic
import pmd_magic
import tdt_magic
import jr6_jr6_magic
import jr6_txt_magic
import bgc_magic


__all__ = [generic_magic, sio_magic, cit_magic, _2g_bin_magic, huji_magic,
           huji_magic_new, ldeo_magic, iodp_srm_magic, iodp_dscr_magic,
           pmd_magic, tdt_magic, jr6_jr6_magic, jr6_txt_magic, bgc_magic,
           iodp_samples_magic]
