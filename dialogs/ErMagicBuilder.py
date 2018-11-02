#!/usr/bin/env pythonw

# pylint: disable=W0612,C0111,C0103,W0201,C0301,E265

#============================================================================================
# LOG HEADER:
#============================================================================================

import os
import sys
import pandas as pd
import wx
import wx.grid
import wx.html
#import pdb
from . import pmag_widgets as pw
from pmagpy import find_pmag_dir
from pmagpy import builder2 as builder
from pmagpy import contribution_builder as cb
from pmagpy import data_model3 as data_model

#from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas \

#--------------------------------------------------------------
# MagIC model builder
#--------------------------------------------------------------



class MagIC_model_builder3(wx.Frame):

    def __init__(self, WD, parent, contribution=None):
        SIZE = wx.DisplaySize()
        SIZE = (SIZE[0] * .95, SIZE[1] * .95)

        wx.Frame.__init__(self, parent, wx.ID_ANY, size=SIZE,
                          name='ErMagicBuilder')
        self.parent = parent
        self.main_frame = self.Parent
        self.panel = wx.ScrolledWindow(self)
        self.panel.SetScrollbars(1, 1, 1, 1)
        if sys.platform in ['win32', 'win64']:
            self.panel.SetScrollbars(20, 20, 50, 50)
        os.chdir(WD)
        self.WD = os.getcwd()
        self.site_lons = []
        self.site_lats = []

        # if ErMagic data object was not passed in,
        # create one based on the working directory

        if not contribution:
            self.contribution = cb.Contribution(self.WD)
        else:
            self.contribution = contribution

        # first propagate from measurements
        self.contribution.propagate_measurement_info()
        # then propagate from other tables
        # (i.e., if sites are in specimens or samples but not measurements)
        self.contribution.propagate_all_tables_info()
        # then add in blank tables if any are missing
        self.table_list = ["specimens", "samples", "sites", "locations", "ages"]
        for table in self.table_list:
            if table not in self.contribution.tables:
                new_table = cb.MagicDataFrame(dtype=table,
                                              dmodel=self.contribution.data_model)
                self.contribution.tables[table] = new_table

        self.SetTitle("Earth-Ref Magic Builder")
        self.InitUI()
        # hide mainframe, bind close event so that it closes the current window not the mainframe
        self.parent.Hide()
        self.parent.Bind(wx.EVT_MENU, lambda event: self.parent.menubar.on_quit(event, self), self.parent.menubar.file_quit)



    def InitUI(self):
        pnl1 = self.panel
        box_sizers = []
        self.text_controls = {}
        self.info_options = {}
        add_buttons = []
        remove_buttons = []
        if not self.contribution.data_model:
            self.contribution.data_model = data_model.DataModel()
        dmodel = self.contribution.data_model

        for table in self.table_list:
            N = self.table_list.index(table)
            label = table

            # make sure all tables have any actual headers (read from file)
            # plus any required headers
            reqd_headers = dmodel.get_reqd_headers(table)
            if table in self.contribution.tables:
                df_container = self.contribution.tables[table]
                actual_headers = df_container.df.columns.union(reqd_headers)
            else:
                actual_headers = reqd_headers
            # add any extra headers (i.e., reqd but not present), into the table
            add_headers = actual_headers.difference(df_container.df.columns)
            if table in ['sites', 'locations']:
                if 'age' not in add_headers and 'age' not in actual_headers:
                    add_headers = add_headers.append(pd.Index(['age']))
            for head in add_headers:
                df_container.df[head] = None
            # define actual (includes reqd) vs optional headers
            actual_headers = df_container.df.columns
            optional_headers = dmodel.dm[table].index.difference(actual_headers)

            box_sizer = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY,
                                                        table), wx.VERTICAL)
            box_sizers.append(box_sizer)

            text_control = wx.TextCtrl(self.panel, id=-1, size=(210, 250),
                                       style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL,
                                       name=table)
            self.text_controls[table] = text_control

            info_option = wx.ListBox(choices=optional_headers, id=-1, name=table,
                                     parent=self.panel, size=(200, 250), style=0)
            self.info_options[table] = info_option

            add_button = wx.Button(self.panel, id=-1, label='add', name=table)
            add_buttons.append(add_button)

            self.Bind(wx.EVT_BUTTON, self.on_add_button, add_button)

            remove_button = wx.Button(self.panel, id=-1, label='remove', name=table)

            self.Bind(wx.EVT_BUTTON, self.on_remove_button, remove_button)

            #------
            box_sizer.Add(wx.StaticText(pnl1, label='{} header list:'.format(table)),
                          wx.ALIGN_TOP)

            box_sizer.Add(text_control, wx.ALIGN_TOP)

            box_sizer.Add(wx.StaticText(pnl1, label='{} optional:'.format(table)),
                          flag=wx.ALIGN_TOP|wx.TOP, border=10)

            box_sizer.Add(info_option, wx.ALIGN_TOP)

            box_sizer.Add(add_button, wx.ALIGN_TOP)

            box_sizer.Add(remove_button, wx.ALIGN_TOP)

            # need headers
            self.update_text_box(actual_headers, text_control)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(self.panel, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)
        self.okButton.SetDefault()

        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.Bind(wx.EVT_CLOSE, self.on_cancelButton)

        self.helpButton = wx.Button(self.panel, wx.ID_ANY, '&Help')
        self.Bind(wx.EVT_BUTTON, self.on_helpButton, self.helpButton)

        hbox1.Add(self.okButton, flag=wx.ALL, border=5)
        hbox1.Add(self.cancelButton, flag=wx.ALL, border=5)
        hbox1.Add(self.helpButton, flag=wx.ALL, border=5)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddSpacer(5)
        for sizer in box_sizers:
            hbox.Add(sizer, flag=wx.ALIGN_LEFT|wx.BOTTOM, border=5)
            hbox.AddSpacer(5)
        hbox.AddSpacer(5)

        text = wx.StaticText(self.panel, label="Step 0:\nChoose the headers for your specimens, samples, sites, locations and ages text files.\nOnce you have selected all necessary headers, click the OK button to move on to step 1.\nFor more information, click the help button below.")
        vbox.Add(text, flag=wx.ALIGN_LEFT|wx.ALL, border=20)
        #vbox.AddSpacer(20)
        vbox.Add(hbox)
        vbox.AddSpacer(20)
        vbox.Add(hbox1, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)

        # if they are not already present
        # add some strongly-recommended categories to age text_box
        if 'ages' in self.contribution.tables:
            actual_age_headers = list(self.contribution.tables['ages'].df.columns)
        else:
            actual_age_headers = dmodel.get_reqd_headers('ages')
        for extra_header in ['age', 'age_unit', 'site']:
            if extra_header not in actual_age_headers:
                actual_age_headers.append(extra_header)
                self.contribution.tables['ages'].df[extra_header] = None
        add_age_headers = list(set(actual_age_headers))
        self.update_text_box(add_age_headers, self.text_controls['ages'])

        self.panel.SetSizer(vbox)
        vbox.Fit(self)
        self.Show()
        self.Centre()
        # these two lines ensure that everything shows up
        wx.CallAfter(self.Refresh)
        self.Update()

    def update_text_box(self, headers_list, text_control):
        text = ""
        for key in sorted(headers_list):
            text = text + key + "\n"
        text = text[:-1]
        text_control.SetValue('')
        text_control.SetValue(text)
        self.Refresh()


    ### Button methods ###

    def on_add_button(self, event):
        table = event.GetEventObject().Name
        text_control = self.text_controls[table]
        info_option = self.info_options[table]
        headers = list(self.contribution.tables[table].df.columns)
        selName = info_option.GetStringSelection()

        if selName not in headers:
            self.contribution.tables[table].df[selName] = None
            headers.append(selName)
        self.update_text_box(headers, text_control)

    def on_remove_button(self, event):
        table = event.GetEventObject().Name
        info_option = self.info_options[table]
        text_control = self.text_controls[table]
        headers = list(self.contribution.tables[table].df.columns)
        selName = str(info_option.GetStringSelection())
        if selName in headers: # and selName not in reqd_header:
            del self.contribution.tables[table].df[selName]
            headers.remove(selName)
        self.update_text_box(headers, text_control)


    def on_okButton(self, event):
        os.chdir(self.WD)
        # update headers properly
        for table in ['specimens', 'samples', 'sites', 'locations', 'ages']:
            headers = self.text_controls[table].GetValue().split('\n')
            for header in headers:
                if header not in self.contribution.tables[table].df.columns:
                    #print "adding", header, "to", table
                    self.contribution.tables[table].df[header] = None
            # take out  unnecessary headers

        self.main_frame.init_check_window()
        self.Destroy()

    def on_cancelButton(self, event):
        self.Destroy()
        self.main_frame.Show()
        self.main_frame.Raise()

    def on_helpButton(self, event):
        #for use on the command line
        path = find_pmag_dir.get_pmag_dir()
        # for use with pyinstaller:
        #path = self.Parent.resource_dir
        help_page = os.path.join(path, 'dialogs', 'help_files', 'ErMagicHeadersHelp.html')
        # if using with py2app, the directory structure is flat,
        # so check to see where the resource actually is
        if not os.path.exists(help_page):
            help_page = os.path.join(path, 'help_files', 'ErMagicHeadersHelp.html')
        html_frame = pw.HtmlFrame(self, page=help_page)
        html_frame.Center()
        html_frame.Show()



