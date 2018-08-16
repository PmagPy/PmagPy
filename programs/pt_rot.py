#!/usr/bin/env python
# define some variables
from __future__ import print_function
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.frp as frp

def main():
    """
    NAME 
        pt_rot.py 

    DESCRIPTION
        rotates pt according to specified age and plate
 
    SYNTAX
        pt_rot.py [command line options]

    OPTIONS
        -h prints help and quits
        -f file with lon lat plate age Dplate as space delimited input
           Dplate is the destination plate coordinates desires 
           - default is "fixed south africa"
           Dplate should be one of: [nwaf, neaf,saf,aus, eur, ind, sam, ant, grn, nam]
        -ff file Efile,   file  has lat lon data file and Efile has sequential rotation poles: Elat Elon Omega 
        -F OFILE, output sites (pmag_results) formatted file with rotated points stored in pole_lon, pole_lat (vgp_lon, vgp_lat).  (data_model=2.5)
           default is to print out rotated lon, lat to standard output
        -dm [2.5,3] set data model for output.  Default is 3 
    """
    dir_path='.'
    PTS=[]
    ResRecs=[]
    ofile=""
    data_model=3
    Dplates=['nwaf', 'neaf','saf','aus', 'eur', 'ind', 'sam', 'ant', 'grn', 'nam']
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-F' in sys.argv:
        ind = sys.argv.index('-F')
        ofile=dir_path+'/'+sys.argv[ind+1]
    if '-dm' in sys.argv:
        ind = sys.argv.index('-dm')
        data_model=dir_path+'/'+sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        file=dir_path+'/'+sys.argv[ind+1]
        f=open(file,'r')
        data=f.readlines()
    elif '-ff' in sys.argv:
        ind = sys.argv.index('-ff')
        file=dir_path+'/'+sys.argv[ind+1]
        f=open(file,'r')
        data=f.readlines()
        Efile=dir_path+'/'+sys.argv[ind+2]
        f=open(Efile,'r')
        edata=f.readlines()
        Poles=[]
        for p in edata:
             rec=p.split()
             pole=[float(rec[0]),float(rec[1]),float(rec[2])] # pole is lat/lon/omega
             Poles.append(pole)
    else:
        data=sys.stdin.readlines()
    polelatkey,polelonkey='pole_lat','pole_lon'
    if data_model!=3:
        polelatkey,polelonkey='vgp_lat','vgp_lon'
    for line in data:
        PtRec={}
        rec=line.split()
        PtRec['site_lon']=rec[0]
        PtRec['site_lat']=rec[1]
        if '-ff' in sys.argv:
            pt_lat,pt_lon=float(rec[1]),float(rec[0])
            for pole in Poles:
                ptrot= pmag.pt_rot(pole,[pt_lat],[pt_lon])
                pt_lat=ptrot[0][0]
                pt_lon=ptrot[1][0]
            if ofile=="":
                print(ptrot[1][0], ptrot[0][0])
            else:
                ResRec={polelonkey: '%7.1f'%(ptrot[0][0]),polelatkey:'%7.1f'%( ptrot[1][0])}
                ResRecs.append(ResRec)
        else:
            PtRec['cont']=rec[2]
            if PtRec['cont']=='af':PtRec['cont']='saf' # use fixed south africa
            PtRec['age']=rec[3]
            if len(rec)>4:
               PtRec['dcont']=rec[4]
            PTS.append(PtRec)
    if '-ff' not in sys.argv:
        for pt in PTS:
            pole='not specified'
            pt_lat=float(pt['site_lat'])
            pt_lon=float(pt['site_lon'])
            age=float(pt['age'])
            ptrot=[[pt_lat],[pt_lon]]
            if pt['cont']=='ib':
                pole=frp.get_pole(pt['cont'],age)
                ptrot= pmag.pt_rot(pole,[pt_lat],[pt_lon])
                pt_lat=ptrot[0][0]
                pt_lon=ptrot[1][0]
                pt['cont']='eur'
            if pt['cont']!='saf':
                pole1=frp.get_pole(pt['cont'],age)
                ptrot= pmag.pt_rot(pole1,[pt_lat],[pt_lon])
                if 'dcont' in list(pt.keys()):
                    pt_lat=ptrot[0][0]
                    pt_lon=ptrot[1][0]
                    pole=frp.get_pole(pt['dcont'],age)
                    pole[2]=-pole[2] 
                    ptrot= pmag.pt_rot(pole,[pt_lat],[pt_lon])
                if ofile=="":
                    print(ptrot[1][0], ptrot[0][0])
                else:
                    ResRec={polelonkey: '%7.1f'%(ptrot[0][0]),polelatkey:'%7.1f'%( ptrot[1][0])}
                    ResRecs.append(ResRec)
            else:
                if 'dcont' in list(pt.keys()):
                    pole=frp.get_pole(pt['dcont'],age)
                    pole[2]=-pole[2] 
                    ptrot= pmag.pt_rot(pole,[pt_lat],[pt_lon])
                    print(ptrot)
                    if ofile=="":
                        print(ptrot[1][0], ptrot[0][0]) 
                    else:
                        ResRec={polelonkey: '%7.1f'%(ptrot[0][0]),polelatkey:'%7.1f'%( ptrot[1][0])}
                        ResRecs.append(ResRec)
                else:
                    if ofile=="":
                        print(ptrot[1][0], ptrot[0][0])
                    else:
                        ResRec={polelonkey: '%7.1f'%(ptrot[0][0]),polelatkey:'%7.1f'%( ptrot[1][0])}
                        ResRecs.append(ResRec)
    if len(ResRecs)>0:
        if data_model==3:
            pmag.magic_write(ofile,ResRecs,'locations')
        else:
            pmag.magic_write(ofile,ResRecs,'pmag_results')

if __name__ == "__main__":
    main()
