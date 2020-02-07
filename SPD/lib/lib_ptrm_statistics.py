#!/usr/bin/env python

from __future__ import division
from __future__ import absolute_import
from past.utils import old_div
import numpy
from . import lib_directional_statistics as lib_direct

numpy.set_printoptions(precision=15)

def get_n_ptrm(tmin, tmax, ptrm_temps, ptrm_starting_temps):
    """
    input: tmin, tmax, ptrm_temps, ptrm_starting_temps
    returns number of ptrm_checks included in best fit segment.
    excludes checks if temp exceeds tmax OR if starting temp exceeds tmax.
    output: n_ptrm, ptrm_checks_included_temperatures
    """
    # does not exclude ptrm checks that are less than tmin
    ptrm_checks_included_temps= []
    for num, check in enumerate(ptrm_temps):
        if check > tmax:
            pass
        elif ptrm_starting_temps[num] > tmax: # or ptrm_starting_temps[num] < tmin:
            pass
        else:
            ptrm_checks_included_temps.append(check)
    return len(ptrm_checks_included_temps), ptrm_checks_included_temps

def get_max_ptrm_check(ptrm_checks_included_temps, ptrm_checks_all_temps, ptrm_x, t_Arai, x_Arai):
    """
    input: ptrm_checks_included_temps, ptrm_checks_all_temps, ptrm_x, t_Arai, x_Arai.
    sorts through included ptrm_checks and finds the largest ptrm check diff,
    the sum of the total diffs,
    and the percentage of the largest check / original measurement at that temperature step
    output: max_diff, sum_diffs, check_percent, sum_abs_diffs.
    """
    if not ptrm_checks_included_temps:
        return [], float('nan'), float('nan'), float('nan'), float('nan')
    diffs = []
    abs_diffs = []
    x_Arai_compare = []
    ptrm_compare = []
    check_percents = []
    ptrm_checks_all_temps = list(ptrm_checks_all_temps)
    for check in ptrm_checks_included_temps: # goes through each included temperature step
        ptrm_ind = ptrm_checks_all_temps.index(check) # indexes the number of the check
        ptrm_check = ptrm_x[ptrm_ind] # x value at that temperature step
        ptrm_compare.append(ptrm_check) #
        arai_ind = t_Arai.index(check)
        ptrm_orig = x_Arai[arai_ind]
        x_Arai_compare.append(ptrm_orig)
        diff = ptrm_orig - ptrm_check
        diffs.append(diff)
        abs_diffs.append(abs(diff))
        if ptrm_orig == 0:
            check_percents.append(0)
        else:
            check_percents.append((old_div(abs(diff), ptrm_orig)) * 100)
    max_diff = max(abs_diffs)
    check_percent = max(check_percents)
    sum_diffs = abs(sum(diffs))
    sum_abs_diffs = sum(abs_diffs)
    return diffs, max_diff, sum_diffs, check_percent, sum_abs_diffs


def get_delta_CK(max_ptrm_check, x_int):
    """
    Input: max_ptrm_check, x intercept.
    Output: delta_CK (max ptrm check normed by x intercept)
    """
    return abs(old_div(max_ptrm_check, x_int)) * 100.

def get_DRAT(delta_x_prime, delta_y_prime, max_ptrm_check):
    """
    Input: TRM length of best fit line (delta_x_prime),
        NRM length of best fit line,
        max_ptrm_check
    Output: DRAT (maximum difference produced by a ptrm check normed by best fit line),
        length best fit line
    """
    L = numpy.sqrt(delta_x_prime**2 + delta_y_prime**2)
    DRAT = (old_div(max_ptrm_check, L)) * 100
    return DRAT, L

def get_length_best_fit_line(delta_x_prime, delta_y_prime):
    L = numpy.sqrt(delta_x_prime**2 + delta_y_prime**2)
    return L

def get_max_DEV(delta_x_prime, max_ptrm_check):
    """
    input: delta_x_prime, max_ptrm_check
    output: max_DEV (maximum ptrm check diff normed by TRM line
    """
    return (old_div(max_ptrm_check, delta_x_prime)) * 100.

