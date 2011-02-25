#!/usr/bin/env python
from Tkinter import *
import exceptions,shutil
import tkFileDialog, tkSimpleDialog, string, os,sys,tkMessageBox,shutil
import pmag,string
#
#
class make_entry(tkSimpleDialog.Dialog): # makes an entry table for basic data from global variable Result
    def body(self, master):
        g=0
        self.list=Edict.keys()
        self.list.sort()
        self.out=[]
        for i in range(len(self.list)):
            self.ival=StringVar()
            self.ival.set(Edict[self.list[i]])
            Label(master,text=self.list[i]).grid(row=g)
            self.e=Entry(master,textvariable=self.ival)
            self.out.append(self.e)
            self.e.grid(row=g,column=1)
            g+=1
            
    def apply(self):
        for i in range(len(self.list)):
            self.e=self.out[i]
            Edict[self.list[i]]=self.e.get()
        self.result=Edict
class make_check: # makes check boxes with labels in input_d
        def __init__(self, master,input_d,instruction):
                self.top=Toplevel(master)
                self.top.geometry('+50+50')
                self.check_value=[] 
                self.b = Button(self.top, text="OK", command=self.ok)
                self.b.grid(row=0,columnspan=1)
                for i in range(len(input_d)):
                        self.var=IntVar()
                        self.cb=Checkbutton(self.top,variable=self.var, text=input_d[i])
                        self.cb.grid(row=i+1,columnspan=2,sticky=W)
                        self.check_value.append(self.var)
        def ok(self):
                self.top.destroy()

def ask_check(parent,choices,title): # returns the values of the check box to caller
        global check_value
        m = make_check(parent,choices,title)
        parent.wait_window(m.top)
        return m.check_value

def custom():
    cust=['Use default criteria', 'Change default criteria','Change existing criteria ','Use no selection criteria']
    cust_rv=ask_radio(root,cust,'Customize selection criteria?') # 
    if cust_rv!=0: customize_criteria(cust_rv)

def customize_criteria(option):
    global Edict
    if option==3:
        nocrit=1
    elif option==1:
        nocrit=0
    elif option==2:
        nocrit=-1
    if nocrit!=-1:
        crit_data=pmag.default_criteria(nocrit)
        for critrec in crit_data:
            if critrec["pmag_criteria_code"]=="DE-SPEC": SpecCrit=critrec
            if critrec["pmag_criteria_code"]=="DE-SAMP": SampCrit=critrec
            if critrec["pmag_criteria_code"]=="IE-SAMP": SampIntCrit=critrec
            if critrec["pmag_criteria_code"]=="IE-SITE": SiteIntCrit=critrec
            if critrec["pmag_criteria_code"]=="DE-SITE": SiteCrit=critrec
            if critrec["pmag_criteria_code"]=="NPOLE": NpoleCrit=critrec
            if critrec["pmag_criteria_code"]=="RPOLE": RpoleCrit=critrec
            if critrec["pmag_criteria_code"]=="IE-SPEC": SpecIntCrit=critrec
            critrec['er_citation_names']="This study"
            critrec['criteria_definition']="Criteria for selection of specimen direction"
  
    else:
# change existing
        infile=opath+'/pmag_criteria.txt'
        try:
            crit_data,file_type=pmag.magic_read(infile)
            if file_type!='pmag_criteria':
                print 'bad input file'
                return
            print "Acceptance criteria read in from ", infile
        except:
            print 'bad pmag_criteria.txt  file'
            return
        print "Acceptance criteria read in from ", infile
        for critrec in crit_data:
            if critrec["pmag_criteria_code"]=="DE-SPEC": 
                for key in SpecCrit.keys(): 
                    if key in critrec.keys():SpecCrit[key]=critrec[key]
                SpecCrit['criteria_definition']='specimen direction'
            if critrec["pmag_criteria_code"]=="IE-SPEC": 
                for key in SpecIntCrit.keys(): 
                    if key in critrec.keys():SpecIntCrit[key]=critrec[key]
                SpecIntCrit['criteria_definition']='specimen intensity'
            if critrec["pmag_criteria_code"]=="DE-SAMP": 
                for key in SampCrit.keys(): 
                    if key in critrec.keys():SampCrit[key]=critrec[key]
                SampCrit['criteria_definition']='sample direction'
            if critrec["pmag_criteria_code"]=="IE-SAMP": 
                for key in SampIntCrit.keys(): 
                    if key in critrec.keys():SampIntCrit[key]=critrec[key]
                SampIntCrit['criteria_definition']='sample intensity'
            if critrec["pmag_criteria_code"]=="IE-SITE": 
                for key in SiteIntCrit.keys(): 
                    if key in critrec.keys():SiteIntCrit[key]=critrec[key]
                SiteIntCrit['criteria_definition']='site intensity'
            if critrec["pmag_criteria_code"]=="DE-SITE": 
                for key in SiteCrit.keys(): 
                    if key in critrec.keys():SiteCrit[key]=critrec[key]
                SiteCrit['criteria_definition']='site direction'
            if critrec["pmag_criteria_code"]=="NPOLE": 
                for key in NpoleCrit.keys(): 
                    if key in critrec.keys():NpoleCrit[key]=critrec[key]
                NpoleCrit['criteria_definition']='inclusion in normal pole'
            if critrec["pmag_criteria_code"]=="RPOLE": 
                for key in RpoleCrit.keys(): 
                    if key in critrec.keys():RpoleCrit[key]=critrec[key]
                RpoleCrit['criteria_definition']='inclusion in reverse pole'
    Crits=[SpecCrit,SpecIntCrit,SampCrit,SampIntCrit,SiteIntCrit,SiteCrit]
    TmpCrits=[]
    for crit in Crits:
        Edict={}
        for key in crit.keys():Edict[key]=crit[key]
        c=make_entry(root) 
        for key in crit.keys():crit[key]=Edict[key]
        crit['er_citation_names']='This study'
        TmpCrits.append(crit)
    PmagCrits,critkeys=pmag.fillkeys(TmpCrits)
    critout=opath+'/pmag_criteria.txt'
    pmag.magic_write(critout,PmagCrits,'pmag_criteria')
#    tkMessageBox.showinfo("Info",'Selection criteria saved in pmag_criteria.txt\n check command window for errors')
    print "Criteria saved in pmag_criteria.txt"


def add_agm():
    global Edict 
    fpath=tkFileDialog.askopenfilename(title="Set AGM input file:")
    file=fpath.split('/')[-1] 
    basename=file
    print """
    OPTIONS
        -loc LOCNAME : specify location/study name, (only if naming convention < 6)
        -syn SYN,  synthetic specimen name (either specimen_name or synthetic_name must be specified,
                  but NOT BOTH)
        -ins INST : specify which instrument was used (e.g, SIO-Maud), default is "unknown"
        -usr USER:   identify user, default is ""
        -spn SPEC, specimen name, default is base of input file name, e.g. SPECNAME.agm
        -spc NUM, specify number of characters to designate a  specimen, default = 0
        -bak: set this to 'y' if this is a back-field curve file 
    """
    ncn_rv=ask_radio(root,NCN_types,'select naming convention:') # sets naming convention
    if ncn_rv==3 or ncn_rv==6: # site_name and location in er_samples.txt file
        Edict={'loc':'','usr':"",'spn':basename.split('.')[0],'ins':'','spc':'1','Z':"",'bak':'n'}
    if ncn_rv==5: # site_name and location in er_samples.txt file
        Edict={'usr':"",'spn':basename.split('.')[0],'syn':'','ins':'','spc':'1','bak':'n'}
    elif ncn_rv==7: # specimen comes from a synthetic sample
        Edict={'usr':"",'syn':basename.split('.')[0],'ins':'','bak':'n'}
    else:  # all others
        Edict={'loc':'','usr':"",'spn':basename.split('.')[0],'ins':'','spc':'1','bak':'n'}
    make_entry(root)
    Edict['ncn']=ncn_rv
    add_agm_file(fpath)


def add_agm_dir():
    global Edict 
    agmpath= tkFileDialog.askdirectory()
    ncn_rv=ask_radio(root,NCN_types,'select naming convention\n NB: all file names must have specimen name as root\n and have same naming convention relating specimen to sample and site:') # sets naming convention
    print """
    OPTIONS
        -loc LOCNAME : specify location/study name, (only if naming convention < 6)
        -spc: number of characters to distinguish from sample name
        -syn SYN,  synthetic specimen name (either specimen_name or synthetic_name must be specified,
                  but NOT BOTH)
        -ins INST : specify which instrument was used (e.g, SIO-Maud), default is "unknown"
        -usr USER:   identify user, default is ""
        -bak: set this to 'y' if these are back-field curves
    """
    if ncn_rv==3: # site_name and location in er_samples.txt file
        Edict={'loc':'','usr':"",'ins':'','spc':'1','Z':"",'bak':'n'}
    if ncn_rv==5: # site_name and location in er_samples.txt file
        Edict={'usr':"",'ins':'','spc':'1','bak':'n'}
    elif ncn_rv==6:
        Edict={'loc':'','usr':"",'ins':'','bak':'n'}
    else: 
        Edict={'loc':'','usr':"",'ins':'','spc':'1','bak':'n'}
    make_entry(root)
    Edict['ncn']=ncn_rv
    filelist=os.listdir(agmpath)
    for file in filelist:
        if ncn_rv!=6:
            Edict['spn']=file.split('.')[0]
        else:
            Edict['syn']=file.split('.')[0]
        add_agm_file(agmpath+'/'+file)
    tkMessageBox.showinfo("Info","Import of directory completed - select Assemble Measurement before plotting\n Check terminal window for errors")

def add_agm_file(fpath):
    file=fpath.split('/')[-1] 
    basename=file
    ofile=opath+"/"+file
    try:
        filelist=[]
        logfile=open(opath+"/agm.log",'r')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
        if basename+'.magic' not in filelist:filelist.append(basename+'.magic')
    except IOError:
        filelist=[basename+'.magic']
    logfile=open(opath+"/agm.log",'w')
    for f in filelist:
        logfile.write(f+'\n') 
    logfile.close()
    infile=open(fpath,'rU').readlines()
    out=open(ofile,'w')
    for line in infile:
        out.write(line)
    out.close()
    if Edict['ncn']!=6:
        outstring='agm_magic.py -WD '+'"'+opath+'"'+ ' -F '+basename+'.magic -f '+ basename+ '  -spn ' + Edict['spn']+' -spc '+Edict['spc'] 
    else:
        outstring='agm_magic.py -WD '+'"'+opath+'"'+ ' -F '+basename+'.magic -f '+ basename+ '  -syn ' + Edict['syn']
    outstring=outstring + ' -ncn '+str(Edict['ncn']+1)
    if Edict['ncn']==5: outstring=outstring+' -fsa er_samples.txt'
    if Edict['usr']!="":outstring=outstring + ' -usr '+ Edict['usr']
    if 'loc' in Edict.keys() and Edict['loc']!="":outstring=outstring + ' -loc "'+ Edict['loc']+'"'
    if Edict['ins']!="":outstring=outstring + ' -ins '+ Edict['ins'] 
    if Edict['bak']=="y" or Edict['bak']=='Y':outstring=outstring + ' -bak '
    print outstring
    os.system(outstring)
    try:
        logfile=open(opath+"/measurements.log",'a')
        logfile.write(basename+".magic" +" | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/measurements.log",'w')
        logfile.write(basename+".magic" +" | " + outstring+"\n")


def add_curie():
    global Edict 
    fpath=tkFileDialog.askopenfilename(title="Set Curie temperature input file:")
    file=fpath.split('/')[-1] 
    basename=file
    ofile=opath+"/"+file
    print """
    OPTIONS
        -loc LOCNAME : specify location/study name, (only if naming convention < 6)
        -syn SYN,  synthetic specimen name (either specimen_name or synthetic_name must be specified,
                  but NOT BOTH)
        -ins INST : specify which instrument was used (e.g, SIO-Maud), default is "unknown"
        -usr USER:   identify user, default is ""
        -spn SPEC, specimen name, default is base of input file name, e.g. SPECNAME.agm
        -spc NUM, specify number of characters to designate a  specimen, default = 0
        -syn SYN, synthetic specimen name - no site, sample, location information
    """
    ncn_rv=ask_radio(root,NCN_types,'select naming convention:') # sets naming convention
    if ncn_rv==3 or ncn_rv==6: # site_name and location in er_samples.txt file
        Edict={'loc':'','usr':"",'spn':basename.split('.')[0],'ins':'','spc':'1','Z':""}
    if ncn_rv==5: # site_name and location in er_samples.txt file
        Edict={'usr':"",'spn':basename.split('.')[0],'syn':'','ins':'','spc':'1'}
    elif ncn_rv==7: # specimen comes from a synthetic sample
        Edict={'usr':"",'syn':basename.split('.')[0],'ins':''}
    else:  # all others
        Edict={'loc':'','usr':"",'spn':basename.split('.')[0],'ins':'','spc':'1'}
    make_entry(root)
    Edict['ncn']=ncn_rv
    infile=open(fpath,'rU').readlines()
    out=open(ofile,'w')
    for line in infile:
        out.write(line)
    out.close()
    if Edict['ncn']!=7:
        outstring='MsT_magic.py -WD '+'"'+opath+'"'+ ' -F '+basename+'.magic -f '+ basename+ '  -spn ' + Edict['spn']+' -spc '+Edict['spc'] 
    else:
        outstring='MsT_magic.py -WD '+'"'+opath+'"'+ ' -F '+basename+'.magic -f '+ basename+ '  -spn ' + Edict['syn']+' -syn '
    outstring=outstring + ' -ncn '+str(Edict['ncn']+1)
    if Edict['ncn']==5: outstring=outstring+' -fsa er_samples.txt'
    if Edict['usr']!="":outstring=outstring + ' -usr '+ Edict['usr']
    if 'loc' in Edict.keys() and Edict['loc']!="":outstring=outstring + ' -loc "'+ Edict['loc']+'"'
    if Edict['ins']!="":outstring=outstring + ' -ins '+ Edict['ins'] 
    print outstring
    os.system(outstring)
    try:
        logfile=open(opath+"/measurements.log",'a')
        logfile.write(basename+".magic" +" | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/measurements.log",'w')
        logfile.write(basename+".magic" +" | " + outstring+"\n")

class MagDialog(tkSimpleDialog.Dialog): # makes an entry table for basic data from a .mag file
    def body(self, master):
        Label(master, text="Location name: [default=unknown]").grid(row=0)
        Label(master, text="# characters for specimen: [default=1]").grid(row=1)
        Label(master, text="dc field (uT): [default=0]").grid(row=3)
        Label(master, text="dc field (phi): [default=0],set to -1 if ANI").grid(row=4)
        Label(master, text="dc field (theta): [default=-90],set to -1 if ANI").grid(row=5)
        Label(master, text="peak AF field (mT): [default=0]").grid(row=6)
        Label(master, text="Measurer: ").grid(row=7)
        Label(master, text="Average replicates [y/n]: [default is y] ").grid(row=8)
        Label(master, text="Z: only for naming convention #4").grid(row=9)
        self.loc = Entry(master)
        self.spc=Entry(master,textvariable='1')
        self.B = Entry(master)
        self.phi = Entry(master)
        self.theta = Entry(master)
        self.ac = Entry(master)
        self.usr = Entry(master)
        self.noave = Entry(master)
        self.Z = Entry(master)
        self.loc.grid(row=0, column=1)
        self.spc.grid(row=1, column=1)
        self.B.grid(row=3, column=1)
        self.phi.grid(row=4, column=1)
        self.theta.grid(row=5, column=1)
        self.ac.grid(row=6, column=1)
        self.usr.grid(row=7, column=1)
        self.noave.grid(row=8, column=1)
        self.Z.grid(row=9, column=1)
        return self.loc # initial focus
    def apply(self):
        Result['out']=opath+"/"+basename+".magic"
        if self.usr.get()!="":
            Result['usr']=self.usr.get()
        Result['noave']=self.noave.get()
        if self.loc.get()!="":
            Result['loc']=self.loc.get()
        if self.B.get()!="":
            Result['dc']=self.B.get()
        if self.phi.get()!="":
            Result['phi']=self.phi.get()
        if self.theta.get()!="":
            Result['theta']=self.theta.get()
        if self.ac.get()!="":
            Result['ac']=self.ac.get()
        if self.spc.get()!="":
            Result['spc']=self.spc.get()
        if self.Z.get()!="":
            Result['Z']=self.Z.get()
        self.result=Result

radio_value = 99
class make_radio: # makes a radio button form with labels in input_d
        def __init__(self, master,input_d,instruction):
                top=self.top=Toplevel(master) 
                self.top.geometry('+50+50')
                Label(top, text=instruction).pack(anchor="w")
                self.rv = IntVar()
                for i in range(len(input_d)):
                        Radiobutton(top,variable=self.rv, value=i,text=input_d[i]).pack(anchor="w")
                b = Button(top, text="OK", command=self.ok)
                b.pack(pady=5)
        def ok(self):
                global radio_value
                radio_value = self.rv.get()
                self.top.destroy()

def ask_radio(parent,choices,title): # returns the values of the radio button form to caller
        global radio_value
        m = make_radio(parent,choices,title)
        parent.wait_window(m.top)
        return radio_value

def age(): # imports a site age file
    global orpath
    mpath=tkFileDialog.askopenfilename(title="Set age file:")
    file=mpath.split('/')[-1]
    infile=open(mpath,'rU').readlines()
    print mpath,'opened for reading'
    mfile=opath+'/er_ages.txt'
    out=open(mfile,'w')
    for line in infile: 
        out.write(line) # copies contents of source file to Project directory
    out.close()
    print orpath,' copied to ',mfile  


