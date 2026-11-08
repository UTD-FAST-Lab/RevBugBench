#!/bin/bash -eu
# FixReverter-injected bugs (RevBugBench)
git -C /src/libgit2 apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

cd $SRC/libgit2
rm -rf build && mkdir -p build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX="$WORK" -DBUILD_SHARED_LIBS=OFF -DBUILD_CLAR=OFF -DUSE_HTTPS=OFF -DUSE_SSH=OFF -DUSE_BUNDLED_ZLIB=ON
make -j$(nproc)
make install
$CC $CFLAGS -c -I"$WORK/include" -I"$SRC/libgit2/src" -DLIBGIT2_NO_FEATURES_H ../fuzzers/objects_fuzzer.c -o "$WORK/objects_fuzzer.o"
$CXX $CXXFLAGS -std=c++11 -o "$OUT/objects_fuzzer" "$WORK/objects_fuzzer.o" $LIB_FUZZING_ENGINE "$WORK/lib/libgit2.a"
rm -rf $SRC/fr_seeds && mkdir -p $SRC/fr_seeds && cp ../fuzzers/corpora/objects/* $SRC/fr_seeds/
# seed corpus, FuzzBench-style
if [ -d $SRC/fr_seeds ] && [ -n "$(ls -A $SRC/fr_seeds)" ]; then (cd $SRC/fr_seeds && rm -f $OUT/objects_fuzzer_seed_corpus.zip && zip -qr $OUT/objects_fuzzer_seed_corpus.zip .); fi
