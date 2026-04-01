#!/usr/bin/env pythonw

import sys
try:
    import importlib.metadata as importlib_metadata
except ImportError:
    import importlib_metadata # if Python < 3.7
from os import path
import matplotlib
from .program_envs import prog_env

command = path.split(sys.argv[0])[-1]

if command.endswith(".py"):
    mpl_env = prog_env.get(command[:-3])
elif command.endswith("_a"):
    mpl_env = prog_env.get(command[:-2])
else:
    mpl_env = prog_env.get(command)

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
    for package in ['pmagpy', 'pmagpy-cli']:
        try:
            version = importlib_metadata.version(package)
            print(f"{package} version: {version}")
        except importlib_metadata.version.PackageNotFoundError:
            pass