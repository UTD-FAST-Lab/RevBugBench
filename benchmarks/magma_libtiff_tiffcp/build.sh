#!/bin/bash -eu
# FixReverter-injected bugs (RevBugBench)
git -C /src/libtiff apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

TW=$SRC/tiffwork; rm -rf $TW; mkdir -p $TW/lib $TW/include
cd $SRC/libtiff
sed -i "s/test \$retval -eq 0 || exit \$retval/true/" autogen.sh
./autogen.sh
./configure --disable-shared --prefix="$TW"
make -j$(nproc) clean
make -j$(nproc)
make install
# Magma driver: tiffcp -M @@ tmp.out, run in-process through the CLI wrapper
$CC $CFLAGS -Dmain=fr_tool_main -Dexit=fr_tool_exit -I$SRC/libtiff/libtiff -I$SRC/libtiff/port -I$TW/include -Ilibtiff -c tools/tiffcp.c -o $SRC/tiffcp_tool.o
$CC $CFLAGS -DFR_TOOL_ARGS='"-M","@@","tmp.out"' -c $SRC/tiffcp_fuzzer.c -o $SRC/tiffcp_fuzzer.o
$CXX $CXXFLAGS $SRC/tiffcp_fuzzer.o $SRC/tiffcp_tool.o -o $OUT/tiffcp $LIB_FUZZING_ENGINE \
    $TW/lib/libtiff.a -lz -ljpeg -Wl,-Bstatic -llzma -Wl,-Bdynamic
rm -rf $SRC/fr_seeds && mkdir -p $SRC/fr_seeds && cp -r /src/corpus/. $SRC/fr_seeds/
# seed corpus, FuzzBench-style
if [ -d $SRC/fr_seeds ] && [ -n "$(ls -A $SRC/fr_seeds)" ]; then (cd $SRC/fr_seeds && rm -f $OUT/tiffcp_seed_corpus.zip && zip -qr $OUT/tiffcp_seed_corpus.zip .); fi
