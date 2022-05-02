#ifdef FRCOV
#define FIXREVERTER_SIZE 639
short FIXREVERTER[FIXREVERTER_SIZE];
#endif
// Copyright 2020 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <stdint.h>

#include "lcms2.h"


#ifdef FRCOV
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#endif
extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
  
  #ifdef FRCOV
  char *fixReverterEnv = getenv("FIXREVERTER");
  char *fixReverterToken = strtok(fixReverterEnv, " ");
  if (fixReverterToken == NULL) {
    for (int i = 0; i < FIXREVERTER_SIZE; i++)
      FIXREVERTER[i] = 1;
  } else if (!strcmp("on", fixReverterToken)) {
    for (int i = 0; i < FIXREVERTER_SIZE; i++)
      FIXREVERTER[i] = 0;
    fixReverterToken = strtok(NULL, " ");
    while (fixReverterToken != NULL) {
      FIXREVERTER[atoi(fixReverterToken)] = 1;
      fixReverterToken = strtok(NULL, " ");
    }
  } else if (!strcmp("off", fixReverterToken)) {
    for (int i = 0; i < FIXREVERTER_SIZE; i++)
      FIXREVERTER[i] = 1;
    fixReverterToken = strtok(NULL, " ");
    while (fixReverterToken != NULL) {
      FIXREVERTER[atoi(fixReverterToken)] = 0;
      fixReverterToken = strtok(NULL, " ");
    }
  } else {
    fprintf(stderr, "[FIXREVERTER] - first token must be on or off\n");
    exit(0);
  }
  #endif
  cmsHPROFILE srcProfile = cmsOpenProfileFromMem(data, size);
  if (!srcProfile) return 0;

  cmsHPROFILE dstProfile = cmsCreate_sRGBProfile();
  if (!dstProfile) {
    cmsCloseProfile(srcProfile);
    return 0;
  }

  cmsColorSpaceSignature srcCS = cmsGetColorSpace(srcProfile);
  cmsUInt32Number nSrcComponents = cmsChannelsOf(srcCS);
  cmsUInt32Number srcFormat;
  if (srcCS == cmsSigLabData) {
    srcFormat =
        COLORSPACE_SH(PT_Lab) | CHANNELS_SH(nSrcComponents) | BYTES_SH(0);
  } else {
    srcFormat =
        COLORSPACE_SH(PT_ANY) | CHANNELS_SH(nSrcComponents) | BYTES_SH(1);
  }

  cmsUInt32Number intent = 0;
  cmsUInt32Number flags = 0;
  cmsHTRANSFORM hTransform = cmsCreateTransform(
      srcProfile, srcFormat, dstProfile, TYPE_BGR_8, intent, flags);
  cmsCloseProfile(srcProfile);
  cmsCloseProfile(dstProfile);
  if (!hTransform) return 0;

  uint8_t output[4];
  if (T_BYTES(srcFormat) == 0) {  // 0 means double
    double input[nSrcComponents];
    for (uint32_t i = 0; i < nSrcComponents; i++) input[i] = 0.5f;
    cmsDoTransform(hTransform, input, output, 1);
  } else {
    uint8_t input[nSrcComponents];
    for (uint32_t i = 0; i < nSrcComponents; i++) input[i] = 128;
    cmsDoTransform(hTransform, input, output, 1);
  }
  cmsDeleteTransform(hTransform);

  return 0;
}
