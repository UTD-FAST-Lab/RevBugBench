#!/bin/bash -eu
# FixReverter-injected bugs (RevBugBench)
git -C /src/file apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

cd $SRC/file
autoreconf -fi
./configure --enable-static --disable-shared --disable-libseccomp
make clean
make V=1 all
$CXX $CXXFLAGS -std=c++11 -Isrc/ $SRC/magic_fuzzer.cc -o $OUT/magic_fuzzer $LIB_FUZZING_ENGINE ./src/.libs/libmagic.a -lz
cp ./magic/magic.mgc $OUT/
rm -rf $SRC/fr_seeds && mkdir -p $SRC/fr_seeds
# seed corpus, FuzzBench-style
if [ -d $SRC/fr_seeds ] && [ -n "$(ls -A $SRC/fr_seeds)" ]; then (cd $SRC/fr_seeds && rm -f $OUT/magic_fuzzer_seed_corpus.zip && zip -qr $OUT/magic_fuzzer_seed_corpus.zip .); fi
