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
        # make a backup of McMurdo images.txt file
        copyfile(os.path.join(WD, 'data_files', '3_0', 'McMurdo', "images.txt"), os.path.join(WD, 'data_files', '3_0', 'McMurdo', "images.txt.bak"))


    def tearDown(self):
        #return
        glob_strings = ["*.png", "*errors*", "log.txt"]
        for glob_string in glob_strings:
            for filename in glob.glob(glob_string):
                os.remove(filename)
        # remove Osler images file if one was created
        if os.path.exists(os.path.join(WD, 'data_files', '3_0', 'Osler', "images.txt")):
            os.remove(os.path.join(WD, 'data_files', '3_0', 'Osler', "images.txt"))
        os.chdir(WD)
        # restore McMurdo images.txt to original
        copyfile(os.path.join(WD, 'data_files', '3_0', 'McMurdo', "images.txt"), os.path.join(WD, 'data_files', '3_0', 'McMurdo', "last_images.txt"))
        copyfile(os.path.join(WD, 'data_files', '3_0', 'McMurdo', "images.txt.bak"), os.path.join(WD, 'data_files', '3_0', 'McMurdo', "images.txt"))


    def test_make_plots(self):
        dir_path = os.path.join(WD, 'data_files', '3_0', 'Osler')
        image_file = os.path.join(dir_path, 'images.txt')
        os.chdir(dir_path)
        for filename in glob.glob("*error*"):
            os.remove(filename)
        os.system("new_make_magic_plots.py")
        self.assertFalse(glob.glob("errors.txt"))
        self.assertTrue(os.path.exists(image_file))
        lines = pmag.magic_read(image_file)[0]
        for line in lines:
            print(line)
        self.assertEqual(len(lines), 4)
        self.assertFalse("image" in lines[0].keys())

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
        for filename in glob.glob("*error*"):
            os.remove(filename)
        os.system("new_make_magic_plots.py")
        lines = pmag.magic_read("images.txt")[0]
        self.assertEqual(len(lines), 532)
        self.assertFalse("image" in lines[0].keys())
        self.assertFalse(glob.glob("errors.txt"))
        if pmagplotlib.isServer:
            num_pngs = len(glob.glob("*png"))
            num_thumbnails = len(glob.glob("*thumb.png"))
            self.assertEqual(num_pngs / 2, num_thumbnails)
            self.assertFalse(glob.glob("thumbnail_errors.txt"))
