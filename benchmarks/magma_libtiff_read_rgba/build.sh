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
$CXX $CXXFLAGS -std=c++11 -I$TW/include $SRC/tiff_read_rgba_fuzzer.cc -o $OUT/tiff_read_rgba_fuzzer $LIB_FUZZING_ENGINE \
    $TW/lib/libtiffxx.a $TW/lib/libtiff.a -lz -ljpeg -Wl,-Bstatic -llzma -Wl,-Bdynamic
rm -rf $SRC/fr_seeds && mkdir -p $SRC/fr_seeds && cp -r /src/corpus/. $SRC/fr_seeds/ && find $SRC/fr_seeds -type f | head -1 >/dev/null
# seed corpus, FuzzBench-style
if [ -d $SRC/fr_seeds ] && [ -n "$(ls -A $SRC/fr_seeds)" ]; then (cd $SRC/fr_seeds && rm -f $OUT/tiff_read_rgba_fuzzer_seed_corpus.zip && zip -qr $OUT/tiff_read_rgba_fuzzer_seed_corpus.zip .); fi
