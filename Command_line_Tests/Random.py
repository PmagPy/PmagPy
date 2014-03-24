#! /usr/bin/env python

from scripttest import TestFileEnvironment
env = TestFileEnvironment('./new-test-output')
import unittest
import sys
import PmagPy_tests as PT
import error_logging as EL

file_prefix = PT.file_prefix
directory = PT.directory

def complete_fisher_test():
    """test fisher.py"""
    print "-"
    print "Testing fisher.py"
    print "running: ('fisher.py', '-k', '30', '-n', '10')" 
    obj1 = env.run('fisher.py', '-k', '30', '-n', '10') 
    output1 = obj1.stdout
    length1 = len(output1)
    print "output1: " + str(output1)
    print "length1: " + str(length1)
    print "running:  ('fisher.py', '-k', '30', '-n', '10')"
    obj2 = env.run('fisher.py', '-k', '30', '-n', '10')
    output2 = obj2.stdout
    length2 = len(output2)
    print "output2: " + str(output2)
    print "length2: " + str(length2)
    if length1 == 170 and length1 == length2:
        print "fisher.py produces the right amount of output"
    else:
        print "raising error (wrong length output produced)"
        raise NameError("fisher.py is producing the wrong amount of output")
    if output1 != output2:
        print "fisher.py seems to be producing a random distribution"
    else:
        print "raising error (identical, rather than random, output produced)"
        raise NameError("fisher.py produced identical output twice")
    print "running: fisher.py"
    obj3 = env.run('fisher.py')
    output3 = obj3.stdout
    length3 = len(output3)
    print "output3: " + str(output3)
    print "length3: " + str(length3)
    print "running fisher.py"
    obj4 = env.run('fisher.py')
    output4 = obj4.stdout
    length4 = len(output4)
    print "output4: " + str(output4)
    print "length4: " + str(length4)
    if length3 == length4:
        print "Fisher.py is producing the correct amount of output"
    else:
        raise NameError("fisher.py is producing different amounts of output for the same command")
    if output3 != output4:
        print "Fisher.py appears to be producing a random distribution"
    else:
        raise NameError("fisher.py produced identical output twice")

def complete_fishrot_test():
    """test fishrot.py"""
    print "_"
    print "Testing fishrot.py"
    obj = env.run('fishrot.py', '-h')
    print obj.stdout
    print "running: ('fishrot.py', '-n', '5', '-D', '23', '-I', '41', '-k', '50')"
    obj1 = env.run('fishrot.py', '-n', '5', '-D', '23', '-I', '41', '-k', '50')
    output1 = obj1.stdout
    print "output1: " + str(output1)
    print "Length output1: " + str(len(output1))
    print "Running: ('fishrot.py', '-n', '5', '-D', '23', '-I', '41', '-k', '50')"
    obj2 = env.run('fishrot.py', '-n', '5', '-D', '23', '-I', '41', '-k', '50')
    output2 = obj2.stdout
    print "output2: " + str(output2)
    print "output2: " + str(len(output2))
    # they should be random, thus different
    if output1 != output2:
        print "Fishrot.py appears to be generating a random distribution"
    else:
        raise NameError("Fishrot.py produced identical output twice")
    # but they should be the same length, because of the -n 5 arguments
    if len(output1) == len(output2):
        print "Fishrot.py is producing the correct amount of output"
    else:
        raise NameError("Fishrot.py is producing the wrong amount of output")
    print "running fishrot.py"
    obj3 = env.run('fishrot.py')
    output3 = obj3.stdout
    length3 = len(output3)
    print "output3: " + str(output3) + " length3: " + str(length3)
    print "running: fishrot.py"
    obj4 = env.run('fishrot.py')
    output4 = obj4.stdout
    length4 = len(output4)
    print "output4 :" + str(output4) + " length4: " + str(length4)
    if output3 != output4:
        print "Fishrot.py distributions appear to be random"
    else:
        raise NameError("Fishrot.py produced identical output twice in a row")
    if length3 == length4:
        print "Fishrot.py appears to be producing the right amount of output"
    else:
        raise NameError("Fishrot.py is not producing the right amount of output")

def complete_tk03_test():
    """test tk03.py"""
    obj = env.run('tk03.py', '-h')
    print obj.stdout
    print "running tk03.py"
    obj1 = env.run('tk03.py')
    out1 = str(obj1.stdout).split()
    print "output1: " + str(out1)
    print "running tk03.py"
    obj2 = env.run('tk03.py')
    out2 = str(obj2.stdout).split()
    print "output2: " + str(out2)
    if out1 == out2:
        raise NameError("tk03.py produced non-random output")
    if len(out1) != len(out2):
        raise NameError("lengths should have been the same")
    print "tk03 produced random distributions with default options"
    print "running ('tk03.py', '-lat', '30', '-N', '50')"
    obj3 = env.run('tk03.py', '-lat', '30', '-N', '50')
    out3 = str(obj3.stdout).split()
    print "output3: " + str(out3)
    print "running ('tk03.py', '-lat', '30', '-N', '50')"
    obj4 = env.run('tk03.py', '-lat', '30', '-N', '50')
    out4 = str(obj4.stdout).split()
    print "output4: " + str(out4)
    if out3 == out4:
        raise NameError("tk03.py produced non-random output")
    if len(out3) != len(out4):
        raise NameError("lengths should have been the same")
    print "tk03 produced random distributions with -lat 30, -N 50"

