echo StartTests > test_output.log
for test in $(grep -rl --include \*.py "unittest" | grep -v "run_" | xargs); do
path=$(echo $test | cut -f 1 -d '.')
string_to_replace=/
pytest="${path//$string_to_replace/'.'}"
echo "running $pytest"
python3 -m unittest $pytest >> test_output.log
done
