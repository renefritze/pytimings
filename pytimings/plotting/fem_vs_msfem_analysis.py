#!/usr/bin/env python3


import sys
import os
import pandas_common as pc

common_string = pc.common_substring(sys.argv[1:])
merged = 'merged_{}.csv'.format(common_string)
baseline_name = 'msfem.all'

header, current = pc.read_files(sys.argv[1:])
headerlist = header['profiler']
current = pc.sorted_f(current, True)
current = pc.speedup(headerlist, current, baseline_name)
# pprint(t_sections)
current.transpose().to_csv(merged)
pc.plot_fem(current, merged)
