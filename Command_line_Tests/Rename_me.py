#! /usr/bin/env python                                                                                                                        
import sys
from scripttest import TestFileEnvironment
env = TestFileEnvironment('./new-test-output')
import unittest
import subprocess
import PmagPy_tests as PT
import error_logging as EL

#import Extra_output

file_prefix = PT.file_prefix
directory = PT.directory

class Test_instance(object):
     def __init__(self, name, infile, outfile, ref_out, wrong_out, stdin, WD, *args):
         """Takes a program name, an input file, an output file, a reference output file, an incorrect output file, standard input for the program, whether or not the program has a -WD option, and up to 6 additional command line arguments"""
         self.name = name
         if infile != None:
              self.infile = file_prefix + infile
         else:
              self.infile = None
         if outfile != None:
              self.outfile = file_prefix + outfile
         else:
              self.outfile = None
         self.ref_out = ref_out
         self.wrong_out = wrong_out
         self.stdin = stdin
         self.WD = WD
         self.arg_0, self.arg_1, self.arg_2, self.arg_3, self.arg_4, self.arg_5 = None, None, None, None, None, None
         self.args = args
         self.parse_args() # SEE IF THIS WORKS
         if self.WD:
              self.infile = infile
              self.outfile = outfile
     
     def parse_args(self):  
         """turns up to 6 args into command line options"""
         if len(self.args) == 1:
             self.arg_0 = self.args[0]
         if len(self.args) == 2:
             self.arg_0 = self.args[0]
             self.arg_1 = self.args[1]
         if len(self.args) == 3:
             self.arg_0 = self.args[0]
             self.arg_1 = self.args[1]
             self.arg_2 = self.args[2]
         if len(self.args) == 4:
             self.arg_0 = self.args[0]
             self.arg_1 = self.args[1]
             self.arg_2 = self.args[2]
             self.arg_3 = self.args[3]
         if len(self.args) == 5:
             self.arg_0 = self.args[0]
             self.arg_1 = self.args[1]
             self.arg_2 = self.args[2]
             self.arg_3 = self.args[3]
             self.arg_4 = self.args[4]
         if len(self.args) == 6:
             self.arg_0 = self.args[0]
             self.arg_1 = self.args[1]
             self.arg_2 = self.args[2]
             self.arg_3 = self.args[3]
             self.arg_4 = self.args[4]
             self.arg_5 = self.args[5]
         for num, arg in enumerate(self.args):
              pass
         

         # this function simply runs the command line program with whatever its options

     def run_program(self, output_type="stdout"): # 
          """Runs pmagpy program in a simulated command-line type environment. It takes the arguments "stdout", "plot", or  "file", and respectively returns the standard output for the program, the plots created, or the file created/updated."""  
          PT.clean_house() # this wipes the test output directory and prevents programs from interfering with each other. they are run twice for unittesting
          if self.WD:
               print "WD program about to run:"
               print(self.name, '-WD', directory, '-f', self.infile, '-F', self.outfile, self.arg_0, self.arg_1, self.arg_2, self.arg_3, self.arg_4, self.arg_5, 'stdin='+str(self.stdin))
               obj = env.run(self.name, '-WD', directory, '-f', self.infile, '-F', self.outfile, self.arg_0, self.arg_1, self.arg_2, self.arg_3, self.arg_4, self.arg_5, stdin=self.stdin)
          else:
               print "Non-WD program about to run:"
               print self.name, '-f', self.infile, '-F', self.outfile, self.arg_0, self.arg_1, self.arg_2, self.arg_3, self.arg_4, self.arg_5,  'stdin=' + str(self.stdin)
               obj = env.run(self.name, '-f', self.infile, '-F', self.outfile, self.arg_0, self.arg_1, self.arg_2, self.arg_3, self.arg_4, self.arg_5, stdin=self.stdin)
          if "not a valid" in str(obj.stdout) or "bad file" in str(obj.stdout):
               print "stdout:" + str(obj.stdout)
               raise NameError(str(self.name) + " encountered an invalid file")
          if output_type == "plot":
               print "output is plot"
               if obj.files_created == {}:
                    print "stdout:" + str(obj.stdout)[:500]
                    print "no files were created"
                    print "files updated: ", obj.files_updated
                    return obj.files_updated
               else:
                    print "stdout:" + str(obj.stdout)[:500]
                    print "new files created: ", obj.files_created
                    return obj.files_created
          elif output_type == "file":
               print "stdout:" + str(obj.stdout)[:500]
               print "output is file: " + str(self.outfile)
               return self.outfile
          elif output_type == "stdout":
               print "output is stdout: "
               print obj.stdout
               return obj.stdout
          else:
               raise NameError("invalid output type was selected for run_program()")


         # this function compares real against expected output.  it can take any form of output, as long as the reference output is formatted the same as the expected output.  
     def check_output(self, actual_out, reference_out):
          """Checks actual against expected output.  It is useful for short output, since it does not iterate through but just compares wholesale"""
          print "Checking stdout output"
          actual_out, reference_out = str(actual_out), str(reference_out)
          if reference_out in actual_out: #the in syntax is because of weird extra spaces and characters at the end/start of stdout
               print str(self.name) + " output as expected"
               print "-"
          else:
               print "Output was: "
               print str(actual_out)
               print "Output should have been: " 
               print str(reference_out)
               print "Error raised"
               raise NameError(str(self.name) + " produced incorrect output")

     # this function will iterate through a reference list and see if each item of output is correct 
     def check_list_output(self, output_list, correct_output_list):
          """Iterates through an output list and a reference output list, and checks if each item matches"""
          print "checking output (in list form)"
          print "output_list:         " + str(output_list)[:200] + " ..."
          print "correct_output_list: " + str(correct_output_list)[:200] + " ...."
          print "Comparing two lists"
          list_empty = True
          for num, i in enumerate(output_list):
               list_empty = False
               if i == correct_output_list[num]:
                    print i, "   ",  correct_output_list[num]
               else:
                    print "Output contained:    " + str(i)  
                    print "but should have had: " + str(correct_output_list[num])
                    print "Error raised"
                    raise NameError("Wrong output")
          if list_empty:
               print "ONE OR BOTH LISTS DID NOT HAVE CONTENT"
               raise NameError("Output list empty")
          print "Lists were the same"
          print str(self.name) + " produced correct output"
               
     def check_file_output(self, output_file, correct_file): 
          """Takes in two file names as arguments, parses their contents into list format, and then compares the first against the second"""
          print "checking file output, using: " + str(output_file) + " AND " + str(correct_file)
          parsed_output = PT.file_parse_by_word_and_pmagpy_strip(output_file)
          print str(parsed_output)[:500] + " ..."
          parsed_correct = PT.file_parse_by_word_and_pmagpy_strip(correct_file)
          print str(parsed_correct)[:500] + "..."
          self.check_list_output(parsed_output, parsed_correct)

     def test_help(self): 
          """Runs the help option, and makes sure the help message is of a reasonable length"""
          print "testing help for " + str(self.name)
          obj = env.run(self.name, '-h')
          message = str(obj.stdout)
          print(len(message))
          if len(message) > 150:
               print "Help message successfully called"
               print "-"
          else:
               raise NameError("Help message for " + str(self.name)+ " failed...")

     def test_interactive(self):
          """Calls the interactive option on a program"""
          print "testing interactive option for " + str(self.name)
          obj = env.run(self.name, '-i', stdin=self.stdin)#, stdin='3')                                        
          print "stdout: "+ str(obj.stdout)
          if len(obj.stdout) > 10:
               print "Interactive mode works"
               print "-"
          else:
               raise NameError("Interactive mode for " + str(self.name) + " came up empty")

     def file_in_file_out_sequence(self, interactive=False):
          """This sequence fully tests a standard program that takes in a file and outputs another file. It defaults to no testing for an interactive mode, but it can be given interactive=True, and then it will"""
          self.test_help()
          result = self.run_program(output_type = "file")
          self.check_file_output(result, self.ref_out)
          if interactive:
               self.test_interactive()  
          self.unittest_file()         

     def plot_program_sequence(self, stdout=True):
          """ this sequence fully tests plotting programs, either that give stdout or that just make a plot"""
          self.test_help()
          if stdout:
               result = self.run_program()
          else:
               result = self.run_program(output_type = "plot")
          self.check_output(result, self.ref_out)
          self.unittest_short_output() # possibly this is not the best way to do this.  possibly some should get listified.  but, fuck it. 


     def list_sequence(self):
          """this sequence fully tests programs that produce stdout, without producing a file or a plot.  It puts the output into list form to make it nicer"""
          result = self.run_program(output_type = "stdout")
          print result
          new_list = str(result).split()
          self.check_list_output(new_list, self.ref_out)
          self.unittest_list()

     def unittest_file(self): 
          """creates a unittest for a simple file in file out program"""
          unittest = Bad_test(self)
          unittest.test_file_for_error()
          
     def unittest_short_output(self):  
          """creates a unittest for a plot program"""
          unittest = Bad_test(self)
          unittest.test_short_output_for_error()

     def unittest_list(self): 
          """creates a unittest for a stdout-producing program"""
          unittest = Bad_test(self)
          unittest.test_list_output_for_error()


class Bad_test(unittest.TestCase):
#     """These unittests are meant to ensure that my tests are catching errors when they are present.  They should raise an error if the main tests fail to raise errors with incorrect data"""
     def __init__(self, test_obj):
          """Each unittest belongs to a test object"""
          self.test_obj = test_obj
     def test_file_for_error(self):
          """unittests a file producing program"""
          print "Testing: " + str(self.test_obj.name) + " with incorrect file, expecting error"
        # means: run the check_file_output(self.wrong_out, self.ref_out)
          self.assertRaises(NameError, self.test_obj.check_file_output, self.test_obj.wrong_out, self.test_obj.ref_out)
          print "Error expected"
          print "-"

     def test_short_output_for_error(self):
          """tests a stdout producing program"""
          print "Testing: " + str(self.test_obj.name) + " with incorrect short output, expecting error"
          self.assertRaises(NameError, self.test_obj.check_output, self.test_obj.wrong_out, self.test_obj.ref_out)
          print "Error expected"
          print "-"

     def test_list_output_for_error(self):
          """tests a program that produces long output that must be list-i-fied"""
          print "Testing: " + str(self.test_obj.name) + " with incorrect list output, expecting error"
          self.assertRaises(NameError, self.test_obj.check_list_output, self.test_obj.wrong_out, self.test_obj.ref_out)
          print "Error expected"
          print "-"


# file_in_file_out example
def complete_angle_test(): 
     """test angle.py"""
     angle = Test_instance('angle.py', 'angle.dat', 'angle_results_new.out', 'angle_results_correct.txt', 'angle_results_incorrect.txt', None, False)
     angle.file_in_file_out_sequence(interactive=True)

