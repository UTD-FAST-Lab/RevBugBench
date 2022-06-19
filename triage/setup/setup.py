import os
import sys
import shutil
import tarfile
import configparser
import logging
from pathlib import Path

from utils.common import SCRIPT_DIR, COV_BINS


def parse_config(config_name):
  config = configparser.ConfigParser()
  config.read(os.path.join(SCRIPT_DIR, os.path.join(SCRIPT_DIR, f'{config_name}.ini')))
  return config


def setup_dirs(work_dir):
  if os.path.exists(work_dir):
    shutil.rmtree(work_dir)
  os.mkdir(work_dir)


def untar_raw_data(prog_dir, work_dir, cov_tar, exp_data_dir, trial_names):
  cov_dir = os.path.join(prog_dir, 'coverage')

  if os.path.exists(cov_dir):
    logging.info(f'{cov_dir} already exists, skip extracting coverage folder')
  else:
    os.mkdir(cov_dir)
    cov_tar = tarfile.open(cov_tar)
    cov_tar.extractall(path=cov_dir)
    cov_tar.close()

  for trial_name in trial_names:
    corpus_dir = os.path.join(exp_data_dir, trial_name, 'corpus')
    max_snap = -1
    
    for file_name in os.listdir(corpus_dir):
      file_name_split = file_name.split('.')[0].split('-')
      snap = int(file_name_split[2])
      if snap > max_snap:
        max_snap = snap
        lastest_file = file_name
    
    if lastest_file != 'corpus-archive-0097.tar.gz':
      logging.warning(f"{corpus_dir}: Lastest snapshot number is not 97: {lastest_file}")

    tar = tarfile.open(os.path.join(corpus_dir, lastest_file))
    trial_dir = os.path.join(work_dir, trial_name)
    tar.extractall(path=trial_dir)
    tar.close()


def get_trial_names(exp_data_dir):
  return os.listdir(exp_data_dir)


def get_trial_dirs(work_dir, trial_names):
  trial_dirs = {}
  for trial_name in trial_names:
    trial_dir = os.path.join(work_dir, trial_name)
    trial_dirs[trial_name] = trial_dir
  return trial_dirs


def get_exp_config():
  return ExpConfig(parse_config('optfuzz'), parse_config('target'))


class ExpConfig:
  def __init__(self, optfuzz_config, target_config):
    self.fuzzbench_exp_dir = optfuzz_config.get('paths', 'fuzzbenchExpDir')
    self.out_dir = optfuzz_config.get('paths', 'outDir')
    if not os.path.exists(self.out_dir):
      os.mkdir(self.out_dir)

    self.cores = int(optfuzz_config.get('values', 'cores'))

    self.experiment = target_config.get('names', 'experiment')
    self.fuzzer = target_config.get('names', 'fuzzer')
    self.program = target_config.get('names', 'program')

    self.exp_data_dir = os.path.join(self.fuzzbench_exp_dir, self.experiment, 'experiment-folders', f'{self.program}-{self.fuzzer}')
    self.exp_cov_tar = os.path.join(self.fuzzbench_exp_dir, self.experiment, 'coverage-binaries', f'coverage-build-{self.program}.tar.gz')
    self.trial_names = get_trial_names(self.exp_data_dir)

    self.prog_dir = os.path.join(optfuzz_config.get('paths', 'workDir'), self.program)
    self.work_dir = os.path.join(self.prog_dir, self.fuzzer)
    Path(self.work_dir).mkdir(parents=True, exist_ok=True)

    self.cov_bin = os.path.join(self.prog_dir, 'coverage', COV_BINS[self.program])

    self.trial_dirs = get_trial_dirs(self.work_dir, self.trial_names)

    self.target_out = os.path.join(self.out_dir, self.program, self.fuzzer)
    Path(self.target_out).mkdir(parents=True, exist_ok=True)
  
    self.is_opt = self.program.endswith('_1') or self.program.endswith('_2')
    if self.is_opt:
      self.argparse_dir = optfuzz_config.get('paths', 'argParseDir')
      self.arg_parser = os.path.join(self.argparse_dir, self.program, 'argparser')
