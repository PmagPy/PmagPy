The scripts in this folder are for making new standalone releases.  This is done using py2app for OSX and py2exe for Windows.

General documentation for py2app: https://pythonhosted.org/py2app/index.html

And for py2exe:  http://py2exe.org/index.cgi/Tutorial

## OSX standalones

The process of making the standalone GUIs is mostly automated, however, it is broken into two parts.  First, you'll run the process to create the guis, then the process to upload and publish a new release.  The reason for the split is to allow you to open and test your shiny new executables before you publish them.

These instructions presume that you have cloned both the PmagPy git repo and the PmagPy-Standalone-OSX repo, and that they are both contained in the same folder (Python_Projects/ or similar).  If you have a different organizational system, you won't be able to use the bash scripts.

Here are the steps to make standalone Pmag/Magic GUIs for OSX.

1.  Make sure your path points to the correct version of Python.  At this time, py2app doesn't play nice with Canopy.  I've had success with brew-installed Python and wxWidgets, but other distributions may work, as well.  You will, of course, need to have all dependencies installed (numpy, matplotlib, etc.)

2.  Edit "main" function in Pmag GUI and MagIC GUI (desired behavior is slightly different when not launching from the command line).
2a. Change:
`wx.App(redirect=False)` to `wx.App(redirect=True)`
2b. Remove comments from these lines:
`if working_dir == '.':`
    `app.frame.on_change_dir_button(None)`

3.  Open your Terminal and navigate to your PmagPy directory

4.  Run:  $ `./setup_scripts/make_guis.sh <new commit name>`

5.  In PmagPy-Standalone-OSX you will find the updated MagIC GUI and Pmag GUI programs.  It is highly recommended that you open both applications and make sure they look good!

6.  Once you are confident that both standalone applications look good, run: $ `./setup_scripts/release_guis.sh <github_user_name> <release_number>`.  To run this step, you will need to provide your Github credentials (so that you can push to the Standalone repo).

## Py2app troubleshooting

If you get see an error message like this (the build _may_ keep running):
TypeError: dyld_find() got an unexpected keyword argument 'loader'

See this documentation on a similar problem: http://stackoverflow.com/questions/31240052/py2app-typeerror-dyld-find-got-an-unexpected-keyword-argument-loader

You may have to monkey-patch this file: MachOGraph.py.  (Located here on my machine: /usr/local/lib/python2.7/site-packages/macholib/MachOGraph.py, may be elsewhere depending on your Python installation.)


## Windows standalones

1. Make sure your path points to the correct version of Python.  I've had success with Canopy Python, but you may be able to use a different installation.

2. From the main PmagPy directory, run `python programs/win_magic_gui_setup.py py2exe'.

3.  From the main PmagPy directory, run `python programs/win_pmag_gui_setup.py py2exe'.

4.  Try to run the distributions.  If one of them doesn't work, you may need to find "numpy-atlas.dll" in your system and copy it to the distribution folders.  (I've had to add "numpy-atlas.dll" to the list of ignored dlls in the setup files.  Otherwise, the build halts with an error halfway through.  However, the finished program needs numpy-atlas to run.)

5.  If you don't already have it, you'll need to download Inno Setup Compiler: http://www.jrsoftware.org/isdl.php

6.  ....

## Py2exe troubleshooting ##

Editing registry for use with Canopy.  

	open regedit

	find .py
	change Enthought.Canopy to Python.File
	also add Python.File to .py subfolder OpenWithProgIds

	find Python.File
	get path where python is installed (python_path = which python)
	in subfolder Python.File/shell/Edit with Pythonwin/command, change Data to "python_path + .exe" + "%1"
	



## Details for people who want them

#setup_pmag_gui.py
Uses py2app to create a Pmag GUI frozen binary for OSX
Run with `python setup_magic_gui.py py2app`
Note: to use this file independently (not wrapped within the make_guis bash script), you must move it to the main PmagPy directory.
#setup_magic_gui.py
Uses py2app to create a MagIC GUI frozen binary for OSX
Run with `python setup_magic_gui.py py2app`
Note: to use this file independently (not wrapped within the make_guis bash script), you must move it to the main PmagPy directory.
#win_setup_pmag_gui.py
Uses py2exe to create a MagIC GUI frozen binary for Windows
Run with `python win_setup_pmag_gui.py py2exe`
#win_setup_magic_gui.py
Uses py2exe to create a MagIC GUI frozen binary for Windows
Run with `python win_setup_pmag_gui.py py2exe`
# make_guis.sh
Creates new OSX standalones for both GUIs
See above.
# release_guis.sh
Creates a new Github release for PmagPy-Standalone-OSX repo.
See above.