def model_lat(): # imports a site paleolatitude file
    global orpath
    mpath=tkFileDialog.askopenfilename(title="Set paleolatitude  file:")
    file=mpath.split('/')[-1]
    infile=open(mpath,'rU').readlines()
    print mpath,'opened for reading'
    mfile=opath+'/model_lat.txt'
    out=open(mfile,'w')
    for line in infile: 
        out.write(line) # copies contents of source file to Project directory
    out.close()
    print orpath,' copied to ',mfile  

def convert_samps():
    outpath=tkFileDialog.askdirectory(title="Set output directory for orient.txt file")
    sampfile=opath+'/er_samples.txt'
    try:
        open(sampfile,'r')
        outstring='convert_samples.py -f er_samples.txt -F '+outpath+'/orient.txt '+' -WD '+opath
        print outstring
        os.system(outstring)
        tkMessageBox.showinfo("Info"," orientation files created in selected output directory\n NB: there will be a file for every location name found in the er_samples.txt file.\n format is location_orient.txt.\n Edit this file, then re-import with Import orient.txt format option.")
    except:
        print 'No er_samples.txt file - import something first! '
def add_ODP_samp():
    global apath
    apath=tkFileDialog.askopenfilename(title="Select ODP Sample Summary .csv file:")
    infile=open(apath,'rU').readlines()
    file=apath.split('/')[-1]
    print apath,'opened for reading'
    afile=opath+'/'+file
    out=open(afile,'w')
    for line in infile: 
        out.write(line) # copies contents of source file to Project directory
    out.close()
    print apath,' copied to ',afile  
    outstring='ODP_samples_magic.py -WD '+opath+' -f '+file+' -Fsa er_samples.txt'
    print outstring
    os.system(outstring)
           

def ODP_fix_names():
    filelist=os.listdir(opath)
    for file in filelist: # fix up ODP sample names
        if file.split(".")[-1]=='magic' or file.split("_")[-1]=='anisotropy.txt':
            fname=file.split('/')[-1]
            outstring='ODP_fix_names.py  -WD '+opath+' -f '+fname
            print outstring
            os.system(outstring)
    

def add_ODP_sum():
    global apath
    apath=tkFileDialog.askopenfilename(title="Select ODP Core Summary .csv file:")
    file=apath.split('/')[-1]
    infile=open(apath,'rU').readlines()
    print apath,'opened for reading'
    afile=opath+'/'+file
    out=open(afile,'w')
    for line in infile: 
        out.write(line) # copies contents of source file to Project directory
    out.close()
    print apath,' copied to ',afile  
    try:
        logfile=open(opath+"/ODPsummary.log",'a')
        logfile.write(file+"\n")
    except IOError:
        logfile=open(opath+"/ODPsummary.log",'w')
        logfile.write(file+"\n")


def add_ages():
    global apath
    apath=tkFileDialog.askopenfilename(title="Select er_ages.txt file:")
    file=apath.split('/')[-1]
    infile=open(apath,'rU').readlines()
    print apath,'opened for reading'
    afile=opath+'/'+file
    out=open(afile,'w')
    for line in infile: 
        out.write(line) # copies contents of source file to Project directory
    out.close()
    print apath,' copied to ',afile  


def orient(): # imports an orientation file to magic
    global orpath
    orpath=tkFileDialog.askopenfilename(title="Select orientation file:")
    file=orpath.split('/')[-1]
    infile=open(orpath,'rU').readlines()
    print orpath,'opened for reading'
    orfile=opath+'/'+file
    out=open(orfile,'w')
    for line in infile: 
        out.write(line) # copies contents of source file to Project directory
    out.close()
    print orpath,' copied to ',orfile  
    N_types=["1: XXXXY: where XXXX is site designation, Y is sample", "2: XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)", "3: XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)","4: XXXX[YYY] where YYY is sample designation with Z characters from site XXX; Z will be supplied on next page", "5: sample name=site name","6: site name entered in site_name column in the orient.txt format input file","7-Z: [XXXX]YYY where XXXX is Z character long site name"]
    ocn_rv=ask_radio(root,OCN_types,'select orientation convention:') # sets orientation convention 
    DCN_types=["1: Use the IGRF value at the lat/long and date supplied","2: Will supply dec correction later","3: mag_az is already corrected in file"]
    dcn_rv=ask_radio(root,DCN_types,'select declination convention:') # sets declination convention 
    ncn_rv=ask_radio(root,N_types,'select naming convention:') # sets naming convention
    o=OrDialog(root) # gets the entry table data with all the good stuff in o.result 
    while (o.result['dcn']=="2" and  o.result['dec']==""):
        print "You must specify a declination correction, with dec convention #2!"
        o=OrDialog(root)
    while o.result['dcn']=="4" and  o.result['Z']=="":
        print "You must specify the # characters for sample ID, with naming convention #4!"
        o=OrDialog(root)
    while o.result['dcn']=="7" and  o.result['Z']=="":
        print "You must specify the # characters for sample ID, with naming convention #7!"
        o=OrDialog(root)
    BED_types=["Take fisher mean of bedding poles?","Don't correct bedding dip direction with declination - already correct"]
    bed_checks=ask_check(root,BED_types,'choose bedding conventions:') # 
    BED_list=map((lambda var:var.get()),bed_checks) # returns method code  radio button list
    mcd_checks=ask_check(root,MCD_types,'select appropriate field methods:') # allows adding of meta data describing field methods
    MCD_list=map((lambda var:var.get()),mcd_checks) # returns method code  radio button list
    MCD=""
    for i in range(len(MCD_list)):
        if MCD_list[i]==1:MCD=MCD+MCD_types[i].split(":")[0]+":"
    o.result['mcd']=MCD[:-1]
    o.result['ocn']=OCN_types[ocn_rv].split(":")[0]
    o.result['dcn']=DCN_types[dcn_rv].split(":")[0]
    o.result['ncn']=N_types[ncn_rv].split(":")[0]
#
# build the command (outstring) for orientation_magic.py
#
    outstring='orientation_magic.py -WD '+opath +'  -ocn '+ o.result['ocn'] + ' -f '+file + ' -dcn '+o.result['dcn'] 
    if o.result['dcn']=="2":outstring=outstring + o.result['dec']
    outstring=outstring+' -ncn '+o.result['ncn'] 
    if o.result['ncn']=="4":outstring=outstring + '-'+o.result['Z']
    if o.result['ncn']=="7":outstring=outstring + '-'+o.result['Z']
    if o.result['gmt']!="":outstring=outstring + ' -gmt '+o.result['gmt']
    if o.result['mcd']!="":outstring=outstring + ' -mcd '+o.result['mcd']
    if o.result['app'].lower()=="y":outstring=outstring + ' -app '
    if BED_list[0]==1:outstring=outstring+' -a '
    if BED_list[1]==1:outstring=outstring+' -BCN '
    print outstring
    os.system(outstring)
    try:
        logfile=open(orpath+"/orient.log",'a')
        logfile.write("er_samples.txt/er_sites.txt/er_images.txt | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/orient.log",'w')
        logfile.write("er_samples.txt/er_sites.txt/er_images.txt  | " + outstring+"\n")
    update_crd()
#    tkMessageBox.showinfo("Info",file+" converted to magic format and added to orient.log \n check command window for errors")

def azdip(): 
    global orpath
    orpath=tkFileDialog.askopenfilename(title="Set AzDip file:")
    file=orpath.split('/')[-1]
    infile=open(orpath,'rU').readlines()
    print orpath,'opened for reading'
    orfile=opath+'/'+file
    out=open(orfile,'w')
    for line in infile: 
        out.write(line) # copies contents of source file to Project directory
    out.close()
    print orpath,' copied to ',orfile  
    ncn_rv=ask_radio(root,NCN_types,'select naming convention - #4-7 are not supported for this option:') # sets naming convention
    mcd_checks=ask_check(root,MCD_types,'select appropriate field methods:') # allows adding of meta data describing field methods
    MCD_list=map((lambda var:var.get()),mcd_checks) # returns method code  radio button list
    MCD=""
    for i in range(len(MCD_list)):
        if MCD_list[i]==1:MCD=MCD+MCD_types[i].split(":")[0]+":"
        
#
# build the command (outstring) for orientation_magic.py
#
    outstring='azdip_magic.py -Fsa '+opath +'/er_samples.txt' + ' -f ' + orfile 
    outstring=outstring+' -ncn '+str(ncn_rv+1)
    if MCD!="":outstring=outstring + ' -mcd '+MCD
    print outstring
    os.system(outstring)
    try:
        logfile=open(orpath+"/orient.log",'a')
        logfile.write("er_samples.txt/er_sites.txt | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/orient.log",'w')
        logfile.write("er_samples.txt/er_sites.txt  | " + outstring+"\n")
    update_crd()

def update_crd():
    geo,tilt=0,0
    orient,file_type=pmag.magic_read(opath+'/er_samples.txt')
    for rec in orient:
        if 'sample_azimuth' in rec.keys() and 'sample_dip' in rec.keys() and  rec['sample_azimuth']!="" and rec['sample_dip']!="": geo=1    
        if 'sample_bed_dip_direction' in rec.keys() and 'sample_bed_dip' in rec.keys() and rec['sample_bed_dip_direction']!="" and rec['sample_bed_dip']!="":
             tilt=1    
             break
    f=open(opath+'/coordinates.log','w')
    coord='-crd s\n'
    f.write(coord)
    if geo==1:
        coord='-crd g\n'
        f.write(coord)
    if tilt==1:
        coord='-crd t\n'
        f.write(coord)
    f.close()
            
class OrDialog(tkSimpleDialog.Dialog): # makes 
    def body(self, master):
        Label(master, text="Dec correction: only if Dec con is #2").grid(row=3)
        Label(master, text="# characters for sample or site [only used with XXXXYYY conventions 4&7]").grid(row=5)
        Label(master, text="Hours to subract from local time for GMT: [default=0]").grid(row=7)
        Label(master, text="Append/update existing MagIC files [y] [default is to overwrite.] ").grid(row=9)
        self.dec = Entry(master)
        self.Z = Entry(master)
        self.gmt=Entry(master)
        self.app = Entry(master)
        self.dec.grid(row=3, column=1)
        self.Z.grid(row=5, column=1)
        self.gmt.grid(row=7, column=1)
        self.app.grid(row=9, column=1)
        return self.dec # initial focus
    def apply(self):
        if self.dec.get()!="":
            OrResult['dec']=self.dec.get()
        if self.Z.get()!="":
            OrResult['Z']=self.Z.get()
        if self.gmt.get()!="":
            OrResult['gmt']=self.gmt.get()
        self.result=OrResult
        if self.app.get()=="y":
            OrResult['app']=self.app.get()
        self.result=OrResult

class ApwpDialog(tkSimpleDialog.Dialog): # makes 
    def body(self, master):
        Label(master, text="Present day Latitude (+north, -south)").grid(row=3)
        Label(master, text="Present day Longitude (+east, -west)").grid(row=5)
        Label(master, text="Age (Ma)").grid(row=7)
        self.lat = Entry(master)
        self.lon = Entry(master)
        self.age=Entry(master)
        self.lat.grid(row=3, column=1)
        self.lon.grid(row=5, column=1)
        self.age.grid(row=7, column=1)
        return self.lat # initial focus
    def apply(self):
        if self.lat.get()!="":
            ApwpResult['lat']=self.lat.get()
        if self.lon.get()!="":
            ApwpResult['lon']=self.lon.get()
        if self.age.get()!="":
            ApwpResult['age']=self.age.get()
        self.result=ApwpResult

def start_over():
    clear=tkMessageBox.askyesno('Confirmation Dialog','This will delete everything in the Project Directory\n Do you wish to proceed')
    if clear==True:
        filelist=os.listdir(opath)
        for file in filelist: os.remove(opath+"/"+file)
        tkMessageBox.showinfo("Info","All files removed from Project Directory\n check command window for errors")
    else:
        tkMessageBox.showinfo("Info","Clear was aborted - your files are safe")
 
def upload():
    outstring="upload_magic.py -WD "+'"'+opath+'"'
    print outstring
    os.system(outstring)
#    tkMessageBox.showinfo("Info","Import upload_dos.txt into Excel program 'MagIC Console'\n check command window for errors")

def download():
    if opath=="":
        print "Must set output directory first!"
        return
    fpath=tkFileDialog.askopenfilename(title="Set MagIC template .txt file:")
    in_path=fpath.split('/')
    file=in_path[-1] 
    ipath=""
    for n in in_path[:-1]: ipath=ipath+n+'/'
    ofile=opath+'/'+file
    infile=open(fpath,'rU').readlines()
    out=open(ofile,'w')
    for line in infile:
        out.write(line)
    out.close()
    print fpath,' copied to ',ofile
    outstring="download_magic.py -WD "+'"'+opath +'"'+' -f '+file
    print outstring
    os.system(outstring)
    filestring=""
    update_crd()
    try:
#  I took out the method code checking because downloaded files mix experiment types and this gets messy real fast
#
#        print 'checking on measurements.txt file'
#        open(opath+'/magic_measurements.txt','r')
#        outstring='fix_meas_magic.py -WD '+'"'+opath+'"'
#        print outstring
#        os.system(outstring)
#        print 'Checked method codes in magic_measurements.txt'
        pass
        try:
            outstring="mk_redo.py -WD "+'"'+opath+'"'
            print outstring
            os.system(outstring)
            try:
                open(opath+'/zeq_redo','r')
                outstring='zeq_magic_redo.py -WD '+'"'+opath+'"'
                print outstring
                os.system(outstring)
                filestring=' zeq_specimens.txt '
            except IOError:
                pass
            try:
                open(opath+'/thellier_redo','r')
                outstring='thellier_magic_redo.py -WD '+'"'+opath+'"'
                try:
                    open(opath+'/pmag_criteria.txt','r')
                    outstring=outstring+' -fcr pmag_criteria.txt '
                except:
                    pass
                print outstring
                os.system(outstring)
                filestring=filestring+' thellier_specimens.txt '
            except IOError:
                pass
            if filestring!="":
                outstring='combine_magic.py -WD '+'"'+opath+'"'+' -F pmag_specimens.txt -f '+filestring
                print outstring
                os.system(outstring)
        except:
            pass
    except IOError:
        pass
#    tkMessageBox.showinfo("Info",file +' unpacked into tab delimited MagIC txt files in: '+opath+'\n check command window for errors')

def list_con():
    try:
        list=open(opath+"/"+'measurements.log').readlines()
        outstring=""
        for comment in list:
            contents=comment.split("|")
            outstring=outstring + contents[0]+'\n created with: \n \t'+contents[-1]+'\n'
        print outstring
#        tkMessageBox.showinfo("Info",outstring)
    except IOError:
        tkMessageBox.showinfo("Info","No log file in Project directory")
def site_edit():
    try:
        open(opath+"/er_samples.txt",'r')
    except IOError:
        tkMessageBox.showinfo("Info",'Import orientation data first.   ')
        return
    try:
        open(opath+"/zeq_specimens_s.txt",'r')
    except IOError:
        tkMessageBox.showinfo("Info",'select Assemble specimens first.   ')
        return
    SE_types=["Ignore previous sample exclusions - re-examine all","Use existing exclusions? "]  
    se_checks=ask_check(root,SE_types," ") # 
    SE_list=map((lambda var:var.get()),se_checks) # returns file type choices
    outstring='site_edit_magic.py -WD '+opath
    if SE_list[0]==1:outstring=outstring + ' -N '
    if SE_list[1]==1:outstring=outstring + ' -exc '
    print outstring
    os.system(outstring)
    try:
        tkMessageBox.showinfo("Info","Be sure to re-run 'Assemble Specimens' to use orientations flags.")
    except:
        pass
    
    
def spec_combine():
    filestring=" -f "
    try: # check for anisotropy stuff first
        aarmfile=open(opath+"/aarm_measurements.txt",'r')
        outstring='aarm_magic.py -WD '+'"'+opath+'"'
        print outstring
        os.system(outstring)
    except IOError:
        pass
    try:
        open(opath+'/zeq_specimens.txt','r')
        print 'zeq_specimens.txt exists'
        try:
            f=open(opath+'/coordinates.log','r')
            lines=f.readlines()
            coords=[]
            for line in lines:
                coords.append(line.replace('\n',''))
            outstring="mk_redo.py -f zeq_specimens.txt -F zeq_redo -WD "+'"'+opath+'"'
            print outstring
            os.system(outstring)
            basestring='zeq_magic_redo.py   -WD '+'"'+opath+'"'
            redstring=basestring+' -crd s -F zeq_specimens_s.txt '
            print redstring
            os.system(redstring)
            filestring=filestring+' zeq_specimens_s.txt '
            if '-crd g' in coords:
                redstring=basestring+' -crd g -F zeq_specimens_g.txt '
                print redstring
                os.system(redstring)
                filestring=filestring+' zeq_specimens_g.txt '
            if '-crd t' in coords:
                redstring=basestring+' -crd t -F zeq_specimens_t.txt '
                print redstring
                os.system(redstring)
                filestring=filestring+' zeq_specimens_t.txt '
        except: # no coordinates.log file
            print 'problem in coordinates.log file'
            shutil.copyfile(opath+'/zeq_specimens.txt',opath+'/zeq_specimens_crd.txt')  # copy each data file to project directory
            filestring=filestring + ' zeq_specimens_crd.txt ' 
    except:
       pass
    try:
        open(opath+'/thellier_specimens.txt') # check anisotropy correction
        types=["Non-linear TRM", "Anisotropy","Cooling Rate"]
        checks=ask_check(root,types,'choose corrections desired')
        check_list=map((lambda var:var.get()),checks) # returns file type choices
        filestring=filestring+' thellier_specimens.txt '
        outstring="mk_redo.py -f thellier_specimens.txt -F thellier_redo  -WD "+'"'+opath+'"'
        os.system(outstring)
        print outstring
        outstring='thellier_magic_redo.py -WD '+'"'+opath+'"'
        try:
            open(opath+'/pmag_criteria.txt','r')
            outstring=outstring+' -fcr pmag_criteria.txt '
        except:
            pass
        if check_list[2]==1: 
            outstring = outstring + " -CR " # do cooling rate correction
            filestring=filestring+' CR_specimens.txt '
            cr=CRDialog(root) # gets the entry table data with all the good stuff in cr.result
            if cr.result['frac']!="" and cr.result['type']!="":
                outstring=outstring+ cr.result['frac'] +" " + cr.result['type']
        if check_list[0]==1: 
            outstring = outstring + " -NLT " # do non-linear correction
            filestring=filestring+' NLT_specimens.txt '
        if check_list[1]==1:
            try:
                f=open(opath+'/rmag_anisotropy.txt','rU')
                outstring=outstring + " -ANI " # do anisotropy correction
                ani=1
            except: # no anisotropy data
                tkMessageBox.showinfo("Info",'No anisotropy data found')
            os.system(outstring)
            print outstring
            replacestring='replace_AC_specimens.py  -WD '+'"'+opath+'"'
            print "CAUTION: replacing thellier data with anisotropy corrected data"
            print replacestring
            os.system(replacestring)
            filestring=filestring+' TorAC_specimens.txt '
        else:
            os.system(outstring)
            print outstring
    except:
        pass
    outstring='combine_magic.py -WD '+'"'+opath+'"'+' -F pmag_specimens.txt '+filestring +'\n'
    print outstring
    os.system(outstring)

