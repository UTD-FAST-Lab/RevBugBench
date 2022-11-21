import configparser
import os
from pathlib import Path

import yaml

from os.path import join
from common import paths


class ConfigHelper:
    def __init__(self, config_path: str):
        config = configparser.ConfigParser(allow_no_value=True)
        # Options are case sensitive.
        config.optionxform = str
        config.read(config_path)

        self.__work_dir = config.get('paths', 'workDir')
        paths.mkdir(self.__work_dir)
        self.__out_dir = config.get('paths', 'outDir')
        paths.mkdir(self.__out_dir)
        self.__fuzzbench_dir = config.get('paths', 'fuzzbenchDir')
        paths.error_if_not_exist(self.__fuzzbench_dir, 'fuzzbenchDir in config')
        self.__raw_data_dir = config.get('paths', 'fuzzbenchExpDir')
        paths.error_if_not_exist(self.__raw_data_dir, 'fuzzbenchExpDir in config')

        self.__exps = list(config['experiments'].keys())
        self.__benchmarks = list(config['benchmarks'].keys())
        self.__fuzzers = list(config['fuzzers'].keys())
        self.__cores = int(config.get('values', 'cores'))

        self.__fuzz_targets = self.__get_fuzz_targets(self.__benchmarks)

    def __get_fuzz_targets(self, benchmarks: list) -> dict:
        target_names = {}
        for benchmark in benchmarks:
            benchmark_dir = join(self.__fuzzbench_dir, 'benchmarks', benchmark)
            paths.error_if_not_exist(benchmark_dir, f'FuzzBench benchmark {benchmark}')
            target_names[benchmark] = yaml.safe_load(Path(join(benchmark_dir, 'benchmark.yaml'))
                                                     .read_text())['fuzz_target']
        return target_names

    def raw_data_dir(self) -> str:
        return self.__raw_data_dir

    def cores(self) -> int:
        return self.__cores

    def exps(self) -> list:
        return self.__exps

    def benchmarks(self) -> list:
        return self.__benchmarks

    def fuzzers(self) -> list:
        return self.__fuzzers

    def fuzz_target(self, benchmark: str) -> str:
        return self.__fuzz_targets[benchmark]

    def data_dir(self) -> str:
        return join(self.__work_dir, 'data')

    def bf_data_dir(self, benchmark: str, fuzzer: str) -> str:
        return join(self.data_dir(), benchmark, fuzzer)

    def trial_data_dir(self, benchmark: str, fuzzer: str, trial_name: str) -> str:
        return join(self.bf_data_dir(benchmark, fuzzer), trial_name)

    def trials(self, benchmark: str, fuzzer: str) -> list:
        paths.error_if_not_exist(self.bf_data_dir(benchmark, fuzzer), 'cannot extract trial names')
        return os.listdir(self.bf_data_dir(benchmark, fuzzer))

    def benchmark_triage_bin_dir(self, benchmark: str) -> str:
        return join(self.__work_dir, 'triage_binaries', benchmark)

    def benchmark_triage_binary(self, benchmark: str) -> str:
        return join(self.benchmark_triage_bin_dir(benchmark), self.__fuzz_targets[benchmark])

    def parsed_seeds_store(self, benchmark: str, fuzzer: str, trial_name: str, seed_type: str) -> str:
        store_dir = join(self.__work_dir, 'parsed_seeds', benchmark, fuzzer)
        paths.mkdir(store_dir)
        return join(store_dir, f'{trial_name}_{seed_type}.json')

    def tmp_running_dir(self, process_name: str) -> str:
        return join(self.__work_dir, 'tmp_running_dir', process_name)

    def dda_file(self, benchmark: str) -> str:
        return join(self.__work_dir, 'dda_store', benchmark, 'dda.json')
