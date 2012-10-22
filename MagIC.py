#!/usr/bin/env python
from Tkinter import *
import exceptions,shutil
import tkFileDialog, tkSimpleDialog, string, os,sys,tkMessageBox,shutil
import pmag,string
#
#
class make_entry(tkSimpleDialog.Dialog): # makes an entry table for basic data from global variable Result
    def body(self, master):
        self.list=Edict.keys()
        self.list.sort()
        self.out=[]
        #Label(master, text=instruction).grid(row=0,coiumnspan=2)
        g=1
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
                self.l=Label(self.top, text=instruction)
                self.l.grid(row=0,columnspan=2,sticky=W)
                for i in range(len(input_d)):
                        self.var=IntVar()
                        self.cb=Checkbutton(self.top,variable=self.var, text=input_d[i])
                        self.cb.grid(row=i+1,columnspan=2,sticky=W)
                        self.check_value.append(self.var)
                self.b = Button(self.top, text="OK", command=self.ok)
                self.b.grid(row=i+2,columnspan=1)
        def ok(self):
                self.top.destroy()

def ask_check(parent,choices,title): # returns the values of the check box to caller
        global check_value
        m = make_check(parent,choices,title)
        parent.wait_window(m.top)
        return m.check_value

def custom():
    cust=['Use default criteria', 'Change default criteria','Change existing criteria ','Use no selection criteria']
    option=ask_radio(root,cust,'Customize selection criteria?') # 
    global Edict
    critout=opath+'/pmag_criteria.txt'
    if option==0: # use default
        crit_data=pmag.default_criteria(0)
        PmagCrits,critkeys=pmag.fillkeys(crit_data)
        pmag.magic_write(critout,PmagCrits,'pmag_criteria')
        print "Default criteria saved in pmag_criteria.txt"
        return
    elif option==1: # change default
        crit_data=pmag.default_criteria(0)
    elif option==2: # change existing
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
    elif option==3: # no criteria
        crit_data=pmag.default_criteria(1)
        PmagCrits,critkeys=pmag.fillkeys(crit_data)
        pmag.magic_write(critout,PmagCrits,'pmag_criteria')
        print "Extremely loose criteria saved in pmag_criteria.txt"
        return
    TmpCrits=[]
    for crit in crit_data:
        if len(crit.keys())>0:
            Edict={}
            for key in crit.keys():
                if crit[key]=='\n':crit[key]=""
                if crit[key]!="":Edict[key]=crit[key]
            c=make_entry(root) 
            for key in Edict.keys():crit[key]=Edict[key]
            crit['er_citation_names']="This study"
            crit['criteria_definition']="Criteria for selection"
            TmpCrits.append(crit)
    PmagCrits,critkeys=pmag.fillkeys(TmpCrits)
    critout=opath+'/pmag_criteria.txt'
    pmag.magic_write(critout,PmagCrits,'pmag_criteria')
#    tkMessageBox.showinfo("Info",'Selection criteria saved in pmag_criteria.txt\n check command window for errors')
    print "New Criteria saved in pmag_criteria.txt"

class make_agm: # makes an entry table for basic data for an AGM file
    def __init__(self,master):
        global AGM
        top=self.top=Toplevel(master)
        self.top.geometry('+50+50')
        Label(top,text='Fill in the following information for your study(* are required): ').grid(row=0,columnspan=2)
        Label(top, text="*******************").grid(row=1,sticky=W)
        Label(top, text="* Location name: [default=unknown]").grid(row=2,sticky=W)
        self.loc = Entry(top)
        self.loc.grid(row=2, column=1,sticky=W)
        Label(top, text="Measurer: ").grid(row=3,sticky=W)
        self.usr = Entry(top)
        self.usr.grid(row=3, column=1,sticky=W)
        Label(top, text="Instrument: ").grid(row=4,sticky=W)
        self.ins = Entry(top)
        self.ins.grid(row=4, column=1,sticky=W)
        g=5
        if AGM['spn']: # ask for specimen name and other particulars
            Label(top, text="* Specimen name").grid(row=g,sticky=W)
            self.spn=Entry(top,textvariable='')
            self.spn.grid(row=g, column=1,sticky=W)
        else: # importing whole directory - must follow strict file name rules
            Label(top, text="For importing directories: ").grid(row=g,sticky=W)
            Label(top, text="File names must be SPECIMEN_NAME.AGM for hysteresis").grid(row=g+1,sticky=W)
            Label(top, text="OR file names are  SPECIMEN_NAME.IRM for backfield (case insensitive)").grid(row=g+2,sticky=W)
        g+=3
        Label(top, text="* # characters to distinguish specimen from sample: [default=1]").grid(row=g,sticky=W)
        self.spc=Entry(top,textvariable='1')
        self.spc.grid(row=g, column=1,sticky=W)
        g+=1
        Label(top, text="*******************").grid(row=g,sticky=W)
        Label(top, text="Lab protocol particulars:").grid(row=g+1,sticky=W)
        Label(top, text="*******************").grid(row=g+2,sticky=W)
        g+=3
        self.rv = IntVar()
        Radiobutton(top,variable=self.rv, value=0,text='CGS units').grid(row=g,sticky="W")
        Radiobutton(top,variable=self.rv, value=1,text='SI units').grid(row=g+1,sticky="W")
        g+=2
        self.agm_check_value=[]
        if AGM['spn']: # also ask if backfield file 
            self.var=IntVar()
            self.cb=Checkbutton(top,variable=self.var, text='backfield curve')
            self.cb.grid(row=g,column=0,sticky=W)
            self.agm_check_value.append(self.var)
            g+=1
        self.b = Button(top, text="OK", command=self.ok)
        self.b.grid(row=g+1)
    def ok(self):
        global AGM
        if self.usr.get()!="":
            AGM['usr']=self.usr.get()
        if self.loc.get()!="":
            AGM['loc']=self.loc.get()
        if self.spc.get()!="":
            AGM['spc']=self.spc.get()
        if AGM['spn']:
            if self.spn.get()!="":
                AGM['spn']=self.spn.get()
            agmlist= map((lambda var:var.get()),self.agm_check_value)
        else:agmlist=[0]
        if agmlist[0]==1:AGM['bak']=1 # make it a backfield
        radio_value=self.rv.get()
        if radio_value==1:AGM['SI']=1 # make SI
        self.top.destroy()
0
def ask_agm(parent):
    global AGM
    m=make_agm(parent)
    parent.wait_window(m.top)

def add_agm_file():
    global AGM,names
  # copies .agm or .irm file sets up AGM settings for constructing command line
    basename,fpath=copy_text_file("Select AGM/IRM input file: ")
    names=ask_names(root) # gets naming convention
    if names['rv']==7: AGM['syn']=1 # see if synthetic?
    AGM['spn']=1 # won't ask for specimen name or whether backfield experiment
    AGM['bak']=0 # sets default to be hysteresis loop - not backfield
    ask_agm(root) # sets up AGM dictionary
    add_agm(fpath)

def add_agm_dir():
    global AGM,names
  # copies .agm and .irm files from whole directory to project directory, and sets up AGM settings for constructing command line
    dpath,filelist=copy_text_directory(" Select Directory with .AGM and/or .IRM files  for import ",['agm','irm'])
    names=ask_names(root) # name convention
    AGM['spn']=0 # don't ask for a specimen name - it must in the file name
    ask_agm(root) #  set up AGM dictionary settings
    for file in filelist: # step through file by file
        name_parts=file.split('.') # get specimen name and format
        spn=''
        for n in name_parts[0:-1]:spn=spn+n # skip the file format to create specimen name
        AGM['spn']=spn # set specimen name
        if name_parts[-1].lower()=='agm':AGM['bak']=0 # .agm means hysteresis
        if name_parts[-1].lower()=='irm':AGM['bak']=1 # .irm means backfield
        fpath=dpath+'/'+file 
        add_agm(fpath) 

def add_agm(fpath):
    global AGM,names
 # constructs command for AGM_magic.py
    file=fpath.split('/')[-1] 
    outstring='AGM_magic.py -WD '+opath+ ' -f '+file +' -F '+file+'.magic '+' -spc '+AGM['spc']
    if AGM['loc']!="":outstring=outstring + ' -loc "'+ AGM['loc']+'"' # er_location_name
    if AGM['usr']!="":outstring=outstring + ' -usr "'+ AGM['usr']+'"' # user name
    if AGM['ins']!="": outstring=outstring+' -ins '+AGM['ins'] # instrument name
    if AGM['bak']: outstring=outstring+' -bak ' # if a backfield curve
    if AGM['SI']==1: outstring=outstring+' -u SI ' # if SI units
    outstring=outstring+' -ncn '+'%s'%(names['rv']+1) # sets naming convention
    if names['rv']==3:outstring=outstring + '-'+'%s'%(names['Y'])
    if names['rv']==6:outstring=outstring + '-'+'%s'%(names['Z'])
    if names['rv']=='7': # synthetic
        outstring=outstring+' -Fsa '+opath+'/er_synthetics.txt -syn '+AGM['spn']
    else: # or not
        outstring=outstring+' -Fsa '+opath+'/er_specimens.txt -spn '+AGM['spn']
    print outstring
    os.system(outstring)
    try:
        logfile=open(opath+"/measurements.log",'a')
        logfile.write(file+".magic" +" | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/measurements.log",'w')
        logfile.write(file+".magic" +" | " + outstring+"\n")


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
        -ins INST : specify which instrument was used (e.g, MAG-Maud), default is "unknown"
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

