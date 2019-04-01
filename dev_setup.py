#!/usr/bin/env python
"""
NAME
    dev_setup.py

DESCRIPTION
    Facilitates simple install, uninstall, and reinstall of the developer
    version of the PmagPy library and GUIs for Unix systems.
    This will edit global environment variables and shell configuration files
    if you have no idea what those are, unless you need immediate quick
    updates to PmagPy, it may be better to use the pip or binary installs of
    this software instructions here:
    (https://earthref.org/PmagPy/cookbook/#pip_install).
    Note for OSX users: you must use bash as your shell (not csh, zsh, etc.).
    To switch to bash, select Terminal --> Preferences --> General,
    and choose "default login shell".
    Last, this script MUST BE RUN FROM THE PMAGPY DIRECTORY.

    Note for Windows users: This functionality is not currently available for Windows.
    Please follow the Cookbook instructions to edit your path by hand:
    https://earthref.org/PmagPy/cookbook/#setting_path


SYNTAX
    python dev_setup.py [install,uninstall,reinstall] [OPTIONS]

OPTIONS
    -h: open help message
"""

#    The windows_install function of this file
#    requires administrative access so you will need to run in a command prompt
#    with elevated privileges. See:
#    (http://www.thewindowsclub.com/how-to-run-command-prompt-as-an-administrator)

#    -p: path_to_python -> necessary if you don't have a fully set up python
#        environment on windows. This information will allow the script to set
#        this python.exe to be the default python interpreter and will have it
#        run when file name with extension .py is entered in command prompt.
#        Note: this should be an ABSOLUTE path.
#        E.g. C:\\Users\\USERNAME\\AppData\\Local\\Continuum\\Anaconda2\\python.exe
#        If you don't know where your python.exe is, type these commands:
#            cd \\
#            dir python.exe /s /p
#        into command prompt and it will tell you the location of all
#        python.exe it can find. This process can take a while, so be
#        patient.


import sys
import os
import subprocess
import functools


def unix_install():
    """
    Edits or creates .bashrc, .bash_profile, and .profile files in the users
    HOME directory in order to add your current directory (hopefully your
    PmagPy directory) and assorted lower directories in the PmagPy/programs
    directory to your PATH environment variable. It also adds the PmagPy and
    the PmagPy/programs directories to PYTHONPATH.
    """
    PmagPyDir = os.path.abspath(".")
    COMMAND = """\n
for d in %s/programs/*/ "%s/programs/"; do
  case ":$PATH:" in
    *":$d:"*) :;; # already there
    *) PMAGPATHS="$PMAGPATHS:$d";; # or PATH="$PATH:$new_entry"
  esac
done
export PYTHONPATH="$PYTHONPATH:%s:%s/programs/"
export PATH="$PATH:$PMAGPATHS" """ % (PmagPyDir, PmagPyDir, PmagPyDir, PmagPyDir)
    frc_path = os.path.join(
        os.environ["HOME"], ".bashrc")  # not recommended, but hey it freaking works
    fbprof_path = os.path.join(os.environ["HOME"], ".bash_profile")
    fprof_path = os.path.join(os.environ["HOME"], ".profile")
    all_paths = [frc_path, fbprof_path, fprof_path]

    for f_path in all_paths:
        open_type = 'a'
        if not os.path.isfile(f_path):
            open_type = 'w+'
            fout = open(f_path, open_type)
            fout.write(COMMAND)
            fout.close()
        else:
            fin = open(f_path, 'r')
            current_f = fin.read()
            fin.close()
            if COMMAND not in current_f:
                fout = open(f_path, open_type)
                fout.write(COMMAND)
                fout.close()

    print("Install complete. Please restart the shell to complete install.\nIf you are seeing strange or non-existent paths in your PATH or PYTHONPATH variable please manually check your .bashrc, .bash_profile, and .profile or attempt to reinstall.")


def unix_uninstall():
    # not recommended, but hey it freaking works
    frc_path = os.path.join(os.environ["HOME"], ".bashrc")
    fbprof_path = os.path.join(os.environ["HOME"], ".bash_profile")
    fprof_path = os.path.join(os.environ["HOME"], ".profile")

    for f_path in [frc_path, fbprof_path, fprof_path]:
        fin = open(f_path, 'r')
        fout_string, skip = "", False
        for line in fin.readlines():
            if ("for d in " in line and "/programs/*/" in line) or "PMAGPATHS=" in line:
                skip = True
            elif 'export PATH="$PATH:$PMAGPATHS"' in line:
                skip = False
                continue
            if skip:
                continue
            else:
                fout_string += line
        fout_string = fout_string.strip('\n')
        fout = open(f_path, 'w')
        fout.write(fout_string)
        fin.close()
        fout.close()

    print("Uninstall complete. Please restart your shell to complete uninstall.")


