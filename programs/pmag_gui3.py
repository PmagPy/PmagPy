#!/usr/bin/env pythonw

import sys
import wx
import matplotlib


def main():
    if '-h' in sys.argv:
        print "See https://earthref.org/PmagPy/cookbook/#pmag_gui.py for a complete tutorial"
        sys.exit()
    from programs import pmag_gui
    from pmagpy import pmag
    print '-I- Starting Pmag GUI 3 - please be patient'
    # if redirect is true, wxpython makes its own output window for stdout/stderr
    app = wx.App(redirect=True)
    app.frame = pmag_gui.MagMainFrame(DM=3)
    working_dir = pmag.get_named_arg_from_sys('-WD', '.')
    ## this causes an error with Canopy Python
    ## (it works with brew Python)
    ## need to use these lines for Py2app
    if working_dir == '.':
        app.frame.on_change_dir_button(None)

    app.frame.Show()
    app.frame.Center()
    ## use for debugging:
    #if '-i' in sys.argv:
    #    import wx.lib.inspection
    #    wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()

if __name__ == "__main__":
    main()
