#!/usr/bin/env pythonw

#============================================================================================
# LOG HEADER:
#============================================================================================

import matplotlib
matplotlib.use('WXAgg')
import  wx.html
import pmag
import pmag_widgets as pw
import check_updates

#from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas \
import os
#import sys,pylab,scipy,os
#import pmag
#import time
import wx
import wx.html
import wx.grid
import pmag
import copy

#from pylab import *
#from scipy.optimize import curve_fit
#import wx.lib.agw.floatspin as FS

#from matplotlib.backends.backend_wx import NavigationToolbar2Wx

#rcParams.update({"svg.embed_char_paths":False})
#rcParams.update({"svg.fonttype":'none'})



#--------------------------------------------------------------    
# MagIC model builder
#--------------------------------------------------------------


class MagIC_model_builder(wx.Frame):
    """"""
 
    #----------------------------------------------------------------------
    def __init__(self, WD, parent):
        SIZE=wx.DisplaySize()
        SIZE=(SIZE[0]-0.05*SIZE[0],SIZE[1]-0.05*SIZE[1])

        #print WD
        #print ".............."
        #print Data
        #print "-------------"
        #print Data_hierarchy
        wx.Frame.__init__(self, parent, wx.ID_ANY,size=SIZE)
        #self.panel = wx.Panel(self)
        self.main_frame = self.Parent
        self.panel = wx.ScrolledWindow(self)
        self.panel.SetScrollbars(1, 1, 1, 1)
        self.er_specimens_header=['er_citation_names','er_specimen_name','er_sample_name','er_site_name','er_location_name','specimen_class','specimen_lithology','specimen_type']
        self.er_samples_header=['er_citation_names','er_sample_name','er_site_name','er_location_name','sample_class','sample_lithology','sample_type','sample_lat','sample_lon']
        self.er_sites_header=['er_citation_names','er_site_name','er_location_name','site_class','site_lithology','site_type','site_definition','site_lon','site_lat']
        self.er_locations_header=['er_citation_names','er_location_name','location_begin_lon','location_end_lon','location_begin_lat','location_end_lat','location_type']
        self.er_ages_header=['er_citation_names','er_site_name','er_location_name','age_description','magic_method_codes','age','age_unit']
        os.chdir(WD)
        self.WD=os.getcwd()  
        #self.WD=WD
        self.Data,self.Data_hierarchy=self.get_data()
        self.read_MagIC_info()
        self.SetTitle("Earth-Ref Magic Builder" )
        self.InitUI()

    def InitUI(self):

        er_specimens_optional_header=['er_specimen_alternatives','er_expedition_name','er_formation_name','er_member_name',\
                                      'specimen_texture','specimen_alteration','specimen_alteration_type',\
                                      'specimen_elevation','specimen_height','specimen_core_depth','specimen_composite_depth','specimen_azimuth','specimen_dip',\
                                      'specimen_volume','specimen_weight','specimen_density','specimen_size','specimen_shape','specimen_igsn','specimen_description',\
                                      'magic_method_codes','er_scientist_mail_names']
        er_samples_optional_header=['sample_elevation','er_scientist_mail_names','magic_method_codes','sample_bed_dip','sample_bed_dip_direction','sample_dip',\
                                    'sample_azimuth','sample_declination_correction','sample_orientation_flag','sample_time_zone','sample_date','sample_height',\
                                    'sample_location_precision','sample_location_geoid','sample_composite_depth','sample_core_depth','sample_cooling_rate',\
                                    'er_sample_alternatives','sample_description','er_member_name','er_expedition_name','er_expedition_name','sample_alteration_type',\
                                    'sample_alteration','sample_texture','sample_igsn']

        er_sites_optional_header=['site_location_precision','er_scientist_mail_names','magic_method_codes','site_bed_dip','site_bed_dip_direction','site_height',\
                                  'site_elevation','site_location_geoid','site_composite_depth','site_core_depth','site_cooling_rate','site_description','er_member_name',\
                                  'er_site_alternatives','er_expedition_name','er_formation_name','site_igsn']
                                
          
        er_locations_optional_header=['continent_ocean','location_geoid','location_precision','location_end_elevation','location_begin_elevation','ocean_sea','er_scientist_mail_names',\
                                      'location_lithology','country','region','village_city','plate_block','terrane','geological_province_section','tectonic_setting',\
                                      'location_class','location_description','location_url','er_location_alternatives']

          
        er_ages_optional_header=['er_timescale_citation_names','age_range_low','age_range_high','age_sigma','age_culture_name','oxygen_stage','astronomical_stage','magnetic_reversal_chron',\
                                 'er_sample_name','er_specimen_name','er_fossil_name','er_mineral_name','tiepoint_name','tiepoint_height','tiepoint_height_sigma',\
                                 'tiepoint_elevation','tiepoint_type','timescale_eon','timescale_era','timescale_period','timescale_epoch',\
                                 'timescale_stage','biostrat_zone','conodont_zone','er_formation_name','er_expedition_name','tiepoint_alternatives',\
                                 'er_member_name']

        if len(self.data_er_specimens.keys())>0:
            for key in self.data_er_specimens[self.data_er_specimens.keys()[0]].keys():
                if key not in self.er_specimens_header:
                    self.er_specimens_header.append(key)

        if len(self.data_er_samples.keys()) >0:
            for key in self.data_er_samples[self.data_er_samples.keys()[0]].keys():
                if key not in self.er_samples_header:
                    self.er_samples_header.append(key)

        if len(self.data_er_sites.keys()) >0:
            for key in self.data_er_sites[self.data_er_sites.keys()[0]].keys():
                if key not in self.er_sites_header:
                    self.er_sites_header.append(key)

        if len(self.data_er_locations.keys()) >0:
            for key in self.data_er_locations[self.data_er_locations.keys()[0]].keys():
                if key not in self.er_locations_header:
                    self.er_locations_header.append(key)

        if len(self.data_er_ages.keys())>0:
            #print self.data_er_ages.keys()
            for key in self.data_er_ages[self.data_er_ages.keys()[0]].keys():
                if key not in self.er_ages_header:
                    self.er_ages_header.append(key)
                  
        
        pnl1 = self.panel

        table_list=["er_specimens","er_samples","er_sites","er_locations","er_ages"]
        #table_list=["er_specimens"]

        for table in table_list:
          N=table_list.index(table)
          command="bSizer%i = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, '%s' ), wx.VERTICAL )"%(N,table)
          exec command
          command="self.%s_info = wx.TextCtrl(self.panel, id=-1, size=(210,250), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)"%table
          exec command
          command = "self.%s_info_options = wx.ListBox(choices=%s_optional_header, id=-1,name='listBox1', parent=self.panel, size=wx.Size(200, 250), style=0)"%(table,table)
          exec command
          command="self.%s_info_add =  wx.Button(self.panel, id=-1, label='add')"%table
          exec command
          command="self.Bind(wx.EVT_BUTTON, self.on_%s_add_button, self.%s_info_add)"%(table,table)
          exec command
          command="self.%s_info_remove =  wx.Button(self.panel, id=-1, label='remove')"%table
          exec command
          command="self.Bind(wx.EVT_BUTTON, self.on_%s_remove_button, self.%s_info_remove)"%(table,table)
          exec command
        
                
        #------
          command="bSizer%i.Add(wx.StaticText(pnl1,label='%s header list:'),wx.ALIGN_TOP)"%(N,table)
          exec command
          command="bSizer%i.Add(self.%s_info,wx.ALIGN_TOP)"%(N,table)
          exec command
          command="bSizer%i.Add(wx.StaticText(pnl1,label='%s optional:'),wx.ALIGN_TOP)"%(N,table)
          exec command
          command="bSizer%i.Add(self.%s_info_options,wx.ALIGN_TOP)"%(N,table)
          exec command
          command="bSizer%i.Add(self.%s_info_add,wx.ALIGN_TOP)"%(N,table)
          exec command
          command="bSizer%i.Add(self.%s_info_remove,wx.ALIGN_TOP)"%(N,table)
          exec command

          
          self.update_text_box(table)
          
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(self.panel, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        self.helpButton = wx.Button(self.panel, wx.ID_ANY, '&Help')
        self.Bind(wx.EVT_BUTTON, self.on_helpButton, self.helpButton)

        hbox1.Add(self.okButton)
        hbox1.Add(self.cancelButton )
        hbox1.Add(self.helpButton)

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

        text = wx.StaticText(self.panel, label="Step 0:\nChoose the headers for your er_specimens, er_samples, er_sites, er_locations and er_ages text files.\nOnce you have selected all necessary headers, click the OK button to move on to step 1.\nFor more information, click the help button below.")
        vbox.Add(text, flag=wx.ALIGN_LEFT|wx.ALL, border=20)
        #vbox.AddSpacer(20)
        vbox.Add(hbox)
        vbox.AddSpacer(20)
        vbox.Add(hbox1,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
        
        self.panel.SetSizer(vbox)
        vbox.Fit(self)
        self.Show()
        self.Centre()


    def update_text_box(self,table):
        TEXT=""
        command="keys=self.%s_header"%table
        exec command
        for key in keys:
          TEXT=TEXT+key+"\n"
        TEXT=TEXT[:-1]
        commad="self.%s_info.SetValue('')"%table
        exec command
        command="self.%s_info.SetValue(TEXT)"%table
        exec command

    def on_er_specimens_add_button(self, event):
        selName = str(self.er_specimens_info_options.GetStringSelection())
        if selName not in self.er_specimens_header:
          self.er_specimens_header.append(selName)
        self.update_text_box('er_specimens')
          
    def on_er_samples_add_button(self, event):
        selName = self.er_samples_info_options.GetStringSelection()
        if selName not in self.er_samples_header:
          self.er_samples_header.append(selName)
        self.update_text_box('er_samples')
        
    def on_er_sites_add_button(self, event):
        selName = self.er_sites_info_options.GetStringSelection()
        if selName not in self.er_sites_header:
          self.er_sites_header.append(selName)
        self.update_text_box('er_sites')
        
    def on_er_locations_add_button(self, event):
        selName = self.er_locations_info_options.GetStringSelection()
        if selName not in self.er_locations_header:
          self.er_locations_header.append(selName)
        self.update_text_box('er_locations')
        
    def on_er_ages_add_button(self, event):
        selName = self.er_ages_info_options.GetStringSelection()
        if selName not in self.er_ages_header:
          self.er_ages_header.append(selName)
        self.update_text_box('er_ages')

    def on_er_specimens_remove_button(self, event):
        selName = str(self.er_specimens_info_options.GetStringSelection())
        if selName  in self.er_specimens_header:
          self.er_specimens_header.remove(selName)
        self.update_text_box('er_specimens')
          
    def on_er_samples_remove_button(self, event):
        selName = self.er_samples_info_options.GetStringSelection()
        if selName  in self.er_samples_header:
          self.er_samples_header.remove(selName)
        self.update_text_box('er_samples')
        
    def on_er_sites_remove_button(self, event):
        selName = self.er_sites_info_options.GetStringSelection()
        if selName  in self.er_sites_header:
          self.er_sites_header.remove(selName)
        self.update_text_box('er_sites')
        
    def on_er_locations_remove_button(self, event):
        selName = self.er_locations_info_options.GetStringSelection()
        if selName  in self.er_locations_header:
          self.er_locations_header.remove(selName)
        self.update_text_box('er_locations')
        
    def on_er_ages_remove_button(self, event):
        selName = self.er_ages_info_options.GetStringSelection()
        if selName  in self.er_ages_header:
          self.er_ages_header.remove(selName)
        self.update_text_box('er_ages')


    def on_okButton(self, event):
        self.update_ErMagic()
        self.main_frame.init_check_window()

    def update_ErMagic(self):
        """check for changes and write (or re-write) er_specimens.txt, er_samples.txt, etc."""
        wait = wx.BusyInfo("Please wait, working...")
        samples_list=self.Data_hierarchy['samples'].keys()
        samples_list = list(set(samples_list).union(self.data_er_samples.keys())) # uses samples from er_samples.txt even if they are not in the magic_measurements file
        samples_list.sort()

        specimens_list=self.Data_hierarchy['sample_of_specimen'].keys()
        specimens_list.sort()

        #---------------------------------------------
        # make er_samples.txt
        #---------------------------------------------

        #header
        er_samples_file=open(os.path.join(self.WD, "er_samples.txt"),'w')
        er_samples_file.write("tab\ter_samples\n")
        string=""
        for key in self.er_samples_header:
          string=string+key+"\t"
        er_samples_file.write(string[:-1]+"\n")

        for sample in samples_list:
          string=""
          for key in self.er_samples_header:

            if sample in self.data_er_samples.keys() and "er_site_name" in self.data_er_samples[sample].keys() and self.data_er_samples[sample]["er_site_name"] != "":
                site=self.data_er_samples[sample]["er_site_name"]
            elif sample in self.Data_hierarchy['site_of_sample'].keys():
                site=self.Data_hierarchy['site_of_sample'][sample]
            else:
                site = "unknown"
            
            if key=="er_citation_names":
              string=string+"This study"+"\t"
            
            elif key=="er_sample_name":
              string=string+sample+"\t"
              
            elif key in ['er_site_name']:
                string=string+site+"\t"

            elif key in ['er_location_name']:
                if site in self.data_er_sites.keys() and key in self.data_er_sites[site].keys():
                    string=string+self.data_er_sites[site][key]+"\t"
                else:
                    try:
                        string=string+self.Data_hierarchy['location_of_sample'][sample]+"\t"
                    except KeyError:
                        string = string + "" + "\t"
                        

            # if er_samples.txt already has a value in a column, don't try to get it from er_sites.txt
            elif sample in self.data_er_samples.keys() and key in self.data_er_samples[sample].keys() and self.data_er_samples[sample][key]!="":
                string=string+self.data_er_samples[sample][key]+"\t"

            # try to take lat/lon from er_sites table
            elif (key in ['sample_lon','sample_lat'] and sample in self.data_er_samples.keys()\
                  and "er_site_name" in self.data_er_samples[sample].keys()\
                  and self.data_er_samples[sample]['er_site_name'] in self.data_er_sites.keys()\
                  and "site_"+key.split("_")[1] in self.data_er_sites[self.data_er_samples[sample]['er_site_name']].keys()):
              string=string+self.data_er_sites[self.data_er_samples[sample]['er_site_name']]["site_"+key.split("_")[1]]+"\t"

            elif key in ['sample_class','sample_lithology','sample_type']:
              site_key="site_"+key.split('sample_')[1]
              if (site in self.data_er_sites.keys() and site_key in self.data_er_sites[site] and self.data_er_sites[site][site_key]!=""):
                    string=string+self.data_er_sites[site][site_key]+"\t"
                    continue
              else:
                    string=string+'\t'                        
            else:
              string=string+"\t"
          er_samples_file.write(string[:-1]+"\n")
        er_samples_file.close()
        #---------------------------------------------
        # make er_specimens.txt
        #---------------------------------------------

        #header
        er_specimens_file=open(os.path.join(self.WD, "er_specimens.txt"),'w')
        er_specimens_file.write("tab\ter_specimens\n")
        string=""
        for key in self.er_specimens_header:
          string=string+key+"\t"
        er_specimens_file.write(string[:-1]+"\n")

        for specimen in specimens_list:
          if  specimen in self.data_er_specimens.keys() and  "er_sample_name" in self.data_er_specimens[specimen].keys() and self.data_er_specimens[specimen]["er_sample_name"] != "":
                sample=self.data_er_specimens[specimen]["er_sample_name"]   
          else:
              sample=self.Data_hierarchy['sample_of_specimen'][specimen]
          string=""
          for key in self.er_specimens_header:
            if key=="er_citation_names":
              string=string+"This study"+"\t"
            elif key=="er_specimen_name":
              string=string+specimen+"\t"
            elif key=="er_sample_name":
            # take sample name from existing 
                string=string+sample+"\t"
            # try to take site and location name from er_sample table 
            # if not: take it from hierachy dictionary                    
            elif key in ['er_location_name']:
                if sample in self.data_er_samples.keys() and key in self.data_er_samples[sample].keys():
                    string=string+self.data_er_samples[sample][key]+"\t"
                else:
                    string=string+self.Data_hierarchy['location_of_specimen'][specimen]+"\t"
            elif key in ['er_site_name']:
                if sample in self.data_er_samples.keys() and key in self.data_er_samples[sample].keys():
                    string=string+self.data_er_samples[sample][key]+"\t"
                else:
                    string=string+self.Data_hierarchy['site_of_specimen'][specimen]+"\t"

            elif key in ['specimen_class','specimen_lithology','specimen_type']:
              sample_key="sample_"+key.split('specimen_')[1]
              if (sample in self.data_er_samples.keys() and sample_key in self.data_er_samples[sample] and self.data_er_samples[sample][sample_key]!=""):
                string=string+self.data_er_samples[sample][sample_key]+"\t"
                continue
              else:
                  string=string+"\t"
              
              #sample_key="sample_"+key.split('specimen_')[1]
              #if 'er_site_name' in self.data_er_samples[sample].keys() and self.data_er_samples[sample]['er_site_name']!="":
              #  site=self.data_er_samples[sample]['er_site_name']
              #site_key="site_"+key.split('specimen_')[1]                
              #if (sample in self.data_er_samples.keys() and sample_key in self.data_er_samples[sample] and self.data_er_samples[sample][sample_key]!=""):
              #  string=string+self.data_er_samples[sample][sample_key]+"\t"
              #elif (site in self.data_er_sites.keys() and site_key in self.data_er_sites[site] and self.data_er_sites[site][site_key]!=""):
              #  string=string+self.data_er_samples[sample][sample_key]+"\t"
                
            # take information from the existing er_samples table             
            elif specimen in self.data_er_specimens.keys() and key in self.data_er_specimens[specimen].keys() and self.data_er_specimens[specimen][key]!="":
                string=string+self.data_er_specimens[specimen][key]+"\t"
            else:
              string=string+"\t"
          er_specimens_file.write(string[:-1]+"\n")
        er_specimens_file.close()  

        #---------------------------------------------
        # make er_sites.txt
        #---------------------------------------------


        #header
        er_sites_file=open(os.path.join(self.WD, "er_sites.txt"),'w')
        er_sites_file.write("tab\ter_sites\n")
        string=""
        for key in self.er_sites_header:
          string=string+key+"\t"
        er_sites_file.write(string[:-1]+"\n")

        #data
        sites_list=self.data_er_sites.keys()
        for site in self.Data_hierarchy['sites'].keys():
            if site not in sites_list:
                sites_list.append(site)

        
        #for sample in self.data_er_samples.keys():
        #  if "er_site_name" in self.data_er_samples[sample].keys() and self.data_er_samples[sample]["er_site_name"] not in sites_list and self.data_er_samples[sample]["er_site_name"]!="":
        #    sites_list.append(self.data_er_samples[sample]["er_site_name"])
        sites_list.sort() 
        string=""  
        site_lons=[]     
        site_lats=[]     
        for site in sites_list:
          if site ==""  or site==" ":
              continue
          string=""    
          for key in self.er_sites_header:
            if key=="er_citation_names":
              string=string+"This study"+"\t"
            elif key=="er_site_name":
              string=string+site+"\t"            
            # take information from the existing er_samples table             
            elif (site in self.data_er_sites.keys() and key in self.data_er_sites[site].keys() and self.data_er_sites[site][key]!=""):
                #print "site: {}, key: {}, data {}".format(site, key, self.data_er_sites[site][key])
                string=string+self.data_er_sites[site][key]+"\t"

            elif key in ['er_location_name']:
                try:
                    string=string+self.Data_hierarchy['location_of_site'][site]+"\t"
                except KeyError:
                    string = string+"\t"
                    
            else:
              string=string+"\t"

          if site in self.data_er_sites.keys() and 'site_lon' in self.data_er_sites[site].keys() and self.data_er_sites[site]['site_lon']!="":
              try:
                    site_lons.append(float(self.data_er_sites[site]['site_lon']))
              except:
                  pass
          if site in self.data_er_sites.keys() and 'site_lat' in self.data_er_sites[site].keys() and self.data_er_sites[site]['site_lat']!="":
              try:
                    site_lats.append(float(self.data_er_sites[site]['site_lat']))
              except:
                  pass
          er_sites_file.write(string[:-1]+"\n")
        er_sites_file.close()

        #---------------------------------------------
        # make er_locations.txt
        #---------------------------------------------

        #header
        er_locations_file=open(os.path.join(self.WD, "er_locations.txt"),'w')
        er_locations_file.write("tab\ter_locations\n")
        string=""
        for key in self.er_locations_header:
          string=string+key+"\t"
        er_locations_file.write(string[:-1]+"\n")

        #data
        locations_list=self.data_er_locations.keys()
        for location in self.Data_hierarchy['locations'].keys():
            if location not in locations_list:
                locations_list.append(location)
        #for site in self.data_er_sites.keys():
        #  if "er_location_name" in self.data_er_sites[site].keys() and self.data_er_sites[site]["er_location_name"] not in locations_list:
        #    locations_list.append(self.data_er_sites[site]["er_location_name"])
        locations_list.sort()        
        for location in locations_list:
          string=""
          for key in self.er_locations_header:
            if key=="er_citation_names":
              if location in self.data_er_locations.keys():
                  value = self.data_er_locations[location][key] or "This study"
              else:
                  value = "This study"
              string=string+ value + "\t"
            elif key=="er_location_name":
              string=string+location+"\t"
            # take information from the existing er_location table             
            elif (location in self.data_er_locations.keys() and key in self.data_er_locations[location].keys() and self.data_er_locations[location][key]!=""):
                string=string+self.data_er_locations[location][key]+"\t"
            elif key in ['location_begin_lon','location_end_lon','location_begin_lat','location_end_lat']:
                if len(site_lons)>0 and key=='location_begin_lon':
                    value="%f"%min(site_lons)
                elif len(site_lons)>0 and key=='location_end_lon':
                    value="%f"%max(site_lons)
                elif len(site_lats)>0 and key=='location_begin_lat':
                    value="%f"%min(site_lats)
                elif len(site_lats)>0 and key=='location_end_lat':
                    value="%f"%max(site_lats)
                else:
                    value=""
                string=string+value+"\t"
                
            else:
              string=string+"\t"
          er_locations_file.write(string[:-1]+"\n")
        er_locations_file.close()


        #---------------------------------------------
        # make er_ages.txt
        #---------------------------------------------

        #header
        er_ages_file=open(os.path.join(self.WD, "er_ages.txt"),'w')
        er_ages_file.write("tab\ter_ages\n")
        string=""
        for key in self.er_ages_header:
          string=string+key+"\t"
        er_ages_file.write(string[:-1]+"\n")

        #data
        sites_list=self.data_er_sites.keys()
        for site in self.Data_hierarchy['sites'].keys():
            if site not in sites_list:
                sites_list.append(site)
        sites_list.sort() 
        for site in sites_list:
          string=""
          for key in self.er_ages_header:
            if key=="er_site_name":
              string=string+site+"\t"

            elif key=="er_citation_names":
              if site in self.data_er_ages.keys():
                  value = self.data_er_ages[site][key] or "This study"
              else: value = "This study"
              string=string + value + "\t"

            elif (key in ['er_location_name'] and site in self.data_er_sites.keys() \
                 and  key in self.data_er_sites[site] and self.data_er_sites[site][key]!=""):
              string=string+self.data_er_sites[site][key]+"\t"
              
            # take information from the existing er_samples table             
            elif (site in self.data_er_ages.keys() and key in self.data_er_ages[site].keys() and self.data_er_ages[site][key]!=""):
                string=string+self.data_er_ages[site][key]+"\t"

            else:
              string=string+"\t"
          er_ages_file.write(string[:-1]+"\n")

        er_ages_file.close()
        
        #-----------------------------------------------------
        # Fix magic_measurement with samples, sites and locations  
        #-----------------------------------------------------

        #print "in ErMagicBuilder on_okButton udpating magic_measurements.txt"
        f_old=open(os.path.join(self.WD, "magic_measurements.txt"),'rU')
        f_new=open(os.path.join(self.WD, "magic_measurements.new.tmp.txt"),'w')
             
        line=f_old.readline()
        f_new.write(line)

        line=f_old.readline()
        header=line.strip("\n").split('\t')
        f_new.write(line)

        # if you want to make it possible to change specimen names, add that into this for loop
        #print "self.data_er_specimens.keys()", self.data_er_specimens.keys()
        #print "self.Data_hierarchy['specimens'].keys()", self.Data_hierarchy['specimens'].keys()
        for line in f_old.readlines():
            tmp_line=line.strip('\n').split('\t')
            tmp={}
            for i in range(len(header)):
                if i>= len(tmp_line):
                    tmp[header[i]]=""
                else:
                    tmp[header[i]]=tmp_line[i]
            specimen=tmp["er_specimen_name"]
            sample=tmp["er_sample_name"]
            if specimen in  self.data_er_specimens.keys() and "er_sample_name" in self.data_er_specimens[specimen].keys():
                if sample != self.data_er_specimens[specimen]["er_sample_name"]:
                    sample=self.data_er_specimens[specimen]["er_sample_name"]
                    tmp["er_sample_name"]=sample
                                    
            if sample in self.data_er_samples.keys() and "er_site_name" in self.data_er_samples[sample].keys() and self.data_er_samples[sample]["er_site_name"]!="":
                tmp["er_site_name"]=self.data_er_samples[sample]["er_site_name"]
            site=tmp["er_site_name"]
            if site in self.data_er_sites.keys() and "er_location_name" in self.data_er_sites[site].keys() and self.data_er_sites[site]["er_location_name"]!="":
                tmp["er_location_name"]=self.data_er_sites[site]["er_location_name"]

            new_line=""
            for i in range(len(header)):
                new_line=new_line+tmp[header[i]]+"\t"
            #print new_line
            f_new.write(new_line[:-1]+"\n")
        f_new.close()
        f_old.close()

        os.remove(os.path.join(self.WD, "magic_measurements.txt"))
        os.rename(os.path.join(self.WD, "magic_measurements.new.tmp.txt"),os.path.join(self.WD, "magic_measurements.txt"))
        

                
##        #---------------------------------------------
##        # make er_locations.txt
##        #---------------------------------------------
##
##        #header
##        er_qges_file=open(os.path.join(self.WD, "er_ages.txt"),'w')
##        er_ages_file.write("tab\ter_ages\n")
##        string=""
##        for key in self.er_ages_header:
##          string=string+key+"\t"
##        er_ages_file.write(string[:-1]+"\n")
##
##        #data
##        ages_list=self.data_er_ages.keys()
##        ages_list.sort()        
##        for age in ages_list:
##          string=""
##          for key in self.er_locations_header:
##            if key=="er_citation_names":
##              string=string+"This study"+"\t"
##            elif key=="er_location_name":
##              string=string+location+"\t"
##            elif (location in self.data_er_locations.keys() and key in self.data_er_locations[location].keys() and self.data_er_locations[location][key]!=""):
##                string=string+self.data_er_locations[location][key]+"\t"
##            else:
##              string=string+"\t"
##          er_locations_file.write(string[:-1]+"\n")


        del wait
        dlg1 = wx.MessageDialog(self,caption="Saved", message="MagIC Earth-Ref tables are saved in MagIC Project Directory!" ,style=wx.OK|wx.ICON_INFORMATION)
        # is this dialog actually useful??
        dlg1.ShowModal()
        dlg1.Destroy()
        #self.Destroy()
        self.Hide()

        #print "done on_ok_Button in ErMagicBuilder"


    def on_cancelButton(self,event):
        self.Destroy()

    def on_helpButton(self, event):
        #path = check_updates.get_pmag_dir()
        # for running as module:
        path = self.Parent.resource_dir
        html_frame = pw.HtmlFrame(self, page=(os.path.join(path, "help_files", "ErMagicHeadersHelp.html")))
        html_frame.Center()
        html_frame.Show()

      
    def read_magic_file(self,path,sort_by_this_name):
        #print "doing ErMagic read_magic_file"
        DATA={}
        fin=open(path,'rU')
        fin.readline()
        line=fin.readline()
        header=line.strip('\n').split('\t')
        #print "path", path#,header
        counter=0
        for line in fin.readlines():
            #print "line:", line
            tmp_data={}
            tmp_line=line.strip('\n').split('\t')
            for i in range(len(header)):
                if i < len(tmp_line):
                    tmp_data[header[i]]=tmp_line[i]
                else:
                    print header[i]
                    tmp_data[header[i]]=""
            if sort_by_this_name=="by_line_number":
              DATA[counter]=tmp_data
              counter+=1
            else:
              if tmp_data[sort_by_this_name]!="":  
                DATA[tmp_data[sort_by_this_name]]=tmp_data
        fin.close()   
        return(DATA)

    def converge_headers(self,old_recs):
        # fix the headers of pmag recs
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
                    rec[header]=""
        return recs

    def read_MagIC_info(self):
        #print "read_MagIC_info in ErMagicBuilder.py"
        Data_info={}
        print "-I- read existing MagIC model files"
        self.data_er_specimens,self.data_er_samples,self.data_er_sites,self.data_er_locations,self.data_er_ages={},{},{},{},{}

        try:
            self.data_er_specimens=self.read_magic_file(os.path.join(self.WD, "er_specimens.txt"),'er_specimen_name')
        except:
            #self.GUI_log.write ("-W- Cant find er_samples.txt in project directory")
            print "-W- Cant find er_samples.txt in project directory"
        try:
            self.data_er_samples=self.read_magic_file(os.path.join(self.WD, "er_samples.txt"),'er_sample_name')
        except:
            #self.GUI_log.write ("-W- Cant find er_sample.txt in project directory")
            print "-W- Cant find er_sample.txt in project directory"
        try:
            self.data_er_sites=self.read_magic_file(os.path.join(self.WD, "er_sites.txt"),'er_site_name')
        except:
            pass
        try:
            self.data_er_locations=self.read_magic_file(os.path.join(self.WD, "er_locations.txt"),'er_location_name')
        except:
            #self.GUI_log.write ("-W- Cant find er_sites.txt in project directory")
            print "-W- Cant find er_sites.txt in project directory"
        try:
            self.data_er_ages=self.read_magic_file(os.path.join(self.WD, "er_ages.txt"),"er_site_name")
        except:
            try:
                self.data_er_ages=self.read_magic_file(os.path.join(self.WD, "er_ages.txt"),"er_sample_name")
            except:
                print "-W- Cant find er_ages.txt in project directory"
                pass


    def get_data(self):
      Data={}
      Data_hierarchy={}
      Data_hierarchy['locations']={}
      Data_hierarchy['sites']={}
      Data_hierarchy['samples']={}
      Data_hierarchy['specimens']={}
      Data_hierarchy['sample_of_specimen']={} 
      Data_hierarchy['site_of_specimen']={}   
      Data_hierarchy['site_of_sample']={}   
      Data_hierarchy['location_of_specimen']={}   
      Data_hierarchy['location_of_sample']={}   
      Data_hierarchy['location_of_site']={}   
      try:
          meas_data,file_type=pmag.magic_read(os.path.join(self.WD, "magic_measurements.txt"))
      except:
          print "-E- ERROR: Cant read magic_measurement.txt file. File is corrupted."
          return {},{}
         
      sids=pmag.get_specs(meas_data) # samples ID's
      
      for s in sids:
          if s not in Data.keys() and s!="" and s!=" ":
              Data[s]={}
      for rec in meas_data:
          s=rec["er_specimen_name"]
          if s=="" or s== " ":
              continue
          sample=rec["er_sample_name"]
          site=rec["er_site_name"]
          location=rec["er_location_name"]
          if sample not in Data_hierarchy['samples'].keys():
              Data_hierarchy['samples'][sample]=[]

          if site not in Data_hierarchy['sites'].keys():
              Data_hierarchy['sites'][site]=[]         

          if location not in Data_hierarchy['locations'].keys():
              Data_hierarchy['locations'][location]=[]         
          
          if s not in Data_hierarchy['samples'][sample]:
              Data_hierarchy['samples'][sample].append(s)

          if sample not in Data_hierarchy['sites'][site]:
              Data_hierarchy['sites'][site].append(sample)

          if site not in Data_hierarchy['locations'][location]:
              Data_hierarchy['locations'][location].append(site)

          Data_hierarchy['specimens'][s]=sample
          Data_hierarchy['sample_of_specimen'][s]=sample  
          Data_hierarchy['site_of_specimen'][s]=site  
          Data_hierarchy['site_of_sample'][sample]=site
          Data_hierarchy['location_of_specimen'][s]=location 
          Data_hierarchy['location_of_sample'][sample]=location 
          Data_hierarchy['location_of_site'][site]=location 
          
      return(Data,Data_hierarchy)

    
            
class HtmlWindow(wx.html.HtmlWindow):
    def OnLinkClicked(self, link):
        wx.LaunchDefaultBrowser(link.GetHref())

class MyHtmlPanel(wx.Frame):
     def __init__(self, parent,HTML):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title="Help Window", size=(800,600))
        html = HtmlWindow(self)
        html.LoadPage(HTML)  
        #self.Show()


#class HtmlWindow(wx.html.HtmlWindow,id):
#    def __init__(self, parent):
#        wx.html.HtmlWindow.__init__(self,parent,id=-1)
#        if "gtk2" in wx.PlatformInfo:
#            self.SetStandardFonts()
#
#    def OnLinkClicked(self, link):
#        wx.LaunchDefaultBrowser(link.GetHref())
#
#class MyHtmlPanel(wx.Frame):
#     def __init__(self, parent,id):
#        wx.Frame.__init__(self, parent,id)
#        panel = wx.Panel(self)
#        html = HtmlWindow(self,-1)
#        if "gtk2" in wx.PlatformInfo:
#            html.SetStandardFonts()
#        html.LoadPage('MagICModlBuilderHelp.html')  
#        sizer = wx.BoxSizer(wx.VERTICAL)
#        sizer.Add(html, 1, wx.EXPAND)
#        sizer.Fit(self)
#        panel.SetSizer(sizer)
               
