#!/bin/bash -eu
# FixReverter-injected bugs (RevBugBench)
git -C /src/libpng apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

cd $SRC/libpng
autoreconf -f -i
./configure --with-libpng-prefix=MAGMA_ --disable-shared
make -j$(nproc) clean
make -j$(nproc) libpng16.la
$CXX $CXXFLAGS -std=c++11 -I. contrib/oss-fuzz/libpng_read_fuzzer.cc -o $OUT/libpng_read_fuzzer $LIB_FUZZING_ENGINE .libs/libpng16.a -lz
rm -rf $SRC/fr_seeds && mkdir -p $SRC/fr_seeds && cp -r /src/corpus/. $SRC/fr_seeds/ && find $SRC/fr_seeds -type f | head -1 >/dev/null
# seed corpus, FuzzBench-style
if [ -d $SRC/fr_seeds ] && [ -n "$(ls -A $SRC/fr_seeds)" ]; then (cd $SRC/fr_seeds && rm -f $OUT/libpng_read_fuzzer_seed_corpus.zip && zip -qr $OUT/libpng_read_fuzzer_seed_corpus.zip .); fi
