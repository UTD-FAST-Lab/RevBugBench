#!/bin/bash -eu
# FixReverter-injected bugs (RevBugBench)
git -C /src/njs apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

cd $SRC/njs
rm -rf build
./configure
make njs_fuzzer
cp ./build/njs_process_script_fuzzer $OUT/
SEED=$SRC/fr_seeds; rm -rf $SEED; mkdir -p $SEED
set +x
cat src/test/njs_interactive_test.c src/test/njs_unit_test.c | egrep -o '".*"' | awk '{print substr($0,2,length($0)-2)}' | sort | uniq \
  | while IFS= read -r line; do echo "$line" > $SEED/$(echo "$line" | sha1sum | awk '{ print $1 }'); done
# seed corpus, FuzzBench-style
if [ -d $SRC/fr_seeds ] && [ -n "$(ls -A $SRC/fr_seeds)" ]; then (cd $SRC/fr_seeds && rm -f $OUT/njs_process_script_fuzzer_seed_corpus.zip && zip -qr $OUT/njs_process_script_fuzzer_seed_corpus.zip .); fi
