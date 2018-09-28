#!/usr/bin/env pythonw

import sys
from os import path
import pkg_resources
command = path.split(sys.argv[0])[-1]

from .program_envs import prog_env

if command.endswith(".py"):
    mpl_env = prog_env.get(command[:-3])
elif command.endswith("_a"):
    mpl_env = prog_env.get(command[:-2])
else:
    mpl_env = prog_env.get(command)

import matplotlib

# if backend was already set, skip this step
if matplotlib.get_backend() in ('WXAgg', 'TKAgg'):
    pass
# if backend wasn't set yet, set it appropriately
else:
    if mpl_env:
        matplotlib.use(mpl_env)
    else:
        matplotlib.use("TKAgg")

if "-v" in sys.argv:
    print("You are running:")
    try:
        print(pkg_resources.get_distribution('pmagpy'))
    except pkg_resources.DistributionNotFound:
        pass
    try:
        print(pkg_resources.get_distribution('pmagpy-cli'))
    except pkg_resources.DistributionNotFound:
        pass

#from . import generic_magic
#from . import sio_magic
#from . import cit_magic
#from . import _2g_bin_magic
#from . import huji_magic
#from . import huji_magic_new
#from . import ldeo_magic
#from . import iodp_srm_magic
#from . import iodp_dscr_magic
#from . import iodp_samples_magic
#from . import pmd_magic
#from . import tdt_magic
#from . import jr6_jr6_magic
#from . import jr6_txt_magic
#from . import bgc_magic


#__all__ = [generic_magic, sio_magic, cit_magic, _2g_bin_magic, huji_magic,
#           huji_magic_new, ldeo_magic, iodp_srm_magic, iodp_dscr_magic,
#           pmd_magic, tdt_magic, jr6_jr6_magic, jr6_txt_magic, bgc_magic,
#           iodp_samples_magic]
