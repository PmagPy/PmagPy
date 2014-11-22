:: -----------------------------------------------------------------------------
:: Installation test script for Lisa Tauxe's PmagPy Python Package
:: Written by Rupert C. J. Minnett, Ph.D.
:: Last updated 11/17/2014
:: -----------------------------------------------------------------------------

:: Change to the drive's root directory to test outside of the installation directory
cd \

:: Execute a test of the PmagPy package
eqarea.py -h

:: Prompt the user to check the output of the previous command
@ECHO OFF
ECHO --------------------------------------------------------------------------------
ECHO If PmagPy installed correctly, you should see the help instructions for the
ECHO eqarea.py program above.                                                        
ECHO --------------------------------------------------------------------------------

:: Keep the console open
PAUSE > NUL