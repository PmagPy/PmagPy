#!/usr/bin/env python
import sys,pmagplotlib,pmag
def main():
    """
    NAME
       fishqq.py

    DESCRIPTION
       makes qq plot from dec,inc input data

    INPUT FORMAT
       takes dec/inc pairs in space delimited file
   
    SYNTAX
       fishqq.py [command line options]

    OPTIONS
        -h help message
        -f FILE, specify file on command line

    """
    fmt,plot='svg',0
    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit
    elif '-f' in sys.argv: # ask for filename
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        data=f.readlines()
    DIs,nDIs,rDIs= [],[],[] # set up list for data
    for line in data:   # read in the data from standard input
        if '\t' in line:
            rec=line.split('\t') # split each line on space to get records
        else:
            rec=line.split() # split each line on space to get records
        DIs.append([float(rec[0]),float(rec[1])]) # append data to Inc
# split into two modes
    ppars=pmag.doprinc(DIs) # get principal directions
    for rec in DIs:
        angle=pmag.angle([rec[0],rec[1]],[ppars['dec'],ppars['inc']])
        if angle>90.:
            rDIs.append(rec)
        else:
            nDIs.append(rec)
    
#
    if len(rDIs) >=10 or len(nDIs) >=10:
        D1,I1=[],[]
        QQ={'unf1':1,'exp1':2}
        pmagplotlib.plot_init(QQ['unf1'],5,5)
        pmagplotlib.plot_init(QQ['exp1'],5,5)
        if len(nDIs) < 10: 
            ppars=pmag.doprinc(rDIs) # get principal directions
            Dbar,Ibar=ppars['dec']-180.,-ppars['inc']
            for di in rDIs:
                d,irot=pmag.dotilt(di[0],di[1],Dbar-180.,90.-Ibar) # rotate to mean
                drot=d-180.
                if drot<0:drot=drot+360.
                D1.append(drot)           
                I1.append(irot) 
                Dtit='Reverse Declinations'
                Itit='Reverse Inclinations'
        else:          
            ppars=pmag.doprinc(nDIs) # get principal directions
            Dbar,Ibar=ppars['dec'],ppars['inc']
            for di in nDIs:
                d,irot=pmag.dotilt(di[0],di[1],Dbar-180.,90.-Ibar) # rotate to mean
                drot=d-180.
                if drot<0:drot=drot+360.
                D1.append(drot)
                I1.append(irot)
                Dtit='Declinations'
                Itit='Inclinations'
                print drot,irot 
        pmagplotlib.plotQQunf(QQ['unf1'],D1,Dtit) # make plot
        pmagplotlib.plotQQexp(QQ['exp1'],I1,Itit) # make plot
    else:
        print 'you need N> 10 for at least one mode'
        sys.exit()
    if len(rDIs)>10 and len(nDIs)>10:
        D2,I2=[],[]
        QQ={'unf2':3,'exp2':4}
        pmagplotlib.plot_init(QQ['unf2'],5,5)
        pmagplotlib.plot_init(QQ['exp2'],5,5)
        ppars=pmag.doprinc(rDIs) # get principal directions
        Dbar,Ibar=ppars['dec']-180.,-ppars['inc']
        for di in rDIs:
            d,irot=pmag.dotilt(di[0],di[1],Dbar-180.,90.-Ibar) # rotate to mean
            drot=d-180.
            if drot<0:drot=drot+360.
            D2.append(drot)           
            I2.append(irot) 
            Dtit='Reverse Declinations'
            Itit='Reverse Inclinations'
        pmagplotlib.plotQQunf(QQ['unf2'],D2,Dtit) # make plot
        pmagplotlib.plotQQexp(QQ['exp2'],I2,Itit) # make plot
    pmagplotlib.drawFIGS(QQ) 
    files={}
    for key in QQ.keys():
        files[key]=key+'.'+fmt 
    if pmagplotlib.isServer:
        black     = '#000000'
        purple    = '#800080'
        titles={}
        titles['eq']='Equal Area Plot'
        EQ = pmagplotlib.addBorders(EQ,titles,black,purple)
        pmagplotlib.saveP(QQ,files)
    elif plot==1:
        files['qq']=file+'.'+fmt 
        pmagplotlib.saveP(QQ,files)
    else:
        ans=raw_input(" S[a]ve to save plot, [q]uit without saving:  ")
        if ans=="a": pmagplotlib.saveP(QQ,files) 
main()
