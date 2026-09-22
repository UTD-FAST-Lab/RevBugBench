import logging
import json
import multiprocessing
import os
import subprocess
import tarfile

import common.paths
import common.utils
from common.confighelper import ConfigHelper
from triage.get_seeds import get_seeds
from triage.common import sanitizer
from triage.common.utils import RSS_LIMIT_MB, UNIT_TIMEOUT

PROFILE_MERGE_CHUNK_SIZE = 500


def retrieve_coverage_binaries(helper: ConfigHelper) -> None:
    for benchmark in helper.benchmarks():
        experiment = _coverage_experiment(benchmark, helper)
        archive_path = os.path.join(helper.raw_data_dir(), experiment,
                                    'coverage-binaries',
                                    f'coverage-build-{benchmark}.tar.gz')
        common.paths.error_if_not_exist(archive_path,
                                        f'coverage binary archive for {benchmark}')

        benchmark_dir = common.utils.cov_bin_dir(benchmark, helper.work_dir())
        common.paths.rm_before_mkdir(benchmark_dir)
        with tarfile.open(archive_path, 'r:gz') as archive:
            archive.extractall(benchmark_dir)

        binary_path = os.path.join(benchmark_dir, helper.fuzz_target(benchmark))
        common.paths.error_if_not_exist(binary_path,
                                        f'coverage binary for {benchmark}')
        logging.info('retrieved coverage binary for %s from experiment %s',
                     benchmark, experiment)


def _coverage_experiment(benchmark: str, helper: ConfigHelper) -> str:
    experiments = []
    for experiment in helper.exps():
        archive_path = os.path.join(helper.raw_data_dir(), experiment,
                                    'coverage-binaries',
                                    f'coverage-build-{benchmark}.tar.gz')
        if os.path.exists(archive_path):
            experiments.append(experiment)
    if len(experiments) != 1:
        raise RuntimeError(f'coverage binary for {benchmark} appears in '
                           f'{len(experiments)} configured experiments: {experiments}')
    return experiments[0]


def calculate_edge_coverage(helper: ConfigHelper) -> None:
    retrieve_coverage_binaries(helper)
    for seed_type in ('queue', 'crash'):
        seeds = get_seeds(seed_type, helper)
        logging.info('edge coverage on %s %s entries with %s parallel jobs',
                     len(seeds), seed_type, helper.cores())
        with multiprocessing.Pool(processes=helper.cores()) as pool:
            profile_paths = pool.starmap(_run_seed,
                                         [(seed, helper, index)
                                          for index, seed in enumerate(seeds)])
        _merge_profiles(profile_paths, seed_type, helper)


def generate_edge_coverage_reports(helper: ConfigHelper) -> None:
    root = os.path.join(helper.work_dir(), 'edge-coverage')
    if not os.path.isdir(root):
        raise RuntimeError(f'edge coverage directory does not exist: {root}')
    report_count = 0
    for benchmark in helper.benchmarks():
        for fuzzer in helper.fuzzers():
            benchmark_fuzzer_dir = os.path.join(root, benchmark, fuzzer)
            if not os.path.isdir(benchmark_fuzzer_dir):
                logging.warning('edge coverage directory does not exist: %s',
                                benchmark_fuzzer_dir)
                continue
            for trial in os.listdir(benchmark_fuzzer_dir):
                trial_dir = os.path.join(benchmark_fuzzer_dir, trial)
                if not os.path.isdir(trial_dir):
                    continue
                queue_profile = os.path.join(trial_dir, 'queue.profdata')
                crash_profile = os.path.join(trial_dir, 'crash.profdata')
                if not os.path.exists(queue_profile):
                    raise RuntimeError(f'queue profile does not exist: {queue_profile}')
                profile_paths = [queue_profile]
                if os.path.exists(crash_profile):
                    profile_paths.append(crash_profile)
                else:
                    logging.warning('crash profile does not exist: %s', crash_profile)
                merged_profile = os.path.join(trial_dir, 'coverage.profdata')
                _merge_profile_files(profile_paths, merged_profile)
                _write_json_report(benchmark, 'coverage', merged_profile, helper)
                report_count += 1
    logging.info('generated %s edge coverage JSON reports', report_count)


