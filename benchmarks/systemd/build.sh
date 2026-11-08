#!/bin/bash -eu
# FixReverter-injected bugs (RevBugBench)
git -C /src/systemd apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

# FuzzBench build: tools/oss-fuzz.sh (meson -Doss-fuzz=true), restricted to the fuzz-varlink target
case "$LIB_FUZZING_ENGINE" in
  *.a) [ "$LIB_FUZZING_ENGINE" -ef /usr/lib/libFuzzingEngine.a ] || ln -sf "$LIB_FUZZING_ENGINE" /usr/lib/libFuzzingEngine.a ;;
  *.o) rm -f /usr/lib/libFuzzingEngine.a; ar rcs /usr/lib/libFuzzingEngine.a "$LIB_FUZZING_ENGINE" ;;
esac
cd $SRC/systemd
export LC_CTYPE=C.UTF-8
B=$SRC/systemd_build; rm -rf $B
meson $B -Doss-fuzz=true -Db_lundef=false
ninja -C $B fuzz-varlink
cp $B/fuzz-varlink $OUT/
rm -rf $SRC/fr_seeds && mkdir -p $SRC/fr_seeds && cp test/fuzz/fuzz-varlink/* $SRC/fr_seeds/ 2>/dev/null || true
# seed corpus, FuzzBench-style
if [ -d $SRC/fr_seeds ] && [ -n "$(ls -A $SRC/fr_seeds)" ]; then (cd $SRC/fr_seeds && rm -f $OUT/fuzz-varlink_seed_corpus.zip && zip -qr $OUT/fuzz-varlink_seed_corpus.zip .); fi