def update_meas():
    try: # check for anisotropy stuff first
        open(opath+"/aarm_measurements.txt",'r')
        outstring="update_measurements.py -F aarm_measurements.txt -f aarm_measurements.txt -WD "+opath 
        os.system(outstring)
        print outstring
        print 'updated aarm_measurements.txt'
    except:
       pass
    try: # check for measurements.txt
        open(opath+"/magic_measurements.txt",'r')
        outstring="update_measurements.py -WD "+opath 
        os.system(outstring)
        print outstring
        print 'updated magic_measurements.txt'
    except:
       pass

def meas_combine():
    log=0
    try:
        logfile=open(opath+"/measurements.log",'r')
        filestring="-f "
        files=[]
        for line in logfile.readlines():
          if line[0]!="#":
            file=line.split("|")[0]
            if file not in files:files.append(file)
        for file in files:
            filestring=filestring + file + ' '
        outstring='combine_magic.py -WD '+'"'+opath+'"'+' -F magic_measurements.txt '+filestring
        print outstring
        os.system(outstring)
#        tkMessageBox.showinfo("Info",'all magic files combined into magic_measurements.txt \n Check command window for errors')
        log=1
    except IOError:
        pass
    try:
        logfile=open(opath+"/ucsc_imports.log",'r') # this is for the UCSC legacy files
        files=[]
        for line in logfile.readlines():
          if line[0]!="#":
            file=line.split()[0]
            if file not in files:files.append(file)
        filestring="-f "
        for file in files:
            filestring=filestring + file + '/magic_measurements.txt ' #
        outstring='combine_magic.py -WD '+'"'+opath+'"'+' -F magic_measurements.txt '+filestring
        print outstring
        os.system(outstring)
        filestring="-f "
        for file in files:
            filestring=filestring + file + '/er_samples.txt ' #
        outstring='combine_magic.py -WD '+'"'+opath+'"'+' -F er_samples.txt '+filestring
        print outstring
        os.system(outstring)
        filestring="-f "
        for file in files:
            filestring=filestring + file + '/er_sites.txt ' #
        outstring='combine_magic.py -WD '+'"'+opath+'"'+' -F er_sites.txt '+filestring
        print outstring
        os.system(outstring)
#        tkMessageBox.showinfo("Info",'all magic files combined \n Check command window for errors')
        log=1
    except IOError:
        pass
    try:
        logfile=open(opath+"/ani.log",'r')
        filestring="-f "
        files=[]
        for line in logfile.readlines():
            file=line.split("|")[0][:-1]
            if file not in files:files.append(file)
        for file in files:
            filestring=filestring + file + ' '
        outstring='combine_magic.py -WD '+'"'+opath+'"'+' -F aarm_measurements.txt '+filestring
        print outstring
        os.system(outstring)
#        tkMessageBox.showinfo("Info",'all ARM anisotropy files combined into aarm_measurements.txt \n Check command window for errors.')
        log=1
    except IOError:
        pass
    try:
        logfile=open(opath+"/ams.log",'r')
        filestring="-f "
        files=[]
        for line in logfile.readlines():
            file=line.split()[0]
            if file not in files:files.append(file)
        for file in files:
            filestring=filestring + file + ' '
        outstring='combine_magic.py -WD '+'"'+opath+'"'+' -F rmag_anisotropy.txt '+filestring
        print outstring
        os.system(outstring)
#        tkMessageBox.showinfo("Info",'all anisotropy files combined into rmag_anisotropy.txt \n Check command window for errors.')
        log=1
    except IOError:
        pass
    if log==0: tkMessageBox.showinfo("Info",'no log files!')

def add_cit():
        if opath=="":
            print "Must set output directory first!"
            return
        fpath=tkFileDialog.askopenfilename(title="Set input file:")
        in_path=fpath.split('/')
        file=in_path[-1] 
        ipath=""
        for n in in_path[:-1]: ipath=ipath+n+'/'
        ofile=opath+'/'+file
        infile=open(fpath,'rU').readlines()
        out=open(ofile,'w')
        for line in infile:
            out.write(line)
        out.close()
        print fpath,' copied to ',ofile
        outstring='CIT_magic.py -WD '+'"'+opath+'"'+'  -f '+file + ' -F ' + file+'.magic'
        ln=0
        if infile[0]=="CIT":
            ln+=3
        else:
            ln+=2
        while ln<len(infile):
            mfile=infile[ln].split()[0]
            ofile=opath+"/"+mfile
            cpfile=open(ipath+mfile,'rU').readlines()
            out=open(ofile,'w')
            for line in cpfile:
                out.write(line)
            out.close()
            ln+=1
            print ipath+mfile,' copied to ',ofile
        print outstring
        os.system(outstring)
#        tkMessageBox.showinfo("Info",file+' imported to MagIC \n Check command window for errors')
        try:
            logfile=open(opath+"/measurements.log",'a')
            logfile.write(file+".magic  | " + outstring+"\n")
        except IOError:
            logfile=open(opath+"/measurements.log",'w')
            logfile.write(file+".magic | " + outstring+"\n")
#        tkMessageBox.showinfo("Info",file+" converted to magic format and added to measurements.log  \n Check command window for errors")
        

def add_redo():
    try:
        open(opath+'/magic_measurements.txt','r')
    except IOError:
        tkMessageBox.showinfo("Info","You must Assemble Measurments first!")
        return
    lpath=tkFileDialog.askopenfilename(title="Set 'redo' file:")
    infile=open(lpath,'rU').readlines()
    if '\t' in infile[0]:
        line=infile[0].split('\t')
    else:
        line=infile[0].split()
    if len(line)>3:
        file='zeq_redo'
    else:
        file='thellier_redo'
    ofile=opath+'/'+file
    out=open(ofile,'w')
    redo_list=[]
    for line in infile:
        out.write(line)
    out.close()
    print lpath,' copied to ',ofile
    filelist=[]
    try:
        logfile=open(opath+"/specimens.log",'r')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
    except IOError:
        pass
    if file=='zeq_redo':
        outstring='zeq_magic_redo.py -WD '+'"'+opath+'"'
        if "zeq_specimens.txt" not in filelist:filelist.append("zeq_specimens.txt")
    elif file=='thellier_redo':
        outstring='thellier_magic_redo.py -WD '+'"'+opath+'"'
        if "thellier_specimens.txt" not in filelist:filelist.append("thellier_specimens.txt")
    logfile=open(opath+"/specimens.log",'w')
    for file in filelist:
        logfile.write(file+'\n') 
    logfile.close()
    try:
        open(opath+'/pmag_criteria.txt','r')
        outstring=outstring+' -fcr pmag_criteria.txt '
    except:
        pass
    print outstring
    os.system(outstring)
    tkMessageBox.showinfo("Info","Interpretation file imported to Project Directory, see terminal window for error messages \n You can check interpretations with Demagnetization Data and \n Assemble specimens when done.")

def add_DIR_ascii():
    try:
        open(opath+'/magic_measurements.txt','r')
    except IOError:
        tkMessageBox.showinfo("Info","You must Assemble Measurments first!")
        return
    lpath=tkFileDialog.askopenfilename(title="Set 'DIR' file:")
    infile=open(lpath,'rU').readlines()
    file=lpath.split('/')[-1] 
    basename=file
    ofile=opath+"/"+file
    out=open(ofile,'w') # copy file to MagIC directory
    for line in infile:
        out.write(line)
    out.close()
    print lpath,' copied to ',ofile
    outstring='DIR_redo.py -WD '+opath+' -f '+file +' -F DIR_redo '
    print outstring
    os.system(outstring) # convert DIR to redo file format
    outstring='zeq_magic_redo.py -fre DIR_redo -WD '+'"'+opath+'"'
    REP_types=["Overwrite existing interpretations","Save in separate file"]
    rep_rv=ask_radio(root,REP_types,'choose desired option:') # 
    if rep_rv==1:outstring=outstring+' -F zeq_specimens_DIR.txt'
    print outstring
    os.system(outstring) # convert DIR to redo file format
    filelist=[]
    try:
        logfile=open(opath+"/specimens.log",'r')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
    except IOError:
        pass
    try:
        open(opath+'/pmag_criteria.txt','r')
        outstring=outstring+' -fcr pmag_criteria.txt '
    except:
        pass
    print outstring
    os.system(outstring) # execute zeq_magic_redo with new redo file
    if "zeq_specimens_DIR.txt" not in filelist:filelist.append("zeq_specimens_DIR.txt")
    logfile=open(opath+"/specimens.log",'w')
    for file in filelist:
        logfile.write(file+'\n')  # add to log
    logfile.close()
    update_crd()
    tkMessageBox.showinfo("Info","Interpretation file imported to Project Directory, see terminal window for error messages \n You can check interpretations with Demagnetization Data and \n Assemble specimens when done.")

def add_LSQ():
    try:
        open(opath+'/magic_measurements.txt','r')
    except IOError:
        tkMessageBox.showinfo("Info","You must Assemble Measurments first!")
        return
    lpath=tkFileDialog.askopenfilename(title="Set 'LSQ' file:")
    infile=open(lpath,'rU').readlines()
    file=lpath.split('/')[-1] 
    basename=file
    ofile=opath+"/"+file
    out=open(ofile,'w') # copy file to MagIC directory
    for line in infile:
        out.write(line)
    out.close()
    print lpath,' copied to ',ofile
    outstring='LSQ_redo.py -WD '+opath+' -f '+file +' -F LSQ_redo '
    print outstring
    os.system(outstring) # convert DIR to redo file format
    outstring='zeq_magic_redo.py -fre LSQ_redo -WD '+'"'+opath+'"'
    REP_types=["Overwrite existing interpretations","Save in separate file"]
    rep_rv=ask_radio(root,REP_types,'choose desired option:') # 
    if rep_rv==1:outstring=outstring+' -F zeq_specimens_LSQ.txt'
    print outstring
    os.system(outstring) # convert LSQ to redo file format
    filelist=[]
    try:
        logfile=open(opath+"/specimens.log",'r')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
    except IOError:
        pass
    try:
        open(opath+'/pmag_criteria.txt','r')
        outstring=outstring+' -fcr pmag_criteria.txt '
    except:
        pass
    print outstring
    os.system(outstring) # execute zeq_magic_redo with new redo file
    if "zeq_specimens_LSQ.txt" not in filelist:filelist.append("zeq_specimens_LSQ.txt")
    logfile=open(opath+"/specimens.log",'w')
    for file in filelist:
        logfile.write(file+'\n')  # add to log
    logfile.close()
    tkMessageBox.showinfo("Info","Interpretation file imported to Project Directory, see terminal window for error messages \n You can check interpretations with Demagnetization Data and \n Assemble specimens when done.")

def add_PMM():
    try:
        open(opath+'/magic_measurements.txt','r')
    except IOError:
        tkMessageBox.showinfo("Info","You must Assemble Measurments first!")
        return
    lpath=tkFileDialog.askopenfilename(title="Set 'PMM' file:")
    infile=open(lpath,'rU').readlines()
    file=lpath.split('/')[-1] 
    basename=file
    ofile=opath+"/"+file
    out=open(ofile,'w') # copy file to MagIC directory
    for line in infile:
        out.write(line)
    out.close()
    print lpath,' copied to ',ofile
    outstring='PMM_redo.py -WD '+opath+' -f '+file +' -F PMM_redo '
    print outstring
    os.system(outstring) # convert PMM to redo file format
    outstring='zeq_magic_redo.py -fre PMM_redo -WD '+'"'+opath+'"'
    REP_types=["Overwrite existing interpretations","Save in separate file"]
    rep_rv=ask_radio(root,REP_types,'choose desired option:') # 
    if rep_rv==1:outstring=outstring+' -F zeq_specimens_PMM.txt'
    print outstring
    os.system(outstring) # 
    filelist=[]
    try:
        logfile=open(opath+"/specimens.log",'r')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
    except IOError:
        pass
    try:
        open(opath+'/pmag_criteria.txt','r')
        outstring=outstring+' -fcr pmag_criteria.txt '
    except:
        pass
    print outstring
    os.system(outstring) # execute zeq_magic_redo with new redo file
    if "zeq_specimens_PMM.txt" not in filelist:filelist.append("zeq_specimens_PMM.txt")
    logfile=open(opath+"/specimens.log",'w')
    for file in filelist:
        logfile.write(file+'\n')  # add to log
    logfile.close()
    tkMessageBox.showinfo("Info","Interpretation file imported to Project Directory, see terminal window for error messages \n You can check interpretations with Demagnetization Data and \n Assemble specimens when done.")

def add_mag():
        global fpath,basename, Result
        Result={'usr':'','out':'','dc':'0','ac':'0','phi':'0','theta':'-90','spc':'1'}
        if opath=="":
            print "Must set output directory first!"
            return
        fpath=tkFileDialog.askopenfilename(title="Set input file:")
        file=fpath.split('/')[-1] 
        basename=file
        ofile=opath+"/"+file
        ncn_rv=ask_radio(root,NCN_types,'select naming convention:') # sets naming convention
        if ncn_rv==3: # site_name and location in er_samples.txt file
            Result['Z']=""
        else:  # all others
            Result['loc']=''
        d=MagDialog(root)
        LP_types=["AF: alternating field demagnetization","S: Shaw method paleointensity","T: Thermal de(re)magnetization including thellier but excluding TRM acquisition","NRM: no lab treatment","TRM: TRM acquisition experiment","ANI: anisotropy of TRM,IRM or ARM","D: double demagnetization","G: GRM protocol","I: IRM"]
        checks=ask_check(root,LP_types,'select lab protocols:\n ')
        LPlist= map((lambda var:var.get()),checks)
        LP=""
        for i in range(len(LPlist)):
             if LPlist[i]==1:
                 LP=LP+LP_types[i].split(':')[0]+":"
                 if "ANI" in LP.split(':'): 
                     try:
                         filelist=[]
                         logfile=open(opath+"/ani.log",'r')
                         for line in logfile.readlines():
                             if line.split()[0] not in filelist:filelist.append(line.split()[0])
                         if basename+'.magic' not in filelist:filelist.append(basename+'.magic')
                     except IOError:
                         filelist=[basename+'.magic']
                     logfile=open(opath+"/ani.log",'w')
                     for f in filelist:
                         logfile.write(f+'\n') 
                     logfile.close()
        d.result['LP']=LP[:-1]
        d.result['fpath']=fpath
        infile=open(fpath,'rU').readlines()
        out=open(ofile,'w')
        for line in infile:
            out.write(line)
        out.close()
        outstring='mag_magic.py -F '+d.result['out']+' -f '+ ofile+ ' -LP ' + d.result['LP'] + ' -spc ' + d.result['spc'] 
        if d.result['loc']!="":outstring=outstring + ' -loc "'+ d.result['loc']+'"'
        if d.result['dc']!="0":outstring=outstring + ' -dc '+ d.result['dc'] + ' ' + d.result['phi'] + ' ' + d.result['theta']
        if d.result['usr']!="":outstring=outstring + ' -usr '+ d.result['usr'] 
        if d.result['noave']=="n":outstring=outstring + ' -A '
        outstring=outstring+' -ncn '+NCN_types[ncn_rv].split(":")[0]
        if ncn_rv==3:outstring=outstring+'-'+d.result['Z']+" "
        if ncn_rv==6:outstring=outstring+'-'+d.result['Z']+" "
        if outstring[-1]=='6':outstring=outstring+' -fsa '+opath+'/er_samples.txt'
        print outstring
        os.system(outstring)
        try:
            logfile=open(opath+"/measurements.log",'a')
            logfile.write(basename+".magic" +" | " + outstring+"\n")
        except IOError:
            logfile=open(opath+"/measurements.log",'w')
            logfile.write(basename+".magic" +" | " + outstring+"\n")
#        tkMessageBox.showinfo("Info",file+" converted to magic format and added to measurements.log  \n Check command window for errors")


