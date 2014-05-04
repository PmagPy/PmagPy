#!/usr/bin/env python
import wx
import wx.lib.buttons as buttons
import pmag
import pmag_dialogs
import thellier_gui_dialogs
import os
import sys



class MagMainFrame(wx.Frame):
    """"""
    title = "PmagPy MagIC main functions"

    def __init__(self):
        print 'init magic main frame'
        global FIRST_RUN
        FIRST_RUN=True
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.Panel(self)
        self.InitUI()
        self.create_menu()
        self.get_DIR()        # choose directory dialog                    
    
    def InitUI(self):

        pnl = self.panel

        #---sizer logo ----
                
        #start_image = wx.Image("/Users/ronshaar/PmagPy/images/logo2.png")
        #start_image = wx.Image("/Users/Python/simple_examples/001.png")
        #start_image.Rescale(start_image.GetWidth(), start_image.GetHeight())
        #image = wx.BitmapFromImage(start_image)
        #self.logo = wx.StaticBitmap(self.panel, -1, image) 
                                  
        #---sizer 0 ----
        bSizer0 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "Choose MagIC project directory" ), wx.HORIZONTAL )
        self.dir_path = wx.TextCtrl(self.panel, id=-1, size=(600,25), style=wx.TE_READONLY)
        self.change_dir_button = buttons.GenButton(self.panel, id=-1, label="change dir",size=(-1, -1))
        self.change_dir_button.SetBackgroundColour("#F8F8FF")
        self.change_dir_button.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_change_dir_button,self.change_dir_button)
        bSizer0.Add(self.change_dir_button,wx.ALIGN_LEFT)
        bSizer0.AddSpacer(40)
        bSizer0.Add(self.dir_path,wx.ALIGN_CENTER_VERTICAL)
    
                
                                
        #---sizer 1 ----
        bSizer1 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "Import MagIC formatted data to working directory" ), wx.HORIZONTAL )
        
        TEXT="1. convert magnetometer files to MagIC format"
        self.btn1=buttons.GenButton(self.panel, id=-1, label=TEXT,size=(450, 50))        
        self.btn1.SetBackgroundColour("#FDC68A")
        self.btn1.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_convert_file,self.btn1)
        TEXT="2. optional: \n calculate geographic/tilt-corrected directions"
        self.btn2 =buttons.GenButton(self.panel, id=-1, label=TEXT,size=(450, 50))
        self.btn2.SetBackgroundColour("#FDC68A")
        self.btn2.InitColours()
        TEXT="3. fill Earth-Ref data"
        self.btn3 =buttons.GenButton(self.panel, id=-1, label=TEXT,size=(450, 50))
        self.btn3.SetBackgroundColour("#FDC68A")
        self.btn3.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_er_data,self.btn3)

        TEXT="unpack downloaded txt file "
        self.btn4 =buttons.GenButton(self.panel, id=-1, label=TEXT,size=(300, 50))
        self.btn4.SetBackgroundColour("#FDC68A")
        self.btn4.InitColours()
 
        #str = "OR"
        OR = wx.StaticText(self.panel, -1, "or", (20, 120))
        font = wx.Font(18, wx.SWISS, wx.NORMAL, wx.NORMAL)
        OR.SetFont(font)
            
                                  
        #bSizer0.Add(self.panel,self.btn1,wx.ALIGN_TOP)
        bSizer1_1 = wx.BoxSizer(wx.VERTICAL)
        bSizer1_1.AddSpacer(20)
        bSizer1_1.Add(self.btn1,wx.ALIGN_TOP)
        bSizer1_1.AddSpacer(20)
        bSizer1_1.Add(self.btn2,wx.ALIGN_TOP)
        bSizer1_1.AddSpacer(20)
        bSizer1_1.Add(self.btn3,wx.ALIGN_TOP)
        bSizer1_1.AddSpacer(20)
                
        bSizer1.Add(bSizer1_1,wx.ALIGN_CENTER,wx.EXPAND)
        bSizer1.AddSpacer(20)
        
        bSizer1.Add(OR, 0, wx.ALIGN_CENTER, 0)
        bSizer1.AddSpacer(20)
        bSizer1.Add(self.btn4, 0, wx.ALIGN_CENTER, 0)
        bSizer1.AddSpacer(20)


        #---sizer 2 ----
        bSizer2 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "Analysis and plots" ), wx.HORIZONTAL )
        
        TEXT="Demag GUI"
        self.btn_demag_gui =buttons.GenButton(self.panel, id=-1, label=TEXT,size=(300, 50))
        self.btn_demag_gui.SetBackgroundColour("#6ECFF6")
        self.btn_demag_gui.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_run_demag_gui,self.btn_demag_gui)

        TEXT="Thellier GUI"
        self.btn_thellier_gui =buttons.GenButton(self.panel, id=-1, label=TEXT,size=(300, 50))
        self.btn_thellier_gui.SetBackgroundColour("#6ECFF6")
        self.btn_thellier_gui.InitColours()
        self.Bind(wx.EVT_BUTTON, self.on_run_thellier_gui,self.btn_thellier_gui)

        bSizer2.AddSpacer(20)
        bSizer2.Add(self.btn_demag_gui, 0, wx.ALIGN_CENTER, 0)
        bSizer2.AddSpacer(20)
        bSizer2.Add(self.btn_thellier_gui, 0, wx.ALIGN_CENTER, 0)
        bSizer2.AddSpacer(20)
        
        #---sizer 3 ----
        bSizer3 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "Upload to MagIC database" ), wx.HORIZONTAL )
        
        TEXT="prepare upload txt file"
        self.btn_magic =buttons.GenButton(self.panel, id=-1, label=TEXT,size=(300, 50))
        self.btn_magic.SetBackgroundColour("#C4DF9B")
        self.btn_magic.InitColours()

        bSizer3.AddSpacer(20)
        bSizer3.Add(self.btn_magic, 0, wx.ALIGN_CENTER, 0)
        bSizer3.AddSpacer(20)



        #---arange sizers ----
        
        hbox=wx.BoxSizer(wx.HORIZONTAL)
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(5)
        #vbox.Add(self.logo,0,wx.ALIGN_CENTER,0)
        vbox.AddSpacer(5)        
        vbox.Add(bSizer0,0,wx.ALIGN_CENTER,0)
        vbox.AddSpacer(10)        
        vbox.Add(bSizer1,0,wx.ALIGN_CENTER,0)
        vbox.AddSpacer(10)        
        vbox.Add(bSizer2,0,wx.ALIGN_CENTER,0)
        vbox.AddSpacer(10)        
        vbox.Add(bSizer3,0,wx.ALIGN_CENTER,0)
        vbox.AddSpacer(10)        
        #vbox.Add(bSizer1)
        #vbox.AddSpacer(20)        
        #vbox.Add(bSizer2)
        #vbox.AddSpacer(20)  
        hbox.AddSpacer(10)      
        hbox.Add(vbox,0,wx.ALIGN_CENTER,0)
        hbox.AddSpacer(5)      
              
        pnl.SetSizer(hbox)
        hbox.Fit(self)
        

    #----------------------------------------------------------------------


    def get_DIR(self):
        """ Choose a working directory dialog
        """
        self.WD=""
        if "-WD" in sys.argv and FIRST_RUN:
            ind=sys.argv.index('-WD')
            self.WD=sys.argv[ind+1]            
        
        else:
            
            
            
            TEXT1="Set Project MagIC Directory.\nPath should have NO SPACES.\n This Directory is to be used by this program ONLY"               
            dlg1 = wx.MessageDialog(self, caption="First step",message=TEXT1,style=wx.OK|wx.ICON_EXCLAMATION)
            result1 = dlg1.ShowModal()            
            if result1 == wx.ID_OK:            
                dlg1.Destroy()

            
            TEXT="choose directory. No spaces are allowed in path!"
            currentDirectory=os.getcwd()
            dialog = wx.DirDialog(None, TEXT,defaultPath = currentDirectory ,style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
            result=dialog.ShowModal()                                     
            if result == wx.ID_OK:
              self.WD=dialog.GetPath()
            dialog.Destroy()
        
        os.chdir(self.WD)
        self.WD=os.getcwd()+"/"
        self.dir_path.SetValue(self.WD)

    #----------------------------------------------------------------------
    
    def getFolderBitmap():
        img = folder_icon.GetImage().Rescale(50, 50)
        return img.ConvertToBitmap()   
                 
                  
    def on_change_dir_button(self,event):
        currentDirectory=os.getcwd()
        dialog = wx.DirDialog(None, "choose directory:",defaultPath = currentDirectory ,style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
            self.WD=dialog.GetPath()
            os.chdir(self.WD)
            self.dir_path.SetValue(self.WD)
            dialog.Destroy()

    def on_run_thellier_gui(self,event):
        outstring="thellier_gui.py -WD %s"%self.WD
        print "-I- running python script:\n %s"%(outstring)
        os.system(outstring)

    def on_run_demag_gui(self,event):
        outstring="demag_gui.py -WD %s"%self.WD
        print "-I- running python script:\n %s"%(outstring)
        os.system(outstring)
        
    def on_convert_file(self,event):
        print 'convert file'
        pmag_dialogs_dia=pmag_dialogs.import_magnetometer_data(None, -1, '',self.WD)
        pmag_dialogs_dia.Center()
        pmag_dialogs_dia.ShowModal()
                                    
    def on_er_data(self,event):

        import MagIC_Model_Builder
        foundHTML=False
        try:
            PATH= sys.modules['MagIC_Model_Builder'].__file__
            HTML_PATH="/".join(PATH.split("/")[:-1]+["MagICModlBuilderHelp.html"])
            foundHTML=True
        except:
            pass
        if foundHTML:
            help_window=MagIC_Model_Builder.MyHtmlPanel(None,HTML_PATH)
            help_window.Show()
            
        dia = MagIC_Model_Builder.MagIC_model_builder(self.WD,self.Data,self.Data_hierarchy)
        dia.Show()
        dia.Center()
                                                                                                                                                                                                                        
#==============================================================
# Menu Bar functions
#==============================================================

    #----------------------------------------------------------------------
        
    def create_menu(self):
        """ Create menu
        """
        self.menubar = wx.MenuBar()

        menu_file = wx.Menu()
        
        m_change_working_directory = menu_file.Append(-1, "&Change MagIC project directory", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_change_working_directory, m_change_working_directory)

        m_clear_working_directory = menu_file.Append(-1, "&Clear MagIC project directory", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_change_working_directory, m_change_working_directory)

        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        #self.Bind(wx.EVT_MENU, self.on_menu_exit, m_exit)
                                                                                                                                                                                                           
        #-----------------                            

        menu_import = wx.Menu()

        #-----------------                            

        menu_analysis_and_plots = wx.Menu()

        #-------------------

        menu_utilities = wx.Menu()

        #-------------------
       
        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_import, "&Import")
        self.menubar.Append(menu_analysis_and_plots, "&Analysis and Plots")
        self.menubar.Append(menu_utilities, "&Utilities")        
        self.SetMenuBar(self.menubar)

    #============================================
        


if __name__ == "__main__":
    app = wx.App(redirect=True, filename="beta_log.log")
    frame = MagMainFrame()
    frame.Center()
    frame.Show()
    app.MainLoop()
