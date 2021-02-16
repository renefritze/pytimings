#!/usr/bin/env python3
import logging
import sys

import pandas_common as pc

common_string = pc.common_substring(sys.argv[1:])
merged = 'merged_{}.csv'.format(common_string)
baseline_name = 'msfem.all'

header, current = pc.read_files(sys.argv[1:])
headerlist = header['profiler']
current = pc.sorted_f(current, True)
speedup = pc.speedup(headerlist, current, baseline_name)
# pprint(t_sections)
pc.plot_msfem(speedup, merged, original=current)
try:
    pc.plot_error(
        speedup,
        merged,
        ['msfem_exactH1s', 'msfem_exact_L2'],
        'grids.macro_cells_per_dim',
        ['$H^1_s$', '$L^2$', 'walltime'],
        baseline_name,
        logy_base=10,
    )
except KeyError:
    logging.error('No error data')
speedup.transpose().to_csv(merged)
# current.transpose().to_excel(merged+'.xls')
# current.to_csv(merged)
