#!/bin/bash -eu
# FixReverter-injected bugs (RevBugBench)
git -C /src/tpm2 apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

rm -rf $WORK/tpm2 && mkdir -p $WORK/tpm2
cd $SRC/tpm2
CFLAGS="$CFLAGS -I/usr/local/ssl10/include" make V=1 obj=$WORK/tpm2 $WORK/tpm2/libtpm2.a
$CXX $CXXFLAGS -std=c++11 $SRC/tpm2/fuzz/execute-command.cc -o $OUT/tpm2_execute_command_fuzzer -I $SRC/tpm2 -I/usr/local/ssl10/include \
  $WORK/tpm2/libtpm2.a /usr/local/ssl10/lib/libssl.a /usr/local/ssl10/lib/libcrypto.a $LIB_FUZZING_ENGINE -ldl -lpthread
rm -rf $SRC/fr_seeds && mkdir -p $SRC/fr_seeds
# seed corpus, FuzzBench-style
if [ -d $SRC/fr_seeds ] && [ -n "$(ls -A $SRC/fr_seeds)" ]; then (cd $SRC/fr_seeds && rm -f $OUT/tpm2_execute_command_fuzzer_seed_corpus.zip && zip -qr $OUT/tpm2_execute_command_fuzzer_seed_corpus.zip .); fi
