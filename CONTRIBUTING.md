# Developer's Guide

## Contributing

As an open-source, community project, we welcome improvements and feedback!  There are two main ways to contribute to the PmagPy project.

1. If you want to report a bug or request a new feature, please create a [Github issue](https://github.com/PmagPy/PmagPy/issues).  If you are reporting a bug, please provide as much detail as possible about how you discovered the bug.  For a full explanation of how to create a new issue, and what information to include, see [Github documentation](https://guides.github.com/activities/contributing-to-open-source/#contributing).

2. If you want to add a new feature yourself or fix a bug yourself, that's great too.  The process for adding a feature looks like this: fork the PmagPy repository, create a branch for your feature or bugfix, make some changes, and then submit a pull request.  Don't worry if you don't know how to do all of those steps!  If you aren't familiar with git, Github, or the details of this process, you will find this short [tutorial](https://guides.github.com/activities/forking/) helpful.  If you're still stuck after that but want to contribute, you can create a [Github issue](https://github.com/PmagPy/PmagPy/issues) and we will help get you sorted.  Depending on what kind of contribution you are making, you may also want to add some tests.  See our [testing README](https://github.com/PmagPy/PmagPy/blob/master/pmagpy_tests/README.md) for details on making and running PmagPy tests.

## Style guidelines

Readable code is good code.  To that end, we request that contributors adhere to reasonable style guidelines.  For more information about standard Python style guidelines, see [PEP 8](https://www.python.org/dev/peps/pep-0008/).


## Testing guidelines

For information about writing and running tests, see the [testing README](https://github.com/PmagPy/PmagPy/blob/master/pmagpy_tests/README.md).


## Directory structure

**Coming soon:** links to the relevant Jupyter notebooks where you can see how some of these pieces work.

#### Key directories

The `pmagpy` directory contains all the low-level functionality that the PmagPy project is built on. pmag.py and ipmag.py contain many functions that can be used in Jupyter notebooks or for building up more complex programs and GUIs.  Other important modules in the `pmagpy` directory:
- a plotting library -- pmagplotlib.py
- a utility for building up MagIC contributions -- new_builder.py
- modules for interfacing with the data models (controlled_vocabularies2.py, controlled\_vocabularies3.py, and data\_model3.py), as well as a full backup of the 2.5 and 3.0. data model (in the `data_model` subdirectory).

To see a notebook with examples of how to use pmag.py and ipmag.py:  https://github.com/PmagPy/2016_Tauxe-et-al_PmagPy_Notebooks/blob/master/Example_PmagPy_Notebook.ipynb

To actually _run_ that notebook:

Go into your command line.
Change directories into a directory where you keep projects.
`git clone git@github.com:PmagPy/2016_Tauxe-et-al_PmagPy_Notebooks.git`
`cd 2016_Tauxe-et-al_PmagPy_Notebooks`
`jupyter notebook`
A browser window will open automatically.
Click Example\_PmagPy\_Notebook.ipynb

For more examples of how to use ipmag.py/pmag.py, try Additional\_PmagPy\_Examples.ipynb as well (located in the same directory as the previous notebook).


The `SPD` directory contains a program to calculate statistics using Greig Paterson's [standard paleointensity definitions](https://earthref.org/PmagPy/SPD/home.html).

The `programs` directory contains executable programs that are installed as part of the pmagpy-cli package and can be run on the command-line.

You can see a static version of [the notebook](https://github.com/PmagPy/PmagPy/blob/master/notebooks/_PmagPy.ipynb).

If you want to actually run the notebook:

You will either need to download _PmagPy.ipynb from the Github link above, or find your PmagPy directory.  Go into your command line.  You can run `jupyter notebook` from wherever you put _PmagPy.ipynb, or from your PmagPy directory.  Open _PmagPy.ipynb for examples of how to use most of the PmagPy command line programs.

The `dialogs` directory contains GUI components that are used to build the graphical elements of the PmagPy GUIs.

`data_files` contains example files used in testing and in [Cookbook](https://earthref.org/PmagPy/cookbook/) examples.

`notebooks` contains a number of example Jupyter notebooks that demonstrate PmagPy functionality.

`pmag_env` is a module that sets the backend for plotting as either TKAgg (for non-wxPython programs) or WXAgg (for wxPython programs).

`locator` is a module that finds the directory where PmagPy is installed.  __Please__ use caution in modifying this module!  You can break a lot of things.


#### Less key directories

`help_files` contains html help that is used in the GUIs.

`setup_scripts` contains scripts that are used in created standalone releases of the GUIs for Mac, Windows, and Linux.

`bin` contains some scripts that are used in creating the Anaconda part of a pip release.

`build`, `dist`, `pmagpy.egg_info` and `pmagpy_cli.egg_info` are not in the main Github repo, however they may be created automatically when making a pip release.  You should not need to interact directly with any of them.

`uninstall_Mac_OSX.app` is an executable that allows users who installed PmagPy pre-pip to uninstall it completely.  This prevents possible conflicts between old and new versions of PmagPy.

Here is a visual representation of the directory structure:

```
├── bin
├── build
├── data_files
├── dialogs
│   └── help_files
├── dist
├── help_files
├── locator
├── notebooks
├── pmag_env
├── pmagpy
│   ├── data_model
│   └── mapping
├── pmagpy.egg-info
├── pmagpy_cli.egg-info
├── pmagpy_tests
├── programs
│   ├── deprecated
├── setup_scripts
└── uninstall_Mac_OSX.app
```

## Compile and Release Guide

We try to make new releases of PmagPy several times per year.

A new release includes: updated pip packages (pmagpy & pmagpy-cli), and updated standalone GUIs (for Windows, Mac, and Linux).
Making a new release has several steps:

1. Make (or update) a release branch.  This allows work to continue on the master branch, while keeping a stable branch for the release.  Once the release is ready, the pip releases and standalones should be released from this branch!

2. Make sure all tests are passing and all new features are working.

3. Create a new release number.  Release numbers are in the form of MAJOR.MINOR.PATCH, and each release number should be higher than the one before it.  More on semantic versioning can be found [here](http://semver.org).  The pip release and the standalones should all use the same release number!

4. Create a pip release.

**Note:** To make a pip release, you must have a PyPI account and be added as an Owner or Maintainer of pmagpy and pmagpy-cli.

These are the steps to make a pip release for pmagpy and pmagpy-cli.

First, increment the version number in setup.py or command\_line\_setup.py.  PYPI will reject a duplicate version number I forget this step.

From the PmagPy directory, use the following command to build a new distribution of pmagpy, upload it to PYPI, and upgrade locally:

`rm -rf build dist && python setup.py sdist bdist_wheel && twine upload dist/* && pip install pmagpy —upgrade`

To make a test release, use a slightly different command from the PmagPy directory, which will: build a new distribution of pmagpy, upload it to the test site (will not overwrite the version people can download), and upgrade locally:

`python setup.py sdist bdist_wheel upload -r https://testpypi.python.org/pypi && pip install -i https://testpypi.python.org/pypi pmagpy —upgrade`

To build pmagpy-cli, you can use the same two commands above, but replacing "setup.py" with "command\_line\_setup.py".

A few notes on the whole thing:  first of all, testing the pip install locally doesn't work very well (i.e., `python setup.py install` or `python setup.py test`), because it doesn’t deal correctly with the required data files.  Whenever testing a new pip distribution, it is best to upload to test\_PYPI instead, even though it takes a minute or so to do.  Second, we are using twine for uploading to real PYPI but not to upload to test PYPI.  Using twine is recommended because it transfers the package data in a more secure way, but it doesn't currently work with test_PYPI.

This article has some more good information about uploading to PYPI, etc.:  https://tom-christie.github.io/articles/pypi/

5. Create standalone executables.  The process is different for each platform, and details are in the [standalones README](https://github.com/PmagPy/PmagPy/tree/master/setup_scripts).

6. If any bug-fixes were made on the release branch during this process, those changes should be merged into master.



## Resources

Detailed information about installing and running all of the [PmagPy programs](https://earthref.org/PmagPy/cookbook/)

The [MagIC database](https://earthref.org/MagIC/)

Lisa Tauxe's [Essentials of Paleomagnetism](https://earthref.org/MagIC/books/Tauxe/Essentials/)
