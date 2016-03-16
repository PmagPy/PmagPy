The scripts in this folder are for making new standalone releases.  This is done using py2app for OSX and py2exe for Windows.

General documentation for py2app: https://pythonhosted.org/py2app/index.html

And for py2exe:  http://py2exe.org/index.cgi/Tutorial

## OSX standalones

The process of making the standalone GUIs is mostly automated, however, it is broken into two parts.  First, you'll run the process to create the guis, then the process to upload and publish a new release.  The reason for the split is to allow you to open and test your shiny new executables before you publish them.

This setup presumes that you have cloned both the PmagPy git repo and the PmagPy-Standalone-OSX repo, and that they are both contained in a Python_Projects/ folder, or similar.  If you have a different organizational system, you won't be able to use the automated system.

Here are the steps to make standalone Pmag/Magic GUIs for OSX.

1.  Make sure your path points to the correct version of Python.  At this time, py2app doesn't play nice with Canopy.  I've had success with brew-installed Python and wxWidgets, but other distributions may work, as well.

2.  Open your Terminal and navigate to your PmagPy directory

3.  Run:  $ `./setup_scripts/make_guis.sh <new commit name>`

4.  In PmagPy-Standalone-OSX you will find the updated MagIC GUI and Pmag GUI programs.  It is highly recommended that you open both applications and make sure they look good!

5.  Once you are confident that both standalone applications look good, run: $ `./setup_scripts/release_guis.sh <github_user_name> <release_number>`.  To run this step, you will need to provide your Github credentials (so that you can push to the Standalone repo).


## Windows standalones

Coming soon


## Details for people who want them

#setup_pmag_gui.py
Uses py2app to create a Pmag GUI frozen binary
Run with `python setup_magic_gui.py py2app`
Note: to use this file independently (not wrapped within the make_guis bash script), you must move it to the main PmagPy directory.
#setup_magic_gui.py
Uses py2app to create a MagIC GUI frozen binary
Run with `python setup_magic_gui.py py2app`
Note: to use this file independently (not wrapped within the make_guis bash script), you must move it to the main PmagPy directory.
#win_setup_pmag_gui.py
Uses py2exe to create a MagIC GUI frozen binary
Run with `python win_setup_pmag_gui.py py2exe`
#win_setup_magic_gui.py
Uses py2exe to create a MagIC GUI frozen binary
Run with `python win_setup_pmag_gui.py py2exe`
# make_guis.sh
Creates new standalones for both GUIs
See above.
# release_guis.sh
Creates a new Github release for PmagPy-Standalone-OSX repo.
See above.