class make_PlotOptions:
    global PlotOptions,COORDs
    def __init__(self,master):
        top=self.top=Toplevel(master)
        self.top.geometry('+50+50')
        Label(top,text='Check the desired plot options:').grid(row=0,columnspan=2)
        Label(top, text="*******************").grid(row=1,sticky=W)
        g=2
        self.coord_rv=IntVar()
        if len(COORDs)>1:
            for i in range(len(COORDs)):
                Radiobutton(top,variable=self.coord_rv,value=i,text=COORDs[i]).grid(row=g,stick=W)
                g+=1
        self.plt_check_value=[] 
        for op in PlotOptions: # make the check boxes for the plot
            self.var=IntVar()
            self.cb=Checkbutton(top,variable=self.var,text=op)
            self.cb.grid(row=g,sticky=W) 
            g+=1
            self.plt_check_value.append(self.var)
        self.b = Button(top, text="OK", command=self.ok)
        self.b.grid(row=g+1)
    def ok(self):
        global PlotOptions,COORDs
        PlotOptions.append(self.plt_check_value)
        if len(COORDs)>1:
            COORDs=COORDs[self.coord_rv.get()] # return the desired coordinate system
        self.top.destroy()

class make_ani:
    def __init__(self,master):
        top=self.top=Toplevel(master)
        self.top.geometry('+50+50')
        g=0
# make left hand panel with data and plotting options
        Label(top,text="Plotting Options").grid(row=g,columnspan=4)
        g+=1
        Label(top,text="Minimum Depth: ").grid(row=g,sticky=W)
        self.dmin=Entry(top)
        self.dmin.grid(row=g,column=1,sticky=W)
        g+=1
        Label(top,text="Maximum Depth: ").grid(row=g,sticky=W)
        self.dmax=Entry(top)
        self.dmax.grid(row=g,column=1,sticky=W)
        g+=1
        self.meters_rv = IntVar()
        Radiobutton(top,variable=self.meters_rv, value=0,text='meters').grid(row=g,sticky="W")
        self.mcd_rv = IntVar()
        Radiobutton(top,variable=self.mcd_rv, value=1,text='composite depth units').grid(row=g+1,sticky="W")
        g+=2
        b=Button(top,text="OK",command=self.ok)
        b.grid(row=g)
    def ok(self):
        global ANI
        if self.dmin.get()!="":
            ANI['dmin']=self.dmin.get()
        if self.dmax.get()!="":
            ANI['dmax']=self.dmax.get()
        ANI['mcd']=self.mcd_rv.get()
        self.top.destroy()

class make_strat:
    def __init__(self,master):
        top=self.top=Toplevel(master)
        self.top.geometry('+50+50')
        g=0
# make left hand panel with data and plotting options
        Label(top,text="Plotting Options").grid(row=g,columnspan=4)
        g+=1
        Label(top,text="Minimum Depth: ").grid(row=g,sticky=W)
        self.dmin=Entry(top)
        self.dmin.grid(row=g,column=1,sticky=W)
        g+=1
        Label(top,text="Maximum Depth: ").grid(row=g,sticky=W)
        self.dmax=Entry(top)
        self.dmax.grid(row=g,column=1,sticky=W)
        g+=1
        Label(top,text="AF step (mT): ").grid(row=g,sticky=W)
        self.af=Entry(top)
        self.af.grid(row=g,column=1,sticky=W)
        g+=1
        Label(top,text="Thermal step (C): ").grid(row=g,sticky=W)
        self.therm=Entry(top)
        self.therm.grid(row=g,column=1,sticky=W)
        g+=1
        Label(top,text="Peak field ARM (mT): ").grid(row=g,sticky=W)
        self.arm=Entry(top)
        self.arm.grid(row=g,column=1,sticky=W)
        g+=1
        Label(top,text="IRM (mT): ").grid(row=g,sticky=W)
        self.irm=Entry(top)
        self.irm.grid(row=g,column=1,sticky=W)
        g+=1
        Label(top,text="Time scale preference [ck95, gts04] ").grid(row=g,sticky=W)
        self.ts=Entry(top)
        self.ts.grid(row=g,column=1,sticky=W)
        g+=1
        Label(top,text="Time scale Minimum Age (Ma)").grid(row=g,sticky=W)
        self.amin=Entry(top)
        self.amin.grid(row=g,column=1,sticky=W)
        g+=1
        Label(top,text="Time scale Maximum Age (Ma)").grid(row=g,sticky=W)
        self.amax=Entry(top)
        self.amax.grid(row=g,column=1,sticky=W)
        g=1
# make right hand panel with for check boxes with plotting options
        self.strat_check_value=[] # make a list for check box values
        self.check_list=['Plot Declinations','Plot Inclinations','Plot Intensities [linear scale]','Plot Intensities [log scale]','Use weight normalized intensities','Plot BFL/FM directions from Specimens table', 'Plot directions in Results table','Plot core boundaries','Use composite depth scale','Connect long core symbols','Plot blanket specimen step']
        for box in self.check_list:
            self.var=IntVar()
            self.cb=Checkbutton(top,variable=self.var, text=box)
            self.cb.grid(row=g,column=2,sticky=W)
            self.strat_check_value.append(self.var)
            self.var=IntVar()
            g+=1
# customize symbols for long core measurements:
        row=0
        column=3
        Label(top,text="Long core symbol").grid(row=row,column=column,sticky=W)
        row+=1
        self.long_sym=IntVar()
        for sym in range(len(SYM_descr)):
            rb=Radiobutton(top,variable=self.long_sym,value=sym,text=SYM_descr[sym]) 
            rb.grid(row=row,column=column,sticky=W)
            row+=1
        column+=1
        row=0
        Label(top,text="Long core color").grid(row=row,column=column,sticky=W)
        row+=1
        self.long_color=IntVar()
        for sym in range(len(SYM_col_descr)):
            rb=Radiobutton(top,variable=self.long_color,value=sym,text=SYM_col_descr[sym]) 
            rb.grid(row=row,column=column,sticky=W)
            row+=1
        column+=1
        row=0
        Label(top,text="Long core size").grid(row=row,column=column,sticky=W)
        row+=1
        self.long_size=IntVar()
        for sym in range(len(SYM_size)):
            rb=Radiobutton(top,variable=self.long_size,value=sym,text=SYM_size[sym]) 
            rb.grid(row=row,column=column,sticky=W)
            row+=1
# customize symbols for discrete specimen  directions:
        row=0
        column+=1
        Label(top,text="Specimen direction marker").grid(row=row,column=column,sticky=W)
        row+=1
        self.disc_sym=IntVar()
        for sym in range(len(SYM_descr)):
            rb=Radiobutton(top,variable=self.disc_sym,value=sym,text=SYM_descr[sym]) 
            rb.grid(row=row,column=column,sticky=W)
            row+=1
        row=0
        column+=1
        Label(top,text="Specimen direction color").grid(row=row,column=column,sticky=W)
        row+=1
        self.disc_color=IntVar()
        for sym in range(len(SYM_col_descr)):
            rb=Radiobutton(top,variable=self.disc_color,value=sym,text=SYM_col_descr[sym]) 
            rb.grid(row=row,column=column,sticky=W)
            row+=1
        row=0
        column+=1
        Label(top,text="Specimen size").grid(row=row,column=column,sticky=W)
        row+=1
        self.disc_size=IntVar()
        for sym in range(len(SYM_size)):
            rb=Radiobutton(top,variable=self.disc_size,value=sym,text=SYM_size[sym]) 
            rb.grid(row=row,column=column,sticky=W)
            row+=1
        b=Button(top,text="OK",command=self.ok)
        b.grid(row=len(SYM_descr)+2)

    def ok(self):
        global STRAT,SYM_markers,SYM_colors,SYM_size
        if self.dmin.get()!="":
            STRAT['dmin']=self.dmin.get()
        if self.dmax.get()!="":
            STRAT['dmax']=self.dmax.get()
        if self.af.get()!="":
            STRAT['af']=self.af.get()
        if self.therm.get()!="":
            STRAT['therm']=self.therm.get()
        if self.arm.get()!="":
            STRAT['arm']=self.arm.get()
        if self.irm.get()!="":
            STRAT['irm']=self.irm.get()
        if self.ts.get()!="":
            STRAT['ts']=self.ts.get()
        if self.amin.get()!="":
            STRAT['amin']=self.amin.get()
        if self.amax.get()!="":
            STRAT['amax']=self.amax.get()
        if self.amax.get()!="":
            STRAT['amax']=self.amax.get()
        STRAT['strat_check_list']= map((lambda var:var.get()),self.strat_check_value)
        STRAT['long_sym']=SYM_markers[self.long_sym.get()]
        STRAT['long_color']=SYM_colors[self.long_color.get()]
        STRAT['long_size']=SYM_size[self.long_size.get()]
        STRAT['disc_sym']=SYM_markers[self.disc_sym.get()]
        STRAT['disc_color']=SYM_colors[self.disc_color.get()]
        STRAT['disc_size']=SYM_size[self.disc_size.get()]
        self.top.destroy()

