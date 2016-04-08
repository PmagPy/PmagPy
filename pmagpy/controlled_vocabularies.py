#!/usr/bin/env python
import pandas as pd
from pandas import Series, DataFrame
import urllib2
import httplib
import json
import os
import backup_vocabulary as backup
# get list of controlled vocabularies form this part of the api:
#'http://api.earthref.org/MagIC/vocabularies.json'
# then, use that list to determine whether or not any given column has a controlled vocabulary list
import check_updates
pmag_dir = check_updates.get_pmag_dir()
data_model_dir = os.path.join(pmag_dir, 'pmagpy', 'data_model')
# if using with py2app, the directory structure is flat,
# so check to see where the resource actually is
if not os.path.exists(data_model_dir):
    data_model_dir = os.path.join(pmag_dir, 'data_model')

class Vocabulary(object):

    def __init__(self):
        self.vocabularies = []
        self.possible_vocabularies = []
        self.all_codes = []
        self.code_types = []
        self.er_methods = []
        self.pmag_methods = []
        self.age_methods = []

    def get_meth_codes(self):
        """
        Get method codes from the MagIC API
        """
        try:
            raw_codes = pd.io.json.read_json('https://api.earthref.org/MagIC/method_codes.json')
        except urllib2.URLError:
            return [], []
        except httplib.BadStatusLine:
            return [], []
        code_types = raw_codes.ix['label']
        tot_codes = raw_codes.ix['count'].sum()

        all_codes = []
        for code_name in code_types.index:
            code_url = 'https://api.earthref.org/MagIC/method_codes/{}.json'.format(code_name)
            # if internet fails in the middle, cut out
            try:
                raw_df = pd.io.json.read_json(code_url)
            except urllib2.URLError:
                return [], []
            except httplib.BadStatusLine:
                return [], []
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
        code_types['pmag'] = False
        code_types['er'] = False
        code_types['age'] = False
        age = ['geochronology_method']
        pmag = ['anisotropy_estimation', 'data_adjustment',
                'direction_estimation', 'geochronology_method',
                'intensity_estimation', 'lab_protocol', 'lab_treatment',
                'stability_tests', 'statistical_method']
        er = ['field_sampling', 'sample_characterization',
              'sample_orientation', 'sample_preparation',
              'geochronology_method']
        code_types.ix[pmag, 'pmag'] = True
        code_types.ix[er, 'er'] = True
        code_types.ix[age, 'age'] = True
        return all_codes, code_types

    def get_one_meth_type(self, mtype, method_list):
        """
        Get all codes of one type (i.e., 'anisotropy_estimation')
        """
        cond = method_list['dtype'] == mtype
        codes = method_list[cond]
        return codes

    def get_one_meth_category(self, category, all_codes, code_types):
        """
        Get all codes in one category (i.e., all pmag codes).
        This can include multiple method types (i.e., 'anisotropy_estimation', 'sample_prepartion', etc.)
        """
        categories = Series(code_types[code_types[category] == True].index)
        cond = all_codes['dtype'].isin(categories)
        codes = all_codes[cond]
        return codes

    def get_tiered_meth_category(self, mtype, all_codes, code_types):
        """
        Get a tiered list of all er/pmag_age codes
        i.e. pmag_codes = {'anisotropy_codes': ['code1', 'code2'], 
        'sample_preparation': [code1, code2], ...}
        """
        #cond = code_types[code_types[mtype] == True]
        categories = Series(code_types[code_types[mtype] == True].index)
        codes = {cat: list(self.get_one_meth_type(cat, all_codes).index) for cat in categories}
        return codes

    default_vocab_types = ('lithology', 'class', 'type','location_type',
                           'age_unit', 'site_definition')

    def get_controlled_vocabularies(self, vocab_types=default_vocab_types):
        """
        Get all non-method controlled vocabularies
        """
        #vocab_types = ['lithology', 'class', 'type', 'location_type', 'age_unit', 'site_definition']
        connected = True
        try:
            controlled_vocabularies = []
            print '-I- Importing controlled vocabularies from https://earthref.org'
            url = 'https://api.earthref.org/MagIC/vocabularies.json'
            data = pd.io.json.read_json(url)
            possible_vocabularies = data.columns
            ## this line means, grab every single controlled vocabulary
            #vocab_types = possible_vocabularies
            for vocab in vocab_types:
                url = 'https://api.earthref.org/MagIC/vocabularies/{}.json'.format(vocab)
                data = pd.io.json.read_json(url)
                stripped_list = [item['item'] for item in data[vocab][0]]
                if len(stripped_list) > 100:
                # split out the list alphabetically, into a dict of lists:
                # {'A': ['alpha', 'artist'], 'B': ['beta', 'beggar']...}
                    dictionary = {}
                    for item in stripped_list:
                        if not item: # ignore null values
                            continue
                        letter = item[0].upper()
                        if letter not in dictionary.keys():
                            dictionary[letter] = []
                        dictionary[letter].append(item)

                    stripped_list = dictionary

                controlled_vocabularies.append(stripped_list)

            vocabularies = pd.Series(controlled_vocabularies, index=vocab_types)
        except urllib2.URLError:
            connected = False
        except httplib.BadStatusLine:
            connected = False
        if not connected:
            print "-W- Could not connect to internet -- will not be able to provide all controlled vocabularies"
            vocabularies = pd.Series([backup.site_lithology, backup.site_class, backup.site_type,
                                      backup.location_type, backup.age_unit, backup.site_definition], index=vocab_types)
            possible_vocabularies = []
        return vocabularies, possible_vocabularies


    #def get_all_possible_vocabularies(possible_list):

    def get_tiered_meth_category_offline(self, category):
        path = os.path.join(data_model_dir, 'er_methods.txt')
        dfile = open(path)
        json_data = json.load(dfile)
        dfile.close()
        return json_data



    def get_stuff(self):
        all_codes, code_types = self.get_meth_codes()
        ## do it this way if you want a non-nested list of all er/pmag/age codes
        ##def get_one_meth_category(category, all_codes, code_types):
        ## i.e. er_codes = [code1, code2,...]
        #er_methods = list(get_one_meth_category('er', all_codes, code_types).index)
        #pmag_methods = list(get_one_meth_category('pmag', all_codes, code_types).index)
        #age_methods = list(get_one_meth_category('age', all_codes, code_types).index)

        ## do it this way if you want a tiered list of all er/pmag_age codes
        ## i.e. er_codes = {'anisotropy_codes': ['code1', 'code2'], ...}
        ##def get_tiered_meth_category(mtype, all_codes, code_types):


        if any(all_codes):
            er_methods = self.get_tiered_meth_category('er', all_codes, code_types)
            pmag_methods = self.get_tiered_meth_category('pmag', all_codes, code_types)
            age_methods = self.get_tiered_meth_category('age', all_codes, code_types)
        else:
            #def get_tiered_meth_category_offline(category):
            er_methods = self.get_tiered_meth_category_offline('er')
            pmag_methods = self.get_tiered_meth_category_offline('pmag')
            age_methods = self.get_tiered_meth_category_offline('age')
            path = os.path.join(data_model_dir, 'code_types.txt')
            with open(path, 'r') as type_file:
                raw_code_types = json.load(type_file)
            code_types = pd.read_json(raw_code_types)
            path = os.path.join(data_model_dir, 'all_codes.txt')
            with open(path, 'r') as code_file:
                raw_all_codes = json.load(code_file)
            all_codes = pd.read_json(raw_all_codes)

        vocabularies, possible_vocabularies = self.get_controlled_vocabularies()
        #return vocabularies, possible_vocabularies, all_codes, code_types, er_methods, pmag_methods, age_methods
        self.vocabularies = vocabularies
        self.possible_vocabularies = possible_vocabularies
        self.all_codes = all_codes
        self.code_types = code_types
        self.er_methods = er_methods
        self.pmag_methods = pmag_methods
        self.age_methods = age_methods


vocab = Vocabulary()
        
# vocabularies, possible_vocabularies, all_codes, code_types, er_methods, pmag_methods, age_methods = get_stuff()
