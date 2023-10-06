# Copyright 2020 Google LLC
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
    apt-get install -y \
    make \
    automake \
    autoconf \
    libtool \
    sqlite3 \
    wget \
    libsqlite3-dev

RUN git clone https://github.com/OSGeo/PROJ $SRC/PROJ && git -C $SRC/PROJ checkout -f d00501750b210a73f9fb107ac97a683d4e3d8e7a 

RUN wget -qO $OUT/fuzz-target.dict \
    https://raw.githubusercontent.com/google/fuzzing/master/dictionaries/proj4.dict
COPY build.sh $SRC/
COPY fr_injection.patch $SRC/
