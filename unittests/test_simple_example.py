#!/usr/bin/env python

import wx
import unittest

class TestMyDialog(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = wx.Frame(None)

    def tearDown(self):
        self.app.Exit()

    def test_fake(self):
        print wx.__version__
        self.assertEqual(1,1)



if __name__ == '__main__':
    unittest.main()        
