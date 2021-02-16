import math

__author__ = 'r_milk01'

import os
import pandas as pd
from configparser import ConfigParser

import matplotlib.pyplot as plt
import matplotlib
import itertools
import logging
import difflib
import colors as color_util

TIMINGS = ['usr', 'sys', 'wall']
MEASURES = ['max', 'avg']
SPECIALS = ['run', 'threads', 'ranks', 'cores']
'''markers = {0: u'tickleft', 1: u'tickright', 2: u'tickup', 3: u'tickdown', 4: u'caretleft', u'D': u'diamond',
           6: u'caretup', 7: u'caretdown', u's': u'square', u'|': u'vline', u'': u'nothing', u'None': u'nothing',
           None: u'nothing', u'x': u'x', 5: u'caretright', u'_': u'hline', u'^': u'triangle_up', u' ': u'nothing',
           u'd': u'thin_diamond', u'h': u'hexagon1', u'+': u'plus', u'*': u'star', u',': u'pixel', u'o': u'circle',
           u'.': u'point', u'1': u'tri_down', u'p': u'pentagon', u'3': u'tri_left', u'2': u'tri_up', u'4': u'tri_right',
           u'H': u'hexagon2', u'v': u'triangle_down', u'8': u'octagon', u'<': u'triangle_left', u'>': u'triangle_right'}
'''
MARKERS = ['s', 'o', 4, 5, 7, '|', '*', 1, 2, 3, 4, 6, 7]
FIGURE_OUTPUTS = ['png', 'pdf', 'pgf']