class make_mag:
    def __init__(self,master):
        top=self.top=Toplevel(master)
        self.top.geometry('+50+50')
        Label(top,text='Fill in the following information for your study(* are required): ').grid(row=0,columnspan=2)
        Label(top, text="*******************").grid(row=1,sticky=W)
        Label(top, text="* Location name: [default=unknown]").grid(row=2,sticky=W)
        self.loc = Entry(top)
        self.loc.grid(row=2, column=1,sticky=W)
        Label(top, text="Measurer: ").grid(row=3,sticky=W)
        self.usr = Entry(top)
        self.usr.grid(row=3, column=1,sticky=W)
        Label(top, text="Average replicates [y/n]: [default is y] ").grid(row=4,sticky=W)
        self.noave = Entry(top)
        self.noave.grid(row=4, column=1,sticky=W)
        Label(top, text="* # characters to distinguish specimen from sample: [default=1]").grid(row=5,sticky=W)
        self.spc=Entry(top,textvariable='1')
        self.spc.grid(row=5, column=1,sticky=W)
        Label(top, text="instrument used?").grid(row=6,sticky=W)
        self.ins=Entry(top,textvariable='')
        self.ins.grid(row=6, column=1,sticky=W)
        g=7
        if MAG['LP']:
            Label(top, text="*******************").grid(row=g,sticky=W)
            Label(top, text="Lab protocol particulars:").grid(row=g+1,sticky=W)
            Label(top, text="*******************").grid(row=g+2,sticky=W)
            g+=3
            self.lp_check_value=[] 
            for i in range(len(LP_types)):
                self.var=IntVar()
                self.cb=Checkbutton(top,variable=self.var, text=LP_types[i])
                self.cb.grid(row=i+g,column=0,sticky=W)
                if i==1:g+=1 # make extra room if AF 
                if i==2:g+=1 # make extra room if Thermal
                self.lp_check_value.append(self.var)
            Label(top, text="leave blank if not needed").grid(row=g-2,column=2,sticky=E)
            Label(top, text="peak AF field (mT) if ARM:").grid(row=g-1,column=1,sticky=E)
            self.ac = Entry(top)
            self.ac.grid(row=g-1, column=2,sticky=W)
            Label(top, text="dc field (uT) for ARM/TRM:").grid(row=g,column=1,sticky=E)
            self.B = Entry(top)
            self.B.grid(row=g, column=2,sticky=W)
            g+=1
            Label(top, text="dc field (phi): [default=0]:").grid(row=g,column=1,sticky=E)
            self.phi = Entry(top)
            self.phi.grid(row=g, column=2,sticky=W)
            g+=1
            Label(top, text="dc field (theta): [default=-90]:").grid(row=g,column=1,sticky=E)
            self.theta = Entry(top)
            self.theta.grid(row=g, column=2,sticky=W)
            g+=3
            Label(top, text="Coil number for ASC impulse coil (if treatment units in Volts):").grid(row=g,column=1,sticky=E)
            self.coil = Entry(top)
            self.coil.grid(row=g, column=2,sticky=W)
            g+=2
        if MAG['MCD']==1:
            Label(top, text="*******************").grid(row=g,sticky=W)
            Label(top, text="Sampling particulars:").grid(row=g+1,sticky=W)
            Label(top, text="*******************").grid(row=g+2,sticky=W)
            g+=3
            self.mcd_check_value=[] 
            for i in range(len(MCD_types)):
                self.var=IntVar()
                self.cb=Checkbutton(top,variable=self.var, text=MCD_types[i])
                self.cb.grid(row=i+g,column=0,sticky=W)
                self.mcd_check_value.append(self.var)
            g=g+i
        self.b = Button(top, text="OK", command=self.ok)
        self.b.grid(row=g+1)
    def ok(self):
        global MAG
        if self.usr.get()!="":
            MAG['usr']=self.usr.get()
        if self.noave.get()!="":
            MAG['noave']=self.noave.get()
        else:
            MAG['noave']='y'
        if self.loc.get()!="":
            MAG['loc']=self.loc.get()
        else:
            MAG['loc']='unknown'
        if self.spc.get()!="":
            MAG['spc']=self.spc.get()
        if self.ins.get()!="":
            MAG['ins']=self.spc.get()
        if MAG['LP']==1:
            if self.B.get()!="":
                MAG['dc']=self.B.get()
            if self.phi.get()!="":
                MAG['phi']=self.phi.get()
            if self.theta.get()!="":
                MAG['theta']=self.theta.get()
            if self.ac.get()!="":
                MAG['ac']=self.ac.get()
            if self.coil.get()!="":
                MAG['coil']=self.coil.get()
            MAG['lp_check_value']=self.lp_check_value
        if MAG['MCD']==1:
            MCD=""
            MCD_list=map((lambda var:var.get()),self.mcd_check_value) # returns method code check box list
            for i in range(len(MCD_list)):
                if MCD_list[i]==1:MCD=MCD+MCD_types[i].split(":")[0]+":"
                MAG['mcd']='%s'%(MCD[:-1].strip(':'))
        self.top.destroy()

def ask_ani(parent):
    global ANI
    m=make_ani(parent)
    parent.wait_window(m.top)

def ask_strat(parent):
    global STRAT,SYM_descr, SYM_col_descr,SYM_size
    m=make_strat(parent)
    parent.wait_window(m.top)

def ask_plt(parent):
    global PlotOptions,COORDs
    m=make_PlotOptions(parent)
    parent.wait_window(m.top)

def ask_mag(parent):
    global MAG
    m=make_mag(parent)
    parent.wait_window(m.top)

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

def add_age(): # imports a site age file
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
    global opath
    basename,fpath=copy_text_file("Select paleolatitude file")
    mfile=opath+'/model_lat.txt'
    outstring='mv '+opath+'/'+basename+' '+mfile
    os.system(outstring)

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
    file,path=copy_text_file("Select ODP Sample Summary .csv file:")
    outstring='ODP_samples_magic.py -WD '+opath+' -f '+file+' -Fsa er_samples.txt'
    print outstring
    os.system(outstring)
           

#def ODP_fix_names():
#    filelist=os.listdir(opath)
#    for file in filelist: # fix up ODP sample names
#        if file.split(".")[-1]=='magic' or file.split("_")[-1]=='anisotropy.txt':
#            fname=file.split('/')[-1]
#            outstring='ODP_fix_names.py  -WD '+opath+' -f '+fname
#            print outstring
#            os.system(outstring)
#    
#
def add_ODP_sum():
    global apath
    file,path=copy_text_file("Select IODP Core Summary .csv file:")
    try:
        logfile=open(opath+"/ODPsummary.log",'a')
        logfile.write(file+"\n")
    except IOError:
        logfile=open(opath+"/ODPsummary.log",'w')
        logfile.write(file+"\n")


def add_ages():
    file,path=copy_text_file("Select er_ages formatted file: ")
    afile=opath+'/er_ages.txt'
    outstring='mv '+opath+'/'+file+' '+afile
    os.system(outstring)
    print file,' copied to er_ages.txt'

class make_names:
    def __init__(self,master):
        top=self.top=Toplevel(master)
        self.top.geometry('+50+50')
        Label(top,text='select naming convention').grid(row=0,columnspan=1)
        self.Z=StringVar()
        self.Y=StringVar()
        self.rv=IntVar()
    # make the naming convention check boxes
        for i in range(len(NCN_types)):
            ncn=NCN_types[i].split(":")
            Radiobutton(top,variable=self.rv,value=i,text=ncn[1]).grid(row=i+1,column=0,sticky=W)
            if ncn[0]=='4': 
               self.Y=Entry(self.top)
               self.Y.grid(row=i+1,column=1) 
            if ncn[0]=='7': 
               self.Z=Entry(self.top)
               self.Z.grid(row=i+1,column=1) 
        self.b = Button(top, text="OK", command=self.ok)
        self.b.grid(row=i+2,columnspan=2)
    def ok(self):
        global radio_value,Z,Y
        radio_value=self.rv.get()
        Z=self.Z.get()
        Y=self.Y.get()
        self.top.destroy()

def ask_names(parent):
    global radio_value,Z,Y
    m=make_names(parent)
    parent.wait_window(m.top)
    names={'rv':radio_value,'Z':Z,'Y':Y}
    while (names['rv']==3 and names['Y']=="") or (names['rv']==6 and names['Z']==""):
        print "You must specify the # characters for sample/site, with this naming convention"
        m=make_names(parent)
        parent.wait_window(m.top)
        names={'rv':radio_value,'Z':Z,'Y':Y}
    return names

class make_ocn:
    def __init__(self,master):
        global suns
        top=self.top=Toplevel(master)
        self.top.geometry('+50+50')
        Label(top,text='select orientation convention and declination correction').grid(row=0,columnspan=1)
        self.dec=StringVar()
        self.gmt=StringVar()
        self.ocn_rv=IntVar()
        self.dec_rv=IntVar()
    # make the naming convention check boxes
        for i in range(len(OCN_types)):
            ocn=OCN_types[i].split(":")
            Radiobutton(top,variable=self.ocn_rv,value=i,text=ocn[1]).grid(row=i+1,column=0,sticky=W)
        g=i+3
        for i in range(len(DCN_types)-1):
            dcn=DCN_types[i].split(":")
            Radiobutton(top,variable=self.dec_rv,value=i,text=dcn[1]).grid(row=i+g,column=0,sticky=W)
            if dcn[0]=='2': 
               self.dec=Entry(self.top)
               self.dec.grid(row=i+g,column=1,sticky=W)
        if suns>0: # ask for GMT offset
           dcn=DCN_types[-1].split(":")
           Label(top, text="Hours to ADD local time for GMT, default is 0:").grid(row=i+g+1,sticky=W)
           self.gmt=Entry(top)
           self.gmt.grid(row=i+g+1,column=1,sticky=W) 
        self.b = Button(top, text="OK", command=self.ok)
        self.b.grid(row=i+g+2,columnspan=2)
    def ok(self):
        global ocn_rv,dec_rv,dec,GMT,suns,app
        ocn_rv=self.ocn_rv.get()
        dec_rv=self.dec_rv.get()
        dec=self.dec.get()
        if suns!=0: 
            GMT=self.gmt.get()
            if GMT=="":GMT='0'
        else: GMT=""
        self.top.destroy()

def ask_ocn(parent):
    global ocn_rv,dec_rv,dec,GMT
    m=make_ocn(parent)
    parent.wait_window(m.top)
    orients={'ocn_rv':ocn_rv,'dec_rv':dec_rv,'dec':dec,'gmt':GMT}
    while (orients['ocn_rv']==1 and  orients['dec']==""):
        print "You must specify a declination correction, with dec convention #2!"
        m=make_ocn(parent)
        parent.wait_window(m.top)
        orients={'ocn_rv':ocn_rv,'dec_rv':dec_rv,'dec':dec,'gmt':GMT}
    return orients


