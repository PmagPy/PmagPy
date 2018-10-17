import os
import json
import numpy as np
try:
    import requests
except ImportError:
    requests = None
import pandas as pd
from pmagpy import find_pmag_dir


class DataModel():

    """
    Contains the MagIC data model and validation information.
    self.dm is a dictionary of DataFrames for each table.
    self.crit_map is a DataFrame with all of the columns validations.
    """

    def __init__(self, offline=False):
        self.offline = offline
        self.dm, self.crit_map = self.get_data_model()


    def get_data_model(self):
        """
        Try to download the data model from Earthref.
        If that fails, grab the cached data model.
        """
        dm = self.get_dm_online()
        if dm:
            print('-I- Using online data model')
            #self.cache_data_model(dm)
            return self.parse_response(dm)
        # if online is not available, get cached dm
        dm = self.get_dm_offline()
        print('-I- Using cached data model')
        return self.parse_cache(dm)


    def get_dm_offline(self):
        """
        Grab the 3.0 data model from the PmagPy/pmagpy directory

        Returns
        ---------
        full : DataFrame
            cached data model json in DataFrame format
        """
        model_file = self.find_cached_dm()
        try:
            f = open(model_file, 'r', encoding='utf-8-sig')
        except TypeError:
            f = open(model_file, 'r')
        string = '\n'.join(f.readlines())
        f.close()
        raw = json.loads(string)
        full = pd.DataFrame(raw)
        return full


    def get_dm_online(self):
        """
        Use requests module to get data model from Earthref.
        If this fails or times out, return false.

        Returns
        ---------
        result : requests.models.Response, False if unsuccessful
        """
        if not requests:
            return False
        try:
            req = requests.get("https://earthref.org/MagIC/data-models/3.0.json", timeout=3)
            if not req.ok:
                return False
            return req
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout):
            return False


    def parse_cache(self, full_df):
        """
        Format the cached data model into a dictionary of DataFrames
        and a criteria map DataFrame.

        Parameters
        ----------
        full_df : DataFrame
            result of self.get_dm_offline()

        Returns
        ----------
        data_model : dictionary of DataFrames
        crit_map : DataFrame
        """
        data_model = {}
        levels = ['specimens', 'samples', 'sites', 'locations',
                  'ages', 'measurements', 'criteria', 'contribution',
                  'images']
        criteria_map = pd.DataFrame(full_df['criteria_map'])
        for level in levels:
            df = pd.DataFrame(full_df['tables'][level]['columns'])
            data_model[level] = df.transpose()
        # replace np.nan with None
        data_model[level] = data_model[level].where((pd.notnull(data_model[level])), None)
        return data_model, criteria_map


    def parse(self, data_model, crit):
        """
        Take the relevant pieces of the data model json
        and parse into data model and criteria map.

        Parameters
        ----------
        data_model : data model piece of json (nested dicts)
        crit : criteria map piece of json (nested dicts)

        Returns
        ----------
        data_model : dictionary of DataFrames
        crit_map : DataFrame
        """
        # data model
        tables = pd.DataFrame(data_model)
        data_model = {}
        for table_name in tables.columns:
            data_model[table_name] = pd.DataFrame(tables[table_name]['columns']).T
            # replace np.nan with None
            data_model[table_name] = data_model[table_name].where((pd.notnull(data_model[table_name])), None)
        # criteria map
        zipped = list(zip(crit.keys(), crit.values()))
        crit_map = pd.DataFrame(zipped)
        crit_map.index = crit_map[0]
        crit_map.drop(0, axis='columns', inplace=True)
        crit_map.rename({1: 'criteria_map'}, axis='columns', inplace=True)
        crit_map.index.rename("", inplace=True)
        for table_name in ['measurements', 'specimens', 'samples', 'sites', 'locations',
                           'contribution', 'criteria', 'images', 'ages']:
            crit_map.loc[table_name] = np.nan

        return data_model, crit_map


    def parse_response(self, raw):
        """
        Format the requested data model into a dictionary of DataFrames
        and a criteria map DataFrame.
        Take data returned by a requests.get call to Earthref.

        Parameters
        ----------
        raw: 'requests.models.Response'

        Returns
        ---------
        data_model : dictionary of DataFrames
        crit_map : DataFrame
        """

        tables = raw.json()['tables']
        crit = raw.json()['criteria_map']
        return self.parse(tables, crit)


    def find_cached_dm(self):
        """
        Find filename where cached data model json is stored.

        Returns
        ---------
        model_file : str
            data model json file location
        """
        pmag_dir = find_pmag_dir.get_pmag_dir()
        if pmag_dir is None:
            pmag_dir = '.'
        model_file = os.path.join(pmag_dir, 'pmagpy',
                                  'data_model', 'data_model.json')
        # for py2app:
        if not os.path.isfile(model_file):
            model_file = os.path.join(pmag_dir, 'data_model',
                                      'data_model.json')
        if not os.path.isfile(model_file):
            model_file = os.path.join(os.path.split(os.path.dirname(__file__))[0],'pmagpy', 'data_model','data_model.json')
        if not os.path.isfile(model_file):
            model_file = os.path.join(os.path.split(os.path.dirname(__file__))[0], 'data_model','data_model.json')
        return model_file


    def cache_data_model(self, raw):
        """
        Cache the data model json.
        Take data returned by a requests.get call to Earthref.

        Parameters
        ----------
        raw: requests.models.Response

        """
        output_json = json.loads(raw.content)
        output_file = self.find_cached_dm()
        json.dump(output_json, open(output_file, 'w+'))



    # Utility methods for getting a piece of the data model
    def get_groups(self, table_name):
        """
        Return list of all groups for a particular data type
        """
        df = self.dm[table_name]
        return list(df['group'].unique())

    def get_group_headers(self, table_name, group_name):
        """
        Return a list of all headers for a given group
        """
        # get all headers of a particular group
        df = self.dm[table_name]
        cond = df['group'] == group_name
        return df[cond].index

    def get_reqd_headers(self, table_name):
        """
        Return a list of all required headers for a particular table
        """
        df = self.dm[table_name]
        cond = df['validations'].map(lambda x: 'required()' in str(x))
        return df[cond].index

    def get_group_for_col(self, table_name, col_name):
        """
        Check data model to find group name for a given column header

        Parameters
        ----------
        table_name: str
        col_name: str

        Returns
        ---------
        group_name: str
        """
        df = self.dm[table_name]
        try:
            group_name = df.loc[col_name, 'group']
        except KeyError:
            return ''
        return group_name


if __name__ == "__main__":
    dm = DataModel()
    raw = dm.get_dm_online()
    dm.cache_data_model(raw)
