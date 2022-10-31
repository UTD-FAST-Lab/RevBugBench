import logging
import os
import pathlib
import shutil

SCRIPT_DIR = os.path.dirname(os.path.dirname(__file__))

CORPUS_QUEUE_STORE = {'aflplusplus': ['corpus/default/queue'],
                      'afl': ['corpus/queue'],
                      'libfuzzer': ['corpus/corpus'],
                      'eclipser': ['corpus/afl-worker/queue', 'corpus/eclipser_output/queue'],
                      'fairfuzz': ['corpus/queue']}
CORPUS_CRASH_STORE = {'aflplusplus': ['corpus/default/crashes'],
                      'afl': ['corpus/crashes'],
                      'libfuzzer': ['corpus/crashes'],
                      'eclipser': ['corpus/afl-worker/crashes', 'corpus/eclipser_output/crashes'],
                      'fairfuzz': ['corpus/crashes']}


def fuzzer_queue_store(fuzzer: str) -> list:
    return CORPUS_QUEUE_STORE[fuzzer]


def fuzzer_crash_store(fuzzer: str) -> list:
    return CORPUS_CRASH_STORE[fuzzer]




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
