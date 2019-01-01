#!/usr/bin/env python

import unittest
from pmag_env import set_env

class TestEnvVariables(unittest.TestCase):

    def test_is_server(self):
        self.assertFalse(set_env.isServer)

    def test_is_frozen(self):
        self.assertFalse(set_env.IS_FROZEN)

    def test_is_notebook(self):
        self.assertFalse(set_env.IS_NOTEBOOK)
