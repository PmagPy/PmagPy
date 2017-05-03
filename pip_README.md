# Making pip releases

This documentation will walk through making a pip release of pmagpy and pmagpy-cli.

I will explain how to create a Python 2 release and a Python 3 release, although for the most part the Python 2 branch should only be updated with urgent bug fixes from now on.  If no fixes have been made for the Python 2 branch, you can skip the Python 2 version release steps.

## Permissions & Requirements

In order to make a pip release, you must have a PyPI account, and be added to pmagpy and pmagpy-cli as a maintainer. You will need to have PmagPy up to date, Python 2 and 3.  You will also need to install an additional pip package: `pip install wheel`.

## Making a release

### Prepare for new release

- Test current code

- Increment version \# in pmagpy/version.py

### Do Python 2 version release

- Switch to Python2 branch, with Python 2 as your default python

- Create and upload pmagpy to test site (sdist and wheel):
`python setup.py sdist bdist_wheel upload -r https://testpypi.python.org/pypi`

- Download and install pmagpy from test site:
`pip install -i https://testpypi.python.org/pypi pmagpy --upgrade --no-deps --force-reinstall --no-cache-dir`

- Create and upload pmagpy-cli to test site (sdist and wheel):
`python command_line_setup.py sdist bdist_wheel upload -r https://testpypi.python.org/pypi`

- Download and install pmagpy-cli from test site:
`pip install -i https://testpypi.python.org/pypi pmagpy-cli --upgrade --no-deps --force-reinstall --no-cache-dir`

- Once you are satisifed that the test packages are working, you can build and upload to PyPI

- Create and upload pmagpy to real PyPI (sdist and wheel) `rm -rf build dist && python setup.py sdist bdist_wheel && twine upload dist/*`

- Install pmagpy from PyPI
`pip install pmagpy --upgrade --no-deps --force-reinstall --no-cache-dir`

- Create and upload pmagpy-cli to real PyPI (sdist and wheel) `rm -rf build dist && python command_line_setup.py sdist bdist_wheel && twine upload dist/*`

- Install pmagpy-cli from PyPI `pip install pmagpy-cli --upgrade --no-deps --force-reinstall --no-cache-dir`

- Troubleshooting note: If you have a dev install, you may have to remove that install first.  Running `python dev_install.py uninstall` should do the trick.

### Do Python 3 version release

- Switch to master branch, with Python 3 as your default Python

- Create and upload to test site (wheel only):
`python setup.py bdist_wheel upload -r https://testpypi.python.org/pypi`

- Download and install from test site:
`pip install -i https://testpypi.python.org/pypi pmagpy --upgrade --no-deps --force-reinstall --no-cache-dir`

- Repeat the above two steps with pmagpy-cli.

- Create and upload pmagpy to real PyPI (wheel only) `rm -rf build dist && python setup.py bdist_wheel && twine upload dist/*`

- Install pmagpy from PyPI
`pip install pmagpy --upgrade --no-deps --force-reinstall --no-cache-dir`

- Create and upload pmagpy-cli to real PyPI (wheel only) `rm -rf build dist && python command_line_setup.py bdist_wheel && twine upload dist/*`

- Install pmagpy-cli from PyPI `pip install pmagpy-cli --upgrade --no-deps --force-reinstall --no-cache-dir`

- Troubleshooting note: If you have a dev install, you may have to remove that install first.  `dev_install.py uninstall` should do the trick.


## Wheels vs. sdist, and Python 2 vs. Python 3

Pip will preferentially download and install a wheel if it is available for your package.  Pip detects which verison of Python you are using, and downloads the correct wheel for your system.  If you try to upgrade a package, you will get the most recent compatible release.  So, if we have a Python 3 pmagpy 4.0.0, and a Python 2 pmagpy 3.9.1, a user with Python 2 who runs `pip install pmagpy --upgrade` will be updated only to pmagpy 3.9.1.

Most of the time, using wheels allows us to maintain Python 2 and Python 3 compatibility quite easily.  However, pip will sometimes use sdist as a backup, so it is important to continue creating a "standard distribution".

Our current strategy is: creating a wheel for Python 3 and a wheel for Python 2, as well as a backup sdist which will be compatible with Python 2.  Eventually, we will switch that default.
