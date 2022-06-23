# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as colors
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
import numpy as np
import Orange
import seaborn as sns
import sys
import pandas as pd
import os
import csv
import logging
import math
import pickle

_DEFAULT_TICKS_COUNT = 12
_DEFAULT_LABEL_ROTATION = 30
DEFAULT_SNAPSHOT_SECONDS = 15 * 60  # Seconds.

BIGGER_SIZE = 16


plt.rc('font', size=BIGGER_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=BIGGER_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=BIGGER_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=BIGGER_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=BIGGER_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=BIGGER_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

fuzzer_names = {
    'afl': 'AFL',
    'aflplusplus': 'AFL++',
    'eclipser': 'Eclipser',
    'fairfuzz': 'FairFuzz',
    'libfuzzer': 'LibFuzzer'
  }


def combine_progs(experiment_df):
  grouping1 = ['fuzzer', 'benchmark', 'time', 'trial_id', 'single_crash_covered']
  grouping2 = ['fuzzer', 'time']
  grouping3 = ['fuzzer', 'benchmark', 'time']
  grouping4 = ['fuzzer', 'time', 'trial_index']
  grouping5 = ['fuzzer', 'benchmark']
  df = experiment_df[grouping1].sort_values(['fuzzer', 'benchmark', 'trial_id', 'time'])
  df = df.drop(columns=['trial_id'])
  df = df.groupby(grouping3).median().reset_index()
  df = df.groupby(grouping2).sum().reset_index()
  df['benchmark'] = 'combined'

  def addRow(x):
    #x = x.append({'fuzzer': x.name[0] , 'time': 0, 'single_crash_covered': 0.0, 'benchmark': x.name[1]}, ignore_index=True)
    x.loc[-1] = {'fuzzer': x.name[0] , 'time': 0, 'single_crash_covered': 0.0, 'benchmark': x.name[1]}
    x.index = x.index + 1  # shifting index
    x.sort_index(inplace=True) 
    return x

  df = df.groupby(grouping5).apply(addRow).reset_index(drop=True)
  
  with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(df)
  return df

def benchmark_rank_by_mean(benchmark_snapshot_df, key='edges_covered'):
    """Returns ranking of fuzzers based on mean coverage."""
    assert benchmark_snapshot_df.time.nunique() == 1, 'Not a snapshot!'
    means = benchmark_snapshot_df.groupby('fuzzer')[key].mean()
    means.rename('mean cov', inplace=True)
    return means.sort_values(ascending=False)


def _write_plot_to_image(plot_function,
                         data,
                         image_path,
                         wide=False,
                         **kwargs):
    """Writes the result of |plot_function(data)| to |image_path|.

    If |wide|, then the image size will be twice as wide as normal.
    """
    width = 4.8
    height = 4.8
    figsize = (2 * width, height) if wide else (width, height)
    fig, axes = plt.subplots(figsize=figsize)
    try:
        plot_function(data, axes=axes, **kwargs)
        fig.savefig(image_path, bbox_inches="tight", dpi=300)
    finally:
        plt.close(fig)

def _formatted_title(benchmark_snapshot_df):
    """Return a formatted title with time and trial count."""
    benchmark_name = benchmark_snapshot_df.benchmark.unique()[0]
    stats_string = ""
    #stats_string += ' ('

    snapshot_time = benchmark_snapshot_df.time.unique()[0]
    stats_string += _formatted_hour_min(snapshot_time)

    trial_count = 3
    stats_string += ', %d trials/fuzzer' % trial_count
    #stats_string += ')'
    return stats_string

def _formatted_hour_min(seconds):
    """Turns |seconds| seconds into %H:%m format.

    We don't use to_datetime() or to_timedelta(), because we want to
    show hours larger than 23, e.g.: 24h:00m.
    """
    time_string = ''
    hours = int(seconds / 60 / 60)
    minutes = int(seconds / 60) % 60
    if hours:
        time_string += '%d' % hours
    if minutes:
        if hours:
            time_string += ':'
        time_string += '%dm' % minutes
    return time_string

def growth_plot(benchmark_df,
                     axes=None,
                     logscale=False,
                     interest="single_crash_covered"):
    """Draws edge (or bug) coverage growth plot on given |axes|.

    The fuzzer labels will be in the order of their mean coverage at the
    snapshot time (typically, the end of experiment).
    """

    _COLOR_PALETTE = [
        '#1f77b4',
        '#98df8a',
        '#d62728',
        '#c7c7c7',
        '#ff7f0e',
        '#ff9896',
        '#e377c2',
        '#dbdb8d',
        '#2ca02c',
        '#c5b0d5',
        '#7f7f7f',
        '#9edae5',
        '#aec7e8',
        '#8c564b',
        '#c49c94',
        '#bcbd22',
        '#ffbb78',
        '#9467bd',
        '#f7b6d2',
        '#17becf',
    ]

    _MARKER_PALETTE = [
        'o', 'v', '^', '<', '>', '8', 's', 'p', '*', 'h', 'H', 'D', 'd', 'P',
        'X', ',', '+', 'x', '|', '_'
    ]

    fuzzer_colors = {
      fuzzer: _COLOR_PALETTE[idx % len(_COLOR_PALETTE)]
      for idx, fuzzer in enumerate(sorted(fuzzer_names_list))
    }
    fuzzer_markers = {
      fuzzer: _MARKER_PALETTE[idx % len(_MARKER_PALETTE)]
      for idx, fuzzer in enumerate(sorted(fuzzer_names_list))
    }

    column_of_interest = interest
    benchmark_snapshot_df = benchmark_df[benchmark_df.time == 86400]
    snapshot_time = benchmark_snapshot_df.time.unique()[0]
    fuzzer_order = benchmark_rank_by_mean(
        benchmark_snapshot_df, key=column_of_interest).index
    fuzzers_named = list(map(lambda x: fuzzer_names[x], fuzzer_order))

    axes = sns.lineplot(
        y=column_of_interest,
        x='time',
        hue='fuzzer',
        hue_order=fuzzer_order,
        data=benchmark_df[benchmark_df.time <= snapshot_time],
        ci=None,
        estimator=np.median,
        palette=fuzzer_colors,
        style='fuzzer',
        dashes=False,
        markers=fuzzer_markers,
        ax=axes)

    #axes.set_title(_formatted_title(benchmark_snapshot_df))

    # Indicate the snapshot time with a big red vertical line.
    axes.axvline(x=snapshot_time, color='r')

    # Move legend outside of the plot.
    axes.legend(fuzzers_named, loc='lower right',
                bbox_to_anchor=(0.6875, 0.05),
                mode ='expand',
                frameon=False)

    axes.set(ylabel='Number of individual causes')
    axes.set(xlabel='Time (hour)')

    if logscale:
      axes.set_xscale('log')
      ticks = np.logspace(
        # Start from the time of the first measurement.
        np.log10(DEFAULT_SNAPSHOT_SECONDS),
        np.log10(snapshot_time + 1),  # Include tick at end time.
        _DEFAULT_TICKS_COUNT)
    else:
      ticks = np.arange(
        0,
        snapshot_time + 1,  # Include tick at end time.
        snapshot_time / _DEFAULT_TICKS_COUNT / 2)

    axes.set_xticks(ticks)
    axes.set_xticklabels([_formatted_hour_min(t) for t in ticks])

    axes.spines['left'].set_position(('data', 0))
    axes.spines['bottom'].set_position(('data', 0))

    #axes.set_xlim(xmin=0, xmax=86400)
    axes.set_ylim(0, int(math.ceil(1.05* maxy / 10.0)) * 10)

    sns.despine(ax=axes, trim=True)

def generate_df(out_dir, fuzzers, programs):
  time_ticks = [i*900 for i in range(0, 97)]
  df_rows = []

  for program in programs:
    prog_out_dir = os.path.join(out_dir, program)
    for fuzzer in fuzzers:
      target_out_dir = os.path.join(prog_out_dir, fuzzer)
      with open(os.path.join(target_out_dir, 'crash_seeds.pickle'), 'rb') as f:
        crash_seeds_by_trial = pickle.load(f)

      for trial_name, seeds in crash_seeds_by_trial.items():
        indi_by_time = {t: set() for t in time_ticks}
        for seed in seeds:
          # the time unit are all messed up, correct here
          if fuzzer == 'aflplusplus':
            seed['time'] = format(float(seed['time']) / 10, '.2f')
          else:
            seed['time'] = format(float(seed['time']) * 100, '.2f')
          for crashset in seed['min_crashsets']:
            if len(crashset) == 1:
              index = crashset[0]
              seed_tick = int(float(seed['time']) / 900) * 900 + 900
              if seed_tick > 86400:
                seed_tick = 86400
              indi_by_time[seed_tick].add(index)

        pre_tick = -900
        for tick in time_ticks:
          if pre_tick >= 0:
            indi_by_time[tick].update(indi_by_time[pre_tick])
          pre_tick = tick
        for tick in time_ticks:
          df_rows.append([fuzzer, program, tick, trial_name, len(indi_by_time[tick])])
                
  df = pd.DataFrame(df_rows, columns=['fuzzer', 'benchmark', 'time', 'trial_id', 'single_crash_covered'])
  return df

def generate_growth_plot(out_dir, fuzzers, programs):
  global fuzzer_names_list
  fuzzer_names_list = fuzzers

  df = generate_df(out_dir, fuzzers, programs)
  combined_df = combine_progs(df)

  global maxy
  maxy = combined_df['single_crash_covered'].max()

  _write_plot_to_image(growth_plot, combined_df,
                                  os.path.join(out_dir, 'single_crash_growth.pdf'),
                                  wide=True,
                                  logscale=False,
                                  interest='single_crash_covered')
