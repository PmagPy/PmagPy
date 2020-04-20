#!/usr/bin/env python

from __future__ import print_function

from builtins import zip
from builtins import str
from builtins import range

import math
import os
import re
import numpy as np
from pmagpy import contribution_builder as cb


## LOW-LEVEL VALIDATION FUNCTIONS

def requiredUnless(col_name, arg, dm, df, *args):
    """
    Arg is a string in the format "str1, str2, ..."
    Each string will be a column name.
    Col_name is required in df unless each column from arg is present.
    """
    # if column name is present, no need to check if it is required
    if col_name in df.columns:
        return None
    arg_list = arg.split(",")
    arg_list = [argument.strip('"') for argument in arg_list]
    msg = ""
    for a in arg_list:
        # ignore validations that reference a different table
        if "." in a:
            continue
        if a not in df.columns:
            msg += "{} column is required unless {} is present.  ".format(col_name, a)
    if msg:
        return msg
    else:
        return None
    return None


def requiredUnlessTable(col_name, arg, dm, df, con=None):
    """
    Col_name must be present in df unless
    arg (table_name) is present in contribution
    """
    table_name = arg
    if col_name in df.columns:
        return None
    elif not con:
        return None
    elif table_name in con.tables:
        return None
    else:
        return "{} column is required unless table {} is present".format(col_name, table_name)


def requiredIfGroup(col_name, arg, dm, df, *args):
    """
    Col_name is required if other columns of
    the group arg are present.
    """
    group_name = arg
    groups = set()
    columns = df.columns
    for col in columns:
        if col not in dm.index:
            continue
        group = dm.loc[col]['group']
        groups.add(group)
    if group_name in groups:
        if col_name in columns:
            return None
        else:
            return "{} column is required if column group {} is used".format(col_name, group_name)
    return None


def required(col_name, arg, dm, df, *args):
    """
    Col_name is required in df.columns.
    Return error message if not.
    """
    if col_name in df.columns:
        return None
    else:
        return '"{}" column is required'.format(col_name)

def isIn(row, col_name, arg, dm, df, con=None):
    """
    row[col_name] must contain a value from another column.
    If not, return error message.
    """
    #grade = df.apply(func, args=(validation_name, arg, dm), axis=1)
    cell_value = row[col_name]
    cell_value = str(cell_value)
    if not cell_value:
        return None
    elif cell_value == 'None':
        return None
    elif cell_value == 'nan':
        return None
    elif not con:
        return None
    # if it's in another table
    cell_values = [v.strip(" ") for v in cell_value.split(":")]
    if "." in arg:
        table_name, table_col_name = arg.split(".")
        if table_name not in con.tables:
            return None
            #return "Must contain a value from {} table. Missing {} table.".format(table_name, table_name)
        if table_col_name not in con.tables[table_name].df.columns:
            return '{} table is missing "{}" column, which is required for validating "{}" column'.format(table_name, table_col_name, col_name)
        possible_values = con.tables[table_name].df[table_col_name].unique()
        for value in cell_values:
            if value not in possible_values:
                trunc_possible_values = [val.replace(' ', '') for val in possible_values if val]
                trunc_cell_value = cell_value.replace(' ', '')
                if trunc_cell_value not in trunc_possible_values:
                    if trunc_cell_value != value:
                        return 'This value (long): "{}" is not found in: {} column in {} table.  Also (short): {} is not in {}'.format(value, table_col_name, table_name, trunc_cell_value, arg)
                    else:
                        return 'This value: "{}" is not found in: {} column in {} table'.format(value, table_col_name, table_name)
                    break
    # if it's in the present table:
    else:
        possible_values = df[arg].unique()
        for value in cell_values:
            if value not in possible_values:
                return 'This value: "{}" is not found in: {} column'.format(value, arg)
                break
    return None

