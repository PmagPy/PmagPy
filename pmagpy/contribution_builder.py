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
import math
import numpy as np
import pandas as pd
from pandas import DataFrame
# from pmagpy import pmag
from pmagpy import data_model3 as data_model
from pmagpy import controlled_vocabularies3 as cv
from pmagpy import pmag


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
            typ = self.add_magic_table('unknown', single_file)[0]
            self.filenames[typ] = single_file
        # read in data for all required tables
        for name in read_tables:
            if name not in self.tables:
                self.add_magic_table(name, fname=self.filenames[name])

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
            print("-W- {} is not a valid MagIC table name".format(dtype))
            print("-I- Valid table names are: {}".format(", ".join(self.table_names)))
            return
        data_container = MagicDataFrame(dtype=dtype, columns=col_names, groups=groups)
        self.tables[dtype] = data_container

    def add_magic_table_from_data(self, dtype, data):
        """
        Add a MagIC table to the contribution from a data list

        Parameters
        ----------
        dtype : str
            MagIC table type, i.e. 'specimens'
        data : list of dicts
            data list with format [{'key1': 'val1', ...}, {'key1': 'val2', ...}, ... }]
        """
        self.tables[dtype] = MagicDataFrame(dtype=dtype, data=data)
        if dtype == 'measurements':
            self.tables['measurements'].add_sequence()
        return dtype, self.tables[dtype]


    def add_magic_table(self, dtype, fname=None, df=None):
        """
        Read in a new file to add a table to self.tables.
        Requires dtype argument and EITHER filename or df.

        Parameters
        ----------
        dtype : str
            MagIC table name (plural, i.e. 'specimens')
        fname : str
            filename of MagIC format file
            (short path, directory is self.directory)
            default: None
        df : pandas DataFrame
            data to create the new table with
            default: None
        """
        if df is None:
            # if providing a filename but no data type
            if dtype == "unknown":
                filename = os.path.join(self.directory, fname)
                data_container = MagicDataFrame(filename, dmodel=self.data_model)
                dtype = data_container.dtype
                if dtype == 'empty':
                    return False, False
                else:
                    self.tables[dtype] = data_container
                    return dtype, data_container
            # if providing a data type, use the canonical filename
            elif dtype not in self.filenames:
                print('-W- "{}" is not a valid MagIC table type'.format(dtype))
                print("-I- Available table types are: {}".format(", ".join(self.table_names)))
                return False, False
            #filename = os.path.join(self.directory, self.filenames[dtype])
            filename = pmag.resolve_file_name(self.filenames[dtype], self.directory)
            if os.path.exists(filename):
                data_container = MagicDataFrame(filename, dtype=dtype,
                                                dmodel=self.data_model)
                if data_container.dtype != "empty":
                    self.tables[dtype] = data_container
                    return dtype, data_container
                else:
                    return False, False
            else:
                #print("-W- No such file: {}".format(filename))
                return False, False
        # df is not None
        else:
            if not dtype:
                print("-W- Must provide dtype")
                return False, False
            data_container = MagicDataFrame(dtype=dtype, df=df)
            self.tables[dtype] = data_container
        self.tables[dtype].sort_dataframe_cols()
        return dtype, self.tables[dtype]


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
                items = meas_df[name].unique()
                df = pd.DataFrame(columns=[name], index=items)
                df[name] = df.index
                # add in parent name if possible
                # (i.e., sample name to specimens table)
                if num < (len(names_list) - 1):
                    parent = names_list[num+1]
                    if parent in meas_df.columns:
                        meas_df = meas_df.where(meas_df.notnull(), "")
                        df[parent] = meas_df.drop_duplicates(subset=[name])[parent].values.astype(str)
                df = df.where(df != "", np.nan)
                df = df.dropna(how='all', axis='rows')
                if len(df):
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
                    parents = sorted(set(df[parent_name[:-1]].dropna().values.astype(str)))
                    if parent_name in self.tables: # if there is a parent table, update it
                        parent_df = self.tables[parent_name].df
                        missing_parents = set(parents) - set(parent_df.index)
                        if missing_parents: # add any missing values
                            print("-I- Updating {} table with values from {} table".format(parent_name, table_name))
                            for item in missing_parents:
                                self.add_item(parent_name, {parent_name[:-1]: item}, label=item)
                            # save any changes to file
                            if write:
                                self.write_table_to_file(parent_name)

                    else:  # if there is no parent table, create it if necessary
                        if parents:
                            # create a parent_df with the names you got from the child
                            print("-I- Creating new {} table with data from {} table".format(parent_name, table_name))
                            # add in the grandparent if available
                            grandparent_name = self.get_parent_and_child(parent_name)[0]
                            if grandparent_name:
                                grandparent = ""
                                if grandparent_name in df.columns:
                                    grandparent = df[df[parent_name] == item][grandparent_name].values[0]
                                columns = [parent_name[:-1]]#, grandparent_name[:-1]]
                            else:
                                columns = [parent_name[:-1]]

                            parent_df = pd.DataFrame(columns=columns, index=parents)
                            parent_df[parent_name[:-1]] = parent_df.index
                            if grandparent_name:
                                if grandparent_name[:-1] in df.columns:
                                    parent_df = pd.merge(df[[parent_name[:-1], grandparent_name[:-1]]], parent_df, on=parent_name[:-1])
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
                    for parent, children in raw_children.items():
                        for child in children:
                            # remove whitespace
                            child = child.strip()
                            old_parent = parent_of_child.get(child)
                            if old_parent and parent and (old_parent != parent):
                                print('-I- for {} {}, replacing: {} with: {}'.format(child_name[:-1], child,
                                                                                     old_parent, parent))
                            parent_of_child[child] = parent
                    # old way:
                    # flatten list, ignore duplicates
                    #children = sorted(set([item.strip() for sublist in raw_children for item in sublist]))
                    if child_name in self.tables: # if there is already a child table, update it
                        child_df = self.tables[child_name].df
                        missing_children = set(parent_of_child.keys()) - set(child_df.index)
                        if missing_children: # add any missing values
                            print("-I- Updating {} table with values from {} table".format(child_name, table_name))
                            for item in missing_children:
                                data = {child_name[:-1]: item, table_name[:-1]: parent_of_child[item]}
                                self.add_item(child_name, data, label=item)
                            if write:
                                # save any changes to file
                                self.write_table_to_file(child_name)
                    else: # if there is no child table, create it if necessary
                        if children:
                            # create a child_df with the names you got from the parent
                            print("-I- Creating new {} table with data from {} table".format(child_name, table_name))
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
        try:
            site_container.df['lat'] = site_container.df['lat'].astype(float)
        except ValueError as ex:
            print('-W- Improperly formatted numbers in sites.lat')
            return
        try:
            site_container.df['lon'] = site_container.df['lon'].astype(float)
        except ValueError as ex:
            print('-W- Improperly formatted numbers in sites.lon')
            return
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
                    if is_null(new_value, zero_as_null=False):
                        continue
                    # set old value to None if it wasn't in table
                    if coord not in loc_container.df.columns:
                        loc_container.df[coord] = None
                    old_value = loc_container.df.loc[loc_name, coord]
                    # use first value if multiple values returned, but don't shorten a string
                    if not (isinstance(old_value, str)):
                        try:
                            old_value = old_value.values.astype(str)[0]
                        except (TypeError,IndexError,AttributeError) as e: # if only one value, or np.nan, or NoneType
                            pass
                    if is_null(old_value, zero_as_null=False):
                        pass
                    elif isinstance(old_value, str):
                        try:
                            old_value = float(old_value)
                        except ValueError:
                            print('-W- In {}, automatically generated {} value ({}) will overwrite previous value ({})'.format(loc_name, coord, new_value, old_value))
                            old_value = None
                    elif not math.isclose(new_value, old_value):
                        print('-W- In {}, automatically generated {} value ({}) will overwrite previous value ({})'.format(loc_name, coord, new_value, old_value))
                    # set new value
                    new_value = round(float(new_value), 5)
                    loc_container.df.loc[loc_name, coord] = new_value
        self.write_table_to_file('locations')
        return locs

    def propagate_lithology_cols(self):
        """
        Propagate any data from lithologies, geologic_types, or geologic_classes
        from the sites table to the samples and specimens table.
        In the samples/specimens tables, null or "Not Specified" values
        will be overwritten based on the data from their parent site.
        """
        cols = ['lithologies', 'geologic_types', 'geologic_classes']
        #for table in ['specimens', 'samples']:
            # convert "Not Specified" to blank
            #self.tables[table].df.replace("^[Nn]ot [Ss]pecified", '',
            #                              regex=True, inplace=True)
        self.propagate_cols(cols, 'samples', 'sites')
        cols = ['lithologies', 'geologic_types', 'geologic_classes']
        self.propagate_cols(cols, 'specimens', 'samples')
        # if sites table is missing any values,
        # go ahead and propagate values UP as well
        if 'sites' not in self.tables:
            return
        for col in cols:
            if col not in self.tables['sites'].df.columns:
                self.tables['sites'].df[col] = None
        if not all(self.tables['sites'].df[cols].values.ravel()):
            print('-I- Propagating values up from samples to sites...')
            self.propagate_cols_up(cols, 'sites', 'samples')

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
                df.loc[count, col_name] = names_list
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


    def propagate_location_to_measurements(self):
        """
        Propagate all names from location down to measurements.
        --------
        Returns: measurements MagicDataFrame
        """
        self.propagate_name_down('sample', 'measurements')
        self.propagate_name_down('site', 'measurements')
        return self.propagate_name_down('location', 'measurements')

    def propagate_location_to_specimens(self):
        self.propagate_name_down('site', 'specimens')
        return self.propagate_name_down('location', 'specimens')

    def propagate_location_to_samples(self):
        """
        Propagate all names from location down to samples.
        --------
        Returns: samples MagicDataFrame
        """
        return self.propagate_name_down('location', 'samples')

    def propagate_name_down(self, col_name, df_name):
        """
        Put the data for "col_name" into dataframe with df_name
        Used to add 'site_name' to specimen table, for example.
        """
        if df_name not in self.tables:
            table = self.add_magic_table(df_name)[1]
            if is_null(table):
                return
        df = self.tables[df_name].df
        if col_name in df.columns:
            if all(df[col_name].apply(not_null)):
                #print('{} already in {}'.format(col_name, df_name))
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
                result = self.add_magic_table(bottom_table_name)[1]
                if not isinstance(result, MagicDataFrame):
                    print("-W- Couldn't read in {} data for data propagation".format(bottom_table_name))
                    return df
            # add child_name to df
            add_df = self.tables[bottom_table_name].df
            # drop duplicate names
            add_df = add_df.drop_duplicates(subset=bottom_name)
            if child_name not in df.columns:
                print("-W- Cannot complete propagation, {} table is missing {} column".format(df_name, child_name))
            else:
                add_df = stringify_col(add_df, child_name)
                df = stringify_col(df, bottom_name)
                df = df.merge(add_df[[child_name]],
                              left_on=[bottom_name],
                              right_index=True, how="left")
                self.tables[df_name].df = df

        # merge in one level above
        if parent_name not in df.columns:
            # add parent_table if missing
            if child_table_name not in self.tables:
                result = self.add_magic_table(child_table_name)[1]
                if not isinstance(result, MagicDataFrame):
                    print("-W- Couldn't read in {} data".format(child_table_name))
                    print("-I- Make sure you've provided the correct file name")
                    return df
            # add parent_name to df
            add_df = self.tables[child_table_name].df
            # drop duplicate names
            add_df = add_df.drop_duplicates(subset=child_name)
            if parent_name not in add_df:
                print('-W- could not finish propagating names: {} table is missing {} column'.format(child_table_name, parent_name))
            elif parent_name not in df:
                print('-W- could not finish propagating names: {} table is missing {} column'.format(df_name, parent_name))
            else:
                add_df = stringify_col(add_df, parent_name)
                df = stringify_col(df, child_name)
                df = df.merge(add_df[[parent_name]],
                              left_on=[child_name],
                              right_index=True, how="left")
                self.tables[df_name].df = df

        # merge in two levels above
        if grandparent_name not in df.columns:
            # add grandparent table if it is missing
            if parent_table_name not in self.tables:
                result = self.add_magic_table(parent_table_name)[1]
                if not isinstance(result, MagicDataFrame):
                    print("-W- Couldn't read in {} data".format(parent_table_name))
                    print("-I- Make sure you've provided the correct file name")
                    return df
            # add grandparent name to df
            add_df = self.tables[parent_table_name].df
            # drop duplicate names
            add_df = add_df.drop_duplicates(subset=parent_name)
            if grandparent_name not in add_df.columns:
                print('-W- could not finish propagating names: {} table is missing {} column'.format(parent_table_name, grandparent_name))
            elif parent_name not in df.columns:
                print('-W- could not finish propagating names: {} table is missing {} column'.format(df_name, parent_name))
            else:
                add_df = stringify_col(add_df, grandparent_name)
                df = stringify_col(df, parent_name)
                df = df.merge(add_df[[grandparent_name]],
                              left_on=[parent_name],
                              right_index=True, how="left")
                df = stringify_col(df, grandparent_name)
        # update the Contribution
        self.tables[df_name].df = df
        return df

    def propagate_cols(self, col_names, target_df_name, source_df_name,
                       down=True):
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
            print("-W- Couldn't read in {} table".format(target_df_name))
            return
        # make sure source table is read in
        if source_df_name not in self.tables:
            self.add_magic_table(source_df_name)
            print("-W- Couldn't read in {} table".format(source_df_name))
            return
        # make sure col_names are all available in source table
        source_df = self.tables[source_df_name].df
        if not set(col_names).issubset(source_df.columns):
            for col in col_names[:]:
                if col not in source_df.columns:
                    print("-W- Column '{}' isn't in {} table, skipping it".format(col, source_df_name))
                    col_names.remove(col)
        if not col_names:
            print("-W- Invalid or missing column names, could not propagate columns")
            return
        #
        if down:
            add_name = source_df_name[:-1]
            if 'measurements' in self.tables.keys():
                self.propagate_location_to_measurements()
            elif 'specimens' in self.tables.keys():
                self.propagate_location_to_specimens()
            else:
                self.propagate_name_down('location', 'sites')
        else:
            add_name = target_df_name[:-1]

        # get dataframes for merge
        target_df = self.tables[target_df_name].df
        source_df = self.tables[source_df_name].df
        backup_source_df = source_df.copy()
        # finesse source_df to make sure it has all the right columns
        # and no unnecessary duplicates
        if source_df_name[:-1] not in source_df.columns:
            source_df[source_df_name[:-1]] = source_df.index
        source_df = source_df.drop_duplicates(inplace=False, subset=col_names + [source_df_name[:-1]])
        source_df = source_df.groupby(source_df.index, sort=False).fillna(method='ffill')
        source_df = source_df.groupby(source_df.index, sort=False).fillna(method='bfill')
        # if the groupby/fillna operation fails due to pandas bug, do the same by hand:
        if not len(source_df):
            new = []
            grouped = backup_source_df.groupby(backup_source_df.index)
            for label, group in grouped:
                new_group = group.fillna(method="ffill")
                new_group = new_group.fillna(method="bfill")
                new.append(new_group)
            source_df = pd.concat(new, sort=True)

        # if the groupby/fillna still doesn't work, we are out of luck
        if not len(source_df):
            return target_df
        # propagate down
        if down:
            # do merge
            target_df = target_df.merge(source_df[col_names], how='left',
                                        left_on=add_name, right_index=True,
                                        suffixes=["_target", "_source"])
        # propagate up
        else:
            # do merge
            col_names.append(add_name)
            target_df = target_df.merge(source_df[col_names],
                                        how='left', left_index=True,
                                        right_on=add_name,
                                        suffixes=['_target', '_source'])
            target_df.index = target_df[add_name]
            target_df.drop([add_name + "_source", add_name + "_target"], axis=1, inplace=True)

        # ignore any duplicate rows
        target_df.drop_duplicates(inplace=True)
        # mess with target_df to remove un-needed merge columns
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

        # drop any duplicate rows
        target_df.drop_duplicates(inplace=True)
        self.tables[target_df_name].df = target_df
        return target_df

    def propagate_cols_up(self, cols, target_df_name, source_df_name):
        """
        Take values from source table, compile them into a colon-delimited list,
        and apply them to the target table.
        This method won't overwrite values in the target table, it will only
        supply values where they are missing.

        Parameters
        ----------
        cols : list-like
            list of columns to propagate
        target_df_name : str
            name of table to propagate values into
        source_df_name:
            name of table to propagate values from

        Returns
        ---------
        target_df : MagicDataFrame
            updated MagicDataFrame with propagated values
        """
        print("-I- Trying to propagate {} columns from {} table into {} table".format(cols,
                                                                                      source_df_name,
                                                                                      target_df_name))
        # make sure target table is read in
        if target_df_name not in self.tables:
            self.add_magic_table(target_df_name)
        if target_df_name not in self.tables:
            print("-W- Couldn't read in {} table".format(target_df_name))
            return
        # make sure source table is read in
        if source_df_name not in self.tables:
            self.add_magic_table(source_df_name)
            print("-W- Couldn't read in {} table".format(source_df_name))
            return
        target_df = self.tables[target_df_name]
        source_df = self.tables[source_df_name]
        target_name = target_df_name[:-1]
        # make sure source_df has relevant columns
        for col in cols:
            if col not in source_df.df.columns:
                source_df.df[col] = None
        # if target_df has info, propagate that into all rows
        target_df.front_and_backfill(cols)
        # make sure target_name is in source_df for merging
        if target_name not in source_df.df.columns:
            print("-W- You can't merge data from {} table into {} table".format(source_df_name, target_df_name))
            print("    Your {} table is missing {} column".format(source_df_name, target_name))
            self.tables[target_df_name] = target_df
            return target_df
        source_df.front_and_backfill([target_name])
        # group source df by target_name
        grouped = source_df.df.groupby(source_df.df[target_name])
        if not len(grouped):
            print("-W- Couldn't propagate from {} to {}".format(source_df_name, target_df_name))
            return target_df
        # function to generate capitalized, sorted, colon-delimited list
        # of unique, non-null values from a column
        def func(group, col_name):
            lst = group[col_name][group[col_name].notnull()].unique()
            split_lst = [col.split(':') for col in lst if col]
            sorted_lst = sorted(np.unique([item.capitalize() for sublist in split_lst for item in sublist]))
            group_col = ":".join(sorted_lst)
            return group_col
        # apply func to each column
        for col in cols:
            res = grouped.apply(func, col)
            target_df.df['new_' + col] = res
            target_df.df[col] = np.where(target_df.df[col], target_df.df[col], target_df.df['new_' + col])
            target_df.df.drop(['new_' + col], axis='columns', inplace=True)
        # set table
        self.tables[target_df_name] = target_df
        return target_df

    def propagate_average_up(self, cols=['lat', 'lon'],
                             target_df_name='sites', source_df_name='samples'):
        """
        Propagate average values from a lower table to a higher one.
        For example, propagate average lats/lons from samples to sites.
        Pre-existing values will not be overwritten.

        Parameters
        ----------
        cols : list-like
            list of columns to propagate
        target_df_name : str
            name of table to propagate values into
        source_df_name:
            name of table to propagate values from

        Returns
        ---------
        target_df : MagicDataFrame or None
            returns table with propagated data,
            or None if no propagation could be done
        """
        # make sure target/source table are appropriate
        target_ind = self.ancestry.index(target_df_name)
        source_ind = self.ancestry.index(source_df_name)
        if target_ind - source_ind != 1:
            print('-W- propagate_average_up only works with tables that are spaced one apart, i.e. sites and samples.')
            print('    Source table must be lower in the hierarchy than the target table.')
            print('    You have provided "{}" as the target table and "{}" as the source table.'.format(target_df_name, source_df_name))
            return None
        # make sure target table is read in
        if target_df_name not in self.tables:
            self.add_magic_table(target_df_name)
        if target_df_name not in self.tables:
            print("-W- Couldn't read in {} table".format(target_df_name))
            return
        # make sure source table is read in
        if source_df_name not in self.tables:
            self.add_magic_table(source_df_name)
        if source_df_name not in self.tables:
            print("-W- Couldn't read in {} table".format(source_df_name))
            return
        # get tables
        target_df = self.tables[target_df_name]
        source_df = self.tables[source_df_name]
        target_name = target_df_name[:-1]
        # step 1: make sure columns exist in target_df
        for col in cols:
            if col not in target_df.df.columns:
                target_df.df[col] = None
        # step 2: propagate target_df columns forward & back
        target_df.front_and_backfill(cols)
        # step 3: see if any column values are missing
        values = [not_null(val) for val in target_df.df[cols].values.ravel()]
        if all(values):
            print('-I- {} table already has {} filled column(s)'.format(target_df_name, cols))
            self.tables[target_df_name] = target_df
            return target_df
        # step 4: make sure columns are in source table, also target name
        if target_name not in source_df.df.columns:
            print("-W- can't propagate from {} to {} table".format(source_df_name, target_df_name))
            print("    Missing {} column in {} table".format(target_name, source_df_name))
            self.tables[target_df_name] = target_df
            return target_df
        for col in cols:
            if col not in target_df.df.columns:
                target_df.df[col] = None
        # step 5: if needed, average from source table and apply to target table
        for col in cols:
            if col not in source_df.df.columns:
                source_df.df[col] = np.nan
            else:
                # make sure is numeric
                source_df.df[col] = pd.to_numeric(source_df.df[col], errors='coerce')
        grouped = source_df.df[cols + [target_name]].groupby(target_name)
        grouped = grouped[cols].apply(np.mean)
        for col in cols:
            target_df.df['new_' + col] = grouped[col]
            # use custom not_null
            mask = [not_null(val) for val in target_df.df[col]]
            target_df.df[col] = np.where(mask, #target_df.df[col].notnull(),
                                         target_df.df[col],
                                         target_df.df['new_' + col])
            target_df.df.drop(['new_' + col], inplace=True, axis=1)
            # round column to 5 decimal points
            try:
                target_df.df[col] = target_df.df[col].astype(float)
                target_df.df = target_df.df.round({col: 5})
            except ValueError: # if there are sneaky strings...
                pass
        self.tables[target_df_name] = target_df
        return target_df

    def propagate_min_max_up(self, cols=['age'],
                             target_df_name='locations',
                             source_df_name='sites',
                             min_suffix='low',
                             max_suffix='high'):
        """
        Take minimum/maximum values for a set of columns in source_df,
        and apply them to the target table.
        This method won't overwrite values in the target table, it will only
        supply values where they are missing.

        Parameters
        ----------
        cols : list-like
            list of columns to propagate, default ['age']
        target_df_name : str
            name of table to propagate values into, default 'locations'
        source_df_name:
            name of table to propagate values from, default 'sites'
        min_suffix : str
            suffix for minimum value, default 'low'
        max_suffix : str
            suffix for maximum value, default 'high'

        Returns
        ---------
        target_df : MagicDataFrame
            updated MagicDataFrame with propagated values
        """
        # make sure target/source table are appropriate
        target_ind = self.ancestry.index(target_df_name)
        source_ind = self.ancestry.index(source_df_name)
        if target_ind - source_ind != 1:
            print('-W- propagate_min_max_up only works with tables that are spaced one apart, i.e. sites and samples.')
            print('    Source table must be lower in the hierarchy than the target table.')
            print('    You have provided "{}" as the target table and "{}" as the source table.'.format(target_df_name, source_df_name))
            return None
        # make sure target table is read in
        if target_df_name not in self.tables:
            self.add_magic_table(target_df_name)
        if target_df_name not in self.tables:
            print("-W- Couldn't read in {} table".format(target_df_name))
            return
        # make sure source table is read in
        if source_df_name not in self.tables:
            self.add_magic_table(source_df_name)
        if source_df_name not in self.tables:
            print("-W- Couldn't read in {} table".format(source_df_name))
            return
        # get tables
        target_df = self.tables[target_df_name]
        source_df = self.tables[source_df_name]
        target_name = target_df_name[:-1]
        # find and propagate min/max for each col in cols
        for col in cols:
            if col not in source_df.df.columns:
                print('-W- {} table is missing "{}" column, skipping'.format(source_df_name, col))
                continue
            min_col = col + "_" + min_suffix
            max_col = col + "_" + max_suffix
            # add min/max cols to target_df if missing
            if min_col not in target_df.df.columns:
                target_df.df[min_col] = None
            if max_col not in target_df.df.columns:
                target_df.df[max_col] = None
            # get min/max from source
            if target_name not in source_df.df.columns:
                print('-W- {} table missing {} column, cannot propagate age info'.format(target_name, source_df_name))
                return
            # make sure source is appropriately filled
            source = source_df.front_and_backfill([col], inplace=False)
            # add target_name back into front/backfilled source
            source[target_name] = source_df.df[target_name]
            grouped = source[[col, target_name]].groupby(target_name)
            if len(grouped):
                minimum, maximum = grouped.min(), grouped.max()
                minimum = minimum.reindex(target_df.df.index)
                maximum = maximum.reindex(target_df.df.index)
                # update target_df without overwriting existing values
                cond_min = target_df.df[min_col].apply(not_null)
                cond_max = target_df.df[max_col].apply(not_null)
                #
                target_df.df[min_col] = np.where(cond_min,
                                                 target_df.df[min_col],
                                                 minimum[col])
                target_df.df[max_col] = np.where(cond_max,
                                                 target_df.df[max_col],
                                                 maximum[col])
        # update contribution
        self.tables[target_df_name] = target_df
        return target_df

    def get_age_levels(self):
        """
        Method to add a "level" column to the ages table.
        Finds the lowest filled in level (i.e., specimen, sample, etc.)
        for that particular row.
        I.e., a row with both site and sample name filled in is considered
        a sample-level age.

        Returns
        ---------
        self.tables['ages'] : MagicDataFrame
            updated ages table
        """
        def get_level(ser, levels=('specimen', 'sample', 'site', 'location')):
            for level in levels:
                if pd.notnull(ser[level]):
                    if len(ser[level]):  # guard against empty strings
                        return level
            return
        # get available levels in age table
        possible_levels = ['specimen', 'sample', 'site', 'location']
        levels = [level for level in possible_levels if level in self.tables['ages'].df.columns]
        # find level for each age row
        age_levels = self.tables['ages'].df.apply(get_level, axis=1, args=[levels])
        if any(age_levels):
            self.tables['ages'].df.loc[:, 'level'] = age_levels
        return self.tables['ages']

    def propagate_ages(self):
        """
        Mine ages table for any age data, and write it into
        specimens, samples, sites, locations tables.
        Do not overwrite existing age data.
        """
        # if there is no age table, skip
        if 'ages' not in self.tables:
            return
        # if age table has no data, skip
        if not len(self.tables['ages'].df):
            return
        # get levels in age table
        self.get_age_levels()
        # if age levels could not be determined, skip
        if not "level" in self.tables["ages"].df.columns:
            return
        if not any(self.tables["ages"].df["level"]):
            return
        # go through each level of age data
        for level in self.tables['ages'].df['level'].unique():
            table_name = level + 's'
            age_headers = self.data_model.get_group_headers(table_name, 'Age')
            # find age headers that are actually in table
            actual_age_headers = list(set(self.tables[table_name].df.columns).intersection(age_headers))
            # find site age headers that are available in ages table
            available_age_headers = list(set(self.tables['ages'].df.columns).intersection(age_headers))
            # fill in all available age info to all rows
            self.tables[table_name].front_and_backfill(actual_age_headers)
            # add any available headers to table
            add_headers = set(available_age_headers).difference(actual_age_headers)
            for header in add_headers:
                self.tables[table_name].df[header] = None
            # propagate values from ages into table
            def move_values(ser, level, available_headers):
                name = ser.name
                cond1 = self.tables['ages'].df[level] == name
                cond2 = self.tables['ages'].df['level'] == level
                mask = cond1 & cond2
                sli = self.tables['ages'].df[mask]
                if len(sli):
                    return list(sli[available_headers].values[0])
                return [None] * len(available_headers)

            res = self.tables[table_name].df.apply(move_values, axis=1,
                                                   args=[level, available_age_headers])
            # fill in table with values gleaned from ages
            new_df = pd.DataFrame(data=list(res.values), index=res.index,
                                  columns=available_age_headers)
            age_values = np.where(self.tables[table_name].df[available_age_headers],
                                  self.tables[table_name].df[available_age_headers],
                                  new_df)
            self.tables[table_name].df[available_age_headers] = age_values
        #
        # put age_high, age_low into locations table
        print("-I- Adding age_high and age_low to locations table based on minimum/maximum ages found in sites table")
        self.propagate_min_max_up(cols=['age'], target_df_name='locations',
                                  source_df_name='sites')

    ## Methods for outputting tables

    def remove_non_magic_cols(self):
        """
        Remove all non-MagIC columns from all tables.
        """
        for table_name in self.tables:
            table = self.tables[table_name]
            table.remove_non_magic_cols_from_table()

    def write_table_to_file(self, dtype, custom_name=None, append=False, dir_path=None):
        """
        Write out a MagIC table to file, using custom filename
        as specified in self.filenames.

        Parameters
        ----------
        dtype : str
            magic table name
        """
        if custom_name:
            fname = custom_name
        else:
            fname = self.filenames[dtype]
        if not dir_path:
            dir_path=self.directory
        if dtype in self.tables:
            write_df = self.remove_names(dtype)
            outfile = self.tables[dtype].write_magic_file(custom_name=fname,
                                                          dir_path=dir_path,
                                                          append=append, df=write_df)
        return outfile

    def remove_names(self, dtype):
        """
        Remove unneeded name columns ('specimen'/'sample'/etc)
        from the specified table.

        Parameters
        ----------
        dtype : str

        Returns
        ---------
        pandas DataFrame without the unneeded columns

        Example
        ---------
        Contribution.tables['specimens'].df = Contribution.remove_names('specimens')
        # takes out 'location', 'site', and/or 'sample' columns from the
        # specimens dataframe if those columns have been added
        """
        if dtype not in self.ancestry:
            return
        if dtype in self.tables:
            # remove extra columns here
            self_ind = self.ancestry.index(dtype)
            parent_ind = self_ind + 1 if self_ind < (len(self.ancestry) -1) else self_ind
            remove = set(self.ancestry).difference([self.ancestry[self_ind], self.ancestry[parent_ind]])
            remove = [dtype[:-1] for dtype in remove]
            columns = self.tables[dtype].df.columns.difference(remove)
            return self.tables[dtype].df[columns]


    ## Methods for validating contributions

    def find_missing_items(self, dtype):
        """
        Find any items that are referenced in a child table
        but are missing in their own table.
        For example, a site that is listed in the samples table,
        but has no entry in the sites table.

        Parameters
        ----------
        dtype : str
            table name, e.g. 'specimens'

        Returns
        ---------
        set of missing values
        """
        parent_dtype, child_dtype = self.get_parent_and_child(dtype)
        if not child_dtype in self.tables:
            return set()
        items = set(self.tables[dtype].df.index.unique())
        items_in_child_table = set(self.tables[child_dtype].df[dtype[:-1]].unique())
        return {i for i in (items_in_child_table - items) if not_null(i)}



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
        provided_dtype = dtype
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

        # get singular and plural dtype
        if dtype and magic_file:
            name, self.dtype = self.get_singular_and_plural_dtype(dtype)

        # create MagicDataFrame using a DataFrame and a dtype:
        if isinstance(df, pd.DataFrame):
            self.df = df
            #if dtype == 'ages':
            #    pass
            if dtype:
                name, self.dtype = self.get_singular_and_plural_dtype(dtype)
                if name in self.df.columns:
                    self.df.index = self.df[name]
            else:
                print('-W- Please provide data type...')

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
                print("-W- To make a MagicDataFrame from data, you must provide a datatype")
                self.df = None
                return

        # if user has not provided a filename, they must provide a dtype and either a df/data
        # warn them and return
        if not magic_file and not dtype and not isinstance(df, pd.DataFrame):
            print("-W- To make a MagicDataFrame, you must provide either a filename or a datatype")
            self.df = None
            return

        # create MagicDataFrame using a DataFrame and a dtype
        if isinstance(df, pd.DataFrame):
            self.df = df
            if provided_dtype:
                name, self.dtype = self.get_singular_and_plural_dtype(provided_dtype)
            elif dtype:
                name, self.dtype = self.get_singular_and_plural_dtype(provided_dtype)
                if name in self.df.columns:
                    self.df.index = self.df[name]
            else:
                print('-W- Please provide data type...')

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
                print("-W- To make a MagicDataFrame from data, you must provide a datatype")
                self.df = None
                return

        # if user has not provided a filename, they must provide a dtype and either a df/data
        # warn them and return
        if not magic_file and not dtype and not isinstance(df, pd.DataFrame):
            print("-W- To make a MagicDataFrame, you must provide either a filename or a datatype")
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
            self.df.index.name = name + " name"
        # if there is a file provided, read in the data and ascertain dtype
        else:
            with open(magic_file) as f:
                try:
                    delim, dtype = f.readline().split('\t')[:2]
                except ValueError as ex:
                    print(ex, type(ex))
                    print("-W- Empty file {}".format(magic_file))
                    self.dtype = 'empty'
                    self.df = DataFrame()
                    return
            # get singular name and plural datatype
            name, self.dtype = self.get_singular_and_plural_dtype(dtype)
            self.df = pd.read_table(magic_file, skiprows=[0],
                                    low_memory=False)#, dtype={name: str})
            # make sure names are strings (sometimes could be numbers)


            # drop all blank rows
            self.df = self.df.dropna(how='all', axis=0)
            #
            if self.dtype == 'measurements':
                self.add_measurement_names()
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
        elif name == 'measurement' and len(self.df):
            self.add_measurement_names()
        self.name = name
        self.df.index.name = name + ' name'



    ## Methods to change self.df inplace

    def remove_non_magic_cols_from_table(self, ignore_cols=()):
        """
        Remove all non-magic columns from self.df.
        Changes in place.

        Parameters
        ----------
        ignore_cols : list-like
            columns not to remove, whether they are proper
            MagIC columns or not

        Returns
        ---------
        unrecognized_cols : list
            any columns that were removed
        """
        unrecognized_cols = self.get_non_magic_cols()
        for col in ignore_cols:
            if col in unrecognized_cols:
                unrecognized_cols.remove(col)
        if unrecognized_cols:
            print('-I- Removing non-MagIC column names from {}:'.format(self.dtype), end=' ')
            for col in unrecognized_cols:
                self.df.drop(col, axis='columns', inplace=True)
                print(col, end=' ')
            print("\n")
        return unrecognized_cols


    def add_measurement_names(self):
        # first add sequence column
        if 'sequence' not in self.df.columns:
            self.df['sequence'] = range(1, len(self.df) + 1)
        # then, see if measurement is already present
        if 'measurement' in self.df.columns:
            return
        # if measurement column is missing, try to add it
        if 'number' in self.df.columns:
            self.df.rename(columns={'number':'treat_step_num'}, inplace=True)
        if 'treat_step_num' not in self.df.columns:
            print("-W- You are missing the 'treat_step_num' column in your measurements file")
            print("    This may cause strange behavior in the analysis GUIs")
            self.df['treat_step_num'] = ''
        treat_step = lambda x: str(x) if not_null(x) else ""
        if 'measurement' in self.df.columns:
            print('measurement already in self.df.columns!')
        else:
            print('adding measurement column to measurements table!')
            self.df['measurement'] = self.df['experiment'] + self.df['treat_step_num'].apply(treat_step)
            self.write_magic_file()



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
                if col_label not in list(row_data.keys()):
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
                if col_label not in list(row_data.keys()):
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
        df.index.name = name + " name"
        self.df = df

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
        self.df = pd.concat([self.df[:ind], self.df[ind+1:]], sort=True)
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
        self.df['num'] = list(range(len(self.df)))
        df_data = self.df
        # delete all records that meet condition
        if len(df_data[condition]) > 0:  #we have one or more records to delete
            inds = df_data[condition]['num'] # list of all rows where condition is TRUE
            for ind in inds[::-1]:
                df_data = self.delete_row(ind)
                if info_str:
                    print("-I- Deleting {}. ".format(info_str), end=' ')
                    print('deleting row {}'.format(str(ind)))
        # sort so that all rows for an item are together
        df_data.sort_index(inplace=True)
        # redo temporary index
        df_data['num'] = list(range(len(df_data)))
        self.df = df_data
        return df_data

    def drop_stub_rows(self, ignore_cols=('specimen',
                                          'sample',
                                          'software_packages',
                                          'num')):
        """
        Drop self.df rows that have only null values,
        ignoring certain columns.

        Parameters
        ----------
        ignore_cols : list-like
            list of column names to ignore for

        Returns
        ---------
        self.df : pandas DataFrame
        """
        # ignore citations if they just say 'This study'
        if 'citations' in self.df.columns:
            if list(self.df['citations'].unique()) == ['This study']:
                ignore_cols = ignore_cols + ('citations',)
        drop_cols = self.df.columns.difference(ignore_cols)
        self.df.dropna(axis='index', subset=drop_cols, how='all', inplace=True)
        return self.df

    def drop_duplicate_rows(self, ignore_cols=['specimen', 'sample']):
        """
        Drop self.df rows that have only null values,
        ignoring certain columns BUT only if those rows
        do not have a unique index.

        Different from drop_stub_rows because it only drops
        empty rows if there is another row with that index.

        Parameters
        ----------
        ignore_cols : list_like
            list of colum names to ignore

        Returns
        ----------
        self.df : pandas DataFrame
        """
        # keep any row with a unique index
        unique_index = self.df.index.unique()
        cond1 = ~self.df.index.duplicated(keep=False)
        # or with actual data
        ignore_cols = [col for col in ignore_cols if col in self.df.columns]
        relevant_df = self.df.drop(ignore_cols, axis=1)
        cond2 = relevant_df.notnull().any(axis=1)
        orig_len = len(self.df)
        new_df = self.df[cond1 | cond2]
        # make sure we haven't lost anything important
        if any(unique_index.difference(new_df.index.unique())):
                cond1 = ~self.df.index.duplicated(keep="first")
        self.df = self.df[cond1 | cond2]
        end_len = len(self.df)
        removed = orig_len - end_len
        if removed:
            print('-I- Removed {} redundant records from {} table'.format(removed, self.dtype))
        return self.df


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
        self.df['num'] = list(range(len(self.df)))
        df_data = self.df
        condition2 = (df_data.index == name)
        # edit first of existing data that meets condition
        if len(df_data[condition & condition2]) > 0:  #we have one or more records to update or delete
            # list of all rows where condition is true and index == name
            inds = df_data[condition & condition2]['num']
            #inds = df_data[condition]['num'] # list of all rows where condition is true
            existing_data = dict(df_data.iloc[inds.iloc[0]]) # get first record of existing_data from dataframe
            existing_data.update(new_data) # update existing data with new interpretations
            # update row
            self.update_row(inds.iloc[0], existing_data)
            # now remove all the remaining records of same condition
            if len(inds) > 1:
                for ind in inds[1:]:
                    print("deleting redundant records for:", name)
                    df_data = self.delete_row(ind)
        else:
            if update_only:
                print("no record found for that condition, not updating ", name)
            else:
                print('no record found - creating new one for ', name)
                # add new row
                df_data = self.add_row(name, new_data)
        # sort so that all rows for an item are together
        df_data.sort_index(inplace=True)
        # redo temporary index
        df_data['num'] = list(range(len(df_data)))
        self.df = df_data
        return df_data

    def front_and_backfill(self, cols, inplace=True):
        """
        Groups dataframe by index name then replaces null values in selected
        columns with front/backfilled values if available.
        Changes self.df inplace.

        Parameters
        ----------
        self : MagicDataFrame
        cols : array-like
            list of column names

        Returns
        ---------
        self.df
        """
        cols = list(cols)
        for col in cols:
            if col not in self.df.columns: self.df[col] = np.nan
        short_df = self.df[cols]
        # horrible, bizarre hack to test for pandas malfunction
        tester = short_df.groupby(short_df.index, sort=False).fillna(method='ffill')
        if not_null(tester):
            short_df = short_df.groupby(short_df.index, sort=False).fillna(method='ffill').groupby(short_df.index, sort=False).fillna(method='bfill')
        else:
            print('-W- Was not able to front/back fill table {} with these columns: {}'.format(self.dtype, ', '.join(cols)))
        if inplace:
            self.df[cols] = short_df[cols]
            return self.df
        return short_df


    def sort_dataframe_cols(self):
        """
        Sort self.df so that self.name is the first column,
        and the rest of the columns are sorted by group.
        """
        # get the group for each column
        cols = self.df.columns
        groups = list(map(lambda x: self.data_model.get_group_for_col(self.dtype, x), cols))
        sorted_cols = cols.groupby(groups)
        ordered_cols = []
        # put names first
        try:
            names = sorted_cols.pop('Names')
        except KeyError:
            names = []
        ordered_cols.extend(list(names))
        no_group = []
        # remove ungrouped columns
        if '' in sorted_cols:
            no_group = sorted_cols.pop('')
        # flatten list of columns
        for k in sorted(sorted_cols):
            ordered_cols.extend(sorted(sorted_cols[k]))
        # add back in ungrouped columns
        ordered_cols.extend(no_group)
        # put name first
        try:
            if self.name in ordered_cols:
                ordered_cols.remove(self.name)
                ordered_cols[:0] = [self.name]
        except AttributeError:
            pass
        #
        self.df = self.df[ordered_cols]
        return self.df

    def add_sequence(self):
        self.df['sequence'] = range(len(self.df))
        return self.df

    ## Methods that take self.df and extract some information from it

    def find_filled_col(self, col_list):
        """
        return the first col_name from the list that is both
        a. present in self.df.columns and
        b. self.df[col_name] has at least one non-null value

        Parameters
        ----------
        self: MagicDataFrame
        col_list : iterable
           list of columns to check

        Returns
        ----------
        col_name : str
        """
        for col in col_list:
            if col in self.df.columns:
                if not all([is_null(val, False) for val in self.df[col]]):
                    return col

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
        # replace np.nan / None with ""
        df = df.where(df.notnull(), "")
        # string-i-fy everything
        df = df.astype(str)

        if lst_or_dict == "lst":
            return list(df.T.apply(dict))
        else:
            return {str(i[df.index.name.split(' ')[0]]): dict(i) for i in list(df.T.apply(dict))}

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
            df_slice = self.df.loc[index_names]
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
        first_val = list(df_slice[col_name].dropna())
        if any(first_val):
            return first_val[0]
        else:
            return ""
        #return df_slice[col_name].dropna()[0]


    def get_di_block(self, df_slice=None, do_index=False,
                     item_names=None, tilt_corr='100',
                     excl=None, ignore_tilt=False):
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
            df_slice = self.df.loc[item_names]
        elif not do_index:
            # otherwise use the provided slice
            df_slice = df_slice

        # once you have the slice, fix up the data
        # tilt correction must match
        if not ignore_tilt:
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

    def merge_dfs(self, df1):
        """
        Description: takes new calculated data and replaces the corresponding data in self.df with the new input data preserving the most important metadata if they are not otherwise saved. Note this does not mutate self.df it simply returns the merged dataframe if you want to replace self.df you'll have to do that yourself.

        @param: df1 - first DataFrame whose data will preferentially be used.
        """

        if self.df.empty: return df1
        elif df1.empty: return self.df

        #copy to prevent mutation
        cdf2 = self.df.copy()

        #split data into types and decide which to replace
