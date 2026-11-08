#!/bin/bash -eu
# FixReverter-injected bugs (RevBugBench)
git -C /src/ndpi apply $SRC/fr_injection.patch
# injected bugs leave guard variables set-but-unused in the bugs-compiled-in (non-FRCOV) build; keep -Werror projects building
export CFLAGS="${CFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable" CXXFLAGS="${CXXFLAGS:-} -Wno-error=unused-but-set-variable -Wno-error=unused-variable"

cd $SRC
rm -rf libpcap-1.9.1 && tar -xzf libpcap-1.9.1.tar.gz
cd libpcap-1.9.1
./configure --disable-shared --disable-rdma --disable-dbus --disable-bluetooth --disable-usb --without-libnl
make -j$(nproc)
make install
cd $SRC/ndpi
sh autogen.sh
./configure --enable-fuzztargets
make clean
make
cp fuzz/fuzz_ndpi_reader $OUT/
rm -rf $SRC/fr_seeds && mkdir -p $SRC/fr_seeds
# seed corpus, FuzzBench-style
if [ -d $SRC/fr_seeds ] && [ -n "$(ls -A $SRC/fr_seeds)" ]; then (cd $SRC/fr_seeds && rm -f $OUT/fuzz_ndpi_reader_seed_corpus.zip && zip -qr $OUT/fuzz_ndpi_reader_seed_corpus.zip .); fi
