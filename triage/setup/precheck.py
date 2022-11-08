import logging
import os

import common.paths
import setup.utils
from common.confighelper import ConfigHelper


# Returns a list of benchmrak-experiment pair.
# Throws error when a benchmark is not mapped to exactly one experiment.
# Throws error when a benchmark-fuzzer pair is not mapped to exactly one experiment.

def exp_tuples(benchmarks: list, fuzzers: list, exps: list, raw_data_dir: str) -> list:
    # Stores experiment names for benchmark-fuzzer pairs.
    exp_map = {(b, f): [] for b in benchmarks for f in fuzzers}
    for e in exps:
        for b in benchmarks:
            for f in fuzzers:
                # Checks if the benchmark-fuzzer pair `(b, f)` exists in the experiment `e`.
                data_dir = setup.utils.fuzzbench_data_dir(raw_data_dir, e, b, f)
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
