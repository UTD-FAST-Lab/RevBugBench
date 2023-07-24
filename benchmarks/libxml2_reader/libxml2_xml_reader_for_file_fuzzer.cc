#ifdef FRCOV
#define FIXREVERTER_SIZE 4734
short FIXREVERTER[FIXREVERTER_SIZE];
#endif
// Copyright 2018 Google Inc.
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

#include <fuzzer/FuzzedDataProvider.h>

#include <cstddef>
#include <cstdint>
#include <string>

#include "fuzzer_temp_file.h"

#include "libxml/xmlreader.h"

void ignore (void* ctx, const char* msg, ...) {
  // Error handler to avoid spam of error messages from libxml parser.
}


#ifdef FRCOV
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#endif
extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
  
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
  xmlSetGenericErrorFunc(NULL, &ignore);

  FuzzedDataProvider provider(data, size);
  const int options = provider.ConsumeIntegral<int>();

  // libxml does not expect more than 100 characters, let's go beyond that.
  const std::string encoding = provider.ConsumeRandomLengthString(128);
  auto file_contents = provider.ConsumeRemainingBytes<uint8_t>();

  FuzzerTemporaryFile file(file_contents.data(), file_contents.size());

  xmlTextReaderPtr xmlReader =
      xmlReaderForFile(file.filename(), encoding.c_str(), options);

  constexpr int kReadSuccessful = 1;
  while (xmlTextReaderRead(xmlReader) == kReadSuccessful) {
    xmlTextReaderNodeType(xmlReader);
    xmlTextReaderConstValue(xmlReader);
  }

  xmlFreeTextReader(xmlReader);
  return EXIT_SUCCESS;
}
