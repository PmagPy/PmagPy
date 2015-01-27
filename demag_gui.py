#!/usr/bin/env pythonw

#============================================================================================
# LOG HEADER:
#============================================================================================
#
# Demag_GUI Version 0.30 fix backward compatibility with strange pmag_speciemns.txt 01/29/2015
#
# Demag_GUI Version 0.29 fix on_close_event 23/12/2014

# Demag_GUI Version 0.28 fix on_close_event 12/12/2014

# Demag_GUI Version 0.27 some minor bug fix

# Demag_GUI Version 0.26 (version for MagIC workshop) by Ron Shaar 5/8/2014
#
# Demag_GUI Version 0.25 (beta) by Ron Shaar
#
# Demag_GUI Version 0.24 (beta) by Ron Shaar
#
# Demag_GUI Version 0.23 (beta) by Ron Shaar
#
# Demag_GUI Version 0.22 (beta) by Ron Shaar
#
# Demag_GUI Version 0.21 (beta) by Ron Shaar
# 
#
#
#============================================================================================


#--------------------------------------
# definitions
#--------------------------------------


global CURRENT_VRSION
CURRENT_VRSION = "v.0.30"
import matplotlib
matplotlib.use('WXAgg')

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas 
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

import sys,pylab,scipy,os
try:
    import zeq_gui_preferences
except:
    pass
import stat
import subprocess
import time
import wx
import wx.grid
import random
import numpy
from pylab import *
from scipy.optimize import curve_fit
import wx.lib.agw.floatspin as FS
try:
    from mpl_toolkits.basemap import Basemap, shiftgrid
except:
    pass

import pmag,demag_dialogs
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
import copy
from copy import deepcopy



matplotlib.rc('xtick', labelsize=10) 
matplotlib.rc('ytick', labelsize=10) 
matplotlib.rc('axes', labelsize=8) 
matplotlib.rcParams['savefig.dpi'] = 300.

rcParams.update({"svg.embed_char_paths":False})
rcParams.update({"svg.fonttype":'none'})


#--------------------------------------
# ZEQ GUI FRAME
#--------------------------------------

class Zeq_GUI(wx.Frame):
    """ The main frame of the application
    """
    title = "PmagPy Demag GUI %s (beta)"%CURRENT_VRSION
    
    def __init__(self, WD):
        
        TEXT="""
        NAME
   	demag_gui.py
    
        DESCRIPTION
   	GUI for interpreting demagnetization data (AF and/or thermal).
   	For tutorial chcek PmagPy cookbook in http://earthref.org/PmagPy/cookbook/   	    
        """  
        args=sys.argv
        if "-h" in args:
	   print TEXT
	   sys.exit()

        global FIRST_RUN
        FIRST_RUN=True
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.redo_specimens={}
        self.currentDirectory = os.getcwd() # get the current working directory
        if WD:
            self.WD = WD
            self.get_DIR(WD)        # initialize directory variables
        else:
            self.get_DIR()        # choose directory dialog, then initialize directory variables
        
        # initialize acceptence criteria with NULL values
        self.acceptance_criteria=pmag.initialize_acceptance_criteria()
        try:
            self.acceptance_criteria=pmag.read_criteria_from_file(os.path.join(self.WD, "pmag_criteria.txt"), self.acceptance_criteria)
        except:
            print "-I- Cant find/read file  pmag_criteria.txt"          
        
         
        preferences=self.get_preferences()
        self.dpi = 100
        self.preferences={}
        self.preferences=preferences
        # inialize selecting criteria

        self.COORDINATE_SYSTEM='specimen'
        self.Data_info=self.get_data_info() # Read  er_* data
        self.Data,self.Data_hierarchy=self.get_data() # Get data from magic_measurements and rmag_anistropy if exist.

        
        self.pmag_results_data={}
        for level in ['specimens','samples','sites','lcoations','study']:
            self.pmag_results_data[level]={}
        self.high_level_means={}

        high_level_means={}                                            
        for high_level in ['samples','sites','locations','study']:
            if high_level not in self.high_level_means.keys():
                self.high_level_means[high_level]={}
        
        
        self.Data_samples={}
        self.last_saved_pars={}
        self.specimens=self.Data.keys()         # get list of specimens
        self.specimens.sort()                   # get list of specimens
        if len(self.specimens)>0:
            self.s=str(self.specimens[0])
        else:
            self.s=""
        self.pars={} 
        self.samples=self.Data_hierarchy['samples'].keys()         # get list of samples
        self.samples.sort()                   # get list of specimens
        self.sites=self.Data_hierarchy['sites'].keys()         # get list of sites
        self.sites.sort()                   # get list of sites
        self.locations=self.Data_hierarchy['locations'].keys()         # get list of sites
        self.locations.sort()                   # get list of sites

        # check if pmag_specimens.txt exist. If yes, import speci
        #self.get_pmag_tables()
        #self.update_pmag_tables()        
        self.panel = wx.Panel(self)          # make the Panel
        self.Main_Frame()                   # build the main frame
        self.create_menu()                  # create manu bar
        self.Zij_picker()
        self.Zij_zoom()
        self.arrow_keys()
        self.Bind(wx.EVT_CLOSE, self.on_menu_exit)
        #self.get_previous_interpretation() # get interpretations from pmag_specimens.txt
        FIRST_RUN=False
        self.close_warning=False


    def Main_Frame(self):
        """ Build main frame of panel: buttons, etc.
            choose the first specimen and display data
        """
        #GUI width is 200+100*5+100*5=1202
        #GUI hieght is 640
        
        dw, dh = wx.DisplaySize() 
        w, h = self.GetSize()
        #print 'diplay', dw, dh
        #print "gui", w, h
        r1=dw/1210.
        r2=dw/640.
        
        #if  dw>w:
        self.GUI_RESOLUTION=min(r1,r2,1.3)
        #print "gui resolution 2"
        #self.GUI_RESOLUTION=float(self.preferences['gui_resolution'])/100
        #----------------------------------------------------------------------                     
        # initialize first specimen in list as current specimen
        #----------------------------------------------------------------------                     
        try:
            self.s=str(self.specimens[0])
        except:
            self.s=""
        try:
            self.sample=self.Data_hierarchy['sample_of_specimen'][self.s]
        except:
            self.sample=""
        try:
            self.site=self.Data_hierarchy['site_of_specimen'][self.s]
        except:
            self.site=""
        #print "self.sample=self.Data_hierarchy['sample_of_specimen'][self.s]",self.Data_hierarchy['sample_of_specimen'][self.s]
        #print ":self.site=self.Data_hierarchy['site_of_specimen'][self.s]",self.Data_hierarchy['site_of_specimen'][self.s]
        #print "first specimen is"
        #print self.s
        #print self.specimens
        #----------------------------------------------------------------------                     
        # Create Figures and FigCanvas objects. 
        #----------------------------------------------------------------------                     
        #
        self.fig1 = Figure((5.*self.GUI_RESOLUTION, 5.*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas1 = FigCanvas(self.panel, -1, self.fig1)
        self.toolbar1 = NavigationToolbar(self.canvas1)
        self.toolbar1.Hide()
        #self.fig1.text(0.01,0.98,"Zijderveld plot",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        
        self.fig2 = Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.specimen_eqarea_net = self.fig2.add_subplot(111)  
        self.draw_net(self.specimen_eqarea_net)        
        self.specimen_eqarea = self.fig2.add_axes(self.specimen_eqarea_net.get_position(), frameon=False,axisbg='None')
        self.specimen_eqarea_interpretation = self.fig2.add_axes(self.specimen_eqarea_net.get_position(), frameon=False,axisbg='None')
        self.specimen_eqarea_interpretation.axes.set_aspect('equal')
        self.specimen_eqarea_interpretation.axis('off')
        self.canvas2 = FigCanvas(self.panel, -1, self.fig2)

        self.fig3 = Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas3 = FigCanvas(self.panel, -1, self.fig3)

        self.fig4 = Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas4 = FigCanvas(self.panel, -1, self.fig4)

        # make axes of the figures
        #self.zijplot = self.fig1.add_axes([0.1,0.1,0.8,0.8])
        #self.specimen_eqarea = self.fig2.add_subplot(111)
        #self.m_plot = self.fig3.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')
        #self.m_plot_interpretation = self.fig3.add_axes(self.m_plot.get_position(), frameon=False,axisbg='None')

        
        #self.high_level_eqarea = self.fig4.add_subplot(111)
        
          
        
                    
        self.high_level_eqarea_net = self.fig4.add_subplot(111)
        self.draw_net(self.high_level_eqarea_net)        
        self.high_level_eqarea = self.fig4.add_axes(self.high_level_eqarea_net.get_position(), frameon=False,axisbg='None')
        self.high_level_eqarea_interpretation = self.fig4.add_axes(self.high_level_eqarea_net.get_position(), frameon=False,axisbg='None')
        self.high_level_eqarea_interpretation.axis('equal')
        self.high_level_eqarea_interpretation.axis('off')


        #----------------------------------------------------------------------                     
        #  set font size and style
        #----------------------------------------------------------------------                     

        #font1 = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Comic Sans MS')
        # FONT_RATIO=self.GUI_RESOLUTION+(self.GUI_RESOLUTION-1)*5
        FONT_RATIO=1
        font1 = wx.Font(9+FONT_RATIO, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        # GUI headers
        font2 = wx.Font(12+min(1,FONT_RATIO), wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        font3 = wx.Font(11+FONT_RATIO, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(10+FONT_RATIO)        

        #----------------------------------------------------------------------                     
        # Create text_box for presenting the measurements
        #----------------------------------------------------------------------                     

        #self.logger = wx.TextCtrl(self.panel, id=-1, size=(200*self.GUI_RESOLUTION,300*self.GUI_RESOLUTION), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.logger = wx.ListCtrl(self.panel, -1, size=(200*self.GUI_RESOLUTION,300*self.GUI_RESOLUTION),style=wx.LC_REPORT)
        #print "res",self.GUI_RESOLUTION
        self.logger.SetFont(font1)
        self.logger.InsertColumn(0, 'i',width=25*self.GUI_RESOLUTION)
        self.logger.InsertColumn(1, 'Step',width=25*self.GUI_RESOLUTION)
        self.logger.InsertColumn(2, 'Tr',width=35*self.GUI_RESOLUTION)
        self.logger.InsertColumn(3, 'Dec',width=35*self.GUI_RESOLUTION)
        self.logger.InsertColumn(4, 'Inc',width=35*self.GUI_RESOLUTION)
        self.logger.InsertColumn(5, 'M',width=45*self.GUI_RESOLUTION) 
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnClick_listctrl, self.logger) 
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK,self.OnRightClickListctrl,self.logger) 
        #list, -1, self.RightClickCb )
        #EVT_LIST_ITEM_RIGHT_CLICK( list, -1, self.RightClickCb ) 
        #----------------------------------------------------------------------                     
        #  select specimen box
        #----------------------------------------------------------------------                     

        self.box_sizer_select_specimen = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY), wx.VERTICAL )

        # Combo-box with a list of specimen
        #self.specimens_box = wx.ComboBox(self.panel, -1, self.s, (250*self.GUI_RESOLUTION, 25), wx.DefaultSize,self.specimens, wx.CB_DROPDOWN,name="specimen")
        self.specimens_box = wx.ComboBox(self.panel, -1, value=self.s,choices=self.specimens, style=wx.CB_DROPDOWN,name="specimen")
        #self.specimens_box.SetFont(font2)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_specimen,self.specimens_box)
        
        # buttons to move forward and backwards from specimens        
        self.nextbutton = wx.Button(self.panel, id=-1, label='next',size=(75*self.GUI_RESOLUTION, 25))#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.Bind(wx.EVT_BUTTON, self.on_next_button, self.nextbutton)
        self.nextbutton.SetFont(font2)
        
        self.prevbutton = wx.Button(self.panel, id=-1, label='previous',size=(75*self.GUI_RESOLUTION, 25))#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.prevbutton.SetFont(font2)
        self.Bind(wx.EVT_BUTTON, self.on_prev_button, self.prevbutton)
        
        select_specimen_window = wx.GridSizer(1, 2, 5, 10)
        select_specimen_window.AddMany( [(self.prevbutton, wx.ALIGN_LEFT),
            (self.nextbutton, wx.ALIGN_LEFT)])



        #----------------------------------------------------------------------                     
        #  select coordinate box
        #----------------------------------------------------------------------                     
        # stopped here
        #self.coordinates_box = wx.ComboBox(self.panel, -1, 'specimen', (350*self.GUI_RESOLUTION, 25), wx.DefaultSize,['specimen','geographic','tilt-corrected'], wx.CB_DROPDOWN,name="coordinates")
        self.coordinates_box = wx.ComboBox(self.panel, -1, choices=['specimen','geographic','tilt-corrected'], value='specimen',style=wx.CB_DROPDOWN,name="coordinates")
        #self.coordinates_box.SetFont(font2)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_coordinates,self.coordinates_box)
        #self.box_sizer_select_coordinate.Add(self.coordinates_box, 0, wx.TOP, 0 )        
        #self.orthogonal_box = wx.ComboBox(self.panel, -1, 'X=NRM dec',(350*self.GUI_RESOLUTION, 25), wx.DefaultSize,['X=NRM dec','X=East','X=North','X=best fit line dec'], wx.CB_DROPDOWN,name="orthogonal_plot")
        self.orthogonal_box = wx.ComboBox(self.panel, -1, value='X=NRM dec', choices=['X=NRM dec','X=East','X=North','X=best fit line dec'], style=wx.CB_DROPDOWN,name="orthogonal_plot")
        #self.orthogonal_box.SetFont(font2)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_orthogonal_box,self.orthogonal_box)

        self.box_sizer_select_specimen.Add(wx.StaticText(self.panel,label="specimen:",style=wx.TE_CENTER))        
        self.box_sizer_select_specimen.Add(self.specimens_box, 0, wx.TOP, 0 )        
        self.box_sizer_select_specimen.Add(select_specimen_window, 0, wx.TOP, 4 )        
        self.box_sizer_select_specimen.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
        self.box_sizer_select_specimen.Add(wx.StaticText(self.panel,label="coordinate system:",style=wx.TE_CENTER))        
        self.box_sizer_select_specimen.Add(self.coordinates_box, 0, wx.TOP, 4 )        
        self.box_sizer_select_specimen.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
        self.box_sizer_select_specimen.Add(wx.StaticText(self.panel,label="Zijderveld plot:",style=wx.TE_CENTER))        
        self.box_sizer_select_specimen.Add(self.orthogonal_box, 0, wx.TOP, 4 )        

        #----------------------------------------------------------------------                     
        #  select bounds box
        #----------------------------------------------------------------------                     

        self.T_list=[]
        
        self.box_sizer_select_bounds = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"bounds" ), wx.VERTICAL )
        #self.tmin_box = wx.ComboBox(self.panel, -1 ,size=(100*self.GUI_RESOLUTION, 25),choices=self.T_list, style=wx.CB_DROPDOWN)
        self.tmin_box = wx.ComboBox(self.panel, -1 ,size=(100*self.GUI_RESOLUTION, 25),choices=self.T_list, style=wx.CB_DROPDOWN)
        #self.tmin_box.SetFont(font2)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_PCA_parameters,self.tmin_box)

        #self.tmax_box = wx.ComboBox(self.panel, -1 ,size=(100*self.GUI_RESOLUTION, 25),choices=self.T_list, style=wx.CB_DROPDOWN)
        self.tmax_box = wx.ComboBox(self.panel, -1 ,size=(100*self.GUI_RESOLUTION, 25),choices=self.T_list, style=wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_PCA_parameters,self.tmax_box)

        select_temp_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 0)
        select_temp_window.AddMany( [(self.tmin_box, wx.ALIGN_LEFT),
            (self.tmax_box, wx.ALIGN_LEFT)])
        self.box_sizer_select_bounds.Add(select_temp_window, 0, wx.ALIGN_LEFT, 3.5 )        
        

        #----------------------------------------------------------------------                     
        #  save/delete box
        #----------------------------------------------------------------------                     

        self.box_sizer_save = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"" ), wx.HORIZONTAL )

        # save/delete interpretation buttons
        self.save_interpretation_button = wx.Button(self.panel, id=-1, label='save',size=(75*self.GUI_RESOLUTION,25))#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.save_interpretation_button.SetFont(font2)
        self.delete_interpretation_button = wx.Button(self.panel, id=-1, label='delete',size=(75*self.GUI_RESOLUTION,25))#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.delete_interpretation_button.SetFont(font2)
        self.Bind(wx.EVT_BUTTON, self.on_save_interpretation_button, self.save_interpretation_button)
        self.Bind(wx.EVT_BUTTON, self.on_delete_interpretation_button, self.delete_interpretation_button)
        
        save_delete_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        save_delete_window.AddMany( [(self.save_interpretation_button, wx.ALIGN_LEFT),
            (self.delete_interpretation_button, wx.ALIGN_LEFT)])
        self.box_sizer_save.Add(save_delete_window, 0, wx.TOP, 5.5 )        
        

        #----------------------------------------------------------------------                     
        # Specimen interpretation window 
        #----------------------------------------------------------------------                     
        self.box_sizer_specimen = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"specimen mean type"  ), wx.HORIZONTAL )                        
