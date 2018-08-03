"""
tests for magic_gui
"""

import wx
import unittest
import os
#import dialogs.pmag_widgets as pmag_widgets
from pmagpy import pmag
from pmagpy import contribution_builder as cb
from pmagpy import data_model3 as data_model
from pmagpy import controlled_vocabularies3 as cv3

# set constants
DMODEL = data_model.DataModel()
WD = pmag.get_test_WD()
PROJECT_WD = os.path.join(WD, "data_files", "magic_gui", "3_0")


class TestVocabularies(unittest.TestCase):

    def setUp(self):
        self.vocab = cv3.Vocabulary()

    def tearDown(self):
        pass

    def test_vocabularies(self):
        self.assertIn('timescale_era', self.vocab.vocabularies.index)
        self.assertIn('Neoproterozoic', self.vocab.vocabularies.loc['timescale_era'])

    def test_suggested(self):
        self.assertIn('fossil_class', self.vocab.suggested.index)
        self.assertIn('Anthozoa', self.vocab.suggested.loc['fossil_class'])


    def test_methods(self):
        self.assertIn('sample_preparation', list(self.vocab.methods.keys()))
        for item in self.vocab.methods['sample_preparation']:
            self.assertTrue(item.startswith('SP-'))

    def test_all_codes(self):
        self.assertIn('SM-TTEST', self.vocab.all_codes.index)
        self.assertEqual('statistical_method',
                         self.vocab.all_codes.loc['SM-TTEST']['dtype'])