# plotting without stdout example
def complete_zeq_test():   
     """test zeq.py"""
     zeq_infile = 'zeq_example.dat'
     zeq_reference_output = """0      0.0 9.283e-08   339.9    57.9 
1      2.5 7.582e-08   325.7    49.1 
2      5.0 6.292e-08   321.3    45.9 
3     10.0 5.209e-08   314.8    41.7 
4     15.0 4.455e-08   310.3    38.7 
5     20.0 3.954e-08   305.0    37.0 
6     30.0 3.257e-08   303.9    34.7 
7     40.0 2.567e-08   303.0    32.3 
8     50.0 2.252e-08   303.6    32.4 
9     60.0 1.982e-08   299.8    30.8 
10     70.0 1.389e-08   292.5    31.0 
11     80.0 1.257e-08   297.0    25.6 
12     90.0 5.030e-09   299.3    11.3 
 s[a]ve plot, [b]ounds for pca and calculate, change [h]orizontal projection angle, [q]uit:   """
     zeq_wrong_output = "Hi there"
     zeq_outfile = None
     zeq = Test_instance('zeq.py', zeq_infile, zeq_outfile, zeq_reference_output, zeq_wrong_output, 'q', False, '-u', 'C')
     zeq.plot_program_sequence(stdout=True)

# plotting example, no stdout
def complete_chartmaker_test(): 
     """test chartmaker.py"""
     chartmaker_infile = None
     chartmaker_outfile = None
     chartmaker_reference = "{'chart.txt': <FoundFile ./new-test-output:chart.txt>}"
     chartmaker_wrong = "wrong"
     chartmaker = Test_instance('chartmaker.py', chartmaker_infile, chartmaker_outfile, chartmaker_reference, chartmaker_wrong, 'q', False)
     chartmaker.plot_program_sequence(stdout=False)
     chartmaker.unittest_short_output()

# List output example
def complete_di_eq_test(): 
     """test di_eq.py"""
     print "Testing di_eq.py"
     di_eq_infile = 'di_eq_example.dat'
     di_eq_outfile = None
     di_eq_reference = ['-0.239410', '-0.893491', '0.436413', '0.712161', '0.063844', '0.760300', '0.321447', '0.686216', '0.322720', '0.670562', '0.407412', '0.540654', '0.580156', '0.340376', '0.105351', '0.657728', '0.247173', '0.599687', '0.182349', '0.615600', '0.174815', '0.601717', '0.282746', '0.545472', '0.264863', '0.538273', '0.235758', '0.534536', '0.290665', '0.505482', '0.260629', '0.511513', '0.232090', '0.516423', '0.244448', '0.505666', '0.277927', '0.464381', '0.250510', '0.477152', '0.291770', '0.440816', '0.108769', '0.516148', '0.196706', '0.482014', '0.349390', '0.381292', '0.168407', '0.475566', '0.206286', '0.446444', '0.175701', '0.450649', '0.301104', '0.378539', '0.204955', '0.423970', '0.199755', '0.422584', '0.346920', '0.308010', '0.119030', '0.441144', '0.239848', '0.376486', '0.269528', '0.342510', '0.085451', '0.423789', '0.192224', '0.387233', '0.172608', '0.395084', '0.272008', '0.320741', '0.393981', '0.117451', '-0.017726', '0.406002', '0.154273', '0.367000', '0.213903', '0.335760', '0.103221', '0.372202', '0.231833', '0.283245', '0.072160', '0.351538', '0.007802', '0.319236', '0.152583', '0.265350', '0.248133', '0.136412']
     di_eq_wrong = "wrong"
     di_eq = Test_instance('di_eq.py', di_eq_infile, di_eq_outfile, di_eq_reference, di_eq_wrong, None, False)
     di_eq.list_sequence()


# the rest of the UCs

def complete_azdip_magic_test(): # irregular, because the outfile is signaled with -Fsa, not -F.  sequence is in longhand
     """test azdip_magic.py"""
     # non WD
     azdip_magic_infile = 'azdip_magic_example.dat'
     azdip_magic_reference = 'azdip_magic_output_correct.out'
     azdip_magic_wrong = 'azdip_magic_output_incorrect.out'
     azdip_magic_outfile = file_prefix + 'azdip_magic_output_new.out' # needs file prefix because it doesn't go into the azdip_magic object
     azdip_magic = Test_instance('azdip_magic.py', azdip_magic_infile, None, azdip_magic_reference, azdip_magic_wrong, False, None, '-Fsa', azdip_magic_outfile, '-mcd', 'FS-FD:SO-POM', '-loc', "Northern Iceland")
     azdip_magic.run_program(output_type='file')
     print azdip_magic_outfile
     azdip_magic.check_file_output(azdip_magic_outfile, azdip_magic.ref_out)
     azdip_magic.unittest_file()

def complete_combine_magic_test(): # irregular type.  this one is a weird amalgam, because of two -f inputs.  but it works.  
     """test combine_magic_test.py"""
     output_file = 'combine_magic_output_new.out'
     reference_file =  'combine_magic_output_correct.out'
     incorrect_output = 'combine_magic_output_incorrect.out'
     input_1 = 'combine_magic_input_1.dat'
     input_2 = 'combine_magic_input_2.dat'
    # have to run it specially, because -f takes two arguments.  it doesn't fit with its class in this regard. 
     obj = env.run('combine_magic.py', '-WD', directory, '-F', output_file, '-f', input_1, input_2)
     combine_magic = Test_instance('combine_magic.py', None, output_file, reference_file, incorrect_output, None, True, '-f', input_1, input_2)
     combine_magic.check_file_output(combine_magic.outfile, combine_magic.ref_out)
     combine_magic.test_help()
     combine_magic.unittest_file()
     print "Successfully finished combine_magic_test"

def complete_cont_rot_test(): # Irregular type -- running specially because it has so many command line options
     """test cont_rot.py"""
     print "running: cont_rot.py -con af:sam -prj ortho -eye -20 0 -sym k- 1 -age 180 -res l, stdin='a'"
     obj = env.run('cont_rot.py', '-con', 'af:sam', '-prj', 'ortho', '-eye', '-20', '0', '-sym', 'k-', '1', '-age', '180', '-res', 'l', stdin='a')
     output = str(obj.files_created) # output is the name of the plot that has been saved
     print "stdout = " + str(obj.stdout)
     print "output file(s): " + str(output)
     reference_output = "{'Cont_rot.pdf': <FoundFile ./new-test-output:Cont_rot.pdf>}"
     incorrect_output = "wrong"
     cont_rot = Test_instance('cont_rot.py', None, output, reference_output, incorrect_output, 'a', False)
     cont_rot.check_output(cont_rot.outfile, cont_rot.ref_out)
     cont_rot.test_help()
     cont_rot_unittest = Bad_test(cont_rot)
     cont_rot_unittest.test_short_output_for_error()

def complete_download_magic_test(): # irregular
     """test download_magic.py"""
     subprocess.call(['rm', '-rf', 'Location_1/'])
     subprocess.call(['rm', 'er_locations.txt', 'magic_measurements.txt', 'pmag_samples.txt', 'er_samples.txt', 'magic_methods.txt', 'pmag_sites.txt', 'er_ages.txt', 'er_sites.txt', 'pmag_criteria.txt', 'pmag_specimens.txt', 'er_citations.txt', 'er_specimens.txt', 'pmag_results.txt'])  # deleting all files first, just in case they were missed the time before, as they would in the case of an error.  
     download_magic_infile = 'download_magic_example.dat'
     download_magic_reference = download_magic_ref
     download_magic_wrong = 'download_magic_correct_output.out'
     download_magic = Test_instance('download_magic.py', download_magic_infile, None, download_magic_reference, download_magic_wrong, 'y', True)
     output = str(download_magic.run_program()).split()
     print output
     clean_out = []
     for thing in output: # removing long path names from output, so it can be run on any machine
          if directory in thing:
               pass
          else:
               clean_out.append(thing)
     print clean_out
     download_magic.check_list_output(clean_out, download_magic_reference)
     subprocess.call(['rm', '-rf', 'Location_1/'])
     subprocess.call(['rm', 'er_locations.txt', 'magic_measurements.txt', 'pmag_samples.txt', 'er_samples.txt', 'magic_methods.txt', 'pmag_sites.txt', 'er_ages.txt', 'er_sites.txt', 'pmag_criteria.txt', 'pmag_specimens.txt', 'er_citations.txt', 'er_specimens.txt', 'pmag_results.txt'])
     print "all created files removed"

download_magic_ref = ['working', 'on:', "'er_locations'", 'er_locations', 'data', 'put', 'in', 'working', 'on:', "'er_sites'", 'er_sites', 'data', 'put', 'in', 'working', 'on:', "'er_samples'", 'er_samples', 'data', 'put', 'in', 'working', 'on:', "'er_specimens'", 'er_specimens', 'data', 'put', 'in', 'working', 'on:', "'er_ages'", 'er_ages', 'data', 'put', 'in', 'working', 'on:', "'er_citations'", 'er_citations', 'data', 'put', 'in', 'working', 'on:', "'magic_measurements'", 'magic_measurements', 'data', 'put', 'in', 'working', 'on:', "'pmag_specimens'", 'pmag_specimens', 'data', 'put', 'in', 'working', 'on:', "'pmag_samples'", 'pmag_samples', 'data', 'put', 'in', 'working', 'on:', "'pmag_sites'", 'pmag_sites', 'data', 'put', 'in', 'working', 'on:', "'pmag_results'", 'pmag_results', 'data', 'put', 'in', 'working', 'on:', "'pmag_criteria'", 'pmag_criteria', 'data', 'put', 'in', 'working', 'on:', "'magic_methods'", 'magic_methods', 'data', 'put', 'in', 'location_1:', 'Snake', 'River', 'unpacking:', '1', 'read', 'in', '1', 'stored', 'in', 'unpacking:', '27', 'read', 'in', '27', 'stored', 'in', 'unpacking:', '271', 'read', 'in', '271', 'stored', 'in', 'unpacking:', '177', 'read', 'in', '177', 'stored', 'in', 'unpacking:', '20', 'read', 'in', '20', 'stored', 'in', 'unpacking:', '17', 'read', 'in', 'unpacking:', '3072', 'read', 'in', '3072', 'stored', 'in', 'unpacking:', '225', 'read', 'in', '225', 'stored', 'in', 'unpacking:', '166', 'read', 'in', '166', 'stored', 'in', 'unpacking:', '30', 'read', 'in', '30', 'stored', 'in', 'unpacking:', '24', 'read', 'in', '24', 'stored', 'in', 'unpacking:', '7', 'read', 'in', 'unpacking:', '32', 'read', 'in']


