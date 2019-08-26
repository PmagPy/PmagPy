#!/usr/bin/env python

import sys

from builtins import object
import pandas as pd
import pmagpy.pmag as pmag

class command_line_dataframe(object):
    """
    creates a dataframe used for validating arguments grabbed from sys.argv.
    the dataframe is accessed as self.df.
    the dataframe has three columns -- arg_name, reqd, and default -- and an arbitrary number of rows.
    arg_name is the flag that signals the beginning of a value or list of values, i.e. "-f" for infile(s).
    reqd is a boolean value for whether that flag is required to run the script.
    default is a default value to use if the user doesn't provide that flag.

    to deviate from using the default dataframe, pass in a list of lists with this format: [["f', False, "default.txt"], ...]
    this adds or updates values for "f", indicating that it is not required and does have a default value ("default.txt")
    """

    def __init__(self, changes=None):
        arg_names = ['f', 'F', 'A', 'WD', 'ID', 'Fsa', 'Fsi']
        self.default_dict = {'arg_name': arg_names, 'reqd': [True, False, False, False, False, False, False], 'default': ['', '', '', '.', '.', 'er_samples.txt', 'er_sites.txt']}
        #print(arg_names, len(arg_names))
        self.df = pd.DataFrame(self.default_dict, index=arg_names)
        arg_names = self.df['arg_name']
        if changes:
            for change in changes:
                #print 'change:', change
                if change[0] in arg_names.index:
                    self.df.loc[change[0], 'reqd'] = change[1]
                    self.df.loc[change[0], 'default'] = change[2]
                else:
                    #print 'putting in:', change
                    d = pd.DataFrame({'arg_name': [change[0]], 'reqd': [change[1]], 'default': [change[2]]}, index=[change[0]])
                    self.df = pd.concat([self.df, d], sort=True)

def extract_args(argv):
    """
    take sys.argv that is used to call a command-line script and return a correctly split list of arguments
    for example, this input: ["eqarea.py", "-f", "infile", "-F", "outfile", "-A"]
    will return this output: [['f', 'infile'], ['F', 'outfile'], ['A']]
    """
    string = " ".join(argv)
    string = string.split(' -')
    program = string[0]
    arguments = [s.split() for s in string[1:]]
    return arguments

def check_args(arguments, data_frame):
    """
    check arguments against a command_line_dataframe.
    checks that:
    all arguments are valid
    all required arguments are present
    default values are used where needed
    """
    stripped_args = [a[0] for a in arguments]
    df = data_frame.df
    # first make sure all args are valid
    for a in arguments:
        if a[0] not in df.index:
            print("-I- ignoring invalid argument: {}".format(a[0]))
            print("-")
    # next make sure required arguments are present
    condition = df['reqd']
    reqd_args = df[condition]
    for arg in reqd_args['arg_name']:
        if arg not in stripped_args:
            raise pmag.MissingCommandLineArgException("-"+arg)
    #next, assign any default values as needed

    #condition = df['default'] != '' # don't need this, and sometimes the correct default argument IS ''
    default_args = df #[condition]
    using_defaults = []
    for arg_name, row in default_args.iterrows():
        default = row['default']
        if arg_name not in stripped_args:
            using_defaults.append(arg_name)
            arguments.append([arg_name, default])
    using_defaults = ["-" + arg for arg in using_defaults]
    print('Using default arguments for: {}'.format(', '.join(using_defaults)))
    return arguments

def extract_and_check_args(args_list, dataframe):
    arguments = extract_args(args_list)
    checked_args = check_args(arguments, dataframe)
    return checked_args

def get_vars(arg_names, args_list):
    stripped_args = [arg[0] for arg in args_list]
    vals = []
    for arg in arg_names:
        ind = stripped_args.index(arg)
        values = args_list[ind][1:]
        islower = arg.islower()
        vals.append(values or islower)
    clean_vals = []
    for val in vals:  # transform vals into a list of strings, int/floats, and booleans (instead of lists and booleans)
        # deal with booleans
        if isinstance(val, bool) or isinstance(val, int) or isinstance(val, float):
            clean_vals.append(val)
        else:
            # deal with numbers
            if len(val) == 1 and (isinstance(val[0], int) or isinstance(val[0], float)):
                clean_vals.append(val[0])
            # deal with lists
            elif not isinstance(val, bool):
                try:
                    clean_vals.append(' '.join(val))
                except TypeError:
                    clean_vals.append([])
            # deal with strings
            else:
                clean_vals.append(val)
    return clean_vals

##example use:
##make a pandas dataframe with three columns:
## col 1 is the command-line flag (minus the '-'), common ones include f, F, fsa, Fsa, etc.
## col 2 is a boolean for if the flag is required or not
## col 3 is a default value to use if the flag is not provided
#dataframe = command_line_dataframe([['sav', False, 0], ['fmt', False, 'svg'], ['s', False, 20]])
## get the args from the command line:
#args = sys.argv
## check through the args to make sure that reqd args are present, defaults are used as needed, and invalid args are ignored
#checked_args = extract_and_check_args(args, dataframe)
## assign values to variables based on their associated command-line flag
#fmt, size, plot = get_vars(['fmt', 's', 'sav'], checked_args)
#print "fmt:", fmt, "size:", size, "plot:", plot
