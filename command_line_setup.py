from __future__ import print_function
import sys
if sys.version_info < (3,):
    raise Exception("""
You are running Python {}.
This version of pmagpy-cli is only compatible with Python 3.
Make sure you have pip ≥ 9.0 to avoid this kind of issue,
as well as setuptools ≥ 24.2:

 $ pip install pip setuptools --upgrade

Then you should be able to download the correct version of pmagpy-cli:

 $ pip install pmagpy-cli --upgrade

If this still gives you an error, please report the issue:
https://github.com/PmagPy/PmagPy/issues

Thanks!

""".format(sys.version))
# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path
from setuptools.command.install import install
from pmagpy import version


#import glob
# Get list of programs to alias
from programs_list import programs_list

version_num = version.version.strip('pmagpy-')
here = path.abspath(path.dirname(__file__))

#packages = find_packages(exclude=['pmagpy', 'pmagpy_tests', 'pmagpy_tests.examples'
#                                  'SPD', 'pmag_env'])
#print('packages', packages)


# Get the long description from the README file
#with open(path.join(here, 'README.md'), encoding='utf-8') as f:
#    long_description = f.read()

# skip the html part
with open('README.md', encoding='utf-8') as f:
    lines = f.readlines()[14:]
    long_description = "\n".join(lines)



class CustomInstall(install):

    def run(self):
        install.run(self)
        # custom stuff here

setup(
    #cmdclass={'install': CustomInstall},

    name='pmagpy-cli',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version_num,

    description='Analysis tools for paleo/rock magnetic data',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/PmagPy/PmagPy',

    # Author details
    author='PmagPy team',
    author_email='ltauxe@ucsd.edu',

    # Choose your license
    license='BSD-3',

    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        #'Intended Audience :: Geologists',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='geology paleomagnetism',

    # won't install if user has python 2
    python_requires='>=3.4',


    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['pmagpy', 'pmagpy_tests.examples'
                                    'SPD', 'pmag_env', 'pmagpy_tests']), # tests


    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    #install_requires=['numpy', 'matplotlib'],
    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    #extras_require={
    #            'dev': ['check-manifest'],
    #            'test': ['coverage'],
    #        },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    include_package_data=True,
    #package_data={
    #            'images': glob.glob('images/*'),
    #        },
    #package_data=formatted_dict,

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    #data_files=[('pmag_data_files', glob.glob('data_files/*/*.*'))],
    #data_files=formatted,


            #data_files=[('bitmaps', ['bm/b1.gif', 'bm/b2.gif']),
            #                              ('config', ['cfg/data.cfg']),
            #                              ('/etc/init.d', ['init-script'])]
            # )
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    #entry_points={
    #            #'console_scripts': [
    #            #                'angle=programs.angle:main',
    #            #                'angle2.py=programs.angle:main',
    #            #            ],
    #            'console_scripts': programs_list
    #        },
    scripts=['bin/pmag_gui_anaconda', 'bin/magic_gui_anaconda',
             'bin/magic_gui2_anaconda', 'bin/thellier_gui_anaconda',
             'bin/demag_gui_anaconda', 'bin/core_depthplot_anaconda',
             'bin/ani_depthplot_anaconda'],
    entry_points={
            'console_scripts': programs_list,
            'gui_scripts': [
                    'magic_gui.py = programs.magic_gui:main',
                    'pmag_gui.py = programs.pmag_gui:main',
                    'demag_gui.py = programs.demag_gui:main',
                    'thellier_gui.py = programs.thellier_gui:main',
                    'pmag_gui = programs.pmag_gui:main',
                    'magic_gui2.py = programs.magic_gui2:main',
                    'magic_gui = programs.magic_gui:main',
            ]

    }
)