#        if replace_dir_or_int == 'dir' and 'method_codes' in cdf2.columns:
#            cdf2 = cdf2[cdf2['method_codes'].notnull()]
#            acdf2 = cdf2[cdf2['method_codes'].str.contains('LP-PI')]
#            mcdf2 = cdf2[cdf2['method_codes'].str.contains('LP-DIR')]
#        elif replace_dir_or_int == 'int' and 'method_codes' in cdf2.columns:
#            cdf2 = cdf2[cdf2['method_codes'].notnull()]
#            mcdf2 = cdf2[cdf2['method_codes'].str.contains('LP-PI')]
#            acdf2 = cdf2[cdf2['method_codes'].str.contains('LP-DIR')]
#        else:
#            mcdf2 = cdf2
#            acdf2 = pd.DataFrame(columns=mcdf2.columns)

        #get rid of stupid duplicates
#        [mcdf2.drop(cx,inplace=True,axis=1) for cx in mcdf2.columns if cx in df1.columns]

        #join the new calculated data with the old data of same type
        if self.dtype.endswith('s'): dtype = self.dtype[:-1]
        else: dtype = self.dtype
        index_name = dtype + "_name"
        for df in [df1, cdf2]:
            df.index.name = index_name
        mdf = df1.join(cdf2, how='outer', rsuffix='_remove', on=index_name)
        if 'specimen' in mdf.columns and \
           'specimen_remove' in mdf.columns and \
           len(mdf[mdf['specimen'].isnull()])>0:
            mdf['specimen']=mdf['specimen_remove']
        if 'sample' in mdf.columns and \
           'sample_remove' in mdf.columns and \
           len(mdf[mdf['sample'].isnull()])>0:
            mdf['sample']=mdf['sample_remove']
        if 'site' in mdf.columns and \
           'site_remove' in mdf.columns and \
            len(mdf[mdf['site'].isnull()])>0:
            mdf['site']=mdf['site_remove']
        if 'location' in mdf.columns and \
           'location_remove' in mdf.columns and \
           len(mdf[mdf['location'].isnull()])>0:
            mdf['location']=mdf['location_remove']
        if 'lat' in mdf.columns and \
           'lat_remove' in mdf.columns:
            if len(mdf[mdf['lat'].isnull()])>len(mdf[mdf['lat_remove'].isnull()]):
                mdf['lat']=mdf['lat_remove']
        if 'lon' in mdf.columns and \
           'lon_remove' in mdf.columns:
            if len(mdf[mdf['lon'].isnull()])>len(mdf[mdf['lon_remove'].isnull()]):
                mdf['lon']=mdf['lon_remove']
        #drop duplicate columns if they are created
        [mdf.drop(col,inplace=True,axis=1) for col in mdf.columns if col.endswith("_remove")]
        #duplicates rows for some freaking reason
        mdf.drop_duplicates(inplace=True,subset=[col for col in mdf.columns if col != 'description'])
        #merge the data of the other type with the new data
