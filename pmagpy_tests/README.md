## Testing locally (for developers)

You can run tests from your local PmagPy directory.  (Tests will fail if you try to run them from PmagPy/pmagpy\_tests -- always run them from PmagPy).  To run find and run all tests, use:

`python -m unittest discover`

Annoyingly, running all of the tests like this can cause segfaults (but generally not on Windows!)  Also, the tests will take ~10 minutes to run.  For these reasons, it is often best to just run a subset of the tests -- whatever is relevant to the changes you've made.

To run tests at the most granular level, the syntax looks like this:

`python -m unittest pmagpy_tests.test_ipmag.TestIGRF.test_igrf_output`

This runs a single test from the pmagpy\_tests module, from the test\_ipmag submodule (the file named test\_ipmag.py), from the TestIGRF class.  The individual test is called test\_igrf\_output.  You can also run the entire test\_ipmag submodule:

`python -m unittest pmagpy_tests.test_ipmag`

or all tests in the TestIGRF class:

`python -m unittest pmagpy_tests.test_ipmag.TestIGRF`.

Here is the code that makes the IGRF test run, with comments.

    import unittest
    import os
    from pmagpy import ipmag
    WD = os.getcwd()  # all tests should be designed to run from the main PmagPy directory.
                      # the WD constant allows you to keep track of your working directory
                      # this is important for finding example data files, etc.

    DATA_DIR = os.path.join(WD, 'data_files')


    class TestIGRF(unittest.TestCase):  # group similar tests together at the class level

        def setUp(self):   # the setUp function will run before each test in your class
            self.reference = [1.20288657e+00, 2.82331112e+01, 3.9782338913649881e+04]

        def tearDown(self):  # the tearDown function will run at the end of each test in your class
            os.chdir(WD)   # in this case, I want to make sure we always end up back in our start directory

        def test_igrf_output(self):  # any function in the TestIGRF class that starts with "test_" will be treated as a unittest
            result = ipmag.igrf([1999.1, 30, 20, 50])
            for num, item in enumerate(result):
                self.assertAlmostEqual(item, self.reference[num])   # unittest.TestCase has many helpful assert methods (see linked documentation below)



More documentation about creating and running unittests can be found [here](https://docs.python.org/2/library/unittest.html).
