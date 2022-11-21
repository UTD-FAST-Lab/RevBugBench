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
    max_snap_id = 0
    last_gz_file = None
    for trial_name in os.listdir(fuzzbench_data_dir):
        fuzzbench_corpus_dir = os.path.join(fuzzbench_data_dir, trial_name, 'corpus')
        for file_name in os.listdir(fuzzbench_corpus_dir):
            match = re.search(r'corpus-archive-(\d+).tar.gz', file_name)
            assert match, f'corpus archive file not found in {fuzzbench_corpus_dir}'
            snap_id = int(match.group(1))
            if snap_id > max_snap_id:
                max_snap_id = snap_id
                last_gz_file = file_name
        logging.info(f'{fuzzbench_corpus_dir}: Latest snapshot number is {max_snap_id}')

        # Stores fuzzing results of a trial in data_dir.
        with tarfile.open(os.path.join(fuzzbench_corpus_dir, last_gz_file)) as tar:
            tar.extractall(path=helper.trial_data_dir(benchmark, fuzzer, trial_name), members=corpus_members(tar))


# Only extracts files in `corpus/` and removes `corpus/` from path.
def corpus_members(tf: tarfile.TarFile):
    for member in tf.getmembers():
        if member.path.startswith('corpus/'):
            # len("corpus/") is 7
            member.path = member.path[7:]
            yield member