def complete_pt_rot_test(): # Irregular type.  has both an -ff and an -f option.  testing both here. 
     """test pt_rot.py"""
     pt_rot = Test_instance('pt_rot.py', 'pt_rot_example.dat', 'pt_rot_results_new.out', 'pt_rot_results_correct.out', 'pt_rot_results_incorrect.out', None, True)
     pt_rot.file_in_file_out_sequence()
     # then, testing the -ff option
     input_1 = 'pt_rot_extra_in_nam_180-200.txt'
     input_2 = 'pt_rot_extra_in_nam_panA.frp'
     pt_rot_extra_outfile = 'pt_rot_extra_out.out'
     pt_rot_extra_reference = 'pt_rot_extra_correct.out'
     pt_rot_extra_wrong ='pt_rot_results_incorrect.out'
     pt_rot_extra = Test_instance('pt_rot.py', None, pt_rot_extra_outfile, pt_rot_extra_reference, pt_rot_extra_wrong, None, True, '-ff', input_1, input_2)
     print "Testing pt_rot.py with -ff option"
     obj = env.run('pt_rot.py', '-WD', directory, '-ff', input_1, input_2 , '-F', pt_rot_extra_outfile)
     pt_rot_extra.check_file_output(pt_rot_extra.outfile, pt_rot_extra.ref_out)
     pt_rot_extra_unittest = Bad_test(pt_rot_extra)
     pt_rot_extra_unittest.test_file_for_error()

def complete_customize_criteria_test():  # file type
     """test customize_criteria.py"""
     customize_criteria_infile = 'customize_criteria_example.dat'
     customize_criteria_output = 'customize_criteria_output_new.out'
     customize_criteria_reference = "customize_criteria_output_correct.out"
     customize_criteria_wrong = "customize_criteria_output_incorrect.out"
     customize_criteria = Test_instance('customize_criteria.py', customize_criteria_infile, customize_criteria_output, customize_criteria_reference, customize_criteria_wrong, '1', False)
     customize_criteria.file_in_file_out_sequence(interactive=True)

def complete_dipole_pinc_test(): # list type
     """test dipole_pinc.py"""
     dipole_pinc_infile = 'dipole_pinc_example.dat'
     dipole_pinc_outfile = None
     dipole_pinc_reference = ['33.0', '38.9', '54.5', '9.9']
     dipole_pinc_wrong = [1,2,3,4]
     dipole_pinc = Test_instance('dipole_pinc.py', dipole_pinc_infile, dipole_pinc_outfile, dipole_pinc_reference, dipole_pinc_wrong, None, False)
     dipole_pinc.list_sequence()

def complete_dipole_plat_test(): # list type
     """test dipole_plat.py"""
     dipole_plat_infile = 'dipole_plat_example.dat'
     dipole_plat_outfile = None
     dipole_plat_reference = ['9.2', '11.4', '19.3', '2.5']
     dipole_plat_wrong = "wrong"
     dipole_plat = Test_instance('dipole_plat.py', dipole_plat_infile, dipole_plat_outfile, dipole_plat_reference, dipole_plat_wrong, None, False)
     dipole_plat.list_sequence()

grab_magic_key_reference_list = ['42.60264', '42.60264', '42.60352', '42.60104', '42.73656', '42.8418', '42.8657', '42.92031', '42.56857', '42.49964', '42.49962', '42.50001', '42.52872', '42.45559', '42.48923', '42.46186', '42.69156', '42.65289', '43.30504', '43.36817', '43.42133', '43.8859', '43.84273', '43.53289', '43.57494', '44.15663', '44.18629']

def complete_grab_magic_key_test(): # List type
     """test grab_magic_key.py"""
     print "Testing grab magic"
     grab_magic_key_infile = 'grab_magic_key_er_sites.txt'
     grab_magic_key_outfile = None
     grab_magic_key_wrong = "wrong"
     grab_magic_key_reference = grab_magic_key_reference_list
     grab_magic_key = Test_instance('grab_magic_key.py', grab_magic_key_infile, grab_magic_key_outfile, grab_magic_key_reference, grab_magic_key_wrong, None, True, '-key', 'site_lat')
     grab_magic_key.list_sequence()
     print "Sucessfully finished complete_grab_magic_key_test"

def complete_incfish_test(): # file type 
     """test incfish.py"""
     incfish_infile = 'incfish_example_inc.dat'
     incfish_outfile = 'incfish_results_new.out'
     incfish_reference = 'incfish_results_correct.out'
     incfish_wrong = 'incfish_results_incorrect.out'
     incfish = Test_instance('incfish.py', incfish_infile, incfish_outfile, incfish_reference, incfish_wrong, None, False)
     incfish.file_in_file_out_sequence()

def complete_magic_select_test(): # file type.. but it doesn't work yet!  Lisa must add in a WD option.  
     """test magic_select.py"""
     magic_select_infile = 'magic_select_example.txt'
     magic_select_outfile = 'magic_select_results_new.out'
     magic_select_reference = 'magic_select_results_correct.out'
     magic_select_wrong = 'magic_select_results_incorrect.out'
     raise NameError('This program needs WD option')
     magic_select = Test_instance('magic_select.py', magic_select_infile, magic_select_outfile, magic_select_reference, magic_select_wrong, None, False, '-key', 'magic_method_codes', 'LP-DIR-AF', 'has')
     print "fails because needs WD option..."
     obj = env.run('magic_select.py', '-h')
     magic_select.run_program()
 #    obj = env.run('magic_select.py', '-f', magic_select_infile, '-key', 'magic_method_codes', 'DE-BFL', 'has', '-F', 'AF_specimens.txt')

#     magic_select.file_in_file_out_sequence()
    # add unittest when you get it together


def complete_nrm_specimens_magic_test(): # file type
     """test nrm_specimens_magic.py"""
     print "Testing nrm_specimens_magic.py"
     fsa = file_prefix + 'nrm_specimens_magic_er_samples.txt'
     nrm_specimens_magic_infile = 'nrm_specimens_magic_measurements.txt'
     nrm_specimens_magic_outfile = 'nrm_specimens_results_new.out'
     nrm_specimens_magic_reference = 'nrm_specimens_results_correct.out'
     nrm_specimens_magic_wrong = 'nrm_specimens_results_incorrect.out'
     nrm_specimens_magic = Test_instance('nrm_specimens_magic.py', nrm_specimens_magic_infile, nrm_specimens_magic_outfile, nrm_specimens_magic_reference, nrm_specimens_magic_wrong, None, False, '-fsa', fsa, '-crd', 'g')
     nrm_specimens_magic.file_in_file_out_sequence()
     print "Successfully completed nrm_specimens_magic.py tests"

def complete_sundec_test(): # list type
     """test sundec.py"""
     sundec_infile = 'sundec_example.dat'
     sundec_outfile = None
     sundec_reference = ['154.2']
     sundec_wrong = ['154.3']
     sundec = Test_instance('sundec.py', sundec_infile, sundec_outfile, sundec_reference, sundec_wrong, None, False)
     sundec.run_program()
     sundec.list_sequence()
     print "Successfully finished sundec.py tests"

def complete_pca_test(): # list type
     """test pca_example.py"""
     pca_infile = 'pca_example.dat'
     pca_outfile = None
     pca_reference = pca_correct_out
     pca_wrong = ['eba24a', 'wrong']
     pca = Test_instance('pca.py', pca_infile, pca_outfile, pca_reference, pca_wrong, None, False, '-dir', 'L', '1', '10')
     pca.list_sequence()

pca_correct_out = ['eba24a', 'DE-BFL', '0', '0.00', '339.9', '57.9', '9.2830e-05', '1', '2.50', '325.7', '49.1', '7.5820e-05', '2', '5.00', '321.3', '45.9', '6.2920e-05', '3', '10.00', '314.8', '41.7', '5.2090e-05', '4', '15.00', '310.3', '38.7', '4.4550e-05', '5', '20.00', '305.0', '37.0', '3.9540e-05', '6', '30.00', '303.9', '34.7', '3.2570e-05', '7', '40.00', '303.0', '32.3', '2.5670e-05', '8', '50.00', '303.6', '32.4', '2.2520e-05', '9', '60.00', '299.8', '30.8', '1.9820e-05', '10', '70.00', '292.5', '31.0', '1.3890e-05', '11', '80.00', '297.0', '25.6', '1.2570e-05', '12', '90.00', '299.3', '11.3', '0.5030e-05', 'eba24a', 'DE-BFL', '10', '2.50', '70.00', '8.8', '334.9', '51.5']

def complete_scalc_test(): # irregular, & list type
     """test scalc.py"""
     scalc_infile = 'scalc_example.txt'
     scalc_outfile = None
     scalc_reference = ['99', '19.5', '90.0']
     scalc_wrong = ['99', '19.5', '90.1']
     scalc = Test_instance('scalc.py', scalc_infile, scalc_outfile, scalc_reference, scalc_wrong, None, False)
     scalc.list_sequence()
     # testing addition command line options
     scalc_reference2 = ["89", "15.2", "32.3"]
     scalc2 = Test_instance('scalc.py', scalc_infile, scalc_outfile, scalc_reference2, scalc_wrong, None, False, '-v')
     scalc2.list_sequence()
     #
     scalc_reference3 = ["100" ,"21.1", "90.0"]
     scalc3 = Test_instance('scalc.py', scalc_infile, scalc_outfile, scalc_reference3, scalc_wrong, None, False, '-a')
     scalc3.list_sequence()
     #
     scalc_reference4 = ["99", "19.8", "90.0"]
     scalc4 = Test_instance('scalc.py', scalc_infile, scalc_outfile, scalc_reference4, scalc_wrong, None, False, '-p')
     scalc4.list_sequence()
     # 
     scalc_reference5 = ["100", "21.1", "180.0"] 
     scalc5 = Test_instance('scalc.py', scalc_infile, scalc_outfile, scalc_reference5, scalc_wrong, None, False, '-C')
     scalc5.list_sequence()
     #
     scalc_reference6 = ["71", "10.9", "20.0"]
     scalc6 = Test_instance('scalc.py', scalc_infile, scalc_outfile, scalc_reference6, scalc_wrong, None, False, '-c', '20')
     scalc6.list_sequence()
     #
     scalc_reference7 = ["90", "15.9", "33.6"]
     scalc7 = Test_instance('scalc.py', scalc_infile, scalc_outfile, scalc_reference7, scalc_wrong, None, False, '-p', '-C', '-v', '-a', '-c', '20')
     scalc7.list_sequence()

def complete_scalc_magic_test():
     """test scalc_magic.py"""
     scalc_magic_infile = 'scalc_magic_example.txt'
     scalc_magic_outfile = None
     scalc_magic_reference = ['13', '17.8', '90.0']
     scalc_magic_wrong = [1, 2, 3, 4]
     scalc_magic = Test_instance('scalc_magic.py', scalc_magic_infile, scalc_magic_outfile, scalc_magic_reference, scalc_magic_wrong, None, False)
     scalc_magic.list_sequence()
     # not testing every single option because they are essentially the same as scalc.py above
     scalc_magic_reference2 = ['21','16.8','35.3']
     scalc_magic2 = Test_instance('scalc_magic.py', scalc_magic_infile, scalc_magic_outfile, scalc_magic_reference2, scalc_magic_wrong, None, False, '-p', '-C', '-v', '-a', '-c', '20')
     scalc_magic2.list_sequence()

def complete_s_hext_test(): # list type
     """test s_hext.py"""
     s_hext_infile = "s_hext_example.dat"
     s_hext_outfile = None
     s_hext_reference = s_hext_correct
     s_hext_wrong = ["wrong", "wronger"]
     s_hext = Test_instance('s_hext.py', s_hext_infile, s_hext_outfile, s_hext_reference, s_hext_wrong, None, False)
     s_hext.list_sequence()

