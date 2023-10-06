#!/bin/bash -eu
# Copyright 2019 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################

git apply ../fr_injection.patch
# add FRCOV flag if building coverage
if [[ -z "${FR_COV_BUILD}" ]]; then
  cmake -Dsctp_build_programs=0 -Dsctp_debug=0 -Dsctp_invariants=1 -DCMAKE_C_FLAGS="-Wno-error=unused-but-set-variable" -DCMAKE_CXX_FLAGS="-Wno-error=unused-but-set-variable" -DCMAKE_BUILD_TYPE=RelWithDebInfo .
else
  cmake -Dsctp_build_programs=0 -Dsctp_debug=0 -Dsctp_invariants=1 -DCMAKE_C_FLAGS="-DFRCOV -Wno-error=unused-but-set-variable" -DCMAKE_CXX_FLAGS="-DFRCOV -Wno-error=unused-but-set-variable" -DCMAKE_BUILD_TYPE=RelWithDebInfo .
fi

make
cd fuzzer

for target in "fuzzer_connect"; do
  $CC $CFLAGS -DFUZZING_STAGE=0 -I . -I ../usrsctplib/ -c ${target}.c -o $OUT/${target}.o
  $CXX $CXXFLAGS -o $OUT/${target} $OUT/${target}.o $LIB_FUZZING_ENGINE ../usrsctplib/libusrsctp.a
  rm -f $OUT/${target}.o
done

zip -jr fuzzer_connect_seed_corpus.zip CORPUS_CONNECT/
cp fuzzer_connect_seed_corpus.zip $OUT/
