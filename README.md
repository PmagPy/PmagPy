# PmagPy: tools for paleomagnetic data analysis

<table>
<tr>
  <td>Latest Release</td>
  <td><img src="https://img.shields.io/pypi/v/pmagpy.svg" alt="latest release" /></td>
</tr>
<tr>
  <td>License</td>
  <td><img src="https://img.shields.io/pypi/l/pmagpy.svg" alt="license" /></td>
</tr>
</table>

## What is it

**PmagPy** is a comprehensive set of tools for analyzing paleomagnetic data. It facilitates interpretation of demagnetization data, Thellier-type experimental data and data from other types of rock magnetic experiments. PmagPy can be used to create a wide variety of useful plots and conduct statistical tests. It is designed to work with the MagIC database (https://earthref.org/MagIC), allowing manipulation of downloaded data sets as well as preparation of new contributions for uploading to the MagIC database. Functions within PmagPy can be imported and used in Jupyter notebooks enabling fully documented and nicely illustrated data analysis.

## Citing PmagPy

Users of PmagPy should cite the open access article:

Tauxe, L., R. Shaar, L. Jonestrask, N. L. Swanson-Hysell, R. Minnett, A. A. P. Koppers, C. G. Constable, N. Jarboe, K. Gaastra, and L. Fairchild (2016), PmagPy: Software package for paleomagnetic data analysis and a bridge to the Magnetics Information Consortium (MagIC) Database, Geochem. Geophys. Geosyst., 17, https://doi.org/10.1002/2016GC006307.

## Main features

PmagPy is comprised of:
  - GUI programs for getting data into MagIC database format (pmag\_gui), analyzing demagnetization data (demag\_gui) and analyzing paleointensity data (thellier\_gui). These GUIs are available as part of the python package pmagpy-cli.  Alternatively, these GUIs are availible for download as [executable programs](#stand-alone-applications) outside of this repository.
  - Command line programs for all sorts of paleomagnetic data analysis and wrangling (contained within the programs folder of the repository and pip installed as pmagpy-cli).
  - The pmagpy function modules for paleomagnetic data analysis (pmagpy.pmag) and plotting (pmagpy.pmagplotlib) as well as a function module that further enables paleomagnetic data analysis within interactive computing environments such as the Jupyter notebook (pmagpy.ipmag). The functions within these modules are at the heart of the GUI and command line programs. With pmagpy installed ([described below](#full-pmagpy-install)), these modules are can be imported (e.g. ```from pmagpy import ipmag```).
  - Example data files that are used in the examples provided in the [PmagPy cookbook](http://earthref.org/PmagPy/cookbook)

Use of all these features is described in the [Cookbook](http://earthref.org/PmagPy/cookbook) and the underlying science behind the data and code can be explored in the book [Essentials of Paleomagnetism: Third Web Edition](http://earthref.org/MagIC/books/Tauxe/Essentials/). Example Jupyter notebooks using PmagPy can be found in this [repository](https://github.com/PmagPy/2016_Tauxe-et-al_PmagPy_Notebooks)

## How to get it

There are several different ways to install PmagPy.  Complete documentation for PmagPy installation and use is available in the [PmagPy cookbook](http://earthref.org/PmagPy/cookbook).

You can try a preview of PmagPy here:

[![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/PmagPy/PmagPy-notebooks/master?filepath=PmagPy.ipynb)

Please be patient, the preview will take a few minutes to launch.

### Stand alone applications
If you do not need the full PmagPy functionality, and you only want to use Pmag GUI, MagIC GUI, Thellier GUI, and Demag GUI, there a standalone download for which Python does not need to be installed. Once downloaded, the GUIs should run when you double click on their icon, but they will take time to start up (anywhere from 5 to 30 seconds) please be patient.

#### OSX Standalone download

You’ll find the latest stable release here: [Mac PmagPy Executable Application](https://github.com/PmagPy/PmagPy-Standalone-OSX/releases/latest)

####  Windows Standalone download

You’ll find the latest stable release here: [Windows PmagPy Executable Application](https://github.com/PmagPy/PmagPy-Standalone-Windows/releases/latest)

####  Linux Standalone download

This binary has only been tested on a Ubuntu 14.04 (Trusty) distribution and might experience problems on other distributions.
You’ll find the latest stable release here: [Linux PmagPy Executable Application](https://github.com/PmagPy/PmagPy-Standalone-Linux/releases)

### Full PmagPy install

To get the full use of PmagPy functionality, you will first have to have a Python installation with some standard scientific modules. You can follow instructions to do so [here](https://earthref.org/PmagPy/cookbook/#x1-60001.2). Once you have Python installed:

- Find and open your command line (for help finding your command prompt, see the [documentation](http://earthref.org/PmagPy/#command_line))
- Update pip: type on the command line: ```pip install --upgrade pip```
- Install or update pmagpy: use the command: ```pip install --upgrade pmagpy```
- Install or update pmagpy-cli, use the command: ```pip install --upgrade pmagpy-cli```
- To uninstall, use the commands: ```pip uninstall pmagpy``` and ```pip uninstall pmagpy-cli```
- If you run into trouble, use pip to uninstall both pmagpy and pmagpy-cli, then try again to install first pmagpy and then pmagpy-cli

If you want access to the master branch rather than the latest release, see the [developer install instructions](https://earthref.org/PmagPy/cookbook/#developer_install).

<!-- Alternatively if you want simply to install the latest under development version without messing with environment variables you can download or clone the repository and run `python setup.py install` and it will use setup tools to install PmagPy somewhere where it is accessible to python and in your path. This, however, does not update your in path version of the library when you update using `git pull origin master` but rather you must update using setup tools manually.-->

## Background and support

The code base for the PmagPy project has been built up over many years by Lisa Tauxe (Distinguished Professor of Geophysics at the Scripps Institution of Oceanography) supported by grants from the National Science Foundation. Substantial contributions to the project have been made by Nick Swanson-Hysell (Assistant Professor at UC Berkeley), Ron Shaar (Senior Lecturer at the Hebrew University of Jerusalem), Lori Jonestrask and Kevin Gaastra as well as others.

## Contributing

If you want to get involved with the project - whether that means reporting a bug, requesting a feature, or adding significant code - please check out the project's [Contribution guidelines](https://github.com/PmagPy/PmagPy/blob/master/CONTRIBUTING.md).

## More information

This code and the PmagPy cookbook (http://earthref.org/PmagPy/cookbook) are companions to the the book Essentials of Paleomagnetism: Third Web Edition (http://earthref.org/MagIC/books/Tauxe/Essentials/) written by Lisa Tauxe with contributions from Subir K. Banerjee, Robert F. Butler and Rob van der Voo. The printed version of the book came out in January, 2010 from University of California Press (http://www.ucpress.edu/book.php?isbn=9780520260313).

## Licensing

This code can be freely used, modified, and shared. It is licensed under a 3-clause BSD license. See [license.txt](https://github.com/ltauxe/PmagPy/blob/master/license.txt) for details.
