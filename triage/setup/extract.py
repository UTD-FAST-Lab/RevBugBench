import logging
import os
import re
import tarfile

import common.utils
import common.paths
import setup.utils
from common.confighelper import ConfigHelper


def extract_fuzzing_result(benchmark: str, fuzzer: str, exp_name: str, helper: ConfigHelper) -> None:
    # Stores extracted fuzzing results for each trial.
    bf_data_dir = helper.bf_data_dir(benchmark, fuzzer)
    common.paths.rm_before_mkdir(bf_data_dir)
    fuzzbench_data_dir = setup.utils.fuzzbench_data_dir(helper.raw_data_dir(), exp_name, benchmark, fuzzer)
    for trial_name in os.listdir(fuzzbench_data_dir):
        fuzzbench_corpus_dir = os.path.join(fuzzbench_data_dir, trial_name, 'corpus')
        archives = []
        for file_name in os.listdir(fuzzbench_corpus_dir):
            match = re.search(r'corpus-archive-(\d+).tar.gz', file_name)
            assert match, f'corpus archive file not found in {fuzzbench_corpus_dir}'
            archives.append((int(match.group(1)), file_name))
        archives.sort()
        logging.info(f'{fuzzbench_corpus_dir}: Extracting {len(archives)} corpus archives')

        # Stores fuzzing results of a trial in data_dir.
        trial_data_dir = helper.trial_data_dir(benchmark, fuzzer, trial_name)
        common.paths.mkdir(trial_data_dir)
        for _, file_name in archives:
            with tarfile.open(os.path.join(fuzzbench_corpus_dir, file_name)) as tar:
                tar.extractall(path=trial_data_dir)