def complete_uniform_test():
    """test uniform.py"""
    obj = env.run('uniform.py', '-h')
    print "running: uniform.py"
    obj1 = env.run("uniform.py")
    out1 = str(obj1.stdout).split()
    print "output1: " + str(out1)
    print "running: uniform.py"
    obj2 = env.run("uniform.py")
    out2 = str(obj2.stdout).split()
    print "output2: " + str(out2)
    if out1 == out2:
        raise NameError( "uniform.py produced non-random output")
    if len(out1) != len(out2):
        raise NameError( "uniform.py produced the wrong amount of output")
    print "uniform.py ran correctly with default options"
    print "running: ('uniform.py', '-N', '50')"
    obj3 = env.run("uniform.py", '-N', '50')
    out3 = str(obj3.stdout).split()
    print "output3: " + str(out3)
    print "running: ('uniform.py','-N', '50')"
    obj4 = env.run("uniform.py","-N", "50")
    out4 = str(obj4.stdout).split()
    print "output4: " + str(out4)
    if out3 == out4:
        raise NameError( "uniform.py produced non-random output")
    if len(out3) != len(out4):
        print len(out3), len(out4)
        raise NameError( "uniform.py produced the wrong amount of output")
    print "uniform.py ran correctly with -N 50"

def complete_gaussian_test():
    """test gaussian.py"""
    print "-"
    print "Testing gaussian.py"
    obj = env.run('gaussian.py', '-h')
    print obj.stdout
    print "running: " + ' gaussian.py', '-s', '3', '-n', '100', '-m', '10.', '-F', 'gauss.out'
    obj1 = env.run('gaussian.py', '-s', '3', '-n', '100', '-m', '10.', '-F', 'gauss.out')
    output1 = obj1.stdout
    o1 = len(output1.split())
    print "output1: "+ str(output1)
    print("output 1 length: ", o1)
    print "output1 files_created: " + str(obj1.files_created)
    print "running + ('gaussian.py', '-s', '3', '-n', '95', '-m', '10.')"
    obj2 = env.run('gaussian.py', '-s', '3', '-n', '95', '-m', '10.')
    output2 = obj2.stdout
    o2 = len(output2.split())
    print "output2: "+ str(output2)
    print "length of output 2: ", o2
    print "output2 files created: " + str(obj2.files_created)
    print "running: 'gaussian.py', '-s', '3', '-n', '95', '-m', '10.'"
    obj3 = env.run('gaussian.py', '-s', '3', '-n', '95', '-m', '10.')
    output3 = obj3.stdout
    o3 = len(output3.split())
    print "output3: " + str(output3)
    print "Output 3 length: ", o3
    print "output3 files_created: " + str(obj3.files_created)
    print "running: 'gaussian.py', '-n', '4'"
    obj4 = env.run('gaussian.py', '-n', '4')
    output4 = obj4.stdout
    o4 = len(output4.split())
    print "output4: " + str(output4)
    print "output4 length:" + str(o4)
    # checking to see if files were created when they were supposed to, and not otherwise
    if obj1.files_created:
        print "Gaussian.py correctly created a file"
    else:
        raise NameError( "Gaussian.py failed to create a file with the '-F' flag")
    if obj2.files_created or obj3.files_created or obj4.files_created:
        raise NameError( "Gaussian.py created a file when the '-F' flag was not present")
    # checking to see that distribution is indeed random
    if output2 != output3:
        print "Distributions appear to be random"
    else:
        raise NameError( "Gaussian.py produced identical distributions")
    # checking to see if gaussian.py is responding correctly to the requested amount of output
    if o1 == 0 and o2 == 95 and o3 == 95 and o4 == 4:
        print "Gaussian.py is giving the correct amount of output"
    else:
        raise NameError("Gaussian.py is giving the wrong amount of output")
    # testing other command line arguments
    print "running gaussian.py -m 20 -n 5 -s 3 -F " + file_prefix + "gaussian_output_new.out"
#    objx = env.run('gaussian.py', '-m', '20', '-s', '3', '-F', file_prefix + 'gauss_out.out')
    objx = env.run('gaussian.py', '-m', '20.', '-s', '3', '-n', '15', '-F', 'gaussian_output_new.out')
    if objx.files_created:
        print objx.files_created
        print "Gaussian.py is working"
    else:
        raise NameError("Gaussian.py failed with extra command line options")

random_tests = {"gaussian": complete_gaussian_test, "fishrot": complete_fishrot_test, "fisher": complete_fisher_test, "tk03": complete_tk03_test, "uniform": complete_uniform_test}
random_errors_list = open('random_errors_list.txt', 'w')

def complete_working_test():
    complete_gaussian_test()
    complete_fishrot_test()
    complete_fisher_test()
    complete_tk03_test()
    complete_uniform_test()

if __name__ == "__main__":
    if "-r" in sys.argv:
        PT.run_individual_program(random_tests)
    elif "-all" in sys.argv:
        complete_working_test()
        print "remember to delete *_new.out files as needed"
    else:
#        new_list = EL.go_through(random_tests, random_errors_list)
        new_list = EL.go_through(random_tests, random_errors_list)
        EL.redo_broken_ones(new_list)
        print "finished with Random testing and re-testing"

# run: python random_stuff.py > random_all_output.txt
# then: python clean_log_output.py
        # infile: random_all_output.txt
        # outfile: random_clean_output.txt



# unittests not really possible
