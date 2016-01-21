#!/usr/bin/env python
import sys
import random
import pmagpy.pmag as pmag

def main():
    """
    NAME
        scalc_magic.py

    DESCRIPTION
       calculates Sb from pmag_results files

    SYNTAX 
        scalc_magic -h [command line options]
    
    INPUT 
       takes magic formatted pmag_results table
       pmag_result_name must start with "VGP: Site"
       must have average_lat if spin axis is reference
    
    OPTIONS
        -h prints help message and quits
        -f FILE: specify input results file, default is 'pmag_results.txt'
        -c cutoff:  specify VGP colatitude cutoff value
        -k cutoff: specify kappa cutoff
        -crd [s,g,t]: specify coordinate system, default is geographic
        -v : use the VanDammme criterion 
        -a: use antipodes of reverse data: default is to use only normal
        -C: use all data without regard to polarity
        -r:  use reverse data only
        -p: do relative to principle axis
        -b: do bootstrap confidence bounds

     OUTPUT:
         if option -b used: N,  S_B, lower and upper bounds
         otherwise: N,  S_B, cutoff
    """
    in_file='pmag_results.txt'
    coord,kappa,cutoff="0",1.,90.
    nb,anti,spin,v,boot=1000,0,1,0,0
    coord_key='tilt_correction'
    rev=0
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        in_file=sys.argv[ind+1]
    if '-c' in sys.argv:
        ind=sys.argv.index('-c')
        cutoff=float(sys.argv[ind+1])
    if '-k' in sys.argv:
        ind=sys.argv.index('-k')
        kappa=float(sys.argv[ind+1])
    if '-crd' in sys.argv:
        ind=sys.argv.index("-crd")
        coord=sys.argv[ind+1]
        if coord=='s':coord="-1"
        if coord=='g':coord="0"
        if coord=='t':coord="100"
    if '-a' in sys.argv: anti=1
    if '-C' in sys.argv: cutoff=180. # no cutoff
    if '-r' in sys.argv: rev=1
    if '-p' in sys.argv: spin=0
    if '-v' in sys.argv: v=1
    if '-b' in sys.argv: boot=1
    data,file_type=pmag.magic_read(in_file)
    #
    #
    # find desired vgp lat,lon, kappa,N_site data:
    #
    #
    #
    A,Vgps,Pvgps=180.,[],[]
    VgpRecs=pmag.get_dictitem(data,'vgp_lat','','F') # get all non-blank vgp latitudes
    VgpRecs=pmag.get_dictitem(VgpRecs,'vgp_lon','','F') # get all non-blank vgp longitudes
    SiteRecs=pmag.get_dictitem(VgpRecs,'data_type','i','T') # get VGPs (as opposed to averaged)
    SiteRecs=pmag.get_dictitem(SiteRecs,coord_key,coord,'T') # get right coordinate system
    for rec in SiteRecs:
            if anti==1:
                if 90.-abs(float(rec['vgp_lat']))<=cutoff and float(rec['average_k'])>=kappa: 
                    if float(rec['vgp_lat'])<0:
                        rec['vgp_lat']='%7.1f'%(-1*float(rec['vgp_lat']))
                        rec['vgp_lon']='%7.1f'%(float(rec['vgp_lon'])-180.)
                    Vgps.append(rec)
                    Pvgps.append([float(rec['vgp_lon']),float(rec['vgp_lat'])])
            elif rev==0: # exclude normals
                if 90.-(float(rec['vgp_lat']))<=cutoff and float(rec['average_k'])>=kappa: 
                    Vgps.append(rec)
                    Pvgps.append([float(rec['vgp_lon']),float(rec['vgp_lat'])])
            else: # include normals
                if 90.-abs(float(rec['vgp_lat']))<=cutoff and float(rec['average_k'])>=kappa: 
                    if float(rec['vgp_lat'])<0:
                        rec['vgp_lat']='%7.1f'%(-1*float(rec['vgp_lat']))
                        rec['vgp_lon']='%7.1f'%(float(rec['vgp_lon'])-180.)
                        Vgps.append(rec)
                        Pvgps.append([float(rec['vgp_lon']),float(rec['vgp_lat'])])
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
    SBs=[]
    if boot==1:
        for i in range(nb): # now do bootstrap 
            BVgps=[]
            if i%100==0: print i,' out of ',nb
            for k in range(len(Vgps)):
                ind=random.randint(0,len(Vgps)-1)
                random.jumpahead(int(ind*1000))
                BVgps.append(Vgps[ind])
            SBs.append(pmag.get_Sb(BVgps))
        SBs.sort()
        low=int(.025*nb)
        high=int(.975*nb)
        print len(Vgps),'%7.1f _ %7.1f ^ %7.1f %7.1f'%(S_B,SBs[low],SBs[high],A)
    else:
        print len(Vgps),'%7.1f  %7.1f '%(S_B,A)

    
# 
if __name__ == "__main__":
    main()
