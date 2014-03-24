#! /usr/bin/env python

import sys
from scripttest import TestFileEnvironment
env = TestFileEnvironment('./new-test-output')
import unittest
import subprocess
import PmagPy_tests as PT
import error_logging as EL

file_prefix = PT.file_prefix
directory =  PT.directory

def remove_non_numbers_from_output(raw_output):
    """Takes in output and returns a list of only the floats"""
    clean_output = []
    for i in raw_output:
        if i[-1] == ":":
            i = i.strip(":")
        try:
            clean_output.append(float(i))
        except:
            pass
    return clean_output

def check_bootstrap(actual_output, reference_output):
    """Checks an output list against a reference list of tuples with a high and a low acceptable value.  It raises an error if the actual output is not within the bounds of the reference list.  I.e., output is [1, 10], reference is [(.5, 1.5), (9, 11)]"""
    for num, z in enumerate(actual_output):
        lower_bound = reference_output[num][0]
        upper_bound = reference_output[num][1]
        if z <= upper_bound and z >= lower_bound:
            print "success"
        else:
            print "z was: " + str(z) + ", upper_bound was: " + str(upper_bound) + ", lower_bound was: " + str(lower_bound)
            print "error raised"
            raise ValueError("program produced incorrect output (" + str(z) + " should have been between " + str(lower_bound) + " and " + str(upper_bound) + ")")
    print "End of check_bootstrap"

aniso_magic_reference = [(.3402, .34042), (29.5, 29.7), (14.4, 14.6), (30., 38.), (169., 173.), (66., 69.), (6.3, 7.), (295.,297.), (12., 14.), (0.33535, .33537), (166.2, 166.4), (70.4, 70.6), (23.5, 25.0), (25., 29.), (12., 14.), (10.5, 11.2), (292., 295.), (11., 13.), (0.324231, .324232), (296.1, 296.3), (12.7, 12.9), (10.5, 11.5), (177, 181.), (60., 65.), (4.8, 5.1), (31., 32.5), (21., 25.)]

def do_aniso_magic(times):
    print "Testing aniso_magic.py, running bootstrap: " + str(times) + " times"
    obj = env.run('aniso_magic.py', '-WD', directory, '-f', 'aniso_magic_dike_anisotropy.txt', '-F', 'aniso_magic_rmag_anisotropy_new.out', '-nb', times, '-gtc', '110', '2', '-par', '-v', '-crd', 'g', '-P') #stdin='q')
    print obj.stdout
    PT.test_for_bad_file(obj.stdout)
    a_list = str(obj.stdout).split()
    print a_list
    clean_list = remove_non_numbers_from_output(a_list)
    return clean_list

def complete_aniso_magic_test():
    """test aniso_magic.py"""
    output1 = do_aniso_magic(5000)# change 20000 for real test
    check_bootstrap(output1, aniso_magic_reference)
    output2 =  do_aniso_magic(5000)# change 20000 for real test
    check_bootstrap(output2, aniso_magic_reference)
    output3 = do_aniso_magic(5000)# change 20000 for real test
    check_bootstrap(output3, aniso_magic_reference)

scalc_reference = [(88.5, 89.5), (14.8, 15.8), (13.0, 14.0), (16.5, 17.5), (31.6, 32.6)] 

def do_scalc():
    print "testing scalc.py"
    obj = env.run('scalc.py', '-f', file_prefix + 'scalc_example.txt', '-v', '-b')
    a_list = str(obj.stdout).split()
    print a_list
    clean_list = remove_non_numbers_from_output(a_list)
    return clean_list

def complete_scalc_test():
    """test scalc.py"""
    output = do_scalc()
    print "output: " + str(output)
    check_bootstrap(output, scalc_reference)

scalc_magic_reference = [(12.5, 13.5), (17.2, 18.2), (13., 14.), (21., 22.), (36.5, 37.5)]