#        mdf = mdf.merge(acdf2, how='outer')
        if dtype in mdf.columns:
            #fix freaking indecies because pandas
            mdf = mdf.set_index(dtype)
            #really? I wanted the index changed not a column deleted?!?
            mdf[dtype] = mdf.index
            mdf.index.name = index_name
            mdf.sort_index(inplace=True)

        return mdf


    ## Methods for writing self.df out to tab-delimited file

    def write_magic_file(self, custom_name=None, dir_path=".",
                         append=False, multi_type=False, df=None):
        """
        Write self.df out to tab-delimited file.
        By default will use standard MagIC filenames (specimens.txt, etc.),
        or you can provide a custom_name to write to instead.
        By default will write to custom_name if custom_name is a full path,
        or will write to dir_path + custom_name if custom_name
        is not a full path.

        Parameters
        ----------
        self : MagIC DataFrame
        custom_name : str
            custom file name
        dir_path : str
            dir_path (used if custom_name is not a full path), default "."
        append : bool
            append to existing file, default False
        multi_type : bool
            for creating upload file

        Return
        --------
        fname : str
            output file name
        """
        # don't let custom name start with "./"
        if custom_name:
            if custom_name.startswith('.'):
                custom_name = os.path.split(custom_name)[1]
        # put columns in logical order (by group)
        self.sort_dataframe_cols()
        # if indexing column was put in, remove it
        if "num" in self.df.columns:
            self.df = self.df.drop("num", axis=1)
        #
        # make sure name is a string
        name = self.get_singular_and_plural_dtype(self.dtype)[0]
        if name in self.df.columns:
            self.df[name] = self.df[name].astype(str)
        #
        if df is None:
            df = self.df
        # get full file path
        dir_path = os.path.realpath(dir_path)
        if custom_name:
            fname = pmag.resolve_file_name(custom_name, dir_path) # os.path.join(dir_path, custom_name)
        else:
            fname = os.path.join(dir_path, self.dtype + ".txt")
        # see if there's any data
        if not len(df):
            print('-W- No data to write to {}'.format(fname))
            return False
        # add to existing file
        if append:
            print('-I- appending {} data to {}'.format(self.dtype, fname))
            mode = "a"
        # overwrite existing file
        elif os.path.exists(fname):
            print('-I- overwriting {}'.format(fname))
            mode = "w"
        # or create new file
        else:
            print('-I- writing {} records to {}'.format(self.dtype, fname))
            mode = "w"
        f = open(fname, mode)
        if append:
            header = False
            if multi_type:
                header = True
                f.write('tab\t{}\n'.format(self.dtype))
            f.flush()
            df.to_csv(f, sep="\t", header=header, index=False, mode='a')
        else:
            f.write('tab\t{}\n'.format(self.dtype))
            f.flush()
            df.to_csv(f, sep="\t", header=True, index=False, mode='a')
        print('-I- {} records written to {} file'.format(len(df), self.dtype))
        f.close()
        return fname

    ## Helper methods


    def get_non_magic_cols(self):
        """
        Find all columns in self.df that are not real MagIC 3 columns.

        Returns
        --------
        unrecognized_cols : list
        """
        table_dm = self.data_model.dm[self.dtype]
        approved_cols = table_dm.index
        unrecognized_cols = (set(self.df.columns) - set(approved_cols))
        return unrecognized_cols


    def get_first_non_null_value(self, ind_name, col_name):
        """
        For a given index and column, find the first non-null value.

        Parameters
        ----------
        self : MagicDataFrame
        ind_name : str
            index name for indexing
        col_name : str
            column name for indexing

        Returns
        ---------
        single value of str, float, or int
        """
        short_df = self.df.loc[ind_name, col_name]
        mask = pd.notnull(short_df)
        print(short_df[mask])
        try:
            val = short_df[mask].unique()[0]
        except IndexError:
            val = None
        return val


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

