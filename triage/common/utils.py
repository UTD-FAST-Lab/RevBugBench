import logging
import os
import pathlib
import shutil

TRIAGE_ROOT = os.path.dirname(os.path.dirname(__file__))

Coverage_Binaries = {}


def check_path_exist(path: str) -> None:
    if not os.path.exists(path):
        logging.error(f'{path} does not exist')
        exit(1)


def mkdir_if_not_exist(path: str) -> None:
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


# Removes existing directory at `dir_path` if it exists, and makes an empty one.
def remove_before_mkdir(dir_path: str) -> None:
    if os.path.exists(dir_path):
        logging.warning(f'directory removed before make: {dir_path}')
        shutil.rmtree(dir_path)
    os.mkdir(dir_path)


# Returns the coverage binary name of a benchmark.
# Throws error if the benchmark is not hard coded in Coverage_Binaries.
def cov_bin_name(benchmark: str) -> str:
    if benchmark not in Coverage_Binaries.keys():
        logging.error(f'coverage binary name of benchmark {benchmark}'
                      f' not hard coded in common/utils.py')
    return Coverage_Binaries[benchmark]


# Root directory for coverage binary folders.
def cov_bin_root(work_dir: str) -> str:
    return os.path.join(work_dir, 'coverage-binaries')


# Stores the coverage binary for a benchmark in work_dir.
def cov_bin_dir(benchmark: str, work_dir: str) -> str:
    return os.path.join(cov_bin_root(work_dir), benchmark)


# Path to the coverage binary for a benchmark.
def cov_bin(benchmark: str, work_dir: str) -> str:
    return os.path.join(cov_bin_dir(benchmark, work_dir), cov_bin_name(benchmark))


# Root directory for extracted fuzzing results.
def data_root(work_dir: str) -> str:
    return os.path.join(work_dir, 'experiment-data')


# Stores fuzzing results for a target benchmark in work_dir.
def data_dir(benchmark: str, fuzzer: str, work_dir: str) -> str:
    return os.path.join(data_root(work_dir), f'{benchmark}_{fuzzer}')