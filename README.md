## What is it

**PmagPy** is a comprehensive set of tools for analyzing paleomagnetic data. It facilitates interpretation of demagnetization and Thellier-type experimental data and can create a wide variety of useful plots. It is designed to work with the MagIC database (https://earthref.org/MagIC), allowing manipulation of downloaded data sets as well as preparation of new contributions for uploading to the MagIC database. It also supports the use of IPython/Jupyter notebooks for fully documented and nicely illustrated data analysis.

## How to use it

Full documentation for PmagPy installation and use is available in the PmagPy cookbook: http://earthref.org/PmagPy/cookbook

To get started:
- download a zip file of the latest release here: https://github.com/ltauxe/PmagPy/releases/latest. Click on "Source code (zip)" or "Source code (tar.gz)" to download. 
- To install the software on a Mac or a PC, unzip the downloaded folder and double-click on the install script for your system. 
- Linux and advanced users on Mac and PCs can either clone the repository or download the latest release and then add the directory of the main repository folder (and the program directory for access to the command line programs) to their path and pythonpath. On a Mac, this can be done by adding these lines to the bash_profile: ```export PATH=~/PmagPy:./:$PATH```; ```export PATH=~/PmagPy/programs:./:$PATH```; ```export PYTHONPATH=$PYTHONPATH:~/PmagPy```

## Main features

PmagPy is comprised of:
  - GUI programs for getting data into MagIC database format (pmag_gui), analyzing demagnetization data (demag_gui) and analyzing paleointensity data (thellier_gui). These GUIs are also availible for download as executable programs outside of this repository: 
    - [Mac PmagPy Executable Application](https://github.com/PmagPy/PmagPy-Standalone-OSX) 
    - [Windows PmagPy Executable Application](https://github.com/PmagPy/PmagPy-Standalone-Windows)
  - Command line programs for all sorts of paleomagnetic data analysis and wrangling (contained within the programs folder of the repository).
  - The pmagpy function module for paleomagnetic data analysis (pmagpy.pmag) and plotting (pmagpy.pmagplotlib) as well as a function module that further enables paleomagnetic data analysis within interactive computing environments such as the Jupyter notebook (pmagpy.ipmag). The functions within this modules are at the heart of the GUI and command line programs. With pmagpy in the python path (which is accomplished with the install scripts), these modules are can be imported (e.g. ```import pmagpy.ipmag as ipmag```).
  - Example data files that are used in the examples provided in the PmagPy cookbook http://earthref.org/PmagPy/cookbook
  
Use of all these features is described in the cookbook and the underlying science behind the data and code can be explored in the book Essentials of Paleomagnetism: Third Web Edition (http://earthref.org/MagIC/books/Tauxe/Essentials/).

## Background and support

The code base for the PmagPy project has been built up over many years by Lisa Tauxe (Distinguished Professor of Geophysics at the Scripps Institution of Oceanography) supported by grants from the National Science Foundation. Ron Shaar (Senior Lecturer at the Hebrew University of Jerusalem), Lori Jonestrask and Nick Swanson-Hysell (Assistant Professor at UC Berkeley) have also made substantial contributions to the project.

## More information

This code and the PmagPy cookbook (http://earthref.org/PmagPy/cookbook) are companions to the the book Essentials of Paleomagnetism: Third Web Edition (http://earthref.org/MagIC/books/Tauxe/Essentials/) written by Lisa Tauxe with contributions from Subir K. Banerjee, Robert F. Butler and Rob van der Voo. The printed version of the book came out in January, 2010 from University of California Press (http://www.ucpress.edu/book.php?isbn=9780520260313).

## Licensing

This code can be freely used, modified, and shared. It is licensed under a 3-clause BSD license. See [license.txt](https://github.com/ltauxe/PmagPy/blob/master/license.txt) for details.  
