#! /usr/bin/env python                                                                                                                
import sys
from scripttest import TestFileEnvironment
env = TestFileEnvironment('./new-test-output')
import unittest
import subprocess

file_prefix = '/Users/nebula/Python/Tests/'
directory =  '/Users/nebula/Python/Tests'

def file_parse(the_file):
    """Takes in a file and returns a list with each line as a list item"""
    print("Parsing file:", the_file)
    data = open(the_file, 'rU').readlines()
    clean_file = []
    for l in data:
        new_line = l.strip('\n')
        new_line = new_line.strip(" ")
        clean_file.append(new_line)
    print("Finished parsing file:", the_file)
    return clean_file 

def file_parse_by_word(the_file):
    """Takes in a file and returns a list with each word as a list item"""
    print "parsing file (by word): " + str(the_file)
    data = open(the_file, 'rU').readlines()
    clean_data = []
    for line in data:
        line = line.split()
        clean_data += line
#    clean_file = str(data)
    print "finished parsing file: " + str(the_file)
    return clean_data # returns a list.  each word is an item

def output_parse(the_output):
    """Takes in output and returns a list with each word as a list item"""
    data = str(the_output)
    data = data.split()
    return data # returns a list.  each word is an item.  

# this function is used to deal with the changing versions of pmagpy
def pmagpy_strip(a_list):
    """Takes a list and removes instances of 'pmagpy-version', i.e. -- pmagpy-2.194 -- so that changing versions don't break correctfiles"""
    print "stripping out instances of pmagpy"
    if type(a_list) != list:
        a_list = str(a_list).split()
    new_list = []
    for i in a_list:
        if "pmagpy" in i:
            pass
        else:
            new_list.append(i)
    return new_list

def file_parse_by_word_and_pmagpy_strip(a_file): 
    """Takes in a file, then parses it by word and removes instances of pmagpy"""
    data = file_parse_by_word(a_file)
  #  print data
    end_data = []
    for d in data:
        if "pmagpy" in d:
            pass
        else:
            end_data.append(d)
    print "finished parsing file " + str(a_file)
    return end_data

def test_for_bad_file(output):
    """Catches output of 'bad file' even when no error is raised"""
    output = str(output)
    if "bad file" in output:
        raise NameError("Output said 'bad file'")

def compare_two_lists(output, correct_output):
    """Iterates through a list and a reference list, catches any possible differences"""
    print "Comparing two lists"
    for num, i in enumerate(output):
        if i == correct_output[num]:
            print i, correct_output[num]
#            print "Lists were the same"
        else:
            print "Output contained: " + str(i) + " where it should have had " + str(correct_output[num])
            print "Error raised"
            raise ValueError("Wrong output")

def lowercase_all(a_list):
    """Takes a list as input, and downcases all items in that list"""
    new_list = []
    for i in a_list:
        n = str(i).lower()
        new_list.append(n)
    return new_list

def clean_house():
    """Removes all items from new-test-output/ so they don't cause conflict when a test is run a second time."""
    print "CLEANING HOUSE"
    print "-"
#    subprocess.call('rm ' + directory + '/*_new.out', shell=True)
    subprocess.call('rm ' + file_prefix + 'new-test-output/*', shell=True) # add long path name???

def remove_new_outfiles(): 
    """
    gets rid of all freshly created outfiles.
    """
    subprocess.call('rm ' + directory + '/*_new.out', shell=True)

def clean_program_name(name = None): 
    """
    Takes input of program name in different forms and gets it ready to run, i.e. --  "complete_angle.py", "angle", "complete_angle_test()", "angle_test", "complete_angle","complete_Angle" -- all turn into: "complete_angle_test()"
    """
    if name == None:
        n = raw_input("name?  ")
    else:
        n = name
 #   print "name", name
#    print "n", n
    n = str(n)
  #  print n
    n = n.lower()
 #   print n
    n = n.strip(" ")
#    print n
    if ".py" in n:
        n = n[:-3]
    print n
    if "_test" in n:
        if "()" in n:
            pass
        else:
            n += "()"
    else:
        n += "_test()"
    if "complete" in n:
        pass
    else:
        n = "complete_" + n
#    print "final: " + str(n)
    return n


# for testing clean_program_name()
#clean_program_name("complete_angle.py")
#clean_program_name("angle")
#clean_program_name("complete_angle_test()")
#clean_program_name("angle_test")
#clean_program_name("complete_angle")
#clean_program_name("complete_Angle")
#clean_program_name("thellier_REDO")
#clean_program_name("thellier_REDO_magic_test()")
#clean_program_name("complete_thellier_REDO")
#clean_program_name()

def find_a_program(name):
    """Takes a program name as input and finds which if any of the modules contain a test for it"""
    found_in = []
    full_name = clean_program_name(name)
 #   print "FULL NAME", full_name
    Rename = file_parse_by_word(file_prefix + "Rename_me.py")
    new_rename = lowercase_all(Rename)
    found = False
    if full_name in new_rename:
        found = True
        print full_name + " occurs in Rename_me.py"
        found_in.append("Rename_me.py")
    Extra_output = file_parse_by_word(file_prefix + "Extra_output.py")
    new_extra_output = lowercase_all(Extra_output)
    if full_name in new_extra_output:
        found = True
        print full_name + " occurs in Extra_output.py"
        found_in.append("Extra_output.py")
    Bootstrap = file_parse_by_word(file_prefix + "Bootstrap.py")
    new_bootstrap = lowercase_all(Bootstrap)
    if full_name in new_bootstrap:
        found = True
        print full_name + " occurs in Bootstrap.py"
        found_in.append("Bootstrap.py")
    Random = file_parse_by_word(file_prefix + "Random.py")
    new_random = lowercase_all(Random)
    if full_name in new_random:
        found = True
        print full_name + " occurs in Random.py"
        found_in.append("Random.py")
    if found:
        print full_name + " was found"
        print name + ".py is tested in: " + str(found_in)
    else:
        print name + " not found.  Make sure your spelling is good!"


def run_individual_program(mapping, program=None): # takes as argument a mapping of function name to the actual function, then runs that function
    """
    Takes in the name of a program as an argument, then runs the test for that program. 
    """
    print "running individual program!"
    print "remember to delete the _new.out file(s) as needed, if debugging"
    try:
        if program == None:
            ind=sys.argv.index('-r')
            run_program=sys.argv[ind+1]
        else:
            run_program = program
        print run_program
        if ".py" in run_program:
            run_program = run_program[:-3]
        program = mapping[run_program]
        print program
        print type(program)
        program()
    except KeyError as er:
        print er
        print "Please try again.  Check spelling, etc.  Make sure to input the name of the program with no quotations or extra words: i.e.: angle, or: thellier_magic_redo"
#        break
    except Exception as ex:
        print "printing error:"
        print ex
        raise(ex)


if __name__ == "__main__":
    print "Please type the name of the program test you wish to find"
    print "You may enter either: program.py, or: program. No quotation marks, case does not matter"
    search_item = str(raw_input("what program are you looking for?   "))
    find_a_program(search_item)
