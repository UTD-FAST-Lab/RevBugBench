import json
import os

import logging
import itertools
import multiprocessing
import tqdm

import common.paths
from common.confighelper import ConfigHelper
import include.istarmap
from triage.common.new_process import ProcessResult
from triage.common.parse_log import parse_log
from triage.common import new_process, sanitizer
from triage.get_seeds import get_seeds
from triage.common.utils import UNIT_TIMEOUT, RSS_LIMIT_MB


def triage_seeds(helper: ConfigHelper, seed_type: str) -> None:
    seeds = get_seeds(seed_type, helper)
    logging.info(f'triage seeds on {len(seeds)} {seed_type} entries with {helper.cores()} parallel jobs')
    multiprocessing.pool.Pool.istartmap = include.istarmap.istarmap
    with multiprocessing.Pool(processes=helper.cores()) as p:
        seeds = list(tqdm.tqdm(p.istartmap(triage_worker,
                                           zip(seeds, itertools.repeat(helper), itertools.repeat(seed_type))),
                               total=len(seeds)))
    logging.info(f'store {seed_type} seeds to parsed_seeds')

    # seeds is contiguous w.r.t (fuzzer, benchmark).
    for k, v in itertools.groupby(seeds, lambda x: (x['fuzzer'], x['benchmark'])):
        with open(helper.parsed_seeds_store(k[0], k[1], seed_type), 'w+') as f:
            json.dump(list(v), f, indent=2)


def triage_worker(seed: dict, helper: ConfigHelper, seed_type: str) -> dict:
    worker_name = multiprocessing.current_process().name
    common.paths.mkdir(helper.tmp_running_dir(worker_name))
    seed_env = os.environ.copy()
    sanitizer.set_sanitizer_options(seed_env)
    # Turn on logging of all injections.
    seed_env["FIXREVERTER"] = 'off '
    args = [
        helper.benchmark_triage_binary(seed['benchmark']),
        f'-timeout={UNIT_TIMEOUT}',
        f'-rss_limit_mb={RSS_LIMIT_MB}',
        seed['path']
    ]
    res = execute_seed(args, seed_env, helper.tmp_running_dir(worker_name))
    seed['reaches'], seed['triggers'] = parse_log(res.output)
    # We only need reaches and triggers for seeds in queue.
    if seed_type == 'queue':
        return seed

    # Turn off logging of any injections.
    seed_env["FIXREVERTER"] = 'on '
    non_inj_res = execute_seed(args, seed_env, helper.tmp_running_dir(worker_name))
    # this bug is not caused by FixReverter injections.
    if non_inj_res.retcode:
        seed['crashes'] = []
    else:
        logging.debug(f'triage on trial {seed["trial"]} is running {seed["path"]} with triggers{seed["triggers"]}')
        min_crashsets = []
        # TODO: Make combination level configurable.
        comb_level = min(len(seed['triggers']), 3)
        # Find min crash sets by iterating the power set of triggers.
        for n in range(1, comb_level + 1):
            for currset in itertools.combinations(seed['triggers'], n):
                # Skip if current set is superset of a crash set.
                for crashset in min_crashsets:
                    if set(currset).issuperset(crashset):
                        break
                else:
                    # Only turn on injections of currset.
                    seed_env["FIXREVERTER"] = 'on ' + ' '.join([str(i) for i in currset])
                    logging.debug(f'triage on trial {seed["trial"]} is running {seed["path"]} with set{currset}')
                    curr_res = execute_seed(args, seed_env, helper.tmp_running_dir(worker_name))
                    if curr_res.retcode:
                        logging.debug(f'triage on trial {seed["trial"]} is running {seed["path"]} and get min set {currset}')
                        min_crashsets.append(sorted(currset))
        seed['crashes'] = min_crashsets
    return seed


def execute_seed(args: list, env: dict, cwd: str) -> ProcessResult:
    return new_process.execute(args,
                               env=env,
                               cwd=cwd,
                               expect_zero=False,
                               kill_children=True,
                               timeout=UNIT_TIMEOUT + 5)