def add_ldgo():
        global fpath,basename,Result
        Result={'usr':'','out':'','dc':'0','ac':'0','phi':'0','theta':'-90','loc':"unknown",'spc':'1'}
        if opath=="":
            print "Must set output directory first!"
            return
        fpath=tkFileDialog.askopenfilename(title="Set input file:")
        file=fpath.split('/')[-1] 
        basename=file
        LP_types=["AF: alternating field demagnetization","T: Thermal de(re)magnetization including thellier but excluding TRM acquisition","NRM: no lab treatment","TRM: TRM acquisition experiment","ANI: anisotropy of TRM or ARM","D: double demagnetization","G: GRM protocol"]
        checks=ask_check(root,LP_types,'select lab protocols:\n ')
        LPlist= map((lambda var:var.get()),checks)
        LP=""
        for i in range(len(LPlist)):
             if LPlist[i]==1:LP=LP+LP_types[i].split(':')[0]+":"
        ncn_rv=ask_radio(root,NCN_types,'select naming convention:') # sets naming convention
        if ncn_rv==3: # site_name and location in er_samples.txt file
            Result['Z']=""
        else:  # all others
            Result['loc']=''
        d=MagDialog(root)
        d.result['LP']=LP[:-1]
        d.result['fpath']=fpath
        ofile=opath+"/"+file
        infile=open(fpath,'rU').readlines()
        out=open(ofile,'w')
        for line in infile:
            out.write(line)
        out.close()
        outstring='mag_magic.py -FT LDGO -F '+d.result['out']+' -f '+ ofile+ ' -LP ' + d.result['LP'] + ' -spc ' + d.result['spc'] 
        if d.result['loc']!="":outstring=outstring + ' -loc "'+ d.result['loc']+'"'
        if d.result['dc']!="0":outstring=outstring + ' -dc '+ d.result['dc'] + ' ' + d.result['phi'] + ' ' + d.result['theta']
        if d.result['usr']!="":outstring=outstring + ' -usr '+ d.result['usr'] 
        orient=['Recalculate azimuth and plunge from ldeo file', ' Will use imported orientation file. ']
        or_rv=ask_radio(root,orient,'Choose option: ') # 
        if or_rv==0: outstring=outstring + ' -Fsa '+ opath+'/er_samples.txt' # overwrite any existing er_samples.txt file
        outstring=outstring+' -ncn '+NCN_types[ncn_rv].split(":")[0]
        if ncn_rv==3:outstring=outstring+'-'+d.result['Z']+" "
        print outstring
        os.system(outstring)
        try:
            logfile=open(opath+"/measurements.log",'a')
            logfile.write(basename+".magic" +" | " + outstring+"\n")
        except IOError:
            logfile=open(opath+"/measurements.log",'w')
            logfile.write(basename+".magic" +" | " + outstring+"\n")
#        tkMessageBox.showinfo("Info",file+" converted to magic format and added to measurements.log\n er_samples.txt file created, to overwrite, import orientation file (AzDip or orient.txt format).")

def add_uu():
    global fpath,basename,Edict
    fpath=tkFileDialog.askopenfilename(title="Set input file:")
    file=fpath.split('/')[-1] 
    basename=file
    ofile=opath+"/"+file
    infile=open(fpath,'rU').readlines()
    out=open(ofile,'w')
    for line in infile:
        out.write(line)
    out.close()
    outstring='UU_magic.py -ocn 5  -WD '+'"'+opath+'"'+ ' -F '+basename+'.magic'+' -f '+ file
    safpath=tkFileDialog.askopenfilename(title="Select stratigraphic postion file (cancel if none):")
    if safpath!="":
        sfile=safpath.split('/')[-1]
        saffile=opath+'/'+sfile
        saf=open(safpath,'rU').readlines()
        out=open(saffile,'w')
        for line in saf:
            out.write(line)
        outstring=outstring+' -fpos '+sfile
    Edict={'usr':"",'loc':"",'spc':'1','ins':''}
    make_entry(root) 
    if Edict['usr']!="":outstring=outstring + ' -usr '+ Edict['usr']
    if Edict['loc']!="":outstring=outstring + ' -loc "'+ Edict['loc']+'"'
    if Edict['spc']!="":outstring=outstring + ' -spc '+ Edict['spc']
    if Edict['ins']!="":outstring=outstring + ' -ins '+ Edict['ins']
    ncn_rv=ask_radio(root,NCN_types,'select naming convention:') # sets naming convention
    mcd_checks=ask_check(root,MCD_types,'select appropriate field methods:') # allows adding of meta data describing field methods
    MCD_list=map((lambda var:var.get()),mcd_checks) # returns method code  radio button list
    MCD=""
    for i in range(len(MCD_list)):
        if MCD_list[i]==1:MCD=MCD+MCD_types[i].split(":")[0]+":"
    if MCD!="":
        outstring=outstring+' -mcd '+MCD[:-1]
    outstring=outstring+' -ncn '+NCN_types[ncn_rv].split(":")[0]
    print outstring
    os.system(outstring)
    try:
        logfile=open(opath+"/measurements.log",'a')
        logfile.write(basename+".magic" +" | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/measurements.log",'w')
        logfile.write(basename+".magic" +" | " + outstring+"\n")
#    tkMessageBox.showinfo("Info",file+" converted to magic format and added to measurements.log  \n Check command window for errors")

def add_liv():
    global fpath,basename,Edict
    fpath=tkFileDialog.askopenfilename(title="Set input file:")
    file=fpath.split('/')[-1] 
    basename=file
    ofile=opath+"/"+file
    infile=open(fpath,'rU').readlines()
    out=open(ofile,'w')
    for line in infile:
        out.write(line)
    out.close()
    outstring='LIVMW_magic.py -WD '+'"'+opath+'"'+ ' -F '+basename+'.magic -Fsa er_samples.txt  -f '+ file
    Edict={'usr':"",'loc':"",'spc':'','ins':'','sit':'','B phi':"",'B theta':""}
    make_entry(root) 
    phi,theta='0','-90'
    if Edict['usr']!="":outstring=outstring + ' -usr '+ Edict['usr']
    if Edict['loc']!="":outstring=outstring + ' -loc "'+ Edict['loc']+'"'
    if Edict['spc']!="":outstring=outstring + ' -spc '+ Edict['spc']
    if Edict['ins']!="":outstring=outstring + ' -ins '+ Edict['ins']
    if Edict['sit']!="":outstring=outstring + ' -sit '+ Edict['sit']
    if Edict['B phi']!="":phi= Edict['B phi']
    if Edict['B theta']!="":theta= Edict['B theta']
    outstring=outstring+" -B "+phi+' '+theta
    if Edict['sit']=="":
        ncn_rv=ask_radio(root,NCN_types,'select naming convention:') # sets naming convention
        outstring=outstring+' -ncn '+NCN_types[ncn_rv].split(":")[0]
    print outstring
    os.system(outstring)
    try:
        logfile=open(opath+"/measurements.log",'a')
        logfile.write(basename+".magic" +" | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/measurements.log",'w')
        logfile.write(basename+".magic" +" | " + outstring+"\n")
#    tkMessageBox.showinfo("Info",file+" converted to magic format and added to measurements.log  \n Check command window for errors")


def add_ub():
    global fpath,basename,Edict
    fpath=tkFileDialog.askopenfilename(title="Set input file:")
    ipathL=fpath.split('/')
    file=ipathL[-1]
    parts=file.split('.')
    if len(parts)==1: file=file+'.txt'
    ipath=""
    for el in ipathL[:-1]:ipath=ipath+el+"/" 
    ofile=opath+"/"+file
    infile=open(fpath,'rU').readlines()
    out=open(ofile,'w')
    for line in infile:
        out.write(line)
        cfile=line.split()[0]
        if cfile!='end':shutil.copyfile(ipath+cfile+'.dat',opath+'/'+cfile+'.dat')  # copy each data file to project directory
    out.close()
    outstring='UB_magic.py -ocn 5  -WD '+'"'+opath+'"'+ ' -F '+file+'.magic'+' -f '+ file
    safpath=tkFileDialog.askopenfilename(title="Select stratigraphic postion file (cancel if none):")
    if safpath!="":
        sfile=safpath.split('/')[-1]
        saffile=opath+'/'+sfile
        saf=open(safpath,'rU').readlines()
        out=open(saffile,'w')
        for line in saf:
            out.write(line)
        outstring=outstring+' -fpos '+sfile
    Edict={'usr':"",'loc':"",'spc':'0','ins':''}
    make_entry(root) 
    if Edict['usr']!="":outstring=outstring + ' -usr '+ Edict['usr']
    if Edict['loc']!="":outstring=outstring + ' -loc "'+ Edict['loc']+'"'
    if Edict['spc']!="":outstring=outstring + ' -spc '+ Edict['spc']
    if Edict['ins']!="":outstring=outstring + ' -ins '+ Edict['ins']
    ncn_rv=ask_radio(root,NCN_types,'select naming convention:') # sets naming convention
    mcd_checks=ask_check(root,MCD_types,'select appropriate field methods:') # allows adding of meta data describing field methods
    MCD_list=map((lambda var:var.get()),mcd_checks) # returns method code  radio button list
    MCD=""
    for i in range(len(MCD_list)):
        if MCD_list[i]==1:MCD=MCD+MCD_types[i].split(":")[0]+":"
    if MCD!="":
        outstring=outstring+' -mcd '+MCD[:-1]
    outstring=outstring+' -ncn '+NCN_types[ncn_rv].split(":")[0]
    AVE_types=["Do not average replicate measurements","Average replicate measurements"]
    ave_checks=ask_check(root,AVE_types,'choose desired averaging option:') # 
    ave_list=map((lambda var:var.get()),ave_checks) # returns averaging options radio button list
    if ave_list[1]==1:outstring=outstring+ ' -a'
    print outstring
    os.system(outstring)
    try:
        logfile=open(opath+"/measurements.log",'a')
        logfile.write(file+".magic" +" | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/measurements.log",'w')
        logfile.write(file+".magic" +" | " + outstring+"\n")
#    tkMessageBox.showinfo("Info",file+" converted to magic format and added to measurements.log  \n Check command window for errors")

def add_pmd_ascii():
    global Edict
    dpath=tkFileDialog.askdirectory(title="Select Directory of .PMD files for import ")
    ncn_rv=ask_radio(root,NCN_types,'select naming convention\n NB: all file names must have same naming convention relating specimen to sample and site:') # sets naming convention
    ncn_string=str(ncn_rv+1)
    Edict={'usr':"",'spc':'0','ins':''}
    if ncn_rv==3 or ncn_rv==6:
        Edict['loc']=""
        Edict['Z']=""
    elif ncn_rv!=5:
        Edict['loc']=""
    make_entry(root) 
    if ncn_rv==3 or ncn_rv==6:ncn_string=ncn_string+'-'+Edict['Z']
    mcd_checks=ask_check(root,MCD_types,'select appropriate field methods:') # allows adding of meta data describing field methods
    MCD_list=map((lambda var:var.get()),mcd_checks) # returns method code  radio button list
    MCD=""
    for i in range(len(MCD_list)):
        if MCD_list[i]==1:MCD=MCD+MCD_types[i].split(":")[0]+":"
    AVE_types=["Do not average replicate measurements","Average replicate measurements"]
    ave_rv=ask_radio(root,AVE_types,'choose desired averaging option:') # 
    try:
        open(opath+'/er_samples.txt','r')
        APP=""
        Or_types=["Append to existing er_samples.txt file","Overwrite existing er_samples.txt file"]
        or_rv=ask_radio(root,Or_types,'choose desired averaging option:') # 
        if or_rv==0: APP=" -Fsa er_samples.txt "
    except:
        APP=""
    filelist=os.listdir(dpath) # get directory listing
    first=1
    for file in filelist: 
      if first!=1:APP=" -Fsa er_samples.txt "
      first=0 
      if file.split('.')[1].lower()=='pmd':
        basename=file
        ofile=opath+"/"+file
        infile=open(dpath+'/'+file,'rU').readlines()
        out=open(ofile,'w') # copy file to MagIC project directory
        for line in infile:
            out.write(line)
        out.close()
        print ofile,' copied to MagIC project directory'
        outstring='PMD_magic.py  -WD '+'"'+opath+'"'+ ' -F '+file+'.magic'+' -f '+ file +APP
        if MCD!="": # add method codes
            outstring=outstring+' -mcd '+MCD[:-1]
        outstring=outstring+' -ncn '+ncn_string
        if ave_rv==0:outstring=outstring+ ' -A'
        if Edict['usr']!="":outstring=outstring + ' -usr '+ Edict['usr']
        if 'loc' in Edict.keys() and  Edict['loc']!="":outstring=outstring + ' -loc "'+ Edict['loc']+'"'
        if Edict['ins']!="":outstring=outstring + ' -ins '+ Edict['ins']
        print outstring
        os.system(outstring)
        try:  # add file to measurements.log
            filelist=[]
            logfile=open(opath+"/measurements.log",'r')
            for line in logfile.readlines():
                if line.split()[0] not in filelist:filelist.append(line.split()[0])
            if basename+'.magic' not in filelist:filelist.append(basename+'.magic')
        except IOError:
            filelist=[basename+'.magic']
        logfile=open(opath+"/measurements.log",'w')
        for f in filelist:
            logfile.write(f+' | '+outstring+'\n')
        logfile.close()


def add_ur_jr6():
    global Edict
    dpath=tkFileDialog.askdirectory(title="Select Directory of .JR6 files for import ")
    ncn_rv=ask_radio(root,NCN_types,'select naming convention\n NB: all file names must have same naming convention relating specimen to sample and site:') # sets naming convention
    ncn_string=str(ncn_rv+1)
    Edict={'usr':"",'spc':'0'}
    if ncn_rv==3 or ncn_rv==6:
        Edict['loc']=""
        Edict['Z']=""
    elif ncn_rv!=5:
        Edict['loc']=""
    make_entry(root) 
    if ncn_rv==3 or ncn_rv==6:ncn_string=ncn_string+'-'+Edict['Z']
    mcd_checks=ask_check(root,MCD_types,'select appropriate field methods:') # allows adding of meta data describing field methods
    MCD_list=map((lambda var:var.get()),mcd_checks) # returns method code  radio button list
    MCD=""
    for i in range(len(MCD_list)):
        if MCD_list[i]==1:MCD=MCD+MCD_types[i].split(":")[0]+":"
    AVE_types=["Do not average replicate measurements","Average replicate measurements"]
    ave_rv=ask_radio(root,AVE_types,'choose desired averaging option:') # 
    try:
        open(opath+'/er_samples.txt','r')
        APP=""
        Or_types=["Append to existing er_samples.txt file","Overwrite existing er_samples.txt file"]
        or_rv=ask_radio(root,Or_types,'choose desired averaging option:') # 
        if or_rv==0: APP=" -Fsa er_samples.txt "
    except:
        APP=""
    filelist=os.listdir(dpath) # get directory listing
    dirname=dpath.split('/')[-1]
    for file in filelist: 
      if file.split('.')[-1].upper()=='JR6':
        ofile=opath+'/'+file
        infile=open(dpath+'/'+file,'rU').readlines()
        out=open(ofile,'w') # copy file to MagIC project directory
        for line in infile:
            out.write(line)
        out.close()
    outfile=dirname+'.magic'
    outstring='UR_jr6_magic.py  -WD '+opath +'/'+' -F '+dirname+'.magic'
    if Edict['usr']!="":outstring=outstring + ' -usr '+ Edict['usr']
    if Edict['loc']!="":outstring=outstring + ' -loc "'+ Edict['loc']+'"'
    if Edict['spc']!="":outstring=outstring + ' -spc '+ Edict['spc']
    if MCD!="":
        outstring=outstring+' -mcd '+MCD[:-1]
    outstring=outstring+' -ncn '+NCN_types[ncn_rv].split(":")[0]
    if ncn_rv==3 or ncn_rv==6:
        outstring=outstring+'-'+Edict['Z']
        Edict['Z']=""
    if ave_rv==1:outstring=outstring+ ' -A'
    print outstring
    os.system(outstring)
    try:
        logfile=open(opath+"/measurements.log",'a')
        logfile.write(outfile +" | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/measurements.log",'w')
        logfile.write(dirname+".magic" +" | " + outstring+"\n")

    try:
        logfile=open(opath+"/coordinates.log",'a')
        logfile.write('-crd g'+"\n")
    except IOError:
        logfile=open(opath+"/coordintates.log",'w')
        logfile.write('-crd g'+"\n")

def add_ipg():
    global Edict
    fpath=tkFileDialog.askopenfilename(title="Set input file:")
    file=fpath.split('/')[-1] 
    basename=file
    ofile=opath+"/"+file
    ncn_rv=ask_radio(root,NCN_types,'select naming convention:') # sets naming convention
    ncn_string=str(ncn_rv+1)
    Edict={'usr':"",'spc':'0','ins':''}
    if ncn_rv==3:
        Edict['Z']=""
    elif ncn_rv!=5:
        Edict['loc']=""
    make_entry(root) 
    if ncn_rv==3:ncn_string=ncn_string+'-'+Edict['Z']
    mcd_checks=ask_check(root,MCD_types,'select appropriate field methods:') # allows adding of meta data describing field methods
    MCD_list=map((lambda var:var.get()),mcd_checks) # returns method code  radio button list
    MCD=""
    for i in range(len(MCD_list)):
        if MCD_list[i]==1:MCD=MCD+MCD_types[i].split(":")[0]+":"
    AVE_types=["Do not average replicate measurements","Average replicate measurements"]
    ave_rv=ask_radio(root,AVE_types,'choose desired averaging option:') # 
    try:
        open(opath+'/er_samples.txt','r')
        APP=""
        Or_types=["Append to existing er_samples.txt file","Overwrite existing er_samples.txt file"]
        or_rv=ask_radio(root,Or_types,'choose desired averaging option:') # 
        if or_rv==0: APP=" -Fsa er_samples.txt "
    except:
        APP=""
    infile=open(fpath,'rU').readlines()
    out=open(ofile,'w') # copy file to MagIC project directory
    for line in infile:
        out.write(line)
    out.close()
    print ofile,' copied to MagIC project directory'
    outstring='IPG_magic.py  -WD '+'"'+opath+'"'+ ' -F '+file+'.magic'+' -f '+ file +APP
    if MCD!="": # add method codes
        outstring=outstring+' -mcd '+MCD[:-1]
    outstring=outstring+' -ncn '+ncn_string
    if ave_rv==0:outstring=outstring+ ' -A'
    if Edict['usr']!="":outstring=outstring + ' -usr '+ Edict['usr']
    if 'loc' in Edict.keys() and  Edict['loc']!="":outstring=outstring + ' -loc "'+ Edict['loc']+'"'
    if Edict['ins']!="":outstring=outstring + ' -ins '+ Edict['ins']
    print outstring
    os.system(outstring)
    try:  # add file to measurements.log
        filelist=[]
        logfile=open(opath+"/measurements.log",'r')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
        if basename+'.magic' not in filelist:filelist.append(basename+'.magic')
    except IOError:
        filelist=[basename+'.magic']
    logfile=open(opath+"/measurements.log",'w')
    for f in filelist:
        logfile.write(f+' | '+outstring+'\n')
    logfile.close()

