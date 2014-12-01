#!/usr/bin/env python

#print "this is the right module"


import urllib2
import pmag
import check_updates


def get_data_model():
    print "getting data model"
    url = 'http://earthref.org/services/MagIC-data-model.txt'
    try:
        data = urllib2.urlopen(url)
    except urllib2.URLError:
        try:
            pmag_dir = check_updates.get_pmag_dir()
            the_file = pmag_dir + "/MagIC-data-model.txt"
            data = open(the_file, 'rU')
        except:
            print "can't access MagIC-data-model at the moment\nif you are working offline, make sure MagIC-data-model.txt is in your PmagPy directory (or get it from https://github.com/ltauxe/PmagPy)\notherwise, check your internet connection"
            return False

    data_model = pmag.magic_read(None, data)
    ref_dicts = [d for d in data_model[0] if d['column_nmb'] != '>>>>>>>>>>' and d['column_nmb'] != 'tab delimited']
    complete_ref = {}
    for d in ref_dicts:
        complete_ref[d['field_name_oracle']] = {'data_type': d['data_type'], 'data_status': d['data_status']}
    return complete_ref


def read_upload(up_file):
    f = open(up_file)
    lines = f.readlines()
    f.close()
    data = split_lines(lines)
    data_dicts = get_dicts(data)
    missing_data = {}
    number_scramble = {}
    data_model = get_data_model()
    if not data_model:
        return False
    for dictionary in data_dicts:
        for k, v in dictionary.items():
            if k == "file_type": # meta data
                continue
            file_type = dictionary['file_type']

            missing = do_validate(k, v, data_model)
            if missing:
                if file_type not in missing_data.keys():
                    missing_data[file_type] = set()
                missing_data[file_type].add(missing)

            number_fail = do_num_validate(k, v, data_model)
            if number_fail:
                if file_type not in number_scramble.keys():
                    number_scramble[file_type] = set()
                number_scramble[file_type].add(number_fail)

    for file_type, wrong_cols in number_scramble.items():
        print "In your {} file, you must provide a valid number, in the following columns: {}".format(file_type, ', '.join(wrong_cols))

    for file_type, empty_cols in missing_data.items():
        print "In your {} file, you are missing data in the following required columns: {}".format(file_type, ', '.join(empty_cols))

    if number_scramble or missing_data:
        return False
    else:
        return True
    
    

def split_lines(lines):
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
        
        
def do_validate(key, value, complete_ref):
    reqd = complete_ref[key]['data_status']
    if reqd == 'Required':
        if not value or value == " ":
            return key
    return

def do_num_validate(key, value, complete_ref):
    dtype = complete_ref[key]['data_type']
    if value:
        if 'Number' in dtype:
            if not isinstance(value, (int, float)):
                try:
                    float(value)
                except ValueError:
                    return key
    return
