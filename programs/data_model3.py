import os
import json
from pandas import DataFrame

def download_data_model():
    model_file = os.path.join('3_0', 'MagIC Data Model v3.0 - unpublished.json')
    f = open(model_file, 'r')
    string = '\n'.join(f.readlines())
    raw = json.loads(unicode(string, errors='ignore'))
    full = DataFrame(raw)
    return full

def parse_data_model(full_df):
    data_model = {}
    levels = ['specimens', 'samples', 'sites', 'locations']
    for level in levels:
        df = DataFrame(full_df['tables'][level]['columns'])
        data_model[level] = df.transpose()
    return data_model


def get_data_model():
    full_df = download_data_model()
    return parse_data_model(full_df)


DATA_MODEL = get_data_model()
#

def get_groups(table_name):
    """
    Return list of all groups for a particular data type
    """
    df = DATA_MODEL[table_name]
    return list(df['group'].unique())


def get_headers(table_name, group_name):
    """
    Return a list of all headers for a given group
    """
    # get all headers of a particular group
    df = DATA_MODEL[table_name]
    cond = df['group'] == group_name
    return df[cond].index



if __name__ == "__main__":
    dm = get_data_model()
    print dm['specimens'].index


