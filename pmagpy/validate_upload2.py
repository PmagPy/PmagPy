#!/usr/bin/env python

import os

from . import pmag
from . import find_pmag_dir
from pmagpy.controlled_vocabularies2 import vocab

def get_data_offline():
    try:
        pmag_dir = find_pmag_dir.get_pmag_dir()
        the_file = os.path.join(pmag_dir, 'pmagpy', 'data_model', "MagIC-data-model.txt")
        # if using with py2app, the directory structure is flat,
        # so check to see where the resource actually is
        if not os.path.exists(the_file):
            the_file = os.path.join(pmag_dir, 'data_model', 'MagIC-data-model.txt')
        with open(the_file, 'r') as finput:
            return finput.readlines()
    except IOError:
        print("can't access MagIC-data-model at the moment\nif you are working offline, make sure MagIC-data-model.txt is in your PmagPy directory (or download it from https://github.com/ltauxe/PmagPy and put it in your PmagPy directory)\notherwise, check your internet connection")
        return False


def get_data_model():
    """
    try to grab the up to date data model document from the EarthRef site.
    if that fails, try to get the data model document from the PmagPy directory on the user's computer.
    if that fails, return False.
    data_model is a set of nested dictionaries that looks like this:
    {'magic_contributions':
        {'group_userid': {'data_status': 'Optional', 'data_type': 'String(10)'}, 'activate': {'data_status': 'Optional', 'data_type': 'String(1)'}, ....},
    'er_synthetics':
        {'synthetic_type': {'data_status': 'Required', 'data_type': 'String(50)'}, 'er_citation_names': {'data_status': 'Required', 'data_type': 'List(500)'}, ...},
    ....
    }
    the top level keys are the file types.
    the second level keys are the possible headers for that file type.
    the third level keys are data_type and data_status for that header.
    """
    #print("-I- getting data model, please be patient!!!!")
    url = 'http://earthref.org/services/MagIC-data-model.txt'
    offline = True # always get cached data model, as 2.5 is now static
    #try:
    #    data = urllib2.urlopen(url)
    #except urllib2.URLError:
    #    print '-W- Unable to fetch data model online\nTrying to use cached data model instead'
    #    offline = True
    #except httplib.BadStatusLine:
    #    print '-W- Website: {} not responding\nTrying to use cached data model instead'.format(url)
    #    offline = True
    if offline:
        data = get_data_offline()
    data_model, file_type = pmag.magic_read(None, data)
    if file_type in ('bad file', 'empty_file'):
        print('-W- Unable to read online data model.\nTrying to use cached data model instead')
        data = get_data_offline()
        data_model, file_type = pmag.magic_read(None, data)
    ref_dicts = [d for d in data_model if d['column_nmb'] != '>>>>>>>>>>']
    file_types = [d['field_name'] for d in data_model if d['column_nmb'] == 'tab delimited']
    file_types.insert(0, file_type)
    complete_ref = {}

    dictionary = {}
    n = 0
    for d in ref_dicts:
        if d['field_name'] in file_types:
            complete_ref[file_types[n]] = dictionary
            n += 1
            dictionary = {}
        else:
            dictionary[d['field_name_oracle']] = {'data_type': d['data_type'], 'data_status': d['data_status']}
    return complete_ref