def checkMax(row, col_name, arg, *args):
    """
    row[col_name] must be less than or equal to arg.
    else, return error message.
    """
    cell_value = row[col_name]
    if not cell_value:
        return None
    elif isinstance(cell_value, float):
        if np.isnan(cell_value):
            return None
    try:
        arg_val = float(arg)
    except ValueError:
        if arg in row.index:
            arg_val = row[arg]
        else:
            return None
    if cb.is_null(arg_val):
        return None
    #arg = float(arg)
    try:
        if float(cell_value) <= float(arg_val):
            return None
        else:
            return "{} ({}) must be <= {} ({})".format(str(cell_value), col_name, str(arg_val), str(arg))
    # this happens when the value isn't a float (an error which will be caught elsewhere)
    except ValueError:
        return None

def checkMin(row, col_name, arg, *args):
    """
    row[col_name] must be greater than or equal to arg.
    else, return error message.
    """
    cell_value = row[col_name]
    if not cell_value:
        return None
    elif isinstance(cell_value, float):
        if np.isnan(cell_value):
            return None
    try:
        arg_val = float(arg)
    except ValueError:
        if arg in row.index:
            arg_val = row[arg]
        else:
            return None
    if cb.is_null(arg_val):
        return None
    try:
        if float(cell_value) >= float(arg_val):
            return None
        else:
            return "{} ({}) must be >= {} ({})".format(str(cell_value), col_name, arg_val, str(arg))
    # this happens when the value isn't a float (an error which will be caught elsewhere)
    except ValueError:
        return None

def cv(row, col_name, arg, current_data_model, df, con):
    """
    row[col_name] must contain only values from the appropriate controlled vocabulary
    """
    vocabulary = con.vocab.vocabularies
    cell_value = str(row[col_name])
    col_type = current_data_model.loc[col_name].type
    if not cell_value:
        return None
    elif cell_value == "None":
        return None
    cell_values = [cell_value]
    # split Matrix value rows by semicolons unless they are within quotes
    if col_type == 'Matrix':
        cell_values = re.split(';(?=(?:[^"]*"[^"]*")*[^"]*$)', cell_value)
    # split List and Dictionary values by colons unless they are within quotes
    if col_type == 'List' or col_type == 'Dictionary':
        cell_values = re.split(':(?=(?:[^"]*"[^"]*")*[^"]*$)', cell_value)
    cell_values = [c.strip() for c in cell_values]
    # get possible values for controlled vocabulary
    # exclude weird unicode
    possible_values = []
    for val in vocabulary[col_name]:
        try:
            possible_values.append(str(val).lower())
        except UnicodeEncodeError as ex:
            print(val, ex)
    for value in cell_values:
        # only validate the first column in a Matrix row agaist the vocabulary
        if col_type == 'Matrix':
            value = value.split(':')[0]
        if str(value).lower() == "nan":
            continue
        elif str(value).lower() in possible_values:
            continue
        elif value.lower() == "none":
            continue
        else:
            try:
                if str(float(value)) in possible_values:
                    continue
            except:
                pass
            return '"{}" is not in controlled vocabulary for {}'.format(value, arg)
    return None


def requiredOneInGroup(col_name, group, dm, df, *args):
    """
    If col_name is present in df, the group validation is satisfied.
    If not, it still may be satisfied, but not by THIS col_name.
    If col_name is missing, return col_name, else return None.
    Later, we will validate to see if there is at least one None (non-missing)
    value for this group.
    """
    if col_name in df.columns:
        # if the column name is present, return nothing
        return None
    else:
        # if the column name is missing, return column name
        return col_name


# validate presence
presence_operations = {"required": required, "requiredUnless": requiredUnless,
                       "requiredIfGroup": requiredIfGroup,
                       'requiredUnlessTable': requiredUnlessTable}
# validate values
value_operations = {"max": checkMax, "min": checkMin, "cv": cv, "in": isIn}

# validate group

group_operations = {"requiredOneInGroup": requiredOneInGroup}

# validate_type

def test_type(value, value_type):
    if not value:
        return None
    if value_type == "String":
        return None
    elif value_type == "Number":
        try:
            float(value)
            return None
        except ValueError:
            return '"{}" should be a number'.format(str(value))
    elif value_type == "Integer":
        if isinstance(value, int):
            return None
        try:
            flt = float(value)
        except ValueError:
            return '"{}" should be an integer'.format(str(value))
        if math.trunc(flt) == flt:
            return None
        return '"{}" should be an integer'.format(str(value))

        #try:
        #    int(value)
        #except ValueError:
        #    return '"{}" should be an integer'.format(str(value))
        #if isinstance(value, str):
        #    try:
        #        str(int(float(value))
        #    if str(int(value)) == value:
        #        return None
        #    else:
        #        return '"{}" should be an integer'.format(str(value))
    else:
        return None
    #String, Number, Integer, List, Matrix, Dictionary, Text