def add_2G():
    global Edict
    dpath=tkFileDialog.askdirectory(title="Select Directory of 2G files for import ")
    ncn_rv=ask_radio(root,NCN_types,'select naming convention\n NB: all file names must have same naming convention relating specimen to sample and site:') # sets naming convention
    ocn_rv=ask_radio(root,OCN_types,'select orientation convention:')
    Edict={'usr':"",'spc':'1','ins':''}
    if ncn_rv==3: Edict['Z']=""
    if ncn_rv!=5: Edict['loc']=""
    make_entry(root) 
    mcd_checks=ask_check(root,MCD_types,'select appropriate field methods:') # allows adding of meta data describing field methods
    MCD_list=map((lambda var:var.get()),mcd_checks) # returns method code  radio button list
    MCD=""
    for i in range(len(MCD_list)):
        if MCD_list[i]==1:MCD=MCD+MCD_types[i].split(":")[0]+":"
    AVE_types=["Do not average replicate measurements","Average replicate measurements"]
    ave_rv=ask_radio(root,AVE_types,'choose desired averaging option:') # 
    filelist=os.listdir(dpath) # get directory listing
    for file in filelist: 
      if file.split('.')[1].lower()=='dat':
        basename=file
        ofile=opath+"/"+file
        infile=open(dpath+'/'+file,'rU').readlines()
        out=open(ofile,'w') # copy file to MagIC project directory
        for line in infile:
            out.write(line)
        out.close()
        outstring='2G_magic.py -Fsa er_samples.txt  -WD '+'"'+opath+'"'+ ' -F '+file+'.magic'+' -f '+ file
        if MCD!="": # add method codes
            outstring=outstring+' -mcd '+MCD[:-1]
        outstring=outstring+' -ncn '+str(ncn_rv+1) +' -ocn '+str(ocn_rv+1) + ' -spc '+Edict['spc']
        if ave_rv==1:outstring=outstring+ ' -a'
        if Edict['usr']!="":outstring=outstring + ' -usr '+ Edict['usr']
        if 'loc' in Edict.keys() and  Edict['loc']!="":outstring=outstring + ' -loc "'+ Edict['loc']+'"'
        if Edict['ins']!="":outstring=outstring + ' -ins '+ Edict['ins']
        print outstring
        os.system(outstring)
        try:  # add file to measurements.log
            filelist=[]
            logfile=open(opath+"/measurements.log",'r')
            for line in logfile.readlines():
                if line.split()[0] not in filelist:filelist.append(line.split()[0])
            if basename+'.magic' not in filelist:filelist.append(basename+'.magic')
        except IOError:
            filelist=[basename+'.magic']
        logfile=open(opath+"/measurements.log",'w')
        for f in filelist:
            logfile.write(f+' | '+outstring+'\n')
        logfile.close()
#    tkMessageBox.showinfo("Info",file+" converted to magic format and added to measurements.log  \n Check command window for errors")


def add_ODP_srm(): 
    pass
def add_ODP_csv():
    global Edict
    AVE_types=["Average replicate measurements","Do not average replicate measurements"]
    ave_rv=ask_radio(root,AVE_types,'choose desired averaging option:') #
    fpath=tkFileDialog.askopenfilename(title="Set input file:")
    file=fpath.split('/')[-1] 
    basename=file
    ofile=opath+"/"+file
    infile=open(fpath,'rU').readlines()
    out=open(ofile,'w') # copy file to MagIC project directory
    for line in infile:
        out.write(line)
    out.close()
    outstring='ODP_csv_magic.py  -WD '+'"'+opath+'"'+ ' -F '+file+'.magic -f '+ofile
    if ave_rv==1:outstring=outstring+ ' -A'
    try:
        sampfile=open(opath+"/er_samples.txt",'r') # append to existing er_samples file
        outstring=outstring + ' -Fsa er_samples.txt'
    except IOError:
        pass
    print outstring
    os.system(outstring)
    try:
        logfile=open(opath+"/measurements.log",'a')
        logfile.write(basename+".magic" +" | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/measurements.log",'w')
        logfile.write(basename+".magic" +" | " + outstring+"\n")

def add_ODP_spn():
    global Edict
    fpath=tkFileDialog.askopenfilename(title="Set input file:")
    file=fpath.split('/')[-1] 
    basename=file
    ofile=opath+"/"+file
    infile=open(fpath,'rU').readlines()
    out=open(ofile,'w') # copy file to MagIC project directory
    for line in infile:
        out.write(line)
    out.close()
    AVE_types=["Average replicate measurements","Do not average replicate measurements"]
    ave_rv=ask_radio(root,AVE_types,'choose desired averaging option:') #
    LP_types=["AF demagnetization","Thermal demagnetization","Anhysteretic remanence","Isothermal Remanence"]
    LP_rv=ask_radio(root,LP_types,'choose desired treatment type:') #
    outstring='ODP_spn_magic.py  -WD '+'"'+opath+'"'+ ' -F '+file+'.magic -f '+file
    if ave_rv==1:outstring=outstring+ ' -A'
    if LP_rv==0:outstring=outstring+ ' -LP AF'
    if LP_rv==1:outstring=outstring+ ' -LP T'
    if LP_rv==2:
        dc=raw_input("What was your DC field (uT): ")
        outstring=outstring+ ' -LP A '+dc
    if LP_rv==3:outstring=outstring+ ' -LP I'
    vol_types=["Change default volume? ","Assume 10.5 cc"]
    vol_rv=ask_radio(root,vol_types,'choose desired volume option:') #
    if vol_rv==0:
        vol=raw_input("What was your assumed volume (cc): ")
        outstring=outstring + " -v "+vol
    print outstring
    os.system(outstring)
    try:
        logfile=open(opath+"/measurements.log",'a')
        logfile.write(basename+".magic" +" | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/measurements.log",'w')
        logfile.write(basename+".magic" +" | " + outstring+"\n")


def add_ODP_dsc():
    global Edict
    AVE_types=["Average replicate measurements","Do not average replicate measurements"]
    ave_rv=ask_radio(root,AVE_types,'choose desired averaging option:') #
    dpath=tkFileDialog.askdirectory(title="Select Directory of ODP discrete sample files for import ")
    filelist=os.listdir(dpath) # get directory listing
    dirname=dpath.split('/')[-1]
    try:
        dirlist=os.listdir(opath+'/'+dirname) # check if existing directory
        print dirlist
        for f in dirlist:
            os.remove(opath+'/'+dirname+'/'+f) # clean it out
            print 'removing  ',opath+'/'+dirname+'/'+f
    except:
        os.mkdir(opath+'/'+dirname)
    for file in filelist: 
      if file.split('.')[-1].lower()=='dsc':
        ofile=opath+'/'+dirname+"/"+file
        infile=open(dpath+'/'+file,'rU').readlines()
        out=open(ofile,'w') # copy file to MagIC project directory
        for line in infile:
            out.write(line)
        out.close()
    outfile=dirname+'.magic'
    outstring='ODP_dsc_magic.py  -WD '+opath+'/'+dirname+'/'+' -F '+dirname+'.magic'
    outstring=outstring + ' -Fsa er_samples.txt -Fsp er_specimens.txt'
    if ave_rv==1:outstring=outstring+ ' -A'
    print outstring
    os.system(outstring)
    try: # combine er_sample data
        open(opath+"/er_samples.txt",'r') # append to existing er_samples file
        Samps,file_type=pmag.magic_read(opath+"/er_samples.txt") # append to existing er_samples file
        NewSamps,file_type=pmag.magic_read(opath+'/'+dirname+"/er_samples.txt") 
        samples,OutSamps=[],[]
        for samp in Samps:
            if samp['er_sample_name'] not in samples:
                samples.append(samp['er_sample_name'])
                OutSamps.append(samp) 
        for samp in NewSamps:
            if samp['er_sample_name'] not in samples:
                samples.append(samp['er_sample_name'])
                OutSamps.append(samp) 
        Samps,keys=pmag.fillkeys(OutSamps)
        pmag.magic_write(opath+'/er_samples.txt',Samps,'er_samples.txt') # write combined file to project directory
    except IOError:
        os.rename(opath+'/'+dirname+'/er_samples.txt', opath+'/er_samples.txt')
    try: # combine er_specimen data
        open(opath+"/er_specimens.txt",'r') # append to existing er_samples file
        Samps,file_type=pmag.magic_read(opath+"/er_specimens.txt") # append to existing er_samples file
        NewSamps,file_type=pmag.magic_read(opath+'/'+dirname+"/er_specimens.txt") 
        samples,OutSamps=[],[]
        for samp in Samps:
            if samp['er_specimen_name'] not in samples:
                samples.append(samp['er_specimen_name'])
                OutSamps.append(samp) 
        for samp in NewSamps:
            if samp['er_specimen_name'] not in samples:
                samples.append(samp['er_specimen_name'])
                OutSamps.append(samp) 
        Samps,keys=pmag.fillkeys(OutSamps)
        pmag.magic_write(opath+'/er_specimens.txt',Samps,'er_specimens.txt') # write combined file to project directory
    except IOError:
        os.rename(opath+'/'+dirname+'/er_specimens.txt', opath+'/er_specimens.txt')
    os.rename(opath+'/'+dirname+'/'+dirname+'.magic', opath+'/'+dirname+'.magic')
    try:  # add file to measurements.log
        filelist=[]
        logfile=open(opath+"/measurements.log",'r')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
        if outfile not in filelist:filelist.append(outfile)
    except IOError:
        filelist=[outfile]
    logfile=open(opath+"/measurements.log",'w')
    for f in filelist:
        logfile.write(f+' | '+outstring+'\n')
    logfile.close()
#    tkMessageBox.showinfo("Info",file+" converted to magic format and added to measurements.log  \n Check command window for errors")


def add_umich():
    global Edict
    dpath=tkFileDialog.askdirectory(title="Select Directory of .dat files for import ")
    ncn_rv=ask_radio(root,NCN_types,'select naming convention\n NB: all file names must have same naming convention relating specimen to sample and site:') # sets naming convention
    Edict={'usr':"",'spc':'1','ins':''}
    if ncn_rv==3: Edict['Z']=""
    if ncn_rv==6: Edict['Z']=""
    if ncn_rv!=5: Edict['loc']=""
    make_entry(root) 
    mcd_checks=ask_check(root,MCD_types,'select appropriate field methods:') # allows adding of meta data describing field methods
    MCD_list=map((lambda var:var.get()),mcd_checks) # returns method code  radio button list
    MCD=""
    for i in range(len(MCD_list)):
        if MCD_list[i]==1:MCD=MCD+MCD_types[i].split(":")[0]+":"
    filelist=os.listdir(dpath) # get directory listing
    for file in filelist: 
      if file.split('.')[1].lower()=='dat':
        basename=file
        ofile=opath+"/"+file
        infile=open(dpath+'/'+file,'rU').readlines()
        out=open(ofile,'w') # copy file to MagIC project directory
        for line in infile:
            out.write(line)
        out.close()
        outstring='UMICH_magic.py -WD '+'"'+opath+'"'+ ' -F '+file+'.magic'+' -f '+ file
        if MCD!="": # add method codes
            outstring=outstring+' -mcd '+MCD[:-1]
        outstring=outstring+' -ncn '+str(ncn_rv+1) 
        if ncn_rv==3 or ncn_rv==6:
            outstring=outstring+'-'+Edict['Z']
        if Edict['usr']!="":outstring=outstring + ' -usr '+ Edict['usr']
        if Edict['spc']!="":outstring=outstring + ' -spc '+ Edict['spc']
        if 'loc' in Edict.keys() and  Edict['loc']!="":outstring=outstring + ' -loc "'+ Edict['loc']+'"'
        print outstring
        os.system(outstring)
        try:  # add file to measurements.log
            filelist=[]
            logfile=open(opath+"/measurements.log",'r')
            for line in logfile.readlines():
                if line.split()[0] not in filelist:filelist.append(line.split()[0])
            if basename+'.magic' not in filelist:filelist.append(basename+'.magic')
        except IOError:
            filelist=[basename+'.magic']
        logfile=open(opath+"/measurements.log",'w')
        for f in filelist:
            logfile.write(f+' | '+outstring+'\n')
        logfile.close()

def add_tdt():
    global Edict
    dpath=tkFileDialog.askdirectory(title="Select Directory of .tdt files for import ")
    ncn_rv=ask_radio(root,NCN_types,'select naming convention\n NB: all file names must have same naming convention relating specimen to sample and site:') # sets naming convention
    Edict={'usr':"",'spc':'0'}
    if ncn_rv==3: Edict['Z']=""
    if ncn_rv==6: Edict['Z']=""
    if ncn_rv!=5: Edict['loc']=""
    make_entry(root) 
    filelist=os.listdir(dpath) # get directory listing
    for file in filelist: 
      if file.split('.')[1].lower()=='tdt':
        basename=file
        ofile=opath+"/"+file
        infile=open(dpath+'/'+file,'rU').readlines()
        out=open(ofile,'w') # copy file to MagIC project directory
        for line in infile:
            out.write(line)
        out.close()
        outstring='TDT_magic.py -WD '+'"'+opath+'"'+ ' -F '+file+'.magic'+' -f '+ file
        outstring=outstring+' -ncn '+str(ncn_rv+1) 
        if ncn_rv==3 or ncn_rv==6:
            outstring=outstring+'-'+Edict['Z']
        if Edict['usr']!="":outstring=outstring + ' -usr '+ Edict['usr']
        if Edict['spc']!="":outstring=outstring + ' -spc '+ Edict['spc']
        if 'loc' in Edict.keys() and  Edict['loc']!="":outstring=outstring + ' -loc "'+ Edict['loc']+'"'
        print outstring
        os.system(outstring)
        try:  # add file to measurements.log
            filelist=[]
            logfile=open(opath+"/measurements.log",'r')
            for line in logfile.readlines():
                if line.split()[0] not in filelist:filelist.append(line.split()[0])
            if basename+'.magic' not in filelist:filelist.append(basename+'.magic')
        except IOError:
            filelist=[basename+'.magic']
        logfile=open(opath+"/measurements.log",'w')
        for f in filelist:
            logfile.write(f+' | '+outstring+'\n')
        logfile.close()


def add_leg_ucsc():
    global fpath,basename,Result
    Result={'usr':'','loc':"unknown",'spc':'1'}
    fpath= tkFileDialog.askdirectory(title="Set directory with files to import")
    basename=fpath.split('/')[-1]  # this is the directory name for copying
    d=MagDialog(root)
    try:
        print opath,opath+'/'+basename
        shutil.copytree(fpath,opath+'/'+basename) # copy contents of directory to MagIC project directory
    except OSError: # directory already exists
        shutil.rmtree(opath+'/'+basename) # remove it
        shutil.copytree(fpath,opath+'/'+basename) # copy it again
    outstring='UCSC_leg_magic.py -WD '+opath+'/'+basename + ' -loc '+d.result['loc']
    if d.result['usr']!="":outstring=outstring + ' -usr '+ d.result['usr'] 
    if d.result['spc']!="":outstring=outstring + ' -spc '+ d.result['spc'] 
    print outstring
    os.system(outstring) # this should create a bunch of files in the new directory
    try:
        logfile=open(opath+"/ucsc_imports.log",'a')
        logfile.write(basename+'\n')
    except IOError:
        logfile=open(opath+"/ucsc_imports.log",'w')
        logfile.write(basename+'\n')
#    tkMessageBox.showinfo("Info",basename+" converted to magic format and added to ucsc_imports.log  \n Check command window for errors")

def add_ucsc():
    global fpath,basename,Edict
    fpath=tkFileDialog.askopenfilename(title="Set input file:")
    file=fpath.split('/')[-1] 
    basename=file
    ofile=opath+"/"+file
    infile=open(fpath,'rU').readlines()
    out=open(ofile,'w')
    for line in infile:
        out.write(line)
    out.close()
    outstring='UCSC_magic.py -WD '+'"'+opath+'"'+ ' -F '+basename+'.magic'+' -f '+ file
    os.system(outstring)
#    tkMessageBox.showinfo("Info",basename+' imported to MagIC, saved in magic_measurements format and added to ams.log  \n Check command window for errors')