s_hext_correct = ['F', '=', '2.56', 'F12', '=', '1.12', 'F23', '=', '2.16', 'N', '=', '8', 'sigma', '=', '0.000815076759', '0.33471', '265.8', '17.6', '40.3', '93.0', '72.2', '19.6', '356.5', '2.1', '0.33349', '93.0', '72.2', '31.4', '356.5', '2.1', '40.3', '265.8', '17.6', '0.33180', '356.5', '2.1', '19.6', '265.8', '17.6', '31.4', '93.0', '72.2']

def complete_vgp_di_test(): # list type
     """test vgp_di.py"""
     vgp_di_infile = 'vgp_di_example.dat'
     vgp_di_outfile = None
     vgp_di_reference = ['335.6', '62.9']
     vgp_di_wrong = ['335.6', '20']
     vgp_di = Test_instance('vgp_di.py', vgp_di_infile, vgp_di_outfile, vgp_di_reference, vgp_di_wrong, None, False)
     vgp_di.list_sequence()

def complete_watsonsF_test(): # list/stdout type
     """test_watsonsF.py"""
     watsonsF_infile = "watsonsF_example_file1.dat"
     watsonsF_infile2 = file_prefix + "watsonsF_example_file2.dat"
     watsonsF_outfile = None
     watsonsF_reference = ["5.23074427567", "3.2594"]
     watsonsF_wrong = ["5.23074427567", "3.2394"]
     watsonsF = Test_instance('watsonsF.py', watsonsF_infile, watsonsF_outfile, watsonsF_reference, watsonsF_wrong, None, False, '-f2', watsonsF_infile2)
     watsonsF.list_sequence()

# File in/file out ones

def complete_apwp_test():
     """test apwp.py"""
     apwp = Test_instance('apwp.py', 'apwp_example.dat', 'apwp_results_new.out', 'apwp_results_correct.out', 'apwp_results_incorrect.out', None, False)
     apwp.file_in_file_out_sequence(interactive=True)
     
def complete_b_vdm_test():
     """test b_vdm.py"""
     b_vdm = Test_instance('b_vdm.py', 'b_vdm_example.dat', 'b_vdm_results_new.out', 'b_vdm_results_correct.out', 'b_vdm_results_incorrect.out', None, False)
     b_vdm.file_in_file_out_sequence(interactive=True)

def complete_cart_dir_test():
     """test cart_dir.py"""
     cart_dir = Test_instance('cart_dir.py', 'cart_dir_example.dat', 'cart_dir_results_new.out', 'cart_dir_results_correct.out', 'cart_dir_results_incorrect.out', None, False)
     cart_dir.file_in_file_out_sequence(interactive=True)
    
def complete_convert_samples_test(): # irregular.  "-F" option does not work correctly, so outfile must be assigned later. also, -OD option
     """test convert_samples.py"""
     subprocess.call('rm orient_Northern_Iceland.txt', shell=True)
     convert_samples = Test_instance('convert_samples.py', 'convert_samples_example.dat', "", 'convert_samples_results_correct.out', 'convert_samples_results_incorrect.out', None, True)
     obj = env.run('convert_samples.py', '-f', 'convert_samples_example.dat', '-WD', directory, '-OD', directory)
     print obj.stdout
     convert_samples.test_help()
     convert_samples.outfile = file_prefix + 'orient_Northern_Iceland.txt'
     convert_samples.check_file_output(convert_samples.outfile, convert_samples.ref_out)
     convert_samples.unittest_file()

def complete_di_geo_test():
     """test di_geo.py"""
     di_geo = Test_instance('di_geo.py', 'di_geo_example.dat', 'di_geo_results_new.out', 'di_geo_results_correct.out', 'di_geo_results_incorrect.out', None, False)
     di_geo.file_in_file_out_sequence(interactive=True)

def complete_di_tilt_test():
     """test di_tilt.py"""
     di_tilt = Test_instance('di_tilt.py', 'di_tilt_example.dat', 'di_tilt_results_new.out', 'di_tilt_results_correct.out', 'di_tilt_results_incorrect.out', None, False)
     di_tilt.file_in_file_out_sequence(interactive=True)

def complete_dir_cart_test():
     """test dir_cart.py"""
     dir_cart = Test_instance('dir_cart.py', 'dir_cart_example.dat', 'dir_cart_results_new.out', 'dir_cart_results_correct.out', 'dir_cart_results_incorrect.out', None, False)
     dir_cart.file_in_file_out_sequence(interactive=True)

def complete_di_rot_test():
     """test di_rot.py"""
     di_rot = Test_instance('di_rot.py', 'di_rot_example.dat', 'di_rot_results_new.out', 'di_rot_results_correct.out', 'di_rot_results_incorrect.out', None, False)
     di_rot.file_in_file_out_sequence()

def complete_di_vgp_test():
     """test di_vgp.py"""
     di_vgp = Test_instance('di_vgp.py', 'di_vgp_example.dat', 'di_vgp_results_new.out', 'di_vgp_results_correct.out', 'di_vgp_results_incorrect.out', None, False)
     di_vgp.file_in_file_out_sequence(interactive=True)

def complete_eigs_s_test():
     """test eigs_s.py"""
     eigs_s = Test_instance('eigs_s.py', 'eigs_s_example.dat', 'eigs_s_results_new.out', 'eigs_s_results_correct.out', 'eigs_s_results_incorrect.out', None, False)
     eigs_s.file_in_file_out_sequence()

def complete_eq_di_test():
     """test eq_di.py"""
     eq_di = Test_instance('eq_di.py', 'eq_di_example.dat', 'eq_di_results_new.out', 'eq_di_results_correct.out', 'eq_di_results_incorrect.out', None, False)
     eq_di.file_in_file_out_sequence()

def complete_gobing_test():
     """test gobing.py"""
     gobing = Test_instance('gobing.py', 'gobing_example.out', 'gobing_results_new.out', 'gobing_results_correct.out', 'gobing_results_incorrect.out', None, False)
     gobing.file_in_file_out_sequence()

def complete_gofish_test():
     """test gofish.py"""
     gofish = Test_instance('gofish.py', 'gofish_example.out', 'gofish_results_new.out', 'gofish_results_correct.out', 'gofish_results_incorrect.out', None, False)
     gofish.file_in_file_out_sequence()

def complete_gokent_test():
     """test gokent.py"""
     gokent = Test_instance('gokent.py', 'gokent_example.out', 'gokent_results_new.out', 'gokent_results_correct.out', 'gokent_results_incorrect.out', None, False)
     gokent.file_in_file_out_sequence()
    # no interactive  

def complete_goprinc_test():
     """test go_princ.py"""
     goprinc = Test_instance('goprinc.py', 'goprinc_example.dat', 'goprinc_results_new.out', 'goprinc_results_correct.out', 'goprinc_results_incorrect.out', None, False)
     goprinc.file_in_file_out_sequence()

def complete_igrf_test(): # runs as file in, file out, but then also with alternative command line options
     """test igrf.py"""
     igrf = Test_instance('igrf.py', 'igrf_example.dat', 'igrf_results_new.out', 'igrf_results_correct.out', 'igrf_results_incorrect.out', None, False)
     igrf.file_in_file_out_sequence(interactive=True)
     igrf.arg_0 = "-plt"
     igrf.arg_1 = "-alt"
     igrf.arg_2 = 8
     igrf.arg_3 = "loc"
     igrf.arg_4 = 10
     igrf.arg_5 = 10
     igrf.stdin = 'a'
     igrf.ref_out = "{'igrf.svg': <FoundFile ./new-test-output:igrf.svg>}"
     igrf.wrong_out = "heyo"
     igrf.plot_program_sequence(stdout=False)
     igrf.arg_1 = None
     igrf.arg_2 = '-ages'
     igrf.arg_3 = 1
     igrf.arg_4 = 500
     igrf.arg_5 = 2
     igrf.plot_program_sequence(stdout=False)


def complete_k15_s_test():
     """test k15.py"""
     k15_s = Test_instance('k15_s.py', 'k15_s_example.dat', 'k15_s_results_new.out', 'k15_s_results_correct.out', 'k15_s_results_incorrect.out', None, False)
     # runs program with extra command line options, then makes sure it has different output than running it without those option
     k15_s.file_in_file_out_sequence()
     k15_s.arg_0 = '-crd'
     k15_s.arg_1 = 'g'
     k15_s.arg_2 = "t"
     k15_s.outfile = file_prefix + 'k15_s_results_other_new.out'
     k15_s.run_program(output_type="file")
     try:
          k15_s.check_file_output(k15_s.outfile, 'k15_s_results_new.out')
     except NameError as er:
          print "Files were appropriately different"
          print er
          print type(er)
  
def complete_mk_redo_test():
     """test mk_redo.py"""
     mk_redo = Test_instance('mk_redo.py', 'mk_redo_example.txt', 'mk_redo_results_new.out', 'mk_redo_results_correct.out', 'mk_redo_results_incorrect.out', None, True)
     mk_redo.file_in_file_out_sequence()

def complete_s_eigs_test():
     """test s_eigs.py"""
     s_eigs = Test_instance('s_eigs.py', 's_eigs_example.dat', 's_eigs_results_new.out', 's_eigs_results_correct.out', 's_eigs_results_incorrect.out', None, False)
     s_eigs.file_in_file_out_sequence()

def complete_s_geo_test():
     """test s_geo.py"""
     s_geo = Test_instance('s_geo.py', 's_geo_example.dat', 's_geo_results_new.out', 's_geo_results_correct.out', 's_geo_results_incorrect.out', None, False)
     s_geo.file_in_file_out_sequence()

def complete_s_tilt_test():
     """test s_tilt.py"""
     s_tilt = Test_instance('s_tilt.py', 's_tilt_example.dat', 's_tilt_results_new.out', 's_tilt_results_correct.out', 's_tilt_results_incorrect.out', None, False)
     s_tilt.file_in_file_out_sequence()

def complete_stats_test():
     """test stats.py"""
     stats = Test_instance('stats.py', 'stats_example.dat', 'stats_results_new.out', 'stats_results_correct.out', 'stats_results_incorrect.out', None, False)
     stats.file_in_file_out_sequence()

def complete_vdm_b_test():
     """test vdm_b.py"""
     vdm_b = Test_instance('vdm_b.py', 'vdm_b_example.dat', 'vdm_b_results_new.out', 'vdm_b_results_correct.out', 'vdm_b_results_incorrect.out', None, False)
     vdm_b.file_in_file_out_sequence(interactive=True)

def complete_vector_mean_test():
     """test vector_mean.py"""
     infile = "vector_mean_example.dat"
     outfile = "vector_mean_results_new.out"
     reference = "vector_mean_results_correct.out"
     wrong = "vector_mean_results_incorrect.out"
     vector_mean = Test_instance('vector_mean.py', infile, outfile, reference, wrong, None, False)
     vector_mean.file_in_file_out_sequence()

# end of file section : ) 

# beginning of Plotting section