## Table-level validation functions


def validate_df(df, dm, con=None):
    """
    Take in a DataFrame and corresponding data model.
    Run all validations for that DataFrame.
    Output is the original DataFrame with some new columns
    that contain the validation output.
    Validation columns start with:
    presence_pass_ (checking that req'd columns are present)
    type_pass_  (checking that the data is of the correct type)
    value_pass_ (checking that the value is within the appropriate range)
    group_pass_ (making sure that group validations pass)
    """
    # check column validity
    required_one = {}  # keep track of req'd one in group validations here
    cols = df.columns
    invalid_cols = [col for col in cols if col not in dm.index]
    # go through and run all validations for the data type
    for validation_name, validation in dm.iterrows():
        value_type = validation['type']
        if validation_name in df.columns:
            output = df[validation_name].apply(test_type, args=(value_type,))
            df["type_pass" + "_" + validation_name + "_" + value_type] = output
        #
        val_list = validation['validations']
        if not val_list or isinstance(val_list, float):
            continue
        for num, val in enumerate(val_list):
            func_name, arg = split_func(val)
            if arg == "magic_table_column":
                continue
            # first validate for presence
            if func_name in presence_operations:
                func = presence_operations[func_name]
                #grade = func(validation_name, df, arg, dm)
                grade = func(validation_name, arg, dm, df, con)
                pass_col_name = "presence_pass_" + validation_name + "_" + func.__name__
                df[pass_col_name] = grade
            # then validate for correct values
            elif func_name in value_operations:
                func = value_operations[func_name]
                if validation_name in df.columns:
                    grade = df.apply(func, args=(validation_name, arg, dm, df, con), axis=1)
                    col_name = "value_pass_" + validation_name + "_" + func.__name__
                    if col_name in df.columns:
                        num_range = list(range(1, 10))
                        for num in num_range:
                            if (col_name + str(num)) in df.columns:
                                continue
                            else:
                                col_name = col_name + str(num)
                                break
                    df[col_name] = grade.astype(object)
            # last, validate at the column group level
            elif func_name in group_operations:
                func = group_operations[func_name]
                missing = func(validation_name, arg, dm, df)
                if arg not in required_one:
                    required_one[arg] = [missing]
                else:
                    required_one[arg].append(missing)
    # format the group validation columns
    for key, value in list(required_one.items()):
        if None in value:
            col_name = "group_pass_{}".format(key)
            if col_name in df.columns:
                del df[col_name]
            # this means at least one value from the required group is present,
            # so the validation passes
            continue
        else:
            # otherwise, all of the values from the required group are missing,
            # so the validation fails
            df["group_pass_{}".format(key)] = "you must have one column from group {}: {}".format(key, ", ".join(value))

    return df


## Extracting data from a validated dataframe

def get_validation_col_names(df):
    """
    Input: validated pandas DataFrame (using validate_df)
    Output: names of all value validation columns,
            names of all presence validation columns,
            names of all type validation columns,
            names of all missing group columns,
            names of all validation columns (excluding groups).
    """
    value_cols = df.columns.str.match("^value_pass_")
    present_cols = df.columns.str.match("^presence_pass")
    type_cols = df.columns.str.match("^type_pass_")
    groups_missing = df.columns.str.match("^group_pass_")
    #
    value_col_names = df.columns[value_cols]
    present_col_names = df.columns[present_cols]
    type_col_names = df.columns[type_cols]
    group_missing_names = df.columns[groups_missing]
    #
    # all validation columns
    validation_cols = np.where(value_cols, value_cols, present_cols)
    validation_cols = np.where(validation_cols, validation_cols, type_cols)
    validation_col_names = df.columns[validation_cols]
    return value_col_names, present_col_names, type_col_names, group_missing_names, validation_col_names


