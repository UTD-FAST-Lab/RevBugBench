#!/bin/bash -eu
# Copyright 2020 Google Inc.
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
git -C $SRC/stb apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

# FixReverter: the injected harness is FuzzBench's sed '2d' of tests/stb_png_read_fuzzer.cpp plus the flag array
cp $SRC/stbi_read_fuzzer.fr.c $SRC/stb/tests/stbi_read_fuzzer.c

$CXX $CXXFLAGS -std=c++11 -I. \
    $SRC/stb/tests/stbi_read_fuzzer.c \
    -o $OUT/stbi_read_fuzzer $LIB_FUZZING_ENGINE

find $SRC/stb/tests/pngsuite -name "*.png" | \
     xargs zip $OUT/stb_png_read_fuzzer_seed_corpus.zip

cp $SRC/stb/tests/stb_png.dict $OUT/stb_png_read_fuzzer.dict

tar xvzf $SRC/stb/jpg.tar.gz --directory $SRC/stb/tests
tar xvzf $SRC/stb/gif.tar.gz --directory $SRC/stb/tests

find $SRC/stb/tests -name "*.png" -o -name "*.jpg" -o -name ".gif" | \
     xargs zip $OUT/stbi_read_fuzzer_seed_corpus.zip

echo "" >> $SRC/stb/tests/gif.dict
cat $SRC/stb/tests/gif.dict $SRC/stb/tests/stb_png.dict > $OUT/stbi_read_fuzzer.dict

# RevBugBench: drop the 10 seeds that abort on stb's own JPEG assert with all injected bugs off (fr_assert_seeds)
zip -qd $OUT/stbi_read_fuzzer_seed_corpus.zip $(printf 'src/stb/tests/imagetestsuite/jpg/%s.jpg ' \
  194531363df5b73f59c4c0517422f917 46f5d9c1b0fe352353688f736e5617b6 551c2656a4f6f9f5ea7e9945b9081202 \
  59d3b529c78ac722127c41ba75b3355b 5dc71b1d868ef137394d3cc23abea65a 8e5e74dbf9b68a322fbb9512db837329 \
  9efd60f04cd971daa83d3131e6d6f389 c3018ebe53d0046eecb58858ca869a99 eecb78b937a7c5f04aae2f5b0f5b5acc \
  fd44dc63fa7bdd12ee34fc602231ef02)
