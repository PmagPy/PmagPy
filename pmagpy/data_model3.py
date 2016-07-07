import os
import json
from pandas import DataFrame
from pmagpy import check_updates


class DataModel(object):

    def __init__(self):
        self.dm = self.get_data_model()
    
    def download_data_model(self):
        pmag_dir = check_updates.get_pmag_dir()
        model_file = os.path.join(pmag_dir, '3_0', 'data_model_July_7_2016.json')
        f = open(model_file, 'r')
        string = '\n'.join(f.readlines())
        raw = json.loads(unicode(string, errors='ignore'))
        full = DataFrame(raw)
        return full

    def parse_data_model(self, full_df):
        data_model = {}
        levels = ['specimens', 'samples', 'sites', 'locations', 'ages']
        for level in levels:
            df = DataFrame(full_df['tables'][level]['columns'])
            data_model[level] = df.transpose()
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


    def get_headers(self, table_name, group_name):
        """
        Return a list of all headers for a given group
        """
        # get all headers of a particular group
        df = self.dm[table_name]
        cond = df['group'] == group_name
        return df[cond].index





if __name__ == "__main__":
    #dm = DataModel()
    pass


