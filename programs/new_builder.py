#!/usr/bin/env python

import os
import numpy as np
import pandas as pd
from pandas import DataFrame, Series
from pmagpy import pmag

class Contribution(object):

    def __init__(self, directory):
        directory = os.path.realpath(directory)
        tables = ['measurements', 'specimens', 'samples',
                  'sites', 'locations', 'contribution',
                  'criteria', 'ages', 'images']

        self.tables = {}
        for name in tables:
            filename = os.path.join(directory, name + ".txt")
            print filename
            if os.path.exists(filename):
                self.tables[name] = MagicDataFrame(filename)

               
    def rename_item(self, table_name, item_old_name, item_new_name):

        # define some helper methods:
        def split_if_str(x):
            if isinstance(x, str):
                return x.split(':')
            else:
                return x

        def put_together_if_str(x):
            try:
                return ":".join(x)
            except TypeError:
                return x

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


class MagicDataFrame(object):

    def __init__(self, magic_file):
        data, dtype = pmag.magic_read(magic_file)
        self.df = DataFrame(data)
        if dtype.endswith('s'):
            dtype = dtype[:-1]
            name = '{}_name'.format(dtype)
            if dtype == 'contribution':
                name = 'doi'
            self.df.index = self.df[name]
            #del self.df[name]
            self.df.dtype = dtype
            # replace '' with np.nan, so you can use isnull(), notnull(), etc.
            # can always switch back with DataFrame.fillna('')
            self.df[self.df == ''] = np.nan
                
                
    def add_blank_row(self, label):
        """
        Add a blank row with only an index value to self.df
        """
        col_labels = self.df.columns
        blank_item = pd.Series({}, index=col_labels, name=label)
        self.df = self.df.append(blank_item)


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


    def get_di_block(self, df_slice=None, do_index=False, item_names=[], tilt_corr='100'):
        """
        Input either a DataFrame slice
        or
        do_index=True and a list of index_names.
        Output dec/inc from the slice in this format:
        [[dec1, inc1], [dec2, inc2], ...]
        """
        if isinstance(df_slice, str):
            if df_slice == "all":
                # use entire DataFrame
                df_slice = self.df
        elif do_index:
            # use fancy indexing (but note this will give duplicates)
            df_slice = self.df.ix[item_names]
        elif not do_index:
            # otherwise use the provided slice
            df_slice = df_slice

        # once you have the slice, fix up the data
        df_slice = df_slice[df_slice['dir_tilt_correction'] == tilt_corr]
        df_slice = df_slice[df_slice['dir_inc'].notnull() & df_slice['dir_dec'].notnull()]
        # possible add in:
        # split out di_block from this study from di_block from other studies (in citations column)
        # for now, just use "This study"
        if 'citations' in df_slice.columns:
            df_slice = df_slice[df_slice['citations'] == "This study"]

        # convert values into DIblock format
        di_block = [[float(row['dir_dec']), float(row['dir_inc'])] for ind, row in df_slice.iterrows()]
        return di_block




if __name__ == "__main__":
    working_dir = "/Users/nebula/Python/PmagPy/3_0"
    print 'working_dir', working_dir
    con = Contribution(working_dir)
    con.tables['locations'].df['site_name'] = ['16', np.nan, '30', '22']
    con.rename_item('sites', '16', 'classier_site')
    print con
    print con.tables.keys()
    print con.tables['locations'].df[['site_names', 'site_name']]
    
