#!/usr/bin/env pythonw

import sys
try:
    import importlib.metadata as importlib_metadata
except ImportError:
    import importlib_metadata # if Python < 3.7
from os import path
from pmag_env import set_env
from .program_envs import prog_env

command = path.split(sys.argv[0])[-1]

if command.endswith(".py"):
    mpl_env = prog_env.get(command[:-3])
elif command.endswith("_a"):
    mpl_env = prog_env.get(command[:-2])
else:
    mpl_env = prog_env.get(command)

# Pick a GUI backend for the command-line program being run. If a backend has
# already been chosen (notebook inline backend, MPLBACKEND, an explicit
# matplotlib.use() call) it is left alone -- see set_env.set_backend_if_unset.
set_env.set_backend_if_unset(mpl_env or "TKAgg")

if "-v" in sys.argv:
    print("You are running:")
    for package in ['pmagpy', 'pmagpy-cli']:
        try:
            version = importlib_metadata.version(package)
            print(f"{package} version: {version}")
        except importlib_metadata.version.PackageNotFoundError:
            pass