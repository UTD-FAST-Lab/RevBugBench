import os
import shutil
import logging
import random
from pathlib import Path

from utils.common import CORPUS_QUEUE_STORE, CORPUS_CRASH_STORE

def get_seed_info(trial_dirs, program, fuzzer, seed_type):
  logging.info('extracting seed info')
  seeds_by_trial = {}
  has_time = fuzzer == 'aflplusplus'
  has_id = fuzzer != 'libfuzzer' and fuzzer != 'eclipser'

  corpus_store = CORPUS_CRASH_STORE if seed_type == 'crash' else CORPUS_QUEUE_STORE

  for trial_name, trial_dir in trial_dirs.items():
    queue_dirs = corpus_store[fuzzer]
    init_time = None

    if len(queue_dirs) == 1:
      queue_dir = os.path.join(trial_dir, queue_dirs[0])
    else:
      queue_dir = os.path.join(trial_dir, f'combined_{seed_type}')
      if os.path.exists(queue_dir):
        shutil.rmtree(queue_dir)
      os.mkdir(queue_dir)
      for qd in queue_dirs:
        qd_path = os.path.join(trial_dir, qd)
        if os.path.exists(qd_path):
          for f in os.listdir(qd_path):
            source_path = os.path.join(qd_path, f)
            if os.path.isfile(source_path):
              shutil.copy(source_path, queue_dir)

    seeds = []
    if not os.path.exists(queue_dir):
      seeds_by_trial[trial_name] = []
      continue
    
    for f in os.listdir(queue_dir):
      if f == 'README.txt':
        continue
      if fuzzer == 'libfuzzer' and seed_type == 'crash' and not f.startswith('oom') and not f.startswith('crash'):
        continue

      file_path = os.path.join(queue_dir, f)

      if os.path.isfile(file_path):
        seed = {}
        seed['path'] = file_path
        seed['type'] = seed_type
        seed['program'] = program
        seed['fuzzer'] = fuzzer

        if has_time:
          file_name_split = f.split(',')
          for elem in file_name_split:
            elem_split = elem.split(':')
            if elem_split[0] == 'time':
              seed['time'] = format(int(elem_split[1]) / 100, '.2f')
              break
        else:
          seed['time'] = os.path.getmtime(file_path) / 100

        if has_id:
          file_name_split = f.split(',')
          for elem in file_name_split:
            elem_split = elem.split(':')
            if elem_split[0] == 'id':
              seed['id'] = int(elem_split[1])
              break
        
        seeds.append(seed)
    
    if not has_id or not has_time:
      seeds.sort(key=lambda x: x['time'])
    if not has_id:
      for i in range(len(seeds)):
        seeds[i]['id'] = i

    if not has_time:
      init_time = seeds[0]['time']
      for seed in seeds:
        seed['time'] = format(seed['time'] - init_time, '.2f')

    for seed in seeds:
      if 'id' not in seed or 'time' not in seed:
        logging.info(seed)
        a = seed['id'] + seed['time']
        

    if seed_type == 'crash' and len(seeds) > 664:
      seeds_for_combined = random.sample(seeds, 664)
    else:
      seeds_for_combined = seeds
    for seed in seeds_for_combined:
      seed['run_combined'] = True
#    if seed_type == 'crash':
#      for seed in seeds:
#        seed['run_combined'] = True

    seeds_by_trial[trial_name] = seeds

  return seeds_by_trial
