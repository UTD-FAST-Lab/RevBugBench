import logging
import os
import pathlib
import re
import tarfile

import common.utils
import prepare.utils
from prepare.precheck import benchmark_exp_pairs


def run_prepare(benchmarks: list[str], fuzzers: list[str],
                exp_names: list[str], fuzzbench_exp_dir: str, work_dir: str) -> None:
    exp_data = benchmark_exp_pairs(benchmarks, fuzzers, exp_names, fuzzbench_exp_dir)
    has_cov_bin = {b: False for b in benchmarks}
    for benchmark, fuzzer, exp_name in exp_data:
        if not has_cov_bin[benchmark]:
            extract_coverage_binary(benchmark, exp_name, work_dir, fuzzbench_exp_dir)
            has_cov_bin[benchmark] = True
        extract_fuzzing_result(benchmark, fuzzer, exp_name, work_dir, fuzzbench_exp_dir)


def extract_coverage_binary(benchmark: str, exp_name: str, work_dir: str, fuzzbench_exp_dir: str) -> None:
    common.utils.mkdir_if_not_exist(common.utils.cov_bin_root(work_dir))
    cov_bin_dir = common.utils.cov_bin_dir(benchmark, work_dir)
    common.utils.remove_before_mkdir(cov_bin_dir)
    # Where the coverage binary compressed file is stored by FuzzBench.
    fuzzbench_cov_tar = os.path.join(fuzzbench_exp_dir, exp_name, 'coverage-binaries',
                                     f'coverage-build-{benchmark}.tar.gz')
    # Only untars the coverage binary.
    with tarfile.open(fuzzbench_cov_tar) as tar:
        tar.extractall(path=cov_bin_dir,
                       members=[x for x in tar.getmembers() if x.name == common.utils.cov_bin_name(benchmark)])


def extract_fuzzing_result(benchmark: str, fuzzer: str, exp_name: str, work_dir: str, fuzzbench_exp_dir: str) -> None:
    common.utils.mkdir_if_not_exist(common.utils.data_root(work_dir))
    # Stores extracted fuzzing results for each trial.
    data_dir = common.utils.data_dir(benchmark, fuzzer, work_dir)
    common.utils.remove_before_mkdir(data_dir)
    fuzzbench_data_dir = prepare.utils.fuzzbench_data_dir(benchmark, fuzzer, exp_name, fuzzbench_exp_dir)
    max_snap_id = 0
    last_gz_file = None
    for trial_name in os.listdir(fuzzbench_data_dir):
        fuzzbench_corpus_dir = os.path.join(fuzzbench_data_dir, trial_name, 'corpus')
        for file_name in os.listdir(fuzzbench_corpus_dir):
            match = re.search(r'corpus-archive-(\d+).tar.gz', file_name)
            assert match
            snap_id = int(match.group(1))
            if snap_id > max_snap_id:
                max_snap_id = snap_id
                last_gz_file = file_name
        assert max_snap_id
        logging.info(f'{fuzzbench_corpus_dir}: Latest snapshot number is {max_snap_id}')

        # Stores fuzzing results of a trial in data_dir.
        working_trial_dir = os.path.join(data_dir, trial_name)
        with tarfile.open(os.path.join(fuzzbench_corpus_dir, last_gz_file)) as tar:
            tar.extractall(path=working_trial_dir, members=corpus_members(tar))


# Only extracts files in `corpus/` and removes `corpus/` from path.
def corpus_members(tf: tarfile.TarFile):
    for member in tf.getmembers():
        if member.path.startswith('corpus/'):
            # len("corpus/") is 7
            member.path = member.path[7:]
            yield member




