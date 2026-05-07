# Contributing

## Ways to contribute

As an open-source, community project, we welcome improvements and feedback!  There are two main ways to contribute to the PmagPy project.

1. If you want to report a bug or request a new feature, you can click here to create a [Github issue](https://github.com/PmagPy/PmagPy/issues).  If you are reporting a bug, please provide as much detail as possible about how you discovered the bug.  For a full explanation of how to create a new issue, and what information to include, see [Github documentation](https://guides.github.com/activities/contributing-to-open-source/#contributing).

2. If you want to add a new feature yourself or fix a bug yourself, that's great too.  The process for adding a feature looks like this: fork the PmagPy repository, create a branch for your feature or bugfix, make some changes, and then submit a pull request.  Don't worry if you don't know how to do all of those steps!  If you aren't familiar with git, Github, or the details of this process, you will find this short [tutorial](https://guides.github.com/activities/forking/) helpful.  If you're still stuck after that but want to contribute, you can create a [Github issue](https://github.com/PmagPy/PmagPy/issues) and we will help get you sorted.  Depending on what kind of contribution you are making, you may also want to add some tests.  See our [testing README](https://github.com/PmagPy/PmagPy/blob/master/pmagpy_tests/README.md) for details on making and running PmagPy tests.

If you will be making significant contributions via git, we have some additional guidelines for [good git protocols](#git-protocols).

## Style guidelines

Good code must be readable.  To that end, we request that contributors try to write code that can be understood by others!  One way to do this is by adhering to reasonable style guidelines.  For more information about standard Python style guidelines, see [PEP 8](https://www.python.org/dev/peps/pep-0008/).


## Testing guidelines

For information about writing and running tests, see the [testing README](https://github.com/PmagPy/PmagPy/blob/master/pmagpy_tests/README.md).


## Directory structure

Next we have a breakdown of how the PmagPy repository is structured.  In some cases, we have included relevant Jupyter notebooks so that you can get an interactive demonstration of how some these pieces of code work.

### Key directories

#### pmagpy
The `pmagpy` directory contains all the low-level functionality that the PmagPy project is built on. pmag.py and ipmag.py contain many functions that can be used in Jupyter notebooks or for building up more complex programs and GUIs.  Other important modules in the `pmagpy` directory:
  - a plotting library -- pmagplotlib.py
  - a utility for building up MagIC contributions -- contribution\_builder.py
  - modules for interfacing with the data models (controlled\_vocabularies2.py, controlled\_vocabularies3.py, and data\_model3.py), as well as a full backup of the 2.5 and 3.0. data model (in the `data_model` subdirectory).

To see a notebook with examples of how to use pmag.py and ipmag.py, see the [PmagPy notebook](http://pmagpy.github.io/PmagPy.html).

To actually _run_ that notebook, see this [Cookbook section](https://earthref.org/PmagPy/cookbook/#notebook_quickstart) on how to get the notebook up and running.


#### SPD
The `SPD` directory contains a program to calculate statistics using Greig Paterson's [standard paleointensity definitions](https://earthref.org/PmagPy/SPD/home.html).

#### programs
The `programs` directory contains executable programs that are installed as part of the pmagpy-cli package and can be run on the command-line.

To see a notebook with examples of how to run most of the command-line programs, see the [PmagPy notebook](http://pmagpy.github.io/PmagPy.html).

To actually run these notebooks, see this [Cookbook section](https://earthref.org/PmagPy/cookbook/#notebook_quickstart) on how to get notebooks up and running.

#### dialogs
The `dialogs` directory contains GUI components that are used to build the graphical elements of the PmagPy GUIs.

#### data_files
`data_files` contains example files used in testing and in [Cookbook](https://earthref.org/PmagPy/cookbook/) examples.

#### pmag_env
`pmag_env` is a module that sets the backend for plotting as either TKAgg (for non-wxPython programs) or WXAgg (for wxPython programs).

#### locator
`locator` is a module that finds the directory where PmagPy is installed.  __Please__ use caution in modifying this module!  You can break a lot of things.


### Less key directories

- `help_files` contains html help that is used in the GUIs.

- `setup_scripts` contains scripts that are used in created standalone releases of the GUIs for Mac, Windows, and Linux.

- `bin` contains some scripts that are used in creating the Anaconda part of a pip release.

- `build`, `dist`, `pmagpy.egg_info` and `pmagpy_cli.egg_info` are not in the main Github repo, however they may be created automatically when making a pip release.  You should not need to interact directly with any of them.

Here is a visual representation of the directory structure:

```
├── PmagPy_online
├── SPD
│   ├── lib
│   └── tests
├── bin
├── data_files
│   └── notebooks
├── dialogs
│   └── help_files
├── help_files
├── locator
├── pmag_env
├── pmagpy
│   ├── data_model
│   ├── field_models
│   ├── mapping
│   └── test
├── pmagpy_tests
│   └── examples
├── programs
│   ├── conversion_scripts
│   ├── conversion_scripts2
│   ├── deprecated
│   └── images
└── setup_scripts
```

## Git protocols

For an open source project with multiple contributors, it is especially important for changes to be well and clearly documented.  Your reasoning for a certain change may be clear to you, but might need a little extra explanation for someone else.  Here are some basic guidelines to keep in mind.

- Commits should have descriptive names that briefly explain what was done and why.  "Edited file1.py" is a bad commit name!

- If your commit directly fixes [Github issue](https://github.com/PmagPy/PmagPy/issues) 100, it is useful to include "Fixes #100" in the text of the commit.  This syntax both closes the issue and links the issue to the commit for future reference.   However, commit names should always include more detail that just “Fixes #100” - additional context means that the commit message can stand alone.

- Commits should deal with one concern at a time — spanning multiple files is fine, but commits with many unrelated changes are confusing and should be broken up. This makes it easier for someone else to understand what happened, and if something broke in a particular commit it is easier to track it down if the changes are more isolated.

- If you are making a large change that will take multiple commits to implement, it is best to start a feature/fix branch.  Once the feature or fix is done, the changes can be merged into master without breaking core functionality in the meantime.

- Here is a nifty article with some fun [Github keyboard shortcuts](https://help.github.com/articles/using-keyboard-shortcuts/) to let you navigate around Github quickly and easily.

If you are left with any questions about git and Github best practices, go ahead and make a new [Github issue](https://github.com/PmagPy/PmagPy/issues) and we will try to get it worked out!

## Compile and Release Guide

PmagPy ships in two forms, released on different cadences:

- __pip packages__ (`pmagpy` and `pmagpy-cli`) — released several times per year. The full process is documented in [pip_README.md](pip_README.md): prerequisites, pre-release testing on Colab from a feature branch, the build/upload commands for both packages, the optional TestPyPI rehearsal, and tagging plus GitHub release.

- __Standalone GUI executables__ (Windows, Mac, Linux) — released less frequently. See the [setup_scripts README](https://github.com/PmagPy/PmagPy/tree/master/setup_scripts) for the build process.

## Resources

### PmagPy-specific resources

Detailed information about installing and running all of the [PmagPy programs](https://earthref.org/PmagPy/cookbook/)

### The larger world of MagIC and paleomagnetism

The [MagIC database](https://earthref.org/MagIC/)

Lisa Tauxe's [Essentials of Paleomagnetism](https://earthref.org/MagIC/books/Tauxe/Essentials/)

### Programming resources

Learn [Python for Earth Sciences](https://github.com/ltauxe/Python-for-Earth-Science-Students)

Learn the basics of [Python](http://cscircles.cemc.uwaterloo.ca/).

Learn wxPython, which is the basis of our [GUIs here](http://zetcode.com/wxpython/)

Learn more about [git here](https://www.codeschool.com/courses/try-git).