ani_depthplot_infile = 'ani_depthplot_rmag_anisotropy.txt'
ani_depthplot_outfile = None
ani_depthplot_reference = "{'U1359A_ani-depthplot.svg': <FoundFile ./new-test-output:U1359A_ani-depthplot.svg>}"
ani_depthplot_wrong = "No way"
ani_depthplot_fsa = 'ani_depthplot_er_samples.txt'

def complete_ani_depthplot_test():
     """test ani_depthplot.py"""
     print "Testing ani_depthplot.py"
     ani_depthplot_infile = 'ani_depthplot_rmag_anisotropy.txt'
     ani_depthplot_outfile = None
     ani_depthplot_reference = "{'U1359A_ani-depthplot.svg': <FoundFile ./new-test-output:U1359A_ani-depthplot.svg>}"
     ani_depthplot_wrong = "No way"
     ani_depthplot_fsa = 'ani_depthplot_er_samples.txt'
     ani_depthplot = Test_instance('ani_depthplot.py', ani_depthplot_infile, ani_depthplot_outfile, ani_depthplot_reference, ani_depthplot_wrong, 'a', True, '-fsa', ani_depthplot_fsa)
     ani_depthplot.plot_program_sequence(stdout=False)
     # testing extra options
     ani_depthplot = Test_instance('ani_depthplot.py', ani_depthplot_infile, ani_depthplot_outfile, ani_depthplot_reference, ani_depthplot_wrong, 'a', True, '-fsa', ani_depthplot_fsa, '-ds', 'mcd', '-sav')
     ani_depthplot.run_program()
     ani_depthplot = Test_instance('ani_depthplot.py', ani_depthplot_infile, ani_depthplot_outfile, ani_depthplot_reference, ani_depthplot_wrong, 'a', True, '-fsa', ani_depthplot_fsa, '-d', '1', '100')
     ani_depthplot.run_program()
   
def weird_ani_depthplot_test(): # irregular..? why is this here??
     """weird ani_depthplot_test"""
     print "weird test"
     try:
          complete_ani_depthplot_test()
     except:
          print "exception raised"
          obj = env.run('ani_depthplot.py', '-WD', directory, '-f', ani_depthplot_infile, '-f', ani_depthplot_outfile, '-fsa', ani_depthplot_fsa, stdin = 'a')
          print obj.stdout

def complete_basemap_magic_test():
     """test_basemap_magic.py"""
     basemap_magic_infile = 'basemap_example.txt'
     basemap_magic_outfile = None
     basemap_magic_reference = "{'Site_map.pdf': <FoundFile ./new-test-output:Site_map.pdf>}"
     basemap_magic_wrong = "wrong"
     basemap_magic = Test_instance('basemap_magic.py', basemap_magic_infile, basemap_magic_outfile, basemap_magic_reference, basemap_magic_wrong, 'a', True)
     basemap_magic.plot_program_sequence(stdout=False)

def complete_biplot_magic_test():
     """test biplot_magic.py"""
     biplot_magic_infile = 'biplot_magic_example.dat'
     biplot_magic_outfile = None
     biplot_magic_reference = """LP-X  selected for X axis
LT-AF-I  selected for Y axis
All
measurement_magn_mass  being used for plotting Y
measurement_chi_mass  being used for plotting X.
S[a]ve plots, [q]uit,  Return for next plot """
     biplot_magic_wrong = 1235.
     biplot_magic = Test_instance('biplot_magic.py', biplot_magic_infile, biplot_magic_outfile, biplot_magic_reference, biplot_magic_wrong, 'q', False, '-x', 'LP-X', '-y', 'LT-AF-I')
     biplot_magic.plot_program_sequence(stdout=True)

def complete_chi_magic_test():
     """test chi_magic.py"""
     chi_magic_infile = 'chi_magic_example.dat'
     chi_magic_outfile = None
     chi_magic_reference = "{'IRM-OldBlue-1892_2.svg': <FoundFile ./new-test-output:IRM-OldBlue-1892_2.svg>, 'IRM-OldBlue-1892_3.svg': <FoundFile ./new-test-output:IRM-OldBlue-1892_3.svg>, 'IRM-OldBlue-1892_1.svg': <FoundFile ./new-test-output:IRM-OldBlue-1892_1.svg>}"
     chi_magic_wrong = "wrong"
     chi_magic = Test_instance('chi_magic.py', chi_magic_infile, chi_magic_outfile, chi_magic_reference, chi_magic_wrong, 'a', False)
     chi_magic.plot_program_sequence(stdout=False)

def complete_common_mean_test(): # Irregular type: a little fanciness after the standard stuff
     """test common_mean.py"""
     common_mean_infile = 'common_mean_ex_file1.dat'
     common_mean_outfile = None
     common_mean_reference = "{'CD_X.svg': <FoundFile ./new-test-output:CD_X.svg>, 'CD_Y.svg': <FoundFile ./new-test-output:CD_Y.svg>, 'CD_Z.svg': <FoundFile ./new-test-output:CD_Z.svg>}"
     common_mean_wrong = "wrong"
     common_mean_f2 = file_prefix + 'common_mean_ex_file2.dat'
     common_mean = Test_instance('common_mean.py', common_mean_infile, common_mean_outfile, common_mean_reference, common_mean_wrong, 'a', False, '-f2', common_mean_f2)
     common_mean.plot_program_sequence(stdout=False)
     # testing with -dir option
     common_mean_2 = Test_instance('common_mean.py', common_mean_infile, common_mean_outfile, common_mean_reference, common_mean_wrong, 'a', False, '-dir', '0', '9.9')
     obj = env.run('common_mean.py', '-f', file_prefix + common_mean_infile, '-f2', common_mean_f2, stdin='a')
     if obj.files_updated:
          print "Successfully updated file"
     else:
          raise NameError("common_mean.py with -dir option did not update plots")

def complete_core_depthplot_test():
     """test core_depthplot.py"""
     core_depthplot_infile = 'core_depthplot_example.dat'
     core_depthplot_outfile = None
     core_depthplot_reference = "{'DSDP Site 522_m:_LT-AF-Z_core-depthplot.svg': <FoundFile ./new-test-output:DSDP Site 522_m:_LT-AF-Z_core-depthplot.svg>}"
     core_depthplot_wrong = "wrong"
     core_depthplot_fsa = 'core_depthplot_er_samples.txt'
     core_depthplot = Test_instance('core_depthplot.py', core_depthplot_infile, core_depthplot_outfile, core_depthplot_reference, core_depthplot_wrong, 'a', True, '-fsa', core_depthplot_fsa, '-LP', 'AF', '15')
     core_depthplot.plot_program_sequence(stdout=False)

def complete_dayplot_magic_test():
     """test dayplot_magic.py"""
     dayplot_magic_infile = 'dayplot_magic_example.dat'
     dayplot_magic_outfile = None
     dayplot_magic_reference = "{'LO:_unknown_SI:__SA:__SP:__TY:_day_.svg': <FoundFile ./new-test-output:LO:_unknown_SI:__SA:__SP:__TY:_day_.svg>, 'LO:_unknown_SI:__SA:__SP:__TY:_S-Bc_.svg': <FoundFile ./new-test-output:LO:_unknown_SI:__SA:__SP:__TY:_S-Bc_.svg>, 'LO:_unknown_SI:__SA:__SP:__TY:_S-Bcr_.svg': <FoundFile ./new-test-output:LO:_unknown_SI:__SA:__SP:__TY:_S-Bcr_.svg>}"
     dayplot_magic_wrong = "wrong"
     dayplot_magic = Test_instance('dayplot_magic.py', dayplot_magic_infile, dayplot_magic_outfile, dayplot_magic_reference, dayplot_magic_wrong, 'a', True)
     dayplot_magic.plot_program_sequence(stdout=False)

def complete_dmag_magic_test():
     """test dmag_magic.py"""
     dmag_magic_infile = 'dmag_magic_example.dat'
     dmag_magic_outfile = None
     dmag_magic_reference = "{'McMurdo_LT-AF-Z.svg': <FoundFile ./new-test-output:McMurdo_LT-AF-Z.svg>}"
     dmag_magic_wrong = "wrong"
     dmag_magic = Test_instance('dmag_magic.py', dmag_magic_infile, dmag_magic_outfile, dmag_magic_reference, dmag_magic_wrong, 'a', False)
     dmag_magic.plot_program_sequence(stdout=False)

def complete_eqarea_test():
     """test eqarea.py"""
     eqarea_infile = 'eqarea_example.dat'
     eqarea_outfile = None
     eqarea_reference = "{'eq.svg': <FoundFile ./new-test-output:eq.svg>}"
     eqarea_wrong = "wrong"
     eqarea = Test_instance('eqarea.py', eqarea_infile, eqarea_outfile, eqarea_reference, eqarea_wrong, 'a', False)
     eqarea.plot_program_sequence(stdout=False)

def complete_eqarea_ell_test():
     """test eqarea_ell.py"""
     eqarea_ell_infile = 'eqarea_ell_example.dat'
     eqarea_ell_outfile = None
     eqarea_ell_reference = """Zdec   137.8
     Edec   235.4
     Eta     2.9
     n        100
     Einc    17.7
     Zinc    22.6
     Zeta     2.1
     dec     0.0
     inc    60.7
 S[a]ve to save plot, [q]uit, Return to continue:"""
     eqarea_ell_wrong = "wrong"
     eqarea_ell = Test_instance('eqarea_ell.py', eqarea_ell_infile, eqarea_ell_outfile, eqarea_ell_reference, eqarea_ell_wrong, 'q', False, '-ell', 'B')
     eqarea_ell.plot_program_sequence(stdout=True)

def complete_fishqq_test(): # irregular type, because it produces a useful outfile as well as a plot
     """test fishqq.py"""
     fishqq_infile = 'fishqq_example.dat'
     fishqq_outfile = 'fishqq_results_new.out'
     fishqq_reference = "{'exp1.svg': <FoundFile ./new-test-output:exp1.svg>, 'unf1.svg': <FoundFile ./new-test-output:unf1.svg>}"
     # not sure why the order switched....
     new_fishqq_reference = "{'unf1.svg': <FoundFile ./new-test-output:unf1.svg>, 'exp1.svg': <FoundFile ./new-test-output:exp1.svg>}"  # sometimes this one is correct, sometimes the other.  huh.
     fishqq_file_reference = 'fishqq_results_correct.out'
     fishqq_wrong = "wrong"
     fishqq = Test_instance('fishqq.py', fishqq_infile, fishqq_outfile, fishqq_reference, fishqq_wrong, 'a', False)
     fishqq.plot_program_sequence(stdout=False)
     fishqq.check_file_output(fishqq.outfile, fishqq_file_reference)

