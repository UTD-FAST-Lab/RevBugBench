import sys
import pandas as pd
import os
import logging
import matplotlib
import pickle
matplotlib.use('Agg')

import include.pyvenn.venn as venn

matplotlib.pyplot.rc('font', size=12)

fuzzer_names = {
    'afl': 'AFL',
    'aflplusplus': 'AFL++',
    'eclipser': 'Eclipser',
    'fairfuzz': 'FairFuzz',
    'libfuzzer': 'LibFuzzer'
  }

def draw_venn_graph(out_dir, fuzzers, programs):
  single_crash_sets = []

  for fuzzer in fuzzers:
    fuzzer_indi_set = set()
    for program in programs:
      prog_out_dir = os.path.join(out_dir, program)
      target_out_dir = os.path.join(prog_out_dir, fuzzer)
      with open(os.path.join(target_out_dir, 'crash_seeds.pickle'), 'rb') as f:
        crash_seeds_by_trial = pickle.load(f)

      for trial_name, seeds in crash_seeds_by_trial.items():
        for seed in seeds:
          for crashset in seed['min_crashsets']:
            if len(crashset) == 1:
              fuzzer_indi_set.add(f'{program}:{crashset[0]}')

    single_crash_sets.append(fuzzer_indi_set)

  print(single_crash_sets)
  unique_keys = set.union(*single_crash_sets)
  print(f'total number of single causes found: {len(unique_keys)}')

  labels = venn.get_labels(single_crash_sets, fill=['number'])
  fig, ax = venn.venn5(labels, names=list(map(lambda x: fuzzer_names[x], fuzzers)))
  fig.savefig(os.path.join(out_dir, 'total_venn.png'))
  matplotlib.pyplot.clf()

if __name__ == '__main__':
  if len(sys.argv) != 2 or not os.path.exists(sys.argv[1]):
    sys.exit(0)
  csv_path = sys.argv[1]

  df = pd.read_csv(csv_path)

  logging.basicConfig(stream=sys.stderr, level=logging.INFO)

  programs = df['benchmark'].unique()
  fuzzers = df['fuzzer'].unique()

  single_crash_sets = []
  for fuzzer in fuzzers:
    single_crashes = set()
    for prog in programs:
      logging.info(f'collecting single causes of {prog} - {fuzzer}')

      program_fuzzer_filter = (df['benchmark'] == prog) & (df['fuzzer'] == fuzzer)
      program_fuzzer_df = df[program_fuzzer_filter]

      trials = program_fuzzer_df['trial_id'].unique()

      for trial in trials:
        trial_filter = program_fuzzer_df['trial_id'] == trial
        trial_df = program_fuzzer_df[trial_filter]

        crash_df = trial_df.dropna(subset=['fr_crashes']).assign(fr_crash_key=trial_df['fr_crashes'].str.split(',')).explode('fr_crash_key')
        unique_crash_keys = crash_df['fr_crash_key'].dropna().unique()

        single_crash_keys = set()
        for key in unique_crash_keys:
          comma_split = key.split('+')
          if len(comma_split) == 1:
            single_crashes.add(f'{prog}:{int(comma_split[0])}')

    single_crash_sets.append(single_crashes)

  print(single_crash_sets)
  unique_keys = set.union(*single_crash_sets)
  print(f'total number of single causes found: {len(unique_keys)}')