def read_upload(up_file, data_model=None):
    """
    take a file that should be ready for upload
    using the data model, check that all required columns are full,
    and that all numeric data is in fact numeric.
    print out warnings for any validation problems
    return True if there were no problems, otherwise return False
    """
    print("-I- Running validation for your upload file")

    ## Read file
    f = open(up_file)
    lines = f.readlines()
    f.close()
    data = split_lines(lines)
    data_dicts = get_dicts(data)
    ## initialize
    invalid_data = {}
    missing_data = {}
    non_numeric = {}
    bad_vocab = {}
    bad_coords = {}
    invalid_col_names = {}
    missing_file_type = False
    ## make sure you have the data model
    if not data_model:
        data_model = get_data_model()
    reqd_file_types = ['er_locations']
    provided_file_types = set()
    if not data_model:
        return False, None
    ## Iterate through data
    # each dictionary is one tab delimited line in a csv file
    for dictionary in data_dicts:
        for k, v in list(dictionary.items()):
            if k == "file_type": # meta data
                provided_file_types.add(v)
                continue
            file_type = dictionary['file_type']
            # need to deal with pmag_criteria type file, too
            item_type = file_type.split('_')[1][:-1]
            if item_type == 'criteria':
                item_name = dictionary.get('criteria_definition')
            elif item_type == 'result':
                item_name = dictionary.get('pmag_result_name', None)
            elif item_type in ('specimen', 'sample', 'site', 'location'):
                item_name = dictionary.get('er_' + item_type + '_name', None)
            elif item_type == 'age':
                # get the lowest level er_*_name column that is filled in
                for dtype in ('specimen', 'sample', 'site', 'location'):
                    item_name = dictionary.get('er_' + dtype + '_name', None)
                    if item_name:
                        break
            elif item_type == 'measurement':
                exp_name = dictionary.get('magic_experiment_name')
                meas_num = dictionary.get('measurement_number')
                item_name = exp_name + '_' + str(meas_num)
            else:
                item_name = None

            if file_type not in list(data_model.keys()):
                continue
            specific_data_model = data_model[file_type]

            ## Function for building problems list
            def add_to_invalid_data(item_name, item_type, invalid_data,
                                    validation, problem_type):
                """
                correctly create or add to the dictionary of invalid values
                """
                if item_name:
                    if item_type not in invalid_data:
                        invalid_data[item_type] = {}
                    if item_name not in invalid_data[item_type]:
                        invalid_data[item_type][item_name] = {}
                    if problem_type not in invalid_data[item_type][item_name]:
                        invalid_data[item_type][item_name][problem_type] = []
                    invalid_data[item_type][item_name][problem_type].append(validation)

            ## Validate for each problem type

            # check if column header is in the data model
            invalid_col_name = validate_for_recognized_column(k, v, specific_data_model)
            if invalid_col_name:
                if item_type not in list(invalid_col_names.keys()):
                    invalid_col_names[item_type] = set()
                invalid_col_names[item_type].add(invalid_col_name)
                # skip to next item, as additional validations won't work
                # (key is not in the data model)

                ## new style
                add_to_invalid_data(item_name, item_type, invalid_data,
                                    invalid_col_name, 'invalid_col')
                # skip to next item, as additional validations won't work
                # (key is not in the data model)
                continue

            # make a list of missing, required data
            missing_item = validate_for_presence(k, v, specific_data_model)
            #print 'k, v', k, v
            if missing_item:
                if item_type not in list(missing_data.keys()):
                    missing_data[item_type] = set()
                missing_data[item_type].add(missing_item)
                if item_name:
                    # don't double count if a site is missing its parent location
                    if item_type == 'age' and missing_item == 'er_location_name':
                        pass
                    # ignore er_synthetic_name (data model is incorrect here)
                    if missing_item == 'er_synthetic_name':
                        pass
                    else:
                        add_to_invalid_data(item_name, item_type, invalid_data,
                                            missing_item, 'missing_data')

            # vocabulary problems
            vocab_problem = validate_for_controlled_vocab(k, v, specific_data_model)
            if vocab_problem:
                if item_type not in list(bad_vocab.keys()):
                    bad_vocab[item_type] = set()
                bad_vocab[item_type].add(vocab_problem)
                add_to_invalid_data(item_name, item_type, invalid_data,
                                    vocab_problem, 'vocab_problem')

            # illegal coordinates
            coord_problem = validate_for_coordinates(k, v, specific_data_model)
            if coord_problem:
                if item_type not in list(bad_coords.keys()):
                    bad_coords[item_type] = set()
                bad_coords[item_type].add(coord_problem)
                add_to_invalid_data(item_name, item_type, invalid_data,
                                    coord_problem, 'coordinates')

            # make a list of data that should be numeric, but aren't
            number_fail = validate_for_numericality(k, v, specific_data_model)
            if number_fail:
                if item_type not in list(non_numeric.keys()):
                    non_numeric[item_type] = set()
                non_numeric[item_type].add(number_fail)
                add_to_invalid_data(item_name, item_type, invalid_data,
                                    number_fail, 'number_fail')

    ## Print out all issues

    for file_type, invalid_names in list(invalid_col_names.items()):
        print("-W- In your {} file, you are using the following unrecognized columns: {}".format(file_type, ', '.join(invalid_names)))

    for file_type, wrong_cols in list(non_numeric.items()):
        print("-W- In your {} file, you must provide only valid numbers, in the following columns: {}".format(file_type, ', '.join(wrong_cols)))

    for file_type, empty_cols in list(missing_data.items()):
        print("-W- In your {} file, you are missing data in the following required columns: {}".format(file_type, ', '.join(empty_cols)))

    for file_type in reqd_file_types:
        if file_type not in provided_file_types:
            print("-W- You have not provided a(n) {} type file, which is required data".format(file_type))
            missing_file_type = True

    for file_type, vocab_types in list(bad_vocab.items()):
        print("-W- In your {} file, you are using an unrecognized value for these controlled vocabularies: {}".format(file_type, ', '.join(vocab_types)))

    for file_type, coords in list(bad_coords.items()):
        print("-W- In your {} file, you are using an illegal value for these columns: {}.  (Latitude must be between -90 and +90)".format(file_type, ', '.join(coords)))


    if any((invalid_col_names, non_numeric, missing_data, missing_file_type, bad_vocab, bad_coords)):
        return False, invalid_data
    else:
        print("-I- validation was successful")
        return True, None


