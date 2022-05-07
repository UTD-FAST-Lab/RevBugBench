# Copyright 2016 Google Inc.
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

RUN apt-get update && apt-get install -y make autoconf automake libtool pkg-config python-dev python3-dev

RUN git clone https://gitlab.gnome.org/GNOME/libxml2.git $SRC/libxml2 && git -C $SRC/libxml2 checkout -f 99a864a1f7a9cb59865f803770d7d62fb47cad69

WORKDIR $SRC/libxml2
COPY build.sh $SRC/
COPY fr_injection.patch $SRC/
COPY *.cc *.h *.dict $SRC/
