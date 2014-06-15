#!/usr/bin/env pythonw

import wx
import os
import pmag_basic_dialogs as pbd
import pmag_menu_dialogs as pmd
import pmag_widgets as pw



class MagICMenu(wx.MenuBar):
    
    def __init__(self, parent):
        self.parent = parent
        super(MagICMenu, self).__init__()
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
        self.Append(import_menu, 'Import')




    def orient_import1(self, event): 
        orient1 = pmd.ImportOrientFile(self.parent, self.parent.WD)
        
        # first bring up window to select file
        # then bring up window(s) to select options
        # then run orientation_magic.py with command-line options
        print "you clicked item"

    def orient_import2(self, event):
        print 'you clicked item2'

    def orient_import3(self, event):
        print 'you clicked item3'

    def orient_import4(self, event):
        print 'you clicked item4'

    def orient_import5(self, event):
        print 'you clicked item5'

    def anisotropy_import1(self, event):
        print "aniso1"

    def anisotropy_import2(self, event):
        print "aniso2"
    
    def anisotropy_import3(self, event):
        print "aniso3"

    def hysteresis_import1(self, event):
        print "hysteresis1"

    def hysteresis_import2(self, event):
        print "hysteresis2"


    
