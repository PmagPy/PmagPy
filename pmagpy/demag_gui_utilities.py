from __future__ import print_function
from __future__ import absolute_import
from builtins import zip
from builtins import map
from builtins import range
import os
from wx import FileDialog
from re import findall,split
from numpy import array,arange,pi,cos,sin
from .pmag import dimap,cart2dir,dir2cart

def spec_cmp(s1,s2=''):
    if type(s1) != str and type(s2) != str: return 0
    elif type(s1) != str: return -1
    elif type(s2) != str: return 1
    sam_sp1 = split(r'[-,.]+',s1)
    sam_sp2 = split(r'[-,.]+',s2)
    for e1,e2 in zip(sam_sp1,sam_sp2):
        for c1,c2 in zip(e1,e2): #sort by letters
            if c1 != c2 and c1.isalpha() and c2.isalpha():
                return ord(c1)-ord(c2)
        l1 = list(map(int, findall('\d+', e1))) #retrieves numbers from names
        l2 = list(map(int, findall('\d+', e2)))
        for i1,i2 in zip(l1,l2): #sort by numbers
            if i1-i2 != 0:
                return i1-i2
    return 0

def meas_cmp(m1,m2):
    if not isinstance(m1,dict) and not isinstance(m2,dict): return 0
    elif not isinstance(m1,dict): return -1
    elif not isinstance(m2,dict): return 1
    spec_key,num_key,meth_key = 'er_specimen_name','measurement_number','magic_method_codes'
    if spec_key in list(m1.keys()) and spec_key in list(m2.keys()):
        if m1[spec_key] > m2[spec_key]: return 1
        elif m1[spec_key] < m2[spec_key]: return -1
    if num_key in list(m1.keys()) and num_key in list(m2.keys()):
        try: return int(m1[num_key]) - int(m2[num_key])
        except ValueError: print("measurement number sorting impossible as some measurement indecies are not numbers")
    if meth_key in list(m1.keys()) and meth_key in list(m2.keys()):
        m1_meths,m2_meths = m1[meth_key].split(':'),m2[meth_key].split(':')
        if 'LT-NO' in m1_meths and 'LT-NO' in m2_meths: return 0
        elif 'LT-NO' in m1_meths: return -1
        elif 'LT-NO' in m2_meths: return 1
    return 0

def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0  
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K

spec_key_func=cmp_to_key(spec_cmp)
meas_key_func=cmp_to_key(meas_cmp)

def read_LSQ(filepath):
    fin = open(filepath, 'r')
    interps = fin.read().splitlines()
    interps_out = []
    parse_LSQ_bound = lambda x: ord(x)-ord("A") if ord(x)-ord("A") < 26 else ord(x)-ord("A")-6
    for i,interp in enumerate(interps):
        interps_out.append({})
        enteries = interp.split()
        interps_out[i]['er_specimen_name'] = enteries[0]
        if enteries[1] == 'L':
            interps_out[i]['magic_method_codes'] = 'DE-BFL:DA-DIR-GEO'
        elif enteries[1] == 'P':
            interps_out[i]['magic_method_codes'] = 'DE-BFP:DA-DIR-GEO'
        elif enteries[1] == 'C':
            interps_out[i]['magic_method_codes'] = 'DE-FM:DA-DIR-GEO'
        else:
            interps_out[i]['magic_method_codes'] = ''
        j = 2
        if len(enteries) > 9: interps_out[i]['specimen_comp_name'] = enteries[j]; j += 1;
        else: interps_out[i]['specimen_comp_name'] = None
        interps_out[i]['specimen_dec'] = enteries[j]
        interps_out[i]['specimen_inc'] = enteries[j+1]
        j += 4
        bounds = enteries[j].split('-')
        lower = bounds[0]
        upper = bounds[-1]
        if len(bounds[0]) > 1: lower = lower[0]
        if len(bounds[-1]) > 1: upper = upper[-1]
        interps_out[i]['measurement_min_index'] = parse_LSQ_bound(lower)
        interps_out[i]['measurement_max_index'] = parse_LSQ_bound(upper)
        bad_meas = [bounds[k] for k in range(len(bounds)) if len(bounds[k]) > 1]
        for bad_m in bad_meas:
            if bad_m==bounds[-1] and len(bad_m)>2: bad_m = bad_m[:-1]
            elif bad_m==bounds[0] and len(bad_m)>2: bad_m = bad_m[1:]
            fc = parse_LSQ_bound(bad_m[0])
            lc = parse_LSQ_bound(bad_m[-1])
            interps_out[i]['bad_measurement_index'] = []
            for k in range(1,lc-fc):
                interps_out[i]['bad_measurement_index'].append(fc+k)
        try:
            interps_out[i]['specimen_n'] = enteries[j+1]
            interps_out[i]['specimen_mad'] = enteries[j+2]
        except IndexError: pass
    fin.close()
    return interps_out

def find_file(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)

def Rotate_zijderveld(Zdata,rot_declination):
    if len(Zdata)==0:
        return([])
    CART_rot=[]
    for i in range(0,len(Zdata)):
        DIR=cart2dir(Zdata[i])
        DIR[0]=(DIR[0]-rot_declination)%360.
        CART_rot.append(array(dir2cart(DIR)))
    CART_rot=array(CART_rot)
    return(CART_rot)

def draw_net(FIG):
    FIG.clear()
    eq=FIG
    eq.axis((-1,1,-1,1))
    eq.axis('off')
    theta=arange(0.,2*pi,2*pi/1000)
    eq.plot(cos(theta),sin(theta),'k',clip_on=False,lw=1)
    #eq.vlines((0,0),(0.9,-0.9),(1.0,-1.0),'k')
    #eq.hlines((0,0),(0.9,-0.9),(1.0,-1.0),'k')
    #eq.plot([0.0],[0.0],'+k')

    Xsym,Ysym=[],[]
    for I in range(10,100,10):
        XY=dimap(0.,I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    for I in range(10,90,10):
        XY=dimap(90.,I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    for I in range(10,90,10):
        XY=dimap(180.,I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    for I in range(10,90,10):
        XY=dimap(270.,I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    eq.plot(Xsym,Ysym,'k+',clip_on=False,mew=0.5)
    for D in range(0,360,10):
        Xtick,Ytick=[],[]
        for I in range(4):
            XY=dimap(D,I)
            Xtick.append(XY[0])
            Ytick.append(XY[1])
        eq.plot(Xtick,Ytick,'k',clip_on=False,lw=0.5)
    eq.axes.set_aspect('equal')
