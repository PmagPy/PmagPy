#!/bin/sh -e

# Run a PmagPy program using the syntax:
# wrapper.sh program_name.py [command line options]
# e.g.
# wrapper.sh angle.py -h

# make sure a program name was provided
prog_name="$1"
if [ -z "$prog_name" ]; then
    echo "-I- You have not provided a PmagPy program name, defaulting to open Pmag GUI"
    echo '-I- If you want to invoke a different program, correct usage is pmag_gui.sh pmagpy_program.py'
    prog_name="pmag_gui.py"
fi

echo $prog_name

# try pythonw first, then python
pythons=('pythonw' 'python')
for py_exec in ${pythons[@]}; do
    echo $py_exec
    # get full path to python version
    py_exec="$(which $py_exec)"
    echo $py_exec
    # find what version of python it is
    output="$($py_exec --version 2>&1)"
    is_3=false
    # determine if version is Python 3
    if [[ ${output} == *"Python 3"* ]]; then
        is_3=true
    fi
    # if we found Python 3, execute the program
    if "$is_3"; then
        echo $is_3
        if [[ -f $py_exec ]]; then
            echo $py_exec
            # get full program name
            echo partial prog name
            echo $prog_name
            prog_name="$(which $prog_name)"
            echo full prog name
            echo $prog_name
            # find number of args
            num_args="$#"
            echo num_args
            echo $num_args
            # grab all args after the first two
            use_args=${@:2:$num_args}
            echo 'executing:' $py_exec $prog_name $use_args
            # execute the program
            exec $py_exec $prog_name $use_args
            exit
        else
            echo 'cannot execute' $py_exec $1
        fi
    fi
done

# useful bash pieces:

# get last character:
#stringZ=abcABC123ABCabc
#echo ${stringZ: -1}

# get string length
#stringZ=abcABC123ABCabc
#val=${#stringZ}
#echo $val

# evaluate numeric expressions
#echo $((1+1))

# find if substring is included in string
#testmystring='hello'
#echo $testmystring
#if [[ ${testmystring} == *"c0"* ]]; then
#    echo 'is in'
#else
#    echo 'not in'
#fi

# assign bash output to a variable
#OUTPUT="$(ls -1)"
#echo "${OUTPUT}"
#output="$(which python)"
#echo $output

# length of array
#a=(1 2 3 4)
#echo ${#a[@]}
