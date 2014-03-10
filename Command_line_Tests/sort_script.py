#! /usr/bin/env python

import PmagPy_tests as PT

file_prefix = PT.file_prefix


def parse_files():
    rename = PT.file_parse_by_word(file_prefix + 'Rename_me.py')
    random = PT.file_parse_by_word(file_prefix + 'Random.py')
    bootstrap = PT.file_parse_by_word(file_prefix + 'Bootstrap.py')
    ex_out = PT.file_parse_by_word(file_prefix + 'Extra_output.py')
    return rename + random + bootstrap + ex_out


def trim_list(a_list):
    new_list = []
    for w in a_list:
        if 'complete' in w:
            new_list.append(w)
        else:
            pass
#            print w
    return new_list


def remove_duplicates(a_list):
    new_list = []
    for i in a_list:
        if i in new_list:
            pass
        elif i[-1] != ":":
            pass
        else:
            new_list.append(i)
    return new_list

the_list = parse_files()
print the_list
clean_list = trim_list(the_list)
print clean_list
final = remove_duplicates(clean_list)
#final = clean_list
final.sort()
total = 0
for i in final:
    total += 1
    print i
print total

