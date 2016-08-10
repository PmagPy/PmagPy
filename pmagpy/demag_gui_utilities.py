import os
from re import findall,split
from pylab import arange,pi,cos,sin
from pmag import dimap

def specimens_comparator(s1,s2):
    sam_sp1 = split(r'[-,.]+',s1)
    sam_sp2 = split(r'[-,.]+',s2)
    for e1,e2 in zip(sam_sp1,sam_sp2):
        for c1,c2 in zip(e1,e2): #sort by letters
            if c1 != c2 and c1.isalpha() and c2.isalpha():
                return ord(c1)-ord(c2)
        l1 = map(int, findall('\d+', e1)) #retrieves numbers from names
        l2 = map(int, findall('\d+', e2))
        for i1,i2 in zip(l1,l2): #sort by numbers
            if i1-i2 != 0:
                return i1-i2
    return 0

def read_LSQ(filepath):
    fin = open(filepath, 'r')
    interps = fin.readlines()
    interps_out = []
    parse_LSQ_bound = lambda x: ord(x)-ord("A") if ord(x)-ord("A") < 25 else ord(x)-ord("A")-6
    for i,interp in enumerate(interps):
        interps_out.append({})
        enteries = interp.split()
        interps_out[i]['er_specimen_name'] = enteries[0]
        if enteries[1] == 'L':
            interps_out[i]['magic_method_codes'] = 'DE-BFL:DA-DIR-GEO'
        j = 2
        if len(enteries) > 9: interps_out[i]['specimen_comp_name'] = enteries[j]; j += 1;
        else: interps_out[i]['specimen_comp_name'] = None
        interps_out[i]['specimen_dec'] = enteries[j]
        interps_out[i]['specimen_inc'] = enteries[j+1]
        j += 4
        bounds = enteries[j].split('-')
        interps_out[i]['measurement_min_index'] = parse_LSQ_bound(bounds[0])
        interps_out[i]['measurement_max_index'] = parse_LSQ_bound(bounds[-1])
        bad_meas = [bounds[k] for k in range(len(bounds)) if len(bounds[k]) > 1]
        for bad_m in bad_meas:
             fc = parse_LSQ_bound(bad_m[0])
             lc = parse_LSQ_bound(bad_m[-1])
             interps_out[i]['bad_measurement_index'] = []
             for k in range(1,lc-fc+1):
                     interps_out[i]['bad_measurement_index'].append(fc+k)
        interps_out[i]['specimen_n'] = enteries[j+1]
        interps_out[i]['specimen_mad'] = enteries[j+2]
    fin.close()
    return interps_out

def find_file(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)

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
