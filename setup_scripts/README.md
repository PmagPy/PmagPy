The scripts in this directory are for making new standalone releases.  This is done using py2app for OSX and pyinstaller for Windows and Linux.

## Compiling on OS X

**This doesn't seem to work at present, follow the "more compact executable" instructions in the next section**

First, install anaconda python 3.

Install pyinstaller from the developer branch (certain needed bug fixes are here only, as of 6/8/17, see this [pyinstaller issue](https://github.com/pyinstaller/pyinstaller/issues/2434)):

    pip install git+https://github.com/pyinstaller/pyinstaller.git

Install nomkl to prevent MKL problem (see [this issue](https://github.com/scikit-learn/scikit-learn/issues/5046)):

    conda install nomkl

From your PmagPy directory, generate the .spec file:

    pyi-makespec --onefile --windowed --icon=.\programs\images\PmagPy.ico  --name=PmagGUI .\programs\pmag_gui.py

add the following to the resulting pmag_gui.spec file (where \*\*\* is your username):

    files = [
         ('/Users/***/PmagPy/pmagpy/data_model/*.json', './pmagpy/data_model/'),
         ('/Users/***/PmagPy/dialogs/help_files/*.html', './dialogs/help_files')
    ]

    ...
    a = Analysis(['programs/pmag_gui.py'],
        ...
        datas=files,
    ...

Then run:

    pyinstaller pmag_gui.spec

This will create pmag\_gui.app in PmagPy/dist.  You can then move pmag\_gui.app to PmagPy\_Standalone\_OSX, commit, and push it to Github.  Make a new release on Github, and you're done!


### For a more compact OS X executable

You can create an executable that is over 100MB smaller by installing a more minimal Python distribution using homebrew and pip.  To do so, follow these steps:

- Install brew
  - `/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`
- Install Python
  - `brew install python`
- Link python3 --> python
   - `ln -s /usr/local/bin/python3 /usr/local/bin/python`
- Use pip to install required packages
  - `pip install future matplotlib numpy scipy pandas`
- Use pip to install wxPython
  - `pip install --upgrade -f https://wxpython.org/Phoenix/snapshot-builds/ wxPython`
- Use pip to install Pyinstaller
  - `pip install git+https://github.com/pyinstaller/pyinstaller.git`
- Then you can generate a .spec file and run Pyinstaller, as explained above!

- NB: to brew uninstall this python, you must first delete the symlink you created:
  - `rm /usr/local/bin/python`
  - `brew uninstall python`

Do *not* install cartopy.  It is not required for creating standalones and breaks everything.

Same idea but with miniconda, (a stripped down version of Anaconda Python):

- Download miniconda for Python 3
  - https://conda.io/miniconda.html
- Install Python 3.5.1 # see: https://github.com/pyinstaller/pyinstaller/issues/3192
   - `conda install python=3.5.1`
- Use conda to install required packages
  - `conda install future matplotlib numpy scipy pandas`
- Use pip to install wxPython
  - `pip install --upgrade --pre -f https://wxpython.org/Phoenix/snapshot-builds/ wxPython`
- Use pip to install Pyinstaller
  - `pip install git+https://github.com/pyinstaller/pyinstaller.git`
- Upgrade setuptools
    - `pip install setuptools --upgrade`
- Then you can generate a .spec file and run Pyinstaller, as explained above!


## Compiling on Windows

Windows standalone binaries are compiled using the pyinstaller utility. Before compiling you must ensure you have all dependencies installed and the programs run correctly as python scripts. Then you can start the two stage building process, first by creating the spec file by running this script in the PmagPy main directory:

```bash
pyi-makespec --onefile --windowed --icon=.\programs\images\PmagPy.ico
--version-file=$PATH_TO_PMAGPY_VERSION_FILE --name=PmagGUI
-p=$PATH_TO_ANY_DEPENDENCIES_NOT_ALREADY_IN_ENV .\programs\pmag_gui.py
```

This should make a .spec file in the PmagPy main directory called PmagGUI.spec, you should then open that file and replace the line `datas=None` with `datas=[('./pmagpy/data_model/*','./data_model')]` so that pyinstaller knows where to retrieve data files. Then you can run the following to tell pyinstaller to use the data in the .spec file to build the binary. **Note:** the version file is not strictly necessary but it allows windows to better populate the properties menu for the file, an example can be found [here](http://stackoverflow.com/questions/14624245/what-does-a-version-file-look-like) and documentation [here](https://msdn.microsoft.com/en-us/library/ff468916(v=vs.85).aspx).


```bash
pyinstaller --clean PmagGUI.spec
```

The executable will be in the dist directory. If you're having trouble because your computer can't find pyinstaller try replacing pyinstaller with a direct path the the pyinstaller.exe usually in the scripts file of wherever your python environment is installed. If dependencies are not being bundled make sure all dependencies are in your $PATH variable or added to the -p flag like so -p="PATH1;PATH2".

Optional: To reduce the application size, you can download [UPX](https://github.com/upx/upx/releases/latest), which is a tool for compressing executables.  After downloading, you will unzip it by selecting "extract all".  Then, you'll need to specify the full path to upx.exe in your call to pyinstaller.  So, if upx.exe is C:\path\to\upx\upx394w\upx.exe, your call will look like this:

```bash
pyinstaller --clean PmagGUI.spec --upx-dir C:\path\to\upx\upx394w
```

(Not like this: `--upx-dir C:\path\to\upx\upx394w\upx.exe` or this: `C:\path\to\upx`!)

## Compiling on Linux

The Linux binary is generated very similar to the Windows binary. Again you must have all PmagPy dependencies and pyinstaller on your machine all of which can be found in the standard repositories or pypi. Then you should modify and run this script from the PmagPy main directory to make the .spec file:

```bash
pyi-makespec --onefile --windowed --icon=./programs/images/PmagPy.ico
--name=PmagGUI -p=$PATH_TO_ANY_DEPENDENCIES_NOT_ALREADY_IN_ENV
./programs/pmag_gui.py
```

Then just like above you should open the PmagGUI.spec file and edit the line `datas=None` so it reads `datas=[('./pmagpy/data_model/*','./data_model')]`. Once you've fixed the datas line you should run the same code as above to finish the compiling process.

```bash
pyinstaller --clean PmagGUI.spec
```

The executable will be in the dist directory. If it does not run when you double click it or enter its name in the terminal you may have to change execution permissions to make it runnable by running `chmod a+x $EXENAME`. Also due to the way Pyinstaller is constructed when bundling as one-file you should note that it can take 5-30 seconds for the program to run so check with an activity manager (like top) before assuming the executable did not compile correctly.

**Note:** if compiling this document to pdf using pandoc the command used is `pandoc devguide.md -o devguide.pdf --highlight-style tango -V geometry:margin=.7in`


## Troubleshooting

You can run the executable with output to Terminal (this is particularly useful when your build is refusing to launch):

    ./dist/pmag_gui_3.0

If this doesn't help, see the [Pyinstaller troubleshooting guide](https://pythonhosted.org/PyInstaller/when-things-go-wrong.html).


## DEPRECATED way of making Windows standalones

**Note**: this is the old way of making Windows standalones.

1. Make sure your path points to the correct version of Python.  I've had success with Canopy Python, but you may be able to use a different installation.  You should have pmagpy installed using pip.

2.  Edit "main" function in Pmag GUI and MagIC GUI (desired behavior is slightly different when not launching from the command line).
Change:
`wx.App(redirect=False)` to `wx.App(redirect=True)`

3. Run unittests to make sure that everything works on Windows.  In PmagPy directory: `python -m unittest discover`.  Note: not all tests necessarily have to been passing to have a successful build.  It's still a good point of reference.

4.  Move both Windows setup scripts from the setup_scripts directory to the main PmagPy directory.

5. From the main PmagPy directory, run `python win\_magic\_gui\_setup.py py2exe'. (expect this to take a horribly long time)

6.  From the main PmagPy directory, run `python win\_pmag\_gui\_setup.py py2exe'.  (same as above)

7.  Try to run the distributions.  If one of them doesn't work, you may need to find "numpy-atlas.dll" in your system and copy it to the distribution folders.  (I've had to add "numpy-atlas.dll" to the list of ignored dlls in the setup files.  Otherwise, the build halts with an error halfway through.  However, the finished program needs numpy-atlas to run.)  Once you have the standalones working correctly, you can move on to packaging them up.

8.  If you don't already have it, you'll need to download Inno Setup Compiler: http://www.jrsoftware.org/isdl.php

9.  Either in Inno Setup Compiler or in a text editor, edit setup\_scripts/Pmag_GUI.iss and setup\_scripts/Magic\_GUI.iss.  You'll want to: a) update the version number, b) edit the paths to be correct to your local machine (everywhere you see '\***'), and c) increment the AppVersion number.

10.  Select build --> compile in Inno Setup Compiler.

11.  Sometimes you'll get an error with "EndUpdateResource failed" or something like that.  This may or may not be a real error.  Check that the path of the resource is in fact correct and customized to your machine.  If it is, try again to build the setup script.  Sometimes you might have to try a few times in a row (I don't know why).

12.  Run Pmag\_GUI.iss and Magic\_GUI.iss in the Inno Setup Compiler GUI.  You can find the output files through the Inno GUI by selecting Build --> Open Output Folder.  They should be called: "install\_Pmag\_GUI.exe" and "install\_Magic\_GUI.exe".

13.  Try running the setup for each and see if you get a nice, happy installation.

14.  If everything is good, upload "install\_Pmag\_GUI.exe" and "install\_MagIC\_GUI.exe" to https://github.com/PmagPy/PmagPy-Standalone-Windows

15.  Create a new Github release.  Make sure to update the release number and the links.

NB: I know this process sucks.  Sorry.

### Py2exe troubleshooting


1.  If the executable works fine but the Inno-installed program doesn't, you may want to install the program into a directory where the log can be created (i.e., Desktop.)  You'll want to do this if the program won't run AND you get an error message that the log can't be opened.

2.  Editing registry for use with Canopy.

    open regedit

    find .py
    change Enthought.Canopy to Python.File
    also add Python.File to .py subfolder OpenWithProgIds

    find Python.File
    get path where python is installed (python\_path = which python)
    in subfolder Python.File/shell/Edit with Pythonwin/command, change Data to "python\_path + .exe" + "%1"


## DEPRECATED way of making OSX standalones

**Note**: this is the old way of making OSX standalones

The process of making the standalone GUIs is mostly automated, however, it is broken into two parts.  First, you'll run the process to create the guis, then the process to upload and publish a new release.  The reason for the split is to allow you to open and test your shiny new executables before you publish them.

These instructions presume that you have cloned both the PmagPy git repo and the PmagPy-Standalone-OSX repo, and that they are both contained in the same folder (Python_Projects/ or similar).  If you have a different organizational system, you won't be able to use the bash scripts.

Here are the steps to make standalone Pmag/Magic GUIs for OSX.

1.  Make sure your path points to the correct version of Python.  At this time, py2app doesn't play nice with Canopy.  I've had success with brew-installed Python and wxWidgets, but other distributions may work, as well.  You will, of course, need to have all dependencies installed (numpy, matplotlib, etc.)

2.  Edit "main" function in Pmag GUI and MagIC GUI (desired behavior is slightly different when not launching from the command line).
Change:
`wx.App(redirect=False)` to `wx.App(redirect=True)`

3.  Open your Terminal and navigate to your PmagPy directory

4.  Run:  $ `./setup_scripts/make_guis.sh <new commit name>`

5.  In PmagPy-Standalone-OSX you will find the updated MagIC GUI and Pmag GUI programs.  It is highly recommended that you open both applications and make sure they look good!

6.  Once you are confident that both standalone applications look good, run: $ `./setup_scripts/release_guis.sh <github_user_name> <release_number>`.  To run this step, you will need to provide your Github credentials (so that you can push to the Standalone repo).

### Py2app troubleshooting

General documentation for py2app is available here: https://pythonhosted.org/py2app/index.html

If you get see an error message like this (the build _may_ keep running):
TypeError: dyld_find() got an unexpected keyword argument 'loader'

See this documentation on a similar problem: http://stackoverflow.com/questions/31240052/py2app-typeerror-dyld-find-got-an-unexpected-keyword-argument-loader

You may have to monkey-patch this file: MachOGraph.py.  (Located here on my machine: /usr/local/lib/python2.7/site-packages/macholib/MachOGraph.py, may be elsewhere depending on your Python installation.)
