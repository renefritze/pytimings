#!/usr/bin/env python3

import os
import sys
import itertools
import matplotlib as mpl

import pandas_common as pc


def plot_mlmc(current, filename_base):
    all = ['mlmc.all', 'fem.apply', 'msfem.Elliptic_MsFEM_Solver.apply']
    all_labels = ['Overall', 'CgFem', 'MsFem', 'Ideal']
    simple = ['mlmc.all']
    for pref, tpl in {'all': (all, all_labels), 'simple': (simple, ['Overall', 'Ideal'])}.items():
        cat, labels = tpl
        ycols = ['{}_avg_wall_speedup'.format(v) for v in cat] + ['ideal_speedup']
        pc.plot_common(current, '{}_{}'.format(pref, filename_base), ycols, labels)


common_string = pc.common_substring(sys.argv[1:])
merged = 'merged_{}.csv'.format(common_string)
baseline_name = 'mlmc.all'

header, current = pc.read_files(sys.argv[1:])
headerlist = header['profiler']
current = pc.sorted_f(current, True)
# full = pc.speedup(headerlist, current.copy(), baseline_name)
# full.transpose().to_csv(merged)
current = pc.speedup(headerlist, current, baseline_name)
# pprint(t_sections)
plot_mlmc(current, merged)

current.transpose().to_csv('filtered_' + merged)