def not_null(val, zero_as_null=True):
    """
    Comprehensive check to see if a value is null or not.
    Returns True for: non-empty iterables, True, non-zero floats and ints,
    non-emtpy strings.
    Returns False for: empty iterables, False, zero, empty strings.

    Parameters
    ----------
    val : any Python object
    zero_as_null: bool
        treat zero as null, default True

    Returns
    ---------
    boolean
    """

    def can_iter(x):
        """
        Returns True for a non-empty iterable
        """
        try:
            any(x)
            return True
        except TypeError:
            return False

    def not_empty(x):
        """
        Returns true if x has length
        """
        if len(x):
            return True
        return False


    def exists(x):
        """
        Returns true if x
        """
        if x:
            return True
        return False

    def is_nan(x):
        """
        Returns True if x is nan
        """
        try:
            if np.isnan(x):
                return True
        except TypeError:
            return False
        return False

    # return True iff you have a non-empty iterable
    # and False for an empty iterable (including an empty string)
    if can_iter(val):
        return not_empty(val)
    # if value is not iterable, return False for np.nan, None, 0, or False
    # & True for all else
    else:
        if is_nan(val):
            return False
        if not zero_as_null:
            if val == 0:
                return True
        return exists(val)

def is_null(val, zero_as_null=True):
    """
    Convenience function for ! not_null
    """
    return not not_null(val, zero_as_null)


