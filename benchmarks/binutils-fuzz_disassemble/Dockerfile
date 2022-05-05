# Copyright 2019 Google Inc.
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

FROM gcr.io/oss-fuzz-base/base-builder@sha256:b112cfb8b4adbb796643f42f8ba40b92962912893f64d617b2706d51c1bd1a53

RUN apt-get update && apt-get install -y make autoconf autogen texinfo flex bison

RUN git clone --recursive git://sourceware.org/git/binutils-gdb.git $SRC/binutils-gdb && git -C $SRC/binutils-gdb checkout -f 7c96e6120f1b9b5025629bbe995ca55d1be8f36f

COPY build.sh $SRC/
COPY fuzz_disassemble.c $SRC/
COPY fr_injection.patch $SRC/
ADD seeds $OUT/seeds

WORKDIR $SRC/
