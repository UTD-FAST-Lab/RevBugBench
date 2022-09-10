import argparse
import configparser
import logging
import os
import sys

# Add the triage folder to PATH.
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from common import utils
from prepare import run_prepare


def parse_args():
    parser = argparse.ArgumentParser(description='Runs coverage experiments on ConfigFuzz empirical study and '
                                                 'summarize results.')
    parser.add_argument('-p',
                        '--prepare',
                        help='Extract coverage binary and fuzz corpus from fuzzbench results.',
                        required=False,
                        action='store_true')
    parser.add_argument('-r',
                        '--run',
                        help='Run coverage binary on the corpus of each trial and generate profraw files.',
                        required=False,
                        action='store_true')
    parser.add_argument('-a',
                        '--analyze',
                        help='Analyze coverage results and write summary to outDir.',
                        required=False,
                        action='store_true')
    parser.add_argument('-c',
                        '--config',
                        help='Path to the config file, default to `config.ini`.',
                        required=False,
                        default=os.path.join(utils.TRIAGE_ROOT, 'config.ini'))
    return parser.parse_args()


def parse_config(config_path):
    config = configparser.ConfigParser(allow_no_value=True)
    # Options are case sensitive.
    config.optionxform = str
    config.read(config_path)
    return config


def setup_logging():
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')


def main():
    setup_logging()
    args = parse_args()
    config = parse_config(args.config)

    benchmarks = list(config['benchmarks'].keys())
    options = list(config['options'].keys())
    exps = list(config['experiments'].keys())
    fuzzers = list(config['fuzzers'].keys())
    work_dir = config.get('paths', 'workDir')
    out_dir = config.get('paths', 'outDir')
    fuzzbench_exp_dir = config.get('paths', 'fuzzbenchExpDir')
    cores = int(config.get('values', 'cores'))

    # Make sure the two directories exist.
    utils.mkdir_if_not_exist(work_dir)
    utils.mkdir_if_not_exist(out_dir)

    if args.prepare:
        run_prepare.run_prepare(benchmarks, fuzzers,
                                exps, fuzzbench_exp_dir, work_dir)
    if args.run:
        # Unimplemented
        return
    if args.analyze:
        # Unimplemented
        return


if __name__ == '__main__':
    exit(main())
