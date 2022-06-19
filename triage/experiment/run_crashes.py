import sys
import os

import shutil
import re
import logging
import pickle
import itertools
import multiprocessing
import time
import numpy as np

from utils.common import dump_to_pickle
from utils import sanitizer, new_process
from setup.setup import get_exp_config
from experiment.get_seed_info import get_seed_info

UNIT_TIMEOUT = 1
RSS_LIMIT_MB = 2048


def parseFixReverterLog(output: list) -> set:
  lines = output.split('\n')
  reaches = set()
  triggers = set()
  for line in lines:
    if 'triggered bug index' in line:
      try:
        injectionID = int(line.split(' ')[-1])
        reaches.add(injectionID)
        triggers.add(injectionID)
      except:
        pass
    elif 'reached bug index' in line:
      try:
        injectionID = int(line.split(' ')[-1])
        reaches.add(injectionID)
      except:
        pass
  return reaches, triggers

def run_crashes(seeds_by_trial, cov_bin, work_dir, target_out_dir, cores):
  start_time = time.time()
  triage_dir = os.path.join(work_dir, 'triage')
  if os.path.exists(triage_dir):
    shutil.rmtree(triage_dir)
  os.mkdir(triage_dir)

  all_seeds = []
  for trial_name, seeds in seeds_by_trial.items():
    for seed in seeds:
      all_seeds.append((trial_name, seed))

  logging.info(f'going to triage {len(all_seeds)} seeds')
  seed_chucks = np.array_split(all_seeds, 100)

  multiprocessing.freeze_support()


  accum_count = 0
  with multiprocessing.Pool(processes=cores) as pool:
    processed_seeds_by_trial = {name: [] for name in seeds_by_trial}
    for chunck in seed_chucks:
      logging.info(f'triage has reached {accum_count/len(all_seeds)*100}% progress [{accum_count}/{len(all_seeds)}]')
      results = pool.starmap(run_crashes_worker, zip(chunck, 
                    itertools.repeat(cov_bin), itertools.repeat(triage_dir)))
      for res in results:
        processed_seeds_by_trial[res[0]].append(res[1])
      accum_count += len(chunck)
  end_time = time.time()
  with open(os.path.join(target_out_dir, 'crash_time'), 'w+') as f:
    f.write(str(end_time - start_time))

  dump_to_pickle(target_out_dir, processed_seeds_by_trial, 'crash_seeds')
  logging.info('dumped crash seeds info to pickle')

def run_crashes_worker(seed_pair, cov_bin, triage_dir):
  worker_name = multiprocessing.current_process().name
  worker_triage_dir = os.path.join(triage_dir, worker_name)
  if not os.path.exists(worker_triage_dir):
    os.mkdir(worker_triage_dir)

  trial_name, seed = seed_pair
  seed_env = os.environ.copy()
  sanitizer.set_sanitizer_options(seed_env)

  if True:  
    # first run for reach and trigger
    args = [
      cov_bin,
      f'-timeout={UNIT_TIMEOUT}',
      f'-rss_limit_mb={RSS_LIMIT_MB}',
      seed['path']
    ]

    seed_env["FIXREVERTER"] = 'off '
    cov_res = new_process.execute(args,
                                 env=seed_env,
                                 cwd=worker_triage_dir,
                                 expect_zero=False,
                                 kill_children=True,
                                 timeout=UNIT_TIMEOUT + 5)

    reaches, triggers = parseFixReverterLog(cov_res.output)

    seed['reach'] = reaches
    seed['trigger'] = triggers

    seed_env["FIXREVERTER"] = 'on '
    non_inj_res = new_process.execute(args,
                                 env=seed_env,
                                 cwd=worker_triage_dir,
                                 expect_zero=False,
                                 kill_children=True,
                                 timeout=UNIT_TIMEOUT + 5)

    # this bug is not caused by FixReverter injections
    if non_inj_res.retcode:
      seed['min_crashsets'] = []

    logging.debug(f'triage on trial {trial_name} is running {seed["path"]} with triggers{triggers}')
    min_crashsets = []
    if 'run_combined' in seed:
      comb_degree = min(len(triggers), 3)
    else:
      comb_degree = 1
    # get minimal crash sets
    for n in range(1, comb_degree+1):
      for currset in itertools.combinations(triggers, n):
        # skip if current set is superset of a crash set
        isSuper = False
        for crashset in min_crashsets:
          if set(currset).issuperset(crashset):
            isSuper = True
            break
        if isSuper:
          continue
            
        seed_env["FIXREVERTER"] = 'on ' + ' '.join([str(i) for i in currset])
        logging.debug(f'triage on trial {trial_name} is running {seed["path"]} with set{currset}')
        curr_res = new_process.execute(args,
                                 env=seed_env,
                                 cwd=worker_triage_dir,
                                 expect_zero=False,
                                 kill_children=True,
                                 timeout=UNIT_TIMEOUT + 5)
        if curr_res.retcode:
          logging.debug(f'triage on trial {trial_name} is running {seed["path"]} and get min set {currset}')
          min_crashsets.append(currset)

    seed['min_crashsets'] = min_crashsets

  return trial_name, seed

def run_crashes_main(analysis):
  seeds_by_trial = get_seed_info(analysis.trial_dirs, analysis.program, analysis.fuzzer, 'crash')
  run_crashes(seeds_by_trial, analysis.cov_bin, analysis.work_dir, analysis.target_out, analysis.cores)

def main():
  logging.basicConfig(level = logging.INFO)
  analysis = get_exp_config()

  seeds_by_trial = get_seed_info(analysis.trial_dirs, analysis.program, analysis.fuzzer, 'crash')
  run_crashes(seeds_by_trial, analysis.cov_bin, analysis.work_dir, analysis.target_out, analysis.cores)


if __name__ == '__main__':
  sys.exit(main())