def windows_install(path_to_python=""):
    """
    Sets the .py extension to be associated with the ftype Python which is
    then set to the python.exe you provide in the path_to_python variable or
    after the -p flag if run as a script. Once the python environment is set
    up the function proceeds to set PATH and PYTHONPATH using setx.

    Parameters
    ----------
    path_to_python : the path the python.exe you want windows to execute when
    running .py files
    """
    if not path_to_python:
        print("Please enter the path to your python.exe you wish Windows to use to run python files. If you do not, this script will not be able to set up a full python environment in Windows. If you already have a python environment set up in Windows such that you can run python scripts from command prompt with just a file name then ignore this message. Otherwise, you will need to run dev_setup.py again with the command line option '-p' followed by the correct full path to python.\nRun dev_setup.py with the -h flag for more details")
        print("Would you like to continue? [y/N] ")
        ans = input()
        if ans == 'y':
            pass
        else:
            return

    # be sure to add python.exe if the user forgets to include the file name
    if os.path.isdir(path_to_python):
        path_to_python = os.path.join(path_to_python, "python.exe")
    if not os.path.isfile(path_to_python):
        print("The path to python provided is not a full path to the python.exe file or this path does not exist, was given %s.\nPlease run again with the command line option '-p' followed by the correct full path to python.\nRun dev_setup.py with the -h flag for more details" % path_to_python)
        return

    # make windows associate .py with python
    subprocess.check_call('assoc .py=Python', shell=True)
    subprocess.check_call('ftype Python=%s ' %
                          path_to_python + '"%1" %*', shell=True)

    PmagPyDir = os.path.abspath(".")
    ProgramsDir = os.path.join(PmagPyDir, 'programs')
    dirs_to_add = [ProgramsDir]
    for d in next(os.walk(ProgramsDir))[1]:
        dirs_to_add.append(os.path.join(ProgramsDir, d))
    path = str(subprocess.check_output('echo %PATH%', shell=True)).strip('\n')
    if "PATH" in path:
        path = ''
    pypath = str(subprocess.check_output(
        'echo %PYTHONPATH%', shell=True)).strip('\n')
    if "PYTHONPATH" in pypath:
        pypath = PmagPyDir + ';' + ProgramsDir
    else:
        pypath += ';' + PmagPyDir + ';' + ProgramsDir
    for d_add in dirs_to_add:
        path += ';' + d_add
    unique_path_list = []
    for p in path.split(';'):
        p = p.replace('"', '')
        if p not in unique_path_list:
            unique_path_list.append(p)
    unique_pypath_list = []
    for p in pypath.split(';'):
        p = p.replace('"', '')
        if p not in unique_pypath_list:
            unique_pypath_list.append(p)
    path = functools.reduce(lambda x, y: x + ';' + y, unique_path_list)
    pypath = functools.reduce(lambda x, y: x + ';' + y, unique_pypath_list)
    print('setx PATH "%s"' % path)
    subprocess.call('setx PATH "%s"' % path, shell=True)
    print('setx PYTHONPATH "%s"' % pypath)
    subprocess.call('setx PYTHONPATH "%s"' % (pypath), shell=True)

    print("Install complete. Please restart the command prompt to complete install")


def windows_uninstall():
    path = str(subprocess.check_output('echo %PATH%', shell=True)).strip('\n')
    if "PATH" in path:
        print("PmagPy dev version not installed, aborting")
        return
    pypath = str(subprocess.check_output(
        'echo %PYTHONPATH%', shell=True)).strip('\n')
    if "PYTHONPATH" in pypath:
        print("PmagPy dev version not installed, aborting")
        return

    paths = path.split(';')
    pypaths = pypath.split(';')

    new_paths = [p for p in paths if 'pmagpy' not in p.lower()]
    new_pypaths = [p for p in pypaths if 'pmagpy' not in p.lower()]

    if new_paths:
        new_path = functools.reduce(lambda x, y: x + ';' + y, new_paths)
    else:
        new_path = ''
    if new_pypaths:
        new_pypath = functools.reduce(lambda x, y: x + ';' + y, new_pypaths)
    else:
        new_pypath = ''

    print('setx PATH "%s"' % new_path)
    subprocess.call('setx PATH "%s"' % new_path, shell=True)
    print('setx PYTHONPATH "%s"' % new_pypath)
    subprocess.call('setx PYTHONPATH "%s"' % (new_pypath), shell=True)

    print("Uninstall complete. Please restart the command prompt to complete uninstall")


if __name__ == "__main__":
    if '-h' in sys.argv:
        help(__name__)
    elif sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
        if "install" in sys.argv:
            unix_install()
        elif "uninstall" in sys.argv:
            unix_uninstall()
        elif "reinstall" in sys.argv:
            unix_uninstall()
            unix_install()
        else:
            unix_install()
    else:
        kwargs = {}
        if '-p' in sys.argv:
            ip = sys.argv.index('-p')
            kwargs['path_to_python'] = sys.argv[ip + 1]

        if "install" in sys.argv:
            windows_install(**kwargs)
        elif "uninstall" in sys.argv:
            windows_uninstall()
        elif "reinstall" in sys.argv:
            windows_uninstall()
            windows_install(**kwargs)
        else:
            windows_install(**kwargs)
