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
import json
import math
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
import os

from common.confighelper import ConfigHelper

_DEFAULT_TICKS_COUNT = 12
_DEFAULT_LABEL_ROTATION = 30
REPORT_INTERVAL = 15 * 60  # Seconds.
BIGGER_SIZE = 16

plt.rc('font', size=BIGGER_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=BIGGER_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=BIGGER_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=BIGGER_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=BIGGER_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=BIGGER_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

def _write_plot_to_image(plot_function,
                         data: pd.DataFrame,
                         helper: ConfigHelper,
                         image_path: str,
                         wide=False,
                         **kwargs) -> None:
    """Writes the result of |plot_function(data)| to |image_path|.

    If |wide|, then the image size will be twice as wide as normal.
    """
    width = 4.8
    height = 4.8
    figsize = (2 * width, height) if wide else (width, height)
    fig, axes = plt.subplots(figsize=figsize)
    try:
        plot_function(data, helper, axes=axes, **kwargs)
        fig.savefig(image_path, bbox_inches="tight", dpi=300)
    finally:
        plt.close(fig)


def _formatted_title(interest: str, ending_time: int, trials: int) -> str:
    """Return a formatted title with time and trial count."""
    return f'{interest} ({_formatted_hour_min(ending_time)}, {trials} trials/fuzzer)'


def _formatted_hour_min(seconds: int) -> str:
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


def draw(df: pd.DataFrame,
         helper: ConfigHelper,
         axes=None,
         logscale: bool=False,
         interest: str="single_cause") -> None:
    """Draws reach/trigger/cause growth plot on given |axes|.

    The fuzzer labels will be in the order of their median interest values at
    the end of experiment.
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
      for idx, fuzzer in enumerate(sorted(df.fuzzer.unique()))
    }
    fuzzer_markers = {
      fuzzer: _MARKER_PALETTE[idx % len(_MARKER_PALETTE)]
      for idx, fuzzer in enumerate(sorted(df.fuzzer.unique()))
    }

    column_of_interest = interest
    ending_time = int(helper.timeout() * 3600)
    ending_df = df[df.time == ending_time]
    fuzzer_order = ending_df.sort_values([column_of_interest], ascending=False)['fuzzer']

    axes = sns.lineplot(
        y=column_of_interest,
        x='time',
        hue='fuzzer',
        hue_order=fuzzer_order,
        data=df,
        errorbar=None,
        palette=fuzzer_colors,
        style='fuzzer',
        dashes=False,
        markers=fuzzer_markers,
        ax=axes)

    # TODO: Detect when experiments have variable number of trials.
    axes.set_title(_formatted_title(interest, ending_time, helper.num_trials()))

    # Indicate the ending time with a big red vertical line.
    axes.axvline(x=ending_time, color='r')

    # Move legend outside the plot.
    axes.legend(fuzzer_order, loc='lower right',
                bbox_to_anchor=(0.6875, 0.05),
                mode ='expand',
                frameon=False)

    axes.set(ylabel='Number of individual causes')
    axes.set(xlabel='Time (hour)')

    if logscale:
      axes.set_xscale('log')
      ticks = np.logspace(
        # Start from the time of the first measurement.
        np.log10(REPORT_INTERVAL),
        np.log10(ending_time + 1),  # Include tick at end time.
        _DEFAULT_TICKS_COUNT)
    else:
      ticks = np.arange(
        0,
        ending_time + 1,  # Include tick at end time.
        ending_time / _DEFAULT_TICKS_COUNT / 2)

    axes.set_xticks(ticks)
    axes.set_xticklabels([_formatted_hour_min(t) for t in ticks])

    axes.spines['left'].set_position(('data', 0))
    axes.spines['bottom'].set_position(('data', 0))

    axes.set_ylim(0, int(math.ceil(1.05* df[column_of_interest].max() / 10.0)) * 10)

    sns.despine(ax=axes, trim=True)


def generate_df(helper: ConfigHelper,
                interest: str= 'single_cause') -> pd.DataFrame:
    ticks = range(0, int(helper.timeout()*3600)+REPORT_INTERVAL, REPORT_INTERVAL)
    rows = []
    type_keys = {'single_cause': 'crashes',
                 'all_cause': 'crashes',
                 'reach': 'reaches',
                 'trigger': 'triggers'}

    for benchmark in helper.benchmarks():
        for fuzzer in helper.fuzzers():
            for trial in helper.trials(benchmark, fuzzer):
                with open(helper.parsed_seeds_store(benchmark, fuzzer, trial, 'crash'), 'r') as f:
                    crashed_seeds = json.load(f)
                vals_by_time = {t: set() for t in ticks}
                for seed in crashed_seeds:
                    # Map to the smallest tick that is larger than the seed generation time.
                    tick = min(int(seed['time'] / REPORT_INTERVAL + 1) * REPORT_INTERVAL, ticks[-1])
                    print(int(seed['time'] / REPORT_INTERVAL))
                    for val_list in seed[type_keys[interest]]:
                        if interest == 'single_cause' and len(val_list) != 1:
                            continue
                        vals_by_time[tick] |= set(val_list)
                # Vals of a tick should contain all vals in preceding ticks.
                for i in range(1, len(ticks)):
                    vals_by_time[ticks[i]] |= vals_by_time[ticks[i-1]]
                for tick in ticks:
                  rows.append([benchmark, fuzzer, tick, trial, len(vals_by_time[tick])])

    df = pd.DataFrame(rows, columns=['benchmark', 'fuzzer', 'time', 'trial', interest])
    df = df.sort_values(['fuzzer', 'benchmark', 'trial', 'time']).drop(columns=['trial'])
    # Median over trials.
    df = df.groupby(['fuzzer', 'benchmark', 'time']).median().reset_index().drop(columns=['benchmark'])
    # Sum over benchmarks.
    df = df.groupby(['fuzzer', 'time']).sum().reset_index()
    return df


def growth_plot(helper: ConfigHelper,
                interest='single_cause') -> None:
    df = generate_df(helper)
    _write_plot_to_image(draw, df, helper,
                         os.path.join(helper.out_dir(), f'{interest}_growth.png'),
                         wide=True,
                         logscale=False,
                         interest=interest)
