from setuptools import setup, find_packages
import os
from os import path
import glob
from pmagpy import version

version_num = version.version.strip('pmagpy-')
packages = find_packages(exclude=['programs', 'pmagpy_tests',
                                  'programs.conversion_scripts',
                                  'programs.conversion_scripts2',
                                  'pmagpy_tests.examples', 'pmag_env',
                                  'pmagpy_tests.examples.my_project',
                                  'pmagpy_tests.examples.empty_dir',
                                  'pmagpy_tests.examples.my_project_with_errors'])
packages.append('pmag_env')


def do_walk(data_path):
    """
    Walk through data_files and list all in dict format
    """
    data_files = {}
    def cond(File, prefix):
        """
        Return True for useful files
        Return False for non-useful files
        """
        file_path = path.join(prefix, 'data_files', File)
        return (not File.startswith('!') and
                not File.endswith('~') and
                not File.endswith('#') and
                not File.endswith('.pyc') and
                not File.startswith('.') and
                path.exists(path.join(prefix, File)))

    for (dir_path, dirs, files) in os.walk(data_path):
        data_files[dir_path] = [f for f in files if cond(f, dir_path)]
        if not dirs:
            continue
        else:
            for Dir in dirs:
                do_walk(path.join(dir_path, Dir))
    return data_files

def parse_dict(dictionary):
    formatted = []
    formatted_dict = {}
    for key in list(dictionary.keys()):
        files = dictionary.pop(key)
        formatted_files = [path.join(key, f) for f in files]
        ind = key.index('data_files') + len('data_files/')
        new_key = key[ind:]
        new_key = os.path.join('data_files', new_key)
        formatted.append((new_key, formatted_files))
        formatted_dict[new_key] = formatted_files
    return formatted, formatted_dict

data_files = do_walk('data_files')
formatted, formatted_dict = parse_dict(data_files)
# add notebooks
notebooks = glob.glob("*.ipynb")
for notebook in notebooks:
    formatted.append(('data_files', [notebook]))


# skip the html header at the top of README.md
with open('README.md', encoding='utf-8') as f:
    lines = f.readlines()[14:]
    long_description = "\n".join(lines)


setup(
    name='pmagpy',
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
        'numpy',
        'scipy',
        'matplotlib',
        'pandas',
        'pytz',
        'packaging',
    ],

    # cartopy and shapely are only needed for map-making.
    # The library imports both lazily and degrades gracefully without them.
    # Install with: pip install pmagpy[maps]
    extras_require={
        'maps': ['cartopy', 'shapely'],
    },

    packages=packages,
    include_package_data=True,
    data_files=formatted,

    entry_points={
        'console_scripts': [
            'pmagpy=pmagpy:main',
        ],
    },
)
