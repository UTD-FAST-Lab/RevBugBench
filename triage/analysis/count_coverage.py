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
  reach_by_trial = {}
  trigger_by_trial = {}

  with open(os.path.join(target_out_dir, 'crash_seeds.pickle'), 'rb') as f:
    crash_seeds_by_trial = pickle.load(f)
  with open(os.path.join(target_out_dir, 'queue_seeds.pickle'), 'rb') as f:
    queue_seeds_by_trial = pickle.load(f)

  seeds_by_trial = {trial_name: [] for trial_name in crash_seeds_by_trial}
  for trial_name in seeds_by_trial:
    seeds_by_trial[trial_name] = crash_seeds_by_trial[trial_name] + queue_seeds_by_trial[trial_name]

  with open(os.path.join(prog_out_dir, 'dda.json'), 'r') as f:
    jData = json.load(f)

  patternDict = {}
  for j in jData:
    patternDict[j['index']] = j['pattern']

  reach_by_pattern_by_trial = {}
  trigger_by_pattern_by_trial = {}

  for pattern in PATTERNS:
    reach_by_pattern_by_trial[pattern] = {}
    trigger_by_pattern_by_trial[pattern] = {}

  for trial_name, seeds in seeds_by_trial.items():
    reach = set()
    trigger = set()
    reach_by_pattern = {}
    trigger_by_pattern = {}
    for pattern in PATTERNS:
      reach_by_pattern[pattern] = set()
      trigger_by_pattern[pattern] = set()

    for seed in seeds:
      for r_index in seed['reach']:
        reach.add(r_index)
        reach_by_pattern[patternDict[r_index]].add(r_index)

      for t_index in seed['trigger']:
        reach.add(t_index)
        reach_by_pattern[patternDict[t_index]].add(t_index)
        trigger.add(t_index)
        trigger_by_pattern[patternDict[t_index]].add(t_index)

    reach_by_trial[trial_name] = reach
    trigger_by_trial[trial_name] = trigger

    for pattern in PATTERNS:
      reach_by_pattern_by_trial[pattern][trial_name] = reach_by_pattern[pattern]
      trigger_by_pattern_by_trial[pattern][trial_name] = trigger_by_pattern[pattern]

  return reach_by_trial, trigger_by_trial, reach_by_pattern_by_trial, trigger_by_pattern_by_trial

def count_coverage(out_dir, fuzzers, programs):
  tables = {}
  for fuzzer in fuzzers:
    tables[fuzzer] = PrettyTable()
    tables[fuzzer].field_names = [fuzzer, 'reach', 'trigger']

  metaTable = PrettyTable()
  metaTable.field_names = ['MetaFuzzer', 'reach', 'trigger']

  for program in programs:
    meta_reach = set()
    meta_trigger = set()
    meta_reach_by_pattern = {}
    meta_trigger_by_pattern = {}

    for pattern in PATTERNS:
      meta_reach_by_pattern[pattern] = set()
      meta_trigger_by_pattern[pattern] = set()
  

    for fuzzer in fuzzers:
      prog_out_dir = os.path.join(out_dir, program)
      target_out_dir = os.path.join(prog_out_dir, fuzzer)
      reach_by_trial, trigger_by_trial, reach_by_pattern_by_trial, trigger_by_pattern_by_trial = count_crashes_by_trial(prog_out_dir, target_out_dir)

      med_reach = statistics.median([len(i) for i in reach_by_trial.values()])
      med_trigger = statistics.median([len(i) for i in trigger_by_trial.values()])

      reach_pattern_str = ''
      trigger_pattern_str = ''
      for pattern in PATTERNS:
        med_reach_pattern = statistics.median([len(i) for i in reach_by_pattern_by_trial[pattern].values()])
        med_trigger_pattern = statistics.median([len(i) for i in trigger_by_pattern_by_trial[pattern].values()])
        reach_pattern_str += ' '
        reach_pattern_str += str(med_reach_pattern)
        trigger_pattern_str += ' '
        trigger_pattern_str += str(med_trigger_pattern)

        meta_reach_by_pattern[pattern].update(*reach_by_pattern_by_trial[pattern].values())
        meta_trigger_by_pattern[pattern].update(*trigger_by_pattern_by_trial[pattern].values())

      tables[fuzzer].add_row([program, f'{med_reach} ({reach_pattern_str.lstrip()})', f'{med_trigger} ({trigger_pattern_str.lstrip()})'])


      meta_reach.update(set(itertools.chain(*reach_by_trial.values())))
      meta_trigger.update(set(itertools.chain(*trigger_by_trial.values())))


    reach_pattern_str = ''
    trigger_pattern_str = ''
    for pattern in PATTERNS:
      reach_pattern_str += ' '
      reach_pattern_str += str(len(meta_reach_by_pattern[pattern]))
      trigger_pattern_str += ' '
      trigger_pattern_str += str(len(meta_trigger_by_pattern[pattern]))

    metaTable.add_row([program, f'{len(meta_reach)} ({reach_pattern_str.lstrip()})', f'{len(meta_trigger)} ({trigger_pattern_str.lstrip()})'])
 
  for fuzzer in fuzzers:
    print(tables[fuzzer])
  print(metaTable)










