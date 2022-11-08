from common.confighelper import ConfigHelper
from setup import precheck
from setup.extract import extract_fuzzing_result
from setup.triage_bin import build_triage_bin


def setup(helper: ConfigHelper) -> None:
    exp_tuples = precheck.exp_tuples(helper.benchmarks(), helper.fuzzers(), helper.exps(), helper.raw_data_dir())
    for benchmark, fuzzer, exp_name in exp_tuples:
        extract_fuzzing_result(benchmark, fuzzer, exp_name, helper)
    for benchmark in helper.benchmarks():
        build_triage_bin(benchmark, helper)
        