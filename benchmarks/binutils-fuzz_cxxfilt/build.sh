#!/bin/bash -eu

# Copyright 2020 Google Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#       http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

cd binutils-gdb
git apply ../fr_injection.patch

cd binutils
sed -i 's/vfprintf (stderr/\/\//' elfcomm.c
sed -i 's/fprintf (stderr/\/\//' elfcomm.c
cd ../

./configure --disable-gdb --disable-gdbserver --disable-gdbsupport \
	    --disable-libdecnumber --disable-readline --disable-sim \
	    --enable-targets=all --disable-werror
make -j

cd binutils
cp ../../fuzz_cxxfilt.c .

sed 's/main (int argc/old_main (int argc, char **argv);\nint old_main (int argc/' cxxfilt.c > cxxfilt.h

$CC $CFLAGS -DHAVE_CONFIG_H -I. -I../bfd -I./../bfd -I./../include -I./../zlib -DLOCALEDIR="\"/usr/local/share/locale\"" -Dbin_dummy_emulation=bin_vanilla_emulation -W -Wall -MT fuzz_cxxfilt.o -MD -MP -c -o fuzz_cxxfilt.o fuzz_cxxfilt.c

$CXX $CXXFLAGS $LIB_FUZZING_ENGINE -W -Wall -Wstrict-prototypes -Wmissing-prototypes -Wshadow -I./../zlib -o fuzz_cxxfilt fuzz_cxxfilt.o bucomm.o version.o filemode.o ../bfd/.libs/libbfd.a -L/src/binutils-gdb/zlib -lpthread -ldl -lz ../libiberty/libiberty.a
mv fuzz_cxxfilt $OUT/fuzz_cxxfilt

cp $SRC/fuzz_cxxfilt.options $OUT/fuzz_cxxfilt.options
