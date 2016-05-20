#!/usr/bin/env python

import os
import numpy as np
import pandas as pd
import re
from pandas import DataFrame, Series
from pmagpy import pmag

class Contribution(object):

    def __init__(self, directory, read_tables='all', custom_filenames=None, single_file=None):
        self.directory = os.path.realpath(directory)
        self.table_names = ['measurements', 'specimens', 'samples',
                            'sites', 'locations', 'contribution',
                            'criteria', 'ages', 'images']
        # create standard filenames from table names
        self.filenames = {t: t + ".txt" for t in self.table_names}
        # update self.filenames to include custom names
        if custom_filenames:
            self.add_custom_filenames(custom_filenames)

        self.tables = {}
        # if not otherwise specified, read in all possible tables
        if read_tables == 'all':
            read_tables = self.table_names

        if single_file: # use if filename is known but type isn't
            self.add_magic_table('unknown', single_file)
            print 'self.tables.keys()', self.tables.keys()
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
                return
            else:
                self.tables[dtype] = data_container
                return
        # if providing a data type, use the canonical filename
        elif dtype not in self.filenames:
            print '-W- "{}" is not a valid MagIC table type'.format(dtype)
            print "-I- Available table types are: {}".format(", ".join(self.table_names))
            return
        filename = os.path.join(self.directory, self.filenames[dtype])
        print 'filename', filename
        if os.path.exists(filename):
            self.tables[dtype] = MagicDataFrame(filename)
        else:
            print "-W- No such file: {}".format(filename)


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


    def add_site_names_to_specimen_table(self):
        """
        Add temporary column "site_name" at specimen level.
        Requires specimen & sample data to be available.
        """
        # first make sure contribution has both specimen & sample level data
        print 'trying to add site_name'
        for dtype in ['specimens', 'samples']:
            if dtype not in self.tables:
                self.add_magic_table(dtype)
            # if no data was found to add:
            if dtype not in self.tables:
                print "-W- No {} data found".format(dtype)
                return
        # next, do SQL style join
        spec_container = self.tables['specimens']
        samp_container = self.tables['samples']
        print 'samp_container', len(samp_container.df)
        spec_container.merge_in(join_on='sample_name',
                                right_df=samp_container.df,
                                add_col='site_name')
        print 'self.tables.keys() at end of add_site_names', self.tables.keys()
            


class MagicDataFrame(object):

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


    def get_di_block(self, df_slice=None, do_index=False, item_names=[], tilt_corr='100'):
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
        pattern = re.compile('{}(?=:|\s|\Z)'.format(meth_code))
        # (must use fillna to replace np.nan with False for indexing)
        if use_slice:
            df = sli
        else:
            df = self.df.copy()
        cond = df['method_codes'].str.contains(pattern).fillna('')
        if incl:
            # return a copy of records with that method code:
            return df[cond]
        else:
            # return a copy of records without that method code
            return df[~cond]


    def merge_in(self, join_on, right_df, add_col):
        #if 'site_name' not in spec_df.columns:
        #    spec_df = spec_df.merge(samp_df[['site_name']], left_on=['sample_name'], right_index=True, how="left")
        if add_col not in self.df.columns:
            # SQL style merge between two DataFrames
            # joins on self.df.index and specified col for other dataframe
            self.df = self.df.merge(right_df[[add_col]], left_on=[join_on], right_index=True, how="left")
     


if __name__ == "__main__":
    working_dir = "/Users/nebula/Python/PmagPy/3_0"
    print 'working_dir', working_dir
    con = Contribution(working_dir)
    con.tables['locations'].df['site_name'] = ['16', np.nan, '30', '22']
    con.rename_item('sites', '16', 'classier_site')
    print con
    print con.tables.keys()
    print con.tables['locations'].df[['site_names', 'site_name']]
    
