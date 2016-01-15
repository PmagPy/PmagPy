#!/usr/bin/env python


# two files
# read each
# compare
# provide easy, readable diff

import sys
from numpy import isnan



f1 = sys.argv.index('-f1')
f2 = sys.argv.index('-f2')
path1 = sys.argv[f1+1]
path2 = sys.argv[f2+1]


def parse_file(file_path):
    """takes file and returns dictionary...."""
    file = open(file_path, 'rU')
    lines = file.readlines()
    categories = []
    data = []
    specimens = {}
    for line in lines[1:]: #
        d = line.split('\t')
        #print 'd        ', d
        data = []
        for i in d[:-1]: # empty space
            temp = i.split()
            #print "temp", temp
            categories.append(temp[0])
            data.append(temp[1])
        specimens[data[0]] = data
    return specimens, categories
    


def print_all(categories, specs1, specs2):
    for specimen in specs1.keys():
        #print "SPECIMEN: ", specimen
        data1 = specs1[specimen]
        data2 = specs2[specimen]
        for num, i in enumerate(data1):
            v1 = i
            v2 = data2[num]
            print categories1[num]
            print v1, v2
        print '--------'
        print '--------'


def append_if_not_present(lst, item):
    if item in lst:
        pass
    else:
        lst.append(item)

def add_to_dict(dct, item, value):
    try:
        dct[item]
    except KeyError:
        dct[item] = []
    dct[item].append(value)


problems = {}
def compare_all(categories, specs1, specs2):
    if sorted(specs1.keys()) == sorted(specs2.keys()):
        print "{} specimens compared".format(len(specs1.keys()))
        #pass
    else:
        print "first file specimens:", len(sorted(specs1.keys()))
        print "second file specimens:", len(sorted(specs2.keys()))
        print "specimens in file1 but not file2:", [spec for spec in specs1.keys() if spec not in specs2.keys()]
        print "specimens in file2 but not file1:", [spec for spec in specs2.keys() if spec not in specs1.keys()]
        print "--"
        print "--"
        raise NameError('different specimens detected')
    for specimen in specs1.keys():
        #print "SPECIMEN: ", specimen
        data1 = specs1[specimen]
        data2 = specs2[specimen]
        for num, i in enumerate(data1):
            v1 = i
            v2 = data2[num]
            str = False
            try:
                float(v1)
                n1 = round(float(v1), 1)
                n2 = round(float(v2), 1)
                #print "ROUNDED", r
            except ValueError as ex: # could not convert string to float
                #print ex
                str = True
            if not str:
                if isnan(float(v1)) and isnan(float(v2)):
                    #   print " SAME!"
                    break
            if str:
                if categories1[num] == 'SCAT:':
                    if bool(v1) == bool(v2):
                        pass
                    else:
                        add_to_dict(problems, categories1[num], specimen)
                        print categories1[num]
                        print v1, "------", v2
                elif v1 == v2:
                    pass
                else:
                    add_to_dict(problems, categories1[num], specimen)
                    print "SPECIMEN: ", specimen
                    print categories1[num]
                    print v1, "------", v2
                    print "--"
            elif round(n1,-1) != round(n2,-1):  # it's not a string, and not nan, and the values don't match
                add_to_dict(problems, categories1[num], specimen)
                print "SPECIMEN: ", specimen
                print categories1[num], categories2[num]
                print v1, "-----",  v2
                print n1, "-----", n2
                print "--"
            else:
                pass
                #print "same"
        #print "--"
    print "problems: {}".format(problems.keys())
    for k, v in problems.items():
        if len(v) < 100:
            print k, len(v)
        else:
            print k, ": lots"
    print "{} specimens compared".format(len(specs1.keys()))
    return problems



def compare_one_stat(stat, categories, specs1, specs2):
    print "comparing one"
    specimens = specs1.keys()
    i = categories.index(stat + ':')
    for spec in specimens:
        print str(spec) + ": " + str(stat)
        print specs1[spec][i], specs2[spec][i]


def compare_one_spec(spec, categories, specs1, specs2):
    print "mine, Greig's"
    for num, stat in enumerate(specs1[spec]):
        print categories[num]
        print specs1[spec][num],
        print specs2[spec][num]



specs1, categories1 = parse_file(path1)
specs2, categories2 = parse_file(path2)
if ('-spec' in sys.argv):
    ind = sys.argv.index('-spec')
    spec = sys.argv[ind+1]
    compare_one_spec(spec, categories1, specs1, specs2)
elif ('-stat' in sys.argv):
    single = sys.argv.index('-stat')
    stat = sys.argv[single+1]
    compare_one_stat(stat, categories1, specs1, specs2)
elif ('-a' in sys.argv):
    print_all(categories1, specs1, specs2)
else:
    compare_all(categories1, specs1, specs2)
#try:
#    single = sys.argv.index('-s')
#    stat = sys.argv[single+1]
#    compare_one_stat(stat, categories1, specs1, specs2)
#except ValueError as ex:
#    print ex

         
    
lori_only = ['y_prime', 'x_prime', 'delta_y_prime', 'delta_x_prime']
greig_only = ['Line_Len']
#print lori_only
#print greig_only
