#!/bin/bash -eu
# FixReverter-injected bugs (RevBugBench)
git -C /src/libxml2 apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

cd $SRC/libxml2
./autogen.sh --with-http=no --with-python=no --with-lzma=yes --with-threads=no --disable-shared
make -j$(nproc) clean
make -j$(nproc) all
$CXX $CXXFLAGS -std=c++11 -Iinclude/ -I$SRC/ $SRC/libxml2_xml_read_memory_fuzzer.cc -o $OUT/libxml2_xml_read_memory_fuzzer $LIB_FUZZING_ENGINE .libs/libxml2.a -lz -llzma
rm -rf $SRC/fr_seeds && mkdir -p $SRC/fr_seeds && cp -r /src/corpus/. $SRC/fr_seeds/ && find $SRC/fr_seeds -type f | head -1 >/dev/null
# seed corpus, FuzzBench-style
if [ -d $SRC/fr_seeds ] && [ -n "$(ls -A $SRC/fr_seeds)" ]; then (cd $SRC/fr_seeds && rm -f $OUT/libxml2_xml_read_memory_fuzzer_seed_corpus.zip && zip -qr $OUT/libxml2_xml_read_memory_fuzzer_seed_corpus.zip .); fi
