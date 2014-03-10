#! /bin/bash

# making sure all files are created afresh
rm old_all_errors.txt   # removes list of errors from two rounds of testing ago
mv all_errors_list.txt old_all_errors.txt # renames the previous test result as the 'old' test result
rm *new.out*  # removes all output files from the last round of testing
rm *full_output.txt*  # removes long files with stdout from tests
rm *clean_output.txt* # removes shorter files with shortened stdout from tests
rm *errors_list.txt* # removes files with a list of the problem programs

python Bootstrap.py > bootstrap_full_output.txt
echo "finished Bootstrap.py"
python Extra_output.py > extra_out_full_output.txt
echo "finished Extra_output.py"
python Random.py > random_full_output.txt
echo "finished Random.py"
python Rename_me.py > rename_me_full_output.txt
echo "finished Rename_me"
python clean_log_output.py -all
echo "ran clean_log_output.py -all"

cat bootstrap_errors_list.txt rename_me_errors_list.txt random_errors_list.txt extra_output_errors_list.txt > all_errors_list.txt  

echo "concatenated bootstrap_errors_list, rename_me_errors_list, random_errors_list, and extra_output_errors_list into: all_errors_list.txt"

echo "see rename_me_clean_output.txt, random_clean_output.txt, bootstrap_clean_output.txt, and extra_out_clean_output.txt for logs of the problem programs."  

