import os
import sys
import time
import urllib2
import pickle
import tempfile
from Tkinter import *


def get_version():
    global pmagpy_path, local_path
    pmagpy_path = os.path.dirname(sys.argv[0])
    local_path = os.path.join(pmagpy_path, 'version.txt')
    try:
        fh_local = open(local_path, 'r')
        local_version = fh_local.read().strip('\n')
    except:
        return # if an error occured (e.g. file not found),
        # give up trying to check for an update
    finally:
        try:
            fh_local.close()  # always close the file handle
        except:
            pass
    return local_version


def main():
    global pmagpy_path, local_path
    local_version = get_version()
    last_path = os.path.join(pmagpy_path, 'version_last_checked.txt')
    # Get the version of the local PmagPy installation
    # from the version.txt file in the current directory.
    # Make sure this check for an update hasn't be done in the last 24 hours
    try:
        fh_last = open(last_path, 'r+')
        last_checked = pickle.load(fh_last)
        if last_checked < time.time() - 24 * 60 * 60:
            return # stop here because it's been less than 24 hours
        else:
            pickle.dump(time.time(), fh_last)
    except IOError:
        try:
            fh_last = open(last_path, 'w')
        except IOError:
            fh_last = open(os.path.join(tempfile.gettempdir(), 'version_last_checked.txt'), 'w')
        pickle.dump(time.time(), fh_last)
    except pickle.UnpicklingError:
        pickle.dump(time.time(), fh_last)
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
        uh_remote = urllib2.urlopen('https://raw.github.com/ltauxe/PmagPy/master/version.txt')
        remote_version = uh_remote.read().strip('\n')
    except:
        return # if an error occured (e.g. not online),
        # give up trying to check for an update
    finally:
        try:
            uh_remote.close() # always close the URL handle
        except:
            pass              # ignore any problems trying to close the file handle

    # Warn the user if their local PmagPy installation is out of date
    if local_version != remote_version:
        root = Tk()
        root.title("Message from PmagPy")
        frame = Frame(root)
        frame.pack()
        l = Label(frame,
                  text="     Your local installation of PmagPy is out of date.\n       Please download the latest version:      \n https://github.com/ltauxe/PmagPy/zipball/master.      ")
        l.pack(side=TOP)
        root.wait_window(frame)


main()
