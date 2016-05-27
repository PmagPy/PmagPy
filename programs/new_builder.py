#!/usr/bin/env python

"""
This module is for creating or editing a MagIC contribution,
(or a piece of one).
You can build a contribution or an individual table from the ground up,
or you can read in one or more MagIC-format files.
You can also extract specific data from a table --
for instance, you can build a DIblock for plotting.
"""

import os
import re
import pandas as pd
from pandas import DataFrame
from pmagpy import pmag


class Contribution(object):

    """
    A Contribution is a collection of MagicDataFrames,
    each of which corresponds to one MagIC table.
    The Contribution object also has methods for
    manipulating one or more tables in the contribution --
    for example, renaming a site.
    """

    def __init__(self, directory, read_tables='all',
                 custom_filenames=None, single_file=None):

        self.directory = os.path.realpath(directory)
        self.table_names = ['measurements', 'specimens', 'samples',
                            'sites', 'locations', 'contribution',
                            'criteria', 'ages', 'images']
        self.ancestry = ['measurements', 'specimens', 'samples',
                         'sites', 'locations']

        # create standard filenames from table names
        self.filenames = {t: t + ".txt" for t in self.table_names}
        # update self.filenames to include custom names
        if custom_filenames:
            self.add_custom_filenames(custom_filenames)

        self.tables = {}
        # if not otherwise specified, read in all possible tables
        if read_tables == 'all':
            read_tables = self.table_names
        if single_file:  # use if filename is known but type isn't
            self.add_magic_table('unknown', single_file)
            return
        else:  # read in data for all required tables
            for name in read_tables:
                self.add_magic_table(name)

    def add_custom_filenames(self, custom_filenames):
        """
        Update/overwrite self.filenames with custom names.
        Input dict should have the format:
        {"specimens": "custom_spec_file.txt", ...}
        """
        if custom_filenames:
            self.filenames.update(custom_filenames)

    def add_magic_table(self, dtype, fname=None):
        """
        Add a table to self.tables.
        """
        # if providing a filename but no data type
        if dtype == "unknown":
            filename = os.path.join(self.directory, fname)
            data_container = MagicDataFrame(filename)
            dtype = data_container.dtype
            if dtype == 'empty':
                return False
            else:
                self.tables[dtype] = data_container
                return data_container
        # if providing a data type, use the canonical filename
        elif dtype not in self.filenames:
            print '-W- "{}" is not a valid MagIC table type'.format(dtype)
            print "-I- Available table types are: {}".format(", ".join(self.table_names))
            return False
        filename = os.path.join(self.directory, self.filenames[dtype])
        if os.path.exists(filename):
            data_container = MagicDataFrame(filename)
            self.tables[dtype] = data_container
            return data_container
        else:
            print "-W- No such file: {}".format(filename)
            return False

    def rename_item(self, table_name, item_old_name, item_new_name):
        """
        Rename itme (such as a site) everywhere that it occurs.
        This change often spans multiple tables.
        For example, a site name will occur in the sites table,
        the samples table, and possibly in the locations/ages tables.
        """
        # define some helper methods:
        def split_if_str(item):
            """
            String splitting function
            that doesn't break with None/np.nan
            """
            if isinstance(item, str):
                return item.split(':')
            else:
                return item

        def put_together_if_str(item):
            """
            String joining function
            that doesn't break with None/np.nan
            """
            try:
                return ":".join(item)
            except TypeError:
                return item

        def replace_colon_delimited_value(df, col_name, old_value, new_value):
            """
            Col must contain list
            """
            for index, row in df[df[col_name].notnull()].iterrows():
                names_list = row[col_name]
                try:
                    ind = names_list.index(old_value)
                except ValueError:
                    continue
                names_list[ind] = new_value

        # initialize some things
        item_type = table_name
        col_name = item_type[:-1] + "_name"
        col_name_plural = col_name + "s"
        table_df = self.tables[item_type].df
        # rename item in its own table
        table_df.rename(index={item_old_name: item_new_name}, inplace=True)
        # rename in any parent/child tables
        for table_name in self.tables:
            df = self.tables[table_name].df
            col_names = df.columns
            # change anywhere col_name (singular, i.e. site_name) is found
            if col_name in col_names:
                df[col_name].where(df[col_name] != item_old_name, item_new_name, inplace=True)
                # change anywhere col_name (plural, i.e. site_names) is found
            if col_name_plural in col_names:
                df[col_name_plural + "_list"] = df[col_name_plural].apply(split_if_str)
                replace_colon_delimited_value(df, col_name_plural + "_list", item_old_name, item_new_name)
                df[col_name_plural] = df[col_name_plural + "_list"].apply(put_together_if_str)

    def get_table_name(self, ind):
        """
        Return both the table_name (i.e., 'specimens')
        and the col_name (i.e., 'specimen_name')
        for a given index in self.ancestry.
        """
        if ind > -1:
            table_name = self.ancestry[ind]
            name = table_name[:-1] + "_name"
            return table_name, name
        return "", ""

    def propagate_col_name_down(self, col_name, df_name):
        """
        Put the data for "col_name" into dataframe with df_name
        Used to add 'site_name' to specimen table, for example.
        """
        if df_name not in self.tables:
            self.add_magic_table(df_name)
        df = self.tables[df_name].df
        if col_name in df.columns:
            print '{} already in {}'.format(col_name, df_name)
            return df

        # otherwise, do necessary merges to get col_name into df
        # get names for each level
        grandparent_table_name = col_name.split('_')[0] + "s"
        grandparent_name = grandparent_table_name[:-1] + "_name"
        ind = self.ancestry.index(grandparent_table_name) - 1
        #
        parent_table_name, parent_name = self.get_table_name(ind)
        child_table_name, child_name = self.get_table_name(ind - 1)
        bottom_table_name, bottom_name = self.get_table_name(ind - 2)

        # merge in bottom level
        if child_name not in df.columns:
            # add child table if missing
            if bottom_table_name not in self.tables:
                result = self.add_magic_table(bottom_table_name)
                if not isinstance(result, MagicDataFrame):
                    print "-W- Couldn't read in {} data".format(bottom_table_name)
                    print "-I- Make sure you've provided the correct file name"
                    return df
            # add child_name to df
            add_df = self.tables[bottom_table_name].df
            # drop duplicate names
            add_df = add_df.drop_duplicates(subset=bottom_name)
            df = df.merge(add_df[[child_name]],
                          left_on=[bottom_name],
                          right_index=True, how="left")

        # merge in one level above
        if parent_name not in df.columns:
            # add parent_table if missing
            if child_table_name not in self.tables:
                result = self.add_magic_table(child_table_name)
                if not isinstance(result, MagicDataFrame):
                    print "-W- Couldn't read in {} data".format(child_table_name)
                    print "-I- Make sure you've provided the correct file name"
                    return df
            # add parent_name to df
            add_df = self.tables[child_table_name].df
            # drop duplicate names
            add_df = add_df.drop_duplicates(subset=child_name)
            df = df.merge(add_df[[parent_name]],
                          left_on=[child_name],
                          right_index=True, how="left")

        # merge in two levels above
        if grandparent_name not in df.columns:
            # add grandparent table if it is missing
            if parent_table_name not in self.tables:
                result = self.add_magic_table(parent_table_name)
                if not isinstance(result, MagicDataFrame):
                    print "-W- Couldn't read in {} data".format(parent_table_name)
                    print "-I- Make sure you've provided the correct file name"
                    return df
            # add grandparent name to df
            add_df = self.tables[parent_table_name].df
            # drop duplicate names
            add_df = add_df.drop_duplicates(subset=parent_name)
            df = df.merge(add_df[[grandparent_name]],
                          left_on=[parent_name],
                          right_index=True, how="left")
        # update the Contribution
        self.tables[df_name].df = df
        return df


