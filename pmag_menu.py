#!/usr/bin/env pythonw

import wx
import os
import pmag_basic_dialogs
import pmag_menu_dialogs
import pmag_widgets as pw



class MagICMenu(wx.MenuBar):
    
    def __init__(self, parent):
        self.parent = parent
        super(MagICMenu, self).__init__()

        file_menu = wx.Menu()
        file_quit = file_menu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        file_clear = file_menu.Append(wx.ID_ANY, 'Clear directory', 'Delete all files from working directory')
        parent.Bind(wx.EVT_MENU, self.on_quit, file_quit)
        parent.Bind(wx.EVT_MENU, self.on_clear, file_clear)

        import_menu = wx.Menu()

        orient_submenu = wx.Menu()

        orient1 = wx.MenuItem(import_menu, -1, "orient.txt format")
        orient_submenu.AppendItem(orient1)
        orient2 = orient_submenu.Append(-1, 'AzDip format')
        orient3 = orient_submenu.Append(-1, "ODP Core Summary csv file")
        orient4 = orient_submenu.Append(-1, "ODP Sample Summary csv file")
        orient5 = orient_submenu.Append(-1, "Import model latitude data file")

        parent.Bind(wx.EVT_MENU, self.orient_import1, orient1)
        parent.Bind(wx.EVT_MENU, self.orient_import2, orient2)
        parent.Bind(wx.EVT_MENU, self.orient_import3, orient3)
        parent.Bind(wx.EVT_MENU, self.orient_import4, orient4)
        parent.Bind(wx.EVT_MENU, self.orient_import5, orient5)

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
        
        import_menu.AppendMenu(wx.ID_ANY, "orientation/location/stratigraphic files", orient_submenu)
        import_menu.AppendMenu(wx.ID_ANY, "Anisotropy files", anisotropy_submenu)
        import_menu.AppendMenu(wx.ID_ANY, "Hysteresis files", hysteresis_submenu)

        analysis_menu = wx.Menu()
        #analysis1 = analysis_menu.Append(-1, "Customize Criteria")
        #analysis_menu.AppendSeparator()
        #analysis2 = analysis_menu.Append(-1, "Zeq_magic program")
        #analysis3 = analysis_menu.Append(-1, "Thellier_magic program")

        equal_area_submenu = wx.Menu()
        equal_area1 = equal_area_submenu.Append(-1, 'Quick Look - NRM directions')
        equal_area2 = equal_area_submenu.Append(-1, 'General remanence directions')
        equal_area3 = equal_area_submenu.Append(-1, 'Anisotropy data')

        analysis4 = analysis_menu.AppendMenu(-1, "Equal area plots", equal_area_submenu)
        #analysis5 = analysis_menu.Append(-1, "Hysteresis data")
        #analysis6 = analysis_menu.Append(-1, "Hysteresis ratio plots")
        #analysis7 = analysis_menu.Append(-1, "IRM acquisition")
        #analysis8 = analysis_menu.Append(-1, "3D IRM acquisition")
        analysis9 = analysis_menu.Append(-1, "Remanence data versus depth/height")
        analysis10 = analysis_menu.Append(-1, "Anisotropy data versus depth/height")
        analysis11 = analysis_menu.Append(-1, "Reversals test")
        analysis12 = analysis_menu.Append(-1, "Fold test")
        #analysis13 = analysis_menu.Append(-1, "Elong/Inc")

        #parent.Bind(wx.EVT_MENU, self.analysis1, analysis1)
        #parent.Bind(wx.EVT_MENU, self.analysis2, analysis2)
        #parent.Bind(wx.EVT_MENU, self.analysis3, analysis3)

        parent.Bind(wx.EVT_MENU, self.analysis4, equal_area1)
        parent.Bind(wx.EVT_MENU, self.analysis4, equal_area2)
        parent.Bind(wx.EVT_MENU, self.analysis4, equal_area3)

        #parent.Bind(wx.EVT_MENU, self.analysis5, analysis5)
        #parent.Bind(wx.EVT_MENU, self.analysis6, analysis6)
        #parent.Bind(wx.EVT_MENU, self.analysis7, analysis7)
        #parent.Bind(wx.EVT_MENU, self.analysis8, analysis8)
        parent.Bind(wx.EVT_MENU, self.analysis9, analysis9)
        parent.Bind(wx.EVT_MENU, self.analysis10, analysis10)
        parent.Bind(wx.EVT_MENU, self.analysis11, analysis11)
        parent.Bind(wx.EVT_MENU, self.analysis12, analysis12)
        #parent.Bind(wx.EVT_MENU, self.analysis13, analysis13)

        self.Append(file_menu, 'File')
        self.Append(import_menu, 'Import')
        self.Append(analysis_menu, 'Analysis and Plots (Coming soon!)') # probably won't use this
        


    def on_quit(self, event):
        self.parent.Close()

    def on_clear(self, event):
        clear = pmag_menu_dialogs.ClearWD(self.parent, self.parent.WD)

    def orient_import1(self, event): 
        orient1 = pmag_menu_dialogs.ImportOrientFile(self.parent, self.parent.WD)

    def orient_import2(self, event):
        orient2 = pmag_menu_dialogs.ImportAzDipFile(self.parent, self.parent.WD)

    def orient_import3(self, event):
        orient3 = pmag_menu_dialogs.ImportODPCoreSummary(self.parent, self.parent.WD)

    def orient_import4(self, event):
        orient4 = pmag_menu_dialogs.ImportODPSampleSummary(self.parent, self.parent.WD)

    def orient_import5(self, event):
        orient5 = pmag_menu_dialogs.ImportModelLatitude(self.parent, self.parent.WD)

    def anisotropy_import1(self, event):
        aniso1 = pmag_menu_dialogs.ImportKly4s(self.parent, self.parent.WD)

    def anisotropy_import2(self, event):
        aniso2 = pmag_menu_dialogs.ImportK15(self.parent, self.parent.WD)
    
    def anisotropy_import3(self, event):
        aniso3 = pmag_menu_dialogs.ImportSufarAscii(self.parent, self.parent.WD)

    def hysteresis_import1(self, event):
        hyst1 = pmag_menu_dialogs.ImportAgmFile(self.parent, self.parent.WD)

    def hysteresis_import2(self, event):
        hyst2 = pmag_menu_dialogs.ImportAgmFolder(self.parent, self.parent.WD)

    def analysis1(self, event):
        analysis1 = pmag_menu_dialogs.CustomizeCriteria(self.parent, self.parent.WD)

    def analysis2(self, event):
        analysis2 = pmag_menu_dialogs.ZeqMagic(self.parent, self.parent.WD)


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
        analysis9 = pmag_menu_dialogs.Core_depthplot(self.parent, self.parent.WD)

    def analysis10(self, event):
        analysis10 = pmag_menu_dialogs.Ani_depthplot(self.parent, self.parent.WD)


    def analysis11(self, event):
        pass

    def analysis12(self, event):
        pass

    def analysis13(self, event):
        pass


    
