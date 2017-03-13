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
import numpy as np
import pandas as pd
from pandas import DataFrame
# from pmagpy import pmag
from pmagpy import data_model3 as data_model
from pmagpy import controlled_vocabularies3 as cv


class Contribution(object):

    """
    A Contribution is a collection of MagicDataFrames,
    each of which corresponds to one MagIC table.
    The Contribution object also has methods for
    manipulating one or more tables in the contribution --
    for example, renaming a site.
    """

    def __init__(self, directory=".", read_tables='all',
                 custom_filenames=None, single_file=None,
                 dmodel=None, vocabulary=""):
        if isinstance(dmodel, data_model.DataModel):
            self.data_model = dmodel
            Contribution.dmodel = dmodel
        else:
            try:
                self.data_model = Contribution.dmodel
            except AttributeError:
                Contribution.dmodel = data_model.DataModel()
                self.data_model = Contribution.dmodel
        if isinstance(vocabulary, cv.Vocabulary):
            self.vocab = vocabulary
        else:
            try:
                self.vocab = Contribution.vocab
            except AttributeError:
                Contribution.vocab = cv.Vocabulary(dmodel=self.data_model)
                self.vocab = Contribution.vocab
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

    ## Methods for building up the contribution

    def add_custom_filenames(self, custom_filenames):
        """
        Update/overwrite self.filenames with custom names.
        Input dict should have the format:
        {"specimens": "custom_spec_file.txt", ...}
        """
        if custom_filenames:
            self.filenames.update(custom_filenames)

    def add_empty_magic_table(self, dtype, col_names=None, groups=None):
        """
        Add a blank MagicDataFrame to the contribution.
        You can provide either a list of column names,
        or a list of column group names.
        If provided, col_names takes precedence.
        """
        if dtype not in self.table_names:
            print "-W- {} is not a valid MagIC table name".format(dtype)
            print "-I- Valid table names are: {}".format(", ".join(self.table_names))
            return
        data_container = MagicDataFrame(dtype=dtype, columns=col_names, groups=groups)
        self.tables[dtype] = data_container

    def add_magic_table_from_data(self, dtype, data):
        """
        Add a MagIC table to the contribution from a data list


        Parameters
        ----------
        dtype : str
            MagIC table type
        data : list of dicts
            data list with format [{'key1': 'val1', ...}, {'key1': 'val2', ...}, ... }]
        """
        self.tables[dtype] = MagicDataFrame(dtype=dtype, data=data)


    def add_magic_table(self, dtype, fname=None, df=None):
        """
        Read in a new file to add a table to self.tables.
        Requires dtype argument and EITHER filename or df.

        Parameters
        ----------
        dtype : str
            MagIC table name
        fname : str
            filename of MagIC format file
            (short path, directory is self.directory)
        df : pandas DataFrame
            data to create the new table with
        """
        if df is None:
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
                if data_container.dtype != "empty":
                    self.tables[dtype] = data_container
                    return data_container
            else:
                print "-W- No such file: {}".format(filename)
                return False
        # df is not None
        else:
            if not dtype:
                print "-W- Must provide dtype"
                return False
            data_container = MagicDataFrame(dtype=dtype, df=df)
            self.tables[dtype] = data_container


    def propagate_measurement_info(self):
        """
        Take a contribution with a measurement table.
        Create specimen, sample, site, and location tables
        using the unique names in the measurement table to fill in
        the index.
        """
        meas_df = self.tables['measurements'].df
        names_list = ['specimen', 'sample', 'site', 'location']
        # add in any tables that you can
        for num, name in enumerate(names_list):
            # don't replace tables that already exist
            if (name + "s") in self.tables:
                continue
            elif name in meas_df.columns:
                print "making new {} file".format(name)
                items = meas_df[name].unique()
                df = pd.DataFrame(columns=[name], index=items)
                df[name] = df.index
                # add in parent name if possible
                # (i.e., sample name to specimens table)
                if num < (len(names_list) - 1):
                    parent = names_list[num+1]
                    if parent in meas_df.columns:
                        df[parent] = meas_df.drop_duplicates(subset=[name])[parent].values
                self.tables[name + "s"] = MagicDataFrame(dtype=name + "s", df=df)
                self.write_table_to_file(name + "s")


    def propagate_all_tables_info(self, write=True):
        """
        Find any items (specimens, samples, sites, or locations) from
        tables other than measurements and make sure they each have a
        row in their own table.  For example, if a site name is in
        the samples table but not in the sites table, create a row
        for it in the sites table.
        """
        for table_name in ["specimens", "samples", "sites", "locations"]:
            if not table_name in self.tables:
                continue
            df = self.tables[table_name].df
            parent_name, child_name = self.get_parent_and_child(table_name)
            if parent_name:
                if parent_name[:-1] in df.columns:
                    parents = sorted(set(df[parent_name[:-1]].dropna().values))
                    if parent_name in self.tables: # if there is a parent table, update it
                        parent_df = self.tables[parent_name].df
                        missing_parents = set(parents) - set(parent_df.index)
                        if missing_parents: # add any missing values
                            print "-I- Updating {} table with values from {} table".format(parent_name, table_name)
                            for item in missing_parents:
                                self.add_item(parent_name, {parent_name[:-1]: item}, label=item)
                            # save any changes to file
                            if write:
                                self.write_table_to_file(parent_name)

                    else:  # if there is no parent table, create it if necessary
                        if parents:
                            # create a parent_df with the names you got from the child
                            print "-I- Creating new {} table with data from {} table".format(parent_name, table_name)
                            parent_df = pd.DataFrame(columns=[parent_name[:-1]], index=parents)
                            parent_df[parent_name[:-1]] = parent_df.index
                            self.tables[parent_name] = MagicDataFrame(dtype=parent_name,
                                                                      df=parent_df)
                            if write:
                                # save new table to file
                                self.write_table_to_file(parent_name)
            if child_name:
                if child_name in df.columns:
                    raw_children = df[child_name].dropna().str.split(':')
                    # create dict of all children with parent info
                    parent_of_child = {}
                    for parent, children in raw_children.iteritems():
                        for child in children:
                            # remove whitespace
                            child = child.strip()
                            old_parent = parent_of_child.get(child)
                            if old_parent and parent and (old_parent != parent):
                                print '-I- for {} {}, replacing: {} with: {}'.format(child_name[:-1], child,
                                                                                     old_parent, parent)
                            parent_of_child[child] = parent
                    # old way:
                    # flatten list, ignore duplicates
                    #children = sorted(set([item.strip() for sublist in raw_children for item in sublist]))
                    if child_name in self.tables: # if there is already a child table, update it
                        child_df = self.tables[child_name].df
                        missing_children = set(parent_of_child.keys()) - set(child_df.index)
                        if missing_children: # add any missing values
                            print "-I- Updating {} table with values from {} table".format(child_name, table_name)
                            for item in missing_children:
                                data = {child_name[:-1]: item, table_name[:-1]: parent_of_child[item]}
                                self.add_item(child_name, data, label=item)
                            if write:
                                # save any changes to file
                                self.write_table_to_file(child_name)
                    else: # if there is no child table, create it if necessary
                        if children:
                            # create a child_df with the names you got from the parent
                            print "-I- Creating new {} table with data from {} table".format(child_name, table_name)
                            # old way to make new table:
                            #child_df = pd.DataFrame(columns=[table_name[:-1]], index=children)
                            # new way to make new table
                            children_list = sorted(parent_of_child.keys())
                            children_data = [[child_name, parent_of_child[c_name]] for c_name in children_list]
                            child_df = pd.DataFrame(index=children_list, columns=[child_name[:-1], table_name[:-1]], data=children_data)

                            self.tables[child_name] = MagicDataFrame(dtype=child_name, df=child_df)
                            if write:
                                # save new table to file
                                self.write_table_to_file(child_name)


    def get_parent_and_child(self, table_name):
        """
        Get the name of the parent table and the child table
        for a given MagIC table name.

        Parameters
        ----------
        table_name : string of MagIC table name ['specimens', 'samples', 'sites', 'locations']

        Returns
        -------
        parent_name : string of parent table name
        child_name : string of child table name
        """
        if table_name not in self.ancestry:
            return None, None
        parent_ind = self.ancestry.index(table_name) + 1
        if parent_ind + 1 > len(self.ancestry):
            parent_name = None
        else:
            parent_name = self.ancestry[parent_ind]
        child_ind = self.ancestry.index(table_name) - 1
        if child_ind < 0:
            child_name = None
        else:
            child_name = self.ancestry[child_ind]
        return parent_name, child_name

    def get_min_max_lat_lon(self):
        """
        Find latitude/longitude information from sites table
        and group it by location.

        Returns
        ---------
        """
        if 'sites' not in self.tables:
            return
        # get min/max lat/lon from sites table
        site_container = self.tables['sites']
        if not ('lat' in site_container.df.columns and 'lon' in site_container.df.columns):
            return
        # convert lat/lon columns to string type
        # (this is necessary for consistency because they MAY be string type already)
        site_container.df['lat'] = site_container.df['lat'].fillna('').astype(str)
        site_container.df['lon'] = site_container.df['lon'].fillna('').astype(str)
        # replace empty strings with np.nan
        site_container.df['lat'] = np.where(site_container.df['lat'].str.len(), site_container.df['lat'], np.nan)
        site_container.df['lon'] = np.where(site_container.df['lon'].str.len(), site_container.df['lon'], np.nan)
        # convert lat/lon values to float (they make be string from grid)
        site_container.df['lat'] = site_container.df['lat'].astype(float)
        site_container.df['lon'] = site_container.df['lon'].astype(float)
        # group lat/lon by location
        grouped_lon = site_container.df[['lon', 'location']].groupby('location')
        grouped_lat = site_container.df[['lat', 'location']].groupby('location')
        # get min/max longitude by location
        lon_w = grouped_lon.min()
        lon_e = grouped_lon.max()
        # get min/max latitude by location
        lat_s = grouped_lat.min()
        lat_n = grouped_lat.max()
        # assign lat/lon to location table
        locs = {}
        if 'locations' not in self.tables:
            return
        loc_container = self.tables['locations']
        for loc in lat_s.index:
            coords = {}
            coords['lat_s'] = lat_s.loc[loc]['lat']
            coords['lat_n'] = lat_n.loc[loc]['lat']
            coords['lon_e'] = lon_e.loc[loc]['lon']
            coords['lon_w'] = lon_w.loc[loc]['lon']
            locs[loc] = coords
        loc_container = self.tables['locations']
        for loc_name in locs:
            if loc_name in loc_container.df.index:
                coords = locs[loc_name]
                for coord in locs[loc_name]:
                    # warn user if an old value will be overwritten
                    new_value = coords[coord]
                    # if the new value is null, ignore it
                    if np.isnan(new_value):
                        continue
                    # set old value to None if it wasn't in table
                    if coord not in loc_container.df.columns:
                        loc_container.df[coord] = None
                    old_value = loc_container.df.ix[loc_name, coord]
                    # use first value if multiple values returned, but don't shorten a string
                    if not (isinstance(old_value, str) or isinstance(old_value, unicode)):
                        try:
                            old_value = old_value[0]
                        except TypeError: # if only one value
                            pass
                        except IndexError: # if np.nan
                            pass
                    if old_value is None or old_value is np.nan:
                        pass
                    elif isinstance(old_value, str) or isinstance(old_value, unicode):
                        try:
                            old_value = float(old_value)
                        except ValueError:
                            print '-W- In {}, automatically generated {} value ({}) will overwrite previous value ({})'.format(loc_name, coord, new_value, old_value)
                            old_value = None
                    elif np.isnan(old_value):
                        pass
                    elif new_value != old_value:
                        print '-W- In {}, automatically generated {} value ({}) will overwrite previous value ({})'.format(loc_name, coord, new_value, old_value)
                    # set new value
                    loc_container.df.set_value(loc_name, coord, new_value)
        self.write_table_to_file('locations')
        return locs

    def add_item(self, table_name, data, label):
        self.tables[table_name].add_row(label, data)

    ## Methods for making changes to a Contribution
    ## that need to propagate to multiple tables

    def rename_item(self, table_name, item_old_name, item_new_name):
        """
        Rename item (such as a site) everywhere that it occurs.
        This change often spans multiple tables.
        For example, a site name will occur in the sites table,
        the samples table, and possibly in the locations/ages tables.
        """
        # define some helper methods:

        def put_together_if_list(item):
            """
            String joining function
            that doesn't break with None/np.nan
            """
            try:
                res = ":".join(item)
                return ":".join(item)
            except TypeError as ex:
                #print ex
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

        if item_old_name == '':
            # just add a new item
            self.add_item(table_name, {col_name: item_new_name}, item_new_name)
            return

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
                df[col_name_plural + "_list"] = df[col_name_plural].str.split(":")
                replace_colon_delimited_value(df, col_name_plural + "_list", item_old_name, item_new_name)
                df[col_name_plural] = df[col_name_plural + "_list"].apply(put_together_if_list)
                df.drop(col_name_plural + "_list", axis=1, inplace=True)
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
            self.add_magic_table(source_df_name)
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

        add_name = source_df_name[:-1]
        self.propagate_name_down(add_name, target_df_name)
        #
        target_df = self.tables[target_df_name].df
        source_df = self.tables[source_df_name].df
        #
        target_df = target_df.merge(source_df[col_names], how='left',
                                    left_on=add_name, right_index=True,
                                    suffixes=["_target", "_source"])
        # mess with target_df to remove unneded merge columns
        for col in col_names:
            # if there has been a previous merge, consolidate and delete data
            if col + "_target" in target_df.columns:
                # prioritize values from target df
                new_arr = np.where(target_df[col + "_target"],
                                   target_df[col + "_target"],
                                   target_df[col + "_source"])
                target_df.rename(columns={col + "_target": col}, inplace=True)
                target_df[col] = new_arr
            if col + "_source" in target_df.columns:
                # delete extra merge column
                del target_df[col + "_source"]
        #
        self.tables[target_df_name].df = target_df
        return target_df

    def remove_non_magic_cols(self):
        """
        Remove all non-MagIC columns from all tables.
        """
        for table_name in self.tables:
            table = self.tables[table_name]
            table_dm = self.data_model.dm[table_name]
            approved_cols = table_dm.index
            unrecognized_cols = (set(table.df.columns) - set(approved_cols))
            if unrecognized_cols:
                print '-I- Removing non-MagIC column names from {}:'.format(table_name),
                for col in unrecognized_cols:
                    self.tables[table_name].df.drop(col, axis='columns', inplace=True)
                    print col,
                print "\n"

    def write_table_to_file(self, dtype):
        """
        Write out a MagIC table to file, using custom filename
        as specified in self.filenames.

        Parameters
        ----------
        dtype : str
            magic table name
        """
        fname = self.filenames[dtype]
        if dtype in self.tables:
            self.tables[dtype].write_magic_file(custom_name=fname,
                                                dir_path=self.directory)



