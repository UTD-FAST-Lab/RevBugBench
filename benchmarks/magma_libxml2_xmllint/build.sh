#!/bin/bash -eu
# FixReverter-injected bugs (RevBugBench)
git -C /src/libxml2 apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

cd $SRC/libxml2
./autogen.sh --with-http=no --with-python=no --with-lzma=yes --with-threads=no --disable-shared
make -j$(nproc) clean
make -j$(nproc) all
# Magma driver: xmllint --valid --oldxml10 --push --memory @@, run in-process through the CLI wrapper
$CC $CFLAGS -Dmain=fr_tool_main -Dexit=fr_tool_exit -I. -Iinclude -c xmllint.c -o $SRC/xmllint_tool.o
$CC $CFLAGS -DFR_TOOL_ARGS='"--valid","--oldxml10","--push","--memory","@@"' -c $SRC/xmllint_fuzzer.c -o $SRC/xmllint_fuzzer.o
$CXX $CXXFLAGS $SRC/xmllint_fuzzer.o $SRC/xmllint_tool.o -o $OUT/xmllint $LIB_FUZZING_ENGINE .libs/libxml2.a -lz -llzma -lm
rm -rf $SRC/fr_seeds && mkdir -p $SRC/fr_seeds && cp -r /src/corpus/. $SRC/fr_seeds/
# seed corpus, FuzzBench-style
if [ -d $SRC/fr_seeds ] && [ -n "$(ls -A $SRC/fr_seeds)" ]; then (cd $SRC/fr_seeds && rm -f $OUT/xmllint_seed_corpus.zip && zip -qr $OUT/xmllint_seed_corpus.zip .); fi
