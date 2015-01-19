#!/usr/bin/env python

import pandas as pd
import pmag

class command_line_dataframe():
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
        self.default_dict = {'arg_name': ['f', 'F', 'A', 'WD'], 'reqd': [True, False, False, False], 'default': ['', '', '', '.']}
        self.df = pd.DataFrame(self.default_dict, index=['f', 'F', 'A', 'WD'])
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
        self.df = pd.concat([self.df, d])
            
def extract_args(argv):
    """
    take sys.argv that is used to call a command-line script and return a correctly split list of arguments
    for example: ["eqarea.py", "-f", "infile", "-F", "outfile", "-A"] will return: [['f', 'infile'], ['F', 'outfile'], ['A']]
    """
    string = " ".join(argv)
    string = string.split('-')
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
    # first make sure all args are valid
    for a in arguments:
        if a[0] not in data_frame.index:
            print "-I- ignoring invalid argument: {}".format(a[0])
            print "-"
    # next make sure required arguments are present
    condition = df['reqd']
    reqd_args = df[condition]
    for arg in reqd_args['arg_name']:
        if arg not in stripped_args:
            raise pmag.MissingCommandLineArgException("-"+arg)
    #next, assign any default values as needed
    condition = df['default'] != ''
    default_args = df[condition]
    for value in default_args.values:
        arg_name, default = value[0], value[1]
        if arg_name not in stripped_args:
            print "-I- using default for arg:", arg_name
            print "-"
            arguments.append([arg_name, default])
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
    return vals
    

# example usage:                                                                                                 
#df = command_line_dataframe([['f', False, 'hello.txt'], ['F', True, ''], ['r', False, 'thingee']]).df
#print df
#checked_args = extract_and_check_args(["eqarea.py", "-A", "-t", "18", "20", "-F", "output.txt"], df)
#infile, outfile, append, temp = get_vars(['f', 'F', 'A', 't'], checked_args)
#print infile, outfile, append, temp
