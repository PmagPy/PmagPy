#!/usr/bin/env python
import sys
import random


import pylab
import pmagpy.pmag as pmag

def main():
    """
    NAME
        scalc.py

    DESCRIPTION
       calculates Sb from VGP Long,VGP Lat,Directional kappa,Site latitude data

    SYNTAX 
        scalc -h [command line options] [< standard input]
    
    INPUT 
       takes space delimited files with PLong, PLat,[kappa, N_site, slat]
    
    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file
        -c cutoff:  specify VGP colatitude cutoff value
        -k cutoff: specify kappa cutoff
        -v : use the VanDammme criterion 
        -a: use antipodes of reverse data: default is to use only normal
        -C:  use all data without regard to polarity
        -b: do a bootstrap for confidence
        -p: do relative to principle axis
    NOTES
        if kappa, N_site, lat supplied, will consider within site scatter
    OUTPUT
        N Sb  Sb_lower Sb_upper Co-lat. Cutoff
    """
    coord,kappa,cutoff="0",0,90.
    nb,anti,boot=1000,0,0
    all=0
    n=0
    v=0
    spin=1
    coord_key='tilt_correction'
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        in_file=sys.argv[ind+1]
        f=open(in_file,'rU')
        lines=f.readlines()
    else:
        lines=sys.stdin.readlines()
    if '-c' in sys.argv:
        ind=sys.argv.index('-c')
        cutoff=float(sys.argv[ind+1])
    if '-k' in sys.argv:
        ind=sys.argv.index('-k')
        kappa=float(sys.argv[ind+1])
    if '-n' in sys.argv:
        ind=sys.argv.index('-n')
        n=int(sys.argv[ind+1])
    if '-a' in sys.argv: anti=1
    if '-C' in sys.argv: cutoff=180. # no cutoff
    if '-b' in sys.argv: boot=1
    if '-v' in sys.argv: v=1
    if '-p' in sys.argv: spin=0
    #
    #
    # find desired vgp lat,lon, kappa,N_site data:
    #
    A,Vgps,slats,Pvgps=180.,[],[],[]
    for line in lines:
        if '\t' in line:
            rec=line.replace('\n','').split('\t') # split each line on space to get records
        else:
            rec=line.replace('\n','').split() # split each line on space to get records
        vgp={}
        vgp['vgp_lon'],vgp['vgp_lat']=rec[0],rec[1]
        Pvgps.append([float(rec[0]),float(rec[1])])
        if anti==1:
            if float(vgp['vgp_lat'])<0:
                vgp['vgp_lat']='%7.1f'%(-1*float(vgp['vgp_lat']))
                vgp['vgp_lon']='%7.1f'%(float(vgp['vgp_lon'])-180.)
        if len(rec)==5:
            vgp['average_k'],vgp['average_nn'],vgp['average_lat']=rec[2],rec[3],rec[4]
            slats.append(float(rec[4]))
        else: 
            vgp['average_k'],vgp['average_nn'],vgp['average_lat']="0","0","0"
        if 90.-(float(vgp['vgp_lat']))<=cutoff and float(vgp['average_k'])>=kappa and int(vgp['average_nn'])>=n: Vgps.append(vgp) 
    if spin==0: # do transformation to pole
        ppars=pmag.doprinc(Pvgps)
        for vgp in Vgps:
	    vlon,vlat=pmag.dotilt(float(vgp['vgp_lon']),float(vgp['vgp_lat']),ppars['dec']-180.,90.-ppars['inc'])
            vgp['vgp_lon']=vlon  
            vgp['vgp_lat']=vlat  
            vgp['average_k']="0"
    S_B= pmag.get_Sb(Vgps)
    A=cutoff
    if v==1:
        thetamax,A=181.,180.
        vVgps,cnt=[],0
        for vgp in Vgps:vVgps.append(vgp) # make a copy of Vgps
        while thetamax>A:
            thetas=[]
            A=1.8*S_B+5
            cnt+=1
            for vgp in vVgps:thetas.append(90.-(float(vgp['vgp_lat'])))
            thetas.sort()
            thetamax=thetas[-1]
            if thetamax<A:break
            nVgps=[]
            for  vgp in vVgps:
                if 90.-(float(vgp['vgp_lat']))<thetamax:nVgps.append(vgp)
            vVgps=[]
            for vgp in nVgps:vVgps.append(vgp) 
            S_B= pmag.get_Sb(vVgps)
        Vgps=[]
        for vgp in vVgps:Vgps.append(vgp) # make a new Vgp list
    SBs,Ns=[],[]
    if boot==1:
      print 'please be patient...   bootstrapping'
      for i in range(nb): # now do bootstrap 
        BVgps=[]
        for k in range(len(Vgps)):
            ind=random.randint(0,len(Vgps)-1)
            random.jumpahead(int(ind*1000))
            BVgps.append(Vgps[ind])
        SBs.append(pmag.get_Sb(BVgps))
      SBs.sort()
      low=int(.025*nb)
      high=int(.975*nb)
      print len(Vgps),'%7.1f %7.1f  %7.1f %7.1f '%(S_B,SBs[low],SBs[high],A)
    else:
      print len(Vgps),'%7.1f  %7.1f '%(S_B,A)
    if  len(slats)>2:
        stats= pmag.gausspars(slats)
        print 'mean lat = ','%7.1f'%(stats[0])

if __name__ == "__main__":
    main()