def copy_text_file(title):
    path=tkFileDialog.askopenfilename(title=title)
    infile=open(path,'rU').readlines()
    file=path.split('/')[-1]
    basename=file
    ofile=opath+"/"+file
    out=open(ofile,'w') # copy file to MagIC directory
    for line in infile:
        out.write(line)
    print path,' copied to ',ofile
    return file,path

def copy_magic_file(title):
    path=tkFileDialog.askopenfilename(title=title)
    file=path.split('/')[-1]
    data,filetype=pmag.magic_read(path)
    cpfile=opath+'/'+file
    pmag.magic_write(cpfile,data,filetype) # copy over to project directory
    print path,' copied to ',cpfile
    return data,filetype,file,path

def orient(): # imports an orientation file to magic
    global orpath,suns
    ordata,location,file,orpath=copy_magic_file("Select orientation file:")
#
# check a few things
#
    Tilts=pmag.get_dictitem(ordata,'bedding_dip','','F') # are there bedding dips? 
    Suns=pmag.get_dictitem(ordata,'shadow_angle','','F') # are there sun compass data?
    suns=len(Suns)
    names=ask_names(root)
    orients=ask_ocn(root) # sets orientation convention 
    mcd_checks=ask_check(root,MCD_types,'Select field methods that apply to all samples:') # allows adding of meta data describing field methods
    MCD_list=map((lambda var:var.get()),mcd_checks) # returns method code  radio button list
    MCD=""
    for i in range(len(MCD_list)):
        if MCD_list[i]==1:MCD=MCD+MCD_types[i].split(":")[0]+":"
    orients['mcd']='%s'%(MCD[:-1].strip(':'))
    orients['ocn']='%s'%(OCN_types[ocn_rv].split(":")[0])
    orients['dcn']='%s'%(DCN_types[dec_rv].split(":")[0])
    orients['ncn']='%s'%(NCN_types[names['rv']])
#
# build the command (outstring) for orientation_magic.py
#
    outstring='orientation_magic.py -WD '+opath+ ' -ocn '+ orients['ocn'] + ' -f '+file + ' -dcn '+orients['dcn'] 
    if orients['dcn']=="2":outstring=outstring + ' %s'%(orients['dec'])
    outstring=outstring+' -ncn '+'%s'%(names['rv']+1)
    if names['rv']==3:outstring=outstring + '-'+'%s'%(names['Y'])
    if names['rv']==6:outstring=outstring + '-'+'%s'%(names['Z'])
    if orients['gmt']!="":outstring=outstring + ' -gmt '+'%s'%(orients['gmt'])
    if orients['mcd']!="":outstring=outstring + ' -mcd '+'%s'%(orients['mcd'])
    if len(Tilts)>0:
        BED_types=["Take fisher mean of bedding poles?","Don't correct bedding dip direction with declination - already correct"]
        bed_checks=ask_check(root,BED_types,'choose bedding conventions:') # 
        BED_list=map((lambda var:var.get()),bed_checks) # returns method code  radio button list
        if BED_list[0]==1:outstring=outstring+' -a '
        if BED_list[1]==1:outstring=outstring+' -BCN '
    Samps,filetype=pmag.magic_read(opath+'/er_samples.txt') # check if existing
    if len(Samps)>0: # there is an existing file
        if tkMessageBox.askyesno("","Update and append existing er_samples file? No will overwrite"): outstring=outstring + ' -app '
    print outstring
    os.system(outstring)
    try:
        logfile=open(opath+"/orient.log",'a')
        logfile.write("er_samples.txt/er_sites.txt/er_images.txt | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/orient.log",'w')
        logfile.write("er_samples.txt/er_sites.txt/er_images.txt  | " + outstring+"\n")
    update_crd()
#    tkMessageBox.showinfo("Info",file+" converted to magic format and added to orient.log \n check command window for errors")

def azdip(): 
    global orpath
    file,path=copy_text_file("Select AzDip file:")
    names=ask_names(root)
    mcd_checks=ask_check(root,MCD_types,'select appropriate field methods:') # allows adding of meta data describing field methods
    MCD_list=map((lambda var:var.get()),mcd_checks) # returns method code  radio button list
    MCD=""
    for i in range(len(MCD_list)):
        if MCD_list[i]==1:MCD=MCD+MCD_types[i].split(":")[0]+":"
    MCD=MCD.strip(":")
        
#
# build the command (outstring) for orientation_magic.py
#
    outstring='azdip_magic.py -Fsa '+opath +'/er_samples.txt' + ' -f ' + opath+'/'+file 
    outstring=outstring+' -ncn '+'%s'%(names['rv']+1)
    if names['rv']==3:outstring=outstring + '-'+'%s'%(names['Y'])
    if names['rv']==6:outstring=outstring + '-'+'%s'%(names['Z'])
    if MCD!="":outstring=outstring + ' -mcd '+MCD
    Samps,filetype=pmag.magic_read(opath+'/er_samples.txt') # check if existing
    if len(Samps)>0: # there is an existing file
        if tkMessageBox.askyesno("","Update and append existing er_samples file? No will overwrite"): outstring=outstring + ' -app '
    print outstring
    os.system(outstring)
    try:
        logfile=open(path+"/orient.log",'a')
        logfile.write("er_samples.txt/er_sites.txt | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/orient.log",'w')
        logfile.write("er_samples.txt/er_sites.txt  | " + outstring+"\n")
    update_crd()

def update_crd():
    geo,tilt=0,0
    orient,file_type=pmag.magic_read(opath+'/er_samples.txt')
    Geos=pmag.get_dictitem(orient,'sample_azimuth','','F') # orientations?
    Geos=pmag.get_dictitem(Geos,'sample_dip','','F') # orientations?
    if len(Geos)>0: geo=1
    Tilts=pmag.get_dictitem(orient,'sample_bed_dip_direction','','F') # orientations?
    Tilts=pmag.get_dictitem(Tilts,'sample_bed_dip','','F') # structural corrections?
    Tilts=pmag.get_dictitem(Tilts,'sample_bed_dip','0','F') # find non-zero tilts
    if len(Tilts)>0: tilt=1    
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
        Label(master, text="Hours to add to local time for GMT: [default=0]").grid(row=7)
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
        for file in filelist: 
            try:
                os.remove(opath+"/"+file)
            except:
                shutil.rmtree(opath+"/"+file)
        tkMessageBox.showinfo("Info","All files and directories removed from Project Directory\n check command window for errors")
    else:
        tkMessageBox.showinfo("Info","Clear was aborted - your files are safe")
 
def upload():
    # create a specimen table from the magic_measurements table
    try:
        measfile=opath+"/magic_measurements.txt"
        open(measfile,'rU') # test if there are measurements
        instfile=opath+"/magic_instruments.txt"
        sitefile=opath+"/er_sites.txt"
        specout=opath+"/er_specimens.txt"
        print "creating specimen and instrument files from magic_measurements.txt"
        pmag.ParseMeasFile(measfile,sitefile,instfile,specout)
    except:
        pass
    outstring="upload_magic.py -WD "+'"'+opath+'"' 
    print outstring
    os.system(outstring) # call upload magic

