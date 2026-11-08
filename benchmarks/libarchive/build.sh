#!/bin/bash -eu
# FixReverter-injected bugs (RevBugBench)
git -C /src/libarchive apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

cd $SRC/libarchive
./build/autogen.sh
./configure
make clean
make -j$(nproc) all
$CXX $CXXFLAGS -Ilibarchive $SRC/libarchive_fuzzer.cc -o $OUT/libarchive_fuzzer $LIB_FUZZING_ENGINE .libs/libarchive.a \
    -Wl,-Bstatic -lbz2 -llzo2 -lxml2 -llzma -lz -lcrypto -llz4 -licuuc -licudata -Wl,-Bdynamic -l:libstdc++.so.6
rm -rf $SRC/fr_seeds && mkdir -p $SRC/fr_seeds
# seed corpus, FuzzBench-style
if [ -d $SRC/fr_seeds ] && [ -n "$(ls -A $SRC/fr_seeds)" ]; then (cd $SRC/fr_seeds && rm -f $OUT/libarchive_fuzzer_seed_corpus.zip && zip -qr $OUT/libarchive_fuzzer_seed_corpus.zip .); fi
