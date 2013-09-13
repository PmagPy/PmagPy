#!/usr/bin/env python
# -*- coding: utf-8 -*-
import wx,string,sys,math,os
import scipy
from scipy import * 



def cart2dir(cart):
    """
    converts a direction to cartesian coordinates
    """
    cart=array(cart)
    rad=pi/180. # constant to convert degrees to radians
    if len(cart.shape)>1:
        Xs,Ys,Zs=cart[:,0],cart[:,1],cart[:,2]
    else: #single vector
        Xs,Ys,Zs=cart[0],cart[1],cart[2]
    Rs=sqrt(Xs**2+Ys**2+Zs**2) # calculate resultant vector length
    Decs=(arctan2(Ys,Xs)/rad)%360. # calculate declination taking care of correct quadrants (arctan2) and making modulo 360.
    try:
        Incs=arcsin(Zs/Rs)/rad # calculate inclination (converting to degrees) # 
    except:
        print 'trouble in cart2dir' # most likely division by zero somewhere
        return zeros(3)
        
    return array([Decs,Incs,Rs]).transpose() # return the directions list



                    


class convert_livdb_files_to_MagIC(wx.Frame):
    """"""
    title = "Convert Livdb files to MagIC format"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.Panel(self)
        self.max_files=10
        self.WD=WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        #---sizer infor ----

        TEXT1="Instructions:\n"
        TEXT2="Put all livdb files of the same Location in one folder\n"
        TEXT3="If there is a more than one location use multiple folders\n"
        TEXT4="Each measurement file end with '.livdb'\n"

        TEXT=TEXT1+TEXT2+TEXT3+TEXT4
        bSizer_info = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.HORIZONTAL )
        bSizer_info.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)
            

        #---sizer 1 ----
        TEXT="File:\n Choose a working directory path\n No spaces are alowd in path"
        bSizer1 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        bSizer1.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        bSizer1.AddSpacer(5)
        for i in range(self.max_files):
            command= "self.dir_path_%i = wx.TextCtrl(self.panel, id=-1, size=(200,25), style=wx.TE_READONLY)"%i
            exec command
            command= "self.add_dir_button_%i =  wx.Button(self.panel, id=-1, label='add',name='add_%i')"%(i,i)
            exec command
            command= "self.Bind(wx.EVT_BUTTON, self.on_add_dir_button_i, self.add_dir_button_%i)"%i
            #print command
            exec command            
            command="bSizer1_%i = wx.BoxSizer(wx.HORIZONTAL)"%i
            exec command
            command="bSizer1_%i.Add(wx.StaticText(pnl,label=('%i  '[:2])),wx.ALIGN_LEFT)"%(i,i+1)
            exec command
            
            command="bSizer1_%i.Add(self.dir_path_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer1_%i.Add(self.add_dir_button_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer1.Add(bSizer1_%i,wx.ALIGN_TOP)" %i
            exec command
            bSizer1.AddSpacer(5)
                  

        #---sizer 2 ----

        TEXT="\nLocation\nname:\n"
        bSizer2 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        bSizer2.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        bSizer2.AddSpacer(5)
        for i in range(self.max_files):
            command= "self.file_location_%i = wx.TextCtrl(self.panel, id=-1, size=(60,25))"%i
            exec command
            command="bSizer2.Add(self.file_location_%i,wx.ALIGN_TOP)" %i
            exec command
            bSizer2.AddSpacer(5)

