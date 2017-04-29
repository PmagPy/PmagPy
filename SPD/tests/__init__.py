#!/usr/bin/env python

# __init__.py: -*- Python -*-  DESCRIPTIVE TEXT.
# 
#  Copyright (c) 2014 Lori Jonestrask
#  Author: Lori Jonestrask (mintblue87@gmail.com) .


from __future__ import absolute_import
__all__ = ['test_arai_plot_statistics', 'test_curvature', 'test_directional_statistics', 'test_ptrm_statistics', 'test_tail_check_statistics', 'test_additivity_check_statistics']

from . import test_arai_plot_statistics
#test_arai_plot_statistics.run_all_tests()
from . import test_curvature
from . import test_directional_statistics
from . import test_ptrm_statistics
from . import test_tail_check_statistics
from . import test_additivity_check_statistics

