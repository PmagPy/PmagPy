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
  - GUI programs for getting data into MagIC database format (pmag\_gui), analyzing demagnetization data (demag\_gui) and analyzing paleointensity data (thellier\_gui). These GUIs are available as part of the python package pmagpy-cli.  Alternatively, these GUIs are available for download as standalone applications for [macOS](https://github.com/PmagPy/PmagPy-Standalone-OSX/releases/latest) and [Windows](https://github.com/PmagPy/PmagPy-Standalone-Windows/releases/latest).
  - Command line programs for all sorts of paleomagnetic data analysis and wrangling (contained within the programs folder of the repository and pip installed as pmagpy-cli).
  - The pmagpy function modules for paleomagnetic data analysis (pmagpy.pmag) and plotting (pmagpy.pmagplotlib) as well as a function module that further enables paleomagnetic data analysis within interactive computing environments such as the Jupyter notebook (pmagpy.ipmag). The functions within these modules are at the heart of the GUI and command line programs. With pmagpy installed ([described below](#how-to-get-it)), these modules can be imported (e.g. `from pmagpy import ipmag`).
  - A rock magnetism module (pmagpy.rockmag) for processing and interpreting hysteresis, backfield, FORC, low-temperature, thermomagnetic, and anisotropy experiments, demonstrated in the [RockmagPy notebooks](https://pmagpy.github.io/RockmagPy-notebooks).
  - Example data files that are used in the examples provided in the [PmagPy documentation notebooks](https://pmagpy.github.io/PmagPy-docs/documentation_notebooks/PmagPy_introduction.html)

Use of all these features is described in the [PmagPy documentation](https://pmagpy.github.io/PmagPy-docs/) and the underlying science behind the data and code can be explored in the book [Essentials of Paleomagnetism: Third Web Edition](http://earthref.org/MagIC/books/Tauxe/Essentials/). Example Jupyter notebooks using PmagPy can be found in this [repository](https://github.com/PmagPy/2016_Tauxe-et-al_PmagPy_Notebooks)

## How to get it

Full instructions for installing and using PmagPy are in the [PmagPy documentation](https://pmagpy.github.io/PmagPy-docs/installation/PmagPy_install.html). You don't need a programming background to follow them. In brief:

| I want to... | Do this |
|---|---|
| Use Pmag GUI, Demag GUI, or Thellier GUI, and nothing else | Download the standalone application for [macOS](https://github.com/PmagPy/PmagPy-Standalone-OSX/releases/latest) or [Windows](https://github.com/PmagPy/PmagPy-Standalone-Windows/releases/latest) (no Python needed) |
| Try PmagPy without installing anything | Use the [EarthRef JupyterHub](https://pmagpy.github.io/PmagPy-docs/installation/PmagPy_install.html#using-pmagpy-online), or run `%pip install pmagpy` in a Google Colab notebook |
| Use PmagPy in Jupyter notebooks, run the command-line programs, or run the GUIs on Linux | [Install PmagPy on your computer](https://pmagpy.github.io/PmagPy-docs/installation/pip_install.html) with conda and pip |
| Contribute to PmagPy, or use changes before they are released | Do a [developer install](https://pmagpy.github.io/PmagPy-docs/installation/developer_install.html) |

### Install on your computer

The recommended approach uses [Miniforge](https://github.com/conda-forge/miniforge) to create a conda environment with the scientific Python packages, and then pip to install PmagPy. With Miniforge installed, run these commands in a terminal (on Windows, in Miniforge Prompt):

```
conda create -n pmagpy -c conda-forge python=3.12 numpy scipy matplotlib pandas cartopy shapely wxpython pyqt jupyterlab pip
conda activate pmagpy
pip install --upgrade pmagpy pmagpy-cli
```

`pmagpy` contains the function modules used in Jupyter notebooks and your own code; `pmagpy-cli` adds the command-line programs and the GUIs. To update later, activate the environment and rerun the last command. The [installation guide](https://pmagpy.github.io/PmagPy-docs/installation/pip_install.html) explains each step, and the [troubleshooting page](https://pmagpy.github.io/PmagPy-docs/installation/troubleshooting.html) covers common problems.

### Developer install

To work from the source code (the master branch or your own fork) rather than a release, clone the repository, create an environment from its `environment.yml`, and install it in editable mode:

```
git clone https://github.com/PmagPy/PmagPy.git
cd PmagPy
conda env create -f environment.yml -n pmagpy-dev
conda activate pmagpy-dev
pip install -e ".[maps]"
```

Edits to the code, and `git pull`, take effect immediately without reinstalling. The command-line programs and GUIs can be run from the `programs` directory (for example, `python pmag_gui.py`), or installed from the released `pmagpy-cli` package alongside the editable library. Full details are in the [developer install instructions](https://pmagpy.github.io/PmagPy-docs/installation/developer_install.html).


## Background and support

The code base for the PmagPy project has been built up over many years by Lisa Tauxe (Professor Emerita at the Scripps Institution of Oceanography) supported by grants from the National Science Foundation. Substantial contributions to the project have been made by Nick Swanson-Hysell (Associate Professor at the University of Minnesota), Ron Shaar (Associate Professor at the Hebrew University of Jerusalem), Lori Jonestrask and Kevin Gaastra as well as others.

## Contributing

If you want to get involved with the project - whether that means reporting a bug, requesting a feature, or adding significant code - please check out the project's [Contribution guidelines](https://github.com/PmagPy/PmagPy/blob/master/CONTRIBUTING.md).

## More information

This code and the [PmagPy documentation](https://pmagpy.github.io/PmagPy-docs/) are companions to the the book Essentials of Paleomagnetism: Third Web Edition (http://earthref.org/MagIC/books/Tauxe/Essentials/) written by Lisa Tauxe with contributions from Subir K. Banerjee, Robert F. Butler and Rob van der Voo. The printed version of the book came out in January, 2010 from University of California Press (http://www.ucpress.edu/book.php?isbn=9780520260313).

## Licensing

This code can be freely used, modified, and shared. It is licensed under a 3-clause BSD license. See [license.txt](https://github.com/PmagPy/PmagPy/blob/master/license.txt) for details.