def add_huji():
        global fpath,basename, Result
        Result={'usr':'','out':'','dc':'0','ac':'0','phi':'0','theta':'-90','loc':"unknown",'spc':'1'}
        if opath=="":
            print "Must set output directory first!"
            return
        fpath=tkFileDialog.askopenfilename(title="Set input file:")
        file=fpath.split('/')[-1] 
        basename=file
        ofile=opath+"/"+file
        LP_types=["AF: alternating field demagnetization","S: Shaw method paleointensity","T: Thermal de(re)magnetization including thellier but excluding TRM acquisition","NRM: no lab treatment","TRM: TRM acquisition experiment","ANI: anisotropy of TRM,IRM or ARM","D: double demagnetization","G: GRM protocol","I: IRM"]
        checks=ask_check(root,LP_types,'select lab protocols:\n ')
        LPlist= map((lambda var:var.get()),checks)
        d=MagDialog(root)
        LP=""
        for i in range(len(LPlist)):
             if LPlist[i]==1:
                 LP=LP+LP_types[i].split(':')[0]+":"
                 if "ANI" in LP.split(':'): 
                     try:
                         filelist=[]
                         logfile=open(opath+"/ani.log",'r')
                         for line in logfile.readlines():
                             if line.split()[0] not in filelist:filelist.append(line.split()[0])
                         if basename+'.magic' not in filelist:filelist.append(basename+'.magic')
                     except IOError:
                         filelist=[basename+'.magic']
                     logfile=open(opath+"/ani.log",'w')
                     for f in filelist:
                         logfile.write(f+'\n') 
                     logfile.close()
        d.result['LP']=LP[:-1]
        d.result['fpath']=fpath
        infile=open(fpath,'rU').readlines()
        out=open(ofile,'w')
        for line in infile:
            out.write(line)
        out.close()
        outstring='HUJI_magic.py  -F '+d.result['out']+' -f '+ ofile+ ' -LP ' + d.result['LP'] + ' -spc ' + d.result['spc'] 
        if d.result['loc']!="":outstring=outstring + ' -loc "'+ d.result['loc']+'"'
        if d.result['dc']!="0":outstring=outstring + ' -dc '+ d.result['dc'] + ' ' + d.result['phi'] + ' ' + d.result['theta']
        if d.result['usr']!="":outstring=outstring + ' -usr '+ d.result['usr'] 
        if d.result['noave']=="n":outstring=outstring + ' -A '
        ncn_rv=ask_radio(root,NCN_types,'select naming convention:') # sets naming convention
        outstring=outstring+' -ncn '+NCN_types[ncn_rv].split(":")[0]
        print outstring
        os.system(outstring)
        try:
            logfile=open(opath+"/measurements.log",'a')
            logfile.write(basename+".magic" +" | " + outstring+"\n")
        except IOError:
            logfile=open(opath+"/measurements.log",'w')
            logfile.write(basename+".magic" +" | " + outstring+"\n")
#        tkMessageBox.showinfo("Info",file+" converted to magic format and added to measurements.log  \n Check command window for errors")


def add_s_dir():
    global Edict
    spath= tkFileDialog.askdirectory()
    types=["-n: col. #1 is name - naming convention on next page\n if not, name must be root of filename","-sig: has sigma in last column"]
    checks=ask_check(root,types,'select options:\n ')
    checklist= map((lambda var:var.get()),checks)
    ncn_rv=ask_radio(root,NCN_types,'select naming convention:') # sets naming convention
    if ncn_rv==3: # need to specify Z
        Edict={'typ':'AMS','loc':'','usr':"",'ins':'','spc':'1','Z':"",'crd':'s'}
    if ncn_rv==5: # site_name and location in er_samples.txt file
        Edict={'typ':'AMS','usr':"",'ins':'','spc':'1','crd':'s'}
    else:  # all others
        Edict={'typ':'AMS','loc':'','usr':"",'ins':'','spc':'1','crd':'s'}
    print """
    -loc LOCNAME : specify location/study name, (only if naming convention < 6)
    -spc: number of characters to distinguish from sample name
    -typ: anisotropy type: AMS, AARM, ATRM
    -usr: name of person who made measurements
    -ins: name of instrument (e.g., SIO:Bruno)
    -crd: [s,g,t] coordinate system of data
    """
    make_entry(root)
    Edict['ncn']=ncn_rv
    Edict['n']=checklist[0]
    Edict['sig']=checklist[1]
    filelist=os.listdir(spath)
    for file in filelist:
        if ncn_rv!=6 and checklist[0]==0:
            Edict['spn']=file.split('.')[0]
        add_s_file(spath+'/'+file)
    tkMessageBox.showinfo("Info","Import of directory completed - select Assemble Measurement before plotting\n Check terminal window for errors")

def add_s():
    global Edict
    if opath=="":
        print "Must set output directory first!"
        return
    spath=tkFileDialog.askopenfilename(title="Set .s  input file:")
    types=["-n: col. #1 is name - naming convention on next page","-sig: has sigma in last column"]
    checks=ask_check(root,types,'select options:\n ')
    checklist= map((lambda var:var.get()),checks)
    ncn_rv=ask_radio(root,NCN_types,'select naming convention:') # sets naming convention
    file=spath.split('/')[-1] 
    basename=file.split('.')[0]
    if ncn_rv==3: # need to specify Z
        Edict={'typ':'AMS','loc':'','usr':"",'ins':'','spc':'1','Z':"",'crd':'s'}
    if ncn_rv==5: # site_name and location in er_samples.txt file
        Edict={'typ':'AMS','usr':"",'ins':'','spc':'1','crd':'s'}
    else:  # all others
        Edict={'typ':'AMS','loc':'','usr':"",'ins':'','spc':'1','crd':'s'}
    if checklist[0]==0: Edict['spn']=basename
    print """
    -loc LOCNAME : specify location/study name, (only if naming convention < 6)
    -spc: number of characters to distinguish from sample name
    -typ: anisotropy type: AMS, AARM, ATRM 
    -usr: name of person who made measurements
    -ins: name of instrument (e.g., SIO:Bruno)
    -crd: [s,g,t] coordinate system of data 
    -spn: specimen name  (only if names not first column in file)
    """
    make_entry(root)
    Edict['ncn']=ncn_rv
    Edict['n']=checklist[0]
    Edict['sig']=checklist[1]
    add_s_file(spath)

def add_s_file(spath):
    file=spath.split('/')[-1] 
    ofile=opath+'/'+file
    basename=file.split('.')[0]
    outstring='s_magic.py -WD '+opath+ ' -F '+basename+'_anisotropy.txt -f '+ file +' -ncn '+str(Edict['ncn']+1)
    if Edict['ncn']==3 and Edict['Z']!="":
        outstring=outstring + '-'+Edict['Z']
    elif Edict['ncn']==3:
        tkMessageBox.showinfo("Info","Must specify 'Z' with this naming convention")
        add_s()
    if Edict['usr']!="":outstring=outstring + ' -usr '+ Edict['usr']
    if Edict['typ']!="":outstring=outstring + ' -typ '+ Edict['typ']
    if Edict['spc']!="":outstring=outstring + ' -spc '+ Edict['spc']
    if 'loc' in Edict.keys() and Edict['loc']!="":outstring=outstring + ' -loc '+ "'"+ Edict['loc']+"'"
    if 'spn' in Edict.keys() and Edict['spn']!="":outstring=outstring + ' -spn '+"'"+ Edict['spn']+"'"
    if Edict['crd']=='g':outstring=outstring+' -crd g' 
    if Edict['crd']=='t':outstring=outstring+' -crd t' 
    infile=open(spath,'rU').readlines()
    out=open(ofile,'w')
    for line in infile:
        out.write(line)
    out.close()
    if Edict['n']==1:outstring=outstring+' -n '
    if Edict['sig']==1:outstring=outstring+' -sig '
    print outstring
    os.system(outstring)
    try:
        filelist=[]
        logfile=open(opath+"/ams.log",'r')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
        if basename+'.magic' not in filelist:filelist.append(basename+'_anisotropy.txt')
    except IOError:
        filelist=[basename+'_anisotropy.txt']
    logfile=open(opath+"/ams.log",'w')
    for f in filelist:
        logfile.write(f+'\n') 
    logfile.close()
    print basename+' imported to MagIC, saved in rmag_anisotropy format and added to ams.log.'

def add_k15():
    global Edict
    kpath=tkFileDialog.askopenfilename(title="Set .k15  file:")
    file=kpath.split('/')[-1]
    basename=file.split('.')[0]
    ncn_rv=ask_radio(root,NCN_types,'select naming convention:') # sets naming convention
    if ncn_rv==3: # need to specify Z
        Edict={'loc':'','usr':"",'ins':'','spc':'1','Z':""}
    if ncn_rv==5: # site_name and location in er_samples.txt file
        Edict={'usr':"",'ins':'','spc':'1'}
    else:  # all others
        Edict={'loc':'','usr':"",'ins':'','spc':'1'}
    print """
    -loc LOCNAME : specify location/study name, (only if naming convention < 6)
    -spc: number of characters to distinguish from sample name
    -usr: name of person who made measurements
    -ins: name of instrument (e.g., SIO:Bruno)
    """
    make_entry(root)
    if ncn_rv==3 and Edict['Z']!="":
        outstring=outstring + '-'+Edict['Z']
    elif ncn_rv==3:
        tkMessageBox.showinfo("Info","Must specify 'Z' with this naming convention")
        add_k15()
    infile=open(kpath,'rU').readlines()
    kfile=opath+'/'+file
    out=open(kfile,'w')
    for line in infile: 
        out.write(line) # copies contents of source file to Project directory
    out.close()
    print kpath,' copied to ',kfile  
#
    outstring='k15_magic.py -WD '+'"'+opath+'"'+' -f '+file +' -F '+file+'.magic'+' -Fa '+file+'_anisotropy.txt -Fsa er_samples.txt' + ' -ncn '+str(ncn_rv+1)
    if 'loc' in Edict.keys() and Edict['loc']!="":outstring=outstring + ' -loc "'+ Edict['loc']+'"'
    if Edict['ins']!="":outstring=outstring + ' -ins '+ Edict['ins']
    if Edict['spc']!="":outstring=outstring + ' -spc '+ Edict['spc']
    if Edict['usr']!="":outstring=outstring + ' -usr '+ Edict['usr']
    print outstring
    os.system(outstring)
    try:
        filelist=[]
        logfile=open(opath+"/ams.log",'r')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
        if basename+'_anisotropy.txt' not in filelist:filelist.append(file+'_anisotropy.txt')
    except IOError:
        filelist=[file+'_anisotropy.txt']
    logfile=open(opath+"/ams.log",'w')
    for f in filelist:
        logfile.write(f+'\n') 
    logfile.close()
    try:
        logfile=open(opath+"/measurements.log",'a')
        logfile.write(file+".magic" +" | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/measurements.log",'w')
        logfile.write(file+".magic" +" | " + outstring+"\n")

def add_sufar4():
    global Edict
    kpath=tkFileDialog.askopenfilename(title="Set sufar4-asc  file:")
    file=kpath.split('/')[-1]
    infile=open(kpath,'rU').readlines()
    kfile=opath+'/'+file
    out=open(kfile,'w')
    for line in infile: 
        out.write(line) # copies contents of source file to Project directory
    out.close()
    print kpath,' copied to ',kfile  
#
    outstring='sufar4-asc_magic.py -WD '+'"'+opath+'"'+' -f '+file +' -F '+file+'.magic'+' -Fa '+file+'_anisotropy.txt '
    ncn_rv=ask_radio(root,NCN_types,'select naming convention:') # sets naming convention
    if NCN_types[ncn_rv].split(":")[0]=="9": # ODP naming convention
        outstring=outstring +  ' -spc  0 -ins ODP-KLY4S -ncn 9'
    else:
        outstring=outstring + ' -ncn '+NCN_types[ncn_rv].split(":")[0]
        Edict={'usr':"",'loc':"unknown",'spc':'1','ins':'unknown'}
        make_entry(root) 
        if Edict['usr']!="":outstring=outstring + ' -usr '+ Edict['usr']
        if Edict['loc']!="":outstring=outstring + ' -loc "'+ Edict['loc']+'"'
        if Edict['ins']!="":outstring=outstring + ' -ins '+ Edict['ins']
        if Edict['spc']!="":outstring=outstring + ' -spc '+ Edict['spc']
    print outstring
    os.system(outstring)
    if NCN_types[ncn_rv].split(":")[0]=="9": # ODP naming convention - fixing the stupid sample names (pads core number)
        outstring='ODP_fix_names.py  -WD '+opath+' -f '+file+'.magic'
        print outstring
        os.system(outstring)
        outstring='ODP_fix_names.py  -WD '+opath+' -f '+file+'_anisotropy.txt'
        print outstring
        os.system(outstring)
    try:
        filelist=[]
        logfile=open(opath+"/ams.log",'r')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
        if file+'_anisotropy.txt' not in filelist:filelist.append(file+'_anisotropy.txt')
    except IOError:
        filelist=[file+'_anisotropy.txt']
    try:
        filelist=[]
        logfile=open(opath+"/ams.log",'r')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
        if file+'_anisotropy.txt' not in filelist:filelist.append(file+'_anisotropy.txt')
    except IOError:
        filelist=[file+'_anisotropy.txt']
    logfile=open(opath+"/ams.log",'w')
    for f in filelist:
        logfile.write(f+'\n') 
    logfile.close()
#    tkMessageBox.showinfo("Info",file+' imported to MagIC, saved in rmag_anisotropy format and added to ams.log  \n Check command window for errors')
    try:
        logfile=open(opath+"/measurements.log",'a')
        logfile.write(file+".magic" +" | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/measurements.log",'w')
        logfile.write(file+".magic" +" | " + outstring+"\n")
#    tkMessageBox.showinfo("Info",'measurements saved in '+file+'.magic  and added to measurements.log  \n Check command window for errors')


def add_kly4s():
    global Edict
    kpath=tkFileDialog.askopenfilename(title="Set kly4s  file:")
    file=kpath.split('/')[-1]
    infile=open(kpath,'rU').readlines()
    kfile=opath+'/'+file
    out=open(kfile,'w')
    for line in infile: 
        out.write(line) # copies contents of source file to Project directory
    out.close()
    print kpath,' copied to ',kfile  
#
# build the command (outstring) for orientation_magic.py
#
    outstring='kly4s_magic.py -WD '+'"'+opath+'"'+' -f '+file +' -F '+file+'.magic'+' -Fa '+file+'_anisotropy.txt '
    ncn_rv=ask_radio(root,NCN_types,'select naming convention:') # sets naming convention
    if NCN_types[ncn_rv].split(":")[0]=="9": # ODP naming convention
        outstring=outstring +  ' -spc  0 -ins ODP-KLY4S'
    else:
        try:
            open(opath+'/er_samples.txt','rU')
            outstring=outstring+' -fsa er_samples.txt '
        except IOError:
            tkMessageBox.showinfo("Info","No orientation data imported, using specimen coordinates only\n  Import orientation file first, then re-import kly4s data.")
        outstring=outstring + ' -ncn '+NCN_types[ncn_rv].split(":")[0]
        Edict={'usr':"",'loc':"unknown",'spc':'1','ins':'SIO-KLY4S'}
        make_entry(root) 
        if Edict['usr']!="":outstring=outstring + ' -usr '+ Edict['usr']
        if Edict['loc']!="":outstring=outstring + ' -loc "'+ Edict['loc']+'"'
        if Edict['ins']!="":outstring=outstring + ' -ins '+ Edict['ins']
        if Edict['spc']!="":outstring=outstring + ' -spc '+ Edict['spc']
    print outstring
    os.system(outstring)
    if NCN_types[ncn_rv].split(":")[0]=="9": # ODP naming convention - fixing the stupid sample names (pads core number)
        outstring='ODP_fix_names.py  -WD '+opath+' -f '+file+'.magic'
        print outstring
        os.system(outstring)
        outstring='ODP_fix_names.py  -WD '+opath+' -f '+file+'_anisotropy.txt'
        print outstring
        os.system(outstring)
    try:
        filelist=[]
        logfile=open(opath+"/ams.log",'r')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
        if file+'_anisotropy.txt' not in filelist:filelist.append(file+'_anisotropy.txt')
    except IOError:
        filelist=[file+'_anisotropy.txt']
    logfile=open(opath+"/ams.log",'w')
    for f in filelist:
        logfile.write(f+'\n') 
    logfile.close()
#    tkMessageBox.showinfo("Info",file+' imported to MagIC, saved in rmag_anisotropy format and added to ams.log  \n Check command window for errors')
    try:
        logfile=open(opath+"/measurements.log",'a')
        logfile.write(file+".magic" +" | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/measurements.log",'w')
        logfile.write(file+".magic" +" | " + outstring+"\n")
#    tkMessageBox.showinfo("Info",'measurements saved in '+file+'.magic  and added to measurements.log  \n Check command window for errors')

def set_out(question=""):
        global opath,user
        opath= tkFileDialog.askdirectory()
#        print opath,' has been set'

def help_magic():
    """
    Help string
    """
    print help_magic.__doc__


def exit():
    sys.exit()

def zeq():
    z_command="zeq_magic.py "
    try:
        open(opath+'/magic_measurements.txt','r')
        z_command=z_command+ ' -f '+opath+'/magic_measurements.txt' 
        z_command=z_command+ ' -fsp ' +opath+"/zeq_specimens.txt"
    except IOError:
        tkMessageBox.showinfo("Info",'select Assemble Measurements in Import file first. ')
        return
    try:
        open(opath+'/er_samples.txt','r')
        z_command=z_command+ ' -crd g -fsa '+opath+'/er_samples.txt'
    except IOError:
        tkMessageBox.showinfo("Info",'No orientation file available, use specimen coordinates or import orientations')
    print z_command
    os.system(z_command)
    try:
        filelist=[]
        logfile=open(opath+"/specimens.log",'r')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
        if "zeq_specimens.txt" not in filelist:filelist.append("zeq_specimens.txt")
    except IOError:
        filelist=['zeq_specimens.txt']
    logfile=open(opath+"/specimens.log",'w')
    for file in filelist:
        logfile.write(file+'\n') 
    logfile.close()
#    tkMessageBox.showinfo("Info","Specimen interpretations saved in "+opath+'/zeq_specimens.txt \n Check command window for errors')

