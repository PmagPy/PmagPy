#!/usr/bin/env python
from __future__ import print_function
from __future__ import absolute_import
from builtins import object
import pandas as pd
from pandas import Series
import json
import os
from . import find_pmag_dir
pmag_dir = find_pmag_dir.get_pmag_dir()
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

    def get_tiered_meth_category_offline(self, category):
        path = os.path.join(data_model_dir, '{}_methods.txt'.format(category))
        dfile = open(path)
        json_data = json.load(dfile)
        dfile.close()
        return json_data

    def get_meth_codes(self):
        print('-I- Getting cached method codes for 2.5')
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
        self.er_methods = er_methods
        self.pmag_methods = pmag_methods
        self.age_methods = age_methods
        self.all_codes = all_codes
        self.code_types = code_types

    def get_vocabularies(self):
        print('-I- Getting cached controlled vocabularies for 2.5')
        ## skip trying to get method codes etc. dynamically.
        ## 2.5 method codes etc. are no longer available on earthref
        #all_codes, code_types = self.get_meth_codes()
        #if any(all_codes):
        #    er_methods = self.get_tiered_meth_category('er', all_codes, code_types)
        #    pmag_methods = self.get_tiered_meth_category('pmag', all_codes, code_types)
        #     age_methods = self.get_tiered_meth_category('age', all_codes, code_types)
        #else:
        #
        # method codes

        # controlled vocabularies
        path = os.path.join(data_model_dir, 'controlled_vocabularies2.json')
        with open(path, 'r') as code_file:
            raw_vocabularies = json.load(code_file)
        vocabularies = dict([(k, v) for k, v in raw_vocabularies.items()])
        self.vocabularies = vocabularies
        self.possible_vocabularies = vocabularies

    def get_all_vocabulary(self):
        self.get_vocabularies()
        self.get_meth_codes()


vocab = Vocabulary()