def get_intensity_col(data):
    """
    Check measurement dataframe for intensity columns 'magn_moment', 'magn_volume', 'magn_mass','magn_uncal'.
    Return the first intensity column that is in the dataframe AND has data.

    Parameters
    ----------
    data : pandas DataFrame

    Returns
    ---------
    str
        intensity method column or ""
    """
    # possible intensity columns
    intlist = ['magn_moment', 'magn_volume', 'magn_mass','magn_uncal']
    # intensity columns that are in the data
    int_meths = [col_name for col_name in data.columns if col_name in intlist]
    # drop fully null columns
    data.dropna(axis='columns', how='all')
    # ignore columns with only blank values (including "")
    for col_name in int_meths[:]:
        if not data[col_name].any():
            int_meths.remove(col_name)
    if len(int_meths):
        if 'magn_moment' in int_meths:
            return 'magn_moment'
        return int_meths[0]
    return ""


def add_sites_to_meas_table(dir_path):
    """
    Add site columns to measurements table (e.g., to plot intensity data),
    or generate an informative error message.

    Parameters
    ----------
    dir_path : str
        directory with data files


    Returns
    ----------
    status : bool
        True if successful, else False
    data : pandas DataFrame
        measurement data with site/sample
    """
    reqd_tables = ['measurements', 'specimens', 'samples', 'sites']
    con = Contribution(dir_path, read_tables=reqd_tables)
    # check that all required tables are available
    missing_tables = []
    for table in reqd_tables:
        if table not in con.tables:
            missing_tables.append(table)
    if missing_tables:
        return False, "You are missing {} tables".format(", ".join(missing_tables))

    # put sample column into the measurements table
    con.propagate_name_down('sample', 'measurements')
    # put site column into the measurements table
    con.propagate_name_down('site', 'measurements')
    # check that column propagation was successful
    if 'site' not in con.tables['measurements'].df.columns:
        return False, "Something went wrong with propagating sites down to the measurement level"
    return True, con.tables['measurements'].df