def print_row_failures(failing_items, verbose=False, outfile_name=None):
    """
    Take output from get_row_failures (DataFrame), and output it to
    stdout, an outfile, or both.
    """
    if outfile_name:
        outfile = open(outfile_name, "w")
        outfile.write("\t".join(["name", "row_number", "problem_type",
                                 "problem_col", "error_message"]))
        outfile.write("\n")
    else:
        outfile = None
    for ind, row in failing_items.iterrows():
        issues = row['issues']
        string = "{:10}  |  row number: {}".format(ind, str(row["num"]))
        first_string = "\t".join([str(ind), str(row["num"])])
        if verbose:
            print(first_string)
        #if outfile:
        #    ofile.write("{}\n".format(string))
        for key, issue in list(issues.items()):
            issue_type, issue_col = extract_col_name(key)
            string = "{:10}  |  {:10}  |  {}".format(issue_type, issue_col, issue)
            string = "\t".join([issue_type, issue_col, issue])
            if verbose:
                print(string)
            if outfile:
                outfile.write(first_string + "\t" + string + "\n")
    if outfile:
        outfile.close()


def get_row_failures(df, value_cols, type_cols, verbose=False, outfile=None):
    """
    Input: already validated DataFrame, value & type column names,
    and output options.
    Get details on each detected issue, row by row.
    Output: DataFrame with type & value validation columns,
    plus an "issues" column with a dictionary of every problem
    for that row.
    """
    # set temporary numeric index
    df["num"] = list(range(len(df)))
    # get column names for value & type validations
    names = value_cols.union(type_cols)
    # drop all non validation columns
    value_problems = df[names.union(["num"])]
    # drop validation columns that contain no problems
    failing_items = value_problems.dropna(how="all", subset=names)
    if not len(failing_items):
        if verbose:
            print("No problems")
        return []
    failing_items = failing_items.dropna(how="all", axis=1)
    # get names of the failing items
    bad_items = list(failing_items.index)
    # get index numbers of the failing items
    bad_indices = list(failing_items["num"])
    failing_items['issues'] = failing_items.drop("num", axis=1).apply(make_row_dict, axis=1).values
    # take output and print/write to file
    print_row_failures(failing_items, verbose, outfile)
    return failing_items


def get_bad_rows_and_cols(df, validation_names, type_col_names,
                          value_col_names, verbose=False):
    """
    Input: validated DataFrame, all validation names, names of the type columns,
    names of the value columns, verbose (True or False).
    Output: list of rows with bad values, list of columns with bad values,
    list of missing (but required) columns.
    """
    df["num"] = list(range(len(df)))
    problems = df[validation_names.union(["num"])]
    all_problems = problems.dropna(how='all', axis=0, subset=validation_names)
    value_problems = problems.dropna(how='all', axis=0, subset=type_col_names.union(value_col_names))
    all_problems = all_problems.dropna(how='all', axis=1)
    value_problems = value_problems.dropna(how='all', axis=1)
    if not len(problems):
        return None, None, None
    #
    bad_cols = all_problems.columns
    prefixes = ["value_pass_", "type_pass_"]
    missing_prefix = "presence_pass_"
    problem_cols = []
    missing_cols = []
    long_missing_cols = []
    problem_rows = []
    for col in bad_cols:
        pre, stripped_col = extract_col_name(col)
        for prefix in prefixes:
            if col.startswith(prefix):
                problem_cols.append(stripped_col)
                continue
        if col.startswith(missing_prefix):
            missing_cols.append(stripped_col)
            long_missing_cols.append(col)
    if len(value_problems):
        bad_rows = list(zip(list(value_problems["num"]), list(value_problems.index)))
    else:
        bad_rows = []
    if verbose:
        if bad_rows:
            formatted_rows = ["row: {}, name: {}".format(row[0], row[1]) for row in bad_rows]
            if len(bad_rows) > 5:
                print("-W- these rows have problems:\n", "\n".join(formatted_rows[:5]), " ...")
                print("(for full error output see error file)")
            else:
                print("-W- these rows have problems:", "\n".join(formatted_rows))
        if problem_cols:
            print("-W- these columns contain bad values:", ", ".join(set(problem_cols)))
        if missing_cols:
            print("-W- these required columns are missing:", ", ".join(missing_cols))
    return bad_rows, problem_cols, missing_cols


