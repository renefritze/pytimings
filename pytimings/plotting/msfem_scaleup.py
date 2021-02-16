#!/usr/bin/env python3
import logging
import sys
import traceback

import pandas_common as pc

common_string = pc.common_substring(sys.argv[1:])
merged = 'merged_{}.csv'.format(common_string)
baseline_name = 'msfem.all'


def _get(func_name='scaleup'):
    header, current = pc.read_files(sys.argv[1:])
    headerlist = header['profiler']
    current = pc.sorted_f(current, True)
    func = getattr(pc, func_name)
    current = func(headerlist, current, baseline_name)
    current.transpose().to_csv('{}_{}'.format(merged, func_name))
    return current


current = _get('scaleup')
pc.plot_msfem(current, merged, series_name='scaleup', xcol='grids.total_macro_cells')

current = _get('speedup')
pc.plot_msfem(current, merged, series_name='speedup', xcol='cores')

try:
    pc.plot_error(
        data_frame=current,
        filename_base='{}_errors'.format(merged),
        error_cols=['msfem_exact_H1s', 'msfem_exact_L2', 'fem_exact_H1s', 'fem_exact_L2'],
        xcol='grids.micro_cells_per_macrocell_dim',
        labels=['MsFEM $H^1_s$', 'MsFEM $L^2$', 'CgFEM $H^1_s$', 'CgFEM $L^2$'],
        baseline_name=baseline_name,
        logy_base=10,
        logx_base=2,
    )
except KeyError as k:
    logging.error('No error data')
    logging.error(traceback.format_exc())
# current.transpose().to_excel(merged+'.xls')
# current.to_csv(merged)
