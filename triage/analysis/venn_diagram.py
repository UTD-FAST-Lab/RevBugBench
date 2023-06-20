import json
import logging
import matplotlib
import os

from analysis.utils import TYPE_KEYS
from common.confighelper import ConfigHelper
from include.pyvenn import venn

# matplotlib.use('Agg')
# matplotlib.pyplot.rc('font', size=12)

def venn_diagram(helper: ConfigHelper, interest: str='single_cause') -> None:
    if len(helper.fuzzers()) != 5:
        logging.error('the number of fuzzers has to be 5 to draw the 5-way venn diagram')
        exit(0)
    id_sets = {f: set() for f in helper.fuzzers()}
    for fuzzer in helper.fuzzers():
        for benchmark in helper.benchmarks():
            for trial in helper.trials(benchmark, fuzzer):
                with open(helper.parsed_seeds_store(benchmark, fuzzer, trial, 'crash'), 'r') as f:
                    crashed_seeds = json.load(f)
                for seed in crashed_seeds:
                    for id_list in seed[TYPE_KEYS[interest]]:
                        if interest == 'single_cause' and len(id_list) != 1:
                            continue
                        id_sets[fuzzer] |= set([(benchmark, i) for i in id_list])
    logging.info(f'number of unique {interest}: {len(set.union(*id_sets.values()))}')
    fuzzers = list(id_sets.keys())
    data = [id_sets[f] for f in fuzzers]
    labels = venn.get_labels(data, fill=['number'])
    fig, ax = venn.venn5(labels, names=fuzzers, fontsize=12, figsize=(14, 12))
    fig.savefig(os.path.join(helper.out_dir(), 'venn_diagram.png'))
    matplotlib.pyplot.clf()