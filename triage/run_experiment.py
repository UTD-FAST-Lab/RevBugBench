import sys
import logging
import csv
import argparse
import os
import docker
import configparser
from pathlib import Path

from setup.setup import setup_dirs, untar_raw_data, get_exp_config
from utils.common import fill_missing_time, SCRIPT_DIR, PROGRAMS, FUZZERS

from analysis.count_crashes import count_crashes
from analysis.count_coverage import count_coverage
from analysis.growth_plot import generate_growth_plot
from analysis.venn_graph import draw_venn_graph
from experiment.run_crashes import run_crashes_main
from experiment.run_coverage import run_coverage_main

def parse_args():
  parser = argparse.ArgumentParser(description='Triage scripts for RevBugBench.')
  parser.add_argument('-u',
      '--untar',
      help='Extract coverage binary and fuzz corpus from fuzzbench experimental results',
      required=False,
      action='store_true')
  parser.add_argument(
      '--crash',
      help='Run coverage binary on each crashing seed and dump crash and coverage info into pickle',
      required=False,
      action='store_true')
  parser.add_argument(
      '--coverage',
      help='Run coverage binary on each queue seed and dump coverage info into pickle',
      required=False,
      action='store_true')
  parser.add_argument('-e',
      '--experiments',
      help='The FuzzBench experiment.',
      required=True,
      nargs='+')
  parser.add_argument('-f',
      '--fuzzers',
      help='Fuzzers to run the analysis on. Default to all fuzzers',
      required=False,
      nargs='+',
      default=FUZZERS,
      choices=FUZZERS)
  parser.add_argument('-p',
      '--programs',
      help='Programs to run the analysis on. Default to all targets',
      required=False,
      nargs='+',
      default=PROGRAMS,
      choices=PROGRAMS)
  parser.add_argument('-c',
      '--count',
      help='Count FixReverter coverage and/or crashes',
      required=False,
      nargs='+',
      default=[],
      choices=['crashes', 'coverage'])
  parser.add_argument('-g',
      '--growth',
      help='generate combined single cause growth graph',
      required=False,
      action='store_true')
  parser.add_argument('-v',
      '--venn',
      help='generate venn diagram for single causes',
      required=False,
      action='store_true')

  return parser.parse_args()


def generate_pickle(analysis, pickle_path, measure):
  script_names = {'crash': 'run_crashes', 'coverage': 'run_coverage'}
  logging.info(f'{analysis.fuzzer}-{analysis.program}: Generating {measure} pickle')
  run_script_in_docker(analysis, f'-u {script_names[measure]}.py')
  if not os.path.exists(pickle_path):
    logging.warning(f'{analysis.program}-{analysis.fuzzer}: Failed to generate {measure}.pickle')

def run_experiment_on_targets(args):
  visited = {}
  for experiment in args.experiments:
    for fuzzer in args.fuzzers:
      for program in args.programs:
        if not set_config(experiment, fuzzer, program, log=False):
          logging.error(f"{fuzzer}-{program} Fail to set config file")
          sys.exit(1)

        fuzzer_program_pair = (fuzzer, program)
        # get target config from file as it's also used in docker
        analysis = get_exp_config()
        
        if fuzzer_program_pair in visited.keys():
          logging.error(f"{fuzzer}-{program} exists in multiple experiments")
          sys.exit(1)

        if os.path.exists(analysis.exp_data_dir):
          visited[fuzzer_program_pair] = experiment

  for fuzzer in args.fuzzers:
    for program in args.programs:
      fuzzer_program_pair = (fuzzer, program)
      if fuzzer_program_pair not in visited.keys():
        logging.error(f"{fuzzer}-{program} does not exist in any experiment")
        sys.exit(1)

  for pair, experiment in visited.items():
    fuzzer, program = pair
    set_config(experiment, fuzzer, program)
    analysis = get_exp_config()
    crash_path = os.path.join(analysis.target_out, 'crash_seeds.pickle')
    queue_path = os.path.join(analysis.target_out, 'queue_seeds.pickle')

    if args.untar:
      setup_dirs(analysis.work_dir)
      untar_raw_data(analysis.prog_dir, analysis.work_dir, analysis.exp_cov_tar, analysis.exp_data_dir, analysis.trial_names)

    if args.crash:
      run_crashes_main(analysis)
      #generate_pickle(analysis, crash_path, 'crash')

    if args.coverage:
      run_coverage_main(analysis)
      #generate_pickle(analysis, queue_path, 'coverage')

  if args.count:
    if 'coverage' in args.count:
      logging.info(f"Loggings to be added")
      count_coverage(analysis.out_dir, args.fuzzers, args.programs)
    if 'crashes' in args.count:
      logging.info(f"Loggings to be added")
      count_crashes(analysis.out_dir, args.fuzzers, args.programs)

  if args.growth:
    generate_growth_plot(analysis.out_dir, args.fuzzers, args.programs)
    
  if args.venn:
    draw_venn_graph(analysis.out_dir, args.fuzzers, args.programs)


def set_config(experiment, fuzzer, program, log=True):
  if log:
    logging.info(f'{experiment}-{fuzzer}-{program}: Setting target config file')
  ini_path = os.path.join(SCRIPT_DIR, 'target.ini')
  if os.path.exists(ini_path):
    os.remove(ini_path)

  config = configparser.ConfigParser()
  config.add_section('names')
  config.set('names', 'experiment', experiment)
  config.set('names', 'fuzzer', fuzzer)
  config.set('names', 'program', program)


  with open(ini_path, 'w+') as f:
    config.write(f)

  if os.path.exists(ini_path):
    return True
  logging.warning(f'{program}-{fuzzer}: Failed to create config file')
  return False


def run_script_in_docker(analysis, command):
    prog_parent = str(Path(analysis.prog_dir).parent.absolute())

    client = docker.from_env()
    client.containers.run('fixreverter/post-process',
                            remove=True,
                            entrypoint='python3',
                            working_dir='/fuzzer-internal-study/experiment',
                            command=command,
                            volumes={SCRIPT_DIR: {'bind': '/fuzzer-internal-study', 'mode': 'rw'},
                                     prog_parent: {'bind': prog_parent, 'mode': 'rw'},
                                     analysis.exp_data_dir: {'bind': analysis.exp_data_dir, 'mode': 'rw'},
                                     analysis.target_out: {'bind': analysis.target_out, 'mode': 'rw'}},
                            environment=['PYTHONUNBUFFERED=1'])


def main():
  logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
  args = parse_args()
  run_experiment_on_targets(args)

if __name__ == '__main__':
  sys.exit(main())