##        #---sizer 3 ----
##
##        missing

        #---sizer 4 ----

        TEXT="\nSample-specimen\nnaming convention:"
        bSizer4 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        bSizer4.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        self.sample_naming_conventions=['sample=specimen','no. of terminate characters','charceter delimited']
        bSizer4.AddSpacer(5)
        for i in range(self.max_files):
            command="self.sample_naming_convention_%i = wx.ComboBox(self.panel, -1, self.sample_naming_conventions[0], size=(180,25), choices=self.sample_naming_conventions, style=wx.CB_DROPDOWN)"%i
            exec command            
            command="self.sample_naming_convention_char_%i = wx.TextCtrl(self.panel, id=-1, size=(40,25))"%i
            exec command
            command="bSizer4_%i = wx.BoxSizer(wx.HORIZONTAL)"%i
            exec command
            command="bSizer4_%i.Add(self.sample_naming_convention_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer4_%i.Add(self.sample_naming_convention_char_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer4.Add(bSizer4_%i,wx.ALIGN_TOP)"%i        
            exec command

            bSizer4.AddSpacer(5)

        #---sizer 5 ----

        TEXT="\nSite-sample\nnaming convention:"
        bSizer5 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        bSizer5.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        self.site_naming_conventions=['site=sample','no. of terminate characters','charceter delimited']
        bSizer5.AddSpacer(5)
        for i in range(self.max_files):
            command="self.site_naming_convention_char_%i = wx.TextCtrl(self.panel, id=-1, size=(40,25))"%i
            exec command
            command="self.site_naming_convention_%i = wx.ComboBox(self.panel, -1, self.site_naming_conventions[0], size=(180,25), choices=self.site_naming_conventions, style=wx.CB_DROPDOWN)"%i
            exec command
            command="bSizer5_%i = wx.BoxSizer(wx.HORIZONTAL)"%i
            exec command
            command="bSizer5_%i.Add(self.site_naming_convention_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer5_%i.Add(self.site_naming_convention_char_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer5.Add(bSizer5_%i,wx.ALIGN_TOP)"%i        
            exec command
            bSizer5.AddSpacer(5)

        #------------------

        self.okButton = wx.Button(self.panel, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)        
        #hbox1.Add(self.add_file_button)
        #hbox1.Add(self.remove_file_button )

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)        
        hbox2.Add(self.okButton)
        hbox2.Add(self.cancelButton )

        #------

        vbox=wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddSpacer(5)
        hbox.Add(bSizer1, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)
        hbox.Add(bSizer2, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)