#        self.PCA_type_box = wx.ComboBox(self.panel, -1, 'line', size=(100*self.GUI_RESOLUTION, 25),choices=['line','line-anchored','line-with-origin','plane','Fisher'], style=wx.CB_DROPDOWN,name="coordinates")
        self.PCA_type_box = wx.ComboBox(self.panel, -1, size=(130*self.GUI_RESOLUTION, 25), value='line',choices=['line','line-anchored','line-with-origin','plane','Fisher'], style=wx.CB_DROPDOWN,name="coordinates")
        #self.tmin_box = wx.ComboBox(self.panel, -1 ,size=(100*self.GUI_RESOLUTION, 25),choices=self.T_list, style=wx.CB_DROPDOWN)

        #self.PCA_type_box.SetFont(font2)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_PCA_parameters,self.PCA_type_box)

        specimen_stat_type_window = wx.GridSizer(2, 1, 0, 19*self.GUI_RESOLUTION)
        specimen_stat_type_window.AddMany( [(wx.StaticText(self.panel,label="\n ",style=wx.TE_CENTER), wx.ALIGN_LEFT),
            (self.PCA_type_box, wx.ALIGN_LEFT)])
        self.box_sizer_specimen.Add( specimen_stat_type_window, 0, wx.ALIGN_LEFT, 0 )        
 
        self.box_sizer_specimen_stat = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"specimen mean statistics"  ), wx.HORIZONTAL )                        
               
        for parameter in ['dec','inc','n','mad','dang','alpha95']:
            COMMAND="self.%s_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))"%parameter
            exec COMMAND
            COMMAND="self.%s_window.SetBackgroundColour(wx.WHITE)"%parameter
            exec COMMAND
            COMMAND="self.%s_window.SetFont(font2)"%parameter
            exec COMMAND

        specimen_stat_window = wx.GridSizer(2, 6, 0, 15*self.GUI_RESOLUTION)
        specimen_stat_window.AddMany( [(wx.StaticText(self.panel,label="\ndec",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="\ninc",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="\nn",style=wx.TE_CENTER),wx.EXPAND),
            (wx.StaticText(self.panel,label="\nmad",style=wx.TE_CENTER),wx.EXPAND),
            #(wx.StaticText(self.panel,label="\nmad-anc",style=wx.TE_CENTER),wx.EXPAND),
            (wx.StaticText(self.panel,label="\ndang",style=wx.TE_CENTER),wx.TE_CENTER),
            (wx.StaticText(self.panel,label="\na95",style=wx.TE_CENTER),wx.TE_CENTER),
            (self.dec_window, wx.EXPAND),
            (self.inc_window, wx.EXPAND) ,
            (self.n_window, wx.EXPAND) ,
            (self.mad_window, wx.EXPAND),
            #(self.mad_anc_window, wx.EXPAND),
            (self.dang_window, wx.EXPAND),
            (self.alpha95_window, wx.EXPAND)])
        self.box_sizer_specimen_stat.Add( specimen_stat_window, 0, wx.ALIGN_LEFT, 0 )

        #----------------------------------------------------------------------                     
        # High level mean window 
        #----------------------------------------------------------------------                     
        self.box_sizer_high_level = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"higher level mean"  ), wx.HORIZONTAL )                        
        #self.level_box = wx.ComboBox(self.panel, -1, 'site', (100*self.GUI_RESOLUTION, 25), wx.DefaultSize,['sample','site','location','study'], wx.CB_DROPDOWN,name="high_level")
        self.level_box = wx.ComboBox(self.panel, -1, size=(100*self.GUI_RESOLUTION, 25),value='site',  choices=['sample','site','location','study'], style=wx.CB_DROPDOWN,name="high_level")
        #self.level_box.SetFont(font2)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_higher_level,self.level_box)

        self.level_names = wx.ComboBox(self.panel, -1,size=(100*self.GUI_RESOLUTION, 25), value=self.site,choices=self.sites, style=wx.CB_DROPDOWN,name="high_level_names")
        #self.level_names.SetFont(font2)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_level_name,self.level_names)


        #self.show_box = wx.ComboBox(self.panel, -1, 'specimens', (100*self.GUI_RESOLUTION, 25), wx.DefaultSize,['specimens','samples','sites','sites-VGP'], wx.CB_DROPDOWN,name="high_elements")
        self.show_box = wx.ComboBox(self.panel, -1, size=(100*self.GUI_RESOLUTION, 25), value='specimens', choices=['specimens','samples','sites','sites-VGP'], style=wx.CB_DROPDOWN,name="high_elements")
        #self.show_box.SetFont(font2)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_show_box,self.show_box)

        #self.mean_type_box = wx.ComboBox(self.panel, -1, 'None', (100*self.GUI_RESOLUTION, 25), wx.DefaultSize,['Fisher','Fisher by polarity','Bingham','None'], wx.CB_DROPDOWN,name="high_type")
        self.mean_type_box = wx.ComboBox(self.panel, -1, size=(120*self.GUI_RESOLUTION, 25), value='None', choices=['Fisher','Fisher by polarity','Bingham','None'], style=wx.CB_DROPDOWN,name="high_type")
        #self.mean_type_box.SetFont(font2)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_mean_type_box,self.mean_type_box)

                
        high_level_window = wx.GridSizer(2, 3, 0*self.GUI_RESOLUTION, 2*self.GUI_RESOLUTION)
        high_level_window.AddMany( [(self.level_box, wx.ALIGN_LEFT),
            (wx.StaticText(self.panel,label="\nshow",style=wx.TE_CENTER), wx.ALIGN_LEFT),
            (wx.StaticText(self.panel,label="\nmean",style=wx.TE_CENTER), wx.ALIGN_LEFT),
            (self.level_names, wx.ALIGN_LEFT),
            (self.show_box, wx.ALIGN_LEFT),
            (self.mean_type_box,wx.ALIGN_LEFT)])
        self.box_sizer_high_level.Add( high_level_window, 0, wx.ALIGN_LEFT, 0 )
                       
        #----------------------------------------------------------------------                     
        # High level text box
        #----------------------------------------------------------------------                     

        self.box_sizer_high_level_text = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,""  ), wx.HORIZONTAL )                        
        self.high_level_text_box = wx.TextCtrl(self.panel, id=-1, size=(220*self.GUI_RESOLUTION,210*self.GUI_RESOLUTION), style=wx.TE_MULTILINE | wx.TE_READONLY )
        self.high_level_text_box.SetFont(font1)
        self.box_sizer_high_level_text.Add(self.high_level_text_box, 0, wx.ALIGN_LEFT, 0 )                                                               
        #----------------------------------------------------------------------                     
        # Design the panel
        #----------------------------------------------------------------------

        
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox1.AddSpacer(10)

        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_select_bounds,flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_save,flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_specimen, flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_specimen_stat, flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_high_level, flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)

        vbox2a=wx.BoxSizer(wx.VERTICAL)
        vbox2a.Add(self.box_sizer_select_specimen,flag=wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND,border=8)
        vbox2a.Add(self.logger,flag=wx.ALIGN_TOP,border=8)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.AddSpacer(2)      
        hbox2.Add(vbox2a,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)        
        hbox2.Add(self.canvas1,flag=wx.ALIGN_CENTER_HORIZONTAL,border=8)

        vbox2 = wx.BoxSizer(wx.VERTICAL)        
        vbox2.Add(self.canvas2,flag=wx.ALIGN_LEFT,border=8)
        vbox2.Add(self.canvas3,flag=wx.ALIGN_LEFT,border=8)
        #vbox2.Add(

        vbox3 = wx.BoxSizer(wx.VERTICAL)        
        vbox3.Add(self.canvas4,flag=wx.ALIGN_LEFT|wx.ALIGN_TOP,border=8)
        vbox3.Add(self.box_sizer_high_level_text,flag=wx.ALIGN_CENTER_VERTICAL,border=8)
       
        hbox2.Add(vbox2,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)
        hbox2.Add(vbox3,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)


        vbox1.Add(hbox1, flag=wx.ALIGN_LEFT)#, border=10)
        vbox1.Add(hbox2, flag=wx.LEFT)#, border=10)

        self.panel.SetSizer(vbox1)
        vbox1.Fit(self)

        self.GUI_SIZE = self.GetSize()
        #print "self.GUI_SIZE",self.GUI_SIZE
        # Draw figures and add  text
        #try:
        #self.draw_figure(self.s)        # draw the figures
        #self.Add_text(self.s)           # write measurement data to text box
        #except:
        #    pass
        
        # get previous interpretations from spmag tables
        self.update_pmag_tables()
        # Draw figures and add  text
        try:
            self.update_selection()
        except:
            pass


    #----------------------------------------------------------------------
    # Arrow keys control
    #----------------------------------------------------------------------

    def arrow_keys(self):
        self.panel.Bind(wx.EVT_CHAR, self.onCharEvent)

    def onCharEvent(self, event):
        keycode = event.GetKeyCode()
        #controlDown = event.CmdDown()
        #altDown = event.AltDown()
        #shiftDown = event.ShiftDown()
 
        if keycode == wx.WXK_RIGHT or keycode == wx.WXK_NUMPAD_RIGHT or keycode == wx.WXK_WINDOWS_RIGHT:
            #print "you pressed the right!"
            self.on_next_button(None)
        elif keycode == wx.WXK_LEFT or keycode == wx.WXK_NUMPAD_LEFT or keycode == wx.WXK_WINDOWS_LEFT:
            #print "you pressed the right!"
            self.on_prev_button(None)
        event.Skip()

    #----------------------------------------------------------------------
    # zooming into zijderveld
    #----------------------------------------------------------------------

    def Zij_zoom(self):
        #cursur_entry_zij=self.canvas1.mpl_connect('axes_enter_event', self.on_enter_zij_fig_new) 
        cursur_entry_zij=self.canvas1.mpl_connect('axes_enter_event', self.on_enter_zij_fig) 
        cursur_leave_zij=self.canvas1.mpl_connect('axes_leave_event', self.on_leave_zij_fig)

    def on_enter_zij_fig_new(self,event):
        #self.toolbar1.zoom()        
        self.curser_in_zij_figure=True
        self.canvas2.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        cid3=self.canvas1.mpl_connect('button_press_event', self.onclick_z_11)
        cid4=self.canvas1.mpl_connect('button_release_event', self.onclick_z_22)


    def onclick_z_11(self,event):
        #if self.curser_in_zij_figure:
        self.tmp_x_press=event.xdata
        self.tmp_y_press=event.ydata
        
    def onclick_z_22(self,event):
        self.tmp_x_release=event.xdata
        self.tmp_y_release=event.ydata
        if abs(self.tmp_x_press-self.tmp_x_release)<0.05 and abs(self.tmp_y_press-self.tmp_y_release)<0.05:
                self.zijplot.set_xlim(xmin=self.zij_xlim_initial[0],xmax=self.zij_xlim_initial[1])
                self.zijplot.set_ylim(ymin=self.zij_ylim_initial[0],ymax=self.zij_ylim_initial[1])
                self.canvas1.draw()



    def on_leave_zij_fig (self,event):
        self.canvas1.mpl_disconnect(self.cid3)
        self.canvas1.mpl_disconnect(self.cid4)
        self.canvas1.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        self.curser_in_zij_figure=False
                
                                                
    def on_enter_zij_fig(self,event):
        #AX=gca(label='zig_orig')
        #print AX
        self.fig1.sca(self.zijplot)
        self.curser_in_zij_figure=True
        self.canvas1.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        cid3=self.canvas1.mpl_connect('button_press_event', self.onclick_z_1)
        cid4=self.canvas1.mpl_connect('button_release_event', self.onclick_z_2)

    def onclick_z_1(self,event):
        if self.curser_in_zij_figure:
            self.tmp3_x=event.xdata
            self.tmp3_y=event.ydata
        
    def onclick_z_2(self,event):
        self.canvas1.mpl_connect('axes_leave_event', self.on_leave_zij_fig)
        if self.curser_in_zij_figure:
            self.tmp4_x=event.xdata
            self.tmp4_y=event.ydata
            try:
                delta_x=abs(self.tmp3_x - self.tmp4_x )
                delta_y=abs(self.tmp3_y - self.tmp4_y )
            except:
                return

            if self.tmp3_x < self.tmp4_x and self.tmp3_y > self.tmp4_y:
                self.zijplot.set_xlim(xmin=self.tmp3_x,xmax=self.tmp4_x)
                self.zijplot.set_ylim(ymin=self.tmp4_y,ymax=self.tmp3_y)
            else:
                self.zijplot.set_xlim(xmin=self.zij_xlim_initial[0],xmax=self.zij_xlim_initial[1])
                self.zijplot.set_ylim(ymin=self.zij_ylim_initial[0],ymax=self.zij_ylim_initial[1])
            
            self.canvas1.draw()                        
            #if self.tmp3_x < self.tmp4_x and self.tmp3_y > self.tmp4_y and delta_x >0.05 and delta_y >0.05:
            #    self.zijplot.set_xlim(xmin=self.tmp3_x,xmax=self.tmp4_x)
            #    self.zijplot.set_ylim(ymin=self.tmp4_y,ymax=self.tmp3_y)
            #elif delta_x < 0.05 and delta_y < 0.05:
            #    return
            #else:
            #    self.zijplot.set_xlim(xmin=self.zij_xlim_initial[0],xmax=self.zij_xlim_initial[1])
            #    self.zijplot.set_ylim(ymin=self.zij_ylim_initial[0],ymax=self.zij_ylim_initial[1])
            #self.canvas1.draw()
        else:
            return

    #----------------------------------------------------------------------
    # Picking bounds from Zijderveld plot
    #----------------------------------------------------------------------

    def Zij_picker(self):
       self.canvas1.mpl_connect('pick_event', self.onpick)
       #self.canvas1.mpl_connect('pick_event', self.onpick())
        
    def onpick(self,event):
        self.second_click=time.time()
        try:
            if self.second_click-self.first_click > 1:
                self.first_click=self.second_click
                return
        except:
            self.first_click= self.second_click
            return     
        index = event.ind[0]
        #print "index",index

        # delete previose interpretation on screen
        if len(self.zijplot.collections)>0:
             self.zijplot.collections=[] # scatter green plots 
        if self.green_line_plot:
             del self.zijplot.lines[-1] # green line
             del self.zijplot.lines[-1]# green line
             self.green_line_plot=False

        # clear selection in measurement window
        for item in range(self.logger.GetItemCount()):
            self.logger.SetItemBackgroundColour(item,"WHITE")
            self.logger.Select(item, on=0)

        # clear equal area plot        
        self.specimen_eqarea_interpretation.clear()   # equal area
        self.mplot_interpretation.clear() # M / M0
                
        tmin_index,tmax_index="",""
        if str(self.tmin_box.GetValue())!="":
            tmin_index=self.tmin_box.GetSelection()
        if str(self.tmax_box.GetValue())!="":
            tmax_index=self.tmax_box.GetSelection()

        
        # set slection in        
        if tmin_index !="" and tmax_index =="":
            if index<tmin_index:
                self.tmin_box.SetSelection(index)
                self.tmax_box.SetSelection(tmin_index)
            else:
                self.tmax_box.SetSelection(index)
            self.logger.Select(index, on=0)
            self.get_new_PCA_parameters(-1)
            
        elif tmin_index =="" and tmax_index !="":
            if index>tmax_index:
                self.tmin_box.SetSelection(tmax_index)
                self.tmax_box.SetSelection(index)
            else:
                self.tmin_box.SetSelection(index)
            self.logger.Select(index, on=0)
            self.get_new_PCA_parameters(-1)
        else:
            if int(index) > (self.logger.GetItemCount())/2.:
                self.tmin_box.SetValue("")
                self.tmax_box.SetSelection(int(index))
            else:
                self.tmin_box.SetSelection(int(index))
                self.tmax_box.SetValue("")

            self.logger.Select(index, on=1)            
            self.zijplot.scatter([self.CART_rot[:,0][index]],[-1* self.CART_rot[:,1][index]],marker='o',s=40,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)
            self.zijplot.scatter([self.CART_rot[:,0][index]],[-1* self.CART_rot[:,2][index]],marker='s',s=50,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)

            #self.mplot_interpretation.scatter([self.Data[self.s]['zijdblock'][index][0]],[self.Data[self.s]['zijdblock'][index][3]/self.Data[self.s]['zijdblock'][0][3]],marker='o',s=30,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)
        self.canvas1.draw()
        self.canvas2.draw()
        self.canvas3.draw()
        
    #----------------------------------------------------------------------
    # Draw plots
    #----------------------------------------------------------------------
       
        
    def draw_figure(self,s):
        
        #-----------------------------------------------------------
        #  initialization
        #-----------------------------------------------------------
        #start_time=time.time() 
        self.s=s
        
        if self.orthogonal_box.GetValue()=="X=East":
            self.ORTHO_PLOT_TYPE='E-W'
        elif self.orthogonal_box.GetValue()=="X=North":
            self.ORTHO_PLOT_TYPE='N-S'
        elif self.orthogonal_box.GetValue()=="X=best fit line dec":
            self.ORTHO_PLOT_TYPE='PCA_dec'
        else:
            self.ORTHO_PLOT_TYPE='ZIJ'            
        if self.COORDINATE_SYSTEM=='geographic':
            #self.CART_rot=self.Data[self.s]['zij_rotated_geo']
            self.zij=array(self.Data[self.s]['zdata_geo'])
            self.zijblock=self.Data[self.s]['zijdblock_geo']
        elif self.COORDINATE_SYSTEM=='tilt-corrected':
            #self.CART_rot=self.Data[self.s]['zij_rotated_tilt']
            self.zij=array(self.Data[self.s]['zdata_tilt'])        
            self.zijblock=self.Data[self.s]['zijdblock_tilt']
        else:
            #self.CART_rot=self.Data[self.s]['zij_rotated']
            self.zij=array(self.Data[self.s]['zdata'])        
            self.zijblock=self.Data[self.s]['zijdblock']

        if self.COORDINATE_SYSTEM=='geographic':
            if self.ORTHO_PLOT_TYPE=='N-S':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_geo'],0.)
            elif self.ORTHO_PLOT_TYPE=='E-W':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_geo'],90.)
            elif self.ORTHO_PLOT_TYPE=='PCA_dec':
                if 'specimen_dec' in self.pars.keys() and type(self.pars['specimen_dec'])!=str:
                    self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_geo'],self.pars['specimen_dec'])
                else:
                    self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_geo'],pmag.cart2dir(self.Data[self.s]['zdata_geo'][0])[0])
            else:
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_geo'],pmag.cart2dir(self.Data[self.s]['zdata_geo'][0])[0])
                 
        elif self.COORDINATE_SYSTEM=='tilt-corrected':
            if self.ORTHO_PLOT_TYPE=='N-S':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_tilt'],0.)
            elif self.ORTHO_PLOT_TYPE=='E-W':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_tilt'],90)
            elif self.ORTHO_PLOT_TYPE=='PCA_dec':
                if 'specimen_dec' in self.pars.keys() and type(self.pars['specimen_dec'])!=str:
                    self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_tilt'],self.pars['specimen_dec'])
                else:
                    self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_tilt'],pmag.cart2dir(self.Data[self.s]['zdata_tilt'][0])[0])
            else:
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_tilt'],pmag.cart2dir(self.Data[self.s]['zdata_tilt'][0])[0])
        else:
            if self.ORTHO_PLOT_TYPE=='N-S':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata'],0.)
            elif self.ORTHO_PLOT_TYPE=='E-W':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata'],90)
            elif self.ORTHO_PLOT_TYPE=='PCA_dec':
                if 'specimen_dec' in self.pars.keys() and type(self.pars['specimen_dec'])!=str:
                    print self.pars['specimen_dec']
                    self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata'],self.pars['specimen_dec'])
                else:#Zijderveld
                    self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata'],pmag.cart2dir(self.Data[self.s]['zdata'][0])[0])

            else:#Zijderveld
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata'],pmag.cart2dir(self.Data[self.s]['zdata'][0])[0])


        self.zij_norm=array([row/sqrt(sum(row**2)) for row in self.zij])
        
        #-----------------------------------------------------------         
        # remove bad data from plotting:     
        #-----------------------------------------------------------
        
        self.CART_rot_good=[]   
        self.CART_rot_bad=[]   
        for i in range(len(list(self.CART_rot))):
            if self.Data[self.s]['measurement_flag'][i]=='g':
                self.CART_rot_good.append(list(self.CART_rot[i]))
            else:
                self.CART_rot_bad.append(list(self.CART_rot[i]))
        
        self.CART_rot_good= array(self.CART_rot_good)
        self.CART_rot_bad= array(self.CART_rot_bad)
            
        
        #-----------------------------------------------------------
        # Draw Zij plot
        #-----------------------------------------------------------
        self.fig1.clf()
        self.zijplot = self.fig1.add_axes([0.1,0.1,0.8,0.8],frameon=False, axisbg='None',label='zig_orig',zorder=0)
        self.zijplot.clear()
        self.zijplot.axis('equal')
        self.zijplot.xaxis.set_visible(False)
        self.zijplot.yaxis.set_visible(False)
        self.green_line_plot=False
        #self.zijplot_interpretation = self.fig1.add_axes(self.zijplot.get_position(), frameon=False,axisbg='None',label='zij_interpretation',zorder=1)
        #self.zijplot_interpretation.clear()
        #self.zijplot_interpretation.axis('equal')
        #self.zijplot_interpretation.xaxis.set_visible(False)
        #self.zijplot_interpretation.yaxis.set_visible(False)
        
        self.MS=6*self.GUI_RESOLUTION;self.dec_MEC='k';self.dec_MFC='r'; self.inc_MEC='k';self.inc_MFC='b'
        self.zijdblock_steps=self.Data[self.s]['zijdblock_steps']
        self.vds=self.Data[self.s]['vds']

        #self.zijplot.scatter(self.CART_rot[:,0],-1* self.CART_rot[:,1],marker="o",s=self.MS,c='r',clip_on=False,picker=True)
        #self.zijplot.plot(self.CART_rot[:,0],-1* self.CART_rot[:,1],'ro-',mfc=self.dec_MFC,mec=self.dec_MEC,markersize=self.MS,clip_on=False,picker=True)  #x,y or N,E
        #self.zijplot.plot(self.CART_rot[:,0],-1 * self.CART_rot[:,2],'bs-',mfc=self.inc_MFC,mec=self.inc_MEC,markersize=self.MS,clip_on=False,picker=True)   #x-z or N,D
        #self.zijplot.plot(self.CART_rot_clean[:,0],-1* self.CART_rot_clean[:,1],'r-')  #x,y or N,E
        #self.zijplot.plot(self.CART_rot_clean[:,0],-1 * self.CART_rot_clean[:,2],'b-')   #x-z or N,D
        #self.zijplot.scatter(self.CART_rot[:,0],-1* self.CART_rot[:,1],marker="o",s=20,c='r',clip_on=False,picker=True)

        self.zijplot.plot(self.CART_rot_good[:,0],-1* self.CART_rot_good[:,1],'ro-',mfc=self.dec_MFC,mec=self.dec_MEC,markersize=self.MS,clip_on=False,picker=True)  #x,y or N,E
        self.zijplot.plot(self.CART_rot_good[:,0],-1 * self.CART_rot_good[:,2],'bs-',mfc=self.inc_MFC,mec=self.inc_MEC,markersize=self.MS,clip_on=False,picker=True)   #x-z or N,D
        
        if len(self.CART_rot_bad)>0:
            for i in range(len( self.CART_rot_bad)):
                self.zijplot.plot(self.CART_rot_bad[:,0][i],-1* self.CART_rot_bad[:,1][i],'o',mfc='None',mec=self.dec_MEC,markersize=self.MS,clip_on=False,picker=False)  #x,y or N,E
                self.zijplot.plot(self.CART_rot_bad[:,0][i],-1 * self.CART_rot_bad[:,2][i],'s',mfc='None',mec=self.inc_MEC,markersize=self.MS,clip_on=False,picker=False)   #x-z or N,D
        
        #self.zijplot.axis('off')
        #last_cart_1=array([self.CART_rot[0][0],self.CART_rot[0][1]])
        #last_cart_2=array([self.CART_rot[0][0],self.CART_rot[0][2]])
        #K_diff=0
        if self.preferences['show_Zij_treatments'] :
            for i in range(len(self.zijdblock_steps)):
                if int(self.preferences['show_Zij_treatments_steps']) !=1:
                    if i!=0  and (i+1)%int(self.preferences['show_Zij_treatments_steps'])==0:
                        self.zijplot.text(self.CART_rot[i][0],-1*self.CART_rot[i][2],"  %s"%(self.zijdblock_steps[i]),fontsize=10*self.GUI_RESOLUTION,color='gray',ha='left',va='center')   #inc
                else:
                  self.zijplot.text(self.CART_rot[i][0],-1*self.CART_rot[i][2],"  %s"%(self.zijdblock_steps[i]),fontsize=10*self.GUI_RESOLUTION,color='gray',ha='left',va='center')   #inc

        #-----
        xmin, xmax = self.zijplot.get_xlim()
        if xmax <0:
            xmax=0
        if xmin>0:
            xmin=0
        #else:
        #    xmin=xmin+xmin%0.2
        props = dict(color='black', linewidth=1.0, markeredgewidth=0.5)

        xlocs=array(list(arange(0.2,xmax,0.2)) + list(arange(-0.2,xmin,-0.2)))
        if len(xlocs)>0:
            xtickline, = self.zijplot.plot(xlocs, [0]*len(xlocs),linestyle='',marker='+', **props)
            xtickline.set_clip_on(False)
                

        axxline, = self.zijplot.plot([xmin, xmax], [0, 0], **props)
        axxline.set_clip_on(False)
        
        TEXT=""
        if self.COORDINATE_SYSTEM=='specimen':
            self.zijplot.text(xmax,0,' x',fontsize=10,verticalalignment='bottom')
        else:
            if self.ORTHO_PLOT_TYPE=='N-S':
                TEXT=" N"
            elif self.ORTHO_PLOT_TYPE=='E-W':
                TEXT=" E"
            else:
                TEXT=" x"       
            self.zijplot.text(xmax,0,TEXT,fontsize=10,verticalalignment='bottom')



        #-----

        ymin, ymax = self.zijplot.get_ylim()
        if ymax <0:
            ymax=0
        if ymin>0:
            ymin=0
 
        ylocs=array(list(arange(0.2,ymax,0.2)) + list(arange(-0.2,ymin,-0.2)))
        if len(ylocs)>0:
            ytickline, = self.zijplot.plot([0]*len(ylocs),ylocs, linestyle='',marker='+', **props)
            ytickline.set_clip_on(False)
       
        axyline, = self.zijplot.plot([0, 0],[ymin, ymax], **props)
        axyline.set_clip_on(False)

        TEXT1,TEXT2="",""
        if self.COORDINATE_SYSTEM=='specimen':
                TEXT1,TEXT2=" y","      z"  
            #self.zijplot.text(0,ymin,' y,z',fontsize=10,verticalalignment='top')
        else:
            if self.ORTHO_PLOT_TYPE=='N-S':
                TEXT1,TEXT2=" E","     D"
            elif self.ORTHO_PLOT_TYPE=='E-W':
                TEXT1,TEXT2=" S","     D"
            else:
                TEXT1,TEXT2=" y","      z"  
        self.zijplot.text(0,ymin,TEXT1,fontsize=10,color='r',verticalalignment='top')
        self.zijplot.text(0,ymin,'    ,',fontsize=10,color='k',verticalalignment='top')
        self.zijplot.text(0,ymin,TEXT2,fontsize=10,color='b',verticalalignment='top')

        #----

        if self.ORTHO_PLOT_TYPE=='N-S':
            STRING=""
            #STRING1="N-S orthogonal plot"
            self.fig1.text(0.01,0.98,"Zijderveld plot: x = North",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        elif self.ORTHO_PLOT_TYPE=='E-W':
            STRING=""
            #STRING1="E-W orthogonal plot"
            self.fig1.text(0.01,0.98,"Zijderveld plot:: x = East",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        
        elif self.ORTHO_PLOT_TYPE=='PCA_dec':
            self.fig1.text(0.01,0.98,"Zijderveld plot",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
            if 'specimen_dec' in self.pars.keys() and type(self.pars['specimen_dec'])!=str:
                STRING="X-axis rotated to best fit line declination (%.0f); "%(self.pars['specimen_dec'])
            else:
                STRING="X-axis rotated to NRM (%.0f); "%(self.zijblock[0][1])
                
        else:
            self.fig1.text(0.01,0.98,"Zijderveld plot",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
            STRING="X-axis rotated to NRM (%.0f); "%(self.zijblock[0][1])
            #STRING1="Zijderveld plot"
         
        
        STRING=STRING+"NRM=%.2e "%(self.zijblock[0][3])+ '$Am^2$'        
        self.fig1.text(0.01,0.95,STRING,{'family':'Arial', 'fontsize':8*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        
        xmin, xmax = self.zijplot.get_xlim()
        ymin, ymax = self.zijplot.get_ylim()

        
        self.zij_xlim_initial=(xmin, xmax)
        self.zij_ylim_initial=(ymin, ymax )
        
                
        self.canvas1.draw()
        #-----------------------------------------------------------
        # specimen equal area
        #-----------------------------------------------------------

        self.specimen_eqarea.clear()
        self.specimen_eqarea_interpretation.clear()
        self.specimen_eqarea.text(-1.2,1.15,"specimen: %s"%self.s,{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })


        x_eq=array([row[0] for row in self.zij_norm])
        y_eq=array([row[1] for row in self.zij_norm])
        z_eq=abs(array([row[2] for row in self.zij_norm]))
        
        # remove bad data from plotting:     
        x_eq_good,y_eq_good,z_eq_good=[],[],[]
        x_eq_bad,y_eq_bad,z_eq_bad=[],[],[]
        for i in range(len(list(self.zij_norm))):
            if self.Data[self.s]['measurement_flag'][i]=='g':
                x_eq_good.append(self.zij_norm[i][0])
                y_eq_good.append(self.zij_norm[i][1])
                z_eq_good.append(abs(self.zij_norm[i][2]))
            else:
                x_eq_bad.append(self.zij_norm[i][0])
                y_eq_bad.append(self.zij_norm[i][1])
                z_eq_bad.append(abs(self.zij_norm[i][2]))
        
        x_eq_good,y_eq_good,z_eq_good=array(x_eq_good),array(y_eq_good),array(z_eq_good)
        x_eq_bad,y_eq_bad,z_eq_bad=array(x_eq_bad),array(y_eq_bad),array(z_eq_bad) 
        
        R_good=array(sqrt(1-z_eq_good)/sqrt(x_eq_good**2+y_eq_good**2)) # from Collinson 1983
        R_bad=array(sqrt(1-z_eq_bad)/sqrt(x_eq_bad**2+y_eq_bad**2)) # from Collinson 1983

        eqarea_data_x_good=y_eq_good*R_good
        eqarea_data_y_good=x_eq_good*R_good

        eqarea_data_x_bad=y_eq_bad*R_bad
        eqarea_data_y_bad=x_eq_bad*R_bad
        
        self.specimen_eqarea.plot(eqarea_data_x_good,eqarea_data_y_good,lw=0.5,color='gray')#,zorder=0)

        #--------------------
        # scatter plot
        x_eq_dn,y_eq_dn,z_eq_dn,eq_dn_temperatures=[],[],[],[]
        x_eq_dn=array([row[0] for row in self.zij_norm if row[2]>0])
        y_eq_dn=array([row[1] for row in self.zij_norm if row[2]>0])
        z_eq_dn=abs(array([row[2] for row in self.zij_norm if row[2]>0]))

        
        if len(x_eq_dn)>0:
            R=array(sqrt(1-z_eq_dn)/sqrt(x_eq_dn**2+y_eq_dn**2)) # from Collinson 1983
            eqarea_data_x_dn=y_eq_dn*R
            eqarea_data_y_dn=x_eq_dn*R
            self.specimen_eqarea.scatter([eqarea_data_x_dn],[eqarea_data_y_dn],marker='o',edgecolor='black', facecolor='gray',s=15*self.GUI_RESOLUTION,lw=1,clip_on=False)
                    
           

        x_eq_up,y_eq_up,z_eq_up=[],[],[]
        x_eq_up=array([row[0] for row in self.zij_norm if row[2]<=0])
        y_eq_up=array([row[1] for row in self.zij_norm if row[2]<=0])
        z_eq_up=abs(array([row[2] for row in self.zij_norm if row[2]<=0]))
        if len(x_eq_up)>0:
            R=array(sqrt(1-z_eq_up)/sqrt(x_eq_up**2+y_eq_up**2)) # from Collinson 1983
            eqarea_data_x_up=y_eq_up*R
            eqarea_data_y_up=x_eq_up*R
            self.specimen_eqarea.scatter([eqarea_data_x_up],[eqarea_data_y_up],marker='o',edgecolor='black', facecolor='white',s=15*self.GUI_RESOLUTION,lw=1,clip_on=False)        
        
        #self.preferences['show_eqarea_treatments']=True
        if self.preferences['show_eqarea_treatments']:
            for i in range(len(self.zijdblock_steps)):
                self.specimen_eqarea.text(eqarea_data_x[i],eqarea_data_y[i],"%.1f"%float(self.zijdblock_steps[i]),fontsize=8*self.GUI_RESOLUTION,color="0.5")
        

        
        # add line to show the direction of the x axis in the Zijderveld plot     
        
        if str(self.orthogonal_box.GetValue()) in ["X=best fit line dec","X=NRM dec"]:
            XY=[]
            if str(self.orthogonal_box.GetValue())=="X=NRM dec":
                dec_zij=self.zijblock[0][1]
                XY=pmag.dimap(dec_zij,0)
            if str(self.orthogonal_box.GetValue())=="X=best fit line dec":
                if 'specimen_dec' in self.pars.keys() and  type(self.pars['specimen_dec'])!=str:
                    dec_zij=self.pars['specimen_dec']
                    XY=pmag.dimap(dec_zij,0)
            if XY!=[]:
                self.specimen_eqarea.plot([0,XY[0]],[0,XY[1]],ls='-',c='gray',lw=0.5)#,zorder=0)
                
                
            
        self.specimen_eqarea.set_xlim(-1., 1.)        
        self.specimen_eqarea.set_ylim(-1., 1.)        
        self.specimen_eqarea.axes.set_aspect('equal')
        self.specimen_eqarea.axis('off')
        
        self.specimen_eqarea_interpretation.set_xlim(-1., 1.)
        self.specimen_eqarea_interpretation.set_ylim(-1., 1.)        
        self.specimen_eqarea_interpretation.axes.set_aspect('equal')
        self.specimen_eqarea_interpretation.axis('off')
        
        self.canvas2.draw()

        #start_time_2=time.time() 
        #runtime_sec2 = start_time_2 - start_time_1
        #print "-I- draw eqarea figures is", runtime_sec2,"seconds"

        #-----------------------------------------------------------
        # Draw M/M0 plot ( or NLT data on the same area in the GUI)
        #-----------------------------------------------------------

        self.fig3.clf()
        self.fig3.text(0.02,0.96,'M/M0',{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        self.mplot = self.fig3.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')        
        self.mplot_interpretation = self.fig3.add_axes(self.mplot.get_position(), frameon=False,axisbg='None')
        self.mplot_interpretation.xaxis.set_visible(False)
        self.mplot_interpretation.yaxis.set_visible(False)
        
        #fig, ax1 = plt.subplots()
        #print "measurement_step_unit",self.Data[self.s]['measurement_step_unit'] 
        if self.Data[self.s]['measurement_step_unit'] =="mT:C" or self.Data[self.s]['measurement_step_unit'] =="C:mT":
            thermal_x,thermal_y=[],[]
            thermal_x_bad,thermal_y_bad=[],[]
            af_x,af_y=[],[]
            af_x_bad,af_y_bad=[],[]
            for i in range(len(self.Data[self.s]['zijdblock'])):
                # bad point
                if self.Data[self.s]['measurement_flag'][i]=='b':
                    
                    if step=="0":
                        thermal_x_bad.append(self.Data[self.s]['zijdblock'][i][0])
                        af_x_bad.append(self.Data[self.s]['zijdblock'][i][0])
                        thermal_y_bad.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                        af_y_bad.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                    elif "C" in step:
                        thermal_x_bad.append(self.Data[self.s]['zijdblock'][i][0])
                        thermal_y_bad.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                    elif "T" in step:
                        af_x_bad.append(self.Data[self.s]['zijdblock'][i][0])
                        af_y_bad.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                    else:
                        continue                            
                    
                else:    
                    step=self.Data[self.s]['zijdblock_steps'][i]
                    if step=="0":
                        thermal_x.append(self.Data[self.s]['zijdblock'][i][0])
                        af_x.append(self.Data[self.s]['zijdblock'][i][0])
                        thermal_y.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                        af_y.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                    elif "C" in step:
                        thermal_x.append(self.Data[self.s]['zijdblock'][i][0])
                        thermal_y.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                    elif "T" in step:
                        af_x.append(self.Data[self.s]['zijdblock'][i][0])
                        af_y.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                    else:
                        continue                            
            
            self.mplot.plot(thermal_x, thermal_y, 'ro-',markersize=5*self.GUI_RESOLUTION,lw=1,clip_on=False)
            for i in range(len(thermal_x_bad)):
                self.mplot.plot([thermal_x_bad[i]], [thermal_y_bad[i]],'o',mfc='None',mec='k',markersize=self.MS,clip_on=False)
                     
            self.mplot.set_xlabel('Thermal (C)',color='r')
            for tl in self.mplot.get_xticklabels():
                tl.set_color('r')
            
            
            ax2 = self.mplot.twiny()
            ax2.plot(af_x, af_y, 'bo-',markersize=5*self.GUI_RESOLUTION,lw=1,clip_on=False)
            for i in range(len(af_x_bad)):
                ax2.plot([af_x_bad[i]], [af_y_bad[i]],'o',mfc='None',mec='k',markersize=self.MS,clip_on=False)
            
            ax2.set_xlabel('AF (mT)',color='b')
            for tl in ax2.get_xticklabels():
                tl.set_color('b')

            self.mplot.tick_params(axis='both', which='major', labelsize=7)
            ax2.tick_params(axis='both', which='major', labelsize=7)
            self.mplot.spines["right"].set_visible(False)
            ax2.spines["right"].set_visible(False)
            self.mplot.get_xaxis().tick_bottom()
            self.mplot.get_yaxis().tick_left()
            self.mplot.set_ylabel("M / NRM0",fontsize=8*self.GUI_RESOLUTION)
        
        else:
            
 
        
                            
            #self.mplot = self.fig3.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')        
            self.mplot.clear()
            x_data,y_data=[],[]
            x_data_bad,y_data_bad=[],[]
            for i in range(len(self.Data[self.s]['zijdblock'])):
                # bad point
                if self.Data[self.s]['measurement_flag'][i]=='b':
                    x_data_bad.append(self.Data[self.s]['zijdblock'][i][0])
                    y_data_bad.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])                    
                else:
                    x_data.append(self.Data[self.s]['zijdblock'][i][0])
                    y_data.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
    
            self.mplot = self.fig3.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')        
            self.mplot.clear()
            self.mplot.plot(x_data,y_data,'bo-',mec='0.2',markersize=5*self.GUI_RESOLUTION,lw=1,clip_on=False)
            for i in range(len(x_data_bad)):
                self.mplot.plot([x_data_bad[i]], [y_data_bad[i]],'o',mfc='None',mec='k',markersize=self.MS,clip_on=False)
            self.mplot.set_xlabel("Treatment",fontsize=8*self.GUI_RESOLUTION)                  
            self.mplot.set_ylabel("M / NRM$_0$",fontsize=8*self.GUI_RESOLUTION)
            try:
                self.mplot.tick_params(axis='both', which='major', labelsize=7)
            except:
                pass
            #self.mplot.tick_params(axis='x', which='major', labelsize=8)          
            self.mplot.spines["right"].set_visible(False)
            self.mplot.spines["top"].set_visible(False)
            self.mplot.get_xaxis().tick_bottom()
            self.mplot.get_yaxis().tick_left()
        
        #xt=xticks()

        self.canvas3.draw()
        #start_time_3=time.time() 
        #runtime_sec3 = start_time_3 - start_time_2
        #print "-I- draw M_M0 figures is", runtime_sec3,"seconds"

        #-----------------------------------------------------------
        # high level equal area
        #-----------------------------------------------------------
        self.plot_higher_levels_data()
        #self.fig4.clf()
        #what_is_it=self.level_box.GetValue()
        #self.fig4.text(0.02,0.96,what_is_it,{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        #self.high_level_eqarea = self.fig4.add_subplot(111)        
        ## draw_net        
        #self.draw_net(self.high_level_eqarea)
        #self.canvas4.draw()

        self.canvas4.draw()
        #start_time_4=time.time() 
        #runtime_sec4 = start_time_4 - start_time_3
        #print "-I- draw high level figures is", runtime_sec4,"seconds"

    def draw_net_new(self,ax):
        FIG.clear()
        eq=FIG
        host = fig.add_subplot(111)
        eq.axis((-1,1,-1,1))
        eq.axis('off')
        theta=arange(0.,2*pi,2*pi/1000)
        eq.plot(cos(theta),sin(theta),'k',clip_on=False,lw=1)
        #eq.vlines((0,0),(0.9,-0.9),(1.0,-1.0),'k')
        #eq.hlines((0,0),(0.9,-0.9),(1.0,-1.0),'k')
        #eq.plot([0.0],[0.0],'+k')

        Xsym,Ysym=[],[]
        for I in range(10,100,10):
            XY=pmag.dimap(0.,I)
            Xsym.append(XY[0])
            Ysym.append(XY[1])
        for I in range(10,90,10):
            XY=pmag.dimap(90.,I)
            Xsym.append(XY[0])
            Ysym.append(XY[1])
        for I in range(10,90,10):
            XY=pmag.dimap(180.,I)
            Xsym.append(XY[0])
            Ysym.append(XY[1])
        for I in range(10,90,10):
            XY=pmag.dimap(270.,I)
            Xsym.append(XY[0])
            Ysym.append(XY[1])
        eq.plot(Xsym,Ysym,'k+',clip_on=False,mew=0.5)
        for D in range(0,360,10):
            Xtick,Ytick=[],[]
            for I in range(4):
                XY=pmag.dimap(D,I)
                Xtick.append(XY[0])
                Ytick.append(XY[1])
            eq.plot(Xtick,Ytick,'k',clip_on=False,lw=0.5)
        eq.axes.set_aspect('equal')


    def draw_net(self,FIG):
        FIG.clear()
        eq=FIG
        eq.axis((-1,1,-1,1))
        eq.axis('off')
        theta=arange(0.,2*pi,2*pi/1000)
        eq.plot(cos(theta),sin(theta),'k',clip_on=False,lw=1)
        #eq.vlines((0,0),(0.9,-0.9),(1.0,-1.0),'k')
        #eq.hlines((0,0),(0.9,-0.9),(1.0,-1.0),'k')
        #eq.plot([0.0],[0.0],'+k')

        Xsym,Ysym=[],[]
        for I in range(10,100,10):
            XY=pmag.dimap(0.,I)
            Xsym.append(XY[0])
            Ysym.append(XY[1])
        for I in range(10,90,10):
            XY=pmag.dimap(90.,I)
            Xsym.append(XY[0])
            Ysym.append(XY[1])
        for I in range(10,90,10):
            XY=pmag.dimap(180.,I)
            Xsym.append(XY[0])
            Ysym.append(XY[1])
        for I in range(10,90,10):
            XY=pmag.dimap(270.,I)
            Xsym.append(XY[0])
            Ysym.append(XY[1])
        eq.plot(Xsym,Ysym,'k+',clip_on=False,mew=0.5)
        for D in range(0,360,10):
            Xtick,Ytick=[],[]
            for I in range(4):
                XY=pmag.dimap(D,I)
                Xtick.append(XY[0])
                Ytick.append(XY[1])
            eq.plot(Xtick,Ytick,'k',clip_on=False,lw=0.5)
        eq.axes.set_aspect('equal')

    #----------------------------------------------------------------------
    # add text to text box
    #----------------------------------------------------------------------
       
        
    def Add_text(self,s):
        
      """ Add measurement data lines to the text window.
      """

      if self.COORDINATE_SYSTEM=='geographic':
          zijdblock=self.Data[self.s]['zijdblock_geo']
      elif self.COORDINATE_SYSTEM=='tilt-corrected':
          zijdblock=self.Data[self.s]['zijdblock_tilt']
      else:
          zijdblock=self.Data[self.s]['zijdblock']
            
          
      TEXT=""
      self.logger.DeleteAllItems()
      for i in range(len(zijdblock)):
          lab_treatment=self.Data[self.s]['zijdblock_lab_treatments'][i]
          Step=""
          methods=lab_treatment.split('-')
          if "NO" in methods:
              Step="N "
          elif "T" in  methods or "LT" in methods:
              Step="T"
          elif "AF" in  methods:
              Step="AF"             
          Tr=zijdblock[i][0]
          Dec=zijdblock[i][1]
          Inc=zijdblock[i][2]
          Int=zijdblock[i][3]
          self.logger.InsertStringItem(i, "%i"%i)
          self.logger.SetStringItem(i, 1, Step)
          self.logger.SetStringItem(i, 2, "%.1f"%Tr)
          self.logger.SetStringItem(i, 3, "%.1f"%Dec)
          self.logger.SetStringItem(i, 4, "%.1f"%Inc)
          self.logger.SetStringItem(i, 5, "%.2e"%Int)
          self.logger.SetItemBackgroundColour(i,"WHITE")
          if self.Data[self.s]['measurement_flag'][i]=='b':
            self.logger.SetItemBackgroundColour(i,"YELLOW")
             
    #----------------------------------------------------------------------
      
    def onSelect_specimen(self, event):
        """ update figures and text when a new specimen is selected
        """        
        self.s=str(self.specimens_box.GetValue())
        #self.pars=self.Data[self.s]['pars'] 
        self.update_selection()

    #----------------------------------------------------------------------

    def onSelect_coordinates(self, event):
        old=self.COORDINATE_SYSTEM
        new=self.coordinates_box.GetValue()
        if new=='geographic' and len(self.Data[self.s]['zijdblock_geo'])==0:
            self.coordinates_box.SetStringSelection(old)
        elif new=='tilt-corrected' and len(self.Data[self.s]['zijdblock_tilt'])==0:
            self.coordinates_box.SetStringSelection(old)
        else:
            self.COORDINATE_SYSTEM=new
        #self.update_selection()

        coordinate_system=self.COORDINATE_SYSTEM
        self.update_selection()
        #self.clear_boxes() 
        #self.Add_text(self.s)
        #self.draw_figure(self.s)
        #if self.pars!={} and 'measurement_step_min' in self.pars.keys() and 'measurement_step_max' in self.pars.keys() :
        #    tmin= "%.0f"%(float(self.pars['measurement_step_min']))       
        #    tmax= "%.0f"%(float(self.pars['measurement_step_max']))
        #    self.tmin_box.SetStringSelection(tmin)
        #    self.tmax_box.SetStringSelection(tmax)  
        #    calculation_type=self.pars['calculation_type']       
        ## calcuate again self.pars and update the figures and the statistics tables.                                
        #    self.pars=self.get_PCA_parameters(self.s,tmin,tmax,coordinate_system,calculation_type)                         
        #    self.update_GUI_with_new_interpretation()

    #----------------------------------------------------------------------

    def onSelect_orthogonal_box(self, event):
        self.clear_boxes() 
        self.Add_text(self.s)
        self.draw_figure(self.s)
        self.update_selection()
        if self.pars!={}:
            #tmin= "%.0f"%(float(self.pars['measurement_step_min']))       
            #tmax= "%.0f"%(float(self.pars['measurement_step_max']))
            #calculation_type=self.pars['calculation_type']       
        # calcuate again self.pars and update the figures and the statistics tables.                                
            #self.pars=self.get_PCA_parameters(self.s,tmin,tmax,coordinate_system,calculation_type)                         
            self.update_GUI_with_new_interpretation()
              
    #----------------------------------------------------------------------

    def on_next_button(self,event):
        
      """ update figures and text when a next button is selected
      """
      #del self.Data[self.s]['pars']
      #self.Data[self.s]['pars']={}
                 
              
      index=self.specimens.index(self.s)
      if index==len(self.specimens)-1:
        index=0
      else:
        index+=1
      self.s=str(self.specimens[index])
      self.specimens_box.SetStringSelection(str(self.s))      
      self.update_selection()
      
    #----------------------------------------------------------------------

    def on_prev_button(self,event):
      """ update figures and text when a next button is selected
      """
      #if 'saved' not in self.Data[self.s]['pars'] or self.Data[self.s]['pars']['saved']!= True:
      #        del self.Data[self.s]['pars']
      #        self.Data[self.s]['pars']={}
      ##       # return to last saved interpretation if exist
      #if 'er_specimen_name' in self.last_saved_pars.keys() and self.last_saved_pars['er_specimen_name']==self.s:
      #           self.Data[self.s]['pars']={}
      #           for key in self.last_saved_pars.keys():
      #               self.Data[self.s]['pars'][key]=self.last_saved_pars[key]
      #           self.last_saved_pars={}
                                
      index=self.specimens.index(self.s)
      if index==0: index=len(self.specimens)
      index-=1
      self.s=str(self.specimens[index])
      self.specimens_box.SetStringSelection(str(self.s))
      self.update_selection()

    #----------------------------------------------------------------------

                
    def update_selection(self):
        """ 
        update display (figures, text boxes and statistics windows) with a new selection of specimen 
        """

        self.clear_boxes() 

        #--------------------------
        # check if the coordinate system in the window exists (if not change to "specimen" coordinate system)
        #--------------------------
        
        coordinate_system=self.coordinates_box.GetValue()
        if coordinate_system=='tilt-corrected' and len(self.Data[self.s]['zijdblock_tilt'])==0:
            self.coordinates_box.SetStringSelection('geographic')
        coordinate_system=self.coordinates_box.GetValue()            
        if coordinate_system=='geographic' and len(self.Data[self.s]['zijdblock_geo'])==0:
            self.coordinates_box.SetStringSelection("specimen")
        self.COORDINATE_SYSTEM=str(self.coordinates_box.GetValue())                           



        #--------------------------                
        # updtaes treatment list
        #--------------------------
        #treatments=[]
        #for i in range(len(self.Data[self.s]['zijdblock'])):
        #    treatments.append("%.1f"%(self.Data[self.s]['zijdblock'][i][0]))
        self.T_list=self.Data[self.s]['zijdblock_steps']
        self.tmin_box.SetItems(self.T_list)
        self.tmax_box.SetItems(self.T_list)
        self.tmin_box.SetStringSelection("")
        self.tmax_box.SetStringSelection("")

        #start_time_4=time.time()        
        #runtime_sec = start_time_4 - start_time_3
        #print "-I- update treatment is", runtime_sec,"seconds"

        #--------------------------
        # update high level boxes and figures (if needed)
        #--------------------------

        higher_level=self.level_box.GetValue()
        old_string=self.level_names.GetValue()
        new_string=old_string
        if higher_level=='sample':
            new_string=self.Data_hierarchy['sample_of_specimen'][self.s]
        if higher_level=='site':
            new_string=self.Data_hierarchy['site_of_specimen'][self.s]
        if higher_level=='location':
            new_string=self.Data_hierarchy['location_of_specimen'][self.s]
        self.level_names.SetValue(new_string)

        #--------------------------
        # check if specimen's interpretation is saved 
        #--------------------------
        found_interpretation=False
        if self.s in self.pmag_results_data['specimens'].keys() and found_interpretation==False:
          for dirtype in self.pmag_results_data['specimens'][self.s].keys():
              if 'measurement_step_min' in self.pmag_results_data['specimens'][self.s][dirtype].keys()\
              and 'measurement_step_max' in self.pmag_results_data['specimens'][self.s][dirtype].keys():
                  # updatet min/tmax windows
                  measurement_step_min= float(self.pmag_results_data['specimens'][self.s][dirtype]['measurement_step_min'])
                  measurement_step_max= float(self.pmag_results_data['specimens'][self.s][dirtype]['measurement_step_max'])
                  if measurement_step_min==0:
                      tmin="0"
                  elif self.Data[self.s]['measurement_step_unit']=="C":
                      tmin="%.0fC"%(measurement_step_min)
                  elif self.Data[self.s]['measurement_step_unit']=="mT":
                      tmin="%.1fmT"%(measurement_step_min)
                  else: # combimned experiment T:AF
                    if "%.0fC"%(measurement_step_min) in self.Data[self.s]['zijdblock_steps']:
                        tmin="%.0fC"%(measurement_step_min)
                    elif "%.1fmT"%(measurement_step_min) in self.Data[self.s]['zijdblock_steps']:
                        tmin="%.1fmT"%(measurement_step_min)
                    else:
                        continue
                        
                  if self.Data[self.s]['measurement_step_unit']=="C":
                      tmax="%.0fC"%(measurement_step_max)
                  elif self.Data[self.s]['measurement_step_unit']=="mT":
                      tmax="%.1fmT"%(measurement_step_max)
                  else: # combimned experiment T:AF
                    if "%.0fC"%(measurement_step_max) in self.Data[self.s]['zijdblock_steps']:
                        tmax="%.0fC"%(measurement_step_max)
                    elif "%.1fmT"%(measurement_step_max) in self.Data[self.s]['zijdblock_steps']:
                        tmax="%.1fmT"%(measurement_step_max)
                    else:
                        continue
                                                                    
                  self.tmin_box.SetStringSelection(tmin)
                  self.tmax_box.SetStringSelection(tmax)  
                  
                  # update calculation type windows                                
                  calculation_type=self.pmag_results_data['specimens'][self.s][dirtype]['calculation_type']
                  if calculation_type=="DE-BFL": PCA_type="line"
                  elif calculation_type=="DE-BFL-A": PCA_type="line-anchored"
                  elif calculation_type=="DE-BFL-O": PCA_type="line-with-origin"
                  elif calculation_type=="DE-FM": PCA_type="Fisher"
                  elif calculation_type=="DE-BFP": PCA_type="plane"
                  self.PCA_type_box.SetStringSelection(PCA_type)
                  
                  found_interpretation=True
                  


        # measurements text box
        self.Add_text(self.s)
        
        # calcuate again self.pars and update the figures and the statistics tables. 
        coordinate_system=self.COORDINATE_SYSTEM
        if found_interpretation: 
            self.pars=self.get_PCA_parameters(self.s,tmin,tmax,coordinate_system,calculation_type) 
            self.draw_figure(self.s)
            self.update_GUI_with_new_interpretation()
        else:
            self.draw_figure(self.s)
            

        # draw the figures        
    
        if  found_interpretation:                   
            self.mean_type_box.SetStringSelection(calculation_type)
        self.plot_higher_levels_data()

        # check if high level interpretation exists 
        #--------------------------
        dirtype=str(self.coordinates_box.GetValue())
        if dirtype=='specimen':dirtype='DA-DIR'
        if dirtype=='geographic':dirtype='DA-DIR-GEO'
        if dirtype=='tilt-corrected':dirtype='DA-DIR-TILT'
        if str(self.level_box.GetValue())=='sample': high_level_type='samples' 
        if str(self.level_box.GetValue())=='site': high_level_type='sites' 
        if str(self.level_box.GetValue())=='location': high_level_type='locations' 
        if str(self.level_box.GetValue())=='study': high_level_type='study' 
        high_level_name=str(self.level_names.GetValue())
        elements_type=str(self.show_box.GetValue())
        calculation_type="None"
        self.high_level_text_box.SetValue("")
        if high_level_name in self.high_level_means[high_level_type].keys():
            if dirtype in self.high_level_means[high_level_type][high_level_name].keys():
                mpars=self.high_level_means[high_level_type][high_level_name][dirtype]
                calculation_type= mpars['calculation_type'] 
                self.show_higher_levels_pars(mpars)

        
        #start_time_6=time.time()        
        #runtime_sec = start_time_6 - start_time_5
        #print "-I- higher level plot", runtime_sec,"seconds"

        #start_time_7=time.time()        
        #runtime_sec = start_time_7 - start_time
        #print "-I- total:", runtime_sec,"seconds"
        # clear all boxes


    #----------------------------------------------------------------------


    def get_DIR(self, WD=None):
        """ Choose a working directory dialog
        """
        if "-WD" in sys.argv and FIRST_RUN:
            ind=sys.argv.index('-WD')
            self.WD=sys.argv[ind+1]            
            #self.WD=os.getcwd()+"/"
 
        elif not WD:   
            dialog = wx.DirDialog(None, "Choose a directory:",defaultPath = self.currentDirectory ,style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
            ok = dialog.ShowModal()
            if ok == wx.ID_OK:
                self.WD=dialog.GetPath()
            else:
                self.WD = os.getcwd()
            dialog.Destroy()
        os.chdir(self.WD)
        self.WD=os.getcwd()
        self.magic_file=os.path.join(self.WD, "magic_measurements.txt")
        self.GUI_log=open(os.path.join(self.WD, "demag_gui.log"),'w')
        self.GUI_log.write("start gui\n")
        self.GUI_log.close()
        self.GUI_log=open(os.path.join(self.WD, "demag_gui.log"),'a')

    #----------------------------------------------------------------------


    def OnClick_listctrl(self,event):

        for item in range(self.logger.GetItemCount()):
            self.logger.SetItemBackgroundColour(item,"WHITE")
          
        index=int(event.GetText())
        tmin_index,tmax_index="",""
        
        if str(self.tmin_box.GetValue())!="":
            tmin_index=self.tmin_box.GetSelection()
        if str(self.tmax_box.GetValue())!="":
            tmax_index=self.tmax_box.GetSelection()

        if tmin_index !="" and tmax_index =="":
            if index<tmin_index:
                self.tmin_box.SetSelection(index)
                self.tmax_box.SetSelection(tmin_index)
            else:
                self.tmax_box.SetSelection(index)
            self.logger.Select(index, on=0)
            self.get_new_PCA_parameters(-1)
            
        elif tmin_index =="" and tmax_index !="":
            if index>tmax_index:
                self.tmin_box.SetSelection(tmax_index)
                self.tmax_box.SetSelection(index)
            else:
                self.tmin_box.SetSelection(index)
            self.logger.Select(index, on=0)
            self.get_new_PCA_parameters(-1)
            
        else:
            if int(index) > (self.logger.GetItemCount())/2.:
                self.tmin_box.SetValue("")
                self.tmax_box.SetSelection(int(index))
            else:
                self.tmin_box.SetSelection(int(index))
                self.tmax_box.SetValue("")
            return
          
             
    def OnRightClickListctrl(self,event):
        '''
        right click on the listctrl opens a popup menu for 
        changing the measurement line from "g" to "b"
        
        If there is  change, the program rewrirte magic_measurements.txt a
        and reads it again.
        '''
        #print "dialogs"
        #y_offset=300*self.GUI_RESOLUTION
        position=event.GetPosition()
        position[1]=position[1]+300*self.GUI_RESOLUTION
        #print position
        g_index =event.GetIndex()

        GBpopupmenu=self.PopupMenu(demag_dialogs.GBPopupMenu(self.Data,self.magic_file,self.mag_meas_data,self.s,g_index,position))
        #print "OK"
        #self.write_good_bad_magic_measurements()
        # write the corrected magic_measurements.txt

    #def write_good_bad_magic_measurements(self):
    #    print "write_good_bad_magic_measurements"
    #    # read magic_measurements.txt
    #    #meas_data,file_type=pmag.magic_read(self.magic_file)
    #    
    #    pmag.magic_write("kaka.txt",self.mag_meas_data,"magic_measurements")
    #    
    #    # read again the data from the new file
    #    self.Data,self.Data_hierarchy=self.get_data()
         
        # delete interpretation
        TXT="measurement good or bad data is saved in magic_measurements.txt file"
        dlg = wx.MessageDialog(self, caption="Saved",message=TXT,style=wx.OK)
        result = dlg.ShowModal()
        if result == wx.ID_OK:            
            dlg.Destroy()

        if 'specimens' in self.pmag_results_data.keys() and str(self.s) in self.pmag_results_data['specimens'].keys():
            del(self.pmag_results_data['specimens'][str(self.s)])

        self.pars={}
        # read again the data
        self.Data,self.Data_hierarchy=self.get_data() #
        self.calculate_higher_levels_data()
        self.update_pmag_tables()
        self.update_selection()
        

    #----------------------------------------------------------------------

    def get_new_PCA_parameters(self,event):
        
        """
        calcualte statisics when temperatures are selected
        or PCA type is changes
        """

        #remember the last saved interpretation

        #if "saved" in self.pars.keys():
        #    if self.pars['saved']:
        #        self.last_saved_pars={}
        #        for key in self.pars.keys():
        #            self.last_saved_pars[key]=self.pars[key]
        #self.pars['saved']=False
        tmin=str(self.tmin_box.GetValue())
        #index_min=self.tmin_box.GetSelection()
        tmax=str(self.tmax_box.GetValue())
        #index_max=self.tmax_box.GetSelection()
        if tmin=="" or tmax=="":
            return
       
        if (self.T_list.index(tmax) <= self.T_list.index(tmin)):
            return 
               
        #if (index_2-indparsex_1)+1 >= self.acceptance_criteria['specimen_int_n']:
        PCA_type=self.PCA_type_box.GetValue()
        if PCA_type=="line":calculation_type="DE-BFL"
        elif PCA_type=="line-anchored":calculation_type="DE-BFL-A"
        elif PCA_type=="line-with-origin":calculation_type="DE-BFL-O"
        elif PCA_type=="Fisher":calculation_type="DE-FM"
        elif PCA_type=="plane":calculation_type="DE-BFP"
        coordinate_system=self.COORDINATE_SYSTEM
        self.pars=self.get_PCA_parameters(self.s,tmin,tmax,coordinate_system,calculation_type)        
        self.update_GUI_with_new_interpretation()

    #----------------------------------------------------------------------

    def SortOutBadData(self,block_name):
        """
        sort out datpoints marked with 'b' flag
        """
        blockin=self.Data[self.s][block_name]
        blockout=[]
        for i in range(len(blockin)):
            if self.Data[self.s]['measurement_flag'][i]=='g':
               blockout.append( blockin[i])
        return(blockout)
            

    def get_PCA_parameters(self,specimen,tmin,tmax,coordinate_system,calculation_type):
        """
        calcualte statisics 
        """
        beg_pca=self.Data[specimen]['zijdblock_steps'].index(tmin)
        end_pca=self.Data[specimen]['zijdblock_steps'].index(tmax)
        if coordinate_system=='geographic':
            block=self.Data[specimen]['zijdblock_geo']
        elif coordinate_system=='tilt-corrected':
            block=self.Data[specimen]['zijdblock_tilt']
        else:
            block=self.Data[specimen]['zijdblock']
        if  end_pca>  beg_pca and   end_pca - beg_pca >1: 
            mpars=pmag.domean(block,beg_pca,end_pca,calculation_type)
        else:
            mpars={}
        for k in mpars.keys():
            try:
                if math.isnan(float(mpars[k])):
                    mpars[k]=0
            except:
                pass
        if "DE-BFL" in calculation_type and 'specimen_dang' not in mpars.keys():
             mpars['specimen_dang']=0
            
            
        mpars['zijdblock_step_min']=tmin                    
        mpars['zijdblock_step_max']=tmax
                
            

        return(mpars)
 
    #----------------------------------------------------------------------

    def update_GUI_with_new_interpretation(self):
        """
        update statistics boxes and figures with a new interpretatiom
        when selecting new temperature bound
        """
        self.dec_window.SetValue("%.1f"%self.pars['specimen_dec'])
        self.dec_window.SetBackgroundColour(wx.WHITE)
        
        self.inc_window.SetValue("%.1f"%self.pars['specimen_inc'])
        self.inc_window.SetBackgroundColour(wx.WHITE)

        self.n_window.SetValue("%i"%self.pars['specimen_n'])
        self.n_window.SetBackgroundColour(wx.WHITE)

        if 'specimen_mad' in self.pars.keys():
            self.mad_window.SetValue("%.1f"%self.pars['specimen_mad'])
            self.mad_window.SetBackgroundColour(wx.WHITE)
        else:
            self.mad_window.SetValue("")
            self.mad_window.SetBackgroundColour(wx.NullColour)

        if 'specimen_dang' in self.pars.keys() and float(self.pars['specimen_dang'])!=-1:
            self.dang_window.SetValue("%.1f"%self.pars['specimen_dang'])
            self.dang_window.SetBackgroundColour(wx.WHITE)
        else:
            self.dang_window.SetValue("")
            self.dang_window.SetBackgroundColour(wx.NullColour)

        if 'specimen_alpha95' in self.pars.keys() and float(self.pars['specimen_alpha95'])!=-1:
            self.alpha95_window.SetValue("%.1f"%self.pars['specimen_alpha95'])
            self.alpha95_window.SetBackgroundColour(wx.WHITE)
        else:
            self.alpha95_window.SetValue("")
            self.alpha95_window.SetBackgroundColour(wx.NullColour)
        
        if self.orthogonal_box.GetValue()=="X=best fit line dec":                              
            if  'specimen_dec' in self.pars.keys(): 
                self.draw_figure(self.s)
        #else:
        #    self.draw_figure(self.s)         
  
        self.draw_interpretation()

    #----------------------------------------------------------------------
                       
    def draw_interpretation(self):
        PCA_type=self.PCA_type_box.GetValue()
        
        tmin_index=self.Data[self.s]['zijdblock_steps'].index(self.pars['zijdblock_step_min'])
        tmax_index=self.Data[self.s]['zijdblock_steps'].index(self.pars['zijdblock_step_max'])

        # Zijderveld plot
                            
        ymin, ymax = self.zijplot.get_ylim()
        xmin, xmax = self.zijplot.get_xlim()

        #print "1)lines",self.zijplot.lines
        #print "2)collection",self.zijplot.collections
        
        # delete previose interpretation
        if len(self.zijplot.collections)>0:
             self.zijplot.collections=[] # delete scatter green points 
        if self.green_line_plot:
             del self.zijplot.lines[-1] # delete green line
             del self.zijplot.lines[-1]# delete green line
        self.green_line_plot=False
        
        self.zijplot.scatter([self.CART_rot[:,0][tmin_index],self.CART_rot[:,0][tmax_index]],[-1* self.CART_rot[:,1][tmin_index],-1* self.CART_rot[:,1][tmax_index]],marker='o',s=40,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)
        self.zijplot.scatter([self.CART_rot[:,0][tmin_index],self.CART_rot[:,0][tmax_index]],[-1* self.CART_rot[:,2][tmin_index],-1* self.CART_rot[:,2][tmax_index]],marker='s',s=50,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)
        
        if self.pars['calculation_type'] in ['DE-BFL','DE-BFL-A','DE-BFL-O']:
            
            #rotated zijderveld
            if self.COORDINATE_SYSTEM=='geographic':
                first_data=self.Data[self.s]['zdata_geo'][0]
            elif self.COORDINATE_SYSTEM=='tilt-corrected':
                first_data=self.Data[self.s]['zdata_tilt'][0]
            else:
                first_data=self.Data[self.s]['zdata'][0]
            
            if self.ORTHO_PLOT_TYPE=='N-S':
                rotation_declination=0. 
            elif self.ORTHO_PLOT_TYPE=='E-W':
                rotation_declination=90.
            elif self.ORTHO_PLOT_TYPE=='PCA_dec':
                if 'specimen_dec' in self.pars.keys() and type(self.pars['specimen_dec'])!=str:
                    rotation_declination=self.pars['specimen_dec']
                else:
                    rotation_declination=pmag.cart2dir(first_data)[0]            
            else:#Zijderveld
                rotation_declination=pmag.cart2dir(first_data)[0]
                                                                 
            PCA_dir=[self.pars['specimen_dec'],self.pars['specimen_inc'],1]         
            PCA_dir_rotated=[PCA_dir[0]-rotation_declination,PCA_dir[1],1]      
            PCA_CART_rotated=pmag.dir2cart(PCA_dir_rotated)
            
            slop_xy_PCA=-1*PCA_CART_rotated[1]/PCA_CART_rotated[0]
            slop_xz_PCA=-1*PCA_CART_rotated[2]/PCA_CART_rotated[0]
    
            # Center of mass rotated for plotting 
            # (self.CART_rot_good) ignoring the bad points
            CM_x=mean(self.CART_rot_good[:,0][tmin_index:tmax_index+1])
            CM_y=mean(self.CART_rot_good[:,1][tmin_index:tmax_index+1])
            CM_z=mean(self.CART_rot_good[:,2][tmin_index:tmax_index+1])
                    
            # intercpet from the center of mass
            intercept_xy_PCA=-1*CM_y - slop_xy_PCA*CM_x
            intercept_xz_PCA=-1*CM_z - slop_xz_PCA*CM_x
    
            xx=array([0,self.CART_rot_good[:,0][tmin_index]])
            yy=slop_xy_PCA*xx+intercept_xy_PCA
            #self.zijplot_interpretation.plot(xx,yy,'-',color='g',lw=3,alpha=0.5)
            zz=slop_xz_PCA*xx+intercept_xz_PCA
            #self.zijplot_interpretation.plot(xx,zz,'-',color='g',lw=3,alpha=0.5)
            self.zijplot.plot(xx,yy,'-',color='g',lw=3,alpha=0.5,zorder=0)
            self.zijplot.plot(xx,zz,'-',color='g',lw=3,alpha=0.5,zorder=0)
            self.green_line_plot=True  
        self.zijplot.set_xlim(xmin=self.zij_xlim_initial[0],xmax=self.zij_xlim_initial[1])
        self.zijplot.set_ylim(ymin=self.zij_ylim_initial[0],ymax=self.zij_ylim_initial[1])
        self.canvas1.draw()       
    
        # Equal Area plot
        self.specimen_eqarea_interpretation.clear()
        if self.pars['calculation_type']!='DE-BFP':
            CART=pmag.dir2cart([self.pars['specimen_dec'],self.pars['specimen_inc'],1])    
            x=CART[0]
            y=CART[1]
            z=abs(CART[2])
            R=array(sqrt(1-z)/sqrt(x**2+y**2))
            eqarea_x=y*R
            eqarea_y=x*R
    
            if z>0:
                FC='green';EC='0.1'
            else:
                FC='yellow';EC='green'
            self.specimen_eqarea_interpretation.scatter([eqarea_x],[eqarea_y],marker='o',edgecolor=EC, facecolor=FC,s=30,lw=1,clip_on=False)
            self.specimen_eqarea_interpretation.set_xlim(-1., 1.)        
            self.specimen_eqarea_interpretation.set_ylim(-1., 1.)        
            self.specimen_eqarea_interpretation.axes.set_aspect('equal')
            self.specimen_eqarea_interpretation.axis('off')
            self.canvas2.draw()
        
        # draw a best-fit plane
        
        if self.pars['calculation_type']=='DE-BFP':
            
            ymin, ymax = self.specimen_eqarea.get_ylim()
            xmin, xmax = self.specimen_eqarea.get_xlim()
            
            D_c,I_c=pmag.circ(self.pars["specimen_dec"],self.pars["specimen_inc"],90)
            X_c_up,Y_c_up=[],[]
            X_c_d,Y_c_d=[],[]
            for k in range(len(D_c)):
                #print D_c[k],I_c[k]
                XY=pmag.dimap(D_c[k],I_c[k])
                if I_c[k]<0:
                    X_c_up.append(XY[0])
                    Y_c_up.append(XY[1])
                if I_c[k]>0:
                    X_c_d.append(XY[0])
                    Y_c_d.append(XY[1])
            self.specimen_eqarea_interpretation.plot(X_c_d,Y_c_d,'b')
            self.specimen_eqarea_interpretation.plot(X_c_up,Y_c_up,'c')
            
            #self.specimen_eqarea_interpretation.set_xlim(xmin, xmax)
            #self.specimen_eqarea_interpretation.set_ylim(ymin, ymax)           
            self.specimen_eqarea_interpretation.set_xlim(-1., 1.)        
            self.specimen_eqarea_interpretation.set_ylim(-1., 1.)        
            self.specimen_eqarea_interpretation.axes.set_aspect('equal')
            self.specimen_eqarea_interpretation.axis('off')
            self.canvas2.draw()
            
                                        
        # M/M0 plot (only if C or mT - not both)
        if self.Data[self.s]['measurement_step_unit'] !="mT:C" and self.Data[self.s]['measurement_step_unit'] !="C:mT":
            ymin, ymax = self.mplot.get_ylim()
            xmin, xmax = self.mplot.get_xlim()
            self.mplot_interpretation.clear()
            self.mplot_interpretation.scatter([self.Data[self.s]['zijdblock'][tmin_index][0]],[self.Data[self.s]['zijdblock'][tmin_index][3]/self.Data[self.s]['zijdblock'][0][3]],marker='o',s=30,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)
            self.mplot_interpretation.scatter([self.Data[self.s]['zijdblock'][tmax_index][0]],[self.Data[self.s]['zijdblock'][tmax_index][3]/self.Data[self.s]['zijdblock'][0][3]],marker='o',s=30,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)
            self.mplot_interpretation.set_xlim(xmin, xmax)
            self.mplot_interpretation.set_ylim(ymin, ymax)
            self.canvas3.draw()
        
        # logger
        #self.logger.SetBackgroundColour('red')
        for item in range(self.logger.GetItemCount()):
            if item >= tmin_index and item <= tmax_index:
                self.logger.SetItemBackgroundColour(item,"LIGHT BLUE") # gray
            else:
                self.logger.SetItemBackgroundColour(item,"WHITE")
            if self.Data[self.s]['measurement_flag'][item]=='b':
                self.logger.SetItemBackgroundColour(item,"YELLOW")
                
    #----------------------------------------------------------------------

                    
                                
                    
                                                                                                                                                   
    #----------------------------------------------------------------------
                                                                                                                                       
    def on_save_interpretation_button(self,event):

        """
        on the save button
        the interpretation is saved to pmag_results_table data 
        in all coordinate systems
        """
        calculation_type=self.pars['calculation_type']
        tmin_index=str(self.tmin_box.GetSelection())
        tmax_index=str(self.tmax_box.GetSelection())
        tmin=str(self.tmin_box.GetValue())
        tmax=str(self.tmax_box.GetValue())

        self.pmag_results_data['specimens'][self.s]={}
        self.pmag_results_data['specimens'][self.s]['DA-DIR']=self.get_PCA_parameters(self.s,tmin,tmax,'specimen',calculation_type)
        if len(self.Data[self.s]['zijdblock_geo'])>0:      
            self.pmag_results_data['specimens'][self.s]['DA-DIR-GEO']=self.get_PCA_parameters(self.s,tmin,tmax,'geographic',calculation_type)                
        if len(self.Data[self.s]['zijdblock_tilt'])>0:      
            self.pmag_results_data['specimens'][self.s]['DA-DIR-TILT']=self.get_PCA_parameters(self.s,tmin,tmax,'tilt-corrected',calculation_type)                        

        # calculate higher level data
        self.calculate_higher_levels_data()
        #self.plot_higher_levels_data()
        self.update_selection()
        self.close_warning=True
        
    #----------------------------------------------------------------------  
   
    #----------------------------------------------------------------------

    def on_delete_interpretation_button(self,event):
        #self.Data[self.s]['pars']={}
        #for dirtype in ['DA-DIR','DA-DIR-GEO','DA-DIR-TILT']:
        #    if dirtype in self.Data[self.s].keys():
        #        del self.Data[self.s][dirtype]
        
        if 'specimens' in self.pmag_results_data.keys() and str(self.s) in self.pmag_results_data['specimens'].keys():
            del(self.pmag_results_data['specimens'][str(self.s)])
        self.pars={}
        self.calculate_higher_levels_data()
        self.update_selection()
        self.close_warning=True
        return
 
    #----------------------------------------------------------------------
           
    def clear_boxes(self):
        """ Clear all boxes
        """        
        self.tmin_box.Clear()
        self.tmin_box.SetItems(self.T_list)
        self.tmin_box.SetSelection(-1)

        self.tmax_box.Clear()
        self.tmax_box.SetItems(self.T_list)
        self.tmax_box.SetSelection(-1)

        for parameter in ['dec','inc','n','mad','dang','alpha95']:
            COMMAND="self.%s_window.SetValue('')"%parameter
            exec COMMAND
            COMMAND="self.%s_window.SetBackgroundColour(wx.NullColour)"%parameter
            exec COMMAND
            
    #----------------------------------------------------------------------

    def onSelect_mean_type_box(self,event):
        # calculate higher level data
        self.calculate_higher_levels_data()
        self.update_selection()        

        
    #----------------------------------------------------------------------
        
    def onSelect_higher_level(self,event):
       self.UPPER_LEVEL=self.level_box.GetValue() 
       if self.UPPER_LEVEL=='sample':
           self.show_box.SetItems(['specimens'])
           self.show_box.SetStringSelection('specimens')
           self.level_names.SetItems(self.samples)
           self.level_names.SetStringSelection(self.Data_hierarchy['sample_of_specimen'][self.s])
           
       if self.UPPER_LEVEL=='site':
           self.show_box.SetItems(['specimens','samples'])
           if self.show_box.GetValue() not in ['specimens','samples']:
               self.show_box.SetStringSelection('samples')
           self.level_names.SetItems(self.sites)
           self.level_names.SetStringSelection(self.Data_hierarchy['site_of_specimen'][self.s])
       if self.UPPER_LEVEL=='location':
           self.show_box.SetItems(['specimens','samples','sites'])#,'sites VGP'])
           if self.show_box.GetValue() not in ['specimens','samples','sites']:#,'sites VGP']:
               self.show_box.SetStringSelection('sites')
           self.level_names.SetItems(self.locations)
           self.level_names.SetStringSelection(self.Data_hierarchy['location_of_specimen'][self.s])
       if self.UPPER_LEVEL=='study':
           self.show_box.SetItems(['specimens','samples','sites'])#,'sites VGP'])
           if self.show_box.GetValue() not in ['specimens','samples','sites']:#,'sites VGP']:
               self.show_box.SetStringSelection('sites')
           self.level_names.SetItems(['this study'])
           self.level_names.SetStringSelection('this study')
           
       #self.calculate_higher_levels_data()
       self.plot_higher_levels_data()
       self.update_selection()        

    #----------------------------------------------------------------------
        
    def onSelect_level_name(self,event):
       high_level_name=str(self.level_names.GetValue())
       
       if self.level_box.GetValue()=='sample':
           specimen_list=self.Data_hierarchy['samples'][high_level_name]['specimens']
       if self.level_box.GetValue()=='site':
           specimen_list=self.Data_hierarchy['sites'][high_level_name]['specimens']
       if self.level_box.GetValue()=='location':  
           specimen_list=self.Data_hierarchy['locations'][high_level_name]['specimens']
       if self.level_box.GetValue()=='study':
           specimen_list=self.Data_hierarchy['study']['this study']['specimens']
       
       if  self.s not in specimen_list:
           specimen_list.sort()
           self.s=str(specimen_list[0])
           self.specimens_box.SetStringSelection(str(self.s))      
           self.update_selection()
           #self.calculate_higher_levels_data()
           #self.plot_higher_levels_data()
       self.update_selection() 
    #----------------------------------------------------------------------

    def onSelect_show_box(self,event):

        self.calculate_higher_levels_data()
        self.update_selection()
        
        #self.plot_higher_levels_data()
        #self.show_higher_levels_pars(mpars)
           
    #----------------------------------------------------------------------


    def calculate_high_level_mean (self,high_level_type,high_level_name,calculation_type,elements_type):
        # high_level_type:'samples','sites','locations','study'
        # calculation_type: 'Bingham','Fisher','Fisher by polarity'
        # elements_type (what to average):'specimens','samples','sites' (Ron. ToDo alos VGP and maybe locations?) 

        # figure out what level to average,and what elements to average (specimen, samples, sites, vgp)        
        self.high_level_means[high_level_type][high_level_name]={}
        for dirtype in ["DA-DIR","DA-DIR-GEO","DA-DIR-TILT"]:
            if high_level_name not in self.Data_hierarchy[high_level_type].keys():
                continue
                
            elements_list=self.Data_hierarchy[high_level_type][high_level_name][elements_type]
            pars_for_mean=[]              
            for element in elements_list:
                #found_element=False
                if elements_type=='specimens':
                    if element in self.pmag_results_data['specimens'].keys():
                        #print "found element",self.pmag_results_data['specimens'][element]
                        if dirtype in self.pmag_results_data['specimens'][element].keys():
                            pars=self.pmag_results_data['specimens'][element][dirtype]
                            if "calculation_type" in pars.keys() and pars["calculation_type"] == 'DE-BFP':
                                dec,inc,direction_type=pars["specimen_dec"],pars["specimen_inc"],'p'
                            elif "specimen_dec" in pars.keys() and "specimen_inc" in pars.keys():
                                dec,inc,direction_type=pars["specimen_dec"],pars["specimen_inc"],'l'
                            elif "dec" in pars.keys() and "inc" in pars.keys():
                                dec,inc,direction_type=pars["dec"],pars["inc"],'l'
                            else:
                                print "-E- ERROR: cant find mean for element %s"%element
                                continue 
                        else:
                            continue
                    else:
                        continue                                           
                else:
                    if element in self.high_level_means[elements_type].keys():
                        if dirtype in self.high_level_means[elements_type][element].keys():
                            pars=self.high_level_means[elements_type][element][dirtype]
                            if "dec" in pars.keys() and "inc" in pars.keys():
                                dec,inc,direction_type=pars["dec"],pars["inc"],'l'
                            else:
                                print "-E- ERROR: cant find mean for element %s"%element
                                continue 
                        else:
                            continue                               
                            #pars_for_mean.append({'dec':float(dec),'inc':float(inc),'direction_type':direction_type})
                    else:
                        continue
                pars_for_mean.append({'dec':float(dec),'inc':float(inc),'direction_type':direction_type,'element_name':element})
                                                                                                                                                                      
            if len(pars_for_mean)  > 0 and calculation_type !="None":
                self.high_level_means[high_level_type][high_level_name][dirtype]=self.calculate_mean(pars_for_mean,calculation_type)
                
            
                #print "calculate mean for high level",high_level_name,self.high_level_means[high_level_type][high_level_name]
    #----------------------------------------------------------------------

    def calculate_mean(self,pars_for_mean,calculation_type):
        #print "calculate_mean !!"
        #print pars_for_mean,calculation_type
        ''' 
        claculates:
            Fisher mean (lines/planes)
            or Bingham mean
            or Fisher by polarity
        '''
        if len(pars_for_mean)==0:
            return({})
        elif len(pars_for_mean)==1:
            return ({"dec":float(pars_for_mean[0]['dec']),"inc":float(pars_for_mean[0]['inc']),"calculation_type":calculation_type,"n":1})                        
        elif calculation_type =='Bingham':
            data=[]
            for pars in pars_for_mean:
                # ignore great circle
                if 'direction_type' in pars.keys() and 'direction_type'=='p':
                    continue
                else:
                    data.append([pars['dec'],pars['inc']])
            mpars=pmag.dobingham(data)
        elif calculation_type=='Fisher':
            mpars=pmag.dolnp(pars_for_mean,'direction_type')
        elif calculation_type=='Fisher by polarity':
            mpars=pmag.fisher_by_pol(pars_for_mean)
            print "mpars",mpars
        
        # change strigs to floats
        if  calculation_type!='Fisher by polarity':  
            for key in mpars.keys():
                try:
                    mpars[key]=float( mpars[key] )
                except:
                    pass
                                
        else:
            for mode in ['A','B','All']:
                print mode
                for key in mpars[mode].keys():
                    try:
                        mpars[mode][key]=float(mpars[mode][key])
                    except:
                        pass
        mpars['calculation_type']=calculation_type

        return(mpars)
                                                            
                                                                        
    
    def calculate_higher_levels_data(self):

        high_level_type=str(self.level_box.GetValue())
        if high_level_type=='sample':high_level_type='samples'
        if high_level_type=='site':high_level_type='sites'
        if high_level_type=='location':high_level_type='locations'
        high_level_name=str(self.level_names.GetValue())
        calculation_type=str(self.mean_type_box.GetValue())
        elements_type=str(self.show_box.GetValue())
        self.calculate_high_level_mean(high_level_type,high_level_name,calculation_type,elements_type)                
        
                                    

        
                
    def plot_higher_levels_data(self):
       #print " plot_higher_levels_data" 
       
       high_level=self.level_box.GetValue() 
       self.UPPER_LEVEL_NAME=self.level_names.GetValue() 
       self.UPPER_LEVEL_SHOW=self.show_box.GetValue() 
       self.UPPER_LEVEL_MEAN=self.mean_type_box.GetValue() 
       

       #self.fig4.clf()
       self.high_level_eqarea.clear()
       what_is_it=self.level_box.GetValue()+": "+self.level_names.GetValue()
       self.high_level_eqarea.text(-1.2,1.15,what_is_it,{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })

              
       #self.high_level_eqarea_net = self.fig4.add_subplot(111)        
       #self.high_level_eqarea = self.high_level_eqarea_net.twinx()        
       # draw_net        
       #self.draw_net(self.high_level_eqarea)
       #self.canvas4.draw()

       if self.COORDINATE_SYSTEM=="geographic": dirtype='DA-DIR-GEO'
       elif self.COORDINATE_SYSTEM=="tilt-corrected": dirtype='DA-DIR-TILT'
       else: dirtype='DA-DIR'

       if self.level_box.GetValue()=='sample': high_level_type='samples' 
       if self.level_box.GetValue()=='site': high_level_type='sites' 
       if self.level_box.GetValue()=='location': high_level_type='locations' 
       if self.level_box.GetValue()=='study': high_level_type='study' 

       high_level_name=str(self.level_names.GetValue())
       calculation_type=str(self.mean_type_box.GetValue())
       elements_type=str(self.show_box.GetValue())
       
       #print high_level_type,high_level_name,elements_type
       #print "high_level_type",high_level_type
       #print self.Data_hierarchy[high_level_type]
       elements_list=self.Data_hierarchy[high_level_type][high_level_name][elements_type]
       
       # plot elements directions
       for element in elements_list:
            if elements_type=='specimens':
                if element in self.pmag_results_data['specimens'].keys():
                    if dirtype in self.pmag_results_data['specimens'][element].keys():
                        mpars=self.pmag_results_data['specimens'][element][dirtype]
                        self.plot_eqarea_pars(mpars,self.high_level_eqarea)

            else:
                if element in self.high_level_means[elements_type].keys():
                    if dirtype in self.high_level_means[elements_type][element].keys():
                        mpars=self.high_level_means[elements_type][element][dirtype]
                        self.plot_eqarea_pars(mpars,self.high_level_eqarea)
                        
       # plot elements means
       if calculation_type!="None":
           if high_level_name in self.high_level_means[high_level_type].keys():
               if dirtype in self.high_level_means[high_level_type][high_level_name].keys():
                   self.plot_eqarea_mean( self.high_level_means[high_level_type][high_level_name][dirtype],self.high_level_eqarea)
                        
           
       self.high_level_eqarea.set_xlim(-1., 1.)                                
       self.high_level_eqarea.set_ylim(-1., 1.)
       self.high_level_eqarea.axes.set_aspect('equal')
       self.high_level_eqarea.axis('off')
       self.canvas4.draw()
                        
    def plot_eqarea_pars(self,pars,fig):
        # plot best-fit plane
        #fig.clear()
        if pars=={}:
            return
        if 'calculation_type' in pars.keys() and pars['calculation_type']=='DE-BFP':
            ymin, ymax = fig.get_ylim()
            xmin, xmax = fig.get_xlim()
            
            D_c,I_c=pmag.circ(pars["specimen_dec"],pars["specimen_inc"],90)
            X_c_up,Y_c_up=[],[]
            X_c_d,Y_c_d=[],[]
            for k in range(len(D_c)):
                XY=pmag.dimap(D_c[k],I_c[k])
                if I_c[k]<0:
                    X_c_up.append(XY[0])
                    Y_c_up.append(XY[1])
                if I_c[k]>0:
                    X_c_d.append(XY[0])
                    Y_c_d.append(XY[1])
            fig.plot(X_c_d,Y_c_d,'b',lw=0.5)
            fig.plot(X_c_up,Y_c_up,'c',lw=0.5)
            
            fig.set_xlim(xmin, xmax)
            fig.set_ylim(ymin, ymax)           
        # plot best-fit direction
        else:
            if "specimen_dec" in pars.keys() and "specimen_inc" in pars.keys():
                dec=pars["specimen_dec"];inc=pars["specimen_inc"]
            elif "dec" in pars.keys() and "inc" in pars.keys():
                dec=pars["dec"];inc=pars["inc"]                
            XY=pmag.dimap(dec,inc)                
            if inc>0:
                FC='gray';SIZE=15*self.GUI_RESOLUTION
            else:
                FC='white';SIZE=15*self.GUI_RESOLUTION
            fig.scatter([XY[0]],[XY[1]],marker='o',edgecolor='black', facecolor=FC,s=SIZE,lw=1,clip_on=False)
                            
    def plot_eqarea_mean(self,meanpars,fig):
        #fig.clear()
        mpars_to_plot=[]
        if meanpars=={}:
            return
        if meanpars['calculation_type']=='Fisher by polarity':
            for mode in ['A','B','All']:
                if meanpars[mode]!={}:
                    mpars_to_plot.append(meanpars[mode])
        else:
           mpars_to_plot.append(meanpars)
        ymin, ymax = fig.get_ylim()
        xmin, xmax = fig.get_xlim()
        # put on the mean direction
        for mpars in mpars_to_plot:
            XY=pmag.dimap(float(mpars["dec"]),float(mpars["inc"]))
            if mpars["inc"]>0:
                FC='green';EC='0.1'
            else:
                FC='yellow';EC='green'
            fig.scatter([XY[0]],[XY[1]],marker='o',edgecolor=EC, facecolor=FC,s=30,lw=1,clip_on=False)
            
            #if 'calculation_type' not in mpars.keys():
            #    return
                
            if "alpha95" in mpars.keys():
            # get the alpha95
                Xcirc,Ycirc=[],[]
                Da95,Ia95=pmag.circ(float(mpars["dec"]),float(mpars["inc"]),float(mpars["alpha95"]))
                for k in  range(len(Da95)):
                    XY=pmag.dimap(Da95[k],Ia95[k])
                    Xcirc.append(XY[0])
                    Ycirc.append(XY[1])
                fig.plot(Xcirc,Ycirc,'g')
            elif 'calculation_type' in mpars.keys() and mpars['calculation_type']=='Bingham':
                # copied from plotELL function in pmagplotlib
                rad=numpy.pi/180.
                #Pdec,Pinc,beta,Bdec,Binc,gamma,Gdec,Ginc=pars[0],pars[1],pars[2],pars[3],pars[4],pars[5],pars[6],pars[7]
                Pdec,Pinc,beta,Bdec,Binc,gamma,Gdec,Ginc=\
                mpars['dec'],mpars['inc'],mpars['Zeta'],mpars['Zdec'],mpars['Zinc'],mpars['Eta'],mpars['Edec'],mpars['Einc']
                
                if beta > 90. or gamma>90:
                    beta=180.-beta
                    gamma=180.-beta
                    Pdec=Pdec-180.
                    Pinc=-Pinc
                beta,gamma=beta*rad,gamma*rad # convert to radians
                X_ell,Y_ell,X_up,Y_up,PTS=[],[],[],[],[]
                nums=201
                xnum=float(nums-1.)/2.
            # set up t matrix
                t=[[0,0,0],[0,0,0],[0,0,0]]
                X=pmag.dir2cart((Pdec,Pinc,1.0)) # convert to cartesian coordintes
                if  X[2]<0:
                    for i in range(3):
                        X[i]=-X[i]
            # set up rotation matrix t
                t[0][2]=X[0]
                t[1][2]=X[1]
                t[2][2]=X[2]
                X=pmag.dir2cart((Bdec,Binc,1.0))
                if  X[2]<0:
                    for i in range(3):
                        X[i]=-X[i]
                t[0][0]=X[0]
                t[1][0]=X[1]
                t[2][0]=X[2]
                X=pmag.dir2cart((Gdec,Ginc,1.0))
                if X[2]<0:
                    for i in range(3):
                        X[i]=-X[i]
                t[0][1]=X[0]
                t[1][1]=X[1]
                t[2][1]=X[2]
            # set up v matrix
                v=[0,0,0]
                for i in range(nums):  # incremental point along ellipse
                    psi=float(i)*numpy.pi/xnum
                    v[0]=numpy.sin(beta)*numpy.cos(psi) 
                    v[1]=numpy.sin(gamma)*numpy.sin(psi) 
                    v[2]=numpy.sqrt(1.-v[0]**2 - v[1]**2)
                    elli=[0,0,0]
            # calculate points on the ellipse
                    for j in range(3):
                        for k in range(3):
                            elli[j]=elli[j] + t[j][k]*v[k]  # cartesian coordinate j of ellipse
                    PTS.append(pmag.cart2dir(elli))
                    R=numpy.sqrt( 1.-abs(elli[2]))/(numpy.sqrt(elli[0]**2+elli[1]**2)) # put on an equal area projection
                    if elli[2]<0:
            #            for i in range(3): elli[i]=-elli[i]
                        X_up.append(elli[1]*R)
                        Y_up.append(elli[0]*R)
                    else:
                        X_ell.append(elli[1]*R)
                        Y_ell.append(elli[0]*R)
                #if plot==1:
                if X_ell!=[]:fig.plot(X_ell,Y_ell,'b')
                if X_up!=[]:fig.plot(X_up,Y_up,'g-')
                #pylab.draw()
                #else: 
                #    return PTS
                
        fig.set_xlim(xmin, xmax)
        fig.set_ylim(ymin, ymax)    

    def show_higher_levels_pars(self,mpars):
        self.high_level_text_box.SetValue("")
        FONT_RATIO=self.GUI_RESOLUTION+(self.GUI_RESOLUTION-1)*5
        font2 = wx.Font(12+min(1,FONT_RATIO), wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        self.high_level_text_box.SetFont(font2)
        if mpars["calculation_type"]=='Fisher' and "alpha95" in mpars.keys():
            String="Fisher statistics:\n"
            String=String+"dec"+": "+"%.1f\n"%float(mpars['dec'])
            String=String+"inc"+": "+"%.1f\n"%float(mpars['inc'])
            String=String+"alpha95"+": "+"%.1f\n"%float(mpars['alpha95'])
            String=String+"K"+": "+"%.1f\n"%float(mpars['K'])
            String=String+"R"+": "+"%.4f\n"%float(mpars['R'])
            String=String+"n_lines"+": "+"%.0f\n"%float(mpars['n_lines'])
            String=String+"n_planes"+": "+"%.0f\n"%float(mpars['n_planes'])
            self.high_level_text_box.AppendText(String)

        if mpars["calculation_type"]=='Fisher by polarity':
            for mode in ['A','B','All']:
                if mode not in mpars.keys():
                    continue
                if mpars[mode]=={}:
                    continue
                String="Fisher statistics [%s]:\n"%mode
                String=String+"dec"+": "+"%.1f\n"%float(mpars[mode]['dec'])
                String=String+"inc"+": "+"%.1f\n"%float(mpars[mode]['inc'])
                String=String+"alpha95"+": "+"%.1f\n"%float(mpars[mode]['alpha95'])
                String=String+"N"+": "+"%.0f\n"%float(mpars[mode]['n'])
                String=String+"K"+": "+"%.1f\n"%float(mpars[mode]['k'])
                String=String+"R"+": "+"%.4f\n"%float(mpars[mode]['r'])
                self.high_level_text_box.AppendText(String)
                
                                
        if mpars["calculation_type"]=='Bingham':
            String="Bingham statistics:\n"
            self.high_level_text_box.AppendText(String)
            String=""
            String=String+"dec"+": "+"%.1f\n"%float(mpars['dec'])
            String=String+"inc"+": "+"%.1f\n"%float(mpars['inc'])
            String=String+"n"+": "+"%.0f\n"%float(mpars['n'])
            String=String+"Zdec"+": "+"%.0f\n"%float(mpars['Zdec'])
            String=String+"Zinc"+": "+"%.1f\n"%float(mpars['Zinc'])
            String=String+"Zeta"+": "+"%.4f\n"%float(mpars['Zeta'])
            String=String+"Edec"+": "+"%.0f\n"%float(mpars['Edec'])
            String=String+"Einc"+": "+"%.1f\n"%float(mpars['Einc'])
            String=String+"Eta"+": "+"%.1f\n"%float(mpars['Eta'])
            self.high_level_text_box.AppendText(String)
                

                
    #def initialize_acceptence_criteria (self):
    #    self.acceptance_criteria={}
    #    self.acceptance_criteria=self.pmag.initialize_acceptence_criteria()
           
                             
#============================================

    #-------------------------------
    # get_data:
    # Read data from magic_measurements.txt
    #-------------------------------

    def get_data(self):
      



      #------------------------------------------------
      # Read magic measurement file and sort to blocks
      #------------------------------------------------

      # All data information is stored in Data[secimen]={}
      Data={}
      Data_hierarchy={}
      Data_hierarchy['study']={}
      Data_hierarchy['locations']={}
      Data_hierarchy['sites']={}
      Data_hierarchy['samples']={}
      Data_hierarchy['specimens']={}
      Data_hierarchy['sample_of_specimen']={} 
      Data_hierarchy['site_of_specimen']={}   
      Data_hierarchy['site_of_sample']={}   
      Data_hierarchy['location_of_site']={}   
      Data_hierarchy['location_of_specimen']={}   
      Data_hierarchy['study_of_specimen']={}   
      Data_hierarchy['expedition_name_of_specimen']={}
      mag_meas_data,file_type=pmag.magic_read(self.magic_file)
      self.mag_meas_data=copy.deepcopy(self.merge_pmag_recs(mag_meas_data))
      
      self.GUI_log.write("-I- Read magic file  %s\n"%self.magic_file)

      # get list of unique specimen names
      
      CurrRec=[]
      # print "-I- get sids"

      sids=pmag.get_specs(self.mag_meas_data) # samples ID's
      # print "-I- done get sids"

      # print "initialize blocks"
      
      for s in sids:

          if s not in Data.keys():
              Data[s]={}
              Data[s]['zijdblock']=[]
              Data[s]['zijdblock_geo']=[]
              Data[s]['zijdblock_tilt']=[]
              Data[s]['zijdblock_lab_treatments']=[]
              Data[s]['pars']={}
              Data[s]['zijdblock_steps']=[]
              Data[s]['measurement_flag']=[]# a list of points 'g' or 'b'
              Data[s]['mag_meas_data_index']=[]  # index in original magic_measurements.txt
              #print "done initialize blocks"

      #print "sorting meas data"
      cnt=-1
      for rec in self.mag_meas_data:
          cnt+=1 #index counter
          s=rec["er_specimen_name"]
          sample=rec["er_sample_name"]
          site=rec["er_site_name"]
          location=rec["er_location_name"]
          expedition_name=""
          if "er_expedition_name" in rec.keys():
              expedition_name=rec["er_expedition_name"]

          #---------------------
          # sort data to Zijderveld block"
          # [tr,dec,inc,int,ZI,rec['measurement_flag'],rec['magic_instrument_codes']\
          # (ZI=0)
          #---------------------
          
          # list of excluded lab protocols. copied from pmag.find_dmag_rec(s,data)  
          EX=["LP-AN-ARM","LP-AN-TRM","LP-ARM-AFD","LP-ARM2-AFD","LP-TRM-AFD","LP-TRM","LP-TRM-TD","LP-X"] 
          INC=["LT-NO","LT-AF-Z","LT-T-Z", "LT-M-Z","LT-LT-Z"]

          methods=rec["magic_method_codes"].replace(" ","").strip("\n").split(":")
          LP_methods=[]
          LT_methods=[]
          
          for i in range (len(methods)):
               methods[i]=methods[i].strip()
          if 'measurement_flag' not in rec.keys():
              rec['measurement_flag']='g'
          SKIP=True;lab_treatment=""
          for meth in methods:
               if meth in ["LT-NO","LT-AF-Z","LT-T-Z", "LT-M-Z","LT-LT-Z"]:
                   lab_treatment=meth
                   SKIP=False
               if "LP" in meth:
                   LP_methods.append(meth) 
          for meth in EX:
               if meth in methods:
                   SKIP=True
          if not SKIP:
             tr=""
             if "LT-NO" in methods:
                 tr=0
                 measurement_step_unit=""   
                 LPcode=""
                 for method in methods:
                     if "AF" in method:
                         LPcode="LP-DIR-AF"
                         measurement_step_unit="mT"
                     if "TRM" in method:
                         LPcode="LP-DIR-T"
                         measurement_step_unit="C"
             elif "LT-AF-Z" in  methods:
                 tr = float(rec["treatment_ac_field"])*1e3 #(mT)
                 measurement_step_unit="mT" # in magic its T in GUI its mT
                 LPcode="LP-DIR-AF"
             elif  "LT-T-Z" in  methods or "LT-LT-Z" in methods:
                 tr = float(rec["treatment_temp"])-273. # celsius
                 measurement_step_unit="C" # in magic its K in GUI its C
                 LPcode="LP-DIR-T"
             elif  "LT-M-Z" in  methods:
                 tr = float(rec["measurement_number"]) # temporary for microwave
             else:
                 tr = float(rec["measurement_number"])
                                
             #if "LP-PI-TRM-IZ" in methods or "LP-PI-M-IZ" in methods:  # looking for in-field first thellier or microwave data - otherwise, just ignore this
             #    ZI=0
             #else:
             #    ZI=1
             ZI=0
             
             if tr !="":
                 Data[s]['mag_meas_data_index'].append(cnt) # magic_measurement file intex 
                 Data[s]['zijdblock_lab_treatments'].append(lab_treatment)
                 if measurement_step_unit!="": 
                    if  'measurement_step_unit' in Data[s].keys():
                        if measurement_step_unit not in Data[s]['measurement_step_unit'].split(":"):
                            Data[s]['measurement_step_unit']=Data[s]['measurement_step_unit']+":"+measurement_step_unit
                    else:
                        Data[s]['measurement_step_unit']=measurement_step_unit
                 dec,inc,int = "","",""
                 if "measurement_dec" in rec.keys() and rec["measurement_dec"] != "":
                     dec=float(rec["measurement_dec"])
                 else:
                     continue
                 if "measurement_inc" in rec.keys() and rec["measurement_inc"] != "":
                     inc=float(rec["measurement_inc"])
                 else:
                     continue
                 if "measurement_magn_moment" in rec.keys() and rec["measurement_magn_moment"] != "":
                     intensity=float(rec["measurement_magn_moment"])
                 else:
                     continue
                 if 'magic_instrument_codes' not in rec.keys():
                     rec['magic_instrument_codes']=''
                 Data[s]['zijdblock'].append([tr,dec,inc,intensity,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
                 if 'magic_experiment_name' in Data[s].keys() and Data[s]['magic_experiment_name']!=rec["magic_experiment_name"]:
                      self.GUI_log.write("-E- ERROR: specimen %s has more than one demagnetization experiment name. You need to merge them to one experiment-name?\n")
                 if float(tr)==0 or float(tr)==273:
                    Data[s]['zijdblock_steps'].append("0")                     
                 elif measurement_step_unit=="C":
                    Data[s]['zijdblock_steps'].append("%.0f%s"%(tr,measurement_step_unit))
                 else:
                    Data[s]['zijdblock_steps'].append("%.1f%s"%(tr,measurement_step_unit))
                 #--------------
                 Data[s]['magic_experiment_name']=rec["magic_experiment_name"]
                 if "magic_instrument_codes" in rec.keys():
                     Data[s]['magic_instrument_codes']=rec['magic_instrument_codes']
                 #if len(LP_methods)==0:
                 Data[s]["magic_method_codes"]=LPcode
                 #else:
                 #Data[s]["magic_method_codes"]=":".join(LP_methods)
                     


                 #--------------
                 # ""good" or "bad" data
                 #--------------
                 flag='g'
                 if 'measurement_flag' in rec.keys():
                     if str(rec["measurement_flag"])=='b':
                         flag='b'
                 Data[s]['measurement_flag'].append(flag)     
                                  
                 # gegraphic coordinates

                                  
                 try:
                    sample_azimuth=float(self.Data_info["er_samples"][sample]['sample_azimuth'])
                    sample_dip=float(self.Data_info["er_samples"][sample]['sample_dip'])
                    sample_orientation_flag='g'
                    if 'sample_orientation_flag' in  self.Data_info["er_samples"][sample].keys():
                        if str(self.Data_info["er_samples"][sample]['sample_orientation_flag'])=='b':
                            sample_orientation_flag='b'
                    if sample_orientation_flag!='b':                     
                        d_geo,i_geo=pmag.dogeo(dec,inc,sample_azimuth,sample_dip)
                        Data[s]['zijdblock_geo'].append([tr,d_geo,i_geo,intensity,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
                 except:
                    self.GUI_log.write( "-W- cant find sample_azimuth,sample_dip for sample %s\n"%sample) 

                 # tilt-corrected coordinates

                 try:
                    sample_bed_dip_direction=float(self.Data_info["er_samples"][sample]['sample_bed_dip_direction'])
                    sample_bed_dip=float(self.Data_info["er_samples"][sample]['sample_bed_dip'])                 
                    d_tilt,i_tilt=pmag.dotilt(d_geo,i_geo,sample_bed_dip_direction,sample_bed_dip)
                    Data[s]['zijdblock_tilt'].append([tr,d_tilt,i_tilt,intensity,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
                 except:
                    self.GUI_log.write("-W- cant find tilt-corrected data for sample %s\n"%sample) 
                    
                    #print methods
                 
          #---------------------
          # hierarchy is determined from magic_measurements.txt
          #
          #---------------------
                 
          if sample not in Data_hierarchy['samples'].keys():
              Data_hierarchy['samples'][sample]={}
              Data_hierarchy['samples'][sample]['specimens']=[]
              
          if site not in Data_hierarchy['sites'].keys():
              Data_hierarchy['sites'][site]={}         
              Data_hierarchy['sites'][site]['samples']=[]         
              Data_hierarchy['sites'][site]['specimens']=[]      

          if location not in Data_hierarchy['locations'].keys():
              Data_hierarchy['locations'][location]={}         
              Data_hierarchy['locations'][location]['sites']=[]         
              Data_hierarchy['locations'][location]['samples']=[]         
              Data_hierarchy['locations'][location]['specimens']=[]      
          
          if   'this study' not in Data_hierarchy['study'].keys():
            Data_hierarchy['study']['this study']={}  
            Data_hierarchy['study']['this study']['sites']=[]         
            Data_hierarchy['study']['this study']['samples']=[]         
            Data_hierarchy['study']['this study']['specimens']=[]      
          
          if s not in Data_hierarchy['samples'][sample]['specimens']:
              Data_hierarchy['samples'][sample]['specimens'].append(s)

          if s not in Data_hierarchy['sites'][site]['specimens']:
              Data_hierarchy['sites'][site]['specimens'].append(s)

          if s not in Data_hierarchy['locations'][location]['specimens']:
              Data_hierarchy['locations'][location]['specimens'].append(s)

          if s not in Data_hierarchy['study']['this study']['specimens']:
              Data_hierarchy['study']['this study']['specimens'].append(s)

          if sample not in Data_hierarchy['sites'][site]['samples']:
              Data_hierarchy['sites'][site]['samples'].append(sample)

          if sample not in Data_hierarchy['locations'][location]['samples']:
              Data_hierarchy['locations'][location]['samples'].append(sample)

          if sample not in Data_hierarchy['study']['this study']['samples']:
              Data_hierarchy['study']['this study']['samples'].append(sample)

          if site not in Data_hierarchy['locations'][location]['sites']:
              Data_hierarchy['locations'][location]['sites'].append(site)

          if site not in Data_hierarchy['study']['this study']['sites']:
              Data_hierarchy['study']['this study']['sites'].append(site)

          #Data_hierarchy['specimens'][s]=sample
          Data_hierarchy['sample_of_specimen'][s]=sample  
          Data_hierarchy['site_of_specimen'][s]=site  
          Data_hierarchy['site_of_sample'][sample]=site
          Data_hierarchy['location_of_site'][site]=location
          Data_hierarchy['location_of_specimen'][s]=location
          if expedition_name!="":
            Data_hierarchy['expedition_name_of_specimen'][s]=expedition_name                      
                                                   
                                                                                     
          
      print "-I- done sorting meas data"
      
      self.specimens=Data.keys()
      self.specimens.sort()

      #------------------------------------------------
      # analyze Zij block and save in dictionaries:
      # cartesian coordinates of the different datablocks:
      # Data[s]['zdata'] ;Data[s]['zdata_geo'];Data[s]['zijdblock_tilt']
      # cartesian datablocks Rotated to zijederveld block:
      # Data[s]['zij_rotated'] ;Data[s]['zij_rotated_geo'];Data[s]['zij_rotated_tilt']
      # VDS calculations:
      # Data[s]['vector_diffs']=array(vector_diffs)
      # Data[s]['vds']=vds
      #------------------------------------------------

      for s in self.specimens:
        # collected the data
        zijdblock=Data[s]['zijdblock']
        zijdblock_geo=Data[s]['zijdblock_geo']
        zijdblock_tilt=Data[s]['zijdblock_tilt']
        if len(zijdblock)<3:
            del Data[s]           
            continue

        #--------------------------------------------------------------
        # collect all zijderveld data to array and calculate VDS
        #--------------------------------------------------------------
        #z_treatments=[row[0] for row in zijdblock]
        zdata=[]
        zdata_geo=[]
        zdata_tilt=[]
        vector_diffs=[]
        NRM=zijdblock[0][3]
        for k in range(len(zijdblock)):
            # specimen coordinates
            DIR=[zijdblock[k][1],zijdblock[k][2],zijdblock[k][3]/NRM]
            cart=pmag.dir2cart(DIR)
            zdata.append(array([cart[0],cart[1],cart[2]]))
            # geographic coordinates
            if len(zijdblock_geo)!=0:
                DIR=[zijdblock_geo[k][1],zijdblock_geo[k][2],zijdblock_geo[k][3]/NRM]
                cart=pmag.dir2cart(DIR)
                zdata_geo.append(array([cart[0],cart[1],cart[2]]))
            # tilt-corrected coordinates
            if len(zijdblock_tilt)!=0:
                DIR=[zijdblock_tilt[k][1],zijdblock_tilt[k][2],zijdblock_tilt[k][3]/NRM]
                cart=pmag.dir2cart(DIR)
                zdata_tilt.append(array([cart[0],cart[1],cart[2]]))
            if k>0:
                vector_diffs.append(sqrt(sum((array(zdata[-2])-array(zdata[-1]))**2)))

        vector_diffs.append(sqrt(sum(array(zdata[-1])**2))) # last vector of the vds
        vds=sum(vector_diffs)  # vds calculation       

        Data[s]['vector_diffs']=array(vector_diffs)
        Data[s]['vds']=vds
        #Data[s]['z_treatments']=z_treatments
        Data[s]['zdata']=array(zdata)
        Data[s]['zdata_geo']=array(zdata_geo)
        Data[s]['zdata_tilt']=array(zdata_tilt)
        
        #--------------------------------------------------------------    
        # Rotate zijderveld plot
        #--------------------------------------------------------------
    
        
        #Data[s]['zij_rotated']=self.Rotate_zijderveld(Data[s]['zdata'],pmag.cart2dir(Data[s]['zdata'][0])[0])
        #Data[s]['zij_rotated_geo']=self.Rotate_zijderveld(Data[s]['zdata_geo'],pmag.cart2dir(Data[s]['zdata_geo'][0])[0])
        #Data[s]['zij_rotated_tilt']=self.Rotate_zijderveld(Data[s]['zdata_tilt'],pmag.cart2dir(Data[s]['zdata_tilt'][0])[0])
      
      self.mag_meas_data=self.merge_pmag_recs(mag_meas_data)
         
      return(Data,Data_hierarchy)

    def Rotate_zijderveld(self,Zdata,rot_declination):
        if len(Zdata)==0:
            return([])
        CART_rot=[]
        for i in range(0,len(Zdata)):
            DIR=pmag.cart2dir(Zdata[i])
            DIR[0]=(DIR[0]-rot_declination)%360.
            CART_rot.append(array(pmag.dir2cart(DIR)))
        CART_rot=array(CART_rot)        
        return(CART_rot)

    #def Rotate_zijderveld(self,Zdata,declination):
    #    if len(Zdata)==0:
    #        return([])
    #    DIR_rot=[]
    #    CART_rot=[]
    #    # rotate to be as NRM
    #    NRM_dir=pmag.cart2dir(Zdata[0])         
    #    NRM_dec=NRM_dir[0]
    #    NRM_dir[0]=0.
    #    CART_rot.append(pmag.dir2cart(NRM_dir))
    #    
    #    for i in range(1,len(Zdata)):
    #        DIR=pmag.cart2dir(Zdata[i])
    #        DIR[0]=(DIR[0]-NRM_dec)%360
    #        CART_rot.append(array(pmag.dir2cart(DIR)))
    #    CART_rot=array(CART_rot)        
    #    return(CART_rot)

    def read_magic_file(self,path,sort_by_this_name):
        DATA={}
        fin=open(path,'rU')
        fin.readline()
        line=fin.readline()
        header=line.strip('\n').split('\t')
        for line in fin.readlines():
            tmp_data={}
            tmp_line=line.strip('\n').split('\t')
            for i in range(len(tmp_line)):
                tmp_data[header[i]]=tmp_line[i]
            if tmp_data[sort_by_this_name] in DATA.keys():
                self.GUI_log.write("-E- ERROR: magic file %s has more than one line for %s %s\n"%(path,sort_by_this_name,tmp_data[sort_by_this_name]))
            DATA[tmp_data[sort_by_this_name]]=tmp_data
        fin.close()        
        return(DATA)


    #-------------------------------
    # get_data_info:
    # Read data from er_* tables
    #-------------------------------

    def get_data_info(self):
        Data_info={}
        data_er_samples={}
        data_er_sites={}
        data_er_locations={}
        data_er_ages={}

        try:
            data_er_samples=self.read_magic_file(os.path.join(self.WD, "er_samples.txt"),'er_sample_name')
        except:
            self.GUI_log.write ("-W- Cant find er_sample.txt in project directory")

        try:
            data_er_sites=self.read_magic_file(os.path.join(self.WD, "er_sites.txt"),'er_site_name')
        except:
            self.GUI_log.write ("-W- Cant find er_sites.txt in project directory")

        try:
            data_er_locations=self.read_magic_file(os.path.join(self.WD, "er_locations.txt"), 'er_location_name')
        except:
            self.GUI_log.write ("-W- Cant find er_locations.txt in project directory")

        try:
            data_er_ages=self.read_magic_file(os.path.join(self.WD, "er_ages.txt"),'er_sample_name')
        except:
            try:
                data_er_ages=self.read_magic_file(os.path.join(self.WD, "er_ages.txt"),'er_site_name')
            except:    
                self.GUI_log.write ("-W- Cant find er_ages in project directory")



        Data_info["er_samples"]=data_er_samples
        Data_info["er_sites"]=data_er_sites
        Data_info["er_locations"]=data_er_locations
        Data_info["er_ages"]=data_er_ages
        
        return(Data_info)

#    def get_pmag_table(self,table_name):
#        ''' 
#        read existing pmag table from working directory
#        '''
#        data_pmag_table={}
#        try:
#            data_pmag_table=self.read_magic_file(self.WD+"/"+table_name,'er_specimen_name')
#        except:
#            self.GUI_log.write ("-W- Cant find %s with old interpretation in project directory"%table_name)
#
#        return(data_pmag_table)
        
    def update_pmag_tables(self):
        #print "run update_pmag_tables"
        pmag_specimens,pmag_samples,pmag_sites=[],[],[]
        try:
            pmag_specimens,file_type=pmag.magic_read(os.path.join(self.WD, "pmag_specimens.txt"))
        except:
            print "-I- Cant read pmag_specimens.txt"
        try:
            pmag_samples,file_type=pmag.magic_read(os.path.join(self.WD, "pmag_samples.txt"))
        except:
            print "-I- Cant read pmag_samples.txt"
        try:
            pmag_sites,file_type=pmag.magic_read(os.path.join(self.WD, "pmag_sites.txt"))
        except:
            print "-I- Cant read pmag_sites.txt"
        self.GUI_log.write ("-I- Reading previous interpretations from pmag* tables\n")        
        #--------------------------
        # reads pmag_specimens.txt and 
        # update pmag_results_data['specimens'][specimen]
        # with the new interpertation
        #--------------------------
        
        #specimens = pmag.get_specs(pmag_specimens)
        #specimens.sort()
        for rec in pmag_specimens:
            specimen=rec['er_specimen_name']
            methods=rec['magic_method_codes'].strip("\n").replace(" ","").split(":")
            LPDIR=False;calculation_type=""
            for method in methods:
                if "LP-DIR" in method:
                    LPDIR=True
                if "DE-" in method:
                    calculation_type=method
            if LPDIR: # this a mean of directions
                if float(rec['measurement_step_min'])==0 or float(rec['measurement_step_min'])==273.:
                    tmin="0"
                elif float(rec['measurement_step_min'])>2: # thermal
                    tmin="%.0fC"%(float(rec['measurement_step_min'])-273.)
                else: # AF
                    tmin="%.1fmT"%(float(rec['measurement_step_min'])*1000.)

                if float(rec['measurement_step_max'])==0 or float(rec['measurement_step_max'])==273.:
                    tmax="0"
                elif float(rec['measurement_step_max'])>2: # thermal
                    tmax="%.0fC"%(float(rec['measurement_step_max'])-273.)
                else: # AF
                    tmax="%.1fmT"%(float(rec['measurement_step_max'])*1000.)
                
                
                #else:
                #    continue
                if calculation_type !="":                              
                    self.pmag_results_data['specimens'][specimen]={}
                    if specimen in self.Data.keys() and 'zijdblock_steps' in self.Data[specimen]\
                    and tmin in self.Data[specimen]['zijdblock_steps']\
                    and tmax in self.Data[specimen]['zijdblock_steps']:
                        #print "specimen,tmin,tmax",specimen,tmin,tmax
                        #print "specimen calc"
                        #print self.Data[specimen].keys()
                        #print "len(self.Data[specimen]['zijdblock'])",len(self.Data[specimen]['zijdblock'])
                        #print "len(self.Data[specimen][zijdblock_geo]",len(self.Data[specimen]['zijdblock_geo'])
                        #print "len(self.Data[specimen]['zijdblock_tilt'])",len(self.Data[specimen]['zijdblock_tilt'])
                        self.pmag_results_data['specimens'][specimen]['DA-DIR']=self.get_PCA_parameters(specimen,tmin,tmax,'specimen',calculation_type)
                        if len(self.Data[specimen]['zijdblock_geo'])>0: 
                            self.pmag_results_data['specimens'][specimen]['DA-DIR-GEO']=self.get_PCA_parameters(specimen,tmin,tmax,'geographic',calculation_type)                
                        if len(self.Data[specimen]['zijdblock_tilt'])>0:      
                            self.pmag_results_data['specimens'][specimen]['DA-DIR-TILT']=self.get_PCA_parameters(specimen,tmin,tmax,'tilt-corrected',calculation_type)                        
                    else:
                        self.GUI_log.write ( "-W- WARNING: Cant find specimen and steps of specimen %s tmin=%s, tmax=%s"%(specimen,tmin,tmax))
                        
        #--------------------------
        # reads pmag_sample.txt and 
        # if finds a mean in pmag_samples.txt
        # calculate the mean for self.high_level_means['samples'][samples]
        # If the program finds a codes "DE-FM","DE-FM-LP","DE-FM-UV"in magic_method_codes
        # then the program repeat teh fisher mean
        #--------------------------
        
        for rec in pmag_samples:
            methods=rec['magic_method_codes'].strip("\n").replace(" ","").split(":")
            sample=rec['er_sample_name'].strip("\n")
            LPDIR=False;calculation_method=""
            for method in methods:
                if "LP-DIR" in method:
                    LPDIR=True
                if "DE-" in method:
                    calculation_method=method
            if LPDIR: # this a mean of directions
                #if  calculation_method in ["DE-FM","DE-FM-LP","DE-FM-UV"]:
                    calculation_type="Fisher"
                    for dirtype in ['DA-DIR','DA-DIR-GEO','DA-DIR-TILT']: 
                        self.calculate_high_level_mean('samples',sample,calculation_type,'specimens')
        #--------------------------
        # reads pmag_sites.txt and 
        # if finds a mean in pmag_sites.txt
        # calculate the mean for self.high_level_means['sites'][site]
        # using specimens or samples, depends on the er_specimen_names or er_samples_names
        #  The program repeat the fisher calculation and oevrwrites it
        #--------------------------
        
        for rec in pmag_sites:
            methods=rec['magic_method_codes'].strip("\n").replace(" ","").split(":")
            site=rec['er_site_name'].strip("\n")
            LPDIR=False;calculation_method=""
            for method in methods:
                if "LP-DIR" in method or "DA-DIR" in method or "DE-FM" in method:
                    LPDIR=True
                if "DE-" in method:
                    calculation_method=method
            if LPDIR: # this a mean of directions
                if  calculation_method in ["DE-BS"]:
                    calculation_type="Bingham"
                else:
                    calculation_type="Fisher"
                if 'er_sample_names' in rec.keys() and len(rec['er_sample_names'].strip('\n').replace(" ","").split(":"))>0:
                    elements_type='samples'
                if 'er_specimen_names' in rec.keys() and len(rec['er_specimen_names'].strip('\n').replace(" ","").split(":"))>0:
                    elements_type='specimens'
                self.calculate_high_level_mean('sites',site,calculation_type,elements_type)
                #print "found previose interpretation",site,calculation_type,elements_type
            #print "this is sites"
            #print self.high_level_means['sites']        
               
                    
                
                    
            

    #-----------------------------------

    def get_preferences(self):
        #default
        preferences={}
        preferences['gui_resolution']=100.
        preferences['show_Zij_treatments']=True
        preferences['show_Zij_treatments_steps']=2.
        preferences['show_eqarea_treatments']=False
        #preferences['show_statistics_on_gui']=["int_n","int_ptrm_n","frac","scat","gmax","b_beta","int_mad","dang","f","fvds","g","q","drats"]#,'ptrms_dec','ptrms_inc','ptrms_mad','ptrms_angle']
        #try to read preferences file:
        try:
            import zeq_gui_preferences
            self.GUI_log.write( "-I- zeq_gui.preferences imported\n")
            preferences.update(thellier_gui_preferences.preferences)
        except:
            self.GUI_log.write( " -I- cant find zeq_gui_preferences file, using defualt default \n")
        return(preferences)

#==============================================================
# Menu Bar functions
#==============================================================

    #----------------------------------------------------------------------
        
    def create_menu(self):
        """ Create menu
        """
        self.menubar = wx.MenuBar()

        #-----------------                            

        #menu_preferences = wx.Menu()

        #m_preferences_apperance = menu_preferences.Append(-1, "&Appearence preferences", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_appearance_preferences, m_preferences_apperance)
        
        #m_preferences_stat = menu_preferences.Append(-1, "&Statistics preferences", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_preferences_stat, m_preferences_stat)

        #-----------------                            

        menu_file = wx.Menu()
        
        #m_change_working_directory = menu_file.Append(-1, "&Change MagIC project directory", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_change_working_directory, m_change_working_directory)

        m_make_MagIC_results_tables= menu_file.Append(-1, "&Save MagIC pmag tables", "")
        self.Bind(wx.EVT_MENU, self.on_menu_make_MagIC_results_tables, m_make_MagIC_results_tables)

        #m_open_magic_file = menu_file.Append(-1, "&Open MagIC measurement file", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_open_magic_file, m_open_magic_file)

        submenu_save_plots = wx.Menu()

        m_save_zij_plot = submenu_save_plots.Append(-1, "&Save Zijderveld plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Zij_plot, m_save_zij_plot,"Zij")

        m_save_eq_plot = submenu_save_plots.Append(-1, "&Save specimen equal area plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Eq_plot, m_save_eq_plot,"specimen-Eq")

        m_save_M_t_plot = submenu_save_plots.Append(-1, "&Save M-t plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_M_t_plot, m_save_M_t_plot,"M_t")

        m_save_high_level = submenu_save_plots.Append(-1, "&Save high level plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_high_level, m_save_high_level,"Eq")

        m_save_all_plots = submenu_save_plots.Append(-1, "&Save all plots", "")
        self.Bind(wx.EVT_MENU, self.on_save_all_figures, m_save_all_plots)

        m_new_sub_plots = menu_file.AppendMenu(-1, "&Save plot", submenu_save_plots)

        
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_menu_exit, m_exit)
                                                                                                                                                                                                           
        #-----------------                            

        menu_Analysis = wx.Menu()

        submenu_criteria = wx.Menu()

        #m_set_criteria_to_default = submenu_criteria.Append(-1, "&Set acceptance criteria to default", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_default_criteria, m_set_criteria_to_default)

        m_change_criteria_file = submenu_criteria.Append(-1, "&Change acceptance criteria", "")
        self.Bind(wx.EVT_MENU, self.on_menu_change_criteria, m_change_criteria_file)

        m_import_criteria_file =  submenu_criteria.Append(-1, "&Import criteria file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_criteria_file, m_import_criteria_file)

        m_new_sub = menu_Analysis.AppendMenu(-1, "Acceptance criteria", submenu_criteria)


        m_previous_interpretation = menu_Analysis.Append(-1, "&Import previous interpretation from a redo file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_previous_interpretation, m_previous_interpretation)

        m_save_interpretation = menu_Analysis.Append(-1, "&Save current interpretations to a redo file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_save_interpretation, m_save_interpretation)

        m_delete_interpretation = menu_Analysis.Append(-1, "&Clear all current interpretations", "")
        self.Bind(wx.EVT_MENU, self.on_menu_clear_interpretation, m_delete_interpretation)

        #-----------------                            

        menu_Tools = wx.Menu()
        m_bulk_demagnetization = menu_Tools.Append(-1, "&Bulk demagnetization", "")
        self.Bind(wx.EVT_MENU, self.on_menu_bulk_demagnetization, m_bulk_demagnetization)

        #-------------------
        
        #menu_Plot= wx.Menu()
        #m_plot_data = menu_Plot.Append(-1, "&Plot ...", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_plot_data, m_plot_data)

        #-------------------

        #menu_results_table= wx.Menu()
        #m_make_results_table = menu_results_table.Append(-1, "&Make results table", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_results_data, m_make_results_table)
        
        #menu_Auto_Interpreter = wx.Menu()
        
        #m_interpreter = menu_Auto_Interpreter.Append(-1, "&Run Thellier auto interpreter", "Run auto interpter")
        #self.Bind(wx.EVT_MENU, self.on_menu_run_interpreter, m_interpreter)

        #m_open_interpreter_file = menu_Auto_Interpreter.Append(-1, "&Open auto-interpreter output files", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_open_interpreter_file, m_open_interpreter_file)

        #m_open_interpreter_log = menu_Auto_Interpreter.Append(-1, "&Open auto-interpreter Warnings/Errors", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_open_interpreter_log, m_open_interpreter_log)

        #-----------------                            

#        menu_MagIC= wx.Menu()
#        m_convert_to_magic= menu_MagIC.Append(-1, "&Convert generic files to MagIC format", "")
#        self.Bind(wx.EVT_MENU, self.on_menu_generic_to_magic, m_convert_to_magic)
#        m_samples_orientation= menu_MagIC.Append(-1, "&Sample orientation", "")
#        self.Bind(wx.EVT_MENU, self.on_menu_samples_orientation, m_samples_orientation)
#
#        m_build_magic_model= menu_MagIC.Append(-1, "&Run MagIC model builder", "")
#        self.Bind(wx.EVT_MENU, self.on_menu_MagIC_model_builder, m_build_magic_model)
#        m_make_MagIC_results_tables= menu_MagIC.Append(-1, "&Save MagIC results tables", "")
#        self.Bind(wx.EVT_MENU, self.on_menu_make_MagIC_results_tables, m_make_MagIC_results_tables)

        #-----------------                            
        
        #self.menubar.Append(menu_preferences, "& Preferences") 
        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_Analysis, "&Analysis")
        self.menubar.Append(menu_Tools, "&Tools")
        #self.menubar.Append(menu_Plot, "&Plot")
        #self.menubar.Append(menu_results_table, "&Table")        
        #self.menubar.Append(menu_MagIC, "&MagIC")        
        self.SetMenuBar(self.menubar)

    #============================================

    def reset(self):
        '''
        reset the GUI like restarting it (same as __init__
        '''
        #global FIRST_RUN
        FIRST_RUN=False
        self.redo_specimens={}
        self.currentDirectory = os.getcwd() # get the current working directory
        self.get_DIR()        # choose directory dialog
                
        #preferences=self.get_preferences()
        #self.dpi = 100
        #self.preferences={}
        #self.preferences=preferences

        self.COORDINATE_SYSTEM='specimen'
        self.Data_info=self.get_data_info() # Read  er_* data
        self.Data,self.Data_hierarchy=self.get_data() # Get data from magic_measurements and rmag_anistropy if exist.
        
        self.pmag_results_data={}
        for level in ['specimens','samples','sites','lcoations','study']:
            self.pmag_results_data[level]={}
        self.high_level_means={}

        high_level_means={}                                            
        for high_level in ['samples','sites','locations','study']:
            if high_level not in self.high_level_means.keys():
                self.high_level_means[high_level]={}
        
        
        self.Data_samples={}
        self.last_saved_pars={}
        self.specimens=self.Data.keys()         # get list of specimens
        self.specimens.sort()                   # get list of specimens
        if len(self.specimens)>0:
            self.s=str(self.specimens[0])
        else:
            self.s=""
        self.pars={} 
        self.samples=self.Data_hierarchy['samples'].keys()         # get list of samples
        self.samples.sort()                   # get list of specimens
        self.sites=self.Data_hierarchy['sites'].keys()         # get list of sites
        self.sites.sort()                   # get list of sites
        self.locations=self.Data_hierarchy['locations'].keys()         # get list of sites
        self.locations.sort()                   # get list of sites
        
        #----------------------------------------------------------------------                     
        # initialize first specimen in list as current specimen
        #----------------------------------------------------------------------                     
        try:
            self.s=str(self.specimens[0])
        except:
            self.s=""
        try:
            self.sample=self.Data_hierarchy['sample_of_specimen'][self.s]
        except:
            self.sample=""
        try:
            self.site=self.Data_hierarchy['site_of_specimen'][self.s]
        except:
            self.site=""

        #self.get_previous_interpretation() # get interpretations from pmag_specimens.txt

        self.specimens_box.SetItems(self.specimens)
        self.specimens_box.SetStringSelection(str(self.s))  
        self.update_pmag_tables()
        # Draw figures and add  text
        try:
            self.update_selection()
        except:
            pass
        
        FIRST_RUN=False

    #--------------------------------------------------------------
    # File menu 
    #--------------------------------------------------------------

    def on_menu_exit(self, event):
        
        if self.close_warning:
            TEXT="Data is not saved to a file yet!\nTo properly save your data:\n1) Analysis --> Save current interpretations to a redo file.\nor\n1) File --> Save MagIC pmag tables.\n\n Press OK to exit without saving."
            
            #Save all interpretation to a 'redo' file or to MagIC specimens result table\n\nPress OK to exit"
            dlg1 = wx.MessageDialog(None,caption="Warning:", message=TEXT ,style=wx.OK|wx.CANCEL|wx.ICON_EXCLAMATION)
            if dlg1.ShowModal() == wx.ID_OK:
                dlg1.Destroy()
                self.Destroy()
                #sys.exit()
        else:
            self.Destroy()
            #sys.exit()
        
#        dlg1 = wx.MessageDialog(None,caption="Warning:", message="Exiting program.\nSave all interpretation to a 'redo' file or to MagIC specimens result table\n\nPress OK to exit" ,style=wx.OK|wx.CANCEL|wx.ICON_INFORMATION)
#        if dlg1.ShowModal() == wx.ID_OK:
#            dlg1.Destroy()
#            self.Destroy()
#            exit()
#
    def on_save_Zij_plot(self, event):
        self.fig1.text(0.9,0.98,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        SaveMyPlot(self.fig1,self.s,"Zij",self.WD)
        self.fig1.clear()
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_Eq_plot(self, event):
        #self.fig2.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        #self.canvas4.print_figure("./tmp.pdf")#, dpi=self.dpi) 
        SaveMyPlot(self.fig2,self.s,"EqArea",self.WD)
        #self.fig2.clear()
        #self.draw_figure(self.s)
        #self.update_selection()
        
    def on_save_M_t_plot(self, event):
        self.fig3.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        SaveMyPlot(self.fig3,self.s,"M_M0",self.WD)
        self.fig3.clear()
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_high_level(self, event):
        SaveMyPlot(self.fig4,str(self.level_names.GetValue()),str(self.level_box.GetValue()), self.WD )
        #self.fig4.clear()
        #self.draw_figure(self.s)
        #self.update_selection()
        #self.plot_higher_levels_data()

    def on_save_all_figures(self, event):

        dialog = wx.DirDialog(None, "choose a folder:",defaultPath = self.WD ,style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
              dir_path=dialog.GetPath()
              dialog.Destroy()
       
        #figs=[self.fig1,self.fig2,self.fig3,self.fig4]
        plot_types=["Zij","EqArea","M_M0",str(self.level_box.GetValue())]
        #elements=[self.s,self.s,self.s,str(self.level_names.GetValue())]
        for i in range(4):
            try:
                if plot_types[i]=="Zij":
                    self.fig1.text(0.9,0.98,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
                    SaveMyPlot(self.fig1,self.s,"Zij",dir_path)
                if plot_types[i]=="EqArea":
                    SaveMyPlot(self.fig2,self.s,"EqArea",dir_path)                
                if plot_types[i]=="M_M0":
                    self.fig3.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
                    SaveMyPlot(self.fig3,self.s,"M_M0",dir_path)
                if plot_types[i]==str(self.level_box.GetValue()):
                    SaveMyPlot(self.fig4,str(self.level_names.GetValue()),str(self.level_box.GetValue()),dir_path )
            except:
                pass    
                
        self.fig1.clear()
        self.fig3.clear()
        self.draw_figure(self.s)
        self.update_selection()
                              
    def on_menu_change_working_directory(self, event):
        self.reset()
    
    
                            
    #--------------------------------------------------------------
    # Analysis menu Bar functions
    #--------------------------------------------------------------


    def on_menu_previous_interpretation(self,event):
        
        save_current_specimen=self.s
        """
        Create and show the Open FileDialog for upload previous interpretation
        input should be a valid "redo file":
        [specimen name] [tmin(kelvin)] [tmax(kelvin)]
        or 
        [specimen name] [tmin(Tesla)] [tmax(Tesla)]
        There is a problem with experiment that combines AF and thermal
        """
        dlg = wx.FileDialog(
            self, message="choose a file in a pmagpy redo format",
            defaultDir=self.WD, 
            defaultFile="demag_gui.redo",
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            redo_file = dlg.GetPath()
        dlg.Destroy()

        self.read_redo_file(redo_file)    
    

    #----------------------------------------------------------------------

    def clear_interpretations(self):
        
        for specimen in self.pmag_results_data['specimens'].keys():
            del(self.pmag_results_data['specimens'][specimen])
            for high_level_type in ['samples','sites','locations','study']:
                self.high_level_means[high_level_type]={}
    #----------------------------------------------------------------------
            
    def read_redo_file(self,redo_file):
        """
        Read previous interpretation from a redo file
        and update gui with the new interpretation
        """
        self.GUI_log.write ("-I- read redo file and processing new bounds")
        self.redo_specimens={}
        # first delete all previous interpretation
        self.clear_interpretations()
        fin=open(redo_file,'rU')
        
        for Line in fin.readlines():
            line=Line.strip('\n').split()
            specimen=line[0]
            tmin,tmax="",""
            if specimen in self.pmag_results_data['specimens'].keys() and 'DA-DIR' in self.pmag_results_data['specimens'][specimen].keys():
                print "-W- WARNING: more than one interpretations for specimen %s"%specimen
            calculation_type=line[1]
            if self.Data[specimen]['measurement_step_unit']=="C":
                if float(line[2])==0 or float(line[2])==273:
                    tmin="0"
                else:
                    tmin="%.0fC"%(float(line[2])-273)
                if float(line[3])==0 or float(line[3])==273:
                    tmax="0"
                else:
                    tmax="%.0fC"%(float(line[3])-273)
            elif self.Data[specimen]['measurement_step_unit']=="mT":
                if float(line[2])==0:
                    tmin="0"
                else:
                    tmin="%.1fmT"%(float(line[2])*1000)
                if float(line[3])==0:
                    tmax="0"
                else:
                    tmax="%.1fmT"%(float(line[3])*1000)
            else: # combimned experiment T:AF
                if float(line[2])==0:
                    tmin="0"
                elif "%.0fC"%(float(line[2])-273) in self.Data[specimen]['zijdblock_steps']:
                    tmin="%.0fC"%(float(line[2])-273)
                elif "%.1fmT"%(float(line[2])*1000) in self.Data[specimen]['zijdblock_steps']:
                    tmin="%.1fmT"%(float(line[2])*1000)
                else:
                    continue
                if float(line[3])==0:
                    tmax="0"
                elif "%.0fC"%(float(line[3])-273) in self.Data[specimen]['zijdblock_steps']:
                    tmax="%.0fC"%(float(line[3])-273)
                elif "%.1fmT"%(float(line[3])*1000) in self.Data[specimen]['zijdblock_steps']:
                    tmax="%.1fmT"%(float(line[3])*1000)
                else:
                    continue
            if tmin not in self.Data[specimen]['zijdblock_steps'] or  tmax not in self.Data[specimen]['zijdblock_steps']:
                print "-E- ERROR in redo file specimen %s. Cant find treatment steps"%specimen      
                                
            self.pmag_results_data['specimens'][specimen]={}             
            self.pmag_results_data['specimens'][specimen]['DA-DIR']=self.get_PCA_parameters(specimen,tmin,tmax,'specimen',calculation_type)
            if len(self.Data[specimen]['zijdblock_geo'])>0:      
                self.pmag_results_data['specimens'][specimen]['DA-DIR-GEO']=self.get_PCA_parameters(specimen,tmin,tmax,'geographic',calculation_type)                
            if len(self.Data[specimen]['zijdblock_tilt'])>0:      
                self.pmag_results_data['specimens'][specimen]['DA-DIR-TILT']=self.get_PCA_parameters(specimen,tmin,tmax,'tilt-corrected',calculation_type)                        
          
        fin.close()
        self.s=str(self.specimens_box.GetValue())
        self.calculate_higher_levels_data()
        self.update_selection()


    #----------------------------------------------------------------------

    def on_menu_save_interpretation(self,event):
        fout=open("demag_gui.redo",'w')
        specimens_list=self.pmag_results_data['specimens'].keys()
        specimens_list.sort()
        for specimen in specimens_list:
            if "DA-DIR" in self.pmag_results_data['specimens'][specimen].keys():
                STRING=specimen+"\t"
                STRING=STRING+self.pmag_results_data['specimens'][specimen]["DA-DIR"]["calculation_type"]+"\t"
                if self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_min']=="0":
                    tmin="0"
                elif "C" in self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_min']:
                    tmin="%.0f"%(float(self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_min'].split("C")[0])+273.)
                elif "mT" in self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_min']:
                    tmin="%.2e"%(float(self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_min'].split("mT")[0])/1000)
                if self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_max']=="0":
                    tmax="0"
                elif "C" in self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_max']:
                    tmax="%.0f"%(float(self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_max'].split("C")[0])+273.)
                elif "mT" in self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_max']:
                    tmax="%.2e"%(float(self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_max'].split("mT")[0])/1000)
                    
                STRING=STRING+tmin+"\t"+tmax+"\n"
                fout.write(STRING)
        TEXT="specimens interpretations are saved in demag_gui.redo"                
        dlg = wx.MessageDialog(self, caption="Saved",message=TEXT,style=wx.OK|wx.CANCEL )
        result = dlg.ShowModal()
        if result == wx.ID_OK:            
            dlg.Destroy()
               
     #----------------------------------------------------------------------
               
                
        
                
                                
    def on_menu_clear_interpretation(self,event):
        self.clear_interpretations()
        self.s=str(self.specimens_box.GetValue())
        self.update_selection()


    #----------------------------------------------------------------------
        
    def on_menu_change_criteria(self, event):
        dia=demag_dialogs.demag_criteria_dialog(None,self.acceptance_criteria,title='PmagPy Demag Gui Acceptance Criteria')
        dia.Center()
        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message            
            self.on_close_criteria_box(dia)
    
    def on_close_criteria_box (self,dia):
        
        window_list_specimens=['specimen_n','specimen_mad','specimen_dang','specimen_alpha95']
        window_list_samples=['sample_n','sample_n_lines','sample_n_planes','sample_k','sample_r','sample_alpha95']
        window_list_sites=['site_n','site_n_lines','site_n_planes','site_k','site_r','site_alpha95']
        demag_gui_supported_criteria= window_list_specimens+ window_list_samples+window_list_sites
        
        for crit in demag_gui_supported_criteria:
            command="new_value=dia.set_%s.GetValue()"%(crit) 
            exec command
            # empty box
            if new_value=="":
                self.acceptance_criteria[crit]['value']=-999
                continue
            # box with no valid number
            try:
                float(new_value)
            except:
                self.show_crit_window_err_messege(crit)
                continue
            self.acceptance_criteria[crit]['value']=float(new_value)
            
        #  message dialog
        dlg1 = wx.MessageDialog(self,caption="Warning:", message="Canges are saved to pmag_criteria.txt\n " ,style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            self.write_acceptance_criteria_to_file()
            dlg1.Destroy()    
            dia.Destroy()
        #self.recaclulate_satistics()
                
    # only valid naumber can be entered to boxes        
    def show_crit_window_err_messege(self,crit):
        '''
        error message if a valid naumber is not entered to criteria dialog boxes        
        '''
        dlg1 = wx.MessageDialog(self,caption="Error:",message="not a vaild value for statistic %s\n ignoring value"%crit ,style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            dlg1.Destroy()
            
    def write_acceptance_criteria_to_file(self):
        crit_list=self.acceptance_criteria.keys()
        crit_list.sort()
        rec={}
        rec['pmag_criteria_code']="ACCEPT"
        #rec['criteria_definition']=""
        rec['criteria_definition']="acceptance criteria for study"
        rec['er_citation_names']="This study"
                
        for crit in crit_list:
            if type(self.acceptance_criteria[crit]['value'])==str:
                if self.acceptance_criteria[crit]['value'] != "-999" and self.acceptance_criteria[crit]['value'] != "":
                    rec[crit]=self.acceptance_criteria[crit]['value']
            elif type(self.acceptance_criteria[crit]['value'])==int:
                if self.acceptance_criteria[crit]['value'] !=-999:
                    rec[crit]="%.i"%(self.acceptance_criteria[crit]['value'])
            elif type(self.acceptance_criteria[crit]['value'])==float:
                if float(self.acceptance_criteria[crit]['value'])==-999:
                    continue
                decimal_points=self.acceptance_criteria[crit]['decimal_points']
                if decimal_points != -999:
                    command="rec[crit]='%%.%sf'%%(self.acceptance_criteria[crit]['value'])"%(decimal_points)
                    exec command
                else:
                    rec[crit]="%e"%(self.acceptance_criteria[crit]['value'])
        pmag.magic_write(os.path.join(self.WD, "pmag_criteria.txt"),[rec],"pmag_criteria")
                
                
    #--------------------------------------------------------------
               
    def on_menu_criteria_file (self, event):
                   
        """
        read pmag_criteria.txt file
        and open changecriteria dialog
        """
        read_sucsess=False
        dlg = wx.FileDialog(
            self, message="choose pmag criteria file",
            defaultDir=self.WD, 
            defaultFile="pmag_criteria.txt",
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            criteria_file = dlg.GetPath()
            self.GUI_log.write ("-I- Read new criteria file: %s\n"%criteria_file)
            
            # check if this is a valid pmag_criteria file
            try:
                mag_meas_data,file_type=pmag.magic_read(criteria_file)
            except:
                dlg1 = wx.MessageDialog(self, caption="Error",message="not a valid pmag_criteria file",style=wx.OK)
                result = dlg1.ShowModal()
                if result == wx.ID_OK:            
                    dlg1.Destroy()
                dlg.Destroy()
                return

            # initialize criteria              
            self.acceptance_criteria=pmag.initialize_acceptance_criteria() 
            self.acceptance_criteria=pmag.read_criteria_from_file(criteria_file,self.acceptance_criteria) 
            read_sucsess=True
        
        dlg.Destroy()
        if read_sucsess:
            self.on_menu_change_criteria(None)   

    #--------------------------------------------------------------
    # Tools menu 
    #--------------------------------------------------------------

                                                            
    def on_menu_bulk_demagnetization (self,event):
        
        dlg1 = wx.MessageDialog(self, caption="message",message="tool not supported in this beta version",style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:            
            dlg1.Destroy()
                                     
    #--------------------------------------------------------------
    # MagIC menu 
    #--------------------------------------------------------------
    
    def  on_menu_make_MagIC_results_tables(self,event):

        #---------------------------------------            
        # 1. read pmag_specimens.txt, pmag_samples.txt, pmag_sites.txt, and sort out lines with LP-DIR in magic_codes 
        # 2. saves a clean pmag_*.txt files without LP-DIR stuff as pmag_*.txt.tmp .
        # 3. write a new file pmag_specimens.txt
        # 4. merge pmag_specimens.txt and pmag_specimens.txt.tmp using combine_magic.py 
        # 5. delete pmag_specimens.txt.tmp
        
        # 6 (optional) extracting new pag_*.txt files (except pmag_specimens.txt) using specimens_results_magic.py
        # 7: if #6: merge pmag_*.txt and pmag_*.txt.tmp using combine_magic.py 
        #    if not #6: save pmag_*.txt.tmp as pmag_*.txt
        #---------------------------------------            

        #---------------------------------------
        # save pmag_*.txt.tmp without directional data           
        #---------------------------------------  
        try:
            self.on_menu_save_interpretation(None)    
        except:
            pass    
        self.PmagRecsOld={}
        for FILE in ['pmag_specimens.txt']:
            self.PmagRecsOld[FILE]=[]
            try: 
                meas_data,file_type=pmag.magic_read(os.path.join(self.WD, FILE))
                self.GUI_log.write("-I- Read old magic file  %s\n"%os.path.join(self.WD, FILE))
                if FILE !='pmag_specimens.txt':
                    os.remove(os.path.join(self.WD,FILE))
                    self.GUI_log.write("-I- Delete old magic file  %s\n"%os.path.join(self.WD,FILE))
                               
            except:
                continue                                                                           
            for rec in meas_data:
                if "magic_method_codes" in rec.keys():
                    if "LP-DIR" not in rec['magic_method_codes'] and "DE-" not in  rec['magic_method_codes']:
                        self.PmagRecsOld[FILE].append(rec)
            #pmag.magic_write(self.WD+"/"+FILE+".tmp",PmagRecs,FILE.split(".")[0])
            #self.GUI_log.write("-I- Write magic file  %s\n"%self.WD+"/"+FILE+".tmp") 

        #---------------------------------------
        # write a new pmag_specimens.txt       
        #---------------------------------------  
                                  
        specimens_list=self.pmag_results_data['specimens'].keys()
        specimens_list.sort()
        PmagSpecs=[]
        for specimen in specimens_list:
            if 'DA-DIR' not in self.pmag_results_data['specimens'][specimen].keys() or self.pmag_results_data['specimens'][specimen]['DA-DIR']=={}:
                continue
            for dirtype in ['DA-DIR','DA-DIR-GEO','DA-DIR-TILT']:
                PmagSpecRec={}
                user="" # Todo
                PmagSpecRec["er_analyst_mail_names"]=user
                PmagSpecRec["magic_software_packages"]=pmag.get_version()
                PmagSpecRec["er_specimen_name"]=specimen
                PmagSpecRec["er_sample_name"]=self.Data_hierarchy['sample_of_specimen'][specimen]
                PmagSpecRec["er_site_name"]=self.Data_hierarchy['site_of_specimen'][specimen]
                PmagSpecRec["er_location_name"]=self.Data_hierarchy['location_of_specimen'][specimen]
                if specimen in self.Data_hierarchy['expedition_name_of_specimen'].keys():
                    PmagSpecRec["er_expedition_name"]=self.Data_hierarchy['expedition_name_of_specimen'][specimen]
                #else:
                #    PmagSpecRec["er_expedition_name"]=""
                PmagSpecRec["er_citation_names"]="This study"
                PmagSpecRec["magic_experiment_names"]=self.Data[specimen]["magic_experiment_name"]
                if 'magic_instrument_codes' in self.Data[specimen].keys():
                    PmagSpecRec["magic_instrument_codes"]= self.Data[specimen]['magic_instrument_codes']
                #magic_ood_codes=[]
                #all_methods=self.Data[specimen]['magic_method_codes'].strip('\n').replace(" ","").split(":")
                #for method in all_methods:
                #    if "LP" in method:
                #        magic_method_codes.append(method)
                #if 
                #-------
                OK=False
                if dirtype in self.pmag_results_data['specimens'][specimen].keys():
                    if  self.pmag_results_data['specimens'][specimen][dirtype]!={}:
                        OK=True
                if not OK:
                    continue
                #if self.Data[specimen]['measurement_step_unit']=="C":
                #     PmagSpecRec['measurement_step_unit']="K"
                #else:
                #     PmagSpecRec['measurement_step_unit']="T"
                    
                #PmagSpecRec['measurement_step_unit']=self.Data[specimen]['measurement_step_unit'] 
                PmagSpecRec['specimen_correction']='u'
                mpars=self.pmag_results_data['specimens'][specimen][dirtype]
                PmagSpecRec['specimen_direction_type'] = mpars["specimen_direction_type"]
                PmagSpecRec['specimen_dec'] = "%.1f"%mpars["specimen_dec"]
                PmagSpecRec['specimen_inc'] = "%.1f"%mpars["specimen_inc"]
                
                if  mpars['zijdblock_step_min'] =="0":
                     PmagSpecRec['measurement_step_min'] ="0"
                elif "C" in mpars['zijdblock_step_min']:
                    PmagSpecRec['measurement_step_min'] = "%.0f"%(mpars["measurement_step_min"]+273.)
                else:
                    PmagSpecRec['measurement_step_min'] = "%8.3e"%(mpars["measurement_step_min"]*1e-3)
                
                if  mpars['zijdblock_step_max'] =="0":
                     PmagSpecRec['measurement_step_max'] ="0"
                elif "C" in mpars['zijdblock_step_max']:
                    PmagSpecRec['measurement_step_max'] = "%.0f"%(mpars["measurement_step_max"]+273.)
                else:
                    PmagSpecRec['measurement_step_max'] = "%8.3e"%(mpars["measurement_step_max"]*1e-3)
                if "C" in   mpars['zijdblock_step_min']  or "C" in mpars['zijdblock_step_min']:
                    PmagSpecRec['measurement_step_unit']="K"
                else:
                    PmagSpecRec['measurement_step_unit']="T"                                  
                PmagSpecRec['specimen_n'] = "%.0f"%mpars["specimen_n"]
                calculation_type=mpars['calculation_type']
                PmagSpecRec["magic_method_codes"]=self.Data[specimen]['magic_method_codes']+":"+calculation_type+":"+dirtype
                if calculation_type in ["DE-BFL","DE-BFL-A","DE-BFL-O"]:
                    PmagSpecRec['specimen_direction_type']='l'
                    PmagSpecRec['specimen_mad']="%.1f"%float(mpars["specimen_mad"])
                    PmagSpecRec['specimen_dang']="%.1f"%float(mpars['specimen_dang'])
                    PmagSpecRec['specimen_alpha95']=""
                elif calculation_type in ["DE-BFP"]:
                    PmagSpecRec['specimen_direction_type']='p'
                    PmagSpecRec['specimen_mad']="%.1f"%float(mpars['specimen_mad'])
                    PmagSpecRec['specimen_dang']=""
                    PmagSpecRec['specimen_alpha95']=""
                elif calculation_type in ["DE-FM"]:
                    PmagSpecRec['specimen_direction_type']='l'
                    PmagSpecRec['specimen_mad']=""
                    PmagSpecRec['specimen_dang']=""
                    PmagSpecRec['specimen_alpha95']="%.1f"%float(mpars['specimen_alpha95'])
                if dirtype=='DA-DIR-TILT':
                    PmagSpecRec['specimen_tilt_correction']="100"
                elif dirtype=='DA-DIR-GEO':
                    PmagSpecRec['specimen_tilt_correction']="0"
                else:
                    PmagSpecRec['specimen_tilt_correction']="-1"
                PmagSpecs.append(PmagSpecRec)    
        # add the 'old' lines with no "LP-DIR" in 
        for rec in self.PmagRecsOld['pmag_specimens.txt']:
            PmagSpecs.append(rec)
        PmagSpecs_fixed=self.merge_pmag_recs(PmagSpecs)
        pmag.magic_write(os.path.join(self.WD, "pmag_specimens.txt"),PmagSpecs_fixed,'pmag_specimens')
        self.GUI_log.write( "specimen data stored in %s\n"%os.path.join(self.WD, "pmag_specimens.txt"))
        
        TEXT="specimens interpretations are saved in pmag_specimens.txt.\nPress OK for pmag_samples/pmag_sites/pmag_results tables."
        dlg = wx.MessageDialog(self, caption="Saved",message=TEXT,style=wx.OK|wx.CANCEL )
        result = dlg.ShowModal()
        if result == wx.ID_OK:            
            dlg.Destroy()
        if result == wx.ID_CANCEL:            
            dlg.Destroy()
            return
            
        #--------------------------------
                
        dia = demag_dialogs.magic_pmag_tables_dialog(None,self.WD,self.Data,self.Data_info)
        dia.Center()

        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message            
            self.On_close_MagIC_dialog(dia)
                                                      
    def On_close_MagIC_dialog(self,dia):
        # run specimens_results_magic.py

                
        #-- acceptance criteria
        #AGE_STR=""
        #if os.path.isfile(self.WD+"/er_ages.txt"):
        #    AGE_STR="-fa er_ages"
        #    print "YESS !"
        
        run_script_flags=["specimens_results_magic.py","-fsp","pmag_specimens.txt", "-xI",  "-WD", str(self.WD)]
        if dia.cb_acceptance_criteria.GetValue()==True:
            run_script_flags.append("-exc")
        else:
            run_script_flags.append("-C")

        #-- coordinate system
        if dia.rb_spec_coor.GetValue()==True:
            run_script_flags.append("-crd");  run_script_flags.append("s")       
        if dia.rb_geo_coor.GetValue()==True:
            run_script_flags.append("-crd");  run_script_flags.append("g")       
        if dia.rb_tilt_coor.GetValue()==True:
            run_script_flags.append("-crd");  run_script_flags.append("t")       
        if dia.rb_geo_tilt_coor.GetValue()==True:
            run_script_flags.append("-crd");  run_script_flags.append("b")       
        
        #-- default age options 
        if dia.cb_default_age.GetValue()==True:
            try:
                min_age="%f"%float(dia.default_age_min.GetValue()) 
                max_age="%f"%float(dia.default_age_max.GetValue())
            except:
                pass
            age_units= dia.default_age_unit.GetValue()       
            run_script_flags.append("-age"); run_script_flags.append(min_age)
            run_script_flags.append(max_age); run_script_flags.append(age_units)

        #-- sample mean 
        if dia.cb_sample_mean.GetValue()==True:
            run_script_flags.append("-aD") 
                
        if dia.cb_sample_mean_VGP.GetValue()==True:
            run_script_flags.append("-sam") 

        #-- site mean
         
        if dia.cb_site_mean.GetValue()==True:
            pass
            
        #-- location mean
         
        if dia.cb_location_mean.GetValue()==True:
            run_script_flags.append("-pol")

        for FILE in ['pmag_samples.txt','pmag_sites.txt','pmag_results.txt']:
            self.PmagRecsOld[FILE]=[]
            try: 
                meas_data,file_type=pmag.magic_read(os.path.join(self.WD, FILE))
                self.GUI_log.write("-I- Read old magic file  %s\n"%os.path.join(self.WD, FILE))
                if FILE !='pmag_specimens.txt':
                    os.remove(os.path.join(self.WD, FILE))
                    self.GUI_log.write("-I- Delete old magic file  %s\n"%os.path.join(self.WD,FILE))
                               
            except:
                continue                                                                           

            for rec in meas_data:
                if "magic_method_codes" in rec.keys():
                    if "LP-DIR" not in rec['magic_method_codes'] and "DE-" not in  rec['magic_method_codes']:
                        self.PmagRecsOld[FILE].append(rec)

                                                
        #print  run_script_flags
        outstring=" ".join(run_script_flags)
        print "-I- running python script:\n %s"%(outstring)
        os.system(outstring)
        #    subprocess.call(run_script_flags, shell=True)                
        # reads new pmag tables, and merge the old lines:
        for FILE in ['pmag_samples.txt','pmag_sites.txt','pmag_results.txt']:
            pmag_data=[]
            try:
                pmag_data,file_type=pmag.magic_read(os.path.join(self.WD,FILE))
            except:
                pass
            if FILE in self.PmagRecsOld.keys():
                for rec in self.PmagRecsOld[FILE]:
                    pmag_data.append(rec)
            if len(pmag_data) >0:
                pmag_data_fixed=self.merge_pmag_recs(pmag_data)
                pmag.magic_write(os.path.join(self.WD, FILE), pmag_data_fixed, FILE.split(".")[0])
                self.GUI_log.write( "write new interpretations in %s\n"%(os.path.join(self.WD, FILE)))

        # make pmag_criteria.txt if it does not exist
        if not os.path.isfile(os.path.join(self.WD, "pmag_criteria.txt")):
            Fout=open(os.path.join(self.WD, "pmag_criteria.txt"),'w')
            Fout.write("tab\tpmag_criteria\n")
            Fout.write("er_citation_names\tpmag_criteria_code\n")
            Fout.write("This study\tACCEPT\n")
            

        self.update_pmag_tables()
        self.update_selection()
        TEXT="interpretations are saved in pmag tables.\n"
        dlg = wx.MessageDialog(self, caption="Saved",message=TEXT,style=wx.OK)
        result = dlg.ShowModal()
        if result == wx.ID_OK:            
            dlg.Destroy()
                        
        self.close_warning=False       

    def merge_pmag_recs(self,old_recs):
        # fix the headers of pmag recs
        # make sure that all headers appear in all recs
        recs={}
        recs=copy.deepcopy(old_recs)
        headers=[]
        for rec in recs:
            for key in rec.keys():
                if key not in headers:
                    headers.append(key)
        for rec in recs:
            for header in headers:
                if header not in rec.keys():
                    #print "found a problmem in rec: ",rec
                    #print "missing: ", header
                    rec[header]=""
        return recs
            

                        
    def on_menu_MagIC_model_builder(self,event):
            
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
            
        #dia = MagIC_Model_Builder.MagIC_model_builder(self.WD,self.Data,self.Data_hierarchy)
        dia = MagIC_Model_Builder.MagIC_model_builder(self.WD)#,self.Data,self.Data_hierarchy)
        dia.Show()
        dia.Center()
        print "OK"
        #help_window.Close()
        self.Data,self.Data_hierarchy,self.Data_info={},{},{}
        self.Data_info=self.get_data_info() # get all ages, locations etc. (from er_ages, er_sites, er_locations)
        self.Data,self.Data_hierarchy=self.get_data() # Get data from magic_measurements and rmag_anistropy if exist.
        self.update_selection()                                    

    def on_menu_samples_orientation(self,event):
        TEXT="A template for file demag_orient.txt, which contains samples orientation data was created in MagIC working directory.\n\n"
        TEXT=TEXT+"You can view/modify the orientation data using the demag-gui frame, or using Excel.\n\n"
        TEXT=TEXT+"If you choose to use Excel:\n"
        TEXT=TEXT+"1) save demag_orient.txt as 'tab delimited'\n"
        TEXT=TEXT+"2) Import demag_orient.txt to the demag-gui frame by choosing from the menu-bar: File -> Open orientation file\n\n"
        TEXT=TEXT+"After filling orientation data choose from the menu-bar: File -> Calculate samples orientations"
              
        SIZE=self.GetSize()
        frame = demag_dialogs.OrientFrameGrid (None, -1, 'demag_orient.txt',self.WD,self.Data_hierarchy,SIZE)
        
        frame.Show(True)
        frame.Centre()
        dlg1 = wx.MessageDialog(self,caption="Message:", message=TEXT ,style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            dlg1.Destroy()    

                                                                                                                                                                                                        
    def on_menu_generic_to_magic(self,event):
        import demag_dialogs
        f=demag_dialogs.convert_generic_files_to_MagIC(self.WD)
        #def MyOnClose(evt):
        #    print "My onclose called"
        #    f.MakeModal(False)
        #    self.on_close_generic_file(self.WD)
        #    evt.Skip()
        #f.Bind(wx.EVT_CLOSE, MyOnClose)
        #f.MakeModal() 
        #if f.END==True:
        #    self.on_close_generic_file(self.WD)
        #    f.Close()
        #self.on_close_generic_file(self.WD)
   # def on_close_generic_file(self,WD):
   #     print "Closed"
   #     print WD    
        
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
#--------------------------------------------------------------    
# Save plots
#--------------------------------------------------------------

class SaveMyPlot(wx.Frame):
    """"""
    def __init__(self,fig,name,plot_type,dir_path):
        """Constructor"""
        wx.Frame.__init__(self, parent=None, title="")

        file_choices="(*.pdf)|*.pdf|(*.svg)|*.svg| (*.png)|*.png"
        default_fig_name="%s_%s.pdf"%(name,plot_type)
        dlg = wx.FileDialog(
            self, 
            message="Save plot as...",
            defaultDir=dir_path,
            defaultFile=default_fig_name,
            wildcard=file_choices,
            style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            
        title=name
        self.panel = wx.Panel(self)
        self.dpi=300

        canvas_tmp_1 = FigCanvas(self.panel, -1, fig)
        canvas_tmp_1.print_figure(path, dpi=self.dpi)  


        

#--------------------------------------------------------------    
# Run the GUI
#--------------------------------------------------------------
def alignToTop(win):
    dw, dh = wx.DisplaySize() 
    w, h = win.GetSize() 
    #x = dw - w
    #y = dh - h
    
    win.SetPosition(((dw-w)/2.,0 ))

#def resize(win):
#    dw, dh = wx.DisplaySize() 
#    w, h = win.GetSize()
#    if  dw>w:
#        #win.GUI_RESOLUTION=1.5
#        print "gui respoluyion"
    


def do_main(WD=None, standalone_app=True):
    # to run as module:
    if not standalone_app:
        frame = Zeq_GUI(WD)
        frame.Center()
        frame.Show()

    # to run as command_line:
    else:
        app = wx.PySimpleApp()
        app.frame = Zeq_GUI(WD)
        app.frame.Center()
        #alignToTop(app.frame)
        dw, dh = wx.DisplaySize() 
        w, h = app.frame.GetSize()
        #print 'display 2', dw, dh
        #print "gui 2", w, h
        app.frame.Show()
        app.MainLoop()

if __name__ == '__main__':
    do_main()
