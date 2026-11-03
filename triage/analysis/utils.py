import functools
import logging
import os

from common.confighelper import ConfigHelper

TYPE_KEYS = {'single_cause': 'crashes',
             'all_cause': 'crashes',
             'reach': 'reaches',
             'trigger': 'triggers'}


@functools.lru_cache(maxsize=None)
def report_trials(benchmark: str, fuzzer: str, helper: ConfigHelper) -> tuple:
    """Returns the trials that have every input the report needs, warning about each skipped trial."""
    trials = []
    for trial in helper.trials(benchmark, fuzzer):
        required = [helper.parsed_seeds_store(benchmark, fuzzer, trial, 'queue'),
                    helper.parsed_seeds_store(benchmark, fuzzer, trial, 'crash'),
                    os.path.join(helper.edge_coverage_dir(benchmark, fuzzer, trial), 'coverage.json')]
        missing = [path for path in required if not os.path.exists(path)]
        if missing:
            logging.warning('%s-%s-%s: skipping trial in all reports, missing %s',
                            benchmark, fuzzer, trial, ', '.join(missing))
            continue
        trials.append(trial)
    return tuple(trials)
