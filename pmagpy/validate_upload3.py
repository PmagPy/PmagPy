#!/usr/bin/env python



# replace this with something more sensible and less redundant ...
import pmagpy.controlled_vocabularies3 as cv
reload(cv)
vocab = cv.Vocabulary()
vocabulary, possible_vocabulary = vocab.get_controlled_vocabularies()

## LOW-LEVEL VALIDATION FUNCTIONS

def requiredUnless(col_name, arg, dm, df, *args):
    """
    Arg is a string in the format "str1, str2, ..."
    Each string will be a column name.
    Col_name is required in df unless each column from arg is present.
    """
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
    x = 0
    cell_value = row[col_name]
    if not cell_value:
        return None
    elif not con:
        return None
    # if it's in another table
    cell_values = [v.strip(" ") for v in cell_value.split(":")]
    if "." in arg:
        table_name, table_col_name = arg.split(".")
        if table_name not in con.tables:
            return "Must contain a value from {} table. Missing {} table.".format(table_name, table_name)
        if table_col_name not in con.tables[table_name].df.columns:
            return '{} table is missing "{}" column, which is required for validating "{}" column'.format(table_name, table_col_name, col_name)
        possible_values = con.tables[table_name].df[table_col_name].unique()
        for value in cell_values:
            if value not in possible_values:
                return 'This value: "{}" is not found in: {}'.format(value, arg)
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
    try:
        arg_val = float(arg)
    except ValueError:
        arg_val = row[arg]
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
    try:
        arg_val = float(arg)
    except ValueError:
        arg_val = row[arg]
    try:
        if float(cell_value) >= float(arg_val):
            return None
        else:
            return "{} ({}) must be >= {} ({})".format(str(cell_value), col_name, arg_val, str(arg))
    # this happens when the value isn't a float (an error which will be caught elsewhere)
    except ValueError:
        return None

def cv(row, col_name, arg, current_data_model, *args):
    """
    row[col_name] must contain only values from the appropriate controlled vocabulary
    """
    cell_value = row[col_name]
    if not cell_value:
        return None
    cell_values = cell_value.split(":")
    cell_values = [c.strip() for c in cell_values]
    for value in cell_values:
        if value.lower() in [v.lower() for v in vocabulary[col_name]]:
            continue
        else:
            return '"{}" is not in controlled vocabulary for {}'.format(value, arg)
    return None


# validate presence
presence_operations = {"required": required, "requiredUnless": requiredUnless,
                       "requiredIfGroup": requiredIfGroup,
                       'requiredUnlessTable': requiredUnlessTable}
# validate values
value_operations = {"max": checkMax, "min": checkMin, "cv": cv, "in": isIn}


def test_type(value, value_type):
    if not value:
        return None
    if value_type == "String":
        if str(value) == value:
            return None
        else:
            return "should be string"
    elif value_type == "Number":
        try:
            float(value)
            return None
        except ValueError:
            return '"{}" should be a number'.format(str(value))
    elif value_type == "Integer":
        if isinstance(value, str):
            if str(int(value)) == value:
                return None
            else:
                return '"{}" should be an integer'.format(str(value))
        else:
            if int(value) == value:
                return None
            else:
                return '"{}" should be an integer'.format(str(value))
    else:
        return None
    #String, Number, Integer, List, Matrix, Dictionary, Text


## Table-level validation functions


def validate_df(df, dm, con=None):
    # check column validity
    cols = df.columns
    invalid_cols = [col for col in cols if col not in dm.index]
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
                        num_range = range(1, 10)
                        for num in num_range:
                            if (col_name + str(num)) in df.columns:
                                continue
                            else:
                                col_name = col_name + str(num)
                                break
                    df[col_name] = grade.astype(object)
    return df



## Utilities


def split_func(string):
    """
    Take a string like 'requiredIf("arg_name")'
    return the function name and the argument:
    (requiredIf, arg_name)
    """
    ind = string.index("(")
    return string[:ind], string[ind+1:-1].strip('"')