def _run_seed(seed: dict, helper: ConfigHelper, seed_index: int):
    output_dir = helper.edge_coverage_dir(seed['benchmark'], seed['fuzzer'], seed['trial'])
    common.paths.mkdir(output_dir)
    profile_path = os.path.join(output_dir, f'{seed["type"]}-{seed_index}.profraw')
    binary_path = os.path.join(common.utils.cov_bin_dir(seed['benchmark'], helper.work_dir()),
                               helper.fuzz_target(seed['benchmark']))
    environment = os.environ.copy()
    sanitizer.set_sanitizer_options(environment)
    environment['FIXREVERTER'] = 'off '
    environment['LLVM_PROFILE_FILE'] = profile_path
    command = [binary_path,
               f'-timeout={UNIT_TIMEOUT}',
               f'-rss_limit_mb={RSS_LIMIT_MB}',
               seed['path']]
    try:
        result = subprocess.run(command, env=environment, cwd=output_dir,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=UNIT_TIMEOUT + 5, check=False)
    except subprocess.TimeoutExpired:
        logging.warning('edge coverage timed out for %s', seed['path'])
        return None
    if result.returncode != 0:
        logging.warning('coverage binary returned %s for %s', result.returncode, seed['path'])
    return profile_path if os.path.exists(profile_path) else None


def _merge_profiles(profile_paths: list, seed_type: str, helper: ConfigHelper) -> None:
    grouped = {}
    for profile_path in profile_paths:
        if profile_path is None:
            continue
        key = tuple(profile_path.split(os.sep)[-4:-1])
        grouped.setdefault(key, []).append(profile_path)

    for (benchmark, fuzzer, trial), paths in grouped.items():
        output_dir = helper.edge_coverage_dir(benchmark, fuzzer, trial)
        output_path = os.path.join(output_dir, f'{seed_type}.profdata')
        merged_paths = []
        for start in range(0, len(paths), PROFILE_MERGE_CHUNK_SIZE):
            chunk = paths[start:start + PROFILE_MERGE_CHUNK_SIZE]
            chunk_output = os.path.join(output_dir, f'.{seed_type}-merge-{start}.profdata')
            _merge_profile_files(chunk, chunk_output)
            merged_paths.append(chunk_output)
        _merge_profile_files(merged_paths, output_path)
        for path in paths + merged_paths:
            os.remove(path)
        _write_json_report(benchmark, seed_type, output_path, helper)
        logging.info('stored %s edge profile for %s/%s/%s', seed_type,
                     benchmark, fuzzer, trial)


def _merge_profile_files(input_paths: list, output_path: str) -> None:
    command = ['llvm-profdata', 'merge', '-sparse', '-output', output_path, *input_paths]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            check=False)
    if result.returncode != 0:
        error = result.stderr.decode('utf-8', errors='ignore').strip()
        raise RuntimeError(f'llvm-profdata merge failed: {error}')


def _write_json_report(benchmark: str, seed_type: str, profile_path: str,
                       helper: ConfigHelper) -> None:
    binary_path = os.path.join(common.utils.cov_bin_dir(benchmark, helper.work_dir()),
                               helper.fuzz_target(benchmark))
    command = ['llvm-cov', 'export', f'-instr-profile={profile_path}', binary_path]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            check=False)
    if result.returncode != 0:
        error = result.stderr.decode('utf-8', errors='ignore').strip()
        raise RuntimeError(f'llvm-cov export failed for {profile_path}: {error}')
    try:
        report = json.loads(result.stdout.decode('utf-8'))
    except json.JSONDecodeError as error:
        raise RuntimeError(f'llvm-cov returned invalid JSON for {profile_path}') from error

    report_path = os.path.splitext(profile_path)[0] + '.json'
    with open(report_path, 'w') as report_file:
        json.dump(report, report_file, indent=2)
    logging.info('stored %s edge coverage report at %s', seed_type, report_path)