def complete_foldtest_magic_test(): 
     """test foldtest_magic.py"""
     foldtest_magic_infile = 'foldtest_magic_example.txt'
     foldtest_magic_outfile = 'foldtest_magic_results_new.out'
     foldtest_magic_reference = "{'foldtest_ge.svg': <FoundFile ./new-test-output:foldtest_ge.svg>, 'foldtest_st.svg': <FoundFile ./new-test-output:foldtest_st.svg>, 'foldtest_ta.svg': <FoundFile ./new-test-output:foldtest_ta.svg>}"
     foldtest_magic_wrong = [1, 2, 3]
     foldtest_magic_fsa = 'foldtest_magic_er_samples.txt'
     foldtest_magic = Test_instance('foldtest_magic.py', foldtest_magic_infile, foldtest_magic_outfile, foldtest_magic_reference, foldtest_magic_wrong, 'a', True,  '-fsa', foldtest_magic_fsa, '-n', '100')
     foldtest_magic.plot_program_sequence(stdout=False)

def complete_foldtest_test(): # irregular -- can't really check the outfile, because it is bootstrappy
     """test foldtest.py"""
     print"Testing foldtest.py"
     foldtest_infile = 'foldtest_example.dat'
     foldtest_outfile = 'foldtest_results_new.out'
     foldtest_reference = """{'foldtest_ge.svg': <FoundFile ./new-test-output:foldtest_ge.svg>, 'foldtest_st.svg': <FoundFile ./new-test-output:foldtest_st.svg>, 'foldtest_ta.svg': <FoundFile ./new-test-output:foldtest_ta.svg>}"""
     foldtest_wrong = "wrong"
     foldtest = Test_instance('foldtest.py', foldtest_infile, foldtest_outfile, foldtest_reference, foldtest_wrong, 'a', False, '-n', 50, '-u', 30)
     foldtest.plot_program_sequence(stdout=False)

def complete_histplot_test():
     """test histplot.py"""
     print"Testing histplot.py"
     histplot_infile = 'extra_histplot_sample.out'
     histplot_outfile = None
     histplot_reference = "{'hist.svg': <FoundFile ./new-test-output:hist.svg>}"
     histplot_wrong = "wrong"
     histplot = Test_instance('histplot.py', histplot_infile, histplot_outfile, histplot_reference, histplot_wrong, 'a', False)
     histplot.plot_program_sequence(stdout=False)

def complete_irmaq_magic_test():
     """test irmaq_magic.py"""
     print"Testing irmaq_magic.py"
     irmaq_magic_infile = 'irmaq_magic_measurements.txt'
     irmaq_magic_outfile = None
     irmaq_magic_reference = "{'U1359A_LP-IRM.svg': <FoundFile ./new-test-output:U1359A_LP-IRM.svg>}"
     irmaq_magic_wrong = 8
     irmaq_magic = Test_instance('irmaq_magic.py', irmaq_magic_infile, irmaq_magic_outfile, irmaq_magic_reference, irmaq_magic_wrong, 'a', True)
     irmaq_magic.plot_program_sequence(stdout=False)

def complete_lnp_magic_test(): # irregular type.  it had to be written the long way, because it won't run with -F.  
     """test lnp_magic.py"""
     PT.clean_house() # because it doesn't have run_program()
     print"Testing lnp_magic.py"
     lnp_magic_infile = 'lnp_magic_pmag_specimens.txt'
     lnp_magic_outfile = None
     lnp_magic_reference = PT.file_parse_by_word(file_prefix + 'lnp_magic_output_correct.txt')
     lnp_magic_wrong = ['sv01', 'Site', 'lines', 'planes', 'kappa', 'a95', 'dec', 'I am not right']
     lnp_magic = Test_instance('lnp_magic.py', lnp_magic_infile, lnp_magic_outfile, lnp_magic_reference, lnp_magic_wrong, None, True, '-crd', 'g', '-P')
     raise NameError("-F option doesn't work")
     lnp_magic.run_program()
     obj = env.run('lnp_magic.py', '-WD', directory, '-f', 'lnp_magic_pmag_specimens.txt', '-crd', 'g', '-P')
     result = str(obj.stdout).split()
     lnp_magic.test_help()
     lnp_magic.check_list_output(result, lnp_magic.ref_out)
     lnp_magic.unittest_list()

def complete_lowrie_test():
     """test lowrie.py"""
     print "Testing lowrie.py"
     lowrie_infile = 'lowrie_example.dat'
     lowrie_outfile = None
     lowrie_reference = """318-U1359A-002H-1-W-109
S[a]ve figure? [q]uit, <return> to continue"""
     lowrie_wrong = "wrong"
     lowrie = Test_instance('lowrie.py', lowrie_infile, lowrie_outfile, lowrie_reference, lowrie_wrong, 'q', False)
     lowrie.plot_program_sequence(stdout=True)

def complete_lowrie_magic_test():
     """test lowrie_magic.py"""
     print "testing lowrie_magic.py"
     infile = 'lowrie_magic_example.dat'
     outfile = None
     reference = """318-U1359A-002H-1-W-109
S[a]ve figure? [q]uit, <return> to continue"""
     wrong = "1, 2, 3, 4"
     lowrie_magic = Test_instance('lowrie_magic.py', infile, outfile, reference, wrong, 'q', True)
     lowrie_magic.plot_program_sequence(stdout=True)

def complete_plot_cdf_test():
     """test plot_cdf.py"""
     PT.clean_house() 
     print"Testing plot_cdf.py"
     infile =  "plot_cdf_example.dat"
     outfile = None
     reference = "{'CDF_.svg': <FoundFile ./new-test-output:CDF_.svg>}"
     wrong = "Not right"
     plot_cdf = Test_instance('plot_cdf.py', infile, outfile, reference, wrong, 'a', False)
     plot_cdf.plot_program_sequence(stdout=False)

def complete_plotdi_a_test():
     """test plotdi_a.py"""
     print "Testing plotdi_a.py"
     plotdi_a_infile = "plotdi_a_example.dat"
     plotdi_a_outfile = None
     plotdi_a_reference = "{'eq.svg': <FoundFile ./new-test-output:eq.svg>}"
     plotdi_a_wrong = ['1', 'one']
     plotdi_a = Test_instance('plotdi_a.py', plotdi_a_infile, plotdi_a_outfile, plotdi_a_reference, plotdi_a_wrong, 'a', False)
     plotdi_a.plot_program_sequence(stdout=False)

def complete_plotxy_test():
     """test_plotXY.py"""
     plotxy_infile = 'plotxy_example.dat'
     plotxy_outfile = None
     plotxy_reference = "{'plotXY.svg': <FoundFile ./new-test-output:plotXY.svg>}"
     plotxy_wrong = ["something", 2]
     plotxy = Test_instance('plotxy.py', plotxy_infile, plotxy_outfile, plotxy_reference, plotxy_wrong, 'a', False, '-l')
     plotxy.plot_program_sequence(stdout=False)

def complete_qqplot_test():  # irregular type.  produces a lot of output, which is then parsed out.  
     """test qqplot.py"""
     qqplot_infile = "qqplot_example.dat"
     qqplot_outfile = None
     qqplot_reference_output = [10.12243251, 2.79670530387, 0.0558584072909, 0.0886]
     qqplot_wrong_output = [10.12243251, 2., 0., 0.]
     qqplot = Test_instance('qqplot.py', qqplot_infile, qqplot_outfile, qqplot_reference_output, qqplot_wrong_output, 'a', False)
     qqplot_output = qqplot.run_program(output_type='stdout')
     qqplot_list_out = str(qqplot_output).split()
     qqplot_clean_out = []
     for num, i in enumerate(qqplot_list_out): # isolates the relevant numbers for testing
          print num
          print i
          if str(i) == '1':  # this prevents the 1 from "1 plot saved" being put into the array of answers
             pass
          else:
               try:
                    qqplot_clean_out.append(float(i))
                    print qqplot_clean_out
               except ValueError:
                    pass
     qqplot.check_output(qqplot_clean_out, qqplot.ref_out)
     qqplot.test_help()
     qqplot.unittest_list()

def complete_quick_hyst_test():
     """test quick_hyst.py"""
     quick_hyst_infile = 'quick_hyst_example.dat'
     quick_hyst_outfile = None
     quick_hyst_reference = """IS06a-1 1 out of  8
working on t:  273
S[a]ve plots, [s]pecimen name, [q]uit, <return> to continue
 Good bye"""
     quick_hyst_wrong = "wrong"
     quick_hyst = Test_instance('quick_hyst.py', quick_hyst_infile, quick_hyst_outfile, quick_hyst_reference, quick_hyst_wrong, 'q', True)
     quick_hyst.plot_program_sequence(stdout=True)

def complete_revtest_test():
     """test revtest.py"""
     revtest_infile = 'revtest_example.dat'
     revtest_outfile = None
     revtest_reference = "{'REV_Z.svg': <FoundFile ./new-test-output:REV_Z.svg>, 'REV_Y.svg': <FoundFile ./new-test-output:REV_Y.svg>, 'REV_X.svg': <FoundFile ./new-test-output:REV_X.svg>}"
     revtest_wrong = "not right"
     revtest = Test_instance('revtest.py', revtest_infile, revtest_outfile, revtest_reference, revtest_wrong, 'a', False)
     revtest.plot_program_sequence(stdout=False)

def complete_revtest_magic_test():
     """test revtest_magic.py"""
     revtest_magic_infile = 'revtest_magic_example.txt'
     revtest_magic_outfile = None
     revtest_magic_reference = "{'REV_Z.svg': <FoundFile ./new-test-output:REV_Z.svg>, 'REV_Y.svg': <FoundFile ./new-test-output:REV_Y.svg>, 'REV_X.svg': <FoundFile ./new-test-output:REV_X.svg>}"
     revtest_magic_wrong = "wrong"
     revtest_magic = Test_instance('revtest_magic.py', revtest_magic_infile, revtest_magic_outfile, revtest_magic_reference, revtest_magic_wrong, 'a', True)
     revtest_magic.plot_program_sequence(stdout=False)

def complete_site_edit_magic_test():
    """test_site_edit_magic.py"""
    site_edit_magic_reference = """sr01
specimen, dec, inc, n_meas/MAD,| method codes 
sr01a1:   331.0    64.5 9 / 1.8 | LP-DIR-T:DE-BFL
sr01a2:   325.9    62.1 10 / 0.9 | LP-DIR-T:DE-BFL
sr01c2:   345.0    64.3 9 / 3.0 | LP-DIR-T:DE-BFL
sr01d1:   327.0    65.2 10 / 1.9 | LP-DIR-T:DE-BFL
sr01e2:   332.9    67.0 10 / 1.9 | LP-DIR-AF:DE-BFL
sr01f2:   325.9    66.1 15 / 1.6 | LP-DIR-T:DE-BFL
sr01g2:   324.3    66.7 10 / 2.6 | LP-DIR-AF:DE-BFL
sr01i1:   328.5    62.5 9 / 2.8 | LP-DIR-T:DE-BFL

 Site lines planes  kappa   a95   dec   inc
sr01 8  0     574      2.3    330.1     64.9  7.9878 
s[a]ve plot, [q]uit, [e]dit specimens, <return> to continue:"""
    site_edit_magic_wrong = "wrong"
    site_edit_magic_infile = 'site_edit_example.dat'
    site_edit_fsa = 'site_edit_er_samples.txt'
    site_edit_magic_outfile = None
    site_edit = Test_instance('site_edit_magic.py', site_edit_magic_infile, site_edit_magic_outfile, site_edit_magic_reference, site_edit_magic_wrong, 'q', True, '-fsa', site_edit_fsa)
    site_edit.plot_program_sequence(stdout=True)

