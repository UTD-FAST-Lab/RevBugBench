import configparser
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

    def benchmark_triage_bin_dir(self, benchmark: str) -> str:
        return join(self.__work_dir, 'triage_binaries', benchmark)

    def benchmark_triage_binary(self, benchmark: str) -> str:
        return join(self.benchmark_triage_bin_dir(benchmark), self.__fuzz_targets[benchmark])

    def inst_dir(self) -> str:
        return join(self.__work_dir, 'inst')

    def prog_inst_dir(self, program: str) -> str:
        return join(self.inst_dir(), self.__fuzzer, program)

    def inst_stats(self, program: str, schedule: str) -> str:
        return join(self.prog_inst_dir(program), f'stats_{schedule}.json')

    def seeds_dir(self) -> str:
        return join(self.__work_dir, 'seeds')

    def prog_seeds_dir(self, program: str) -> str:
        return join(self.seeds_dir(), self.__fuzzer, program)

    def raw_seeds(self, program: str) -> str:
        return join(self.prog_seeds_dir(program), 'raw_seeds.json')

    def trial_profraw_dir(self, program: str, schedule: str, trial_name: str) -> str:
        return join(self.__work_dir, 'raw_files', self.__fuzzer, program, schedule, trial_name)

    def profraw_file(self, program: str, schedule: str, trial_name: str, seed_id: int) -> str:
        return join(self.trial_profraw_dir(program, schedule, trial_name), f'{seed_id}.profraw')

    def trial_prof_dir(self, program: str, schedule: str, trial_name: str) -> str:
        return join(self.__work_dir, 'prof_files', self.__fuzzer, program, schedule, trial_name)

    def prof_file(self, program: str, schedule: str, trial_name: str, file_name: str) -> str:
        return join(self.trial_prof_dir(program, schedule, trial_name), f'{file_name}.prof')

    def out_stats(self, program):
        return join(self.__out_dir, f'{self.__fuzzer}_{program}_stats.csv')
