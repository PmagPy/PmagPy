#--------------------------------------------------------------    
# converting magnetometer files to MagIC format
#--------------------------------------------------------------
import wx

class import_magnetometer_data(wx.Dialog):
    def __init__(self,parent,id,title,WD):
        wx.Dialog.__init__(self, parent, id, title)#, size=(300, 300))
        #super(import_magnetometer_data, self).__init__(*args, **kw) 
        self.WD=WD            
        self.InitUI()
        self.SetTitle("")
        
    def InitUI(self):

        pnl = wx.Panel(self)        
        vbox=wx.BoxSizer(wx.VERTICAL)

        formats=['generic format','SIO format','CIT format','2G-binary format','HUJI format','LDEO format','IODP SRM (csv) format','PMD (ascii) format','TDT format']
        sbs = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'step 1: choose file format' ), wx.VERTICAL )

        sbs.AddSpacer(5)
        self.oc_rb0 = wx.RadioButton(pnl, -1,label=formats[0],name='0', style=wx.RB_GROUP)
        sbs.Add(self.oc_rb0) 
        sbs.AddSpacer(5)
        sbs.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)  
        sbs.AddSpacer(5)
        
        for i in range(1,len(formats)):
            command="self.oc_rb%i = wx.RadioButton(pnl, -1, label='%s', name='%i')"%(i,formats[i],i)
            exec command
            command="sbs.Add(self.oc_rb%i)"%(i)
            exec command
            sbs.AddSpacer(5)  
        self.oc_rb0.SetValue(True) 
        
        #---------------------
        # OK/Cancel buttons 
        #---------------------
                
        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(pnl, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)
        self.cancelButton = wx.Button(pnl, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        hboxok.Add(self.okButton)
        hboxok.AddSpacer(20)
        hboxok.Add(self.cancelButton )

        #-----------------------
        # design the frame
        #-----------------------                
        
        vbox.AddSpacer(10)
        vbox.Add(sbs)
        vbox.AddSpacer(10)
        vbox.Add(hboxok)
        vbox.AddSpacer(10)

        hbox1=wx.BoxSizer(wx.HORIZONTAL)        
        hbox1.AddSpacer(10)
        hbox1.Add(vbox)
        hbox1.AddSpacer(10)

        pnl.SetSizer(hbox1)
        hbox1.Fit(self)

    def on_cancelButton(self,event):
        self.Destroy()

    def on_okButton(self,event):
        generic_dia = convert_generic_files_to_MagIC(self.WD)
        generic_dia.Show()
        generic_dia.Center()

#--------------------------------------------------------------    
# MagIC generic files conversion
#--------------------------------------------------------------


class convert_generic_files_to_MagIC(wx.Frame):
    """"""
    title = "PmagPy generic file conversion"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.Panel(self)
        self.max_files=10
        self.WD=WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        #---sizer infor ----

        #TEXT1="Generic thellier GUI file is a tab-delimited file with the following headers:\n"
        #TEXT2="Specimen  Treatment  Declination  Inclination  Moment\n"
        #TEXT3="Treatment: XXX.Y or XXX.YY where XXX is temperature in C, and YY is treatment code. See tutorial for explenation. NRM step is 000.00\n" 
        #TEXT4="Moment: In units of emu.\n"
        # 
        #TEXT=TEXT1+TEXT2+TEXT3+TEXT4
        TEXT="a template of a generic file can be found in www.blababla\n"
        bSizer_info = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.HORIZONTAL )
        bSizer_info.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)
            

        #---sizer 0 ----

        sbs = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'duplicate measurements' ), wx.HORIZONTAL )

        sbs.AddSpacer(5)
        self.average_duplicate_meas = wx.RadioButton(pnl, -1,label="",name='0', style=wx.RB_GROUP)
        sbs.Add(self.average_duplicate_meas) 
        sbs.AddSpacer(5)
        self.dont_average_duplicate_meas = wx.RadioButton(pnl, -1, label="use only the last measurement", name='1')
        sbs.Add(self.dont_average_duplicate_meas) 
        sbs.AddSpacer(5)
        self.dont_average_duplicate_meas.SetValue(True) 

        #---sizer 0 ----
        TEXT="\n\n\nFile: No spaces are alowd in path"
        bSizer0 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        bSizer0.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        bSizer0.AddSpacer(5)
        for i in range(self.max_files):
            command= "self.file_path_%i = wx.TextCtrl(self.panel, id=-1, size=(200,25), style=wx.TE_READONLY)"%i
            exec command
            command= "self.add_file_button_%i =  wx.Button(self.panel, id=-1, label='add',name='add_%i')"%(i,i)
            exec command
            command= "self.Bind(wx.EVT_BUTTON, self.on_add_file_button_i, self.add_file_button_%i)"%i
            #print command
            exec command            
            command="bSizer0_%i = wx.BoxSizer(wx.HORIZONTAL)"%i
            exec command
            command="bSizer0_%i.Add(wx.StaticText(pnl,label=('%i  '[:2])),wx.ALIGN_LEFT)"%(i,i+1)
            exec command
            
            command="bSizer0_%i.Add(self.file_path_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer0_%i.Add(self.add_file_button_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer0.Add(bSizer0_%i,wx.ALIGN_TOP)" %i
            exec command
            bSizer0.AddSpacer(5)
              
        #---sizer 1 ----

        TEXT="\n\n\nExperiment:"
        bSizer1 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        bSizer1.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        self.experiments_names=['Demag (AF and/or Thermal)','Paleointensity-IZZI','Paleointensity-IZ','Paleointensity-ZI','ATRM 6 positions','cooling rate','NLT']
        bSizer1.AddSpacer(5)
        for i in range(self.max_files):
            command="self.protocol_info_%i = wx.ComboBox(self.panel, -1, self.experiments_names[0], size=(150,25), choices=self.experiments_names, style=wx.CB_DROPDOWN)"%i
            exec command
            command="bSizer1.Add(self.protocol_info_%i,wx.ALIGN_TOP)"%i        
            exec command
            bSizer1.AddSpacer(5)

        #---sizer 2 ----

        TEXT="oven field in\nPI experiment:\nmicroT dec inc\n(example: 40 0 -90)"
        bSizer2 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        bSizer2.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        bSizer2.AddSpacer(5)
        for i in range(self.max_files):
            command= "self.file_info_Blab_%i = wx.TextCtrl(self.panel, id=-1, size=(40,25))"%i
            exec command
            command= "self.file_info_Blab_dec_%i = wx.TextCtrl(self.panel, id=-1, size=(40,25))"%i
            exec command
            command= "self.file_info_Blab_inc_%i = wx.TextCtrl(self.panel, id=-1, size=(40,25))"%i
            exec command          
            command="bSizer2_%i = wx.BoxSizer(wx.HORIZONTAL)"%i
            exec command
            command="bSizer2_%i.Add(self.file_info_Blab_%i ,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer2_%i.Add(self.file_info_Blab_dec_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer2_%i.Add(self.file_info_Blab_inc_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer2.Add(bSizer2_%i,wx.ALIGN_TOP)" %i
            exec command
            bSizer2.AddSpacer(5)


        #self.blab_info = wx.TextCtrl(self.panel, id=-1, size=(80,250), style=wx.TE_MULTILINE | wx.HSCROLL)
        #bSizer2.Add(self.blab_info,wx.ALIGN_TOP)        

        #---sizer 3 ----

        TEXT="\nUser\nname:\n(optional)"
        bSizer3 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        bSizer3.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        bSizer3.AddSpacer(5)
        for i in range(self.max_files):
            command= "self.file_info_user_%i = wx.TextCtrl(self.panel, id=-1, size=(60,25))"%i
            exec command
            command="bSizer3.Add(self.file_info_user_%i,wx.ALIGN_TOP)" %i
            exec command
            bSizer3.AddSpacer(5)

        #---sizer 4 ----

        TEXT="\n\nSample-specimen\nnaming convention:"
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

        TEXT="\n\nSite-sample\nnaming convention:"
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

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)        
        hbox2.Add(self.okButton)
        hbox2.Add(self.cancelButton )

        #------

        vbox=wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddSpacer(5)
        hbox.Add(bSizer0, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)
        hbox.Add(bSizer1, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)
        hbox.Add(bSizer2, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)
        hbox.Add(bSizer3, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)
        hbox.Add(bSizer4, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)
        hbox.Add(bSizer5, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)

        #-----
        
        vbox.AddSpacer(20)
        vbox.Add(bSizer_info,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)    
        vbox.Add(sbs,flag=wx.ALIGN_CENTER_HORIZONTAL)
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


    def on_add_file_button(self,event):

        dlg = wx.FileDialog(
            None,message="choose file to convert to MagIC",
            defaultDir=self.WD, 
            defaultFile="",
            style=wx.OPEN | wx.CHANGE_DIR
            )        
        if dlg.ShowModal() == wx.ID_OK:
            FILE = dlg.GetPath()
        # fin=open(FILE,'rU')
        self.file_path.AppendText(FILE+"\n")
        self.protocol_info.AppendText("IZZI"+"\n")


    def on_add_file_button_i(self,event):

        dlg = wx.FileDialog(
            None,message="choose file to convert to MagIC",
            defaultDir="./", 
            defaultFile="",
            style=wx.OPEN | wx.CHANGE_DIR
            )        
        if dlg.ShowModal() == wx.ID_OK:
            FILE = dlg.GetPath()
        # fin=open(FILE,'rU')
        button = event.GetEventObject()
        name=button.GetName()
        i=int((name).split("_")[-1])
        #print "The button's name is " + button.GetName()
        
        command="self.file_path_%i.SetValue(FILE)"%i
        exec command

        #self.file_path.AppendText(FILE)
        #self.protocol_info.AppendText("IZZI"+"\n")



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
                        print "-W- WARNING: duplicate measurements specimen %s, Treatment %s. keeping only the last one"%(tmp_data['Specimen'],tmp_data['Treatment'])
                        Data[specimen].pop()
                        
                Data[specimen].append(tmp_data)
        return(Data)               

    def on_okButton(self,event):


        #-----------------------------------
        # Prepare MagIC measurement file
        #-----------------------------------

        try:
            self.er_sample_data=self.read_magic_file(self.WD+"/er_samples.txt",'er_sample_name')
        except:
            print "-W- WARNING: Cant find er_samples.txt table"

        Data={}
        header_codes=[]
        ERROR=""
        datafiles=[]
        MagRecs=[]

        for i in range(self.max_files):
            # read data from generic file
            datafile=""
            command="datafile=self.file_path_%i.GetValue()"%i
            exec command
            if datafile!="":
                try:
                    this_file_data= self.read_generic_file(datafile)
                except:
                    print "-E- Cant read file %s" %datafile                
            else:
                continue

                
            # get experiment
            command="experiment=self.protocol_info_%i.GetValue()"%i
            exec command

            # get Blab
            labfield=["0","-1","-1"]
            command="labfield[0]=self.file_info_Blab_%i.GetValue()"%i
            exec command
            command="labfield[1]=self.file_info_Blab_dec_%i.GetValue()"%i
            exec command
            command="labfield[2]=self.file_info_Blab_inc_%i.GetValue()"%i
            exec command
            
            # get User_name
            user_name=""
            command="user_name=self.file_info_user_%i.GetValue()"%i
            exec command
            
            # get sample-specimen naming convention

            sample_naming_convenstion=["",""]
            command="sample_naming_convenstion[0]=self.sample_naming_convention_%i.GetValue()"%i
            exec command
            command="sample_naming_convenstion[1]=self.sample_naming_convention_char_%i.GetValue()"%i
            exec command
            
            # get site-sample naming convention

            site_naming_convenstion=["",""]
            command="site_naming_convenstion[0]=self.site_naming_convention_%i.GetValue()"%i
            exec command
            command="site_naming_convenstion[1]=self.site_naming_convention_char_%i.GetValue()"%i
            exec command

            #-------------------------------
            Magic_lab_protocols={}
            Magic_lab_protocols['Demag (AF and/or Thermal)'] = "LP-DIR"
            Magic_lab_protocols['Paleointensity-IZZI'] = "LP-PI-TRM:LP-PI-BT-IZZI"
            Magic_lab_protocols['Paleointensity-IZ'] = "LP-PI-TRM:LP-PI-TRM-IZ"
            Magic_lab_protocols['Paleointensity-ZI'] = "LP-PI-TRM:LP-PI-TRM-ZI"
            Magic_lab_protocols['ATRM 6 positions'] = "LP-AN-TRM" # LT-T-I:
            Magic_lab_protocols['cooling rate'] = "LP-CR-TRM" # LT-T-I:
            Magic_lab_protocols['NLT'] = "LP-TRM" # LT-T-I:
            #------------------------------
            
            ErSamplesRecs=[]
            for specimen in this_file_data.keys():
                measurement_running_number=0
                this_specimen_treatments=[] # a list of all treatments
                MagRecs_this_specimen=[]
                LP_this_specimen=[] # a list of all lab protocols
                IZ,ZI=0,0 # counter for IZ and ZI steps
                
                for meas_line in this_file_data[specimen]:
                    
                    #------------------
                    # MagRec data
                    #------------------

                    MagRec={}
                    MagRec['er_citation_names']="This study"
                    MagRec["er_specimen_name"]=meas_line['specimen']
                    MagRec["er_sample_name"]=self.get_sample_name(MagRec["er_specimen_name"],sample_naming_convenstion)
                    MagRec["er_site_name"]=self.get_site_name(MagRec["er_sample_name"],site_naming_convenstion)
                    MagRec['er_location_name']=""
                    MagRec['er_analyst_mail_names']=user_name 
                    MagRec["magic_instrument_codes"]="" 
                    MagRec["measurement_flag"]='g'
                    MagRec["measurement_number"]="%i"%measurement_running_number
                    
                    MagRec["measurement_magn_moment"]='%10.3e'%(float(meas_line["moment (emu)"])*1e-3) # in Am^2
                    MagRec["measurement_temp"]='273.' # room temp in kelvin
                    if 'Paleointensity' in experiment or 'cooling rate' in experiment or "NLT" in experiment:                        
                        MagRec["treatment_dc_field"]='%8.3e'%(float(labfield[0])*1e-6)
                        MagRec["treatment_dc_field_phi"]="%.2f"%(float(labfield[1]))
                        MagRec["treatment_dc_field_theta"]="%.2f"%(float(labfield[2]))
                    else:
                        MagRec["treatment_dc_field"]=""
                        MagRec["treatment_dc_field_phi"]=""
                        MagRec["treatment_dc_field_theta"]=""
                    
                    # need to be changed !!!! Ron dont forget ! 
                    print "Ron, dont forget    magic_experiment_name"
                    #MagRec["magic_experiment_name"]=MagRec["er_specimen_name"]+":"+Magic_lab_protocols[experiment]

                    # Ron, change this one:
                    #this_specimen_treatments.append(float(meas_line['treatment']))

                    ## fill in LP and LT
                    #lab_protocols_string=Magic_lab_protocols[experiment]
                    #tr_temp=float(meas_line['step'].split(".")[0])
                    #if len(meas_line['step'].split("."))==1:
                    #    tr_tr=0
                    #else:
                    #    tr_tr=float(meas_line['step'].split(".")[1])

                    #------------------
                    # treatment is split to a list of float (100.0 --> [100.,1.]
                    #------------------

                    treatment=float(meas_line['step'].split("."))
                    treatment[0]=float(treatment[0])
                    if len(treatment)==0:
                        treatment[1]=0
                    else:
                        treatment[1]=float(treatment[1])
                    
                    #------------------
                    # treatment temperature/peak field 
                    #------------------
                    
                    if 'Demag' in experiment:
                        if meas_line['treatment_type']=='A':
                            MagRec['treatment_temp']="273."
                            MagRec["treatment_ac_field"]="%.4f"%(treatment[0]*1e-3)                                                        
                        elif meas_line['treatment_type']=='N':
                            MagRec['treatment_temp']="273."
                            MagRec["treatment_ac_field"]=""                                                        
                        else:
                            MagRec['treatment_temp']="%.2f"%(treatment[0]+273.)
                            MagRec["treatment_ac_field"]=""                                                        
                    else: 
                            MagRec['treatment_temp']="%.2f"%(treatment[0]+273.)
                            MagRec["treatment_ac_field"]=""                                                        
                    
                    
                    #---------------------                    
                    # Lab treatment
                    # Lab protocol
                    #---------------------
                                        
                    #---------------------                    
                    # identify NRM:
                    #---------------------
                    if float['treatment']==0:
                        LT="LT-NO"
                        LP=""

                    #---------------------                    
                    # Lab treatment and lab protocoal for paleointensity experiment
                    #---------------------
                                        
                    elif "Paleointensity" in experiment:
                        if treatment[1]==0:
                            LT="LT-T-Z"
                        elif  treatment[1]==1 or treatment[1]==10:
                            LT="LT-T-I"
                        elif treatment[1]==2 or treatment[1]==20:                            
                            LT="LT-PTRM-I"            
                        elif treatment[1]==3 or treatment[1]==30:                            
                            LT="LT-PTRM-MD"            
                        elif treatment[1]==4 or treatment[1]==40:                            
                            LT="LT-PTRM-AC"            
                        else:
                            print "-E- unknown measurement code specimen %s treatmemt %s"%(meas_line['specimen'],meas_line['treatment'])
                            MagRec={}
                            continue
                        this_specimen_treatments.append(float(meas_line['step']))
 
                    LP="LP-PI-TRM"
                    if treatment[1]==0:                            
                        if treatment[0]+0.1 in this_specimen_treatments[:-1]:
                            IZ=IZ+1
                        else:
                            ZI=ZI+1
                                            
                    elif treatment[1]==10 or treatment[1]==1:                            
                        if treatment[0]+0.0 in this_specimen_treatments[:-1]:
                            ZI=ZI+1
                        else:
                            IZ=IZ+1
                     
                    #---------------------                    
                    # Lab treatment and lab protocoal for demag experiment
                    #---------------------
                    elif "Demag" in experiment:
                        if meas_line['treatment_type']=='A': 
                            LT="LT-AF-Z"
                            LP="LP-DIR-AF"
                        else:
                            LT="LT-T-Z"
                            LP="LP-DIR-T"
                             
                        
                    #---------------------                    
                    # Lab treatment and lab protocoal for ATRM experiment
                    #---------------------
                                       
                    elif 'ATRM' in experiment :
                        LP="LP-AN-TRM"
                        if treatment[1]==0:
                            LT="LT-T-Z"
                            MagRec["treatment_dc_field_phi"]='0'
                            MagRec["treatment_dc_field_theta"]='0'
                        else:
                                    
                            # find the direction of the lab field in two ways:
                            
                            # (1) using the treatment coding (XX.1=+x, XX.2=+y, XX.3=+z, XX.4=-x, XX.5=-y, XX.6=-z)
                            tdec=[0,90,0,180,270,0,0,90,0]
                            tinc=[0,0,90,0,0,-90,0,0,90]
                            if treatment[1] < 10:
                                ipos_code=int(treatment[1])-1
                            else:
                                ipos_code=int(treatment[1]/10)-1
                            
                            # (2) using the magnetization
                            if meas_line["dec_s"]!="":
                                DEC=float(meas_line["dec_s"])
                                INC=float(meas_line["inc_s"])
                            elif meas_line["dec_g"]!="":
                                DEC=float(meas_line["dec_g"])
                                INC=float(meas_line["inc_g"])
                            elif meas_line["dec_t"]!="":
                                DEC=float(meas_line["dec_t"])
                                INC=float(meas_line["inc_t"])
                            if INC < 45 and INC > -45:
                                if DEC>315  or DEC<45: ipos_guess=0
                                if DEC>45 and DEC<135: ipos_guess=1
                                if DEC>135 and DEC<225: ipos_guess=3
                                if DEC>225 and DEC<315: ipos_guess=4
                            else:
                                if INC >45: ipos_guess=2
                                if INC <-45: ipos_guess=5
                            # prefer the guess over the code
                            ipos=ipos_guess
                            # check it 
                            if treatment[1]!= 7 and treatment[1]!= 70:
                                if ipos_guess!=ipos_code:
                                    print "-W- WARNING: check specimen %s step %s, ATRM measurements, coding does not match the direction of the lab field"%(specimen,meas_line['Treatment'])
                            MagRec["treatment_dc_field_phi"]='%7.1f' %(tdec[ipos])
                            MagRec["treatment_dc_field_theta"]='%7.1f'% (tinc[ipos])
                                
                            if float(treatment[1])==70 or float(treatment[1])==7: # alteration check as final measurement
                                    LT="LT-PTRM-I"
                            else:
                                    LT="LT-T-I"

                    #---------------------                    
                    # Lab treatment and lab protocoal for cooling rate experiment
                    #---------------------
                                                               
                    elif 'cooling' in experiment :
                        print "Dont support yet cooling rate experiment file. Contact rshaar@ucsd.edu"
 
                    #---------------------                    
                    # Lab treatment and lab protocoal for NLT experiment
                    #---------------------
                    
                    elif NLT in experiment:
                        LP="LP-TRM"
                        if treatment[1]==0:
                            LT="LT-T-Z"
                        else:
                            LT="LT-T-I"
                            
                    MagRec["magic_method_codes"]=LP+":"+LT




                    # see if core azimuth and tilt-corrected data are in er_samples.txt
                    sample=MagRec["er_sample_name"]
                    found_sample_azimuth,found_sample_dip,found_sample_bed_dip_direction,found_sample_bed_dip=False,False,False,False
                    if sample in self.er_sample_data.keys():
                        if "sample_azimuth" in self.er_sample_data[sample].keys() and self.er_sample_data[sample]['sample_azimuth'] !="":
                            sample_azimuth=float(self.er_sample_data[sample]['sample_azimuth'])
                            found_sample_azimuth=True
                        if "sample_dip" in self.er_sample_data[sample].keys() and self.er_sample_data[sample]['sample_dip']!="":
                            sample_dip=float(self.er_sample_data[sample]['sample_dip'])
                            found_sample_dip=True
                        if "sample_bed_dip_direction" in self.er_sample_data[sample].keys() and self.er_sample_data[sample]['sample_bed_dip_direction']!="":
                            sample_bed_dip_direction=float(self.er_sample_data[sample]['sample_bed_dip_direction'])
                            found_sample_bed_dip_direction=True
                        if "sample_bed_dip" in self.er_sample_data[sample].keys() and self.er_sample_data[sample]['sample_bed_dip']!="":
                            sample_bed_dip=float(self.er_sample_data[sample]['sample_bed_dip'])
                            found_sample_bed_dip=True
                    else:
                        self.er_sample_data[sample]={}
                    
                    #--------------------
                    # deal with sample orientation
                    #--------------------

                    found_s,found_geo,found_tilt=False,False,False
                    if "dec_s" in meas_line.keys() and "inc_s" in meas_line.keys():
                        found_s=True
                        MagRec["measurement_dec"]=meas_line["dec_s"]
                        MagRec["measurement_inc"]=meas_line["inc_s"]
                    if "dec_g" in meas_line.keys() and "inc_g" in meas_line.keys():
                        found_geo=True
                    if "dec_t" in meas_line.keys() and "inc_t" in meas_line.keys():
                        found_tilt=True
                        
                    #-----------------------------                    
                    # specimen coordinates: no
                    # geographic coordinates: yes
                    #-----------------------------                    
                    
                    if found_geo and not found_s:
                        MagRec["measurement_dec"]=meas_line["dec_g"]
                        MagRec["measurement_inc"]=meas_line["inc_g"]
                        
                        # core azimuth/plunge is not in er_samples.txt
                        if not found_sample_dip or not found_sample_azimuth:
                            self.er_sample_data[sample]['sample_azimuth']="0"
                            self.er_sample_data[sample]['sample_dip']="0"

                        # core azimuth/plunge is in er_samples.txt                        
                        else:
                            sample_azimuth=float(self.er_sample_data[sample]['sample_azimuth'])  
                            sample_dip=float(self.er_sample_data[sample]['sample_dip'])   
                            if sample_azimuth!=0 and sample_dip!=0:
                                print "-W- WARNING: delete core azimuth/plunge in er_samples.txt\n\
                                becasue dec_s and inc_s are not avaialable" 

                    #-----------------------------                                                
                    # specimen coordinates: no
                    # geographic coordinates: no
                    #-----------------------------                    
                    if not found_geo and not found_s:
                        print "-E- ERROR: sample %s does not have dec_s/inc_s or dec_g/inc_g. Ignore specimen %s "%(sample,specimen)
                        break
                           
                    #-----------------------------                                                
                    # specimen coordinates: yes
                    # geographic coordinates: yes
                    #
                    # commant: Ron, this need to be tested !!
                    #-----------------------------                    
                    if found_geo and found_s:
                        
                        cdec,cinc=float(meas_line["dec_s"]),float(meas_line["inc_s"])
                        gdec,ginc=float(meas_line["dec_g"]),float(meas_line["inc_g"])
                        az,pl=pmag.get_azpl(cdec,cinc,gdec,ginc)

                        # core azimuth/plunge is not in er_samples.txt:
                        # calculate core az/pl and add it to er_samples.txt
                        if not found_sample_dip or not found_sample_azimuth:
                            self.er_sample_data[sample]['sample_azimuth']="%.1f"%az
                            self.er_sample_data[sample]['sample_dip']="%.1f"%pl
                        
                        # core azimuth/plunge is in er_samples.txt
                        else:
                            if float(self.er_sample_data[sample]['sample_azimuth'])!= az:
                                print "-E- ERROR in sample_azimuth sample %s. Check it! using the value in er_samples.txt"%sample
                                
                            if float(self.er_sample_data[sample]['sample_dip'])!= pl:
                                print "-E- ERROR in sample_dip sample %s. Check it! using the value in er_samples.txt"%sample
                            
                    #-----------------------------                                                
                    # specimen coordinates: yes
                    # geographic coordinates: no
                    #-----------------------------                    
                    if found_geo and found_s:
                        if found_sample_dip and found_sample_azimuth:
                            pass
                            # (nothing to do)
                        else:
                            print "-E- ERROR: missing sample_dip or sample_azimuth for sample %s.ignoring specimens "%sample
                            break 
 
                    #-----------------------------                                                
                    # tilt-corrected coordinates: yes
                    # geographic coordinates: no
                    #-----------------------------                    
                    if found_tilt and not found_geo:
                            print "-E- ERROR: missing geographic data for sample %s. Ignoring tilt-corrected data "%sample
                    if found_tilt and found_geo:
                        dec_geo,inc_geo=float(meas_line["dec_g"]),float(meas_line["inc_g"])
                        dec_tilt,inc_tilt=float(meas_line["dec_t"]),float(meas_line["inc_t"])
                        if dec_geo==dec_tilt and inc_geo==inc_tilt:
                           DipDir,Dip=0.,0. 
                        else:
                           DipDir,Dip=pmag.get_tilt(dec_geo,inc_geo,dec_tilt,inc_tilt)
                            
                        if not found_sample_bed_dip_direction or not found_sample_bed_dip:
                            print "-I- calculating dip and dip direction used for tilt correction sample %s. results are put in er_samples.txt"%sample
                            self.er_sample_data[sample]['sample_bed_dip_direction']="%.1f"%DipDir
                            self.er_sample_data[sample]['sample_bed_dip']="%.1f"%Dip

                    #-----------------------------                                                
                    # er_samples method codes
                    # geographic coordinates: no
                    #-----------------------------                    
                    if found_tilt or found_geo:
                        self.er_sample_data[sample]['magic_method_codes']="SO-NO"               
                    #-----                    
                    # Lab treatments and MagIC methods
                    #-----                    
                    if meas_line['treatment']=="N":
                        LT="LT-NO"
                        LP="" 
                        MagRec["treatment_temp"]="273."                        
                        #MagRec["treatment_temp"]
                    elif meas_line['treatment']=="A":
                        LT="LT-AF-Z" 
                        LP="LP-DIR-AF"
                        MagRec["treatment_ac_field"]="%.4f"%(float(meas_line['step'])*1e-3)
                        MagRec["treatment_temp"]="273."                        
                        #print MagRec["treatment_ac_field"],"treatment_ac_field"
                    elif meas_line['treatment']=="T":
                        LT="LT-T-Z" 
                        LP="LP-DIR-T"
                        MagRec["treatment_temp"]="%.1f"%(float(meas_line['step'])+273.)
                        #print MagRec["treatment_temp"],"treatment_temp"

                    #if LT not in this_specimen_LT:
                    #    this_specimen_LT.append(LT)
                    #if LP!="" and LP not in this_specimen_LP:
                    #    this_specimen_LP.append(LP)
                                                                                            
                    #MagRec["magic_experiment_name"]=MagRec["er_specimen_name"]+":"+":".join(this_specimen_LP)
                    
                    #-----------------
                    # er_samples_data
                    #
                    if sample in self.er_sample_data.keys():
                        self.er_sample_data[sample]['er_sample_name']=sample
                        self.er_sample_data[sample]['er_site_name']=MagRec["er_site_name"]
                        self.er_sample_data[sample]['er_location_name']=MagRec["er_location_name"]

                    MagRec["magic_method_codes"]=LT
                    MagRecs_this_specimen.append(MagRec)

                    if LP!="" and LP not in this_specimen_LP:
                        LP_this_specimen.append(LP)
                    
                    measurement_running_number+=1
                    #-------                    

                #-------                    
                # add magic_experiment_name
                # fix magic_method_codes with the correct lab protocol
                #-------                    
                for MagRec in MagRecs_this_specimen:
                    # check if this is IZZI, ZI, or IZ:
                    print "Ron, add a check for IZZI, IZ, or ZI !! and make the right LP for it"
                    
                    MagRec["magic_experiment_name"]=MagRec["er_specimen_name"]+":"+":".join(LP_this_specimen)
                    MagRec["magic_method_codes"]=MagRec["magic_method_codes"]+":"+":".join(LP_this_specimen)
                    MagRecs.append(MagRec)   
                                        
                    #line_string=""
                    #for i in range(len(magic_headers)):
                    #    line_string=line_string+MagRec[magic_headers[i]]+"\t"
                    #fout.write(line_string[:-1]+"\n")


        #--
        MSG="files converted to MagIC format and merged into one file:\n magic_measurements.txt\n "            
        dlg1 = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()

        self.Destroy()


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
            if len(site_splitted)==1:
                site=site_splitted[0]
            else:
                site=d.join(site_splitted[:-1])
        
        return site


