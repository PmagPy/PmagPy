# Developer's Guide


## Contributing

There are two main ways to contribute to the PmagPy project.
1. If you want to report a bug or request a new feature, please create a [Github issue](https://github.com/PmagPy/PmagPy/issues).  If you are reporting a bug, please provide as much detail as possible about how you discovered the bug.

2. If you want to add a new feature yourself, make a pull request..... FILL IN DETAILS.


## Style guidelines

Readable code is good code.  To that end, we request that contributors adhere to reasonable style guidelines.  For more information about standard Python style guidelines, see [PEP 8](https://www.python.org/dev/peps/pep-0008/).


## Testing guidelines

For information about writing and running tests, see the [testing README](https://github.com/PmagPy/PmagPy/blob/master/pmagpy_tests/README.md).

## Directory structure


├── bin
├── build
├── data\_files
├── dialogs
│   └── help\_files
├── dist
├── help\_files
├── locator
├── notebooks
├── pmag\_env
├── pmagpy
│   ├── data\_model
│   └── mapping
├── pmagpy.egg-info
├── pmagpy\_cli.egg-info
├── pmagpy\_tests
├── programs
│   ├── deprecated
├── setup\_scripts
└── uninstall\_Mac\_OSX.app
    └── Contents
        ├── MacOS
        └── Resources

## Resources

Link to Cookbook
Link to Data model
Link to Lisa's textbook


## Compile and Release Guide

For information about how the standalone executables are created, see the [standalones README](https://github.com/PmagPy/PmagPy/tree/master/setup_scripts).

### Compiling on Windows

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

### Compiling on Linux

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
