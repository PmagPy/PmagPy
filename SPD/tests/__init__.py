#!/usr/bin/env python

# __init__.py: -*- Python -*-  DESCRIPTIVE TEXT.
# 
#  Copyright (c) 2014 Lori Jonestrask
#  Author: Lori Jonestrask (mintblue87@gmail.com) .


__all__ = ['test_arai_plot_statistics', 'test_curvature', 'test_directional_statistics', 'test_ptrm_statistics', 'test_tail_check_statistics', 'test_additivity_check_statistics']

import test_arai_plot_statistics
#test_arai_plot_statistics.run_all_tests()
import test_curvature
import test_directional_statistics
import test_ptrm_statistics
import test_tail_check_statistics
import test_additivity_check_statistics

