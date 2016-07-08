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
from pmagpy import data_model3 as data_model


class Contribution(object):

    """
    A Contribution is a collection of MagicDataFrames,
    each of which corresponds to one MagIC table.
    The Contribution object also has methods for
    manipulating one or more tables in the contribution --
    for example, renaming a site.
    """

    def __init__(self, directory, read_tables='all',
                 custom_filenames=None, single_file=None,
                 dmodel=None):
        self.data_model = dmodel
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
            data_container = MagicDataFrame(filename, dmodel=self.data_model)
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
            data_container = MagicDataFrame(filename, dmodel=self.data_model)
            self.tables[dtype] = data_container
            return data_container
        else:
            print "-W- No such file: {}".format(filename)
            return False

    def rename_item(self, table_name, item_old_name, item_new_name):
        """
        Rename item (such as a site) everywhere that it occurs.
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

        def put_together_if_list(item):
            """
            String joining function
            that doesn't break with None/np.nan
            """
            try:
                res = ":".join(item)
                return ":".join(item)
            except TypeError as ex:
                print ex
                return item

        def replace_colon_delimited_value(df, col_name, old_value, new_value):
            """
            Col must contain list
            """
            count = 1
            for index, row in df[df[col_name].notnull()].iterrows():
                names_list = row[col_name]
                names_list = [name.strip() for name in names_list]
                try:
                    ind = names_list.index(old_value)
                except ValueError as ex:
                    count += 1
                    continue
                names_list[ind] = new_value
                df.ix[count, col_name] = names_list
                count += 1


        # initialize some things
        item_type = table_name
        ###col_name = item_type[:-1] + "_name"
        col_name = item_type[:-1]
        col_name_plural = col_name + "s"
        table_df = self.tables[item_type].df
        # rename item in its own table
        table_df.rename(index={item_old_name: item_new_name}, inplace=True)
        # rename in any parent/child tables
        for table_name in self.tables:
            df = self.tables[table_name].df
            col_names = df.columns
            # change anywhere col_name (singular, i.e. site) is found
            if col_name in col_names:
                df[col_name].where(df[col_name] != item_old_name, item_new_name, inplace=True)
                # change anywhere col_name (plural, i.e. sites) is found
            if col_name_plural in col_names:
                df[col_name_plural + "_list"] = df[col_name_plural].apply(split_if_str)
                replace_colon_delimited_value(df, col_name_plural + "_list", item_old_name, item_new_name)
                df[col_name_plural] = df[col_name_plural + "_list"].apply(put_together_if_list)
            self.tables[table_name].df = df

    def get_table_name(self, ind):
        """
        Return both the table_name (i.e., 'specimens')
        ###and the col_name (i.e., 'specimen_name')
        and the col_name (i.e., 'specimen')
        for a given index in self.ancestry.
        """
        if ind >= len(self.ancestry):
            return "", ""
        if ind > -1:
            table_name = self.ancestry[ind]
            ###name = table_name[:-1] + "_name"
            name = table_name[:-1]
            return table_name, name
        return "", ""

    
    def propagate_name_down(self, col_name, df_name):
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
        grandparent_name = grandparent_table_name[:-1]
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
            self.tables[df_name].df = df

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
            self.tables[df_name].df = df

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


    def propagate_cols_down(self, col_names, target_df_name, source_df_name):
        """
        Put the data for "col_name" from source_df into target_df
        Used to get "azimuth" from sample table into measurements table
        (for example).
        ###Note: if getting data from the sample table, don't include "sample_name"
        Note: if getting data from the sample table, don't include "sample"
        in the col_names list.  It is included automatically.
        """
        # make sure target table is read in
        if target_df_name not in self.tables:
            self.add_magic_table(target_df_name)
        if target_df_name not in self.tables:
            print "-W- Couldn't read in {} table".format(target_df_name)
            return
        # make sure source table is read in
        if source_df_name not in self.tables:
            self.add_magic_table(source_table_name)
            print "-W- Couldn't read in {} table".format(source_df_name)
            return
        # make sure col_names are all available in source table
        source_df = self.tables[source_df_name].df
        if not set(col_names).issubset(source_df.columns):
            for col in col_names[:]:
                if col not in source_df.columns:
                    print "-W- Column '{}' isn't in {} table, skipping it".format(col, source_df_name)
                    col_names.remove(col)
        if not col_names:
            print "-W- Invalid or missing column names, could not propagate down"
            return
        
        ###add_name = source_df_name[:-1] + "_name"
        add_name = source_df_name[:-1]
        self.propagate_name_down(add_name, target_df_name)
        #
        target_df = self.tables[target_df_name].df
        source_df = self.tables[source_df_name].df
        #
        target_df = target_df.merge(source_df[col_names], how='left', left_on=add_name, right_index=True)
        self.tables[target_df_name].df = target_df
        return target_df


class MagicDataFrame(object):

    """
    Each MagicDataFrame corresponds to one MagIC table.
    The MagicDataFrame object consists of a pandas DataFrame,
    and assorted methods for manipulating that DataFrame.
    """

    def __init__(self, magic_file=None, columns=None, dtype=None,
                 groups=None, dmodel=None, df=None):
        """
        Provide either a magic_file or a dtype.
        List of columns is optional,
        and will only be used if magic_file == None.
        Instead of a list of columns, you can also provide
        a list of group-names, and the specific col_names
        will be filled in by the data model.
        """
        if isinstance(df, pd.DataFrame):
            self.df = df
            if dtype:
                self.dtype = dtype
            else:
                print '-W- Please provide data type...'
        # make sure all required arguments are present
        if not magic_file and not dtype and not isinstance(df, pd.DataFrame):
            print "-W- To make a MagicDataFrame, you must provide either a filename or a datatype"
            return
        # fetch data model if not provided
        if not dmodel:
            self.data_model = data_model.DataModel()
        else:
            self.data_model = dmodel

        if isinstance(df, pd.DataFrame):
            pass
        # if no file is provided, make an empty dataframe of the appropriate type
        elif not magic_file:
            self.dtype = dtype
            if not isinstance(columns, type(None)):
                self.df = DataFrame(columns=columns)
            else:
                self.df = DataFrame()
                self.df.index.name = dtype[:-1] if dtype.endswith("s") else dtype
        # if there is a file provided, read in the data and ascertain dtype
        else:
            data, dtype, keys = pmag.magic_read(magic_file, return_keys=True)
            self.df = DataFrame(data)
            if dtype == 'bad_file':
                print "-W- Bad file {}".format(magic_file)
                self.dtype = 'empty'
                return
            #
            self.dtype = dtype
            if dtype == 'measurements':
                ###self.df['measurement_name'] = self.df['experiment_name'] + self.df['measurement_number']
                self.df['measurement'] = self.df['experiment'] + self.df['number']
                name = 'measurement'
            elif dtype.endswith('s'):
                dtype = dtype[:-1]
                ###name = '{}_name'.format(dtype)
                name = '{}'.format(dtype)
            elif dtype == 'contribution':
                name = 'doi'
                # **** this is broken at the moment, fix it!
                return
            # fix these:
            if dtype == 'age':
                # find which key has _name in it, use that as index
                # this won't work if site_name/sample_name/etc. are interspersed
                for key in keys:
                    if 'name' in key:
                        name = key
                        break
            if dtype == 'image':
                self.df = pd.DataFrame()
                return
            if dtype == 'criteria':
                #self.df = pd.DataFrame()
                self.df.index = self.df['table_column']
                return
            if len(self.df):
                self.df.index = self.df[name]
            #del self.df[name]
            #self.dtype = dtype
            # replace '' with None, so you can use isnull(), notnull(), etc.
            # can always switch back with DataFrame.fillna('')
            self.df[self.df == ''] = None
            # drop any completely blank columns
            self.df.dropna(axis=1, how='all', inplace=True)

        # add col_names by group
        if groups and not columns:
            columns = []
            for group_name in groups:
                columns.extend(list(self.data_model.get_headers(self.dtype, group_name)))
            for col in columns:
                if col not in self.df.columns:
                    self.df[col] = None
            self.df = self.df[columns]



    def update_row(self, ind, row_data):
        """
        Update a row with data.
        Must provide the specific numeric index (not row label).
        If any new keys are present in row_data dictionary,
        that column will be added to the dataframe
        """
        if sorted(row_data.keys()) != sorted(self.df.columns):
            # add any new column names
            for key in row_data:
                if key not in self.df.columns:
                    self.df[key] = None
            # add missing column names into row_data
            for col_label in self.df.columns:
                if col_label not in row_data.keys():
                    row_data[col_label] = None
        self.df.iloc[ind] = row_data


    def add_row(self, label, row_data):
        """
        Add a row with data.
        If any new keys are present in row_data dictionary,
        that column will be added to the dataframe
        """
        if sorted(row_data.keys()) != sorted(self.df.columns):
            # add any new column names
            for key in row_data:
                if key not in self.df.columns:
                    self.df[key] = None
            # add missing column names into row_data
            for col_label in self.df.columns:
                if col_label not in row_data.keys():
                    row_data[col_label] = None
        self.df.loc[label] = row_data

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
        first_val = df_slice[col_name].dropna()
        if any(first_val):
            return first_val[0]
        else:
            return ""
        #return df_slice[col_name].dropna()[0]

    def get_di_block(self, df_slice=None, do_index=False,
                     item_names=None, tilt_corr='100',
                     excl=None):
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
        # tilt correction must match
        if tilt_corr != "0":
            df_slice = df_slice[df_slice['dir_tilt_correction'] == tilt_corr]
        else:
            # if geographic ("0"),
            # use records with no tilt_corr and assume geographic
            cond1 = df_slice['dir_tilt_correction'] == None
            cond2 = df_slice['dir_tilt_correction'] == tilt_corr
            df_slice = df_slice[cond1 | cond2]
        # exclude data with unwanted codes
        if excl:
            for ex in excl:
                df_slice = self.get_records_for_code(ex, incl=False,
                                                     use_slice=True,
                                                     sli=df_slice)

        df_slice = df_slice[df_slice['dir_inc'].notnull() & df_slice['dir_dec'].notnull()]
        # possible add in:
        # split out di_block from this study from di_block from other studies (in citations column)
        # for now, just use "This study"
        if 'citations' in df_slice.columns:
            df_slice = df_slice[df_slice['citations'] == "This study"]

        # convert values into DIblock format
        di_block = [[float(row['dir_dec']), float(row['dir_inc'])] for ind, row in df_slice.iterrows()]
        return di_block


    def get_records_for_code(self, meth_code, incl=True, use_slice=False,
                             sli=None, strict_match=True):
        """
        Use regex to see if meth_code is in the method_codes ":" delimited list.
        If incl == True, return all records WITH meth_code.
        If incl == False, return all records WITHOUT meth_code.
        If strict_match == True, return only records with the exact meth_code.
        If strict_match == False, return records that contain the meth_code partial string,
        (i.e., "DE-")
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
        if not strict_match:
            # grab any record that contains any part of meth_code
            cond = df['method_codes'].str.contains(meth_code).fillna(False)
        else:
            # grab only an exact match
            pattern = re.compile('{}(?=:|\s|\Z)'.format(meth_code))
            cond = df['method_codes'].str.contains(pattern).fillna(False)
        if incl:
            # return a copy of records with that method code:
            return df[cond]
        else:
            # return a copy of records without that method code
            return df[~cond]


    def write_magic_file(self, custom_name=None, dir_path="."):
        """
        Write self.df out to tab-delimited file.
        By default will use standard MagIC filenames (specimens.txt, etc.),
        or you can provide a custom_name to write to instead.
        By default will write to current directory, 
        or provide dir_path to write out to instead.
        """
        # *** maybe add some logical order to the column names, here?
        # *** i.e., alphabetical...  see grid_frame3.GridBuilder.make_grid
        df = self.df
        dir_path = os.path.realpath(dir_path)
        if custom_name:
            fname = os.path.join(dir_path, custom_name)
        else:
            fname = os.path.join(dir_path, self.dtype + ".txt")
        if os.path.exists(fname):
            print '-I- overwriting {}'.format(fname)
        else:
            print '-I- writing {} data to {}'.format(self.dtype, fname)
        f = open(fname, 'w')
        f.write('tab\t{}\n'.format(self.dtype))
        df.to_csv(f, sep="\t", header=True, index=False)
        f.close()


if __name__ == "__main__":
    pass
