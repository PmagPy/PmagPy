#!/usr/bin/env python
import sys,os,subprocess

def unix_install():
    """
    Edits or creates .bashrc, .bash_profile, and .profile files in the users HOME directory  in order to add your current directory (hopefully your PmagPy directory) and assorted lower directories in the PmagPy/programs directory to your PATH enviornment variable. It also adds the PmagPy and the PmagPy/programs directories to PYTHONPATH.
    """
    PmagPyDir=os.path.abspath(".")
    COMMAND="""
PMAGPATHS="%s"
PMAGPATHS="$PMAGPATHS:%s/programs/"
for d in %s/programs/*/; do
  PMAGPATHS="$PMAGPATHS:$d"
done
export PYTHONPATH="$PYTHONPATH:%s:%s/programs/"
export PATH="$PATH:$PMAGPATHS" """%(PmagPyDir,PmagPyDir,PmagPyDir,PmagPyDir,PmagPyDir)
    frc_path=os.path.join(os.environ["HOME"],".bashrc") #not recommended, but hey it freaking works
    fbprof_path=os.path.join(os.environ["HOME"],".bash_profile")
    fprof_path=os.path.join(os.environ["HOME"],".profile")

    open_type='a'
    if not os.path.isfile(frc_path): open_type='w+'
    frc=open(frc_path,open_type)
    frc.write(COMMAND)
    frc.close()

    open_type='a'
    if not os.path.isfile(fbprof_path): open_type='w+'
    fbprof=open(fbprof_path,open_type)
    fbprof.write(COMMAND)
    fbprof.close()

    open_type='a'
    if not os.path.isfile(fprof_path): open_type='w+'
    fprof=open(fprof_path,open_type)
    fprof.write(COMMAND)
    fprof.close()

    print("please restart the shell to complete install")

def windows_install(path_to_python=""):
    """
    Sets the .py extension to be associated with the ftype Python which is then set to the python.exe you provide in the path_to_python variable or after the -p flag if run as a script. Once the python environment is set up the function proceeds to set PATH and PYTHONPATH using setx.

    Parameters
    ----------
    path_to_python : the path the python.exe you want windows to execute when running .py files
    """
    if not path_to_python: print("please the path to your python.exe you wish windows to use to run python files, aborting");return
    #make windows associate .py with python
    subprocess.check_call('assoc .py=Python',shell=True)
    subprocess.check_call('ftype Python=%s '%path_to_python + '"%1" %*', shell=True)

    PmagPyDir=os.path.abspath(".")
    ProgramsDir=os.path.join(PmagPyDir,'programs')
    dirs_to_add = [PmagPyDir,ProgramsDir]
    for d in next(os.walk(ProgramsDir))[1]:
        dirs_to_add.append(os.path.join(ProgramsDir,d))
    path = subprocess.check_output('echo %PATH%', shell=True).strip('\n')
    if "PATH" in path: path=''
    pypath = subprocess.check_output('echo %PYTHONPATH%', shell=True).strip('\n')
    if "PYTHONPATH" in pypath: pypath=''
    for d_add in dirs_to_add:
#        print('set PATH="%PATH%;'+d_add+'"')
#        subprocess.call('set PATH="%PATH%;'+d_add+'"', shell=True)
        path+=';'+d_add
    pypath+=PmagPyDir+';'+ProgramsDir
    unique_path_list=[]
    for p in path.split(';'):
        p=p.replace('"','')
        if p not in unique_path_list:
            unique_path_list.append(p)
    unique_pypath_list=[]
    for p in pypath.split(';'):
        p=p.replace('"','')
        if p not in unique_pypath_list:
            unique_pypath_list.append(p)
    path=reduce(lambda x,y: x+';'+y, unique_path_list)
    pypath=reduce(lambda x,y: x+';'+y, unique_pypath_list)
    print('setx PATH "%s"'%path)
    subprocess.call('setx PATH "%s"'%path, shell=True)
    print('setx PYTHONPATH "%s"'%pypath)
    subprocess.call('setx PYTHONPATH "%s"'%(pypath), shell=True)

    print("please restart the shell to complete install")

if __name__=="__main__":
    if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
        unix_install()
    else:
        kwargs={}
        if '-p' in sys.argv:
            ip=sys.argv.index('-p')
            kwargs['path_to_python']=sys.argv[ip+1]
        windows_install(**kwargs)
