from setuptools import setup, find_packages
from pmagpy import version
from programs_list import programs_list

version_num = version.version.strip('pmagpy-')

# skip the html header at the top of README.md
with open('README.md', encoding='utf-8') as f:
    lines = f.readlines()[14:]
    long_description = "\n".join(lines)


setup(
    name='pmagpy-cli',
    version=version_num,
    description='Analysis tools for paleo/rock magnetic data',
    long_description=long_description,
    url='https://github.com/PmagPy/PmagPy',
    author='PmagPy team',
    author_email='ltauxe@ucsd.edu',
    license='BSD-3-Clause',

    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],

    keywords='geology paleomagnetism',

    python_requires='>=3.9',

    install_requires=[
        'pmagpy',
        'wxPython',
        'PyQt5',
        'lmfit',
        'pillow',
        'appdirs',
    ],

    # cartopy and shapely are only needed for map-making.
    # Install with: pip install pmagpy-cli[maps]
    extras_require={
        'maps': ['pmagpy[maps]'],
    },

    packages=find_packages(exclude=['pmagpy', 'pmag_env', 'pmagpy_tests']),
    include_package_data=True,

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
        ],
    },
)