def thellier():
    t_command="thellier_magic.py -fsp "+opath+'/thellier_specimens.txt' 
    try:
        open(opath+'/magic_measurements.txt','r')
        t_command=t_command+' -f '+opath+'/magic_measurements.txt'
    except IOError:
        tkMessageBox.showinfo("Info",'Select Assemble in Import file first.')
        return
    try:
        open(opath+'/pmag_criteria.txt','r')
        t_command=t_command+' -f '+opath+'/magic_measurements.txt' +' -fcr '+opath+'/pmag_criteria.txt'
    except:
        pass
    try:
        open(opath+'/rmag_anisotropy.txt','rU')
        t_command=t_command+' -fan '+opath+'/rmag_anisotropy.txt'
    except:
        pass
    print t_command
    os.system(t_command)
    try:
        filelist=[]
        logfile=open(opath+"/specimens.log",'r')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
        if "thellier_specimens.txt" not in filelist:filelist.append("thellier_specimens.txt")
    except IOError:
        filelist=['thellier_specimens.txt']
    logfile=open(opath+"/specimens.log",'w')
    for file in filelist:
        logfile.write(file+'\n') 
    logfile.close()

def microwave():
    t_command="microwave_magic.py -fsp "+opath+'/microwave_specimens.txt' 
    try:
        open(opath+'/magic_measurements.txt','r')
        t_command=t_command+' -f '+opath+'/magic_measurements.txt'
    except IOError:
        tkMessageBox.showinfo("Info",'Select Assemble in Import file first.')
        return
    try:
        open(opath+'/pmag_criteria.txt','r')
        t_command=t_command+' -f '+opath+'/magic_measurements.txt' +' -fcr '+opath+'/pmag_criteria.txt'
    except:
        pass
    print t_command
    os.system(t_command)
    try:
        filelist=[]
        logfile=open(opath+"/specimens.log",'r')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
        if "microwave_specimens.txt" not in filelist:filelist.append("microwave_specimens.txt")
    except IOError:
        filelist=['microwave_specimens.txt']
    logfile=open(opath+"/specimens.log",'w')
    for file in filelist:
        logfile.write(file+'\n') 
    logfile.close()

def hysteresis():
    outstring="hysteresis_magic.py -f magic_measurements.txt -WD "+'"'+opath+'"'
    print outstring
    os.system(outstring)
#    tkMessageBox.showinfo("Info","Hysteresis parameters  saved in "+opath+'/rmag_hysteresis.txt and rmag_remanence.txt \n Check command window for errors')


def aniso():
    global Edict
    outstring='aniso_magic.py -WD '+opath
    if user != "": outstring=outstring+' -usr "'+user+'"'
    try:
        open(opath+'/rmag_anisotropy.txt','r')
        outstring=outstring+ ' -f rmag_anisotropy.txt' 
        outstring=outstring+ ' -F rmag_results.txt'
    except IOError:
        tkMessageBox.showinfo("Info",'select Assemble measurements first. ')
        return
    ELL_types=["-x: Hext ellipses","-B: suppress bootstrap","-par: parametric bootstrap","-v: plot bootstrap eigenvectors","-sit: plot by site instead of whole file"]
    ell_checks=ask_check(root,ELL_types,'select desired options:') # allows adding of meta data describing field methods
    ELL_list=map((lambda var:var.get()),ell_checks) # returns type of ellipse
    options=" "
    for i in range(len(ELL_list)):
        if ELL_list[i]==1:options=options+ELL_types[i].split(":")[0]+" "
    outstring=outstring+options
    outstring=outstring+ ' -crd g '
    print outstring
    os.system(outstring)

def sitemeans():
    clist,error=" ",0
    crd=["s: Specimen coordinates","g: geographic", "t: tilt corrected","b: both geo and tilt corrected"]
    sm=SMDialog(root) # gets the entry table data with all the good stuff in sm.result
    if sm.result['min']!="" and sm.result['max']!="" and sm.result["units"]!="":
        clist=clist+ ' -age '+sm.result['min']+' '+sm.result['max']+' '+'"'+sm.result['units']+'" '
    cust=['Use default criteria', 'Use no selection criteria','Customize criteria ']
    erfiles=['Import existing file','Will fill in later']
    try:
        open(opath+"/er_ages.txt",'rU')
        clist=clist+' -fa '+opath+'/er_ages.txt'
    except:
        print 'Ages missing, you should fill them in later'
    try:
        open(opath+"/magic_measurements.txt",'r')
    except IOError:
        tkMessageBox.showinfo("Info","Assemble measurements first")
        return
    sfiles=['Use default specimen file','Customize choice of specimen file']
    spec_rv=ask_radio(root,sfiles,'Choose option for specimen files:') # 
    if spec_rv==1:
        fpath=tkFileDialog.askopenfilename(title="Select specimen file for averaging at sample/site level")
        file=fpath.split('/')[-1] 
        basename=file.split('_')[-1]
        if basename!='specimens.txt':
            tkMessageBox.showinfo("Info","Must be a specimen file type: e.g., thellier_specimens.txt, AC_specimens.txt...")
            fpath=tkFileDialog.askopenfilename(title="Select specimen file for averaging at sample/site level")
            file=fpath.split('/')[-1] 
    else: 
        try:
            open(opath+"/pmag_specimens.txt",'r')
            file="pmag_specimens.txt"
        except IOError:
            tkMessageBox.showinfo("Info","Assemble specimens first")
            return
    clist=clist+' -fsp '+file
    try:
        open(opath+"/er_sites.txt",'r')
    except IOError:
        tkMessageBox.showinfo("Info","Make an er_sites.txt file, e.g. with orient.txt file")
        return
    OPT_types=["-D: Use default selection criteria","-C: Use no selection criteria", "-exc: Use customized selection criteria","-aD: Average multiple specimen lines per sample, default is by site","-aI: Average multiple specimen intensities per sample, default is by site","-sam: Calculate sample level VGPs/V[A]DMs, default is by site","-p: look at data by site","-lat: Use present latitude for VADM calculation","-fla model_lat.txt: use site paleolatitude data in model_lat.txt file","-xD: skip directions", "-xI: skip intensities","-pol: calculate averages by polarity"]
    opt_checks=ask_check(root,OPT_types,'select desired options:') #
    OPT_list=map((lambda var:var.get()),opt_checks) # returns method code  radio button list
    for opt in range(len(OPT_list)):
        if OPT_list[opt]==1:clist=clist+' '+OPT_types[opt].split(":")[0]+' '
    if OPT_list[6]==1:
        try:
            open(opath+"/model_lat.txt",'r')
        except IOError:
            tkMessageBox.showinfo("Info","Import paleolatitude file first ")
            return
    if '-xD' not in clist:
        try:
            open(opath+"/er_samples.txt",'r')
            crd_rv=ask_radio(root,crd,'Select Coordinate system') # sets coordinate system
            if crd_rv==0:clist=clist+' -crd s '
            if crd_rv==1:clist=clist+' -crd g '
            if crd_rv==2:clist=clist+' -crd t '
            if crd_rv==3:clist=clist+' -crd b '
        except IOError:
            pass
    outstring="specimens_results_magic.py  -WD "+'"'+opath+'"'+" "+clist
    print outstring
    os.system(outstring)
        
    
class SMDialog(tkSimpleDialog.Dialog): # makes an entry table for basic data from a .mag file
    def body(self, master):
        Label(master, text="Minimum age").grid(row=0)
        Label(master, text="Maximum age").grid(row=1)
        Label(master, text="age  units").grid(row=2)
        self.min = Entry(master)
        self.max=Entry(master)
        self.units=Entry(master)
        self.min.grid(row=0, column=1)
        self.max.grid(row=1, column=1)
        self.units.grid(row=2, column=1)
        return self.min # initial focus
    def apply(self):
        if self.min.get()!="":
            SMopts['min']=self.min.get()
        if self.max.get()!="":
            SMopts['max']=self.max.get()
        if self.units.get()!="":
            SMopts['units']=self.units.get()
        self.result=SMopts

class CRDialog(tkSimpleDialog.Dialog): # makes an entry table for basic data for cooling rate correction
    def body(self, master):
        Label(master, text="Cooling Rate Percent of uncorrected").grid(row=0)
        Label(master, text="Type: [EG, PS, TRM] for educated guess, pilot samples or 2TRM  ").grid(row=1)
        self.frac = Entry(master)
        self.type=Entry(master)
        self.frac.grid(row=0, column=1)
        self.type.grid(row=1, column=1)
        return self.frac # initial focus
    def apply(self):
        if self.frac.get()!="":
            SMopts['frac']=self.frac.get()
        if self.type.get()!="":
            SMopts['type']=self.type.get()
        self.result=SMopts

def vgp_map():
    global Edict
    outstring='vgpmap_magic.py -WD '+'"'+opath+'"'+ ' -res c -sym ro 5 -prj ortho '
    crd=["a: plot all","g: geographic", "t: tilt corrected"]
    crd_rv=ask_radio(root,crd,'Select Coordinate system') # sets coordinate system
    if crd_rv==1:outstring=outstring+' -crd g '
    if crd_rv==2:coutstring=outstring+' -crd t '
    crd=["all: plot as is" ,"rev: flip reverse data to antipode"]
    crd_rv=ask_radio(root,crd,'Select antipodes: ') # sets coordinate system
    if crd_rv==1:outstring=outstring+' -rev g^ 0'
    Edict={'eye_latitude': '90.','eye_longitude':0.}
    eye=make_entry(root) 
    outstring=outstring+' -eye '+Edict['eye_latitude']+' '+Edict['eye_longitude']+' '
    print outstring
    os.system(outstring)
    
def eqarea():
    files=[]
    try:
       open(opath+'/pmag_specimens.txt','r')
       files.append("Specimens")
    except:
       pass 
    try:
       open(opath+'/pmag_samples.txt','r')
       files.append("Samples")
    except:
        pass
    try:
       open(opath+'/pmag_sites.txt','r')
       files.append("Sites")
    except:
       pass
    try:
       open(opath+'/pmag_results.txt','r')
       files.append("Results")
    except:
       pass
    if len(files)==0:
       tkMessageBox.showinfo("Info","You have no files available for processing \n Assemble specimens first.")
       return
    file_rv=ask_radio(root,files,'Select File type') 
    if file_rv==0:FILE='pmag_specimens.txt -WD ' +opath
    if file_rv==1:FILE='pmag_samples.txt -WD ' +opath
    if file_rv==2:FILE='pmag_sites.txt -WD ' +opath
    if file_rv==3:FILE='pmag_results.txt -WD ' +opath
    outstring="eqarea_magic.py -f "+FILE 
    objs=["Whole file","By Site","By Sample","By Specimen"]
    obj_rv=ask_radio(root,objs,'Select Level for plotting')
    if obj_rv==0:outstring=outstring+' -obj all '
    if obj_rv==1:outstring=outstring+' -obj sit '
    if obj_rv==2:outstring=outstring+' -obj sam '
    if obj_rv==3:outstring=outstring+' -obj spc '
    ells=["None","Fisher","Kent","Bingham","Bootstrap ellipses","Bootstrap eigenvectors","Combine Lines & Planes"]
    ell_rv=ask_radio(root,ells,'Select Confidence ellipses')
    if ell_rv==1:outstring=outstring+' -ell F '
    if ell_rv==2:outstring=outstring+' -ell K '
    if ell_rv==3:outstring=outstring+' -ell B '
    if ell_rv==4:outstring=outstring+' -ell Be '
    if ell_rv==5:outstring=outstring+' -ell Bv '
    if ell_rv==6:
        outstring="lnp_magic.py -f "+FILE
        crit=["None","Existing"]
        crit_rv=ask_radio(root,crit,'Use selection criteria?  [To modify, use customize criteria option')
        if crit_rv==1:outstring=outstring+' -exc '
        
    try:
        f=open(opath+'/coordinates.log','r')
        coords=[]
        for line in f.readlines():
            coords.append(line.replace('\n',''))
        crd=["s: Specimen coordinates"]
        if '-crd g' in coords:crd.append("g: geographic")
        if '-crd t' in coords:crd.append("t: tilt corrected")
        crd_rv=ask_radio(root,crd,'Select Coordinate system') # sets coordinate system
        if crd_rv==0:outstring=outstring+' -crd s '
        if crd_rv==1:outstring=outstring+' -crd g '
        if crd_rv==2:outstring=outstring+' -crd t '
    except IOError:
        pass
    print outstring
    os.system(outstring)

def quick_look():
    try:
        data,file_type=pmag.magic_read(opath+"/magic_measurements.txt")
        NRMs=[]
        nrmfile=opath+'/nrm_measurements.txt'
        nrmspec=opath+'/nrm_specimens.txt'
        sampfile=opath+'/er_samples.txt'
        for rec in data:
            meths=rec["magic_method_codes"].replace(" ","").split(":")
            if "LT-NO" in meths:NRMs.append(rec)
        pmag.magic_write(nrmfile,NRMs,'magic_measurements')
        print "NRM measurements saved in ",nrmfile
    except:
        print "select assemble measurements first"
        return  
    mk_command = 'nrm_specimens_magic.py -A -f '+nrmfile+'  -F '+nrmspec +' -fsa '+sampfile  # don't average replicates
    eq_command = 'eqarea_magic.py -WD '+opath+' -f nrm_specimens.txt'
    try:
        open(opath+'/er_samples.txt','r')
        crd_OPTS=['Specimen','Geographic','Tilt adjusted']
        crd_rv=ask_radio(root,crd_OPTS,'select coordinate system:') # sets naming convention
        if crd_rv==1: 
            mk_command=mk_command+ ' -crd g -fsa '+opath+'/er_samples.txt -F '+nrmspec
            eq_command=eq_command+' -crd g '
        if crd_rv==2:
            mk_command=mk_command+ ' -crd t -fsa '+opath+'/er_samples.txt -F '+nrmspec
            eq_command=eq_command+' -crd t '
    except IOError:
        tkMessageBox.showinfo("Info",'No orientation file available, use specimen coordinates or import orientations')
    objs=["Whole file","By Site","By Sample"]
    obj_rv=ask_radio(root,objs,'Select Level for plotting')
    if obj_rv==1:eq_command=eq_command+' -obj sit '
    if obj_rv==2:eq_command=eq_command+' -obj sam '
    print mk_command
    os.system(mk_command)
    print eq_command
    os.system(eq_command)

def map_sites():
#    Cont=["Requires installation of basemap tool,  continue?   "]
#    cont_check=ask_check(root,Cont,'') # 
#    cont_list=map((lambda var:var.get()),cont_check) # 
#    if cont_list[0]==0: return
    try:
        open(opath+"/er_sites.txt",'r')
    except IOError:
        tkMessageBox.showinfo("Info",'No Site Table: import orientation data first')
        return
    outstring='basemap_magic.py -WD '+'"'+opath+'"'
    Opts=["c: Crude ","l: low", "i: intermediate [default]","h: high","Lambert conic confor. [default is Mercator]","Plot site names"]
    opts_check=ask_check(root,Opts,'Select Resolution, [c/l/i/h] and other options ') # sets resolution
    opts_list=map((lambda var:var.get()),opts_check) # 
    if opts_list[0]==1:outstring=outstring+' -res c '
    if opts_list[1]==1:outstring=outstring+' -res l '
    if opts_list[2]==1:outstring=outstring+' -res i '
    if opts_list[3]==1:outstring=outstring+' -res h '
    if opts_list[4]==1:outstring=outstring+' -prc lcc '
    if opts_list[5]==1:outstring=outstring+' -n '
    print outstring
    os.system(outstring)

def revtest():
    outstring='revtest_magic.py -WD '+'"'+opath+'"'
    try:
        f=open(opath+'/coordinates.log','r')
        coords=[]
        for line in f.readlines():
            coords.append(line.replace('\n',''))
        crd=["s: Specimen coordinates"]
        if '-crd g' in coords:crd.append("g: geographic")
        if '-crd t' in coords:crd.append("t: tilt corrected")
        crd_rv=ask_radio(root,crd,'Select Coordinate system') # sets coordinate system
        if crd_rv==0:outstring=outstring+' -crd s '
        if crd_rv==1:outstring=outstring+' -crd g '
        if crd_rv==2:outstring=outstring+' -crd t '
    except IOError:
        pass
    cust=['Use default criteria', 'Use no selection criteria','Customize criteria ']
    try:
        open(opath+"/pmag_criteria.txt",'r')
        crit_data,file_type=pmag.magic_read('pmag_criteria.txt')
        cust.append("Use previously customized  acceptance criteria")
    except IOError:
        pass
    cust_rv=ask_radio(root,cust,'Customize selection criteria?') # 
    if cust_rv!=0:
        outstring=outstring+' -exc '
        if cust_rv!=3:customize_criteria(cust_rv)
    print outstring
    os.system(outstring)

def fold():
    outstring='foldtest_magic.py -WD '+'"'+opath+'"'
    cust=['Use default criteria', 'Use no selection criteria','Customize criteria ']
    try:
        open(opath+"/pmag_criteria.txt",'r')
        crit_data,file_type=pmag.magic_read('pmag_criteria.txt')
        cust.append("Use previously customized  acceptance criteria")
    except IOError:
        pass
    cust_rv=ask_radio(root,cust,'Customize selection criteria?') # 
    if cust_rv!=0:
        outstring=outstring+' -exc '
        if cust_rv!=3:customize_criteria(cust_rv)
    print outstring
    os.system(outstring)

def EI():
    print "under construction" 

def dayplot():
    outstring='dayplot_magic.py -WD '+'"'+opath+'"'
    try:
        open(opath+"/rmag_hysteresis.txt",'r')
    except:
        tkMessageBox.showinfo("Info","option unavailable - you must run 'Hysteresis Data' option" )
        return
    print outstring
    os.system(outstring)

def curie():
    outstring='curie_magic.py -f magic_measurements.txt -F rmag_results.txt -WD '+'"'+opath+'"'
    print outstring
    os.system(outstring)
  
