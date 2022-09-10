import logging
import os

import common.utils
import prepare.utils


# Returns a list of benchmrak-experiment pair.
# Throws error when a benchmark is not mapped to exactly one experiment.
# Throws error when all fuzzers on a benchamrk are mapped to exactly one experiment.

def benchmark_exp_pairs(benchmarks: list[str], fuzzers: list[str],
                        exp_names: list[str], fuzzbench_exp_dir: str) -> list[(str, str, str)]:
    common.utils.check_path_exist(fuzzbench_exp_dir)
    # Stores experiment names for benchmark-fuzzer pairs.
    exp_map = {(b, f): [] for b in benchmarks for f in fuzzers}
    for e in exp_names:
        for b in benchmarks:
            for f in fuzzers:
                data_dir = prepare.utils.fuzzbench_data_dir(b, f, e, fuzzbench_exp_dir)
                if os.path.exists(data_dir):
                    exp_map[(b, f)].append(e)
    ret = []
    # Make sure each benchmark-fuzzer pair only appears in one experiment.
    for b in benchmarks:
        benchmark_exp_set = set()
        for f in fuzzers:
            exps = exp_map[(b, f)]
            if len(exps) == 0:
                logging.error(f'benchmark-fuzzer pair {b}-{f} does not appear in any experiment')
                exit(1)
            if len(exps) > 1:
                logging.error(f'benchmark-fuzzer pair {b}-{f} appears in multiple experiments: {exps}')
                exit(1)
            benchmark_exp_set.add(exps[0])
            ret.append((b, f, exps[0]))
        # Make sure all fuzzers on a benchmark only appear in one experiment.
        if len(benchmark_exp_set) != 1:
            logging.error(f'fuzzers {fuzzers} on benchmark {b} '
                          f'appear in multiple experiments: {list(benchmark_exp_set)}')
            exit(1)
    return ret
