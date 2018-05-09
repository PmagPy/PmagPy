#### You will need to follow the regular PmagPy install instructions from the [Cookbook](https://earthref.org/PmagPy/cookbook), except for installing wxPython.  This includes:

- Download and install Anaconda Python
- Install PmagPy Python dependencies
- Download the PmagPy directory

For complete and up to date instructions, please see the [Cookbook](https://earthref.org/PmagPy/cookbook), except for installing wxPython.

#### This is a list of some additional dependencies for Linux on Ubuntu 16.04 (there may be redundancies or missing steps, depending on your specific OS):

    pip install libtiff

    sudo apt-get install libgtk-3-dev freeglut3-dev libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-doc gstreamer1.0-tools libgstreamer-plugins-base0.10-dev libjpeg libpng libtff libsdl libnotify libsm

    sudo apt-get install dpkg-dev build-essential libjpeg-dev  libtiff-dev libsdl1.2-dev   libnotify-dev  freeglut3 freeglut3-dev libsm-dev libwebkitgtk-3.0-dev libxtst-dev python-dev libpng-dev

    sudo apt-get install libwebkit2gtk-4.0-dev libsdl2-dev

#### Install wxPython according to these instructions:

https://github.com/wxWidgets/Phoenix/blob/master/README.rst#how-to-build-phoenix

https://github.com/wxWidgets/Phoenix/blob/e13273c5d939d993abf2a2649e90b3ea0d39382c/packaging/README-bdist.txt#L38-L57

#### Then, try to import wx.  if you can't import wx:

You may have an error like this:

    ImportError: libwx_gtk3u_core-3.0.so.0: cannot open shared object file: No such file or directory

If so, try:

    export LD_LIBRARY_PATH=~/anaconda3/lib/python3.6/site-packages/wx/

And checkout [this blog post](https://wxpython.org/blog/2017-08-17-builds-for-linux-with-pip/) and this [issue](https://github.com/pyenv/pyenv/issues/691) for more information.

#### Deal with pythonw/python issue:

    ln -s ~/anaconda3/bin/python3 ~/anaconda3/bin/pythonw

#### At this point, you should be able to run all PmagPy programs on the command line.

#### To run pyinstaller:

    rm -rf build dist && LD_LIBRARY_PATH=/home/parallels/anaconda3/lib pyinstaller pmag_gui.spec
