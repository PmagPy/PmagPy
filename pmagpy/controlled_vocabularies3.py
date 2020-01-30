#!/usr/bin/env python
import json
import os

import pandas as pd
from pandas import Series
try:
    import requests
except ImportError:
    requests = None
from . import find_pmag_dir
from . import data_model3 as data_model
from pmag_env import set_env

pmag_dir = find_pmag_dir.get_pmag_dir()
data_model_dir = os.path.join(pmag_dir, 'pmagpy', 'data_model')
# if using with py2app, the directory structure is flat,
# so check to see where the resource actually is
if not os.path.exists(data_model_dir):
    data_model_dir = os.path.join(pmag_dir, 'data_model')


VOCAB = {}

class Vocabulary(object):

    def __init__(self, dmodel=None):
        global VOCAB
        self.vocabularies = []
        self.possible_vocabularies = []
        self.all_codes = []
        self.code_types = []
        self.methods = []
        self.age_methods = []
        if len(VOCAB):
            self.set_vocabularies()
        else:
            if isinstance(dmodel, data_model.DataModel):
                self.data_model = dmodel
                Vocabulary.dmodel = dmodel
            else:
                try:
                    self.data_model = Vocabulary.dmodel
                except AttributeError:
                    Vocabulary.dmodel = data_model.DataModel()
                    self.data_model = Vocabulary.dmodel
            self.get_all_vocabulary()
            VOCAB['vocabularies'] = self.vocabularies
            VOCAB['possible_vocabularies'] = self.possible_vocabularies
            VOCAB['all_codes'] = self.all_codes
            VOCAB['code_types'] = self.code_types
            VOCAB['methods'] = self.methods
            VOCAB['age_methods'] = self.age_methods
            VOCAB['suggested'] = self.suggested


    def set_vocabularies(self):
        self.vocabularies = VOCAB['vocabularies']
        self.possible_vocabularies = VOCAB['possible_vocabularies']
        self.all_codes = VOCAB['all_codes']
        self.code_types = VOCAB['code_types']
        self.methods = VOCAB['methods']
        self.age_methods = VOCAB['age_methods']
        self.suggested = VOCAB['suggested']


    ## Get method codes

    def get_json_online(self, url):
        """
        Use requests module to json from Earthref.
        If this fails or times out, return false.

        Returns
        ---------
        result : requests.models.Response, or [] if unsuccessful
        """
        if not requests:
            return False
        try:
            req = requests.get(url, timeout=3)
            if not req.ok:
                return []
            return req
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout):
            return []


    def get_meth_codes(self):
        if len(VOCAB):
            self.set_vocabularies()
            return
        raw_codes = []
        # try to get meth codes online
        if not set_env.OFFLINE:
            try:
                raw = self.get_json_online('https://www2.earthref.org/MagIC/method-codes.json')
                raw_codes = pd.DataFrame(raw.json())
                print('-I- Getting method codes from earthref.org')
            except Exception as ex:
                #print(ex, type(ex))
                print("-I- Couldn't connect to earthref.org, using cached method codes")
        # if you couldn't get them online, use the cache
        if not len(raw_codes):
            print("-I- Using cached method codes")
            raw_codes = pd.io.json.read_json(os.path.join(data_model_dir, "method_codes.json"), encoding='utf-8-sig')
        # parse codes
        code_types = raw_codes.loc['label']
        all_codes = []
        for code_name in code_types.index:
            if code_name == 'geoid':
                continue
            df = pd.DataFrame(raw_codes[code_name]['codes'])
            # remake the dataframe with the code (i.e., 'SM_VAR') as the index
            df.index = df['code']
            del df['code']
            # add a column with the code type (i.e., 'anisotropy_estimation')
            df['dtype'] = code_name
            little_series = df['definition']
            big_series = Series()
            if any(all_codes):
                try: # retains pandas backwards compatibility
                    all_codes = pd.concat([all_codes, df], sort=True)
                    big_series = pd.concat([big_series, little_series], sort=True)
                except TypeError:
                    all_codes = pd.concat([all_codes, df])
                    big_series = pd.concat([big_series, little_series])
            else:
                all_codes = df
                big_series = little_series

        # format code_types and age column
        code_types = raw_codes.T
        code_types['age'] = False
        age = ['geochronology_method']
        code_types.loc[age, 'age'] = True
        code_types['other'] = ~code_types['age']
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
        Get all codes in one category (i.e., all age codes).
        This can include multiple method types
        (i.e., 'anisotropy_estimation', 'sample_prepartion', etc.)
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
        categories = Series(code_types[code_types[mtype] == True].index)
        codes = {cat: list(self.get_one_meth_type(cat, all_codes).index) for cat in categories}
        return codes

    def get_tiered_meth_category_offline(self):
        path = os.path.join(data_model_dir, 'er_methods.txt')
        dfile = open(path)
        json_data = json.load(dfile)
        dfile.close()
        return json_data


    ## Get non-method-code controlled vocabularies

    default_vocab_types = ('lithologies', 'geologic_classes', 'geologic_types', 'location_types',
                           'age_unit')

    def get_controlled_vocabularies(self, vocab_types=default_vocab_types):
        """
        Get all non-method controlled vocabularies
        """
        if len(VOCAB):
            self.set_vocabularies()
            return
        data = []
        controlled_vocabularies = []
        # try to get online
        if not set_env.OFFLINE:
            url = 'https://www2.earthref.org/vocabularies/controlled.json'
            try:
                raw = self.get_json_online(url)
                data = pd.DataFrame(raw.json())
                print('-I- Importing controlled vocabularies from https://earthref.org')
            except Exception as ex:
                pass
                #print(ex, type(ex))
        # used cached
        if not len(data):
            print('-I- Using cached vocabularies')
            fname = os.path.join(data_model_dir, "controlled_vocabularies_October_3_2019.json")
            data = pd.io.json.read_json(fname, encoding='utf-8-sig')
        # parse data
        possible_vocabularies = data.columns
        ## this line means, grab every single controlled vocabulary
        vocab_types = list(possible_vocabularies)

        def get_cv_from_list(lst):
            """
            Check a validations list from the data model.
            If there is a controlled vocabulary validation,
            return which category of controlled vocabulary it is.
            This will generally be applied to the validations col
            of the data model
            """
            try:
                for i in lst:
                    if "cv(" in i:
                        return i[4:-2]
            except TypeError:
                return None
            else:
                return None

        vocab_col_names = []
        data_model = self.data_model
        for dm_key in data_model.dm:
            df = data_model.dm[dm_key]
            df['vocab_name'] = df['validations'].apply(get_cv_from_list)
            lst = list(zip(df[df['vocab_name'].notnull()]['vocab_name'], df[df['vocab_name'].notnull()].index))
            # in lst, first value is the name of the controlled vocabulary
            # second value is the name of the dataframe column
            vocab_col_names.extend(lst)

        # vocab_col_names is now a list of tuples
        # consisting of the vocabulary name and the column name
        # i.e., (u'type', u'geologic_types')

        # remove duplicate col_names:
        vocab_col_names = sorted(set(vocab_col_names))

        # add in boolean category to controlled vocabularies
        bool_items = [{'item': True}, {'item': False}, {'item': 'true'},
                      {'item': 'false'}, {'item': 0}, {'item': 1},
                      {'item': 0.0}, {'item': 1.0},
                      {'item': 't'}, {'item': 'f'},
                      {'item': 'T'}, {'item': 'F'}]
        series = Series({'label': 'Boolean', 'items': bool_items})
        data['boolean'] = series
        # use vocabulary name to get possible values for the column name
        for vocab in vocab_col_names[:]:
            if vocab[0] == "magic_table_column":
                vocab_col_names.remove(("magic_table_column", "table_column"))
                continue
            try:
                items = data[vocab[0]]['items']
                stripped_list = [item['item'] for item in items]
                controlled_vocabularies.append(stripped_list)
            except KeyError:
                # this means there is a controlled vocabulary referenced in the data model
                # that doesn't actually show up in the controlled vocabulary json
                # so just skip it
                vocab_col_names.remove(vocab)
        # create series with the column name as the index,
        # and the possible values as the values
        ind_values = [i[1] for i in vocab_col_names]
        vocabularies = pd.Series(controlled_vocabularies, index=ind_values)
        return vocabularies


    def get_suggested_vocabularies(self, vocab_types=default_vocab_types):
        """
        Get all non-method suggested vocabularies
        """
        suggested_vocabularies = []
        data = []
        # try to get suggested vocabularies online
        if not set_env.OFFLINE:
            url = 'https://www2.earthref.org/vocabularies/suggested.json'
            try:
                raw = self.get_json_online(url)
                data = pd.DataFrame(raw.json())
            except Exception as ex:
                #print(ex, type(ex))
                data = []
        # if not available online, use cached
        if not len(data):
            print('-I- Using cached suggested vocabularies')
            fname = os.path.join(data_model_dir, "suggested_vocabularies_December_10_2018.json")
            data = pd.io.json.read_json(fname, encoding='utf-8-sig')
        # parse data
        possible_vocabularies = data.columns
        ## this line means, grab every single controlled vocabulary
        vocab_types = list(possible_vocabularies)

        def get_cv_from_list(lst):
            """
            Check a validations list from the data model.
            If there is a controlled vocabulary validation,
            return which category of controlled vocabulary it is.
            This will generally be applied to the validations col
            of the data model
            """
            try:
                for i in lst:
                    if "sv(" in i:
                        return i[4:-2]
            except TypeError:
                return None
            else:
                return None

        vocab_col_names = []
        data_model = self.data_model
        for dm_key in data_model.dm:
            df = data_model.dm[dm_key]
            df['vocab_name'] = df['validations'].apply(get_cv_from_list)
            lst = list(zip(df[df['vocab_name'].notnull()]['vocab_name'], df[df['vocab_name'].notnull()].index))
            # in lst, first value is the name of the controlled vocabulary
            # second value is the name of the dataframe column
            vocab_col_names.extend(lst)

        # vocab_col_names is now a list of tuples
        # consisting of the vocabulary name and the column name
        # i.e., (u'type', u'geologic_types')

        # remove duplicate col_names:
        vocab_col_names = sorted(set(vocab_col_names))
        # add in boolean category to controlled vocabularies
        bool_items = [{'item': True}, {'item': False}, {'item': 'true'},
                      {'item': 'false'}, {'item': 0}, {'item': 1}]
        series = Series({'label': 'Boolean', 'items': bool_items})
        data['boolean'] = series
        # use vocabulary name to get possible values for the column name
        for vocab in vocab_col_names[:]:
            if vocab[0] == "magic_table_column":
                vocab_col_names.remove(("magic_table_column", "table_column"))
                continue
            try:
                items = data[vocab[0]]['items']
            except:
                vocab_col_names.remove(vocab)
                continue
            items = data[vocab[0]]['items']
            stripped_list = [item['item'] for item in items]
            suggested_vocabularies.append(stripped_list)
        # create series with the column name as the index,
        # and the possible values as the values
        ind_values = [i[1] for i in vocab_col_names]
        vocabularies = pd.Series(suggested_vocabularies, index=ind_values)
        return vocabularies


    ## Get method codes and controlled vocabularies

    def get_all_vocabulary(self):
        all_codes, code_types = self.get_meth_codes()

        ## do it this way if you want a non-nested list of all codes
        ## i.e. er_codes = [code1, code2,...]
        ##def get_one_meth_category(category, all_codes, code_types):

        ## do it this way if you want a tiered list of all codes
        ## i.e. er_codes = {'anisotropy_codes': ['code1', 'code2'], ...}
        ##def get_tiered_meth_category(mtype, all_codes, code_types):

        if any(all_codes):
            methods = self.get_tiered_meth_category('other', all_codes, code_types)
            age_methods = self.get_tiered_meth_category('age', all_codes, code_types)
        else:
            methods = self.get_tiered_meth_category_offline()
            age_methods = self.get_tiered_meth_category_offline()
            path = os.path.join(data_model_dir, 'code_types.txt')
            with open(path, 'r') as type_file:
                raw_code_types = json.load(type_file)
            code_types = pd.read_json(raw_code_types, encoding='utf-8-sig')
            path = os.path.join(data_model_dir, 'all_codes.txt')
            with open(path, 'r') as code_file:
                raw_all_codes = json.load(code_file)
            all_codes = pd.read_json(raw_all_codes, encoding='utf-8-sig')

        vocabularies = self.get_controlled_vocabularies()
        suggested = self.get_suggested_vocabularies()
        self.vocabularies = vocabularies
        self.suggested = suggested
        self.all_codes = all_codes
        self.code_types = code_types
        self.methods = methods
        self.age_methods = age_methods
