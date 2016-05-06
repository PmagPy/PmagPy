#!/usr/bin/env python

import os
import numpy as np
import pandas as pd
from pandas import DataFrame, Series
from pmagpy import pmag

class Contribution(object):

    def __init__(self, directory):
        print 'directory', directory
        print os.path.relpath(directory)
        directory = os.path.realpath(directory)
        print 'directory', directory
        tables = ['measurements', 'specimens', 'samples',
                  'sites', 'locations', 'contribution',
                  'criteria', 'ages', 'images']

        self.tables = {}
        for name in tables:
            filename = os.path.join(directory, name + ".txt")
            print filename
            if os.path.exists(filename):
                print 'filename', filename
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
            print 'dtype', dtype
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
        col_labels = self.df.columns
        blank_item = pd.Series({}, index=col_labels, name=label)
        self.df = self.df.append(blank_item)


    def get_name(self, df_or_series, col_name):
        # series
        if isinstance(df_or_series, pd.Series):
            if col_name not in df_or_series.index:
                return ""
            else:
                return df_or_series[col_name]
        # dataframe
        if col_name not in df_or_series.columns:
            return ""
        value = df_or_series[col_name]
        if isinstance(value, pd.Series):
            return value[0]





if __name__ == "__main__":
    working_dir = "/Users/nebula/Python/PmagPy/3_0"
    print 'working_dir', working_dir
    con = Contribution(working_dir)
    con.tables['locations'].df['site_name'] = ['16', np.nan, '30', '22']
    con.rename_item('sites', '16', 'classier_site')
    print con
    print con.tables.keys()
    print con.tables['locations'].df[['site_names', 'site_name']]