def complete_strip_magic_test():
     """test strip_magic.py"""
     strip_magic_infile = 'strip_magic_example.txt'
     strip_magic_outfile = None
     strip_magic_reference = "{'strat.svg': <FoundFile ./new-test-output:strat.svg>}"
     strip_magic_wrong = "hello there"
     strip_magic = Test_instance('strip_magic.py', strip_magic_infile, strip_magic_outfile, strip_magic_reference, strip_magic_wrong, 'a', True, '-x', 'age', '-y', 'lat')
     strip_magic.plot_program_sequence(stdout=False)
     
def complete_thellier_magic_test(): # Irregular
     """test thellier_magic.py"""
     thellier_magic_infile = 'thellier_magic_measurements.txt'
     thellier_magic_reference = PT.file_parse_by_word('thellier_magic_output_correct.out')# this is in a file because it is irritatingly long to keep in the document.  
     print thellier_magic_reference
     thellier_magic_outfile = None
     thellier_magic_wrong = "wrong"
     thellier_magic = Test_instance('thellier_magic.py', thellier_magic_infile, thellier_magic_outfile, thellier_magic_reference, thellier_magic_wrong,  'q', False)
     thellier_magic.list_sequence()

def complete_vgpmap_magic_test():
     """test vgpmap_magic.py"""
     vgpmap_magic_infile = 'vgpmap_magic_pmag_results.txt'
     vgpmap_magic_outfile = None
     vgpmap_magic_reference = "{'VGP_map.pdf': <FoundFile ./new-test-output:VGP_map.pdf>}"
     vgpmap_magic_wrong = "wrong"
     vgpmap_magic = Test_instance('vgpmap_magic.py', vgpmap_magic_infile, vgpmap_magic_outfile, vgpmap_magic_reference, vgpmap_magic_wrong, 'a', True, '-prj', 'ortho', '-eye', '60', '0')
     vgpmap_magic.plot_program_sequence(stdout=False)
#    obj = env.run('vgpmap_magic.py', '-WD', directory, '-f', vgpmap_magic_infile, '-crd', 'g', '-prj', 'ortho', '-eye', '60', '0', '-sym', 'ko', '10', '-fmt', 'png', stdin='a') 

zeq_magic_reference = """sr01a1 0 out of  177
    looking up previous interpretations...
g: 0      0.0  C  4.065e-05   324.1    66.0 
g: 1    100.0  C  3.943e-05   330.5    64.6 
g: 2    150.0  C  3.908e-05   324.9    65.5 
g: 3    200.0  C  3.867e-05   329.4    64.6 
g: 4    250.0  C  3.797e-05   330.3    64.5 
g: 5    300.0  C  3.627e-05   330.1    64.0 
g: 6    350.0  C  3.398e-05   327.0    64.4 
g: 7    400.0  C  2.876e-05   328.2    64.0 
g: 8    450.0  C  2.148e-05   323.8    65.2 
g: 9    500.0  C  1.704e-05   326.0    63.9 
g: 10    525.0  C  1.200e-05   326.5    63.7 
g: 11    550.0  C  5.619e-06   325.5    64.4 

                g/b: indicates  good/bad measurement.  "bad" measurements excluded from calculation

                 set s[a]ve plot, [b]ounds for pca and calculate, [p]revious, [s]pecimen, 
                 change [h]orizontal projection angle,   change [c]oordinate systems, 
                 [d]elete current interpretation(s), [e]dit data,   [q]uit: 
                
<Return>  for  next specimen 
Good bye"""

def complete_zeq_magic_test(): # NOT SURE THIS IS ACTUALLY USEFUL.  Consider
     """test zeq_magic.py"""
     zeq_magic_infile = 'zeq_magic_measurements.txt'
     zeq_magic_outfile = None
#    zeq_magic_reference = See above                                       
     zeq_magic_wrong = "wrong"
     fsa = 'zeq_magic_er_samples.txt'
     fsp = 'zeq_magic_specimens.txt'
     zeq_magic = Test_instance('zeq_magic.py', zeq_magic_infile, zeq_magic_outfile, zeq_magic_reference, zeq_magic_wrong, 'q', True, '-fsa', fsa, '-fsp', fsp, '-crd', 'g')
     zeq_magic.plot_program_sequence(stdout=True)
# could do the below, but it takes forever and creates a TON of files                                                       #    extra_zeq_magic = Plot('zeq_magic.py', zeq_magic_infile, zeq_magic_reference, zeq_magic_wrong, None, True, '-fsa', fsa, '-fsp', fsp, '-sav')                                                          

def complete_zeq_magic_redo_test(): # file type
     """test zeq_magic_redo.py"""
     zeq_redo_infile = 'zeq_magic_redo_measurements.txt'
     zeq_redo_outfile = 'zeq_magic_redo_results_new.out'
     zeq_redo_reference = 'zeq_magic_redo_results_correct.out'
     zeq_redo_wrong = 'zeq_magic_redo_results_incorrect.out'
     fre =  'zeq_magic_redo'
     fsa =  'zeq_magic_redo_er_samples.txt'
     zeq_magic_redo = Test_instance('zeq_magic_redo.py', zeq_redo_infile, zeq_redo_outfile, zeq_redo_reference, zeq_redo_wrong, None, True, '-fre', fre, '-fsa', fsa)
     zeq_magic_redo.file_in_file_out_sequence()


def complete_upload_magic_test(): # irregular.  must be tested in a different directory. 
     """test upload_magic.py"""
     obj = env.run("upload_magic.py", cwd=directory + "/upload_magic") # cwd allows specifying a directory other than the one you are in
     reference = "upload_magic/correct_upload.txt"
     wrong = "upload_magic/incorrect_upload.txt"
     upload_magic = Test_instance("upload_magic.py", None, None, reference, wrong, None, False)
     print obj.stdout
     upload_magic.test_help()
     upload_magic.check_file_output(file_prefix + "upload_magic/upload.txt", upload_magic.ref_out)
     subprocess.call(['rm', 'upload_magic/upload.txt'])

def complete_make_magic_plots_test(): # irregular -- runs in a different directory, specified by cwd
     """test make_magic_plots.py"""
     obj = env.run("make_magic_plots.py", cwd=directory + "/make_magic_plots_example")
     print obj.stdout
     correctfile = file_prefix + "make_magic_plots_output_correct.txt"
     results = PT.output_parse(obj.stdout)
     results_clean = PT.pmagpy_strip(results)
     reference = PT.file_parse_by_word_and_pmagpy_strip(correctfile)
     PT.compare_two_lists(results_clean, reference)
     subprocess.call("rm " + directory + "/make_magic_plots_example/Location_1/*.png", shell=True)

def complete_convert2unix_test(): # irregular
     """test convert2unix.py"""
     obj = env.run("convert2unix.py", "-h")
     stat1 = subprocess.check_output('stat convert2unix_example.dat', shell=True)
     print "stat1:  ", stat1
     obj = env.run("convert2unix.py", file_prefix + "convert2unix_example.dat")
     stat2 = subprocess.check_output('stat convert2unix_example.dat', shell=True)
     print "stat2: ", stat2
     if str(stat1) == str(stat2):
          print "convert2unix did not affect target file"
          raise NameError("convert2unix did not affect target file")
     else:
          print "convert2unix works!"

def complete_curie_test(): # NOT DONE
     """test curie.py"""
     curie = Test_instance('curie.py', 'curie_example.dat', 'curie_results_new.out', 'curie_results_correct.txt', 'curie_results_incorrect.txt', 'a', False)
     try:
          curie.plot_program_sequence()
     except:
          raise NameError('curie.py still has a lone raw_input() at its end...')
     
def complete_plot_magic_keys_test(): # not done --- no way of saving the plot : (
     """test plot_magic_keys.py"""     
     infile = "plot_magic_keys_example.dat"
     outfile = None
     reference = "something"
     wrong = "wrong"
     raise NameError('raw_input at the end')
     plot_magic_keys = Test_instance('plot_magic_keys.py', infile, outfile, reference, wrong, 'a', True, '-xkey', 'average_age', '-ykey', 'average_age_sigma')
     plot_magic_keys.run_program()
     plot_magic_keys.plot_program_sequence(stdout=False)

def complete_measurements_normalize_test(): 
     """test measurements_normalize_test.py"""
     infile = 'measurements_normalize_example.dat'
     outfile = 'measurements_normalize_output_new.out' 
     reference = 'measurements_normalize_output_correct.out'
     wrong = 'measurements_normalize_output_incorrect.out'
     fsp = 'measurements_normalize_specimens_weight.txt'
     measurements_normalize = Test_instance('measurements_normalize.py', infile, outfile, reference, wrong, None, True, '-fsp', fsp)
     measurements_normalize.file_in_file_out_sequence()
#measurements_normalize.py -f measurements_normalize_example.dat -fsp measurements_normalize_specimens_weight.txt -F measurements_normalize_output_new.out 

def complete_s_magic_test():
     """test s_magic.py"""
     infile = 's_magic_example.dat'
     outfile = 's_magic_results_new.out'
     reference = 's_magic_results_correct.out'
     wrong = 's_magic_results_incorrect.out'
     s_magic = Test_instance('s_magic.py', infile, outfile, reference, wrong, None, True, '-loc', 'Camelot', '-usr', 'Merlin')
     s_magic.file_in_file_out_sequence()
#s_magic.py -f s_magic_example.dat -F s_magic_results_new.out -loc Camelot -usr Merlin

# Measurement import stuff
 
def complete_agm_magic_test(): # a little irregular
     """test agm_magic.py"""
     agm_magic_infile = 'agm_magic_example.agm'
     agm_magic_outfile = 'agm_magic_output_new.out'
     agm_magic_reference = 'agm_magic_output_correct.out'
     agm_magic_wrong = 'agm_magic_output_incorrect.out'
     agm = Test_instance('agm_magic.py', agm_magic_infile, agm_magic_outfile, agm_magic_reference, agm_magic_wrong, None, True, '-spn', 'myspec', '--usr', "Lima Tango", '-u', 'cgs')
     agm.file_in_file_out_sequence()
     extra_infile = 'agm_magic_example.irm'
     extra_outfile = 'agm_magic_irm_output_new.out'
     extra_reference = 'agm_magic_extra_output_correct.out'
     extra_wrong = 'agm_magic_extra_output_incorrect.out'
     extra_agm = Test_instance('agm_magic.py', extra_infile, extra_outfile, extra_reference, extra_wrong, None, True, '-spn', 'myspec', '--usr', "Lima Tango", '-bak')
     extra_agm.file_in_file_out_sequence()

def complete_LDEO_magic_test():
     """test LDEO_magic.py"""
     infile = 'ldeo_magic_example.dat'
     outfile = 'ldeo_magic_measurements_new.out'
     reference = 'ldeo_magic_measurements_correct.out'
     wrong = 'ldeo_magic_measurements_incorrect.out'
     ldeo_magic = Test_instance('ldeo_magic.py', infile, outfile, reference, wrong, None, False, '-LP', 'AF', '-loc', 'here')
