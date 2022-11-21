import collections
import itertools
import json
import statistics

from prettytable import PrettyTable
from common.confighelper import ConfigHelper

PATTERNS = ['COND_ABORT', 'COND_EXEC', 'COND_ASSIGN']
EXTENDED_PATTERNS = ['ALL', *PATTERNS]
COV_TYPES = ['reaches', 'triggers', 'single_causes', 'all_causes']
CoverageSummary = collections.namedtuple('CoverageSummary', COV_TYPES)


def trial_coverage(benchmark: str, fuzzer: str, helper: ConfigHelper) -> dict:
    with open(helper.dda_file(benchmark), 'r') as f:
        dda_data = json.load(f)
    pattern_dict = {j['index']: j['pattern'] for j in dda_data}
    ret = {}

    for trial in helper.trials(benchmark, fuzzer):
        summary = CoverageSummary({p: set() for p in EXTENDED_PATTERNS},
                                  {p: set() for p in EXTENDED_PATTERNS},
                                  {p: set() for p in EXTENDED_PATTERNS},
                                  {p: set() for p in EXTENDED_PATTERNS})
        with open(helper.parsed_seeds_store(benchmark, fuzzer, trial, 'queue'), 'r') as f:
            queued = json.load(f)
        with open(helper.parsed_seeds_store(benchmark, fuzzer, trial, 'crash'), 'r') as f:
            crashed = json.load(f)
        for seed in [*queued, *crashed]:
            for r_id in seed['reaches']:
                summary.reaches[pattern_dict[r_id]].add(r_id)
            for t_id in seed['triggers']:
                summary.triggers[pattern_dict[t_id]].add(t_id)
        for seed in crashed:
            for crashset in seed['crashes']:
                for c_id in crashset:
                    if len(crashset) == 1:
                        summary.single_causes[pattern_dict[c_id]].add(c_id)
                    summary.all_causes[pattern_dict[c_id]].add(c_id)
        # Aggregate coverage of all patterns to ALL.
        for p in PATTERNS:
            for cov in summary:
                cov['ALL'].update(cov[p])
        ret[trial] = summary
    return ret


def coverage_table(helper: ConfigHelper) -> None:
    tables = {}
    expanded_fuzzers = [*helper.fuzzers(), 'MetaFuzzer']
    for fuzzer in expanded_fuzzers:
        tables[fuzzer] = PrettyTable()
        tables[fuzzer].field_names = [fuzzer, 'reaches', 'triggers', 'single_causes', 'all_causes']

    for benchmark in helper.benchmarks():
        meta_summary = CoverageSummary({p: set() for p in EXTENDED_PATTERNS},
                                       {p: set() for p in EXTENDED_PATTERNS},
                                       {p: set() for p in EXTENDED_PATTERNS},
                                       {p: set() for p in EXTENDED_PATTERNS})
        for fuzzer in helper.fuzzers():
            trial_cov = trial_coverage(benchmark, fuzzer, helper)
            median_summary = CoverageSummary({p: statistics.median([len(trial_cov[t].reaches[p]) for t in trial_cov])
                                              for p in EXTENDED_PATTERNS},
                                             {p: statistics.median([len(trial_cov[t].triggers[p]) for t in trial_cov])
                                              for p in EXTENDED_PATTERNS},
                                             {p: statistics.median([len(trial_cov[t].single_causes[p]) for t in trial_cov])
                                              for p in EXTENDED_PATTERNS},
                                             {p: statistics.median([len(trial_cov[t].all_causes[p]) for t in trial_cov])
                                              for p in EXTENDED_PATTERNS})
            for cov in COV_TYPES:
                for p in EXTENDED_PATTERNS:
                    getattr(meta_summary, cov)[p].update(itertools.chain(*[getattr(s, cov)[p]
                                                                           for s in trial_cov.values()]))

            tables = construct_row(benchmark, fuzzer, median_summary, tables)
        meta_agg_summary = CoverageSummary({p: len(meta_summary.reaches[p]) for p in EXTENDED_PATTERNS},
                                           {p: len(meta_summary.triggers[p]) for p in EXTENDED_PATTERNS},
                                           {p: len(meta_summary.single_causes[p]) for p in EXTENDED_PATTERNS},
                                           {p: len(meta_summary.all_causes[p]) for p in EXTENDED_PATTERNS})
        tables = construct_row(benchmark, 'MetaFuzzer', meta_agg_summary, tables)
    for fuzzer in expanded_fuzzers:
        print(tables[fuzzer])


def construct_row(benchmark: str, fuzzer: str, summary: CoverageSummary, tables: dict) -> dict:
    row = [benchmark]
    for cov in COV_TYPES:
        # Construct format of `10 (7 1 2)`.
        cov_str = f'{getattr(summary, cov)["ALL"]} ('
        for p in PATTERNS:
            cov_str += str(getattr(summary, cov)[p])
            cov_str += ' '
        row.append(cov_str.rstrip() + ')')
    tables[fuzzer].add_row(row)
    return tables
