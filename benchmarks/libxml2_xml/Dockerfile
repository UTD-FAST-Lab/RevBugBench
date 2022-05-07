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

FROM gcr.io/oss-fuzz-base/base-builder@sha256:b112cfb8b4adbb796643f42f8ba40b92962912893f64d617b2706d51c1bd1a53

ENV GIT_SSL_NO_VERIFY 1

RUN apt-get update && \
    apt-get install -y \
    make \
    wget \
    autoconf \
    automake \
    libtool \
    libglib2.0-dev

RUN git clone https://gitlab.gnome.org/GNOME/libxml2.git $SRC/libxml2 && git -C $SRC/libxml2 checkout -f v2.9.2

ADD seeds $OUT/seeds

RUN wget -qO $OUT/fuzz-target.dict \
    https://raw.githubusercontent.com/google/AFL/debe27037b9444bbf090a0ffbd5d24889bb887ae/dictionaries/xml.dict
COPY target.cc build.sh $SRC/
COPY fr_injection.patch $SRC/
