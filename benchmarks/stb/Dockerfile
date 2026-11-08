# Copyright 2020 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################

FROM gcr.io/oss-fuzz-base/base-builder@sha256:87ca1e9e19235e731fac8de8d1892ebe8d55caf18e7aa131346fc582a2034fdd

RUN apt-get update && \
    apt-get install -y wget tar

RUN git clone https://github.com/nothings/stb.git && git -C stb checkout -f f54acd4e13430c5122cab4ca657705c84aa61b08

RUN wget -O $SRC/stb/gif.tar.gz https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/imagetestsuite/imagetestsuite-gif-1.00.tar.gz
RUN wget -O $SRC/stb/jpg.tar.gz https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/imagetestsuite/imagetestsuite-jpg-1.00.tar.gz
RUN wget -O $SRC/stb/tests/gif.dict https://raw.githubusercontent.com/mirrorer/afl/master/dictionaries/gif.dict &> /dev/null

COPY build.sh $SRC/
COPY fr_injection.patch $SRC/
COPY stbi_read_fuzzer.c $SRC/stbi_read_fuzzer.fr.c
