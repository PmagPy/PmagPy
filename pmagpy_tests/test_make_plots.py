#!/usr/bin/env python

import unittest
import os
# import random
import glob
from pmagpy import pmag
from pmagpy import pmagplotlib
from pmag_env import set_env
from shutil import copyfile

WD = pmag.get_test_WD()

@unittest.skipIf(not pmagplotlib.isServer, "these tests are mainly needed when isServer is True, and don't work on Travis at all")
class TestMakeMagicPlots(unittest.TestCase):

    def setUp(self):
        set_env.set_server(True)
        for filename in glob.glob("*error*"):
            os.remove(filename)

    def tearDown(self):
        glob_strings = ["*.png", "*errors*", "log.txt"]
        for glob_string in glob_strings:
            for filename in glob.glob(glob_string):
                os.remove(filename)
        os.chdir(WD)

    def test_make_plots(self):
        dir_path = os.path.join(WD, 'data_files', '3_0', 'Osler')
        os.chdir(dir_path)
        for filename in glob.glob("*error*"):
            os.remove(filename)
        os.system("new_make_magic_plots.py")
        self.assertFalse(glob.glob("errors.txt"))
        if pmagplotlib.isServer:
            self.assertFalse(glob.glob("thumbnail_errors.txt"))
            self.assertEqual(14, len(glob.glob("*.png")))
            self.assertEqual(7, len(glob.glob("*thumb*.png")))
        else:
            self.assertEqual(10, len(glob.glob("*.png")))
            self.assertEqual(5, len(glob.glob("*thumb*.png")))


    def test_make_plots_long(self):
        #if not pmagplotlib.isServer:
        #    # only run this annoyingly slow test 10% of the time
        #    num = random.randint(1, 10)
        #    if num != 3:
        #        return
        # make a backup of images.txt
        os.chdir(os.path.join(WD, 'data_files', '3_0', 'McMurdo'))
        copyfile("images.txt", "images.txt.bak")
        for filename in glob.glob("*error*"):
            os.remove(filename)
        os.system("new_make_magic_plots.py")
        lines = pmag.magic_read("images.txt")[0]
        self.assertEqual(len(lines), 491)
        self.assertFalse("image" in lines[0].keys())
        # restore images.txt to original
        copyfile("images.txt.bak", "images.txt")
        self.assertFalse(glob.glob("errors.txt"))
        if pmagplotlib.isServer:
            num_pngs = len(glob.glob("*png"))
            num_thumbnails = len(glob.glob("*thumb.png"))
            self.assertEqual(num_pngs / 2, num_thumbnails)
            self.assertFalse(glob.glob("thumbnail_errors.txt"))