class MagicDataFrame(object):

    """
    Each MagicDataFrame corresponds to one MagIC table.
    The MagicDataFrame object consists of a pandas DataFrame,
    and assorted methods for manipulating that DataFrame.
    """

    def __init__(self, magic_file=None, columns=None, dtype=None,
                 groups=None, dmodel=None, df=None, data=None):
        """
        Provide either a magic_file or a dtype.
        List of columns is optional,
        and will only be used if magic_file == None.
        Instead of a list of columns, you can also provide
        a list of group-names, and the specific col_names
        will be filled in by the data model.
        If provided, col_names takes precedence.
        """
        # first fetch data model if not provided
        # (DataModel type sometimes not recognized, hence ugly hack below)
        if isinstance(dmodel, data_model.DataModel) or str(data_model.DataModel) == str(type(dmodel)):
            MagicDataFrame.data_model = dmodel
            self.data_model = dmodel
        else:
            try:
                self.data_model = MagicDataFrame.data_model
            except AttributeError:
                MagicDataFrame.data_model = data_model.DataModel()
                self.data_model = MagicDataFrame.data_model

        # create MagicDataFrame using a DataFrame and a dtype:
        if isinstance(df, pd.DataFrame):
            self.df = df
            if dtype:
                name, self.dtype = self.get_singular_and_plural_dtype(dtype)
                if name in self.df.columns:
                    self.df.index = self.df[name]
            else:
                print '-W- Please provide data type...'

        # create MagicDataFrame using data and a dtype
        if data:
            df = pd.DataFrame(data)
            self.df = df
            if dtype:
                self.dtype = dtype
                try:
                    self.df.index = self.df[dtype[:-1]]
                except KeyError:
                    pass

            else:
                print "-W- To make a MagicDataFrame from data, you must provide a datatype"
                self.df = None
                return

        # if user has not provided a filename, they must provide a dtype and either a df/data
        # warn them and return
        if not magic_file and not dtype and not isinstance(df, pd.DataFrame):
            print "-W- To make a MagicDataFrame, you must provide either a filename or a datatype"
            self.df = None
            return

        # create MagicDataFrame using a DataFrame and a dtype:
        if isinstance(df, pd.DataFrame):
            self.df = df
            if dtype:
                name, self.dtype = self.get_singular_and_plural_dtype(dtype)
                if name in self.df.columns:
                    self.df.index = self.df[name]
            else:
                print '-W- Please provide data type...'

        # create MagicDataFrame using data and a dtype
        if data:
            df = pd.DataFrame(data)
            self.df = df
            if dtype:
                self.dtype = dtype
                try:
                    self.df.index = self.df[dtype[:-1]]
                except KeyError:
                    pass

            else:
                print "-W- To make a MagicDataFrame from data, you must provide a datatype"
                self.df = None
                return

        # if user has not provided a filename, they must provide a dtype and either a df/data
        # warn them and return
        if not magic_file and not dtype and not isinstance(df, pd.DataFrame):
            print "-W- To make a MagicDataFrame, you must provide either a filename or a datatype"
            self.df = None
            return

        # if a DataFrame was already created, continue
        # otherwise create MagicDataFrame by reading the file if present,
        # or make an empty MagicDataFrame of the correct dtype
        if isinstance(df, pd.DataFrame):
            # get singular name and plural datatype
            name, self.dtype = self.get_singular_and_plural_dtype(dtype)
        # if no file is provided, make an empty dataframe of the appropriate type
        elif dtype and not magic_file:
            name, self.dtype = self.get_singular_and_plural_dtype(dtype)
            if not isinstance(columns, type(None)):
                self.df = DataFrame(columns=columns)
            else:
                self.df = DataFrame()
                self.df.index.name = name #dtype[:-1] if dtype.endswith("s") else dtype
        # if there is a file provided, read in the data and ascertain dtype
        else:
            ## new way of reading in data using pd.read_table
            with open(magic_file) as f:
                try:
                    delim, dtype = f.readline().split('\t')[:2]
                except ValueError as ex:
                    print ex, type(ex)
                    print "-W- Empty file {}".format(magic_file)
                    self.dtype = 'empty'
                    self.df = DataFrame()
                    return
            # get singular name and plural datatype
            name, self.dtype = self.get_singular_and_plural_dtype(dtype)
            self.df = pd.read_table(magic_file, skiprows=[0])
            if self.dtype == 'measurements':
                self.df['measurement'] = self.df['experiment'] + self.df['number'].astype(str)
            elif self.dtype == 'contribution':
                return
            elif self.dtype == 'images':
                return
            elif self.dtype == 'criteria':
                self.df.index = self.df['table_column']
                return
            #
            if len(self.df) and self.dtype != 'ages':
                self.df.index = self.df[name].astype(str)
            elif self.dtype == 'ages':
                self.df.index = self.df.index.astype(str)
            #del self.df[name]
            #self.dtype = dtype
            # replace '' with None, so you can use isnull(), notnull(), etc.
            # can always switch back with DataFrame.fillna('')
            self.df = self.df.where(self.df.notnull(), None)

            # drop any completely blank columns
            # this is not necessarily a good idea....
            #self.df.dropna(axis=1, how='all', inplace=True)
            #

        # add any columns specified but not already in self.df
        if columns:
            for col in columns:
                if col not in self.df.columns:
                    self.df[col] = None

        # add col_names by group (unless columns was specified)
        if groups and not columns:
            columns = list(self.df.columns)
            for group_name in groups:
                columns.extend(list(self.data_model.get_group_headers(self.dtype, group_name)))
            for col in columns:
                if col not in self.df.columns:
                    self.df[col] = None
            self.df = self.df[columns]

        # make sure name column is present (i.e., sample column in samples df)
        if name not in ['measurement', 'age']:
            self.df[name] = self.df.index
        elif name == 'measurement':
            self.df['measurement'] = self.df['experiment'] + self.df['number'].astype(str)


    ## Methods to change self.df inplace

    def update_row(self, ind, row_data):
        """
        Update a row with data.
        Must provide the specific numeric index (not row label).
        If any new keys are present in row_data dictionary,
        that column will be added to the dataframe.
        This is done inplace.
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
        try:
            self.df.iloc[ind] = pd.Series(row_data)
        except IndexError:
            return False
        return self.df


    def add_row(self, label, row_data, columns=""):
        """
        Add a row with data.
        If any new keys are present in row_data dictionary,
        that column will be added to the dataframe.
        This is done inplace
        """
        # use provided column order, making sure you don't lose any values
        # from self.df.columns
        if len(columns):
            if sorted(self.df.columns) == sorted(columns):
                self.df.columns = columns
            else:
                new_columns = []
                new_columns.extend(columns)
                for col in self.df.columns:
                    if col not in new_columns:
                        new_columns.append(col)
        # makes sure all columns have data or None
        if sorted(row_data.keys()) != sorted(self.df.columns):
            # add any new column names
            for key in row_data:
                if key not in self.df.columns:
                    self.df[key] = None
            # add missing column names into row_data
            for col_label in self.df.columns:
                if col_label not in row_data.keys():
                    row_data[col_label] = None

        # (make sure you are working with strings)
        self.df.index = self.df.index.astype(str)
        label = str(label)

        # create a new row with suffix "new"
        # (this ensures that you get a unique, new row,
        #  instead of adding on to an existing row with the same label)
        self.df.loc[label + "new"] = pd.Series(row_data)
        # rename it to be correct
        self.df.rename(index={label + "new": label}, inplace=True)
        # use next line to sort index inplace
        #self.df.sort_index(inplace=True)
        return self.df


    def add_data(self, data):  # add append option later
        """
        Add df to a MagicDataFrame using a data list.

        Parameters
        ----------
        data : list of dicts
            data list with format [{'key1': 'val1', ...}, {'key1': 'val2', ...}, ... }]
        dtype : str
            MagIC table type
        """
        df = pd.DataFrame(data)
        name, dtype = self.get_singular_and_plural_dtype(self.dtype)
        if name in df.columns:
            df.index = df[name]
        self.df = df


    def get_singular_and_plural_dtype(self, dtype):
        """
        Parameters
        ----------
        dtype : str
            MagIC table type (specimens, samples, contribution, etc.)

        Returns
        ---------
        name : str
           singular name for MagIC table ('specimen' for specimens table, etc.)
        dtype : str
           plural dtype for MagIC table ('specimens' for specimens table, etc.)
        """
        dtype = dtype.strip()
        if dtype.endswith('s'):
            return dtype[:-1], dtype
        elif dtype == 'criteria':
            return 'table_column', 'criteria'
        elif dtype == 'contribution':
            return 'doi', 'contribution'

    def add_blank_row(self, label):
        """
        Add a blank row with only an index value to self.df.
        This is done inplace.
        """
        col_labels = self.df.columns
        blank_item = pd.Series({}, index=col_labels, name=label)
        # use .loc to add in place (append won't do that)
        self.df.loc[blank_item.name] = blank_item
        return self.df


    def delete_row(self, ind):
        """
        remove self.df row at ind
        inplace
        """
        self.df = pd.concat([self.df[:ind], self.df[ind+1:]])
        return self.df

    def delete_rows(self, condition, info_str=None):
        """
        delete all rows with  condition==True
        inplace

        Parameters
        ----------
        condition : pandas DataFrame indexer
            all self.df rows that meet this condition will be deleted
        info_str : str
            description of the kind of rows to be deleted,
            e.g "specimen rows with blank method codes"

        Returns
        --------
        df_data : pandas DataFrame
            updated self.df
        """
        self.df['num'] = range(len(self.df))
        df_data = self.df
        # delete all records that meet condition
        if len(df_data[condition]) > 0:  #we have one or more records to delete
            inds = df_data[condition]['num'] # list of all rows where condition is TRUE
            for ind in inds[::-1]:
                df_data = self.delete_row(ind)
                if info_str:
                    print "-I- Deleting {}. ".format(info_str),
                    print 'deleting row {}'.format(str(ind))
        # sort so that all rows for an item are together
        df_data.sort_index(inplace=True)
        # redo temporary index
        df_data['num'] = range(len(df_data))
        self.df = df_data
        return df_data


    def update_record(self, name, new_data, condition, update_only=False,
                      debug=False):
        """
        Find the first row in self.df with index == name
        and condition == True.
        Update that record with new_data, then delete any
        additional records where index == name and condition == True.
        Change is inplace
        """
        # add numeric index column temporarily
        self.df['num'] = range(len(self.df))
        df_data = self.df
        condition2 = df_data.index == name
        # edit first of existing data that meets condition
        if len(df_data[condition & condition2]) > 0:  #we have one or more records to update or delete
            # list of all rows where condition is true and index == name
            inds = df_data[condition & condition2]['num']
            #inds = df_data[condition]['num'] # list of all rows where condition is true
            existing_data = dict(df_data.iloc[inds[0]]) # get first record of existing_data from dataframe
            existing_data.update(new_data) # update existing data with new interpretations
            # update row
            self.update_row(inds[0], existing_data)
            # now remove all the remaining records of same condition
            if len(inds) > 1:
                for ind in inds[1:]:
                    print "deleting redundant records for:", name
                    df_data = self.delete_row(ind)
        else:
            if update_only:
                print "no record found for that condition, not updating ", name
            else:
                print 'no record found - creating new one for ', name
                # add new row
                df_data = self.add_row(name, new_data)
        # sort so that all rows for an item are together
        df_data.sort_index(inplace=True)
        # redo temporary index
        df_data['num'] = range(len(df_data))
        self.df = df_data
        return df_data


    ## Methods that take self.df and extract some information from it

    def convert_to_pmag_data_list(self, lst_or_dict="lst", df=None):

        """
        Take MagicDataFrame and turn it into a list of dictionaries.
        This will have the same format as reading in a 2.5 file
        with pmag.magic_read(), i.e.:
        if "lst":
          [{"sample": "samp_name", "azimuth": 12, ...}, {...}]
        if "dict":
          {"samp_name": {"azimuth": 12, ...}, "samp_name2": {...}, ...}
        NOTE: "dict" not recommended with 3.0, as one sample can have
        many rows, which means that dictionary items can be overwritten
        """
        if isinstance(df, type(None)):
            df = self.df
        if lst_or_dict == "lst":
            return list(df.T.apply(dict))
        else:
            return {str(i[df.index.name]): dict(i) for i in list(df.T.apply(dict))}

    def get_name(self, col_name, df_slice="", index_names=""):
        """
        Takes in a column name, and either a DataFrame slice or
        a list of index_names to slice self.df using fancy indexing.
        Then return the value for that column in the relevant slice.
        (Assumes that all values for column will be the same in the
         chosen slice, so return the first one.)
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
        Optional arguments:
        Provide tilt_corr (default 100).
        Excl is a list of method codes to exclude.
        Output dec/inc from the slice in this format:
        [[dec1, inc1], [dec2, inc2], ...].
        Not inplace
        """
        tilt_corr = int(tilt_corr)
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
        if tilt_corr != 0:
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
        (i.e., "DE-").
        Not inplace
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


    ## Combining multiple DataFrames

    def merge_dfs(self, df1, replace_dir_or_int):
        """
        Description: takes new calculated directional, intensity data, or both and replaces the corresponding data in self.df with the new input data preserving any data that is not replaced.

        @param: df1 - first DataFrame whose data will preferentially be used.
        @param: replace_dir_or_int - must be string 'dir', 'int', or 'full' and acts as a flag to tell the funciton weather to replace directional, intensity data, or just everything in current table. If there is not enough data in the current table to split by dir or int the two dfs will be fully merged (Note: if you are dealing with tables other than specimens.txt you should likely use full as that is the only table the other options have been tested on)
        """

        if self.df.empty: return df1
        elif df1.empty: return self.df

        #copy to prevent mutation
        cdf2 = self.df.copy()

        #split data into types and decide which to replace
        if replace_dir_or_int == 'dir' and 'method_codes' in cdf2.columns:
            cdf2 = cdf2[cdf2['method_codes'].notnull()]
            acdf2 = cdf2[cdf2['method_codes'].str.contains('LP-PI')]
            mcdf2 = cdf2[cdf2['method_codes'].str.contains('LP-DIR')]
        elif replace_dir_or_int == 'int' and 'method_codes' in cdf2.columns:
            cdf2 = cdf2[cdf2['method_codes'].notnull()]
            mcdf2 = cdf2[cdf2['method_codes'].str.contains('LP-PI')]
            acdf2 = cdf2[cdf2['method_codes'].str.contains('LP-DIR')]
        else:
            mcdf2 = cdf2
            acdf2 = pd.DataFrame(columns=mcdf2.columns)

        #get rid of stupid duplicates
        [mcdf2.drop(cx,inplace=True,axis=1) for cx in mcdf2.columns if cx in df1.columns]

        #join the new calculated data with the old data of same type
        if self.dtype.endswith('s'): dtype = self.dtype[:-1]
        else: dtype = self.dtype
        mdf = df1.join(mcdf2, how='left', rsuffix='_remove', on=dtype)
        #drop duplicate columns if they are created
        [mdf.drop(col,inplace=True,axis=1) for col in mdf.columns if col.endswith("_remove")]
        #duplicates rows for some freaking reason
        mdf.drop_duplicates(inplace=True,subset=[col for col in mdf.columns if col != 'description'])
        #merge the data of the other type with the new data
        mdf = mdf.merge(acdf2, how='outer')
        if dtype in mdf.columns:
            #fix freaking indecies because pandas
            mdf = mdf.set_index(dtype)
            #really? I wanted the index changed not a column deleted?!?
            mdf[dtype] = mdf.index
            mdf.sort_index(inplace=True)

        return mdf


    ## Methods for writing self.df out to tab-delimited file

    def write_magic_file(self, custom_name=None, dir_path=".", append=False):
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
        # if indexing column was put in, remove it
        if "num" in self.df.columns:
            self.df.drop("num", axis=1, inplace=True)
        dir_path = os.path.realpath(dir_path)
        if custom_name:
            fname = os.path.join(dir_path, custom_name)
        else:
            fname = os.path.join(dir_path, self.dtype + ".txt")
        # add to existing file
        if append:
            print '-I- appending {} data to {}'.format(self.dtype, fname)
            mode = "a"
        # overwrite existing file
        elif os.path.exists(fname):
            print '-I- overwriting {}'.format(fname)
            mode = "w"
        # or create new file
        else:
            print '-I- writing {} data to {}'.format(self.dtype, fname)
            mode = "w"
        f = open(fname, mode)
        f.write('tab\t{}\n'.format(self.dtype))
        df.to_csv(f, sep="\t", header=True, index=False)
        f.close()




if __name__ == "__main__":
    pass
