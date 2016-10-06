import os
import json
import pandas as pd
from pandas import DataFrame
from pmagpy import check_updates


class DataModel(object):

    def __init__(self):
        self.dm = self.get_data_model()

    def download_data_model(self):
        pmag_dir = check_updates.get_pmag_dir()
        model_file = os.path.join(pmag_dir, 'pmagpy', 'data_model', 'data_model.json')
        #if not os.path.exists(model_file):
        #    model_file = os.path.join(pmag_dir, 'data_model_August_4_2016.json')
        f = open(model_file, 'r')
        string = '\n'.join(f.readlines())
        raw = json.loads(unicode(string, errors='ignore'))
        full = DataFrame(raw)
        return full

    def parse_data_model(self, full_df):
        data_model = {}
        levels = ['specimens', 'samples', 'sites', 'locations',
                  'ages', 'measurements', 'criteria', 'contribution']
        for level in levels:
            df = DataFrame(full_df['tables'][level]['columns'])
            data_model[level] = df.transpose()
        # replace np.nan with None
        data_model[level] = data_model[level].where((pd.notnull(data_model[level])), None)
        return data_model


    def get_data_model(self):
        full_df = self.download_data_model()
        parsed_df = self.parse_data_model(full_df)
        return parsed_df

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
