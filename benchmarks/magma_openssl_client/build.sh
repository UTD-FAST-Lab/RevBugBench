#!/bin/bash -eu
# FixReverter-injected bugs (RevBugBench)
git -C /src/openssl apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

cd $SRC/openssl
export LDLIBS="$LIB_FUZZING_ENGINE"
# OpenSSL links --with-fuzzer-lib=<dir>/lib<name> as -L<dir> -l<name>, but
# $LIB_FUZZING_ENGINE may be any archive, an object, or a flag (libFuzzer:
# -fsanitize=fuzzer, which LDLIBS above already links). Normalize it.
rm -f $SRC/libfr_fuzz_engine.a
case "$LIB_FUZZING_ENGINE" in
  *.a) cp "$LIB_FUZZING_ENGINE" $SRC/libfr_fuzz_engine.a ;;
  *.o) ar rcs $SRC/libfr_fuzz_engine.a "$LIB_FUZZING_ENGINE" ;;
  *)   ar rcs $SRC/libfr_fuzz_engine.a ;;
esac
FR_FUZZ_LIB=$SRC/libfr_fuzz_engine
./config --debug enable-fuzz-libfuzzer --with-fuzzer-lib=$FR_FUZZ_LIB disable-tests -DPEDANTIC \
    -DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION no-shared no-module \
    enable-tls1_3 enable-rc5 enable-md2 enable-ec_nistp_64_gcc_128 enable-ssl3 \
    enable-ssl3-method enable-nextprotoneg enable-weak-ssl-ciphers \
    $CFLAGS -fno-sanitize=alignment
make -j$(nproc) clean
make -j$(nproc) build_generated
make -j$(nproc) fuzz/client LDCMD="$CXX $CXXFLAGS"
cp fuzz/client $OUT/
rm -rf $SRC/fr_seeds && mkdir -p $SRC/fr_seeds && cp -r /src/corpus/. $SRC/fr_seeds/
# seed corpus, FuzzBench-style
if [ -d $SRC/fr_seeds ] && [ -n "$(ls -A $SRC/fr_seeds)" ]; then (cd $SRC/fr_seeds && rm -f $OUT/client_seed_corpus.zip && zip -qr $OUT/client_seed_corpus.zip .); fi
