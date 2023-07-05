# RevBugBench
RevBugBench is a fuzzing benchmark generated by [FixReverter](https://github.com/SlaterLatiao/FixReverter),
with the idea of automated generation of real-world like bugs. 
See our paper [FIXREVERTER: A Realistic Bug Injection Methodology for Benchmarking Fuzz Testing](https://www.usenix.org/conference/usenixsecurity22/presentation/zhang-zenong) for more details.

This repository consists of 5 directories, and each of them will be introduced in the following sections.

## fuzzbench
**RevBugBench** was developed on FuzzBench commit 65297c4c76e63cbe4025f1ce7abc1e89b7a1566c. 
The [diff file](/fuzzbench/revbugbench.patch) shows the modifications made by RevBugBench. 
The following commands on will apply the changes.
```
cd [path/to/fuzzbench]
git checkout 65297c4c76e63cbe4025f1ce7abc1e89b7a1566c
git apply [path/to/the/diff/file]
```
The changes in the diff file can also be manually ported the the lastest verion of FuzzBench.

## benchmarks
Target programs in this directory consist of 8 fuzzing targets from FuzzBench and 2 commonly fuzzed Binutils utilities, 
injected with bugs by FixReverter. 
Versions of each program can be found in the Dockerfile in each program's directory. 
The target programs are compatible with FuzzBench benchmarks.
They can be added to FuzzBench by copying each program directory into the _benchmarks_ directory of FuzzBench.
```
cp -r [path/to/revbugbench]/benchmarks/* [path/to/fuzzbench]/benchmarks
```
RevBugBench can then be fuzzed the same with as FuzzBench, including 
[setting up prerequites](https://google.github.io/fuzzbench/getting-started/prerequisites/) and 
[running local experiments](https://google.github.io/fuzzbench/running-a-local-experiment).

## ddas
This folder contains the data dependency analysis results for each benchmark program generated by FixReverter.
They are needed in the triage process, and will be elobrated in the [triage](##triage) section.

## fr_triage_driver
This folder contains the driver used by RevBugBench to triage programs with LibFuzzer fuzzing harness.
The triage driver is compatible with FuzzBench fuzzers, and will be built automatically by the triage scripts with the help of FuzzBench Makefile.


## triage
This folder contains the scripts for triage.

### Prerequisites
The triage scripts are developed with python 3.9.0. The [requirements.txt](/triage/requirements.txt) specifies packages used by the scripts. To install them, run with
```
pip install -r requirements.txt
```
### Config
Before running the scripts, a config file needs to be first set up.
The [example config](/triage/config.ini) lists all the necessary configs with explanations in the comments.

After setting up the config file, the data dependency analysis results need to be manually placed on the _workDir_.

```
cp -r [path/to/revbugbench]/ddas [path/to/workDir]/dda_store
```
### Triage binary images
The triage binaries are manually built with FuzzBench. First copy the triage binary source code to FuzzBench.
```
cp -r [path/to/revbugbench]/fuzzers/fr_triage_driver [path/to/fuzzbench]/fuzzers
```
Generate the makefile to build the docker image.
```
cd [path/to/fuzzbench]
# the venv is created when setting up fuzzbench with `make install-dependencies`
source .venv/bin/activate
PYTHONPATH=. python3 docker/generate_makefile.py triage.mk
```
For each benchmark to triage, build the triage binary image by
```
make -f triage.mk .fr_triage_driver-[benchmark name]-builder
```
The triage script will then use the built image to extract triage binaries.

### Command-line Options
The main script to run the triage is [main.py](/triage/main.py).
The following command-line options decided the triage tasks to perform.
#### --setup / -s
Extract fuzzing corpus from fuzzbench results and set up triage binaries.
It needs to be executed before the other tasks.
#### --triage / -t
Run the triage binaries on fuzzing results and produce triage results.
It needs to be executed before --report.
#### --report / -r
Summarize triage results and generate performance plots/tables/figures on out directory.
#### --config / -c
Path to the config file, default to `[path/to/revbugbench]/triage/config.ini`.

### workflow
Running the triage tasks in sequence will generate the performance plots/tables/figures.
```
cd [path/to/revbugbench/triage]
PYTHONPATH=. python3 main.py -c [path/to/config/file] -s
PYTHONPATH=. python3 main.py -c [path/to/config/file] -t
PYTHONPATH=. python3 main.py -c [path/to/config/file] -r
```

# Cite
Please consider citing our USENIX Security 2022 paper if you use FixReverter/RevBugBench in your academic work:
```
@inproceedings {281412,
	title = {{FIXREVERTER}: A Realistic Bug Injection Methodology for Benchmarking Fuzz Testing},
	booktitle = {31st USENIX Security Symposium (USENIX Security 22)},
	year = {2022},
	address = {Boston, MA},
	url = {https://www.usenix.org/conference/usenixsecurity22/presentation/zhang-zenong},
	publisher = {USENIX Association},
	month = aug,
}
```
