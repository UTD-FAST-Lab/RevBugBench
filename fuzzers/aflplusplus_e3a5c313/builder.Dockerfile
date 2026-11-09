# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

ARG parent_image
FROM $parent_image

# This AFL++ commit predates LLVM 15 (the OSS-Fuzz base-builder clang) and its
# LLVM mode refuses to build against it. Build it against Ubuntu 20.04's
# clang-12 (what FuzzBench used in 2021) and let afl-cc compile targets with it.
RUN apt-get update && \
    apt-get install -y clang-12 llvm-12-dev lld-12 libc++-12-dev libc++abi-12-dev \
                       wget libtool-bin automake flex bison \
                       libglib2.0-dev libpixman-1-dev python3-setuptools unzip \
                       apt-utils apt-transport-https ca-certificates

# Download and compile afl++.
RUN git clone https://github.com/AFLplusplus/AFLplusplus.git /afl && \
    cd /afl && \
    git checkout e3a5c31307f323452dc4b5288e0d19a02b596a33 && \
    # Backport of AFL++ 110cc276: skip >64-bit switches in laf/CmpLog switch
    # splitting instead of aborting clang (e.g. OpenSSL curve448 __int128).
    grep -q 'bitw <= 8) {' instrumentation/split-switches-pass.so.cc && \
    sed -i 's/if (!SI->getNumCases() || bitw <= 8) {/if (!SI->getNumCases() || bitw <= 8 || bitw > 64) {/' \
        instrumentation/split-switches-pass.so.cc && \
    sed -i 's|^#define CMPLOG_SOLVE|// #define CMPLOG_SOLVE|' include/config.h

# Build without Python support as we don't need it.
# Set AFL_NO_X86 to skip flaky tests.
RUN cd /afl && unset CFLAGS && unset CXXFLAGS && \
    export CC=clang-12 CXX=clang++-12 LLVM_CONFIG=llvm-config-12 && \
    export AFL_NO_X86=1 && \
    PYTHON_INCLUDE=/ make && make install && \
    make -C utils/aflpp_driver CC=clang-12 CXX=clang++-12 && \
    cp utils/aflpp_driver/libAFLDriver.a /