#     ldeo_magic.run_program()
     ldeo_magic.file_in_file_out_sequence()
#LDEO_magic.py -f ldeo_magic_example.dat -LP AF -F ldeo_magic_measurements.txt -loc here

def complete_sio_magic_test(): # regular-ish, but testing three different infiles.  last one is irregular -- too many command line args
     """test sio_magic.py"""
     infile = "sio_af_example.dat"
     outfile = "sio_af_measurements_new.out"
     reference = "sio_af_measurements_correct.out"
     wrong = "sio_af_measurements_incorrect.out"
     sio_magic = Test_instance('sio_magic.py', infile, outfile, reference, wrong, None, False, '-LP', '-AF', '-spc', '1', '-loc', 'Socorro')
     sio_magic.file_in_file_out_sequence()
     # testing with different infile
     sio_magic2 = Test_instance('sio_magic.py', 'sio_thermal_example.dat', 'sio_thermal_new.out', 'sio_thermal_correct.out', 'sio_thermal_incorrect.out', None, False, '-LP', '-T', '-spc', '1', '-loc', 'Socorro')
     sio_magic2.file_in_file_out_sequence()
     # last infile:
     sio_magic3 = Test_instance('sio_magic.py', 'sio_thellier_example.dat', 'sio_thellier_new.out', 'sio_thellier_correct.out', 'sio_thellier_incorrect.out', None, False)
     obj = env.run('sio_magic.py', '-f', sio_magic3.infile, '-F', sio_magic3.outfile, "-LP", "T", "-spc", "1", "-loc", "Socorro", "-dcg", "25", "0", "90")
     sio_magic3.check_file_output(sio_magic3.outfile, sio_magic3.ref_out)
     sio_magic3.unittest_file()
#% sio_magic.py -f sio_thellier_example.dat -F  thellier_measurements.txt  \  
#      -LP T -spc 1 -loc Socorro -dc 25 0 90  

def complete_TDT_magic_test():
     """test tdt_magic.py"""
     infile = 'tdt_magic_example.dat'
     outfile = 'tdt_out_new.out'
     reference = 'tdt_out_correct.out'
     wrong = 'tdt_out_incorrect.out'
     tdt_magic = Test_instance('TDT_magic.py', infile, outfile, reference, wrong, None, False, '-loc', 'TEST', '-dc', '50.12', '0', '0')
     tdt_magic.file_in_file_out_sequence()

def complete_HUJI_magic_test():
     """test HUJI_magic.py"""
     infile = 'HUJI_magic_example.dat'
     outfile = 'HUJI_magic_new.out'
     reference = 'HUJI_magic_correct.out'
     wrong = 'HUJI_magic_incorrect.out'
     raise NameError('initializing variables were removed')
     HUJI_magic = Test_instance('HUJI_magic.py', infile, outfile, reference, wrong, None, False, '-LP', 'AF')
     HUJI_magic.file_in_file_out_sequence()
#HUJI_magic.py -f HUJI_magic_example.dat -LP AF -F HUJI_magic_new.out

def complete_working_test():
     # the examples
     complete_angle_test()
     complete_zeq_test()
     complete_chartmaker_test()
     complete_di_eq_test()
     # the UCs
     complete_azdip_magic_test()
     complete_combine_magic_test()
     complete_cont_rot_test()
     complete_customize_criteria_test()
     complete_download_magic_test()
     complete_dipole_pinc_test()
     complete_dipole_plat_test()
     complete_grab_magic_key_test()
     complete_incfish_test()
#     complete_magic_select_test() # NEEDS WD!!!!!!!!
     complete_nrm_specimens_magic_test()
     complete_sundec_test()
     complete_pca_test()
     complete_scalc_test()  #  also in bootstrap-plotting
     complete_scalc_magic_test() # also in bootstrap_plotting
     complete_vgp_di_test()
     complete_watsonsF_test()
     # the file types
     complete_apwp_test()
     complete_b_vdm_test()
     complete_cart_dir_test()
     complete_convert_samples_test()
     complete_di_geo_test()
     complete_di_tilt_test()
     complete_dir_cart_test()
     complete_di_rot_test()
     complete_di_vgp_test()
     complete_eigs_s_test()
     complete_eq_di_test()
     complete_gobing_test()
     complete_gofish_test()
     complete_gokent_test()
     complete_goprinc_test()
     complete_igrf_test()
     complete_k15_s_test()
     complete_mk_redo_test()
     complete_pt_rot_test()
     complete_s_eigs_test()
     complete_s_geo_test()
     complete_s_tilt_test()
     complete_stats_test()
     complete_vdm_b_test()
     complete_vector_mean_test()
     complete_zeq_magic_redo_test()
     #PLOTTING
     complete_ani_depthplot_test()
#     weird_ani_depthplot_test()
     complete_basemap_magic_test()
     complete_biplot_magic_test()
     complete_chi_magic_test()  # probs working
     complete_common_mean_test() # same
     complete_core_depthplot_test()
     complete_dayplot_magic_test()
     complete_dmag_magic_test()
     complete_eqarea_test()
     complete_eqarea_ell_test()
     complete_fishqq_test()
     complete_foldtest_magic_test()
     complete_foldtest_test()
     complete_histplot_test()
     complete_irmaq_magic_test()
     complete_lnp_magic_test()
     complete_lowrie_test()
     complete_lowrie_magic_test()
     complete_plot_cdf_test()
     complete_plotdi_a_test()
     complete_plotxy_test()
     complete_qqplot_test()
     complete_quick_hyst_test()
     complete_revtest_test() # Done, but possibly will have stdout added
     complete_revtest_magic_test() # Done, but possibly will have stdout added
     complete_site_edit_magic_test()
     complete_strip_magic_test()
     complete_s_hext_test()
     complete_thellier_magic_test()
     complete_vgpmap_magic_test()
     complete_zeq_magic_test()
     complete_agm_magic_test()
     complete_convert2unix_test()
     complete_upload_magic_test()
     complete_make_magic_plots_test()
#     complete_plot_magic_keys_test()
 #    complete_curie_test()
     complete_measurements_normalize_test() 
     complete_s_magic_test() 
     complete_ldeo_magic_test()
     complete_sio_magic_test()
     complete_TDT_magic_test()
     complete_HUJI_magic_test()

rename_me_tests = {"angle": complete_angle_test, "zeq": complete_zeq_test, "chartmaker": complete_chartmaker_test, "di_eq": complete_di_eq_test, "azdip_magic": complete_azdip_magic_test, "combine_magic": complete_combine_magic_test, "cont_rot": complete_cont_rot_test, "customize_criteria": complete_customize_criteria_test, "download_magic": complete_download_magic_test, "dipole_pinc": complete_dipole_pinc_test, "dipole_plat": complete_dipole_plat_test, "grab_magic_key": complete_grab_magic_key_test, "incfish": complete_incfish_test, "magic_select": complete_magic_select_test, "nrm_specimens": complete_nrm_specimens_magic_test, "sundec": complete_sundec_test, "pca": complete_pca_test, "scalc": complete_scalc_test, "scalc_magic": complete_scalc_magic_test, "vgp_di": complete_vgp_di_test, "watsonsF": complete_watsonsF_test, "apwp": complete_apwp_test, "b_vdm": complete_b_vdm_test, "cart_dir": complete_cart_dir_test, "convert_samples": complete_convert_samples_test, "di_geo": complete_di_geo_test, "di_tilt": complete_di_tilt_test, "dir_cart": complete_dir_cart_test, "di_rot": complete_di_rot_test, "di_vgp": complete_di_vgp_test, "eigs_s": complete_eigs_s_test, "eq_di": complete_eq_di_test, "gobing": complete_gobing_test, "gofish": complete_gofish_test, "gokent": complete_gokent_test, "goprinc": complete_goprinc_test, "igrf": complete_igrf_test, "k15_s": complete_k15_s_test, "mk_redo": complete_mk_redo_test, "pt_rot": complete_pt_rot_test, "s_eigs": complete_s_eigs_test, "s_geo": complete_s_geo_test, "s_tilt": complete_s_tilt_test, "stats": complete_stats_test, "vdm_b": complete_vdm_b_test, "vector_mean": complete_vector_mean_test, "zeq_magic": complete_zeq_magic_redo_test, "ani_depthplot": complete_ani_depthplot_test, "weird_ani_depthplot": weird_ani_depthplot_test, "basemap_magic": complete_basemap_magic_test, "biplot_magic": complete_biplot_magic_test, "chi_magic": complete_chi_magic_test, "common_mean": complete_common_mean_test, "core_depthplot": complete_core_depthplot_test, "dayplot_magic": complete_dayplot_magic_test, "dmag_magic": complete_dmag_magic_test, "eqarea": complete_eqarea_test, "eqarea_ell": complete_eqarea_ell_test, "fishqq": complete_fishqq_test, "foldtest_magic": complete_foldtest_magic_test, "foldtest": complete_foldtest_test, "histplot": complete_histplot_test, "irmaq_magic": complete_irmaq_magic_test, "lnp_magic": complete_lnp_magic_test, "lowrie": complete_lowrie_test, "lowrie_magic": complete_lowrie_magic_test, "plot_cdf": complete_plot_cdf_test, "plotdi_a": complete_plotdi_a_test, "plotxy": complete_plotxy_test, "qqplot": complete_qqplot_test, "quick_hyst": complete_quick_hyst_test, "revtest": complete_revtest_test, "revtest_magic": complete_revtest_magic_test, "site_edit_magic": complete_site_edit_magic_test, "strip_magic": complete_strip_magic_test, "s_hext": complete_s_hext_test, "thellier_magic": complete_thellier_magic_test, "vgpmap_magic": complete_vgpmap_magic_test, "zeq_magic": complete_zeq_magic_test, "agm_magic": complete_agm_magic_test, "upload_magic": complete_upload_magic_test, "make_magic_plots": complete_make_magic_plots_test,"convert2unix": complete_convert2unix_test, "curie": complete_curie_test, "plot_magic_keys": complete_plot_magic_keys_test, "measurements_normalize": complete_measurements_normalize_test, "s_magic": complete_s_magic_test, "ldeo_magic": complete_LDEO_magic_test, "sio_magic": complete_sio_magic_test, "TDT_magic": complete_TDT_magic_test, "HUJI_magic": complete_HUJI_magic_test}

rename_me_errors_list = open('rename_me_errors_list.txt', 'w')

if __name__ == '__main__':
     if "-r" in sys.argv:
          PT.run_individual_program(rename_me_tests)
     elif "-all" in sys.argv:
          complete_working_test()
          print "remember to delete *_new.out files as needed"
     else:
          new_list = EL.go_through(rename_me_tests, rename_me_errors_list)
          EL.redo_broken_ones(new_list)

     
# run as: python Rename_me.py > rename_me_full_output.txt
# then: python clean_output.py
     # input: rename_me_full_output.txt
     # output: rename_me_clean_output.txt



