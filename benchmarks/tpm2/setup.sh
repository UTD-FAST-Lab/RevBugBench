apt-get update && apt-get install -y make libssl-dev binutils
git clone https://chromium.googlesource.com/chromiumos/third_party/tpm2 tpm2
git -C tpm2 checkout -f 0f114d2d7eb1950faab02fe479864da5e5d50414
# tpm2 (2017) needs the OpenSSL 1.0 API (FuzzBench's xenial base-builder shipped 1.0.2); build it as a static system library
if [ ! -f /usr/local/ssl10/lib/libcrypto.a ]; then
  wget -q https://github.com/openssl/openssl/archive/refs/tags/OpenSSL_1_0_2u.tar.gz -O /tmp/ossl.tgz
  rm -rf /tmp/ossl && mkdir /tmp/ossl && tar -xzf /tmp/ossl.tgz -C /tmp/ossl --strip-components=1
  (cd /tmp/ossl && env -u CFLAGS -u CXXFLAGS CC=clang ./config no-shared no-asm --prefix=/usr/local/ssl10 >/dev/null && make >/dev/null && make install_sw >/dev/null)
fi
