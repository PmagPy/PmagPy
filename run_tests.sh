#!/bin/bash

#pythons=('python3' 'pythonw')
#for py_exec in ${pythons[@]}; do
#    # get full path to python version
#    py_exec="$(which $py_exec)"
#    # find what version of python it is
#    output="$($py_exec --version 2>&1)"
#    # determine if version is Python 3
#    if [[ ${output} == *"Python 3"* ]]; then
#        use_this_python=$py_exec
#    fi
#done

#$use_this_python="$(which python)"

echo Do Test Simple Example
pythonw -m unittest -v pmagpy_tests.test_simple_example
echo Do Test Pmag GUI
pythonw -m unittest -v pmagpy_tests.test_pmag_gui
echo Do Test Pmag
pythonw -m unittest -v pmagpy_tests.test_pmag
echo Do Test Imports2
pythonw -m unittest -v pmagpy_tests.test_imports2
echo Do Test Imports3
pythonw -m unittest -v pmagpy_tests.test_imports3
echo Do Test Ipmag
pythonw -m unittest -v pmagpy_tests.test_ipmag
echo Do Test Thellier GUI
pythonw -m unittest -v pmagpy_tests.test_thellier_gui
echo Do Test Demag GUI
pythonw -m unittest -v pmagpy_tests.test_demag_gui
echo Do Test Magic GUI
pythonw -m unittest -v pmagpy_tests.test_magic_gui
echo Do Test Builder
pythonw -m unittest -v pmagpy_tests.test_builder
echo Do Test Validations
pythonw -m unittest -v pmagpy_tests.test_validations
#echo Do Test Programs
#pythonw -m unittest -v pmagpy_tests.test_programs
echo Do Test Magic GUI 2
pythonw -m unittest -v pmagpy_tests.test_magic_gui2
echo Do Test New Builder
pythonw -m unittest -v pmagpy_tests.test_new_builder
echo Do Test Er Magic Dialogs
pythonw -m unittest -v pmagpy_tests.test_er_magic_dialogs
echo Do Test Find Pmag Dir
pythonw -m unittest -v pmagpy_tests.test_find_pmag_dir
echo Do Test Map Magic
pythonw -m unittest -v pmagpy_tests.test_map_magic
echo Do Test Dialog Components
pythonw -m unittest -v pmagpy_tests.test_dialog_components
