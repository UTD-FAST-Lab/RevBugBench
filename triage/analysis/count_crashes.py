import sys
import os
import pickle
import csv
import logging
import statistics
import itertools
import json
from prettytable import PrettyTable

import setup
from utils.common import dump_to_pickle


PATTERNS = ['COND_ABORT', 'COND_EXEC', 'COND_ASSIGN']

def count_crashes_by_trial(prog_out_dir, target_out_dir):
  indi_by_trial = {}
  comb_by_trial = {}

  with open(os.path.join(target_out_dir, 'crash_seeds.pickle'), 'rb') as f:
    seeds_by_trial = pickle.load(f)

  with open(os.path.join(prog_out_dir, 'dda.json'), 'r') as f:
    jData = json.load(f)

  patternDict = {}
  for j in jData:
    patternDict[j['index']] = j['pattern']

  indi_by_pattern_by_trial = {}
  comb_by_pattern_by_trial = {}

  for pattern in PATTERNS:
    indi_by_pattern_by_trial[pattern] = {}
    comb_by_pattern_by_trial[pattern] = {}

  for trial_name, seeds in seeds_by_trial.items():
    indi = set()
    comb = set()
    indi_by_pattern = {}
    comb_by_pattern = {}
    for pattern in PATTERNS:
      indi_by_pattern[pattern] = set()
      comb_by_pattern[pattern] = set()

    for seed in seeds:
      for crashset in seed['min_crashsets']:
        for index in crashset:
          if len(crashset) == 1:
            indi.add(index)
            indi_by_pattern[patternDict[index]].add(index)
          comb.add(index)
          comb_by_pattern[patternDict[index]].add(index)

    indi_by_trial[trial_name] = indi
    comb_by_trial[trial_name] = comb

    for pattern in PATTERNS:
      indi_by_pattern_by_trial[pattern][trial_name] = indi_by_pattern[pattern]
      comb_by_pattern_by_trial[pattern][trial_name] = comb_by_pattern[pattern]

  return indi_by_trial, comb_by_trial, indi_by_pattern_by_trial, comb_by_pattern_by_trial

def count_crashes(out_dir, fuzzers, programs):
  tables = {}
  for fuzzer in fuzzers:
    tables[fuzzer] = PrettyTable()
    tables[fuzzer].field_names = [fuzzer, 'indi', 'all']

  metaTable = PrettyTable()
  metaTable.field_names = ['MetaFuzzer', 'indi', 'all']

  for program in programs:
    meta_indi = set()
    meta_comb = set()
    meta_indi_by_pattern = {}
    meta_comb_by_pattern = {}

    for pattern in PATTERNS:
      meta_indi_by_pattern[pattern] = set()
      meta_comb_by_pattern[pattern] = set()
  

    for fuzzer in fuzzers:
      prog_out_dir = os.path.join(out_dir, program)
      target_out_dir = os.path.join(prog_out_dir, fuzzer)
      indi_by_trial, comb_by_trial, indi_by_pattern_by_trial, comb_by_pattern_by_trial = count_crashes_by_trial(prog_out_dir, target_out_dir)

      med_indi = statistics.median([len(i) for i in indi_by_trial.values()])
      med_comb = statistics.median([len(i) for i in comb_by_trial.values()])

      indi_pattern_str = ''
      comb_pattern_str = ''
      for pattern in PATTERNS:
        med_indi_pattern = statistics.median([len(i) for i in indi_by_pattern_by_trial[pattern].values()])
        med_comb_pattern = statistics.median([len(i) for i in comb_by_pattern_by_trial[pattern].values()])
        indi_pattern_str += ' '
        indi_pattern_str += str(med_indi_pattern)
        comb_pattern_str += ' '
        comb_pattern_str += str(med_comb_pattern)

        meta_indi_by_pattern[pattern].update(*indi_by_pattern_by_trial[pattern].values())
        meta_comb_by_pattern[pattern].update(*comb_by_pattern_by_trial[pattern].values())

      tables[fuzzer].add_row([program, f'{med_indi} ({indi_pattern_str.lstrip()})', f'{med_comb} ({comb_pattern_str.lstrip()})'])


      meta_indi.update(set(itertools.chain(*indi_by_trial.values())))
      meta_comb.update(set(itertools.chain(*comb_by_trial.values())))


    indi_pattern_str = ''
    comb_pattern_str = ''
    for pattern in PATTERNS:
      indi_pattern_str += ' '
      indi_pattern_str += str(len(meta_indi_by_pattern[pattern]))
      comb_pattern_str += ' '
      comb_pattern_str += str(len(meta_comb_by_pattern[pattern]))

    metaTable.add_row([program, f'{len(meta_indi)} ({indi_pattern_str.lstrip()})', f'{len(meta_comb)} ({comb_pattern_str.lstrip()})'])
 
  for fuzzer in fuzzers:
    print(tables[fuzzer])

  print(metaTable)