# Run through all validations for a single table

def validate_table(the_con, dtype, verbose=False, output_dir="."):
    """
    Return name of bad table, or False if no errors found.
    Calls validate_df then parses its output.
    """
    print("-I- Validating {}".format(dtype))
    # grab dataframe
    current_df = the_con.tables[dtype].df
    # grab data model
    current_dm = the_con.tables[dtype].data_model.dm[dtype]
    # run all validations (will add columns to current_df)
    current_df = validate_df(current_df, current_dm, the_con)
    # get names of the added columns
    value_col_names, present_col_names, type_col_names, missing_groups, validation_col_names = get_validation_col_names(current_df)
    # print out failure messages
    ofile = os.path.join(output_dir, "{}_errors.txt".format(dtype))
    failing_items = get_row_failures(current_df, value_col_names,
                                     type_col_names, verbose, outfile=ofile)
    bad_rows, bad_cols, missing_cols = get_bad_rows_and_cols(current_df, validation_col_names,
                                                             value_col_names, type_col_names,
                                                             verbose=True)
    # delete all validation rows
    current_df.drop(validation_col_names, axis=1, inplace=True)
    current_df.drop(missing_groups, axis=1, inplace=True)
    if len(failing_items):
        print("-I- Complete list of row errors can be found in {}".format(ofile))
        return dtype, bad_rows, bad_cols, missing_cols, missing_groups, failing_items
    elif len(missing_cols) or len(missing_groups):
        print("-I- You are missing some required headers")
        if len(missing_cols):
            print("-I- You are missing these required headers: {}".format(", ".join(missing_cols)))
        if len(missing_groups):
            formatted_groups = [group[11:] for group in missing_groups]
            print('-I- You need at least one header from these groups: {}'.format(", ".join(formatted_groups)))
        else:
            formatted_groups = []
        return dtype, bad_rows, bad_cols, missing_cols, formatted_groups, failing_items
    else:
        print("-I- No row errors found!")
        return False


## Run validations on an entire contribution

def validate_contribution(the_con):
    """
    Go through a Contribution and validate each table
    """
    passing = True
    for dtype in list(the_con.tables.keys()):
        print("validating {}".format(dtype))
        fail = validate_table(the_con, dtype)
        if fail:
            passing = False
        print('--')


## Utilities


def split_func(string):
    """
    Take a string like 'requiredIf("arg_name")'
    return the function name and the argument:
    (requiredIf, arg_name)
    """
    ind = string.index("(")
    return string[:ind], string[ind+1:-1].strip('"')


def get_degree_cols(df):
    """
    Take in a pandas DataFrame, and return a list of columns
    that are in that DataFrame AND should be between 0 - 360 degrees.
    """
    vals = ['lon_w', 'lon_e', 'lat_lon_precision', 'pole_lon',
            'paleolon', 'paleolon_sigma',
            'lon', 'lon_sigma', 'vgp_lon', 'paleo_lon', 'paleo_lon_sigma',
            'azimuth', 'azimuth_dec_correction', 'dir_dec',
            'geographic_precision', 'bed_dip_direction']
    relevant_cols = list(set(vals).intersection(df.columns))
    return relevant_cols


def extract_col_name(string):
    """
    Take a string and split it.
    String will be a format like "presence_pass_azimuth",
    where "azimuth" is the MagIC column name and "presence_pass"
    is the validation.
    Return "presence", "azimuth".
    """
    prefixes = ["presence_pass_", "value_pass_", "type_pass_"]
    end = string.rfind("_")
    for prefix in prefixes:
        if string.startswith(prefix):
            return prefix[:-6], string[len(prefix):end]
    return string, string


def make_row_dict(row):
    """
    Takes in a DataFrame row (Series),
    and return a dictionary with the row's index as key,
    and the row's values as values.
    {col1_name: col1_value, col2_name: col2_value}
    """
    ind = row[row.notnull()].index
    values = row[row.notnull()].values
    # to transformation with extract_col_name here???
    return dict(list(zip(ind, values)))
