#!/bin/bash -eu
# FixReverter-injected bugs (RevBugBench)
git -C /src/libsndfile apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

cd $SRC/libsndfile
./autogen.sh
./configure --disable-shared --enable-ossfuzzers
make -j$(nproc) clean
make -j$(nproc)
cp -v ossfuzz/sndfile_fuzzer $OUT/
rm -rf $SRC/fr_seeds && mkdir -p $SRC/fr_seeds
# seed corpus, FuzzBench-style
if [ -d $SRC/fr_seeds ] && [ -n "$(ls -A $SRC/fr_seeds)" ]; then (cd $SRC/fr_seeds && rm -f $OUT/sndfile_fuzzer_seed_corpus.zip && zip -qr $OUT/sndfile_fuzzer_seed_corpus.zip .); fi