##        hbox.Add(bSizer3, flag=wx.ALIGN_LEFT)        
##        hbox.AddSpacer(5)
        hbox.Add(bSizer4, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)
        hbox.Add(bSizer5, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)

        #-----
        
        vbox.AddSpacer(20)
        vbox.Add(bSizer_info,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)        
        vbox.Add(hbox)
        vbox.AddSpacer(20)
        vbox.Add(hbox1,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
        vbox.Add(hbox2,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
        
        self.panel.SetSizer(vbox)
        vbox.Fit(self)
        self.Show()
        self.Centre()


    def cart2dir(cart):
        """
        converts a direction to cartesian coordinates
        """
        cart=array(cart)
        rad=pi/180. # constant to convert degrees to radians
        if len(cart.shape)>1:
            Xs,Ys,Zs=cart[:,0],cart[:,1],cart[:,2]
        else: #single vector
            Xs,Ys,Zs=cart[0],cart[1],cart[2]
        Rs=sqrt(Xs**2+Ys**2+Zs**2) # calculate resultant vector length
        Decs=(arctan2(Ys,Xs)/rad)%360. # calculate declination taking care of correct quadrants (arctan2) and making modulo 360.
        try:
            Incs=arcsin(Zs/Rs)/rad # calculate inclination (converting to degrees) # 
        except:
            print 'trouble in cart2dir' # most likely division by zero somewhere
            return zeros(3)
            
        return array([Decs,Incs,Rs]).transpose() # return the directions list



##    def on_add_file_button(self,event):
##
##        dlg = wx.FileDialog(
##            None,message="choose file to convert to MagIC",
##            defaultDir=self.WD, 
##            defaultFile="",
##            style=wx.OPEN | wx.CHANGE_DIR
##            )        
##        if dlg.ShowModal() == wx.ID_OK:
##            FILE = dlg.GetPath()
##        # fin=open(FILE,'rU')
##        self.file_path.AppendText(FILE+"\n")
##        self.protocol_info.AppendText("IZZI"+"\n")


    def on_add_dir_button_i(self,event):

        dlg = wx.DirDialog(
            None,message="choose directtory with livdb files",
            defaultPath ="./", 
            style=wx.OPEN | wx.CHANGE_DIR
            )        
        if dlg.ShowModal() == wx.ID_OK:
            FILE = dlg.GetPath()
        # fin=open(FILE,'rU')
        button = event.GetEventObject()
        name=button.GetName()
        i=int((name).split("_")[-1])
        #print "The button's name is " + button.GetName()
        
        command="self.dir_path_%i.SetValue(FILE)"%i
        exec command



    def read_generic_file(self,path):
        Data={}
        Fin=open(path,'rU')
        header=Fin.readline().strip('\n').split('\t')
        
        for line in Fin.readlines():
            tmp_data={}
            l=line.strip('\n').split('\t')
            if len(l)<len(header):
                continue
            else:
                for i in range(len(header)):
                    tmp_data[header[i]]=l[i]
                specimen=tmp_data['Specimen']
                if specimen not in Data.keys():
                    Data[specimen]=[]
                # check dupliactes
                if len(Data[specimen]) >0:
                    if tmp_data['Treatment']==Data[specimen][-1]['Treatment']:
                        print "-W- WARNING: duplicate measurements specimen %s, Treatment %s. keeping onlt the last one"%(tmp_data['Specimen'],tmp_data['Treatment'])
                        Data[specimen].pop()
                        
                Data[specimen].append(tmp_data)
        return(Data)               

    def on_okButton(self,event):


        print "yyyy"
        DIRS_data={}
        
##        #-----------------------------------
##        # Prepare MagIC measurement file
##        #-----------------------------------
##
##        # prepare output file
##        magic_headers=['er_citation_names','er_specimen_name',"er_sample_name","er_site_name",'er_location_name','er_analyst_mail_names',\
##                       "magic_instrument_codes","measurement_flag","measurement_standard","magic_experiment_name","magic_method_codes","measurement_number",'treatment_temp',"measurement_dec","measurement_inc",\
##                       "measurement_magn_moment","measurement_temp","treatment_dc_field","treatment_dc_field_phi","treatment_dc_field_theta"]             
##
##        fout=open("magic_measurements.txt",'w')        
##        fout.write("tab\tmagic_measurements\n")
##        header_string=""
##        for i in range(len(magic_headers)):
##            header_string=header_string+magic_headers[i]+"\t"
##        fout.write(header_string[:-1]+"\n")
##
##        #-----------------------------------
##            
##        Data={}
##        header_codes=[]
##        ERROR=""
##        datafiles=[]

        for i in range(self.max_files):

            # read directiory path 
            dirpath=""
            command="dirpath=self.dir_path_%i.GetValue()"%i
            exec command
            if dirpath!="":
                dir_name=str(dirpath.split("/")[-1])
                DIRS_data[dir_name]={}
                DIRS_data[dir_name]['path']=str(dirpath)
            else:
                continue

                            
            # get location
            user_name=""
            command="location_name=self.file_location_%i.GetValue()"%i
            exec command
            DIRS_data[dir_name]['location_name']=str(location_name)
            
            # get sample-specimen naming convention

            sample_naming_convenstion=["",""]
            command="sample_naming_convenstion[0]=str(self.sample_naming_convention_%i.GetValue())"%i
            exec command
            command="sample_naming_convenstion[1]=str(self.sample_naming_convention_char_%i.GetValue())"%i
            exec command
            DIRS_data[dir_name]["sample_naming_convenstion"]=sample_naming_convenstion
            
            
            # get site-sample naming convention

            site_naming_convenstion=["",""]
            command="site_naming_convenstion[0]=str(self.site_naming_convention_%i.GetValue())"%i
            exec command
            command="site_naming_convenstion[1]=str(self.site_naming_convention_char_%i.GetValue())"%i
            exec command
            DIRS_data[dir_name]["site_naming_convenstion"]=site_naming_convenstion

            print "DIRS_data",DIRS_data
            self.convert_2_magic(DIRS_data)

##            #-------------------------------
##            Magic_lab_protocols={}
##            Magic_lab_protocols['IZZI'] = "LP-PI-TRM:LP-PI-BT-IZZI"
##            Magic_lab_protocols['IZ'] = "LP-PI-TRM:LP-PI-TRM-IZ"
##            Magic_lab_protocols['ZI'] = "LP-PI-TRM:LP-PI-TRM-ZI"
##            Magic_lab_protocols['ATRM 6 positions'] = "LP-AN-TRM" # LT-T-I:
##            Magic_lab_protocols['cooling rate'] = "LP-CR-TRM" # LT-T-I:
##            Magic_lab_protocols['NLT'] = "LP-TRM" # LT-T-I:
##            #------------------------------
##
##            for specimen in this_file_data.keys():
##                measurement_running_number=0
##                this_specimen_teratments=[]
##                for meas_line in this_file_data[specimen]:
##                    MagRec={}
##                    #
##                    MagRec["er_specimen_name"]=meas_line['Specimen']
##                    MagRec['er_citation_names']="This study"
##                    MagRec["er_sample_name"]=self.get_sample_name(MagRec["er_specimen_name"],sample_naming_convenstion)
##                    MagRec["er_site_name"]=self.get_site_name(MagRec["er_sample_name"],site_naming_convenstion)
##                    MagRec['er_location_name']=""
##                    MagRec['er_analyst_mail_names']=user_name 
##                    MagRec["magic_instrument_codes"]="" 
##                    MagRec["measurement_flag"]='g'
##                    MagRec["measurement_number"]="%i"%measurement_running_number
##                    MagRec['treatment_temp']="%.2f"%(float(meas_line['Treatment'].split(".")[0])+273.)
##                    MagRec["measurement_dec"]=meas_line["Declination"]
##                    MagRec["measurement_inc"]=meas_line["Inclination"]
##                    MagRec["measurement_magn_moment"]='%10.3e'%(float(meas_line["Moment"])*1e-3) # in Am^2
##                    MagRec["measurement_temp"]='273.' # room temp in kelvin
##                    MagRec["treatment_dc_field"]='%8.3e'%(float(labfield[0])*1e-6)
##                    MagRec["treatment_dc_field_phi"]="%.2f"%(float(labfield[1]))
##                    MagRec["treatment_dc_field_theta"]="%.2f"%(float(labfield[2]))
##                    MagRec["measurement_standard"]="u"
##                    MagRec["magic_experiment_name"]=MagRec["er_specimen_name"]+":"+Magic_lab_protocols[experiment]
##
##                    this_specimen_teratments.append(float(meas_line['Treatment']))                    
##                    # fill in LP and LT
##                    lab_protocols_string=Magic_lab_protocols[experiment]
##                    tr_temp=float(meas_line['Treatment'].split(".")[0])
##                    if len(meas_line['Treatment'].split("."))==1:
##                        tr_tr=0
##                    else:
##                        tr_tr=float(meas_line['Treatment'].split(".")[1])
##                    
##                    # identify the step in the experiment from Experiment_Type,
##                    # IZ/ZI/IZZI
##                    if experiment in ['IZZI','IZ','ZI']:
##                        if float(tr_temp)==0:
##                            lab_treatment="LT-NO" # NRM
##                        elif float(tr_tr)==0:                            
##                            lab_treatment="LT-T-Z"
##                            if tr_temp+0.1 in this_specimen_teratments[:-1]:
##                                lab_protocols_string="LP-PI-TRM-IZ:"+lab_protocols_string
##                            else:
##                                lab_protocols_string="LP-PI-TRM-ZI:"+lab_protocols_string
##                                                
##                        elif float(tr_tr)==10 or float(tr_tr)==1:                            
##                            lab_treatment="LT-T-I"
##                            if tr_temp+0.0 in this_specimen_teratments[:-1]:
##                                lab_protocols_string="LP-PI-TRM-ZI:"+lab_protocols_string
##                            else:
##                                lab_protocols_string="LP-PI-TRM-IZ:"+lab_protocols_string
##
##                        elif float(tr_tr)==20 or float(tr_tr)==2:                            
##                            lab_treatment="LT-PTRM-I"            
##                        else:                            
##                            print "-E- unknown measurement code specimen %s treatmemt %s"%(meas_line['Specimen'],meas_line['Treatment'])
##                        
##                    elif experiment in ['ATRM 6 positions']:
##                        lab_protocols_string="LP-AN-TRM"
##                        if float(tr_tr)==0:
##                            lab_treatment="LT-T-Z"
##                            MagRec["treatment_dc_field_phi"]='0'
##                            MagRec["treatment_dc_field_theta"]='0'
##                        else:
##                                    
##                            # find the direction of the lab field in two ways:
##                            # (1) using the treatment coding (XX.1=+x, XX.2=+y, XX.3=+z, XX.4=-x, XX.5=-y, XX.6=-z)
##                            tdec=[0,90,0,180,270,0,0,90,0]
##                            tinc=[0,0,90,0,0,-90,0,0,90]
##                            if tr_tr < 10:
##                                ipos_code=int(tr_tr)-1
##                            else:
##                                ipos_code=int(tr_tr/10)-1
##                            # (2) using the magnetization
##                            DEC=float(meas_line["Declination"])
##                            INC=float(meas_line["Inclination"])
##                            if INC < 45 and INC > -45:
##                                if DEC>315  or DEC<45: ipos_guess=0
##                                if DEC>45 and DEC<135: ipos_guess=1
##                                if DEC>135 and DEC<225: ipos_guess=3
##                                if DEC>225 and DEC<315: ipos_guess=4
##                            else:
##                                if INC >45: ipos_guess=2
##                                if INC <-45: ipos_guess=5
##                            # prefer the guess over the code
##                            ipos=ipos_guess
##                            # check it 
##                            if tr_tr!= 7 and tr_tr!= 70:
##                                if ipos_guess!=ipos_code:
##                                    print "-W- WARNING: check specimen %s step %s, ATRM measurements, coding does not match the direction of the lab field"%(specimen,meas_line['Treatment'])
##                            MagRec["treatment_dc_field_phi"]='%7.1f' %(tdec[ipos])
##                            MagRec["treatment_dc_field_theta"]='%7.1f'% (tinc[ipos])
##                                
##                            if float(tr_tr)==70 or float(tr_tr)==7: # alteration check as final measurement
##                                    lab_treatment="LT-PTRM-I"
##                            else:
##                                    lab_treatment="LT-T-I"
##                                
##                    elif experiment in ['cooling rate']:
##                        print "Dont support yet cooling rate experiment file. Contact rshaar@ucsd.edu"
##                    elif experiment in ['NLT']:
##                        if float(tr_tr)==0:
##                            lab_protocols_string="LP-TRM"
##                            lab_treatment="LT-T-Z"
##                        else:
##                            lab_protocols_string="LP-TRM"
##                            lab_treatment="LT-T-I"
##                            
##                    MagRec["magic_method_codes"]=lab_treatment+":"+lab_protocols_string
##                    line_string=""
##                    for i in range(len(magic_headers)):
##                        line_string=line_string+MagRec[magic_headers[i]]+"\t"
##                    fout.write(line_string[:-1]+"\n")
##
##        #--
##        MSG="files converted to MagIC format and merged into one file:\n magic_measurements.txt\n "            
##        dlg1 = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
##        dlg1.ShowModal()
##        dlg1.Destroy()
##
##        self.Destroy()


    def on_cancelButton(self,event):
        self.Destroy()

    def get_sample_name(self,specimen,sample_naming_convenstion):
        if sample_naming_convenstion[0]=="sample=specimen":
            sample=specimen
        elif sample_naming_convenstion[0]=="no. of terminate characters":
            n=int(sample_naming_convenstion[1])*-1
            sample=specimen[:n]
        elif sample_naming_convenstion[0]=="charceter delimited":
            d=sample_naming_convenstion[1]
            sample_splitted=specimen.split(d)
            if len(sample_splitted)==1:
                sample=sample_splitted[0]
            else:
                sample=d.join(sample_splitted[:-1])
        return sample
                            
    def get_site_name(self,sample,site_naming_convenstion):
        if site_naming_convenstion[0]=="site=sample":
            site=sample
        elif site_naming_convenstion[0]=="no. of terminate characters":
            n=int(site_naming_convenstion[1])*-1
            site=sample[:n]
        elif site_naming_convenstion[0]=="charceter delimited":
            d=site_naming_convenstion[1]
            site_splitted=sample.split(d)
            if len(site_splitted==1):
                site=site_splitted[0]
            else:
                site=d.join(site_splitted[:-1])
        
        return site




    ##application = wx.PySimpleApp()
    ##dia = convert_generic_files_to_MagIC("./")
    ##dia.Show()
    ##dia.Center()
    ##print "hey"

    ##    application = wx.PySimpleApp()
    ##
    ##    dlg = wx.FileDialog(
    ##        None,message="choose file to convert to MagIC",
    ##        defaultDir="./", 
    ##        defaultFile="",
    ##        style=wx.OPEN | wx.CHANGE_DIR
    ##        )        
    ##    if dlg.ShowModal() == wx.ID_OK:
    ##        FILE = dlg.GetPath()
    ##    fin=open(FILE,'rU')

    def convert_2_magic(self,DIRS_data):

        
        for dir_name in DIRS_data.keys():

            
            #--------------------------------------
            # Read the file
            # 
            # Database structure
            #
            # 1) Each file contains the data from one specimen
            # 2) First line is the header header. Header includes 19 fields with different delimiters listed below
            # 3) Body includes 22 fields with different delimiters listed below
            # 4) Body ends with end statment 
            #
            # HEADER:
            # Sample code (string): (delimiter = space+) 
            # Sample Dip (degrees): (delimiter = space)
            # Sample Dec (degrees): (delimiter = space)
            # Height (meters): (delimiter = space)
            # Position (no units): (delimiter = space)
            # Thickness (meters): (delimiter = space)
            # Unit Dip (aka tilt) (degrees): (delimiter = space)
            # Unit Dip Direction (aka Direction) (degrees): (delimiter = space)
            # Site Latitude (decimal degrees): (delimiter = space)
            # Site Longitude (decimal degrees): (delimiter = space)
            # Experiment Type (string): (delimiter = |) 
            # Name of measurer (string): (delimiter = |) 
            # Magnetometer name  (string): (delimiter = |) 
            # Demagnetiser name  (string): (delimiter = |) 
            # Specimen/Experiment Comment  (string): (delimiter = |) 
            # Database version (integer): (delimiter = |)
            # Conversion Version (string): (delimiter = |) 
            # Sample Volume (cc): (delimiter = |) 
            # Sample Density  (kg/m^3): (delimiter = |) 
            #
            #
            # BODY:
            # Treatment (aka field) (mT / deg C / 10-2 W): (delimiter = space)
            # Microwave Power (W) : (delimiter = space)
            # Microwave Time (s) : (delimiter = space)
            # X (nAm^2): (delimiter = space)
            # Y (nAm^2): (delimiter = space)
            # Z (nAm^2): (delimiter = space)
            # Mass g: (delimiter = space)
            # Applied field intensity (micro_T): (delimiter = space)
            # Applied field Dec (degrees): (delimiter = space)
            # Applied Field Inc (degrees): (delimiter = space)
            # Measurement Date (DD-MM-YYYY)  #### CHECK !! ## (delimiter = |)
            # Measurement Time (HH:SS:MM) (delimiter = |)
            # Measurement Remark (string) (delimiter = |)
            # Step Number (integer) (delimiter = |)
            # Step Type (string) (delimiter = |)
            # Tristan Gain (integer) (delimiter = |)
            # Microwave Power Integral (W.s) (delimiter = |)
            # JR6 Error(percent %) (delimiter = |)
            # FiT Smm (?) (delimiter = |)
            # Utrecht Error (percent %) (delimiter = |)
            # AF Demag/Remag Peak Field (mT) (delimiter = |)
            # TH Demag/Remag Peak Temperature (deg C) (delimiter = |)
            # -------------------------------------------------------------


            #-----------------------------------
            # Read file and sort data by specimen
            #-----------------------------------

            #print DIR_data
            #os.chdir(DIR_data["path"])
            #print DIRs_data[dir_name]["path"]
            magic_measurements_headers=[]
            MagRecs=[]

            for files in os.listdir(DIRS_data[dir_name]["path"]):
                if files.endswith(".livdb"):
                    print DIRS_data[dir_name]["path"]+"/"+files
                    fin=open(DIRS_data[dir_name]["path"]+"/"+files,'rU')
                    Data={}
                    header_codes=['Sample code','Sample Dip','Sample Dec','Height','Position','Thickness','Unit Dip','Unit Dip Direction','Site Latitude',\
                                  'Site Longitude','Experiment Type','Name of measurer','Magnetometer name','Demagnetiser name','Specimen/Experiment Comment',\
                                  'Database version','Conversion Version','Sample Volume','Sample Density']

                    meas_codes=['Treatment','Microwave Power','Microwave Time','moment_X','moment_Y','moment_Z','Mass','Applied field Intensity','Applied field Dec',\
                                'Applied field Inc','Measurement Date','Measurement Time','Measurement Remark','Step Number','Step Type','Tristan Gain','Microwave Power Integral',\
                                'JR6 Error','FiT Smm','Utrecht Error','AF Demag/Remag Peak Field','TH Demag/Remag Peak Temperature']

                    line_number=0
                    continue_reading=True
                    while continue_reading:
                        # first line is the header
                        this_specimen=True
                        while this_specimen==True:
                            line=fin.readline()
                            line_number+=1
                            if not line:
                                continue_reading=False
                                break
                            #header=line.strip('\n').replace('|', ' ').split()
                            this_line=line.strip('\n').split("|")
                            header=str(this_line[0]).split()+ this_line[1:-1]

                            # header consists of  fields seperated by spaces and "|"

                    ##            if len (header) > 15:
                    ##                this_line_data[14:]=" ".join(this_line_data[14:])
                    ##                del(this_line_data[15:])

                            # warning if missing info.
                            
                            if len(header) < 19:
                                print "missing data in header.Line %i" %line_number
                                print header

                            # read header and sort in a dictionary
                            tmp_header_data={}
                            
                            for i in range(len(header)):
                                tmp_header_data[header_codes[i]]=header[i]
                            specimen=tmp_header_data['Sample code']
                            Experiment_Type=tmp_header_data['Experiment Type']
                            
                            if specimen not in Data.keys():
                                Data[specimen]={}
                            if Experiment_Type in Data[specimen].keys():
                                print "-E- specimen %s has duplicate Experimental type %s. check it!"%(specimen,Experiment_Type)
                            
                            Data[specimen][Experiment_Type]={}
                            Data[specimen][Experiment_Type]['header_data']=tmp_header_data
                            Data[specimen][Experiment_Type]['meas_data']=[]

                            # read measurement data and sort in dictonaries
                            
                            while this_specimen:
                                line=fin.readline()
                                line_number+=1
                                # each specimen ends with "END" statement
                                if "END" in line:
                                    this_specimen=False
                                    break
                                this_line=line.strip('\n').split("|")
                                this_line_data=str(this_line[0]).split()+ this_line[1:-1]
                                tmp_data={}
                                for i in range(len(this_line_data)):
                                    tmp_data[meas_codes[i]]=this_line_data[i]
                                Data[specimen][Experiment_Type]['meas_data'].append(tmp_data)
                                

                    #-----------------------------------
                    # Convert to MagIC
                    #-----------------------------------


                    specimens_list=Data.keys()
                    specimens_list.sort()
                    for specimen in specimens_list:
                        Experiment_Types_list=Data[specimen].keys()
                        Experiment_Types_list.sort()
                        for Experiment_Type in Experiment_Types_list:

                            #-----------------------------------
                            # MW-PI-OT+:
                            #  Microwave Thellier Thellier protocol
                            # MW-PI-P:
                            #  Perpernicular mathod
                            #  demagnetizations until overprint is removed
                            #  then remagnetization perpendicular to the remaining NRM direction
                            #-----------------------------------

                            if Experiment_Type in ['MW-PI-OT+','MW-PI-P']:
                                
                                header_line=Data[specimen][Experiment_Type]['header_data']
                                experiment_treatments=[]
                                measurement_running_number=0
                                for meas_line in Data[specimen][Experiment_Type]['meas_data']:
                                                           
                                    MagRec={}
                                    # header_data
                                    MagRec['er_citation_names']="This study"
                                    MagRec["er_specimen_name"]=header_line['Sample code']
                                    MagRec["er_sample_name"]=self.get_sample_name(MagRec["er_specimen_name"],DIRS_data[dir_name]['sample_naming_convenstion'])
                                    MagRec["er_site_name"]=self.get_site_name(MagRec["er_sample_name"],DIRS_data[dir_name]['site_naming_convenstion'])
                                    MagRec['er_location_name']=DIRS_data[dir_name]['location_name'] 
                                    MagRec['er_analyst_mail_names']=header_line['Name of measurer']
                                    MagRec["magic_instrument_codes"]=header_line['Magnetometer name']+":"+header_line['Demagnetiser name']

                                    # meas data
                                    MagRec["measurement_flag"]='g'
                                    MagRec["measurement_standard"]='u'
                                    MagRec["measurement_number"]="%i"%measurement_running_number
                                    
                                    MagRec['treatment_mw_power']=meas_line['Microwave Power']
                                    CART=array([1e-9*float(meas_line['moment_X']),1e-9*float(meas_line['moment_Y']),1e-9*float(meas_line['moment_Z'])])  # Am^2
                                    DIR = cart2dir(CART)
                                    MagRec["measurement_dec"]="%.2f"%DIR[0]
                                    MagRec["measurement_inc"]="%.2f"%DIR[1]
                                    MagRec["measurement_magn_moment"]='%10.3e'%(math.sqrt(sum(CART**2)))
                                    MagRec["measurement_temp"]='273.' # room temp in kelvin
                                    labfield=float(meas_line['Applied field Intensity'])*1e-6
                                    MagRec["treatment_dc_field"]='%8.3e'%(labfield)
                                    MagRec["treatment_dc_field_phi"]=meas_line['Applied field Dec']
                                    MagRec["treatment_dc_field_theta"]=meas_line['Applied field Inc']
                                    date=meas_line['Measurement Date'].strip("\"").split('-')
                                    yyyy=date[2];mm=date[1];dd=date[0]
                                    hour=meas_line['Measurement Time'].strip("\"")
                                    MagRec["measurement_date"]=yyyy+':'+mm+":"+dd+":"+hour

                                    # identify the step in the experiment from Experiment_Type,  MW Input power, and Applied field Intensity:
                                    # Thellier-Thellier protocol
                                    
                                    if Experiment_Type =='MW-PI-OT+':
                                        lab_protocols_string="LP-PI-M:LP-PI-II:LP-PI-M-II:LP-PI-ALT-PMRM"
                                        # first line is the NRM always
                                        if len(experiment_treatments)==0:
                                            lab_treatment="LT-NO"
                                        elif labfield!=0 and float(meas_line['Microwave Power'])  < float(experiment_treatments[-1]):                            
                                            lab_treatment="LT-PMRM-I"                            
                                        else:                            
                                            lab_treatment="LT-M-I"
                                        experiment_treatments.append(meas_line['Microwave Power'])

                                    if Experiment_Type == 'MW-PI-P':
                                        lab_protocols_string="LP-PI-M:LP-PI-M-PERP"
                                        # first line is the NRM always
                                        if len(experiment_treatments)==0:
                                            lab_treatment="LT-NO"
                                        if labfield==0:
                                            lab_treatment="LT-M-Z"
                                        else:
                                            lab_treatment="LT-M-I:LT-NRM-PERP"
                                                                                        
                                    MagRec["magic_method_codes"]=lab_treatment+":"+lab_protocols_string
                                    MagRec["magic_experiment_name"]=specimen+":"+lab_protocols_string
                                    MagRecs.append(MagRec)
                                    measurement_running_number+=1
                                    headers=MagRec.keys()
                                    for key in headers:
                                        if key not in magic_measurements_headers:
                                            magic_measurements_headers.append(key)



                            else:
                                print "experiment format",Experiment_Type," is not supported yet. sorry.."

        fout=open("magic_measurements.txt",'w')
        fout.write("tab\tmagic_measurements\n")
        header_string=""
        for i in range(len(magic_measurements_headers)):
            header_string=header_string+magic_measurements_headers[i]+"\t"
        fout.write(header_string[:-1]+"\n")

        for MagRec in MagRecs:
            line_string=""
            for i in range(len(magic_measurements_headers)):
                if magic_measurements_headers[i] in MagRec.keys():
                    line_string=line_string+MagRec[magic_measurements_headers[i]]+"\t"
                else:
                    line_string=line_string+"\t"
                   
            fout.write(line_string[:-1]+"\n")



                           
        dlg1 = wx.MessageDialog(None,caption="Message:", message="file converted to magic_measurements.txt\n you can try running thellier gui...\n" ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()
        self.Destroy()
            
#------------------------------------------------------------------------
#   def main():
#------------------------------------------------------------------------


"""
NAME
    LIVMW_Ron_magic.py.py

DESCRIPTION
    converts XXX format files to magic_measurements format files

 
"""

if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = convert_livdb_files_to_MagIC("./")
    app.frame.Show()
    app.frame.Center()
    app.MainLoop()



                   
        
        
#main()