class MagicDataFrame(object):

    """
    Each MagicDataFrame corresponds to one MagIC table.
    The MagicDataFrame object consists of a pandas DataFrame,
    and assorted methods for manipulating that DataFrame.
    """

    def __init__(self, magic_file):
        data, dtype = pmag.magic_read(magic_file)
        self.df = DataFrame(data)
        if dtype == 'bad_file':
            print "-W- Bad file {}".format(magic_file)
            self.dtype = 'empty'
            return
        #
        self.dtype = dtype
        if dtype == 'measurements':
            self.df['measurement_name'] = self.df['experiment_name'] + self.df['measurement_number']
            name = 'measurement_name'
        elif dtype.endswith('s'):
            dtype = dtype[:-1]
            name = '{}_name'.format(dtype)
        elif dtype == 'contribution':
            name = 'doi'
        # fix these:
        if dtype == 'age':
            self.df = pd.DataFrame()
            return
        if dtype == 'image':
            self.df = pd.DataFrame()
            return
        if dtype == 'criteria':
            #self.df = pd.DataFrame()
            self.df.index = self.df['table_column_name']
            return
        self.df.index = self.df[name]
        #del self.df[name]
        #self.dtype = dtype
        # replace '' with None, so you can use isnull(), notnull(), etc.
        # can always switch back with DataFrame.fillna('')
        self.df[self.df == ''] = None
        # drop any completely blank columns
        self.df.dropna(axis=1, how='all', inplace=True)

    def add_blank_row(self, label):
        """
        Add a blank row with only an index value to self.df
        """
        col_labels = self.df.columns
        blank_item = pd.Series({}, index=col_labels, name=label)
        # use .loc to add in place (append won't do that)
        self.df.loc[blank_item.name] = blank_item

    def get_name(self, col_name, df_slice="", index_names=""):
        """
        Takes in a column name, and either a DataFrame slice or
        a list of index_names to slice self.df using fancy indexing.
        Then return the value for that column in the relevant slice.
        """
        # if slice is provided, use it
        if any(df_slice):
            df_slice = df_slice
        # if given index_names, grab a slice using fancy indexing
        elif index_names:
            df_slice = self.df.ix[index_names]
        # otherwise, use the full DataFrame
        else:
            df_slice = self.df
        # if the slice is empty, return ""
        if len(df_slice) == 0:
            return ""
        # if the column name isn't present in the slice, return ""
        if col_name not in df_slice.columns:
            return ""
        # otherwise, return the first value from that column
        return df_slice[col_name][0]

    def get_di_block(self, df_slice=None, do_index=False,
                     item_names=None, tilt_corr='100'):
        """
        Input either a DataFrame slice
        or
        do_index=True and a list of index_names.
        Output dec/inc from the slice in this format:
        [[dec1, inc1], [dec2, inc2], ...]
        """
        if isinstance(df_slice, str):
            if df_slice.lower() == "all":
                # use entire DataFrame
                df_slice = self.df
        elif do_index:
            # use fancy indexing (but note this will give duplicates)
            df_slice = self.df.ix[item_names]
        elif not do_index:
            # otherwise use the provided slice
            df_slice = df_slice

        # once you have the slice, fix up the data
        if tilt_corr != "0":
            df_slice = df_slice[df_slice['dir_tilt_correction'] == tilt_corr]
        else:
            cond1 = df_slice['dir_tilt_correction'].fillna('') == tilt_corr
            cond2 = df_slice['dir_tilt_correction'].isnull()
            df_slice = df_slice
        df_slice = df_slice[df_slice['dir_inc'].notnull() & df_slice['dir_dec'].notnull()]
        # possible add in:
        # split out di_block from this study from di_block from other studies (in citations column)
        # for now, just use "This study"
        if 'citations' in df_slice.columns:
            df_slice = df_slice[df_slice['citations'] == "This study"]

        # convert values into DIblock format
        di_block = [[float(row['dir_dec']), float(row['dir_inc'])] for ind, row in df_slice.iterrows()]
        return di_block

    def get_records_for_code(self, meth_code, incl=True, use_slice=False, sli=None):
        """
        Use regex to see if meth_code is in the method_codes ":" delimited list.
        If incl == True, return all records WITH meth_code.
        If incl == False, return all records WITHOUT meth_code.
        """

        # (must use fillna to replace np.nan with False for indexing)
        if use_slice:
            df = sli.copy()
        else:
            df = self.df.copy()
        # if meth_code not provided, return unchanged dataframe
        if not meth_code:
            return df
        # get regex
        pattern = re.compile('{}(?=:|\s|\Z)'.format(meth_code))
        cond = df['method_codes'].str.contains(pattern).fillna('')
        if incl:
            # return a copy of records with that method code:
            return df[cond]
        else:
            # return a copy of records without that method code
            return df[~cond]


if __name__ == "__main__":
    pass