class MagIC_model_builder(wx.Frame):
    """"""
    #----------------------------------------------------------------------
    def __init__(self, WD, parent, ErMagic_data=None):
        SIZE = wx.DisplaySize()
        SIZE = (SIZE[0] * .95, SIZE[1] * .95)

        wx.Frame.__init__(self, parent, wx.ID_ANY, size=SIZE,
                          name='ErMagicBuilder')
        #self.panel = wx.Panel(self)
        self.main_frame = self.Parent
        self.panel = wx.ScrolledWindow(self)
        self.panel.SetScrollbars(1, 1, 1, 1)
        if sys.platform in ['win32', 'win64']:
            self.panel.SetScrollbars(20, 20, 50, 50)
        os.chdir(WD)
        self.WD = os.getcwd()
        self.site_lons = []
        self.site_lats = []

        # if ErMagic data object was not passed in,
        # create one based on the working directory

        if not ErMagic_data:
            self.er_magic = builder.ErMagicBuilder(self.WD)
        else:
            self.er_magic= ErMagic_data

        print('-I- Read in any available data from working directory')
        self.er_magic.get_all_magic_info()
        print('-I- Initializing headers')
        self.er_magic.init_default_headers()
        self.er_magic.init_actual_headers()
        self.SetTitle("Earth-Ref Magic Builder" )
        self.InitUI()

    def InitUI(self):
        pnl1 = self.panel

        table_list = ["specimen", "sample", "site", "location", "age"]

        box_sizers = []
        self.text_controls = {}
        self.info_options = {}
        add_buttons = []
        remove_buttons = []

        for table in table_list:
            N = table_list.index(table)
            label = table

            optional_headers = self.er_magic.headers[label]['er'][2]
            actual_headers = self.er_magic.headers[label]['er'][0]

            box_sizer = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY,
                                                        table), wx.VERTICAL)
            box_sizers.append(box_sizer)

            text_control = wx.TextCtrl(self.panel, id=-1, size=(210, 250),
                                       style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL,
                                       name=table)
            self.text_controls[table] = text_control

            info_option = wx.ListBox(choices=optional_headers, id=-1, name=table,
                                     parent=self.panel, size=(200, 250), style=0)
            self.info_options[table] = info_option

            add_button = wx.Button(self.panel, id=-1, label='add', name=table)
            add_buttons.append(add_button)

            self.Bind(wx.EVT_BUTTON, self.on_add_button, add_button)

            remove_button = wx.Button(self.panel, id=-1, label='remove', name=table)

            self.Bind(wx.EVT_BUTTON, self.on_remove_button, remove_button)

            #------
            box_sizer.Add(wx.StaticText(pnl1, label='{} header list:'.format(table)),
                          wx.ALIGN_TOP)

            box_sizer.Add(text_control, wx.ALIGN_TOP)

            box_sizer.Add(wx.StaticText(pnl1, label='{} optional:'.format(table)),
                          flag=wx.ALIGN_TOP|wx.TOP, border=10)

            box_sizer.Add(info_option, wx.ALIGN_TOP)

            box_sizer.Add(add_button, wx.ALIGN_TOP)

            box_sizer.Add(remove_button, wx.ALIGN_TOP)

            # need headers
            self.update_text_box(actual_headers, text_control)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(self.panel, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)
        self.okButton.SetDefault()

        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        self.helpButton = wx.Button(self.panel, wx.ID_ANY, '&Help')
        self.Bind(wx.EVT_BUTTON, self.on_helpButton, self.helpButton)

        hbox1.Add(self.okButton, flag=wx.ALL, border=5)
        hbox1.Add(self.cancelButton, flag=wx.ALL, border=5)
        hbox1.Add(self.helpButton, flag=wx.ALL, border=5)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddSpacer(5)
        for sizer in box_sizers:
            hbox.Add(sizer, flag=wx.ALIGN_LEFT|wx.BOTTOM, border=5)
            hbox.AddSpacer(5)
        hbox.AddSpacer(5)

        text = wx.StaticText(self.panel, label="Step 0:\nChoose the headers for your specimens, samples, sites, locations and ages tables.\nOnce you have selected all necessary headers, click the OK button to move on to step 1.\nFor more information, click the help button below.")
        vbox.Add(text, flag=wx.ALIGN_LEFT|wx.ALL, border=20)
        #vbox.AddSpacer(20)
        vbox.Add(hbox)
        vbox.AddSpacer(20)
        vbox.Add(hbox1, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)

        # if they are not already present
        # add some strongly-recommended categories to age text_box
        actual_age_headers = self.er_magic.headers['age']['er'][0]
        for extra_header in ['age', 'age_unit']:
            if extra_header not in actual_age_headers:
                actual_age_headers.append(extra_header)
        add_age_headers = list(set(actual_age_headers))
        self.update_text_box(add_age_headers, self.text_controls['age'])

        self.panel.SetSizer(vbox)
        vbox.Fit(self)
        self.Show()
        self.Centre()
        # these two lines ensure that everything shows up
        wx.CallAfter(self.Refresh)
        self.Update()

    def update_text_box(self, headers_list, text_control):
        text = ""
        #command="keys=self.%s_header"%table
        #exec command
        for key in sorted(headers_list):
            text = text + key + "\n"
        text = text[:-1]
        text_control.SetValue('')
        text_control.SetValue(text)
        self.Refresh()

    ### Button methods ###

    def on_add_button(self, event):
        table = event.GetEventObject().Name
        text_control = self.text_controls[table]
        info_option = self.info_options[table]
        header = self.er_magic.headers[table]['er'][0]

        selName = info_option.GetStringSelection()

        if selName not in header:
            header.append(selName)
        self.update_text_box(header, text_control)

    def on_remove_button(self, event):
        table = event.GetEventObject().Name
        info_option = self.info_options[table]
        text_control = self.text_controls[table]
        header = self.er_magic.headers[table]['er'][0]
        reqd_header = self.er_magic.headers[table]['er'][1]

        selName = str(info_option.GetStringSelection())
        if selName in header and selName not in reqd_header:
            header.remove(selName)
        self.update_text_box(header, text_control)

    def on_okButton(self, event):
        os.chdir(self.WD)
        # update headers properly
        for table in ['specimen', 'sample', 'site', 'location', 'age']:
            headers = self.text_controls[table].GetValue().split('\n')
            for header in headers:
                if header not in self.er_magic.headers[table]['er'][0]:
                    self.er_magic.headers[table]['er'][0].append(header)
            # take out 'er_specimen_name' and other unnecessary headers
            self.er_magic.headers[table]['er'][0] = builder.remove_list_headers(self.er_magic.headers[table]['er'][0])

        self.main_frame.init_check_window2()
        self.Destroy()

    def on_cancelButton(self, event):
        self.Destroy()

    def on_helpButton(self, event):
        #for use on the command line
        path = find_pmag_dir.get_pmag_dir()

        # for use with pyinstaller:
        #path = self.Parent.resource_dir
        help_page = os.path.join(path, 'dialogs', 'help_files', 'ErMagicBuilderHelp.html')
        # if using with py2app, the directory structure is flat,
        # so check to see where the resource actually is
        if not os.path.exists(help_page):
            help_page = os.path.join(path, 'help_files', 'ErMagicBuilderHelp.html')
        html_frame = pw.HtmlFrame(self, page=help_page)
        html_frame.Center()
        html_frame.Show()


class HtmlWindow(wx.html.HtmlWindow):
    def OnLinkClicked(self, link):
        wx.LaunchDefaultBrowser(link.GetHref())

class MyHtmlPanel(wx.Frame):
    def __init__(self, parent,HTML):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title="Help Window", size=(800,600))
        html = HtmlWindow(self)
        html.LoadPage(HTML)
        #self.Show()
