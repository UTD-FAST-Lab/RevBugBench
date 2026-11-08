#!/bin/bash -eu
# FixReverter-injected bugs (RevBugBench)
git -C /src/matio apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

export HDF5_DIR=/usr/lib/x86_64-linux-gnu/hdf5/serial
cd $SRC
rm -rf szip-2.1.1 && tar -xf szip.tar.gz
cd szip-2.1.1 && ./configure --disable-shared CFLAGS="-w" && make -C src && cd ..
cd $SRC/matio
./autogen.sh
./configure --with-hdf5=$HDF5_DIR
make clean
make -j$(nproc)
make install
cd ossfuzz
$CXX $CXXFLAGS -std=c++11 -I../include matio_fuzzer.cpp ../getopt/.libs/libgetopt.a ../src/.libs/libmatio.a -o $OUT/matio_fuzzer \
    $LIB_FUZZING_ENGINE $HDF5_DIR/libhdf5.a $SRC/szip-2.1.1/src/.libs/libsz.a -lz
rm -rf $SRC/fr_seeds && mkdir -p $SRC/fr_seeds && find ../share -type f -exec cp {} $SRC/fr_seeds/ \;
# seed corpus, FuzzBench-style
if [ -d $SRC/fr_seeds ] && [ -n "$(ls -A $SRC/fr_seeds)" ]; then (cd $SRC/fr_seeds && rm -f $OUT/matio_fuzzer_seed_corpus.zip && zip -qr $OUT/matio_fuzzer_seed_corpus.zip .); fi
