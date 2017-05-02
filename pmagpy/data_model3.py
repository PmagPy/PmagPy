from __future__ import print_function
from builtins import str
from builtins import object
import os
import json
import pandas as pd
from pandas import DataFrame
from pmagpy import find_pmag_dir


class DataModel(object):

    def __init__(self):
        self.dm, self.crit_map = self.get_data_model()

    # Acquiring the data model
    def get_dm_online(self):
        """
        Grab the 3.0 data model from earthref.org
        """
        url = 'https://www2.earthref.org/MagIC/data-models/3.0.json'
        url = "https://earthref.org/MagIC/data-models/3.0.json"
        raw_dm = pd.io.json.read_json(url)
        return raw_dm

    def get_dm_offline(self):
        """
        Grab the 3.0 data model from the PmagPy/pmagpy directory
        """
        print("-I- Using cached 3.0 data model")
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
        try:
            f = open(model_file, 'r', encoding='utf-8-sig')
        except TypeError:
            f = open(model_file, 'r')
        string = '\n'.join(f.readlines())
        f.close()
        raw = json.loads(string)
        full = DataFrame(raw)
        return full

    def download_data_model(self):
        """
        Try to get the 3.0 data model online,
        if that fails get it offline.
        """
        #try:
        #    raw_dm = self.get_dm_online()
        #except:
        #    raw_dm = self.get_dm_offline()
        raw_dm = self.get_dm_offline()
        return raw_dm

    def parse_data_model(self, full_df):
        """
        Format the data model into a dictionary of DataFrames.
        """
        data_model = {}
        levels = ['specimens', 'samples', 'sites', 'locations',
                  'ages', 'measurements', 'criteria', 'contribution',
                  'images']
        criteria_map = DataFrame(full_df['criteria_map'])
        for level in levels:
            df = DataFrame(full_df['tables'][level]['columns'])
            data_model[level] = df.transpose()
        # replace np.nan with None
        data_model[level] = data_model[level].where((pd.notnull(data_model[level])), None)
        return data_model, criteria_map

    def get_data_model(self):
        """
        Acquire and parse the data model
        """
        full_df = self.download_data_model()
        parsed_df, criteria_map = self.parse_data_model(full_df)
        return parsed_df, criteria_map


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


if __name__ == "__main__":
    #dm = DataModel()
    pass
