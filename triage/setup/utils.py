# Where fuzzing results are stored for each trail of a benchmark-fuzzer pair.
import os


def fuzzbench_data_dir(fuzzbench_exp_dir: str, exp_name: str, benchmark: str, fuzzer: str) -> str:
    return os.path.join(fuzzbench_exp_dir, exp_name, 'experiment-folders', f'{benchmark}-{fuzzer}')
