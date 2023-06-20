import argparse
import logging
import os
import sys

from analysis.coverage_table import coverage_table
from analysis.growth_plot import growth_plot
from analysis.venn_diagram import venn_diagram
from triage.triage_seeds import triage_seeds

# Add the triage folder to PATH.
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import common.confighelper
import common.utils
from setup import setup


def parse_args():
    parser = argparse.ArgumentParser(description='Triage RevBugBench results and generate performance report.')
    parser.add_argument('-s',
                        '--setup',
                        help='Extract fuzz corpus from fuzzbench results and setup triage binary.',
                        required=False,
                        action='store_true')
    parser.add_argument('-t',
                        '--triage',
                        help='Run triage binary on the fuzzing results and triage individual and/or combined causes.',
                        required=False,
                        action='store_true')
    parser.add_argument('-r',
                        '--report',
                        help='Generate performance plots/tables/figures on out directory.',
                        required=False,
                        action='store_true')
    parser.add_argument('-c',
                        '--config',
                        help='Path to the config file, default to `config.ini`.',
                        required=False,
                        default=os.path.join(common.utils.SCRIPT_DIR, 'config.ini'))
    return parser.parse_args()


def setup_logging():
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')


def main():
    setup_logging()
    args = parse_args()

    helper = common.confighelper.ConfigHelper(args.config)

    if args.setup:
        setup.setup(helper)
    if args.triage:
        triage_seeds(helper, 'queue')
        triage_seeds(helper, 'crash')
    if args.report:
        coverage_table(helper)
        growth_plot(helper)
        venn_diagram(helper)


if __name__ == '__main__':
    exit(main())
