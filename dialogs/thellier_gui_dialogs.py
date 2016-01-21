#!/usr/bin/env python

#============================================================================================
# LOG HEADER:
#  
# Dialogs boxes for thellier_gui.py
#
#============================================================================================
#
#  11/16/2014 add some units to criteria dialogs
#
# 11/08/2014 Version add k_prime description
#
# 08/08/2014 Version add k_prime description
#
# 3/22/2014 Version 1.0 by Ron Shaar
#
#
#============================================================================================

#--------------------------------------------------------------    
# Thellier GUI dialog
#--------------------------------------------------------------

import matplotlib
#matplotlib.use('WXAgg')
import wx
import copy
import os
import scipy
from scipy import arange
# only this one is nessesary.
import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas \

import pmagpy.pmag as pmag
#--------------------------------------------------------------    
# paleointensity statistics list (SPD.v.1.0)
#--------------------------------------------------------------

class PI_Statistics_Dialog(wx.Dialog):

    def __init__(self, parent, show_statistics_on_gui,title):
        style =  wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER  
        super(PI_Statistics_Dialog, self).__init__(parent, title=title,style=style)
        self.show_statistics_on_gui=copy.copy(show_statistics_on_gui)

        self.stat_by_category={}
        
        self.stat_by_category['Arai plot']=['specimen_int_n',
        'specimen_frac','specimen_f','specimen_fvds',
        'specimen_b_sigma','specimen_b_beta','specimen_scat',
        'specimen_g','specimen_gmax',
        'specimen_k','specimen_k_sse',
        'specimen_k_prime','specimen_k_prime_sse',
        'specimen_z','specimen_z_md',
        'specimen_q',
        'specimen_r_sq','specimen_coeff_det_sq',      
        ]
        self.stat_by_category['Direction']=['specimen_int_mad','specimen_int_mad_anc','specimen_int_dang','specimen_int_alpha','specimen_alpha_prime','specimen_theta','specimen_int_crm','specimen_gamma']
        self.stat_by_category['pTRM Checks']=['specimen_int_ptrm_n','specimen_ptrm','specimen_drat','specimen_drats','specimen_cdrat','specimen_mdrat',
        'specimen_dck','specimen_maxdev','specimen_mdev','specimen_dpal']
        self.stat_by_category['Tail Checks']=['specimen_int_ptrm_tail_n','specimen_md','specimen_tail_drat','specimen_dtr','specimen_dt']
        self.stat_by_category['Additivity Checks']=['specimen_ac_n','specimen_dac']
        self.DESC={}
        self.DESC['specimen_frac']='The angle between the applied field direction and the ChRM direction of the NRM as determined from the free-floating PCA fit to the selected demagnetization steps of the paleointensity experiment'
        self.DESC['specimen_int_n']='Number of measurements included in field strength calculations'
        self.DESC['specimen_alpha_prime']='Angular difference between the anchored best-fit direction from the paleointensity experiment and an independent measure of the paleomagnetic direction'
        self.DESC['specimen_alpha']='Angular difference between the anchored and free-floating best-fit directions on a vector component diagram'
        self.DESC['specimen_int_alpha']='Angular difference between the anchored and free-floating best-fit directions on a vector component diagram from a paleointensity experiment'
        self.DESC['specimen_mad']='Maximum Angular Deviation (MAD) of the free-floating directional PCA fits to the paleomagnetic vector'
        self.DESC['specimen_mad_anc']='Maximum Angular Deviation (MAD) of the anchored directional PCA fits to the paleomagnetic vector'
        self.DESC['specimen_int_mad']='Maximum Angular Deviation (MAD) of the free-floating directional PCA fits to the paleomagnetic vector from a paleointensity experiment'
        self.DESC['specimen_int_mad_anc']='Maximum Angular Deviation (MAD) of the anchored directional PCA fits to the paleomagnetic vector from a paleointensity experiment'
        self.DESC['specimen_w']='Weighting factor'
        self.DESC['specimen_q']='A measure of the overall quality of the paleointensity estimate and combines the relative scatter of the best-fit line, the NRM fraction and the gap factor'
        self.DESC['specimen_f']='NRM fraction used for the best-fit on an Arai plot '
        self.DESC['specimen_fvds']='NRM fraction used for the best-fit on an Arai plot calculated as a vector difference sum'
        self.DESC['specimen_b']='The slope of the best-fit line of the selected TRM and NRM points on an Arai plot'
        self.DESC['specimen_b_sigma']='The standard error on the slope on an Arai plot'
        self.DESC['specimen_b_beta']='The ratio of the standard error of the slope to the absolute value of the slope on an Arai plot'
        self.DESC['specimen_g']='The gap reflects the average spacing of the selected Arai plot points along the best-fit line'
        self.DESC['specimen_gmax']='The maximum gap between two points in Arai plot determined by vector arithmetic'
        self.DESC['specimen_r_sq']='The squared correlation coefficient to estimate the strength of the linear relationship between the NRM and TRM over the best-fit Arai plot segment'
        self.DESC['specimen_coeff_det_sq']='The squared coefficient of determination to estimate variance accounted for by the linear model fit on an Arai plot'
        self.DESC['specimen_dang']='Deviation angle of direction of component with respect to origin'
        self.DESC['specimen_int_dang']='The angle between the free-floating best-fit direction and the vector connecting the center of mass and the origin of the vector component diagram'
        self.DESC['specimen_int_crm']='The cumulative deflection between the NRM vectors and the ChRM direction'
        self.DESC['specimen_int_ptrm_tail_n']='Number of pTRM tail checks used in paleointensity experiment'
        self.DESC['specimen_md']='Maximum absolute difference produced by a pTRM tail check, normalized by the vector difference sum of the NRM'
        self.DESC['specimen_tail_drat']='Maximum absolute difference produced by a pTRM tail check, normalized by the length of the best-fit line'
        self.DESC['specimen_dtr']='Maximum absolute difference produced by a pTRM tail check, normalized by the NRM (obtained from the intersection of the best-fit line and the y-axis on an Arai plot)'
        self.DESC['specimen_int_ptrm_n']='Number of pTRM checks used in paleointensity experiment'
        self.DESC['specimen_ptrm']='Maximum absolute difference produced by a pTRM check, normalized by the TRM acquired at that heating step'
        self.DESC['specimen_dck']='Maximum absolute difference produced by a pTRM check, normalized by the total TRM (obtained from the intersection of the best-fit line and the x-axis on an Arai plot)'
        self.DESC['specimen_maxdev']='Maximum absolute difference produced by a pTRM check, normalized by the length of the TRM segment of the best-fit line on an Arai plot'
        self.DESC['specimen_drat']='Maximum absolute difference produced by a pTRM check, normalized by the length of the best-fit line'
        self.DESC['specimen_mdrat']='The average difference produced by a pTRM check, normalized by the length of the best-fit line'
        self.DESC['specimen_cdrat']='Cumulative difference ratio difference produced by a pTRM check'
        self.DESC['specimen_drats']='Cumulative pTRM check difference normalized by the pTRM gained at the maximum temperature used for the best-fit on the Arai plot'
        self.DESC['specimen_mdev']='Mean deviation of a pTRM check'
        self.DESC['specimen_dpal']='A measure of cumulative alteration determined by the difference of the alteration corrected intensity estimate (Valet et al., 1996) and the uncorrected estimate, normalized by the uncorrected estimate (Leonhardt et al., 2004a)'
        self.DESC['specimen_dt']='The extent of a pTRM tail after correction for angular dependence'
        self.DESC['specimen_dac']='The maximum absolute additivity check difference normalized by the total TRM (obtained from the intersection of the best-fit line and the x-axis on an Arai plot'
        self.DESC['specimen_ac_n']='The number of additivity checks used to analyze the best-fit segment on an Arai plot'
        self.DESC['specimen_k']='The curvature of the Arai plot as determined by the best-fit circle to all of the data '
        self.DESC['specimen_k_sse']='The quality of the best-fit circle used to determine k'
        self.DESC['specimen_k_prime']='The curvature of the Arai plot as determined by the best-fit circle to the selected data points'
        self.DESC['specimen_k_prime_sse']='The quality of the best-fit circle used to determine k_prime'
        self.DESC['specimen_z']='Arai plot zigzag parameter calculated using the scatter around the best-fit slope on an Arai plot'
        self.DESC['specimen_z_md']='Arai plot zigzag parameter calculated by the area bounded by the curve that the ZI points make and the curve that the IZ points make'
        self.DESC['specimen_scat']='All pTRM checks, MD checks, IZ ZI data, etc. are in the box (g = good or b=bad)'
        self.DESC['specimen_viscosity_index']='Viscosity index'
        self.DESC['specimen_lab_field_dc']='Applied DC field in laboratory'
        self.DESC['specimen_lab_field_ac']='Applied maximum or peak AC field in laboratory'
        self.DESC['specimen_magn_moment']='Measured magnetic moment'
        self.DESC['specimen_magn_volume']='Measured intensity of magnetization, Volume normalized'
        self.DESC['specimen_magn_mass']='Measured intensity of magnetization, Mass normalized'
        self.DESC['specimen_int_corr_cooling_rate']='Cooling rate correction factor for intensity'
        self.DESC['specimen_int_corr_anisotropy']='Anisotropy correction factor for intensity'
        self.DESC['specimen_int_corr_nlt']='Non-linear TRM correction factor for intensity'
        self.DESC['specimen_delta']='Maximum angle of deviation between assumed NRM and measured NRM in perpendicular paleointensity method'
        self.DESC['specimen_theta']='The angle between the applied field direction and the ChRM direction of the NRM as determined from the free-floating PCA fit to the selected demagnetization steps of the paleointensity experiment'
        self.DESC['specimen_gamma']='Maximum angle of deviation between acquired pTRM direction and assumed applied field direction'
        self.InitUI()
        self.initialize_stat()
    def InitUI(self):

        pnl1 = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        #============================        
        # design the panel
        #============================        

        #---------------------------
        # sizer 1
        # Specimen criteria
        #---------------------------

        categories=['Arai plot','Direction','pTRM Checks','Tail Checks','Additivity Checks']
        for k in range(len(categories)):
            command = "bSizer%i = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, '%s' ), wx.VERTICAL )"%(k,categories[k])
            exec command
            
            for stat in self.stat_by_category[categories[k]]:
                short_name=stat.replace("specimen_","")
                command="self.set_specimen_%s=wx.CheckBox(pnl1,-1,label='%s',name='%s')"%(short_name,short_name,short_name)
                exec command
                command = "self.Bind(wx.EVT_CHECKBOX, self.OnCheckBox, self.set_specimen_%s)"%(short_name)
                exec command                
                command="self.specimen_%s_button = wx.Button(pnl1, -1, label='description',name='%s')" %(short_name,stat)
                exec command
                command = "self.Bind(wx.EVT_BUTTON,self.PI_stat_description, self.specimen_%s_button)"%(short_name)
                exec command
                
            for i in range(len(self.stat_by_category[categories[k]])):
                command="hbox_%i= wx.BoxSizer(wx.HORIZONTAL)"%i
                exec command
                stat=self.stat_by_category[categories[k]][i]
                short_name=stat.replace("specimen_","")
                command="hbox_%i.Add(self.specimen_%s_button)"%(i,short_name)
                exec command
                command="hbox_%i.AddSpacer(10)"%(i)
                exec command
                
                command="hbox_%i.Add(self.set_specimen_%s)"%(i,short_name)
                exec command
                command="bSizer%i.Add(hbox_%i)"%(k,i)
                exec command
                command="bSizer%i.AddSpacer(10)"%k
                exec command
        #self.specimen_int_n_button.Bind(wx.EVT_BUTTON, lambda evt, name=specimen_int_n_button.GetLabel(): self.onButton(evt, name)        
        #self.Bind(wx.EVT_BUTTON,self.PI_stat_description, self.specimen_int_n_button)
        #---------------------------
        # OK / CANCEL
        #---------------------------

        hbox_OK_CANCEL = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(pnl1, wx.ID_OK, "&OK")
        self.cancelButton = wx.Button(pnl1, wx.ID_CANCEL, '&Cancel')
        hbox_OK_CANCEL.Add(self.okButton)
        hbox_OK_CANCEL.AddSpacer(10)
        hbox_OK_CANCEL.Add(self.cancelButton )

        #============================        
        # arrange sizers
        #============================   
             
             
        hbox= wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddSpacer(10)
        hbox.Add(bSizer0, flag=wx.ALIGN_CENTER_HORIZONTAL)
        hbox.AddSpacer(10)
        hbox.Add(bSizer1, flag=wx.ALIGN_CENTER_HORIZONTAL)
        hbox.AddSpacer(10)
        hbox.Add(bSizer2, flag=wx.ALIGN_CENTER_HORIZONTAL)
        hbox.AddSpacer(10)
        hbox.Add(bSizer3, flag=wx.ALIGN_CENTER_HORIZONTAL)
        hbox.AddSpacer(10)
        hbox.Add(bSizer4, flag=wx.ALIGN_CENTER_HORIZONTAL)
        hbox.AddSpacer(10)            
                                    
        vbox.AddSpacer(10)
        vbox.Add(hbox, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(hbox_OK_CANCEL, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
                    
        pnl1.SetSizer(vbox)
        vbox.Fit(self)


    def initialize_stat(self):
        categories=['Arai plot','Direction','pTRM Checks','Tail Checks','Additivity Checks']
        for short_name in self.show_statistics_on_gui:
            for category in categories:
                if "specimen_" + short_name in self.stat_by_category[category]:
                    command="self.set_specimen_%s.SetValue(True)"%short_name
                    exec command
                    
                    

    def PI_stat_description(self,event):
        button = event.GetEventObject()
        crit=button.GetName()
        TEXT=self.DESC[crit]
        TEXT=TEXT+"\n\n"
        TEXT=TEXT+"For more details see:\n http://www.paleomag.net/SPD"
        dlg1 = wx.MessageDialog(None,caption=crit, message=TEXT ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()
        
    def OnCheckBox(self,event):
        checkbox= event.GetEventObject()
        if checkbox.GetValue()==True:
            crit=str(checkbox.GetName())
            if crit not in self.show_statistics_on_gui:
                self.show_statistics_on_gui.append(crit)
        if checkbox.GetValue()==False:
            crit=str(checkbox.GetName())
            if crit in self.show_statistics_on_gui:
                self.show_statistics_on_gui.remove(crit)
        
        # arrange_all_statistics in order:
        tmp_list=copy.copy(self.show_statistics_on_gui)
        self.show_statistics_on_gui=[]
        categories=['Arai plot','Direction','pTRM Checks','Tail Checks','Additivity Checks']
        for category in categories:
            for stat in self.stat_by_category[category]:
                short_name=str(stat.replace("specimen_",""))
                if short_name in tmp_list:
                    self.show_statistics_on_gui.append(short_name)


#--------------------------------------------------------------    
# Change Acceptance criteria dialog
#--------------------------------------------------------------



class Criteria_Dialog(wx.Dialog):

    def __init__(self, parent, acceptance_criteria,preferences,title):
        style =  wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER  
        super(Criteria_Dialog, self).__init__(parent, title=title,style=style)
        self.acceptance_criteria=acceptance_criteria
        self.preferences=preferences
        self.InitUI()



    def InitUI(self):


        pnl1 = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)


        #============================        
        # design the panel
        #============================        

        #---------------------------
        # sizer 1
        # Specimen criteria
        #---------------------------

        bSizer1 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "specimen acceptance criteria" ), wx.HORIZONTAL )
        
        hbox_criteria = wx.BoxSizer(wx.HORIZONTAL)
        window_list_specimens=self.preferences['show_statistics_on_gui']
        
        for stat in window_list_specimens:
            if stat=='scat':
                self.set_specimen_scat=wx.CheckBox(pnl1, -1, '')
            else:
                command="self.set_specimen_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%stat
                exec command
            command="self.%s_label=wx.StaticText(pnl1,label='%s',style=wx.ALIGN_CENTRE)"%(stat,stat.replace("specimen_",""))
            exec command
            
            command="gs_%s = wx.GridSizer(2, 1,5,5)"%stat
            exec command            
            command="gs_%s.AddMany( [(self.%s_label,wx.EXPAND),(self.set_specimen_%s,wx.EXPAND)])"%(stat,stat,stat)
            exec command
            command="bSizer1.Add(gs_%s,flag=wx.ALIGN_LEFT)"%stat
            exec command
            bSizer1.AddSpacer(12)

                
                                                
        #criteria_specimen_window = wx.GridSizer(2, 14, 6, 6)
        #criteria_specimen_window.AddMany( [(wx.StaticText(pnl1,label="int_n",style=wx.TE_CENTER), wx.EXPAND),
        #    (wx.StaticText(pnl1,label="int_ptrm_n",style=wx.TE_CENTER), wx.EXPAND),
        #    (wx.StaticText(pnl1,label="FRAC",style=wx.TE_CENTER), wx.EXPAND),
        #    (wx.StaticText(pnl1,label="SCAT",style=wx.TE_CENTER), wx.EXPAND),
        #    (wx.StaticText(pnl1,label="gap_max",style=wx.TE_CENTER), wx.EXPAND),
        #    (wx.StaticText(pnl1,label="f",style=wx.TE_CENTER), wx.EXPAND),
        #    (wx.StaticText(pnl1,label="fvds",style=wx.TE_CENTER), wx.EXPAND),
        #    (wx.StaticText(pnl1,label="beta",style=wx.TE_CENTER), wx.EXPAND),
        #    (wx.StaticText(pnl1,label="g",style=wx.TE_CENTER), wx.EXPAND),
        #    (wx.StaticText(pnl1,label="q",style=wx.TE_CENTER), wx.EXPAND),
        #    (wx.StaticText(pnl1,label="MAD",style=wx.TE_CENTER), wx.EXPAND),
        #    (wx.StaticText(pnl1,label="DANG",style=wx.TE_CENTER), wx.EXPAND),
        #    (wx.StaticText(pnl1,label="DRATS",style=wx.TE_CENTER), wx.EXPAND),
        #    (wx.StaticText(pnl1,label="MD tail",style=wx.TE_CENTER), wx.EXPAND),
        #    (self.set_specimen_int_n),
        #    (self.set_specimen_int_ptrm_n),
        #    (self.set_specimen_frac),
        #    (self.set_specimen_scat),                        
        #    (self.set_specimen_gmax),
        #    (self.set_specimen_f),
        #    (self.set_specimen_fvds),
        #    (self.set_specimen_b_beta),
        #    (self.set_specimen_g),
        #    (self.set_specimen_q),
        #    (self.set_specimen_int_mad),
        #    (self.set_specimen_int_dang),
        #    (self.set_specimen_drats),                                
        #    (self.set_specimen_md)])
                                           

        # bSizer1.Add( criteria_specimen_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

        #---------------------------
        # anistropy criteria
        #---------------------------

        bSizer1a = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "anisotropy criteria" ), wx.HORIZONTAL )
        self.set_anisotropy_alt=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))
        #self.set_anisotropy_ftest=wx.ComboBox(self.panel, -1, value='None', choices=["None","pass 95%"],style=wx.CB_DROPDOWN,name="aniso-ftest")
        self.set_anisotropy_ftest_flag= wx.CheckBox(pnl1, -1, '', (10, 10))
        criteria_aniso_window = wx.GridSizer(2, 2, 6, 6)
        criteria_aniso_window.AddMany( [(wx.StaticText(pnl1,label="use F test as acceptance criteria",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="alteration check (%)",style=wx.TE_CENTER), wx.EXPAND),
            (self.set_anisotropy_ftest_flag),
            (self.set_anisotropy_alt)])

        bSizer1a.Add( criteria_aniso_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )


        #---------------------------
        # sample/site criteria
        #---------------------------

        bSizer2 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "sample/Site acceptance criteria" ), wx.HORIZONTAL )
    
        self.set_average_by_sample_or_site=wx.ComboBox(pnl1, -1,size=(150, -1), value = 'sample', choices=['sample','site'], style=wx.CB_READONLY)
        
        # Sample criteria
        window_list_samples=['int_n','int_n_outlier_check']
        for key in window_list_samples:
            command="self.set_sample_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        criteria_sample_window = wx.GridSizer(2, 3, 6, 6)
        criteria_sample_window.AddMany( [(wx.StaticText(pnl1,label="averge by sample/site",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_n",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_n_outlier_check",style=wx.TE_CENTER), wx.EXPAND),
            (self.set_average_by_sample_or_site),            
            (self.set_sample_int_n),
            (self.set_sample_int_n_outlier_check)])

        bSizer2.Add( criteria_sample_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )


        #---------------------------
        # thellier interpreter calculation type
        #---------------------------


        bSizer2a = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "mean calculation algorithm" ), wx.HORIZONTAL )
    

        self.set_stdev_opt=wx.RadioButton(pnl1, -1, '', (10, 10), style=wx.RB_GROUP)
        self.set_bs=wx.RadioButton(pnl1, -1, ' ', (10, 30))
        self.set_bs_par=wx.RadioButton(pnl1, -1, '', (50, 50))
        self.set_include_nrm= wx.CheckBox(pnl1, -1, '', (10, 10))
        criteria_sample_window = wx.GridSizer(2, 4, 6, 6)
        criteria_sample_window.AddMany( [(wx.StaticText(pnl1,label="Enable STDEV-OPT",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="Enable BS",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="Enable BS_PAR",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="include NRM",style=wx.TE_CENTER), wx.EXPAND),
            (self.set_stdev_opt),            
            (self.set_bs),
            (self.set_bs_par),
            (self.set_include_nrm)])

        bSizer2a.Add( criteria_sample_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )


        #---------------------------
        # sample/site criteria
        #---------------------------


        bSizer3 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "sample/site acceptance criteria: STDEV-OPT" ), wx.HORIZONTAL )
        # Sample STEV-OPT
        window_list_samples=['int_sigma_uT','int_sigma_perc','int_interval_uT','int_interval_perc','aniso_mean']
        for key in window_list_samples:
            command="self.set_sample_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        
        criteria_sample_window_2 = wx.GridSizer(2, 5, 6, 6)
        criteria_sample_window_2.AddMany( [(wx.StaticText(pnl1,label="int_sigma_uT",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_sigma_perc",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_interval",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_interval_perc",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="sample aniso mean (%)",style=wx.TE_CENTER), wx.EXPAND),
            (self.set_sample_int_sigma_uT),
            (self.set_sample_int_sigma_perc),
            (self.set_sample_int_interval_uT),
            (self.set_sample_int_interval_perc),
            (self.set_sample_aniso_mean)])

        bSizer3.Add( criteria_sample_window_2, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

        
        #---------------------------
        # bootstrap criteria
        #---------------------------

        bSizer4 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "sample Acceptance criteria: BS / BS-PAR" ), wx.HORIZONTAL )
        window_list_samples=['int_BS_68_uT','int_BS_68_perc','int_BS_95_uT','int_BS_95_perc']
        for key in window_list_samples:
            command="self.set_sample_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        # for bootstarp
        self.set_specimen_int_max_slope_diff=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))
        
        criteria_sample_window_3 = wx.GridSizer(2, 5, 6, 6)
        criteria_sample_window_3.AddMany( [(wx.StaticText(pnl1,label="specimen_int_max_slope_diff",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_BS_68_uT",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_BS_68_perc",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_BS_95_uT",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_BS_95_perc",style=wx.TE_CENTER), wx.EXPAND),                                           
            (self.set_specimen_int_max_slope_diff),                                           
            (self.set_sample_int_BS_68_uT),
            (self.set_sample_int_BS_68_perc),
            (self.set_sample_int_BS_95_uT),
            (self.set_sample_int_BS_95_perc)])

        bSizer4.Add( criteria_sample_window_3, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

        #---------------------------
        # OK / CANCEL
        #---------------------------

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(pnl1, wx.ID_OK, "&OK")
        self.cancelButton = wx.Button(pnl1, wx.ID_CANCEL, '&Cancel')
        hbox3.Add(self.okButton)
        hbox3.AddSpacer(10)
        hbox3.Add(self.cancelButton )
        
        #============================        
        # Intialize values
        #============================        
        
        for key in window_list_specimens:
            command="self.set_specimen_%s.SetBackgroundColour(wx.NullColour)"%key
        exec command


        #-------------------------------------------        
        # Intialize values: specimen criteria window
        #-------------------------------------------        

        #criteria_list_for_window=['specimen_gmax','specimen_b_beta','specimen_int_dang','specimen_drats','specimen_int_mad','specimen_md']+\
        #['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']
        
        criteria_list_for_window=self.preferences['show_statistics_on_gui']
        for crit in criteria_list_for_window:
            value=""
            crit="specimen_"+crit
            if crit!="specimen_scat":
                if self.acceptance_criteria[crit]['value']==-999:
                    value=""
                elif type(self.acceptance_criteria[crit]['threshold_type'])==list:
                    if type(self.acceptance_criteria[crit]['value'])==str:
                        value=self.acceptance_criteria[crit]['value']
                elif type(self.acceptance_criteria[crit]['value'])==float or  type(self.acceptance_criteria[crit]['value'])==int:
                    if self.acceptance_criteria[crit]['decimal_points']!=-999:
                        command="value='%%.%if'%%(self.acceptance_criteria[crit]['value'])"%int(self.acceptance_criteria[crit]['decimal_points'])
                        exec command
                    else:
                        value="%.3e"%(self.acceptance_criteria[crit]['value'])
    
                command="self.set_%s.SetValue(value)"%crit
    
                exec command
            else:    
                if self.acceptance_criteria['specimen_scat']['value'] in [True,1,"True","TRUE","1","1.0",'g']:
                    self.set_specimen_scat.SetValue(True)
                    
                else:
                    self.set_specimen_scat.SetValue(False)

        #-------------------------------------------        
        # Intialize values: anisotropy window
        #-------------------------------------------        
        
        crit="anisotropy_alt"
        if self.acceptance_criteria[crit]['value']==-999:
            value=""
        else:
            command="value='%%.%if'%%(self.acceptance_criteria[crit]['value'])"%int(self.acceptance_criteria[crit]['decimal_points'])
            exec command
        self.set_anisotropy_alt.SetValue(value) 

        crit="anisotropy_ftest_flag"        
        if self.acceptance_criteria[crit]['value'] in [True,1,"True","TRUE","1","1.0",'g']:
            self.set_anisotropy_ftest_flag.SetValue(True)
        else:
            self.set_anisotropy_ftest_flag.SetValue(False)
            
        #-------------------------------------------        
        # Intialize values: avearge by site or sample
        #-------------------------------------------        
        if 'average_by_sample_or_site' not in self.acceptance_criteria.keys():self.acceptance_criteria['average_by_sample_or_site']['value']='site' 
        if str(self.acceptance_criteria['average_by_sample_or_site']['value'])=='site':
            self.set_average_by_sample_or_site.SetStringSelection('site')           
        else:
            self.set_average_by_sample_or_site.SetStringSelection('sample')           

        #-------------------------------------------        
        # Intialize values: sample/site criteria method codes
        #-------------------------------------------        
       
        if self.acceptance_criteria['interpreter_method']=="bs":
            self.set_bs.SetValue(True) 
        elif self.acceptance_criteria['interpreter_method']=="bs_par":
            self.set_bs_par.SetValue(True) 
        else:
            self.set_stdev_opt.SetValue(True) 

        #-------------------------------------------        
        # Intialize values: include NRM
        #-------------------------------------------        
        self.set_include_nrm.SetValue(True)         
        #-------------------------------------------        
        # Intialize values: sample/site criteria
        #------------------------------------------- 
               
        criteria_list_for_window=[]+\
        ['sample_int_n','sample_int_sigma','sample_int_sigma_perc','sample_int_n_outlier_check']+\
        ['site_int_n','site_int_sigma','site_int_sigma_perc','site_int_n_outlier_check']+\
        ['sample_aniso_mean','site_aniso_mean']+\
        ['sample_int_interval_uT','sample_int_interval_perc']+\
        ['sample_int_BS_68_uT','sample_int_BS_95_uT','sample_int_BS_68_perc','sample_int_BS_95_perc']
        
        for crit in criteria_list_for_window:
            
            # check if averaging by site or sample
            if self.acceptance_criteria['average_by_sample_or_site']['value']=='site':
                if 'sample' in crit:
                    continue
            else:
                if 'site' in crit:
                    continue
                
            #--------------
            # get the value to write         
            if self.acceptance_criteria[crit]['value']==-999:
                value=""            
            elif crit in ['sample_int_sigma','site_int_sigma']:
                value="%.1f"%(float(self.acceptance_criteria[crit]['value'])*1e6)
            elif type(self.acceptance_criteria[crit]['value'])==float or type(self.acceptance_criteria[crit]['value'])==int :
                command="value='%%.%if'%%(self.acceptance_criteria[crit]['value'])"%int(self.acceptance_criteria[crit]['decimal_points'])
                exec command
            elif type(self.acceptance_criteria[crit]['value'])==bool:
                 value="%.s"%str(self.acceptance_criteria[crit]['value'])
            elif type(self.acceptance_criteria[crit]['value'])==str:
                 value=str(self.acceptance_criteria[crit]['value'])
            #-------
            
            # write the value to box       
            
            
            if str(self.acceptance_criteria['average_by_sample_or_site']['value'])=='site':
                if crit in ['site_int_n','site_int_sigma_perc','site_int_n_outlier_check','site_aniso_mean']:
                    command="self.set_%s.SetValue(value)"%(crit.replace('site','sample'))
                    exec command
                if crit in ['site_int_sigma']:
                    command="self.set_%s_uT.SetValue(value)"%(crit.replace('site','sample'))
                    exec command
            else:
                if crit in ['sample_int_sigma']:
                    command="self.set_%s_uT.SetValue(value)"%crit
                else:
                    command="self.set_%s.SetValue(value)"%crit
                exec command
                         
                                  
            
                    
        
        #============================        
        # arrange sizers
        #============================   
             
        vbox.AddSpacer(10)
        vbox.Add(bSizer1, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer1a, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer2, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer2a, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer3, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer4, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(hbox3, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
                    
        pnl1.SetSizer(vbox)
        vbox.Fit(self)


#--------------------------------------------------------------    
# Show a table
#--------------------------------------------------------------

class MyForm(wx.Frame):
    """"""
 
    #----------------------------------------------------------------------
    def __init__(self,number_of_rows_to_ignore,file_name):
        """Constructor"""
        wx.Frame.__init__(self, parent=None, title=file_name.split('/')[-1])
        
        panel = wx.Panel(self)

        self.read_the_file(file_name)
        
        self.myGrid = wx.grid.Grid(panel)
        self.myGrid.CreateGrid(len(self.report)-number_of_rows_to_ignore-1, len(self.report[number_of_rows_to_ignore]))
        index=0
        for i in range(len(self.report[number_of_rows_to_ignore])):
          self.myGrid.SetColLabelValue(i, self.report[number_of_rows_to_ignore][i])
        for i in range(1+number_of_rows_to_ignore,len(self.report)):
          for j in range(len(self.report[i])):
            self.myGrid.SetCellValue(index,j, self.report[i][j])
          index+=1
        self.myGrid.SetLabelFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial'))
        self.myGrid.SetDefaultCellFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial'))

        
        self.myGrid.AutoSize()
        #myGrid.SetRowLabelSize(0)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.myGrid, 1, wx.EXPAND)
        #sizer.Fit(self)
        panel.SetSizer(sizer)



    def  read_the_file(self,file_name):                    

##        dlg = wx.FileDialog(
##            self, message="choose a file in a pmagpy redo format",
##            style=wx.OPEN | wx.CHANGE_DIR
##            )
##        if dlg.ShowModal() == wx.ID_OK:
##            interpreter_output= dlg.GetPath()
##        dlg.Destroy()

        fin=open(str(file_name),'rU')
        self.report=[]
        for L in fin.readlines():
          line=L.strip('\n').split('\t')
          self.report.append(line)


#--------------------------------------------------------------    
# Save plots
#--------------------------------------------------------------

class SaveMyPlot(wx.Frame):
    """"""
    def __init__(self,fig,pars,plot_type):
        """Constructor"""
        wx.Frame.__init__(self, parent=None, title="")

        file_choices="(*.pdf)|*.pdf|(*.svg)|*.svg| (*.png)|*.png"
        default_fig_name="%s_%s.pdf"%(pars['er_specimen_name'],plot_type)
        dlg = wx.FileDialog(
            self, 
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile=default_fig_name,
            wildcard=file_choices,
            style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            
        title=pars['er_specimen_name']
        self.panel = wx.Panel(self)
        self.dpi=300

        canvas_tmp_1 = FigCanvas(self.panel, -1, fig)
        canvas_tmp_1.print_figure(path, dpi=self.dpi)  

#----------------------------------------------------------------------

#===========================================================
# Consistency Test
#===========================================================
    

class Consistency_Test(wx.Frame):
    """"""
    
    #----------------------------------------------------------------------
    def __init__(self,Data,Data_hierarchy,WD,acceptance_criteria,preferences,Thermal,Microwave):
        wx.Frame.__init__(self, parent=None)
        """
        """
        import thellier_consistency_test        
        self.WD=WD
        self.Data=Data
        self.Data_hierarchy=Data_hierarchy
        self.acceptance_criteria=acceptance_criteria
        self.preferences=preferences
        self.panel = wx.Panel(self)
        self.make_fixed_criteria()
        self.init_optimizer_frame()  
        global THERMAL
        global MICROWAVE
        THERMAL = Thermal
        MICROWAVE =  Microwave           

    def make_fixed_criteria(self):

        Text="Choose fixed acceptance criteria"
        
        dlg = wx.MessageDialog(self, Text, caption="First step", style=wx.OK )
        dlg.ShowModal(); dlg.Destroy()
        #self.fixed_criteria['specimen_frac']=0
        #self.fixed_criteria['specimen_b_beta']=10000000
        
        dia = Criteria_Dialog(None, self.acceptance_criteria,self.preferences,title='Set fixed_criteria_file')
        dia.Center()

        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message            
            self.On_close_fixed_criteria_box(dia)
        

    def On_close_fixed_criteria_box(self,dia):
        
        """
        after criteria dialog window is closed. 
        Take the acceptance criteria values and update
        self.acceptance_criteria
        """
        
        criteria_list=self.acceptance_criteria.keys()
        criteria_list.sort()
        
        #---------------------------------------
        # check if averaging by sample or by site
        # and intialize sample/site criteria
        #---------------------------------------
        
        if dia.set_average_by_sample_or_site.GetValue()=='sample':
            for crit in ['site_int_n','site_int_sigma','site_int_sigma_perc','site_aniso_mean','site_int_n_outlier_check']:
                self.acceptance_criteria[crit]['value']=-999
        if dia.set_average_by_sample_or_site.GetValue()=='site':
            for crit in ['sample_int_n','sample_int_sigma','sample_int_sigma_perc','sample_aniso_mean','sample_int_n_outlier_check']:
                self.acceptance_criteria[crit]['value']=-999

        #---------
        
        for i in range(len(criteria_list)):            
            crit=criteria_list[i]
            #---------
            # get the "value" from dialog box
            #---------
                # dealing with sample/site
            if dia.set_average_by_sample_or_site.GetValue()=='sample':
                if crit in ['site_int_n','site_int_sigma','site_int_sigma_perc','site_aniso_mean','site_int_n_outlier_check']:
                    continue
            if dia.set_average_by_sample_or_site.GetValue()=='site':
                if crit in ['sample_int_n','sample_int_sigma','sample_int_sigma_perc','sample_aniso_mean','sample_int_n_outlier_check']:
                    continue
            #------
            if crit in ['site_int_n','site_int_sigma_perc','site_aniso_mean','site_int_n_outlier_check']:
                command="value=dia.set_%s.GetValue()"%crit.replace('site','sample')                
            
            elif crit=='sample_int_sigma' or crit=='site_int_sigma':
                #command="value=float(dia.set_sample_int_sigma_uT.GetValue())*1e-6"            
                command="value=dia.set_%s.GetValue()"%crit
            else:
                command="value=dia.set_%s.GetValue()"%crit
            #------
            try:
                exec command
            except:
                continue
            
            #---------
            # write the "value" to self.acceptance_criteria
            #---------
                        
            if crit=='average_by_sample_or_site': 
                self.acceptance_criteria[crit]['value']=str(value)
                continue 
            if type(value)==bool and value==True:
                self.acceptance_criteria[crit]['value']=True
            elif type(value)==bool and value==False:
                self.acceptance_criteria[crit]['value']=-999                        
            elif type(value)==unicode and str(value)=="":
                self.acceptance_criteria[crit]['value']=-999
            elif type(value)==unicode and str(value)!="": # should be a number
                try:
                    self.acceptance_criteria[crit]['value']=float(value)
                except:
                    self.show_messege(crit) 
            elif type(value)==float or type(value)==int:
               if  crit=='sample_int_sigma' or crit=='site_int_sigma':
                    self.acceptance_criteria[crit]['value']=float(value)*1e-6
               else:
                    self.acceptance_criteria[crit]['value']=float(value)                             
            else:  
                self.show_messege(crit)
        #---------
        # thellier interpreter calculation type
        if dia.set_stdev_opt.GetValue()==True:
            self.acceptance_criteria['interpreter_method']['value']='stdev_opt'
        elif  dia.set_bs.GetValue()==True:
            self.acceptance_criteria['interpreter_method']['value']='bs'            
        elif  dia.set_bs_par.GetValue()==True:
            self.acceptance_criteria['interpreter_method']['value']='bs_par'            
            
                
            
        #  message dialog
        dlg1 = wx.MessageDialog(self,caption="Warning:", message="changes are saved to consistency_test/pmag_fixed_criteria.txt\n " ,style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:

            try:
                new_dir = os.path.join(self.WD, "consistency_test")
                os.mkdir(new_dir)
            except:
                pass

            #try:
            #    self.clear_boxes()
            #except:
            #    pass
            #try:
            #    self.write_acceptance_criteria_to_boxes()
            #except:
            #    pass
            ofile = os.path.join(self.WD, "consistency_test/pmag_fixed_criteria.txt")
            pmag.write_criteria_to_file(ofile, self.acceptance_criteria)
            dlg1.Destroy()    
            dia.Destroy()
        #self.recaclulate_satistics()
        
    # only valid naumber can be entered to boxes
    # used by On_close_criteria_box         
    def show_messege(self,key):
        dlg1 = wx.MessageDialog(self,caption="Error:",
            message="non-vaild value for box %s"%key ,style=wx.OK)
        #dlg1.ShowModal()
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            dlg1.Destroy()


        
    def init_optimizer_frame(self):

        Text="Set Consistency Test function parameters"
        dlg = wx.MessageDialog(self, Text, caption="Second step", style=wx.OK )
        dlg.ShowModal(); dlg.Destroy()

        """ Build main frame od panel: buttons, etc.
            choose the first specimen and display data
        """
        # import wx.lib.agw.floatspin as FS

        stat_list=self.preferences['show_statistics_on_gui']
        if "scat" in stat_list:
            stat_list.remove("scat")
        self.stat_1 = wx.ComboBox(self.panel, -1, value="", choices=stat_list, style=wx.CB_DROPDOWN,name="stat_1")
        self.stat_1_low = wx.TextCtrl(self.panel,style=wx.TE_CENTER,size=(50,20))
        self.stat_1_high = wx.TextCtrl(self.panel,style=wx.TE_CENTER,size=(50,20))
        self.stat_1_delta = wx.TextCtrl(self.panel,style=wx.TE_CENTER,size=(50,20))

        self.stat_2 = wx.ComboBox(self.panel, -1, value="", choices=stat_list, style=wx.CB_DROPDOWN,name="stat_2")
        self.stat_2_low = wx.TextCtrl(self.panel,style=wx.TE_CENTER,size=(50,20))
        self.stat_2_high = wx.TextCtrl(self.panel,style=wx.TE_CENTER,size=(50,20))
        self.stat_2_delta = wx.TextCtrl(self.panel,style=wx.TE_CENTER,size=(50,20))
        

        
        beta_window = wx.GridSizer(2, 4, 5, 10)
        beta_window.AddMany( [(wx.StaticText(self.panel,label="statistic",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="start value",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="end value",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="delta",style=wx.TE_CENTER), wx.EXPAND),
            (self.stat_1, wx.EXPAND),
            (self.stat_1_low, wx.EXPAND) ,
            (self.stat_1_high, wx.EXPAND) ,
            (self.stat_1_delta, wx.EXPAND) ])

        scat_window = wx.GridSizer(2, 4, 5, 10)
        
        scat_window.AddMany( [(wx.StaticText(self.panel,label="statistic",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="start value",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="end value",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="delta",style=wx.TE_CENTER), wx.EXPAND),
            (self.stat_2, wx.EXPAND) ,
            (self.stat_2_low, wx.EXPAND) ,
            (self.stat_2_high, wx.EXPAND) ,
            (self.stat_2_delta, wx.EXPAND) ])
        Text1="insert functions in the text window below, each function in a seperate line.\n"
        Text2="Use a valid python syntax with logic or arithmetic operators\n (see example functions)\n\n"
        Text3="List of legal operands:\n"
        Text4="study_sample_n:  Total number of samples in the study that pass the criteria\n"
        Text5="test_group_n:  Number of test groups that have at least one sample that passed acceptance criteria\n" 
        Text6="max_group_int_sigma_uT:  standard deviation of the group with the maximum scatter \n"
        Text7="max_group_int_sigma_perc:  standard deviation of the group with the maximum scatter divided by its mean (in unit of %)\n\n"
        Text8="Check \"Check function syntax\" when done inserting functions.\n\n" 
                    
        self.function_label = wx.StaticText(self.panel, label=Text1+Text2+Text3+Text4+Text5+Text6+Text7+Text8,style=wx.ALIGN_CENTRE)

        # text_box 
        self.text_logger = wx.TextCtrl(self.panel, id=-1, size=(800,200), style= wx.HSCROLL|wx.TE_MULTILINE)
        self.Bind(wx.EVT_TEXT,self.on_change_function,self.text_logger)

        # check function button 
        self.check_button = wx.Button(self.panel, id=-1, label='Check function syntax')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.Bind(wx.EVT_BUTTON, self.on_check_button, self.check_button)

        # check function status 
        self.check_status=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))

        # group definition  button 
#        self.optimizer_make_groups_next_button = wx.Button(self.panel, id=-1, label='Next')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
#        self.Bind(wx.EVT_BUTTON, self.on_optimizer_make_groups_next_button, self.optimizer_make_groups_next_button)
        self.open_existing_optimizer_group_file = wx.Button(self.panel,id=-1, label='Choose a test group file')
        self.Bind(wx.EVT_BUTTON, self.on_open_existing_optimizer_group_file, self.open_existing_optimizer_group_file)

        self.optimizer_group_file_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(800,20))

        #self.make_new_optimizer_group_file = wx.Button(self.panel,id=-1, label='make new group definition file')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        #self.Bind(wx.EVT_BUTTON, self.on_make_new_optimizer_group_file, self.make_new_optimizer_group_file)

        # Cancel  button 
        self.cancel_optimizer_button = wx.Button(self.panel, id=-1, label='Cancel')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.Bind(wx.EVT_BUTTON, self.on_cancel_optimizer_button, self.cancel_optimizer_button)

        self.run_optimizer_button = wx.Button(self.panel, id=-1, label='Run Consistency Test')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.Bind(wx.EVT_BUTTON, self.on_run_optimizer_button, self.run_optimizer_button)

        # put an example
        try:
            ofile = os.path.join(self.WD, "consistency_test", "consistency_test_functions.txt")
            function_in=open(ofile, 'rU')
            TEXT=""
            for line in function_in.readlines():
                TEXT=TEXT+line
        except:
            TEXT="study_sample_n\ntest_group_n\nmax_group_int_sigma_uT\nmax_group_int_sigma_perc\n((max_group_int_sigma_uT < 6) or (max_group_int_sigma_perc < 10)) and  int(study_sample_n)"

        self.text_logger.SetValue(TEXT)
            
        #TEXT=Text1+Text2+Text3+Text4+Text5+Text6+Text7+Text8

        #self.text_logger.SetValue()

        box=wx.BoxSizer(wx.wx.HORIZONTAL)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1a = wx.BoxSizer(wx.HORIZONTAL)
        hbox1b = wx.BoxSizer(wx.HORIZONTAL)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4a = wx.BoxSizer(wx.HORIZONTAL)
        hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        hbox6 = wx.BoxSizer(wx.HORIZONTAL)
        hbox7 = wx.BoxSizer(wx.HORIZONTAL)
        hbox8 = wx.BoxSizer(wx.HORIZONTAL)


        hbox1a.AddSpacer(10)
        hbox1a.Add(beta_window,flag=wx.ALIGN_CENTER_VERTICAL,border=2)
        hbox1a.AddSpacer(10)

        hbox1b.AddSpacer(10)
        hbox1b.Add(scat_window,flag=wx.ALIGN_CENTER_VERTICAL,border=2)
        hbox1b.AddSpacer(10)

        hbox2.Add(self.function_label,flag=wx.ALIGN_CENTER_VERTICAL,border=2)

        hbox3.Add(self.text_logger,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)        

        hbox4.Add(self.check_button,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)
        hbox4a.Add(self.check_status,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)
        #hbox4.AddSpacer(50)
    
        #hbox6.Add(self.optimizer_make_groups_next_button,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)
        hbox5.Add(self.open_existing_optimizer_group_file,flag=wx.ALIGN_LEFT)
        hbox6.Add(self.optimizer_group_file_window,flag=wx.ALIGN_LEFT)

        hbox7.Add(self.run_optimizer_button,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)

        hbox8.Add(self.cancel_optimizer_button,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)

        vbox.AddSpacer(30)
        vbox.Add(hbox1a, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.AddSpacer(30)
        vbox.Add(hbox1b, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.AddSpacer(30)
        vbox.Add(hbox2, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.Add(hbox3, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.Add(hbox4, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.Add(hbox4a, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.Add(hbox5, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.Add(hbox6, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.AddSpacer(10)
        vbox.Add(hbox7, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.AddSpacer(10)
        vbox.Add(hbox8, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.AddSpacer(30)

        box.AddSpacer(30)
        box.AddSpacer(vbox)
        box.AddSpacer(30)
        
        self.panel.SetSizer(box)
        box.Fit(self)
        
        self.Show()
        self.Centre()


    def on_cancel_optimizer_button (self,event):
        self.Destroy()

    def on_check_button(self,event):
        S1=self.text_logger.GetValue()
        func=S1.split('\n')
        study_sample_n,test_group_n,max_group_int_sigma_uT,max_group_int_sigma_perc,max_sample_accuracy_uT,max_sample_accuracy_perc=10,10.,0.1,0.1,1,0.1
        functions=[]
        OK=True
        for f in func:
            try:
                exec f
            except:
                OK=False
                #  message dialog
                dlg1 = wx.MessageDialog(self, message="Error in function line %i"%(func.index(f)) ,style=wx.OK)
                result = dlg1.ShowModal()
                #if result == wx.ID_OK:
                #    d.Destroy()
        if OK:
            self.check_status.SetValue("PASS")
        else:
            self.check_status.SetValue("FAIL")

    def on_change_function (self,event):
            self.check_status.SetValue("")
         


    #def on_make_new_optimizer_group_file(self,event):
    def on_open_existing_optimizer_group_file(self,event):
        
        dirname=self.WD 
            
        dlg = wx.FileDialog(self, "Choose a test groups file", dirname, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            self.optimizer_group_file_path=dlg.GetPath()
        ignore_n=1
        self.optimizer_group_file_window.SetValue(self.optimizer_group_file_path)
            
    def on_run_optimizer_button( self,event):
        if self.optimizer_group_file_window.GetValue() != "" and self.check_status.GetValue()=="PASS":
            stat1=str("specimen_"+str(self.stat_1.GetValue()))
            stat1_start=float(self.stat_1_low.GetValue())
            stat1_end=float(self.stat_1_high.GetValue())
            stat1_delta=float(self.stat_1_delta.GetValue())
            
            stat2=str("specimen_"+str(self.stat_2.GetValue()))
            stat2_start=float(self.stat_2_low.GetValue())
            stat2_end=float(self.stat_2_high.GetValue())
            stat2_delta=float(self.stat_2_delta.GetValue())

            FILE = os.path.join(self.WD, "consistency_test", "consistency_test_functions.txt")
            optimizer_function_file=open(FILE, 'w')
            TEXT=self.text_logger.GetValue()
            optimizer_function_file.write(TEXT)
            optimizer_function_file.close()

            gframe=wx.BusyInfo("Running Thellier Consistency Test\n It may take a while ....", self)

            optimizer_functions_path="/consistency_test/consistency_test_functions.txt"
            criteria_fixed_paremeters_file="/consistency_test/pmag_fixed_criteria.txt"
  
            stat1_range=[stat1,arange(stat1_start,stat1_end,stat1_delta)]
            stat2_range=[stat2,arange(stat2_start,stat2_end,stat2_delta)]
                      
            #beta_range=arange(beta_start,beta_end,beta_step)
            #frac_range=arange(frac_start,frac_end,beta_step)
            #try:
            import thellier_consistency_test
            thellier_consistency_test.run_thellier_consistency_test(self.WD, self.Data,self.Data_hierarchy,self.acceptance_criteria,self.optimizer_group_file_path,optimizer_functions_path,self.preferences,stat1_range,stat2_range,THERMAL,MICROWAVE)
            #except:
            #    dlg1 = wx.MessageDialog(self,caption="Error:", message="Optimizer finished with Errors" ,style=wx.OK)
                
            #tmp.Thellier_optimizer(self.WD, self.Data,self.optimizer_group_file_path,optimizer_functions_path,beta_range,frac_range)

##            optimizer_output=open(self.WD+"/optimizer/thellier_optimizer.log",'w')
##
##            Command_line=["thellier_optimizer_2d.py","-WD",self.WD,"-optimize_by_list",self.optimizer_group_file_path,\
##                                 "-optimization_functions","/optimizer/optimizer_functions.txt"\
##                                 ,"-beta_range","%.2f,%.2f,%.2f"%(beta_start,beta_end,beta_step),"-f_range","%.2f,%.2f,%.2f"%(frac_start,frac_end,frac_step)]
##            try:
##                subprocess.check_call(Command_line,stdout=optimizer_output)
##                dlg1 = wx.MessageDialog(self,caption="Message:", message="Optimizer finished sucsessfuly\nCheck folder optimizer in working directory" ,style=wx.OK|wx.ICON_INFORMATION)
##                
##            except:
##                dlg1 = wx.MessageDialog(self,caption="Error:", message="Optimizer finished with Errors" ,style=wx.OK)
            

            dlg1 = wx.MessageDialog(self,caption="Message:", message="Consistency Test finished sucsessfuly\nCheck folder consistency_test in working directory" ,style=wx.OK|wx.ICON_INFORMATION)
            dlg1.ShowModal()
            dlg1.Destroy()
            gframe.Destroy()
        

#--------------------------------------------------------------


            
#--------------------------------------------------------------    
# Ploting  dialog
#--------------------------------------------------------------

class Plot_Dialog(wx.Dialog):

    def __init__(self,parent,WD,Data,Data_info):
        super(Plot_Dialog, self).__init__(parent, title="plot paleointensity data")
        self.InitUI()
        #self.SetSize((250, 200))

    def InitUI(self):

        pnl1 = wx.Panel(self)
        
        vbox = wx.BoxSizer(wx.VERTICAL)

        #-----------   
        #-----------        

        bSizer1 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Age axis" ), wx.HORIZONTAL )
        
        window_list_commands=["age_min","age_max",]
        for key in window_list_commands:
            command="self.set_plot_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        self.set_x_axis_auto=wx.CheckBox(pnl1, -1, '', (50, 50))
        self.set_x_axis_auto.SetValue(True)

        self.set_age_unit=wx.ComboBox(pnl1, -1, 'Automatic',choices=['Automatic','Years AD (+/-)','Years BP','Ka','Ma','Ga'],style=wx.CB_DROPDOWN)
        
        #self.set_plot_year = wx.RadioButton(pnl1, -1, 'timescale = date (year)', (10, 10), style=wx.RB_GROUP)
        # self.set_plot_BP = wx.RadioButton(pnl1, -1, 'timescale = BP ', (10, 30))
        #self.set_plot_year.SetValue(True)
        
        Plot_age_window = wx.GridSizer(2, 4, 12, 12)
        Plot_age_window.AddMany( [(wx.StaticText(pnl1,label="age unit",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="auto scale",style=wx.TE_CENTER), wx.EXPAND),                                  
            (wx.StaticText(pnl1,label="younger bound",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="older bound",style=wx.TE_CENTER), wx.EXPAND),
            (self.set_age_unit),
            #(self.set_plot_BP),                                  
            (self.set_x_axis_auto),
            (self.set_plot_age_min),
            (self.set_plot_age_max)])
                                           
        bSizer1.Add( Plot_age_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

        #-----------   
        #-----------        


        bSizer2 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Intensity axis" ), wx.HORIZONTAL )
        
        window_list_commands=["intensity_min","intensity_max"]
        for key in window_list_commands:
            command="self.set_plot_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        self.set_y_axis_auto=wx.CheckBox(pnl1, -1, '', (50, 50))
        self.set_plot_B = wx.RadioButton(pnl1, -1, 'B (microT)', (10, 10), style=wx.RB_GROUP)
        self.set_plot_VADM = wx.RadioButton(pnl1, -1, 'VADM (ZAm^2)', (10, 30))

        self.set_y_axis_auto.SetValue(True)
        self.set_plot_VADM.SetValue(True)
        
        Plot_intensity_window = wx.GridSizer(2, 5, 12, 12)
        Plot_intensity_window.AddMany( [(wx.StaticText(pnl1,label="",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="auto scale",style=wx.TE_CENTER), wx.EXPAND),                                        
            (wx.StaticText(pnl1,label="min value",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="max value",style=wx.TE_CENTER), wx.EXPAND),
            (self.set_plot_B),
            (self.set_plot_VADM),
            (self.set_y_axis_auto),                        
            (self.set_plot_intensity_min),
            (self.set_plot_intensity_max)])
                                           
        bSizer2.Add( Plot_intensity_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

        #-----------  



        bSizer3 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "more plot options" ), wx.HORIZONTAL )
        
        self.show_samples_ID=wx.CheckBox(pnl1, -1, '', (50, 50))
        self.show_x_error_bar=wx.CheckBox(pnl1, -1, '', (50, 50))
        self.show_y_error_bar=wx.CheckBox(pnl1, -1, '', (50, 50))
        self.show_STDEVOPT=wx.CheckBox(pnl1, -1, '', (50, 50))
        self.show_STDEVOPT_extended=wx.CheckBox(pnl1, -1, '', (50, 50))
        
        self.show_samples_ID.SetValue(True)
        self.show_x_error_bar.SetValue(True)
        self.show_y_error_bar.SetValue(True)
        self.show_STDEVOPT.SetValue(False)
        self.show_STDEVOPT_extended.SetValue(False)
        bsizer_3_window = wx.GridSizer(2, 5, 12, 12)
        bsizer_3_window.AddMany( [(wx.StaticText(pnl1,label="show sample labels",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="show x error bars",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="show y error bars",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="show STDEV-OPT means",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="show STDEV-OPT error bounds",style=wx.TE_CENTER), wx.EXPAND),
            (self.show_samples_ID),
            (self.show_x_error_bar),
            (self.show_y_error_bar),                                              
            (self.show_STDEVOPT),
            (self.show_STDEVOPT_extended)])
                                           
        bSizer3.Add( bsizer_3_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

        #-----------  




        bSizer4 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Location map" ), wx.HORIZONTAL )
        
        self.show_map=wx.CheckBox(pnl1, -1, '', (50, 50))
        self.show_map.SetValue(False)
        self.set_map_autoscale=wx.CheckBox(pnl1, -1, '', (50, 50))
        self.set_map_autoscale.SetValue(True)

        window_list_commands=["lat_min","lat_max","lat_grid","lon_min","lon_max","lon_grid"]
        for key in window_list_commands:
            command="self.set_map_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        bsizer_4_window = wx.GridSizer(2, 8, 12, 12)

        bsizer_4_window.AddMany( [(wx.StaticText(pnl1,label="show location map",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="auto scale",style=wx.TE_CENTER), wx.EXPAND),                      
            (wx.StaticText(pnl1,label="lat min",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="lat max",style=wx.TE_CENTER), wx.EXPAND),                                        
            (wx.StaticText(pnl1,label="lat grid",style=wx.TE_CENTER), wx.EXPAND),                                        
            (wx.StaticText(pnl1,label="lon min",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="lon max",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="lon grid",style=wx.TE_CENTER), wx.EXPAND),
            (self.show_map),
            (self.set_map_autoscale),
            (self.set_map_lat_min),
            (self.set_map_lat_max),                        
            (self.set_map_lat_grid),                        
            (self.set_map_lon_min),
            (self.set_map_lon_max),
            (self.set_map_lon_grid)])

        
                                           
        bSizer4.Add( bsizer_4_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

        #-----------  


        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(pnl1, wx.ID_OK, "&OK")
        self.cancelButton = wx.Button(pnl1, wx.ID_CANCEL, '&Cancel')
        hbox2.Add(self.okButton)
        hbox2.Add(self.cancelButton )
        #self.okButton.Bind(wx.EVT_BUTTON, self.OnOK)
        #-----------  

        
        #----------------------  
        vbox.AddSpacer(20)
        vbox.Add(bSizer1, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
        vbox.Add(bSizer2, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
        vbox.Add(bSizer3, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
        vbox.Add(bSizer4, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)

        vbox.Add(hbox2, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
                    
        pnl1.SetSizer(vbox)
        vbox.Fit(self)
        

#--------------------------------------------------------------    
# Show a logfile erros
#--------------------------------------------------------------

class MyLogFileErrors(wx.Frame):
    """"""
 
    #----------------------------------------------------------------------
    def __init__(self,title,file_path):
        wx.Frame.__init__(self, parent=None,size=(1000,500))
        
        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.text_log = wx.TextCtrl(self.panel, id=-1, style=wx.TE_MULTILINE | wx.TE_READONLY  | wx.HSCROLL)
        self.sizer.Add(self.text_log, 1, wx.EXPAND)

        fin =open(file_path,'rU')
        for line in fin.readlines():
            if "-E-" in line :
                self.text_log.SetDefaultStyle(wx.TextAttr(wx.RED))
                self.text_log.AppendText(line)
            if "-W-" in line:
                self.text_log.SetDefaultStyle(wx.TextAttr(wx.BLACK))
                self.text_log.AppendText(line)
        fin.close()
        #sizer.Fit(self)
        self.panel.SetSizer(self.sizer)

    

#--------------------------------------------------------------    
# MagIC generic files conversion
#--------------------------------------------------------------


class convert_generic_files_to_MagIC(wx.Frame):
    """"""
    title = "PmagPy Thellier GUI generic file conversion"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.Panel(self)
        self.max_files=10
        self.WD=WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        #---sizer infor ----

        TEXT1="Generic thellier GUI file is a tab-delimited file with the following headers:\n"
        TEXT2="Specimen  Treatment  Declination  Inclination  Moment\n"
        TEXT3="Treatment: XXX.Y or XXX.YY where XXX is temperature in C, and YY is treatment code. See tutorial for explenation. NRM step is 000.00\n" 
        TEXT4="Moment: In units of emu.\n"

        TEXT=TEXT1+TEXT2+TEXT3+TEXT4
        bSizer_info = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.HORIZONTAL )
        bSizer_info.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)
            

        #---sizer 0 ----
        TEXT="File:\n Choose measurement file\n No spaces are alowd in path"
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

        TEXT="\n\nExperiment:"
        bSizer1 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        bSizer1.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        self.experiments_names=['IZZI','IZ','ZI','ATRM 6 positions','cooling rate','NLT']
        bSizer1.AddSpacer(5)
        for i in range(self.max_files):
            command="self.protocol_info_%i = wx.ComboBox(self.panel, -1, self.experiments_names[0], size=(100,25), choices=self.experiments_names, style=wx.CB_DROPDOWN)"%i
            #command="self.protocol_info_%i = wx.TextCtrl(self.panel, id=-1, size=(100,20), style=wx.TE_MULTILINE | wx.HSCROLL)"%i
            #print command
            exec command
            command="bSizer1.Add(self.protocol_info_%i,wx.ALIGN_TOP)"%i        
            exec command
            bSizer1.AddSpacer(5)

        #---sizer 2 ----

        TEXT="Blab:\n(microT dec inc)\nexample: 40 0 -90 "
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

        TEXT="\nUser\nname:"
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

        #self.add_file_button =  wx.Button(self.panel, id=-1, label='add file')
        #self.Bind(wx.EVT_BUTTON, self.on_add_file_button, self.add_file_button)

        #self.remove_file_button =  wx.Button(self.panel, id=-1, label='remove file')

                     
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
            #print l
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
        os.chdir(self.WD)

        #-----------------------------------
        # Prepare MagIC measurement file
        #-----------------------------------

        # prepare output file
        magic_headers=['er_citation_names','er_specimen_name',"er_sample_name","er_site_name",'er_location_name','er_analyst_mail_names',\
                       "magic_instrument_codes","measurement_flag","measurement_standard","magic_experiment_name","magic_method_codes","measurement_number",'treatment_temp',"measurement_dec","measurement_inc",\
                       "measurement_magn_moment","measurement_temp","treatment_dc_field","treatment_dc_field_phi","treatment_dc_field_theta"]             

        fout=open("magic_measurements.txt",'w')        
        fout.write("tab\tmagic_measurements\n")
        header_string=""
        for i in range(len(magic_headers)):
            header_string=header_string+magic_headers[i]+"\t"
        fout.write(header_string[:-1]+"\n")

        #-----------------------------------
            
        Data={}
        header_codes=[]
        ERROR=""
        datafiles=[]
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
            Magic_lab_protocols['IZZI'] = "LP-PI-TRM:LP-PI-BT-IZZI"
            Magic_lab_protocols['IZ'] = "LP-PI-TRM:LP-PI-TRM-IZ"
            Magic_lab_protocols['ZI'] = "LP-PI-TRM:LP-PI-TRM-ZI"
            Magic_lab_protocols['ATRM 6 positions'] = "LP-AN-TRM" # LT-T-I:
            Magic_lab_protocols['cooling rate'] = "LP-CR-TRM" # LT-T-I:
            Magic_lab_protocols['NLT'] = "LP-TRM" # LT-T-I:
            #------------------------------

            for specimen in this_file_data.keys():
                measurement_running_number=0
                this_specimen_teratments=[]
                for meas_line in this_file_data[specimen]:
                    MagRec={}
                    #
                    MagRec["er_specimen_name"]=meas_line['Specimen']
                    MagRec['er_citation_names']="This study"
                    MagRec["er_sample_name"]=self.get_sample_name(MagRec["er_specimen_name"],sample_naming_convenstion)
                    MagRec["er_site_name"]=self.get_site_name(MagRec["er_sample_name"],site_naming_convenstion)
                    MagRec['er_location_name']=""
                    MagRec['er_analyst_mail_names']=user_name 
                    MagRec["magic_instrument_codes"]="" 
                    MagRec["measurement_flag"]='g'
                    MagRec["measurement_number"]="%i"%measurement_running_number
                    MagRec['treatment_temp']="%.2f"%(float(meas_line['Treatment'].split(".")[0])+273.)
                    MagRec["measurement_dec"]=meas_line["Declination"]
                    MagRec["measurement_inc"]=meas_line["Inclination"]
                    MagRec["measurement_magn_moment"]='%10.3e'%(float(meas_line["Moment"])*1e-3) # in Am^2
                    MagRec["measurement_temp"]='273.' # room temp in kelvin
                    MagRec["treatment_dc_field"]='%8.3e'%(float(labfield[0])*1e-6)
                    MagRec["treatment_dc_field_phi"]="%.2f"%(float(labfield[1]))
                    MagRec["treatment_dc_field_theta"]="%.2f"%(float(labfield[2]))
                    MagRec["measurement_standard"]="u"
                    MagRec["magic_experiment_name"]=MagRec["er_specimen_name"]+":"+Magic_lab_protocols[experiment]

                    this_specimen_teratments.append(float(meas_line['Treatment']))                    
                    # fill in LP and LT
                    lab_protocols_string=Magic_lab_protocols[experiment]
                    tr_temp=float(meas_line['Treatment'].split(".")[0])
                    if len(meas_line['Treatment'].split("."))==1:
                        tr_tr=0
                    else:
                        tr_tr=float(meas_line['Treatment'].split(".")[1])
                    
                    # identify the step in the experiment from Experiment_Type,
                    # IZ/ZI/IZZI
                    if experiment in ['IZZI','IZ','ZI']:
                        if float(tr_temp)==0:
                            lab_treatment="LT-NO" # NRM
                        elif float(tr_tr)==0:                            
                            lab_treatment="LT-T-Z"
                            if tr_temp+0.1 in this_specimen_teratments[:-1]:
                                lab_protocols_string="LP-PI-TRM-IZ:"+lab_protocols_string
                            else:
                                lab_protocols_string="LP-PI-TRM-ZI:"+lab_protocols_string
                                                
                        elif float(tr_tr)==10 or float(tr_tr)==1:                            
                            lab_treatment="LT-T-I"
                            if tr_temp+0.0 in this_specimen_teratments[:-1]:
                                lab_protocols_string="LP-PI-TRM-ZI:"+lab_protocols_string
                            else:
                                lab_protocols_string="LP-PI-TRM-IZ:"+lab_protocols_string

                        elif float(tr_tr)==20 or float(tr_tr)==2:                            
                            lab_treatment="LT-PTRM-I"            
                        elif float(tr_tr)==30 or float(tr_tr)==3:                            
                            lab_treatment="LT-PTRM-MD"            
                        elif float(tr_tr)==40 or float(tr_tr)==4:                            
                            lab_treatment="LT-PTRM-AC"            
                        else:                            
                            print "-E- unknown measurement code specimen %s treatmemt %s"%(meas_line['Specimen'],meas_line['Treatment'])
                        
                    elif experiment in ['ATRM 6 positions']:
                        lab_protocols_string="LP-AN-TRM"
                        if float(tr_tr)==0:
                            lab_treatment="LT-T-Z"
                            MagRec["treatment_dc_field_phi"]='0'
                            MagRec["treatment_dc_field_theta"]='0'
                        else:
                                    
                            # find the direction of the lab field in two ways:
                            # (1) using the treatment coding (XX.1=+x, XX.2=+y, XX.3=+z, XX.4=-x, XX.5=-y, XX.6=-z)
                            tdec=[0,90,0,180,270,0,0,90,0]
                            tinc=[0,0,90,0,0,-90,0,0,90]
                            if tr_tr < 10:
                                ipos_code=int(tr_tr)-1
                            else:
                                ipos_code=int(tr_tr/10)-1
                            # (2) using the magnetization
                            DEC=float(meas_line["Declination"])
                            INC=float(meas_line["Inclination"])
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
                            if tr_tr!= 7 and tr_tr!= 70:
                                if ipos_guess!=ipos_code:
                                    print "-W- WARNING: check specimen %s step %s, ATRM measurements, coding does not match the direction of the lab field"%(specimen,meas_line['Treatment'])
                            MagRec["treatment_dc_field_phi"]='%7.1f' %(tdec[ipos])
                            MagRec["treatment_dc_field_theta"]='%7.1f'% (tinc[ipos])
                                
                            if float(tr_tr)==70 or float(tr_tr)==7: # alteration check as final measurement
                                    lab_treatment="LT-PTRM-I"
                            else:
                                    lab_treatment="LT-T-I"
                                
                    elif experiment in ['cooling rate']:
                        print "Dont support yet cooling rate experiment file. Contact rshaar@ucsd.edu"
                    elif experiment in ['NLT']:
                        if float(tr_tr)==0:
                            lab_protocols_string="LP-TRM"
                            lab_treatment="LT-T-Z"
                        else:
                            lab_protocols_string="LP-TRM"
                            lab_treatment="LT-T-I"
                            
                    MagRec["magic_method_codes"]=lab_treatment+":"+lab_protocols_string
                    line_string=""
                    for i in range(len(magic_headers)):
                        line_string=line_string+MagRec[magic_headers[i]]+"\t"
                    fout.write(line_string[:-1]+"\n")

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

class preferences_stats_dialog(wx.Dialog):
            
            def __init__(self, parent,title,preferences):
                self.preferences=preferences
                super(preferences_stats_dialog, self).__init__(parent, title=title)
                self.InitUI()

            def on_add_button(self,event):
                selName = str(self.criteria_options.GetStringSelection())
                if selName not in self.preferences['show_statistics_on_gui']:
                  self.preferences['show_statistics_on_gui'].append(selName)
                #self.update_text_box()
                self.criteria_list_window.Set(self.preferences['show_statistics_on_gui'])
                self.criteria_options.Set(self.statistics_options)

            def on_remove_button(self,event):
                selName = str(self.criteria_list_window.GetStringSelection())
                if selName  in self.preferences['show_statistics_on_gui']:
                  self.preferences['show_statistics_on_gui'].remove(selName)
                self.criteria_list_window.Set(self.preferences['show_statistics_on_gui'])
                self.criteria_options.Set(self.statistics_options)
               
                
            def InitUI(self):

                pnl1 = wx.Panel(self)

                vbox = wx.BoxSizer(wx.VERTICAL)

                #-----------box1        

                bSizer1 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Statistical definitions" ), wx.HORIZONTAL )
                self.bootstrap_N=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(80,20))
                                             
                Statistics_definitions_window = wx.GridSizer(1, 2, 12, 12)
                Statistics_definitions_window.AddMany( [(wx.StaticText(pnl1,label="Bootstrap N",style=wx.TE_CENTER), wx.EXPAND),
                    (self.bootstrap_N, wx.EXPAND)])                 
                bSizer1.Add( Statistics_definitions_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )
                
                #-----------box2        

                bSizer2 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Dipole Moment" ), wx.HORIZONTAL )

                self.v_adm_box = wx.ComboBox(pnl1, -1, self.preferences['VDM_or_VADM'], (100, 20), wx.DefaultSize, ["VADM","VDM"], wx.CB_DROPDOWN,name="VDM or VADM?")
                                             
                Statistics_VADM = wx.GridSizer(1, 2, 12, 12)
                Statistics_VADM.AddMany( [(wx.StaticText(pnl1,label="VDM or VADM?",style=wx.TE_CENTER), wx.EXPAND),
                    (self.v_adm_box, wx.EXPAND)])                 
                bSizer2.Add( Statistics_VADM, 0, wx.ALIGN_LEFT|wx.ALL, 5 )
                         
                #----------------------
                                    
#                bSizer3 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Choose statistics to display on GUI" ), wx.VERTICAL )
#
#                self.statistics_options=["int_n","int_ptrm_n","frac","scat","gmax","b_beta","int_mad","int_dang","f","fvds","g","q","drats","md",'ptrms_dec','ptrms_inc','ptrms_mad','ptrms_angle']
#                #self.criteria_list_window = wx.TextCtrl(pnl1, id=-1, size=(200,250), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
#                self.criteria_list_window =wx.ListBox(choices=self.preferences['show_statistics_on_gui'], id=-1,name='listBox1', parent=pnl1, size=wx.Size(150, 150), style=0)
#                self.criteria_options = wx.ListBox(choices=self.statistics_options, id=-1,name='listBox1', parent=pnl1, size=wx.Size(150, 150), style=0)
#                #self.criteria_options.Bind(wx.EVT_LISTBOX, self.on_choose_criterion,id=-1)
#                self.criteria_add =  wx.Button(pnl1, id=-1, label='add')
#                self.Bind(wx.EVT_BUTTON, self.on_add_button, self.criteria_add)
#                self.criteria_remove =  wx.Button(pnl1, id=-1, label='remove')
#                self.Bind(wx.EVT_BUTTON, self.on_remove_button, self.criteria_remove)
#
#                Statistics_criteria_0 = wx.GridSizer(1, 2, 0, 0)
#                Statistics_criteria_0.AddMany( [(wx.StaticText(pnl1,label="Options:"), wx.EXPAND),
#                    (wx.StaticText(pnl1,label="Statistics displayed:"), wx.EXPAND)])
#   
#                Statistics_criteria_1 = wx.GridSizer(2, 2, 0, 0)
#                Statistics_criteria_1.AddMany( [((self.criteria_options),wx.EXPAND),
#                    ((self.criteria_list_window),wx.EXPAND),
#                    ((self.criteria_add),wx.EXPAND),
#                    ((self.criteria_remove),wx.EXPAND)])
#
#
###                bSizer3.Add(self.criteria_options,wx.ALIGN_LEFT)
###                bSizer3.Add(self.criteria_add,wx.ALIGN_LEFT)
###                bSizer3.Add(self.criteria_list_window)
#                bSizer3.Add(Statistics_criteria_0, 0, wx.ALIGN_TOP, 0 )
#                bSizer3.Add(Statistics_criteria_1, 0, wx.ALIGN_TOP, 0 )
#                #self.update_text_box() 

                #----------------------

                hbox2 = wx.BoxSizer(wx.HORIZONTAL)
                self.okButton = wx.Button(pnl1, wx.ID_OK, "&OK")
                self.cancelButton = wx.Button(pnl1, wx.ID_CANCEL, '&Cancel')
                hbox2.Add(self.okButton)
                hbox2.Add(self.cancelButton )

                
                #----------------------  
                vbox.AddSpacer(20)
                vbox.Add(bSizer1, flag=wx.ALIGN_TOP)
                vbox.AddSpacer(20)

                vbox.Add(bSizer2, flag=wx.ALIGN_TOP)
                vbox.AddSpacer(20)

                #vbox.Add(bSizer3, flag=wx.ALIGN_TOP)
                #vbox.AddSpacer(20)

                vbox.Add(hbox2, flag=wx.ALIGN_TOP)
                vbox.AddSpacer(20)
                            
                pnl1.SetSizer(vbox)
                vbox.Fit(self)


                #---------------------- Initialize  values:

                try:                    
                    self.bootstrap_N.SetValue("%.0f"%(self.preferences["BOOTSTRAP_N"]))
                except:
                    self.bootstrap_N.SetValue("10000")
                    
                #----------------------

#--------------------------------------------------------------    
# show figures
#--------------------------------------------------------------

class ShowFigure():
    def __init__(self,fig):
        self.fig=fig
        self.fig.show()
    
    
