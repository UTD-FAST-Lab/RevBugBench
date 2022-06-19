import sys
import os
import subprocess
import pickle
import statistics


TIME_INTERVALS = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 
                  75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 
                  225, 240, 255, 270, 285, 300, 360, 420, 480, 540, 
                  600, 660, 720, 780, 840, 900, 1800, 2700, 3600, 4500, 
                  5400, 6300, 7200, 8100, 9000, 9900, 10800, 11700, 
                  12600, 13500, 14400, 15300, 16200, 17100, 18000, 18900, 
                  19800, 20700, 21600, 22500, 23400, 24300, 25200, 26100, 
                  27000, 27900, 28800, 29700, 30600, 31500, 32400, 33300, 
                  34200, 35100, 36000, 36900, 37800, 38700, 39600, 40500, 
                  41400, 42300, 43200, 44100, 45000, 45900, 46800, 47700, 
                  48600, 49500, 50400, 51300, 52200, 53100, 54000, 54900, 
                  55800, 56700, 57600, 58500, 59400, 60300, 61200, 62100, 
                  63000, 63900, 64800, 65700, 66600, 67500, 68400, 69300, 
                  70200, 71100, 72000, 72900, 73800, 74700, 75600, 76500, 
                  77400, 78300, 79200, 80100, 81000, 81900, 82800, 83700, 
                  84600, 85500, 86400]

TIME_LABELS = ['0', '5s', '', '', '', '', '30s', '', '', '', '', '', '60s', 
                  '', '', '', '', '', '150s', '', '', '', '', 
                  '', '', '', '', '', '300s', '', '', '', '', 
                  '10m', '', '', '', '', '15m', '', '', '1h', '', 
                  '', '', '2h', '', '', '', '3h', '', 
                  '', '', '4h', '', '', '', '5h', '', 
                  '', '', '6h', '', '', '', '7h', '', 
                  '', '', '8h', '', '', '', '9h', '', 
                  '', '', '10h', '', '', '', '11h', '', 
                  '', '', '12h', '', '', '', '13h', '', 
                  '', '', '14h', '', '', '', '15h', '', 
                  '', '', '16h', '', '', '', '17h', '', 
                  '', '', '18h', '', '', '', '19h', '', 
                  '', '', '20h', '', '', '', '21h', '', 
                  '', '', '22h', '', '', '', '23h', '', 
                  '', '', '24h']

TIME_LABELS_TWO_HOUR = ['', '', '', '', '', '', '', '', '', '', '', '', '', 
                  '', '', '', '', '', '', '', '', '', '', 
                  '', '', '', '', '', '', '', '', '', '', 
                  '', '', '', '', '', '', '', '', '', '', 
                  '', '', '2h', '', '', '', '', '', 
                  '', '', '4h', '', '', '', '', '', 
                  '', '', '6h', '', '', '', '', '', 
                  '', '', '8h', '', '', '', '', '', 
                  '', '', '10h', '', '', '', '', '', 
                  '', '', '12h', '', '', '', '', '', 
                  '', '', '14h', '', '', '', '', '', 
                  '', '', '16h', '', '', '', '', '', 
                  '', '', '18h', '', '', '', '', '', 
                  '', '', '20h', '', '', '', '', '', 
                  '', '', '22h', '', '', '', '', '', 
                  '', '', '24h']

PROGRAMS = {'binutils-fuzz_cxxfilt', 'binutils-fuzz_disassemble', 'lcms', 'proj4', 'zstd', 'libpcap', 'usrsctp', 'curl', 'libxml2_xml', 'libxml2_reader'}

FUZZERS = ['afl', 'aflplusplus', 'eclipser', 'fairfuzz', 'libfuzzer']

CORPUS_QUEUE_STORE = {'aflplusplus': ['corpus/default/queue'],
                      'afl': ['corpus/queue'],
                      'libfuzzer': ['corpus/corpus'],
                      'eclipser': ['corpus/afl-worker/queue', 'corpus/eclipser_output/queue'],
                      'fairfuzz': ['corpus/queue']}
CORPUS_CRASH_STORE = {'aflplusplus': ['corpus/default/crashes'],
                      'afl': ['corpus/crashes'],
                      'libfuzzer': ['corpus/crashes'],
                      'eclipser': ['corpus/afl-worker/crashes', 'corpus/eclipser_output/crashes'],
                      'fairfuzz': ['corpus/crashes']}

COV_BINS = {'binutils-fuzz_cxxfilt': 'fuzz_cxxfilt',
            'binutils-fuzz_disassemble': 'fuzz_disassemble',
            'lcms': 'cms_transform_fuzzer',
            'proj4': 'standard_fuzzer',
            'zstd': 'stream_decompress',
            'libpcap': 'fuzz_both',
            'usrsctp': 'fuzzer_connect',
            'curl': 'curl_fuzzer_http',
            'libxml2_xml': 'xml',
            'libxml2_reader': 'libxml2_xml_reader_for_file_fuzzer',
           }

TRIAGE_TYPES = ['individual', 'combined', 'trigger', 'reach']
MEASURE_TYPES = ['trigger', 'region', 'function', 'line', 'branch']

SCRIPT_DIR = os.path.dirname(os.path.dirname(__file__))


def run_command(args: str, stdin=subprocess.PIPE, env=os.environ, cwd=None, shell=False, timeout=None):
  try:
    res = subprocess.run(args, shell=shell, stdin=stdin, env=env, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    return res.returncode, res.stdout, res.stderr
  except subprocess.TimeoutExpired:    
    return 124, b'', b''


def median_of_trials(nums_by_time_by_trial):
  total_nums_by_time = {}

  for trial_name, nums_by_time in nums_by_time_by_trial.items():
    for elapsed_seconds, num in nums_by_time.items():
      if elapsed_seconds not in total_nums_by_time:
        total_nums_by_time[elapsed_seconds] = []
      total_nums_by_time[elapsed_seconds].append(num)

  for elapsed_seconds, total_nums in total_nums_by_time.items():
    if len(total_nums) != len(nums_by_time_by_trial.keys()):
      print('something went wrong')
    total_nums_by_time[elapsed_seconds] = statistics.median(total_nums)

  return total_nums_by_time


def fill_missing_time(num_by_time):
  last_num = 0
  num_by_time[0] = 0
  for i in TIME_INTERVALS:
    if i not in num_by_time:
      num_by_time[i] = last_num
    else:
      last_num = num_by_time[i]

  return num_by_time


def dump_to_pickle(out_folder, trial_nums, data_type: str):
  with open(os.path.join(out_folder ,f'{data_type}.pickle'), 'wb+') as f:
    pickle.dump(trial_nums, f)


def read_from_pickle(out_dir):
  with open(os.path.join(out_dir, 'measure.pickle'), 'rb') as f:
    measures = pickle.load(f)
  return measures


if __name__ == '__main__':
  sys.exit(main())
