#!/usr/bin/env python
import pandas as pd
from pandas import Series, DataFrame

import backup_vocabulary as backup
# get list of controlled vocabularies form this part of the api:
#'http://api.earthref.org/MAGIC/vocabularies.json'
# then, use that list to determine whether or not any given column has a controlled vocabulary list




def get_meth_codes():
    raw_codes = pd.io.json.read_json('http://api.earthref.org/MAGIC/method_codes.json')
    code_types = raw_codes.ix['label']
    tot_codes = raw_codes.ix['count'].sum()

    all_codes = []
    for code_name in code_types.index:
        code_url = 'http://api.earthref.org/MAGIC/method_codes/{}.json'.format(code_name)
        raw_df = pd.io.json.read_json(code_url)
        # unpack the data into a dataframe, drop unnecessary columns
        df = DataFrame(raw_df[code_name][0])[['definition', 'code']]
        # remake the dataframe with the code (i.e., 'SM_VAR') as the index
        df = DataFrame(raw_df[code_name][0], index=df['code'])[['definition']]
        # add a column with the code type (i.e., 'anisotropy_estimation')
        df['dtype'] = code_name
        little_series = df['definition']
        big_series = Series()
        if any(all_codes):
            all_codes = pd.concat([all_codes, df])
            big_series = pd.concat([big_series, little_series])
        else:
            all_codes = df
            big_series = little_series

    # format code_types and add pmag, er, and age columns
    code_types = raw_codes.T
    code_types['pmag'], code_types['er'], code_types['age'] = False, False, False
    age = ['geochronology_method']
    pmag = ['anisotropy_estimation', 'data_adjustment', 'direction_estimation', 'geochronology_method', 'intensity_estimation', 'lab_protocol', 'lab_treatment', 'stability_tests', 'statistical_method']
    er = ['field_sampling', 'sample_characterization', 'sample_orientation', 'sample_preparation', 'geochronology_method']
    code_types.ix[pmag, 'pmag'] = True
    code_types.ix[er, 'er'] = True
    code_types.ix[age, 'age'] = True
    return all_codes, code_types

def get_one_meth_type(mtype, all_codes):
    string = 'anisotropy_estimation'
    cond = all_codes['dtype'] == string
    codes = all_codes[cond]
    return codes

def get_one_meth_category(category, all_codes, code_types):
    categories = Series(code_types[code_types[category] == True].index)
    sort_func = lambda x: x in list(categories)
    cond = all_codes['dtype'].apply(sort_func)
    codes = all_codes[cond]
    return codes


def get_controlled_vocabularies():
    vocab_types = ['lithology', 'class', 'type', 'location_type', 'age_unit', 'site_definition']

    try:
        controlled_vocabularies = []

        print '-I- Importing controlled vocabularies from http://earthref.org'
        url = 'http://api.earthref.org/MAGIC/vocabularies.json'
        data = pd.io.json.read_json(url)
        possible_vocabularies = data.columns

        for vocab in vocab_types:
            url = 'http://api.earthref.org/MAGIC/vocabularies/{}.json'.format(vocab)
            data = pd.io.json.read_json(url)
            stripped_list = [item['item'] for item in data[vocab][0]]


            if len(stripped_list) > 100:
            # split out the list alphabetically, into a dict of lists {'A': ['alpha', 'artist'], 'B': ['beta', 'beggar']...}
                dictionary = {}
                for item in stripped_list:
                    letter = item[0].upper()
                    if letter not in dictionary.keys():
                        dictionary[letter] = []
                    dictionary[letter].append(item)

                stripped_list = dictionary

            controlled_vocabularies.append(stripped_list)

        vocabularies = pd.Series(controlled_vocabularies, index=vocab_types)

    except:
        print "-W- Could not connect to internet -- will not be able to provide all controlled vocabularies"
        vocabularies = pd.Series([backup.site_lithology, backup.site_class, backup.site_type,
                                  backup.location_type, backup.age_unit, backup.site_definition], index=vocab_types)
        possible_vocabularies = []
    return vocabularies, possible_vocabularies
    

all_codes, code_types = get_meth_codes()
#def get_one_meth_category(category, all_codes, code_types):
er_methods = list(get_one_meth_category('er', all_codes, code_types).index)
pmag_methods = list(get_one_meth_category('pmag', all_codes, code_types).index)
age_methods = list(get_one_meth_category('age', all_codes, code_types).index)
vocabularies, possible_vocabularies = get_controlled_vocabularies()

