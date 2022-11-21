import getpass
import os

import docker

import common.paths
from common.confighelper import ConfigHelper


def build_triage_bin(benchmark: str, helper: ConfigHelper):
    benchmark_triage_dir = helper.benchmark_triage_bin_dir(benchmark)
    common.paths.mkdir(benchmark_triage_dir)
    host_user = getpass.getuser()
    uid = os.getuid()
    gid = os.getgid()

    # Add local host to the container and transfer the ownership of the triage binary.
    # This avoids the trouble of deleting a root-owned triage binary.
    command = f'''
    "groupadd -g {gid} -o {host_user}
    useradd -m -u {uid} -g {gid} -o {host_user}
    cp /out/{helper.fuzz_target(benchmark)} /triage_bin_dir/
    chown  {uid} /triage_bin_dir/{helper.fuzz_target(benchmark)}
    chgrp {gid} /triage_bin_dir/{helper.fuzz_target(benchmark)}"
    '''
    client = docker.from_env()
    client.containers.run(f'gcr.io/fuzzbench/builders/fr_triage_driver/{benchmark}',
                            remove=True,
                            entrypoint='/bin/bash -c',
                            working_dir='/src',
                            command=command,
                            volumes={benchmark_triage_dir: {'bind': '/triage_bin_dir', 'mode': 'rw'}})
    common.paths.error_if_not_exist(helper.benchmark_triage_binary(benchmark),
                                    f'triage binary of benchmark {benchmark} is not successfully extracted')