def download():
    file,path=copy_text_file("Select downloaded MagIC txt file:")
    outstring="download_magic.py -WD "+'"'+opath +'"'+' -f '+file
    print outstring
    os.system(outstring)
    filestring=""
    update_crd()
    filelist=os.listdir(opath)
    if 'pmag_specimens.txt'in filelist: # recreate zeq_specimens and thellier_specimens
        specdata,file_type=pmag.magic_read(opath+'/pmag_specimens.txt')
        DIRS=pmag.get_dictitem(specdata,'magic_method_codes','DIR','has')
        pmag.magic_write(opath+'/zeq_specimens.txt',DIRS,'pmag_specimens') # write out available directions
        PINTS=pmag.get_dictitem(specdata,'magic_method_codes','LP-PI-TRM','has')
        pmag.magic_write(opath+'/thellier_specimens.txt',PINTS,'pmag_specimens') # write out available directions
    spec_combine() # make all the specimen coordinate systems available for plotting

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
    rmag_anisotropy_instring=""
    rmag_results_instring=""
    filelist=os.listdir(opath)
    if 'aarm_measurements.txt' in filelist:
        aarmfile=open(opath+"/aarm_measurements.txt",'r')
        outstring='aarm_magic.py -WD '+'"'+opath+'"'
        print outstring
        os.system(outstring)
        rmag_anisotropy_instring=rmag_anisotropy_instring+' arm_anisotropy.txt '
        rmag_results_instring=rmag_results_instring+' aarm_results.txt '
    if 'atrm_measurments.txt' in filelist:
        atrmfile=open(opath+"/atrm_measurements.txt",'r')
        outstring='atrm_magic.py -WD '+'"'+opath+'"'
        print outstring
        os.system(outstring)
        rmag_anisotropy_instring=rmag_anisotropy_instring+' trm_anisotropy.txt '
        rmag_results_instring=rmag_results_instring+' atrm_results.txt '
    if rmag_anisotropy_instring!="":
        rmag_outstring='combine_magic.py -WD '+'"'+opath+'"' + ' -F rmag_anisotropy.txt -f '+rmag_anisotropy_instring
        print rmag_outstring
        os.system(rmag_outstring)
        rmag_outstring='combine_magic.py -WD '+'"'+opath+'"' + ' -F rmag_results.txt -f '+rmag_results_instring
        print rmag_outstring
        os.system(rmag_outstring)
    if 'zeq_specimens.txt' in filelist:
        open(opath+'/zeq_specimens.txt','r')
        outstring="mk_redo.py -f zeq_specimens.txt -F zeq_redo -WD "+'"'+opath+'"'
        print outstring
        os.system(outstring)
        basestring='zeq_magic_redo.py   -WD '+'"'+opath+'"'
        if 'coordinates.log' in filelist: 
            f=open(opath+'/coordinates.log','r')
            lines=f.readlines()
            coords=[]
            for line in lines:
                coords.append(line.replace('\n',''))
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
        else: # no coordinates.log file
            print 'problem in coordinates.log file'
            shutil.copyfile(opath+'/zeq_specimens.txt',opath+'/zeq_specimens_crd.txt')  # copy each data file to project directory
            filestring=filestring + ' zeq_specimens_crd.txt ' 
    if 'thellier_specimens.txt' in filelist:
        open(opath+'/thellier_specimens.txt') # check for thellier data 
        filestring=filestring+' thellier_specimens.txt '
        outstring="mk_redo.py -f thellier_specimens.txt -F thellier_redo  -WD "+'"'+opath+'"'
        os.system(outstring)
        print outstring
        outstring='thellier_magic_redo.py -WD '+'"'+opath+'"'
        if 'pmag_criteria.txt' in filelist:
            open(opath+'/pmag_criteria.txt','r')
            outstring=outstring+' -fcr pmag_criteria.txt '
        outstring = outstring + " -NLT " # do non-linear correction if available
        if 'rmag_anisotropy.txt' in filelist:
            f=open(opath+'/rmag_anisotropy.txt','rU')
            outstring=outstring + " -ANI " # do anisotropy correction
            ani=1
        os.system(outstring)
      #      print outstring
      #      replacestring='replace_AC_specimens.py  -WD '+'"'+opath+'"'
      #      print "CAUTION: replacing thellier data with anisotropy corrected data"
      #      print replacestring
      #      os.system(replacestring)
      #      filestring=filestring+' TorAC_specimens.txt '
      #  else:
           # os.system(outstring)
           # print outstring
    if len(filestring.split())>1:
        outstring='combine_magic.py -WD '+'"'+opath+'"'+' -F pmag_specimens.txt '+filestring +'\n'
        print outstring
        os.system(outstring)
    else:
        Recs=[{'er_specimen_name':""}]
        pmag.magic_write(opath+'pmag_specimens.txt',Recs,'pmag_specimens')
        print 'Created fake pmag_specimens.txt file in: ',opath+'/pmag_specimens.txt'

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
        ani_types=[]
        aarm_files=[]
        atrm_files=[]
        for line in logfile.readlines():
            description=line.split("|")
            file=description[0][:-1]
            if len(description)>1:
               LP=description[1].replace('\n',"").split(":")
               if LP[0].strip()=='T':
                   if file not in atrm_files:
                       atrm_files.append(file)
                       ani_types.append(description[1].replace('\n',""))
               else:
                   if file not in aarm_files:
                       aarm_files.append(file)
                       ani_types.append(description[1].replace('\n',""))
        if len(aarm_files)>0:
            filestring="-f "
            for k in range(len(aarm_files)):
                    filestring=filestring + aarm_files[k] + ' '
            outstring='combine_magic.py -WD '+'"'+opath+'"'+' -F aarm_measurements.txt '+filestring
            print outstring
            os.system(outstring)
        if len(atrm_files)>0:
            filestring="-f "
            for k in range(len(atrm_files)):
                    filestring=filestring + atrm_files[k] + ' '
            outstring='combine_magic.py -WD '+'"'+opath+'"'+' -F atrm_measurements.txt '+filestring
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
    global MAG
    MAG['LP'],MAG['MCD']=0,1 # don't get lab protocols, do get method codes
# copy over files
    fpath=tkFileDialog.askopenfilename(title="Select .sam file in directory with specimen data:")
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
# get the location, naming conventions, method codes, etc.
    ask_mag(root)
    names=ask_names(root)
    outstring='CIT_magic.py -WD '+'"'+opath+'"'+'  -f '+file + ' -F ' + file+'.magic'
    if MAG['mcd']!="": # add method codes
        outstring=outstring+' -mcd '+MAG['mcd']
    outstring=outstring+ ' -spc ' + MAG['spc']
    if MAG['loc']!="":outstring=outstring + ' -loc "'+ MAG['loc']+'"'
    if MAG['usr']!="":outstring=outstring + ' -usr '+ MAG['usr']
    if MAG['noave']=="n":outstring=outstring + ' -A '
    outstring=outstring+' -ncn '+'%s'%(names['rv']+1)
    if names['rv']==3:outstring=outstring + '-'+'%s'%(names['Y'])
    if names['rv']==6:outstring=outstring + '-'+'%s'%(names['Z'])
    if outstring[-1]=='8':outstring=outstring+' -Fsa '+opath+'/er_synthetics.txt'
    print outstring
    os.system(outstring)
    try:
        logfile=open(opath+"/measurements.log",'a')
        logfile.write(file+".magic  | " + outstring+"\n")
    except IOError:
        logfile=open(opath+"/measurements.log",'w')
        logfile.write(file+".magic | " + outstring+"\n")
    try: # add to orientation log
        logfile=open(opath+"/orient.log",'a')
        logfile.write("er_samples.txt/er_sites.txt | " + outstring+"\n")
    except:
        logfile=open(opath+"/orient.log",'w')
        logfile.write("er_samples.txt/er_sites.txt | " + outstring+"\n")



def add_redo():
    try:
        open(opath+'/magic_measurements.txt','r')
    except IOError:
        tkMessageBox.showinfo("Info","You must Combine Measurments first!")
        return
    lpath=tkFileDialog.askopenfilename(title="Select 'redo' file:")
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

def add_DIR_ascii():
    try:
        open(opath+'/magic_measurements.txt','r')
    except IOError:
        tkMessageBox.showinfo("Info","You must Combine Measurments first!")
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
        tkMessageBox.showinfo("Info","You must Combine Measurements first!")
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
        tkMessageBox.showinfo("Info","You must Combine Measurements first!")
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

def add_ldeo():
    add_mag('ldeo')

def add_sio():
    add_mag('sio')

def add_huji():
    add_mag('huji')

def add_tdt():
    add_mag('tdt')

def add_mag(ftype):
        global fpath,basename, MAG
        basename,fpath=copy_text_file("Select magnetometer format input file: ")
        ifile=opath+'/'+basename 
        outfile=opath+'/'+basename+'.magic'
        names=ask_names(root)
        ask_mag(root)
        LPlist= map((lambda var:var.get()),MAG['lp_check_value'])
        LP=""
        for i in range(len(LPlist)):
             if LPlist[i]==1:
                 LP=LP+LP_types[i].split(':')[0]+":"
                 if "ANI" in LP.split(':'): 
                     MAG['phi']='-1'
                     MAG['theta']='-1'
                     try:
                         filelist=[]
                         lp_types=[]
                         logfile=open(opath+"/ani.log",'r')
                         for line in logfile.readlines():
                             if line.split()[0] not in filelist:
                                 filelist.append(line.split()[0])
                                 lp_types.append(line.split()[2])
                         if basename+'.magic' not in filelist:
                             filelist.append(basename+'.magic')
                             lp_types.append(LP[:-1])
                     except IOError:
                         filelist=[basename+'.magic']
                         lp_types.append(LP[:-1])
                     logfile=open(opath+"/ani.log",'w')
                     for i in range(len(filelist)):
                         logfile.write(filelist[i]+' | '+ lp_types[i]+'\n') 
                     logfile.close()
        MAG['fpath']=fpath
        if ftype=='huji': 
            outstring = 'HUJI_magic.py '
        if ftype=='ldeo': 
            outstring = 'LDEO_magic.py '
        elif ftype=='sio':
            outstring = 'sio_magic.py '
        elif ftype=='tdt':
            outstring = 'TDT_magic.py '
        outstring=outstring+' -F '+outfile+' -f '+ ifile+ ' -LP ' + LP.strip(":") + ' -spc ' + MAG['spc'] 
        if MAG['loc']!="":outstring=outstring + ' -loc "'+ MAG['loc']+'"'
        if MAG['dc']!="0":outstring=outstring + ' -dc '+ MAG['dc'] + ' ' + MAG['phi'] + ' ' + MAG['theta']
        if MAG['coil']!="":outstring=outstring + ' -V '+ MAG['coil'] 
        if MAG['usr']!="":outstring=outstring + ' -usr '+ MAG['usr'] 
        if MAG['ins']!="":outstring=outstring + ' -ins '+ MAG['ins'] 
        if MAG['noave']=="n":outstring=outstring + ' -A '
        outstring=outstring+' -ncn '+'%s'%(names['rv']+1)
        if names['rv']==3:outstring=outstring + '-'+'%s'%(names['Y'])
        if names['rv']==6:outstring=outstring + '-'+'%s'%(names['Z'])
        if outstring[-1]=='8':outstring=outstring+' -Fsa '+opath+'/er_synthetics.txt'
        print outstring
        os.system(outstring)
        try:
            logfile=open(opath+"/measurements.log",'a')
            logfile.write(basename+".magic" +" | " + outstring+"\n")
        except IOError:
            logfile=open(opath+"/measurements.log",'w')
            logfile.write(basename+".magic" +" | " + outstring+"\n")



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

def copy_text_directory(title,fmtlist):
    # copies files matching formats in fmtlist to project directory
    dpath=tkFileDialog.askdirectory(title=title) # get directory path name
    filelist=os.listdir(dpath) # get directory listing
    outlist=[] # list of files copied
    for fmt in fmtlist: # look for each desired format 
        for file in filelist:
            if file.split('.')[-1].lower()==fmt: # check format
                outlist.append(file) # collect name
                basename=file
                ofile=opath+"/"+file
                infile=open(dpath+'/'+file,'rU').readlines() # this will convert to UNIX format
                out=open(ofile,'w') # copy file to MagIC project directory
                for line in infile:
                    out.write(line)
                out.close()
                print ofile,' copied to MagIC project directory'
    return dpath,outlist

