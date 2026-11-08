apt-get update && apt-get install -y gperf m4 gettext libcap-dev libmount-dev libkmod-dev pkg-config wget python3-pip zip
pip3 install meson==0.55.3 ninja==1.10.0
git clone https://github.com/systemd/systemd systemd
git -C systemd checkout -f cb367b17853d215ebcf2816118c1f53d003e5088
# Link fuzz-varlink against the static libsystemd-shared so the whole program is in one binary
# (needed for whole-program IR and for the FRCOV flag array); FuzzBench's build links the .so.
sed -i "/'src\/fuzz\/fuzz-varlink.c'/{n;s/\[libshared\]/[libshared_static, libbasic, libbasic_gcrypt, libsystemd_static, libjournal_client]/}" systemd/src/fuzz/meson.build
grep -A1 "fuzz-varlink.c" systemd/src/fuzz/meson.build
