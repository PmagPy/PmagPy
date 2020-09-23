The scripts in this directory are for making new standalone releases.  This is done using pyinstaller for all platforms.

## Compiling on OS X

**This doesn't seem to work at present, follow the "more compact executable" instructions in the next section**

First, install anaconda python 3.

Install pyinstaller from the developer branch (certain needed bug fixes are here only, as of 6/8/17, see this [pyinstaller issue](https://github.com/pyinstaller/pyinstaller/issues/2434)):

    pip install git+https://github.com/pyinstaller/pyinstaller.git

You may be able to use conda pyinstaller:

    conda install pyinstaller --channel conda-forge


Either way, you will need to monkey patch pyinstaller.  Here is information on the issue:

https://stackoverflow.com/questions/63163027/how-to-use-pyinstaller-with-matplotlib-in-use

Here is more information on how to find the file that you need to edit:

    >>> import PyInstaller
    >>> PyInstaller.__file__
    '/Users/***/anaconda3/envs/pmagpy_september_2020/lib/python3.7/site-packages/PyInstaller/__init__.py'
>>>

modify:
    /Users/***/anaconda3/envs/pmagpy_septempber_2020/lib/python3.7/site-packages/PyInstaller/hooks/hook-matplotlib.py


If you have a dll not loading error:

    File "shapely/geos.py", line 112, in <module>
    File "PyInstaller/loader/pyiboot01_bootstrap.py", line 146, in __init__.__main__.PyInstallerImportError: Failed to load dynlib/dll '/var/folders/qb/3td4bl3s2pz__jc94hp7z2c40000gn/T/_MEICSr2rH/lib/libgeos_c.dylib'. Most probably this dynlib/dll was not found when the application was frozen.

try commenting out line 112 and 113 from geos.py

https://github.com/Toblerity/Shapely/issues/916

The file is here:

~/anaconda3/envs/pmagpy_september)2020/lib/python3.7/site-packages/shapely/geos.py

Cartopy currently causes a seg fault and cannot be used (the executable will compile, but won't run).  To fix this, I've prevented cartopy from being imported for the OSX executable.  See commit fd5a710.


If you have a problem with MKL:

Install nomkl to prevent MKL problem (see [this issue](https://github.com/scikit-learn/scikit-learn/issues/5046)):


Ok, you're finally ready.  You will need a spec file to generate the executable.  You should be able to use PmagPy/pmag_gui.spec.  To create that file from scratch, see instructions at the end of this README.


Then run:

    pyinstaller pmag_gui.spec

This will create pmag\_gui.app in PmagPy/dist.  You can then move pmag\_gui.app to PmagPy\_Standalone\_OSX, commit, and push it to Github.  Make a new release on Github, and you're done!


### For a more compact OS X executable

You can create an executable that is over 100MB smaller by installing a more minimal Python distribution using homebrew and pip.  To do so, follow these steps:

- Install brew
  - `/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`
- Install Python
  - `brew install python`
- Link python3 --> python (not sure this is necessary)
   - `ln -s /usr/local/bin/python3 /usr/local/bin/python`
- Use pip to install required packages
  - `pip install future matplotlib numpy scipy pandas`
- Use pip to install wxPython
  - `pip install --upgrade -f https://wxpython.org/Phoenix/snapshot-builds/ wxPython`
- Use pip to install Pyinstaller
  - `pip install git+https://github.com/pyinstaller/pyinstaller.git`
- Replace `#!/usr/bin/env/pythonw` with `#!/usr/bin/env/python3` at the top of pmag\_gui.py magic\_gui.py.
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

Windows standalone binaries are compiled using the pyinstaller utility. Before compiling you must ensure you have all dependencies installed and the Pmag GUI runs correctly on your local machine. Next, you need a spec file.  You can generate the .spec file using the instructions in the last section of this README, or you can use the file that's already been created in PmagPy/pmag_gui.spec.


```bash
pyinstaller --clean PmagGUI.spec
```

The executable will be in the dist directory. If you're having trouble because your computer can't find pyinstaller try replacing pyinstaller with a direct path the the pyinstaller.exe usually in the scripts file of wherever your python environment is installed. If dependencies are not being bundled make sure all dependencies are in your $PATH variable or added to the -p flag like so -p="PATH1;PATH2".

Optional: To reduce the application size, you can download [UPX](https://github.com/upx/upx/releases/latest), which is a tool for compressing executables.  After downloading, you will unzip it by selecting "extract all".  Then, you'll need to specify the full path to upx.exe in your call to pyinstaller.  So, if upx.exe is C:\path\to\upx\upx394w\upx.exe, your call will look like this:

```bash
pyinstaller --clean PmagGUI.spec --upx-dir C:\path\to\upx\upx394w
```

(Not like this: `--upx-dir C:\path\to\upx\upx394w\upx.exe` or this: `C:\path\to\upx`!)


Environment (other configurations may work, but I can confirm that this way does):

You need to activate a conda environment to this work -- you cannot just use your base environment.  Here are the steps to create and activate the environment, install pyinstaller, and then make the executable.

    # create an environment with the required packages
    conda create --name pmagpy python=3.7 future wxPython pandas matplotlib
    # activate that environment
    conda activate pmagpy
    # install pyinstaller
    conda install pyinstaller --channel conda-forge
    # create executable
    pyinstaller --clean pmag_gui.spec


Windows 10
Conda python 3.7
Regular dependencies, but: no cartopy, no scripttest.
You can also install the `requests` module
Conda cartopy IS NOT compatible with conda pyinstaller.
Pyinstaller from conda-forge seems to work well currently, but you can install the latest pyinstaller directly from Github if needed:

    pip install git+https://github.com/pyinstaller/pyinstaller.git

If you need to install this way, but you get a weird error, you might have a pep 517 issue, and should check out this issue.  See https://github.com/PmagPy/PmagPy/issues/567.




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


## Generating the .spec file

The following commands will allow you to generate the .spec file.  You can also find it in PmagPy/pmag_gui.spec. To generate a new pmag_gui.spec file, change direcotries into your PmagPy directory and run the following command:

    pyi-makespec --onefile --windowed --icon=.\programs\images\PmagPy.ico  --name=PmagGUI .\programs\pmag_gui.py

Then add the following to the resulting pmag_gui.spec file:


    current_dir = os.getcwd()
    files = [('{}/pmagpy/data_model/*.json'.format(current_dir), './pmagpy/data_model/'),
         ('{}/dialogs/help_files/*.html'.format(current_dir), './dialogs/help_files')
        ]


Additionally, in the Analysis function you will need to add the following arguments:

     a = Analysis(['programs/pmag_gui.py'],
             pathex=[current_dir],
             binaries=[],
             datas=files,
             hiddenimports=['scipy.optimize', 'scipy.interpolate',
                            'scipy._lib.messagestream',
                            # timdeltas appears necessary for Windows with
                            # conda-installed pyinstaller
                            'pandas._libs.tslibs.timedeltas',
                            'pandas.concat', 'wget', 'pkg_resources.py2_warn'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

That should do it!

If you want to include a version file as well, you can find more information here: an example can be found [here](http://stackoverflow.com/questions/14624245/what-does-a-version-file-look-like) and documentation [here](https://msdn.microsoft.com/en-us/library/ff468916(v=vs.85).aspx).