# pd.options.display.mpl_style = 'default'
# matplotlib.rc('font', family='sans-serif')
# matplotlib.rc('xtick', labelsize=20)
# matplotlib.rc('ytick', labelsize=20)
SMALL_SIZE = 11
MEDIUM_SIZE = 13
BIGGER_SIZE = 16
matplotlib.rc('font', size=MEDIUM_SIZE, family='sans-serif')  # controls default text sizes
matplotlib.rc('axes', titlesize=BIGGER_SIZE)  # fontsize of the axes title
matplotlib.rc('axes', labelsize=BIGGER_SIZE)  # fontsize of the x and y labels
matplotlib.rc('xtick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
matplotlib.rc('ytick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
matplotlib.rc('legend', fontsize=SMALL_SIZE)  # legend fontsize
matplotlib.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

# http://nerdjusttyped.blogspot.de/2010/07/type-1-fonts-and-matplotlib-figures.html
matplotlib.rcParams['ps.useafm'] = True
matplotlib.rcParams['text.usetex'] = True
matplotlib.rcParams['pgf.texsystem'] = 'pdflatex'


def common_substring(strings, glue='_'):
    first, last = strings[0], strings[-1]
    seq = difflib.SequenceMatcher(None, first, last, autojunk=False)
    mb = seq.get_matching_blocks()
    return glue.join([first[m.a : m.a + m.size] for m in mb]).replace(os.path.sep, '')


def make_val(val, round_digits=3):
    try:
        return round(float(val), round_digits)
    except ValueError:
        return str(val)


def m_strip(s, timings=None, measures=None):
    timings = timings or TIMINGS
    measures = measures or MEASURES
    for t, m in itertools.product(timings, measures):
        s = s.replace('_{}_{}'.format(m, t), '')
    return s


def read_files(dirnames, specials=None):
    current = None
    specials = specials or SPECIALS
    header = {'memory': [], 'profiler': [], 'params': [], 'errors': []}
    for fn in dirnames:
        assert os.path.isdir(fn)
        prof = os.path.join(fn, 'profiler.csv')
        try:
            new = pd.read_csv(prof)
        except pd.parser.CParserError as e:
            logging.error('Failed parsing {}'.format(prof))
            raise e
        header['profiler'] = list(new.columns.values)
        params = ConfigParser()
        param_fn = ['dsc_parameter.log', 'dxtc_parameter.log']
        subdirs = ['', 'logs', 'logdata']
        params.read([os.path.join(fn, sd, pfn) for sd, pfn in itertools.product(subdirs, param_fn)])
        p = {}
        for section in params.sections():
            p.update({'{}.{}'.format(section, n): make_val(v) for n, v in params.items(section)})
        p['grids.total_macro_cells'] = math.pow(p['grids.macro_cells_per_dim'], p['grids.dim'])
        p['grids.total_fine_cells'] = p['grids.total_macro_cells'] * math.pow(
            p['grids.micro_cells_per_macrocell_dim'], p['grids.dim']
        )
        param = pd.DataFrame(p, index=[0])
        # mem
        mem = os.path.join(fn, 'memory.csv')
        mem = pd.read_csv(mem)
        new = pd.concat((new, param, mem), axis=1)
        header['memory'] = mem.columns.values
        header['params'] = param.columns.values
        err = os.path.join(fn, 'errors.csv')
        if os.path.isfile(err):
            err = pd.read_csv(err)
            header['errors'] = err.columns.values
            new = pd.concat((new, err), axis=1)

        current = current.append(new, ignore_index=True) if current is not None else new
    # ideal speedup account for non-uniform thread/rank ratio across columns
    count = len(current['ranks'])
    cmp_value = lambda j: current['grids.total_macro_cells'][j] / (current['ranks'][j] * current['threads'][j])
    values = [cmp_value(i) / cmp_value(0) for i in range(0, count)]
    current.insert(len(specials), 'ideal_scaleup', pd.Series(values))
    cmp_value = lambda j: current['ranks'][j] * current['threads'][j]
    values = [cmp_value(i) / cmp_value(0) for i in range(0, count)]
    current.insert(len(specials), 'ideal_speedup', pd.Series(values))
    cores = [cmp_value(i) for i in range(0, count)]
    current.insert(len(specials), 'cores', pd.Series(cores))
    cmp_value = lambda j: current['grids.total_macro_cells'][j] / (current['ranks'][j] * current['threads'][j])
    values = [cmp_value(i) / cmp_value(0) for i in range(0, count)]
    current.insert(len(specials), 'ideal_time', pd.Series(values))

    return header, current


def sorted_f(frame, ascending=True, sort_cols=None):
    sort_cols = sort_cols or ['ranks', 'threads']
    return frame.sort_values(by=sort_cols, na_position='last', ascending=ascending)


def speedup(headerlist, current, baseline_name, specials=None, round_digits=3, timings=None, measures=None):
    timings = timings or TIMINGS
    measures = measures or MEASURES
    specials = specials or SPECIALS
    t_sections = set([m_strip(h) for h in headerlist]) - set(specials)

    for sec in t_sections:
        for t, m in itertools.product(timings, measures):
            source_col = '{}_{}_{}'.format(sec, m, t)
            source = current[source_col]

            speedup_col = source_col + '_speedup'
            ref_value = source[0]
            values = [round(ref_value / source[i], round_digits) for i in range(len(source))]
            current[speedup_col] = pd.Series(values)

            # relative part of overall absolut timing category
            abspart_col = source_col + '_abspart'
            ref_value = lambda j: float(current['{}_{}_{}'.format(baseline_name, m, t)][j])
            values = [round(source[i] / ref_value(i), round_digits) for i in range(len(source))]
            current[abspart_col] = pd.Series(values)

            # relative part of overall total walltime
            wallpart_col = source_col + '_wallpart'
            ref_value = lambda j: float(current['{}_{}_{}'.format(baseline_name, m, 'wall')][j])
            values = [round(source[i] / ref_value(i), round_digits) for i in range(len(source))]
            current[wallpart_col] = pd.Series(values)

        for m in measures:
            # thread efficiency
            source_col = '{}_{}_{}'.format(sec, m, 'usr')
            threadeff_col = source_col + '_threadeff'
            wall = current['{}_{}_{}'.format(sec, m, 'wall')]
            source = current[source_col]
            value = lambda j: float(source[j] / (current['threads'][j] * wall[j]))
            values = [round(value(i), round_digits) for i in range(len(source))]
            current[threadeff_col] = pd.Series(values)

    current = sorted_f(current, True)
    return current


def scaleup(headerlist, current, baseline_name, specials=None, round_digits=3, timings=None, measures=None):
    timings = timings or TIMINGS
    measures = measures or MEASURES
    specials = specials or SPECIALS
    t_sections = set([m_strip(h) for h in headerlist]) - set(specials)

    for sec in t_sections:
        for t, m in itertools.product(timings, measures):
            source_col = '{}_{}_{}'.format(sec, m, t)
            source = current[source_col]

            speedup_col = '{}_{}'.format(source_col, 'scaleup')
            ref_value = source[0]
            values = [round(ref_value / source[i], round_digits) for i in range(len(source))]
            current[speedup_col] = pd.Series(values)

            # relative part of overall absolut timing category
            abspart_col = source_col + '_abspart'
            ref_value = lambda j: float(current['{}_{}_{}'.format(baseline_name, m, t)][j])
            values = [round(source[i] / ref_value(i), round_digits) for i in range(len(source))]
            current[abspart_col] = pd.Series(values)

            # relative part of overall total walltime
            wallpart_col = source_col + '_wallpart'
            ref_value = lambda j: float(current['{}_{}_{}'.format(baseline_name, m, 'wall')][j])
            values = [round(source[i] / ref_value(i), round_digits) for i in range(len(source))]
            current[wallpart_col] = pd.Series(values)

        for m in measures:
            # thread efficiency
            source_col = '{}_{}_{}'.format(sec, m, 'usr')
            threadeff_col = source_col + '_threadeff'
            wall = current['{}_{}_{}'.format(sec, m, 'wall')]
            source = current[source_col]
            value = lambda j: float(source[j] / (current['threads'][j] * wall[j]))
            values = [round(value(i), round_digits) for i in range(len(source))]
            current[threadeff_col] = pd.Series(values)

    current = sorted_f(current, True)
    return current


def plot_msfem(current, filename_base, series_name=None, xcol=None, original=None):
    xcol = xcol or 'cores'
    series_name = series_name or 'speedup'
    categories = ['Elliptic_MsFEM_Solver.apply', 'coarse.solve', 'local.solve_for_all_cells', 'coarse.assemble']
    measure = 'usr'
    ycols = ['msfem.{}_avg_{}_{}'.format(v, measure, series_name) for v in categories] + [
        'ideal_{}'.format(series_name)
    ]
    bar_cols = ['msfem.{}_avg_{}_abspart'.format(v, measure) for v in categories[1:]]
    labels = ['Overall', 'Coarse solve', 'Local assembly + solve', 'Coarse assembly'] + ['Ideal']
    plot_common(
        current,
        filename_base,
        ycols,
        labels,
        bar=(bar_cols, ['Coarse solve', 'Local assembly + solve', 'Coarse assembly']),
        xcol=xcol,
        series_name=series_name,
        logx_base=2,
        logy_base=2,
    )

    ycols = ['msfem.{}_avg_{}'.format(v, measure) for v in categories]
    for col in ycols:
        original[col] = original[col] / 1000.0
    bar_cols = ['msfem.{}_avg_{}_abspart'.format(v, measure) for v in categories[1:]]
    series_name = 'Time (s)'
    labels = ['Overall', 'Coarse solve', 'Local assembly + solve', 'Coarse assembly'] + ['Ideal']
    plot_common(
        original,
        filename_base,
        ycols,
        labels,
        bar=(bar_cols, ['Coarse solve', 'Local assembly + solve', 'Coarse assembly']),
        xcol=xcol,
        series_name=series_name,
        logx_base=2,
        logy_base=10,
        lgd_loc=6,
    )


def plot_fem(current, filename_base, series_name=None, xcol=None):
    xcol = xcol or 'cores'
    series_name = series_name or 'speedup'
    categories = ['apply', 'solve', 'constraints', 'assemble']
    ycols = ['fem.{}_avg_wall_speedup'.format(v) for v in categories] + ['ideal_speedup']
    labels = ['Overall', 'Solve', 'Constraints', 'Assembly', 'Ideal']
    plot_common(current, filename_base, ycols, labels, categories)


def plot_common(
    current,
    filename_base,
    ycols,
    labels,
    xcol,
    series_name,
    bar=None,
    logx_base=None,
    logy_base=None,
    color_map=None,
    bg_color=(1, 1, 1),
    lgd_loc=2,
):
    xlabels = {'cores': '\# Cores', 'grids.total_macro_cells': '\# Macro Cells'}
    fig = plt.figure()
    color_map = color_map or color_util.discrete_cmap(len(labels), bg_color=bg_color)
    subplot = current.plot(x=xcol, y=ycols, colormap=color_map, figsize=(6.3, 3.5))
    # [‘solid’ | ‘dashed’, ‘dashdot’, ‘dotted’ | (offset, on - off - dash - seq) | '-' | '--' | '-.' | ':' | 'None' | ' ' | '']

    for i, line in enumerate(subplot.lines):
        if i == len(subplot.lines) - 1:
            line.set_linestyle('dashed')
        line.set_marker(MARKERS[i])
    plt.ylabel(series_name.capitalize())
    plt.xlabel(xlabels[xcol])
    ax = subplot.figure.axes[0]
    if logx_base is not None:
        ax.set_xscale('log', basex=logx_base)
    if logy_base is not None:
        ax.set_yscale('log', basey=logy_base)
    lgd = plt.legend(ax.lines, labels, loc=lgd_loc)  # , bbox_to_anchor=(1.05, 1),  borderaxespad=0., loc=2)
    ax.set_facecolor(bg_color)
    lgd.get_frame().set_facecolor(bg_color)

    tt = current[xcol].array
    plt.xticks(ticks=tt, labels=[str(t) for t in tt])

    for fmt in FIGURE_OUTPUTS:
        plt.savefig(filename_base + '_{}.{}'.format(series_name, fmt), bbox_extra_artists=(lgd,), bbox_inches='tight')

    if bar is None:
        return
    cols, labels = bar
    fig = plt.figure()
    ax = current[cols].plot(kind='bar', stacked=True, colormap=color_map)
    patches, _ = ax.get_legend_handles_labels()

    lgd = ax.legend(patches, labels, bbox_to_anchor=(1.05, 1), borderaxespad=0.0, loc=2)

    plt.savefig(f'{filename_base}_{series_name}_pie.png', bbox_extra_artists=(lgd,), bbox_inches='tight')


def plot_error(
    data_frame, filename_base, error_cols, xcol, labels, baseline_name, logx_base=None, logy_base=None, color_map=None
):
    fig = plt.figure()

    # normed walltime
    normed = 'normed_walltime'
    w_time = data_frame['{}_avg_wall'.format(baseline_name)]
    count = len(w_time)
    values = [w_time[i] / w_time.max() for i in range(0, count)]
    # data_frame.insert(0, normed, pd.Series(values))

    color_map = color_map or color_util.discrete_cmap(len(labels))
    ax = data_frame.plot(x=xcol, y=error_cols, colormap=color_map)
    for i, line in enumerate(ax.lines):
        line.set_marker(MARKERS[i])
    plt.ylabel('Error')
    plt.xlabel('Cells')

    if logx_base is not None:
        ax.set_xscale('log', basex=logx_base)
    if logy_base is not None:
        ax.set_yscale('log', basey=logy_base)
    lgd = plt.legend(ax.lines, labels, loc=2)  # , bbox_to_anchor=(1.05, 1),  borderaxespad=0., loc=2)

    common = common_substring(error_cols)
    for fmt in FIGURE_OUTPUTS:
        plt.savefig('{}_{}.{}'.format(filename_base, common, fmt), bbox_extra_artists=(lgd,), bbox_inches='tight')
