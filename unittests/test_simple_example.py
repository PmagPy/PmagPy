#!/usr/bin/env python

import wx
import unittest
print wx.version

class TestMyDialog(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_fake(self):
        self.assertEqual(1, 2)



if __name__ == '__main__':
    unittest.main()        
