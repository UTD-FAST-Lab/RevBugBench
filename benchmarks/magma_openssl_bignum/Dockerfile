# RevBugBench benchmark magma_openssl_bignum: Magma v1.2.0 program with FixReverter-injected bugs
FROM gcr.io/oss-fuzz-base/base-builder@sha256:87ca1e9e19235e731fac8de8d1892ebe8d55caf18e7aa131346fc582a2034fdd
WORKDIR $SRC
# apt dependencies + clone at the pinned commit
COPY setup.sh $SRC/
RUN bash -ex setup.sh
COPY corpus $SRC/corpus
COPY build.sh fr_injection.patch $SRC/