def irm_magic():
    outstring='irmaq_magic.py -WD '+'"'+opath+'"'
    print outstring
    os.system(outstring)

def chart():
    outstring='chartmaker.py'
    print outstring
    os.system(outstring)

def ANI_depthplot():
    global Edict
    try:
        open(opath+"/rmag_anisotropy.txt",'r')
        open(opath+"/magic_measurements.txt",'r')
    except IOError:
        tkMessageBox.showinfo("Info",'select Assemble measurements first.   ')
        return
    outstring='ANI_depthplot.py -WD '+'"'+opath+'"' +' -fb magic_measurements.txt '
    Edict={'Depth Max':'','Depth Min':''}
    make_entry(root)
    dmin,dmax=-1,-1
    if Edict['Depth Min']!='':dmin=Edict['Depth Min']
    if Edict['Depth Max']!='':
        dmax=Edict['Depth Max']
        outstring=outstring+' -d '+dmin+' '+dmax
    print outstring
    os.system(outstring)

def get_symbols():
    SYM_list=['circle', 'triangle_down','triangle_up','triangle_right','triangle_left', 'square', 'pentagon','star','hexagon','+','x','diamond','|','-']
    SYM_rv=ask_radio(root,SYM_list,'Which marker:') # 
    if SYM_rv==0: marker='o'
    if SYM_rv==1: marker='v'
    if SYM_rv==2: marker='^'
    if SYM_rv==3: marker='>'
    if SYM_rv==4: marker='<'
    if SYM_rv==5: marker='s'
    if SYM_rv==6: marker='p'
    if SYM_rv==7: marker='*'
    if SYM_rv==8: marker='h'
    if SYM_rv==9: marker='+'
    if SYM_rv==10: marker='x'
    if SYM_rv==11: marker='D'
    if SYM_rv==12: marker='|'
    if SYM_rv==13: marker='_'
    SYM_col=['blue', 'green','red','cyan','magenta', 'yellow', 'black','white']
    SYM_rv=ask_radio(root,SYM_col,'What color:')
    if SYM_rv==0: color='b'
    if SYM_rv==1: color='g'
    if SYM_rv==2: color='r'
    if SYM_rv==3: color='c'
    if SYM_rv==4: color='m'
    if SYM_rv==5: color='y'
    if SYM_rv==6: color='k'
    if SYM_rv==7: color='w'
    sym= color+marker
    SYM_size=['3pt', '5pt','7pt','10pt']
    SYM_rv=ask_radio(root,SYM_size,'What size:')
    if SYM_rv==0: size='3'
    if SYM_rv==1: size='5'
    if SYM_rv==2: size='7'
    if SYM_rv==3: size='10'
    return sym,size
    
def ODP_depthplot():
    global Edict
    syms={'sym':'bo','size':'5','dsym':'r^','dsize':'10'}
    try:
        open(opath+'/magic_measurements.txt') # check if pmag_results file exists
        outstring="ODP_depthplot.py -WD "+opath # get list of available plots
    except IOError:
        tkMessageBox.showinfo("Info",'Must assemble measurements first')
        return
    try:
        open(opath+"/er_samples.txt")
        outstring=outstring + ' -fsa er_samples.txt'
    except IOError:
        pass       
    Edict={'Step AF (mT)':'','Step T (C)':'','Peak field ARM (mT)':'','Step IRM (mT)':'','Depth Max':'','Depth Min':'','Time Scale (ck95,gts04)':'','Time Scale Age Max':'','Time Scale Age Min':''}
    make_entry(root)
    if Edict['Step AF (mT)']!='':outstring=outstring+ ' -LP AF '+Edict['Step AF (mT)']
    if Edict['Step T (C)']!='':outstring=outstring+ ' -LP T '+Edict['Step T (C) ']
    if Edict['Peak field ARM (mT)']!='':outstring=outstring+ ' -LP ARM '+Edict['Peak field ARM (mT)']
    if Edict['Step IRM (mT)']!='':outstring=outstring+ ' -LP IRM '+Edict['Step IRM (mT)']
    dmin,dmax=0,0
    if Edict['Depth Min']!='':dmin=Edict['Depth Min']
    if Edict['Depth Max']!='':
        dmax=Edict['Depth Max']
        outstring=outstring+' -d '+dmin+' '+dmax
    ts=''
    if Edict['Time Scale (ck95,gts04)']!='' and Edict['Time Scale Age Max']!='' and Edict['Time Scale Age Min']!='':
        outstring=outstring+' -ts '+Edict['Time Scale (ck95,gts04)']+' '+Edict['Time Scale Age Min']+' '+Edict['Time Scale Age Max']
    PLT_types=["Don't plot declinations","Don't plot inclinations","Don't plot intensities","Don't connect the dots","Don't plot the core boundaries","Don't plot the specimen directions","Don't use log scale for intensities","Customize long core symbols","Customize best-fit specimen symbols","Normalize intensity by weight"]
    plt_checks=ask_check(root,PLT_types,'choose plotting options:') #
    PLT_list=map((lambda var:var.get()),plt_checks) # returns method code  radio button list
    if PLT_list[7]!=0:
        syms['sym'],syms['size']=get_symbols()
    if PLT_list[8]!=0:
        syms['dsym'],syms['dsize']=get_symbols()
    outstring=outstring+' -sym '+'"'+syms['sym']+'"'+' '+syms['size']
    if PLT_list[9]!=0: outstring=outstring+' -n er_specimens.txt'
    if PLT_list[0]==1:outstring=outstring+' -D '
    if PLT_list[1]==1:outstring=outstring+' -I '
    if PLT_list[2]==1:outstring=outstring+' -M '
    if PLT_list[3]==1:outstring=outstring+' -L '
    if PLT_list[4]==0:
        try:
            logfile=open(opath+"/ODPsummary.log",'r')
            files=logfile.readlines()
            for file in files[-1:]: # fine most recently added
                if "summary" in file:
                    outstring=outstring + ' -fsum '+file.replace('\n','')
                    break
        except IOError:
            pass
    if PLT_list[5]==0:
        try:
            open(opath+"/zeq_specimens.txt",'r')
            outstring=outstring + ' -fsp zeq_specimens.txt ' + syms['dsym']+ ' ' +syms['dsize'] 
        except IOError:
            pass       
    else:
        outstring=outstring+' -S '
    if PLT_list[6]==0: outstring = outstring + ' -log'
        
    print outstring
    os.system(outstring)
    
  

def apwp():
    outstring='apwp.py'
    plate_types=['NA:North America','SA: South America','AF: Africa','IN: Indian','EU: European','AU: Australian','ANT: Antarctic','GL: Greenland']
    p_rv=ask_radio(root,plate_types,'select plate:') # sets plate
    plate=plate_types[p_rv].split(':')[0]
    a=ApwpDialog(root)
    print a
    outstring=outstring +' -F apwp.out  -P '+plate+' -lat '+a.result['lat'] +' -lon '+a.result['lon'] +' -age '+a.result['age'] 
    print outstring
    os.system(outstring)
    file=open('apwp.out','r')
    ans="   Age  Paleolat.  Expected Dec/Inc.  lat/lon of pole used.  \n"
    ans=ans+file.readline()
    tkMessageBox.showinfo("Info",ans)
    os.system("rm apwp.out")

    
def extract():
    outstring='pmag_results_extract.py -WD '+opath
    exfmt=['Tab delimited text file output','Latex format output'] 
    exfmt_rv=ask_radio(root,exfmt,'Format choice?') #
    if exfmt_rv==1: outstring = outstring+' -tex' 
    print outstring
    os.system(outstring)

    
def create_menus():
    filemenu=Menu(menubar)
    filemenu.add_command(label="Change Project MagIC Directory",command=set_out)
    filemenu.add_command(label="Clear Project MagIC Directory",command=start_over)
    filemenu.add_command(label="Unpack Downloaded txt File",command=download)
    filemenu.add_separator()
    filemenu.add_command(label="Exit ",command=exit)
    menubar.add_cascade(label="File",menu=filemenu)
    importmenu=Menu(menubar)
    orientmenu=Menu(importmenu)
    importmenu.add_cascade(label="Orientation/location/stratigraphic files",menu=orientmenu)
    orientmenu.add_command(label="orient.txt format",command=orient)
    orientmenu.add_command(label="AzDip format",command=azdip)
    orientmenu.add_command(label="ODP Core Summary csv file",command=add_ODP_sum)
    orientmenu.add_command(label="ODP Sample Summary csv file",command=add_ODP_samp)
    magmenu=Menu(importmenu)
    importmenu.add_cascade(label="Magnetometer files",menu=magmenu)
    magmenu.add_command(label="SIO format",command=add_mag)
    magmenu.add_command(label="LDEO format",command=add_ldgo)
    magmenu.add_command(label="CIT format",command=add_cit)
    magmenu.add_command(label="UU format",command=add_uu)
    magmenu.add_command(label="UB format",command=add_ub)
    magmenu.add_command(label="2G format",command=add_2G)
    UCSCmenu=Menu(magmenu)
    magmenu.add_cascade(label="UCSC formats",menu=UCSCmenu)
    UCSCmenu.add_command(label="UCSC New format",command=add_ucsc)
    UCSCmenu.add_command(label="UCSC legacy format",command=add_leg_ucsc)
    magmenu.add_command(label="LIV-MW format",command=add_liv)
    magmenu.add_command(label="HUJI format",command=add_huji)
    magmenu.add_command(label="PMD (Enkin) format",command=add_pmd_ascii)
    magmenu.add_command(label="PMD (IPG-PaleoMac) format",command=add_ipg)
    magmenu.add_command(label="UMICH (Gee) format",command=add_umich)
    magmenu.add_command(label="TDT format",command=add_tdt)
    magmenu.add_command(label="UR (JR6)  format",command=add_ur_jr6)
    ODPmenu=Menu(magmenu)
    magmenu.add_cascade(label="IODP formats",menu=ODPmenu)
    ODPmenu.add_command(label="ODP SRM .dsc files",command=add_ODP_dsc)
#    ODPmenu.add_command(label="ODP SRM .srm files",command=add_ODP_srm)
    ODPmenu.add_command(label="ODP SRM .csv files",command=add_ODP_csv)
    ODPmenu.add_command(label="ODP Minispin .spn files",command=add_ODP_spn)
    amsmenu=Menu(importmenu)
    importmenu.add_cascade(label="Anisotropy files",menu=amsmenu)
    s_menu=Menu(amsmenu)
    amsmenu.add_cascade(label=".s format",menu=s_menu)
    s_menu.add_command(label="import single .s file", command=add_s)
    s_menu.add_command(label="import entire directory", command=add_s_dir)
    amsmenu.add_command(label="kly4s format",command=add_kly4s)
    amsmenu.add_command(label="k15 format",command=add_k15)
    amsmenu.add_command(label="Sufar 4.0 ascii format",command=add_sufar4)
    agmmenu=Menu(importmenu)
    importmenu.add_cascade(label="Hysteresis files",menu=agmmenu)
    agmmenu.add_command(label="Import single agm file",command=add_agm)
    agmmenu.add_command(label="Import entire directory",command=add_agm_dir)
    importmenu.add_command(label="Curie Temperatures",command=add_curie)
    importmenu.add_separator()
    importmenu.add_command(label="Assemble measurements",command=meas_combine)
    importmenu.add_command(label="Convert er_samples => orient.txt",command=convert_samps)
    importmenu.add_command(label="Update measurements\n if new orientation imported",command=update_meas)
    importmenu.add_separator()
    importmenu.add_command(label="Import er_ages.txt",command=add_ages)
    menubar.add_cascade(label="Import",menu=importmenu)
    plotmenu=Menu(menubar)
    prior=Menu(plotmenu)
    plotmenu.add_cascade(label="Import prior interpretations",menu=prior)
    prior.add_command(label="PmagPy redo file",command=add_redo)
    prior.add_command(label="DIR (Enkin) file",command=add_DIR_ascii)
    prior.add_command(label="LSQ (Jones/PaleoMag) file",command=add_LSQ)
    prior.add_command(label="PMM (USCS) file",command=add_PMM)
    plotmenu.add_command(label="Customize Criteria ",command=custom)
    plotmenu.add_separator()
    plotmenu.add_command(label="Demagnetization data ",command=zeq)
    plotmenu.add_command(label="Thellier-type experiments",command=thellier)
    plotmenu.add_command(label="Microwave experiments",command=microwave)
    plotmenu.add_command(label="Anisotropy data",command=aniso)
    plotmenu.add_command(label="Hysteresis data",command=hysteresis)
    plotmenu.add_command(label="Curie Temperatures data",command=curie)
    plotmenu.add_command(label="Hysteresis parameters",command=dayplot)
    plotmenu.add_command(label="Plot IRM acquisition",command=irm_magic)
    plotmenu.add_command(label="Plot measurement data versus depth",command=ODP_depthplot)
    plotmenu.add_command(label="Plot AMS data versus depth",command=ANI_depthplot)
    plotmenu.add_separator()
    plotmenu.add_command(label="Assemble specimens",command=spec_combine)
    plotmenu.add_separator()
    plotmenu.add_command(label="Check sample orientations",command=site_edit)
    plotmenu.add_separator()
    plotmenu.add_command(label="Assemble results",command=sitemeans)
    plotmenu.add_command(label="Extract Results to Table",command=extract)
    plotmenu.add_command(label="Prepare Upload txt File",command=upload)
    menubar.add_cascade(label="Data Reduction",menu=plotmenu)
    utilitymenu=Menu(menubar)
    eqareamenu=Menu(utilitymenu)
    utilitymenu.add_cascade(label="Equal area plots",menu=eqareamenu)
    eqareamenu.add_command(label="Quick look - NRM directions",command=quick_look)
    eqareamenu.add_command(label="General equal area plots",command=eqarea)
    utilitymenu.add_command(label="Map of  VGPs",command=vgp_map)
    utilitymenu.add_command(label="Basemap of site locations",command=map_sites)
    utilitymenu.add_command(label="Reversal test",command=revtest)
    utilitymenu.add_command(label="Fold test ",command=fold)
    utilitymenu.add_command(label="Elong/Inc",command=EI,state="disabled")
    utilitymenu.add_command(label="Make IZZI exp.  chart",command=chart)
    utilitymenu.add_command(label="Expected directions/Paleolatitudes",command=apwp)
    utilitymenu.add_separator()
    menubar.add_cascade(label="Utilities",menu=utilitymenu)
#    helpmenu=Menu(menubar)
#    menubar.add_cascade(label="Help",menu=helpmenu)
#    helpmenu.add_command(label="About MagIC",command=help_magic)
    root.config(menu=menubar)



###
###
global Result,OrResult,user,ApwpResult,NCN_types,OCN_types,MCD_types
user=""
root=Tk()
root.title("MagIC-Py GUI")
#####
menubar=Menu(root)
frame=Frame(root)
frame.pack()
#l1=Label(frame,text="******************************************** ")
#l1.pack(side=TOP)
#l2=Label(frame,text=" ")
#l2.pack(side=TOP)
#l3=Label(frame,text=" ")
#l3.pack(side=TOP)
#l4=Label(frame,text="         Welcome to the MagIC-Py GUI         ")
#l4.pack(side=TOP)
#l5=Label(frame,text=" ")
#l5.pack(side=TOP)
#l6=Label(frame,text=" ")
#l6.pack(side=TOP)
#l7=Label(frame,text=" ")
#l7.pack(side=TOP)
#l8=Label(frame,text="******************************************** ")
#l8.pack(side=TOP)
l9=Label(frame,text=" Use the menu options to import files to magic format and make plots ")
l9.pack(side=TOP)
b=Button(frame,text="Quit",command=exit)
b.pack(side=TOP)
create_menus()
#####
tkMessageBox.showinfo("Info","First Step: \n Set Project MagIC Directory\n\n This should have NO SPACES in Path\n\n This Directory is to be used by this program ONLY.\n\n Only import files from a single Location or MagIC download file into this directory. ")
set_out()
#user=tkSimpleDialog.askstring("Enter MagIC mail name:","")
user=""
OrResult={'out':'er_samples.txt','gmt':'0','dec':'','Z':'','dcn':'1','dec':'','Z':'','ocn':'1','ncn':'1','a':0,'app':'n'}
SMopts={'usr':user,'min':"",'max':"",'units':"","crd":"s",'frac':"",'type':""}
ApwpResult={}
NCN_types=["1: XXXXY: where XXXX is site designation, Y is sample", "2: XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)", "3: XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)","4: XXXX[YYY] where YYY is sample designation with Z characters from site XXX; Z will be supplied on next page", "5: sample name=site name","6: OPTION NOT AVAILABLE, TO TIE SPECIAL SITE NAME TO SAMPLE, USE UPDATE MEASUREMENTS OPTION","7: [XXXX]YYY where XXXX is Z character long site name","8: this is a synthetic and has no site name","9: ODP naming convention"] 
OCN_types=["1: Lab arrow azimuth = mag_azimuth; Lab arrow dip=-field_dip (field_dip is hade)", "2: Lab arrow azimuth = mag_azimuth-90 (mag_azimuth is strike); Lab arrow dip = -field_dip","3: Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip (field_dip is inclination of lab arrow)","4: Lab arrow azimuth and dip are same as mag_azimuth, field_dip","5: Lab arrow azimuth and dip are mag_azimuth, field_dip-90 (field arrow is inclination of specimen Z direction)","6: Lab arrow azimuth = mag_azimuth-90 (mag_azimuth is strike); Lab arrow dip = 90-field_dip"]
MCD_types=["FS-FD: field sampling done with a drill","FS-H: field sampling done with hand samples","FS-LOC-GPS: field location done with GPS","FS-LOC-MAP:  field location done with map","SO-POM:  a Pomeroy orientation device was used","SO-ASC:  an ASC orientation device was used","SO-MAG: a magnetic compass was used","SO-SUN: a sun compass was used "]
root.mainloop()
