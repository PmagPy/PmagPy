import wx
import unittest
import os
import make_magic

WD = os.getcwd()

class TestMakeMagicMainFrame(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        #WD = os.path.join(os.getcwd(), 'unittests', 'examples', 'my_project')
        self.frame = make_magic.MainFrame(WD, "my panel")
        self.pnl = self.frame.GetChildren()[0]

    def tearDown(self):
        #self.frame.Destroy() # this does not work and causes strange errors
        self.app.Destroy()
        os.chdir(WD)

    def test_main_panel_is_created(self):
        """
        test for existence of main panel
        """
        self.assertTrue(self.pnl.IsEnabled())
        self.assertEqual("my panel", str(self.pnl.GetName()))

    def test_grid_is_created(self):
        """
        """
        self.assertTrue(self.frame.grid)