def split_lines(lines):
    """
    split a MagIC upload format file into lists.
    the lists are split by the '>>>' lines between file_types.
    """
    container = []
    new_list = []
    for line in lines:
        if '>>>' in line:
            container.append(new_list)
            new_list = []
        else:
            new_list.append(line)
    container.append(new_list)
    return container


def get_dicts(data):
    """
    data must be a list of lists, from a tab delimited file.
    in each list:
    the first list item will be the type of data.
    the second list item will be a tab delimited list of headers.
    the remaining items  will be a tab delimited list following the list of headers.
    """
    data_dictionaries = []
    for chunk in data[:-1]:
        if not chunk:
            continue
        data1 = data[0]
        file_type = chunk[0].split('\t')[1].strip('\n').strip('\r')
        keys = chunk[1].split('\t')
        clean_keys = []

        # remove new-line characters, and any empty string keys
        for key in keys:
            clean_key = key.strip('\n').strip('\r')
            if clean_key:
                clean_keys.append(clean_key)
        for line in chunk[2:]:
            data_dict = {}
            for key in clean_keys:
                data_dict[key] = ""
            line = line.split('\t')
            for n, key in enumerate(clean_keys):
                data_dict[key] = line[n].strip('\n').strip('\r')
            data_dict['file_type'] = file_type
            data_dictionaries.append(data_dict)
    return data_dictionaries



def validate_for_recognized_column(key, value, complete_ref):
    if not key in complete_ref:
        return key
    return


def validate_for_presence(key, value, complete_ref):
    reqd = complete_ref[key]['data_status']
    if reqd == 'Required':
        if not value or value == " ":
            return key
    return

def validate_for_numericality(key, value, complete_ref):
    dtype = complete_ref[key]['data_type']
    if value:
        if 'Number' in dtype:
            if not isinstance(value, (int, float)):
                try:
                    float(value)
                except ValueError:
                    return key
    return


def validate_for_controlled_vocab(key, value, complete_ref):

    if not any(vocab.vocabularies):
        vocab.get_all_vocabulary()
    #
    cv = False
    stripped_key = ''
    for level in ['specimen_', 'sample_', 'site_']:
        if key.startswith(level):
            #stripped_key = key.strip(level)
            stripped_key = key[len(level):]
            break
    #print 'key', key
    #print 'stripped_key', stripped_key
    if key in vocab.possible_vocabularies or key in vocab.vocabularies:
        cv = True
    elif stripped_key in vocab.possible_vocabularies or stripped_key in vocab.vocabularies:
        cv = True
        key = stripped_key
        #return key

    #if there is a controlled vocabulary for the given header,
    # check and see if all values provided are legitimate
    if cv:
        # make sure colon-delimited lists are split
        values = value.split(':')
        values = [v.strip() for v in values]
        #print 'key', key
        #print 'values', values

        ## Not anymore
        # if we don't have the options for the needed controlled vocabulary,
        # fetch them from earthref
        #if key not in vocab.vocabularies:
        #    add = vocab.get_controlled_vocabularies((key,))
        #    vocab.vocabularies = pd.concat((vocab.vocabularies, add[0]), sort=True)

        ## for each value from a controlled vocabulary header,
        ## make sure it is within the controlled vocabulary list
        ## and that the value is not null
        for val in values:
            if val not in vocab.vocabularies[key] and val:
                if isinstance(vocab.vocabularies[key], dict):
                    if val not in vocab.vocabularies[key][val[0].upper()]:
                        return key
                else:
                    return key


def validate_for_coordinates(key, value, complete_ref):
    keys = ['location_begin_lat', 'location_end_lat',
            'location_begin_lon', 'location_end_lon']
    # see if it is lat/lon
    if key not in keys:
        return
    # if it is lat/lon, see if it is a float
    try:
        val = float(value)
    except ValueError:
        return key
    # then, see if it is a float within proper bounds
    if 'lat' in key:
        if not -90. < val < 90.:
            return key
    if 'lon' in key:
        if not 0 < val < 360.:
            return key