def do_scalc_magic():
    obj = env.run('scalc_magic.py', '-f', file_prefix + 'scalc_magic_example.txt', '-v', '-b')
    a_list = str(obj.stdout).split()
    clean_list = remove_non_numbers_from_output(a_list)
    print clean_list
    final_list = clean_list[-5:] # removes the extraneous output, i.e. 100 out of 100, 200 out of 1000, etc.
    print final_list
    return final_list

def complete_scalc_magic_test():
    """test scalc_magic.py"""
    output = do_scalc_magic()
    check_bootstrap(output, scalc_magic_reference)

bootams_reference=[(0.3350, 0.3351), (0.0002, 0.0003), (5.1, 5.5), (14.5, 14.9), (10.1, 10.5), (260.5, 261.5), (37.5, 40.), (13.2, 13.9), (111.6, 112.4), (46., 48.), (.3333, .3334), (.00009, .0003), (124.5, 124.7), (61.5, 61.9), (5.8, 6.2), (225., 225.6), (5.6, 6.2), (17., 17.4), (318.3, 318.9), (28.3, 28.9), (.33150, .3317), (.0001, .0002), (268.5, 269.), (23.3, 23.9), (10.4, 11.), (357.6, 359.5), (3.6, 6.5), (12.2, 12.8), (95., 103.5), (65., 66.)]

def do_bootams(num):
    print "doing bootams"
    bootams_infile = file_prefix + 'bootams_example.dat'
    obj = env.run('bootams.py', '-f', bootams_infile, '-nb', num)
    print "finished running bootams.py"
    a_list = str(obj.stdout).split()
    clean_list = remove_non_numbers_from_output(a_list)
    print clean_list
    return clean_list

def complete_bootams_test():
    """test bootams.py"""
    print "testing bootams.py"
    output1 = do_bootams(100000)
    print "finished do_bootams()"
    check_bootstrap(output1, bootams_reference)
# add in extras for real testing
    output2 = do_bootams(100000)
    check_bootstrap(output2, bootams_reference)

def do_watsonsV():
    """test watsonsV.py"""
    watsonsV_infile = file_prefix + "watsonsF_example_file1.dat"
    watsonsV_infile2 = file_prefix + "watsonsF_example_file2.dat"
    obj = env.run("watsonsV.py", "-f", watsonsV_infile, "-f2", watsonsV_infile2, stdin='q') 
    print obj.stdout
    a_list = str(obj.stdout).split()
    clean_list = remove_non_numbers_from_output(a_list)
    final_list = clean_list[-2:]
    print final_list
    return final_list

watsonsV_reference = [(10., 11.),(6., 7.)]

def complete_watsonsV_test():
     """test watsonsV.py"""
     output1 = do_watsonsV()
     check_bootstrap(output1, watsonsV_reference)
     output2 = do_watsonsV()
     check_bootstrap(output2, watsonsV_reference)


find_EI_reference = [(38.85, 39.0), (58.75, 58.9), (45., 50.), (65.5, 69.), (1.45, 1.5), (1.23, 1.35), (1.6, 2.2)]

def run_EI(num):
     print ('find_EI.py', '-f', file_prefix + 'find_EI_example.dat', '-nb', num, "stdin='a'")
     obj = env.run('find_EI.py', '-f', file_prefix + 'find_EI_example.dat', '-nb', num, stdin='a')
     print "full output = " +str(obj.stdout)
     print "files created: " + str(obj.files_created)
     print "files updated: " + str(obj.files_updated)
     output = str(obj.stdout[-210:-143]).split()
     print "raw output = " + str(output)
     clean_out = remove_non_numbers_from_output(output)
     print "clean output = " + str(clean_out)
     print "Finish run_EI()"
     return clean_out

