import os
import sys
from pkg_resources import resource_filename
#import time
#import urllib2
#import pickle
#from Tkinter import *

def get_pmag_dir():
    """
    Returns directory in which PmagPy is installed
    """
    # need to update this so that it works with compiled version
    # this is correct for use with PmagPy:
    #return os.path.dirname(os.path.realpath(__file__))
    # this is correct for py2exe
    win_frozen = is_frozen()
    if win_frozen:
        path = os.path.abspath(unicode(sys.executable, sys.getfilesystemencoding()))
        path = os.path.split(path)[0]
        return path
    # this is correct for py2app
    try:
        return os.environ['RESOURCEPATH']
    # this works for everything else
    except KeyError:
        # new way:
        lib_file = resource_filename('pmagpy', 'pmag.py')
        lib_dir = os.path.split(lib_file)[0]
        lib_dir = os.path.realpath(lib_dir)
        # old way:
        #lib_dir = os.path.dirname(os.path.realpath(__file__))
        if not os.path.exists(lib_dir):
            lib_dir = os.getcwd()
        if not os.path.exists(lib_dir):
            print '-W- Can\'t find the data model!  Make sure you have installed pmagpy using pip: "pip install pmagpy --upgrade"'
            return
        lib_dir = lib_dir.strip(os.pathsep)
        if lib_dir.endswith('pmagpy'):
            pmag_dir = lib_dir[:-6]
        else:
            pmag_dir = lib_dir
        if not os.path.exists(pmag_dir):
            print '-W- Can\'t find the data model!  Make sure you have installed pmagpy using pip: "pip install pmagpy --upgrade"'
            return
        return pmag_dir # os.path.dirname(os.path.realpath(__file__))

    ##except KeyError:
    ##    return os.path.dirname(os.path.realpath(__file__))


def is_frozen():
    """
    Checks whether python is running as a Windows frozen binary
    """
    if hasattr(sys, "frozen"):
        if sys.frozen in ("windows_exe", "console_exe"):
            return True
    return False

def get_version():
    import version
    #global pmagpy_path
    pmagpy_path = get_pmag_dir()
    return version.version


"""    
def main():
    global pmagpy_path
    local_version=get_version()
    last_path   = os.path.join(pmagpy_path, 'version_last_checked.txt')
    # Get the version of the local PmagPy installation
    # from the version.py file in the current directory.
    # Make sure this check for an update hasn't be done in the last 24 hours
    try:
        fh_last = open(last_path, 'r+')
        last_checked = pickle.load(fh_last)
        if (time.time() - last_checked) < 24*60*60: # if last check was less than a day ago
            return            # stop here because it's been less than 24 hours
        else:
            fh_last.close()
            fh_last = open(last_path, 'w') # open it and overwrite previous value
            pickle.dump(time.time(), fh_last)
            fh_last.write('\nThe above is a "pickled" representation of the last time you checked for updates.  Please leave this file alone; it will be updated automatically!')
            
    except IOError as io:
        #print "IOError", io
        fh_last = open(last_path, 'w')
        pickle.dump(time.time(), fh_last)
        fh_last.write('\nThe above is a "pickled" representation of the last time you checked for updates.  Please leave this file alone; it will be updated automatically!')
    except pickle.UnpicklingError as ue:
        #print "UnpicklingError", ue
        pickle.dump(time.time(), fh_last)
    except EOFError: # if version_last_checked file is empty for some reason
        pickle.dump(time.time(), fh_last)
        fh_last.write('\nThe above is a "pickled" representation of the last time you checked for updates.  Please leave this file alone; it will be updated automatically!')
    except:
        pass                  # ignore any other problems opening the file handle
                              # or pickling the time stamp
    finally:
        try:
            fh_last.close()   # always close the file handle
        except:
            pass              # ignore any problems trying to close the file handle


    # Get the version of the latest remote PmagPy repository
    # from the version.txt file on GitHub
    try:
       #uh_remote = urllib2.urlopen('https://raw.github.com/ltauxe/PmagPy/master/version.txt')
       uh_remote = urllib2.urlopen('https://raw.github.com/ltauxe/PmagPy/master/version.py')
       remote_version = uh_remote.readlines()[0][1:-2] # strips out extra quotation marks
    except Exception as ex:
       return                # if an error occured (e.g. not online), 
                              # give up trying to check for an update
    finally:
        try:
            uh_remote.close() # always close the URL handle
        except:
            pass              # ignore any problems trying to close the file handle
    
    # Warn the user if their local PmagPy installation is out of date
    if local_version != remote_version:
        root=Tk()
        root.title("Message from PmagPy")
        frame=Frame(root)
        frame.pack()
        l=Label(frame,text="     Your local installation of PmagPy is out of date.\n       Please download the latest version:      \n https://github.com/ltauxe/PmagPy/zipball/master.      ")
        l.pack(side=TOP)
        root.wait_window(frame)

if __name__ == '__main__':
   main()
"""