def add_2G_bin():
    add_pmd_like('2G_bin')

def add_pmd_ascii():
    add_pmd_like('pmd')


def add_pmd_like(type):
    global MAG
    MAG['LP']=0
    MAG['MCD'],APP=1,0
    if type=='pmd': 
        title="Select Directory of .PMD files for import"
        fmt='pmd'
        basestring='PMD_magic.py '
    if type=='2G_bin': 
        title="Select Directory of .DAT files for import"
        fmt='dat'
        basestring='2G_bin_magic.py '
    dpath,pmdlist=copy_text_directory(title,[fmt])
    names=ask_names(root)
    ask_mag(root)
    outlist=[]
    Samps,filetype=pmag.magic_read(opath+'/er_samples.txt') # check if existing
    if len(Samps)>0: # there is an existing file
        APP=tkMessageBox.askyesno("","Update and append existing er_samples file? No will overwrite")
    for file in pmdlist: 
        outstring=basestring
        if pmdlist.index(file)==0 and APP==0:  # overwrite existing
            outstring=outstring+'  -WD '+'"'+opath+'"'+ ' -F '+file+'.magic'+' -f '+ file 
        else: # append to existing
            outstring=outstring+'  -WD '+'"'+opath+'"'+ ' -F '+file+'.magic'+' -f '+ file +' -Fsa er_samples.txt '
        if MAG['mcd']!="": # add method codes
            outstring=outstring+' -mcd '+MAG['mcd']
        outstring=outstring+ ' -spc ' + MAG['spc']
        if MAG['loc']!="":outstring=outstring + ' -loc "'+ MAG['loc']+'"'
        if MAG['usr']!="":outstring=outstring + ' -usr '+ MAG['usr']
        if MAG['noave']=="n":outstring=outstring + ' -A '
        outstring=outstring+' -ncn '+'%s'%(names['rv']+1)
        if names['rv']==3:outstring=outstring + '-'+'%s'%(names['Y'])
        if names['rv']==6:outstring=outstring + '-'+'%s'%(names['Z'])
        if outstring[-1]=='8':outstring=outstring+' -Fsa '+opath+'/er_synthetics.txt'
        print outstring
        os.system(outstring)
        outlist.append(outstring)
    try:
        logfile=open(opath+"/measurements.log",'a')
    except IOError:
        logfile=open(opath+"/measurements.log",'w')
    for k in range(len(pmdlist)):
        basename=pmdlist[k]
        outstring=outlist[k]
        logfile.write(basename+".magic" +" | " + outstring+"\n")
    update_crd()


def add_jr6():
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
    outstring='JR6_magic.py  -WD '+opath +'/'+' -F '+dirname+'.magic'
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


def add_srm_csv():
    global Edict
    fpath=tkFileDialog.askopenfilename(title="Set WebTabular SRM .csv file:")
    AVE_types=["Average replicate measurements","Do not average replicate measurements"]
    ave_rv=ask_radio(root,AVE_types,'choose desired averaging option:') #
    file=fpath.split('/')[-1] 
    basename=file
    ofile=opath+"/"+file
    infile=open(fpath,'rU').readlines()
    out=open(ofile,'w') # copy file to MagIC project directory
    for line in infile:
        out.write(line)
    out.close()
    outstring='IODP_csv_magic.py  -WD '+'"'+opath+'"'+ ' -F '+file+'.magic -f '+ofile
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
    -ins: name of instrument (e.g., MAG:Bruno)
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
    tkMessageBox.showinfo("Info","Import of directory completed - select Combine Measurement before plotting\n Check terminal window for errors")

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
    -ins: name of instrument (e.g., MAG:Bruno)
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
#    outstring='aniso_magic.py -WD '+opath+ ' -f '+basename+'_anisotropy.txt -F '+ base_name+'_results.txt -B -P' 
#    os.system(outstring)
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


def add_sufar4():
    add_ams('sufar4')

def add_k15():
    add_ams('k15')

def add_kly4s():
    add_ams('kly4s')


def add_ams(format): # add generic AMS data
    global MAG
    MAG['LP']=0
    file,kpath=copy_text_file(" Select AMS input file: ")
#
# build the command (outstring) for kly4s_magic.py
#
    if format=='sufar4':
        outstring='SUFAR4_asc_magic.py -WD '+'"'+opath+'"'+' -f '+file +' -F '+file+'.magic'+' -Fa '+file+'_anisotropy.txt '+'-Fsa er_samples.txt -Fs er_specimens.txt' 
    if format=='kly4s':
        outstring='KLY4S_magic.py -WD '+'"'+opath+'"'+' -f '+file +' -F '+file+'.magic'+' -Fa '+file+'_anisotropy.txt '
    if format=='k15':
        outstring='k15_magic.py -WD '+'"'+opath+'"'+' -f '+file +' -F '+file+'.magic'+' -Fa '+file+'_anisotropy.txt '+'-Fsa er_samples.txt' 
    names=ask_names(root)  # set naming convention
    ask_mag(root) # set up MAG dictionary
    if MAG['loc']!="":outstring=outstring + ' -loc "'+ MAG['loc']+'"' # er_location_name
    if MAG['usr']!="":outstring=outstring + ' -usr '+ MAG['usr'] # user name
    if MAG['ins']!="":outstring=outstring + ' -ins '+ MAG['ins'] # instrument name
    if MAG['spc']!="":outstring=outstring + ' -spc '+ MAG['spc'] # instrument name
    outstring=outstring+' -ncn '+'%s'%(names['rv']+1) # naming convention
    if names['rv']==3:outstring=outstring + '-'+'%s'%(names['Y'])
    if names['rv']==6:outstring=outstring + '-'+'%s'%(names['Z'])
    if outstring[-1]=='8':outstring=outstring+' -Fsa '+opath+'/er_synthetics.txt'
    print outstring # execute command
    os.system(outstring)
    try:
        filelist=[]
        logfile=open(opath+"/ams.log",'rU')
        for line in logfile.readlines():
            if line.split()[0] not in filelist:filelist.append(line.split()[0])
        if file+'_anisotropy.txt' not in filelist:filelist.append(file+'_anisotropy.txt')
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

def set_out(question=""):
        global opath,user
        opath= tkFileDialog.askdirectory()
#        print opath,' has been set'

def help_PmagPy():
    helpme="#PmagPy"
    help_magic(helpme)


def help_FileMenu():
    helpme="#FileMenu"
    help_magic(helpme)

def help_ImportMenu():
    helpme="#ImportMenu"
    help_magic(helpme)

def help_AnalysisMenu():
    helpme="#AnalysisPlotsMenu"
    help_magic(helpme)

def help_PrepareMenu():
    helpme="#PrepareMagicConsole"
    help_magic(helpme)

def help_Utilities():
    helpme="#Utilities"
    help_magic(helpme)

def help_magic(helpme):
    import webbrowser
    webbrowser.open("http://earthref.org/MAGIC/cookbook"+helpme)


def exit():
    sys.exit()

def zeq():
    z_command='zeq_magic.py -WD '+'"'+opath+'"'
    try:
        open(opath+'/magic_measurements.txt','r')
        z_command=z_command+ ' -fsp zeq_specimens.txt'
    except IOError:
        tkMessageBox.showinfo("Info",'select Combine Measurements in Import file first. ')
        return
    try:
        open(opath+'/er_samples.txt','r')
        z_command=z_command+ ' -crd g -fsa er_samples.txt'
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
def thellier_gui():
    os.system('thellier_gui.py')