def complete_find_EI_test():
     """test find_EI.py"""
     output1 = run_EI(1000)
     print output1
     check_bootstrap(output1, find_EI_reference)
 # extras, add in for real testing
     output2 = run_EI(1000)
     check_bootstrap(output2, find_EI_reference)
     output3 = run_EI(1000)
     check_bootstrap(output3, find_EI_reference)
     print "Finished find_EI test"

class Bad_find_EI(unittest.TestCase):
     def test_for_error(self):
         print "TESTING FOR ERROR"
         bad_out = run_EI(25)
         self.assertRaises(ValueError, check_bootstrap, bad_out, find_EI_reference)

class Bad_aniso_magic(unittest.TestCase):
     def test_for_error(self):
         print "TESTING FOR ERROR"
         bad_out = do_aniso_magic(100)
         self.assertRaises(ValueError, check_bootstrap, bad_out, aniso_magic_reference)

class Bad_bootams(unittest.TestCase):
     def test_for_error(self):
         print "TESTING FOR ERROR"
         bad_out = do_bootams(100)
         self.assertRaises(ValueError, check_bootstrap, bad_out, bootams_reference)

def complete_eqarea_magic_test():
     """test eqarea_magic.py"""
     eqarea_magic_infile = 'eqarea_magic_example.dat'
     eqarea_reference = [(1.0, 1.0), (109., 112.), (203., 207.), (7., 8.), (.9, 1.1), (28.5, 29.5), (7.5, 9.5), (3., 3.5), (5.5, 6.5), (59., 60.), (1.9, 2.1), (247., 250.), (148., 153.), (4., 4.6), (.9, 1.1), (26., 27.), (14.5, 16.5), (7.5, 8.5), (184.5, 186.5), (-59.5, -58.)]
     obj = env.run('eqarea_magic.py', '-WD', directory, '-f', eqarea_magic_infile, '-obj', 'loc', '-crd', 'g', '-ell', 'Be', stdin='q')
     result = obj.stdout
     result_list = str(result).split()
     a_list = []
     add_me = False
     for i in result_list: # this goes through the output and isolates the relevant numbers for testing
   #       print i
         if str(i) == 'mode':
             add_me = True
         if str(i) == 'S[a]ve':
             add_me = False
         if add_me == True:
             a_list.append(i)
     stripped_list = remove_non_numbers_from_output(a_list)
     print stripped_list
     print len(stripped_list)
     print eqarea_reference
     print len(eqarea_reference)
     check_bootstrap(stripped_list, eqarea_reference)

Bootstrap_tests = {"aniso_magic": complete_aniso_magic_test, "find_EI": complete_find_EI_test, "bootams": complete_bootams_test, "eqarea": complete_eqarea_magic_test, "scalc": complete_scalc_test, "scalc_magic": complete_scalc_magic_test, "watsonsV": complete_watsonsV_test}

bootstrap_errors_list = open('bootstrap_errors_list.txt', 'w')

def complete_working_test():
     complete_aniso_magic_test()        
     complete_find_EI_test()
     complete_bootams_test()
     complete_eqarea_magic_test()
     complete_scalc_test()
     complete_scalc_magic_test()
     complete_watsonsV_test()

if __name__ == "__main__":
    PT.clean_house()
    if "-r" in sys.argv:
        print "Bootstrapping! Be patient"
        PT.run_individual_program(Bootstrap_tests)
    elif "-all" in sys.argv:
        complete_working_test()
        print "remember to delete *_new.out files as needed"
    else:
        new_list = EL.go_through(Bootstrap_tests, bootstrap_errors_list)
        EL.redo_broken_ones(new_list)
        print "finished with Bootstrap testing and re-testing"

#    unittest.main(module="Bootstrap_plotting")


# run: python Bootstrap.py > bootstrap_all_output.txt
# then: python clean_log_output.py
        # infile: bootstrap_all_output.txt
        # outfile: bootstrap_clean_output.txt


# You can't run the bootstrap, plot things at the same time as other python programs.  Or else it gets all kinds of wacky

