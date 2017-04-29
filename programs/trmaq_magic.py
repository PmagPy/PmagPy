#!/usr/bin/env python
from __future__ import print_function
from builtins import input
from builtins import range
import sys


import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.nlt as nlt

def main():
    """
    NAME
        trmaq_magic.py

    DESCTIPTION
        does non-linear trm acquisisiton correction
  
    SYNTAX
        trmaq_magic.py [-h][-i][command line options]

    OPTIONS
        -h prints help message and quits
        -i allows interactive setting of file names
        -f MFILE, sets magic_measurements input file
        -ft TSPEC, sets thellier_specimens input file
        -F OUT, sets output for non-linear TRM acquisition corrected data


    DEFAULTS
        MFILE: trmaq_measurements.txt
        TSPEC: thellier_specimens.txt
        OUT: NLT_specimens.txt
    """
    meas_file='trmaq_measurements.txt'
    tspec="thellier_specimens.txt"
    output='NLT_specimens.txt'
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-i' in sys.argv:
        meas_file=input("Input magic_measurements file name? [trmaq_measurements.txt] ")
        if meas_file=="":meas_file="trmaq_measurements.txt" 
        tspec=input(" thellier_specimens file name? [thellier_specimens.txt] ")
        if tspec=="":tspec="thellier_specimens.txt" 
        output=input("File for non-linear TRM adjusted specimen data: [NLTspecimens.txt] ")
        if output=="":output="NLT_specimens.txt"
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        meas_file=sys.argv[ind+1]
    if '-ft' in sys.argv:
        ind=sys.argv.index('-ft')
        tspec=sys.argv[ind+1]
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        output=sys.argv[ind+1]
    # 
    PLT={'aq':1}
    pmagplotlib.plot_init(PLT['aq'],5,5)
    #
    # get name of file from command line
    #
    comment=""
    #
    #
    meas_data,file_type=pmag.magic_read(meas_file)
    if file_type != 'magic_measurements':
        print(file_type)
        print(file_type,"This is not a valid magic_measurements file ") 
        sys.exit()
    sids=pmag.get_specs(meas_data)
    specimen=0
    #
    # read in thellier_specimen data
    #
    nrm,file_type=pmag.magic_read(tspec)
    PmagSpecRecs=[]
    while specimen < len(sids):
    #
    # find corresoponding paleointensity data for this specimen
    #
        s=sids[specimen]
        blab,best="",""
        for nrec in nrm:   # pick out the Banc data for this spec
            if nrec["er_specimen_name"]==s:
                blab=float(nrec["specimen_lab_field_dc"])
                best=float(nrec["specimen_int"])
                TrmRec=nrec
                break
        if blab=="":
            print("skipping ",s," : no best ")
            specimen+=1
        else:
            print(sids[specimen],specimen+1, 'of ', len(sids),'Best = ',best*1e6)
            MeasRecs=[]
    #
    # find the data from the meas_data file for this specimen
    #
            for rec in meas_data:
                if rec["er_specimen_name"]==s:
                    meths=rec["magic_method_codes"].split(":")
                    methcodes=[]
                    for meth in meths:
                        methcodes.append(meth.strip()) 
                    if "LP-TRM" in methcodes: MeasRecs.append(rec)
            if len(MeasRecs) <2:
               specimen+=1
               print('skipping specimen -  no trm acquisition data ', s)
    #
    #  collect info for the PmagSpecRec dictionary
    #
            else:
                TRMs,Bs=[],[]
                for rec in MeasRecs:
                    Bs.append(float(rec['treatment_dc_field']))
                    TRMs.append(float(rec['measurement_magn_moment']))
                NLpars=nlt.NLtrm(Bs,TRMs,best,blab,0) # calculate best fit parameters through TRM acquisition data, and get new banc
    #
                Mp,Bp=[],[]
                for k in  range(int(max(Bs)*1e6)):
                    Bp.append(float(k)*1e-6)
                    npred=nlt.TRM(Bp[-1],NLpars['xopt'][0],NLpars['xopt'][1]) # predicted NRM for this field
                    Mp.append(npred)
                pmagplotlib.plotTRM(PLT['aq'],Bs,TRMs,Bp,Mp,NLpars,rec['magic_experiment_name'])
                pmagplotlib.drawFIGS(PLT)
                print('Banc= ',float(NLpars['banc'])*1e6)
                trmTC={}
                for key in list(TrmRec.keys()):
                    trmTC[key]=TrmRec[key] # copy of info from thellier_specimens record
                trmTC['specimen_int']='%8.3e'%(NLpars['banc'])
                trmTC['magic_method_codes']=TrmRec["magic_method_codes"]+":DA-NL"
                PmagSpecRecs.append(trmTC)
                ans=input("Return for next specimen, s[a]ve plot  ")
                if ans=='a':
                    Name={'aq':rec['er_specimen_name']+'_TRM.svg'}
                    pmagplotlib.saveP(PLT,Name)
                specimen+=1
    pmag.magic_write(output,PmagSpecRecs,'pmag_specimens')

if __name__ == "__main__":
    main()
