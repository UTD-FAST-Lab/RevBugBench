#!/bin/bash -eu
# Copyright 2018 Google Inc.
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

cd libpcap
git apply ../fr_injection.patch
# build project
mkdir build
cd build
cmake ..
make -k || true


# build fuzz targets
for target in both
do
    $CC $CFLAGS -I.. -c ../testprogs/fuzz/fuzz_$target.c -o fuzz_$target.o
    $CXX $CXXFLAGS fuzz_$target.o -o $OUT/fuzz_$target libpcap.a $LIB_FUZZING_ENGINE
done

# export other associated stuff
cd ..
cp testprogs/fuzz/fuzz_*.options $OUT/