def thellier():
    t_command="thellier_magic.py -fsp "+opath+'/thellier_specimens.txt' 
    try:
        open(opath+'/magic_measurements.txt','r')
        t_command=t_command+' -f '+opath+'/magic_measurements.txt'
    except IOError:
        tkMessageBox.showinfo("Info",'Select Combine Measurements in Import file first.')
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
        tkMessageBox.showinfo("Info",'Select Combine Measurements in Import file first.')
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
        tkMessageBox.showinfo("Info",'select Combine measurements first. ')
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
        tkMessageBox.showinfo("Info","Combine measurements first")
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
            specfile=opath+"/pmag_specimens.txt"
            open(specfile,'r')
            file="pmag_specimens.txt"
            # re-order 
            #tkMessageBox.showinfo("Info","Assemble specimens first")
            #return
        except:
            pass
    clist=clist+' -fsp '+file
    try:
        open(opath+"/er_sites.txt",'r')
    except IOError:
        tkMessageBox.showinfo("Info","Make an er_sites.txt file, e.g. with orient.txt file")
        return
    OPT_types=["-D: Use default selection criteria","-C: Use no selection criteria", "-exc: Use customized selection criteria","-aD: Average multiple specimen lines per sample, default is by site","-aI: Average multiple specimen intensities per sample, default is by site","-sam: Calculate sample level VGPs/V[A]DMs, default is by site","-xSi: skip site level intensity data","-p: look at data by site","-lat: Use present latitude for VADM calculation","-fla model_lat.txt: use site paleolatitude data in model_lat.txt file","-xD: skip directions", "-xI: skip intensities","-pol: calculate averages by polarity"]
    opt_checks=ask_check(root,OPT_types,'select desired options:') #
    OPT_list=map((lambda var:var.get()),opt_checks) # returns method code  radio button list
    for opt in range(len(OPT_list)):
        if OPT_list[opt]==1:clist=clist+' '+OPT_types[opt].split(":")[0]+' '
    if OPT_list[9]==1:
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
       tkMessageBox.showinfo("Info","You have no files available for processing \n Interpret measurements and assemble specimens first.")
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
    global PlotOptions,COORDs
    COORDs=[] # restore to initial
    try: # make the NRM file for plotting
        data,file_type=pmag.magic_read(opath+"/magic_measurements.txt")
        NRMs=[]
        nrmfile=opath+'/nrm_measurements.txt'
        nrmspec=opath+'/nrm_specimens.txt'
        sampfile=opath+'/er_samples.txt'
        NRMs=pmag.get_dictitem(data,'magic_method_codes','LT-NO','has')
        pmag.magic_write(nrmfile,NRMs,'magic_measurements')
        print "NRM measurements saved in ",nrmfile
    except:
        print "select assemble measurements first"
        return  
    mk_command = 'nrm_specimens_magic.py -A -f '+nrmfile+'  -F '+opath+'/nrm_specimens_s.txt '  +' -fsa '+sampfile  # don't average replicates
    print mk_command
    os.system(mk_command) # make the nrm file
    mk_command = 'nrm_specimens_magic.py -A -crd g -f '+nrmfile+'  -F '+opath+'/nrm_specimens_g.txt '  +' -fsa '+sampfile  # don't average replicates
    print mk_command
    os.system(mk_command) # make the nrm file
    mk_command = 'nrm_specimens_magic.py -A -crd t -f '+nrmfile+'  -F '+opath+'/nrm_specimens_t.txt '  +' -fsa '+sampfile  # don't average replicates
    print mk_command
    os.system(mk_command) # make the nrm file
    outstring='combine_magic.py -WD '+opath+' -F nrm_specimens.txt -f nrm_specimens_s.txt nrm_specimens_g.txt nrm_specimens_t.txt'
    print outstring
    os.system(outstring) # make the nrm file
    NRMspecs,filetype=pmag.magic_read(nrmspec)
    NRMs=pmag.get_dictitem(NRMspecs,'specimen_tilt_correction','-1','T') # are there specimen coordinates?
    NRMg=pmag.get_dictitem(NRMspecs,'specimen_tilt_correction','0','T') # are there geographic data?
    NRMt=pmag.get_dictitem(NRMspecs,'specimen_tilt_correction','100','T') # are there tilt corrected data?
    if len(NRMs)>0:
        COORDs.append('Specimen')
    if len(NRMg)>0:
        COORDs.append('Geographic')
    if len(NRMt)>0:
        COORDs.append('Tilt corrected')
    if len(NRMspecs)>0 and len(COORDs)==0:COORDs=['Specimen']
    ask_plt(root) # get the desired plotting options
    plt_check_values=PlotOptions.pop() # get and delete the plot options
    eq_command = 'eqarea_magic.py -WD '+opath+' -f nrm_specimens.txt'
    PLTlist= map((lambda var:var.get()),plt_check_values) # get a list of the plot option check boxes
    if PLTlist[1]==1:
        eq_command =eq_command+' -obj sit ' # plot by site
    elif PLTlist[2]==1:
        eq_command =eq_command+' -obj sam ' # plot by sample
    elif PLTlist[3]==1:
        eq_command =eq_command+' -obj spc ' # plot by specimen
    if 'Specimen' in  COORDs:  # radio button options
        eq_command=eq_command + ' -crd s ' # plot geographic coordinates
    elif 'Geographic' in  COORDs: 
        eq_command=eq_command + ' -crd g ' # plot geographic coordinates
    elif 'Tilt corrected' in  COORDs: 
        eq_command=eq_command + ' -crd t ' # plot geographic coordinates
    print eq_command
    os.system(eq_command)
    COORDs=[] # restore to initial

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
        if cust_rv!=3:custom()
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
        if cust_rv!=3 and cust_rv!=1:custom()
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
    global PlotOptions
    if 'Normalize to unit intensity' not in PlotOptions:
        PlotOptions.append('Normalize to unit intensity')
    ask_plt(root)
    plt_check_values=PlotOptions.pop() # get and delete the plot options
    PLTlist= map((lambda var:var.get()),plt_check_values) # get a list of the plot option check boxes
    outstring='irmaq_magic.py -WD '+'"'+opath+'"'
    if PLTlist[1]==1:
        outstring =outstring+' -obj sit ' # plot by site
    elif PLTlist[2]==1:
        outstring =outstring+' -obj sam ' # plot by sample
    elif PLTlist[3]==1:
        outstring =outstring+' -obj spc ' # plot by specimen
    if PLTlist[4]==0:
        outstring =outstring+' -N ' # do not normalize
    print outstring
    os.system(outstring)

def lowrie_magic():
    outstring='lowrie_magic.py -WD '+'"'+opath+'"'
    plt_types=["Use measurement units","Normalize to unity"]
    plt_rv=ask_radio(root,plt_types,'Choose desired option:') # 
    if plt_rv==0:outstring=outstring+' -N '
    print outstring
    os.system(outstring)

def chart():
    outstring='chartmaker.py'
    print outstring
    os.system(outstring)

def ani_depthplot():
    global ANI
    try:
        open(opath+"/rmag_anisotropy.txt",'r')
        open(opath+"/magic_measurements.txt",'r')
    except IOError:
        tkMessageBox.showinfo("Info",'select Combine measurements first.   ')
        return
    outstring='ani_depthplot.py -WD '+'"'+opath+'"' +' -fb magic_measurements.txt '
    ask_ani(root)
    dmin,dmax=-1,-1
    if ANI['dmin']!='':dmin=ANI['dmin']
    if ANI['dmax']!='':
        dmax=ANI['dmax']
        outstring=outstring+' -d '+dmin+' '+dmax
    if ANI['mcd']==1:
        outstring=outstring+' -ds mcd '
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
    
def core_depthplot():
    global STRAT
    try:
        open(opath+'/magic_measurements.txt') # check if pmag_results file exists
        outstring="core_depthplot.py -WD "+opath # get list of available plots
    except IOError:
        tkMessageBox.showinfo("Info",'Must assemble measurements first')
        return
    try:
        open(opath+"/er_samples.txt")
        outstring=outstring + ' -fsa er_samples.txt'
    except IOError:
        pass       
    ask_strat(root)
    syms={'sym':STRAT['long_color']+STRAT['long_sym'],'size':STRAT['long_size'],'dsym':STRAT['disc_color']+STRAT['disc_sym'],'dsize':STRAT['disc_size']}
    if STRAT['af']!='':outstring=outstring+ ' -LP AF '+STRAT['af']
    if STRAT['therm']!='':outstring=outstring+ ' -LP T '+STRAT['therm']
    if STRAT['arm']!='':outstring=outstring+ ' -LP ARM '+STRAT['arm']
    if STRAT['irm']!='':outstring=outstring+ ' -LP IRM '+STRAT['irm']
    dmin,dmax=0,0
    if STRAT['dmin']!='':dmin=STRAT['dmin']
    if STRAT['dmax']!='':
        dmax=STRAT['dmax']
        outstring=outstring+' -d '+dmin+' '+dmax
    ts=''
    if STRAT['ts']!='' and STRAT['amax']!='' and STRAT['amin']!='':
        outstring=outstring+' -ts '+STRAT['ts']+' '+STRAT['amin']+' '+STRAT['amax']
    outstring=outstring+' -sym '+'"'+syms['sym']+'"'+' '+syms['size']
    PLT_list=STRAT['strat_check_list']
    if PLT_list[0]==0:outstring=outstring+' -D '
    if PLT_list[1]==0:outstring=outstring+' -I '
    if PLT_list[2]==0:outstring=outstring+' -M '
    if PLT_list[3]==1:outstring=outstring+' -log '
    if PLT_list[4]==1: outstring=outstring+' -n er_specimens.txt'
    if PLT_list[5]==1:
        try:
            open(opath+"/pmag_specimens.txt",'r')
            outstring=outstring + ' -fsp pmag_specimens.txt ' + syms['dsym']+ ' ' +syms['dsize'] 
        except IOError:
            print 'cant plot  PCAs  - none found'
    if PLT_list[6]==1:outstring=outstring+' -fres pmag_results.txt ro 5 '
    if PLT_list[7]==1:
        try:
            logfile=open(opath+"/ODPsummary.log",'r')
            files=logfile.readlines()
            print files
            for file in files[-1:]: # find most recently added core summary file
                if 'coresummary' in file:
                    outstring=outstring + ' -fsum '+file.replace('\n','')
                    break
        except IOError:
            pass
    if PLT_list[8]==1:outstring=outstring+' -ds mcd ' # use composite depth
    if PLT_list[9]==0:outstring=outstring+' -L ' # don't connect the dots
    if PLT_list[10]==0:
        outstring=outstring+' -S '
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
    if exfmt_rv: outstring = outstring+' -tex' 
    exfmt=['Export specimen intensities?','Skip specimen level intensities'] 
    exfmt_rv=ask_radio(root,exfmt,'Export Specimens?') #
    if exfmt_rv==0: outstring = outstring+' -fsp pmag_specimens.txt -g' 
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
    orientmenu.add_command(label="Import model latitude data file",command=model_lat)
    orientmenu.add_command(label="Import er_ages.txt file",command=add_ages)
    magmenu=Menu(importmenu)
    importmenu.add_cascade(label="Magnetometer files",menu=magmenu)
    magmenu.add_command(label="SIO format",command=add_sio)
    filemenu.add_separator()
    magmenu.add_command(label="CIT format",command=add_cit)
   # magmenu.add_command(label="2G-ascii format",command=add_2G_asc)
    magmenu.add_command(label="2G-binary format",command=add_2G_bin)
    magmenu.add_command(label="HUJI format",command=add_huji)
   # magmenu.add_command(label="JR6 format",command=add_jr6)
    magmenu.add_command(label="LDEO format",command=add_ldeo)
    magmenu.add_command(label="IODP SRM (csv) format",command=add_srm_csv)
    magmenu.add_command(label="PMD (ascii) format",command=add_pmd_ascii)
   # magmenu.add_command(label="PMD (IPG-PaleoMac) format",command=add_ipg)
