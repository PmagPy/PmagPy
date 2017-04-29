#!/usr/bin/env pythonw

"""
Create Pmag GUI menubar
"""

import wx
from . import pmag_widgets as pw
from . import pmag_menu_dialogs
from pmagpy import builder2 as builder
from pmagpy import new_builder as nb


class MagICMenu(wx.MenuBar):
    """
    initialize menu bar for Pmag GUI
    """

    # prevent error message about too many public methods
    #pylint: disable=R0904
    #pylint: disable=R0914

    def __init__(self, parent, data_model_num):
        self.parent = parent
        self.data_model_num = data_model_num
        super(MagICMenu, self).__init__()

        ## File
        file_menu = wx.Menu()
        file_quit = file_menu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        file_show = file_menu.Append(wx.ID_ANY, 'Show main window',
                                     'Show main window')
        file_clear = file_menu.Append(wx.ID_ANY, 'Clear directory',
                                      'Delete all files from working directory')

        parent.Bind(wx.EVT_MENU, self.on_quit, file_quit)
        parent.Bind(wx.EVT_MENU, self.on_show_mainframe, file_show)
        parent.Bind(wx.EVT_MENU, self.on_clear, file_clear)

        ## Help
        help_menu = wx.Menu()
        help_cookbook = help_menu.Append(wx.ID_ANY, '&PmagPy Cookbook\tCtrl-Shift-H',
                                         'Access the online documentation')
        help_git = help_menu.Append(wx.ID_ANY, '&Github Page\tCtrl-Shift-G',
                                    'Access the PmagPy repository')
        parent.Bind(wx.EVT_MENU, pw.on_cookbook, help_cookbook)
        parent.Bind(wx.EVT_MENU, pw.on_git, help_git)
        if pw.get_output_frame():
            help_show = help_menu.Append(wx.ID_ANY, 'Show output', 'Show help')
            help_hide = help_menu.Append(wx.ID_ANY, 'Hide output', 'Hide output')
            parent.Bind(wx.EVT_MENU, pw.on_show_output, help_show)
            parent.Bind(wx.EVT_MENU, pw.on_hide_output, help_hide)

        import_menu = wx.Menu()

        orient_submenu = wx.Menu()
        orient2 = orient_submenu.Append(-1, 'AzDip format')
        #orient3 = orient_submenu.Append(-1, "IODP Core Summary csv file")
        orient4 = orient_submenu.Append(-1, "IODP Sample Summary csv file")
        #orient5 = orient_submenu.Append(-1, "Import model latitude data file")

        parent.Bind(wx.EVT_MENU, self.orient_import2, orient2)
        #parent.Bind(wx.EVT_MENU, self.orient_import3, orient3)
        parent.Bind(wx.EVT_MENU, self.orient_import4, orient4)
        #parent.Bind(wx.EVT_MENU, self.orient_import5, orient5)

        anisotropy_submenu = wx.Menu()
        anisotropy1 = anisotropy_submenu.Append(-1, "kly4s format")
        anisotropy2 = anisotropy_submenu.Append(-1, "k15 format")
        anisotropy3 = anisotropy_submenu.Append(-1, "Sufar 4.0 ascii format")

        parent.Bind(wx.EVT_MENU, self.anisotropy_import1, anisotropy1)
        parent.Bind(wx.EVT_MENU, self.anisotropy_import2, anisotropy2)
        parent.Bind(wx.EVT_MENU, self.anisotropy_import3, anisotropy3)

        hysteresis_submenu = wx.Menu()
        hysteresis1 = hysteresis_submenu.Append(-1, "Import single agm file")
        hysteresis2 = hysteresis_submenu.Append(-1, "Import entire directory")

        parent.Bind(wx.EVT_MENU, self.hysteresis_import1, hysteresis1)
        parent.Bind(wx.EVT_MENU, self.hysteresis_import2, hysteresis2)

        import1 = import_menu.Append(-1, "Import any file into your working directory")
        import_menu.AppendSeparator()
        import_menu.Append(wx.ID_ANY, "orientation/location/stratigraphic files", orient_submenu)
        import_menu.Append(wx.ID_ANY, "Anisotropy files", anisotropy_submenu)
        import_menu.Append(wx.ID_ANY, "Hysteresis files", hysteresis_submenu)

        parent.Bind(wx.EVT_MENU, self.on_import1, import1)

        ## Export
        export_menu = wx.Menu()
        export1 = export_menu.Append(-1, "Export result tables")

        parent.Bind(wx.EVT_MENU, self.on_export_results, export1)

        ## Plotting and analysis
        analysis_menu = wx.Menu()
        #analysis1 = analysis_menu.Append(-1, "Customize Criteria")
        #analysis_menu.AppendSeparator()
        #analysis2 = analysis_menu.Append(-1, "Zeq_magic program")
        #analysis3 = analysis_menu.Append(-1, "Thellier_magic program")

        #equal_area_submenu = wx.Menu()
        #equal_area1 = equal_area_submenu.Append(-1, 'Quick Look - NRM directions')
        #equal_area2 = equal_area_submenu.Append(-1, 'General remanence directions')
        #equal_area3 = equal_area_submenu.Append(-1, 'Anisotropy data')

        #analysis4 = analysis_menu.Append(-1, "Equal area plots", equal_area_submenu)
        #analysis5 = analysis_menu.Append(-1, "Hysteresis data")
        #analysis6 = analysis_menu.Append(-1, "Hysteresis ratio plots")
        #analysis7 = analysis_menu.Append(-1, "IRM acquisition")
        #analysis8 = analysis_menu.Append(-1, "3D IRM acquisition")
        analysis9 = analysis_menu.Append(-1, "Remanence data vs. depth/height/age")
        analysis10 = analysis_menu.Append(-1, "Anisotropy data vs. depth/height/age")
        #analysis11 = analysis_menu.Append(-1, "Reversals test")
        #analysis12 = analysis_menu.Append(-1, "Fold test")
        #analysis13 = analysis_menu.Append(-1, "Elong/Inc")

        #parent.Bind(wx.EVT_MENU, self.analysis1, analysis1)
        #parent.Bind(wx.EVT_MENU, self.analysis2, analysis2)
        #parent.Bind(wx.EVT_MENU, self.analysis3, analysis3)

        #parent.Bind(wx.EVT_MENU, self.analysis4, equal_area1)
        #parent.Bind(wx.EVT_MENU, self.analysis4, equal_area2)
        #parent.Bind(wx.EVT_MENU, self.analysis4, equal_area3)

        #parent.Bind(wx.EVT_MENU, self.analysis5, analysis5)
        #parent.Bind(wx.EVT_MENU, self.analysis6, analysis6)
        #parent.Bind(wx.EVT_MENU, self.analysis7, analysis7)
        #parent.Bind(wx.EVT_MENU, self.analysis8, analysis8)
        parent.Bind(wx.EVT_MENU, self.analysis9, analysis9)
        parent.Bind(wx.EVT_MENU, self.analysis10, analysis10)
        #parent.Bind(wx.EVT_MENU, self.analysis11, analysis11)
        #parent.Bind(wx.EVT_MENU, self.analysis12, analysis12)
        #parent.Bind(wx.EVT_MENU, self.analysis13, analysis13)

        self.Append(file_menu, 'File')
        self.Append(help_menu, 'Help ')
        self.Append(import_menu, 'Import')
        self.Append(export_menu, 'Export')
        self.Append(analysis_menu, 'Analysis and Plots') # probably won't use this



    def on_quit(self, event):
        """
        shut down application
        """
        self.parent.Close()

    def on_show_mainframe(self, event):
        """
        Show main make_magic window
        """
        self.parent.Show()
        self.parent.Raise()


    def on_clear(self, event):
        """
        initialize window to allow user to empty the working directory
        """
        dia = pmag_menu_dialogs.ClearWD(self.parent, self.parent.WD)
        clear = dia.do_clear()
        if clear:
            # clear directory, but use previously acquired data_model
            if self.data_model_num == 2.5:
                self.parent.er_magic = builder.ErMagicBuilder(self.parent.WD, self.parent.er_magic.data_model)
            elif self.data_model_num == 3:
                self.parent.contribution = nb.Contribution(self.parent.WD,
                                                           dmodel=self.parent.contribution.data_model)


    def on_import1(self, event):
        """
        initialize window to import an arbitrary file into the working directory
        """
        pmag_menu_dialogs.MoveFileIntoWD(self.parent, self.parent.WD)

    def on_export_results(self, event):
        pmag_menu_dialogs.ExportResults(self.parent, self.parent.WD)

    def orient_import2(self, event):
        """
        initialize window to import an AzDip format file into the working directory
        """
        pmag_menu_dialogs.ImportAzDipFile(self.parent, self.parent.WD)

    #def orient_import3(self, event):
        #orient3 = pmag_menu_dialogs.ImportODPCoreSummary(self.parent, self.parent.WD)

    def orient_import4(self, event):
        pmag_menu_dialogs.ImportIODPSampleSummary(self.parent, self.parent.WD)

    #def orient_import5(self, event):
    #    orient5 = pmag_menu_dialogs.ImportModelLatitude(self.parent, self.parent.WD)

    def anisotropy_import1(self, event):
        pmag_menu_dialogs.ImportKly4s(self.parent, self.parent.WD)

    def anisotropy_import2(self, event):
        pmag_menu_dialogs.ImportK15(self.parent, self.parent.WD)

    def anisotropy_import3(self, event):
        pmag_menu_dialogs.ImportSufarAscii(self.parent, self.parent.WD)

    def hysteresis_import1(self, event):
        pmag_menu_dialogs.ImportAgmFile(self.parent, self.parent.WD)

    def hysteresis_import2(self, event):
        pmag_menu_dialogs.ImportAgmFolder(self.parent, self.parent.WD)

    def analysis1(self, event):
        pmag_menu_dialogs.CustomizeCriteria(self.parent, self.parent.WD)

    def analysis2(self, event):
        pmag_menu_dialogs.ZeqMagic(self.parent, self.parent.WD)

    def analysis3(self, event):
        pass

    def analysis4(self, event):
        pass

    def analysis5(self, event):
        pass

    def analysis6(self, event):
        pass

    def analysis7(self, event):
        pass

    def analysis8(self, event):
        pass

    def analysis9(self, event):
        pmag_menu_dialogs.Core_depthplot(self.parent, self.parent.WD)

    def analysis10(self, event):
        pmag_menu_dialogs.Ani_depthplot(self.parent, self.parent.WD)

    def analysis11(self, event):
        pass

    def analysis12(self, event):
        pass

    def analysis13(self, event):
        pass