def add_sites_to_spec_table(dir_path):
    """
    Add site columns to specimens table (e.g., to plot intensity data),
    or generate an informative error message.

    Parameters
    ----------
    dir_path : str
        directory with data files

    Returns
    ----------
    status : bool
        True if successful, else False
    data : pandas DataFrame
        specimen data with site/sample
    """
    reqd_tables = ['specimens', 'samples', 'sites']
    con = Contribution(dir_path, read_tables=reqd_tables)
    # check that all required tables are available
    missing_tables = []
    for table in reqd_tables:
        if table not in con.tables:
            missing_tables.append(table)
    if missing_tables:
        return False, "You are missing {} tables".format(", ".join(missing_tables))

    # put site column into the specimens table
    con.propagate_name_down('site', 'specimens')
    # check that column propagation was successful
    if 'site' not in con.tables['specimens'].df.columns:
        return False, "Something went wrong with propagating sites down to the specimen level"
    return True, con.tables['specimens'].df



def prep_for_intensity_plot(data, meth_code, dropna=(), reqd_cols=()):
    """
    Strip down measurement data to what is needed for an intensity plot.
    Find the column with intensity data.
    Drop empty columns, and make sure required columns are present.
    Keep only records with the specified method code.

    Parameters
    ----------
    data : pandas DataFrame
        measurement dataframe
    meth_code : str
        MagIC method code to include, i.e. 'LT-AF-Z'
    dropna : list
        columns that must not be empty
    reqd_cols : list
        columns that must be present

    Returns
    ----------
    status : bool
        True if successful, else False
    data : pandas DataFrame
        measurement data with required columns
    """
    # initialize
    dropna = list(dropna)
    reqd_cols = list(reqd_cols)
    # get intensity column
    try:
        magn_col = get_intensity_col(data)
    except AttributeError:
        return False, "Could not get intensity method from data"
    # drop empty columns
    if magn_col not in dropna:
        dropna.append(magn_col)
    data = data.dropna(axis=0, subset=dropna)
    # add to reqd_cols list
    if 'method_codes' not in reqd_cols:
        reqd_cols.append('method_codes')
    if magn_col not in reqd_cols:
        reqd_cols.append(magn_col)
    # drop non reqd cols, make sure all reqd cols are present
    try:
        data = data[reqd_cols]
    except KeyError as ex:
        print(ex)
        missing = set(reqd_cols).difference(data.columns)
        return False, "missing these required columns: {}".format(", ".join(missing))
    # filter out records without the correct method code
    data = data[data['method_codes'].str.contains(meth_code).astype(bool)]
    return True, data

def stringify_col(df, col_name):
    """
    Take a dataframe and string-i-fy a column of values.
    Turn nan/None into "" and all other values into strings.

    Parameters
    ----------
    df : dataframe
    col_name : string
    """
    df = df.copy()
    df[col_name] = df[col_name].fillna("")
    df[col_name] = df[col_name].astype(str)
    return df



if __name__ == "__main__":
    pass