#    magmenu.add_command(label="UU format",command=add_uu)
#    magmenu.add_command(label="UB format",command=add_ub)
#    UCSCmenu=Menu(magmenu)
#    magmenu.add_cascade(label="UCSC formats",menu=UCSCmenu)
   # UCSCmenu.add_command(label="UCSC New format",command=add_ucsc)
   # UCSCmenu.add_command(label="UCSC legacy format",command=add_leg_ucsc)
#    magmenu.add_command(label="LIV-MW format",command=add_liv)
#    magmenu.add_command(label="UMICH (Gee) format",command=add_umich)
    magmenu.add_command(label="TDT format",command=add_tdt)
    amsmenu=Menu(importmenu)
    importmenu.add_cascade(label="Anisotropy files",menu=amsmenu)
#    s_menu=Menu(amsmenu)
#    amsmenu.add_cascade(label=".s format",menu=s_menu)
#    s_menu.add_command(label="import single .s file", command=add_s)
#    s_menu.add_command(label="import entire directory", command=add_s_dir)
    amsmenu.add_command(label="kly4s format",command=add_kly4s)
    amsmenu.add_command(label="k15 format",command=add_k15)
    amsmenu.add_command(label="Sufar 4.0 ascii format",command=add_sufar4)
    agmmenu=Menu(importmenu)
    importmenu.add_cascade(label="Hysteresis files",menu=agmmenu)
    agmmenu.add_command(label="Import single agm file",command=add_agm_file)
    agmmenu.add_command(label="Import entire directory",command=add_agm_dir)
#    importmenu.add_command(label="Curie Temperatures",command=add_curie)
    importmenu.add_separator()
    importmenu.add_command(label="Combine measurements",command=meas_combine)
    importmenu.add_separator()
    importmenu.add_command(label="Convert er_samples => orient.txt",command=convert_samps)
    importmenu.add_command(label="Update measurements\n if new orientation imported",command=update_meas)
    importmenu.add_separator()
    prior=Menu(importmenu)
    importmenu.add_cascade(label="Import prior interpretations",menu=prior)
    prior.add_command(label="PmagPy redo file",command=add_redo)
#    prior.add_command(label="DIR (Enkin) file",command=add_DIR_ascii)
#    prior.add_command(label="LSQ (Jones/PaleoMag) file",command=add_LSQ)
#    prior.add_command(label="PMM (USCS) file",command=add_PMM)
    menubar.add_cascade(label="Import",menu=importmenu)
    plotmenu=Menu(menubar)
    plotmenu.add_command(label="Customize Criteria ",command=custom)
    plotmenu.add_separator()
    plotmenu.add_command(label="Demagnetization data ",command=zeq)
#    plotmenu.add_command(label="Demagnetization GUI",command=zeq_gui)
    plotmenu.add_command(label="Thellier-type experiments",command=thellier)
#    plotmenu.add_command(label="Thellier GUI",command=thellier_gui)
#    plotmenu.add_command(label="Microwave experiments",command=microwave)
    eqareamenu=Menu(plotmenu)
    eqareamenu.add_command(label="Quick look - NRM directions",command=quick_look)
    eqareamenu.add_command(label="General remanence directions",command=eqarea)
    eqareamenu.add_command(label="Anisotropy data",command=aniso)
    plotmenu.add_cascade(label="Equal area plots",menu=eqareamenu)
    plotmenu.add_command(label="Hysteresis data",command=hysteresis)
#    plotmenu.add_command(label="Curie Temperatures data",command=curie)
    plotmenu.add_command(label="Hysteresis ratio plots",command=dayplot)
    plotmenu.add_command(label="IRM acquisition",command=irm_magic)
    plotmenu.add_command(label="3D-IRM experiment",command=lowrie_magic)
    plotmenu.add_command(label="Remanence data versus depth/height",command=core_depthplot)
    plotmenu.add_command(label="Anisotropy data versus depth/height",command=ani_depthplot)
    plotmenu.add_command(label="Reversals test",command=revtest)
    plotmenu.add_command(label="Fold test ",command=fold)
    plotmenu.add_command(label="Elong/Inc",command=EI,state="disabled")
    menubar.add_cascade(label="Analysis and Plots",menu=plotmenu)
    uploadmenu=Menu(menubar)
    uploadmenu.add_command(label="Assemble specimens",command=spec_combine)
    uploadmenu.add_command(label="Assemble results",command=sitemeans)
    uploadmenu.add_command(label="Prepare Upload txt File",command=upload)
    menubar.add_cascade(label="Prepare for MagIC Console",menu=uploadmenu)
    utilitymenu=Menu(menubar)
    utilitymenu.add_command(label="Check sample orientations",command=site_edit)
    utilitymenu.add_command(label="Extract Results to Table",command=extract)
    utilitymenu.add_command(label="Map of VGPs",command=vgp_map)
    utilitymenu.add_command(label="Map of site locations",command=map_sites)
    utilitymenu.add_command(label="Make IZZI exp.  chart",command=chart)
    utilitymenu.add_command(label="Expected directions/Paleolatitudes",command=apwp)
    utilitymenu.add_separator()
    menubar.add_cascade(label="Utilities",menu=utilitymenu)
    helpmenu=Menu(menubar)
    menubar.add_cascade(label="Help",menu=helpmenu)
    helpmenu.add_command(label="PmagPy Help",command=help_PmagPy)
    helpmenu.add_command(label="File Menu",command=help_FileMenu)
    helpmenu.add_command(label="Import Menu",command=help_ImportMenu)
    helpmenu.add_command(label="Analysis and Plots Menu",command=help_AnalysisMenu)
    helpmenu.add_command(label="Prepare for MagIC Console Menu",command=help_PrepareMenu)
    helpmenu.add_command(label="Utilities Menu",command=help_Utilities)
    root.config(menu=menubar)



###
###
global Result,OrResult,user,ApwpResult,NCN_types,OCN_types,MCD_types
user=""
helpme=""
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
#### common lists, dictionaries
OrResult={'out':'er_samples.txt','gmt':'0','dec':'','Z':'','dcn':'1','dec':'','Z':'','ocn':'1','ncn':'1','a':0,'app':'n'}
#
SMopts={'usr':user,'min':"",'max':"",'units':"","crd":"s",'frac':"",'type':""}
#
ApwpResult={}
#
NCN_types=["1: XXXXY: where XXXX is site designation, Y is sample", "2: XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)", "3: XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)","4: XXXX[YYY] where YYY is sample designation, enter number of Y:", "5: sample name=site name","6: Site names in orient.txt file","7: [XXXX]YYY where XXXX is the site name, enter number of X:","8: this is a synthetic and has no site name"] 
#
OCN_types=["1: Lab arrow azimuth = mag_azimuth; Lab arrow dip=-field_dip (field_dip is hade)", "2: Lab arrow azimuth = mag_azimuth-90 (mag_azimuth is strike); Lab arrow dip = -field_dip","3: Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip (field_dip is inclination of lab arrow)","4: Lab arrow azimuth and dip are same as mag_azimuth, field_dip","5: Lab arrow azimuth and dip are mag_azimuth, field_dip-90 (field arrow is inclination of specimen Z direction)","6: Lab arrow azimuth = mag_azimuth-90 (mag_azimuth is strike); Lab arrow dip = 90-field_dip"]
#
MCD_types=["FS-FD: field sampling done with a drill","FS-H: field sampling done with hand samples","FS-LOC-GPS: field location done with GPS","FS-LOC-MAP:  field location done with map","SO-POM:  a Pomeroy orientation device was used","SO-ASC:  an ASC orientation device was used","SO-MAG: magnetic compass used for all orientations","SO-SUN: sun compass used for all orientations","SO-SM: either magnetic or sun used on all orientations","SO-SIGHT: orientation from sighting"]
#
DCN_types=["1: Use the IGRF DEC value at the lat/long and date supplied","2: Use this DEC: ","3: DEC=0, mag_az is already corrected in file","4: value to ADD to local time for GMT"]
#
LP_types=["NRM: no lab treatment", "AF: alternating field de(re)magnetization","T: Thermal de(re)magnetization including Thellier, excluding TRM acquis.","TRM: TRM acquisition experiment","ANI: anisotropy of TRM,IRM or ARM","I: IRM","I3d: Lowrie 3D-IRM"]
#
MAG={'usr':'','out':'','dc':'0','ac':'0','phi':'0','theta':'-90','spc':'1','coil':'','LP':1,'MCD':0,'ins':''}
#
AGM={'usr':'','loc':'unknown','spc':'1','spn':0,'syn':0,'SI':0,'bak':0,'ins':''}
#
PlotOptions=['Plot by location','Plot by site','Plot by sample','Plot by specimen']
#
SYM_descr=['circle', 'triangle_down','triangle_up','triangle_right','triangle_left', 'square', 'pentagon','star','hexagon','plus','x','diamond','pipe','dash']
SYM_markers=['o', 'v','^','>','<', 's', 'p','*','h','+','x','D','|','-']
SYM_col_descr=['blue', 'green','red','cyan','magenta', 'yellow', 'black','white']
SYM_colors=['b', 'g','r','c','m', 'y', 'k','w']
SYM_size=['3', '5','7','10']
STRAT={'long_sym':'o','long_color':'b','long_size':'5','disc_sym':'^','disc_color':'r','disc_size':'10','dmin':'','dmax':'','af':'','therm':'','arm':'','irm':'','ts':'','amin':'','amax':''}
ANI={'dmin':'','dmax':'','mcd':'0'}
COORDs=[]
root.mainloop()
