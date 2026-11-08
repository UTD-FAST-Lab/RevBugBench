#!/bin/bash -eu
# Copyright 2016 Google Inc.
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

# FixReverter-injected bugs (RevBugBench)
git -C $SRC/file apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

autoreconf -fi
./configure --enable-static --disable-shared --disable-libseccomp
make V=1 all

$CXX $CXXFLAGS -std=c++11 -Isrc/ \
     $SRC/magic_fuzzer.cc -o $OUT/magic_fuzzer \
     $LIB_FUZZING_ENGINE ./src/.libs/libmagic.a -lz

cp ./magic/magic.mgc $OUT/


# Force a empty seed.
# zip -j $OUT/magic_fuzzer_seed_corpus.zip ./tests/*.testfile