def get_CDRAT(L, sum_ptrm_checks, sum_abs_ptrm_checks):
    """
    input: best_fit line length, sum of ptrm check diffs,
        sum of absolute value of ptrm check diffs
    output: CDRAT (uses sum of diffs), CDRAT_prime (uses sum of absolute diffs)
    """
    CDRAT = (old_div(sum_ptrm_checks, L)) * 100.
    CDRAT_prime = (old_div(sum_abs_ptrm_checks, L)) * 100.
    return CDRAT, CDRAT_prime

def get_DRATS(sum_ptrm_checks, sum_abs_ptrm_checks, x_Arai, end):
    """
    input: sum of ptrm check diffs, sum of absolute value of ptrm check diffs,
        x_Arai set of points, end.
    output: DRATS (uses sum of diffs), DRATS_prime (uses sum of absolute diffs)
    """
    DRATS = (old_div(sum_ptrm_checks, x_Arai[end])) * 100.
    DRATS_prime = (old_div(sum_abs_ptrm_checks, x_Arai[end])) * 100.
    return DRATS, DRATS_prime

def get_mean_DRAT(sum_ptrm_checks, sum_abs_ptrm_checks, n_pTRM, L):
    """
    input: sum_ptrm_checks, sum_abs_ptrm_checks, n_pTRM, L
    output: mean DRAT (the average difference produced by a pTRM check,
    normalized by the length of the best-fit line)
    """
    if not n_pTRM:
        return float('nan'), float('nan')
    mean_DRAT = ((old_div(1., n_pTRM)) * (old_div(sum_ptrm_checks, L))) * 100
    mean_DRAT_prime = ((old_div(1., n_pTRM)) * (old_div(sum_abs_ptrm_checks, L))) * 100
    return mean_DRAT, mean_DRAT_prime

def get_mean_DEV(sum_ptrm_checks, sum_abs_ptrm_checks, n_pTRM, delta_x_prime):
    """
    input: sum_ptrm_checks, sum_abs_ptrm_checks, n_pTRM, delta_x_prime
    output: Mean deviation of a pTRM check
    """
    if not n_pTRM:
        return float('nan'), float('nan')
    mean_DEV = ((old_div(1., n_pTRM)) * (old_div(sum_ptrm_checks, delta_x_prime))) * 100
    mean_DEV_prime= ((old_div(1., n_pTRM)) * (old_div(sum_abs_ptrm_checks, delta_x_prime))) * 100
    return mean_DEV, mean_DEV_prime

def get_delta_pal_vectors(PTRMS, PTRM_Checks, NRM):
    """ takes in PTRM data in this format: [temp, dec, inc, moment, ZI or IZ] -- and PTRM_check data in this format: [temp, dec, inc, moment].  Returns them in vector form (cartesian). """
    PTRMS = numpy.array(PTRMS)
    PTRM_Checks = numpy.array(PTRM_Checks)
    TRM_1 = lib_direct.dir2cart(PTRMS[0,1:3])
    PTRMS_cart = []
    Checks_cart = []
    for num, ptrm in enumerate(PTRMS):
        #ptrm_cart = lib_direct.dir2cart([PTRMS[num][1], PTRMS[num][2], old_div(PTRMS[num][3], NRM)])
        ptrm_cart = lib_direct.dir2cart([PTRMS[num][1], PTRMS[num][2], PTRMS[num][3]/NRM])
        PTRMS_cart.append(ptrm_cart)
    for num, check in enumerate(PTRM_Checks):
        #check_cart = lib_direct.dir2cart([PTRM_Checks[num][1], PTRM_Checks[num][2], old_div(PTRM_Checks[num][3], NRM)])
        check_cart = lib_direct.dir2cart([float(PTRM_Checks[num][1]), float(PTRM_Checks[num][2]), float(PTRM_Checks[num][3])/ NRM])
        Checks_cart.append(check_cart)
    return PTRMS_cart, Checks_cart, TRM_1

