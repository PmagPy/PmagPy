#!/usr/bin/env python

import numpy



def get_n_add(temps, starting_temps, tmax):
    incl_temps = []
    for num, temp in enumerate(temps):
        if temp <= tmax and starting_temps[num] <= tmax:
            incl_temps.append(temp)
    n_add = len(incl_temps)
    if n_add < 1:
        n_add = float('NaN')
    return incl_temps, n_add

#lib_add.get_delta_AC(self.ref_incl_temps, self.add_checks, self.x_int)
def get_delta_AC(n_add, add_checks, x_int):
    if n_add > 0:
        incl_add_checks = numpy.array(add_checks[ :n_add])
        #print "checks segment", incl_add_checks
        #print "n_add", n_add
        #print "x_int", x_int
        #print "(abs(incl_add_checks)", (abs(incl_add_checks))
        #print "( max(abs(incl_add_checks) ) ", ( max(abs(incl_add_checks) ) )
        delta_AC = ( max(abs(incl_add_checks) ) / abs(x_int))  * 100.
        #print delta_AC
    else:
        incl_add_checks = 0
        delta_AC = float('NaN')
    return delta_AC, incl_add_checks


ignore = """
#probs ignore all below
def get_ptrm_star(incl_temps, starting_temps, x_Arai, t_Arai):
    ptrm_star = {}
    for num, temp in enumerate(incl_temps):
        starting_temp = starting_temps[num]
        k = (starting_temps[num], temp)
        ind_temp = t_Arai.index(temp)
        ind_start_temp = t_Arai.index(starting_temp)
        v = x_Arai[ind_start_temp] - x_Arai[ind_temp]
        ptrm_star[k] = v
    return ptrm_star


def get_ptrm_actual(incl_temps, starting_temps, x_Arai, t_Arai, x_add_check):
   # get_ptrm_actual(self.ref_incl_temps, self.starting_temps,self.x_Arai, self.t_Arai, self.x_add_check)
    ptrm_actual = {}
    for num, temp in enumerate(incl_temps):
        starting_temp = starting_temps[num]
        k = (starting_temps[num], temp)
        ind_temp = t_Arai.index(temp)
        ind_start_temp = t_Arai.index(starting_temp)
        v = x_Arai[ind_start_temp] - x_add_check[num]
        ptrm_actual[k] = v
    return ptrm_actual

def get_add_checks(ptrm_star, ptrm_actual):
    add_checks = {}
        
    return {(2,1): 0, (3,2): 0, (4,3): 0}


def get_max_ptrm_check(ptrm_checks_included_temps, ptrm_checks_all_temps, ptrm_x, t_Arai, x_Arai):
    #sorts through included ptrm_checks and finds the largest ptrm check diff, the sum of the total diffs, and the percentage of the largest check / original measurement at that temperature step#
    diffs = []
    abs_diffs = []
    x_Arai_compare = []
    ptrm_compare = []
    check_percents = []
    ptrm_checks_all_temps = list(ptrm_checks_all_temps)
    for check in ptrm_checks_included_temps: # goes through each included temperature step
        ptrm_ind = ptrm_checks_all_temps.index(check) # indexes the number of the 
        ptrm_check = ptrm_x[ptrm_ind] # x value at that temperature step
        ptrm_compare.append(ptrm_check) #                                                                       
        arai_ind = t_Arai.index(check)
        ptrm_orig = x_Arai[arai_ind]
        x_Arai_compare.append(ptrm_orig)
        diff = ptrm_orig - ptrm_check
        diffs.append(diff)
        abs_diffs.append(abs(diff))
        check_percents.append((abs(diff) / ptrm_orig) * 100)
#    print "ptrm_checks_included_temps", ptrm_checks_included_
#    print "x_Arai_compare", x_Arai_compare
#    print "diffs", diffs                                                                                                
    max_diff = max(abs_diffs)
    check_percent = max(check_percents)
    sum_diffs = abs(sum(diffs))

"""
