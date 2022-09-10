# Where fuzzing results are stored for each trail of a benchmark-fuzzer pair.
import os


def fuzzbench_data_dir(benchmark: str, fuzzer: str, exp_name: str, fuzzbench_exp_dir: str) -> str:
    return os.path.join(fuzzbench_exp_dir, exp_name, 'experiment-folders', f'{benchmark}-{fuzzer}')