def get_diffs(ptrms_vectors, ptrm_checks_vectors, ptrms_orig, checks_orig):
    """
    input: ptrms_vectors, ptrm_checks_vectors, ptrms_orig, checks_orig
    output: vector diffs between original and ptrm check, C
    """
    ptrm_temps = numpy.array(ptrms_orig)[:,0]
    check_temps = numpy.array(checks_orig)[:,0]
    index = numpy.zeros(len(ptrm_temps))
    for num, temp in enumerate(ptrm_temps):
        if len(numpy.where(check_temps == temp)[0]):
            index[num] = numpy.where(check_temps == temp)[0][0]
        else:
            index[num] = float('nan')
    diffs = numpy.zeros((len(ptrms_vectors), 3))
    for num, ptrm in enumerate(ptrms_vectors):
        if numpy.isnan(index[num]):
            diffs[num] = numpy.array([0,0,0])
        else:
            diffs[num] = ptrm_checks_vectors[int(index[num])] - ptrm
    C = numpy.cumsum(diffs, 0)
    #print "diffs (should be same as to_sum"
    #print diffs
    #print "C (should be same as dpal_sum)"
    #print C
    return diffs, C

def get_TRM_star(C, ptrms_vectors, start, end):
    """
    input: C, ptrms_vectors, start, end
    output: TRM_star, x_star (for delta_pal statistic)
    """
    TRM_star = numpy.zeros([len(ptrms_vectors), 3])
    TRM_star[0] = [0., 0., 0.]
    x_star = numpy.zeros(len(ptrms_vectors))
    for num, vec in enumerate(ptrms_vectors[1:]):
        TRM_star[num+1] = vec + C[num]
       # print 'vec', vec
       # print 'C', C[num]
    for num, trm in enumerate(TRM_star):
        x_star[num] = numpy.linalg.norm(trm)
    #print "x_star (should match corr_TRM / NRM)"
    #print x_star[start:end+1]
    return TRM_star[start:end+1], x_star[start:end+1]

def get_b_star(x_star, y_err, y_mean, y_segment):
    """
    input: x_star, y_err, y_mean, y_segment
    output: b_star (corrected slope for delta_pal statistic)
    """
    #print "x_star, should be same as Xcorr / NRM"
    #print x_star
    x_star_mean = numpy.mean(x_star)
    x_err = x_star - x_star_mean
    b_star = -1* numpy.sqrt( old_div(sum(numpy.array(y_err)**2), sum(numpy.array(x_err)**2)) )  # averaged slope
    #print "y_segment", y_segment
    b_star = numpy.sign(sum(x_err * y_err)) * numpy.std(y_segment, ddof=1) / numpy.std(x_star, ddof=1)
    #print "b_star (should be same as corr_slope)"
    #print b_star
    return b_star

# check delta pal
def get_delta_pal(b, b_star):
    """
    input: b, b_star (actual and corrected slope)
    output: delta_pal
    """
    delta_pal = numpy.abs(old_div((b - b_star), b)) * 100
    return delta_pal

# check delta pal
def get_full_delta_pal(PTRMS, PTRM_Checks, NRM, y_err, y_mean, b, start, end, y_segment):
    """
    input: PTRMS, PTRM_Checks, NRM, y_err, y_mean, b, start, end, y_segment
    runs full sequence necessary to get delta_pal
    """
    #print "-------"
    #print "calling get_full_delta_pal in lib"
#    return 0
    PTRMS_cart, checks, TRM_1 = get_delta_pal_vectors(PTRMS, PTRM_Checks, NRM)
#    print "PTRMS_Cart", PTRMS_cart
    diffs, C = get_diffs(PTRMS_cart, checks, PTRMS, PTRM_Checks)
#    print "C", C
    TRM_star, x_star = get_TRM_star(C, PTRMS_cart, start, end)
#    print "x_star", x_star
#    print type(x_star)
    b_star = get_b_star(x_star, y_err, y_mean, y_segment)
    delta_pal = get_delta_pal(b, b_star)
    return delta_pal

def get_segments(ptrms, ptrm_checks, tmax):
    """
    input: ptrms, ptrm_checks, tmax
    grabs ptrms that are done below tmax
    grabs ptrm checks that are done below tmax AND whose starting temp is below tmax
    output: ptrms_included, checks_included
    """
    ptrms_included = []
    checks_included = []
    ptrms = numpy.array(ptrms)
    for ptrm in ptrms:
        if ptrm[0] <= tmax:
            ptrms_included.append(ptrm)
    for check in ptrm_checks:
        if check[0] <= tmax:
            checks_included.append(check)
    #print "checks", ptrm_checks
    #print "checks_included", checks_included
    return ptrms_included, checks_included
