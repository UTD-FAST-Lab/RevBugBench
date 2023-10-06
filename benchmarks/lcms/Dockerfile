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
    libtool \
    wget

RUN git clone https://github.com/mm2/Little-CMS.git $SRC/Little-CMS && git -C $SRC/Little-CMS checkout -f f9d75ccef0b54c9f4167d95088d4727985133c

RUN wget -qO $OUT/fuzz-target.dict \
    https://raw.githubusercontent.com/google/fuzzing/master/dictionaries/icc.dict
COPY cms_transform_fuzzer.cc build.sh $SRC/
COPY fr_injection.patch $SRC/
ADD seeds /opt/seeds
